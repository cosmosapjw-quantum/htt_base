"""Published FLRW reference and exact observable method-mix accounting tests."""
import numpy as np
import pytest
from obsstat.htt_hubble_depth_window import C_KM_S,K_LOG
from obsstat.cf4_apparent_kinematic_distribution import luminosity_distance_flat_lcdm
from obsstat.cf4_flrw_method_decomposition import (
    DepthMethodDomainError,flrw_log_cz_over_luminosity,
    exact_symmetric_decomposition,method_depth_source_moments,
    reference_residual_moments,constant_method_standardization,
)


def fake_flat_sources(seed=2,n=100):
    rng=np.random.default_rng(seed)
    bins=[(.01,.035),(.035,.075),(.075,.11)]
    methods=np.asarray(["FP","SN","TF","OTHER"])
    z=[];mod=[];ff=[]
    for low,hi in bins:
        for m in methods:
            zz=rng.uniform(low+.0001,hi-.0001,n)
            d_l,*_=luminosity_distance_flat_lcdm(zz,H0=74.6,omega_m=.3153)
            z.extend(zz);mod.extend(25+5*np.log10(d_l));ff.extend([m]*n)
    z=np.array(z);mod=np.array(mod);ff=np.asarray(ff)
    return z,mod,np.full(len(z),.2),ff,np.arange(len(z)),bins


def test_isotropic_flatlcdm_proxy_has_declining_cz_over_dL_even_when_lcdm():
    z=np.array([.01,.03,.05,.075,.1])
    measured=flrw_log_cz_over_luminosity(z)
    assert np.all(np.diff(measured)<0)
    # For q0=(3/2)Omega_m -1, dL=(c/H0)[z+(1-3Omega_m/4)z^2+...].
    h0=74.6;om=.3153
    expected=(1-3*om/4)
    slopes=(np.log(h0)-measured)/z
    assert abs(slopes[0]-expected)<.02


def test_isotropic_ref_catalog_zero_residual_at_actual_each_source_redshift():
    z,mu,err,methods,ids,bins=fake_flat_sources()
    a=method_depth_source_moments(z,mu,err,methods,ids,bins)
    b=reference_residual_moments(a,z)
    np.testing.assert_allclose(b["residual_method_logh_mean"],0.,atol=1e-13)
    np.testing.assert_allclose(b["residual_shell_logh"],0.,atol=1e-13)
    assert a["method_weight_fraction"].shape==(3,4)


def test_symmetric_exact_decomposition_and_center_shift_invariance():
    f0=np.array([.2,.7,.1]);f1=np.array([.7,.1,.2])
    y0=np.array([3.,4.,5.]);y1=np.array([2.,1.,6.])
    out=exact_symmetric_decomposition(f0,f1,y0,y1)
    assert out["total"]==pytest.approx(f1@y1-f0@y0)
    assert out["total"]==pytest.approx(out["composition"]+out["within_method"])
    shift=1e9
    y0s=y0+shift;y1s=y1+shift
    altered=exact_symmetric_decomposition(f0,f1,y0s,y1s)
    assert altered["total"]==pytest.approx(out["total"],abs=5e-7)
    assert altered["composition"]==pytest.approx(out["composition"],abs=5e-7)


def test_constant_method_zero_points_cancel_from_fixed_standardized_contrast():
    z,mu,err,methods,ids,bins=fake_flat_sources()
    first=method_depth_source_moments(z,mu,err,methods,ids,bins)
    residual=reference_residual_moments(first,z)
    std=constant_method_standardization(first,residual["residual_method_logh_mean"])
    labels=first["method_names"]
    offset=dict(FP=.14,SN=-.05,TF=.2,OTHER=-.04)
    moved=mu+np.array([offset[str(m)] for m in methods])
    other=method_depth_source_moments(z,moved,err,methods,ids,bins)
    other_res=reference_residual_moments(other,z)
    follow=constant_method_standardization(other,other_res["residual_method_logh_mean"],
                                            policy="declared",declared_weights=std["method_mix_pi"])
    d1=np.diff(std["logh"]);d2=np.diff(follow["logh"])
    np.testing.assert_allclose(d1,d2,atol=2e-14)
    assert np.linalg.norm(follow["logh"])>0


