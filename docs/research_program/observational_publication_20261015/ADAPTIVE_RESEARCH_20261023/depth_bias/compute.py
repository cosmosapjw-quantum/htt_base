"""Conditional coefficient-bias/covariance frontier for the reviewed depth vector."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ADAPTIVE = HERE.parent
SOURCE = ADAPTIVE / "depth_covariance" / "RESULT.json"
INPUT = ADAPTIVE / "R25-K03-DEPTH-BIAS-FRONTIER_INPUT.json"
EXPECTED = {
    INPUT: "34e88ac00f25c5cb849152167f93364491a43e88c2c609e98710d42a04fb39d2",
    SOURCE: "fb4456451cf10582bf7ad1406ae1c5040dbf15b8d662b83ffb07a2f7de97d400",
    ADAPTIVE / "depth_covariance" / "MANIFEST.json": "bee5babe4f0610df53656beb2fd6dc69a99028d5d91e2e847e30be320ab61e9e",
    ADAPTIVE.parent / "METHOD_EXECUTION_20261023" / "tensor_bundle" / "RESULT.json": "7d90415eede2b08fc51067bcff5b3276e3d554f20e90d3d7033692b885a4e7e9",
    ADAPTIVE.parent / "METHOD_EXECUTION_20261023" / "depth_images" / "RESULT.json": "b93bb2829dd90d6ece1afb6e9ef065f8d6e5dd87a702fd06f1979d2681ff7ff2",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    for path, digest in EXPECTED.items():
        if sha(path) != digest:
            raise ValueError(f"immutable source identity changed: {path}")
    spec = json.loads(INPUT.read_text())
    src = json.loads(SOURCE.read_text())
    mu = np.asarray(src["full24"]["mean_uasyr"], float)
    cov = np.asarray(src["full24"]["cov_uasyr2"], float)
    A = np.asarray(src["A12x24"], float)
    G = np.asarray(src["G_F"]["map24_to_Z18"], float)
    S = np.zeros((24, 6)); S[18:, :] = np.eye(6)
    assert mu.shape == (24,) and cov.shape == (24, 24)
    assert A.shape == (12, 24) and G.shape == (18, 24)
    assert np.max(np.abs(cov-cov.T)) < 1e-10
    assert np.linalg.eigvalsh(cov)[0] > 0
    assert np.linalg.matrix_rank(A) == 12 and np.linalg.matrix_rank(A @ S) == 6
    return spec, src, mu, cov, A, G, S


def solve(y, W, delta):
    """Compact positive-rank SVD trust-region least squares, including rank zero."""
    U, sv, Zt = np.linalg.svd(W, full_matrices=False)
    tol = np.finfo(float).eps * max(W.shape) * (sv[0] if sv.size else 0)
    rank = int(np.count_nonzero(sv > tol))
    U, sv, Zt = U[:, :rank], sv[:rank], Zt[:rank]
    proj = U.T @ y
    orth = y - U @ proj
    if rank == 0 or delta == 0:
        b = np.zeros(W.shape[1]); lam = 0.0 if rank == 0 else None
        branch = "zero_rank" if rank == 0 else "zero_radius"
    else:
        b_free = Zt.T @ (proj / sv)
        if np.linalg.norm(b_free) <= delta:
            b = b_free; lam = 0.0; branch = "unconstrained"
        else:
            norm_at = lambda t: np.linalg.norm(sv * proj / (sv*sv + t))
            hi = max(1.0, float(sv[0]**2))
            while norm_at(hi) > delta:
                hi *= 2
            lam = brentq(lambda t: norm_at(t)-delta, 0, hi, xtol=1e-14, rtol=1e-14)
            b = Zt.T @ (sv * proj / (sv*sv + lam))
            branch = "boundary"
    residual = y - W @ b
    objective = float(residual @ residual)
    if branch == "zero_radius":
        stationarity = None  # singleton feasible set; finite ball multiplier is not defined
        scaled_stationarity = None
    else:
        stationarity = float(np.linalg.norm(W.T @ (W @ b-y) + lam*b))
        scale = max(1.0, float(np.linalg.norm(W.T @ y)),
                    float(np.linalg.norm(W.T @ W @ b)), float(lam*np.linalg.norm(b)))
        scaled_stationarity = stationarity / scale
    return {
        "b": b, "T": objective, "rank": rank, "singular_values": sv,
        "orthogonal_residual_norm2": float(orth @ orth),
        "norm": float(np.linalg.norm(b)), "lambda": lam,
        "branch": branch, "kkt_stationarity_abs": stationarity,
        "kkt_stationarity_scaled": scaled_stationarity,
        "feasibility_excess": float(max(0, np.linalg.norm(b)-delta)),
    }


def whitening(mu, cov, A, scope, tau):
    U24 = cov + tau*tau*np.eye(24)
    V = A @ U24 @ A.T
    L = np.linalg.cholesky(V)
    d = A @ mu
    return np.linalg.solve(L, d), np.linalg.solve(L, A @ scope), U24, V


def independent_control(y, W, delta, candidate):
    # SLSQP optimizes the original constrained objective, independent of SVD/secular root.
    fun = lambda b: float(np.linalg.norm(y-W@b)**2)
    jac = lambda b: 2 * W.T @ (W@b-y)
    if delta == 0:
        value = fun(np.zeros(W.shape[1])); success = True
    else:
        result = minimize(fun, np.zeros(W.shape[1]), jac=jac, method="SLSQP",
                          constraints=[{"type": "ineq", "fun": lambda b: delta**2-b@b,
                                        "jac": lambda b: -2*b}],
                          options={"ftol": 1e-10, "maxiter": 2000})
        value = float(result.fun); success = bool(result.success)
    return {"independent_T": value, "SLSQP_success": success,
            "objective_abs_difference": abs(value-candidate["T"]),
            "objective_agreement": bool(success and np.isclose(value,candidate["T"],rtol=1e-8,atol=1e-9))}


def frontier(y, W, threshold):
    at0 = solve(y,W,0)
    if at0["T"] <= threshold:
        return {"status":"already_contained", "delta":0.0, "T":at0["T"], "witness":at0["b"].tolist()}
    free = solve(y,W,float("inf"))
    if free["T"] > threshold + 1e-9:
        return {"status":"never_reached", "least_squares_floor":free["T"],
                "least_squares_radius":free["norm"], "least_squares_witness":free["b"].tolist(),
                "orthogonal_residual_norm2":free["orthogonal_residual_norm2"]}
    radius = brentq(lambda d: solve(y,W,d)["T"]-threshold,0,free["norm"],xtol=1e-11,rtol=1e-12)
    fit = solve(y,W,radius)
    return {"status":"crossed", "delta":float(radius), "T":fit["T"],
            "witness":fit["b"].tolist(), "witness_norm":fit["norm"]}


def support(mu, U24, map18, scope, delta, rho, direction):
    v = map18.T @ direction if map18 is not None else direction
    bias_vec = scope.T @ v
    bn = np.linalg.norm(bias_vec)
    b = np.zeros(scope.shape[1]) if bn == 0 else delta*bias_vec/bn
    cn = np.sqrt(float(v @ U24 @ v))
    covariance_witness = np.zeros(24) if cn == 0 else rho*U24@v/cn
    h = float(v@mu + delta*bn + rho*cn)
    attained = float(v@(mu+scope@b+covariance_witness))
    return {"value":h,"attained":attained,"bias_witness":b.tolist(),
            "covariance_witness24":covariance_witness.tolist(),"direction":direction.tolist()}


def main():
    started = time.monotonic()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    spec, src, mu, cov, A, G, S = load()
    taus = spec["tau_uasyr"]; deltas = spec["delta_uasyr"]
    thresholds = {"gaussian_chi2_12_95":float(chi2.ppf(.95,12)),"moment_240":240.0}
    scopes = {"full24":np.eye(24),"slope6":S}
    result = {"task_id":spec["task_id"],"input_identity":"sha256:"+sha(INPUT),
              "units":"microarcsec/year", "thresholds":thresholds,
              "coordinates":src["coordinates"],"full24":src["full24"],
              "A12x24":src["A12x24"],"G18x24":src["G_F"]["map24_to_Z18"],
              "scopes":{},"source_science":{k:src[k] for k in ("x","Q","F","Pi","G_F")},
              "physical_status":"HOLD; physical Pi and physical Q UNKNOWN; original K03 unchanged",
              "claim_ceiling":spec["claim_ceiling"]}
    controls = []
    for name, scope in scopes.items():
        rows=[]; fronts=[]
        for tau in taus:
            y,W,U24,V = whitening(mu,cov,A,scope,tau)
            cells=[]
            for delta in deltas:
                f=solve(y,W,delta)
                cell={"delta":delta,"T":f["T"],"bias_witness":f["b"].tolist(),
                      "bias_witness24":(scope@f["b"]).tolist(),
                      "witness_norm":f["norm"],"branch":f["branch"],
                      "rank":f["rank"],"orthogonal_residual_norm2":f["orthogonal_residual_norm2"],
                      "kkt_stationarity_abs":f["kkt_stationarity_abs"],
                      "kkt_stationarity_scaled":f["kkt_stationarity_scaled"],
                      "feasibility_excess":f["feasibility_excess"],"lambda":f["lambda"]}
                cells.append(cell)
                if delta in (0,1,10) and tau in (0,.3,10):
                    controls.append({"scope":name,"tau":tau,"delta":delta,
                                     **independent_control(y,W,delta,f)})
            rows.append({"tau":tau,"cells":cells,"V12x12":V.tolist()})
            fronts.append({"tau":tau,"thresholds":{key:frontier(y,W,val) for key,val in thresholds.items()},
                           "unrestricted_least_squares":{key: (float(v) if isinstance(v,(float,np.floating)) else v)
                                                        for key,v in solve(y,W,float("inf")).items() if key not in ("b","singular_values")}})
        result["scopes"][name]={"grid":rows,"frontiers":fronts}
    b0=A.T@np.linalg.solve(A@A.T,A@mu)
    result["full24_zero_residual"]={"radius":float(np.linalg.norm(b0)),
        "witness24":b0.tolist(),"relative_Ab_minus_d":float(np.linalg.norm(A@b0-A@mu)/np.linalg.norm(A@mu)),
        "tau_invariant":True}
    result["independent_controls"]=controls
    rho=1.0; tau=.3; delta=1.0; U24=cov+tau*tau*np.eye(24)
    u24=np.arange(1,25,dtype=float);u24/=np.linalg.norm(u24)
    u18=np.arange(1,19,dtype=float);u18/=np.linalg.norm(u18)
    result["support_examples"]={name:{"full24":support(mu,U24,None,scope,delta,rho,u24),
                                        "G_F18":support(mu,U24,G,scope,delta,rho,u18)}
                                for name,scope in scopes.items()}
    result["support_examples_parameters"]={"tau":tau,"delta":delta,"rho":rho,
      "rho_status":"named reference radius, no coverage calibration"}
    result["runtime_seconds"]=time.monotonic()-started
    (HERE/"RESULT.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout="constrained")
    for ax,(name,part) in zip(axes,result["scopes"].items()):
        for row in part["grid"]:
            ax.plot(deltas,[c["T"] for c in row["cells"]],marker="o",label=f"tau={row['tau']}")
        for label,threshold in thresholds.items():
            ax.axhline(threshold,ls="--",lw=1,label=label)
        ax.set(xlabel="bias radius delta (microarcsec/year)",ylabel="minimized contrast T",title=name,
               yscale="symlog",xscale="symlog",ylim=(0,450))
        ax.set_xticks(deltas,[str(x) for x in deltas])
        ax.grid(alpha=.25);ax.legend(fontsize=7)
    fig.suptitle("Selected reported-depth contrast: conditional bias/covariance sensitivity")
    fig.savefig(HERE/"figure.png",dpi=160)
    plt.close(fig)
    print(json.dumps({"production_seconds":time.monotonic()-started,"grid_cells":72,
                      "independent_controls":len(controls),"full24_zero_radius":result["full24_zero_residual"]["radius"]}))


if __name__ == "__main__":
    main()
