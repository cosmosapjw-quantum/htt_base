#!/usr/bin/env python3
"""Read-only R54 count-dipole covariance/calibration sensitivity.

Nominal Gaussian calculations condition on the saved covariance estimates.
They are deliberately separate from the original finite-mock Pi values.
"""
from __future__ import annotations
import argparse, hashlib, json, math, platform, subprocess
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import brentq, minimize
from scipy.stats import chi2

RELATIVE_SOURCE = "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L03_RESULT.json"

def direction(vector):
    vector=np.asarray(vector,dtype=float)
    size=float(np.linalg.norm(vector))
    if size==0:
        return {"unit_icrs":None,"ra_dec_deg":None,"reason":"zero vector has no direction"}
    n=vector/size
    return {"unit_icrs":n.tolist(),"ra_dec_deg":[float(np.degrees(np.arctan2(n[1],n[0]))%360),float(np.degrees(np.arcsin(np.clip(n[2],-1,1))))]}

def minimal_shift(e,C,cut):
    eigen,U=np.linalg.eigh(C)
    if np.min(eigen)<=0: raise ValueError("mock covariance must be positive definite")
    q0=float(e@np.linalg.solve(C,e))
    if q0<=cut:
        return {"vector_icrs":[0.,0.,0.],"norm_count_dipole":0.,"fraction_of_excess_norm":0.,
                "direction":direction(np.zeros(3)),"nominal_residual_quadratic":q0,
                "lagrange_multiplier_variance_units":0.,
                "constrained_crosscheck":{"required":False,"reason":"origin already belongs to the ellipsoid; objective norm has lower bound zero"},
                "kkt_stationarity_norm":0.}
    scale2=float(np.mean(eigen));h=eigen/scale2;y=U.T@e/math.sqrt(scale2)
    def f(mu): return float(np.sum(h*y*y/(h+mu)**2)-cut)
    upper=1.
    while f(upper)>0: upper*=2
    mu=brentq(f,0.,upper,xtol=1e-14,rtol=1e-14)
    tau=mu*scale2
    b=U@(tau/(eigen+tau)*(U.T@e))
    residual=e-b
    # Independent constrained optimizer in dimensionless Cartesian coordinates.
    scale=math.sqrt(scale2);es=e/scale;Cs=C/scale2;P=np.linalg.solve(Cs,np.eye(3))
    x0=es*(1-math.sqrt(cut/q0))
    def constraint(x): return cut-float((es-x)@P@(es-x))
    opt=minimize(lambda x:.5*float(x@x),x0,jac=lambda x:x,method="SLSQP",
                 constraints=[{"type":"ineq","fun":constraint,"jac":lambda x:2*P@(es-x)}],
                 options={"ftol":1e-13,"maxiter":500})
    b2=opt.x*scale
    error=float(np.linalg.norm(b-b2))
    if not opt.success or error>1e-9: raise AssertionError("root/constrained calibration disagreement")
    return {"vector_icrs":b.tolist(),"norm_count_dipole":float(np.linalg.norm(b)),
            "fraction_of_excess_norm":float(np.linalg.norm(b)/np.linalg.norm(e)),
            "direction":direction(b),"nominal_residual_quadratic":float(residual@np.linalg.solve(C,residual)),
            "lagrange_multiplier_variance_units":tau,
            "constrained_crosscheck":{"required":True,"method":"SLSQP in Cartesian coordinates","success":bool(opt.success),
                "message":opt.message,"vector_icrs":b2.tolist(),"norm_count_dipole":float(np.linalg.norm(b2)),
                "vector_difference_norm":error,"residual_constraint":constraint(opt.x)},
            "kkt_stationarity_norm":float(np.linalg.norm(b-tau*np.linalg.solve(C,residual)))}

