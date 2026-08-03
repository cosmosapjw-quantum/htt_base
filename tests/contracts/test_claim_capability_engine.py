from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
import hashlib
import inspect
import json
from pathlib import Path
import weakref

import pytest
import yaml

import common.evidence_graph as evidence_graph_module
import common.remediation_state as remediation_state_module
from common.evidence_graph import (
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
    authority_registry_content_ref,
    issue_claim_capability_decision,
    issue_evidence_receipt,
    lifecycle_invalidation_dimension,
    typed_invalidation_targets,
)
from common.remediation_state import (
    AdjudicatedClaim,
    AdjudicationReceipt,
    ArtifactReadinessAxis,
    AuthorityRegistry,
    CapabilityAction,
    CapabilityBlocker,
    CapabilityBlockerKind,
    CapabilityEvidenceBranch,
    CapabilityIdentification,
    CapabilityOutcome,
    CapabilityProvenanceGrade,
    CapabilityScientificSemantics,
    CanonicalClaimTier,
    ClaimCapability,
    ClaimCapabilityDecision,
    ClaimIdentity,
    ClaimLevelScheme,
    IdentityDimension,
    NON_RELAXABLE_CAPABILITY_RULES,
    PrincipalRecord,
    RemediationContractError,
    ScientificStatus,
    VersionedClaimIdentity,
)


ROOT = Path(__file__).resolve().parents[2]
SCOPE = "PR-277:claim-capability-engine"
ISSUED_AT = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 8, 3, 13, 0, tzinfo=UTC)

_CAPABILITY_CEILINGS = {
    ClaimCapability.CONTRACT_VALIDATED: "contract_only",
    ClaimCapability.THEOREM_PROVED_EXACT: "exact_theorem_only",
    ClaimCapability.THEOREM_PROVED_CONDITIONAL: "conditional_theorem_only",
    ClaimCapability.METHOD_CALIBRATED: "method_only",
    ClaimCapability.DATA_ADMITTED: "data_admission_only",
    ClaimCapability.OBSERVED_DESCRIPTIVE: "observed_descriptive_only",
    ClaimCapability.OBSERVED_INFERENTIAL: "htt_inference_only",
    ClaimCapability.SOURCE_SEPARATION_CANDIDATE: "candidate_only",
    ClaimCapability.MORPHOLOGY_COMPATIBILITY: "compatibility_only",
    ClaimCapability.FAMILY_IDENTIFICATION: "blocked_pre_native_atlas",
    ClaimCapability.PUBLIC_RELEASE: "receipt_scoped_public_release",
}

_CAPABILITY_ALLOWED_OWNERS = {
    ClaimCapability.CONTRACT_VALIDATED: {"COMMON"},
    ClaimCapability.THEOREM_PROVED_EXACT: {"COMMON", "BASS"},
    ClaimCapability.THEOREM_PROVED_CONDITIONAL: {"COMMON", "BASS"},
    ClaimCapability.METHOD_CALIBRATED: {
        "COMMON",
        "HTT",
        "MIO",
        "BASS",
        "OBSSTAT",
    },
    ClaimCapability.DATA_ADMITTED: {"COMMON", "OBSSTAT"},
    ClaimCapability.OBSERVED_DESCRIPTIVE: {"HTT", "MIO", "OBSSTAT"},
    ClaimCapability.OBSERVED_INFERENTIAL: {"HTT"},
    ClaimCapability.SOURCE_SEPARATION_CANDIDATE: {"HTT"},
    ClaimCapability.MORPHOLOGY_COMPATIBILITY: {"HTT", "BASS", "OBSSTAT"},
    ClaimCapability.FAMILY_IDENTIFICATION: {"BASS"},
    ClaimCapability.PUBLIC_RELEASE: {"COMMON"},
}

_ACTIVE_TEST_OWNERS = ("COMMON", "HTT", "MIO", "BASS", "OBSSTAT")


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _identity(*, claim_id: str = "PR277-CONTRACT", suffix: str = "v1") -> ClaimIdentity:
    return ClaimIdentity(
        claim_id=claim_id,
        claim_text=f"evidence-conditioned contract {suffix}",
        quantifier="exact_registered_contract",
        estimand="claim_capability_decision",
        target_population="registered_claim_consumers",
        domain="pre_solver",
        frame="not_applicable",
        perturbative_order="not_applicable",
        units="not_applicable",
        data_release="not_applicable",
        sky_support_mask_selection="not_applicable",
        statistic_pipeline="content_addressed_evidence_closure",
        transfer_source="none",
        nuisance_prior_null_multiplicity="not_applicable",
        claim_level_scheme=ClaimLevelScheme.NOT_APPLICABLE_GOVERNANCE_V1,
        claim_level="NOT_APPLICABLE",
        claim_tier_ceiling=CanonicalClaimTier.DIAGNOSTIC_ONLY,
    )


def _components(suffix: str = "v1") -> dict[IdentityDimension, str]:
    return {
        dimension: _digest(f"{dimension.value}:{suffix}")
        for dimension in IdentityDimension
    }


def _versioned(*, owner: str = "COMMON", suffix: str = "v1") -> VersionedClaimIdentity:
    return VersionedClaimIdentity.root(
        version=suffix,
        owner=owner,
        claim_identity=_identity(suffix=suffix),
        component_fingerprints=_components(suffix),
    )


def _axes(science: ScientificStatus = ScientificStatus.OPEN) -> EvidenceAxes:
    return EvidenceAxes(ProcessResult.PASS, EvidenceStatus.PRESENT, science)


