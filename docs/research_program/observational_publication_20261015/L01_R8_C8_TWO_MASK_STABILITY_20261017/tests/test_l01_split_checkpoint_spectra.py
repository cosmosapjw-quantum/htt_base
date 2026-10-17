"""Synthetic-alm and producer-checkpoint protocol tests; no real Planck data."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def test_module_is_present():
    assert importlib.util.find_spec('l01_split_checkpoint_spectra') is not None


def api():
    import l01_split_checkpoint_spectra as mod
    return mod


def manufactured(lmax, seed=1, amplitude=1e-6):
    rng = np.random.default_rng(seed)
    a = amplitude * (rng.normal(size=(2, (lmax+1)*(lmax+2)//2)) +
                     1j*rng.normal(size=(2, (lmax+1)*(lmax+2)//2)))
    a[:, :lmax+1] = a[:, :lmax+1].real
    a[:, :2] = 0
    a[:, lmax+1] = 0  # m=1, ell=1
    return a


@pytest.mark.parametrize('lmax', [2, 5, 16, 32, 64, 128])
def test_spectra_against_explicit_negative_m_oracle(lmax):
    mod = api(); a = manufactured(lmax); b = manufactured(lmax, 3)
    got = mod.cross_spectrum_matrix(a, b, lmax)
    for ell in range(2, lmax+1):
        for i in range(2):
            for j in range(2):
                values=[]
                for m in range(-ell, ell+1):
                    k=abs(m)*(2*lmax+1-abs(m))//2+ell
                    x=a[i,k] if m>=0 else (-1)**abs(m)*a[i,k].conjugate()
                    y=b[j,k] if m>=0 else (-1)**abs(m)*b[j,k].conjugate()
                    values.append(x*y.conjugate())
                assert got[i,j,ell] == pytest.approx(np.sum(values).real/(2*ell+1), rel=2e-13, abs=1e-28)


@pytest.mark.parametrize('amplitude', [1., 1e-6, 1e-12, 1e-100])
def test_pair_identity_unit_scaling_and_signed_cross(amplitude):
    mod=api(); a=manufactured(16, 4, amplitude); b=manufactured(16, 9, amplitude)
    r=mod.pair_diagnostics(a,b,16)
    assert r['sum_difference_cross_max_relative'] < 2e-14
    cross=mod.cross_spectrum_matrix(a,b,16)
    reverse=mod.cross_spectrum_matrix(b,a,16)
    np.testing.assert_allclose(cross, reverse.transpose(1,0,2), rtol=2e-14, atol=0)
    assert r['noise_covariance_estimated'] is False


def test_identical_and_opposite_splits():
    mod=api(); a=manufactured(5)
    assert np.count_nonzero(mod.pair_diagnostics(a,a,5)['half_difference']['BB_K_CMB2'])==0
    r=mod.pair_diagnostics(a,-a,5)
    assert np.count_nonzero(r['half_sum']['EE_K_CMB2'])==0
    assert max(r['cross_symmetrized']['EE_K_CMB2'][2:]) < 0


def test_single_ell_m_has_expected_multiplicity_and_signed_eb():
    mod=api(); a=np.zeros((2,15),complex)  # lmax=4
    a[0,4]=3.; a[1,4]=-2.
    k=2*(2*4+1-2)//2+4
    a[0,k]=1+2j; a[1,k]=-2+1j
    c=mod.cross_spectrum_matrix(a,a,4)
    assert c[0,0,4] == pytest.approx(19/9)
    assert c[1,1,4] == pytest.approx(14/9)
    assert c[0,1,4] == pytest.approx(-6/9)
    assert c[0,1,4] == c[1,0,4]


@pytest.mark.parametrize('bad', ['shape','nan','m0','lowspin','object'])
def test_reject_bad_coefficients(bad):
    mod=api(); a=manufactured(5)
    if bad=='shape':a=a[:,:-1]
    if bad=='nan':a[0,8]=complex(float('nan'))
    if bad=='m0':a[0,2]+=1e-30j
    if bad=='lowspin':a[0,0]=1.
    if bad=='object':a=a.astype(object)
    with pytest.raises(ValueError):mod.cross_spectrum_matrix(a,a,5)


def create_checkpoints(folder, lmax=16):
    mod=api(); folder.mkdir()
    common={'schema':mod.PRODUCER_SCHEMA, 'lmax':lmax, 'nside_out':64,
        'native_window_sha256':'2'*64, 'native_receipt_sha256':mod.NATIVE_RECEIPT_SHA,
        'analysis_code_sha256':'3'*64,'healpy_version':'synthetic-fixture',
        'dependency_sha256':{'spin2_finite':'4'*64},
        'native_window':'AND_OF_THREE_NATIVE_PMASKS_STRICTLY_GT_0_5',
        'mask_order':'NESTED2048','missing_inside_fixed_window':'REJECT',
        'processing':'MASK_NATIVE_QU_THEN_MAP2ALM_SPIN_THEN_ALM2MAP_SPIN_RING64'}
    for seed,product in enumerate(mod.PRODUCTS):
        a=manufactured(lmax, seed)
        p=folder/(product+'.npz');np.savez_compressed(p,E=a[0],B=a[1])
        rec={'contract':dict(common,product=product,source_sha256=mod.SOURCE_SHA[product]),
             'alms_npz_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
             'result':{'claim':mod.CLAIM}}
        (folder/(product+'.json')).write_text(json.dumps(rec))
    summary={'schema':mod.PRODUCER_SCHEMA,'status':'PASS_WINDOWED_QU_FINITE_BAND_ACCOUNTING',
        'contract':common, 'source_receipts':{p:{'sha256':mod.SOURCE_SHA[p]} for p in mod.PRODUCTS},
        'paper_gate':'NOT_READY_TO_SUBMIT','independent_sky_count':1}
    (folder/'summary.json').write_text(json.dumps(summary))
    return folder


def change_json(p, function):
    r=json.loads(p.read_text());function(r);p.write_text(json.dumps(r))


def test_five_product_end_to_end_and_no_overwrite(tmp_path):
    mod=api(); folder=create_checkpoints(tmp_path/'checkpoints'); out=tmp_path/'spectra.json'
    before={p.name:p.read_bytes() for p in folder.iterdir()}
    assert mod.main(['--band-dir',str(folder),'--out',str(out)])==0
    result=json.loads(out.read_text())
    assert result['status']=='PASS_SAME_WINDOW_SPLIT_SPECTRA'
    assert set(result['split_pairs'])=={'HM','OE'}
    assert result['p_value'] is None
    assert result['tail_beyond_lmax']=='NOT_BOUNDED'
    assert result['independent_sky_count']==1
    assert 'full_minus_hm_mean' in result['residuals']
    assert mod.main(['--band-dir',str(folder),'--out',str(out)])==2
    assert before=={p.name:p.read_bytes() for p in folder.iterdir()}


@pytest.mark.parametrize('mutation', ['window','source','npz','missing','schema','code','lmax','symlink','paper','extra_contract'])
def test_checkpoint_mismatch_never_reused(tmp_path,mutation):
    mod=api();folder=create_checkpoints(tmp_path/'checkpoints');p=folder/'hm1.json'
    if mutation=='window':change_json(p,lambda r:r['contract'].update(native_window_sha256='5'*64))
    if mutation=='source':change_json(p,lambda r:r['contract'].update(source_sha256='6'*64))
    if mutation=='npz':
        with (folder/'hm1.npz').open('ab') as f:f.write(b'x')
    if mutation=='missing':(folder/'hm1.npz').unlink()
    if mutation=='schema':change_json(folder/'summary.json',lambda r:r.update(schema='wrong'))
    if mutation=='code':change_json(p,lambda r:r['contract'].update(analysis_code_sha256='7'*64))
    if mutation=='lmax':change_json(p,lambda r:r['contract'].update(lmax=32))
    if mutation=='symlink':p.rename(folder/'saved.json');p.symlink_to(folder/'saved.json')
    if mutation=='paper':change_json(folder/'summary.json',lambda r:r.update(paper_gate='READY'))
    if mutation=='extra_contract':change_json(p,lambda r:r['contract'].update(beam_applied=True))
    with pytest.raises((ValueError,OSError)):mod.read_checkpoints(folder)


def test_cli_help_is_standalone_without_healpy(tmp_path):
    mod=api();p=subprocess.run([sys.executable,mod.__file__,'--help'],capture_output=True,text=True,cwd=tmp_path)
    assert p.returncode==0 and '--band-dir' in p.stdout
