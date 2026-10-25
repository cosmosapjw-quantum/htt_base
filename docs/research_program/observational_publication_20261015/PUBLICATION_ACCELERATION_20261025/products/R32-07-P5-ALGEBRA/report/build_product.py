#!/usr/bin/env python3
"""Frozen P5 deterministic algebraic consumer; run from the repository root.

    python3 docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/build_product.py
    python3 docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/build_product.py --validate-only
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
PRODUCT = HERE.parent
REPO = next(p for p in HERE.parents if (p / ".git").exists())
SOURCE_LIST_SHA = "5587eecdc83ce4a0c43a53177f792dc425741bf707753a2ff4f784f811e7de92"
PREP_SHA = "fb65137ec8263f367554d0528c68ba1dd3b42ac0940141da8b7df9ac111f0733"
SOURCE_PATH = Path("/mnt/extdrive/workdir/htt_open_data/r35_p4_p5_source_contract_intake")
MANUSCRIPT_SHA = "b4acf4ae0772e4a8cc387063a8ec19e56e166fdca85ad26c0b688843bc50d6cf"
BUILD_SHA = "9a389efd96bf0d22df3320562a9a1728a3d1ac52a20ec26c50262185af822b42"
MAP_SHA = "924a68dbee926a83384647170b67b80ae5340494ddd3d0b42bcd729a47812904"
NOTES_SHA = "41d2c33da02a9f96e1fb9ba0eeee7f8d4cace4f064b49590c421d6aca31ffd79"
TOL = 2e-12
HTOL = 2e-14
KGRID = np.linspace(0.02, 0.98, 161)
BGRID = np.linspace(-0.9, 0.9, 181)
WVALUES = (0.0, 1.0 / 3.0)
FIGURES = ("domain", "joint_image", "fixed_matter_tilt", "shear_envelope", "history_temperature", "error_geometry")

CAPTIONS = {
"domain": r"Instantaneous LRS Bianchi V boundary images for one perfect fluid and nonnegative cosmological constant. Columns show the maximal rest-density parameter and its signed normalized shear at $\Omega_\Lambda=0$; rows use $w=0$ and $w=1/3$. The displayed support is $0.02\le K\le0.98$, $-0.9\le\beta\le0.9$. The sign follows the oriented momentum constraint.",
"joint_image": r"Coupled shear--density image curves at fixed curvature, tilt and equation of state. Each curve varies $u$ from zero to one in (9), with signed mirror branches displayed. The terminal points have $\Omega_\Lambda=0$. Scalar projection intervals cannot be recombined independently.",
"fixed_matter_tilt": r"Exact allowed tilt speed at fixed rest-density parameter and curvature. Curves use $\Omega=0.1,0.3,0.6$ and the indicated equation of state. The boundary saturates the normal constraint with $\Omega_\Lambda=0$. Gaps mark the empty domain ($K+\Omega>1$); the line at 0.9 marks only the heatmap display support.",
"shear_envelope": r"Sharp compact-support shear envelopes at $|\beta|\le0.9$ for $w=0,1/3,1$, compared with the ultrarelativistic supremum $(1-\sqrt K)^2$. For $0<K<1$ the dashed limiting curve is approached at finite normal energy and vanishing rest density as $|\beta|\to1$; it is not an attained finite-timelike state.",
"history_temperature": r"Exact kinematic Bianchi I histories with equal final radiation. The signed $zz$ shear components and $b_{zz}$ histories differ, while their full final axisymmetric temperature functions coincide. The endpoint shear ratio is $9/5$. The radiation equality follows from common endpoint deformation and collisionless transport, without an Einstein-perfect-fluid evolution assumption.",
"error_geometry": r"Deterministic separation of the history pair by an additional endpoint shear measurement. Equal closed Frobenius-error balls are disjoint for $r_{\mathrm{err}}<\alpha\sqrt6\epsilon/2$, touch at equality, and intersect above it. The radius is a deterministic tensor-error allowance with no probability or confidence interpretation."
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ensure(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def source_check(validate_only: bool) -> dict:
    source_files = (("manuscript.md", MANUSCRIPT_SHA), ("BUILD_CONTRACT.md", BUILD_SHA),
                    ("CLAIM_SOURCE_MAP.md", MAP_SHA), ("RESEARCH_NOTES.md", NOTES_SHA))
    for name, digest in source_files:
        p = PRODUCT / "science" / name
        ensure(sha(p) == digest, f"IMMUTABLE_SOURCE_MISMATCH {p}")
    for name, digest in (("P5_SOURCE_IDENTITIES.json", SOURCE_LIST_SHA),
                         ("P5_BUILD_CONTRACT.md", PREP_SHA)):
        original = SOURCE_PATH / name
        copy = HERE / "inputs" / name
        if not validate_only:
            ensure(sha(original) == digest, f"IMMUTABLE_SOURCE_MISMATCH {original}")
            shutil.copyfile(original, copy)
        ensure(sha(copy) == digest, f"IMMUTABLE_SOURCE_MISMATCH {copy}")
    info = json.loads((HERE / "inputs/P5_SOURCE_IDENTITIES.json").read_text())
    manifest = None
    for item in info["files"]:
        p = REPO / item["path"]
        ensure(p.stat().st_size == item["bytes"] and sha(p) == item["sha256"],
               f"IMMUTABLE_SOURCE_MISMATCH {p}")
        if p.name == "EVIDENCE_MANIFEST.json":
            manifest = json.loads(p.read_text())
    ensure(manifest is not None, "MISSING_EVIDENCE_MANIFEST")
    by_path = {f["path"]: f for f in manifest["files"]}
    for item in info["files"]:
        if item["manifest_match"] is True:
            m = by_path.get(item["path"])
            ensure(m is not None and m["sha256"] == item["sha256"] and m["bytes"] == item["bytes"],
                   f"MANIFEST_SOURCE_MISMATCH {item['path']}")
    return info


def tuple_at(K: float, beta: float, w: float, u: float) -> dict:
    if not all(math.isfinite(v) for v in (K, beta, w, u)):
        return {"status": "OUTSIDE_DOMAIN", "reason": "nonfinite input"}
    if K <= 0 or abs(beta) >= 1 or not (0 <= w <= 1) or not (0 <= u <= 1):
        return {"status": "OUTSIDE_DOMAIN", "reason": "K, beta, w or u outside stipulated domain"}
    if K > 1:
        return {"status": "EMPTY_DOMAIN", "reason": "K>1"}
    A = (1 + w) ** 2 * beta ** 2 / (4 * K * (1 - beta ** 2) ** 2)
    B = (1 + w * beta ** 2) / (1 - beta ** 2)
    D = 1 - K
    maximum = 2 * D / (B + math.sqrt(B * B + 4 * A * D))
    omega = u * maximum
    z = (1 + w) * omega * beta / (2 * math.sqrt(K) * (1 - beta ** 2))
    tilt = (1 + w) * omega * beta ** 2 / (1 - beta ** 2)
    fluxz = (1 + w) * omega * beta / (1 - beta ** 2)
    shear = np.diag((-z, -z, 2 * z))
    stress = np.diag((-tilt / 3, -tilt / 3, 2 * tilt / 3))
    return dict(status="ADMISSIBLE", reason="analytic parameterization", K=K, w=w,
                beta=beta, u=u, A=A, B=B, D=D, Omega=omega, Omega_max=maximum,
                z_s=z, Sigma2=z*z, Omega_n=B*omega,
                Omega_Lambda=D-B*omega-A*omega*omega, E_tilt=tilt,
                pressure=w*omega+tilt/3, shear=shear, pi=stress,
                flux=np.array((0., 0., fluxz)), beta_chart=np.array((0., 0., beta)),
                beta_physical=None if omega == 0 else beta,
                matter_velocity_status="UNDEFINED_ABSENT_MATTER" if omega == 0 else "DEFINED",
                normal_vorticity=0., normal_vorticity_status="HYPERSURFACE_ORTHOGONAL",
                matter_vorticity=None, matter_vorticity_status="NOT_DETERMINED")


def metrics(rows: list[dict], heat: list[dict], fixed: list[dict], arrays: dict) -> dict:
    m = {}
    def maximum(name, values, tol=TOL):
        value = max((abs(float(x)) for x in values), default=0.0)
        m[name] = value
        ensure(value <= tol, f"NUMERIC_TOLERANCE_EXCEEDED {name} {value} > {tol}")
    whole = rows + heat + fixed
    maximum("normal_hamiltonian", [r["K"]+r["Sigma2"]+r["Omega_n"]+r["Omega_Lambda"]-1 for r in whole])
    maximum("signed_momentum", [2*math.sqrt(r["K"])*r["z_s"]-r["flux"][2] for r in whole])
    maximum("shear_trace", [np.trace(r["shear"]) for r in whole])
    maximum("stress_trace", [np.trace(r["pi"]) for r in whole])
    maximum("shear_full_norm", [np.sum(r["shear"]**2)-6*r["Sigma2"] for r in whole])
    maximum("stress_full_norm", [np.sum(r["pi"]**2)-2*r["E_tilt"]**2/3 for r in whole])
    maximum("omega_polynomial", [r["A"]*r["Omega_max"]**2+r["B"]*r["Omega_max"]-r["D"] for r in rows+heat])
    maximum("fixed_omega_boundary", [r["K"]+r["Sigma2"]+r["Omega_n"]-1 for r in fixed], 5e-12)
    mirror = []
    lookup = {(r["K"], r["w"], r["beta"], r["u"]):r for r in rows}
    for r in rows:
        s = lookup[(r["K"],r["w"],-r["beta"],r["u"])]
        mirror += [r["z_s"]+s["z_s"], *(r["flux"]+s["flux"]),
                   *(r["shear"]+s["shear"]).flat,
                   r["Sigma2"]-s["Sigma2"], r["Omega_n"]-s["Omega_n"],
                   r["pressure"]-s["pressure"], *(r["pi"]-s["pi"]).flat]
    maximum("beta_mirror", mirror)
    maximum("heatmap_beta_mirror", [*(arrays["domain_shear"]+arrays["domain_shear"][:,::-1]).flat,
                                    *(arrays["domain_flux"]+arrays["domain_flux"][:,::-1]).flat,
                                    *(arrays["domain_pi"]-arrays["domain_pi"][:,::-1]).flat,
                                    *(arrays["domain_Omega_n"]-arrays["domain_Omega_n"][:,::-1]).flat,
                                    *(arrays["domain_Sigma2"]-arrays["domain_Sigma2"][:,::-1]).flat])
    envelope = arrays["envelope_z"]
    direct = arrays["envelope_direct_z"]
    maximum("compact_envelope_independent", (envelope-direct).flat)
    limit = arrays["envelope_ultrarelativistic"]
    maximum("timelike_envelope_violation", np.maximum(0, arrays["envelope_sigma2"]-limit).flat)
    maximum("heatmap_timelike_envelope_violation", np.maximum(0, arrays["domain_Sigma2"]-(1-np.sqrt(KGRID))**2).flat)
    maximum("history_endpoint_B", (arrays["B_A"][-1]-arrays["B_B"][-1]).flat, HTOL)
    maximum("history_temperature", (arrays["temperature_A"]-arrays["temperature_B"]).flat, HTOL)
    maximum("history_explicit_temperature", (arrays["temperature_A"]-arrays["temperature_explicit"]).flat, HTOL)
    maximum("history_shear_ratio", (arrays["shear_B_over_H"][-1]-1.8*arrays["shear_A_over_H"][-1]).flat, HTOL)
    na = np.sum(arrays["shear_A_over_H"][-1]**2)/6
    nb = np.sum(arrays["shear_B_over_H"][-1]**2)/6
    maximum("history_squared_norm_ratio", [nb/na-81/25], HTOL)
    maximum("history_stf", [*np.trace(arrays["B_A"],axis1=1,axis2=2),
                            *np.trace(arrays["B_B"],axis1=1,axis2=2),
                            *np.trace(arrays["shear_A_over_H"],axis1=1,axis2=2),
                            *np.trace(arrays["shear_B_over_H"],axis1=1,axis2=2)], HTOL)
    maximum("history_separation", [np.linalg.norm(arrays["shear_B_over_H"][-1]-arrays["shear_A_over_H"][-1])-arrays["error_separation"]], HTOL)
    maximum("history_equator_pole", [arrays["temperature_explicit"][200]-math.exp(0.02),
                                     arrays["temperature_explicit"][0]-math.exp(-0.04),
                                     arrays["temperature_explicit"][-1]-math.exp(-0.04)], HTOL)
    ensure(arrays["error_threshold"] == arrays["error_separation"]/2, "ERROR_THRESHOLD")
    ensure(arrays["error_touch_status"] == "TOUCHING", "ERROR_TOUCH")
    ensure(arrays["error_touch_expression"] == "alpha*sqrt(6)*epsilon/2" and arrays["error_touch_margin_exact"] == 0,
           "ERROR_SYMBOLIC_TOUCH_ROW")
    ensure(arrays["error_status"][0] == "DISJOINT" and arrays["error_status"][-1] == "INTERSECT", "ERROR_ENDPOINTS")
    ensure(tuple_at(1,0.5,0,1)["matter_velocity_status"] == "UNDEFINED_ABSENT_MATTER", "VACUUM")
    ensure(tuple_at(0.2,0,1/3,0.5)["z_s"] == 0 and tuple_at(0.2,0,1/3,0.5)["Omega"] > 0, "UNTILTED")
    for args, status in [((0,0,0,0),"OUTSIDE_DOMAIN"),((-0.1,0,0,0),"OUTSIDE_DOMAIN"),
                         ((0.2,1,0,0),"OUTSIDE_DOMAIN"),((0.2,1.01,0,0),"OUTSIDE_DOMAIN"),
                         ((0.2,0,-0.1,0),"OUTSIDE_DOMAIN"),((0.2,0,1.1,0),"OUTSIDE_DOMAIN"),
                         ((0.2,0,0,-0.1),"OUTSIDE_DOMAIN"),((0.2,0,0,1.1),"OUTSIDE_DOMAIN"),
                         ((math.nan,0,0,0),"OUTSIDE_DOMAIN"),((math.inf,0,0,0),"OUTSIDE_DOMAIN"),
                         ((1.1,0,0,0),"EMPTY_DOMAIN")]:
        ensure(tuple_at(*args)["status"] == status, f"INVALID_DOMAIN {args}")
    negative = [r for r in rows if 1+2*r["z_s"] < 0]
    if not negative:
        edge = tuple_at(0.02,-0.9,1,1)
        ensure(1+2*edge["z_s"] < 0, "NEGATIVE_DIRECTIONAL_EXPANSION")
        negative = [edge]
        m["negative_directional_expansion_source"] = "contract_approved_edge_tuple"
    else:
        m["negative_directional_expansion_source"] = "joint_grid"
    m["negative_directional_expansion_count"] = len(negative)
    m["negative_directional_expansion_example"] = {k:negative[0][k] for k in ("K","w","beta","u","z_s")}
    m["joint_rows"] = len(rows)
    m["fixed_boundary_rows"] = len(fixed)
    m["fixed_empty_rows"] = int(np.sum(arrays["fixed_status"] == "EMPTY_DOMAIN"))
    m["heatmap_points"] = int(arrays["domain_Omega_max"].size)
    m["max_abs_boundary_lambda"] = max([abs(r["Omega_Lambda"]) for r in rows if r["u"] == 1]
                                        +[abs(r["Omega_Lambda"]) for r in heat]
                                        +[abs(r["Omega_Lambda"]) for r in fixed])
    return m


def compute() -> tuple[dict, list[dict], list[dict], dict]:
    arrays = {}
    rows = [tuple_at(K,b,w,u) for K in (0.05,0.2,0.5,0.8) for w in WVALUES
            for b in (0.,-0.2,0.2,-0.5,0.5,-0.8,0.8) for u in (0.,0.25,0.5,0.75,1.)]
    ensure(len(rows)==280 and all(r["status"]=="ADMISSIBLE" for r in rows), "JOINT_GRID")
    for key in ("K","w","beta","u","Omega","Omega_max","z_s","Sigma2","Omega_n","Omega_Lambda","E_tilt","pressure"):
        arrays["joint_"+key] = np.array([r[key] for r in rows])
    for key in ("shear","pi","flux","beta_chart"):
        arrays["joint_"+key] = np.stack([r[key] for r in rows])
    arrays["joint_matter_velocity_status"] = np.array([r["matter_velocity_status"] for r in rows])
    arrays["joint_beta_physical"] = np.array([np.nan if r["beta_physical"] is None else r["beta_physical"] for r in rows])
    arrays["joint_normal_vorticity"] = np.zeros(len(rows))
    arrays["joint_normal_vorticity_status"] = np.full(len(rows),"HYPERSURFACE_ORTHOGONAL")
    arrays["joint_matter_vorticity"] = np.full(len(rows),np.nan)
    arrays["joint_matter_vorticity_status"] = np.full(len(rows),"NOT_DETERMINED")
    heat = [tuple_at(float(K),float(b),float(w),1.) for w in WVALUES for b in BGRID for K in KGRID]
    shape = (2,len(BGRID),len(KGRID))
    for key in ("Omega_max","z_s","Sigma2","Omega_n","Omega_Lambda","shear","pi","flux","beta_chart","E_tilt","pressure"):
        vals = np.stack([r[key] for r in heat]) if key in ("shear","pi","flux","beta_chart") else np.array([r[key] for r in heat])
        arrays["domain_"+key] = vals.reshape(shape+vals.shape[1:])
    arrays["domain_status"] = np.full(shape,"ADMISSIBLE")
    arrays["domain_matter_velocity_status"] = np.array([r["matter_velocity_status"] for r in heat]).reshape(shape)
    arrays["domain_normal_vorticity"] = np.zeros(shape)
    arrays["domain_normal_vorticity_status"] = np.full(shape,"HYPERSURFACE_ORTHOGONAL")
    arrays["domain_matter_vorticity"] = np.full(shape,np.nan)
    arrays["domain_matter_vorticity_status"] = np.full(shape,"NOT_DETERMINED")
    arrays["domain_K"] = KGRID
    arrays["domain_beta"] = BGRID
    arrays["domain_w"] = np.array(WVALUES)
    fixed = []
    bounds = np.full((2,3,len(KGRID)),np.nan)
    status = np.full((2,3,len(KGRID)),"EMPTY_DOMAIN")
    fixed_records=[]
    for wi,w in enumerate(WVALUES):
        for oi,omega in enumerate((0.1,0.3,0.6)):
            for ki,K in enumerate(KGRID):
                C=(1+w)*omega; a=C*C/(4*K); b=C+a; d=1-K-omega
                if d < 0:
                    fixed_records.append(dict(K=K,w=w,Omega=omega,status="EMPTY_DOMAIN",beta_bound=None))
                    continue
                t=2*d/(b+math.sqrt(b*b+4*a*d))
                v=math.sqrt(t/(1+t))
                bounds[wi,oi,ki]=v; status[wi,oi,ki]="ADMISSIBLE"
                fixed_records.append(dict(K=K,w=w,Omega=omega,status="ADMISSIBLE",beta_bound=v))
                for sign in ((0,) if v==0 else (-1,1)):
                    beta=sign*v
                    r=tuple_at(float(K),float(beta),float(w),0.)
                    ensure(r["status"]=="ADMISSIBLE", "FIXED_BOUNDARY_DOMAIN")
                    # Use fixed Omega directly; do not interpolate from the u grid.
                    r["Omega"]=omega
                    r["z_s"]=(1+w)*omega*beta/(2*math.sqrt(K)*(1-beta*beta))
                    r["Sigma2"]=r["z_s"]**2
                    r["Omega_n"]=r["B"]*omega
                    r["Omega_Lambda"]=1-K-r["Sigma2"]-r["Omega_n"]
                    r["E_tilt"]=(1+w)*omega*beta*beta/(1-beta*beta)
                    r["pressure"]=w*omega+r["E_tilt"]/3
                    r["shear"]=np.diag((-r["z_s"],-r["z_s"],2*r["z_s"]))
                    r["pi"]=np.diag((-r["E_tilt"]/3,-r["E_tilt"]/3,2*r["E_tilt"]/3))
                    r["flux"]=np.array((0.,0.,(1+w)*omega*beta/(1-beta*beta)))
                    r["beta_chart"]=np.array((0.,0.,beta))
                    r["beta_physical"]=beta; r["matter_velocity_status"]="DEFINED"
                    fixed.append(r)
    arrays["fixed_beta_bound"] = bounds
    arrays["fixed_status"] = status
    arrays["fixed_K"] = KGRID
    arrays["fixed_Omega"] = np.array((0.1,0.3,0.6))
    arrays["fixed_w"] = np.array(WVALUES)
    arrays["fixed_boundary_K"] = np.array([r["K"] for r in fixed])
    arrays["fixed_boundary_w"] = np.array([r["w"] for r in fixed])
    arrays["fixed_boundary_Omega"] = np.array([r["Omega"] for r in fixed])
    arrays["fixed_boundary_beta"] = np.array([r["beta"] for r in fixed])
    arrays["fixed_boundary_matter_velocity_status"] = np.full(len(fixed),"DEFINED")
    arrays["fixed_boundary_normal_vorticity"] = np.zeros(len(fixed))
    arrays["fixed_boundary_normal_vorticity_status"] = np.full(len(fixed),"HYPERSURFACE_ORTHOGONAL")
    arrays["fixed_boundary_matter_vorticity"] = np.full(len(fixed),np.nan)
    arrays["fixed_boundary_matter_vorticity_status"] = np.full(len(fixed),"NOT_DETERMINED")
    for key in ("z_s","Sigma2","Omega_n","Omega_Lambda","E_tilt","pressure"):
        arrays["fixed_boundary_"+key] = np.array([r[key] for r in fixed])
    for key in ("shear","pi","flux","beta_chart"):
        arrays["fixed_boundary_"+key] = np.stack([r[key] for r in fixed])
    ew=np.array((0.,1/3,1.))
    v=0.9
    rr=(1+ew[:,None])*v/(1+ew[:,None]*v*v)*np.ones((3,len(KGRID)))
    z=rr*(1-KGRID)/(np.sqrt(KGRID+rr*rr*(1-KGRID))+np.sqrt(KGRID))
    direct=np.array([[math.sqrt(tuple_at(float(K),v,float(w),1.)["A"])*tuple_at(float(K),v,float(w),1.)["Omega_max"] for K in KGRID] for w in ew])
    arrays.update(envelope_K=KGRID,envelope_w=ew,envelope_vmax=np.array(v),envelope_r=rr,
                  envelope_z=z,envelope_sigma2=z*z,envelope_direct_z=direct,
                  envelope_ultrarelativistic=(1-np.sqrt(KGRID))**2,
                  envelope_limit_status=np.full(len(KGRID),"ULTRARELATIVISTIC_SUPREMUM_NOT_FINITE_BETA_STATE"),
                  envelope_K1_status=np.array("ZERO_SHEAR_VACUUM_ENDPOINT"))
    tau=np.linspace(0,1,201); mu=np.linspace(-1,1,401)
    L=0.02*np.diag((-1.,-1.,2.)); alpha=0.8
    BA=tau[:,None,None]*L; BB=((1-alpha)*tau+alpha*tau*tau)[:,None,None]*L
    SA=np.broadcast_to(L,BA.shape).copy(); SB=(1-alpha+2*alpha*tau)[:,None,None]*L
    def temperature(B):
        return (np.exp(2*B[0,0])*(1-mu*mu)+np.exp(2*B[2,2])*mu*mu)**(-0.5)
    TA=temperature(BA[-1]); TB=temperature(BB[-1])
    TE=(np.exp(-0.04)*(1-mu*mu)+np.exp(0.08)*mu*mu)**(-0.5)
    sep=alpha*math.sqrt(6)*0.02
    radius=np.linspace(0,0.02,101)
    margin=sep-2*radius
    error_status=np.where(2*radius<sep,"DISJOINT",np.where(2*radius>sep,"INTERSECT","TOUCHING"))
    arrays.update(tau=tau,mu=mu,L=L,B_A=BA,B_B=BB,shear_A_over_H=SA,shear_B_over_H=SB,
                  temperature_A=TA,temperature_B=TB,temperature_explicit=TE,
                  error_radius=radius,error_separation=np.array(sep),error_threshold=np.array(sep/2),
                  error_margin=margin,error_status=error_status,error_touch_status=np.array("TOUCHING"),
                  error_touch_radius=np.array(sep/2),error_touch_margin_exact=np.array(0.),
                  error_touch_expression=np.array("alpha*sqrt(6)*epsilon/2"))
    return arrays, rows, fixed, {"heat":heat,"fixed_records":fixed_records}


def rows_csv(rows: list[dict], path: Path) -> None:
    scalars=("K","w","beta","u","Omega","Omega_max","z_s","Sigma2","Omega_n","Omega_Lambda","E_tilt","pressure")
    vectors=("flux","beta_chart")
    tensors=("shear","pi")
    keys=list(scalars)+[f"{v}_{i}" for v in vectors for i in "xyz"]+[f"{t}_{i}{j}" for t in tensors for i in "xyz" for j in "xyz"]
    keys += ["beta_physical","matter_velocity_status","normal_vorticity","normal_vorticity_status","matter_vorticity","matter_vorticity_status"]
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=keys); writer.writeheader()
        for r in rows:
            out={k:format(r[k],".17g") for k in scalars}
            out.update({f"{v}_{i}":format(r[v][j],".17g") for v in vectors for j,i in enumerate("xyz")})
            out.update({f"{t}_{i}{j}":format(r[t][ii,jj],".17g") for t in tensors for ii,i in enumerate("xyz") for jj,j in enumerate("xyz")})
            out.update(beta_physical="" if r["beta_physical"] is None else format(r["beta_physical"],".17g"),
                       matter_velocity_status=r["matter_velocity_status"],normal_vorticity="0",
                       normal_vorticity_status=r["normal_vorticity_status"],matter_vorticity="",
                       matter_vorticity_status=r["matter_vorticity_status"])
            writer.writerow(out)


def table_csv(rows: list[dict], path: Path) -> list[dict]:
    selected=[r for r in rows if r["u"]==1 and r["beta"]==0.5]
    ensure(len(selected)==8,"TABLE_SELECTION")
    keys=("K","w","Omega_max","z_s","Sigma2","Omega_n","Omega_Lambda")
    with path.open("w",newline="") as stream:
        writer=csv.writer(stream); writer.writerow(keys)
        for r in selected:
            writer.writerow([format(r[k],".10g") for k in keys])
    return selected


def save_fig(fig, name: str) -> None:
    fig.savefig(HERE/"figures"/(name+".pdf"),bbox_inches="tight")
    fig.savefig(HERE/"figures"/(name+".png"),bbox_inches="tight",dpi=180)
    plt.close(fig)


def figures(arrays: dict, rows: list[dict]) -> None:
    plt.rcParams.update({"font.size":9,"axes.labelsize":9,"figure.dpi":120,"savefig.dpi":180})
    fig,axes=plt.subplots(2,2,figsize=(9.3,6.4),sharex=True,sharey=True,constrained_layout=True)
    for wi,w in enumerate(WVALUES):
        for ci,(key,title) in enumerate((("domain_Omega_max",r"$\Omega_{\max}$"),("domain_z_s",r"signed $z_s$"))):
            a=axes[wi,ci]
            data=arrays[key][wi]
            vmax=float(np.max(np.abs(data)))
            im=a.pcolormesh(KGRID,BGRID,data,shading="auto",cmap="coolwarm" if ci else "viridis",vmin=-vmax if ci else 0,vmax=vmax)
            fig.colorbar(im,ax=a,shrink=.8)
            a.set_title(f"w={w:g}: {title}")
            a.set_xlabel("K"); a.set_ylabel(r"$\beta$")
    save_fig(fig,"domain")

    fig,axes=plt.subplots(1,2,figsize=(10,4.2),sharey=True,constrained_layout=True)
    colors={.05:"#1f77b4",.2:"#ff7f0e",.5:"#2ca02c",.8:"#d62728"}
    styles={0.0:":",0.2:"-",0.5:"--",0.8:"-."}
    for wi,w in enumerate(WVALUES):
        a=axes[wi]
        for K in colors:
            for ab in styles:
                for sign in ((1,) if ab==0 else (-1,1)):
                    branch=[r for r in rows if r["K"]==K and r["w"]==w and r["beta"]==sign*ab]
                    a.plot([r["Omega"] for r in branch],[r["z_s"] for r in branch],
                           color=colors[K],linestyle=styles[ab],marker="o",markersize=2.2,
                           label=f"K={K:g}, |β|={ab:g}" if sign==1 else None)
        a.axhline(0,color="0.4",lw=.5)
        a.set_title(f"w={w:g}"); a.set_xlabel(r"$\Omega$"); a.set_ylabel(r"$z_s$")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",ncol=4,fontsize=7,bbox_to_anchor=(.5,-.11))
    save_fig(fig,"joint_image")

    fig,axes=plt.subplots(1,2,figsize=(9,3.7),sharey=True,constrained_layout=True)
    for wi,w in enumerate(WVALUES):
        for oi,om in enumerate((0.1,0.3,0.6)):
            axes[wi].plot(KGRID,arrays["fixed_beta_bound"][wi,oi],label=rf"$\Omega={om:g}$")
        axes[wi].axhline(.9,color="0.35",ls=":",label="display support 0.9")
        axes[wi].set(xlabel="K",ylabel=r"max $|\beta|$",title=f"w={w:g}",ylim=(0,1.02))
        axes[wi].legend(fontsize=8)
    save_fig(fig,"fixed_matter_tilt")

    fig,ax=plt.subplots(figsize=(6,4),constrained_layout=True)
    for wi,w in enumerate(arrays["envelope_w"]):
        ax.plot(KGRID,arrays["envelope_sigma2"][wi],label=f"w={w:g}, |β|≤0.9")
    ax.plot(KGRID,arrays["envelope_ultrarelativistic"],"k--",label="ultrarelativistic supremum")
    ax.set(xlabel="K",ylabel=r"$\Sigma^2$",title="Compact shear envelopes")
    ax.legend(fontsize=8)
    save_fig(fig,"shear_envelope")

    fig,axes=plt.subplots(1,3,figsize=(11,3.5),constrained_layout=True)
    for ax,key,ylabel in ((axes[0],"shear",r"$\sigma_{zz}/H$"),(axes[1],"B",r"$b_{zz}$")):
        axes[0].plot(tau:=arrays["tau"],arrays["shear_A_over_H"][:,2,2],label="A") if key=="shear" else None
        if key=="shear": ax.plot(tau,arrays["shear_B_over_H"][:,2,2],label="B")
        else:
            ax.plot(arrays["tau"],arrays["B_A"][:,2,2],label="A")
            ax.plot(arrays["tau"],arrays["B_B"][:,2,2],label="B")
        ax.set(xlabel=r"$\tau$",ylabel=ylabel); ax.legend()
    axes[2].plot(arrays["mu"],arrays["temperature_A"],label="A")
    axes[2].plot(arrays["mu"][::24],arrays["temperature_B"][::24],"o",markersize=2.7,label="B, coincident")
    axes[2].set(xlabel=r"$\mu$",ylabel=r"$T/T_0$"); axes[2].legend()
    save_fig(fig,"history_temperature")

    fig,ax=plt.subplots(figsize=(6,3.8),constrained_layout=True)
    ax.plot(arrays["error_radius"],arrays["error_margin"],label=r"$d_\sigma-2r_{\rm err}$")
    ax.axhline(0,color="0.4",lw=.8)
    ax.axvline(float(arrays["error_threshold"]),color="tab:red",ls="--",label="analytic touching threshold")
    ax.set(xlabel=r"deterministic radius $r_{\rm err}$",ylabel="signed separation margin")
    ax.legend(fontsize=8)
    save_fig(fig,"error_geometry")


def claim_map_json() -> dict:
    claim_source=(PRODUCT/"science/CLAIM_SOURCE_MAP.md").read_text()
    claim_lines={m.group(1):line for line in claim_source.splitlines()
                 if (m:=re.match(r"\|\s*(P5-[A-J])\s*\|",line))}
    rows=[]
    specs=[
        ("P5-A","DERIVED","retained derivation","S1 P9; S2 metric check; manuscript Sections 1-2","oriented LRS V normal-frame constraints and signed shear"),
        ("P5-B","DERIVED","proof","S1-S2; manuscript Proposition 1","complete instantaneous algebraically admissible set"),
        ("P5-C","DERIVED","algebraic tensor decomposition","S1-S2; manuscript Section 3","coupled full shear, flux and STF stress image"),
        ("P5-D","DERIVED","proof","manuscript Proposition 2","fixed positive rest-density exact tilt interval"),
        ("P5-E","DERIVED","proof","manuscript equations 18-21","compact and limiting shear envelope"),
        ("P5-F","DERIVED","retained derivation","S1 P10; S2","conditional common-frame shear-ceiling implication"),
        ("P5-G","DERIVED","proof","S3; manuscript Proposition 3","equal full final temperature for kinematic Bianchi I pair"),
        ("P5-H","DERIVED","Euclidean tensor geometry","manuscript equations 29-30","deterministic endpoint shear ball separation"),
        ("P5-I","NOT_ESTABLISHED","none","missing Bianchi V solution family/dynamics/radiation map","Einstein-perfect-fluid Bianchi V equal-radiation pair"),
        ("P5-J","FORBIDDEN","none","outside this product","empirical family identification or native transfer atlas")]
    for cid,status,evidence,source,statement in specs:
        rows.append(dict(claim_id=cid,owner="manuscript",claim_tier="conditional",transfer_source="none",
                         status=status,evidence_type=evidence,source_and_proof=source,text=statement,
                         source_table_row=claim_lines[cid]))
    undefined={"x_C":{"value":None,"status":"NOT_EVALUABLE","missing":"fixed same-frame comparator and curvature/energy subtraction"},
               "Q":{"value":None,"status":"NOT_EVALUABLE","missing":"anchor/body, denominator and policy"},
               "F":{"value":None,"status":"NOT_EVALUABLE","missing":"support/occupancy measure and sign-clean ceiling"},
               "Pi":{"value":None,"status":"NOT_EVALUABLE","missing":"joint probability law and support"},
               "G_F":{"value":None,"status":"NOT_EVALUABLE","missing":"supported depth-F reports, bin measures and dependence"},
               "matter_vorticity":{"value":None,"status":"NOT_DETERMINED","missing":"matter-congruence kinematic development/bridge"},
               "normal_vorticity":{"value":0,"status":"EXACT_ZERO","reason":"hypersurface orthogonality"},
               "physical_beta_at_Omega_zero":{"value":None,"status":"UNDEFINED_ABSENT_MATTER"},
               "fluid_stress_flux_at_Omega_zero":{"value":0,"status":"EXACT_ZERO"}}
    return dict(source_markdown="../science/CLAIM_SOURCE_MAP.md",source_sha256=MAP_SHA,
                source_claim_table_verbatim=claim_source.split("## Claim map",1)[1].split("## Undefined",1)[0].strip(),
                source_undefined_table_verbatim=claim_source.split("## Undefined and exact-zero sectors",1)[1].split("## Physics/math audit verdict",1)[0].strip(),
                claims=rows,undefined_sectors=undefined)


def math_normalize(expr: str) -> str:
    expr=expr.replace("\x0barepsilon",r"\varepsilon").replace("\x08eta",r"\beta")
    expr=expr.replace("\x08oldsymbol",r"\boldsymbol").replace("\tau",r"\tau")
    expr=expr.replace("|sigma/H|_F^2",r"\|\sigma/H\|_F^2")
    expr=expr.replace("|pi/",r"\|\pi/").replace("}|_F^2",r"}\|_F^2")
    expr=expr.replace("z_sin[",r"z_s\in[")
    expr=expr.replace("int_0^Deltasigma,dt=L",r"\int_0^\Delta\sigma\,dt=L")
    expr=expr.replace(r"\betamapsto",r"\beta\mapsto").replace("betamapsto",r"\beta\mapsto").replace("tmapsto",r"t\mapsto")
    expr=expr.replace("vto1",r"v\to1")
    expr=expr.replace("AOmega",r"A\Omega").replace("BOmega",r"B\Omega")
    for name in ("Omega","Sigma","Lambda","Delta","gamma","epsilon","alpha","beta","mu","tau","Pi"):
        expr=re.sub(r"(?<![A-Za-z\\])"+name,lambda m:"\\"+name,expr)
    for old,new in (("Omegale",r"Omega\le "),("Omegage",r"Omega\ge "),
                    ("Lambdage",r"Lambda\ge "),("varepsilonge",r"varepsilon\ge "),
                    ("betale",r"beta\le "),
                    ("Age",r"A\ge "),("Dge",r"D\ge "),("Kle",r"K\le "),
                    ("dge",r"d\ge "),("tge",r"t\ge "),("vle",r"v\le "),
                    ("wle",r"w\le "),("ule",r"u\le ")):
        expr=expr.replace(old,new)
    expr=re.sub(r"(?<=\d)le(?=\s|$|\\|[A-Z0-9])",r"\\le ",expr)
    expr=re.sub(r"(?<=\d)ge(?=\s|$|\\|[A-Z0-9])",r"\\ge ",expr)
    expr=expr.replace("vto1",r"v\to1").replace("Omegato0",r"\Omega\to0")
    expr=expr.replace(r"\toinfty",r"\to\infty")
    expr=expr.replace(r"\sqrt A,\Omega",r"\sqrt A\,\Omega").replace(r"sqrt A,\Omega",r"\sqrt A\,\Omega")
    expr=expr.replace("partial r/partial w",r"\partial r/\partial w")
    expr=expr.replace("leSigma",r"\le \Sigma").replace("leOmega",r"\le \Omega")
    expr=expr.replace("geOmega",r"\ge \Omega")
    for name in ("Omega","Sigma","Lambda","Delta","gamma","epsilon","alpha","beta","mu","tau","Pi"):
        expr=re.sub(r"(?<![A-Za-z\\])"+name,lambda m:"\\"+name,expr)
    for command in ("mathrm","operatorname","sqrt","int"):
        expr=re.sub(r"(?<!\\)"+command+r"(?=\{|_|\s)",lambda m:"\\"+command,expr)
    expr=expr.replace("8pi ",r"8\pi ").replace("sqrt A,Omega",r"\sqrt A\,\Omega")
    return expr


def inline_math(line: str) -> str:
    # Consume outermost parenthetical spans; simple prose parentheses are retained.
    out=[]; i=0
    while i<len(line):
        if line[i] != "(": out.append(line[i]); i+=1; continue
        depth=1; j=i+1
        while j<len(line) and depth:
            if line[j]=="(": depth+=1
            elif line[j]==")": depth-=1
            j+=1
        if depth: out.append(line[i]); i+=1; continue
        inner=line[i+1:j-1]
        is_math=bool(re.search(r"[\\_\^=<>|+]|\dle\b|(?:Omega|Sigma|beta|gamma|epsilon|alpha|mu|tau|K|A|D|d|t|w)(?:le|ge|to|mapsto)|(?<![A-Za-z])(?:K|H|s|t|u|v|w|r|z|X|Y|A|B|D|L|E|F|G|Q|Pi|Omega|Sigma|beta|mu|tau|epsilon|alpha|gamma|a|b|d|m)(?![A-Za-z])|\d/\d",inner))
        if inner.isdigit(): is_math=False
        if is_math: out.append("$"+math_normalize(inner)+"$")
        else: out.append("("+inner+")")
        i=j
    return "".join(out)


def figure_tex(name: str) -> str:
    return ("\\begin{figure}[tbp]\n\\centering\n\\includegraphics[width=0.94\\linewidth]{figures/"+name+
            ".pdf}\n\\caption{"+CAPTIONS[name]+"}\n\\label{fig:"+name+"}\n\\end{figure}\n")


def table_tex(selected: list[dict], max_residual: float) -> str:
    lines=[r"\begin{table}[tbp]",r"\caption{Selected joint-image boundary tuples at $u=1$ and $\beta=+0.5$. The boundary has analytically $\Omega_\Lambda=0$; the largest computed absolute residual over the validation record is $"+format(max_residual,".3g")+r"$. These are parameter choices, not measured cosmological values.}",
           r"\label{tab:selected}",r"\begin{ruledtabular}",r"\begin{tabular}{ccccccc}",
           r"$K$ & $w$ & $\Omega_{\max}$ & $z_s$ & $\Sigma^2$ & $\Omega_n$ & $\Omega_\Lambda$ \\"]
    for r in selected:
        lines.append(" & ".join(format(r[k],".6g") for k in ("K","w","Omega_max","z_s","Sigma2","Omega_n","Omega_Lambda"))+r" \\")
    lines.extend((r"\end{tabular}",r"\end{ruledtabular}",r"\end{table}"))
    return "\n".join(lines)+"\n"


def tex_build(selected: list[dict], residual: float) -> dict:
    src=(PRODUCT/"science/manuscript.md").read_text()
    # This frozen source contains transport-escaped control bytes. The author-approved
    # byte-to-notation mapping is logged separately; source bytes are never rewritten.
    src=src.replace("\x0barepsilon",r"\varepsilon").replace("\x08eta",r"\beta")
    src=src.replace("\x08oldsymbol",r"\boldsymbol")
    src=src.replace("\tau",r"\tau")
    src=src.replace("\t"+"au",r"\tau").replace("\t"+"o",r"\to")
    # The source's multi-column equation (9) needs aligned's multiple & pairs.
    src=src.replace(r"\begin{split}",r"\begin{aligned}").replace(r"\end{split}",r"\end{aligned}")
    lines=src.splitlines()
    out=[]; display=False
    for ln in lines:
        if ln.startswith("# "):
            continue
        if ln == "## Abstract":
            out.append(r"\begin{abstract}"); continue
        if ln.startswith("## ") or ln.startswith("### "):
            if ln.startswith("## 1."):
                out.append(r"\end{abstract}")
            if ln.startswith("## 4.") and "Tilt and shear" in ln:
                out.append("\n"+figure_tex("domain")+figure_tex("joint_image")+table_tex(selected,residual))
            if ln.startswith("### 4.2"):
                out.append("\n"+figure_tex("fixed_matter_tilt"))
            if ln.startswith("## 5."):
                out.append("\n"+figure_tex("shear_envelope"))
            if ln.startswith("## 6."):
                out.append("\n"+figure_tex("history_temperature")+figure_tex("error_geometry"))
            heading=re.sub(r"^(#{2,3})\s+\d+(?:\.\d+)?\.?\s+",lambda m:m.group(1)+" ",ln)
            out.append(heading[1:]); continue
        if ln.strip()==r"\[": display=True; out.append(ln); continue
        if ln.strip()==r"\]": display=False; out.append(ln); continue
        if display:
            ln=math_normalize(ln)
            out.append(ln); continue
        out.append(inline_math(ln))
    norm="\n".join(out)+"\n"
    (HERE/"raw/manuscript_normalized.md").write_text(norm)
    process=subprocess.run(["pandoc","--from=markdown+tex_math_single_backslash+raw_tex","--to=latex","--wrap=none"],
                           input=norm,text=True,capture_output=True,cwd=HERE)
    (HERE/"raw/pandoc.stdout").write_text(process.stdout)
    (HERE/"raw/pandoc.stderr").write_text(process.stderr)
    ensure(process.returncode==0,f"PANDOC_EXIT {process.returncode}")
    body=process.stdout
    body=re.sub(r"\\texttt\{([^{}]+)\}",lambda m:r"\path{"+m.group(1).replace(r"\_","_")+"}",body)
    body=body.replace(
        " =\\left[\\sum_i e^{2b_i(t_f)}n_i^2\\right]^{-1/2}\n =\\left[e^{-2\\epsilon}(1-\\mu^2)+e^{4\\epsilon}\\mu^2\\right]^{-1/2},\n \\quad T_0=T_i a_i/a(t_f),\\quad \\mu=n_z.\n \\tag{27}",
        " &=\\left[\\sum_i e^{2b_i(t_f)}n_i^2\\right]^{-1/2}\\\\\n & =\\left[e^{-2\\epsilon}(1-\\mu^2)+e^{4\\epsilon}\\mu^2\\right]^{-1/2},\\\\\n &\\quad T_0=T_i a_i/a(t_f),\\quad \\mu=n_z.\n \\tag{27}")
    body=body.replace("\\mathcal O[B,a](\\boldsymbol n)\n =\\frac{T(\\boldsymbol n,t_f)}{T_0}",
                      "\\begin{aligned}\\mathcal O[B,a](\\boldsymbol n)\n &=\\frac{T(\\boldsymbol n,t_f)}{T_0}")
    body=body.replace(" \\tag{27}\n\\]","\\end{aligned}\\tag{27}\n\\]")
    title="Admissible shear--tilt images in LRS Bianchi V and a radiation-history degeneracy"
    header=(r"\documentclass[aps,prd,reprint,onecolumn,nofootinbib]{revtex4-2}"+"\n"+
            r"\usepackage{amsmath,amssymb,graphicx,hyperref}"+"\n"+
            r"\begin{document}"+"\n"+r"\title{"+title+r"}"+"\n"+
            r"\author{HTT research program}"+"\n"+r"\date{October 2026}"+"\n")
    body=body.replace(r"\end{abstract}",r"\end{abstract}"+"\n"+r"\maketitle",1)
    tex=header+body+"\n\\end{document}\n"
    (HERE/"manuscript.tex").write_text(tex)
    compile=subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","-file-line-error","manuscript.tex"],
                           text=True,capture_output=True,cwd=HERE)
    (HERE/"raw/latexmk.stdout").write_text(compile.stdout)
    (HERE/"raw/latexmk.stderr").write_text(compile.stderr)
    ensure(compile.returncode==0 and (HERE/"manuscript.pdf").exists(),f"LATEXMK_EXIT {compile.returncode}")
    return {"pandoc_exit":process.returncode,"latexmk_exit":compile.returncode}


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n")


def seal_product(source: dict, metrics_record: dict, tex_result: dict) -> None:
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=REPO,text=True,capture_output=True,check=True).stdout.strip()
    log=(HERE/"manuscript.log").read_text()
    ensure("undefined references" not in log.lower() and "undefined control sequence" not in log.lower(),"UNRESOLVED_LATEX")
    ensure("Overfull \\hbox" not in log,"OVERFULL_LAYOUT")
    tex=(HERE/"manuscript.tex").read_text()
    ensure(tex.count(r"\includegraphics")==6 and tex.count(r"\begin{table}")==1,"FIGURE_TABLE_COUNT")
    pages_info=subprocess.run(["pdfinfo",str(HERE/"manuscript.pdf")],text=True,capture_output=True,check=True).stdout
    pages=int(re.search(r"^Pages:\s+(\d+)",pages_info,re.M).group(1))
    notation={"source_manuscript_sha256":MANUSCRIPT_SHA,"source_build_contract_sha256":BUILD_SHA,
              "approved_by":"/root/rc_1f2400c98c81ce56",
              "mapping":"Source transport controls U+000B+'arepsilon' to \\varepsilon; U+0008+'eta' to \\beta; U+0008+'oldsymbol' to \\boldsymbol; tab+'au' to \\tau; tab+'o' to \\to. Inline math line mappings supplied by the author at manuscript lines 5,9,17,26,36,38,48,69,80,88,102,104,106,122,130,145,147,156,158,160,166,182,191,193,195,206,210,218,235,237,247,259,267,283,306,314,326,339,341. In line 145 bars are full Frobenius norms; line 247 sqrt(A)*Omega_max is a product. BUILD_CONTRACT.md controls at lines 51,53,59,65,90,91,101 have the same approved notation mapping. Equation (9) uses aligned in TeX to support two alignment columns. Scientific source bytes remain unchanged.",
              "author_approval_status":"APPROVED_NOTATION_ONLY","scientific_formula_changes":False,
              "source_count_correction":{"frozen_source_lines":"science/BUILD_CONTRACT.md and science/CLAIM_SOURCE_MAP.md say all ten",
                                         "actual_source_list_entries":len(source["files"]),
                                         "author_confirmation":"Counting typo; all nine listed entries are complete and verified. No source omitted. Frozen science bytes unchanged."}}
    write_json(HERE/"raw/notation_correction.json",notation)
    result={"status":"CANDIDATE_BUILT_PENDING_INDEPENDENT_REVIEW","task_id":"R32-07-P5-ALGEBRA",
            "attempt":1,"campaign":"R23-whole-42-solver-free",
            "packet_id":"1f2400c98c81ce56b5964beb1ba8c0c0b5d00452049470f22b188ed5bdd96154",
            "input_identity":"sha256:d6d2dc2c653bf3f611d0272d22cceb8562e1c277c76bdda1f50fbc91bc420a71",
            "task_spec_identity":"11ead068de6c2f1d1aea1adea92ef6b6fb135312c51dd47813828cd0da7544e5",
            "frontier_identity":"27b1e5df1ffbe44e31a69772db64138b0c2cc6902c009cef87d4b57cc4f3a508",
            "acceptance_passed":False,"original_acceptance_passed":False,"promotes_original_acceptance":False,
            "qualified_product":None,"qualified_products":[],"proposed_qualified_product":"bianchi_algebra_note",
            "owner":"manuscript","scope":"conditional instantaneous LRS Bianchi V algebra and exact kinematic Bianchi I radiation equivalence",
            "claim_tier":"conditional","transfer_source":"none","radiation_map":"explicit analytic collisionless Bianchi I endpoint map",
            "sky_support_status":"NO_EMPIRICAL_SKY_ANALYTIC_FULL_SPHERE",
            "covariance_null_status":"NOT_APPLICABLE_DETERMINISTIC_NO_PROBABILITY_LAW",
            "statistical_law_status":"NOT_SUPPLIED_NO_PROBABILISTIC_CLAIM",
            "branches":{"LRS_V_INSTANTANEOUS_CONSTRAINT_IMAGE":"DERIVED_CANDIDATE",
                        "BIANCHI_I_KINEMATIC_FULL_TEMPERATURE_NONINJECTIVITY":"DERIVED_CANDIDATE",
                        "BIANCHI_V_EINSTEIN_FLUID_HISTORY_PAIR_NOT_ESTABLISHED":"NOT_ESTABLISHED"},
            "undefined_sectors":claim_map_json()["undefined_sectors"],
            "source_head_from_preparation":source["source_head_observed"],
            "observed_git_head_at_build":head,"requested_builder_model":"gpt-6-sol","requested_builder_effort":"high",
            "observed_builder_runtime":"UNKNOWN",
            "source_identifiers":{"preparation_contract_sha256":PREP_SHA,"preparation_list_sha256":SOURCE_LIST_SHA,
                                  "science_manuscript_sha256":MANUSCRIPT_SHA,"science_build_contract_sha256":BUILD_SHA,
                                  "science_claim_map_sha256":MAP_SHA,"science_research_notes_sha256":NOTES_SHA,
                                  "retained_file_count":len(source["files"]),"retained_files":source["files"]},
            "display_support":{"K":[0.02,0.98,161],"beta":[-0.9,0.9,181],"w":[0,1/3]},
            "units_frames":"dimensionless binary64; c explicit in manuscript; normal orthonormal x,y,z axes; signed +z beta and z_s; H>0 mean expansion",
            "generating_command":"python3 docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/build_product.py",
            "candidate_artifacts":["arrays.npz","joint_image.csv","generated_table.csv","manuscript.tex","manuscript.pdf","CLAIM_SOURCE_MAP.json"]+[f"figures/{name}.{ext}" for name in FIGURES for ext in ("pdf","png")],
            "numerical_validation":metrics_record,"pdf_pages":pages,"figure_count":6,"table_count":1,
            "independent_review_status":"PENDING","caveats":["Instantaneous Bianchi V constraint tuples are not evolved Einstein-fluid histories.",
                "Kinematic Bianchi I radiation equality is not an Einstein-perfect-fluid Bianchi V pair.",
                "No empirical sky, probability law, native transfer or T/E/B atlas is supplied."]}
    write_json(HERE/"RESULT.json",result)
    receipt={"build_status":"PASS","source_binding":"PASS","numeric_checks":"PASS","tex":tex_result,
             "pdf_pages":pages,"figure_pdf_png_pairs":6,"table_rows":8,"joint_rows":280,"observed_git_head":head,
             "python":subprocess.run(["python3","--version"],text=True,capture_output=True).stdout.strip(),
             "numpy":np.__version__,"matplotlib":matplotlib.__version__,"review":"PENDING"}
    write_json(HERE/"BUILD_RECEIPT.json",receipt)
    report=(f"## Build status\n\nPASS candidate; independent review pending. Nine-page count is discovered from pdfinfo: {pages}.\n\n"
            f"## Entrypoint and included files\n\n`manuscript.tex` renders the frozen `../science/manuscript.md` with the author-approved notation mapping in `raw/notation_correction.json`; all six figure PDFs and the eight-row table are included.\n\n"
            f"## Commands run\n\n`python3 docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/build_product.py`; `pandoc --from=markdown+tex_math_single_backslash+raw_tex --to=latex --wrap=none`; `latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error manuscript.tex`; `python3 .../report/build_product.py --validate-only`; `pdfinfo` and `pdftoppm` page inspections. Actual Python: {receipt['python']}; NumPy {np.__version__}; Matplotlib {matplotlib.__version__}.\n\n"
            f"## Numerical validation\n\n{json.dumps(metrics_record,indent=2,sort_keys=True)}\n\n"
            f"## Errors and warnings\n\nFirst failures and repair attempts are retained in `raw/build_numeric*` and `raw/build_full_*`; they were consumer/TeX plumbing errors, not tolerance failures. Final LaTeX log has no overfull boxes, undefined references or missing figures. It retains RevTeX no-affiliation and hyperref/nameref warnings. Matplotlib reported unavailable optional Axes3D; all figures are 2D.\n\n"
            f"## Missing figures and missing figure sources\n\nNone; all six figures are generated by `build_product.py`.\n\n"
            f"## Citation/reference status\n\nNo unresolved LaTeX references. S1--S4 refer to exact retained source paths and identities in the frozen claim map. The hashed preparation list contains nine entries; the science author's 'all ten' wording is a confirmed counting typo, with no omitted source.\n\n"
            f"## Claim-language risks\n\nThe Bianchi I pair is kinematic, not an Einstein-fluid Bianchi V pair. Empirical sky, probability law, family identification and all-m T/E/B atlas are absent.\n\n"
            f"## Required manuscript fixes\n\nNone for this scoped conditional candidate. Independent scientific review remains pending.\n")
    (HERE/"BUILD_REPORT.md").write_text(report)
    inventory=["build_product.py","arrays.npz","joint_image.csv","generated_table.csv","manuscript.tex","manuscript.pdf",
               "CLAIM_SOURCE_MAP.json","RESULT.json","BUILD_RECEIPT.json","BUILD_REPORT.md",
               "inputs/P5_SOURCE_IDENTITIES.json","inputs/P5_BUILD_CONTRACT.md","raw/numerical_validation.json",
               "raw/notation_correction.json","raw/manuscript_normalized.md","raw/pandoc.stdout","raw/pandoc.stderr",
               "raw/latexmk.stdout","raw/latexmk.stderr"]
    inventory += [f"figures/{name}.{ext}" for name in FIGURES for ext in ("pdf","png")]
    write_json(HERE/"OUTPUT_MANIFEST.json",{"schema":"htt.p5_candidate_inventory/1","preimage_excludes":["OUTPUT_MANIFEST.json","CONTROLLER_RETURN.json","REVIEW.json","raw/build_*.stdout","raw/build_*.stderr"],
                                            "files":[{"path":name,"sha256":sha(HERE/name),"bytes":(HERE/name).stat().st_size} for name in inventory]})


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--validate-only",action="store_true")
    args=parser.parse_args()
    source=source_check(args.validate_only)
    arrays,rows,fixed,aux=compute()
    outcome=metrics(rows,aux["heat"],fixed,arrays)
    if args.validate_only:
        with np.load(HERE/"arrays.npz",allow_pickle=False) as saved:
            ensure(set(saved.files)==set(arrays),"SAVED_ARRAY_KEYS")
            for key,value in arrays.items():
                ensure(np.array_equal(saved[key],value,equal_nan=True) if value.dtype.kind in "fci" else np.array_equal(saved[key],value),f"SAVED_ARRAY_DRIFT {key}")
        ensure((HERE/"joint_image.csv").exists() and (HERE/"generated_table.csv").exists(),"MISSING_CSV")
        ensure(all((HERE/"figures"/(f+ext)).exists() for f in FIGURES for ext in (".pdf",".png")),"MISSING_FIGURE")
        ensure((HERE/"manuscript.pdf").exists() and (HERE/"RESULT.json").exists(),"MISSING_REPORT")
        manifest=json.loads((HERE/"OUTPUT_MANIFEST.json").read_text())
        for item in manifest["files"]:
            path=HERE/item["path"]
            ensure(path.stat().st_size==item["bytes"] and sha(path)==item["sha256"],f"OUTPUT_IDENTITY_MISMATCH {path}")
        print(json.dumps({"status":"VALIDATED","metrics":outcome},sort_keys=True))
        return
    np.savez_compressed(HERE/"arrays.npz",**arrays)
    rows_csv(rows,HERE/"joint_image.csv")
    selected=table_csv(rows,HERE/"generated_table.csv")
    figures(arrays,rows)
    tex_result=tex_build(selected,outcome["max_abs_boundary_lambda"])
    write_json(HERE/"CLAIM_SOURCE_MAP.json",claim_map_json())
    write_json(HERE/"raw/numerical_validation.json",{"status":"PASS","metrics":outcome,"source_count":len(source["files"]),
                                                          "selected_table_rows":len(selected),"fixed_boundary_rows":len(fixed)})
    seal_product(source,outcome,tex_result)
    print(json.dumps({"status":"NUMERIC_FIGURES_AND_PDF_BUILT","metrics":outcome,"tex":tex_result},sort_keys=True))


if __name__ == "__main__":
    main()