def _node(
    kind: EvidenceNodeKind,
    label: str,
    *,
    science: ScientificStatus = ScientificStatus.OPEN,
    content_sha256: str | None = None,
    metadata: dict[str, object] | None = None,
) -> EvidenceNode:
    return EvidenceNode(
        kind=kind,
        label=label,
        content_sha256=content_sha256 or _digest(label),
        axes=_axes(science),
        metadata={"owner": "COMMON", **(metadata or {})},
    )


def _graph(
    versioned: VersionedClaimIdentity,
    *,
    science: ScientificStatus = ScientificStatus.RESCUED,
    rules: tuple[str, ...] = NON_RELAXABLE_CAPABILITY_RULES,
    capability: ClaimCapability = ClaimCapability.CONTRACT_VALIDATED,
    action: CapabilityAction = CapabilityAction.GRANT,
    outcome: CapabilityOutcome = CapabilityOutcome.PASS,
    lifecycle_edges: tuple[EvidenceEdge, ...] = (),
    extra_nodes: tuple[EvidenceNode, ...] = (),
) -> tuple[EvidenceGraph, EvidenceNode, dict[str, EvidenceNode]]:
    claim = _node(
        EvidenceNodeKind.CLAIM,
        f"claim:{versioned.identity_ref[:12]}",
        science=science,
        content_sha256=versioned.identity_ref,
        metadata={
            "claim_id": versioned.claim_identity.claim_id,
            "claim_identity_fingerprint": (
                versioned.claim_identity.identity_fingerprint
            ),
            "versioned_identity_ref": versioned.identity_ref,
            "non_relaxable_rules": list(rules),
            "capability_binding": {
                "schema_version": "claim_capability_binding_v1",
                "capability": capability.value,
                "action": action.value,
                "outcome": outcome.value,
                "claim_ceiling": _CAPABILITY_CEILINGS[capability],
            },
        },
    )
    nodes = {
        "producer": _node(EvidenceNodeKind.PRODUCER, "producer:pr277"),
        "input": _node(EvidenceNodeKind.INPUT, "input:pr277"),
        "config": _node(EvidenceNodeKind.CONFIG, "config:pr277"),
        "environment": _node(EvidenceNodeKind.ENVIRONMENT, "environment:pr277"),
        "oracle": _node(EvidenceNodeKind.ORACLE, "oracle:pr277"),
        "artifact": _node(EvidenceNodeKind.ARTIFACT, "artifact:pr277"),
        "consumer": _node(EvidenceNodeKind.CONSUMER, "consumer:pr277"),
    }
    support = (
        EvidenceEdge(
            EvidenceEdgeKind.PRODUCED_BY,
            claim.node_ref,
            nodes["producer"].node_ref,
            {},
        ),
        EvidenceEdge(
            EvidenceEdgeKind.USES_INPUT,
            nodes["producer"].node_ref,
            nodes["input"].node_ref,
            {},
        ),
        EvidenceEdge(
            EvidenceEdgeKind.USES_CONFIG,
            nodes["producer"].node_ref,
            nodes["config"].node_ref,
            {},
        ),
        EvidenceEdge(
            EvidenceEdgeKind.USES_ENVIRONMENT,
            nodes["producer"].node_ref,
            nodes["environment"].node_ref,
            {},
        ),
        EvidenceEdge(
            EvidenceEdgeKind.CHECKED_BY,
            nodes["producer"].node_ref,
            nodes["oracle"].node_ref,
            {},
        ),
        EvidenceEdge(
            EvidenceEdgeKind.GENERATES,
            nodes["oracle"].node_ref,
            nodes["artifact"].node_ref,
            {},
        ),
        EvidenceEdge(
            EvidenceEdgeKind.CONSUMED_BY,
            nodes["artifact"].node_ref,
            nodes["consumer"].node_ref,
            {},
        ),
    )
    return (
        EvidenceGraph(
            nodes=(claim, *nodes.values(), *extra_nodes),
            edges=(*support, *lifecycle_edges),
        ),
        claim,
        nodes,
    )


def _registry() -> tuple[AuthorityRegistry, PrincipalRecord, PrincipalRecord]:
    verifier = "pr277_sha256_verifier"
    author = PrincipalRecord(
        principal_id="pr277-author",
        identity_fingerprint=_digest("pr277-author"),
        aliases=(),
        allowed_roles=("author",),
        allowed_scopes=(SCOPE,),
        independence_class="internal_author",
        valid_from="2026-01-01T00:00:00+00:00",
        valid_until="2027-01-01T00:00:00+00:00",
        revoked=False,
        verifier=verifier,
    )
    adjudicator = PrincipalRecord(
        principal_id="pr277-adjudicator",
        identity_fingerprint=_digest("pr277-adjudicator"),
        aliases=(),
        allowed_roles=("adjudicator", "scientific_status_promoter"),
        allowed_scopes=(SCOPE,),
        independence_class="independent_external",
        valid_from="2026-01-01T00:00:00+00:00",
        valid_until="2027-01-01T00:00:00+00:00",
        revoked=False,
        verifier=verifier,
    )

    def verify(principal: PrincipalRecord, payload: bytes, attestation: str) -> bool:
        expected = hashlib.sha256(
            principal.identity_fingerprint.encode("ascii") + payload
        ).hexdigest()
        return attestation == expected

    return (
        AuthorityRegistry((author, adjudicator), verifiers={verifier: verify}),
        author,
        adjudicator,
    )


