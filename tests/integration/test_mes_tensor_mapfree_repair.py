"""Synthetic Git-object integration tests; no real maps or observation claims."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('mes_repair_runner_under_test',ROOT/'scripts/observed_runs/rebuild_mes_tensor_carriers.py')
MOD=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()


def powers(rows):
    out=np.zeros((len(rows),12))
    for j,(ell,start,end) in enumerate([(2,0,5),(3,5,12),(4,12,21),(5,21,32)]):
        out[:,j]=np.sum(rows[:,start:end]**2,axis=1)/(2*ell+1)
    return out


@pytest.fixture
def synthetic_git(tmp_path,monkeypatch):
    repo=tmp_path/'repo';repo.mkdir()
    git(repo,'init');git(repo,'config','user.name','Synthetic Test');git(repo,'config','user.email','test@example.invalid')
    rng=np.random.default_rng(8128)
    paired=rng.normal(size=(301,32));cmb=rng.normal(size=(1000,32));cmb[0]=paired[0]
    ids0=np.array([MOD.OBSERVATION_ID]+[f'FFP10-SMICA-CMBNOISE-{i:05d}' for i in range(300)],dtype='U64')
    ids1=np.array([MOD.OBSERVATION_ID]+[f'FFP10-SMICA-CMB-{i:05d}' for i in range(1000) if i!=970],dtype='U64')
    layout=np.array([(str(l),str(m),k) for l in range(2,6) for m in range(l+1) for k in (('real',) if m==0 else ('real','imag'))],dtype='U8')
    for name in (MOD.PAIRED,MOD.FROZEN,MOD.CMBONLY):(repo/name).parent.mkdir(parents=True,exist_ok=True)
    np.savez(repo/MOD.PAIRED,observed_real_alm=paired[0],null_real_alm=paired[1:],row_ids=ids0,real_alm_layout=layout)
    scalar=powers(paired)
    np.savez(repo/MOD.FROZEN,observed_features=scalar[0],null_features=scalar[1:])
    np.savez(repo/MOD.CMBONLY,carrier_rows=cmb,scalar_features=powers(cmb),row_ids=ids1,
             q_components=np.array(['WITHDRAWN_NEVER_LOAD']),o_components=np.array(['WITHDRAWN_NEVER_LOAD']))
    git(repo,'add','docs');git(repo,'commit','-m','synthetic carrier fixtures')
    monkeypatch.setattr(MOD,'SOURCE_HEAD',git(repo,'rev-parse','HEAD'))
    monkeypatch.setattr(MOD,'SOURCE_TREE',git(repo,'rev-parse','HEAD^{tree}'))
    monkeypatch.setattr(MOD,'EXPECTED_SHA',{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in (MOD.PAIRED,MOD.FROZEN)})
    return repo,paired,cmb


def test_correct_m0_quadrupole_and_octupole_basis():
    rows=np.zeros((2,32));rows[0,0]=1;rows[1,5]=1
    q,o,p=MOD.project_carrier(rows)
    k2=math.sqrt(5/(16*math.pi));k3=math.sqrt(7/(16*math.pi))
    np.testing.assert_allclose(q[0],np.diag([-k2,-k2,2*k2]),rtol=2e-13,atol=1e-14)
    assert abs(o[1,2,2,2]-2*k3)<2e-13
    assert abs(o[1,0,0,2]+k3)<2e-13
    assert abs(o[1,1,1,2]+k3)<2e-13
    np.testing.assert_allclose(q[1],0,atol=1e-14)
    np.testing.assert_allclose(o[0],0,atol=1e-14)


def test_unit_basis_gram_and_stored_real_metric():
    qb,ob=MOD.harmonic_stf_matrices()
    np.testing.assert_allclose(np.einsum('aij,bij->ab',qb,qb),np.eye(5)*15/(8*math.pi),rtol=3e-13,atol=3e-13)
    np.testing.assert_allclose(np.einsum('aijk,bijk->ab',ob,ob),np.eye(7)*35/(8*math.pi),rtol=3e-13,atol=3e-13)


def test_source_loader_selects_only_original_carriers(synthetic_git):
    repo,paired,cmb=synthetic_git
    arms,ledger=MOD._load_sources(repo)
    np.testing.assert_array_equal(arms['paired300'][0],paired)
    np.testing.assert_array_equal(arms['cmbonly999'][0],cmb)
    assert len(ledger)==3
    assert all(v['git_blob'] and len(v['sha256'])==64 for v in ledger.values())


def test_actual_synthetic_git_execute_is_pending_and_map_free(synthetic_git):
    repo,paired,cmb=synthetic_git
    out=repo/'docs/generated/new_representation_repair'
    result=MOD.execute(repo,out,t0=2725500.,epsilon1=0.)
    assert result['raw_maps_reopened'] is False
    assert result['new_ranks_generated'] is False
    assert result['physical_claim_promoted'] is False
    assert result['arms']['paired300']['rows']==301
    assert result['arms']['cmbonly999']['rows']==1000
    pending=json.loads((out/'terminal.pending.json').read_text())
    assert pending['state']=='EXECUTED_PENDING_INDEPENDENT_REVIEW'
    assert pending['independent_review']=='NOT_PERFORMED'
    assert 'P0_remaining' not in pending and 'P1_remaining' not in pending
    assert not (out/'terminal.json').exists()
    for name,rows in [('paired300',paired),('cmbonly999',cmb)]:
        with np.load(out/name/'corrected_representation.npz',allow_pickle=False) as z:
            np.testing.assert_array_equal(z['carrier_rows'],rows)
        lines=(out/name/'krylov_chart_rows.jsonl').read_text().splitlines()
        assert len(lines)==len(rows)
    for relative,digest in pending['artifact_sha256'].items():
        assert hashlib.sha256((out/relative).read_bytes()).hexdigest()==digest


def test_wrong_frozen_sha_is_not_silently_rehashed(synthetic_git,monkeypatch):
    repo,_,_=synthetic_git
    monkeypatch.setattr(MOD,'EXPECTED_SHA',{MOD.PAIRED:'0'*64})
    with pytest.raises(ValueError,match='Immutable source mismatch'):MOD._load_sources(repo)


def test_wrong_source_tree_is_rejected(synthetic_git,monkeypatch):
    repo,_,_=synthetic_git
    monkeypatch.setattr(MOD,'SOURCE_TREE','0'*40)
    with pytest.raises(ValueError,match='tree differs'):MOD._load_sources(repo)


@pytest.mark.parametrize('change',['reversed','duplicate','omitted'])
def test_row_identity_mutants_are_rejected(change):
    expected=['obs','a','b']
    value={'reversed':['obs','b','a'],'duplicate':['obs','a','a'],'omitted':['obs','a']}[change]
    with pytest.raises(ValueError,match='row identity/order mismatch'):MOD._ids(np.array(value,dtype='U8'),expected,'rows')


@pytest.mark.parametrize('bad',[np.ones((2,32),dtype=np.float32),np.ones((2,32),dtype=object),np.full((2,32),np.nan)])
def test_noncanonical_numeric_carriers_are_refused(bad):
    with pytest.raises(ValueError):MOD.project_carrier(bad)


def test_existing_output_is_preserved(synthetic_git):
    repo,_,_=synthetic_git;out=repo/'docs/generated/existing';out.mkdir();(out/'unique.txt').write_text('preserve')
    with pytest.raises(FileExistsError):MOD.execute(repo,out,t0=2725500.,epsilon1=0.)
    assert (out/'unique.txt').read_text()=='preserve'


def test_raw_or_arbitrary_output_root_is_refused(synthetic_git):
    repo,_,_=synthetic_git
    with pytest.raises(ValueError,match='explicitly allowed'):MOD.execute(repo,repo/'raw/new',t0=2725500.,epsilon1=0.)


def test_without_execute_neither_git_inputs_nor_output_are_touched(tmp_path):
    out=tmp_path/'must_not_exist'
    p=subprocess.run([sys.executable,str(ROOT/'scripts/observed_runs/rebuild_mes_tensor_carriers.py'),
        '--repo',str(tmp_path/'not_a_repo'),'--output-dir',str(out),'--t0-uk','2725500','--residual-epsilon1','0'],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    assert json.loads(p.stdout)['state']=='NOT_EXECUTED'
    assert not out.exists()
