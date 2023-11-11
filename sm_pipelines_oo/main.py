from loguru import logger
from typing import Literal
from pydantic_settings import BaseSettings

from sagemaker.workflow.pipeline import Pipeline

from sm_pipelines_oo.pipeline_config import SharedConfig
from sm_pipelines_oo.steps.pre_processing import make_pre_processing_step
# from sm_pipelines_oo.steps.model_training import train_step
# from sm_pipelines_oo.steps.model_evaluation import eval_step
# from sm_pipelines_oo.steps.model_registration import condition_step

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.pipeline_config import BootstrapConfig, SharedConfig
from sm_pipelines_oo.pipeline_wrapper import PipelineWrapper


# Load configs
# ============
# Todo: Pipeline object should take config directory as an init argument and be able to load config
# itself, so that we don't have to do this here.
ENVIRONMENT: Literal['local', 'dev', 'qa', 'prod'] = BootstrapConfig().ENVIRONMENT  # type: ignore

shared_config: BaseSettings = load_pydantic_config_from_file(
    config_cls=SharedConfig,
    env_file = f"configs/{ENVIRONMENT}/.env_shared",
)


# Create Pipeline
# ===============
pipeline = PipelineWrapper(
    steps=[
        (make_pre_processing_step, pre_processing_config),
        # train_step
    ],
    environment=ENVIRONMENT,
    shared_config=shared_config,
)
