from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from common.transfer_registry import TransferFunctionSpec, TransferValidRange
from mio.formalism.budget_spec import BudgetPolicy, BudgetSpec, BudgetUse
from mio.formalism.departure_bundle import build_departure_bundle
from mio.formalism.exceedance import MeasureKind, build_exceedance_curve
from mio.formalism.filling_fraction import build_certified_filling_fraction
from mio.formalism.isotropy_gap import (
    DepthBinMetadata,
    build_depth_bin_f_record,
    build_isotropy_gap,
)
from mio.formalism.normalized_score import build_normalized_score


_REPORT_COMMAND = "python -m pytest tests/mio/test_departure_report.py -q"
_WORKTREE_STATE = "test-worktree"


def _transfer_metadata(transfer_id: str) -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(k_min=1.0e-5, k_max=0.2, ell_min=2, ell_max=30),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    return spec.to_metadata()


def _bundle(
    x_c: float = 0.2,
    *,
    transfer_source: str = "none",
    transfer_spec_id: str | None = None,
    transfer_metadata: dict[str, object] | None = None,
):
    return build_departure_bundle(
        components={
            "Sigma2_std": x_c,
            "W2_std": 0.0,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        config_hash=f"cfg-x-{x_c}",
        input_hashes=(f"bundle-input-{x_c}",),
        transfer_source=transfer_source,
        transfer_spec_id=transfer_spec_id,
        transfer_metadata=transfer_metadata,
    )


def _q_budget() -> BudgetSpec:
    return BudgetSpec(
        policy=BudgetPolicy.MES_LINEAR,
        denominator_value=0.5,
        denominator_label="linear MES reference denominator",
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
        ),
        assumptions=("linear MES denominator for score normalization",),
        config_hash="q-budget-config",
        input_hashes=("q-budget-input",),
        sky_support_status="fixture full sky",
        caveats=("diagnostic budget fixture",),
        is_admissible_ceiling=False,
    )


def _f_budget() -> BudgetSpec:
    return BudgetSpec(
        policy=BudgetPolicy.MES_LINEAR,
        denominator_value=1.0,
        denominator_label="linear MES certified filling ceiling",
        comparator="CMB_FLRW_reference",
        frame="normal_frame",
        units="dimensionless_hubble_normalized",
        admissible_uses=(
            BudgetUse.DENOMINATOR_SENSITIVITY,
            BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
            BudgetUse.CERTIFIED_FILLING_CEILING,
            BudgetUse.EXCEEDANCE_THRESHOLD,
            BudgetUse.DEPTH_GAP_REFERENCE,
        ),
        assumptions=("linear MES ceiling for filling-fraction diagnostics",),
        config_hash="f-budget-config",
        input_hashes=("f-budget-input",),
        sky_support_status="fixture full sky",
        null_mock_status="synthetic fixture only",
        caveats=("diagnostic ceiling fixture",),
        is_admissible_ceiling=True,
    )


def _q_score(bundle=None):
    return build_normalized_score(
        bundle or _bundle(),
        _q_budget(),
        numerator_policy="signed",
    )


