from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Any

from sagemaker.processing import Processor, FrameworkProcessor
from sagemaker.base_predictor import Predictor
from sagemaker.workflow.steps import ConfigurableRetryStep, ProcessingStep

from sm_pipelines_oo.shared_config_schema import SharedConfig

from sagemaker.session import Session, get_execution_role
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
        pipeline_session: PipelineSession | LocalPipelineSession, # todo: consider allowing normal session - probably should be separate argument though?
    ):
        ...

    # @staticmethod
    # @abstractmethod
    # def _get_config_model() -> type[BaseSettings]:
    #     """
    #     Pydantic model used to validate and convert the config_dict to an instance of pydantic.BaseSettings.
    #     """
    #     ...


    @abstractmethod
    def create_step(self) -> ConfigurableRetryStep:
        # Note that we don't have to worry about violating the LSP -  even though we are adding back an argument for the config – because at this stage that config will simply be of type dictionary. Thus, subclasses don't have to specify a more specific subtype of config here yet.
        ...
