from abc import ABC, abstractmethod
from typing import final, Any
from pathlib import Path
from functools import cached_property

from sm_pipelines_oo.shared_config_schema import Environment


class AbstractConfigLoader():
    """
    Abstract factory for loading configs as dictionaries.
    Concrete implementations will  implement a method for how to load a given config file, as well as an attribute of which file types to load.
    This abstract class provides implementation for how to load both the shared config as well as all the steps configs.
    """

    # todo: get rid of init and implement as properties (as MockConfigLoader is initialized differently)
    def __init__(
        self,
        env: Environment,
        config_root_folder: str = 'config',  # relative path from project root
    ):
        self._env = env
        self._config_folder = Path(config_root_folder) / env

    @final
    @cached_property
    def shared_config_as_dict(self) -> dict[str, Any]:
        shared_config_path: Path = self._config_folder / f'shared_config.{self._file_type_to_load}'
        return self._load_config(shared_config_path)

    @final
    @cached_property
    def step_configs_as_dicts(self) -> list[dict[str, Any]]:
        """Traverses the config directory and returns names of all subfolders, each of which will correspond to a step name."""
        # Since we are using Path.suffix, we need to add a `.` to the file extension we are looking for.
        file_suffix_to_match = f'.{self._file_type_to_load}'
        step_config_paths: list[Path] = [
            path for path in self._config_folder.iterdir() if path.suffix == file_suffix_to_match
        ]
        return [
            self._load_config(config_path)
            for config_path in step_config_paths
        ]

    # Abstract methods that concrete implementations must implement
    # --------------------------------------------------------------
    @abstractmethod
    def _load_config(self, config_file: Path) -> dict[str, Any]:
        ...

    @property
    @abstractmethod
    def _file_type_to_load(self) -> str:
        """
        Returns file extension that identifies which files in config directory should be loaded.
        """
        ...
