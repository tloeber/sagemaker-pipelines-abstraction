# Required to not make boto3-stubs a runtime dependency: https://mypy.readthedocs.io/en/stable/runtime_troubles.html#future-annotations-import-pep-563
from __future__ import annotations
from typing import TYPE_CHECKING
from functools import cached_property

from loguru import logger
import boto3
from sagemaker.local.local_session import LocalSession
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession
if TYPE_CHECKING:
    from mypy_boto3_sagemaker.client import SageMakerClient
    from mypy_boto3_sagemaker_runtime.client import SageMakerRuntimeClient
    from mypy_boto3_sts.client import STSClient
    from mypy_boto3_s3.client import S3Client

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface


class AWSConnector(AWSConnectorInterface):
    """
    This is the main connector that we will use everywhere except for local runs and testing.
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

    # @cached_property
    # def _sm_runtime_client(self) -> SageMakerRuntimeClient:
    #     """For invoking endpoints."""
    #     return self._boto_session.client("sagemaker-runtime")

    @cached_property
    def sm_client(self) -> SageMakerClient:
        return self._boto_session.client("sagemaker")

    @cached_property
    def s3_client(self) -> S3Client:
        return self._boto_session.client("s3")

    @cached_property
    def sm_session(self) -> Session:
        """
        Use for running individual step directly (i.e. outside of pipeline. Implies that a step actor's (e.g., processor's) .run() method will return `None` and actually run the step. See
            https://github.com/aws/sagemaker-python-sdk/blob/8462f1a1975da59304da4441aea956a43deec380/src/sagemaker/processing.py#L1763
        """
        return Session(
            boto_session=self._boto_session,
        )

    @cached_property
    def pipeline_session(self) -> PipelineSession:
        """
        For running pipeline. Implies that a step actor's (e.g., processor's) .run() method will return  pipeline step args rather than running the step and returning `None`. See
            https://github.com/aws/sagemaker-python-sdk/blob/8462f1a1975da59304da4441aea956a43deec380/src/sagemaker/processing.py#L1763
        """
        return PipelineSession(
            boto_session=self._boto_session,
            sagemaker_client=self.sm_client,
            # default_bucket=self.shared_config.project_bucket_name,
        )

    @cached_property
    def aws_account_id(self) -> str:
        # todo: use value in configs, if specified?
        sts_client: STSClient = boto3.client("sts")
        return sts_client.get_caller_identity()["Account"]

    @cached_property
    def role_arn(self) -> str:
        """
        - Constructs role arn from role name
        - If role name (or AWS account ID) is not set, returns default role arn.
        """
        provided_role_name: str | None = self.shared_config.role_name

        if provided_role_name is None:
            current_role =  get_execution_role(self.sm_session)
            logger.debug(f'role: {current_role}')
            return current_role
        else:
            return f'arn:aws:iam::{self.aws_account_id}:role/{provided_role_name}'

    @cached_property
    def default_bucket(self) -> str:
        return self.sm_session.default_bucket()  # type: ignore


class LocalAWSConnector(AWSConnectorInterface):
    @cached_property
    def sm_client(self):
        raise NotImplementedError

    @cached_property
    def s3_client(self) -> S3Client:
        raise NotImplementedError

    @cached_property
    def sm_session(self) -> LocalSession:
        return  LocalSession()

    @cached_property
    def pipeline_session(self) -> LocalPipelineSession:
        return LocalPipelineSession()

    @cached_property
    def role_arn(self) -> str:
        # todo: Check if you have to be authenticated to run local - if so, implement this.
        raise NotImplementedError  # type: ignore

    @cached_property
    def default_bucket(self) -> str:
        return self.sm_session.default_bucket()  # type: ignore


# Factory_method
# ==============
# todo: use class + staticmethod instead of function
def create_aws_connector(
    environment: Environment,
    shared_config: SharedConfig
) -> AWSConnectorInterface:
    """Note: At this point, local runs only support using pipeline."""

    if environment == 'local':
        return LocalAWSConnector()

    else:
        return AWSConnector(
            environment=environment,
            shared_config=shared_config,
        )
