from loguru import logger
from pathlib import Path

from sagemaker.sklearn.estimator import SKLearn
from sagemaker.processing import FrameworkProcessor
from sm_pipelines_oo.shared_config_schema import SharedConfig
from sm_pipelines_oo.steps.processing import ProcessingStepFactory
# from sm_pipelines_oo.steps.model_training import train_step
# from sm_pipelines_oo.steps.model_evaluation import eval_step
# from sm_pipelines_oo.steps.model_registration import condition_step

from sm_pipelines_oo.utils import load_pydantic_config_from_file
from sm_pipelines_oo.shared_config_schema import BootstrapConfig, SharedConfig, Environment
from sm_pipelines_oo.aws_connector.interface import AWSConnectorInterface
from sm_pipelines_oo.aws_connector.implementation import create_aws_connector
from sm_pipelines_oo.pipeline_wrapper import PipelineWrapper

# Whether to run through SM Pipeline, or to run steps directly.
RUN_AS_PIPELINE = False


# Load configs
# ============
# Todo: Pipeline (Wrapper?) object should take config directory as an init argument and be able to
# load config itself, so that we don't have to do this here.
ENVIRONMENT: Environment = 'dev'  # BootstrapConfig().ENVIRONMENT  # type: ignore
logger.info(f"Loaded configs for environment: {ENVIRONMENT}")

config_path_shared = f"configs/{ENVIRONMENT}/.env_shared"
config_path_pre_processing = Path(f"configs/{ENVIRONMENT}/.env_pre_process")

# todo: fix type problem by making load_p... generic. Potentially think about making it a decorator instead?
shared_config: SharedConfig = load_pydantic_config_from_file(  # type: ignore
    config_cls=SharedConfig,
    config_path=config_path_shared,
)

# Create AWS Connector
# ====================
aws_connector: AWSConnectorInterface = create_aws_connector(
    environment=ENVIRONMENT,
    shared_config=shared_config,
    run_as_pipeline=RUN_AS_PIPELINE,
)

# Create Step Factories
# =====================
pre_processing_step_factory = ProcessingStepFactory(
    processor_cls=FrameworkProcessor,
    processor_extra_kwargs={'estimator_cls': SKLearn},
    step_config_path=config_path_pre_processing,
    aws_connector=aws_connector,
)

if RUN_AS_PIPELINE:
    pipeline = PipelineWrapper(
        step_factories=[
            pre_processing_step_factory,
        ],
        environment=ENVIRONMENT,
        shared_config=shared_config,
        aws_connector=aws_connector,
    )
    try:
        pipeline.run()
    except Exception as e:
        logger.error(e)

# Running processing step directly
else:
    pre_processor = pre_processing_step_factory.processor
    run_args = pre_processing_step_factory.get_processor_run_args(shared_config=shared_config)
    try:
        pre_processor.run(**run_args)  # type: ignore
    except Exception as e:
        logger.error(e)

logger.info('Finished')
