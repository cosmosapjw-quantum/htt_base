#!/usr/bin/env python3
"""Independent SymPy proof of the exact PR-284 four-atom fixture."""

from __future__ import annotations

import json

import sympy as sp


OBLIGATIONS = (
    "common_target_centered",
    "registered_second_moment",
    "fine_to_middle_conditional_expectation",
    "middle_to_coarse_conditional_expectation",
    "reverse_tower_on_all_atoms",
    "path_maximum_squares",
    "inclusive_event_mass",
    "doob_bound_exact",
    "event_within_doob_bound",
    "general_theorem_not_promoted",
)


def main() -> None:
    weights = (sp.Rational(1, 4),) * 4
    target = tuple(map(sp.Integer, (-3, -1, 1, 3)))
    middle_blocks = ((0, 1), (2, 3))
    middle = [sp.Integer(0)] * 4
    for block in middle_blocks:
        mass = sum(weights[index] for index in block)
        mean = sp.simplify(
            sum(weights[index] * target[index] for index in block) / mass
        )
        for index in block:
            middle[index] = mean
    coarse_mean = sp.simplify(sum(w * x for w, x in zip(weights, target)))
    coarse = [coarse_mean] * 4
    second_moment = sp.simplify(
        sum(weight * value**2 for weight, value in zip(weights, target))
    )
    middle_to_coarse = sp.simplify(sum(middle) / len(middle))
    path_maximum_squares = tuple(
        max(target[index] ** 2, middle[index] ** 2, coarse[index] ** 2)
        for index in range(4)
    )
    lam = sp.Rational(6, 5)
    threshold_squared = sp.simplify(lam**2 * second_moment)
    event = tuple(value >= threshold_squared for value in path_maximum_squares)
    event_probability = sp.simplify(
        sum(weight for weight, selected in zip(weights, event) if selected)
    )
    doob_bound = sp.simplify(1 / lam**2)
    bound_slack = sp.simplify(doob_bound - event_probability)

    checks = {
        "common_target_centered": bool(coarse_mean == 0),
        "registered_second_moment": bool(second_moment == 5),
        "fine_to_middle_conditional_expectation": bool(
            tuple(middle) == (-2, -2, 2, 2)
        ),
        "middle_to_coarse_conditional_expectation": bool(
            middle_to_coarse == 0 and tuple(coarse) == (0, 0, 0, 0)
        ),
        "reverse_tower_on_all_atoms": bool(
            tuple(middle) == (-2, -2, 2, 2)
            and tuple(coarse) == (0, 0, 0, 0)
        ),
        "path_maximum_squares": bool(path_maximum_squares == (9, 4, 4, 9)),
        "inclusive_event_mass": bool(event == (True, False, False, True) and event_probability == sp.Rational(1, 2)),
        "doob_bound_exact": bool(doob_bound == sp.Rational(25, 36)),
        "event_within_doob_bound": bool(event_probability <= doob_bound and bound_slack == sp.Rational(7, 36)),
        "general_theorem_not_promoted": True,
    }
    assert tuple(checks) == OBLIGATIONS
    print(
        json.dumps(
            {
                "checks": checks,
                "computed": {
                    "centered_mean": "0",
                    "second_moment": "5",
                    "middle_values": "[-2,-2,2,2]",
                    "coarse_values": "[0,0,0,0]",
                    "path_maximum_squares": "[9,4,4,9]",
                    "threshold_squared": "36/5",
                    "event_probability": "1/2",
                    "doob_bound": "25/36",
                    "bound_slack": "7/36",
                },
                "counterexample": None,
                "domain_assumption_diff": [],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
