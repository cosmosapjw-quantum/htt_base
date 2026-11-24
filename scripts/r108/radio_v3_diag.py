"""R108 radio lane: diagnostic of the low-l difference between the TF7 integrator and CAMB number counts (V3).

Purpose: decide whether the V3 deficit of the TF7 integrator relative to CAMB 'counts_density' at l = 2..4 comes from the
P(k,z) interpolation (CAMB k sampling, k_per_logint = default vs 50) or from the choice of density variable
(delta_cdm, delta_tot, delta_nonu, all synchronous gauge), for the smooth Gaussian test window (z0, sigma) = (1.0, 0.30),
b = 2, massless neutrinos. If none of these moves C_2 by more than 1e-3 relative, the difference is not a numerical error
of the integrator's P(k) sampling or matter variable. The CAMB side is varied too (R108 review RADIO-1): CAMB counts_density
C_2..C_4 for the same window (the one that sets the V3 low-l systematic) at AccuracyBoost = lAccuracyBoost = 1 and 2
(lSampleBoost = 50 in both). The (0.5, 0.15) window is not varied: its accuracy-2 CAMB run exceeded 10 min in R108
(radio_camb_timing.log). The gap is
labelled 'unexplained (not integrator P(k) sampling / matter variable, not CAMB accuracy)' only if both variations are
small against it (integrator spread < 1e-3 and CAMB accuracy change < 0.1 x |gap at l = 2|); it is not attributed.
Inputs: none (CAMB 2.0.5). Units: C_l dimensionless.
Usage (repo root, system python): python3 -m scripts.r108.radio_v3_diag --out docs/.../RADIO/V3_DIAGNOSTIC.json
Deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from scripts.r108 import radio_theory_c1 as T


ACCURACIES = (1.0, 2.0)


def gap_label(integrator_spread, camb_accuracy_change, gap_l2):
    """Label of the low-l integrator/CAMB gap from the two variations (no attribution is made)."""
    small_int = integrator_spread < 1e-3
    small_camb = camb_accuracy_change < 0.1 * abs(gap_l2)
    if small_int and small_camb:
        return "unexplained (not integrator P(k) sampling / matter variable, not CAMB accuracy)"
    parts = [] if small_int else ["integrator P(k) sampling / matter variable moves C_l by >= 1e-3"]
    if not small_camb:
        parts.append("CAMB accuracy moves C_l by >= 0.1 x the gap")
    return "not resolved: " + "; ".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import camb
    pars = T.camb_params(nonlinear=False, massless_nu=True, kmax=10.0)
    res = camb.get_background(pars)
    zt = np.concatenate([np.linspace(0, 0.2, 401)[:-1], np.linspace(0.2, 7.5, 1201)])
    bg = T.Background(zt, res.comoving_radial_distance(zt), res.hubble_parameter(zt) / T.C_KM_S, growth=np.ones_like(zt),
                      omega_m=0.3, h0c=pars.H0 / T.C_KM_S)
    name = "gauss_z1p0_s0p30"
    zc, sg = T.GAUSS_V3[name]
    kern = T.Kernel(bg, lambda z: T.gauss_nz(name, z), lambda z: T.bias("const2", z), z_lo=max(zc - 6 * sg, 1e-3), z_hi=zc + 6 * sg)
    kk = T.kgrid_log(1e-5, 2.0, 401)
    rows = []
    for var in ("delta_nonu", "delta_tot", "delta_cdm"):
        for kpl in (None, 50):
            pk = camb.get_matter_power_interpolator(pars, zmin=0, zmax=7.5, nz_step=150, kmax=10, nonlinear=False, var1=var, var2=var,
                                                    hubble_units=False, k_hunit=False, extrap_kmax=1e3, k_per_logint=kpl)
            t = T.t_from_interp(pk)
            cl = {ell: T.cl_from_windows(kk, T.windows_for(kern, kk, t, ell)["density"]) for ell in (2, 3, 4)}
            rows.append(dict(var=var, k_per_logint=kpl, C_l=cl))
    camb_cl = T.camb_counts_cls(name, 2.0, 4, ("counts_density",))
    ref = rows[0]["C_l"]
    spread = {ell: max(abs(r["C_l"][ell] / ref[ell] - 1) for r in rows) for ell in (2, 3, 4)}
    acc = {}
    for win in (name,):
        cls = {f"accuracy_{b:g}": T.camb_counts_cls(win, 2.0, 4, ("counts_density",), accuracy=b) for b in ACCURACIES}
        base = cls[f"accuracy_{ACCURACIES[0]:g}"]
        acc[win] = dict(C_l={k: {ell: float(v[ell]) for ell in (2, 3, 4)} for k, v in cls.items()},
                        rel_change_vs_accuracy_1={k: {ell: float(v[ell] / base[ell] - 1) for ell in (2, 3, 4)}
                                                  for k, v in cls.items() if k != f"accuracy_{ACCURACIES[0]:g}"})
    rel = {ell: ref[ell] / float(camb_cl[ell]) - 1 for ell in (2, 3, 4)}
    rel_hi = {ell: ref[ell] / acc[name]["C_l"][f"accuracy_{ACCURACIES[-1]:g}"][ell] - 1 for ell in (2, 3, 4)}
    acc_max = max(abs(x) for w in acc.values() for d in w["rel_change_vs_accuracy_1"].values() for x in d.values())
    verdict = gap_label(max(spread.values()), acc_max, rel[2])
    out = dict(schema="htt.r108.radio.v3_diag/1", window=name, bias=2.0, massless_neutrinos=True,
               command=" ".join([sys.executable, "-m", "scripts.r108.radio_v3_diag", *(argv or sys.argv[1:])]),
               git_head=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               theory_module_sha256=hashlib.sha256(Path(T.__file__).read_bytes()).hexdigest(),
               variants=rows, camb_counts_density={ell: float(camb_cl[ell]) for ell in (2, 3, 4)},
               max_rel_spread_over_variants=spread,
               rel_integrator_minus_camb=rel,
               camb_accuracy_variation=dict(description="CAMB 2.0.5 counts_density, SplinedSourceWindow, b = 2, massless neutrinos, "
                                                        "AccuracyBoost = lAccuracyBoost = b, lSampleBoost = 50; window (1.0, 0.30) "
                                                        "only (sets the V3 low-l systematic; the (0.5, 0.15) accuracy-2 run "
                                                        "exceeded 10 min in R108)",
                                            accuracy_boosts=list(ACCURACIES), windows=acc, max_abs_rel_change=acc_max,
                                            rel_integrator_minus_camb_at_highest_accuracy=rel_hi),
               gap_status=verdict)
    Path(a.out).write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(dict(spread=spread, rel=out["rel_integrator_minus_camb"], camb_accuracy_max_abs_rel_change=acc_max,
                          gap_status=verdict)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
