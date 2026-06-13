from __future__ import annotations

import pytest

from obsstat.null_ensembles import (
    LookElsewhereBookkeeping,
    NullEnsembleSpec,
    build_null_ensemble_feature_payload,
)
from obsstat.template_fit import OrientationScanMetadata


_CONFIG_HASH = "sha256:" + "c" * 64
_INPUT_HASHES = ("sha256:" + "d" * 64,)
_COMMAND = "python -m pytest tests/htt/test_mes_template_bound.py -q"
_WORKTREE = "test-worktree"


def _orientation_scan() -> OrientationScanMetadata:
    return OrientationScanMetadata(
        scan_id="scan.synthetic.template",
        orientation_parameterization="fixed_synthetic_basis",
        orientation_count=4,
        scan_volume={
            "orientation_parameterization": "fixed_synthetic_basis",
            "orientation_count": 4,
            "global_local_status": "global_corrected",
        },
        coordinate_frame="cmb_sky",
        sky_support_status="mock_calibrated",
        mask_status="mask_hash_recorded",
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
    )


def _null_feature_payload(
    *,
    feature_targets: tuple[str, ...] = ("mes_template_bound",),
    statistic_keys: tuple[str, ...] = ("template_delta_chi2",),
    look_elsewhere_status: str = "global_corrected",
    p_value_key: str = "template_delta_chi2",
    config_hash: str = _CONFIG_HASH,
    input_hashes: tuple[str, ...] = _INPUT_HASHES,
    sky_support_status: str = "mock_calibrated",
    mask_status: str = "mask_hash_recorded",
    covariance_status: str = "full_positive_definite_covariance_supplied",
    trial_count: int = 4,
    observed_feature_ref: str = "memory://obsstat/template-fit",
) -> dict[str, object]:
    null_ensemble = NullEnsembleSpec(
        null_ensemble_ref="mock://mes-template-bound-null",
        null_family="injected_template",
        mock_count=128,
        feature_targets=feature_targets,
        statistic_keys=statistic_keys,
        sky_support_status=sky_support_status,
        mask_status=mask_status,
        noise_model_status="synthetic_noise_fixed",
        covariance_status=covariance_status,
        null_mock_status="synthetic_nulls_available",
        random_seed_policy="fixed_seed_manifest:mes_template",
        config_hash=config_hash,
        input_hashes=input_hashes,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    look_elsewhere = LookElsewhereBookkeeping(
        look_elsewhere_status=look_elsewhere_status,
        trial_count=trial_count,
        scan_volume={
            "feature_targets": list(feature_targets),
            "statistic_keys": list(statistic_keys),
            "trial_count": trial_count,
            "global_local_status": look_elsewhere_status,
        },
        correction_method="synthetic_max_scan",
        pre_registration_status="pre_registered_synthetic_fixture",
        tail_definitions={key: "upper_tail" for key in statistic_keys},
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=null_ensemble,
        look_elsewhere=look_elsewhere,
        p_values={p_value_key: 0.25},
        observed_feature_ref=observed_feature_ref,
    )


def test_mes_template_branch_computes_synthetic_bound_with_manifest():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    result = build_mes_template_bound(
        observed=(2.0, 0.25),
        template=(1.0, 0.0),
        full_covariance=((2.0, 0.5), (0.5, 1.0)),
        diagonal_bound=3.0,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=_null_feature_payload(),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.synthetic_bound_available is True
    assert result.report.manifest.owner == "COMMON"
    assert result.report.manifest.implementation_scope == "common"
    assert result.report.manifest.claim_tier == "diagnostic_only"
    assert result.report.response_rank == 1
    assert result.report.covariance_bound == pytest.approx(1.3228756555)
    assert result.report.final_bound == pytest.approx(result.report.covariance_bound)
    assert result.report.information_gain == pytest.approx(
        result.report.diagonal_bound / result.report.final_bound
    )
    assert payload["template_fit"]["template_mean_branch"]["template_norm_weighted"] == (
        pytest.approx(4.0 / 7.0)
    )
    assert payload["branch_separation"]["does_not_replace_diagonal_mes"] is True
    assert payload["branch_separation"]["universal_mes_claim"] is False
    assert payload["transfer_source"] == "none"
    assert "p_values" not in payload
    assert result.null_feature_payload is not None
    assert "p_values" not in result.null_feature_payload


def test_mes_template_branch_missing_null_payload_is_no_claim():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    result = build_mes_template_bound(
        observed=(2.0, 0.25),
        template=(1.0, 0.0),
        full_covariance=((2.0, 0.5), (0.5, 1.0)),
        diagonal_bound=3.0,
        dynamical_bound=0.5,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=None,
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    assert result.synthetic_bound_available is False
    assert result.template_bound is None
    assert result.report.covariance_bound is None
    assert result.report.final_bound == pytest.approx(3.0)
    assert result.as_payload()["template_bound"] is None
    assert result.report.information_gain == pytest.approx(1.0)
    assert result.report.manifest.claim_tier == "blocked"
    assert result.report.manifest.production_status == "blocked_missing_null_mocks"
    assert "missing_null_feature_payload" in result.no_claim_reasons


def test_mes_template_branch_missing_full_covariance_is_no_claim():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    result = build_mes_template_bound(
        observed=(2.0, 0.25),
        template=(1.0, 0.0),
        full_covariance=None,
        diagonal_bound=3.0,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=_null_feature_payload(),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    assert result.synthetic_bound_available is False
    assert result.report.manifest.production_status == "blocked_missing_covariance"
    assert "missing_full_covariance" in result.no_claim_reasons


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (
            _null_feature_payload(feature_targets=("other_template_feature",)),
            "null_feature_target_missing",
        ),
        (
            _null_feature_payload(
                statistic_keys=("other_delta_chi2",),
                p_value_key="other_delta_chi2",
            ),
            "null_statistic_key_missing",
        ),
        (
            _null_feature_payload(look_elsewhere_status="tracked_not_corrected"),
            "null_look_elsewhere_not_global",
        ),
        (
            _null_feature_payload(config_hash="sha256:" + "e" * 64),
            "null_config_hash_mismatch",
        ),
        (
            _null_feature_payload(
                covariance_status="full_covariance_from_other_fixture",
            ),
            "null_covariance_status_mismatch",
        ),
        (
            _null_feature_payload(trial_count=2),
            "null_scan_volume_mismatch",
        ),
    ],
)
def test_mes_template_branch_malformed_typed_null_payload_is_no_claim(
    payload: dict[str, object],
    reason: str,
):
    from htt.statistics.mes_template_bound import build_mes_template_bound

    result = build_mes_template_bound(
        observed=(2.0, 0.25),
        template=(1.0, 0.0),
        full_covariance=((2.0, 0.5), (0.5, 1.0)),
        diagonal_bound=3.0,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=payload,
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    assert result.synthetic_bound_available is False
    assert result.report.covariance_bound is None
    assert result.report.final_bound == pytest.approx(3.0)
    assert result.report.information_gain == pytest.approx(1.0)
    assert result.report.manifest.production_status == "blocked_missing_null_mocks"
    assert reason in result.no_claim_reasons


def test_mes_template_branch_rank_deficiency_is_no_claim_not_error():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    result = build_mes_template_bound(
        observed=(2.0, 0.25),
        template=(0.0, 0.0),
        full_covariance=((2.0, 0.5), (0.5, 1.0)),
        diagonal_bound=3.0,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=_null_feature_payload(),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )

    assert result.synthetic_bound_available is False
    assert result.report.response_rank == 0
    assert result.report.covariance_bound is None
    assert "response_rank_deficient" in result.no_claim_reasons


def test_mes_template_branch_rejects_invalid_covariance_without_diagonal_fallback():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    kwargs = dict(
        observed=(2.0, 0.25),
        template=(1.0, 0.0),
        diagonal_bound=3.0,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=_null_feature_payload(),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    with pytest.raises(ValueError, match="symmetric"):
        build_mes_template_bound(full_covariance=((1.0, 2.0), (0.0, 1.0)), **kwargs)
    with pytest.raises(ValueError, match="positive definite"):
        build_mes_template_bound(full_covariance=((1.0, 2.0), (2.0, 1.0)), **kwargs)
    with pytest.raises(ValueError, match="shape"):
        build_mes_template_bound(full_covariance=((1.0,),), **kwargs)


def test_mes_template_branch_rejects_invalid_vectors_and_positive_bounds():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    kwargs = dict(
        full_covariance=((2.0, 0.5), (0.5, 1.0)),
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=_null_feature_payload(),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    with pytest.raises(ValueError, match="shape"):
        build_mes_template_bound(
            observed=(2.0, 0.25),
            template=(1.0,),
            diagonal_bound=3.0,
            rho_synthetic=1.0,
            **kwargs,
        )
    with pytest.raises(ValueError, match="finite"):
        build_mes_template_bound(
            observed=(float("nan"), 0.25),
            template=(1.0, 0.0),
            diagonal_bound=3.0,
            rho_synthetic=1.0,
            **kwargs,
        )
    with pytest.raises(ValueError, match="positive finite"):
        build_mes_template_bound(
            observed=(2.0, 0.25),
            template=(1.0, 0.0),
            diagonal_bound=0.0,
            rho_synthetic=1.0,
            **kwargs,
        )
    with pytest.raises(ValueError, match="positive finite"):
        build_mes_template_bound(
            observed=(2.0, 0.25),
            template=(1.0, 0.0),
            diagonal_bound=3.0,
            rho_synthetic=0.0,
            **kwargs,
        )


def test_mes_template_branch_rejects_universal_or_family_claim_language():
    from htt.statistics.mes_template_bound import build_mes_template_bound

    with pytest.raises(ValueError, match="forbidden"):
        build_mes_template_bound(
            observed=(2.0, 0.25),
            template=(1.0, 0.0),
            full_covariance=((2.0, 0.5), (0.5, 1.0)),
            diagonal_bound=3.0,
            rho_synthetic=1.0,
            parameter_block="universal " + "MES",
            orientation_scan=_orientation_scan(),
            null_feature_payload=_null_feature_payload(),
            config_hash=_CONFIG_HASH,
            input_hashes=_INPUT_HASHES,
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_mes_template_bound_package_exports():
    from htt.statistics import MesTemplateBoundResult, build_mes_template_bound
    from htt.statistics.mes_template_bound import MesTemplateBoundResult as ModuleResult

    assert MesTemplateBoundResult is ModuleResult
    assert callable(build_mes_template_bound)
