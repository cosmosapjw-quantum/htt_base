"""Control-flow tests use synthetic artifacts, never the observed 301-row pool.

AST isolation executes the actual runner functions while avoiding imports and
execution of the independent cosmology layer. Full numerical integration is a
separate post-CI check, not claimed by these tests.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/observed_runs/run_planck_mes_irrep_analysis.py'


def control(name, **namespace):
    tree = ast.parse(RUNNER.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if not nodes:
        pytest.fail(f'{name} control boundary is not implemented', pytrace=False)
    unit = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), *nodes], type_ignores=[])
    env = dict(Path=Path, json=json, sys=sys, argparse=argparse, tempfile=tempfile, ROOT=ROOT,
               DEFAULT_OUTPUT=ROOT/'absent-analysis-output', DEFAULT_CARRIER_DIR=ROOT/'absent-carrier', **namespace)
    exec(compile(ast.fix_missing_locations(unit), str(RUNNER), 'exec'), env)
    return env[name]


def _write(path, payload):
    path.write_text(json.dumps(payload, sort_keys=True) + '\n')


def test_finalizer_without_external_receipt_cannot_change_any_file(tmp_path):
    terminal = {'state':'EXECUTED_PENDING_REVIEW', 'work_unit':'PMG-WU-006'}
    _write(tmp_path/'terminal.json', terminal)
    _write(tmp_path/'plot_audit.json', {'figures':{'f.pdf':{}}})
    before = {p.name:p.read_bytes() for p in tmp_path.iterdir()}
    finalize = control('finalize_reviewed',
        replay_directory=lambda p:{'packaging_validity':'MATCH'},
        DETERMINISTIC_EVIDENCE_FILES=(), _load_npz=lambda p:{},
        _array_bundle_content_id=lambda *a,**k:'synthetic', _write_json=_write,
        AdmissionError=RuntimeError)
    with pytest.raises(RuntimeError, match='external.*review|fresh.review'):
        finalize(tmp_path)
    assert before == {p.name:p.read_bytes() for p in tmp_path.iterdir()}


def test_replay_builds_numerical_reference_without_rendering_figures(tmp_path):
    _write(tmp_path/'result.json', {'content_id':'synthetic'})
    _write(tmp_path/'plot_audit.json', {'result_content_id':'synthetic'})
    seen = []
    class StopAtBuild(RuntimeError): pass
    def build(*args, **kwargs):
        seen.append(kwargs)
        raise StopAtBuild()
    replay = control('replay_directory', _canonical_content_id=lambda *a,**k:'synthetic', build=build)
    with pytest.raises(StopAtBuild): replay(tmp_path)
    assert seen == [{'render_figures':False}]


def test_cli_cannot_reach_build_when_live_upstream_ci_is_closed(monkeypatch):
    reached = []
    def reject(*args, **kwargs): raise RuntimeError('CI_PENDING')
    main = control('main', require_live_ci=reject, RB2_HEAD='0'*40,
                   build=lambda *a,**k:reached.append(True), CIError=RuntimeError,
                   AdmissionError=RuntimeError)
    monkeypatch.setattr(sys, 'argv', ['run_planck_mes_irrep_analysis.py'])
    with pytest.raises(SystemExit) as exc: main()
    assert exc.value.code == 3
    assert reached == []


def test_preserved_result_rebind_changes_only_four_evidence_jsons(tmp_path):
    spec=importlib.util.spec_from_file_location('admission_control', ROOT/'scripts/observed_runs/planck_mes_wu006_admission.py')
    admission=importlib.util.module_from_spec(spec);spec.loader.exec_module(admission)
    out=tmp_path/'out';out.mkdir()
    result={'row_count':301, 'family_results':{'rank':'27/301'}, 'numerical_outputs':{'unchanged':'value'}}
    result['content_id']=admission.content_id(result)
    _write(out/'result.json',result)
    _write(out/'replay.json', {'result_content_id':result['content_id'], 'status':'PASS'})
    _write(out/'plot_audit.json', {'result_content_id':result['content_id'], 'figures':{'f.pdf':{}}})
    _write(out/'terminal.json', {'state':'SUCCEEDED', 'fresh_review':'PASS'})
    (out/'irrep_features.npz').write_bytes(b'synthetic-not-a-science-NPZ')
    (out/'f.pdf').write_bytes(b'synthetic-not-a-figure')
    before={p.name:p.read_bytes() for p in out.iterdir()}
    predecessor={'terminal_sha256':'sha256:'+'a'*64}
    rebind=control('rebind_preserved', validate_predecessor=lambda *a:predecessor,
        rebind_result_record=admission.rebind_result_record, file_sha256=admission.file_sha256,
        _write_json=_write, AdmissionError=admission.AdmissionError,
        candidate_identity=lambda *a,**k:('b'*40,'c'*40), shutil=__import__('shutil'),
        EVIDENCE_UPDATE_FILES=('result.json','replay.json','plot_audit.json','terminal.json'))
    archive=tmp_path/'archive'
    report=rebind(out, private_archive_dir=archive)
    assert report['state']=='REBOUND_PENDING_FRESH_REVIEW'
    after={p.name:p.read_bytes() for p in out.iterdir()}
    assert {k for k in before if before[k]!=after[k]} == {'result.json','replay.json','plot_audit.json','terminal.json'}
    assert json.loads(after['terminal.json'])['state']=='EXECUTED_PENDING_REVIEW'
    assert {p.name:p.read_bytes() for p in archive.iterdir()} == {k:before[k] for k in ('result.json','replay.json','plot_audit.json','terminal.json')}


@pytest.mark.parametrize('mutation', ['none','wrong_head','replay_mutates_artifact','raw_mutation','claim','replay_failure','not_executed','pre_review_pass','no_blocker','premature_transition'])
def test_finalizer_consumes_exact_external_receipt_without_self_attesting_figures(tmp_path, mutation):
    spec=importlib.util.spec_from_file_location('admission_finalize', ROOT/'scripts/observed_runs/planck_mes_wu006_admission.py')
    admission=importlib.util.module_from_spec(spec);spec.loader.exec_module(admission)
    out=tmp_path/'output';out.mkdir()
    predecessor={'terminal_sha256':'sha256:'+'a'*64}
    result={'predecessor_admission':predecessor};result['content_id']=admission.content_id(result)
    _write(out/'result.json',result);_write(out/'replay.json',{'status':'PASS'})
    pending={'format':'PLANCK_MES_OBSERVABLE_IRREP_TERMINAL_V1','state':'EXECUTED_PENDING_REVIEW','work_unit':'PMG-WU-006',
        'fresh_review':'PENDING','claim_promotion':False,'raw_data_read_or_mutated':False,
        'science_execution_performed':True,'replay_status':'MATCH','unresolved_blockers':['FRESH_READ_ONLY_REVIEW_PENDING'],
        'next_executable_action':'FRESH_READ_ONLY_REVIEW'}
    bad_pending={'raw_mutation':('raw_data_read_or_mutated',True),'claim':('claim_promotion',True),
        'replay_failure':('replay_status','FAIL'),'not_executed':('science_execution_performed',False),
        'pre_review_pass':('fresh_review','PASS'),'no_blocker':('unresolved_blockers',[]),
        'premature_transition':('next_executable_action','PMG-WU-007')}
    if mutation in bad_pending:pending[bad_pending[mutation][0]]=bad_pending[mutation][1]
    _write(out/'terminal.json',pending)
    _write(out/'plot_audit.json',{'inspection_state':'PENDING_NEW_CANDIDATE_REVIEW'})
    for name in ('irrep_features.npz','null_distributions.npz','f.pdf'):(out/name).write_bytes(b'synthetic-fixture')
    names=('result.json','replay.json','irrep_features.npz','null_distributions.npz','plot_audit.json','f.pdf')
    receipt={'format':admission.REVIEW_FORMAT,'work_unit':'PMG-WU-006','state':'PASS','P0':0,'P1':0,
        'candidate_git_head':'b'*40,'candidate_git_tree':'c'*40,'result_content_id':result['content_id'],
        'predecessor_terminal_sha256':predecessor['terminal_sha256'],
        'objective_output_sha256':admission.artifact_hashes(out,names),'independent_read_only_first_pass':True,
        'repair_rounds_used':0,'findings':[],
        'visual_inspection':{'f.pdf':{'single_column_3.3in':'PASS','double_column_6.8in':'PASS'}}}
    if mutation=='wrong_head':receipt['candidate_git_head']='d'*40
    review_path=tmp_path/'external_review.json';_write(review_path,receipt)
    before={p.name:p.read_bytes() for p in out.iterdir()};replay_calls=[]
    def replay(p):
        replay_calls.append(True)
        if mutation=='replay_mutates_artifact':(out/'replay.json').write_text('changed')
        return {'packaging_validity':'BYTE_IDENTICAL'}
    finalize=control('finalize_reviewed',candidate_identity=lambda *a,**k:('b'*40,'c'*40),
        validate_predecessor=lambda *a:predecessor, artifact_hashes=admission.artifact_hashes,
        validate_review_binding=admission.validate_review_binding, file_sha256=admission.file_sha256,
        DETERMINISTIC_EVIDENCE_FILES=('result.json','replay.json'),FIGURE_FILES=('f.pdf',),
        replay_directory=replay,_write_json=_write,AdmissionError=admission.AdmissionError)
    if mutation!='none':
        with pytest.raises(admission.AdmissionError):finalize(out,fresh_review_receipt_path=review_path)
        assert not (out/'fresh_review.json').exists()
        assert (out/'terminal.json').read_bytes()==before['terminal.json']
        if mutation=='wrong_head':assert replay_calls==[]
    else:
        finalize(out,fresh_review_receipt_path=review_path)
        terminal=json.loads((out/'terminal.json').read_text())
        assert terminal['state']=='SUCCEEDED'
        assert terminal['candidate_git_head']=='b'*40
        assert terminal['visual_admission_source']=='fresh_review.json'
        assert (out/'fresh_review.json').read_bytes()==review_path.read_bytes()
        assert (out/'plot_audit.json').read_bytes()==before['plot_audit.json']
