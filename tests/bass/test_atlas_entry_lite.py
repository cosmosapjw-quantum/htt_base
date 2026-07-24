from __future__ import annotations

import dataclasses

import pytest

from common.transfer_registry import (
    CalibrationStatus,
    ObservableKind,
    TransferFunctionSpec,
    TransferSource,
    TransferValidRange,
    validate_transfer_dependent_result,
)


def test_default_side_by_side_atlas_entries_coexist_without_values() -> None:
    from bass.atlas import (
        AtlasEntryLite,
        build_default_transfer_side_by_side_comparison,
        validate_atlas_entry_lite_metadata,
    )

    comparison = build_default_transfer_side_by_side_comparison(
        git_commit_or_worktree_state="test-worktree-pr082",
    )
    metadata = comparison.to_metadata()

    assert comparison.entries
    assert any(entry.is_external_or_proxy for entry in comparison.entries)
    assert any(entry.is_future_native_schema for entry in comparison.entries)
    assert all(isinstance(entry, AtlasEntryLite) for entry in comparison.entries)
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["comparison_role"] == "transfer_provenance_side_by_side_only"
    assert metadata["consumable_as_observed_data"] is False
    assert metadata["consumable_as_posterior"] is False
    assert metadata["external_entry_count"] >= 1
    assert metadata["future_native_schema_entry_count"] >= 1
    assert len(set(metadata["transfer_ids"])) == len(metadata["transfer_ids"])
    assert "entries" in metadata
    for entry in comparison.entries:
        entry_metadata = entry.to_metadata()
        validate_atlas_entry_lite_metadata(entry_metadata)
        assert entry_metadata["atlas_entry_returns_values"] is False
        assert entry_metadata["family_label_role"].endswith("not_identification")
        assert entry_metadata["family_identification_status"] == (
            "blocked_pre_native_morphology_atlas"
        )
        assert "values" not in entry_metadata


def test_external_transfer_entry_preserves_conditional_transfer_metadata() -> None:
    from bass.atlas import AtlasEntryLite, validate_atlas_entry_lite_metadata
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")
    entry = AtlasEntryLite.from_transfer_spec(
        spec,
        comparison_group="pr082-test",
        config_hash="sha256:test-config",
        input_hashes=("sha256:external-registry",),
        generating_command="pytest pr082",
        git_commit_or_worktree_state="test-worktree-pr082",
    )
    metadata = entry.to_metadata()

    validate_atlas_entry_lite_metadata(metadata)
    validate_transfer_dependent_result(metadata["transfer_metadata"])
    assert entry.is_external_or_proxy
    assert metadata["transfer_source"] == "AniCLASS_external"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["transfer_metadata"]["claim_tier"] == "conditional"
    assert metadata["native_solver_result"] is False
    assert metadata["data_role"] == "metadata_only_not_measurement"
    assert metadata["inference_role"] == "not_model_dependent_inference_input"
    assert any("transfer-conditional" in caveat for caveat in metadata["caveats"])


def test_external_transfer_entry_rejects_status_overrides() -> None:
    from bass.atlas import AtlasEntryLite
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")
    cases = [
        ({"claim_tier": "C6_native_family_identification"}, "conditional"),
        ({"production_status": "production"}, "diagnostic_only"),
        ({"transfer_conditional": False}, "transfer-conditional"),
    ]
    for overrides, expected in cases:
        metadata = spec.to_metadata()
        metadata.update(overrides)
        with pytest.raises(ValueError, match=expected):
            AtlasEntryLite(
                entry_id="bad.external.status",
                comparison_group="pr082-test",
                transfer_metadata=metadata,
                config_hash="sha256:test-config",
                input_hashes=("sha256:external-registry",),
                generating_command="pytest pr082",
                git_commit_or_worktree_state="test-worktree-pr082",
            )