def _pi_curve():
    return build_exceedance_curve(
        sample_values=(0.1, 0.3, 0.6),
        thresholds=(0.0, 0.2, 0.5),
        source_score_label="Q",
        measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
        input_hashes=("pi-input",),
        config_hash="pi-config",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


def _f_score(scores=(0.1, 0.3, 0.6)):
    return build_certified_filling_fraction(
        departure_bundles=tuple(_bundle(float(score)) for score in scores),
        budget_specs=tuple(_f_budget() for _ in scores),
        input_hashes=("f-input",),
        config_hash="f-config",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


def _depth_bin(label: str, z_min: float, z_max: float) -> DepthBinMetadata:
    return DepthBinMetadata(
        bin_id=label,
        depth_min=z_min,
        depth_max=z_max,
        depth_unit="redshift",
        depth_convention="z_cmb_bin_edges_left_closed_right_open",
        selection_rule="pre-registered redshift bin assignment",
        selection_hash=f"sha256:selection-{label}",
        bin_assignment_hash=f"sha256:assignment-{label}",
        sky_support_status="mask_weighted_directional_support",
        mask_status="masked_with_hash",
        covariance_status="mock_covariance",
        covariance_metadata={
            "covariance_hash": f"sha256:cov-{label}",
            "shape": [2, 2],
            "estimator": "mock_bank",
            "calibration_status": "matched_calibrated",
        },
        null_mock_status="mock_calibrated",
        null_metadata={
            "mock_bank_hash": f"sha256:null-{label}",
            "calibration_status": "matched_calibrated",
        },
        denominator_evolution_status="per_bin_denominator_recorded",
        sample_count=3,
    )


def _record(label: str, z_min: float, z_max: float, scores=(0.1, 0.3, 0.6)):
    return build_depth_bin_f_record(
        _f_score(scores=scores),
        depth_bin=_depth_bin(label, z_min, z_max),
    )


def _g_gap():
    return build_isotropy_gap(
        depth_bin_records=(
            _record("near", 0.0, 0.1, scores=(0.1, 0.2, 0.3)),
            _record("far", 0.1, 0.2, scores=(0.4, 0.5, 0.6)),
        ),
        reference_bin_id="near",
        comparison_bin_id="far",
        floor_value=1.0e-3,
        floor_label="pre_registered_positive_F_floor",
        floor_reason="stabilize log_g_F without altering raw F values",
        input_hashes=("g-input",),
        config_hash="g-config",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


def _full_report():
    from mio.reports.departure_report import build_departure_report

    bundle = _bundle()
    return build_departure_report(
        departure_bundle=bundle,
        normalized_score=_q_score(bundle),
        exceedance_curve=_pi_curve(),
        filling_fraction=_f_score(),
        isotropy_gap=_g_gap(),
        artifact_id="mio-report-fixture",
        artifact_path="memory://mio-report-fixture.json",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )


class _PayloadWrapper:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = dict(payload)

    def as_payload(self) -> dict[str, object]:
        return dict(self._payload)


def test_departure_report_preserves_separate_x_q_pi_f_g_sections():
    report = _full_report()
    payload = report.as_payload()

    assert payload["owner"] == "MIO"
    assert payload["implementation_scope"] == "mio"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["score_order"] == ["x_C", "Q", "Pi", "F", "G_F"]
    assert set(payload["sections"]) == {"x_C", "Q", "Pi", "F", "G_F"}
    assert payload["sections"]["x_C"]["status"] == "available"
    assert payload["sections"]["Q"]["payload"]["score_kind"] == "policy_normalized_score"
    assert payload["sections"]["Pi"]["payload"]["score_kind"] == "exceedance_curve"
    assert payload["sections"]["F"]["payload"]["score_kind"] == "certified_filling_fraction"
    assert payload["sections"]["G_F"]["payload"]["score_kind"] == "isotropy_depth_gap"
    assert payload["f_status"]["status"] == "available"
    assert payload["f_status"]["sample_count"] == 3
    assert payload["g_status"]["status"] == "available"
    assert payload["g_status"]["depth_bin_count"] == 2
    assert "headline_score" not in payload
    assert "combined_score" not in payload
    assert "combined_mio_htt_score" not in payload
    assert payload["manifest"]["owner"] == "MIO"
    assert payload["manifest"]["implementation_scope"] == "mio"
    assert payload["manifest"]["claim_tier"] == "diagnostic_only"
    assert payload["manifest"]["config_hash"] == payload["config_hash"]
    assert "bundle-input-0.2" in payload["input_hashes"]
    assert "f-input" in payload["input_hashes"]


def test_report_marks_missing_f_and_g_with_explicit_status_not_zero():
    from mio.reports.departure_report import build_departure_report

    bundle = _bundle()
    payload = build_departure_report(
        departure_bundle=bundle,
        normalized_score=_q_score(bundle),
        artifact_id="mio-report-minimal",
        artifact_path="memory://mio-report-minimal.json",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    assert payload["sections"]["F"]["status"] == "not_provided"
    assert payload["sections"]["F"]["payload"] is None
    assert payload["sections"]["G_F"]["status"] == "not_provided"
    assert payload["sections"]["G_F"]["payload"] is None
    assert payload["f_status"] == {"status": "not_provided", "reason": "not_supplied"}
    assert payload["g_status"] == {"status": "not_provided", "reason": "not_supplied"}


def test_report_preserves_external_transfer_provenance_without_native_label():
    from mio.reports.departure_report import build_departure_report

    metadata = _transfer_metadata("aniclass.report.x.v1")
    bundle = _bundle(
        transfer_source="AniCLASS_external",
        transfer_spec_id="aniclass.report.x.v1",
        transfer_metadata=metadata,
    )
    payload = build_departure_report(
        departure_bundle=bundle,
        normalized_score=_q_score(bundle),
        artifact_id="mio-report-transfer",
        artifact_path="memory://mio-report-transfer.json",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    ).as_payload()

    transfer = payload["transfer_provenance_by_section"]["x_C"]
    assert transfer["transfer_source"] == "AniCLASS_external"
    assert transfer["transfer_spec_id"] == "aniclass.report.x.v1"
    assert transfer["transfer_metadata"]["transfer_id"] == "aniclass.report.x.v1"
    payload_text = json.dumps(payload, sort_keys=True).lower()
    assert ("native_" + "validated") not in payload_text
    assert ("native " + "solver result") not in payload_text


def test_report_sections_are_immutable_and_payloads_are_detached():
    report = _full_report()
    section = report.sections["x_C"]

    with pytest.raises(TypeError):
        section.payload["headline_score"] = 0.99
    with pytest.raises(TypeError):
        section.transfer_provenance["transfer_source"] = "forged_source"
    with pytest.raises(TypeError):
        report.artifact_metadata["headline_score"] = 0.99

    payload = report.as_payload()
    payload["sections"]["x_C"]["payload"]["display_metadata"][
        "headline_score"
    ] = 0.99
    payload["transfer_provenance_by_section"]["x_C"][
        "transfer_source"
    ] = "payload_only"
    payload["artifact_metadata"]["headline_score"] = 0.99

    fresh = report.as_payload()
    assert "headline_score" not in fresh["sections"]["x_C"]["payload"][
        "display_metadata"
    ]
    assert fresh["transfer_provenance_by_section"]["x_C"][
        "transfer_source"
    ] == "none"
    assert "headline_score" not in fresh["artifact_metadata"]


def test_report_rejects_combined_or_inference_fields():
    from mio.reports.departure_report import build_departure_report

    bundle = _bundle()
    kwargs = dict(
        departure_bundle=bundle,
        normalized_score=_q_score(bundle),
        artifact_id="mio-report-bad",
        artifact_path="memory://mio-report-bad.json",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    with pytest.raises(ValueError, match="headline"):
        build_departure_report(**kwargs, artifact_metadata={"headline_score": 1.0})
    with pytest.raises(ValueError, match="posterior"):
        build_departure_report(**kwargs, artifact_metadata={"post" + "erior_odds": 2.0})
    with pytest.raises(ValueError, match="geometry"):
        build_departure_report(**kwargs, caveats=("geo" + "metry label",))

    variant_keys = (
        "post" + "erior_probability",
        "family" + "_ranking",
        "geo" + "metry_family_candidate",
        "native" + "_solver_label",
        "combined_report_score",
    )
    for key in variant_keys:
        with pytest.raises(ValueError, match="reserved|headline"):
            build_departure_report(**kwargs, artifact_metadata={key: "bad"})


def test_report_rejects_reserved_fields_inside_section_payloads():
    from mio.reports.departure_report import build_departure_report

    base = _bundle().as_payload()
    kwargs = dict(
        artifact_id="mio-report-section-bad",
        artifact_path="memory://mio-report-section-bad.json",
        generating_command=_REPORT_COMMAND,
        worktree_state=_WORKTREE_STATE,
    )

    for key in (
        "headline_score",
        "post" + "erior_odds",
        "geo" + "metry_label",
        "native" + "_solver_label",
    ):
        payload = dict(base)
        payload[key] = 1.0
        with pytest.raises(ValueError, match="reserved|headline"):
            build_departure_report(departure_bundle=_PayloadWrapper(payload), **kwargs)

    payload = dict(base)
    payload["artifact_metadata"] = {"caption": "native " + "solver result"}
    with pytest.raises(ValueError, match="reserved"):
        build_departure_report(departure_bundle=_PayloadWrapper(payload), **kwargs)


def test_report_requires_q_to_match_x_departure_bundle():
    from mio.reports.departure_report import build_departure_report

    with pytest.raises(ValueError, match="Q departure"):
        build_departure_report(
            departure_bundle=_bundle(x_c=0.2),
            normalized_score=_q_score(_bundle(x_c=0.4)),
            artifact_id="mio-report-mismatch",
            artifact_path="memory://mio-report-mismatch.json",
            generating_command=_REPORT_COMMAND,
            worktree_state=_WORKTREE_STATE,
        )


def test_report_exports_and_avoids_htt_inference_imports():
    from mio.reports import DepartureReport
    from mio.reports.departure_report import build_departure_report

    assert DepartureReport.__name__ == "DepartureReport"
    assert callable(build_departure_report)

    source = Path("htt/mio/reports/departure_report.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = ("htt.htt", "htt.infer", "htt.likelihood", "mio.interface.mio_certificate")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith(forbidden_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert not node.module.startswith(forbidden_roots)
