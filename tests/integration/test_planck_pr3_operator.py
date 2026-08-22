from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import healpy as hp
import numpy as np
import pytest

from obsstat.planck_pr3_operator import (
    COMPONENT_FEATURE_IDS,
    FFP10Inventory,
    GLOBAL_CLAIM_BOUNDARY,
    JOINT_FEATURE_IDS,
    PlanckLaneContractError,
    alm_to_real_vector,
    build_mask_coupling_inverse,
    calibrate_complete_synthetic_pool,
    commonize_beam_pixel_alm,
    covariance_whitened_response_rank,
    estimate_matched_joint_covariance,
    extract_component_features,
    extract_multipole_vectors,
    real_vector_to_alm,
    validate_component_operator_identities,
)
from obsstat.planck_post275_lane import observation_inclusive_max_scan
from obsstat.boost_biposh_residual import (
    DIPOLE_B_DEG,
    DIPOLE_L_DEG,
    ExactBoostOperator,
)


ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "scripts/observed_runs/run_planck_pr3.py"


def _load_worker():
    return importlib.import_module("scripts.observed_runs.run_planck_pr3")


def _profile_cli(
    tmp_path: Path, *, rows: str, mode: str, workers: int
) -> dict[str, object]:
    output = tmp_path / f"profile-{rows}-{mode}.json"
    environment = {
        **os.environ,
        "PYTHONPATH": "htt/src:htt",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    subprocess.run(
        [
            sys.executable,
            "-B",
            str(WORKER),
            "--synthetic-profile",
            "--rows",
            rows,
            "--mode",
            mode,
            "--workers",
            str(workers),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        timeout=60,
    )
    return json.loads(output.read_text(encoding="ascii"))


def _dipole_alm(axis: tuple[float, float, float], *, lmax: int = 5) -> np.ndarray:
    nside = 8
    xyz = np.asarray(hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))).T
    return hp.map2alm(xyz @ np.asarray(axis), lmax=lmax, iter=3)


@pytest.mark.requires_healpy
@pytest.mark.parametrize(
    ("axis", "expected"),
    [
        ((1.0, 0.0, 0.0), np.array([1.0, 0.0, 0.0])),
        ((0.0, 1.0, 0.0), np.array([0.0, 1.0, 0.0])),
        ((0.0, 0.0, 1.0), np.array([0.0, 0.0, 1.0])),
    ],
)
def test_majorana_dipoles_recover_the_three_cartesian_axes(axis, expected) -> None:
    result = extract_multipole_vectors(_dipole_alm(axis), ell=1, lmax=5)
    assert result.shape == (1, 3)
    np.testing.assert_allclose(result[0], expected, atol=2e-7)


@pytest.mark.requires_healpy
@pytest.mark.parametrize("ell", [2, 3])
def test_axisymmetric_multipoles_keep_repeated_projective_zero_infinity_axes(
    ell: int,
) -> None:
    alm = np.zeros(hp.Alm.getsize(5), dtype=np.complex128)
    alm[hp.Alm.getidx(5, ell, 0)] = 1.0
    vectors = extract_multipole_vectors(alm, ell=ell, lmax=5)
    assert vectors.shape == (ell, 3)
    np.testing.assert_allclose(vectors, np.tile([0.0, 0.0, 1.0], (ell, 1)), atol=1e-12)


@pytest.mark.requires_healpy
def test_real_linear_mask_inverse_recovers_sine_and_cosine_modes() -> None:
    nside = 8
    _, _, z = hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))
    mask = (np.abs(z) > 0.2).astype(float)
    mask[(np.abs(z) > 0.2) & (np.abs(z) < 0.35)] = 0.5
    inverse = build_mask_coupling_inverse(mask)
    rng = np.random.default_rng(306)
    original = rng.normal(size=inverse.dimension)
    sky = hp.alm2map(real_vector_to_alm(original), nside=nside, lmax=5)
    pseudo = hp.map2alm(mask * sky, lmax=5, iter=0)
    recovered = inverse.inverse @ alm_to_real_vector(pseudo)
    np.testing.assert_allclose(recovered, original, rtol=1e-11, atol=1e-11)


