"""
Test suite: validation_labels.py (Week 3 Day 1, merged v4.1)
=============================================================

Exercises the 8-label enum + deterministic emission rules from design spec §4.

  1. TestLabelEnum             (enum identity, string values, stability)
  2. TestAllPassEmission       (positive verdicts, D-band branches)
  3. TestSourceFailEmission    (UPGRADE_TO_TWOFIELD_CANDIDATE logic)
  4. TestPolicyFailEmission    (beta / sigma blocks, combos)
  5. TestMixedChannelEmission  (fraction_on_manifold > 0.99 rule)
  6. TestDeterminism           (no hidden state, idempotent, frozenset)
  7. TestPredicates            (labels_indicate_block / _upgrade_path)

Target: 15 tests.
"""
from __future__ import annotations

import pytest

from bass.runtime.validation_labels import (
    ValidationLabel,
    ALL_LABELS,
    SPIN2_RISK_BAND_LOW,
    SPIN2_RISK_BAND_HIGH,
    MIXED_CHANNEL_FRACTION_FLOOR,
    derive_labels,
    labels_indicate_block,
    labels_indicate_upgrade_path,
)


# Canonical diagnostic shape used throughout (source values controlled per test)
def _diag(rel_res: float = 0.0, fraction: float = 1.0) -> dict:
    return {
        "source": {
            "relative_residual": rel_res,
            "fraction_on_manifold": fraction,
        },
        "beta": {},
        "sigma": {},
    }


# ============================================================================
# Test Class 1 - Label enum identity
# ============================================================================

class TestLabelEnum:
    """Enum stability: exactly 8 members with pinned string values."""

    def test_enum_has_exactly_8_members(self):
        assert len(list(ValidationLabel)) == 8

    def test_enum_values_are_pinned(self):
        # These strings are the serialized contract; changing them is a spec
        # version bump. Each enum member keeps its stable string.
        expected = {
            ValidationLabel.TRACE_SOURCE_ADEQUATE: "trace_source_adequate",
            ValidationLabel.TRACE_SOURCE_INADEQUATE: "trace_source_inadequate",
            ValidationLabel.UPGRADE_TO_TWOFIELD_CANDIDATE: "upgrade_to_twofield_candidate",
            ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK: "resolved_spin2_invisibility_risk",
            ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING: "mixed_channel_propagation_pending",
            ValidationLabel.BETA_POLICY_BLOCK: "beta_policy_block",
            ValidationLabel.SOURCE_DGE2_GATE: "source_Dge2_gate",
            ValidationLabel.SIGMA_MIN_BELOW_FLOOR: "sigma_min_below_floor",
        }
        for label, expected_value in expected.items():
            assert label.value == expected_value

    def test_ALL_LABELS_is_frozen(self):
        assert isinstance(ALL_LABELS, frozenset)
        assert len(ALL_LABELS) == 8


# ============================================================================
# Test Class 2 - All-pass emission
# ============================================================================

class TestAllPassEmission:
    """Positive verdicts when all three gates pass."""

    def test_all_pass_emits_TRACE_SOURCE_ADEQUATE(self):
        labels = derive_labels(
            beta_policy_pass=True,
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(rel_res=1e-10, fraction=1.0),
        )
        assert ValidationLabel.TRACE_SOURCE_ADEQUATE in labels
        assert ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK not in labels

    def test_all_pass_with_borderline_rel_res_emits_risk(self):
        # Band: [1e-7, 1e-6) -> flag fires
        labels = derive_labels(
            beta_policy_pass=True,
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(rel_res=5e-7, fraction=1.0),
        )
        assert ValidationLabel.TRACE_SOURCE_ADEQUATE in labels
        assert ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK in labels

    def test_band_edges_are_half_open(self):
        # Lower edge (inclusive) fires
        at_low = derive_labels(
            True, True, True,
            _diag(rel_res=SPIN2_RISK_BAND_LOW, fraction=1.0),
        )
        assert ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK in at_low

        # Just below lower edge: does not fire
        below = derive_labels(
            True, True, True,
            _diag(rel_res=SPIN2_RISK_BAND_LOW * 0.9, fraction=1.0),
        )
        assert ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK not in below

        # Upper edge (exclusive): the gate fails there since 1e-6 is the
        # is_tangent threshold. derive_labels is called with source_pass=True
        # for this unit test purpose; we only check the band logic in isolation.
        # At exactly the upper edge, source_pass would be False in reality.
        # To check the band edge in isolation, use source_pass=True with
        # rel_res = SPIN2_RISK_BAND_HIGH - eps.
        near_upper = derive_labels(
            True, True, True,
            _diag(
                rel_res=SPIN2_RISK_BAND_HIGH * (1 - 1e-9),
                fraction=1.0,
            ),
        )
        assert ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK in near_upper


# ============================================================================
# Test Class 3 - Source-side failure emission
# ============================================================================

