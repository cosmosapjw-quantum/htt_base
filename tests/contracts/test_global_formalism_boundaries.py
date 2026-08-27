"""Exact-type firewalls for the Planck MES irrep/global formalism."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "htt" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _observable_api():
    try:
        return importlib.import_module("common.observable_irrep_state")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "ObservableIrrepState public API is not implemented",
            pytrace=False,
        )
        raise AssertionError("unreachable") from exc


def _observable_state():
    api = _observable_api()
    block = api.ObservableIrrepBlock(
        ell=2,
        spin=0,
        representation="CARTESIAN_STF2_5",
        parity="EVEN",
        components=(1.0, -2.0, 3.0, -4.0, 5.0),
        support_kind="REGISTERED_STF_PROJECTION",
        support_identity="sha256:test-observer-stf2-projection",
    )
    return api, api.ObservableIrrepState(
        blocks=(block,),
        frame="GALACTIC",
        basis="STF5_CARTESIAN_ORTHONORMAL",
        units="microK_CMB",
        source_identity="sha256:observer-row",
        operator_identity="sha256:observer-operator",
        row_identity="SMICA_OBSERVED",
    )


def test_physical_state_refusal_preserves_exact_type_separation() -> None:
    """Catch inheritance or payload coercion into the physical state layer."""

    _, observable = _observable_state()
    from common.joint_anisotropy_state import (
        JointAnisotropyState,
        JointAnisotropyStateError,
    )

    assert type(observable) is not JointAnisotropyState
    assert JointAnisotropyState not in type(observable).__mro__
    with pytest.raises(JointAnisotropyStateError, match="schema|keys"):
        JointAnisotropyState.from_payload(observable.to_payload())


def test_physical_orbit_catalogue_refusal_requires_exact_joint_state() -> None:
    """Catch observer-space Q/O content entering the physical orbit catalogue."""

    _, observable = _observable_state()
    from common.orbit_catalogue_v3 import orbit_catalogue_v3

    with pytest.raises(TypeError, match="exact JointAnisotropyState"):
        orbit_catalogue_v3(observable, object())


def test_scalar_refusal_at_observable_global_boundary() -> None:
    """Catch a scalar MES ceiling being treated as directional support."""

    api = _observable_api()
    with pytest.raises(api.ObservableIrrepStateError, match="components"):
        api.ObservableIrrepBlock(
            ell=3,
            spin=0,
            representation="CARTESIAN_STF3_7",
            parity="ODD",
            components=0.2458,
            support_kind="REGISTERED_STF_PROJECTION",
            support_identity="sha256:direct-scalar-must-still-fail",
        )


def test_physical_claim_refusal_survives_payload_replay() -> None:
    """Catch claim-ceiling mutation during observer-state deserialization."""

    api, observable = _observable_state()
    payload = observable.to_payload()
    payload["claim_ceiling"] = "global_tilt"
    with pytest.raises(api.ObservableIrrepStateError, match="claim ceiling"):
        api.observable_irrep_state_from_payload(payload)


def test_migration_coverage_inventory_matches_declared_paths() -> None:
    """Catch a migration surface being silently omitted or falsely completed."""

    matrix_path = (
        ROOT
        / "docs"
        / "codex_handoff"
        / "planck_mes_irrep_global_formalism_execution"
        / "FORMALISM_MIGRATION_MATRIX.yaml"
    )
    status_path = (
        ROOT
        / "docs"
        / "generated"
        / "planck_mes_irrep_formalism"
        / "migration_status.json"
    )
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))

    expected = {
        row["path"]: row["work_unit"]
        for row in matrix["rows"]
    }
    observed = {row["path"]: row for row in status["rows"]}
    assert observed.keys() == expected.keys()
    assert len(observed) == 22
    assert status["schema"] == "htt.planck_mes_irrep_formalism.migration_status.v1"
    assert status["current_work_unit"] == "PMG-WU-001"
    assert status["claim_promotion"] is False
    for path, owner in expected.items():
        assert observed[path]["owner_work_unit"] == owner
        assert observed[path]["status"] in {
            "MIGRATED",
            "ADAPTED",
            "FROZEN_WITH_GUARD",
            "PENDING_ORDERED_WORK_UNIT",
        }
    assert observed["htt/src/common/observable_irrep_state.py"]["status"] == "MIGRATED"
    assert observed["scripts/observed_runs/run_planck_mes_morphology.py"]["status"] == "FROZEN_WITH_GUARD"
    assert observed["tests/architecture/test_import_boundaries.py"]["status"] == "ADAPTED"


def test_wu001_terminal_records_enabling_output_and_exact_transition() -> None:
    """Catch WU-001 being called successful without its objective terminal."""

    terminal_path = (
        ROOT
        / "docs"
        / "generated"
        / "planck_mes_irrep_formalism"
        / "wu001_terminal.json"
    )
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))

    assert terminal["schema"] == "htt.planck_mes_irrep_formalism.work_unit_terminal.v1"
    assert terminal["work_unit"] == "PMG-WU-001"
    assert terminal["state"] == "SUCCEEDED"
    assert terminal["base_git_head"] == "80781295cb161436eac164fc40bd7f57adfe10d1"
    assert terminal["output_class"] == "ENABLING_OUTPUT"
    assert terminal["claim_promotion"] is False
    assert terminal["science_execution_performed"] is False
    assert terminal["raw_data_read_or_mutated"] is False
    assert terminal["replay_status"] == "MATCH_FROZEN_BASELINE"
    assert terminal["next_executable_action"] == "PMG-WU-002"
    assert terminal["invariant_results"]["PMG-INV-ACTIVE-PACKAGE"] == (
        "PASS_AT_PRECONDITION_BASE_ONLY"
    )
    assert terminal["post_candidate_plan_validator"] == {
        "command": "python scripts/validate_planck_mes_irrep_global_formalism_plan.py",
        "exit_code": 1,
        "status": "EXPECTED_PLANNING_SCOPE_REFUSAL",
    }
    assert terminal["frozen_scalar_rank_numerators"] == {
        "ANCHORS_ONLY_2": 78,
        "EPS_REDUCED_10": 109,
        "GENERIC_12": 133,
        "MES_10": 98,
        "MORPHOLOGY_ONLY_8": 88,
        "RAW_REDUCED_10": 110,
    }
    assert terminal["rank_denominator"] == 301
