#!/usr/bin/env python3
"""R54-L07: adversarial benchmark against published methods, evidence verification and novelty checks.

Steps follow LOCAL_AGENT_CONTRACT.json:nodes[R54-L07]:
 1. each target with owned-data overlap: published headline reproduced under the published assumptions -> REPRODUCED,
    NOT_REPRODUCED or NOT_REPRODUCIBLE_FROM_TEXT with the measured value (numbers read from RESULTS/*.json)
 2. score under the common R54 assumptions (WIN / TIE / LOSS / NOT_COMPARABLE; a tie is never a win)
 3. evidence rows not VERIFIED: verification from primary-source searches of 2026-11-16 (recorded below with the source URL)
 4. novelty checks for H-L1b and H-L5g (nearest prior art)
The published numbers are those of ADVERSARIAL_BENCHMARK_SPEC.json and of the paper text read in R54-L03. Claim tier C0.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "htt", ROOT / "htt/src", ROOT, ROOT / "scripts/r54"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import run_r54_lowz_frames as lz  # noqa: E402

PUB = ROOT / "docs/research_program/observational_publication_20261015"
R54 = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
RES = R54 / "RESULTS"
OUT = RES / "R54_L07_BENCHMARK.json"
SPEC = R54 / "ADVERSARIAL_BENCHMARK_SPEC.json"
FILES = {k: RES / v for k, v in (("l1", "R54_L1_TYPE1_TE.json"), ("l5", "R54_L5_LOWZ_FRAMES.json"), ("l05", "R54_L05_CF4_EXACT.json"),
                                 ("l01", "R54_L01_RESULT.json"), ("l02", "R54_L02_RESULT.json"), ("l03", "R54_L03_RESULT.json"),
                                 ("l04", "R54_L04_RESULT.json"), ("l06", "R54_L06_JOINT.json"))}
#: ledger rows that were not VERIFIED, checked by web searches of 2026-11-16 (identifier and claim seen unless the status says otherwise)
EVIDENCE_CHECKS = {
    "E08": ("VERIFIED", "arXiv astro-ph/9702170: Hu & White, PRD 56, 596 (1997), total angular momentum method", "https://arxiv.org/abs/astro-ph/9702170"),
    "E18": ("VERIFIED", "arXiv 2010.06534: Heinesen, JCAP 05 (2021) 008, multipole decomposition of the luminosity-distance Hubble law", "https://arxiv.org/abs/2010.06534"),
    "E23": ("VERIFIED", "arXiv 2311.14938: Mittal, Oayda & Lewis, MNRAS 527, 8497; Quaia dipole consistent with the CMB dipole for |b| > 40 deg", "https://arxiv.org/html/2311.14938v2"),
    "E24": ("VERIFIED", "arXiv 2305.15335: Wagenveld, Kloeckner & Schwarz, A&A 675, A72; NVSS+RACS amplitude about three times the CMB expectation", "https://arxiv.org/pdf/2305.15335"),
    "E29": ("VERIFIED", "arXiv 1511.05969: Sellentin & Heavens, MNRAS 456, L132; t-type likelihood with an estimated covariance", "https://arxiv.org/abs/1511.05969"),
    "E30": ("VERIFIED", "arXiv 2108.10402: Percival, Friedrich, Sellentin & Heavens, MNRAS 510, 3207; frequentist-matching prior", "https://arxiv.org/abs/2108.10402"),
    "E31": ("VERIFIED", "arXiv astro-ph/9501016: Maartens, Ellis & Stoeger, PRD 51, 1525; quadrupole and octopole limits on shear and vorticity", "https://arxiv.org/abs/astro-ph/9501016"),
    "E32": ("VERIFIED", "arXiv 1906.02552: Planck 2018 VII (A&A 641, A7); residual systematics limit polarization tests", "https://arxiv.org/abs/1906.02552"),
    "E35": ("NOT_FOUND", "no record of doi:10.1093/mnras/stag677 found; nearest: arXiv 2604.08314 (CF4 peculiar-velocity correlation function), authors not seen", "https://arxiv.org/abs/2604.08314"),
    "E36": ("NOT_FOUND", "ApJ 332, L7 not confirmed by a search; the velocity correlation tensor is re-derived and tested (R54-EQ-30/31)", ""),
    "E37": ("VERIFIED", "arXiv astro-ph/9502079: Strauss & Willick, Phys. Rep. 261, 271", "https://arxiv.org/abs/astro-ph/9502079"),
    "E38": ("IDENTIFIER_ONLY", "arXiv 1012.2912: Davis et al., ApJ 741, 67 (identifier seen; the (1 + u/c)^2 factor was not seen in the search result)", "https://arxiv.org/abs/1012.2912"),
    "E39": ("VERIFIED", "arXiv astro-ph/0512159: Hui & Greene, PRD 73, 123526; correlated luminosity-distance fluctuations from peculiar motion", "https://arxiv.org/abs/astro-ph/0512159"),
    "E40": ("IDENTIFIER_ONLY", "arXiv 1312.1022: Koda et al. (identifier seen; the sinc damping form is attributed to it by later papers)", "https://arxiv.org/abs/1312.1022"),
    "E41": ("VERIFIED", "arXiv 1411.6665: Watkins & Feldman, MNRAS 450, 1868; unbiased estimator with Gaussian errors", "https://arxiv.org/abs/1411.6665"),
    "E42": ("VERIFIED", "arXiv 2212.10328: Sorrenti, Durrer & Kunz; Pantheon+ dipole, direction differing from the CMB dipole (as summarised in arXiv 2403.17741)", "https://arxiv.org/abs/2212.10328"),
    "E48": ("VERIFIED", "Negroponte & Silk, PRL 44, 1433 (1980), doi:10.1103/PhysRevLett.44.1433, polarization in anisotropic universes", "https://doi.org/10.1103/PhysRevLett.44.1433"),
}
NOVELTY = {
    "H-L1b": {"question": "prior stress-corrected Bianchi-I CMB shear limits",
              "searches": ["Bianchi I shear CMB limit neutrino anisotropic stress free-streaming shear decay constraint quadrupole polarization (extended search)"],
              "nearest_prior_art": ["E01/E02 Saadeh et al. 2016 (perfect-fluid Bianchi limits from Planck T+pol)", "E03 Pontzen & Challinor 2007",
                                    "arXiv:1102.5235 (free-streaming neutrino stress back-reacts on a Bianchi-I anisotropy; temperature only)",
                                    "E46 Basko & Polnarev 1980 (kernels)"],
              "novelty": "LOW-MODERATE (searched): no prior T+E limit with a radiation-stress history map was found; the kernels are a re-derivation and the present-shear numbers are model illustrations"},
    "H-L5f": {"question": "log-distance CF4 estimator replacing the biased linear-in-distance estimator, with an exact pair-sum LCDM body",
              "searches": ["arXiv 1411.6665 Watkins Feldman unbiased estimator peculiar velocities Gaussian distribution",
                           "Gorski 1988 ApJ 332 L7 velocity correlation (not confirmed)"],
              "nearest_prior_art": ["E41 Watkins & Feldman 2015 (log-distance estimator avoiding the log-normal bias)", "E37 Strauss & Willick 1995 (Malmquist and estimator biases)",
                                    "E36 Gorski 1988 velocity correlation tensor (identifier NOT_FOUND; the tensor is re-derived and tested in R54-EQ-30/31)"],
              "novelty": "LOW (searched): the estimator is E41-type and the pair-sum body is the standard velocity correlation tensor; the contribution is their application to the CF4 window multipoles"},
    "H-L5g": {"question": "cross-indicator common-mode test of the CF4 hemisphere asymmetry with a catalogue-level LCDM covariance",
              "searches": ["Cosmicflows-4 hemisphere asymmetry zero point distance indicators Tully-Fisher fundamental plane supernova north south calibration offset (extended search)"],
              "nearest_prior_art": ["E43 Nusser & Tully 2026 (per-catalogue log-distance dipoles; 6dFGS removal)", "E09 Stiskalek et al. 2026 (TF zero-point dipole)",
                                    "E33 Boubel et al. 2024 (TF H0 dipole)"],
              "novelty": "LOW (searched): E43 already compares constituent catalogues with a log-distance estimator; the exact pair-sum cross-covariance between indicators is the only addition, and the step is UNRESOLVED (R54-L04)"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute() -> dict:
    missing = [str(p) for p in [SPEC, *FILES.values()] if not p.is_file()]
    if missing:
        return {"status": "BLOCKED_MISSING_INPUT", "reason": "missing: " + ", ".join(missing)}
    d = {k: json.loads(p.read_text()) for k, p in FILES.items()}
    spec = json.loads(SPEC.read_text())
    t = {}
    ps = d["l1"]["data"]["physics_primary"]["present_shear_over_H"]
    pf, pft, pub01 = ps["perfect_fluid_T_plus_E"]["frobenius_range_95"]["norm_max"], ps["perfect_fluid_T_only"]["frobenius_range_95"]["norm_max"], 4.7e-11
    t["B01"] = {"measured": {"perfect_fluid_T_plus_E_95": pf, "perfect_fluid_T_only_95": pft}, "published": pub01, "ratio_to_published": pf / pub01,
                "status": "REPRODUCED" if 0.1 <= pf / pub01 <= 10.0 else "NOT_REPRODUCED", "score": "NOT_COMPARABLE",
                "reason": "within the factor-10 tolerance of the spec (the tolerance is not changed after the result); the T+E bound is weaker than the published "
                          "limit and uses the FFP10-only E covariance of a DIAGNOSTIC E lane; different data (all-ell T + polarization against the ell = 2 carrier); "
                          "R54 adds the radiation-stress model label"}
    tf = d["l05"]["common_mode"]["white_plus_exact_body"]["per_method"]["TF"]
    pub02, sd02 = 4.1, 0.9
    t["B02"] = {"measured": {"TF_dipole_percent": tf["amplitude_percent"], "TF_wald_p_with_body": tf["p_value"], "direction_l_b_deg": tf["direction_l_b_deg"]},
                "published": {"percent": pub02, "sd": sd02}, "difference_in_published_sd": (tf["amplitude_percent"] - pub02) / sd02,
                "status": "REPRODUCED" if abs(tf["amplitude_percent"] - pub02) <= 2.0 * sd02 else "NOT_REPRODUCED", "score": "NOT_COMPARABLE",
                "reason": "different selections (all TF groups against TF W1), so the scoring rule gives NOT_COMPARABLE; the amplitude agrees within the tolerance "
                          "and with the exact LCDM body the TF dipole is not significant (R57 review RC-07)"}
    hw, hg = d["l05"]["log_distance"]["headline_white_only"], d["l05"]["log_distance"]["headline"]
    pub03, sd03 = 419.0, 36.0
    dir_ok, amp_ok = hw["V_only_angle_to_watkins_deg"] <= 20.0, abs(hw["V_only_km_s"] - pub03) <= 2.0 * sd03
    t["B03"] = {"measured": {"V_white_km_s": hw["V_only_km_s"], "V_white_angle_deg": hw["V_only_angle_to_watkins_deg"], "V_body_km_s": hg["V_only_km_s"],
                             "V_body_angle_deg": hg["V_only_angle_to_watkins_deg"]}, "published": {"km_s": pub03, "sd": sd03, "l_b_deg": [298.0, -8.0]},
                "direction_reproduced": dir_ok, "amplitude_reproduced": amp_ok, "status": "REPRODUCED" if dir_ok and amp_ok else "NOT_REPRODUCED",
                "score": "NOT_COMPARABLE", "reason": "the published bulk flow is a 200 h^-1 Mpc volume moment; the R54 V is a window-fit velocity of the log-distance estimator"}
    ax = lz.angle_deg(lz.gal_unit(*hg["best_axis_l_b_deg"]), lz.gal_unit(295.0, 5.0), axis=True)
    t["B04"] = {"measured": {"best_template_axis_l_b_deg": hg["best_axis_l_b_deg"], "angle_to_published_axis_deg": ax, "robust_class": d["l04"]["decision"]["robust_class"]},
                "published": {"l_b_deg": [295.0, 5.0]}, "status": "REPRODUCED" if ax <= 20.0 else "NOT_REPRODUCED", "score": "NOT_COMPARABLE",
                "reason": "R54 assigns no physical axis: the class depends on the zero-point nuisance model (R54-L04)"}
    cp = d["l03"]["competitors"]
    t["B05"] = {"measured": {k: {"owned_D": v["owned"]["D"], "published_D": v["published"]["D"], "difference_in_published_sd": v["amplitude_difference_in_published_sd"],
                                 "status": v["status"]} for k, v in cp.items()},
                "R54_excess_tails": {k: v["chi2"]["p_value"] for k, v in d["l03"]["excess_tests"].items()},
                "status": "REPRODUCED" if all(v["status"] == "REPRODUCED" for v in cp.values()) else "NOT_REPRODUCED", "score": "TIE",
                "reason": "the amplitudes agree; the R54 tails differ because the receipt covariance carries declared declination and mask systematics, "
                          "an error-model choice that is not shown to be better calibrated (no WIN)"}
    an = d["l06"]["anchors"]
    t["B06"] = {"measured": {k: v["difference_in_sd"] for k, v in an.items()}, "status": "NOT_REPRODUCIBLE_FROM_TEXT", "score": "NOT_COMPARABLE",
                "reason": "no owned map-level aberration or redshift-tomography data; published anchors only"}
    t["B07"] = {"measured": None, "status": "NOT_REPRODUCIBLE_FROM_TEXT", "score": "NOT_COMPARABLE", "reason": "Gaia CRF3 systematics model not opened (RESEARCH_DAG not_opened)"}
    l04 = d["l04"]
    mono_outer = d["l05"]["zero_point_split"]["method_monopoles_only"]["window_subsets"]["outer_windows_z0.06_z0.08"]["joint"]["p_value"]
    no6_outer = l04["leave_6dfgs_proxy_out"]["window_subsets"]["outer_windows_z0.06_z0.08"]["joint"]["p_value"]
    t["B08"] = {"measured": {"FP_NOT_SDSS_minus_FP_SDSS_mag": l04["survey_offsets"]["white_plus_exact_body"]["FP_NOT_SDSS-FP_SDSS"]["delta_mu_mag"],
                             "outer_windows_joint_p_method_monopoles": mono_outer, "outer_windows_joint_p_without_6dFGS_proxy": no6_outer},
                "published": "removing 6dFGS lowers the upper-bin deviation", "direction_of_change_reproduced": bool(no6_outer > mono_outer),
                "status": "NOT_REPRODUCIBLE_FROM_TEXT", "score": "NOT_COMPARABLE",
                "reason": "6dFGSv is not separable from other non-SDSS FP in owned files and the radial bins differ; only the direction of the change is compared"}
    t["B09"] = {"measured": {"r_E_perfect_fluid": d["l1"]["history"]["perfect_fluid"]["r_E"]}, "status": "REPRODUCED", "score": "TIE",
                "label": "re-derivation (identity)",
                "reason": "kernel identity (tests/r54/test_r54_modules.py::test_eq03_sympy_seal_of_kernels); a re-derivation, not a methods comparison, no novelty"}
    for b in spec["targets"]:
        t[b["id"]]["node"] = b["node"]
        t[b["id"]]["published_claim"] = b["published_claim"]
    scores = {k: v["score"] for k, v in t.items()}
    complete = len(t) == len(spec["targets"]) and all(v.get("status") for v in t.values())
    return {"status": "DONE_SCOPED_C0", "targets": t, "scores": scores,
            "score_counts": {s: sum(1 for v in scores.values() if v == s) for s in ("WIN", "TIE", "LOSS", "NOT_COMPARABLE")},
            "evidence_verification": {k: {"status": v[0], "note": v[1], "source": v[2]} for k, v in EVIDENCE_CHECKS.items()},
            "novelty_checks": NOVELTY,
            "acceptance": {"targets_with_status": {"value": "all" if complete else "incomplete", "op": "==", "threshold": "all", "pass": complete}}}


def main() -> None:
    res = compute()
    prov = {"script": "scripts/r54/run_r54_l07_benchmark.py", "script_sha256": sha256(Path(__file__)),
            "inputs_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in FILES.values() if p.is_file()},
            "spec_targets_read": [b["id"] for b in json.loads(SPEC.read_text())["targets"]] if SPEC.is_file() else [],
            "spec_note": "ADVERSARIAL_BENCHMARK_SPEC.json is generated from this result (status, score), so only its target list is bound",
            "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}
    out = {"schema": "htt.r54.l07_benchmark/1", "node": "R54-L07", "claim_tier": "C0", **res, "provenance": prov,
           "limitations": ["Published numbers come from the benchmark spec and from the paper text read in R54-L03; literature checks are web searches of 2026-11-16.",
                           "A TIE is never scored as a WIN; NOT_COMPARABLE is used whenever data or model class differ."]}
    OUT.write_text(json.dumps(lz.clean(out), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(lz.clean({"status": out["status"], "scores": out.get("scores"), "acceptance": out.get("acceptance")}), indent=1))
    if out["status"] != "DONE_SCOPED_C0":
        raise SystemExit(out["status"])


if __name__ == "__main__":
    main()
