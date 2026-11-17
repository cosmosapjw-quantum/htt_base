#!/usr/bin/env python3
"""Read-only feasible axisymmetric witnesses for the retained CF4 STF experiment.

This is a confidence-set intersection calculation, not an axisymmetry p-value.
The optimizer supplies a feasible candidate, never a certified global minimum.
All five-dimensional marginal ellipsoids are conditional on the R58 fixed
Gaussian covariance law and its post hoc nuisance family.
"""
from __future__ import annotations
import argparse, hashlib, json, math, platform, subprocess
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.stats import chi2

RELATIVE_SOURCE = "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/NATIVE_REPLAY/OWNED_TENSOR_RESULT.json"
S2, S6 = 1 / math.sqrt(2), 1 / math.sqrt(6)
# Independent explicit implementation of the declared orthonormal STF chart.
BASIS = np.array([
    [[S2,0,0],[0,-S2,0],[0,0,0]],
    [[S6,0,0],[0,S6,0],[0,0,-2*S6]],
    [[0,S2,0],[S2,0,0],[0,0,0]],
    [[0,0,S2],[0,0,0],[S2,0,0]],
    [[0,0,0],[0,0,S2],[0,S2,0]],
], dtype=float)

def tensor(k):
    return np.einsum("a,aij->ij", k, BASIS)

def axial_unit(n):
    n = np.asarray(n, dtype=float)
    n = n / np.linalg.norm(n)
    return math.sqrt(1.5) * np.einsum("i,aij,j->a", n, BASIS, n)

def invariant_shape(k):
    e = np.linalg.eigvalsh(tensor(k))
    n2 = float(e @ e)
    return None if n2 == 0 else float(math.sqrt(6) * np.sum(e**3) / n2**1.5)

def fibonacci(n):
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    phi = math.pi * (1 + math.sqrt(5)) * i
    r = np.sqrt(1-z*z)
    return np.column_stack((r*np.cos(phi),r*np.sin(phi),z))

