"""Bounded independent contract probes. No product writes and no main() calls."""
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent
os.environ.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
                  MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1",
                  MPLCONFIGDIR=str(OUT / "mplconfig"))

import hashlib
import importlib.util
import json
import subprocess
import sys
import mpmath as mp
import numpy as np
import sympy as sp

ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
PA = ROOT / "docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025"
PRODUCT = PA / "products/R32-04-BANDPASS-BOUNDS"
SOURCE = PA / "evidence/R31/report/data/RESULT.json"
paths = [PA / "FRONTIER.json", SOURCE,
         Path("/mnt/extdrive/workdir/htt_open_data/r35_h03_bandpass_contract_intake/CONTRACT.md"),
         PRODUCT / "report/main.tex", PRODUCT / "repair_02/consumer.py",
         PRODUCT / "repair_04/consumer.py"]
paths += [PRODUCT / "repair_05" / x for x in (
    "consumer.py", "report/main.tex", "CLAIM_SOURCE_MAP.md",
    "test_pure_target_boundary.py", "test_bandpass_boundary_repair.py",
    "test_center_geometry.py", "test_range_boundary.py", "test_structural_range.py",
    "ordinary_probe.py", "raw/pytest_puretarget_first.stdout",
    "raw/pytest_puretarget_first.stderr")]

def identity(p):
    b = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

before = [identity(p) for p in paths]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == "b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f"
source = json.loads(SOURCE.read_text())["branches"]

