"""
Run this script to set up imput data.
To perform validation, import check_output()
"""

import time

import pandas as pd
import awswrangler as wr


_PROJECT_BUCKET = 'smp-oo-example'
_DATA_PREFIX = 'examples/data/input_1'
_FILENAME = 'input.parquet'
input_path_s3 = f's3://{_PROJECT_BUCKET}/{_DATA_PREFIX}/{_FILENAME}'

df = pd.DataFrame(
    {
        'a': [1, 2, 3],
        'b': [4, 5, 6],
        'c': [7, 8, 9],
    }
)
expected_sum = df.sum().sum()


def check_output(wait_time_in_minutes: int = 0):
    time.sleep(wait_time_in_minutes*60)
    df = pd.read_parquet(input_path_s3)
    assert df.sum().sum() == expected_sum
    print('Success')


if __name__ == '__main__':
    # Upload input data to S3
    wr.s3.to_parquet(
        df,
        path=input_path_s3,
    )