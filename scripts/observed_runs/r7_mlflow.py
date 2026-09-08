"""Optional operational tracing. Never a scientific eligibility provider.

API: https://mlflow.org/docs/latest/genai/tracing/app-instrumentation/manual-tracing/
https://mlflow.org/docs/latest/genai/tracing/search-traces/
"""
from __future__ import annotations
import os
import numpy as np


class MlflowTracing:
    def __init__(self,sdk,experiment_id):
        self.sdk=sdk;self.experiment_id=experiment_id

    def record_node(self,result,entry):
        with self.sdk.start_span(name='r7.'+result.node_id) as span:
            span.set_inputs({'node_id':result.node_id,'attempt':result.attempt,'fingerprint':entry['fingerprint']})
            span.set_outputs({'process_status':result.process_status,'scientific_outcome':result.scientific_outcome})
            span.set_attributes({'r7.operational_only':True})

    def evaluate_routing(self,fixture_results):
        # Reuse deterministic local routing fixture outcomes. No LLM judge,
        # scientific truth scoring, or alteration of the fixture thresholds.
        from mlflow.genai.scorers import scorer
        @scorer
        def routing_exact(outputs,expectations):
            return outputs==expectations['expected_response']
        rows=[{'inputs':{'fixture_id':r['fixture_id']},'outputs':r['actual'],
               'expectations':{'expected_response':r['expected']}} for r in fixture_results]
        return self.sdk.genai.evaluate(data=rows,scorers=[routing_exact])

    def aggregate_traces(self,max_results=1000):
        frame=self.sdk.search_traces(experiment_ids=[self.experiment_id],return_type='pandas',max_results=max_results)
        values=np.asarray(frame['execution_duration'].dropna(),dtype=float)
        return {'returned_trace_count':len(frame),'query_limit':max_results,'complete_population':len(frame)<max_results,
                'mean_duration_ms':float(values.mean()) if len(values) else None,
                'p95_duration_ms':float(np.quantile(values,.95)) if len(values) else None}


def configured_tracer(environ=None):
    env=os.environ if environ is None else environ
    if env.get('R7_ENABLE_MLFLOW')!='1':return None,{'status':'DISABLED','reason':'default off'}
    if not env.get('MLFLOW_TRACKING_URI') or not env.get('MLFLOW_EXPERIMENT_ID'):
        return None,{'status':'UNAVAILABLE','reason':'explicit tracking URI and experiment ID required'}
    try:
        import mlflow
        mlflow.set_tracking_uri(env['MLFLOW_TRACKING_URI'])
        mlflow.set_experiment(experiment_id=env['MLFLOW_EXPERIMENT_ID'])
        return MlflowTracing(mlflow,env['MLFLOW_EXPERIMENT_ID']),{'status':'CONFIGURED','version':mlflow.__version__}
    except Exception as exc:
        return None,{'status':'UNAVAILABLE','reason':f'{type(exc).__name__}: {exc}'}