def _receipts(
    graph: EvidenceGraph,
    claim: EvidenceNode,
    versioned: VersionedClaimIdentity,
) -> tuple[EvidenceReceipt, AdjudicationReceipt, AuthorityRegistry]:
    registry, author, adjudicator = _registry()
    body = EvidenceReceiptBody.from_graph(
        graph,
        claim_ref=claim.node_ref,
        author=author.principal_id,
        author_identity_fingerprint=author.identity_fingerprint,
        adjudicator=adjudicator.principal_id,
        adjudicator_identity_fingerprint=adjudicator.identity_fingerprint,
        authority_registry_ref=authority_registry_content_ref(registry),
        scope=SCOPE,
        issued_at=ISSUED_AT,
    )
    evidence_receipt = issue_evidence_receipt(
        body,
        attestation_factory=lambda payload: hashlib.sha256(
            adjudicator.identity_fingerprint.encode("ascii") + payload
        ).hexdigest(),
    )
    adjudication = AdjudicationReceipt(
        receipt_id=_digest("pr277-adjudication-receipt"),
        author=author.principal_id,
        author_identity_fingerprint=author.identity_fingerprint,
        adjudicator=adjudicator.principal_id,
        adjudicator_identity_fingerprint=adjudicator.identity_fingerprint,
        scope=SCOPE,
        accepted_claims=(
            AdjudicatedClaim(
                claim_id=versioned.claim_identity.claim_id,
                identity_fingerprint=(versioned.claim_identity.identity_fingerprint),
                scientific_status=claim.axes.scientific_status,
            ),
        ),
        issued_at=ISSUED_AT,
        attestation="pending",
    )
    adjudication = replace(
        adjudication,
        attestation=hashlib.sha256(
            adjudicator.identity_fingerprint.encode("ascii")
            + adjudication.canonical_attestation_payload()
        ).hexdigest(),
    )
    return evidence_receipt, adjudication, registry


def _issue(
    *,
    versioned: VersionedClaimIdentity | None = None,
    capability: ClaimCapability = ClaimCapability.CONTRACT_VALIDATED,
    action: CapabilityAction = CapabilityAction.GRANT,
    outcome: CapabilityOutcome = CapabilityOutcome.PASS,
    blockers: tuple[CapabilityBlocker, ...] = (),
    science: ScientificStatus = ScientificStatus.RESCUED,
    rules: tuple[str, ...] = NON_RELAXABLE_CAPABILITY_RULES,
) -> ClaimCapabilityDecision:
    identity = versioned or _versioned()
    graph, claim, _nodes = _graph(
        identity,
        science=science,
        rules=rules,
        capability=capability,
        action=action,
        outcome=outcome,
    )
    evidence_receipt, adjudication, registry = _receipts(graph, claim, identity)
    return issue_claim_capability_decision(
        graph,
        versioned_identity=identity,
        evidence_receipt=evidence_receipt,
        adjudication_receipt=adjudication,
        registry=registry,
        capability=capability,
        action=action,
        outcome=outcome,
        blockers=blockers,
        evaluated_at=EVALUATED_AT,
    )


def test_spec_and_public_vocabulary_are_exact() -> None:
    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr277_spec.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert spec["capabilities"] == [item.value for item in ClaimCapability]
    assert spec["actions"] == [item.value for item in CapabilityAction]
    assert spec["outcomes"] == [item.value for item in CapabilityOutcome]
    assert spec["non_relaxable_rules"] == list(NON_RELAXABLE_CAPABILITY_RULES)
    assert spec["factory_contract"]["capability_binding"] == {
        "schema_version": "claim_capability_binding_v1",
        "exact_fields": ["capability", "action", "outcome", "claim_ceiling"],
        "rule": (
            "The requested decision must exactly match the binding adjudicated "
            "with the claim node."
        ),
    }
    assert set(spec["evidence_lifecycle_edges"]) == {
        item.name
        for item in EvidenceEdgeKind
        if item.name.startswith("INVALIDATES_")
        or item
        in {
            EvidenceEdgeKind.SUPERSEDED_BY,
            EvidenceEdgeKind.REQUIRES_RECALIBRATION,
            EvidenceEdgeKind.REQUIRES_REEXECUTION,
        }
    }


def test_publication_policy_allows_only_one_attended_review_pr_transaction() -> None:
    policy = json.loads(
        (
            ROOT
            / "docs/research_program/post_pr275/pr277_publication_policy.json"
        ).read_text(encoding="utf-8")
    )
    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr277_spec.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert policy["target_sha"] == "a6d3bd8b24e15727fbb6011c515d66d49cd4ba92"
    assert policy["ordinary_agent_push_forbidden"] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert policy["attended_publication"] == {
        "enabled": True,
        "authorization_mode": "attended_explicit_user",
        "transaction": "sealed_sha_push_then_single_pr_create",
        "max_transactions": 1,
        "requires_current_turn_authorization": True,
        "direct_mutation_commands_forbidden": True,
        "nonce_ledger_binding": "authorization_hmac_frozen_external_inode_v1",
        "publisher_entrypoint": ".agent-harness/scripts/attended_pr_publisher.py",
        "forbidden_actions": [
            "force_push",
            "approve",
            "merge",
            "ruleset_mutation",
        ],
    }
    assert [row["id"] for row in policy["required_commands"]] == [
        "pr277-focused",
        "pr277-dag",
        "pr277-mirror-check",
        "pr277-collect",
        "pr277-smoke",
        "pr277-claim-language",
        "pr277-research-surface-claim-lint",
    ]
    assert spec["delivery_authorization"]["authorized_actions"] == [
        "content_commit",
        "closeout_commit",
        "one_review_pr",
    ]
    assert spec["delivery_authorization"]["forbidden_actions"] == [
        "force_push",
        "approve",
        "merge",
        "ruleset_mutation",
    ]


