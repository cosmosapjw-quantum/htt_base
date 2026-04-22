from __future__ import annotations

import numpy as np

from common.contracts import ArtifactManifest, ObservableVector, SkySupport
from htt.infer.local_global_discrimination import (
    build_discrimination_matrix,
    build_discrimination_matrix_stub,
    default_response_library,
    whitened_inner_product,
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


def test_build_discrimination_matrix_promotes_local_global_pair_with_morphology_support():
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
    assert matrix.manifest.production_status == "production_candidate"
    assert matrix.manifest.claim_tier == "conditional"
    assert matrix.claim_tier_by_pair[pair] == "conditional"
    assert matrix.degeneracy_flags[pair] is False
    assert matrix.recommended_next_observable[pair] in {
        "depth_direction_coherence",
        "atlas_template_biposh",
        "null_mock_covariance",
    }
    stats = matrix.manifest.statistics_definitions
    assert stats["pair_claim_tier"][pair] == "conditional"
    assert stats["pair_degeneracy_flags"][pair] is False
    assert pair in stats["conditional_pairs"]
    assert stats["support_profile"]["template"] >= 0.75


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
