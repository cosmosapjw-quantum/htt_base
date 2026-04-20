"""
htt/tests/test_wbs04_artifacts.py — HTT/common closure regressions
===================================================================
Adversarial tests for the WBS-04 closure tranche:
  - identifiability audit artifact export
  - survey nuisance artifact export
  - directional likelihood must penalise misalignment
  - shared-cause auto-fit must follow input data, not hardcoded defaults
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest


def _load_obs() -> dict:
    path = (
        Path(__file__).resolve().parent.parent.parent
        / 'workspace'
        / 'data'
        / 'obs_defaults.json'
    )
    if not path.exists():
        pytest.skip("obs_defaults.json not found")
    return json.loads(path.read_text())


def test_model_identifiability_artifact_is_json_ready():
    from htt.core.evidence_models_R03a import model_identifiability_audit_artifact

    artifact = model_identifiability_audit_artifact(metadata={'git_commit': 'test'})

    assert artifact['artifact_name'] == 'model_identifiability_audit_v1.json'
    assert artifact['production_allowed'] is False
    assert artifact['n_models'] == len(artifact['model_audit'])
    assert artifact['n_duplicate_models'] == len(artifact['duplicate_models'])
    assert artifact['config_hash'] != ''
    json.dumps(artifact)


def test_survey_nuisance_artifact_is_json_ready():
    from htt.infer.survey_nuisance import survey_nuisance_report_artifact

    artifact = survey_nuisance_report_artifact(
        {'CF4': 1.334e-3, 'CW': 1.60e-3, 'Radio': 1.50e-3},
        metadata={'git_commit': 'test'},
    )

    assert artifact['artifact_name'] == 'survey_nuisance_report_v1.json'
    assert artifact['production_allowed'] is False
    assert artifact['off_diagonal_policy'] == 'diagonal_only_conservative'
    assert len(artifact['covariance_matrix']) == 3
    assert set(artifact['surveys']) == {'CF4', 'CW', 'Radio'}
    json.dumps(artifact)


def test_directional_log_likelihood_penalizes_misalignment():
    from htt.infer.dipole_vector_likelihood import DipoleVectorLikelihood
    from htt.infer.shared_cause import run_shared_cause_test

    obs = _load_obs()
    result = run_shared_cause_test(obs)
    dvl = DipoleVectorLikelihood(obs)

    aligned = dvl.directional_log_likelihood(
        result.direction_l,
        result.direction_b,
        result.amplitude,
    )
    misaligned = dvl.directional_log_likelihood(
        (result.direction_l + 180.0) % 360.0,
        -result.direction_b,
        result.amplitude,
    )

    assert aligned > misaligned


def test_shared_cause_auto_fit_is_not_hardcoded():
    from htt.infer.shared_cause import run_shared_cause_test

    obs = copy.deepcopy(_load_obs())
    target_l = 120.0
    target_b = 10.0
    target_a = 2.4e-3

    dp = obs['dipole_observations']
    dp['cf4_watkins_2023']['l_deg'] = target_l
    dp['cf4_watkins_2023']['b_deg'] = target_b
    dp['cf4_watkins_2023']['beta'] = target_a
    dp['catwise_bohme_2025']['l_deg'] = target_l
    dp['catwise_bohme_2025']['b_deg'] = target_b
    dp['catwise_bohme_2025']['eps1'] = target_a
    dp['radio_secrest_2021']['l_deg'] = target_l
    dp['radio_secrest_2021']['b_deg'] = target_b
    dp['radio_secrest_2021']['eps1'] = target_a

    result = run_shared_cause_test(obs)

    assert result.direction_l == pytest.approx(target_l)
    assert result.direction_b == pytest.approx(target_b)
    assert result.amplitude == pytest.approx(target_a)
    assert abs(result.direction_l - 264.0) > 1.0
    assert abs(result.direction_b - 48.0) > 1.0
    assert abs(result.amplitude - 1.1e-3) > 1e-4


def test_shared_cause_report_artifact_is_json_ready():
    from htt.infer.shared_cause import shared_cause_report_artifact

    artifact = shared_cause_report_artifact(
        _load_obs(),
        metadata={'git_commit': 'test'},
    )

    assert artifact['artifact_name'] == 'shared_cause_report_v1.json'
    assert artifact['production_allowed'] is False
    assert artifact['fit_mode'] == 'weighted_data_fit'
    assert len(artifact['ablation_checks']) == 3
    assert artifact['config_hash'] != ''
    json.dumps(artifact)
