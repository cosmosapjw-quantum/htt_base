from __future__ import annotations

import pytest

from obsstat.null_ensembles import (
    LookElsewhereBookkeeping,
    NullEnsembleSpec,
    build_null_ensemble_feature_payload,
)


_CONFIG_HASH = "sha256:" + "9" * 64
_INPUT_HASHES = ("sha256:" + "8" * 64,)
_COMMAND = "python -m pytest tests/htt/test_mes_cov_bound.py -q"
_WORKTREE = "test-worktree"


def _null_feature_payload(
    *,
    feature_targets: tuple[str, ...] = ("mes_covariance_bound",),
    statistic_keys: tuple[str, ...] = ("covariance_response_svd",),
    look_elsewhere_status: str = "global_corrected",
    p_value_key: str = "covariance_response_svd",
    config_hash: str = _CONFIG_HASH,
    input_hashes: tuple[str, ...] = _INPUT_HASHES,
    sky_support_status: str = "mock_calibrated",
    mask_status: str = "mask_hash_recorded",
    covariance_status: str = "full_positive_definite_covariance_supplied",
    trial_count: int = 6,
    observed_feature_ref: str = "sha256:" + "b" * 64,
) -> dict[str, object]:
    null_ensemble = NullEnsembleSpec(
        null_ensemble_ref="mock://mes-cov-bound-null",
        null_family="flrw_mask_noise",
        mock_count=256,
        feature_targets=feature_targets,
        statistic_keys=statistic_keys,
        sky_support_status=sky_support_status,
        mask_status=mask_status,
        noise_model_status="synthetic_noise_fixed",
        covariance_status=covariance_status,
        null_mock_status="synthetic_nulls_available",
        random_seed_policy="fixed_seed_manifest:mes_covariance",
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
        tail_definitions={key: "max_scan_tail" for key in statistic_keys},
    )
    return build_null_ensemble_feature_payload(
        null_ensemble=null_ensemble,
        look_elsewhere=look_elsewhere,
        p_values={p_value_key: 0.2},
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


def _build_kwargs(**overrides: object) -> dict[str, object]:
    biposh_feature = _biposh_feature_payload()
    values: dict[str, object] = {
        "response_vectors": ((1.0, 0.0, 0.0), (0.0, 2.0, 0.0)),
        "observable_labels": ("biposh_L1M0", "biposh_L2M1", "mask_control"),
        "response_labels": ("sigma_covariance", "omega_covariance"),
        "full_covariance": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "diagonal_bound": 4.0,
        "rho_synthetic": 1.0,
        "parameter_block": "covariance_biposh_synthetic",
        "biposh_feature_payload": biposh_feature,
        "null_feature_payload": _null_feature_payload(
            observed_feature_ref=str(biposh_feature["entry_hash"])
        ),
        "config_hash": _CONFIG_HASH,
        "input_hashes": _INPUT_HASHES,
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
        "sky_support_status": "mock_calibrated",
        "mask_status": "mask_hash_recorded",
        "look_elsewhere_trial_count": 6,
    }
    values.update(overrides)
    return values


def test_mes_covariance_branch_computes_rank_bound_with_nuisance_projection():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(
            nuisance_responses=((0.0, 0.0, 1.0),),
            nuisance_labels=("mask_control_mode",),
        )
    )
    payload = result.as_payload()

    assert result.synthetic_bound_available is True
    assert result.report.manifest.owner == "COMMON"
    assert result.report.manifest.implementation_scope == "common"
    assert result.report.manifest.claim_tier == "diagnostic_only"
    assert result.report.response_rank == 2
    assert result.report.singular_values == pytest.approx([2.0, 1.0])
    assert result.report.nuisance_projection_status == "projected"
    assert result.report.covariance_bound == pytest.approx(1.0)
    assert result.report.final_bound == pytest.approx(1.0)
    assert result.report.information_gain == pytest.approx(4.0)
    assert payload["branch_role"] == "synthetic_covariance_biposh_mes_bound"
    assert payload["branch_separation"]["template_mean_branch"] == "not_evaluated_by_this_module"
    assert payload["branch_separation"]["covariance_branch"] == "synthetic_covariance_biposh_bound"
    assert payload["transfer_source"] == "none"
    assert payload["biposh_feature_ref"]["entry_hash"].startswith("sha256:")
    assert payload["biposh_feature_ref"]["model_role"] == "not_model_input"
    assert payload["null_feature_ref"]["look_elsewhere_status"] == "global_corrected"
    assert "p_values" not in result.null_feature_payload


