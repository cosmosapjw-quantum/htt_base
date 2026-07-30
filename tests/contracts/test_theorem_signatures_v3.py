from __future__ import annotations

import copy
import hashlib
import inspect
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from common.tensor_foundations_oracle import run_all
from common.theorem_signatures_v3 import (
    ComponentStatus,
    MUTATION_VECTOR_IDS,
    ProofAdjudicationStatus,
    SourceGroup,
    StatementStatus,
    TheoremSignatureV3Error,
    exercise_tensor_oracle_mutations,
    load_theorem_signature_registry_v3,
    run_registered_tensor_oracle,
    validate_tensor_oracle_receipt,
)


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = (
    ROOT
    / "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
)
V2_PATH = ROOT / "docs/research_program/THEOREM_SIGNATURES_V2.yaml"
V2_LOADER_PATH = ROOT / "htt/src/common/theorem_signatures.py"
ORACLE_PROPOSAL_PATH = (
    ROOT
    / "docs/research_program/vector_tensor/"
    "tensor_foundations_oracle_proposal.py"
)
ORACLE_PRODUCTION_PATH = (
    ROOT / "htt/src/common/tensor_foundations_oracle.py"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload() -> dict:
    value = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_mutation(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "THEOREM_SIGNATURES_V3.yaml"
    path.write_text(
        yaml.safe_dump(
            payload,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture(scope="session")
def registry():
    return load_theorem_signature_registry_v3(ROOT)


@pytest.fixture(scope="session")
def full_oracle_receipt():
    return run_all(seed=20260730, fast=False)


def test_v2_registry_and_loader_bytes_remain_frozen() -> None:
    assert _sha256(V2_PATH) == (
        "4e43de815088b372cac82e889fe86b55c815f327af231611336b11ebb8a487d9"
    )
    assert _sha256(V2_LOADER_PATH) == (
        "214edec76e6deb8c2064b7edb5765a683213b552783baebe6be1b902fa0e160e"
    )


def test_generated_registry_is_current() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/build_pr268_theorem_signatures.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_exact_alias_cardinalities_and_true_partitions(registry) -> None:
    assert len(registry.legacy_entries) == 65
    assert len(registry.proposal_entries) == 58
    assert sum(
        entry.source_partition == "T" for entry in registry.legacy_entries
    ) == 31
    assert sum(
        entry.source_partition == "S" for entry in registry.legacy_entries
    ) == 34
    assert sum(
        entry.source_partition == "I" for entry in registry.proposal_entries
    ) == 30
    assert sum(
        entry.source_partition == "II" for entry in registry.proposal_entries
    ) == 24
    assert sum(
        entry.source_partition == "BRIDGE"
        for entry in registry.proposal_entries
    ) == 4


def test_source_groups_are_exact_and_id_disjoint(registry) -> None:
    legacy_ids = {entry.entry_id for entry in registry.legacy_entries}
    proposal_ids = {entry.entry_id for entry in registry.proposal_entries}
    assert len(legacy_ids) == 65
    assert len(proposal_ids) == 58
    assert legacy_ids.isdisjoint(proposal_ids)
    assert all(
        entry.source_group is SourceGroup.LEGACY
        for entry in registry.legacy_entries
    )
    assert all(
        entry.source_group is SourceGroup.PROPOSAL
        for entry in registry.proposal_entries
    )


def test_checked_v2_metadata_and_missingness_are_typed(registry) -> None:
    checked = tuple(
        entry
        for entry in registry.legacy_entries
        if entry.source_status == "CHECKED"
    )
    pending = tuple(
        entry
        for entry in registry.legacy_entries
        if entry.source_status == "MIGRATION_PENDING"
    )
    assert len(checked) == 12
    assert len(pending) == 53
    assert all(
        entry.assumption_status is ComponentStatus.DECLARED
        and entry.domain_status is ComponentStatus.DECLARED
        and entry.frame_status is ComponentStatus.DECLARED
        and entry.branch_status is ComponentStatus.SOURCE_NOT_TYPED
        and entry.perturbative_order_status is ComponentStatus.DECLARED
        for entry in checked
    )
    assert all(
        entry.statement_status is StatementStatus.TITLE_ONLY
        and entry.assumption_status is ComponentStatus.SOURCE_NOT_TYPED
        and not entry.assumptions
        and entry.domain_status is ComponentStatus.SOURCE_NOT_TYPED
        and not entry.domains
        and entry.frame_convention is None
        and entry.branch_convention is None
        for entry in pending
    )


def test_proposal_prose_is_not_promoted_to_typed_premises(registry) -> None:
    assert all(
        entry.assumption_status is ComponentStatus.SOURCE_NOT_TYPED
        and not entry.assumptions
        and entry.domain_status is ComponentStatus.SOURCE_NOT_TYPED
        and not entry.domains
        and entry.frame_status is ComponentStatus.SOURCE_NOT_TYPED
        and entry.frame_convention is None
        and entry.branch_status is ComponentStatus.SOURCE_NOT_TYPED
        and entry.branch_convention is None
        for entry in registry.proposal_entries
    )
    assert registry.entry("I-5.5").statement_status is (
        StatementStatus.SOURCE_NOT_TYPED
    )
    assert registry.entry("I-5.5").statement is None


def test_every_row_binds_owner_dependencies_evidence_and_ceiling(
    registry,
) -> None:
    for entry in registry.entries:
        assert entry.registry_owner == "COMMON"
        assert entry.scientific_owner
        assert entry.dependencies
        assert entry.required_evidence
        assert entry.evidence_path
        assert entry.claim_ceiling == "diagnostic_only"
        assert entry.proof_adjudication_status is (
            ProofAdjudicationStatus.NOT_ADJUDICATED
        )
        assert not entry.counts_toward_theorem_count


def test_raw_cardinality_cannot_be_rendered_as_theorem_count(
    registry,
) -> None:
    with pytest.raises(
        TheoremSignatureV3Error,
        match="not an adjudicated theorem count",
    ):
        registry.reject_raw_theorem_count(len(registry.entries))


def test_statement_identity_mutation_is_refused(
    tmp_path: Path,
) -> None:
    payload = _payload()
    payload["source_groups"]["legacy_signature_inventory"]["entries"][0][
        "statement_identity_sha256"
    ] = "0" * 64
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(
        TheoremSignatureV3Error,
        match="statement identity drifted",
    ):
        load_theorem_signature_registry_v3(ROOT, path)


def test_proposal_premise_invention_is_refused(tmp_path: Path) -> None:
    payload = _payload()
    row = payload["source_groups"]["proposal_registry_rows"]["entries"][0]
    row["assumption_status"] = "DECLARED"
    row["assumptions"] = ["inferred from prose"]
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(
        TheoremSignatureV3Error,
        match="proposal prose was promoted",
    ):
        load_theorem_signature_registry_v3(ROOT, path)


def test_source_status_cannot_promote_adjudication(
    tmp_path: Path,
) -> None:
    payload = _payload()
    row = payload["source_groups"]["proposal_registry_rows"]["entries"][0]
    row["proof_adjudication_status"] = "PROVEN"
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(
        TheoremSignatureV3Error,
        match="unsupported typed enum",
    ):
        load_theorem_signature_registry_v3(ROOT, path)


def test_cardinality_alias_mutation_is_refused(tmp_path: Path) -> None:
    payload = _payload()
    payload["cardinality_aliases"][
        "requested_pillar_T_65"
    ] = "proposal_registry_rows"
    path = _write_mutation(tmp_path, payload)
    with pytest.raises(
        TheoremSignatureV3Error,
        match="65-row alias semantics drifted",
    ):
        load_theorem_signature_registry_v3(ROOT, path)


def test_oracle_is_byte_identical_to_registered_proposal(registry) -> None:
    assert ORACLE_PROPOSAL_PATH.read_bytes() == (
        ORACLE_PRODUCTION_PATH.read_bytes()
    )
    assert registry.oracle_source_sha256 == _sha256(ORACLE_PROPOSAL_PATH)
    assert registry.oracle_production_sha256 == _sha256(
        ORACLE_PRODUCTION_PATH
    )


def test_all_twelve_oracle_statement_links_preserve_primary_status(
    registry,
) -> None:
    assert len(registry.oracle_links) == 12
    by_proposition = {
        link.proposition_id: link for link in registry.oracle_links
    }
    assert by_proposition[
        "TF-03-KRYLOV-SYZYGY"
    ].primary_source_status == "PROVEN_CAS4"
    assert by_proposition[
        "TF-04-CAYLEY-HAMILTON-REDUCTION"
    ].primary_source_status == "PROVEN_CAS4"
    assert by_proposition[
        "TF-12-ACCELERATION-EULER-SLAVING"
    ].primary_source_status == "ACTIVE_CONDITIONAL"
    assert all(link.proof_effect == "none" for link in registry.oracle_links)


def test_full_registered_oracle_receipt_is_valid(
    full_oracle_receipt,
) -> None:
    validation = validate_tensor_oracle_receipt(full_oracle_receipt)
    assert validation.valid, validation.errors
    assert validation.proof_effect == "none"
    assert validation.evidence_posture == "EXECUTABLE_TEST_EVIDENCE_ONLY"


def test_supplied_fast_mode_is_not_an_acceptance_vector() -> None:
    receipt = run_all(seed=20260730, fast=True)
    assert receipt["failed"] == ("TF-11-MASK-PATH-MARTINGALE",)
    validation = validate_tensor_oracle_receipt(receipt)
    assert not validation.valid
    assert "stable vector must use the full registered oracle" in (
        validation.errors
    )


def test_full_oracle_is_deterministic(full_oracle_receipt) -> None:
    repeated = run_all(seed=20260730, fast=False)
    assert repeated == full_oracle_receipt
    assert validate_tensor_oracle_receipt(repeated).receipt_sha256 == (
        validate_tensor_oracle_receipt(
            full_oracle_receipt
        ).receipt_sha256
    )


def test_all_registered_oracle_mutations_are_killed(
    full_oracle_receipt,
) -> None:
    errors = exercise_tensor_oracle_mutations(full_oracle_receipt)
    assert tuple(errors) == MUTATION_VECTOR_IDS
    assert all(errors[vector_id] for vector_id in MUTATION_VECTOR_IDS)


def test_registered_wrapper_retains_no_proof_effect(registry) -> None:
    receipt, validation = run_registered_tensor_oracle(registry)
    assert receipt["ok"] is True
    assert validation.valid
    assert validation.proof_effect == "none"
    assert registry.proof_adjudication_status is (
        ProofAdjudicationStatus.NOT_ADJUDICATED
    )


def test_oracle_unproven_and_premise_mutations_are_refused(
    full_oracle_receipt,
) -> None:
    promoted = copy.deepcopy(full_oracle_receipt)
    promoted["propositions"]["TF-02-CATALOGUE-COMPLETION"][
        "degree_completeness_status"
    ] = "PROVEN"
    assert "TF-02 degree completeness was promoted" in (
        validate_tensor_oracle_receipt(promoted).errors
    )

    erased = copy.deepcopy(full_oracle_receipt)
    erased["propositions"]["TF-12-ACCELERATION-EULER-SLAVING"][
        "premises"
    ] = ()
    assert "TF-12 premise block drifted" in (
        validate_tensor_oracle_receipt(erased).errors
    )


def test_public_loader_and_oracle_resolve_to_pr268_sources() -> None:
    import common.tensor_foundations_oracle as oracle_module
    import common.theorem_signatures_v3 as registry_module

    assert Path(inspect.getsourcefile(registry_module)).resolve() == (
        ROOT / "htt/src/common/theorem_signatures_v3.py"
    ).resolve()
    assert Path(inspect.getsourcefile(oracle_module)).resolve() == (
        ORACLE_PRODUCTION_PATH.resolve()
    )
