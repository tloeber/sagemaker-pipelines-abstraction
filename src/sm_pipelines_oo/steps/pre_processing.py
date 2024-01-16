from abc import ABC, abstractmethod
import os
from pathlib import Path
from dataclasses import dataclass
from functools import cached_property

from typing import TypedDict, TypeAlias, Any, Generic, TypeVar, Literal

from loguru import logger
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.processing import Processor, FrameworkProcessor

# from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.pipeline_context import _JobStepArguments
from sagemaker.workflow.entities import PipelineVariable
from pydantic_settings import BaseSettings

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.steps.step_utils import PathFactory
from sm_pipelines_oo.shared_config_schema import SharedConfig
from sm_pipelines_oo.pipeline_wrapper import AWSConnectorInterface
from sm_pipelines_oo.steps.interfaces import StepFactoryInterface


class ProcessingConfig(BaseSettings):
    input_filename: str
    output_train_filename: str
    output_val_filename: str
    output_test_filename: str
    instance_type: str
    instance_count: int
    sklearn_framework_version: str
    # Don't set in config. This needs to correspond to SM's convention for local folder structure.
    # todo: Make this not set-able. Use property instead?
    step_type: Literal['processing'] = "processing"
    step_name: str = "processing"
    # Ability to override default S3 bucket (and path)
    input_s3_dir: str | None = None
    output_s3_dir: str | None = None


class ProcessorRunArgs(TypedDict):
    inputs: list[ProcessingInput]
    outputs: list[ProcessingOutput]
    arguments: list[str] | None

class FrameworkProcessorRunArgs(ProcessorRunArgs):
    # Additional args for FrameworkProcessor:
    source_dir: str
    code: str


class ProcessorWrapperInterface(ABC):
    @abstractmethod
    def run(self, **RunArgs):
        pass

    @abstractmethod
    def get_run_args(self, shared_config: SharedConfig) -> ProcessorRunArgs:
        pass

class FrameworkProcessorWrapper(ProcessorWrapperInterface):
    def __init__(
        self,
        processor_cls,
        processor_extra_kwargs: dict[str, Any],
    ):
        self._processor_cls = processor_cls
        self._processor_extra_kwargs = processor_extra_kwargs

    def run(self, **FrameworkProcessorRunArgs):
        return self._processor_cls.run(**FrameworkProcessorRunArgs)

class ProcessingStepFactory(StepFactoryInterface):
    def __init__(
        self,
        processor_cls,
        processor_extra_kwargs: dict[str, Any],
        step_config_path: Path,  # Path to .env file containing configurations for this step.
        aws_connector: AWSConnectorInterface,
        path_factory: PathFactory,
    ):
        self._processor_cls = processor_cls
        self._processor_extra_kwargs = processor_extra_kwargs
        self.aws_connector = aws_connector
        # todo: fixed type problem by making load_p... generic. Potentially think about making it a decorator instead?
        self.step_config: ProcessingConfig = load_pydantic_config_from_file(  # type: ignore
            config_cls=ProcessingConfig,
            config_path=str(step_config_path),
        )
        self.path_factory = path_factory


    def get_processor_run_args(self) -> ProcessorRunArgs:
        s3_input_folder: str = self.path_factory.s3_input_folder
        s3_output_folder: str = self.path_factory.s3_output_folder
        local_folderpath: str = self.path_factory.local_folderpath

        skl_run_args = ProcessorRunArgs(
            inputs = [
                ProcessingInput(
                    source=s3_input_folder,
                    destination=f"{local_folderpath}/input/"
                ),
            ],
            outputs = [
                ProcessingOutput(
                    output_name="train",
                    source=f"/{local_folderpath}/train",
                    destination=f"{s3_output_folder}/train",
                ),
                ProcessingOutput(
                    output_name="validation",
                    source=f"/{local_folderpath}/validation",
                    destination=f"{s3_output_folder}/validation",
                ),
                ProcessingOutput(
                    output_name="test",
                    source=f"/{local_folderpath}/test",
                    destination=f"{s3_output_folder}/test",
                ),
            ],
            source_dir=self.path_factory.source_dir,
            code=self.path_factory.step_code_file,
            arguments=None # Todo: Decide whether this should come from configuration. May depend on type of step.
        )
        return skl_run_args

    # todo: Generalize types to other processors
    @cached_property
    def processor(self) -> Processor:  # type: ignore
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
            **self._processor_extra_kwargs,
        )  # type: ignore

    def create_step(self, shared_config: SharedConfig) -> ProcessingStep:
        """
        Note that this can only be run from the PipelineWrapper, because this factory does not have
        access to the shared configs.
        """
        run_args: ProcessorRunArgs = self.get_processor_run_args(shared_config=shared_config)
        step_args: _JobStepArguments = self.processor.run(**run_args)
        return ProcessingStep(
            name=self.step_config.step_name,
            step_args=step_args,  # type: ignore
        )

# class StepFactory:
#     def __init__(
#         self,
#         run_args,
#         step_args,
#         step_class,
#         step_name,
#     ):
#         self.run_args = run_args
#         self.step_args = step_args
#         self.step_class = step_class
#         self.step_name = step_name

#     def create_step(self):
#         return self.step_class(
#             name=self.step_name,
#             step_args=self.step_args,
#         )
