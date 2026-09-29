from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from htt.obsstat.owned_data_adapter import bind_owned_products, binding_report, load_matrix


def _matrix(tmp_path: Path) -> dict:
    rows = []
    for index in range(52):
        path = f"inputs/d{index}.npz"
        rows.append({
            "dataset_id": f"dataset.{index}",
            "work_packet": "DATA-02" if index == 0 else "DATA-01",
            "role_for_analysis": "observed_spectrum_or_release_container",
            "ownership": "USER_CONFIRMED",
            "historical_inventory_path_hint": path,
            "index_metadata": {"unit": "uK^2 (D_ell)"} if index == 0 else {},
            "overlap_family_candidate": "same-sky" if index < 2 else None,
            "duplicate_relation_status": "VERIFY_TRANSFORM_AND_CONTENT_ID",
            "claim_ceiling": "diagnostic only",
        })
    payload = {"user_dataset_count": 52, "datasets": rows}
    (tmp_path / "matrix.json").write_text(json.dumps(payload))
    return payload


def test_exact_52_bindings_preserve_missing_and_known_arrays(tmp_path: Path) -> None:
    matrix = _matrix(tmp_path)
    source = tmp_path / "inputs" / "d0.npz"
    source.parent.mkdir()
    np.savez(source, ell=np.array([2, 3]), dl=np.array([1.0, -2.0]), covariance=np.eye(2))
    rows = bind_owned_products(matrix, repo_root=tmp_path)
    report = binding_report(rows)
    assert len(rows) == report["dataset_count"] == 52
    assert rows[0].path_status == "PRESENT_FILE"
    assert rows[0].units == "uK^2 (D_ell)"
    assert rows[0].covariance_status == "AVAILABLE"
    assert rows[0].schema["fields"]["dl"]["shape"] == [2]
    assert rows[1].path_status == "MISSING"
    assert rows[1].sha256 is None
    assert rows[1].covariance_status == "NOT_INSPECTED_INPUT_MISSING"
    assert report["cross_dataset_independence"] == "NOT_ASSUMED"


def test_object_array_schema_is_inspected_without_pickle(tmp_path: Path) -> None:
    matrix = _matrix(tmp_path)
    source = tmp_path / "inputs" / "d0.npz"
    source.parent.mkdir()
    np.savez(source, ell=np.array([2, 3]), dl=np.array([1.0, 2.0]), optional=np.array(None, dtype=object))
    row = bind_owned_products(matrix, repo_root=tmp_path)[0]
    assert row.path_status == "PRESENT_FILE"
    assert row.schema["fields"]["optional"]["dtype"] == "object"
    assert row.schema["fields"]["optional"]["scalar"] is None


def test_broken_symlink_is_not_recreated_or_followed(tmp_path: Path) -> None:
    matrix = _matrix(tmp_path)
    link = tmp_path / "inputs" / "d0.npz"
    link.parent.mkdir()
    link.symlink_to(tmp_path / "absent.npz")
    row = bind_owned_products(matrix, repo_root=tmp_path)[0]
    assert row.path_status == "BROKEN_SYMLINK"
    assert row.sha256 is None
    assert link.is_symlink()


def test_broken_symlink_ancestor_is_reported(tmp_path: Path) -> None:
    matrix = _matrix(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.symlink_to(tmp_path / "missing-volume")
    row = bind_owned_products(matrix, repo_root=tmp_path)[0]
    assert row.path_status == "BROKEN_SYMLINK_ANCESTOR"
    assert row.sha256 is None


def test_matrix_rejects_non_52_inventory(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"user_dataset_count": 1, "datasets": [{"dataset_id": "x"}]}))
    with pytest.raises(ValueError, match="exactly 52"):
        load_matrix(path)


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
