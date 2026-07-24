from __future__ import annotations

from importlib import import_module

import pytest

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferSource,
    TransferValidRange,
    validate_transfer_dependent_result,
)


def test_default_registry_records_external_and_empirical_transfer_sources() -> None:
    from bass.transfer.registry import default_external_transfer_registry

    registry = default_external_transfer_registry()

    assert registry.get("aniclass.lowell.f2_vector.v1").source is (
        TransferSource.ANICLASS_EXTERNAL
    )
    assert registry.get("aniclass.lowell.shear_to_D2.v1").observable_kind is (
        ObservableKind.TEMPERATURE
    )
    assert registry.get("bass.empirical_proxy.shear_to_D2.v1").source is (
        TransferSource.EMPIRICAL_PROXY
    )
    assert registry.get("bass.empirical_proxy.shear_to_D2.v1").calibration_status is (
        CalibrationStatus.EMPIRICAL_PROXY
    )


def test_adapter_records_transfer_conditional_metadata_not_native() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    adapters = default_external_transfer_adapter_registry()
    adapter = adapters.get("aniclass.lowell.shear_to_D2.v1")

    metadata = adapter.metadata()

    validate_transfer_dependent_result(metadata)
    assert metadata["transfer_source"] == "AniCLASS_external"
    assert metadata["claim_tier"] == "conditional"
    assert metadata["production_status"] == "diagnostic_only"
    assert metadata["transfer_conditional"] is True
    assert metadata["native_solver_result"] is False
    assert metadata["implementation_scope"] == "bass_py"
    assert metadata["callable_path"] == "htt.core.evidence_models_R03a:shear_to_D2"
    assert metadata["callable_input_domain"] == {
        "Sigma2_min": 1.0e-24,
        "Sigma2_max": 1.0e-20,
        "Sigma2_note": "legacy Saadeh-linear-regime external calibration window",
        "x_h_min": 0.001,
        "x_h_max": 1000.0,
        "x_h_note": "explicit x_h values use the AniCLASS interpolation domain",
    }
    assert "callable input domain" in str(metadata["valid_range_role"])
    assert "transfer-conditional result" in metadata["caveats"]
    assert any("not family identification" in caveat for caveat in metadata["caveats"])
    assert not metadata["passed_validation_gates"]


def test_adapter_evaluation_wraps_legacy_value_with_provenance() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    evaluation = default_external_transfer_adapter_registry().evaluate(
        "aniclass.lowell.shear_to_D2.v1",
        1.0e-22,
    )

    assert evaluation.value > 0.0
    assert evaluation.transfer_metadata["transfer_source"] == "AniCLASS_external"
    assert evaluation.claim_tier == "conditional"
    assert evaluation.transfer_conditional is True
    assert evaluation.native_solver_result is False
    validate_transfer_dependent_result(evaluation.transfer_metadata)


def test_adapter_evaluation_matches_referenced_legacy_callable() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    adapters = default_external_transfer_adapter_registry()

    cases = {
        "aniclass.lowell.f2_vector.v1": (0.2,),
        "aniclass.lowell.f2_tensor.v1": (0.2,),
        "aniclass.lowell.f3_vector.v1": (0.2,),
        "aniclass.lowell.f3_tensor.v1": (0.2,),
        "aniclass.lowell.shear_to_D2.v1": (1.0e-22,),
        "aniclass.lowell.shear_to_D3.v1": (1.0e-22,),
        "bass.empirical_proxy.shear_to_D2.v1": (1.0e-8,),
    }
    for transfer_id, args in cases.items():
        adapter = adapters.get(transfer_id)
        module_name, function_name = adapter.callable_path.split(":", 1)
        legacy_callable = getattr(import_module(module_name), function_name)

        evaluation = adapter.evaluate(*args)

        assert evaluation.value == pytest.approx(legacy_callable(*args))
        validate_transfer_dependent_result(evaluation.transfer_metadata)


def test_empirical_proxy_evaluation_stays_separate_from_aniclass_external() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    adapters = default_external_transfer_adapter_registry()
    external = adapters.evaluate("aniclass.lowell.shear_to_D2.v1", 1.0e-22)
    proxy = adapters.evaluate("bass.empirical_proxy.shear_to_D2.v1", 1.0e-8)

    assert external.transfer_metadata["transfer_source"] == "AniCLASS_external"
    assert proxy.transfer_metadata["transfer_source"] == "empirical_proxy"
    assert external.transfer_metadata["transfer_id"] != proxy.transfer_metadata[
        "transfer_id"
    ]
    assert proxy.transfer_metadata["calibration_status"] == "empirical_proxy"
    assert proxy.native_solver_result is False


def test_adapter_registry_covers_current_legacy_transfer_functions() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    adapters = default_external_transfer_adapter_registry()

    assert set(adapters.transfer_ids()) == {
        "aniclass.lowell.f2_vector.v1",
        "aniclass.lowell.f2_tensor.v1",
        "aniclass.lowell.f3_vector.v1",
        "aniclass.lowell.f3_tensor.v1",
        "aniclass.lowell.shear_to_D2.v1",
        "aniclass.lowell.shear_to_D3.v1",
        "bass.empirical_proxy.shear_to_D2.v1",
    }


