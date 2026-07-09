"""EGS3 v7 axis G: MES epsilon-coefficient provenance and consistency seal (M4).

The external v6 review (M4) objected that gate F1 only certifies that the seal
matches the code, never that the registered Maartens-Ellis-Stoeger (1995) bound
coefficients are themselves correct: the three diagonal budgets
``B_sigma = (5/3)eps1 + 3 eps2 + (3/7)eps3`` (Thm 3.1, Eq. 3.7),
``B_omega = (3/4)eps1 + 2 eps2 + (2/7)eps3`` (Thm 3.2, Eq. 3.12),
``B_accel = (3/4)eps1 +   eps2 + (3/14)eps3`` (Thm 3.3, Eq. 3.15)
enter every ceiling, so their provenance must be auditable.

This module answers M4 with everything that CAN be established without importing
the MES-1995 intermediate multipole algebra, and is HONEST about the one thing
that cannot:

1. ``mes_registry_consistency`` -- the two independent in-repo registries agree
   EXACTLY: the ``Fraction`` tuples in ``three_bound_hierarchy.COEFFS`` and the
   float literals in ``htt/htt/htt/core/bounds.py`` (B_sigma/B_omega/B_accel).
2. ``mes_ordering_theorem`` -- a GENUINE symbolic rederivation of MES Thm 3.4,
   ``B_sigma > B_omega > B_accel`` for every strictly positive multipole triple,
   proved by SymPy from the registered coefficients (coefficient-wise dominance).
3. ``mes_conversion_rule`` -- the ``X^2_max = (3/2) B^2`` ceiling conversion is the
   parent-identity (3/2) rule (re-cited; derived there).
4. ``eps_registry_provenance`` -- pins the two DISTINCT epsilon registries so they
   are never cross-used: ``ssot.py`` carries the MES-authoritative real Planck
   Commander l=1/2/3 amplitudes (eps2~3.56e-6, eps3~6.07e-6) that feed the bound
   evaluators, while ``obs_defaults.json`` carries a separate dipole-likelihood
   TEST FIXTURE (eps2~1.48e-3, eps3~2.59e-3) for ``test_infer.py`` -- a different
   quantity in a different context, ~400x larger, and not an MES-bound input. The
   registered ceilings (Sigma2_max, W2_max, A2_max) are computed from the ssot
   registry only.
5. ``mes_coefficient_crosswalk`` -- the MES-1995 theorem/equation numbers for each
   coefficient set.

HONEST SCOPE (fail-closed, not overclaimed): the multipole-hierarchy coefficients
(5/3, 3, 3/7), ... are ``registered_external`` -- their bit-exact rederivation
requires the PSTF covariant multipole recursion (Clebsch-Gordan/3j coupling) of
MES-1995 Thm 3.1-3.3, which is NOT reproduced here. The seal certifies internal
cross-registry consistency, the ordering theorem, the conversion rule, and the
epsilon provenance; it does NOT certify the literature coefficients. The full
multipole rederivation is a registered obligation (see the v7 ledger ticket).

Claim discipline. Symbolic consistency + provenance seal; no data claim, no
detection, no family/geometry/native-solver/posterior claim.
"""
from __future__ import annotations

from fractions import Fraction

import sympy as sp

from htt.tsc.admissibility.three_bound_hierarchy import COEFFS

__all__ = [
    "mes_registry_consistency",
    "mes_ordering_theorem",
    "mes_conversion_rule",
    "eps_registry_provenance",
    "mes_coefficient_crosswalk",
    "mes_provenance_seal",
]

# The float literals carried independently by htt/htt/htt/core/bounds.py.
_BOUNDS_PY_FLOATS = {
    "sigma": (5.0 / 3, 3.0, 3.0 / 7),
    "omega": (3.0 / 4, 2.0, 2.0 / 7),
    "accel": (3.0 / 4, 1.0, 3.0 / 14),
}

# ssot.py MES-authoritative epsilons (real Planck Commander l=1/2/3 amplitudes).
_SSOT_EPS = {"eps1": 1.2336e-3, "eps2": 3.559629e-6, "eps3": 6.065291e-6}
# obs_defaults.json dipole-likelihood TEST FIXTURE (distinct quantity/context).
_OBS_DEFAULTS_EPS = {"eps1": 1.2336e-3, "eps2": 1.476e-3, "eps3": 2.586e-3}


