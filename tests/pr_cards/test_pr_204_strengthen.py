"""PR-204 strict-band injection-contract unit tests."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "htt") not in sys.path:
    sys.path.insert(0, str(REPO / "htt"))

from obsstat.act_inband_injection import (  # noqa: E402
    AXIS_NAMES,
    analyze_injection_records,
    full_sky_real_y2_templates,
    injection_assignment,
    terminal_from_analysis,
)
from obsstat.act_inband_modulation import ActInbandModulationError  # noqa: E402
from obsstat.act_inband_modulation import canonical_sha256  # noqa: E402


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(simulation_id: int, response_scale: float = 1.0) -> dict:
    assignment = injection_assignment(simulation_id)
    zero = np.zeros(5, dtype=float)
    delta = np.zeros(5, dtype=float)
    delta[assignment.axis_index] = assignment.amplitude * response_scale
    feature_zero = {
        "q_raw": zero.tolist(),
        "q_controlled": zero.tolist(),
    }
    feature_injected = {
        "q_raw": delta.tolist(),
        "q_controlled": delta.tolist(),
    }
    return {
        "simulation_id": simulation_id,
        "assignment": {
            "axis_index": assignment.axis_index,
            "axis_name": assignment.axis_name,
            "within_axis_index": assignment.within_axis_index,
            "amplitude": assignment.amplitude,
            "split": assignment.split,
        },
        "baseline": feature_zero,
        "injected": feature_injected,
    }


def test_assignment_is_balanced_and_disjoint() -> None:
    assignments = [injection_assignment(index) for index in range(1, 401)]
    assert Counter(row.axis_name for row in assignments) == {
        name: 80 for name in AXIS_NAMES
    }
    for axis in range(5):
        rows = [row for row in assignments if row.axis_index == axis]
        assert Counter(row.split for row in rows) == {
            "response_fit": 20,
            "coverage_calibration": 20,
            "evaluation": 40,
        }
        for split, count in (
            ("response_fit", 10),
            ("coverage_calibration", 10),
            ("evaluation", 20),
        ):
            selected = [row for row in rows if row.split == split]
            assert sum(row.amplitude > 0 for row in selected) == count
            assert sum(row.amplitude < 0 for row in selected) == count


def test_real_y2_templates_are_finite_and_centered() -> None:
    templates = full_sky_real_y2_templates(8)
    assert templates.shape == (5, 12 * 8 * 8)
    assert np.all(np.isfinite(templates))
    assert np.max(np.abs(np.mean(templates, axis=1))) < 1.0e-3
    gram = templates @ templates.T / templates.shape[1]
    assert np.max(np.abs(gram - np.diag(np.diag(gram)))) < 1.0e-4
    assert np.min(1.0 - 0.08 * np.abs(templates)) > 0.9


def test_exact_synthetic_response_and_coverage_pass() -> None:
    analysis = analyze_injection_records(
        [_record(index) for index in range(1, 401)]
    )
    assert np.allclose(analysis["controlled_response_matrix"], np.eye(5))
    assert analysis["response_gate_passed"] is True
    assert analysis["coverage_gate_passed"] is True
    assert analysis["mask_sensitivity_gate_passed"] is True
    assert terminal_from_analysis(analysis) == (
        "AUTHOR_EVIDENCE_READY_VALIDATED_BAND_RESPONSE_CALIBRATED"
    )


def test_response_failure_is_fail_closed() -> None:
    records = [_record(index) for index in range(1, 401)]
    for row in records:
        if row["assignment"]["axis_index"] == 0:
            amplitude = row["assignment"]["amplitude"]
            row["injected"]["q_raw"][0] = 0.5 * amplitude
            row["injected"]["q_controlled"][0] = 0.5 * amplitude
    analysis = analyze_injection_records(records)
    assert analysis["response_gate_passed"] is False
    assert terminal_from_analysis(analysis) == (
        "BLOCKED_INBAND_INJECTION_RESPONSE_FAILURE"
    )


def test_coverage_failure_is_fail_closed() -> None:
    records = [_record(index) for index in range(1, 401)]
    for row in records:
        if row["assignment"]["split"] == "evaluation":
            axis = row["assignment"]["axis_index"]
            row["injected"]["q_raw"][axis] *= 0.5
            row["injected"]["q_controlled"][axis] *= 0.5
    analysis = analyze_injection_records(records)
    assert analysis["response_gate_passed"] is True
    assert analysis["coverage_gate_passed"] is False
    assert terminal_from_analysis(analysis) == (
        "BLOCKED_INBAND_INJECTION_COVERAGE_FAILURE"
    )


def test_mask_sensitivity_failure_is_fail_closed() -> None:
    records = [_record(index) for index in range(1, 401)]
    for row in records:
        if row["assignment"]["split"] == "evaluation":
            axis = row["assignment"]["axis_index"]
            row["injected"]["q_raw"][axis] *= 2.0
    analysis = analyze_injection_records(records)
    assert analysis["response_gate_passed"] is True
    assert analysis["coverage_gate_passed"] is True
    assert analysis["mask_sensitivity_gate_passed"] is False
    assert terminal_from_analysis(analysis) == (
        "BLOCKED_MASK_SENSITIVITY_COMPARABLE_TO_INJECTION"
    )


def test_assignment_or_order_drift_is_rejected() -> None:
    records = [_record(index) for index in range(1, 401)]
    records[0], records[1] = records[1], records[0]
    with pytest.raises(ActInbandModulationError, match="order drift"):
        analyze_injection_records(records)


def test_spec_keeps_raw_qe_and_claim_boundary_open() -> None:
    spec = yaml.safe_load(
        (
            REPO
            / "docs/research_program/strengthening/pr204_spec.yaml"
        ).read_text(encoding="utf-8")
    )
    assert spec["route"]["raw_qe_selected"] is False
    assert spec["claim_tier"] == "exploratory"
    assert spec["readiness_ceiling"] == "EVIDENCE_READY"
    assert spec["independence_gate"] == "OPEN"
    assert spec["public_use"] is False


def test_actual_calibration_preserves_the_coverage_failure() -> None:
    card = _json(
        REPO / "docs/generated/pr204_injection_calibration.json"
    )
    assert card["process_execution_status"] == (
        "PASS_COMPLETE_400_PAIRED_INJECTIONS"
    )
    assert card["unit_count"] == 400
    assert card["analysis"]["response_gate_passed"] is True
    assert card["analysis"]["coverage_gate_passed"] is False
    assert card["analysis"]["mask_sensitivity_gate_passed"] is True
    y21c = next(
        row
        for row in card["analysis"]["split_coverage"]
        if row["axis"] == "Y21c"
    )
    assert y21c["evaluation_coverage_count"] == 35
    assert y21c["evaluation_count"] == 40
    assert y21c["evaluation_coverage"] == 0.875
    material = dict(card)
    material.pop("semantic_digest")
    assert card["semantic_digest"] == canonical_sha256(material)


def test_result_card_is_blocked_without_claim_promotion() -> None:
    card_path = REPO / "docs/generated/pr204_result_card.json"
    calibration_path = (
        REPO / "docs/generated/pr204_injection_calibration.json"
    )
    card = _json(card_path)
    assert card["terminal"] == (
        "BLOCKED_INBAND_INJECTION_COVERAGE_FAILURE"
    )
    assert card["readiness_state"] == "BLOCKED"
    assert card["independence_gate"] == "OPEN"
    assert card["scientific_result"] is None
    assert card["claim_tier"] == "exploratory"
    assert card["public_use"] is False
    assert card["raw_qe_reproduction"] is False
    assert card["calibration_card_sha256"] == _sha(calibration_path)
    material = dict(card)
    material.pop("semantic_digest")
    assert card["semantic_digest"] == canonical_sha256(material)
