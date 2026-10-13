"""Run frozen Lean argv with pre-execution source and import identity receipts."""

import hashlib
import json
import pathlib
import shlex
import subprocess
import sys
from datetime import datetime, timezone


TASK = pathlib.Path(__file__).resolve().parent.parent
PACKET = json.loads((TASK / "DELEGATION_PACKET.json").read_text())
RAW = TASK / "raw"
IMPORTS = RAW / "imports"
IMPORTS.mkdir(exist_ok=True)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


for arg in sys.argv[1:]:
    index = int(arg)
    spec = PACKET["commands"][index]
    argv = spec["argv"]
    source = pathlib.Path(shlex.split(argv[-1])[-1])
    expected = next((item["sha256"] for item in PACKET["imports"]
                     if item["source_path"] == str(source)), None)
    source_hash = sha256(source)
    if expected is not None and source_hash != expected:
        raise SystemExit(f"source drift at index {index}: {source_hash} != {expected}")
    runs = sorted(RAW.glob(f"compile_{index:02d}_*.json"))
    suffix = len(runs) + 1
    stem = f"compile_{index:02d}_{suffix:02d}"
    snapshot = RAW / f"{stem}.source.lean"
    snapshot.write_bytes(source.read_bytes())
    import_hashes_before = {p.name: sha256(p) for p in sorted(IMPORTS.glob("*.olean"))}
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(argv, cwd=spec["cwd"], capture_output=True, timeout=100)
        stdout, stderr, exit_code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code, timed_out = exc.stdout or b"", exc.stderr or b"", 124, True
    (RAW / f"{stem}.stdout").write_bytes(stdout)
    (RAW / f"{stem}.stderr").write_bytes(stderr)
    receipt = {
        "index": index,
        "purpose": spec["purpose"],
        "argv": argv,
        "cwd": spec["cwd"],
        "started_utc": started,
        "exit_code": exit_code,
        "timed_out_after_seconds": 100 if timed_out else None,
        "source_path": str(source),
        "source_snapshot": snapshot.name,
        "source_sha256": source_hash,
        "import_sha256_before": import_hashes_before,
        "import_sha256_after": {p.name: sha256(p) for p in sorted(IMPORTS.glob("*.olean"))},
        "stdout": f"{stem}.stdout",
        "stderr": f"{stem}.stderr",
    }
    (RAW / f"{stem}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"{stem}: exit={exit_code} source={source_hash}", flush=True)
    if exit_code:
        print(stderr.decode(errors="replace")[-3000:], file=sys.stderr)
        raise SystemExit(exit_code)
