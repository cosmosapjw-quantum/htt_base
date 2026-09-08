from contextlib import contextmanager
from common.r7_contracts import BranchResult
from scripts.observed_runs.r7_mlflow import configured_tracer,MlflowTracing


def test_default_disabled_and_missing_config_is_nonfatal():
    assert configured_tracer({})[0] is None
    assert configured_tracer({'R7_ENABLE_MLFLOW':'1'})[1]['status']=='UNAVAILABLE'


def test_operational_span_contains_no_scientific_side_effect():
    class Span:
        def set_inputs(self,x):self.inputs=x
        def set_outputs(self,x):self.outputs=x
        def set_attributes(self,x):self.attributes=x
    class SDK:
        @contextmanager
        def start_span(self,**kwargs):
            self.span=Span();yield self.span
    sdk=SDK();tracer=MlflowTracing(sdk,'fixture')
    result=BranchResult('R7-19','COMPLETED_SUCCESS','CONDITIONAL_BOUND')
    tracer.record_node(result,{'fingerprint':'fixed'})
    assert sdk.span.outputs['scientific_outcome']=='CONDITIONAL_BOUND'
    assert sdk.span.attributes['r7.operational_only'] is True
    assert result.capabilities==()
