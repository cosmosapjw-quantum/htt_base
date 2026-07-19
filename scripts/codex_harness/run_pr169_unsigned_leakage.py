#!/usr/bin/env python3
"""Build or byte-check the exact PR-169 algebraic-only result pack."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "scripts" / "codex_harness"))

from common.unsigned_isotropy_leakage import (  # noqa: E402
    QuadraticSectorSymbol,
    ReceiptStatus,
    UnsignedLeakageError,
    adjudicate_physical_bundle,
    classify_pr127_evidence,
    clip_signed_curvature,
    exact_ceiling_receipt,
    full_saturating_point,
    require_no_unresolved_consumer_hits,
    require_typed_symbol_bridge,
    route_terminal_result,
    sign_mutant_x_c,
    slice_saturating_point,
)
from pr167_intake_contract import semantic_sha256  # noqa: E402


SPEC = Path("docs/research_program/long_horizon_rescue/pr169_spec.yaml")
PROVENANCE = Path(
    "docs/research_program/long_horizon_rescue/"
    "pr169_primary_source_provenance.yaml"
)
CONTRACT_V1 = Path(
    "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE.json"
)
CONTRACT_V2 = Path(
    "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE_V2.json"
)
COLLECTION = Path("docs/generated/pr169_cas_collection_receipt.json")
ADJ_V1 = Path("docs/generated/pr169_cas/adjudication_v1.json")
ADJ_V2 = Path("docs/generated/pr169_cas/adjudication_v2.json")
RUNNER = Path("scripts/codex_harness/run_pr169_unsigned_leakage.py")
OUTPUTS = {
    "ceiling": Path("docs/generated/pr169_exact_ceiling.json"),
    "physical": Path("docs/generated/pr169_physical_admissibility.json"),
    "supersession": Path("docs/generated/pr169_candidate_branch_supersession.json"),
    "consumers": Path("docs/generated/pr169_all_consumer_scan.json"),
    "mutations": Path("docs/generated/pr169_mutation_report.json"),
    "result": Path("docs/generated/pr169_result_card.json"),
    "manifest": Path("docs/generated/pr169_artifact_manifest.json"),
}
AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
REQUIRED_METADATA = {
    "owner",
    "implementation_scope",
    "claim_tier",
    "claim_level",
    "artifact_mode",
    "allowed_use",
    "forbidden_use",
    "transfer_source",
    "config_hash",
    "input_hashes",
    "sky_support_status",
    "mask_status",
    "covariance_status",
    "null_mock_status",
    "caveats",
    "generating_command",
    "runtime_environment",
    "git_commit",
    "worktree_state",
}

_TOKEN = re.compile(r"x_C|\bxC\b|\bW2\b|W\^2|W_N2|Weyl|vorticity", re.I)
_RISK_PATTERNS = {
    "order_independent_vorticity": re.compile(
        r"(?:order[-_ ]independent.{0,180}(?:W2|W\^2|vorticity)|"
        r"(?:W2|W\^2|vorticity).{0,180}order[-_ ]independent)",
        re.I | re.S,
    ),
    "signed_scalar_isotropy_promotion": re.compile(
        r"(?:x_C|\bxC\b)[^.;\n]{0,180}(?:proves?|certif(?:y|ies)|"
        r"recovers?|implies|supports?|indicates?|entails?|suffices?\s+for|"
        r"is\s+(?:an?\s+)?(?:certificate|proof|criterion))"
        r"[^.;\n]{0,100}(?:FLRW|isotrop|almost[-_ ]?EGS)|"
        r"(?:FLRW|isotrop|almost[-_ ]?EGS)[^.;\n]{0,140}"
        r"(?:follows?\s+from|is\s+(?:proved|certified|implied)\s+by)"
        r"[^.;\n]{0,80}(?:x_C|\bxC\b)",
        re.I | re.S,
    ),
    "signed_scalar_global_promotion": re.compile(
        r"(?:x_C|\bxC\b)[^.;\n]{0,120}(?:"
        r"(?:scalar\s+)?measure\s+of\s+FLRW\s+departure|"
        r"(?:constrains?|bounds?|measures?|quantifies?)\s+"
        r"(?:the\s+)?(?:global\s+)?anisotropy)",
        re.I | re.S,
    ),
    "tilt_only_flrw_promotion": re.compile(
        r"(?:vanishing|zero|absence\s+of)[^.;\n]{0,60}"
        r"(?:displacement|tilt)[^.;\n]{0,120}"
        r"(?:guarantees?|proves?|implies|recovers?|certifies?|entails?)"
        r"[^.;\n]{0,80}FLRW|"
        r"FLRW[^.;\n]{0,100}(?:follows?\s+from|is\s+guaranteed\s+by)"
        r"[^.;\n]{0,60}(?:vanishing|zero)[^.;\n]{0,40}"
        r"(?:displacement|tilt)",
        re.I | re.S,
    ),
    "weyl_blind_vorticity_promotion": re.compile(
        r"CMB.{0,40}curl/Weyl[-_ ]blind", re.I | re.S
    ),
    "nilsson_symbol_conflation": re.compile(
        r"(?:W_N2\s*(?:=|->|maps?\s+to|is\s+(?:identical|equivalent|"
        r"the\s+same)\s+(?:to|as))\s*V2|"
        r"V2\s*(?:=|->|maps?\s+to|is\s+(?:identical|equivalent|"
        r"the\s+same)\s+(?:to|as))\s*W_N2)",
        re.I | re.S,
    ),
}
_REFUTATION_WITHIN = re.compile(
    r"\b(?:does\s+not|do\s+not|cannot|never|fails?\s+to|must\s+not|"
    r"is\s+not|are\s+not|not_claimed|"
    r"no\s+(?:order[-_ ]independent|claim|FLRW|isotrop|equivalen))\b",
    re.I,
)
_REFUTATION_PREFIX = re.compile(
    r"(?:(?:no|not)|no\s+claim\s+that|it\s+is\s+false\s+that|"
    r"we\s+reject(?:\s+the\s+claim)?\s+that|forbidden\s+claim\s*:)\s*$",
    re.I,
)
_REFUTATION_SUFFIX = re.compile(
    r"^\s*(?:is|are)\s+(?:false|forbidden|rejected|not\s+claimed)\b",
    re.I,
)
_CLASSIFICATION_DISPOSITIONS = {
    "guard_or_mutation_fixture": {"allowed_test_surface"},
    "registered_claim_firewall": {"allowed_guard_surface"},
    "explicit_refutation": {"allowed_claim_firewall"},
    "active_claim": {"unresolved", "remediated"},
}
_FINDING_KEYS = {
    "finding_kind",
    "path",
    "file_sha256",
    "line",
    "text_sha256",
    "classification",
    "disposition",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return value


def _render(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _publish(path: Path, payload: dict[str, Any], *, write: bool) -> None:
    content = _render(payload)
    target = REPO / path
    if not write:
        if not target.is_file() or target.read_bytes() != content:
            raise ValueError(f"artifact differs under --check: {path}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.read_bytes() == content:
        return
    with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, target)


def _input_paths() -> tuple[Path, ...]:
    paths = [
        SPEC,
        PROVENANCE,
        Path("docs/research_program/long_horizon_rescue/pr127_spec.yaml"),
        CONTRACT_V1,
        CONTRACT_V2,
        COLLECTION,
        ADJ_V1,
        ADJ_V2,
        Path("docs/codex_handoff/pr_backlog.yaml"),
        Path("docs/generated/pr167_artifact_manifest.json"),
        Path("htt/src/common/unsigned_isotropy_leakage.py"),
        Path("htt/src/common/egs_oneway.py"),
        Path("htt/src/common/graded_nonid.py"),
        Path("htt/obsstat/egs3_graded_comparator.py"),
        Path("htt/obsstat/egs3_vorticity_channels.py"),
        Path("htt/obsstat/egs2_transport.py"),
        Path("htt/obsstat/egs3_unification_schema.py"),
        Path("scripts/build_egs_results_table_v9.py"),
        Path("docs/generated/egs_results_table_v9.json"),
        Path("docs/generated/egs_results_table_v9.md"),
        RUNNER,
    ]
    for version in ("v1", "v2"):
        paths.extend(
            Path(f"docs/generated/pr169_cas/{version}/axis_result_{axis}.json")
            for axis in AXES
        )
    return tuple(paths)


def _input_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in _input_paths():
        target = REPO / path
        if not target.is_file():
            raise ValueError(f"required PR-169 input absent: {path}")
        hashes[path.as_posix()] = _sha(target)
    return hashes


def _metadata(spec: dict[str, Any], inputs: dict[str, str], *, owner: str) -> dict[str, Any]:
    return {
        "owner": owner,
        "implementation_scope": "common",
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "artifact_mode": "exact_comparator_result",
        "allowed_use": (
            "internal exact comparator algebra and claim-firewall evidence"
        ),
        "forbidden_use": [
            "physical cosmological witness without complete admissibility receipts",
            "FLRW or isotropy certificate",
            "Bianchi family identification",
            "native-transfer validation",
        ],
        "transfer_source": "none",
        "config_hash": _sha(REPO / SPEC),
        "input_hashes": inputs,
        "sky_support_status": "not_applicable_exact_theory",
        "mask_status": "not_applicable_exact_theory",
        "covariance_status": "not_applicable_exact_theory",
        "null_mock_status": "not_applicable_exact_theory",
        "caveats": [
            "The result is exact only on the declared PR-126/127 comparator carrier.",
            "No Einstein-matter solution or physical admissibility is established.",
            "The historical W2 label denotes normalized vorticity, not Nilsson normalized Weyl curvature.",
            "The artifact is internal and non-public before native-solver validation.",
        ],
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr169_unsigned_leakage.py --write"
        ),
        "runtime_environment": {
            "python": platform.python_version(),
            "exact_scalar": "fractions.Fraction and four independent CAS axes",
        },
        "git_commit": spec["baseline_commit"],
        "worktree_state": f"{spec['baseline_commit']}+PR-169-worktree",
        "public_use": False,
    }


def _candidate_files() -> list[Path]:
    paths: list[Path] = []
    for root, suffixes in (
        (REPO / "htt", {".py"}),
        (REPO / "scripts", {".py"}),
        (REPO / "docs/manuscript", {".tex"}),
    ):
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix in suffixes
                and "__pycache__" not in path.parts
                and "build" not in path.relative_to(REPO).parts
                and "dist" not in path.relative_to(REPO).parts
            ):
                paths.append(path)
    paths.extend(
        REPO / value
        for value in (
            "docs/codex_handoff/pr_backlog.yaml",
            "docs/research_program/long_horizon_rescue/pr169_spec.yaml",
            "docs/generated/egs_results_table_v9.json",
            "docs/generated/egs_results_table_v9.md",
        )
    )
    return sorted(set(paths))


def _is_explicit_refutation(prefix: str, matched: str, suffix: str) -> bool:
    return bool(
        _REFUTATION_WITHIN.search(matched)
        or _REFUTATION_PREFIX.search(prefix[-100:])
        or _REFUTATION_SUFFIX.search(suffix[:100])
    )


def _classify_risk(
    path: str,
    *,
    prefix: str,
    matched: str,
    suffix: str,
) -> tuple[str, str]:
    if path == RUNNER.as_posix() or path.startswith("tests/"):
        return "guard_or_mutation_fixture", "allowed_test_surface"
    if path in {
        "docs/research_program/long_horizon_rescue/pr169_spec.yaml",
        "htt/src/common/egs_oneway.py",
    }:
        return "registered_claim_firewall", "allowed_guard_surface"
    if _is_explicit_refutation(prefix, matched, suffix):
        return "explicit_refutation", "allowed_claim_firewall"
    return "active_claim", "unresolved"


def validate_consumer_records(records: object) -> None:
    """Reject unknown or incomplete claim classifications before adjudication."""

    if not isinstance(records, list):
        raise ValueError("consumer findings must be a list")
    for index, row in enumerate(records):
        if not isinstance(row, dict) or set(row) != _FINDING_KEYS:
            raise ValueError(f"consumer finding {index} has an open or incomplete schema")
        classification = row["classification"]
        disposition = row["disposition"]
        if classification not in _CLASSIFICATION_DISPOSITIONS:
            raise ValueError(
                f"consumer finding {index} has unknown classification: {classification}"
            )
        if disposition not in _CLASSIFICATION_DISPOSITIONS[classification]:
            raise ValueError(
                f"consumer finding {index} has invalid disposition "
                f"{disposition!r} for {classification!r}"
            )
        if not isinstance(row["path"], str) or not row["path"]:
            raise ValueError(f"consumer finding {index} has no path")
        if not isinstance(row["line"], int) or row["line"] < 1:
            raise ValueError(f"consumer finding {index} has invalid line")
        for key in ("file_sha256", "text_sha256"):
            if not isinstance(row[key], str) or not re.fullmatch(r"[0-9a-f]{64}", row[key]):
                raise ValueError(f"consumer finding {index} has invalid {key}")


def scan_active_consumers(
    *, extra_texts: Iterable[tuple[str, str]] = (),
) -> dict[str, Any]:
    """Inventory active comparator consumers and classify risky claim windows."""

    inventory: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    texts: list[tuple[str, str, str]] = []
    for path in _candidate_files():
        relative = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if not _TOKEN.search(text):
            continue
        token_count = len(_TOKEN.findall(text))
        inventory.append(
            {
                "path": relative,
                "sha256": _sha(path),
                "semantic_token_count": token_count,
                "scope": "active_code_or_current_claim_surface",
            }
        )
        texts.append((relative, text, _sha(path)))
    for path, text in extra_texts:
        digest = hashlib.sha256(text.encode()).hexdigest()
        texts.append((path, text, digest))

    for path, text, digest in texts:
        for finding_kind, pattern in _RISK_PATTERNS.items():
            for match in pattern.finditer(text):
                start = max(0, match.start() - 120)
                stop = min(len(text), match.end() + 120)
                window = " ".join(text[start:stop].split())
                prefix = text[max(0, match.start() - 120):match.start()]
                matched = match.group(0)
                suffix = text[match.end():min(len(text), match.end() + 120)]
                classification, disposition = _classify_risk(
                    path,
                    prefix=prefix,
                    matched=matched,
                    suffix=suffix,
                )
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "finding_kind": finding_kind,
                        "path": path,
                        "file_sha256": digest,
                        "line": line,
                        "text_sha256": hashlib.sha256(window.encode()).hexdigest(),
                        "classification": classification,
                        "disposition": disposition,
                    }
                )
    findings.sort(key=lambda row: (row["path"], row["line"], row["finding_kind"]))
    inventory.sort(key=lambda row: row["path"])
    validate_consumer_records(findings)
    unresolved = [
        row for row in findings
        if row["classification"] == "active_claim" and row["disposition"] == "unresolved"
    ]
    return {
        "schema": "htt.pr169.all_consumer_scan.v1",
        "scan_scope": [
            "htt/**/*.py",
            "scripts/**/*.py",
            "docs/manuscript/**/*.tex",
            "canonical backlog and PR-169 spec",
            "current egs_results_table_v9 JSON and Markdown",
        ],
        "excluded_as_non_active": [
            "docs/audits/**",
            "docs/PR_DELTAS/**",
            "docs/harness append-only validation history",
            "legacy/**",
            "build caches and bytecode",
        ],
        "inventory": inventory,
        "risk_findings": findings,
        "inventory_file_count": len(inventory),
        "risk_finding_count": len(findings),
        "unresolved_active_claims": unresolved,
        "unresolved_active_claim_count": len(unresolved),
        "pass": not unresolved,
    }


def _find_card(backlog: dict[str, Any], pr_id: str) -> dict[str, Any]:
    cards = backlog.get("prs")
    if not isinstance(cards, list):
        raise ValueError("backlog prs missing")
    matches = [card for card in cards if isinstance(card, dict) and card.get("id") == pr_id]
    if len(matches) != 1:
        raise ValueError(f"expected one {pr_id} card")
    return matches[0]


def _mutation_report() -> dict[str, Any]:
    full = full_saturating_point("3/10")
    sliced = slice_saturating_point("3/10")
    rows: list[dict[str, Any]] = []

    semantic_mutants = (
        ("mutation/forbidden_claim.txt", "x_C=0 proves FLRW isotropy"),
        (
            "mutation/not_a_caveat.txt",
            "This is not a caveat: x_C=0 proves FLRW isotropy",
        ),
        ("mutation/nilsson_forward.txt", "W_N2 is identical to V2"),
        ("mutation/nilsson_reverse.txt", "V2 = W_N2"),
        (
            "mutation/global_measure.txt",
            "x_C is a scalar measure of FLRW departure",
        ),
        (
            "mutation/global_bound.txt",
            "x_C constrains global anisotropy",
        ),
        (
            "mutation/tilt_only.txt",
            "Vanishing tilt guarantees FLRW recovery",
        ),
        (
            "docs/codex_handoff/pr_backlog.yaml",
            "x_C=0 proves FLRW isotropy",
        ),
    )
    mutated = scan_active_consumers(extra_texts=semantic_mutants)
    for path, text in semantic_mutants:
        digest = hashlib.sha256(text.encode()).hexdigest()
        detected = any(
            row["path"] == path
            and row["file_sha256"] == digest
            and row["classification"] == "active_claim"
            and row["disposition"] == "unresolved"
            for row in mutated["risk_findings"]
        )
        rows.append(
            {
                "id": f"semantic_claim_mutation:{path}",
                "detected": detected,
            }
        )

    valid_finding = {
        "finding_kind": "signed_scalar_isotropy_promotion",
        "path": "mutation/schema.txt",
        "file_sha256": "a" * 64,
        "line": 1,
        "text_sha256": "b" * 64,
        "classification": "active_claim",
        "disposition": "unresolved",
    }
    missing = dict(valid_finding)
    missing.pop("classification")
    unknown = dict(valid_finding)
    unknown["classification"] = "unknown"
    missing_disposition = dict(valid_finding)
    missing_disposition.pop("disposition")
    unknown_disposition = dict(valid_finding)
    unknown_disposition["disposition"] = "unknown"
    incompatible = dict(valid_finding)
    incompatible["disposition"] = "allowed_guard_surface"
    for mutation_id, finding in (
        ("missing_classification_rejected", missing),
        ("unknown_classification_rejected", unknown),
        ("missing_disposition_rejected", missing_disposition),
        ("unknown_disposition_rejected", unknown_disposition),
        ("incompatible_disposition_rejected", incompatible),
    ):
        try:
            validate_consumer_records([finding])
            detected = False
        except ValueError:
            detected = True
        rows.append({"id": mutation_id, "detected": detected})
    rows.append(
        {
            "id": "sign_mutation",
            "detected": sign_mutant_x_c(sliced) != sliced.x_c(),
        }
    )
    projected = clip_signed_curvature(full)
    rows.append(
        {
            "id": "signed_projection",
            "detected": (
                projected.x_c() != full.x_c()
                and projected.m_unsigned() != full.m_unsigned()
            ),
        }
    )
    try:
        require_typed_symbol_bridge(
            QuadraticSectorSymbol.W_N2,
            QuadraticSectorSymbol.V2,
            exact_derivation_sha256=None,
        )
        bridge_detected = False
    except UnsignedLeakageError:
        bridge_detected = True
    rows.append({"id": "nilsson_symbol_conflation", "detected": bridge_detected})
    missing_route = route_terminal_result(
        "CAS_4AXIS_PASS",
        ReceiptStatus.MISSING.value,
        semantic_gate_pass=True,
        artifact_gate_pass=True,
    )
    rows.append(
        {
            "id": "missing_receipt_promotion",
            "detected": missing_route["scientific_result"] == "algebraic_only",
        }
    )
    failed_route = route_terminal_result(
        "CAS_FAIL",
        ReceiptStatus.PASS.value,
        semantic_gate_pass=True,
        artifact_gate_pass=True,
    )
    rows.append(
        {
            "id": "cas_failure_precedence",
            "detected": (
                failed_route["process_gate_status"] == "FAIL"
                and failed_route["scientific_result"] == "none"
            ),
        }
    )
    survivors = [row["id"] for row in rows if not row["detected"]]
    return {
        "schema": "htt.pr169.mutation_report.v1",
        "mutations": rows,
        "survivors": survivors,
        "surviving_mutation_count": len(survivors),
        "pass": not survivors,
    }


def build(*, write: bool) -> dict[str, Any]:
    spec = _yaml(REPO / SPEC)
    provenance = _yaml(REPO / PROVENANCE)
    inputs = _input_hashes()
    common_meta = _metadata(spec, inputs, owner="COMMON")

    collection = _json(REPO / COLLECTION)
    adjudication_v1 = _json(REPO / ADJ_V1)
    adjudication_v2 = _json(REPO / ADJ_V2)
    if collection["versions"]["v1"]["aggregate_status"] != "CAS_FAIL":
        raise ValueError("PR-169 v1 failure receipt was not preserved")
    if adjudication_v1["aggregate_status"] != "CAS_FAIL":
        raise ValueError("PR-169 v1 adjudication drifted")
    if collection["versions"]["v2"]["aggregate_status"] != "CAS_4AXIS_PASS":
        raise ValueError("PR-169 v2 collection is not a four-axis pass")
    if adjudication_v2["aggregate_status"] != "CAS_4AXIS_PASS":
        raise ValueError("PR-169 v2 adjudication is not a four-axis pass")

    ceiling = {
        "schema": "htt.pr169.exact_ceiling_result.v1",
        **common_meta,
        "cas_history": {
            "v1": "CAS_FAIL",
            "v2": "CAS_4AXIS_PASS",
            "cross_version_result_reuse": False,
        },
        "declared_carrier": {
            "x_C": "Sigma2 - V2 + Omega_tilt + DeltaOmega_k",
            "M_unsigned": "Sigma2 + V2 + Omega_tilt + abs(DeltaOmega_k)",
            "domain": "exact ordered rationals",
        },
        "exact_result": {
            "full_capped_ceiling": "M_max(B)=4B",
            "shear_vorticity_slice_ceiling": "M_slice_max(B)=2B",
            "uncapped_family": "(a,a,0,0), a>0: x_C=0 and M_unsigned=2a",
            "b_independent_upper_bound_from_x_C_zero": False,
        },
        "fixture_receipt": exact_ceiling_receipt(),
        "physical_model_claim": False,
    }

    physical_bundle = adjudicate_physical_bundle([])
    try:
        require_typed_symbol_bridge(
            QuadraticSectorSymbol.W_N2,
            QuadraticSectorSymbol.V2,
            exact_derivation_sha256=None,
        )
        symbol_bridge = {"status": "UNEXPECTED_PASS"}
    except UnsignedLeakageError as exc:
        symbol_bridge = {
            "status": "REJECTED_TYPED_MISMATCH",
            "reason": str(exc),
        }
    physical = {
        "schema": "htt.pr169.physical_admissibility.v1",
        **common_meta,
        "physical_bundle": physical_bundle,
        "nilsson_source": {
            "paper": provenance["source"]["citation"],
            "source_variable": "W_N2_normalized_weyl_curvature_squared",
            "repository_variable": "V2_normalized_vorticity_squared",
            "bridge": symbol_bridge,
        },
        "pr127_parent_evidence": classify_pr127_evidence(
            "physical", "A_C_comparator_level"
        ),
        "constructive_promotion_allowed": False,
        "terminal_scientific_result_if_cas_passes": "algebraic_only",
    }

    backlog = _yaml(REPO / "docs/codex_handoff/pr_backlog.yaml")
    card = _find_card(backlog, "PR-169")
    supersession = {
        "schema": "htt.pr169.candidate_branch_supersession.v1",
        **common_meta,
        "authoritative_card": {
            "path": "docs/codex_handoff/pr_backlog.yaml",
            "pr_id": "PR-169",
            "card_semantic_sha256": semantic_sha256(card),
            "backlog_file_sha256": _sha(REPO / "docs/codex_handoff/pr_backlog.yaml"),
            "card_rewritten": False,
        },
        "candidate_branch": "constructive Nilsson-class witness",
        "registered_kill_switch": card["kill"],
        "kill_switch_activated": True,
        "activation_evidence": [
            "Nilsson W_N2 is normalized Weyl curvature, not repository vorticity V2",
            "all eight typed physical-promotion receipts are missing",
        ],
        "disposition": "registered_candidate_superseded_by_algebraic_only_result",
        "intake_transaction_preserved": True,
    }

    consumers = scan_active_consumers()
    validate_consumer_records(consumers["risk_findings"])
    require_no_unresolved_consumer_hits(consumers["risk_findings"])
    consumers.update(common_meta)
    mutations = _mutation_report()
    if mutations["surviving_mutation_count"]:
        raise ValueError(f"PR-169 mutation survivors: {mutations['survivors']}")
    mutations.update(common_meta)

    route = route_terminal_result(
        "CAS_4AXIS_PASS",
        physical_bundle["bundle_status"],
        semantic_gate_pass=consumers["pass"],
        artifact_gate_pass=True,
    )
    if route["scientific_result"] != "algebraic_only":
        raise ValueError("PR-169 did not terminate at algebraic_only")
    result = {
        "schema": "htt.pr169.result_card.v1",
        **common_meta,
        "result_status": "ALGEBRAIC_ONLY_EXACT_COMPARATOR_RESULT",
        "terminal_route": route,
        "exact_claim": ceiling["exact_result"],
        "physical_promotion_status": physical_bundle["bundle_status"],
        "nilsson_bridge_status": symbol_bridge["status"],
        "consumer_gate": {
            "pass": consumers["pass"],
            "inventory_file_count": consumers["inventory_file_count"],
            "unresolved_active_claim_count": consumers[
                "unresolved_active_claim_count"
            ],
        },
        "mutation_gate": mutations["pass"],
        "scientific_interpretation": (
            "Exact cancellation and ceiling result on the declared comparator "
            "carrier; no physically admissible cosmological witness identified."
        ),
        "family_identification": False,
        "native_solver_validation": False,
    }

    payloads = {
        "ceiling": ceiling,
        "physical": physical,
        "supersession": supersession,
        "consumers": consumers,
        "mutations": mutations,
        "result": result,
    }
    for payload in payloads.values():
        missing = sorted(REQUIRED_METADATA - set(payload))
        if missing:
            raise ValueError(f"artifact metadata incomplete: {missing}")
    for key, payload in payloads.items():
        _publish(OUTPUTS[key], payload, write=write)

    artifact_hashes = {
        OUTPUTS[key].as_posix(): hashlib.sha256(_render(payload)).hexdigest()
        for key, payload in payloads.items()
    }
    manifest = {
        "schema": "htt.pr169.artifact_manifest.v1",
        **common_meta,
        "scientific_result": "algebraic_only",
        "process_gate_status": "PASS",
        "cas_aggregate": "CAS_4AXIS_PASS",
        "physical_bundle_status": "MISSING",
        "artifact_hashes": artifact_hashes,
        "check_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr169_unsigned_leakage.py --check"
        ),
        "planck_pr3_raw_deleted": False,
        "pr4_data_actions": 0,
    }
    if sorted(REQUIRED_METADATA - set(manifest)):
        raise ValueError("manifest metadata incomplete")
    _publish(OUTPUTS["manifest"], manifest, write=write)
    return {
        "ok": True,
        "mode": "write" if write else "check",
        "scientific_result": manifest["scientific_result"],
        "cas_aggregate": manifest["cas_aggregate"],
        "physical_bundle_status": manifest["physical_bundle_status"],
        "consumer_inventory_files": consumers["inventory_file_count"],
        "consumer_unresolved": consumers["unresolved_active_claim_count"],
        "mutation_survivors": mutations["surviving_mutation_count"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(write=args.write), indent=2))


if __name__ == "__main__":
    main()
