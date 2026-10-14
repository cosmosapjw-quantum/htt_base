#!/usr/bin/python3.12
"""Execute only the frozen CAS-02 Wolfram+xTensor C01--C03 axis."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
UNIT = Path("docs/research_program/gr_statistics_loops_20260930/local_cas/") / (
    "GRSTAT-CAS-20260930-1308KST/CAS-02/c01_c03_input_aligned_v1_20261005"
)
AXIS = UNIT / "wolfram_xact"
SOURCE = REPO / AXIS / "proof.wl"
FROZEN = {
    UNIT / "EXECUTION_CONTRACT.json": "f1df856a0da477256e8adfbb889001d75fd659dda6f834ea72e87f314ff844a8",
    UNIT / "ADMITTED_INPUTS.json": "e7cfe79d7ad075899ee75f166687f40363e207ba334da3d8733fa2ab5a4b82bd",
    Path("docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    Path(".agent-harness/scripts/cas_gate.py"): "fcaaa08083221fa69ff22066d6fb9f769913bd774b15628dbf684544c69f0744",
}
OBLIGATIONS = ("CAS-02-C01", "CAS-02-C02", "CAS-02-C03")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    if Path.cwd().resolve() != REPO.resolve():
        print(json.dumps({"error": "runner requires frozen repository cwd"}))
        return 2
    started = utc()
    attempt = REPO / AXIS / "attempts" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt.mkdir(parents=True, exist_ok=False)
    before = {str(p): sha(REPO / p) for p in FROZEN}
    source_before = sha(SOURCE)
    runner_before = sha(Path(__file__))
    snapshot = attempt / "proof.wl"
    shutil.copyfile(SOURCE, snapshot)
    snapshot_sha = sha(snapshot)
    runner_snapshot = attempt / "run.py"
    shutil.copyfile(Path(__file__), runner_snapshot)
    runner_snapshot_sha = sha(runner_snapshot)
    argv = ["wolframscript", "-file", str(snapshot)]
    exit_code = None
    timed_out = False
    launch_error = None
    try:
        proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                              timeout=1800, check=False)
        exit_code = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    except OSError as exc:
        launch_error = repr(exc)
        stdout, stderr = "", launch_error
    (attempt / "wolfram.stdout.log").write_text(stdout)
    (attempt / "wolfram.stderr.log").write_text(stderr)
    after = {str(p): sha(REPO / p) for p in FROZEN}
    source_after = sha(SOURCE)
    runner_after = sha(Path(__file__))
    lines = [line[len("CAS_JSON:"):] for line in stdout.splitlines() if line.startswith("CAS_JSON:")]
    parsed = None
    parse_error = None
    if len(lines) == 1:
        try:
            parsed = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    else:
        parse_error = f"expected one CAS_JSON line, got {len(lines)}"
    messages = re.findall(r"\b[A-Za-z][A-Za-z0-9`]*::[A-Za-z][A-Za-z0-9]*\b", stdout + "\n" + stderr)
    checks = (parsed or {}).get("checks", {})
    exact = (
        parsed is not None and set(checks) == set(OBLIGATIONS)
        and all(checks.get(k) is True for k in OBLIGATIONS)
        and exit_code == 0 and not timed_out and launch_error is None
        and not messages and all(before[str(p)] == digest for p, digest in FROZEN.items())
        and before == after and source_before == source_after == snapshot_sha
        and runner_before == runner_after == runner_snapshot_sha
    )
    first_gap = None
    if not exact:
        if any(before[str(p)] != digest for p, digest in FROZEN.items()):
            first_gap = "frozen input hash mismatch before engine execution"
        elif source_before != snapshot_sha or source_before != source_after or before != after or runner_before != runner_after or runner_before != runner_snapshot_sha:
            first_gap = "source or frozen input changed during engine execution"
        elif launch_error or timed_out:
            first_gap = launch_error or "Wolfram engine timeout"
        elif parse_error:
            first_gap = parse_error
        elif messages:
            first_gap = f"Wolfram messages: {messages}"
        elif exit_code != 0:
            first_gap = f"Wolfram exit {exit_code}"
        else:
            first_gap = "one or more exact component checks did not establish target"
    execution = {
        "started_at": started, "completed_at": utc(), "argv": argv,
        "cwd": str(REPO), "timeout_seconds": 1800, "exit_code": exit_code,
        "timed_out": timed_out, "launch_error": launch_error,
        "source_path": str(SOURCE.relative_to(REPO)), "source_sha256_before": source_before,
        "source_sha256_after": source_after, "snapshot_path": str(snapshot.relative_to(REPO)),
        "snapshot_sha256": snapshot_sha, "input_hashes_before": before,
        "runner_sha256_before": runner_before, "runner_sha256_after": runner_after,
        "runner_snapshot_path": str(runner_snapshot.relative_to(REPO)),
        "runner_snapshot_sha256": runner_snapshot_sha,
        "input_hashes_after": after, "wolfram_messages": messages,
        "parse_error": parse_error, "first_gap": first_gap,
        "stdout_path": str((attempt / "wolfram.stdout.log").relative_to(REPO)),
        "stderr_path": str((attempt / "wolfram.stderr.log").relative_to(REPO)),
    }
    (attempt / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    result = {
        "axis": "wolfram_xact", "status": "PASS" if exact else "INCONCLUSIVE",
        "contract_sha256": FROZEN[UNIT / "EXECUTION_CONTRACT.json"],
        "evidence_class": "exact", "completed_at": execution["completed_at"],
        "commands": [execution], "component_checks": checks,
        "domain_assumption_diff": [], "counterexample": None,
        "statement_alignment": {
            "CAS-02-C01": "arbitrary pair of optical S embeddings with symmetric tracefree h2; positive Euclidean squared Frobenius and metric norm",
            "CAS-02-C02": "both universal finite quadratic anchors, coordinate polynomial and xTensor abstract contractions",
            "CAS-02-C03": "actual positive-root real chart derivative, Gram spectrum including d=0 and pointwise radius bound",
        },
        "engine_contributions": {
            "wolfram": "C01 coordinate polynomial; C02 symmetric coordinate polynomial; C03 actual D, Gram, characteristic polynomial, exact rational and hyperbolic bound",
            "xTensor": "C02 two nonzero pre-canonical anchor residuals using symmetry-equivalent covariant slot order, each reduced to zero by ToCanonical",
        },
        "engine_versions": {k: (parsed or {}).get(k) for k in ("wolfram_version", "xtensor_version")},
        "details": (parsed or {}).get("details"), "first_gap": first_gap,
        "excluded": {"CAS-02-C04": "NEEDS_OWNER_DECISION"},
        "scientific_admission": "HOLD",
    }
    result_bytes = json.dumps(result, indent=2) + "\n"
    (attempt / "result.json").write_text(result_bytes)
    (REPO / AXIS / "result.json").write_text(result_bytes)
    payload = {"checks": {k: checks.get(k) is True for k in OBLIGATIONS},
               "domain_assumption_diff": [], "counterexample": None}
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if exact else 2


if __name__ == "__main__":
    sys.exit(main())
