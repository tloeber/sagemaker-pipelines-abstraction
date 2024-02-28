# For Python < 3.12, don't use typing.TypedDict: https://docs.pydantic.dev/2.6/errors/usage_errors/#typed-dict-version
from typing_extensions import TypedDict
from abc import ABC, abstractmethod
import os
from dataclasses import dataclass
from functools import cached_property
from typing import TypeAlias, Any, Generic, TypeVar, Literal, ClassVar
from pathlib import Path

from loguru import logger
from s3path import S3Path

from sagemaker.session import Session
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.processing import Processor, FrameworkProcessor

from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.pipeline_context import _JobStepArguments
from sagemaker.workflow.entities import PipelineVariable
from sagemaker.sklearn.estimator import SKLearn
from pydantic_settings import BaseSettings

from sm_pipelines_oo.shared_config_schema import SharedConfig
from sm_pipelines_oo.steps.interfaces import StepFactoryInterface

from sm_pipelines_oo.shared_config_schema import SharedConfig


# Pairs of: *Types* on AWS side we need to match + associated *config* from which to construct them
# =================================================================================================

# Note that the AWS SDK provides the class `_JobStepArguments`, but it does not constrain the types
# of permissible keys. See
# https://github.com/aws/sagemaker-python-sdk/blob/e7595a5e0839313d38a87ed0c944739406357a95/src/sagemaker/workflow/pipeline_context.py#L47 and
# https://github.com/aws/sagemaker-python-sdk/blob/e7595a5e0839313d38a87ed0c944739406357a95/src/sagemaker/workflow/pipeline_context.py#L26

# Initialization of FrameworkProcessor
# ------------------------------------
class InitArgs(TypedDict):
    """kwargs for instantiating *Framework*Processor."""
    framework_version: str
    estimator_cls: type[SKLearn] # todo: extend to support more estimators (ideally find supertype)
    instance_count: int
    instance_type: str
    role: str
    sagemaker_session: Session


class _InitConfig(TypedDict):
    framework_version: str
    estimator_cls_name: str
    instance_count: int
    instance_type: str


# Arguments for *running* FrameworkProcessor
# ------------------------------------------
class RunArgs(TypedDict):
    """Kwargs for *Framework*Processor.run()."""
    code: str
    source_dir: str
    inputs: list[ProcessingInput]
    outputs: list[ProcessingOutput]


class _RunConfig(TypedDict):
    code: str
    source_dir: str
    # todo: allow athena datasetdefinition instead
    input_files_s3paths: list[S3Path]  # todo: validate it's an s3 path
    output_files_s3paths: list[S3Path]  # todo: validate it's an s3 path


# Combining configs into single config for the step
# ==================================================

class StepConfig(BaseSettings):
    """
    Note that it would be more explicit to call this a *FrameworkProcessing*StepConfig. However, to avoid this tedious naming, we go with the shorter name – which is unambiguous within the module namespace anyway.
    """
    # todo:
    step_name: str
    step_factory_class: str
    processor_init_config: _InitConfig
    processor_run_config: _RunConfig
    # For now, we will reload this for every step config to avoid dependency on pipeline wrapper.
    shared_config: SharedConfig


# Impementation of StepFactory
# ============================

class StepFactory(StepFactoryInterface):
    _local_dir: ClassVar = Path('/opt/ml/processing')
    # Note: this is a public attribute, so user can add support for additional estimators
    estimator_name_to_cls_mapping: ClassVar[dict[str, Any]] = {  # todo:  find supertype
        'SKLearn': SKLearn,
    }

    _config_model: ClassVar[type[StepConfig]] = StepConfig

    def __init__(
        self,
        # todo: should values be constrained to str to make it independent from source it's read
        #  from? (Parsing is handled by pydantic anyway.)
        step_config_dict: dict[str, Any],
        role_arn: str,
        pipeline_session: PipelineSession | LocalPipelineSession
    ):
        # Parse config, using the specific pydantic model that this factory has as a class variable.
        self._config: StepConfig = self._config_model(**step_config_dict)
        self._role_arn = role_arn
        self._pipeline_session = pipeline_session

    @property
    def processor(self) -> FrameworkProcessor:
        # Start with init args from config, but convert TypedDict to dict so we can modify keys.
        init_args: dict[str, Any] = dict(self._config.processor_init_config)
        # Replace the string of estimator_cls_name with the actual estimator_cls
        estimator_cls_name = init_args.pop('estimator_cls_name')
        init_args['estimator_cls'] = self.estimator_name_to_cls_mapping[estimator_cls_name]
        return FrameworkProcessor(
            **init_args,
            role=self._role_arn,
            sagemaker_session=self._pipeline_session,
        )  # todo: check if typechecker catches wrong args. Otherwise, define typed dict for FWPInitArgs.

    def _construct_run_args(self) -> RunArgs:
        """
        Takes config and modifies it for creating run args.  At the moment, this only involves  constructing ProcessingInputs and ProcessingOutputs.

        Note: Unfortunately we can't just pass through everything else from config except what we don't need - which would be more flexible. Unfortunately, this would require *deleting* items from the typed dict (input/output_files_s3_path), which is not possible unless we convert it to a normal (untyped) dictionary. But doing so is not a desirable  approach either, because it would cause the type checker to lose knowledge about which types *are* still in there and are thus passed through (so type checker wouldn't recognize these and would think they are missing).
        """

        # Create ProcessingInputs from list of s3paths (strings)
        _input_files_s3paths: list[S3Path] = self._config.processor_run_config['input_files_s3paths']
        _processing_inputs: list[ProcessingInput] = [
            ProcessingInput(
                input_name=str(s3path.stem), # filename without extension
                source=s3path.as_uri(),
                destination=str(self._local_dir / s3path.name), # Same filename, but in local dir
                # todo: Allow passing through extra arguments
            )
            for s3path in _input_files_s3paths
        ]

        # Do the same for ProcessingOutputs
        _output_files_s3paths: list[S3Path] = self._config.processor_run_config['output_files_s3paths']
        _processing_outputs: list[ProcessingOutput] = [
            ProcessingOutput(
                output_name=str(s3path.stem), # filename without extension
                source=str(self._local_dir / s3path.name), # Same filename, but in local dir
                destination=s3path.as_uri(),
                # todo: Allow passing through extra arguments
            )
            for s3path in _output_files_s3paths
        ]

        return RunArgs(
            # Newly constructed inputs and outputs:
            inputs=_processing_inputs,
            outputs=_processing_outputs,
            # The rest is passed through literally from configs.
            code=self._config.processor_run_config['code'],
            source_dir=self._config.processor_run_config['source_dir'],
        )

    def create_step(self) -> ProcessingStep:
        _step_args = self.processor.run(
            **self._construct_run_args()
        )
        return ProcessingStep(
            name=self._config.step_name,
            step_args=_step_args, # mypy doesn't complain, just pylance. So don't silence.
        )