class TestSourceFailEmission:
    """UPGRADE_TO_TWOFIELD_CANDIDATE and SOURCE_DGE2_GATE logic."""

    def test_source_fail_only_emits_upgrade_candidate(self):
        # source fails while other two pass -> upgrade candidate fires
        labels = derive_labels(
            beta_policy_pass=True,
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=False,
            diagnostics=_diag(rel_res=1e-4, fraction=0.5),
        )
        assert ValidationLabel.TRACE_SOURCE_INADEQUATE in labels
        assert ValidationLabel.SOURCE_DGE2_GATE in labels
        assert ValidationLabel.UPGRADE_TO_TWOFIELD_CANDIDATE in labels
        # Positive verdicts must NOT appear when source fails
        assert ValidationLabel.TRACE_SOURCE_ADEQUATE not in labels

    def test_source_fail_with_beta_fail_no_upgrade_candidate(self):
        # When multiple gates fail, upgrade candidate should NOT fire
        # (it means "source is the sole failure; upgrade may rescue")
        labels = derive_labels(
            beta_policy_pass=False,
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=False,
            diagnostics=_diag(rel_res=1e-4, fraction=0.5),
        )
        assert ValidationLabel.TRACE_SOURCE_INADEQUATE in labels
        assert ValidationLabel.SOURCE_DGE2_GATE in labels
        assert ValidationLabel.BETA_POLICY_BLOCK in labels
        assert ValidationLabel.UPGRADE_TO_TWOFIELD_CANDIDATE not in labels


# ============================================================================
# Test Class 4 - Policy failure emissions (beta / sigma)
# ============================================================================

class TestPolicyFailEmission:
    """BETA_POLICY_BLOCK and SIGMA_MIN_BELOW_FLOOR are independent."""

    def test_beta_fail_emits_block(self):
        labels = derive_labels(
            beta_policy_pass=False,
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(rel_res=1e-8, fraction=1.0),
        )
        assert ValidationLabel.BETA_POLICY_BLOCK in labels
        assert ValidationLabel.SIGMA_MIN_BELOW_FLOOR not in labels

    def test_sigma_fail_emits_floor(self):
        labels = derive_labels(
            beta_policy_pass=True,
            sigma_min_above_floor=False,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(rel_res=1e-8, fraction=1.0),
        )
        assert ValidationLabel.SIGMA_MIN_BELOW_FLOOR in labels
        assert ValidationLabel.BETA_POLICY_BLOCK not in labels

    def test_both_policies_fail_both_flags(self):
        labels = derive_labels(
            beta_policy_pass=False,
            sigma_min_above_floor=False,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(rel_res=1e-8, fraction=1.0),
        )
        assert ValidationLabel.BETA_POLICY_BLOCK in labels
        assert ValidationLabel.SIGMA_MIN_BELOW_FLOOR in labels


# ============================================================================
# Test Class 5 - Mixed-channel emission
# ============================================================================

class TestMixedChannelEmission:
    """MIXED_CHANNEL_PROPAGATION_PENDING on high tangency fraction despite fail."""

    def test_fires_when_any_fail_and_fraction_high(self):
        labels = derive_labels(
            beta_policy_pass=False,   # something fails
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(rel_res=1e-8, fraction=0.995),   # > 0.99
        )
        assert ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING in labels

    def test_does_not_fire_when_all_pass(self):
        labels = derive_labels(
            True, True, True,
            _diag(rel_res=1e-10, fraction=1.0),
        )
        assert ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING not in labels

    def test_does_not_fire_when_fraction_below_floor(self):
        labels = derive_labels(
            beta_policy_pass=False,
            sigma_min_above_floor=True,
            source_Dge2_gate_pass=True,
            diagnostics=_diag(
                rel_res=1e-8, fraction=MIXED_CHANNEL_FRACTION_FLOOR - 1e-3,
            ),
        )
        assert ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING not in labels


# ============================================================================
# Test Class 6 - Determinism and frozenset return
# ============================================================================

class TestDeterminism:
    """Pure-function contract: no hidden state, always frozenset."""

    def test_returns_frozenset(self):
        result = derive_labels(True, True, True, _diag(1e-10, 1.0))
        assert isinstance(result, frozenset)

    def test_idempotent_across_calls(self):
        args = (True, False, True, _diag(rel_res=1e-8, fraction=0.995))
        a = derive_labels(*args)
        b = derive_labels(*args)
        assert a == b
        # Calling again with same inputs must produce equal sets (no mutation)
        args2 = (False, True, False, _diag(rel_res=1e-4, fraction=0.5))
        c = derive_labels(*args2)
        d = derive_labels(*args)  # back to original inputs
        assert d == a   # state has not drifted
        # c is different (different inputs)
        assert c != a

    def test_empty_diagnostics_defaults_to_zero(self):
        # Missing 'source' key -> defaults rel_res=0, fraction=0
        labels = derive_labels(True, True, True, {})
        # With fraction=0 and all passing, no mixed-channel nor risk flag
        assert ValidationLabel.TRACE_SOURCE_ADEQUATE in labels
        assert ValidationLabel.RESOLVED_SPIN2_INVISIBILITY_RISK not in labels
        assert ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING not in labels


# ============================================================================
# Test Class 7 - Convenience predicates
# ============================================================================

class TestPredicates:
    """labels_indicate_block + labels_indicate_upgrade_path."""

    def test_block_predicate_true_on_beta_fail(self):
        labels = derive_labels(
            False, True, True, _diag(rel_res=1e-8, fraction=1.0),
        )
        assert labels_indicate_block(labels) is True

    def test_block_predicate_false_on_all_pass(self):
        labels = derive_labels(
            True, True, True, _diag(rel_res=1e-10, fraction=1.0),
        )
        assert labels_indicate_block(labels) is False

    def test_upgrade_predicate_true_on_sole_source_fail(self):
        labels = derive_labels(
            True, True, False, _diag(rel_res=1e-4, fraction=0.5),
        )
        assert labels_indicate_upgrade_path(labels) is True
        # But if additional gates also fail, no upgrade signal
        labels2 = derive_labels(
            False, True, False, _diag(rel_res=1e-4, fraction=0.5),
        )
        assert labels_indicate_upgrade_path(labels2) is False
