from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

import common.mes_successor_registry as mes_registry
from common.mes_successor_registry import (
    CURRENT_SUCCESSOR_ID,
    DEFAULT_ACTIVE_PYTHON_ROOTS,
    DEFAULT_CONSUMER_INVENTORY_PATH,
    DEFAULT_CONSUMER_MIGRATION_PATH,
    DEFAULT_CONSUMER_SUPERSESSION_PATH,
    EGS3_BRANCH_SEAL_PATH,
    EGS3_BRANCH_SEAL_SHA256,
    LEGACY_REPRODUCTION_SHA256,
    MesConsumerDeclaration,
    MesConsumerExclusion,
    MesConsumerIssueCode,
    MesExclusionTransition,
    MesProcessResult,
    MesRegistryError,
    MesScientificAuthorityStatus,
    MesSuccessorPointer,
    MesSuccessorRegistry,
    PR248_CONSUMER_SUPERSESSION_SHA256,
    PR252_CONSUMER_MIGRATION_SHA256,
    SourceAvailability,
    SourceHashBinding,
    current_mes_successor_registry,
    finding_codes,
    registered_mes_exclusion_transition,
    resolve_mes_exclusion_transition,
    scan_declared_mes_consumers,
    validate_mes_successor_registry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGED_PR124_RECEIPT = (
    REPO_ROOT / "htt/src/common/resources/pr124_mes_authority_table.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_consumer(
    tmp_path: Path,
    text: str,
    *,
    relative_path: str = "consumer.py",
    consumer_id: str = "synthetic-active-consumer",
) -> MesConsumerDeclaration:
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return MesConsumerDeclaration(
        consumer_id=consumer_id,
        source=SourceHashBinding(
            path=relative_path,
            availability=SourceAvailability.AVAILABLE,
            sha256=_digest(path),
        ),
    )


def _copy_current_registry_inputs(tmp_path: Path) -> MesSuccessorRegistry:
    registry = current_mes_successor_registry()
    for binding in (
        registry.legacy_reproduction_source,
        registry.egs3_branch_witness.source,
        registry.egs3_branch_witness.seal,
        # PR-124: the successor source is AVAILABLE and hash-pinned
        registry.successor.source,
    ):
        target = tmp_path / binding.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO_ROOT / binding.path).read_bytes())
    return registry


# In a tmp copy the PR-124 receipt artifacts are absent by construction, so
# the live receipt verification fails closed there: tmp validations carry
# exactly this authority blocker on top of any injected defect.
TMP_AUTHORITY_BLOCKER = MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED.value


