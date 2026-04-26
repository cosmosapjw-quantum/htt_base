"""bass/hierarchy/family_k_grid.py — Round-16 PR-S6/S7 off-axis k-grids.

Implements V5_ROUND16_02_SOLVER_LAYER.md §3 (closes Round-16 gap **G3**
mode-coverage side: off-axis modes for class-A intrinsic and class-B
Bianchi families. Currently the audit shows 8/11 families restricted to
axis-aligned k-vectors; this module lifts that restriction by
generating the family-specific k-grid + Plancherel weights consumed
by the LoS aggregation in PR-S8/S9/S10.

Each family has its own spatial-spectrum parametrisation per
V5_ROUND16_01 §2 / V5_ROUND16_02 §3.1:

| Family | k-vec parametrisation                | Weight rule                   |
|--------|---------------------------------------|-------------------------------|
| FLRW/I | (k, 0, 0) on log-grid                 | uniform                       |
| II     | (k₁, k₂) ∈ ℝ × ℤ_{≥0}                 | k₁ log + k₂ lattice           |
| VI₀    | (k₁, k₃, k₂)                          | continuous-continuous-lattice |
| VII₀   | (k_⊥, φ, k₃) helical                  | helical Euclidean             |
| VIII   | (μ, s) continuous + D^±_λ discrete    | sl(2,ℝ) Plancherel            |
| IX     | ℓ_spec ∈ {1, 2, ...}                  | (2ℓ_spec + 1)                 |
| V      | continuous k + curvature scale        | open hyperbolic               |
| III/IV/VI_h/VII_h | continuous k + h-dependent λ | h-continuous                  |

The module exposes :func:`build_family_k_grid(family, ...)` returning a
:class:`FamilyKGrid` with `k_vectors` (list of 3-vectors) and
`weights` (per-k Plancherel measure) plus a `branch_label` describing
the parametrisation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

__all__ = [
    "FamilyKGrid",
    "build_family_k_grid",
    "SUPPORTED_FAMILIES",
    "DEFAULT_K_MIN",
    "DEFAULT_K_MAX",
    "DEFAULT_N_K",
]


DEFAULT_K_MIN = 1.0e-4
DEFAULT_K_MAX = 0.3
DEFAULT_N_K = 24

SUPPORTED_FAMILIES: frozenset[str] = frozenset({
    "FLRW", "I",
    "II", "III", "IV", "V",
    "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX",
})


@dataclass(frozen=True)
class FamilyKGrid:
    """Per-family k-grid bundle with Plancherel weights.

    Attributes
    ----------
    family : str
        Bianchi family label.
    k_vectors : ndarray, shape (n_k, 3)
        Comoving wavenumber vectors. For Type IX the first component
        is the discrete spectral index ℓ_spec; for Type VIII the first
        two components are (s, μ) continuous-Plancherel labels.
    weights : ndarray, shape (n_k,)
        Per-k weights normalised so Σ weights = 1 (when finite).
    branch_label : str
        Short string describing the parametrisation
        (e.g., "su2_discrete", "sl2r_continuous_plus_discrete").
    """

    family: str
    k_vectors: np.ndarray
    weights: np.ndarray
    branch_label: str

    def __post_init__(self) -> None:
        kvecs = np.asarray(self.k_vectors, dtype=np.float64)
        if kvecs.ndim != 2 or kvecs.shape[1] != 3:
            raise ValueError(
                f"k_vectors must have shape (n_k, 3); got {kvecs.shape!r}"
            )
        weights = np.asarray(self.weights, dtype=np.float64)
        if weights.shape != (kvecs.shape[0],):
            raise ValueError(
                f"weights shape {weights.shape!r} != ({kvecs.shape[0]},)"
            )
        object.__setattr__(self, "k_vectors", kvecs)
        object.__setattr__(self, "weights", weights)

    @property
    def n_k(self) -> int:
        return int(self.k_vectors.shape[0])

    def distinct_directions(self) -> int:
        """Count the number of distinct unit-direction vectors.

        Used by the family-coverage audit (V5_ROUND16_02 §3.4 P3): for
        each of the 8 intrinsic-anisotropic families the off-axis grid
        must contain ≥ 2 distinct directions to avoid silent FLRW.
        """
        norms = np.linalg.norm(self.k_vectors, axis=1)
        # Map (k, 0, 0)-like vectors to a single direction; everything
        # with k=0 components in two slots is "axis-aligned".
        directions = set()
        for kv, norm in zip(self.k_vectors, norms):
            if norm == 0.0:
                directions.add(("origin",))
                continue
            unit = kv / norm
            # Round to 6 decimal places to merge near-duplicate floats.
            directions.add(tuple(np.round(unit, 6).tolist()))
        return len(directions)


# ──────────────────────────────────────────────────────────────────────
# Factory helpers
# ──────────────────────────────────────────────────────────────────────


def _continuous_log_k(n_k: int, k_min: float, k_max: float) -> np.ndarray:
    return np.geomspace(k_min, k_max, n_k)


def _flrw_or_typeI_grid(family: str, *, n_k: int, k_min: float, k_max: float) -> FamilyKGrid:
    k_log = _continuous_log_k(n_k, k_min, k_max)
    kvecs = np.zeros((n_k, 3), dtype=np.float64)
    kvecs[:, 0] = k_log
    weights = np.ones(n_k, dtype=np.float64) / float(n_k)
    return FamilyKGrid(
        family=family,
        k_vectors=kvecs,
        weights=weights,
        branch_label="continuous_1d",
    )


def _type_ii_grid(*, n_k1: int, n_k2: int, k_min: float, k_max: float) -> FamilyKGrid:
    """Heisenberg chart: k₁ continuous (log), k₂ ∈ ℤ_{≥0} lattice."""
    k1 = _continuous_log_k(n_k1, k_min, k_max)
    k2 = np.arange(n_k2, dtype=np.float64)  # 0, 1, 2, ...
    kvecs = np.array(
        [(float(k1_v), float(k2_v), 0.0) for k1_v in k1 for k2_v in k2],
        dtype=np.float64,
    )
    n_total = kvecs.shape[0]
    # Nilpotent-Heisenberg Plancherel: weight ∝ |k₂| for k₂ > 0,
    # uniform-log in k₁; we normalise to sum 1.
    weights = np.array(
        [
            (1.0 if k2_v == 0.0 else float(k2_v))
            for _ in k1 for k2_v in k2
        ],
        dtype=np.float64,
    )
    weights /= float(np.sum(weights))
    return FamilyKGrid(
        family="II",
        k_vectors=kvecs, weights=weights,
        branch_label="heisenberg_lattice",
    )


def _type_vi_0_grid(*, n_k1: int, n_k3: int, k_min: float, k_max: float) -> FamilyKGrid:
    """e(1, 1) solvable: k₁ log, k₃ log, k₂ lattice (5 entries)."""
    k1 = _continuous_log_k(n_k1, k_min, k_max)
    k3 = _continuous_log_k(n_k3, k_min, k_max)
    k2 = np.arange(0, 5, dtype=np.float64)
    kvecs = np.array(
        [(float(a), float(c), float(b)) for a in k1 for c in k3 for b in k2],
        dtype=np.float64,
    )
    weights = np.ones(kvecs.shape[0], dtype=np.float64) / float(kvecs.shape[0])
    return FamilyKGrid(
        family="VI_0",
        k_vectors=kvecs, weights=weights,
        branch_label="solvable_e11_lattice",
    )


def _type_vii_0_grid(*, n_kperp: int, n_phi: int, n_k3: int,
                       k_min: float, k_max: float) -> FamilyKGrid:
    """Helical Euclidean: (k_⊥, φ, k₃)."""
    kperp = _continuous_log_k(n_kperp, k_min, k_max)
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    k3 = _continuous_log_k(n_k3, k_min, k_max)
    kvecs = np.array(
        [
            (float(kp) * np.cos(p), float(kp) * np.sin(p), float(z))
            for kp in kperp for p in phi for z in k3
        ],
        dtype=np.float64,
    )
    n_total = kvecs.shape[0]
    weights = np.ones(n_total, dtype=np.float64) / float(n_total)
    return FamilyKGrid(
        family="VII_0",
        k_vectors=kvecs, weights=weights,
        branch_label="helical_euclidean",
    )


def _type_viii_grid(*, n_s: int, n_mu: int, k_min: float, k_max: float) -> FamilyKGrid:
    """sl(2, ℝ) Plancherel: continuous (μ, s) + discrete D^±_λ."""
    s = np.geomspace(max(k_min, 0.01), max(k_max, 5.0), n_s)
    mu = np.linspace(-0.5 + 0.05, 0.5 - 0.05, n_mu)
    cont_kvecs = np.array(
        [(float(s_v), float(mu_v), 0.0) for s_v in s for mu_v in mu],
        dtype=np.float64,
    )
    cont_weights = np.array(
        [
            (1.0 / (4.0 * np.pi ** 2)) * float(s_v)
            * np.sinh(2.0 * np.pi * float(s_v))
            / (
                np.cosh(2.0 * np.pi * float(s_v))
                + np.cos(2.0 * np.pi * float(mu_v))
            )
            for s_v in s for mu_v in mu
        ],
        dtype=np.float64,
    )
    # Discrete series: D^±_λ for λ ∈ {3/2, 5/2, ...}. The boundary
    # λ=1/2 is the singular limit (zero Plancherel weight) and is
    # excluded from the production grid.
    lambdas = np.arange(1.5, 5.5, 1.0)
    disc_kvecs = np.array(
        [(0.0, 0.0, float(l)) for l in lambdas], dtype=np.float64,
    )
    disc_weights = np.array(
        [(1.0 / (4.0 * np.pi ** 2)) * (float(l) - 0.5) for l in lambdas],
        dtype=np.float64,
    )
    kvecs = np.concatenate([cont_kvecs, disc_kvecs], axis=0)
    weights = np.concatenate([cont_weights, disc_weights], axis=0)
    weights /= float(np.sum(weights))
    return FamilyKGrid(
        family="VIII",
        k_vectors=kvecs, weights=weights,
        branch_label="sl2r_continuous_plus_discrete",
    )


def _type_ix_grid(*, ell_max_spec: int) -> FamilyKGrid:
    """SU(2) compact: discrete ℓ_spec."""
    if ell_max_spec < 1:
        raise ValueError(f"ell_max_spec must be >= 1; got {ell_max_spec!r}")
    ells = np.arange(1, ell_max_spec + 1, dtype=np.float64)
    kvecs = np.zeros((ells.size, 3), dtype=np.float64)
    kvecs[:, 0] = ells
    weights = (2.0 * ells + 1.0)
    weights /= float(np.sum(weights))
    return FamilyKGrid(
        family="IX",
        k_vectors=kvecs, weights=weights,
        branch_label="su2_discrete",
    )


def _type_v_grid(*, n_k: int, k_min: float, k_max: float) -> FamilyKGrid:
    """Open hyperbolic: continuous k with off-axis directions."""
    # Off-axis sweep: 12 (k_x, k_y, 0) directions to lift the
    # axisymmetric restriction.
    k_log = _continuous_log_k(n_k, k_min, k_max)
    n_dir = 12
    angles = np.linspace(0.0, 2.0 * np.pi, n_dir, endpoint=False)
    kvecs = np.array(
        [
            (float(k) * np.cos(a), float(k) * np.sin(a), 0.0)
            for k in k_log for a in angles
        ],
        dtype=np.float64,
    )
    weights = np.ones(kvecs.shape[0], dtype=np.float64) / float(kvecs.shape[0])
    return FamilyKGrid(
        family="V",
        k_vectors=kvecs, weights=weights,
        branch_label="open_hyperbolic_continuous_off_axis",
    )


def _type_classB_h_grid(family: str, *, n_k: int, k_min: float,
                          k_max: float) -> FamilyKGrid:
    """III, IV, VI_h, VII_h: continuous k + h-dependent λ.

    For the Round-16 deliverable we sample n_k log-spaced wavenumbers in
    each of 8 directions to lift the axisymmetric restriction. The
    h-dependent eigenvalue offset is absorbed by the family-specific
    chart-normalisation in the LoS propagator (PR-S10).
    """
    k_log = _continuous_log_k(n_k, k_min, k_max)
    n_dir = 8
    angles = np.linspace(0.0, 2.0 * np.pi, n_dir, endpoint=False)
    kvecs = np.array(
        [
            (float(k) * np.cos(a), float(k) * np.sin(a), 0.0)
            for k in k_log for a in angles
        ],
        dtype=np.float64,
    )
    weights = np.ones(kvecs.shape[0], dtype=np.float64) / float(kvecs.shape[0])
    return FamilyKGrid(
        family=family,
        k_vectors=kvecs, weights=weights,
        branch_label=f"class_b_h_continuous_off_axis_{family}",
    )


# ──────────────────────────────────────────────────────────────────────
# Dispatch
# ──────────────────────────────────────────────────────────────────────


def build_family_k_grid(
    family: str,
    *,
    k_min: float = DEFAULT_K_MIN,
    k_max: float = DEFAULT_K_MAX,
    n_k: int = DEFAULT_N_K,
    n_k_secondary: int | None = None,
    ell_max_spec: int = 20,
) -> FamilyKGrid:
    """Build the family-specific k-grid + Plancherel weights.

    Parameters
    ----------
    family : str
        Bianchi family label (one of :data:`SUPPORTED_FAMILIES`).
    k_min, k_max : float
        Continuous-k log-grid bounds.
    n_k : int
        Number of continuous-k samples per axis.
    n_k_secondary : int, optional
        Number of secondary-axis samples (e.g. ℤ-lattice depth for Type
        II); defaults to ``n_k`` when None.
    ell_max_spec : int
        Maximum spectral index for Type IX (1 to ``ell_max_spec``).

    Returns
    -------
    FamilyKGrid
    """
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(
            f"family={family!r} not in SUPPORTED_FAMILIES "
            f"{sorted(SUPPORTED_FAMILIES)!r}"
        )
    if k_min <= 0.0 or k_max <= k_min:
        raise ValueError(
            f"require 0 < k_min < k_max; got k_min={k_min!r}, k_max={k_max!r}"
        )
    if n_k < 2:
        raise ValueError(f"n_k must be >= 2; got {n_k!r}")
    secondary = n_k if n_k_secondary is None else int(n_k_secondary)

    if family in {"FLRW", "I"}:
        return _flrw_or_typeI_grid(
            family, n_k=n_k, k_min=k_min, k_max=k_max,
        )
    if family == "II":
        return _type_ii_grid(
            n_k1=n_k, n_k2=secondary, k_min=k_min, k_max=k_max,
        )
    if family == "VI_0":
        return _type_vi_0_grid(
            n_k1=n_k, n_k3=secondary, k_min=k_min, k_max=k_max,
        )
    if family == "VII_0":
        return _type_vii_0_grid(
            n_kperp=n_k, n_phi=8, n_k3=secondary,
            k_min=k_min, k_max=k_max,
        )
    if family == "VIII":
        return _type_viii_grid(
            n_s=n_k, n_mu=secondary, k_min=k_min, k_max=k_max,
        )
    if family == "IX":
        return _type_ix_grid(ell_max_spec=ell_max_spec)
    if family == "V":
        return _type_v_grid(n_k=n_k, k_min=k_min, k_max=k_max)
    # III, IV, VI_h, VII_h
    return _type_classB_h_grid(
        family, n_k=n_k, k_min=k_min, k_max=k_max,
    )
