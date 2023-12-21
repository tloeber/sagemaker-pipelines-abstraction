import pytest
from pathlib import Path

from sm_pipelines_oo.steps.step_utils import DataLocations
from sm_pipelines_oo.shared_config_schema import SharedConfig
from sm_pipelines_oo.steps.pre_processing import ProcessingConfig


@pytest.fixture
def shared_config() -> SharedConfig:
    return SharedConfig(
        project_name="test",
        project_version='v0.0',  # Versions data (and probably more in the future)
        region='us-east-1',
        role_name='test_role',
        project_bucket_name='test-bucket',
    )


@pytest.fixture
def processing_config() -> ProcessingConfig:
    return ProcessingConfig(
        input_filename='input.parquet',
        output_train_filename='train.parquet',
        output_val_filename='val.parquet',
        output_test_filename='test.parquet',
        instance_type='ml.m5.large',
        instance_count=2,
        sklearn_framework_version='0.23-1',
        step_type="processing",
        step_name="testing_preprocessing",

        input_s3_dir=None,
        output_s3_dir=None,
    )


def test_default_s3_data_folder(
        processing_config: ProcessingConfig,
        shared_config: SharedConfig,
):
    data_locations = DataLocations(processing_config, shared_config)
    expected_path = 's3://test-bucket/v0.0/testing_preprocessing'
    assert data_locations._default_s3_data_folder == expected_path


def test_s3_input_folder(
        processing_config: ProcessingConfig,
        shared_config: SharedConfig,
):
    data_locations = DataLocations(processing_config, shared_config)
    expected_path = 's3://test-bucket/v0.0/testing_preprocessing/input'
    assert data_locations.s3_input_folder == expected_path


def test_s3_output_folder(
        processing_config: ProcessingConfig,
        shared_config: SharedConfig,
):
    data_locations = DataLocations(processing_config, shared_config)
    expected_path = 's3://test-bucket/v0.0/testing_preprocessing/output'
    assert data_locations.s3_output_folder == expected_path


def test_local_folderpath(
        processing_config: ProcessingConfig,
        shared_config: SharedConfig,
):
    data_locations = DataLocations(processing_config, shared_config)
    expected_path = '/opt/ml/processing/testing_preprocessing'
    assert data_locations.local_folderpath == expected_path