def test_versioned_identity_is_factory_only_and_successor_is_not_in_place() -> None:
    root = _versioned()
    with pytest.raises(TypeError):
        VersionedClaimIdentity()  # type: ignore[call-arg]
    with pytest.raises(RemediationContractError, match="no-op successor"):
        VersionedClaimIdentity.successor(
            root,
            version="v2",
            claim_identity=root.claim_identity,
            component_fingerprints=root.component_fingerprints,
        )
    changed = dict(root.component_fingerprints)
    changed[IdentityDimension.DATA] = _digest("DATA:v2")
    successor = VersionedClaimIdentity.successor(
        root,
        version="v2",
        claim_identity=_identity(suffix="v2"),
        component_fingerprints=changed,
    )
    assert successor.predecessor_ref == root.identity_ref
    assert successor.changed_dimensions == (IdentityDimension.DATA,)
    assert successor.identity_ref != root.identity_ref
    assert root.version == "v1"


def test_decision_is_factory_only_and_all_authority_axes_are_derived() -> None:
    assert (
        "granted" not in inspect.signature(issue_claim_capability_decision).parameters
    )
    assert (
        "artifact_readiness"
        not in inspect.signature(issue_claim_capability_decision).parameters
    )
    with pytest.raises(RemediationContractError, match="factory-only"):
        ClaimCapabilityDecision()  # type: ignore[call-arg]

    decision = _issue()
    assert decision.granted is True
    assert decision.artifact_readiness is ArtifactReadinessAxis.EVIDENCE_CLOSED
    assert decision.evidence_branch is CapabilityEvidenceBranch.CONTRACT
    assert decision.scientific_semantics is CapabilityScientificSemantics.CONTRACT_ONLY
    assert decision.identification is CapabilityIdentification.NOT_APPLICABLE
    assert (
        decision.provenance_grade
        is CapabilityProvenanceGrade.CONTENT_ADDRESSED_ADJUDICATED
    )
    assert decision.allowed_use == ("validated_contract_consumption",)
    assert decision.non_relaxable_rules == NON_RELAXABLE_CAPABILITY_RULES
    assert decision.to_record()["granted"] is True
    with pytest.raises(FrozenInstanceError):
        decision.action = CapabilityAction.HOLD  # type: ignore[misc]


def test_raw_decision_builder_and_factory_token_are_not_module_surfaces() -> None:
    assert not hasattr(
        remediation_state_module, "_build_claim_capability_decision"
    )
    assert not hasattr(
        remediation_state_module, "_CAPABILITY_DECISION_FACTORY_TOKEN"
    )
    assert not hasattr(evidence_graph_module, "_build_claim_capability_decision")
    assert not hasattr(
        evidence_graph_module, "_mark_claim_capability_decision_issued"
    )
    assert not hasattr(evidence_graph_module, "_bind_claim_capability_issuer")
    assert not hasattr(
        evidence_graph_module,
        "_bind_claim_capability_decision_registration",
    )
    assert issue_claim_capability_decision.__closure__ is None
    assert remediation_state_module.ClaimCapabilityDecision is ClaimCapabilityDecision

    expected_public_contracts = {
        "ArtifactReadinessAxis",
        "CapabilityAction",
        "CapabilityBlocker",
        "CapabilityBlockerKind",
        "CapabilityEvidenceBranch",
        "CapabilityIdentification",
        "CapabilityOutcome",
        "CapabilityProvenanceGrade",
        "CapabilityScientificSemantics",
        "ClaimCapability",
        "ClaimCapabilityDecision",
        "IdentityDimension",
        "NON_RELAXABLE_CAPABILITY_RULES",
        "VersionedClaimIdentity",
    }
    assert expected_public_contracts <= set(remediation_state_module.__all__)

    with pytest.raises(RemediationContractError, match="factory-only"):
        ClaimCapabilityDecision(
            versioned_identity=_versioned(owner="BASS"),
            capability=ClaimCapability.FAMILY_IDENTIFICATION,
            action=CapabilityAction.GRANT,
            outcome=CapabilityOutcome.PASS,
            evidence_graph_ref="0" * 64,
            evidence_closure_ref="1" * 64,
            evidence_receipt_id="2" * 64,
            adjudication_receipt_ref="3" * 64,
        )


def test_raw_object_allocation_cannot_expose_a_trust_bearing_decision() -> None:
    issued = _issue()
    fabricated = object.__new__(ClaimCapabilityDecision)
    for field in fields(ClaimCapabilityDecision):
        object.__setattr__(
            fabricated,
            field.name,
            object.__getattribute__(issued, field.name),
        )

    with pytest.raises(RemediationContractError, match="validated evidence authority"):
        _ = fabricated.granted
    with pytest.raises(RemediationContractError, match="validated evidence authority"):
        fabricated.to_record()
    with pytest.raises(RemediationContractError, match="validated evidence authority"):
        vars(fabricated)

    impl = evidence_graph_module._issue_claim_capability_decision_impl
    leaked_markers = [
        cell.cell_contents
        for cell in (impl.__closure__ or ())
        if callable(cell.cell_contents)
        and getattr(cell.cell_contents, "__name__", "") == "mark_issued"
    ]
    assert len(leaked_markers) == 1
    with pytest.raises(RemediationContractError, match="issuer frame"):
        leaked_markers[0](fabricated)

    relabelled = _issue()
    object.__setattr__(
        relabelled,
        "capability",
        ClaimCapability.FAMILY_IDENTIFICATION,
    )
    with pytest.raises(RemediationContractError, match="exact authority context"):
        relabelled.to_record()


def test_identity_registration_is_only_a_misuse_guard() -> None:
    issued = _issue()
    copied = object.__new__(ClaimCapabilityDecision)
    for field in fields(ClaimCapabilityDecision):
        object.__setattr__(
            copied,
            field.name,
            object.__getattribute__(issued, field.name),
        )
    object.__setattr__(
        copied,
        "capability",
        ClaimCapability.FAMILY_IDENTIFICATION,
    )

    registration_guard = (
        evidence_graph_module._require_claim_capability_decision_registered
    )
    registries = [
        cell.cell_contents
        for cell in (registration_guard.__closure__ or ())
        if isinstance(cell.cell_contents, dict)
    ]
    assert len(registries) == 1
    identity = id(copied)
    registries[0][identity] = weakref.ref(copied)
    try:
        with pytest.raises(
            RemediationContractError,
            match="exact authority context",
        ):
            copied.to_record()
    finally:
        registries[0].pop(identity, None)


