"""PR-327 exact 300-pair Planck MES morphology integration tests."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[2]
SOURCE_PACKAGE = REPO / "docs/generated/pr315_planck_smica_feature_replay.npz"
SOURCE_METADATA = REPO / "docs/generated/pr315_planck_smica_feature_replay.json"
COMMITTED_OUTPUT = REPO / "docs/generated/planck_mes_morphology"
PR314_BLOBS = {
    "docs/PR_DELTAS/pr-314.md": "4355832a77320bc86a467793054396e5657ed1f5",
    "docs/generated/pr314_planck_pr3_smica_existing_result.json": (
        "fe2e1a6121cfee8f8dc0e7ff7dc1893253e0a346"
    ),
    "docs/generated/pr314_planck_pr3_smica_existing_replay.json": (
        "d206f8c5249bd750904813f798f5fea7359fd769"
    ),
    "docs/research_program/post_pr275/pr314_existing_data_analysis_report.md": (
        "962bc2117af0981904f3f65e545680c5b1b58a82"
    ),
    "docs/research_program/post_pr275/pr314_spec.yaml": (
        "6cf44181639092fd5ddeabd3a0fb1ccf1018cb59"
    ),
}
EXPECTED_FEATURE_IDS = (
    "mes_sigma_anchor",
    "mes_omega_anchor",
    "parity_even_over_odd_l2_l5",
    "power_tensor_gap_l2",
    "power_tensor_gap_l3",
    "multipole_l2_absdot",
    "multipole_l3_absdot_0",
    "multipole_l3_absdot_1",
    "multipole_l3_absdot_2",
    "multipole_plane_alignment_max_l2_l3",
)


def _runner():
    try:
        return importlib.import_module(
            "scripts.observed_runs.run_planck_mes_morphology"
        )
    except (AttributeError, ModuleNotFoundError):
        pytest.fail("PR-327 Planck MES morphology runner is not implemented")


def _run(tmp_path: Path):
    runner = _runner()
    output = tmp_path / "planck-mes"
    payload = runner.run_planck_mes_morphology_analysis(
        feature_package_path=SOURCE_PACKAGE,
        feature_metadata_path=SOURCE_METADATA,
        output_dir=output,
        residual_dipole_attribution=(
            runner.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
        ),
    )
    return runner, output, payload


def test_exact_row_operator_has_two_active_anchors_and_eight_invariants(
    tmp_path: Path,
) -> None:
    runner, output, payload = _run(tmp_path)
    with np.load(output / runner.MES_PACKAGE_FILENAME, allow_pickle=False) as bundle:
        assert set(bundle.files) == {
            "feature_rows",
            "pooled_covariance",
            "row_ids",
            "feature_ids",
            "feature_units",
            "feature_roles",
            "tails",
            "anchor_row_content_identities",
        }
        rows = np.asarray(bundle["feature_rows"], dtype=float)
        covariance = np.asarray(bundle["pooled_covariance"], dtype=float)
        row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
        feature_ids = tuple(str(value) for value in bundle["feature_ids"].tolist())
        feature_roles = tuple(
            str(value) for value in bundle["feature_roles"].tolist()
        )

    assert rows.shape == (301, 10)
    assert covariance.shape == (10, 10)
    assert row_ids[0] == runner.OBSERVED_ROW_ID
    assert feature_ids == EXPECTED_FEATURE_IDS
    assert feature_roles[:2] == (
        "ROWWISE_REALIZATION_CONDITIONAL_MES_AMPLITUDE_ANCHOR",
        "ROWWISE_REALIZATION_CONDITIONAL_MES_AMPLITUDE_ANCHOR",
    )
    assert set(feature_roles[2:]) == {"DIMENSIONLESS_IRREDUCIBLE_MORPHOLOGY"}
    assert rows[0] == pytest.approx(
        (
            2.400087022175844e-10,
            3.0061887930898035e-13,
            0.5533649184674748,
            0.4499927615199697,
            0.5601372467878019,
            0.13317343756618844,
            0.398744286835429,
            0.43385751928412986,
            0.4368284926099312,
            0.9402390888212062,
        ),
        rel=0.0,
        abs=1e-24,
    )
    assert payload["result"]["self_anchor_independent_information_gain"] is False


def test_exact_mes_finite_rank_is_98_of_301_and_generic_control_is_separate(
    tmp_path: Path,
) -> None:
    runner, _, payload = _run(tmp_path)
    result = payload["result"]

    assert result["primary_result_role"] == (
        "MES_ANCHORED_SCALAR_IRREDUCIBLE_MORPHOLOGY_FINITE_RANK"
    )
    assert result["global_finite_rank"] == {
        "exceedances_including_observation": 98,
        "denominator": 301,
        "fraction": "98/301",
        "reduced_fraction": "14/43",
    }
    assert result["local_finite_rank_numerators"] == [
        74,
        74,
        95,
        182,
        35,
        177,
        16,
        155,
        174,
        135,
    ]
    assert result["generic_benchmark_control"] == {
        "role": "FROZEN_PR314_BENCHMARK_CONTROL_NOT_MES",
        "result_sha256": (
            "sha256:898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97"
        ),
        "rank_fraction": "133/301",
        "reduced_fraction": "19/43",
    }
    assert result["generic_control_preserved"] is True
    assert runner.MES_FEATURE_IDS == EXPECTED_FEATURE_IDS


def test_pool_covariance_and_scan_are_row_and_observation_index_equivariant(
    tmp_path: Path,
) -> None:
    runner, output, payload = _run(tmp_path)
    assert payload["result"]["equivariance_receipt"] == {
        "observation_index_swap": "PASS",
        "row_permutation": "PASS",
        "pooled_covariance_row_permutation": "PASS",
    }
    with np.load(output / runner.MES_PACKAGE_FILENAME, allow_pickle=False) as bundle:
        rows = np.asarray(bundle["feature_rows"], dtype=float)
    scan = runner.observation_inclusive_max_scan(
        rows[::-1], runner.MES_TAILS, observation_index=300
    )
    assert scan.global_p.numerator * 301 // scan.global_p.denominator == 98
    assert [value.numerator * 301 // value.denominator for value in scan.local_p] == [
        74,
        74,
        95,
        182,
        35,
        177,
        16,
        155,
        174,
        135,
    ]


def test_portable_replay_recomputes_result_and_rejects_mutations(
    tmp_path: Path,
) -> None:
    runner, output, payload = _run(tmp_path)
    replay = runner.replay_planck_mes_morphology_package(output_dir=output)
    assert replay == payload["replay"]
    assert replay["replay_status"] == "PASS_EXACT_301_ROW_MES_MORPHOLOGY"
    assert replay["raw_maps_reopened"] is False

    result_path = output / runner.MES_RESULT_FILENAME
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["global_finite_rank"]["exceedances_including_observation"] = 97
    result_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    with pytest.raises(runner.PlanckMesMorphologyError, match="result identity"):
        runner.replay_planck_mes_morphology_package(output_dir=output)

    _, clean_output, _ = _run(tmp_path / "second")
    metadata_path = clean_output / runner.MES_METADATA_FILENAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["source_feature_package_identity"] = "sha256:" + "0" * 64
    metadata_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    with pytest.raises(runner.PlanckMesMorphologyError, match="source identity"):
        runner.replay_planck_mes_morphology_package(output_dir=clean_output)

    _, claim_output, _ = _run(tmp_path / "third")
    claim_result_path = claim_output / runner.MES_RESULT_FILENAME
    claim_metadata_path = claim_output / runner.MES_METADATA_FILENAME
    claim_result = json.loads(claim_result_path.read_text(encoding="utf-8"))
    claim_result["claim_tier"] = "publication_ready"
    claim_result["public_use"] = True
    claim_result_path.write_text(
        json.dumps(claim_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    claim_metadata = json.loads(
        claim_metadata_path.read_text(encoding="utf-8")
    )
    claim_metadata["result_sha256"] = "sha256:" + hashlib.sha256(
        claim_result_path.read_bytes()
    ).hexdigest()
    claim_metadata_path.write_text(
        json.dumps(claim_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(runner.PlanckMesMorphologyError, match="claim boundary"):
        runner.replay_planck_mes_morphology_package(output_dir=claim_output)


def test_missing_rows_attribution_and_existing_output_fail_closed(tmp_path: Path) -> None:
    runner = _runner()
    with np.load(SOURCE_PACKAGE, allow_pickle=False) as bundle:
        observed = np.asarray(bundle["observed_features"], dtype=float)
        ids = tuple(str(value) for value in bundle["feature_ids"].tolist())
        units = tuple(str(value) for value in bundle["feature_units"].tolist())

    with pytest.raises(runner.PlanckMesMorphologyError, match="exactly 301"):
        runner.build_planck_mes_morphology_rows(
            row_ids=(runner.OBSERVED_ROW_ID,),
            feature_matrix=observed[None, :],
            feature_ids=ids,
            feature_units=units,
            residual_dipole_attribution=(
                runner.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
            ),
            source_identity="sha256:" + "1" * 64,
            covariance_identity="sha256:" + "2" * 64,
            operator_identity="sha256:" + "3" * 64,
        )

    output = tmp_path / "blocked"
    with pytest.raises(runner.PlanckMesMorphologyError, match="BLOCKED_MES_ATTRIBUTION"):
        runner.run_planck_mes_morphology_analysis(
            feature_package_path=SOURCE_PACKAGE,
            feature_metadata_path=SOURCE_METADATA,
            output_dir=output,
            residual_dipole_attribution=None,
        )
    assert not output.exists()

    output.mkdir()
    with pytest.raises(runner.PlanckMesMorphologyError, match="must not already exist"):
        runner.run_planck_mes_morphology_analysis(
            feature_package_path=SOURCE_PACKAGE,
            feature_metadata_path=SOURCE_METADATA,
            output_dir=output,
            residual_dipole_attribution=(
                runner.ResidualDipoleAttribution.SAG_OBSERVER_MOTION_EPS1_ZERO
            ),
        )


def test_directional_local_global_and_family_claims_remain_blocked(tmp_path: Path) -> None:
    _, _, payload = _run(tmp_path)
    result = payload["result"]
    assert result["directional_moment_state"] == "BLOCKED_DIRECTIONAL_SUPPORT"
    assert result["local_global_response"] == (
        "SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED"
    )
    assert result["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert result["claim_tier"] == "diagnostic_only"
    assert result["public_use"] is False
    assert "unconditional p-value" in result["forbidden_use"]

    source = (
        REPO / "scripts/observed_runs/run_planck_mes_morphology.py"
    ).read_text(encoding="utf-8")
    assert "planck_mes_bounds" not in source


def test_pr314_five_exact_evidence_blobs_and_133_of_301_control_are_unchanged() -> None:
    for path, expected_blob in PR314_BLOBS.items():
        completed = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=True,
        )
        assert completed.stdout.strip() == expected_blob

    result_path = REPO / "docs/generated/pr314_planck_pr3_smica_existing_result.json"
    assert hashlib.sha256(result_path.read_bytes()).hexdigest() == (
        "898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97"
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["finite_feature_family_p"] == "19/43"
    assert 19 * 7 == 133 and 43 * 7 == 301


def test_committed_portable_package_replays_and_cli_executes(tmp_path: Path) -> None:
    runner = _runner()
    committed = runner.replay_planck_mes_morphology_package(
        output_dir=COMMITTED_OUTPUT
    )
    assert committed["global_rank_fraction"] == "98/301"

    output = tmp_path / "cli-output"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(REPO / path) for path in ("htt", "htt/src", "htt/htt")
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/observed_runs/run_planck_mes_morphology.py",
            "--feature-package",
            str(SOURCE_PACKAGE.relative_to(REPO)),
            "--feature-metadata",
            str(SOURCE_METADATA.relative_to(REPO)),
            "--output-dir",
            str(output),
            "--residual-dipole-attribution",
            "SAG_OBSERVER_MOTION_EPS1_ZERO",
        ],
        cwd=REPO,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert runner.replay_planck_mes_morphology_package(
        output_dir=output
    )["global_rank_fraction"] == "98/301"
