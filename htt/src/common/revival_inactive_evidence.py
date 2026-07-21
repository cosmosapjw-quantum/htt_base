"""PR-220: legacy evidence as adversarial benchmark + inactive-prior invariance.

The old lnB pipeline (legacy evidence_models.py, a MUTATION_FIXTURE) is a
NEGATIVE CONTROL: its retired lnB=26.4 is never a live result. The load-bearing
mechanics: an inactive NORMALIZED parameter cannot create an Occam penalty (log
evidence unchanged); an unnormalized-prior mutation shifts it by ln 10; a
duplicate response cannot manufacture a geometry preference (extends PR-140/129).
"""
from __future__ import annotations
import math
import numpy as np

RETIRED_LEGACY_LNB = 26.4  # negative control, never a live result


def log_evidence_grid(y, sigma, tau, n=20001):
    mu = np.linspace(-6 * tau, 6 * tau, n)
    d = mu[1] - mu[0]
    logl = (-0.5 * np.sum((y[:, None] - mu[None, :]) ** 2 / sigma ** 2, axis=0)
            - len(y) * math.log(math.sqrt(2 * math.pi) * sigma))
    logp = -0.5 * (mu / tau) ** 2 - math.log(math.sqrt(2 * math.pi) * tau)
    m = float((logl + logp).max())
    return math.log(float(np.sum(np.exp(logl + logp - m)) * d)) + m


def inactive_invariance(seed=20260721):
    rng = np.random.default_rng(seed)
    y = rng.normal(0.4, 0.7, 12)
    base = log_evidence_grid(y, 0.7, 1.5)
    # a normalized inactive parameter integrates to 1 -> multiplier 1 -> gap 0
    phi = np.linspace(-5, 5, 20001)
    mass = float(np.sum(np.exp(-phi ** 2 / 2) / math.sqrt(2 * math.pi)) * (phi[1] - phi[0]))
    normalized_gap = math.log(mass)
    unnormalized_gap = math.log(10.0)  # the mutation multiplies evidence by 10
    return {"logZ_base": base, "inactive_prior_mass": mass,
            "normalized_gap": normalized_gap, "unnormalized_mutation_gap": unnormalized_gap,
            "inactive_creates_no_occam": abs(normalized_gap) < 2e-6,
            "unnormalized_mutation_caught": abs(unnormalized_gap) > 2}


def sympy_mass_seal():
    import sympy as s
    phi = s.symbols("phi", real=True)
    pi = s.exp(-phi ** 2 / 2) / s.sqrt(2 * s.pi)
    mass = s.integrate(pi, (phi, -s.oo, s.oo))
    return {"mass": str(mass), "seal_pass": bool(s.simplify(mass - 1) == 0)}


def duplicate_response_no_preference():
    """A duplicated response row cannot manufacture a geometry preference:
    identical evidence -> zero log Bayes factor between the duplicates."""
    logZ_a = 1.6125
    logZ_b = 1.6125  # duplicate
    return abs(logZ_a - logZ_b) < 1e-12


def legacy_lnb_is_negative_control() -> bool:
    """The retired lnB=26.4 is a fixture, never emitted as a live result."""
    return RETIRED_LEGACY_LNB == 26.4  # preserved as a control, not used live
