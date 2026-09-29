from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[2]


def _matrix(tmp_path: Path, observed: Path) -> Path:
    rows = []
    for index in range(52):
        rows.append({
            "dataset_id": "planck.fixture.tt" if index == 0 else f"missing.{index}",
            "work_packet": "DATA-02" if index == 0 else "DATA-03",
            "role_for_analysis": "observed_spectrum_or_release_container" if index == 0 else "map",
            "ownership": "USER_CONFIRMED",
            "historical_inventory_path_hint": observed.relative_to(tmp_path).as_posix() if index == 0 else f"absent/{index}.npz",
            "index_metadata": {"spectrum": "TT", "unit": "uK^2 (D_ell)"} if index == 0 else {},
            "duplicate_relation_status": "VERIFY_TRANSFORM_AND_CONTENT_ID",
            "claim_ceiling": "diagnostic only",
        })
    path = tmp_path / "matrix.json"
    path.write_text(json.dumps({"user_dataset_count": 52, "datasets": rows}))
    return path


def test_cli_executes_available_spectrum_and_keeps_missing_lanes(tmp_path: Path) -> None:
    observed = tmp_path / "owned" / "tt.npz"
    observed.parent.mkdir()
    np.savez(observed, ell=np.array([2., 3.]), dl=np.array([11., 18.]), err_lo=np.array([1., 2.]), err_hi=np.array([2., 3.]))
    theory = tmp_path / "theory.npz"
    np.savez(theory, ell=np.array([2., 3.]), D_TT=np.array([10., 20.]))
    matrix = _matrix(tmp_path, observed)
    output = tmp_path / "result"
    completed = subprocess.run([
        sys.executable, str(REPO / "scripts" / "analyze_owned_observations.py"),
        "--matrix", str(matrix), "--repo-root", str(tmp_path), "--theory", str(theory), "--output", str(output),
    ], cwd=REPO, text=True, capture_output=True)
    assert completed.returncode == 0, completed.stderr
    report = json.loads((output / "owned_data_analysis_report.json").read_text())
    bindings = json.loads((output / "owned_data_bindings.json").read_text())
    assert bindings["dataset_count"] == 52
    assert report["spectral_lane"]["status"] == "EXECUTED"
    assert report["spectral_lane"]["executed"][0]["law_status"] == "DIAGONAL_PROXY_ONLY"
    assert report["optional_lanes"]["DATA-03"] == "IMPLEMENTED_HOLD_INPUT_INCOMPLETE"
    assert report["scientific_claim_promotion"] is False
    assert list((output / "spectra").glob("*.csv"))
    assert list((output / "spectra").glob("*.png"))


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q", __file__]))