def test_adapter_refuses_native_transfer_specs() -> None:
    from bass.transfer.aniclass_adapter import ExternalTransferAdapter

    base_payload = {
        "transfer_id": "native.fake.lowell.v1",
        "family": "BianchiVIIh_external_calibration",
        "valid_range": TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=3,
        ),
        "observable_kind": "temperature",
        "normalization": "unit_shear_to_microkelvin_squared",
        "caveats": ("native test fixture",),
        "source_ref": "native:test",
    }
    native_spec = TransferFunctionSpec(
        **base_payload,
        source="BASS_native_validated",
        calibration_status="native_validated",
        passed_validation_gates=("native_transfer_validated",),
    )

    with pytest.raises(ValueError, match="cannot wrap native"):
        ExternalTransferAdapter(
            transfer_spec=native_spec,
            callable_path="htt.core.evidence_models_R03a:shear_to_D2",
        )

    none_payload = dict(base_payload)
    none_payload["transfer_id"] = "none.fake.lowell.v1"
    none_spec = TransferFunctionSpec(
        **none_payload,
        source="none",
        calibration_status="none",
    )
    with pytest.raises(ValueError, match="external or empirical_proxy"):
        ExternalTransferAdapter(
            transfer_spec=none_spec,
            callable_path="htt.core.evidence_models_R03a:shear_to_D2",
        )


def test_adapter_fails_closed_for_malformed_callable_path() -> None:
    from bass.transfer.aniclass_adapter import ExternalTransferAdapter
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")

    with pytest.raises(ValueError, match="callable_path"):
        ExternalTransferAdapter(transfer_spec=spec, callable_path="not_a_path")

    with pytest.raises(AttributeError):
        ExternalTransferAdapter(
            transfer_spec=spec,
            callable_path="htt.core.evidence_models_R03a:missing_function",
        ).evaluate(1.0e-8)

    with pytest.raises(TypeError, match="does not resolve to a callable"):
        ExternalTransferAdapter(
            transfer_spec=spec,
            callable_path="htt.core.evidence_models_R03a:T0",
        ).evaluate(1.0e-8)


def test_adapter_fails_closed_outside_declared_input_domain() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    adapters = default_external_transfer_adapter_registry()

    with pytest.raises(ValueError, match="x_h.*outside"):
        adapters.evaluate("aniclass.lowell.f2_vector.v1", 1.0e-4)
    with pytest.raises(ValueError, match="Sigma2.*outside"):
        adapters.evaluate("aniclass.lowell.shear_to_D2.v1", 1.0e-8)
    with pytest.raises(ValueError, match="x_h.*outside"):
        adapters.evaluate(
            "aniclass.lowell.shear_to_D2.v1",
            1.0e-22,
            x_h=1.0e12,
        )
    with pytest.raises(ValueError, match="x_h.*outside"):
        adapters.evaluate(
            "aniclass.lowell.shear_to_D2.v1",
            1.0e-22,
            "decay",
            1.0e12,
        )
    with pytest.raises(ValueError, match="Sigma2.*outside"):
        adapters.evaluate("bass.empirical_proxy.shear_to_D2.v1", 1.0e-12)


def test_adapter_input_domain_supports_one_sided_ranges() -> None:
    from bass.transfer.aniclass_adapter import ExternalTransferAdapter
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")
    adapter = ExternalTransferAdapter(
        transfer_spec=spec,
        callable_path="htt.core.evidence_models_R03a:shear_to_D2",
        parameter_range={"Sigma2_min": 1.0e-24},
    )

    assert adapter.evaluate(1.0e-22).value > 0.0
    with pytest.raises(ValueError, match="Sigma2.*outside"):
        adapter.evaluate(1.0e-25)


def test_adapter_input_domain_rejects_bad_bounds() -> None:
    from bass.transfer.aniclass_adapter import ExternalTransferAdapter
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")
    adapter = ExternalTransferAdapter(
        transfer_spec=spec,
        callable_path="htt.core.evidence_models_R03a:shear_to_D2",
        parameter_range={"Sigma2_min": "not_numeric"},
    )

    with pytest.raises(ValueError, match="domain bound must be numeric"):
        adapter.evaluate(1.0e-22)


def test_adapter_metadata_blocks_external_as_native_spoofing() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    metadata = default_external_transfer_adapter_registry().get(
        "aniclass.lowell.shear_to_D2.v1"
    ).metadata()
    metadata["calibration_status"] = "native_validated"

    with pytest.raises(ValueError, match="external.*native"):
        validate_transfer_dependent_result(metadata)


def test_unknown_transfer_id_fails_closed() -> None:
    from bass.transfer.registry import default_external_transfer_adapter_registry

    adapters = default_external_transfer_adapter_registry()

    with pytest.raises(KeyError, match="unknown transfer_id"):
        adapters.get("missing.transfer")
    with pytest.raises(KeyError, match="unknown transfer_id"):
        adapters.evaluate("missing.transfer", 1.0e-8)
