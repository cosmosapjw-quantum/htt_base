#!/usr/bin/env python3
"""Research-only reference experiments. No production or observational admission.

Run from any directory; output files live next to this script in evidence/.
Dependencies: numpy, scipy, matplotlib. Tolerances/seed set in REVISION_SPEC.md.
"""
from __future__ import annotations

import itertools
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.stats import chi2, norm

SEED, DRAWS, ALPHA, ATOL, MC_TOL = 20260912, 100000, .05, 1e-10, .005
OUT = Path(__file__).resolve().parent / "evidence"


def path_operators(dimensions, kernels):
    """Fixed rectangular transports; retain initial block for an invertible view."""
    if len(kernels) != len(dimensions) - 1 or any(d <= 0 for d in dimensions):
        raise ValueError("one transport per adjacent pair and positive dimensions required")
    offsets = np.r_[0, np.cumsum(dimensions)]
    h = np.zeros((sum(dimensions[1:]), sum(dimensions)))
    start = 0
    for j, k in enumerate(kernels):
        k = np.asarray(k, dtype=float)
        if k.shape != (dimensions[j+1], dimensions[j]) or not np.isfinite(k).all():
            raise ValueError("transport shape or finite-value mismatch")
        end = start + dimensions[j+1]
        h[start:end, offsets[j]:offsets[j+1]] = -k
        h[start:end, offsets[j+1]:offsets[j+2]] = np.eye(dimensions[j+1])
        start = end
    initial = np.eye(sum(dimensions))[:dimensions[0]]
    return h, np.vstack((initial, h))


def quadratic_on_support(residual, covariance):
    """Small-matrix numerical oracle, not an interval-certified rank algorithm."""
    r, c = np.asarray(residual, float), np.asarray(covariance, float)
    if c.shape != (len(r), len(r)) or not np.isfinite(c).all() or not np.isfinite(r).all():
        raise ValueError("invalid finite residual/covariance")
    if not np.allclose(c, c.T, atol=ATOL, rtol=0):
        raise ValueError("covariance not symmetric")
    eig, basis = np.linalg.eigh(c)
    scale = max(1., float(np.max(np.abs(eig))))
    if np.min(eig) < -ATOL * scale:
        raise ValueError("covariance not PSD")
    keep = eig > ATOL * scale
    coords = basis.T @ r
    if np.linalg.norm(coords[~keep]) > ATOL * max(1., np.linalg.norm(r)):
        return {"status": "OUTSIDE_DETERMINISTIC_SUPPORT", "rank": int(sum(keep)), "q": None}
    return {"status": "ON_SUPPORT", "rank": int(sum(keep)),
            "q": float(np.sum(coords[keep]**2/eig[keep]))}


def stf3_basis():
    """Construct STF tensors by trace removal, independently of contraction inverse."""
    projected = []
    eye = np.eye(3)
    for ijk in itertools.combinations_with_replacement(range(3), 3):
        a = np.zeros((3, 3, 3))
        for p in set(itertools.permutations(ijk)):
            a[p] = 1.
        tr = np.einsum("iik->k", a)
        a -= (np.einsum("ij,k->ijk", eye, tr)
              + np.einsum("ik,j->ijk", eye, tr)
              + np.einsum("jk,i->ijk", eye, tr))/5
        projected.append(a.ravel())
    u, s, _ = np.linalg.svd(np.stack(projected, axis=1))
    assert sum(s > ATOL) == 7
    return u[:, :7].T.reshape(7, 3, 3, 3)


