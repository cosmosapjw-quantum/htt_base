"""R54 results binding and anti-drift guards.

Every number in an R54 document is generated from RESULTS/*.json by scripts/r54/build_r54_contract.py.
These tests fail when
  (a) a committed input or a run script changes without the results being regenerated (MG-13),
  (b) a quoted statistic cannot be recomputed, either with plain numpy or by the run scripts,
  (c) generated documents, DAG, contract, prompt and canonical cards disagree,
  (d) the contract names code, files, equations or evidence that do not exist,
  (e) the mutation receipt is stale, or claim language drifts.
A failing test names the file to regenerate; never edit a generated document by hand.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml
from scipy import stats

from htt.htt.infer import r54_distance_estimators as de
from htt.htt.infer import r54_identifiability as idn
from htt.htt.infer import r54_lcdm_body as lb
from htt.htt.infer import r54_tensor_five_view as fv
from htt.htt.infer import r54_type1_thomson as th

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "docs/research_program/observational_publication_20261015"
R54 = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
RESULT_FILES = ("R54_L1_TYPE1_TE.json", "R54_L5_LOWZ_FRAMES.json", "R54_L05_CF4_EXACT.json")
CF4_SOURCE = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
C_KM_S = 299792.458
METHODS = ("FP", "OTHER", "SN", "TF")
BANNED = ("delve", "crucial", "multifaceted", "nuanced", "landscape", "underscore", "leverag", "facilitat",
          "it is important to note", "interestingly", "in conclusion")


def _json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _module(rel: str, name: str):
    path = ROOT / rel
    for extra in (ROOT / "htt", ROOT / "htt/src", ROOT, path.parent):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generated_text_files() -> list[Path]:
    return sorted(R54.glob("*.md")) + sorted((R54 / "state").glob("*.md")) + [R54 / "LOCAL_AGENT_RESTART_PROMPT.txt", R54 / "LOCAL_AGENT_HANDOFF_UPDATE.txt"]


@pytest.fixture(scope="module")
def builder():
    return _module("scripts/r54/build_r54_contract.py", "r54_builder")


@pytest.fixture(scope="module")
def results():
    return [_json(R54 / "RESULTS" / name) for name in RESULT_FILES]


@pytest.fixture(scope="module")
def cf4():
    """CF4 catalogue quantities rebuilt with plain numpy (no project module)."""
    with np.load(CF4_SOURCE, allow_pickle=False) as z:
        zc, mu, emu, n, meth = z["z_CMB"].copy(), z["dmzp"].copy(), z["e_dmzp"].copy(), z["n_J2000"].copy(), z["method_family"].copy()
    om = 0.3153
    zg = np.linspace(0.0, 0.11, 22001)
    inv_e = 1.0 / np.sqrt(om * (1.0 + zg) ** 3 + 1.0 - om)
    chi = np.interp(zc, zg, np.concatenate([[0.0], np.cumsum(0.5 * (inv_e[1:] + inv_e[:-1]) * np.diff(zg))]))
    e_z = np.sqrt(om * (1.0 + zc) ** 3 + 1.0 - om)
    g = ((1.0 + zc) / (e_z * chi) - 1.0) / C_KM_S
    eta = np.log(C_KM_S * (1.0 + zc) * chi / 10.0 ** ((mu - 25.0) / 5.0))
    tau2 = (math.log(10.0) / 5.0 * emu) ** 2 + (250.0 * g) ** 2
    x, y, w = n.T
    basis = np.column_stack([np.ones(zc.size), x, y, w, (x * x - y * y) / math.sqrt(2.0), (x * x + y * y - 2.0 * w * w) / math.sqrt(6.0),
                             math.sqrt(2.0) * x * y, math.sqrt(2.0) * x * w, math.sqrt(2.0) * y * w])
    return {"z": zc, "n": n, "method": meth, "eta": eta, "g": g, "tau2": tau2, "chi": chi, "basis": basis}


# ----------------------------------------------------------------- (a) inputs
def test_inputs_are_the_committed_ones(results):                                   # MG-13
    for res in results:
        prov = res["provenance"]
        assert _sha(ROOT / prov["script"]) == prov["script_sha256"], f"{prov['script']} changed: re-run it and rebuild the contract"
        for rel, digest in prov["inputs_sha256"].items():
            assert _sha(ROOT / rel) == digest, f"input drift: {rel}"
        assert res["claim_tier"].startswith("C0")
    for rel, digest in _json(R54 / "LOCAL_AGENT_CONTRACT.json")["committed_inputs_sha256"].items():
        assert _sha(ROOT / rel) == digest, f"contract input drift: {rel}"


def test_local_results_bind_their_scripts_and_inputs():
    """R54 local node results: script hash, repository inputs, and absolute data-drive inputs when the drive is mounted; acceptance recorded."""
    local = ("R54_L01_RESULT.json", "R54_L02_RESULT.json", "R54_L03_RESULT.json", "R54_L04_RESULT.json", "R54_L06_JOINT.json", "R54_L07_BENCHMARK.json")
    for path in [R54 / "RESULTS" / name for name in local if (R54 / "RESULTS" / name).is_file()]:
        res = _json(path)
        if "provenance" not in res:
            continue
        prov = res["provenance"]
        assert _sha(ROOT / prov["script"]) == prov["script_sha256"], f"{prov['script']} changed after {path.name}: re-run the node"
        for key, digest in prov["inputs_sha256"].items():
            p = Path(key) if key.startswith("/") else ROOT / key
            if key.startswith("/") and not p.exists():
                continue                                          # data drive not mounted: checked where it is
            if p.exists():
                assert _sha(p) == digest, f"input drift for {path.name}: {key}"
        assert res["claim_tier"].startswith("C0") and res["status"] in ("DONE_SCOPED_C0", "BLOCKED_MISSING_INPUT")
        if res["status"] == "DONE_SCOPED_C0":
            assert res["acceptance"] and all(set(v) >= {"value", "op", "threshold", "pass"} for v in res["acceptance"].values())


# ----------------------------------------------------------------- (b) plain-numpy recomputation
def test_l1_statistics_recomputed_with_plain_numpy(results):
    rec = results[0]["data"]
    with np.load(PUB / "R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz", allow_pickle=False) as z:
        labels = [str(v) for v in z["mode_labels"]]
        d, s = z["d_smica_135_uK"], z["S_ffp10_300_135x135_uK2"]
        j_t, j_ideal, n_mc = z["response_J_135x5_uK"], z["response_J_ideal_135x5_uK"], int(z["n_mc"])
    assert (labels[0], labels[45], labels[90], n_mc) == ("T_2_0", "E_2_0", "B_2_0", 300)
    assert rec["primary_carrier"] == "TE_l2"
    idx = list(range(0, 5)) + list(range(45, 50))
    j = np.zeros((10, 10))
    j[:, :5] = j_t[idx]
    j[5:, 5:] = j_ideal[0:5]                                   # ideal in-basis E response
    si = np.linalg.inv(s[np.ix_(idx, idx)])
    f, t = j.T @ si @ j, j.T @ si @ d[idx]
    est = np.linalg.solve(f, t)
    prim = rec["results"]["primary"]
    # square carrier (p = k = 10): the exact Wishart ratio is 1 and the Wald statistic follows the Hotelling law with n = N - 1
    wald, n_dof = float(t @ est), n_mc - 1
    assert abs(wald - prim["wald_all"]["statistic"]) < 1e-8 and prim["inflation_sd"] == 1.0
    tail = float(stats.f.sf(wald * (n_dof - 10 + 1) / (n_dof * 10), 10, n_dof - 10 + 1))
    assert abs(tail - prim["wald_all"]["p_value"]) < 1e-10 and prim["wald_all"]["law"] == "hotelling_T2(p=10,n=299)"
    assert np.allclose(est[:5], prim["Sigma_T_hat"], rtol=1e-8, atol=1e-16) and np.allclose(est[5:], prim["Sigma_E_hat"], rtol=1e-8, atol=1e-18)
    assert np.allclose(np.sqrt(np.diag(np.linalg.inv(f)))[:5], prim["sd_T"], rtol=1e-8)
    # non-square T-only carrier (p = 45, k = 5): exact finite-MC ratio against the leave-one-out ratio stored by the script
    t_only = rec["t_only_r51_reproduction"]
    exact = math.sqrt(n_dof * (n_dof - 1) / ((n_dof - 45 + 5) * (n_dof - 45 + 5 - 1)))
    assert abs(exact - t_only["inflation_sd_analytic"]) < 1e-12 and abs(np.mean(t_only["loo_sd_over_plugin_sd"]) / exact - 1.0) < 0.01
    b = list(range(90, 95))
    t2 = float(d[b] @ np.linalg.solve(s[np.ix_(b, b)], d[b]))
    assert abs(t2 - rec["null_gates"]["B_l2"]["statistic"]) < 1e-8
    assert rec["B_null_gate"]["pass"] is False and rec["null_gates"]["B_l2"]["p_value"] < 0.01
    # late-time bounds are the functional limits divided by the kernel sensitivities; tau is tiny at z < 0.2, so int K_T dN ~ ln(1 + z)
    sens = {row["z_max"]: row for row in results[0]["history"]["late_time_sensitivity"]}
    for row in rec["late_time_shear_bounds"]["primary"]:
        k = sens[row["z_max"]]
        assert math.isclose(row["constant_sign_bound_from_T"], prim["Sigma_T_frobenius_range_95"]["norm_max"] / k["I_T_constant"], rel_tol=1e-9)
        assert math.isclose(row["sign_changing_rms_bound_from_E"],
                            prim["Sigma_E_frobenius_range_95"]["norm_max"] * k["sign_changing"]["rms_shear_per_unit"] / abs(k["sign_changing"]["Sigma_E_per_unit"]), rel_tol=1e-9)
        assert row["sign_changing_rms_bound_from_T"] == "inf" and abs(k["sign_changing"]["Sigma_T_per_unit"]) < 1e-12
        if row["z_max"] <= 0.2:
            assert 0.0 < math.log1p(row["z_max"]) - k["I_T_constant"] < 1e-3 * math.log1p(row["z_max"])
    sweep = results[0]["history"]["photon_neutrino_stress"]["neutrino_decoupling_initial_condition_sweep"]
    for row in sweep:                                          # T_nu = (4/11)^(1/3) T_CMB k_B (1 + z)
        assert math.isclose(row["T_nu_MeV"], (4.0 / 11.0) ** (1.0 / 3.0) * 2.72548 * 8.617333262e-11 * (1.0 + row["z_init"]), rel_tol=1e-9)


def test_l5_statistics_recomputed_with_plain_numpy(results):
    src = _json(PUB / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/RESULT.json")
    theta, cov = np.asarray(src["theta4x9"], float).ravel(), np.asarray(src["covariance36x36"], float)
    meas = results[1]["cf4"]["analysis"]["MEAS"]
    dip = [9 * w + k for w in range(4) for k in (1, 2, 3)]
    quad = [9 * w + k for w in range(4) for k in (4, 5, 6, 7, 8)]
    both = [9 * w + k for w in range(4) for k in range(1, 9)]

    def chi2(rows):
        return float(theta[rows] @ np.linalg.solve(cov[np.ix_(rows, rows)], theta[rows]))

    assert abs(chi2(dip) - meas["dipole"]["null"]["statistic"]) < 1e-7
    assert abs(chi2(quad) - meas["quadrupole"]["null"]["statistic"]) < 1e-7
    # pole template by hand: dH dipole along +z and the axisymmetric quadrupole about z, which is -e_2 of the STF5 basis
    j = np.zeros((32, 2))
    for w in range(4):
        j[8 * w + 2, 0] = 1.0
        j[8 * w + 4, 1] = -1.0
    ci = np.linalg.inv(cov[np.ix_(both, both)])
    t = j.T @ ci @ theta[both]
    gain = float(t @ np.linalg.solve(j.T @ ci @ j, t))
    assert abs(gain - meas["axis_locking"]["delta_chi2_at_reference_axes"]["equatorial_pole"]) < 1e-6


def test_l05_statistics_recomputed_with_plain_numpy(results, cf4):
    x = results[2]
    car, head = x["log_distance"]["carrier"], x["log_distance"]["headline"]
    theta, cw, cb = np.asarray(car["theta"]), np.asarray(car["covariance_white"]), np.asarray(car["covariance_body"])
    # window multipoles from the catalogue by normal equations (the module uses QR)
    for w, center in enumerate((0.025, 0.04, 0.06, 0.08)):
        wt = np.exp(-0.5 * ((cf4["z"] - center) / 0.012) ** 2) / cf4["tau2"]
        xw = cf4["basis"] * wt[:, None]
        assert np.allclose(np.linalg.solve(xw.T @ cf4["basis"], xw.T @ cf4["eta"]), theta[9 * w:9 * w + 9], rtol=0.0, atol=1e-8)
    cov = cw + cb
    dip = [9 * w + k for w in range(4) for k in (1, 2, 3)]
    quad = [9 * w + k for w in range(4) for k in (4, 5, 6, 7, 8)]
    both = sorted(dip + quad)

    def chi2(rows):
        return float(theta[rows] @ np.linalg.solve(cov[np.ix_(rows, rows)], theta[rows]))

    assert math.isclose(chi2(dip), head["dipole_null_chi2"], rel_tol=1e-8)
    assert math.isclose(chi2(quad), head["quadrupole_null_chi2"], rel_tol=1e-8)
    assert math.isclose(chi2(both), head["joint_null_chi2"], rel_tol=1e-8)
    a = np.tile(np.eye(3), (4, 1))
    ci = np.linalg.inv(cov[np.ix_(dip, dip)])
    a_hat = np.linalg.solve(a.T @ ci @ a, a.T @ ci @ theta[dip])
    assert np.allclose(a_hat, head["A_only"], rtol=1e-7, atol=1e-12)
    assert math.isclose(chi2(dip) - float(a_hat @ (a.T @ ci @ a) @ a_hat), head["chi2_A"], rel_tol=1e-7)
    # cached pair sum: block identity, symmetry, positivity
    rows = x["setup"]["operator_rows"]
    with np.load(R54 / "RESULTS/R54_L05_COSMIC_COV.npz", allow_pickle=False) as z:
        body, labels = z["cosmic_linear"], [str(v) for v in z["labels"]]
    assert labels[rows["log"][0]] == "log:0" and len(labels) == body.shape[0] == max(v[1] for v in rows.values())
    assert np.allclose(body[rows["log"][0]:rows["log"][1], rows["log"][0]:rows["log"][1]], cb, rtol=1e-12, atol=0.0)
    assert np.abs(body - body.T).max() == 0.0 and np.linalg.eigvalsh(body).min() > -1e-10 * np.trace(body)
    # per-method hemisphere steps by normal equations; exact-body error from the cached pair sum
    steps = x["zero_point_split"]["hemisphere_step_by_method"]
    zbin = np.digitize(cf4["z"], [0.02, 0.03, 0.04])
    in_range = (cf4["z"] >= 0.01) & (cf4["z"] < 0.055)
    design = np.column_stack([(zbin == b).astype(float) for b in range(4)] + [np.where(cf4["n"][:, 2] >= 0.0, 1.0, -1.0)])
    for i, m in enumerate(METHODS):
        sel = in_range & (cf4["method"] == m)
        xs, ws = design[sel], 1.0 / cf4["tau2"][sel]
        fisher = (xs * ws[:, None]).T @ xs
        step = float(np.linalg.solve(fisher, (xs * ws[:, None]).T @ cf4["eta"][sel])[4])
        var_white = float(np.linalg.inv(fisher)[4, 4])
        assert abs(step - steps["white"]["per_method"][m]["step"]) < 1e-9
        assert abs(math.sqrt(var_white) - steps["white"]["per_method"][m]["sd"]) < 1e-9
        var_body = float(body[rows["method_step"][0] + i, rows["method_step"][0] + i])
        assert math.isclose(math.sqrt(var_white + var_body), steps["white_plus_exact_body"]["per_method"][m]["sd"], rel_tol=1e-8)
    classes = ("LCDM_BODY_COMPATIBLE", "METHOD_HEMISPHERE_ZERO_POINT_TYPE", "UNRESOLVED_POLE_LOCKED", "EXCESS_NOT_POLE_LOCKED")
    assert x["decision"]["class"] in classes
    # inner and outer window nulls from the stored carrier
    for tag, wins in (("inner_windows_z0.025_z0.04", (0, 1)), ("outer_windows_z0.06_z0.08", (2, 3))):
        sub = sorted(9 * w + k for w in wins for k in range(1, 9))
        got = x["log_distance"]["window_subsets"][tag]["joint"]
        assert math.isclose(chi2(sub), got["chi2"], rel_tol=1e-8) and got["dof"] == 16
        assert math.isclose(float(stats.chi2.sf(got["chi2"], 16)), got["p_value"], rel_tol=1e-9)
    # hemisphere-step scan: the pole row of the restricted pair sum equals the full pair sum; scan tails are ordered
    scan = x["zero_point_split"]["hemisphere_step_scan"]
    ref = steps["white_plus_exact_body"]
    assert abs(scan["pole"]["common_step"] - ref["common_step"]) < 1e-9 and abs(scan["pole"]["sd"] - ref["common_step_sd"]) < 1e-9
    with np.load(R54 / "RESULTS/R54_L05_STEP_SCAN_COV.npz", allow_pickle=False) as z:
        scan_body, axes = z["body"], z["axes_icrs"]
    m0 = rows["method_step"][0]
    assert scan_body.shape == (4 * scan["n_axes"],) * 2 and np.allclose(axes[0], [0.0, 0.0, 1.0], atol=1e-12)
    assert np.allclose(scan_body[:4, :4], body[m0:m0 + 4, m0:m0 + 4], rtol=1e-8, atol=0.0)      # two separate pair-sum runs (same kernel and positions; not an independent check) agree
    tails = scan["tails"]
    assert tails["pole_single_axis_two_sided"] < tails["scan_max_at_least_pole_value"] <= 1.0
    assert tails["scan_max_at_least_observed_max"] <= tails["scan_max_at_least_pole_value"] + 1e-12
    assert math.isclose(tails["pole_single_axis_two_sided"], float(2.0 * stats.norm.sf(abs(scan["pole"]["z_score"]))), rel_tol=1e-9)
    # classification per nuisance model follows the coded rule from the stored tails; a robust class needs all three to agree
    dec = x["decision"]

    def classify(joint_p, removed, tail):
        if joint_p >= 0.01:
            return classes[0]
        if removed:
            return classes[1]
        return classes[2] if tail < 0.01 else classes[3]

    removed = dec["flags"]["removed_by_method_hemisphere_split"]
    for name in ("pooled", "method_monopoles_marginalised", "method_x_hemisphere_steps_marginalised"):
        rm = removed and name != "method_x_hemisphere_steps_marginalised"
        assert dec["class_by_nuisance_variant"][name] == classify(dec["joint_null_p_by_nuisance_variant"][name], rm, dec["locking_tail_by_nuisance_variant"][name])
    agree = len(set(dec["class_by_nuisance_variant"].values())) == 1
    assert dec["robust_class"] == (dec["class"] if agree else "DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL")
    for op in ("pooled", "method_monopoles_marginalised"):       # size of the pole_locked flag without injection, 1000 draws
        assert x["injections"][op]["cases"]["none"]["fraction_pole_locked_flag"] < 0.03
    assert x["five_views"]["F"]["status"] == "UNAVAILABLE" and results[1]["five_views"]["F"]["status"] == "UNAVAILABLE"


def test_committed_numbers_are_reproduced_by_the_run_scripts(builder, results):
    l1, _, l05 = results
    cmb = _module("scripts/r54/run_r54_cmb_type1.py", "r54_run_cmb")
    low = _module("scripts/r54/run_r54_lowz_frames.py", "r54_run_lowz")
    exact = _module("scripts/r54/run_r54_cf4_exact.py", "r54_run_cf4")
    exact.CACHE_WRITE = False                                    # a stale or missing pair-sum cache fails here; it is never rewritten by pytest
    tab = np.loadtxt(low.PK, delimiter=",", skiprows=1)
    got = builder.numbers({"history": l1["history"], "data": cmb.clean(cmb.data_block(l1["history"]))},
                          {"cf4": low.clean(low.cf4_block(tab[:, 0], tab[:, 1])), "count_dipoles": low.clean(low.counts_block())},
                          exact.compute())
    want = builder.numbers()
    same_numpy = np.__version__ == l05["provenance"]["numpy"]
    assert set(got) == set(want)
    for key, value in want.items():
        if key in builder.MONTE_CARLO_KEYS and not same_numpy:
            continue                                             # pseudo-random streams are only compared on the recorded numpy version
        if isinstance(value, (str, bool)):
            assert got[key] == value, key
        else:
            assert math.isclose(float(got[key]), float(value), rel_tol=1e-6, abs_tol=1e-12), (key, got[key], value)


@pytest.mark.skipif(os.environ.get("R54_SLOW") != "1", reason="set R54_SLOW=1 to recompute one pair-sum element independently (several minutes)")
def test_pair_sum_element_recomputed_independently(results, cf4):
    """Variance of the FP hemisphere step under the linear LCDM body, with an independent kernel table and 3-vector geometry."""
    rows = results[2]["setup"]["operator_rows"]
    tab = np.loadtxt(ROOT / "tests/fixtures/r54/planck18_linear_pk_z0.csv", delimiter=",", skiprows=1)
    good = tab[:, 1] > 0
    lk = np.linspace(math.log(tab[good, 0][0]), math.log(tab[good, 0][-1]), 150000)
    kf = np.exp(lk)
    wk = np.exp(np.interp(lk, np.log(tab[good, 0]), np.log(tab[good, 1]))) * kf * (lk[1] - lk[0])
    wk[[0, -1]] *= 0.5
    r = C_KM_S / 67.36 * cf4["chi"]
    rg = np.linspace(0.0, 2.0 * r.max() * 1.001, 3001)
    norm = (0.3153 ** 0.55 * 67.36) ** 2 / (2.0 * math.pi ** 2)
    perp, par = np.empty_like(rg), np.empty_like(rg)
    for a in range(0, rg.size, 50):
        xk = np.outer(rg[a:a + 50], kf)
        xs = np.where(xk < 1e-3, 1.0, xk)
        j0 = np.where(xk < 1e-3, 1.0 - xk * xk / 6.0, np.sin(xs) / xs)
        j1x = np.where(xk < 1e-3, 1.0 / 3.0 - xk * xk / 30.0, (np.sin(xs) - xs * np.cos(xs)) / xs ** 3)
        perp[a:a + 50], par[a:a + 50] = norm * (j1x @ wk), norm * ((j0 - 2.0 * j1x) @ wk)
    zbin = np.digitize(cf4["z"], [0.02, 0.03, 0.04])
    sel = (cf4["z"] >= 0.01) & (cf4["z"] < 0.055) & (cf4["method"] == "FP")
    design = np.column_stack([(zbin == b).astype(float) for b in range(4)] + [np.where(cf4["n"][:, 2] >= 0.0, 1.0, -1.0)])
    wt = np.where(sel, 1.0 / cf4["tau2"], 0.0)
    op = np.linalg.solve((design * wt[:, None]).T @ design, (design * wt[:, None]).T)[4] * cf4["g"]
    pos, nz = r[:, None] * cf4["n"], np.flatnonzero(op)
    total = 0.0
    for a in range(0, nz.size, 300):
        i = nz[a:a + 300]
        dx = pos[i][:, None, :] - pos[nz][None, :, :]
        rij = np.linalg.norm(dx, axis=2)
        rhat = dx / np.where(rij > 0, rij, 1.0)[:, :, None]
        pp, pl = np.interp(rij, rg, perp), np.interp(rij, rg, par)
        cuu = pp * (cf4["n"][i] @ cf4["n"][nz].T) + (pl - pp) * np.einsum("ia,ija->ij", cf4["n"][i], rhat) * np.einsum("ja,ija->ij", cf4["n"][nz], rhat)
        total += float(op[i] @ cuu @ op[nz])
    with np.load(R54 / "RESULTS/R54_L05_COSMIC_COV.npz", allow_pickle=False) as z:
        cached = float(z["cosmic_linear"][rows["method_step"][0], rows["method_step"][0]])
    assert math.isclose(total, cached, rel_tol=2e-4), (total, cached)


# ----------------------------------------------------------------- (c) documents, DAG, contract, prompt, cards
def test_generated_documents_match_the_builder(builder):
    n = builder.numbers()
    hyps = builder.hypotheses(n)
    texts = {"R54_REPORT_KO.md": builder.report_ko(n), "THEORY_LOOPS.md": builder.theory_md(n),
             "LOCAL_AGENT_RESTART_PROMPT.txt": builder.prompt_txt(n), "README.md": builder.readme_md(),
             "LOCAL_AGENT_HANDOFF_UPDATE.txt": builder.handoff_txt(n)}
    texts.update({f"state/{name}": text for name, text in builder.state_files(n, hyps).items()})
    for rel, text in texts.items():
        assert (R54 / rel).read_text(encoding="utf-8") == text, f"{rel} is stale or hand-edited: run scripts/r54/build_r54_contract.py build"
    docs = {"RESEARCH_DAG.json": builder.dag_doc(n), "LOCAL_AGENT_CONTRACT.json": builder.contract_doc(n), "MUTATION_GATES.json": builder.gates_doc(),
            "SELF_AUDIT_PROTOCOL.json": builder.self_audit_doc(), "ADVERSARIAL_BENCHMARK_SPEC.json": builder.benchmark_doc(n),
            "PR4_BYPASS_CONTRACT.json": builder.pr4_doc(n), "HISTORY_AUDIT.json": builder.history_doc(), "HANDOFF_UPDATE.json": builder.handoff_doc(n)}
    for rel, doc in docs.items():
        assert _json(R54 / rel) == json.loads(json.dumps(doc)), f"{rel} is stale or hand-edited: run scripts/r54/build_r54_contract.py build"


def test_dag_contract_and_prompt_are_consistent():
    dag, contract, gates = (_json(R54 / name) for name in ("RESEARCH_DAG.json", "LOCAL_AGENT_CONTRACT.json", "MUTATION_GATES.json"))
    nodes = {node["id"]: node for node in contract["nodes"]}
    cloud = {node["id"] for node in dag["cloud_nodes"]}
    assert [node["id"] for node in dag["local_nodes"]] == list(nodes) and not cloud & set(nodes)
    assert sorted(dag["execution_order_local"]) == sorted(nodes)
    seen = set(cloud)
    for nid in dag["execution_order_local"]:                    # the declared order is a topological order
        assert set(nodes[nid]["depends"]) <= seen, f"{nid} is scheduled before its dependencies"
        seen.add(nid)
    carded = [nid for ids in dag["canonical_cards"].values() for nid in ids]
    assert sorted(carded) == sorted(cloud | set(nodes))
    local_gate_ids = {g["id"] for g in gates["local_gates"]}
    assert {g["node"] for g in gates["local_gates"]} <= set(nodes)
    prompt = (R54 / "LOCAL_AGENT_RESTART_PROMPT.txt").read_text(encoding="utf-8")
    for nid, node in nodes.items():
        assert nid in dag["canonical_cards"][node["card"]] and nid in prompt
        for key in ("inputs", "steps", "outputs", "acceptance", "kill"):
            assert node[key], f"{nid} lacks {key}"
        assert [s.split(".")[0] for s in node["steps"]] == [str(i + 1) for i in range(len(node["steps"]))], f"{nid} steps are not numbered 1..n"
        assert set(node["mutation_gates"]) <= local_gate_ids
        for check in node.get("decision_checks", []):
            assert set(check) == {"check", "if_true", "if_false"}
        for out in node["outputs"]:
            assert out["path"].startswith(dag["file_allowlist_local"][0])
    for name in contract["read_order"]:
        assert (R54 / name).exists(), name
    for node in dag["cloud_nodes"]:
        assert node["status"] == "DONE_SCOPED_C0"
        for out in node["outputs"]:
            assert (ROOT / out).exists() or (R54 / out).exists(), f"cloud output missing: {out}"


def test_contract_names_only_existing_code_files_and_equations():
    contract = _json(R54 / "LOCAL_AGENT_CONTRACT.json")
    modules = {"r54_type1_thomson": th, "r54_lcdm_body": lb, "r54_tensor_five_view": fv, "r54_distance_estimators": de, "r54_identifiability": idn}
    for name, entries in contract["module_api"].items():
        target = modules[name] if name in modules else _module(name, "r54_api_" + Path(name).stem)
        for entry in entries:
            assert hasattr(target, entry.split("(")[0]), f"{name}: {entry} is named in the contract but does not exist"
    for rel in contract["committed_inputs_sha256"]:
        assert (ROOT / rel).is_file(), rel
    for node in contract["nodes"]:
        for item in node["inputs"]:
            path = item["path"]
            if path.startswith(("docs/", "tests/", "scripts/", "htt/")) and " " not in path and ":" not in path:
                assert (ROOT / path).exists(), f"{node['id']} names a missing committed input: {path}"
    text = json.dumps(contract["nodes"]) + (R54 / "THEORY_LOOPS.md").read_text(encoding="utf-8") + (R54 / "R54_REPORT_KO.md").read_text(encoding="utf-8")
    for eq in set(re.findall(r"R54-EQ-\d+", text)):
        assert eq in contract["equations"], f"{eq} is cited but not in the equation register"
    for token in ("scripts/r51/run_r51_pr3_lowell.py", "scripts/r53/run_r53_benchmark.py", "data/camb_ref_planck2018.npz",
                  "docs/research_program/cf4_schur_loop8_20261015/inputs/loop6_result.json",
                  "docs/research_program/observational_publication_20261015/HTT_SIX_LOOP_INTEGRATED_20261109/L2_real_dipoles.py"):
        assert (ROOT / token).exists(), f"path named in the node steps is missing: {token}"


def test_canonical_cards_are_registered_and_mirrored():
    backlog = yaml.safe_load((ROOT / "docs/codex_handoff/pr_backlog.yaml").read_text(encoding="utf-8"))
    status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text(encoding="utf-8"))
    cards = list(_json(R54 / "RESEARCH_DAG.json")["canonical_cards"])
    by_id = {row["id"]: row for row in backlog["prs"]}
    for prev, card in zip(["PR-R53-OBSERVED-CONVERGENCE"] + cards[:-1], cards):
        assert card in by_id and card in backlog["policy"]["topological_order"] and card in backlog["policy"]["strict_extension_cards"]
        assert by_id[card]["depends"] == [prev] and by_id[card]["claim_tier_ceiling"] == "C0" and by_id[card]["user_authorized"] is True
        done, waiting = card in status["completed"], card in status["pending"]
        assert done != waiting, f"{card} must be in exactly one of completed or pending"
        assert not done or prev in status["completed"], f"{card} is complete before {prev}"
    assert cards[0] in status["completed"]
    for name in ("pr_backlog.yaml", "pr_backlog.json", "pr_status.yaml"):
        assert (ROOT / "docs/codex_handoff" / name).read_bytes() == (ROOT / "machine_readable" / name).read_bytes(), f"mirror out of sync: {name}"


# ----------------------------------------------------------------- (d, e) receipts, language, evidence
def test_mutation_receipt_is_current_and_complete(builder):
    gates, receipt = _json(R54 / "MUTATION_GATES.json"), _json(R54 / "MUTATION_GATE_RECEIPT.json")
    implemented = {g["id"] for g in gates["cloud_gates"] if g["id"] != "MG-13"} | {g["id"] for g in gates["local_gates"] if g["status"] == "IMPLEMENTED"}
    assert receipt["all_killed"] is True and receipt["unmutated_suite_exit_code"] == 0
    assert {r["id"] for r in receipt["gates"]} == implemented and all(r["status"] == "KILLED" for r in receipt["gates"])
    assert set(receipt["sources_sha256"]) == set(builder.RECEIPT_SOURCES)
    for rel, digest in receipt["sources_sha256"].items():
        assert _sha(ROOT / rel) == digest, f"{rel} changed after the receipt: run scripts/r54/build_r54_contract.py mutation-receipt"


def test_language_and_claim_guards():
    forbidden = [p.lower() for p in _json(R54 / "LOCAL_AGENT_CONTRACT.json")["conventions"]["forbidden_phrases_in_reports"]]
    for path in _generated_text_files():
        text = path.read_text(encoding="utf-8").lower()
        for phrase in list(BANNED) + forbidden:
            assert phrase not in text, f"{path.name} contains '{phrase}'"
    prompt = (R54 / "LOCAL_AGENT_RESTART_PROMPT.txt").read_text(encoding="utf-8")
    for required in ("No downloads", "PR4", "never merge to main", "push without force", "STOP CONDITION", "decision_checks"):
        assert required in prompt, f"prompt lost the rule: {required}"


def test_evidence_ids_resolve_and_keep_their_verification_status(builder):
    rows = builder.EVIDENCE_ROWS
    known = {row["id"] for row in rows}
    assert len(known) == len(rows) and {row["verification"] for row in rows} <= {builder.V, builder.P, builder.M}
    text = "".join(path.read_text(encoding="utf-8") for path in _generated_text_files())
    text += (R54 / "state/HYPOTHESES.json").read_text(encoding="utf-8") + (R54 / "ADVERSARIAL_BENCHMARK_SPEC.json").read_text(encoding="utf-8")
    for token in set(re.findall(r"\bE\d{2}\b", text)):
        assert token in known, f"evidence id {token} is cited but not in the ledger"
    hyps = {h["id"]: h for h in _json(R54 / "state/HYPOTHESES.json")["hypotheses"]}
    l07 = R54 / "RESULTS/R54_L07_BENCHMARK.json"
    for hid in ("H-L1b", "H-L5g"):                               # novelty stays flagged until the literature check of R54-L07, then comes from it
        if l07.is_file():
            assert hyps[hid]["dimensions"]["novelty"].startswith(_json(l07)["novelty_checks"][hid]["novelty"])
        else:
            assert "UNVERIFIED" in hyps[hid]["dimensions"]["novelty"] or "R54-L07" in hyps[hid]["dimensions"]["novelty"]
    assert {h["decision"] for h in hyps.values()} <= {"PROMOTE", "HOLD", "REJECT", "REOPEN"}
    # decisions fixed by the independent review: no claim in either direction on pole locking, excess or common mode
    local = builder.local_hypothesis_decisions()               # decisions fixed by the decision checks of executed local nodes
    for hid in ("H-L5c", "H-L5a", "H-L5g", "H-L2a", "H-L4a", "H-L6b"):
        assert hyps[hid]["decision"] == local.get(hid, {"decision": "HOLD"})["decision"], hid
    for hid in ("H-C2", "H-L3c", "H-L5e", "H-L1c", "H-L1d"):
        assert hyps[hid]["decision"] == "REJECT", hid
    for hid in ("H-C1", "H-L1a", "H-L3a", "H-L3b"):               # promoted without a novelty claim
        assert hyps[hid]["decision"] == "PROMOTE" and hyps[hid]["dimensions"]["novelty"].startswith("NONE claimed"), hid


def test_independent_review_record_is_complete_and_resolved(builder):
    rec = _json(R54 / "INDEPENDENT_REVIEW.json")
    nodes = {n["id"] for n in _json(R54 / "LOCAL_AGENT_CONTRACT.json")["nodes"]}
    contract = _json(R54 / "LOCAL_AGENT_CONTRACT.json")
    assert len(rec["reviewers"]) >= 1 and {r["independent_of_author"] for r in rec["reviewers"]} == {True}
    # a review that did not report is never counted as a review: it must be handed over explicitly
    pending = contract["pending_independent_review"]
    read = {rel for reviewer in rec["reviewers"] for rel in reviewer.get("files", [])}
    assert all((ROOT / rel).is_file() for rel in read), "a reviewer lists a file that does not exist"
    assert pending["scope"] == builder.REVIEW_SCOPE and all((ROOT / rel).is_file() for rel in pending["scope"])
    assert not set(pending["uncovered"]) & read                          # a file that a recorded reviewer lists is covered
    for rel in builder.REVIEW_SCOPE_ADDED:                               # a file added after the diff review counts only if a reviewer lists it
        assert (rel in pending["uncovered"]) is (rel not in read), rel
    if not rec["incomplete_reviews"]:                                    # the recorded diff review covers the scope of the start commit as a whole
        assert set(pending["uncovered"]) <= set(builder.REVIEW_SCOPE_ADDED)
    assert pending["status"] == ("PENDING_LOCAL" if rec["incomplete_reviews"] or pending["uncovered"] else "NONE")
    for item in rec["incomplete_reviews"]:
        assert item["status"] == "INTERRUPTED" and item["reason"] and "findings" not in item and "verdict" not in item
    if rec["incomplete_reviews"]:
        assert all((ROOT / rel).is_file() for rel in pending["scope"])
        assert "interrupted" in (R54 / "LOCAL_AGENT_RESTART_PROMPT.txt").read_text(encoding="utf-8")
    seen = set()
    for reviewer in rec["reviewers"]:
        assert reviewer["verdict"] in ("ACCEPT", "ACCEPT_WITH_REQUIRED_CHANGES", "REJECT")
        assert reviewer["findings"] or reviewer.get("checks_performed"), "a review records its findings or, when it has none, the checks it ran; never an invented finding"
        for f in reviewer["findings"]:
            assert f["id"] not in seen and f["severity"] in ("critical", "major", "minor") and f["summary"] and f["resolution"]
            seen.add(f["id"])
            assert f["resolution_status"] in ("FIXED", "DEFERRED", "DECLINED")
            if f["resolution_status"] == "DEFERRED":
                assert f["deferred_to"] in nodes, f["id"]
            if f["severity"] == "critical":
                assert f["resolution_status"] == "FIXED", f"critical finding {f['id']} is not fixed"


def test_withdrawn_statements_do_not_reappear():
    withdrawn = ("no pole-specific locking", "singles out no axis", "사전 규칙", "locking came from the estimator bias", "(met)")
    for path in _generated_text_files() + [R54 / "state/HYPOTHESES.json", R54 / "ADVERSARIAL_BENCHMARK_SPEC.json", R54 / "HISTORY_AUDIT.json",
                                           ROOT / "docs/codex_handoff/pr_status.yaml"]:
        text = path.read_text(encoding="utf-8")
        for phrase in withdrawn:
            assert phrase not in text, f"{path.name} repeats a withdrawn statement: '{phrase}'"
    theory = (R54 / "THEORY_LOOPS.md").read_text(encoding="utf-8")
    assert "## Forking-path register" in theory and theory.count("| FP-") >= 10


def test_theorems_document_is_bound_to_checks_and_claims_no_unverified_novelty():
    text = (R54 / "THEOREMS.md").read_text(encoding="utf-8")
    checks = (ROOT / "tests/r54/test_r54_theorems.py").read_text(encoding="utf-8") + (ROOT / "tests/r54/test_r54_modules.py").read_text(encoding="utf-8")
    for tid, prefix in (("T1", "test_t1_"), ("T2", "test_t2_"), ("T3", "test_t3_"), ("T4", "test_eq20_"), ("T5", "test_t5_"), ("T6", "test_t6_"),
                        ("T7", "test_t7"), ("T8", "test_t8_"), ("T9", "test_t9_"), ("L1", "test_l1_"), ("L2", "test_eq06_")):
        assert f"### {tid}." in text and f"def {prefix}" in checks, f"{tid} lacks a statement or an executable check"
    pending = _json(R54 / "LOCAL_AGENT_CONTRACT.json")["pending_independent_review"]
    if any(rel.endswith("THEOREMS.md") for rel in pending["uncovered"]):  # flagged as unreviewed until a recorded review lists the file (R54-A1)
        assert "not yet read by an independent" in text
    else:
        assert "not yet read by an independent" not in text and re.search(r"^Independent review: .*\d{4}-\d{2}-\d{2}", text, re.M)
    assert not re.search(r"\b\d+\.\d+e[-+]\d+\b", text), "THEOREMS.md must not carry result numbers"
    hyps = {h["id"]: h for h in _json(R54 / "state/HYPOTHESES.json")["hypotheses"]}
    for hid in ("H-T1", "H-T2", "H-T7", "H-T9"):
        assert hyps[hid]["decision"] == "PROMOTE" and ("NONE claimed" in hyps[hid]["dimensions"]["novelty"] or hyps[hid]["dimensions"]["novelty"].startswith("LOW"))
    attribution = R54 / "RESULTS/R54_A2_ATTRIBUTION.json"                  # written by addendum task R54-A2
    for hid in ("H-T6", "H-T8"):                                         # the two statements with a possible claim stay flagged until that task
        novelty = hyps[hid]["dimensions"]["novelty"]
        if attribution.is_file():
            assert novelty.startswith(_json(attribution)["novelty_checks"][hid]["novelty"]), f"{hid}: the novelty field is the text recorded by R54-A2"
        else:
            assert hyps[hid]["decision"] == "PROMOTE" and "UNVERIFIED" in novelty, hid
    if attribution.is_file():
        rows = {row["id"]: row for row in _json(R54 / "state/HYPOTHESES.json")["evidence"]}
        for eid, check in _json(attribution)["evidence_verification"].items():
            assert (rows[eid]["verification"].startswith("VERIFIED")) is (check["status"] == "VERIFIED"), f"{eid}: the ledger status differs from the R54-A2 record"
    scope = pending["scope"]
    assert any(rel.endswith("THEOREMS.md") for rel in scope) and any(rel.endswith("r54_identifiability.py") for rel in scope)


# ----------------------------------------------------------------- theorem addendum after the programme stop
def test_handoff_update_states_only_facts(builder):
    doc, contract = _json(R54 / "HANDOFF_UPDATE.json"), _json(R54 / "LOCAL_AGENT_CONTRACT.json")
    text = (R54 / "LOCAL_AGENT_HANDOFF_UPDATE.txt").read_text(encoding="utf-8")
    assert all((ROOT / rel).is_file() for rel in doc["delta"]["added"]) and all((ROOT / rel).exists() for rel in doc["delta"]["untouched"])
    assert doc["delta"]["executed_results_changed"] == doc["delta"]["node_steps_changed"] == doc["delta"]["decisions_changed"] == []
    assert not set(doc["delta"]["added"]) & set(doc["delta"]["untouched"])
    present = {"evidence": [row["id"] for row in builder.EVIDENCE_ROWS], "gates": [g[0] for g in builder.implemented_gates()] + ["MG-13"],
               "hypotheses": [h["id"] for h in _json(R54 / "state/HYPOTHESES.json")["hypotheses"]],
               "cloud_nodes": [node["id"] for node in _json(R54 / "RESEARCH_DAG.json")["cloud_nodes"]]}
    for kind, ids in present.items():
        assert len(ids) == len(set(ids)), f"duplicate {kind} id: {sorted(i for i in set(ids) if ids.count(i) > 1)}"
        assert set(doc["delta"]["reserved_ids"][kind]) <= set(ids), f"{kind} ids of the update are missing: {sorted(set(doc['delta']['reserved_ids'][kind]) - set(ids))}"
    for token in (builder.HANDOFF_FETCH, builder.HANDOFF_APPLY, builder.HANDOFF_FINISH, builder.HANDOFF_COMMIT, builder.HANDOFF_PUSH, builder.RESERVED_TEXT, builder.LOCAL_HEAD[:8],
                  builder.CLOUD_UNVERIFIED, "HANDOFF OK", "never to main", "No downloads", "no force", "does not reopen the programme", "theorem_usage"):
        assert token in text, f"the handoff text lost: {token}"
    assert all(f"RESULT: {name}" in text for name in builder.HANDOFF_RESULTS) and all(task["id"] in text for task in doc["addendum_tasks"])
    assert doc["local_nodes"] == {node["id"]: builder.node_status(node["id"]) for node in contract["nodes"]}     # the state of the local nodes is read, not typed
    assert {row["kind"] for row in doc["VALIDATION_MATRIX"]} >= {"software", "scientific", "numerical", "reproducibility"}
    for case in doc["SCIENTIFIC_CONTRACT"]["reference_cases"] + doc["cloud_verification"]["not_verifiable_on_the_cloud_machine"]:
        rel, name = case.split("::")
        assert f"def {name}(" in (ROOT / rel).read_text(encoding="utf-8"), f"named test does not exist: {case}"
    assert doc["review"]["uncovered"] == contract["pending_independent_review"]["uncovered"]
    assert all(q["owner"] and q["default_if_unanswered"] for q in doc["open_questions"])
    assert all(set(task["needs"]) <= {t["id"] for t in doc["addendum_tasks"]} for task in doc["addendum_tasks"])
    assert not re.search(r"\b\d+ (passed|skipped|failed)\b", text + json.dumps(doc)), "test counts are never typed into the handoff"
    final = (R54 / "FINAL_DECISION_R57.md").read_text(encoding="utf-8")
    assert "The programme stops here" in final and "R54-THM" not in final                 # the update leaves the manuscript decision as the local session wrote it


def test_theorem_usage_is_bound_to_the_theorems_and_changes_no_node(builder):
    contract = _json(R54 / "LOCAL_AGENT_CONTRACT.json")
    theorems = (R54 / "THEOREMS.md").read_text(encoding="utf-8")
    usage = contract["theorem_usage"]
    assert usage["proofs_independently_reviewed"] is (not any(rel.endswith("THEOREMS.md") for rel in contract["pending_independent_review"]["uncovered"]))
    assert all(f"### {rule['theorem']}." in theorems and rule["rule"] for rule in usage["rules"])
    for node in contract["nodes"]:                                                       # executed nodes carry no step that was added after they ran
        assert "THEOREMS.md" not in " ".join(node["steps"]) and "H-T" not in " ".join(node["steps"]), node["id"]
    prompt = (R54 / "LOCAL_AGENT_RESTART_PROMPT.txt").read_text(encoding="utf-8")
    for token in ("theorem_usage", "LOCAL_AGENT_HANDOFF_UPDATE.txt", "R54-A1"):
        assert token in prompt, f"prompt lost: {token}"



def test_a2_attribution_is_bound_to_its_script_and_covers_the_rows_of_the_task():
    """Addendum task R54-A2: the record is written by its script and checks exactly the rows and hypotheses that the task names."""
    path = R54 / "RESULTS/R54_A2_ATTRIBUTION.json"
    if not path.is_file():
        pytest.skip("R54-A2 not executed")
    rec = _json(path)
    script = ROOT / rec["provenance"]["script"]
    assert hashlib.sha256(script.read_bytes()).hexdigest() == rec["provenance"]["script_sha256"], "R54-A2 record is stale; re-run its script"
    assert set(rec["novelty_checks"]) == {"H-T6", "H-T8"}
    assert set(rec["evidence_verification"]) == {"E51", "E54", "E63", "E64", "E65", "E66", "E67", "E68", "E69"} == set(rec["rows_checked"])
    for hid, chk in rec["novelty_checks"].items():
        assert chk["searches"] and chk["nearest_prior_art"] and "searched" in chk["novelty"], hid
    assert {c["status"] for c in rec["evidence_verification"].values()} <= {"VERIFIED", "IDENTIFIER_ONLY", "NOT_FOUND"}
