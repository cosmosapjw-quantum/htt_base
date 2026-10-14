#!/usr/bin/env python3
"""Execute the frozen CAS-07 M04 Wolfram/xAct axis and emit one JSON payload."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = Path.cwd()
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
INPUTS = BASE / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "553502c17d46c3b47c5a7b892f149f603235239d8504392b9bd19923f4edde7a",
    INPUTS: "f4d3b3b96a86fabcf83c7134193ec70da61b15d7a45b1a4b2c6b581312c1d4d8",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
OBLIGATIONS = [
    "CAS-07-M04-VOLTERRA-IDENTITY",
    "CAS-07-M04-SCALAR-PREMISE",
    "CAS-07-M04-D-NORM",
    "CAS-07-M04-D-MINUS-SI",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marked_json(raw: str, marker: str) -> dict:
    pos = raw.rfind(marker)
    if pos < 0:
        raise ValueError(f"missing {marker}")
    obj, _ = json.JSONDecoder().raw_decode(raw[pos + len(marker) :].lstrip())
    if not isinstance(obj, dict):
        raise ValueError(f"{marker} is not an object")
    return obj


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    errors: list[str] = []
    observed = {str(path.relative_to(ROOT)): sha256(path) for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if observed[str(path.relative_to(ROOT))] != expected:
            errors.append(f"frozen input hash mismatch: {path.relative_to(ROOT)}")

    command = ["wolframscript", "-file", str(HERE / "check.wl")]
    exit_code: int | None = None
    raw_stdout = ""
    raw_stderr = ""
    checks = {key: False for key in OBLIGATIONS}
    diagnostics: dict = {}
    if not errors:
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=1500,
                check=False,
            )
            exit_code = completed.returncode
            raw_stdout = completed.stdout
            raw_stderr = completed.stderr
            try:
                parsed = marked_json(raw_stdout, "M04_CHECKS_JSON=")
                diagnostics = marked_json(raw_stdout, "M04_DIAGNOSTICS_JSON=")
                if set(parsed) != set(OBLIGATIONS) or any(type(v) is not bool for v in parsed.values()):
                    errors.append("Wolfram check keys/types differ from the frozen obligations")
                else:
                    checks = parsed
            except (ValueError, json.JSONDecodeError) as exc:
                errors.append(f"Wolfram output parse failed: {exc}")
            if exit_code != 0:
                errors.append(f"wolframscript exited {exit_code}")
        except subprocess.TimeoutExpired as exc:
            raw_stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            raw_stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            errors.append("wolframscript exceeded 1500 seconds")
        except OSError as exc:
            errors.append(f"wolframscript launch failed: {exc}")

    (HERE / "stdout.raw.txt").write_text(raw_stdout)
    (HERE / "stderr.raw.txt").write_text(raw_stderr)
    executable_hashes = {name: sha256(HERE / name) for name in ("run.py", "check.wl", "proof.md")}
    raw_hashes = {name: sha256(HERE / name) for name in ("stdout.raw.txt", "stderr.raw.txt")}
    all_pass = not errors and all(checks.values())
    payload = {
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "axis": "wolfram_xact",
        "status": "PASS" if all_pass else "INCONCLUSIVE",
        "contract_sha256": EXPECTED[CONTRACT],
        "evidence_class": "exact",
        "started_at": started,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": [{"argv": command, "cwd": str(ROOT), "exit_code": exit_code}],
        "tool_versions": {
            "wolfram": diagnostics.get("wolfram_version", "UNKNOWN"),
            "xTensor": diagnostics.get("xact_version", "UNKNOWN"),
            "python": platform.python_version(),
        },
        "executable_artifact_sha256": executable_hashes,
        "raw_evidence_sha256": raw_hashes,
        "input_sha256": observed,
        "diagnostics": diagnostics,
        "errors": errors,
        "launch_id": None,
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
        "scope": "CAS-07 M04 2D Jacobi matrix Volterra/operator-norm majorant only",
    }
    (HERE / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
