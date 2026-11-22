"""Meaningful R98 NB1, QR, shared-patch and cache-boundary regressions."""
from __future__ import annotations
import hashlib,json,os
from types import SimpleNamespace
import numpy as np
import pytest
from scipy.stats import nbinom
from scripts.r98 import cross_survey as m

def test_nb1_probability_and_score_against_distribution():
    n=np.array([0.,1.,7.,22.,104.]); eta=np.log([.2,1.1,8.,25.,100.])
    for p in (.01,.12,.66,.98):
        l,s=m.logpmf_score(n,eta,p)
        ref=nbinom.logpmf(n,np.exp(eta)*(1-p)/p,1-p)
        np.testing.assert_allclose(l,ref,rtol=2e-10,atol=2e-10)
        step=2e-5
        numeric=(m.logpmf_score(n,eta+step,p)[0]-m.logpmf_score(n,eta-step,p)[0])/(2*step)
        np.testing.assert_allclose(s,numeric,rtol=5e-5,atol=2e-7)

def test_qr_changes_coordinates_without_ridge_or_law_change():
    rng=np.random.default_rng(9801);X=np.c_[np.ones(500),rng.normal(size=(500,3))]
    y=rng.poisson(np.exp(X@np.array([3,.1,-.15,.07])))
    T=np.array([[1.,0,0,0],[0,1,1000,0],[0,0,.1,0],[0,0,0,10.]])
    for model in ("poisson","nb1"):
        a=m.fit_count_model(y,X,model);b=m.fit_count_model(y,X@T,model)
        np.testing.assert_allclose(X@a["beta"],X@T@b["beta"],atol=3e-7,rtol=1e-7)
        assert abs(a["nll"]-b["nll"])<1e-10

def test_joint_patch_contrast_contains_shared_cross_terms():
    rng=np.random.default_rng(9802);a=rng.normal(size=(48,3));b=2*a
    C=m.jackknife_cov(np.c_[a,b]);D=m.jackknife_cov(a-b)
    np.testing.assert_allclose(D,C[:3,:3]+C[3:,3:]-C[:3,3:]-C[3:,:3],atol=1e-12)
    assert np.linalg.norm(D-(C[:3,:3]+C[3:,3:]))>1
    assert np.linalg.matrix_rank(m.jackknife_cov(rng.normal(size=(48,160))))==47

def cache_fixture(tmp_path,monkeypatch):
    cache=tmp_path/"cache";cache.mkdir()
    paths=[tmp_path/str(i) for i in range(6)]
    for i,p in enumerate(paths):p.write_bytes(bytes([i])*8)
    reader=tmp_path/"reader.py";reader.write_text("# inherited reader\n")
    fake=SimpleNamespace(**dict(zip(("NHI_FITS","NVSS_GZ","RACS_GZ","SPICE_GZ","SUMSS_GZ","LOTSS_FITS"),paths)))
    monkeypatch.setattr(m,"CACHE",cache);monkeypatch.setattr(m,"RADIO_SOURCE",reader);monkeypatch.setattr(m,"load_radio",lambda:fake)
    cp=cache/"radio_full_maps.npz";cp.write_bytes(b"unused map payload")
    receipt=cache/"radio_full_maps_sources.json"
    identities={str(p):{"bytes":p.stat().st_size,"sha256":m.sha(p)} for p in paths};identities["reader_sha256"]=m.sha(reader)
    receipt.write_text(json.dumps(identities))
    now={str(p):{"bytes":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"inode":p.stat().st_ino} for p in paths}
    finger=cache/"radio_full_maps_fingerprints.json"
    finger.write_text(json.dumps({"fingerprints":now,"receipt_sha256":m.sha(receipt),"maps_sha256":m.sha(cp)}))
    return paths,cp,receipt,finger

