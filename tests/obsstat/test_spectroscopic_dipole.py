from __future__ import annotations

import json

import numpy as np
import pytest


def _sha(char: str = "a") -> str:
    return "sha256:" + char * 64


def _metadata(*, role: str, **overrides):
    from obsstat.catalogs.spectroscopic_dipole import SpectroscopicCatalogMetadata

    values = {
        "release": "toy_desi_dr1",
        "tracer": "QSO",
        "region": "NGC",
        "z_bin_id": "z0p8_1p2",
        "catalog_role": role,
        "source_path": f"memory://{role}.fits",
        "checksum": _sha("b" if role == "data" else "c"),
        "redshift_frame": "heliocentric_observed",
        "redshift_selection_status": "observed_redshift_selected",
    }
    values.update(overrides)
    return SpectroscopicCatalogMetadata(**values)


def _payload(**overrides):
    payload = {
        "object_id": np.asarray(["qso-1", "qso-2"]),
        "ra_deg": np.asarray([0.0, 90.0]),
        "dec_deg": np.asarray([0.0, 0.0]),
        "redshift": np.asarray([0.9, 1.1]),
        "weight": np.asarray([1.0, 1.0]),
    }
    payload.update(overrides)
    return payload


def _catalog(role: str, **metadata_overrides):
    from obsstat.catalogs.spectroscopic_dipole import (
        build_spectroscopic_catalog_from_mapping,
    )

    payload_overrides = {"object_id": np.asarray([f"{role}-1", f"{role}-2"])}
    if role == "random":
        payload_overrides.update(
            {
                "ra_deg": np.asarray([180.0, 270.0]),
                "dec_deg": np.asarray([0.0, 0.0]),
            }
        )
    return build_spectroscopic_catalog_from_mapping(
        _payload(**payload_overrides),
        metadata=_metadata(role=role, **metadata_overrides),
    )


def _correction(status: str = "not_bound"):
    from obsstat.catalogs.redshift_selection import RedshiftSelectionCorrectionSpec

    return RedshiftSelectionCorrectionSpec(
        z_bin_id="z0p8_1p2",
        selection_basis="observed_redshift",
        correction_status=status,
        correction_vector=(0.01, 0.0, 0.0) if status == "toy_correction_bound" else (0.0, 0.0, 0.0),
        config_hash=_sha("d"),
        input_hashes=(_sha("e"),),
        generating_command="pytest spectroscopic dipole",
        worktree_state="test",
    )


def test_data_random_dipole_estimator_is_obsstat_feature_only() -> None:
    from obsstat.catalogs.spectroscopic_dipole import estimate_data_random_dipole

    result = estimate_data_random_dipole(
        data_catalog=_catalog("data"),
        random_catalog=_catalog("random"),
        alpha=0.5,
        redshift_selection=_correction("not_bound"),
        config_hash=_sha("1"),
        input_hashes=(_sha("2"),),
        generating_command="pytest spectroscopic dipole",
        worktree_state="test",
    )
    payload = result.to_payload()

    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["artifact_role"] == "spectroscopic_data_random_dipole_feature"
    assert payload["publication_ready"] is False
    assert payload["production_status"] == "diagnostic_only"
    assert payload["statistic_role"] == "feature_only"
    assert payload["model_role"] == "not_model_input"
    assert payload["transfer_source"] == "none"
    assert payload["mask_status"] == "random_catalog_bound_mask_not_certified"
    assert payload["null_mock_status"] == "not_bound"
    assert payload["covariance_status"] == "not_bound"
    assert payload["config_hash"] == _sha("1")
    assert payload["input_hashes"] == [_sha("2")]
    assert payload["generating_command"] == "pytest spectroscopic dipole"
    assert payload["git_commit_or_worktree_state"] == "test"
    assert payload["alpha_definition"] == "user_supplied_random_first_moment_scale"
    assert payload["data_catalog"]["metadata"]["weight_definition"] == "precomputed_object_weight"
    assert payload["dipole_vector"] == pytest.approx([0.75, 0.75, 0.0])
    assert payload["raw_data_random_dipole"] == pytest.approx([0.75, 0.75, 0.0])
    assert "redshift_selection_correction_not_bound" in payload["blockers"]
    assert "matched_nulls_not_bound" in payload["blockers"]
    assert "certified_selection_weights_not_bound" in payload["blockers"]
    assert "random_mask_certification_not_bound" in payload["blockers"]
    assert "response_rank_not_bound" in payload["blockers"]
    assert "local_global_interpretation_not_bound" in payload["blockers"]
    assert "native_morphology_atlas_not_bound" in payload["blockers"]
    text = json.dumps(payload, sort_keys=True).lower()
    assert "mio posterior" not in text
    assert ("geometry " + "detected") not in text
    assert ("family " + "identified") not in text


def test_data_random_dipole_applies_toy_correction_but_stays_blocked() -> None:
    from obsstat.catalogs.spectroscopic_dipole import estimate_data_random_dipole

    result = estimate_data_random_dipole(
        data_catalog=_catalog("data"),
        random_catalog=_catalog("random"),
        alpha=0.5,
        redshift_selection=_correction("toy_correction_bound"),
        config_hash=_sha("1"),
        input_hashes=(_sha("2"),),
        generating_command="pytest spectroscopic dipole",
        worktree_state="test",
    )
    payload = result.to_payload()

    assert payload["raw_data_random_dipole"] == pytest.approx([0.75, 0.75, 0.0])
    assert payload["dipole_vector"] == pytest.approx([0.74, 0.75, 0.0])
    assert "redshift_selection_correction_not_bound" in payload["blockers"]
    assert payload["publication_ready"] is False


def test_data_random_dipole_rejects_parity_mismatch_and_missing_random() -> None:
    from obsstat.catalogs.spectroscopic_dipole import estimate_data_random_dipole

    with pytest.raises(ValueError, match="release/tracer/region/bin"):
        estimate_data_random_dipole(
            data_catalog=_catalog("data"),
            random_catalog=_catalog("random", region="SGC"),
            alpha=0.5,
            redshift_selection=_correction("not_bound"),
            config_hash=_sha("1"),
            input_hashes=(_sha("2"),),
            generating_command="pytest spectroscopic dipole",
            worktree_state="test",
        )
    with pytest.raises(ValueError, match="random_catalog"):
        estimate_data_random_dipole(
            data_catalog=_catalog("data"),
            random_catalog=None,
            alpha=0.5,
            redshift_selection=_correction("not_bound"),
            config_hash=_sha("1"),
            input_hashes=(_sha("2"),),
            generating_command="pytest spectroscopic dipole",
            worktree_state="test",
        )


def test_spectroscopic_catalog_rejects_bad_weights_and_claim_drift() -> None:
    from obsstat.catalogs.spectroscopic_dipole import (
        SpectroscopicCatalogMetadata,
        build_spectroscopic_catalog_from_mapping,
    )

    with pytest.raises(ValueError, match="weight"):
        build_spectroscopic_catalog_from_mapping(
            _payload(weight=np.asarray([1.0, -1.0])),
            metadata=_metadata(role="data"),
        )
    with pytest.raises(ValueError, match="allowed_use"):
        SpectroscopicCatalogMetadata(
            release="toy_desi_dr1",
            tracer="QSO",
            region="NGC",
            z_bin_id="z0p8_1p2",
            catalog_role="data",
            source_path="memory://data.fits",
            checksum=_sha("f"),
            redshift_frame="heliocentric_observed",
            redshift_selection_status="observed_redshift_selected",
            allowed_use="production_inference",
        )
