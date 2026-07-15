from __future__ import annotations

import hashlib
import hmac
from dataclasses import replace
from datetime import UTC, datetime
from itertools import product
from typing import Callable

import pytest

from common.remediation_state import (
    AdjudicatedClaim,
    AdjudicationReceipt,
    AuthorityError,
    AuthorityRegistry,
    CanonicalClaimTier,
    ClaimIdentity,
    ClaimLevel,
    ClaimLevelScheme,
    DependencyEvidence,
    DependencyMode,
    ExecutionResolution,
    ExternalDeliveryReceipt,
    OrchestrationState,
    PrincipalRecord,
    RemediationContractError,
    RemediationState,
    ScientificStatus,
    assert_distinct_author_adjudicator,
    canonical_claim_identity_payload,
    claim_identity_fingerprint,
    compare_claim_levels,
    is_negative_execution_receipt,
    resolve_dependency,
    validate_active_owner,
    validate_scientific_transition,
)


SPEC_FINGERPRINT = "b5bf554526fe36a264888926478627e0a94f5b00cdfd92627c9c3ebef82da57e"
AT = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
_VERIFIER_KEYS = {
    "principal:adjudicator": b"test-only-adjudicator-key",
    "principal:internal-reviewer": b"test-only-internal-reviewer-key",
    "principal:external-provider": b"test-only-external-provider-key",
    "principal:internal-provider": b"test-only-internal-provider-key",
}


def _attestation(
    principal_id: str,
    payload: bytes,
) -> str:
    return hmac.new(_VERIFIER_KEYS[principal_id], payload, hashlib.sha256).hexdigest()


def _test_receipt_verifier(
    principal: PrincipalRecord,
    payload: bytes,
    attestation: str,
) -> bool:
    key = _VERIFIER_KEYS.get(principal.principal_id)
    if key is None:
        return False
    expected = hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, attestation)


def _verifiers() -> dict[
    str, Callable[[PrincipalRecord, bytes, str], bool]
]:
    return {"test_hmac_sha256": _test_receipt_verifier}


def _claim_record() -> dict[str, object]:
    return {
        "claim_id": "GOV-PR119-DAG-INTAKE",
        "claim_text": (
            "PR-119 through PR-166 are intaken as governance records while the "
            "completed PR-000 through PR-118 baseline and authoritative rescued "
            "count of zero are preserved."
        ),
        "quantifier": "exactly_48_cards_once_each",
        "estimand": "not_applicable_governance",
        "target_population": "active_pr_dag_and_remediation_records",
        "domain": "PR-119_through_PR-166_only",
        "frame": "not_applicable",
        "perturbative_order": "not_applicable",
        "units": "not_applicable",
        "data_release": "not_applicable",
        "sky_support_mask_selection": "not_applicable",
        "statistic_pipeline": "codex_dag_intake_and_remediation_state_machine",
        "transfer_source": "none",
        "nuisance_prior_null_multiplicity": "not_applicable",
        "claim_level_scheme": "not_applicable_governance_v1",
        "claim_level": "NOT_APPLICABLE",
        "claim_tier_ceiling": "exploratory",
        "canonicalization": "sorted_compact_json_utf8_v1",
        "identity_fingerprint": SPEC_FINGERPRINT,
    }


def _principal(
    principal_id: str,
    fingerprint_character: str,
    *,
    aliases: tuple[str, ...] = (),
    roles: tuple[str, ...] = ("author",),
    scopes: tuple[str, ...] = ("PR-119",),
    revoked: bool = False,
    valid_from: str = "2026-01-01T00:00:00+00:00",
    valid_until: str = "2027-01-01T00:00:00+00:00",
    independence_class: str = "correlated_internal_non_author_review",
) -> PrincipalRecord:
    return PrincipalRecord(
        principal_id=principal_id,
        identity_fingerprint=fingerprint_character * 64,
        aliases=aliases,
        allowed_roles=roles,
        allowed_scopes=scopes,
        independence_class=independence_class,
        valid_from=valid_from,
        valid_until=valid_until,
        revoked=revoked,
        verifier="test_hmac_sha256",
    )


