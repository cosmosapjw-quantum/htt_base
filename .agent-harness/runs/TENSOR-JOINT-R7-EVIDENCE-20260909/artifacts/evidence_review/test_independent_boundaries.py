"""Independent consumer checks: stored evidence and fixture-only campaign runs."""
import importlib.util
import json
from pathlib import Path
import pytest
from common.r7_evidence import cas_evidence_binding
from common.r7_contracts import BranchResult
from scripts.observed_runs import run_tensor_joint_r7 as driver
from scripts.observed_runs.run_r7_campaign import run_campaign

ROOT = Path(__file__).resolve().parents[5]
spec = importlib.util.spec_from_file_location('assigned_evidence_fixture', ROOT / 'tests/r7/test_evidence_binding.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
sandbox = fixtures.sandbox
OLD_RUN = fixtures.OLD_RUN
write_json = fixtures.write_json


def test_current_real_evidence_consumer_only():
    report, binding = cas_evidence_binding(ROOT, ROOT / OLD_RUN / 'cas_adjudication.json', ROOT / OLD_RUN / 'CAS_CONTRACT.json')
    assert binding['eligible'], binding['errors']
    assert 'no empirical admission' in binding['scope']


@pytest.mark.parametrize('status', ['CAS_CONFLICT', 'CAS_PASS_WITH_REGISTERED_EXCEPTION', 'PASS', None])
def test_other_nonfouraxis_states_never_certify(sandbox, status):
    root, run, _, report = sandbox
    report['aggregate_status'] = status
    write_json(root / OLD_RUN / 'cas_adjudication.json', report)
    result = driver.algebra(fixtures.node(run, 'algebra'), {})
    assert set(result.capabilities) == {'ALGEBRA_VERIFIED'}


@pytest.mark.parametrize('transition', ['cas_removed', 'contract_arrives', 'review_arrives', 'review_removed'])
def test_evidence_transition_and_unchanged_second_resume(sandbox, transition):
    root, run, _, _ = sandbox
    cas = root / OLD_RUN / 'cas_adjudication.json'
    contract = root / OLD_RUN / 'CAS_CONTRACT.json'
    reviewed = root / 'Q.py'
    review = run / 'independent_review.json'
    review_payload = {'status':'PASS', 'final_source_sha256':{reviewed.name:driver._sha(reviewed)}}
    if transition == 'contract_arrives':
        saved = contract.read_bytes(); contract.unlink()
    if transition == 'review_removed': write_json(review, review_payload)
    consumer = 'R7-23' if transition.startswith('review') else 'R7-01'
    dag = run / 'independent_dag.json'
    deps = {consumer: [], 'child':[consumer], 'untouched':[], 'final':['child','untouched']}
    write_json(dag, {'campaign_id':'independent-evidence-transitions', 'nodes':[
        {'id':key,'settle_after':pred,'capability_routes':[[]],'declared_outputs':[],'always_run':False}
        for key,pred in deps.items()]})
    calls=[]
    def execute(node, predecessors):
        calls.append(node['id'])
        return BranchResult(node['id'],'COMPLETED_SUCCESS','NOT_EVALUATED')
    def invoke(resume=False):
        _,inputs,sources,_=driver.campaign_executors(root,run)
        run_campaign(dag,run,resume=resume,executors={key:execute for key in deps},input_identities=inputs,implementation_sources=sources)
    invoke(); calls.clear()
    if transition == 'cas_removed': cas.unlink()
    elif transition == 'contract_arrives': contract.write_bytes(saved)
    elif transition == 'review_arrives': write_json(review,review_payload)
    else: review.unlink()
    invoke(True)
    assert set(calls)=={consumer,'child','final'}
    calls.clear(); invoke(True); assert not calls
    assert not (run/'nodes/untouched/attempt-0002').exists()
