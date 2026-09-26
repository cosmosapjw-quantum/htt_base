from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from obsstat.act_inband_modulation import semantic_digest
from obsstat.act_modulation_closure import (
    ACCEPTED_RESULT,
    RAW_QE_BLOCKER,
    TERMINAL,
    ActModulationClosureError,
    build_closure_card,
)


REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "docs/research_program/long_horizon_rescue/pr204_spec.yaml"
OUTPUT = REPO / "docs/generated/pr204_result_card.json"
RUNNER = REPO / "scripts/codex_harness/run_pr204_act_closure.py"
SOURCES = {
    "result": REPO / "docs/generated/pr177_act_modulation_result.json",
    "mask": REPO / "docs/generated/pr177_mask_control.json",
    "mc": REPO / "docs/generated/pr177_mc_resolution.json",
    "result_card": REPO / "docs/generated/pr177_result_card.json",
    "availability": REPO / "docs/generated/pr152_availability_decision.json",
    "inventory": REPO / "docs/generated/pr152_inventory.json",
}


def _load() -> tuple[dict, dict[str, dict]]:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    sources = {
        name: json.loads(path.read_text(encoding="utf-8"))
        for name, path in SOURCES.items()
    }
    return spec, sources


def _build(**mutations: dict) -> dict:
    spec, sources = _load()
    sources.update(mutations)
    return build_closure_card(spec=spec, **sources)


def _resign(payload: dict) -> dict:
    payload["semantic_digest"] = semantic_digest(payload)
    return payload


def test_release_summary_and_raw_qe_branches_close_separately() -> None:
    card = _build()
    assert card["terminal"] == TERMINAL
    assert card["scientific_result"] == ACCEPTED_RESULT
    assert card["scientific_effect"] == "none_new_reuses_pr177_conditional_null"
    assert card["claim_id"] == "C-PR204-ACT-CLOSURE"
    assert card["claim_status"] == "CONDITIONAL"
    assert card["evidence_type"] == "artifact"
    assert card["owner"] == "OBSSTAT"
    assert card["transfer_source"] == "none"
    assert card["sky_support_status"]
    assert card["covariance_status"]
    assert card["null_mock_status"]
    assert len(card["caveats"]) == 4
    assert card["release_summary"]["analysis_support"] == {
        "inequality": "40 < L < 763",
        "integer_min": 41,
        "integer_max": 762,
        "integer_count": 722,
        "endpoints_40_and_763_included": False,
        "coordinate_frame": "Equatorial",
    }
    assert card["release_summary"]["rank_summary"]["controlled"]["rank_fraction"] == "102/401"
    assert card["raw_qe_branch"]["status"] == RAW_QE_BLOCKER
    assert card["response_and_injection_boundary"]["pre_qe_injection_coverage"] == RAW_QE_BLOCKER
    assert card["response_and_injection_boundary"]["amplitude_constraint"] == "NOT_COMPUTED"
    assert card["independence_gate"] == "OPEN"
    assert card["anisotropic_modulation_claim_status"] == (
        "WITHHELD_PRE_QE_RESPONSE_COVERAGE_NOT_COMPUTED"
    )
    assert card["publication_use"] is False
    assert card["detection_claim"] is False
    assert card["physical_attribution"] is False
    assert card["family_identification"] is False
    assert card["semantic_digest"] == semantic_digest(card)


@pytest.mark.parametrize(
    ("source_name", "mutate", "message"),
    [
        (
            "result",
            lambda value: value["analysis_support"].update(integer_min=40),
            "support mismatch",
        ),
        (
            "result_card",
            lambda value: value["rank_summary"]["controlled"].update(rank_fraction="1/401"),
            "rank fraction drift",
        ),
        (
            "mask",
            lambda value: value.update(candidate_survives_registered_mask_control=True),
            "mask control",
        ),
        (
            "mc",
            lambda value: value["replicate_lineage"].update(replicate_count=399),
            "finite-ensemble lineage mismatch",
        ),
    ],
)
def test_release_branch_rejects_support_rank_mask_and_lineage_drift(
    source_name: str, mutate, message: str
) -> None:
    _, sources = _load()
    changed = copy.deepcopy(sources[source_name])
    mutate(changed)
    _resign(changed)
    with pytest.raises(ActModulationClosureError, match=message):
        _build(**{source_name: changed})


def test_raw_qe_branch_rejects_missing_blocker_or_false_readiness() -> None:
    _, sources = _load()
    inventory = copy.deepcopy(sources["inventory"])
    inventory["local_missing_raw_qe_inputs"].pop()
    with pytest.raises(ActModulationClosureError, match="blocker inventory"):
        _build(inventory=inventory)

    availability = copy.deepcopy(sources["availability"])
    availability["raw_qe_available"] = True
    with pytest.raises(ActModulationClosureError, match="separate configuration validator"):
        _build(availability=availability)


@pytest.mark.parametrize(
    "requested_output",
    [
        "anisotropy_detection",
        "physical_modulation_amplitude",
        "sky_power_measurement",
        "raw_qe_reproduction",
        "pre_qe_injection_coverage",
        "bianchi_family_identification",
        "publication_use",
        "joint_confidence",
    ],
)
def test_forbidden_scientific_requests_fail_closed(requested_output: str) -> None:
    spec, sources = _load()
    with pytest.raises(ActModulationClosureError, match="unsupported"):
        build_closure_card(spec=spec, requested_output=requested_output, **sources)


def test_generated_card_is_current_and_source_bound() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    card = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert card["semantic_digest"] == semantic_digest(card)
    assert card["source_sha256"] == yaml.safe_load(SPEC.read_text(encoding="utf-8"))[
        "source_identities"
    ]
