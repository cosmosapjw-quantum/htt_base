from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import warnings


FitsStatus = Literal["ok", "truncated", "unreadable", "unavailable"]


@dataclass(frozen=True)
class FitsIntegrityReport:
    status: FitsStatus
    actual_size: int
    expected_size: int | None = None
    detail: str | None = None
    warnings: tuple[str, ...] = ()


def inspect_fits_file(path: str | Path) -> FitsIntegrityReport:
    """Inspect a FITS file without forcing full data reads.

    Returns a small status object that can distinguish between:
    - intact FITS files (`ok`)
    - files shorter than their own FITS layout (`truncated`)
    - unreadable/corrupt files (`unreadable`)
    - environments where astropy is unavailable (`unavailable`)
    """
    path = Path(path)
    actual_size = path.stat().st_size

    try:
        from astropy.io import fits
    except ImportError as exc:
        return FitsIntegrityReport(
            status="unavailable",
            actual_size=actual_size,
            detail=str(exc),
        )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            with fits.open(path, memmap=True, lazy_load_hdus=True) as hdul:
                info = hdul.fileinfo(len(hdul) - 1)
                expected_size = info["datLoc"] + info["datSpan"]
        except Exception as exc:
            return FitsIntegrityReport(
                status="unreadable",
                actual_size=actual_size,
                detail=f"{type(exc).__name__}: {exc}",
                warnings=tuple(str(w.message) for w in caught),
            )

    status: FitsStatus = "ok"
    if actual_size < expected_size:
        status = "truncated"

    return FitsIntegrityReport(
        status=status,
        actual_size=actual_size,
        expected_size=expected_size,
        warnings=tuple(str(w.message) for w in caught),
    )


def format_fits_size(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "unknown"
    gib = num_bytes / (1024 ** 3)
    return f"{gib:.2f} GiB ({num_bytes} bytes)"
