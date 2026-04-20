from __future__ import annotations

from common.contracts import ArtifactManifest, ObservableVector, SkySupport
from common.departure_contracts import BudgetSpec, DepartureBundle

from bass.observational import (
    build_descriptive_departure_report,
    build_full_cov_mes_report,
)
from common.contracts import AtlasEntryLite


def _manifest(owner: str = "BASS", scope: str = "bass_py") -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=f"{owner.lower()}.artifact",
        artifact_path=f"artifacts/{owner.lower()}.json",
        owner=owner,  # type: ignore[arg-type]
        implementation_scope=scope,  # type: ignore[arg-type]
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["x"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _observable(*, with_covariance: bool = True) -> ObservableVector:
    return ObservableVector(
        ell_max=8,
        channels=("TT", "TE"),
        cl={"TT": [1.0], "TE": [0.5]},
        alm_features={"harmonic_basis": "m_explicit"},
        biposh={"representation": "sparse_mode_block_proxy"} if with_covariance else None,
        template_fit=None,
        covariance_features={"psd_guard": {"passed": True}} if with_covariance else None,
        scan_volume={"scan_volume_hash": "scan123"},
        sky_support=SkySupport(
            selection_mode="mock_calibrated",
            sky_support_hash="sky123",
            mask_hash="mask123",
            mock_coverage_status="adequate",
            scan_volume_hash="scan123",
        ),
        manifest=_manifest(),
    )


def _atlas(response_blocks: dict[str, object] | None = None) -> AtlasEntryLite:
    return AtlasEntryLite(
        atlas_id="atlas-lite",
        theory_family="BianchiI",
        geometry_params={},
        kinematic_params={},
        tilt_params={},
        solver_output_ref="solver:1",
        observable_vector_ref="obs:1",
        response_blocks=response_blocks or {"sigma": {"R_sigma_proxy": 1.0}},
        validity_domain={},
        interpolation_status="skeleton",
        manifest=_manifest("BASS", "canonical_BASS"),
    )


def test_full_cov_mes_rank_failure_returns_no_claim():
    result = build_full_cov_mes_report(
        _atlas(),
        _observable(),
        parameter_block="sigma",
        diagonal_bound=2.0,
        singular_values=[],
        covariance_assumption="diag+offdiag",
    )
    assert result.covariance_claim_allowed is False
    assert "response_rank_deficient" in result.blocked_reasons
    assert result.report.covariance_bound is None
    assert result.report.manifest.claim_tier == "blocked"


def test_full_cov_mes_uses_covariance_bound_when_rank_is_available():
    result = build_full_cov_mes_report(
        _atlas(),
        _observable(),
        parameter_block="sigma",
        diagonal_bound=2.0,
        singular_values=[0.5, 2.0],
        covariance_assumption="diag+offdiag",
        noise_radius=0.5,
    )
    assert result.covariance_claim_allowed is True
    assert result.report.covariance_bound == 1.0
    assert result.report.information_gain >= 1.0


def test_departure_report_stays_descriptive_without_claim_gate():
    bundle = DepartureBundle(
        comparator="matched",
        Sigma2_std=0.4,
        W2_std=0.1,
        Omega_tilt=0.2,
        Omega_k_aniso=0.1,
        covariance=None,
        frame_convention="normal_frame",
        sector="full",
        provenance={},
    )
    budget = BudgetSpec(
        kind="linear_MES",
        value=1.0,
        uncertainty=None,
        family_id=None,
        channel="TT",
        redshift=None,
        confidence_level=None,
        assumptions=tuple(),
        is_admissible_ceiling=True,
    )
    result = build_descriptive_departure_report(
        _observable(),
        bundle=bundle,
        budget=budget,
        claim_gate_passed=False,
        occupancy_certified=False,
    )
    assert result.claim_language_allowed is False
    assert "claim_gate_not_passed" in result.blocked_reasons
    assert result.report.F_status == "linear_proxy_score"
    assert "report_is_descriptive_until_claim_gates_pass" in result.report.caveats


def test_departure_report_blocks_negative_sector_certified_filling():
    bundle = DepartureBundle(
        comparator="matched",
        Sigma2_std=0.1,
        W2_std=0.4,
        Omega_tilt=0.0,
        Omega_k_aniso=0.0,
        covariance=None,
        frame_convention="normal_frame",
        sector="full",
        provenance={},
    )
    budget = BudgetSpec(
        kind="linear_MES",
        value=1.0,
        uncertainty=None,
        family_id=None,
        channel="TT",
        redshift=None,
        confidence_level=None,
        assumptions=tuple(),
        is_admissible_ceiling=True,
    )
    result = build_descriptive_departure_report(
        _observable(),
        bundle=bundle,
        budget=budget,
        claim_gate_passed=True,
        occupancy_certified=True,
    )
    assert result.report.F_status == "invalid_negative_sector"
    assert result.report.F_value is None
