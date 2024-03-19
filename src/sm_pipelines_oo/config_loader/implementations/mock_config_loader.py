from typing import Any
from functools import cached_property
from pathlib import Path

from sm_pipelines_oo.config_loader.interface import ConfigLoaderInterface


class MockConfigLoader(ConfigLoaderInterface):
    def __init__(
        self,
        shared_config_dict: dict[str, Any],
        step_configs_dicts: list[dict[str, Any]],
    ):
        self._shared_config_dict = shared_config_dict
        self._step_configs_dicts = step_configs_dicts

    # Disable type checking, because we are overwriting a `final` method with a mock implementation.
    @cached_property # type: ignore[misc]
    def shared_config_as_dict(self) -> dict[str, Any]:
        return self._shared_config_dict

    # Disable type checking, because we are overwriting a `final` method with a mock implementation.
    @cached_property # type: ignore[misc]
    def step_configs_as_dicts(self) -> list[dict[str, Any]]:
        return self._step_configs_dicts

    # The following two methods are not needed, but are required to make the class *concrete*. While we could override this with a type: `ignore[abstract]`, it is better to avoid silencing type errors if easily possible.
    @property
    def _file_type_to_load(self) -> str:
        raise NotImplementedError

    def _load_config(self, config_file: Path) -> dict[str, Any]:
        raise NotImplementedError
