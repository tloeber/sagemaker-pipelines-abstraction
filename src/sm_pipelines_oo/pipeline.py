import subprocess
from pathlib import Path

from loguru import logger
from s3path import S3Path # type: ignore[import-untyped]
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ConfigurableRetryStep

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.steps.step_factory_facade import StepFactoryFacade
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface
from sm_pipelines_oo.aws_connector.implementation import create_aws_connector
from sm_pipelines_oo.config_loader.abstraction import AbstractConfigLoader
from sm_pipelines_oo.config_loader.implementations import YamlConfigLoader
from sm_pipelines_oo.steps.interfaces import StepFactoryLookupTable


class PipelineFacade:
    def __init__(
        self,
        env: Environment,
        custom_config_loader: AbstractConfigLoader | None = None,
        custom_stepfactory_lookup_table: StepFactoryLookupTable | None = None,
    ):
        """
        High level interface for using this library. For custom needs, you can use this as a template for your own implementation.
        """
        self._env: Environment = env # Added type hint to satisfy IDE's type checker
        # Allows user to provide a different config loader, especially for testing
        self._custom_config_loader = custom_config_loader
        # Allows user to specify a custom stepfactory lookup table (so they can specify in config which of their custom stepfactories to use)
        self._custom_stepfactory_lookup_table = custom_stepfactory_lookup_table

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
        # todo: Any reason to make step-factory-facade an attribute instead? (Would it make class diagram more clear, or can we still say that pipeline façade "has a" step factory façade,  even if you don't save it past initialization)?
        _step_factory_facade = StepFactoryFacade(
            step_config_dicts=self._config_loader.step_configs_as_dicts, # todo: pass in method call again?
            role_arn=self.aws_connector.role_arn,
            pipeline_session=self.aws_connector.pipeline_session,
            custom_stepfactory_lookup_table=self._custom_stepfactory_lookup_table,
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

        # Upload to S3. (Override type error caused by missing type stubs for s3path.)
        s3_path: S3Path = (
            self._shared_config.project_bucket /  # type: ignore[operator]
            f'pipeline_definitions/{self.pipeline_name}.json'
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
        if self._custom_config_loader is not None:
            return self._custom_config_loader
        else:
            # todo: Should we inject this, so we don't depend on a concrete class?
            return YamlConfigLoader(env=self._env)


class DevPipelineFacade(PipelineFacade):
    """Adds additional methods to pipeline façade that are only needed for development."""

    def upsert_pipeline(self, s3_location: S3Path) -> None:
        try:
            result = subprocess.run(
                [
                    'aws', 'sagemaker', 'create-pipeline',
                    '--pipeline-name', self.pipeline_name,
                    '--pipeline-definition-s3-location',
                        f'Bucket={s3_location.bucket},ObjectKey={s3_location.key}',
                    '--role-arn', self.aws_connector.role_arn,
                ],
                check=True, # Fail on error
            )
        except subprocess.CalledProcessError:
            logger.info('Creating pipeline failed. Trying to update it instead.')
            result = subprocess.run(
                [
                    'aws', 'sagemaker', 'update-pipeline',
                    '--pipeline-name', self.pipeline_name,
                    '--pipeline-definition-s3-location',
                        f'Bucket={s3_location.bucket},ObjectKey={s3_location.key}',
                ],
                check=False,  # Don't fail on error, so we can manually examine error msg
                capture_output=True,
            )
            # Capture error and raise it, if it still didn't work
            if result.returncode != 0:
                logger.error(result.stderr)
                raise Exception(
                    result.stderr.decode('utf-8')
                )
            else:
                logger.info('Pipeline updated successfully.')

    def _start_pipeline(self) -> None:
        result = subprocess.run(
            [
                'aws', 'sagemaker', 'start-pipeline-execution',
                '--pipeline-name', self.pipeline_name,
            ],
            check=False,  # Don't fail on error, so we can manually examine error msg
            capture_output=True,
        )
        if result.returncode != 0:
            logger.error(
                result.stderr.decode('utf-8'),
            )
            raise Exception

    def create_and_start_pipeline_from_definition(self) -> None:
        """
        After exporting JSON definition to S3,  use AWS CLI to create and start pipeline.

        Requires AWS CLI to be installed and configured.
        """

        s3_location: S3Path = self.export_pipeline_definition_to_s3()
        self.upsert_pipeline(s3_location)
        self._start_pipeline()


    # Alternative way of running pipeline
    # -----------------------------------
    def _create_and_run_pipeline_directly(self) -> None:
        """
        Use `create_and_run_from_definition()` instead, except for troubleshooting.
        """
        self._pipeline.upsert(
            role_arn=self.aws_connector.role_arn,
        )
        execution = self._pipeline.start()
        execution.describe()
