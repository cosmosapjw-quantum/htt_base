"""MIO-HJ-03a/b — FLRW PPP + direct x_C estimator tests."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from mio.tension import (
    ARTEFACT_FILENAME,
    XC_ARTEFACT_FILENAME,
    XCInputs,
    departure_parameter_estimate,
    emit_flrw_tension_artefact,
    emit_xc_direct_estimate_artefact,
    evaluate_flrw_tension,
    posterior_predictive_pvalue,
)
from mio.tension.flrw_tension import to_mio_certificate as flrw_to_mio_certificate
from mio.tension.xc_estimator import estimate_xc_report
from workspace.contracts.mio_certificate import MioCertificate


def test_posterior_predictive_pvalue_right_tail_uses_additive_smoothing():
    p = posterior_predictive_pvalue(
        1.0,
        [0.1, 0.2, 0.5, 1.2],
        tail="greater",
    )
    assert p == pytest.approx((1 + 1) / (4 + 1))


def test_evaluate_flrw_tension_applies_bonferroni_correction():
    report = evaluate_flrw_tension(
        {"T_directional": 1.2, "T_biposh": 3.0},
        {
            "T_directional": [0.2, 0.5, 1.5, 1.7],
            "T_biposh": [0.1, 0.2, 0.3, 0.4],
        },
    )
    stats = {item.name: item for item in report.statistics}
    assert stats["T_directional"].p_value == pytest.approx((2 + 1) / (4 + 1))
    assert stats["T_directional"].corrected_p_value == pytest.approx(
        min(stats["T_directional"].p_value * 2.0, 1.0)
    )
    assert report.strongest_statistic == "T_biposh"
    assert report.min_corrected_p_value == pytest.approx(0.4)


def test_flrw_tension_certificate_has_no_posterior_field():
    report = evaluate_flrw_tension(
        {"T_directional": 2.5},
        {"T_directional": [0.2, 0.4, 0.5, 0.7]},
    )
    cert = flrw_to_mio_certificate(report)
    assert isinstance(cert, MioCertificate)
    for field in dataclasses.fields(cert):
        assert "posterior" not in field.name.lower()
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


def test_emit_flrw_tension_artefact_round_trip(tmp_path: Path):
    out = tmp_path / ARTEFACT_FILENAME
    payload = emit_flrw_tension_artefact(
        out,
        {"T_directional": 2.5, "T_biposh": 0.3},
        {
            "T_directional": [0.2, 0.4, 0.5, 0.7],
            "T_biposh": [0.1, 0.2, 0.4, 0.6],
        },
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    assert payload["certificate"]["report_type"] == "flrw_tension"
    assert payload["certificate"]["probe_name"] == "FLRW"
    assert payload["strongest_statistic"] == "T_directional"


def test_emit_flrw_tension_artefact_rejects_non_mio_prefix(tmp_path: Path):
    with pytest.raises(ValueError, match="must start with 'mio_'"):
        emit_flrw_tension_artefact(
            tmp_path / "bad_flrw_tension.json",
            {"T_directional": 1.0},
            {"T_directional": [0.1, 0.2, 0.3]},
        )


def test_departure_parameter_estimate_matches_plan_formula():
    x_c, sigma_x = departure_parameter_estimate(
        XCInputs(
            sigma2_mio=0.40,
            sigma2_mio_sigma=0.10,
            w2=0.15,
            w2_sigma=0.05,
            omega_tilt=0.03,
            omega_tilt_sigma=0.02,
            omega_k_aniso=0.01,
            omega_k_aniso_sigma=0.01,
        )
    )
    assert x_c == pytest.approx(0.29)
    assert sigma_x == pytest.approx((0.10**2 + 0.05**2 + 0.02**2 + 0.01**2) ** 0.5)


def test_emit_xc_direct_estimate_artefact_round_trip(tmp_path: Path):
    out = tmp_path / XC_ARTEFACT_FILENAME
    payload = emit_xc_direct_estimate_artefact(
        out,
        XCInputs(
            sigma2_mio=0.40,
            sigma2_mio_sigma=0.10,
            w2=0.15,
            w2_sigma=0.05,
            omega_tilt=0.03,
            omega_tilt_sigma=0.02,
            omega_k_aniso=0.01,
            omega_k_aniso_sigma=0.01,
        ),
    )
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded == payload
    assert payload["certificate"]["report_type"] == "flrw_tension"
    assert payload["certificate"]["channel"] == "xc_direct"
    assert payload["report"]["x_c"] == pytest.approx(0.29)


def test_xc_report_significance_tracks_sigma():
    report = estimate_xc_report(
        XCInputs(
            sigma2_mio=0.20,
            sigma2_mio_sigma=0.05,
            w2=0.05,
            w2_sigma=0.02,
            omega_tilt=0.01,
            omega_tilt_sigma=0.01,
            omega_k_aniso=0.00,
            omega_k_aniso_sigma=0.00,
        )
    )
    assert report.x_c == pytest.approx(0.16)
    assert report.significance_sigma > 2.0
