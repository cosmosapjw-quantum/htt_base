"""Analytic falsifiers for cache-only RB17/20/21 adapters."""
import importlib.util
import os
from pathlib import Path

import numpy as np
import pytest

_candidate = os.environ.get("HTT_CACHE_DATA_CANDIDATE")
if _candidate:
    spec = importlib.util.spec_from_file_location("reboot_cache_data_suite", _candidate)
    suite = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(suite)
else:
    from scripts import reboot_cache_data_suite as suite


def test_amplitude_correlated_covariance_and_precision_scale():
    t = np.array([1., 2., 4.])
    c = np.array([[2., .5, 0.], [.5, 3., .4], [0., .4, 4.]])
    fit = suite.amplitude_fit(1.7*t, t, c, .8)
    assert fit["amplitude"] == pytest.approx(1.7)
    assert fit["residual_quadratic"] == pytest.approx(0, abs=1e-28)
    assert fit["conditional_se"] == pytest.approx((.8*t@np.linalg.solve(c,t))**-.5)
    assert fit["calibrated_chi2_p"] is None


def test_marginal_deletion_is_not_precision_submatrix_conditioning():
    covariance = np.array([[2., 1.], [1., 3.]])
    precision = np.linalg.inv(covariance)
    marginal = suite.marginal_precision(precision, [0])
    assert marginal[0,0] == pytest.approx(.5)
    assert marginal[0,0] != pytest.approx(precision[0,0])


def test_common_offset_cancels_after_marginal_deletion():
    c = np.array([[2., .5, .2], [.5, 3., .3], [.2, .3, 4.]])
    p = suite.marginal_precision(np.linalg.inv(c), [0,2])
    model = np.array([.2, .4]); mu = np.array([1.5, 1.9])
    a, q = suite.offset_profile(mu, model, p)
    shifted, shifted_q = suite.offset_profile(mu+20, model, p)
    assert shifted == pytest.approx(a+20)
    assert shifted_q == pytest.approx(q, abs=1e-13)
    method_a = np.array([30.1,31.2]); method_b = np.array([30.,31.])
    common = np.array([100.,-20.])
    assert np.allclose((method_a+common)-(method_b+common), method_a-method_b)


def test_box_cluster_mean_variance_geometry():
    # Two repeated observers per box: mean uncertainty is box-based.
    box = np.repeat(np.arange(4), 2)
    y = np.repeat(np.array([-3.,-1.,1.,3.]), 2)[:,None]
    feature, iid, cluster = suite.mean_covariances_by_box(y, box)
    assert feature[0,0] == pytest.approx(40/7)
    assert iid[0,0] == pytest.approx(5/7)
    assert cluster[0,0] == pytest.approx(5/3)
    # Singleton boxes recover ordinary sample covariance of the mean.
    _, ordinary, singleton = suite.mean_covariances_by_box(y, np.arange(8))
    assert np.allclose(ordinary, singleton)


def test_no_covariance_repair_or_nan_output_shortcut():
    with pytest.raises(np.linalg.LinAlgError):
        suite.amplitude_fit(np.ones(2), np.ones(2), np.diag([1.,-1.]))
    with pytest.raises(ValueError):
        suite.amplitude_fit(np.ones(2), np.ones(2), np.eye(2), 0)
    with pytest.raises(ValueError):
        suite.mean_covariances_by_box(np.array([[np.nan],[1.]]), np.array([0,1]))


def test_cli_lensing_synthetic_release_creates_bound_outputs(tmp_path):
    import json
    root = tmp_path / 'repo'
    base = root / 'workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2'
    (base/'like_corrs').mkdir(parents=True)
    wa = np.zeros((18,3000)); wa[np.arange(18),np.arange(20,38)] = 1
    wp = np.zeros((9,3000)); wp[np.arange(9),np.arange(100,109)] = 1
    kk = np.ones(3000)*2
    np.savetxt(base/'binning_matrix_act.txt',wa)
    np.savetxt(base/'binning_matrix_planck.txt',wp)
    np.savetxt(base/'clkk_bandpowers_act.txt',1.2*wa@kk)
    np.savetxt(base/'clkk_bandpowers_planck.txt',1.2*wp@kk)
    np.savetxt(base/'covmat_act_cmbmarg.txt',np.eye(18))
    joint = np.eye(27);joint[:18,18:] = .01;joint[18:,:18] = .01
    np.savetxt(base/'covmat_actplanck_cmbmarg.txt',joint)
    fid = np.zeros((2998,8));fid[:,0] = np.arange(2,3000);fid[:,5] = 4/np.pi
    np.savetxt(base/'like_corrs/cosmo2017_10K_acc3_lenspotentialCls.dat',fid)
    (base/'README').write_text('Synthetic release fixture; not observational data.')
    out = tmp_path/'output'
    assert suite.main(['lensing','--repo-root',str(root),'--output',str(out)]) == 0
    assert {'result.json','diagnostic.png','diagnostic.pdf','report.md','execution_receipt.json'} <= {p.name for p in out.iterdir()}
    result = json.loads((out/'result.json').read_text())
    assert [len(r['data']) for r in result['scenarios']] == [10,19,13,22]
    assert all(r['amplitude'] == pytest.approx(1.2) for r in result['scenarios'])
    receipt = json.loads((out/'execution_receipt.json').read_text())
    assert receipt['exit_code'] == 0 and len(receipt['sources']) == 8
    with pytest.raises(FileExistsError):
        suite.main(['lensing','--repo-root',str(root),'--output',str(out)])


