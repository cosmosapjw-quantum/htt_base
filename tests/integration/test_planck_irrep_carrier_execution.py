from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from obsstat.planck_irrep_carrier import EXPECTED_DIMENSION, EXPECTED_NULL_ROWS
from obsstat.planck_paired300_carrier_execution import (
    Paired300ExecutionError,
    capture_regular_file_identity,
    expected_paired300_row_ids,
    process_paired300_rows_one_pass,
    require_regular_file_identity_unchanged,
)


def _rows() -> tuple[str, ...]:
    return expected_paired300_row_ids()


def _process_factory(calls: list[int]):
    def process_map(pixel_map, *, component, context):
        assert component == "SMICA"
        assert context == {"operator": "frozen"}
        value = int(np.asarray(pixel_map)[0])
        calls.append(value)
        features = np.arange(12, dtype=np.float64) + value
        alm = np.arange(EXPECTED_DIMENSION, dtype=np.float64) + 1000.0 * value
        return features, {"fit": 1.0}, alm

    return process_map


def _carrier_from_alm(value) -> np.ndarray:
    return np.asarray(value, dtype=np.float64)


def test_one_pass_execution_preserves_exact_order_and_calls_each_row_once() -> None:
    calls: list[int] = []
    rows = _rows()
    result = process_paired300_rows_one_pass(
        observed_map=np.asarray([-1.0]),
        null_rows=((row_id, np.asarray([index], dtype=np.float64)) for index, row_id in enumerate(rows)),
        context={"operator": "frozen"},
        process_map=_process_factory(calls),
        carrier_from_alm=_carrier_from_alm,
    )
    assert calls == [-1, *range(EXPECTED_NULL_ROWS)]
    assert result.row_ids == ("PLANCK-PR3-SMICA-OBSERVED", *rows)
    assert result.observed_features.shape == (12,)
    assert result.null_features.shape == (300, 12)
    assert result.observed_real_alm.shape == (32,)
    assert result.null_real_alm.shape == (300, 32)
    assert np.array_equal(result.null_features[:, 0], np.arange(300))
    assert np.array_equal(result.null_real_alm[:, 0], 1000.0 * np.arange(300))


@pytest.mark.parametrize(
    "rows",
    [
        lambda values: values[:-1],
        lambda values: (values[1], values[0], *values[2:]),
        lambda values: (*values[:-1], values[-2]),
    ],
)
def test_one_pass_execution_rejects_missing_reordered_or_duplicate_rows(rows) -> None:
    identifiers = rows(_rows())
    with pytest.raises(Paired300ExecutionError, match="exact registered order"):
        process_paired300_rows_one_pass(
            observed_map=np.asarray([-1.0]),
            null_rows=((row_id, np.asarray([index])) for index, row_id in enumerate(identifiers)),
            context={"operator": "frozen"},
            process_map=_process_factory([]),
            carrier_from_alm=_carrier_from_alm,
        )


def test_one_pass_execution_rejects_bad_feature_or_carrier_shape() -> None:
    rows = _rows()

    def bad_process(pixel_map, *, component, context):
        value = int(np.asarray(pixel_map)[0])
        features = np.zeros(11 if value == 17 else 12, dtype=np.float64)
        carrier = np.zeros(EXPECTED_DIMENSION, dtype=np.float64)
        return features, {}, carrier

    with pytest.raises(Paired300ExecutionError, match="feature shape"):
        process_paired300_rows_one_pass(
            observed_map=np.asarray([-1.0]),
            null_rows=((row_id, np.asarray([index])) for index, row_id in enumerate(rows)),
            context={"operator": "frozen"},
            process_map=bad_process,
            carrier_from_alm=_carrier_from_alm,
        )


def test_regular_file_identity_detects_content_and_stat_mutation(tmp_path: Path) -> None:
    source = tmp_path / "source.fits"
    source.write_bytes(b"authority")
    before = capture_regular_file_identity(source, hash_content=True)
    assert require_regular_file_identity_unchanged(source, before) == before
    source.write_bytes(b"mutation")
    with pytest.raises(Paired300ExecutionError, match="mutated"):
        require_regular_file_identity_unchanged(source, before)


def test_regular_file_identity_refuses_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source.fits"
    source.write_bytes(b"authority")
    link = tmp_path / "link.fits"
    link.symlink_to(source)
    with pytest.raises(Paired300ExecutionError, match="regular non-symlink"):
        capture_regular_file_identity(link, hash_content=True)
