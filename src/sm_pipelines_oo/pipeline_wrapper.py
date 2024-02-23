from loguru import logger
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ConfigurableRetryStep

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.steps.step_factory_facade import StepFactoryFacade
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface
from sm_pipelines_oo.aws_connector.implementation import create_aws_connector
from sm_pipelines_oo.config_loader.abstraction import AbstractConfigLoader

class PipelineFacade:
    def __init__(
        self,
        env: Environment,
        config_loader: AbstractConfigLoader | None = None,
    ):
        self._env = env
        # Allows providing a different config loader, especially for testing
        self._user_provided_config_loader = config_loader

        # Derived attributes
        # ------------------
        self._shared_config = SharedConfig(
            **self._config_loader.shared_config_as_dict
        )
        self.aws_connector: AWSConnectorInterface = create_aws_connector(
            shared_config=self._shared_config,
            environment=env,
        )
        # todo: how can we depend on an abstraction instead?
        self.step_factory_facade = StepFactoryFacade(
            step_config_dicts=self._config_loader.step_configs_as_dicts, # todo: pass in method call again?
            role_arn=self.aws_connector.role_arn,
            pipeline_session=self.aws_connector.pipeline_session,
        )

    @property
    def _config_loader(self) -> AbstractConfigLoader:
        if self._user_provided_config_loader is not None:
            return self._user_provided_config_loader
        else:
            # todo: Should be in check lists, so we don't depend on a concrete class?
            return YamlConfigLoader(env=self._env)

    def run(self) -> None:
        """This is the main way user will interact with this class."""
        self._pipeline.upsert(
            role_arn=self.aws_connector.role_arn,
        )

    @property
    def _pipeline(self):
        steps: list[ConfigurableRetryStep] = self.step_factory_facade.create_all_steps()
        return Pipeline(
            name=self._shared_config.project_name,
            # parameters=[],
            steps=steps,
            sagemaker_session=self.aws_connector.pipeline_session,
        )
