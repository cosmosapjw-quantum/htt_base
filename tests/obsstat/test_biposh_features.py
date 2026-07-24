from __future__ import annotations

import ast
import importlib

import pytest

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    SkySupport,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="obsstat.test.biposh",
        artifact_path="memory://obsstat/biposh",
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.biposh_features.v1",
        caveats=["diagnostic feature extraction only"],
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="none",
        sky_support_hash="sha256:sky",
        mask_hash="sha256:mask",
        mock_coverage_status="not_statistical",
        coordinate_frame="galactic",
        sky_fraction=1.0,
        completeness_status="full_sky_synthetic",
        pixelization="none",
    )


def _convention():
    from htt.obsstat.alm_conventions import canonical_temperature_alm_convention
    from htt.obsstat.biposh_features import BiPoSHConventionMetadata

    return BiPoSHConventionMetadata(
        alm_convention=canonical_temperature_alm_convention(lmax=4),
        rotation_metadata={
            "rotation_group": "SO3",
            "component_index": "M",
            "norm_invariant_under": "unitary_M_basis_rotation",
            "wigner_convention": "real_components_not_used",
        },
    )


def _entries():
    from htt.obsstat.biposh_features import SparseBiPoSHCoefficient

    return (
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=2,
            ell2=2,
            L=2,
            M=0,
            value=3.0,
        ),
        SparseBiPoSHCoefficient(
            channel_pair=("T", "E"),
            ell1=2,
            ell2=3,
            L=2,
            M=1,
            value=4.0,
        ),
        SparseBiPoSHCoefficient(
            channel_pair=("E", "E"),
            ell1=2,
            ell2=3,
            L=2,
            M=-1,
            value=1.0,
        ),
    )


def _feature(**overrides):
    from htt.obsstat.biposh_features import build_biposh_feature_payload

    kwargs = {
        "entries": _entries(),
        "convention": _convention(),
        "sky_support_status": "full_sky_synthetic",
        "mask_status": "unmasked_synthetic",
        "beam_status": "beam_not_applied_synthetic",
        "systematic_status": "systematics_not_injected_synthetic",
        "covariance_status": "sparse_biposh_coefficients_supplied",
        "null_mock_status": "not_supplied",
        "threshold": 0.0,
        "config_hash": "sha256:biposh-config",
        "input_hashes": ("sha256:biposh-input",),
        "generating_command": "python -m pytest tests/obsstat/test_biposh_features.py -q",
        "worktree_state": "test-clean",
    }
    kwargs.update(overrides)
    return build_biposh_feature_payload(**kwargs)


def test_biposh_payload_emits_rotation_aware_norms_and_metadata() -> None:
    payload = _feature()

    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["statistic_role"] == "feature_only"
    assert payload["model_role"] == "not_model_input"
    assert payload["transfer_source"] == "none"
    assert payload["config_hash"] == "sha256:biposh-config"
    assert payload["input_hashes"] == ["sha256:biposh-input"]
    assert payload["generating_command"].startswith("python -m pytest")
    assert payload["worktree_state"] == "test-clean"

    convention = payload["convention_metadata"]
    assert convention["alm_convention"]["basis"] == "complex_spherical_harmonic"
    assert convention["alm_convention"]["normalization"] == "orthonormal_4pi"
    assert convention["alm_convention"]["coordinate_frame"] == "galactic"
    assert convention["rotation_metadata"]["rotation_group"] == "SO3"
    assert convention["rotation_metadata"]["component_index"] == "M"

    norms = payload["norm_summary"]
    assert norms["rotation_aware_norm_definition"] == "sqrt(sum_M |A_l1_l2^LM|^2)"
    assert norms["total_power"] == pytest.approx(26.0)
    assert norms["total_norm"] == pytest.approx(26.0 ** 0.5)
    assert norms["by_L"]["2"]["power"] == pytest.approx(26.0)
    assert norms["by_L"]["2"]["norm"] == pytest.approx(26.0 ** 0.5)
    assert norms["by_L_l1_l2"]["2:2:2"]["power"] == pytest.approx(9.0)
    assert norms["by_L_l1_l2"]["2:2:3"]["power"] == pytest.approx(17.0)
    assert norms["by_channel_L_l1_l2"]["T:E:2:2:3"]["power"] == pytest.approx(16.0)
    assert norms["by_channel_L_l1_l2"]["E:E:2:2:3"]["power"] == pytest.approx(1.0)
    assert payload["sparse_index_policy"]["duplicate_policy"] == "reject"
    assert payload["sparse_index_policy"]["ordering"] == "canonical_sorted"
    assert payload["mask_status"] == "unmasked_synthetic"
    assert payload["beam_status"] == "beam_not_applied_synthetic"
    assert payload["systematic_status"] == "systematics_not_injected_synthetic"
    assert payload["claim_status"]["family_status"] == "blocked_pre_native_atlas"
    assert payload["claim_status"]["inference_status"] == "not_model_input"


