"""
Test suite: canonical_decision.py (Week 3 Day 1, merged v4.1)
==============================================================

Exercises the design spec §6.1 — 18 structural tests covering:
  1. TestFrozenContract     (immutability, spec_version pin)
  2. TestAllowReductionAND  (all 8 truth-table rows)
  3. TestSourceDge2Gate     (TangencyResult wrapper)
  4. TestFactoryPath        (make_canonical_decision shape / types)
  5. TestConsumerAPI        (require_allow_reduction + CanonicalBlockError)
  6. TestDiagnosticsFlow    (diagnostics dict shape / readonly contract)

Target: 18 tests.
"""
from __future__ import annotations

import numpy as np
import pytest

from tsc.diagnostics.tangency import TangencyResult, TangentKind
from bass.runtime.canonical_decision import (
    SPEC_VERSION,
    CanonicalDecision,
    CanonicalBlockError,
    make_canonical_decision,
    source_Dge2_gate,
    require_allow_reduction,
)
from bass.runtime.validation_labels import ValidationLabel, derive_labels


# ============================================================================
# Helpers — construct TangencyResult at a prescribed rel_res
# ============================================================================

def _make_tangency(rel_res: float, fraction: float = 1.0) -> TangencyResult:
    """Forge a TangencyResult with the chosen relative_residual and fraction.

    We bypass `compute_D_diagnostic` because the tests probe the *wrapper*,
    not the diagnostic itself. Physical realizability is not required.
    """
    total = 1.0
    tangent = fraction * total
    D_sq = total - tangent
    D = float(np.sqrt(max(D_sq, 0.0)))
    return TangencyResult(
        coefficients=np.zeros(3),
        tangent_norm_sq=tangent,
        total_norm_sq=total,
        D_sq=D_sq,
        D=D,
        relative_residual=rel_res,
        kind=TangentKind.ONE_FIELD,
        xi=0,
        eta=0.0,
        gram_matrix=np.eye(3),
        moment_vector=np.zeros(3),
    )


def _pass_tangency() -> TangencyResult:
    """Tangency with rel_res well below 1e-6 → is_tangent True."""
    return _make_tangency(rel_res=1e-8, fraction=1.0 - 1e-16)


def _fail_tangency() -> TangencyResult:
    """Tangency with rel_res above 1e-6 → is_tangent False, fraction=0.5."""
    return _make_tangency(rel_res=5e-1, fraction=0.5)


# ============================================================================
# Test Class 1 - Frozen contract and spec_version
# ============================================================================

class TestFrozenContract:
    """Immutability + spec version pin enforcement."""

    def test_dataclass_is_frozen(self):
        dec = make_canonical_decision(
            (True, {}), (True, {}), _pass_tangency(),
        )
        with pytest.raises((AttributeError, Exception)):
            dec.allow_reduction = False  # frozen dataclass -> FrozenInstanceError

    def test_spec_version_literal(self):
        # The pin string must be exactly this for interface stability
        assert SPEC_VERSION == "v1.0-w3d1"

    def test_spec_version_mismatch_raises(self):
        with pytest.raises(ValueError, match="spec_version"):
            CanonicalDecision(
                spec_version="wrong-version",
                beta_policy_pass=True,
                sigma_min_above_floor=True,
                source_Dge2_gate_pass=True,
                allow_reduction=True,
                emitted_labels=frozenset({
                    ValidationLabel.TRACE_SOURCE_ADEQUATE
                }),
            )

    def test_allow_reduction_consistency_enforced(self):
        # allow_reduction must equal AND of three bools; mis-claim raises
        with pytest.raises(ValueError, match="allow_reduction"):
            CanonicalDecision(
                spec_version=SPEC_VERSION,
                beta_policy_pass=True,
                sigma_min_above_floor=True,
                source_Dge2_gate_pass=False,
                allow_reduction=True,        # lie
                emitted_labels=frozenset(),
            )


# ============================================================================
# Test Class 2 - allow_reduction AND truth table
# ============================================================================

class TestAllowReductionAND:
    """Full 8-row truth table for (beta, sigma, source) -> allow_reduction."""

    @pytest.mark.parametrize(
        "beta_pass,sigma_pass,source_pass,expected",
        [
            (True,  True,  True,  True),   # all pass
            (False, True,  True,  False),
            (True,  False, True,  False),
            (True,  True,  False, False),
            (False, False, True,  False),
            (False, True,  False, False),
            (True,  False, False, False),
            (False, False, False, False),  # all fail
        ],
    )
    def test_AND_truth_table(
        self, beta_pass, sigma_pass, source_pass, expected,
    ):
        tang = _pass_tangency() if source_pass else _fail_tangency()
        dec = make_canonical_decision(
            beta_result=(beta_pass, {}),
            sigma_result=(sigma_pass, {}),
            tangency_result=tang,
        )
        assert dec.allow_reduction == expected
        assert dec.beta_policy_pass == beta_pass
        assert dec.sigma_min_above_floor == sigma_pass
        assert dec.source_Dge2_gate_pass == source_pass


# ============================================================================
# Test Class 3 - source_Dge2_gate wrapper
# ============================================================================

