"""Offline scalar toy (no solver): which stage placement sets the SIGN of the SDIRK collision lag?

y' = rate(N) (g(N) - y) with rate(N), g(N) = x-component of 4 v_b/(3+v_b^2) spline-interpolated
from the 384-cell fluid diagnostics (cell ends). Exact: Radau rtol 1e-13. Scheme 'N': the photon
cell's SDIRK(2,2) with equal-N bisection to depth cap 1 and stages at N_j + c dN_j (as the solver).
Scheme 'tau': same substeps/depths, stages placed where the integrated depth equals c d_j.
Compared at the second common endpoint (cell 1 of the 48 grid; cells 2-3 of 96; 4-7 of 192),
starting from the exact value at that cell's start.
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp, quad
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

W = Path(__file__).resolve().parent
f = np.load(W/"runs/mimic_c384.npz")
N = f["N_end"]; rate = f["rate_fn_end"]; vb = f["v_b_end"]
geq = (4*vb/(3+np.sum(vb*vb, 1))[:, None])[:, 0]
lr = CubicSpline(N, np.log(rate)); gs = CubicSpline(N, geq)
R = lambda n: math.exp(float(lr(n))); G = lambda n: float(gs(n))
gam = 1 - 1/math.sqrt(2)
common = np.load(W/"runs/repo_c48.npz")["N_end"]
N_start = -math.log1p(1600.0)

def depth(a, b):
    return quad(R, a, b, epsabs=0, epsrel=1e-13, limit=200)[0]

def substeps(a, b, cap=1.0, nmin=2):
    e = list(np.linspace(a, b, nmin+1))
    while True:
        d = [depth(e[i], e[i+1]) for i in range(len(e)-1)]
        split = [i for i, x in enumerate(d) if x > cap*(1+8*np.finfo(float).eps)]
        if not split:
            return np.array(e), np.array(d)
        for i in sorted(split, reverse=True):
            e.insert(i+1, e[i] + (e[i+1]-e[i])/2)

def scheme(y, a, b, mode):
    e, d = substeps(a, b)
    for j in range(len(d)):
        def nstage(c):
            if mode == "N":
                return e[j] + c*(e[j+1]-e[j])
            return brentq(lambda n: depth(e[j], n) - c*d[j], e[j], e[j+1], xtol=1e-15)
        n1, n2 = nstage(gam), e[j+1]
        Y1 = (y + gam*d[j]*G(n1)) / (1 + gam*d[j])
        base = y + ((1-gam)/gam)*(Y1 - y)
        y = (base + gam*d[j]*G(n2)) / (1 + gam*d[j])
    return y

res = {}
for n_cells in (48, 96, 192):
    edges = np.linspace(N_start, 0.0, 2*n_cells+1)[::2]
    out_n = {}
    for tag, k_common in (("first_common", 0), ("second_common", 1)):
        i1 = int(np.flatnonzero(edges == common[k_common])[0])
        stride = n_cells // 48
        i0 = i1 - stride if k_common else i1 - 1          # second: the whole 48-cell span; first: last cell only
        a = edges[i0]
        extrap = bool(a < N[0])
        ex = solve_ivp(lambda n, y: [R(n)*(G(n)-y[0])], (a, edges[i1]), [G(a) - (gs(a, 1)/R(a))],
                       method="Radau", rtol=1e-13, atol=1e-22, dense_output=True)
        out = {"start_ln_a": float(a), "extrapolated_inputs": extrap}
        for mode in ("N", "tau"):
            y = float(ex.sol(a)[0])
            for k in range(i0, i1):
                y = scheme(y, edges[k], edges[k+1], mode)
            yex = float(ex.sol(edges[i1])[0])
            slip = yex - G(edges[i1])
            out[mode] = {"scheme_minus_exact": y - yex, "over_slip": (y - yex)/slip}
        out_n[tag] = out
        print(n_cells, tag, "start %.6f extrap=%s" % (a, extrap), {m: "%.4e" % out[m]["over_slip"] for m in ("N", "tau")})
    res[n_cells] = out_n
(W/"TOY_STAGE_PLACEMENT.json").write_text(json.dumps(res, indent=1) + "\n")
