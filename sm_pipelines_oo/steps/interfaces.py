from abc import ABC, abstractmethod

from sagemaker.workflow.steps import ProcessingStep

class StepFactoryInterface(ABC):
    @abstractmethod
    def create_step(self, shared_config) -> ProcessingStep:
        ...
