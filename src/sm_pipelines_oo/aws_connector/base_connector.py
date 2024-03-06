from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sagemaker.local.local_session import LocalSession
from sagemaker.session import Session
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession

# if TYPE_CHECKING:
from mypy_boto3_sagemaker.client import SageMakerClient
from mypy_boto3_s3.client import S3Client


class AWSConnectorInterface(ABC):
    @property
    @abstractmethod
    def sm_session(self) -> Session | LocalSession:
        ...

    @property
    @abstractmethod
    def pipeline_session(self) -> PipelineSession | LocalPipelineSession:
        ...

    @property
    @abstractmethod
    def sm_client(self) -> SageMakerClient:
        ...

    @property
    @abstractmethod
    def s3_client(self) -> S3Client:
        ...

    @property
    @abstractmethod
    def role_arn(self) -> str:
        ...

    @property
    @abstractmethod
    def default_bucket(self) -> str:
        ...