def test_failed_fresh_audit_cannot_poison_stat_seal(tmp_path,monkeypatch):
    paths,cp,receipt,finger=cache_fixture(tmp_path,monkeypatch);before=finger.read_bytes()
    p=paths[0];old=p.stat().st_mtime_ns;p.write_bytes(b"modified")
    os.utime(p,ns=(old+10**9,old+10**9))
    with pytest.raises(RuntimeError,match="source storage identity changed"):m.radio_run()
    with pytest.raises(RuntimeError,match="cached maps/input identity mismatch"):m.radio_run(audit_inputs=True)
    assert finger.read_bytes()==before
    with pytest.raises(RuntimeError,match="source storage identity changed"):m.radio_run()

def test_cached_map_and_receipt_are_bound_to_seal(tmp_path,monkeypatch):
    paths,cp,receipt,finger=cache_fixture(tmp_path,monkeypatch)
    cp.write_bytes(b"modified map")
    with pytest.raises(RuntimeError,match="map/receipt digest changed"):m.radio_run()

def test_exact_spherical_log_dipole_has_regular_zero_limit():
    np.testing.assert_array_equal(m.exact_log_dipole([0,0,0]),np.zeros(3))
    from numpy.polynomial.legendre import leggauss
    x,w=leggauss(160)
    for b in (1e-6,.1,.7):
        expected=3*np.sum(w*x*np.exp(b*x))/np.sum(w*np.exp(b*x))
        np.testing.assert_allclose(m.exact_log_dipole([b,0,0])[0],expected,rtol=1e-8,atol=1e-13)

def test_raw_audit_does_not_reseal_a_changed_map(tmp_path,monkeypatch):
    paths,cp,receipt,finger=cache_fixture(tmp_path,monkeypatch);before=finger.read_bytes()
    np.savez(cp,map__NVSS__20=np.array([99.]))
    with pytest.raises(RuntimeError,match="map/receipt digest changed"):m.radio_run(audit_inputs=True)
    assert finger.read_bytes()==before


def test_subspace_mahalanobis_and_4shell_z_slope_no_inversion():
    rng = np.random.default_rng(9847)
    names = ["a", "b", "c", "d", "e", "f", "quaia_z0", "quaia_z1", "quaia_z2", "quaia_z3"]
    # Rank-deficient 48-patch jackknife covariance (48 < 160 -> exact singular in 160D)
    patches = rng.normal(scale=0.5, size=(48, 160))
    C = m.jackknife_cov(patches)
    assert np.linalg.matrix_rank(C) == 47
    theta = np.zeros(160)
    # Inject a known linear-in-z E2 signal across quaia_z0..z3 at z=[0.5, 1.1, 1.8, 2.4]
    z_med = [0.5, 1.1, 1.8, 2.4]
    zc = np.array(z_med) - np.mean(z_med)
    slope_true = np.array([2.0, -1.0, 0.5, 0.0, 1.5])
    const_true = np.array([1.0, 0.5, -0.2, 0.3, -0.4])
    fits_out = {}
    leaves = {}
    for i, name in enumerate(names):
        vec = np.zeros(16)
        if name.startswith("quaia_z"):
            zi = int(name[-1])
            vec[6:11] = const_true + zc[zi] * slope_true
        theta[16 * i : 16 * (i + 1)] = vec
        fits_out[name] = {"coefs_microasyr": vec.tolist()}
        leaves[name] = patches[:, 16 * i : 16 * (i + 1)]
    out = m.gaia_subspace_and_optical_audit(names, fits_out, leaves, C, z_med)
    assert out["full_160D_subspace_projection"]["numerical_rank"] == 47
    assert out["full_160d_inversion_avoided"] is True
    e2_fit = out["quaia_4shell_scan_and_finite_z_transfer"]["E2_5"]
    assert e2_fit["subspace_rank"] == 20
    assert e2_fit["delta_chi2_for_z_slope"] > 0.0
    assert e2_fit["z_slope_norm_microasyr_per_z"] > 1.0