def test_mes_covariance_branch_rank_deficiency_is_no_claim_not_finite_bound():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(response_vectors=((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)))
    )

    assert result.synthetic_bound_available is False
    assert result.report.response_rank == 1
    assert result.report.covariance_bound is None
    assert result.covariance_bound is None
    assert result.report.final_bound == pytest.approx(4.0)
    assert result.report.information_gain == pytest.approx(1.0)
    assert result.report.manifest.claim_tier == "blocked"
    assert result.report.manifest.production_status == "blocked_rank_deficient"
    assert "response_rank_deficient" in result.no_claim_reasons


def test_mes_covariance_branch_nuisance_projection_can_erase_response_rank():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(
            response_vectors=((1.0, 0.0, 0.0), (0.0, 2.0, 0.0)),
            nuisance_responses=((1.0, 0.0, 0.0),),
            nuisance_labels=("sigma_like_nuisance",),
        )
    )

    assert result.synthetic_bound_available is False
    assert result.report.response_rank == 1
    assert result.report.covariance_bound is None
    assert result.report.manifest.production_status == "blocked_rank_deficient"
    assert result.report.nuisance_projection_status.startswith("no_claim:")
    assert "zero_projected_response" in result.no_claim_reasons
    assert "response_rank_deficient" in result.no_claim_reasons


def test_mes_covariance_branch_near_singular_response_is_no_claim():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(response_vectors=((1.0, 0.0, 0.0), (0.0, 1.0e-14, 0.0)))
    )

    assert result.synthetic_bound_available is False
    assert result.report.response_rank == 1
    assert result.report.covariance_bound is None
    assert result.report.manifest.production_status == "blocked_rank_deficient"
    assert result.report.singular_values[1] == pytest.approx(1.0e-14)
    assert "response_rank_deficient" in result.no_claim_reasons


def test_mes_covariance_branch_non_diagonal_covariance_changes_singular_values():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(
            response_vectors=((1.0, 0.0), (0.0, 1.0)),
            observable_labels=("biposh_L1M0", "biposh_L2M1"),
            full_covariance=((4.0, 1.0), (1.0, 1.0)),
            nuisance_responses=(),
            nuisance_labels=(),
        )
    )

    assert result.synthetic_bound_available is True
    assert result.report.response_rank == 2
    assert result.report.singular_values == pytest.approx([1.197605, 0.482087], rel=1e-6)
    assert result.report.covariance_bound == pytest.approx(1.0 / 0.482087, rel=1e-6)


def test_mes_covariance_branch_null_payload_must_match_biposh_feature_ref():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(
            null_feature_payload=_null_feature_payload(
                observed_feature_ref="sha256:" + "e" * 64
            )
        )
    )

    assert result.synthetic_bound_available is False
    assert result.report.covariance_bound is None
    assert result.report.manifest.production_status == "blocked_missing_null_mocks"
    assert "null_observed_feature_ref_mismatch" in result.no_claim_reasons


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("owner", "HTT", "biposh_owner_mismatch"),
        ("implementation_scope", "htt", "biposh_scope_mismatch"),
        ("claim_tier", "blocked", "biposh_claim_tier_mismatch"),
        ("model_role", "model_input", "biposh_model_role_mismatch"),
        ("transfer_source", "external_transfer", "biposh_transfer_source_not_none"),
        ("config_hash", "sha256:" + "6" * 64, "biposh_config_hash_mismatch"),
        ("input_hashes", ["sha256:" + "5" * 64], "biposh_input_hashes_mismatch"),
        ("sky_support_status", "other_sky", "biposh_sky_support_mismatch"),
        ("mask_status", "other_mask", "biposh_mask_status_mismatch"),
        ("covariance_status", "other_covariance", "biposh_covariance_status_mismatch"),
        ("null_mock_status", "other_nulls", "biposh_null_mock_status_mismatch"),
    ],
)
def test_mes_covariance_branch_biposh_payload_mismatch_is_no_claim(
    field: str,
    value: object,
    reason: str,
):
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    payload = dict(_biposh_feature_payload())
    payload[field] = value

    result = build_mes_covariance_bound(
        **_build_kwargs(biposh_feature_payload=payload)
    )

    assert result.synthetic_bound_available is False
    assert result.report.covariance_bound is None
    assert result.report.manifest.production_status == "blocked_provenance_mismatch"
    assert reason in result.no_claim_reasons


