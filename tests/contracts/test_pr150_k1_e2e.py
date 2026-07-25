"""PR-150 contract tests: K1 exchangeable global scan + Planck PR3 FFP10 E2E.

The idealised correlated-GRF pooled-rank super-uniformity (the falsifier), the
guards, the PR4 skip receipt, captions and mutation-exactness run everywhere;
the tests that read the heavy FFP10 E2E max-scan card and the built artifacts
skip when the card is absent (produced once by
``scripts/k1_global_maxscan.py --precision``).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import warnings
from fractions import Fraction
from pathlib import Path

import pytest

warnings.filterwarnings("ignore")

from obsstat.k1_e2e_calibration import (
    K1E2EError,
    e2e_input_manifest,
    generate_caption,
    idealised_super_uniformity,
    lint_caption,
    pooled_rank_from_e2e_card,
    pr4_npipe_skip_receipt,
    refuse_idealised_promotion,
    refuse_k1_axis_detection,
    refuse_non_super_uniform,
    refuse_pr3_pr4_joint,
    refuse_pr4_numeric,
    refuse_real_sky_p_without_e2e,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CARD = REPO_ROOT / "docs/generated/k1_global_maxscan_e2e_full.json"
GEN = REPO_ROOT / "docs/generated"
needs_card = pytest.mark.skipif(
    not CARD.is_file(), reason="FFP10 E2E max-scan card absent")


def _load_runner():
    runner_path = REPO_ROOT / "scripts/codex_harness/run_pr150_k1_e2e.py"
    spec = importlib.util.spec_from_file_location("run_pr150", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_check_normalizes_only_maintenance_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    rel = runner.OUTPUTS["manifest_e2e"]
    stored = {
        "e2e_global_pooled_rank_p": 0.039,
        "cmb_mc_dir": (
            "/owner/repo/workdir/raw/planck_ffp10/smica/cmb_mc"
        ),
        "noise_mc_dir": (
            "/owner/repo/workdir/raw/planck_ffp10/smica/noise_mc"
        ),
        "artifact_metadata": {
            "input_hashes": [
                {"path": source, "sha256": f"sha256:{'1' * 64}"},
                {"path": "input.json", "sha256": f"sha256:{'a' * 64}"},
            ],
        },
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
                runner.OUTPUTS["captions"]: {
                    "sha256": "3" * 64,
                    "hits": [],
                },
            },
        },
    }
    current = json.loads(json.dumps(stored))
    current["cmb_mc_dir"] = (
        "/tmp/worktree/workdir/raw/planck_ffp10/smica/cmb_mc"
    )
    current["noise_mc_dir"] = (
        "/tmp/worktree/workdir/raw/planck_ffp10/smica/noise_mc"
    )
    current["artifact_metadata"]["input_hashes"][0]["sha256"] = (
        f"sha256:{'4' * 64}"
    )
    current["negative_scan"]["targets"][source]["sha256"] = "5" * 64
    current["negative_scan"]["targets"][
        runner.OUTPUTS["captions"]
    ]["sha256"] = "6" * 64
    assert runner._semantic_artifact(
        rel, stored
    ) == runner._semantic_artifact(rel, current)

    current["e2e_global_pooled_rank_p"] = 0.04
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["e2e_global_pooled_rank_p"] = 0.039
    current["artifact_metadata"]["input_hashes"][1]["sha256"] = (
        f"sha256:{'b' * 64}"
    )
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["artifact_metadata"]["input_hashes"][1]["sha256"] = (
        f"sha256:{'a' * 64}"
    )
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["negative_scan"]["targets"][source]["hits"] = []
    current["cmb_mc_dir"] = "/tmp/unrelated/cmb_mc"
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["cmb_mc_dir"] = stored["cmb_mc_dir"]
    current["artifact_metadata"]["input_hashes"][0]["sha256"] = "not-a-sha"
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    stored_manifest = {
        "input_hashes": [
            f"{source}:{'1' * 64}",
            f"input.json:{'a' * 64}",
        ],
    }
    current_manifest = {
        "input_hashes": [
            f"{source}:{'2' * 64}",
            f"input.json:{'a' * 64}",
        ],
    }
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["input_hashes"][1] = f"input.json:{'b' * 64}"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)


@pytest.mark.parametrize("sample_hash_count", [-1, 0, True, 2.5])
def test_input_manifest_rejects_invalid_sample_hash_count(
    tmp_path, sample_hash_count
) -> None:
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    cmb.mkdir()
    noise.mkdir()
    (cmb / "cmb_00001.fits").touch()
    (noise / "noise_00001.fits").touch()
    with pytest.raises(K1E2EError, match="positive integer"):
        e2e_input_manifest(
            cmb, noise, sample_hash_count=sample_hash_count
        )


def test_input_manifest_rejects_sample_larger_than_ensemble(tmp_path) -> None:
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    cmb.mkdir()
    noise.mkdir()
    (cmb / "cmb_00001.fits").touch()
    (noise / "noise_00001.fits").touch()
    with pytest.raises(K1E2EError, match="exceeds"):
        e2e_input_manifest(cmb, noise, sample_hash_count=2)


def test_runner_preserves_sample_hash_count_type(tmp_path, monkeypatch) -> None:
    runner = _load_runner()
    config = runner.yaml.safe_load(
        runner.SPEC_PATH.read_text(encoding="utf-8")
    )
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    cmb.mkdir()
    noise.mkdir()
    for index in range(3):
        (cmb / f"cmb_{index:05}.fits").touch()
    (noise / "noise_00000.fits").touch()
    paths = config["data_scope"]["raw_data_paths"]
    paths["cmb_mc_dir"] = str(cmb)
    paths["noise_mc_dir"] = str(noise)
    config["model"]["e2e"]["sample_hash_count"] = 2.5

    def fail_if_hashing_is_reached(path):
        pytest.fail("fractional sample count reached file hashing")

    monkeypatch.setitem(
        runner.e2e_input_manifest.__globals__,
        "_sha256_file",
        fail_if_hashing_is_reached,
    )
    with pytest.raises(K1E2EError, match="positive integer"):
        runner.build_reports(config)


# --------------------------------------------------------------------------
# idealised correlated-GRF pooled-rank super-uniformity (the falsifier)
# --------------------------------------------------------------------------
def test_idealised_pooled_rank_is_super_uniform() -> None:
    idl = idealised_super_uniformity(n_statistics=8, rho=0.35,
                                     n_realizations=400, seed=20260724,
                                     band=0.03)
    assert idl["super_uniform"]
    # the shipped (1+b)/(N+1) pooled rank never over-rejects (conservative)
    assert idl["max_exceedance_above_uniform"] <= 0.03
    # the live anti-conservative b/(N-1) negative control over-rejects the
    # shipped form at the sub-resolution level: the shipped (1+b)/(N+1) form
    # structurally CANNOT reject below its 1/N floor, the naive form CAN -- so
    # the conservativeness check has genuine discriminating power, not a stamp
    assert idl["control_discriminates"]
    assert idl["shipped_subfloor_rejection"] == 0.0
    assert idl["anti_conservative_control_subfloor_rejection"] > 0.0
    # rejection fraction is at or below the nominal at every grid point (+band)
    for rej, a in zip(idl["rejection_fraction"], idl["alpha_grid"]):
        assert rej <= a + 0.03


def test_falsifier_kills_a_non_super_uniform_method() -> None:
    # the exchangeable pooled rank is conservative, so its exceedance is small;
    # setting the band just BELOW the measured exceedance forces rejection ---
    # the falsifier is a real threshold with discriminating power, not a rubber
    # stamp that passes any band
    idl = idealised_super_uniformity(n_statistics=8, rho=0.35,
                                     n_realizations=400, seed=20260724,
                                     band=0.5)
    measured = idl["max_exceedance_above_uniform"]
    with pytest.raises(K1E2EError, match="self-consistency check fails|not "
                       "conservative"):
        idealised_super_uniformity(n_statistics=8, rho=0.35,
                                   n_realizations=400, seed=20260724,
                                   band=measured - 0.01)
    with pytest.raises(K1E2EError, match="falsified"):
        refuse_non_super_uniform(False)


@pytest.mark.parametrize("band", [float("inf"), float("nan"), 1.0, 2.0])
def test_idealised_check_rejects_non_discriminating_band(band) -> None:
    with pytest.raises(K1E2EError, match="finite and less than 1"):
        idealised_super_uniformity(
            n_statistics=8,
            rho=0.35,
            n_realizations=400,
            seed=20260724,
            band=band,
        )


# --------------------------------------------------------------------------
# non-numeric PR4/NPIPE external-blocker receipt
# --------------------------------------------------------------------------
def test_pr4_skip_receipt_is_non_numeric() -> None:
    r = pr4_npipe_skip_receipt()
    assert r["pr4_npipe_status"] == "EXTERNALLY_BLOCKED_MISSING_SIMULATION_ACCESS"
    assert r["observed_map_status"] == "public_in_PLA"
    assert r["observed_map_id"] == "COM_CMB_IQU-sevem_2048_R4.00.fits"
    assert r["simulation_status"] == "not_ingested_in_PLA"
    assert r["analysis_status"] == "externally_blocked"
    assert r["numeric_outputs"] == "none"
    assert r["pr3_plus_pr4_joint_result"] == "not_produced"


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def test_guards_reject_the_forbidden_moves() -> None:
    with pytest.raises(K1E2EError, match="promoted to a"):
        refuse_idealised_promotion("idealised_is_planck_calibration")
    with pytest.raises(K1E2EError, match="without the E2E ensemble"):
        refuse_real_sky_p_without_e2e(False, "real_sky_p")
    with pytest.raises(K1E2EError, match="PR4 NPIPE numeric"):
        refuse_pr4_numeric("pr4_p_value")
    with pytest.raises(K1E2EError, match="combined result"):
        refuse_pr3_pr4_joint("pr3_pr4_joint")
    with pytest.raises(K1E2EError, match="directional detection"):
        refuse_k1_axis_detection("k1_axis")
    # admissible inputs do NOT raise
    refuse_idealised_promotion("method_calibration_only")
    refuse_real_sky_p_without_e2e(True, "e2e_conditional_p")
    refuse_k1_axis_detection("feature_extraction_only")


def test_caption_lint_blocks_a_detection_phrase() -> None:
    with pytest.raises(K1E2EError, match="forbidden caption"):
        lint_caption("this establishes shear detected in the K1 sky")


# --------------------------------------------------------------------------
# E2E card -> finite-ensemble pooled rank (data-gated)
# --------------------------------------------------------------------------
@needs_card
def test_pooled_rank_from_real_e2e_card() -> None:
    pr = pooled_rank_from_e2e_card(CARD)
    n = pr["simulation_count"]
    assert n == 999
    # The global p uses (1+b)/(N+1) arithmetic on its finite-rank support
    # grid. Noise reuse is disclosed separately, so grid membership alone is
    # not promoted to an iid/exchangeability theorem.
    assert pr["on_finite_rank_support_grid"]
    assert pr["resolution_floor"] == pytest.approx(1.0 / (n + 1))
    assert pr["e2e_global_pooled_rank_p"] >= pr["resolution_floor"]
    # the reported p lands exactly on a (1+b)/(N+1) grid node
    b = round(pr["e2e_global_pooled_rank_p"] * (n + 1)) - 1
    assert 0 <= b <= n
    assert pr["e2e_global_pooled_rank_p"] == pytest.approx(
        float(Fraction(1 + b, n + 1)), abs=1e-9)
    # the observed max-scan score is carried through (not lost to a null)
    assert pr["observed_max_scan_score"] is not None
    assert pr["per_statistic_local_p"]     # per-statistic local p-values present
    # the look-elsewhere global p equals the pooled rank (over the 6 statistics)
    assert pr["look_elsewhere_global_p"] == pr["e2e_global_pooled_rank_p"]
    assert pr["unique_noise_realization_count"] == 300
    assert pr["noise_realizations_reused"]
    assert not pr["exact_iid_or_exchangeability_claimed"]
    sensitivity = pr["noise_reuse_sensitivity"]
    assert sensitivity["noise_cluster_bootstrap"]["replicates"] == 20000
    assert len(sensitivity["cycle_split_pooled_ranks"]) == 4


def test_pooled_rank_rejects_off_grid_and_sub_floor_cards(tmp_path) -> None:
    # P1 regression: the grid/floor validation is load-bearing on the ACTUAL
    # reported global_p, not a grid-snapped surrogate. A sub-resolution p that
    # snaps onto the floor node must still be REFUSED (PR-135 forbids it).
    def _card(gp: float) -> Path:
        p = tmp_path / f"card_{gp}.json"
        p.write_text(json.dumps({
            "statistics": [f"stat_{i}" for i in range(6)],
            "result": {"global_p": gp,
                       "local_p": {f"stat_{i}": gp for i in range(6)},
                       "observed_max_score": 1.0},
            "config": {"n_sims": 300}}))
        return p
    # 0.002 < floor 1/301 (0.00332); round(0.002*301)=1 snaps to 1/301 and would
    # pass a surrogate check, but the raw value is off-grid AND sub-floor -> raise
    with pytest.raises(K1E2EError, match="support grid|resolution floor"):
        pooled_rank_from_e2e_card(_card(0.002))
    # a value strictly between two grid nodes is off-grid -> raise
    with pytest.raises(K1E2EError, match="support grid"):
        pooled_rank_from_e2e_card(_card(0.05))
    # an exact grid node at/above the floor is accepted
    ok = pooled_rank_from_e2e_card(_card(11.0 / 301.0))
    assert ok["e2e_global_pooled_rank_p"] == pytest.approx(11.0 / 301.0)


@pytest.mark.parametrize("mutation", [
    "missing_observed_score",
    "missing_local_p",
    "wrong_local_p_keys",
    "string_reuse",
    "partial_reuse",
])
def test_pooled_rank_rejects_incomplete_card_evidence(
    tmp_path, mutation
) -> None:
    statistics = [f"stat_{i}" for i in range(6)]
    result = {
        "global_p": 11.0 / 301.0,
        "local_p": {name: 0.1 for name in statistics},
        "observed_max_score": 1.0,
        "noise_reuse_sensitivity": {
            "cycle_split_pooled_ranks": [{"pooled_rank_p": 0.1}],
            "noise_cluster_bootstrap": {
                "replicates": 10,
                "percentile_95_interval": [0.05, 0.2],
            },
        },
    }
    card = {
        "statistics": statistics,
        "result": result,
        "config": {"n_sims": 300},
        "e2e_sims": {"n_noise_used": 10},
    }
    if mutation == "missing_observed_score":
        result.pop("observed_max_score")
    elif mutation == "missing_local_p":
        result.pop("local_p")
    elif mutation == "wrong_local_p_keys":
        result["local_p"] = {"other": 0.1}
    elif mutation == "string_reuse":
        result["noise_reuse_sensitivity"] = "yes"
    elif mutation == "partial_reuse":
        result["noise_reuse_sensitivity"] = {
            "cycle_split_pooled_ranks": [],
        }
    path = tmp_path / f"{mutation}.json"
    path.write_text(json.dumps(card), encoding="utf-8")
    with pytest.raises(K1E2EError, match="must report|six unique|sensitivity"):
        pooled_rank_from_e2e_card(path)


@needs_card
def test_built_artifacts_are_current_and_honest() -> None:
    # the E2E input manifest records the full available ensemble + sample hashes
    man = json.loads((GEN / "pr150_e2e_input_manifest.json")
                     .read_text(encoding="utf-8"))
    assert man["cmb_mc_count"] == 999
    assert man["noise_mc_count"] == 300
    assert len(man["sample_sha256"]) == 4
    assert man["observed_null_byte_equivalent_path"]
    # the pooled-rank artifact reports all 999 usable CMB sims
    pr = json.loads((GEN / "pr150_e2e_pooled_rank.json")
                    .read_text(encoding="utf-8"))
    assert pr["simulation_count"] == 999
    retention = json.loads((GEN / "pr150_compact_retention_receipt.json")
                           .read_text(encoding="utf-8"))
    assert retention["cache_reproducibility_green"]
    assert retention["reduced_manifest_creation_time_gate_flag"] is False
    assert "separate content-addressed cache-gate" in \
        retention["gate_status_authority"]
    assert retention["full_raw_to_compact_map_replay_count"] == 1299
    assert retention["full_999_by_6_result_replay_exact"]
    assert retention["raw_sources_present"]
    assert not retention["raw_deletion_executed"]
    assert not retention["pr4_replacement_ready"]
    assert not retention["safe_to_delete_raw"]
    assert retention["compact_cache"]["sha256"] == \
        retention["independent_backup"]["sha256"]
    assert retention["independent_backup"]["distinct_filesystem_device"]
    # the caption names the 999 CMB and 300 unique-noise contract
    cap = json.loads((GEN / "pr150_captions.json")
                     .read_text(encoding="utf-8"))["captions"]["summary"]
    assert "999 usable CMB" in cap and "300 unique noise" in cap
    lint_caption(cap)
    required_metadata = {
        "owner", "implementation_scope", "claim_tier", "transfer_source",
        "config_hash", "input_hashes", "sky_support_status", "mask_status",
        "covariance_status", "null_mock_status", "caveats",
        "generating_command", "git_commit", "worktree_state",
    }
    for name in (
            "pr150_idealised_super_uniformity.json",
            "pr150_e2e_input_manifest.json",
            "pr150_e2e_pooled_rank.json",
            "pr150_compact_retention_receipt.json",
            "pr150_pr4_skip_receipt.json",
            "pr150_captions.json",
            "pr150_mutation_report.json",
            "pr150_artifact_manifest.json"):
        payload = json.loads((GEN / name).read_text(encoding="utf-8"))
        metadata = payload["artifact_metadata"]
        assert required_metadata <= set(metadata), name
        assert metadata["claim_tier"] == "conditional"
        assert metadata["config_hash"].startswith("sha256:")
        assert metadata["input_hashes"]


@needs_card
def test_runner_check_mode_is_current_and_mutations_killed() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr150_k1_e2e.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((GEN / "pr150_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads((GEN / "pr150_artifact_manifest.json")
                          .read_text(encoding="utf-8"))
    assert manifest["raw_data_pins"]["e2e_card_sha256"]
    assert manifest["raw_data_pins"]["reduced_manifest_sha256"]
    assert manifest["raw_data_pins"]["cache_gate_sha256"]
    assert manifest["raw_data_pins"]["compact_cache_sha256"].startswith(
        "sha256:")
    # the PR4 external-blocker receipt is a non-numeric artifact on disk
    pr4 = json.loads((GEN / "pr150_pr4_skip_receipt.json")
                     .read_text(encoding="utf-8"))
    assert pr4["numeric_outputs"] == "none"
    assert pr4["analysis_status"] == "externally_blocked"
