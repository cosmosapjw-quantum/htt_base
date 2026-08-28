from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from obsstat.planck_irrep_carrier import (
    CLAIM_TIER,
    EXPECTED_DIMENSION,
    EXPECTED_NULL_ROWS,
    FORMAT,
    OBSERVATION_ROW_ID,
    PlanckIrrepCarrierError,
    replay_planck_irrep_carrier,
    scalar_feature_closure_report,
    write_planck_irrep_carrier,
)
from obsstat.planck_pr3_operator import (
    JOINT_CUTSKY_ESTIMATOR_ID,
    ordered_row_id_hash,
)


def _sha(character: str) -> str:
    return "sha256:" + character * 64


def _rows() -> tuple[str, ...]:
    return tuple(
        f"FFP10-SMICA-CMBNOISE-{index:05d}"
        for index in range(EXPECTED_NULL_ROWS)
    )


def _operator() -> dict[str, object]:
    return {
        "estimator_id": JOINT_CUTSKY_ESTIMATOR_ID,
        "basis_dimension": 36,
        "retained_dimension": EXPECTED_DIMENSION,
        "basis_order": [],
        "mask_sha256": _sha("1"),
        "normal_matrix_sha256": _sha("2"),
        "operator_sha256": _sha("3"),
        "condition_number": 6.2,
        "singular_floor": 0.15,
        "relative_threshold": 1.0e-10,
        "condition_ceiling": 1.0e8,
        "transfer_order": "JOINT_MASKED_FIT_THEN_BEAM_PIXEL_COMMONIZATION",
    }


def _transfer() -> dict[str, str]:
    return {
        "source_beam_sha256": _sha("4"),
        "source_pixel_window_sha256": _sha("5"),
        "target_beam_sha256": _sha("6"),
        "target_pixel_window_sha256": _sha("7"),
    }


def _arrays() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260828)
    observed = rng.normal(size=EXPECTED_DIMENSION).astype(np.float64)
    nulls = rng.normal(
        size=(EXPECTED_NULL_ROWS, EXPECTED_DIMENSION)
    ).astype(np.float64)
    return observed, nulls


