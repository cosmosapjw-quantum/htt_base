from __future__ import annotations

import dataclasses
import math

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.departure_bundle import (
    DepartureBundle,
    build_departure_bundle,
)
from mio.formalism.component_breakdown import (
    CANONICAL_COMPONENT_SIGNS,
    ComponentBreakdown,
    DepartureComponent,
    signed_component_projection,
)


def _external_transfer_metadata() -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id="aniclass.lowell.scalar.v1",
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref="aniclass:lowell:scalar:v1",
    )
    return spec.to_metadata()


def test_signed_projection_uses_comparator_basis_not_norm() -> None:
    components = {
        "Sigma2_std": 0.08,
        "W2_std": 0.23,
        "Omega_tilt": 0.02,
        "Omega_k_aniso": -0.01,
    }

    assert signed_component_projection(components) == pytest.approx(-0.14)
    assert abs(signed_component_projection(components)) < math.sqrt(
        sum(value * value for value in components.values())
    )


def test_canonical_component_signs_cannot_mutate_existing_bundles() -> None:
    bundle = build_departure_bundle(
        {
            "Sigma2_std": 0.1,
            "W2_std": 0.4,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg-immutable-signs",
        input_hashes=("input",),
    )
    original_x_c = bundle.x_C

    with pytest.raises(TypeError):
        CANONICAL_COMPONENT_SIGNS["W2_std"] = 1.0

    assert bundle.x_C == original_x_c
    assert bundle.as_payload()["component_breakdown"]["component_signs"][
        "W2_std"
    ] == pytest.approx(-1.0)


def test_departure_bundle_exports_xc_with_required_metadata() -> None:
    bundle = build_departure_bundle(
        {
            "Sigma2_std": 0.40,
            "W2_std": 0.15,
            "Omega_tilt": 0.03,
            "Omega_k_aniso": 0.01,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg-pr050",
        input_hashes=("input-a", "input-b"),
    )

    assert bundle.x_C == pytest.approx(0.29)
    assert bundle.component_breakdown.cancellation_index == pytest.approx(
        1.0 - abs(0.29) / (0.40 + 0.15 + 0.03 + 0.01)
    )
    payload = bundle.as_payload()
    assert payload["x_C"] == pytest.approx(0.29)
    assert payload["comparator"] == "CMB_FLRW_reference"
    assert payload["frame"] == "normal_frame"
    assert payload["units"] == "dimensionless_hubble_normalized"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["owner"] == "MIO"
    assert payload["config_hash"] == "cfg-pr050"
    assert payload["input_hashes"] == ["input-a", "input-b"]
    assert payload["component_breakdown"]["signed_contributions"]["W2_std"] == pytest.approx(
        -0.15
    )
    assert payload["absolute_component_total"] == pytest.approx(0.59)
    assert payload["sector_magnitude_companion"] == pytest.approx(0.59)
    assert payload["sector_profile"]["signed_component_vector"]["W2_std"] == pytest.approx(
        -0.15
    )
    assert payload["display_metadata"]["requires_sector_profile"] is True
    assert payload["display_metadata"]["requires_cancellation_index"] is True
    assert payload["display_metadata"]["requires_magnitude_companion_M"] is True


def test_component_metadata_must_match_export_metadata() -> None:
    component = DepartureComponent(
        name="Sigma2_std",
        value=0.1,
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
    )

    with pytest.raises(ValueError, match="same comparator"):
        ComponentBreakdown(
            components=(
                component,
                DepartureComponent(
                    name="W2_std",
                    value=0.0,
                    comparator="other",
                    frame="normal_frame",
                    units="dimensionless_hubble_normalized",
                ),
                DepartureComponent(
                    name="Omega_tilt",
                    value=0.0,
                    comparator="CMB_FLRW_reference",
                    frame="normal_frame",
                    units="dimensionless_hubble_normalized",
                ),
                DepartureComponent(
                    name="Omega_k_aniso",
                    value=0.0,
                    comparator="CMB_FLRW_reference",
                    frame="normal_frame",
                    units="dimensionless_hubble_normalized",
                ),
            ),
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
        )


def test_xc_cannot_be_exported_without_comparator_frame_units() -> None:
    components = {
        "Sigma2_std": 0.1,
        "W2_std": 0.0,
        "Omega_tilt": 0.0,
        "Omega_k_aniso": 0.0,
    }

    with pytest.raises(ValueError, match="comparator"):
        build_departure_bundle(
            components,
            comparator="",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
        )
    with pytest.raises(ValueError, match="frame"):
        build_departure_bundle(
            components,
            comparator="CMB_FLRW_reference",
            frame="",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
        )
    with pytest.raises(ValueError, match="units"):
        build_departure_bundle(
            components,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="",
            config_hash="cfg",
            input_hashes=("input",),
        )


def test_components_are_finite_and_complete() -> None:
    valid = {
        "Sigma2_std": 0.1,
        "W2_std": 0.0,
        "Omega_tilt": 0.0,
        "Omega_k_aniso": 0.0,
    }
    missing = dict(valid)
    missing.pop("W2_std")
    with pytest.raises(ValueError, match="canonical components"):
        build_departure_bundle(
            missing,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
        )
    with pytest.raises(ValueError, match="canonical components"):
        build_departure_bundle(
            {**valid, "extra_component": 1.0},
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
        )
    with pytest.raises(ValueError, match="finite"):
        build_departure_bundle(
            {**valid, "W2_std": float("nan")},
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
        )


def test_cancellation_index_handles_exact_cancellation_and_zero_total() -> None:
    exact = build_departure_bundle(
        {
            "Sigma2_std": 0.2,
            "W2_std": 0.2,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg",
        input_hashes=("input",),
    )
    zero = build_departure_bundle(
        {
            "Sigma2_std": 0.0,
            "W2_std": 0.0,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg",
        input_hashes=("input",),
    )

    assert exact.x_C == pytest.approx(0.0)
    assert exact.cancellation_index == pytest.approx(1.0)
    assert zero.x_C == pytest.approx(0.0)
    assert zero.cancellation_index == pytest.approx(0.0)


def test_xc_zero_counterexample_exports_large_sector_profile() -> None:
    bundle = build_departure_bundle(
        {
            "Sigma2_std": 0.35,
            "W2_std": 0.35,
            "Omega_tilt": 0.20,
            "Omega_k_aniso": -0.20,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg-counterexample",
        input_hashes=("input",),
    )

    payload = bundle.as_payload()

    assert bundle.x_C == pytest.approx(0.0)
    assert bundle.absolute_component_total == pytest.approx(1.10)
    assert bundle.sector_magnitude_companion == pytest.approx(1.10)
    assert bundle.cancellation_index == pytest.approx(1.0)
    assert payload["sector_profile"]["absolute_component_total"] == pytest.approx(1.10)
    assert payload["sector_profile"]["sector_magnitude_companion"] == pytest.approx(1.10)
    assert "not isotropy" in payload["sector_profile"]["interpretation"]


def test_bundle_requires_non_empty_input_hashes() -> None:
    with pytest.raises(ValueError, match="input_hashes"):
        build_departure_bundle(
            {
                "Sigma2_std": 0.1,
                "W2_std": 0.0,
                "Omega_tilt": 0.0,
                "Omega_k_aniso": 0.0,
            },
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=(),
        )


def test_transfer_derived_bundle_requires_pr014_metadata() -> None:
    components = {
        "Sigma2_std": 0.1,
        "W2_std": 0.0,
        "Omega_tilt": 0.0,
        "Omega_k_aniso": 0.0,
    }

    with pytest.raises(ValueError, match="transfer_metadata"):
        build_departure_bundle(
            components,
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
            transfer_source="AniCLASS_external",
        )

    bundle = build_departure_bundle(
        components,
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg",
        input_hashes=("input",),
        transfer_source="AniCLASS_external",
        transfer_spec_id="aniclass.lowell.scalar.v1",
        transfer_metadata=_external_transfer_metadata(),
    )

    assert bundle.as_payload()["transfer_source"] == "AniCLASS_external"
    assert bundle.as_payload()["transfer_metadata"]["calibration_status"] == (
        "external_calibrated"
    )


def test_external_transfer_metadata_cannot_claim_native_validation() -> None:
    metadata = _external_transfer_metadata()
    metadata["calibration_status"] = "native_validated"

    with pytest.raises(ValueError, match="external transfer"):
        build_departure_bundle(
            {
                "Sigma2_std": 0.1,
                "W2_std": 0.0,
                "Omega_tilt": 0.0,
                "Omega_k_aniso": 0.0,
            },
            comparator="CMB_FLRW_reference",
            frame="normal_frame",
            units="dimensionless_hubble_normalized",
            config_hash="cfg",
            input_hashes=("input",),
            transfer_source="AniCLASS_external",
            transfer_spec_id="aniclass.lowell.scalar.v1",
            transfer_metadata=metadata,
        )


def test_formalism_package_exports_public_contracts() -> None:
    import mio.formalism as formalism

    assert formalism.DepartureBundle is DepartureBundle
    assert formalism.build_departure_bundle is build_departure_bundle
    assert formalism.CANONICAL_COMPONENT_SIGNS["W2_std"] == -1.0


def test_bundle_is_diagnostic_not_inference_surface() -> None:
    bundle = build_departure_bundle(
        {
            "Sigma2_std": 0.2,
            "W2_std": 0.4,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash="cfg",
        input_hashes=("input",),
        caveats=("signed projection can be negative",),
    )

    assert bundle.x_C == pytest.approx(-0.2)
    assert bundle.claim_tier == "diagnostic_only"
    assert not hasattr(bundle, "posterior")
    assert not hasattr(bundle, "evidence")
    assert dataclasses.is_dataclass(bundle)
    assert CANONICAL_COMPONENT_SIGNS["W2_std"] == -1.0
    assert "signed projection can be negative" in bundle.as_payload()["caveats"]
