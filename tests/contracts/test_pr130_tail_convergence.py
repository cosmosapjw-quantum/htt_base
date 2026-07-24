"""PR-130 contract tests: NT2 tail convergence vs sufficiency."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.nt2_tail_convergence import (
    FACTORIZATION_REGISTRY,
    PROFILE_P_REGISTERED,
    Nt2TailError,
    certified_tail_enclosure,
    closed_form_infinite_mpmath,
    divergence_witness_p1,
    fisher_term_exact,
    generate_caption,
    lint_caption,
    partial_sum_exact,
    require_convergent_profile,
    tail_bracket_exact,
    tail_positive_witness,
    three_engine_enclosure,
    validate_sufficiency_claim,
    validate_truncation_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr130_tail_convergence.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr130", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_current_tail_source_measurements_are_generation_time() -> None:
    runner = _load_runner()
    source = runner.TAIL_SOURCE
    theorem = runner.OUTPUTS["theorem"]
    stored = {
        "negative_scan": {
            "targets": {
                source: {
                    "sha256": "1" * 64,
                    "lines_scanned": 10,
                    "hits": [],
                }
            }
        }
    }
    current = {
        "negative_scan": {
            "targets": {
                source: {
                    "sha256": "2" * 64,
                    "lines_scanned": 20,
                    "hits": [],
                }
            }
        }
    }
    assert runner._semantic_artifact(
        theorem, stored
    ) == runner._semantic_artifact(theorem, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        theorem, stored
    ) != runner._semantic_artifact(theorem, current)


def test_manifest_tail_source_hash_is_generation_time() -> None:
    runner = _load_runner()
    source = runner.TAIL_SOURCE
    legacy = "htt/obsstat/egs2_fisher.py"
    manifest = runner.OUTPUTS["manifest"]
    stored = {
        "input_hashes": [
            f"{source}:{'1' * 64}",
            f"{legacy}:{'2' * 64}",
        ]
    }
    current = {
        "input_hashes": [
            f"{source}:{'3' * 64}",
            f"{legacy}:{'2' * 64}",
        ]
    }
    assert runner._semantic_artifact(
        manifest, stored
    ) == runner._semantic_artifact(manifest, current)
    current["input_hashes"][1] = f"{legacy}:{'4' * 64}"
    assert runner._semantic_artifact(
        manifest, stored
    ) != runner._semantic_artifact(manifest, current)


def test_registered_profile_and_exact_terms() -> None:
    assert PROFILE_P_REGISTERED == Fraction(3, 2)
    # t_l = (2l+1)/2 * (2/l)^3 = 8/l^2 + 4/l^3 exactly
    assert fisher_term_exact(2) == Fraction(8, 4) + Fraction(4, 8)
    assert fisher_term_exact(3) == Fraction(8, 9) + Fraction(4, 27)
    assert partial_sum_exact(2, 3) == \
        fisher_term_exact(2) + fisher_term_exact(3)


def test_convergence_domain_boundary() -> None:
    require_convergent_profile(Fraction(3, 2))
    require_convergent_profile(Fraction(101, 100))
    for p in (Fraction(1), Fraction(1, 2), Fraction(0)):
        with pytest.raises(Nt2TailError, match="outside the convergence"):
            require_convergent_profile(p)


@pytest.mark.parametrize("f_sky", [
    Fraction(0), Fraction(-1), Fraction(3, 2),
])
def test_invalid_sky_fraction_fails_closed(f_sky: Fraction) -> None:
    for call in (
        lambda: fisher_term_exact(2, f_sky),
        lambda: tail_bracket_exact(80, f_sky),
        lambda: closed_form_infinite_mpmath(Fraction(3, 2), f_sky),
        lambda: divergence_witness_p1(f_sky=f_sky),
    ):
        with pytest.raises(Nt2TailError, match="f_sky"):
            call()


def test_tail_bracket_and_strict_positivity() -> None:
    for L in (10, 80, 500):
        lower, upper = tail_bracket_exact(L)
        assert Fraction(0) < lower < upper
        witness = tail_positive_witness(L)
        assert witness > 0
        # the single-term witness sits below the certified upper bound
        assert witness < upper
    # the bracket actually contains the certified enclosure of the tail
    lo80, up80 = tail_bracket_exact(80)
    enc_lo, enc_hi = certified_tail_enclosure(80, 5000)
    assert lo80 < enc_lo < enc_hi < up80


def test_three_engine_enclosure_agrees() -> None:
    result = three_engine_enclosure(2000)
    assert result["sympy_identity_vanishes"] is True
    lo = float(result["enclosure_lower_50_digits_display"])
    hi = float(result["enclosure_upper_50_digits_display"])
    mp = float(result["mpmath_closed_form_50_digits"])
    assert lo <= mp <= hi


def test_sufficiency_gate_fail_closed() -> None:
    assert FACTORIZATION_REGISTRY == {}
    validate_sufficiency_claim({"asserts": "tail converges at O(1/L)"})
    with pytest.raises(Nt2TailError, match="never an accepted basis"):
        validate_sufficiency_claim({
            "asserts": "the pair is " + "sufficient for inference",
            "basis": "tail_fraction_small"})
    with pytest.raises(Nt2TailError, match="registry is empty"):
        validate_sufficiency_claim({
            "asserts": "octupole sufficiency established",
            "factorization_proof_reference": "THM-UNREGISTERED"})
    with pytest.raises(Nt2TailError, match="registry is empty"):
        validate_sufficiency_claim({
            "asserts": "no information" + " beyond the octupole"})


def test_sufficiency_gate_rejects_completeness_synonyms() -> None:
    # the adversarial-lane synonym bypass: completeness paraphrases
    for phrase in ("the pair (a2,a3) is a complete" + " statistic for F",
                   "the set exhausts the" + " information",
                   "the pair captures all" + " information",
                   "a lossless" + " summary of the likelihood",
                   "the pair fully determines" + " the likelihood"):
        with pytest.raises(Nt2TailError):
            validate_sufficiency_claim({"asserts": phrase,
                                        "basis": "tail_fraction_small"})


def test_gate_exempts_explicit_insufficiency() -> None:
    # the mandated anti-sufficiency reading must not be blocked
    validate_sufficiency_claim({
        "asserts": "L = 80 alone is insufficient; higher multipoles "
                   "carry information"})


def test_factorization_registration_typed_and_toy_barred() -> None:
    from common.nt2_tail_convergence import (TOY_FAMILY_ID,
                                             register_factorization)
    with pytest.raises(Nt2TailError, match="permanently barred"):
        register_factorization("THM-X", TOY_FAMILY_ID,
                               "docs/SSOT_POLICY.md", "reviewer")
    with pytest.raises(Nt2TailError, match="existing proof artifact"):
        register_factorization("THM-X", "other_family",
                               "docs/NO_SUCH_FILE.md", "reviewer")
    # even a hand-inserted untyped entry cannot unlock a claim, and a
    # typed entry for another family never binds the toy family
    FACTORIZATION_REGISTRY["fake"] = "no proof"
    try:
        with pytest.raises(Nt2TailError):
            validate_sufficiency_claim({
                "asserts": "is sufficient" + " for inference",
                "factorization_proof_reference": "fake"})
        FACTORIZATION_REGISTRY["typed"] = {
            "family_id": "other_family", "proof_artifact": "x",
            "reviewed_by": "r"}
        with pytest.raises(Nt2TailError, match="does not bind"):
            validate_sufficiency_claim({
                "asserts": "is sufficient" + " for inference",
                "factorization_proof_reference": "typed",
                "family": "registered_toy_response"})
    finally:
        FACTORIZATION_REGISTRY.clear()


def test_truncation_claim_understatement_killed() -> None:
    lower, _ = tail_bracket_exact(80)
    # the bracket is STRICT, so a claim AT the lower bound provably
    # understates the tail and is rejected (adversarial-lane boundary fix)
    with pytest.raises(Nt2TailError, match="understatement"):
        validate_truncation_claim(lower, 80)
    validate_truncation_claim(lower + Fraction(1, 10**9), 80)
    with pytest.raises(Nt2TailError, match="understatement"):
        validate_truncation_claim(Fraction(1, 1000), 80)
    with pytest.raises(Nt2TailError, match="understatement"):
        validate_truncation_claim(Fraction(0), 80)


def test_caption_lint_kills_sufficiency_language() -> None:
    text = generate_caption(80)
    lint_caption(text)
    for suffix in (" This set is " + "sufficient for F.",
                   " Rao-" + "Blackwell complete.",
                   " No information" + " beyond L."):
        with pytest.raises(Nt2TailError, match="forbidden"):
            lint_caption(text + suffix)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr130_tail_convergence.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_wrong_constant_killed_by_production_validator() -> None:
    with pytest.raises(Nt2TailError, match="outside the certified"):
        three_engine_enclosure(500, closed_form_shift=Fraction(8))


def test_relabeled_surfaces_carry_supersession_markers() -> None:
    record = json.loads(
        (REPO_ROOT / "docs/generated/pr130_legacy_invalidation.json")
        .read_text(encoding="utf-8"))
    relabeled = {r["path"]: r for r in record["relabeled_active_surfaces"]}
    assert len(relabeled) == 3
    for path, row in relabeled.items():
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert row["marker"] in text


def test_legacy_module_stays_byte_frozen() -> None:
    import hashlib

    import yaml

    spec = yaml.safe_load(
        (REPO_ROOT /
         "docs/research_program/long_horizon_rescue/pr130_spec.yaml")
        .read_text(encoding="utf-8"))
    legacy = spec["legacy_invalidation"]
    digest = hashlib.sha256(
        (REPO_ROOT / legacy["legacy_module"]).read_bytes()).hexdigest()
    assert digest == legacy["legacy_module_sha256"]
    record = json.loads(
        (REPO_ROOT / "docs/generated/pr130_legacy_invalidation.json")
        .read_text(encoding="utf-8"))
    assert record["byte_frozen"] is True
    assert record["finding_status"] == "OPEN"
    assert len(record["superseded_lines"]) == 3


def test_artifacts_probes_mutations_manifest() -> None:
    theorem = json.loads(
        (REPO_ROOT / "docs/generated/pr130_tail_theorem.json")
        .read_text(encoding="utf-8"))
    assert theorem["tail_strictly_positive_at_every_probe"] is True
    assert theorem["factorization_registry_state"] == "EMPTY"
    assert len(theorem["truncation_probes"]) == 5
    assert theorem["negative_scan"]["total_hits"] == 0
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr130_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    sensitivity = json.loads(
        (REPO_ROOT / "docs/generated/pr130_profile_sensitivity.json")
        .read_text(encoding="utf-8"))
    assert [row["p"] for row in sensitivity["rows"]] == ["5/4", "3/2", "2"]
    assert sensitivity["divergent_boundary"]["verdict"] == \
        "divergent_excluded"
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr130_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
