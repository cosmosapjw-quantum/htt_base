"""Fetch the exact public PR4 Commander observed map for FITS semantic intake.

Writes the large FITS only on the verified external mount. A partial file is
retained on transport failure; a successful existing target is never replaced.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual")
NAME = "COM_CMB_IQU-commander_4096_R4.00_full.fits"
URL = "https://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CMB_IQU-commander_4096_R4.00_full.fits"
EXPECTED_BYTES = 1_207_972_800  # official PLA CMB_MAP OID 15001 catalog
RESERVE_BYTES = 2 * 1024**3
PACKET = "902ebd6a521d6b31864e0bfce63336c62d6cec5ff2f6c3128de7ab68046fce35"
INPUT = "sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mount_and_capacity() -> tuple[str, int]:
    mount = subprocess.check_output(
        ["findmnt", "-no", "TARGET,SOURCE,FSTYPE,OPTIONS", "/mnt/extdrive"], text=True).strip()
    fields = mount.split()
    if len(fields) < 3 or fields[:3] != ["/mnt/extdrive", "/dev/sda2", "fuseblk"] or "rw" not in fields[3]:
        raise RuntimeError("external mount identity or RW mode changed")
    available = shutil.disk_usage("/mnt/extdrive").free
    if available < RESERVE_BYTES + EXPECTED_BYTES:
        raise RuntimeError("insufficient external free space for target plus reserve")
    return mount, available


def process_identity() -> dict:
    stat = Path("/proc/self/stat").read_text()
    after_comm = stat.split(") ", 1)[1].split()
    return {"pid": os.getpid(), "ppid": os.getppid(),
            "proc_stat_starttime_ticks": int(after_comm[19]),
            "cwd": str(Path.cwd()), "source": str(Path(__file__).resolve()),
            "source_sha256": sha256(Path(__file__)),
            "packet_id": PACKET, "input_identity": INPUT,
            "started_utc": datetime.now(timezone.utc).isoformat()}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    mount, available_before = mount_and_capacity()
    target = ROOT / NAME
    part = ROOT / (NAME + ".part")
    receipt = ROOT / (NAME + ".receipt.json")
    if target.exists() or part.exists() or receipt.exists():
        raise FileExistsError("existing target/partial/receipt requires explicit inspection")
    identity = process_identity()
    (ROOT / "COMMANDER_OBS_PROCESS_START.json").write_text(json.dumps(identity, indent=2) + "\n")
    started = time.monotonic()
    h = hashlib.sha256()
    size = 0
    request = Request(URL, headers={"User-Agent": "htt_base-research-source-intake/1"})
    with urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"provider HTTP status {response.status}")
        response_headers = dict(response.headers.items())
        content_length = response_headers.get("Content-Length")
        if content_length is not None and int(content_length) != EXPECTED_BYTES:
            raise ValueError("provider length differs from official PLA catalog")
        with part.open("xb") as out:
            while True:
                block = response.read(4 * 1024 * 1024)
                if not block:
                    break
                if size == 0 and not block.startswith(b"SIMPLE"):
                    raise ValueError("provider did not send FITS content")
                out.write(block)
                h.update(block)
                size += len(block)
                if shutil.disk_usage("/mnt/extdrive").free < RESERVE_BYTES:
                    raise RuntimeError("external free space fell below 2 GiB reserve")
            out.flush()
            os.fsync(out.fileno())
        final_url = response.geturl()
    if size != EXPECTED_BYTES:
        raise ValueError(f"download size {size} differs from catalog {EXPECTED_BYTES}")
    part.rename(target)
    record = {"schema": "htt.r36_pr4_public_fetch/1", "status": "DOWNLOADED_SOURCE_BYTES_ONLY",
              "packet_id": PACKET, "input_identity": INPUT, "source_catalog": "official PLA CMB_MAP OID 15001",
              "url": URL, "final_url": final_url, "response_headers": response_headers,
              "path": str(target), "bytes": size, "sha256": h.hexdigest(),
              "mount": mount, "available_before_bytes": available_before,
              "available_after_bytes": shutil.disk_usage("/mnt/extdrive").free,
              "reserve_bytes": RESERVE_BYTES, "elapsed_seconds": time.monotonic() - started,
              "process_identity": identity, "scientific_role": "PENDING_POLARIZATION_HDU_FRAME_UNIT_BEAM_INSPECTION"}
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"path": str(target), "bytes": size, "sha256": h.hexdigest(),
                      "elapsed_seconds": record["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