def main():
    rng = np.random.default_rng(SEED)
    checks, rows = {}, []
    h, t = path_operators([1, 1, 1], [np.ones((1, 1))]*2)
    v = h @ h.T
    assert np.array_equal(v, [[2., -1.], [-1., 2.]])
    assert np.array_equal(h @ np.ones(3), [0., 0.])
    assert abs(np.linalg.det(t)-1) < ATOL
    info = t.T @ np.linalg.solve(t @ t.T, t)
    assert np.max(np.abs(info-np.eye(3))) < ATOL
    checks["path_exact"] = {"H": h.tolist(), "V": v.tolist(),
        "discarded_common_mode": (h@np.ones(3)).tolist(), "anchored_det": float(np.linalg.det(t)),
        "anchored_information_error": float(np.max(np.abs(info-np.eye(3))))}

    raw = rng.standard_normal((DRAWS, 3))
    residuals = raw @ h.T
    correct = np.einsum("ni,ij,nj->n", residuals, np.linalg.inv(v), residuals)
    wrong = np.sum(residuals**2, axis=1)/2
    threshold2 = chi2.ppf(1-ALPHA, 2)
    fpr_wrong_exact = quad(lambda angle: np.exp(-threshold2/(2*(.5*np.cos(angle)**2+1.5*np.sin(angle)**2))),
                           0, 2*np.pi, epsabs=1e-12)[0]/(2*np.pi)
    correct_rate, wrong_rate = float(np.mean(correct>threshold2)), float(np.mean(wrong>threshold2))
    assert abs(correct_rate-ALPHA) < MC_TOL
    assert abs(wrong_rate-fpr_wrong_exact) < MC_TOL
    assert fpr_wrong_exact > ALPHA + .005
    rows.append({"case":"three independent inputs, two overlapping differences", "correct_fpr":correct_rate,
        "wrong_fpr":wrong_rate, "wrong_exact_fpr":fpr_wrong_exact,
        "wrong_reference":"chi-square 2 after deleting cross-step covariance"})
    threshold1 = chi2.ppf(1-ALPHA, 1)
    for rho in (-.8, 0., .8):
        draws = rng.multivariate_normal([0., 0.], [[1.,rho],[rho,1.]], size=DRAWS)
        delta = draws[:,1]-draws[:,0]
        truevar = 2-2*rho
        exact_wrong = float(2*norm.sf(np.sqrt(threshold1/(1-rho))))
        cr = float(np.mean(delta**2/truevar>threshold1))
        wr = float(np.mean(delta**2/2>threshold1))
        assert abs(cr-ALPHA) < MC_TOL and abs(wr-exact_wrong) < MC_TOL
        rows.append({"case":f"two inputs rho={rho:g}", "rho":rho, "true_variance":truevar,
                     "correct_fpr":cr,"wrong_fpr":wr,"wrong_exact_fpr":exact_wrong})

    duplicate_v = h @ np.ones((3,3)) @ h.T
    on = quadratic_on_support([0.,0.], duplicate_v)
    off = quadratic_on_support([1.,0.], duplicate_v)
    assert on["rank"] == 0 and on["q"] == 0 and off["status"] == "OUTSIDE_DETERMINISTIC_SUPPORT"
    checks["singular_support"] = {"duplicate_covariance":duplicate_v.tolist(),"zero":on,"violation":off}
    checks["common_mode_information"] = {"full":3.,"contrast_only":float((h@np.ones(3))@np.linalg.solve(v,h@np.ones(3))),"anchored":float(np.ones(3)@info@np.ones(3))}
    # A rectangular K still gives a square invertible anchored transform.
    hr, tr = path_operators([2,1,2], [np.array([[1.,2.]]), np.array([[1.],[3.]])])
    assert np.linalg.matrix_rank(tr) == 5 and abs(np.linalg.det(tr)-1)<ATOL
    checks["rectangular_transport"] = {"dimension":5,"contrast_rank":int(np.linalg.matrix_rank(hr)),"anchored_rank":5}

    basis = stf3_basis()
    q = np.diag([1.,-1.,0.])/np.sqrt(2.)
    l = np.einsum("sijk,jk->is", basis, q)
    m = np.eye(3)+6*(q@q)/5
    assert np.max(np.abs(l@l.T-m/3)) < ATOL
    right = l.T @ np.linalg.inv(l@l.T)
    nullp = np.eye(7)-right@l
    eta_metric = right.T@right
    assert np.max(np.abs(eta_metric-3*np.linalg.inv(m))) < ATOL
    direction = rng.standard_normal(7)
    vv = np.array([.1,.15,-.05])
    center = right@vv
    eta = float(center@center)
    radial = np.sqrt(1-eta)
    null_direction = nullp@direction
    witness = center+radial*null_direction/np.linalg.norm(null_direction)
    support = float(direction@center+radial*np.linalg.norm(null_direction))
    assert abs(witness@witness-1)<ATOL
    assert np.max(np.abs(l@witness-vv))<ATOL
    assert abs(direction@witness-support)<ATOL
    # Kernel witnesses test the support bound independently of its maximizer.
    ns = rng.standard_normal((10000,7))@nullp
    ns /= np.linalg.norm(ns,axis=1)[:,None]
    sampled = center+radial*ns
    assert np.max(sampled@direction) <= support+ATOL
    boundary_v=np.array([1.,0.,0.])/np.sqrt(eta_metric[0,0])
    boundary=[]
    for step in (1e-2,1e-4,1e-6):
        vstep=(1-step)*boundary_v
        dist2=np.linalg.norm(right@(vstep-boundary_v))**2+(np.sqrt(max(0.,1-np.linalg.norm(right@vstep)**2)))**2
        assert abs(dist2-2*step)<ATOL
        boundary.append({"step":step,"hausdorff":float(np.sqrt(dist2)),"linear_input_change":float(np.linalg.norm(vstep-boundary_v))})
    checks["fibre"]={"fixed_q":q.tolist(),"kernel_dimension":4,"eta":eta,"support":support,
        "max_sampled_value":float(np.max(sampled@direction)),"witness_norm":float(np.linalg.norm(witness)),
        "contraction_error":float(np.linalg.norm(l@witness-vv)),"boundary":boundary}

    # Joint anchor tuples vs independent marginal endpoints.
    tuples=np.array([[1.,1.],[2.,2.]])
    paired=tuples[:,0]/tuples[:,1]
    assert np.array_equal(paired,[1.,1.])
    checks["random_anchor"]={"paired_ratios":paired.tolist(),"cartesian_interval":[.5,2.],
        "scope":"algebraic dependence control only, not a coverage simulation",
        "zero_denominator":"undefined/unbounded by declared extended target, never epsilon-clipped"}
    for row in rows:
        for kind in ("correct", "wrong"):
            estimate = row[f"{kind}_fpr"]
            z95 = norm.ppf(.975)
            denom = 1+z95*z95/DRAWS
            middle = (estimate+z95*z95/(2*DRAWS))/denom
            half = z95*np.sqrt(estimate*(1-estimate)/DRAWS+z95*z95/(4*DRAWS**2))/denom
            row[f"{kind}_rejections"] = round(estimate*DRAWS)
            row[f"{kind}_wilson95"] = [max(0.,float(middle-half)),min(1.,float(middle+half))]
    result={"scope":"research-only synthetic/reference; no observed data", "status":"CHECKS_PASSED",
        "seed":SEED,"draws_per_gaussian_cell":DRAWS,"alpha":ALPHA,"atol":ATOL,"mc_tolerance":MC_TOL,
        "versions":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
        "checks":checks,"fpr":rows}
    OUT.mkdir(exist_ok=True)
    (OUT/"research_checks.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    plot(rows, boundary)
    print(json.dumps({"status":result["status"],"fpr":rows,"checks":list(checks)},indent=2))


def plot(rows,boundary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4.2),constrained_layout=True)
    x=np.arange(len(rows)); width=.34
    for kind,shift,label,color in (("correct",-width/2,"Full covariance","#2563a6"),("wrong",width/2,"Cross terms omitted","#bc5136")):
        estimates=np.array([r[f"{kind}_fpr"] for r in rows])
        bounds=np.array([r[f"{kind}_wilson95"] for r in rows])
        axes[0].bar(x+shift,estimates,width,label=label,color=color,
                    yerr=np.array([estimates-bounds[:,0],bounds[:,1]-estimates]),capsize=2)
    axes[0].axhline(ALPHA,color="#222",linestyle="--",linewidth=1)
    axes[0].set_xticks(x,["3-depth\npath","rho=-0.8","rho=0","rho=0.8"])
    axes[0].set_ylabel("Rejection fraction under the fixed Gaussian null")
    axes[0].set_title("A. Correlation omission changes size")
    axes[0].legend(fontsize=8)
    tt=np.geomspace(1e-6,1e-2,100)
    axes[1].loglog(tt,np.sqrt(2*tt),color="#2563a6",label="Exact fibre Hausdorff distance")
    axes[1].loglog(tt,tt,linestyle="--",color="#777",label="Linear reference t")
    axes[1].scatter([b["step"] for b in boundary],[b["hausdorff"] for b in boundary],color="#bc5136",s=25)
    axes[1].set_xlabel("Contraction perturbation t")
    axes[1].set_ylabel("Distance in unit STF3 shape space")
    axes[1].set_title("B. Square-root boundary sensitivity")
    axes[1].legend(fontsize=8)
    fig.suptitle("R9 revision 2 — synthetic research controls; no observational inference",fontsize=11)
    fig.savefig(OUT/"research_controls.png",dpi=170)
    fig.savefig(OUT/"research_controls.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
