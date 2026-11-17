#!/usr/bin/env python3
"""Summarize executed R62 results and render publication-oriented figures."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np


def span(values):
    values = list(map(float, values))
    return [min(values), max(values)]


def run(base):
    base = Path(base).resolve()
    src = json.loads((base / "RESULTS/SOURCE/SOURCE_TENSOR_RESULT.json").read_text())
    cls = json.loads((base / "RESULTS/CLASSIFICATION/CLASSIFICATION_SUMMARY.json").read_text())
    variants = list(src["variants"])
    kinds = ("raw_windows", "raw_differences", "J2_coefficients", "J2_varying", "J3_coefficients", "J3_varying")
    names = ("ZERO", "SHARED_FRAME", "SHARED_AXIS", "SHARED_ZERO_EIGENVALUE_SHAPE", "SHARED_GENERAL_SHAPE")
    aggregate = {}
    max_gap, max_q_error, unresolved_ranges, computed_ranges = 0., 0., 0, 0
    for kind in kinds:
        items = [cls["experiments"][name + "/" + kind] for name in variants]
        aggregate[kind] = {
            "dimension": items[0]["dimension"], "cutoff": items[0]["cutoff"],
            "zero_nominal_p_range": span(x["zero_nominal_p"] for x in items),
            "classes": {c: {"status_counts": dict(Counter(x["classes"][c]["status"] for x in items)),
                "feasible_distance2_upper_range": span(x["classes"][c]["feasible_distance2_upper"] for x in items),
                "ratio_range": span(x["classes"][c]["ratio_to_cutoff"] for x in items)} for c in names}}
        for item in items:
            receipt = base / "RESULTS/CLASSIFICATION" / item["receipt"]
            if hashlib.sha256(receipt.read_bytes()).hexdigest() != cls["receipt_sha256"][item["receipt"]]:
                raise ValueError("classification receipt identity mismatch")
            record = json.loads(receipt.read_text())
            v = record["verification"]
            max_gap = max(max_gap, v["max_quadratic_primal_dual_gap"])
            max_q_error = max(max_q_error, v["stored_witness_quadratic_max_abs_difference"])
            unresolved_ranges += v["quadratic_enclosures_unresolved"]
            computed_ranges += v["quadratic_enclosures_computed"]
    source_audit = {
        "n_sources": src["n_sources"],
        "J2_condition_scaled": span(x["fits"]["2"]["condition_scaled"] for x in src["variants"].values()),
        "J3_condition_scaled": span(x["fits"]["3"]["condition_scaled"] for x in src["variants"].values()),
        "J2_adequacy_p": span(x["fits"]["2"]["adequacy_p"] for x in src["variants"].values()),
        "J3_adequacy_p": span(x["fits"]["3"]["adequacy_p"] for x in src["variants"].values()),
        "J2_over_J1_p": span(x["nested_linear_tests"]["J2_over_J1"]["nominal_p"] for x in src["variants"].values()),
        "J3_over_J2_p": span(x["nested_linear_tests"]["J3_over_J2"]["nominal_p"] for x in src["variants"].values()),
        "operator_parity_max_abs": max(float(v) for x in src["variants"].values() for v in x["source_parity"].values()),
        "R61_coordinate_mean_scaled_error_max": max(x["R61_coordinate_control"]["estimate_scaled_max_abs"] for x in src["variants"].values()),
        "R61_coordinate_covariance_scaled_error_max": max(x["R61_coordinate_control"]["covariance_scaled_max_abs"] for x in src["variants"].values()),
        "common_calibration_varying_error_max": max(x["fits"][str(j)]["constant_calibration_varying_max_abs"] for x in src["variants"].values() for j in (1, 2, 3)),
        "injection_scaled_recovery_max": max(x["actual_operator_commuting_source_injection"]["scaled_parameter_recovery_max_abs"] for x in src["variants"].values()),
        "injection_max_apparent_commutator_range": span(max(x["actual_operator_commuting_source_injection"]["apparent_commutator_norms"]) for x in src["variants"].values()),
        "injection_max_recovered_commutator": max(max(x["actual_operator_commuting_source_injection"]["recovered_source_commutator_norms"]) for x in src["variants"].values())}
    report = {"schema": "htt.r62.interpretation_summary/1", "experiments": aggregate,
              "source_audit": source_audit,
              "numerics": {"computed_commutator_enclosures": computed_ranges, "unresolved_commutator_enclosures": unresolved_ranges,
                           "max_quadratic_primal_dual_gap": max_gap, "max_witness_quadratic_crosscheck_error": max_q_error},
              "decision": "All 168 structured-class queries have feasible intersection witnesses; no preferred Bianchi type, no robust tensor-zero exclusion across the nuisance union, and no detected varying tensor response.",
              "no_extra_tests": "Stage8 interprets the executed source-order sensitivity and verifies saved receipt identities; no optional optimizer rerun or new Monte Carlo family."}
    (base / "RESULTS/INTERPRETATION_SUMMARY.json").write_text(json.dumps(report, indent=2) + "\n")
    figures = base / "FIGURES"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 12, "savefig.dpi": 180, "svg.fonttype": "none"})
    short_variants = ["base", "+ monopole", "split", "survey", "monopole + radial", "monopole + Galactic", "monopole + error"]
    xlabels = ["Zero", "Common\nframe", "Common\naxis", "Fixed shape\n(det = 0)", "Common\nshape"]
    fig, axes = plt.subplots(1, 2, figsize=(12.7, 5.3), sharey=True)
    for ax, kind, label in zip(axes, ("J2_coefficients", "J3_coefficients"), ("Quadratic source response (J = 2)", "Cubic source sensitivity (J = 3)")):
        data = np.array([[cls["experiments"][n + "/" + kind]["classes"][c]["ratio_to_cutoff"] for c in names] for n in variants])
        im = ax.imshow(data, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=0., vcenter=1., vmax=1.5), aspect="auto")
        for i in range(7):
            for j in range(5):
                ax.text(j, i, f"{data[i,j]:.3f}", ha="center", va="center", color="white" if data[i,j] < .22 or data[i,j] > 1.3 else "black", fontsize=10)
        ax.set_xticks(range(5), xlabels)
        ax.set_yticks(range(7), short_variants)
        ax.set_title(label)
        ax.tick_params(length=0)
    fig.suptitle("Squared Mahalanobis witness distance / 95% confidence cutoff", fontsize=15, y=.97)
    fig.subplots_adjust(left=.16, right=.91, bottom=.20, top=.86, wspace=.12)
    cax = fig.add_axes([.93, .24, .015, .56])
    fig.colorbar(im, cax=cax, label="Distance ratio")
    fig.text(.16, .075, "Ratio <= 1 proves intersection. Nonlinear entries are feasible upper bounds, not global minima or model odds.", fontsize=9)
    fig.text(.16, .035, "The zero state is nuisance/order sensitive; all four structured classes intersect each source confidence set.", fontsize=9)
    for ext in ("png", "svg"):
        fig.savefig(figures / ("source_class_compatibility." + ext))
    plt.close(fig)

    apparent = [max(src["variants"][n]["actual_operator_commuting_source_injection"]["apparent_commutator_norms"]) for n in variants]
    recovered = [max(src["variants"][n]["actual_operator_commuting_source_injection"]["recovered_source_commutator_norms"]) for n in variants]
    fig, ax = plt.subplots(figsize=(11.3, 4.8))
    xx = np.arange(7)
    ax.scatter(xx, apparent, s=60, marker="s", label="Apparent window tensors", color="#c04a31", zorder=3)
    ax.scatter(xx, recovered, s=65, marker="o", label="Recovered source coefficients (roundoff)", color="#176ea5", zorder=3)
    ax.set_yscale("log")
    ax.set_xticks(xx, ["base", "mono", "split", "survey", "mono+radial", "mono+Galactic", "mono+error"])
    ax.set_ylabel("Maximum pairwise commutator norm\n(dimensionless response squared)")
    ax.set_title("A commuting source can produce noncommuting observed windows")
    ax.grid(axis="y", which="major", alpha=.25)
    ax.legend(loc="center left", frameon=False)
    fig.subplots_adjust(left=.12, right=.98, bottom=.23, top=.87)
    fig.text(.12, .08, "Noise-free constructed source through the actual CF4 operators. The exact source commutators are zero.", fontsize=10)
    fig.text(.12, .035, "This validates response handling; it is neither an observed cosmic frame rotation nor a stochastic survey forecast.", fontsize=9)
    for ext in ("png", "svg"):
        fig.savefig(figures / ("actual_operator_injection." + ext))
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    run(parser.parse_args().base)
