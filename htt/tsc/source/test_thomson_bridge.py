from __future__ import annotations

import numpy as np
import pytest

from common.contracts import ArtifactManifest
from tsc.source.quadrupole_conventions import linear_intensity_quadrupole_from_parameter
from tsc.source.thomson_bridge import (
    build_source_bridge_report,
    build_source_bridge_report_from_samples,
    eta_correction_indicator,
    intensity_from_theta,
    quadrupole_from_intensity,
    source_error_bound,
    thomson_source_from_quadrupole,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.source.bridge",
        artifact_path="artifacts/tsc/source_bridge.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["a"],
        code_version="0.0-test",
        schema_version="ver2-v1",
    )


def test_axisymmetric_table_convention_matches_q_normalization_regression():
    mu, weights = np.polynomial.legendre.leggauss(256)
    amplitude_dipole = 0.30
    quadrupole_amp = 0.15
    theta = 1.0 + amplitude_dipole * mu + quadrupole_amp * (mu ** 2 - 1.0 / 3.0)

    intensity = intensity_from_theta(theta, T0=1.0, xi=0)
    exact_q2 = quadrupole_from_intensity(intensity, mu, weights)
    linear_q2 = linear_intensity_quadrupole_from_parameter(
        quadrupole_amp,
        "mu2_minus_one_third",
    )
    underestimate = 1.0 - linear_q2 / exact_q2

    assert exact_q2 == pytest.approx(0.84214, rel=5.0e-4, abs=5.0e-5)
    assert linear_q2 == pytest.approx(0.40000, abs=1.0e-12)
    assert underestimate == pytest.approx(0.5250, rel=2.0e-3)


def test_source_error_bound_scales_with_delta_i_and_prefactor():
    bound_small = source_error_bound(0.05, q2_op_norm=2.0, ne=3.0, sigma_T=5.0)
    bound_large = source_error_bound(0.10, q2_op_norm=2.0, ne=3.0, sigma_T=5.0)

    assert bound_small == pytest.approx(0.15)
    assert bound_large == pytest.approx(0.30)
    assert bound_large == pytest.approx(2.0 * bound_small)


def test_thomson_source_uses_documented_minus_one_tenth_prefactor():
    source = thomson_source_from_quadrupole(q2=0.84, ne=2.0, sigma_T=5.0)
    assert source == pytest.approx(-0.84)


def test_eta_correction_indicator_tracks_twofield_smallness():
    indicator_small = eta_correction_indicator(np.array([-0.02, -0.01]), xi=1)
    indicator_large = eta_correction_indicator(np.array([-1.5, -1.0]), xi=1)

    assert indicator_small < 0.1
    assert indicator_large > indicator_small


def test_linear_bridge_warning_fires_for_moderate_dipole():
    report = build_source_bridge_report(
        chart="one_field",
        q2_norm=0.84214,
        manifest=_manifest(),
        source_error=0.05,
        quadrupole_convention="mu2_minus_one_third",
        dipole_amplitude=0.30,
        linear_bridge_requested=True,
    )

    assert report.source_status == "adequate"
    assert report.quadrupole_convention == "mu2_minus_one_third"
    assert report.quadrupole_parameter_name == "Q_mu"
    assert report.conversion_to_legendre_q == pytest.approx(2.0 / 3.0)
    assert report.spin2_propagation_required is True
    assert "linear_bridge_underestimates_risk" in report.labels


def test_build_source_bridge_report_from_samples_infers_exact_trace_labels_and_primitives():
    mu, weights = np.polynomial.legendre.leggauss(32)
    theta = 1.0 + 0.10 * mu

    report = build_source_bridge_report_from_samples(
        chart="one_field",
        theta_samples=theta,
        directions=mu,
        weights=weights,
        manifest=_manifest(),
        quadrupole_convention="legendre_P2",
        on_manifold_exact=True,
        linear_bridge_requested=False,
    )

    assert report.source_status == "adequate"
    assert "trace_source_exact_on_manifold" in report.labels
    assert report.quadrupole_convention == "legendre_P2"
    assert report.quadrupole_parameter_name == "q"
    assert report.conversion_to_legendre_q == pytest.approx(1.0)
    assert report.spin2_propagation_required is True
    assert report.required_bass_primitives == (
        "theta_samples",
        "quadrature_weights",
        "electron_density",
        "sigma_T",
    )


def test_build_source_bridge_report_from_samples_marks_pending_off_manifold_bridge():
    mu, weights = np.polynomial.legendre.leggauss(32)
    theta = 1.0 + 0.25 * mu

    report = build_source_bridge_report_from_samples(
        chart="two_field",
        theta_samples=theta,
        directions=mu,
        weights=weights,
        manifest=_manifest(),
        quadrupole_convention="mu2_minus_one_third",
        eta=np.full_like(theta, -0.3),
        on_manifold_exact=False,
        linear_bridge_requested=True,
        q2_op_norm=0.2,
    )

    assert report.source_status == "pending"
    assert report.quadrupole_convention == "mu2_minus_one_third"
    assert "source_bridge_bound_pending" in report.labels
    assert "eta_correction_not_small" in report.labels or "eta_correction_small" in report.labels
    assert "eta_samples" in report.required_bass_primitives
