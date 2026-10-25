"""Synthetic, finite-dimensional covariance-image algebra.

No observational response, physical state law, or covariance cap is supplied here.
Exact methods require decidable SymPy entries. A float near-null is diagnostic
only and never proves protection under an unbounded covariance class.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any

import sympy as sp


EXACT_NULL = "EXACT_ALGEBRAIC_NULL"
NEAR_NULL = "NUMERICAL_NEAR_NULL"
UNBOUNDED = "UNBOUNDED"
ABSENT_BOUND = "ABSENT_COVARIANCE_BOUND"
UNAVAILABLE_MAP = "UNAVAILABLE_PHYSICAL_MAP"
UNDEFINED = "UNDEFINED_INPUT_DOMAIN"


def _matrix(value: Any, *, name: str) -> sp.Matrix:
    if value is None:
        raise ValueError(f"{UNDEFINED}: {name} is required")
    out = sp.Matrix(value)
    if any(x.has(sp.Float) for x in out):
        raise ValueError(f"{UNDEFINED}: exact interface rejects floating entries")
    if any(x.free_symbols for x in out):
        raise ValueError(f"{UNDEFINED}: unqualified symbolic branch conditions")
    if any(x.is_real is not True or x.is_finite is not True for x in out):
        raise ValueError(f"{UNDEFINED}: {name} needs finite decidable real entries")
    return out


def _symmetric(value: Any, *, name: str, psd: bool = False) -> sp.Matrix:
    a = _matrix(value, name=name)
    if a.rows != a.cols or a != a.T:
        raise ValueError(f"{UNDEFINED}: {name} must be symmetric square")
    if psd:
        signs = [e.is_nonnegative for e in a.eigenvals()]
        if any(sign is None for sign in signs):
            raise ValueError(f"{UNDEFINED}: {name} PSD status undecidable")
        if any(sign is False for sign in signs):
            raise ValueError(f"{UNDEFINED}: {name} must be exact PSD")
    return a


def _projection(vectors: list[sp.Matrix], size: int) -> sp.Matrix:
    if not vectors:
        return sp.zeros(size)
    v = sp.Matrix.hstack(*vectors)
    return sp.simplify(v * (v.T * v).inv() * v.T)


def _spectral_parts(a: sp.Matrix) -> tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    """Positive projector, positive part, and PSD square root for exact symmetric a."""
    positive = sp.zeros(a.rows)
    sqrt_part = sp.zeros(a.rows)
    projector = sp.zeros(a.rows)
    for eigenvalue, _, vectors in a.eigenvects():
        if eigenvalue.is_real is not True or eigenvalue.is_positive is None:
            raise ValueError(f"{UNDEFINED}: undecidable spectral sign")
        if eigenvalue.is_positive:
            p = _projection(vectors, a.rows)
            projector += p
            positive += eigenvalue * p
            sqrt_part += sp.sqrt(eigenvalue) * p
    return sp.simplify(projector), sp.simplify(positive), sp.simplify(sqrt_part)


def physical_response_status(qualified_map: Any) -> str:
    """Boundary status only; this module never constructs a physical map."""
    return UNAVAILABLE_MAP if qualified_map is None else "SUPPLIED_EXTERNALLY_UNVERIFIED"


def cone_membership(M: Any, C: Any) -> dict[str, Any]:
    """Exact image membership and canonical minimum-trace PSD lift."""
    m = _matrix(M, name="M")
    c = _symmetric(C, name="C", psd=True)
    if c.rows != m.rows:
        raise ValueError(f"{UNDEFINED}: output dimension mismatch")
    p = m * m.pinv()
    in_range = sp.simplify(p * c - c) == sp.zeros(c.rows)
    lift = sp.simplify(m.pinv() * c * m.pinv().T)
    return {
        "status": "MEMBER" if in_range else "OUTSIDE_RANGE",
        "member": in_range,
        "canonical_lift": lift if in_range else None,
        "minimum_trace": sp.simplify(sp.trace(lift)) if in_range else None,
        "diagnostic_pseudoinverse_cost": sp.simplify(sp.trace(lift)),
        "protected_output_dimension": m.rows - m.rank(),
    }


def trace_membership(M: Any, C: Any, tau_squared: Any) -> dict[str, Any]:
    cap = sp.sympify(tau_squared)
    if cap.free_symbols:
        raise ValueError(f"{UNDEFINED}: unqualified symbolic trace cap")
    if cap.has(sp.Float):
        raise ValueError(f"{UNDEFINED}: exact trace cap rejects floating entries")
    if cap.is_real is not True or cap.is_finite is not True or cap.is_nonnegative is not True:
        raise ValueError(f"{UNDEFINED}: trace cap must be finite nonnegative tau squared")
    result = cone_membership(M, C)
    if not result["member"]:
        result.update(status="OUTSIDE_RANGE", trace_member=False, trace_cap=cap)
        return result
    allowed = (cap - result["minimum_trace"]).is_nonnegative
    if allowed is None:
        raise ValueError(f"{UNDEFINED}: undecidable trace comparison")
    result.update(status="MEMBER" if allowed else "OVER_TRACE_CAP", trace_member=bool(allowed), trace_cap=cap)
    return result


def loewner_membership(M: Any, C: Any, G: Any) -> dict[str, Any]:
    m = _matrix(M, name="M")
    c = _symmetric(C, name="C", psd=True)
    g = _symmetric(G, name="G", psd=True)
    if c.rows != m.rows or g.rows != m.cols:
        raise ValueError(f"{UNDEFINED}: Loewner dimensions disagree")
    image_cap = sp.simplify(m * g * m.T)
    try:
        _symmetric(image_cap - c, name="M G M^T - C", psd=True)
    except ValueError as exc:
        if "must be exact PSD" not in str(exc):
            raise
        return {"status": "OVER_LOEWNER_CAP", "member": False, "image_cap": image_cap, "lift": None}
    _, _, gs = _spectral_parts(g)
    n = m * gs
    z = sp.simplify(n.pinv() * c * n.pinv().T)
    lift = sp.simplify(gs * z * gs)
    return {"status": "MEMBER", "member": True, "image_cap": image_cap, "lift": lift}


def matrix_support(M: Any, H: Any, *, covariance_class: str,
                   tau_squared: Any = None, G: Any = None) -> dict[str, Any]:
    """Exact full-matrix support with an attaining latent covariance or ray."""
    m = _matrix(M, name="M")
    h = _symmetric(H, name="H")
    if h.rows != m.rows:
        raise ValueError(f"{UNDEFINED}: H and M output dimensions disagree")
    k = sp.simplify(m.T * h * m)
    zero = sp.zeros(m.cols)
    base = {"class_identity": covariance_class, "K": k}
    if covariance_class == "unbounded_psd":
        projector, _, _ = _spectral_parts(k)
        if projector == zero:
            return dict(base, status="FINITE", value=sp.Integer(0), attainer=zero, ray=None)
        for eigenvalue, _, vectors in k.eigenvects():
            if eigenvalue.is_positive:
                w = vectors[0]
                ray = sp.simplify(w * w.T / (w.T * w)[0])
                return dict(base, status=UNBOUNDED, value=sp.oo, attainer=None, ray=ray)
    if covariance_class in {"trace", "spectral"}:
        if tau_squared is None:
            return dict(base, status=ABSENT_BOUND, value=None, attainer=None, ray=None)
        cap = sp.sympify(tau_squared)
        if cap.free_symbols:
            raise ValueError(f"{UNDEFINED}: unqualified symbolic support cap")
        if cap.has(sp.Float):
            raise ValueError(f"{UNDEFINED}: exact support rejects floating cap")
        if cap.is_real is not True or cap.is_finite is not True or cap.is_nonnegative is not True:
            raise ValueError(f"{UNDEFINED}: tau squared must be finite nonnegative")
        if covariance_class == "trace":
            eigenpairs = k.eigenvects()
            if any(val.is_positive is None for val, _, _ in eigenpairs):
                raise ValueError(f"{UNDEFINED}: undecidable support spectrum")
            positive = [(val, vecs[0]) for val, _, vecs in eigenpairs if val.is_positive]
            if not positive or cap == 0:
                return dict(base, status="FINITE", value=sp.Integer(0), attainer=zero, ray=None)
            largest = sp.Max(*(pair[0] for pair in positive))
            if not any(sp.simplify(pair[0] - largest) == 0 for pair in positive):
                raise ValueError(f"{UNDEFINED}: exact maximal eigenvalue unresolved")
            val, w = next(pair for pair in positive if sp.simplify(pair[0] - largest) == 0)
            gamma = sp.simplify(cap * w * w.T / (w.T * w)[0])
            return dict(base, status="FINITE", value=sp.simplify(cap * val), attainer=gamma, ray=None)
        G = cap * sp.eye(m.cols)
    elif covariance_class != "loewner":
        raise ValueError(f"{UNDEFINED}: unknown covariance class")
    if G is None:
        return dict(base, status=ABSENT_BOUND, value=None, attainer=None, ray=None)
    g = _symmetric(G, name="G", psd=True)
    if g.rows != m.cols:
        raise ValueError(f"{UNDEFINED}: G dimension mismatch")
    _, _, gs = _spectral_parts(g)
    projector, positive, _ = _spectral_parts(sp.simplify(gs * k * gs))
    gamma = sp.simplify(gs * projector * gs)
    return dict(base, status="FINITE", value=sp.simplify(sp.trace(positive)), attainer=gamma, ray=None)


def directional_support(M: Any, u: Any, **kwargs: Any) -> dict[str, Any]:
    m = _matrix(M, name="M")
    direction = _matrix(u, name="u")
    if direction.cols != 1 or direction.rows != m.rows:
        raise ValueError(f"{UNDEFINED}: u must be an output column")
    v = sp.simplify(m.T * direction)
    result = matrix_support(m, direction * direction.T, **kwargs)
    result["null_status"] = EXACT_NULL if v == sp.zeros(m.cols, 1) else "EXACT_NONZERO"
    return result


def joint_congruence(T: Any, Omega: Any, *, block_sizes: tuple[int, ...],
                     latent_units: tuple[str, ...], output_unit: str,
                     class_identity: str) -> dict[str, Any]:
    """Require the complete joint PSD block, including every cross block."""
    t = _matrix(T, name="T")
    omega = _symmetric(Omega, name="complete Omega", psd=True)
    if not class_identity or not output_unit or len(block_sizes) != len(latent_units):
        raise ValueError(f"{UNDEFINED}: class and unit metadata are required")
    if any(n <= 0 for n in block_sizes) or sum(block_sizes) != t.cols or omega.rows != t.cols:
        raise ValueError(f"{UNDEFINED}: full joint block dimensions required")
    if any(not unit for unit in latent_units):
        raise ValueError(f"{UNDEFINED}: latent units required")
    return {"status": "FINITE", "covariance": sp.simplify(t * omega * t.T),
            "complete_Omega": omega, "class_identity": class_identity,
            "latent_units": latent_units, "output_unit": output_unit}


def marginal_directional_bounds(maps: list[Any], marginals: list[Any], u: Any) -> dict[str, Any]:
    """Sharp bounds for one fixed direction and unrestricted joint PSD completion."""
    if not maps or len(maps) != len(marginals):
        raise ValueError(f"{UNDEFINED}: every map needs a stated covariance")
    direction = _matrix(u, name="u")
    if direction.cols != 1:
        raise ValueError(f"{UNDEFINED}: u must be a column")
    s = []
    for index, (t_in, c_in) in enumerate(zip(maps, marginals)):
        t = _matrix(t_in, name=f"T{index}")
        c = _symmetric(c_in, name=f"C{index}", psd=True)
        if t.rows != direction.rows or t.cols != c.rows:
            raise ValueError(f"{UNDEFINED}: marginal dimension mismatch")
        q = sp.simplify((direction.T * t * c * t.T * direction)[0])
        if q.is_nonnegative is not True:
            raise ValueError(f"{UNDEFINED}: undecidable projected variance")
        s.append(sp.sqrt(q))
    total = sp.simplify(sum(s))
    biggest = sp.Max(*s)
    gap = sp.Max(2 * biggest - total, 0)
    return {"status": "FINITE", "projected_standard_deviations": s,
            "upper": sp.simplify(total**2), "lower": sp.simplify(gap**2),
            "attainment_scope": "pointwise fixed direction, unrestricted PSD cross blocks"}


def floating_directional_diagnostic(M: Any, u: Any, *, covariance_class: str,
                                    tau_squared: float | None = None,
                                    rtol: float = 1e-12, atol: float = 1e-12) -> dict[str, Any]:
    """NumPy diagnostic; no tolerance may declare an exact unbounded-class null."""
    import numpy as np

    m = np.asarray(M, dtype=float)
    direction = np.asarray(u, dtype=float).reshape(-1)
    if m.ndim != 2 or direction.shape != (m.shape[0],) or not np.isfinite(m).all() or not np.isfinite(direction).all():
        raise ValueError(f"{UNDEFINED}: finite array dimensions required")
    # Fraction.from_float uses the actual binary input values. No floating
    # multiplication, reduction, norm square, or dot product decides a bound.
    exact_response = [sum((Fraction.from_float(float(m[i, j])) *
                           Fraction.from_float(float(direction[i]))
                           for i in range(m.shape[0])), Fraction(0))
                      for j in range(m.shape[1])]
    exact_norm_squared = sum((value * value for value in exact_response), Fraction(0))
    try:
        norm = math.sqrt(float(exact_norm_squared))
    except OverflowError:
        norm = math.inf
    threshold = atol + rtol * float(np.linalg.norm(m, ord=2) * np.linalg.norm(direction))
    near = norm <= threshold
    status = NEAR_NULL if near else "NUMERICAL_NONZERO"
    if covariance_class == "unbounded_psd":
        # Even a value below the diagnostic cutoff is an unbounded direction.
        return {"status": status, "upper": 0.0 if exact_norm_squared == 0 else math.inf,
                "exact_protection_proved": False, "response_norm": norm,
                "diagnostic_threshold": threshold,
                "contraction_certified_for_supplied_binary_floats": True}
    if covariance_class == "trace":
        if tau_squared is None:
            return {"status": ABSENT_BOUND, "upper": None, "exact_protection_proved": False}
        if not math.isfinite(tau_squared) or tau_squared < 0:
            raise ValueError(f"{UNDEFINED}: trace cap must be finite nonnegative")
        exact_bound = Fraction.from_float(float(tau_squared)) * exact_norm_squared
        try:
            upper = float(exact_bound)
        except OverflowError:
            upper = math.inf
        if not math.isfinite(upper) or (upper == 0.0 and exact_bound != 0):
            return {"status": "NUMERICAL_BOUND_UNREPRESENTABLE", "upper": None,
                    "exact_protection_proved": False, "response_norm": norm,
                    "diagnostic_threshold": threshold,
                    "contraction_certified_for_supplied_binary_floats": True}
        if Fraction.from_float(upper) < exact_bound:
            upper = math.nextafter(upper, math.inf)
            if not math.isfinite(upper):
                return {"status": "NUMERICAL_BOUND_UNREPRESENTABLE", "upper": None,
                        "exact_protection_proved": False, "response_norm": norm,
                        "diagnostic_threshold": threshold,
                        "contraction_certified_for_supplied_binary_floats": True}
        return {"status": status, "upper": upper,
                "exact_protection_proved": False, "response_norm": norm,
                "diagnostic_threshold": threshold,
                "contraction_certified_for_supplied_binary_floats": True}
    raise ValueError(f"{UNDEFINED}: unsupported floating class")
