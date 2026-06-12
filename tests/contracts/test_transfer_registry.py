from __future__ import annotations

import pytest

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
    TransferValidRange,
    validate_transfer_dependent_result,
)
from workspace.contracts.transfer import TransferFunctionSpec as WorkspaceTransferFunctionSpec


def _range() -> TransferValidRange:
    return TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30)


def _external_spec(**overrides: object) -> TransferFunctionSpec:
    payload: dict[str, object] = {
        "transfer_id": "aniclass.lowell.temperature.v1",
        "source": "AniCLASS_external",
        "family": "BianchiI",
        "valid_range": _range(),
        "observable_kind": "temperature",
        "normalization": "unit_primordial_curvature",
        "calibration_status": "external_calibrated",
        "caveats": ("external-transfer path", "transfer-conditional result"),
        "source_ref": "aniclass:lowell:v1",
    }
    payload.update(overrides)
    return TransferFunctionSpec(**payload)  # type: ignore[arg-type]


def _native_spec(**overrides: object) -> TransferFunctionSpec:
    payload: dict[str, object] = {
        "transfer_id": "bass.native.lowell.temperature.v1",
        "source": "BASS_native_validated",
        "family": "BianchiI",
        "valid_range": _range(),
        "observable_kind": "temperature",
        "normalization": "unit_primordial_curvature",
        "calibration_status": "native_validated",
        "caveats": ("future native path", "requires native solver artifact"),
        "source_ref": "bass-native:lowell:v1",
        "passed_validation_gates": ("native_transfer_validated",),
    }
    payload.update(overrides)
    return TransferFunctionSpec(**payload)  # type: ignore[arg-type]


def test_transfer_spec_records_required_pr014_metadata() -> None:
    spec = _external_spec()

    metadata = spec.to_metadata()

    assert metadata["transfer_source"] == "AniCLASS_external"
    assert metadata["family"] == "BianchiI"
    assert metadata["valid_range"] == {
        "k_min": 1.0e-5,
        "k_max": 0.2,
        "ell_min": 2,
        "ell_max": 30,
    }
    assert metadata["observable_kind"] == "temperature"
    assert metadata["normalization"] == "unit_primordial_curvature"
    assert metadata["calibration_status"] == "external_calibrated"
    assert metadata["caveats"] == [
        "external-transfer path",
        "transfer-conditional result",
    ]


def test_transfer_valid_range_rejects_invalid_domains() -> None:
    with pytest.raises(ValueError, match="k_min"):
        TransferValidRange(k_min=0.2, k_max=1.0e-5, ell_min=2, ell_max=30)
    with pytest.raises(ValueError, match="ell_min"):
        TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=31, ell_max=30)


def test_external_transfer_cannot_claim_native_validation() -> None:
    with pytest.raises(ValueError, match="external.*native"):
        _external_spec(calibration_status="native_validated")
    with pytest.raises(ValueError, match="external.*native"):
        _external_spec(passed_validation_gates=("native_transfer_validated",))


def test_raw_external_transfer_metadata_cannot_claim_native_validation() -> None:
    metadata = _external_spec().to_metadata()
    metadata["calibration_status"] = "native_validated"

    with pytest.raises(ValueError, match="external.*native"):
        validate_transfer_dependent_result(metadata)


def test_native_validated_transfer_requires_native_gate() -> None:
    with pytest.raises(ValueError, match="native_transfer_validated"):
        _native_spec(passed_validation_gates=())

    spec = _native_spec()
    assert spec.source is TransferSource.BASS_NATIVE_VALIDATED
    assert spec.calibration_status is CalibrationStatus.NATIVE_VALIDATED


def test_external_and_native_transfer_specs_can_coexist_in_registry() -> None:
    registry = TransferRegistry()
    registry.register(_external_spec())
    registry.register(_native_spec())

    matches = registry.by_family("BianchiI")

    assert {spec.source for spec in matches} == {
        TransferSource.ANICLASS_EXTERNAL,
        TransferSource.BASS_NATIVE_VALIDATED,
    }
    assert (
        registry.get("aniclass.lowell.temperature.v1").observable_kind
        is ObservableKind.TEMPERATURE
    )
    assert (
        registry.get("bass.native.lowell.temperature.v1").source
        is TransferSource.BASS_NATIVE_VALIDATED
    )


def test_registry_rejects_duplicate_transfer_ids() -> None:
    registry = TransferRegistry([_external_spec()])

    with pytest.raises(ValueError, match="duplicate"):
        registry.register(_external_spec())


def test_transfer_dependent_result_requires_metadata_fields() -> None:
    metadata = _external_spec().to_metadata()
    del metadata["caveats"]

    with pytest.raises(ValueError, match="caveats"):
        validate_transfer_dependent_result(metadata)

    validate_transfer_dependent_result(_external_spec().to_metadata())


def test_transfer_dependent_result_requires_valid_range_shape() -> None:
    metadata = _external_spec().to_metadata()
    metadata["valid_range"] = {"k_min": 1.0e-5, "k_max": 0.2}

    with pytest.raises(ValueError, match="valid_range"):
        validate_transfer_dependent_result(metadata)


def test_transfer_spec_requires_non_string_caveat_sequence() -> None:
    with pytest.raises(ValueError, match="caveats"):
        _external_spec(caveats="transfer-conditional result")


def test_workspace_transfer_reexports_common_contract() -> None:
    assert WorkspaceTransferFunctionSpec is TransferFunctionSpec
