"""Evidence-consumer regressions; fixtures do not execute or certify science."""
import hashlib
import json
from pathlib import Path

import pytest

from common.r7_contracts import BranchResult
from scripts.observed_runs import run_tensor_joint_r7 as driver
from scripts.observed_runs.run_r7_campaign import run_campaign

ROOT = Path(__file__).resolve().parents[2]
OLD_RUN = Path('.agent-harness/runs/TENSOR-JOINT-R7-20260908')
BINDINGS = Path('docs/generated/tensor_joint_r7/source_bindings.json')


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    root = tmp_path / 'repo'
    contract = json.loads((ROOT / OLD_RUN / 'CAS_CONTRACT.json').read_text())
    report = json.loads((ROOT / OLD_RUN / 'cas_adjudication.json').read_text())
    for name in ('CAS_CONTRACT.json', 'cas_adjudication.json'):
        target = root / OLD_RUN / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / OLD_RUN / name).read_bytes())
    for item in contract['identity']['source_input_hashes']:
        target = root / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / item['path']).read_bytes())
    # Only a Q source is mutated; a separately bound B source must survive.
    records = []
    for donor in ('Q', 'B'):
        path = root / (donor + '.py')
        path.write_text('# selected ' + donor)
        records.append(dict(donor=donor, path=path.name,
                            selected_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    write_json(root / BINDINGS, {'records': records})
    inventory = root / 'inventory.csv'
    inventory.write_text('name,physical_path,workdir_path\n')
    monkeypatch.setattr(driver, 'INVENTORY', inventory)
    monkeypatch.setattr(driver, 'EXTERNAL_INVENTORY', root / 'absent_external_inventory')
    monkeypatch.setattr(driver, 'ROOT', root)
    # Keep these tests on the admission boundary: no numerical subprocesses.
    def tests(node, paths, extra=()):
        log = node['_attempt_dir'] / 'validation.log'
        log.write_text('FIXTURE: numerical validation not executed')
        return {'log': str(log), 'exit_code': 0}
    def finish(node, details, capabilities=(), outcome='NOT_EVALUATED', reasons=(), extra_evidence=()):
        artifact = node['_attempt_dir'] / 'fixture.json'
        write_json(artifact, {'scope': 'EVIDENCE_CONSUMER_FIXTURE_ONLY'})
        return BranchResult(node['id'], 'COMPLETED_SUCCESS', outcome,
                            tuple(capabilities), evidence=(str(artifact),), product_results=details)
    monkeypatch.setattr(driver, '_tests', tests)
    monkeypatch.setattr(driver, '_finish', finish)
    run = tmp_path / 'run'
    run.mkdir()
    return root, run, contract, report


def node(run, name):
    attempt = run / name
    attempt.mkdir()
    return {'id': name, '_run_dir': run, '_attempt_dir': attempt}


@pytest.mark.parametrize('status', ['CAS_FAIL', 'CAS_BLOCKED'])
def test_failed_cas_note_cannot_issue_capability(sandbox, status):
    root, run, _, report = sandbox
    report['aggregate_status'] = status
    assert 'CAS_4AXIS_PASS' in report['note']
    write_json(root / OLD_RUN / 'cas_adjudication.json', report)
    result = driver.algebra(node(run, 'R7-01'), {})
    assert result.capabilities == ('ALGEBRA_VERIFIED',)


def test_existing_observed_cas_retains_only_its_narrow_scope(sandbox):
    _, run, _, _ = sandbox
    result = driver.algebra(node(run, 'R7-01'), {})
    assert set(result.capabilities) == {'ALGEBRA_VERIFIED', 'FOUR_AXIS_CAS', 'CONTINUUM_CERTIFIED'}
    assert 'Seven fixed' in result.product_results['cas_scope']
    assert result.product_results['cas_binding']['eligible'] is True


@pytest.mark.parametrize('defect', [
    'contract_hash', 'contract_source', 'missing_axis', 'failed_axis', 'axis_error',
    'not_executed', 'timeout', 'exit_code', 'missing_check', 'false_check',
    'assumption_diff', 'counterexample', 'not_eligible', 'stored_result',
    'missing_contract', 'malformed_report', 'malformed_contract', 'integer_check',
    'wrong_axis', 'extra_axis', 'aggregate_error',
])
def test_cas_admission_requires_bound_observed_axis_evidence(sandbox, defect):
    root, run, contract, report = sandbox
    axis = report['execution_evidence']['sympy']
    if defect == 'contract_hash': report['contract_sha256'] = '0' * 64
    elif defect == 'contract_source': (root / contract['identity']['source_input_hashes'][0]['path']).write_text('changed')
    elif defect == 'missing_axis': del report['execution_evidence']['lean']
    elif defect == 'failed_axis': report['axis_statuses']['sympy'] = 'FAIL'
    elif defect == 'axis_error': axis['errors'] = ['invalid result']
    elif defect == 'not_executed': axis['solver_executed'] = False
    elif defect == 'timeout': axis['timed_out'] = True
    elif defect == 'exit_code': axis['exit_code'] = 1
    elif defect == 'missing_check': axis['payload']['checks'].pop(next(iter(axis['payload']['checks'])))
    elif defect == 'false_check': axis['payload']['checks'][next(iter(axis['payload']['checks']))] = False
    elif defect == 'assumption_diff': axis['payload']['domain_assumption_diff'] = ['changed domain']
    elif defect == 'counterexample': axis['payload']['counterexample'] = {'witness': 1}
    elif defect == 'not_eligible': report['claim_promotion_cas_eligible'] = False
    elif defect == 'stored_result': report['verification_state'] = 'STORED_RESULT_INSPECTION'
    elif defect == 'missing_contract': (root / OLD_RUN / 'CAS_CONTRACT.json').unlink()
    elif defect == 'malformed_contract': (root / OLD_RUN / 'CAS_CONTRACT.json').write_text('{')
    elif defect == 'integer_check': axis['payload']['checks'][next(iter(axis['payload']['checks']))] = 1
    elif defect == 'wrong_axis': axis['axis'] = 'lean'
    elif defect == 'extra_axis': report['execution_evidence']['unrequired'] = axis
    elif defect == 'aggregate_error': report['errors'] = ['failed binding']
    write_json(root / OLD_RUN / 'cas_adjudication.json', report)
    if defect == 'malformed_report': (root / OLD_RUN / 'cas_adjudication.json').write_text('{')
    result = driver.algebra(node(run, 'R7-01'), {})
    assert result.capabilities == ('ALGEBRA_VERIFIED',)
    assert result.product_results['cas_binding']['errors']


def test_donor_consumer_rechecks_bytes_despite_cached_intake(sandbox):
    root, run, _, _ = sandbox
    bindings = json.loads((root / BINDINGS).read_text())
    cached = BranchResult('R7-00', 'COMPLETED_SUCCESS', 'NOT_EVALUATED',
        product_results={'source_binding_failures': {}, 'selected_source_binding': bindings})
    (root / 'Q.py').write_text('# changed after intake')
    result = driver.donor_integration(node(run, 'R7-02'), {'R7-00': cached})
    assert 'DONOR_KRYLOV' not in result.capabilities
    assert 'DONOR_BOOST' in result.capabilities
    assert result.product_results['donor_capability_records']['krylov']['status'] == 'SOURCE_UNAVAILABLE'
    assert json.loads((root / BINDINGS).read_text()) == bindings


def test_intake_records_donor_only_mismatch_without_repinning(sandbox):
    root, run, _, _ = sandbox
    pinned_bytes = (root / BINDINGS).read_bytes()
    before = driver.source_intake(node(run, 'before'), {})
    assert before.product_results['source_binding_failures'] == {}
    (root / 'Q.py').write_text('# changed donor')
    after = driver.source_intake(node(run, 'after'), {})
    assert after.product_results['source_binding_failures'] == {'Q': ['Q.py']}
    assert (root / BINDINGS).read_bytes() == pinned_bytes


@pytest.mark.parametrize('defect', ['changed', 'missing', 'empty', 'malformed'])
def test_review_pass_requires_current_reviewed_bytes(sandbox, defect):
    root, run, _, _ = sandbox
    source = root / 'Q.py'
    review = {'status': 'PASS', 'final_source_sha256': {source.name: driver._sha(source)}}
    write_json(run / 'independent_review.json', review)
    assert driver.audit(node(run, 'before'), {}).capabilities == ('FINAL_AUDIT',)
    if defect == 'changed': source.write_text('# new implementation')
    elif defect == 'missing': source.unlink()
    elif defect == 'empty': write_json(run / 'independent_review.json', {'status': 'PASS', 'final_source_sha256': {}})
    else: (run / 'independent_review.json').write_text('{')
    result = driver.audit(node(run, 'after'), {})
    assert not result.capabilities
    assert result.product_results['review_binding']['eligible'] is False


@pytest.mark.parametrize('change,affected', [
    ('cas_arrival', ['R7-01', 'child', 'final']),
    ('contract', ['R7-01', 'child', 'final']),
    ('contract_source', ['R7-01', 'child', 'final']),
    ('donor', ['R7-00', 'R7-02', 'final']),
    ('reviewed_source', ['R7-23', 'final']),
])
def test_default_dependency_slices_reopen_only_affected_attempts(sandbox, change, affected):
    root, run, _, report = sandbox
    cas = root / OLD_RUN / 'cas_adjudication.json'
    if change == 'cas_arrival': cas.unlink()
    reviewed = root / 'reviewed.py'
    reviewed.write_text('# original')
    write_json(run / 'independent_review.json',
               {'status': 'PASS', 'final_source_sha256': {reviewed.name: driver._sha(reviewed)}})
    deps = {'R7-00': [], 'R7-01': [], 'R7-02': ['R7-00'], 'R7-23': [],
            'unrelated': [], 'child': ['R7-01'], 'final': ['R7-02', 'child', 'R7-23', 'unrelated']}
    nodes = [dict(id=key, settle_after=value, capability_routes=[[]], declared_outputs=[], always_run=False)
             for key, value in deps.items()]
    dag = run / 'dag.json'
    write_json(dag, {'campaign_id': 'evidence-resume-fixture', 'nodes': nodes})
    calls = []
    def execute(n, predecessors):
        calls.append(n['id'])
        return BranchResult(n['id'], 'COMPLETED_SUCCESS', 'NOT_EVALUATED')
    def invoke(resume=False):
        _, inputs, sources, _ = driver.campaign_executors(root, run)
        return run_campaign(dag, run, resume=resume,
            executors={key: execute for key in deps}, input_identities=inputs, implementation_sources=sources)
    invoke()
    calls.clear()
    invoke(True)
    assert calls == []
    if change == 'cas_arrival': write_json(cas, report)
    elif change == 'contract':
        path = root / OLD_RUN / 'CAS_CONTRACT.json'
        path.write_text(path.read_text() + '\n')
    elif change == 'contract_source': (root / 'docs/research_program/tensor_joint_r7/THEORY.md').write_text('new assumptions')
    elif change == 'donor': (root / 'Q.py').write_text('# modified donor')
    elif change == 'reviewed_source': reviewed.write_text('# modified reviewed source')
    invoke(True)
    assert set(calls) == set(affected)
    for key in deps:
        assert (run / 'nodes' / key / 'attempt-0001/result.json').is_file()
        assert (run / 'nodes' / key / 'attempt-0002/result.json').exists() == (key in affected)
    calls.clear()
    invoke(True)
    assert calls == []
