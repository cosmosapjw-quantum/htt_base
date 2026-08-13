#!/usr/bin/env python3
"""Independent numerical oracle for the frozen PR-286 candidate.

Exit zero means that the oracle completed and reproduced its declared verdict;
it does not mean that the reviewed candidate passed.  The emitted
``review_outcome`` is the scientific/code-review verdict.
"""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import sys
import warnings

import numpy as np


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "htt/src"))
sys.path.insert(0, str(ROOT / "htt"))
sys.path.insert(0, str(ROOT))

from common import vector_tensor_statistical_inference as inference  # noqa: E402
import mio.formalism.vector_tensor_validation as mio_public  # noqa: E402


def floats(value: object):
    if isinstance(value, bool):
        return
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from floats(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from floats(child)


def expect_typed_refusal(label: str, function) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            function()
    except inference.PillarSInferenceError:
        return "PillarSInferenceError"
    except Exception as exc:  # pragma: no cover - this is a review failure
        raise AssertionError(
            f"{label} escaped through the wrong exception: {type(exc).__name__}"
        ) from exc
    raise AssertionError(f"{label} was accepted instead of refused")


def load_runner():
    path = ROOT / "scripts/codex_harness/run_pr286_pillar_s_adjudication.py"
    spec = importlib.util.spec_from_file_location("pr286_oracle_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    receipt_path = (
        ROOT
        / "docs/research_program/post_pr275/pillar_s_adjudication/"
        "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert len(receipt["rows"]) == 72
    assert all(math.isfinite(value) for value in floats(receipt))

    huge_local = np.asarray((1.0e200, 1.0e200))
    huge_global = np.asarray((1.0e200, 1.0e200 + 2.0e185))
    htt_huge = expect_typed_refusal(
        "finite huge-scale near-proportional HTT GLS",
        lambda: inference.evaluate_depth_local_global(
            huge_local,
            covariance=np.eye(2),
            covariance_id="oracle-huge",
            local_design=huge_local,
            global_design=huge_global,
            mask_path_id="oracle-mask",
            transfer_source="none",
            principal_angle_floor_radians=1.0e-12,
        ),
    )
    htt_extreme_spd = expect_typed_refusal(
        "finite extreme-SPD HTT GLS",
        lambda: inference.evaluate_depth_local_global(
            np.asarray((0.25, 0.5, 0.75, 1.0)),
            covariance=np.diag((1.0e-320, 1.0, 2.0, 3.0)),
            covariance_id="oracle-extreme-spd",
            local_design=np.asarray((0.25, 0.5, 0.75, 1.0)),
            global_design=np.ones(4),
            mask_path_id="oracle-mask",
            transfer_source="none",
        ),
    )
    htt_zero = expect_typed_refusal(
        "zero HTT design",
        lambda: inference.evaluate_depth_local_global(
            np.zeros(2),
            covariance=np.eye(2),
            covariance_id="oracle-zero",
            local_design=np.zeros(2),
            global_design=np.asarray((1.0, 0.0)),
            mask_path_id="oracle-mask",
            transfer_source="none",
        ),
    )

    covariance = np.asarray(((2.0, 0.25), (0.25, 0.5)))
    local = np.asarray((1.0, 0.2))
    global_ = np.asarray((0.9, 0.6))
    baseline_rank, baseline_angle = inference._whitened_design_geometry(
        covariance, local, global_
    )
    scale_angles = []
    for local_scale, global_scale in (
        (1.0e-200, 1.0e200),
        (1.0e-100, 1.0e100),
        (1.0, 1.0),
        (1.0e100, 1.0e-100),
        (1.0e200, 1.0e-200),
    ):
        rank, angle = inference._whitened_design_geometry(
            covariance, local_scale * local, global_scale * global_
        )
        assert rank == baseline_rank == 2
        assert math.isclose(angle, baseline_angle, rel_tol=2.0e-15, abs_tol=2.0e-15)
        scale_angles.append(angle)

    rank_probe = inference.evaluate_depth_local_global(
        np.asarray((1.0, 0.0)),
        covariance=np.diag((1.0, 1.0e-32)),
        covariance_id="oracle-whitened-rank",
        local_design=np.asarray((1.0, 0.0)),
        global_design=np.asarray((1.0, 1.0e-16)),
        mask_path_id="oracle-mask",
        transfer_source="none",
    )
    assert rank_probe.status is inference.ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    assert rank_probe.selected_candidate is inference.ModelCandidate.LOCAL
    assert all(math.isfinite(value) for value in floats(rank_probe.__dict__))

    proportional = inference.evaluate_depth_local_global(
        np.asarray((1.0, 2.0, 3.0, 4.0)),
        covariance=np.eye(4),
        covariance_id="oracle-proportional",
        local_design=np.asarray((1.0, 2.0, 3.0, 4.0)),
        global_design=np.asarray((2.0, 4.0, 6.0, 8.0)),
        mask_path_id="oracle-mask",
        transfer_source="none",
    )
    assert proportional.status is inference.ValidationStatus.ABSTAIN_NON_IDENTIFIED
    assert proportional.selected_candidate is inference.ModelCandidate.INDETERMINATE
    assert all(math.isfinite(value) for value in floats(proportional.__dict__))

    source = Path(inference.__file__).read_text(encoding="utf-8")
    local_global_source = source[source.index("def _gls_fit(") : source.index("def build_mio_depth_cross_check(")]
    assert "np.linalg.cond" not in local_global_source
    assert "condition_number" not in local_global_source

    runner = load_runner()
    payload = runner.build_complete_adjudication_receipt()
    mutation = runner.apply_registered_mutation(
        deepcopy(payload), "MU286-VTS14-NUMERIC-GUARD-DRIFT"
    )
    mutation["receipt_content_sha256"] = runner.receipt_content_sha256(mutation)
    mutation_marker = None
    try:
        runner.validate_complete_adjudication_receipt(mutation)
    except runner.PillarSAdjudicationError as exc:
        mutation_marker = str(exc)
    assert mutation_marker == "SEMANTIC_TYPE_DRIFT"

    # Discriminating counterexample: this public helper accepts finite inputs,
    # emits a success status, and nevertheless carries three non-finite fields.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        assert "build_mio_depth_cross_check" in mio_public.__all__
        mio_huge = mio_public.build_mio_depth_cross_check(
            huge_local,
            local_design=huge_local,
            global_design=huge_global,
            mask_path_id="oracle-mask",
        )
    mio_numeric = list(floats(mio_huge.__dict__))
    assert mio_huge.status is inference.ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
    assert len(mio_numeric) == 3
    assert not any(math.isfinite(value) for value in mio_numeric)
    try:
        json.dumps(mio_huge.__dict__, allow_nan=False)
    except ValueError:
        mio_strict_json = "REFUSED_NONFINITE"
    else:  # pragma: no cover - this is a review failure
        raise AssertionError("strict JSON unexpectedly accepted non-finite MIO report")

    print(
        json.dumps(
            {
                "oracle": "A-PR286-R2-PHYSCODE",
                "review_outcome": "FAIL",
                "candidate_receipt_rows": len(receipt["rows"]),
                "candidate_receipt_all_numeric_finite": True,
                "htt_invalid_paths": {
                    "huge_scale_near_proportional": htt_huge,
                    "extreme_finite_spd": htt_extreme_spd,
                    "zero_design": htt_zero,
                },
                "whitened_rank_probe": {
                    "status": rank_probe.status.value,
                    "selected_candidate": rank_probe.selected_candidate.value,
                },
                "principal_angle_scale_stability": {
                    "baseline_radians": baseline_angle,
                    "maximum_absolute_delta": max(
                        abs(value - baseline_angle) for value in scale_angles
                    ),
                },
                "proportional_design": {
                    "status": proportional.status.value,
                    "selected_candidate": proportional.selected_candidate.value,
                },
                "registered_numeric_mutation_kill_marker": mutation_marker,
                "blocking_counterexample": {
                    "api": "mio.formalism.vector_tensor_validation.build_mio_depth_cross_check",
                    "public_export": True,
                    "input_class": "finite_huge_scale_near_proportional",
                    "returned_status": mio_huge.status.value,
                    "numeric_fields": [str(value) for value in mio_numeric],
                    "strict_json": mio_strict_json,
                    "expected": "PillarSInferenceError",
                },
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
