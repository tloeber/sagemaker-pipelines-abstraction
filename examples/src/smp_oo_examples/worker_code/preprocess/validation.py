"""
todo: refactor into a class.
"""
from __future__ import annotations

from functools import cached_property
import time
from typing import Callable
try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

import pandas as pd
import awswrangler as wr


# Type aliases
# ============
DataframeTransform: TypeAlias = Callable[[pd.DataFrame], pd.DataFrame]


# Core class
# ==========
class Validator:
    def __init__(
        self,
        input_path_s3: str,
        output_path_s3: str,
        transform: Callable[[pd.DataFrame], pd.DataFrame],
    ) -> None:
        """Instantiate this before triggering the pipeline to set up input data."""

        self._input_path_s3 = input_path_s3
        self._output_path_s3 = output_path_s3
        self._transform = transform

        # Perform setup
        # -------------
        # Save time this validation was started, so we can check the output is fresh
        self._start_date = pd.Timestamp.now(tz='UTC')
        self._upload_input(
            df=self._input_df,
            s3_path=self._input_path_s3
        )
        self.expected_df_out = self._transform(self._input_df)


    # Public methods
    # ==============

    def validate_output(
        self,
        wait_time_in_minutes: int = 0,
    ) -> None:
        """This is the main method a user will call after triggering the pipeline."""

        # Wait if job has been triggered asyncronously
        time.sleep(wait_time_in_minutes*60)

        # Download output data from S3
        actual_output_df = pd.read_parquet(self._output_path_s3)
        print(f'Actual output:\n{actual_output_df}\n\nExpected output:\n{self._expected_output_df}')


        # Perform validation
        pd.testing.assert_frame_equal(
            actual_output_df,
            self._expected_output_df,
            check_dtype=False,
        )

    # Helper methods
    # ===============
    @property
    def _input_df(self) -> pd.DataFrame:
        # Todo: Allow user to override default input df
        df_to_transform = pd.DataFrame(
            {
                'a': [1, 1],
                'b': [2, 2],
            }
        )
        return df_to_transform.assign(date=self._start_date)

    def _upload_input(self, df, s3_path: str):
        # Upload input data to S3
        wr.s3.to_parquet(
            df,
            path=s3_path,
        )

    @cached_property
    def _expected_output_df(self) -> pd.DataFrame:
        """
        Perform transformation locally, so we can compare with output from pipeline.

        Note: We exclude date column from transform, as it is just there to make sure we're notwith
        dealing results from a previous run.
        """
        # Todo: Allow user to override default output df
        # df_in_without_date: pd.DataFrame = self._input_df.drop('date')
        # df_out_without_date: pd.DataFrame = self._transform(df_in_without_date)
        # df_out: pd.DataFrame = df_out_without_date.assign(date=self._start_date)
        return  self._transform(self._input_df)


# Helper functions
# ================

def exclude_date_column_from_transform(inner_func: DataframeTransform) -> DataframeTransform:
    def wrapper_func(df_in: pd.DataFrame) -> pd.DataFrame:
        df_to_transform = df_in.drop('date', axis='columns')
        transformed_df = inner_func(df_to_transform)
        transformed_df_with_date = transformed_df.assign(date=df_in.date)
        return transformed_df_with_date

    return wrapper_func
