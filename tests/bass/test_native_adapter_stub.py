from __future__ import annotations

import pytest

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferSource,
    validate_transfer_dependent_result,
)


def test_default_native_schema_exports_provisional_specs_without_values() -> None:
    from bass.transfer.native_schema import default_native_lowell_schema

    schema = default_native_lowell_schema()
    registry = schema.to_transfer_registry()
    spec = registry.get("native.lowell.alm_T.v1")
    metadata = schema.to_metadata()

    assert schema.schema_status == "schema_only_no_solver_output"
    assert metadata["native_solver_result"] is False
    assert metadata["returns_values"] is False
    assert metadata["consumable_as_result"] is False
    assert metadata["adapter_scope"] == "future_native_lowell"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["production_status"] == "schema_only"
    assert metadata["artifact_manifest_schema"]["owner"] == "BASS"
    assert metadata["artifact_manifest_schema"]["config_hash"].endswith("no_values")
    assert metadata["output_split_schema"] == {
        "alm_det": "required_future_field_no_values",
        "alm_stoch": "required_future_field_no_values",
        "alm_boost": "required_future_field_no_values",
    }
    assert metadata["gate_status_schema"]["family_backend_status"].endswith(
        "no_value"
    )
    assert metadata["family_identification_status"] == (
        "blocked_pre_native_morphology_atlas"
    )
    assert metadata["morphology_atlas_status"] == "absent"
    assert metadata["observables"][0]["name"] == "alm_T"
    assert metadata["observables"][0]["split_descriptors"] == [
        "det",
        "stoch",
        "boost",
    ]
    assert "values" not in metadata
    assert spec.source is TransferSource.BASS_NATIVE_PROVISIONAL
    assert spec.calibration_status is CalibrationStatus.NATIVE_PROVISIONAL
    assert spec.observable_kind is ObservableKind.TEMPERATURE
    assert spec.passed_validation_gates == ()
    assert spec.to_metadata()["schema_status"] == "schema_only_no_solver_output"
    assert spec.to_metadata()["consumable_as_result"] is False
    with pytest.raises(ValueError, match="schema-only"):
        validate_transfer_dependent_result(spec.to_metadata())


def test_native_adapter_stub_never_returns_fake_solver_values() -> None:
    from bass.transfer.native_adapter import default_native_lowell_adapter_stub

    adapter = default_native_lowell_adapter_stub()
    metadata = adapter.metadata()

    assert metadata["native_solver_result"] is False
    assert metadata["returns_values"] is False
    assert metadata["production_status"] == "schema_only"
    assert "values" not in metadata
    with pytest.raises(NotImplementedError, match="future low-ell solver artifact"):
        adapter.evaluate("native.lowell.alm_T.v1")
    with pytest.raises(NotImplementedError, match="future low-ell solver artifact"):
        adapter.solve()
    with pytest.raises(NotImplementedError, match="future low-ell solver artifact"):
        adapter.load_solver_output("memory://future-output")
    with pytest.raises(NotImplementedError, match="future low-ell solver artifact"):
        adapter("native.lowell.temperature_alm.v1")


