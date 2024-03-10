"""
This example shows how a library user can use a custom estimator with our framework processor. The reason why this is not more straightforward is that we can't easily pass the estimator_to_cls_mappnig as an argument to constructor, because this would violate the common interface that other stepfactories implement (which don't have a need for this second level of customization).
Thus, we should try to keep this mapping up to date in the library to support all estimator classes that AWS supports, so end user doesn not need to do this customization on their side.
"""
from typing import Any, ClassVar

from sm_pipelines_oo.steps.interfaces import StepFactoryInterface, StepFactoryFacadeInterface
from sm_pipelines_oo.steps import framework_processing_step
from sm_pipelines_oo.steps.framework_processing_step import StepFactory
from sm_pipelines_oo.pipeline import PipelineFacade
from sm_pipelines_oo.steps.step_factory_facade import StepFactoryFacade


class MyEstimatorCls():
    """This is class we want FrameworkProcessor to use as `estimator_cls`."""
    name: ClassVar[str] = 'my_custom_estimator'

# Create a custom StepFactory for FrameworkProcessor that changes the default lookup table for estimators to use our custom estimator class.
_customized_fwp_stepfactory: type[StepFactory] = framework_processing_step.StepFactory
_customized_fwp_stepfactory.estimator_name_to_cls_mapping = {
    'my_custom_estimator': MyEstimatorCls,
}
# Now we can use this in our stepfactory facade
customized_stepfactory_lookup_table: dict[str, type[StepFactoryInterface]] = {
    'CustomFrameworkProcessor': _customized_fwp_stepfactory,
}

custom_pipeline = PipelineFacade(
    env='dev',
    custom_stepfactory_lookup_table=customized_stepfactory_lookup_table,
)
