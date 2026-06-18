#!/usr/bin/env python3
"""Build and check the PR-115 publication-claim freeze artifacts.

The freeze is a claim-control artifact for the pre-solver repository. It maps
publicly reusable claims to artifacts, tests, caveats, and owners, while keeping
submission readiness blocked where required evidence is absent.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_SRC = REPO_ROOT / "htt" / "src"
if str(COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(COMMON_SRC))

from common.semantic_guards.no_overclaim import (  # noqa: E402
    issue_to_dict,
    scan_text,
)


DEFAULT_FREEZE_OUTPUT = Path("docs/generated/publication_claim_freeze.md")
DEFAULT_MATRIX_OUTPUT = Path("docs/generated/hostile_review_response_matrix.md")
SCHEMA_VERSION = "common.publication_claim_freeze.v1"
ARTIFACT_ID = "publication_claim_freeze"
FAMILY_ID_RE = re.compile(
    r"\b(family[- ]?ID|family\s+identif|identified\s+famil|geometry\s+detected)\b",
    re.IGNORECASE,
)


DEFAULT_REQUIRED_INPUTS: tuple[str, ...] = (
    "scripts/check_publication_claim_freeze.py",
    "tests/contracts/test_publication_claim_freeze.py",
    "docs/generated/status_snapshot.json",
    "docs/generated/claim_ledger.json",
    "docs/generated/status_matrix.md",
    "docs/generated/result_pack_A.md",
    "docs/generated/result_pack_B.md",
    "docs/generated/result_pack_C.md",
    "docs/generated/transfer_sensitivity_report.md",
    "docs/generated/manuscript_figure_inventory.md",
    "docs/generated/missing_figure_references.md",
    "docs/generated/pdf_claim_lint_report.md",
    "docs/audit_prompts/claim_firewall_review.md",
    "docs/audit_prompts/local_global_review.md",
    "docs/audit_prompts/manuscript_figure_review.md",
    "docs/audit_prompts/transfer_provenance_review.md",
    "docs/audit_prompts/future_solver_interface_review.md",
)


PUBLIC_CLAIMS: tuple[dict[str, Any], ...] = (
    {
        "claim_id": "framework.claim_tiered_observatory",
        "owner": "COMMON",
        "claim_tier": "C1",
        "status": "allowed_with_caveats",
        "statement": "claim-tiered observational/statistical framework status is implemented as generated DAG and claim-ledger artifacts",
        "allowed_phrase": "claim-tiered observational/statistical framework",
        "artifacts": [
            "docs/generated/status_snapshot.json",
            "docs/generated/claim_ledger.json",
            "docs/generated/status_matrix.md",
        ],
        "manifest_refs": ["docs/generated/status_snapshot.json"],
        "tests": [
            "tests/contracts/test_status_snapshot.py",
            "python -m common.status_snapshot --write docs/generated/status_snapshot.json",
        ],
        "caveats": [
            "DAG completion is project bookkeeping only.",
            "Production validation remains false without native, null, mask, and covariance gates.",
        ],
    },
    {
        "claim_id": "transfer.current_external_paths",
        "owner": "COMMON",
        "claim_tier": "C2",
        "status": "allowed_with_caveats",
        "statement": "current transfer-dependent report surfaces are transfer-conditional under explicit external/proxy provenance",
        "allowed_phrase": "transfer-conditional result",
        "artifacts": ["docs/generated/transfer_sensitivity_report.md"],
        "manifest_refs": ["docs/generated/transfer_sensitivity_report.md"],
        "tests": [
            "tests/contracts/test_transfer_sensitivity_report.py",
            "python scripts/generate_transfer_sensitivity_report.py --dry-run",
        ],
        "caveats": [
            "External/proxy transfer paths are not native validated artifacts.",
            "Transfer metadata labels are provenance labels only.",
        ],
    },
    {
        "claim_id": "mio.certificates_diagnostic_only",
        "owner": "MIO",
        "claim_tier": "C2",
        "status": "allowed_with_caveats",
        "statement": "MIO certificate and coherence rows are diagnostic-only report surfaces",
        "allowed_phrase": "diagnostic-only certificate",
        "artifacts": ["docs/generated/result_pack_C.md"],
        "manifest_refs": ["docs/generated/result_pack_C.md"],
        "tests": [
            "tests/result_packs/test_pack_C.py",
            "tests/contracts/test_claim_language_lint.py",
        ],
        "caveats": [
            "MIO reports are not truth, posterior, or model-ranking objects.",
            "HTT evidence traces remain HTT-owned and read-only to MIO reports.",
        ],
    },
    {
        "claim_id": "htt.local_global_candidate",
        "owner": "HTT",
        "claim_tier": "C4",
        "status": "allowed_with_caveats",
        "statement": "local/global discrimination remains a conditional candidate gated by rank, local-null, survey/systematic, PPC, and LOOCV status",
        "allowed_phrase": "local/global discrimination candidate",
        "artifacts": ["docs/generated/result_pack_B.md"],
        "manifest_refs": ["docs/generated/result_pack_B.md"],
        "tests": [
            "tests/result_packs/test_pack_B.py",
            "tests/htt/test_local_global_mixture.py",
            "tests/htt/test_posterior_pushforward.py",
        ],
        "caveats": [
            "Candidate wording is blocked when rank or FPR prerequisites fail.",
            "MIO directional/depth rows are diagnostic cross-checks, not HTT evidence.",
        ],
    },
    {
        "claim_id": "obsstat.scalar_morphology_side_by_side",
        "owner": "OBSSTAT",
        "claim_tier": "C3",
        "status": "allowed_with_caveats",
        "statement": "scalar and morphology features can be reported side by side only as separate diagnostics with separate provenance",
        "allowed_phrase": "morphology compatibility remains unclaimed",
        "artifacts": ["docs/generated/result_pack_A.md"],
        "manifest_refs": ["docs/generated/result_pack_A.md"],
        "tests": [
            "tests/result_packs/test_pack_A.py",
            "tests/contracts/test_claim_language_lint.py",
        ],
        "caveats": [
            "Scalar x/Q/Pi/F/G and low-ell feature summaries do not classify geometry.",
            "Native morphology atlas support is absent.",
        ],
    },
    {
        "claim_id": "audit.external_package_disclosure",
        "owner": "COMMON",
        "claim_tier": "C1",
        "status": "allowed_with_caveats",
        "statement": "external audit package bundles code snapshots, reports, manifests, prompts, status, claim ledger, and transfer provenance for review",
        "allowed_phrase": "external audit disclosure package",
        "artifacts": [
            "docs/generated/external_audit_package.zip",
            "docs/generated/external_audit_package_manifest.json",
        ],
        "manifest_refs": ["docs/generated/external_audit_package_manifest.json"],
        "tests": [
            "tests/contracts/test_audit_package_generator.py",
            "python scripts/build_external_audit_package.py --check",
        ],
        "caveats": [
            "Audit packaging is not publication readiness.",
            "Missing manuscript figure provenance remains visible inside the package.",
        ],
    },
    {
        "claim_id": "bass.future_native_interface_schema_only",
        "owner": "BASS",
        "claim_tier": "C1",
        "status": "allowed_with_caveats",
        "statement": "future native low-ell solver interfaces are schema and adapter-stub surfaces only",
        "allowed_phrase": "future native solver interface schema",
        "artifacts": [
            "htt/bass/transfer/native_schema.py",
            "htt/bass/transfer/native_adapter.py",
            "docs/generated/external_audit_package_manifest.json",
        ],
        "manifest_refs": ["docs/generated/external_audit_package_manifest.json"],
        "tests": [
            "tests/contracts/test_transfer_registry.py",
            "tests/contracts/test_audit_package_generator.py",
        ],
        "caveats": [
            "The adapter stub must not return synthetic science values.",
            "No native low-ell solver output is present in this repository state.",
        ],
    },
    {
        "claim_id": "manuscript.figure_inventory_blocks_submission",
        "owner": "COMMON",
        "claim_tier": "C1",
        "status": "blocked_for_submission",
        "statement": "manuscript figure inventory records missing and quarantined figure references that block final submission freeze",
        "allowed_phrase": "manuscript figure inventory blocks final freeze",
        "artifacts": [
            "docs/generated/manuscript_figure_inventory.md",
            "docs/generated/missing_figure_references.md",
            "docs/generated/quarantined_figures.md",
        ],
        "manifest_refs": ["docs/generated/manuscript_figure_inventory.md"],
        "tests": [
            "tests/contracts/test_manuscript_figure_audit.py",
            "python scripts/audit_manuscript_figures.py --dry-run",
        ],
        "caveats": [
            "Missing or quarantined figures are blockers, not promoted figures.",
            "Text audit findings are review findings, not scientific results.",
        ],
    },
)


HOSTILE_REVIEW_ROWS: tuple[dict[str, str], ...] = (
    {
        "reviewer": "relativistic_cosmology",
        "verdict": "INTERNAL_ONLY",
        "attack": "No native low-ell morphology atlas or externally gated equivalence-class analysis is present.",
        "response": "Freeze allows only pre-solver framework and schema claims.",
        "required_fix": "Ingest native solver artifacts and rerun morphology, null, mask, covariance, and equivalence gates.",
    },
    {
        "reviewer": "statistical_inference",
        "verdict": "MAJOR_REVISIONS",
        "attack": "Local/global candidate claims require rank, null, PPC, LOOCV, and look-elsewhere evidence before stronger public wording.",
        "response": "Result Pack B keeps candidate status conditional and records no-claim scenarios.",
        "required_fix": "Attach matched null ensembles and held-out adequacy artifacts to any stronger inference claim.",
    },
    {
        "reviewer": "numerical_methods",
        "verdict": "MAJOR_REVISIONS",
        "attack": "Current native-transfer rows are schema-only; external/proxy paths are not native validation.",
        "response": "Transfer report and audit package preserve external/proxy provenance.",
        "required_fix": "Add external native solver outputs plus reproducibility and convergence manifests.",
    },
    {
        "reviewer": "software_reproducibility",
        "verdict": "PASS_WITH_BLOCKERS",
        "attack": "Generated reports and audit package are reproducible, but manuscript figures remain unmanifested or missing.",
        "response": "Freeze report maps public claims to generated artifacts and records figure blockers.",
        "required_fix": "Resolve or quarantine every manuscript figure with manifest-backed provenance.",
    },
    {
        "reviewer": "claim_hygiene_editor",
        "verdict": "PASS_WITH_BLOCKERS",
        "attack": "Public language must not collapse HTT inference, MIO diagnostics, transfer provenance, or BASS schema surfaces.",
        "response": "Freeze claims carry owner, tier, artifacts, tests, caveats, and forbidden promotions.",
        "required_fix": "Keep manuscript/release copy synced to this freeze before submission.",
    },
    {
        "reviewer": "skeptical_family_id",
        "verdict": "REJECT_STRONGER_CLAIMS",
        "attack": "Scalar features, MIO reports, and local/global candidates cannot establish geometry or family-ID.",
        "response": "Freeze blocks C5/C6 family-ID claims before native morphology atlas support.",
        "required_fix": "Provide native atlas, equivalence-class, response-rank, null, mask, covariance, PPC, and LOOCV gates.",
    },
)


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _git_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_state(repo_root: Path) -> str:
    commit = _git_commit(repo_root)
    try:
        dirty = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = list(sys.argv[1:] if argv is None else argv)
    args = [arg for arg in args if arg != "--check"]
    return " ".join(["python", "scripts/check_publication_claim_freeze.py", *args]).strip()


def _normalise(path: Path) -> str:
    return path.as_posix()


def _required_input_hashes(repo_root: Path, required_inputs: Iterable[str]) -> list[str]:
    hashes: list[str] = []
    missing: list[str] = []
    for item in sorted(set(required_inputs)):
        path = repo_root / item
        if not path.is_file():
            missing.append(item)
            continue
        hashes.append(f"{item}:{_sha256_file(path)}")
    if missing:
        raise FileNotFoundError(
            "publication claim freeze required inputs are missing: "
            + ", ".join(sorted(missing))
        )
    return hashes


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object at {path}")
    return data


def _extract_summary_count(text: str, label: str) -> int | None:
    pattern = re.compile(rf"^-\s+{re.escape(label)}:\s+(\d+)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return int(match.group(1)) if match else None


def _manuscript_blockers(repo_root: Path) -> dict[str, int | str]:
    inventory = (repo_root / "docs/generated/manuscript_figure_inventory.md").read_text(encoding="utf-8")
    missing = (repo_root / "docs/generated/missing_figure_references.md").read_text(encoding="utf-8")
    def count_or_unknown(text: str, label: str) -> int | str:
        count = _extract_summary_count(text, label)
        return "unknown" if count is None else count

    return {
        "includegraphics_refs": count_or_unknown(inventory, "Includegraphics refs"),
        "resolved_refs": count_or_unknown(inventory, "Resolved refs"),
        "missing_refs": count_or_unknown(inventory, "Missing refs"),
        "quarantined_refs": count_or_unknown(inventory, "Quarantined refs"),
        "text_audit_findings": count_or_unknown(inventory, "Text audit findings"),
        "claim_risk_findings": count_or_unknown(missing, "Claim-risk findings"),
    }


def _pdf_claim_lint_passed(repo_root: Path) -> bool:
    report_path = repo_root / "docs/generated/pdf_claim_lint_report.md"
    pdf_path = repo_root / "docs/generated/manuscript_pdf/htt_base_research_report.pdf"
    if not report_path.is_file() or not pdf_path.is_file():
        return False
    text = report_path.read_text(encoding="utf-8")
    current_hash = _sha256_file(pdf_path)
    return (
        f"- Failed findings: `0`" in text
        and f"- PDF SHA256: `{current_hash}`" in text
    )


def _claim_language_issues(claims: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    text = json.dumps(claims, sort_keys=True, indent=2)
    return [
        issue_to_dict(issue)
        for issue in scan_text(text, path=Path("publication_claim_freeze.claims.json"))
    ]


def _c5_c6_family_id_violations(
    claims: Sequence[dict[str, Any]],
    *,
    native_morphology_atlas_present: bool,
) -> list[dict[str, str]]:
    if native_morphology_atlas_present:
        return []
    violations: list[dict[str, str]] = []
    for claim in claims:
        tier = str(claim.get("claim_tier", "")).upper()
        haystack = " ".join(
            str(claim.get(key, ""))
            for key in ("statement", "allowed_phrase", "claim_kind")
        )
        if tier in {"C5", "C6"} and FAMILY_ID_RE.search(haystack):
            violations.append(
                {
                    "claim_id": str(claim.get("claim_id", "<unknown>")),
                    "claim_tier": tier,
                    "reason": "C5/C6 family-ID claim requires native morphology atlas support",
                }
            )
    return violations


def _all_claims_have(claims: Sequence[dict[str, Any]], key: str) -> bool:
    return all(bool(claim.get(key)) for claim in claims)


def _all_claim_paths_exist(repo_root: Path, claims: Sequence[dict[str, Any]], key: str) -> bool:
    for claim in claims:
        for item in claim.get(key, ()):
            if not (repo_root / str(item)).exists():
                return False
    return True


def _submission_decision(blockers: dict[str, int | str]) -> str:
    missing = blockers.get("missing_refs")
    quarantined = blockers.get("quarantined_refs")
    if isinstance(missing, int) and missing > 0:
        return "blocked_internal_only"
    if isinstance(quarantined, int) and quarantined > 0:
        return "blocked_internal_only"
    return "claim_freeze_only_not_submission_approval"


def build_publication_claim_freeze_payload(
    *,
    repo_root: Path | str = REPO_ROOT,
    freeze_output: Path = DEFAULT_FREEZE_OUTPUT,
    matrix_output: Path = DEFAULT_MATRIX_OUTPUT,
    generating_command: str,
    public_claims: Sequence[dict[str, Any]] = PUBLIC_CLAIMS,
    hostile_review_rows: Sequence[dict[str, str]] = HOSTILE_REVIEW_ROWS,
    required_inputs: Sequence[str] = DEFAULT_REQUIRED_INPUTS,
    native_morphology_atlas_present: bool = False,
    worktree_state: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    claims = [dict(claim) for claim in public_claims]
    review_rows = [dict(row) for row in hostile_review_rows]
    input_hashes = _required_input_hashes(root, required_inputs)
    status_snapshot = _load_json(root / "docs/generated/status_snapshot.json")
    claim_ledger = _load_json(root / "docs/generated/claim_ledger.json")
    blockers = _manuscript_blockers(root)
    claim_issues = _claim_language_issues(claims)
    family_id_violations = _c5_c6_family_id_violations(
        claims,
        native_morphology_atlas_present=native_morphology_atlas_present,
    )
    required_assertions = {
        "all_claims_have_owner": _all_claims_have(claims, "owner"),
        "all_claims_have_artifacts": _all_claims_have(claims, "artifacts"),
        "all_claim_artifacts_exist": _all_claim_paths_exist(root, claims, "artifacts"),
        "all_claims_have_manifest_refs": _all_claims_have(claims, "manifest_refs"),
        "all_manifest_refs_exist": _all_claim_paths_exist(root, claims, "manifest_refs"),
        "all_claims_have_tests": _all_claims_have(claims, "tests"),
        "all_claims_have_caveats": _all_claims_have(claims, "caveats"),
        "claim_ledger_included": (root / "docs/generated/claim_ledger.json").is_file(),
        "transfer_provenance_included": (root / "docs/generated/transfer_sensitivity_report.md").is_file(),
        "external_audit_package_included": (root / "docs/generated/external_audit_package_manifest.json").is_file(),
        "pdf_claim_lint_passed": _pdf_claim_lint_passed(root),
        "manuscript_blockers_recorded": isinstance(blockers.get("missing_refs"), int)
        and isinstance(blockers.get("quarantined_refs"), int),
        "no_forbidden_claim_language": not claim_issues,
        "no_c5_c6_family_id_claim": not family_id_violations,
    }
    failed_gates = [key for key, value in required_assertions.items() if not value]
    config_hash = _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "claim_ids": [claim["claim_id"] for claim in claims],
            "reviewers": [row["reviewer"] for row in review_rows],
            "required_inputs": sorted(required_inputs),
            "native_morphology_atlas_present": native_morphology_atlas_present,
        }
    )
    state = worktree_state or _git_state(root)
    metadata = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": _normalise(freeze_output),
        "matrix_path": _normalise(matrix_output),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "created_by": "scripts/check_publication_claim_freeze.py",
        "code_version": state,
        "caveats": [
            "Publication claim freeze controls public wording; it is not submission approval.",
            "Current transfer-dependent outputs remain transfer-conditional.",
            "MIO diagnostics remain separate from HTT inference.",
            "Native morphology atlas support is absent in this repository state.",
            "Missing or quarantined manuscript figures block final submission freeze.",
        ],
        "generating_command": generating_command,
        "git_commit": _git_commit(root),
        "git_commit_or_worktree_state": state,
        "schema_version": SCHEMA_VERSION,
    }
    return {
        **metadata,
        "status_snapshot_summary": {
            "total_prs": status_snapshot.get("metadata", {}).get("total_prs"),
            "completed_prs": status_snapshot.get("metadata", {}).get("completed_prs"),
            "pending_prs": status_snapshot.get("metadata", {}).get("pending_prs"),
            "claim_rows": len(claim_ledger.get("rows", [])),
        },
        "submission_decision": _submission_decision(blockers),
        "native_morphology_atlas_present": native_morphology_atlas_present,
        "public_claims": claims,
        "hostile_review_rows": review_rows,
        "manuscript_blockers": blockers,
        "required_assertions": required_assertions,
        "passed_gates": sorted(key for key, value in required_assertions.items() if value),
        "failed_gates": failed_gates,
        "claim_language_issues": claim_issues,
        "family_id_violations": family_id_violations,
    }


def _metadata_lines(payload: dict[str, Any], *, artifact_path_key: str = "artifact_path") -> list[str]:
    lines = [
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"transfer_source: {payload['transfer_source']}",
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
    ]
    lines.extend(f"- {item}" for item in payload["input_hashes"])
    lines.extend(
        [
            "caveats:",
            *[f"- {item}" for item in payload["caveats"]],
            f"generating_command: {payload['generating_command']}",
            f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
            f"artifact_path: {payload[artifact_path_key]}",
        ]
    )
    return lines


def render_publication_claim_freeze(payload: dict[str, Any]) -> str:
    lines = [
        "# Publication Claim Freeze",
        "",
        *_metadata_lines(payload),
        "",
        "## Decision",
        "",
        f"- Submission decision: `{payload['submission_decision']}`",
        f"- Native morphology atlas present: `{payload['native_morphology_atlas_present']}`",
        f"- Public claim count: `{len(payload['public_claims'])}`",
        f"- Failed gates: `{', '.join(payload['failed_gates']) if payload['failed_gates'] else 'none'}`",
        "",
        "This freeze allows only caveated status, framework, transfer-provenance, diagnostic, and audit-package claims.",
        "It blocks stronger geometry, native-validation, or family-ID wording until the missing native and manuscript gates are closed.",
        "",
        "## Required Assertions",
        "",
        "| Assertion | Status |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{key}` | `{value}` |"
        for key, value in sorted(payload["required_assertions"].items())
    )
    blockers = payload["manuscript_blockers"]
    lines.extend(
        [
            "",
            "## Manuscript Blockers",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| Includegraphics refs | {blockers['includegraphics_refs']} |",
            f"| Resolved refs | {blockers['resolved_refs']} |",
            f"| Missing refs | {blockers['missing_refs']} |",
            f"| Quarantined refs | {blockers['quarantined_refs']} |",
            f"| Text audit findings | {blockers['text_audit_findings']} |",
            f"| Claim-risk findings | {blockers['claim_risk_findings']} |",
            "",
            "## Frozen Public Claims",
            "",
            "| Claim ID | Owner | Tier | Status | Allowed Phrase | Artifacts | Tests | Caveats |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for claim in payload["public_claims"]:
        lines.append(
            "| `{claim_id}` | `{owner}` | `{tier}` | `{status}` | {phrase} | {artifacts} | {tests} | {caveats} |".format(
                claim_id=claim["claim_id"],
                owner=claim["owner"],
                tier=claim["claim_tier"],
                status=claim["status"],
                phrase=claim["allowed_phrase"],
                artifacts="<br>".join(f"`{item}`" for item in claim["artifacts"]),
                tests="<br>".join(f"`{item}`" for item in claim["tests"]),
                caveats="<br>".join(str(item) for item in claim["caveats"]),
            )
        )
    lines.extend(
        [
            "",
            "## Forbidden Promotions",
            "",
            "- Do not label external/proxy transfer outputs as native validated artifacts.",
            "- Do not merge MIO diagnostic reports into HTT evidence or posterior quantities.",
            "- Do not use scalar x/Q/Pi/F/G, low-ell summaries, or directional coherence as geometry or family-ID evidence.",
            "- Do not present audit packaging or DAG completion as publication readiness.",
            "- Do not submit the manuscript while missing or quarantined figure references remain unresolved.",
            "",
        ]
    )
    if payload["claim_language_issues"]:
        lines.extend(
            [
                "## Claim Language Issues",
                "",
                "```json",
                json.dumps(payload["claim_language_issues"], indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    if payload["family_id_violations"]:
        lines.extend(
            [
                "## C5/C6 Family-ID Violations",
                "",
                "```json",
                json.dumps(payload["family_id_violations"], indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_hostile_review_response_matrix(payload: dict[str, Any]) -> str:
    lines = [
        "# Hostile Review Response Matrix",
        "",
        *_metadata_lines(payload, artifact_path_key="matrix_path"),
        "",
        "## Verdict",
        "",
        f"- Freeze verdict: `{payload['submission_decision']}`",
        "- Minimal public claim: caveated pre-solver framework, diagnostic, transfer-provenance, and audit-disclosure status only.",
        "- Stronger claims remain rejected until native, null, covariance, mask, rank, PPC, LOOCV, equivalence, and figure-provenance gates exist.",
        "",
        "## Review Matrix",
        "",
        "| Reviewer | Verdict | Attack | Response | Required Fix |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["hostile_review_rows"]:
        lines.append(
            "| `{reviewer}` | `{verdict}` | {attack} | {response} | {required_fix} |".format(
                reviewer=row["reviewer"],
                verdict=row["verdict"],
                attack=row["attack"],
                response=row["response"],
                required_fix=row["required_fix"],
            )
        )
    lines.extend(
        [
            "",
            "## Release Decision",
            "",
            "- Internal merge of the freeze gate is allowed when required assertions pass.",
            "- Public manuscript or release submission remains blocked by manuscript figure provenance and missing native morphology atlas gates.",
            "- External audit handoff may use the PR-114 disclosure package with this PR-115 freeze attached.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_outputs(repo_root: Path, payload: dict[str, Any], freeze_output: Path, matrix_output: Path) -> None:
    freeze_path = freeze_output if freeze_output.is_absolute() else repo_root / freeze_output
    matrix_path = matrix_output if matrix_output.is_absolute() else repo_root / matrix_output
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(render_publication_claim_freeze(payload), encoding="utf-8")
    matrix_path.write_text(render_hostile_review_response_matrix(payload), encoding="utf-8")


def _check_outputs(repo_root: Path, payload: dict[str, Any], freeze_output: Path, matrix_output: Path) -> int:
    freeze_path = freeze_output if freeze_output.is_absolute() else repo_root / freeze_output
    matrix_path = matrix_output if matrix_output.is_absolute() else repo_root / matrix_output
    if not freeze_path.exists() or not matrix_path.exists():
        print("missing publication claim freeze output")
        return 1
    expected_freeze = render_publication_claim_freeze(payload)
    expected_matrix = render_hostile_review_response_matrix(payload)
    if freeze_path.read_text(encoding="utf-8") != expected_freeze:
        print("stale publication claim freeze report")
        return 1
    if matrix_path.read_text(encoding="utf-8") != expected_matrix:
        print("stale hostile review response matrix")
        return 1
    print(f"up-to-date {freeze_path}")
    print(f"up-to-date {matrix_path}")
    return 0


def _existing_freeze_git_state(repo_root: Path, freeze_output: Path) -> str | None:
    freeze_path = freeze_output if freeze_output.is_absolute() else repo_root / freeze_output
    if not freeze_path.exists():
        return None
    for line in freeze_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("git_commit_or_worktree_state: "):
            return line.split(": ", 1)[1].strip()
    return None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--freeze-output", type=Path, default=DEFAULT_FREEZE_OUTPUT)
    parser.add_argument("--matrix-output", type=Path, default=DEFAULT_MATRIX_OUTPUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    worktree_state = (
        _existing_freeze_git_state(repo_root, args.freeze_output)
        if args.check
        else None
    )
    payload = build_publication_claim_freeze_payload(
        repo_root=repo_root,
        freeze_output=args.freeze_output,
        matrix_output=args.matrix_output,
        generating_command=_command_from_args(argv),
        worktree_state=worktree_state,
    )
    if payload["failed_gates"]:
        print("publication claim freeze failed required gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print("DRY-RUN: not writing publication claim freeze artifacts")
        print(f"submission_decision={payload['submission_decision']}")
        print(f"public_claim_count={len(payload['public_claims'])}")
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(repo_root, payload, args.freeze_output, args.matrix_output)
    _write_outputs(repo_root, payload, args.freeze_output, args.matrix_output)
    freeze_path = args.freeze_output if args.freeze_output.is_absolute() else repo_root / args.freeze_output
    matrix_path = args.matrix_output if args.matrix_output.is_absolute() else repo_root / args.matrix_output
    print(f"wrote {freeze_path}")
    print(f"wrote {matrix_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
