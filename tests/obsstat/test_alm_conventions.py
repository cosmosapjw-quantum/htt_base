from __future__ import annotations

import pytest
import numpy as np

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    SkySupport,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="obsstat.test.alm_conventions",
        artifact_path="memory://obsstat/alm-conventions",
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.observable_vector.v1",
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


def test_canonical_temperature_convention_has_required_metadata() -> None:
    from htt.obsstat.alm_conventions import (
        REQUIRED_CONVENTION_FIELDS,
        canonical_temperature_alm_convention,
        validate_alm_convention_metadata,
    )

    convention = canonical_temperature_alm_convention(lmax=4, mmax=3)
    metadata = convention.to_metadata()

    assert set(REQUIRED_CONVENTION_FIELDS).issubset(metadata)
    assert metadata["basis"] == "complex_spherical_harmonic"
    assert metadata["normalization"] == "orthonormal_4pi"
    assert metadata["phase_convention"] == "condon_shortley_included"
    assert metadata["theta_phi_convention"] == "theta_colatitude_phi_longitude"
    assert metadata["harmonic_evaluator"] == "scipy.special.sph_harm_y"
    assert (
        metadata["evaluator_provenance"]
        == "scipy_sph_harm_y_docs_current_theta_colatitude_phi_longitude"
    )
    assert metadata["coordinate_frame"] == "galactic"
    assert metadata["alm_storage"] == "healpy_m_major_l_minor"
    assert metadata["reality_condition"] == "real_scalar_map"
    assert metadata["spin_weight"] == 0
    assert metadata["paired_map_order"] == "not_applicable"
    assert validate_alm_convention_metadata(metadata) == metadata


def test_convention_validation_rejects_missing_or_invalid_fields() -> None:
    from htt.obsstat.alm_conventions import (
        canonical_temperature_alm_convention,
        validate_alm_convention_metadata,
    )

    metadata = canonical_temperature_alm_convention(lmax=3).to_metadata()
    for field in (
        "reality_condition",
        "coordinate_frame",
        "normalization",
        "theta_phi_convention",
    ):
        broken = dict(metadata)
        del broken[field]
        with pytest.raises(ValueError, match=field):
            validate_alm_convention_metadata(broken)

    broken = dict(metadata)
    broken["normalization"] = "arbitrary_unit_norm"
    with pytest.raises(ValueError, match="normalization"):
        validate_alm_convention_metadata(broken)

    broken = dict(metadata)
    broken["posterior_odds"] = 3.0
    with pytest.raises(ValueError, match="unknown field"):
        validate_alm_convention_metadata(broken)

    broken = dict(metadata)
    broken["mmax"] = 4
    broken["lmax"] = 3
    with pytest.raises(ValueError, match="mmax"):
        validate_alm_convention_metadata(broken)


def test_convention_factory_rejects_non_integral_harmonic_indices() -> None:
    from dataclasses import replace

    from htt.obsstat.alm_conventions import (
        canonical_spin2_alm_convention,
        canonical_temperature_alm_convention,
    )

    with pytest.raises(ValueError, match="lmax must be an integer"):
        canonical_temperature_alm_convention(lmax=2.9)
    with pytest.raises(ValueError, match="mmax must be an integer"):
        canonical_temperature_alm_convention(lmax=3, mmax=1.9)
    with pytest.raises(ValueError, match="lmax must be an integer"):
        canonical_temperature_alm_convention(lmax=True)

    with pytest.raises(ValueError, match="spin_weight must be an integer"):
        replace(canonical_spin2_alm_convention(lmax=3), spin_weight=2.9)

    numpy_convention = canonical_temperature_alm_convention(
        lmax=np.int64(3),
        mmax=np.int64(2),
    )
    assert numpy_convention.to_metadata()["lmax"] == 3
    assert numpy_convention.to_metadata()["mmax"] == 2


def test_spin2_convention_requires_paired_spin_metadata() -> None:
    from htt.obsstat.alm_conventions import (
        canonical_spin2_alm_convention,
        validate_alm_convention_metadata,
    )

    metadata = canonical_spin2_alm_convention(lmax=4).to_metadata()

    assert metadata["basis"] == "spin_weighted_spherical_harmonic"
    assert metadata["spin_weight"] == 2
    assert metadata["spin_transform"] == "healpy_map2alm_spin"
    assert metadata["polarization_basis"] == "IAU_Q_U"
    assert metadata["paired_map_order"] == "Q_then_U"
    assert metadata["spin_output_convention"] == "healpy_return_pair_unlabeled_spin_alms"
    assert metadata["eb_sign_convention"] == "not_declared_no_eb_export"
    assert metadata["reality_condition"] == "spin_pair_q_u"
    assert validate_alm_convention_metadata(metadata) == metadata

    missing_basis = dict(metadata)
    missing_basis["polarization_basis"] = "not_applicable"
    with pytest.raises(ValueError, match="polarization_basis"):
        validate_alm_convention_metadata(missing_basis)

    missing_transform = dict(metadata)
    missing_transform["spin_transform"] = "not_applicable"
    with pytest.raises(ValueError, match="spin_transform"):
        validate_alm_convention_metadata(missing_transform)


