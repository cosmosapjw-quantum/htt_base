from __future__ import annotations

from dataclasses import replace

import pytest

from obsstat.null_ensembles import (
    LookElsewhereBookkeeping,
    NullEnsembleSpec,
    build_null_ensemble_feature_payload,
)
from obsstat.template_fit import OrientationScanMetadata


_CONFIG_HASH = "sha256:" + "a" * 64
_INPUT_HASHES = ("sha256:" + "b" * 64,)
_COMMAND = "python -m pytest tests/htt/test_mes_information_gain.py -q"
_WORKTREE = "test-worktree"


def _orientation_scan() -> OrientationScanMetadata:
    return OrientationScanMetadata(
        scan_id="scan.information_gain.template",
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


def _template_null_payload(
    *,
    config_hash: str = _CONFIG_HASH,
    input_hashes: tuple[str, ...] = _INPUT_HASHES,
) -> dict[str, object]:
    null_ensemble = NullEnsembleSpec(
        null_ensemble_ref="mock://mes-information-template-null",
        null_family="injected_template",
        mock_count=128,
        feature_targets=("mes_template_bound",),
        statistic_keys=("template_delta_chi2",),
        sky_support_status="mock_calibrated",
        mask_status="mask_hash_recorded",
        noise_model_status="synthetic_noise_fixed",
        covariance_status="full_positive_definite_covariance_supplied",
        null_mock_status="synthetic_nulls_available",
        random_seed_policy="fixed_seed_manifest:mes_information_template",
        config_hash=config_hash,
        input_hashes=input_hashes,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    look_elsewhere = LookElsewhereBookkeeping(
        look_elsewhere_status="global_corrected",
        trial_count=4,
        scan_volume={
            "feature_targets": ["mes_template_bound"],
            "statistic_keys": ["template_delta_chi2"],
            "trial_count": 4,
            "global_local_status": "global_corrected",
        },
        correction_method="synthetic_max_scan",
        pre_registration_status="pre_registered_synthetic_fixture",
        tail_definitions={"template_delta_chi2": "upper_tail"},
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=null_ensemble,
        look_elsewhere=look_elsewhere,
        p_values={"template_delta_chi2": 0.25},
        observed_feature_ref="memory://obsstat/template-fit",
    )


def _template_result(
    *,
    diagonal_bound: float = 4.0,
    template: tuple[float, ...] = (1.0, 0.0),
    null_payload: dict[str, object] | None | str = "default",
    dynamical_bound: float | None = None,
):
    from htt.statistics.mes_template_bound import build_mes_template_bound

    payload = _template_null_payload() if null_payload == "default" else null_payload
    return build_mes_template_bound(
        observed=(2.0, 0.25),
        template=template,
        full_covariance=((1.0, 0.0), (0.0, 1.0)),
        diagonal_bound=diagonal_bound,
        rho_synthetic=1.0,
        parameter_block="sigma_template",
        orientation_scan=_orientation_scan(),
        null_feature_payload=payload,
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        dynamical_bound=dynamical_bound,
    )


def _cov_null_payload(
    *,
    observed_feature_ref: str,
    config_hash: str = _CONFIG_HASH,
    input_hashes: tuple[str, ...] = _INPUT_HASHES,
) -> dict[str, object]:
    null_ensemble = NullEnsembleSpec(
        null_ensemble_ref="mock://mes-information-cov-null",
        null_family="flrw_mask_noise",
        mock_count=256,
        feature_targets=("mes_covariance_bound",),
        statistic_keys=("covariance_response_svd",),
        sky_support_status="mock_calibrated",
        mask_status="mask_hash_recorded",
        noise_model_status="synthetic_noise_fixed",
        covariance_status="full_positive_definite_covariance_supplied",
        null_mock_status="synthetic_nulls_available",
        random_seed_policy="fixed_seed_manifest:mes_information_cov",
        config_hash=config_hash,
        input_hashes=input_hashes,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    look_elsewhere = LookElsewhereBookkeeping(
        look_elsewhere_status="global_corrected",
        trial_count=6,
        scan_volume={
            "feature_targets": ["mes_covariance_bound"],
            "statistic_keys": ["covariance_response_svd"],
            "trial_count": 6,
            "global_local_status": "global_corrected",
        },
        correction_method="synthetic_max_scan",
        pre_registration_status="pre_registered_synthetic_fixture",
        tail_definitions={"covariance_response_svd": "max_scan_tail"},
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=null_ensemble,
        look_elsewhere=look_elsewhere,
        p_values={"covariance_response_svd": 0.2},
        observed_feature_ref=observed_feature_ref,
    )


def _biposh_feature_payload() -> dict[str, object]:
    from htt.obsstat.alm_conventions import canonical_temperature_alm_convention
    from htt.obsstat.biposh_features import (
        BiPoSHConventionMetadata,
        SparseBiPoSHCoefficient,
        build_biposh_feature_payload,
    )

    convention = BiPoSHConventionMetadata(
        alm_convention=canonical_temperature_alm_convention(lmax=4),
        rotation_metadata={
            "rotation_group": "SO3",
            "component_index": "M",
            "norm_invariant_under": "unitary_M_basis_rotation",
        },
    )
    return build_biposh_feature_payload(
        entries=(
            SparseBiPoSHCoefficient(
                channel_pair=("T", "T"),
                ell1=2,
                ell2=2,
                L=2,
                M=0,
                value=1.0,
            ),
            SparseBiPoSHCoefficient(
                channel_pair=("T", "E"),
                ell1=2,
                ell2=3,
                L=2,
                M=1,
                value=2.0,
            ),
        ),
        convention=convention,
        sky_support_status="mock_calibrated",
        mask_status="mask_hash_recorded",
        beam_status="beam_not_applied_synthetic",
        systematic_status="systematics_not_injected_synthetic",
        covariance_status="full_positive_definite_covariance_supplied",
        null_mock_status="synthetic_nulls_available",
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )


def _covariance_result(
    *,
    diagonal_bound: float = 4.0,
    response_vectors: tuple[tuple[float, ...], ...] = (
        (4.0, 0.0, 0.0),
        (0.0, 4.0, 0.0),
    ),
    dynamical_bound: float | None = None,
):
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    biposh_feature = _biposh_feature_payload()
    return build_mes_covariance_bound(
        response_vectors=response_vectors,
        observable_labels=("biposh_L1M0", "biposh_L2M1", "mask_control"),
        response_labels=("sigma_covariance", "omega_covariance"),
        full_covariance=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        diagonal_bound=diagonal_bound,
        rho_synthetic=1.0,
        parameter_block="covariance_biposh_synthetic",
        biposh_feature_payload=biposh_feature,
        null_feature_payload=_cov_null_payload(
            observed_feature_ref=str(biposh_feature["entry_hash"])
        ),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
        sky_support_status="mock_calibrated",
        mask_status="mask_hash_recorded",
        look_elsewhere_trial_count=6,
        dynamical_bound=dynamical_bound,
    )


def test_information_gain_report_composes_branch_separated_valid_bounds():
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    template_result = _template_result()
    covariance_result = _covariance_result(dynamical_bound=0.125)

    result = build_mes_information_gain_report(
        template_result=template_result,
        covariance_result=covariance_result,
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.manifest.owner == "COMMON"
    assert result.manifest.implementation_scope == "common"
    assert result.manifest.claim_tier == "diagnostic_only"
    assert result.transfer_source == "none"
    assert result.best_valid_branch == "cov"
    assert result.morphology_final_bound == pytest.approx(0.25)
    assert result.i_morph == pytest.approx(16.0)
    assert result.improvement_candidate is True
    assert set(payload["branches"]) == {"diag", "template", "cov", "dyn"}
    assert payload["branches"]["diag"]["status"] == "baseline"
    assert payload["branches"]["template"]["morphology_branch"] is True
    assert payload["branches"]["cov"]["information_gain"] == pytest.approx(16.0)
    assert payload["branches"]["dyn"]["morphology_branch"] is False
    assert payload["branches"]["dyn"]["improvement_candidate"] is False
    assert payload["branch_separation"]["template_branch"] == "synthetic_template_mean"
    assert payload["branch_separation"]["cov_branch"] == "synthetic_covariance_biposh"
    assert payload["branch_separation"]["dyn_branch"] == "auxiliary_not_morphology_gain"
    assert payload["claim_status"]["inference_status"] == "not_model_input"
    assert payload["claim_status"]["native_solver_status"] == "not_native_solver_result"
    assert "p_values" not in payload


def test_valid_no_gain_branch_is_not_an_improvement_candidate():
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    result = build_mes_information_gain_report(
        template_result=_template_result(diagonal_bound=2.0, template=(0.5, 0.0)),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.i_morph == pytest.approx(1.0)
    assert result.best_valid_branch == "template"
    assert result.improvement_candidate is False
    assert result.morphology_gain_status == "no_gain"
    assert payload["branches"]["template"]["status"] == "no_gain"
    assert payload["branches"]["template"]["information_gain"] == pytest.approx(1.0)
    assert payload["branches"]["template"]["improvement_candidate"] is False


def test_blocked_branch_fallbacks_do_not_create_information_gain():
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    template_result = _template_result(null_payload=None)
    covariance_result = _covariance_result(
        response_vectors=((1.0, 0.0, 0.0), (2.0, 0.0, 0.0))
    )

    result = build_mes_information_gain_report(
        template_result=template_result,
        covariance_result=covariance_result,
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.i_morph is None
    assert result.best_valid_branch is None
    assert result.improvement_candidate is False
    assert result.manifest.claim_tier == "blocked"
    assert result.manifest.production_status in {
        "blocked_missing_null_mocks",
        "blocked_rank_deficient",
    }
    assert payload["branches"]["template"]["status"] == "no_claim"
    assert payload["branches"]["cov"]["status"] == "no_claim"
    assert payload["branches"]["template"]["improvement_candidate"] is False
    assert payload["branches"]["cov"]["improvement_candidate"] is False
    assert "no_valid_morphology_branch" in result.no_claim_reasons


def test_provenance_mismatch_blocks_aggregate_gain():
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    result = build_mes_information_gain_report(
        template_result=_template_result(),
        config_hash="sha256:" + "c" * 64,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.i_morph is None
    assert result.manifest.claim_tier == "blocked"
    assert result.manifest.production_status == "blocked_provenance_mismatch"
    assert payload["branches"]["template"]["status"] == "no_claim"
    assert "template_config_hash_mismatch" in result.no_claim_reasons


def test_mixed_branch_provenance_mismatch_blocks_otherwise_valid_cov_gain():
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    template_good = _template_result()
    mismatched_manifest = replace(
        template_good.report.manifest,
        config_hash="sha256:" + "c" * 64,
    )
    template_bad = replace(
        template_good,
        report=replace(template_good.report, manifest=mismatched_manifest),
    )

    result = build_mes_information_gain_report(
        template_result=template_bad,
        covariance_result=_covariance_result(),
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.i_morph is None
    assert result.best_valid_branch is None
    assert result.manifest.claim_tier == "blocked"
    assert result.manifest.production_status == "blocked_provenance_mismatch"
    assert "template_config_hash_mismatch" in result.no_claim_reasons
    assert payload["branches"]["cov"]["status"] == "improvement"
    assert payload["branches"]["cov"]["selected"] is False


def test_source_failed_gates_block_even_when_wrapper_claims_available():
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    good = _template_result()
    manifest = replace(
        good.report.manifest,
        production_status="blocked_missing_null_mocks",
        failed_gates=["typed_null_feature_payload"],
    )
    forged_report = replace(good.report, manifest=manifest)
    forged = replace(good, report=forged_report)

    result = build_mes_information_gain_report(
        template_result=forged,
        config_hash=_CONFIG_HASH,
        input_hashes=_INPUT_HASHES,
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )
    payload = result.as_payload()

    assert result.i_morph is None
    assert result.manifest.claim_tier == "blocked"
    assert result.manifest.production_status == "blocked_missing_null_mocks"
    assert payload["branches"]["template"]["status"] == "no_claim"
    assert "template_failed_gate_typed_null_feature_payload" in result.no_claim_reasons


@pytest.mark.parametrize(
    ("target", "bad_value", "match"),
    [
        ("diagonal_argument", 0.0, "diagonal_bound.*positive finite"),
        ("source_diagonal", -1.0, "source diagonal_bound.*positive finite"),
        ("template_covariance_bound", float("nan"), "template covariance_bound.*positive finite"),
        ("template_final_bound", float("inf"), "template final_bound.*positive finite"),
        ("cov_covariance_bound", 0.0, "cov covariance_bound.*positive finite"),
        ("cov_final_bound", -1.0, "cov final_bound.*positive finite"),
    ],
)
def test_invalid_bounds_are_rejected_not_clamped_or_plotted(
    target: str,
    bad_value: float,
    match: str,
):
    from htt.statistics.mes_information_gain import build_mes_information_gain_report

    template_result = _template_result()
    covariance_result = None
    explicit_diagonal = None
    if target == "diagonal_argument":
        explicit_diagonal = bad_value
    elif target == "source_diagonal":
        template_result = replace(
            template_result,
            report=replace(template_result.report, diagonal_bound=bad_value),
        )
    elif target == "template_covariance_bound":
        template_result = replace(
            template_result,
            report=replace(template_result.report, covariance_bound=bad_value),
        )
    elif target == "template_final_bound":
        template_result = replace(
            template_result,
            report=replace(template_result.report, final_bound=bad_value),
        )
    elif target == "cov_covariance_bound":
        template_result = None
        covariance_result = _covariance_result()
        covariance_result = replace(
            covariance_result,
            report=replace(covariance_result.report, covariance_bound=bad_value),
        )
    elif target == "cov_final_bound":
        template_result = None
        covariance_result = _covariance_result()
        covariance_result = replace(
            covariance_result,
            report=replace(covariance_result.report, final_bound=bad_value),
        )

    with pytest.raises(ValueError, match=match):
        build_mes_information_gain_report(
            template_result=template_result,
            covariance_result=covariance_result,
            diagonal_bound=explicit_diagonal,
            config_hash=_CONFIG_HASH,
            input_hashes=_INPUT_HASHES,
            generating_command=_COMMAND,
            worktree_state=_WORKTREE,
        )


def test_mes_information_gain_package_exports():
    from htt.statistics import MesInformationGainReport, build_mes_information_gain_report
    from htt.statistics.mes_information_gain import (
        MesInformationGainReport as ModuleReport,
    )

    assert MesInformationGainReport is ModuleReport
    assert callable(build_mes_information_gain_report)
