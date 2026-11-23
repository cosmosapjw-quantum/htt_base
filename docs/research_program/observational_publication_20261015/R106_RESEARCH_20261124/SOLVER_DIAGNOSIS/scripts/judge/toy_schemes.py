"""Scalar tight-coupling toy: dy/dN = -R(N) (y - g(N)), R = R0 exp(-k (N-Ne)).
Compares photon-cell collision substep schemes against the exact solution at a cell endpoint,
using the repo partition rule (min 2 equal-N steps, equal-N bisection until depth <= cap).
Reports (scheme - exact)/slip at the endpoint, slip = exact - g."""
import math, json, sys
import numpy as np
from scipy.integrate import solve_ivp

G = 1.0 - 1.0/math.sqrt(2.0)

def make(R0, k, Ne, gfun):
    R = lambda N: R0*math.exp(-k*(N-Ne))
    D = lambda a, b: R0/k*(math.exp(-k*(a-Ne)) - math.exp(-k*(b-Ne)))
    Ninv = lambda a, tau: Ne - math.log(math.exp(-k*(a-Ne)) - tau*k/R0)/k  # N with depth(a,N)=tau
    return R, D, Ninv

def partition(D, a, b, m, cap):
    e = list(np.linspace(a, b, m+1))
    while True:
        d = [D(e[i], e[i+1]) for i in range(len(e)-1)]
        if cap is None or max(d) <= cap*(1+8*np.finfo(float).eps):
            return e, d
        new = [e[0]]
        for i in range(len(e)-1):
            if d[i] > cap*(1+8*np.finfo(float).eps):
                new.append(e[i] + (e[i+1]-e[i])/2)
            new.append(e[i+1])
        e = new

def sdirk_step(y, a, b, depth, R, g, mode, Ninv):
    h = b - a
    if mode == "repo":           # frozen average rate, N-fraction stages (R105)
        ts = [a+G*h, b]; rs = [depth/h]*2
    elif mode == "stage_rate":   # instantaneous rate at N-fraction stages
        ts = [a+G*h, b]; rs = [R(a+G*h), R(b)]
    elif mode == "tau_frac":     # frozen average rate, stages at tau fractions
        ts = [Ninv(a, G*depth), b]; rs = [depth/h]*2
    g1, g2 = g(ts[0]), g(ts[1])
    r1, r2 = rs
    y1 = (y + G*h*r1*g1)/(1 + G*h*r1)
    f1 = -r1*(y1-g1)
    rhs = y + (1-G)*h*f1 + G*h*r2*g2
    return rhs/(1 + G*h*r2)

def advance(y, edges, depths, R, g, mode, Ninv, richardson=False):
    for j in range(len(depths)):
        a, b, d = edges[j], edges[j+1], depths[j]
        if not richardson:
            y = sdirk_step(y, a, b, d, R, g, mode, Ninv)
        else:
            m = a + (b-a)/2
            # depths of equal-N halves (exact integrals)
            DA = d_of(a, m); DB = d_of(m, b)
            yh = sdirk_step(y, a, b, d, R, g, mode, Ninv)
            yq = sdirk_step(sdirk_step(y, a, m, DA, R, g, mode, Ninv), m, b, DB, R, g, mode, Ninv)
            y = (4*yq - yh)/3
    return y

def run(case):
    global d_of
    R0, k, Ne, gname = case["R0"], case["k"], case["Ne"], case["g"]
    gfun = {"exp": lambda N: math.exp(0.22*(N-Ne)),
            "quad": lambda N: 1 + 0.22*(N-Ne) + 0.5*(N-Ne)**2,
            "sin": lambda N: 1 + 0.3*math.sin(3*(N-Ne))}[gname]
    R, D, Ninv = make(R0, k, Ne, gfun)
    d_of = D
    # domain: 3 e-folds before Ne, cells of width dN, endpoint Ne
    out = {}
    for ncells_per_unit in (48/7.36, 96/7.36, 192/7.36, 384/7.36, 768/7.36, 1536/7.36):
        dN = 1.0/ncells_per_unit
        n = int(round(0.6/dN)); N0 = Ne - n*dN
        # exact solution from equilibrium start
        sol = solve_ivp(lambda N, y: [-R(N)*(y[0]-gfun(N))], (N0-0.3, Ne), [gfun(N0-0.3)], method="Radau",
                        rtol=1e-13, atol=1e-16, dense_output=True)
        yex = sol.sol(Ne)[0]; y0 = sol.sol(N0)[0]
        slip = yex - gfun(Ne)
        row = {}
        for cap in (1.0, 0.5, 0.25, 0.125, 0.0625):
            for mode in ("repo", "tau_frac", "stage_rate"):
                for rich in (False, True):
                    y = y0
                    for c in range(n):
                        a, b = N0 + c*dN, N0 + (c+1)*dN
                        e, d = partition(D, a, b, 2, cap)
                        y = advance(y, e, d, R, gfun, mode, Ninv, rich)
                    row[f"{mode}{'+rich' if rich else ''}@cap{cap}"] = (y - yex)/slip
        out[round(ncells_per_unit*7.36)] = {"slip_rel": slip/yex, **row}
    return out

cases = [dict(R0=98.40, k=5.5, Ne=-7.2247, g="exp"), dict(R0=29.46, k=9.6, Ne=-7.0710, g="exp"),
         dict(R0=98.40, k=5.5, Ne=-7.2247, g="sin")]
res = {}
for c in cases:
    key = f"R0={c['R0']} k={c['k']} g={c['g']}"
    res[key] = run(c)
    print("==", key)
    for nc, row in res[key].items():
        print(f" cells~{nc:5d} slip/y={row['slip_rel']:.3e}  " + "  ".join(
            f"{m}={row[m]:+.3e}" for m in ("repo@cap1.0", "repo@cap0.0625", "repo+rich@cap1.0", "repo+rich@cap0.25",
                                           "tau_frac@cap1.0", "stage_rate@cap1.0", "stage_rate+rich@cap1.0")))
json.dump(res, open(sys.argv[1], "w"), indent=1)
