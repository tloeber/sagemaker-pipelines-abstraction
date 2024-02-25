from typing import Any, ClassVar

from loguru import logger

from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession
from sagemaker.workflow.steps import ConfigurableRetryStep

from sm_pipelines_oo.steps.interfaces import StepFactoryInterface, StepFactoryFacadeInterface
from sm_pipelines_oo.steps.framework_processing_step import FrameworkProcessingStepFactory


class StepFactoryFacade(StepFactoryFacadeInterface):
    """
    Relationship between façade and concrete factories: A pipeline will generally have a *single* instance of  this façade, which in turn will create an instance of a concrete factory for every step.

    This class serves as a façade for creating steps that abstracts the following tasks from the user:
    - It receives the configs for all steps as a list of dictionaries.
    - For each step config, it:
      - Looks up which factory it should use for creating that kind of step. To be able to do so, it has a lookup table that maps step names to factory classes. (This lookup table can be provided during instantiation of this class, but there is also a default lookup table for standard use cases.)
      - Creates an instance of that specific step factory.
      - Delegates the creation of the actual step to that specific factory.
    - Finally, it will return the resulting list containing all steps.
    """

    _default_stepfactory_lookup_table: ClassVar[dict[str, type[StepFactoryInterface]]] = {
        'FrameworkProcessor': FrameworkProcessingStepFactory,
    }

    def __init__(
        self,
        step_config_dicts: list[dict[str, Any]],
        role_arn: str,
        pipeline_session: PipelineSession | LocalPipelineSession,
        # Generally, user does not set this, but it's useful for testing and custom use cases.
        stepfactory_lookup_table: dict[str, type[StepFactoryInterface]] | None = None,
    ):
        self._step_config_dicts = step_config_dicts
        self._role_arn = role_arn
        self._pipeline_session = pipeline_session
        self._userprovided_stepfactory_lookup_table = stepfactory_lookup_table

    @property
    def _stepfactory_lookup_table(self) -> dict[str, type[StepFactoryInterface]]:
        if self._userprovided_stepfactory_lookup_table is not None:
            return self._userprovided_stepfactory_lookup_table
        else:
            return self._default_stepfactory_lookup_table

    def _create_individual_step(
        self,
        step_config_dict: dict[str, Any]
    ) -> ConfigurableRetryStep:

        # todo: extract more into the property (make it a lookup method)
        # Get the right *class* of step factory for a given step (based on its config)
        factory_cls_name: str = step_config_dict['step_factory_class']
        StepFactory_cls: type[StepFactoryInterface] = self._stepfactory_lookup_table[factory_cls_name]

        # Instantiate factory, using step config. Then create step
        step_factory: StepFactoryInterface = StepFactory_cls(
            step_config_dict=step_config_dict,
            role_arn=self._role_arn,
            pipeline_session=self._pipeline_session
        )
        return step_factory.create_step()

    def create_all_steps(self) -> list[ConfigurableRetryStep]:
        steps: list[ConfigurableRetryStep] = []
        for config in self._step_config_dicts:
            step: ConfigurableRetryStep = self._create_individual_step(config)
            steps.append(step)
        return steps
