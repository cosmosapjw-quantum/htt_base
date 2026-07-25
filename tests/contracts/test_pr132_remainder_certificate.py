"""PR-132 contract tests: interval remainder certification."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.omk_remainder_certificate import (
    K_ABS_MAX,
    M_TRAP,
    W_BOX,
    ClaimBlockError,
    CompactDomain,
    OmkRemainderError,
    build_budget,
    central_prediction,
    check_admissible_state,
    enclosure,
    generate_caption,
    lint_caption,
    propagate_to_ceiling,
    prove_polynomial_sign,
    prove_trapping_certificate,
    register_domain,
    validate_budget,
    validate_certificate_method,
    validate_report_central,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr132_remainder_certificate.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr132", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_maintained_source_hashes_are_generation_time_provenance() -> None:
    runner = _load_runner()
    own_source, upstream_source = runner.MAINTAINED_SOURCES
    frozen_fd = "docs/generated/pr131_fd_plateau.json"
    manifest = runner.OUTPUTS["manifest"]
    stored = {
        "input_hashes": [
            f"{own_source}:{'1' * 64}",
            f"{upstream_source}:{'2' * 64}",
            f"{frozen_fd}:{'3' * 64}",
        ]
    }
    current = {
        "input_hashes": [
            f"{own_source}:{'4' * 64}",
            f"{upstream_source}:{'5' * 64}",
            f"{frozen_fd}:{'3' * 64}",
        ]
    }
    assert runner._semantic_artifact(
        manifest, stored
    ) == runner._semantic_artifact(manifest, current)
    current["input_hashes"][2] = f"{frozen_fd}:{'6' * 64}"
    assert runner._semantic_artifact(
        manifest, stored
    ) != runner._semantic_artifact(manifest, current)

    certificate = runner.OUTPUTS["certificate"]
    stored = {
        "negative_scan": {
            "targets": {
                own_source: {"sha256": "1" * 64, "hits": []},
            }
        }
    }
    current = {
        "negative_scan": {
            "targets": {
                own_source: {"sha256": "2" * 64, "hits": []},
            }
        }
    }
    assert runner._semantic_artifact(
        certificate, stored
    ) == runner._semantic_artifact(certificate, current)
    current["negative_scan"]["targets"][own_source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        certificate, stored
    ) != runner._semantic_artifact(certificate, current)


def test_trapping_certificate_proves_all_four_boundaries() -> None:
    cert = prove_trapping_certificate()
    assert len(cert["boundaries"]) == 4
    assert {(b["branch"], b["side"]) for b in cert["boundaries"]} == \
        {(1, "upper"), (1, "lower"), (-1, "upper"), (-1, "lower")}
    assert all(b["proved"] for b in cert["boundaries"])
    assert cert["grid_sampling_used"] is False
    validate_certificate_method(cert)


def test_wrong_trap_constant_fails_with_counterexample() -> None:
    with pytest.raises(OmkRemainderError, match="FAILED"):
        prove_trapping_certificate(Fraction(1, 100))


def test_interval_prover_rejects_reversed_boxes() -> None:
    import sympy as sp

    x, y = sp.symbols("x y")
    with pytest.raises(OmkRemainderError, match="ordered box"):
        prove_polynomial_sign(
            x - sp.Rational(1, 2),
            True,
            (Fraction(1), Fraction(0)),
            (Fraction(0), Fraction(0)),
            x,
            y,
        )


def test_enclosure_and_claim_block() -> None:
    w, k = Fraction(0), Fraction(1, 100)
    lo, hi = enclosure(w, k)
    center = central_prediction(w, k)
    assert lo < center < hi
    assert hi - lo == 2 * M_TRAP * k ** 3
    check_admissible_state(w, k, center)
    check_admissible_state(w, k, hi)   # boundary inclusive
    with pytest.raises(ClaimBlockError, match="claim\nblocked|claim "
                       "blocked"):
        check_admissible_state(w, k, hi + Fraction(1, 10 ** 12))
    # KS branch states work identically
    lo_n, hi_n = enclosure(Fraction(1, 3), Fraction(-1, 100))
    assert lo_n < hi_n


def test_domain_api_fail_closed() -> None:
    with pytest.raises(OmkRemainderError, match="out-of-domain"):
        enclosure(Fraction(0), Fraction(1, 5))
    with pytest.raises(OmkRemainderError, match="out-of-domain"):
        enclosure(Fraction(3, 4), Fraction(1, 100))
    with pytest.raises(OmkRemainderError, match="expansion is refused"):
        register_domain("omk_domain_v9", Fraction(0), Fraction(1),
                        K_ABS_MAX)
    with pytest.raises(OmkRemainderError, match="NEW version"):
        register_domain("omk_domain_v1", Fraction(0), Fraction(1, 3),
                        Fraction(1, 20))
    with pytest.raises(OmkRemainderError, match="unchanged domain"):
        register_domain("omk_domain_v2", W_BOX[0], W_BOX[1], K_ABS_MAX)
    with pytest.raises(OmkRemainderError, match="unchanged domain"):
        CompactDomain("omk_domain_v2")
    shrunk = register_domain("omk_domain_v1_test_shrink", Fraction(0),
                             Fraction(1, 3), Fraction(1, 20))
    assert shrunk.k_abs_max == Fraction(1, 20)
    with pytest.raises(OmkRemainderError, match="post-hoc expansion"):
        CompactDomain("direct-expansion", Fraction(-1), Fraction(2),
                      Fraction(1))
    with pytest.raises(OmkRemainderError, match="must be ordered"):
        register_domain("reversed", Fraction(1, 3), Fraction(0),
                        Fraction(1, 20))


def test_budget_separation_and_central_rule() -> None:
    payload = build_budget(Fraction(0), Fraction(1, 100)).as_payload()
    validate_budget(payload)
    collapsed = dict(payload, collapsed_single_number="0.001")
    with pytest.raises(OmkRemainderError, match="collapsed"):
        validate_budget(collapsed)
    incomplete = dict(payload)
    incomplete["physical_model_form"] = ""
    with pytest.raises(OmkRemainderError, match="missing typed"):
        validate_budget(incomplete)
    wrong_type = dict(payload, source_convention=1)
    with pytest.raises(OmkRemainderError, match="missing typed"):
        validate_budget(wrong_type)
    validate_report_central({
        "w": "0", "K": "1/100",
        "central": str(central_prediction(Fraction(0),
                                          Fraction(1, 100)))})
    with pytest.raises(OmkRemainderError, match="absorption"):
        validate_report_central({"w": "0", "K": "1/100",
                                 "central": "-1/250"})


@pytest.mark.parametrize(("w", "k"), [
    (Fraction(3, 4), Fraction(1, 100)),
    (Fraction(0), Fraction(1, 5)),
    (Fraction(0), Fraction(0)),
])
def test_report_central_rejects_out_of_domain_state(
    w: Fraction, k: Fraction
) -> None:
    with pytest.raises(OmkRemainderError, match="out-of-domain"):
        validate_report_central({
            "w": str(w),
            "K": str(k),
            "central": str(central_prediction(w, k)),
        })


def test_propagation_preserves_components() -> None:
    prop = propagate_to_ceiling(Fraction(1, 3), Fraction(-1, 100))
    lo, hi = (Fraction(x) for x in prop["delta_omega_k_enclosure"])
    assert lo < hi
    comps = prop["uncertainty_components"]
    for key in ("numerical_enclosure", "source_convention",
                "physical_model_form", "inhouse_conservative_rule"):
        assert comps[key]
    assert comps["collapsed_single_number"] is None
    assert "UNQUANTIFIED_CONDITIONAL" in comps["physical_model_form"]


def test_caption_gate() -> None:
    text = generate_caption(Fraction(0), Fraction(1, 100))
    lint_caption(text)
    for suffix in (" Proven uniform by" + " sampling.",
                   " A grid-verified" + " proof.",
                   " Remainder absorbed into" + " the central value.",
                   " One single combined" + " uncertainty number."):
        with pytest.raises(OmkRemainderError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr132_remainder_certificate.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_boundary_states_and_mutations() -> None:
    boundary = json.loads(
        (REPO_ROOT / "docs/generated/pr132_boundary_states.json")
        .read_text(encoding="utf-8"))
    assert len(boundary["corner_states_accepted"]) == 8
    assert boundary["out_of_trap_states_blocked"] == 4
    assert boundary["pr131_fd_probes_in_trap"] == 12
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr132_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    cert = json.loads(
        (REPO_ROOT / "docs/generated/pr132_trapping_certificate.json")
        .read_text(encoding="utf-8"))
    assert cert["certificate"]["M_exact"] == "1"
    assert cert["certificate"]["method"] == \
        "exact_fraction_interval_branch_and_bound"
    domain = json.loads(
        (REPO_ROOT / "docs/generated/pr132_domain_api.json")
        .read_text(encoding="utf-8"))
    assert all(domain["exercises"].values())
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr132_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
    assert W_BOX == (Fraction(0), Fraction(1, 2))
