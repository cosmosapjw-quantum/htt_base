"""VER2 shared contract layer tests."""
from __future__ import annotations

import numpy as np
import pytest

from common.contracts import (
    ArtifactManifest,
    AtlasEntryLite,
    ClaimLedgerEntry,
    FullCovMESReport,
    TscAdequacyOverlay,
    TscChannelAdequacyBudget,
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)
from common.departure_contracts import (
    BudgetSpec,
    DepartureBundle,
    DepartureReport,
    ExceedanceCurve,
    FillingFraction,
    IsotropyGap,
)


def _manifest(owner: str = "COMMON") -> ArtifactManifest:
    scope_by_owner = {
        "COMMON": "common",
        "BASS": "canonical_BASS",
        "HTT": "htt",
        "MIO": "mio",
        "TSC": "tsc",
    }
    return ArtifactManifest(
        artifact_id=f"{owner.lower()}.artifact",
        artifact_path=f"artifacts/{owner.lower()}.json",
        owner=owner,  # type: ignore[arg-type]
        implementation_scope=scope_by_owner[owner],  # type: ignore[arg-type]
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["x"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def test_atlas_entry_lite_requires_bass_owner():
    with pytest.raises(ValueError, match="must be 'BASS'"):
        AtlasEntryLite(
            atlas_id="atlas-lite",
            theory_family="BianchiI",
            geometry_params={},
            kinematic_params={},
            tilt_params={},
            solver_output_ref="solver:1",
            observable_vector_ref="obs:1",
            response_blocks={},
            validity_domain={},
            interpolation_status="skeleton",
            manifest=_manifest("COMMON"),
        )


def test_full_cov_mes_report_rejects_negative_rank():
    with pytest.raises(ValueError, match="response_rank"):
        FullCovMESReport(
            parameter_block="sigma",
            diagonal_bound=1.0,
            covariance_bound=None,
            dynamical_bound=None,
            final_bound=1.0,
            information_gain=1.0,
            response_rank=-1,
            singular_values=[],
            nuisance_projection_status="none",
            observable_set=[],
            covariance_assumption="diag",
            validity_radius=None,
            manifest=_manifest(),
        )


def test_tsc_overlay_stack_requires_tsc_owner():
    man = _manifest("TSC")
    domain = TscDomainReport(
        chart="one_field",
        theta_min=1.0,
        eta_max=0.0,
        be_eta_nonpositive=True,
        weight_simplex_ok=True,
        jacobian_sigma_min=0.1,
        domain_margin=0.1,
        status="valid_one_field",
        blocking_reasons=tuple(),
        manifest=man,
    )
    residual = TscResidualReport(
        chart="one_field",
        laguerre_n_ge_2_norm=0.0,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.0,
        twofield_residual=None,
        eta_tangent_fraction=None,
        trace_residual_q_tr=None,
        spin2_residual=None,
        high_residual=None,
        residual_origin="trace",
        labels=tuple(),
        manifest=man,
    )
    bridge = TscSourceBridgeReport(
        source_name="other",
        chart="one_field",
        quadrupole_convention="legendre_P2",
        quadrupole_parameter_name="q",
        conversion_to_legendre_q=1.0,
        q2_norm=0.0,
        source_error_bound=None,
        nonlinear_dipole_quartic_correction=None,
        eta_correction_indicator=None,
        on_manifold_exact=False,
        spin2_propagation_required=True,
        source_status="pending",
        required_bass_primitives=tuple(),
        labels=tuple(),
        manifest=man,
    )
    budget = TscChannelAdequacyBudget(
        channel="TT",
        trace_budget=None,
        spin2_budget=None,
        high_budget=None,
        source_to_field_bound=None,
        spectrum_bound_linear=None,
        spectrum_bound_quadratic=None,
        source_status="pending",
        propagation_status="pending",
        claim_ceiling="conditional",
        labels=tuple(),
        manifest=man,
    )
    rec = TscUpgradeRecommendation(
        current_chart="one_field",
        recommended_chart="two_field",
        reason="eta_tangent_false_trigger",
        severity="warn",
        dwell_time_required=None,
        hysteresis_state=None,
        labels=tuple(),
        manifest=man,
    )
    overlay = TscAdequacyOverlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=bridge,
        channel_budgets=(budget,),
        upgrade_recommendation=rec,
        no_overclaim_flags={"tt_only": True},
        quarantine_reasons=tuple(),
        public_caveat_snippet="diagnostic-only",
        manifest=man,
    )
    assert overlay.manifest.owner == "TSC"


def test_tsc_overlay_hook_fields_exist_on_cross_package_reports():
    mes_fields = {field.name for field in FullCovMESReport.__dataclass_fields__.values()}
    departure_fields = {
        field.name for field in DepartureReport.__dataclass_fields__.values()
    }
    assert "tsc_overlay_ref" in mes_fields
    assert "tsc_overlay_ref" in departure_fields


def test_departure_bundle_signed_and_positive_views():
    bundle = DepartureBundle(
        comparator="matched",
        Sigma2_std=3.0,
        W2_std=5.0,
        Omega_tilt=1.0,
        Omega_k_aniso=0.5,
        covariance=None,
        frame_convention="normal_frame",
        sector="full",
        provenance={},
    )
    assert bundle.x_signed == -0.5
    assert bundle.x_positive == 0.0


def test_budget_spec_rejects_negative_value():
    with pytest.raises(ValueError, match="non-negative"):
        BudgetSpec(
            kind="linear_MES",
            value=-1.0,
            uncertainty=None,
            family_id=None,
            channel=None,
            redshift=None,
            confidence_level=None,
            assumptions=tuple(),
            is_admissible_ceiling=True,
        )


def test_claim_ledger_entry_requires_claim_content():
    with pytest.raises(ValueError, match="at least one allowed or forbidden claim"):
        ClaimLedgerEntry(
            artifact_id="claimless",
            owner="COMMON",
            claim_tier="conditional",
            allowed_claims=tuple(),
            forbidden_claims=tuple(),
            evidence_refs=tuple(),
            source_commit="abc123",
        )


def test_exceedance_curve_requires_matching_shapes():
    with pytest.raises(ValueError, match="matching shape"):
        ExceedanceCurve(
            q_grid=np.zeros(4),
            pi_grid=np.zeros(3),
            uncertainty_kind="bootstrap",
            target="Q",
            threshold_labels={},
            q50=0.0,
            q95=0.0,
            provenance={},
        )


def test_departure_report_owner_restricted():
    budget = BudgetSpec(
        kind="linear_MES",
        value=1.0,
        uncertainty=None,
        family_id=None,
        channel=None,
        redshift=None,
        confidence_level=None,
        assumptions=tuple(),
        is_admissible_ceiling=True,
    )
    fill = FillingFraction(
        value=0.3,
        status="certified_occupancy",
        score_if_invalid=None,
        comparator="matched",
        budget=budget,
        sector="full",
        redshift=None,
        component_breakdown={},
        provenance={},
    )
    gap = IsotropyGap(
        value=0.0,
        kind="difference",
        z_a=0.0,
        z_b=1.0,
        F_a=fill,
        F_b=fill,
        epsilon_floor=1e-12,
        status="ok",
        uncertainty_kind="bootstrap",
        provenance={},
    )
    assert gap.kind == "difference"
    with pytest.raises(ValueError, match="must be 'HTT', 'MIO', or 'COMMON'"):
        DepartureReport(
            comparator_policy="matched",
            bundle_B={"Sigma2": 0.1},
            x_value=0.1,
            numerator_policy="signed",
            denominator_policy="MES",
            U_value=1.0,
            Q_value=0.1,
            F_value=0.3,
            F_status="certified_occupancy",
            Pi_curve_ref=None,
            G_values={},
            component_filling={},
            channel_filling={},
            caveats=[],
            manifest=_manifest("BASS"),
        )
