"""Falsifiers for the exact-source Planck PR3 PP amplitude contraction."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

PATH=Path(__file__).resolve().parents[2]/"scripts/reboot_planck_pr3_lensing.py"
spec=importlib.util.spec_from_file_location("planck_pr3_candidate",PATH)
pr3=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=pr3
spec.loader.exec_module(pr3)


def test_affine_gls_and_consistent_bin_covariance_permutation():
    a=np.linspace(.5,1.5,9)
    c=np.linspace(-.3,.1,9)
    y=1.17*a+c
    m=np.eye(9)*.7+.03*np.ones((9,9))
    cov=m@m.T
    fit=pr3.affine_fit(y,a,c,cov)
    assert fit["amplitude"]==pytest.approx(1.17)
    assert fit["optimized_chi_square_descriptor"]==pytest.approx(0,abs=1e-27)
    assert fit["reference_A1_chi_square_descriptor"]>0
    p=np.array([8,0,4,2,7,1,6,3,5])
    shuffled=pr3.affine_fit(y[p],a[p],c[p],cov[np.ix_(p,p)])
    assert shuffled["amplitude"]==pytest.approx(fit["amplitude"],rel=1e-12)
    assert shuffled["conditional_se"]==pytest.approx(fit["conditional_se"],rel=1e-12)
    assert pr3.affine_fit(y[p],a,c,cov)["amplitude"]!=pytest.approx(fit["amplitude"],abs=1e-4)


def test_affine_response_differences_and_declared_posterior():
    a=np.arange(1,10)*.01
    c=np.full(9,.13)
    model=lambda A:A*a+c
    assert np.allclose(model(1.2)-model(.8),.4*a)
    assert np.allclose((model(1+1e-4)-model(1-1e-4))/(2e-4),a,rtol=1e-12)
    posterior=pr3.bounded_posterior(.2,.3)
    mass=norm.cdf((2-.2)/.3)-norm.cdf((0-.2)/.3)
    density=lambda value:norm.pdf(value,.2,.3)/mass
    assert posterior["normalizing_gaussian_mass"]==pytest.approx(mass)
    assert posterior["mean"]==pytest.approx(quad(lambda x:x*density(x),0,2)[0],abs=1e-11)
    assert posterior["variance"]==pytest.approx(quad(lambda x:(x-posterior["mean"])**2*density(x),0,2)[0],abs=1e-11)
    assert 0<posterior["quantiles"]["0.025"]<posterior["quantiles"]["0.975"]<2


def test_window_raw_support_and_reject_truncation(tmp_path):
    path=tmp_path/"window.dat"
    np.savetxt(path,np.array([[1,7.],[2,3.],[450,5.],[2500,2.]]))
    (ell,weights),receipt=pr3.read_window(path,["PP"])
    assert ell.tolist()==[2,450,2500]
    assert receipt["outside_native_support_nonzero"]==1
    spectrum=np.zeros(2501);spectrum[450]=1
    assert pr3.window_product([(ell,weights)],["PP"],{"PP":spectrum})[0]==5
    np.savetxt(path,np.array([[2,1.],[2501,3.]]))
    with pytest.raises(ValueError,match="support"):
        pr3.read_window(path,["PP"])


def test_pp_header_covariance_and_missing_source_fail_closed(tmp_path):
    path=tmp_path/"bandpowers.dat"
    np.savetxt(path,np.tile(np.arange(7.),(9,1)),header="bin L_min L_max L_av PT Error Ahat")
    with pytest.raises(ValueError,match="PP column"):
        pr3.read_bandpowers(path)
    with pytest.raises(FileNotFoundError):
        pr3.read_window(tmp_path/"missing-window.dat",["PP"])
    with pytest.raises(ValueError,match="finite real"):
        pr3.covariance9(np.eye(9,dtype=complex))
    with pytest.raises(np.linalg.LinAlgError):
        pr3.covariance9(np.diag([0.]+[1.]*8))
    asymmetric=np.eye(9);asymmetric[0,1]=1e-3
    with pytest.raises(ValueError,match="antisymmetry"):
        pr3.covariance9(asymmetric)


def test_exact_released_windows_pp_column_and_native_parity():
    root=Path.cwd()
    if not (root/pr3.DATA_REL/pr3.MARG).exists():
        pytest.skip("exact Planck PR3 native dataset unavailable")
    base=root/pr3.DATA_REL
    marg=pr3.read_variant(base,pr3.MARG,marginal=True)
    nonmarg=pr3.read_variant(base,pr3.BASE,marginal=False)
    assert marg["data"].shape==(9,) and marg["data"][0]==pytest.approx(1.4696e-7)
    assert marg["data"][0]!=pytest.approx(1.321e-8)
    assert marg["response_order"]==["PP"]
    assert nonmarg["response_order"]==["TT","EE","TE","PP"]
    spectrum=np.zeros(4097);spectrum[432]=1
    assert np.allclose(pr3.window_product(marg["ordinary"],["PP"],{"PP":spectrum}),0)
    assert np.any(pr3.window_product(marg["response"],["PP"],{"PP":spectrum})!=0)
    result=pr3.evaluate(root)
    assert [v["variant"] for v in result["variants"]]==["CMB_MARGINALIZED","NONMARGINAL_FIXED_CMB"]
    for variant in result["variants"]:
        assert len(variant["native_parity"]["rows"])==3
        assert all(row["whitened_model_difference"]<=1e-9 for row in variant["native_parity"]["rows"])
        assert all(row["absolute_chi_square_difference"]<=1e-8*(1+abs(row["chi_square_own"]))
                   for row in variant["native_parity"]["rows"])
        assert variant["fit"]["conditional_se"]>0
    assert result["calibrated_null_PTE"] is None


def test_saved_full_covariance_profile_has_saved_peak_and_A1_curvature():
    path=Path.cwd()/"docs/observational_reboot_20261014/results/planck_pr3_exact_v1/result.json"
    if not path.exists():
        pytest.skip("saved exact-source Planck result absent")
    saved=json.loads(path.read_text())
    for row in saved["variants"]:
        ahat=row["fit"]["amplitude"]
        information=row["fit"]["information"]
        q=pr3.saved_quadratic_profile(row,np.array([ahat,1.,ahat+.1]))
        assert q[0]==pytest.approx(row["fit"]["optimized_chi_square_descriptor"],rel=1e-12)
        assert q[1]-q[0]==pytest.approx(information*(1-ahat)**2,rel=1e-10,abs=1e-10)
        assert q[2]-q[0]==pytest.approx(information*.1**2,rel=1e-10,abs=1e-10)


def test_saved_result_hash_guard_rejects_source_drift(tmp_path):
    path=Path.cwd()/"docs/observational_reboot_20261014/results/planck_pr3_exact_v1/result.json"
    if not path.exists():
        pytest.skip("saved exact-source Planck result absent")
    wrong=json.loads(path.read_text())
    wrong["source_files"][0]["sha256"]="0"*64
    dest=tmp_path/"result.json";dest.write_text(json.dumps(wrong))
    with pytest.raises(ValueError,match="source identity mismatch"):
        pr3.source_bound_saved_result(Path.cwd(),dest)


def test_saved_peak_closeout_renders_fresh_without_touching_original(tmp_path):
    root=Path.cwd()
    path=root/"docs/observational_reboot_20261014/results/planck_pr3_exact_v1/result.json"
    if not path.exists():
        pytest.skip("saved exact-source Planck result absent")
    original=pr3.sha256(path)
    receipt=pr3.sha256(path.parent/"execution_receipt.json")
    output=tmp_path/"closeout"
    assert pr3.main(["--repo-root",str(root),"--closeout-from-result",str(path),
                     "--output",str(output)])==0
    assert {"closeout.json","repair_receipt.json","report.md","peak_closeout.png","peak_closeout.pdf"} <= {p.name for p in output.iterdir()}
    closeout=json.loads((output/"closeout.json").read_text())
    assert closeout["binding"]["result_sha256"]==original
    assert closeout["binding"]["original_execution_receipt_sha256"]==receipt
    assert closeout["binding"]["verified_source_count"]>=30
    assert len(closeout["peak_checks"])==2
    for check in closeout["peak_checks"]:
        assert check["saved_fit_reused_without_refit"] is True
        row=check["native_peak_call"]
        assert row["A"]==pytest.approx(check["saved_amplitude"])
        assert row["whitened_model_difference"]<=1e-9
        assert row["absolute_chi_square_difference"]<=1e-8*(1+abs(row["chi_square_own"]))
    assert pr3.sha256(path)==original
    assert pr3.sha256(path.parent/"execution_receipt.json")==receipt
