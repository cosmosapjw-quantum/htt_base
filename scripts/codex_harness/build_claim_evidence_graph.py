#!/usr/bin/env python3
"""Build/check the PR-122 claim-addressed evidence graph and blocked release receipt.

The generated receipt is intentionally an internally authored audit disclosure.
It records a successful mechanics scan and the current MES/D2 release blockers;
it is not a trusted scientific attestation and cannot authorize a claim release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence


_SOURCE_ONLY_PREFIX_ENV = "HTT_PR122_SOURCE_ONLY_PREFIX"
_SOURCE_ONLY_LAUNCHER_HASH_ENV = "HTT_PR122_SOURCE_ONLY_LAUNCHER_SHA256"
_SOURCE_ONLY_SITE_ENV = "HTT_PR122_SOURCE_ONLY_SITE_PACKAGES"
_SOURCE_ONLY_TARGET_ENV = "HTT_PR122_SOURCE_ONLY_TARGET"
_SOURCE_ONLY_TARGET = "scripts/codex_harness/build_claim_evidence_graph.py"
_SOURCE_ONLY_LAUNCHER = "scripts/codex_harness/run_pr122_source_only.sh"


def _source_only_paths(root: Path) -> list[str]:
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = (
        Path(sys.executable).absolute().parent.parent
        / "lib"
        / version
        / "site-packages"
    )
    return [
        str(root / "htt/src"),
        str(root / "htt"),
        str(site_packages),
    ]


def _require_source_only_launcher() -> None:
    """Fail before project/site imports unless the bound launcher is active."""

    root = Path(__file__).resolve().parents[2]
    launcher = root / _SOURCE_ONLY_LAUNCHER
    prefix_raw = os.environ.get(_SOURCE_ONLY_PREFIX_ENV)
    site_raw = os.environ.get(_SOURCE_ONLY_SITE_ENV)
    expected_site = _source_only_paths(root)[2]
    hidden = (
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
    )
    if (
        not sys.flags.isolated
        or not sys.flags.no_site
        or not sys.dont_write_bytecode
        or os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1"
        or any(os.environ.get(key) is not None for key in hidden)
        or os.environ.get(_SOURCE_ONLY_TARGET_ENV) != _SOURCE_ONLY_TARGET
        or not isinstance(prefix_raw, str)
        or not prefix_raw
        or sys.pycache_prefix != prefix_raw
        or site_raw != expected_site
        or sys.path[:3] != [str(root / "htt/src"), str(root / "htt"), expected_site]
        or Path.cwd().resolve() != root
        or launcher.is_symlink()
        or not launcher.is_file()
    ):
        raise SystemExit(
            "PR-122 CLI requires scripts/codex_harness/" "run_pr122_source_only.sh"
        )
    prefix = Path(prefix_raw)
    if (
        not prefix.is_absolute()
        or prefix.is_symlink()
        or not prefix.is_dir()
        or any(prefix.iterdir())
    ):
        raise SystemExit("invalid PR-122 source-only cache state")
    resolved_prefix = prefix.resolve()
    for forbidden in (
        root,
        root / "venv",
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
    ):
        try:
            resolved_prefix.relative_to(forbidden.resolve())
        except ValueError:
            continue
        raise SystemExit("PR-122 source-only cache is not external")
    expected_hash = hashlib.sha256(launcher.read_bytes()).hexdigest()
    if os.environ.get(_SOURCE_ONLY_LAUNCHER_HASH_ENV) != expected_hash:
        raise SystemExit("PR-122 source-only launcher hash mismatch")


if __name__ == "__main__":
    _require_source_only_launcher()

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON_SRC = REPO_ROOT / "htt/src"
if str(COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(COMMON_SRC))

from common.evidence_graph import (  # noqa: E402
    EvidenceAxes,
    EvidenceEdge,
    EvidenceEdgeKind,
    EvidenceGraph,
    EvidenceGraphError,
    EvidenceNode,
    EvidenceNodeKind,
    EvidenceReceipt,
    EvidenceReceiptBody,
    EvidenceStatus,
    ProcessResult,
    ReceiptDependency,
    ReceiptDependencyKind,
    TestExecution,
    authority_registry_content_ref,
    verify_pytest_environment_inputs,
    verify_pytest_selector_inputs,
)
from common.mes_successor_registry import (  # noqa: E402
    EGS3_BRANCH_SEAL_PATH,
    MesConsumerDeclaration,
    MesConsumerIssueCode,
    SourceAvailability,
    SourceHashBinding,
    current_mes_successor_registry,
    finding_codes,
    scan_declared_mes_consumers,
    validate_mes_successor_registry,
)
from common.remediation_state import (  # noqa: E402
    AuthorityRegistry,
    PrincipalRecord,
    ScientificStatus,
)


GRAPH_SCHEMA = "htt.pr122.claim_evidence_graph_bundle.v1"
DEFAULT_SPEC = Path("docs/research_program/long_horizon_rescue/pr122_spec.yaml")
DEFAULT_CONSUMERS = Path(
    "docs/research_program/long_horizon_rescue/pr122_active_mes_consumers.yaml"
)
DEFAULT_AUTHORITY = Path(
    "docs/research_program/long_horizon_rescue/pr122_authority_snapshot.yaml"
)
DEFAULT_TEST_EXECUTION = Path("docs/generated/pr122_test_execution.json")
DEFAULT_GRAPH = Path("docs/generated/pr122_claim_evidence_graph.json")
DEFAULT_CLOSURE_JSON = Path("docs/generated/pr122_claim_closure_report.json")
DEFAULT_CLOSURE_MD = Path("docs/generated/pr122_claim_closure_report.md")
DEFAULT_MES_SCAN = Path("docs/generated/pr122_mes_successor_scan.json")
DEFAULT_RELEASE_RECEIPT = Path("docs/generated/pr122_release_receipt.json")
DEFAULT_PARENT_RECEIPT = Path("docs/generated/pr122_parent_receipt.json")
DEFAULT_ARTIFACT_MANIFEST = Path("docs/generated/pr122_artifact_manifest.json")
ROADMAP = Path("docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md")
PR121_RECEIPT = Path("docs/generated/pr121_hermetic_replay_receipt.json")
FREEZE_CONSUMER = Path("scripts/check_publication_claim_freeze.py")
PACKAGE_CONSUMER = Path("scripts/build_external_audit_package.py")
GRAPH_PRODUCER = Path("htt/src/common/evidence_graph.py")
MES_PRODUCER = Path("htt/src/common/mes_successor_registry.py")
GRAPH_BUILDER = Path("scripts/codex_harness/build_claim_evidence_graph.py")
SOURCE_ONLY_LAUNCHER = Path(_SOURCE_ONLY_LAUNCHER)
EVIDENCE_VERIFIER = Path("htt/src/common/release_evidence_binding.py")
EVIDENCE_PIN = Path("htt/src/common/release_evidence_pin.py")
PYTEST_EVIDENCE_PLUGIN = Path("htt/src/common/pytest_execution_evidence.py")
REMEDIATION_KERNEL = Path("htt/src/common/remediation_state.py")
COMMON_CONTRACTS = Path("htt/src/common/contracts.py")
STATUS_IMPLEMENTATION = Path("htt/src/common/status_snapshot.py")
INFERENCE_IMPLEMENTATION = Path("htt/htt/htt/infer/prior_sweep.py")
NULL_COMPETITION_CONTRACT = Path("htt/htt/htt/infer/null_competition.py")
GRAPH_GENERATING_COMMAND = (
    "scripts/codex_harness/run_pr122_source_only.sh "
    "scripts/codex_harness/build_claim_evidence_graph.py"
)
ISSUED_AT = "2026-07-16T00:00:00+09:00"
AUTHOR = "codex:/root"
ADJUDICATOR = "codex:/root/pr122_claim_auditor"
AUTHORITATIVE_PYTEST_ARGV = (
    "-p",
    "common.pytest_execution_evidence",
    "-p",
    "no:cacheprovider",
    "--import-mode=importlib",
    "--rootdir",
    ".",
    "-c",
    "pytest.ini",
    "-q",
    "--evidence-output",
    "<evidence-output>",
    "tests/contracts/test_evidence_graph.py",
    "tests/contracts/test_pytest_execution_evidence.py",
    "tests/contracts/test_mes_successor_registry.py",
    "tests/htt/test_inference_adequacy_gates.py",
    (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_data_only_pin_rejects_noncanonical_trust_root_fields"
    ),
    (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_stale_but_well_formed_release_pin_is_rejected_before_audit_disclosure"
    ),
    (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_invalid_artifact_manifest_structure_is_rejected"
    ),
    (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_graph_bound_verifier_source_drift_is_rejected"
    ),
    (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_executable_release_pin_payload_is_rejected_without_execution"
    ),
    (
        "tests/pr_cards/"
        "test_pr_122_claim_addressed_evidence_graph_content_addressed.py::"
        "test_spec_registers_every_required_false_green_mutation_and_pr4_firewall"
    ),
    (
        "tests/pr_cards/"
        "test_pr_122_claim_addressed_evidence_graph_content_addressed.py::"
        "test_arbitrary_readiness_field_is_rejected_at_graph_boundary"
    ),
    (
        "tests/pr_cards/"
        "test_pr_122_claim_addressed_evidence_graph_content_addressed.py::"
        "test_failed_or_tampered_pr121_environment_receipt_is_rejected"
    ),
    (
        "tests/pr_cards/"
        "test_pr_122_claim_addressed_evidence_graph_content_addressed.py::"
        "test_pr122_authority_snapshot_is_an_immutable_exact_scope_slice"
    ),
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _render_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _resolve(root: Path, relative: Path) -> Path:
    if relative.is_absolute():
        candidate = relative.resolve()
    else:
        candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {relative}") from exc
    return candidate


def _relative_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be an exact repository-relative path")
    if "\\" in value:
        raise ValueError(f"{field} must use POSIX separators")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{field} must be a safe repository-relative path")
    return path.as_posix()


def _load_yaml_mapping(path: Path) -> Mapping[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"expected JSON mapping at {path}")
    return payload


def _assert_exact_pytest_replay(
    expected: Mapping[str, object], replayed: Mapping[str, object]
) -> None:
    """Reject any resealed receipt that exact hermetic replay does not reproduce."""

    if _canonical_bytes(expected) != _canonical_bytes(replayed):
        raise EvidenceGraphError(
            "checked-in pytest receipt does not match exact hermetic replay"
        )


def _run_authoritative_pytest(root: Path, output: Path) -> Mapping[str, object]:
    """Run pytest without site startup, editable .pth hooks, or bytecode caches."""

    source_paths = _source_only_paths(root)
    bootstrap = (
        "import os,runpy,sys;"
        f"sys.path[:0]={source_paths!r};"
        "[os.environ.pop(k,None) for k in "
        "('PYTHONPATH','PYTEST_ADDOPTS','PYTEST_PLUGINS')];"
        "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';"
        "sys.argv[0]='pytest';"
        "runpy.run_module('pytest',run_name='__main__')"
    )
    replay_argv = [
        str(output) if value == "<evidence-output>" else value
        for value in AUTHORITATIVE_PYTEST_ARGV
    ]
    clean_env = dict(os.environ)
    for key in (
        _SOURCE_ONLY_PREFIX_ENV,
        _SOURCE_ONLY_LAUNCHER_HASH_ENV,
        _SOURCE_ONLY_SITE_ENV,
        _SOURCE_ONLY_TARGET_ENV,
    ):
        clean_env.pop(key, None)
    for key in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        clean_env.pop(key, None)
    clean_env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    with tempfile.TemporaryDirectory(prefix="pr122-pytest-pycache-") as cache:
        cache_path = Path(cache)
        command = [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-X",
            f"pycache_prefix={cache_path}",
            "-c",
            bootstrap,
            *replay_argv,
        ]
        completed = subprocess.run(
            command,
            cwd=root,
            env=clean_env,
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
        )
        if any(cache_path.iterdir()):
            raise EvidenceGraphError(
                "authoritative pytest wrote to its source-only bytecode cache"
            )
    if completed.returncode != 0:
        raise EvidenceGraphError(
            "authoritative pytest failed before graph closure: "
            f"exit {completed.returncode}\n{completed.stdout[-2000:]}"
            f"{completed.stderr[-2000:]}"
        )
    if not output.is_file() or output.is_symlink():
        raise EvidenceGraphError(
            "authoritative pytest did not produce a regular receipt"
        )
    return _load_json_mapping(output)


def _replay_pytest_receipt(
    root: Path, expected: Mapping[str, object]
) -> Mapping[str, object]:
    """Independently reproduce the authoritative receipt before graph closure."""

    raw_argv = expected.get("normalized_invocation_argv")
    if not isinstance(raw_argv, Sequence) or isinstance(raw_argv, (str, bytes)):
        raise EvidenceGraphError("pytest receipt lacks normalized invocation argv")
    if tuple(raw_argv) != AUTHORITATIVE_PYTEST_ARGV:
        raise EvidenceGraphError(
            "pytest receipt invocation does not match the authoritative selector"
        )
    environment = expected.get("environment_contract")
    if not isinstance(environment, Mapping):
        raise EvidenceGraphError("pytest receipt lacks environment contract")
    hidden = environment.get("hidden_controls")
    if not isinstance(hidden, Mapping) or hidden.get("pythonpath_status") != "unset":
        raise EvidenceGraphError(
            "authoritative pytest replay requires an unset PYTHONPATH"
        )

    with tempfile.TemporaryDirectory(prefix="pr122-pytest-replay-") as temporary:
        output = Path(temporary) / "receipt.json"
        replayed = _run_authoritative_pytest(root, output)
    _assert_exact_pytest_replay(expected, replayed)
    return replayed


def _authority_registry(path: Path) -> AuthorityRegistry:
    payload = _load_yaml_mapping(path)
    if payload.get("schema") != "htt.pr122.authority_snapshot.v1":
        raise ValueError("unsupported PR-122 authority snapshot schema")
    rows = payload.get("principals")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("authority registry principals must be a sequence")
    records: list[PrincipalRecord] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("authority principal must be a mapping")
        records.append(
            PrincipalRecord(
                principal_id=row["principal_id"],
                identity_fingerprint=row["identity_fingerprint"],
                aliases=row["aliases"],
                allowed_roles=row["allowed_roles"],
                allowed_scopes=row["allowed_scopes"],
                independence_class=row["independence_class"],
                valid_from=row["valid_from"],
                valid_until=row["valid_until"],
                revoked=row["revoked"],
                verifier=row["verifier"],
            )
        )
    registry = AuthorityRegistry(tuple(records))
    _validate_authority_snapshot(payload, registry)
    return registry


def _validate_authority_snapshot(
    payload: Mapping[str, object], registry: AuthorityRegistry
) -> None:
    """Validate the immutable PR-122 slice without consulting a live registry."""

    if (
        payload.get("snapshot_status") != "immutable_historical_authority_slice"
        or payload.get("immutable") is not True
        or payload.get("scope") != "PR-122"
        or payload.get("selection_rule") != "exact_pr122_scope_rows_at_issuance"
    ):
        raise ValueError("PR-122 authority snapshot metadata is invalid")
    source = payload.get("source_registry")
    if not isinstance(source, Mapping) or set(source) != {
        "path",
        "file_sha256_at_issuance",
        "authority_registry_ref_at_issuance",
    }:
        raise ValueError("PR-122 authority snapshot source disclosure is invalid")
    if source.get("path") != "docs/codex_handoff/authorized_principals.yaml":
        raise ValueError("PR-122 authority snapshot source path is invalid")
    for field in ("file_sha256_at_issuance", "authority_registry_ref_at_issuance"):
        value = source.get(field)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError("PR-122 authority snapshot source hash is invalid")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError(
                "PR-122 authority snapshot source hash is invalid"
            ) from exc
    rows = payload.get("principals")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("PR-122 authority snapshot principals are invalid")
    expected = {
        AUTHOR: ("author", "correlated_internal_author"),
        ADJUDICATOR: (
            "adjudicator",
            "correlated_internal_non_author_review",
        ),
    }
    if {
        str(row.get("principal_id")) for row in rows if isinstance(row, Mapping)
    } != set(expected) or len(rows) != len(expected):
        raise ValueError("PR-122 authority snapshot must contain the exact principals")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("PR-122 authority snapshot principal is invalid")
        principal_id = str(row.get("principal_id"))
        role, independence = expected[principal_id]
        if (
            row.get("allowed_roles") != [role]
            or row.get("allowed_scopes") != ["PR-122"]
            or row.get("independence_class") != independence
            or row.get("verifier") != "unverified_internal_process_identity"
            or row.get("revoked") is not False
            or row.get("can_promote_scientific_status") is not False
        ):
            raise ValueError("PR-122 authority snapshot broadens principal authority")
    expected_rows_hash = _sha256_bytes(_canonical_bytes(list(rows)))
    if payload.get("selected_principal_rows_sha256") != expected_rows_hash:
        raise ValueError("PR-122 authority snapshot principal row hash is invalid")
    expected_ref = authority_registry_content_ref(registry)
    if payload.get("snapshot_authority_registry_ref") != expected_ref:
        raise ValueError("PR-122 authority snapshot registry ref is invalid")


def _validate_pr121_environment_receipt(payload: Mapping[str, object]) -> None:
    if payload.get("schema") != "htt.pr121.hermetic_replay_receipt.v1":
        raise EvidenceGraphError("PR-121 environment receipt schema is invalid")
    if payload.get("pr_id") != "PR-121" or payload.get("overall_status") != "pass":
        raise EvidenceGraphError("PR-121 environment receipt is not completed-success")
    expected = payload.get("receipt_content_hash")
    if not isinstance(expected, str) or len(expected) != 64:
        raise EvidenceGraphError("PR-121 environment receipt lacks content hash")
    unsigned = {
        key: value for key, value in payload.items() if key != "receipt_content_hash"
    }
    pr121_bytes = (
        json.dumps(
            unsigned,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    if _sha256_bytes(pr121_bytes) != expected:
        raise EvidenceGraphError("PR-121 environment receipt content hash is invalid")
    rows = payload.get("clean_install_matrix")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise EvidenceGraphError("PR-121 environment receipt lacks clean-install cells")
    for row in rows:
        if not isinstance(row, Mapping) or row.get("status") != "pass":
            raise EvidenceGraphError(
                "PR-121 environment receipt contains a failed cell"
            )


def _validate_mutation_execution_matrix(
    spec: Mapping[str, object], test_execution: TestExecution
) -> tuple[dict[str, str], ...]:
    mutation_ids = spec.get("mutations")
    rows = spec.get("mutation_execution_matrix")
    if not isinstance(mutation_ids, Sequence) or isinstance(mutation_ids, (str, bytes)):
        raise EvidenceGraphError("PR-122 spec mutations must be a sequence")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise EvidenceGraphError("PR-122 spec requires mutation_execution_matrix")
    expected_ids = {str(value) for value in mutation_ids}
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    outcomes = {row.test_id: row.outcome.value for row in test_execution.results}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "mutation_id",
            "test_node_id",
            "expected_outcome",
        }:
            raise EvidenceGraphError("invalid mutation execution matrix row")
        mutation_id = str(row["mutation_id"])
        test_node_id = str(row["test_node_id"])
        expected_outcome = str(row["expected_outcome"])
        if mutation_id in seen:
            raise EvidenceGraphError("mutation execution matrix contains duplicates")
        seen.add(mutation_id)
        if expected_outcome != "PASSED_REJECTION_OR_EXPLICIT_DOWNCLAIM":
            raise EvidenceGraphError("mutation matrix outcome is not fail-closed")
        if (
            test_node_id not in test_execution.collected_test_ids
            or test_node_id not in test_execution.executed_test_ids
            or outcomes.get(test_node_id) != "PASSED"
        ):
            raise EvidenceGraphError(
                f"mutation {mutation_id} lacks an exact passing executed test identity"
            )
        normalized.append(
            {
                "mutation_id": mutation_id,
                "test_node_id": test_node_id,
                "expected_outcome": expected_outcome,
            }
        )
    if seen != expected_ids:
        raise EvidenceGraphError(
            "mutation execution matrix does not cover the exact registered corpus"
        )
    return tuple(sorted(normalized, key=lambda row: row["mutation_id"]))


def _bound_worktree_state(root: Path, input_rows: Sequence[str]) -> str:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceGraphError("cannot resolve git HEAD for PR-122 metadata") from exc
    if len(head) != 40:
        raise EvidenceGraphError("git HEAD is not an exact SHA-1 commit id")
    state_ref = _sha256_bytes(_canonical_bytes(sorted(input_rows)))
    return f"HEAD:{head};bound_input_state_sha256:{state_ref}"


def _mes_declarations(root: Path, path: Path) -> tuple[MesConsumerDeclaration, ...]:
    payload = _load_yaml_mapping(path)
    if payload.get("schema") != "htt.long_horizon.pr122_active_mes_consumers.v1":
        raise ValueError("unsupported PR-122 MES consumer inventory schema")
    rows = payload.get("active_consumers")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("active MES consumer inventory must be non-empty")
    declarations: list[MesConsumerDeclaration] = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "consumer_id",
            "path",
            "sha256",
        }:
            raise ValueError("active MES consumer row has invalid fields")
        relative = _relative_path(row["path"], "MES consumer path")
        declarations.append(
            MesConsumerDeclaration(
                consumer_id=str(row["consumer_id"]),
                source=SourceHashBinding(
                    path=relative,
                    availability=SourceAvailability.AVAILABLE,
                    sha256=str(row["sha256"]),
                ),
            )
        )
    # The scanner rechecks every declared hash.  This explicit precheck makes
    # stale inventory a build error rather than an expected scientific blocker.
    for declaration in declarations:
        if (
            _sha256_file(_resolve(root, Path(declaration.source.path)))
            != declaration.source.sha256
        ):
            raise ValueError(
                f"active MES consumer inventory is stale: {declaration.source.path}"
            )
    return tuple(declarations)


def _axes(
    evidence_status: EvidenceStatus = EvidenceStatus.PRESENT,
    *,
    process_result: ProcessResult = ProcessResult.PASS,
    scientific_status: ScientificStatus = ScientificStatus.OPEN,
) -> EvidenceAxes:
    return EvidenceAxes(process_result, evidence_status, scientific_status)


def _file_node(
    root: Path,
    *,
    kind: EvidenceNodeKind,
    label: str,
    path: Path,
    axes: EvidenceAxes | None = None,
    extra: Mapping[str, object] | None = None,
) -> EvidenceNode:
    source = _resolve(root, path)
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"evidence source is missing or non-regular: {path}")
    metadata: dict[str, object] = {"path": path.as_posix()}
    metadata.update(dict(extra or {}))
    return EvidenceNode(
        kind=kind,
        label=label,
        content_sha256=_sha256_file(source),
        axes=axes or _axes(),
        metadata=metadata,
    )


def _inline_node(
    *,
    kind: EvidenceNodeKind,
    label: str,
    payload: Mapping[str, object],
    axes: EvidenceAxes,
) -> EvidenceNode:
    return EvidenceNode(
        kind=kind,
        label=label,
        content_sha256=_sha256_bytes(_canonical_bytes(payload)),
        axes=axes,
        metadata={"inline_contract": dict(payload)},
    )


def _edge(
    kind: EvidenceEdgeKind,
    source: EvidenceNode,
    target: EvidenceNode,
    role: str,
) -> EvidenceEdge:
    return EvidenceEdge(
        kind=kind,
        source_ref=source.node_ref,
        target_ref=target.node_ref,
        metadata={"role": role},
    )


def _build_bundle(
    *,
    root: Path,
    spec_path: Path,
    consumers_path: Path,
    authority_path: Path,
    test_execution_path: Path,
    mes_scan_path: Path,
) -> tuple[EvidenceGraph, dict[str, object], EvidenceReceipt, EvidenceReceipt, bytes]:
    spec = _resolve(root, spec_path)
    consumers = _resolve(root, consumers_path)
    authority = _resolve(root, authority_path)
    test_path = _resolve(root, test_execution_path)
    test_payload = _load_json_mapping(test_path)
    _replay_pytest_receipt(root, test_payload)
    spec_payload = _load_yaml_mapping(spec)
    pr121_payload = _load_json_mapping(_resolve(root, PR121_RECEIPT))
    _validate_pr121_environment_receipt(pr121_payload)
    verify_pytest_selector_inputs(root, test_payload)
    parent_environment_lock = pr121_payload.get("environment_lock")
    if not isinstance(parent_environment_lock, Mapping):
        raise EvidenceGraphError("PR-121 environment receipt lacks environment_lock")
    environment_ref = verify_pytest_environment_inputs(
        root,
        test_payload,
        parent_environment_lock=parent_environment_lock,
    )
    test_execution = TestExecution.from_pytest_evidence(test_payload)
    if test_execution.environment_ref != environment_ref:
        raise EvidenceGraphError(
            "PR-122 test execution does not bind its verified environment"
        )
    if not test_execution.is_authoritative:
        raise EvidenceGraphError(
            "PR-122 graph requires nonzero, fully executed passing test evidence"
        )
    mutation_execution_matrix = _validate_mutation_execution_matrix(
        spec_payload, test_execution
    )

    declarations = _mes_declarations(root, consumers)
    mes_report = scan_declared_mes_consumers(root, declarations)
    mes_registry = current_mes_successor_registry()
    registry_report = validate_mes_successor_registry(root)
    codes = finding_codes(mes_report)
    registry_codes = finding_codes(registry_report)
    required_blockers = {
        MesConsumerIssueCode.SUCCESSOR_MISSING.value,
        MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED.value,
        MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value,
    }
    integrity_failures = {
        MesConsumerIssueCode.SOURCE_MISSING.value,
        MesConsumerIssueCode.SOURCE_NOT_REGULAR.value,
        MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value,
        MesConsumerIssueCode.CONSUMER_PARSE_ERROR.value,
        MesConsumerIssueCode.NO_ACTIVE_CONSUMERS_DECLARED.value,
        MesConsumerIssueCode.UNTRUSTED_REGISTRY_OVERRIDE.value,
        MesConsumerIssueCode.DIAGNOSTIC_WITNESS_INVALID.value,
        MesConsumerIssueCode.INVENTORY_INVALID.value,
        MesConsumerIssueCode.UNDECLARED_ACTIVE_CONSUMER.value,
        MesConsumerIssueCode.DECLARED_CONSUMER_NOT_DISCOVERED.value,
        MesConsumerIssueCode.EXCLUSION_HASH_MISMATCH.value,
    }
    if not required_blockers <= codes:
        raise ValueError(
            "MES release scan no longer records the required pre-PR124 blockers"
        )
    if codes & integrity_failures:
        raise ValueError(
            f"MES release scan has integrity failures: {sorted(codes & integrity_failures)}"
        )
    if mes_report.release_allowed:
        raise ValueError("MES release unexpectedly became allowed before PR-124")
    if registry_codes & integrity_failures:
        raise ValueError(
            "MES registry witness has integrity failures: "
            f"{sorted(registry_codes & integrity_failures)}"
        )
    if (
        not {
            MesConsumerIssueCode.SUCCESSOR_MISSING.value,
            MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED.value,
        }
        <= registry_codes
        or registry_report.release_allowed
    ):
        raise ValueError("MES registry lost its pre-PR124 authority blocker")

    provenance_paths = (
        spec_path,
        consumers_path,
        authority_path,
        test_execution_path,
        ROADMAP,
        PR121_RECEIPT,
        GRAPH_PRODUCER,
        GRAPH_BUILDER,
        SOURCE_ONLY_LAUNCHER,
        MES_PRODUCER,
        EVIDENCE_VERIFIER,
        PYTEST_EVIDENCE_PLUGIN,
        REMEDIATION_KERNEL,
        COMMON_CONTRACTS,
        STATUS_IMPLEMENTATION,
        INFERENCE_IMPLEMENTATION,
        NULL_COMPETITION_CONTRACT,
        Path(mes_registry.egs3_branch_witness.source.path),
        Path(EGS3_BRANCH_SEAL_PATH),
        FREEZE_CONSUMER,
        PACKAGE_CONSUMER,
    )
    provenance_rows = [
        f"{path.as_posix()}:{_sha256_file(_resolve(root, path))}"
        for path in provenance_paths
    ]
    provenance_rows.extend(
        f"{declaration.source.path}:{declaration.source.sha256}"
        for declaration in declarations
    )
    provenance_rows = sorted(set(provenance_rows))
    worktree_state = _bound_worktree_state(root, provenance_rows)

    mes_scan_payload: dict[str, object] = {
        "schema": "htt.pr122.mes_successor_scan.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "artifact_mode": "governance_diagnostic",
        "allowed_use": "release_blocker_inventory_only",
        "transfer_source": "none",
        "config_hash": _sha256_file(consumers),
        "input_hashes": [
            f"{consumers_path.as_posix()}:{_sha256_file(consumers)}",
            (
                f"{mes_registry.egs3_branch_witness.source.path}:"
                f"{mes_registry.egs3_branch_witness.source.sha256}"
            ),
            (
                f"{EGS3_BRANCH_SEAL_PATH}:"
                f"{mes_registry.egs3_branch_witness.seal.sha256}"
            ),
            *[f"{item.source.path}:{item.source.sha256}" for item in declarations],
        ],
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": [
            "MES scan success is process evidence only.",
            "The typed scientific successor remains blocked pending PR-124.",
            "No MES coefficient is validated or replaced by PR-122.",
        ],
        "generating_command": GRAPH_GENERATING_COMMAND,
        "git_commit_or_worktree_state": worktree_state,
        "status": "EXPECTED_BLOCKED_PENDING_PR124",
        "scan": mes_report.as_payload(),
        "registry_scan": registry_report.as_payload(),
    }
    mes_scan_bytes = _render_json(mes_scan_payload)

    present = _axes()
    blocked = _axes(EvidenceStatus.BLOCKED, process_result=ProcessResult.PASS)
    mechanics_claim = _inline_node(
        kind=EvidenceNodeKind.CLAIM,
        label="pr122.fail_closed_mechanics",
        payload={
            "claim_id": "pr122.fail_closed_mechanics",
            "claim_level": "roadmap_rescue_v1:C1",
            "statement": "typed content-addressed evidence closure mechanics execute reproducibly",
        },
        axes=present,
    )
    release_claim = _inline_node(
        kind=EvidenceNodeKind.CLAIM,
        label="pr122.mes_release_authority",
        payload={
            "claim_id": "pr122.mes_release_authority",
            "claim_level": "roadmap_rescue_v1:C1",
            "statement": "active MES release remains blocked until the PR-124 typed successor is authorized",
        },
        axes=present,
    )
    d2_claim = _inline_node(
        kind=EvidenceNodeKind.CLAIM,
        label="pr122.d2_rust_authority",
        payload={
            "claim_id": "pr122.d2_rust_authority",
            "claim_level": "roadmap_rescue_v1:C1",
            "statement": (
                "D2 Rust authority remains blocked until PR-124 supplies a "
                "nonzero independently verified target and execution receipt"
            ),
        },
        axes=present,
    )
    graph_producer = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="common.evidence_graph",
        path=GRAPH_PRODUCER,
    )
    graph_builder = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="codex_harness.build_claim_evidence_graph",
        path=GRAPH_BUILDER,
        extra={
            "source_only_invocation": [
                SOURCE_ONLY_LAUNCHER.as_posix(),
                GRAPH_BUILDER.as_posix(),
            ],
            "authoritative_test_receipt_argv": ["--write-test-execution"],
        },
    )
    source_only_launcher = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="codex_harness.pr122_source_only_launcher",
        path=SOURCE_ONLY_LAUNCHER,
        extra={
            "trust_role": "source-only process launcher",
            "allowed_targets": [
                GRAPH_BUILDER.as_posix(),
                FREEZE_CONSUMER.as_posix(),
                PACKAGE_CONSUMER.as_posix(),
            ],
        },
    )
    verifier_producer = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="common.release_evidence_binding",
        path=EVIDENCE_VERIFIER,
        extra={"trust_role": "graph-bound verifier implementation"},
    )
    pytest_evidence_producer = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="common.pytest_execution_evidence",
        path=PYTEST_EVIDENCE_PLUGIN,
    )
    mes_producer = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="common.mes_successor_registry",
        path=MES_PRODUCER,
    )
    d2_producer = _file_node(
        root,
        kind=EvidenceNodeKind.PRODUCER,
        label="common.d2_authority_gate",
        path=GRAPH_PRODUCER,
    )
    roadmap_input = _file_node(
        root, kind=EvidenceNodeKind.INPUT, label="long_horizon_roadmap", path=ROADMAP
    )
    consumer_inventory_input = _file_node(
        root,
        kind=EvidenceNodeKind.INPUT,
        label="active_mes_consumers",
        path=consumers_path,
    )
    witness_source_input = _file_node(
        root,
        kind=EvidenceNodeKind.INPUT,
        label="mes.egs3_diagnostic_witness_source",
        path=Path(mes_registry.egs3_branch_witness.source.path),
        extra={"allowed_use": "diagnostic process evidence only"},
    )
    witness_seal_input = _file_node(
        root,
        kind=EvidenceNodeKind.INPUT,
        label="mes.egs3_diagnostic_witness_seal",
        path=Path(EGS3_BRANCH_SEAL_PATH),
        extra={"allowed_use": "diagnostic process evidence only"},
    )
    consumer_source_inputs = tuple(
        _file_node(
            root,
            kind=EvidenceNodeKind.INPUT,
            label=f"mes_consumer.{declaration.consumer_id}",
            path=Path(declaration.source.path),
            extra={"consumer_id": declaration.consumer_id},
        )
        for declaration in declarations
    )
    authority_input = _file_node(
        root,
        kind=EvidenceNodeKind.INPUT,
        label="pr122_authority_snapshot",
        path=authority_path,
    )
    missing_successor = _inline_node(
        kind=EvidenceNodeKind.INPUT,
        label="mes.typed-successor.pr124",
        payload={
            "availability": "MISSING",
            "scientific_status": "BLOCKED_PENDING_PR124",
            "source": "htt/src/common/mes_theorem_authority.py",
        },
        axes=blocked,
    )
    missing_d2_target = _inline_node(
        kind=EvidenceNodeKind.INPUT,
        label="d2.rust-target.pr124",
        payload={
            "availability": "MISSING",
            "process_result": "NOT_RUN",
            "scientific_status": "BLOCKED_PENDING_PR124",
            "required": [
                "nonzero_rust_target_identity",
                "source_hash",
                "input_hashes",
                "toolchain_lock",
                "collected_test_ids",
                "executed_test_ids",
                "independent_execution_receipt",
            ],
        },
        axes=_axes(
            EvidenceStatus.BLOCKED,
            process_result=ProcessResult.NOT_RUN,
            scientific_status=ScientificStatus.BLOCKED,
        ),
    )
    config_node = _file_node(
        root, kind=EvidenceNodeKind.CONFIG, label="pr122_spec", path=spec_path
    )
    environment_node = _file_node(
        root,
        kind=EvidenceNodeKind.ENVIRONMENT,
        label="pr121_hermetic_environment",
        path=PR121_RECEIPT,
        extra={"claim_boundary": "replay mechanics only"},
    )
    test_node = EvidenceNode(
        kind=EvidenceNodeKind.TEST,
        label="pr122_mutation_and_contract_suite",
        content_sha256=test_execution.execution_ref,
        axes=EvidenceAxes(
            test_execution.axes[0],
            test_execution.axes[1],
            ScientificStatus.OPEN,
        ),
        metadata={
            "path": test_execution_path.as_posix(),
            "file_sha256": _sha256_file(test_path),
            "environment_ref": environment_ref,
            "parent_environment_receipt_sha256": _sha256_file(
                _resolve(root, PR121_RECEIPT)
            ),
        },
        test_execution=test_execution,
    )
    test_artifact = _file_node(
        root,
        kind=EvidenceNodeKind.ARTIFACT,
        label="pr122_test_execution",
        path=test_execution_path,
    )
    graph_loader_consumer = _file_node(
        root,
        kind=EvidenceNodeKind.CONSUMER,
        label="claim_graph.test_execution_loader",
        path=GRAPH_BUILDER,
    )
    mes_scan_artifact = EvidenceNode(
        kind=EvidenceNodeKind.ARTIFACT,
        label="pr122_mes_successor_scan",
        content_sha256=_sha256_bytes(mes_scan_bytes),
        axes=present,
        metadata={
            "path": mes_scan_path.as_posix(),
            "status": "expected_blocked_pending_PR124",
        },
    )
    freeze_consumer = _file_node(
        root,
        kind=EvidenceNodeKind.CONSUMER,
        label="publication_claim_freeze",
        path=FREEZE_CONSUMER,
    )
    package_consumer = _file_node(
        root,
        kind=EvidenceNodeKind.CONSUMER,
        label="external_audit_package",
        path=PACKAGE_CONSUMER,
    )
    nodes = (
        mechanics_claim,
        release_claim,
        d2_claim,
        source_only_launcher,
        graph_builder,
        graph_producer,
        verifier_producer,
        pytest_evidence_producer,
        mes_producer,
        d2_producer,
        roadmap_input,
        consumer_inventory_input,
        witness_source_input,
        witness_seal_input,
        *consumer_source_inputs,
        authority_input,
        missing_successor,
        missing_d2_target,
        config_node,
        environment_node,
        test_node,
        test_artifact,
        mes_scan_artifact,
        graph_loader_consumer,
        freeze_consumer,
        package_consumer,
    )
    edges = (
        _edge(
            EvidenceEdgeKind.PRODUCED_BY,
            mechanics_claim,
            graph_builder,
            "claim graph builder",
        ),
        _edge(
            EvidenceEdgeKind.PRODUCED_BY,
            release_claim,
            mes_producer,
            "MES release policy producer",
        ),
        _edge(EvidenceEdgeKind.PRODUCED_BY, d2_claim, d2_producer, "D2 authority gate"),
        _edge(
            EvidenceEdgeKind.DEPENDS_ON,
            graph_builder,
            source_only_launcher,
            "source-only launcher",
        ),
        _edge(
            EvidenceEdgeKind.DEPENDS_ON,
            graph_builder,
            graph_producer,
            "typed closure kernel",
        ),
        _edge(
            EvidenceEdgeKind.DEPENDS_ON,
            graph_builder,
            verifier_producer,
            "graph-bound release verifier",
        ),
        _edge(
            EvidenceEdgeKind.DEPENDS_ON,
            graph_builder,
            pytest_evidence_producer,
            "pytest execution plugin",
        ),
        _edge(
            EvidenceEdgeKind.DEPENDS_ON,
            mes_producer,
            graph_producer,
            "shared closure kernel",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            graph_builder,
            roadmap_input,
            "roadmap contract",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            graph_builder,
            authority_input,
            "immutable PR-122 authority slice",
        ),
        _edge(
            EvidenceEdgeKind.USES_CONFIG, graph_builder, config_node, "PR-122 config"
        ),
        _edge(
            EvidenceEdgeKind.USES_ENVIRONMENT,
            graph_builder,
            environment_node,
            "PR-121 hermetic receipt",
        ),
        _edge(
            EvidenceEdgeKind.CHECKED_BY,
            graph_builder,
            test_node,
            "identity-bound mutation suite",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            graph_producer,
            roadmap_input,
            "roadmap contract",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            graph_producer,
            authority_input,
            "immutable PR-122 authority slice",
        ),
        _edge(
            EvidenceEdgeKind.USES_CONFIG, graph_producer, config_node, "PR-122 config"
        ),
        _edge(
            EvidenceEdgeKind.USES_ENVIRONMENT,
            graph_producer,
            environment_node,
            "PR-121 hermetic receipt",
        ),
        _edge(
            EvidenceEdgeKind.CHECKED_BY,
            graph_producer,
            test_node,
            "identity-bound mutation suite",
        ),
        _edge(
            EvidenceEdgeKind.GENERATES,
            test_node,
            test_artifact,
            "actual test execution receipt",
        ),
        _edge(
            EvidenceEdgeKind.GENERATES,
            pytest_evidence_producer,
            test_artifact,
            "pytest plugin execution receipt",
        ),
        _edge(
            EvidenceEdgeKind.CONSUMED_BY,
            test_artifact,
            graph_loader_consumer,
            "builder loads exact execution receipt",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            mes_producer,
            consumer_inventory_input,
            "hash-bound all-consumer inventory",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            mes_producer,
            witness_source_input,
            "diagnostic witness implementation",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            mes_producer,
            witness_seal_input,
            "diagnostic witness seal",
        ),
        *(
            _edge(
                EvidenceEdgeKind.USES_INPUT,
                mes_producer,
                consumer_input,
                "hash-bound declared MES consumer source",
            )
            for consumer_input in consumer_source_inputs
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            mes_producer,
            missing_successor,
            "typed successor pointer",
        ),
        _edge(
            EvidenceEdgeKind.USES_CONFIG,
            mes_producer,
            config_node,
            "PR-122 release policy",
        ),
        _edge(
            EvidenceEdgeKind.USES_ENVIRONMENT,
            mes_producer,
            environment_node,
            "PR-121 hermetic receipt",
        ),
        _edge(
            EvidenceEdgeKind.CHECKED_BY, mes_producer, test_node, "MES bypass mutations"
        ),
        _edge(
            EvidenceEdgeKind.GENERATES,
            mes_producer,
            mes_scan_artifact,
            "deterministic MES blocker scan",
        ),
        _edge(
            EvidenceEdgeKind.CONSUMED_BY,
            mes_scan_artifact,
            freeze_consumer,
            "exact blocked release closure",
        ),
        _edge(
            EvidenceEdgeKind.CONSUMED_BY,
            mes_scan_artifact,
            package_consumer,
            "audit disclosure only",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            d2_producer,
            roadmap_input,
            "roadmap D2 contract",
        ),
        _edge(
            EvidenceEdgeKind.USES_INPUT,
            d2_producer,
            missing_d2_target,
            "missing nonzero Rust target",
        ),
        _edge(
            EvidenceEdgeKind.USES_CONFIG,
            d2_producer,
            config_node,
            "PR-122 D2 blocker policy",
        ),
        _edge(
            EvidenceEdgeKind.USES_ENVIRONMENT,
            d2_producer,
            environment_node,
            "PR-121 environment receipt",
        ),
        _edge(
            EvidenceEdgeKind.CHECKED_BY,
            d2_producer,
            test_node,
            "zero-test fail-closed mutation",
        ),
    )
    graph = EvidenceGraph(nodes=nodes, edges=edges)
    mechanics_closure = graph.closure(mechanics_claim.node_ref)
    release_closure = graph.closure(release_claim.node_ref)
    d2_closure = graph.closure(d2_claim.node_ref)
    if not mechanics_closure.mechanics_closed:
        raise EvidenceGraphError("clean PR-122 mechanics claim did not close")
    if (
        release_closure.package_eligible
        or release_closure.evidence_status is not EvidenceStatus.BLOCKED
    ):
        raise EvidenceGraphError("pre-PR124 MES release claim did not fail closed")
    if (
        d2_closure.process_result is not ProcessResult.NOT_RUN
        or d2_closure.evidence_status is not EvidenceStatus.BLOCKED
        or d2_closure.claim_release_eligible
    ):
        raise EvidenceGraphError("pre-PR124 D2 authority claim did not fail closed")

    registry = _authority_registry(authority)
    author = registry.resolve(AUTHOR, role="author", scope="PR-122", at=ISSUED_AT)
    adjudicator = registry.resolve(
        ADJUDICATOR, role="adjudicator", scope="PR-122", at=ISSUED_AT
    )
    parent_body = EvidenceReceiptBody.from_graph(
        graph,
        claim_ref=mechanics_claim.node_ref,
        author=author.principal_id,
        author_identity_fingerprint=author.identity_fingerprint,
        adjudicator=adjudicator.principal_id,
        adjudicator_identity_fingerprint=adjudicator.identity_fingerprint,
        authority_registry_ref=authority_registry_content_ref(registry),
        scope="PR-122",
        issued_at=ISSUED_AT,
    )
    parent_receipt = EvidenceReceipt(
        body=parent_body,
        attestation=(
            "unverified_internal_process_identity:"
            + _sha256_bytes(parent_body.canonical_bytes())
        ),
    )
    body = EvidenceReceiptBody.from_graph(
        graph,
        claim_ref=release_claim.node_ref,
        author=author.principal_id,
        author_identity_fingerprint=author.identity_fingerprint,
        adjudicator=adjudicator.principal_id,
        adjudicator_identity_fingerprint=adjudicator.identity_fingerprint,
        authority_registry_ref=authority_registry_content_ref(registry),
        scope="PR-122",
        issued_at=ISSUED_AT,
        dependencies=(
            ReceiptDependency(
                kind=ReceiptDependencyKind.PARENT,
                receipt_ref=parent_receipt.receipt_id,
            ),
        ),
    )
    receipt = EvidenceReceipt(
        body=body,
        attestation=(
            "unverified_internal_process_identity:"
            + _sha256_bytes(body.canonical_bytes())
        ),
    )

    closure_payload: dict[str, object] = {
        "schema": GRAPH_SCHEMA,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "artifact_mode": "governance_diagnostic",
        "allowed_use": "internal_release_mechanics_and_external_audit_disclosure_only",
        "transfer_source": "none",
        "config_hash": _sha256_file(spec),
        "input_hashes": provenance_rows,
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": [
            "Evidence closure validates mechanics, not estimand correctness or scientific truth.",
            "The receipt is correlated internal process disclosure and is not a verified external adjudication.",
            "MES and D2 scientific authority remain blocked pending PR-124.",
            "No native solver, family, geometry, posterior, or detection claim is created.",
        ],
        "generating_command": GRAPH_GENERATING_COMMAND,
        "git_commit_or_worktree_state": worktree_state,
        "graph_ref": graph.graph_ref,
        "mechanics_closure": mechanics_closure.to_record(),
        "release_closure": release_closure.to_record(),
        "d2_closure": d2_closure.to_record(),
        "release_receipt": receipt.audit_disclosure(),
        "release_receipt_id": receipt.receipt_id,
        "parent_receipt": parent_receipt.audit_disclosure(),
        "parent_receipt_id": parent_receipt.receipt_id,
        "authority_registry_ref": body.authority_registry_ref,
        "claim_release_allowed": False,
        "audit_disclosure_allowed": True,
        "artifact_manifest_path": DEFAULT_ARTIFACT_MANIFEST.as_posix(),
        "test_execution": {
            "execution_ref": test_execution.execution_ref,
            "environment_ref": environment_ref,
            "collected_count": test_execution.collected_count,
            "executed_count": test_execution.executed_count,
            "process_result": test_execution.axes[0].value,
            "evidence_status": test_execution.axes[1].value,
            "mutation_execution_matrix": list(mutation_execution_matrix),
            "source_only_producer_command": (
                f"{GRAPH_GENERATING_COMMAND} --write-test-execution"
            ),
            "source_only_launcher_sha256": _sha256_file(
                _resolve(root, SOURCE_ONLY_LAUNCHER)
            ),
        },
        "mes_release": {
            "status": "BLOCKED_PENDING_PR124",
            "consumers_scanned": mes_report.consumers_scanned,
            "finding_codes": sorted(codes),
            "scan_path": mes_scan_path.as_posix(),
            "scan_sha256": _sha256_bytes(mes_scan_bytes),
        },
        "pr4_scope_firewall": {
            "download": "not_started",
            "data_work": "skipped_entirely_by_user_scope",
            "commands_run": 0,
        },
    }
    return graph, closure_payload, receipt, parent_receipt, mes_scan_bytes


def _render_markdown(payload: Mapping[str, object]) -> bytes:
    mechanics = payload["mechanics_closure"]
    release = payload["release_closure"]
    d2 = payload["d2_closure"]
    test = payload["test_execution"]
    mes = payload["mes_release"]
    assert isinstance(mechanics, Mapping)
    assert isinstance(release, Mapping)
    assert isinstance(d2, Mapping)
    assert isinstance(test, Mapping)
    assert isinstance(mes, Mapping)
    lines = [
        "# PR-122 Claim Closure Report",
        "",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        "claim_level: roadmap_rescue_v1:C1",
        f"transfer_source: {payload['transfer_source']}",
        f"config_hash: `{payload['config_hash']}`",
        "input_hashes:",
        *[f"- `{item}`" for item in payload["input_hashes"]],
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        "caveats:",
        *[f"- {item}" for item in payload["caveats"]],
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: `{payload['git_commit_or_worktree_state']}`",
        "",
        "## Exact content addresses",
        "",
        f"- Graph root: `{payload['graph_ref']}`",
        f"- Release receipt: `{payload['release_receipt_id']}`",
        f"- Parent mechanics receipt: `{payload['parent_receipt_id']}`",
        f"- Authority registry: `{payload['authority_registry_ref']}`",
        "",
        "## Orthogonal closure axes",
        "",
        "| Claim | Process | Evidence | Science | Mechanics closed | Package eligible |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| clean mechanics | {mechanics['process_result']} | {mechanics['evidence_status']} | {mechanics['scientific_status']} | {mechanics['mechanics_closed']} | {mechanics['package_eligible']} |",
        f"| MES release | {release['process_result']} | {release['evidence_status']} | {release['scientific_status']} | {release['mechanics_closed']} | {release['package_eligible']} |",
        f"| D2 Rust authority | {d2['process_result']} | {d2['evidence_status']} | {d2['scientific_status']} | {d2['mechanics_closed']} | {d2['package_eligible']} |",
        "",
        "## Test execution identity",
        "",
        f"- Collected: `{test['collected_count']}`",
        f"- Executed: `{test['executed_count']}`",
        f"- Execution ref: `{test['execution_ref']}`",
        f"- Environment ref: `{test['environment_ref']}`",
        "",
        "## Release decision",
        "",
        "- Claim release allowed: `false`",
        "- Audit disclosure allowed: `true`",
        f"- MES successor status: `{mes['status']}`",
        f"- Active MES consumers scanned: `{mes['consumers_scanned']}`",
        f"- MES finding codes: `{', '.join(mes['finding_codes'])}`",
        "- The correlated internal receipt is not a scientific attestation.",
        "",
        "## User data-scope firewall",
        "",
        "- PR3 E2E download remains complete; its analysis stays deferred to PR-150.",
        "- PR4 download is not started. PR4 download, intake, reduction, and analysis were skipped entirely.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def build_outputs(
    *,
    repo_root: Path = REPO_ROOT,
    spec_path: Path = DEFAULT_SPEC,
    consumers_path: Path = DEFAULT_CONSUMERS,
    authority_path: Path = DEFAULT_AUTHORITY,
    test_execution_path: Path = DEFAULT_TEST_EXECUTION,
    graph_path: Path = DEFAULT_GRAPH,
    closure_json_path: Path = DEFAULT_CLOSURE_JSON,
    closure_md_path: Path = DEFAULT_CLOSURE_MD,
    mes_scan_path: Path = DEFAULT_MES_SCAN,
    release_receipt_path: Path = DEFAULT_RELEASE_RECEIPT,
    parent_receipt_path: Path = DEFAULT_PARENT_RECEIPT,
    artifact_manifest_path: Path = DEFAULT_ARTIFACT_MANIFEST,
) -> dict[Path, bytes]:
    root = repo_root.resolve()
    graph, closure, receipt, parent_receipt, mes_scan_bytes = _build_bundle(
        root=root,
        spec_path=spec_path,
        consumers_path=consumers_path,
        authority_path=authority_path,
        test_execution_path=test_execution_path,
        mes_scan_path=mes_scan_path,
    )
    outputs = {
        graph_path: _render_json(graph.to_record()),
        closure_json_path: _render_json(closure),
        closure_md_path: _render_markdown(closure),
        mes_scan_path: mes_scan_bytes,
        release_receipt_path: _render_json(receipt.to_record()),
        parent_receipt_path: _render_json(parent_receipt.to_record()),
    }
    artifact_roles = {
        graph_path: "claim_evidence_graph",
        closure_json_path: "claim_closure_report",
        closure_md_path: "human_readable_claim_closure_report",
        mes_scan_path: "mes_successor_blocker_scan",
        release_receipt_path: "blocked_release_receipt",
        parent_receipt_path: "mechanics_parent_receipt",
        test_execution_path: "pytest_execution_receipt",
    }
    artifacts = [
        {
            "path": path.as_posix(),
            "sha256": _sha256_bytes(
                outputs[path] if path in outputs else _resolve(root, path).read_bytes()
            ),
            "artifact_role": artifact_roles[path],
        }
        for path in sorted(artifact_roles, key=lambda value: value.as_posix())
    ]
    manifest = {
        "schema": "htt.pr122.artifact_manifest.v1",
        "owner": closure["owner"],
        "implementation_scope": closure["implementation_scope"],
        "claim_tier": closure["claim_tier"],
        "transfer_source": closure["transfer_source"],
        "config_hash": closure["config_hash"],
        "input_hashes": closure["input_hashes"],
        "sky_support_status": closure["sky_support_status"],
        "null_mock_status": closure["null_mock_status"],
        "caveats": [
            *closure["caveats"],
            "This manifest content-addresses every PR-122 generated output; it does not authorize scientific claim release.",
            "The literal-only release pin fields remain an explicit commit-reviewed fixed-point trust root.",
        ],
        "generating_command": closure["generating_command"],
        "git_commit_or_worktree_state": closure["git_commit_or_worktree_state"],
        "artifacts": artifacts,
    }
    outputs[artifact_manifest_path] = _render_json(manifest)
    return outputs


def _write(root: Path, outputs: Mapping[Path, bytes]) -> None:
    for relative, content in outputs.items():
        path = _resolve(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _check(root: Path, outputs: Mapping[Path, bytes]) -> None:
    for relative, expected in outputs.items():
        path = _resolve(root, relative)
        if not path.is_file():
            raise ValueError(f"missing PR-122 generated artifact: {relative}")
        if path.read_bytes() != expected:
            raise ValueError(f"stale PR-122 generated artifact: {relative}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--test-execution", type=Path, default=DEFAULT_TEST_EXECUTION)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write-test-execution", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    _require_source_only_launcher()
    args = parse_args(argv)
    root = args.repo_root.resolve()
    try:
        if args.write_test_execution:
            destination = _resolve(root, args.test_execution)
            destination.parent.mkdir(parents=True, exist_ok=True)
            payload = _run_authoritative_pytest(root, destination)
            counts = payload.get("counts")
            if not isinstance(counts, Mapping):
                raise EvidenceGraphError(
                    "authoritative pytest receipt lacks exact counts"
                )
            print(
                "wrote authoritative PR-122 pytest receipt "
                f"collected={counts.get('collected')} "
                f"executed={counts.get('executed')} "
                f"passed={counts.get('passed')}"
            )
            return 0
        outputs = build_outputs(
            repo_root=root,
            test_execution_path=args.test_execution,
        )
        if args.check:
            _check(root, outputs)
        elif not args.dry_run:
            _write(root, outputs)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        yaml.YAMLError,
        json.JSONDecodeError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    graph_record = json.loads(outputs[DEFAULT_GRAPH].decode("utf-8"))
    closure_record = json.loads(outputs[DEFAULT_CLOSURE_JSON].decode("utf-8"))
    prefix = "up-to-date" if args.check else ("dry-run" if args.dry_run else "wrote")
    print(
        f"{prefix} PR-122 graph_ref={graph_record['graph_ref']} "
        f"receipt_id={closure_record['release_receipt_id']} "
        f"claim_release_allowed={closure_record['claim_release_allowed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
