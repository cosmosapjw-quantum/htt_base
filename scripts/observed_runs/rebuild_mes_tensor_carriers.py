#!/usr/bin/env python3
"""Map-free, non-promoting representation repair of pinned historical carriers.

Reads Git blobs, never FITS maps. Outputs corrected tensors and algebraic MES
functions; it does NOT calculate new anomaly ranks, physical shear, a boost,
a likelihood or an independently reviewed success terminal.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "htt/src"))
import numpy as np
from common.mes_krylov_completion import OrbitChartUnavailable, krylov16, pstf_mes_ceilings

SOURCE_HEAD = "ccba350d7b725b227c64436e32af96abfe786449"
SOURCE_TREE = "e91b8a4f57777c71c2bf1fc0f8c21395753481ba"
PAIRED = "docs/generated/planck_pr3_paired300_irrep_carrier/carrier.npz"
FROZEN = "docs/generated/pr315_planck_smica_feature_replay.npz"
CMBONLY = "docs/generated/planck_mes_smica_cmbonly_999_irrep/observable_irreps.npz"
EXPECTED_SHA = {
    PAIRED: "0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93",
    FROZEN: "b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b",
}
OBSERVATION_ID = "PLANCK-PR3-SMICA-OBSERVED"


def _git(repo: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if p.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.decode(errors='replace')[:600]}")
    return p.stdout


def _blob(repo: Path, path: str, ledger: dict) -> bytes:
    data = _git(repo, "show", f"{SOURCE_HEAD}:{path}")
    if len(data) > 20_000_000:
        raise ValueError("Unexpectedly large map-free artifact; no map or archive expansion is allowed")
    sha = hashlib.sha256(data).hexdigest()
    if path in EXPECTED_SHA and sha != EXPECTED_SHA[path]:
        raise ValueError(f"Immutable source mismatch: {path}")
    ledger[path] = {"source_commit": SOURCE_HEAD, "sha256": sha, "bytes": len(data),
                    "git_blob": _git(repo, "rev-parse", f"{SOURCE_HEAD}:{path}").decode().strip()}
    return data


def _array(a: object, shape: tuple[int, ...], label: str) -> np.ndarray:
    raw = np.asarray(a)
    if raw.shape != shape or raw.dtype.kind != "f" or raw.dtype.itemsize != 8:
        raise ValueError(f"{label}: expected explicit float64 {shape}, got {raw.dtype} {raw.shape}")
    if not np.all(np.isfinite(raw)):
        raise ValueError(f"{label}: nonfinite source values")
    return np.asarray(raw, dtype=np.float64)


def _ids(a: object, expected: list[str], label: str) -> np.ndarray:
    raw = np.asarray(a)
    if raw.dtype.kind != "U" or raw.shape != (len(expected),) or raw.tolist() != expected:
        raise ValueError(f"{label}: row identity/order mismatch")
    return raw


def _load_sources(repo: Path) -> tuple[dict, dict]:
    if _git(repo, "rev-parse", f"{SOURCE_HEAD}^{{tree}}").decode().strip() != SOURCE_TREE:
        raise ValueError("Historical input tree differs; do not substitute another WU branch")
    ledger = {}
    paired_ids = [OBSERVATION_ID] + [f"FFP10-SMICA-CMBNOISE-{i:05d}" for i in range(300)]
    cmb_ids = [OBSERVATION_ID] + [f"FFP10-SMICA-CMB-{i:05d}" for i in range(1000) if i != 970]
    with np.load(io.BytesIO(_blob(repo, PAIRED, ledger)), allow_pickle=False) as z:
        observation = _array(z["observed_real_alm"], (32,), "paired observation")
        nulls = _array(z["null_real_alm"], (300,32), "paired nulls")
        ids0 = _ids(z["row_ids"], paired_ids, "paired IDs")
        rows0 = np.vstack((observation, nulls))
        layout = [(str(l), str(m), k) for l in range(2,6) for m in range(l+1)
                  for k in (("real",) if m == 0 else ("real", "imag"))]
        if np.asarray(z["real_alm_layout"]).tolist() != [list(v) for v in layout]:
            raise ValueError("Historical real_alm_layout differs")
    with np.load(io.BytesIO(_blob(repo, FROZEN, ledger)), allow_pickle=False) as z:
        scalar0 = np.vstack((_array(z["observed_features"], (12,), "frozen observation"),
                              _array(z["null_features"], (300,12), "frozen nulls")))
    with np.load(io.BytesIO(_blob(repo, CMBONLY, ledger)), allow_pickle=False) as z:
        # Intentionally do not read old q_components/o_components/invariant/rank arrays.
        rows1 = _array(z["carrier_rows"], (1000,32), "CMB-only original carrier")
        scalar1 = _array(z["scalar_features"], (1000,12), "CMB-only scalar projection")
        ids1 = _ids(z["row_ids"], cmb_ids, "CMB-only IDs")
    if not np.array_equal(rows0[0], rows1[0]):
        raise ValueError("The two lanes do not contain the same frozen observation carrier")
    return {"paired300": (rows0, ids0, scalar0), "cmbonly999": (rows1, ids1, scalar1)}, ledger


def harmonic_stf_matrices() -> tuple[np.ndarray, np.ndarray]:
    """Independent spherical-integration oracle for the actual stored basis.

    Quadrature integrates the required polynomial angular products. It is not
    a second map estimator and never reopens the map that produced a carrier.
    """
    from scipy import special
    x, wx = np.polynomial.legendre.leggauss(12)
    phi = np.arange(32) * (2*math.pi/32)
    xx, pp = np.meshgrid(x, phi, indexing="ij")
    th = np.arccos(xx.ravel()); ph = pp.ravel()
    dirs = np.column_stack((np.sin(th)*np.cos(ph),np.sin(th)*np.sin(ph),np.cos(th)))
    weights = np.repeat(wx,32) * (2*math.pi/32)
    matrices=[]
    for ell in (2,3):
        columns=[]
        for m in range(ell+1):
            if hasattr(special,"sph_harm_y"):
                y=special.sph_harm_y(ell,m,th,ph)
            else:
                y=special.sph_harm(m,ell,ph,th)
            if m==0:columns.append(np.real(y))
            else:columns.extend((math.sqrt(2)*np.real(y),math.sqrt(2)*np.imag(y)))
        yreal=np.column_stack(columns)
        if ell==2:
            b=(15/(8*math.pi))*np.einsum("nk,ni,nj,n->kij",yreal,dirs,dirs,weights)
            tr=np.trace(b,axis1=1,axis2=2)
            b=b-tr[:,None,None]*np.eye(3)[None,:,:]/3
        else:
            b=(35/(8*math.pi))*np.einsum("nk,ni,nj,nl,n->kijl",yreal,dirs,dirs,dirs,weights)
            tr=np.einsum("kiij->kj",b)
            for i,j,k in itertools.product(range(3),repeat=3):
                b[:,i,j,k]-=((i==j)*tr[:,k]+(i==k)*tr[:,j]+(j==k)*tr[:,i])/5
        matrices.append(b)
    return matrices[0],matrices[1]


def project_carrier(rows: np.ndarray, matrices=None) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    rows=_array(rows,(len(rows),32),"carrier rows")
    qb,ob=matrices if matrices is not None else harmonic_stf_matrices()
    q=np.tensordot(rows[:,:5],qb,axes=(1,0))
    o=np.tensordot(rows[:,5:12],ob,axes=(1,0))
    powers=np.column_stack([np.sum(rows[:,s:e]**2,axis=1)/(2*l+1)
                            for l,s,e in [(2,0,5),(3,5,12),(4,12,21),(5,21,32)]])
    q2=np.einsum("nij,nij->n",q,q);o2=np.einsum("nijk,nijk->n",o,o)
    if not np.allclose(q2,75/(8*math.pi)*powers[:,0],rtol=2e-12,atol=1e-20):
        raise ValueError("Quadrupole radial identity failed")
    if not np.allclose(o2,245/(8*math.pi)*powers[:,1],rtol=2e-12,atol=1e-20):
        raise ValueError("Octupole radial identity failed")
    return q,o,powers


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")


def execute(repo: Path, output: Path, *, t0: float, epsilon1: float) -> dict:
    repo=repo.resolve(); output=output.resolve()
    allowed=[(repo/"docs/generated").resolve(),Path("/mnt/sn850x2t/htt_base_e2e/workdir/analysis/mes_tensor_research_integration").resolve()]
    if not any(output.is_relative_to(p) and output!=p for p in allowed):
        raise ValueError("Output must be a new child of an explicitly allowed generated/private-analysis root")
    if output.exists():raise FileExistsError("Refusing to overwrite existing evidence")
    if not math.isfinite(t0) or t0<=0 or not math.isfinite(epsilon1) or epsilon1<0:
        raise ValueError("Explicit T0 and residual PSTF dipole must be physical finite values")
    arms,source=_load_sources(repo)
    matrices=harmonic_stf_matrices()
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix=".mes-basis-recovery-",dir=output.parent))
    summary={"format":"MES_TENSOR_MAP_FREE_REPRESENTATION_REPAIR_V1",
             "state":"EXECUTED_PENDING_INDEPENDENT_REVIEW", "source_commit":SOURCE_HEAD,
             "source_tree":SOURCE_TREE,"t0_microK_CMB":t0,"residual_epsilon1_pstf":epsilon1,
             "raw_maps_reopened":False,"historical_ranks_reused":False,"new_ranks_generated":False,
             "physical_claim_promoted":False,"github_actions_used":False,"arms":{}}
    try:
        for name,(rows,ids,scalar) in arms.items():
            q,o,powers=project_carrier(rows,matrices)
            if not np.allclose(powers,scalar[:,:4],rtol=2e-12,atol=1e-14):
                raise ValueError(f"{name}: immutable scalar C_l closure failed")
            directory=tmp/name;directory.mkdir()
            mes=[pstf_mes_ceilings(c2=a,c3=b,t0=t0,epsilon1=epsilon1) for a,b in powers[:,:2]]
            np.savez_compressed(directory/"corrected_representation.npz",row_ids=ids,carrier_rows=rows,
                                q_components=q,o_components=o,cl=powers,
                                mes_ceilings=np.asarray([[r['U_sigma'],r['U_omega']] for r in mes]))
            unavailable=0
            with (directory/"krylov_chart_rows.jsonl").open("w",encoding="utf-8") as stream:
                for row_id,qr,orr in zip(ids,q,o):
                    try: entry={"row_id":str(row_id),"status":"AVAILABLE",**krylov16(qr,orr)}
                    except OrbitChartUnavailable as exc:
                        unavailable+=1;entry={"row_id":str(row_id),"status":"CHART_UNAVAILABLE_TENSORS_PRESERVED","reason":str(exc)}
                    stream.write(json.dumps(entry,sort_keys=True,allow_nan=False)+"\n")
            summary['arms'][name]={"rows":len(rows),"q_o_radial_closure":"MATCH",
              "scalar_closure":"MATCH_WITH_DECLARED_FLOAT_TOLERANCE","chart_unavailable_rows":unavailable,
              "statistical_use":"DESCRIPTIVE_NOISE_MISMATCH_NOT_A_CALIBRATED_PVALUE" if name=='cmbonly999' else "JOINT_NULL_FIDELITY_REQUIRED_NO_NEW_TEST_EXECUTED"}
        _json(tmp/'source_manifest.json',source)
        _json(tmp/'summary.json',summary)
        hashes={str(p.relative_to(tmp)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(tmp.rglob('*')) if p.is_file()}
        _json(tmp/'terminal.pending.json',{'state':'EXECUTED_PENDING_INDEPENDENT_REVIEW',
          'candidate_git_head':_git(repo,'rev-parse','HEAD').decode().strip(),
          'candidate_git_tree':_git(repo,'rev-parse','HEAD^{tree}').decode().strip(),
          'candidate_git_status':_git(repo,'status','--porcelain=v1').decode(),
          'artifact_sha256':hashes,'independent_review':'NOT_PERFORMED',
          'raw_maps_reopened':False,'next_action':'REVIEW_CORRECTED_REPRESENTATION_BEFORE_STATISTICAL_REANALYSIS'})
        os.replace(tmp,output)
    except BaseException:
        # Keep partial results for diagnosis. No user data is deleted or overwritten.
        if tmp.exists():_json(tmp/'FAILED_EXECUTION.json',{'state':'FAILED_OUTPUT_PRESERVED','output_intended':str(output)})
        raise
    return summary


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=ROOT)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--t0-uk',type=float,required=True)
    p.add_argument('--residual-epsilon1',type=float,required=True)
    p.add_argument('--execute',action='store_true')
    args=p.parse_args()
    if not args.execute:
        print(json.dumps({'state':'NOT_EXECUTED','source_commit':SOURCE_HEAD,'raw_map_access':False}));return
    print(json.dumps(execute(args.repo,args.output_dir,t0=args.t0_uk,epsilon1=args.residual_epsilon1),indent=2))


if __name__=='__main__':main()
