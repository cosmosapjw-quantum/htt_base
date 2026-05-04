#!/usr/bin/env python3
"""Compare a BASS PSTF FLRW low-ell spectrum archive against CAMB.

Inputs are static spectrum archives.  This script does not import CAMB and
does not generate transfer functions.  Use
``scripts/export_flrw_lowell_pstf_spectrum.py`` to produce the BASS archive
and ``scripts/generate_camb_reference.py`` to refresh the CAMB oracle.

By default the command is report-only and exits successfully even when the
residuals are large.  Pass ``--fail-on-threshold`` to turn the configured
tolerances into a CI gate after the Python PSTF closure is expected to pass.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


CHANNELS = ("TT", "EE", "TE")


@dataclass(frozen=True)
class ChannelComparison:
    channel: str
    ell_min: int
    ell_max: int
    n_ell: int
    max_abs_rel_error: float
    mean_abs_rel_error: float
    rms_abs_rel_error: float
    max_abs_error_uk2: float
    mean_abs_error_uk2: float
    worst_ell: int
    worst_bass_uk2: float
    worst_camb_uk2: float
    tolerance: float
    passed: bool


@dataclass(frozen=True)
class ComparisonReport:
    bass_path: str
    camb_path: str
    ell_min: int
    ell_max: int
    channels: tuple[ChannelComparison, ...]
    passed: bool
    fail_on_threshold: bool
    bass_metadata: dict[str, object]


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path, allow_pickle=True)
    return {key: np.asarray(data[key]) for key in data.files}


def _decode_metadata(data: dict[str, np.ndarray]) -> dict[str, object]:
    if "metadata_json" not in data:
        return {}
    raw = data["metadata_json"]
    try:
        if raw.shape == ():
            text = str(raw.item())
        else:
            text = str(raw.ravel()[0])
        decoded = json.loads(text)
    except Exception:
        return {"metadata_json_decode_error": str(raw)}
    if isinstance(decoded, dict):
        return decoded
    return {"metadata_json_value": decoded}


def _channel_array(
    data: dict[str, np.ndarray],
    *,
    channel: str,
    prefix: str,
) -> tuple[np.ndarray, np.ndarray]:
    ell = np.asarray(data["ell"], dtype=np.int64)
    names = (
        f"{prefix}_{channel}",
        f"{prefix.lower()}_{channel.lower()}",
    )
    for name in names:
        if name in data:
            values = np.asarray(data[name], dtype=np.float64)
            if values.shape != ell.shape:
                raise ValueError(
                    f"{name} shape {values.shape} does not match ell {ell.shape}"
                )
            return ell, values
    raise ValueError(f"missing {prefix}_{channel} / {prefix.lower()}_{channel.lower()}")


def _values_by_ell(ell: np.ndarray, values: np.ndarray) -> dict[int, float]:
    return {int(l): float(v) for l, v in zip(ell, values)}


def _compare_channel(
    *,
    channel: str,
    bass: dict[str, np.ndarray],
    camb: dict[str, np.ndarray],
    ell_values: Iterable[int],
    tolerance: float,
    zero_abs_floor: float,
) -> ChannelComparison:
    bass_ell, bass_values = _channel_array(bass, channel=channel, prefix="D")
    camb_ell, camb_values = _channel_array(camb, channel=channel, prefix="D")
    bass_by_ell = _values_by_ell(bass_ell, bass_values)
    camb_by_ell = _values_by_ell(camb_ell, camb_values)

    rows: list[tuple[int, float, float, float, float]] = []
    for ell in ell_values:
        if ell not in bass_by_ell or ell not in camb_by_ell:
            continue
        bass_value = bass_by_ell[ell]
        camb_value = camb_by_ell[ell]
        abs_error = abs(bass_value - camb_value)
        if abs(camb_value) < zero_abs_floor:
            rel_error = 0.0 if abs_error < zero_abs_floor else abs_error / zero_abs_floor
        else:
            rel_error = abs_error / abs(camb_value)
        rows.append((ell, bass_value, camb_value, abs_error, rel_error))

    if not rows:
        raise ValueError(f"no overlapping ell values for {channel}")

    rel = np.asarray([row[4] for row in rows], dtype=np.float64)
    abs_err = np.asarray([row[3] for row in rows], dtype=np.float64)
    worst_idx = int(np.argmax(rel))
    worst = rows[worst_idx]
    return ChannelComparison(
        channel=channel,
        ell_min=int(min(row[0] for row in rows)),
        ell_max=int(max(row[0] for row in rows)),
        n_ell=len(rows),
        max_abs_rel_error=float(np.max(rel)),
        mean_abs_rel_error=float(np.mean(rel)),
        rms_abs_rel_error=float(np.sqrt(np.mean(rel**2))),
        max_abs_error_uk2=float(np.max(abs_err)),
        mean_abs_error_uk2=float(np.mean(abs_err)),
        worst_ell=int(worst[0]),
        worst_bass_uk2=float(worst[1]),
        worst_camb_uk2=float(worst[2]),
        tolerance=float(tolerance),
        passed=bool(float(np.max(rel)) <= float(tolerance)),
    )


def compare_archives(
    *,
    bass_path: Path,
    camb_path: Path,
    ell_min: int,
    ell_max: int,
    tt_tolerance: float,
    ee_tolerance: float,
    te_tolerance: float,
    zero_abs_floor: float = 1.0e-12,
    fail_on_threshold: bool = False,
) -> ComparisonReport:
    bass = _load_npz(bass_path)
    camb = _load_npz(camb_path)
    if ell_min < 2:
        raise ValueError("ell_min must be >= 2 for CMB spectrum comparison")
    if ell_max < ell_min:
        raise ValueError("ell_max must be >= ell_min")

    tolerances = {"TT": tt_tolerance, "EE": ee_tolerance, "TE": te_tolerance}
    ell_values = range(int(ell_min), int(ell_max) + 1)
    channel_reports = tuple(
        _compare_channel(
            channel=channel,
            bass=bass,
            camb=camb,
            ell_values=ell_values,
            tolerance=tolerances[channel],
            zero_abs_floor=zero_abs_floor,
        )
        for channel in CHANNELS
    )
    passed = all(item.passed for item in channel_reports)
    return ComparisonReport(
        bass_path=str(bass_path),
        camb_path=str(camb_path),
        ell_min=int(ell_min),
        ell_max=int(ell_max),
        channels=channel_reports,
        passed=passed,
        fail_on_threshold=bool(fail_on_threshold),
        bass_metadata=_decode_metadata(bass),
    )


def _report_to_dict(report: ComparisonReport) -> dict[str, object]:
    return {
        "bass_path": report.bass_path,
        "camb_path": report.camb_path,
        "ell_min": report.ell_min,
        "ell_max": report.ell_max,
        "passed": report.passed,
        "fail_on_threshold": report.fail_on_threshold,
        "bass_metadata": report.bass_metadata,
        "channels": [asdict(channel) for channel in report.channels],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bass", type=Path, required=True)
    parser.add_argument(
        "--camb-ref",
        type=Path,
        default=Path("data/camb_ref_planck2018.npz"),
    )
    parser.add_argument("--ell-min", type=int, default=2)
    parser.add_argument("--ell-max", type=int, default=30)
    parser.add_argument("--tt-tolerance", type=float, default=0.01)
    parser.add_argument("--ee-tolerance", type=float, default=0.02)
    parser.add_argument("--te-tolerance", type=float, default=0.02)
    parser.add_argument("--zero-abs-floor", type=float, default=1.0e-12)
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--fail-on-threshold", action="store_true")
    args = parser.parse_args()

    report = compare_archives(
        bass_path=args.bass,
        camb_path=args.camb_ref,
        ell_min=int(args.ell_min),
        ell_max=int(args.ell_max),
        tt_tolerance=float(args.tt_tolerance),
        ee_tolerance=float(args.ee_tolerance),
        te_tolerance=float(args.te_tolerance),
        zero_abs_floor=float(args.zero_abs_floor),
        fail_on_threshold=bool(args.fail_on_threshold),
    )
    payload = _report_to_dict(report)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out_json is not None:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.fail_on_threshold and not report.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
