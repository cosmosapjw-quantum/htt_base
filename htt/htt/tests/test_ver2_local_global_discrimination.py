from __future__ import annotations

import numpy as np

from common.contracts import ArtifactManifest, ObservableVector, SkySupport
from htt.infer.local_global_discrimination import (
    build_discrimination_matrix,
    build_discrimination_matrix_stub,
    default_response_library,
    whitened_inner_product,
)
from htt.nulls import (
    DepthBinSpec,
    LocalBoostDepthNull,
    LocalBoostNullConfig,
    build_local_boost_null_fpr_report,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.observable",
        artifact_path="artifacts/bass/observable.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["h1"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _observable(
    *,
    channels: tuple[str, ...],
    selection_mode: str = "mock_calibrated",
    mock_coverage_status: str = "adequate",
    template_fit: dict[str, object] | None = None,
    covariance_features: dict[str, object] | None = None,
) -> ObservableVector:
    return ObservableVector(
        ell_max=8,
        channels=channels,
        cl={"TT": [1.0, 0.5]},
        alm_features={"quadrupole_axis": {"l_deg": 264.0, "b_deg": 48.0}},
        biposh=None,
        template_fit=template_fit,
        covariance_features=covariance_features,
        scan_volume={"n_modes": 4},
        sky_support=SkySupport(
            selection_mode=selection_mode,
            sky_support_hash="sky123",
            mask_hash="mask123",
            mock_coverage_status=mock_coverage_status,
            scan_volume_hash="scan123",
        ),
        manifest=_manifest(),
    )


def _sha(char: str) -> str:
    return "sha256:" + char * 64


def _local_null_fpr_report():
    from htt.departure.response_overlap import build_response_overlap_audit

    config = LocalBoostNullConfig(
        n_mocks=32,
        seed=61061,
        depth_bins=(
            DepthBinSpec("near", 0.0, 0.025, 0.0, 100.0, response_weight=1.0),
            DepthBinSpec("mid", 0.025, 0.075, 100.0, 300.0, response_weight=0.5),
            DepthBinSpec("far", 0.075, 0.15, 300.0, 650.0, response_weight=0.2),
        ),
        target_direction=(1.0, 0.0, 0.0),
        gf_threshold=10.0,
        direction_threshold_deg=30.0,
        look_elsewhere_trials=1,
        sky_support_hash=_sha("1"),
        mask_hash=_sha("2"),
        scan_volume_hash=_sha("3"),
        config_hash=_sha("4"),
        input_hashes=(_sha("5"),),
        covariance_status="diagnostic_covariance_supplied",
        sky_support_status="pr040_sky_support_attached",
        generating_command="python -m pytest htt/htt/tests/test_ver2_local_global_discrimination.py -q",
        worktree_state="test-worktree",
    )
    audit = build_response_overlap_audit(
        local_boost_response=(1.0, 0.0),
        global_tilt_response=(0.0, 1.0),
        covariance=np.eye(2),
        observable_labels=("depth_coherence", "template_axis"),
        artifact_id="htt-response-overlap-local-global-fixture",
        artifact_path="memory://htt-response-overlap-local-global-fixture.json",
        input_hashes=(_sha("a"),),
        generating_command=config.generating_command,
        worktree_state=config.worktree_state,
        sky_support_status="pr040_sky_support_attached",
        mask_status="mask_hash_recorded",
        covariance_status="diagnostic_covariance_supplied",
        null_mock_status="rank_audit_without_null_fpr",
    )
    return build_local_boost_null_fpr_report(
        LocalBoostDepthNull(config).generate(),
        response_overlap_audit=audit,
    )


def test_local_boost_and_global_tilt_are_not_merged():
    lib = default_response_library()
    assert lib["local_boost"].physical_side == "observer_side"
    assert lib["global_tilt"].physical_side == "source_background_side"
    assert lib["local_boost"].amplitude_normalization != lib["global_tilt"].amplitude_normalization
    assert "flrw_isotropic_null" in lib
    assert "bianchi_geometry" in lib
    assert "systematic_template" in lib


def test_discrimination_matrix_stub_is_manifest_backed_and_not_posterior():
    matrix = build_discrimination_matrix_stub()
    assert matrix.manifest.owner == "HTT"
    assert matrix.manifest.production_status == "diagnostic_only"
    assert matrix.hypotheses == ("local_boost", "global_tilt")
    overlap = np.asarray(matrix.overlap_matrix)
    assert overlap.shape == (2, 2)
    assert overlap[0, 0] == 1.0
    assert matrix.claim_tier_by_pair["local_boost|global_tilt"] == "exploratory"


