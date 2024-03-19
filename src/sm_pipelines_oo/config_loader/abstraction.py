from abc import abstractmethod
from typing import final, Any
from pathlib import Path
from functools import cached_property

from sm_pipelines_oo.shared_config_schema import Environment
from sm_pipelines_oo.config_loader.interface import ConfigLoaderInterface


class AbstractConfigLoader(ConfigLoaderInterface):
    """
    Abstract factory for loading configs as dictionaries.
    Concrete implementations will  implement a method for how to load a given config file, as well as an attribute of which file types to load.
    This abstract class provides implementation for how to load both the shared config as well as all the steps configs.
    """

    # todo: get rid of init and implement as properties (as MockConfigLoader is initialized differently)
    def __init__(
        self,
        env: Environment,
        config_root_folder: str = 'config',  # relative path from package root
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
        # Find all files in the config directory that match the file type we are looking for.
        # Note: Since we are using Path.suffix, we need to add a `.` to the file extension.
        file_suffix_to_match = f'.{self._file_type_to_load}'
        step_config_paths: list[Path] = [
            path for path in self._config_folder.iterdir() if (
                # Get all files with the matching extension, except for the shared config file
                (path.suffix == file_suffix_to_match) and (path.stem != 'shared_config')
            )
        ]
        # Load all files found
        step_configs: list[dict] = []
        for config_path in step_config_paths:
            step_config = self._load_config(config_path)
            # Add reference to shared config to each step config
            step_config['shared_config'] = self.shared_config_as_dict
            step_configs.append(step_config)
        return step_configs

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
