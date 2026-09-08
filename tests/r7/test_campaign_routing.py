from dataclasses import replace
import json
from pathlib import Path
import pytest
from common.r7_contracts import BranchResult,TERMINAL
from scripts.observed_runs.run_r7_campaign import run_campaign,settle_node

ROOT=Path(__file__).resolve().parents[2]
DAG=ROOT/'docs/research_program/tensor_joint_r7/campaign_dag.json'


def fixture_executors(tmp_path,*,remove=(),crashes=(),all_unavailable=False):
    """Deterministic routing evidence only; no fixture is a scientific admission."""
    dag=json.loads(DAG.read_text());executors={}
    def handler(node,predecessors):
        if node['id'] in crashes:raise RuntimeError('registered routing counterexample')
        caps=[c for c in node['declared_outputs'] if c not in remove]
        if all_unavailable and not node['always_run']:caps=[]
        evidence=node['_attempt_dir']/'fixture.json'
        evidence.write_text(json.dumps({'scope':'ROUTING_FIXTURE_ONLY','node':node['id'],'executed':True}))
        bindings={c:{'scope':'ROUTING_FIXTURE_ONLY','artifacts':[str(evidence)]} for c in caps}
        return BranchResult(node['id'],'COMPLETED_SUCCESS','NOT_EVALUATED',tuple(caps),evidence=(str(evidence),),
            product_results={'capability_evidence':bindings})
    for node in dag['nodes']:executors[node['id']]=handler
    return executors


@pytest.mark.parametrize('remove,crashes',[
    (('DONOR_KRYLOV',),()),
    (('PR3_INPUT','CMB_LAW','CF4_LAW','DESI_LAW','JWST_LAW','PROJECTED_LAW','BACKGROUND_LAW','AUX_DISTANCE_LAW'),()),
    (('R3_BENCHMARK','SUPPORTED_EXTERNAL_TRANSFER'),('R7-15','R7-16')),
    (('DESI_INPUT','DESI_LAW','DESI_LAW_FACTORY','BACKGROUND_AUX_INPUT'),()),
    (('JOINT_LAW',),()),
    ((),('R7-19',)),
    (('MASK_BOUND_VERIFIED','FOUR_AXIS_CAS'),()),
])
def test_failure_routes_always_reach_honest_synthesis(tmp_path,remove,crashes):
    results,conclusion=run_campaign(DAG,tmp_path/'run',executors=fixture_executors(tmp_path,remove=remove,crashes=crashes))
    assert len(results)==26 and all(r.process_status in TERMINAL for r in results.values())
    assert results['R7-25'].process_status=='COMPLETED_SUCCESS' and conclusion.process_complete
    for node in crashes:assert results[node].scientific_outcome=='VALIDATION_FAILED'
    if 'DONOR_KRYLOV' in remove:assert 'DONOR_TENSOR' in results['R7-02'].capabilities and results['R7-11'].process_status=='COMPLETED_SUCCESS'
    if 'R3_BENCHMARK' in remove:assert results['R7-17'].process_status=='COMPLETED_SUCCESS'
    if 'MASK_BOUND_VERIFIED' in remove:assert 'ALGEBRA_VERIFIED' in results['R7-01'].capabilities


def test_every_input_unavailable_still_synthesizes_without_empirical_claim(tmp_path):
    results,c=run_campaign(DAG,tmp_path/'run',executors=fixture_executors(tmp_path,all_unavailable=True))
    assert c.process_complete and c.empirical_scope_count==0
    assert results['R7-19'].process_status=='BLOCKED_WITH_RECEIPT'
    assert results['R7-25'].process_status=='COMPLETED_SUCCESS'


def test_success_does_not_issue_all_declared_capabilities(tmp_path):
    executors=fixture_executors(tmp_path)
    executors['R7-00']=lambda node,p:BranchResult('R7-00','COMPLETED_SUCCESS','NOT_EVALUATED')
    results,_=run_campaign(DAG,tmp_path/'run',executors=executors)
    assert not results['R7-00'].capabilities and results['R7-01'].process_status=='BLOCKED_WITH_RECEIPT'


def test_resume_preserves_attempt_and_reopens_only_affected_descendants(tmp_path):
    # Independent A/B -> C(A) and D(always A,B,C), allowing a precise influence check.
    nodes=[dict(id=id,settle_after=deps,capability_routes=[[]],declared_outputs=[],always_run=always)
        for id,deps,always in [('A',[],False),('B',[],False),('C',['A'],False),('D',['A','B','C'],True)]]
    dag=tmp_path/'dag.json';dag.write_text(json.dumps(dict(campaign_id='resume-fixture',nodes=nodes)))
    calls=[]
    def execute(node,p):
        calls.append(node['id']);return BranchResult(node['id'],'COMPLETED_SUCCESS','NOT_EVALUATED',product_results={'input':node['id']})
    executors={n['id']:execute for n in nodes};directory=tmp_path/'run'
    run_campaign(dag,directory,executors=executors,input_identities={'A':'v1','B':'v1'})
    calls.clear();run_campaign(dag,directory,resume=True,executors=executors,input_identities={'A':'v1','B':'v1'})
    assert calls==[]
    run_campaign(dag,directory,resume=True,executors=executors,input_identities={'A':'v2','B':'v1'})
    assert calls==['A','C','D']
    assert (directory/'nodes/A/attempt-0001/result.json').is_file()
    assert (directory/'nodes/A/attempt-0002/result.json').is_file()
    assert not (directory/'nodes/B/attempt-0002').exists()


