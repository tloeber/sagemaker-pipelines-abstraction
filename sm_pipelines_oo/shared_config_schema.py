"""
This file defines a schema for configs that are shared across multiple *steps* in the pipeline.

(Note that "shared" does not refer to sharing across *environments*. We are not sharing any configs
across environments to avoid the complications that would arise from adding a second dimension of
shared configuration.)
"""

from pathlib import Path
from functools import cached_property
from typing import TypeAlias, Literal
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings
import boto3
import sagemaker
import sagemaker.session
from sagemaker.workflow.pipeline_context import PipelineSession


Environment: TypeAlias = Literal['local', 'dev', 'qa', 'prod']

class BootstrapConfig(BaseSettings):
    """
    The purpose of this config is to define the environment, based on which all the other
    configuration values will be loaded.

    Note that this config will not be loaded from a .env file, but from an environment variable:
    – When deployed, the value will come from Terraform, etc.
    – For development, it could either be globally defined for all project in ~/.bashrc
      (recommended) or for just this project in the IDE.
    """
    ENVIRONMENT: Environment


class SharedConfig(BaseSettings):
    """Defines configuration shared by all pipeline steps (for a given environment)."""
    project_name: str
    # base_job_prefix: str
    region: str
    role_arn: str | None = None
    project_bucket: str | None = None
    project_version: str | None = None
