from __future__ import annotations

import ast
from pathlib import Path

import pytest

from common.contracts import ArtifactManifest, ClaimTier, ImplementationScope, Owner
from common.semantic_guards import scan_text
from common.semantic_guards.admissibility_status import (
    ObservableAdequacyStatus,
    PropagationAdequacyStatus,
    SemanticAdequacyRecord,
    SourceAdequacyStatus,
    attach_semantic_caveats,
)
from common.semantic_guards.source_propagation_status import (
    SourcePropagationStatus,
    build_source_propagation_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_GUARD_ROOT = REPO_ROOT / "htt" / "src" / "common" / "semantic_guards"


def _manifest(
    owner: Owner = Owner.COMMON,
    claim_tier: ClaimTier = ClaimTier.DIAGNOSTIC_ONLY,
) -> ArtifactManifest:
    scope = {
        Owner.COMMON: ImplementationScope.COMMON,
        Owner.HTT: ImplementationScope.HTT,
        Owner.MIO: ImplementationScope.MIO,
        Owner.BASS: ImplementationScope.BASS_PY,
        Owner.OBSSTAT: ImplementationScope.OBSSTAT,
        Owner.TSC_LEGACY: ImplementationScope.TSC_LEGACY,
    }[owner]
    return ArtifactManifest(
        artifact_id=f"{owner.value.lower()}.semantic.guard",
        artifact_path=f"artifacts/{owner.value.lower()}/semantic_guard.json",
        owner=owner,
        implementation_scope=scope,
        claim_tier=claim_tier,
        production_status="diagnostic_only",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["input"],
        code_version="0.0-test",
        schema_version="pr031",
    )


def test_source_propagation_and_observable_statuses_are_separate() -> None:
    record = SemanticAdequacyRecord(
        source_status=SourceAdequacyStatus.ADEQUATE,
        propagation_status=PropagationAdequacyStatus.PENDING,
        observable_status=ObservableAdequacyStatus.NOT_EVALUATED,
        caveats=("observable adequacy not evaluated",),
    )

    assert record.source_is_adequate is True
    assert record.propagation_is_validated is False
    assert record.observable_is_adequate is False
    assert record.to_metadata()["source_status"] == "adequate"
    assert record.to_metadata()["propagation_status"] == "pending"
    assert record.to_metadata()["observable_status"] == "not_evaluated"
    assert record.to_metadata()["observable_status_is_explicit"] is True
    assert record.to_metadata()["observable_adequacy_is_established"] is False
    assert (
        record.to_metadata()["observable_adequacy_scope"]
        == "semantic_guard_only_not_statistical_validation"
    )
    assert "observable_adequacy_is_explicit" not in record.to_metadata()


def test_source_adequate_does_not_imply_observable_adequate() -> None:
    status = build_source_propagation_status(
        source_status=SourceAdequacyStatus.ADEQUATE,
        propagation_status=PropagationAdequacyStatus.VALIDATED,
        observable_status=ObservableAdequacyStatus.NOT_EVALUATED,
    )

    assert status.source_status is SourceAdequacyStatus.ADEQUATE
    assert status.propagation_status is PropagationAdequacyStatus.VALIDATED
    assert status.observable_status is ObservableAdequacyStatus.NOT_EVALUATED
    assert status.observable_is_adequate is False
    assert status.label == "source_adequate__propagation_validated__observable_not_evaluated"
    assert "observable adequacy not established" in status.caveats
    assert status.claim_tier_ceiling is ClaimTier.DIAGNOSTIC_ONLY


def test_observable_adequacy_requires_explicit_source_and_propagation_support() -> None:
    with pytest.raises(ValueError, match="observable_status='adequate'.*source_status"):
        SemanticAdequacyRecord(
            source_status=SourceAdequacyStatus.PENDING,
            propagation_status=PropagationAdequacyStatus.VALIDATED,
            observable_status=ObservableAdequacyStatus.ADEQUATE,
            caveats=("invalid promotion",),
        )
    with pytest.raises(ValueError, match="observable_status='adequate'.*propagation_status"):
        SemanticAdequacyRecord(
            source_status=SourceAdequacyStatus.ADEQUATE,
            propagation_status=PropagationAdequacyStatus.PENDING,
            observable_status=ObservableAdequacyStatus.ADEQUATE,
            caveats=("invalid promotion",),
        )


def test_semantic_guard_rejects_unknown_status_values() -> None:
    with pytest.raises(ValueError, match="Unknown source_status"):
        SemanticAdequacyRecord(
            source_status="sourceish",
            propagation_status="pending",
            observable_status="not_evaluated",
        )
    with pytest.raises(ValueError, match="Unknown propagation_status"):
        SemanticAdequacyRecord(
            source_status="adequate",
            propagation_status="teleported",
            observable_status="not_evaluated",
        )
    with pytest.raises(ValueError, match="Unknown observable_status"):
        SemanticAdequacyRecord(
            source_status="adequate",
            propagation_status="validated",
            observable_status="published",
        )


def test_semantic_guard_rejects_conditional_or_validated_claim_ceiling() -> None:
    with pytest.raises(ValueError, match="claim_tier_ceiling"):
        SemanticAdequacyRecord(
            source_status="adequate",
            propagation_status="validated",
            observable_status="adequate",
            claim_tier_ceiling=ClaimTier.CONDITIONAL,
        )
    with pytest.raises(TypeError, match="claim_tier_ceiling"):
        SourcePropagationStatus(
            source_status="adequate",
            propagation_status="validated",
            observable_status="adequate",
            claim_tier_ceiling=ClaimTier.CONDITIONAL,
        )


def test_trace_source_caveats_attach_without_tsc_ownership() -> None:
    manifest = _manifest(Owner.HTT)
    record = SemanticAdequacyRecord(
        source_status="adequate",
        propagation_status="pending",
        observable_status="not_evaluated",
        caveats=("trace-source bridge adequate but propagation remains pending",),
        labels=("source_adequate__propagation_pending",),
    )

    updated = attach_semantic_caveats(manifest, record)

    assert updated.owner is Owner.HTT
    assert updated.implementation_scope is ImplementationScope.HTT
    assert updated.claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    assert updated.caveats[-2:] == [
        "semantic_guard:source=adequate;propagation=pending;observable=not_evaluated",
        "trace-source bridge adequate but propagation remains pending",
    ]


def test_trace_source_caveats_cannot_support_stronger_manifest_tier() -> None:
    manifest = _manifest(Owner.HTT, claim_tier=ClaimTier.CONDITIONAL)
    record = SemanticAdequacyRecord(
        source_status="adequate",
        propagation_status="validated",
        observable_status="adequate",
    )

    with pytest.raises(ValueError, match="claim_tier above 'diagnostic_only'"):
        attach_semantic_caveats(manifest, record)


def test_source_propagation_status_is_not_an_observable_claim() -> None:
    status = SourcePropagationStatus(
        source_status="adequate",
        propagation_status="pending",
        observable_status="not_evaluated",
    )

    assert status.source_is_adequate
    assert not status.propagation_is_validated
    assert not status.observable_is_adequate
    assert status.claim_tier_ceiling is ClaimTier.DIAGNOSTIC_ONLY
    assert status.to_metadata()["semantic_guard_owner"] == Owner.COMMON.value


def test_source_propagation_hard_failures_block_claim_ceiling() -> None:
    source_failed = SourcePropagationStatus(
        source_status="inadequate",
        propagation_status="validated",
        observable_status="conditional",
    )
    propagation_failed = SourcePropagationStatus(
        source_status="adequate",
        propagation_status="blocked",
        observable_status="conditional",
    )

    assert source_failed.claim_tier_ceiling is ClaimTier.BLOCKED
    assert propagation_failed.claim_tier_ceiling is ClaimTier.BLOCKED


def _unsafe_source_observable_phrase(variant: str) -> str:
    source = "source"
    adequate = "adequate"
    adequacy = "adequacy"
    observable = "observable"
    therefore = "there" + "fore"
    automatically_implies = "automatically " + "implies"
    sufficient = "is sufficient for"
    means = "means"
    if variant == "compact":
        return f"{source} {adequate} {therefore} {observable} {adequate}."
    if variant == "punctuated":
        return f"{source} {adequate}: {therefore} {observable} {adequate}."
    if variant == "automatic":
        return f"{source} {adequate} {automatically_implies} {observable} {adequate}"
    if variant == "adequacy":
        return f"{source} {adequacy} {sufficient} {observable} {adequacy}"
    if variant == "inverted_subject":
        return f"{adequate} {source} {means} the {observable} is {adequate}"
    if variant == "wrapped":
        return f"{source} {adequacy}\n{sufficient} {observable} {adequacy}"
    raise AssertionError(f"unknown fixture variant {variant}")


@pytest.mark.parametrize(
    "variant",
    ["compact", "punctuated", "automatic", "adequacy", "inverted_subject", "wrapped"],
)
def test_common_no_overclaim_guard_blocks_source_observable_conflation(
    variant: str,
) -> None:
    text = _unsafe_source_observable_phrase(variant)
    issues = scan_text(text, path=Path("source_claim.md"))

    assert "source_observable_conflation" in [issue.rule_id for issue in issues]


def test_semantic_guard_modules_do_not_import_package_specific_owners() -> None:
    offending: dict[str, set[str]] = {}
    for path in SEMANTIC_GUARD_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        tsc_imports = {
            name
            for name in imports
            if name == "tsc"
            or name.startswith("tsc.")
            or name == "htt"
            or name.startswith("htt.")
            or name == "mio"
            or name.startswith("mio.")
            or name == "bass"
            or name.startswith("bass.")
            or name == "obsstat"
            or name.startswith("obsstat.")
        }
        if tsc_imports:
            offending[path.name] = tsc_imports

    assert offending == {}
