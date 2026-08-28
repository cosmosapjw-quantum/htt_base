"""PR-120 active HTT channel-c quarantine contracts."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import numpy as np
import pytest


# PR-124 preflight (2026-07-17): rebased by the history rewrite; the
# pre-rewrite id e6da3670043596efdcd93f9ba5e631e1462146c7 resolves via
# docs/git_history/commit_map_20260717.tsv.
_FROZEN_SOURCE_COMMIT = "47693b06f06ee61f758371f0dca1dad6a0028191"
_FROZEN_CONSUMER_PATHS = (
    "htt/htt/htt/core/directional_models.py",
    "htt/htt/htt/core/departure_posteriors.py",
    "htt/htt/htt/core/evidence_models.py",
    "htt/htt/htt/core/h0_sensitivity.py",
    "htt/htt/htt/core/pipeline.py",
    "htt/htt/htt/core/ssot.py",
    "htt/htt/htt/figures/fig_cf4pp_sensitivity.py",
    "htt/htt/htt/figures/fig_colin_beta.py",
    "htt/htt/htt/figures/fig_departure_summary.py",
    "htt/htt/htt/figures/fig_evidence_decomposition.py",
    "htt/htt/htt/figures/fig_peculiar_jeans.py",
    "htt/htt/htt/figures/fig_q0_pushforward.py",
    "htt/htt/htt/figures/fig_scale_hierarchy.py",
    "htt/htt/htt/figures/fig_tilted_H0_depth.py",
    "htt/htt/htt/figures/fig_v_pushforward.py",
    "htt/htt/htt/infer/control_registry.py",
    "htt/htt/htt/infer/directional_lowell.py",
    "htt/htt/htt/infer/matched_complexity.py",
    "htt/htt/htt/infer/shared_cause.py",
    "htt/htt/htt/infer/survey_nuisance.py",
)


def _active_obs() -> dict:
    return {
        "dipole_observations": {
            "cmb_planck_2018": {
                "l_deg": 264.021,
                "b_deg": 48.253,
            },
            "catwise_bohme_2025": {
                "l_deg": 238.2,
                "b_deg": 28.8,
                "eps1": 1.6e-3,
                "sigma_stat": 0.2e-3,
            },
            "radio_secrest_2021": {
                "l_deg": 251.0,
                "b_deg": 38.0,
                "eps1": 1.5e-3,
                "sigma_stat": 0.3e-3,
            },
            "rho_CW_radio": 0.0,
        }
    }


def test_typed_provider_exposes_no_numerical_or_replacement_payload() -> None:
    from htt.core.cf4_observational_input import (
        OPEN_FINDING_IDS,
        cf4_quarantine_status,
    )

    status = cf4_quarantine_status()
    assert status.status == "QUARANTINED_OPEN_FINDINGS"
    assert status.finding_ids == OPEN_FINDING_IDS
    assert status.numerical_payload is None
    assert status.replacement_payload is None
    assert status.active_use_allowed is False
    assert set(status.finding_ids) == {
        "C1-K5-MV-F1",
        "C3-K5-VCORR-ML-F1",
        "N-DATA-CF4-DOWNSTREAM",
    }


def test_evidence_defaults_exclude_c_and_explicit_c_fails_closed() -> None:
    from htt.core.cf4_observational_input import (
        ACTIVE_DEFAULT_CHANNELS,
        CF4InputQuarantined,
    )
    from htt.core.evidence_models_R03a import FLRW, ObsData, create_model

    with pytest.raises(CF4InputQuarantined, match="implicit/default likelihood"):
        FLRW()
    with pytest.raises(CF4InputQuarantined, match="implicit/default likelihood"):
        create_model("FLRW")
    assert FLRW(channels=ACTIVE_DEFAULT_CHANNELS).channels == "abdefh"
    assert create_model(
        "FLRW", channels=ACTIVE_DEFAULT_CHANNELS
    ).channels == "abdefh"
    with pytest.raises(CF4InputQuarantined, match="N-DATA-CF4-DOWNSTREAM"):
        FLRW(channels="abcdefh")
    with pytest.raises(CF4InputQuarantined, match="C1-K5-MV-F1"):
        _ = ObsData().b_CF4


def test_workspace_default_has_status_only_and_no_cf4_dipole_row() -> None:
    repo = Path(__file__).resolve().parents[2]
    payload = json.loads(
        (repo / "htt/workspace/data/obs_defaults.json").read_text(encoding="utf-8")
    )

    assert "cf4_watkins_2023" not in payload["dipole_observations"]
    quarantine = payload["quarantined_observational_inputs"]["channel_c_cf4"]
    assert quarantine["numerical_payload"] is None
    assert quarantine["replacement_payload"] is None
    assert quarantine["active_use_allowed"] is False


def test_evidence_comparison_and_compatibility_kwargs_require_explicit_c_free_mode() -> None:
    from htt.core.analysis_extended import EvidenceComparison
    from htt.core.cf4_observational_input import (
        ACTIVE_DEFAULT_CHANNELS,
        CF4InputQuarantined,
    )
    from htt.core.evidence_models_R03a import consistency_Dq

    with pytest.raises(CF4InputQuarantined, match="implicit/default likelihood"):
        EvidenceComparison()
    comparison = EvidenceComparison(channels=ACTIVE_DEFAULT_CHANNELS)
    assert comparison.channels == ACTIVE_DEFAULT_CHANNELS
    with pytest.raises(CF4InputQuarantined, match="consistency_Dq CF4 arguments"):
        consistency_Dq(1.0e-4, beta_CF4=1.0e-3)


def test_active_dipole_and_latent_axis_paths_ignore_injected_cf4_mapping() -> None:
    from htt.infer.dipole_vector_likelihood import DipoleVectorLikelihood
    from htt.infer.latent_axis import LatentAxisModel

    obs = _active_obs()
    obs["dipole_observations"]["cf4_watkins_2023"] = {
        "beta": 99.0,
        "sigma": 1.0e-12,
        "l_deg": 1.0,
        "b_deg": 2.0,
    }

    likelihood = DipoleVectorLikelihood(obs)
    assert likelihood.excluded_channels == ("c",)
    assert not hasattr(likelihood, "b_CF4")
    assert np.isfinite(likelihood.scalar_log_likelihood(1.0e-3))

    latent = LatentAxisModel(obs)
    assert latent.ndim == 7
    theta = latent.prior_transform(np.full(7, 0.5))
    assert theta.shape == (7,)
    assert np.isfinite(latent.log_likelihood(theta))


def test_null_generators_and_runner_operate_without_cf4_channel() -> None:
    from htt.nulls.runner import run_null_library
    from htt.nulls.scanning_law import ScanningLawNull

    obs = _active_obs()
    sample = ScanningLawNull().generate(seed=7, obs_base=obs)
    assert sample.b_CF4 == 0.0
    assert np.isinf(sample.b_CF4_s)

    report = run_null_library(obs, n_datasets=2)
    assert report["_meta"]["excluded_channels"] == ["c"]
    assert report["_meta"]["cf4_channel_status"] == "QUARANTINED_OPEN_FINDINGS"
    assert len(report["families"]) == 5


def test_lowz_and_bridge_defaults_fail_but_explicit_synthetic_inputs_work() -> None:
    from htt.bridge.runner import run_bridge_bundle
    from htt.core.cf4_observational_input import CF4InputQuarantined
    from htt.infer.lowz_ablation import LowzAblation

    with pytest.raises(CF4InputQuarantined):
        LowzAblation()
    explicit = LowzAblation(
        z_catalog=np.asarray([0.01, 0.02]),
        beta_catalog=np.asarray([1.0e-4, 1.1e-4]),
        lowz_axis=(120.0, 10.0),
    )
    assert explicit.z_catalog.shape == (2,)

    with pytest.raises(CF4InputQuarantined):
        run_bridge_bundle()
    bundle = run_bridge_bundle(beta=1.0e-4, input_mode="synthetic")
    assert bundle["excluded_channels"] == ["c"]
    assert bundle["input_mode"] == "synthetic"


def test_non_cf4_diagnostics_do_not_reintroduce_channel_c() -> None:
    from htt.core.advanced_diagnostics import (
        CrossChannelCoherence,
        DepthTomography,
        PosteriorPredictive,
    )
    from htt.core.source_discrimination import (
        SURVEY_CATALOG,
        run_source_discrimination,
    )

    depth = DepthTomography().run()
    assert {row.name for row in depth.bins} == {"CatWISE", "Radio"}
    coherence = CrossChannelCoherence().run()
    assert {row.channel for row in coherence.estimates} == {"CatWISE", "Radio"}
    predictive = PosteriorPredictive().compute("synthetic", 1.0e-4)
    assert "beta_CF4" not in predictive.observables
    assert "CF4" not in SURVEY_CATALOG
    source = run_source_discrimination(verbose=False)
    assert source["source_models"]["status"] == (
        "blocked_insufficient_non_cf4_surveys"
    )


def test_cf4_conditioned_active_producers_raise_canonical_error() -> None:
    from htt.core.cf4_observational_input import CF4InputQuarantined
    from htt.core.h0_sensitivity import run_h0_sensitivity
    from htt.figures.fig_departure_summary import main as make_departure_summary
    from htt.figures.fig_v_pushforward import main as make_v_pushforward

    with pytest.raises(CF4InputQuarantined, match="OPEN findings"):
        run_h0_sensitivity()
    with pytest.raises(CF4InputQuarantined, match="OPEN findings"):
        make_v_pushforward()
    with pytest.raises(CF4InputQuarantined, match="OPEN findings"):
        make_departure_summary()


def test_deprecated_evidence_alias_and_directional_models_have_no_c_route() -> None:
    from htt.core import evidence_models
    from htt.core.cf4_observational_input import (
        ACTIVE_DEFAULT_CHANNELS,
        CF4InputQuarantined,
    )
    from htt.core.directional_models import FLRW_tilt_directional, REFS

    with pytest.raises(CF4InputQuarantined, match="implicit/default likelihood"):
        evidence_models.FLRW()
    assert evidence_models.FLRW(
        channels=ACTIVE_DEFAULT_CHANNELS
    ).channels == "abdefh"
    assert "CF4" not in REFS
    model = FLRW_tilt_directional()
    assert model.excluded_channels == ("c",)
    assert np.isfinite(model.log_likelihood(np.asarray([1.0e-4, 120.0, 10.0])))


def test_shared_cause_and_nuisance_paths_ignore_or_reject_cf4() -> None:
    from htt.core.cf4_observational_input import CF4InputQuarantined
    from htt.infer.shared_cause import shared_cause_report_artifact
    from htt.infer.survey_nuisance import (
        SURVEY_REGISTRY,
        get_survey_nuisance,
        survey_nuisance_report_artifact,
    )

    obs = _active_obs()
    baseline = shared_cause_report_artifact(obs)
    obs["dipole_observations"]["cf4_watkins_2023"] = {
        "beta": 99.0,
        "sigma": 1.0e-12,
        "l_deg": 1.0,
        "b_deg": 2.0,
    }
    injected = shared_cause_report_artifact(obs)
    for key in ("amplitude", "direction_l", "direction_b"):
        assert injected[key] == pytest.approx(baseline[key])
    assert injected["excluded_channels"] == ["c"]
    assert len(injected["ablation_checks"]) == 2

    assert set(SURVEY_REGISTRY) == {"CW", "Radio"}
    with pytest.raises(CF4InputQuarantined):
        get_survey_nuisance("CF4")
    nuisance = survey_nuisance_report_artifact(
        {"CW": 2.0e-4, "Radio": 3.0e-4}
    )
    assert nuisance["excluded_channels"] == ["c"]


def test_lowell_and_control_defaults_cannot_restore_channel_c() -> None:
    from htt.core.cf4_observational_input import CF4InputQuarantined
    from htt.infer.control_registry import CONTROLS
    from htt.infer.directional_lowell import LowellLikelihood
    from htt.infer.matched_complexity import LowZAblation

    with pytest.raises(CF4InputQuarantined):
        LowellLikelihood()
    explicit = LowellLikelihood(lowz_l=120.0, lowz_b=10.0).evaluate()
    assert explicit.status == "diagnostic_only"
    assert explicit.excluded_channels == ("c",)

    assert CONTROLS["C1"].n_nuisance == 2
    assert CONTROLS["C2"].n_nuisance == 2
    assert CONTROLS["C3"].n_amplitude == 2
    with pytest.raises(CF4InputQuarantined):
        LowZAblation(_active_obs()).ablate("CF4")


@pytest.mark.parametrize("relative_path", _FROZEN_CONSUMER_PATHS)
def test_frozen_legacy_consumer_is_recoverable_from_source_commit(
    relative_path: str,
) -> None:
    repo = Path(__file__).resolve().parents[2]
    frozen = repo / "legacy/cf4_p0/htt_consumers" / relative_path
    source = subprocess.run(
        ["git", "show", f"{_FROZEN_SOURCE_COMMIT}:{relative_path}"],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout

    if frozen.exists():
        assert frozen.is_file()
        assert not frozen.is_symlink()
        assert frozen.read_bytes() == source
    else:
        assert source
