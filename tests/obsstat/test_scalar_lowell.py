from __future__ import annotations

import math

import pytest

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    SkySupport,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="obsstat.test.scalar_lowell",
        artifact_path="memory://obsstat/scalar-lowell",
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.scalar_lowell.v1",
        caveats=["diagnostic feature extraction only"],
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="none",
        sky_support_hash="sha256:sky",
        mask_hash="sha256:mask",
        mock_coverage_status="not_statistical",
        coordinate_frame="galactic",
        sky_fraction=1.0,
        completeness_status="full_sky_synthetic",
        pixelization="none",
    )


def _scalar_null_payload() -> dict[str, object]:
    from htt.obsstat.null_ensembles import (
        LookElsewhereBookkeeping,
        NullEnsembleSpec,
        build_null_ensemble_feature_payload,
    )

    spec = NullEnsembleSpec(
        null_ensemble_ref="mock://lowell",
        null_family="flrw_mask_noise",
        mock_count=128,
        feature_targets=("scalar_lowell",),
        statistic_keys=("s_one_half",),
        sky_support_status="full_sky_synthetic",
        mask_status="full_sky_synthetic",
        noise_model_status="noise_not_injected_synthetic",
        covariance_status="diagonal_mock_covariance",
        null_mock_status="mock_bank_available",
        random_seed_policy="fixed_seed_manifest:lowell",
        config_hash="sha256:null-config",
        input_hashes=("sha256:null-input",),
        generating_command="python -m pytest tests/obsstat/test_scalar_lowell.py -q",
        worktree_state="test-clean",
    )
    look_elsewhere = LookElsewhereBookkeeping(
        look_elsewhere_status="tracked_not_corrected",
        trial_count=1,
        scan_volume={
            "feature_targets": ["scalar_lowell"],
            "statistic_keys": ["s_one_half"],
            "trial_count": 1,
            "global_local_status": "tracked_not_corrected",
        },
        correction_method="not_corrected_single_feature",
        pre_registration_status="pre_registered",
        tail_definitions={"s_one_half": "lower_tail"},
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=spec,
        look_elsewhere=look_elsewhere,
        p_values={"s_one_half": 0.2},
    )


def _flatten_keys(value: object, prefix: str = "") -> tuple[str, ...]:
    if not isinstance(value, dict):
        return ()
    keys: list[str] = []
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        keys.append(path)
        keys.extend(_flatten_keys(item, path))
    return tuple(keys)


def _dense_l2(values: dict[int, complex | float]) -> dict[tuple[int, int], complex | float]:
    return {(2, m): values.get(m, 0.0) for m in range(-2, 3)}


def test_s_one_half_uses_explicit_legendre_definition() -> None:
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    summary = summarize_lowell_scalars({2: 1.0}, ell_min=2, ell_max=2)
    # C(theta) = 5/(4*pi) P_2(x); S_1/2 integrates C(theta)^2 for x in [-1, 1/2].
    antiderivative = lambda x: 9.0 * x**5 / 20.0 - x**3 / 2.0 + x / 4.0
    integral_p2_squared = antiderivative(0.5) - antiderivative(-1.0)
    expected = (5.0 / (4.0 * math.pi)) ** 2 * integral_p2_squared

    assert summary.cl_by_ell == {2: 1.0}
    assert summary.s_one_half == pytest.approx(expected)
    assert (
        summary.definitions["s_one_half"]
        == "integral_-1_to_1/2 [sum_l (2l+1) C_l P_l(x)/(4pi)]^2 dx"
    )


def test_parity_summary_uses_weighted_even_odd_power() -> None:
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    summary = summarize_lowell_scalars(
        {2: 2.0, 3: 1.0, 4: 0.5},
        ell_min=2,
        ell_max=4,
    )
    even = (2 * 3 * 2.0 + 4 * 5 * 0.5) / (2.0 * math.pi)
    odd = (3 * 4 * 1.0) / (2.0 * math.pi)

    assert summary.parity["even_power"] == pytest.approx(even)
    assert summary.parity["odd_power"] == pytest.approx(odd)
    assert summary.parity["even_over_odd_ratio"] == pytest.approx(even / odd)
    assert summary.parity["asymmetry"] == pytest.approx((even - odd) / (even + odd))


def test_planarity_summary_uses_m_squared_power_fraction() -> None:
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    summary = summarize_lowell_scalars(
        ell_min=2,
        ell_max=2,
        alm_by_lm=_dense_l2({-2: 1.0, 2: 1.0}),
    )
    axial = summarize_lowell_scalars(
        ell_min=2,
        ell_max=2,
        alm_by_lm=_dense_l2({0: 1.0}),
    )

    assert summary.planarity["status"] == "computed_from_alm"
    assert summary.planarity["by_ell"][2] == pytest.approx(1.0)
    assert axial.planarity["by_ell"][2] == pytest.approx(0.0)


