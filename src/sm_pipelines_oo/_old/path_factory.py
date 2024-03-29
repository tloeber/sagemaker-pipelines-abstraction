# Required to not make steps.preprocessing a runtime dependency, avoiding a circular import.
# See https://mypy.readthedocs.io/en/stable/runtime_troubles.html#future-annotations-import-pep-563
from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, Literal
from pathlib import Path
from functools import cached_property

from sm_pipelines_oo.shared_config_schema import SharedConfig

if TYPE_CHECKING:
    # Avoid circular import
    # todo: use general step config, once stable
    from sm_pipelines_oo.steps.framework_processing_step import ProcessingConfig


StepType: TypeAlias = Literal['processing', 'training', 'model', 'evaluation']

class PathFactory:
    # todo: use general step config, once stable.
    # todo: Add interface (or rename to distinguish from actual factory patterns)
    def __init__(self, step_config_facade: StepConfigFacade, shared_config: SharedConfig):
        self._step_config_facade = step_config_facade
        self._shared_config = shared_config

    # S3 Folder Paths
    # ===============

    @cached_property
    def _default_s3_data_folder(self) -> str:
        default_bucket_name = self._shared_config.project_bucket_name
        project_version = self._shared_config.project_version
        step_name = self._step_config_facade.step_name
        return f"s3://{default_bucket_name}/{project_version}/{step_name}"

    @cached_property
    def s3_input_folder(self) -> str:
        """
        Returns custom s3 folder with input data, if provided. Otherwise returns default s3 input
        folder.
        """
        custom_s3_folder: str | None = self._step_config_facade.input_s3_dir
        default_s3_folder = f"{self._default_s3_data_folder}/input"
        return  custom_s3_folder or default_s3_folder

    @cached_property
    def s3_output_folder(self) -> str:
        """
        Returns custom s3 folder with output data, if provided. Otherwise returns default s3 output
        folder.
        """
        custom_s3_folder: str | None = self._step_config_facade.output_s3_dir
        default_s3_folder = f'{self._default_s3_data_folder}/output'
        return  custom_s3_folder or default_s3_folder

    # Local Folder Paths
    # =================

    def get_local_folderpath(self, step_type: StepType) -> str:
        # Note that `/opt/ml/${STEP_TYPE}/` is *required* by Sagemaker.
        # todo: Use more precise type annotation? (Create type for StepType)
        step_name: str = self._step_config_facade.step_name
        return f'/opt/ml/{step_type}/{step_name}'

    @property
    def source_dir(self) -> str:
        # Hard-code source_directory name to simplify configs.
        return f"code/{self._step_config_facade.step_name}/"

    @property
    def step_code_file(self) -> str:
        # Hard-code name of step's code file to simplify configs.
        return f"{self._step_config_facade.step_name}.py"
