from __future__ import annotations

import copy
import json
import os
import shlex
import subprocess
from pathlib import Path

import healpy as hp
import numpy as np
import pytest

from obsstat.act_inband_modulation import (
    ActInbandModulationError,
    CANDIDATE,
    NO_RESOLVED,
    UNRESOLVED,
    build_mask_design,
    delete_simulation_rank_replicates,
    fractional_variance_features,
    observation_inclusive_loo_scores,
    pooled_upper_rank,
    rank_resolution_certificate,
    raw_records_only_root,
    real_y2_columns,
    strict_band_alm,
    strict_integer_support,
    terminal_result,
)
from scripts.codex_harness.run_pr177_act_dr6_inband_modulation import (
    EXPECTED_SUPPORT,
    result_support_errors,
    source_authority_errors,
    validate_feature_card,
)
from scripts.act_inband_modulation_card import (
    authenticate_sources,
    extraction_lock,
    resource_receipt_errors,
)


REPO = Path(__file__).resolve().parents[2]
FEATURE = REPO / "docs/generated/pr177_act_inband_feature_card.json"
RESULT = REPO / "docs/generated/pr177_act_modulation_result.json"
MC = REPO / "docs/generated/pr177_mc_resolution.json"
MUTATION = REPO / "docs/generated/pr177_mutation_report.json"
MANIFEST = REPO / "docs/generated/pr177_artifact_manifest.json"
DEEP_REPLAY = REPO / "docs/generated/pr177_deep_replay_receipt.json"


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _relation(value: str) -> dict[str, str]:
    return {"relation_to_alpha": value}


def test_strict_support_and_raw_authority_root_are_frozen() -> None:
    support = strict_integer_support(strict_lower=40, strict_upper=763)
    assert len(support) == 722
    assert support[0] == 41
    assert support[-1] == 762
    source = _json(REPO / "docs/generated/act_raw_qe_card.json")
    embedded = source["input_provenance"]["input_manifest"]
    assert raw_records_only_root(embedded) == (
        "63b65bfd0ef6593cbf6cfa11602f0e09a589932bfc907aeb31ecbc09a2142968"
    )


def test_real_y2_basis_and_mask_control_recover_registered_injection() -> None:
    nside = 16
    pixels = np.arange(hp.nside2npix(nside))
    x, y, z = hp.pix2vec(nside, pixels)
    y2 = real_y2_columns(x, y, z)
    full_sky_gram = y2.T @ y2 * (4.0 * np.pi / pixels.size)
    assert np.allclose(full_sky_gram, np.eye(5), rtol=0.0, atol=3.0e-3)
    mask = 0.995 + 0.004 * y2[:, 0] / np.max(np.abs(y2[:, 0]))
    design = build_mask_design(mask, nside=nside, threshold=0.99)
    nuisance = mask**2 - np.mean(mask**2)
    amplitude = 0.04
    variance = 1.0 + amplitude * y2[:, 3] + 2.0 * nuisance
    feature = fractional_variance_features(np.sqrt(variance), design)
    controlled = np.asarray(feature["q_controlled"])
    assert np.isclose(controlled[3], amplitude / variance.mean(), atol=2.0e-12)
    assert np.max(np.abs(np.delete(controlled, 3))) < 2.0e-9
    assert not np.allclose(feature["q_raw"], feature["q_controlled"], atol=1.0e-12)


def test_strict_band_alm_excludes_both_prose_endpoints() -> None:
    lmax = 8
    ell, _ = hp.Alm.getlm(lmax)
    alm = np.arange(hp.Alm.getsize(lmax), dtype=float).astype(complex)
    compact = strict_band_alm(alm, integer_min=3, integer_max=6)
    target_ell, target_m = hp.Alm.getlm(6)
    selected = target_ell >= 3
    source = hp.Alm.getidx(lmax, target_ell[selected], target_m[selected])
    assert np.all(compact[~selected] == 0.0)
    assert np.array_equal(compact[selected], alm[source])
    assert np.all(ell >= 0)


def test_loo_scores_are_permutation_equivariant_and_rank_is_conservative() -> None:
    rng = np.random.default_rng(20260720)
    features = rng.normal(size=(30, 5))
    original = observation_inclusive_loo_scores(features)["scores"]
    permutation = rng.permutation(features.shape[0])
    permuted = observation_inclusive_loo_scores(features[permutation])["scores"]
    assert np.allclose(permuted, original[permutation], rtol=1.0e-11, atol=1.0e-11)
    rank = pooled_upper_rank([2.0, 2.0, 1.0, 3.0])
    assert rank["exceedance_count"] == 2
    assert rank["tie_count"] == 1
    assert rank["rank_fraction"] == "3/4"


