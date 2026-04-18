"""
bass/runtime/validation_labels.py  (Week 3 Day 1, merged v4.1)
==============================================================

Eight validation labels emitted by `bass/runtime/canonical_decision.py` and
consumed by TSC / MIO / HTT / figure generators.

Ownership rules (per CANONICAL_DECISION_DESIGN.md §4.3):
  - `ValidationLabel` values are emitted only from `bass/runtime/` (outside of
    tests). TSC, MIO, HTT may read but must not instantiate labels.
  - The `UPGRADE_TO_TWOFIELD_CANDIDATE` label is emitted here; its chart-level
    meaning (what upgrade action is taken) is owned by TSC.
  - The `MIXED_CHANNEL_PROPAGATION_PENDING` label's observatory-facing
    interpretation is owned by MIO (W6+).

No runtime allow/block decision is made in this module. The labels are
diagnostic breadcrumbs; the authoritative verdict lives in
`CanonicalDecision.allow_reduction`.

Paper I / execution plan cross-references:
  - execution plan v3 §6 D3 (label enumeration and ownership)
  - execution plan v3 §7 A3 ("source adequate, propagation pending" combo)
  - Paper I Thm 6 (tangency diagnostic feeding SOURCE_DGE2_GATE)
"""
from __future__ import annotations

from enum import Enum
from typing import FrozenSet, Mapping, Any


# ============================================================================
# Section 1 - Label enumeration
# ============================================================================

class ValidationLabel(Enum):
    """Eight labels from execution plan v3 §6 D3.

    Values are stable strings; changing a value is a SPEC_VERSION bump.
    """
    # On-manifold / source adequacy (positive verdicts)
    TRACE_SOURCE_ADEQUATE = "trace_source_adequate"
    RESOLVED_SPIN2_INVISIBILITY_RISK = "resolved_spin2_invisibility_risk"

    # Source-side problems (source fails but other gates may still inform)
    TRACE_SOURCE_INADEQUATE = "trace_source_inadequate"
    UPGRADE_TO_TWOFIELD_CANDIDATE = "upgrade_to_twofield_candidate"
    SOURCE_DGE2_GATE = "source_Dge2_gate"

    # Policy / admissibility blocks
    BETA_POLICY_BLOCK = "beta_policy_block"
    SIGMA_MIN_BELOW_FLOOR = "sigma_min_below_floor"

    # Propagation status (may coexist with other labels)
    MIXED_CHANNEL_PROPAGATION_PENDING = "mixed_channel_propagation_pending"


# Frozen set of all known labels for test/introspection use
ALL_LABELS: FrozenSet[ValidationLabel] = frozenset(ValidationLabel)


# ============================================================================
# Section 2 - Diagnostic-band thresholds
# ============================================================================
#
# Band edges for RESOLVED_SPIN2_INVISIBILITY_RISK (design spec §4.2 table row 2).
# On D/||G|| ∈ [SPIN2_RISK_BAND_LOW, SPIN2_RISK_BAND_HIGH) the gate still passes
# (source is nominally on-manifold) but the residual is large enough to warrant
# the "resolved but visible" flag.

SPIN2_RISK_BAND_LOW: float = 1e-7
SPIN2_RISK_BAND_HIGH: float = 1e-6

# Mixed-channel threshold: if any gate fails but the tangency fraction is still
# above this value, the system is near-on-manifold and the MIXED_CHANNEL
# flag is informative for downstream (MIO) routing.
MIXED_CHANNEL_FRACTION_FLOOR: float = 0.99


# ============================================================================
# Section 3 - Deterministic emission rules
# ============================================================================

