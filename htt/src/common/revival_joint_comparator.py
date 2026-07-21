"""PR-215: general joint feasible-set support theorem (RESCUE -> PR-189).

The general support theorem (I_C = [inf_F c^T g, sup_F c^T g], product box a
factorized corollary) is closed with five-axis CAS in PR-189. This card is the
instantiation on the ACTUAL comparator carrier (Sigma2, W2, Omega_tilt,
DeltaOmega_k) over a coupled 2-parameter feasible manifold, showing the joint
interval is strictly narrower than the marginal product box, plus the PR-189
cross-reference. Exact arithmetic over Fractions; a grid gives the second lineage.
"""

from __future__ import annotations

from fractions import Fraction as Fr

# Coupled feasible manifold, parameters s in [0,1], t in [-1,1]:
#   Sigma2      = 10/100 + 2/100 t
#   W2          =  3/100 + 15/1000 t
#   Omega_tilt  =  2/100 + 1/100 s
#   DeltaOmega_k= -1/100 + 1/100 s - 5/1000 t
# comparator x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k
S_RANGE = (Fr(0), Fr(1))
T_RANGE = (Fr(-1), Fr(1))

# affine coefficients of each component in (const, s-coef, t-coef)
_COMP = {
    "Sigma2":       (Fr(10, 100), Fr(0),      Fr(2, 100)),
    "W2":           (Fr(3, 100),  Fr(0),      Fr(15, 1000)),
    "Omega_tilt":   (Fr(2, 100),  Fr(1, 100), Fr(0)),
    "DeltaOmega_k": (Fr(-1, 100), Fr(1, 100), Fr(-5, 1000)),
}
# comparator sign vector c = (+Sigma2, -W2, +Omega_tilt, +DeltaOmega_k)
_SIGN = {"Sigma2": 1, "W2": -1, "Omega_tilt": 1, "DeltaOmega_k": 1}


def _comparator_affine() -> tuple[Fr, Fr, Fr]:
    """(const, s-coef, t-coef) of x_C on the coupled manifold."""
    c0 = cs = ct = Fr(0)
    for name, (a0, as_, at) in _COMP.items():
        sgn = _SIGN[name]
        c0 += sgn * a0
        cs += sgn * as_
        ct += sgn * at
    return c0, cs, ct


def _affine_range(c0: Fr, cs: Fr, ct: Fr) -> tuple[Fr, Fr]:
    lo = c0 + min(cs * S_RANGE[0], cs * S_RANGE[1]) + min(ct * T_RANGE[0], ct * T_RANGE[1])
    hi = c0 + max(cs * S_RANGE[0], cs * S_RANGE[1]) + max(ct * T_RANGE[0], ct * T_RANGE[1])
    return lo, hi


def joint_interval_exact() -> tuple[Fr, Fr]:
    """Exact image of x_C over the coupled manifold (t drops out; s spans it)."""
    return _affine_range(*_comparator_affine())


def _component_range(name: str) -> tuple[Fr, Fr]:
    a0, as_, at = _COMP[name]
    lo = a0 + min(as_ * S_RANGE[0], as_ * S_RANGE[1]) + min(at * T_RANGE[0], at * T_RANGE[1])
    hi = a0 + max(as_ * S_RANGE[0], as_ * S_RANGE[1]) + max(at * T_RANGE[0], at * T_RANGE[1])
    return lo, hi


def product_box_interval_exact() -> tuple[Fr, Fr]:
    """Marginal product box: independent per-component extremes with signs."""
    lo = hi = Fr(0)
    for name, sgn in _SIGN.items():
        clo, chi = _component_range(name)
        if sgn >= 0:
            lo += sgn * clo
            hi += sgn * chi
        else:
            lo += sgn * chi
            hi += sgn * clo
    return lo, hi


def analysis() -> dict:
    jlo, jhi = joint_interval_exact()
    plo, phi = product_box_interval_exact()
    jw, pw = jhi - jlo, phi - plo
    return {
        "joint_interval": [str(jlo), str(jhi)],
        "product_box_interval": [str(plo), str(phi)],
        "joint_width": str(jw),
        "product_width": str(pw),
        "width_ratio": str(jw / pw),
        "joint_subset_of_product": plo <= jlo and jhi <= phi,
        "strictly_narrower": jw < pw,
        "coupling_kills_t_dependence": _comparator_affine()[2] == 0,
    }


def grid_joint_interval(n: int = 401) -> tuple[float, float]:
    """P2 second lineage: brute grid over the continuous manifold."""
    import numpy as np
    s = np.linspace(0.0, 1.0, n)
    t = np.linspace(-1.0, 1.0, n)
    T, S = np.meshgrid(t, s, indexing="ij")
    x = ((0.10 + 0.02 * T) - (0.03 + 0.015 * T)
         + (0.02 + 0.01 * S) + (-0.01 + 0.01 * S - 0.005 * T))
    return float(x.min()), float(x.max())
