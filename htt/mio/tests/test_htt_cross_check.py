"""Tests for ``mio.interface.htt_cross_check`` (D38).

Covers
  * sum-rule rule (``evidence_anatomy``) — consistent / divergent / missing
  * alarm-sign rule (``flrw_tension``) — agreement / disagreement / missing
  * default fallback (``incomparable`` with diagnostic note)
  * G19 structural guarantees:
      - table has NO merged scalar field mixing MIO and HTT values
      - payload has NO field containing the substring 'posterior'
      - ``build_cross_check_table`` refuses non-``PosteriorExportBundle``
        inputs (cannot be spoofed with an arbitrary object)
  * ``register_rule`` extension hook and overwrite safety
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from mio.interface.htt_cross_check import (
    CrossCheckRow,
    CrossCheckTable,
    STATUS_CONSISTENT,
    STATUS_DIVERGENT,
    STATUS_INCOMPARABLE,
    build_cross_check_table,
    register_rule,
    table_to_payload,
)
from workspace.contracts.htt_to_mio import PosteriorExportBundle
from workspace.contracts.mio_certificate import MioCertificate


# ─── Fixture builders ─────────────────────────────────────────────────
def _evidence_anatomy_cert(total_delta_lnB: float) -> MioCertificate:
    return MioCertificate(
        report_type="evidence_anatomy",
        probe_name="FLRW_tilt",
        channel="channel_decomposition",
        departure_variables={
            "total_delta_lnB": float(total_delta_lnB),
            "reconstructed_delta_lnB": float(total_delta_lnB),
            "strongest_channel_delta_lnB": float(total_delta_lnB) * 0.5,
            "n_channels": 7.0,
        },
        adequacy_indicators={"sum_rule_within_tolerance": True},
        consistency_metrics={"residual_delta_lnB": 0.0, "relative_residual": 0.0},
        domain_caveats=["mio_evidence_anatomy_diagnostic_only"],
        channel_caveats=[],
        reduction_status="diagnostic-only",
        generated_by="test",
        git_commit="abc",
        config_hash="def",
        input_data_hashes=[],
        htt_cross_check_suggested={
            "compare_to": "htt.core.analysis_extended.evidence_matrix_report_artifact",
            "expected_relation": "channel contributions should reconstruct the HTT total evidence within tolerance",
        },
    )


def _flrw_tension_cert(ppp_alarm: bool, ppp_pvalue: float = 0.02) -> MioCertificate:
    return MioCertificate(
        report_type="flrw_tension",
        probe_name="FLRW",
        channel="ppp",
        departure_variables={
            "min_raw_ppp_pvalue": float(ppp_pvalue),
            "min_corrected_ppp_pvalue": float(ppp_pvalue),
            "strongest_observed_statistic": 1.5,
            "n_test_statistics": 3.0,
        },
        adequacy_indicators={
            "ppp_raw_p_lt_0p05": bool(ppp_alarm),
            "ppp_corrected_p_lt_0p05": bool(ppp_alarm),
            "ppp_corrected_p_lt_0p01": False,
        },
        consistency_metrics={},
        domain_caveats=["mio_ppp_diagnostic_only"],
        channel_caveats=[],
        reduction_status="theory-approximate",
        generated_by="test",
        git_commit="abc",
        config_hash="def",
        input_data_hashes=[],
        htt_cross_check_suggested={
            "compare_to": "htt.core.advanced_diagnostics.posterior_predictive_report_artifact",
            "expected_relation": "MIO PPP and HTT predictive residual alarms should agree in sign",
        },
    )


def _bundle(ln_B_total: float = 26.40, Pi_median: float = 0.02) -> PosteriorExportBundle:
    return PosteriorExportBundle(
        x_median=0.1,
        x_hpd68=(0.05, 0.15),
        x_hpd95=(0.01, 0.20),
        Q_median=0.3,
        Q_hpd68=(0.2, 0.4),
        Pi_median=float(Pi_median),
        Pi_hpd68=(0.01, 0.10),
        ln_B_total=float(ln_B_total),
        F_median=0.09,
        F_hpd68=(0.06, 0.13),
        n_live=500,
        model_evidences={"FLRW": 0.0, "FLRW_tilt": float(ln_B_total)},
        model="FLRW_tilt",
    )


# ─── Evidence-anatomy rule ────────────────────────────────────────────
def test_evidence_anatomy_consistent_within_tolerance():
    cert = _evidence_anatomy_cert(total_delta_lnB=26.35)
    tbl = build_cross_check_table([cert], _bundle(ln_B_total=26.40), tolerance=0.05)

    assert len(tbl.rows) == 1
    row = tbl.rows[0]
    assert row.status == STATUS_CONSISTENT
    assert row.mio_value == pytest.approx(26.35)
    assert row.htt_value == pytest.approx(26.40)
    assert row.relative_residual is not None
    assert row.relative_residual == pytest.approx(0.05 / 26.40, rel=1e-6)
    assert tbl.summary[STATUS_CONSISTENT] == 1
    assert tbl.summary[STATUS_DIVERGENT] == 0


def test_evidence_anatomy_divergent_when_sum_rule_fails():
    cert = _evidence_anatomy_cert(total_delta_lnB=10.0)
    tbl = build_cross_check_table([cert], _bundle(ln_B_total=26.40), tolerance=0.05)
    row = tbl.rows[0]
    assert row.status == STATUS_DIVERGENT
    assert "sum rule fails" in row.note


def test_evidence_anatomy_missing_total_is_incomparable():
    cert = dataclasses.replace(
        _evidence_anatomy_cert(total_delta_lnB=26.4),
        departure_variables={"n_channels": 7.0},  # no total_delta_lnB
    )
    tbl = build_cross_check_table([cert], _bundle(), tolerance=0.05)
    row = tbl.rows[0]
    assert row.status == STATUS_INCOMPARABLE
    assert "total_delta_lnB" in row.note
    assert row.mio_value is None


# ─── FLRW-tension alarm-sign rule ─────────────────────────────────────
def test_flrw_tension_alarms_agree():
    cert = _flrw_tension_cert(ppp_alarm=True)
    tbl = build_cross_check_table(
        [cert], _bundle(Pi_median=0.20), tolerance=0.05
    )
    row = tbl.rows[0]
    assert row.status == STATUS_CONSISTENT
    assert "agree" in row.note


def test_flrw_tension_alarms_disagree():
    cert = _flrw_tension_cert(ppp_alarm=True)
    tbl = build_cross_check_table(
        [cert], _bundle(Pi_median=0.02), tolerance=0.05
    )
    row = tbl.rows[0]
    assert row.status == STATUS_DIVERGENT
    assert "disagreement" in row.note


def test_flrw_tension_missing_indicator_is_incomparable():
    base = _flrw_tension_cert(ppp_alarm=True)
    cert = dataclasses.replace(
        base,
        adequacy_indicators={
            "ppp_raw_p_lt_0p05": True,
            # 'ppp_corrected_p_lt_0p05' omitted
        },
    )
    tbl = build_cross_check_table([cert], _bundle(), tolerance=0.05)
    row = tbl.rows[0]
    assert row.status == STATUS_INCOMPARABLE
    assert "ppp_corrected_p_lt_0p05" in row.note


# ─── Default fallback + unregistered rules ────────────────────────────
def test_cert_without_hint_is_incomparable():
    # Build an otherwise-valid cert with no htt_cross_check_suggested set.
    cert = MioCertificate(
        report_type="custom_report",
        probe_name="X",
        channel="Y",
        departure_variables={},
        adequacy_indicators={},
        consistency_metrics={},
        domain_caveats=[],
        channel_caveats=[],
        reduction_status="diagnostic-only",
        generated_by="test",
        git_commit="abc",
        config_hash="def",
        input_data_hashes=[],
        htt_cross_check_suggested=None,
    )
    tbl = build_cross_check_table([cert], _bundle(), tolerance=0.05)
    row = tbl.rows[0]
    assert row.status == STATUS_INCOMPARABLE
    assert row.htt_target == ""
    assert "no rule registered" in row.note


def test_cert_with_unknown_compare_to_is_incomparable():
    base = _evidence_anatomy_cert(total_delta_lnB=26.40)
    cert = dataclasses.replace(
        base,
        htt_cross_check_suggested={"compare_to": "htt.made.up.path", "expected_relation": "n/a"},
    )
    tbl = build_cross_check_table([cert], _bundle(), tolerance=0.05)
    row = tbl.rows[0]
    assert row.status == STATUS_INCOMPARABLE
    assert "htt.made.up.path" in row.note


# ─── G19 structural guarantees ────────────────────────────────────────
def test_cross_check_table_has_no_merged_mio_htt_scalar():
    """No field on CrossCheckTable or CrossCheckRow merges MIO and HTT values."""
    for tp in (CrossCheckTable, CrossCheckRow):
        for f in dataclasses.fields(tp):
            name = f.name.lower()
            assert not ("combined" in name or "merged" in name or "total_score" in name), (
                f"{tp.__name__}.{f.name} looks like a merged MIO+HTT scalar "
                "(G19 §10.2bis forbids combining)."
            )


def test_cross_check_payload_has_no_posterior_field():
    """G19: MIO-owned payload must not carry any 'posterior'-named key."""
    cert = _evidence_anatomy_cert(total_delta_lnB=26.40)
    tbl = build_cross_check_table([cert], _bundle(), tolerance=0.05)
    payload = table_to_payload(tbl)

    # Recursively check all keys.
    def _all_keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from _all_keys(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from _all_keys(item)

    for key in _all_keys(payload):
        assert "posterior" not in str(key).lower(), (
            f"MIO cross-check payload carries posterior-named key: {key!r} "
            "(G19 §10.2bis)."
        )
    # JSON round-trip sanity
    json.dumps(payload)


def test_build_rejects_non_posterior_bundle_input():
    """MIO cannot synthesize an HTT posterior bundle (G19)."""
    cert = _evidence_anatomy_cert(total_delta_lnB=26.40)
    with pytest.raises(TypeError, match="PosteriorExportBundle"):
        build_cross_check_table([cert], {"ln_B_total": 26.40})  # type: ignore[arg-type]


def test_build_rejects_negative_tolerance():
    cert = _evidence_anatomy_cert(total_delta_lnB=26.40)
    with pytest.raises(ValueError, match="tolerance"):
        build_cross_check_table([cert], _bundle(), tolerance=-1e-3)


# ─── register_rule extension hook ─────────────────────────────────────
def test_register_rule_and_consume(monkeypatch):
    from mio.interface import htt_cross_check as xc

    # Snapshot + restore the registry so the global state is not polluted
    # when tests run in any order.
    original = dict(xc._RULE_REGISTRY)
    try:
        def _rule(cert, bundle, tol):
            # Trivial rule: flag consistent iff mio_value == htt_value exactly.
            mio = cert.departure_variables.get("scalar")
            htt = bundle.Q_median
            if mio is None:
                return (None, htt, None, STATUS_INCOMPARABLE, "no scalar")
            status = STATUS_CONSISTENT if mio == htt else STATUS_DIVERGENT
            return (float(mio), float(htt), None, status, "custom")

        register_rule("custom", "htt.fake.target", _rule)
        cert = MioCertificate(
            report_type="custom",
            probe_name="P",
            channel="C",
            departure_variables={"scalar": 0.3},
            adequacy_indicators={},
            consistency_metrics={},
            domain_caveats=[],
            channel_caveats=[],
            reduction_status="diagnostic-only",
            generated_by="t",
            git_commit="g",
            config_hash="h",
            input_data_hashes=[],
            htt_cross_check_suggested={
                "compare_to": "htt.fake.target",
                "expected_relation": "identical",
            },
        )
        tbl = build_cross_check_table([cert], _bundle(), tolerance=0.05)
        assert tbl.rows[0].status == STATUS_CONSISTENT
    finally:
        xc._RULE_REGISTRY.clear()
        xc._RULE_REGISTRY.update(original)


def test_register_rule_refuses_overwrite_without_flag():
    with pytest.raises(ValueError, match="already registered"):
        register_rule(
            "evidence_anatomy",
            "htt.core.analysis_extended.evidence_matrix_report_artifact",
            lambda *a, **kw: (None, None, None, STATUS_INCOMPARABLE, ""),
        )


# ─── Summary bookkeeping ──────────────────────────────────────────────
def test_summary_counts_match_row_statuses():
    certs = [
        _evidence_anatomy_cert(total_delta_lnB=26.40),    # consistent
        _evidence_anatomy_cert(total_delta_lnB=10.0),     # divergent
        _flrw_tension_cert(ppp_alarm=True),               # depends on bundle
    ]
    tbl = build_cross_check_table(certs, _bundle(Pi_median=0.20), tolerance=0.05)
    assert tbl.summary[STATUS_CONSISTENT] == 2
    assert tbl.summary[STATUS_DIVERGENT] == 1
    assert tbl.summary[STATUS_INCOMPARABLE] == 0
    assert sum(tbl.summary.values()) == len(tbl.rows)
