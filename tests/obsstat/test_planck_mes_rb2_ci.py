from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
HEAD = '0ae0e70791273c13c7b80ac835232c3c63555c5b'
JOBS = {
    317997656: ('Repository integrity', ('Python package smoke', 'Repository contracts', 'Rust compile')),
    318213662: ('PR04 theory and integration gates', ('Python 3.10', 'Python 3.11', 'Python 3.12', 'Python 3.13')),
    318213674: ('PR07 audit-repair gates', ('Portable numerical + claim gates',)),
}

def api():
    p = ROOT / 'scripts/observed_runs/check_planck_mes_rb2_ci.py'
    if not p.is_file():
        pytest.fail('exact-head CI checker is not implemented', pytrace=False)
    spec = importlib.util.spec_from_file_location('ci_under_test', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def good_runs():
    result = []
    for number, (wid, (name, names)) in enumerate(JOBS.items(), 1):
        rid = 1000 + number
        jobs = [dict(id=rid*10+i, name=n, run_id=rid, run_attempt=2, head_sha=HEAD,
                     workflow_name=name, runner_id=10+i, status='completed', conclusion='success',
                     steps=[dict(name='Run required checks', number=1, status='completed', conclusion='success')])
                for i, n in enumerate(names)]
        result.append(dict(id=rid, workflow_id=wid, name=name, head_sha=HEAD, run_attempt=2,
                           status='completed', conclusion='success', event='pull_request', jobs=jobs,
                           annotations={}))
    return result

def test_all_eight_executed_jobs_on_exact_head_open_transition():
    r = api().classify_ci(HEAD, good_runs())
    assert r['state'] == 'PASS'
    assert r['transition_open'] is True
    assert r['job_count'] == 8

@pytest.mark.parametrize('reason, expected', [
    ('The job was not started because recent account payments have failed or your spending limit needs to be increased.', 'NOT_STARTED_EXTERNAL_GITHUB_BILLING'),
    ('runner allocation unavailable', 'NOT_STARTED_EXTERNAL_GITHUB_ACTIONS'),
])
def test_nonexecution_is_not_candidate_failure_or_success(reason, expected):
    runs = good_runs()
    for run in runs:
        run['conclusion'] = 'failure'
        for job in run['jobs']:
            job.update(runner_id=0, steps=[], conclusion='failure')
            run['annotations'][str(job['id'])] = [dict(message=reason)]
    r = api().classify_ci(HEAD, runs)
    assert r['state'] == expected
    assert r['transition_open'] is False
    assert r['executed_jobs'] == 0

@pytest.mark.parametrize('mutation', ['run_head', 'job_head', 'attempt', 'missing_job', 'duplicate_job', 'missing_run', 'wrong_workflow'])
def test_incomplete_or_misattributed_ci_never_opens_transition(mutation):
    runs = good_runs()
    if mutation == 'run_head': runs[0]['head_sha'] = 'a'*40
    if mutation == 'job_head': runs[0]['jobs'][0]['head_sha'] = 'a'*40
    if mutation == 'attempt': runs[0]['jobs'][0]['run_attempt'] = 1
    if mutation == 'missing_job': runs[0]['jobs'].pop()
    if mutation == 'duplicate_job': runs[0]['jobs'].append(copy.deepcopy(runs[0]['jobs'][0]))
    if mutation == 'missing_run': runs.pop()
    if mutation == 'wrong_workflow': runs[0]['workflow_id'] = 999
    r = api().classify_ci(HEAD, runs)
    assert r['state'] == 'INVALID_CI_EVIDENCE'
    assert r['transition_open'] is False

@pytest.mark.parametrize('mutation, expected', [
    ('empty_success', 'INCOMPLETE_CI'), ('failure', 'FAILED_EXECUTED_WORKFLOW'),
    ('pending', 'CI_PENDING'), ('skipped', 'INCOMPLETE_CI'),
])
def test_job_status_and_steps_are_not_replaced_by_workflow_badge(mutation, expected):
    runs = good_runs()
    job = runs[0]['jobs'][0]
    if mutation == 'empty_success': job.update(runner_id=0, steps=[])
    if mutation == 'failure': job.update(conclusion='failure'); runs[0]['conclusion'] = 'failure'
    if mutation == 'pending': job.update(status='queued', conclusion=None); runs[0].update(status='in_progress', conclusion=None)
    if mutation == 'skipped': job.update(conclusion='skipped', steps=[])
    r = api().classify_ci(HEAD, runs)
    assert r['state'] == expected
    assert r['transition_open'] is False


def test_live_collector_reads_exact_latest_attempt(monkeypatch):
    mod=api(); runs=good_runs(); calls=[]
    for i,run in enumerate(runs): run['run_number']=i+1
    def get(endpoint, *, paginate=False):
        calls.append((endpoint,paginate))
        if '/actions/runs?' in endpoint:
            return [{'workflow_runs':[{k:v for k,v in r.items() if k not in {'jobs','annotations'}} for r in runs]}]
        for r in runs:
            if endpoint.endswith(f"/actions/runs/{r['id']}"):
                return copy.deepcopy({k:v for k,v in r.items() if k not in {'jobs','annotations'}})
            if f"/actions/runs/{r['id']}/attempts/2/jobs?" in endpoint:
                return [{'jobs':copy.deepcopy(r['jobs'])}]
        raise AssertionError(endpoint)
    monkeypatch.setattr(mod,'_gh_get',get)
    report=mod.check_live_ci(HEAD)
    assert report['state']=='PASS'
    assert report['evidence_origin']=='LIVE_GITHUB_GET_ONLY'
    assert sum('/attempts/2/jobs?' in e for e,_ in calls)==3
    assert sum('/actions/runs?' in e for e,_ in calls)==2


def test_live_collector_rejects_attempt_moving_during_read(monkeypatch):
    mod=api();runs=good_runs();count={}
    def get(endpoint, *, paginate=False):
        if '/actions/runs?' in endpoint:return [{'workflow_runs':runs}]
        r=runs[0]
        if endpoint.endswith(f"/actions/runs/{r['id']}"):
            count[endpoint]=count.get(endpoint,0)+1
            result=copy.deepcopy(r)
            if count[endpoint]>1: result['run_attempt']=3
            return result
        if '/attempts/2/jobs?' in endpoint:return [{'jobs':copy.deepcopy(r['jobs'])}]
        raise AssertionError(endpoint)
    monkeypatch.setattr(mod,'_gh_get',get)
    with pytest.raises(mod.CIError,match='attempt changed'):mod.check_live_ci(HEAD)
