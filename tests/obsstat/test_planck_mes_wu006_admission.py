from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
H, T = 'a'*40, 'b'*40
R, U = 'sha256:'+'c'*64, 'sha256:'+'d'*64
A = {'result.json': 'sha256:'+'e'*64, 'figure.pdf': 'sha256:'+'f'*64}

def api():
    p = ROOT / 'scripts/observed_runs/planck_mes_wu006_admission.py'
    if not p.is_file(): pytest.fail('WU006 admission support is not implemented', pytrace=False)
    spec = importlib.util.spec_from_file_location('admission_under_test', p)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def receipt():
    return dict(format='PLANCK_MES_WU006_FRESH_REVIEW_V1', work_unit='PMG-WU-006', state='PASS',
                P0=0, P1=0, candidate_git_head=H, candidate_git_tree=T, result_content_id=R,
                predecessor_terminal_sha256=U, objective_output_sha256=copy.deepcopy(A),
                independent_read_only_first_pass=True, repair_rounds_used=0, findings=[],
                visual_inspection={'figure.pdf': {'single_column_3.3in':'PASS','double_column_6.8in':'PASS'}})

def validate(mod, r):
    return mod.validate_review_binding(r, candidate_head=H, candidate_tree=T,
        result_content_id=R, predecessor_terminal_sha256=U, artifact_sha256=A,
        figure_names=('figure.pdf',))

def test_matching_external_review_is_accepted():
    r = receipt(); validate(api(), r)
    assert r == receipt()

@pytest.mark.parametrize('field', ['candidate_git_head','candidate_git_tree','result_content_id',
    'predecessor_terminal_sha256','objective_output_sha256','independent_read_only_first_pass'])
def test_review_missing_required_binding_is_rejected(field):
    mod = api(); r=receipt(); r.pop(field)
    with pytest.raises(mod.AdmissionError): validate(mod,r)

@pytest.mark.parametrize('field,value', [('candidate_git_head','9'*40),('candidate_git_tree','8'*40),
    ('candidate_git_head','a'*39),('candidate_git_tree',True),('result_content_id','sha256:'+'9'*64),
    ('predecessor_terminal_sha256','sha256:'+'8'*64),('P0',False),('P1',1),('repair_rounds_used',True),
    ('repair_rounds_used',2),('state','PENDING')])
def test_review_wrong_code_result_or_finding_cannot_pass(field,value):
    mod=api(); r=receipt(); r[field]=value
    with pytest.raises(mod.AdmissionError): validate(mod,r)

@pytest.mark.parametrize('mutation', ['artifact','missing_figure','pending_visual','extra_artifact','hidden_p1'])
def test_review_output_and_visual_scope_are_exact(mutation):
    mod=api();r=receipt()
    if mutation=='artifact':r['objective_output_sha256']['result.json']='sha256:'+'0'*64
    if mutation=='missing_figure':r['visual_inspection']={}
    if mutation=='pending_visual':r['visual_inspection']['figure.pdf']['single_column_3.3in']='PENDING'
    if mutation=='extra_artifact':r['objective_output_sha256']['extra.json']='sha256:'+'0'*64
    if mutation=='hidden_p1':r['findings']=[{'severity':'P1'}]
    with pytest.raises(mod.AdmissionError):validate(mod,r)

def test_provenance_rebind_preserves_scientific_projection():
    mod=api(); old={'row_count':301,'family_results':{'rank':'27/301'}, 'numerical_outputs':{'x':'unchanged'}}
    old['content_id']=mod.content_id(old)
    before=copy.deepcopy(old)
    updated=mod.rebind_result_record(old, {'terminal_sha256':U})
    assert old==before
    assert updated['predecessor_admission']=={'terminal_sha256':U}
    scientific={k:v for k,v in updated.items() if k not in {'content_id','predecessor_admission'}}
    assert scientific=={k:v for k,v in old.items() if k!='content_id'}
    assert updated['content_id']!=old['content_id']

def test_rebind_rejects_modified_provisional_result():
    mod=api();old={'row_count':301};old['content_id']=mod.content_id(old);old['row_count']=300
    with pytest.raises(mod.AdmissionError):mod.rebind_result_record(old, {})


def test_candidate_identity_allows_only_evidence_dirt(tmp_path, monkeypatch):
    import subprocess
    mod=api(); root=tmp_path/'repo';root.mkdir()
    def git(*args):
        return subprocess.run(['git','-C',str(root),*args],text=True,capture_output=True,check=True).stdout.strip()
    git('init','-q');(root/'code.py').write_text('x=1\n');git('add','code.py')
    git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture')
    head,tree=git('rev-parse','HEAD'),git('rev-parse','HEAD^{tree}')
    monkeypatch.setattr(mod,'RB2_HEAD',head)
    output=root/'docs/generated/result';output.mkdir(parents=True);(output/'pending.json').write_text('{}')
    assert mod.candidate_identity(root,output_dir=output)==(head,tree)
    (root/'code.py').write_text('x=2\n')
    with pytest.raises(mod.AdmissionError,match='source or unrelated'):
        mod.candidate_identity(root,output_dir=output)


def test_candidate_identity_requires_upstream_ancestry(tmp_path,monkeypatch):
    import subprocess
    mod=api();root=tmp_path/'repo';root.mkdir()
    def git(*args):return subprocess.run(['git','-C',str(root),*args],text=True,capture_output=True,check=True).stdout.strip()
    git('init','-q');(root/'x').write_text('x');git('add','x')
    git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture')
    with pytest.raises(mod.AdmissionError,match='ancestry'):
        mod.candidate_identity(root,output_dir=root/'output')