def derive_labels(
    beta_policy_pass: bool,
    sigma_min_above_floor: bool,
    source_Dge2_gate_pass: bool,
    diagnostics: Mapping[str, Mapping[str, Any]],
) -> FrozenSet[ValidationLabel]:
    """Map three gate bools + side-channel diagnostics to a label set.

    Parameters
    ----------
    beta_policy_pass : bool
        VT-07 safe-route outcome.
    sigma_min_above_floor : bool
        Sobolev validity floor check.
    source_Dge2_gate_pass : bool
        Tangency diagnostic wrapper outcome.
    diagnostics : mapping
        Expected keys (any may be absent; defaults are used in that case):

        - `'source'`: mapping with optional keys
            * `'relative_residual'` (float)   — D/||G|| from tangency
            * `'fraction_on_manifold'` (float) — tangent_norm_sq / total_norm_sq
        - `'beta'`, `'sigma'`: present for logging only; not used in emission.

    Returns
    -------
    frozenset[ValidationLabel]
        Labels emitted per design spec §4.2. The return is always a frozenset
        (hashable, immutable, equal across identical input states).

    Notes
    -----
    The rules are deterministic and depend only on the four arguments. No
    hidden state, no module-level mutable cache. This is asserted indirectly
    by `test_emission_idempotent` in the test suite.
    """
    labels: set[ValidationLabel] = set()

    source_diag = diagnostics.get("source", {}) if diagnostics else {}
    rel_res = float(source_diag.get("relative_residual", 0.0))
    fraction = float(source_diag.get("fraction_on_manifold", 0.0))

    all_pass = (
        beta_policy_pass and sigma_min_above_floor and source_Dge2_gate_pass
    )

    # Positive verdicts (only when all three gates pass)
    if all_pass:
        labels.add(ValidationLabel.TRACE_SOURCE_ADEQUATE)
        if SPIN2_RISK_BAND_LOW <= rel_res < SPIN2_RISK_BAND_HIGH:
            labels.add(ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK)

    # Source-side failure: always paired with the bundle below
    if not source_Dge2_gate_pass:
        labels.add(ValidationLabel.TRACE_SOURCE_INADEQUATE)
        labels.add(ValidationLabel.SOURCE_DGE2_GATE)
        # Upgrade candidate flagged only when the source is the *sole* failure
        if beta_policy_pass and sigma_min_above_floor:
            labels.add(ValidationLabel.UPGRADE_TO_TWOFIELD_CANDIDATE)

    # Policy / admissibility failures: independent flags
    if not beta_policy_pass:
        labels.add(ValidationLabel.BETA_POLICY_BLOCK)
    if not sigma_min_above_floor:
        labels.add(ValidationLabel.SIGMA_MIN_BELOW_FLOOR)

    # Mixed-channel: any gate fails but tangency fraction is near-unity
    if not all_pass and fraction > MIXED_CHANNEL_FRACTION_FLOOR:
        labels.add(ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING)

    return frozenset(labels)


# ============================================================================
# Section 4 - Convenience predicates (for consumer code)
# ============================================================================

def labels_indicate_block(labels: FrozenSet[ValidationLabel]) -> bool:
    """True iff the label set implies any blocking verdict.

    A pure convenience for consumers that only look at labels. Blocking
    labels are `BETA_POLICY_BLOCK`, `SIGMA_MIN_BELOW_FLOOR`, and
    `TRACE_SOURCE_INADEQUATE`. The authoritative check remains
    `CanonicalDecision.allow_reduction`; this predicate must never
    contradict it.
    """
    blocking = {
        ValidationLabel.BETA_POLICY_BLOCK,
        ValidationLabel.SIGMA_MIN_BELOW_FLOOR,
        ValidationLabel.TRACE_SOURCE_INADEQUATE,
    }
    return any(lab in labels for lab in blocking)


def labels_indicate_upgrade_path(labels: FrozenSet[ValidationLabel]) -> bool:
    """True iff TSC should consider a chart upgrade (e.g., one → two-field).

    Driven by `UPGRADE_TO_TWOFIELD_CANDIDATE`. TSC owns the upgrade semantics;
    this predicate is a pure read.
    """
    return ValidationLabel.UPGRADE_TO_TWOFIELD_CANDIDATE in labels
