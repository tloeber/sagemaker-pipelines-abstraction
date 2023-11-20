from loguru import logger
from typing import Literal
from pydantic_settings import BaseSettings
from pathlib import Path

from sagemaker.workflow.pipeline import Pipeline
from sagemaker.sklearn.processing import SKLearnProcessor

from sm_pipelines_oo.shared_config_schema import SharedConfig
from sm_pipelines_oo.steps.pre_processing import ProcessingStepFactory
# from sm_pipelines_oo.steps.model_training import train_step
# from sm_pipelines_oo.steps.model_evaluation import eval_step
# from sm_pipelines_oo.steps.model_registration import condition_step

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.shared_config_schema import BootstrapConfig, SharedConfig, Environment
from sm_pipelines_oo.connector.interface import AWSConnectorInterface
from sm_pipelines_oo.connector.implementation import create_aws_connector
from sm_pipelines_oo.pipeline_wrapper import PipelineWrapper


# Load configs
# ============
# Todo: Pipeline (Wrapper?) object should take config directory as an init argument and be able to
# load config itself, so that we don't have to do this here.
ENVIRONMENT: Environment = BootstrapConfig().ENVIRONMENT  # type: ignore
logger.info(f"Loaded configs for environment: {ENVIRONMENT}")

config_path_shared = f"configs/{ENVIRONMENT}/.env_shared"
config_path_pre_processing = Path(f"configs/{ENVIRONMENT}/.env_pre_process")

# todo: fix type problem by making load_p... generic. Potentially think about making it a decorator instead?
shared_config: SharedConfig = load_pydantic_config_from_file(  # type: ignore
    config_cls=SharedConfig,
    config_path=config_path_shared,
)

# Create AWS Connector
# ====================
aws_connector: AWSConnectorInterface = create_aws_connector(
    environment=ENVIRONMENT,
    shared_config=shared_config,
)

# Create Step Factories
# =====================
pre_processing_step_factory = ProcessingStepFactory(
    processor_cls=SKLearnProcessor,
    step_config_path=config_path_pre_processing,
    aws_connector=aws_connector,
)


# Running processing step directly
# ================================

proccessing_step = pre_processing_step_factory.create_step(
    shared_config=shared_config,
)
pre_processor = pre_processing_step_factory.processor
run_args = pre_processing_step_factory._get_run_args(shared_config=shared_config)
pre_processor.run(**run_args)


# # Create Pipeline
# # ===============
pipeline = PipelineWrapper(
    step_factories=[
        pre_processing_step_factory,
    ],
    environment=ENVIRONMENT,
    shared_config=shared_config,
    aws_connector=aws_connector,
)


# # Run Pipeline
# # =============
# pipeline.run()
