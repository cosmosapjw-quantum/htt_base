"""v10 external-report data figures (--write / --check).

Renders the v10 report's data-analysis figures DETERMINISTICALLY from
sealed result cards only (no raw re-reads except the odd-L demo, which
reads nothing). Every figure has a .caption.txt sidecar; a manifest JSON
pins sha256 of every artifact. --check regenerates everything into a
temporary directory and byte-compares.

Quarantine discipline: figures consume ONLY active compliant surfaces
(PR-144..148 wave cards, PR-150/177/179/180 cards, the v10 even-L card,
DESI/ACT cards, exact theory seals). Quarantined CF4 legacy numeric
instantiations are never read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
G = REPO / "docs/generated"
OUT = REPO / "figures/data_analysis_current/v10"
MANIFEST = G / "v10_report_figure_manifest.json"

C_KMS = 299792.458
OMEGA_M = 0.315

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 110,
    "font.size": 8.5,
    "axes.titlesize": 9,
    "svg.hashsalt": "v10",
})


def _load(name: str) -> dict:
    return json.loads((G / name).read_text())


def _save(fig, outdir: Path, stem: str, caption: str) -> list[Path]:
    png = outdir / f"{stem}.png"
    fig.savefig(png, bbox_inches="tight", metadata={"Software": "bass-v10"})
    plt.close(fig)
    cap = outdir / f"{stem}.caption.txt"
    cap.write_text(caption.strip() + "\n")
    return [png, cap]


def omega_tilt_of_kms(v: float) -> float:
    """Registered closed form (1+w) Omega_m sinh^2(beta), dust w=0."""
    return OMEGA_M * math.sinh(math.atanh(v / C_KMS)) ** 2


def fig_comparator_region(outdir: Path) -> list[Path]:
    refreeze = _load("mes_geodesic_refreeze_seal.json")["refrozen_anchor"]
    branches = _load("mes_branch_registry_seal.json")["w2_ceiling_branches"]
    omk = _load("k5_omega_k_ceiling_card.json")["ceiling_rows"]
    idset = _load("pr147_identified_set.json")["shells"]

    sigma2_max = float(refreeze["Sigma2_max"])
    w2 = {
        "geodesic (SAG-consistent, live)": float(
            branches["sag_consistent"]["value_float"]
        ),
        "registered (frozen legacy)": float(
            branches["registered"]["value_float"]
        ),
        "hybrid (literature envelope)": float(
            branches["hybrid_literature"]["value_float"]
        ),
    }
    omk_rows = {
        k: float(v["omega_k_ceiling_abs"]) for k, v in sorted(omk.items())
    }
    tilt_iv = [
        (
            f"shell {i} ({s['dist_lo_mpc']:.0f}-{s['dist_hi_mpc']:.0f} Mpc)",
            omega_tilt_of_kms(s["amplitude_interval_kms"][0]),
            omega_tilt_of_kms(s["amplitude_interval_kms"][1]),
        )
        for i, s in enumerate(idset, start=1)
    ]

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(9.6, 3.6), gridspec_kw={"width_ratios": [3, 2]}
    )
    rows: list[tuple[str, float, float, str]] = []
    rows.append((r"$\Sigma^2$ ceiling (MES geodesic)", 1e-16, sigma2_max,
                 "tab:blue"))
    for label, val in w2.items():
        rows.append((rf"$W^2$ ceiling: {label}", 1e-16, val, "tab:red"))
    for label, lo, hi in tilt_iv:
        rows.append((rf"$\Omega_{{\rm tilt}}$ identified: {label}", lo, hi,
                     "tab:green"))
    for label, val in omk_rows.items():
        rows.append((rf"$|\Delta\Omega_k|$ ceiling: {label}", 1e-16, val,
                     "tab:purple"))
    for j, (label, lo, hi, color) in enumerate(rows):
        ax.plot([max(lo, 1e-16), hi], [j, j], lw=5, color=color, alpha=0.75)
        ax.plot([hi], [j], "|", ms=10, color=color)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xlim(1e-14, 1e-1)
    ax.invert_yaxis()
    ax.set_xlabel("dimensionless component magnitude")
    ax.set_title("component ceilings and identified intervals")
    ax.grid(alpha=0.25, axis="x")

    tilt_lo, tilt_hi = tilt_iv[0][1], tilt_iv[0][2]
    combos = {
        "geodesic + cosmological": (
            w2["geodesic (SAG-consistent, live)"],
            omk_rows.get("mes_cosmological__matter_era", 0.0),
        ),
        "registered + registered": (
            w2["registered (frozen legacy)"],
            omk_rows.get("mes_registered__matter_era", 0.0),
        ),
        "hybrid + registered": (
            w2["hybrid (literature envelope)"],
            omk_rows.get("mes_registered__matter_era", 0.0),
        ),
    }
    for j, (label, (w2max, okmax)) in enumerate(combos.items()):
        xlo = 0.0 - w2max + tilt_lo - okmax
        xhi = sigma2_max - 0.0 + tilt_hi + okmax
        ax2.plot([xlo, xhi], [j, j], lw=6, color="tab:orange", alpha=0.8)
        ax2.annotate(f"[{xlo:+.2e}, {xhi:+.2e}]", (0, j),
                     textcoords="offset points", xytext=(0, 8), fontsize=7,
                     ha="center")
    ax2.axvline(0.0, color="k", lw=0.8, ls="--")
    ax2.set_yticks(range(len(combos)))
    ax2.set_yticklabels(list(combos.keys()), fontsize=7)
    ax2.set_ylim(-0.6, len(combos) - 0.4)
    ax2.invert_yaxis()
    ax2.set_xscale("symlog", linthresh=1e-12)
    ax2.set_xticks([-1e-2, -1e-5, -1e-8, 0.0, 1e-8, 1e-5, 1e-2])
    ax2.tick_params(axis="x", labelsize=6)
    ax2.set_xlabel(r"$x_C$ interval (symlog)")
    ax2.set_title(r"$x_C$ identified interval per attribution branch")
    ax2.grid(alpha=0.25, axis="x")
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_comparator_region",
        "Assembled identified region for the registered comparator vector "
        "g = (Sigma^2, W^2, Omega_tilt, DeltaOmega_k). Left: per-component "
        "ceilings (MES vorticity branches; MES-slaved anisotropic-curvature "
        "ceilings) and the CF4 nuisance-box identified Omega_tilt intervals "
        "per depth shell (PR-147 amplitude intervals pushed through the "
        "registered closed form (1+w) Omega_m sinh^2 beta at w = 0). "
        "Right: the induced exact interval for x_C = Sigma^2 - W^2 + "
        "Omega_tilt + DeltaOmega_k under three attribution branches "
        "(interval arithmetic; identical to the exact identified-set "
        "engine on this axis-separable system). Diagnostic rendering of "
        "registered ceilings and identified sets; no detection statement.",
    )


def fig_k1_rank_hist(outdir: Path) -> list[Path]:
    card = _load("k1_global_maxscan_e2e_full.json")
    pooled = _load("pr150_e2e_pooled_rank.json")
    res = card["result"]
    stats = sorted(res["local_p"].keys())
    sims = res["simulation_statistics"]
    obs = res["observed_statistics"]

    fig, axes = plt.subplots(2, 4, figsize=(11.5, 5.2))
    for i, stat in enumerate(stats):
        ax = axes.flat[i]
        vals = np.asarray([s["statistics"][stat] for s in sims])
        ax.hist(vals, bins=36, color="tab:gray", alpha=0.75)
        ax.axvline(obs[stat], color="tab:red", lw=1.5)
        ax.set_title(f"{stat}\nlocal p = {res['local_p'][stat]:.3f}",
                     fontsize=7.5)
        ax.tick_params(labelsize=6)
    ax = axes.flat[len(stats)]
    ax.hist(np.asarray([s["max_score"] for s in res["simulation_max_scores"]]),
            bins=36, color="tab:blue", alpha=0.75)
    ax.axvline(res["observed_max_score"], color="tab:red", lw=1.5)
    ax.set_title(
        "pooled max-scan\nlook-elsewhere global p = "
        f"{pooled['look_elsewhere_global_p']:.4f}", fontsize=7.5)
    ax.tick_params(labelsize=6)
    axes.flat[-1].axis("off")
    fig.suptitle(
        "K1 low-multipole statistics: observed SMICA vs the SMICA-processed "
        "FFP10 end-to-end null (999 CMB + 300 noise MC)", fontsize=9)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_k1_rank_hist",
        "Per-statistic null distributions (grey) and observed values (red) "
        "for the six pre-registered low-multipole statistics on the masked "
        "SMICA map under the SMICA-processed FFP10 end-to-end null, plus "
        "the pooled max-scan distribution whose exchangeable rank gives "
        "the look-elsewhere-corrected global p. E2E-conditional diagnostic; "
        "no detection statement.",
    )


def fig_k1_evenl(outdir: Path) -> list[Path]:
    card = _load("k1_evenl_biposh_rank_card.json")
    res = card["result"]
    hist = card["sim_score_histogram"]
    edges = np.asarray(hist["edges"])
    counts = np.asarray(hist["counts"])
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.bar(0.5 * (edges[:-1] + edges[1:]), counts,
           width=np.diff(edges), color="tab:gray", alpha=0.8)
    ax.axvline(res["pooled"]["observed_score"], color="tab:red", lw=1.6,
               label=f"observed (pooled p = {res['pooled']['rank_p']:.3f})")
    per_l = res["per_L_secondary"]
    txt = ", ".join(f"L={k[1:]}: p = {v['rank_p']:.3f}"
                    for k, v in sorted(per_l.items()))
    ax.set_title(
        "even-L diagonal BiPoSH invariant powers: pooled Mahalanobis rank\n"
        f"per-L secondary ranks: {txt}; odd-L structural zero certified at "
        f"{res['odd_l_structural_zero_max_ratio']:.1e}", fontsize=8)
    ax.set_xlabel("Hartlap-corrected leave-one-out Mahalanobis score")
    ax.set_ylabel("simulations")
    ax.legend(fontsize=7)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_k1_evenl_rank",
        "Even-L diagonal BiPoSH rotationally invariant powers "
        "S_{ell,L} = sum_M |A^{LM}_{ll}|^2 (L = 2, 4; ell = 2..10) on the "
        "masked SMICA map, ranked against the SMICA-processed FFP10 "
        "end-to-end null by a Hartlap-corrected leave-one-out Mahalanobis "
        "score. The odd-L diagonal vanishes identically for any alm "
        "(exchange symmetry; known result), so odd L carries no trials; "
        "the measured odd/even ratio on the observed map certifies the "
        "implementation at float precision. E2E-conditional diagnostic; "
        "no detection statement.",
    )


def fig_boost_biposh(outdir: Path) -> list[Path]:
    card = _load("pr180_result_card.json")
    band = _load("k1_evenl_biposh_rank_card.json")["result"][
        "boost_feature_band"]
    res = card["result"]
    ells = np.asarray(res["feature_ells"])
    obs = np.asarray(res["observed_feature"])
    mean = np.asarray(res["sim_feature_mean"])
    tem = np.asarray(res["template_operator_derived"])
    tse = np.asarray(res["template_mc_se"])
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.3))
    ax.fill_between(band["ells"], band["sim_p16"], band["sim_p84"],
                    color="tab:gray", alpha=0.35,
                    label="boosted-FFP10 16-84% band")
    ax.plot(ells, obs, "o-", color="tab:red", label="observed SMICA")
    ax.plot(ells, mean, "s--", color="tab:gray",
            label="boosted-FFP10 sim mean")
    ax.set_xlabel(r"$\ell$")
    ax.set_ylabel(r"$F_\ell$ (dipole-frame $(\ell,\ell+1)$ coupling)")
    ax.set_title(
        f"boost-BiPoSH feature vector; rank p = {res['rank_p']:.3f}",
        fontsize=8.5)
    ax.legend(fontsize=7)
    ax2.errorbar(ells, tem, yerr=tse, fmt="d-", color="tab:blue",
                 label="operator-derived template (per unit map)")
    ax2.axhline(0, color="k", lw=0.7)
    ax2.set_xlabel(r"$\ell$")
    ax2.set_title(
        "zero-parameter exact-boost template "
        f"(linearity ratio {res['linearity_ratio_f2h_over_fh']:.3f})",
        fontsize=8.5)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_boost_biposh_features",
        "Left: the dipole-frame L = 1 boost-BiPoSH feature vector F_ell of "
        "the masked SMICA map against the boosted-FFP10 ensemble mean and "
        "16-84% scatter band; the observed excitation ranks p = 0.854 "
        "inside the end-to-end null under the full-covariance Mahalanobis "
        "score (per-ell excursions are within the correlated null spread). "
        "Right: the zero-parameter template derived from the exact "
        "pixel-space boost operator by two-point Richardson extrapolation "
        "at amplified boost, with Monte-Carlo standard errors; the "
        "linearity gate value is shown. Consistency diagnostic only; never "
        "a boost confirmation or detection.",
    )


def fig_cf4_depth(outdir: Path) -> list[Path]:
    idset = _load("pr147_identified_set.json")["shells"]
    growth = _load("pr148_fsigma8_by_depth.json")
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(8.8, 3.3))
    for j, s in enumerate(idset):
        lo, hi = s["amplitude_interval_kms"]
        ax.plot([lo, hi], [j, j], lw=6, color="tab:green", alpha=0.8)
        ax.annotate(
            f"cone {s['apex_cone_deg']:.0f} deg", (hi, j),
            textcoords="offset points", xytext=(5, -3), fontsize=7)
    ax.set_yticks(range(len(idset)))
    ax.set_yticklabels([
        f"{s['dist_lo_mpc']:.0f}-{s['dist_hi_mpc']:.0f} Mpc" for s in idset
    ], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("bulk-flow amplitude identified interval (km/s)")
    ax.set_title("CF4 identified sets per depth shell (nuisance box)",
                 fontsize=8.5)
    ax.grid(alpha=0.25, axis="x")
    shells = growth["shells"]
    for s in shells:
        x = 0.5 * (s["dist_lo_mpc"] + s["dist_hi_mpc"])
        if s["constrained"]:
            ax2.errorbar([x], [s["fsigma8"]], yerr=[s["mock_sigma"]],
                         fmt="o", color="tab:blue", capsize=3)
        else:
            ax2.errorbar([x], [s["fsigma8"]], yerr=[s["mock_sigma"]],
                         fmt="o", mfc="none", color="tab:gray", capsize=3)
    ax2.axhline(growth["fiducial_fsigma8"], color="k", lw=0.8, ls="--",
                label=f"fiducial {growth['fiducial_fsigma8']:.3f}")
    ax2.set_xlabel("shell centre (Mpc)")
    ax2.set_ylabel(r"$f\sigma_8$")
    ax2.set_ylim(0, 4.6)
    ax2.set_title(
        "depth-resolved growth (filled = constrained under mock "
        "classification)", fontsize=8.5)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_cf4_depth",
        "Left: CF4 bulk-flow identified sets per pre-registered depth "
        "shell under the frozen nuisance box (distance-scale calibration, "
        "reconstruction observable, nonlinear dispersion), with the "
        "monopole always fit; every shell is bounded and the interval "
        "widens with depth. Apex cones annotated. Right: depth-resolved "
        "f sigma_8 from the safeguarded whitened amplitude fit with "
        "mock-calibrated errors; only the nearest shell is constrained. "
        "Set-valued diagnostics; a set containing a value is never a "
        "point estimate and no tension statement is made.",
    )


def fig_desi_dipole(outdir: Path) -> list[Path]:
    mock = _load("desi_dipole_mock_card.json")
    sel = _load("desi_exact_selection_card.json")
    null = mock["lcdm_clustering_mock_null"]
    obs = float(mock["observed_dipole_amplitude"])
    fig, ax = plt.subplots(figsize=(5.8, 3.3))
    biases = sorted(null.keys(), key=float)
    for j, b in enumerate(biases):
        m = null[b]
        ax.errorbar([j], [m["mock_dipole_mean"]],
                    yerr=[m["mock_dipole_std"]], fmt="s",
                    color="tab:gray", capsize=4,
                    label="clustering-mock null" if j == 0 else None)
        ax.annotate(f"p = {m['p_value']:.2f}", (j, m["mock_dipole_mean"]),
                    textcoords="offset points", xytext=(8, 6), fontsize=7)
    ax.axhline(obs, color="tab:red", lw=1.5,
               label=f"observed window-corrected D = {obs:.2e}")
    ax.set_xticks(range(len(biases)))
    ax.set_xticklabels([f"bias {b}" for b in biases], fontsize=8)
    ax.set_ylabel("number-count dipole amplitude")
    sc = sel["survey_conditional_null"]
    ax.set_title(
        "DESI DR1 BGS number-count dipole vs LCDM clustering mocks; "
        "exact-selection survey-conditional null: consistent = "
        f"{sc['consistent_with_survey_conditional_null']}", fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_desi_dipole",
        "The DESI DR1 BGS window-corrected number-count dipole against the "
        "in-house LCDM clustering-mock null at three bias values (mock "
        "mean and standard deviation; two-sided consistency p annotated) "
        "and the exact-selection survey-conditional pooled-rank "
        "consistency flag. The observed dipole is clustering-dominated "
        "and consistent with clustering cosmic variance; causal "
        "attribution is deferred to the complete official validation-mock "
        "ensemble (acquisition in progress). No kinematic or anisotropy "
        "claim.",
    )


def fig_act_kappa(outdir: Path) -> list[Path]:
    act = _load("act_kappa_card.json")
    p177 = _load("pr177_result_card.json")
    ells = sorted(int(k) for k in act["cl_debiased_data"])
    data = [act["cl_debiased_data"][str(l)] for l in ells]
    simm = [act["cl_debiased_sim_mean"][str(l)] for l in ells]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    ax.plot(ells, data, "o-", color="tab:red", label="ACT DR6 (debiased)")
    ax.plot(ells, simm, "s--", color="tab:gray", label="400-sim mean")
    ax.set_yscale("log")
    ax.set_xlabel("L")
    ax.set_ylabel(r"$C_L^{\kappa\kappa}$ (mean-field debiased)")
    rk = p177["rank_summary"]["controlled"]
    ax.set_title(
        f"low-L band p = {act['p_value_data_vs_isotropic_sims']:.2f}; "
        f"95% UL on excess band power {act['upper_limit_95cl']['band_power_95ul']:.2e}; "
        f"in-band modulation rank {rk['rank_fraction']}",
        fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_act_kappa",
        "ACT DR6 lensing-convergence low-L band powers after "
        "mean-field debiasing, against the 400-simulation ensemble mean; "
        "the band statistic is consistent with the isotropic simulation "
        "null and yields a 95% upper limit on excess L = 2..10 band "
        "power. The strict-in-band modulation rank (controlled variant) "
        "from the release-simulation ensemble is annotated. Consistency "
        "diagnostics on released reconstructed products; no anisotropy "
        "claim.",
    )


def fig_pr179(outdir: Path) -> list[Path]:
    ident = _load("pr179_response_identifiability.json")
    card = _load("pr179_result_card.json")
    folds = ident["folds"]
    xs = [f["fold"] for f in folds]
    qcc = [f["q_directional_cubic_canonical_correlation"] for f in folds]
    hcond = [f["h_condition_number"] for f in folds]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.2))
    ax.plot(xs, qcc, "o-", color="tab:red",
            label="q-block cubic canonical correlation")
    ax.axhline(0.95, color="k", ls="--", lw=0.9,
               label="falsifier threshold 0.95")
    ax.set_ylim(0.9, 1.0)
    ax.set_xlabel("fold")
    ax.set_title("q-block withheld: falsifier fails every fold", fontsize=8.5)
    ax.legend(fontsize=7)
    ax2.plot(xs, hcond, "s-", color="tab:blue",
             label="H-block condition number")
    ax2.set_xlabel("fold")
    fr = card["finite_rank"]
    ax2.set_title(
        f"H-only branch: exact rank {fr['finite_resolution_fraction']} "
        f"scaled estimate {fr['estimate']:.1e}\n"
        f"guard interval [{fr['guard_interval'][0]:.1e}, "
        f"{fr['guard_interval'][1]:.1e}] (conditional)", fontsize=8)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_pr179_conditional",
        "Raw-catalogue reconstruction-independent directional cosmography. "
        "Left: the pre-registered cubic falsifier's canonical correlation "
        "between the q-block and directional-cubic selection response "
        "exceeds the 0.95 threshold in every fold, so every q-level "
        "result is withheld. Right: the H-block passes identifiability in "
        "all folds; the H-only exact rank under the matched exchangeable "
        "null is shown with its finite-resolution guard interval. The "
        "H-only result is CONDITIONAL on unresolved selection systematics "
        "and is not a detection; resolution requires the survey-mock "
        "validation stages and independent adjudication.",
    )


def fig_omk_slaving(outdir: Path) -> list[Path]:
    coeff = _load("pr131_coefficients.json")
    w = np.linspace(-0.32, 1.0, 400)
    kappa = -2.0 / (5.0 + 3.0 * w)
    c2 = -2.0 * (9.0 * w**2 + 18.0 * w + 13.0) / (
        (3.0 * w + 5.0) ** 2 * (9.0 * w + 7.0)
    )
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.plot(w, kappa, color="tab:blue", label=r"$\kappa(w) = -2/(5+3w)$")
    ax.plot(w, c2, color="tab:orange",
            label=r"$c_2(w) = -2(9w^2+18w+13)/((3w+5)^2(9w+7))$")
    for wv, kv, label in [(0.0, -2.0 / 5.0, "dust"),
                          (1.0 / 3.0, -1.0 / 3.0, "radiation")]:
        ax.plot([wv], [kv], "o", color="tab:blue")
        ax.annotate(label, (wv, kv), textcoords="offset points",
                    xytext=(5, 5), fontsize=7)
    resonances = [-(2 * n + 3) / (6 * n - 3) for n in range(1, 6)]
    for j, wn in enumerate(resonances):
        ax.axvline(wn, color="tab:red", lw=0.7, alpha=0.5,
                   label="resonance family $w_n$" if j == 0 else None)
    ax.set_xlim(-1.75, 1.05)
    ax.set_ylim(-1.1, 0.3)
    ax.set_xlabel("equation-of-state parameter w")
    ax.set_title(
        "curvature-shear slaving coefficients and the exact resonance "
        "family (declared open domain (-1/3, 1))", fontsize=8.5)
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    cap_kappa = coeff["kappa_exact"]
    return _save(
        fig, outdir, "fig_v10_omk_slaving",
        "The exact slaved-mode expansion Sigma = kappa K + c2 K^2 of the "
        "LRS-III/Kantowski-Sachs reduced system: kappa(w) and c2(w) on the "
        "declared open domain, with the dust and radiation values marked "
        f"(exact kappa registry: {cap_kappa}) and the exact resonance "
        "family w_n = -(2n+3)/(6n-3) outside the domain shown. The "
        "second-order truncation carries an interval-arithmetic certified "
        "remainder tube on the registered compact domain. Class-conditional "
        "exact mathematics; no observational statement.",
    )


def fig_ricci_gaps(outdir: Path) -> list[Path]:
    card = _load("pr175_result_card.json")
    types = card["oracle"]["types"]
    names = list(types.keys())
    gaps = [max(float(types[t]["engine_b_gap_abs"]), 1e-16) for t in names]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.bar(range(len(names)), gaps, color="tab:cyan", alpha=0.85)
    ax.set_yscale("log")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("|coordinate-engine - exact| (absolute)")
    ax.set_title(
        "11-type spatial Ricci-scalar identity: independent "
        "coordinate/complex-step engine gap per canonical representative "
        "(exact Koszul engine equals the Ellis-MacCallum anchor "
        "identically on all 11)", fontsize=8)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    return _save(
        fig, outdir, "fig_v10_ricci_gaps",
        "Independent-engine verification of the exact spatial Ricci "
        "scalar on the 11 canonical Bianchi representatives: the exact "
        "Koszul frame engine agrees with the Ellis-MacCallum anchor "
        "formula identically (rational arithmetic), and the independent "
        "second-kind-coordinate engine with complex-step metric "
        "derivatives agrees to the plotted absolute gap (floored at 1e-16 "
        "for log display). Exact-mathematics verification; no "
        "observational content.",
    )


FIGURES = [
    fig_comparator_region,
    fig_k1_rank_hist,
    fig_k1_evenl,
    fig_boost_biposh,
    fig_cf4_depth,
    fig_desi_dipole,
    fig_act_kappa,
    fig_pr179,
    fig_omk_slaving,
    fig_ricci_gaps,
]


def build(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Path] = []
    for fn in FIGURES:
        artifacts.extend(fn(outdir))
    entries = {}
    for p in sorted(artifacts):
        entries[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        "schema": "htt.v10.report_figure_manifest.v1",
        "figure_dir": str(OUT.relative_to(REPO)),
        "artifact_sha256": entries,
        "inputs": [
            "docs/generated/mes_geodesic_refreeze_seal.json",
            "docs/generated/mes_branch_registry_seal.json",
            "docs/generated/k5_omega_k_ceiling_card.json",
            "docs/generated/pr147_identified_set.json",
            "docs/generated/pr148_fsigma8_by_depth.json",
            "docs/generated/k1_global_maxscan_e2e_full.json",
            "docs/generated/pr150_e2e_pooled_rank.json",
            "docs/generated/k1_evenl_biposh_rank_card.json",
            "docs/generated/pr180_result_card.json",
            "docs/generated/desi_dipole_mock_card.json",
            "docs/generated/desi_exact_selection_card.json",
            "docs/generated/act_kappa_card.json",
            "docs/generated/pr177_result_card.json",
            "docs/generated/pr179_response_identifiability.json",
            "docs/generated/pr179_result_card.json",
            "docs/generated/pr131_coefficients.json",
            "docs/generated/pr175_result_card.json",
        ],
        "determinism": "sealed-card reads only; Agg backend; no timestamps",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = build(OUT)
        MANIFEST.write_text(json.dumps(manifest, sort_keys=True, indent=1)
                            + "\n")
        print(f"wrote {len(manifest['artifact_sha256'])} artifacts + manifest")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        fresh = build(Path(tmp))
    stored = json.loads(MANIFEST.read_text())
    ok = True
    if stored["artifact_sha256"] != fresh["artifact_sha256"]:
        ok = False
        for name in sorted(set(stored["artifact_sha256"])
                           | set(fresh["artifact_sha256"])):
            a = stored["artifact_sha256"].get(name)
            b = fresh["artifact_sha256"].get(name)
            if a != b:
                print(f"drift: {name}")
    for name, digest in stored["artifact_sha256"].items():
        p = OUT / name
        if not p.exists() or hashlib.sha256(
                p.read_bytes()).hexdigest() != digest:
            ok = False
            print(f"on-disk mismatch: {name}")
    print(json.dumps({"mode": "check", "ok": ok}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