def _dependency_registry(*, include_promotion_role: bool = True) -> AuthorityRegistry:
    adjudicator_roles = ("adjudicator",)
    if include_promotion_role:
        adjudicator_roles += ("scientific_status_promoter",)
    return AuthorityRegistry(
        (
            _principal(
                "principal:author",
                "a",
                aliases=("author-alias",),
                roles=("author",),
            ),
            _principal(
                "principal:adjudicator",
                "b",
                aliases=("adjudicator-alias",),
                roles=adjudicator_roles,
                independence_class=(
                    "independent_external"
                    if include_promotion_role
                    else "correlated_internal_non_author_review"
                ),
            ),
            _principal(
                "principal:external-provider",
                "c",
                aliases=("provider-alias",),
                roles=("external_receipt_provider",),
                scopes=("PR-159",),
                independence_class="independent_external",
            ),
        ),
        verifiers=_verifiers(),
    )


def _pr119_bootstrap_registry() -> AuthorityRegistry:
    """Approved bootstrap: correlated internal roles, no science promoter."""

    return AuthorityRegistry(
        (
            _principal(
                "principal:author",
                "a",
                aliases=("author-alias",),
                roles=("author",),
            ),
            _principal(
                "principal:internal-reviewer",
                "b",
                aliases=("adjudicator-alias",),
                roles=("adjudicator",),
            ),
        ),
        verifiers=_verifiers(),
    )


def _claim_outcome(
    status: ScientificStatus = ScientificStatus.RESCUED,
    *,
    fingerprint: str = SPEC_FINGERPRINT,
    claim_id: str = "GOV-PR119-DAG-INTAKE",
) -> AdjudicatedClaim:
    return AdjudicatedClaim(
        claim_id=claim_id,
        identity_fingerprint=fingerprint,
        scientific_status=status,
    )


def _adjudication_receipt(
    status: ScientificStatus = ScientificStatus.RESCUED,
    *,
    accepted_claims: tuple[AdjudicatedClaim, ...] | None = None,
    scope: str = "PR-119",
    author: str = "author-alias",
    adjudicator: str = "adjudicator-alias",
    author_fingerprint: str = "a" * 64,
    adjudicator_fingerprint: str = "b" * 64,
    signer_id: str = "principal:adjudicator",
) -> AdjudicationReceipt:
    claims = (
        (_claim_outcome(status),)
        if accepted_claims is None
        else accepted_claims
    )
    draft = AdjudicationReceipt(
        receipt_id=f"adjudication:{status.value}",
        author=author,
        author_identity_fingerprint=author_fingerprint,
        adjudicator=adjudicator,
        adjudicator_identity_fingerprint=adjudicator_fingerprint,
        scope=scope,
        accepted_claims=claims,
        issued_at=AT,
        attestation="unsigned",
    )
    return replace(
        draft,
        attestation=_attestation(signer_id, draft.canonical_attestation_payload()),
    )


def _external_receipt(
    *,
    provider: str = "provider-alias",
    provider_fingerprint: str = "c" * 64,
    scope: str = "PR-159",
) -> ExternalDeliveryReceipt:
    draft = ExternalDeliveryReceipt(
        receipt_id="external:native-lowell:delivery-001",
        provider=provider,
        provider_identity_fingerprint=provider_fingerprint,
        scope=scope,
        artifact_fingerprint="d" * 64,
        issued_at=AT,
        attestation="unsigned",
    )
    return replace(
        draft,
        attestation=_attestation(
            "principal:external-provider",
            draft.canonical_attestation_payload(),
        ),
    )


def _state_at_scientific_status(status: ScientificStatus) -> RemediationState:
    state = RemediationState(OrchestrationState.IN_PROGRESS)
    if status is ScientificStatus.OPEN:
        return state
    state = state.transition_scientific(ScientificStatus.IN_REMEDIATION)
    if status is ScientificStatus.IN_REMEDIATION:
        return state
    state = state.transition_scientific(ScientificStatus.EVIDENCE_READY)
    if status is ScientificStatus.EVIDENCE_READY:
        return state
    state = state.transition_scientific(ScientificStatus.ADJUDICATION_PENDING)
    if status is ScientificStatus.ADJUDICATION_PENDING:
        return state
    return state.transition_scientific(
        status,
        registry=_dependency_registry(),
        attestation=_adjudication_receipt(status),
        claim_id="GOV-PR119-DAG-INTAKE",
        claim_identity_fingerprint=SPEC_FINGERPRINT,
        scope="PR-119",
        at=AT,
    )


