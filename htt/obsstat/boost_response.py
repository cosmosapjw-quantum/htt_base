"""Exact first-order local-boost response of an observer-space quadrupole.

For a real Cartesian STF quadrupole ``Q_ab`` and a dimensionless local
observer velocity ``beta_a``, the convention-locked octupole response is

``(B_Q beta)_abc = 3 beta_<a Q_bc>``.

With the Frobenius products on STF2 and STF3,

``(B_Q beta):Q = M_Q beta``,  ``M_Q = q2 I + (6/5) Q^2``,
``B_Q* B_Q = 3 M_Q``.

The resulting inverse and projector are algebraic observer-space tools.  They
do not turn an arbitrary octupole into a measured peculiar velocity, global
matter-frame tilt, or Bianchi-family attribution; those claims require an
explicit nuisance and empirical response model.
"""

from __future__ import annotations

import numpy as np


_TENSOR_ATOL = 2.0e-13
_STF3_COMPONENT_LAYOUT = (
    "Oxxx",
    "Oxxy",
    "Oxxz",
    "Oxyy",
    "Oxyz",
    "Oyyy",
    "Oyyz",
)
_STF3_COMPONENT_METRIC = np.array(
    [
        [4.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0],
        [0.0, 6.0, 0.0, 0.0, 0.0, 3.0, 0.0],
        [0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 1.0],
        [3.0, 0.0, 0.0, 6.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 6.0, 0.0, 0.0],
        [0.0, 3.0, 0.0, 0.0, 0.0, 4.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 4.0],
    ],
    dtype=np.float64,
)


class BoostResponseError(ValueError):
    """Raised when a local-boost STF response contract is violated."""


def _vector3(value: object, *, label: str) -> np.ndarray:
    try:
        vector = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise BoostResponseError(f"{label} must be a finite real three-vector") from exc
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise BoostResponseError(f"{label} must be a finite real three-vector")
    return vector


def _quadrupole(value: object) -> np.ndarray:
    try:
        tensor = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise BoostResponseError("quadrupole must be a finite real 3x3 STF tensor") from exc
    if tensor.shape != (3, 3) or not np.all(np.isfinite(tensor)):
        raise BoostResponseError("quadrupole must be a finite real 3x3 STF tensor")
    scale = max(1.0, float(np.max(np.abs(tensor))))
    if not np.allclose(tensor, tensor.T, rtol=0.0, atol=_TENSOR_ATOL * scale):
        raise BoostResponseError("quadrupole must be symmetric")
    if abs(float(np.trace(tensor))) > _TENSOR_ATOL * scale:
        raise BoostResponseError("quadrupole must be trace-free")
    return tensor


def _octupole(value: object) -> np.ndarray:
    try:
        tensor = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise BoostResponseError("octupole must be a finite real 3x3x3 STF tensor") from exc
    if tensor.shape != (3, 3, 3) or not np.all(np.isfinite(tensor)):
        raise BoostResponseError("octupole must be a finite real 3x3x3 STF tensor")
    scale = max(1.0, float(np.max(np.abs(tensor))))
    for permutation in ((1, 0, 2), (2, 1, 0), (0, 2, 1), (2, 0, 1), (1, 2, 0)):
        if not np.allclose(
            tensor,
            np.transpose(tensor, permutation),
            rtol=0.0,
            atol=_TENSOR_ATOL * scale,
        ):
            raise BoostResponseError("octupole must be fully symmetric")
    if float(np.max(np.abs(np.einsum("iik->k", tensor)))) > _TENSOR_ATOL * scale:
        raise BoostResponseError("octupole must be trace-free on every index pair")
    return tensor


def _unit_directions(value: object) -> np.ndarray:
    try:
        directions = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise BoostResponseError("sky directions must be finite unit three-vectors") from exc
    if (
        directions.ndim < 1
        or directions.shape[-1] != 3
        or not np.all(np.isfinite(directions))
    ):
        raise BoostResponseError("sky directions must be finite unit three-vectors")
    if not np.allclose(
        np.linalg.norm(directions, axis=-1),
        1.0,
        rtol=0.0,
        atol=5.0e-13,
    ):
        raise BoostResponseError(
            "sky directions must be unit normalized; no silent projection is allowed"
        )
    return directions


def _stf3_components(tensor: np.ndarray) -> np.ndarray:
    return np.asarray(
        [
            tensor[0, 0, 0],
            tensor[0, 0, 1],
            tensor[0, 0, 2],
            tensor[0, 1, 1],
            tensor[0, 1, 2],
            tensor[1, 1, 1],
            tensor[1, 1, 2],
        ],
        dtype=np.float64,
    )


def quadrupole_temperature(quadrupole: object, direction: object) -> np.ndarray:
    """Evaluate ``T_Q(n) = Q_ab n^a n^b`` on one or more unit directions."""

    q = _quadrupole(quadrupole)
    directions = _unit_directions(direction)
    return np.einsum("...a,ab,...b->...", directions, q, directions)


