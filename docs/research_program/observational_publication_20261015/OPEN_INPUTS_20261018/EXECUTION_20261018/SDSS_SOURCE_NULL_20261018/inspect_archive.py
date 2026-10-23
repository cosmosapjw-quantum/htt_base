"""Index verified archive, freeze lexical member selection, inspect first header."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import time

from acquire_sdss import BLOCK, MD5, TOTAL, digest, safe_member, save_json

PATTERN = re.compile(r"R19(?P<box>[0-9]{3})\.(?P<observer>[0-7])_err_corr$")
FIELDS = ["ID", "RA", "Dec", "z_true", "z_obs", "z_obs_cen", "cen_flag",
          "subhalomass", "parenthalomass", "deVMag_r", "gmr", "kcor", "extinction_r",
          "rtrue", "r", "er", "strue", "s", "es", "itrue", "i", "ei", "x", "y", "z",
          "vxcen", "vycen", "vzcen", "vx", "vy", "vz", "nbar", "logdist_true",
          "logdist", "logdist_err", "logdist_alpha"]


def selected_entries(entries):
    identities = {}
    for entry in entries:
        match = PATTERN.search(PurePosixPath(entry["name"]).name)
        if match:
            key = (int(match["box"]), int(match["observer"]))
            if key in identities:
                raise ValueError(f"Duplicate box/observer identity {key}")
            identities[key] = entry
    boxes = sorted({key[0] for key in identities})
    if len(boxes) != 256 or len(identities) != 2048:
        raise ValueError(f"Expected 256 boxes x 8 observers, found {len(boxes)} and {len(identities)}")
    if any((box, observer) not in identities for box in boxes for observer in range(8)):
        raise ValueError("Incomplete observer membership")
    selected = [dict(identities[(box, 0)], box=box, observer=0) for box in boxes[:64]]
    if sum(entry["size"] for entry in selected) > 2 * 1024**3:
        raise ValueError("Selected members exceed frozen 2 GiB extraction cap")
    return boxes, selected


def inspect(root, output):
    archive = root / "mocks.tar.gz"
    identity = json.loads((root / "archive_identity.json").read_text())
    if (identity["status"] != "VALIDATED" or identity["md5"] != MD5
            or identity["bytes"] != TOTAL or archive.stat().st_size != TOTAL):
        raise ValueError("Verified complete archive required")
    # This same execution follows full acquisition MD5 validation; immutable archive
    # identity is rechecked here before its first external-input inspection.
    if digest(archive, "md5") != MD5:
        raise ValueError("Archive MD5 mismatch before index")
    started = time.monotonic()
    entries = []
    with tarfile.open(archive, "r|gz") as source:
        for member in source:
            p = PurePosixPath(member.name)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"Unsafe archive path {member.name!r}")
            if member.isdir():
                continue
            safe_member(member.name, member.isfile(), member.size, limit=TOTAL * 100)
            entries.append({"name": member.name, "size": member.size,
                            "mode": member.mode, "mtime": member.mtime})
            if len(entries) % 128 == 0:
                print(f"INDEX {len(entries)} regular members; {time.monotonic()-started:.1f}s", flush=True)
    save_json(root / "archive_index.json", {"archive_sha256": identity["sha256"], "entries": entries})
    boxes, selected = selected_entries(entries)
    selection = {"rule": "64 numerically lowest distinct XXX boxes; observer Y=0",
                 "frozen_before_scientific_outcome_read": True, "boxes": boxes[:64],
                 "members": selected, "selected_size_bytes": sum(e["size"] for e in selected),
                 "box_count": len(boxes), "observer_count_per_box": 8,
                 "independent_universes_certified": False,
                 "archive_sha256": identity["sha256"], "archive_md5": MD5,
                 "intake_head": "ad27f4cb5f84dfaccc322e53f2810ad29dc72276",
                 "observed_header_stage_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    save_json(output / "SELECTED_MEMBERS.json", selection)
    print(f"FROZEN {len(selected)} member names, {selection['selected_size_bytes']} bytes", flush=True)
    first = selected[0]
    target_dir = root / "selected"
    target_dir.mkdir(exist_ok=True)
    target = target_dir / PurePosixPath(first["name"]).name
    with tarfile.open(archive, "r|gz") as source:
        for member in source:
            if member.name != first["name"]:
                continue
            safe_member(member.name, member.isfile(), member.size)
            if target.exists():
                raise ValueError("Preserve existing selected member; explicit recovery required")
            h = hashlib.sha256()
            count = 0
            with source.extractfile(member) as stream, target.open("xb") as out:
                for block in iter(lambda: stream.read(BLOCK), b""):
                    count += len(block)
                    if count > first["size"]:
                        raise ValueError("Member exceeds frozen declared size")
                    out.write(block)
                    h.update(block)
            if count != first["size"]:
                raise ValueError("Short selected member")
            break
        else:
            raise ValueError("Selected member not found in verified archive")
    with target.open(encoding="ascii") as stream:
        lines = [stream.readline().rstrip("\r\n") for _ in range(8)]
    data_lines = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
    tokens = [line.split() for line in data_lines]
    inspection = {"status": "HEADER_INSPECTED_AWAITING_ASTRA", "member": first,
                  "member_sha256": h.hexdigest(), "member_path": str(target),
                  "first_eight_lines": lines, "whitespace_token_counts": [len(row) for row in tokens],
                  "pdf_documented_column_order": FIELDS,
                  "actual_header_present": any(line.lstrip().startswith("#") for line in lines),
                  "scientific_execution": "NOT_STARTED", "elapsed_index_header_s": time.monotonic()-started}
    save_json(output / "ACTUAL_HEADER.json", inspection)
    print(json.dumps(inspection, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    inspect(args.root, args.output)