def load(name, repair):
    spec = importlib.util.spec_from_file_location(name, PRODUCT / repair / "consumer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

current = load("unsealed_subject", "repair_05")
old02 = load("historical_bp04_subject", "repair_02")
old04 = load("historical_bp05_subject", "repair_04")
rat = lambda x: sp.Rational(*float(x).as_integer_ratio())
mp.mp.dps = 150
to_mp = lambda q: mp.mpf(int(q.p)) / int(q.q)
show = lambda x: mp.nstr(x, 45)
H = sp.zeros(6, 7)
for i in range(6):
    H[i, 0], H[i, i+1] = -1, 1

def oracle(F, d):
    # Independent exact row-contrast elimination of the common target.
    G = sp.Matrix([[rat(F[i,j]) / rat(d[j]) for j in range(9)] for i in range(7)])
    A = H * G
    W = (A * A.T).inv(method="DM")
    g0 = G[0,:]
    ell2 = 1 / ((g0*g0.T)[0] - (g0*A.T*W*A*g0.T)[0])
    crow = sp.zeros(1,7)
    crow[0,0] = 1
    crow -= g0*A.T*W*H
    return ell2, crow, H.T*W*H

def ratios(Y, center, radius, rho, oracle_state):
    ell2, crow, Q = oracle_state
    Yq = sp.Matrix([[rat(x) for x in row] for row in Y])
    exact_c = crow * Yq
    exact_j = sum((Yq[:,j].T*Q*Yq[:,j])[0] for j in range(24))
    delta2 = sum((rat(center[j])-exact_c[j])**2 for j in range(24))
    b = rat(rho)**2
    c_cost = exact_j + ell2*delta2
    answer = {"J0_over_budget": show(to_mp(exact_j/b)),
              "center_cost_over_budget": show(to_mp(c_cost/b)),
              "exact_center_col0": show(to_mp(exact_c[0]))}
    if radius is not None:
        rm, dm = mp.mpf(float(radius)), mp.sqrt(to_mp(delta2))
        e, j, bm = to_mp(ell2), to_mp(exact_j), to_mp(b)
        sphere_error = abs(j + e*(dm**2+rm**2)-bm) + 2*e*rm*dm
        answer["abstract_sphere_error_over_budget"] = show(sphere_error/bm)
    return answer

records = []
for metric, d in (("common", current.D), ("raw", np.ones(9))):
    name = "A_BT_1e-06"
    F = np.asarray(source[name]["F2"]["matrix_7xk"], float)
    a = np.ones(7)
    state = oracle(F, d)
    ell = mp.sqrt(to_mp(state[0]))
    sol = current.solve_metric(F, a, d)
    center = np.zeros(24)
    center[0] = 1e-6
    rho = 1e-206
    Y = np.tile(center, (7,1))
    out = current.identified(Y, F, a, d, sol, rho)
    r = float(mp.mpf(rho)/ell)
    cost_ratio = state[0] * rat(r)**2 / rat(rho)**2
    assert abs(cost_ratio-1) < sp.Rational(1,10**9)
    assert center[0]+r == center[0]
    high = current.structural_high_precision_geometry(center,F,a,d,sol,rho)
    budget_err = high["mp_state"][-1]
    records.append({"case": "representable_abstract_structural_ball", "branch": name,
                    "metric": metric, "rho_hex": rho.hex(), "radius_hex": r.hex(),
                    "radius": r, "abstract_exact_rational_budget_ratio": show(to_mp(cost_ratio)),
                    "abstract_relative_budget_error": show(abs(to_mp(cost_ratio-1))),
                    "rounded_axis_witness_equals_center": True,
                    "rounded_axis_witness_cost_over_budget": "0",
                    "rounded_axis_witness_absolute_boundary_error_over_budget": "1",
                    "binary64_rho_squared": rho*rho,
                    "current_internal_budget_error_over_true_budget": show(budget_err/mp.mpf(rho)**2),
                    "current_status": out["status"],
                    "current_reason": out["radius_uncertainty"]["reason"]})
    if metric == "raw":
        for rho_hex in ("0x0.0000000000040p-1022", "0x0.00000000007e8p-1022"):
            rho = float.fromhex(rho_hex)
            Y = np.zeros((7,24))
            prior = old04.identified(Y,F,a,d,old04.solve_metric(F,a,d),rho)
            current_out = current.identified(Y,F,a,d,sol,rho)
            r = prior["radius"]
            cost_ratio = state[0]*rat(r)**2/rat(rho)**2
            assert abs(cost_ratio-1) > sp.Rational(1,10**9)
            records.append({"case": "BP05_radius_quantization", "branch": name,
                            "metric": metric, "rho_hex": rho_hex,
                            "old_radius_hex": r.hex(), "old_status": prior["status"],
                            "abstract_exact_rational_budget_ratio": show(to_mp(cost_ratio)),
                            "abstract_relative_budget_error": show(abs(to_mp(cost_ratio-1))),
                            "current_status": current_out["status"]})
        Y = np.zeros((7,24))
        Y[:,0] = 1.
        Y[0,0] += 1e-14
        Y[6,0] -= 1e-14
        rho = float.fromhex("0x1.ba775222664cdp-44")
        prior = old02.identified(Y,F,a,d,old02.solve_metric(F,a,d),rho)
        now = current.identified(Y,F,a,d,sol,rho)
        exact = ratios(Y,prior["center"],prior["radius"],rho,state)
        assert mp.mpf(exact["center_cost_over_budget"]) > 10
        # The best rounded center remains materially inaccurate in this example.
        Yq = sp.Matrix([[rat(x) for x in row] for row in Y])
        nearest_c = np.asarray([float(to_mp(x)) for x in state[1]*Yq])
        exact_j = sum((Yq[:,j].T*state[2]*Yq[:,j])[0] for j in range(24))
        ideal_r = float(mp.sqrt(mp.mpf(rho)**2-to_mp(exact_j))/ell)
        nearest = ratios(Y,nearest_c,ideal_r,rho,state)
        records.append({"case": "BP04_incoherent_center", "branch": name, "metric": metric,
                        "rho_hex":rho.hex(), "old_status":prior["status"],
                        "old_center_hex":float(prior["center"][0]).hex(),
                        "current_status":now["status"], "historical_output":exact,
                        "nearest_binary64_abstract_parameters":nearest})

after = [identity(p) for p in paths]
assert before == after, "input changed during bounded read-only probe"
git = {key: subprocess.check_output(args, cwd=ROOT, text=True).strip() for key,args in (
    ("branch", ["git","branch","--show-current"]),
    ("head", ["git","rev-parse","HEAD"]),
    ("origin", ["git","remote","get-url","origin"]))}
(OUT/"git_status.txt").write_text(subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True))
(OUT/"SOURCE_IDENTITIES.json").write_text(json.dumps({"git":git,"source_files":before,
    "identities_unchanged_during_probe":True,"python":sys.executable},indent=2)+"\n")
(OUT/"exact_checks.json").write_text(json.dumps({"records":records,
    "assertions":"all bounded independent assertions passed; not a candidate admission"},indent=2)+"\n")
print(json.dumps(records,indent=2))
