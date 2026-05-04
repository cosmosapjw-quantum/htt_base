"""bass/inference/planck_likelihood.py — Round-16 PR-S14 Planck likelihood scaffold.

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §6.1 (closes Round-16 gap
**G8**: no real-data Planck likelihood binding — inference whitelist
is synthetic-only).

Provides:
- :class:`PlanckDataset` — declares the dataset tier (synthetic vs real)
  and the Plik low-ℓ subset (TT only for Round-16; TE/EE/BB deferred).
- :class:`PlanckLikelihood` — evaluates the Plik low-ℓ Gaussian
  likelihood per Planck 2018 §2.2.3 eq. 6, gated by:
  (a) ``dataset.kind == "planck2018_plik_low_l_tt_only"``;
  (b) all 14 upstream gates open (caller-supplied
      ``GateLadderDecision``);
  (c) FLRW-only family scope. Bianchi real-data fitting requires a
      harmonic/template covariance likelihood, not this C_l-only path.
- :class:`FittingBlockedError` — surfaces gate-block reasons loudly.

The wrapper intentionally raises rather than silently falling back to a
synthetic surrogate when:
- The dataset.kind whitelist forbids real-data fitting.
- A non-FLRW Bianchi family is routed into the C_l-only Planck path.
- Any upstream gate of the 15-stage ``GATE_LADDER`` is closed.

Round-16 scope: TT-only Plik low-ℓ Gaussian (the simplest, gauge-
invariant likelihood). Polarisation (TE, EE, BB), high-ℓ (Plik HL),
and the full Planck 2018 wrapper are deferred until Tier-C ship gate.

References
----------
- ``docs/V5_ROUND16_03_OBSERVABLES_LAYER.md §6.1`` — implementation spec.
- Planck Collaboration 2018 V (likelihoods), §2.2.3 — Plik low-ℓ
  Gaussian.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal, Mapping

import numpy as np

__all__ = [
    "PLANCK_2018_LOWL_TT_DATASET_KIND",
    "ALLOWED_DATASET_KINDS",
    "PlanckDataset",
    "GateLadderDecision",
    "PlanckLikelihood",
    "FittingBlockedError",
    "load_planck_low_l_tt_dataset",
]


PLANCK_2018_LOWL_TT_DATASET_KIND = "planck2018_plik_low_l_tt_only"


#: Allowed dataset.kind whitelist for Round-16 (extends in Tier-C).
ALLOWED_DATASET_KINDS: frozenset[str] = frozenset({
    "synthetic_gaussian",                # development & null tests
    "synthetic_with_bianchi_template",   # null + injected templates
    PLANCK_2018_LOWL_TT_DATASET_KIND,    # real Planck 2018 Plik low-ℓ TT
})


class FittingBlockedError(RuntimeError):
    """Raised by :meth:`PlanckLikelihood.log_likelihood` when gates fail.

    Carries the missing-gate set and the proposed dataset.kind.
    """

    def __init__(
        self, message: str, *,
        missing_gates: Iterable[str] = (),
        dataset_kind: str | None = None,
    ) -> None:
        super().__init__(message)
        self.missing_gates: tuple[str, ...] = tuple(missing_gates)
        self.dataset_kind: str | None = dataset_kind


# ──────────────────────────────────────────────────────────────────────
# Dataset descriptor
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlanckDataset:
    """Descriptor for a Planck-likelihood dataset.

    Attributes
    ----------
    kind : str
        One of :data:`ALLOWED_DATASET_KINDS`. Real-data fits require
        ``"planck2018_plik_low_l_tt_only"``.
    path : Path | None
        Filesystem path to the dataset fixture (None for synthetic).
    ell_min, ell_max : int
        Inclusive multipole range.
    C_l_obs : ndarray
        Observed bandpowers, shape ``(ell_max - ell_min + 1,)``.
    sigma : ndarray
        Per-bandpower 1σ errors, same shape.
    """

    kind: str
    path: Path | None
    ell_min: int
    ell_max: int
    C_l_obs: np.ndarray
    sigma: np.ndarray

    def __post_init__(self) -> None:
        if self.kind not in ALLOWED_DATASET_KINDS:
            raise ValueError(
                f"Unknown dataset kind {self.kind!r}; allowed: "
                f"{sorted(ALLOWED_DATASET_KINDS)!r}"
            )
        if self.ell_max < self.ell_min:
            raise ValueError(
                f"ell_max={self.ell_max} < ell_min={self.ell_min}"
            )
        path = None if self.path is None else Path(self.path)
        if self.kind == PLANCK_2018_LOWL_TT_DATASET_KIND:
            if path is None:
                raise ValueError("real Planck low-l TT datasets require a path")
            if not path.is_file():
                raise FileNotFoundError(
                    f"Planck low-l TT dataset file not found: {path}"
                )
            if path.stat().st_size <= 0:
                raise ValueError(
                    f"Planck low-l TT dataset file is empty: {path}"
                )
        cls = np.asarray(self.C_l_obs, dtype=np.float64)
        sig = np.asarray(self.sigma, dtype=np.float64)
        n = self.ell_max - self.ell_min + 1
        if cls.shape != (n,):
            raise ValueError(
                f"C_l_obs shape {cls.shape!r} != ({n},)"
            )
        if sig.shape != (n,):
            raise ValueError(f"sigma shape {sig.shape!r} != ({n},)")
        if not np.all(sig > 0.0):
            raise ValueError("All sigma entries must be strictly positive.")
        if not np.all(np.isfinite(cls)):
            raise ValueError("All C_l_obs entries must be finite.")
        if not np.all(np.isfinite(sig)):
            raise ValueError("All sigma entries must be finite.")
        object.__setattr__(self, "C_l_obs", cls)
        object.__setattr__(self, "sigma", sig)
        object.__setattr__(self, "path", path)

    @classmethod
    def from_low_l_text(
        cls,
        path: Path | str,
        *,
        kind: str = PLANCK_2018_LOWL_TT_DATASET_KIND,
    ) -> "PlanckDataset":
        """Load a low-l TT table with columns ``ell C_l sigma``.

        This intentionally remains a narrow adapter: it verifies that the
        multipoles are integer, contiguous, and backed by a real non-empty
        file, then delegates the same fitting gates as the manual constructor.
        """

        table_path = Path(path)
        data = np.loadtxt(table_path, comments="#", ndmin=2)
        if data.ndim != 2 or data.shape[1] < 3:
            raise ValueError(
                "Planck low-l TT text dataset must have columns ell C_l sigma"
            )
        ell = np.asarray(data[:, 0], dtype=np.float64)
        rounded = np.rint(ell).astype(int)
        if not np.allclose(ell, rounded, atol=0.0, rtol=0.0):
            raise ValueError("Planck low-l TT ell column must be integer valued")
        if rounded.size == 0:
            raise ValueError("Planck low-l TT text dataset is empty")
        expected = np.arange(int(rounded[0]), int(rounded[-1]) + 1, dtype=int)
        if rounded.shape != expected.shape or not np.array_equal(rounded, expected):
            raise ValueError("Planck low-l TT ell column must be contiguous")
        return cls(
            kind=kind,
            path=table_path,
            ell_min=int(rounded[0]),
            ell_max=int(rounded[-1]),
            C_l_obs=np.asarray(data[:, 1], dtype=np.float64),
            sigma=np.asarray(data[:, 2], dtype=np.float64),
        )


def load_planck_low_l_tt_dataset(path: Path | str) -> PlanckDataset:
    """Load the audited text-backed Planck low-l TT dataset format."""

    return PlanckDataset.from_low_l_text(path)


# ──────────────────────────────────────────────────────────────────────
# Gate-ladder decision (caller-supplied)
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GateLadderDecision:
    """Decision payload from :func:`bass.validation.hard_gate_before_fitting`.

    The caller assembles this from the gate-bundle registry; we
    re-declare the minimal fields here so this module does not import
    the full validation layer (keeps the scaffold lightweight).
    """

    allowed: bool
    missing_gates: tuple[str, ...] = ()
    template_card_authorized: bool = False
    family: str = "FLRW"

    def __post_init__(self) -> None:
        object.__setattr__(self, "missing_gates", tuple(self.missing_gates))


# ──────────────────────────────────────────────────────────────────────
# Likelihood
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlanckLikelihood:
    """Plik low-ℓ Gaussian (TT only) per Planck 2018 §2.2.3 eq. 6.

    Parameters
    ----------
    dataset : PlanckDataset
        Bandpower data + errors. Must satisfy the Round-16 whitelist.
    """

    dataset: PlanckDataset

    def log_likelihood(
        self,
        theory_C_l: np.ndarray,
        *,
        gate_decision: GateLadderDecision,
        family: str | None = None,
    ) -> float:
        """Plik low-ℓ Gaussian log-likelihood.

        Parameters
        ----------
        theory_C_l : ndarray
            Theory C_ℓ at every ℓ ∈ [0, dataset.ell_max]; the slice
            [ell_min, ell_max] is compared against the observation.
        gate_decision : GateLadderDecision
            Snapshot of the 15-stage gate ladder + template-card
            authorisation.
        family : str, optional
            Bianchi family being fit. Required for the template-card
            check when the dataset is real Planck.

        Raises
        ------
        FittingBlockedError
            When any gate predicate is violated.
        """
        # Gate 1: dataset.kind whitelist.
        if self.dataset.kind not in ALLOWED_DATASET_KINDS:
            raise FittingBlockedError(
                f"dataset.kind={self.dataset.kind!r} not in whitelist",
                dataset_kind=self.dataset.kind,
            )

        is_real_data = self.dataset.kind == PLANCK_2018_LOWL_TT_DATASET_KIND
        if is_real_data:
            # Gate 2: the 15-stage gate ladder must all be open.
            if not gate_decision.allowed:
                raise FittingBlockedError(
                    "Real-data Planck fitting blocked: upstream gates "
                    f"closed: {gate_decision.missing_gates!r}",
                    missing_gates=gate_decision.missing_gates,
                    dataset_kind=self.dataset.kind,
                )
            inference_family = family if family is not None else gate_decision.family
            if inference_family != "FLRW":
                raise FittingBlockedError(
                    "Real-data Planck TT-only C_l likelihood is FLRW-limit "
                    f"only; family={inference_family!r} requires a harmonic "
                    "template/covariance likelihood gate",
                    missing_gates=("harmonic_template_likelihood_gate",),
                    dataset_kind=self.dataset.kind,
                )

        # All gates passed → evaluate Gaussian log-likelihood.
        theory = np.asarray(theory_C_l, dtype=np.float64)
        if theory.size <= self.dataset.ell_max:
            raise ValueError(
                f"theory_C_l size {theory.size} insufficient for "
                f"ell_max={self.dataset.ell_max}"
            )
        slice_th = theory[self.dataset.ell_min : self.dataset.ell_max + 1]
        diff = slice_th - self.dataset.C_l_obs
        chi_sq = float(np.sum((diff / self.dataset.sigma) ** 2))
        return -0.5 * chi_sq


# ──────────────────────────────────────────────────────────────────────
# Convenience constructors
# ──────────────────────────────────────────────────────────────────────


def make_synthetic_dataset(
    *,
    C_l_truth: np.ndarray,
    ell_min: int = 2,
    ell_max: int = 30,
    relative_error: float = 0.05,
    rng: np.random.Generator | None = None,
) -> PlanckDataset:
    """Build a Gaussian synthetic dataset for development.

    Used by tests and inference-driver smoke tests; the resulting
    :class:`PlanckDataset` carries ``kind = "synthetic_gaussian"``,
    so :meth:`PlanckLikelihood.log_likelihood` will not gate-block it.
    """
    if rng is None:
        rng = np.random.default_rng(seed=1)
    truth = np.asarray(C_l_truth, dtype=np.float64)
    if truth.size <= ell_max:
        raise ValueError(
            f"C_l_truth size {truth.size} insufficient for ell_max={ell_max}"
        )
    sigma = relative_error * np.maximum(np.abs(truth[ell_min : ell_max + 1]), 1.0e-30)
    obs = truth[ell_min : ell_max + 1] + sigma * rng.standard_normal(sigma.size)
    return PlanckDataset(
        kind="synthetic_gaussian",
        path=None,
        ell_min=ell_min,
        ell_max=ell_max,
        C_l_obs=obs,
        sigma=sigma,
    )
