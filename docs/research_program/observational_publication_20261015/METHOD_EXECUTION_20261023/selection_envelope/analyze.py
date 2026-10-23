"""Exact finite-cohort density-ratio envelopes for the reviewed R24 OOF rows.

The empirical law is uniform over the 274 released rows. This program does not
estimate a sampling propensity or a physical population distribution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linprog


HERE = Path(__file__).resolve().parent
METHOD = HERE.parent
ROOT = next(p for p in METHOD.parents if p.name == "htt_base")
INPUT = METHOD / "R24-SELECTION-ENVELOPE_INPUT.json"
INPUT_SHA = "b02fc724d3a6360617392ad1d9deee3934d09e1a42eeb4dff535ad3fcfdaeae0"
GAMMAS = (1.0, 1.25, 1.5, 2.0, 4.0)
DISPLAY_THRESHOLDS = (0.0, 0.1, 0.3, 0.5, 1.0, 2.0)
N = 274
FRAME = 628


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_check() -> dict:
    if digest(INPUT) != INPUT_SHA:
        raise ValueError("frozen selection input SHA mismatch")
    spec = json.loads(INPUT.read_text())
    for item in spec["sources"]:
        path = ROOT / item["path"]
        if digest(path) != item["sha256"]:
            raise ValueError(f"source SHA mismatch: {item['path']}")
        if "bytes" in item and path.stat().st_size != item["bytes"]:
            raise ValueError(f"source size mismatch: {item['path']}")
    return spec


def sharp_bounds(event_count: int, n: int, gamma: float) -> tuple[float, float]:
    """Exact LP values for binary events under mean-one bounded weights."""
    if not (0 <= event_count <= n and n > 0 and math.isfinite(gamma) and gamma >= 1):
        raise ValueError("invalid event count or Gamma")
    e = event_count / n
    if gamma == 1.0:
        return e, e
    lo = max(e / gamma, 1.0 - gamma * (1.0 - e))
    hi = min(gamma * e, 1.0 - (1.0 - e) / gamma)
    return max(0.0, lo), min(1.0, hi)


def witness(event: np.ndarray, gamma: float, maximize: bool) -> np.ndarray:
    """Construct an attained endpoint with constant weights per event class."""
    n = len(event)
    m = int(np.count_nonzero(event))
    if m in (0, n):
        return np.ones(n)
    e = m / n
    endpoint = sharp_bounds(m, n, gamma)[int(maximize)]
    event_weight = endpoint / e
    nonevent_weight = (1.0 - endpoint) / (1.0 - e)
    return np.where(event, event_weight, nonevent_weight)


def lp_oracle(event: np.ndarray, gamma: float, maximize: bool) -> dict:
    """Independent HiGHS check, including primal and dual/KKT certificates."""
    n = len(event)
    c = event.astype(float) / n * (-1.0 if maximize else 1.0)
    fit = linprog(c, A_eq=np.ones((1, n)) / n, b_eq=[1.0],
                  bounds=[(1.0 / gamma, gamma)] * n, method="highs")
    if not fit.success:
        raise ArithmeticError(f"LP failed: {fit.status} {fit.message}")
    w = fit.x
    eq = float(fit.eqlin.marginals[0])
    low = fit.lower.marginals
    high = fit.upper.marginals
    stationarity = c - eq / n - low - high
    dual_objective = eq + float(np.sum(low)) / gamma + gamma * float(np.sum(high))
    signed_value = float(c @ w)
    primal_residual = max(abs(float(np.mean(w)) - 1.0),
                          max(0.0, 1.0 / gamma - float(np.min(w))),
                          max(0.0, float(np.max(w)) - gamma))
    dual_residual = max(float(np.max(np.abs(stationarity))),
                        max(0.0, -float(np.min(low))),
                        max(0.0, float(np.max(high))),
                        float(np.max(np.abs(low * (w - 1.0 / gamma)))),
                        float(np.max(np.abs(high * (w - gamma)))),
                        abs(signed_value - dual_objective))
    if max(primal_residual, dual_residual) > 1e-9:
        raise ArithmeticError(f"LP primal/dual failure {primal_residual}, {dual_residual}")
    return {"value": signed_value * (-1.0 if maximize else 1.0),
            "max_primal_residual": primal_residual,
            "max_dual_residual": dual_residual,
            "dual_gap": abs(signed_value - dual_objective),
            "status": fit.status}


def read_oof(result: dict) -> dict[tuple[str, str], np.ndarray]:
    rows: dict[tuple[str, str], dict[str, float]] = {}
    with (METHOD / "distance" / "OOF_ROWS.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["scenario"], row["model"])
            pgc = row["pgc"]
            cohort = rows.setdefault(key, {})
            if pgc in cohort:
                raise ValueError(f"duplicate OOF PGC {key} {pgc}")
            value = float(row["OOF_signed_residual_mag"])
            if not math.isfinite(value):
                raise ValueError("nonfinite OOF signed residual")
            cohort[pgc] = value
    expected = {(scenario, model) for scenario, info in result["scenarios"].items()
                for model in info["models"]}
    if set(rows) != expected or len(rows) != 12:
        raise ValueError("OOF scenarios/models differ from frozen result")
    ids = None
    output = {}
    for key, cohort in rows.items():
        if len(cohort) != N:
            raise ValueError(f"OOF cohort size is {len(cohort)}, expected {N}: {key}")
        current = set(cohort)
        if ids is None:
            ids = current
        elif current != ids:
            raise ValueError("OOF PGC set differs across scenarios/models")
        output[key] = np.asarray([cohort[pgc] for pgc in sorted(cohort, key=int)])
    return output


def evaluate() -> tuple[list[dict], dict]:
    spec = source_check()
    distance = json.loads((METHOD / "distance" / "RESULT.json").read_text())
    if (distance["cohort"]["released"], distance["cohort"]["selected"],
        distance["cohort"]["undefined"]) != (N, FRAME, FRAME - N):
        raise ValueError("reviewed distance counts differ from frozen contract")
    residuals = read_oof(distance)
    surface: list[dict] = []
    fixed: list[dict] = []
    oracle: list[dict] = []
    max_gamma1_error = max_nesting_error = max_witness_error = 0.0
    max_primal = max_dual = 0.0
    for (scenario, model), signed in sorted(residuals.items()):
        absolute = np.abs(signed)
        thresholds = sorted(set(absolute.tolist()) | set(DISPLAY_THRESHOLDS))
        previous = None
        for t in thresholds:
            indicator = absolute > t  # strict tie convention
            m = int(np.count_nonzero(indicator))
            e = m / N
            records = []
            for gamma in GAMMAS:
                lo, hi = sharp_bounds(m, N, gamma)
                row = {"scenario": scenario, "model": model,
                       "threshold_mag": float(t), "gamma": gamma,
                       "event_count": m, "empirical_event_rate": e,
                       "cohort_lower": lo, "cohort_upper": hi,
                       "cohort_width": hi - lo,
                       "frame628_lower": N / FRAME * lo,
                       "frame628_upper": N / FRAME * hi + (FRAME - N) / FRAME,
                       "frame628_width": N / FRAME * (hi - lo) + (FRAME - N) / FRAME,
                       "is_fixed_display": t in DISPLAY_THRESHOLDS}
                surface.append(row)
                records.append(row)
                if gamma == 1:
                    max_gamma1_error = max(max_gamma1_error, abs(lo - e), abs(hi - e))
                for maximize, endpoint in ((False, lo), (True, hi)):
                    w = witness(indicator, gamma, maximize)
                    error = max(abs(float(np.mean(w)) - 1),
                                abs(float(np.mean(w * indicator)) - endpoint),
                                max(0.0, 1.0 / gamma - float(np.min(w))),
                                max(0.0, float(np.max(w)) - gamma))
                    max_witness_error = max(max_witness_error, error)
                if t == 0.5:
                    for maximize, endpoint in ((False, lo), (True, hi)):
                        check = lp_oracle(indicator, gamma, maximize)
                        if abs(check["value"] - endpoint) > 1e-9:
                            raise ArithmeticError("LP endpoint differs from analytic sharp bound")
                        max_primal = max(max_primal, check["max_primal_residual"])
                        max_dual = max(max_dual, check["max_dual_residual"])
                        oracle.append({"scenario": scenario, "model": model,
                                       "threshold_mag": .5, "gamma": gamma,
                                       "endpoint": "upper" if maximize else "lower",
                                       "analytic": endpoint, **check})
                if t in DISPLAY_THRESHOLDS:
                    fixed.append(row)
            if previous is not None:
                for old, new in zip(previous, records):
                    # As the threshold increases, both endpoints cannot increase.
                    if new["cohort_lower"] > old["cohort_lower"] + 1e-10 or new["cohort_upper"] > old["cohort_upper"] + 1e-10:
                        raise ArithmeticError("threshold monotonicity failed")
            for old, new in zip(records, records[1:]):
                error = max(0.0, new["cohort_lower"] - old["cohort_lower"],
                            old["cohort_upper"] - new["cohort_upper"])
                max_nesting_error = max(max_nesting_error, error)
            previous = records
    if max_gamma1_error > 1e-12 or max_nesting_error > 1e-10 or max_witness_error > 1e-9:
        raise ArithmeticError("parity, nesting, or primal witness gate failed")
    if len(oracle) != 120:
        raise ArithmeticError("expected two LP optimizations for each of 60 cells")
    half = [r for r in fixed if r["threshold_mag"] == .5]
    if len(half) != 60:
        raise ArithmeticError("fixed 0.5 mag grid incomplete")
    result = {
        "task_id": "R24-SELECTION-ENVELOPE",
        "input_identity": f"sha256:{INPUT_SHA}",
        "consumed_review": spec["consumed_review"],
        "claim_tier": "C0 empirical selected-cohort sensitivity diagnostic",
        "scientific_admission": "HOLD",
        "original_acceptance": "UNCHANGED",
        "law": "Uniform empirical law on each reviewed 274-row OOF cohort; Gamma bounds mean-one rowwise density ratios, not measured selection propensities",
        "event": "abs(OOF_signed_residual_mag)>t, with strict ties, for every breakpoint and fixed display thresholds",
        "cohort_size": N, "known_frame_size": FRAME,
        "undefined_binary_rows": FRAME - N,
        "full_signed_residual_source": "distance/OOF_ROWS.csv",
        "full_tensor_source": "distance/RESULT.json",
        "gamma_grid": list(GAMMAS), "fixed_thresholds_mag": list(DISPLAY_THRESHOLDS),
        "surface_rows": len(surface), "scenario_model_count": len(residuals),
        "fixed_surface": fixed,
        "oracle_threshold_mag": .5, "oracle_cells": len(oracle) // 2,
        "oracle_optimizations": len(oracle),
        "max_lp_primal_residual": max_primal,
        "max_lp_dual_residual": max_dual,
        "max_gamma1_parity_error": max_gamma1_error,
        "max_nesting_violation": max_nesting_error,
        "max_constructive_witness_error": max_witness_error,
        "minimum_frame628_width": (FRAME - N) / FRAME,
        "physical_mean_witness": {
            "model": "Unrestricted missing-data completion: set all 354 undefined signed residuals to M while preserving all 274 released values and their weights",
            "functional": "628-frame mean signed residual contains (354/628)*M; M tends to either positive or negative infinity",
            "scope": "Constructive nonidentification for unrestricted missing-data model only; no universal physical no-go claim",
        },
        "physical_unknown_mass": 1,
        "r9_alpha": "NOT_USED",
        "parent_5460": "NO_INFERENCE",
        "confidence_or_geometry_probability": "NOT_ESTIMATED",
        "next_discriminator": "Source-qualified inclusion/overlap information and the 354 missing binary outcomes; bounded physical coordinate/support information for a physical mean",
    }
    return surface, {"summary": result, "oracle": oracle}


def save() -> None:
    surface, artifacts = evaluate()
    with (HERE / "SURFACE.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(surface[0]))
        writer.writeheader()
        writer.writerows(surface)
    (HERE / "LP_ORACLE.json").write_text(json.dumps(artifacts["oracle"], indent=2) + "\n")
    (HERE / "RESULT.json").write_text(json.dumps(artifacts["summary"], indent=2) + "\n")
    plot(surface)
    print(json.dumps({k: artifacts["summary"][k] for k in (
        "scenario_model_count", "surface_rows", "oracle_cells", "oracle_optimizations",
        "max_lp_primal_residual", "max_lp_dual_residual", "max_gamma1_parity_error",
        "max_nesting_violation", "minimum_frame628_width")}))


def plot(surface: list[dict]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True, sharey=True)
    scenarios = sorted({r["scenario"] for r in surface})
    colors = {"A_calibration_flow": "#2166ac", "B_optical_STF": "#b2182b", "C_union": "#4d9221"}
    for axis, scenario in zip(axes.flat, scenarios):
        for model, color in colors.items():
            rows = [r for r in surface if r["scenario"] == scenario and r["model"] == model and r["gamma"] == 2.0]
            axis.step([r["threshold_mag"] for r in rows],
                      [r["frame628_width"] for r in rows], where="post", color=color, label=model)
        axis.axhline((FRAME - N) / FRAME, color="black", ls=":", lw=1)
        axis.set_title(scenario.replace("_", " "))
        axis.set_xlim(0, 2)
        axis.grid(alpha=.2)
    axes[0, 0].legend(fontsize=7)
    fig.supxlabel("Strict residual threshold t (mag)")
    fig.supylabel("628-frame indicator interval width")
    fig.suptitle("Empirical density-ratio sensitivity, Gamma=2; undefined outcomes retained")
    fig.tight_layout()
    fig.savefig(HERE / "SELECTION_ENVELOPE.png", dpi=180)
    fig.savefig(HERE / "SELECTION_ENVELOPE.pdf")
    plt.close(fig)


if __name__ == "__main__":
    save()
