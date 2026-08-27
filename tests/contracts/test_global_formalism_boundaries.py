"""Exact-type firewalls for the Planck MES irrep/global formalism."""

from __future__ import annotations

import hashlib
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


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


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
    carrier = api.ObservableIrrepCarrier(
        components=tuple(float(index) for index in range(1, 33)),
        frame="GALACTIC",
        basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
        units="microK_CMB",
        source_identity=_sha("observer-row-source"),
        operator_identity=_sha("observer-operator"),
        row_identity="SMICA_OBSERVED",
    )
    harmonic = api.build_real_harmonic_irrep_block(carrier=carrier, ell=2)
    block = api.build_cartesian_stf_irrep_block(
        parent=harmonic,
        components=(1.0, -2.0, 3.0, -4.0, 5.0),
        basis="CARTESIAN_STF2_5_ORTHONORMAL_V1",
        projection_identity=_sha("observer-stf2-projection"),
    )
    return api, api.ObservableIrrepState(
        blocks=(block,),
        frame=block.support.frame,
        basis=block.support.basis,
        units=block.support.units,
        source_identity=block.support.source_identity,
        operator_identity=block.support.operator_identity,
        row_identity=block.support.row_identity,
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
    with pytest.raises(api.ObservableIrrepStateError, match="carrier"):
        api.build_real_harmonic_irrep_block(carrier=0.2458, ell=3)
    with pytest.raises(api.ObservableIrrepStateError, match="parent"):
        api.build_cartesian_stf_irrep_block(
            parent=0.2458,
            components=(0.2458, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            basis="CARTESIAN_STF3_7_ORTHONORMAL_V1",
            projection_identity=_sha("scalar-must-not-project"),
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

    expected = {row["path"]: row["work_unit"] for row in matrix["rows"]}
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
    assert (
        observed["scripts/observed_runs/run_planck_mes_morphology.py"]["status"]
        == "FROZEN_WITH_GUARD"
    )
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
