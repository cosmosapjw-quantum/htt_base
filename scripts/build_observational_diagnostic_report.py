#!/usr/bin/env python3
"""Present existing CF4/CMB diagnostics beside a DESI released-summary analysis.

This command reads three JSON products, validates the fields used by the figures,
and writes a fresh report directory. It never refits catalogues or component maps,
combines their likelihoods, or runs the manufactured CF4 injection.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


SAMPLES = ("full", "dA_20_200_Mpc", "central_49_51_percent")
SAMPLE_LABELS = ("Full grouped catalogue", "Fiducial dA: 20–200 Mpc", "Central 49–51% distance slice")
METHODS = ("CAL", "SNIA", "FP", "TF", "SBFO", "SBFI", "SNII")
SCENARIOS = ("mu_published_v100_motion300_fixed_cal", "free_common", "free_common_and_method_presence")
SCENARIO_LABELS = ("Fixed calibration", "Free common zero point", "Free common + method presence")
SCALES = [1000.] * 4 + [100.] * 9
CONVENTION = ("Real orthonormal harmonics: for each ell, Y(ell,0), sqrt(2) Re Y(ell,m), "
              "sqrt(2) Im Y(ell,m) for m=1..ell; Galactic source directions; K_CMB.")
CAVEATS = [
    "CF4 coverage and conditional response sensitivity are descriptive, not a fitted observed flow or posterior.",
    "CF4 fiducial dA uses catalogue modulus and Vh/c; it is not an observed latent area distance.",
    "CF4 method-presence counts overlap and are not fractional calibration weights; selections overlap too.",
    "The CMB products share one sky. Their contrasts are not independent measurements, bias estimates, or significance.",
    "DESI results are conditional on its released fixed Gaussian scalar summary; no posterior or raw-catalogue coverage is claimed.",
    "No joint likelihood, joint posterior, native transfer, tilt detection, or family identification is produced.",
]


def _finite_tree(value, path="input"):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path}: nonfinite JSON number")
    if isinstance(value, dict):
        for key, item in value.items():
            _finite_tree(item, f"{path}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _finite_tree(item, f"{path}[{i}]")


def _number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name}: finite number required")
    if positive and value <= 0:
        raise ValueError(f"{name}: positive value required")
    return float(value)


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name}: integer >= {minimum} required")
    return value


def _hashes(value, name):
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{name}: source identity map required")
    for path, digest in value.items():
        if not path or not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"{name}: SHA256 identity required")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError(f"{name}: invalid SHA256") from exc


def _load(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise ValueError(f"{path}: top-level object required")
    _finite_tree(result)
    return result, {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def validate_cf4(record):
    if record.get("task") != "R2-02" or record.get("transfer_source") != "none":
        raise ValueError("expected R2-02 diagnostic with no transfer")
    if not str(record.get("actual_posterior_status", "")).startswith("HOLD"):
        raise ValueError("CF4 diagnostic must preserve its unresolved posterior status")
    _hashes(record["source"]["source_sha256"], "CF4 source hashes")
    total = _integer(record["groups"], "CF4 groups", 1)
    all_coverage = record["coverage"]
    by_sample = {row["sample"]: row for row in all_coverage}
    if len(by_sample) != len(all_coverage):
        raise ValueError("CF4 duplicate coverage sample")
    coverage = []
    for name in SAMPLES:
        row = by_sample[name]
        n = _integer(row["groups"], name + ".groups", 1)
        if n > total or (name == "full" and n != total):
            raise ValueError("CF4 inconsistent group counts")
        distances = row["fiducial_dA_min_median_max_Mpc"]
        if len(distances) != 3:
            raise ValueError("CF4 min/median/max requires three values")
        d = [_number(x, "fiducial dA", True) for x in distances]
        if not d[0] <= d[1] <= d[2]:
            raise ValueError("CF4 unordered distance summary")
        counts = {method: _integer(row["method_presence_counts"][method], method) for method in METHODS}
        if any(count > n for count in counts.values()):
            raise ValueError("CF4 method-presence count exceeds its group count")
        coverage.append({"sample": name, "groups": n, "fiducial_dA_min_median_max_Mpc": d,
                         "method_presence_counts": counts})
    all_sensitivity = record["sensitivity"]
    by_key = {(row["sample"], row["scenario"]["name"]): row for row in all_sensitivity}
    if len(by_key) != len(all_sensitivity):
        raise ValueError("CF4 duplicate sensitivity sample/scenario")
    sensitivity = []
    for sample in SAMPLES:
        for scenario in SCENARIOS:
            row = by_key[sample, scenario]
            sv = np.asarray(row["singular_values"], dtype=float)
            if sv.shape != (13,) or not np.all(np.isfinite(sv)) or np.any(sv < 0) or np.any(np.diff(sv) > 0):
                raise ValueError("CF4 requires 13 finite ordered nonnegative singular values")
            scales = row["fixed_coefficient_scales"]
            if scales != SCALES:
                raise ValueError("CF4 fixed coefficient scales differ from the endpoint13 display contract")
            tolerance = _number(row["rank_tolerance"], "rank tolerance", True)
            rank = _integer(row["rank"], "CF4 rank")
            if rank != int(np.count_nonzero(sv > tolerance)):
                raise ValueError("CF4 stored numerical rank inconsistent with singular values/tolerance")
            if row["rows"] != by_sample[sample]["groups"]:
                raise ValueError("CF4 sensitivity rows differ from coverage")
            sensitivity.append({key: row[key] for key in ("sample", "scenario", "singular_values", "rank",
                                "rank_tolerance", "fixed_coefficient_scales", "rows", "nuisance_rank")})
    return {"groups": total, "coverage": coverage, "sensitivity": sensitivity,
            "coefficient_order": ["b0", "Bx", "By", "Bz", "H", "Ax", "Ay", "Az", "STF1", "STF2", "STF3", "STF4", "STF5"],
            "coefficient_scale_units": ["km/s"] * 4 + ["km/s/Mpc"] * 9,
            "source": record["source"], "distance": record["distance"], "frame": record["frame"],
            "actual_posterior_status": record["actual_posterior_status"],
            "actual_remainder": record["actual_remainder"], "source_runtime": record.get("runtime"),
            "scope": record["scope"], "claim_tier": record["claim_tier"],
            "computation": "REUSED_INPUT_DIAGNOSTIC; no catalogue fit, SVD, covariance, or injection rerun"}


def validate_cmb(record):
    if record.get("scope") != "DESCRIPTIVE_REDUCED_SAME_SKY_CONTROL":
        raise ValueError("expected reduced same-sky CMB diagnostic")
    if record.get("product_independence") is not False or record.get("cross_product_covariance") is not None:
        raise ValueError("unsupported CMB independence/covariance contract")
    _hashes(record["source_identities"], "CMB source hashes")
    processing, coverage = record["processing"], record["coverage"]
    if (processing["id"] != "R8_SAME_SKY_PIXEL_CONTROL_V1" or processing["nside"] != 64
            or processing["fit_ells"] != [0, 5] or processing["retained_ells"] != [2, 5]):
        raise ValueError("unsupported CMB processing/ell contract")
    products = processing["input_products"]
    if len(products) != 4 or len(set(products)) != 4:
        raise ValueError("CMB requires four distinct product IDs, not independent skies")
    valid = _integer(coverage["common_valid_pixels"], "valid pixels", 1)
    if (coverage["pixel_count"] != 12 * 64 ** 2 or valid > coverage["pixel_count"]
            or valid != processing["valid_pixels"] or coverage["retained_ells"] != [2, 5]):
        raise ValueError("CMB inconsistent mask coverage")
    fits = processing["fits"]
    by_product = {row["sample_id"]: row for row in fits}
    if len(fits) != 4 or set(by_product) != set(products):
        raise ValueError("CMB fit/product identity mismatch")
    retained = {}
    for product in products:
        coeff = np.asarray(by_product[product]["all_coefficients_K"], dtype=float)
        if coeff.shape != (36,) or not np.all(np.isfinite(coeff)):
            raise ValueError("CMB requires 36 finite real harmonic coefficients")
        retained[product] = coeff[4:].tolist()
    seen, contrasts = set(), []
    for row in record["contrasts"]:
        a, b = row["products"]
        pair = frozenset((a, b))
        if a == b or a not in retained or b not in retained or pair in seen:
            raise ValueError("CMB invalid or duplicated contrast pair")
        seen.add(pair)
        norm = _number(row["retained_difference_norm_K"], "CMB contrast norm")
        quad = _number(row["quadrupole_difference_frobenius_K"], "CMB quadrupole norm")
        if min(norm, quad) < 0:
            raise ValueError("CMB contrast norms must be nonnegative")
        # A report-input consistency check, not a new map reduction or uncertainty estimate.
        difference = np.asarray(retained[a]) - retained[b]
        if not np.isclose(np.linalg.norm(difference), norm, rtol=2e-10, atol=1e-15):
            raise ValueError("CMB stored contrast disagrees with retained coefficients")
        contrasts.append({"products": [a, b], "retained_difference_norm_K": norm,
                          "quadrupole_difference_frobenius_K": quad})
    if len(seen) != 6:
        raise ValueError("CMB requires all six descriptive pairs")
    return {"products": products, "retained_coefficients_K": retained, "contrasts": contrasts,
            "coverage": coverage, "processing": processing, "harmonic_convention": CONVENTION,
            "harmonic_convention_source": "htt/obsstat/r7_cmb_product_response.py:real_design",
            "source_identities": record["source_identities"], "source_runtime": record.get("runtime"),
            "source_code_identities": record.get("code_identities"), "source_release": record["source_release"],
            "posterior_status": record["posterior_status"], "full_field_F4_status": record["full_field_F4_status"],
            "product_independence": False, "cross_product_covariance": None,
            "computation": "REUSED_INPUT_DIAGNOSTIC; no FITS reduction, harmonic fit, or covariance estimation rerun"}


def validate_desi(record):
    if (record.get("artifact_mode") != "RELEASED_SUMMARY_REEXPRESSION"
            or record.get("transfer_source") != "none"
            or record.get("law", {}).get("conditioning_target") != "PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE"):
        raise ValueError("expected DESI released fixed-Gaussian summary analysis")
    measurement = record["measurement"]
    for key in ("qiso", "qiso_sigma", "DV_over_rd", "DV_over_rd_sigma", "DV_over_rd_fid", "zeff"):
        _number(measurement[key], "DESI " + key, True)
    fid = measurement["DV_over_rd_fid"]
    if (not math.isclose(measurement["DV_over_rd"], fid * measurement["qiso"], rel_tol=1e-12)
            or not math.isclose(measurement["DV_over_rd_sigma"], fid * measurement["qiso_sigma"], rel_tol=1e-12)):
        raise ValueError("DESI affine re-expression is inconsistent")
    _hashes({"DESI source": record["source"]["source_sha256"]}, "DESI source")
    intervals = record["conditional_intervals"]
    if not intervals:
        raise ValueError("DESI conditional intervals required")
    for row in intervals:
        if not 0 < _number(row["coverage"], "coverage") < 1:
            raise ValueError("invalid DESI interval coverage")
        for key in ("qiso", "DV_over_rd"):
            bounds = row[key]
            if len(bounds) != 2 or not 0 <= bounds[0] < bounds[1]:
                raise ValueError("invalid DESI interval")
        if not np.allclose(np.asarray(row["qiso"]) * fid, row["DV_over_rd"], rtol=1e-12, atol=0):
            raise ValueError("DESI interval affine re-expression is inconsistent")
    return {"measurement": measurement, "conditional_intervals": intervals, "source": record["source"],
            "source_provenance": record.get("provenance"), "claim_tier": record["claim_tier"],
            "scope": record["scope"], "computation": "INGESTED_RELEASE_SUMMARY_ANALYSIS; no new likelihood evaluation by report command"}


def _save(fig, directory, stem):
    for suffix in ("png", "pdf"):
        fig.savefig(directory / f"{stem}.{suffix}", dpi=190)


def make_figures(data, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    cf4, cmb = data["cf4"], data["cmb"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.3), gridspec_kw={"width_ratios": [1.05, 1.5]})
    for i, row in enumerate(cf4["coverage"]):
        lower, middle, upper = row["fiducial_dA_min_median_max_Mpc"]
        axes[0].plot([lower, upper], [i, i], color="#28638e", lw=3)
        axes[0].scatter([middle], [i], color="#bc653e", s=44, zorder=3)
    axes[0].set(xscale="log", xlabel="Fiducial area-distance coordinate [Mpc]", yticks=range(3),
                yticklabels=[f"{label}\nN = {row['groups']:,}" for label, row in zip(SAMPLE_LABELS, cf4["coverage"])],
                ylim=(2.6, -.6), title="Range and median; overlapping selections")
    axes[0].grid(axis="x", alpha=.2)
    counts = np.array([[row["method_presence_counts"][m] for m in METHODS] for row in cf4["coverage"]])
    plot = axes[1].imshow(np.log10(1 + counts), cmap="Blues", aspect="auto", vmin=0)
    for (i, j), count in np.ndenumerate(counts):
        axes[1].text(j, i, f"{count:,}", ha="center", va="center", fontsize=8,
                     color="white" if plot.norm(math.log10(1 + count)) > .65 else "#152b3c")
    axes[1].set(xticks=range(7), xticklabels=METHODS, yticks=range(3), yticklabels=["Full", "20–200 Mpc", "49–51%"],
                title="Method presence: overlapping group counts")
    fig.colorbar(plot, ax=axes[1], fraction=.035, pad=.02, label="log10(1 + count)")
    fig.suptitle("Cosmicflows-4 grouped-product sampling coverage", fontsize=14)
    fig.text(.5, .08, "Reused R2-02 values | Catalogue-point coordinates | Lines: min–max; dots: median | No fitted flow", ha="center", fontsize=8)
    fig.text(.5, .045, "Table 3 supplies method presence only. Group selections and method counts are not independent data sets.", ha="center", fontsize=8)
    fig.subplots_adjust(left=.19, right=.925, bottom=.23, top=.80, wspace=.52)
    _save(fig, directory, "cf4_coverage"); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12, 5.2), sharey=True)
    colors = ("#28638e", "#bd663e", "#408478")
    for ax, sample, label in zip(axes, SAMPLES, SAMPLE_LABELS):
        for scenario, name, color in zip(SCENARIOS, SCENARIO_LABELS, colors):
            row = next(x for x in cf4["sensitivity"] if x["sample"] == sample and x["scenario"]["name"] == scenario)
            sv, tol = np.array(row["singular_values"]), row["rank_tolerance"]
            x = np.arange(1, 14)
            ax.plot(x, np.maximum(sv, tol), marker="o", ms=3, color=color, label=f"{name} (rank {row['rank']})")
            below = sv <= tol
            ax.scatter(x[below], np.full(np.count_nonzero(below), tol), marker="v", color=color, s=48, zorder=4)
        ax.set(yscale="log", xlabel="Singular-value index", xticks=[1, 4, 7, 10, 13], title=label)
        ax.grid(alpha=.2)
        ax.legend(fontsize=7, loc="lower left")
    axes[0].set_ylabel("Scaled, noise-whitened singular value [dimensionless]")
    fig.suptitle("CF4 endpoint13 response: conditional sampling sensitivity", fontsize=14)
    fig.text(.5, .105, "Published modulus errors; scenario velocity/motion errors = 100/300 km/s. Same fixed coefficient scales in every panel.", ha="center", fontsize=8)
    fig.text(.5, .070, "Downward triangles: singular values at/below numerical rank tolerance, displayed at that tolerance (raw values retained).", ha="center", fontsize=8)
    fig.text(.5, .035, "Reused R2-02 SVD; no response fit. Free common calibration leaves one unestimable direction; a full-rank scenario is not a detection.", ha="center", fontsize=8)
    fig.subplots_adjust(left=.07, right=.985, bottom=.25, top=.81, wspace=.18)
    _save(fig, directory, "cf4_sensitivity"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), gridspec_kw={"width_ratios": [1.0, 1.25]})
    labels = ["–".join(x.replace("PR3_", "") for x in row["products"]) for row in cmb["contrasts"]]
    x = np.arange(6)
    axes[0].barh(x - .18, [row["retained_difference_norm_K"] * 1e6 for row in cmb["contrasts"]], .34,
                 label="ell 2–5 coefficient norm", color="#28638e")
    axes[0].barh(x + .18, [row["quadrupole_difference_frobenius_K"] * 1e6 for row in cmb["contrasts"]], .34,
                 label="Quadrupole STF norm", color="#bd663e")
    axes[0].set(yticks=x, yticklabels=labels, xlabel="Descriptive difference norm [microK]", title="Six contrasts of four same-sky products")
    axes[0].invert_yaxis()
    axes[0].legend(fontsize=8, ncol=2, loc="upper left", bbox_to_anchor=(0, 1.22), frameon=False)
    axes[0].grid(axis="x", alpha=.2)
    for product in cmb["products"]:
        axes[1].plot(np.arange(1, 33), np.array(cmb["retained_coefficients_K"][product]) * 1e6,
                     marker=".", lw=1, ms=4, label=product.replace("PR3_", ""))
    for boundary in (5.5, 12.5, 21.5):
        axes[1].axvline(boundary, color="gray", lw=.6, ls=":")
    axes[1].set(xlabel="Stored real-harmonic coefficient index (ell 2–5)", ylabel="Coefficient [microK]",
                title="Common-mask simultaneous ell 0–5 fits")
    axes[1].legend(fontsize=8, ncol=2); axes[1].grid(alpha=.2)
    fig.suptitle("Planck PR3 component-product contrasts", fontsize=14)
    fig.text(.5, .105, f"Reused R2-03 controls | NSIDE 64 | Common pixels: {cmb['coverage']['common_valid_pixels']:,}/49,152 | Galactic, K_CMB", ha="center", fontsize=8)
    fig.text(.5, .070, "Released maps followed by pixel averaging; no beam deconvolution. Same sky; no covariance or significance inferred.", ha="center", fontsize=8)
    fig.text(.5, .035, "The STF tensor is a temperature quadrupole, not velocity shear. Residual fitted ell 1 is not a restored physical dipole.", ha="center", fontsize=8)
    fig.subplots_adjust(left=.16, right=.985, bottom=.25, top=.81, wspace=.36)
    _save(fig, directory, "cmb_same_sky"); plt.close(fig)


def report_text(data, metadata, directory):
    cf4, cmb, desi = data["cf4"], data["cmb"], data["desi"]
    m = desi["measurement"]
    lines = ["# Retained observations: released-summary result and descriptive diagnostics", "",
             f"DESI BGS Bright gives D_V/r_d = **{m['DV_over_rd']:.6f} ± {m['DV_over_rd_sigma']:.6f}** at z_eff = {m['zeff']:.9f}, conditional on its released Gaussian scalar summary.",
             f"The CF4 panels describe {cf4['groups']:,} grouped observations. The CMB panels compare four reconstructions of one sky.",
             "This report assembles distinct scientific products; it performs no cross-probe likelihood multiplication or physical joint fit.", "",
             "## Evidence reuse and computation", "",
             "| Component | Input | Computation in this report | Scientific use |", "|---|---|---|---|",
             "| DESI | Supplied analysis.json from the original-H5 runner | Read scalar values and intervals; check affine consistency | Released-summary conditional likelihood |",
             "| CF4 | Supplied R2-02 diagnostic | Plot stored coverage and singular values | Sampling and local conditional sensitivity |",
             "| CMB | Supplied R2-03 diagnostic | Check stored norm consistency; convert K to microK; plot | Same-sky descriptive contrasts |", "",
             "Input execution times, revisions and source hashes are preserved as inherited evidence in figure_data.json. They are not recorded as executions performed by this command.",
             "The command newly creates the figures and this report. It does not claim a fresh raw-data audit, a repeated SVD/harmonic fit, or a fresh independent review of the underlying results.", "",
             "## DESI scalar released-summary result", "",
             f"qiso = {m['qiso']:.9f} ± {m['qiso_sigma']:.9f}; (D_V/r_d)_fid = {m['DV_over_rd_fid']:.9f}. Both views encode one datum.", "",
             "| Conditional coverage | qiso | D_V/r_d |", "|---|---|---|"]
    for row in desi["conditional_intervals"]:
        lines.append(f"| {100 * row['coverage']:.5f}% | [{row['qiso'][0]:.8f}, {row['qiso'][1]:.8f}] | [{row['DV_over_rd'][0]:.6f}, {row['DV_over_rd'][1]:.6f}] |")
    desi_dir = Path(metadata["inputs"]["desi"]["path"]).parent
    image = desi_dir / "desi_bao_summary.png"
    if image.is_file():
        lines += ["", f"![DESI relative likelihood: two coordinates of one observation]({Path(os.path.relpath(image, directory)).as_posix()})"]
    lines += ["", "Intervals are pointwise Gaussian acceptance inversions in the positive prediction domain, not posterior credible intervals. A zero lower boundary, if present, is open.",
              "The syst product is consumed once; its statistical-only alternative and raw catalogue are not additional independent factors. Historical R9 family allocation is unchanged.", "",
              "## CF4 coverage and conditional sensitivity", "", "![CF4 sampling coverage](cf4_coverage.png)", "",
              "The range plot shows the minimum, median and maximum fiducial area-distance coordinate. The method matrix counts groups with each method present; overlaps are allowed.",
              cf4["distance"] + ". " + cf4["frame"] + ".", "",
              "![CF4 endpoint13 singular spectra](cf4_sensitivity.png)", "",
              "All panels use endpoint13 coefficient order b0, Bx, By, Bz, H, Ax, Ay, Az, STF1..5. The first four fixed scales are 1000 km/s; the remaining nine are 100 km/s/Mpc.",
              "These noise-whitened, scaled singular values depend on the declared velocity/motion error and calibration scenario. Values at or below each stored rank tolerance are displayed at that tolerance with downward triangles, while their unmodified values remain in figure_data.json.", "",
              "| Sample | Groups | Fixed-calibration numerical rank | Free-common rank | Free-common + method-presence rank |", "|---|---:|---:|---:|---:|"]
    for sample, label in zip(SAMPLES, SAMPLE_LABELS):
        rows = [next(x for x in cf4["sensitivity"] if x["sample"] == sample and x["scenario"]["name"] == s) for s in SCENARIOS]
        lines.append(f"| {label} | {rows[0]['rows']:,} | {rows[0]['rank']} | {rows[1]['rank']} | {rows[2]['rank']} |")
    lines += ["", "The scale-sensitive spectra diagnose how the selected response separates its coefficients. Numerical rank is not a calibrated physical identifiability or detection statement.",
              f"Actual CF4 posterior status remains `{cf4['actual_posterior_status']}`. Remainder: {cf4['actual_remainder']}.", "",
              "## CMB product contrasts", "", "![Same-sky component-map contrasts](cmb_same_sky.png)", "", CONVENTION, "",
              "Each fit includes ell 0..5 simultaneously on the common mask; only ell 2..5 are plotted. The ell 2, 3, 4 and 5 blocks contain 5, 7, 9 and 11 coefficients.",
              "The six pair contrasts share maps and sky. A contrast can diagnose reconstruction sensitivity but cannot determine common bias or yield six independent likelihood factors.",
              "Neither coefficient norms nor temperature-quadrupole STF norms measure velocity shear. A fitted residual dipole is not the physical dipole needed by an absolute-temperature statistic.",
              f"CMB posterior status remains `{cmb['posterior_status']}`; full-field F4 status remains `{cmb['full_field_F4_status']}`.", "",
              "## Inputs needed for physical inference", "",
              "CF4 needs a selected source/count model or justified subset, a true-redshift/heliocentric-velocity convention and error law, shared group/flow covariance, calibrated aggregate-modulus zero-point law, an absolute-scale anchor, and a finite-distance remainder or named truncation scenario.",
              "CMB physical inference needs the released-product response and common-sky measurement law. Absolute-temperature/F4 claims additionally need physical dipole and angular-mean inputs plus omitted-mode control. These are distinct from the temperature-coefficient diagnostics already shown.",
              "A joint posterior additionally needs one common physical response and prior, cross-product dependence/overlap treatment, and one integration over each shared nuisance. No absent component is replaced by zero or independence.", "",
              "## Provenance", "", "| Consumed JSON | SHA256 | Bytes |", "|---|---|---:|"]
    for name, identity in metadata["inputs"].items():
        lines.append(f"| {name}: `{identity['path']}` | `{identity['sha256']}` | {identity['bytes']} |")
    lines += ["", "The source-report byte identities above were computed in this command. Upstream catalogue/map hashes and historical code revisions are inherited from those reports, not freshly recomputed.",
              "Figure payloads, units and component-specific claim status are in [figure_data.json](figure_data.json); execution and figure identities are in [report.json](report.json).", "",
              "```sh", metadata["generating_command"], "```", "", *["- " + x for x in CAVEATS], ""]
    return "\n".join(lines)


def run(desi_result, cf4_result, cmb_result, output_dir):
    directory = Path(output_dir).resolve()
    if directory.exists():
        raise FileExistsError("output directory already exists; select a new run-specific directory")
    paths = {"desi": Path(desi_result).resolve(), "cf4": Path(cf4_result).resolve(), "cmb": Path(cmb_result).resolve()}
    loaded = {name: _load(path) for name, path in paths.items()}
    data = {"desi": validate_desi(loaded["desi"][0]), "cf4": validate_cf4(loaded["cf4"][0]),
            "cmb": validate_cmb(loaded["cmb"][0])}
    command = [sys.executable, str(Path(__file__).resolve()), "--desi-result", str(paths["desi"]),
               "--cf4-result", str(paths["cf4"]), "--cmb-result", str(paths["cmb"]), "--output-dir", str(directory)]
    metadata = {"schema": "htt.observational_diagnostic_report/v1", "owner": "manuscript", "claim_tier": "C0",
                "scope": "DESCRIPTIVE_REPORT_WITH_SEPARATELY_LABELED_DESI_CONDITIONAL_SUMMARY",
                "transfer_source": "none", "status": "COMPLETE_REPORT_ONLY", "scientific_claim_promotion": False,
                "joint_likelihood": "NOT_PERFORMED", "posterior": "NOT_PERFORMED", "raw_data_reexecution": False,
                "inputs": {name: pair[1] for name, pair in loaded.items()},
                "upstream_identities_status": "INHERITED_NOT_REHASHED", "caveats": CAVEATS,
                "generated_utc": datetime.now(timezone.utc).isoformat(), "generating_command": shlex.join(command),
                "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "environment": {"executable": sys.executable, "python": platform.python_version(),
                                "packages": {name: importlib.metadata.version(name) for name in ("numpy", "matplotlib")}},
                "figure_operations": ["Replot stored numbers", "K to microK", "Rank-tolerance display floor with explicit markers"],
                "synthetic_validation_in_scientific_report": "EXCLUDED_CF4_MANUFACTURED_INJECTION"}
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "figure_data.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    make_figures(data, directory)
    (directory / "report.md").write_text(report_text(data, metadata, directory), encoding="utf-8")
    metadata["outputs"] = {path.name: {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                           for path in sorted(directory.iterdir()) if path.is_file()}
    (directory / "report.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("desi-result", "cf4-result", "cmb-result", "output-dir"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run(args.desi_result, args.cf4_result, args.cmb_result, args.output_dir)
    except (ValueError, KeyError, TypeError, OSError, ImportError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": result["status"], "output_dir": str(args.output_dir.resolve()),
                      "raw_data_reexecution": False, "scientific_claim_promotion": False}))


if __name__ == "__main__":
    main()
