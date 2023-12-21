from dataclasses import dataclass

from sm_pipelines_oo.shared_config_schema import SharedConfig
# todo: use general step config, once stable
from sm_pipelines_oo.steps.pre_processing import ProcessingConfig


# S3 Folder Paths
# ==============

@dataclass(frozen=True, kw_only=True, slots=True)
class S3InputOutputFolders:
    """
    This provides a type-safe way to pass input- and output folders between methods as a single
    object.
    """
    input_folder: str
    output_folder: str


# todo: use general step config, once stable
def get_s3_folderpaths(
        step_config: ProcessingConfig,
        shared_config: SharedConfig
) -> S3InputOutputFolders:
    """
    Construct Path to S3 folder for input and output from shared and step-specific config. If a
    custom S3 path is specified, it overrides the default path.
    """
    default_data_folder = "s3://{}/{}/{}".format(  # pylint: disable=consider-using-f-string
        shared_config.project_bucket_name,
        shared_config.project_version,
        step_config.step_name
    )
    # Use custom input folder if provided, otherwise use default
    input_folder: str = step_config.input_s3_dir or f'{default_data_folder}/input'
    output_folder: str = step_config.output_s3_dir or f'{default_data_folder}/output'

    return S3InputOutputFolders(
        input_folder=input_folder,
        output_folder=output_folder
    )


# Local Folder Paths
# =================

# todo: use general step config, once stable
def get_local_folderpath(step_config: ProcessingConfig) -> str:
    return f'/opt/ml/{step_config.step_type}/{step_config.step_name}'
