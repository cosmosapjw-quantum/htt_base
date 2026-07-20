"""PR-177 ACT DR6 strict-in-band variance-modulation primitives.

The functions in this module operate on one released reconstructed-kappa map
and its matched released reconstructions.  They define an OBSSTAT feature and
an empirical, release-simulation-conditional rank.  They do not reproduce the
quadratic estimator, validate a transfer function, or attribute the feature to
cosmological anisotropy.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


CANDIDATE = "ACT_RELEASE_SIMULATION_CONDITIONAL_MODULATION_CANDIDATE"
NO_RESOLVED = "NO_RESOLVED_COUPLING_AT_CURRENT_MC_RESOLUTION"
UNRESOLVED = "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"
BLOCKED = "BLOCKED_NO_SCIENTIFIC_RESULT"
ALLOWED_SCIENTIFIC_RESULTS = (CANDIDATE, NO_RESOLVED, UNRESOLVED)


class ActInbandModulationError(ValueError):
    """Raised when the frozen PR-177 statistical contract is violated."""


def canonical_sha256(value: object) -> str:
    """Return the SHA-256 of compact, sorted-key JSON."""

    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def raw_records_only_root(input_manifest: Mapping[str, object]) -> str:
    """Digest only PR-152's authenticated raw data/simulation records.

    The enclosing PR-152 manifest also binds its obsolete L=2..10 analysis
    configuration.  PR-177 deliberately authenticates that small file but
    derives a separate root containing only the reusable raw records.
    """

    try:
        payload = {
            "data_alm": input_manifest["data_alm"],
            "ordered_simulation_alms": input_manifest["ordered_simulation_alms"],
        }
    except KeyError as exc:
        raise ActInbandModulationError("PR-152 raw records are incomplete") from exc
    if not isinstance(payload["data_alm"], Mapping):
        raise ActInbandModulationError("data_alm record must be a mapping")
    rows = payload["ordered_simulation_alms"]
    if not isinstance(rows, list) or len(rows) != 400:
        raise ActInbandModulationError("exactly 400 ordered simulation records required")
    paths = [str(row.get("path")) for row in rows if isinstance(row, Mapping)]
    if len(paths) != 400 or len(set(paths)) != 400:
        raise ActInbandModulationError("simulation records must have unique paths")
    return canonical_sha256(payload)


def strict_integer_support(
    *, strict_lower: int = 40, strict_upper: int = 763
) -> tuple[int, ...]:
    """Return the exact integer set for ``strict_lower < L < strict_upper``."""

    if isinstance(strict_lower, bool) or isinstance(strict_upper, bool):
        raise ActInbandModulationError("multipole bounds must be integers")
    if not isinstance(strict_lower, int) or not isinstance(strict_upper, int):
        raise ActInbandModulationError("multipole bounds must be integers")
    if strict_upper <= strict_lower + 1:
        raise ActInbandModulationError("strict multipole support is empty")
    return tuple(range(strict_lower + 1, strict_upper))


def real_y2_columns(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Evaluate the frozen orthonormal real ``ell=2`` basis.

    The order is ``Y20, sqrt(2)(-1)^1 ReY21, sqrt(2)(-1)^1 ImY21,
    sqrt(2)(-1)^2 ReY22, sqrt(2)(-1)^2 ImY22`` in the Equatorial frame.
    """

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    if x.shape != y.shape or x.shape != z.shape:
        raise ActInbandModulationError("Cartesian direction arrays must match")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)) or not np.all(np.isfinite(z)):
        raise ActInbandModulationError("Cartesian directions must be finite")
    return np.column_stack(
        [
            math.sqrt(5.0 / (16.0 * math.pi)) * (3.0 * z * z - 1.0),
            math.sqrt(15.0 / (4.0 * math.pi)) * x * z,
            math.sqrt(15.0 / (4.0 * math.pi)) * y * z,
            math.sqrt(15.0 / (16.0 * math.pi)) * (x * x - y * y),
            math.sqrt(15.0 / (4.0 * math.pi)) * x * y,
        ]
    )


