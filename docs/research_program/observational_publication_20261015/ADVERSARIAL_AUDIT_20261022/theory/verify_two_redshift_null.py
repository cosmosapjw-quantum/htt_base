"""Finite endpoint/pipeline falsifiers; standard library, no data or ODE.

Owner htt theory audit; C0 conditional analytic. Inputs are manufactured.
The exact cancellation is a metamorphic pipeline target, not a sky likelihood.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

G = 5 / math.log(10)


def chi(z: float, omega_r: float = 0.0001) -> float:
    """H0/c-scaled flat dust+radiation distance, exact algebraic background."""
    if z <= 0:
        raise ValueError("positive depth required")
    y = 1 + z
    sb = math.sqrt(omega_r + (1 - omega_r) / y)
    return 2 * z / (y * (1 + sb))


def residual(m: float, z_h: float, z_d: float) -> float:
    return m - G * math.log((1 + z_h) * chi(z_d))


def exact_tube(z: float, eta_bound: float, kappa_bound: float) -> tuple[float, float]:
    if eta_bound < 0 or kappa_bound < 0 or z <= eta_bound:
        raise ValueError("finite nonnegative bounds and positive lower depth required")
    return (
        -kappa_bound - G * math.log(chi(z + eta_bound) / chi(z)),
        kappa_bound - G * math.log(chi(z - eta_bound) / chi(z)),
    )


def main() -> dict:
    # Baseline directions are in the unprimed observer tetrad.  delta is E'/E.
    beta = (0.12, -0.09, 0.07)
    gamma = 1 / math.sqrt(1 - sum(x*x for x in beta))
    directions = [(1., 0., 0.), (0., 1., 0.), (0., 0., 1.),
                  tuple(x/math.sqrt(14) for x in (1., 2., 3.))]
    invariant_errors, redshift_only = [], []
    for n in directions:
        delta = gamma * (1 + sum(x*y for x,y in zip(beta,n)))
        for z_h,z_d in [(0.015,0.02),(0.12,0.1),(0.53,0.5)]:
            m = 20.3
            base = residual(m,z_h,z_d)
            z_h_prime = (1+z_h)/delta-1
            transformed = residual(m-G*math.log(delta),z_h_prime,z_d)
            invariant_errors.append(abs(transformed-base))
            bad = residual(m,z_h_prime,z_d)-base
            assert math.isclose(bad,G*math.log(delta),abs_tol=1e-13)
            redshift_only.append(bad)
    assert max(invariant_errors) < 2e-14

    # Exact finite interval is attained at its independent-box corners.
    z,eta_bound,kappa_bound = 0.02,0.0002,0.0005
    lo,hi = exact_tube(z,eta_bound,kappa_bound)
    differences = [kap-G*math.log(chi(z+eta)/chi(z))
                   for kap in (-kappa_bound,kappa_bound)
                   for eta in (-eta_bound,eta_bound)]
    assert math.isclose(min(differences),lo,abs_tol=1e-15)
    assert math.isclose(max(differences),hi,abs_tol=1e-15)

    # Standardized band magnitudes require their own response: for Fnu~nu^-alpha
    # a fixed observer band has F_R'=delta^(1+alpha) F_R, not delta^2 F_R.
    delta,alpha = 1.0012,0.4
    kappa = G/2*(1-alpha)*math.log(delta)
    band_shift = -G/2*(1+alpha)*math.log(delta)
    residual_shift = residual(20.3+band_shift,1.03/delta-1,0.03)-residual(20.3,0.03,0.03)
    assert math.isclose(residual_shift,kappa,abs_tol=1e-13)

    # Fixed-data inference of a candidate reference-frame correction is different
    # from a passive reboost.  Its z_D change gives a nonzero A column.
    z,eps = 0.08,1e-7
    rplus = -G*math.log(chi((1+z)*math.exp(eps)-1))
    rminus = -G*math.log(chi((1+z)*math.exp(-eps)-1))
    numerical = (rplus-rminus)/(2*eps)
    sb = math.sqrt(0.0001+0.9999/(1+z))
    A = (1+sb)/(2*z*sb)
    assert math.isclose(numerical,-G*A,rel_tol=1e-9)

    # Domain guard falsifier.
    try:
        exact_tube(0.001,0.002,0.)
    except ValueError:
        pass
    else:
        raise AssertionError("nonpositive distance endpoint accepted")

    return {
        "scope":"C0_MANUFACTURED_EXACT_KINEMATIC_PIPELINE_NULL",
        "source_commit":"76595070beb97e52dce9f2d7a0ff1dbf3c289e98",
        "calibrated_observational_test":False,
        "cases":len(invariant_errors),
        "max_exact_invariance_roundoff_mag":max(invariant_errors),
        "redshift_only_spurious_mag_range":[min(redshift_only),max(redshift_only)],
        "finite_box":{"z":0.02,"eta_bound":eta_bound,"kappa_bound_mag":kappa_bound,"residual_change_mag":[lo,hi]},
        "fixed_band_falsifier":{"alpha":alpha,"delta":delta,"residual_change_mag":residual_shift,"predicted_kappa_mag":kappa},
        "fixed_data_candidate_frame_derivative":{"numeric":numerical,"analytic":-G*A},
        "checks":"12 exact finite boosts; wrong-pipeline falsifier; attained tube endpoints; fixed-band falsifier; fixed-data derivative; domain rejection",
        "no_ode_or_catalogue_campaign":True,
    }


if __name__ == "__main__":
    result = main()
    text = json.dumps(result,indent=2,allow_nan=False)+"\n"
    Path(__file__).with_name("RESULT.json").write_text(text)
    print(text,end="")