def test_native_schema_validates_observable_descriptors() -> None:
    from bass.transfer.native_schema import NativeLowEllObservableSchema

    descriptor = NativeLowEllObservableSchema(
        name="temperature_alm",
        observable_kind="temperature",
        channels=("TT",),
        ell_min=2,
        ell_max=32,
        coefficient_space="alm",
        normalization="dimensionless_delta_t_over_t",
        units="dimensionless",
        convention_ref="obsstat.alm_conventions.temperature.v1",
    )

    assert descriptor.observable_kind is ObservableKind.TEMPERATURE
    assert descriptor.to_metadata()["channels"] == ["TT"]
    assert descriptor.to_metadata()["harmonic_ordering"].startswith("dense_full")

    with pytest.raises(ValueError, match="channels"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=(),
            ell_min=2,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
        )
    with pytest.raises(ValueError, match="non-string sequence"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels="TT",
            ell_min=2,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
        )
    with pytest.raises(ValueError, match="ell_min"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=("TT",),
            ell_min=0,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
        )
    with pytest.raises(ValueError, match="coefficient_space"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=("TT",),
            ell_min=2,
            ell_max=32,
            coefficient_space="posterior_map",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
        )
    with pytest.raises(ValueError, match="split_descriptors"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=("TT",),
            ell_min=2,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
            split_descriptors=("total",),
        )
    with pytest.raises(ValueError, match="covariance_status"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=("TT",),
            ell_min=2,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
            covariance_status="",
        )
    with pytest.raises(ValueError, match="mask_status"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=("TT",),
            ell_min=2,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
            mask_status="",
        )
    with pytest.raises(ValueError, match="harmonic_ordering"):
        NativeLowEllObservableSchema(
            name="bad",
            observable_kind="temperature",
            channels=("TT",),
            ell_min=2,
            ell_max=32,
            coefficient_space="alm",
            normalization="dimensionless",
            units="dimensionless",
            convention_ref="obsstat",
            harmonic_ordering="",
        )

    from bass.transfer.native_schema import NativeLowEllSchema
    from common.transfer_registry import TransferValidRange

    for schema_ell_min, schema_ell_max in ((2, 10), (4, 32)):
        with pytest.raises(ValueError, match="within the schema valid_range"):
            NativeLowEllSchema(
                transfer_id_prefix="native.lowell",
                family="future_native_lowell_schema",
                valid_range=TransferValidRange(
                    k_min=1.0e-5,
                    k_max=0.2,
                    ell_min=schema_ell_min,
                    ell_max=schema_ell_max,
                ),
                observables=(descriptor,),
                source_ref="future-solver-interface:pending",
            )


def test_native_schema_rejects_validated_or_claim_like_language() -> None:
    from bass.transfer.native_schema import (
        NativeLowEllObservableSchema,
        NativeLowEllSchema,
    )
    from common.transfer_registry import TransferValidRange

    descriptor = NativeLowEllObservableSchema(
        name="temperature_alm",
        observable_kind="temperature",
        channels=("TT",),
        ell_min=2,
        ell_max=32,
        coefficient_space="alm",
        normalization="dimensionless_delta_t_over_t",
        units="dimensionless",
        convention_ref="obsstat.alm_conventions.temperature.v1",
    )

    with pytest.raises(ValueError, match="forbidden claim language"):
        NativeLowEllSchema(
            transfer_id_prefix="native.lowell",
            family="future identified family",
            valid_range=TransferValidRange(
                k_min=1.0e-5,
                k_max=0.2,
                ell_min=2,
                ell_max=32,
            ),
            observables=(descriptor,),
            source_ref="external-native-solver:future",
        )
    with pytest.raises(ValueError, match="provisional"):
        NativeLowEllSchema(
            transfer_id_prefix="native.lowell",
            family="future_native_lowell_schema",
            valid_range=TransferValidRange(
                k_min=1.0e-5,
                k_max=0.2,
                ell_min=2,
                ell_max=32,
            ),
            observables=(descriptor,),
            source_ref="external-native-solver:future",
            calibration_status="native_validated",
        )


def test_native_and_external_transfer_registries_can_coexist() -> None:
    from bass.transfer.native_schema import default_native_lowell_schema
    from bass.transfer.registry import default_external_transfer_registry

    native_ids = {
        spec.transfer_id
        for spec in default_native_lowell_schema().to_transfer_registry().all()
    }
    external_ids = {
        spec.transfer_id for spec in default_external_transfer_registry().all()
    }

    assert native_ids
    assert external_ids
    assert native_ids.isdisjoint(external_ids)


def test_transfer_package_exports_native_stub_surface() -> None:
    from bass.transfer import (
        FutureNativeLowEllAdapterStub,
        NativeLowEllObservableSchema,
        NativeLowEllSchema,
        default_native_lowell_adapter_stub,
        default_native_lowell_schema,
    )

    assert FutureNativeLowEllAdapterStub.__name__ == "FutureNativeLowEllAdapterStub"
    assert NativeLowEllObservableSchema.__name__ == "NativeLowEllObservableSchema"
    assert NativeLowEllSchema.__name__ == "NativeLowEllSchema"
    assert default_native_lowell_schema().schema_status == "schema_only_no_solver_output"
    assert (
        default_native_lowell_adapter_stub().metadata()["production_status"]
        == "schema_only"
    )