def test_build_alm_feature_attaches_metadata_and_coefficient_hash() -> None:
    from htt.obsstat.alm_conventions import (
        build_alm_feature,
        canonical_temperature_alm_convention,
    )

    convention = canonical_temperature_alm_convention(lmax=1)
    feature = build_alm_feature(
        channel="T",
        coefficients=np.array([1.0, 0.25, -0.5]),
        convention=convention,
    )
    same_feature = build_alm_feature(
        channel="T",
        coefficients=[1.0, 0.25, -0.5],
        convention=convention,
    )
    changed_feature = build_alm_feature(
        channel="T",
        coefficients=[1.0, 0.25, -0.4],
        convention=convention,
    )

    assert feature["channel"] == "T"
    assert feature["claim_tier"] == "diagnostic_only"
    assert feature["convention_metadata"]["reality_condition"] == "real_scalar_map"
    assert feature["coefficient_hash"].startswith("sha256:")
    assert feature["coefficient_hash"] == same_feature["coefficient_hash"]
    assert feature["coefficient_hash"] != changed_feature["coefficient_hash"]


def test_build_alm_feature_rejects_storage_shape_mismatch() -> None:
    from htt.obsstat.alm_conventions import (
        build_alm_feature,
        canonical_spin2_alm_convention,
        canonical_temperature_alm_convention,
    )

    with pytest.raises(ValueError, match="must contain 6 entries"):
        build_alm_feature(
            channel="T",
            coefficients=[1.0, 0.0, 0.0],
            convention=canonical_temperature_alm_convention(lmax=2),
        )

    with pytest.raises(ValueError, match="pair of arrays"):
        build_alm_feature(
            channel="QU",
            coefficients=[[0.0] * 6],
            convention=canonical_spin2_alm_convention(lmax=2),
        )

    feature = build_alm_feature(
        channel="QU",
        coefficients=([0.0] * 6, [1.0] * 6),
        convention=canonical_spin2_alm_convention(lmax=2),
    )

    assert feature["convention_metadata"]["paired_map_order"] == "Q_then_U"


def test_observable_vector_rejects_alm_payload_without_convention_metadata() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="convention_metadata"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            alm_features={"T": {"lmax": 4, "convention": "complex_alm"}},
            sky_support=_sky_support(),
            manifest=_manifest(),
        )

    with pytest.raises(ValueError, match="convention_metadata"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            alm_features={"T": {"coefficients": [1.0, 0.0]}},
            sky_support=_sky_support(),
            manifest=_manifest(),
        )

    from htt.obsstat.alm_conventions import canonical_temperature_alm_convention

    with pytest.raises(ValueError, match="convention_metadata"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            alm_features={
                "convention_metadata": canonical_temperature_alm_convention(
                    lmax=1
                ).to_metadata(),
                "T": {"coefficients": [1.0, 0.0, 0.0]},
            },
            sky_support=_sky_support(),
            manifest=_manifest(),
        )


def test_observable_vector_accepts_alm_payload_with_valid_metadata() -> None:
    from htt.obsstat.alm_conventions import (
        build_alm_feature,
        canonical_temperature_alm_convention,
    )
    from htt.obsstat.observable_vector import build_observable_vector

    vector = build_observable_vector(
        ell_max=4,
        channels=("TT",),
        alm_features={
            "T": build_alm_feature(
                channel="T",
                coefficients=[0.0] * 15,
                convention=canonical_temperature_alm_convention(lmax=4),
            )
        },
        sky_support=_sky_support(),
        manifest=_manifest(),
    )

    metadata = vector.alm_features["alm"]["T"]["convention_metadata"]
    assert metadata["coordinate_frame"] == "galactic"
    assert metadata["claim_scope"] == "observable_feature_convention"


def test_observable_vector_rejects_alm_sky_frame_mismatch() -> None:
    from htt.obsstat.alm_conventions import (
        build_alm_feature,
        canonical_temperature_alm_convention,
    )
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="coordinate_frame"):
        build_observable_vector(
            ell_max=4,
            channels=("TT",),
            alm_features={
                "T": build_alm_feature(
                    channel="T",
                    coefficients=[0.0] * 15,
                    convention=canonical_temperature_alm_convention(
                        lmax=4,
                        coordinate_frame="icrs",
                    ),
                )
            },
            sky_support=_sky_support(),
            manifest=_manifest(),
        )


def test_registry_exports_no_inference_or_family_identification_claims() -> None:
    import htt.obsstat.alm_conventions as alm_conventions

    public_names = set(alm_conventions.__all__)

    assert "build_alm_feature" in public_names
    assert not [
        name
        for name in public_names
        if any(
            forbidden in name.lower()
            for forbidden in ("posterior", "evidence", "family", "geometry")
        )
    ]
