import subprocess
from pathlib import Path

from loguru import logger
from s3path import S3Path
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ConfigurableRetryStep

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.steps.step_factory_facade import StepFactoryFacade
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface
from sm_pipelines_oo.aws_connector.implementation import create_aws_connector
from sm_pipelines_oo.config_loader.abstraction import AbstractConfigLoader
from sm_pipelines_oo.config_loader.implementations import YamlConfigLoader

# Dev dependencies
from sm_pipelines_oo.utils import run_aws_cli_cmd

class PipelineFacade:
    def __init__(
        self,
        env: Environment,
        config_loader: AbstractConfigLoader | None = None,
    ):
        """
        High level interface for using this library. For custom needs, you can use this as a template for your own implementation.
        """
        self._env: Environment = env # Added type hint to satisfy IDE's type checker
        # Allows providing a different config loader, especially for testing
        self._user_provided_config_loader = config_loader

        # Derived attributes
        # ------------------
        self._shared_config = SharedConfig(
            **self._config_loader.shared_config_as_dict
        )
        self.pipeline_name = \
            f'{self._shared_config.project_name}-v{self._shared_config.project_version}'

        self.aws_connector: AWSConnectorInterface = create_aws_connector(
            shared_config=self._shared_config,
            environment=env,
        )
        # todo: Any reason to make facade an attribute instead? (Would it make class diagram more clear, or can we still say that pipeline façade "has a" step factory façade,  even if you don't save it past initialization)?
        _step_factory_facade = StepFactoryFacade(
            step_config_dicts=self._config_loader.step_configs_as_dicts, # todo: pass in method call again?
            role_arn=self.aws_connector.role_arn,
            pipeline_session=self.aws_connector.pipeline_session,
        )
        _steps: list[ConfigurableRetryStep] = _step_factory_facade.create_all_steps()

        self._pipeline = Pipeline(
            name=self.pipeline_name,
            # parameters=[],
            steps=_steps,
            sagemaker_session=self.aws_connector.pipeline_session,
        )

    def export_pipeline_definition_to_s3(self) -> S3Path:
        """
        Exports pipeline definition to JSON and writes it to S3.
        Returns s3 uri of the file, for use by downstream tasks, such as terraform.
        """
        local_path = Path(f'/var/tmp/{self.pipeline_name}-definition.json')
        with local_path.open(mode='w') as file:
            file.write(self._pipeline.definition())

        # Upload to S3
        s3_path: S3Path = (
            self._shared_config.project_bucket /
            f'pipeline_definitions/{self.pipeline_name}-definition.json'
        )
        self.aws_connector.s3_client \
            .upload_file(
                Filename=str(local_path),
                Bucket=s3_path.bucket,
                Key=s3_path.key,
            )
        logger.info(f'Uploaded pipeline definition to {s3_path.as_uri()}')
        return s3_path


    @property
    def _config_loader(self) -> AbstractConfigLoader:
        if self._user_provided_config_loader is not None:
            return self._user_provided_config_loader
        else:
            # todo: Should be in check lists, so we don't depend on a concrete class?
            return YamlConfigLoader(env=self._env)


class DevPipelineFacade(PipelineFacade):
    """Adds additional methods to pipeline façade that are only needed for development."""

    def create_and_start_pipeline_from_definition(self) -> None:
        """
        After exporting JSON definition to S3,  use AWS CLI to create and start pipeline.

        Requires AWS CLI to be installed and configured.
        """

        def _create_pipeline(s3_location: S3Path) -> None:
            run_aws_cli_cmd(
                cmd=[
                    'aws', 'sagemaker', 'create-pipeline',
                    '--pipeline-name', self.pipeline_name,
                    '--pipeline-definition-s3-location',
                        f'Bucket={s3_location.bucket},ObjectKey={s3_location.key}',
                    '--role-arn', self.aws_connector.role_arn,
                ]
            )

        def _update_pipeline(s3_location: S3Path) -> None:
            run_aws_cli_cmd(
                cmd=[
                    'aws', 'sagemaker', 'update-pipeline',
                    '--pipeline-name', self.pipeline_name,
                    '--pipeline-definition-s3-location',
                        f'Bucket={s3_location.bucket},ObjectKey={s3_location.key}',
                    '--role-arn', self.aws_connector.role_arn,
                ]
            )

        def _start_pipeline() -> None:
            run_aws_cli_cmd(
                cmd=[
                    'aws', 'sagemaker', 'start-pipeline-execution',
                    '--pipeline-name', self.pipeline_name,
                ]
            )

        # Write definition to S3
        s3_location: S3Path = self.export_pipeline_definition_to_s3()

        try:
            _create_pipeline(s3_location)
        except Exception as e:
            _update_pipeline(s3_location)

        _start_pipeline()

    def create_and_run(self) -> None:
        """Deprecated. Use `create_and_run_from_definition()` instead."""
        self._pipeline.upsert(
            role_arn=self.aws_connector.role_arn,
        )
        execution = self._pipeline.start()
        execution.describe()