def _inventory() -> dict[str, object]:
    payload = yaml.safe_load(
        (REPO_ROOT / DEFAULT_CONSUMER_INVENTORY_PATH).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def _inventory_declarations(
    payload: dict[str, object],
) -> tuple[MesConsumerDeclaration, ...]:
    rows = payload["active_consumers"]
    assert isinstance(rows, list)
    return tuple(
        MesConsumerDeclaration(
            consumer_id=row["consumer_id"],
            source=SourceHashBinding(
                path=row["path"],
                availability=SourceAvailability.AVAILABLE,
                sha256=row["sha256"],
            ),
        )
        for row in rows
    )


def _consumer_supersession() -> dict[str, object]:
    path = REPO_ROOT / DEFAULT_CONSUMER_SUPERSESSION_PATH
    assert _digest(path) == PR248_CONSUMER_SUPERSESSION_SHA256
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _consumer_migration() -> dict[str, object]:
    path = REPO_ROOT / DEFAULT_CONSUMER_MIGRATION_PATH
    assert _digest(path) == PR252_CONSUMER_MIGRATION_SHA256
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _registered_exclusion_row() -> dict[str, str]:
    return {
        "exclusion_id": "tsc.admissibility.three_bound_hierarchy",
        "path": "htt/tsc/admissibility/three_bound_hierarchy.py",
        "prior_sha256": (
            "cc3ba841a4b61ac10a1d7a82e56b96391afcd81d8bd169bd8ca33940c7cf671e"
        ),
        "sha256": LEGACY_REPRODUCTION_SHA256,
        "reason": "registered chronology fixture",
    }


def test_registered_pr252_exclusion_transition_binds_historical_and_live_bytes() -> None:
    transition = registered_mes_exclusion_transition(
        REPO_ROOT,
        path="htt/tsc/admissibility/three_bound_hierarchy.py",
        historical_sha256=(
            "cc3ba841a4b61ac10a1d7a82e56b96391afcd81d8bd169bd8ca33940c7cf671e"
        ),
    )

    assert isinstance(transition, MesExclusionTransition)
    assert transition.sha256 == LEGACY_REPRODUCTION_SHA256
    assert transition.sha256 == _digest(REPO_ROOT / transition.path)


def test_exclusion_transition_mutations_fail_closed() -> None:
    row = _registered_exclusion_row()

    with pytest.raises(MesRegistryError, match="no unique registered"):
        resolve_mes_exclusion_transition(
            [row],
            path="htt/tsc/admissibility/unknown.py",
            prior_sha256=row["prior_sha256"],
            current_sha256=row["sha256"],
        )

    duplicate = {**row, "exclusion_id": "duplicate.transition"}
    with pytest.raises(MesRegistryError, match="duplicate exclusion transition path"):
        resolve_mes_exclusion_transition(
            [row, duplicate],
            path=row["path"],
            prior_sha256=row["prior_sha256"],
            current_sha256=row["sha256"],
        )

    duplicate_identity = {
        **row,
        "path": "htt/tsc/admissibility/duplicate.py",
    }
    with pytest.raises(
        MesRegistryError, match="duplicate exclusion transition identity"
    ):
        resolve_mes_exclusion_transition(
            [row, duplicate_identity],
            path=row["path"],
            prior_sha256=row["prior_sha256"],
            current_sha256=row["sha256"],
        )

    with pytest.raises(MesRegistryError, match="historical exclusion pin drifted"):
        resolve_mes_exclusion_transition(
            [row],
            path=row["path"],
            prior_sha256="0" * 64,
            current_sha256=row["sha256"],
        )

    with pytest.raises(MesRegistryError, match="current exclusion pin drifted"):
        resolve_mes_exclusion_transition(
            [row],
            path=row["path"],
            prior_sha256=row["prior_sha256"],
            current_sha256="f" * 64,
        )


def test_current_successor_is_available_and_pr124_authorized() -> None:
    registry = current_mes_successor_registry()
    pointer = registry.successor

    assert pointer.successor_id == CURRENT_SUCCESSOR_ID
    assert pointer.source.availability is SourceAvailability.AVAILABLE
    assert pointer.source.sha256 == _digest(REPO_ROOT / pointer.source.path)
    assert pointer.process_result is MesProcessResult.PASS
    assert (
        pointer.scientific_status is MesScientificAuthorityStatus.AUTHORIZED_BY_PR124
    )
    # governance authority at conditional C1 (pins match + live verification
    # is re-run by validate_mes_successor_registry below)
    assert pointer.scientific_authority is True
    assert registry.as_payload()["release_claim_allowed"] is True


def test_packaged_pr124_receipt_is_byte_identical_to_historical_authority() -> None:
    historical = REPO_ROOT / "docs/generated/pr124_mes_authority_table.json"

    assert PACKAGED_PR124_RECEIPT.read_bytes() == historical.read_bytes()
    assert _digest(PACKAGED_PR124_RECEIPT) == mes_registry.PR124_AUTHORITY_RECEIPT_SHA256


def test_repository_layout_never_falls_back_when_receipt_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module_path = tmp_path / "htt/src/common/mes_successor_registry.py"
    module_path.parent.mkdir(parents=True)
    module_path.write_text("# identity fixture\n", encoding="utf-8")
    monkeypatch.setattr(mes_registry, "__file__", str(module_path))
    monkeypatch.setattr(
        mes_registry.resources,
        "files",
        lambda package: REPO_ROOT / "htt/src/common",
    )
    mes_registry._live_receipt_pin_check.cache_clear()

    with pytest.raises(MesRegistryError, match="package fallback is forbidden"):
        mes_registry._live_receipt_pin_check()


def test_installed_layout_uses_only_hash_pinned_package_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    installed_module = tmp_path / "site-packages/common/mes_successor_registry.py"
    installed_module.parent.mkdir(parents=True)
    installed_module.write_text("# installed fixture\n", encoding="utf-8")
    resources_root = tmp_path / "package/common"
    resource = resources_root / "resources/pr124_mes_authority_table.json"
    resource.parent.mkdir(parents=True)
    resource.write_bytes(PACKAGED_PR124_RECEIPT.read_bytes())
    monkeypatch.setattr(mes_registry, "__file__", str(installed_module))
    monkeypatch.setattr(mes_registry.resources, "files", lambda package: resources_root)
    mes_registry._live_receipt_pin_check.cache_clear()

    assert (
        mes_registry._live_receipt_pin_check()
        == mes_registry.PR124_AUTHORITY_RECEIPT_SHA256
    )
    resource.write_bytes(resource.read_bytes() + b"\n")
    mes_registry._live_receipt_pin_check.cache_clear()
    with pytest.raises(MesRegistryError, match="do not match the module pin"):
        mes_registry._live_receipt_pin_check()


def test_installed_layout_rejects_unreadable_package_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class UnreadableResource:
        def joinpath(self, *parts: str) -> "UnreadableResource":
            return self

        def is_file(self) -> bool:
            return True

        def read_bytes(self) -> bytes:
            raise OSError("synthetic unreadable resource")

    installed_module = tmp_path / "site-packages/common/mes_successor_registry.py"
    installed_module.parent.mkdir(parents=True)
    installed_module.write_text("# installed fixture\n", encoding="utf-8")
    monkeypatch.setattr(mes_registry, "__file__", str(installed_module))
    monkeypatch.setattr(
        mes_registry.resources,
        "files",
        lambda package: UnreadableResource(),
    )
    mes_registry._live_receipt_pin_check.cache_clear()

    with pytest.raises(MesRegistryError, match="unreadable"):
        mes_registry._live_receipt_pin_check()


@pytest.mark.parametrize(
    ("process_result", "scientific_status", "receipt", "match"),
    [
        pytest.param(
            MesProcessResult.PASS,
            MesScientificAuthorityStatus.AUTHORIZED_BY_PR124,
            "x",
            "authority_receipt_id",
            id="malformed-receipt",
        ),
        pytest.param(
            MesProcessResult.FAIL,
            MesScientificAuthorityStatus.AUTHORIZED_BY_PR124,
            "0" * 64,
            "PR-124 gate PASS",
            id="failed-process",
        ),
        pytest.param(
            MesProcessResult.PASS,
            MesScientificAuthorityStatus.BLOCKED_PENDING_PR124,
            "0" * 64,
            "AUTHORIZED_BY_PR124",
            id="blocked-status",
        ),
    ],
)
def test_available_successor_shape_is_fail_closed(
    process_result: MesProcessResult | str,
    scientific_status: MesScientificAuthorityStatus | str,
    receipt: str | None,
    match: str,
) -> None:
    available = SourceHashBinding("future.py", SourceAvailability.AVAILABLE, "0" * 64)

    with pytest.raises(MesRegistryError, match=match):
        MesSuccessorPointer(
            CURRENT_SUCCESSOR_ID,
            available,
            process_result,
            scientific_status,
            receipt,
        )


def test_foreign_receipt_string_never_carries_authority() -> None:
    """A well-formed pointer with a receipt hash that is not the module pin
    has NO scientific authority — caller strings alone never escalate."""
    available = SourceHashBinding("future.py", SourceAvailability.AVAILABLE, "0" * 64)
    pointer = MesSuccessorPointer(
        CURRENT_SUCCESSOR_ID,
        available,
        MesProcessResult.PASS,
        MesScientificAuthorityStatus.AUTHORIZED_BY_PR124,
        "f" * 64,
    )
    assert pointer.scientific_authority is False


def test_egs3_pass_binds_source_and_seal_but_has_no_scientific_authority() -> None:
    registry = current_mes_successor_registry()
    witness = registry.egs3_branch_witness

    assert witness.process_result is MesProcessResult.PASS
    assert witness.scientific_authority is False
    assert witness.source.sha256 == _digest(REPO_ROOT / witness.source.path)
    assert witness.seal.path == EGS3_BRANCH_SEAL_PATH
    assert witness.seal.sha256 == EGS3_BRANCH_SEAL_SHA256
    assert witness.seal.sha256 == _digest(REPO_ROOT / witness.seal.path)
    assert witness.source.path != witness.seal.path
    assert "typed MES scientific authority" in witness.forbidden_uses
    assert registry.legacy_reproduction_source.sha256 == _digest(
        REPO_ROOT / registry.legacy_reproduction_source.path
    )


def test_current_registry_validates_clean_under_pr124_authority() -> None:
    report = validate_mes_successor_registry(REPO_ROOT)

    assert finding_codes(report) == frozenset()
    assert report.release_allowed is True
    report.assert_release_allowed()


def test_witness_source_and_seal_hashes_are_checked_separately(
    tmp_path: Path,
) -> None:
    registry = _copy_current_registry_inputs(tmp_path)
    source = tmp_path / registry.egs3_branch_witness.source.path
    source.write_text("MUTATED_SOURCE = True\n", encoding="utf-8")

    report = validate_mes_successor_registry(tmp_path)
    mismatches = [
        finding
        for finding in report.findings
        if finding.code is MesConsumerIssueCode.SOURCE_HASH_MISMATCH
    ]
    assert [finding.subject for finding in mismatches] == [
        registry.egs3_branch_witness.witness_id
    ]
    assert MesConsumerIssueCode.DIAGNOSTIC_WITNESS_INVALID.value not in finding_codes(
        report
    )

    source.write_bytes(
        (REPO_ROOT / registry.egs3_branch_witness.source.path).read_bytes()
    )
    seal = tmp_path / registry.egs3_branch_witness.seal.path
    seal.write_text("{}\n", encoding="utf-8")
    report = validate_mes_successor_registry(tmp_path)
    mismatches = [
        finding
        for finding in report.findings
        if finding.code is MesConsumerIssueCode.SOURCE_HASH_MISMATCH
    ]
    assert [finding.subject for finding in mismatches] == [
        f"{registry.egs3_branch_witness.witness_id}.seal"
    ]


@pytest.mark.parametrize(
    ("mutation", "detail"),
    [
        pytest.param(
            lambda payload: payload.update(status="FAIL"),
            "status must be PASS",
            id="seal-status-fail",
        ),
        pytest.param(
            lambda payload: payload.pop("eps1_attribution_triple"),
            "missing required keys: eps1_attribution_triple",
            id="seal-required-key-missing",
        ),
        pytest.param(
            lambda payload: payload["branch_table"]["MES_NG"].update(
                status="VERIFIED_NON_GEODESIC"
            ),
            "MES_NG.status must be UNVERIFIED_NON_GEODESIC",
            id="seal-branch-status-promoted",
        ),
    ],
)
def test_hash_bound_but_semantically_invalid_witness_seal_is_blocked(
    tmp_path: Path,
    mutation: object,
    detail: str,
) -> None:
    registry = _copy_current_registry_inputs(tmp_path)
    seal_path = tmp_path / registry.egs3_branch_witness.seal.path
    payload = json.loads(seal_path.read_text(encoding="utf-8"))
    mutation(payload)  # type: ignore[operator]
    seal_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    witness = replace(
        registry.egs3_branch_witness,
        seal=SourceHashBinding(
            registry.egs3_branch_witness.seal.path,
            SourceAvailability.AVAILABLE,
            _digest(seal_path),
        ),
    )
    custom = replace(registry, egs3_branch_witness=witness)

    report = validate_mes_successor_registry(tmp_path, custom)
    invalid = [
        finding.detail
        for finding in report.findings
        if finding.code is MesConsumerIssueCode.DIAGNOSTIC_WITNESS_INVALID
    ]
    assert any(detail in finding_detail for finding_detail in invalid)
    assert report.release_allowed is False


def test_missing_successor_cannot_spoof_pass_or_authority() -> None:
    missing = SourceHashBinding("future.py", SourceAvailability.MISSING, None)
    with pytest.raises(MesRegistryError, match="process NOT_RUN"):
        MesSuccessorPointer(
            CURRENT_SUCCESSOR_ID,
            missing,
            MesProcessResult.PASS,
            MesScientificAuthorityStatus.BLOCKED_PENDING_PR124,
        )
    with pytest.raises(MesRegistryError, match="remain blocked"):
        MesSuccessorPointer(
            CURRENT_SUCCESSOR_ID,
            missing,
            MesProcessResult.NOT_RUN,
            MesScientificAuthorityStatus.AUTHORIZED_BY_PR124,
        )


def test_source_binding_rejects_unhashed_available_and_hashed_missing() -> None:
    with pytest.raises(MesRegistryError, match="SHA-256"):
        SourceHashBinding("source.py", SourceAvailability.AVAILABLE, None)
    with pytest.raises(MesRegistryError, match="MISSING source"):
        SourceHashBinding("source.py", SourceAvailability.MISSING, "0" * 64)
    with pytest.raises(MesRegistryError, match="repository-relative"):
        SourceHashBinding("../source.py", SourceAvailability.MISSING, None)


def test_hash_mutation_blocks_an_otherwise_typed_consumer(tmp_path: Path) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
    )
    (tmp_path / "consumer.py").write_text("MUTATED = True\n", encoding="utf-8")

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value in finding_codes(report)
    assert report.release_allowed is False