def test_compute_cl_from_dense_full_alm_and_rejects_ambiguous_storage() -> None:
    from htt.obsstat.scalar_lowell import (
        compute_cl_from_alm,
        summarize_lowell_scalars,
    )

    alm = _dense_l2({-2: 1.0, 0: 2.0, 2: 3.0})
    expected_cl2 = (1.0 + 4.0 + 9.0) / 5.0

    assert compute_cl_from_alm(alm)[2] == pytest.approx(expected_cl2)
    summary = summarize_lowell_scalars(alm_by_lm=alm, ell_min=2, ell_max=2)
    assert summary.cl_by_ell[2] == pytest.approx(expected_cl2)
    assert summary.definitions["cl_source"] == "computed_from_dense_full_alm"
    assert "dense_full" in summary.definitions["alm_storage"]

    with pytest.raises(ValueError, match="dense_full"):
        compute_cl_from_alm({(2, 0): 1.0})
    with pytest.raises(ValueError, match="finite"):
        compute_cl_from_alm(_dense_l2({0: float("nan")}))
    with pytest.raises(ValueError, match="invalid ell/m"):
        compute_cl_from_alm({(2, 3): 1.0})


def test_mixed_cl_and_alm_sources_must_be_consistent() -> None:
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    alm = _dense_l2({-2: 1.0, 2: 1.0})

    with pytest.raises(ValueError, match="inconsistent"):
        summarize_lowell_scalars(
            {2: 2.0},
            ell_min=2,
            ell_max=2,
            alm_by_lm=alm,
        )

    summary = summarize_lowell_scalars(
        {2: 0.4},
        ell_min=2,
        ell_max=2,
        alm_by_lm=alm,
    )
    assert (
        summary.definitions["cl_source"]
        == "provided_cl_checked_against_dense_full_alm_overlap"
    )


def test_monopole_planarity_uses_null_policy_instead_of_dividing_by_zero() -> None:
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    summary = summarize_lowell_scalars(
        alm_by_lm={(0, 0): 1.0},
        ell_min=0,
        ell_max=0,
    )

    assert summary.planarity["by_ell"][0] is None
    assert summary.planarity["mean"] is None
    assert (
        summary.planarity["degeneracy_policy"]
        == "null_when_ell_less_than_one_or_power_zero"
    )


def test_feature_payload_is_not_evidence_or_geometry_claim() -> None:
    from htt.obsstat.observable_vector import build_observable_vector
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    summary = summarize_lowell_scalars({2: 1.0, 3: 0.5}, ell_min=2, ell_max=3)
    payload = summary.to_feature_payload()

    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["statistic_role"] == "feature_only"
    assert payload["model_role"] == "not_model_input"
    assert payload["claim_status"]["geometry_status"] == "blocked_pre_native_atlas"
    assert payload["claim_status"]["family_status"] == "blocked_pre_native_atlas"
    assert payload["transfer_source"] == "none"
    assert payload["parity"]["weights_by_ell"]["2"] == pytest.approx(
        summary.parity["weights_by_ell"][2]
    )
    assert payload["planarity"]["by_ell"] == {}
    lower_keys = [key.lower() for key in _flatten_keys(payload)]
    assert not any("evidence" in key or "posterior" in key for key in lower_keys)
    assert not any("certificate" in key or "truth" in key for key in lower_keys)

    vector = build_observable_vector(
        ell_max=3,
        channels=("TT",),
        scalar_features={"lowell_scalar": payload},
        sky_support=_sky_support(),
        manifest=_manifest(),
    )
    assert (
        vector.alm_features["scalar_features"]["lowell_scalar"]["statistic_role"]
        == "feature_only"
    )


