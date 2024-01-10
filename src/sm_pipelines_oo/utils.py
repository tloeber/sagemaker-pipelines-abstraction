from pathlib import Path
from pydantic import ValidationError
from pydantic_settings import BaseSettings
from loguru import logger

# todo (first): Make return type more specific, because we know it will be a specific subtype of
#  BaseSettings, namely config_cls. Potential solution: Make this function generic in
#  config_cls (constrained by BaseSettings)?
# todo (second): check if we can use decorator pattern to avoid load_pydantic_config_from_file().
def load_pydantic_config_from_file(
        config_cls: type[BaseSettings],
        config_path: str,  # todo: Make this a Path
) -> BaseSettings:
    """Load settings from a .env file."""
    try:
        return config_cls(_env_file=config_path)

    except ValidationError as e:
        absolute_config_path = Path(config_path).resolve()
        if not absolute_config_path.is_file():
            logger.exception(
                f"Failed to load {config_cls.__name__} because the following file does not exist:"
                f"{absolute_config_path}.\n\nCurrent directory: {Path.cwd()}\n\nError: {e}"
            )

        raise e
