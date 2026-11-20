"""R85 C7 independent actual K02 old QR vs new source native/NumPy and K03 Gaia.

No physical transfer or Bianchi full T/E/B inference qualified.
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from htt.obsstat import p5p6_fast as P

ROOT=Path("docs/research_program/observational_publication_20261015")
SELECTED=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
K02=ROOT/"NEXT_20261016/K02"
R75=ROOT/"R75_P5_LIE_TILT_FIVEVIEW_20261119/RESULTS.json"
B01=ROOT/"READY_20261016/B01_BIANCHI_ATLAS_REGISTRY.json"
B02_REPORT=ROOT/"CONTINUOUS_RESEARCH_20261023/execution/R23-ATLAS/REPORT.md"
EXTERNAL=Path("/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz")
OUT=ROOT/"R85_PRE_DAG_NODES51_60_20261120/C7_REAL_SOURCE.json"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def mx(x,y):return float(np.max(abs(np.asarray(x,float)-np.asarray(y,float))))

def main():
    if sha(SELECTED)!=P.SOURCE_SHA:raise ValueError("original 35970 CF4 source changed")
    sys.path.insert(0,str(K02.resolve()))
    import k02_source_identification as ref
    actual=ref.compute(SELECTED)
    source=P.prepare_cf4_method_source(SELECTED)
    assert source["N"]==35970
    Npy=P.k02_method_profiled(source,native_lib=None)
    so=P._certified_fortran()
    native=P.k02_method_profiled(source,native_lib=so,threads=12)
    oldcoef=np.array(actual["identified_working_shape8_kmsMpc"])
    oldcov=np.array(actual["joint_shape_cov32"])
    for val in (Npy,native):
        np.testing.assert_allclose(val["shape8"],oldcoef,rtol=2e-10,atol=1e-9)
        np.testing.assert_allclose(val["joint_cov32"],oldcov,rtol=2e-10,atol=1e-9)
    assert np.linalg.norm(native["joint_cov32"][:8,8:16])>0
    # Numerical identity rank(1 universal + 4 one-hot method + 8 shape)=12.
    X=source["X"]
    d=source["distance_Mpc"]
    assert np.linalg.matrix_rank(X)==12
    full=np.column_stack((d,X))
    assert np.max(abs(full[:,0]-full[:,1:5].sum(axis=1)))<2e-11
    assert np.linalg.matrix_rank(full)==12
    k03=P.inspect_k03_cross_moments(EXTERNAL)
    assert k03["source_n"]==755850 and k03["rank_whitened_K"]==6
    atlas=json.loads(B01.read_text())
    assert atlas["canonical_count"]==11
    claim=P.historical_BK_statuses()
    assert claim["next_actual_science_ID"]=="SQ-CF4"
    for key in ("B02","B03","B04","B05","K03","K04","K05","K06"):
        assert claim["science_nodes"][key]=="pending"
    for key in ("K01","K02"):
        assert claim["science_nodes"][key]=="completed_scoped"
    # Spatial antisymmetric omega exactly radial-blind for every sky direction.
    with np.load(SELECTED,allow_pickle=False) as original:
        n=original["n_J2000"][:100].copy() # actual source unit vectors
    assert np.max(abs(np.linalg.norm(n,axis=1)-1))<2e-10
    packet=P.observer_radial_kinematics(n,theta=6e-18,
        sigma=np.diag([1e-19,-.5e-19,-.5e-19]),
        acceleration_over_c=np.array([1e-19,0,0]),omega=np.array([1e-18,2e-18,-1e-18]))
    assert packet["radial_omega_response_maxabs"]<1e-30
    assert packet["observed_physical_omega"] is None
    r={
      "schema":"htt.r85.c7_original_CF4_K02_32D_and_Gaia_K03_source_replay/1",
      "source_sha256":{str(p):sha(p) for p in (SELECTED,EXTERNAL,B01,R75,B02_REPORT,K02/"k02_source_identification.py")},
      "original_selected_CF4_groups":source["N"],
      "source_four_windows":source["window_centers"],
      "source_diagnostic_modes_per_window":8,
      "working_source_12D_rank":12,"augmented_13D_method_monopole_gauge_rank":12,
      "numpy_4x8_original_QR_max_abs_error":mx(Npy["shape8"],oldcoef),
      "fortran_4x8_original_QR_max_abs_error":mx(native["shape8"],oldcoef),
      "numpy_C32_original_QR_max_abs_error":mx(Npy["joint_cov32"],oldcov),
      "fortran_C32_original_QR_max_abs_error":mx(native["joint_cov32"],oldcov),
      "fortran_C32_smallest_eigen":float(np.linalg.eigvalsh(native["joint_cov32"])[0]),
      "source_C32_cross_window_frobenius":float(np.linalg.norm(native["joint_cov32"][:8,8:16])),
      "original_K02_condition_F":native["condition_F"],
      "native_backend_receipt":P.last_p5p6_receipt(),
      "K03_actual_Gaia_source_moments":k03,
      "K01_omega_radial_maxabs":packet["radial_omega_response_maxabs"],
      "B01_registry_canonical_count":atlas["canonical_count"],
      "B02_full_physical_all_m_atlas":"MISSING_AUTHENTIC_NUMERIC_TRANSFER",
      "B02_historical_source_report_SHA256":sha(B02_REPORT),
      "R78_science_status":claim,
      "scientific_nonclaims":["K02 apparent 32-dimensional source rank is not normal sigma/acceleration",
        "K03 real moments are not observed independent total normal flux or vorticity",
        "B02 has no qualified full-T/E/B all-m primordial mode/history family atlas",
        "K04-K06 physical optical and cross-source congruence/null not qualified"]
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"CF4":source["N"],
      "K02_shape8_maxabs":r["fortran_4x8_original_QR_max_abs_error"],
      "K02_C32_maxabs":r["fortran_C32_original_QR_max_abs_error"],
      "K02_shared_cov_offblock":r["source_C32_cross_window_frobenius"],
      "K03_n":k03["source_n"],"K03_rank":k03["rank_whitened_K"],
      "B02":"AUTHENTIC_ALLM_TRANSFER_MISSING"}))
if __name__=="__main__":main()
