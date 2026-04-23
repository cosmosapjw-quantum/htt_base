"""Single-surface statistics module (v5 §G3).

Consolidates the χ² / Gaussian-log-density arithmetic that v5 expects to
live in one place. Today the same math sits in three locations:

* ``bass.likelihood.cosmological_frame._harmonic_log_prob`` — dense
  quadratic form with a precomputed covariance inverse.
* ``bass.likelihood.cosmological_frame._spectral_log_prob`` — diagonal
  per-ℓ inverse-variance sum.
* ``bass.spectrum.off_diagonal_covariance`` — covariance assembly only.

This module provides:

* ``chi_squared`` / ``log_gaussian`` — canonical scalar forms.
* ``CovariancePack`` — typed wrapper around
  ``build_dense_harmonic_covariance`` output plus PSD-guard result.
* ``ResidualPack`` — frozen dataclass carrying per-family residual
  metadata for the gate-stop bundle (see
  ``bass.validation.ver3_gate_stop.GateBundle.residual_summary``).
* ``build_residual_pack`` / ``merge_residual_packs`` — constructors.

Legacy dict-shape consumers are supported via ``as_payload()``; no
existing call site must change as part of S1.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np


__all__ = (
    "ResidualPack",
    "CovariancePack",
    "chi_squared",
    "chi_squared_by_mode",
    "log_gaussian",
    "build_residual_pack",
    "merge_residual_packs",
    "build_covariance_pack",
)


# =============================================================================
# Canonical χ² / log-Gaussian arithmetic
# =============================================================================

def chi_squared(residual: np.ndarray, cov_inv: np.ndarray) -> float:
    """Return r^T Σ⁻¹ r for a vector residual and dense inverse covariance.

    This is the single source of truth for the quadratic form appearing in
    ``CosmologicalFrameLikelihood._harmonic_log_prob``. The implementation
    is intentionally plain so that bit-identity with the inlined form is
    provable by inspection:

        quad = float(residual @ cov_inv @ residual)

    Parameters
    ----------
    residual
        1-D array of length ``n``.
    cov_inv
        ``(n, n)`` dense inverse-covariance matrix.

    Returns
    -------
    float
        The scalar quadratic form. Never negative for a PSD ``Σ⁻¹`` and a
        real residual, but no clipping is applied — numerical negatives
        are surfaced so callers can detect conditioning failures.
    """
    r = np.asarray(residual, dtype=float)
    m = np.asarray(cov_inv, dtype=float)
    return float(r @ m @ r)


def chi_squared_by_mode(
    residual: np.ndarray, sigma: np.ndarray
) -> float:
    """Diagonal form: Σ_i (r_i / σ_i)².

    Matches ``_spectral_log_prob`` arithmetic. Any per-mode weighting
    stays in the caller — pass weighted ``residual`` / ``sigma`` if a
    mask or tier weight must be applied.
    """
    r = np.asarray(residual, dtype=float)
    s = np.asarray(sigma, dtype=float)
    return float(np.sum((r / s) ** 2))


def log_gaussian(
    residual: np.ndarray,
    cov_inv: np.ndarray,
    *,
    log_det_cov: float | None = None,
) -> float:
    """Multivariate Gaussian log density (up to a constant).

    Returns ``-0.5 * chi_squared(r, Σ⁻¹)`` when ``log_det_cov`` is
    ``None`` — this matches the ``_harmonic_log_prob`` return value, which
    drops the ``-0.5 ln|Σ|`` and ``-0.5 n ln(2π)`` terms that cancel in
    ratio-based MCMC usage. If ``log_det_cov`` is provided, the returned
    density includes the ``-0.5 ln|Σ|`` term (still no ``-0.5 n ln(2π)``).
    """
    q = chi_squared(residual, cov_inv)
    if log_det_cov is None:
        return -0.5 * q
    return -0.5 * q - 0.5 * float(log_det_cov)


# =============================================================================
# CovariancePack
# =============================================================================

@dataclass(frozen=True)
class CovariancePack:
    """Typed wrapper around ``build_dense_harmonic_covariance`` output.

    Backward-compatible with the dict shape returned by
    ``build_dense_harmonic_covariance``: every dict key is mirrored as an
    attribute and recoverable via ``as_payload()``.
    """

    representation: str
    harmonic_basis: str
    support: tuple[Mapping[str, object], ...]
    subspace_size: int
    dense_blocks: Mapping[str, np.ndarray]
    invalid_mode_residual: float
    structure_label: str = "unknown"
    preferred_axis: np.ndarray | None = None
    anisotropy_tensor: np.ndarray | None = None
    offdiag_strength: float = 0.0
    rotation_strength: float = 0.0
    psd_guard: Mapping[str, object] | None = None

    def as_payload(self) -> dict[str, object]:
        """Return the original dict shape. Keys match ``build_dense_harmonic_covariance``."""
        payload: dict[str, object] = {
            "representation": self.representation,
            "harmonic_basis": self.harmonic_basis,
            "support": list(self.support),
            "subspace_size": int(self.subspace_size),
            "dense_blocks": dict(self.dense_blocks),
            "invalid_mode_residual": float(self.invalid_mode_residual),
            "structure_label": self.structure_label,
            "preferred_axis": None
            if self.preferred_axis is None
            else np.asarray(self.preferred_axis, dtype=float),
            "anisotropy_tensor": None
            if self.anisotropy_tensor is None
            else np.asarray(self.anisotropy_tensor, dtype=float),
            "offdiag_strength": float(self.offdiag_strength),
            "rotation_strength": float(self.rotation_strength),
        }
        if self.psd_guard is not None:
            payload["psd_guard"] = dict(self.psd_guard)
        return payload


def build_covariance_pack(
    dense_payload: Mapping[str, object],
    *,
    psd_guard: Mapping[str, object] | None = None,
) -> CovariancePack:
    """Wrap a ``build_dense_harmonic_covariance`` result as a CovariancePack."""
    return CovariancePack(
        representation=str(dense_payload.get("representation", "low_ell_harmonic_dense_gaussian")),
        harmonic_basis=str(dense_payload.get("harmonic_basis", "real_pstf_packed")),
        support=tuple(dense_payload.get("support", ())),
        subspace_size=int(dense_payload.get("subspace_size", 0)),
        dense_blocks=MappingProxyType(dict(dense_payload.get("dense_blocks", {}))),
        invalid_mode_residual=float(dense_payload.get("invalid_mode_residual", 0.0)),
        structure_label=str(dense_payload.get("structure_label", "unknown")),
        preferred_axis=dense_payload.get("preferred_axis"),
        anisotropy_tensor=dense_payload.get("anisotropy_tensor"),
        offdiag_strength=float(dense_payload.get("offdiag_strength", 0.0)),
        rotation_strength=float(dense_payload.get("rotation_strength", 0.0)),
        psd_guard=None if psd_guard is None else MappingProxyType(dict(psd_guard)),
    )


# =============================================================================
# ResidualPack
# =============================================================================

@dataclass(frozen=True)
class ResidualPack:
    """Typed residual report for one family-backend invocation.

    Shape is designed to slot into
    ``bass.validation.ver3_gate_stop.GateBundle.residual_summary`` without
    remapping. Legacy dict consumers use ``as_payload()``.
    """

    family: str
    branch: str
    backend: str
    residual_labels: tuple[str, ...]
    residual_values: Mapping[str, float]
    tolerance: Mapping[str, float]
    required_residuals: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...] = ()
    forbidden_shortcut_violations: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    passed: bool = False
    verification_crosscheck_pass: bool = False

    @property
    def missing_residuals(self) -> tuple[str, ...]:
        """Required residuals that are absent from ``residual_values``."""
        return tuple(
            label
            for label in self.required_residuals
            if label not in self.residual_values
        )

    @property
    def violated_tolerances(self) -> tuple[str, ...]:
        """Residual labels whose absolute value exceeds the per-label tolerance."""
        violated: list[str] = []
        for label, value in self.residual_values.items():
            limit = self.tolerance.get(label)
            if limit is None:
                continue
            if not np.isfinite(value):
                violated.append(label)
                continue
            if abs(float(value)) > float(limit):
                violated.append(label)
        return tuple(violated)

    def recomputed_passed(self) -> bool:
        """Recompute ``passed`` from current fields.

        ``passed`` is stored at construction time for audit cheapness;
        callers that want to defend against hand-mutated copies can
        recompute via this method.
        """
        if self.missing_residuals:
            return False
        if self.violated_tolerances:
            return False
        if self.forbidden_shortcut_violations:
            return False
        return True

    def as_payload(self) -> dict[str, object]:
        """Dict shape compatible with ``GateBundle.residual_summary``."""
        return {
            "family": self.family,
            "branch": self.branch,
            "backend": self.backend,
            "residual_labels": list(self.residual_labels),
            "residual_values": {k: float(v) for k, v in self.residual_values.items()},
            "tolerance": {k: float(v) for k, v in self.tolerance.items()},
            "required_residuals": list(self.required_residuals),
            "forbidden_shortcuts": list(self.forbidden_shortcuts),
            "forbidden_shortcut_violations": list(self.forbidden_shortcut_violations),
            "metadata": dict(self.metadata),
            "passed": bool(self.passed),
            "verification_crosscheck_pass": bool(self.verification_crosscheck_pass),
            "missing_residuals": list(self.missing_residuals),
            "violated_tolerances": list(self.violated_tolerances),
        }


def build_residual_pack(
    *,
    family: str,
    branch: str,
    backend: str,
    residual_values: Mapping[str, float],
    tolerance: Mapping[str, float],
    required_residuals: Iterable[str],
    forbidden_shortcuts: Iterable[str] = (),
    forbidden_shortcut_violations: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
    verification_crosscheck_pass: bool = False,
) -> ResidualPack:
    """Construct a ResidualPack and populate derived fields.

    ``residual_labels`` is built from ``residual_values.keys()`` in
    insertion order. ``passed`` is evaluated eagerly from the inputs so
    the object can be read without calling ``recomputed_passed()``.
    """
    values = {str(k): float(v) for k, v in residual_values.items()}
    tol = {str(k): float(v) for k, v in tolerance.items()}
    required = tuple(str(x) for x in required_residuals)
    forbidden = tuple(str(x) for x in forbidden_shortcuts)
    violations = tuple(str(x) for x in forbidden_shortcut_violations)
    meta = MappingProxyType(dict(metadata or {}))

    missing = tuple(label for label in required if label not in values)
    violated: list[str] = []
    for label, value in values.items():
        limit = tol.get(label)
        if limit is None:
            continue
        if not np.isfinite(value) or abs(value) > limit:
            violated.append(label)
    passed = (
        not missing
        and not violated
        and not violations
    )
    return ResidualPack(
        family=str(family),
        branch=str(branch),
        backend=str(backend),
        residual_labels=tuple(values.keys()),
        residual_values=MappingProxyType(values),
        tolerance=MappingProxyType(tol),
        required_residuals=required,
        forbidden_shortcuts=forbidden,
        forbidden_shortcut_violations=violations,
        metadata=meta,
        passed=passed,
        verification_crosscheck_pass=bool(verification_crosscheck_pass),
    )


def merge_residual_packs(packs: Iterable[ResidualPack]) -> ResidualPack:
    """Merge multiple family packs into one combined pack.

    Labels are namespaced ``<family>:<label>`` to avoid collisions.
    ``passed`` is the logical AND of all inputs. ``family``/``branch``/
    ``backend`` are joined with ``+`` when heterogeneous.
    """
    packs = tuple(packs)
    if not packs:
        raise ValueError("merge_residual_packs needs at least one pack")

    families = sorted({p.family for p in packs})
    branches = sorted({p.branch for p in packs})
    backends = sorted({p.backend for p in packs})

    merged_values: dict[str, float] = {}
    merged_tolerance: dict[str, float] = {}
    merged_required: list[str] = []
    merged_forbidden: list[str] = []
    merged_violations: list[str] = []
    merged_meta: dict[str, Any] = {"subpacks": [p.as_payload() for p in packs]}

    for p in packs:
        prefix = f"{p.family}:"
        for label, value in p.residual_values.items():
            merged_values[prefix + label] = float(value)
        for label, limit in p.tolerance.items():
            merged_tolerance[prefix + label] = float(limit)
        for label in p.required_residuals:
            merged_required.append(prefix + label)
        for label in p.forbidden_shortcuts:
            merged_forbidden.append(prefix + label)
        for label in p.forbidden_shortcut_violations:
            merged_violations.append(prefix + label)

    all_verified = all(p.verification_crosscheck_pass for p in packs)
    return build_residual_pack(
        family="+".join(families),
        branch="+".join(branches),
        backend="+".join(backends),
        residual_values=merged_values,
        tolerance=merged_tolerance,
        required_residuals=merged_required,
        forbidden_shortcuts=merged_forbidden,
        forbidden_shortcut_violations=merged_violations,
        metadata=merged_meta,
        verification_crosscheck_pass=all_verified,
    )