def test_pr119_claim_identity_matches_frozen_spec_fingerprint() -> None:
    identity = ClaimIdentity.from_record(_claim_record())

    assert identity.identity_fingerprint == SPEC_FINGERPRINT
    assert claim_identity_fingerprint(identity) == SPEC_FINGERPRINT
    assert claim_identity_fingerprint(_claim_record()) == SPEC_FINGERPRINT
    assert identity.to_record() == _claim_record()
    assert b'"canonicalization"' not in canonical_claim_identity_payload(identity)
    assert b'"identity_fingerprint"' not in canonical_claim_identity_payload(identity)


def test_claim_identity_fingerprint_changes_for_every_semantic_field() -> None:
    identity = ClaimIdentity.from_record(_claim_record())
    ordinary_fields = (
        "claim_id",
        "claim_text",
        "quantifier",
        "estimand",
        "target_population",
        "domain",
        "frame",
        "perturbative_order",
        "units",
        "data_release",
        "sky_support_mask_selection",
        "statistic_pipeline",
        "transfer_source",
        "nuisance_prior_null_multiplicity",
        "claim_tier_ceiling",
    )

    for field_name in ordinary_fields:
        replacement = (
            CanonicalClaimTier.DIAGNOSTIC_ONLY
            if field_name == "claim_tier_ceiling"
            else f"changed-{field_name}"
        )
        changed = replace(identity, **{field_name: replacement})
        assert changed.identity_fingerprint != identity.identity_fingerprint

    changed_level = replace(
        identity,
        claim_level_scheme=ClaimLevelScheme.FAMILY_GATE_V1,
        claim_level="C0",
    )
    assert changed_level.identity_fingerprint != identity.identity_fingerprint


def test_claim_identity_rejects_tampering_and_unknown_fields() -> None:
    tampered = _claim_record()
    tampered["claim_text"] = "different claim"
    with pytest.raises(RemediationContractError, match="fingerprint does not match"):
        ClaimIdentity.from_record(tampered)

    unknown = _claim_record()
    unknown["unreviewed_semantics"] = "silent drift"
    with pytest.raises(RemediationContractError, match="unknown fields"):
        ClaimIdentity.from_record(unknown)

    unsupported = _claim_record()
    unsupported.pop("identity_fingerprint")
    unsupported["canonicalization"] = "platform_default_json"
    with pytest.raises(RemediationContractError, match="unsupported.*canonicalization"):
        ClaimIdentity.from_record(unsupported)

    whitespace_drift = _claim_record()
    whitespace_drift["claim_text"] = f" {whitespace_drift['claim_text']}"
    with pytest.raises(RemediationContractError, match="whitespace"):
        ClaimIdentity.from_record(whitespace_drift)


@pytest.mark.parametrize(
    ("scheme", "level"),
    [
        (ClaimLevelScheme.FAMILY_GATE_V1, "C0"),
        (ClaimLevelScheme.FAMILY_GATE_V1, "C6"),
        (ClaimLevelScheme.ROADMAP_RESCUE_V1, "C3"),
        (ClaimLevelScheme.NOT_APPLICABLE_GOVERNANCE_V1, "NOT_APPLICABLE"),
    ],
)
def test_claim_levels_require_a_versioned_scheme(
    scheme: ClaimLevelScheme, level: str
) -> None:
    claim_level = ClaimLevel(scheme, level)

    assert claim_level.scheme is scheme
    assert claim_level.level == level


def test_bare_or_scheme_incompatible_claim_levels_are_rejected() -> None:
    with pytest.raises(RemediationContractError, match="mapping with scheme and level"):
        ClaimLevel.from_record("C1")  # type: ignore[arg-type]
    with pytest.raises(RemediationContractError, match="missing required"):
        ClaimLevel.from_record({"level": "C1"})
    with pytest.raises(RemediationContractError, match="unknown fields"):
        ClaimLevel.from_record(
            {"scheme": "family_gate_v1", "level": "C1", "map_to": "C1"}
        )
    with pytest.raises(RemediationContractError, match="invalid for scheme"):
        ClaimLevel(ClaimLevelScheme.NOT_APPLICABLE_GOVERNANCE_V1, "C1")
    with pytest.raises(RemediationContractError, match="invalid for scheme"):
        ClaimLevel(ClaimLevelScheme.FAMILY_GATE_V1, "C1-K5")
    with pytest.raises(RemediationContractError, match="whitespace"):
        ClaimLevel(ClaimLevelScheme.FAMILY_GATE_V1, " C1")


