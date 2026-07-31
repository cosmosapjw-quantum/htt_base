#!/usr/bin/env python3
"""Risk-scaled CAS gate: preflight, stored-result inspection, and execution.

Canonical axes (display order): Wolfram Engine+xAct, SymPy,
SageMath+Singular, Lean. Contracts select 0/1/2/4 axes for R0/R1/R2/R3
claims respectively. Rocq remains an explicit ``required_axes`` opt-in:

- `preflight`  — repo-pinned per-axis tool probes → receipts under
  `.agent-harness/receipts/cas_preflight/`. A missing engine yields a
  BLOCKED receipt, never a silent skip. Tool readiness is NOT claim
  validation.
- `check-axis` — validate one axis result envelope against a contract
  (hash binding, status vocabulary, typed output hashes).
- `adjudicate` — inspect serialized axis-result envelopes. Stored envelopes
  are not execution authority and therefore cannot satisfy the CAS component
  of claim promotion. `--historical-replay` reports a frozen computed label
  only as `historical_aggregate_status`; the primary status remains blocked.
- `run-adjudicate` — execute every contract-required axis in one parent
  process and adjudicate only what that parent observed: argv, exit/timeout,
  and a JSON payload whose checks exactly cover the contract obligations.
  This is the only claim-promotion-eligible CAS path.

The aggregate state machine has no majority-vote path. A missing/blocked
required axis is `CAS_BLOCKED`; a counterexample or failed obligation is
`CAS_FAIL`; an assumption mismatch or inconclusive result is `CAS_CONFLICT`.
Registered exceptions may produce `CAS_PASS_WITH_REGISTERED_EXCEPTION`, but
that status never satisfies the claim-promotion CAS component.

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

# Canonical computer-algebra axes, plus Rocq (Coq) as an opt-in,
# kernel-independent proof-assistant lineage running in parallel with Lean.
CANONICAL_AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
ALL_KNOWN_AXES = CANONICAL_AXES + ("rocq",)
AXES = ALL_KNOWN_AXES  # recognized axis vocabulary
RISK_AXIS_COUNTS = {"R0": 0, "R1": 1, "R2": 2, "R3": 4}
# Contract axis-name aliases -> internal probe/axis names.
CONTRACT_AXIS_ALIASES = {
    "wolfram_xact": "wolfram_xact",
    "sympy": "sympy",
    "sympy_high_precision": "sympy",
    "sage_singular": "sage_singular",
    "lean": "lean",
    "lean_mathlib": "lean",
    "rocq": "rocq",
    "rocq_stdlib": "rocq",
    "coq": "rocq",
}
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


_WOLFRAM_LICENSE_MARKERS = (
    "not activated",
    "license-related problem",
    "license checkout failed",
    "license manager",
    "licensing error",
    "activation key",
    "with the -activate option",
)


def _classify_wolfram_probe_failure(exit_code: int, transcript: str) -> str:
    """Separate host/licensing blockers from a missing xAct installation.

    ``wolframscript`` commonly returns 255 for an unactivated engine.  Exit
    code alone therefore cannot distinguish a licensing failure from a
    Wolfram-language/package error.  The engine's own bounded transcript is
    the fail-closed discriminator.
    """

    if exit_code in (127, 124):
        return "BLOCKED_PLATFORM_OR_LICENSE"
    normalized = str(transcript).casefold()
    if any(marker in normalized for marker in _WOLFRAM_LICENSE_MARKERS):
        return "BLOCKED_PLATFORM_OR_LICENSE"
    return "BLOCKED_PACKAGE_UNAVAILABLE"


def _probe_wolfram(repo: Path) -> dict:
    code = 'Print[$VersionNumber]; Needs["xAct`xTensor`"]; Print["XACT_LOAD_OK"]; Exit[0]'
    exit_code, out = _run(["wolframscript", "-code", code], timeout=120)
    ready = exit_code == 0 and "XACT_LOAD_OK" in out
    return {
        "status": (
            "PASS"
            if ready
            else _classify_wolfram_probe_failure(exit_code, out)
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


def _probe_rocq(repo: Path) -> dict:
    # Rocq (Coq) proof assistant; a repo-pinned formal_rocq/rocq-toolchain
    # is used when present, else the host rocq/coqc is probed for readiness.
    toolchain_file = repo / "formal_rocq" / "rocq-toolchain"
    pinned = toolchain_file.read_text(encoding="utf-8").strip() if toolchain_file.is_file() else None
    binary = "rocq" if _run(["rocq", "--version"], timeout=60)[0] != 127 else "coqc"
    version_cmd = ["rocq", "--version"] if binary == "rocq" else ["coqc", "--version"]
    exit_code, out = _run(version_cmd, timeout=120)
    ready = exit_code == 0 and ("Rocq" in out or "Coq" in out)
    receipt = {
        "status": "PASS" if ready else (
            "BLOCKED_PLATFORM_OR_LICENSE" if exit_code in (127, 124)
            else "BLOCKED_PACKAGE_UNAVAILABLE"
        ),
        "commands": [{"cmd": f"{binary} --version", "exit": exit_code}],
        "transcript_tail": out[-800:],
    }
    if pinned:
        receipt["pinned_toolchain"] = pinned
    return receipt


PROBES = {
    "wolfram_xact": _probe_wolfram,
    "sympy": _probe_sympy,
    "sage_singular": _probe_sage_singular,
    "lean": _probe_lean,
    "rocq": _probe_rocq,
}


def _required_axes(contract: dict) -> list[str]:
    """The axes a contract mandates, normalized to internal names.

    Legacy contracts without a risk tier retain their explicit canonical
    four/five-axis behavior. New reduced-axis contracts must declare the
    risk tier that justifies their 0/1/2-axis selection.
    """
    if "required_axes" not in contract:
        declared = list(CANONICAL_AXES)
    else:
        declared = contract["required_axes"]
    if not isinstance(declared, list):
        raise ValueError("contract required_axes must be an array")
    normalized: list[str] = []
    for name in declared:
        internal = CONTRACT_AXIS_ALIASES.get(str(name))
        if internal is None:
            raise ValueError(f"contract requires unknown axis {name!r}")
        if internal in normalized:
            raise ValueError(f"contract repeats required axis {internal!r}")
        normalized.append(internal)

    risk_tier = contract.get("risk_tier")
    if risk_tier is None:
        normalized_set = set(normalized)
        if normalized_set == set(CANONICAL_AXES):
            return list(CANONICAL_AXES)
        if normalized_set == set(ALL_KNOWN_AXES):
            return list(ALL_KNOWN_AXES)
        raise ValueError(
            "reduced-axis contracts must declare risk_tier R0, R1, or R2"
        )
    if risk_tier not in RISK_AXIS_COUNTS:
        raise ValueError(
            f"contract risk_tier must be one of {list(RISK_AXIS_COUNTS)}"
        )

    expected = RISK_AXIS_COUNTS[risk_tier]
    if risk_tier == "R3":
        normalized_set = set(normalized)
        if normalized_set == set(CANONICAL_AXES):
            return list(CANONICAL_AXES)
        if normalized_set == set(ALL_KNOWN_AXES):
            return list(ALL_KNOWN_AXES)
        raise ValueError(
            "R3 contracts require the canonical four axes; Rocq may be added "
            "only by naming it explicitly in required_axes"
        )
    if len(normalized) != expected:
        raise ValueError(
            f"{risk_tier} contracts require exactly {expected} CAS axes"
        )
    return normalized


def _risk_tier(contract: dict) -> str:
    """Return the declared tier, treating frozen legacy contracts as R3."""

    tier = contract.get("risk_tier", "R3")
    return tier if tier in RISK_AXIS_COUNTS else "R3"


def _pass_status(contract: dict, required: list[str]) -> str:
    """Use bounded states for reduced tiers, not new axis-count authority labels."""

    tier = _risk_tier(contract)
    if tier == "R0":
        return "NOT_APPLICABLE"
    if tier in {"R1", "R2"}:
        return "PASS"
    return "CAS_5AXIS_PASS" if "rocq" in required else "CAS_4AXIS_PASS"


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
    print(
        json.dumps(
            {
                "ok": True,
                "axis": result["axis"],
                "status": result["status"],
                "verification_state": "STORED_ENVELOPE_ONLY",
                "claim_promotion_cas_eligible": False,
            }
        )
    )
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


def _aggregate_results(
    contract: dict,
    contract_sha: str,
    results: dict[str, dict],
    initial_errors: list[str] | None = None,
    required_axes: list[str] | None = None,
) -> tuple[dict, str]:
    """Apply the shared no-majority-vote aggregate state machine."""

    errors = list(initial_errors or [])
    exceptions, exception_errors = _validate_exceptions(contract, results)
    errors.extend(exception_errors)

    if required_axes is None:
        try:
            required = _required_axes(contract)
        except ValueError as exc:
            errors.append(str(exc))
            required = list(CANONICAL_AXES)
    else:
        required = list(required_axes)
    required_set = set(required)

    statuses = {axis: res.get("status") for axis, res in results.items()}
    missing = [axis for axis in required if axis not in results]
    pass_label = _pass_status(contract, required)

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
        unresolved = (required_set - passing - excepted) | set(missing)
        if conflicted:
            aggregate = "CAS_CONFLICT"
        elif unresolved:
            aggregate = "CAS_BLOCKED"
        elif excepted:
            aggregate = "CAS_PASS_WITH_REGISTERED_EXCEPTION"
        else:
            aggregate = pass_label

    lineage_note = (
        " Lean and Rocq are kernel-independent proof lineages."
        if "rocq" in required
        else ""
    )
    adjudication = {
        "schema_version": 2,
        "contract_id": contract.get("identity", {}).get("contract_id"),
        "contract_sha256": contract_sha,
        "aggregate_status": aggregate,
        "risk_tier": _risk_tier(contract),
        "required_axes": required,
        "axis_statuses": statuses,
        "missing_axes": missing,
        "exceptions_applied": sorted(exceptions),
        "errors": errors,
        "adjudicated_at": _utc_now(),
        "note": (
            f"{pass_label} requires all {len(required)} contract-required axes "
            "to satisfy the risk-scaled contract under one contract hash; "
            f"majority vote is structurally forbidden.{lineage_note}"
        ),
    }
    return adjudication, pass_label


def _emit_adjudication(repo: Path, out: str | None, adjudication: dict) -> None:
    if out:
        dump_json(repo / out, adjudication)
    print(json.dumps(adjudication, indent=2, ensure_ascii=False))


def cmd_adjudicate(args) -> int:
    """Inspect stored envelopes without treating their fields as execution facts."""

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

    adjudication, _ = _aggregate_results(
        contract, contract_sha, results, errors
    )
    replay_status = adjudication["aggregate_status"]
    adjudication.update(
        {
            "evidence_origin": "stored_axis_result_envelopes",
            "claim_promotion_cas_eligible": False,
            "claim_promotion_cas_requirement": "NOT_SATISFIED",
            "historical_aggregate_status": replay_status,
            "aggregate_status": "CAS_BLOCKED",
        }
    )
    adjudication["errors"].append(
        "UNVERIFIED_EXECUTION: serialized axis results are diagnostic "
        "inputs, not parent-observed process execution"
    )
    if args.historical_replay:
        adjudication["verification_state"] = "HISTORICAL_REPLAY"
        adjudication["note"] += (
            " Historical replay reports the frozen computed label only in "
            "historical_aggregate_status; it remains blocked because it is "
            "not runner-observed execution."
        )
    else:
        adjudication["verification_state"] = "UNVERIFIED_EXECUTION"
        adjudication["note"] += (
            " This stored-result assessment is non-authoritative. Use "
            "run-adjudicate for the CAS component of claim promotion."
        )

    adjudication["note"] += (
        " CAS eligibility is one evidence component only; it does not establish "
        "scientific validity, novelty, or overall claim readiness."
    )
    _emit_adjudication(repo, args.out, adjudication)
    return 2


def _repo_directory(repo: Path, value: object, field: str) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, f"{field} must be a non-empty repo-relative directory"
    relative = Path(value)
    if relative.is_absolute():
        return None, f"{field} must be repo-relative"
    resolved = (repo / relative).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return None, f"{field} escapes the repository"
    if not resolved.is_dir():
        return None, f"{field} does not name a directory: {value!r}"
    return resolved, None


def _validate_run_spec(
    repo: Path, run_spec: object, required: list[str]
) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    configs: dict[str, dict] = {}
    if not isinstance(run_spec, dict):
        return configs, ["run spec must be a JSON object"]
    schema_version = run_spec.get("schema_version")
    if type(schema_version) is not int or schema_version != 1:
        errors.append("run spec schema_version must be 1")
    axes = run_spec.get("axes")
    if not isinstance(axes, dict):
        return configs, errors + ["run spec axes must be an object"]

    actual_axes = set(axes)
    required_axes = set(required)
    if actual_axes != required_axes:
        missing = sorted(required_axes - actual_axes)
        extra = sorted(actual_axes - required_axes)
        if missing:
            errors.append(f"run spec is missing required axes: {missing}")
        if extra:
            errors.append(f"run spec contains non-required axes: {extra}")

    for axis in required:
        raw = axes.get(axis)
        if not isinstance(raw, dict):
            errors.append(f"run spec axis {axis} must be an object")
            continue
        argv = raw.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(item, str) for item in argv)
            or not argv[0]
        ):
            errors.append(f"run spec axis {axis} argv must be a non-empty string array")
            continue
        if "shell" in raw:
            errors.append(
                f"run spec axis {axis} must not select a shell; argv is executed directly"
            )
            continue
        timeout = raw.get("timeout_seconds")
        if type(timeout) is not int or timeout <= 0:
            errors.append(
                f"run spec axis {axis} timeout_seconds must be a positive integer"
            )
            continue
        cwd, cwd_error = _repo_directory(repo, raw.get("cwd"), f"axes.{axis}.cwd")
        if cwd_error:
            errors.append(cwd_error)
            continue
        configs[axis] = {
            "argv": list(argv),
            "cwd": cwd,
            "cwd_label": str(raw["cwd"]),
            "timeout_seconds": timeout,
        }
    argv_owners: dict[tuple[str, ...], str] = {}
    for axis, config in configs.items():
        argv_key = tuple(config["argv"])
        owner = argv_owners.get(argv_key)
        if owner is not None:
            errors.append(
                f"run spec axes {owner} and {axis} reuse the same full argv; "
                "each axis must invoke an independently identified command"
            )
        else:
            argv_owners[argv_key] = axis
    return configs, errors


def _contract_obligations(contract: dict) -> tuple[list[str], list[str]]:
    obligations = contract.get("target", {}).get("exact_test_obligations")
    if not isinstance(obligations, list):
        return [], ["contract target.exact_test_obligations must be an array"]
    if not obligations:
        return [], [
            "contract must register at least one exact_test_obligation before "
            "runner-observed execution can promote a claim"
        ]
    if not all(isinstance(item, str) and item for item in obligations):
        return [], ["contract exact_test_obligations must be non-empty strings"]
    if len(set(obligations)) != len(obligations):
        return [], ["contract exact_test_obligations must be unique"]
    return obligations, []


def _coerce_process_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _bounded_probe_result(probe: dict) -> dict:
    commands: list[dict] = []
    raw_commands = probe.get("commands")
    if isinstance(raw_commands, list):
        for raw in raw_commands[:4]:
            if isinstance(raw, dict):
                commands.append(
                    {
                        "cmd": str(raw.get("cmd", ""))[:500],
                        "exit": raw.get("exit"),
                    }
                )
    bounded = {
        "status": probe.get("status"),
        "commands": commands,
        "transcript_tail": str(probe.get("transcript_tail", ""))[-800:],
    }
    if "pinned_toolchain" in probe:
        bounded["pinned_toolchain"] = str(probe["pinned_toolchain"])[:200]
    return bounded


def _probe_blocked_evidence(axis: str, config: dict, probe: dict) -> dict:
    probe_status = probe.get("status")
    status = (
        probe_status
        if probe_status in BLOCKED_STATUSES
        else "BLOCKED_PACKAGE_UNAVAILABLE"
    )
    completed_at = _utc_now()
    return {
        "evidence_origin": "runner_observed_local_subprocess",
        "axis": axis,
        "argv": config["argv"],
        "cwd": config["cwd_label"],
        "timeout_seconds": config["timeout_seconds"],
        "completed_at": completed_at,
        "solver_executed": False,
        "preflight_probe": probe,
        "derived_status": status,
        "errors": [f"parent-owned preflight probe did not PASS: {probe_status!r}"],
    }


def _derive_payload_status(
    contract: dict,
    obligations: list[str],
    payload: object,
    exit_code: int,
) -> tuple[str, list[str]]:
    if not isinstance(payload, dict):
        return "INCONCLUSIVE", ["child stdout JSON must be an object"]

    errors: list[str] = []
    target = contract.get("target", {})
    required_payload_keys = {"checks", "domain_assumption_diff", "counterexample"}
    if "expected_exact_values" in target:
        required_payload_keys.add("computed")
    missing_payload_keys = sorted(required_payload_keys - set(payload))
    structural_error = bool(missing_payload_keys)
    if missing_payload_keys:
        errors.append(f"child payload is missing required keys: {missing_payload_keys}")

    checks = payload.get("checks")
    if not isinstance(checks, dict):
        errors.append("child payload checks must be an object")
        structural_error = True
    else:
        expected_keys = set(obligations)
        actual_keys = set(checks)
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            errors.append(
                "child checks must exactly match contract obligations "
                f"(missing={missing}, extra={extra})"
            )
            structural_error = True
        if any(type(value) is not bool for value in checks.values()):
            errors.append("every child check value must be a JSON boolean")
            structural_error = True

    assumption_diff = payload.get("domain_assumption_diff")
    if not isinstance(assumption_diff, list):
        errors.append("child payload domain_assumption_diff must be an array")
        structural_error = True

    if structural_error:
        return "INCONCLUSIVE", errors
    if assumption_diff:
        errors.append("child reported a non-empty domain_assumption_diff")
        return "MISALIGNED_ASSUMPTIONS", errors

    failed_obligations = sorted(key for key, value in checks.items() if not value)
    if failed_obligations:
        errors.append(f"failed contract obligations: {failed_obligations}")

    expected_mismatch = False
    if "expected_exact_values" in target:
        expected_mismatch = payload.get("computed") != target["expected_exact_values"]
        if expected_mismatch:
            errors.append("child computed values do not match contract expected_exact_values")

    counterexample = payload.get("counterexample")
    if counterexample is not None:
        errors.append("child reported a counterexample")

    if failed_obligations or expected_mismatch or counterexample is not None:
        return "FAIL", errors
    if exit_code != 0:
        errors.append(f"child exited {exit_code} without a validated failure payload")
        return "INCONCLUSIVE", errors
    return "PASS", errors


def _execute_axis(
    contract: dict,
    obligations: list[str],
    axis: str,
    config: dict,
    preflight_probe: dict,
) -> dict:
    started_at = _utc_now()
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    timed_out = False
    launch_error: str | None = None
    try:
        completed = subprocess.run(
            config["argv"],
            cwd=config["cwd"],
            capture_output=True,
            text=True,
            timeout=config["timeout_seconds"],
            check=False,
            shell=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _coerce_process_text(exc.stdout)
        stderr = _coerce_process_text(exc.stderr)
    except OSError as exc:
        launch_error = str(exc)
    completed_at = _utc_now()

    payload: object = None
    validation_errors: list[str] = []
    if launch_error is not None:
        status = "BLOCKED_PACKAGE_UNAVAILABLE"
        validation_errors.append(f"process launch failed: {launch_error}")
    elif timed_out:
        status = "BLOCKED_RESOURCE_LIMIT"
        validation_errors.append("child process exceeded timeout_seconds")
    else:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            status = "INCONCLUSIVE"
            validation_errors.append(f"child stdout is not one JSON document: {exc}")
        else:
            status, validation_errors = _derive_payload_status(
                contract, obligations, payload, int(exit_code)
            )

    selected_payload = (
        {
            key: payload[key]
            for key in (
                "checks",
                "domain_assumption_diff",
                "computed",
                "counterexample",
            )
            if key in payload
        }
        if isinstance(payload, dict)
        else None
    )
    evidence = {
        "evidence_origin": "runner_observed_local_subprocess",
        "axis": axis,
        "argv": config["argv"],
        "cwd": config["cwd_label"],
        "timeout_seconds": config["timeout_seconds"],
        "solver_executed": True,
        "preflight_probe": preflight_probe,
        "started_at": started_at,
        "completed_at": completed_at,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-2000:],
        "derived_status": status,
        "errors": validation_errors,
    }
    if selected_payload is not None:
        evidence["payload"] = selected_payload
    return evidence


def cmd_run_adjudicate(args) -> int:
    """Run all required axes and adjudicate only parent-observed evidence."""

    repo = root()
    contract, contract_sha = _load_contract(repo, args.contract)
    setup_errors: list[str] = []
    try:
        required = _required_axes(contract)
    except ValueError as exc:
        required = list(CANONICAL_AXES)
        setup_errors.append(str(exc))
    obligations: list[str] = []
    if required:
        obligations, obligation_errors = _contract_obligations(contract)
        setup_errors.extend(obligation_errors)
    run_spec = load_json(repo / args.run_spec)
    configs, spec_errors = _validate_run_spec(repo, run_spec, required)
    setup_errors.extend(spec_errors)

    execution_evidence: dict[str, dict] = {}
    results: dict[str, dict] = {}
    if not setup_errors:
        for axis in required:
            preflight_probe = _bounded_probe_result(PROBES[axis](repo))
            if preflight_probe["status"] == "PASS":
                evidence = _execute_axis(
                    contract,
                    obligations,
                    axis,
                    configs[axis],
                    preflight_probe,
                )
            else:
                evidence = _probe_blocked_evidence(
                    axis, configs[axis], preflight_probe
                )
            execution_evidence[axis] = evidence
            results[axis] = {
                "axis": axis,
                "status": evidence["derived_status"],
                "completed_at": evidence["completed_at"],
            }

    adjudication, pass_label = _aggregate_results(
        contract, contract_sha, results, setup_errors, required_axes=required
    )
    successful = adjudication["aggregate_status"] == pass_label
    eligible = successful and _risk_tier(contract) != "R0"
    requirement = (
        "NOT_REQUIRED"
        if _risk_tier(contract) == "R0" and successful
        else "SATISFIED" if eligible
        else "NOT_SATISFIED"
    )
    adjudication.update(
        {
            "verification_state": "RUNNER_OBSERVED_EXECUTION",
            "evidence_origin": "runner_observed_local_subprocess",
            "execution_evidence": execution_evidence,
            "claim_promotion_cas_eligible": eligible,
            "claim_promotion_cas_requirement": requirement,
        }
    )
    if _risk_tier(contract) == "R0" and successful:
        adjudication["note"] += (
            " Runner observation confirms that this contract declares no CAS "
            "requirement; it does not create CAS evidence."
        )
    else:
        adjudication["note"] += (
            " Runner observation establishes only the CAS evidence component; "
            "it does not establish scientific validity, novelty, or overall "
            "claim readiness. Local observation is not a security attestation."
        )
    _emit_adjudication(repo, args.out, adjudication)
    return 0 if successful else 2


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
    adjudicate.add_argument(
        "--historical-replay",
        action="store_true",
        help="report the frozen computed label while keeping primary status blocked",
    )

    run_adjudicate = sub.add_parser("run-adjudicate")
    run_adjudicate.add_argument("--contract", required=True)
    run_adjudicate.add_argument("--run-spec", required=True)
    run_adjudicate.add_argument("--out", default=None)

    args = parser.parse_args()
    if args.command == "preflight":
        sys.exit(cmd_preflight(args))
    if args.command == "check-axis":
        sys.exit(cmd_check_axis(args))
    if args.command == "adjudicate":
        sys.exit(cmd_adjudicate(args))
    sys.exit(cmd_run_adjudicate(args))


if __name__ == "__main__":
    main()