def test_direct_legacy_import_is_a_bypass_even_with_typed_import(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "from htt.tsc.admissibility.three_bound_hierarchy import W2_max\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    codes = finding_codes(report)
    assert MesConsumerIssueCode.SUCCESSOR_BYPASS.value in codes
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value not in codes
    assert report.release_allowed is False


def test_egs3_import_is_process_evidence_bypass_not_authority(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "from htt.obsstat.egs3_mes_branch_registry import branch_table\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.SUCCESSOR_BYPASS.value in finding_codes(report)


@pytest.mark.parametrize(
    "literal",
    [
        "(Fraction(3, 4), Fraction(2), Fraction(2, 7))",
        "('3/4', '1', '3/14')",
        "(3 / 4, 2, 2 / 7)",
        "(3. / 4, 2., 2. / 7)",
    ],
)
def test_copied_stale_triple_is_blocked(tmp_path: Path, literal: str) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from fractions import Fraction\n"
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        f"STALE = {literal}\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.STALE_MES_TRIPLE.value in finding_codes(report)
    assert report.release_allowed is False


def test_dead_or_bare_registry_call_cannot_clear_stale_literal_blocker(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "if False:\n"
        "    DEAD = current_mes_successor_registry().successor\n"
        "current_mes_successor_registry()\n"
        "current_mes_successor_registry().successor\n"
        "SHORT_CIRCUIT = False and current_mes_successor_registry().successor\n"
        "DEAD_IFEXP = None if True else current_mes_successor_registry().successor\n"
        "STALE = (3 / 4, 2, 2 / 7)\n",
    )

    codes = finding_codes(scan_declared_mes_consumers(tmp_path, (declaration,)))
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value in codes
    assert MesConsumerIssueCode.STALE_MES_TRIPLE.value in codes


@pytest.mark.parametrize(
    "decoy",
    [
        pytest.param(
            "POINTER = current_mes_successor_registry().successor\n",
            id="unused-module-binding",
        ),
        pytest.param(
            "def unused():\n" "    return current_mes_successor_registry().successor\n",
            id="never-called-function",
        ),
        pytest.param(
            "if 0:\n" "    POINTER = current_mes_successor_registry().successor\n",
            id="if-zero",
        ),
        pytest.param(
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    POINTER = current_mes_successor_registry().successor\n",
            id="type-checking-only",
        ),
    ],
)
def test_dead_pointer_cannot_clear_inline_stale_affine_formula(
    tmp_path: Path,
    decoy: str,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        f"{decoy}"
        "def B_omega(e1, e2, e3):\n"
        "    return (3 / 4) * e1 + 2 * e2 + (2 / 7) * e3\n",
    )

    codes = finding_codes(scan_declared_mes_consumers(tmp_path, (declaration,)))
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value in codes
    assert MesConsumerIssueCode.STALE_MES_TRIPLE.value in codes


def test_clean_typed_consumer_has_no_pointer_or_literal_blocker(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    codes = finding_codes(report)
    # tmp copies lack the PR-124 receipt artifacts, so the authority blocker
    # is present; the CONSUMER itself must be clean.
    assert TMP_AUTHORITY_BLOCKER in codes
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value not in codes
    assert MesConsumerIssueCode.SUCCESSOR_BYPASS.value not in codes
    assert MesConsumerIssueCode.STALE_MES_TRIPLE.value not in codes
    assert report.release_allowed is False


def test_caller_supplied_registry_is_never_a_release_trust_root(
    tmp_path: Path,
) -> None:
    registry = _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,), registry)
    assert MesConsumerIssueCode.UNTRUSTED_REGISTRY_OVERRIDE.value in finding_codes(
        report
    )
    assert report.release_allowed is False


def test_zero_consumer_set_cannot_pass_vacuously(tmp_path: Path) -> None:
    _copy_current_registry_inputs(tmp_path)

    report = scan_declared_mes_consumers(tmp_path, ())

    assert MesConsumerIssueCode.NO_ACTIVE_CONSUMERS_DECLARED.value in finding_codes(
        report
    )
    assert report.release_allowed is False


def test_successor_id_and_pointer_import_are_independent_gates(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "VALUE = 1\n",
        consumer_id="bad-pointer",
    )
    declaration = replace(declaration, expected_successor_id="mes.some-other-pointer")

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    codes = finding_codes(report)
    assert MesConsumerIssueCode.SUCCESSOR_ID_MISMATCH.value in codes
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value in codes


def test_import_only_does_not_spoof_typed_successor_consumption(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value in finding_codes(report)


def test_module_alias_call_counts_as_typed_successor_consumption(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "import common.mes_successor_registry as mes_registry\n"
        "POINTER = mes_registry.current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value not in finding_codes(
        report
    )


def test_dynamic_legacy_import_is_a_bypass(tmp_path: Path) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from importlib import import_module\n"
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "LEGACY = import_module('htt.tsc.admissibility.three_bound_hierarchy')\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.SUCCESSOR_BYPASS.value in finding_codes(report)


def test_constant_folded_dynamic_legacy_import_is_a_bypass(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from importlib import import_module\n"
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "LEGACY = import_module('htt.tsc.admissibility.' + 'three_bound_hierarchy')\n",
    )

    report = scan_declared_mes_consumers(tmp_path, (declaration,))
    assert MesConsumerIssueCode.SUCCESSOR_BYPASS.value in finding_codes(report)
    assert MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value not in finding_codes(
        report
    )


def test_self_asserted_successor_source_is_not_auto_promoted(
    tmp_path: Path,
) -> None:
    """Replacing the pinned authority module with self-asserted bytes is a
    hash mismatch, never a promotion (PR-124 pin discipline)."""
    registry = _copy_current_registry_inputs(tmp_path)
    planned = tmp_path / registry.successor.source.path
    planned.parent.mkdir(parents=True, exist_ok=True)
    planned.write_text("AUTHORITY = 'self-asserted'\n", encoding="utf-8")

    report = validate_mes_successor_registry(tmp_path)
    codes = finding_codes(report)
    assert MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value in codes
    assert TMP_AUTHORITY_BLOCKER in codes
    assert report.release_allowed is False


def test_inventory_is_exact_hash_pinned_and_matches_ast_discovery() -> None:
    payload = _inventory()
    declarations = _inventory_declarations(payload)
    migration = _consumer_migration()

    report = scan_declared_mes_consumers(REPO_ROOT, declarations)
    forbidden = {
        MesConsumerIssueCode.SOURCE_MISSING.value,
        MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value,
        MesConsumerIssueCode.INVENTORY_INVALID.value,
        MesConsumerIssueCode.UNDECLARED_ACTIVE_CONSUMER.value,
        MesConsumerIssueCode.DECLARED_CONSUMER_NOT_DISCOVERED.value,
        MesConsumerIssueCode.EXCLUSION_HASH_MISMATCH.value,
        MesConsumerIssueCode.CONSUMER_PARSE_ERROR.value,
    }
    assert finding_codes(report).isdisjoint(forbidden)
    assert len(declarations) == 22
    reclassified_ids = {
        row["consumer_id"] for row in migration["legacy_reclassifications"]
    }
    new_ids = {row["consumer_id"] for row in migration["new_bindings"]}
    retained_ids = {row.consumer_id for row in declarations} - reclassified_ids
    assert report.consumers_scanned == len(retained_ids | new_ids) == 7
    assert tuple(payload["active_python_roots"]) == DEFAULT_ACTIVE_PYTHON_ROOTS
    assert migration["schema"] == "htt.mes_consumer_migration.v1"
    assert migration["authority"] == "PR-252"
    assert migration["claim_effect"] == "none"

    supersession = _consumer_supersession()
    assert supersession["schema"] == "htt.mes_consumer_supersession.v1"
    assert supersession["authority"] == "PR-248"
    replacement_by_id = {
        row["consumer_id"]: row for row in supersession["bindings"]
    }
    migration_by_id = {
        row["consumer_id"]: row
        for section in ("bindings", "legacy_reclassifications")
        for row in migration[section]
    }
    for row in payload["active_consumers"]:
        assert set(row) == {"consumer_id", "path", "sha256"}
        replacement = replacement_by_id.get(row["consumer_id"])
        prior_sha256 = row["sha256"]
        if replacement is not None:
            assert replacement["path"] == row["path"]
            assert replacement["prior_sha256"] == row["sha256"]
            prior_sha256 = replacement["sha256"]
        transition = migration_by_id.get(row["consumer_id"])
        if transition is not None:
            assert transition["path"] == row["path"]
            assert transition["prior_sha256"] == prior_sha256
            prior_sha256 = transition["sha256"]
        assert prior_sha256 == _digest(REPO_ROOT / row["path"])

    for row in migration["new_bindings"]:
        assert row["expected_successor_id"] == CURRENT_SUCCESSOR_ID
        assert row["sha256"] == _digest(REPO_ROOT / row["path"])

    exclusion_transition_by_id = {
        row["exclusion_id"]: row for row in migration["exclusion_bindings"]
    }
    for row in payload["excluded_consumers"]:
        assert set(row) == {"exclusion_id", "path", "sha256", "reason"}
        assert row["path"].endswith(".py")
        transition = exclusion_transition_by_id.get(row["exclusion_id"])
        expected_sha256 = row["sha256"]
        if transition is not None:
            assert transition["path"] == row["path"]
            assert transition["prior_sha256"] == expected_sha256
            expected_sha256 = transition["sha256"]
        assert expected_sha256 == _digest(REPO_ROOT / row["path"])


def test_inventory_declaration_comparison_is_order_independent() -> None:
    payload = _inventory()
    declarations = _inventory_declarations(payload)

    report = scan_declared_mes_consumers(REPO_ROOT, tuple(reversed(declarations)))

    assert report.consumers_scanned == 7
    assert MesConsumerIssueCode.INVENTORY_INVALID.value not in finding_codes(report)


def test_inventory_enumerates_live_figures_without_directory_exclusion() -> None:
    payload = _inventory()
    active_paths = {row["path"] for row in payload["active_consumers"]}
    excluded_paths = {row["path"] for row in payload["excluded_consumers"]}
    expected_figures = {
        "htt/htt/htt/figures/fig_3D_constraint_volume.py",
        "htt/htt/htt/figures/fig_4D_projection_atlas.py",
        "htt/htt/htt/figures/fig_MES_three_bounds.py",
        "htt/htt/htt/figures/fig_nonlinear_heatmap_vorticity_accel.py",
        "htt/htt/htt/figures/fig_sigma_accel_contour.py",
        "htt/htt/htt/figures/fig_sigma_omega_contour.py",
        "htt/htt/htt/figures/fig_type_by_type_summary.py",
        "htt/htt/htt/figures/fig_vorticity_hierarchy.py",
    }

    assert expected_figures <= active_paths
    assert not any(path.endswith("/figures") for path in excluded_paths)
    assert all(path.endswith(".py") for path in excluded_paths)
    assert "legacy_or_diagnostic_exclusions" not in payload


def test_ast_discovery_reports_undeclared_exact_mes_consumer(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "def B_sigma(value):\n"
        "    return value\n",
        relative_path="active/declared.py",
    )
    undeclared = tmp_path / "active/undeclared.py"
    undeclared.write_text("def B_omega(value):\n    return value\n", encoding="utf-8")

    report = scan_declared_mes_consumers(
        tmp_path,
        (declaration,),
        exclusions=(),
        discovery_roots=("active",),
    )
    findings = [
        finding
        for finding in report.findings
        if finding.code is MesConsumerIssueCode.UNDECLARED_ACTIVE_CONSUMER
    ]
    assert [finding.subject for finding in findings] == ["active/undeclared.py"]


def test_ast_discovery_rejects_declared_decoy_with_only_non_mes_import(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "from bass.observational.planck_mes_bounds import T_CMB_K\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
        relative_path="active/decoy.py",
    )

    report = scan_declared_mes_consumers(
        tmp_path,
        (declaration,),
        exclusions=(),
        discovery_roots=("active",),
    )
    assert MesConsumerIssueCode.DECLARED_CONSUMER_NOT_DISCOVERED.value in finding_codes(
        report
    )


def test_excluded_consumer_hash_mutation_is_a_distinct_blocker(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "def B_sigma(value):\n"
        "    return value\n",
        relative_path="active/declared.py",
    )
    excluded_path = tmp_path / "active/excluded.py"
    excluded_path.write_text(
        "def B_omega(value):\n    return value\n", encoding="utf-8"
    )
    exclusion = MesConsumerExclusion(
        exclusion_id="diagnostic.excluded",
        source=SourceHashBinding(
            "active/excluded.py",
            SourceAvailability.AVAILABLE,
            _digest(excluded_path),
        ),
        reason="synthetic diagnostic fixture",
    )
    excluded_path.write_text(
        "def B_accel(value):\n    return value\n", encoding="utf-8"
    )

    report = scan_declared_mes_consumers(
        tmp_path,
        (declaration,),
        exclusions=(exclusion,),
        discovery_roots=("active",),
    )
    assert MesConsumerIssueCode.EXCLUSION_HASH_MISMATCH.value in finding_codes(report)


def test_consumer_exclusion_cannot_name_a_broad_directory() -> None:
    with pytest.raises(MesRegistryError, match="one Python file"):
        MesConsumerExclusion(
            exclusion_id="broad-directory",
            source=SourceHashBinding(
                "htt/htt/htt/figures",
                SourceAvailability.AVAILABLE,
                "0" * 64,
            ),
            reason="not allowed",
        )


def test_repository_inventory_roots_and_exclusions_cannot_be_overridden() -> None:
    payload = _inventory()
    declarations = _inventory_declarations(payload)

    with pytest.raises(MesRegistryError, match="exclusions cannot replace"):
        scan_declared_mes_consumers(REPO_ROOT, declarations, exclusions=())
    with pytest.raises(MesRegistryError, match="roots cannot replace"):
        scan_declared_mes_consumers(
            REPO_ROOT,
            declarations,
            discovery_roots=("htt/htt/htt",),
        )


def test_yaml_active_hash_cannot_be_replaced_by_caller_declaration(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n"
        "def B_sigma(value):\n"
        "    return value\n",
        relative_path="active/consumer.py",
    )
    stale_hash = "0" * 64
    inventory = tmp_path / DEFAULT_CONSUMER_INVENTORY_PATH
    inventory.parent.mkdir(parents=True, exist_ok=True)
    inventory.write_text(
        yaml.safe_dump(
            {
                "schema": "htt.long_horizon.pr122_active_mes_consumers.v1",
                "successor_id": CURRENT_SUCCESSOR_ID,
                "active_python_roots": ["active"],
                "active_consumers": [
                    {
                        "consumer_id": declaration.consumer_id,
                        "path": declaration.source.path,
                        "sha256": stale_hash,
                    }
                ],
                "excluded_consumers": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(MesRegistryError, match="declarations cannot replace"):
        scan_declared_mes_consumers(tmp_path, (declaration,))

    stale_declaration = replace(
        declaration,
        source=SourceHashBinding(
            declaration.source.path,
            SourceAvailability.AVAILABLE,
            stale_hash,
        ),
    )
    report = scan_declared_mes_consumers(tmp_path, (stale_declaration,))
    assert MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value in finding_codes(report)


def test_inventory_symlink_cannot_disable_repository_controls(
    tmp_path: Path,
) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
    )
    inventory = tmp_path / DEFAULT_CONSUMER_INVENTORY_PATH
    inventory.parent.mkdir(parents=True, exist_ok=True)
    target = tmp_path / "inventory-target.yaml"
    target.write_text("{}\n", encoding="utf-8")
    inventory.symlink_to(target)

    with pytest.raises(MesRegistryError, match="regular repository file"):
        scan_declared_mes_consumers(tmp_path, (declaration,))


def test_missing_discovery_root_is_an_inventory_blocker(tmp_path: Path) -> None:
    _copy_current_registry_inputs(tmp_path)
    declaration = _write_consumer(
        tmp_path,
        "from common.mes_successor_registry import current_mes_successor_registry\n"
        "POINTER = current_mes_successor_registry().successor\n"
        "POINTER_ID = POINTER.successor_id\n",
    )

    report = scan_declared_mes_consumers(
        tmp_path,
        (declaration,),
        exclusions=(),
        discovery_roots=("missing-active-root",),
    )
    assert MesConsumerIssueCode.INVENTORY_INVALID.value in finding_codes(report)
