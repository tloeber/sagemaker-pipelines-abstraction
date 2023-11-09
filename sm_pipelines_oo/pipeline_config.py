"""This file defines a config for settings that are shared by multiple steps in the pipeline."""

from pathlib import Path
from functools import cached_property
from typing import Literal
import os

from pydantic_settings import BaseSettings
import boto3
import sagemaker
import sagemaker.session
from sagemaker.workflow.pipeline_context import PipelineSession


class BootstrapConfig(BaseSettings):
    """
    The purpose of this config is to define the environment, based on which all the other
    configuration values will be loaded.

    Note that this config will not be loaded from a .env file, but from an environment variable:
    – When deployed, the value will come from Terraform, etc.
    – For development, it could either be globally defined for all project in ~/.bashrc
      (recommended) or for just this project in the IDE.
    """
    ENVIRONMENT: Literal['local', 'dev', 'qa', 'prod']


class SharedConfig(BaseSettings):
    """Defines configuration shared by all pipeline steps (for a given environment)."""
    project_name: str
    # base_job_prefix: str
    region: str
    # Todo: make the following three fields optional and use Sagemaker default if None
    role: str
    project_bucket: str
    project_prefix: str
