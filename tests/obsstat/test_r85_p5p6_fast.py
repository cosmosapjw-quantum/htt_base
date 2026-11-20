"""R85 exact original K02/ K03 and B02 external source-code preflight.

Scientific source gates stay unchanged; no polarized Einstein-Boltzmann solver.
"""
import json,sys,hashlib
from pathlib import Path
import numpy as np
import pytest
ROOT=Path("docs/research_program/observational_publication_20261015")
CF4=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
K03=Path("/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz")
K02_CODE=ROOT/"NEXT_20261016/K02"

def api():
    from htt.obsstat import p5p6_fast as f
    return f

@pytest.fixture(scope="module")
def original():
    sys.path.insert(0,str(K02_CODE.resolve()))
    import k02_source_identification as ref
    actual=ref.compute(CF4)
    prepared=api().prepare_cf4_method_source(CF4)
    return ref,actual,prepared

def test_K02_original_35970_method_gauge_and_correct_12D_source(original):
    ref,old,source=original
    assert source["N"]==35970 and source["X"].shape==(35970,12)
    np.testing.assert_allclose(source["X"][:,:4].sum(axis=1),
                               source["distance_Mpc"],rtol=0,atol=2e-11)
    assert source["weights"].shape==(35970,4)
    assert source["method_names"]==["FP","OTHER","SN","TF"]
    assert np.linalg.matrix_rank(source["X"][:10000])==12

def test_K02_new_NumPy_4x8_and_C32_exact_original_4_QR(original):
    _,old,source=original
    calc=api().k02_method_profiled(source,native_lib=None)
    assert calc["shape8"].shape==(4,8) and calc["joint_cov32"].shape==(32,32)
    np.testing.assert_allclose(calc["shape8"],old["identified_working_shape8_kmsMpc"],
                               rtol=2e-10,atol=1e-9)
    np.testing.assert_allclose(calc["joint_cov32"],old["joint_shape_cov32"],
                               rtol=2e-10,atol=1e-9)
    assert min(np.linalg.eigvalsh(calc["joint_cov32"]))>0
    assert np.linalg.norm(calc["joint_cov32"][:8,8:16])>0
    assert calc["physical_shear"] is None
    assert calc["physical_Pi"] is None

def test_K02_optional_native_1_4_8_12_worker_parity(original):
    import os
    so=os.environ.get("HTT_R85_K02_SO")
    if not so:pytest.skip("R85 K02 optional native not built")
    _,old,source=original
    ref=api().k02_method_profiled(source,native_lib=None)
    covs=[]
    for threads in (1,4,8,12):
        got=api().k02_method_profiled(source,native_lib=so,threads=threads)
        np.testing.assert_allclose(got["shape8"],ref["shape8"],rtol=2e-10,atol=1e-9)
        np.testing.assert_allclose(got["joint_cov32"],ref["joint_cov32"],rtol=2e-10,atol=1e-9)
        covs.append(got["joint_cov32"])
    np.testing.assert_array_equal(covs[0],covs[-1])

def test_K02_invalid_rank_and_noise_is_typed_failure(original):
    _,_,src=original
    cloned={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in src.items()}
    cloned["X"][:,:4]=0
    with pytest.raises(ValueError,match="SPD|rank|condition"):
        api().k02_method_profiled(cloned,native_lib=None)
    cloned={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in src.items()}
    cloned["sigma_kms"][0]=0
    with pytest.raises(ValueError):
        api().k02_method_profiled(cloned,native_lib=None)

def test_K03_real_external_6x102_cross_moment_source_verified():
    result=api().inspect_k03_cross_moments(K03)
    assert result["source_n"]==755850
    assert result["A_min_eigen"]>0
    assert result["rank_whitened_K"]==6
    assert result["actual_normal_vorticity"] is None
    assert result["physical_congruence_identified"] is False

def test_K03_external_changed_sha_rejected_before_claim(tmp_path):
    with pytest.raises(ValueError,match="sha256|SHA"):
        api().inspect_k03_cross_moments(K03,expected_sha="0"*64)

def test_K01_radial_omega_blindness_and_optical_sign():
    n=np.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
    sig=np.diag([2.,-1.,-1.])
    w=np.array([.1,.2,.3])
    acceleration=np.array([3.,0.,0.])
    obj=api().observer_radial_kinematics(n,theta=12.,sigma=sig,
                                         acceleration_over_c=acceleration,omega=w)
    np.testing.assert_allclose(obj["local_H_values"],[3.,3.,3.],atol=1e-14)
    assert obj["radial_omega_response_maxabs"]<1e-15
    assert obj["observed_physical_omega"] is None
    assert obj["true_optical_transfer_calibrated"] is False

