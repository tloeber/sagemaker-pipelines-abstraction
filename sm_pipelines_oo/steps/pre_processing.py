import os
from pathlib import Path
from dataclasses import dataclass
from functools import cached_property

from typing import TypedDict, TypeAlias, Any
from loguru import logger
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.entities import PipelineVariable
from pydantic_settings import BaseSettings

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.shared_config_schema import Environment, SharedConfig
from sm_pipelines_oo.pipeline_wrapper import AWSConnectorInterface
from sm_pipelines_oo.steps.interfaces import StepFactoryInterface

class ProcessingConfig(BaseSettings):
    input_filename: str
    instance_type: str
    instance_count: int
    sklearn_framework_version: str
    step_name: str = "Process"


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


class ProcessingStepFactory(StepFactoryInterface):
    def __init__(
        self,
        processor_cls,
        step_config_path: Path,  # Path to .env file containing configurations for this step.
        aws_connector: AWSConnectorInterface,
    ):
        self._processor_cls = processor_cls
        self.aws_connector = aws_connector
        # todo: fixed type problem by making load_p... generic. Potentially think about making it a decorator instead?
        self.step_config: ProcessingConfig = load_pydantic_config_from_file(  # type: ignore
            config_cls=ProcessingConfig,
            config_path=str(step_config_path),
        )


    def _get_run_args(self, shared_config) -> SKLearnProcessorRunArgs:
        input_path_s3 = f"s3://{shared_config.project_bucket_name}/{self.step_config.step_name}/{self.step_config.input_filename}"
        skl_run_args = SKLearnProcessorRunArgs(
            inputs = [
                ProcessingInput(
                    source=input_path_s3,
                    destination=f"/opt/ml/processing/input"
                ),
            ],
            outputs = [
                ProcessingOutput(
                    output_name="train",
                    source=f"/opt/ml/processing/train"
                ),
                ProcessingOutput(
                    output_name="validation",
                    source=f"/opt/ml/processing/validation"
                ),
                ProcessingOutput(
                    output_name="test",
                    source=f"/opt/ml/processing/test"
                ),
            ],
            code=f"code/{self.step_config.step_name}.py",
            arguments=None # Todo: Decide whether this should come from configuration. May depend on type of step.
        )
        return skl_run_args

    # todo: Generalize types to other processors
    @cached_property
    def processor(self) -> SKLearnProcessor:  # type: ignore
        """
        Instantiate processor, combining step-specific configs with configs from AWS connector.

        Note that we could technically run this in __init__() now, because we do no longer use
        anything from the shared_config. However, leaving it here keeps the option open to make it
        a separate method that accepts outside configs as arguments, if necessary in the future.
        """
        return self._processor_cls(
            framework_version=self.step_config.sklearn_framework_version,
            instance_type=self.step_config.instance_type,
            instance_count=self.step_config.instance_count,
            base_job_name=self.step_config.step_name,
            sagemaker_session=self.aws_connector.sm_session,
            role=self.aws_connector.role_arn,
        )  # type: ignore

    def create_step(self, shared_config: SharedConfig) -> ProcessingStep:
        """
        Note that this can only be run from the PipelineWrapper, because this factory does not have
        access to the shared configs.
        """
        processor: SKLearnProcessor = self.processor

        run_args: SKLearnProcessorRunArgs = self._get_run_args(shared_config=shared_config)
        return ProcessingStep(
            name=self.step_config.step_name,
            step_args=processor.run(
                **run_args
            ),
        )
