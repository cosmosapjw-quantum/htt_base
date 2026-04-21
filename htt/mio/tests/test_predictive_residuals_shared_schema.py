"""IM-07M regression tests for shared-schema predictive residual atlases."""
from __future__ import annotations

import numpy as np

from common.contracts import ArtifactManifest, SkySupport
from mio.diagnostics.predictive_residuals import (
    ResidualChannelSlice,
    build_predictive_residual_atlas_from_shared_schema,
    emit_predictive_residuals_artefact,
    emit_predictive_residuals_shared_schema_artefact,
)
from tsc.admissibility.domain import build_domain_report
from tsc.budget.source_to_channel import build_channel_budgets
from tsc.control.upgrade_advisor import recommend_chart_transition
from tsc.reports.overlay_builder import build_tsc_overlay
from tsc.residuals.blockwise import ambient_vs_projected_defect_report
from tsc.source.thomson_bridge import build_source_bridge_report
from workspace.contracts.atlas_entry_lite import AtlasEntryLite
from workspace.contracts.htt_forward_output import HttForwardOutput
from workspace.contracts.observable_vector import ObservableVector


def _bass_manifest(artifact_id: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/bass/{artifact_id.replace('.', '_')}.json",
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash=f"cfg:{artifact_id}",
        input_hashes=["seed:0"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _tsc_manifest(artifact_id: str = "tsc.overlay") -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/tsc/{artifact_id.replace('.', '_')}.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash=f"cfg:{artifact_id}",
        input_hashes=["seed:0"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="mock_calibrated",
        sky_support_hash="sky123",
        mask_hash="mask123",
        mock_coverage_status="adequate",
        scan_volume_hash="scan123",
    )


def _observable_vector() -> ObservableVector:
    return ObservableVector(
        ell_max=5,
        channels=("TT", "TE", "EE"),
        cl={
            "TT": np.array([0.0, 0.0, 1.0, 1.5, 2.0, 2.5]),
            "TE": np.array([0.0, 0.0, 0.3, 0.5, 0.7, 0.9]),
            "EE": np.array([0.0, 0.0, 0.2, 0.35, 0.5, 0.65]),
        },
        alm_features={"harmonic_basis": "m_explicit"},
        biposh=None,
        template_fit=None,
        covariance_features={"summary": "diagnostic_proxy"},
        scan_volume={"scan_volume_hash": "scan123"},
        sky_support=_sky_support(),
        manifest=_bass_manifest("bass.observable"),
    )


def _forward_output(
    model_name: str,
    *,
    tt_offset: float,
    te_offset: float = 0.0,
    ee_offset: float = 0.0,
) -> HttForwardOutput:
    ell = np.arange(2, 6, dtype=int)
    return HttForwardOutput(
        model_name=model_name,
        bianchi_type="VII_h" if "VII" in model_name else "FLRW",
        axis_galactic_lb_deg=(264.0, 48.0),
        ell=ell,
        C_ell_TT=np.array([1.0, 1.5, 2.0, 2.5]) + tt_offset,
        C_ell_TE=np.array([0.3, 0.5, 0.7, 0.9]) + te_offset,
        C_ell_EE=np.array([0.2, 0.35, 0.5, 0.65]) + ee_offset,
        directional_summary={"l_deg": 264.0, "b_deg": 48.0, "R": 0.9},
        shear_Sigma2=1.0e-8,
        tilt_beta=1.3e-3,
        atlas_entry_hashes=("atlas-entry-1",),
        generated_by="test-suite",
        git_commit="abc123",
        config_hash=f"cfg:{model_name}",
        manifest=_bass_manifest(f"bass.forward.{model_name}"),
    )


def _atlas_entry() -> AtlasEntryLite:
    return AtlasEntryLite(
        atlas_id="atlas-lite-1",
        theory_family="VII_h",
        geometry_params={"h": 0.5},
        kinematic_params={"beta": 1.3e-3},
        tilt_params={"tilt": 1.3e-3},
        solver_output_ref="bass.solver.run0",
        observable_vector_ref="bass.observable",
        response_blocks={"R_covariance_proxy": "cov:block:1"},
        validity_domain={"selection_mode": "mock_calibrated"},
        interpolation_status="ready_for_diagnostics",
        manifest=_bass_manifest("bass.atlas_lite"),
    )


def _overlay_pending():
    manifest = _tsc_manifest()
    domain = build_domain_report(chart="one_field", theta_samples=[1.0, 1.1], manifest=manifest)
    residual = ambient_vs_projected_defect_report(
        chart="one_field",
        laguerre_n_ge_2_norm=0.1,
        ambient_defect_rate=None,
        projected_defect_estimate=None,
        onefield_residual=0.1,
        twofield_residual=0.05,
        eta_tangent_fraction=0.2,
        trace_residual_q_tr=0.1,
        spin2_residual=None,
        high_residual=None,
        labels=tuple(),
        manifest=manifest,
    )
    source = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.1,
        manifest=manifest,
        source_error=0.01,
        on_manifold_exact=True,
    )
    budgets = build_channel_budgets(
        manifest=manifest,
        source_status="adequate",
        propagation_status="pending",
        trace_budget=0.01,
        spin2_budget=0.2,
    )
    upgrade = recommend_chart_transition(domain, residual, source)
    return build_tsc_overlay(
        domain_report=domain,
        residual_report=residual,
        source_bridge_report=source,
        channel_budgets=budgets,
        upgrade_recommendation=upgrade,
        artifact_manifest=manifest,
    )


def test_shared_schema_builder_tracks_worst_model_channel():
    observable = _observable_vector()
    atlas = build_predictive_residual_atlas_from_shared_schema(
        observable,
        [
            _forward_output("FLRW_tilt", tt_offset=0.05, te_offset=0.01),
            _forward_output("BianchiVIIh_tilt", tt_offset=0.60, ee_offset=0.10),
        ],
        atlas_entry=_atlas_entry(),
        ell_bins=((2, 3), (4, 5)),
    )
    assert len(atlas.slices) == 12
    assert atlas.worst_model_label == "BianchiVIIh_tilt"
    assert atlas.worst_channel == "TT"
    assert atlas.atlas_ref == "bass.atlas_lite"
    assert atlas.mean_rms_residual > 0.0


def test_shared_schema_emitter_attaches_manifest_and_overlay(tmp_path):
    observable = _observable_vector()
    overlay = _overlay_pending()
    out_path = tmp_path / "mio_predictive_residuals_v1.json"
    payload = emit_predictive_residuals_shared_schema_artefact(
        out_path,
        observable,
        [_forward_output("FLRW_tilt", tt_offset=0.10, te_offset=0.02)],
        atlas_entry=_atlas_entry(),
        covariance_ref="cov:001",
        tsc_overlay=overlay,
    )
    certificate = payload["certificate"]
    assert certificate["manifest"]["production_status"] == "production_candidate"
    assert certificate["tsc_overlay_ref"] == "tsc.overlay"
    assert certificate["adequacy_indicators"]["tsc_overlay_attached"] is True
    assert certificate["adequacy_indicators"]["tsc_overlay_diagnostic_only"] is True
    assert "tsc_overlay_diagnostic_only" in certificate["domain_caveats"]
    assert payload["shared_schema_inputs"]["observable_vector_ref"] == "bass.observable"
    assert payload["shared_schema_inputs"]["atlas_entry_ref"] == "bass.atlas_lite"


def test_packaged_slice_emitter_attaches_overlay(tmp_path):
    overlay = _overlay_pending()
    out_path = tmp_path / "mio_predictive_residuals_v1.json"
    payload = emit_predictive_residuals_artefact(
        out_path,
        (
            ResidualChannelSlice(
                model_label="FLRW_tilt",
                channel="TT",
                ell_min=2,
                ell_max=5,
                rms_residual=0.1,
                max_abs_residual=0.2,
                n_modes=4,
            ),
        ),
        atlas_ref="bass.atlas_lite",
        covariance_ref="cov:001",
        tsc_overlay=overlay,
    )
    certificate = payload["certificate"]
    assert certificate["tsc_overlay_ref"] == "tsc.overlay"
    assert certificate["adequacy_indicators"]["tsc_overlay_attached"] is True
    assert "tsc_overlay_diagnostic_only" in certificate["domain_caveats"]
