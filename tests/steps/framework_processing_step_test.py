import pytest
from typing import Any
from pathlib import Path

from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession

from sm_pipelines_oo.steps.framework_processing_step import (
    FrameworkProcessingStepFactory, FrameworkProcessorRunArgs, _FWProcessorRunConfig
)


# Pairs of input and expected output
# ==================================

# Case 1: *Single* input and output
# ---------------------------------
run_args_config_dict_1: dict[str, Any] = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'input_files_s3paths': [Path('s3://test_bucket/input/input1.txt')],
    'output_files_s3paths': [Path('s3://test_bucket/output/output1.txt')],
}
expected_run_args_1: FrameworkProcessorRunArgs = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'inputs': [
        ProcessingInput(
            input_name='input1',
            source='s3://test_bucket/input/input1.txt',
            destination='/opt/ml/processing/input1.txt'
        )
    ],
    'outputs': [
        ProcessingOutput(
            output_name='output1',
            source='s3://test_bucket/output/output1.txt'
        )
    ]
}

# Case 2: *Multiple* inputs and outputs
# -------------------------------------
run_args_config_dict_2: dict[str, Any] = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'input_files_s3paths': [
        Path('s3://test_bucket/input/input1.txt'),
        Path('s3://test_bucket/input/input2.txt'),
        Path('s3://test_bucket/input/input3.txt'),
    ],
    'output_files_s3paths': [
        Path('s3://test_bucket/output/output2.txt')
    ]
}

expected_run_args_2: FrameworkProcessorRunArgs = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'inputs': [
        ProcessingInput(
            input_name='input1',
            source='s3://test_bucket/input/input2.txt',
            destination='/opt/ml/type1/step1/input2.txt'
        )
    ],
    'outputs': [
        ProcessingOutput(
            output_name='output1',
            source='s3://test_bucket/output/output2.txt'
        )
    ]
}


# Actual test
# ===========

@pytest.mark.parametrize(
    argnames="run_config_dict, expected_run_args",
    argvalues=[
        (run_args_config_dict_1, expected_run_args_1),
        # (run_args_config_dict_2, expected_run_args_2),
    ]
)
def test_construct_processing_input_output(run_config_dict: dict[str, Any], expected_run_args):
    step_config_dict = {
        'step_name': 'testing',
        'step_factory_class': 'FrameworkProcessingStepFactory',
        # todo: create mock version and share among tests
        'processor_init_config': {
            'framework_version': '0.23-1',
            'estimator_cls_name': 'SKLearn',
            'instance_count': 2,
            'instance_type': 'ml.m5.large'
        },
        'processor_run_config': run_config_dict,
        # todo: create mock version and share among tests
        'shared_config': {
            'project_name': 'unit-testing',
            'project_version': '0',
            'region': 'us-east-1', # todo: use nonexisting region to make sure tests run locally
            'project_bucket_name': 'test-bucket',
            'role_name': 'test_role'
        }
    }
    framework_processing_step_factory = FrameworkProcessingStepFactory(
        step_config_dict=step_config_dict,
        role_arn='mock-role-arn',
        pipeline_session=LocalPipelineSession()
    )
    actual_run_args: FrameworkProcessorRunArgs = \
        framework_processing_step_factory._construct_run_args()
    assert actual_run_args['inputs'][0].input_name == expected_run_args['inputs'][0].input_name