def test_cross_scheme_claim_level_comparison_and_mapping_are_forbidden() -> None:
    family_c1 = ClaimLevel(ClaimLevelScheme.FAMILY_GATE_V1, "C1")
    roadmap_c1 = ClaimLevel(ClaimLevelScheme.ROADMAP_RESCUE_V1, "C1")

    with pytest.raises(RemediationContractError, match="cross-scheme"):
        compare_claim_levels(family_c1, roadmap_c1)
    with pytest.raises(RemediationContractError, match="cross-scheme"):
        family_c1 == roadmap_c1
    with pytest.raises(RemediationContractError, match="cross-scheme"):
        family_c1 != roadmap_c1
    assert compare_claim_levels(
        family_c1, ClaimLevel(ClaimLevelScheme.FAMILY_GATE_V1, "C2")
    ) == -1


def test_canonical_claim_tiers_are_explicitly_unordered() -> None:
    with pytest.raises(RemediationContractError, match="unordered"):
        CanonicalClaimTier.EXPLORATORY < CanonicalClaimTier.VALIDATED
    with pytest.raises(RemediationContractError, match="unordered"):
        CanonicalClaimTier.BLOCKED >= CanonicalClaimTier.CONDITIONAL
    with pytest.raises(RemediationContractError, match="unordered"):
        "conditional" < CanonicalClaimTier.VALIDATED


def test_orchestration_and_execution_resolution_have_an_iff_contract() -> None:
    for orchestration, resolution in product(
        OrchestrationState, (None, *tuple(ExecutionResolution))
    ):
        is_valid = (orchestration is OrchestrationState.TERMINAL) == (
            resolution is not None
        )
        if is_valid:
            state = RemediationState(
                orchestration_state=orchestration,
                execution_resolution=resolution,
            )
            assert state.scientific_status is ScientificStatus.OPEN
        else:
            with pytest.raises(RemediationContractError):
                RemediationState(
                    orchestration_state=orchestration,
                    execution_resolution=resolution,
                )


@pytest.mark.parametrize("scientific_status", list(ScientificStatus))
@pytest.mark.parametrize("resolution", list(ExecutionResolution))
def test_execution_resolution_never_changes_scientific_status(
    scientific_status: ScientificStatus,
    resolution: ExecutionResolution,
) -> None:
    initial = _state_at_scientific_status(scientific_status)

    terminal = initial.resolve_execution(resolution)

    assert terminal.orchestration_state is OrchestrationState.TERMINAL
    assert terminal.execution_resolution is resolution
    assert terminal.scientific_status is scientific_status


@pytest.mark.parametrize("resolution", list(ExecutionResolution))
def test_requires_success_is_never_scientific_promotion(
    resolution: ExecutionResolution,
) -> None:
    decision = resolve_dependency(
        DependencyMode.REQUIRES_SUCCESS,
        DependencyEvidence(execution_resolution=resolution),
    )

    assert decision.satisfied is (
        resolution is ExecutionResolution.COMPLETED_SUCCESS
    )
    assert decision.scientific_input_allowed is False
    assert decision.accepted_claim_ids == ()


@pytest.mark.parametrize("resolution", list(ExecutionResolution))
def test_terminal_receipts_are_aggregation_only(
    resolution: ExecutionResolution,
) -> None:
    decision = resolve_dependency(
        DependencyMode.REQUIRES_TERMINAL_RECEIPT,
        DependencyEvidence(execution_resolution=resolution),
    )

    assert decision.satisfied is True
    assert decision.scientific_input_allowed is False
    assert decision.allowed_use == "adjudication_aggregation_only"


@pytest.mark.parametrize(
    "resolution",
    [
        ExecutionResolution.COMPLETED_FAILED_WITH_RECEIPT,
        ExecutionResolution.BLOCKED_WITH_RECEIPT,
        ExecutionResolution.ABANDONED_WITH_RECEIPT,
    ],
)
def test_negative_receipts_cannot_be_imputed_as_success(
    resolution: ExecutionResolution,
) -> None:
    assert is_negative_execution_receipt(resolution) is True
    assert resolve_dependency(
        DependencyMode.REQUIRES_SUCCESS,
        DependencyEvidence(execution_resolution=resolution),
    ).satisfied is False
    assert resolve_dependency(
        DependencyMode.REQUIRES_TERMINAL_RECEIPT,
        DependencyEvidence(execution_resolution=resolution),
    ).allowed_use == "adjudication_aggregation_only"


