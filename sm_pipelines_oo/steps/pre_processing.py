import os
from pathlib import Path

from loguru import logger
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.steps import ProcessingStep
from pydantic_settings import BaseSettings

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.steps.pipeline_config import ENVIRONMENT, SharedConfig

import sm_pipelines_oo.sagemaker_utils as su


class PreProcessingConfig(BaseSettings):
    input_filename: str
    instance_type: str
    instance_count: int

# Return type should be "PreProcessingConfig", but first need to refactor load_pydantic...() to use
# the more specific return type. (See ToDo at function definition.)
pre_processing_config: BaseSettings = load_pydantic_config_from_file(
    config_cls=PreProcessingConfig,
    env_file=f"sm_pipelines_oo/configs/{ENVIRONMENT}/.env_pre_processing",
)


def make_pre_processing_step(
        shared_config: SharedConfig,
        pre_processing_config: PreProcessingConfig,
        sm_session,
        role_arn,
) -> ProcessingStep:
    sklearn_processor = SKLearnProcessor(
        framework_version="0.23-1",
        instance_type=pre_processing_config.instance_type,
        instance_count=pre_processing_config.instance_count,
        sagemaker_session=sm_session,
        role=role_arn,
    )

    local_dir = Path(shared_config.base_dir_local) / "pre_processing"
    inputs = [
        ProcessingInput(
            source=f"s3://{shared_config.PROJECT_BUCKET}/preprocessing/input/{pre_processing_config.input_filename}",
            destination=str(local_dir / "input"),
        )
    ]
    outputs = [
        ProcessingOutput(output_name="train", source=str(local_dir / "train")),
        ProcessingOutput(output_name="validation", source=str(local_dir / "validation")),
        ProcessingOutput(output_name="test", source=str(local_dir / "test")),
    ]

    step_args = sklearn_processor.run(
        inputs=inputs,
        outputs=outputs,
        code='../code/pre_processing.py',
    )

    return ProcessingStep(
        name="Preprocess",
        step_args=step_args,
    )
