"""Finite normalized-selection bounds for certified binary event envelopes.

The ratios are unnormalized positive joint importance/selection weights. Their
target/reference joint-law Radon-Nikodym ratios are r_i / Z, Z = p @ r.
State-dependent catalogue selection normalization belongs inside the target
kernel; its remaining common normalizer is Z. This module does not construct a
physical event or selection weight from survey data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Sequence

import numpy as np
from scipy.optimize import linprog


SOURCE = (Path(__file__).resolve().parents[2] / "L01_S02_SHARP_20261017"
          / "results" / "S02_CONDITIONAL_SHARP_EVENT_ENVELOPES.json")
SOURCE_SHA256 = "c1ff9cb02da191eca01d7675981788c028cb3ded20ae4bd7d99af97573dcd4e5"
TOL = 1e-10


def _vector(name: str, value: Sequence[float], n: int | None = None) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.ndim != 1 or (n is not None and len(result) != n) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be a finite vector of expected length")
    return result


def _matrix(name: str, value: Sequence[Sequence[float]] | None, n: int) -> np.ndarray:
    if value is None:
        return np.empty((0, n))
    result = np.asarray(value, dtype=float)
    if result.ndim != 2 or result.shape[1] != n or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be a finite matrix with {n} columns")
    return result


def normalized_bounds(
    p: Sequence[float], event_lower: Sequence[float], event_upper: Sequence[float],
    weight_lower: Sequence[float], weight_upper: Sequence[float],
    B: Sequence[Sequence[float]] | None = None, d: Sequence[float] | None = None,
    E: Sequence[Sequence[float]] | None = None, f: Sequence[float] | None = None,
    joint_ids: Sequence[str] | None = None,
) -> dict:
    """Solve min/max of (p*event)@r/(p@r) over compact positive weights.

    Event lower/upper are certified per-atom binary-event flags in {0,1}.
    They are optimized separately, so coupling between event completion and
    weight choices can narrow the identified set; these remain valid outer bounds.
    All vectors use the same ordered joint-atom indices. Optional IDs document
    and validate this ordering; they must be distinct.
    """
    p = _vector("p", p)
    n = len(p)
    if n == 0 or np.any(p <= 0) or abs(float(np.sum(p)) - 1.0) > TOL:
        raise ValueError("p must be strictly positive and sum to one")
    lo = _vector("event_lower", event_lower, n)
    hi = _vector("event_upper", event_upper, n)
    a = _vector("weight_lower", weight_lower, n)
    b = _vector("weight_upper", weight_upper, n)
    if np.any((lo != 0) & (lo != 1)) or np.any((hi != 0) & (hi != 1)) or np.any(lo > hi):
        raise ValueError("per-atom event flags must satisfy binary lower <= upper")
    if np.any(a <= 0) or np.any(a > b):
        raise ValueError("weight bounds must satisfy 0 < lower <= upper")
    if np.any(p * a == 0):
        raise ValueError("reference-weight products underflow; endpoint cannot be certified")
    if joint_ids is not None and (len(joint_ids) != n or len(set(joint_ids)) != n):
        raise ValueError("joint_ids must be ordered and unique for every atom")
    Bm = _matrix("B", B, n)
    Em = _matrix("E", E, n)
    dv = _vector("d", [] if d is None else d, Bm.shape[0])
    fv = _vector("f", [] if f is None else f, Em.shape[0])

    # Mass-conditioned Charnes-Cooper: q_i=p_i*t*r_i, sum(q)=1.
    # This makes event objective coefficients O(1), even for tiny p_i.
    invp = 1.0 / p
    Bq = Bm / p[None, :]
    Eq = Em / p[None, :]
    if not (np.all(np.isfinite(invp)) and np.all(np.isfinite(Bq)) and np.all(np.isfinite(Eq))):
        raise ValueError("mass-conditioned LP coefficients are not finite")
    # Row normalization only changes LP representation, not the polytope.
    Bscale = np.maximum(1.0, np.max(np.abs(np.column_stack((Bq, -dv))), axis=1)) if len(dv) else np.empty(0)
    Escale = np.maximum(1.0, np.max(np.abs(np.column_stack((Eq, -fv))), axis=1)) if len(fv) else np.empty(0)
    A_ub = np.vstack((
        np.column_stack((-np.diag(invp), a)),
        np.column_stack((np.diag(invp), -b)),
        np.column_stack((Bq / Bscale[:, None], -dv / Bscale)) if len(dv) else np.empty((0, n + 1)),
    ))
    A_eq = np.vstack((
        np.r_[np.ones(n), 0.0],
        np.column_stack((Eq / Escale[:, None], -fv / Escale)) if len(fv) else np.empty((0, n + 1)),
    ))
    rhs_eq = np.r_[1.0, np.zeros(len(fv))]

    def solve(event: np.ndarray, maximize: bool) -> dict:
        if len(dv) == 0 and len(fv) == 0:
            # The box-only extrema follow directly from monotonicity of event
            # mass in each event/non-event coordinate; no LP tolerance enters.
            r = np.where(event == 1, b if maximize else a, a if maximize else b)
            with np.errstate(over="ignore", invalid="ignore"):
                box_denom = float(p @ r)
            if not np.isfinite(box_denom) or box_denom <= 0:
                raise ArithmeticError("nonfinite or nonpositive weight normalizer")
            t = 1.0 / box_denom
            if not np.isfinite(t) or t <= 0:
                raise ArithmeticError("nonpositive transformed normalization")
            q = p * r * t
            dual_gap = 0.0
            method = "box_vertex"
        else:
            c = np.r_[event, 0.0] * (-1 if maximize else 1)
            fit = linprog(c, A_ub=A_ub, b_ub=np.zeros(len(A_ub)),
                          A_eq=A_eq, b_eq=rhs_eq,
                          bounds=[(0.0, None)] * (n + 1), method="highs")
            if not fit.success:
                raise ValueError(f"weight polytope LP failed: status={fit.status}; {fit.message}")
            q, t = fit.x[:n], float(fit.x[n])
            if t <= 0 or not np.isfinite(t):
                raise ArithmeticError("nonpositive transformed normalization")
            r = q / (p * t)
            dual = float(fit.eqlin.marginals[0])
            stationarity = c - (A_ub.T @ fit.ineqlin.marginals
                                + A_eq.T @ fit.eqlin.marginals + fit.lower.marginals)
            dual_gap = abs(float(c @ fit.x) - dual)
            optimality_tolerance = min(TOL, max(1e-12, 1e-8 * abs(float(c @ fit.x))))
            if (not np.isfinite(dual) or not np.isfinite(dual_gap) or
                    not np.all(np.isfinite(stationarity)) or
                    not np.all(np.isfinite(fit.ineqlin.marginals)) or
                    not np.all(np.isfinite(fit.lower.marginals)) or
                    np.max(np.abs(stationarity)) > TOL or
                    np.max(fit.ineqlin.marginals) > TOL or
                    np.min(fit.lower.marginals) < -TOL or
                    dual_gap > optimality_tolerance):
                raise ArithmeticError("LP dual optimality certificate failed")
            method = "mass_conditioned_lp"
        if not np.all(np.isfinite(r)) or not np.all(np.isfinite(q)) or not np.isfinite(t) or t <= 0:
            raise ArithmeticError("nonfinite recovered weight or transformed mass")
        with np.errstate(over="ignore", invalid="ignore"):
            denom = float(p @ r)
        if not np.isfinite(denom) or denom <= 0:
            raise ArithmeticError("nonfinite or nonpositive weight normalizer")
        with np.errstate(over="ignore", invalid="ignore"):
            value = float((p * event) @ r / denom)
        if not np.isfinite(value):
            raise ArithmeticError("nonfinite event endpoint")
        residual_components = np.array((
            abs(denom * t - 1.0), abs(float(np.sum(q)) - 1.0),
            float(np.max(np.maximum(a - r, 0))),
            float(np.max(np.maximum(r - b, 0))),
            float(np.max(np.maximum(Bm @ r - dv, 0))) if len(dv) else 0.0,
            float(np.max(np.abs(Em @ r - fv))) if len(fv) else 0.0,
            abs(value - float(event @ q)),
        ))
        if not np.all(np.isfinite(residual_components)):
            raise ArithmeticError("nonfinite original-variable witness residual")
        residual = float(np.max(residual_components))
        if residual > TOL:
            raise ArithmeticError(f"recovered original-variable witness residual {residual:.3g}")
        with np.errstate(over="ignore", invalid="ignore"):
            normalized_rn = r / denom
        if not np.all(np.isfinite(normalized_rn)):
            raise ArithmeticError("nonfinite normalized RN witness")
        return {"value": value, "weight_witness": r.tolist(),
                "normalized_rn_witness": normalized_rn.tolist(),
                "normalizer": denom, "t": t, "max_original_residual": residual,
                "dual_gap": dual_gap, "optimization_method": method}

    lower = solve(lo, False)
    upper = solve(hi, True)
    if not np.isfinite(lower["value"]) or not np.isfinite(upper["value"]):
        raise ArithmeticError("nonfinite event endpoint")
    if lower["value"] > upper["value"] + TOL:
        raise ArithmeticError("lower endpoint exceeds upper endpoint")
    return {"lower": lower, "upper": upper,
            "joint_ids": list(joint_ids) if joint_ids is not None else None}


def box_mass_bounds(lower_mass: float, upper_mass: float, gamma: float) -> tuple[float, float]:
    """Sharp mass-only bounds for unnormalized weights in [1/gamma,gamma]."""
    if not all(np.isfinite([lower_mass, upper_mass, gamma])) or not 0 <= lower_mass <= upper_mass <= 1 or gamma < 1:
        raise ValueError("require 0 <= lower_mass <= upper_mass <= 1 and finite gamma >= 1")
    # Divide both denominators by gamma^2. This remains stable if gamma^2
    # would overflow; exact 0/1 event endpoints stay exact.
    inverse_g2 = (1.0 / gamma) ** 2
    lower = 1.0 if lower_mass == 1 else lower_mass * inverse_g2 / (lower_mass * inverse_g2 + 1 - lower_mass)
    upper = 0.0 if upper_mass == 0 else upper_mass / (upper_mass + (1 - upper_mass) * inverse_g2)
    return lower, upper


def unsupported_mass_bounds(lower: float, upper: float, epsilon: float) -> tuple[float, float]:
    """Widen a supported target interval by unsupported target mass <= epsilon."""
    if not all(np.isfinite([lower, upper, epsilon])) or not 0 <= lower <= upper <= 1 or not 0 <= epsilon <= 1:
        raise ValueError("require valid interval and 0 <= epsilon <= 1")
    return ((1 - epsilon) * lower, (1 - epsilon) * upper + epsilon)


def retained_result() -> dict:
    raw = SOURCE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"retained source identity changed: {digest}")
    source = json.loads(raw)
    scenarios = source["scenarios"]

    def event(scenario: str) -> dict:
        matches = [x for x in scenarios[scenario]["working_ratio_joint_event_bounds"]["at_least_one"]
                   if x["threshold"] == 0.05]
        if len(matches) != 1:
            raise ValueError(f"missing or duplicate retained threshold for {scenario}")
        return matches[0]

    conditional = event("assumed_stf0p5_H0p2")
    exact = event("exact_working")
    sweep = []
    for gamma in (1.0, 1.5, 2.0, 3.0, 4.0):
        bounds = box_mass_bounds(conditional["lower"], conditional["upper"], gamma)
        exact_bounds = box_mass_bounds(exact["lower"], exact["upper"], gamma)
        sweep.append({"gamma": gamma, "assumed_hard_ball": list(bounds),
                      "exact_working": list(exact_bounds)})
    return {
        "schema": "htt.normalized_selection_sensitivity/1",
        "owner": "HTT research intake",
        "scope": "finite normalized-selection sensitivity of retained S02 working-law event bounds",
        "claim_tier": "C0_EXPLORATORY_NON_CLAIM_BEARING",
        "artifact_mode": "derived_reuse_of_retained_result",
        "source": str(SOURCE.relative_to(Path(__file__).resolve().parents[5])),
        "source_sha256": digest,
        "source_git_base": "d66328b8d96ba9cc7bd8c1cbfd929be40903312c",
        "event": "at_least_one; strict working Q threshold 0.05",
        "selection_weight_semantics": "assumed unnormalized positive joint importance weights; normalized target/reference RN is r/Z with Z=p dot r",
        "weight_bounds_status": "ASSUMED_SENSITIVITY_ONLY_NO_MEASURED_WEIGHTS",
        "transfer_source": "CF4 H03 source-conditioned Gaussian working law; not native BASS",
        "sky_support_status": "NOT_APPLICABLE_TO_THIS_EVENT",
        "null_mock_status": "NOT_CALIBRATED_FOR_PHYSICAL_Q",
        "covariance_status": "retained source-conditioned working law only",
        "assumptions": ["Gamma is finite, >=1, and caps unnormalized positive joint weights on every ordered joint atom",
                        "event completion and ratio choice are independent in the relaxed class",
                        "retained hard-ball radii are assumed, not measured"],
        "retained_event_masses": {"assumed_hard_ball": [conditional["lower"], conditional["upper"]],
                                  "exact_working": exact["lower"]},
        "gamma_sweep": sweep,
        "physical": {"Q_domain": "UNRESOLVED", "selection_weight_bounds": "UNMEASURED",
                     "event_unknown_mass": 1.0, "outer_bound": [0.0, 1.0]},
        "allowed_use": "working-law selection sensitivity illustration",
        "forbidden_uses": ["physical Pi or Q inference", "S02/H02 completion", "Bianchi family identification"],
    }


def write_artifacts(output_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    result = retained_result()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    rows = result["gamma_sweep"]
    gammas = [x["gamma"] for x in rows]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    for key, label, color in (("assumed_hard_ball", "Assumed radii working law", "C0"),
                              ("exact_working", "Exact working law", "C1")):
        lo = [x[key][0] for x in rows]
        hi = [x[key][1] for x in rows]
        ax.fill_between(gammas, lo, hi, alpha=0.18, color=color)
        ax.plot(gammas, lo, color=color, marker="o", label=f"{label}: lower")
        ax.plot(gammas, hi, color=color, marker="s", linestyle="--", label=f"{label}: upper")
    ax.set(xlabel=r"Assumed unnormalized joint-weight cap $\Gamma$", ylabel="Conditional event mass bound",
           xlim=(1, 4), ylim=(0, 1), title="S02 retained working-law selection sensitivity")
    ax.legend(loc="center right", fontsize=7)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.text(0.5, 0.015, "Physical Q unresolved; physical outer bound [0, 1]",
             ha="center", fontsize=8)
    fig.savefig(output_dir / "SENSITIVITY.png", dpi=180)
    fig.savefig(output_dir / "SENSITIVITY.pdf")
    plt.close(fig)
    import scipy
    receipt = {
        "schema": "htt.selection_plot_receipt/1",
        "owner": result["owner"], "claim_tier": result["claim_tier"],
        "artifact_mode": result["artifact_mode"], "allowed_use": result["allowed_use"],
        "forbidden_uses": result["forbidden_uses"],
        "transfer_source": result["transfer_source"],
        "null_mock_status": result["null_mock_status"],
        "covariance_status": result["covariance_status"],
        "sky_support_status": result["sky_support_status"],
        "generation_command": [sys.executable, str(Path(__file__).resolve()), "--write-artifacts"],
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": sys.version.split()[0],
        "scipy_version": scipy.__version__, "matplotlib_version": matplotlib.__version__,
        "files_sha256": {name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
                         for name in ("RESULT.json", "SENSITIVITY.png", "SENSITIVITY.pdf")},
    }
    (output_dir / "PLOT_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args()
    if args.write_artifacts:
        write_artifacts(Path(__file__).resolve().parent)
    else:
        print(json.dumps(retained_result(), indent=2))