def test_validation_context_is_not_a_public_decision_field() -> None:
    issued = _issue()
    with pytest.raises(AttributeError, match="validation context is private"):
        _ = issued._validation_context


def test_action_outcome_derives_granted_without_caller_boolean() -> None:
    held = _issue(action=CapabilityAction.HOLD, outcome=CapabilityOutcome.ABSTAIN)
    downgraded = _issue(
        action=CapabilityAction.DOWNGRADE,
        outcome=CapabilityOutcome.PASS_WITH_CEILING,
    )
    assert held.granted is False
    assert downgraded.granted is False


@pytest.mark.parametrize(
    ("action", "outcome"),
    (
        (CapabilityAction.GRANT, CapabilityOutcome.PASS),
        (CapabilityAction.GRANT, CapabilityOutcome.PASS_WITH_CEILING),
        (CapabilityAction.HOLD, CapabilityOutcome.ABSTAIN),
        (CapabilityAction.HOLD, CapabilityOutcome.BLOCK),
        (CapabilityAction.REVOKE, CapabilityOutcome.BLOCK),
        (CapabilityAction.REVOKE, CapabilityOutcome.STALE_REPLACED),
        (CapabilityAction.DOWNGRADE, CapabilityOutcome.PASS_WITH_CEILING),
        (CapabilityAction.DOWNGRADE, CapabilityOutcome.ABSTAIN),
        (CapabilityAction.DOWNGRADE, CapabilityOutcome.BLOCK),
    ),
)
def test_every_non_supersession_action_outcome_pair_is_executable(
    action: CapabilityAction,
    outcome: CapabilityOutcome,
) -> None:
    decision = _issue(action=action, outcome=outcome)
    assert decision.action is action
    assert decision.outcome is outcome


@pytest.mark.parametrize(
    ("action", "outcome"),
    tuple(
        (action, outcome)
        for action in CapabilityAction
        for outcome in CapabilityOutcome
        if outcome
        not in {
            CapabilityAction.GRANT: {
                CapabilityOutcome.PASS,
                CapabilityOutcome.PASS_WITH_CEILING,
            },
            CapabilityAction.HOLD: {
                CapabilityOutcome.ABSTAIN,
                CapabilityOutcome.BLOCK,
            },
            CapabilityAction.SUPERSEDE: {
                CapabilityOutcome.PASS,
                CapabilityOutcome.PASS_WITH_CEILING,
            },
            CapabilityAction.REVOKE: {
                CapabilityOutcome.BLOCK,
                CapabilityOutcome.STALE_REPLACED,
            },
            CapabilityAction.DOWNGRADE: {
                CapabilityOutcome.PASS_WITH_CEILING,
                CapabilityOutcome.ABSTAIN,
                CapabilityOutcome.BLOCK,
            },
        }[action]
    ),
)
def test_every_forbidden_action_outcome_pair_fails_closed(
    action: CapabilityAction,
    outcome: CapabilityOutcome,
) -> None:
    with pytest.raises(RemediationContractError, match="invalid for action"):
        _issue(action=action, outcome=outcome)


