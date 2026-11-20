"""R81 PHY-01..07 / SQ-NATIVE / E0,E1 coding preflight tests.

Physics states are conditional or synthetic; real source checks use frozen R77/R80
and selected CF4 files. Invalid/missing source must not produce astrophysical Pi.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import chi2
from htt.obsstat.pre_dag_fast import hemisphere_moments, radial_design, codazzi_map
from scripts.r68.fiveview_geometry import E, stf_matrix, stf_coordinates

HERE=Path("docs/research_program/observational_publication_20261015")
SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
R77=HERE/"R77_SEVEN_PHY_CROSSVIEW_20261119/RESULTS.json"
R80=HERE/"R80_SQ_CF4_SOURCE_BINDING_20261120/RESULT.json"

def phy():
    from htt.obsstat import phy_fast
    return phy_fast

def sample_axes(m=32):
    k=np.arange(m,dtype=float)
    z=1-2*(k+.5)/m
    phi=np.mod(k*np.pi*(3-np.sqrt(5)),2*np.pi)
    return np.column_stack([np.sqrt(1-z*z)*np.cos(phi),
                            np.sqrt(1-z*z)*np.sin(phi),z])

def test_11_external_solver_input_missing_is_blocked_not_simulated(tmp_path):
    p=tmp_path/"nonexistent_manifest.json"
    with pytest.raises(FileNotFoundError):
        phy().inspect_external_native(p)
    assert not list(tmp_path.glob("*.npz"))

def test_11_external_solver_source_digest_and_physical_claim_are_separate(tmp_path):
    payload=tmp_path/"native_from_external.npz"
    np.savez(payload,ell=np.array([2,2,2,2,2]),m=np.arange(-2,3),
             E=np.arange(5,dtype=float),B=np.zeros(5))
    h=hashlib.sha256(payload.read_bytes()).hexdigest()
    manifest=tmp_path/"manifest.json"
    manifest.write_text(json.dumps({"schema":"htt.external_bianchi_polarized/1",
       "source_kind":"external_native_result","solver_commit":"actual_source_not_qualified",
       "model_family":"Bianchi_V", "observer_frame":"normal_freely_propagated",
       "units":"dimensionless_photon_TEB","data_file":payload.name,
       "data_sha256":h}))
    out=phy().inspect_external_native(manifest)
    assert out["source_hash_matches"]
    assert out["physical_transfer_qualified"] is False
    manifest.write_text(manifest.read_text().replace(h,"0"*64))
    with pytest.raises(ValueError,match="sha256"):
        phy().inspect_external_native(manifest)

def test_12_many_axes_numpy_reference_and_input_validation():
    rng=np.random.default_rng(77)
    n=rng.normal(size=(1307,3));n/=np.linalg.norm(n,axis=1)[:,None]
    axes=sample_axes(34)
    w=rng.uniform(.1,2.,size=len(n))
    got=phy().multi_axis_hemisphere(n,axes,weights=w,native_lib=None)
    assert got["counts"].shape==(len(axes),2)
    for k in range(len(axes)):
        ref=hemisphere_moments(n,axes[k],weights=w,native_lib=None)
        for key in ("weights","means","second","counts"):
            np.testing.assert_allclose(got[key][k],ref[key],atol=1e-12,rtol=1e-12)
    with pytest.raises(ValueError):
        phy().multi_axis_hemisphere(n,axes,weights=-w)

def test_12_native_batch_when_library_available():
    import os
    path=os.environ.get("HTT_R81_MASK_SO")
    if not path:pytest.skip("R81 Fortran not explicitly compiled")
    rng=np.random.default_rng(5)
    n=rng.normal(size=(5107,3));n/=np.linalg.norm(n,axis=1)[:,None]
    axes=sample_axes(64)
    w=rng.uniform(.1,1.9,len(n))
    ref=phy().multi_axis_hemisphere(n,axes,weights=w,native_lib=None)
    for threads in (1,4):
        got=phy().multi_axis_hemisphere(n,axes,weights=w,native_lib=path,threads=threads)
        for k in ("weights","means","second","counts"):
            np.testing.assert_allclose(got[k],ref[k],atol=2e-11,rtol=2e-11)
    assert phy().last_phy_receipt()["used"]=="fortran_batch"

def test_12_true_source_selected_and_fullraw_not_same_footprint():
    d=json.loads(R80.read_text())["angular_mask_diagnostics"]
    assert d["selected_40_400"]["n"]==31382
    assert d["full_table4_40_400"]["n"]==31649
    assert d["selected_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"]!=d["full_table4_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"]

def test_13_photon_covariance_and_codazzi_source_null():
    a=np.array([1.,0,0]);N=np.diag([0.,3.,-3.])
    M=codazzi_map(a,N)
    shear=np.array([-.2,.1,.03,.04,.02])
    S=np.zeros((3,3))
    blocked=phy().photon_codazzi_feasibility(S,shear,LieM=M,Omega=.3,eta=.2,f=None)
    assert blocked["photon_flux_missing"]
    assert blocked["physical_Pi"] is None
    f=np.array([.1,0,0])
    result=phy().photon_codazzi_feasibility(S,shear,LieM=M,Omega=.3,eta=.2,f=f)
    assert result["photon_psd"]
    assert result["Codazzi_source_only_conditional"] is True
    with pytest.raises(ValueError):
        phy().photon_codazzi_feasibility(S,shear,LieM=M,Omega=0.,eta=.2,f=f)

def test_14_lorentz_photon_radio_shared_frame_and_beta_domain():
    beta=np.array([.002,0,0])
    x=phy().shared_beta_radio_photon(beta,k=3.8254286125,kappa=0)
    np.testing.assert_allclose(x["photon_flux"],4*beta/(3+beta@beta),rtol=2e-14)
    np.testing.assert_allclose(x["count_STF"],x["ratio"]*x["photon_STF"],rtol=2e-13,atol=1e-20)
    assert x["source_qualified"] is False
    assert x["physical_Pi"] is None
    assert abs(x["photon_chi"]-1)<1e-12
    with pytest.raises(ValueError):
        phy().shared_beta_radio_photon(np.array([1.,0.,0.]),k=3.,kappa=0.)

def test_15_gaia_E2_B2_masked_Fisher_conditionals():
    source=json.loads((HERE/"R76_P6_COVARIANT_DRIFT_FIVEVIEW_20261119/RESULTS.json").read_text())
    gaia=json.loads((HERE/"R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json").read_text())
    for key in ("quality","quality_north","quality_south"):
        C=np.array(gaia["results"][key]["formal_cov_microasyr2"])
        got=phy().gaia_eb_mask_alias(C)
        ref=source["R69_Gaia_VSH_actual_source"]["results"][key]
        np.testing.assert_allclose(got["maxcanonical"],ref["E2_B2_profiled_design_maxcanonical"],
                                   rtol=1e-10,atol=1e-12)
    assert got["physical_vorticity_identified"] is False

def test_15_Lie_B2_tangent_orthogonality_and_normalization():
    rng=np.random.default_rng(3)
    n=rng.normal(size=(503,3));n/=np.linalg.norm(n,axis=1)[:,None]
    sigma=stf_matrix(np.array([-.02,.01,.005,0.,0.]))
    N=np.diag([.013,-.017,.004])
    e,b=phy().local_E2_and_Lie_B2(n,sigma,N)
    np.testing.assert_allclose(np.einsum("ni,ni->n",e,n),np.zeros(len(n)),atol=1e-15)
    np.testing.assert_allclose(np.einsum("ni,ni->n",b,n),np.zeros(len(n)),atol=1e-15)
    np.testing.assert_allclose(b,-np.cross(n,n@N.T),atol=1e-15)
    assert e.shape==b.shape==(len(n),3)

def test_16_normal_flux_residual_not_a_tautological_p_value():
    rng=np.random.default_rng(9)
    M=codazzi_map(np.array([1.,0,0]),np.diag([0.,3.,-3.]))
    x=rng.normal(size=5)
    C=np.diag([.02**2]*5+[.01**2]*3)
    u=-M@x/(3*.4)+np.array([.01,0.,-.01])
    b=phy().normal_flux_residual(x,u,M,Omega=.4,C_joint=C,independent_source=False)
    assert b["physical_Pi"] is None
    a=phy().normal_flux_residual(x,u,M,Omega=.4,C_joint=C,independent_source=True,
                                  calibrated_null=False)
    assert a["rank_covariance"]==3 and a["physical_Pi"] is None
    c=phy().normal_flux_residual(x,u,M,Omega=.4,C_joint=C,independent_source=True,
                                  calibrated_null=True)
    assert c["working_chi2"]>=0
    np.testing.assert_allclose(c["working_tail"],chi2.sf(c["working_chi2"],3))
    assert c["physical_Pi"] is None

def test_17_shear_shape_derivative_eigenframe_counterexample():
    S=np.diag([-.03,-.01,.04]);D=np.zeros((3,3));D[0,1]=D[1,0]=.01
    result=phy().shear_shape_rate(S,D,H=.1)
    assert abs(result["dchi"])<1e-12
    assert result["commutator_norm"]>1e-5
    assert result["signed_tensor_evolves"] is True
    assert phy().shear_shape_rate(np.zeros((3,3)),D,H=.1)["chi"] is None

def test_17_photon_l4_nonclosure_exact_F_and_stress_derivative():
    x=phy().photon_l4_family(0.0,threshold=.9,shear_s=.07)
    y=phy().photon_l4_family(1.0,threshold=.9,shear_s=.07)
    assert abs(x["cap_F"]-.1)<1e-14
    assert abs(y["cap_F"]-.15707125)<1e-10
    assert abs((y["source_stress_derivative_zz"]-x["source_stress_derivative_zz"])-8*.07/315)<1e-13

def test_18_conditional_diagonal_weighted_gram_native_and_numpy():
    import os
    rng=np.random.default_rng(11)
    n=rng.normal(size=(2001,3));n/=np.linalg.norm(n,axis=1)[:,None]
    X=radial_design(rng.uniform(40,400,len(n)),n)
    w=rng.uniform(.5,3.,size=len(n));y=rng.normal(size=len(n))
    ref=phy().weighted_radial_stats(X,w,y,native_lib=None)
    so=os.environ.get("HTT_R81_GRAM_SO")
    if not so:pytest.skip("optional C++ source not built")
    got=phy().weighted_radial_stats(X,w,y,native_lib=so,threads=4)
    for x,y in zip(got,ref):
        np.testing.assert_allclose(x,y,rtol=2e-11,atol=1e-10)

def test_18_negative_or_infinite_diagonal_weight_is_never_silent():
    X=np.eye(3);w=np.array([1.,-1.,1.]);y=np.ones(3)
    with pytest.raises(ValueError):
        phy().weighted_radial_stats(X,w,y)
    with pytest.raises(ValueError):
        phy().weighted_radial_stats(X,np.array([1.,np.inf,1.]),y)

def test_19_20_immutable_historical_evidence_anchors():
    x=phy().historical_common_anchors()
    assert x["E0"]["state"]=="completed_scoped"
    assert x["E1"]["state"]=="completed_scoped"
    assert x["R78_science_nodes_42_sha"]=="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
    assert x["R78_next_id"]=="SQ-CF4"
    assert x["physical_claim_upgrade"] is False

def test_11_external_native_archive_resource_budget_precedes_npz_materialization(tmp_path):
    payload=tmp_path/"intake.npz"
    np.savez(payload,ell=np.array([2],dtype=int),m=np.array([0],dtype=int),
             E=np.zeros(1),B=np.zeros(1))
    h=hashlib.sha256(payload.read_bytes()).hexdigest()
    manifest=tmp_path/"manifest.json"
    manifest.write_text(json.dumps({
      "schema":"htt.external_bianchi_polarized/1",
      "source_kind":"external_native_result","solver_commit":"unqualified_fixture",
      "model_family":"Bianchi_I","observer_frame":"normal",
      "units":"dimensionless_photon_TEB","data_file":payload.name,
      "data_sha256":h}))
    with pytest.raises(ValueError,match="uncompressed"):
        phy().inspect_external_native(manifest,max_uncompressed_bytes=64)


def test_11_external_native_manifest_rejects_escape_paths(tmp_path):
    source=tmp_path/"source.npz"
    np.savez(source,ell=np.array([2]),m=np.array([0]),E=np.zeros(1),B=np.zeros(1))
    manifest=tmp_path/"manifest.json"
    h=hashlib.sha256(source.read_bytes()).hexdigest()
    manifest.write_text(json.dumps({"schema":"htt.external_bianchi_polarized/1",
       "source_kind":"external_native_result","solver_commit":"unqualified",
       "model_family":"Bianchi_V","observer_frame":"normal",
       "units":"dimensionless_photon_TEB","data_file":"../source.npz",
       "data_sha256":h}))
    with pytest.raises(ValueError,match="relative NPZ"):
        phy().inspect_external_native(manifest)


def test_12_native_source_mutation_never_reuses_valid_certificate(tmp_path,monkeypatch):
    monkeypatch.setenv("HTT_ANALYSIS_BACKEND","auto")
    p=phy()
    rng=np.random.default_rng(812)
    n=rng.normal(size=(5000,3));n/=np.linalg.norm(n,axis=1)[:,None]
    arr=sample_axes(24)  # 120,000 source-axis pairs > auto-native threshold
    p.multi_axis_hemisphere(n,arr)
    assert p.last_phy_receipt()["used"]=="fortran_batch"
    mutated=tmp_path/"multi_axis_mask_mutated.f90"
    mutated.write_bytes(p._SOURCE["mask"].read_bytes()+b"\n! deliberately untrusted source change\n")
    monkeypatch.setitem(p._SOURCE,"mask",mutated)
    x=p.multi_axis_hemisphere(n,arr)
    assert x["counts"].sum()==len(n)*len(arr)
    receipt=p.last_phy_receipt()
    assert receipt["used"]=="numpy_reference"
    assert "uncertified_mask_source_changed" in receipt["fallback_reason"]


def test_12_native_multiworker_bitwise_stability_on_source_finite():
    import os
    so=os.environ.get("HTT_R81_MASK_SO")
    if not so:pytest.skip("optional Fortran shared library not provided")
    p=phy()
    n=np.random.default_rng(221).normal(size=(5019,3))
    n/=np.linalg.norm(n,axis=1)[:,None]
    arr=sample_axes(48)
    w=np.random.default_rng(42).uniform(.1,1.1,len(n))
    a=p.multi_axis_hemisphere(n,arr,weights=w,native_lib=so,threads=1)
    b=p.multi_axis_hemisphere(n,arr,weights=w,native_lib=so,threads=8)
    for k in ("weights","means","second"):
        np.testing.assert_array_equal(a[k],b[k])
    np.testing.assert_array_equal(a["counts"],b["counts"])
