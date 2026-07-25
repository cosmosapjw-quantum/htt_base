"""PR-133 contract tests: source-response type system."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.source_response_types import (
    EQUIVALENCE_EDGES,
    EXPECTED_RANK,
    QuantityType,
    Rung,
    SourceResponseError,
    TypedQuantity,
    analytic_response_rank,
    bridge,
    deprojection_estimator_property,
    deprojected_shear,
    discrimination_verdict,
    generate_caption,
    harmonic_order_counting,
    label_highest_rung,
    lint_caption,
    observed_response,
    require_beta_order,
    require_declared_provenance,
    require_rung_not_above,
    require_surfaced_exception,
)

_PR127_KERNEL_EV = "docs/generated/pr127_response_kernel.json"
_PR127_WITNESS_EV = "docs/generated/pr127_nonid_witnesses.json"
_DOPPLER_EV = "htt/bass/forward/doppler_boost.py"

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr133_source_response_types.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr133", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_source_types_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.SOURCE_TYPES_PATH
    types = runner.OUTPUTS["types"]
    stored = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            }
        }
    }
    current = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
            }
        }
    }
    assert runner._semantic_artifact(
        types, stored
    ) == runner._semantic_artifact(types, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        types, stored
    ) != runner._semantic_artifact(types, current)

    legacy = "htt/obsstat/egs3_kinematic_deprojection.py"
    upstream = "htt/src/common/graded_nonid.py"
    manifest = runner.OUTPUTS["manifest"]
    stored = {
        "input_hashes": [
            f"{source}:{'1' * 64}",
            f"{legacy}:{'3' * 64}",
            f"{upstream}:{'4' * 64}",
        ]
    }
    current = {
        "input_hashes": [
            f"{source}:{'2' * 64}",
            f"{legacy}:{'3' * 64}",
            f"{upstream}:{'4' * 64}",
        ]
    }
    assert runner._semantic_artifact(
        manifest, stored
    ) == runner._semantic_artifact(manifest, current)
    current["input_hashes"][1] = f"{legacy}:{'5' * 64}"
    assert runner._semantic_artifact(
        manifest, stored
    ) != runner._semantic_artifact(manifest, current)


def test_runner_rejects_unknown_typed_quantity_rows() -> None:
    runner = _load_runner()
    rows = [
        {"name": qtype.value, **runner._TYPE_META[qtype]}
        for qtype in QuantityType
    ]
    rows.append({
        "name": "forged_type",
        "symbol": "X",
        "order_in_beta": 0,
        "harmonic_channel": 0,
        "physical": True,
    })
    with pytest.raises(SystemExit, match="production enum"):
        runner.build_types({"typed_quantities": {"types": rows}})


def test_runner_binds_boost_labels_to_symbolic_derivation() -> None:
    runner = _load_runner()
    with pytest.raises(SystemExit, match="symbolic derivation"):
        runner.build_boost({
            "harmonic_boost": {
                "order_counting": {
                    "A_v": "O(beta^0), ell = 0",
                    "kinematic_quadrupole": (
                        "O(beta^2), ell = 2 "
                        "(from the Doppler/aberration transform of the "
                        "monopole)"
                    ),
                },
            },
        })


def test_runner_binds_deprojection_formula_to_implementation() -> None:
    runner = _load_runner()
    with pytest.raises(SystemExit, match="production subtraction"):
        runner.build_deprojection({
            "deprojection": {
                "formula": (
                    "Sigma_tilde^2 = Sigma^2 "
                    "+ 7 alpha (Omega_tilt)^2"
                ),
                "alpha_note": "forged",
            },
        })


def test_runner_binds_analytic_rank_to_response_map() -> None:
    runner = _load_runner()
    with pytest.raises(SystemExit, match="PR-127 response map"):
        runner.build_graph({
            "response_graph": {"analytic_rank": 4},
        })


def test_type_firewall_blocks_cross_type() -> None:
    av = TypedQuantity(QuantityType.OBSERVER_PROXY, Fraction(1, 100))
    ot = TypedQuantity(QuantityType.PHYSICAL_TILT, Fraction(1, 100))
    (av + TypedQuantity(QuantityType.OBSERVER_PROXY, Fraction(1, 100)))
    for op in (lambda: av + ot, lambda: av - ot, lambda: av < ot,
               lambda: av <= ot, lambda: av > ot, lambda: av >= ot):
        with pytest.raises(SourceResponseError, match="cross-type"):
            op()
    # cross-type equality is always False (never a silent match)
    assert (av == ot) is False


@pytest.mark.parametrize("value", [True, False])
def test_typed_quantity_rejects_boolean_values(value) -> None:
    with pytest.raises(SourceResponseError, match="must not be boolean"):
        TypedQuantity(QuantityType.OBSERVER_PROXY, value)


def test_typed_quantity_requires_string_provenance() -> None:
    class ForgedDeclared:
        def __str__(self) -> str:
            return "declared"

    with pytest.raises(SourceResponseError, match="non-empty string"):
        TypedQuantity(
            QuantityType.PHYSICAL_TILT,
            Fraction(1, 100),
            provenance=ForgedDeclared(),
        )


def test_non_bridge_guard_and_provenance() -> None:
    av = TypedQuantity(QuantityType.OBSERVER_PROXY, Fraction(1, 100))
    with pytest.raises(SourceResponseError, match="bridge.*refused"):
        bridge(av, QuantityType.PHYSICAL_TILT, "any-ref")
    with pytest.raises(SourceResponseError, match="bridge.*refused"):
        bridge(av, QuantityType.PHYSICAL_TILT, None)
    # direct reconstruction with a forged bridged provenance is caught
    smuggled = TypedQuantity(QuantityType.PHYSICAL_TILT, av.value,
                             provenance="bridged:forged")
    with pytest.raises(SourceResponseError, match="unsanctioned"):
        require_declared_provenance(smuggled)
    require_declared_provenance(
        TypedQuantity(QuantityType.PHYSICAL_TILT, Fraction(1, 100)))


def test_equivalence_edges_cannot_be_registered_at_runtime() -> None:
    key = (QuantityType.OBSERVER_PROXY, QuantityType.PHYSICAL_TILT)
    with pytest.raises(TypeError):
        EQUIVALENCE_EDGES[key] = {"evidence": "forged-local-reference"}


def test_same_type_arithmetic_cannot_launder_bridge_provenance() -> None:
    forged = TypedQuantity(
        QuantityType.PHYSICAL_TILT,
        Fraction(1, 100),
        provenance="bridged:forged",
    )
    declared = TypedQuantity(
        QuantityType.PHYSICAL_TILT,
        Fraction(1, 100),
    )
    result = forged + declared
    assert result.provenance == "bridged:forged"
    with pytest.raises(SourceResponseError, match="unsanctioned"):
        require_declared_provenance(result)


def test_harmonic_order_counting() -> None:
    counting = harmonic_order_counting()
    assert counting["A_v_order_in_beta"] == 1
    assert counting["kinematic_quadrupole_order_in_beta"] == 2
    require_beta_order("A_v", 1)
    require_beta_order("kinematic_quadrupole", 2)
    with pytest.raises(SourceResponseError, match="order counting"):
        require_beta_order("kinematic_quadrupole", 1)
    with pytest.raises(SourceResponseError, match="order counting"):
        require_beta_order("A_v", 2)
    for claimed in (True, Fraction(1)):
        with pytest.raises(SourceResponseError, match="explicit integer"):
            require_beta_order("A_v", claimed)


def test_deprojection_estimator_property() -> None:
    prop = deprojection_estimator_property()
    assert all(r["sigma_tilde2"] == "0"
               for r in prop["boost_removed_states"])
    assert prop["no_oversubtraction_states"]
    # pure boost removed exactly
    assert deprojected_shear(Fraction(9, 10 ** 6), Fraction(3, 1000)) == 0
    # shear-only not over-subtracted
    assert deprojected_shear(Fraction(1, 100), Fraction(0)) == \
        Fraction(1, 100)


def test_response_ladder_no_auto_promotion(tmp_path: Path) -> None:
    # a gap in the middle caps the candidate below the gap (pointers
    # must resolve to real repo files)
    labelled = label_highest_rung({
        Rung.ALGEBRAIC_WITNESS: _PR127_KERNEL_EV,
        Rung.CONSTRAINT_ADMISSIBLE: _PR127_WITNESS_EV,
        Rung.LOCAL_DYNAMICS_ADMISSIBLE: None,
        Rung.GLOBAL_DYNAMICS_ADMISSIBLE: _DOPPLER_EV})
    assert labelled["highest_rung"] == "constraint_admissible"
    assert set(labelled["evidence"]) == {
        "algebraic_witness", "constraint_admissible"
    }
    # an unresolvable pointer is a false citation -> raise
    with pytest.raises(SourceResponseError, match="does not resolve"):
        label_highest_rung({Rung.ALGEBRAIC_WITNESS: "docs/nope.json"})
    outside = tmp_path / "outside-evidence.txt"
    outside.write_text("not repository evidence", encoding="utf-8")
    with pytest.raises(SourceResponseError, match="outside the repository"):
        label_highest_rung({Rung.ALGEBRAIC_WITNESS: str(outside)})
    # claiming the top rung with no base evidence -> raise
    with pytest.raises(SourceResponseError, match="no rung reached"):
        label_highest_rung({Rung.GLOBAL_DYNAMICS_ADMISSIBLE: _DOPPLER_EV})
    # the REAL auto-promotion kill: mid-gap with the top rung present
    with pytest.raises(SourceResponseError, match="auto-promotion"):
        require_rung_not_above(
            {Rung.ALGEBRAIC_WITNESS: _PR127_KERNEL_EV,
             Rung.CONSTRAINT_ADMISSIBLE: _PR127_WITNESS_EV,
             Rung.LOCAL_DYNAMICS_ADMISSIBLE: None,
             Rung.GLOBAL_DYNAMICS_ADMISSIBLE: _DOPPLER_EV},
            Rung.GLOBAL_DYNAMICS_ADMISSIBLE)


def test_response_graph_analytic_vs_observed() -> None:
    # analytic rank is the PR-127 frozen rank 2 (consistency anchor)
    assert analytic_response_rank() == EXPECTED_RANK == 2
    clean = observed_response(None)
    assert clean["observed_rank"] == 2
    assert clean["aligned_axis_exception"] is None
    assert len(clean["analytic_kernel"]) == 2
    aligned = observed_response(
        {"collinear_axes": [("Sigma2", "Omega_tilt")]})
    assert aligned["observed_rank"] == 1
    assert aligned["aligned_axis_exception"]["colliding_axes"] == \
        [["Omega_tilt", "Sigma2"]]
    require_surfaced_exception(aligned)
    with pytest.raises(SourceResponseError, match="hiding the exception"):
        require_surfaced_exception({"analytic_rank": 2, "observed_rank": 1,
                                    "aligned_axis_exception": None})
    with pytest.raises(SourceResponseError, match="inconsistent"):
        require_surfaced_exception({
            "analytic_rank": 2,
            "observed_rank": 1,
            "aligned_axis_exception": {"kind": "placeholder"},
        })
    with pytest.raises(SourceResponseError, match="without.*reduction"):
        require_surfaced_exception({
            "analytic_rank": 2,
            "observed_rank": 2,
            "aligned_axis_exception": {
                "kind": "aligned_axis_rank_reduction",
            },
        })


@pytest.mark.parametrize("pairs", [
    [("Sigma2", "Sigma2")],
    [("W2", "DeltaOmega_k")],
    [("Sigma2", "Omega_tilt"), ("Omega_tilt", "Sigma2")],
])
def test_observed_response_rejects_invalid_collinear_axes(pairs) -> None:
    with pytest.raises(SourceResponseError, match="active response axes"):
        observed_response({"collinear_axes": pairs})


def test_discrimination_verdict() -> None:
    assert discrimination_verdict(boost_removed=False, local_rank=2,
                                  global_rank=2, full_rank=2) == \
        "non_identified"
    assert discrimination_verdict(boost_removed=True, local_rank=1,
                                  global_rank=2, full_rank=2) == \
        "non_identified"
    assert discrimination_verdict(boost_removed=True, local_rank=2,
                                  global_rank=1, full_rank=2) == \
        "non_identified"
    assert discrimination_verdict(boost_removed=True, local_rank=2,
                                  global_rank=2, full_rank=2) == \
        "discriminable_pre_solver"
    for ranks in (
        {"local_rank": -1, "global_rank": -1, "full_rank": -1},
        {"local_rank": 3, "global_rank": 3, "full_rank": 2},
    ):
        with pytest.raises(SourceResponseError, match="rank"):
            discrimination_verdict(boost_removed=True, **ranks)
    with pytest.raises(SourceResponseError, match="explicit boolean"):
        discrimination_verdict(boost_removed="false", local_rank=2,
                               global_rank=2, full_rank=2)


def test_caption_gate() -> None:
    text = generate_caption()
    lint_caption(text)
    for suffix in (" We bridge A_v" + " to Omega_tilt here.",
                   " This measures the" + " Bianchi family.",
                   " Shear detected" + " via deprojection.",
                   " Aligned-axis exception" + " suppressed."):
        with pytest.raises(SourceResponseError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr133_source_response_types.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_types_graph_mutations() -> None:
    types = json.loads(
        (REPO_ROOT / "docs/generated/pr133_typed_quantities.json")
        .read_text(encoding="utf-8"))
    assert len(types["types"]) == 6
    assert types["registered_equivalence_edges"] == 0
    names = {t["name"] for t in types["types"]}
    assert names == {"observer_proxy", "physical_tilt", "vorticity",
                     "shear", "curvature", "background_geometry"}
    graph = json.loads(
        (REPO_ROOT / "docs/generated/pr133_response_graph.json")
        .read_text(encoding="utf-8"))
    assert graph["analytic_rank"] == 2
    assert graph["observed_aligned"]["observed_rank"] == 1
    assert graph["observed_aligned"]["aligned_axis_exception"]
    assert len(graph["observed_aligned"]["analytic_kernel"]) == 2
    assert graph["discrimination_verdicts"]["boost_not_removed"] == \
        "non_identified"
    assert graph["response_ladder"]["W2_DeltaOmega_k_joint_null"][
        "highest_rung"] == "constraint_admissible"
    assert graph["response_ladder"]["omega_tilt_kinematic_proxy"][
        "highest_rung"] == "algebraic_witness"
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr133_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr133_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
