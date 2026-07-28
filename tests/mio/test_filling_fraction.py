from __future__ import annotations

import dataclasses
import json

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.budget_spec import (
    BudgetPolicy,
    BudgetSpec,
    BudgetUse,
    NativeMorphologyAtlasStatus,
)
from mio.formalism.departure_bundle import build_departure_bundle
from mio.formalism.filling_fraction import (
    CertifiedFillingFraction,
    build_certified_filling_fraction,
)

_GENERATING_COMMAND = "pytest tests/mio/test_filling_fraction.py"
_WORKTREE_STATE = "test-fixture"


def _external_transfer_metadata(transfer_id: str) -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=30,
        ),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    return spec.to_metadata()


def _bundle(x_c: float, **overrides: object):
    values: dict[str, object] = {
        "components": {
            "Sigma2_std": x_c,
            "W2_std": 0.0,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-x-{x_c}",
        "input_hashes": (f"x-input-{x_c}",),
    }
    values.update(overrides)
    return build_departure_bundle(**values)


def _budget(denominator_value: float, **overrides: object) -> BudgetSpec:
    values: dict[str, object] = {
        "policy": BudgetPolicy.MES_LINEAR,
        "denominator_value": denominator_value,
        "denominator_label": "linear MES certified filling ceiling",
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-budget-{denominator_value}",
        "input_hashes": (f"budget-input-{denominator_value}",),
        "assumptions": ("linear MES ceiling for certified F",),
        "admissible_uses": (
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
        ),
        "is_admissible_ceiling": True,
    }
    values.update(overrides)
    return BudgetSpec(**values)


def test_f_valid_certified_samplewise_pushforward() -> None:
    f = build_certified_filling_fraction(
        (_bundle(0.2), _bundle(0.6)),
        (_budget(1.0), _budget(1.2)),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
        artifact_metadata={"report_role": "F diagnostic"},
    )

    payload = f.as_payload()

    assert dataclasses.is_dataclass(f)
    assert f.f_samples == pytest.approx((0.2, 0.5))
    assert f.mean_samplewise_legacy_F == pytest.approx(0.35)
    assert f.sector_magnitude_companion_samples == pytest.approx((0.2, 0.5))
    assert f.M_sector_magnitude == pytest.approx(0.35)
    assert payload["score_label"] == "F"
    assert payload["score_kind"] == "legacy_denominator_conditioned_ratio"
    assert payload["sample_pushforward"] == "sample_wise"
    assert payload["aggregation_method"] == "sample_mean_of_samplewise_F"
    assert payload["ratio_of_means_used"] is False
    assert payload["generating_command"] == _GENERATING_COMMAND
    assert payload["worktree_state"] == _WORKTREE_STATE
    assert payload["sign_clean_sector"] is True
    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["denominator_use"] == "certified_filling_ceiling"
    assert payload["budget_is_admissible_ceiling"] is True
    assert payload["sample_count"] == 2
    assert payload["valid_sample_count"] == 2
    assert payload["invalid_sample_count"] == 0
    assert payload["M_samples"] == pytest.approx([0.2, 0.5])
    assert payload["M_sector_magnitude"] == pytest.approx(0.35)
    assert payload["display_metadata"]["requires_magnitude_companion_M"] is True
    assert payload["input_hashes"] == [
        "x-input-0.2",
        "x-input-0.6",
        "budget-input-1.0",
        "budget-input-1.2",
    ]


def test_f_bayes_is_sample_mean_not_ratio_of_means() -> None:
    f = build_certified_filling_fraction(
        (_bundle(1.0), _bundle(9.0)),
        (_budget(2.0), _budget(90.0)),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    ratio_of_means = ((1.0 + 9.0) / 2.0) / ((2.0 + 90.0) / 2.0)

    assert f.f_samples == pytest.approx((0.5, 0.1))
    assert f.mean_samplewise_legacy_F == pytest.approx(0.3)
    assert f.mean_samplewise_legacy_F != pytest.approx(ratio_of_means)
    assert f.as_payload()["ratio_of_means_used"] is False


def test_f_reports_magnitude_companion_for_cancellation_case() -> None:
    cancelling_bundle = _bundle(
        0.0,
        components={
            "Sigma2_std": 0.4,
            "W2_std": 0.4,
            "Omega_tilt": 0.2,
            "Omega_k_aniso": -0.2,
        },
        config_hash="cfg-cancelling",
        input_hashes=("x-input-cancelling",),
    )

    payload = build_certified_filling_fraction(
        (cancelling_bundle,),
        (_budget(2.0),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    assert payload["x_C_samples"] == pytest.approx([0.0])
    assert payload["f_samples"] == pytest.approx([0.0])
    assert payload["absolute_component_total_samples"] == pytest.approx([1.2])
    assert payload["cancellation_index_samples"] == pytest.approx([1.0])
    assert payload["M_samples"] == pytest.approx([0.6])
    assert payload["M_sector_magnitude"] == pytest.approx(0.6)
    assert payload["display_metadata"]["requires_magnitude_companion_M"] is True
    assert payload["sector_profiles"][0]["absolute_component_total"] == pytest.approx(1.2)
    assert "not isotropy" in payload["sector_profiles"][0]["interpretation"]


def test_f_requires_sign_clean_nonnegative_sector() -> None:
    with pytest.raises(ValueError, match="sign-clean"):
        build_certified_filling_fraction(
            (_bundle(-0.1),),
            (_budget(1.0),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


@pytest.mark.parametrize("bad_ceiling", [0.0, -1.0, float("nan"), float("inf")])
def test_f_requires_positive_finite_ceiling_samples(bad_ceiling: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        _budget(bad_ceiling)


def test_f_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="same sample count"):
        build_certified_filling_fraction(
            (_bundle(0.1), _bundle(0.2)),
            (_budget(1.0),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_f_rejects_bundle_budget_metadata_mismatch() -> None:
    with pytest.raises(ValueError, match="comparator mismatch"):
        build_certified_filling_fraction(
            (_bundle(0.2),),
            (_budget(1.0, comparator="other_reference"),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )
    with pytest.raises(ValueError, match="frame mismatch"):
        build_certified_filling_fraction(
            (_bundle(0.2),),
            (_budget(1.0, frame="tilted_frame"),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )
    with pytest.raises(ValueError, match="units mismatch"):
        build_certified_filling_fraction(
            (_bundle(0.2),),
            (_budget(1.0, units="other_dimensionless_units"),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_f_preserves_super_anchor_stress_without_clipping() -> None:
    result = build_certified_filling_fraction(
        (_bundle(1.1),),
        (_budget(1.0),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )
    assert result.f_samples == pytest.approx((1.1,))
    assert result.exceedance_samples == pytest.approx((0.1,))
    assert result.as_payload()["status"] == "legacy_reproduction_only"


def test_f_allows_closed_interval_boundaries() -> None:
    f = build_certified_filling_fraction(
        (_bundle(0.0), _bundle(1.0)),
        (_budget(1.0), _budget(1.0)),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    assert f.f_samples == pytest.approx((0.0, 1.0))
    assert f.as_payload()["f_min"] == pytest.approx(0.0)
    assert f.as_payload()["f_max"] == pytest.approx(1.0)


def test_f_requires_budget_admitting_certified_filling_ceiling() -> None:
    budget = _budget(
        1.0,
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
        ),
        is_admissible_ceiling=False,
    )

    with pytest.raises(ValueError, match="certified_filling_ceiling"):
        build_certified_filling_fraction(
            (_bundle(0.2),),
            (budget,),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_f_requires_admissible_ceiling_budget() -> None:
    with pytest.raises(ValueError, match="certified filling"):
        _budget(
            1.0,
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
            is_admissible_ceiling=False,
        )


def test_f_rejects_non_certifying_budget_policies_pre_native() -> None:
    with pytest.raises(ValueError, match="external_transfer policy cannot certify"):
        _budget(
            1.0,
            policy=BudgetPolicy.EXTERNAL_TRANSFER,
            denominator_label="external transfer ceiling",
            assumptions=("transfer-conditional denominator",),
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.lowell.budget.v1",
            transfer_metadata=_external_transfer_metadata(
                "aniclass.lowell.budget.v1"
            ),
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
            is_admissible_ceiling=True,
        )

    with pytest.raises(ValueError, match="atlas_quantile policy cannot"):
        _budget(
            1.0,
            policy=BudgetPolicy.ATLAS_QUANTILE,
            quantile=0.95,
            confidence_level=0.95,
            native_morphology_atlas_status=(
                NativeMorphologyAtlasStatus.NOT_AVAILABLE_PRE_SOLVER
            ),
            source_description="pre-native atlas quantile scaffold",
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
            is_admissible_ceiling=True,
        )

    with pytest.raises(ValueError, match="observational budget policy cannot"):
        _budget(
            1.0,
            policy=BudgetPolicy.OBSERVATIONAL,
            channel="temperature",
            source_description="masked observational ceiling",
            sky_support_status="partial_sky_masked",
            covariance_status="empirical_covariance",
            null_mock_status="mock_calibrated",
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
            is_admissible_ceiling=True,
        )


def test_f_preserves_external_departure_provenance_without_native_label() -> None:
    transfer_bundle = _bundle(
        0.2,
        transfer_source="AniCLASS_external",
        transfer_spec_id="aniclass.lowell.scalar.v1",
        transfer_metadata=_external_transfer_metadata("aniclass.lowell.scalar.v1"),
    )

    payload = build_certified_filling_fraction(
        (transfer_bundle,),
        (_budget(1.0),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["departure_transfer_sources"] == ["AniCLASS_external"]
    assert payload["departure_transfer_spec_ids"] == ["aniclass.lowell.scalar.v1"]
    assert payload["budget_transfer_sources"] == ["none"]
    assert payload["budget_transfer_spec_ids"] == [None]
    assert "native_validated" not in json.dumps(payload, sort_keys=True)


def test_f_rejects_mismatched_transfer_spec_ids_across_samples() -> None:
    with pytest.raises(ValueError, match="transfer_spec_id"):
        build_certified_filling_fraction(
            (
                _bundle(
                    0.2,
                    transfer_source="AniCLASS_external",
                    transfer_spec_id="aniclass.lowell.scalar.v1",
                    transfer_metadata=_external_transfer_metadata(
                        "aniclass.lowell.scalar.v1"
                    ),
                ),
                _bundle(
                    0.3,
                    transfer_source="AniCLASS_external",
                    transfer_spec_id="aniclass.lowell.scalar.v2",
                    transfer_metadata=_external_transfer_metadata(
                        "aniclass.lowell.scalar.v2"
                    ),
                ),
            ),
            (_budget(1.0), _budget(1.0)),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_f_payload_carries_claim_and_provenance_metadata() -> None:
    payload = build_certified_filling_fraction(
        (_bundle(0.2),),
        (_budget(1.0),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    required_keys = {
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "covariance_status",
        "null_mock_status",
        "caveats",
        "denominator_policy",
        "denominator_use",
        "departure_config_hashes",
        "budget_config_hashes",
        "artifact_metadata",
        "generating_command",
        "git_commit",
        "worktree_state",
    }
    assert required_keys <= set(payload)
    assert payload["transfer_source"] == "none"
    assert payload["sky_support_status"] == "not_directional"
    assert payload["covariance_status"] == "not_statistical"
    assert payload["null_mock_status"] == "not_statistical"
    assert payload["sky_support_statuses"] == ["not_directional"]
    assert payload["covariance_statuses"] == ["not_statistical"]
    assert payload["null_mock_statuses"] == ["not_statistical"]


def test_f_rejects_overclaim_metadata_and_caveats() -> None:
    rejected_metadata = (
        {"caption": "F supports family identification"},
        {"caption": "F is a native solver result"},
        {"caption": "external transfer " + "validated as " + "native"},
        {"caption": "F is physical occupancy"},
    )
    for metadata in rejected_metadata:
        with pytest.raises(ValueError, match="artifact_metadata"):
            build_certified_filling_fraction(
                (_bundle(0.2),),
                (_budget(1.0),),
                generating_command=_GENERATING_COMMAND,
                worktree_state=_WORKTREE_STATE,
                artifact_metadata=metadata,
            )

    with pytest.raises(ValueError, match="caveats"):
        CertifiedFillingFraction(
            departure_bundles=(_bundle(0.2),),
            budget_specs=(_budget(1.0),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
            caveats=("F provides HTT evidence",),
        )

    with pytest.raises(ValueError, match="budget_spec"):
        build_certified_filling_fraction(
            (_bundle(0.2),),
            (_budget(1.0, assumptions=("physical occupancy assumption",)),),
            generating_command=_GENERATING_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_f_payload_requires_generation_and_worktree_provenance() -> None:
    with pytest.raises(ValueError, match="generating_command"):
        CertifiedFillingFraction(
            departure_bundles=(_bundle(0.2),),
            budget_specs=(_budget(1.0),),
            worktree_state=_WORKTREE_STATE,
        )

    with pytest.raises(ValueError, match="git_commit or worktree_state"):
        build_certified_filling_fraction(
            (_bundle(0.2),),
            (_budget(1.0),),
            generating_command=_GENERATING_COMMAND,
        )


def test_f_payload_marks_inference_and_family_uses_forbidden() -> None:
    payload = build_certified_filling_fraction(
        (_bundle(0.2),),
        (_budget(1.0),),
        generating_command=_GENERATING_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    assert payload["classification"] == "BC1_LEGACY_PROJECTION"
    assert payload["representation_policy"] == "BC2_NO_REPRESENTATION_PROMOTION"
    forbidden = set(payload["forbidden_use"])
    assert {"occupancy", "probability", "evidence", "family identification"} <= forbidden
    assert "posterior_summary" not in payload


def test_active_formalism_hides_legacy_filling_fraction_contract() -> None:
    import mio.formalism as formalism
    import mio.legacy_projection as legacy

    assert not hasattr(formalism, "CertifiedFillingFraction")
    assert not hasattr(formalism, "build_certified_filling_fraction")
    assert legacy.CertifiedFillingFraction is CertifiedFillingFraction
    assert legacy.build_certified_filling_fraction is build_certified_filling_fraction
