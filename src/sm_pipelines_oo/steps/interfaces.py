from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sagemaker.processing import Processor, FrameworkProcessor
from sagemaker.base_predictor import Predictor
from sagemaker.workflow.steps import ConfigurableRetryStep, ProcessingStep

from sm_pipelines_oo.shared_config_schema import SharedConfig


# *General* step factory interface
# ==============================
class StepFactoryInterface(ABC):
    @abstractmethod
    def create_step(self) -> ConfigurableRetryStep:
        ...


# Factory interfaces for *specific* step types
# =============================================
ProcessorType = TypeVar("ProcessorType", bound=Processor)

class ProcessingStepFactoryInterface(StepFactoryInterface, Generic[ProcessorType]):
    @abstractmethod
    def create_step(self) -> ProcessingStep:
        ...

    @abstractmethod
    def processor(self) -> ProcessorType:
        ...

    @abstractmethod
    def get_processor_run_args(self, shared_config: SharedConfig) -> dict:
        # todo: improve return type
        ...

    @abstractmethod
    def get_processor_extra_kwargs(self, shared_config: SharedConfig) -> dict:
        # todo: improve return type
        ...
