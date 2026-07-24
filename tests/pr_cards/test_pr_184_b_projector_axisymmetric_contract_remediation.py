"""PR-184 card gates: premise-complete B-projector contract remediation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

from bass.pr184_axisym_contract import (  # noqa: E402
    PR172_FIXTURE_VALUE,
    PremiseViolation,
    check_axisymmetric_premise,
    run_adjudication,
)

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr184_spec.yaml"
CARD = REPO / "docs/generated/pr184_result_card.json"
ADAPTER = REPO / "htt/bass/los/b_mode_projector.py"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_frozen_adapter_matches_pr172_pin() -> None:
    """Kill condition: the production adapter must stay byte-identical."""
    assert _sha(ADAPTER) == (
        "4f0268892e59c0145e59e822fb9d6d1828fbb375f8a3d67d5fbb170cae6dacdf"
    )


def test_adjudication_terminal_and_witnesses() -> None:
    result = run_adjudication()
    assert result["terminal"] == (
        "PREMISE_COMPLETE_CONTRACT_REGISTERED_IMPLEMENTATION_UPHELD"
    )
    assert all(result["checks"].values())
    witnesses = result["witnesses"]
    assert witnesses["consistent_configuration_output_max_abs"] == 0.0
    assert witnesses["pr172_fixture_output_max_abs"] == PR172_FIXTURE_VALUE
    assert witnesses["pr172_fixture_output_support_m_indices"] == [0]


def test_premise_checker_negative_paths() -> None:
    sigma_axisym = np.zeros((9, 5))
    sigma_axisym[:, 2] = 1.0
    b_zero = np.zeros((9, 3, 5))
    check_axisymmetric_premise(sigma_axisym, b_zero)  # must not raise

    b_bad = np.zeros((9, 3, 5))
    b_bad[:, 2, 0] = 1.0
    with pytest.raises(PremiseViolation, match="B-tower history is nonzero"):
        check_axisymmetric_premise(sigma_axisym, b_bad)

    sigma_bad = np.zeros((9, 5))
    sigma_bad[:, 2] = 1.0
    sigma_bad[:, 3] = 0.5  # sigma_{2,+1} != 0
    with pytest.raises(PremiseViolation, match="not axisymmetric"):
        check_axisymmetric_premise(sigma_bad, b_zero)


@pytest.mark.parametrize(
    ("sigma", "b_history", "message"),
    [
        (np.zeros((9, 4)), np.zeros((9, 3, 5)), "sigma_2M_history"),
        (np.zeros((9, 5)), np.zeros((9, 1, 5)), "include ell=2"),
        (np.zeros((9, 5)), np.zeros((1, 3, 5)), "share a nonempty n_eta"),
        (np.zeros((0, 5)), np.zeros((0, 3, 5)), "share a nonempty n_eta"),
    ],
)
def test_premise_checker_rejects_non_projector_shapes(
    sigma: np.ndarray, b_history: np.ndarray, message: str
) -> None:
    with pytest.raises(PremiseViolation, match=message):
        check_axisymmetric_premise(sigma, b_history)


def test_pr172_receipts_untouched_and_never_relabeled() -> None:
    status = (REPO / "docs/codex_handoff/pr_status.yaml").read_text()
    assert "COMPLETED_FAILED_WITH_RECEIPT" in status
    block = status.split("  PR-172:\n")[1].split("  PR-171:\n")[0]
    assert "success_dependency_satisfied: false" in block
    card = json.loads(CARD.read_text())
    joined = json.dumps(card)
    assert "never relabeled" in joined
    assert "UNDERDEFINED_NOT_TESTED" in joined


def test_card_is_byte_current_under_read_only_check() -> None:
    proc = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr184_axisym_contract.py"),
            "--check",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
    assert payload["terminal"] == (
        "PREMISE_COMPLETE_CONTRACT_REGISTERED_IMPLEMENTATION_UPHELD"
    )


def test_spec_bound_and_gates() -> None:
    card = json.loads(CARD.read_text())
    assert card["metadata"]["spec_sha256"] == _sha(SPEC)
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["claim_level"]["level"] == "C1"
    assert "frozen_before_result: true" in SPEC.read_text()
