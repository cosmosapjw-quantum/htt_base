from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py"
PRIMARY_CARRIER = ROOT / "docs/generated/planck_pr3_paired300_irrep_carrier"
PRIMARY_ANALYSIS = ROOT / "docs/generated/planck_mes_irrep_analysis"


def _api():
    if not SCRIPT.is_file():
        pytest.fail("PMG-WU-007 real runner is not implemented", pytrace=False)
    spec = importlib.util.spec_from_file_location("planck_mes_smica999", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fake_rows(api):
    return tuple(
        api.CmbOnlyRow(
            row_id=f"FFP10-SMICA-CMB-{row_id}",
            source_id=row_id,
            path=Path(f"dx12_v3_smica_cmb_mc_{row_id}_raw.fits"),
            source_identity={"row_id": row_id, "size": 100 + index},
        )
        for index, row_id in enumerate(api.EXPECTED_CMB_IDS)
    )


def test_exact_999_inventory_order_excludes_only_00970_and_includes_00818() -> None:
    api = _api()
    assert len(api.EXPECTED_CMB_IDS) == 999
    assert api.EXPECTED_CMB_IDS == tuple(
        f"{index:05d}" for index in range(1000) if index != 970
    )
    assert "00818" in api.EXPECTED_CMB_IDS
    assert "00970" not in api.EXPECTED_CMB_IDS


def test_observation_row_is_reused_and_null_carriers_come_from_same_pass_retained_coefficients() -> None:
    api = _api()
    observed_features = np.arange(12, dtype=np.float64)
    observed_carrier = np.arange(32, dtype=np.float64)
    read_calls: list[str] = []
    process_calls: list[int] = []

    def read_cmb(path: Path) -> np.ndarray:
        assert "noise" not in path.name
        source_id = path.name.rsplit("_", 2)[-2]
        read_calls.append(source_id)
        return np.asarray([int(source_id)], dtype=np.float64)

    def process_map(pixel_map, *, component, context):
        assert component == "SMICA"
        assert context == {"operator": "accepted"}
        value = int(np.asarray(pixel_map)[0])
        process_calls.append(value)
        return (
            np.arange(12, dtype=np.float64) + value,
            {"fit": 1.0},
            np.arange(32, dtype=np.float64) + 1000.0 * value,
        )

    result = api.process_null_rows_one_pass(
        observed_features=observed_features,
        observed_carrier=observed_carrier,
        rows=_fake_rows(api),
        context={"operator": "accepted"},
        operator_identity_sha256="sha256:" + "a" * 64,
        read_cmb=read_cmb,
        process_map=process_map,
        carrier_from_alm=lambda value: np.asarray(value, dtype=np.float64),
        checkpoint_dir=None,
        verify_source_unchanged=lambda row: None,
    )
    expected = [int(value) for value in api.EXPECTED_CMB_IDS]
    assert read_calls == list(api.EXPECTED_CMB_IDS)
    assert process_calls == expected
    assert result.row_ids == (
        "PLANCK-PR3-SMICA-OBSERVED",
        *(f"FFP10-SMICA-CMB-{value}" for value in api.EXPECTED_CMB_IDS),
    )
    assert np.array_equal(result.scalar_features[0], observed_features)
    assert np.array_equal(result.carrier_rows[0], observed_carrier)
    assert result.scalar_features.shape == (1000, 12)
    assert result.carrier_rows.shape == (1000, 32)


def test_cmbonly_route_rejects_noise_products_and_mixed_rows() -> None:
    api = _api()
    rows = list(_fake_rows(api))
    rows[17] = api.CmbOnlyRow(
        row_id=rows[17].row_id,
        source_id=rows[17].source_id,
        path=Path("dx12_v3_smica_noise_mc_00017_raw.fits"),
        source_identity=rows[17].source_identity,
    )
    with pytest.raises(api.Wu007Error, match="noise|CMB-only"):
        api.validate_cmbonly_rows(rows)


def test_same_row_scalar_and_irrep_outputs_project_from_the_same_carrier() -> None:
    api = _api()
    worker = api.worker
    carrier = np.linspace(-0.25, 0.75, 32, dtype=np.float64)
    scalar = worker._component_features_from_real_carrier(carrier)
    api.require_scalar_carrier_closure(
        scalar.reshape(1, 12), carrier.reshape(1, 32)
    )
    forged = scalar.copy()
    forged[-1] += 1.0e-6
    with pytest.raises(api.Wu007Error, match="scalar.*carrier|closure"):
        api.require_scalar_carrier_closure(
            forged.reshape(1, 12), carrier.reshape(1, 32)
        )


def test_exact_operator_and_carrier_conventions_match_accepted_primary() -> None:
    api = _api()
    accepted = json.loads((PRIMARY_CARRIER / "metadata.json").read_text())
    api.require_accepted_operator_and_representation(
        operator_identity=accepted["operator_identity"],
        operator_identity_sha256=accepted["operator_identity_sha256"],
        metadata=accepted,
    )
    changed = dict(accepted["operator_identity"])
    changed["mask_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(api.Wu007Error, match="operator"):
        api.require_accepted_operator_and_representation(
            operator_identity=changed,
            operator_identity_sha256=accepted["operator_identity_sha256"],
            metadata=accepted,
        )


def test_primary_and_robustness_outputs_are_distinct_and_primary_is_immutable(
    tmp_path: Path,
) -> None:
    api = _api()
    before = api.snapshot_primary_artifacts(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
    output = tmp_path / "planck_mes_smica_cmbonly_999_irrep"
    api.require_separate_output_boundary(
        output, primary_paths=(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
    )
    assert api.snapshot_primary_artifacts(PRIMARY_CARRIER, PRIMARY_ANALYSIS) == before
    for primary in (PRIMARY_CARRIER, PRIMARY_ANALYSIS):
        with pytest.raises(api.Wu007Error, match="primary|separate"):
            api.require_separate_output_boundary(
                primary, primary_paths=(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
            )


def test_raw_inputs_are_immutable_and_forbidden_paths_are_not_staged(
    tmp_path: Path,
) -> None:
    api = _api()
    source = tmp_path / "cmb.fits"
    source.write_bytes(b"immutable")
    before = api.stat_identity(source)
    api.require_stat_identity(source, before)
    source.write_bytes(b"mutated")
    with pytest.raises(api.Wu007Error, match="mutated|identity"):
        api.require_stat_identity(source, before)


def test_wu007_registry_is_exactly_the_accepted_wu006_registry() -> None:
    api = _api()
    registry = api.load_frozen_registry(
        ROOT / "docs/research_program/post_pr327/planck_mes_wu007_registry.yaml"
    )
    assert registry["reducers"] == list(api.wu006.REDUCERS)
    assert registry["families"] == api.wu006.family_registry_payload()
    assert registry["source_reducer_registry_sha256"] == (
        api.wu006.EXPECTED_COORDINATE_REGISTRY_SHA256
    )


def test_claim_envelope_forbids_rank_based_promotion() -> None:
    api = _api()
    envelope = api.claim_envelope()
    assert envelope["claim_promotion"] is False
    assert envelope["rank_based_promotion_forbidden"] is True
    assert envelope["physical_source_status"] == "NOT_IDENTIFIED"
    assert envelope["bianchi_family_status"] == "NOT_IDENTIFIED"
    assert envelope["primary_replacement"] is False
    forbidden = " ".join(envelope["forbidden_use"]).lower()
    assert "foreground" in forbidden
    assert "local" in forbidden
    assert "bianchi" in forbidden


def test_success_terminal_requires_real_999_execution_and_reviewed_evidence(
    tmp_path: Path,
) -> None:
    api = _api()
    pending = {
        "format": api.TERMINAL_FORMAT,
        "work_unit": "PMG-WU-007",
        "state": "EXECUTED_PENDING_REVIEW",
        "real_host_execution": True,
        "row_count": 1000,
        "null_row_count": 999,
        "noise_read_count": 0,
        "replay_status": "MATCH",
        "raw_data_mutation": False,
        "primary_replacement": False,
        "claim_promotion": False,
        "fresh_review": "PENDING",
        "P0_remaining": None,
        "P1_remaining": None,
        "unresolved_blockers": ["FRESH_REVIEW_PENDING"],
        "next_executable_action": "FRESH_READ_ONLY_REVIEW",
    }
    review = {
        "format": api.REVIEW_FORMAT,
        "state": "PASS",
        "P0_remaining": 0,
        "P1_remaining": 0,
        "repair_rounds_used": 0,
        "candidate_git_head": "a" * 40,
        "candidate_git_tree": "b" * 40,
        "figures": {
            name: {
                "single_column_3.3in": "PASS",
                "double_column_6.8in": "PASS",
            }
            for name in api.FIGURE_FILES
        },
    }
    final = api.final_terminal_payload(
        pending=pending,
        review=review,
        candidate_head="a" * 40,
        candidate_tree="b" * 40,
    )
    assert final["state"] == "SUCCEEDED"
    assert final["unresolved_blockers"] == []
    assert final["next_executable_action"] == "PMG-WU-008"
    broken = dict(review)
    broken["P1_remaining"] = 1
    with pytest.raises(api.Wu007Error, match="review"):
        api.final_terminal_payload(
            pending=pending,
            review=broken,
            candidate_head="a" * 40,
            candidate_tree="b" * 40,
        )


def test_terminal_pass_transition_is_exactly_pmg_wu008_and_only_after_review() -> None:
    api = _api()
    terminal = json.loads(
        (ROOT / "docs/generated/planck_mes_irrep_analysis/terminal.json").read_text()
    )
    assert terminal["next_executable_action"] == "PMG-WU-007"
    assert api.SUCCESS_NEXT_ACTION == "PMG-WU-008"


def test_portable_1000_row_build_and_map_free_replay(tmp_path: Path) -> None:
    api = _api()
    rng = np.random.default_rng(7007)
    carriers = rng.normal(size=(1000, 32)).astype(np.float64)
    scalars = np.asarray(
        [api.worker._component_features_from_real_carrier(row) for row in carriers],
        dtype=np.float64,
    )
    execution = api.ExecutionRows(
        row_ids=(
            api.OBSERVATION_ROW_ID,
            *(f"{api.ROW_PREFIX}{value}" for value in api.EXPECTED_CMB_IDS),
        ),
        scalar_features=scalars,
        carrier_rows=carriers,
        checkpoint_reused_count=0,
    )
    metadata = json.loads((PRIMARY_CARRIER / "metadata.json").read_text())
    operator = {
        "content_id": "sha256:" + "1" * 64,
        "carrier_operator_identity_sha256": metadata["operator_identity_sha256"],
    }
    primary = api.snapshot_primary_artifacts(PRIMARY_CARRIER, PRIMARY_ANALYSIS)
    output = tmp_path / "analysis"
    output.mkdir()
    result = api.build_portable_analysis(
        output=output,
        execution=execution,
        metadata=metadata,
        preflight_binding={"selected_input_manifest_content_id": "sha256:" + "2" * 64},
        operator_receipt=operator,
        scalar_closure=api.require_scalar_carrier_closure(scalars, carriers),
        primary_before=primary,
        primary_after=primary,
        checkpoint_reused_count=0,
    )
    assert result["row_count"] == 1000
    assert result["null_row_count"] == 999
    assert result["noise_read_count"] == 0
    assert result["primary_replacement"] is False
    assert api.replay_directory(output)["status"] == "MATCH"
    terminal = json.loads((output / "terminal.json").read_text())
    assert terminal["state"] == "EXECUTED_PENDING_REVIEW"
    assert terminal["next_executable_action"] == "FRESH_READ_ONLY_REVIEW"
