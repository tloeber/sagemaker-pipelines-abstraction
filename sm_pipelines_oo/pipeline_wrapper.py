from typing import Literal, Callable, TypeAlias
from functools import cached_property

from pydantic_settings import BaseSettings
import boto3
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import LocalPipelineSession
from sagemaker.workflow.steps import Step

from sm_pipelines_oo.pipeline_config import BootstrapConfig, SharedConfig
from sm_pipelines_oo.utils import load_pydantic_config_from_file


StepFactoryFunction: TypeAlias = Callable[
    [BaseSettings, BaseSettings, Session, str],
    Step
]

class PipelineWrapper:
    def __init__(
        self,
        steps: list[tuple[StepFactoryFunction, BaseSettings]],
        environment: Literal['local', 'dev', 'qa', 'prod'],
        shared_config: SharedConfig,
    ) -> None:
        self.environment = environment
        self.shared_config = shared_config

        self.steps: list[Step] = []
        for step_factory_function, step_config in steps:
            step: Step = step_factory_function(
                shared_config=shared_config,
                step_config=step_config,
                sm_session=self._sm_session,
                role_arn=self._role_arn,
            )
            self.steps.append(step)

    @cached_property
    def _boto_session(self):
        return boto3.Session(region_name=self.shared_config.region)

    @cached_property
    def _sm_client(self):
        return self._boto_session.client("sagemaker")

    @cached_property
    def _sm_runtime_client(self):
        return self._boto_session.client("sagemaker-runtime")

    @cached_property
    def _sm_session(self):
        if self.environment == 'local':
            return LocalPipelineSession()
        else:
            return Session(
                boto_session=self._boto_session,
                sagemaker_client=self._sm_client,
                sagemaker_runtime_client=self._sm_runtime_client,
                default_bucket=self.shared_config.project_bucket,
            )

    @cached_property
    def _role_arn(self) -> str:
        """
        Wrapper around the role_arn specified in shared_config. Adds handling the case where the
        user has not specified this optional field. In this case, returns the default role.
        """
        provided_role_arn: str | None = self.shared_config.role_arn
        if provided_role_arn is None:
            return get_execution_role(self._sm_session)
        else:
            return provided_role_arn

    @cached_property
    def _pipeline(self):
        pipeline = Pipeline(
            name=self.shared_config.project_name,
            steps=self.steps,
            sagemaker_session=self._sm_session,
        )
        pipeline.create(role_arn=self._role_arn)
        return pipeline


    def run(self) -> None:
        execution = self._pipeline.start()
        execution.wait(max_attempts=120, delay=60)
