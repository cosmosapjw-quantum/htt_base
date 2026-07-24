"""PR-128 contract tests: NT2 coefficient authority."""
from __future__ import annotations

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.nt2_bracket_authority import (
    KAPPA_REGISTERED,
    Nt2AuthorityError,
    build_authority_bracket,
    f_lo,
    require_bracket_agreement,
    require_claimed_lower_direction,
    require_direction,
    require_registered_kappa,
    seeded_admissible_draws,
    sigma_bracket,
    validate_interval_claim,
)
from scripts.codex_harness import run_pr128_nt2_authority as pr128_runner

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_direct_witness_pins_reciprocal_entry() -> None:
    """delta = 0: the bracket degenerates to Sigma = a2/kappa exactly —
    NOT the legacy a2*kappa."""
    sigma = Fraction(1, 10**6)
    a2 = KAPPA_REGISTERED * sigma
    lower, upper = require_bracket_agreement(a2, Fraction(0))
    assert lower == upper == sigma
    assert lower == a2 / KAPPA_REGISTERED
    assert lower != a2 * KAPPA_REGISTERED
    # the understatement factor of the legacy form is exactly (21/4)^2
    assert (a2 / KAPPA_REGISTERED) / (a2 * KAPPA_REGISTERED) == \
        Fraction(441, 16)


def test_bracket_contains_truth_for_seeded_draws_interior() -> None:
    interior = 0
    for draw in seeded_admissible_draws(16):
        lower, upper = require_bracket_agreement(draw["a2"], draw["a3"])
        assert lower <= draw["sigma"] <= upper
        if lower < draw["sigma"] < upper:
            interior += 1
    assert interior >= 14  # draws test the interior, not just endpoints


def test_engine_consensus_gate() -> None:
    from common.nt2_bracket_authority import require_engine_consensus

    a2, a3 = Fraction(1, 10**6), Fraction(1, 10**7)
    endpoints = sigma_bracket(a2, a3)
    with pytest.raises(Nt2AuthorityError, match="BOTH engines"):
        require_engine_consensus({"fraction_numeric": endpoints})
    with pytest.raises(Nt2AuthorityError, match="disagree"):
        require_engine_consensus({
            "fraction_numeric": endpoints,
            "sympy_symbolic": (endpoints[0] * 2, endpoints[1]),
        })


def test_theorem_upper_containment_guard() -> None:
    from common.nt2_bracket_authority import validate_theorem_upper

    a2 = Fraction(1, 10**6)
    a3 = a2 / 2   # R = 1/2 -> theorem upper = 10.5 * a2
    with pytest.raises(Nt2AuthorityError, match="excludes admissible"):
        validate_theorem_upper(Fraction(9) * a2, a2, a3)
    validate_theorem_upper(Fraction(11) * a2, a2, a3)


def test_direction_checks() -> None:
    require_direction()
    a2, a3 = Fraction(1, 10**6), Fraction(1, 10**7)
    lo_k, _ = sigma_bracket(a2, a3, KAPPA_REGISTERED)
    lo_2k, _ = sigma_bracket(a2, a3, KAPPA_REGISTERED * 2)
    assert lo_2k < lo_k  # reciprocal entry: decreasing in kappa
    with pytest.raises(Nt2AuthorityError, match="reciprocal-wrong"):
        require_claimed_lower_direction(lo_2k, lo_k)


def test_domain_rejections() -> None:
    with pytest.raises(Nt2AuthorityError, match="zero/"):
        sigma_bracket(Fraction(1, 10**6), Fraction(1, 10**6))  # R = 1
    with pytest.raises(Nt2AuthorityError, match="strictly positive"):
        sigma_bracket(Fraction(1, 10**6), Fraction(0), Fraction(0))
    with pytest.raises(Nt2AuthorityError, match="strictly positive"):
        sigma_bracket(Fraction(-1, 10**6), Fraction(0))
    with pytest.raises(Nt2AuthorityError, match="nonnegative"):
        sigma_bracket(Fraction(1, 10**6), Fraction(-1, 10**7))


def test_specification_pin_rejects_output_matching_kappa() -> None:
    with pytest.raises(Nt2AuthorityError, match="specification-first"):
        require_registered_kappa(KAPPA_REGISTERED * Fraction(16, 441))


def test_placeholder_never_merges() -> None:
    bracket = build_authority_bracket(Fraction(1, 10**6), Fraction(1, 10**7),
                                      c_up_placeholder=Fraction(9))
    payload = bracket.as_payload()
    assert payload["merged"] is False
    assert payload["mes_placeholder_provenance"] == "placeholder_not_merged"
    with pytest.raises(Nt2AuthorityError, match="forbidden"):
        validate_interval_claim({"merged": True})


def test_f_lo_uses_corrected_lower() -> None:
    a2, a3 = Fraction(1, 10**6), Fraction(0)
    lower, _ = require_bracket_agreement(a2, a3)
    from common.nt2_bracket_authority import X_MAX_REGISTERED
    assert X_MAX_REGISTERED == Fraction(925, 100000000)
    assert f_lo(a2, a3) == lower * lower / X_MAX_REGISTERED


def test_manifest_authority_hash_is_generation_time_provenance() -> None:
    source = pr128_runner.AUTHORITY_SOURCE
    legacy = "htt/obsstat/egs2_shear_bracket.py"
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
    manifest = pr128_runner.OUTPUTS["manifest"]
    assert pr128_runner._semantic_artifact(
        manifest, stored
    ) == pr128_runner._semantic_artifact(manifest, current)

    current["input_hashes"][1] = f"{legacy}:{'4' * 64}"
    assert pr128_runner._semantic_artifact(
        manifest, stored
    ) != pr128_runner._semantic_artifact(manifest, current)


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr128_nt2_authority.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_invalidation_and_mutations() -> None:
    table = json.loads(
        (REPO_ROOT / "docs/generated/pr128_invalidation_table.json")
        .read_text(encoding="utf-8"))
    assert "reciprocal-wrong" in table["before_legacy"]["form"]
    assert "registered inversion" in table["after_authority"]["form"]
    assert len(table["consumers"]) == 6
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr128_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    randomized = json.loads(
        (REPO_ROOT / "docs/generated/pr128_randomized_bracket_report.json")
        .read_text(encoding="utf-8"))
    assert randomized["contained_exactly"] == 64
