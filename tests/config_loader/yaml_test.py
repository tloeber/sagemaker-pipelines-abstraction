from pathlib import Path
from sm_pipelines_oo.config_loader.implementations.file_loaders import YamlConfigLoader


# Use *relative* path from this file, so we can move this folder if necessary
# (Otherwise path is from package root.)
CONFIG_PATH = Path(__file__).parent / 'config_files/'
expected_shared_config = {
    'project_name': 'test',
    'project_version': '0.0',
    'region': 'us-east-1',
    'project_bucket_name': 'smp-oo-test',
    'role_name': 'sagemaker_pipelines_role'
}
expected_preprocessing_config = {
    'step_name': 'preprocessing',
    'step_factory_class': 'FrameworkProcessor',
    'processor_init_config': {
        'framework_version': '0.23-1',
        'estimator_cls_name': 'SKLearn',
        'instance_count': 1,
        'instance_type': 'ml.m5.xlarge',
        'env': {'OUTPUT_FILENAME': 'output.csv'},
    },
    'processor_run_config': {
        'code': 'preprocess.py',
        'source_dir': 'worker_code/preprocess',
        'inputs': {
            'input_1': 's3://smp-oo-test/examples/data/input_1',
        },
        'outputs': {
            'output_1': 's3://smp-oo-test/examples/data/output_1'},
    },
    'shared_config': expected_shared_config
}


def test_load_yaml_config():
    # Arrange
    loader = YamlConfigLoader(
        env='dev',
        config_root_folder=str(CONFIG_PATH),
    )

    # Act
    shared_config = loader.shared_config_as_dict
    step_configs = loader.step_configs_as_dicts

    # Assert
    assert shared_config == expected_shared_config
    assert step_configs == [expected_preprocessing_config]
