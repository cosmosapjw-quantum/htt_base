import pathlib,sys
import numpy as np
import pytest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code'))
from source_only_bound import source_only_certificate,EXPECTED_SHA

SOURCE=ROOT/'source/baseline_response_matrices.npz'
if not SOURCE.is_file():
    SOURCE=ROOT.parent/'loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz'

def test_previous_actual_input_sha_and_operators():
    p=source_only_certificate(SOURCE)
    assert p['source_npz_sha256']==EXPECTED_SHA
    assert p['new_shell_coefficients']==800
    assert p['n_selected_nside64_ring']==26846
    np.testing.assert_allclose(p['archived_old_ell6_16_operators']['ell2_5'],2.255720291177002,atol=1e-12,rtol=0)
    assert p['new_shell_actual_mask_specific_operator_norm']=='NOT_COMPUTED_SOURCE_MASK_UNAVAILABLE_IN_SANDBOX'


def test_source_input_tamper_rejects(tmp_path):
    content=bytearray(SOURCE.read_bytes())
    content[-1]^=1
    modified=tmp_path/'source.npz';modified.write_bytes(content)
    with pytest.raises(ValueError,match='SHA mismatch'):
        source_only_certificate(modified)


def test_conservative_mask_free_bound_vs_harmonic_coefficient_count():
    p=source_only_certificate(SOURCE)
    kappa=p['low_condition_from_prior_source']
    assert p['new_shell_conservative_operator_norm_upper']==pytest.approx(kappa*np.sqrt(800))
    assert p['combined_ell6_32_retained_ell2_5_operator_norm_interval'][1] > p['new_shell_conservative_operator_norm_upper']


def test_local_runner_root_resolution_matches_staged_git_layout(tmp_path):
    """Exact code/ nesting must resolve htt_base, not htt_base/docs."""
    import shutil,subprocess,os
    repo=tmp_path/'htt_base'
    unit=repo/'docs/research_program/theory_obs_application_20261015/loop10_smica_ell17_32_sandbox'
    (unit/'code').mkdir(parents=True)
    shutil.copy2(ROOT/'code/run_local_source.py',unit/'code/run_local_source.py')
    shutil.copy2(ROOT/'code/finite_shell_stream.py',unit/'code/finite_shell_stream.py')
    cmd=['python','-c',
         "import sys;sys.path.insert(0,"+repr(str(unit/'code'))+");import run_local_source; print(run_local_source.ROOT)"]
    p=subprocess.run(cmd,capture_output=True,text=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'1'})
    assert p.returncode==0,p.stderr
    assert pathlib.Path(p.stdout.strip())==repo
