#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reference_formalism.py — a dependency-free reference implementation of the
x_C / Q / Pi / F / G_F diagnostic algebra, faithful to the shipped contracts
(htt/mio/formalism/*, htt/src/common/departure_contracts.py), plus the three
audit-driven upgrades:

  F7  DepartureProfile          — sector-resolved signed vector + cancellation
  F8  total_anisotropy_magnitude — unsigned magnitude companion to F
  F9  CANONICAL_REGISTRY + firewall — reserved-language refusal + label registry

This is a *reference / demonstration* module (stdlib only) so the experiments
run anywhere. It mirrors the contract semantics; it is NOT the production code
(which lives in the htt.* package and depends on `common`). Where the production
code raises, this module raises FormalismError with the same intent.

No detection, evidence, posterior, family, or geometry claim is implied by any
quantity here. All quantities are diagnostic-only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class FormalismError(ValueError):
    """Raised when a diagnostic would be constructed in an invalid/over-claimed form."""


# --------------------------------------------------------------------------- #
# Canonical sign convention (verbatim from component_breakdown.py)
# --------------------------------------------------------------------------- #

CANONICAL_COMPONENT_SIGNS: dict[str, float] = {
    "Sigma2_std": 1.0,    # shear^2          -> +
    "W2_std": -1.0,       # vorticity^2      -> -
    "Omega_tilt": 1.0,    # tilt             -> +
    "Omega_k_aniso": 1.0, # anisotropic curv -> +
}
CANONICAL_COMPONENT_ORDER = tuple(CANONICAL_COMPONENT_SIGNS)

COMPARATORS = ("flat", "matched", "closed")

# --------------------------------------------------------------------------- #
# F9 — semantic firewall: reserved-language sets + canonical symbol registry
# --------------------------------------------------------------------------- #

# Union of the reserved terms enforced across Q/Pi/F/G_F metadata in the
# production contracts. A diagnostic refuses construction if any appears.
RESERVED_LANGUAGE: tuple[str, ...] = (
    "occupancy", "filling", "physical occupancy", "volume fraction",
    "certified occupancy", "occupied sector",
    "posterior", "posterior odds", "evidence", "likelihood", "bayes factor",
    "model weight", "truth probability", "probability anisotropy true",
    "truth certificate", "certifies truth", "model-independent proof",
    "family id", "family identification", "family identified",
    "family classification", "geometry", "class label", "class-label",
    "solver result", "native solver result", "validated as native",
    "native validated", "global tilt", "morphology compatibility", "detection",
)

# Canonical symbol -> (owner, one-line definition, keyword that MUST appear in
# any figure/table definition that uses the symbol). Used by the label linter.
CANONICAL_REGISTRY: dict[str, dict[str, str]] = {
    "x":   {"owner": "MIO", "definition": "signed comparator projection "
            "Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso", "keyword": "projection"},
    "Q":   {"owner": "MIO", "definition": "numerator_policy(x_C) over an explicit "
            "denominator U", "keyword": "denominator"},
    "Pi":  {"owner": "MIO", "definition": "empirical exceedance-fraction curve over "
            "Q or F samples", "keyword": "exceedance"},
    "F":   {"owner": "MIO", "definition": "certified filling fraction = sample-wise "
            "x_C / admissible ceiling U", "keyword": "filling"},
    "G_F": {"owner": "MIO", "definition": "floor-stabilized depth-bin ratio "
            "exp(log F_cmp - log F_ref)", "keyword": "ratio"},
}


def _normalise(text: str) -> str:
    return "".join(ch if ch.isalnum() else " " for ch in str(text).lower())


def scan_reserved_language(value: object, name: str = "metadata") -> None:
    """Raise FormalismError if any reserved overclaim term appears in `value`."""
    flat = _normalise(_flatten_text(value))
    for term in RESERVED_LANGUAGE:
        if _normalise(term) in flat:
            raise FormalismError(
                f"{name} must not use reserved diagnostic language: {term!r}"
            )


def _flatten_text(value: object) -> str:
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(k) + " " + _flatten_text(v)
                        for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(v) for v in value)
    return str(value)


def lint_figure_label(symbol: str, owner: str, definition: str) -> list[str]:
    """Return a list of problems if a plotted symbol's owner/definition
    contradicts the canonical registry. Empty list == OK. (Seed for U3.)"""
    problems: list[str] = []
    sym = "G_F" if symbol in ("G", "G_F") else symbol
    if sym not in CANONICAL_REGISTRY:
        return [f"unknown symbol {symbol!r}"]
    canon = CANONICAL_REGISTRY[sym]
    if owner != canon["owner"]:
        problems.append(f"{sym}: owner {owner!r} != canonical {canon['owner']!r}")
    if canon["keyword"] not in definition.lower():
        problems.append(
            f"{sym}: definition {definition!r} missing canonical keyword "
            f"{canon['keyword']!r} (canonical: {canon['definition']!r})")
    return problems


def _finite(x: object, name: str) -> float:
    v = float(x)
    if not math.isfinite(v):
        raise FormalismError(f"{name} must be finite")
    return v


def _positive_finite(x: object, name: str) -> float:
    v = _finite(x, name)
    if v <= 0.0:
        raise FormalismError(f"{name} must be positive finite")
    return v


# --------------------------------------------------------------------------- #
# F2 / F7 — signed coordinate x_C, cancellation index, sector-resolved profile
# --------------------------------------------------------------------------- #


def x_C(components: Mapping[str, float]) -> float:
    """Signed comparator projection (NOT a magnitude)."""
    if set(components) != set(CANONICAL_COMPONENT_ORDER):
        raise FormalismError(
            f"components must be exactly {CANONICAL_COMPONENT_ORDER}")
    return float(sum(CANONICAL_COMPONENT_SIGNS[k] * _finite(components[k], k)
                     for k in CANONICAL_COMPONENT_ORDER))


def absolute_component_total(components: Mapping[str, float]) -> float:
    return float(sum(abs(_finite(components[k], k)) for k in CANONICAL_COMPONENT_ORDER))


def cancellation_index(components: Mapping[str, float]) -> float:
    """1 - |x_C| / sum|components|.  1 == full cancellation, 0 == no cancellation."""
    total = absolute_component_total(components)
    if total == 0.0:
        return 0.0
    return float(1.0 - min(abs(x_C(components)) / total, 1.0))


def total_anisotropy_magnitude(components: Mapping[str, float],
                               ceiling: float | None = None) -> float:
    """F8 companion: unsigned total-anisotropy magnitude (optionally /ceiling).
    Diverges from F exactly under cancellation -- the informative case."""
    mag = absolute_component_total(components)
    if ceiling is None:
        return mag
    return mag / _positive_finite(ceiling, "ceiling")


@dataclass(frozen=True)
class DepartureProfile:
    """F7: the canonical reported unit -- the signed sector vector plus the
    scalar and the cancellation diagnostic. The bare scalar is *derived*."""
    components: Mapping[str, float]
    comparator: str = "flat"
    frame: str = "O-frame"
    units: str = "dimensionless"

    def __post_init__(self) -> None:
        if self.comparator not in COMPARATORS:
            raise FormalismError(f"comparator must be one of {COMPARATORS}")
        x_C(self.components)  # validates component names/finiteness

    @property
    def x_C(self) -> float:
        return x_C(self.components)

    @property
    def signed_contributions(self) -> dict[str, float]:
        return {k: CANONICAL_COMPONENT_SIGNS[k] * float(self.components[k])
                for k in CANONICAL_COMPONENT_ORDER}

    @property
    def cancellation_index(self) -> float:
        return cancellation_index(self.components)

    @property
    def total_magnitude(self) -> float:
        return absolute_component_total(self.components)

    def as_report(self) -> dict[str, object]:
        return {
            "comparator": self.comparator, "frame": self.frame, "units": self.units,
            "components": dict(self.components),
            "signed_contributions": self.signed_contributions,
            "x_C": self.x_C, "total_magnitude": self.total_magnitude,
            "cancellation_index": self.cancellation_index,
            "note": "x_C is a SIGNED projection; x_C~0 reflects inter-sector "
                    "cancellation, not isotropy. Read the sector vector + "
                    "total_magnitude.",
        }


# --------------------------------------------------------------------------- #
# Budget / ceiling policy (positive-finite denominator; admissibility gate)
# --------------------------------------------------------------------------- #

_CERTIFYING_POLICIES = {"MES_linear"}  # only the analytic linear ceiling may certify F


@dataclass(frozen=True)
class BudgetSpec:
    denominator_value: float
    policy: str = "MES_linear"
    is_admissible_ceiling: bool = False
    comparator: str = "flat"
    denominator_label: str = "U"
    assumptions: tuple[str, ...] = ("diagnostic_only",)

    def __post_init__(self) -> None:
        _positive_finite(self.denominator_value, "denominator_value")
        scan_reserved_language((self.denominator_label, *self.assumptions), "budget")
        if self.is_admissible_ceiling and self.policy not in _CERTIFYING_POLICIES:
            raise FormalismError(
                f"policy {self.policy!r} cannot be an admissible certified ceiling "
                f"(only {_CERTIFYING_POLICIES} may certify filling)")


# --------------------------------------------------------------------------- #
# F3 — Q (policy-normalized score)
# --------------------------------------------------------------------------- #

_NUMERATOR_POLICIES = ("signed", "absolute", "positive_part")


def numerator_value(xc: float, policy: str) -> float:
    if policy not in _NUMERATOR_POLICIES:
        raise FormalismError(f"numerator policy must be one of {_NUMERATOR_POLICIES}")
    xc = _finite(xc, "x_C")
    if policy == "signed":
        return xc
    if policy == "absolute":
        return abs(xc)
    return max(xc, 0.0)


def Q(profile: DepartureProfile, budget: BudgetSpec, *,
      numerator_policy: str = "absolute",
      metadata: Mapping[str, object] | None = None) -> float:
    """Q = numerator_policy(x_C) / U.  Denominator positive-finite-enforced;
    reserved-language scanned."""
    if budget.comparator != profile.comparator:
        raise FormalismError("Q comparator must match profile and budget")
    if metadata is not None:
        scan_reserved_language(metadata, "Q.metadata")
    val = numerator_value(profile.x_C, numerator_policy) / budget.denominator_value
    return _finite(val, "Q")


# --------------------------------------------------------------------------- #
# F4 — Pi (registered-threshold exceedance curve)
# --------------------------------------------------------------------------- #

_MEASURE_KINDS = ("sample_distribution", "bootstrap_mock_distribution",
                  "null_ensemble", "cross_check_pushforward")
_POST_HOC_TERMS = ("post hoc", "post-hoc", "after looking", "after scan",
                   "data dependent", "data-dependent", "chosen after")


@dataclass(frozen=True)
class ExceedanceCurve:
    """Pi: empirical survival fraction of nonnegative Q/F samples over thresholds."""
    sample_values: tuple[float, ...]
    source_score_label: str = "Q"          # "Q" or "F"
    measure_kind: str = "sample_distribution"
    threshold_policy: str = "curve_only"   # "curve_only" or "pre_registered"
    thresholds: tuple[float, ...] | None = None
    selected_threshold: float | None = None
    registration_hash: str | None = None
    selection_rule: str | None = None
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if self.source_score_label not in ("Q", "F"):
            raise FormalismError("source_score_label must be 'Q' or 'F'")
        if self.measure_kind not in _MEASURE_KINDS:
            raise FormalismError(f"measure_kind must be one of {_MEASURE_KINDS}")
        samples = tuple(_finite(v, "sample") for v in self.sample_values)
        if not samples:
            raise FormalismError("sample_values must be non-empty")
        if any(v < 0.0 for v in samples):
            raise FormalismError("Pi requires nonnegative samples "
                                 "(use absolute/positive_part Q, or F)")
        object.__setattr__(self, "sample_values", samples)
        thr = tuple(sorted(set(self.thresholds if self.thresholds is not None
                               else samples)))
        object.__setattr__(self, "thresholds", thr)
        if self.metadata is not None:
            scan_reserved_language(self.metadata, "Pi.metadata")
        if self.threshold_policy == "curve_only":
            if self.selected_threshold is not None:
                raise FormalismError("curve_only forbids a selected_threshold")
        elif self.threshold_policy == "pre_registered":
            if self.selected_threshold is None or self.registration_hash is None \
                    or self.selection_rule is None:
                raise FormalismError("pre_registered requires selected_threshold, "
                                     "registration_hash, and selection_rule")
            if _normalise_lower(self.selection_rule) and any(
                    t in self.selection_rule.lower() for t in _POST_HOC_TERMS):
                raise FormalismError("pre_registered threshold cannot be post-hoc")
            if self.selected_threshold not in thr:
                raise FormalismError("selected_threshold must appear in thresholds")
        else:
            raise FormalismError("threshold_policy must be curve_only|pre_registered")

    def exceedance_fraction(self, threshold: float) -> float:
        n = len(self.sample_values)
        return sum(1 for v in self.sample_values if v > threshold) / n

    @property
    def curve(self) -> list[tuple[float, float]]:
        return [(t, self.exceedance_fraction(t)) for t in self.thresholds]

    @property
    def selected_exceedance(self) -> float | None:
        if self.selected_threshold is None:
            return None
        return self.exceedance_fraction(self.selected_threshold)


def _normalise_lower(s: object) -> str:
    return str(s).lower()


# --------------------------------------------------------------------------- #
# F3 — F (fail-closed certified filling fraction)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CertifiedFillingFraction:
    """F = sample-wise x_C/U. Constructible only when every sample is sign-clean
    (x_C>=0), the ceiling is admissible, and 0<=F<=1 WITHOUT clipping."""
    profiles: tuple[DepartureProfile, ...]
    budgets: tuple[BudgetSpec, ...]
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if len(self.profiles) != len(self.budgets) or not self.profiles:
            raise FormalismError("profiles and budgets must be equal, non-empty")
        if self.metadata is not None:
            scan_reserved_language(self.metadata, "F.metadata")
        for i, (p, b) in enumerate(zip(self.profiles, self.budgets)):
            if not b.is_admissible_ceiling:
                raise FormalismError(f"F sample {i}: ceiling not admissible")
            if b.comparator != p.comparator:
                raise FormalismError(f"F sample {i}: comparator mismatch")
            xc = p.x_C
            if xc < 0.0:
                raise FormalismError(
                    f"F sample {i}: requires sign-clean nonnegative x_C "
                    f"(got {xc:.3e}); cancellation/vortical sector not certifiable")
            f = xc / b.denominator_value
            if not 0.0 <= f <= 1.0:
                raise FormalismError(
                    f"F sample {i}: F={f:.3e} outside [0,1] (no clipping)")

    @property
    def f_samples(self) -> tuple[float, ...]:
        return tuple(p.x_C / b.denominator_value
                     for p, b in zip(self.profiles, self.budgets))

    @property
    def F_value(self) -> float:                 # mean of sample-wise ratios
        fs = self.f_samples
        return math.fsum(fs) / len(fs)

    @property
    def magnitude_companion(self) -> float:     # F8: unsigned total / ceiling
        ms = [total_anisotropy_magnitude(p.components, b.denominator_value)
              for p, b in zip(self.profiles, self.budgets)]
        return math.fsum(ms) / len(ms)


# --------------------------------------------------------------------------- #
# F5 — G_F (denominator-evolution-split, floor-stabilized depth gap)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DepthBin:
    bin_id: str
    F: CertifiedFillingFraction
    depth_min: float
    depth_max: float
    covariance_status: str = "diagnostic_unmatched_covariance"
    null_mock_status: str = "diagnostic_unmatched_null"

    def __post_init__(self) -> None:
        if self.depth_max <= self.depth_min:
            raise FormalismError("depth_max must exceed depth_min")
        # G_F requires EXPLICIT (non-'not_statistical') covariance & null statuses
        for s, n in ((self.covariance_status, "covariance_status"),
                     (self.null_mock_status, "null_mock_status")):
            if s == "not_statistical":
                raise FormalismError(f"G_F depth bin requires explicit {n}")

    @property
    def f_value(self) -> float:
        return self.F.F_value


@dataclass(frozen=True)
class IsotropyGap:
    """G_F = exp(log max(F_cmp,floor) - log max(F_ref,floor)).  Carries a
    denominator-evolution split and refuses 'global tilt' language."""
    bins: tuple[DepthBin, ...]
    reference_bin_id: str
    comparison_bin_id: str
    floor_value: float = 1e-3
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if len(self.bins) < 2:
            raise FormalismError("G_F requires >= 2 depth bins")
        ids = [b.bin_id for b in self.bins]
        if len(set(ids)) != len(ids):
            raise FormalismError("depth bin ids must be unique")
        ordered = sorted(self.bins, key=lambda b: b.depth_min)
        for a, c in zip(ordered, ordered[1:]):
            if a.depth_max > c.depth_min:
                raise FormalismError("depth bins must not overlap")
        if self.reference_bin_id == self.comparison_bin_id:
            raise FormalismError("reference and comparison bins must differ")
        if not 0.0 < self.floor_value <= 1.0:
            raise FormalismError("floor_value must be in (0, 1]")
        if self.metadata is not None:
            scan_reserved_language(self.metadata, "G_F.metadata")
        by = {b.bin_id: b for b in self.bins}
        if self.reference_bin_id not in by or self.comparison_bin_id not in by:
            raise FormalismError("reference/comparison bin ids must exist")

    def _by_id(self) -> dict[str, DepthBin]:
        return {b.bin_id: b for b in self.bins}

    def effective_F(self, bin_id: str) -> float:
        return max(self._by_id()[bin_id].f_value, self.floor_value)

    def floor_applied(self, bin_id: str) -> bool:
        return self._by_id()[bin_id].f_value < self.floor_value

    @property
    def log_g_F(self) -> float:
        return (math.log(self.effective_F(self.comparison_bin_id))
                - math.log(self.effective_F(self.reference_bin_id)))

    @property
    def G_F(self) -> float:
        return math.exp(self.log_g_F)

    def denominator_evolution_split(self) -> dict[str, object]:
        ref, cmp = self._by_id()[self.reference_bin_id], \
            self._by_id()[self.comparison_bin_id]
        return {
            "F_by_bin": {b.bin_id: b.f_value for b in self.bins},
            "floor_applied_by_bin": {b.bin_id: self.floor_applied(b.bin_id)
                                     for b in self.bins},
            "F_depth_delta": cmp.f_value - ref.f_value,
            "note": "F can change across depth via the numerator (x_C) OR the "
                    "denominator (ceiling). Report sample-wise arrays to attribute.",
        }


__all__ = [
    "FormalismError", "CANONICAL_COMPONENT_SIGNS", "CANONICAL_REGISTRY",
    "RESERVED_LANGUAGE", "COMPARATORS", "scan_reserved_language",
    "lint_figure_label", "x_C", "cancellation_index", "absolute_component_total",
    "total_anisotropy_magnitude", "DepartureProfile", "BudgetSpec", "Q",
    "numerator_value", "ExceedanceCurve", "CertifiedFillingFraction", "DepthBin",
    "IsotropyGap",
]