def test_sparse_entries_are_order_invariant_for_hashes_and_norms() -> None:
    first = _feature(entries=_entries())
    second = _feature(entries=tuple(reversed(_entries())))

    assert first["entry_hash"] == second["entry_hash"]
    assert first["entries"] == second["entries"]
    assert first["norm_summary"] == second["norm_summary"]


def test_rotation_metadata_is_required_for_rotation_aware_norms() -> None:
    from htt.obsstat.alm_conventions import canonical_temperature_alm_convention
    from htt.obsstat.biposh_features import BiPoSHConventionMetadata

    with pytest.raises(ValueError, match="rotation_metadata"):
        BiPoSHConventionMetadata(
            alm_convention=canonical_temperature_alm_convention(lmax=4),
            rotation_metadata={},
        )
    with pytest.raises(ValueError, match="rotation_group"):
        BiPoSHConventionMetadata(
            alm_convention=canonical_temperature_alm_convention(lmax=4),
            rotation_metadata={
                "component_index": "M",
                "norm_invariant_under": "unitary_M_basis_rotation",
            },
        )
    with pytest.raises(ValueError, match="rotation_group"):
        BiPoSHConventionMetadata(
            alm_convention=canonical_temperature_alm_convention(lmax=4),
            rotation_metadata={
                "rotation_group": "",
                "component_index": "M",
                "norm_invariant_under": "unitary_M_basis_rotation",
            },
        )
    with pytest.raises(ValueError, match="norm_invariant_under"):
        BiPoSHConventionMetadata(
            alm_convention=canonical_temperature_alm_convention(lmax=4),
            rotation_metadata={
                "rotation_group": "SO3",
                "component_index": "M",
                "norm_invariant_under": "",
            },
        )


def test_sparse_entries_reject_duplicate_nonfinite_and_invalid_indices() -> None:
    from htt.obsstat.biposh_features import SparseBiPoSHCoefficient

    duplicate = (
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=2,
            ell2=2,
            L=2,
            M=0,
            value=1.0,
        ),
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=2,
            ell2=2,
            L=2,
            M=0,
            value=2.0,
        ),
    )
    with pytest.raises(ValueError, match="duplicate sparse BiPoSH index"):
        _feature(entries=duplicate)
    with pytest.raises(ValueError, match="finite"):
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=2,
            ell2=2,
            L=2,
            M=0,
            value=float("nan"),
        )
    with pytest.raises(ValueError, match="non-negative"):
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=-1,
            ell2=2,
            L=2,
            M=0,
            value=1.0,
        )
    with pytest.raises(ValueError, match="abs\\(M\\) <= L"):
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=2,
            ell2=2,
            L=2,
            M=3,
            value=1.0,
        )
    with pytest.raises(ValueError, match="triangle"):
        SparseBiPoSHCoefficient(
            channel_pair=("T", "T"),
            ell1=0,
            ell2=0,
            L=2,
            M=0,
            value=1.0,
        )
    with pytest.raises(ValueError, match="alm_convention lmax"):
        _feature(
            entries=(
                SparseBiPoSHCoefficient(
                    channel_pair=("T", "T"),
                    ell1=8,
                    ell2=8,
                    L=2,
                    M=0,
                    value=1.0,
                ),
            )
        )


def test_thresholding_is_explicit_and_records_discarded_entries() -> None:
    payload = _feature(threshold=3.5)

    assert payload["threshold_policy"]["absolute_value_threshold"] == pytest.approx(3.5)
    assert payload["threshold_policy"]["retained_count"] == 1
    assert payload["threshold_policy"]["discarded_count"] == 2
    assert payload["norm_summary"]["total_power"] == pytest.approx(16.0)
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["abs_value"] == pytest.approx(4.0)
    assert payload["threshold_policy"]["discarded_power"] == pytest.approx(10.0)
    assert payload["threshold_policy"]["max_discarded_abs_value"] == pytest.approx(3.0)
    assert payload["threshold_policy"]["discarded_entry_hash"].startswith("sha256:")


def test_mask_beam_and_systematic_caveat_hooks_are_required() -> None:
    for field_name in ("mask_status", "beam_status", "systematic_status"):
        with pytest.raises(ValueError, match=field_name):
            _feature(**{field_name: ""})
    payload = _feature()
    assert payload["caveat_hooks"]["mask_status"] == "unmasked_synthetic"
    assert payload["caveat_hooks"]["beam_status"] == "beam_not_applied_synthetic"
    assert (
        payload["caveat_hooks"]["systematic_status"]
        == "systematics_not_injected_synthetic"
    )
    assert any("mask/beam/systematic" in caveat for caveat in payload["caveats"])


def test_biposh_payload_integrates_with_observable_vector_without_branch_collapse() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    payload = _feature()
    vector = build_observable_vector(
        ell_max=4,
        channels=("TT", "BiPoSH"),
        biposh_features={"biposh_sparse": payload},
        manifest=_manifest(),
        sky_support=_sky_support(),
    )

    assert vector.biposh["biposh_sparse"]["norm_summary"]["total_norm"] == pytest.approx(26.0 ** 0.5)
    assert vector.template_fit is None
    assert vector.covariance_features is None


