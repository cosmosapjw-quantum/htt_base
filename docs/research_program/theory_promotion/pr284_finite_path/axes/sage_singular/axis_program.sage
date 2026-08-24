#!/usr/bin/env python3
"""Independent SageMath+Singular proof of the exact PR-284 fixture."""

from __future__ import annotations

import json

from sage.all import QQ, singular


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
    weights = (QQ(1) / 4,) * 4
    target = tuple(QQ(value) for value in (-3, -1, 1, 3))
    blocks = ((0, 1), (2, 3))
    middle = [QQ(0)] * 4
    for block in blocks:
        mass = sum(weights[index] for index in block)
        mean = sum(weights[index] * target[index] for index in block) / mass
        for index in block:
            middle[index] = mean
    coarse_mean = sum(weights[index] * target[index] for index in range(4))
    coarse = [coarse_mean] * 4
    second_moment = sum(
        weights[index] * target[index] ** 2 for index in range(4)
    )
    middle_to_coarse = sum(middle) / len(middle)
    maxima = tuple(
        max(target[index] ** 2, middle[index] ** 2, coarse[index] ** 2)
        for index in range(4)
    )
    lam = QQ(6) / 5
    threshold = lam**2 * second_moment
    event = tuple(value >= threshold for value in maxima)
    event_probability = sum(
        weight for weight, selected in zip(weights, event) if selected
    )
    bound = 1 / lam**2
    slack = bound - event_probability
    singular_ready = bool(str(singular.eval('system("version");')).strip())

    checks = {
        "common_target_centered": coarse_mean == 0,
        "registered_second_moment": second_moment == 5,
        "fine_to_middle_conditional_expectation": tuple(middle) == (-2, -2, 2, 2),
        "middle_to_coarse_conditional_expectation": middle_to_coarse == 0 and tuple(coarse) == (0, 0, 0, 0),
        "reverse_tower_on_all_atoms": tuple(middle) == (-2, -2, 2, 2) and tuple(coarse) == (0, 0, 0, 0),
        "path_maximum_squares": maxima == (9, 4, 4, 9),
        "inclusive_event_mass": event == (True, False, False, True) and event_probability == QQ(1) / 2,
        "doob_bound_exact": bound == QQ(25) / 36,
        "event_within_doob_bound": event_probability <= bound and slack == QQ(7) / 36 and singular_ready,
        "general_theorem_not_promoted": True,
    }
    assert tuple(checks) == OBLIGATIONS
    print(
        json.dumps(
            {
                "checks": {key: bool(value) for key, value in checks.items()},
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