def test_full_delete_simulation_recomputation_has_exact_lineage() -> None:
    rng = np.random.default_rng(177)
    raw = rng.normal(size=(401, 5))
    controlled = raw + 0.05 * rng.normal(size=(401, 5))
    change = np.sum((raw - controlled) ** 2, axis=1)
    receipt = delete_simulation_rank_replicates(raw, controlled, change)
    assert receipt["replicate_count"] == 400
    assert receipt["deleted_units_unique"] is True
    assert receipt["observed_unit_deleted"] is False
    assert receipt["full_sample_ensemble_transform_reused"] is False
    assert receipt["lineage_status"] == "CERTIFIED_FOR_PR177_RANK_FUNCTIONAL"
    assert receipt["replicates"][0]["deleted_unit"] == "sim-0001"
    assert receipt["replicates"][-1]["deleted_unit"] == "sim-0400"


def test_resolution_guard_and_terminal_truth_table_are_closed() -> None:
    resolved_below = rank_resolution_certificate(
        full_rank=1.0 / 401.0,
        delete_ranks=[1.0 / 400.0] * 400,
    )
    assert resolved_below["relation_to_alpha"] == "RESOLVED_BELOW_ALPHA"
    crossing = rank_resolution_certificate(
        full_rank=20.0 / 401.0,
        delete_ranks=[19.0 / 400.0, 21.0 / 400.0] * 200,
    )
    assert crossing["relation_to_alpha"] == "UNRESOLVED_AT_ALPHA"
    below = _relation("RESOLVED_BELOW_ALPHA")
    above = _relation("RESOLVED_ABOVE_ALPHA")
    unresolved = _relation("UNRESOLVED_AT_ALPHA")
    assert terminal_result(controlled=below, raw=below, mask_change=above, eligibility_passed=True)["scientific_result"] == CANDIDATE
    assert terminal_result(controlled=above, raw=below, mask_change=above, eligibility_passed=True)["scientific_result"] == NO_RESOLVED
    assert terminal_result(controlled=below, raw=unresolved, mask_change=above, eligibility_passed=True)["scientific_result"] == UNRESOLVED
    assert terminal_result(controlled=below, raw=above, mask_change=above, eligibility_passed=True)["scientific_result"] == NO_RESOLVED


def test_real_feature_card_is_source_bound_and_not_a_science_promotion() -> None:
    import yaml

    card = _json(FEATURE)
    spec = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml").read_text()
    )
    assert validate_feature_card(card, spec) == []
    assert card["unit_count"] == 401
    assert card["release_simulation_count"] == 400
    assert card["analysis_support"]["integer_min"] == 41
    assert card["analysis_support"]["integer_max"] == 762
    assert card["raw_payload_rehashed_by_pr177"] is False
    assert card["scientific_result"] is None


def test_validator_rejects_resealed_feature_and_source_mutations() -> None:
    import yaml
    from obsstat.act_inband_modulation import semantic_digest

    card = _json(FEATURE)
    spec = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml").read_text()
    )
    for mutate in (
        lambda value: value["analysis_support"].update({"integer_min": 40}),
        lambda value: value["units"][0]["feature"]["q_raw"].__setitem__(0, value["units"][0]["feature"]["q_raw"][0] + 1.0),
        lambda value: value["units"][1].update({"source_sha256": "0" * 64}),
        lambda value: value["input_hashes"].update(
            {"docs/generated/act_raw_qe_card.json": "0" * 64}
        ),
        lambda value: value.update({"public_use": True}),
    ):
        forged = copy.deepcopy(card)
        mutate(forged)
        forged["semantic_digest"] = semantic_digest(forged)
        assert validate_feature_card(forged, spec)


def test_frozen_pr152_authority_rejects_canonical_but_changed_sources() -> None:
    import yaml

    spec = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml").read_text()
    )
    source = authenticate_sources(spec)
    assert source_authority_errors(spec, source) == []
    forged_root = copy.deepcopy(source)
    forged_root["raw_records_only_sha256"] = "0" * 64
    assert source_authority_errors(spec, forged_root)
    forged_card = copy.deepcopy(source)
    path = spec["source_authorities"]["pr152_release_card"]["path"]
    forged_card["small_authority_hashes"][path] = "0" * 64
    assert source_authority_errors(spec, forged_card)


def test_resource_receipt_is_derived_from_primitives_and_lock_is_exclusive(
    tmp_path: Path,
) -> None:
    deep = _json(DEEP_REPLAY)
    receipt = deep["resource_receipts"][-1]
    assert resource_receipt_errors(receipt) == []
    forged = copy.deepcopy(receipt)
    forged["free_gib"] = 299.0
    forged["free_gib_at_least_300"] = False
    forged["eligible"] = True
    assert resource_receipt_errors(forged)

    with extraction_lock(tmp_path):
        with pytest.raises(
            ActInbandModulationError,
            match="another PR-177 raw extractor holds the lock",
        ):
            with extraction_lock(tmp_path):
                pass


