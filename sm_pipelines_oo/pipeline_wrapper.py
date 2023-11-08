from typing import Literal

from pydantic_settings import BaseSettings
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import Step

from sm_pipelines_oo.pipeline_config import BootstrapConfig, SharedConfig
from sm_pipelines_oo.utils import load_pydantic_config_from_file



class PipelineWrapper:
    def __init__(
        self,
        steps: list[Step],
        environment:  Literal['dev', 'qa', 'prod'],
        shared_config: SharedConfig,
        step_configs: list[BaseSettings],
    ) -> None:
        self.steps = steps
        self.environment = environment
        self.shared_config = shared_config
        self.step_configs = step_configs

        self.pipeline = Pipeline(
            name=self.shared_config.project_name,
            steps=self.steps,
            sagemaker_session=self.get_sagemaker_session(),
        )
