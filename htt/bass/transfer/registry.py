"""Default BASS transfer-provenance registry for current external paths."""

from __future__ import annotations

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
    TransferValidRange,
)

from .aniclass_adapter import (
    ExternalTransferAdapter,
    ExternalTransferAdapterRegistry,
)

_LEGACY_MODULE = "htt.core.evidence_models_R03a"
_FAMILY = "VII_h_external_calibration"
_ANICLASS_SOURCE_REF = "htt.core.evidence_models_R03a:VR-17:Planck2018:OmegaK0.001"
_EMPIRICAL_PROXY_SOURCE_REF = "htt.core.evidence_models_R03a:BASS_v8.2_power_law_fit"
_X_H_RANGE = {"x_h_min": 0.001, "x_h_max": 1000.0}
_SIGMA2_ANICLASS_RANGE = {
    "Sigma2_min": 1.0e-24,
    "Sigma2_max": 1.0e-20,
    "Sigma2_note": "legacy Saadeh-linear-regime external calibration window",
    **_X_H_RANGE,
    "x_h_note": "explicit x_h values use the AniCLASS interpolation domain",
}
_SIGMA2_PROXY_RANGE = {"Sigma2_min": 1.0e-11, "Sigma2_max": 1.0e-3}
_ANICLASS_CAVEATS = (
    "external-transfer path",
    "transfer-conditional result",
    "not native solver output",
    "calibration family label is provenance only, not family identification",
    "PR-014 valid_range k fields are schema carriers; callable input domain is adapter metadata",
    "legacy AniCLASS-calibrated table/function; no live external code execution",
)
_EMPIRICAL_PROXY_CAVEATS = (
    "empirical_proxy",
    "transfer-conditional result",
    "not native solver output",
    "not family identification or morphology compatibility evidence",
    "PR-014 valid_range k fields are schema carriers; callable input domain is adapter metadata",
    "BASS power-law comparison path, not HTT evidence",
)


def default_external_transfer_registry() -> TransferRegistry:
    """Return the PR-014 registry for current external/proxy transfer paths."""

    return default_external_transfer_adapter_registry().as_transfer_registry()


def default_external_transfer_adapter_registry() -> ExternalTransferAdapterRegistry:
    """Return lazy adapters for current AniCLASS/proxy transfer-dependent paths."""

    return ExternalTransferAdapterRegistry(_default_adapters())


def _default_adapters() -> tuple[ExternalTransferAdapter, ...]:
    return (
        _aniclass_adapter(
            transfer_id="aniclass.lowell.f2_vector.v1",
            function_name="f2_vector",
            ell_min=2,
            ell_max=2,
            observable_kind=ObservableKind.SCALAR_SUMMARY,
            normalization="fractional_ell2_power",
            parameter_range=_X_H_RANGE,
        ),
        _aniclass_adapter(
            transfer_id="aniclass.lowell.f2_tensor.v1",
            function_name="f2_tensor",
            ell_min=2,
            ell_max=2,
            observable_kind=ObservableKind.SCALAR_SUMMARY,
            normalization="fractional_ell2_power",
            parameter_range=_X_H_RANGE,
        ),
        _aniclass_adapter(
            transfer_id="aniclass.lowell.f3_vector.v1",
            function_name="f3_vector",
            ell_min=3,
            ell_max=3,
            observable_kind=ObservableKind.SCALAR_SUMMARY,
            normalization="fractional_ell3_power",
            parameter_range=_X_H_RANGE,
        ),
        _aniclass_adapter(
            transfer_id="aniclass.lowell.f3_tensor.v1",
            function_name="f3_tensor",
            ell_min=3,
            ell_max=3,
            observable_kind=ObservableKind.SCALAR_SUMMARY,
            normalization="fractional_ell3_power",
            parameter_range=_X_H_RANGE,
        ),
        _aniclass_adapter(
            transfer_id="aniclass.lowell.shear_to_D2.v1",
            function_name="shear_to_D2",
            ell_min=2,
            ell_max=2,
            observable_kind=ObservableKind.TEMPERATURE,
            normalization="Sigma2_to_D2_microkelvin_squared",
            parameter_range=_SIGMA2_ANICLASS_RANGE,
        ),
        _aniclass_adapter(
            transfer_id="aniclass.lowell.shear_to_D3.v1",
            function_name="shear_to_D3",
            ell_min=3,
            ell_max=3,
            observable_kind=ObservableKind.TEMPERATURE,
            normalization="Sigma2_to_D3_microkelvin_squared",
            parameter_range=_SIGMA2_ANICLASS_RANGE,
        ),
        _empirical_proxy_adapter(
            transfer_id="bass.empirical_proxy.shear_to_D2.v1",
            function_name="bass_shear_to_D2",
            ell_min=2,
            ell_max=2,
            observable_kind=ObservableKind.TEMPERATURE,
            normalization="Sigma2_to_D2_microkelvin_squared",
            parameter_range=_SIGMA2_PROXY_RANGE,
        ),
    )


def _aniclass_adapter(
    *,
    transfer_id: str,
    function_name: str,
    ell_min: int,
    ell_max: int,
    observable_kind: ObservableKind,
    normalization: str,
    parameter_range: dict[str, object],
) -> ExternalTransferAdapter:
    return ExternalTransferAdapter(
        transfer_spec=TransferFunctionSpec(
            transfer_id=transfer_id,
            source=TransferSource.ANICLASS_EXTERNAL,
            family=_FAMILY,
            valid_range=_valid_range(ell_min, ell_max),
            observable_kind=observable_kind,
            normalization=normalization,
            calibration_status=CalibrationStatus.EXTERNAL_CALIBRATED,
            caveats=_ANICLASS_CAVEATS,
            source_ref=_ANICLASS_SOURCE_REF,
            version="pr080",
        ),
        callable_path=f"{_LEGACY_MODULE}:{function_name}",
        parameter_range=parameter_range,
    )


def _empirical_proxy_adapter(
    *,
    transfer_id: str,
    function_name: str,
    ell_min: int,
    ell_max: int,
    observable_kind: ObservableKind,
    normalization: str,
    parameter_range: dict[str, object],
) -> ExternalTransferAdapter:
    return ExternalTransferAdapter(
        transfer_spec=TransferFunctionSpec(
            transfer_id=transfer_id,
            source=TransferSource.EMPIRICAL_PROXY,
            family="BASS_empirical_proxy",
            valid_range=_valid_range(ell_min, ell_max),
            observable_kind=observable_kind,
            normalization=normalization,
            calibration_status=CalibrationStatus.EMPIRICAL_PROXY,
            caveats=_EMPIRICAL_PROXY_CAVEATS,
            source_ref=_EMPIRICAL_PROXY_SOURCE_REF,
            version="pr080",
        ),
        callable_path=f"{_LEGACY_MODULE}:{function_name}",
        parameter_range=parameter_range,
    )


def _valid_range(ell_min: int, ell_max: int) -> TransferValidRange:
    return TransferValidRange(
        k_min=1.0e-5,
        k_max=0.2,
        ell_min=ell_min,
        ell_max=ell_max,
    )


__all__ = [
    "default_external_transfer_adapter_registry",
    "default_external_transfer_registry",
]
