import json, glob, hashlib, math
from pathlib import Path
import numpy as np
R = {Path(f).stem: json.load(open(f)) for f in sorted(glob.glob("runs/*.json"))}
# plumbing: variant frozen vs repo bit identity
a, b = R["repo_c48"], R["varfrozen_c48"]
same = all(np.array_equal(np.array(a[k]), np.array(b[k])) for k in ("q_sky_all", "q_fluid_all")) and a["C2"] == b["C2"]
print("plumbing varfrozen==repo bitwise:", same, " repo sha", a["solver_sha256"][:12], " variant sha", b["solver_sha256"][:12])
f = R["flrw_stage_c48"]
print("FLRW stage: max|sky q/E|=%.3e max|fluid q/E|=%.3e C2=%s ham=%.3e cod=%.3e reality=%.3e" % (
    f["max_abs_sky_q"], f["max_abs_fluid_q"], f["C2"], f["max_hamiltonian"], f["max_codazzi"], f["stokes_reality"]))
rows = []
print(f"{'label':22s} {'first_rel':>11s} {'par1':>11s} {'perp1':>9s} {'second_rel':>11s} {'par2':>11s} {'worst(cell,lna,rel,dtau,sub)':>44s} {'|pi/E|F sky':>11s} {'dpiF':>8s} {'Ham':>8s} {'Cod':>8s} {'real':>8s} {'C2T':>12s} {'C2E':>12s} {'C2B':>12s} {'subst':>5s} {'wall':>5s}")
for k, r in R.items():
    if r["family"] != "VI_-1/9": continue
    F, S, W = r["first"], r["second"], r["worst"]
    ps, pf = np.array(F["pi_over_E_sky"]), np.array(F["pi_over_E_fluid"])
    print(f"{k:22s} {F['relative']:11.4e} {F['parallel_over_q']:+11.4e} {F['perp_over_q']:9.3e} {S['relative']:11.4e} {S['parallel_over_q']:+11.4e} "
          f"{'(%d,%.4f,%.3e,%.3e,%d)'%(W['cell'],W['ln_a'],W['relative'],W['delta_tau'],W['photon_substeps']):>44s} "
          f"{np.linalg.norm(ps):11.5e} {np.linalg.norm(ps-pf):8.1e} {r['max_hamiltonian']:8.2e} {r['max_codazzi']:8.2e} {r['stokes_reality']:8.1e} "
          f"{r['C2']['T']:12.6e} {r['C2']['E']:12.6e} {r['C2']['B']:12.6e} {r['total_substeps']:5d} {r['wall_solve_s']:5.1f}")
def rich(e48, e96, e192):
    r = (e96-e48)/(e192-e96); return r, e192 + (e192-e96)/(r-1)
for cap in ("", "_cap0.5"):
    e = [R[f"stage_c{n}{cap}"]["first"]["relative"] for n in (48, 96, 192)]
    p = [R[f"stage_c{n}{cap}"]["first"]["parallel_over_q"] for n in (48, 96, 192)]
    e2 = [R[f"stage_c{n}{cap}"]["second"]["relative"] for n in (48, 96, 192)]
    print("stage cap", cap or "1.0", "first norm r=%.3f lim=%.4e | signed par r=%.3f lim=%+.4e | second norm r=%.3f lim=%.4e" % (*rich(*e), *rich(*p), *rich(*e2)))
# A/B decomposition vs cap at fixed cells (signed parallel), e = A c^2 + B
for n in (48, 96, 192):
    for ep in ("first", "second"):
        e1 = R[f"stage_c{n}"][ep]["parallel_over_q"]; e5 = R[f"stage_c{n}_cap0.5"][ep]["parallel_over_q"]
        A = (e1-e5)/0.75; print(f"stage n={n} {ep}: A(cap^2 coeff)={A:+.4e} B(cell term)={e1-A:+.4e}")
e1 = R["stage_c192"]["first"]["parallel_over_q"]; e5 = R["stage_c192_cap0.5"]["first"]["parallel_over_q"]; A=(e1-e5)/0.75
print("cap0.25@192 predicted par1 %.4e measured %.4e" % (A*0.0625 + e1 - A, R["stage_c192_cap0.25"]["first"]["parallel_over_q"]))
for n in (48, 96, 192):
    for ep in ("first", "second"):
        print(f"stage c{n} {ep} sky-fluid signed:", ["%+.6e" % x for x in R[f"stage_c{n}"][ep]["sky_minus_fluid"]], "cap0.5:", ["%+.6e" % x for x in R[f"stage_c{n}_cap0.5"][ep]["sky_minus_fluid"]])
for k in ("stage_c384", "stage_c192_cap0.25", "stagenorm_c48", "repo_c48"):
    for ep in ("first", "second"):
        print(f"{k} {ep} ln_a={R[k][ep]['ln_a']!r} signed:", ["%+.6e" % x for x in R[k][ep]["sky_minus_fluid"]])
