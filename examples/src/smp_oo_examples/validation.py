"""
todo: refactor into a class.
"""

import time

import pandas as pd
import awswrangler as wr

from smp_oo_examples.worker_code.preprocess.preprocess import transform


def setup_input(input_path_s3: str):
    """Run this *before* pipeline."""
    df_in = _create_input()
    _upload_input(df_in, s3_path=input_path_s3)
    expected_df_out = transform(df_in)
    return {
        'input': df_in,
        'expected_output': expected_df_out
    }


def check_output(
    df_in: pd.DataFrame,
    output_path_s3: str,
    wait_time_in_minutes: int = 0,
    max_age_minutes: int = 15,
) -> None:
    """Run this *after* pipeline."""
    # Wait if job has been triggered asyncronously
    time.sleep(wait_time_in_minutes*60)

    # Download output data from S3
    df_out = pd.read_parquet(output_path_s3)
    print(df_out)

    _validate_transform(df_in=df_in, df_out=df_out)
    _validate_date_column(df_out=df_out, max_age_minutes=max_age_minutes)


def _create_input():
    df_in = pd.DataFrame(
        {
            'a': [1, 1],
            'b': [2, 2],
        }
    )
    return df_in


def _upload_input(df, s3_path: str):
    # Upload input data to S3
    wr.s3.to_parquet(
        df,
        path=s3_path,
    )


def _validate_transform(df_in: pd.DataFrame, df_out: pd.DataFrame):
    # Check *transformation* is correct (only applied to first two columns)
    sum_input = df_in.loc[:, ['a', 'b']].sum().sum()
    expected_sum_output = sum_input * 2
    actual_sum_output =  df_out.loc[:, ['a', 'b']].sum().sum()
    assert actual_sum_output == expected_sum_output


def _validate_date_column(df_out: pd.DataFrame, max_age_minutes=15):
    """
    Makes sure we're not dealing with data from previous iteration.
    Adjust max_age_minutes according to time it takes to run the pipeline.
    """
    current_datetime = pd.Timestamp.now(tz='UTC')
    # Note we need to use the *output* here, as we want to check we're checking a new version of the transformed data
    datetime_of_transform = df_out.date.iloc[0]
    max_allowed_timedelta = pd.Timedelta(minutes=max_age_minutes)
    actual_timedelta = current_datetime - datetime_of_transform
    print(f'\nObserved timedelta: {actual_timedelta}')
    assert actual_timedelta < max_allowed_timedelta
