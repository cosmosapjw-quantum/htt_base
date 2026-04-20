from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from astropy.io import fits


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dl_fits_utils import inspect_fits_file


def write_test_fits(path: Path) -> None:
    fits.PrimaryHDU(data=np.arange(16, dtype=np.float32).reshape(4, 4)).writeto(path)


def test_inspect_fits_file_reports_ok_for_complete_file(tmp_path: Path) -> None:
    path = tmp_path / "complete.fits"
    write_test_fits(path)

    report = inspect_fits_file(path)

    assert report.status == "ok"
    assert report.expected_size == report.actual_size


def test_inspect_fits_file_reports_truncated_file(tmp_path: Path) -> None:
    path = tmp_path / "truncated.fits"
    write_test_fits(path)
    original = path.read_bytes()
    path.write_bytes(original[:-128])

    report = inspect_fits_file(path)

    assert report.status == "truncated"
    assert report.expected_size is not None
    assert report.actual_size < report.expected_size


def test_inspect_fits_file_reports_unreadable_for_non_fits(tmp_path: Path) -> None:
    path = tmp_path / "broken.fits"
    path.write_bytes(b"not-a-fits-file")

    report = inspect_fits_file(path)

    assert report.status == "unreadable"
    assert report.detail is not None
