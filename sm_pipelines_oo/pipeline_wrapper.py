from typing import Literal

from pydantic_settings import BaseSettings
import boto3
from sagemaker.session import Session
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
    ) -> None:
        self.steps = steps
        self.environment = environment
        self.shared_config = shared_config

        # Derived attributes
        # ------------------
        self._boto_session = boto3.Session(region_name=self.shared_config.region)
        self._sm_client = self._boto_session.client("sagemaker")
        self._sm_runtime_client = self._boto_session.client("sagemaker-runtime")
        self._sm_session = Session(
            boto_session=self._boto_session,
            sagemaker_client=self._sm_client,
            sagemaker_runtime_client=self._sm_runtime_client,
            default_bucket=self.shared_config.project_bucket,
        )
        self.pipeline = Pipeline(
            name=self.shared_config.project_name,
            steps=self.steps,
            sagemaker_session=self._sm_session,
        )

    def run(self) -> None:
        execution = self.pipeline.start()
        execution.wait(max_attempts=120, delay=60)
