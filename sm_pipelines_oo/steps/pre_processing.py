import os
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import TypedDict
from loguru import logger
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.entities import PipelineVariable
from pydantic_settings import BaseSettings

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.pipeline_config import ENVIRONMENT, SharedConfig

import sm_pipelines_oo.sagemaker_utils as su


class ProcessingConfig(BaseSettings):
    input_filename: str
    instance_type: str
    instance_count: int
    sklearn_framework_version: str
    step_name: str | None = "Process"

# Return type should be "PreProcessingConfig", but first need to refactor load_pydantic...() to use
# the more specific return type. (See ToDo at function definition.)
pre_processing_config: BaseSettings = load_pydantic_config_from_file(
    config_cls=ProcessingConfig,
    env_file=f"sm_pipelines_oo/configs/{ENVIRONMENT}/.env_pre_processing",
)

# class RunArgs(ABC):
#     """This serves as an abstract supertype for all permissible concrete types of RunArgs."""
#     @abstractmethod
#     def as_dict():
#         """
#         Don't have to implement this ourselves if we use a dataclass, which already contains this
#         method.
#         """
#         ...


# @dataclass
class SKLearnProcessorRunArgs(TypedDict):
    inputs: list[ProcessingInput]
    outputs: list[ProcessingOutput]
    code: str
    arguments: list[str | PipelineVariable] | None

# Register SKLearnProcessorRunArgs as a virtual subclass of RunArgs
# RunArgs.register(SKLearnProcessorRunArgs)

class StepFactoryInterface(ABC):
    @abstractmethod
    def create_step(step_config, shared_config) -> ProcessingStep: ...


# For now, I need to explicitly add each factory here to "register" it.
# Preferably, we would make registration possible where a new class is defined. Tried using virtual
# subclassing, but this did not play well with type checker.
# Todo: Try using generics.
StepFactory: TypeAlias = ProcessingStepFactory

class ProcessingStepFactory:
    def __init__(
        self,
        processor_cls,
    ):
        self._processor_cls = processor_cls
        self._processor: SKLearnProcessor | None = None


    def _create_processor(self, step_config, shared_config) -> None:
        """
        Instantiate processor, combining shared and step-specific configurations.

        Note that this can only be run from the PipelineWrapper, because this factory does not have
        access to the step- or shared configs. (This is why it is not run in __init__().)
        """
        processor_args = {
            **step_config.to_dict(),
            'sagemaker_session': shared_config.sm_session,
            'role': shared_config.role_arn,
        }
        self._processor: SKLearnProcessor = self._processor_cls(**processor_args)

    def _get_run_args(self, step_config, shared_config) -> SKLearnProcessorRunArgs:
        input_path_s3 = f"s3://{shared_config.project_bucket}/{step_config.step_name}/{step_config.input_filename}"
        skl_run_args = SKLearnProcessorRunArgs(
            inputs = [
                ProcessingInput(
                    source=input_path_s3,
                    destination=f"/opt/ml/{step_config.step_name}/input"
                ),
            ],
            outputs = [
                ProcessingOutput(
                    output_name="train",
                    source=f"/opt/ml/{step_config.step_name}/train"
                ),
                ProcessingOutput(
                    output_name="validation",
                    source=f"/opt/ml/{step_config.step_name}/validation"
                ),
                ProcessingOutput(
                    output_name="test",
                    source=f"/opt/ml/{step_config.step_name}/test"
                ),
            ],
            code=f"../code/{step_config.step_name}.py",
            run_args = None,  # Todo: Decide whether this should come from configuration. May depend on type of step.
        )
        return skl_run_args


    def create_step(self, step_config, shared_config) -> ProcessingStep:
        """
        Note that this can only be run from the PipelineWrapper, because this factory does not have
        access to the step- or shared configs.
        """
        self._create_processor(step_config=step_config, shared_config=shared_config)
        # Tell type checker that this variable cannot be None anymore (because we ran
        # _create_processor()).
        self._processor: SKLearnProcessor

        run_args: SKLearnProcessorRunArgs = self._get_run_args(step_config=step_config, shared_config=shared_config)
        return ProcessingStep(
            name=step_config.step_name,
            step_args=self._processor.run(
                **run_args
            ),
        )