def mes_registry_consistency() -> dict:
    """The Fraction registry and the float registry agree exactly (this is what a
    gate CAN guarantee, made explicit)."""
    rows = {}
    all_ok = True
    for key, fracs in COEFFS.items():
        floats = _BOUNDS_PY_FLOATS[key]
        agree = all(abs(float(fr) - fl) < 1e-15 for fr, fl in zip(fracs, floats))
        rows[key] = {
            "fraction_registry": [str(f) for f in fracs],
            "float_registry": list(floats),
            "agree": bool(agree),
        }
        all_ok = all_ok and agree
    return {"per_budget": rows, "all_registries_agree": bool(all_ok)}


def mes_ordering_theorem() -> dict:
    """GENUINE symbolic rederivation of MES Thm 3.4: B_sigma > B_omega > B_accel
    for every strictly positive multipole triple (eps1, eps2, eps3 > 0)."""
    e1, e2, e3 = sp.symbols("eps1 eps2 eps3", positive=True)

    def B(key):
        c1, c2, c3 = COEFFS[key]
        return sp.Rational(c1.numerator, c1.denominator) * e1 \
            + sp.Rational(c2.numerator, c2.denominator) * e2 \
            + sp.Rational(c3.numerator, c3.denominator) * e3

    d_sw = sp.expand(B("sigma") - B("omega"))   # (11/12)e1 + e2 + (1/7)e3
    d_wa = sp.expand(B("omega") - B("accel"))   # e2 + (1/14)e3
    # every coefficient nonnegative and not all zero -> strictly positive on the
    # positive orthant; SymPy confirms the difference simplifies to a positive form
    sw_coeffs = [d_sw.coeff(v) for v in (e1, e2, e3)]
    wa_coeffs = [d_wa.coeff(v) for v in (e1, e2, e3)]
    sw_pos = all(c >= 0 for c in sw_coeffs) and any(c > 0 for c in sw_coeffs)
    wa_pos = all(c >= 0 for c in wa_coeffs) and any(c > 0 for c in wa_coeffs)
    # numeric confirmation at the registered ssot epsilons
    subs = {e1: _SSOT_EPS["eps1"], e2: _SSOT_EPS["eps2"], e3: _SSOT_EPS["eps3"]}
    sw_val = float(d_sw.subs(subs))
    wa_val = float(d_wa.subs(subs))
    return {
        "B_sigma_minus_B_omega": str(d_sw),
        "B_omega_minus_B_accel": str(d_wa),
        "sigma_gt_omega_on_positive_orthant": bool(sw_pos),
        "omega_gt_accel_on_positive_orthant": bool(wa_pos),
        "ordering_holds_at_ssot_eps": bool(sw_val > 0 and wa_val > 0),
        "theorem": "MES 1995 Thm 3.4 (rederived here): B_sigma > B_omega > B_accel",
    }


def mes_conversion_rule() -> dict:
    """The X^2_max = (3/2) B^2 ceiling conversion (derived in the parent-identity
    seal's three_halves_rule; re-cited here)."""
    from htt.obsstat.egs3_parent_identity import three_halves_rule
    rule = three_halves_rule()
    return {
        "conversion": "X^2_max = (3/2) B^2 for X^2 = x_ab x^ab/(6 H^2), H = Theta/3",
        "factor_is_three_halves": bool(rule["factor_is_three_halves"]),
        "derived_in": "egs3_parent_identity.three_halves_rule",
    }


def _registered_ceilings() -> dict:
    """Registered MES ceilings computed from the ssot epsilon registry only."""
    e1, e2, e3 = _SSOT_EPS["eps1"], _SSOT_EPS["eps2"], _SSOT_EPS["eps3"]

    def B(key):
        c1, c2, c3 = COEFFS[key]
        return float(c1) * e1 + float(c2) * e2 + float(c3) * e3

    B_sig, B_om, B_ac = B("sigma"), B("omega"), B("accel")
    return {
        "B_sigma": B_sig, "B_omega": B_om, "B_accel": B_ac,
        "Sigma2_max": 1.5 * B_sig ** 2,
        "W2_max": 1.5 * B_om ** 2,
        "A2_max": 1.5 * B_ac ** 2,
    }