def test_missing_external_receipt_is_dormant_and_never_scientific_input() -> None:
    registry = _dependency_registry()
    missing = resolve_dependency(
        DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
        DependencyEvidence(),
    )
    present = resolve_dependency(
        DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
        DependencyEvidence(external_receipt=_external_receipt()),
        registry=registry,
        scope="PR-159",
        at=AT,
    )

    assert missing.satisfied is False
    assert missing.missing_state is OrchestrationState.DORMANT_EXTERNAL
    assert present.satisfied is True
    assert present.missing_state is None
    assert missing.scientific_input_allowed is False
    assert present.scientific_input_allowed is False


def test_only_authorized_adjudicated_subset_is_scientific_input() -> None:
    registry = _dependency_registry()
    unauthorized = resolve_dependency(
        DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
        DependencyEvidence(),
    )
    empty_receipt = _adjudication_receipt(accepted_claims=())
    empty_adjudication = resolve_dependency(
        DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
        DependencyEvidence(adjudication_receipt=empty_receipt),
        registry=registry,
        scope="PR-119",
        at=AT,
    )
    claims = (
        _claim_outcome(
            ScientificStatus.FALSIFIED,
            fingerprint="e" * 64,
            claim_id="finding:C1-K5",
        ),
        _claim_outcome(
            ScientificStatus.RESCUED,
            fingerprint="f" * 64,
            claim_id="finding:C1-M4",
        ),
    )
    accepted = resolve_dependency(
        DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
        DependencyEvidence(
            adjudication_receipt=_adjudication_receipt(accepted_claims=claims),
        ),
        registry=registry,
        scope="PR-119",
        at=AT,
    )

    assert unauthorized.satisfied is False
    assert unauthorized.accepted_claim_ids == ()
    assert empty_adjudication.satisfied is True
    assert empty_adjudication.scientific_input_allowed is False
    assert accepted.satisfied is True
    assert accepted.scientific_input_allowed is True
    assert accepted.accepted_claim_ids == ("finding:C1-K5", "finding:C1-M4")
    assert accepted.accepted_claims[0].scientific_status is ScientificStatus.FALSIFIED


