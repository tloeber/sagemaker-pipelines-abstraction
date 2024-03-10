import os
import pandas as pd
# from loguru import logger

INPUT_PATH = '/opt/ml/processing/input_1/input.parquet'
OUTPUT_PATH = f'/opt/ml/processing/output_1/{os.environ["OUTPUT_FILENAME"]}'

# logger.info("Starting preprocess")
df = (
    pd.read_parquet(INPUT_PATH)
    .multiply(2)
)
df.to_parquet(OUTPUT_PATH)
# logger.info('\nFinished preprocess')