@pytest.mark.parametrize(
    (
        "capability",
        "owner",
        "branch",
        "semantics",
        "identification",
        "allowed_use",
    ),
    (
        (
            ClaimCapability.CONTRACT_VALIDATED,
            "COMMON",
            CapabilityEvidenceBranch.CONTRACT,
            CapabilityScientificSemantics.CONTRACT_ONLY,
            CapabilityIdentification.NOT_APPLICABLE,
            "validated_contract_consumption",
        ),
        (
            ClaimCapability.THEOREM_PROVED_EXACT,
            "COMMON",
            CapabilityEvidenceBranch.THEOREM,
            CapabilityScientificSemantics.EXACT_THEOREM,
            CapabilityIdentification.NOT_APPLICABLE,
            "exact_theorem_reference",
        ),
        (
            ClaimCapability.THEOREM_PROVED_CONDITIONAL,
            "BASS",
            CapabilityEvidenceBranch.THEOREM,
            CapabilityScientificSemantics.CONDITIONAL_THEOREM,
            CapabilityIdentification.NOT_APPLICABLE,
            "conditional_theorem_reference",
        ),
        (
            ClaimCapability.METHOD_CALIBRATED,
            "MIO",
            CapabilityEvidenceBranch.METHOD,
            CapabilityScientificSemantics.CALIBRATED_METHOD,
            CapabilityIdentification.NOT_APPLICABLE,
            "calibrated_method_use",
        ),
        (
            ClaimCapability.DATA_ADMITTED,
            "OBSSTAT",
            CapabilityEvidenceBranch.DATA,
            CapabilityScientificSemantics.DATA_ADMISSION_ONLY,
            CapabilityIdentification.NOT_APPLICABLE,
            "admitted_data_input",
        ),
        (
            ClaimCapability.OBSERVED_DESCRIPTIVE,
            "OBSSTAT",
            CapabilityEvidenceBranch.OBSERVATION,
            CapabilityScientificSemantics.OBSERVED_DESCRIPTION,
            CapabilityIdentification.PARTIAL_IDENTIFICATION,
            "observed_descriptive_reporting",
        ),
        (
            ClaimCapability.OBSERVED_INFERENTIAL,
            "HTT",
            CapabilityEvidenceBranch.OBSERVATION,
            CapabilityScientificSemantics.OBSERVED_INFERENCE,
            CapabilityIdentification.PARTIAL_IDENTIFICATION,
            "htt_observed_inference",
        ),
        (
            ClaimCapability.SOURCE_SEPARATION_CANDIDATE,
            "HTT",
            CapabilityEvidenceBranch.SOURCE_SEPARATION,
            CapabilityScientificSemantics.SOURCE_SEPARATION_CANDIDATE,
            CapabilityIdentification.PARTIAL_IDENTIFICATION,
            "source_separation_candidate_only",
        ),
        (
            ClaimCapability.MORPHOLOGY_COMPATIBILITY,
            "BASS",
            CapabilityEvidenceBranch.MORPHOLOGY,
            CapabilityScientificSemantics.MORPHOLOGY_COMPATIBILITY,
            CapabilityIdentification.COMPATIBILITY_ONLY,
            "morphology_compatibility_only",
        ),
        (
            ClaimCapability.FAMILY_IDENTIFICATION,
            "BASS",
            CapabilityEvidenceBranch.FAMILY,
            CapabilityScientificSemantics.FAMILY_IDENTIFICATION,
            CapabilityIdentification.NATIVE_ATLAS_REQUIRED,
            "blocked_pre_native_atlas",
        ),
        (
            ClaimCapability.PUBLIC_RELEASE,
            "COMMON",
            CapabilityEvidenceBranch.RELEASE,
            CapabilityScientificSemantics.PUBLICATION,
            CapabilityIdentification.NOT_APPLICABLE,
            "receipt_scoped_public_release",
        ),
    ),
)
def test_every_capability_profile_is_bound_and_derived(
    capability: ClaimCapability,
    owner: str,
    branch: CapabilityEvidenceBranch,
    semantics: CapabilityScientificSemantics,
    identification: CapabilityIdentification,
    allowed_use: str,
) -> None:
    action = (
        CapabilityAction.HOLD
        if capability is ClaimCapability.FAMILY_IDENTIFICATION
        else CapabilityAction.GRANT
    )
    outcome = (
        CapabilityOutcome.BLOCK
        if capability is ClaimCapability.FAMILY_IDENTIFICATION
        else CapabilityOutcome.PASS
    )
    decision = _issue(
        versioned=_versioned(owner=owner),
        capability=capability,
        action=action,
        outcome=outcome,
    )
    assert decision.evidence_branch is branch
    assert decision.scientific_semantics is semantics
    assert decision.identification is identification
    assert decision.allowed_use == (allowed_use,)
    assert decision.claim_ceiling == _CAPABILITY_CEILINGS[capability]


@pytest.mark.parametrize(
    ("capability", "owner", "allowed"),
    tuple(
        (capability, owner, owner in _CAPABILITY_ALLOWED_OWNERS[capability])
        for capability in ClaimCapability
        for owner in _ACTIVE_TEST_OWNERS
    ),
)
def test_every_capability_owner_pair_matches_the_exact_firewall(
    capability: ClaimCapability,
    owner: str,
    allowed: bool,
) -> None:
    action = (
        CapabilityAction.HOLD
        if capability is ClaimCapability.FAMILY_IDENTIFICATION
        else CapabilityAction.GRANT
    )
    outcome = (
        CapabilityOutcome.BLOCK
        if capability is ClaimCapability.FAMILY_IDENTIFICATION
        else CapabilityOutcome.PASS
    )
    if allowed:
        decision = _issue(
            versioned=_versioned(owner=owner),
            capability=capability,
            action=action,
            outcome=outcome,
        )
        assert decision.versioned_identity.owner == owner
    else:
        with pytest.raises(EvidenceGraphError, match="cannot receive"):
            _issue(
                versioned=_versioned(owner=owner),
                capability=capability,
                action=action,
                outcome=outcome,
            )


def test_capability_request_must_match_the_adjudicated_claim_node() -> None:
    versioned = _versioned()
    graph, claim, _nodes = _graph(versioned)
    evidence_receipt, adjudication, registry = _receipts(graph, claim, versioned)
    with pytest.raises(EvidenceGraphError, match="capability_binding"):
        issue_claim_capability_decision(
            graph,
            versioned_identity=versioned,
            evidence_receipt=evidence_receipt,
            adjudication_receipt=adjudication,
            registry=registry,
            capability=ClaimCapability.PUBLIC_RELEASE,
            action=CapabilityAction.GRANT,
            outcome=CapabilityOutcome.PASS,
            evaluated_at=EVALUATED_AT,
        )


def test_positive_capability_cannot_come_from_terminal_negative_science() -> None:
    with pytest.raises(EvidenceGraphError, match="positive terminal adjudication"):
        _issue(science=ScientificStatus.FALSIFIED)


def test_blockers_affect_only_the_named_capability() -> None:
    unrelated = CapabilityBlocker(
        blocker_id="native-atlas",
        kind=CapabilityBlockerKind.PHYSICAL_HARD,
        affected_capabilities=(ClaimCapability.FAMILY_IDENTIFICATION,),
        evidence_ref=_digest("native-atlas-blocker"),
    )
    assert _issue(blockers=(unrelated,)).granted is True

    direct = CapabilityBlocker(
        blocker_id="contract-evidence",
        kind=CapabilityBlockerKind.EVIDENCE_CONDITIONAL,
        affected_capabilities=(ClaimCapability.CONTRACT_VALIDATED,),
        evidence_ref=_digest("contract-blocker"),
    )
    with pytest.raises(EvidenceGraphError, match="affecting this capability"):
        _issue(blockers=(direct,))


def test_owner_firewall_and_native_family_gate_are_non_relaxable() -> None:
    with pytest.raises(EvidenceGraphError, match="cannot receive"):
        _issue(
            versioned=_versioned(owner="MIO"),
            capability=ClaimCapability.OBSERVED_INFERENTIAL,
        )
    with pytest.raises(
        EvidenceGraphError, match="blocked before an admitted native atlas"
    ):
        _issue(
            versioned=_versioned(owner="BASS"),
            capability=ClaimCapability.FAMILY_IDENTIFICATION,
        )


