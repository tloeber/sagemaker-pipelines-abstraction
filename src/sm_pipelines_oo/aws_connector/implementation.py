# Required to not make boto3-stubs a runtime dependency: https://mypy.readthedocs.io/en/stable/runtime_troubles.html#future-annotations-import-pep-563
from __future__ import annotations
from typing import TYPE_CHECKING
from functools import cached_property

from loguru import logger
import boto3
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession
if TYPE_CHECKING:
    from mypy_boto3_sagemaker.client import SageMakerClient
    from mypy_boto3_sagemaker_runtime.client import SageMakerRuntimeClient
    from mypy_boto3_sts.client import STSClient


from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface


class AWSConnector(AWSConnectorInterface):
    """
    This is the main interface that we will use everywhere except for local runs and
    testing.

    Args:
        run_as_pipeline: Whether to use PipelineSession or normal Sagemaker session. Significance: This
            determines whether processor.run() returns `None` or pipeline step args. See
            https://github.com/aws/sagemaker-python-sdk/blob/8462f1a1975da59304da4441aea956a43deec380/src/sagemaker/processing.py#L1763
    """
    def __init__(
        self,
        environment: Environment,
        shared_config: SharedConfig,
        run_as_pipeline: bool,
    ) -> None:
        self.environment = environment
        self.shared_config = shared_config
        self.run_as_pipeline = run_as_pipeline

    @cached_property
    def _boto_session(self) -> boto3.Session:
        return boto3.Session(region_name=self.shared_config.region)

    @cached_property
    def sm_session(self) -> PipelineSession | Session:
        if self.run_as_pipeline:
            return PipelineSession(
                boto_session=self._boto_session,
                sagemaker_client=self.sm_client,
                default_bucket=self.shared_config.project_bucket_name,
            )
        # For running individual step directly (i.e. outside of pipeline)
        else:
            return Session(
                boto_session=self._boto_session,
                sagemaker_client=self.sm_client,
                sagemaker_runtime_client=self.sm_runtime_client,
                default_bucket=self.shared_config.project_bucket_name,
            )

    @cached_property
    def sm_client(self) -> SageMakerClient:
        return self._boto_session.client("sagemaker")

    @cached_property
    def sm_runtime_client(self) -> SageMakerRuntimeClient:
        return self._boto_session.client("sagemaker-runtime")

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
    def sm_session(self) -> Session:
        return LocalPipelineSession()

    @cached_property
    def sm_client(self):
        raise NotImplementedError

    @cached_property
    def sm_runtime_client(self):
        raise NotImplementedError

    @cached_property
    def role_arn(self) -> str:
        raise NotImplementedError  # type: ignore

    @cached_property
    def default_bucket(self) -> str:
        return self.sm_session.default_bucket()  # type: ignore


# Factory_method
# ==============
def create_aws_connector(
    run_as_pipeline: bool,
    environment: Environment,
    shared_config: SharedConfig
) -> AWSConnectorInterface:
    """
    Args:
    run_as_pipeline: Whether to use PipelineSession or normal Sagemaker session. Significance: This
        determines whether processor.run() returns `None` or pipeline step args. See
        https://github.com/aws/sagemaker-python-sdk/blob/8462f1a1975da59304da4441aea956a43deec380/src/sagemaker/processing.py#L1763

        Note: At this point, local runs only support using pipeline.
    """

    if environment == 'local':
        if run_as_pipeline:
            return LocalAWSConnector()
        else:
            raise NotImplementedError

    # If running on AWS
    else:
        return AWSConnector(
            environment=environment,
            shared_config=shared_config,
            run_as_pipeline=run_as_pipeline
        )
