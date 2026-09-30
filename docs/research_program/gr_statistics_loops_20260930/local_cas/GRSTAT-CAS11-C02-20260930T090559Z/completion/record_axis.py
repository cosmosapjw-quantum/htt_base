#!/usr/bin/python3
"""Record complete axis output and forward its bytes and exit status unchanged."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = RUN.parents[4]
axis = sys.argv[1]
if axis not in {"wolfram_xact", "sympy", "sage_singular", "lean"}:
    raise SystemExit("Unknown axis")
source = RUN / axis / ("run_axis.py" if axis == "lean" else "completion/run_axis.py")
argv = ["/usr/bin/python3", str(source.relative_to(ROOT))]
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
output = HERE / "observed" / (stamp + "_" + axis)
output.mkdir(parents=True, exist_ok=False)
record = {"axis": axis, "argv": argv, "cwd": str(ROOT),
          "source_sha256_before": hashlib.sha256(source.read_bytes()).hexdigest(),
          "started_at": stamp}
(output / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
    result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
record.update(exit_code=result.returncode,
              source_sha256_after=hashlib.sha256(source.read_bytes()).hexdigest())
for name in ("stdout.log", "stderr.log"):
    record[name + "_sha256"] = hashlib.sha256((output / name).read_bytes()).hexdigest()
(output / "execution.json").write_text(json.dumps(record, indent=2) + "\n")
sys.stdout.buffer.write((output / "stdout.log").read_bytes())
sys.stderr.buffer.write((output / "stderr.log").read_bytes())
sys.exit(result.returncode)