def _center_and_normalize(columns: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(columns, dtype=float)
    if values.ndim != 2 or values.shape[0] < values.shape[1] + 2:
        raise ActInbandModulationError("design matrix has insufficient rows")
    means = values.mean(axis=0)
    centered = values - means
    norms = np.sqrt(np.sum(centered * centered, axis=0))
    if not np.all(np.isfinite(norms)) or np.any(norms <= 0.0):
        raise ActInbandModulationError("design contains a constant or non-finite column")
    return centered / norms, means, norms


@dataclass(frozen=True)
class MaskDesign:
    """Frozen core-pixel regression design for raw and mask-controlled fits."""

    nside: int
    threshold: float
    core_pixels: np.ndarray
    raw_columns: np.ndarray
    controlled_columns: np.ndarray
    y2_means: np.ndarray
    y2_norms: np.ndarray
    mask_squared_mean: float
    mask_squared_norm: float
    raw_condition_number: float
    controlled_condition_number: float

    def receipt(self) -> dict[str, object]:
        return {
            "nside": self.nside,
            "ordering": "RING",
            "mask_threshold": self.threshold,
            "core_pixel_count": int(self.core_pixels.size),
            "core_fraction": float(self.core_pixels.size / (12 * self.nside * self.nside)),
            "mask_squared_mean": self.mask_squared_mean,
            "mask_squared_norm": self.mask_squared_norm,
            "raw_design_condition_number": self.raw_condition_number,
            "controlled_design_condition_number": self.controlled_condition_number,
            "real_y2_order": ["Y20", "Y21c", "Y21s", "Y22c", "Y22s"],
        }


def build_mask_design(
    mask_map: Sequence[float],
    *,
    nside: int,
    threshold: float = 0.99,
    maximum_condition_number: float = 1.0e8,
) -> MaskDesign:
    """Build the mask-core raw/control regression design without sky data."""

    import healpy as hp

    mask = np.asarray(mask_map, dtype=float)
    if mask.ndim != 1 or mask.size != hp.nside2npix(nside):
        raise ActInbandModulationError("mask map size does not match nside")
    if not np.all(np.isfinite(mask)):
        raise ActInbandModulationError("mask map contains non-finite values")
    if not 0.0 <= threshold <= 1.0:
        raise ActInbandModulationError("mask threshold must lie in [0,1]")
    core = np.flatnonzero(mask >= threshold)
    if core.size < 100:
        raise ActInbandModulationError("mask core is too small")
    x, y, z = hp.pix2vec(nside, core, nest=False)
    y2 = real_y2_columns(x, y, z)
    y2_normalized, y2_means, y2_norms = _center_and_normalize(y2)
    mask_squared = mask[core] ** 2
    mask_normalized, mask_means, mask_norms = _center_and_normalize(mask_squared[:, None])
    raw_gram = y2_normalized.T @ y2_normalized
    controlled = np.column_stack([mask_normalized, y2_normalized])
    controlled_gram = controlled.T @ controlled
    raw_condition = float(np.linalg.cond(raw_gram))
    controlled_condition = float(np.linalg.cond(controlled_gram))
    if not np.isfinite(raw_condition) or raw_condition > maximum_condition_number:
        raise ActInbandModulationError("raw mask design is ill-conditioned")
    if not np.isfinite(controlled_condition) or controlled_condition > maximum_condition_number:
        raise ActInbandModulationError("controlled mask design is ill-conditioned")
    return MaskDesign(
        nside=int(nside),
        threshold=float(threshold),
        core_pixels=core,
        raw_columns=y2_normalized,
        controlled_columns=controlled,
        y2_means=y2_means,
        y2_norms=y2_norms,
        mask_squared_mean=float(mask_means[0]),
        mask_squared_norm=float(mask_norms[0]),
        raw_condition_number=raw_condition,
        controlled_condition_number=controlled_condition,
    )


def fractional_variance_features(
    band_map: Sequence[float], design: MaskDesign
) -> dict[str, object]:
    """Fit the frozen raw and mask-controlled fractional Y2 vectors."""

    values = np.asarray(band_map, dtype=float)
    expected = 12 * design.nside * design.nside
    if values.ndim != 1 or values.size != expected:
        raise ActInbandModulationError("band map size does not match mask design")
    core_field = values[design.core_pixels]
    if not np.all(np.isfinite(core_field)):
        raise ActInbandModulationError("band field contains non-finite core pixels")
    variance = core_field * core_field
    mean_variance = float(variance.mean())
    if not np.isfinite(mean_variance) or mean_variance <= 0.0:
        raise ActInbandModulationError("mean core variance must be finite and positive")
    centered = variance - mean_variance
    raw_gram = design.raw_columns.T @ design.raw_columns
    raw_rhs = design.raw_columns.T @ centered
    raw_normalized = np.linalg.solve(raw_gram, raw_rhs)
    controlled_gram = design.controlled_columns.T @ design.controlled_columns
    controlled_rhs = design.controlled_columns.T @ centered
    controlled_normalized = np.linalg.solve(controlled_gram, controlled_rhs)
    q_raw = raw_normalized / design.y2_norms / mean_variance
    q_controlled = controlled_normalized[1:] / design.y2_norms / mean_variance
    mask_change = float(np.sum((q_raw - q_controlled) ** 2))
    if not np.all(np.isfinite(q_raw)) or not np.all(np.isfinite(q_controlled)):
        raise ActInbandModulationError("quadrupolar feature is non-finite")
    return {
        "q_raw": [float(value) for value in q_raw],
        "q_controlled": [float(value) for value in q_controlled],
        "mask_change": mask_change,
        "mean_core_variance": mean_variance,
        "raw_design_condition_number": design.raw_condition_number,
        "controlled_design_condition_number": design.controlled_condition_number,
    }


def strict_band_alm(
    full_alm: Sequence[complex], *, integer_min: int = 41, integer_max: int = 762
) -> np.ndarray:
    """Copy exactly ``integer_min..integer_max`` into a compact healpy alm."""

    import healpy as hp

    alm = np.asarray(full_alm, dtype=np.complex128)
    if alm.ndim != 1:
        raise ActInbandModulationError("alm input must be one-dimensional")
    input_lmax = int(hp.Alm.getlmax(alm.size))
    if input_lmax < integer_max:
        raise ActInbandModulationError("alm input does not reach frozen support")
    target_ell, target_m = hp.Alm.getlm(integer_max)
    selected = target_ell >= integer_min
    source_index = hp.Alm.getidx(input_lmax, target_ell[selected], target_m[selected])
    compact = np.zeros(hp.Alm.getsize(integer_max), dtype=np.complex128)
    compact[selected] = alm[source_index]
    if not np.all(np.isfinite(compact[selected].real)) or not np.all(
        np.isfinite(compact[selected].imag)
    ):
        raise ActInbandModulationError("selected strict-band alm contains non-finite values")
    return compact


def extract_alm_features(
    full_alm: Sequence[complex], design: MaskDesign, *, integer_min: int = 41, integer_max: int = 762
) -> dict[str, object]:
    """Run the identical unit-local band/map/feature pipeline."""

    import healpy as hp

    compact = strict_band_alm(full_alm, integer_min=integer_min, integer_max=integer_max)
    band_map = hp.alm2map(
        compact,
        nside=design.nside,
        lmax=integer_max,
        mmax=integer_max,
        pol=False,
    )
    return fractional_variance_features(band_map, design)


def _feature_matrix(features: Sequence[Sequence[float]], *, name: str) -> np.ndarray:
    values = np.asarray(features, dtype=float)
    if values.ndim != 2 or values.shape[0] < 9 or values.shape[1] != 5:
        raise ActInbandModulationError(f"{name} must have shape (n>=9,5)")
    if not np.all(np.isfinite(values)):
        raise ActInbandModulationError(f"{name} contains non-finite values")
    return values


def observation_inclusive_loo_scores(
    features: Sequence[Sequence[float]], *, maximum_condition_number: float = 1.0e8
) -> dict[str, object]:
    """Compute permutation-equivariant leave-one-out Mahalanobis scores."""

    values = _feature_matrix(features, name="features")
    n_total, dimension = values.shape
    n_reference = n_total - 1
    if n_reference <= dimension + 2:
        raise ActInbandModulationError("insufficient reference units for Hartlap factor")
    hartlap = (n_reference - dimension - 2.0) / (n_reference - 1.0)
    scores = np.empty(n_total, dtype=float)
    conditions = np.empty(n_total, dtype=float)
    minimum_eigenvalues = np.empty(n_total, dtype=float)
    global_mean = values.mean(axis=0)
    globally_centered = values - global_mean
    total_scatter = globally_centered.T @ globally_centered
    for index in range(n_total):
        centered_unit = values[index] - global_mean
        mean = (n_total * global_mean - values[index]) / n_reference
        centered_scatter = total_scatter - (n_total / n_reference) * np.outer(
            centered_unit, centered_unit
        )
        covariance = centered_scatter / (n_reference - 1)
        covariance = 0.5 * (covariance + covariance.T)
        eigenvalues = np.linalg.eigvalsh(covariance)
        condition = float(np.linalg.cond(covariance))
        if (
            not np.all(np.isfinite(eigenvalues))
            or eigenvalues[0] <= 0.0
            or not np.isfinite(condition)
            or condition > maximum_condition_number
        ):
            raise ActInbandModulationError(
                f"leave-one-out covariance gate failed for unit {index}"
            )
        residual = values[index] - mean
        scores[index] = hartlap * float(residual @ np.linalg.solve(covariance, residual))
        conditions[index] = condition
        minimum_eigenvalues[index] = float(eigenvalues[0])
    return {
        "scores": scores,
        "hartlap_factor": float(hartlap),
        "n_total": int(n_total),
        "n_reference": int(n_reference),
        "dimension": int(dimension),
        "maximum_condition_number": float(conditions.max()),
        "minimum_covariance_eigenvalue": float(minimum_eigenvalues.min()),
        "permutation_equivariant_transform": True,
    }


def pooled_upper_rank(scores: Sequence[float]) -> dict[str, object]:
    """Return the conservative observation-inclusive plus-one upper rank."""

    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or values.size < 2 or not np.all(np.isfinite(values)):
        raise ActInbandModulationError("rank scores must be a finite vector")
    observed = float(values[0])
    null = values[1:]
    exceedance = int(np.count_nonzero(null >= observed))
    ties = int(np.count_nonzero(null == observed))
    return {
        "observed_score": observed,
        "null_scores": [float(value) for value in null],
        "n_null": int(null.size),
        "exceedance_count": exceedance,
        "tie_count": ties,
        "rank_fraction": f"{1 + exceedance}/{values.size}",
        "rank": float((1 + exceedance) / values.size),
        "finite_resolution": float(1.0 / values.size),
        "tail": "upper",
        "tie_policy": "conservative_greater_equal",
    }


def full_statistics(
    q_raw: Sequence[Sequence[float]],
    q_controlled: Sequence[Sequence[float]],
    mask_change: Sequence[float],
    *,
    maximum_condition_number: float = 1.0e8,
) -> dict[str, object]:
    """Recompute all ensemble-dependent full-sample transforms and ranks."""

    raw = _feature_matrix(q_raw, name="q_raw")
    controlled = _feature_matrix(q_controlled, name="q_controlled")
    change = np.asarray(mask_change, dtype=float)
    if raw.shape != controlled.shape or change.shape != (raw.shape[0],):
        raise ActInbandModulationError("raw/control/mask feature counts differ")
    if not np.all(np.isfinite(change)) or np.any(change < 0.0):
        raise ActInbandModulationError("mask-change scores must be finite and non-negative")
    raw_scores = observation_inclusive_loo_scores(
        raw, maximum_condition_number=maximum_condition_number
    )
    controlled_scores = observation_inclusive_loo_scores(
        controlled, maximum_condition_number=maximum_condition_number
    )
    return {
        "raw": {**pooled_upper_rank(raw_scores["scores"]), "score_gate": _score_gate(raw_scores)},
        "controlled": {
            **pooled_upper_rank(controlled_scores["scores"]),
            "score_gate": _score_gate(controlled_scores),
        },
        "mask_change": pooled_upper_rank(change),
    }


def _score_gate(receipt: Mapping[str, object]) -> dict[str, object]:
    return {
        key: receipt[key]
        for key in (
            "hartlap_factor",
            "n_total",
            "n_reference",
            "dimension",
            "maximum_condition_number",
            "minimum_covariance_eigenvalue",
            "permutation_equivariant_transform",
        )
    }


def delete_simulation_rank_replicates(
    q_raw: Sequence[Sequence[float]],
    q_controlled: Sequence[Sequence[float]],
    mask_change: Sequence[float],
    *,
    maximum_condition_number: float = 1.0e8,
) -> dict[str, object]:
    """Run all 400 delete-simulation ensemble recomputations at feature level."""

    raw = _feature_matrix(q_raw, name="q_raw")
    controlled = _feature_matrix(q_controlled, name="q_controlled")
    change = np.asarray(mask_change, dtype=float)
    if raw.shape != (401, 5) or controlled.shape != (401, 5) or change.shape != (401,):
        raise ActInbandModulationError("delete-unit contract requires data plus exactly 400 simulations")
    replicates: list[dict[str, object]] = []
    for simulation_index in range(1, 401):
        keep = np.ones(401, dtype=bool)
        keep[simulation_index] = False
        stats = full_statistics(
            raw[keep],
            controlled[keep],
            change[keep],
            maximum_condition_number=maximum_condition_number,
        )
        replicates.append(
            {
                "deleted_unit": f"sim-{simulation_index:04d}",
                "raw_rank": stats["raw"]["rank"],
                "controlled_rank": stats["controlled"]["rank"],
                "mask_change_rank": stats["mask_change"]["rank"],
                "remaining_total_units": 400,
                "remaining_null_units": 399,
                "ensemble_transforms_recomputed": True,
            }
        )
    return {
        "replicates": replicates,
        "replicate_count": len(replicates),
        "deleted_units_unique": len({row["deleted_unit"] for row in replicates}) == 400,
        "observed_unit_deleted": False,
        "full_sample_ensemble_transform_reused": False,
        "lineage_status": "CERTIFIED_FOR_PR177_RANK_FUNCTIONAL",
    }


def rank_resolution_certificate(
    *,
    full_rank: float,
    delete_ranks: Sequence[float],
    alpha: float = 0.05,
    critical_value: float = 1.965927295920882,
    full_finite_resolution: float = 1.0 / 401.0,
) -> dict[str, object]:
    """Build the frozen delete-unit t-interval plus finite-grid guard."""

    full = float(full_rank)
    values = np.asarray(delete_ranks, dtype=float)
    if values.shape != (400,) or not np.all(np.isfinite(values)):
        raise ActInbandModulationError("exactly 400 finite delete ranks required")
    if not 0.0 <= full <= 1.0 or np.any((values < 0.0) | (values > 1.0)):
        raise ActInbandModulationError("ranks must lie in [0,1]")
    mean = float(values.mean())
    se = float(math.sqrt(399.0 / 400.0 * np.sum((values - mean) ** 2)))
    lower = max(0.0, full - critical_value * se)
    upper = min(1.0, full + critical_value * se)
    guard_lower = max(0.0, lower - full_finite_resolution)
    guard_upper = min(1.0, upper + full_finite_resolution)
    if guard_upper < alpha:
        relation = "RESOLVED_BELOW_ALPHA"
    elif guard_lower > alpha:
        relation = "RESOLVED_ABOVE_ALPHA"
    else:
        relation = "UNRESOLVED_AT_ALPHA"
    return {
        "full_rank": full,
        "delete_rank_mean": mean,
        "delete_rank_min": float(values.min()),
        "delete_rank_max": float(values.max()),
        "delete_replicates": 400,
        "jackknife_standard_error": se,
        "confidence_level": 0.95,
        "interval_distribution": "student_t_df_399",
        "critical_value": float(critical_value),
        "confidence_interval": [lower, upper],
        "full_finite_resolution": float(full_finite_resolution),
        "guard_interval": [guard_lower, guard_upper],
        "alpha": float(alpha),
        "relation_to_alpha": relation,
        "interpretation": "numerical_resolution_only",
    }


def terminal_result(
    *,
    controlled: Mapping[str, object],
    raw: Mapping[str, object],
    mask_change: Mapping[str, object],
    eligibility_passed: bool,
) -> dict[str, object]:
    """Apply the closed PR-177 terminal truth table."""

    if not eligibility_passed:
        return {
            "scientific_result": None,
            "scientific_status": BLOCKED,
            "reason": "eligibility_gate_failed",
        }
    ctl = str(controlled.get("relation_to_alpha"))
    raw_relation = str(raw.get("relation_to_alpha"))
    mask_relation = str(mask_change.get("relation_to_alpha"))
    allowed_relations = {
        "RESOLVED_BELOW_ALPHA",
        "RESOLVED_ABOVE_ALPHA",
        "UNRESOLVED_AT_ALPHA",
    }
    if {ctl, raw_relation, mask_relation} - allowed_relations:
        raise ActInbandModulationError("resolution certificate relation is invalid")
    if ctl == "RESOLVED_ABOVE_ALPHA":
        return {
            "scientific_result": NO_RESOLVED,
            "scientific_status": "CLOSED",
            "reason": "controlled_rank_resolved_above_alpha",
        }
    if ctl == "UNRESOLVED_AT_ALPHA":
        return {
            "scientific_result": UNRESOLVED,
            "scientific_status": "CLOSED",
            "reason": "controlled_rank_guard_touches_or_crosses_alpha",
        }
    if raw_relation == "UNRESOLVED_AT_ALPHA" or mask_relation == "UNRESOLVED_AT_ALPHA":
        return {
            "scientific_result": UNRESOLVED,
            "scientific_status": "CLOSED",
            "reason": "required_mask_control_guard_touches_or_crosses_alpha",
        }
    if raw_relation == "RESOLVED_BELOW_ALPHA" and mask_relation == "RESOLVED_ABOVE_ALPHA":
        return {
            "scientific_result": CANDIDATE,
            "scientific_status": "CLOSED",
            "reason": "controlled_and_raw_below_alpha_mask_change_not_exceptional",
        }
    return {
        "scientific_result": NO_RESOLVED,
        "scientific_status": "CLOSED",
        "reason": "registered_mask_control_blocks_candidate",
    }


def semantic_digest(payload: Mapping[str, object]) -> str:
    """Digest a result payload excluding its self-referential digest field."""

    material = dict(payload)
    material.pop("semantic_digest", None)
    return canonical_sha256(material)