def test_missing_non_relaxable_rule_is_rejected() -> None:
    with pytest.raises(EvidenceGraphError, match="every non-relaxable"):
        _issue(rules=NON_RELAXABLE_CAPABILITY_RULES[:-1])


def test_adjudication_must_match_exact_claim_identity() -> None:
    versioned = _versioned()
    graph, claim, _nodes = _graph(versioned)
    evidence_receipt, adjudication, registry = _receipts(graph, claim, versioned)
    wrong = replace(
        adjudication,
        accepted_claims=(
            AdjudicatedClaim(
                claim_id=versioned.claim_identity.claim_id,
                identity_fingerprint=_digest("wrong-identity"),
                scientific_status=ScientificStatus.RESCUED,
            ),
        ),
        attestation="pending",
    )
    adjudicator = registry.resolve(
        "pr277-adjudicator",
        role="adjudicator",
        scope=SCOPE,
        at=ISSUED_AT,
    )
    wrong = replace(
        wrong,
        attestation=hashlib.sha256(
            adjudicator.identity_fingerprint.encode("ascii")
            + wrong.canonical_attestation_payload()
        ).hexdigest(),
    )
    with pytest.raises(EvidenceGraphError, match="exact claim identity"):
        issue_claim_capability_decision(
            graph,
            versioned_identity=versioned,
            evidence_receipt=evidence_receipt,
            adjudication_receipt=wrong,
            registry=registry,
            capability=ClaimCapability.CONTRACT_VALIDATED,
            action=CapabilityAction.GRANT,
            outcome=CapabilityOutcome.PASS,
            evaluated_at=EVALUATED_AT,
        )


def test_typed_lifecycle_edges_round_trip_and_propagate_by_capability_only() -> None:
    versioned = _versioned()
    base_graph, _claim, nodes = _graph(versioned)
    lifecycle = EvidenceEdge(
        EvidenceEdgeKind.INVALIDATES_DATA,
        nodes["input"].node_ref,
        nodes["consumer"].node_ref,
        {
            "affected_capabilities": [ClaimCapability.METHOD_CALIBRATED.value],
            "reason_ref": _digest("changed-data"),
        },
    )
    graph = EvidenceGraph(nodes=base_graph.nodes, edges=(*base_graph.edges, lifecycle))
    round_trip = EvidenceGraph.from_record(graph.to_record())
    assert round_trip.graph_ref == graph.graph_ref
    assert lifecycle_invalidation_dimension(lifecycle.kind) is IdentityDimension.DATA
    assert typed_invalidation_targets(
        graph,
        source_ref=nodes["input"].node_ref,
        capability=ClaimCapability.METHOD_CALIBRATED,
    ) == (nodes["consumer"].node_ref,)
    assert (
        typed_invalidation_targets(
            graph,
            source_ref=nodes["input"].node_ref,
            capability=ClaimCapability.THEOREM_PROVED_EXACT,
        )
        == ()
    )
    assert lifecycle.edge_ref not in graph.closure(_claim.node_ref).edge_refs


def test_lifecycle_edge_rejects_untyped_or_duplicate_capability_scope() -> None:
    graph, _claim, nodes = _graph(_versioned())
    with pytest.raises(EvidenceGraphError, match="non-empty and unique"):
        EvidenceEdge(
            EvidenceEdgeKind.REQUIRES_REEXECUTION,
            nodes["input"].node_ref,
            nodes["producer"].node_ref,
            {
                "affected_capabilities": [
                    ClaimCapability.METHOD_CALIBRATED.value,
                    ClaimCapability.METHOD_CALIBRATED.value,
                ],
                "reason_ref": _digest("duplicate"),
            },
        )
    with pytest.raises(EvidenceGraphError, match="missing fields"):
        EvidenceEdge(
            EvidenceEdgeKind.INVALIDATES_DATA,
            nodes["input"].node_ref,
            nodes["consumer"].node_ref,
            {"reason_ref": _digest("missing-capability")},
        )
    assert graph.graph_ref


def test_graph_lifecycle_invalidation_blocks_grant_without_caller_blocker() -> None:
    versioned = _versioned(owner="MIO")
    base_graph, claim, nodes = _graph(
        versioned,
        capability=ClaimCapability.METHOD_CALIBRATED,
    )
    invalidation = EvidenceEdge(
        EvidenceEdgeKind.INVALIDATES_DATA,
        nodes["input"].node_ref,
        nodes["consumer"].node_ref,
        {
            "affected_capabilities": [ClaimCapability.METHOD_CALIBRATED.value],
            "reason_ref": _digest("active-method-data-invalidation"),
        },
    )
    graph = EvidenceGraph(
        nodes=base_graph.nodes,
        edges=(*base_graph.edges, invalidation),
    )
    evidence_receipt, adjudication, registry = _receipts(graph, claim, versioned)
    with pytest.raises(EvidenceGraphError, match="affecting this capability"):
        issue_claim_capability_decision(
            graph,
            versioned_identity=versioned,
            evidence_receipt=evidence_receipt,
            adjudication_receipt=adjudication,
            registry=registry,
            capability=ClaimCapability.METHOD_CALIBRATED,
            action=CapabilityAction.GRANT,
            outcome=CapabilityOutcome.PASS,
            blockers=(),
            evaluated_at=EVALUATED_AT,
        )

    held_base, held_claim, held_nodes = _graph(
        versioned,
        capability=ClaimCapability.METHOD_CALIBRATED,
        action=CapabilityAction.HOLD,
        outcome=CapabilityOutcome.BLOCK,
    )
    held_invalidation = EvidenceEdge(
        EvidenceEdgeKind.INVALIDATES_DATA,
        held_nodes["input"].node_ref,
        held_nodes["consumer"].node_ref,
        {
            "affected_capabilities": [ClaimCapability.METHOD_CALIBRATED.value],
            "reason_ref": _digest("active-method-data-invalidation"),
        },
    )
    held_graph = EvidenceGraph(
        nodes=held_base.nodes,
        edges=(*held_base.edges, held_invalidation),
    )
    held_receipt, held_adjudication, held_registry = _receipts(
        held_graph, held_claim, versioned
    )
    decision = issue_claim_capability_decision(
        held_graph,
        versioned_identity=versioned,
        evidence_receipt=held_receipt,
        adjudication_receipt=held_adjudication,
        registry=held_registry,
        capability=ClaimCapability.METHOD_CALIBRATED,
        action=CapabilityAction.HOLD,
        outcome=CapabilityOutcome.BLOCK,
        blockers=(),
        evaluated_at=EVALUATED_AT,
    )
    assert decision.artifact_readiness is ArtifactReadinessAxis.EVIDENCE_BLOCKED
    assert len(decision.blockers) == 1
    assert decision.blockers[0].evidence_ref == held_invalidation.edge_ref


