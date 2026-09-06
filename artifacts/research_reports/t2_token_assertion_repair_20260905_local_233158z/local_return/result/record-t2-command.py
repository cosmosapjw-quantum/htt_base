"""Capture this work unit's existing test commands; no validation policy changes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
PLAN = json.loads((OUT / "execution-plan.before-edits.json").read_text())
WT = Path(PLAN["REPO"])
PY = PLAN["PY"]
label = sys.argv[1]
assert label in {"syntax", "diff-check", "focused", "collect", "authority-replay"}
if label == "focused":
    argv = PLAN["focused_argv"]
elif label == "authority-replay":
    argv = PLAN["suite_argv"]
elif label == "collect":
    argv = [PY, "-B", "-m", "pytest", "-q", "--collect-only", *PLAN["suite_files"]]
elif label == "diff-check":
    argv = ["git", "diff", "--check"]
else:
    argv = [PY, "-B", "-c", "from pathlib import Path; p=Path('tests/contracts/test_report_a_r4a0_source.py'); compile(p.read_bytes(), str(p), 'exec'); print('SYNTAX_PASS')"]
freeze = json.loads((OUT / "repaired-source-freeze.json").read_text())
for row in freeze["files"]:
    assert hashlib.sha256((WT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
assert not (OUT / (label + ".command.json")).exists()
env = os.environ.copy()
removed = [key for key in ("PYTHONPATH", "PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS") if key in env]
for key in removed:
    env.pop(key)
env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
start = datetime.now(timezone.utc).isoformat()
clock = time.monotonic()
with (OUT / (label + ".stdout")).open("xb") as out, (OUT / (label + ".stderr")).open("xb") as err:
    process = subprocess.Popen(argv, cwd=WT, env=env, stdout=out, stderr=err, start_new_session=True)
    timed_out = False
    try:
        exit_code = process.wait(timeout=PLAN["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        exit_code = process.wait()
record = {
    "label": label, "argv": argv, "cwd": str(WT), "child_pid": process.pid,
    "started_at": start, "completed_at": datetime.now(timezone.utc).isoformat(),
    "elapsed_seconds": time.monotonic() - clock, "exit_code": exit_code,
    "timeout_seconds": PLAN["timeout_seconds"], "timed_out": timed_out,
    "versions": json.loads((OUT / "versions.json").read_text()),
    "source_freeze_sha256": hashlib.sha256((OUT / "repaired-source-freeze.json").read_bytes()).hexdigest(),
    "removed_environment_override_names": removed,
    "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"},
    "stdout": label + ".stdout", "stderr": label + ".stderr",
    "junit": label + ".xml" if label in {"focused", "authority-replay"} else None,
    "invocation_count_for_label": 1,
}
with (OUT / (label + ".command.json")).open("x") as f:
    json.dump(record, f, indent=2)
    f.write("\n")
(OUT / (label + ".exit")).write_text(str(exit_code) + "\n")
print(json.dumps({k: record[k] for k in ("label", "child_pid", "exit_code", "timed_out", "elapsed_seconds")}))
raise SystemExit(124 if timed_out else exit_code)
