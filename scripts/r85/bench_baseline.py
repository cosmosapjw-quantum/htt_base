"""R85 C1 actual K02 CF4 selected-source 4-window method-profiled QR baseline.

No physical optical normal-frame map/claimed all-Bianchi polarized atlas.
"""
import hashlib,json,sys,time,platform,resource
from pathlib import Path
import numpy as np

ROOT=Path("docs/research_program/observational_publication_20261015")
SOURCE=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
K02=ROOT/"NEXT_20261016/K02"
ATLAS=ROOT/"READY_20261016/B01_BIANCHI_ATLAS_REGISTRY.json"
EXTERNAL=Path("/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz")
DAG=ROOT/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
OUTPUT=ROOT/"R85_PRE_DAG_NODES51_60_20261120/C1_BASELINE.json"
SRC_SHA="86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
K03_SHA="70fc2fee88803a7211c1c157ff87b4adb05b0807a00c03dc38d51f31b3842662"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1<<20),b""):h.update(c)
    return h.hexdigest()

def timed(call,reps=3):
    call()
    samples=[]
    x=None
    for _ in range(reps):
        t=time.perf_counter();x=call();samples.append(time.perf_counter()-t)
    return x,{"median_s":float(np.median(samples)), "samples_s":samples,"repeat":reps}

def main():
    if sha(SOURCE)!=SRC_SHA:raise ValueError("K02 exact original selected groups changed")
    sys.path.insert(0,str(K02.resolve()))
    import k02_source_identification as old
    columns=old.load(SOURCE)
    funcs=old.CENTERS
    assert len(columns["group_id"])==35970 and len(funcs)==4
    result,tperf=timed(lambda:old.compute(SOURCE),3)
    C=np.asarray(result['joint_shape_cov32'],float)
    assert C.shape==(32,32)
    assert abs(result['cov32_eig_min']-np.linalg.eigvalsh(C)[0])<1e-9
    assert np.linalg.eigvalsh(C)[0]>0
    assert np.isfinite(np.asarray(result["identified_working_shape8_kmsMpc"])).all()
    assert 0.0030<result['cov32_eig_min']<0.0035
    with np.load(EXTERNAL,allow_pickle=False) as z:
        assert {"A","K","qH","n","zmin","zmax"}==set(z.files)
        A,K,q=z["A"].copy(),z["K"].copy(),z["qH"].copy()
        n,zmin,zmax=int(z["n"]),float(z["zmin"]),float(z["zmax"])
    assert sha(EXTERNAL)==K03_SHA
    assert A.shape==(6,6) and K.shape==(6,102) and q.shape==(6,) and n==755850
    atlas=json.loads(ATLAS.read_text())
    assert atlas['canonical_count']==11
    dag=json.loads(DAG.read_text())
    assert dag['count_total_graph_nodes']==60 and dag['next_action_id']=='SQ-CF4'
    out={
       "schema":"htt.r85.c1_original_K02_CF4_K03_PM_and_B01_atlas_baseline/1",
       "source_sha256":{str(p):sha(p) for p in (SOURCE,EXTERNAL,ATLAS,DAG,K02/'k02_source_identification.py')},
       "original_pre_DAG_parent_head":"bcb1a26af18d6005a675caf1e87fde7563799855",
       "R78_next_actual_science":"SQ-CF4",
       "target_ids":{str(i):k for i,k in enumerate([f"B{x:02d}" for x in range(2,6)]+[f"K{x:02d}" for x in range(1,7)],51)},
       "original_CF4_group_count":35970,
       "original_method_gauge_rank":"13 original columns include 4 method monopoles + one exactly dependent full monopole; fixed 12D method profile identifies 8 apparent shape modes per window",
       "original_K02_QR_complete_4windows_32cov_times":tperf,
       "original_K02_shape8":[list(map(float,x)) for x in result["identified_working_shape8_kmsMpc"]],
       "original_K02_cov32_eigen_min":float(result["cov32_eig_min"]),
       "original_K02_cov32_eigen_max":float(result["cov32_eig_max"]),
       "K03_external_cross_moments":{"source_sha256":sha(EXTERNAL),"A_shape":list(A.shape),
         "K_shape":list(K.shape),"n_proper_motion_sources":n,"z_range":[zmin,zmax],
         "A_min_eig":float(np.linalg.eigvalsh(A)[0]),"rank_K":int(np.linalg.matrix_rank(K))},
       "B01_canonical_atlas_count":atlas['canonical_count'],
       "B02_external_all_m_polarization_payload":"NOT_QUALIFIED_SOURCE",
       "K03_real_Gaia_nonradial_condition":"working cross-moments available, K03 physical normal mapping NOT QUALIFIED",
       "system":{"python":platform.python_version(),"numpy":np.__version__,
          "maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
       "science_claim":"C1 original source conditional reproduction only; not same normal cosmological physics posterior"
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"rows":35970,"QR_median_s":tperf["median_s"],
        "cov32_min_eig":out["original_K02_cov32_eigen_min"],
        "Gaia_cross_n":n,"K_rank":out["K03_external_cross_moments"]["rank_K"]},ensure_ascii=False))
if __name__=="__main__":main()
