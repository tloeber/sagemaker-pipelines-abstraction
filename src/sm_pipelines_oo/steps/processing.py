# For Python < 3.12, don't use typing.TypedDict: https://docs.pydantic.dev/2.6/errors/usage_errors/#typed-dict-version
from typing_extensions import TypedDict
from abc import ABC, abstractmethod
import os
from pathlib import Path
from dataclasses import dataclass
from functools import cached_property

from typing import TypeAlias, Any, Generic, TypeVar, Literal, ClassVar

from loguru import logger

from sagemaker.session import Session
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.processing import Processor, FrameworkProcessor

from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.pipeline_context import _JobStepArguments
from sagemaker.workflow.entities import PipelineVariable
from sagemaker.sklearn.estimator import SKLearn
from pydantic_settings import BaseSettings

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.steps.step_utils import PathFactory
from sm_pipelines_oo.shared_config_schema import SharedConfig
from sm_pipelines_oo.pipeline_wrapper import AWSConnectorInterface
from sm_pipelines_oo.steps.interfaces import StepFactoryInterface

from sm_pipelines_oo.shared_config_schema import SharedConfig

class _FWProcessorInitConfig(TypedDict):
    framework_version: str
    estimator_cls_name: str
    instance_count: int
    instance_type: str


class _FWProcessorRunConfig(TypedDict):
    code: str
    source_dir: str
    # todo: allow athena datasetdefinition instead
    input_files_s3paths: list[Path]  # todo: validate it's an s3 path
    output_files_s3paths: list[Path]  # todo: validate it's an s3 path


class FrameworkProcessingStepConfig(BaseSettings):
    # todo:
    step_name: str
    step_factory_class: str
    processor_init_args: _FWProcessorInitConfig
    processor_run_args: _FWProcessorRunConfig
    # For now, we will reload this for every step config to avoid dependency on pipeline wrapper.
    shared_config: SharedConfig


class FrameworkProcessingStepFactory(StepFactoryInterface):
    _local_dir: ClassVar = Path('/opt/ml/processing')
    # Note: this is a public attribute, so user can add support for additional estimators
    estimator_name_to_cls_mapping: ClassVar[dict[str, Any]] = {  # todo:  find supertype
        'SKLearn': SKLearn,
    }

    _config_model: ClassVar[type[FrameworkProcessingStepConfig]] = FrameworkProcessingStepConfig

    def __init__(
        self,
        step_config_dict: dict[str, Any],
        role_arn: str,
        pipeline_session: PipelineSession | LocalPipelineSession
    ):
        # Parse config, using the specific pydantic model that this factory has as a class variable.
        self._config: FrameworkProcessingStepConfig = self._config_model(**step_config_dict)
        self._role_arn = role_arn
        self._pipeline_session = pipeline_session

    @property
    def processor(self) -> FrameworkProcessor:
        # Start with init args from config, but convert TypedDict to dict so we can modify keys.
        init_args: dict[str, Any] = dict(self._config.processor_init_args)
        # Replace the string of estimator_cls_name with the actual estimator_cls
        estimator_cls_name = init_args.pop('estimator_cls_name')
        init_args['estimator_cls'] = self.estimator_name_to_cls_mapping[estimator_cls_name]
        return FrameworkProcessor(
            **init_args,
            role=self._role_arn,
            sagemaker_session=self._pipeline_session,
        )  # todo: check if typechecker catches wrong args. Otherwise, define typed dict for FWPInitArgs.

    def _construct_run_args(self) -> dict[str, Any]:
        # Start with init args from config, but convert TypedDict to dict so we can modify keys.
        run_args: dict[str, Any] = dict(self._config.processor_run_args)

        # Create ProcessingInputs from list of s3paths (strings)
        _input_files_s3paths: list[Path] = run_args.pop('input_files_s3paths')
        _processing_inputs: list[ProcessingInput] = [
            ProcessingInput(
                input_name=str(s3path.stem), # filename without extension
                source=str(s3path),
                destination=str(self._local_dir / s3path.name),
                # todo: Allow passing through extra arguments
            )
            for s3path in _input_files_s3paths
        ]
        run_args['inputs'] = _processing_inputs

        # Do the same for ProcessingOutputs
        _output_files_s3paths: list[str] = run_args.pop('output_files_s3paths')
        _processing_outputs: list[ProcessingOutput] = [
            ProcessingOutput(
                source=s3path,
                # todo: Allow passing through extra arguments
            )
            for s3path in _output_files_s3paths
        ]

        run_args['outputs'] = _processing_outputs
        return run_args

    def create_step(self) -> ProcessingStep:
        _step_args = self.processor.run(
            **self._construct_run_args()
        )
        return ProcessingStep(
            name=self._config.step_name,
            step_args=_step_args,
        )
