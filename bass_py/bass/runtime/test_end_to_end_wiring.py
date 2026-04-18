"""
Test suite: end-to-end wiring (Week 3 Day 2, merged v4.1)
==========================================================

Verifies that `make_canonical_decision` composes cleanly with the concrete
D2 gate functions (`beta_policy_gate`, `sigma_min_gate`) and the existing
D1 `source_Dge2_gate`. Covers the happy path and each single-failure branch
at the integration layer.

These tests are small in count (4) but sit at the top of the W3 stack and
catch interface drift that unit tests on individual gates would miss.
"""
from __future__ import annotations

import numpy as np
import pytest

from tsc.diagnostics.tangency import TangencyResult, TangentKind
from bass.tilt.baryon_only_policy import beta_policy_gate
from bass.runtime.sigma_floor import sigma_min_gate
from bass.runtime.canonical_decision import (
    make_canonical_decision,
    require_allow_reduction,
    CanonicalBlockError,
)
from bass.runtime.validation_labels import ValidationLabel


def _on_manifold_tangency() -> TangencyResult:
    """Construct a TangencyResult with is_tangent=True and fraction~1."""
    return TangencyResult(
        coefficients=np.zeros(3),
        tangent_norm_sq=1.0, total_norm_sq=1.0,
        D_sq=0.0, D=1e-9, relative_residual=1e-9,
        kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
        gram_matrix=np.eye(3), moment_vector=np.zeros(3),
    )


def _off_manifold_tangency() -> TangencyResult:
    """is_tangent=False, fraction=0.5."""
    return TangencyResult(
        coefficients=np.zeros(3),
        tangent_norm_sq=0.5, total_norm_sq=1.0,
        D_sq=0.5, D=np.sqrt(0.5), relative_residual=0.5,
        kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
        gram_matrix=np.eye(3), moment_vector=np.zeros(3),
    )


# ============================================================================
# Test Class 1 - Full-pass happy path
# ============================================================================

class TestHappyPath:
    """All three gates pass with realistic production inputs."""

    def test_VER06_production_inputs_allow_reduction(self):
        # β = 1.36e-3 (VER06), ε_1 = 0.02, η_{u̇} = 0.16 → beta gate passes
        # Σ² ~ 1e-5 well above 1e-6 floor → sigma gate passes
        # On-manifold tangency → source gate passes
        decision = make_canonical_decision(
            beta_result=beta_policy_gate(1.36e-3, 0.02, 0.16),
            sigma_result=sigma_min_gate(
                np.array([1e-5, 2e-5, 5e-5, 8e-5])
            ),
            tangency_result=_on_manifold_tangency(),
        )
        assert decision.allow_reduction is True
        assert (
            ValidationLabel.TRACE_SOURCE_ADEQUATE in decision.emitted_labels
        )
        # No block-ish labels should appear
        assert ValidationLabel.BETA_POLICY_BLOCK not in decision.emitted_labels
        assert (
            ValidationLabel.SIGMA_MIN_BELOW_FLOOR
            not in decision.emitted_labels
        )

    def test_require_allow_reduction_no_raise_on_happy(self):
        decision = make_canonical_decision(
            beta_result=beta_policy_gate(1.36e-3, 0.02, 0.16),
            sigma_result=sigma_min_gate(1e-5),
            tangency_result=_on_manifold_tangency(),
        )
        # Should not raise
        require_allow_reduction(decision, context="end_to_end_happy")


# ============================================================================
# Test Class 2 - Single-gate failure scenarios
# ============================================================================

class TestSingleFailureScenarios:
    """Each gate can fail independently; labels localize the offender."""

    def test_beta_fail_only(self):
        # Push ε_1 small enough that β=1.36e-3 violates the VT-07 gate
        decision = make_canonical_decision(
            beta_result=beta_policy_gate(1.36e-3, 1e-3, 0.16),
            sigma_result=sigma_min_gate(1e-5),
            tangency_result=_on_manifold_tangency(),
        )
        assert decision.allow_reduction is False
        assert (
            ValidationLabel.BETA_POLICY_BLOCK in decision.emitted_labels
        )
        # The other two gates pass
        assert decision.sigma_min_above_floor is True
        assert decision.source_Dge2_gate_pass is True
        # Beta diagnostic preserved through the factory
        assert decision.diagnostics["beta"]["fractional_slack"] < 0

    def test_sigma_fail_only(self):
        decision = make_canonical_decision(
            beta_result=beta_policy_gate(1.36e-3, 0.02, 0.16),
            sigma_result=sigma_min_gate(
                np.array([1e-5, 1e-9, 1e-5])  # idx 1 violates
            ),
            tangency_result=_on_manifold_tangency(),
        )
        assert decision.allow_reduction is False
        assert (
            ValidationLabel.SIGMA_MIN_BELOW_FLOOR
            in decision.emitted_labels
        )
        # argmin propagated
        assert decision.diagnostics["sigma"]["argmin_index"] == 1
        # Source still passing with fraction 1.0 → mixed-channel flag fires
        assert (
            ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING
            in decision.emitted_labels
        )

    def test_source_fail_only_emits_upgrade_candidate(self):
        decision = make_canonical_decision(
            beta_result=beta_policy_gate(1.36e-3, 0.02, 0.16),
            sigma_result=sigma_min_gate(1e-5),
            tangency_result=_off_manifold_tangency(),
        )
        assert decision.allow_reduction is False
        assert (
            ValidationLabel.TRACE_SOURCE_INADEQUATE
            in decision.emitted_labels
        )
        assert (
            ValidationLabel.UPGRADE_TO_TWOFIELD_CANDIDATE
            in decision.emitted_labels
        )
        # Source failed with fraction 0.5 (< 0.99) → no mixed-channel flag
        assert (
            ValidationLabel.MIXED_CHANNEL_PROPAGATION_PENDING
            not in decision.emitted_labels
        )


# ============================================================================
# Test Class 3 - Consumer-raise contract
# ============================================================================

class TestConsumerRaise:
    """require_allow_reduction interaction at the integration layer."""

    def test_raises_carrying_full_decision_on_mixed_failure(self):
        decision = make_canonical_decision(
            beta_result=beta_policy_gate(1.36e-3, 1e-3, 0.16),  # fails
            sigma_result=sigma_min_gate(
                np.array([1e-5, 1e-10, 1e-5])  # fails
            ),
            tangency_result=_on_manifold_tangency(),
        )
        with pytest.raises(CanonicalBlockError) as excinfo:
            require_allow_reduction(decision, "integration_test")
        err_decision = excinfo.value.decision
        # Both fails surfaced in labels
        assert (
            ValidationLabel.BETA_POLICY_BLOCK in err_decision.emitted_labels
        )
        assert (
            ValidationLabel.SIGMA_MIN_BELOW_FLOOR
            in err_decision.emitted_labels
        )
        # Diagnostics preserved through the exception
        assert err_decision.diagnostics["sigma"]["argmin_index"] == 1
