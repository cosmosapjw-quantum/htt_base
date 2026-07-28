#!/usr/bin/env python3
"""Independent exact oracle for the PR-254 J1/J2 counterexamples.

This script intentionally does not import ``common.anchor_geometry``.  It
recomputes the two bounded counterexamples with exact ``Fraction`` arithmetic
and can either write or verify the frozen JSON receipt.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = (
    REPO
    / "docs/generated/pr254_anchor_geometry/counterexample_oracle.json"
)


def _fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else str(value)


def _marginal(
    law: tuple[tuple[tuple[Fraction, Fraction], Fraction], ...],
    coordinate: int,
) -> dict[str, str]:
    totals: dict[Fraction, Fraction] = {}
    for pair, probability in law:
        value = pair[coordinate]
        totals[value] = totals.get(value, Fraction(0)) + probability
    return {
        _fraction(value): _fraction(probability)
        for value, probability in sorted(totals.items())
    }


def _exceedance_probability(
    law: tuple[tuple[tuple[Fraction, Fraction], Fraction], ...],
) -> Fraction:
    return sum(
        (
            probability
            for (numerator, anchor), probability in law
            if numerator / anchor > 1
        ),
        Fraction(0),
    )


def build_payload() -> dict[str, object]:
    half = Fraction(1, 2)
    physical_radius = half
    anchor_a_radius = Fraction(1)
    anchor_b_radius = Fraction(2)
    probe = half
    rho_a = abs(probe) / anchor_a_radius
    rho_b = abs(probe) / anchor_b_radius
    containment_a = physical_radius <= anchor_a_radius
    containment_b = physical_radius <= anchor_b_radius

    comonotone = (
        ((Fraction(1), Fraction(1)), half),
        ((Fraction(2), Fraction(2)), half),
    )
    countermonotone = (
        ((Fraction(1), Fraction(2)), half),
        ((Fraction(2), Fraction(1)), half),
    )
    numerator_marginal_a = _marginal(comonotone, 0)
    numerator_marginal_b = _marginal(countermonotone, 0)
    anchor_marginal_a = _marginal(comonotone, 1)
    anchor_marginal_b = _marginal(countermonotone, 1)
    same_marginals = (
        numerator_marginal_a == numerator_marginal_b
        and anchor_marginal_a == anchor_marginal_b
    )
    comonotone_exceedance = _exceedance_probability(comonotone)
    countermonotone_exceedance = _exceedance_probability(countermonotone)

    checks = {
        "j1_both_outer_containments_hold": containment_a and containment_b,
        "j1_gauges_differ_on_same_state": rho_a != rho_b,
        "j1_neither_anchor_equals_physical_set": (
            anchor_a_radius != physical_radius
            and anchor_b_radius != physical_radius
        ),
        "j2_joint_laws_have_same_marginals": same_marginals,
        "j2_exceedance_laws_differ": (
            comonotone_exceedance != countermonotone_exceedance
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"counterexample oracle failed: {checks}")
    return {
        "schema_version": "pr254.counterexample_oracle.v1",
        "arithmetic": "exact_fraction",
        "checks": checks,
        "j1_exact": {
            "claim_id": "J1-EXACT",
            "scope": (
                "outer-envelope implication without an independent physical "
                "equality axiom"
            ),
            "physical_radius": _fraction(physical_radius),
            "anchor_a_radius": _fraction(anchor_a_radius),
            "anchor_b_radius": _fraction(anchor_b_radius),
            "probe": _fraction(probe),
            "rho_a": _fraction(rho_a),
            "rho_b": _fraction(rho_b),
            "gate_outcome": "COUNTEREXAMPLE_FOUND",
            "disposition": "REFUTED_OR_RESTRICTED",
        },
        "j2_exact": {
            "claim_id": "J2-UNIFORM",
            "scope": (
                "joint-law-free or marginal-only calibration over a "
                "composite null"
            ),
            "numerator_marginal": numerator_marginal_a,
            "anchor_marginal": anchor_marginal_a,
            "comonotone_exceedance_probability": _fraction(
                comonotone_exceedance
            ),
            "countermonotone_exceedance_probability": _fraction(
                countermonotone_exceedance
            ),
            "gate_outcome": "COUNTEREXAMPLE_FOUND",
            "disposition": "REFUTED_OR_RESTRICTED",
        },
        "claim_boundary": {
            "allowed": [
                "restrict the general J1-EXACT conjecture",
                "require a registered joint numerator-anchor law",
                "restrict joint-law-free J2-UNIFORM calibration",
            ],
            "forbidden": [
                "claim no narrower physical MES theorem can exist",
                "claim every registered joint-law test is invalid",
                "promote raw excess to calibrated evidence",
                "claim FLRW proximity, departure detection, or family identification",
            ],
        },
    }


def _serialized(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    output = args.out if args.out.is_absolute() else REPO / args.out
    expected = _serialized(build_payload())
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected, encoding="utf-8")
        print(output.relative_to(REPO))
        return 0
    if not output.is_file():
        raise SystemExit(f"missing counterexample receipt: {output}")
    actual = output.read_text(encoding="utf-8")
    if actual != expected:
        raise SystemExit("counterexample receipt drifted from exact oracle")
    print("PR254_COUNTEREXAMPLE_ORACLE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