def test_dependency_evidence_is_typed_and_default_deny() -> None:
    with pytest.raises(TypeError, match="DependencyEvidence"):
        resolve_dependency(
            DependencyMode.REQUIRES_SUCCESS,
            object(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="unexpected keyword"):
        DependencyEvidence(  # type: ignore[call-arg]
            authenticated_external_receipt=True
        )
    with pytest.raises(TypeError, match="unexpected keyword"):
        DependencyEvidence(  # type: ignore[call-arg]
            authorized_non_author_adjudication=True
        )
    with pytest.raises(RemediationContractError, match="ExternalDeliveryReceipt"):
        DependencyEvidence(external_receipt=object())  # type: ignore[arg-type]


def test_fabricated_or_unbound_receipts_fail_closed() -> None:
    registry = _dependency_registry()
    external_evidence = DependencyEvidence(external_receipt=_external_receipt())
    with pytest.raises(AuthorityError, match="registry and exact scope"):
        resolve_dependency(
            DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
            external_evidence,
        )
    with pytest.raises(AuthorityError, match="scope"):
        resolve_dependency(
            DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
            external_evidence,
            registry=registry,
            scope="PR-160",
            at=AT,
        )

    forged_provider = DependencyEvidence(
        external_receipt=_external_receipt(provider_fingerprint="9" * 64)
    )
    with pytest.raises(AuthorityError, match="fingerprint mismatch"):
        resolve_dependency(
            DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
            forged_provider,
            registry=registry,
            scope="PR-159",
            at=AT,
        )

    tampered_external = DependencyEvidence(
        external_receipt=replace(
            _external_receipt(), artifact_fingerprint="e" * 64
        )
    )
    with pytest.raises(AuthorityError, match="attestation verification failed"):
        resolve_dependency(
            DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
            tampered_external,
            registry=registry,
            scope="PR-159",
            at=AT,
        )

    internal_provider_registry = AuthorityRegistry(
        (
            _principal(
                "principal:internal-provider",
                "c",
                aliases=("provider-alias",),
                roles=("external_receipt_provider",),
                scopes=("PR-159",),
            ),
        ),
        verifiers=_verifiers(),
    )
    with pytest.raises(AuthorityError, match="independently authenticated external"):
        resolve_dependency(
            DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
            external_evidence,
            registry=internal_provider_registry,
            scope="PR-159",
            at=AT,
        )

    forged_adjudication = DependencyEvidence(
        adjudication_receipt=_adjudication_receipt(
            adjudicator_fingerprint="9" * 64
        )
    )
    with pytest.raises(AuthorityError, match="fingerprint mismatch"):
        resolve_dependency(
            DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
            forged_adjudication,
            registry=registry,
            scope="PR-119",
            at=AT,
        )

    tampered_adjudication = DependencyEvidence(
        adjudication_receipt=replace(
            _adjudication_receipt(),
            accepted_claims=(
                _claim_outcome(ScientificStatus.FALSIFIED),
            ),
        )
    )
    with pytest.raises(AuthorityError, match="attestation verification failed"):
        resolve_dependency(
            DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
            tampered_adjudication,
            registry=registry,
            scope="PR-119",
            at=AT,
        )


def test_registry_resolves_alias_to_canonical_principal_with_exact_scope() -> None:
    principal = _principal(
        "principal:author",
        "a",
        aliases=("author-alias",),
        roles=("author",),
    )
    registry = AuthorityRegistry((principal,))

    resolved = registry.resolve(
        "author-alias", role="author", scope="PR-119", at=AT
    )

    assert registry.default_deny is True
    assert resolved.principal_id == "principal:author"
    assert resolved is principal


@pytest.mark.parametrize(
    ("record", "identifier", "role", "scope", "at", "message"),
    [
        (
            _principal("principal:author", "a"),
            "unknown",
            "author",
            "PR-119",
            AT,
            "unknown principal",
        ),
        (
            _principal("principal:author", "a"),
            "principal:author",
            "adjudicator",
            "PR-119",
            AT,
            "not allowed role",
        ),
        (
            _principal("principal:author", "a"),
            "principal:author",
            "author",
            "PR-*",
            AT,
            "not allowed scope",
        ),
        (
            _principal("principal:author", "a", revoked=True),
            "principal:author",
            "author",
            "PR-119",
            AT,
            "revoked",
        ),
        (
            _principal("principal:author", "a"),
            "principal:author",
            "author",
            "PR-119",
            datetime(2025, 12, 31, tzinfo=UTC),
            "not yet valid",
        ),
        (
            _principal("principal:author", "a"),
            "principal:author",
            "author",
            "PR-119",
            datetime(2027, 1, 1, tzinfo=UTC),
            "expired",
        ),
    ],
)
def test_registry_denies_unknown_wrong_scope_revoked_or_expired_principals(
    record: PrincipalRecord,
    identifier: str,
    role: str,
    scope: str,
    at: datetime,
    message: str,
) -> None:
    registry = AuthorityRegistry((record,))

    with pytest.raises(AuthorityError, match=message):
        registry.resolve(identifier, role=role, scope=scope, at=at)


def test_registry_validates_identity_fingerprint_on_use() -> None:
    registry = AuthorityRegistry((_principal("principal:author", "a"),))

    with pytest.raises(AuthorityError, match="fingerprint mismatch"):
        registry.resolve(
            "principal:author",
            role="author",
            scope="PR-119",
            at=AT,
            identity_fingerprint="b" * 64,
        )


def test_registry_rejects_alias_collisions_and_malformed_principals() -> None:
    first = _principal("principal:first", "a", aliases=("shared",))
    second = _principal("principal:second", "b", aliases=("shared",))
    with pytest.raises(AuthorityError, match="collision"):
        AuthorityRegistry((first, second))
    with pytest.raises(AuthorityError, match="repeat principal_id"):
        replace(first, aliases=(first.principal_id,))

    with pytest.raises(AuthorityError, match="SHA-256"):
        replace(first, identity_fingerprint="not-a-digest")
    with pytest.raises(AuthorityError, match="allowed_scopes"):
        replace(first, allowed_scopes=())
    with pytest.raises(AuthorityError, match="verifier"):
        replace(first, verifier="")
    with pytest.raises(AuthorityError, match="later"):
        replace(first, valid_until=first.valid_from)


def test_author_adjudicator_inequality_uses_canonical_alias_resolution() -> None:
    same = _principal(
        "principal:same",
        "a",
        aliases=("author-name", "adjudicator-name"),
        roles=("author", "adjudicator"),
    )
    registry = AuthorityRegistry((same,))

    with pytest.raises(AuthorityError, match="distinct canonical identities"):
        assert_distinct_author_adjudicator(
            registry,
            author="author-name",
            adjudicator="adjudicator-name",
            scope="PR-119",
            at=AT,
        )


def test_author_adjudicator_inequality_rejects_duplicate_identity_fingerprint() -> None:
    with pytest.raises(AuthorityError, match="identity_fingerprint collision"):
        AuthorityRegistry(
            (
                _principal("principal:author", "a", roles=("author",)),
                _principal(
                    "principal:adjudicator", "a", roles=("adjudicator",)
                ),
            )
        )


def test_internal_adjudicator_without_promotion_role_cannot_exceed_ceiling() -> None:
    registry = _pr119_bootstrap_registry()
    receipt = _adjudication_receipt(
        adjudicator="adjudicator-alias",
        signer_id="principal:internal-reviewer",
    )

    assert all(
        "scientific_status_promoter" not in principal.allowed_roles
        for principal in registry.all()
    )
    assert all(
        principal.independence_class
        == "correlated_internal_non_author_review"
        for principal in registry.all()
    )

    with pytest.raises(AuthorityError, match="scientific_status_promoter"):
        validate_scientific_transition(
            ScientificStatus.ADJUDICATION_PENDING,
            ScientificStatus.RESCUED,
            registry=registry,
            attestation=receipt,
            claim_id="GOV-PR119-DAG-INTAKE",
            claim_identity_fingerprint=SPEC_FINGERPRINT,
            scope="PR-119",
            at=AT,
        )
    with pytest.raises(AuthorityError, match="scientific_status_promoter"):
        resolve_dependency(
            DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
            DependencyEvidence(adjudication_receipt=receipt),
            registry=registry,
            scope="PR-119",
            at=AT,
        )


@pytest.mark.parametrize(
    "target",
    [
        ScientificStatus.RESCUED,
        ScientificStatus.CORRECTED_SUPERSEDED,
        ScientificStatus.FALSIFIED,
        ScientificStatus.BLOCKED,
        ScientificStatus.ABANDONED,
    ],
)
def test_adjudicated_status_requires_attested_non_author_promotion(
    target: ScientificStatus,
) -> None:
    registry = _dependency_registry()
    with pytest.raises(AuthorityError, match="verifiable.*attestation"):
        validate_scientific_transition(
            ScientificStatus.ADJUDICATION_PENDING,
            target,
            registry=registry,
            claim_id="GOV-PR119-DAG-INTAKE",
            claim_identity_fingerprint=SPEC_FINGERPRINT,
            scope="PR-119",
            at=AT,
        )

    assert validate_scientific_transition(
        ScientificStatus.ADJUDICATION_PENDING,
        target,
        registry=registry,
        attestation=_adjudication_receipt(target),
        claim_id="GOV-PR119-DAG-INTAKE",
        claim_identity_fingerprint=SPEC_FINGERPRINT,
        scope="PR-119",
        at=AT,
    ) is target


def test_scientific_attestation_must_bind_claim_fingerprint_and_target() -> None:
    registry = _dependency_registry()
    receipt = _adjudication_receipt(ScientificStatus.FALSIFIED)

    with pytest.raises(AuthorityError, match="not bound"):
        validate_scientific_transition(
            ScientificStatus.ADJUDICATION_PENDING,
            ScientificStatus.RESCUED,
            registry=registry,
            attestation=receipt,
            claim_id="GOV-PR119-DAG-INTAKE",
            claim_identity_fingerprint=SPEC_FINGERPRINT,
            scope="PR-119",
            at=AT,
        )
    with pytest.raises(AuthorityError, match="not bound"):
        validate_scientific_transition(
            ScientificStatus.ADJUDICATION_PENDING,
            ScientificStatus.FALSIFIED,
            registry=registry,
            attestation=receipt,
            claim_id="WRONG-CLAIM-ID",
            claim_identity_fingerprint=SPEC_FINGERPRINT,
            scope="PR-119",
            at=AT,
        )
    with pytest.raises(AuthorityError, match="not bound"):
        validate_scientific_transition(
            ScientificStatus.ADJUDICATION_PENDING,
            ScientificStatus.FALSIFIED,
            registry=registry,
            attestation=receipt,
            claim_id="GOV-PR119-DAG-INTAKE",
            claim_identity_fingerprint="9" * 64,
            scope="PR-119",
            at=AT,
        )


def test_nonterminal_science_transition_is_explicit_and_execution_independent() -> None:
    state = RemediationState(
        OrchestrationState.TERMINAL,
        execution_resolution=ExecutionResolution.COMPLETED_FAILED_WITH_RECEIPT,
        scientific_status=ScientificStatus.OPEN,
    )

    with pytest.raises(RemediationContractError, match="must follow"):
        state.transition_scientific(ScientificStatus.ADJUDICATION_PENDING)

    updated = state.transition_scientific(ScientificStatus.IN_REMEDIATION)
    updated = updated.transition_scientific(ScientificStatus.EVIDENCE_READY)
    updated = updated.transition_scientific(ScientificStatus.ADJUDICATION_PENDING)

    assert updated.scientific_status is ScientificStatus.ADJUDICATION_PENDING
    assert updated.execution_resolution is state.execution_resolution
    assert updated.orchestration_state is state.orchestration_state


@pytest.mark.parametrize(
    "status",
    [status for status in ScientificStatus if status is not ScientificStatus.OPEN],
)
def test_direct_noninitial_scientific_status_construction_is_rejected(
    status: ScientificStatus,
) -> None:
    with pytest.raises(RemediationContractError, match="initial OPEN state only"):
        RemediationState(
            OrchestrationState.PENDING,
            scientific_status=status,
        )
    assert not hasattr(RemediationState, "_from_validated_axes")


def test_dormant_external_success_requires_verified_delivery_receipt() -> None:
    state = RemediationState(OrchestrationState.DORMANT_EXTERNAL)
    with pytest.raises(AuthorityError, match="authenticated external receipt"):
        state.resolve_execution(ExecutionResolution.COMPLETED_SUCCESS)

    terminal = state.resolve_execution(
        ExecutionResolution.COMPLETED_SUCCESS,
        registry=_dependency_registry(),
        external_receipt=_external_receipt(),
        scope="PR-159",
        at=AT,
    )

    assert terminal.orchestration_state is OrchestrationState.TERMINAL
    assert terminal.execution_resolution is ExecutionResolution.COMPLETED_SUCCESS
    assert terminal.scientific_status is ScientificStatus.OPEN


@pytest.mark.parametrize(
    ("current", "skipped"),
    [
        (ScientificStatus.OPEN, ScientificStatus.EVIDENCE_READY),
        (ScientificStatus.OPEN, ScientificStatus.ADJUDICATION_PENDING),
        (ScientificStatus.IN_REMEDIATION, ScientificStatus.ADJUDICATION_PENDING),
        (ScientificStatus.EVIDENCE_READY, ScientificStatus.RESCUED),
    ],
)
def test_scientific_transition_cannot_skip_adjacent_states(
    current: ScientificStatus,
    skipped: ScientificStatus,
) -> None:
    with pytest.raises(RemediationContractError, match="must follow"):
        validate_scientific_transition(current, skipped)


@pytest.mark.parametrize("owner", ["COMMON", "HTT", "MIO", "BASS", "OBSSTAT"])
def test_active_owner_helper_accepts_only_new_role_map(owner: str) -> None:
    assert validate_active_owner(owner) == owner


@pytest.mark.parametrize(
    "owner", ["TSC", "TSC_LEGACY", "TEFF", "MANUSCRIPT", "BASS_PY"]
)
def test_active_owner_helper_rejects_legacy_or_quarantined_owners(owner: str) -> None:
    with pytest.raises(RemediationContractError, match="forbidden"):
        validate_active_owner(owner)


def test_active_owner_helper_is_default_deny_for_unknown_values() -> None:
    with pytest.raises(RemediationContractError, match="unknown active"):
        validate_active_owner("FUTURE_OWNER")
    with pytest.raises(RemediationContractError, match="unknown active"):
        validate_active_owner("htt")
