"""PR-266 typed depth, mask, transport, coherence, and likelihood contracts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from common.depth_path import (
    DEPTH_PATH_CLAIM_CEILING,
    CoherenceCellStatus,
    DepthCoherenceStatus,
    DepthPathError,
    ScrambleControlStatus,
    apply_covariance_transport,
    apply_transport,
    build_depth_coherence_report,
    build_depth_path,
    build_depth_scramble_control,
    build_mask_stratum,
    build_observable_feature_step,
    build_transport_kernel,
    compose_transport_kernels,
    revalidate_depth_path,
)
from common.sky_support import build_sky_support_from_mask
from htt.infer.depth_path import (
    DepthHypothesisClass,
    build_depth_model_prediction,
    evaluate_depth_path_likelihood,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/vector_tensor/pr266_spec.yaml"
BACKLOG_PATH = ROOT / "docs/codex_handoff/pr_backlog.yaml"


def _stratum(
    suffix: str,
    *,
    depth: float,
    kept: tuple[int, ...],
    support_ids: tuple[str, ...] | None = None,
    covariance_id: str | None = None,
    selection_id: str | None = None,
    coordinate_frame: str = "GALACTIC",
):
    mask = np.zeros(4, dtype=bool)
    mask[list(kept)] = True
    sky_support = build_sky_support_from_mask(
        mask,
        coordinate_frame=coordinate_frame,
        completeness_status="fixture_complete",
        selection_mode=f"selection-{suffix}",
        mock_coverage_status="synthetic_fixture",
        pixelization="PR266_UNIT_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"PR266-{suffix}",
        depth_coordinate=depth,
        depth_unit="redshift_proxy",
        support_unit_ids=(
            tuple(f"pixel-{index}" for index in kept)
            if support_ids is None
            else support_ids
        ),
        support_universe_size=4,
        sky_support=sky_support,
        selection_id=selection_id or f"sha256:selection-{suffix}",
        covariance_id=covariance_id or f"sha256:covariance-{suffix}",
        source_artifact_id=f"sha256:source-{suffix}",
        feature_names=("dipole_x", "dipole_y"),
        feature_unit="dimensionless_observable",
        assumptions=("synthetic observer-side fixture",),
    )


def _path():
    strata = (
        _stratum("D1", depth=0.1, kept=(0, 1, 2, 3)),
        _stratum("D2", depth=0.2, kept=(0, 1, 2)),
        _stratum("D3", depth=0.4, kept=(0, 1)),
    )
    first = build_transport_kernel(
        transport_id="PR266-K12",
        source=strata[0],
        target=strata[1],
        matrix=((2.0, 0.0), (0.0, 2.0)),
        mask_transport_id="sha256:mask-k12",
        selection_transport_id="sha256:selection-k12",
        covariance_transport_id="sha256:covariance-k12",
        method_id="PR266-LINEAR-TRANSPORT-V1",
        assumptions=("dimensionless deterministic transport",),
    )
    second = build_transport_kernel(
        transport_id="PR266-K23",
        source=strata[1],
        target=strata[2],
        matrix=((0.5, 0.0), (0.0, 0.5)),
        mask_transport_id="sha256:mask-k23",
        selection_transport_id="sha256:selection-k23",
        covariance_transport_id="sha256:covariance-k23",
        method_id="PR266-LINEAR-TRANSPORT-V1",
        assumptions=("dimensionless deterministic transport",),
    )
    return build_depth_path(
        path_id="PR266-PATH",
        strata=strata,
        kernels=(first, second),
    )


def _steps(path, *, covariance_scale: float = 0.1):
    values = ((1.0, 2.0), (2.0, 4.0), (1.0, 2.0))
    return tuple(
        build_observable_feature_step(
            step_id=f"PR266-STEP-{stratum.stratum_id}",
            stratum=stratum,
            values=value,
            covariance=(
                (covariance_scale, 0.0),
                (0.0, covariance_scale),
            ),
            source_artifact_id=f"sha256:feature-{stratum.stratum_id}",
            extraction_method_id="PR266-SYNTHETIC-FEATURE-V1",
            sample_count=64,
        )
        for stratum, value in zip(path.strata, values, strict=True)
    )


def test_spec_and_backlog_bind_pr266_ownership_and_dependency() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    backlog = yaml.safe_load(BACKLOG_PATH.read_text())
    card = next(value for value in backlog["prs"] if value["id"] == "PR-266")
    assert spec["work_unit_id"] == "PR-266"
    assert spec["dependencies"] == ["PR-264"]
    assert card["depends"] == ["PR-264"]
    assert spec["ownership"] == {
        "OBSSTAT": "feature extraction and typed transport only",
        "MIO": "diagnostic depth coherence and scramble control only",
        "HTT": "explicit model-conditional likelihood adapter only",
        "COMMON": "shared immutable contracts and semantic firewalls",
    }
    assert spec["claim_boundary"]["ceiling"] == "diagnostic_only"


def test_nested_path_round_trip_binds_every_provenance_identity() -> None:
    path = _path()
    replay = revalidate_depth_path(path)
    assert replay.content_id == path.content_id
    payload = path.as_payload()
    assert payload["nesting_rule"] == "TARGET_SUPPORT_SUBSET_OF_SOURCE"
    assert payload["claim_ceiling"] == DEPTH_PATH_CLAIM_CEILING
    assert [value["selection_id"] for value in payload["strata"]] == [
        "sha256:selection-D1",
        "sha256:selection-D2",
        "sha256:selection-D3",
    ]
    assert [value["covariance_id"] for value in payload["strata"]] == [
        "sha256:covariance-D1",
        "sha256:covariance-D2",
        "sha256:covariance-D3",
    ]
    assert all(
        value["sky_support"]["mask_hash"].startswith("sha256:")
        for value in payload["strata"]
    )


def test_non_nested_or_coordinate_incompatible_support_is_refused() -> None:
    source = _stratum("SOURCE", depth=0.1, kept=(0, 1))
    non_nested = _stratum(
        "NONNESTED",
        depth=0.2,
        kept=(0, 2),
    )
    kernel = build_transport_kernel(
        transport_id="PR266-NONNESTED-K",
        source=source,
        target=non_nested,
        matrix=((1.0, 0.0), (0.0, 1.0)),
        mask_transport_id="sha256:mask",
        selection_transport_id="sha256:selection",
        covariance_transport_id="sha256:covariance",
        method_id="PR266-LINEAR",
        assumptions=("negative-control fixture",),
    )
    with pytest.raises(DepthPathError, match="non-nested"):
        build_depth_path(
            path_id="PR266-NONNESTED",
            strata=(source, non_nested),
            kernels=(kernel,),
        )

    other_frame = _stratum(
        "OTHER-FRAME",
        depth=0.2,
        kept=(0,),
        coordinate_frame="ICRS",
    )
    other_kernel = build_transport_kernel(
        transport_id="PR266-OTHER-FRAME-K",
        source=source,
        target=other_frame,
        matrix=((1.0, 0.0), (0.0, 1.0)),
        mask_transport_id="sha256:mask-frame",
        selection_transport_id="sha256:selection-frame",
        covariance_transport_id="sha256:covariance-frame",
        method_id="PR266-LINEAR",
        assumptions=("negative-control fixture",),
    )
    with pytest.raises(DepthPathError, match="coordinate"):
        build_depth_path(
            path_id="PR266-OTHER-FRAME",
            strata=(source, other_frame),
            kernels=(other_kernel,),
        )


def test_transport_composition_matches_sequential_feature_and_covariance_map() -> None:
    path = _path()
    first, second = path.kernels
    composed = compose_transport_kernels(
        transport_id="PR266-K13",
        first=first,
        second=second,
        method_id="PR266-COMPOSED-LINEAR-V1",
        assumptions=("exact matrix composition",),
    )
    values = (1.5, -2.0)
    assert apply_transport(
        second,
        apply_transport(first, values),
    ) == pytest.approx(apply_transport(composed, values))
    covariance = ((0.3, 0.1), (0.1, 0.4))
    sequential = apply_covariance_transport(
        second,
        apply_covariance_transport(first, covariance),
    )
    assert np.asarray(sequential) == pytest.approx(
        np.asarray(apply_covariance_transport(composed, covariance))
    )
    assert np.asarray(composed.matrix) == pytest.approx(np.eye(2))
    assert composed.component_transport_ids == (
        first.content_id,
        second.content_id,
    )


def test_coherence_is_mio_diagnostic_and_changes_with_covariance() -> None:
    path = _path()
    aligned = _steps(path)
    report = build_depth_coherence_report(
        report_id="PR266-COHERENCE",
        path=path,
        steps=aligned,
    )
    assert report.owner == "MIO"
    assert report.status is DepthCoherenceStatus.DEFINED
    assert report.mean_normalized_score == pytest.approx(0.0)
    assert all(
        cell.status is CoherenceCellStatus.DEFINED
        for cell in report.cells
    )

    perturbed = list(aligned)
    perturbed[1] = build_observable_feature_step(
        step_id="PR266-PERTURBED",
        stratum=path.strata[1],
        values=(2.5, 4.0),
        covariance=((0.1, 0.0), (0.0, 0.1)),
        source_artifact_id="sha256:perturbed-feature",
        extraction_method_id="PR266-COVARIANCE-PERTURBATION",
        sample_count=64,
    )
    narrow = build_depth_coherence_report(
        report_id="PR266-NARROW",
        path=path,
        steps=perturbed,
    )
    wide_steps = list(perturbed)
    wide_steps[1] = build_observable_feature_step(
        step_id="PR266-PERTURBED-WIDE",
        stratum=path.strata[1],
        values=(2.5, 4.0),
        covariance=((10.0, 0.0), (0.0, 10.0)),
        source_artifact_id="sha256:perturbed-feature-wide",
        extraction_method_id="PR266-COVARIANCE-PERTURBATION",
        sample_count=64,
    )
    wide = build_depth_coherence_report(
        report_id="PR266-WIDE",
        path=path,
        steps=wide_steps,
    )
    assert narrow.mean_normalized_score > wide.mean_normalized_score


def test_rank_deficient_covariance_returns_no_coherence_number() -> None:
    path = _path()
    steps = tuple(
        build_observable_feature_step(
            step_id=f"PR266-ZERO-COV-{stratum.stratum_id}",
            stratum=stratum,
            values=value,
            covariance=((0.0, 0.0), (0.0, 0.0)),
            source_artifact_id=f"sha256:zero-{stratum.stratum_id}",
            extraction_method_id="PR266-ZERO-COVARIANCE-CONTROL",
            sample_count=8,
        )
        for stratum, value in zip(
            path.strata,
            ((1.0, 2.0), (2.0, 4.0), (1.0, 2.0)),
            strict=True,
        )
    )
    report = build_depth_coherence_report(
        report_id="PR266-RANK-DEFICIENT",
        path=path,
        steps=steps,
    )
    assert report.status is DepthCoherenceStatus.UNAVAILABLE
    assert report.mean_normalized_score is None
    assert all(
        cell.status is CoherenceCellStatus.COVARIANCE_RANK_DEFICIENT
        and cell.mahalanobis_sq is None
        for cell in report.cells
    )


def test_coherence_rank_decision_is_covariance_scale_invariant() -> None:
    path = _path()
    report = build_depth_coherence_report(
        report_id="PR266-TINY-FULL-RANK",
        path=path,
        steps=_steps(path, covariance_scale=1e-20),
    )
    assert report.status is DepthCoherenceStatus.DEFINED
    assert report.mean_normalized_score == pytest.approx(0.0)


def test_depth_scramble_negative_control_degrades_coherence() -> None:
    path = _path()
    control = build_depth_scramble_control(
        control_id="PR266-SCRAMBLE",
        path=path,
        steps=_steps(path),
        permutation=(1, 2, 0),
        minimum_degradation=0.1,
    )
    assert control.owner == "MIO"
    assert control.status is ScrambleControlStatus.PASSED
    assert control.baseline_score == pytest.approx(0.0)
    assert control.scrambled_score > control.baseline_score
    assert control.score_degradation >= control.minimum_degradation


def test_htt_likelihood_requires_model_prediction_not_mio_report() -> None:
    path = _path()
    steps = _steps(path)
    prediction = build_depth_model_prediction(
        prediction_id="PR266-LOCAL-MODEL",
        path=path,
        model_id="PR266-LOCAL-RESPONSE-V1",
        hypothesis_class=DepthHypothesisClass.LOCAL_RESPONSE,
        means=tuple(value.values for value in steps),
        transfer_source="none",
        model_config_id="sha256:local-model-config",
        assumptions=("synthetic exact-mean likelihood fixture",),
    )
    result = evaluate_depth_path_likelihood(
        result_id="PR266-LOCAL-LOGL",
        path=path,
        observations=steps,
        prediction=prediction,
    )
    assert result.owner == "HTT"
    assert result.hypothesis_class is DepthHypothesisClass.LOCAL_RESPONSE
    assert np.isfinite(result.log_likelihood)
    coherence = build_depth_coherence_report(
        report_id="PR266-MIO-ONLY",
        path=path,
        steps=steps,
    )
    with pytest.raises(DepthPathError, match="not an HTT model"):
        evaluate_depth_path_likelihood(
            result_id="PR266-FORGED-HTT",
            path=path,
            observations=steps,
            prediction=coherence,
        )


def test_htt_likelihood_rejects_numerically_indefinite_covariance() -> None:
    path = _path()
    steps = list(_steps(path))
    steps[0] = build_observable_feature_step(
        step_id="PR266-INDEFINITE-COV",
        stratum=path.strata[0],
        values=(1.0, 2.0),
        covariance=((-1e-13, 0.0), (0.0, -1e-13)),
        source_artifact_id="sha256:indefinite-feature",
        extraction_method_id="PR266-INDEFINITE-COVARIANCE-CONTROL",
        sample_count=64,
    )
    prediction = build_depth_model_prediction(
        prediction_id="PR266-INDEFINITE-MODEL",
        path=path,
        model_id="PR266-LOCAL-RESPONSE-V1",
        hypothesis_class=DepthHypothesisClass.LOCAL_RESPONSE,
        means=tuple(value.values for value in steps),
        transfer_source="none",
        model_config_id="sha256:indefinite-model-config",
        assumptions=("synthetic covariance refusal fixture",),
    )
    with pytest.raises(DepthPathError, match="positive-definite"):
        evaluate_depth_path_likelihood(
            result_id="PR266-INDEFINITE-LOGL",
            path=path,
            observations=steps,
            prediction=prediction,
        )


def test_selection_covariance_and_result_mutations_fail_closed() -> None:
    path = _path()
    step = _steps(path)[0]
    report = build_depth_coherence_report(
        report_id="PR266-MUTATION",
        path=path,
        steps=_steps(path),
    )
    object.__setattr__(
        path.strata[1],
        "selection_id",
        "sha256:forged-selection",
    )
    with pytest.raises(DepthPathError, match="identity drifted"):
        path.as_payload()
    object.__setattr__(step, "covariance", ((99.0, 0.0), (0.0, 99.0)))
    with pytest.raises(DepthPathError, match="identity drifted"):
        step.as_payload()
    object.__setattr__(report, "mean_normalized_score", 99.0)
    with pytest.raises(DepthPathError, match="identity drifted"):
        report.as_payload()


def test_owner_facades_do_not_cross_feature_coherence_likelihood_lanes() -> None:
    import htt.infer.depth_path as htt_lane
    import mio.formalism.depth_path as mio_lane
    import obsstat.depth_path as obsstat_lane

    assert obsstat_lane.ObservableFeatureStep is not None
    assert not hasattr(obsstat_lane, "build_depth_coherence_report")
    assert not hasattr(obsstat_lane, "evaluate_depth_path_likelihood")
    assert mio_lane.DepthCoherenceReport is not None
    assert not hasattr(mio_lane, "DepthLikelihoodResult")
    assert not hasattr(mio_lane, "evaluate_depth_path_likelihood")
    assert htt_lane.DepthLikelihoodResult is not None
    assert not hasattr(htt_lane, "build_depth_coherence_report")


def test_no_depth_surface_promotes_global_native_geometry_or_family_claim() -> None:
    path = _path()
    text = str(path.as_payload()).lower()
    assert "global-tilt evidence" in text
    assert "native solver" in text
    assert "family identification" in text
    assert path.claim_ceiling == "diagnostic_only"