def test_tracing_failure_cannot_change_scientific_result(tmp_path):
    class Broken:
        def record_node(self,*a):raise OSError('tracing unavailable')
    results,c=run_campaign(DAG,tmp_path/'run',executors=fixture_executors(tmp_path),tracer=Broken())
    assert c.process_complete and results['R7-25'].process_status=='COMPLETED_SUCCESS'
    assert (tmp_path/'run/nodes/R7-00/attempt-0001/tracing_failure.json').is_file()


def test_synthesis_counts_unique_exact_scope_and_reports_conflict():
    from scripts.observed_runs.run_r7_campaign import synthesize_campaign
    from common.r7_contracts import BranchResult
    scope=dict(scope={'experiment_id':'same','law_id':'same'},empirical=True,outcome='CONDITIONAL_BOUND',estimate=1.)
    a=BranchResult('R7-19','COMPLETED_SUCCESS','CONDITIONAL_BOUND',product_results={'scope_results':[scope]})
    b=BranchResult('R7-21','COMPLETED_SUCCESS','NOT_EVALUATED',product_results={'scope_results':[scope]})
    assert synthesize_campaign([a,b]).empirical_scope_count==1
    c=BranchResult('R7-21','COMPLETED_SUCCESS','NOT_EVALUATED',product_results={'scope_results':[dict(scope,estimate=2.)]})
    result=synthesize_campaign([a,c])
    assert result.empirical_scope_count==0
    assert result.scope_results[0]['outcome']=='NUMERICALLY_UNRESOLVED'


def test_default_driver_tracks_radiation_and_provider_sources(tmp_path):
    from scripts.observed_runs.run_tensor_joint_r7 import campaign_executors,ROOT
    _,_,sources,_=campaign_executors(ROOT,tmp_path)
    assert ROOT/'htt/src/common/r7_radiation_jet.py' in sources['R7-03']
    assert ROOT/'htt/bass/transfer/r7_benchmark_provider.py' in sources['R7-15']
    assert ROOT/'htt/bass/transfer/r7_external_provider.py' in sources['R7-16']
    assert ROOT/'tests/r7/test_mes_region.py' in sources['R7-03']


def test_actual_donor_executor_preserves_other_capabilities_on_decoder_failure(tmp_path,monkeypatch):
    from common.r7_contracts import BranchResult
    from scripts.observed_runs import run_tensor_joint_r7 as driver
    def validation(node,paths,extra=()):
        if node['_attempt_dir'].name=='krylov':raise RuntimeError('decoder failure fixture')
        log=node['_attempt_dir']/'validation.log';log.write_text('fixed independent oracle PASS')
        return {'log':str(log),'exit_code':0}
    monkeypatch.setattr(driver,'_tests',validation)
    root=BranchResult('R7-00','COMPLETED_SUCCESS','NOT_EVALUATED',product_results={})
    r=driver.donor_integration({'id':'R7-02','_attempt_dir':tmp_path},{'R7-00':root})
    assert 'DONOR_KRYLOV' not in r.capabilities
    assert {'DONOR_BOOST','DONOR_CF4','DONOR_DESI','DONOR_JWST','DONOR_TENSOR'}<=set(r.capabilities)


def test_catalogue_modules_do_not_require_other_catalogue_producers():
    import subprocess,sys,os
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    code="""import sys,importlib.abc
class HoldCF4(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname=='obsstat.cf4_current_stack':raise ImportError('CF4 held by fixture')
sys.meta_path.insert(0,HoldCF4())
import htt.infer.r7_desi_law
import htt.infer.r7_jwst_law
"""
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,(root/'htt/htt',root/'htt/src',root/'htt',root))))
    result=subprocess.run([sys.executable,'-B','-c',code],cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_actual_observed_driver_requires_parent_calibration_scope(tmp_path,monkeypatch):
    from common.r7_contracts import json_value
    from htt.infer.r7_desi_law import build_compressed_bao_law
    from scripts.observed_runs import run_tensor_joint_r7 as driver
    law=build_compressed_bao_law(dict(likelihood_name='gaussian_likelihood',parameter='qiso',
        observed=[.98],covariance=[[.0004]],window=[[1.]],DV_over_rd_fid=8.,zeff=.3,source_id='routing-fixture'))
    monkeypatch.setattr(driver,'_bao_law',lambda results:law)
    _,record=driver._calibrated_bao(law)
    serialized={key:json_value(getattr(record,key)) for key in ('scope','law_specification_id',
        'method_implementation_id','supported_domain_id','conditioning_target','mechanism','validity')}
    def parent(records):
        return {'R7-18':BranchResult('R7-18','COMPLETED_SUCCESS','NOT_EVALUATED',
            product_results={'calibrations':records})}
    node={'id':'R7-19','_attempt_dir':tmp_path}
    for records in ([],[dict(serialized,supported_domain_id='wrong')],[serialized,serialized],
                    [dict(serialized,scope=dict(serialized['scope'],dataset_ids=['wrong']))]):
        with pytest.raises(ValueError,match='no unique calibration'):driver.observed(node,parent(records))
    result=driver.observed(node,parent([serialized]))
    assert result.scientific_outcome=='CONDITIONAL_BOUND'
    assert result.capabilities==('OBSERVED_RESULTS',)
