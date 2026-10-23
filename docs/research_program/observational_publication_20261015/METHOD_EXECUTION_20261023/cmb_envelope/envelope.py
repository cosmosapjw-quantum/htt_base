"""R24-CMB-ENVELOPE: conditional common-contaminant bounds on retained carriers."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UP = HERE.parent
SOURCE = UP / "cmb" / "RESULT.json"
INPUT = UP / "R24-CMB-ENVELOPE_INPUT.json"
PACKET = "3872e6f22331f3aef13a273d7bb446badf612bc7ce80d3207ba2fbd86f840fdb"
INPUT_HASH = "191e516e95b044eee02c2c8c7dd51e74aa9d8863d39763930d8043f59e37a8bf"
SOURCE_HASH = "107c0ab6af308213c91cb1c38477242864fc24c6e5e0739fe6fb93b9c195bdbb"
RHO = (0.0, 0.05, 0.1, 0.25, 0.5, 1.0)
WEIGHTS = np.array([math.sqrt(15.0 / (8.0 * math.pi))] * 5 +
                   [math.sqrt(35.0 / (8.0 * math.pi))] * 7)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invariant_coordinates(bundle: dict, q0: float, o0: float) -> np.ndarray:
    """Orthonormal coordinates for ||(Q/q0,O/o0)||_F, not raw harmonics."""
    c = np.asarray(bundle["harmonic12_K_CMB"], dtype=float)
    if c.shape != (12,) or not np.all(np.isfinite(c)):
        raise ValueError("invalid full harmonic carrier")
    v = c * WEIGHTS / np.array([q0] * 5 + [o0] * 7)
    stf_norm = math.hypot(bundle["STF2_norm_K_CMB"] / q0,
                          bundle["STF3_norm_K_CMB"] / o0)
    if not math.isclose(float(np.linalg.norm(v)), stf_norm, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("STF/harmonic invariant norm mismatch")
    return v


def envelope_interval(lower: float, upper: float, r1: float, r2: float) -> tuple[float, float]:
    if min(lower, upper, r1, r2) < 0 or lower > upper:
        raise ValueError("invalid certified interval or radius")
    return max(0.0, lower - r1 - r2), upper + r1 + r2


def support_interval(value: float, dual_norm: float, radius: float) -> tuple[float, float]:
    """Support of K+h at one functional; ||h||<=r in the invariant norm."""
    if dual_norm < 0 or radius < 0:
        raise ValueError("negative norm or radius")
    return value - dual_norm * radius, value + dual_norm * radius


def split_model(g: np.ndarray, foreground: np.ndarray, split_foregrounds: np.ndarray,
                noises: np.ndarray) -> np.ndarray:
    return g + foreground + split_foregrounds + noises


def cross_power_expectation(common: np.ndarray, cross_noise_trace: float) -> float:
    """E[d1·d2] for centered split-specific noise, with tr N12 retained."""
    return float(np.dot(common, common) + cross_noise_trace)


def lower_at_rho(row: dict, rho: float) -> float:
    """Clipped T3 lower certificate, including points between tabulated radii."""
    if rho < 0:
        raise ValueError("negative rho")
    return max(0.0, row["base_lower"] - rho *
               (row["full_norm_first"] + row["full_norm_second"]))


def plot_lower_vertices(row: dict) -> list[tuple[float, float]]:
    """Insert the exact clipping kink before connecting scenario points."""
    threshold = row["rho_at_zero_lower"]
    grid = sorted(set(RHO) | ({threshold} if 0 < threshold < RHO[-1] else set()))
    return [(rho, 0.0 if rho == threshold else lower_at_rho(row, rho)) for rho in grid]


def compute() -> dict:
    if digest(INPUT) != INPUT_HASH or digest(SOURCE) != SOURCE_HASH:
        raise ValueError("frozen input identity changed")
    source = json.loads(SOURCE.read_text())
    q0, o0 = source["q0_K_CMB"], source["o0_K_CMB"]
    bundles = source["bundles"]
    coords = {(b["source"], b["product"], b["lmax"], b["secondary_window_degrees"]):
              invariant_coordinates(b, q0, o0) for b in bundles}
    full_norms = {(src, ell, win): float(np.linalg.norm(v))
                  for (src, product, ell, win), v in coords.items() if product == "full"}

    def pair_keys(c: dict) -> tuple[tuple, tuple]:
        p, ell, win = c["product"], c["lmax"], c["window"]
        if c["comparison"] == "split_vs_full":
            return ("hash_pinned_primary", "full", ell, 0), ("hash_pinned_primary", p, ell, 0)
        if c["comparison"] == "primary_vs_pilot_cached_w0":
            return ("hash_pinned_primary", p, ell, 0), ("pilot_cached", p, ell, 0)
        if c["comparison"] == "same_product_secondary_window":
            return ("pilot_cached", p, ell, 0), ("pilot_cached", p, ell, win)
        raise ValueError("unknown comparison")

    comparisons = []
    for c in source["comparisons"]:
        a, b = pair_keys(c)
        if a not in coords or b not in coords:
            raise ValueError("missing pair carrier")
        f1 = full_norms[(a[0], a[2], a[3])]
        f2 = full_norms[(b[0], b[2], b[3])]
        lo, hi = c["interval"]["lower"], c["interval"]["feasible_upper"]
        rows = []
        for rho in RHO:
            r1, r2 = rho * f1, rho * f2
            l, u = envelope_interval(lo, hi, r1, r2)
            rows.append({"rho": rho, "radius_first": r1, "radius_second": r2,
                         "certified_outer_lower": l, "feasible_outer_upper": u,
                         "positive_lower_survives": l > 0.0})
        comparisons.append({"comparison": c["comparison"], "product": c["product"],
                            "lmax": c["lmax"], "window": c["window"],
                            "first_key": list(a), "second_key": list(b),
                            "base_lower": lo, "base_feasible_upper": hi,
                            "full_norm_first": f1, "full_norm_second": f2,
                            "rho_at_zero_lower": lo / (f1 + f2), "scenarios": rows})

    # The source processing support used harmonic/K0 axes. Re-evaluate its
    # finite set in the orthonormal invariant coordinates, including the
    # octupole weight. Each axis functional has dual norm exactly one.
    support = []
    for src, ell, win in sorted(full_norms):
        rows = np.stack([v for (s, _, e, w), v in coords.items()
                         if s == src and e == ell and w == win])
        if rows.shape != (5, 12):
            raise ValueError("processing set must have five products")
        direction_values = np.concatenate([rows.max(axis=0), (-rows).max(axis=0)])
        radius_unit = full_norms[(src, ell, win)]
        support.append({"source": src, "lmax": ell, "window": win,
                        "processing_set_size": 5,
                        "direction_set": "24 signed invariant-orthonormal coordinate functionals",
                        "dual_norm": 1.0, "base_support": direction_values.tolist(),
                        "full_norm": radius_unit,
                        "scenarios": [{"rho": rho, "radius": rho * radius_unit,
                                       "support_lower": (direction_values - rho * radius_unit).tolist(),
                                       "support_upper": (direction_values + rho * radius_unit).tolist()}
                                      for rho in RHO]})

    first = coords[("hash_pinned_primary", "full", 32, 0)]
    split_foregrounds = np.stack([np.zeros(12), np.ones(12) * 0.001])
    noises = np.stack([np.ones(12) * 0.002, -np.ones(12) * 0.003])
    f = np.ones(12) * 0.01
    h = np.zeros(12); h[0] = 1000.0 * np.linalg.norm(first)
    observed = split_model(first, f, split_foregrounds, noises)
    transformed = split_model(first + h, f - h, split_foregrounds, noises)
    witness_residual = float(np.max(np.abs(observed - transformed)))
    split_residual = float(np.max(np.abs(np.diff(observed, axis=0) - np.diff(transformed, axis=0))))
    if witness_residual > 1e-12 or split_residual > 1e-12:
        raise ArithmeticError("common mode witness failed")
    noise_vector = np.array([1.0, 2.0])
    noise_samples = np.stack([noise_vector, -noise_vector])
    cross_cov = np.mean([np.outer(n, n) for n in noise_samples], axis=0)
    cross_trace = float(np.trace(cross_cov))
    cross_power = float(np.mean([np.dot(n, n) for n in noise_samples]))
    return {"task_id": "R24-CMB-ENVELOPE", "packet_id": PACKET,
            "input_identity": "sha256:" + INPUT_HASH, "consumed_candidate": "sha256:" + SOURCE_HASH,
            "owner": "obsstat", "status": "CONDITIONAL_DIAGNOSTIC_ONLY", "claim_tier": "C0",
            "transfer_source": "none", "scope": "one PR3 sky and distinct processing views",
            "norm": "sqrt(||Q||_F^2/q0^2+||O||_F^2/o0^2); q0=o0=1e-5 K_CMB",
            "radius_reference": "full product at each source,lmax,window; same processed h is shared by splits within one operator; no source-to-operator map is supplied across distinct operators",
            "rho_grid": list(RHO), "full_norms": [{"source": s, "lmax": e, "window": w, "norm": v}
                                                for (s, e, w), v in sorted(full_norms.items())],
            "comparisons": comparisons, "processing_support": support,
            "common_mode_witness": {"model": "d_s=g+f_common+f_s+n_s",
                                    "transformation": "g -> g+t*u, f_common -> f_common-t*u, t arbitrary",
                                    "example_t_over_full_norm": 1000.0,
                                    "max_observed_residual": witness_residual,
                                    "max_split_difference_residual": split_residual,
                                    "conclusion": "unbounded source/foreground ambiguity without an external constraint"},
            "cross_noise": {"cross_power_formula": "E[d1 dot d2]=||g+f_common||^2+tr(N12) when centered split-specific terms are absent",
                            "trN12": "UNKNOWN", "zero_assumption": False,
                            "counterexample": {"law": "equiprobable S in {-1,+1}; n1=n2=S*(1,2)",
                                               "sample_probabilities": [0.5, 0.5],
                                               "n1_samples": noise_samples.tolist(),
                                               "n2_samples": noise_samples.tolist(),
                                               "mean_n1": noise_samples.mean(axis=0).tolist(),
                                               "mean_n2": noise_samples.mean(axis=0).tolist(),
                                               "N12": cross_cov.tolist(),
                                               "trN12": cross_trace,
                                               "zero_common_cross_power": cross_power}},
            "joint_state": "within one operator, one shared processed h; cross-operator physical coupling is unavailable without a source-to-operator map; pairwise extrema and support directions are not jointly sharp",
            "support_interpretation": "finite processing set convex-hull support at 24 dual-unit directions; no nonconvex stratum recovery",
            "p_value": None, "berger_boos_p": None, "physical_Pi": None,
            "physical_attribution": "UNAVAILABLE", "matched_total_field_law": "ABSENT",
            "original_acceptances": "UNCHANGED", "scientific_admission": "HOLD"}


def plot(result: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    rows = [x for x in result["comparisons"] if x["lmax"] == 32 and x["comparison"] == "split_vs_full"]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for row in rows:
        vertices = plot_lower_vertices(row)
        color = ax[0].plot([v[0] for v in vertices], [v[1] for v in vertices],
                           label=row["product"])[0].get_color()
        ax[0].scatter(RHO, [s["certified_outer_lower"] for s in row["scenarios"]],
                      color=color, s=22)
        ax[0].scatter([row["rho_at_zero_lower"]], [0.0], color=color, marker="x", s=45)
    ax[0].set(xlabel="rho = radius / ||full||", ylabel="certified lower (invariant norm)",
              title="Primary L32 split vs full")
    ax[0].legend(fontsize=8)
    for row in rows:
        ax[1].plot(RHO, [s["feasible_outer_upper"] for s in row["scenarios"]], marker="o", label=row["product"])
    ax[1].set(xlabel="rho = radius / ||full||", ylabel="conservative upper (invariant norm)",
              title="Pairwise conservative upper")
    fig.suptitle("One PR3 sky; conditional common-contaminant radii; no calibrated p")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"ENVELOPE.{ext}", dpi=160)
    plt.close(fig)


def main() -> None:
    result = compute()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    plot(result)
    print(json.dumps({"comparisons": len(result["comparisons"]),
                      "support_sets": len(result["processing_support"]),
                      "primary_positive_lower_at_rho_0.05": sum(
                          r["scenarios"][1]["positive_lower_survives"] for r in result["comparisons"]
                          if r["lmax"] == 32 and r["comparison"] == "split_vs_full")}))


if __name__ == "__main__":
    main()
