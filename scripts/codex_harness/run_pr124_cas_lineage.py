#!/usr/bin/env python3
"""PR-124 runner: four-axis CAS contract + derivation-lineage oracle.

Builds (``--write``) or verifies (``--check``) the PR-124 artifact set:

- the CAS contract instance and the four axis result envelopes (running the
  Wolfram, SymPy, Sage, and Lean axis scripts live) plus the cas_gate
  adjudication (``CAS_4AXIS_PASS`` required — no majority vote, three axes
  never pass);
- the typed theorem-signature inventory (honest count; the historical
  65-entry overstatement must FAIL the counting rule);
- the D2 dual-track authority receipt (Python anchor executed live via
  pytest; the Rust MB-95 target execution transcript is consumed hash-bound
  and must be NONZERO — pass ``--run-rust`` to re-execute the Rust test and
  refresh the transcript);
- the MES branch authority table + derivation-lineage receipt (engine
  agreement and derivation independence reported as separate metrics);
- the mutation report: every preregistered mutation from pr124_spec.yaml
  executes and must be KILLED (any survivor blocks the surface).

Claim discipline: everything here is domain/frame-conditional derived
mechanics at roadmap_rescue_v1:C1. No observed result is validated, no
remediation finding changes, and the executed Rust receipt never claims the
dump_dl_spectrum_sparse bit-identical anchor (documented gap).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / ".agent-harness" / "scripts"))

import yaml  # noqa: E402

from common.mes_theorem_authority import (  # noqa: E402
    AUTHORITY_TABLE_PATH,
    BRANCHES,
    CAS_ADJUDICATION_PATH,
    CAS_CONTRACT_PATH,
    D2_RECEIPT_PATH,
    LINEAGE_RECEIPT_PATH,
    MesAuthorityError,
    branch_table_payload,
    count_independent_lineages,
    sha256_file,
    validate_branch_entry,
    validate_claimed_lineage_count,
    validate_d2_receipt,
    verify_authority_receipt,
)
from common.theorem_signatures import (  # noqa: E402
    SIGNATURES_V2_PATH,
    TheoremSignatureError,
    load_signature_registry,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr124_spec.yaml"
THEOREM_INVENTORY_PATH = "docs/generated/pr124_theorem_inventory.json"
MUTATION_REPORT_PATH = "docs/generated/pr124_mutation_report.json"
ARTIFACT_MANIFEST_PATH = "docs/generated/pr124_artifact_manifest.json"
RUST_TRANSCRIPT_PATH = (
    "docs/audits/pr124_d2_authority/rust_test_dl_200k_20260717.log"
)

AXIS_COMMANDS = {
    "sympy": [str(REPO / "venv/bin/python"),
              str(REPO / "htt/src/common/pr124_sympy_axis.py")],
    "wolfram_xact": ["wolframscript", "-file",
                     str(REPO / "wolfram/pr124_mes_geodesic_axis.wls")],
    "sage_singular": ["sage", str(REPO / "sage/pr124_mes_geodesic_axis.sage")],
    "lean": ["bash", "-c",
             f"cd {REPO / 'formal_pr124'} && ~/.elan/bin/lake build >&2 "
             "&& ~/.elan/bin/lake exe pr124mes"],
}

# Axis script sources: hash-recorded in every envelope so script drift is
# detectable at --check time (a PASS envelope for bytes that no longer exist
# on disk is stale, not green).
AXIS_SCRIPT_SOURCES = {
    "sympy": ["htt/src/common/pr124_sympy_axis.py"],
    "wolfram_xact": ["wolfram/pr124_mes_geodesic_axis.wls"],
    "sage_singular": ["sage/pr124_mes_geodesic_axis.sage"],
    "lean": ["formal_pr124/Pr124Mes/Basic.lean", "formal_pr124/Pr124Mes.lean"],
}

# Every axis must emit these computed exact values (partial computed dicts
# get NO partial credit — a missing key is a mismatch).
REQUIRED_COMPUTED_KEYS = (
    "sigma_triple", "omega_triple", "B_sigma_exact", "B_omega_exact",
    "W2_max_exact", "Sigma2_max_exact",
)

EXPECTED_CHECK_KEYS = {
    "sigma_reduction", "omega_reduction", "e1_crit_coefficients",
    "w2_ceiling_exact", "sigma2_ceiling_exact", "hierarchy_e1_zero_strict",
    "hierarchy_observed_fails", "boundary_e1_crit_equality",
}

FORBIDDEN_OUTPUT_LANGUAGE = (
    "four-axis pass therefore theorem true in nature",
    "MES non-geodesic coefficients verified",
    "D2 bit-identical anchor reproduced by this receipt",
    "engine agreement establishes derivation independence",
    "observed anisotropy constrained",
    "Bianchi geometry detected",
    "Bianchi family identified",
    "remediation finding rescued",
    "finding rescued",
    "validated as native",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode("utf-8")


def _load_spec() -> dict:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr124_cas_lineage.v1":
        raise SystemExit("pr124 spec schema mismatch")
    return spec


def _metadata(spec: dict, config_hash: str, input_hashes: list[str]) -> dict:
    return {
        "owner": spec["owner"],
        "contributors": spec["contributors"],
        "implementation_scope": spec["implementation_scope"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": config_hash,
        "input_hashes": sorted(input_hashes),
        "caveats": [
            "Domain/frame-conditional derived mechanics at roadmap_rescue_v1:C1 only.",
            "Engine agreement (four-axis CAS) and derivation independence (lineage oracle) are separate metrics; neither replaces the other.",
            "No observed result is validated; all 102 remediation findings remain OPEN.",
            "The executed Rust receipt does not reproduce the dump_dl_spectrum_sparse bit-identical anchor (documented gap).",
        ],
        "generating_command": (
            f"{REPO / 'venv/bin/python'} scripts/codex_harness/run_pr124_cas_lineage.py --write"
        ),
        "git_commit_or_worktree_state": _worktree_state(),
    }


def _worktree_state() -> str:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True, check=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                           capture_output=True, text=True, check=True)
    return head.stdout.strip() + ("; dirty" if dirty.stdout.strip() else "")


# ---------------------------------------------------------------------------
# CAS contract + axes
# ---------------------------------------------------------------------------

def _build_contract(spec: dict) -> dict:
    cas = spec["cas_contract"]
    return {
        "schema_version": 2,
        "identity": {
            "contract_id": cas["contract_id"],
            "contract_version": 1,
            "claim_ids": [spec["claim_identity"]["claim_id"]],
            "statement_class": cas["statement_class"],
            "source_input_hashes": [
                {"path": rel, "sha256": sha256_file(REPO / rel)}
                for rel in (
                    "docs/audits/mes_primary_sources/mesa_astro-ph_9501016_PRD51_1525.txt",
                    "docs/audits/mes_primary_sources/sag1997_astro-ph_9904346_ApJ476_435.tex",
                )
            ],
            "claim_ceiling": "conditional_C1",
            "adjudicator": "adjudicator",
        },
        "semantics": {
            "exact_statement": cas["exact_statement"],
            "symbol_type_domain_map": {
                "e1,e2,e3": "positive rationals (multipole bound amplitudes)",
                "raw terms": "(coefficient, multipole L, derivative order d)",
            },
            "assumptions": [
                "linearized almost-EGS multipole hierarchy",
                "geodesic congruence (u_dot = 0)",
                "C1/C2 reduction with Theta t_R ~ 3",
                "SAG observer-motion convention for the eps1 attribution",
            ],
            "branches": ["geodesic only; non-geodesic branches are out of contract"],
            "exclusions": ["no observational values; exact rational data only"],
        },
        "target": {
            "canonical_form": (
                "reduced coefficient triples, e1_crit coefficients, exact "
                "ceilings, hierarchy strictness/failure witnesses"
            ),
            "equivalence_relation": "exact rational equality",
            "exact_test_obligations": sorted(EXPECTED_CHECK_KEYS),
            "expected_exact_values": cas["expected_exact_values"],
            "approximation_order": "exact",
            "forbidden_shortcuts": [
                "Do not assume the target identity in an intermediate rewrite.",
                "Do not import sibling solver results before adjudication.",
            ],
        },
        "axes": {
            axis: {
                "applicability": "required",
                "obligation": "independent exact computation from the contract raw data",
                "script": cas["axis_scripts"][axis],
            }
            for axis in ("wolfram_xact", "sympy", "sage_singular", "lean")
        },
        "independence": {
            "mode": "blind-results",
            "script_result_ownership": "per-axis",
            "correlation_disclosure": (
                "all four axis scripts were authored in one LLM-assisted "
                "session (disclosed); engine evidence remains per-engine"
            ),
        },
        "exceptions_adjudication": {
            "preregistered_exceptions": [],
            "aggregate_status_rule": (
                "CAS_4AXIS_PASS | CAS_PASS_WITH_REGISTERED_EXCEPTION | "
                "CAS_CONFLICT | CAS_BLOCKED | CAS_FAIL"
            ),
            "invalidation_triggers": ["contract_hash_change"],
        },
    }


def _run_axis(axis: str, contract_sha: str, expected: dict) -> dict:
    cmd = AXIS_COMMANDS[axis]
    completed = subprocess.run(
        cmd, capture_output=True, text=True, timeout=1800,
        cwd=REPO, check=False,
    )
    payload = None
    for line in reversed(completed.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                payload = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    status = "PASS"
    counterexample = None
    if completed.returncode != 0 or payload is None:
        status = "BLOCKED_PACKAGE_UNAVAILABLE"
    else:
        checks = payload.get("checks", {})
        computed = payload.get("computed") or {}
        if set(checks) != EXPECTED_CHECK_KEYS:
            status = "MISALIGNED_ASSUMPTIONS"
        elif not payload.get("all_pass") or not all(checks.values()):
            status = "FAIL"
            counterexample = {k: v for k, v in checks.items() if not v}
        elif any(key not in computed for key in REQUIRED_COMPUTED_KEYS):
            # partial computed dicts get no partial credit
            status = "MISALIGNED_ASSUMPTIONS"
            counterexample = {
                "missing_computed_keys": [
                    key for key in REQUIRED_COMPUTED_KEYS
                    if key not in computed
                ]
            }
        else:
            mismatches = _computed_mismatches(computed, expected)
            if mismatches:
                status = "FAIL"
                counterexample = {"value_mismatches": mismatches}
    return {
        "schema_version": 1,
        "axis": axis,
        "contract_id": "CAS-PR124-MES-GEODESIC-001",
        "contract_sha256": contract_sha,
        "status": status,
        "commands": [{"cmd": " ".join(cmd), "exit": completed.returncode}],
        "tool_versions": {
            "reported": (payload or {}).get("engine_version", "unavailable")
        },
        "source_output_hashes": [
            {"path": rel, "sha256": sha256_file(REPO / rel),
             "producer": "axis script source"}
            for rel in AXIS_SCRIPT_SOURCES[axis]
        ],
        "domain_assumption_diff": [],
        "evidence_class": "exact",
        "counterexample": counterexample,
        "checks": (payload or {}).get("checks"),
        "computed": (payload or {}).get("computed"),
        "completed_at": _now(),
    }


def _check_axis_envelope(
    envelope: dict, axis: str, contract_sha: str, expected: dict
) -> list[str]:
    """Full envelope re-verification (used at --check AND after --write):
    status, contract binding, check keyset, computed-value agreement, and
    axis-script byte binding. A PASS envelope whose recorded script bytes no
    longer exist on disk is STALE, not green."""
    problems: list[str] = []
    if envelope.get("axis") != axis:
        problems.append("axis label mismatch")
    if envelope.get("status") != "PASS":
        problems.append(f"status {envelope.get('status')!r} is not PASS")
    if envelope.get("contract_sha256") != contract_sha:
        problems.append("bound to a different contract hash (stale)")
    checks = envelope.get("checks")
    if not isinstance(checks, dict) or set(checks) != EXPECTED_CHECK_KEYS:
        problems.append("check keyset differs from the contract obligations")
    elif not all(checks.values()):
        problems.append("a recorded check is false")
    computed = envelope.get("computed")
    if not isinstance(computed, dict):
        problems.append("missing computed exact values")
    else:
        missing = [k for k in REQUIRED_COMPUTED_KEYS if k not in computed]
        if missing:
            problems.append(f"computed values missing keys: {missing}")
        else:
            mismatches = _computed_mismatches(computed, expected)
            if mismatches:
                problems.append(f"computed value mismatches: {mismatches}")
    recorded = envelope.get("source_output_hashes")
    if not isinstance(recorded, list) or not recorded:
        problems.append("no axis-script source hashes recorded")
    else:
        recorded_paths = {row.get("path"): row.get("sha256")
                          for row in recorded}
        for rel in AXIS_SCRIPT_SOURCES[axis]:
            live = sha256_file(REPO / rel) if (REPO / rel).is_file() else None
            if recorded_paths.get(rel) != live:
                problems.append(
                    f"axis script bytes drifted since the envelope: {rel}"
                )
    return problems


def _computed_mismatches(computed: dict, expected: dict) -> dict:
    from fractions import Fraction

    def frac(text: str) -> Fraction:
        return Fraction(str(text))

    mismatches = {}
    pairs = [
        ("sigma_triple", "sigma_triple"),
        ("omega_triple", "omega_triple"),
        ("e1_crit_coefficients", "e1_crit_coefficients"),
        ("B_sigma_exact", "B_sigma_exact"),
        ("B_omega_exact", "B_omega_exact"),
        ("W2_max_exact", "W2_max_exact"),
        ("Sigma2_max_exact", "Sigma2_max_exact"),
    ]
    for ckey, ekey in pairs:
        if ckey not in computed:
            continue
        got, want = computed[ckey], expected[ekey]
        if isinstance(want, list):
            if [frac(g) for g in got] != [frac(w) for w in want]:
                mismatches[ckey] = {"got": got, "want": want}
        else:
            if frac(got) != frac(want):
                mismatches[ckey] = {"got": got, "want": want}
    return mismatches


def _adjudicate(contract_rel: str, axis_rel: dict[str, str]) -> dict:
    cas_gate = REPO / ".agent-harness/scripts/cas_gate.py"
    cmd = [str(REPO / "venv/bin/python"), str(cas_gate), "adjudicate",
           "--historical-replay", "--contract", contract_rel,
           "--results", *axis_rel.values()]
    completed = subprocess.run(cmd, capture_output=True, text=True,
                               cwd=REPO, check=False)
    if not completed.stdout.strip():
        raise SystemExit(f"cas_gate adjudicate produced no output: {completed.stderr}")
    payload = json.loads(completed.stdout)
    payload["gate_exit_code"] = completed.returncode
    return payload


# ---------------------------------------------------------------------------
# D2 receipt
# ---------------------------------------------------------------------------

def _run_rust_target(spec: dict) -> None:
    d2 = spec["d2_authority_contract"]["rust_target"]
    transcript = REPO / RUST_TRANSCRIPT_PATH
    cmd = ("cargo test --release --lib "
           "solver::sync_gauge_camb::test_dl_200k -- --exact --nocapture")
    # the Rust test emits its D_ell table via eprintln! (stderr); merge the
    # streams so the transcript carries both the values and the result line
    completed = subprocess.run(cmd.split(), stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True,
                               cwd=REPO, timeout=1800, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"rust D2 target failed:\n{completed.stdout[-2000:]}")
    body = completed.stdout
    keep = body[body.index("running 1 test"):] if "running 1 test" in body else body
    toolchains = subprocess.run(["cargo", "--version"], capture_output=True,
                                text=True, check=True).stdout.strip()
    rustc = subprocess.run(["rustc", "--version"], capture_output=True,
                           text=True, check=True).stdout.strip()
    transcript.write_text(
        "# PR-124 D2 authority receipt transcript (refreshed)\n"
        f"# command: {cmd}\n"
        f"# toolchain: {toolchains} / {rustc}\n" + keep,
        encoding="utf-8",
    )
    del d2  # spec hashes for source files are checked at receipt-build time


def _parse_rust_transcript(transcript: Path) -> dict:
    text = transcript.read_text(encoding="utf-8")
    d2_match = re.search(r"D_\s*2\s*=\s*([0-9.]+)", text)
    result_match = re.search(
        r"test result: ok\. (\d+) passed; (\d+) failed", text)
    if not d2_match or not result_match:
        raise SystemExit("rust transcript missing D_2 value or result line")
    toolchain_match = re.search(r"# toolchain: (.+)", text)
    return {
        "d2_value_uK2": float(d2_match.group(1)),
        "tests_passed": int(result_match.group(1)),
        "tests_failed": int(result_match.group(2)),
        "tests_collected": int(result_match.group(1)) + int(result_match.group(2)),
        "toolchain": toolchain_match.group(1) if toolchain_match else "",
    }


def _run_python_anchor(spec: dict) -> dict:
    anchor = spec["d2_authority_contract"]["python_anchor"]
    test_rel = anchor["test_path"]
    collect = subprocess.run(
        [str(REPO / "venv/bin/python"), "-B", "-m", "pytest", test_rel,
         "--collect-only", "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=REPO, check=False,
    )
    collected = len([ln for ln in collect.stdout.splitlines()
                     if "::" in ln and not ln.startswith(" ")])
    run = subprocess.run(
        [str(REPO / "venv/bin/python"), "-B", "-m", "pytest", test_rel,
         "-q", "--no-header", "-p", "no:cacheprovider"],
        capture_output=True, text=True, cwd=REPO, check=False,
    )
    passed_match = re.search(r"(\d+) passed", run.stdout)
    passed = int(passed_match.group(1)) if passed_match else 0
    if run.returncode != 0 or passed < 1 or passed != collected:
        raise SystemExit(
            f"python D2 anchor suite not fully green: rc={run.returncode}, "
            f"collected={collected}, passed={passed}\n{run.stdout[-1500:]}"
        )
    return {
        "test_path": test_rel,
        "test_sha256": sha256_file(REPO / test_rel),
        "golden_path": anchor["golden_path"],
        "golden_sha256": sha256_file(REPO / anchor["golden_path"]),
        "tests_collected": collected,
        "tests_passed": passed,
        "bit_identical_rule": "numpy allclose atol=0 rtol=0 (golden-pinned)",
    }


def _build_d2_receipt(spec: dict) -> dict:
    contract = spec["d2_authority_contract"]
    transcript = REPO / RUST_TRANSCRIPT_PATH
    rust = _parse_rust_transcript(transcript)
    rust_row = {
        **rust,
        "command": contract["rust_target"]["command"],
        "source_path": contract["rust_target"]["source_path"],
        "source_sha256": sha256_file(
            REPO / contract["rust_target"]["source_path"]),
        "cargo_manifest_path": "Cargo.toml",
        "cargo_manifest_sha256": sha256_file(REPO / "Cargo.toml"),
        "transcript_path": RUST_TRANSCRIPT_PATH,
        "transcript_sha256": sha256_file(transcript),
        "config_note": (
            "test_dl_200k production-path configuration (lmax_g=16, n_k=200); "
            "NOT the dump_dl_spectrum_sparse anchor configuration"
        ),
    }
    receipt = {
        "schema": "pr124.d2_authority_receipt.v1",
        "rust_target": rust_row,
        "python_anchor": _run_python_anchor(spec),
        "derivation_stream_separation": (
            "Rust MB-95 synchronous-gauge CAMB-convention Boltzmann hierarchy "
            "(Ma-Bertschinger 1995 lineage) vs Python PSTF 1+3 covariant "
            "hierarchy (Ellis-van Elst lineage); the Python route-B anchor "
            "constants are frozen-pinned and bit-identical-enforced"
        ),
        "documented_anchor_gap": spec["d2_authority_contract"][
            "documented_anchor_gap"],
        "transcript_evidence_class": (
            "hash-bound local execution disclosure produced by this runner "
            "(--run-rust); NOT a remote attestation — fabrication is "
            "excluded by process discipline, not cryptography"
        ),
        "pstf_python_closure_status": spec["d2_authority_contract"][
            "pstf_python_closure_status"],
    }
    validate_d2_receipt(receipt, REPO)
    return receipt


# ---------------------------------------------------------------------------
# theorem inventory + lineage receipt + authority table
# ---------------------------------------------------------------------------

def _build_theorem_inventory(spec: dict) -> dict:
    registry = load_signature_registry(REPO)
    overstatement_killed = False
    try:
        registry.reject_overstated_count(registry.legacy_entry_count)
    except TheoremSignatureError:
        overstatement_killed = True
    grades: dict[str, int] = {}
    for entry in registry.entries:
        grades[entry.evidence_grade.value] = (
            grades.get(entry.evidence_grade.value, 0) + 1)
    return {
        "schema": "pr124.theorem_inventory.v1",
        "legacy_entry_count": registry.legacy_entry_count,
        "legacy_registry_sha256": registry.legacy_sha256,
        "signatures_v2_path": SIGNATURES_V2_PATH,
        "signatures_v2_sha256": sha256_file(REPO / SIGNATURES_V2_PATH),
        "honest_theorem_count": registry.theorem_count(),
        "countable_ids": list(registry.countable_ids()),
        "evidence_grade_histogram": dict(sorted(grades.items())),
        "old_overstatement_killed": overstatement_killed,
        "counting_rule_note": (
            "sanity anchors, specifications, numerical tests, superseded/"
            "retracted/withheld/planned entries, and unchecked signatures "
            "never count; engine re-evaluation never adds a derivation"
        ),
    }


def _build_lineage_receipt() -> dict:
    branches = {}
    for branch_id, entry in BRANCHES.items():
        count = count_independent_lineages(entry["lineages"])
        branches[branch_id] = {
            "congruence": entry["congruence"],
            "status": entry["status"],
            "coefficients_exact": list(entry["coefficients_exact"]),
            "lineages": entry["lineages"],
            "independent_derivation_count": count,
        }
        validate_branch_entry(branch_id, branches[branch_id])
    return {
        "schema": "pr124.lineage_receipt.v1",
        "independence_rule": (
            "lineages collapse by implementation_fingerprint; evaluating one "
            "implementation on a second engine never adds a lineage; numeric "
            "spot checks are never proofs"
        ),
        "minimum_lineages_for_verified_branch": 2,
        "branches": branches,
        "metric_separation_note": (
            "this receipt reports DERIVATION INDEPENDENCE; the four-axis CAS "
            "adjudication reports COMPUTATIONAL REPRODUCIBILITY; neither "
            "metric substitutes for the other"
        ),
    }


def _build_authority_table(spec: dict) -> dict:
    bound = {
        rel: sha256_file(REPO / rel)
        for rel in (CAS_ADJUDICATION_PATH, D2_RECEIPT_PATH,
                    LINEAGE_RECEIPT_PATH, THEOREM_INVENTORY_PATH)
    }
    return {
        "schema": "pr124.mes_authority_table.v1",
        "successor_id": "mes.typed-successor.pr124",
        "branch_table": branch_table_payload(),
        "bound_artifacts": bound,
        "legacy_registry_sha256": spec["theorem_signature_contract"][
            "legacy_registry"]["sha256"],
        "authority_scope": (
            "domain/frame-conditional derived mechanics C1; governance "
            "authority for typed MES coefficient consumption; NOT scientific "
            "validation of any observed result"
        ),
    }


# ---------------------------------------------------------------------------
# mutation laboratory (every registered mutant must be KILLED)
# ---------------------------------------------------------------------------

def _run_mutations(spec: dict, d2_receipt: dict) -> list[dict]:
    from fractions import Fraction

    results = []

    def record(mutation_id: str, action) -> None:
        try:
            action()
        except (MesAuthorityError, TheoremSignatureError) as exc:
            results.append({"mutation_id": mutation_id, "executed": True,
                            "killed": True, "kill_message": str(exc)[:200]})
            return
        results.append({"mutation_id": mutation_id, "executed": True,
                        "killed": False, "kill_message": None})

    # 1. stale_triple_reintroduction — the scanner flags a synthetic consumer
    #    carrying the legacy non-geodesic triple as an active literal.
    def stale_triple() -> None:
        import ast as ast_mod
        from common.mes_successor_registry import _stale_triples

        mutant_source = (
            "from common.mes_successor_registry import current_mes_successor_registry\n"
            "_MES_SUCCESSOR = current_mes_successor_registry().successor\n"
            "_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id\n"
            "def B_omega(eps1, eps2, eps3):\n"
            "    return (3/4)*eps1 + 2*eps2 + (2/7)*eps3\n"
        )
        clean_source = (
            "from common.mes_successor_registry import (\n"
            "    current_mes_successor_registry,\n"
            "    legacy_reproduction_coefficients,\n)\n"
            "_MES_SUCCESSOR = current_mes_successor_registry().successor\n"
            "_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id\n"
            "_C1, _C2, _C3 = (float(c) for c in "
            "legacy_reproduction_coefficients()['omega'])\n"
            "def B_omega(eps1, eps2, eps3):\n"
            "    return _C1*eps1 + _C2*eps2 + _C3*eps3\n"
        )
        mutant_hits = _stale_triples(ast_mod.parse(mutant_source))
        clean_hits = _stale_triples(ast_mod.parse(clean_source))
        if clean_hits:
            raise SystemExit("clean twin unexpectedly flagged (scanner broken)")
        if mutant_hits:
            raise MesAuthorityError(
                f"stale triple reintroduction detected: {sorted(mutant_hits)}"
            )

    # 2. branch_swap — geodesic coefficients presented under MES_NG.
    def branch_swap() -> None:
        entry = {
            "congruence": "non_geodesic",
            "status": "UNVERIFIED_PRINT_ONLY",
            "coefficients_exact": ["10/3", "2/15", "0"],  # geodesic values!
            "independent_derivation_count": 1,
        }
        validate_branch_entry("MES_NG_OMEGA", entry)

    # 3. source_count_inflation — same implementation fingerprint under two
    #    engine names claimed as two derivations.
    def inflation() -> None:
        lineages = [
            {"lineage_id": "reduction_on_sympy", "kind": "in_repo_reduction",
             "implementation_fingerprint": "same_reduction_v1"},
            {"lineage_id": "reduction_on_wolfram", "kind": "in_repo_reduction",
             "implementation_fingerprint": "same_reduction_v1"},
        ]
        validate_claimed_lineage_count(lineages, 2)

    # 4. zero_d2_receipt — a zero executed value must be rejected.
    def zero_d2() -> None:
        mutant = json.loads(json.dumps(d2_receipt))
        mutant["rust_target"]["d2_value_uK2"] = 0.0
        validate_d2_receipt(mutant, REPO)

    # 5. sign_flip_reduction — (-1/3)^order reduction factor corrupts the
    #    omega triple. KILLED BY THE REAL VALIDATOR: validate_branch_entry
    #    rejects a branch entry carrying the mutant triple (the same
    #    validator every lineage-receipt row must pass).
    def sign_flip() -> None:
        acc = {1: Fraction(0), 2: Fraction(0), 3: Fraction(0)}
        raw_omega = [(Fraction(9), 1, 1), (Fraction(3), 1, 2),
                     (Fraction(6, 5), 2, 2)]
        for coeff, ell, order in raw_omega:
            acc[ell] += coeff * Fraction(-1, 3) ** order
        mutant_entry = {
            "congruence": "geodesic",
            "status": "VERIFIED",
            "coefficients_exact": [str(acc[1]), str(acc[2]), str(acc[3])],
            "independent_derivation_count": 3,
        }
        validate_branch_entry("MES_G_OMEGA", mutant_entry)

    # 6. unit_w2_normalization — (1/2)B^2 instead of (3/2)B^2. KILLED BY THE
    #    REAL VALIDATOR: validate_ceiling_map is the production ceiling-map
    #    check the authority verification runs on the adjudicated values.
    def unit_mutation() -> None:
        from common.mes_theorem_authority import validate_ceiling_map

        b_omega = Fraction(1186543, 2500000000000)
        mutant_w2 = Fraction(1, 2) * b_omega ** 2
        validate_ceiling_map(str(b_omega), str(mutant_w2))

    # 7. limit_eps1_domain — accepting e1 == e1_crit (boundary) is wrong:
    #    the hierarchy is strict only STRICTLY below e1_crit. KILLED BY THE
    #    REAL VALIDATOR: validate_hierarchy_strict raises at the exact
    #    boundary (the mutant claims the boundary is admissible).
    def limit_mutation() -> None:
        from common.mes_theorem_authority import validate_hierarchy_strict

        e2 = Fraction(3559629, 10**12)
        e3 = Fraction(6065291, 10**12)
        e1_crit = Fraction(43, 25) * e2 + Fraction(9, 35) * e3
        validate_hierarchy_strict(str(e1_crit), str(e2), str(e3))

    # 8. overstatement_theorem_count — the 65-entry quote must fail.
    def overstatement() -> None:
        registry = load_signature_registry(REPO)
        registry.reject_overstated_count(registry.legacy_entry_count)

    record("stale_triple_reintroduction", stale_triple)
    record("branch_swap", branch_swap)
    record("source_count_inflation", inflation)
    record("zero_d2_receipt", zero_d2)
    record("sign_flip_reduction", sign_flip)
    record("unit_w2_normalization", unit_mutation)
    record("limit_eps1_domain", limit_mutation)
    record("overstatement_theorem_count", overstatement)

    registered_ids = [m["mutation_id"] for m in spec["mutation_registry"]]
    executed_ids = [m["mutation_id"] for m in results]
    if executed_ids != registered_ids:
        raise SystemExit(
            f"mutation set drifted: registered {registered_ids} vs "
            f"executed {executed_ids}"
        )
    return results


# ---------------------------------------------------------------------------
# main build/check
# ---------------------------------------------------------------------------

def _write_if_changed(rel: str, payload: dict, wrote: list[str]) -> None:
    """Atomic write, but keep bytes stable when semantic content (excluding
    volatile fields) is unchanged (H7 discipline)."""
    target = REPO / rel
    rendered = _render(payload)
    if target.is_file():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = None
        if existing is not None and _semantic(existing) == _semantic(payload):
            return
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(rendered)
    tmp.replace(target)
    wrote.append(rel)


_VOLATILE_KEYS = {"completed_at", "adjudicated_at", "generated_at",
                  "git_commit_or_worktree_state"}


def _semantic(payload):
    if isinstance(payload, dict):
        return {k: _semantic(v) for k, v in payload.items()
                if k not in _VOLATILE_KEYS}
    if isinstance(payload, list):
        return [_semantic(v) for v in payload]
    return payload


def _emit(rel: str, payload: dict, write: bool, wrote: list[str],
          problems: list[str]) -> None:
    """Write mode: atomic write-if-changed. Check mode: the freshly built
    payload must semantically equal the on-disk artifact (nothing is
    trusted wholesale; volatile keys excluded)."""
    if write:
        _write_if_changed(rel, payload, wrote)
        return
    target = REPO / rel
    if not target.is_file():
        problems.append(f"missing artifact: {rel}")
        return
    try:
        existing = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        problems.append(f"invalid JSON artifact: {rel}")
        return
    if _semantic(existing) != _semantic(payload):
        problems.append(f"stale artifact (differs from a fresh build): {rel}")


def _check_pin_consistency() -> list[str]:
    """The module pins in mes_successor_registry must match the live bytes;
    a green runner with silently stale pins is a cross-gate inconsistency
    window."""
    from common.mes_successor_registry import (
        PR124_AUTHORITY_RECEIPT_SHA256,
        PR124_AUTHORITY_SOURCE_SHA256,
    )

    problems = []
    live_receipt = sha256_file(REPO / AUTHORITY_TABLE_PATH)
    live_source = sha256_file(REPO / "htt/src/common/mes_theorem_authority.py")
    if live_receipt != PR124_AUTHORITY_RECEIPT_SHA256:
        problems.append(
            "authority receipt pin stale: update "
            f"PR124_AUTHORITY_RECEIPT_SHA256 to {live_receipt}"
        )
    if live_source != PR124_AUTHORITY_SOURCE_SHA256:
        problems.append(
            "authority source pin stale: update "
            f"PR124_AUTHORITY_SOURCE_SHA256 to {live_source}"
        )
    return problems


def build(write: bool, run_rust: bool) -> int:
    spec = _load_spec()
    spec_hash = sha256_file(SPEC_PATH)
    wrote: list[str] = []
    problems: list[str] = []

    if run_rust:
        if not write:
            raise SystemExit("--run-rust requires --write")
        _run_rust_target(spec)

    # 1. contract (check mode: the on-disk contract must equal a fresh build)
    contract = _build_contract(spec)
    _emit(CAS_CONTRACT_PATH, contract, write, wrote, problems)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2
    contract_sha = sha256_file(REPO / CAS_CONTRACT_PATH)

    # 2. axes + adjudication. Write mode runs the four engines live; BOTH
    #    modes then re-verify every envelope (status, contract binding,
    #    check keyset, computed exact values, axis-script byte binding).
    axis_rel = {
        axis: f"docs/generated/pr124_cas/axis_result_{axis}.json"
        for axis in ("wolfram_xact", "sympy", "sage_singular", "lean")
    }
    expected = spec["cas_contract"]["expected_exact_values"]
    if write:
        for axis, rel in axis_rel.items():
            envelope = _run_axis(axis, contract_sha, expected)
            target = REPO / rel
            if envelope["status"] != "PASS" and target.is_file():
                try:
                    existing = json.loads(target.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    existing = {}
                if existing.get("status") == "PASS":
                    print(json.dumps({
                        "ok": False,
                        "reason": (
                            f"axis {axis} did not PASS "
                            f"({envelope['status']}); refusing to clobber "
                            "the existing PASS envelope — fix the engine "
                            "or the axis script first"
                        ),
                    }))
                    return 2
            _write_if_changed(rel, envelope, wrote)
        adjudication = _adjudicate(CAS_CONTRACT_PATH, axis_rel)
        # The frozen v1 adjudication remains a reproducibility artifact.  A
        # stored-envelope replay may check its historical verdict, but must
        # not mint or overwrite a claim-promotion-shaped CAS pass.
        if (
            adjudication.get("gate_exit_code") != 2
            or adjudication.get("verification_state") != "HISTORICAL_REPLAY"
            or adjudication.get("aggregate_status") != "CAS_BLOCKED"
            or adjudication.get("historical_aggregate_status")
            != "CAS_4AXIS_PASS"
            or adjudication.get("claim_promotion_cas_requirement")
            != "NOT_SATISFIED"
        ):
            problems.append(
                "stored-envelope replay did not reproduce the historical "
                "CAS_4AXIS_PASS as a non-promotable diagnostic"
            )
    for axis, rel in axis_rel.items():
        target = REPO / rel
        if not target.is_file():
            problems.append(f"missing axis envelope: {rel}")
            continue
        envelope = json.loads(target.read_text(encoding="utf-8"))
        for problem in _check_axis_envelope(envelope, axis, contract_sha,
                                            expected):
            problems.append(f"{rel}: {problem}")
    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2
    adjudication = json.loads(
        (REPO / CAS_ADJUDICATION_PATH).read_text(encoding="utf-8"))
    if (
        adjudication.get("aggregate_status") != "CAS_4AXIS_PASS"
        or adjudication.get("contract_sha256") != contract_sha
        or adjudication.get("errors")
        or adjudication.get("missing_axes")
    ):
        print(json.dumps({"ok": False,
                          "reason": "CAS adjudication is not a clean "
                                    "CAS_4AXIS_PASS bound to this contract",
                          "aggregate": adjudication.get("aggregate_status")}))
        return 2

    # 3. theorem inventory
    inventory = _build_theorem_inventory(spec)
    _emit(THEOREM_INVENTORY_PATH, inventory, write, wrote, problems)

    # 4. D2 receipt (python anchor executes live in both modes)
    d2_receipt = _build_d2_receipt(spec)
    _emit(D2_RECEIPT_PATH, d2_receipt, write, wrote, problems)

    # 5. lineage receipt
    lineage = _build_lineage_receipt()
    _emit(LINEAGE_RECEIPT_PATH, lineage, write, wrote, problems)

    # 6. mutations (all must be killed, by the REAL validators)
    mutation_rows = _run_mutations(spec, d2_receipt)
    survivors = [m for m in mutation_rows if not m["killed"]]
    mutation_report = {
        "schema": "pr124.mutation_report.v1",
        "mutations": mutation_rows,
        "surviving_mutation_count": len(survivors),
        "survivor_rule": "every survivor blocks its surface",
    }
    _emit(MUTATION_REPORT_PATH, mutation_report, write, wrote, problems)
    if survivors:
        print(json.dumps({"ok": False, "survivors": survivors}))
        return 2

    # 7. authority table (binds artifact hashes)
    table = _build_authority_table(spec)
    _emit(AUTHORITY_TABLE_PATH, table, write, wrote, problems)

    # 8. manifest
    outputs = list(spec["artifact_contract"]["outputs"])
    manifest_inputs = [
        f"{SPEC_PATH.relative_to(REPO).as_posix()}:{spec_hash}",
        f"{RUST_TRANSCRIPT_PATH}:{sha256_file(REPO / RUST_TRANSCRIPT_PATH)}",
    ]
    manifest = {
        "schema": "pr124.artifact_manifest.v1",
        **_metadata(spec, spec_hash, manifest_inputs),
        "artifacts": {
            rel: sha256_file(REPO / rel)
            for rel in outputs if rel != ARTIFACT_MANIFEST_PATH
        },
    }
    _emit(ARTIFACT_MANIFEST_PATH, manifest, write, wrote, problems)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2

    # 9. full authority verification (the same check the successor uses)
    try:
        verification = verify_authority_receipt(REPO)
    except MesAuthorityError as exc:
        print(json.dumps({"ok": False,
                          "reason": f"authority verification failed: {exc}"}))
        return 2

    # 10. forbidden-language lint over every artifact (the manifest's own
    #     forbidden_use registry is the phrase list, not a violation)
    for rel in outputs:
        payload = json.loads((REPO / rel).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.pop("forbidden_use", None)
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in FORBIDDEN_OUTPUT_LANGUAGE:
            if phrase in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}: {phrase}"}))
                return 2

    # 11. module pin consistency — a green runner must never coexist with
    #     silently stale successor pins
    pin_problems = _check_pin_consistency()
    if pin_problems:
        print(json.dumps({"ok": False, "problems": pin_problems,
                          "note": ("regeneration changed the receipt bytes; "
                                   "re-pin mes_successor_registry.py and "
                                   "re-run --check")}))
        return 2

    summary = {
        "ok": True,
        "mode": "write" if write else "check",
        "wrote": wrote,
        "cas_aggregate": adjudication["aggregate_status"],
        "honest_theorem_count": inventory["honest_theorem_count"],
        "d2_value_uK2": d2_receipt["rust_target"]["d2_value_uK2"],
        "surviving_mutations": 0,
        "authority_receipt_sha256": verification.receipt_sha256,
    }
    print(json.dumps(summary, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--run-rust", action="store_true",
                        help="re-execute the Rust D2 target (refreshes the transcript)")
    args = parser.parse_args()
    sys.exit(build(write=args.write, run_rust=args.run_rust))


if __name__ == "__main__":
    main()