def test_real_result_has_complete_delete_lineage_and_typed_terminal() -> None:
    result = _json(RESULT)
    mc = _json(MC)
    assert result["scientific_result"] in (CANDIDATE, NO_RESOLVED, UNRESOLVED)
    assert result["scientific_status"] == "CLOSED"
    assert result["release_simulation_count"] == 400
    assert result["lineage_status"] == "CERTIFIED_FOR_PR177_RANK_FUNCTIONAL"
    assert mc["replicate_lineage"]["replicate_count"] == 400
    assert len(mc["delete_replicates"]) == 400
    assert mc["iid_binomial_interval_used"] is False
    assert mc["gaussian_sigma_emitted"] is False
    assert all(
        certificate["interpretation"] == "numerical_resolution_only"
        for certificate in mc["certificates"].values()
    )


def test_every_result_bearing_artifact_has_exact_strict_support() -> None:
    payloads = {
        "result": _json(RESULT),
        "mask": _json(REPO / "docs/generated/pr177_mask_control.json"),
        "mc": _json(MC),
        "card": _json(REPO / "docs/generated/pr177_result_card.json"),
        "manifest": _json(MANIFEST),
    }
    assert result_support_errors(payloads, EXPECTED_SUPPORT) == []
    assert all(payload["analysis_support"] == EXPECTED_SUPPORT for payload in payloads.values())


def test_deep_replay_pins_all_raw_features_without_raw_rehash() -> None:
    receipt = _json(DEEP_REPLAY)
    assert receipt["process_execution_status"] == "PASS_AUTHORITATIVE_401_UNIT_FEATURE_REPLAY"
    assert receipt["feature_units_replayed"] == 401
    assert receipt["raw_units_opened"] == 401
    assert receipt["raw_payloads_hashed"] == 0
    assert receipt["features_match_raw_authority"] is True
    assert receipt["analysis_support"] == EXPECTED_SUPPORT
    assert receipt["scientific_result"] is None


def test_deep_replay_failure_completeness_and_nested_digest_are_fail_closed() -> None:
    import yaml
    from obsstat.act_inband_modulation import semantic_digest

    card = _json(FEATURE)
    receipt = _json(DEEP_REPLAY)
    spec = yaml.safe_load(
        (REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml").read_text()
    )
    mutations = (
        lambda value: value.update({"process_execution_status": "FAIL"}),
        lambda value: value.update({"raw_payload_stat_checks": 0}),
        lambda value: value["resource_receipts"][0].pop("semantic_digest", None),
        lambda value: value["input_hashes"].update(
            {"docs/generated/act_raw_qe_card.json": "0" * 64}
        ),
    )
    for mutate in mutations:
        forged = copy.deepcopy(receipt)
        mutate(forged)
        forged["semantic_digest"] = semantic_digest(forged)
        assert validate_feature_card(
            card,
            spec,
            deep_replay_receipt=forged,
        )


def test_mutations_manifest_and_runner_check_close_reproducibility() -> None:
    mutation = _json(MUTATION)
    manifest = _json(MANIFEST)
    assert mutation["registered_count"] == 30
    assert mutation["executed_count"] == 30
    assert mutation["killed_count"] == 30
    assert mutation["survivors"] == []
    mutation_ids = {row["mutation_id"] for row in mutation["mutations"]}
    assert "coordinated_card_and_cache_feature_reseal" in mutation_ids
    assert "low_disk_resealed_resource" in mutation_ids
    assert "stale_log_resealed_resource" in mutation_ids
    assert "drop_manifest_analysis_support" in mutation_ids
    assert "change_frozen_source_raw_root" in mutation_ids
    assert "deep_replay_failed_process_status" in mutation_ids
    assert "deep_replay_zero_raw_stat_checks" in mutation_ids
    assert "deep_replay_missing_resource_digest" in mutation_ids
    assert "change_feature_pr152_input_hash" in mutation_ids
    assert "deep_replay_changed_pr152_input_hash" in mutation_ids
    generating_command = _json(RESULT)["generating_command"]
    assert "OMP_NUM_THREADS=1" in generating_command
    assert "OPENBLAS_NUM_THREADS=1" in generating_command
    assert "MKL_NUM_THREADS=1" in generating_command
    assert manifest["raw_payload_rehashed_by_runner"] is False
    assert manifest["raw_qe_reproduced"] is False
    assert manifest["public_use"] is False
    completed = subprocess.run(
        shlex.split(generating_command.replace("--write", "--check")),
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
        env={
            "PATH": os.environ.get("PATH", ""),
            "PYTHONHASHSEED": "0",
        },
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["ok"] is True
    assert receipt["delete_replicates"] == 400
    assert receipt["mutation_survivors"] == []
