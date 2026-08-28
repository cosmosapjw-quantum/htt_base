"""PMG-WU-006 integration contracts for the executed paired-300 irrep analysis."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "htt"
SRC = PACKAGE_ROOT / "src"
for path in (SRC, PACKAGE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _api():
    path = ROOT / "scripts/observed_runs/run_planck_mes_irrep_analysis.py"
    if not path.is_file():
        pytest.fail("PMG-WU-006 analysis runner is not implemented", pytrace=False)
    spec = importlib.util.spec_from_file_location("run_planck_mes_irrep_analysis", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    api = _api()
    output = tmp_path_factory.mktemp("pmg_wu006") / "analysis"
    api.build(output)
    return output


def test_objective_outputs_are_real_complete_and_map_free(built: Path) -> None:
    required = {
        "coordinate_table.csv",
        "degeneracy_ledger.csv",
        "dependence_spectrum.csv",
        "family_table.csv",
        "feature_registry.json",
        "figure_dependence_spectrum.pdf",
        "figure_family_reducer_comparison.pdf",
        "figure_null_score_distributions.pdf",
        "figure_observed_coordinate_ranks.pdf",
        "irrep_features.npz",
        "null_distributions.npz",
        "plot_audit.json",
        "replay.json",
        "result.json",
        "terminal.json",
    }
    assert {path.name for path in built.iterdir()} == required
    result = json.loads((built / "result.json").read_text())
    terminal = json.loads((built / "terminal.json").read_text())
    assert result["row_count"] == 301
    assert result["null_row_count"] == 300
    assert result["raw_maps_reopened"] is False
    assert result["selection_policy"] == (
        "features families tails reducers and row-disposition policy frozen before observed-row scoring"
    )
    assert terminal["state"] == "EXECUTED_PENDING_REVIEW"
    assert terminal["science_execution_performed"] is True
    assert terminal["raw_data_read_or_mutated"] is False
    assert terminal["claim_promotion"] is False


def test_exact_carrier_identity_and_301_row_order_are_preserved(built: Path) -> None:
    result = json.loads((built / "result.json").read_text())
    assert result["source_carrier"] == {
        "carrier_content_id": "sha256:9fa50a818f18346766a07481242acde3afa6069e40b8a279fbc2b1e0f5d013d3",
        "package_sha256": "sha256:0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93",
        "row_ids_sha256": result["source_carrier"]["row_ids_sha256"],
    }
    with np.load(built / "irrep_features.npz", allow_pickle=False) as bundle:
        assert set(bundle.files) == {
            "all_coordinate_values",
            "coordinate_availability",
            "coordinate_ids",
            "frame_free_features",
            "o_components",
            "orientation_features",
            "q_components",
            "row_ids",
            "state_content_ids",
        }
        assert bundle["q_components"].shape == (301, 5)
        assert bundle["o_components"].shape == (301, 7)
        assert bundle["frame_free_features"].shape == (301, 8)
        assert bundle["orientation_features"].shape == (301, 10)
        row_ids = tuple(str(value) for value in bundle["row_ids"])
    with np.load(
        ROOT / "docs/generated/planck_pr3_paired300_irrep_carrier/carrier.npz",
        allow_pickle=False,
    ) as source:
        assert row_ids == tuple(str(value) for value in source["row_ids"])


def test_both_registered_reducers_and_separate_orientation_family(built: Path) -> None:
    result = json.loads((built / "result.json").read_text())
    assert set(result["family_results"]) == {
        "OBSERVABLE_IRREP_ORBIT_V1",
        "OBSERVABLE_IRREP_ORBIT_GALACTIC_V1",
    }
    for family in result["family_results"].values():
        assert set(family) == {
            "LEGACY_ABSOLUTE_MEDIAN_V1",
            "LOO_ECDF_MIDRANK_V1",
        }
        for reducer in family.values():
            assert reducer["rank_denominator"] == 301
            assert 1 <= reducer["global_rank_numerator"] <= 301
    registry = json.loads((built / "feature_registry.json").read_text())
    assert registry["families"]["OBSERVABLE_IRREP_ORBIT_V1"]["frame_role"] == (
        "FRAME_FREE_PRIMARY"
    )
    assert registry["families"]["OBSERVABLE_IRREP_ORBIT_GALACTIC_V1"][
        "frame_role"
    ] == "ABSOLUTE_GALACTIC_DESCRIPTIVE_COMPANION"


def test_feature_registry_matches_the_implemented_mixed_shape_coordinates(
    built: Path,
) -> None:
    registry = json.loads((built / "feature_registry.json").read_text())
    definitions = {
        row["feature_id"]: row["definition"] for row in registry["coordinates"]
    }
    assert definitions["R_v0_normalized"] == "v_a v^a"
    assert definitions["R_v1_normalized"] == "v_a Qhat^a_b v^b"
    assert definitions["R_v2_normalized"] == "v_a (Qhat^2)^a_b v^b"
    assert definitions["R_QS_normalized"] == "Qhat_ab S^ab"
    assert definitions["K_v_normalized"] == "det(v,Qhat v,Qhat^2 v)"
    assert all("vhat" not in definition for definition in definitions.values())
    assert all("Shat" not in definition for definition in definitions.values())


def test_row_permutation_and_observation_swap_equivariance() -> None:
    api = _api()
    rng = np.random.default_rng(6006)
    frame_free = rng.normal(size=(301, 8))
    orientation = np.column_stack((frame_free, rng.normal(size=(301, 2))))
    baseline = api.calibrate_families(frame_free, orientation, observation_index=0)
    permutation = np.arange(301)
    permutation[[0, 117]] = permutation[[117, 0]]
    permuted = api.calibrate_families(
        frame_free[permutation], orientation[permutation], observation_index=117
    )
    for family_id in baseline:
        for reducer_id in baseline[family_id]:
            assert permuted[family_id][reducer_id]["global_rank_numerator"] == (
                baseline[family_id][reducer_id]["global_rank_numerator"]
            )
            assert permuted[family_id][reducer_id]["local_rank_numerators"] == (
                baseline[family_id][reducer_id]["local_rank_numerators"]
            )


def test_tie_dependence_and_degeneracy_dispositions_are_complete(built: Path) -> None:
    result = json.loads((built / "result.json").read_text())
    assert set(result["dependence_diagnostics"]) == {
        "OBSERVABLE_IRREP_ORBIT_V1",
        "OBSERVABLE_IRREP_ORBIT_GALACTIC_V1",
    }
    for family_id, diagnostics in result["dependence_diagnostics"].items():
        expected = 8 if family_id == "OBSERVABLE_IRREP_ORBIT_V1" else 10
        assert len(diagnostics["coordinate_duplicate_counts"]) == expected
        assert len(diagnostics["spearman_eigenvalues_descending"]) == expected
        assert 1.0 <= diagnostics["spearman_participation_ratio"] <= expected + 1e-10
    lines = (built / "degeneracy_ledger.csv").read_text().splitlines()
    assert len(lines) == 302
    assert result["degeneracy_summary"]["row_count"] == 301
    assert sum(result["degeneracy_summary"]["primary_family_dispositions"].values()) == 301


def test_claim_boundary_forbids_physical_and_family_promotion(built: Path) -> None:
    result = json.loads((built / "result.json").read_text())
    assert result["claim_tier"] == "METHODS_DIAGNOSTIC_ONLY"
    assert result["completeness_status"] == "GENERIC_GLOBAL_COMPLETENESS_UNPROVEN"
    assert result["physical_source_status"] == "NOT_IDENTIFIED"
    assert result["bianchi_family_status"] == "NOT_IDENTIFIED"
    assert result["claim_promotion"] is False
    assert result["likelihood_emitted"] is False


def test_replay_uses_typed_identity_for_numerical_npz(built: Path, tmp_path: Path) -> None:
    api = _api()
    candidate = tmp_path / "repacked"
    shutil.copytree(built, candidate)
    path = candidate / "irrep_features.npz"
    with np.load(path, allow_pickle=False) as bundle:
        arrays = {name: np.asarray(bundle[name]) for name in reversed(bundle.files)}
    with path.open("wb") as handle:
        np.savez(handle, **arrays)
    replay = api.replay_directory(candidate)
    assert replay["numerical_output_identity"] == "NUMERICALLY_EQUIVALENT"
    assert replay["packaging_validity"] == "BYTE_IDENTITY_NOT_REQUIRED"

    arrays["q_components"] = arrays["q_components"].copy()
    arrays["q_components"][0, 0] += 1.0e-4
    with path.open("wb") as handle:
        np.savez(handle, **arrays)
    with pytest.raises(RuntimeError, match="numerical|semantic|projection"):
        api.replay_directory(candidate)


def test_replay_mutation_and_input_byte_drift_fail_closed(
    built: Path, tmp_path: Path
) -> None:
    api = _api()
    candidate = tmp_path / "result_mutation"
    shutil.copytree(built, candidate)
    result = json.loads((candidate / "result.json").read_text())
    result["row_count"] = 300
    (candidate / "result.json").write_text(json.dumps(result, sort_keys=True) + "\n")
    with pytest.raises(RuntimeError, match="result|content|deterministic"):
        api.replay_directory(candidate)

    candidate = tmp_path / "plot_audit_mutation"
    shutil.copytree(built, candidate)
    plot_audit = json.loads((candidate / "plot_audit.json").read_text())
    plot_audit["result_content_id"] = "sha256:stale"
    (candidate / "plot_audit.json").write_text(
        json.dumps(plot_audit, sort_keys=True) + "\n"
    )
    with pytest.raises(RuntimeError, match="plot audit.*content identity"):
        api.replay_directory(candidate)

    carrier = tmp_path / "carrier"
    shutil.copytree(
        ROOT / "docs/generated/planck_pr3_paired300_irrep_carrier", carrier
    )
    package = carrier / "carrier.npz"
    package.write_bytes(package.read_bytes() + b"unexpected")
    with pytest.raises(RuntimeError, match="carrier.*identity|package"):
        api.build(tmp_path / "rejected", carrier_dir=carrier)


def test_review_finalization_is_separate_from_execution(built: Path) -> None:
    api = _api()
    api.finalize_reviewed(built)
    terminal = json.loads((built / "terminal.json").read_text())
    plot_audit = json.loads((built / "plot_audit.json").read_text())
    assert terminal["state"] == "SUCCEEDED"
    assert terminal["fresh_review"] == "PASS"
    assert terminal["unresolved_blockers"] == []
    assert terminal["next_executable_action"] == "PMG-WU-007"
    assert plot_audit["inspection_state"] == "PASS_HOST_DIRECT_INSPECTION"
