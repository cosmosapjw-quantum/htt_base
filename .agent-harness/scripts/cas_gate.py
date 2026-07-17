#!/usr/bin/env python3
"""Four-axis CAS gate: preflight, axis-result checking, adjudication.

Canonical axes (display order): Wolfram Engine+xAct, SymPy,
SageMath+Singular, Lean. The four axes are mandatory and non-collapsible
(audit §5, decision ADJ-CAS-FOUR-AXIS-001):

- `preflight`  — repo-pinned per-axis tool probes → receipts under
  `.agent-harness/receipts/cas_preflight/`. A missing engine yields a
  BLOCKED receipt, never a silent skip. Tool readiness is NOT claim
  validation.
- `check-axis` — validate one axis result envelope against a contract
  (hash binding, status vocabulary, typed output hashes).
- `adjudicate` — aggregate state machine. `CAS_4AXIS_PASS` requires all
  four axes PASS under one contract hash; a missing/blocked required axis
  is `CAS_BLOCKED` (three axes can never pass); any valid counterexample or
  proof failure is `CAS_FAIL`; post-normalization disagreement is
  `CAS_CONFLICT` — there is deliberately no majority-vote code path.
  Exceptions count only when preregistered before the earliest axis
  completion and approved by someone other than the excepted axis's agent
  (`CAS_PASS_WITH_REGISTERED_EXCEPTION`, never described as "4-axis pass").

Note: `scripts/run_egs3_v9_seals.py` is a legacy diagnostic runner for the
frozen v9 report lane and is NOT a four-axis CAS gate — it silently skips
unavailable lanes and converts blocker exits to 0 by v9-frozen design.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _harness import dump_json, load_json, root

AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
AXIS_STATUSES = {
    "PASS",
    "FAIL",
    "MISALIGNED_ASSUMPTIONS",
    "BLOCKED_PLATFORM_OR_LICENSE",
    "BLOCKED_PACKAGE_UNAVAILABLE",
    "BLOCKED_RESOURCE_LIMIT",
    "NOT_APPLICABLE_COMPUTATION_CLASS",
    "INCONCLUSIVE",
}
BLOCKED_STATUSES = {
    "BLOCKED_PLATFORM_OR_LICENSE",
    "BLOCKED_PACKAGE_UNAVAILABLE",
    "BLOCKED_RESOURCE_LIMIT",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str], timeout: int) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return completed.returncode, (completed.stdout + completed.stderr)[-4000:]
    except FileNotFoundError as exc:
        return 127, f"not installed: {exc}"
    except subprocess.TimeoutExpired:
        return 124, "probe timeout"


def _probe_wolfram(repo: Path) -> dict:
    code = 'Print[$VersionNumber]; Needs["xAct`xTensor`"]; Print["XACT_LOAD_OK"]; Exit[0]'
    exit_code, out = _run(["wolframscript", "-code", code], timeout=120)
    ready = exit_code == 0 and "XACT_LOAD_OK" in out
    return {
        "status": "PASS" if ready else (
            "BLOCKED_PLATFORM_OR_LICENSE" if exit_code in (127, 124) else "BLOCKED_PACKAGE_UNAVAILABLE"
        ),
        "commands": [{"cmd": "wolframscript -code <version+xAct probe>", "exit": exit_code}],
        "transcript_tail": out[-800:],
    }


def _probe_sympy(repo: Path) -> dict:
    python = repo / "venv" / "bin" / "python"
    interpreter = str(python) if python.is_file() else sys.executable
    code = "import sympy, sys; x = sympy.symbols('x'); assert sympy.factor(x**2-1) == (x-1)*(x+1); print(sympy.__version__)"
    exit_code, out = _run([interpreter, "-c", code], timeout=120)
    return {
        "status": "PASS" if exit_code == 0 else "BLOCKED_PACKAGE_UNAVAILABLE",
        "commands": [{"cmd": f"{interpreter} -c <sympy exact factor probe>", "exit": exit_code}],
        "transcript_tail": out[-800:],
    }


def _probe_sage_singular(repo: Path) -> dict:
    code = "x = polygen(QQ, 'x'); assert (x**2-1).factor() is not None; import sage.all; print(sage.all.version()); print(singular.eval('system(\"version\");'))"
    exit_code, out = _run(["sage", "-c", code], timeout=300)
    return {
        "status": "PASS" if exit_code == 0 else (
            "BLOCKED_PLATFORM_OR_LICENSE" if exit_code in (127, 124) else "BLOCKED_PACKAGE_UNAVAILABLE"
        ),
        "commands": [{"cmd": "sage -c <exact factor + singular version probe>", "exit": exit_code}],
        "transcript_tail": out[-800:],
    }


def _probe_lean(repo: Path) -> dict:
    toolchain_file = repo / "formal" / "lean-toolchain"
    if not toolchain_file.is_file():
        return {
            "status": "BLOCKED_PACKAGE_UNAVAILABLE",
            "commands": [{"cmd": "cat formal/lean-toolchain", "exit": 1}],
            "transcript_tail": "formal/lean-toolchain missing — Lean must run repo-pinned (audit ADJ-LEAN-TOOLCHAIN-001)",
        }
    toolchain = toolchain_file.read_text(encoding="utf-8").strip()
    exit_code, out = _run(["env", f"ELAN_TOOLCHAIN={toolchain}", "lean", "--version"], timeout=300)
    return {
        "status": "PASS" if exit_code == 0 else "BLOCKED_PLATFORM_OR_LICENSE",
        "commands": [
            {"cmd": f"ELAN_TOOLCHAIN={toolchain} lean --version", "exit": exit_code}
        ],
        "pinned_toolchain": toolchain,
        "transcript_tail": out[-800:],
    }


PROBES = {
    "wolfram_xact": _probe_wolfram,
    "sympy": _probe_sympy,
    "sage_singular": _probe_sage_singular,
    "lean": _probe_lean,
}


def cmd_preflight(args) -> int:
    repo = root()
    out_dir = repo / ".agent-harness" / "receipts" / "cas_preflight"
    axes = AXES if args.axis is None else (args.axis,)
    worst = 0
    for axis in axes:
        result = PROBES[axis](repo)
        receipt = {
            "schema_version": 1,
            "axis": axis,
            "probed_at": _utc_now(),
            "scope": "host-local tool readiness only; NOT claim validation",
            **result,
        }
        dump_json(out_dir / f"{axis}.json", receipt)
        print(f"{axis}: {receipt['status']}")
        if receipt["status"] != "PASS":
            worst = 2
    return worst


def _load_contract(repo: Path, contract_path: str) -> tuple[dict, str]:
    path = repo / contract_path
    contract = load_json(path)
    return contract, _sha256_path(path)


def _check_axis_result(result: dict, contract_sha256: str) -> list[str]:
    errors: list[str] = []
    if result.get("axis") not in AXES:
        errors.append(f"axis must be one of {list(AXES)}")
    if result.get("status") not in AXIS_STATUSES:
        errors.append(f"invalid axis status {result.get('status')!r}")
    if result.get("contract_sha256") != contract_sha256:
        errors.append(
            "axis result is bound to a different contract hash (stale — a "
            "contract change invalidates all four axis receipts)"
        )
    commands = result.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("axis result must record the actual commands and exits")
    if result.get("evidence_class") not in {"exact", "numerical"}:
        errors.append("axis result must declare evidence_class exact|numerical")
    if not result.get("completed_at"):
        errors.append("axis result must record completed_at")
    return errors


def cmd_check_axis(args) -> int:
    repo = root()
    _, contract_sha = _load_contract(repo, args.contract)
    result = load_json(repo / args.result)
    errors = _check_axis_result(result, contract_sha)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 2
    print(json.dumps({"ok": True, "axis": result["axis"], "status": result["status"]}))
    return 0


def _validate_exceptions(
    contract: dict, results: dict[str, dict]
) -> tuple[dict[str, dict], list[str]]:
    """Return {axis: exception} for valid preregistered exceptions."""

    errors: list[str] = []
    valid: dict[str, dict] = {}
    completions = [
        str(res.get("completed_at") or "") for res in results.values()
    ]
    earliest = min((c for c in completions if c), default=None)
    for exc in (
        contract.get("exceptions_adjudication", {}).get("preregistered_exceptions", [])
    ):
        axis = exc.get("axis")
        if axis not in AXES:
            errors.append(f"exception names unknown axis {axis!r}")
            continue
        registered_at = str(exc.get("registered_at") or "")
        if not registered_at:
            errors.append(f"exception for {axis} lacks registered_at (post-hoc)")
            continue
        if earliest is not None and registered_at >= earliest:
            errors.append(
                f"exception for {axis} was registered at {registered_at}, not "
                f"before the earliest axis completion {earliest} (post-hoc)"
            )
            continue
        approver = str(exc.get("approver") or "")
        if not approver:
            errors.append(f"exception for {axis} lacks an approver")
            continue
        if approver == axis or approver == f"cas_{axis}":
            errors.append(
                f"exception for {axis} is self-approved by its own axis agent"
            )
            continue
        valid[axis] = exc
    return valid, errors


def cmd_adjudicate(args) -> int:
    repo = root()
    contract, contract_sha = _load_contract(repo, args.contract)

    results: dict[str, dict] = {}
    errors: list[str] = []
    for rel in args.results:
        result = load_json(repo / rel)
        axis_errors = _check_axis_result(result, contract_sha)
        axis = str(result.get("axis"))
        if axis in results:
            errors.append(f"duplicate axis result for {axis}")
        results[axis] = result
        errors.extend(f"{rel}: {item}" for item in axis_errors)

    exceptions, exception_errors = _validate_exceptions(contract, results)
    errors.extend(exception_errors)

    statuses = {axis: res.get("status") for axis, res in results.items()}
    missing = [axis for axis in AXES if axis not in results]

    if any(status == "FAIL" for status in statuses.values()):
        aggregate = "CAS_FAIL"
    elif errors:
        aggregate = "CAS_BLOCKED"
    else:
        passing = {axis for axis, s in statuses.items() if s == "PASS"}
        excepted = {
            axis
            for axis, s in statuses.items()
            if s in BLOCKED_STATUSES | {"NOT_APPLICABLE_COMPUTATION_CLASS"}
            and axis in exceptions
        }
        conflicted = {
            axis
            for axis, s in statuses.items()
            if s in {"MISALIGNED_ASSUMPTIONS", "INCONCLUSIVE"}
        }
        unresolved = (set(AXES) - passing - excepted) | set(missing)
        if conflicted:
            aggregate = "CAS_CONFLICT"
        elif unresolved:
            aggregate = "CAS_BLOCKED"
        elif excepted:
            aggregate = "CAS_PASS_WITH_REGISTERED_EXCEPTION"
        else:
            aggregate = "CAS_4AXIS_PASS"

    adjudication = {
        "schema_version": 1,
        "contract_id": contract.get("identity", {}).get("contract_id"),
        "contract_sha256": contract_sha,
        "aggregate_status": aggregate,
        "axis_statuses": statuses,
        "missing_axes": missing,
        "exceptions_applied": sorted(exceptions),
        "errors": errors,
        "adjudicated_at": _utc_now(),
        "note": (
            "CAS_4AXIS_PASS requires all four axes PASS under one contract "
            "hash; majority vote is structurally forbidden."
        ),
    }
    if args.out:
        dump_json(repo / args.out, adjudication)
    print(json.dumps(adjudication, indent=2, ensure_ascii=False))
    return 0 if aggregate in {"CAS_4AXIS_PASS", "CAS_PASS_WITH_REGISTERED_EXCEPTION"} else 2


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight")
    group = preflight.add_mutually_exclusive_group(required=True)
    group.add_argument("--axis", choices=list(AXES), default=None)
    group.add_argument("--all", action="store_true")

    check = sub.add_parser("check-axis")
    check.add_argument("--contract", required=True)
    check.add_argument("--result", required=True)

    adjudicate = sub.add_parser("adjudicate")
    adjudicate.add_argument("--contract", required=True)
    adjudicate.add_argument("--results", nargs="+", required=True)
    adjudicate.add_argument("--out", default=None)

    args = parser.parse_args()
    if args.command == "preflight":
        sys.exit(cmd_preflight(args))
    if args.command == "check-axis":
        sys.exit(cmd_check_axis(args))
    sys.exit(cmd_adjudicate(args))


if __name__ == "__main__":
    main()