def test_mes_covariance_branch_missing_full_covariance_is_no_claim():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(**_build_kwargs(full_covariance=None))

    assert result.synthetic_bound_available is False
    assert result.report.manifest.production_status == "blocked_missing_covariance"
    assert result.report.covariance_bound is None
    assert "missing_full_covariance" in result.no_claim_reasons


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (
            _null_feature_payload(feature_targets=("other_covariance_feature",)),
            "null_feature_target_missing",
        ),
        (
            _null_feature_payload(
                statistic_keys=("other_response_statistic",),
                p_value_key="other_response_statistic",
            ),
            "null_statistic_key_missing",
        ),
        (
            _null_feature_payload(look_elsewhere_status="tracked_not_corrected"),
            "null_look_elsewhere_not_global",
        ),
        (
            _null_feature_payload(config_hash="sha256:" + "7" * 64),
            "null_config_hash_mismatch",
        ),
        (
            _null_feature_payload(covariance_status="other_covariance_status"),
            "null_covariance_status_mismatch",
        ),
        (
            _null_feature_payload(trial_count=3),
            "null_scan_volume_mismatch",
        ),
    ],
)
def test_mes_covariance_branch_malformed_typed_null_payload_is_no_claim(
    payload: dict[str, object],
    reason: str,
):
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    result = build_mes_covariance_bound(
        **_build_kwargs(null_feature_payload=payload)
    )

    assert result.synthetic_bound_available is False
    assert result.report.covariance_bound is None
    assert result.report.final_bound == pytest.approx(4.0)
    assert result.report.information_gain == pytest.approx(1.0)
    assert result.report.manifest.production_status == "blocked_missing_null_mocks"
    assert reason in result.no_claim_reasons


def test_mes_covariance_branch_rejects_invalid_covariance_and_shapes():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    with pytest.raises(ValueError, match="symmetric"):
        build_mes_covariance_bound(
            **_build_kwargs(
                full_covariance=(
                    (1.0, 2.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (0.0, 0.0, 1.0),
                )
            )
        )
    with pytest.raises(ValueError, match="positive definite"):
        build_mes_covariance_bound(
            **_build_kwargs(
                full_covariance=(
                    (1.0, 2.0, 0.0),
                    (2.0, 1.0, 0.0),
                    (0.0, 0.0, 1.0),
                )
            )
        )
    with pytest.raises(ValueError, match="same length"):
        build_mes_covariance_bound(
            **_build_kwargs(response_vectors=((1.0, 0.0), (0.0, 1.0, 0.0)))
        )
    with pytest.raises(ValueError, match="observable_labels"):
        build_mes_covariance_bound(
            **_build_kwargs(observable_labels=("only_one_label",))
        )
    with pytest.raises(ValueError, match="nuisance_labels"):
        build_mes_covariance_bound(
            **_build_kwargs(nuisance_responses=((0.0, 0.0, 1.0),))
        )


def test_mes_covariance_branch_rejects_inference_or_family_claim_language():
    from htt.statistics.mes_cov_bound import build_mes_covariance_bound

    with pytest.raises(ValueError, match="forbidden"):
        build_mes_covariance_bound(
            **_build_kwargs(parameter_block="family " + "identification")
        )


def test_mes_covariance_bound_package_exports():
    from htt.statistics import MesCovarianceBoundResult, build_mes_covariance_bound
    from htt.statistics.mes_cov_bound import MesCovarianceBoundResult as ModuleResult

    assert MesCovarianceBoundResult is ModuleResult
    assert callable(build_mes_covariance_bound)