def test_whitened_inner_product_is_symmetric_and_normalized():
    left = np.asarray([1.0, 1.0, 0.0], dtype=float)
    right = np.asarray([1.0, 0.0, 1.0], dtype=float)
    noise = np.asarray([1.0, 2.0, 4.0], dtype=float)
    assert whitened_inner_product(left, right, noise) == whitened_inner_product(
        right, left, noise
    )
    assert whitened_inner_product(left, left, noise) > 0.0


def test_build_discrimination_matrix_does_not_promote_without_local_null_fpr():
    matrix = build_discrimination_matrix(
        _observable(
            channels=("TT", "TE", "EE", "BB", "BiPoSH", "template"),
            template_fit={"atlas_ref": "atlas-v1.json"},
            covariance_features={
                "representation": "low_ell_harmonic_sparse_basis",
                "basis_reduction_status": "low_ell_harmonic_sparse_basis",
                "local_global_degeneracy": {
                    "represented": True,
                    "status": "observer_source_discrimination_pending",
                    "distinguishing_observables": ("BiPoSH", "BB", "template"),
                },
            },
        )
    )
    pair = "global_tilt|local_boost"
    assert matrix.manifest.production_status == "diagnostic_only"
    assert matrix.manifest.claim_tier == "exploratory"
    assert matrix.claim_tier_by_pair[pair] == "exploratory"
    assert "local_boost_null_fpr_gate_not_satisfied" in matrix.manifest.caveats
    assert matrix.degeneracy_flags[pair] is False
    assert matrix.recommended_next_observable[pair] in {
        "depth_direction_coherence",
        "atlas_template_biposh",
        "null_mock_covariance",
    }
    stats = matrix.manifest.statistics_definitions
    assert stats["pair_claim_tier"][pair] == "exploratory"
    assert stats["pair_degeneracy_flags"][pair] is False
    assert pair not in stats["conditional_pairs"]
    assert stats["local_null_fpr_gate"]["allowed"] is False
    assert "local_boost_null_fpr_missing" in stats["local_null_fpr_gate"]["blocked_reasons"]
    assert stats["support_profile"]["template"] >= 0.75


def test_build_discrimination_matrix_promotes_with_matching_local_null_fpr():
    matrix = build_discrimination_matrix(
        _observable(
            channels=("TT", "TE", "EE", "BB", "BiPoSH", "template"),
            template_fit={"atlas_ref": "atlas-v1.json"},
            covariance_features={
                "representation": "low_ell_harmonic_sparse_basis",
                "basis_reduction_status": "low_ell_harmonic_sparse_basis",
                "local_global_degeneracy": {
                    "represented": True,
                    "status": "observer_source_discrimination_pending",
                    "distinguishing_observables": ("BiPoSH", "BB", "template"),
                },
            },
        ),
        local_null_fpr_report=_local_null_fpr_report(),
    )
    pair = "global_tilt|local_boost"
    assert matrix.manifest.production_status == "production_candidate"
    assert matrix.manifest.claim_tier == "conditional"
    assert matrix.claim_tier_by_pair[pair] == "conditional"
    stats = matrix.manifest.statistics_definitions
    assert stats["pair_claim_tier"][pair] == "conditional"
    assert stats["local_null_fpr_gate"]["allowed"] is True
    assert pair in stats["conditional_pairs"]


def test_build_discrimination_matrix_blocks_geometry_pair_without_morphology_support():
    matrix = build_discrimination_matrix(
        _observable(
            channels=("TT",),
            selection_mode="none",
            mock_coverage_status="pending",
            template_fit=None,
            covariance_features=None,
        ),
        hypotheses=("local_boost", "bianchi_geometry"),
    )
    pair = "bianchi_geometry|local_boost"
    assert matrix.manifest.production_status == "diagnostic_only"
    assert matrix.claim_tier_by_pair[pair] == "blocked"
    stats = matrix.manifest.statistics_definitions
    assert stats["pair_claim_tier"][pair] == "blocked"
    assert pair in stats["blocked_pairs"]
    assert stats["support_profile"]["template"] == 0.0