def run(root):
    root=Path(root);source=root/RELATIVE_SOURCE;raw=source.read_bytes();d=json.loads(raw);cut=float(chi2.ppf(.95,3))
    output={"schema":"htt.count_dipole_covariance_sensitivity/1",
            "source_file":RELATIVE_SOURCE,"source_sha256":hashlib.sha256(raw).hexdigest(),
            "source_read_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
            "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
            "units":"dimensionless count-dipole coefficients; signed ICRS vectors",
            "confidence_threshold_nominal_3d":cut,
            "models":{}}
    for key in ["Quaia_G20","NVSS"]:
        rec=d["excess_tests"][key];null=d["velocity_null"][key]
        e=np.asarray(rec["excess_icrs"],dtype=float)
        Cmock=np.asarray(null["cov"],dtype=float);Ctotal=np.asarray(rec["covariance"],dtype=float)
        S=(Ctotal-Cmock);S=(S+S.T)/2
        eigS=np.linalg.eigvalsh(S);tol=64*np.finfo(float).eps*max(float(np.linalg.norm(Ctotal,2)),1e-30)
        if np.min(eigS)<-tol: raise AssertionError("receipt covariance increment is not PSD")
        def point(lam):
            C=Cmock+lam*S;r=np.linalg.solve(C,e);w=float(e@r)
            return {"lambda_covariance_fraction":float(lam),"statistic":w,"p_gaussian_nominal":float(chi2.sf(w,3)),
                    "d_statistic_d_lambda":-float(r@S@r)}
        path=[point(float(lam)) for lam in np.linspace(0,1,101)]
        first,last=path[0],path[-1]
        end_error=abs(last["p_gaussian_nominal"]-rec["chi2"]["p_value"])
        if end_error>1e-10: raise AssertionError("saved Gaussian p-value not reproduced")
        monotonic=max(np.diff([r["statistic"] for r in path]))<=1e-10
        if not monotonic: raise AssertionError("quadratic is not nonincreasing")
        crossing=None
        if first["statistic"]>cut and last["statistic"]<cut:
            lamstar=brentq(lambda lam:point(lam)["statistic"]-cut,0.,1.,xtol=1e-14,rtol=1e-14)
            crossing=point(lamstar)
            crossing["systematic_std_scale_relative_to_receipt"]=math.sqrt(lamstar)
        elif abs(first["statistic"]-cut)<=1e-12: crossing=first
        elif abs(last["statistic"]-cut)<=1e-12: crossing=last
        model={"excess_icrs":e.tolist(),"excess_norm_count_dipole":float(np.linalg.norm(e)),"excess_direction":direction(e),
               "C_mock":Cmock.tolist(),"C_total_receipt":Ctotal.tolist(),"S_receipt":S.tolist(),
               "S_receipt_eigenvalues":eigS.tolist(),"S_receipt_psd_tolerance":tol,"S_receipt_psd":bool(np.min(eigS)>=-tol),
               "n_original_mocks":null["n_mocks"],"original_finite_mock_Pi":rec["Pi_mock"],
               "saved_gaussian_with_receipt":rec["chi2"],
               "lambda0_nominal":first,"lambda1_nominal":last,"lambda1_saved_gaussian_p_error_abs":end_error,
               "nominal_p05_crossing":crossing,
               "crossing_interpretation":"crosses from nominal p<0.05 to >=0.05" if crossing else "no crossing in [0,1]; already nominal p>=0.05 at zero" if first["p_gaussian_nominal"]>=.05 else "no crossing in [0,1]",
               "path":path,"quadratic_nonincreasing_on_grid":bool(monotonic),
               "largest_dW_dlambda":max(x["d_statistic_d_lambda"] for x in path),
               "smallest_dp_step":float(min(np.diff([x["p_gaussian_nominal"] for x in path]))),
               "minimum_deterministic_calibration_for_mock_ellipsoid":minimal_shift(e,Cmock,cut)}
        output["models"][key]=model
    output["scope"]=[
        "C(lambda)=C_mock+lambda*S_receipt for lambda in [0,1], conditioning on existing saved matrices and fixed excess vector.",
        "The original finite-mock Pi values remain distinct from every nominal Gaussian tail in this output.",
        "Covariances are estimated from 500 data-conditioned mocks; chi-square tails and ellipsoid levels are nominal, not an exact finite-sample confidence theorem.",
        "The PSD covariance increment implies d(e^T C^-1 e)/d lambda = -(C^-1 e)^T S_receipt (C^-1 e) <= 0 for fixed e; this is not a monotonicity claim for refitted CF4 Wald statistics.",
        "The deterministic calibration is the minimum Euclidean count-dipole offset b satisfying (e-b)^T C_mock^-1(e-b)<=chi2_3(.95); it is a sensitivity threshold, not measured contamination.",
        "No velocity conversion is performed because a physical population response and interpretation must be specified.",
        "No new simulations, null calibration, cross-catalogue probability product, or global-tilt inference was performed.",
    ]
    return output

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--repository-root",default=".");p.add_argument("--output",default="-")
    args=p.parse_args();text=json.dumps(run(args.repository_root),indent=2,allow_nan=False)
    if args.output=="-": print(text)
    else: Path(args.output).write_text(text+"\n",encoding="utf-8")
