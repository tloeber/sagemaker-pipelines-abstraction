from pathlib import Path

from loguru import logger
import pandas as pd
from sklearn.datasets import load_iris
import boto3
import awswrangler as wr

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.shared_config_schema import BootstrapConfig, SharedConfig, Environment


# Load configs
# ============
# Todo: Pipeline (Wrapper?) object should take config directory as an init argument and be able to
# load config itself, so that we don't have to do this here.
ENVIRONMENT: Environment = BootstrapConfig().ENVIRONMENT  # type: ignore
logger.info(f"Loaded configs for environment: {ENVIRONMENT}")

config_path_shared = f"configs/{ENVIRONMENT}/.env_shared"
config_path_pre_processing = Path(f"configs/{ENVIRONMENT}/.env_pre_process")

# todo: fix type problem by making load_p... generic. Potentially think about making it a decorator instead?
shared_config: SharedConfig = load_pydantic_config_from_file(  # type: ignore
    config_cls=SharedConfig,
    config_path=config_path_shared,
)


def write_parquet_to_s3(df: pd.DataFrame, path: str, **kwargs) -> None:
    # Client is needed to catch error. See https://github.com/boto/boto3/issues/1195
    s3_client = boto3.client('s3')
    try:
        wr.s3.to_parquet(
            df=iris_df,
            path=input_path_s3,
            dataset=False,
        )
    except s3_client.exceptions.NoSuchBucket as e:
        logger.error(f'Unable to write to path {path}\n\nOriginal error:\n{e}')
        raise


# s3_client = boto3.client('s3')
# s3_client.upload_file('iris.csv', 'my-bucket', 'iris.csv')

input_path_s3 = f"s3://{shared_config.project_bucket_name}/preprocess/input_data.parquet"
iris_df: pd.DataFrame = load_iris(as_frame=True).frame  # type: ignore

write_parquet_to_s3(df=iris_df, path=input_path_s3)
logger.info(f"Uploaded input data to S3")
