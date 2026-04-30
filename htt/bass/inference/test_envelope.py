"""Tests for the PA-12 inference envelope guard."""
from __future__ import annotations

import pytest

from bass.hierarchy.seed_factory import (
    STRONG_FAMILIES,
    TEMPLATE_CARD_FAMILIES,
)
from bass.inference.envelope import (
    ALLOWED_DATASET_KINDS,
    HEADLINE_SCIENCE_FORBIDDEN_KEYS,
    EnvelopeError,
    InferenceEnvelopeRequest,
    enforce_inference_envelope,
)


class TestStrongFamilyAllowed:
    def test_type_i_native_validation_passes_without_opt_in(self) -> None:
        config = {"dataset": {"kind": "type_i_native_validation"}}
        request = enforce_inference_envelope(config)
        assert request.dataset_kind == "type_i_native_validation"
        assert request.allow_template_card is False

    @pytest.mark.parametrize("family", sorted(STRONG_FAMILIES))
    def test_each_strong_family_passes(self, family: str) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "envelope": {"target_families": [family]},
        }
        request = enforce_inference_envelope(config)
        assert family in request.target_families


class TestTemplateCardFamilyRequiresOptIn:
    @pytest.mark.parametrize("family", sorted(TEMPLATE_CARD_FAMILIES))
    def test_template_card_family_blocked_without_opt_in(self, family: str) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "envelope": {"target_families": [family]},
        }
        with pytest.raises(EnvelopeError) as exc_info:
            enforce_inference_envelope(config)
        violations = exc_info.value.violations
        assert any("template_card_families_without_opt_in" in v for v in violations)

    @pytest.mark.parametrize("family", sorted(TEMPLATE_CARD_FAMILIES))
    def test_template_card_family_passes_with_opt_in(self, family: str) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "envelope": {
                "target_families": [family],
                "allow_template_card": True,
            },
        }
        request = enforce_inference_envelope(config)
        assert request.allow_template_card is True
        assert family in request.target_families


class TestUnknownFamilyAlwaysBlocks:
    def test_unknown_family_rejected(self) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "envelope": {"target_families": ["X_unknown"]},
        }
        with pytest.raises(EnvelopeError) as exc_info:
            enforce_inference_envelope(config)
        assert any("target_families" in v for v in exc_info.value.violations)

    def test_unknown_family_not_unblocked_by_opt_in(self) -> None:
        """``allow_template_card`` does not waive the registry check."""
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "envelope": {
                "target_families": ["LCDM_typo"],
                "allow_template_card": True,
            },
        }
        with pytest.raises(EnvelopeError):
            enforce_inference_envelope(config)


class TestDatasetKindGate:
    def test_unknown_kind_rejected(self) -> None:
        config = {"dataset": {"kind": "live_planck_2018"}}  # not yet wired
        with pytest.raises(EnvelopeError) as exc_info:
            enforce_inference_envelope(config)
        assert any("dataset.kind" in v for v in exc_info.value.violations)

    def test_synthetic_surrogate_requires_allow_surrogate(self) -> None:
        config = {"dataset": {"kind": "synthetic_surrogate"}}
        with pytest.raises(EnvelopeError) as exc_info:
            enforce_inference_envelope(config)
        assert any(
            "synthetic_surrogate_without_allow_surrogate" in v
            for v in exc_info.value.violations
        )

    def test_synthetic_surrogate_passes_with_allow_surrogate(self) -> None:
        config = {
            "dataset": {
                "kind": "synthetic_surrogate",
                "allow_surrogate": True,
            }
        }
        request = enforce_inference_envelope(config)
        assert request.dataset_kind == "synthetic_surrogate"


class TestHeadlineScienceGate:
    @pytest.mark.parametrize("key", HEADLINE_SCIENCE_FORBIDDEN_KEYS)
    def test_headline_key_blocks_without_research_goal_only(self, key: str) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            key: True,
        }
        with pytest.raises(EnvelopeError) as exc_info:
            enforce_inference_envelope(config)
        assert any(
            "headline_science_without_research_goal_only" in v
            for v in exc_info.value.violations
        )

    def test_nested_headline_key_detected(self) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "outputs": {"publish_F_Bayes": True},
        }
        with pytest.raises(EnvelopeError):
            enforce_inference_envelope(config)

    def test_research_goal_only_unlocks_headline_keys(self) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "publish_ln_B": True,
            "envelope": {"allow_research_goal_only": True},
        }
        request = enforce_inference_envelope(config)
        assert request.allow_research_goal_only is True
        assert "publish_ln_B" in request.headline_keys_present


class TestRequestNormalization:
    def test_request_freezes_target_families_as_strings(self) -> None:
        request = InferenceEnvelopeRequest(
            dataset_kind="type_i_native_validation",
            target_families=["I", "V"],  # list intentionally
        )
        assert isinstance(request.target_families, tuple)
        assert all(isinstance(f, str) for f in request.target_families)

    def test_envelope_passes_when_no_target_specified(self) -> None:
        config = {"dataset": {"kind": "type_i_native_validation"}}
        request = enforce_inference_envelope(config)
        assert request.target_families == ()


class TestExceptionShape:
    def test_envelope_error_carries_request(self) -> None:
        config = {
            "dataset": {"kind": "type_i_native_validation"},
            "envelope": {"target_families": ["II"]},
        }
        with pytest.raises(EnvelopeError) as exc_info:
            enforce_inference_envelope(config)
        assert isinstance(exc_info.value.request, InferenceEnvelopeRequest)
        assert "II" in exc_info.value.request.target_families
