"""Regression tests for the file-backed FLRW CAMB comparison report.

These tests use the shipped CAMB reference fixture only.  They do not import
CAMB and do not generate synthetic physics; the temporary BASS archive is just
the fixture recast into the export schema to prove the report math and schema
contract.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "compare_flrw_lowell_pstf_to_camb.py"
CAMB_REF = REPO_ROOT / "data" / "camb_ref_planck2018.npz"


def _load_compare_module():
    spec = importlib.util.spec_from_file_location(
        "compare_flrw_lowell_pstf_to_camb", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_bass_archive_from_camb(
    out: Path,
    *,
    tt_scale: float = 1.0,
    ee_scale: float = 1.0,
    te_scale: float = 1.0,
) -> None:
    if not CAMB_REF.exists():
        pytest.skip(f"missing CAMB fixture: {CAMB_REF}")
    camb = np.load(CAMB_REF)
    ell_ref = np.asarray(camb["ell"], dtype=np.int64)
    ell = np.arange(int(np.max(ell_ref)) + 1, dtype=np.int64)

    def fill(name: str, scale: float) -> np.ndarray:
        values = np.zeros_like(ell, dtype=np.float64)
        values[ell_ref] = np.asarray(camb[name], dtype=np.float64) * scale
        return values

    metadata = {"producer": "test fixture recast from shipped CAMB reference"}
    np.savez(
        out,
        ell=ell,
        d_tt=fill("D_TT", tt_scale),
        d_ee=fill("D_EE", ee_scale),
        d_te=fill("D_TE", te_scale),
        cl_tt=fill("C_TT", tt_scale),
        cl_ee=fill("C_EE", ee_scale),
        cl_te=fill("C_TE", te_scale),
        metadata_json=np.asarray(json.dumps(metadata)),
    )


def test_report_passes_for_identical_recast_fixture(tmp_path: Path) -> None:
    module = _load_compare_module()
    bass_path = tmp_path / "bass_exact.npz"
    _write_bass_archive_from_camb(bass_path)

    report = module.compare_archives(
        bass_path=bass_path,
        camb_path=CAMB_REF,
        ell_min=2,
        ell_max=30,
        tt_tolerance=0.01,
        ee_tolerance=0.02,
        te_tolerance=0.02,
    )

    assert report.passed is True
    assert {item.channel for item in report.channels} == {"TT", "EE", "TE"}
    assert max(item.max_abs_rel_error for item in report.channels) == 0.0
    assert report.bass_metadata["producer"] == (
        "test fixture recast from shipped CAMB reference"
    )


def test_report_flags_channel_residual_without_failing_report_mode(
    tmp_path: Path,
) -> None:
    module = _load_compare_module()
    bass_path = tmp_path / "bass_tt_drift.npz"
    _write_bass_archive_from_camb(bass_path, tt_scale=1.05)

    report = module.compare_archives(
        bass_path=bass_path,
        camb_path=CAMB_REF,
        ell_min=2,
        ell_max=30,
        tt_tolerance=0.01,
        ee_tolerance=0.02,
        te_tolerance=0.02,
    )

    by_channel = {item.channel: item for item in report.channels}
    assert report.passed is False
    assert by_channel["TT"].passed is False
    assert by_channel["TT"].max_abs_rel_error == pytest.approx(0.05)
    assert by_channel["EE"].passed is True
    assert by_channel["TE"].passed is True
