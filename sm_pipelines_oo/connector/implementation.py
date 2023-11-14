from functools import cached_property

import boto3
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline_context import LocalPipelineSession

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.connector.interface import AWSConnectorInterface


class AWSConnector(AWSConnectorInterface):
    """
    This is the main interface that we will use everywhere except for local runs and
    testing.
    """
    def __init__(
        self,
        environment: Environment,
        shared_config: SharedConfig,
    ) -> None:
        self.environment = environment
        self.shared_config = shared_config

    @cached_property
    def _boto_session(self) -> boto3.Session:
        return boto3.Session(region_name=self.shared_config.region)

    @cached_property
    def sm_session(self) -> Session:
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

    @cached_property
    def default_bucket(self) -> str:
        return self.sm_session.default_bucket()  # type: ignore


class LocalAWSConnector(AWSConnectorInterface):
    @cached_property
    def sm_session(self) -> Session:
        return LocalPipelineSession()

    def sm_client(self):
        raise NotImplementedError

    def sm_runtime_client(self):
        raise NotImplementedError

    def role_arn(self) -> str:
        raise NotImplementedError  # type: ignore

    def default_bucket(self) -> str:
        return self.sm_session.default_bucket()  # type: ignore


# Factory_method
# ==============
def create_aws_connector(
    environment: Environment,
    shared_config: SharedConfig
) -> AWSConnectorInterface:

    if environment == 'local':
        return LocalAWSConnector()
    else:
        return AWSConnector(environment=environment, shared_config=shared_config)
