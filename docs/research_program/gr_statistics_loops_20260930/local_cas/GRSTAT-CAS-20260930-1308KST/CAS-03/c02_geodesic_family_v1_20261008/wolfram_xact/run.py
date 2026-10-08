#!/usr/bin/env python3
"""Run the independent CAS-03-C02 Wolfram+xTensor axis and seal evidence."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


AXIS_DIR = Path(__file__).resolve().parent
UNIT_DIR = AXIS_DIR.parent
CONTRACT_PATH = UNIT_DIR / "EXECUTION_CONTRACT.json"
ADMITTED_INPUTS_PATH = UNIT_DIR / "ADMITTED_INPUTS.json"
COMMON_SPEC_PATH = (
    UNIT_DIR.parents[3] / "cas" / "COMMON_SPEC.md"
)
PROOF_PATH = AXIS_DIR / "proof.wl"
GENERATED_NAMES = (
    "raw_engine.stdout.log",
    "raw_engine.stderr.log",
    "argv.json",
    "versions.json",
    "execution.json",
    "result.json",
    "hashes.sha256",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def preserve_previous() -> str | None:
    existing = [AXIS_DIR / name for name in GENERATED_NAMES if (AXIS_DIR / name).exists()]
    if not existing:
        return None
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    destination = AXIS_DIR / "attempts" / stamp
    destination.mkdir(parents=True, exist_ok=False)
    for path in existing:
        shutil.move(str(path), destination / path.name)
    return str(destination.relative_to(AXIS_DIR))


def main() -> int:
    previous_attempt = preserve_previous()
    started = utc_now()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    expected_hashes = {
        item["path"]: item["sha256"]
        for item in contract["identity"]["source_input_hashes"]
    }
    repo_root = UNIT_DIR.parents[6]
    admitted_rel = str(ADMITTED_INPUTS_PATH.relative_to(repo_root))
    common_rel = str(COMMON_SPEC_PATH.relative_to(repo_root))
    actual_inputs = {
        admitted_rel: sha256(ADMITTED_INPUTS_PATH),
        common_rel: sha256(COMMON_SPEC_PATH),
    }
    input_hash_checks = {
        path: {
            "expected": expected_hashes.get(path),
            "actual": actual,
            "match": expected_hashes.get(path) == actual,
        }
        for path, actual in actual_inputs.items()
    }

    executable = shutil.which("wolframscript")
    argv = [executable or "wolframscript", "-file", str(PROOF_PATH)]
    write_json(
        AXIS_DIR / "argv.json",
        {"argv": argv, "cwd": str(AXIS_DIR), "launch": None},
    )

    if executable is None:
        completed = None
        stdout = ""
        stderr = "wolframscript executable unavailable\n"
        exit_code = 127
    else:
        completed = subprocess.run(
            argv,
            cwd=AXIS_DIR,
            text=True,
            capture_output=True,
            timeout=1800,
            check=False,
            env=os.environ.copy(),
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code = completed.returncode

    (AXIS_DIR / "raw_engine.stdout.log").write_text(stdout, encoding="utf-8")
    (AXIS_DIR / "raw_engine.stderr.log").write_text(stderr, encoding="utf-8")

    engine_payload: dict[str, Any] | None = None
    parse_error: str | None = None
    sentinel = "CAS_RESULT_JSON="
    for line in reversed(stdout.splitlines()):
        if line.startswith(sentinel):
            try:
                engine_payload = json.loads(line[len(sentinel) :])
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
            break
    if engine_payload is None and parse_error is None:
        parse_error = "CAS_RESULT_JSON sentinel absent"

    finished = utc_now()
    engine_pass = (
        exit_code == 0
        and engine_payload is not None
        and engine_payload.get("status") == "PASS"
        and engine_payload.get("evidence_class") == "exact"
    )
    hashes_pass = all(item["match"] for item in input_hash_checks.values())
    status = "PASS" if engine_pass and hashes_pass else "FAIL"

    versions = {
        "wolfram": None if engine_payload is None else engine_payload.get("wolfram_version"),
        "xTensor": None if engine_payload is None else engine_payload.get("xtensor_version"),
    }
    write_json(AXIS_DIR / "versions.json", versions)
    execution = {
        "started_utc": started,
        "finished_utc": finished,
        "cwd": str(AXIS_DIR),
        "argv": argv,
        "exit_code": exit_code,
        "timeout_seconds": 1800,
        "previous_attempt_preserved_at": previous_attempt,
        "stdout_path": "raw_engine.stdout.log",
        "stderr_path": "raw_engine.stderr.log",
        "parse_error": parse_error,
    }
    write_json(AXIS_DIR / "execution.json", execution)

    result = {
        "schema": "htt.cas.axis-result.v1",
        "axis": "wolfram_xact",
        "component": "CAS-03-C02",
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": sha256(CONTRACT_PATH),
        "status": status,
        "evidence_class": "exact",
        "claim_ceiling": "C02 finite geodesic family only",
        "scientific_admission": "HOLD",
        "launch": None,
        "authority": "unavailable",
        "model": {"name": "UNKNOWN", "effort": "UNKNOWN"},
        "independence": {
            "mode": "blind-results-and-derivations",
            "sibling_or_historical_results_read": False,
            "permitted_inputs_only": True,
        },
        "statement_alignment": {
            "family_difference": "exact target equality over reals",
            "rank_controls": "all eight zero/nonzero strata; kernel dimension equals zero-entry count",
            "repeated_nonzero": "explicit all-nonzero and two-nonzero repeated controls",
            "all_zero": "explicit rank-zero/kernel-dimension-three control",
            "domain_assumption_diff": [],
        },
        "input_hash_checks": input_hash_checks,
        "engine": {
            "argv": argv,
            "cwd": str(AXIS_DIR),
            "exit_code": exit_code,
            "versions": versions,
            "raw_stdout": "raw_engine.stdout.log",
            "raw_stderr": "raw_engine.stderr.log",
        },
        "proof": engine_payload,
        "remaining_obligations": ["CAS03 C03", "eigenfield existence/IFT", "science"],
        "generated_utc": finished,
    }
    write_json(AXIS_DIR / "result.json", result)

    hashed_paths = [
        CONTRACT_PATH,
        ADMITTED_INPUTS_PATH,
        COMMON_SPEC_PATH,
        PROOF_PATH,
        Path(__file__).resolve(),
        AXIS_DIR / "raw_engine.stdout.log",
        AXIS_DIR / "raw_engine.stderr.log",
        AXIS_DIR / "argv.json",
        AXIS_DIR / "versions.json",
        AXIS_DIR / "execution.json",
        AXIS_DIR / "result.json",
    ]
    hash_lines = []
    for path in hashed_paths:
        try:
            display = path.relative_to(AXIS_DIR)
        except ValueError:
            display = path
        hash_lines.append(f"{sha256(path)}  {display}")
    (AXIS_DIR / "hashes.sha256").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    counterexample = None
    if status != "PASS":
        counterexample = {
            "engine_exit_code": exit_code,
            "engine_status": None if engine_payload is None else engine_payload.get("status"),
            "input_hashes_match": hashes_pass,
            "parse_error": parse_error,
        }
    envelope = {
        "status": status,
        "checks": {"CAS-03-C02": status == "PASS"},
        "domain_assumption_diff": (
            [] if engine_payload is None else engine_payload.get("domain_assumption_diff", [])
        ),
        "counterexample": counterexample,
        "result_path": "result.json",
    }
    print(json.dumps(envelope, sort_keys=True, separators=(",", ":")))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
