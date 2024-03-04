import pytest
from typing import Any
from s3path import S3Path

from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession

from sm_pipelines_oo.steps.framework_processing_step import (
    StepFactory, RunArgs, _RunConfig
)


# Pairs of input and expected output
# ==================================

# Case 1: *Single* input and output
# ---------------------------------
run_args_config_dict_1: dict[str, Any] = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'input_files_s3paths': ['s3://test_bucket/input/input1.txt'],
    'output_files_s3paths': ['s3://test_bucket/output/output1.txt'],
}
expected_run_args_1: RunArgs = {
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
            source='/opt/ml/processing/output1.txt',
            destination='s3://test_bucket/output/output1.txt',
        )
    ]
}

# Case 2: *Multiple* inputs and outputs
# -------------------------------------
run_args_config_dict_2: dict[str, Any] = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'input_files_s3paths': [
        's3://test_bucket/input/input1.txt',
        's3://test_bucket/input/input2.txt',
    ],
    'output_files_s3paths': [
        's3://test_bucket/output/output1.txt',
        's3://test_bucket/output/output2.txt'
    ]
}

expected_run_args_2: RunArgs = {
    'code': 'code.py',
    'source_dir': 'code_dir/',
    'inputs': [
        ProcessingInput(
            input_name='input1',
            source='s3://test_bucket/input/input1.txt',
            destination='/opt/ml/processing/input1.txt'
        ),
        ProcessingInput(
            input_name='input2',
            source='s3://test_bucket/input/input2.txt',
            destination='/opt/ml/processing/input2.txt'
        )

    ],
    'outputs': [
        ProcessingOutput(
            output_name='output1',
            source='/opt/ml/processing/output1.txt',
            destination='s3://test_bucket/output/output1.txt'
        ),
        ProcessingOutput(
            output_name='output2',
            source='/opt/ml/processing/output2.txt',
            destination='s3://test_bucket/output/output2.txt'
        )

    ]
}


# Actual test
# ===========

@pytest.mark.parametrize(
    argnames="run_config_dict, expected_run_args",
    argvalues=[
        (run_args_config_dict_1, expected_run_args_1),
        (run_args_config_dict_2, expected_run_args_2),
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
    framework_processing_step_factory = StepFactory(
        step_config_dict=step_config_dict,
        role_arn='mock-role-arn',
        pipeline_session=LocalPipelineSession()
    )
    actual_run_args: RunArgs = \
        framework_processing_step_factory._construct_run_args()

    # Compare
    # =======
    # Note: Have to compare fields because ProcessingInput and ProcessingOutput don't have a string representation implemented. While hash is implemented, it is different even though fields are the same.
    # Note: unfortunately it's also not possible to specify the fields to compare as a list, and then iterate through it. The reason is that the processing input can't be converted to a dictionary, so we have to stick with dot notation for attribute access.

    # inputs
    # ------
    actual_inputs: list[ProcessingInput] = actual_run_args['inputs']
    expected_inputs: list[ProcessingInput] = expected_run_args['inputs']
    # Go through *list* of inputs, and for each input compare the fields
    for actual_input, expected_input in zip(actual_inputs, expected_inputs):
        assert actual_input.input_name == expected_input.input_name
        assert actual_input.source == expected_input.source
        assert actual_input.destination == expected_input.destination

    # outputs
    # -------
    # Note: Didn't combine this logic with input checking for now, but we may want to compare different fields for each in the future.
    actual_outputs: list[ProcessingOutput] = actual_run_args['outputs']
    expected_outputs: list[ProcessingOutput] = expected_run_args['outputs']
    # Go through *list* of outputs, and for each output compare the fields
    for actual_output, expected_output in zip(actual_outputs, expected_outputs):
        assert actual_output.output_name == expected_output.output_name
        assert actual_output.source == expected_output.source
        assert actual_output.destination == expected_output.destination
