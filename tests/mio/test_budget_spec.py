from __future__ import annotations

import dataclasses

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.budget_spec import (
    BudgetPolicy,
    BudgetSpec,
    BudgetUse,
    NativeMorphologyAtlasStatus,
    build_budget_spec,
    compare_denominator_policies,
)


def _external_transfer_metadata() -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id="aniclass.lowell.budget.v1",
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref="aniclass:lowell:budget:v1",
    )
    return spec.to_metadata()


def _base_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "policy": BudgetPolicy.MES_LINEAR,
        "denominator_value": 0.8,
        "denominator_label": "linear MES reference envelope",
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_xC",
        "config_hash": "cfg-pr051",
        "input_hashes": ("input-a",),
        "assumptions": ("linearized MES denominator",),
        "admissible_uses": (
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
        ),
        "is_admissible_ceiling": True,
    }
    values.update(overrides)
    return values


def _spec(policy: BudgetPolicy, **overrides: object) -> BudgetSpec:
    kwargs = _base_kwargs(
        policy=policy,
        denominator_label=f"{policy.value} denominator",
        assumptions=(f"{policy.value} assumptions",),
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
        ),
        is_admissible_ceiling=False,
    )
    if policy is BudgetPolicy.EXTERNAL_TRANSFER:
        kwargs.update(
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.lowell.budget.v1",
            transfer_metadata=_external_transfer_metadata(),
        )
    elif policy is BudgetPolicy.ATLAS_QUANTILE:
        kwargs.update(
            quantile=0.95,
            confidence_level=0.95,
            native_morphology_atlas_status=(
                NativeMorphologyAtlasStatus.NOT_AVAILABLE_PRE_SOLVER
            ),
            source_description="pre-native atlas quantile denominator scaffold",
        )
    elif policy is BudgetPolicy.OBSERVATIONAL:
        kwargs.update(
            channel="temperature",
            redshift=0.0,
            source_description="masked low-ell observational denominator",
            sky_support_status="partial_sky_masked",
            covariance_status="empirical_covariance",
            null_mock_status="mock_calibrated",
        )
    kwargs.update(overrides)
    return BudgetSpec(**kwargs)


def test_budget_policies_are_explicit_and_distinct() -> None:
    assert {policy.value for policy in BudgetPolicy} == {
        "MES_linear",
        "external_transfer",
        "atlas_quantile",
        "observational",
    }

    specs = tuple(_spec(policy) for policy in BudgetPolicy)
    assert [spec.policy for spec in specs] == list(BudgetPolicy)
    assert [spec.as_payload()["denominator_policy"] for spec in specs] == [
        "MES_linear",
        "external_transfer",
        "atlas_quantile",
        "observational",
    ]


def test_denominator_policy_cannot_be_implicit() -> None:
    with pytest.raises(ValueError, match="denominator policy"):
        BudgetSpec(**_base_kwargs(policy=""))
    with pytest.raises(ValueError, match="denominator policy"):
        build_budget_spec(**_base_kwargs(policy="atlas_or_mes_ceiling"))


