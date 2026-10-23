"""Monitor these existing requests, then finish only the authorized source stage.

Never starts a range request. Stops at actual-header evidence, before science.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

from acquire_sdss import RANGES, acquire

HERE = Path(__file__).resolve().parent
ROOT = Path("/mnt/extdrive/workdir/htt_open_data/sdss_source_null_20261018")
PIDS = (747838, 762427, 762426)


def live(pid):
    try:
        command = Path(f"/proc/{pid}/cmdline").read_bytes()
    except FileNotFoundError:
        return False
    return b"SDSS_SOURCE_NULL_20261018/acquire_sdss.py" in command


while True:
    states = []
    all_validated = True
    for (start, end), pid in zip(RANGES, PIDS):
        part = ROOT / f"mocks.{start}-{end}.part"
        receipt = ROOT / f"range.{start}-{end}.json"
        completed = receipt.exists() and json.loads(receipt.read_text())["status"] == "VALIDATED"
        state = {"start": start, "end": end, "pid": pid, "active": live(pid),
                 "bytes": part.stat().st_size if part.exists() else 0, "completed_receipt": completed}
        states.append(state)
        all_validated &= completed
        if not completed and not state["active"]:
            print(json.dumps({"status": "HOLD_MISSING_COMPLETION", "state": state}), flush=True)
            raise SystemExit(1)
    print(json.dumps({"status": "SOURCE_ACQUISITION_MONITOR", "utc_epoch": time.time(), "ranges": states}), flush=True)
    if all_validated:
        # The original sequential coordinator may already be assembling. Do not
        # race it; wait for its exit or its validated complete archive receipt.
        identity = ROOT / "archive_identity.json"
        if identity.exists() and json.loads(identity.read_text())["status"] == "VALIDATED":
            break
        if not live(PIDS[0]):
            # All receipts exist: this call can only reuse ranges/assemble; any
            # mismatched receipt fails before it could issue a new request.
            acquire(ROOT)
            break
    time.sleep(30)

command = [sys.executable, str(HERE / "inspect_archive.py"), str(ROOT), str(HERE)]
print(json.dumps({"status": "INDEX_AND_HEADER_START", "command": command}), flush=True)
result = subprocess.run(command)
print(json.dumps({"status": "STAGE1_RETURN_TO_ASTRA" if result.returncode == 0 else "STAGE1_FAILURE_PRESERVED",
                  "exit_code": result.returncode, "scientific_execution": "NOT_STARTED"}), flush=True)
raise SystemExit(result.returncode)
