"""PR-152 contract tests: ACT DR6 raw-QE gate + release-simulation cross-fit.

The cross-fit mean field, exact rank, injection-law, availability decision,
inventory, guards and captions run everywhere on small synthetic low-multipole
arrays; the tests that read the built artifacts skip when the heavy real-ACT
card is absent.
"""
from __future__ import annotations

import json
import copy
import hashlib
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

warnings.filterwarnings("ignore")

from obsstat.act_raw_qe_gate import (
    ACTRawQEError,
    act_dr6_lensing_inventory,
    algebraic_finite_rank_ceiling,
    generate_caption,
    injection_law_distinction,
    leave_one_sim_crossfit_mean_field,
    observation_inclusive_crossfit_mean_field,
    lint_caption,
    refuse_act_detection,
    refuse_bianchi_from_act,
    refuse_naive_self_mean_field,
    refuse_pre_qe_transfer_label,
    refuse_raw_qe_without_inputs,
    refuse_sky_power_limit_without_raw_qe,
    upstream_availability_decision,
    validate_raw_qe_execution_receipt,
)
from scripts.act_raw_qe_card import (
    CACHE_SCHEMA,
    _file_record,
    build_input_manifest,
    cache_is_bound,
)
from scripts.codex_harness.run_pr152_act_raw_qe import (
    _render,
    _validate_card,
    validate_artifact_metadata,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN = REPO_ROOT / "docs/generated"
CARD = GEN / "act_raw_qe_card.json"


def _record(path: Path) -> dict:
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _card_with_isolated_cache(tmp_path: Path) -> dict:
    """Bind the tracked card to a tiny cache so each validator mutation is causal."""

    card = json.loads(CARD.read_text(encoding="utf-8"))
    cache = tmp_path / "act_lowl_cache.npz"
    cache.write_bytes(b"isolated PR-152 validator cache fixture\n")
    card["input_provenance"]["cache_path"] = str(cache)
    card["input_provenance"]["cache_sha256"] = _record(cache)["sha256"]
    return card


def _recorded_cache_path() -> Path:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    path = Path(card["input_provenance"]["cache_path"])
    return path if path.is_absolute() else REPO_ROOT / path


def _receipt(tmp_path: Path) -> dict:
    tmp_path.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in (
        "filtering_config", "response_normalization", "analysis_mask",
        "software_lock", "simulation_input_manifest", "qe_output",
        "rdn0_output",
    ):
        path = tmp_path / f"{name}.dat"
        path.write_bytes(f"authenticated {name}\n".encode())
        files[name] = _record(path)
    splits = []
    for split_id in range(4):
        path = tmp_path / f"split_{split_id}.fits"
        path.write_bytes(f"authenticated split {split_id}\n".encode())
        splits.append({"split_id": split_id, **_record(path)})
    receipt = {
        "schema": "htt.act.raw_qe_execution_receipt.v2",
        "status": "RAW_QE_RDN0_EXECUTED",
        "four_split_maps": splits,
        **files,
        "input_checksums_verified": True,
    }
    # The validator computes the canonical identity from reopened input bytes.
    input_identity = validate_raw_qe_execution_receipt(receipt)[
        "verified_input_identity_sha256"]
    command = "so-lenspipe run pinned-config.yaml --rdn0"
    log_payload = {
        "schema": "htt.act.raw_qe_execution_log.v1",
        "status": "COMPLETE",
        "command": command,
        "exit_code": 0,
        "input_identity_sha256": input_identity,
        "software_lock_sha256": files["software_lock"]["sha256"],
        "simulation_input_manifest_sha256": files[
            "simulation_input_manifest"]["sha256"],
        "qe_output_sha256": files["qe_output"]["sha256"],
        "rdn0_output_sha256": files["rdn0_output"]["sha256"],
    }
    log_path = tmp_path / "execution_log.json"
    log_path.write_text(json.dumps(log_payload, sort_keys=True))
    log_record = _record(log_path)
    receipt["execution_log"] = log_record
    receipt["execution"] = {
        "command": command,
        "exit_code": 0,
        "input_identity_sha256": input_identity,
        "software_lock_sha256": files["software_lock"]["sha256"],
        "simulation_input_manifest_sha256": files[
            "simulation_input_manifest"]["sha256"],
        "qe_output_sha256": files["qe_output"]["sha256"],
        "rdn0_output_sha256": files["rdn0_output"]["sha256"],
        "execution_log_sha256": log_record["sha256"],
    }
    return receipt


def _synthetic(nmodes=117, nsim=400, seed=0):
    rng = np.random.default_rng(seed)
    wm = np.ones(nmodes)
    sim = (rng.standard_normal((nsim, nmodes))
           + 1j * rng.standard_normal((nsim, nmodes)))
    data = rng.standard_normal(nmodes) + 1j * rng.standard_normal(nmodes)
    return sim, data, wm


def test_crossfit_removes_self_mean_field_bias() -> None:
    sim, data, wm = _synthetic()
    cf = leave_one_sim_crossfit_mean_field(sim, data, wm)
    # the naive self-inclusive mean field deflates the sim residual band power
    # (biased low) relative to the leave-one-simulation cross-fit
    assert cf["naive_self_mean_field_deflates_residual"]
    assert cf["naive_sim_band_power_mean"] < cf["crossfit_sim_band_power_mean"]
    assert cf["self_mean_field_bias_ratio_naive_over_crossfit"] < 1.0
    # both pooled ranks are on (0, 1]; the cross-fit is the reported one
    assert 0.0 < cf["crossfit_pooled_rank_p"] <= 1.0
    assert not cf["joint_exchangeability_exact"]
    assert cf["simulation_over_data_residual_variance_ratio"] == pytest.approx(
        400**2 / (400**2 - 1))


def test_observation_inclusive_crossfit_is_permutation_equivariant() -> None:
    sim, data, wm = _synthetic(nsim=40)
    primary = observation_inclusive_crossfit_mean_field(sim, data, wm)
    assert primary["permutation_equivariant_transform"]
    assert primary["n_exchangeable_units"] == 41
    assert primary["support_resolution"] == pytest.approx(1 / 41)
    assert ((primary["upper_exceedance_count"] + 1) / 41
            == pytest.approx(primary[
                "observation_inclusive_crossfit_pooled_rank_p"]))

    # Move a simulation into the pseudo-observation slot. Recomputing the full
    # transform merely permutes the same 41 scores.
    combined = np.concatenate([data[None, :], sim], axis=0)
    perm = np.r_[7, np.arange(7), np.arange(8, 41)]
    moved = combined[perm]
    rerun = observation_inclusive_crossfit_mean_field(moved[1:], moved[0], wm)
    total_a = np.sort(np.r_[primary["S_data"],
                            primary["simulation_band_powers"]])
    total_b = np.sort(np.r_[rerun["S_data"], rerun["simulation_band_powers"]])
    assert np.allclose(total_a, total_b)
    caption_crossfit = dict(primary)
    caption_crossfit.update({
        "analysis_ell_range": [2, 10],
        "release_validated_ell_range": [40, 763],
    })
    caption = generate_caption(
        {"present_products": {"x": "y"}}, caption_crossfit,
        {"decision": "DEFER_RAW_QE_RDN0_PUBLIC_INPUTS_LARGE_RECONSTRUCTION"},
    )
    assert "41 units" in caption
    assert "400 simulations" not in caption


def test_algebraic_finite_rank_ceiling_low_ell_band() -> None:
    r = algebraic_finite_rank_ceiling(n_sims=400, ell_min=2, ell_max=10)
    # sum_{ell=2..10}(2 ell + 1) = 117 real harmonic dof
    assert r["n_real_harmonic_dof"] == 117
    assert r["finite_rank_ceiling"] == 117       # modes-limited (399 > 117)
    assert r["realized_numerical_rank_measured"] is False
    assert r["rank_limited_by"] == "modes"
    # with few sims the sample rank binds
    r2 = algebraic_finite_rank_ceiling(n_sims=20, ell_min=2, ell_max=10)
    assert r2["finite_rank_ceiling"] == 19
    assert r2["rank_limited_by"] == "sample"


def test_injection_law_distinction() -> None:
    sim, data, wm = _synthetic()
    cf = leave_one_sim_crossfit_mean_field(sim, data, wm)
    inj = injection_law_distinction(cf["crossfit_sim_band_powers"],
                                    injection_amplitude=0.2, seed=1)
    # the stochastic injection is absorbed into the same null (~uniform mean p);
    # the fixed-template injection is a coherent offset that shifts the rank
    assert inj["laws_distinct"]
    assert (inj["fixed_template_mean_pooled_rank_p"]
            < inj["stochastic_mean_pooled_rank_p"])


def test_availability_decision_defers_public_raw_qe_without_local_run(
        tmp_path) -> None:
    inv = act_dr6_lensing_inventory(
        present={"kappa_alm_data": "x"}, raw_qe_inputs_on_disk=False,
        validated_ell_range=(40, 763), reference_url="u")
    assert "four_split_cmb_maps" in inv["local_missing_raw_qe_inputs"]
    dec = upstream_availability_decision(inv)
    assert dec["decision"] == "DEFER_RAW_QE_RDN0_PUBLIC_INPUTS_LARGE_RECONSTRUCTION"
    assert dec["closed_result"] == "release_simulation_conditioned_null_comparison"
    assert dec["raw_qe_stage_status"] == "publicly_reproducible_not_executed_locally"
    # A bare path/existence boolean is intentionally insufficient.
    inv2 = act_dr6_lensing_inventory(
        present={}, raw_qe_inputs_on_disk=True,
        validated_ell_range=(40, 763), reference_url="u")
    assert not upstream_availability_decision(inv2)["raw_qe_available"]
    # The positive branch requires a typed, content-addressed execution receipt.
    inv3 = act_dr6_lensing_inventory(
        present={}, raw_qe_inputs_on_disk=True,
        validated_ell_range=(40, 763), reference_url="u",
        raw_qe_execution_receipt=_receipt(tmp_path))
    assert upstream_availability_decision(inv3)["raw_qe_available"]
    assert not inv3["local_missing_raw_qe_inputs"]


@pytest.mark.parametrize("missing", [
    "schema", "status", "four_split_maps", "filtering_config",
    "response_normalization", "analysis_mask", "software_lock",
    "simulation_input_manifest", "qe_output", "rdn0_output",
    "execution_log", "input_checksums_verified", "execution",
])
def test_raw_qe_receipt_is_fail_closed_for_every_required_element(
        missing, tmp_path) -> None:
    receipt = _receipt(tmp_path)
    receipt.pop(missing)
    assert not validate_raw_qe_execution_receipt(receipt)["ready"]


def test_raw_qe_receipt_rejects_syntactic_digest_self_assertion() -> None:
    digest = "sha256:" + "0" * 64
    record = {"path": "/does/not/exist", "size_bytes": 1, "sha256": digest}
    receipt = {
        "schema": "htt.act.raw_qe_execution_receipt.v2",
        "status": "RAW_QE_RDN0_EXECUTED",
        "four_split_maps": [
            {"split_id": split_id, **record} for split_id in range(4)],
        "filtering_config": record,
        "response_normalization": record,
        "analysis_mask": record,
        "software_lock": record,
        "simulation_input_manifest": record,
        "qe_output": record,
        "rdn0_output": record,
        "execution_log": record,
        "input_checksums_verified": True,
        "execution": {
            "command": "echo never-ran", "exit_code": 0,
            "input_identity_sha256": digest,
            "software_lock_sha256": digest,
            "simulation_input_manifest_sha256": digest,
            "qe_output_sha256": digest,
            "rdn0_output_sha256": digest,
            "execution_log_sha256": digest,
        },
    }
    result = validate_raw_qe_execution_receipt(receipt)
    assert result["ready"] is False
    assert any("file_absent" in item for item in result["missing_or_invalid"])


def test_raw_qe_receipt_rejects_byte_and_lineage_drift(tmp_path) -> None:
    receipt = _receipt(tmp_path)
    assert validate_raw_qe_execution_receipt(receipt)["ready"] is True

    qe_path = Path(receipt["qe_output"]["path"])
    qe_path.write_bytes(qe_path.read_bytes() + b"tamper")
    changed = validate_raw_qe_execution_receipt(receipt)
    assert changed["ready"] is False
    assert "qe_output:size_mismatch" in changed["missing_or_invalid"]
    assert "qe_output:hash_mismatch" in changed["missing_or_invalid"]

    receipt = _receipt(tmp_path / "fresh")
    receipt["execution"]["command"] = "echo never-ran"
    lineage = validate_raw_qe_execution_receipt(receipt)
    assert lineage["ready"] is False
    assert "execution_log:command_mismatch" in lineage["missing_or_invalid"]


def test_act_cache_binding_rejects_key_or_shape_drift(tmp_path) -> None:
    cache = tmp_path / "cache.npz"
    np.savez(
        cache,
        schema=np.asarray(CACHE_SCHEMA),
        input_manifest_sha256=np.asarray("sha256:" + "b" * 64),
        data_low=np.ones(3, dtype=complex),
        sim_low=np.ones((4, 3), dtype=complex),
        wm=np.ones(3),
    )
    assert cache_is_bound(
        cache, manifest_sha256="sha256:" + "b" * 64,
        expected_simulations=4)
    assert not cache_is_bound(
        cache, manifest_sha256="sha256:" + "c" * 64,
        expected_simulations=4)
    assert not cache_is_bound(
        cache, manifest_sha256="sha256:" + "b" * 64,
        expected_simulations=3)


def test_full_file_digest_changes_after_non_head_byte_mutation(tmp_path) -> None:
    path = tmp_path / "large-enough.bin"
    path.write_bytes(b"a" * (2 << 20))
    first = _file_record(path)
    with path.open("r+b") as stream:
        stream.seek((1 << 20) + 7)
        stream.write(b"b")
    second = _file_record(path)
    assert first["size_bytes"] == second["size_bytes"]
    assert first["sha256"] != second["sha256"]


def test_production_input_manifest_requires_exactly_400() -> None:
    with pytest.raises(ValueError, match="exactly 400"):
        build_input_manifest([Path("x")] * 399)
    with pytest.raises(ValueError, match="exactly 400"):
        build_input_manifest([Path("x")] * 401)


def test_scientific_renderer_preserves_tiny_nonzero_values() -> None:
    payload = json.loads(_render({"p": 8.422603573854381e-17}))
    assert payload["p"] == pytest.approx(8.422603573854381e-17)
    assert payload["p"] > 0


def test_guards_reject_forbidden_moves() -> None:
    with pytest.raises(ACTRawQEError, match="pre-QE"):
        refuse_pre_qe_transfer_label("pre_qe_transfer")
    with pytest.raises(ACTRawQEError, match="sky-power"):
        refuse_sky_power_limit_without_raw_qe(False, "l2_10_sky_power_limit")
    with pytest.raises(ACTRawQEError, match="leave-one-simulation"):
        refuse_naive_self_mean_field(False)
    with pytest.raises(ACTRawQEError, match="detection"):
        refuse_act_detection("act_kappa_detection")
    with pytest.raises(ACTRawQEError, match="Bianchi-family"):
        refuse_bianchi_from_act("bianchi_family")
    with pytest.raises(ACTRawQEError, match="upstream"):
        refuse_raw_qe_without_inputs(False, "raw_qe_inference")
    # admissible inputs do NOT raise
    refuse_naive_self_mean_field(True)
    refuse_sky_power_limit_without_raw_qe(True, "l2_10_sky_power_limit")
    refuse_raw_qe_without_inputs(True, "raw_qe_inference")


def test_caption_lint_blocks_a_detection_phrase() -> None:
    with pytest.raises(ACTRawQEError, match="forbidden caption"):
        lint_caption("this is an ACT kappa detection with anisotropy detected")


@pytest.mark.parametrize("field", [
    "schema", "n_sims", "n_exchangeable_units", "support", "p",
    "score", "rank", "decision",
])
def test_heavy_card_validator_kills_semantic_mutations(
        field: str, tmp_path: Path) -> None:
    import yaml

    card = _card_with_isolated_cache(tmp_path)
    spec = yaml.safe_load((REPO_ROOT /
        "docs/research_program/long_horizon_rescue/pr152_spec.yaml")
        .read_text(encoding="utf-8"))
    _validate_card(card, spec)
    broken = copy.deepcopy(card)
    if field == "schema":
        broken["schema"] = "wrong"
    elif field == "n_sims":
        broken["config"]["n_sims"] = 399
    elif field == "n_exchangeable_units":
        broken["crossfit_mean_field"]["n_exchangeable_units"] = 400
    elif field == "support":
        broken["crossfit_mean_field"]["support_resolution"] = 0.5
    elif field == "p":
        broken["crossfit_mean_field"][
            "observation_inclusive_crossfit_pooled_rank_p"] = 0.5
    elif field == "score":
        broken["crossfit_mean_field"]["simulation_band_powers"][0] = \
            float("nan")
    elif field == "rank":
        broken["rank_ceiling"]["finite_rank_ceiling"] = 116
    elif field == "decision":
        broken["availability_decision"]["raw_qe_available"] = True
    with pytest.raises(SystemExit, match="invalid ACT heavy card"):
        _validate_card(broken, spec)


# --------------------------------------------------------------------------
# built artifacts from the real ACT card (data-gated)
# --------------------------------------------------------------------------
def test_runner_check_and_real_artifacts() -> None:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr152_act_raw_qe.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if _recorded_cache_path().is_file():
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode == 1
        assert "cache bytes do not match provenance" in result.stderr
    manifest = json.loads(
        (GEN / "pr152_artifact_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["raw_data_pins"]["act_raw_qe_card_sha256"] == (
        _record(CARD)["sha256"]
    )
    assert manifest["raw_data_pins"]["low_l_cache_sha256"] == (
        card["input_provenance"]["cache_sha256"]
    )
    for relative, expected in manifest["artifacts"].items():
        assert hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest() == (
            expected
        )
    dec = json.loads((GEN / "pr152_availability_decision.json")
                     .read_text(encoding="utf-8"))
    assert dec["decision"] == "DEFER_RAW_QE_RDN0_PUBLIC_INPUTS_LARGE_RECONSTRUCTION"
    inv = json.loads((GEN / "pr152_inventory.json").read_text(encoding="utf-8"))
    assert not inv["raw_qe_inputs_on_disk"]
    assert "four_split_cmb_maps" in inv["local_missing_raw_qe_inputs"]
    cf = json.loads((GEN / "pr152_crossfit_mean_field.json")
                    .read_text(encoding="utf-8"))
    assert cf["permutation_equivariant_transform"]
    assert cf["n_exchangeable_units"] == 401
    assert 0.0 < cf["observation_inclusive_crossfit_pooled_rank_p"] <= 1.0
    sensitivity = json.loads((GEN / "pr152_legacy_mean_field_sensitivity.json")
                             .read_text(encoding="utf-8"))
    assert not sensitivity["joint_exchangeability_exact"]
    rank = json.loads((GEN / "pr152_rank_ceiling.json")
                      .read_text(encoding="utf-8"))
    assert rank["finite_rank_ceiling"] == 117
    assert rank["realized_numerical_rank_measured"] is False
    report = json.loads((GEN / "pr152_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    for name in (
        "pr152_inventory.json", "pr152_crossfit_mean_field.json",
        "pr152_legacy_mean_field_sensitivity.json", "pr152_rank_ceiling.json",
        "pr152_injection_law.json", "pr152_availability_decision.json",
        "pr152_captions.json", "pr152_mutation_report.json",
    ):
        validate_artifact_metadata(json.loads((GEN / name).read_text()))
    assert cf["analysis_ell_range"] == [2, 10]
    assert cf["release_validated_ell_range"] == [40, 763]
    assert not cf["inside_release_validated_range"]
    assert cf["data_mean_field_band_power"] > 0
