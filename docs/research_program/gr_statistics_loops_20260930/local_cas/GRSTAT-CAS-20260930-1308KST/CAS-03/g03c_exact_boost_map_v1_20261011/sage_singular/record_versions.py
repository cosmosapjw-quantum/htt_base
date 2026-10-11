"""Record exact CAS tool version commands without rerunning the proof."""

import json
import pathlib
import subprocess

axis = pathlib.Path(__file__).resolve().parent
repo = axis.parents[7]
raw = axis / "raw" / "versions_001"
raw.mkdir(parents=True, exist_ok=False)
commands = [
    ("sage", ["/usr/local/bin/sage", "--version"]),
    ("singular", ["/home/cosmosapjw/opt/sage/local/bin/Singular", "-q", "-v"]),
]
records = []
for name, argv in commands:
    proc = subprocess.run(argv, cwd=repo, capture_output=True, check=False)
    (raw / f"{name}.stdout.log").write_bytes(proc.stdout)
    (raw / f"{name}.stderr.log").write_bytes(proc.stderr)
    records.append({"tool": name, "argv": argv, "cwd": str(repo), "exit_code": proc.returncode,
                    "stdout_path": str(raw / f"{name}.stdout.log"),
                    "stderr_path": str(raw / f"{name}.stderr.log")})
(raw / "execution.json").write_text(json.dumps(records, indent=2) + "\n")
print(json.dumps([{"tool": x["tool"], "exit_code": x["exit_code"]} for x in records]))
