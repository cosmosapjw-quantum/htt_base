"""Extension of toy_schemes.py: stage-time rate variants that keep or drop exact substep depth."""
import math, json, sys
import numpy as np
from scipy.integrate import solve_ivp
G = 1.0 - 1.0/math.sqrt(2.0)

def run(R0, k, Ne, gname, n_cells_total=48, span=7.36):
    gf = {"exp": lambda N: math.exp(0.22*(N-Ne)), "sin": lambda N: 1 + 0.3*math.sin(3*(N-Ne))}[gname]
    R = lambda N: R0*math.exp(-k*(N-Ne))
    D = lambda a, b: R0/k*(math.exp(-k*(a-Ne)) - math.exp(-k*(b-Ne)))
    def part(a, b, cap):
        e = list(np.linspace(a, b, 3))
        while True:
            d = [D(e[i], e[i+1]) for i in range(len(e)-1)]
            if max(d) <= cap*(1+8*np.finfo(float).eps): return e, d
            new = [e[0]]
            for i in range(len(e)-1):
                if d[i] > cap*(1+8*np.finfo(float).eps): new.append(e[i]+(e[i+1]-e[i])/2)
                new.append(e[i+1])
            e = new
    def step(y, a, b, d, mode):
        h = b-a; t1, t2 = a+G*h, b
        if mode == "repo": r1 = r2 = d/h
        elif mode == "stage_rate": r1, r2 = R(t1), R(t2)
        elif mode == "stage_rate_norm":   # stage shape, exact depth under the b-weights
            r1, r2 = R(t1), R(t2); s = d/(h*((1-G)*r1 + G*r2)); r1 *= s; r2 *= s
        g1, g2 = gf(t1), gf(t2)
        y1 = (y + G*h*r1*g1)/(1+G*h*r1); f1 = -r1*(y1-g1)
        return (y + (1-G)*h*f1 + G*h*r2*g2)/(1+G*h*r2)
    dN = span/n_cells_total; n = int(round(0.6/dN)); N0 = Ne-n*dN
    sol = solve_ivp(lambda N, y: [-R(N)*(y[0]-gf(N))], (N0-0.3, Ne), [gf(N0-0.3)], method="Radau",
                    rtol=1e-13, atol=1e-16, dense_output=True)
    yex, y0 = sol.sol(Ne)[0], sol.sol(N0)[0]; slip = yex-gf(Ne)
    out = {"slip_over_y": slip/yex}
    for cap in (1.0, 0.5, 0.25, 0.125, 0.0625):
        for mode in ("repo", "stage_rate", "stage_rate_norm"):
            y = y0
            for c in range(n):
                e, d = part(N0+c*dN, N0+(c+1)*dN, cap)
                for j in range(len(d)): y = step(y, e[j], e[j+1], d[j], mode)
            out[f"{mode}@{cap}"] = (y-yex)/slip
    return out

res = {}
for (R0, k, Ne, g, lab) in [(98.40, 5.5, -7.2247, "exp", "first"), (29.46, 9.6, -7.0710, "exp", "second"),
                            (98.40, 5.5, -7.2247, "sin", "first_sin")]:
    r = run(R0, k, Ne, g); res[lab] = r
    print(f"== {lab} slip/y={r['slip_over_y']:.3e}")
    for mode in ("repo", "stage_rate", "stage_rate_norm"):
        vals = [r[f'{mode}@{c}'] for c in (1.0, 0.5, 0.25, 0.125, 0.0625)]
        ords = [math.log2(abs(vals[i]/vals[i+1])) for i in range(4)]
        print(f"  {mode:16s} " + " ".join(f"{v:+.3e}" for v in vals) + "  orders " + " ".join(f"{o:.2f}" for o in ords))
json.dump(res, open(sys.argv[1], "w"), indent=1)
