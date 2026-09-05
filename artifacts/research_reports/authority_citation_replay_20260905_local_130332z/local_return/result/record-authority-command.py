"""Task-local command capture; invokes the existing tests without modifying them."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
WT = OUT.parent / "worktree"
PY = "/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python"
FILES = [
    "tests/contracts/test_report_a_t9_v4.py",
    "tests/contracts/test_report_a_citation_matrix_r4a1nf.py",
    "tests/contracts/test_report_a_r3_flattened.py",
    "tests/contracts/test_report_a_r4a0_source.py",
    "tests/contracts/test_report_a_r4a1n_notation.py",
    "tests/contracts/test_report_a_r4a1nf_flattened.py",
    "tests/contracts/test_report_a_r4a1_authority_v3.py",
    "tests/contracts/test_report_a_r4a1v0_formal_verifiers.py",
]
NODE = FILES[6] + "::test_r4a1nf_binds_the_exact_declared_git_blobs"
name = sys.argv[1]
assert name in {"red", "post-pin", "collect", "authority-replay"}
argv = [PY, "-B", "-m", "pytest", "-q"]
if name in {"red", "post-pin"}:
    argv.append(NODE)
elif name == "collect":
    argv.extend(["--collect-only", *FILES])
else:
    argv.extend([*FILES, "--junitxml=" + str(OUT / "authority-replay.xml")])
assert not (OUT / (name + ".command.json")).exists()
env = os.environ.copy()
removed = {k: env.pop(k) for k in ("PYTHONPATH", "PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS") if k in env}
env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
start = datetime.now(timezone.utc).isoformat()
clock = time.monotonic()
timeout = 900
with (OUT / (name + ".stdout")).open("xb") as out, (OUT / (name + ".stderr")).open("xb") as err:
    child = subprocess.Popen(argv, cwd=WT, env=env, stdout=out, stderr=err, start_new_session=True)
    timed_out = False
    try:
        exit_code = child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        import signal
        os.killpg(child.pid, signal.SIGKILL)
        exit_code = child.wait()
record = {
    "label": name, "cwd": str(WT), "argv": argv,
    "versions": json.loads((OUT / "versions.json").read_text()),
    "started_at": start, "completed_at": datetime.now(timezone.utc).isoformat(),
    "elapsed_seconds": time.monotonic() - clock, "child_pid": child.pid,
    "exit_code": exit_code, "timeout_seconds": timeout, "timed_out": timed_out,
    "fresh_python_process": True, "removed_environment_override_names": sorted(removed),
    "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"},
    "stdout": name + ".stdout", "stderr": name + ".stderr",
    "junit": "authority-replay.xml" if name == "authority-replay" else None,
}
with (OUT / (name + ".command.json")).open("x") as f:
    json.dump(record, f, indent=2)
    f.write("\n")
(OUT / (name + ".exit")).write_text(str(exit_code) + "\n")
print(json.dumps(record, indent=2))
raise SystemExit(124 if timed_out else exit_code)
