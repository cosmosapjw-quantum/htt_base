"""G08-A compile harness: snapshot source, run one frozen Lean argv, write receipts.

Usage: python3 run_compile.py <purpose> <source.lean> [<module_root_dir> [<olean_out>]]

Every invocation gets the next global index NN (never overwriting earlier
attempts) and writes compile_NN.source.lean (pre-execution snapshot),
compile_NN.stdout, compile_NN.stderr and compile_NN.json.
Modeled on CAS-12/g12c_finite_chart_action_v1_20261011/raw/run_compiles.py.
"""

import hashlib
import json
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone

RAW = pathlib.Path(__file__).resolve().parent
IMPORTS = RAW / "imports"
IMPORTS.mkdir(exist_ok=True)
CWD = "/home/cosmosapjw/lean_oracles/viii_oracle"
TIMEOUT_S = 900


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    return sha256_bytes(path.read_bytes())


def next_index():
    used = [int(m.group(1)) for p in RAW.glob("compile_*.json")
            if (m := re.fullmatch(r"compile_(\d+)\.json", p.name))]
    return max(used, default=0) + 1


def main():
    purpose = sys.argv[1]
    source = pathlib.Path(sys.argv[2]).resolve()
    root = pathlib.Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else source.parent
    olean = pathlib.Path(sys.argv[4]).resolve() if len(sys.argv) > 4 else None
    index = next_index()
    stem = f"compile_{index:02d}"
    source_bytes = source.read_bytes()
    (RAW / f"{stem}.source.lean").write_bytes(source_bytes)
    inner = f"LEAN_PATH={shlex.quote(str(IMPORTS))}:$LEAN_PATH lean -R {shlex.quote(str(root))}"
    if olean is not None:
        inner += f" -o {shlex.quote(str(olean))}"
    inner += f" {shlex.quote(str(source))}"
    argv = ["lake", "env", "bash", "-c", inner]
    imports_before = {p.name: sha256(p) for p in sorted(IMPORTS.glob("*.olean"))}
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(argv, cwd=CWD, capture_output=True, timeout=TIMEOUT_S)
        stdout, stderr, code, timed_out = result.stdout, result.stderr, result.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b"", exc.stderr or b"", 124, True
    finished = datetime.now(timezone.utc).isoformat()
    (RAW / f"{stem}.stdout").write_bytes(stdout)
    (RAW / f"{stem}.stderr").write_bytes(stderr)
    receipt = {
        "index": index,
        "purpose": purpose,
        "argv": argv,
        "lake_resolved": shutil.which("lake"),
        "cwd": CWD,
        "started_utc": started,
        "finished_utc": finished,
        "timeout_seconds": TIMEOUT_S,
        "timed_out": timed_out,
        "exit_code": code,
        "source_path": str(source),
        "source_snapshot": f"{stem}.source.lean",
        "source_sha256": sha256_bytes(source_bytes),
        "module_root": str(root),
        "olean_out": str(olean) if olean else None,
        "olean_sha256_after": sha256(olean) if olean and olean.exists() and code == 0 else None,
        "import_sha256_before": imports_before,
        "import_sha256_after": {p.name: sha256(p) for p in sorted(IMPORTS.glob("*.olean"))},
        "stdout": f"{stem}.stdout",
        "stderr": f"{stem}.stderr",
    }
    (RAW / f"{stem}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"{stem}: exit={code} source_sha256={receipt['source_sha256']}", flush=True)
    sys.stdout.write(stdout.decode(errors="replace")[-20000:])
    sys.stderr.write(stderr.decode(errors="replace")[-5000:])
    sys.exit(code)


if __name__ == "__main__":
    main()
