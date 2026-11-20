"""R83 lowell and CF4 source-coherent numerical preflight; no paper claims."""
import json,os,sys
from pathlib import Path

import numpy as np
import pytest
from scipy.linalg import lstsq
ROOT=Path("docs/research_program/observational_publication_20261015")
H03=ROOT/"H03_20261016/src"
SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")


def api():
    from htt.obsstat import p2p3_fast
    return p2p3_fast


@pytest.fixture(scope="module")
def h03():
    sys.path.insert(0,str(H03.resolve()))
    import h03_tomography as H
    source=H.source(SELECTED)
    d=H.proxy_distance(source.mu)
    sig=H.working_sigma(d,source.e_mu)
    X=H.velocity_design(d,source.n)
    y=H.C_KM_S*source.z
    w=np.column_stack([H.window(source.z,sig,c) for c in H.CENTERS])
    archived=json.loads((ROOT/"H03_20261016/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json").read_text())
    return H,X,y,w,sig,archived


def test_4window_GLS_exact_original_H03_theta_and_joint_C(h03):
    _,X,y,w,sig,archived=h03
    o=api().four_window_working_gls(X,y,w,sig,native_lib=None)
    assert o["theta"].shape==(4,9) and o["joint_cov"].shape==(36,36)
    theta=np.asarray([row["theta9"] for row in archived["monopole_dipole_STF2_windows"]])
    np.testing.assert_allclose(o["theta"],theta,rtol=2e-10,atol=1e-9)
    C=np.asarray(archived["joint_covariance_36x36"])
    np.testing.assert_allclose(o["joint_cov"],C,rtol=2e-9,atol=1e-9)
    assert np.linalg.eigvalsh(o["joint_cov"])[0]>0
    corr=o["joint_cov"][0,9]/np.sqrt(o["joint_cov"][0,0]*o["joint_cov"][9,9])
    assert abs(corr)>.6
    assert o["real_physical_H_z_n"] is None


def test_native_H03_optional_real_source_parity_and_thread_determinism(h03):
    so=os.environ.get("HTT_R83_H03_SO")
    if not so:pytest.skip("native source-verified C++ optional build not available")
    _,X,y,w,sig,_=h03
    baseline=api().four_window_working_gls(X,y,w,sig,native_lib=None)
    results=[]
    for nt in (1,4,8):
        out=api().four_window_working_gls(X,y,w,sig,native_lib=so,threads=nt)
        np.testing.assert_allclose(out["theta"],baseline["theta"],rtol=2e-10,atol=1e-9)
        np.testing.assert_allclose(out["joint_cov"],baseline["joint_cov"],rtol=2e-9,atol=1e-9)
        results.append(out["F"])
    np.testing.assert_array_equal(results[1],results[2])


def test_weighted_gaussian_rank_and_invalid_input():
    rng=np.random.default_rng(18)
    X=rng.normal(size=(280,9))
    true=np.array([70.,-.2,.3,.8,.01,.01,0.,.002,-.001])
    y=X@true
    w=rng.uniform(.001,1.,size=(len(X),4))
    s=np.ones(len(X))
    out=api().four_window_working_gls(X,y,w,s,native_lib=None)
    np.testing.assert_allclose(out["theta"],np.tile(true,(4,1)),atol=1e-10,rtol=0)
    with pytest.raises(ValueError):
        api().four_window_working_gls(X,y,np.zeros_like(w),s,native_lib=None)
    with pytest.raises(ValueError):
        api().four_window_working_gls(X,y,w,np.zeros_like(s),native_lib=None)
    with pytest.raises(ValueError):
        api().four_window_working_gls(X,y,w,np.ones((len(X),2)),native_lib=None)
    X[:,0]=0
    with pytest.raises(ValueError,match="rank|SPD|condition"):
        api().four_window_working_gls(X,y,w,s,native_lib=None)


def test_unqualified_planck_same_sky_and_eight_simulation_pair_IDs():
    result=api().historical_planck_science_status()
    assert result["L02_fields"]==25 and result["L02_same_sky_pairs"]==24
    assert result["one_physical_observed_sky"]
    assert result["L03_pilot_pair_ids"]==8 and result["L03_variants_per_pair"]==5
    assert result["L03_complete_source_matched_null_qualified"] is False
    assert result["L04_physical_p_value"] is None
    assert result["R78_science_next_ID"]=="SQ-CF4"
    assert result["R78_original_science_states_changed"] is False


