from __future__ import annotations

import hashlib

import numpy as np
import pytest


def _sha(char: str = "a") -> str:
    return "sha256:" + char * 64


def _file_sha(path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _toy_payload(**overrides):
    payload = {
        "object_id": np.asarray(["cf4-1", "cf4-2", "cf4-3"]),
        "ra_deg": np.asarray([12.0, 140.0, 301.0]),
        "dec_deg": np.asarray([-8.0, 22.0, 55.0]),
        "redshift": np.asarray([0.012, 0.021, 0.034]),
        "distance_variable": np.asarray([0.15, -0.03, 0.08]),
        "distance_uncertainty": np.asarray([0.07, 0.06, 0.09]),
        "group_id": np.asarray(["g1", "g1", "g3"]),
        "is_grouped": np.asarray([True, True, False]),
        "method_flag": np.asarray(["TF", "TF", "SNIa"]),
        "calibration_flag": np.asarray(["cal-a", "cal-a", "cal-b"]),
    }
    payload.update(overrides)
    return payload


def _metadata(**overrides):
    from obsstat.catalogs.cf4 import Cf4CatalogMetadata

    values = {
        "release": "toy_cf4_fixture",
        "source_path": "memory://toy-cf4.npz",
        "checksum": _sha("b"),
        "redshift_frame": "CMB",
        "distance_variable_kind": "logdistance",
        "calibration_status": "toy_fixture_calibration",
    }
    values.update(overrides)
    return Cf4CatalogMetadata(**values)


def test_cf4_catalog_adapter_requires_object_level_schema() -> None:
    from obsstat.catalogs.cf4 import build_cf4_catalog_from_mapping

    catalog = build_cf4_catalog_from_mapping(_toy_payload(), metadata=_metadata())
    payload = catalog.to_metadata()

    assert catalog.row_count == 3
    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["redshift_frame"] == "CMB"
    assert payload["distance_variable_kind"] == "logdistance"
    assert payload["schema_fields"]["object_id"] == "required"
    assert payload["schema_fields"]["distance_uncertainty"] == "required"
    assert catalog.line_of_sight_unit.shape == (3, 3)
    assert np.allclose(np.linalg.norm(catalog.line_of_sight_unit, axis=1), 1.0)


def test_cf4_catalog_adapter_rejects_missing_distance_uncertainty() -> None:
    from obsstat.catalogs.cf4 import build_cf4_catalog_from_mapping

    payload = _toy_payload()
    payload.pop("distance_uncertainty")

    with pytest.raises(ValueError, match="distance_uncertainty"):
        build_cf4_catalog_from_mapping(payload, metadata=_metadata())


def test_cf4_catalog_adapter_rejects_invalid_shapes_and_uncertainties() -> None:
    from obsstat.catalogs.cf4 import build_cf4_catalog_from_mapping

    with pytest.raises(ValueError, match="same row count"):
        build_cf4_catalog_from_mapping(
            _toy_payload(distance_variable=np.asarray([0.1, 0.2])),
            metadata=_metadata(),
        )
    with pytest.raises(ValueError, match="positive finite"):
        build_cf4_catalog_from_mapping(
            _toy_payload(distance_uncertainty=np.asarray([0.07, 0.0, 0.09])),
            metadata=_metadata(),
        )


def test_cf4_catalog_npz_loader_uses_required_schema(tmp_path) -> None:
    from obsstat.catalogs.cf4 import load_cf4_catalog_npz

    path = tmp_path / "toy_cf4_catalog.npz"
    np.savez(path, **_toy_payload())

    catalog = load_cf4_catalog_npz(
        path,
        metadata=_metadata(source_path=str(path), checksum=_file_sha(path)),
    )

    assert catalog.row_count == 3
    assert catalog.metadata.source_path == str(path)


def test_cf4_catalog_npz_loader_rejects_checksum_mismatch(tmp_path) -> None:
    from obsstat.catalogs.cf4 import load_cf4_catalog_npz

    path = tmp_path / "toy_cf4_catalog.npz"
    np.savez(path, **_toy_payload())

    with pytest.raises(ValueError, match="checksum"):
        load_cf4_catalog_npz(path, metadata=_metadata(source_path=str(path), checksum=_sha("0")))


def test_cf4_query_grid_is_not_silently_promoted_to_object_catalog() -> None:
    from obsstat.catalogs.cf4 import build_cf4_catalog_from_mapping

    compact_grid = {
        "sgx": np.asarray([1.0, 2.0]),
        "sgy": np.asarray([3.0, 4.0]),
        "sgz": np.asarray([5.0, 6.0]),
        "vr_mean": np.asarray([20.0, 30.0]),
        "vr_std": np.asarray([100.0, 110.0]),
    }

    with pytest.raises(ValueError, match="object_id"):
        build_cf4_catalog_from_mapping(compact_grid, metadata=_metadata())


def test_peculiar_velocity_gaussian_requires_manifest() -> None:
    from obsstat.catalogs.cf4 import Cf4CatalogMetadata

    with pytest.raises(ValueError, match="Gaussian velocity manifest"):
        Cf4CatalogMetadata(
            release="toy_cf4_fixture",
            source_path="memory://toy-cf4.npz",
            checksum=_sha("c"),
            redshift_frame="CMB",
            distance_variable_kind="peculiar_velocity",
            calibration_status="toy_fixture_calibration",
            velocity_distribution_status="gaussian_exact",
        )

    with pytest.raises(ValueError, match="Gaussian velocity manifest"):
        Cf4CatalogMetadata(
            release="toy_cf4_fixture",
            source_path="memory://toy-cf4.npz",
            checksum=_sha("c"),
            redshift_frame="CMB",
            distance_variable_kind="peculiar_velocity",
            calibration_status="toy_fixture_calibration",
            velocity_distribution_status="gaussian_exact",
            gaussian_velocity_manifest_ref="docs/generated/missing_manifest.json",
        )


def test_peculiar_velocity_gaussian_accepts_loadable_manifest(tmp_path) -> None:
    from obsstat.catalogs.cf4 import Cf4CatalogMetadata

    manifest_path = tmp_path / "cf4_velocity_noise_manifest.json"
    manifest_path.write_text(
        """
{
  "variable_definition": "toy peculiar velocity fixture for schema tests",
  "redshift_frame": "CMB",
  "noise_model": "gaussian_exact",
  "covariance_status": "toy_diagonal_manifest",
  "calibration_status": "toy_fixture_calibration",
  "config_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "input_hashes": [
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
  ]
}
""",
        encoding="utf-8",
    )

    metadata = Cf4CatalogMetadata(
        release="toy_cf4_fixture",
        source_path="memory://toy-cf4.npz",
        checksum=_sha("c"),
        redshift_frame="CMB",
        distance_variable_kind="peculiar_velocity",
        calibration_status="toy_fixture_calibration",
        velocity_distribution_status="gaussian_exact",
        gaussian_velocity_manifest_ref=str(manifest_path),
    )

    payload = metadata.to_metadata()
    assert payload["gaussian_velocity_manifest_ref"] == str(manifest_path)
    assert payload["gaussian_velocity_manifest_hash"].startswith("sha256:")


@pytest.mark.parametrize("noise_model", ["non_gaussian", "not gaussian", "approximately_gaussian"])
def test_peculiar_velocity_manifest_rejects_non_gaussian_noise_labels(
    tmp_path,
    noise_model: str,
) -> None:
    from obsstat.catalogs.cf4 import Cf4CatalogMetadata

    manifest_path = tmp_path / "cf4_velocity_noise_manifest.json"
    manifest_path.write_text(
        f"""
{{
  "variable_definition": "toy peculiar velocity fixture for schema tests",
  "redshift_frame": "CMB",
  "noise_model": "{noise_model}",
  "covariance_status": "toy_diagonal_manifest",
  "calibration_status": "toy_fixture_calibration",
  "config_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "input_hashes": [
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
  ]
}}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="noise_model"):
        Cf4CatalogMetadata(
            release="toy_cf4_fixture",
            source_path="memory://toy-cf4.npz",
            checksum=_sha("c"),
            redshift_frame="CMB",
            distance_variable_kind="peculiar_velocity",
            calibration_status="toy_fixture_calibration",
            velocity_distribution_status="gaussian_exact",
            gaussian_velocity_manifest_ref=str(manifest_path),
        )


@pytest.mark.parametrize(
    "allowed_use",
    [
        "schema_check_and_production_inference",
        "diagnostic_native_transfer",
        "schema_check_family_selection",
        "diagnostic_truth_certificate",
    ],
)
def test_cf4_metadata_rejects_inference_like_allowed_use(allowed_use: str) -> None:
    from obsstat.catalogs.cf4 import Cf4CatalogMetadata

    with pytest.raises(ValueError, match="allowed_use"):
        Cf4CatalogMetadata(
            release="toy_cf4_fixture",
            source_path="memory://toy-cf4.npz",
            checksum=_sha("d"),
            redshift_frame="CMB",
            distance_variable_kind="logdistance",
            calibration_status="toy_fixture_calibration",
            allowed_use=allowed_use,
        )