def test_null_calibrated_payload_requires_null_metadata_without_becoming_evidence() -> None:
    from htt.obsstat.observable_vector import build_observable_vector
    from htt.obsstat.scalar_lowell import (
        LowEllNullCalibration,
        summarize_lowell_scalars,
    )

    with pytest.raises(ValueError, match="p_values"):
        LowEllNullCalibration(
            null_ensemble_ref="mock://lowell",
            look_elsewhere_status="tracked",
            p_values={"s_one_half": 1.2},
            tail_definitions={"s_one_half": "lower_tail"},
            mock_count=128,
            covariance_status="diagonal_mock_covariance",
            mask_status="full_sky_synthetic",
            scan_volume={"statistics": ["s_one_half"]},
        )
    with pytest.raises(ValueError, match="tail_definitions"):
        LowEllNullCalibration(
            null_ensemble_ref="mock://lowell",
            look_elsewhere_status="tracked",
            p_values={"s_one_half": 0.2},
            mock_count=128,
            covariance_status="diagonal_mock_covariance",
            mask_status="full_sky_synthetic",
            scan_volume={"statistics": ["s_one_half"]},
        )
    with pytest.raises(ValueError, match="known low-ell"):
        LowEllNullCalibration(
            null_ensemble_ref="mock://lowell",
            look_elsewhere_status="tracked",
            p_values={"posterior_score": 0.2},
            tail_definitions={"posterior_score": "lower_tail"},
            mock_count=128,
            covariance_status="diagonal_mock_covariance",
            mask_status="full_sky_synthetic",
            scan_volume={"statistics": ["posterior_score"]},
        )

    calibration = LowEllNullCalibration(
        null_ensemble_ref="mock://lowell",
        look_elsewhere_status="tracked",
        p_values={"s_one_half": 0.2},
        mock_count=128,
        tail_definitions={"s_one_half": "lower_tail"},
        covariance_status="diagonal_mock_covariance",
        mask_status="full_sky_synthetic",
        scan_volume={"statistics": ["s_one_half"], "ell_range": [2, 3]},
    )
    summary = summarize_lowell_scalars(
        {2: 1.0, 3: 0.5},
        ell_min=2,
        ell_max=3,
        null_calibration=calibration,
    )
    payload = summary.to_feature_payload()

    assert payload["statistic_role"] == "null_calibrated_feature"
    assert payload["model_role"] == "not_model_input"
    assert payload["null_calibration"]["null_ensemble_ref"] == "mock://lowell"
    assert payload["null_calibration"]["p_values"]["s_one_half"] == 0.2
    assert payload["null_calibration"]["tail_definitions"]["s_one_half"] == "lower_tail"
    assert payload["null_calibration"]["mock_count"] == 128

    vector = build_observable_vector(
        ell_max=3,
        channels=("TT",),
        scalar_features={"lowell_scalar": payload},
        null_features=_scalar_null_payload(),
        sky_support=_sky_support(),
        manifest=_manifest(),
    )
    assert vector.alm_features["scalar_features"]["lowell_scalar"][
        "statistic_role"
    ] == "null_calibrated_feature"


def test_scalar_lowell_exports_are_feature_only() -> None:
    from htt.obsstat import (
        LowEllNullCalibration,
        LowEllScalarSummary,
        summarize_lowell_scalars,
    )
    from htt.obsstat.scalar_lowell import LowEllScalarSummary as ModuleSummary

    summary = summarize_lowell_scalars({2: 1.0}, ell_min=2, ell_max=2)
    assert isinstance(summary, LowEllScalarSummary)
    assert LowEllScalarSummary is ModuleSummary
    assert LowEllNullCalibration.__name__ == "LowEllNullCalibration"


def test_scalar_lowell_rejects_geometry_claim_metadata() -> None:
    from htt.obsstat.observable_vector import build_observable_vector
    from htt.obsstat.scalar_lowell import summarize_lowell_scalars

    payload = summarize_lowell_scalars({2: 1.0}, ell_min=2, ell_max=2).to_feature_payload()
    payload["geometry_detected"] = "forbidden"
    with pytest.raises(ValueError, match="family identification"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            scalar_features={"lowell_scalar": payload},
            sky_support=_sky_support(),
            manifest=_manifest(),
        )


def test_public_summary_constructor_rejects_invalid_payload_values() -> None:
    from htt.obsstat.scalar_lowell import LowEllScalarSummary

    with pytest.raises(ValueError, match="finite and non-negative"):
        LowEllScalarSummary(
            cl_by_ell={2: float("nan")},
            ell_min=2,
            ell_max=2,
            s_one_half=1.0,
            parity={},
            planarity={},
            definitions={},
        )
    with pytest.raises(ValueError, match="selected ell range"):
        LowEllScalarSummary(
            cl_by_ell={3: 1.0},
            ell_min=2,
            ell_max=3,
            s_one_half=1.0,
            parity={},
            planarity={},
            definitions={},
        )
    with pytest.raises(ValueError, match="forbidden claim language"):
        LowEllScalarSummary(
            cl_by_ell={2: 1.0},
            ell_min=2,
            ell_max=2,
            s_one_half=1.0,
            parity={},
            planarity={},
            definitions={},
            channel="geometry detected",
        )
