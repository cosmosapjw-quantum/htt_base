"""Generated DAG status snapshot and claim-ledger sidecars.

The canonical row schemas live in :mod:`common.contracts`.  This module owns
the PR-012 generator that turns the Codex DAG backlog/status YAML into a
machine-readable status snapshot, a generated claim ledger, and a Markdown
status matrix rendered from the same source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from common.claim_ledger import claim_entry_to_dict
from common.harness_profiles_v4 import (
    HarnessProfileError,
    VerifiedSmokeReceipt,
    load_profile_manifest,
    validate_smoke_receipt_registry,
)
from common.contracts import (
    AllowedUse,
    ArtifactMode,
    ClaimLedgerEntry,
    ClaimTier,
    ImplementationScope,
    Owner,
    StatusSnapshotEntry,
    normalize_owner,
)

DEFAULT_BACKLOG_PATH = Path("docs/codex_handoff/pr_backlog.yaml")
DEFAULT_STATUS_PATH = Path("docs/codex_handoff/pr_status.yaml")
DEFAULT_GATE_OUTPUTS_NAME = "artifact_gate_outputs.yaml"
DEFAULT_PROFILE_MANIFEST_PATH = Path(
    "docs/research_program/post_pr275/harness_profiles_v4.yaml"
)
DEFAULT_SMOKE_RECEIPT_REGISTRY_PATH = Path(
    "docs/research_program/post_pr275/test_execution_receipts_v4.yaml"
)

_OWNER_SCOPE = {
    Owner.COMMON: ImplementationScope.COMMON,
    Owner.HTT: ImplementationScope.HTT,
    Owner.MIO: ImplementationScope.MIO,
    Owner.BASS: ImplementationScope.BASS_PY,
    Owner.OBSSTAT: ImplementationScope.OBSSTAT,
    Owner.TSC_LEGACY: ImplementationScope.TSC_LEGACY,
}

_TERMINAL_EXECUTION_RESOLUTIONS = frozenset(
    {
        "COMPLETED_SUCCESS",
        "COMPLETED_FAILED_WITH_RECEIPT",
        "BLOCKED_WITH_RECEIPT",
        "ABANDONED_WITH_RECEIPT",
    }
)


@dataclass(frozen=True)
class StatusBundle:
    """In-memory generated sidecar bundle."""

    metadata: dict[str, object]
    status_rows: list[dict[str, object]]
    claim_rows: list[dict[str, object]]

    def status_snapshot_payload(self) -> dict[str, object]:
        """Return the canonical JSON payload for ``status_snapshot.json``."""

        return {
            "metadata": self.metadata,
            "rows": self.status_rows,
        }

    def claim_ledger_payload(self) -> dict[str, object]:
        """Return the canonical JSON payload for ``claim_ledger.json``."""

        return {
            "metadata": {
                **self.metadata,
                "source": "common.status_snapshot.claim_ledger",
                "semantic_source": "common.contracts.ClaimLedgerEntry",
            },
            "rows": self.claim_rows,
        }


@dataclass(frozen=True)
class StatusArtifactPaths:
    """Paths written by :func:`write_status_artifacts`."""

    status_snapshot_path: Path
    claim_ledger_path: Path
    status_matrix_path: Path


def snapshot_entry_to_dict(entry: StatusSnapshotEntry) -> dict[str, object]:
    """Return a JSON-ready dictionary for one status row."""

    return _json_ready(asdict(entry))


def build_status_bundle(
    *,
    backlog_path: str | Path = DEFAULT_BACKLOG_PATH,
    status_path: str | Path = DEFAULT_STATUS_PATH,
    gate_outputs_path: str | Path | None = None,
    execution_receipts_path: str | Path | None = None,
    source_commit: str | None = None,
    generated_on: str | None = None,
    generating_command: str | None = None,
) -> StatusBundle:
    """Build generated status and claim rows from DAG/status YAML files."""

    resolved_backlog = Path(backlog_path)
    resolved_status = Path(status_path)
    resolved_gate_outputs = _resolve_gate_outputs_path(
        resolved_backlog,
        gate_outputs_path=gate_outputs_path,
    )
    resolved_execution_receipts = _resolve_execution_receipts_path(
        resolved_backlog,
        execution_receipts_path=execution_receipts_path,
    )
    backlog = _load_yaml_mapping(resolved_backlog)
    status = _load_yaml_mapping(resolved_status)
    gate_outputs = _load_gate_outputs(resolved_gate_outputs)
    prs = _ordered_prs(backlog)
    completed = _status_set(status.get("completed"))
    blocked = _status_set(status.get("blocked"))
    skipped = _status_set(status.get("skipped"))
    pending = _status_set(status.get("pending"))
    dormant_external = _status_set(status.get("dormant_external"))
    in_progress = _status_set(status.get("in_progress"))
    background_in_progress = _status_set(status.get("background_in_progress"))
    execution_resolutions = validate_status_contract(cards=prs, status=status)
    verified_smoke_receipts = _load_verified_smoke_receipts(
        resolved_execution_receipts,
        backlog_path=resolved_backlog,
    )
    unknown_receipt_prs = set(verified_smoke_receipts) - {
        _required_str(pr, "id") for pr in prs
    }
    if unknown_receipt_prs:
        raise ValueError(
            f"smoke receipt registry contains unknown PR ids: {sorted(unknown_receipt_prs)}"
        )
    receipt_eligible_terminal_prs = completed | blocked
    nonterminal_receipt_prs = (
        set(verified_smoke_receipts) - receipt_eligible_terminal_prs
    )
    if nonterminal_receipt_prs:
        raise ValueError(
            "smoke receipt registry can bind only completed or receipt-bearing "
            f"blocked PRs: {sorted(nonterminal_receipt_prs)}"
        )
    source = source_commit or _current_source_commit()
    command = generating_command or (
        "python -m common.status_snapshot --write docs/generated/status_snapshot.json"
    )

    status_rows: list[dict[str, object]] = []
    claim_rows: list[dict[str, object]] = []
    for pr in prs:
        pr_id = _required_str(pr, "id")
        owner = _owner_from_card(str(pr.get("owner", Owner.COMMON.value)))
        scope = _OWNER_SCOPE[owner]
        state = _state_for_pr(
            pr_id=pr_id,
            completed=completed,
            blocked=blocked,
            skipped=skipped,
            pending=pending,
            dormant_external=dormant_external,
            in_progress=in_progress,
            background_in_progress=background_in_progress,
        )
        promotion = _promotion_profile(
            pr_id=pr_id,
            state=state,
            gate_outputs=gate_outputs,
        )
        claim_tier = promotion["claim_tier"]
        implemented = state == "completed"
        receipt = verified_smoke_receipts.get(pr_id)
        smoke_tested = receipt is not None
        artifact_readiness = str(promotion["artifact_readiness"])
        promotion_blockers = tuple(promotion["promotion_blockers"])
        report_generation_gates = dict(promotion["report_generation_gates"])
        if smoke_tested:
            artifact_readiness = "smoke_tested"
            promotion_blockers = tuple(
                blocker
                for blocker in promotion_blockers
                if blocker != "exact_test_execution_receipt_not_bound"
            )
            report_generation_gates["exact_test_execution_receipt_bound"] = "pass"
        elif artifact_readiness == "smoke_tested":
            artifact_readiness = "generated" if implemented else "missing"
            promotion_blockers = tuple(
                dict.fromkeys(
                    (*promotion_blockers, "exact_test_execution_receipt_not_bound")
                )
            )
        status_row = snapshot_entry_to_dict(
            StatusSnapshotEntry(
                artifact_id=f"codex_dag.{pr_id}",
                owner=owner,
                implementation_scope=scope,
                claim_tier=claim_tier,
                implemented=implemented,
                smoke_tested=smoke_tested,
                production_validated=bool(promotion["production_validated"]),
                manuscript_used=bool(promotion["manuscript_used"]),
                source_commit=source,
                artifact_readiness=artifact_readiness,
                artifact_mode=ArtifactMode(str(promotion["artifact_mode"])),
                allowed_use=AllowedUse(str(promotion["allowed_use"])),
                caption_policy=tuple(promotion["caption_policy"]),
                promotion_blockers=promotion_blockers,
                report_generation_gates=report_generation_gates,
                science_promotion_gates=dict(promotion["science_promotion_gates"]),
                publication_gates=dict(promotion["publication_gates"]),
                smoke_evidence_ref=(None if receipt is None else receipt.evidence_ref),
                smoke_execution_ref=(None if receipt is None else receipt.execution_ref),
                smoke_profile_id=(None if receipt is None else receipt.profile_id),
                smoke_candidate_commit=(
                    None if receipt is None else receipt.candidate_commit
                ),
                smoke_candidate_tree=(None if receipt is None else receipt.candidate_tree),
            )
        )
        # Orchestration state is orthogonal to implementation/readiness/claim
        # axes. Keep it explicit in the generated row instead of trying to
        # reconstruct it from ``implemented`` or ``claim_tier``.
        status_row["orchestration_state"] = state
        status_rows.append(status_row)
        claim_rows.append(
            claim_entry_to_dict(
                ClaimLedgerEntry(
                    artifact_id=f"codex_dag.{pr_id}",
                    owner=owner,
                    claim_tier=claim_tier,
                    allowed_claims=(_allowed_claim(pr_id, state),),
                    forbidden_claims=(
                        (
                            "DAG status is not scientific readiness, solver validation, "
                            "transfer validation, posterior evidence, MIO certification, "
                            "morphology compatibility, or family-ID evidence."
                        ),
                    ),
                    evidence_refs=(
                        _display_path(resolved_backlog),
                        _display_path(resolved_status),
                    ),
                    source_commit=source,
                    notes=_claim_ledger_notes(pr=pr, state=state),
                )
            )
        )

    input_paths = [resolved_backlog, resolved_status]
    if resolved_gate_outputs is not None:
        input_paths.append(resolved_gate_outputs)
    if resolved_execution_receipts is not None:
        input_paths.extend(
            [resolved_execution_receipts, _profile_manifest_for(resolved_backlog)]
        )
    input_hashes = _input_hashes(input_paths)
    state_counts = Counter(_state_from_row(row) for row in status_rows)
    config_hash = _config_hash(
        {
            "backlog": _display_path(resolved_backlog),
            "status": _display_path(resolved_status),
            "gate_outputs": (
                _display_path(resolved_gate_outputs)
                if resolved_gate_outputs is not None
                else "not_present"
            ),
            "input_hashes": input_hashes,
            "total_prs": len(prs),
            "completed_prs": state_counts["completed"],
            "blocked_prs": state_counts["blocked"],
            "skipped_prs": state_counts["skipped"],
            "in_progress_prs": state_counts["in_progress"],
            "background_in_progress_prs": state_counts["background_in_progress"],
            "pending_prs": state_counts["pending"],
            "dormant_external_prs": state_counts["dormant_external"],
            "execution_resolution_prs": sorted(execution_resolutions),
            "smoke_receipt_prs": sorted(verified_smoke_receipts),
        }
    )
    metadata: dict[str, object] = {
        "source": "common.status_snapshot",
        "semantic_source": "common.contracts.StatusSnapshotEntry",
        "generated_on": generated_on
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "backlog_path": _display_path(resolved_backlog),
        "status_path": _display_path(resolved_status),
        "total_prs": len(prs),
        "completed_prs": state_counts["completed"],
        "blocked_prs": state_counts["blocked"],
        "skipped_prs": state_counts["skipped"],
        "in_progress_prs": state_counts["in_progress"],
        "background_in_progress_prs": state_counts["background_in_progress"],
        "pending_prs": state_counts["pending"],
        "dormant_external_prs": state_counts["dormant_external"],
        "execution_resolution_count": len(execution_resolutions),
        "execution_resolution_prs": sorted(execution_resolutions),
        "smoke_receipt_count": len(verified_smoke_receipts),
        "smoke_receipt_prs": sorted(verified_smoke_receipts),
        "owner": Owner.COMMON.value,
        "implementation_scope": ImplementationScope.COMMON.value,
        "claim_tier": ClaimTier.DIAGNOSTIC_ONLY.value,
        "transfer_source": "none",
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": [
            "DAG completion is project bookkeeping only and is not scientific readiness.",
            "Rows never promote external-transfer outputs to native solver validation.",
            "DAG completion, artifact readiness, allowed use, and production validation are separate axes.",
            "production_validated remains false without an exact factory-issued ClaimCapabilityDecision.",
            "Execution resolutions are process receipts only and never promote scientific status or claim tier.",
            "Verified smoke receipts set only generic process readiness; they do not grant a ClaimCapability.",
        ],
        "generating_command": command,
        "source_commit": source,
        "worktree_state": _worktree_state(),
    }
    return StatusBundle(
        metadata=metadata,
        status_rows=status_rows,
        claim_rows=claim_rows,
    )


def render_status_matrix(bundle: StatusBundle) -> str:
    """Render a human-readable matrix from a generated bundle."""

    metadata = bundle.metadata
    by_owner = Counter(str(row["owner"]) for row in bundle.status_rows)
    by_state = Counter(_state_from_row(row) for row in bundle.status_rows)
    by_claim_tier = Counter(str(row["claim_tier"]) for row in bundle.status_rows)
    by_readiness = Counter(str(row["artifact_readiness"]) for row in bundle.status_rows)
    by_allowed_use = Counter(str(row["allowed_use"]) for row in bundle.status_rows)
    by_artifact_mode = Counter(str(row["artifact_mode"]) for row in bundle.status_rows)
    owner_lines = "\n".join(
        f"| `{owner}` | {count} |" for owner, count in sorted(by_owner.items())
    )
    state_lines = "\n".join(
        f"| `{state}` | {count} |" for state, count in sorted(by_state.items())
    )
    input_hashes = (
        "<br>".join(f"`{item}`" for item in metadata.get("input_hashes", []))
        or "`none`"
    )
    caveats = "<br>".join(str(item) for item in metadata.get("caveats", [])) or "none"
    return (
        "\n".join(
            (
                "<!-- Generated by common.status_snapshot; do not edit counts by hand. -->",
                "# Generated Status Matrix",
                "",
                "Semantic source: `htt/src/common/contracts.py::StatusSnapshotEntry`",
                "",
                "Manual status counts are prohibited; use `docs/generated/status_snapshot.json` as the canonical public status source.",
                "",
                "| Metric | Value |",
                "| --- | ---: |",
                f"| Total PRs | {metadata['total_prs']} |",
                f"| Completed PRs | {metadata['completed_prs']} |",
                f"| Blocked PRs | {metadata['blocked_prs']} |",
                f"| Skipped PRs | {metadata.get('skipped_prs', 0)} |",
                f"| In progress | {metadata['in_progress_prs']} |",
                f"| Background in progress | {metadata.get('background_in_progress_prs', 0)} |",
                f"| Pending PRs | {metadata['pending_prs']} |",
                f"| Dormant external PRs | {metadata.get('dormant_external_prs', 0)} |",
                "",
                "| Metadata | Value |",
                "| --- | --- |",
                f"| Owner | `{metadata['owner']}` |",
                f"| Implementation scope | `{metadata['implementation_scope']}` |",
                f"| Claim tier | `{metadata['claim_tier']}` |",
                f"| Transfer source | `{metadata['transfer_source']}` |",
                f"| Config hash | `{metadata['config_hash']}` |",
                f"| Input hashes | {input_hashes} |",
                f"| Sky support status | `{metadata['sky_support_status']}` |",
                f"| Null/mock status | `{metadata['null_mock_status']}` |",
                f"| Caveats | {caveats} |",
                f"| Generating command | `{metadata['generating_command']}` |",
                f"| Source commit | `{metadata['source_commit']}` |",
                f"| Worktree state | `{metadata['worktree_state']}` |",
                "",
                "| Owner | Rows |",
                "| --- | ---: |",
                owner_lines,
                "",
                "| State | Rows |",
                "| --- | ---: |",
                state_lines,
                "",
                "| Claim Tier | Rows |",
                "| --- | ---: |",
                _counter_table_lines(by_claim_tier),
                "",
                "| Artifact Readiness | Rows |",
                "| --- | ---: |",
                _counter_table_lines(by_readiness),
                "",
                "| Allowed Use | Rows |",
                "| --- | ---: |",
                _counter_table_lines(by_allowed_use),
                "",
                "| Artifact Mode | Rows |",
                "| --- | ---: |",
                _counter_table_lines(by_artifact_mode),
                "",
                "This matrix is a diagnostic-only DAG rendering. It does not certify solver validation, posterior evidence, native transfer validation, or family-ID evidence.",
            )
        )
        + "\n"
    )


def _counter_table_lines(counter: Counter[str]) -> str:
    return "\n".join(f"| `{key}` | {value} |" for key, value in sorted(counter.items()))


def _claim_ledger_notes(*, pr: Mapping[str, object], state: str) -> tuple[str, ...]:
    """Return generated claim-ledger notes for one DAG row.

    Most DAG rows are project bookkeeping artifacts, so their support notes use
    generic non-statistical placeholders. Some PR cards define a concrete
    generated scientific surface; for those, preserve the card-level support
    semantics so regenerated ledgers do not overwrite directional/statistical
    status with generic placeholders.
    """

    pr_id = str(pr.get("id", "")).strip()
    title = str(pr.get("title", "")).strip()
    deps = ",".join(str(dep) for dep in pr.get("depends", []) or []) or "none"
    base = (
        f"title={title}",
        f"state={state}",
        f"depends={deps}",
        "transfer_source=none",
    )
    if _is_directional_coherence_certificate_pr(pr_id=pr_id, pr=pr):
        return base + (
            "covariance_status=certificate_readiness_recorded",
            "null_mock_status=certificate_readiness_recorded",
            "sky_support_status=directional_certificate_readiness_recorded",
        )
    if _is_redshift_binned_coherence_certificate_pr(pr_id=pr_id, pr=pr):
        return base + (
            "covariance_status=redshift_bin_certificate_readiness_recorded",
            "null_mock_status=redshift_bin_certificate_readiness_recorded",
            "sky_support_status=redshift_bin_certificate_readiness_recorded",
            "selection_status=redshift_bin_selection_metadata_required",
            "g_f_bridge_status=diagnostic_bridge_metadata_recorded",
        )
    if _is_flrw_tension_null_predictive_gate_pr(pr_id=pr_id, pr=pr):
        return base + (
            "null_mock_status=flrw_null_predictive_gate_recorded",
            "covariance_status=flrw_null_predictive_gate_recorded",
            "sky_support_status=flrw_null_predictive_gate_recorded",
            "look_elsewhere_status=flrw_null_predictive_gate_recorded",
            "tail_probability_status=descriptive_until_null_gate_passes",
        )
    if _is_survey_systematic_null_pr(pr_id=pr_id, pr=pr):
        return base + (
            "null_mock_status=survey_systematic_null_fpr_recorded",
            "covariance_status=survey_systematic_null_fpr_recorded",
            "sky_support_status=survey_systematic_null_fpr_recorded",
            "selection_status=selection_metadata_hash_required",
            "survey_axis_status=survey_axis_hash_required_when_present",
            "claim_scope=dag_row_not_artifact_payload",
        )
    return base + (
        "null_mock_status=not_statistical",
        "sky_support_status=not_directional",
    )


def _is_directional_coherence_certificate_pr(
    *,
    pr_id: str,
    pr: Mapping[str, object],
) -> bool:
    """Return whether a PR card is the directional-certificate status surface."""

    if pr_id != "PR-100":
        return False
    owner = str(pr.get("owner", "")).strip().upper()
    if owner != Owner.MIO.value:
        return False
    files = {str(path) for path in pr.get("files", ()) or ()}
    if "htt/mio/coherence/directional.py" not in files:
        return False
    dod_items = " ".join(str(item) for item in pr.get("dod", ()) or ())
    return "covariance/sky support/null status" in dod_items


def _is_redshift_binned_coherence_certificate_pr(
    *,
    pr_id: str,
    pr: Mapping[str, object],
) -> bool:
    """Return whether a PR card is the redshift-binned certificate bridge."""

    if pr_id != "PR-101":
        return False
    owner = str(pr.get("owner", "")).strip().upper()
    if owner != Owner.MIO.value:
        return False
    files = {str(path) for path in pr.get("files", ()) or ()}
    if "htt/mio/coherence/redshift_binned.py" not in files:
        return False
    if "tests/mio/test_redshift_binned_coherence.py" not in files:
        return False
    dod_items = " ".join(str(item) for item in pr.get("dod", ()) or ())
    return (
        "Depth-bin covariance and selection metadata required" in dod_items
        and "Descriptive fallback is explicit" in dod_items
    )


def _is_flrw_tension_null_predictive_gate_pr(
    *,
    pr_id: str,
    pr: Mapping[str, object],
) -> bool:
    """Return whether a PR card is the FLRW null-predictive MIO gate."""

    if pr_id != "PR-102":
        return False
    owner = str(pr.get("owner", "")).strip().upper()
    if owner != Owner.MIO.value:
        return False
    files = {str(path) for path in pr.get("files", ()) or ()}
    if "htt/mio/tension/flrw_tension.py" not in files:
        return False
    if "tests/mio/test_flrw_tension_gate.py" not in files:
        return False
    dod_items = " ".join(str(item) for item in pr.get("dod", ()) or ())
    return (
        "PPP/tension metrics require calibrated null predictive distribution"
        in dod_items
        and "No PPP claim without null mocks" in dod_items
    )


def _is_survey_systematic_null_pr(
    *,
    pr_id: str,
    pr: Mapping[str, object],
) -> bool:
    """Return whether a PR card is the HTT survey/systematic null gate."""

    if pr_id != "PR-062":
        return False
    owner = str(pr.get("owner", "")).strip().upper()
    if owner != Owner.HTT.value:
        return False
    files = {str(path) for path in pr.get("files", ()) or ()}
    if "htt/htt/htt/nulls/selection_response_depth.py" not in files:
        return False
    if "htt/htt/htt/nulls/survey_axis_coherence.py" not in files:
        return False
    if "tests/htt/test_survey_nulls.py" not in files:
        return False
    dod_items = " ".join(str(item) for item in pr.get("dod", ()) or ())
    return (
        "Survey/systematic nulls can mimic direction/depth signals in calibration"
        in dod_items
        and "Selection metadata is carried through" in dod_items
    )


def validate_status_matrix_matches_snapshot(
    markdown: str,
    snapshot_payload: Mapping[str, object],
) -> None:
    """Raise when generated Markdown count rows drift from the JSON snapshot."""

    metadata = snapshot_payload.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("status snapshot payload is missing metadata")
    matrix_counts = _extract_matrix_counts(markdown)
    expected = {
        "Total PRs": int(metadata["total_prs"]),
        "Completed PRs": int(metadata["completed_prs"]),
        "Blocked PRs": int(metadata["blocked_prs"]),
        "In progress": int(metadata["in_progress_prs"]),
        "Pending PRs": int(metadata["pending_prs"]),
    }
    if "background_in_progress_prs" in metadata:
        expected["Background in progress"] = int(
            metadata["background_in_progress_prs"]
        )
    if "skipped_prs" in metadata:
        expected["Skipped PRs"] = int(metadata["skipped_prs"])
    if "dormant_external_prs" in metadata:
        expected["Dormant external PRs"] = int(metadata["dormant_external_prs"])
    mismatches = [
        f"{metric}: markdown={matrix_counts.get(metric)!r} snapshot={value!r}"
        for metric, value in expected.items()
        if matrix_counts.get(metric) != value
    ]
    if mismatches:
        raise ValueError(
            "generated status matrix count mismatch: " + "; ".join(mismatches)
        )


def _resolve_gate_outputs_path(
    backlog_path: Path,
    *,
    gate_outputs_path: str | Path | None,
) -> Path | None:
    if gate_outputs_path is not None:
        path = Path(gate_outputs_path)
        return path if path.exists() else None
    candidate = backlog_path.with_name(DEFAULT_GATE_OUTPUTS_NAME)
    return candidate if candidate.exists() else None


def _repo_root_for_backlog(backlog_path: Path) -> Path:
    resolved = backlog_path.resolve()
    if resolved.name != "pr_backlog.yaml" or resolved.parent.name != "codex_handoff":
        raise ValueError(
            "receipt-backed status generation requires docs/codex_handoff/pr_backlog.yaml"
        )
    return resolved.parents[2]


def _profile_manifest_for(backlog_path: Path) -> Path:
    return _repo_root_for_backlog(backlog_path) / DEFAULT_PROFILE_MANIFEST_PATH


def _resolve_execution_receipts_path(
    backlog_path: Path,
    *,
    execution_receipts_path: str | Path | None,
) -> Path | None:
    try:
        canonical = (
            _repo_root_for_backlog(backlog_path)
            / DEFAULT_SMOKE_RECEIPT_REGISTRY_PATH
        )
    except ValueError:
        if execution_receipts_path is not None:
            raise ValueError(
                "explicit execution receipts require the canonical backlog path"
            )
        return None
    if execution_receipts_path is not None:
        path = Path(execution_receipts_path)
        if not path.exists():
            raise FileNotFoundError(path)
        if path.resolve() != canonical.resolve():
            raise ValueError("parallel execution receipt registries are forbidden")
        return path
    return canonical if canonical.exists() else None


def _load_verified_smoke_receipts(
    path: Path | None,
    *,
    backlog_path: Path,
) -> dict[str, VerifiedSmokeReceipt]:
    if path is None:
        return {}
    repo_root = _repo_root_for_backlog(backlog_path)
    manifest = load_profile_manifest(
        _profile_manifest_for(backlog_path), repo_root=repo_root
    )
    try:
        return validate_smoke_receipt_registry(
            path,
            manifest=manifest,
            repo_root=repo_root,
        )
    except HarnessProfileError as exc:
        raise ValueError(f"invalid smoke receipt registry: {exc}") from exc


def _load_gate_outputs(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    payload = _load_yaml_mapping(path)
    schema = payload.get("schema_version")
    if schema != "common.artifact_gate_outputs.v2":
        raise ValueError(
            "artifact gate annotations require common.artifact_gate_outputs.v2"
        )
    _reject_caller_capability_fields(payload)
    return payload


_CALLER_CAPABILITY_FIELDS = frozenset(
    {
        "claimtier",
        "artifactreadiness",
        "artifactmode",
        "alloweduse",
        "smoketested",
        "dataadmitted",
        "productionvalidated",
        "manuscriptused",
        "granted",
        "nativevalidated",
        "nativesolvervalidation",
        "formal4axispass",
        "cas4axispass",
        "theoremprovedexact",
        "theoremprovedconditional",
        "methodcalibrated",
        "observeddescriptive",
        "observedinferential",
        "sourceseparationcandidate",
        "morphologycompatibility",
        "familyidentification",
        "publicrelease",
    }
)
_CALLER_REPORT_GENERATION_GATES = frozenset({"dag_status_row_generated"})


def _reject_caller_capability_fields(value: object, *, path: str = "gate_outputs") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} keys must be strings")
            normalized = "".join(character for character in key.lower() if character.isalnum())
            if normalized in _CALLER_CAPABILITY_FIELDS:
                raise ValueError(
                    f"caller-supplied capability field is forbidden: {path}.{key}"
                )
            _reject_caller_capability_fields(nested, path=f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_caller_capability_fields(nested, path=f"{path}[{index}]")


def _promotion_profile(
    *,
    pr_id: str,
    state: str,
    gate_outputs: Mapping[str, object],
) -> dict[str, object]:
    defaults_by_state = {
        "completed": {
            "claim_tier": ClaimTier.DIAGNOSTIC_ONLY.value,
            "artifact_readiness": "generated",
            "artifact_mode": ArtifactMode.GOVERNANCE_DIAGNOSTIC.value,
            "allowed_use": AllowedUse.INTERNAL_ONLY.value,
            "production_validated": False,
            "manuscript_used": False,
            "caption_policy": ("must_state_dag_row_not_science_readiness",),
            "promotion_blockers": ("claim_capability_decision_absent",),
            "report_generation_gates": {"dag_status_row_generated": "pass"},
            "science_promotion_gates": {"claim_capability_decision": "fail"},
            "publication_gates": {"claim_capability_decision": "fail"},
        },
        "blocked": {
            "claim_tier": ClaimTier.BLOCKED.value,
            "artifact_readiness": "blocked",
            "artifact_mode": ArtifactMode.GOVERNANCE_DIAGNOSTIC.value,
            "allowed_use": AllowedUse.INTERNAL_ONLY.value,
            "production_validated": False,
            "manuscript_used": False,
            "caption_policy": ("must_state_blocker",),
            "promotion_blockers": (
                "dag_status_blocked",
                "claim_capability_decision_absent",
            ),
            "report_generation_gates": {"dag_status_row_generated": "pass"},
            "science_promotion_gates": {"blocked": "fail"},
            "publication_gates": {"blocked": "fail"},
        },
        "not_completed": {
            "claim_tier": ClaimTier.DIAGNOSTIC_ONLY.value,
            "artifact_readiness": "missing",
            "artifact_mode": ArtifactMode.GOVERNANCE_DIAGNOSTIC.value,
            "allowed_use": AllowedUse.INTERNAL_ONLY.value,
            "production_validated": False,
            "manuscript_used": False,
            "caption_policy": ("must_state_not_completed",),
            "promotion_blockers": (
                "dag_status_not_completed",
                "claim_capability_decision_absent",
            ),
            "report_generation_gates": {"dag_status_row_generated": "pass"},
            "science_promotion_gates": {"implementation_complete": "fail"},
            "publication_gates": {"implementation_complete": "fail"},
        },
    }
    base_key = (
        "completed"
        if state == "completed"
        else "blocked" if state == "blocked" else "not_completed"
    )
    profile = dict(defaults_by_state[base_key])
    state_annotations = gate_outputs.get("state_annotations")
    if isinstance(state_annotations, Mapping):
        maybe_state = state_annotations.get(base_key)
        if isinstance(maybe_state, Mapping):
            profile = _apply_gate_annotation(profile, maybe_state)
    annotations = gate_outputs.get("pr_annotations")
    if isinstance(annotations, Mapping):
        maybe_override = annotations.get(pr_id)
        if isinstance(maybe_override, Mapping):
            profile = _apply_gate_annotation(profile, maybe_override)
    return _normalize_promotion_profile(profile)


def _annotation_subset(raw: Mapping[str, object]) -> dict[str, object]:
    allowed = {
        "caption_policy",
        "promotion_blockers",
        "report_generation_gates",
    }
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(
            f"artifact gate annotation has unsupported fields: {sorted(unknown)}"
        )
    return {key: value for key, value in raw.items() if key in allowed}


def _apply_gate_annotation(
    profile: Mapping[str, object], raw: Mapping[str, object]
) -> dict[str, object]:
    annotation = _annotation_subset(raw)
    merged = dict(profile)
    for field in ("caption_policy", "promotion_blockers"):
        if field in annotation:
            merged[field] = tuple(
                dict.fromkeys(
                    (*_string_tuple(merged.get(field)), *_string_tuple(annotation[field]))
                )
            )
    if "report_generation_gates" in annotation:
        requested_gates = _string_map(annotation["report_generation_gates"])
        unknown_gates = set(requested_gates) - _CALLER_REPORT_GENERATION_GATES
        if unknown_gates:
            raise ValueError(
                "caller-supplied report-generation gate is forbidden: "
                f"{sorted(unknown_gates)}"
            )
        gates = _string_map(merged.get("report_generation_gates"))
        gates.update(requested_gates)
        merged["report_generation_gates"] = gates
    return merged


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value)
    raise ValueError("promotion profile list fields must be strings or lists")


def _string_map(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("promotion gate fields must be mappings")
    return {str(key): str(item) for key, item in value.items()}


def _normalize_promotion_profile(profile: Mapping[str, object]) -> dict[str, object]:
    return {
        "claim_tier": ClaimTier(str(profile["claim_tier"])).value,
        "artifact_readiness": str(profile["artifact_readiness"]),
        "artifact_mode": ArtifactMode(str(profile["artifact_mode"])).value,
        "allowed_use": AllowedUse(str(profile["allowed_use"])).value,
        "production_validated": bool(profile["production_validated"]),
        "manuscript_used": bool(profile["manuscript_used"]),
        "caption_policy": _string_tuple(profile.get("caption_policy")),
        "promotion_blockers": _string_tuple(profile.get("promotion_blockers")),
        "report_generation_gates": _string_map(profile.get("report_generation_gates")),
        "science_promotion_gates": _string_map(profile.get("science_promotion_gates")),
        "publication_gates": _string_map(profile.get("publication_gates")),
    }


def write_status_artifacts(
    output_path: str | Path,
    *,
    backlog_path: str | Path = DEFAULT_BACKLOG_PATH,
    status_path: str | Path = DEFAULT_STATUS_PATH,
    gate_outputs_path: str | Path | None = None,
    execution_receipts_path: str | Path | None = None,
    source_commit: str | None = None,
    generating_command: str | None = None,
) -> StatusArtifactPaths:
    """Write status snapshot, companion claim ledger, and status matrix."""

    status_snapshot_path = Path(output_path)
    claim_ledger_path = status_snapshot_path.with_name("claim_ledger.json")
    status_matrix_path = status_snapshot_path.with_name("status_matrix.md")
    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        gate_outputs_path=gate_outputs_path,
        execution_receipts_path=execution_receipts_path,
        source_commit=source_commit,
        generating_command=generating_command,
    )
    snapshot_payload = bundle.status_snapshot_payload()
    claim_payload = bundle.claim_ledger_payload()
    matrix = render_status_matrix(bundle)
    validate_status_matrix_matches_snapshot(matrix, snapshot_payload)

    status_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(status_snapshot_path, snapshot_payload)
    _write_json(claim_ledger_path, claim_payload)
    status_matrix_path.write_text(matrix, encoding="utf-8")
    return StatusArtifactPaths(
        status_snapshot_path=status_snapshot_path,
        claim_ledger_path=claim_ledger_path,
        status_matrix_path=status_matrix_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for ``python -m common.status_snapshot``."""

    parser = argparse.ArgumentParser(
        description="Generate DAG status snapshot and claim-ledger sidecars."
    )
    parser.add_argument(
        "--backlog",
        type=Path,
        default=DEFAULT_BACKLOG_PATH,
        help="Path to pr_backlog.yaml.",
    )
    parser.add_argument(
        "--status",
        type=Path,
        default=DEFAULT_STATUS_PATH,
        help="Path to pr_status.yaml.",
    )
    parser.add_argument(
        "--source-commit",
        default=None,
        help="Override source commit recorded in generated rows.",
    )
    parser.add_argument(
        "--gate-outputs",
        type=Path,
        default=None,
        help="Optional artifact promotion/readiness gate-output YAML.",
    )
    parser.add_argument(
        "--execution-receipts",
        type=Path,
        default=None,
        help="Optional PR-280 exact smoke receipt binding registry.",
    )
    parser.add_argument(
        "--write",
        type=Path,
        required=True,
        help="Path for status_snapshot.json; companion files are written nearby.",
    )
    args = parser.parse_args(argv)
    command = "python -m common.status_snapshot " + " ".join(sys.argv[1:])
    written = write_status_artifacts(
        args.write,
        backlog_path=args.backlog,
        status_path=args.status,
        gate_outputs_path=args.gate_outputs,
        execution_receipts_path=args.execution_receipts,
        source_commit=args.source_commit,
        generating_command=command,
    )
    print(f"wrote {written.status_snapshot_path}")
    print(f"wrote {written.claim_ledger_path}")
    print(f"wrote {written.status_matrix_path}")
    return 0


