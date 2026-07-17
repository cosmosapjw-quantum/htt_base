"""PR-126 one-way FLRW/EGS statement and counterexample registry.

The exact-EGS and almost-EGS premise sets are separated in a typed
premise registry (edge-free in this PR; dependency edges are later work)
whose theorem ids are CONTENT-ADDRESSED over (premise-id set, statement):
editing a premise structurally mints a NEW theorem id, so a counterexample
can never be silenced post-hoc under the old id.

The sealed pair (never separated):

- FORWARD (one-way): every premise-complete FLRW-limit comparator state
  (beta = sigma2 = w2 = omega_tilt = delta_omega_k = 0) has
  ``x_C = sigma2 - w2 + omega_tilt + delta_omega_k = 0`` exactly.
- CONVERSE COUNTEREXAMPLES: constructive states with ``x_C = 0`` and
  nonzero departures — ``x_C = 0`` NEVER implies the FLRW limit.

Almost-EGS is SPECIFIED_ONLY: no quantitative regularity or remainder is
registered, so no almost statement is claimable here. Conditional
mathematics at roadmap_rescue_v1:C2 — no FLRW certificate, no converse,
no scalar-to-geometry language, and no observational claim.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping, Sequence

from common.frame_contract import (
    FrameContractError,
    KinematicState,
    flrw_limit,
)

SCHEMA_VERSION = "pr126.egs_oneway.v1"


class EgsOnewayError(ValueError):
    """Raised on any one-way/premise-governance violation (fail-closed)."""


# ---------------------------------------------------------------------------
# premise DAG (typed; ids are stable, theorems are content-addressed)
# ---------------------------------------------------------------------------

EXACT_EGS_PREMISES = {
    "EGS-P0-expanding_congruence": (
        "the congruence is expanding (theta != 0) — without this EGS 1968 "
        "concludes only 'stationary OR FLRW'"),
    "EGS-P1-radiation_isotropy_every_fundamental_observer": (
        "the radiation field is exactly isotropic for every fundamental "
        "observer of the congruence"),
    "EGS-P2-collisionless_liouville_radiation": (
        "the radiation obeys the collisionless Boltzmann/Liouville "
        "equation (Einstein-Liouville system, classical EGS 1968)"),
    "EGS-P3-geodesic_matter_congruence": (
        "the matter congruence is geodesic (vanishing acceleration)"),
    "EGS-P4-barotropic_matter_generalization": (
        "barotropic perfect-fluid matter — a LATER generalization lineage "
        "(Ellis-Treciokas / Clarkson-Barrett), NOT a classical EGS 1968 "
        "premise; registered separately for the generalized statements"),
    "EGS-P5-differentiability_working_class": (
        "a registered working differentiability assumption (C^3); the "
        "precise classical regularity class is NOT attributed here"),
}

ALMOST_EGS_PREMISES = {
    "AEGS-P1-almost_isotropy_bounded_multipoles": (
        "the radiation multipoles are bounded by small epsilons for every "
        "fundamental observer"),
    "AEGS-P2-regularity_class_UNREGISTERED": (
        "a quantitative regularity/derivative-bound class — UNREGISTERED: "
        "no such registration exists in this repository"),
}
ALMOST_EGS_STATUS = "SPECIFIED_ONLY_no_quantitative_regularity_or_remainder"

COMPARATOR_FORWARD_PREMISES = {
    "CMP-P1-beta_zero": "beta == 0 (no tilt)",
    "CMP-P2-sigma2_zero": "sigma2 == 0 (no shear)",
    "CMP-P3-w2_zero": "w2 == 0 (no vorticity)",
    "CMP-P4-delta_omega_k_zero": "delta_omega_k == 0 (no anisotropic curvature)",
    "CMP-P5-omega_tilt_zero": "omega_tilt == 0 (no tilt energy density)",
}

FORWARD_STATEMENT = (
    "for every comparator state satisfying ALL comparator premises, "
    "x_C = sigma2 - w2 + omega_tilt + delta_omega_k = 0 exactly; this is "
    "ONE-WAY — x_C = 0 does not imply the premises (see the sealed "
    "counterexample registry)"
)


def theorem_id(premise_ids: Sequence[str], statement: str) -> str:
    """Content-addressed theorem id over the premise SET and statement."""
    canonical = json.dumps(
        {"premises": sorted(set(premise_ids)), "statement": statement},
        sort_keys=True,
    ).encode()
    return "THM-" + hashlib.sha256(canonical).hexdigest()[:16]


FORWARD_THEOREM_ID = theorem_id(
    tuple(COMPARATOR_FORWARD_PREMISES), FORWARD_STATEMENT
)


def validate_theorem_claim(claim: Mapping) -> None:
    """A claim must cite the CURRENT content-addressed id for its premise
    set (post-hoc premise edits mint a new id), and must never merge the
    exact theorem with the SPECIFIED_ONLY almost-EGS node."""
    premise_ids = claim.get("premise_ids")
    statement = str(claim.get("statement") or "")
    claimed_id = str(claim.get("theorem_id") or "")
    if not isinstance(premise_ids, (list, tuple)) or not premise_ids:
        raise EgsOnewayError("a theorem claim must list its premise ids")
    expected = theorem_id(tuple(str(p) for p in premise_ids), statement)
    if claimed_id != expected:
        raise EgsOnewayError(
            f"theorem id {claimed_id!r} does not match the content-addressed "
            f"id {expected!r} for this premise set/statement — premise edits "
            "mint a NEW theorem id"
        )
    cited = set(str(p) for p in premise_ids)
    known_groups = {
        "comparator": set(COMPARATOR_FORWARD_PREMISES),
        "exact_egs": set(EXACT_EGS_PREMISES),
        "almost_egs": set(ALMOST_EGS_PREMISES),
    }
    vocabulary = set().union(*known_groups.values())
    unknown = cited - vocabulary
    if unknown:
        raise EgsOnewayError(
            f"claim cites unregistered premise ids {sorted(unknown)} — "
            "renamed premises do not bypass the governance vocabulary"
        )
    touched = [name for name, group in known_groups.items() if cited & group]
    if len(touched) > 1:
        raise EgsOnewayError(
            "a claim must cite premises from exactly one registered group "
            f"(cited groups: {touched}); exact, almost-EGS "
            f"({ALMOST_EGS_STATUS}), and comparator premise sets never merge"
        )


# ---------------------------------------------------------------------------
# comparator states and the sealed one-way pair
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComparatorState:
    """Exact comparator state: the graded components plus the tilt beta.

    The components are INDEPENDENT inputs at the comparator level; the tilt
    MAP beta -> omega_tilt is deliberately not asserted here.
    """

    beta: Fraction
    sigma2: Fraction
    w2: Fraction
    omega_tilt: Fraction
    delta_omega_k: Fraction

    def __post_init__(self) -> None:
        for name in ("beta", "sigma2", "w2", "omega_tilt", "delta_omega_k"):
            object.__setattr__(self, name, Fraction(getattr(self, name)))
        if not (-1 < self.beta < 1):
            raise EgsOnewayError("beta out of the open unit interval")
        for name in ("sigma2", "w2", "omega_tilt"):
            if getattr(self, name) < 0:
                raise EgsOnewayError(f"{name} must be nonnegative")

    def x_c(self) -> Fraction:
        """The master comparator combination c = (1, -1, 1, 1)."""
        return self.sigma2 - self.w2 + self.omega_tilt + self.delta_omega_k

    def kinematic_projection(self) -> KinematicState:
        return KinematicState(beta=self.beta, sigma2=self.sigma2,
                              w2=self.w2, delta_omega_k=self.delta_omega_k)

    def satisfies_forward_premises(self) -> bool:
        """ALL comparator premises (PR-125 flrw_limit plus omega_tilt = 0)."""
        return flrw_limit(self.kinematic_projection()) and self.omega_tilt == 0


# Verified refutation witnesses per droppable premise: each witness
# satisfies every premise EXCEPT the dropped one and has x_C != 0. Dropping
# CMP-P1 (beta_zero) admits NO such witness — beta does not enter x_C — so
# that case is refused fail-closed WITHOUT a refutation claim.
_DROPPED_PREMISE_WITNESSES = {
    "CMP-P2-sigma2_zero": dict(beta=0, sigma2=Fraction(1, 10**6), w2=0,
                               omega_tilt=0, delta_omega_k=0),
    "CMP-P3-w2_zero": dict(beta=0, sigma2=0, w2=Fraction(1, 10**6),
                           omega_tilt=0, delta_omega_k=0),
    "CMP-P4-delta_omega_k_zero": dict(beta=0, sigma2=0, w2=0, omega_tilt=0,
                                      delta_omega_k=Fraction(1, 10**6)),
    "CMP-P5-omega_tilt_zero": dict(beta=0, sigma2=0, w2=0,
                                   omega_tilt=Fraction(1, 10**6),
                                   delta_omega_k=0),
}

_PREMISE_FIELD = {
    "CMP-P1-beta_zero": "beta",
    "CMP-P2-sigma2_zero": "sigma2",
    "CMP-P3-w2_zero": "w2",
    "CMP-P4-delta_omega_k_zero": "delta_omega_k",
    "CMP-P5-omega_tilt_zero": "omega_tilt",
}


def _verified_refutation_witness(missing: set[str]) -> ComparatorState | None:
    """Return a MACHINE-VERIFIED witness refuting the reduced statement, or
    None when no witness exists for the dropped set."""
    for dropped in sorted(missing):
        payload = _DROPPED_PREMISE_WITNESSES.get(dropped)
        if payload is None:
            continue
        witness = ComparatorState(**payload)
        satisfied = all(
            getattr(witness, _PREMISE_FIELD[premise]) == 0
            for premise in COMPARATOR_FORWARD_PREMISES
            if premise not in missing
        )
        if satisfied and witness.x_c() != 0:
            return witness
    return None


def check_forward(states: Sequence[ComparatorState],
                  premise_ids: Sequence[str] = tuple(
                      COMPARATOR_FORWARD_PREMISES)) -> dict:
    """The forward checker: over the FULL premise set every premise-complete
    state must have x_C = 0. Called with a REDUCED premise set it refuses
    fail-closed — with a MACHINE-VERIFIED refuting witness where one
    exists, and WITHOUT any refutation claim where the reduced statement
    happens to remain true (dropping beta_zero): the registered theorem id
    binds the FULL premise set either way."""
    missing = set(COMPARATOR_FORWARD_PREMISES) - set(premise_ids)
    if missing:
        witness = _verified_refutation_witness(missing)
        if witness is not None:
            raise EgsOnewayError(
                f"forward claim under an incomplete premise set (missing "
                f"{sorted(missing)}) is refuted: verified witness with "
                f"x_C = {witness.x_c()} != 0 satisfies the reduced premises"
            )
        raise EgsOnewayError(
            f"forward claim under an incomplete premise set (missing "
            f"{sorted(missing)}) is refused fail-closed; no refutation "
            "witness exists for this reduction (the reduced statement may "
            "hold) but the registered theorem id binds the FULL premise "
            "set — premise edits mint a new id"
        )
    if not states:
        raise EgsOnewayError(
            "the forward check is not vacuous: at least one premise-"
            "complete state is required"
        )
    checked = 0
    for state in states:
        if not state.satisfies_forward_premises():
            raise EgsOnewayError(
                "a state violating the comparator premises was passed to "
                "the forward checker"
            )
        if state.x_c() != 0:
            raise EgsOnewayError(
                f"KILL SWITCH: premise-complete FLRW state with x_C = "
                f"{state.x_c()} != 0 — the one-way statement is refuted"
            )
        checked += 1
    return {"theorem_id": FORWARD_THEOREM_ID, "states_checked": checked}


def validate_counterexample(state: ComparatorState) -> dict:
    """A registered converse counterexample must have x_C = 0 AND fail the
    FLRW limit (nonzero departures) — the cancellation is the point."""
    if state.x_c() != 0:
        raise EgsOnewayError(
            f"counterexample must cancel exactly (x_C = {state.x_c()})"
        )
    if state.satisfies_forward_premises():
        raise EgsOnewayError(
            "counterexample is actually FLRW — it witnesses nothing"
        )
    return {
        "x_c": "0",
        "flrw_limit": False,
        "nonzero_components": sorted(
            name for name in ("beta", "sigma2", "w2", "omega_tilt",
                              "delta_omega_k")
            if getattr(state, name) != 0
        ),
    }


def seeded_cancellation_states(seeds: int) -> list[ComparatorState]:
    """Deterministic seeded cancellation family: x_C = 0 by construction,
    generically non-FLRW. No wall-clock, no global RNG — a fixed integer
    recurrence generates the rationals."""
    states = []
    value = 987654321
    for index in range(seeds):
        value = (1103515245 * value + 12345) % (2**31)
        a = Fraction(value % 997 + 1, 10**9)
        value = (1103515245 * value + 12345) % (2**31)
        b = Fraction(value % 991 + 1, 10**9)
        value = (1103515245 * value + 12345) % (2**31)
        c = Fraction(value % 983 + 1, 10**9)
        # delta_omega_k chosen so x_C = 0 exactly
        states.append(ComparatorState(
            beta=0, sigma2=a, w2=b, omega_tilt=c,
            delta_omega_k=b - a - c,
        ))
    return states


# ---------------------------------------------------------------------------
# safe generated theorem text
# ---------------------------------------------------------------------------

_FORBIDDEN_TEXT = (
    "x_C = 0 therefore FLRW", "FLRW certificate", "EGS certificate",
    "converse established", "isotropy proven", "implies FLRW",
    "implies the FLRW", "implies EGS", "implies the EGS", "certifies",
    "hence the FLRW", "hence FLRW", "establishes isotropy",
    "establishes the FLRW", "Bianchi geometry detected",
    "Bianchi family identified", "finding rescued", "validated as native",
)


def safe_theorem_text() -> str:
    text = (
        f"[{FORWARD_THEOREM_ID}] Under the comparator premises "
        f"{sorted(COMPARATOR_FORWARD_PREMISES)}, x_C = 0 exactly. "
        "This statement is ONE-WAY: the sealed counterexample registry "
        "exhibits x_C = 0 states with nonzero departures, so x_C = 0 "
        "never establishes the premises. The almost-EGS premise set is "
        f"{ALMOST_EGS_STATUS} and supports no claim here."
    )
    lint_theorem_text(text)
    return text


def lint_theorem_text(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_TEXT:
        if phrase.lower() in lowered:
            raise EgsOnewayError(
                f"generated theorem text contains forbidden converse/"
                f"certificate language: {phrase!r}"
            )
