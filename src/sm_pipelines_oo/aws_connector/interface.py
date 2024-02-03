from abc import ABC, abstractmethod

from sagemaker.session import Session
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession


class AWSConnectorInterface(ABC):
    @property
    @abstractmethod
    def sm_session(self) -> PipelineSession | Session | LocalPipelineSession:
        ...

    @property
    @abstractmethod
    def sm_client(self):
        ...

    @property
    @abstractmethod
    def role_arn(self) -> str:
        ...

    @property
    @abstractmethod
    def default_bucket(self) -> str:
        ...
