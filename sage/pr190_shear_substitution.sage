"""Independent SageMath+Singular axis for PR-190 exact obligations."""

import json

s, z = var("s z")
d = s + (1 - s) * z
sigma = s / d
omega = (1 - s) * z / d
sigma_prime = 3 * z * diff(sigma, z)
log_hubble_prime = -3 + QQ(3) / 2 * (1 - s) * z / d


def component_vector(s_value, t_value):
    return {
        "Sigma2": QQ(1) / 10 + t_value / 50,
        "W2": QQ(3) / 100 + 3 * t_value / 200,
        "Omega_tilt": QQ(1) / 50 + s_value / 100,
        "DeltaOmega_k": -QQ(1) / 100 + s_value / 100 - t_value / 200,
    }


def candidate(x_value):
    return {
        "Sigma2": x_value,
        "W2": QQ(0),
        "Omega_tilt": QQ(0),
        "DeltaOmega_k": QQ(0),
    }


def x_c(vector):
    return (
        vector["Sigma2"]
        - vector["W2"]
        + vector["Omega_tilt"]
        + vector["DeltaOmega_k"]
    )


def gap(left, right):
    return max(abs(left[key] - right[key]) for key in left)


# Singular independently reduces the cross-multiplied identity numerators.
singular.eval("ring r=0,(s,z),dp;")
singular.eval("poly D=s+(1-s)*z;")
singular_gauss = singular.eval("reduce(s+(1-s)*z-D,std(ideal(0)));").strip()
singular_logistic = singular.eval(
    "reduce(-3*s*(1-s)*z+3*s*(D-s),std(ideal(0)));"
).strip()
singular_hubble = singular.eval(
    "reduce(-6*D+3*(1-s)*z+3*D+3*s,std(ideal(0)));"
).strip()

lower_target = component_vector(QQ(0), -QQ(2) / 3)
upper_target = component_vector(QQ(1), QQ(0))
lower_candidate = candidate(QQ(2) / 25)
upper_candidate = candidate(QQ(1) / 10)

checks = {
    "dust_gauss_constraint_identity": bool(
        (sigma + omega - 1).simplify_full() == 0 and singular_gauss == "0"
    ),
    "dust_logistic_evolution_identity": bool(
        (sigma_prime + 3 * sigma * (1 - sigma)).simplify_full() == 0
        and singular_logistic == "0"
    ),
    "dust_hubble_evolution_identity": bool(
        (log_hubble_prime + QQ(3) / 2 * (1 + sigma)).simplify_full() == 0
        and singular_hubble == "0"
    ),
    "lower_scalar_match_component_gap": bool(
        x_c(lower_target) == x_c(lower_candidate) == QQ(2) / 25
        and gap(lower_target, lower_candidate) == QQ(1) / 50
        and lower_target["Omega_tilt"] == QQ(1) / 50
    ),
    "upper_scalar_match_component_gap": bool(
        x_c(upper_target) == x_c(upper_candidate) == QQ(1) / 10
        and gap(upper_target, upper_candidate) == QQ(3) / 100
        and upper_target["Omega_tilt"] == QQ(3) / 100
    ),
}
payload = {
    "checks": checks,
    "domain_assumption_diff": [],
    "computed": {
        "lower_x_c": "2/25",
        "upper_x_c": "1/10",
        "lower_component_gap": "1/50",
        "upper_component_gap": "3/100",
    },
    "counterexample": None,
}
print(json.dumps(payload, sort_keys=True))
if not all(checks.values()):
    import sys

    sys.exit(2)
