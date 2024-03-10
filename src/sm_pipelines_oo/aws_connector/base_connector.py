from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from functools import cached_property

from loguru import logger
import boto3
from sagemaker.local.local_session import LocalSession
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface

# if TYPE_CHECKING:
from mypy_boto3_sagemaker.client import SageMakerClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_sagemaker_runtime.client import SageMakerRuntimeClient
from mypy_boto3_sts.client import STSClient


class BaseConnector(AWSConnectorInterface):
    """
    ABC that only implments methods shared between "normal" and local AWSConnector.
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
    def _sm_runtime_client(self) -> SageMakerRuntimeClient:
        """For invoking endpoints."""
        return self._boto_session.client("sagemaker-runtime")

    @cached_property
    def sm_client(self) -> SageMakerClient:
        return self._boto_session.client("sagemaker")

    @cached_property
    def s3_client(self) -> S3Client:
        return self._boto_session.client("s3")

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

    # Abstract methods
    # ================

    @property
    @abstractmethod
    def sm_session(self) -> Session | LocalSession:
        ...

    @property
    @abstractmethod
    def pipeline_session(self) -> PipelineSession | LocalPipelineSession:
        ...
