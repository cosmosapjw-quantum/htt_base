#!/usr/bin/env python3
"""Generate and validate the PR-119 remediation authority/reconciliation roots."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "docs/research_program/long_horizon_rescue/pr119_spec.yaml"
BACKLOG = REPO / "docs/codex_handoff/pr_backlog.yaml"
STATUS = REPO / "docs/codex_handoff/pr_status.yaml"
REGISTRY = REPO / "docs/codex_handoff/authorized_principals.yaml"
MACHINE_REGISTRY = REPO / "machine_readable/authorized_principals.yaml"
STATE = REPO / "docs/codex_handoff/research_remediation_state.yaml"
MACHINE_STATE = REPO / "machine_readable/research_remediation_state.yaml"
CROSSWALK = REPO / "docs/research_program/long_horizon_rescue/pr119_proposal_crosswalk.yaml"
RECONCILIATION = REPO / "docs/research_program/long_horizon_rescue/pr119_intake_reconciliation.json"
CRITICISM_MATRIX = REPO / "docs/audits/jcap_prd_adversarial_audit_20260714/criticism_response_matrix.json"
ATOMIC_LEDGER = REPO / "docs/audits/jcap_prd_adversarial_audit_20260714/atomic_finding_ledger.json"
ROOT_ADJUDICATIONS = REPO / "docs/audits/jcap_prd_adversarial_audit_20260714/root_adjudications.json"
FINAL_REFEREE_REPORT = REPO / "docs/audits/jcap_prd_adversarial_audit_20260714/final_referee_report.md"
NEXT_DAG = REPO / "docs/audits/jcap_prd_adversarial_audit_20260714/next_dag_candidates.json"
OLD_REVISION_DAG = REPO / "docs/codex_handoff/pr_dag_revision.yaml"
CHECKPOINT_065 = REPO / "docs/generated/progress_checkpoints/checkpoint_065.md"

EXPECTED_LEGACY_SLICE_SHA256 = (
    "31caa40afe347857ffbe920a7a5837264dab11d9ecdc430fd6721ab990254899"
)
EXPECTED_CHECKPOINT_065_SHA256 = (
    "dbee93f333d5ca33bb67ac2fed7c2a13720112a2df4b7ffaec17734f3321b809"
)
EXPECTED_PR118_SEAL_COMMIT = "294d74ce07de030da2f18720d3d45c8a2fef6e17"
EXPECTED_PR119_SPEC_SHA256 = (
    "406919201c4ff62ce40fcdc43bb3774780ff0f4fff43ef2e7409806c1ecfe609"
)
EXPECTED_PR119_RECONCILIATION_SHA256 = (
    "b1390f9a7f49cc0895b54c7ebda8910ae079ecfb35c27414c7b9e01ea7c5adb3"
)
EXPECTED_FROZEN_AUTHORITY_SHA256 = {
    "criticism_matrix": "f0c8c5316d8384bf223addd21c3f319039a26134bdc8507f4ae432206e7e9b0d",
    "atomic_finding_ledger": "6e88a6f6c4f95e5154c89e939230c94854b11a8430a64c28ccb339d8c4ab6feb",
    "root_adjudications": "4fcf738aed06ffec7cb3371562673eac211dc72407f475913e020d15d452c94a",
}
EXPECTED_FROZEN_CENSUS = {
    "root_record_count": 102,
    "known_open_and_audit_gap_count": 69,
    "new_open_count": 33,
    "rescued_count": 0,
    "response_dispositions_are_scientific_statuses": False,
}

AUD_CROSSWALK = {
    "AUD-R01A": ["PR-144", "PR-145", "PR-146"],
    "AUD-R01B": ["PR-147", "PR-148"],
    "AUD-R02A": ["PR-135", "PR-149", "PR-150"],
    "AUD-R02B": ["PR-122", "PR-123", "PR-143"],
    "AUD-R03": [f"PR-{value:03d}" for value in range(124, 134)],
    "AUD-R04": [f"PR-{value:03d}" for value in range(151, 155)],
    "AUD-R05A": ["PR-159", "PR-160", "PR-161"],
    "AUD-R05B": ["PR-162", "PR-163"],
    "AUD-R05C": ["PR-164", "PR-165", "PR-166"],
}

OLD_PR_CROSSWALK = {
    "PR-R000": ["PR-119", "PR-122"],
    "PR-R001": ["PR-119", "PR-122"],
    "PR-R002": ["PR-120", "PR-158"],
    "PR-R003": ["PR-158"],
    "PR-R004": ["PR-120", "PR-158"],
    "PR-R010": ["PR-140"],
    "PR-R011": ["PR-147", "PR-148"],
    "PR-R012": ["PR-135", "PR-143"],
    "PR-R013": ["PR-128", "PR-132"],
    "PR-R020": ["PR-142"],
    "PR-R021": ["PR-142"],
    "PR-R022": ["PR-142"],
    "PR-R023": ["PR-142"],
    "PR-R030": ["PR-133", "PR-156"],
    "PR-R031": ["PR-141", "PR-143"],
    "PR-R032": ["PR-141", "PR-156"],
    "PR-R033": ["PR-155"],
    "PR-R034": ["PR-155"],
    "PR-R040": ["PR-134", "PR-140"],
    "PR-R041": ["PR-134", "PR-140"],
    "PR-R042": ["PR-140", "PR-141"],
    "PR-R043": ["PR-127", "PR-136", "PR-163"],
    "PR-R050": ["PR-138"],
    "PR-R051": ["PR-139"],
    "PR-R052": ["PR-137", "PR-140", "PR-155"],
    "PR-R053": ["PR-158"],
    "PR-R060": ["PR-158"],
    "PR-R061": ["PR-158"],
    "PR-R062": ["PR-157"],
}

# Finding-to-active-card ownership is explicit even when a roadmap card names a
# whole finding family (for example ``C4-EXT-DESI-F1--F7``) rather than every
# atomic row.  This mapping schedules remediation only; it does not change the
# scientific status or response disposition of any finding.
FINDING_PREFIX_CROSSWALK = {
    "C1-K5-MV-": ["PR-134", "PR-144", "PR-145", "PR-146", "PR-147"],
    "C2-K5-MOCKSIG-": ["PR-135", "PR-146"],
    "C3-K5-VCORR-ML-": ["PR-134", "PR-144", "PR-145", "PR-146", "PR-147"],
    "C4-EXT-DESI-": ["PR-151"],
    "C5-EXT-ACT-": ["PR-135", "PR-152"],
    "C6-K6-CURL-": ["PR-123"],
    "C7-MES-": ["PR-122", "PR-124"],
    "C8-FRAMEWORK-": ["PR-124", "PR-125"],
    "C9-LCDMCV-RECON-": ["PR-145", "PR-147"],
    "C10-K1-JWST-": ["PR-149", "PR-150", "PR-153", "PR-154"],
}

EXACT_FINDING_CROSSWALK = {
    "GAP-01": ["PR-122", "PR-157"],
    "GAP-02": ["PR-120", "PR-144", "PR-145", "PR-146", "PR-147", "PR-148"],
    "GAP-03": ["PR-145", "PR-148", "PR-157"],
    "GAP-04": ["PR-124", "PR-128", "PR-131", "PR-132", "PR-149", "PR-153"],
    "GAP-05": ["PR-137", "PR-143"],
    "GAP-06": ["PR-135", "PR-150", "PR-151", "PR-152", "PR-154"],
    "GAP-07": ["PR-152", "PR-157"],
    "GAP-08": ["PR-157"],
    "GAP-09": ["PR-157", "PR-158"],
    "GAP-10": ["PR-123", "PR-143"],
    "GAP-11": ["PR-120", "PR-122", "PR-128"],
    "GAP-12": ["PR-144", "PR-145", "PR-146", "PR-147"],
    "GAP-13": ["PR-119"],
    "GAP-14": ["PR-119"],
    "N-DATA-PLANCK-MASK": ["PR-149", "PR-150"],
    "N-THEORY-TEFF-OWNERSHIP": ["PR-121"],
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain a mapping")
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO)} must contain an object")
    return payload


def _validate_frozen_authority_inputs() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    """Return the immutable PR-118 authority roots only after exact validation.

    The approved PR-119 SPEC is itself pinned here so ``--write`` cannot bless a
    coordinated edit to both an authority root and the hash recorded in the
    SPEC.  The semantic census checks are intentionally redundant with the
    byte hashes: they make the zero-rescue intake invariant explicit and give a
    useful failure if a future migration is attempted deliberately.
    """

    spec_hash = _sha256(SPEC)
    if spec_hash != EXPECTED_PR119_SPEC_SHA256:
        raise ValueError("approved PR-119 SPEC hash drift")
    spec = _load_yaml(SPEC)
    frozen_inputs = spec.get("frozen_inputs")
    if not isinstance(frozen_inputs, dict):
        raise ValueError("PR-119 SPEC frozen_inputs must be a mapping")

    authority_paths = {
        "criticism_matrix": (
            CRITICISM_MATRIX,
            "docs/audits/jcap_prd_adversarial_audit_20260714/criticism_response_matrix.json",
        ),
        "atomic_finding_ledger": (
            ATOMIC_LEDGER,
            "docs/audits/jcap_prd_adversarial_audit_20260714/atomic_finding_ledger.json",
        ),
        "root_adjudications": (
            ROOT_ADJUDICATIONS,
            "docs/audits/jcap_prd_adversarial_audit_20260714/root_adjudications.json",
        ),
    }
    for key, (path, expected_path) in authority_paths.items():
        entry = frozen_inputs.get(key)
        expected_hash = EXPECTED_FROZEN_AUTHORITY_SHA256[key]
        if entry != {"path": expected_path, "sha256": expected_hash}:
            raise ValueError(f"PR-119 SPEC frozen authority entry drift: {key}")
        if _sha256(path) != expected_hash:
            raise ValueError(f"frozen authority hash drift: {key}")

    census = spec.get("state_contract", {}).get("initial_authoritative_census")
    if census != EXPECTED_FROZEN_CENSUS:
        raise ValueError("PR-119 SPEC frozen authority census drift")

    matrix = _load_json(CRITICISM_MATRIX)
    atomic = _load_json(ATOMIC_LEDGER)
    adjudications = _load_json(ROOT_ADJUDICATIONS)
    rows = matrix.get("rows")
    if not isinstance(rows, list) or len(rows) != 102:
        raise ValueError("frozen criticism matrix must contain exactly 102 rows")
    finding_ids = [row.get("criticism_id") for row in rows if isinstance(row, dict)]
    if len(finding_ids) != 102 or len(set(finding_ids)) != 102:
        raise ValueError("frozen criticism matrix finding identities are not one-to-one")
    source_states = Counter(
        str(row.get("authoritative_state")) for row in rows if isinstance(row, dict)
    )
    if source_states != Counter({"KNOWN_OPEN": 69, "NEW_OPEN": 33}):
        raise ValueError("frozen criticism matrix census is not 69 known/gap + 33 new")
    if matrix.get("row_count") != 102 or matrix.get("origin_counts") != {
        "audit_gap": 14,
        "delta_new": 33,
        "prior": 55,
    }:
        raise ValueError("frozen criticism matrix declared census drift")

    atomic_rows = atomic.get("atomic_findings")
    if not isinstance(atomic_rows, list):
        raise ValueError("frozen atomic finding ledger rows must be a list")
    atomic_dispositions = Counter(
        str(row.get("disposition")) for row in atomic_rows if isinstance(row, dict)
    )
    if (
        atomic.get("new_open_count") != 33
        or atomic.get("remediated_in_pr117_count") != 1
        or atomic.get("reuse_prior_count") != 2
        or atomic_dispositions
        != Counter({"NEW_OPEN": 33, "REMEDIATED_IN_PR117": 1, "REUSE_PRIOR": 2})
    ):
        raise ValueError("frozen atomic finding ledger census drift")

    if (
        adjudications.get("prior_findings_preserved") != 55
        or adjudications.get("prior_completeness_gaps_preserved") != 14
        or adjudications.get("new_open_finding_count") != 33
    ):
        raise ValueError("frozen root adjudication census drift")
    return spec, matrix, atomic, adjudications


def _artifact_metadata(*, artifact_id: str, config_hash: str, inputs: list[str]) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "artifact_mode": "governance_diagnostic",
        "allowed_use": "internal_orchestration_only",
        "transfer_source": "none",
        "config_hash": config_hash,
        "input_hashes": inputs,
        "sky_support_status": "not_applicable_governance",
        "null_mock_status": "not_applicable_governance",
        "caveats": [
            "DAG and ledger state are not scientific readiness evidence.",
            "Response dispositions remain historical recommendations, not scientific terminal states.",
        ],
        "generating_command": "venv/bin/python -B scripts/codex_harness/validate_research_remediation.py --write",
        "git_commit_or_worktree_state": "PR-119_worktree",
    }


def _target_prs(finding_id: str, cards: list[dict[str, Any]]) -> list[str]:
    targets = {
        str(card["id"])
        for card in cards
        if finding_id in " ".join(str(item) for item in card.get("targets", []))
    }
    targets.update(EXACT_FINDING_CROSSWALK.get(finding_id, ()))
    for prefix, pr_ids in FINDING_PREFIX_CROSSWALK.items():
        if finding_id.startswith(prefix):
            targets.update(pr_ids)
    return sorted(targets, key=lambda value: int(value.split("-")[1]))


def build_state() -> dict[str, Any]:
    _, matrix, _, _ = _validate_frozen_authority_inputs()
    spec_hash = EXPECTED_PR119_SPEC_SHA256
    backlog = _load_yaml(BACKLOG)
    pr119_slice = {f"PR-{value:03d}" for value in range(119, 167)}
    cards = [
        card
        for card in backlog.get("prs", [])
        if isinstance(card, dict) and card.get("id") in pr119_slice
    ]
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        raise ValueError("criticism matrix rows must be a list")
    findings = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("criticism matrix row must be an object")
        identity = {
            "finding_id": row["criticism_id"],
            "source_hash": row["source_hash"],
            "source_reference": row["source_reference"],
            "authoritative_source_state": row["authoritative_state"],
        }
        findings.append(
            {
                **identity,
                "identity_fingerprint": _canonical_sha256(identity),
                "origin": row["origin"],
                "severity": row["severity"],
                "response_disposition": row["disposition"],
                "response_disposition_is_scientific_status": False,
                "scientific_status": "OPEN",
                "execution_resolution": None,
                "claim_tier_ceiling": "blocked",
                "remediation_pr_ids": _target_prs(str(row["criticism_id"]), cards),
                "decisive_closeout_evidence": row["decisive_closeout_evidence"],
            }
        )
    metadata = _artifact_metadata(
        artifact_id="pr119.active_remediation_root",
        config_hash=spec_hash,
        inputs=[
            f"{CRITICISM_MATRIX.relative_to(REPO)}:{_sha256(CRITICISM_MATRIX)}",
            f"{ATOMIC_LEDGER.relative_to(REPO)}:{_sha256(ATOMIC_LEDGER)}",
            f"{ROOT_ADJUDICATIONS.relative_to(REPO)}:{_sha256(ROOT_ADJUDICATIONS)}",
            f"{SPEC.relative_to(REPO)}:{spec_hash}",
            f"{BACKLOG.relative_to(REPO)}:{_sha256(BACKLOG)}",
        ],
    )
    source_states = Counter(str(row["authoritative_state"]) for row in rows)
    return {
        "schema": "htt.research_remediation_state.v1",
        **metadata,
        "authority_registry": str(REGISTRY.relative_to(REPO)),
        "authority_roots": [
            {
                "path": str(CRITICISM_MATRIX.relative_to(REPO)),
                "sha256": _sha256(CRITICISM_MATRIX),
                "role": "active_finding_identity_and_response_disposition_root",
                "immutable": True,
            },
            {
                "path": str(ATOMIC_LEDGER.relative_to(REPO)),
                "sha256": _sha256(ATOMIC_LEDGER),
                "role": "new_open_severity_census",
                "immutable": True,
            },
            {
                "path": str(FINAL_REFEREE_REPORT.relative_to(REPO)),
                "sha256": _sha256(FINAL_REFEREE_REPORT),
                "role": "immutable_historical_referee_prose_non_authoritative_for_current_counts",
                "immutable": True,
            },
        ],
        "census": {
            "finding_count": len(findings),
            "known_open_and_audit_gap_count": source_states["KNOWN_OPEN"],
            "new_open_count": source_states["NEW_OPEN"],
            "scientific_status_counts": {"OPEN": len(findings)},
            "rescued_count": 0,
        },
        "findings": findings,
    }


def _normalize_state_generation_inputs(
    state: dict[str, Any],
    expected_state: dict[str, Any],
) -> dict[str, Any]:
    """Treat the PR-119 backlog digest as generation-time provenance only."""

    inputs = state.get("input_hashes")
    expected_inputs = expected_state.get("input_hashes")
    if (
        not isinstance(inputs, list)
        or not isinstance(expected_inputs, list)
        or len(inputs) != len(expected_inputs)
        or inputs[:-1] != expected_inputs[:-1]
    ):
        raise ValueError("remediation state frozen input identities drifted")
    backlog_prefix = f"{BACKLOG.relative_to(REPO)}:"
    backlog_input = inputs[-1]
    if not isinstance(backlog_input, str) or not backlog_input.startswith(backlog_prefix):
        raise ValueError("remediation state generation-time backlog identity is malformed")
    digest = backlog_input.removeprefix(backlog_prefix)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("remediation state generation-time backlog digest is malformed")

    normalized = dict(state)
    normalized["input_hashes"] = expected_inputs
    return normalized


def build_crosswalk() -> dict[str, Any]:
    spec_hash = _sha256(SPEC)
    next_dag = _load_json(NEXT_DAG)
    aud_ids = {str(row["id"]) for row in next_dag.get("cards", [])}
    old = _load_yaml(OLD_REVISION_DAG)
    old_ids = {str(row["id"]) for row in old.get("prs", [])}
    if aud_ids != set(AUD_CROSSWALK):
        raise ValueError("AUD proposal IDs drift from the approved crosswalk")
    if old_ids != set(OLD_PR_CROSSWALK):
        raise ValueError("PR-R proposal IDs drift from the approved crosswalk")
    metadata = _artifact_metadata(
        artifact_id="pr119.proposal_to_active_crosswalk",
        config_hash=spec_hash,
        inputs=[
            f"{NEXT_DAG.relative_to(REPO)}:{_sha256(NEXT_DAG)}",
            f"{OLD_REVISION_DAG.relative_to(REPO)}:{_sha256(OLD_REVISION_DAG)}",
            f"{SPEC.relative_to(REPO)}:{spec_hash}",
        ],
    )
    rows = [
        {"proposal_id": key, "proposal_kind": "audit_umbrella", "superseded_by": value}
        for key, value in AUD_CROSSWALK.items()
    ]
    rows.extend(
        {"proposal_id": key, "proposal_kind": "supplemental_revision", "superseded_by": value}
        for key, value in OLD_PR_CROSSWALK.items()
    )
    return {"schema": "htt.pr119.proposal_crosswalk.v1", **metadata, "rows": rows}


def build_reconciliation() -> dict[str, Any]:
    """Load and validate the immutable PR-119 closeout snapshot.

    This artifact is historical evidence, not a view over the live DAG.  In
    particular, PR-120+ status changes must not cause it to be regenerated.
    """

    if not RECONCILIATION.exists():
        raise ValueError("immutable PR-119 reconciliation is missing")
    if _sha256(RECONCILIATION) != EXPECTED_PR119_RECONCILIATION_SHA256:
        raise ValueError("immutable PR-119 reconciliation hash drift; refusing overwrite")
    payload = _load_json(RECONCILIATION)
    post_intake = payload.get("post_intake")
    if not isinstance(post_intake, dict) or post_intake.get("active_slice") != [
        f"PR-{value:03d}" for value in range(119, 167)
    ]:
        raise ValueError("immutable PR-119 reconciliation active slice drift")
    if (
        payload.get("schema") != "htt.pr119.intake_reconciliation.v1"
        or payload.get("config_hash") != EXPECTED_PR119_SPEC_SHA256
        or post_intake.get("total_prs") != 113
        or post_intake.get("completed_prs") != 66
        or post_intake.get("pending_prs") != 39
        or post_intake.get("dormant_external_prs") != 8
        or post_intake.get("legacy_slice_semantic_sha256")
        != EXPECTED_LEGACY_SLICE_SHA256
        or post_intake.get("forbidden_advocate_slice_present") is not False
        or payload.get("scientific_authority", {}).get("finding_count") != 102
        or payload.get("scientific_authority", {}).get("rescued_count") != 0
    ):
        raise ValueError("immutable PR-119 reconciliation semantic drift")
    return payload


def _validate_registry() -> None:
    from common.remediation_state import (
        AuthorityRegistry,
        PrincipalRecord,
        assert_distinct_author_adjudicator,
    )

    registry = _load_yaml(REGISTRY)
    if registry.get("default_deny") is not True:
        raise ValueError("authority registry must default deny")
    principals = registry.get("principals")
    if not isinstance(principals, list):
        raise ValueError("authority registry principals must be a list")
    required = {
        "principal_id",
        "identity_fingerprint",
        "aliases",
        "allowed_roles",
        "allowed_scopes",
        "independence_class",
        "valid_from",
        "valid_until",
        "revoked",
        "verifier",
        "can_promote_scientific_status",
    }
    identities: set[str] = set()
    aliases: set[str] = set()
    records: list[PrincipalRecord] = []
    for principal in principals:
        if not isinstance(principal, dict) or required - set(principal):
            raise ValueError("authority registry principal is missing required fields")
        if principal["can_promote_scientific_status"] is not False:
            raise ValueError("PR-119 bootstrap principal cannot promote scientific status")
        if set(principal["allowed_roles"]) - {"author", "adjudicator"}:
            raise ValueError("PR-119 bootstrap grants an unauthorized active role")
        fingerprint = str(principal["identity_fingerprint"])
        if fingerprint in identities:
            raise ValueError("authority registry has duplicate identity fingerprints")
        identities.add(fingerprint)
        for alias in principal["aliases"]:
            if alias in aliases:
                raise ValueError("authority registry has duplicate aliases")
            aliases.add(alias)
        records.append(
            PrincipalRecord(
                principal_id=principal["principal_id"],
                identity_fingerprint=principal["identity_fingerprint"],
                aliases=principal["aliases"],
                allowed_roles=principal["allowed_roles"],
                allowed_scopes=principal["allowed_scopes"],
                independence_class=principal["independence_class"],
                valid_from=principal["valid_from"],
                valid_until=principal["valid_until"],
                revoked=principal["revoked"],
                verifier=principal["verifier"],
            )
        )
    typed_registry = AuthorityRegistry(tuple(records))
    assert_distinct_author_adjudicator(
        typed_registry,
        author="codex:/root",
        adjudicator="codex:/root/pr119_spec",
        scope="PR-119",
        at="2026-07-15T00:00:00+09:00",
    )


def validate_all() -> None:
    spec, _, _, _ = _validate_frozen_authority_inputs()
    if spec.get("spec_status") != "approved_for_implementation":
        raise ValueError("PR-119 SPEC is not approved")
    _validate_registry()
    if REGISTRY.read_bytes() != MACHINE_REGISTRY.read_bytes():
        raise ValueError("authority registry mirror drift")
    state = _load_yaml(STATE)
    expected_state = build_state()
    normalized_state = _normalize_state_generation_inputs(state, expected_state)
    if normalized_state != expected_state or STATE.read_bytes() != MACHINE_STATE.read_bytes():
        raise ValueError("remediation state is stale or mirror-drifted")
    if _load_yaml(CROSSWALK) != build_crosswalk():
        raise ValueError("proposal crosswalk is stale")
    build_reconciliation()
    if state["census"]["finding_count"] != 102 or state["census"]["rescued_count"] != 0:
        raise ValueError("initial remediation census must be 102 OPEN / 0 RESCUED")
    if any(row["scientific_status"] != "OPEN" for row in state["findings"]):
        raise ValueError("intake cannot promote any scientific finding")
    if any(not row["remediation_pr_ids"] for row in state["findings"]):
        raise ValueError("every atomic finding must map to at least one active remediation card")
    backlog = _load_yaml(BACKLOG)
    ids = [row["id"] for row in backlog["prs"]]
    expected_ids = [f"PR-{value:03d}" for value in range(119, 167)]
    if ids[65:113] != expected_ids:
        raise ValueError("PR-119 intake slice is not exactly PR-119..PR-166")
    if _canonical_sha256(backlog["prs"][:65]) != EXPECTED_LEGACY_SLICE_SHA256:
        raise ValueError("frozen legacy 65-card slice drift")
    if _sha256(CHECKPOINT_065) != EXPECTED_CHECKPOINT_065_SHA256:
        raise ValueError("immutable checkpoint_065 drift")


def write_all() -> None:
    # Validate every immutable input, especially the existing reconciliation,
    # before touching generated state.  A divergent historical closeout is
    # never repaired in place by ``--write``.
    _validate_frozen_authority_inputs()
    build_reconciliation()
    expected_state = build_state()
    if STATE.exists():
        state = _load_yaml(STATE)
        if _normalize_state_generation_inputs(state, expected_state) != expected_state:
            raise ValueError("existing PR-119 remediation state semantic drift; refusing overwrite")
        state_text = STATE.read_text(encoding="utf-8")
    else:
        state_text = yaml.safe_dump(
            expected_state,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        )
    crosswalk = build_crosswalk()
    STATE.write_text(state_text, encoding="utf-8")
    MACHINE_STATE.write_text(state_text, encoding="utf-8")
    CROSSWALK.write_text(
        yaml.safe_dump(crosswalk, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            write_all()
        validate_all()
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("OK: PR-119 remediation authority, crosswalk, and reconciliation are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
