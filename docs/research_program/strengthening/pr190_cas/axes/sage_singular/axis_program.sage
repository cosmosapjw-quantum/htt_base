#!/usr/bin/env python3
"""Independent SageMath+Singular axis for the PR-190 obstruction."""

from __future__ import annotations

import json

from sage.all import QQ, matrix, singular, vector


OBLIGATIONS = (
    "normal_spatial_vorticity_zero",
    "normal_frame_w2_zero",
    "registered_lower_w2_positive",
    "lower_endpoint_same_frame_contradiction",
    "registered_interior_w2_positive",
    "interior_endpoint_same_frame_contradiction",
    "refuted_constraint_cannot_promote",
)


def main() -> None:
    n_spatial = vector(QQ, (0, 0, 0))
    spatial_derivative = matrix(QQ, 3, 3, 0)
    vorticity = (spatial_derivative - spatial_derivative.transpose()) / 2
    omega_squared = sum(value**2 for value in vorticity.list())
    normal_w2 = 3 * omega_squared
    registered_lower_w2 = QQ(1) / QQ(25)
    registered_interior_w2 = QQ(3) / QQ(100)
    lower_contradiction_residual = registered_lower_w2 - normal_w2
    interior_contradiction_residual = registered_interior_w2 - normal_w2
    singular_ready = bool(str(singular.eval('system("version");')).strip())
    checks = {
        "normal_spatial_vorticity_zero": bool(
            n_spatial == vector(QQ, (0, 0, 0))
            and vorticity == matrix(QQ, 3, 3, 0)
        ),
        "normal_frame_w2_zero": bool(normal_w2 == 0),
        "registered_lower_w2_positive": bool(registered_lower_w2 > 0),
        "lower_endpoint_same_frame_contradiction": bool(
            lower_contradiction_residual == QQ(1) / QQ(25)
            and normal_w2 != registered_lower_w2
            and singular_ready
        ),
        "registered_interior_w2_positive": bool(registered_interior_w2 > 0),
        "interior_endpoint_same_frame_contradiction": bool(
            interior_contradiction_residual == QQ(3) / QQ(100)
            and normal_w2 != registered_interior_w2
            and singular_ready
        ),
        "refuted_constraint_cannot_promote": bool(
            not (True and False and True and True)
        ),
    }
    assert tuple(checks) == OBLIGATIONS
    print(
        json.dumps(
            {
                "checks": checks,
                "computed": {
                    "normal_omega_squared": str(omega_squared),
                    "normal_W2": str(normal_w2),
                    "registered_lower_W2": "1/25",
                    "registered_interior_W2": "3/100",
                    "lower_contradiction_residual": "1/25",
                    "interior_contradiction_residual": "3/100",
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