def test_fixed_standardized_variance_matches_direct_row_error_pushforward():
    z,mu,err,method,ids,bins=fake_flat_sources(n=50)
    a=method_depth_source_moments(z,mu,err,method,ids,bins)
    std=constant_method_standardization(a,a["method_logh_means"])
    # Exact under declared diagonal source law; no empirical covariance claim.
    rows=np.einsum("m,jmi->ji",std["method_mix_pi"],a["method_cell_source_weights"])
    cv=(rows*a["source_sigma"][None,:]**2)@rows.T
    np.testing.assert_allclose(np.diag(cv),std["variance_diagonal"],rtol=2e-13)
    assert np.max(abs(cv-np.diag(np.diag(cv))))<1e-17


def test_ref_H0_shifts_all_windows_equally_but_depth_residual_contrast_invariant():
    z,mu,err,methods,ids,bins=fake_flat_sources()
    a=method_depth_source_moments(z,mu,err,methods,ids,bins)
    a0=reference_residual_moments(a,z,H0=74.6,omega_m=.3153)
    a1=reference_residual_moments(a,z,H0=70,omega_m=.3153)
    np.testing.assert_allclose(np.diff(a0["residual_shell_logh"]),
                              np.diff(a1["residual_shell_logh"]),atol=2e-14)
    assert np.linalg.norm(a1["residual_shell_logh"])>.01
    changed=reference_residual_moments(a,z,H0=74.6,omega_m=.25)
    assert np.linalg.norm(a0["residual_shell_logh"]-changed["residual_shell_logh"])>1e-4


def test_small_cell_support_ESS_and_missing_method_refused():
    z,mu,err,method,ids,bins=fake_flat_sources(n=20)
    a=method_depth_source_moments(z,mu,err,method,ids,bins)
    assert np.min(a["counts"])==20
    assert np.all(a["effective_n_by_method_cell"]<=a["counts"]+1e-9)
    wrong=method.copy()
    wrong[(z>.075)&(wrong=="SN")]="FP"
    with pytest.raises(DepthMethodDomainError,match="absent"):
        method_depth_source_moments(z,mu,err,wrong,ids,bins)
    with pytest.raises(DepthMethodDomainError,match="unique"):
        method_depth_source_moments(z,mu,err,method,np.zeros(len(ids),int),bins)
    with pytest.raises(DepthMethodDomainError):
        constant_method_standardization(a,a["method_logh_means"],policy="declared",
                                        declared_weights=[.5,.5,0.,.4])


def test_real_cf4_35970_source_H01_and_method_background_decomposition_parity():
    import hashlib,json
    from pathlib import Path
    source=Path(__file__).resolve().parents[2]/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
    prior=Path(__file__).resolve().parents[2]/"docs/research_program/observational_publication_20261015/results/H01_actual_cf4_v1/result.json"
    assert hashlib.sha256(source.read_bytes()).hexdigest()=="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
    with np.load(source,allow_pickle=False) as v:
        z=v["z_CMB"];mu=v["dmzp"];s=v["e_dmzp"];f=v["method_family"];ids=v["group_id"]
    out=method_depth_source_moments(z,mu,s,f,ids,[(.01,.03),(.03,.05),(.05,.075),(.075,.10)])
    ref=reference_residual_moments(out,z)
    j=json.loads(prior.read_text())
    assert int(out["counts"].sum())==35970
    np.testing.assert_allclose(out["raw_shell_logh"],j["fit"]["logH_window_mean"][:4],atol=4e-14,rtol=0)
    decom=exact_symmetric_decomposition(
      out["method_weight_fraction"][0],out["method_weight_fraction"][-1],
      ref["residual_method_logh_mean"][0],ref["residual_method_logh_mean"][-1])
    assert decom["total"]==pytest.approx(-.027213430044946658,abs=5e-12)
    assert decom["composition"]>0 and decom["within_method"]<0
    assert out["counts"][-1,out["method_names"].index("OTHER")]==8
    assert out["counts"][-1,out["method_names"].index("TF")]==14


def test_reference_removal_is_distinct_from_modulus_zero_point_calibration():
    z,mu,err,m,ids,bins=fake_flat_sources(n=15)
    # A flat isotropic distance curve does not imply zero apparent Hubble
    # redshift trend when the estimator is c*z/d_L.
    a=method_depth_source_moments(z,mu,err,m,ids,bins)
    h=a["raw_shell_logh"]
    assert h[0]>h[-1]  # geometric H_eff=c z/d_L naturally decreases
    ref=reference_residual_moments(a,z)
    assert np.max(abs(ref["residual_shell_logh"]))<1e-13
