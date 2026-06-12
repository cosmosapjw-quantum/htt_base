"""Schema-only contracts for future native low-ell transfer outputs.

This module prepares metadata that a future external solver artifact may fill
before it becomes a native-transfer output.  It does not run that solver,
synthesize placeholder spectra, or return solver-output values.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferRegistry,
    TransferSource,
    TransferValidRange,
)

_SCHEMA_VERSION = "bass.native_lowell_schema.v1"
_ADAPTER_SCOPE = "future_native_lowell"
_ALLOWED_COEFFICIENT_SPACES = {"alm", "cl", "biposh", "template", "covariance"}
_FORBIDDEN_CLAIM_TERMS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "detected",
    "identified",
    "ranking",
)
_DEFAULT_CAVEATS = (
    "schema-only future adapter",
    "requires external solver artifact before values exist",
    "provisional transfer metadata",
    "geometry and family-ID status blocked",
)


@dataclass(frozen=True)
class NativeSchemaTransferFunctionSpec(TransferFunctionSpec):
    """Transfer spec metadata that remains marked as schema-only."""

    def to_metadata(self) -> dict[str, object]:
        metadata = super().to_metadata()
        metadata.update(
            {
                "schema_status": "schema_only_no_solver_output",
                "adapter_scope": _ADAPTER_SCOPE,
                "implementation_scope": "bass_py",
                "claim_tier": "diagnostic_only",
                "production_status": "schema_only",
                "native_solver_result": False,
                "returns_values": False,
                "outputs_available": False,
                "consumable_as_result": False,
                "artifact_status": "not_available_schema_only",
                "family_label_role": "schema_provenance_only_not_identification",
                "family_identification_status": "blocked_pre_native_morphology_atlas",
            }
        )
        return metadata


@dataclass(frozen=True)
class NativeLowEllObservableSchema:
    """Descriptor for one future native low-ell observable block."""

    name: str
    observable_kind: ObservableKind | str
    channels: Sequence[str]
    ell_min: int
    ell_max: int
    coefficient_space: str
    normalization: str
    units: str
    convention_ref: str
    spin_weight: int = 0
    harmonic_ordering: str = "dense_full_alm_l_major_m_minus_l_to_plus_l"
    split_descriptors: Sequence[str] = ("det", "stoch", "boost")
    covariance_status: str = "not_supplied"
    mask_status: str = "not_supplied"
    extra_requirements: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("NativeLowEllObservableSchema.name is required")
        observable_kind = ObservableKind(str(self.observable_kind))
        if isinstance(self.channels, (str, bytes)):
            raise ValueError(
                "NativeLowEllObservableSchema.channels must be a non-string sequence"
            )
        channels = tuple(str(channel).strip() for channel in self.channels)
        if not channels or any(not channel for channel in channels):
            raise ValueError("NativeLowEllObservableSchema.channels must be non-empty")
        ell_min = int(self.ell_min)
        ell_max = int(self.ell_max)
        if ell_min < 2:
            raise ValueError("NativeLowEllObservableSchema.ell_min must be >= 2")
        if ell_max < ell_min:
            raise ValueError("NativeLowEllObservableSchema.ell_max must be >= ell_min")
        coefficient_space = str(self.coefficient_space).strip()
        if coefficient_space not in _ALLOWED_COEFFICIENT_SPACES:
            raise ValueError(
                "NativeLowEllObservableSchema.coefficient_space must be one of "
                f"{sorted(_ALLOWED_COEFFICIENT_SPACES)}"
            )
        normalization = str(self.normalization).strip()
        units = str(self.units).strip()
        convention_ref = str(self.convention_ref).strip()
        if not normalization:
            raise ValueError("NativeLowEllObservableSchema.normalization is required")
        if not units:
            raise ValueError("NativeLowEllObservableSchema.units is required")
        if not convention_ref:
            raise ValueError("NativeLowEllObservableSchema.convention_ref is required")
        covariance_status = str(self.covariance_status).strip()
        mask_status = str(self.mask_status).strip()
        if not covariance_status:
            raise ValueError("NativeLowEllObservableSchema.covariance_status is required")
        if not mask_status:
            raise ValueError("NativeLowEllObservableSchema.mask_status is required")
        extra_requirements = {
            str(key): value for key, value in self.extra_requirements.items()
        }
        split_descriptors = tuple(
            str(item).strip() for item in self.split_descriptors
        )
        if split_descriptors != ("det", "stoch", "boost"):
            raise ValueError(
                "NativeLowEllObservableSchema.split_descriptors must be "
                "('det', 'stoch', 'boost')"
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "observable_kind", observable_kind)
        object.__setattr__(self, "channels", channels)
        object.__setattr__(self, "ell_min", ell_min)
        object.__setattr__(self, "ell_max", ell_max)
        object.__setattr__(self, "coefficient_space", coefficient_space)
        object.__setattr__(self, "normalization", normalization)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "convention_ref", convention_ref)
        object.__setattr__(self, "spin_weight", int(self.spin_weight))
        object.__setattr__(
            self,
            "harmonic_ordering",
            str(self.harmonic_ordering).strip(),
        )
        if not self.harmonic_ordering:
            raise ValueError("NativeLowEllObservableSchema.harmonic_ordering is required")
        object.__setattr__(self, "split_descriptors", split_descriptors)
        object.__setattr__(self, "covariance_status", covariance_status)
        object.__setattr__(self, "mask_status", mask_status)
        object.__setattr__(self, "extra_requirements", extra_requirements)
        _reject_forbidden_claim_language(
            {
                "name": name,
                "channels": channels,
                "coefficient_space": coefficient_space,
                "normalization": normalization,
                "units": units,
                "convention_ref": convention_ref,
                "harmonic_ordering": self.harmonic_ordering,
                "split_descriptors": split_descriptors,
                "covariance_status": covariance_status,
                "mask_status": mask_status,
                "extra_requirements": extra_requirements,
            },
            path="NativeLowEllObservableSchema",
        )

    def transfer_id(self, prefix: str) -> str:
        return f"{prefix}.{self.name}.v1"

    def valid_range_from(self, valid_range: TransferValidRange) -> TransferValidRange:
        return TransferValidRange(
            k_min=valid_range.k_min,
            k_max=valid_range.k_max,
            ell_min=self.ell_min,
            ell_max=self.ell_max,
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "name": self.name,
            "observable_kind": self.observable_kind.value,
            "channels": list(self.channels),
            "ell_min": self.ell_min,
            "ell_max": self.ell_max,
            "coefficient_space": self.coefficient_space,
            "normalization": self.normalization,
            "units": self.units,
            "convention_ref": self.convention_ref,
            "spin_weight": self.spin_weight,
            "harmonic_ordering": self.harmonic_ordering,
            "split_descriptors": list(self.split_descriptors),
            "covariance_status": self.covariance_status,
            "mask_status": self.mask_status,
            "extra_requirements": dict(self.extra_requirements),
        }


@dataclass(frozen=True)
class NativeLowEllSchema:
    """Future native low-ell adapter schema without solver-output values."""

    transfer_id_prefix: str
    family: str
    valid_range: TransferValidRange
    observables: Sequence[NativeLowEllObservableSchema]
    source_ref: str
    version: str = _SCHEMA_VERSION
    calibration_status: CalibrationStatus | str = CalibrationStatus.NATIVE_PROVISIONAL
    schema_status: str = "schema_only_no_solver_output"
    caveats: Sequence[str] = _DEFAULT_CAVEATS

    def __post_init__(self) -> None:
        prefix = str(self.transfer_id_prefix).strip()
        if not prefix:
            raise ValueError("NativeLowEllSchema.transfer_id_prefix is required")
        family = str(self.family).strip()
        if not family:
            raise ValueError("NativeLowEllSchema.family is required")
        if not isinstance(self.valid_range, TransferValidRange):
            raise TypeError("NativeLowEllSchema.valid_range must be TransferValidRange")
        observables = tuple(self.observables)
        if not observables:
            raise ValueError("NativeLowEllSchema.observables must be non-empty")
        if any(
            not isinstance(item, NativeLowEllObservableSchema) for item in observables
        ):
            raise TypeError(
                "NativeLowEllSchema.observables must be NativeLowEllObservableSchema"
            )
        names = [observable.name for observable in observables]
        if len(set(names)) != len(names):
            raise ValueError("NativeLowEllSchema observables must have unique names")
        calibration_status = CalibrationStatus(str(self.calibration_status))
        if calibration_status is not CalibrationStatus.NATIVE_PROVISIONAL:
            raise ValueError(
                "NativeLowEllSchema calibration_status must remain provisional"
            )
        if self.schema_status != "schema_only_no_solver_output":
            raise ValueError(
                "NativeLowEllSchema.schema_status must be schema_only_no_solver_output"
            )
        caveats = tuple(str(caveat).strip() for caveat in self.caveats)
        if not caveats or any(not caveat for caveat in caveats):
            raise ValueError("NativeLowEllSchema.caveats must be non-empty")
        source_ref = str(self.source_ref).strip()
        if not source_ref:
            raise ValueError("NativeLowEllSchema.source_ref is required")
        object.__setattr__(self, "transfer_id_prefix", prefix)
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "observables", observables)
        object.__setattr__(self, "source_ref", source_ref)
        object.__setattr__(self, "calibration_status", calibration_status)
        object.__setattr__(self, "caveats", caveats)
        _reject_forbidden_claim_language(
            {
                "transfer_id_prefix": prefix,
                "family": family,
                "source_ref": source_ref,
                "version": self.version,
                "schema_status": self.schema_status,
                "caveats": caveats,
            },
            path="NativeLowEllSchema",
        )

    def observable(self, name: str) -> NativeLowEllObservableSchema:
        for observable in self.observables:
            if observable.name == name:
                return observable
        raise KeyError(f"unknown native low-ell observable {name!r}")

    def to_transfer_spec(self, observable_name: str) -> TransferFunctionSpec:
        observable = self.observable(observable_name)
        spec = NativeSchemaTransferFunctionSpec(
            transfer_id=observable.transfer_id(self.transfer_id_prefix),
            source=TransferSource.BASS_NATIVE_PROVISIONAL,
            family=self.family,
            valid_range=observable.valid_range_from(self.valid_range),
            observable_kind=observable.observable_kind,
            normalization=observable.normalization,
            calibration_status=self.calibration_status,
            caveats=self.caveats,
            source_ref=self.source_ref,
            version=self.version,
            passed_validation_gates=(),
        )
        return spec

    def to_transfer_registry(self) -> TransferRegistry:
        return TransferRegistry(
            self.to_transfer_spec(observable.name) for observable in self.observables
        )

    def to_metadata(self) -> dict[str, object]:
        transfer_ids = [
            observable.transfer_id(self.transfer_id_prefix)
            for observable in self.observables
        ]
        return {
            "metadata_schema": self.version,
            "adapter_scope": _ADAPTER_SCOPE,
            "schema_status": self.schema_status,
            "artifact_manifest_schema": {
                "owner": "BASS",
                "implementation_scope": "bass_py",
                "claim_tier": "diagnostic_only",
                "transfer_source": TransferSource.BASS_NATIVE_PROVISIONAL.value,
                "config_hash": "required_future_field_no_values",
                "input_hashes": "required_future_field_no_values",
                "generating_command": "required_future_field_no_values",
                "git_commit_or_worktree_state": "required_future_field_no_values",
                "caveats": "required_future_field_no_values",
            },
            "implementation_scope": "bass_py",
            "claim_tier": "diagnostic_only",
            "production_status": "schema_only",
            "transfer_source": TransferSource.BASS_NATIVE_PROVISIONAL.value,
            "calibration_status": self.calibration_status.value,
            "transfer_id_prefix": self.transfer_id_prefix,
            "transfer_ids": transfer_ids,
            "family": self.family,
            "family_label_role": "schema_provenance_only_not_identification",
            "valid_range": self.valid_range.to_metadata(),
            "source_ref": self.source_ref,
            "observables": [
                observable.to_metadata() for observable in self.observables
            ],
            "output_split_schema": {
                "alm_det": "required_future_field_no_values",
                "alm_stoch": "required_future_field_no_values",
                "alm_boost": "required_future_field_no_values",
            },
            "observable_output_split_schema": {
                observable.name: {
                    "alm_det": "required_future_field_no_values",
                    "alm_stoch": "required_future_field_no_values",
                    "alm_boost": "required_future_field_no_values",
                }
                for observable in self.observables
            },
            "tilt_and_boost_status_schema": {
                "global_tilt_present_status": "required_future_status_no_value",
                "boost_applied_status": "required_future_status_no_value",
                "local_observer_boost_status": "required_future_status_no_value",
                "survey_systematic_status": "required_future_status_no_value",
            },
            "gate_status_schema": {
                "thomson_status": "required_future_status_no_value",
                "visibility_history_status": "required_future_status_no_value",
                "family_backend_status": "required_future_status_no_value",
                "ic_provenance_status": "required_future_status_no_value",
                "production_cutoff_status": "required_future_status_no_value",
                "output_split_status": "required_future_status_no_value",
                "rank_gate_status": "required_future_status_no_value",
                "mask_gate_status": "required_future_status_no_value",
                "covariance_gate_status": "required_future_status_no_value",
                "equivalence_graph_status": "required_future_status_no_value",
                "null_mock_gate_status": "required_future_status_no_value",
            },
            "residual_summary_schema": {
                "constraint_residual_status": "required_future_status_no_value",
                "transport_residual_status": "required_future_status_no_value",
                "closure_residual_status": "required_future_status_no_value",
            },
            "morphology_gate_future_fields": {
                "equivalence_graph_ref": "required_future_field_no_values",
                "response_rank_summary_ref": "required_future_field_no_values",
                "mask_hash": "required_future_field_no_values",
                "covariance_ref": "required_future_field_no_values",
                "null_mock_ref": "required_future_field_no_values",
            },
            "family_identification_status": "blocked_pre_native_morphology_atlas",
            "morphology_atlas_status": "absent",
            "equivalence_class_status": "not_evaluated",
            "response_rank_status": "not_evaluated",
            "null_mock_status": "not_evaluated",
            "mask_status": "not_evaluated",
            "covariance_status": "not_evaluated",
            "native_solver_result": False,
            "returns_values": False,
            "outputs_available": False,
            "consumable_as_result": False,
            "artifact_status": "not_available_schema_only",
            "passed_validation_gates": [],
            "caveats": list(self.caveats),
        }


def default_native_lowell_schema() -> NativeLowEllSchema:
    """Return a schema-only native low-ell handoff contract."""

    return NativeLowEllSchema(
        transfer_id_prefix="native.lowell",
        family="future_native_lowell_schema",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=32,
        ),
        observables=(
            NativeLowEllObservableSchema(
                name="alm_T",
                observable_kind=ObservableKind.TEMPERATURE,
                channels=("TT",),
                ell_min=2,
                ell_max=32,
                coefficient_space="alm",
                normalization="dimensionless_delta_t_over_t",
                units="dimensionless",
                convention_ref="obsstat.alm_conventions.temperature.v1",
            ),
            NativeLowEllObservableSchema(
                name="alm_E",
                observable_kind=ObservableKind.POLARIZATION_E,
                channels=("EE",),
                ell_min=2,
                ell_max=32,
                coefficient_space="alm",
                normalization="dimensionless_polarization",
                units="dimensionless",
                convention_ref="obsstat.alm_conventions.spin2.v1",
                spin_weight=2,
            ),
            NativeLowEllObservableSchema(
                name="alm_B",
                observable_kind=ObservableKind.POLARIZATION_B,
                channels=("BB",),
                ell_min=2,
                ell_max=32,
                coefficient_space="alm",
                normalization="dimensionless_polarization",
                units="dimensionless",
                convention_ref="obsstat.alm_conventions.spin2.v1",
                spin_weight=2,
            ),
        ),
        source_ref="future-solver-interface:pending-native-transfer-output",
    )


def _reject_forbidden_claim_language(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(term in key_text for term in _FORBIDDEN_CLAIM_TERMS):
                raise ValueError(f"{path}.{key} contains forbidden claim language")
            _reject_forbidden_claim_language(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _reject_forbidden_claim_language(item, path=f"{path}[{idx}]")
        return
    if isinstance(value, str):
        text = value.lower()
        if any(term in text for term in _FORBIDDEN_CLAIM_TERMS):
            raise ValueError(f"{path} contains forbidden claim language")


__all__ = [
    "NativeLowEllObservableSchema",
    "NativeLowEllSchema",
    "NativeSchemaTransferFunctionSpec",
    "default_native_lowell_schema",
]
