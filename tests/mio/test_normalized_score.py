from __future__ import annotations

import dataclasses
import json

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.budget_spec import BudgetPolicy, BudgetSpec, BudgetUse
from mio.formalism.departure_bundle import build_departure_bundle
from mio.formalism.normalized_score import (
    NumeratorPolicy,
    NormalizedScore,
    build_normalized_score,
)


def _external_transfer_metadata(transfer_id: str) -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    return spec.to_metadata()


def _bundle(**overrides: object):
    values: dict[str, object] = {
        "components": {
            "Sigma2_std": 0.1,
            "W2_std": 0.4,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": "cfg-x",
        "input_hashes": ("x-input",),
    }
    values.update(overrides)
    return build_departure_bundle(**values)


def _budget(**overrides: object) -> BudgetSpec:
    values: dict[str, object] = {
        "policy": BudgetPolicy.MES_LINEAR,
        "denominator_value": 0.2,
        "denominator_label": "linear MES reference denominator",
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": "cfg-budget",
        "input_hashes": ("budget-input",),
        "assumptions": ("linear MES denominator for Q normalization",),
        "admissible_uses": (
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
        ),
    }
    values.update(overrides)
    return BudgetSpec(**values)


def test_q_preserves_explicit_numerator_and_denominator_policy() -> None:
    bundle = _bundle()
    budget = _budget()

    score = build_normalized_score(
        bundle,
        budget,
        numerator_policy=NumeratorPolicy.SIGNED,
        artifact_metadata={"report_role": "Q diagnostic"},
    )
    payload = score.as_payload()

    assert score.x_C == pytest.approx(-0.3)
    assert score.numerator_value == pytest.approx(-0.3)
    assert score.q_value == pytest.approx(-1.5)
    assert payload["score_label"] == "Q"
    assert payload["score_kind"] == "policy_normalized_score"
    assert payload["numerator_policy"] == "signed"
    assert payload["denominator_policy"] == "MES_linear"
    assert payload["denominator_value"] == pytest.approx(0.2)
    assert payload["denominator_label"] == "linear MES reference denominator"
    assert payload["denominator_use"] == "signed_projection_normalization"
    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["config_hash"]
    assert payload["input_hashes"] == ["x-input", "budget-input"]
    assert dataclasses.is_dataclass(score)


def test_numerator_policies_do_not_silently_hide_sign() -> None:
    bundle = _bundle()
    budget = _budget()

    signed = build_normalized_score(
        bundle,
        budget,
        numerator_policy="signed",
    )
    absolute = build_normalized_score(
        bundle,
        budget,
        numerator_policy="absolute",
    )
    positive = build_normalized_score(
        bundle,
        budget,
        numerator_policy="positive_part",
    )

    assert signed.numerator_value == pytest.approx(-0.3)
    assert signed.q_value == pytest.approx(-1.5)
    assert absolute.numerator_value == pytest.approx(0.3)
    assert absolute.q_value == pytest.approx(1.5)
    assert positive.numerator_value == pytest.approx(0.0)
    assert positive.q_value == pytest.approx(0.0)


def test_q_requires_budget_admitting_signed_projection_normalization() -> None:
    budget = _budget(admissible_uses=(BudgetUse.DENOMINATOR_SENSITIVITY,))

    with pytest.raises(ValueError, match="signed_projection_normalization"):
        build_normalized_score(_bundle(), budget, numerator_policy="signed")


def test_q_rejects_incompatible_bundle_and_budget_metadata() -> None:
    bundle = _bundle()

    with pytest.raises(ValueError, match="comparator"):
        build_normalized_score(
            bundle,
            _budget(comparator="other_comparator"),
            numerator_policy="signed",
        )
    with pytest.raises(ValueError, match="frame"):
        build_normalized_score(
            bundle,
            _budget(frame="tilted_frame"),
            numerator_policy="signed",
        )
    with pytest.raises(ValueError, match="units"):
        build_normalized_score(
            bundle,
            _budget(units="other_dimensionless_units"),
            numerator_policy="signed",
        )


def test_q_artifact_payload_never_uses_filling_or_occupancy_language() -> None:
    budget = _budget(
        is_admissible_ceiling=True,
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
        ),
    )
    score = build_normalized_score(_bundle(), budget, numerator_policy="absolute")
    payload_text = json.dumps(score.as_payload(), sort_keys=True)

    assert "filling" not in payload_text.lower()
    assert "occupancy" not in payload_text.lower()
    assert "certified_f" not in payload_text.lower()
    assert "posterior" not in payload_text.lower()
    assert "evidence" not in payload_text.lower()
    assert "family_id" not in payload_text.lower()
    assert "geometry" not in payload_text.lower()
    assert "native_validated" not in payload_text.lower()
    assert "F_value" not in score.as_payload()