def test_finite_MC_rank_includes_observation_and_tie_interval():
    out=api().working_rank_interval(3.,np.array([1.,3.,4.,3.]),
             simulation_ids=["0","1","2","3"],null_qualified=False)
    assert out["higher_than_observed"]==1 and out["greater_or_equal"]==3
    assert out["rank_interval"]==[2/5,4/5]
    assert out["rank_resolution"]==1/5
    assert out["physical_p_value"] is None
    with pytest.raises(ValueError):
        api().working_rank_interval(3.,np.array([1.,2.,3.,4.]),
             simulation_ids=["0","1","1","2"],null_qualified=False)
    with pytest.raises(ValueError):
        api().working_rank_interval(3.,np.array([1.,2.,3.,4.]),
             simulation_ids=["0","1","2","3"],null_qualified=True)


def test_simulation_id_family_max_is_not_variant_independent():
    observed=np.array([[1.,3.],[.1,.3],[2.,.01]])
    sim=np.array([[[1.,2.],[1.,1.],[2.,1.]],
                  [[0.,2.],[4.,1.],[2.,2.]],
                  [[2.,2.],[1.,.2],[0.,0.]]])
    out=api().family_rank_interval(observed,sim,
              simulation_ids=["A","B","C"],null_qualified=False)
    assert out["simulation_count"]==3 and out["processing_variants"]==3
    assert out["rank_resolution"]==1/4
    assert out["family_statistic"]=="max_over_selected_family_within_simulation_ID"
    assert out["physical_p_value"] is None
    with pytest.raises(ValueError):
        api().family_rank_interval(observed,sim,simulation_ids=["A","A","C"],
                                   null_qualified=False)


def test_L02_shape_absolute_does_not_erase_signed_original():
    result=api().historical_planck_science_status()
    assert result["L02_signed_vs_absolute_parity_verified"]
    assert result["L02_negative_signed_shapes_preserved"]
    # The B-channel chirality h is parity-even under O(3), unlike T/E,
    # so its sign is retained in the O3 summary, not replaced by |h|.
    original=json.loads((ROOT/"CONTINUATION_20261018/L02_EXECUTION_20261018/results/L02_ACTUAL_STATISTICS.json").read_text())
    negative_B=[z for z in original["field_rows"] if z["field"]=="B" and
                isinstance(z["SO3_signed"]["chirality"],float) and
                z["SO3_signed"]["chirality"]<0]
    assert len(negative_B)>=2
    for z in negative_B:
        assert z["SO3_signed"]["chirality"]==z["O3_summaries"]["chirality"]


def test_S06_L06_H02_claim_HOLD_and_H01_fixed_source():
    result=api().historical_planck_science_status()
    assert result["science_nodes"]["S06"]=="pending"
    assert result["science_nodes"]["L06"]=="pending"
    assert result["science_nodes"]["H02"]=="pending"
    assert result["science_nodes"]["H03"]=="completed_scoped"
    assert result["actual_correlated_PV_calibration_selection_C"] is None
    assert result["real_physical_H_z_n"] is None


def test_fortran_fused_source_h03_actual_4x9_and_36_crosscov(h03):
    lib=os.environ.get("HTT_R83_H03_FORTRAN_SO")
    if not lib:pytest.skip("optional fused source-signed Fortran library not supplied")
    _,X,y,w,sig,archived=h03
    reference=api().four_window_working_gls(X,y,w,sig,native_lib=None)
    old_t=np.asarray([v["theta9"] for v in archived["monopole_dipole_STF2_windows"]])
    old_c=np.asarray(archived["joint_covariance_36x36"])
    results=[]
    for nworker in (1,4,8):
        result=api().four_window_working_gls(
                 X,y,w,sig,native_lib=lib,threads=nworker)
        assert api().last_p2p3_receipt()["used"]=="fortran_source_info_cross"
        np.testing.assert_allclose(result["theta"],reference["theta"],atol=1e-9,rtol=2e-10)
        np.testing.assert_allclose(result["joint_cov"],reference["joint_cov"],atol=1e-9,rtol=2e-10)
        np.testing.assert_allclose(result["theta"],old_t,atol=1e-9,rtol=2e-10)
        np.testing.assert_allclose(result["joint_cov"],old_c,atol=1e-9,rtol=2e-10)
        results.append(result["joint_cov"])
    np.testing.assert_array_equal(results[0],results[2])


