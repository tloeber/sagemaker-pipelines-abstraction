from functools import cached_property
from typing import Literal, Callable, TypeAlias
from pathlib import Path
from datetime import datetime

from loguru import logger
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import Step

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.steps.interfaces import StepFactoryInterface
from sm_pipelines_oo.connector.interface import AWSConnectorInterface


class PipelineWrapper:
    def __init__(
        self,
        step_factories: list[StepFactoryInterface],
        environment: Environment,
        shared_config: SharedConfig,
        aws_connector: AWSConnectorInterface,
    ) -> None:
        self.environment = environment
        self.shared_config = shared_config
        self._aws_connector = aws_connector

        self.steps: list[Step] = []
        self._create_steps(step_factories, shared_config)

    def _create_steps(self, step_factories: list[StepFactoryInterface], shared_config: SharedConfig) -> None:
        for factory in step_factories:
            step: Step = factory.create_step(
                shared_config=shared_config,
            )
            self.steps.append(step)

    @cached_property
    def _pipeline(self) -> Pipeline:
        pipeline_name = f'{self.shared_config.project_name}-{datetime.now():%Y-%m-%d-%H-%M-%S}'
        pipeline = Pipeline(
            name=pipeline_name,
            steps=self.steps,
            sagemaker_session=self._aws_connector.sm_session,
        )
        pipeline.create(role_arn=self._aws_connector.role_arn)
        return pipeline


    # Public methods
    # ==============

    def run(self) -> None:
        logger.info(f"Starting pipeline run for project {self.shared_config.project_name}")
        execution = self._pipeline.start()
        execution.wait()
        execution.list_steps()
