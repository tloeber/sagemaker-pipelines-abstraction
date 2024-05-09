# Required to not make boto3-stubs a runtime dependency: https://mypy.readthedocs.io/en/stable/runtime_troubles.html#future-annotations-import-pep-563
from __future__ import annotations
from typing import TYPE_CHECKING
from functools import cached_property

from loguru import logger
import boto3
from sagemaker.local.local_session import LocalSession
from sagemaker.session import Session, get_execution_role
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession

from sm_pipelines_oo.shared_config_schema import SharedConfig, Environment
from sm_pipelines_oo.aws_connector.base_connector import BaseConnector


class AWSConnector(BaseConnector):
    """
    This is the main connector that we will use everywhere except for local runs and testing.
    """

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



class LocalRunConnector(BaseConnector):
    """
    Use this to run a *Sagemaker job or pipeline* locally.
    Note, however, that this still interacts with other AWS resources, e.g. S3.
    """
    @cached_property
    def sm_session(self) -> LocalSession:
        return  LocalSession()

    @cached_property
    def pipeline_session(self) -> LocalPipelineSession:
        return LocalPipelineSession()


# Factory_method
# ==============

# todo: use class + staticmethod instead of function
def create_aws_connector(
    environment: Environment,
    shared_config: SharedConfig
) -> BaseConnector:
    """Note: At this point, local runs only support using pipeline."""

    if environment == 'local':
        return LocalRunConnector(
            environment=environment,
            shared_config=shared_config,
        )
    else:
        return AWSConnector(
            environment=environment,
            shared_config=shared_config,
        )