def test_native_fortran_certified_source_bound(tmp_path,monkeypatch):
    from htt.obsstat import p3_fortran_bridge as bridge
    original=bridge.SOURCE
    mutated=tmp_path/"p3_mutated.f90"
    mutated.write_bytes(original.read_bytes()+b"\n! intentionally uncertified source\n")
    monkeypatch.setattr(bridge,"SOURCE",mutated)
    with pytest.raises(RuntimeError,match="not certified"):
        bridge._certified_fortran()


def test_source_35970_default_auto_chooses_certified_fused_Fortran(h03,monkeypatch):
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    _,X,y,w,sig,original=h03
    got=api().four_window_working_gls(X,y,w,sig)
    receipt=api().last_p2p3_receipt()
    assert receipt["used"]=="fortran_source_info_cross"
    assert receipt["source_certified"] and receipt["workers"]==12
    np.testing.assert_allclose(got["theta"],
       [v["theta9"] for v in original["monopole_dipole_STF2_windows"]],
       rtol=2e-10,atol=1e-9)
    np.testing.assert_allclose(got["joint_cov"],original["joint_covariance_36x36"],
                              rtol=2e-9,atol=1e-9)


def test_uncertified_Fortran_native_source_changes_fallback_to_NumPy(h03,monkeypatch,tmp_path):
    from htt.obsstat import p3_fortran_bridge as bridge
    monkeypatch.setenv("HTT_ANALYSIS_BACKEND","auto")
    source=tmp_path/"intentionally_modified.f90"
    source.write_bytes(bridge.SOURCE.read_bytes()+b"\n! unverified diff\n")
    monkeypatch.setattr(bridge,"SOURCE",source)
    _,X,y,w,sig,_=h03
    out=api().four_window_working_gls(X,y,w,sig)
    assert out["joint_cov"].shape==(36,36)
    receipt=api().last_p2p3_receipt()
    assert receipt["used"]=="numpy_blas_source"
    assert not receipt["source_certified"]
    assert "hash not certified" in receipt["fallback_reason"]


def test_real_Planck_8_pair_pilot_internal_rank_is_only_code_arithmetic():
    p=ROOT/"CONTINUATION_20261018/L03_EXECUTION_20261018/results/L02_ON_EIGHT_PAIR_PILOT.json"
    source=json.loads(p.read_text())
    exact_variant="sum_noise_1.00"
    ranks=[]
    for uid in source["independent_pair_ids"]:
        match=[x for x in source["rows"] if
               x["simulation_id"]==uid and x["variant"]==exact_variant]
        assert len(match)==1
        ranks.append(abs(match[0]["fields"]["T"]["SO3_signed"]["quadrupole_shape"]))
    arr=np.asarray(ranks,float)
    assert len(arr)==8 and np.isfinite(arr).all()
    # First pilot pair is a numerical pseudo-observation, not observed CMB.
    score=api().working_rank_interval(arr[0],arr[1:],
               simulation_ids=source["independent_pair_ids"][1:],
               null_qualified=False)
    assert score["simulation_count"]==7
    assert score["rank_resolution"]==1/8
    assert score["physical_p_value"] is None
    assert score["source_null_qualified"] is False


def test_new_H03_fast_CLI_core_uses_original_source_and_retains_correlation(h03):
    from scripts.r83.run_h03_fast import run
    result=run()
    assert result["source_group_count"]==35970
    assert result["window_centers"]==[.025,.04,.06,.08]
    assert result["offdiag_9x9_cov_Frobenius"]>.1
    assert result["max_original_theta_absolute_error"]<1e-9
    assert result["max_original_covariance_absolute_error"]<1e-9
    assert result["actual_H_z_n"] is None and result["physical_Pi"] is None


def test_uncertified_cached_fortran_binary_integrity_falls_back_not_success(h03,monkeypatch,tmp_path):
    from htt.obsstat import p3_fortran_bridge as br
    fake=tmp_path/"fake.so"
    fake.write_bytes(b"not a shared library")
    import hashlib
    digest=hashlib.sha256(br.SOURCE.read_bytes()).hexdigest()
    (tmp_path/"manifest.json").write_text(json.dumps({
       "source_sha256":digest,"binary_sha256":"0"*64}))
    monkeypatch.setattr(br,"_compile_fortran",lambda source_sha:str(fake))
    monkeypatch.setenv("HTT_ANALYSIS_BACKEND","auto")
    _,X,y,w,sig,_=h03
    result=api().four_window_working_gls(X,y,w,sig)
    assert result["joint_cov"].shape==(36,36)
    receipt=api().last_p2p3_receipt()
    assert receipt["used"]=="numpy_blas_source"
    assert not receipt["source_certified"]
    assert "binary hash invalid" in receipt["fallback_reason"]
