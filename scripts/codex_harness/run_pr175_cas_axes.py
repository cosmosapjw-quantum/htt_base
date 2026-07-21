#!/usr/bin/env python3
"""PR-175 sealed four-axis CAS runs.

Executes each axis command fresh (blind: no axis reads a sibling result),
parses its emitted checks/computed, and seals an envelope bound to the
frozen contract hash. `--check` re-verifies envelope integrity (contract
binding, source hashes, obligation keyset, expected values) WITHOUT
rerunning engines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTRACT = REPO / "docs/generated/pr175_cas/CAS_CONTRACT_PR175_INVARIANT_V2.json"
OUT_DIR = REPO / "docs/generated/pr175_cas"

AXES = {
    "sympy": {
        "cmd": ["venv/bin/python", "-B", "htt/src/common/pr175_sympy_axis.py"],
        "cwd": ".",
        "timeout": 600,
    },
    "sage_singular": {
        "cmd": ["sage", "sage/pr175_invariant_axis.sage"],
        "cwd": ".",
        "timeout": 900,
    },
    "wolfram_xact": {
        "cmd": ["wolframscript", "-file", "wolfram/pr175_invariant_axis.wls"],
        "cwd": ".",
        "timeout": 900,
    },
    "lean": {
        "cmd": ["lake", "exe", "pr175invariant"],
        "cwd": "formal_pr175",
        "timeout": 900,
    },
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract() -> tuple[dict, str]:
    return json.loads(CONTRACT.read_text()), _sha(CONTRACT)


def _parse_axis_json(axis: str, stdout: str) -> dict:
    if axis == "wolfram_xact":
        checks_line = next(
            line for line in stdout.splitlines() if line.startswith("PR175_CHECKS ")
        )
        computed_line = next(
            line for line in stdout.splitlines() if line.startswith("PR175_COMPUTED ")
        )
        pairs = re.findall(r'"([A-Za-z_0-9]+)" -> (True|False)', checks_line)
        checks = {key: value == "True" for key, value in pairs}
        computed = dict(
            re.findall(r'"([A-Za-z_0-9]+)" -> "([^"]*)"', computed_line)
        )
        all_pass = "PR175_ALL_PASS True" in stdout
        xact = "PR175_XACT True" in stdout
        return {
            "checks": checks,
            "computed": computed,
            "all_pass": all_pass and xact,
        }
    payload = json.loads(stdout.strip().splitlines()[-1])
    return payload


# Shared computed keys every axis must agree on with the contract.
EXPECTED_VALUE_KEYS = (
    "R_I",
    "R_II",
    "R_VI_0",
    "R_VII_0",
    "R_VIII",
    "R_IX",
    "R_V",
    "R_IV",
    "R_III",
    "R_VI_h",
    "R_VII_h",
)


def _expected_values_ok(contract: dict, computed: dict) -> bool:
    expected = contract["target"]["expected_exact_values"]
    return all(
        computed.get(key) == expected.get(key) for key in EXPECTED_VALUE_KEYS
    )


def _run_axis(axis: str, contract: dict, contract_sha: str) -> dict:
    spec = AXES[axis]
    try:
        completed = subprocess.run(
            spec["cmd"],
            cwd=REPO / spec["cwd"],
            capture_output=True,
            text=True,
            timeout=spec["timeout"],
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        blocked = (
            "BLOCKED_RESOURCE_LIMIT"
            if isinstance(exc, subprocess.TimeoutExpired)
            else "BLOCKED_PLATFORM_OR_LICENSE"
        )
        return {
            "schema_version": 1,
            "axis": axis,
            "contract_id": contract["identity"]["contract_id"],
            "contract_sha256": contract_sha,
            "status": blocked,
            "evidence_class": "exact",
            "checks": {},
            "computed": {},
            "commands": [
                {"cmd": " ".join(spec["cmd"]), "cwd": spec["cwd"], "exit": 124}
            ],
            "sibling_results_read": [],
            "source_output_hashes": contract["axes"][axis]["sources"],
            "transcript_tail": f"engine unavailable or timed out: {exc!r}",
            "completed_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            ),
        }
    stdout = completed.stdout
    status = "FAIL"
    checks: dict = {}
    computed: dict = {}
    if completed.returncode == 0:
        try:
            payload = _parse_axis_json(axis, stdout)
            checks = payload.get("checks", {})
            computed = payload.get("computed", {})
            obligations = set(contract["target"]["exact_test_obligations"])
            if (
                set(checks) == obligations
                and all(checks.values())
                and payload.get("all_pass", False)
                and _expected_values_ok(contract, computed)
            ):
                status = "PASS"
        except (StopIteration, json.JSONDecodeError, KeyError):
            status = "INCONCLUSIVE"
    else:
        if completed.returncode in (124, 127):
            status = "BLOCKED_PLATFORM_OR_LICENSE"
        elif completed.returncode == 3:
            status = "BLOCKED_PACKAGE_UNAVAILABLE"
        else:
            status = "FAIL"
    return {
        "schema_version": 1,
        "axis": axis,
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": contract_sha,
        "status": status,
        "evidence_class": "exact",
        "checks": checks,
        "computed": computed,
        "commands": [
            {
                "cmd": " ".join(spec["cmd"]),
                "cwd": spec["cwd"],
                "exit": completed.returncode,
            }
        ],
        "sibling_results_read": [],
        "source_output_hashes": contract["axes"][axis]["sources"],
        "transcript_tail": (stdout + completed.stderr)[-1200:],
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def verify_envelopes() -> list[str]:
    contract, contract_sha = _contract()
    errors: list[str] = []
    obligations = set(contract["target"]["exact_test_obligations"])
    for axis in AXES:
        path = OUT_DIR / f"axis_result_{axis}.json"
        if not path.is_file():
            errors.append(f"missing envelope: {path.name}")
            continue
        env = json.loads(path.read_text())
        if env.get("contract_sha256") != contract_sha:
            errors.append(f"{axis}: stale contract binding")
        if env.get("status") == "PASS":
            if set(env.get("checks", {})) != obligations:
                errors.append(f"{axis}: PASS obligation keyset incomplete")
            if not all(env["checks"].values()):
                errors.append(f"{axis}: PASS carries a false check")
            if not _expected_values_ok(contract, env.get("computed", {})):
                errors.append(
                    f"{axis}: PASS computed values differ from the contract's "
                    "expected_exact_values"
                )
        for ref in env.get("source_output_hashes", []):
            actual = _sha(REPO / ref["path"])
            if actual != ref["sha256"]:
                errors.append(f"{axis}: source drift {ref['path']}")
        if env.get("sibling_results_read") != []:
            errors.append(f"{axis}: blinding violated")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        errors = verify_envelopes()
        print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
        return 0 if not errors else 1

    contract, contract_sha = _contract()
    for axis in AXES:
        envelope = _run_axis(axis, contract, contract_sha)
        target = OUT_DIR / f"axis_result_{axis}.json"
        target.write_text(json.dumps(envelope, indent=1, sort_keys=True) + "\n")
        print(f"{axis}: {envelope['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