@pytest.mark.requires_healpy
def test_mask_inverse_abstains_on_empty_or_rank_deficient_support() -> None:
    with pytest.raises(PlanckLaneContractError, match="support"):
        build_mask_coupling_inverse(np.zeros(hp.nside2npix(8)))
    tiny = np.zeros(hp.nside2npix(8))
    tiny[:4] = 1.0
    with pytest.raises(PlanckLaneContractError, match="rank deficient|condition"):
        build_mask_coupling_inverse(tiny)


@pytest.mark.requires_healpy
def test_commonization_is_non_amplifying_and_feature_order_is_exact() -> None:
    rng = np.random.default_rng(5)
    alm = real_vector_to_alm(rng.normal(size=32))
    ell = np.arange(6, dtype=float)
    source = np.exp(-0.001 * ell * (ell + 1.0))
    target = np.exp(-0.002 * ell * (ell + 1.0))
    common = commonize_beam_pixel_alm(
        alm,
        source_beam=source,
        source_pixel_window=np.ones(6),
        target_beam=target,
        target_pixel_window=np.ones(6),
    )
    assert common.shape == alm.shape
    features = extract_component_features(common)
    assert features.shape == (len(COMPONENT_FEATURE_IDS),)
    assert len(JOINT_FEATURE_IDS) == 2 * len(COMPONENT_FEATURE_IDS)
    with pytest.raises(PlanckLaneContractError, match="amplify"):
        commonize_beam_pixel_alm(
            alm,
            source_beam=target,
            source_pixel_window=np.ones(6),
            target_beam=source,
            target_pixel_window=np.ones(6),
        )


def test_same_sky_joint_covariance_preserves_pairing_and_cross_block() -> None:
    rng = np.random.default_rng(8)
    n = 96
    shared = rng.normal(size=(n, len(COMPONENT_FEATURE_IDS)))
    smica = shared + 0.2 * rng.normal(size=shared.shape)
    commander = 0.8 * shared + 0.25 * rng.normal(size=shared.shape)
    ids = tuple(f"row-{index:03d}" for index in range(n))
    result = estimate_matched_joint_covariance(
        smica_row_ids=ids,
        commander_row_ids=ids,
        smica_features=smica,
        commander_features=commander,
    )
    assert result.rank == len(JOINT_FEATURE_IDS)
    assert result.cross_block_norm > 0.0
    with pytest.raises(PlanckLaneContractError, match="not exactly paired"):
        estimate_matched_joint_covariance(
            smica_row_ids=ids,
            commander_row_ids=tuple(reversed(ids)),
            smica_features=smica,
            commander_features=commander,
        )
    with pytest.raises(PlanckLaneContractError, match="more skies"):
        estimate_matched_joint_covariance(
            smica_row_ids=ids[:10],
            commander_row_ids=ids[:10],
            smica_features=smica[:10],
            commander_features=commander[:10],
        )


def test_partial_ffp10_inventory_can_never_calibrate_a_p_value() -> None:
    inventory = FFP10Inventory(tuple(f"row-{index}" for index in range(128)))
    with pytest.raises(PlanckLaneContractError, match="partial FFP10"):
        calibrate_complete_synthetic_pool(
            observation_features=np.ones(2),
            null_features=np.ones((128, 2)),
            inventory=inventory,
        )


@pytest.mark.parametrize("row_count", [5, 6, 17, 18])
def test_leave_one_out_sufficient_statistics_match_bruteforce(row_count: int) -> None:
    rng = np.random.default_rng(row_count)
    rows = rng.normal(size=(row_count, 4))
    optimized = observation_inclusive_max_scan(rows, ("two-sided",) * rows.shape[1])
    scores = np.empty_like(rows)
    for index in range(row_count):
        centers = np.median(np.delete(rows, index, axis=0), axis=0)
        scores[index] = np.abs(rows[index] - centers)
    local = []
    from fractions import Fraction

    for index in range(row_count):
        local.append(
            tuple(
                Fraction(
                    int(np.count_nonzero(scores[:, column] >= scores[index, column])),
                    row_count,
                )
                for column in range(rows.shape[1])
            )
        )
    assert optimized.local_p_all_rows == tuple(local)


def test_whitened_local_response_rank_keeps_global_response_missing() -> None:
    covariance = np.diag([1.0, 4.0, 9.0])
    response = np.array([[1.0, 0.0], [0.0, 2.0], [0.0, 0.0]])
    result = covariance_whitened_response_rank(covariance, response)
    assert result.rank == 2
    assert result.global_response_status == "MISSING"
    assert result.global_claim_boundary == GLOBAL_CLAIM_BOUNDARY


