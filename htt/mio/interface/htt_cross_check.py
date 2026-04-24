"""mio.interface.htt_cross_check — MIO ↔ HTT cross-check table generator (D38).

INDEPENDENT_TRACKS_PLAN v1.2 / BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3
§0.3 deliverable D38 ("HTT ↔ MIO cross-validation table"), §10.2bis G19.

Consumes:
    * a sequence of :class:`workspace.contracts.MioCertificate` instances
      (each already carrying a ``htt_cross_check_suggested`` hint emitted
      by the originating HJ module);
    * a single :class:`workspace.contracts.PosteriorExportBundle`
      (HTT-owned, ``is_cross_check_only=True`` by contract).

Emits a frozen :class:`CrossCheckTable` whose rows pair each certificate
with the scalar it points at on the HTT side, together with a status
label (``consistent`` | ``divergent`` | ``incomparable``). The status
rule is report-type-specific and is looked up via ``_RULE_REGISTRY``.

G19 hard separation (v3 §10.2bis):
  * The table NEVER sums or multiplies an MIO scalar with an HTT scalar.
  * The summary dict aggregates row *counts* only; no merged evidence
    score or combined lnB is produced at any point.
  * Any consumer that tries to coerce a :class:`CrossCheckTable` into a
    single posterior-like number must fail by construction (there is no
    such field).

The existing ``test_g19_no_scalar_sum_of_mio_and_htt`` lint in
``workspace/contracts/tests/test_g19_enforcement.py`` scans MIO code for
forbidden ``MioCertificate…lnB + htt…`` patterns and covers this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

from workspace.contracts.htt_to_mio import PosteriorExportBundle
from workspace.contracts.mio_certificate import MioCertificate


# ─── Row / table contracts ────────────────────────────────────────────
@dataclass(frozen=True)
class CrossCheckRow:
    """One paired (MIO, HTT) comparison — never a merged scalar."""

    probe_name: str
    channel: str
    report_type: str
    htt_target: str
    expected_relation: str
    mio_value: Optional[float]
    htt_value: Optional[float]
    relative_residual: Optional[float]
    status: str           # 'consistent' | 'divergent' | 'incomparable'
    note: str             # human-readable reason (especially when incomparable)


@dataclass(frozen=True)
class CrossCheckTable:
    """Aggregated (MIO, HTT) comparison. G19: no merged scalar field."""

    rows: Tuple[CrossCheckRow, ...]
    summary: Mapping[str, int]          # {'consistent': n, 'divergent': n, 'incomparable': n}
    tolerance: float                    # fractional tolerance applied to continuous rules
    htt_bundle_model: str         # provenance of the HTT bundle consumed


# ─── Status constants ─────────────────────────────────────────────────
STATUS_CONSISTENT   = "consistent"
STATUS_DIVERGENT    = "divergent"
STATUS_INCOMPARABLE = "incomparable"
_STATUS_LABELS = (STATUS_CONSISTENT, STATUS_DIVERGENT, STATUS_INCOMPARABLE)


# ─── Rule callable signature ──────────────────────────────────────────
# (cert, bundle, tolerance) → (mio_value, htt_value, relative_residual, status, note)
_RuleResult = Tuple[Optional[float], Optional[float], Optional[float], str, str]
_Rule = Callable[[MioCertificate, PosteriorExportBundle, float], _RuleResult]


def _relative_residual(mio: float, htt: float) -> float:
    """|mio - htt| / max(|htt|, 1e-12). Never combines MIO and HTT into a score."""
    denom = abs(htt) if abs(htt) > 1e-12 else 1e-12
    return abs(mio - htt) / denom


def _rule_evidence_anatomy(
    cert: MioCertificate,
    bundle: PosteriorExportBundle,
    tolerance: float,
) -> _RuleResult:
    """Evidence anatomy: reconstructed Δln B from MIO channel sum vs HTT total.

    Emitted by ``mio.decomposition.evidence_anatomy.to_mio_certificate``.
    The MIO certificate's ``departure_variables`` carries a
    ``total_delta_lnB`` produced by summing channel-level contributions;
    the HTT side exposes ``ln_B_total`` on the export bundle.

    A disagreement beyond ``tolerance`` (fractional) is flagged
    ``divergent`` — the channel decomposition failed the sum rule against
    the HTT posterior's total evidence.
    """
    mio_total = cert.departure_variables.get("total_delta_lnB")
    htt_total = float(bundle.ln_B_total)
    if mio_total is None:
        return (
            None,
            htt_total,
            None,
            STATUS_INCOMPARABLE,
            "MIO certificate missing 'total_delta_lnB'",
        )
    mio_total = float(mio_total)
    rel = _relative_residual(mio_total, htt_total)
    status = STATUS_CONSISTENT if rel <= tolerance else STATUS_DIVERGENT
    note = (
        f"rel. residual {rel:.3g} vs tol {tolerance:.3g}"
        if status == STATUS_CONSISTENT
        else f"channel sum rule fails: rel. residual {rel:.3g} > tol {tolerance:.3g}"
    )
    return (mio_total, htt_total, rel, status, note)


def _rule_flrw_tension(
    cert: MioCertificate,
    bundle: PosteriorExportBundle,
    tolerance: float,
) -> _RuleResult:
    """FLRW tension: MIO PPP alarm vs HTT Π exceedance alarm (sign comparison).

    Emitted by ``mio.tension.flrw_tension.to_mio_certificate``. The MIO
    certificate carries a corrected PPP p-value with a boolean alarm
    ``ppp_corrected_p_lt_0p05``; the HTT bundle carries the Layer-3
    exceedance posterior median ``Pi_median``. We compare the *signs* of
    the two alarms (``mio_alarm`` vs ``htt_alarm = Pi_median > tolerance``)
    and declare the comparison ``divergent`` if they disagree.

    No scalars are combined — both are projected to booleans first.
    """
    mio_alarm = cert.adequacy_indicators.get("ppp_corrected_p_lt_0p05")
    if mio_alarm is None:
        return (
            None,
            float(bundle.Pi_median),
            None,
            STATUS_INCOMPARABLE,
            "MIO certificate missing 'ppp_corrected_p_lt_0p05' indicator",
        )
    mio_alarm = bool(mio_alarm)
    htt_alarm = float(bundle.Pi_median) > tolerance
    status = STATUS_CONSISTENT if mio_alarm == htt_alarm else STATUS_DIVERGENT
    note = (
        f"alarms agree: mio={mio_alarm}, htt(Pi>{tolerance:.3g})={htt_alarm}"
        if status == STATUS_CONSISTENT
        else f"alarm sign disagreement: mio={mio_alarm} vs htt={htt_alarm}"
    )
    mio_pval = cert.departure_variables.get("min_corrected_ppp_pvalue")
    return (
        float(mio_pval) if mio_pval is not None else None,
        float(bundle.Pi_median),
        None,
        status,
        note,
    )


_RULE_REGISTRY: Dict[Tuple[str, str], _Rule] = {
    (
        "evidence_anatomy",
        "htt.core.analysis_extended.evidence_matrix_report_artifact",
    ): _rule_evidence_anatomy,
    (
        "flrw_tension",
        "htt.core.advanced_diagnostics.posterior_predictive_report_artifact",
    ): _rule_flrw_tension,
}


def register_rule(
    report_type: str,
    compare_to: str,
    rule: _Rule,
    *,
    overwrite: bool = False,
) -> None:
    """Register a new cross-check rule for a (report_type, compare_to) pair.

    Exposed so downstream HJ modules can ship their own extraction rules
    without editing this file. ``overwrite=False`` (the default) refuses
    to replace an existing registration to keep rule ownership clear.
    """
    key = (report_type, compare_to)
    if key in _RULE_REGISTRY and not overwrite:
        raise ValueError(
            f"Rule already registered for {key}. Pass overwrite=True to replace."
        )
    _RULE_REGISTRY[key] = rule


def _build_row(
    cert: MioCertificate,
    bundle: PosteriorExportBundle,
    tolerance: float,
) -> CrossCheckRow:
    hint = cert.htt_cross_check_suggested or {}
    htt_target = hint.get("compare_to", "")
    expected_relation = hint.get("expected_relation", "")

    rule = _RULE_REGISTRY.get((cert.report_type, htt_target))
    if rule is None:
        return CrossCheckRow(
            probe_name=cert.probe_name,
            channel=cert.channel,
            report_type=cert.report_type,
            htt_target=htt_target,
            expected_relation=expected_relation,
            mio_value=None,
            htt_value=None,
            relative_residual=None,
            status=STATUS_INCOMPARABLE,
            note=(
                "no rule registered for "
                f"(report_type={cert.report_type!r}, compare_to={htt_target!r})"
            ),
        )

    mio_val, htt_val, rel, status, note = rule(cert, bundle, tolerance)
    return CrossCheckRow(
        probe_name=cert.probe_name,
        channel=cert.channel,
        report_type=cert.report_type,
        htt_target=htt_target,
        expected_relation=expected_relation,
        mio_value=mio_val,
        htt_value=htt_val,
        relative_residual=rel,
        status=status,
        note=note,
    )


def build_cross_check_table(
    certificates: Sequence[MioCertificate],
    posterior_bundle: PosteriorExportBundle,
    *,
    tolerance: float = 0.1,
) -> CrossCheckTable:
    """Pair each MIO certificate with its suggested HTT scalar.

    Parameters
    ----------
    certificates
        MIO-owned diagnostic reports. Each must carry a populated
        ``htt_cross_check_suggested`` hint (rows without a hint land as
        ``incomparable``).
    posterior_bundle
        HTT-owned cross-check export bundle. Its ``is_cross_check_only``
        flag is enforced by the dataclass itself; this function does not
        merge any of its scalars with MIO fields (G19).
    tolerance
        Fractional tolerance for continuous rules (e.g. ``evidence_anatomy``
        sum rule) and the Pi-exceedance alarm threshold used in
        ``flrw_tension``.

    Returns
    -------
    CrossCheckTable
        Immutable. Consumers iterate ``rows`` and read ``summary`` for
        counts — no merged scalar exists at any layer.
    """
    if not isinstance(posterior_bundle, PosteriorExportBundle):
        raise TypeError(
            "build_cross_check_table requires a PosteriorExportBundle; "
            f"got {type(posterior_bundle).__name__}. MIO does not synthesize "
            "posterior bundles (v3 G19)."
        )
    if tolerance < 0:
        raise ValueError(f"tolerance must be non-negative, got {tolerance!r}")

    rows = tuple(_build_row(c, posterior_bundle, tolerance) for c in certificates)
    summary = {label: 0 for label in _STATUS_LABELS}
    for row in rows:
        summary[row.status] = summary.get(row.status, 0) + 1

    return CrossCheckTable(
        rows=rows,
        summary=dict(summary),
        tolerance=float(tolerance),
        htt_bundle_model=str(posterior_bundle.model),
    )


def table_to_payload(table: CrossCheckTable) -> Dict[str, object]:
    """JSON-ready payload of ``CrossCheckTable``. No merged scalars."""
    return {
        "rows": [
            {
                "probe_name": r.probe_name,
                "channel": r.channel,
                "report_type": r.report_type,
                "htt_target": r.htt_target,
                "expected_relation": r.expected_relation,
                "mio_value": r.mio_value,
                "htt_value": r.htt_value,
                "relative_residual": r.relative_residual,
                "status": r.status,
                "note": r.note,
            }
            for r in table.rows
        ],
        "summary": dict(table.summary),
        "tolerance": table.tolerance,
        "htt_bundle_model": table.htt_bundle_model,
    }


__all__ = [
    "CrossCheckRow",
    "CrossCheckTable",
    "STATUS_CONSISTENT",
    "STATUS_DIVERGENT",
    "STATUS_INCOMPARABLE",
    "build_cross_check_table",
    "register_rule",
    "table_to_payload",
]
