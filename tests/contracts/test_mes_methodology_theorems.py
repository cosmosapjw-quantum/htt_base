from __future__ import annotations

import hashlib
import json
from pathlib import Path
from copy import deepcopy

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE_LEDGER = (
    ROOT
    / "docs/codex_handoff/mes_methodology_recovery/RESEARCH_DECISION_LEDGER.yaml"
)
THEOREM_LEDGER = (
    ROOT / "docs/research_program/post_pr275/mes_methodology_theorems.yaml"
)
RECEIPT = ROOT / "docs/generated/mes_methodology_recovery/theory_receipts.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_portable_cas_bindings(payload: dict[str, object]) -> None:
    cas = payload["four_axis_cas"]
    assert isinstance(cas, dict)
    for path_key, sha_key in (
        ("contract_path", "contract_sha256"),
        ("run_spec_path", "run_spec_sha256"),
        ("adjudication_path", "adjudication_sha256"),
    ):
        path = ROOT / str(cas[path_key])
        assert path.is_file()
        assert _sha256(path) == cas[sha_key]

    axis_paths = {
        "wolfram_xact": (
            "docs/generated/mes_methodology_recovery/cas/axes/"
            "wolfram_xact/axis_program.wls"
        ),
        "sympy": (
            "docs/generated/mes_methodology_recovery/cas/axes/"
            "sympy/axis_program.py"
        ),
        "sage_singular": (
            "docs/generated/mes_methodology_recovery/cas/axes/"
            "sage_singular/axis_program.sage"
        ),
        "lean_source": (
            "docs/generated/mes_methodology_recovery/cas/axes/"
            "lean/PR323MESMethodologyCore.lean"
        ),
        "lean_runner": (
            "docs/generated/mes_methodology_recovery/cas/axes/lean/axis_program"
        ),
    }
    for axis, relative in axis_paths.items():
        assert _sha256(ROOT / relative) == cas["axis_program_sha256"][axis]


def test_integrated_ledger_preserves_all_four_status_axes() -> None:
    source = yaml.safe_load(SOURCE_LEDGER.read_text(encoding="utf-8"))
    integrated = yaml.safe_load(THEOREM_LEDGER.read_text(encoding="utf-8"))

    assert integrated["schema"] == "htt.mes_methodology.theorems.v1"
    assert integrated["authority"]["canonical_work_unit_id"] == "PR-323"
    assert integrated["authority"]["planning_alias"] == "MSI-WU-001"
    assert integrated["authority"]["source_sha256"] == _sha256(SOURCE_LEDGER)
    assert integrated["status_axes"] == source["status_axes"]

    source_rows = source["decisions"]
    rows = integrated["decisions"]
    assert [row["id"] for row in rows] == [row["id"] for row in source_rows]
    assert len(rows) == 14
    for source_row, row in zip(source_rows, rows, strict=True):
        for axis in source["status_axes"]:
            assert row[axis] == source_row[axis]
        if "statement" in source_row:
            assert row["source_statement"] == source_row["statement"]
        assert row["current_receipt"]["claim_promotion"] is False
        assert row["current_receipt"]["evidence_refs"]


def test_theory_receipt_binds_exact_replay_and_four_axis_cas() -> None:
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))

    assert payload["schema"] == "htt.mes_methodology.theory_receipts.v1"
    assert payload["canonical_work_unit_id"] == "PR-323"
    assert payload["planning_alias"] == "MSI-WU-001"
    assert payload["source_identity"]["pr411_sha"] == (
        "5a3825f903546891fd90e3d708481707d59babf4"
    )
    assert payload["source_identity"]["wolfram_source_sha256"] == _sha256(
        ROOT / "wolfram/mes_methodology_recovery_proofs.wls"
    )
    assert payload["wolfram_replay"]["exit_code"] == 0
    assert payload["wolfram_replay"]["all_pass"] is True
    assert set(payload["wolfram_replay"]["checks"].values()) == {True}

    cas = payload["four_axis_cas"]
    assert cas["aggregate_status"] == "CAS_4AXIS_PASS"
    assert cas["claim_promotion_cas_requirement"] == "SATISFIED"
    assert cas["claim_promotion_from_this_receipt"] is False
    assert cas["required_axes"] == [
        "wolfram_xact",
        "sympy",
        "sage_singular",
        "lean",
    ]
    assert cas["axis_statuses"] == {
        "wolfram_xact": "PASS",
        "sympy": "PASS",
        "sage_singular": "PASS",
        "lean": "PASS",
    }
    _assert_portable_cas_bindings(payload)

    adjudication = json.loads(
        (ROOT / cas["adjudication_path"]).read_text(encoding="utf-8")
    )
    assert adjudication["verification_state"] == "RUNNER_OBSERVED_EXECUTION"
    assert adjudication["missing_axes"] == []
    assert adjudication["exceptions_applied"] == []
    assert adjudication["errors"] == []


def test_content_binding_rejects_a_mutated_contract_digest() -> None:
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    mutated = deepcopy(payload)
    mutated["four_axis_cas"]["contract_sha256"] = "0" * 64
    try:
        _assert_portable_cas_bindings(mutated)
    except AssertionError:
        pass
    else:  # pragma: no cover - the negative control must never survive
        raise AssertionError("mutated CAS contract digest was accepted")


def test_unfinished_local_formal_tasks_remain_typed_blockers() -> None:
    payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    tasks = {row["id"]: row for row in payload["local_formal_tasks"]}

    assert set(tasks) == {
        "LOCAL-XACT-001",
        "LOCAL-XACT-002",
        "LOCAL-SAGE-001",
        "LOCAL-LEAN-001",
        "LOCAL-LEAN-002",
        "LOCAL-ROCQ-001",
        "LOCAL-MES-NG-001",
    }
    assert tasks["LOCAL-LEAN-001"]["status"] in {
        "PASS_SCOPED_CORE",
        "BLOCKED_LEAN_EQUIVARIANCE",
    }
    assert tasks["LOCAL-XACT-001"]["status"] == (
        "BLOCKED_FRAME_TRANSFORM_DERIVATION"
    )
    assert tasks["LOCAL-XACT-002"]["status"] == (
        "BLOCKED_BRANCH_CONSTRAINT_CLOSURE"
    )
    assert tasks["LOCAL-SAGE-001"]["status"] == "BLOCKED_VTT8_DISCRETE_BRANCH"
    assert tasks["LOCAL-LEAN-002"]["status"] == (
        "BLOCKED_LEAN_REVERSE_MARTINGALE"
    )
    assert tasks["LOCAL-ROCQ-001"]["status"] in {
        "PASS_SCOPED_CORE",
        "BLOCKED_ROCQ_FINITE_RANK_OR_MOMENT_CONE",
    }
    assert tasks["LOCAL-MES-NG-001"]["status"] == "BLOCKED_PRIMARY_SOURCE"
    assert tasks["LOCAL-MES-NG-001"]["executed"] is False


def test_receipt_does_not_collapse_truth_replay_or_release() -> None:
    text = RECEIPT.read_text(encoding="utf-8")
    lowered = text.lower()
    payload = json.loads(text)

    assert payload["claim_ceiling"] == "diagnostic_only_methodology_receipt"
    assert payload["scientific_status_changed"] is False
    assert payload["release_authorized"] is False
    assert payload["native_solver_result"] is False
    assert payload["family_identification"] is False
    assert payload["non_geodesic_mes_promoted"] is False
    for forbidden in (
        "bianchi geometry detected",
        "bianchi family identified",
        "external transfer validated as native",
    ):
        assert forbidden not in lowered