def _write(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    observed, nulls = _arrays()
    null_ids = _rows()
    package = tmp_path / "carrier.npz"
    metadata = tmp_path / "metadata.json"
    receipt = write_planck_irrep_carrier(
        package_path=package,
        metadata_path=metadata,
        observed_real_alm=observed,
        null_real_alm=nulls,
        row_ids=(OBSERVATION_ROW_ID, *null_ids),
        null_ordered_row_ids_sha256=ordered_row_id_hash(null_ids),
        operator_identity=_operator(),
        transfer_identity=_transfer(),
        source_manifest_sha256=_sha("8"),
        scalar_feature_package_sha256=_sha("9"),
    )
    return package, metadata, receipt


def test_carrier_roundtrip_is_safe_numeric_and_claim_bounded(
    tmp_path: Path,
) -> None:
    package, metadata, receipt = _write(tmp_path)
    replay = replay_planck_irrep_carrier(
        package_path=package,
        metadata_path=metadata,
    )
    assert receipt["format"] == FORMAT
    assert receipt["claim_tier"] == CLAIM_TIER
    assert replay["state"] == "REPLAY_MATCH"
    assert replay["row_count"] == 301
    assert replay["carrier_dimension"] == 32
    assert replay["raw_maps_reopened"] is False
    assert "physical shear or vorticity measurement" in receipt["forbidden_use"]
    with np.load(package, allow_pickle=False) as bundle:
        assert set(bundle.files) == {
            "observed_real_alm",
            "null_real_alm",
            "row_ids",
            "real_alm_layout",
        }
        assert bundle["observed_real_alm"].dtype == np.dtype("float64")
        assert bundle["null_real_alm"].shape == (300, 32)
        assert bundle["row_ids"].dtype.kind == "U"
        assert bundle["real_alm_layout"].dtype.kind == "U"


@pytest.mark.parametrize(
    ("observed_transform", "null_transform", "match"),
    [
        (lambda value: value.astype(np.float32), lambda value: value, "float64"),
        (lambda value: value, lambda value: value[:, :-1], r"shape \(300,32\)"),
        (
            lambda value: np.where(
                np.arange(value.size) == 0,
                np.nan,
                value,
            ),
            lambda value: value,
            "finite",
        ),
    ],
)
def test_carrier_writer_rejects_malformed_arrays(
    tmp_path: Path,
    observed_transform,
    null_transform,
    match: str,
) -> None:
    observed, nulls = _arrays()
    null_ids = _rows()
    with pytest.raises(PlanckIrrepCarrierError, match=match):
        write_planck_irrep_carrier(
            package_path=tmp_path / "bad.npz",
            metadata_path=tmp_path / "bad.json",
            observed_real_alm=observed_transform(observed),
            null_real_alm=null_transform(nulls),
            row_ids=(OBSERVATION_ROW_ID, *null_ids),
            null_ordered_row_ids_sha256=ordered_row_id_hash(null_ids),
            operator_identity=_operator(),
            transfer_identity=_transfer(),
            source_manifest_sha256=_sha("8"),
            scalar_feature_package_sha256=_sha("9"),
        )


def test_carrier_writer_rejects_row_order_mutation(tmp_path: Path) -> None:
    observed, nulls = _arrays()
    null_ids = _rows()
    mutated = (null_ids[1], null_ids[0], *null_ids[2:])
    with pytest.raises(PlanckIrrepCarrierError, match="row order"):
        write_planck_irrep_carrier(
            package_path=tmp_path / "bad.npz",
            metadata_path=tmp_path / "bad.json",
            observed_real_alm=observed,
            null_real_alm=nulls,
            row_ids=(OBSERVATION_ROW_ID, *mutated),
            null_ordered_row_ids_sha256=ordered_row_id_hash(null_ids),
            operator_identity=_operator(),
            transfer_identity=_transfer(),
            source_manifest_sha256=_sha("8"),
            scalar_feature_package_sha256=_sha("9"),
        )


def test_carrier_writer_rejects_operator_or_transfer_drift(
    tmp_path: Path,
) -> None:
    observed, nulls = _arrays()
    null_ids = _rows()
    operator = _operator()
    operator["retained_dimension"] = 31
    with pytest.raises(PlanckIrrepCarrierError, match="frozen joint cut-sky"):
        write_planck_irrep_carrier(
            package_path=tmp_path / "bad.npz",
            metadata_path=tmp_path / "bad.json",
            observed_real_alm=observed,
            null_real_alm=nulls,
            row_ids=(OBSERVATION_ROW_ID, *null_ids),
            null_ordered_row_ids_sha256=ordered_row_id_hash(null_ids),
            operator_identity=operator,
            transfer_identity=_transfer(),
            source_manifest_sha256=_sha("8"),
            scalar_feature_package_sha256=_sha("9"),
        )


def test_carrier_replay_rejects_metadata_and_package_mutation(
    tmp_path: Path,
) -> None:
    package, metadata, _ = _write(tmp_path)
    payload = json.loads(metadata.read_text())
    payload["coordinate_frame"] = "ECLIPTIC"
    metadata.write_text(json.dumps(payload, sort_keys=True) + "\n")
    with pytest.raises(PlanckIrrepCarrierError, match="schema metadata"):
        replay_planck_irrep_carrier(
            package_path=package,
            metadata_path=metadata,
        )

    package2, metadata2, _ = _write(tmp_path / "second")
    with package2.open("ab") as handle:
        handle.write(b"mutation")
    with pytest.raises(PlanckIrrepCarrierError, match="package or claim"):
        replay_planck_irrep_carrier(
            package_path=package2,
            metadata_path=metadata2,
        )


def test_scalar_feature_closure_is_tight_and_fail_closed() -> None:
    rng = np.random.default_rng(47)
    observed = rng.normal(size=12)
    nulls = rng.normal(size=(300, 12))
    report = scalar_feature_closure_report(
        observed_expected=observed,
        observed_projected=observed.copy(),
        null_expected=nulls,
        null_projected=nulls.copy(),
    )
    assert report["state"] == "MATCH"
    mutated = nulls.copy()
    mutated[17, 8] += 1.0e-6
    with pytest.raises(PlanckIrrepCarrierError, match="differ"):
        scalar_feature_closure_report(
            observed_expected=observed,
            observed_projected=observed,
            null_expected=nulls,
            null_projected=mutated,
        )
