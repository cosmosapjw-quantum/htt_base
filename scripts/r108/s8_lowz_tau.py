"""R108 lane s8 step 2: Thomson depth tau(0 -> 4) of the post-REI continuation for every R106 REI case.

Purpose
  rei_bianchi stops at mean z = 4.  Below z = 4 the R107 module
  htt/bass/recombination/rei_lowz_continuation.py continues x_e from the donor value at z = 4 to
  1 + 2 f_He at z = 0 (DonorMatchedContinuation, HeII timing z_HeII a declared sensitivity parameter)
  and integrates tau = c sigma_T n_H0 int_0^4 (1+z)^2 x_e(z) / H(z) dz (tau_flrw).  This script
    1. recomputes the R107 TF8 donor-matched band (x_e(4) = 1.08339435, z_HeII = 3.0, 3.5, 3.9) with the
       R107 test constants, and compares with the 7-digit TF8 values;
    2. for each of the five R106 REI cases reads the case's own z = 4 restart checkpoint
       (AXBI_CHECKPOINT_V2), forms x_e(4) = x_HII + f_He (x_HeII + 2 x_HeIII) with n_H0, n_He0 of the
       native driver (replay.json of the rerun), takes the cosmology from the solver configuration
       (SCENARIO_LOCK.json at rei_bianchi 56dc609e, cross-checked with the Driver::new literals) and
       evaluates tau(0 -> 4) with the module for each z_HeII;
    3. states whether each case lies inside the donor band, and explains any difference exactly by the
       affine dependence of tau on x_e(4) (tau = A + B x_e(4)) and the n_H0 / f_He normalisation;
    4. evaluates the shear term of the locked H law, H = hypot(H_FLRW, s), s = q_ref H_FLRW(a_ref)(a_ref/a)^3,
       which the module cannot take (FlrwBackground is flat FLRW only): independent integrand, labelled an
       extension outside the locked domain (sensitivity only);
    5. independent units check of the tau integrator: astropy CODATA-2018 constants and astropy Mpc/km
       conversions with a hand-written integrand (scipy quad, same tolerance) and a Gauss-Legendre rule.

Inputs: rerun directory of scripts/r106/rei_restart_replay.py (replay/<case>/replay.json,
  REI_RESTART_REPLAY.json, native trees), the rei_bianchi git object store (read-only `git show`).
Output: docs/.../R108_LOS_ATLAS_DATA_20261124/REI/S8_LOWZ_TAU.json.
Units: tau dimensionless; n in cm^-3 (comoving, a = 1); H in s^-1; z mean redshift.
Claim class: conditional closure (donor-matched continuation, HeII timing declared), not an REI
  computation below z = 4; no physical attribution.  No randomness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HTT_BASE = Path(__file__).resolve().parents[2]
for p in (HTT_BASE, HTT_BASE / "htt", HTT_BASE / "htt/src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scipy.integrate import quad  # noqa: E402

from bass.recombination import rei_lowz_continuation as lowz  # noqa: E402
from bass.recombination.rei_lowz_continuation import (  # noqa: E402
    DonorMatchedContinuation, FlrwBackground, tau_flrw)

REI_REPO = Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi")
REI_COMMIT = "56dc609ea9b801c88d3364aed3eee140b3a20d46"
LOCK_REL = "research/axbi_goal_20261014/scenario/SCENARIO_LOCK.json"
DEFAULT_RERUN = Path.home() / "Downloads/htt_r108/s8/replay_rerun"
DEFAULT_OUT = HTT_BASE / ("docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/"
                          "REI/S8_LOWZ_TAU.json")
R107_TEST = HTT_BASE / "htt/bass/recombination/test_rei_lowz_continuation.py"
R107_TF8 = HTT_BASE / ("docs/research_program/observational_publication_20261015/R107_CLOUD_SOLVER_DATA_THEORY_20261124/"
                       "THEORY_FOUNDATIONS.md")
# R107 TF8 donor value and quoted depths (THEORY_FOUNDATIONS.md TF8, lines 132-135); recomputed below.
TF8_DONOR_XE4 = 1.08339435
TF8_QUOTED = {3.0: 0.0221961, 3.5: 0.0224021, 3.9: 0.0225124}
Z_HEII = (3.0, 3.5, 3.9)
Z_MATCH = 4.0
CASES = ("ZERO", "SHEAR_HALF_PLUS", "SHEAR_HALF_MINUS", "SHEAR_PLUS", "SHEAR_MINUS")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def r107_test_constants() -> dict:
    """N_H0, F_HE and BG of the R107 test module, read from its source text (fails closed if they move)."""
    text = R107_TEST.read_text()
    out = {}
    for name, pat in (("N_H0", r"^N_H0 = ([0-9.eE+-]+)$"), ("F_HE", r"^F_HE = ([0-9.eE+-]+)$")):
        m = re.search(pat, text, re.M)
        if m is None:
            raise ValueError(f"{name} not found in {R107_TEST}")
        out[name] = float(m.group(1))
    m = re.search(r"^BG = FlrwBackground\(([0-9.]+), ([0-9.]+), ([0-9.]+)\)$", text, re.M)
    if m is None:
        raise ValueError("BG not found in R107 test")
    out["BG"] = tuple(float(x) for x in m.groups())
    rel = R107_TEST.relative_to(HTT_BASE)
    out["locator"] = {k: f"{rel}:{i + 1}" for i, line in enumerate(text.splitlines())
                      for k in ("N_H0", "F_HE", "BG") if line.startswith(f"{k} =")}
    return out


def parse_checkpoint_fractions(path: Path) -> dict:
    """a, x_HII, x_HeII, x_HeIII from an AXBI_CHECKPOINT_V2 file (line 2 fields 0, 3, 4, 5)."""
    lines = Path(path).read_text().splitlines()
    if len(lines) != 6 or lines[0] != "AXBI_CHECKPOINT_V2":
        raise ValueError(f"{path}: not AXBI_CHECKPOINT_V2")
    v = [float(x) for x in lines[1].split()]
    return {"a": v[0], "x_HII": v[3], "x_HeII": v[4], "x_HeIII": v[5]}


def xe_per_h(fr: dict, f_he: float) -> float:
    return fr["x_HII"] + f_he * (fr["x_HeII"] + 2.0 * fr["x_HeIII"])


def lock_cosmology() -> tuple[dict, dict]:
    raw = subprocess.run(["git", "-C", str(REI_REPO), "show", f"{REI_COMMIT}:{LOCK_REL}"], capture_output=True,
                         check=True).stdout
    lock = json.loads(raw)
    return lock, {"source": f"git:{REI_COMMIT}:{LOCK_REL}", "sha256": sha256_bytes(raw)}


def driver_literals(tree: Path) -> dict:
    """Find the Driver::new cosmology literals in the compiled source (both epochs)."""
    needles = {"h0_per_s": "let h0 = 67.4 * 1e5 / 3.0856775814913673e24;", "omega_r": "omega_r: 9.2e-5,",
               "omega_m": "omega_m: 0.315,", "omega_lambda": "omega_lambda: 1.0 - 0.315 - 9.2e-5,",
               "f_he": "let f_he = 0.2454 / (4.0 * (1.0 - 0.2454));"}
    out = {}
    for key, needle in needles.items():
        path = tree / "rust/rei_microphysics/src/axbi_driver.rs"
        hits = [i + 1 for i, line in enumerate(path.read_text().splitlines()) if needle in line]
        if not hits:
            raise ValueError(f"driver literal {needle!r} not found in {path}")
        out[key] = {"file": str(path), "lines": hits, "text": needle}
    return out


def hubble_locked(z: float, bg: FlrwBackground, q_ref: float, a_ref: float) -> float:
    """hypot(H_FLRW, s) with s = q_ref H_FLRW(a_ref) (a_ref/a)^3 (SCENARIO_LOCK background.H), extended to a > a_end."""
    a = 1.0 / (1.0 + z)
    hf = float(bg.hubble_si(z))
    s = q_ref * float(bg.hubble_si(1.0 / a_ref - 1.0)) * (a_ref / a) ** 3
    return math.hypot(hf, s)


def tau_with_h(xe, n_h0: float, hfun, z_lo=0.0, z_hi=Z_MATCH) -> float:
    pref = lowz.C_LIGHT * lowz.SIGMA_T * n_h0 * lowz.CM3_TO_M3
    val, _ = quad(lambda z: (1.0 + z) ** 2 * float(xe(z)) / hfun(z), z_lo, z_hi, epsabs=0.0, epsrel=1e-12, limit=400)
    return pref * val


def units_check(xe, n_h0_cm3: float, h0_km_s_mpc: float, om: float, orad: float, tau_module: float) -> dict:
    """Independent tau: astropy CODATA-2018 constants and units, hand-written integrand."""
    import astropy
    import astropy.units as u
    from astropy.constants import codata2018 as c18
    import astropy.constants as cdefault
    h0 = (h0_km_s_mpc * u.km / u.s / u.Mpc).to_value(1 / u.s)
    ol = 1.0 - om - orad
    pref = (c18.c * c18.sigma_T * n_h0_cm3 * u.cm ** -3 / (h0 / u.s)).to_value(u.dimensionless_unscaled)

    def integrand(z):
        e = math.sqrt(orad * (1 + z) ** 4 + om * (1 + z) ** 3 + ol)
        return (1 + z) ** 2 * float(xe(z)) / e
    val, err = quad(integrand, 0.0, Z_MATCH, epsabs=0.0, epsrel=1e-12, limit=400)
    tau_q = pref * val
    xg, wg = np.polynomial.legendre.leggauss(400)
    zg = 2.0 * (xg + 1.0)
    tau_gl = pref * 2.0 * float(np.sum(wg * np.array([integrand(z) for z in zg])))
    out = {
        "astropy_version": astropy.__version__,
        "constants_used": {"c_m_s": c18.c.value, "sigma_T_m2": c18.sigma_T.value, "codata": "astropy.constants.codata2018",
                           "Mpc_m": (1 * u.Mpc).to_value(u.m), "H0_per_s": h0},
        "module_constants": {"C_LIGHT": lowz.C_LIGHT, "SIGMA_T": lowz.SIGMA_T, "MPC_M": lowz.MPC_M},
        "tau_module": tau_module, "tau_astropy_quad": tau_q, "tau_astropy_gauss_legendre_400": tau_gl,
        "relative_astropy_quad_minus_module": tau_q / tau_module - 1.0,
        "relative_astropy_gauss_legendre_minus_module": tau_gl / tau_module - 1.0,
        "astropy_default_constants_sigma_T_m2": cdefault.sigma_T.value,
        "astropy_default_sigma_T_reference": cdefault.sigma_T.reference,
    }
    try:
        from astropy.constants import codata2022 as c22
        out["codata2022_sigma_T_m2"] = c22.sigma_T.value
        out["relative_tau_shift_if_codata2022_sigma_T"] = c22.sigma_T.value / c18.sigma_T.value - 1.0
    except ImportError:
        out["codata2022_sigma_T_m2"] = None
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rerun", type=Path, default=DEFAULT_RERUN)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    t0 = time.time()
    rerun = json.loads((args.rerun / "REI_RESTART_REPLAY.json").read_text())
    const = r107_test_constants()
    lock, lock_src = lock_cosmology()
    cos = lock["cosmology"]
    bg_lock = FlrwBackground(cos["h0_km_s_mpc"], cos["omega_m"], cos["omega_r"])
    ol_formula = 1 - 0.315 - 0.000092  # SCENARIO_LOCK cosmology.omega_lambda_formula "1-0.315-0.000092"
    a_ref = lock["interval"]["a_ref"]
    literals = {tag: driver_literals(args.rerun / "native" / f"tree_{tag}") for tag in ("d7676", "4de69")}
    cosmology = {
        "source": lock_src,
        "lock_values": {k: cos[k] for k in ("h0_km_s_mpc", "mpc_cm", "omega_m", "omega_r", "omega_lambda_formula",
                                             "helium_mass_fraction", "omega_b_formula")},
        "module_background": {"h0_km_s_mpc": bg_lock.h0_km_s_mpc, "omega_m": bg_lock.omega_m,
                              "omega_r": bg_lock.omega_r, "omega_l": bg_lock.omega_l},
        "checks": {
            "module_omega_l_equals_lock_formula": bg_lock.omega_l == ol_formula,
            "module_Mpc_equals_lock_mpc_cm": lowz.MPC_M * 100.0 == cos["mpc_cm"],
            "module_H0_per_s_bitwise_equals_lock_formula": float(bg_lock.hubble_si(0.0)) == 67.4 * 1e5 / cos["mpc_cm"],
            "module_H0_per_s_relative_minus_lock_formula": float(bg_lock.hubble_si(0.0)) / (67.4 * 1e5 / cos["mpc_cm"]) - 1.0,
            "module_H0_per_s_formula": "h0_km_s_mpc * 1e3 / MPC_M (m based); lock: 67.4*1e5/mpc_cm (cm based)",
            "r107_test_background_equals_lock": const["BG"] == (cos["h0_km_s_mpc"], cos["omega_m"], cos["omega_r"])},
        "driver_new_literals": literals,
        "module_allows_solver_cosmology": ("YES for the flat FLRW part (FlrwBackground(h0, omega_m, omega_r), "
                                           "omega_l = 1 - omega_m - omega_r as in the lock). NO for the shear term of the "
                                           "locked H law (H = hypot(H_FLRW, s)): FlrwBackground has no shear field; its "
                                           "effect is evaluated separately below (shear_term_sensitivity)."),
    }
    # 1. donor band, recomputed with the R107 test constants
    bg107 = FlrwBackground(*const["BG"])
    band = {}
    for zh in Z_HEII:
        c = DonorMatchedContinuation(TF8_DONOR_XE4, const["F_HE"], z_heii=zh)
        tau = tau_flrw(0.0, Z_MATCH, c.x_e, const["N_H0"], bg107)
        band[repr(zh)] = {"tau_0_to_4": tau, "tf8_quoted": TF8_QUOTED[zh], "recomputed_minus_quoted": tau - TF8_QUOTED[zh],
                          "rounds_to_quoted_7_decimals": round(tau, 7) == TF8_QUOTED[zh]}
    band_vals = [band[repr(z)]["tau_0_to_4"] for z in Z_HEII]
    band_lo, band_hi = min(band_vals), max(band_vals)
    # affine coefficient B(zh) = d tau / d x_e(4): the continuation is affine in x_e_match
    xfull = 1.0 + 2.0 * const["F_HE"]
    slope = {}
    for zh in Z_HEII:
        t1 = tau_flrw(0.0, Z_MATCH, DonorMatchedContinuation(1.0, const["F_HE"], z_heii=zh).x_e, const["N_H0"], bg107)
        t2 = tau_flrw(0.0, Z_MATCH, DonorMatchedContinuation(xfull, const["F_HE"], z_heii=zh).x_e, const["N_H0"], bg107)
        slope[zh] = (t2 - t1) / (xfull - 1.0)
    # 2.-4. per case
    cases = {}
    inside_all = True
    for case in CASES:
        rc = rerun["cases"][case]
        ck_path = Path(rc["restart_inventory"]["restart_file"])
        if sha256(ck_path) != rc["restart_inventory"]["restart_sha256"]:
            raise ValueError(f"{case}: checkpoint changed since the replay rerun")
        rep = json.loads((args.rerun / "replay" / case / "replay.json").read_text())
        n_h0, n_he0 = rep["n_h0_cm3"], rep["n_he0_cm3"]
        f_he = n_he0 / n_h0
        fr = parse_checkpoint_fractions(ck_path)
        x4 = xe_per_h(fr, f_he)
        q = rc["q_ref"]
        per = {}
        for zh in Z_HEII:
            cont = DonorMatchedContinuation(x4, f_he, z_match=Z_MATCH, z_heii=zh)
            tau = tau_flrw(0.0, Z_MATCH, cont.x_e, n_h0, bg_lock)
            d = band[repr(zh)]["tau_0_to_4"]
            # exact decomposition of tau_case - tau_donor (same z_HeII): x_e(4) term with the R107 normalisation,
            # then the n_H0 and f_He normalisation of the native driver
            tau_x_only = tau_flrw(0.0, Z_MATCH, DonorMatchedContinuation(x4, const["F_HE"], z_heii=zh).x_e,
                                  const["N_H0"], bg107)
            tau_x_nh = tau_flrw(0.0, Z_MATCH, DonorMatchedContinuation(x4, const["F_HE"], z_heii=zh).x_e, n_h0, bg107)
            tau_shear = tau_with_h(cont.x_e, n_h0, lambda z: hubble_locked(z, bg_lock, q, a_ref))
            per[repr(zh)] = {
                "tau_0_to_4": tau,
                "inside_donor_band": band_lo <= tau <= band_hi,
                "minus_donor_same_z_HeII": tau - d,
                "relative_to_donor_same_z_HeII": tau / d - 1.0,
                "above_band_max_by": max(0.0, tau - band_hi), "below_band_min_by": max(0.0, band_lo - tau),
                "decomposition": {
                    "x_e4_term_exact": tau_x_only - d,
                    "x_e4_term_affine_prediction": slope[zh] * (x4 - TF8_DONOR_XE4),
                    "n_H0_term": tau_x_nh - tau_x_only,
                    "f_He_and_background_term": tau - tau_x_nh,
                    "sum_minus_total": (tau_x_only - d) + (tau_x_nh - tau_x_only) + (tau - tau_x_nh) - (tau - d)},
                "shear_term_sensitivity": {
                    "tau_with_locked_H_hypot_extension": tau_shear,
                    "minus_flrw_module": tau_shear - tau,
                    "relative": tau_shear / tau - 1.0,
                    "label": ("EXTENSION_OUTSIDE_LOCKED_DOMAIN: SCENARIO_LOCK background.H = sqrt(H_flrw^2 + s^2) on "
                              "[a_ref, a_end=0.2] only; evaluated at a > 0.2 for sensitivity, independent integrand "
                              "(scipy quad epsrel 1e-12)")}}
            inside_all &= per[repr(zh)]["inside_donor_band"]
        cases[case] = {
            "q_ref": q, "checkpoint": str(ck_path), "checkpoint_sha256": sha256(ck_path),
            "a_checkpoint": fr["a"], "x_HII": fr["x_HII"], "x_HeII": fr["x_HeII"], "x_HeIII": fr["x_HeIII"],
            "n_h0_cm3_native": n_h0, "n_he0_cm3_native": n_he0, "f_He_native": f_he,
            "x_e4_from_checkpoint": x4,
            "x_e4_equals_r106_inventory": x4 == rc["restart_inventory"]["charge"]["xe_per_H"],
            "x_e4_minus_tf8_donor": x4 - TF8_DONOR_XE4,
            "n_h0_minus_r107_constant": n_h0 - const["N_H0"], "f_he_minus_r107_constant": f_he - const["F_HE"],
            "by_z_HeII": per,
            "r106_tanh_foreground_for_context": {
                k: rc["foreground_sensitivity_z_0_to_4"][k]["tau_0_to_4_adaptive"]
                for k in ("H_and_first_He", "with_HeII_to_HeIII")}}
    # 5. units check on the ZERO case at z_HeII = 3.5 and on the TF8 donor at 3.5
    zc = cases["ZERO"]
    cont0 = DonorMatchedContinuation(zc["x_e4_from_checkpoint"], zc["f_He_native"], z_heii=3.5)
    units = {
        "ZERO_case_z_HeII_3.5": units_check(cont0.x_e, zc["n_h0_cm3_native"], cos["h0_km_s_mpc"], cos["omega_m"],
                                            cos["omega_r"], zc["by_z_HeII"]["3.5"]["tau_0_to_4"]),
        "TF8_donor_z_HeII_3.5": units_check(DonorMatchedContinuation(TF8_DONOR_XE4, const["F_HE"], z_heii=3.5).x_e,
                                            const["N_H0"], *const["BG"], band["3.5"]["tau_0_to_4"])}
    taus = np.array([[cases[c]["by_z_HeII"][repr(z)]["tau_0_to_4"] for z in Z_HEII] for c in CASES])
    result = {
        "schema": "htt.r108.s8.lowz_tau/1",
        "script": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve())},
        "module": {"path": str(Path(lowz.__file__).resolve()), "sha256": sha256(Path(lowz.__file__).resolve())},
        "inputs": {"rerun_result": str(args.rerun / "REI_RESTART_REPLAY.json"),
                   "rerun_result_sha256": sha256(args.rerun / "REI_RESTART_REPLAY.json"),
                   "r107_test_constants": const, "tf8_locator": f"{R107_TF8.relative_to(HTT_BASE)}:132-135",
                   "tf8_donor_x_e4": TF8_DONOR_XE4},
        "cosmology_from_solver_configuration": cosmology,
        "donor_band_recomputed": {"by_z_HeII": band, "band_min": band_lo, "band_max": band_hi,
                                  "all_round_to_tf8_quoted": all(v["rounds_to_quoted_7_decimals"] for v in band.values()),
                                  "dtau_dxe4_by_z_HeII": {repr(z): slope[z] for z in Z_HEII},
                                  "constants": "R107 test N_H0, F_HE, BG (inputs.r107_test_constants)"},
        "cases": cases,
        "summary": {
            "tau_table_rows_cases_cols_z_HeII": {"cases": list(CASES), "z_HeII": list(Z_HEII), "tau": taus.tolist()},
            "max_abs_case_minus_donor_same_z_HeII": float(np.max(np.abs(taus - np.array(band_vals)[None, :]))),
            "max_case_to_case_spread_same_z_HeII": float(np.max(taus.max(axis=0) - taus.min(axis=0))),
            "all_case_depths_inside_donor_band": bool(inside_all),
            "n_case_depths_outside_band": int(sum(not cases[c]["by_z_HeII"][repr(z)]["inside_donor_band"]
                                                   for c in CASES for z in Z_HEII))},
        "units_check": units,
        "claim_class": ("CONDITIONAL_CLOSURE: donor-matched continuation with declared HeII timing (sensitivity only); "
                        "not an REI computation below z = 4; no family attribution, no likelihood"),
        "wall_s": None}
    result["wall_s"] = time.time() - t0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["summary"], indent=1))
    print(json.dumps({k: v["relative_astropy_quad_minus_module"] for k, v in units.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