def test_uniform_amplitude_posterior_matches_injected_truncated_density():
    from scipy.integrate import quad
    from scipy.stats import norm
    out=suite.uniform_amplitude_posterior(.2,.3)
    mass=norm.cdf((2-.2)/.3)-norm.cdf((0-.2)/.3)
    density=lambda a: norm.pdf(a,.2,.3)/mass
    assert out['normalizing_gaussian_mass']==pytest.approx(mass)
    assert quad(density,0,2)[0]==pytest.approx(1,abs=1e-12)
    assert out['mean']==pytest.approx(quad(lambda a:a*density(a),0,2)[0],abs=1e-11)
    assert out['variance']==pytest.approx(quad(lambda a:(a-out['mean'])**2*density(a),0,2)[0],abs=1e-11)
    assert out['quantiles']['0.5']>0
    assert out['quantiles']['0.975']<2
    assert out['probability_above_one']==pytest.approx(quad(density,1,2)[0],abs=1e-12)


def _planck_marginal_fixture(tmp_path):
    import json
    root=tmp_path/'repo'
    base=root/'workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2'
    (base/'like_corrs').mkdir(parents=True)
    window=np.zeros((9,3000))
    window[np.arange(9),np.arange(100,109)]=1
    np.savetxt(base/'binning_matrix_planck.txt',window)
    np.savetxt(base/'clkk_bandpowers_planck.txt',np.full(9,2.6))
    joint_cov=np.eye(27)
    joint_cov[18,19]=joint_cov[19,18]=.3
    joint_cov[0,18]=joint_cov[18,0]=.4
    np.savetxt(base/'covmat_actplanck_cmbmarg.txt',joint_cov)
    fid=np.zeros((2998,8));fid[:,0]=np.arange(2,3000);fid[:,5]=4/np.pi
    np.savetxt(base/'like_corrs/cosmo2017_10K_acc3_lenspotentialCls.dat',fid)
    (base/'README').write_text('Synthetic release fixture; not observational data.')
    retained=root/'docs/observational_reboot_20261014/results/cache_lensing_v1'
    retained.mkdir(parents=True)
    prior={'release':'ACT DR6 lensing likelihood v1.2','scenarios':[
        {'name':'act_planck_baseline','release_indices':list(range(2,12))+list(range(18,27)),
         'data':[1.]*10+[2.6]*9,'reference':[1.]*10+[2.]*9}]}
    (retained/'result.json').write_text(json.dumps(prior))
    return root,base,retained,joint_cov


def test_planck_marginal_is_covariance_subset_then_inverse(tmp_path):
    root,_,_,joint_cov=_planck_marginal_fixture(tmp_path)
    result,files=suite.planck_marginal_amplitude(root)
    block=joint_cov[18:,18:]
    t=np.full(9,2.)
    alpha19=(400-19-2)/399
    alpha9=(400-9-2)/399
    expected=suite.amplitude_fit(np.full(9,2.6),t,block,alpha19)
    assert result['amplitude']==pytest.approx(1.3)
    assert result['conditional_se']==pytest.approx(expected['conditional_se'])
    assert result['primary_precision_scale']==pytest.approx(alpha19)
    assert result['alpha9_covariance_estimate_sensitivity']['precision_scale']==pytest.approx(alpha9)
    assert result['alpha9_covariance_estimate_sensitivity']['amplitude']==pytest.approx(1.3)
    assert result['chi_square_descriptor_optimized_A']==pytest.approx(0,abs=1e-28)
    assert result['chi_square_descriptor_fixed_A1']>0
    assert not np.allclose(np.linalg.inv(block),np.linalg.inv(joint_cov)[18:,18:])
    assert len(files)==6
    predictive=result['posterior_predictive_conditional_covariance']
    assert np.all(np.linalg.eigvalsh(predictive['covariance'])>0)
    assert predictive['status'].endswith('NO_CALIBRATED_P_VALUE')
    assert result['calibrated_chi2_p'] is None


def test_planck_marginal_rejects_retained_joint_source_drift(tmp_path):
    import json
    root,_,retained,_=_planck_marginal_fixture(tmp_path)
    path=retained/'result.json'
    old=json.loads(path.read_text());old['scenarios'][0]['reference'][-1]=99
    path.write_text(json.dumps(old))
    with pytest.raises(ValueError,match='retained joint Planck bins/reference'):
        suite.planck_marginal_amplitude(root)


def test_planck_marginal_cli_fixture_writes_diagnostic_report_and_receipts(tmp_path):
    import json
    root,_,_,_=_planck_marginal_fixture(tmp_path)
    out=tmp_path/'planck_output'
    assert suite.main(['planck-marginal','--repo-root',str(root),'--output',str(out)])==0
    assert {'result.json','diagnostic.png','diagnostic.pdf','report.md','execution_receipt.json'} <= {p.name for p in out.iterdir()}
    result=json.loads((out/'result.json').read_text())
    receipt=json.loads((out/'execution_receipt.json').read_text())
    assert result['scope']=='PLANCK_NINE_BIN_MARGINAL_FIXED_REFERENCE_AMPLITUDE'
    assert result['proper_uniform_amplitude_posterior']['prior_bounds']==[0,2]
    assert len(result['data'])==len(result['reference'])==9
    assert len(receipt['sources'])==6
    assert 'never multiply' in (out/'report.md').read_text()
