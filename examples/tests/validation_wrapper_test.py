import pandas as pd
import pytest
from smp_oo_examples.validation import transform_except_date

# Define a simple transformation function
def multiply_by_two(df: pd.DataFrame) -> pd.DataFrame:
    return df * 2


def test_transform_except_date():
    # Apply the decorator
    decorated_multiply_by_two = transform_except_date(multiply_by_two)
    current_date = pd.Timestamp.now()
    # Create a test DataFrame
    df = pd.DataFrame({
        'a': [1, 2, 3],
        'b': [4, 5, 6],
        'date': [current_date] * 3
    })

    # Apply the decorated function
    result = decorated_multiply_by_two(df)

    # Check the result
    expected = pd.DataFrame({
        'a': [2, 4, 6],
        'b': [8, 10, 12],
        'date': [current_date] * 3
    })

    pd.testing.assert_frame_equal(result, expected)
