from abc import ABC, abstractmethod
from typing import Any
from functools import cached_property


class ConfigLoaderInterface(ABC):
    @cached_property
    @abstractmethod
    def shared_config_as_dict(self) -> dict[str, Any]:
        ...

    @cached_property
    @abstractmethod
    def step_configs_as_dicts(self) -> list[dict[str, Any]]:
        ...
