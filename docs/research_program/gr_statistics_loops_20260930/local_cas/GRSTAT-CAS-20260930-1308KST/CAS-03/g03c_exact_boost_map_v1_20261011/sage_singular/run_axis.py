"""Record exact commands and raw outputs for this finite CAS axis."""

import hashlib
import json
import pathlib
import subprocess
import sys

axis = pathlib.Path(__file__).resolve().parent
repo = axis.parents[7]
contract = axis.parent / "CONTRACT.json"
programs = [
    ("sage", ["/usr/local/bin/sage", "-python", str(axis / "verify.py")]),
    ("singular", ["/home/cosmosapjw/opt/sage/local/bin/Singular", "-q", str(axis / "verify.sing")]),
]
attempt = sys.argv[1] if len(sys.argv) == 2 else "attempt_001"
outdir = axis / "raw" / attempt
outdir.mkdir(parents=True, exist_ok=False)
records = []
for name, argv in programs:
    proc = subprocess.run(argv, cwd=repo, capture_output=True, check=False)
    (outdir / f"{name}.stdout.log").write_bytes(proc.stdout)
    (outdir / f"{name}.stderr.log").write_bytes(proc.stderr)
    semantic_success = proc.returncode == 0
    if name == "singular":
        semantic_success = (semantic_success and b"PASS_SINGULAR_REMAINDERS_ZERO" in proc.stdout
                            and b"?" not in proc.stdout and b"FAIL_SINGULAR" not in proc.stdout)
    records.append({
        "tool": name,
        "argv": argv,
        "cwd": str(repo),
        "exit_code": proc.returncode,
        "semantic_success": semantic_success,
        "executable_sha256": hashlib.sha256(pathlib.Path(argv[0]).read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256((axis / ("verify.py" if name == "sage" else "verify.sing")).read_bytes()).hexdigest(),
        "stdout_path": str(outdir / f"{name}.stdout.log"),
        "stderr_path": str(outdir / f"{name}.stderr.log"),
    })
(outdir / "execution.json").write_text(json.dumps({
    "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
    "records": records,
}, indent=2) + "\n")
print(json.dumps({"attempt": attempt, "records": [{"tool": x["tool"], "exit_code": x["exit_code"],
                                                  "semantic_success": x["semantic_success"]} for x in records]}))
raise SystemExit(0 if all(x["semantic_success"] for x in records) else 1)