def test_nonzero_biposh_rejects_family_geometry_or_inference_claims() -> None:
    from htt.obsstat.biposh_features import BiPoSHFeatureSummary

    forbidden_phrase = " ".join(("family", "identified", "by", "BiPoSH"))
    base = {
        "entries": _entries(),
        "convention": _convention(),
        "sky_support_status": "full_sky_synthetic",
        "mask_status": "unmasked_synthetic",
        "beam_status": "beam_not_applied_synthetic",
        "systematic_status": "systematics_not_injected_synthetic",
        "covariance_status": "sparse_biposh_coefficients_supplied",
        "null_mock_status": "not_supplied",
        "config_hash": "sha256:biposh-config",
        "input_hashes": ("sha256:biposh-input",),
        "generating_command": "python -m pytest tests/obsstat/test_biposh_features.py -q",
        "worktree_state": "test-clean",
    }
    for field_name, value in (
        ("source_metadata", {"posterior_odds": 1.0}),
        ("source_metadata", {"nested": [{"posterior_odds": 1.0}]}),
        ("source_metadata", {"family_rank": ["VII_h"]}),
        ("source_metadata", {"geometry_detected": True}),
        ("caveats", (forbidden_phrase,)),
    ):
        with pytest.raises(ValueError, match="forbidden claim language"):
            BiPoSHFeatureSummary(**{**base, field_name: value})


def test_transfer_derived_features_require_valid_transfer_metadata() -> None:
    with pytest.raises(ValueError, match="transfer metadata"):
        _feature(transfer_metadata={"transfer_source": "none"})

    payload = _feature(
        transfer_metadata={
            "transfer_source": "external_transfer",
            "family": "external-template",
            "valid_range": {
                "k_min": 1.0e-4,
                "k_max": 0.2,
                "ell_min": 2,
                "ell_max": 4,
            },
            "observable_kind": "biposh",
            "normalization": "unit_norm",
            "calibration_status": "external_calibrated",
            "caveats": ["external transfer metadata for obsstat packaging test"],
        },
    )

    assert payload["transfer_derived"] is True
    assert payload["transfer_source"] == "external_transfer"
    assert payload["transfer_metadata"]["observable_kind"] == "biposh"
    assert payload["transfer_caveats"] == [
        "external transfer metadata for obsstat packaging test"
    ]
    assert any("mask/beam/systematic" in caveat for caveat in payload["caveats"])


def test_transfer_metadata_cannot_overwrite_obsstat_payload_fields() -> None:
    metadata = {
        "transfer_source": "external_transfer",
        "family": "external-template",
        "valid_range": {
            "k_min": 1.0e-4,
            "k_max": 0.2,
            "ell_min": 2,
            "ell_max": 4,
        },
        "observable_kind": "biposh",
        "normalization": "unit_norm",
        "calibration_status": "external_calibrated",
        "caveats": ["external transfer metadata for obsstat packaging test"],
        "owner": "HTT",
        "claim_tier": "validated",
        "model_role": "model_input",
    }

    with pytest.raises(ValueError, match="protected payload field"):
        _feature(transfer_metadata=metadata)


def test_transfer_metadata_caveats_are_claim_guarded() -> None:
    phrase = " ".join(("family", "identified", "by", "transfer", "metadata"))
    metadata = {
        "transfer_source": "external_transfer",
        "family": "external-template",
        "valid_range": {
            "k_min": 1.0e-4,
            "k_max": 0.2,
            "ell_min": 2,
            "ell_max": 4,
        },
        "observable_kind": "biposh",
        "normalization": "unit_norm",
        "calibration_status": "external_calibrated",
        "caveats": [phrase],
    }

    with pytest.raises(ValueError, match="forbidden claim language"):
        _feature(transfer_metadata=metadata)


def test_biposh_exports_and_import_boundaries() -> None:
    from htt.obsstat import (
        BiPoSHConventionMetadata,
        BiPoSHFeatureSummary,
        SparseBiPoSHCoefficient,
        build_biposh_feature_payload,
    )
    from htt.obsstat.biposh_features import BiPoSHFeatureSummary as ModuleSummary

    assert BiPoSHFeatureSummary is ModuleSummary
    assert BiPoSHConventionMetadata is not None
    assert SparseBiPoSHCoefficient is not None
    assert build_biposh_feature_payload is not None

    from obsstat import BiPoSHFeatureSummary as TopLevelSummary

    assert TopLevelSummary is ModuleSummary

    module = importlib.import_module("htt.obsstat.biposh_features")
    assert module.BiPoSHFeatureSummary is ModuleSummary

    source_path = "htt/obsstat/biposh_features.py"
    tree = ast.parse(open(source_path, encoding="utf-8").read())
    forbidden_roots = (
        "htt.htt",
        "htt.infer",
        "htt.likelihood",
        "mio",
        "bass.transfer.native_adapter",
        "bass.transfer.native_schema",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert not node.module.startswith(forbidden_roots)