def run(repository_root):
    root = Path(repository_root)
    source = root / RELATIVE_SOURCE
    raw = source.read_bytes()
    data = json.loads(raw)
    grid = fibonacci(2048)
    units = np.array([axial_unit(n) for n in grid])
    c95 = float(chi2.ppf(0.95,5))
    ans = {
        "schema":"htt.axisym_feasible_witness/1",
        "source_file":RELATIVE_SOURCE,
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "source_read_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
        "source_claim_tier":data.get("claim_tier"),
        "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
        "source_estimate_parameter_names":data["parameter_names"],
        "basis":BASIS.tolist(),
        "basis_gram_max_error":float(np.max(abs(np.einsum("aij,bij->ab",BASIS,BASIS)-np.eye(5)))),
        "frame":"ICRS/J2000; sourceward directions; unit Frobenius STF5",
        "model":"K_candidate = a * sqrt(3/2) * (n n^T - I/3), signed a; n and -n equivalent",
        "confidence_rule":{
            "marginal_5d_radius_squared":c95,
            "joint_11d_radius_squared":float(chi2.ppf(0.95,11)),
            "intersection_witness":"candidate_delta_chi2 <= chi2_5_0.95",
            "law":"R58 retained fixed-Gaussian experiment, per nuisance variant",
            "interpretation":"Existence of an axisymmetric tensor in the marginal confidence ellipsoid; no rejection/non-rejection p-value is constructed.",
        },
        "algorithm":{"grid":"2048 deterministic Fibonacci axes","starts":"12 smallest analytically amplitude-profiled distances","local_method":"scipy.optimize.minimize BFGS","gtol":1e-9,"global_minimum_proven":False},
        "variants":{},
    }
    for name,record in data["variants"].items():
        mean=np.asarray(record["fit"]["estimate"],dtype=float)
        cov=np.asarray(record["fit"]["covariance"],dtype=float)
        k=mean[6:]
        S=cov[6:,6:]
        P=np.linalg.solve(S,np.eye(5))
        ku=units@P@k
        uu=np.einsum("ni,ij,nj->n",units,P,units)
        vals=k@P@k-ku*ku/uu
        def evaluate(t, full=False):
            n=np.array([np.cos(t[0])*np.cos(t[1]),np.sin(t[0])*np.cos(t[1]),np.sin(t[1])])
            u=axial_unit(n)
            a=float((u@P@k)/(u@P@u))
            candidate=a*u
            residual=k-candidate
            value=float(residual@P@residual)
            return (value,n,a,candidate) if full else value
        best=None
        candidate_objectives=[]
        for j in np.argsort(vals)[:12]:
            n=grid[j]
            initial=[np.arctan2(n[1],n[0]),np.arcsin(n[2])]
            fit=minimize(evaluate,initial,method="BFGS",options={"gtol":1e-9})
            value=evaluate(fit.x,True)
            candidate_objectives.append(value[0])
            if best is None or value[0]<best[0]: best=value
        distance,n,a,candidate=best
        matrix=tensor(candidate)
        eig=np.linalg.eigvalsh(matrix)
        # Full-state profile lift witnesses that the 5d marginal ellipsoid is
        # the exact projection of the 11d quadratic likelihood ellipsoid.
        full_candidate=mean+cov[:,6:]@np.linalg.solve(S,candidate-k)
        full_delta=full_candidate-mean
        full_distance=float(full_delta@np.linalg.solve(cov,full_delta))
        ans["variants"][name]={
            "observed_kappa5":k.tolist(),
            "observed_eigenvalues":np.linalg.eigvalsh(tensor(k)).tolist(),
            "observed_invariant_shape":invariant_shape(k),
            "candidate_axis_icrs_unit":n.tolist(),
            "candidate_axis_ra_dec_deg":[float(np.degrees(np.arctan2(n[1],n[0]))%360),float(np.degrees(np.arcsin(n[2])))],
            "candidate_signed_frobenius_amplitude":a,
            "candidate_kappa5":candidate.tolist(),
            "candidate_matrix":matrix.tolist(),
            "candidate_eigenvalues":eig.tolist(),
            "candidate_invariant_shape":invariant_shape(candidate),
            "candidate_delta_chi2":distance,
            "full_11d_profile_lift":full_candidate.tolist(),
            "full_11d_profile_lift_delta_chi2":full_distance,
            "profile_lift_agreement_abs":abs(full_distance-distance),
            "candidate_norm_agreement_abs":abs(float(np.linalg.norm(matrix))-abs(a)),
            "candidate_trace_abs":abs(float(np.trace(matrix))),
            "candidate_axis_norm_error":abs(float(n@n)-1),
            "intersects_marginal_95_ellipsoid":bool(distance<=c95),
            "margin_below_threshold":c95-distance,
            "local_candidate_objective_range":[float(min(candidate_objectives)),float(max(candidate_objectives))],
            "global_minimum_proven":False,
        }
    ans["all_seven_variants_have_verified_feasible_witness"]=all(v["intersects_marginal_95_ellipsoid"] for v in ans["variants"].values())
    ans["scope_limits"]=[
        "A feasible candidate proves intersection without a certified optimizer minimum.",
        "No calibrated triaxiality or axial-symmetry likelihood-ratio p-value is supplied.",
        "This tests generic axisymmetric apparent STF compatibility; it is not a reproduction of Kalbouneh et al. or a test of their common axis and evolution.",
        "Sampling, cosmic covariance and nuisance-model selection retain all R58 conditional/exploratory limitations.",
        "Free physical calibration still prevents interpreting the apparent STF as measured cosmological shear.",
    ]
    return ans

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--repository-root",default=".")
    p.add_argument("--output",default="-")
    args=p.parse_args()
    text=json.dumps(run(args.repository_root),indent=2,allow_nan=False)
    if args.output=="-": print(text)
    else: Path(args.output).write_text(text+"\n",encoding="utf-8")
