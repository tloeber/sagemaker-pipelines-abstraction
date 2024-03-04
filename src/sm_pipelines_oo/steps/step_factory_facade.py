from typing import Any, ClassVar

from loguru import logger

from sagemaker.workflow.pipeline_context import PipelineSession, LocalPipelineSession
from sagemaker.workflow.steps import ConfigurableRetryStep

from sm_pipelines_oo.steps.interfaces import StepFactoryInterface, StepFactoryFacadeInterface
from sm_pipelines_oo.steps import framework_processing_step
from sm_pipelines_oo.steps.interfaces import StepFactoryLookupTable

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

    _default_stepfactory_lookup_table: ClassVar[StepFactoryLookupTable] = {
        'FrameworkProcessor': framework_processing_step.StepFactory,
    }

    def __init__(
        self,
        step_config_dicts: list[dict[str, Any]],
        role_arn: str,
        pipeline_session: PipelineSession | LocalPipelineSession,
        # Generally, user does not set this, but it's useful for testing and custom use cases.
        custom_stepfactory_lookup_table: StepFactoryLookupTable | None = None,
    ):
        self._step_config_dicts = step_config_dicts
        self._role_arn = role_arn
        self._pipeline_session = pipeline_session
        self._custom_stepfactory_lookup_table = custom_stepfactory_lookup_table

    def _lookup_step_factory_cls(self, step_config_dict: dict[str, Any]) -> type[StepFactoryInterface]:
        """Get the right *class* of step factory for a given step (based on its config)."""
        # Get *name* of class name from config
        stepfactory_cls_name: str = step_config_dict['step_factory_class']
        # Check if user provided a custom lookup table. If not, use the default.
        stepfactory_lookup_table: StepFactoryLookupTable = (
            self._default_stepfactory_lookup_table if self._custom_stepfactory_lookup_table is None
            else self._custom_stepfactory_lookup_table
        )
        # Perform lookup
        return stepfactory_lookup_table[stepfactory_cls_name]

    def _create_individual_step(
        self,
        step_config_dict: dict[str, Any]
    ) -> ConfigurableRetryStep:
        # Look up the right stepfactory class, based on config
        StepFactory_cls: type[StepFactoryInterface] = self._lookup_step_factory_cls(step_config_dict)
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