def _load_yaml_mapping(path: Path) -> Mapping[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a YAML mapping")
    return payload


def _ordered_prs(backlog: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_prs = backlog.get("prs")
    if not isinstance(raw_prs, list):
        raise ValueError("backlog must contain a prs list")
    by_id: dict[str, Mapping[str, object]] = {}
    for raw in raw_prs:
        if not isinstance(raw, Mapping):
            raise ValueError("every PR card must be a mapping")
        pr_id = _required_str(raw, "id")
        by_id[pr_id] = raw
    order = _topological_order(backlog)
    ordered = [by_id[pr_id] for pr_id in order if pr_id in by_id]
    remaining = sorted(set(by_id) - set(order))
    ordered.extend(by_id[pr_id] for pr_id in remaining)
    return ordered


def _topological_order(backlog: Mapping[str, object]) -> list[str]:
    policy = backlog.get("policy")
    if isinstance(policy, Mapping):
        raw_order = policy.get("topological_order")
        if isinstance(raw_order, list):
            return [str(pr_id) for pr_id in raw_order]
    raw_order = backlog.get("topological_order")
    if isinstance(raw_order, list):
        return [str(pr_id) for pr_id in raw_order]
    return []


def _owner_from_card(raw_owner: str) -> Owner:
    owner = raw_owner.strip()
    if owner == "BASS_PY":
        return Owner.BASS
    if owner == "MANUSCRIPT":
        return Owner.COMMON
    return normalize_owner(owner)


def _required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"PR card missing non-empty {key}")
    return value


def _status_set(value: object) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {str(item) for item in value if str(item)}
    raise ValueError("status fields must be null, a string, or a list")


def _execution_resolutions(value: object) -> Mapping[str, object]:
    """Return process-only execution receipts without interpreting them.

    Resolution content is deliberately excluded from promotion logic. The
    status snapshot records only which PRs have receipts so a process outcome
    cannot become scientific evidence through this generator.
    """

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("status execution_resolutions must be a mapping")
    if not all(isinstance(pr_id, str) and pr_id for pr_id in value):
        raise ValueError("status execution_resolutions keys must be PR ids")
    return value


def validate_status_contract(
    *,
    cards: Sequence[Mapping[str, object]],
    status: Mapping[str, object],
) -> Mapping[str, object]:
    """Validate the typed orchestration surface shared by writers/readers.

    This deliberately validates process receipts without interpreting them as
    scientific evidence.  Intake refresh and generated status consumers call
    the same function so a malformed state cannot be accepted on one path and
    rejected on another.
    """

    return _validate_status_partition(
        status=status,
        cards=cards,
        completed=_status_set(status.get("completed")),
        blocked=_status_set(status.get("blocked")),
        skipped=_status_set(status.get("skipped")),
        pending=_status_set(status.get("pending")),
        dormant_external=_status_set(status.get("dormant_external")),
        in_progress=_status_set(status.get("in_progress")),
        background_in_progress=_status_set(status.get("background_in_progress")),
    )


def _validate_status_partition(
    *,
    status: Mapping[str, object],
    cards: Sequence[Mapping[str, object]],
    completed: set[str],
    blocked: set[str],
    skipped: set[str],
    pending: set[str],
    dormant_external: set[str],
    in_progress: set[str],
    background_in_progress: set[str],
) -> Mapping[str, object]:
    """Reject ambiguous foreground/background orchestration state."""

    raw_foreground = status.get("in_progress")
    if raw_foreground is not None and not isinstance(raw_foreground, str):
        raise ValueError("status in_progress must be a scalar PR id or null")
    raw_background = status.get("background_in_progress")
    if raw_background is not None:
        if not isinstance(raw_background, list) or not all(
            isinstance(pr_id, str) and pr_id for pr_id in raw_background
        ):
            raise ValueError("status background_in_progress must be a PR-id list")
        if len(raw_background) != len(set(raw_background)):
            raise ValueError("status background_in_progress contains duplicate PR ids")

    states = {
        "completed": completed,
        "blocked": blocked,
        "skipped": skipped,
        "pending": pending,
        "dormant_external": dormant_external,
        "in_progress": in_progress,
        "background_in_progress": background_in_progress,
    }
    membership: dict[str, list[str]] = {}
    for state, pr_ids in states.items():
        for pr_id in pr_ids:
            membership.setdefault(pr_id, []).append(state)
    overlap = {
        pr_id: state_names
        for pr_id, state_names in membership.items()
        if len(state_names) > 1
    }
    if overlap:
        raise ValueError(f"status orchestration states overlap: {overlap}")

    card_map = {
        _required_str(card, "id"): card
        for card in cards
    }
    unknown = sorted(set(membership) - set(card_map))
    if unknown:
        raise ValueError(f"status contains unknown PR ids: {unknown}")
    strict_rescue = "PR-119" in card_map
    if strict_rescue:
        for field in (
            "completed",
            "blocked",
            "skipped",
            "pending",
            "dormant_external",
            "background_in_progress",
        ):
            raw = status.get(field, []) or []
            if not isinstance(raw, list) or not all(
                isinstance(pr_id, str) and pr_id for pr_id in raw
            ):
                raise ValueError(f"status {field} must be a PR-id list")
            if len(raw) != len(set(raw)):
                raise ValueError(f"status {field} contains duplicate PR ids")
        managed = {
            pr_id
            for pr_id in card_map
            if pr_id.startswith("PR-")
            and pr_id[3:].isdigit()
            and int(pr_id[3:]) >= 119
        }
        missing = sorted(managed - set(membership))
        if missing:
            raise ValueError(
                f"status orchestration coverage missing PR-119+ ids: {missing}"
            )

        expected_dormant = {
            pr_id
            for pr_id, card in card_map.items()
            if card.get("activation_state") in {"DORMANT_EXTERNAL", "NEEDS_NATIVE"}
        }
        if dormant_external != expected_dormant:
            raise ValueError(
                "dormant_external must match typed activation_state: "
                f"missing={sorted(expected_dormant - dormant_external)}, "
                f"unexpected={sorted(dormant_external - expected_dormant)}"
            )

    raw_lanes = status.get("execution_lane", {}) or {}
    if not isinstance(raw_lanes, Mapping) or not all(
        isinstance(pr_id, str)
        and lane in {"defensible", "hypothesis_only", "needs_native"}
        for pr_id, lane in raw_lanes.items()
    ):
        raise ValueError("status execution_lane must contain only typed lane values")
    expected_lanes = {
        pr_id: card["execution_lane"]
        for pr_id, card in card_map.items()
        if "execution_lane" in card
    }
    if dict(raw_lanes) != expected_lanes:
        raise ValueError("status execution_lane must exactly match typed card lanes")

    raw_contracts = status.get("background_execution_contracts", {}) or {}
    if not isinstance(raw_contracts, Mapping):
        raise ValueError("status background_execution_contracts must be a mapping")
    if set(raw_contracts) != background_in_progress:
        raise ValueError(
            "background_execution_contracts must exactly cover background_in_progress"
        )
    expected_contract = {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }
    malformed = sorted(
        pr_id
        for pr_id, contract in raw_contracts.items()
        if contract != expected_contract
    )
    if malformed:
        raise ValueError(f"background acquisition contract is malformed: {malformed}")
    if strict_rescue and background_in_progress - {"PR-151"}:
        raise ValueError("only PR-151 is authorized for rescue background acquisition")

    active = in_progress | background_in_progress
    unauthorized = []
    for pr_id in active:
        card = card_map[pr_id]
        lane = card.get("execution_lane", "defensible")
        authorization = card.get("execution_authorization", "DAG_SCHEDULABLE")
        if lane != "defensible" or authorization in {
            "REGISTERED_NOT_SCHEDULED",
            "NATIVE_BLOCKED",
        }:
            unauthorized.append(pr_id)
    if unauthorized:
        raise ValueError(
            f"active PRs are not execution-authorized: {sorted(unauthorized)}"
        )
    if strict_rescue:
        terminal = completed | blocked | skipped

        def dependency_is_satisfied(
            card: Mapping[str, object], dependency: str
        ) -> bool:
            contracts = card.get("dependency_contracts")
            if not isinstance(contracts, list):
                return dependency in completed
            matching = [
                contract
                for contract in contracts
                if isinstance(contract, Mapping)
                and contract.get("upstream_id") == dependency
            ]
            if len(matching) != 1:
                # The canonical DAG validator owns projection-shape errors.
                # Status generation remains fail-closed if it cannot resolve a
                # unique typed edge.
                return False
            mode = matching[0].get("mode")
            if mode == "requires_terminal_receipt":
                return dependency in terminal
            if mode in {"requires_success", "requires_adjudicated_claim_set"}:
                return dependency in completed
            return False

        dependency_blocked = sorted(
            pr_id
            for pr_id in active
            if any(
                not dependency_is_satisfied(card_map[pr_id], str(dep))
                for dep in card_map[pr_id].get("depends", [])
            )
        )
        if dependency_blocked:
            raise ValueError(
                f"active PRs have incomplete direct dependencies: {dependency_blocked}"
            )

    resolutions = _execution_resolutions(status.get("execution_resolutions"))
    unknown_resolutions = sorted(set(resolutions) - set(card_map))
    if unknown_resolutions:
        raise ValueError(
            f"execution_resolutions contain unknown PR ids: {unknown_resolutions}"
        )
    terminal = completed | blocked | skipped
    for pr_id, record in resolutions.items():
        if pr_id not in terminal:
            raise ValueError(f"non-terminal PR has execution resolution: {pr_id}")
        if not isinstance(record, Mapping):
            raise ValueError(f"execution resolution for {pr_id} must be a mapping")
        resolution = record.get("resolution")
        if resolution not in _TERMINAL_EXECUTION_RESOLUTIONS:
            raise ValueError(f"invalid execution resolution for {pr_id}: {resolution!r}")
        receipt = record.get("receipt")
        if not isinstance(receipt, str) or not receipt.strip():
            raise ValueError(f"execution resolution for {pr_id} lacks a valid receipt")
        if pr_id in completed and resolution != "COMPLETED_SUCCESS":
            raise ValueError(
                f"completed PR {pr_id} must have COMPLETED_SUCCESS resolution"
            )
        if pr_id in blocked and resolution not in {
            "COMPLETED_FAILED_WITH_RECEIPT",
            "BLOCKED_WITH_RECEIPT",
        }:
            raise ValueError(
                f"blocked PR {pr_id} must have a documented negative resolution"
            )
        if pr_id in skipped and resolution != "ABANDONED_WITH_RECEIPT":
            raise ValueError(
                f"skipped PR {pr_id} must have ABANDONED_WITH_RECEIPT resolution"
            )
    if strict_rescue:
        managed_terminal = {
            pr_id
            for pr_id in terminal
            if pr_id.startswith("PR-")
            and pr_id[3:].isdigit()
            and int(pr_id[3:]) >= 119
        }
        missing_resolutions = sorted(managed_terminal - set(resolutions))
        if missing_resolutions:
            raise ValueError(
                "terminal PR-119+ cards require execution resolution receipts: "
                f"{missing_resolutions}"
            )
    return resolutions


def _state_for_pr(
    *,
    pr_id: str,
    completed: set[str],
    blocked: set[str],
    skipped: set[str],
    pending: set[str],
    dormant_external: set[str],
    in_progress: set[str],
    background_in_progress: set[str],
) -> str:
    if pr_id in completed:
        return "completed"
    if pr_id in blocked:
        return "blocked"
    if pr_id in skipped:
        return "skipped"
    if pr_id in in_progress:
        return "in_progress"
    if pr_id in background_in_progress:
        return "background_in_progress"
    if pr_id in dormant_external:
        return "dormant_external"
    if pr_id in pending:
        return "pending"
    # Legacy status files did not enumerate pending rows. Preserve that
    # behavior for any row absent from all explicit state lists.
    return "pending"


def _state_from_row(row: Mapping[str, object]) -> str:
    state = row.get("orchestration_state")
    if isinstance(state, str) and state:
        return state
    # Compatibility with snapshots generated before orchestration_state was
    # an explicit orthogonal row field.
    if bool(row.get("implemented")):
        return "completed"
    if row.get("claim_tier") == ClaimTier.BLOCKED.value:
        return "blocked"
    return "not_completed"


def _allowed_claim(pr_id: str, state: str) -> str:
    return (
        f"{pr_id} is marked {state.replace('_', ' ')} in the Codex DAG status snapshot."
    )


def _input_hashes(paths: Sequence[Path]) -> list[str]:
    return [f"{_display_path(path)}:{_sha256_file(path)}" for path in paths]


def _config_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _current_source_commit() -> str:
    commit = _run_git(("rev-parse", "--short", "HEAD")) or "unknown"
    state = _worktree_state()
    return f"{commit}+dirty" if state == "dirty" else commit


def _worktree_state() -> str:
    status = _run_git(("status", "--short"))
    if status is None:
        return "unknown"
    return "dirty" if status else "clean"


def _run_git(args: Sequence[str]) -> str | None:
    completed = subprocess.run(
        ("git", *args),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _extract_matrix_counts(markdown: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in markdown.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 2:
            continue
        metric, raw_value = cells
        if metric in {"Metric", "---"}:
            continue
        try:
            counts[metric] = int(raw_value)
        except ValueError:
            continue
    return counts


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(
        value, (Owner, ImplementationScope, ClaimTier, ArtifactMode, AllowedUse)
    ):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    return value


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