def test_future_native_entry_remains_schema_only_and_non_consumable() -> None:
    from bass.atlas import AtlasEntryLite, validate_atlas_entry_lite_metadata
    from bass.transfer.native_schema import default_native_lowell_schema

    spec = default_native_lowell_schema().to_transfer_spec("alm_T")
    entry = AtlasEntryLite.from_transfer_spec(
        spec,
        comparison_group="pr082-test",
        config_hash="sha256:test-config",
        input_hashes=("sha256:native-schema",),
        generating_command="pytest pr082",
        git_commit_or_worktree_state="test-worktree-pr082",
    )
    metadata = entry.to_metadata()

    validate_atlas_entry_lite_metadata(metadata)
    assert entry.is_future_native_schema
    assert metadata["transfer_source"] == "BASS_native_provisional"
    assert metadata["transfer_metadata"]["schema_status"] == (
        "schema_only_no_solver_output"
    )
    assert metadata["transfer_metadata"]["returns_values"] is False
    assert metadata["transfer_metadata"]["consumable_as_result"] is False
    with pytest.raises(ValueError, match="schema-only"):
        validate_transfer_dependent_result(metadata["transfer_metadata"])

    value_bearing_metadata = spec.to_metadata()
    value_bearing_metadata["alm_T"] = [0.0, 1.0]
    with pytest.raises(ValueError, match="cannot carry solver or observable values"):
        AtlasEntryLite(
            entry_id="bad.native.values",
            comparison_group="pr082-test",
            transfer_metadata=value_bearing_metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:native-schema",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )


def test_raw_native_schema_mapping_rejects_validation_spoofing() -> None:
    from bass.atlas import AtlasEntryLite
    from bass.transfer.native_schema import default_native_lowell_schema

    spec = default_native_lowell_schema().to_transfer_spec("alm_T")

    metadata = spec.to_metadata()
    metadata["calibration_status"] = "native_validated"
    with pytest.raises(ValueError, match="provisional"):
        AtlasEntryLite(
            entry_id="bad.native.validated",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:native-schema",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    metadata = spec.to_metadata()
    metadata["passed_validation_gates"] = ["native_transfer_validated"]
    with pytest.raises(ValueError, match="cannot carry gates"):
        AtlasEntryLite(
            entry_id="bad.native.gates",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:native-schema",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )


def test_atlas_entry_lite_rejects_consumption_as_observed_or_inference_input() -> None:
    from bass.atlas import build_default_transfer_side_by_side_comparison

    entry = build_default_transfer_side_by_side_comparison(
        git_commit_or_worktree_state="test-worktree-pr082",
    ).entries[0]

    with pytest.raises(RuntimeError, match="not observed data"):
        entry.to_observed_data()
    with pytest.raises(RuntimeError, match="not model-dependent inference input"):
        entry.to_posterior_input()
    with pytest.raises(RuntimeError, match="not HTT evidence"):
        entry.to_evidence_input()

    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.claim_tier = "conditional"  # type: ignore[misc]


def test_atlas_entry_lite_rejects_fake_native_or_active_roles() -> None:
    from bass.atlas import AtlasEntryLite
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")
    metadata = spec.to_metadata()
    metadata["native_solver_result"] = True

    with pytest.raises(ValueError, match="external transfer metadata"):
        AtlasEntryLite(
            entry_id="bad.external.native",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:external-registry",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    metadata = spec.to_metadata()
    metadata["posterior_weight"] = 0.5
    with pytest.raises(ValueError, match="active observed-data or inference"):
        AtlasEntryLite(
            entry_id="bad.posterior.role",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:external-registry",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    metadata = spec.to_metadata()
    metadata["mio_certificate"] = True
    with pytest.raises(ValueError, match="active observed-data or inference"):
        AtlasEntryLite(
            entry_id="bad.mio.certificate",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:external-registry",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    metadata = spec.to_metadata()
    metadata["role"] = "posterior_input"
    with pytest.raises(ValueError, match="active observed-data or inference"):
        AtlasEntryLite(
            entry_id="bad.posterior.value",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:external-registry",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )


def test_atlas_entry_lite_rejects_family_and_morphology_claim_phrases() -> None:
    from bass.atlas import AtlasEntryLite
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")

    metadata = spec.to_metadata()
    metadata["family"] = "VII_h family identified"
    with pytest.raises(ValueError, match="family-identification"):
        AtlasEntryLite(
            entry_id="bad.family.claim",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:external-registry",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    metadata = spec.to_metadata()
    metadata["caveats"] = ["morphology compatibility"]
    with pytest.raises(ValueError, match="morphology-compatibility"):
        AtlasEntryLite(
            entry_id="bad.morphology.claim",
            comparison_group="pr082-test",
            transfer_metadata=metadata,
            config_hash="sha256:test-config",
            input_hashes=("sha256:external-registry",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    metadata = spec.to_metadata()
    metadata["caveats"] = ["not morphology compatibility or family identification"]
    entry = AtlasEntryLite(
        entry_id="safe.downclaim",
        comparison_group="pr082-test",
        transfer_metadata=metadata,
        config_hash="sha256:test-config",
        input_hashes=("sha256:external-registry",),
        generating_command="pytest pr082",
        git_commit_or_worktree_state="test-worktree-pr082",
    )
    assert entry.transfer_source == "AniCLASS_external"


def test_metadata_validator_rejects_top_level_role_tampering() -> None:
    from bass.atlas import (
        build_default_transfer_side_by_side_comparison,
        validate_atlas_entry_lite_metadata,
    )

    entry = build_default_transfer_side_by_side_comparison(
        git_commit_or_worktree_state="test-worktree-pr082",
    ).entries[0]
    metadata = entry.to_metadata()

    bad_native = dict(metadata)
    bad_native["native_solver_result"] = True
    with pytest.raises(ValueError, match="native solver output"):
        validate_atlas_entry_lite_metadata(bad_native)

    bad_data = dict(metadata)
    bad_data["data_role"] = "observed_data"
    with pytest.raises(ValueError, match="data_role"):
        validate_atlas_entry_lite_metadata(bad_data)

    bad_inference = dict(metadata)
    bad_inference["inference_role"] = "posterior"
    with pytest.raises(ValueError, match="inference_role"):
        validate_atlas_entry_lite_metadata(bad_inference)

    bad_transfer_id = dict(metadata)
    bad_transfer_id["transfer_id"] = "aniclass.lowell.shear_to_D3.v1"
    with pytest.raises(ValueError, match="transfer_id must match"):
        validate_atlas_entry_lite_metadata(bad_transfer_id)

    bad_transfer_source = dict(metadata)
    bad_transfer_source["transfer_source"] = "BASS_native_provisional"
    with pytest.raises(ValueError, match="transfer_source must match"):
        validate_atlas_entry_lite_metadata(bad_transfer_source)

    projected_tampering = {
        "transfer_family": "forged_family",
        "observable_kind": "forged_observable",
        "normalization": "forged_normalization",
        "valid_range": {"ell_min": 999},
    }
    for field_name, forged_value in projected_tampering.items():
        tampered = dict(metadata)
        tampered[field_name] = forged_value
        with pytest.raises(ValueError, match=f"{field_name} must match"):
            validate_atlas_entry_lite_metadata(tampered)


def test_atlas_entry_lite_rejects_validated_native_or_none_source() -> None:
    from bass.atlas import AtlasEntryLite

    base = dict(
        transfer_id="native.fake.validated.v1",
        family="future_native_lowell_schema",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=32,
        ),
        observable_kind=ObservableKind.TEMPERATURE,
        normalization="dimensionless",
        caveats=("test fixture",),
        source_ref="pytest",
    )
    validated_native = TransferFunctionSpec(
        **base,
        source=TransferSource.BASS_NATIVE_VALIDATED,
        calibration_status=CalibrationStatus.NATIVE_VALIDATED,
        passed_validation_gates=("native_transfer_validated",),
    )
    with pytest.raises(ValueError, match="schema-only future native"):
        AtlasEntryLite.from_transfer_spec(
            validated_native,
            comparison_group="pr082-test",
            config_hash="sha256:test-config",
            input_hashes=("sha256:native-validated",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )

    none_spec = TransferFunctionSpec(
        **{**base, "transfer_id": "none.fake.v1"},
        source=TransferSource.NONE,
        calibration_status=CalibrationStatus.NONE,
    )
    with pytest.raises(ValueError, match="external/proxy"):
        AtlasEntryLite.from_transfer_spec(
            none_spec,
            comparison_group="pr082-test",
            config_hash="sha256:test-config",
            input_hashes=("sha256:none",),
            generating_command="pytest pr082",
            git_commit_or_worktree_state="test-worktree-pr082",
        )


def test_side_by_side_comparison_requires_external_and_native_members() -> None:
    from bass.atlas import AtlasTransferComparison, entries_from_transfer_registry
    from bass.transfer.registry import default_external_transfer_registry

    external_entries = entries_from_transfer_registry(
        default_external_transfer_registry(),
        comparison_group="external-only",
        config_hash="sha256:test-config",
        input_hashes=("sha256:external",),
        generating_command="pytest pr082",
        git_commit_or_worktree_state="test-worktree-pr082",
    )

    with pytest.raises(ValueError, match="future native schema"):
        AtlasTransferComparison(
            comparison_group="external-only",
            entries=external_entries,
        )


def test_default_builder_requires_worktree_state_metadata() -> None:
    from bass.atlas import build_default_transfer_side_by_side_comparison

    with pytest.raises(ValueError, match="git_commit_or_worktree_state"):
        build_default_transfer_side_by_side_comparison()