@pytest.mark.parametrize(
    "outcome",
    (CapabilityOutcome.PASS, CapabilityOutcome.PASS_WITH_CEILING),
)
def test_successor_requires_exact_supersession_edge_and_preserves_predecessor(
    outcome: CapabilityOutcome,
) -> None:
    predecessor = _versioned()
    changed = dict(predecessor.component_fingerprints)
    changed[IdentityDimension.ESTIMAND] = _digest("ESTIMAND:v2")
    successor = VersionedClaimIdentity.successor(
        predecessor,
        version="v2",
        claim_identity=_identity(suffix="v2"),
        component_fingerprints=changed,
    )
    graph_without_edge, claim, _nodes = _graph(
        successor,
        action=CapabilityAction.SUPERSEDE,
        outcome=outcome,
    )
    evidence_receipt, adjudication, registry = _receipts(
        graph_without_edge, claim, successor
    )
    with pytest.raises(EvidenceGraphError, match="SUPERSEDED_BY"):
        issue_claim_capability_decision(
            graph_without_edge,
            versioned_identity=successor,
            evidence_receipt=evidence_receipt,
            adjudication_receipt=adjudication,
            registry=registry,
            capability=ClaimCapability.CONTRACT_VALIDATED,
            action=CapabilityAction.SUPERSEDE,
            outcome=outcome,
            evaluated_at=EVALUATED_AT,
        )

    old_claim = _node(
        EvidenceNodeKind.CLAIM,
        "claim:historical-predecessor",
        science=ScientificStatus.FALSIFIED,
        content_sha256=predecessor.identity_ref,
    )
    edge = EvidenceEdge(
        EvidenceEdgeKind.SUPERSEDED_BY,
        old_claim.node_ref,
        claim.node_ref,
        {
            "affected_capabilities": [ClaimCapability.CONTRACT_VALIDATED.value],
            "reason_ref": _digest("successor-reason"),
            "changed_dimensions": [IdentityDimension.ESTIMAND.value],
        },
    )
    graph = EvidenceGraph(
        nodes=(*graph_without_edge.nodes, old_claim),
        edges=(*graph_without_edge.edges, edge),
    )
    evidence_receipt, adjudication, registry = _receipts(graph, claim, successor)
    decision = issue_claim_capability_decision(
        graph,
        versioned_identity=successor,
        evidence_receipt=evidence_receipt,
        adjudication_receipt=adjudication,
        registry=registry,
        capability=ClaimCapability.CONTRACT_VALIDATED,
        action=CapabilityAction.SUPERSEDE,
        outcome=outcome,
        evaluated_at=EVALUATED_AT,
    )
    assert decision.granted is True
    assert successor.predecessor_ref == predecessor.identity_ref
    assert old_claim.axes.scientific_status is ScientificStatus.FALSIFIED


def test_decision_record_is_content_addressed_and_json_safe() -> None:
    decision = _issue()
    record = decision.to_record()
    assert record["decision_ref"] == decision.decision_ref
    assert len(decision.decision_ref) == 64
    json.dumps(record, sort_keys=True, allow_nan=False)


def test_identity_and_blocker_input_order_do_not_change_content_addresses() -> None:
    forward_components = _components()
    reverse_components = dict(reversed(tuple(forward_components.items())))
    forward_identity = VersionedClaimIdentity.root(
        version="v1",
        owner="COMMON",
        claim_identity=_identity(),
        component_fingerprints=forward_components,
    )
    reverse_identity = VersionedClaimIdentity.root(
        version="v1",
        owner="COMMON",
        claim_identity=_identity(),
        component_fingerprints=reverse_components,
    )
    assert forward_identity.identity_ref == reverse_identity.identity_ref

    first = CapabilityBlocker(
        blocker_id="method-only",
        kind=CapabilityBlockerKind.EVIDENCE_CONDITIONAL,
        affected_capabilities=(ClaimCapability.METHOD_CALIBRATED,),
        evidence_ref=_digest("method-only"),
    )
    second = CapabilityBlocker(
        blocker_id="native-only",
        kind=CapabilityBlockerKind.PHYSICAL_HARD,
        affected_capabilities=(ClaimCapability.FAMILY_IDENTIFICATION,),
        evidence_ref=_digest("native-only"),
    )
    forward = _issue(blockers=(first, second))
    reverse = _issue(blockers=(second, first))
    assert forward.decision_ref == reverse.decision_ref
    assert tuple(item.blocker_id for item in forward.blockers) == (
        "method-only",
        "native-only",
    )