@pytest.mark.requires_healpy
def test_exact_local_boost_has_a_finite_zero_and_positive_dipole_sign() -> None:
    nside = 8
    constant = np.ones(hp.nside2npix(nside))
    zero = ExactBoostOperator(nside=nside, lmax=5, beta=0.0)(constant)
    np.testing.assert_allclose(zero, constant, atol=2e-5)
    boosted = ExactBoostOperator(nside=nside, lmax=5, beta=1e-3)(constant)
    xyz = np.asarray(hp.pix2vec(nside, np.arange(constant.size))).T
    direction = np.asarray(
        hp.rotator.dir2vec(DIPOLE_L_DEG, DIPOLE_B_DEG, lonlat=True), dtype=float
    )
    cosine = xyz @ (direction / np.linalg.norm(direction))
    assert float(np.dot(boosted - boosted.mean(), cosine)) > 0.0


def _identity(component: str) -> dict[str, str]:
    source = component.lower()
    return {
        "map_product_id": f"planck:pr3:{source}:lowell:v1",
        "source_beam_id": f"beam:{source}",
        "source_pixel_window_id": f"pixel:{source}",
        "source_mask_id": f"mask:{source}",
        "source_covariance_id": f"cov:{source}",
        "pipeline_id": "operator:pr306:v1",
        "target_beam_id": "beam:common-target",
        "target_pixel_window_id": "pixel:common-target",
        "common_analysis_mask_id": "mask:intersection",
        "mask_coupling_inverse_id": "inverse:full-rank",
        "harmonic_convention_id": "harmonic:cs-real",
        "feature_order_id": "features:pr306:v1",
        "null_ensemble_id": "ffp10:complete",
        "local_response_id": "response:boost-local",
        "units_id": "units:microK-CMB",
    }


def test_component_inputs_remain_distinct_while_derived_operator_is_shared() -> None:
    rows = {"SMICA": _identity("SMICA"), "Commander": _identity("Commander")}
    assert (
        validate_component_operator_identities(rows, rows)["SMICA"]["source_mask_id"]
        != rows["Commander"]["source_mask_id"]
    )
    collapsed = {key: dict(value) for key, value in rows.items()}
    collapsed["Commander"]["source_mask_id"] = collapsed["SMICA"]["source_mask_id"]
    with pytest.raises(PlanckLaneContractError, match="collapsed"):
        validate_component_operator_identities(collapsed, collapsed)


@pytest.mark.requires_healpy
def test_partial_profile_has_exact_stages_and_no_calibration() -> None:
    worker = _load_worker()
    payload = worker.build_profile(rows="8", mode="serial", workers=1)
    assert tuple(payload["stages"]) == worker.STAGES
    assert payload["synthetic_calibration"] is None
    assert payload["stages"]["covariance"]["status"] == "NOT_RUN_PARTIAL_INVENTORY"
    assert payload["observed_statistic_seen"] is False
    assert payload["observed_science_executed"] is False


@pytest.mark.requires_healpy
def test_serial_thread_and_process_profiles_restore_identical_row_order(
    tmp_path: Path,
) -> None:
    serial = _profile_cli(tmp_path, rows="8", mode="serial", workers=1)
    threaded = _profile_cli(tmp_path, rows="8", mode="thread", workers=2)
    process = _profile_cli(tmp_path, rows="8", mode="process", workers=2)
    assert serial["joint_features_sha256"] == threaded["joint_features_sha256"]
    assert serial["joint_features_sha256"] == process["joint_features_sha256"]
    assert all(value == "1" for value in process["thread_controls"].values())


@pytest.mark.requires_healpy
def test_full_synthetic_profile_computes_covariance_and_rank_but_abstains_global(
    tmp_path: Path,
) -> None:
    payload = _profile_cli(tmp_path, rows="full", mode="serial", workers=1)
    assert payload["row_count"] == 999
    assert payload["covariance"]["rank"] == len(JOINT_FEATURE_IDS)
    assert payload["covariance"]["cross_block_norm"] > 0.0
    assert payload["local_response_rank"] == 1
    assert (
        payload["synthetic_calibration"]["observation_kind"] == "SYNTHETIC_PROFILE_ROW"
    )
    assert payload["global_claim_boundary"] == GLOBAL_CLAIM_BOUNDARY
    assert payload["rust_gate"].startswith("KEEP_PYTHON")
