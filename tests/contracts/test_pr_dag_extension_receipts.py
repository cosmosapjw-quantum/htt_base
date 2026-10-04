"""Registered extension receipts are optional but retain terminal-state checks."""

from pathlib import Path

import pytest

from scripts.codex_harness.validate_pr_dag import (
    DagInfo,
    _validate_rescue_status,
    load_yaml,
    validate_backlog,
    validate_long_horizon_rescue_slice,
)


REPO = Path(__file__).resolve().parents[2]
EXTENSION = "PR-GR-STATISTICS-CAS-HANDOFF"


def _info(pr_id: str = EXTENSION) -> DagInfo:
    return DagInfo(
        prs=({"id": pr_id},),
        ids=(pr_id,),
        order=(pr_id,),
        prereqs={pr_id: ()},
        children={pr_id: ()},
    )


def _status(pr_id: str = EXTENSION, *, bucket: str = "completed") -> dict:
    return {
        bucket: [pr_id],
        "execution_resolutions": {
            pr_id: {"resolution": "COMPLETED_SUCCESS", "receipt": "evidence.json"}
        },
    }


def test_current_registered_extension_receipts_pass_strict_validation() -> None:
    backlog = load_yaml(REPO / "docs/codex_handoff/pr_backlog.yaml")
    status = load_yaml(REPO / "docs/codex_handoff/pr_status.yaml")
    validate_long_horizon_rescue_slice(backlog, validate_backlog(backlog), status=status)


def test_registered_extension_receipt_is_accepted() -> None:
    _validate_rescue_status(_status(), _info(), extension_ids={EXTENSION})


def test_registered_extension_receipt_is_optional() -> None:
    _validate_rescue_status(
        {"completed": [EXTENSION]}, _info(), extension_ids={EXTENSION}
    )


def test_unregistered_extension_cannot_supply_receipt() -> None:
    with pytest.raises(ValueError, match="restricted to rescue cards or registered"):
        _validate_rescue_status(_status(), _info())


def test_unknown_extension_registration_is_rejected() -> None:
    with pytest.raises(ValueError, match="extensions contain unknown PR ids"):
        _validate_rescue_status(_status(), _info(), extension_ids={"PR-UNKNOWN"})


def test_nonterminal_extension_cannot_supply_receipt() -> None:
    with pytest.raises(ValueError, match="non-terminal PR"):
        _validate_rescue_status(
            _status(bucket="pending"), _info(), extension_ids={EXTENSION}
        )


def test_extension_receipt_must_match_terminal_bucket() -> None:
    with pytest.raises(ValueError, match="terminal bucket requires"):
        _validate_rescue_status(
            _status(bucket="blocked"), _info(), extension_ids={EXTENSION}
        )


@pytest.mark.parametrize("pointer", [None, "", "   "])
def test_extension_receipt_pointer_must_be_nonempty(pointer: str | None) -> None:
    status = _status()
    status["execution_resolutions"][EXTENSION]["receipt"] = pointer
    with pytest.raises(ValueError, match="receipt pointer must be nonempty"):
        _validate_rescue_status(status, _info(), extension_ids={EXTENSION})


def test_numeric_rescue_receipt_remains_required() -> None:
    with pytest.raises(ValueError, match="terminal rescue cards require"):
        _validate_rescue_status({"completed": ["PR-119"]}, _info("PR-119"))
