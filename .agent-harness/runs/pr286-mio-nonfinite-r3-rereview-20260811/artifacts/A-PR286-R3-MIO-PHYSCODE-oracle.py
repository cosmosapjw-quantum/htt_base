#!/usr/bin/env python3
"""Blind executable oracle for the frozen PR-286 MIO numerical repair."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields
import importlib.util
import json
import math
from pathlib import Path
from numbers import Real
import sys

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "htt" / "src"), str(ROOT / "htt")]

import mio.formalism.vector_tensor_validation as mio_surface
from common.vector_tensor_statistical_inference import (
    ModelCandidate,
    PillarSInferenceError,
    ValidationStatus,
    _whitened_design_geometry,
    evaluate_depth_local_global,
    load_preregistered_design,
)


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = load_module(
    "pr286_mio_blind_runner",
    "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
)
builder = load_module(
    "pr286_mio_blind_pr272_builder",
    "scripts/codex_harness/build_pr272_pillar_s_inference.py",
)


def finite_numeric_report(report) -> dict[str, float]:
    numeric_names = (
        "local_residual_norm",
        "global_residual_norm",
        "residual_norm_difference_global_minus_local",
    )
    declared = {item.name for item in fields(report)}
    assert set(numeric_names) <= declared
    values = {name: getattr(report, name) for name in numeric_names}
    assert all(
        isinstance(value, Real)
        and not isinstance(value, (bool, np.bool_))
        and math.isfinite(float(value))
        for value in values.values()
    )
    return {key: float(value) for key, value in values.items()}


def typed_mio_refusal(name: str, *, data, local, global_) -> str:
    assert np.all(np.isfinite(np.asarray(data, dtype=float)))
    assert np.all(np.isfinite(np.asarray(local, dtype=float)))
    assert np.all(np.isfinite(np.asarray(global_, dtype=float)))
    try:
        report = mio_surface.build_mio_depth_cross_check(
            data,
            local_design=local,
            global_design=global_,
            mask_path_id=f"blind-{name}",
        )
    except PillarSInferenceError as exc:
        return str(exc)
    finite_numeric_report(report)
    raise AssertionError(f"{name} unexpectedly returned a positive report")


def typed_htt_refusal(name: str, **kwargs) -> str:
    try:
        evaluate_depth_local_global(**kwargs)
    except PillarSInferenceError as exc:
        return str(exc)
    raise AssertionError(f"{name} unexpectedly returned a positive report")


def main() -> None:
    evidence: dict[str, object] = {}

    # The MIO facade exports one diagnostic builder, its diagnostic record, and
    # typed status/error support. It exposes no HTT likelihood or x/Q/Pi/F/G API.
    assert set(mio_surface.__all__) == {
        "MioDepthDiagnosticCrossCheck",
        "PillarSInferenceError",
        "ValidationStatus",
        "build_mio_depth_cross_check",
    }
    assert not any(
        hasattr(mio_surface, name)
        for name in (
            "evaluate_depth_local_global",
            "HttDepthDiscriminationReport",
            "PosteriorExceedance",
            "build_likelihood_objective",
            "x",
            "Q",
            "Pi",
            "F",
            "G_F",
        )
    )
    evidence["public_mio_facade"] = list(mio_surface.__all__)

    # Exact assigned finite-input counterexample through the exported facade.
    huge_local = np.asarray((1.0e200, 1.0e200))
    huge_global = np.asarray((1.0e200, 1.0e200 + 2.0e185))
    exact_counterexample = typed_mio_refusal(
        "exact-1e200",
        data=huge_local,
        local=huge_local,
        global_=huge_global,
    )
    assert exact_counterexample == "finite MIO diagnostic outputs are required"
    evidence["exact_exported_1e200_counterexample"] = exact_counterexample

    # Distinct finite-input routes exercise scale overflow, projection overflow,
    # residual-norm overflow, and tiny-design underflow. None may return a
    # dataclass containing a NaN/Inf positive diagnostic.
    refusal_cases = {
        "design_scale_overflow": exact_counterexample,
        "projection_overflow": typed_mio_refusal(
            "projection-overflow",
            data=np.asarray((1.0e308, 1.0e308)),
            local=np.asarray((2.0, 1.0)),
            global_=np.asarray((1.0, 2.0)),
        ),
        "residual_norm_overflow": typed_mio_refusal(
            "residual-norm-overflow",
            data=np.asarray((1.0e308, 1.0e308)),
            local=np.asarray((1.0, 0.0)),
            global_=np.asarray((0.0, 1.0)),
        ),
        "tiny_design_underflow": typed_mio_refusal(
            "tiny-design-underflow",
            data=np.asarray((0.0, 0.0)),
            local=np.asarray((1.0e-300, 1.0e-300)),
            global_=np.asarray((1.0, 0.0)),
        ),
    }
    assert all(isinstance(value, str) and value for value in refusal_cases.values())
    evidence["finite_input_nonfinite_routes"] = refusal_cases

    # One-ULP upper boundary around overflow of [s,s]@[s,s]. The last finite
    # scale returns three finite zero diagnostics; the next float fails closed.
    boundary = math.sqrt(np.finfo(float).max / 2.0)
    below = np.nextafter(boundary, 0.0)
    above = np.nextafter(boundary, np.inf)
    boundary_reports = {}
    for label, scale in (("below", below), ("at", boundary)):
        design = np.asarray((scale, scale))
        report = mio_surface.build_mio_depth_cross_check(
            np.zeros(2),
            local_design=design,
            global_design=design,
            mask_path_id="blind-one-ulp-boundary",
        )
        boundary_reports[label] = finite_numeric_report(report)
    boundary_refusal = typed_mio_refusal(
        "one-ulp-above-overflow-boundary",
        data=np.zeros(2),
        local=np.asarray((above, above)),
        global_=np.asarray((above, above)),
    )
    assert boundary_refusal == "finite MIO diagnostic outputs are required"
    evidence["one_ulp_boundary"] = {
        "below": float(below),
        "at": float(boundary),
        "above": float(above),
        "positive_reports": boundary_reports,
        "above_refusal": boundary_refusal,
    }

    # All successful adjacent scale probes must expose only finite numerics.
    scale_sweep = {}
    base_local = np.asarray((0.25, 0.5, 0.75, 1.0))
    base_global = np.ones(4)
    for exponent in (-150, -100, -50, 0, 50, 100, 150):
        scale = 10.0**exponent
        local = scale * base_local
        global_ = scale * base_global
        data = 0.5 * local + 0.1 * global_
        report = mio_surface.build_mio_depth_cross_check(
            data,
            local_design=local,
            global_design=global_,
            mask_path_id="blind-scale-sweep",
        )
        scale_sweep[str(exponent)] = finite_numeric_report(report)
    evidence["successful_scale_sweep"] = scale_sweep

    # Replay the ordinary frozen PR-272 MIO results from the original generator
    # and compare exact JSON values, not approximate hand-derived substitutes.
    registry = yaml.safe_load(
        (ROOT / "docs/research_program/vector_tensor/proofs/"
         "PILLAR_S_INFERENCE_VALIDATION_V1.yaml").read_text(encoding="utf-8")
    )
    design = load_preregistered_design(ROOT)
    master_seed = int(design["preregistration"]["random_stream"]["master_seed"])
    rebuilt_s14 = builder._build_s14(design, master_seed)
    frozen_s14 = registry["validation_results"]["VT-S14"]
    for key in (
        "MIO_local_diagnostic_cross_check",
        "MIO_global_diagnostic_cross_check",
    ):
        assert rebuilt_s14[key] == frozen_s14[key]
        finite_numeric_report(
            mio_surface.MioDepthDiagnosticCrossCheck(
                **{
                    field.name: (
                        ValidationStatus(frozen_s14[key][field.name])
                        if field.name == "status"
                        else frozen_s14[key][field.name]
                    )
                    for field in fields(mio_surface.MioDepthDiagnosticCrossCheck)
                }
            )
        )
    evidence["ordinary_registered_mio_exact_replay"] = {
        key: frozen_s14[key]
        for key in (
            "MIO_local_diagnostic_cross_check",
            "MIO_global_diagnostic_cross_check",
        )
    }

    # Recheck the adjacent HTT numerical and identification controls.
    registered_htt = evaluate_depth_local_global(
        4.0 * base_local,
        covariance=np.eye(4),
        covariance_id="blind-ordinary-identity",
        local_design=base_local,
        global_design=base_global,
        mask_path_id="blind-nested-mask",
        transfer_source="none",
    )
    assert registered_htt.likelihood_owner == "HTT"
    assert registered_htt.selected_candidate is ModelCandidate.LOCAL
    assert all(
        math.isfinite(value)
        for value in (
            registered_htt.local_chi_square,
            registered_htt.global_chi_square,
            registered_htt.chi_square_difference_global_minus_local,
            registered_htt.local_amplitude,
            registered_htt.global_amplitude,
        )
    )
    large_gls = typed_htt_refusal(
        "large-gls",
        data=huge_local,
        covariance=np.eye(2),
        covariance_id="identity",
        local_design=huge_local,
        global_design=huge_global,
        mask_path_id="blind-nested-mask",
        transfer_source="none",
        principal_angle_floor_radians=1.0e-12,
    )
    extreme_spd = typed_htt_refusal(
        "extreme-spd",
        data=base_local,
        covariance=np.diag((1.0e-320, 1.0, 2.0, 3.0)),
        covariance_id="extreme-spd",
        local_design=base_local,
        global_design=base_global,
        mask_path_id="blind-nested-mask",
        transfer_source="none",
    )
    zero_design = typed_htt_refusal(
        "zero-design",
        data=np.zeros(2),
        covariance=np.eye(2),
        covariance_id="identity",
        local_design=np.zeros(2),
        global_design=np.asarray((1.0, 0.0)),
        mask_path_id="blind-nested-mask",
        transfer_source="none",
    )
    assert "finite GLS" in large_gls and "finite GLS" in extreme_spd
    assert "design must be nonzero" in zero_design

    rank_probe = evaluate_depth_local_global(
        np.asarray((1.0, 0.0)),
        covariance=np.diag((1.0, 1.0e-32)),
        covariance_id="blind-whitened-rank",
        local_design=np.asarray((1.0, 0.0)),
        global_design=np.asarray((1.0, 1.0e-16)),
        mask_path_id="blind-nested-mask",
        transfer_source="none",
    )
    assert rank_probe.status is ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    assert rank_probe.selected_candidate is ModelCandidate.LOCAL

    proportional = evaluate_depth_local_global(
        base_local,
        covariance=np.eye(4),
        covariance_id="identity",
        local_design=base_local,
        global_design=2.0 * base_local,
        mask_path_id="blind-nested-mask",
        transfer_source="none",
    )
    assert proportional.status is ValidationStatus.ABSTAIN_NON_IDENTIFIED
    assert proportional.selected_candidate is ModelCandidate.INDETERMINATE

    angles = {}
    expected_angle = 0.3
    local_direction = np.asarray((1.0, 0.0))
    global_direction = np.asarray((math.cos(expected_angle), math.sin(expected_angle)))
    for exponent in (-300, -200, -100, 0, 100, 200, 300):
        scale = 10.0**exponent
        rank, angle = _whitened_design_geometry(
            np.eye(2), scale * local_direction, scale * global_direction
        )
        assert rank == 2
        assert math.isclose(angle, expected_angle, rel_tol=0.0, abs_tol=5.0e-15)
        angles[str(exponent)] = angle
    evidence["htt_adjacent_controls"] = {
        "ordinary_selected": registered_htt.selected_candidate.value,
        "large_scale_gls": large_gls,
        "extreme_spd_gls": extreme_spd,
        "zero_design": zero_design,
        "whitened_rank_selected": rank_probe.selected_candidate.value,
        "proportional_status": proportional.status.value,
        "scale_stable_angles": angles,
    }

    # Validate the tracked receipt and separately activate the discriminating
    # twentieth mutation. Its kill must be semantic, not merely content-address.
    receipt = json.loads(
        (ROOT / "docs/research_program/post_pr275/pillar_s_adjudication/"
         "PILLAR_S_COMPLETE_ADJUDICATION_V1.json").read_text(encoding="utf-8")
    )
    runner.validate_complete_adjudication_receipt(receipt)
    assert len(receipt["rows"]) == 72
    assert len(receipt["mutation_registry"]) == 20
    assert len(receipt["mutation_results"]) == 20
    twentieth = receipt["mutation_registry"][19]
    twentieth_result = receipt["mutation_results"][19]
    assert twentieth["mutation_id"] == "MU286-VTS14-MIO-NUMERIC-GUARD-DRIFT"
    assert twentieth_result["mutation_id"] == twentieth["mutation_id"]
    assert twentieth_result["executed"] is True
    assert twentieth_result["activated"] is True
    assert twentieth_result["killed"] is True
    assert twentieth_result["survivor"] is False
    assert twentieth_result["kill_marker"] == "SEMANTIC_TYPE_DRIFT"
    mutated = runner.apply_registered_mutation(deepcopy(receipt), twentieth["mutation_id"])
    try:
        runner.validate_complete_adjudication_receipt(mutated)
    except runner.PillarSAdjudicationError as exc:
        assert str(exc) == "SEMANTIC_TYPE_DRIFT"
    else:
        raise AssertionError("twentieth mutation survived independent replay")
    evidence["receipt_and_twentieth_mutation"] = {
        "row_count": len(receipt["rows"]),
        "mutation_count": len(receipt["mutation_registry"]),
        "twentieth": twentieth_result,
    }

    # Ownership, likelihood semantics, semantic typing, and claim ceilings.
    metadata = receipt["metadata"]
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert metadata["transfer_source"] == "none"
    assert metadata["observed_data_executed"] is False
    assert metadata["public_use"] is False
    assert metadata["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert receipt["ownership"]["HTT"].startswith("model-dependent")
    assert receipt["ownership"]["MIO"].startswith("diagnostic residual")
    assert receipt["mio_forbidden_outputs"] == [
        "likelihood", "posterior", "Bayes_factor", "evidence"
    ]
    assert all(row["claim_ceiling"] == "diagnostic_only" for row in receipt["rows"])
    vts14 = next(row for row in receipt["rows"] if row["row_id"] == "VT-S14")
    assert vts14["prior_applicability_and_identity"] == (
        "NOT_APPLICABLE_NO_PRIOR_IN_REGISTERED_ROW"
    )
    assert vts14["units_normalization_and_frame"] == {
        "status": "DIMENSIONLESS_GLS_CHI_SQUARE",
        "normalization": "registered_depth_covariance",
        "frame": "HTT_LOCAL_GLOBAL_DESIGN_PAIR",
    }
    assert vts14["sign_orientation_convention"] == (
        "CHI_SQUARE_AND_RESIDUAL_DIFFERENCE_GLOBAL_MINUS_LOCAL"
    )
    assert vts14["rank_and_identification_scope"]["rank_metric"] == (
        "COLUMN_NORMALIZED_COVARIANCE_WHITENED_DESIGN"
    )
    assert vts14["rank_and_identification_scope"]["global_orbit_separation_claimed"] is False
    assert vts14["verdict"] == "BLOCKED_WITH_RECEIPT"
    assert vts14["source_status_effect"] == "RETAIN_PROGRAM_OBLIGATION"
    evidence["semantic_and_claim_firewalls"] = {
        "units": vts14["units_normalization_and_frame"],
        "sign": vts14["sign_orientation_convention"],
        "prior": vts14["prior_applicability_and_identity"],
        "rank_scope": vts14["rank_and_identification_scope"],
        "mio_forbidden_outputs": receipt["mio_forbidden_outputs"],
        "x_q_pi_f_g_status": "NOT_EMITTED_BY_THIS_FACADE_OR_RECEIPT_LANE",
        "claim_tier": metadata["claim_tier"],
        "claim_level_scheme": metadata["claim_level"],
        "family_gate": metadata["family_identification_gate"],
        "vts14_verdict": vts14["verdict"],
    }

    print(json.dumps({"status": "PASS", "evidence": evidence}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
