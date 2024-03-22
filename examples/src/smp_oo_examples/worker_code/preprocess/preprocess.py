import os
import pandas as pd
# from loguru import logger


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Double all values in DataFrame and add current date."""
    return df \
        .multiply(2) \
        .assign(date=pd.Timestamp.now(tz='UTC'))


if __name__ == '__main__':
    INPUT_PATH = '/opt/ml/processing/input_3/input.parquet'
    OUTPUT_PATH = f'/opt/ml/processing/output_1/{os.environ["OUTPUT_FILENAME"]}'

    # logger.info("Starting preprocess")
    df_in = pd.read_parquet(INPUT_PATH)
    df_out = transform(df_in)
    df_out.to_parquet(OUTPUT_PATH)
    # logger.info('\nFinished preprocess')
