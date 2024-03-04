from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any, TypeAlias

from sagemaker.processing import Processor, FrameworkProcessor
from sagemaker.base_predictor import Predictor
from sagemaker.workflow.steps import ConfigurableRetryStep, ProcessingStep

from sm_pipelines_oo.shared_config_schema import SharedConfig

from sagemaker.session import Session, get_execution_role
from sagemaker.local.local_session import LocalSession
from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession


class StepFactoryFacadeInterface(ABC):
    """
    This interface decouples the pipeline façade from the specific step factory first use. The pipeline façade only cares about this one method.
    """
    @abstractmethod
    def create_all_steps(self) -> list[ConfigurableRetryStep]:
        ...


class StepFactoryInterface(ABC):
    """
    In addition to the required methods defined below, it is recommended to implement the following attributes and methods in order to make implementation of the required methods easiest:
    - _config_model: ClassVar[type[BaseSettings]] (Class used to convert config_dict to pydantic model to validate types and potentially compute derived attributes.
    """

    @abstractmethod
    def __init__(
        self,
        step_config_dict: dict[str, Any],
        role_arn: str,
        pipeline_session: PipelineSession | LocalPipelineSession,
        sm_session: Session | LocalSession | None = None,
    ):
        ...

    @abstractmethod
    def create_step(self) -> ConfigurableRetryStep:
        # Note that we don't have to worry about violating the LSP -  even though we are adding back an argument for the config – because at this stage that config will simply be of type dictionary. Thus, subclasses don't have to specify a more specific subtype of config here yet.
        ...


# Type alias for lookup table
StepFactoryLookupTable: TypeAlias = dict[str, type[StepFactoryInterface]]