def test_B02_missing_external_allm_polarized_stays_blocked(tmp_path):
    missing=tmp_path/"absent.json"
    with pytest.raises(FileNotFoundError):
        api().inspect_external_Bianchi_atlas(missing)

def test_B02_unqualified_fixture_not_physical(tmp_path):
    payload=tmp_path/"theory.npz"
    ell=np.repeat([2,3],[5,7]);m=np.concatenate([np.arange(-2,3),np.arange(-3,4)])
    np.savez(payload,ell=ell,m=m,T=np.ones(len(ell),complex),
             E=np.zeros(len(ell),complex),B=np.zeros(len(ell),complex))
    h=hashlib.sha256(payload.read_bytes()).hexdigest()
    mf=tmp_path/"theory.json"
    mf.write_text(json.dumps({"schema":"htt.bianchi_external_polarized_allm/1",
      "source_kind":"external_result","data_file":payload.name,"data_sha256":h,
      "solver_commit":"mock_source_NOT_VERIFIED",
      "family":"VII_h","mode":"scalar","ell_min":2,"ell_max":3,
      "frame":"normal_tetrad","units":"microkelvin",
      "spin_convention":"IAU","history":"mock_input_NOT_PHYSICAL",
      "primordial_mode_normalization":"mock",
      "initial_conditions":"mock_IC",
      "beam":"identity_for_unit_test"}))
    out=api().inspect_external_Bianchi_atlas(mf)
    assert out["structure_verified"]
    assert out["physical_transfer_qualified"] is False
    mf.write_text(mf.read_text().replace(h,"0"*64))
    with pytest.raises(ValueError,match="SHA|sha256"):
        api().inspect_external_Bianchi_atlas(mf)

def test_B03_B04_response_and_equivalence_are_conditional_not_detection():
    M=np.array([[1.,0.,0.],[0.,2.,0.],[0.,0.,.5]])
    T=np.eye(3)
    out=api().conditional_template_projection(M,T,source_qualified=False)
    np.testing.assert_allclose(out["working_observables"],M)
    assert out["physical_planck_match"] is False
    A=np.column_stack((np.array([1.,0.,0.]),np.array([0.,1.,0.])))
    B=np.column_stack((np.array([1.,0.,0.]),np.array([0.,0.,1.])))
    confusion=api().conditional_template_subspace_overlap(A,B,np.eye(3))
    np.testing.assert_allclose(confusion["singular_cosines"],[1,0],atol=1e-14)
    assert confusion["physical_family_evidence"] is None

def test_K04_K05_no_fake_common_congruence():
    J=np.eye(6)[:,:3]
    C=np.eye(6)
    r=api().conditional_kinematic_identification(J,C,source_qualified=False)
    assert r["rank"]==3 and r["physical_shear"] is None
    assert api().joint_same_congruence_gate(
        {"CF4":None,"Gaia":"source_only","CMB":None})["scientific_admission"] is False

def test_original_B01_and_R78_statuses_unchanged():
    x=api().historical_BK_statuses()
    assert x["science_nodes"]["B02"]=="pending"
    assert x["science_nodes"]["K01"]=="completed_scoped"
    assert x["science_nodes"]["K02"]=="completed_scoped"
    assert x["science_nodes"]["K03"]=="pending"
    assert x["original_42_science_SHA"]=="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
    assert x["next_actual_science_ID"]=="SQ-CF4"

def test_original_K02_35970_default_auto_selects_source_certified_Fortran(original,monkeypatch):
    monkeypatch.delenv("HTT_ANALYSIS_BACKEND",raising=False)
    _,old,src=original
    res=api().k02_method_profiled(src)
    receipt=api().last_p5p6_receipt()
    assert receipt["used"]=="fortran_source_info_cross"
    assert receipt["source_certified"] is True and receipt["threads"]==12
    np.testing.assert_allclose(res["shape8"],old["identified_working_shape8_kmsMpc"],rtol=2e-10,atol=1e-9)
    np.testing.assert_allclose(res["joint_cov32"],old["joint_shape_cov32"],rtol=2e-10,atol=1e-9)