class TestSourceDge2Gate:
    """Thin wrapper semantics around TangencyResult.is_tangent."""

    def test_pass_when_is_tangent(self):
        tang = _pass_tangency()
        passed, diag = source_Dge2_gate(tang)
        assert passed is True
        assert diag["relative_residual"] == tang.relative_residual
        assert "D" in diag and "fraction_on_manifold" in diag

    def test_fail_when_not_tangent(self):
        tang = _fail_tangency()
        passed, diag = source_Dge2_gate(tang)
        assert passed is False
        assert diag["relative_residual"] == tang.relative_residual

    def test_boundary_at_threshold(self):
        # Just below is_tangent threshold 1e-6 -> passes
        tang_pass = _make_tangency(rel_res=9.99e-7)
        passed, _ = source_Dge2_gate(tang_pass)
        assert passed is True

        # Just at/above threshold -> fails
        tang_fail = _make_tangency(rel_res=1.001e-6)
        passed, _ = source_Dge2_gate(tang_fail)
        assert passed is False


# ============================================================================
# Test Class 4 - make_canonical_decision factory
# ============================================================================

class TestFactoryPath:
    """Input shape validation; happy-path return shape."""

    def test_happy_path_types(self):
        dec = make_canonical_decision(
            (True, {"beta": 1e-3}),
            (True, {"sigma_min": 1e-5}),
            _pass_tangency(),
        )
        assert isinstance(dec, CanonicalDecision)
        assert isinstance(dec.emitted_labels, frozenset)
        assert dec.spec_version == SPEC_VERSION

    def test_rejects_non_tuple_beta(self):
        with pytest.raises(TypeError, match="beta_result"):
            make_canonical_decision(
                True,  # not a tuple
                (True, {}),
                _pass_tangency(),
            )

    def test_rejects_wrong_length_tuple(self):
        with pytest.raises(TypeError, match="sigma_result"):
            make_canonical_decision(
                (True, {}),
                (True, {}, "extra"),   # wrong length
                _pass_tangency(),
            )

    def test_rejects_non_bool_first_element(self):
        with pytest.raises(TypeError, match="must be bool"):
            make_canonical_decision(
                (1, {}),  # int, not bool
                (True, {}),
                _pass_tangency(),
            )

    def test_rejects_non_dict_second_element(self):
        with pytest.raises(TypeError, match="must be dict"):
            make_canonical_decision(
                (True, "not a dict"),
                (True, {}),
                _pass_tangency(),
            )


# ============================================================================
# Test Class 5 - Consumer API: require_allow_reduction + CanonicalBlockError
# ============================================================================

class TestConsumerAPI:
    """Error-raising helpers for downstream callers."""

    def test_no_raise_when_allow(self):
        dec = make_canonical_decision(
            (True, {}), (True, {}), _pass_tangency(),
        )
        # Should not raise
        require_allow_reduction(dec)

    def test_raises_CanonicalBlockError_when_block(self):
        dec = make_canonical_decision(
            (False, {}), (True, {}), _pass_tangency(),
        )
        with pytest.raises(CanonicalBlockError) as excinfo:
            require_allow_reduction(dec, context="unit_test")
        assert excinfo.value.decision is dec
        assert "unit_test" in str(excinfo.value)

    def test_CanonicalBlockError_carries_decision(self):
        dec = make_canonical_decision(
            (True, {}), (True, {}), _fail_tangency(),
        )
        err = CanonicalBlockError("msg", dec)
        assert err.decision is dec
        # Labels survive the exception trip
        assert ValidationLabel.TRACE_SOURCE_INADEQUATE in err.decision.emitted_labels


# ============================================================================
# Test Class 6 - Diagnostics propagation
# ============================================================================

class TestDiagnosticsFlow:
    """Diagnostics dict shape / readonly contract / forwarded values."""

    def test_diagnostics_has_three_branches(self):
        dec = make_canonical_decision(
            (True, {"beta": 1e-3, "threshold": 2e-3}),
            (True, {"sigma_min": 1e-5, "floor": 1e-6}),
            _pass_tangency(),
        )
        assert "beta" in dec.diagnostics
        assert "sigma" in dec.diagnostics
        assert "source" in dec.diagnostics

    def test_diagnostics_branches_preserve_values(self):
        dec = make_canonical_decision(
            (True, {"beta": 1.23e-3}),
            (True, {"sigma_min": 4.56e-5}),
            _pass_tangency(),
        )
        assert dec.diagnostics["beta"]["beta"] == pytest.approx(1.23e-3)
        assert dec.diagnostics["sigma"]["sigma_min"] == pytest.approx(4.56e-5)
        assert "relative_residual" in dec.diagnostics["source"]

    def test_diagnostics_top_level_readonly(self):
        dec = make_canonical_decision(
            (True, {}), (True, {}), _pass_tangency(),
        )
        # MappingProxyType at top level -> TypeError on setitem
        with pytest.raises(TypeError):
            dec.diagnostics["new_key"] = "injection"

    def test_labels_match_derive_labels_oracle(self):
        # The labels field must match derive_labels on the same inputs.
        beta, sigma = True, True
        tang = _pass_tangency()
        source_pass, source_diag = source_Dge2_gate(tang)
        dec = make_canonical_decision(
            (beta, {}), (sigma, {}), tang,
        )
        expected = derive_labels(
            beta_policy_pass=beta,
            sigma_min_above_floor=sigma,
            source_Dge2_gate_pass=source_pass,
            diagnostics={
                "beta": {},
                "sigma": {},
                "source": source_diag,
            },
        )
        assert dec.emitted_labels == expected
