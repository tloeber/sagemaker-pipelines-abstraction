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

from sm_pipelines_oo.utils import load_pydantic_config_from_file


class BootstrapConfig(BaseSettings):
    """
    The purpose of this config is to define the environment, based on which all the other
    configuration values will be loaded.

    Note that this config will not be loaded from a .env file, but from an environment variable:
    – When deployed, the value will come from Terraform, etc.
    – For development, it could either be globally defined for all project in ~/.bashrc
      (recommended) or for just this project in the IDE.
    """
    ENVIRONMENT: Literal['dev', 'qa', 'prod']


class PipelineConfig(BaseSettings):
    """Defines configuration shared by all pipeline steps (for a given environment)."""
    project_name: str
    # base_job_prefix: str
    region: str
    _role: str | None = None
    project_bucket: str | None = None
    project_prefix: str | None = None


if __name__ == "__main__":
    ENVIRONMENT: Literal['dev', 'qa', 'prod'] =  BootstrapConfig().ENVIRONMENT  # type: ignore

    pipeline_config: BaseSettings = load_pydantic_config_from_file(
        config_cls=PipelineConfig,
        env_file = f"sm_pipelines_oo/configs/{ENVIRONMENT}/.env_shared",
)
