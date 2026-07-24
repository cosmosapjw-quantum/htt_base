"""PR-142: MIO joint-measure F/Pi/G_F invariance and matched-null calibration.

MIO owns REPORTING semantics only. This module defines a typed
``MeasureSpec`` (identity, weights, pairing, and depth/reference policy)
and computes three DISTINCT diagnostic quantities over a departure-
component table (Sigma^2, W^2, Omega_tilt, DeltaOmega_k):

* ``F``  — a weighted joint second-moment (RMS) summary;
* ``Pi`` — a weighted first-moment (mean contrast) summary;
* ``G_F`` — the set-valued FEASIBLE RANGE of F over an identified set.

F, Pi, and Q are never interchangeable, and none of them is a posterior
probability, an evidence, a likelihood term, or a truth certificate. The
module reports each quantity's permutation / pairing / depth sensitivity,
a bootstrap uncertainty, and a MATCHED-null distribution (the null MUST
share the spec's weights, pairing, and depth policy); a calibrated scalar
is emitted only when a scientifically-justified measure is registered,
otherwise the status is ``no_justified_measure`` and only measure-family
sensitivity is reported.

Calibrated MIO diagnostic mechanics at ``roadmap_rescue_v1:C2`` — no
posterior, no evidence, no HTT likelihood, no detection.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from numbers import Integral, Real

import numpy as np

SCHEMA_VERSION = "pr142.mio_joint_measure.v1"

COMPONENTS = ("Sigma2", "W2", "Omega_tilt", "DeltaOmega_k")

# quantities MIO must never manufacture from a diagnostic measure
FORBIDDEN_ROLES = ("posterior_probability", "evidence", "bayes_factor",
                   "likelihood_term", "truth_certificate", "htt_likelihood")
# the three diagnostic measures are distinct and never substituted
MEASURE_KINDS = ("F", "Pi", "Q")


class MeasureError(ValueError):
    """Raised when a MIO measure is mis-used or unjustified."""


class MeasureStatus(str, Enum):
    CALIBRATED = "calibrated"
    NO_JUSTIFIED_MEASURE = "no_justified_measure"


class Pairing(str, Enum):
    UNPAIRED = "unpaired"
    PAIRED = "paired"


class DepthPolicy(str, Enum):
    RAW = "raw"
    REFERENCE_SUBTRACTED = "reference_subtracted"


# --------------------------------------------------------------------------
# measure spec
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class MeasureSpec:
    """A joint-measure choice — a scientific assumption, content-addressed.

    ``justified`` records whether the weights/pairing/depth policy are
    scientifically defended; an unjustified spec yields only measure-family
    sensitivity and no calibrated scalar.
    """

    identity: tuple
    weights: tuple
    pairing: Pairing
    depth_policy: DepthPolicy
    null_scale: tuple = ()
    justified: bool = True
    justification: str = ""

    def __post_init__(self) -> None:
        # canonical (fixed physical) order required so relabeling cannot
        # silently change identity
        if not self.identity:
            raise MeasureError("measure identity must not be empty")
        canonical = tuple(c for c in COMPONENTS if c in self.identity)
        if tuple(self.identity) != canonical:
            raise MeasureError("measure identity must be in canonical "
                               "component order")
        if len(self.weights) != len(self.identity):
            raise MeasureError("weights must match the identity length")
        if any(not isinstance(w, Real) or not np.isfinite(float(w))
               for w in self.weights):
            raise MeasureError("weights must be finite real numbers")
        if any(w < 0 for w in self.weights):
            raise MeasureError("weights must be non-negative")
        if not any(w > 0 for w in self.weights):
            raise MeasureError("at least one weight must be positive")
        for c in self.identity:
            if c not in COMPONENTS:
                raise MeasureError(f"unknown component {c!r}")
        if not self.null_scale:
            object.__setattr__(self, "null_scale",
                               tuple(1.0 for _ in self.identity))
        elif len(self.null_scale) != len(self.identity):
            raise MeasureError("null_scale must match the identity length")
        if any(not isinstance(s, Real) or not np.isfinite(float(s)) or s <= 0
               for s in self.null_scale):
            raise MeasureError(
                "null_scale entries must be positive finite real numbers")

    def fingerprint(self) -> str:
        payload = {"identity": list(self.identity),
                   "weights": [float(w) for w in self.weights],
                   "pairing": self.pairing.value,
                   "depth_policy": self.depth_policy.value,
                   "null_scale": [float(s) for s in self.null_scale]}
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def require_justified_measure(spec: MeasureSpec) -> None:
    if not spec.justified:
        raise MeasureError(
            "no scientifically-justified joint measure — report only "
            "measure-family sensitivity, never a calibrated scalar")


# --------------------------------------------------------------------------
# data + depth/pairing handling
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DepartureTable:
    """Rows of departure components, with optional depth and pair indices."""
    values: np.ndarray                       # (n_obs, n_components)
    columns: tuple
    depth: tuple = ()                        # per-row depth-bin id
    pair: tuple = ()                         # per-row pair id (paired only)

    def column_index(self, name: str) -> int:
        return self.columns.index(name)

    def select(self, identity: tuple) -> np.ndarray:
        idx = [self.column_index(c) for c in identity]
        return self.values[:, idx]


def _apply_depth(x: np.ndarray, depth: tuple,
                 policy: DepthPolicy) -> np.ndarray:
    if policy is DepthPolicy.RAW or not depth:
        return x
    # subtract the per-depth-bin mean (a reference policy)
    out = x.copy()
    depth_arr = np.asarray(depth)
    for d in np.unique(depth_arr):
        mask = depth_arr == d
        out[mask] = out[mask] - out[mask].mean(axis=0, keepdims=True)
    return out


def _apply_pairing(x: np.ndarray, pair: tuple,
                   pairing: Pairing) -> np.ndarray:
    if pairing is Pairing.UNPAIRED:
        return x
    if not pair:
        raise MeasureError("a paired measure requires pair indices")
    pair_arr = np.asarray(pair)
    diffs = []
    for p in np.unique(pair_arr):
        rows = np.where(pair_arr == p)[0]
        if len(rows) != 2:
            raise MeasureError("paired data must have exactly two rows/pair")
        diffs.append(x[rows[0]] - x[rows[1]])
    return np.array(diffs)


def _prepare(table: DepartureTable, spec: MeasureSpec) -> np.ndarray:
    x = table.select(spec.identity)
    x = _apply_depth(x, table.depth, spec.depth_policy)
    x = _apply_pairing(x, table.pair, spec.pairing)
    return x


# --------------------------------------------------------------------------
# the three distinct measures
# --------------------------------------------------------------------------
def measure_F(table: DepartureTable, spec: MeasureSpec) -> float:
    """Weighted joint second-moment (RMS) — permutation-symmetric in rows."""
    x = _prepare(table, spec)
    w = np.asarray(spec.weights)
    return float(np.sqrt(np.mean((x ** 2) @ w)))


def measure_Pi(table: DepartureTable, spec: MeasureSpec) -> float:
    """Weighted first-moment (mean contrast) — a DISTINCT summary from F."""
    x = _prepare(table, spec)
    w = np.asarray(spec.weights)
    return float(np.mean(x @ w))


def measured(kind: str, table: DepartureTable, spec: MeasureSpec) -> float:
    if kind == "F":
        return measure_F(table, spec)
    if kind == "Pi":
        return measure_Pi(table, spec)
    raise MeasureError(f"measure {kind!r} is not computed here")


# --------------------------------------------------------------------------
# invariance
# --------------------------------------------------------------------------
def permutation_invariant(table: DepartureTable, spec: MeasureSpec,
                          kind: str, seed: int, n: int = 8) -> bool:
    """F/Pi must be invariant to relabeling the exchangeable rows."""
    base = measured(kind, table, spec)
    rng = np.random.Generator(np.random.PCG64(seed))
    n_rows = table.values.shape[0]
    for _ in range(n):
        perm = rng.permutation(n_rows)
        permuted = DepartureTable(
            values=table.values[perm], columns=table.columns,
            depth=tuple(np.asarray(table.depth)[perm]) if table.depth else (),
            pair=tuple(np.asarray(table.pair)[perm]) if table.pair else ())
        if abs(measured(kind, permuted, spec) - base) > 1e-9:
            return False
    return True


def pairing_counterexample(paired_table: DepartureTable, spec: MeasureSpec,
                           kind: str) -> dict:
    """Applying an unpaired spec to paired data gives a DIFFERENT value."""
    paired_val = measured(kind, paired_table, spec)
    unpaired_spec = MeasureSpec(
        identity=spec.identity, weights=spec.weights,
        pairing=Pairing.UNPAIRED, depth_policy=spec.depth_policy,
        null_scale=spec.null_scale, justified=spec.justified)
    unpaired_val = measured(kind, paired_table, unpaired_spec)
    return {"paired": paired_val, "unpaired": unpaired_val,
            "differ": abs(paired_val - unpaired_val) > 1e-9}


def depth_sensitivity(table: DepartureTable, spec: MeasureSpec,
                      kind: str) -> dict:
    raw = MeasureSpec(identity=spec.identity, weights=spec.weights,
                      pairing=spec.pairing, depth_policy=DepthPolicy.RAW,
                      null_scale=spec.null_scale, justified=spec.justified)
    ref = MeasureSpec(identity=spec.identity, weights=spec.weights,
                      pairing=spec.pairing,
                      depth_policy=DepthPolicy.REFERENCE_SUBTRACTED,
                      null_scale=spec.null_scale, justified=spec.justified)
    v_raw = measured(kind, table, raw)
    v_ref = measured(kind, table, ref)
    return {"raw": v_raw, "reference_subtracted": v_ref,
            "abs_sensitivity": abs(v_raw - v_ref)}


# --------------------------------------------------------------------------
# matched-null calibration
# --------------------------------------------------------------------------
NULL_TYPES = ("sign_flip", "reference_scale")
# one-sided upper for a magnitude (F); two-sided for a signed contrast (Pi)
# tested against a symmetric null whose direction is NOT pre-registered
_SIDEDNESS = {"F": "upper", "Pi": "two_sided"}


def robust_component_scale(table: DepartureTable, spec: MeasureSpec
                           ) -> np.ndarray:
    """Per-component robust (MAD) scale over the identity columns.

    MAD about the median is robust to a location (mean-shift) departure, so
    it estimates the no-signal noise scale even when a signal is present.
    """
    x = table.select(spec.identity)
    med = np.median(x, axis=0)
    mad = np.median(np.abs(x - med), axis=0)
    return mad / 0.6744897501960817


def require_null_scale_consistent(table: DepartureTable, spec: MeasureSpec,
                                  tol: float = 1.5) -> None:
    """The declared reference (noise) scale must match the data's robust
    scale within a factor, so F's p-value is not governed by an arbitrary
    hyperparameter."""
    est = robust_component_scale(table, spec)
    declared = np.asarray(spec.null_scale)
    for c, e, d in zip(spec.identity, est, declared):
        if e <= 0:
            continue
        ratio = d / e
        if ratio < 1.0 / tol or ratio > tol:
            raise MeasureError(
                f"the declared null_scale for {c} ({d:.3f}) is inconsistent "
                f"with the data's robust scale ({e:.3f}) — the reference null "
                "would be governed by a mis-set hyperparameter, not the data")


def matched_null_distribution(table: DepartureTable, spec: MeasureSpec,
                              kind: str, seed: int, n_null: int, *,
                              null_type: str = "reference_scale") -> dict:
    """Null distribution of the measure under a MATCHED null (same spec).

    Two matched nulls, each RECOMPUTED with the same weights, pairing, and
    depth policy: ``sign_flip`` flips each row's sign (a symmetric null for
    a SIGNED contrast such as Pi) and ``reference_scale`` draws rows from
    the per-component reference (noise) scale (a magnitude null for F). The
    reference scale is VALIDATED against the data's robust scale so F's
    p-value is not governed by an arbitrary hyperparameter. A null that
    leaves the measure invariant (e.g. a sign-flip null for the second-
    moment F) is DEGENERATE and refused. The p-value is one-sided upper for
    a magnitude and TWO-SIDED for a signed contrast against a symmetric
    null.
    """
    require_justified_measure(spec)
    if (isinstance(n_null, bool)
            or not isinstance(n_null, Integral)
            or n_null < 2):
        raise MeasureError("n_null must be an integer of at least 2")
    n_null = int(n_null)
    if null_type not in NULL_TYPES:
        raise MeasureError(f"unknown null_type {null_type!r}")
    obs = measured(kind, table, spec)
    rng = np.random.Generator(np.random.PCG64(seed))
    n_rows = table.values.shape[0]
    col_idx = [table.column_index(c) for c in spec.identity]
    scale = np.asarray(spec.null_scale)
    null = np.empty(n_null)
    for i in range(n_null):
        if null_type == "sign_flip":
            signs = rng.choice([-1.0, 1.0], size=n_rows)
            vals = table.values * signs[:, None]
        else:
            if i == 0:
                require_null_scale_consistent(table, spec)
            vals = table.values.copy()
            vals[:, col_idx] = rng.normal(0.0, 1.0, (n_rows, len(col_idx))) \
                * scale[None, :]
        null[i] = measured(kind, DepartureTable(
            values=vals, columns=table.columns, depth=table.depth,
            pair=table.pair), spec)
    null_std = float(null.std())
    if null_std < 1e-9:
        raise MeasureError(
            f"the {null_type!r} matched null is DEGENERATE for measure "
            f"{kind!r} (zero spread) — it does not exercise the measure and "
            "mis-calibrates; use a measure-appropriate null")
    sided = _SIDEDNESS.get(kind, "upper")
    if sided == "two_sided":
        p = float((1 + np.sum(np.abs(null) >= abs(obs))) / (n_null + 1))
    else:
        p = float((1 + np.sum(null >= obs)) / (n_null + 1))
    return {"observed": obs, "p_value": p, "sided": sided, "n_null": n_null,
            "null_type": null_type, "null_mean": float(null.mean()),
            "null_std": null_std, "spec_fingerprint": spec.fingerprint(),
            "status": MeasureStatus.CALIBRATED.value}


def require_matched_null(measure_spec: MeasureSpec,
                         null_spec: MeasureSpec) -> None:
    """The null must be computed with the SAME measure spec."""
    if measure_spec.fingerprint() != null_spec.fingerprint():
        raise MeasureError(
            "the matched-null distribution must share the measure's weights, "
            "pairing, and depth policy — an unmatched null mis-calibrates")


def bootstrap_uncertainty(table: DepartureTable, spec: MeasureSpec,
                          kind: str, seed: int, n_boot: int) -> float:
    """Bootstrap SE of the measure for the SPEC's estimand.

    A paired spec resamples the PAIR CLUSTERS (so the SE quantifies the
    reported paired estimate); an unpaired spec resamples rows.
    """
    rng = np.random.Generator(np.random.PCG64(seed))
    vals = np.empty(n_boot)
    if spec.pairing is Pairing.PAIRED:
        pair_arr = np.asarray(table.pair)
        clusters = list(np.unique(pair_arr))
        for i in range(n_boot):
            chosen = rng.choice(clusters, size=len(clusters))
            rows, new_pair = [], []
            for j, cid in enumerate(chosen):
                cr = np.where(pair_arr == cid)[0]
                rows.extend(cr.tolist())
                new_pair.extend([j] * len(cr))
            resampled = DepartureTable(
                values=table.values[rows], columns=table.columns,
                depth=tuple(np.asarray(table.depth)[rows])
                if table.depth else (), pair=tuple(new_pair))
            vals[i] = measured(kind, resampled, spec)
    else:
        n_rows = table.values.shape[0]
        for i in range(n_boot):
            idx = rng.integers(0, n_rows, n_rows)
            resampled = DepartureTable(
                values=table.values[idx], columns=table.columns,
                depth=tuple(np.asarray(table.depth)[idx])
                if table.depth else (), pair=())
            vals[i] = measured(kind, resampled, spec)
    return float(vals.std(ddof=1))


# --------------------------------------------------------------------------
# G_F: set-valued feasible range (never a scalar posterior)
# --------------------------------------------------------------------------
def feasible_range_GF(component_intervals: dict, spec: MeasureSpec) -> dict:
    """FEASIBLE RANGE of F over an identified set of component bounds.

    Given per-component intervals (an identified set), the extreme weighted
    RMS is attained at the interval endpoints (each squared term is
    monotone in |component|). Returns a set-valued [lo, hi], never a
    point posterior.
    """
    lo_sq = 0.0
    hi_sq = 0.0
    w = dict(zip(spec.identity, spec.weights))
    for c in spec.identity:
        a, b = component_intervals[c]
        lo_abs = 0.0 if a <= 0 <= b else min(abs(a), abs(b))
        hi_abs = max(abs(a), abs(b))
        lo_sq += w[c] * lo_abs ** 2
        hi_sq += w[c] * hi_abs ** 2
    lo, hi = float(np.sqrt(lo_sq)), float(np.sqrt(hi_sq))
    return {"lo": lo, "hi": hi, "kind": "set_valued_feasible_range",
            "degenerate_point": abs(hi - lo) < 1e-12,
            "is_scalar_posterior": False,
            "note": "a feasible RANGE (a set), never a posterior probability; "
                    "even a degenerate single-point range is a feasible value, "
                    "not a probability"}


# --------------------------------------------------------------------------
# typed no-merge guards
# --------------------------------------------------------------------------
def refuse_forbidden_role(role: str) -> None:
    if role in FORBIDDEN_ROLES:
        raise MeasureError(
            f"a MIO diagnostic measure is not a {role} — MIO reports, it "
            "never manufactures inference; the HTT/BASS likelihood is "
            "separate")


def refuse_measure_substitution(declared_kind: str,
                                actual_kind: str) -> None:
    if declared_kind in MEASURE_KINDS and actual_kind in MEASURE_KINDS \
            and declared_kind != actual_kind:
        raise MeasureError(
            f"measure {actual_kind!r} may not be reported as {declared_kind!r}"
            " — F, Pi, and Q are distinct diagnostics")


def require_registered_measure_family(original: MeasureSpec,
                                      revised: MeasureSpec,
                                      supersedes: str | None,
                                      multiplicity: int | None) -> None:
    """Changing weights/pairing after the result is a NEW diagnostic family."""
    if original.fingerprint() != revised.fingerprint():
        if supersedes is None or multiplicity is None:
            raise MeasureError(
                "changing the joint-measure weights or pairing after the "
                "result requires a NEW registered diagnostic family and an "
                "updated look-elsewhere multiplicity")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("f is the posterior ", "probability"),
        ("mio measure is the ", "evidence"),
        ("diagnostic is a ", "truth certificate"),
        ("f substitutes ", "for pi"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise MeasureError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(kind: str, p_value: float, depth_sens: float,
                     status: str) -> str:
    return (
        f"MIO joint measure {kind} (matched-null calibrated): p = "
        f"{p_value:.4f}, depth-policy sensitivity {depth_sens:.4f}, status "
        f"{status}. A calibrated diagnostic summary conditional on the "
        f"registered MeasureSpec only; {kind} is not a posterior, an "
        f"evidence, or an HTT likelihood, and F/Pi/Q are never substituted; "
        f"no detection.")