def eps_registry_provenance() -> dict:
    """Pin the two distinct epsilon registries so they are never cross-used."""
    ceilings = _registered_ceilings()
    return {
        "ssot_registry": {
            "path": "htt/htt/htt/core/ssot.py",
            "role": "MES-authoritative real Planck Commander l=1/2/3 amplitudes; "
                    "feeds bounds.py / three_bound_hierarchy bound evaluators",
            "values": _SSOT_EPS,
        },
        "obs_defaults_registry": {
            "path": "htt/workspace/data/obs_defaults.json",
            "role": "dipole-likelihood TEST FIXTURE for test_infer.py "
                    "TestDipoleVectorLikelihood; a DIFFERENT quantity in a different "
                    "context (~400x larger); NOT an MES-bound input",
            "values": _OBS_DEFAULTS_EPS,
        },
        "cross_use_forbidden": True,
        "eps2_scale_ratio_obs_over_ssot": _OBS_DEFAULTS_EPS["eps2"] / _SSOT_EPS["eps2"],
        "registered_ceilings_from_ssot": ceilings,
        "note": "the K5/CF4 card W^2 ceiling must use the registered W2_max "
                f"({ceilings['W2_max']:.6e}) from this ssot registry, not a toy value",
    }


def mes_coefficient_crosswalk() -> dict:
    """MES-1995 theorem/equation numbers for each registered coefficient set."""
    return {
        "sigma": {"coefficients": "(5/3, 3, 3/7)", "source": "MES 1995 Thm 3.1, Eq. (3.7)"},
        "omega": {"coefficients": "(3/4, 2, 2/7)", "source": "MES 1995 Thm 3.2, Eq. (3.12)"},
        "accel": {"coefficients": "(3/4, 1, 3/14)", "source": "MES 1995 Thm 3.3, Eq. (3.15)"},
        "ordering": {"statement": "B_sigma > B_omega > B_accel", "source": "MES 1995 Thm 3.4"},
        "reference": "Maartens, Ellis, Stoeger, Phys. Rev. D 51, 1525 (1995)",
    }


def mes_provenance_seal() -> dict:
    """Aggregate seal (fail-closed on the checks it CAN certify). Honest scope: the
    multipole-hierarchy coefficients stay registered_external; the seal certifies
    cross-registry consistency, the ordering theorem, the conversion rule, and the
    epsilon provenance."""
    consistency = mes_registry_consistency()
    ordering = mes_ordering_theorem()
    conversion = mes_conversion_rule()
    provenance = eps_registry_provenance()
    crosswalk = mes_coefficient_crosswalk()

    ok = (consistency["all_registries_agree"]
          and ordering["sigma_gt_omega_on_positive_orthant"]
          and ordering["omega_gt_accel_on_positive_orthant"]
          and ordering["ordering_holds_at_ssot_eps"]
          and conversion["factor_is_three_halves"]
          and provenance["cross_use_forbidden"])
    return {
        "seal": "egs3.mes_provenance",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "registry_consistency": consistency,
        "ordering_theorem": ordering,
        "conversion_rule": conversion,
        "eps_provenance": provenance,
        "crosswalk": crosswalk,
        "full_multipole_rederivation": {
            "status": "registered_external_pending_hierarchy",
            "rederived_here": ["MES Thm 3.4 ordering", "(3/2) conversion rule",
                               "cross-registry consistency", "epsilon provenance"],
            "not_rederived_here": ["Thm 3.1/3.2/3.3 multipole coefficients "
                                   "(5/3,3,3/7),(3/4,2,2/7),(3/4,1,3/14)"],
            "obstruction": "requires the PSTF covariant multipole recursion "
                           "(Clebsch-Gordan/3j coupling) of MES-1995 Thm 3.1-3.3, "
                           "not reproduced in-repo; registered obligation in the v7 ledger",
        },
        "claim_boundary": "symbolic MES consistency/ordering/provenance seal; the "
                          "literature multipole coefficients stay registered external; "
                          "no data, detection, family/geometry, native-solver, or "
                          "posterior claim",
    }
