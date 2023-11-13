from typing import Literal, Callable, TypeAlias
from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings
import boto3
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import LocalPipelineSession
from sagemaker.workflow.steps import Step

from sm_pipelines_oo.pipeline_config import SharedConfig, Environment
from sm_pipelines_oo.steps.pre_processing import StepFactory


class AWSConnector:
    def __init__(
        self,
        environment: Environment,
        shared_config: SharedConfig,
    ) -> None:
        self.environment = environment
        self.shared_config = shared_config

    @cached_property
    def _boto_session(self):
        return boto3.Session(region_name=self.shared_config.region)

    @cached_property
    def sm_session(self) -> Session | LocalPipelineSession:
        if self.environment == 'local':
            return LocalPipelineSession()
        else:
            return Session(
                boto_session=self._boto_session,
                sagemaker_client=self.sm_client,
                sagemaker_runtime_client=self.sm_runtime_client,
                default_bucket=self.shared_config.project_bucket,
            )

    @cached_property
    def sm_client(self):
        return self._boto_session.client("sagemaker")

    @cached_property
    def sm_runtime_client(self):
        return self._boto_session.client("sagemaker-runtime")

    @cached_property
    def role_arn(self) -> str:
        """
        Wrapper around the role_arn specified in shared_config. Adds handling the case where the
        user has not specified this optional field. In this case, returns the default role.
        """
        provided_role_arn: str | None = self.shared_config.role_arn
        if provided_role_arn is None:
            return get_execution_role(self.sm_session)
        else:
            return provided_role_arn


class PipelineWrapper:
    def __init__(
        self,
        step_factories: list[StepFactory],
        environment: Environment,
        shared_config: SharedConfig,
        aws_connector: AWSConnector,
    ) -> None:
        self.environment = environment
        self.shared_config = shared_config
        self._aws_connector = aws_connector

        self.steps: list[Step] = []
        self._create_steps(step_factories, shared_config)

    def _create_steps(self, step_factories: list[StepFactory], shared_config: SharedConfig) -> None:
        for factory in step_factories:
            step: Step = factory.create_step(
                shared_config=shared_config,
            )
            self.steps.append(step)

    @cached_property
    def _pipeline(self):
        pipeline = Pipeline(
            name=self.shared_config.project_name,
            steps=self.steps,
            sagemaker_session=self._aws_connector.sm_session,
        )
        pipeline.create(role_arn=self._aws_connector.role_arn)
        return pipeline


    # Public methods
    # ==============

    def run(self) -> None:
        execution = self._pipeline.start()
        execution.wait(max_attempts=120, delay=60)