@pytest.mark.parametrize("bad_value", [0.0, -1.0, float("nan"), float("inf")])
def test_denominator_must_be_positive_finite(bad_value: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        BudgetSpec(**_base_kwargs(denominator_value=bad_value))


def test_external_transfer_budget_requires_pr014_metadata() -> None:
    with pytest.raises(ValueError, match="transfer_metadata"):
        BudgetSpec(
            **_base_kwargs(
                policy=BudgetPolicy.EXTERNAL_TRANSFER,
                transfer_source="AniCLASS_external",
                transfer_spec_id="aniclass.lowell.budget.v1",
                assumptions=("transfer-conditional denominator",),
                is_admissible_ceiling=False,
                admissible_uses=(BudgetUse.DENOMINATOR_SENSITIVITY,),
            )
        )

    budget = _spec(BudgetPolicy.EXTERNAL_TRANSFER)
    payload = budget.as_payload()

    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["transfer_metadata"]["calibration_status"] == "external_calibrated"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["owner"] == "MIO"


def test_external_transfer_budget_cannot_claim_native_validation() -> None:
    metadata = _external_transfer_metadata()
    metadata["calibration_status"] = "native_validated"

    with pytest.raises(ValueError, match="external transfer"):
        BudgetSpec(
            **_base_kwargs(
                policy=BudgetPolicy.EXTERNAL_TRANSFER,
                transfer_source="AniCLASS_external",
                transfer_spec_id="aniclass.lowell.budget.v1",
                transfer_metadata=metadata,
                assumptions=("transfer-conditional denominator",),
                is_admissible_ceiling=False,
                admissible_uses=(BudgetUse.DENOMINATOR_SENSITIVITY,),
            )
        )


def test_atlas_quantile_policy_is_schema_only_not_family_claim() -> None:
    budget = _spec(BudgetPolicy.ATLAS_QUANTILE)
    payload = budget.as_payload()

    assert payload["quantile"] == pytest.approx(0.95)
    assert payload["native_morphology_atlas_status"] == "not_available_pre_solver"
    assert "family_id" not in payload
    assert "posterior" not in payload
    assert "evidence" not in payload

    with pytest.raises(ValueError, match="pre-solver-safe"):
        _spec(
            BudgetPolicy.ATLAS_QUANTILE,
            native_morphology_atlas_status="native_validated",
        )

    with pytest.raises(ValueError, match="certified filling"):
        _spec(
            BudgetPolicy.ATLAS_QUANTILE,
            is_admissible_ceiling=True,
            admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
        )


def test_observational_policy_requires_support_status_metadata() -> None:
    with pytest.raises(ValueError, match="observational"):
        BudgetSpec(
            **_base_kwargs(
                policy=BudgetPolicy.OBSERVATIONAL,
                assumptions=("observational denominator",),
                is_admissible_ceiling=False,
                admissible_uses=(BudgetUse.DENOMINATOR_SENSITIVITY,),
            )
        )

    budget = _spec(BudgetPolicy.OBSERVATIONAL)
    payload = budget.as_payload()

    assert payload["sky_support_status"] == "partial_sky_masked"
    assert payload["covariance_status"] == "empirical_covariance"
    assert payload["null_mock_status"] == "mock_calibrated"


def test_sensitivity_hooks_carry_policy_and_denominator_metadata() -> None:
    budget = _spec(BudgetPolicy.MES_LINEAR, denominator_value=2.0)

    points = budget.sensitivity_grid(relative_shifts=(-0.25, 0.0, 0.25))
    assert [point.denominator_value for point in points] == pytest.approx(
        [1.5, 2.0, 2.5]
    )
    assert {point.policy for point in points} == {BudgetPolicy.MES_LINEAR}
    assert points[0].as_payload()["relative_shift"] == pytest.approx(-0.25)
    assert points[0].as_payload()["claim_tier"] == "diagnostic_only"
    assert points[0].as_payload()["config_hash"] == "cfg-pr051"
    assert points[0].as_payload()["input_hashes"] == ["input-a"]

    with pytest.raises(ValueError, match="positive"):
        budget.denominator_at_shift(-1.0)


def test_transfer_sensitivity_points_preserve_pr014_provenance() -> None:
    budget = _spec(BudgetPolicy.EXTERNAL_TRANSFER)

    point = budget.sensitivity_grid(relative_shifts=(0.0,))[0]
    payload = point.as_payload()

    assert payload["transfer_source"] == "AniCLASS_external"
    assert payload["transfer_spec_id"] == "aniclass.lowell.budget.v1"
    assert payload["transfer_metadata"]["transfer_id"] == "aniclass.lowell.budget.v1"
    assert payload["transfer_metadata"]["calibration_status"] == "external_calibrated"
    assert payload["config_hash"] == "cfg-pr051"
    assert payload["input_hashes"] == ["input-a"]
    assert payload["assumptions"] == ["external_transfer assumptions"]


def test_compare_denominator_policies_preserves_policy_separation() -> None:
    specs = tuple(
        _spec(policy, denominator_value=1.0 + index)
        for index, policy in enumerate(BudgetPolicy)
    )

    points = compare_denominator_policies(specs, relative_shifts=(0.0,))

    assert [point.policy for point in points] == list(BudgetPolicy)
    assert [point.denominator_value for point in points] == pytest.approx(
        [1.0, 2.0, 3.0, 4.0]
    )


def test_formalism_package_exports_budget_contracts() -> None:
    import mio.formalism as formalism

    assert formalism.BudgetSpec is BudgetSpec
    assert formalism.BudgetPolicy.MES_LINEAR.value == "MES_linear"
    assert formalism.build_budget_spec is build_budget_spec


def test_budget_spec_is_diagnostic_not_inference_surface() -> None:
    budget = _spec(BudgetPolicy.MES_LINEAR)
    payload = budget.as_payload()

    assert dataclasses.is_dataclass(budget)
    assert budget.owner == "MIO"
    assert budget.claim_tier == "diagnostic_only"
    assert not hasattr(budget, "posterior")
    assert not hasattr(budget, "evidence")
    assert not hasattr(budget, "family_id")
    assert "posterior" not in payload
    assert "evidence" not in payload
    assert "family_id" not in payload