def test_q_rejects_f_style_artifact_metadata_and_labels() -> None:
    bundle = _bundle()
    budget = _budget()

    with pytest.raises(ValueError, match="score_label"):
        NormalizedScore(
            departure_bundle=bundle,
            budget_spec=budget,
            numerator_policy="absolute",
            score_label="filling fraction",
        )
    with pytest.raises(ValueError, match="artifact_metadata"):
        build_normalized_score(
            bundle,
            budget,
            numerator_policy="absolute",
            artifact_metadata={"artifact_name": "Q occupancy proxy"},
        )
    with pytest.raises(ValueError, match="caveats"):
        NormalizedScore(
            departure_bundle=bundle,
            budget_spec=budget,
            numerator_policy="absolute",
            caveats=("Q is a certified_F proxy",),
        )


def test_q_rejects_reserved_budget_label_and_assumption_language() -> None:
    bundle = _bundle()

    with pytest.raises(ValueError, match="budget_spec"):
        build_normalized_score(
            bundle,
            _budget(denominator_label="certified filling ceiling denominator"),
            numerator_policy="absolute",
        )
    with pytest.raises(ValueError, match="budget_spec"):
        build_normalized_score(
            bundle,
            _budget(assumptions=("occupancy ceiling assumption",)),
            numerator_policy="absolute",
        )


def test_q_rejects_family_and_native_solver_prose_in_metadata() -> None:
    bundle = _bundle()
    budget = _budget()

    rejected_metadata = (
        {"caption": "Q supports family identification"},
        {"caption": "Q is a native solver result"},
        {"caption": "external transfer " + "validated as " + "native"},
    )

    for metadata in rejected_metadata:
        with pytest.raises(ValueError, match="artifact_metadata"):
            build_normalized_score(
                bundle,
                budget,
                numerator_policy="absolute",
                artifact_metadata=metadata,
            )

    with pytest.raises(ValueError, match="caveats"):
        NormalizedScore(
            departure_bundle=bundle,
            budget_spec=budget,
            numerator_policy="absolute",
            caveats=("Q family identified the model",),
        )


def test_external_transfer_budget_provenance_is_preserved_without_native_label() -> None:
    budget = _budget(
        policy=BudgetPolicy.EXTERNAL_TRANSFER,
        denominator_label="external transfer denominator",
        assumptions=("transfer-conditional denominator",),
        transfer_source="AniCLASS_external",
        transfer_spec_id="aniclass.lowell.budget.v1",
        transfer_metadata=_external_transfer_metadata("aniclass.lowell.budget.v1"),
    )

    payload = build_normalized_score(
        _bundle(),
        budget,
        numerator_policy="absolute",
    ).as_payload()

    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["departure_transfer_source"] == "none"
    assert payload["budget_transfer_source"] == "AniCLASS_external"
    assert payload["budget_transfer_spec_id"] == "aniclass.lowell.budget.v1"
    assert payload["budget_transfer_metadata"]["calibration_status"] == (
        "external_calibrated"
    )
    assert "native_validated" not in json.dumps(payload, sort_keys=True)


def test_transfer_derived_bundle_and_budget_must_match_when_both_present() -> None:
    bundle = _bundle(
        transfer_source="AniCLASS_external",
        transfer_spec_id="aniclass.lowell.scalar.v1",
        transfer_metadata=_external_transfer_metadata("aniclass.lowell.scalar.v1"),
    )
    budget = _budget(
        policy=BudgetPolicy.EXTERNAL_TRANSFER,
        denominator_label="external transfer denominator",
        assumptions=("transfer-conditional denominator",),
        transfer_source="AniCLASS_external",
        transfer_spec_id="aniclass.lowell.budget.v1",
        transfer_metadata=_external_transfer_metadata("aniclass.lowell.budget.v1"),
    )

    with pytest.raises(ValueError, match="transfer_spec_id"):
        build_normalized_score(bundle, budget, numerator_policy="absolute")


def test_formalism_package_exports_normalized_score_contract() -> None:
    import mio.formalism as formalism

    assert formalism.NormalizedScore is NormalizedScore
    assert formalism.NumeratorPolicy.SIGNED.value == "signed"
    assert formalism.build_normalized_score is build_normalized_score
