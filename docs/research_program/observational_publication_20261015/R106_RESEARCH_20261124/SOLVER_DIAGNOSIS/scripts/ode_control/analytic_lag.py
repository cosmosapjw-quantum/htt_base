"""Leading-order analytic SDIRK(2,2) collision-lag estimate at the common endpoints (no solver calls).

Exact steady offset of the photon-cell SDIRK(2,2) stage scheme for y' = -(y - g(tau)), g quadratic:
  delta(h) = a h^2 (7 - 5 sqrt2) / (2 (10 h - 7 sqrt2 h + 4 - 2 sqrt2)),  a = g''_tautau.
Here g(tau) = r_eq(N(tau)), r_eq = 4 v_b/(3+v_b^2), d tau = rate dN, so
  g'' = (1/rate) d/dN [ (d r_eq/dN) / rate ].
d r_eq/dN and rate at cell ends come from the fluid-equation diagnostics recorded in the 384-cell
stash-variant run; the derivative is a centred finite difference on that grid.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from scripts.r105.common_time_moments import nested_samples

W = Path(__file__).resolve().parent
S2 = math.sqrt(2.0)

def coef(h):
    return h**2 * (7 - 5*S2) / (2*(10*h - 7*S2*h + 4 - 2*S2))

fine = np.load(W/"runs/mimic_c384.npz")
vb = fine["v_b_end"]; v2 = np.sum(vb*vb, 1)
J = 4/(3+v2)[:, None, None]*np.eye(3) - 8*np.einsum("ni,nj->nij", vb, vb)/((3+v2)**2)[:, None, None]
dreq = np.einsum("nij,nj->ni", J, fine["dvb_dN"])
rate = fine["rate_fn_end"]; N = fine["N_end"]
gp = dreq / rate[:, None]
gpp = np.gradient(gp, N, axis=0) / rate[:, None]
common = np.load(W/"runs/repo_c48.npz")["N_end"]
out = {}
for k in range(2):
    i = int(np.flatnonzero(N == common[k])[0])
    row = {"ln_a": float(N[i]), "rate": float(rate[i]), "g_prime": gp[i].tolist(), "g_second": gpp[i].tolist()}
    for lab in ("mimic_c48", "mimic_c96", "mimic_c192", "mimic_c384"):
        h = np.load(W/f"runs/{lab}.npz")
        r = nested_samples(common, h["N_end"], h["q_over_E_sky"][0], h["q_over_E_fluid"][0])[k]
        c = r["cell_index"]
        hd = float(h["delta_tau"][c] / h["photon_substeps"][c])
        pred = coef(hd) * gpp[i]
        meas = np.asarray(r["sky_minus_fluid"])
        row[lab] = {"mean_substep_depth": hd, "analytic_delta": pred.tolist(), "measured_sky_minus_fluid": meas.tolist(),
                    "analytic_over_measured_dot": float(pred @ meas / (meas @ meas))}
    out[["first_common", "second_common"][k]] = row
(W/"ANALYTIC_LAG.json").write_text(json.dumps(out, indent=1) + "\n")
for k, row in out.items():
    print(k, "rate %.3f" % row["rate"], "g''", np.round(row["g_second"], 14))
    for lab in ("mimic_c48", "mimic_c96", "mimic_c192", "mimic_c384"):
        x = row[lab]; print("  ", lab, "h=%.4f" % x["mean_substep_depth"], "analytic/measured=%.3f" % x["analytic_over_measured_dot"])
