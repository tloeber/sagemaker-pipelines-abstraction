from loguru import logger
from typing import Literal
from pydantic_settings import BaseSettings

from sagemaker.workflow.pipeline import Pipeline

from sm_pipelines_oo.steps.shared_config import shared_config
from sm_pipelines_oo.steps.pre_processing import pre_process_step
from sm_pipelines_oo.steps.model_training import train_step
# from sm_pipelines_oo.steps.model_evaluation import eval_step
# from sm_pipelines_oo.steps.model_registration import condition_step

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.pipeline_config import BootstrapConfig, SharedConfig
from sm_pipelines_oo.pipeline_wrapper import PipelineWrapper


# Load configs
# ============
ENVIRONMENT: Literal['dev', 'qa', 'prod'] =  BootstrapConfig().ENVIRONMENT  # type: ignore

shared_config: BaseSettings = load_pydantic_config_from_file(
    config_cls=SharedConfig,
    env_file = f"sm_pipelines_oo/configs/{ENVIRONMENT}/.env_shared",
)


pipeline = PipelineWrapper(
    steps=[pre_process_step, train_step],
    environment=ENVIRONMENT,
    shared_config=shared_config,
    step_configs=[],
)