def quadrupole_boost_octupole(quadrupole: object, beta: object) -> np.ndarray:
    """Return the exact STF3 response ``3 beta_<a Q_bc>``."""

    q = _quadrupole(quadrupole)
    velocity = _vector3(beta, label="beta")
    contraction = q @ velocity
    identity = np.eye(3)
    response = (
        np.einsum("a,bc->abc", velocity, q)
        + np.einsum("b,ca->abc", velocity, q)
        + np.einsum("c,ab->abc", velocity, q)
        - (2.0 / 5.0)
        * (
            np.einsum("ab,c->abc", identity, contraction)
            + np.einsum("ac,b->abc", identity, contraction)
            + np.einsum("bc,a->abc", identity, contraction)
        )
    )
    return response


def quadrupole_boost_dipole(quadrupole: object, beta: object) -> np.ndarray:
    """Return the accompanying first-order dipole coefficient ``-(4/5)Q beta``."""

    q = _quadrupole(quadrupole)
    velocity = _vector3(beta, label="beta")
    return -(4.0 / 5.0) * (q @ velocity)


def first_order_quadrupole_boost(
    quadrupole: object,
    beta: object,
    direction: object,
) -> np.ndarray:
    """Evaluate the complete first-order ``ell=1 plus ell=3`` response."""

    directions = _unit_directions(direction)
    octupole = quadrupole_boost_octupole(quadrupole, beta)
    dipole = quadrupole_boost_dipole(quadrupole, beta)
    cubic = np.einsum(
        "abc,...a,...b,...c->...",
        octupole,
        directions,
        directions,
        directions,
    )
    return cubic + np.einsum("a,...a->...", dipole, directions)


def contract_octupole_with_quadrupole(
    octupole: object,
    quadrupole: object,
) -> np.ndarray:
    """Return the vector ``(O:Q)_a = O_abc Q^bc``."""

    o = _octupole(octupole)
    q = _quadrupole(quadrupole)
    return np.einsum("abc,bc->a", o, q)


def boost_response_metric(quadrupole: object) -> np.ndarray:
    """Return ``M_Q = q2 I + (6/5) Q^2``."""

    q = _quadrupole(quadrupole)
    q2 = float(np.einsum("ab,ab->", q, q))
    return q2 * np.eye(3) + (6.0 / 5.0) * (q @ q)


def boost_response_matrix(quadrupole: object) -> np.ndarray:
    """Return the registered seven-component matrix of ``B_Q``.

    Rows follow ``(Oxxx, Oxxy, Oxxz, Oxyy, Oxyz, Oyyy, Oyyz)`` and columns
    correspond to the Cartesian components of ``beta``.
    """

    q = _quadrupole(quadrupole)
    columns = [
        _stf3_components(quadrupole_boost_octupole(q, np.eye(3)[axis]))
        for axis in range(3)
    ]
    return np.column_stack(columns)


def stf3_component_metric() -> np.ndarray:
    """Return the Frobenius Gram matrix in the registered seven-component layout."""

    return _STF3_COMPONENT_METRIC.copy()


def boost_least_squares_inverse(
    quadrupole: object,
    octupole: object,
) -> np.ndarray:
    """Return ``beta_hat = M_Q^{-1}(O:Q)`` on the nonzero-``Q`` domain."""

    q = _quadrupole(quadrupole)
    o = _octupole(octupole)
    q2 = float(np.einsum("ab,ab->", q, q))
    if q2 == 0.0:
        raise BoostResponseError("boost inverse is undefined at zero quadrupole")
    metric = q2 * np.eye(3) + (6.0 / 5.0) * (q @ q)
    try:
        estimate = np.linalg.solve(metric, np.einsum("abc,bc->a", o, q))
    except np.linalg.LinAlgError as exc:  # defensive; M_Q is positive for Q != 0
        raise BoostResponseError("boost response metric became singular") from exc
    if not np.all(np.isfinite(estimate)):
        raise BoostResponseError("boost inverse became nonfinite")
    return estimate


def project_onto_boost_image(quadrupole: object, octupole: object) -> np.ndarray:
    """Orthogonally project an STF3 tensor onto ``Im B_Q``."""

    q = _quadrupole(quadrupole)
    o = _octupole(octupole)
    return quadrupole_boost_octupole(q, boost_least_squares_inverse(q, o))


def boost_orthogonal_residual(quadrupole: object, octupole: object) -> np.ndarray:
    """Return ``O_perp = O - P_ImB O`` with ``O_perp:Q = 0``."""

    o = _octupole(octupole)
    return o - project_onto_boost_image(quadrupole, o)


__all__ = [
    "BoostResponseError",
    "boost_least_squares_inverse",
    "boost_orthogonal_residual",
    "boost_response_matrix",
    "boost_response_metric",
    "contract_octupole_with_quadrupole",
    "first_order_quadrupole_boost",
    "project_onto_boost_image",
    "quadrupole_boost_dipole",
    "quadrupole_boost_octupole",
    "quadrupole_temperature",
    "stf3_component_metric",
]
