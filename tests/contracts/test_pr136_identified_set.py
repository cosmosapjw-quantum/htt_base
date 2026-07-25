"""PR-136 contract tests: identified-set engine."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.identified_set import (
    AXES,
    KERNEL_AXES,
    AdmissibleBox,
    IdentifiedSetError,
    LinearConstraint,
    axis_constraint,
    classify_status_from_solver,
    disconnected_components,
    exact_engine,
    generate_caption,
    lint_caption,
    numeric_engine,
    require_cross_engine_agreement,
    subvector_projection,
    validate_set_valued,
    validate_status_semantics,
    verify_kernel_binding,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    path = REPO_ROOT / "scripts/codex_harness/run_pr136_identified_set.py"
    spec = importlib.util.spec_from_file_location("run_pr136", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_check_normalizes_only_generation_time_source_hash() -> None:
    runner = _load_runner()
    source = runner.SOURCE_PATH
    rel = runner.OUTPUTS["sets"]
    stored = {
        "statuses": {"fixture": "bounded"},
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            },
        },
    }
    current = json.loads(json.dumps(stored))
    current["negative_scan"]["targets"][source]["sha256"] = "2" * 64
    assert runner._semantic_artifact(
        rel, stored
    ) == runner._semantic_artifact(rel, current)
    current["statuses"]["fixture"] = "empty"
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["statuses"]["fixture"] = "bounded"
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)
    current["negative_scan"]["targets"][source]["hits"] = []
    current["negative_scan"]["targets"][source]["sha256"] = "not-a-sha"
    assert runner._semantic_artifact(
        rel, stored
    ) != runner._semantic_artifact(rel, current)

    manifest_rel = runner.OUTPUTS["manifest"]
    dependency = "htt/src/common/graded_nonid.py"
    stored_manifest = {"input_hashes": [
        f"{source}:{'1' * 64}",
        f"{dependency}:{'3' * 64}",
    ]}
    current_manifest = {"input_hashes": [
        f"{source}:{'2' * 64}",
        f"{dependency}:{'3' * 64}",
    ]}
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) == runner._semantic_artifact(manifest_rel, current_manifest)
    current_manifest["input_hashes"][1] = f"{dependency}:{'4' * 64}"
    assert runner._semantic_artifact(
        manifest_rel, stored_manifest
    ) != runner._semantic_artifact(manifest_rel, current_manifest)


def _bounded():
    return [axis_constraint("Sigma2", "==", 1)] + \
        [axis_constraint(a, ">=", -1) for a in AXES[1:]] + \
        [axis_constraint(a, "<=", 1) for a in AXES[1:]]


def _empty():
    return [axis_constraint("Sigma2", ">=", 1),
            axis_constraint("Sigma2", "<=", 0)]


def _rank_deficient():
    return [axis_constraint("Sigma2", "==", 0),
            axis_constraint("Omega_tilt", ">=", -1),
            axis_constraint("Omega_tilt", "<=", 1)]


def test_exact_engine_is_true_continuous_not_grid() -> None:
    # a non-integer boundary: the exact engine must return the TRUE
    # continuous interval [-1, 3/2], not a grid undersample
    cons = [axis_constraint("Sigma2", "==", 1),
            axis_constraint("W2", ">=", -1),
            axis_constraint("W2", "<=", Fraction(3, 2))] + \
        [axis_constraint(a, ">=", -1) for a in ("Omega_tilt",
                                                "DeltaOmega_k")] + \
        [axis_constraint(a, "<=", 1) for a in ("Omega_tilt",
                                               "DeltaOmega_k")]
    e = exact_engine(cons)
    n = numeric_engine(cons)
    assert e["axis_intervals"]["W2"] == ["-1", "3/2"]
    assert n["axis_intervals"]["W2"] == [-1.0, 1.5]
    require_cross_engine_agreement(e, n)


def test_multi_axis_constraint_refused() -> None:
    multi = LinearConstraint((Fraction(1), Fraction(1), Fraction(0),
                              Fraction(0)), "<=", Fraction(1))
    with pytest.raises(IdentifiedSetError, match="AXIS-SEPARABLE"):
        exact_engine([axis_constraint("Sigma2", "==", 0), multi])


@pytest.mark.parametrize("point", [
    [],
    [0],
    [0, 0, 0],
    [0, 0, 0, 0, 0],
    "0000",
])
def test_constraint_satisfaction_rejects_wrong_point_arity(point) -> None:
    constraint = axis_constraint("Sigma2", "<=", 1)
    with pytest.raises(IdentifiedSetError, match="exactly"):
        constraint.satisfied(point)


def test_bounded_both_engines_agree() -> None:
    e = exact_engine(_bounded())
    n = numeric_engine(_bounded())
    assert e["status"] == n["status"] == "bounded"
    require_cross_engine_agreement(e, n)
    assert e["axis_intervals"]["Sigma2"] == ["1", "1"]


def test_empty_both_engines_agree() -> None:
    e = exact_engine(_empty())
    n = numeric_engine(_empty())
    assert e["status"] == n["status"] == "empty"
    require_cross_engine_agreement(e, n)


def test_rank_deficient_unbounded_on_kernel() -> None:
    e = exact_engine(_rank_deficient())
    n = numeric_engine(_rank_deficient())
    assert e["status"] == n["status"] == "unbounded"
    assert set(e["unbounded_axes"]) == set(KERNEL_AXES)
    assert set(n["unbounded_axes"]) == set(KERNEL_AXES)
    require_cross_engine_agreement(e, n)


def test_cross_engine_checks_bounded_axis_inside_unbounded_set() -> None:
    # a bounded Omega_tilt with a non-integer bound INSIDE an
    # overall-unbounded set must still be cross-checked (the P0 hole)
    cons = [axis_constraint("Sigma2", "==", 0),
            axis_constraint("Omega_tilt", ">=", -1),
            axis_constraint("Omega_tilt", "<=", Fraction(3, 2))]
    e = exact_engine(cons)
    n = numeric_engine(cons)
    assert e["status"] == "unbounded"
    require_cross_engine_agreement(e, n)
    # a fabricated exact interval on the bounded axis must be caught even
    # though the overall status is unbounded
    e_bad = {"status": "unbounded",
             "axis_intervals": dict(e["axis_intervals"],
                                    Omega_tilt=["-1", "99"]),
             "unbounded_axes": e["unbounded_axes"]}
    with pytest.raises(IdentifiedSetError, match="boundary disagreement"):
        require_cross_engine_agreement(e_bad, n)


@pytest.mark.parametrize("tol", [
    True,
    -1.0,
    float("nan"),
    float("inf"),
])
def test_cross_engine_rejects_invalid_tolerance(tol) -> None:
    exact = exact_engine(_bounded())
    numeric = numeric_engine(_bounded())
    with pytest.raises(IdentifiedSetError, match="finite non-negative"):
        require_cross_engine_agreement(exact, numeric, tol=tol)


@pytest.mark.parametrize("endpoint", [
    True,
    float("nan"),
    float("inf"),
])
def test_cross_engine_rejects_invalid_numeric_boundary(endpoint) -> None:
    exact = exact_engine(_bounded())
    numeric = numeric_engine(_bounded())
    numeric["axis_intervals"]["Sigma2"] = [endpoint, endpoint]
    with pytest.raises(IdentifiedSetError, match="non-finite/non-real"):
        require_cross_engine_agreement(exact, numeric)


@pytest.mark.parametrize("result,message", [
    ({"status": "bounded", "axis_intervals": {},
      "unbounded_axes": []}, "every registered axis"),
    ({"status": "mystery", "axis_intervals": {},
      "unbounded_axes": []}, "invalid status"),
    ({"status": "empty", "axis_intervals": None,
      "unbounded_axes": ["Sigma2"]}, "cannot name unbounded"),
    ({"status": "unbounded", "axis_intervals": {},
      "unbounded_axes": ["Sigma2"]}, "every registered axis"),
    ({"status": "unbounded",
      "axis_intervals": {axis: [None, None] for axis in AXES},
      "unbounded_axes": []}, "names no unbounded"),
])
def test_cross_engine_rejects_malformed_result_shape(
    result, message
) -> None:
    with pytest.raises(IdentifiedSetError, match=message):
        require_cross_engine_agreement(result, dict(result))


def test_kernel_binding_live() -> None:
    binding = verify_kernel_binding()
    assert binding["bound_live"] is True
    assert set(KERNEL_AXES) == {"W2", "DeltaOmega_k"}


def test_disconnected_two_components_with_width() -> None:
    box = AdmissibleBox(lower={a: Fraction(-3) for a in AXES},
                        upper={a: Fraction(3) for a in AXES},
                        pinned_id="pin1")
    dc = disconnected_components("Omega_tilt", Fraction(1), box)
    assert dc["status"] == "disconnected"
    assert {c["component"] for c in dc["components"]} == \
        {"positive", "negative"}
    # genuine interior width, not two isolated points
    pos = next(c for c in dc["components"] if c["component"] == "positive")
    assert pos["abs_axis_interval"] == ["1", "3"]
    assert dc["excluded_open_gap"] == ["-1", "1"]
    # threshold at the box edge (no width) is refused
    with pytest.raises(IdentifiedSetError, match="strictly inside"):
        disconnected_components("Omega_tilt", Fraction(3), box)


def test_subvector_projection_separate() -> None:
    e = exact_engine(_rank_deficient())
    sub_nonkernel = subvector_projection(e, ["Sigma2", "Omega_tilt"])
    sub_kernel = subvector_projection(e, list(KERNEL_AXES))
    # the full set is unbounded; the non-kernel subvector is bounded
    assert sub_nonkernel["status"] == "bounded"
    assert sub_kernel["status"] == "unbounded"


@pytest.mark.parametrize("full_result,expected", [
    (exact_engine(_empty()), "empty"),
    ({"status": "undetermined", "axis_intervals": None,
      "unbounded_axes": []}, "undetermined"),
])
def test_subvector_projection_preserves_non_estimable_status(
    full_result, expected
) -> None:
    projection = subvector_projection(full_result, ["Sigma2"])
    assert projection["status"] == expected
    assert projection["axis_intervals"] is None
    assert projection["unbounded_in_subvector"] == []


@pytest.mark.parametrize("subaxes,message", [
    ([], "non-empty sequence"),
    ("Sigma2", "non-empty sequence"),
    (["Sigma2", "Sigma2"], "duplicates"),
    (["not-an-axis"], "unknown axis"),
])
def test_subvector_projection_rejects_invalid_axes(
    subaxes, message
) -> None:
    with pytest.raises(IdentifiedSetError, match=message):
        subvector_projection(exact_engine(_bounded()), subaxes)


@pytest.mark.parametrize("artifact,message", [
    ({"status": "bounded"}, "missing required fields"),
    ({"status": "bounded", "central_estimate": 0.5},
     "missing required fields"),
    ({"status": "mystery",
      "axis_intervals": {axis: ["0", "1"] for axis in AXES},
      "unbounded_axes": []}, "invalid status"),
    ({"status": "disconnected"}, "non-empty components"),
])
def test_set_valued_validator_rejects_incomplete_artifact(
    artifact, message
) -> None:
    with pytest.raises(IdentifiedSetError, match=message):
        validate_set_valued(artifact)


def test_set_valued_validator_accepts_disconnected_components() -> None:
    validate_set_valued({
        "status": "disconnected",
        "components": [{"component": "positive"},
                       {"component": "negative"}],
    })


def test_cross_engine_disagreement_blocks() -> None:
    exact = {"status": "bounded",
             "axis_intervals": {a: ["0", "1"] for a in AXES},
             "unbounded_axes": []}
    numeric = {"status": "unbounded", "axis_intervals": None,
               "unbounded_axes": list(AXES)}
    with pytest.raises(IdentifiedSetError, match="STATUS disagreement"):
        require_cross_engine_agreement(exact, numeric)


def test_status_semantics_guards() -> None:
    validate_status_semantics("bounded", "a wide uncertainty region")
    with pytest.raises(IdentifiedSetError, match="NEVER a detection"):
        validate_status_semantics("empty", "this is a detection")
    with pytest.raises(IdentifiedSetError, match="NEVER a central"):
        validate_status_semantics("bounded", "the central estimate is x")
    with pytest.raises(IdentifiedSetError, match="NEVER a"):
        validate_status_semantics("undetermined", "non-identification")


def test_classify_from_solver() -> None:
    assert classify_status_from_solver(False, True, False) == "undetermined"
    assert classify_status_from_solver(True, False, False) == "empty"
    assert classify_status_from_solver(True, True, True) == "unbounded"
    assert classify_status_from_solver(True, True, False) == "bounded"


def test_set_valued_and_admissible_pin() -> None:
    validate_set_valued(exact_engine(_bounded()))
    with pytest.raises(IdentifiedSetError, match="scalar summary"):
        validate_set_valued({"central_estimate": 0.5})
    box = AdmissibleBox(lower={a: Fraction(-3) for a in AXES},
                        upper={a: Fraction(3) for a in AXES},
                        pinned_id="pin1")
    # a REAL shrink (tighter than the pin) is refused
    with pytest.raises(IdentifiedSetError, match="tighter than the pinned"):
        box.validate_proposed({"Omega_tilt": Fraction(-1, 10)},
                              {"Omega_tilt": Fraction(1, 10)})
    with pytest.raises(IdentifiedSetError, match="tighter than the pinned"):
        box.refuse_shrink_to([Fraction(0)] * len(AXES))
    # an equal or wider proposal is allowed (not a shrink)
    box.validate_proposed({}, {"Omega_tilt": Fraction(3)})
    box.validate_proposed({}, {"Omega_tilt": Fraction(5)})


@pytest.mark.parametrize("lower,upper", [
    ({"Omega_tilt": Fraction(0)}, {}),
    ({}, {"Omega_tilt": Fraction(0)}),
])
def test_admissible_pin_rejects_bound_on_unbounded_side(
    lower, upper
) -> None:
    box = AdmissibleBox(lower={}, upper={}, pinned_id="unbounded-pin")
    with pytest.raises(IdentifiedSetError, match="unbounded pinned"):
        box.validate_proposed(lower, upper)


def test_admissible_box_copies_and_freezes_pinned_bounds() -> None:
    lower = {axis: Fraction(-3) for axis in AXES}
    upper = {axis: Fraction(3) for axis in AXES}
    box = AdmissibleBox(lower=lower, upper=upper, pinned_id="pin")
    lower["Omega_tilt"] = Fraction(0)
    upper["Omega_tilt"] = Fraction(0)
    assert box.lower["Omega_tilt"] == Fraction(-3)
    assert box.upper["Omega_tilt"] == Fraction(3)
    with pytest.raises(TypeError):
        box.lower["Omega_tilt"] = Fraction(0)
    with pytest.raises(TypeError):
        box.upper["Omega_tilt"] = Fraction(0)


@pytest.mark.parametrize("lower,upper,pinned_id,message", [
    ({"typo": -1}, {"typo": 1}, "pin", "unknown axes"),
    ({"Sigma2": 2}, {"Sigma2": 1}, "pin", "exceeds upper"),
    ({"Sigma2": -1}, {"Sigma2": 1}, "", "non-empty string"),
    ({"Sigma2": float("nan")}, {"Sigma2": 1}, "pin",
     "finite Fraction-compatible"),
    ({"Sigma2": True}, {"Sigma2": 1}, "pin",
     "finite Fraction-compatible"),
])
def test_admissible_box_rejects_invalid_definition(
    lower, upper, pinned_id, message
) -> None:
    with pytest.raises(IdentifiedSetError, match=message):
        AdmissibleBox(lower=lower, upper=upper, pinned_id=pinned_id)


@pytest.mark.parametrize("lower,upper", [
    ({"Omega_tlt": Fraction(0)}, {}),
    ({}, {"Omega_tlt": Fraction(0)}),
])
def test_admissible_box_rejects_unknown_proposed_axes(
    lower, upper
) -> None:
    box = AdmissibleBox(
        lower={"Omega_tilt": Fraction(-3)},
        upper={"Omega_tilt": Fraction(3)},
        pinned_id="pin",
    )
    with pytest.raises(IdentifiedSetError, match="unknown axes"):
        box.validate_proposed(lower, upper)


def test_caption_gate() -> None:
    text = generate_caption({"bounded_box": "bounded"})
    lint_caption(text)
    for suffix in (" The empty set is" + " a detection.",
                   " Report the broad set as" + " the central estimate.",
                   " Nonconvergence means" + " non-identification.",
                   " We point-identified" + " the shear."):
        with pytest.raises(IdentifiedSetError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr136_identified_set.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_statuses_and_mutations() -> None:
    sets = json.loads(
        (REPO_ROOT / "docs/generated/pr136_identified_sets.json")
        .read_text(encoding="utf-8"))
    assert sets["statuses"] == {
        "bounded_box": "bounded", "empty_infeasible": "empty",
        "rank_deficient_unbounded": "unbounded",
        "disconnected_sign": "disconnected"}
    cross = json.loads(
        (REPO_ROOT / "docs/generated/pr136_cross_engine.json")
        .read_text(encoding="utf-8"))
    assert cross["all_agree"] is True
    sub = json.loads(
        (REPO_ROOT / "docs/generated/pr136_subvector.json")
        .read_text(encoding="utf-8"))
    assert sub["subvector_non_kernel"]["status"] == "bounded"
    assert sub["subvector_kernel"]["status"] == "unbounded"
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr136_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr136_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
