"""Executable oracle for the tensor-foundation propositions (TF-*).

Drop-in target: ``htt/src/common/tensor_foundations_oracle.py``.

This module is an INDEPENDENT verification surface. It imports nothing from the
repository: every generator, invariant, action and identity is re-implemented
from its mathematical definition so that agreement with the production modules
(``orbit_nonlinearity``, ``orbit_catalogue_v2``, ``anchor_geometry``,
``anchored_response_geometry``, ``velocity_frame_decomposition``) is evidence
rather than tautology. It follows the established repository oracle pattern:
each proposition is one function returning a dict carrying an explicit ``ok``
verdict plus the numbers the verdict was taken from.

Claim posture. Every proposition below is a statement about algebra, group
representations, or a stated probability model. None of them identifies a
Bianchi family, detects geometry, validates a native solver, supplies an HTT
posterior or evidence term, or consumes PR-151 acquisition data. Propositions
that require physical premises (TF-12) carry those premises in the returned
payload and are conditional on them.

Conventions used throughout
---------------------------
* ``sigma`` is a real symmetric trace-free 3x3 matrix, supplied either as a
  matrix or in the registered STF5 Cartesian layout ``(Sxx, Syy, Sxy, Sxz, Syz)``
  with ``Szz = -Sxx - Syy`` (basis ``STF5_CARTESIAN_XX_YY_XY_XZ_YZ_V1``).
* ``beta`` and ``accel`` are POLAR 3-vectors; ``omega`` is an AXIAL 3-vector.
  Under ``R in O(3)``: ``sigma -> R sigma R^T``, ``beta -> R beta``,
  ``omega -> det(R) R omega``.
* ``delta_omega_k`` is a signed scalar.
* The relevant orbit group is ``SO(3)`` (choice of spatial axes). ``O(3)``
  parity is carried as a TYPE, never quotiented out: reflection-odd quantities
  are legitimate SO(3) invariants and are the subject of TF-9.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np

__all__ = [
    "ORACLE_ID",
    "PROPOSITION_IDS",
    "stf5_to_matrix",
    "even_invariants",
    "krylov_determinant",
    "shape_coordinates",
    "tf01_parity_typing",
    "tf02_catalogue_completion",
    "tf03_krylov_syzygy",
    "tf04_cayley_hamilton_reduction",
    "tf05_shape_discriminant_identity",
    "tf06_invariant_dimension",
    "tf07_budget_morphology_splitting",
    "tf08_product_gauge_is_max",
    "tf09_parity_sign_exactness",
    "tf10_local_global_separation",
    "tf11_mask_path_reverse_martingale",
    "tf12_acceleration_euler_slaving",
    "run_all",
]

ORACLE_ID = "TENSOR_FOUNDATIONS_ORACLE_V1"
DEFAULT_SEED = 20260730

PROPOSITION_IDS = (
    "TF-01-PARITY-TYPING",
    "TF-02-CATALOGUE-COMPLETION",
    "TF-03-KRYLOV-SYZYGY",
    "TF-04-CAYLEY-HAMILTON-REDUCTION",
    "TF-05-SHAPE-DISCRIMINANT",
    "TF-06-INVARIANT-DIMENSION",
    "TF-07-BUDGET-MORPHOLOGY-SPLIT",
    "TF-08-PRODUCT-GAUGE-MAX",
    "TF-09-PARITY-SIGN-EXACTNESS",
    "TF-10-LOCAL-GLOBAL-SEPARATION",
    "TF-11-MASK-PATH-MARTINGALE",
    "TF-12-ACCELERATION-EULER-SLAVING",
)

STF5_BASIS = "STF5_CARTESIAN_XX_YY_XY_XZ_YZ_V1"


# --------------------------------------------------------------------------
# generators
# --------------------------------------------------------------------------
def stf5_to_matrix(components) -> np.ndarray:
    """Decode the registered STF5 Cartesian layout into a trace-free matrix."""
    sxx, syy, sxy, sxz, syz = (float(c) for c in components)
    return np.array(
        [[sxx, sxy, sxz], [sxy, syy, syz], [sxz, syz, -sxx - syy]], dtype=float
    )


def _random_rotation(rng: np.random.Generator) -> np.ndarray:
    """Haar-uniform SO(3) matrix via QR with sign fixing (no scipy dependency)."""
    a = rng.normal(size=(3, 3))
    q, r = np.linalg.qr(a)
    q = q * np.sign(np.diag(r))[None, :]
    if np.linalg.det(q) < 0.0:
        q[:, 0] = -q[:, 0]
    return q


def krylov_determinant(sigma: np.ndarray, vector: np.ndarray) -> float:
    """det[v, sigma v, sigma^2 v] -- the third-order Krylov determinant."""
    v = np.asarray(vector, dtype=float)
    s = np.asarray(sigma, dtype=float)
    return float(np.linalg.det(np.column_stack([v, s @ v, s @ s @ v])))


def even_invariants(sigma: np.ndarray, vector: np.ndarray) -> dict:
    """The five degree-bounded even invariants attached to (sigma, one vector)."""
    s = np.asarray(sigma, dtype=float)
    v = np.asarray(vector, dtype=float)
    s2 = s @ s
    return {
        "tr_sigma2": float(np.trace(s2)),
        "tr_sigma3": float(np.trace(s2 @ s)),
        "v2": float(v @ v),
        "v_sigma_v": float(v @ s @ v),
        "v_sigma2_v": float(v @ s2 @ v),
    }


def shape_coordinates(sigma: np.ndarray) -> dict:
    """Amplitude-free shear shape coordinates (TF-05).

    ``I2 = tr sigma^2``, ``I3 = tr sigma^3``, ``J = sqrt(6) I3 / I2^{3/2}``,
    ``Delta = I2^3/2 - 3 I3^2`` (the discriminant of the characteristic
    polynomial of a trace-free 3x3 matrix).
    """
    s = np.asarray(sigma, dtype=float)
    s2 = s @ s
    i2 = float(np.trace(s2))
    i3 = float(np.trace(s2 @ s))
    delta = 0.5 * i2**3 - 3.0 * i3**2
    j = None if i2 <= 0.0 else float(np.sqrt(6.0) * i3 / i2**1.5)
    return {"I2": i2, "I3": i3, "J": j, "discriminant": delta}


# --------------------------------------------------------------------------
# TF-01  parity typing of the completed catalogue
# --------------------------------------------------------------------------
def tf01_parity_typing(n_samples: int = 300, seed: int = DEFAULT_SEED) -> dict:
    """TF-01. The axial Krylov determinant is an O(3) SCALAR; the polar one is a
    PSEUDOSCALAR.

    With ``omega`` axial each of the three columns of ``[omega, sigma omega,
    sigma^2 omega]`` carries a factor ``det(R)``, and the determinant of the
    stacked matrix carries a fourth: ``det(R)^4 = 1``. With ``beta`` polar only
    the stacking factor survives, giving ``det(R)``. The consequence used by
    TF-02 is that ``det[omega, sigma omega, sigma^2 omega]`` is a genuine
    invariant that is ODD under ``omega -> -omega``.
    """
    rng = np.random.default_rng(seed)
    sigma = stf5_to_matrix((1.0, 2.0, 0.35, -0.2, 0.7))
    omega = np.array([0.9, -0.4, 0.6])
    beta = np.array([0.2, 0.8, -0.5])
    axial_err = 0.0
    polar_err = 0.0
    for _ in range(int(n_samples)):
        rot = _random_rotation(rng)
        for improper in (False, True):
            matrix = -rot if improper else rot
            det = float(np.linalg.det(matrix))
            sigma_t = matrix @ sigma @ matrix.T
            omega_t = det * (matrix @ omega)
            beta_t = matrix @ beta
            axial_err = max(
                axial_err,
                abs(
                    krylov_determinant(sigma_t, omega_t)
                    - krylov_determinant(sigma, omega)
                ),
            )
            polar_err = max(
                polar_err,
                abs(
                    krylov_determinant(sigma_t, beta_t)
                    - det * krylov_determinant(sigma, beta)
                ),
            )
    scale = max(1.0, abs(krylov_determinant(sigma, omega)))
    tol = 1e-9 * scale
    return {
        "proposition": "TF-01-PARITY-TYPING",
        "axial_krylov_parity": "O3_SCALAR",
        "polar_krylov_parity": "O3_PSEUDOSCALAR",
        "axial_max_abs_error": axial_err,
        "polar_max_abs_error": polar_err,
        "tolerance": tol,
        "n_transforms": 2 * int(n_samples),
        "ok": bool(axial_err <= tol and polar_err <= tol),
    }


# --------------------------------------------------------------------------
# TF-02  catalogue completion against the registered non-separation witness
# --------------------------------------------------------------------------
def tf02_catalogue_completion(seed: int = DEFAULT_SEED) -> dict:
    """TF-02. On the registered ``PR257-NONGENERIC-NONSEPARATION`` witness the
    twelve v2 polynomials do not separate ``(sigma, omega)`` from
    ``(sigma, -omega)``; the axial Krylov determinant does, and the two states
    are genuinely in distinct SO(3) orbits.

    SCOPE, stated precisely because it is easy to over-read. The registered
    witness has ``beta = 0``, i.e. it lies OFF the principal stratum on which
    §3.5 of the upgrade spec states separation. Exhaustive checking of the
    residual gauge shows that for generic ``beta`` the v2 catalogue already
    separates SO(3) orbits, so ``K_omega`` is not a missing generic generator:
    it supplies a sign bit exactly where a vector fails to be cyclic for
    ``sigma``. This proposition therefore closes the registered NON-GENERIC
    witness; it does NOT establish generic orbit separation and does not change
    ``generic_orbit_separation_status`` or ``degree_completeness_status``, both
    of which remain UNPROVEN.

    Anti-vacuity: the candidate generator is checked to be SO(3)-invariant
    before it is allowed to separate anything (an arbitrary odd function of
    ``omega`` would otherwise "separate" the witness while being no invariant at
    all), and the stabiliser is COMPUTED from the commutant rather than
    asserted.
    """
    rng = np.random.default_rng(seed + 7)
    sigma = np.diag([1.0, 2.0, -3.0])
    omega = np.array([1.0, 2.0, 3.0])
    beta = np.zeros(3)

    registered = []
    for om in (omega, -omega):
        even_s = even_invariants(sigma, om)
        even_b = even_invariants(sigma, beta)
        registered.append(
            (
                even_s["tr_sigma2"],
                even_s["tr_sigma3"],
                even_b["v2"],
                even_b["v_sigma_v"],
                even_b["v_sigma2_v"],
                krylov_determinant(sigma, beta),
                even_s["v2"],
                even_s["v_sigma_v"],
                even_s["v_sigma2_v"],
                float(beta @ om),
                float(beta @ sigma @ om),
                float(beta @ sigma @ sigma @ om),
            )
        )
    registered_identical = bool(
        np.allclose(np.array(registered[0]), np.array(registered[1]), atol=0.0, rtol=0.0)
    )

    new_plus = krylov_determinant(sigma, omega)
    new_minus = krylov_determinant(sigma, -omega)
    separated = bool(new_plus != new_minus and new_plus != 0.0)

    # ANTI-VACUITY GATE 1: the candidate must actually be an SO(3) invariant of
    # the axial representation. Without this check any odd function of omega
    # would "separate" the witness.
    invariance_err = 0.0
    for _ in range(200):
        rot = _random_rotation(rng)
        invariance_err = max(
            invariance_err,
            abs(
                krylov_determinant(rot @ sigma @ rot.T, rot @ omega)
                - krylov_determinant(sigma, omega)
            ),
        )
    candidate_is_invariant = bool(invariance_err <= 1e-9 * max(1.0, abs(new_plus)))

    # ANTI-VACUITY GATE 2: compute the stabiliser rather than assert it. For a
    # symmetric matrix with distinct eigenvalues the commutant is exactly the
    # 3-dimensional algebra of matrices diagonal in its eigenbasis, so the
    # orthogonal stabiliser is the 8 sign matrices and its SO(3) part has 4.
    basis = []
    for i in range(3):
        for j in range(3):
            e = np.zeros((3, 3))
            e[i, j] = 1.0
            basis.append((sigma @ e - e @ sigma).ravel())
    commutant_dim = 9 - int(np.linalg.matrix_rank(np.array(basis), tol=1e-9))
    stabiliser = [
        np.diag(np.array(signs, dtype=float))
        for signs in itertools.product((1.0, -1.0), repeat=3)
        if float(np.prod(signs)) == 1.0
    ]
    stabiliser_verified = bool(
        commutant_dim == 3
        and all(np.allclose(g @ sigma @ g.T, sigma) for g in stabiliser)
    )
    # no random rotation outside the computed stabiliser fixes sigma
    spurious = 0
    for _ in range(2000):
        rot = _random_rotation(rng)
        if np.allclose(rot @ sigma @ rot.T, sigma, atol=1e-9):
            if not any(np.allclose(rot, g, atol=1e-6) for g in stabiliser):
                spurious += 1
    orbit_map_exists = any(np.allclose(g @ omega, -omega) for g in stabiliser)

    return {
        "proposition": "TF-02-CATALOGUE-COMPLETION",
        "scope": "closes the registered NON-GENERIC (beta=0) witness only",
        "generic_orbit_separation_status": "UNPROVEN (unchanged)",
        "degree_completeness_status": "UNPROVEN (unchanged)",
        "witness": {
            "sigma_diagonal": [1.0, 2.0, -3.0],
            "beta": [0.0, 0.0, 0.0],
            "omega": [1.0, 2.0, 3.0],
        },
        "registered_twelve_identical_on_witness": registered_identical,
        "axial_krylov_plus": new_plus,
        "axial_krylov_minus": new_minus,
        "candidate_is_so3_invariant": candidate_is_invariant,
        "candidate_invariance_max_error": invariance_err,
        "commutant_dimension": commutant_dim,
        "stabiliser_order": len(stabiliser),
        "stabiliser_verified": stabiliser_verified,
        "spurious_stabiliser_elements_found": spurious,
        "orbit_identification_exists": orbit_map_exists,
        "distinct_orbits": not orbit_map_exists,
        "separated_by_new_generator": separated,
        "ok": bool(
            registered_identical
            and separated
            and candidate_is_invariant
            and stabiliser_verified
            and spurious == 0
            and not orbit_map_exists
        ),
    }


# --------------------------------------------------------------------------
# TF-03  the Krylov syzygy: the square is old information, the sign is new
# --------------------------------------------------------------------------
def tf03_krylov_syzygy(n_samples: int = 400, seed: int = DEFAULT_SEED) -> dict:
    """TF-03. ``det[v, sigma v, sigma^2 v]^2`` equals the Gram determinant of the
    Krylov chain, which by TF-04 is a polynomial in the five even invariants of
    ``(sigma, v)``.

    Interpretation, and the reason TF-02 is not circular: the MAGNITUDE of a
    Krylov determinant carries no information beyond the even catalogue; the
    single new degree of freedom it contributes is its SIGN -- one bit of
    orientation (handedness of the vector relative to the shear eigenframe).
    That bit is the object of the exact test in TF-09.
    """
    rng = np.random.default_rng(seed)
    max_rel_gram = 0.0
    max_rel_poly = 0.0
    for _ in range(int(n_samples)):
        sigma = stf5_to_matrix(rng.normal(size=5))
        v = rng.normal(size=3)
        s2 = sigma @ sigma
        chain = np.column_stack([v, sigma @ v, s2 @ v])
        det = float(np.linalg.det(chain))
        gram = float(np.linalg.det(chain.T @ chain))

        inv = even_invariants(sigma, v)
        i2, i3 = inv["tr_sigma2"], inv["tr_sigma3"]
        m0, m1, m2 = inv["v2"], inv["v_sigma_v"], inv["v_sigma2_v"]
        # Cayley-Hamilton reductions (TF-04) applied to the Gram entries
        m3 = 0.5 * i2 * m1 + i3 * m0 / 3.0
        m4 = 0.5 * i2 * m2 + i3 * m1 / 3.0
        gram_poly = float(
            np.linalg.det(np.array([[m0, m1, m2], [m1, m2, m3], [m2, m3, m4]]))
        )
        scale = max(1.0, abs(gram), abs(gram_poly), det * det)
        max_rel_gram = max(max_rel_gram, abs(det * det - gram) / scale)
        max_rel_poly = max(max_rel_poly, abs(det * det - gram_poly) / scale)
    tol = 1e-8
    return {
        "proposition": "TF-03-KRYLOV-SYZYGY",
        "identity_square_equals_gram": "det(K)^2 == det(K^T K)",
        "identity_gram_is_polynomial": "det(K^T K) == P(tr s2, tr s3, v2, v.s.v, v.s2.v)",
        "max_relative_error_gram": max_rel_gram,
        "max_relative_error_polynomial": max_rel_poly,
        "tolerance": tol,
        "new_information_content": "sign_bit_only",
        "n_samples": int(n_samples),
        "ok": bool(max_rel_gram <= tol and max_rel_poly <= tol),
    }


# --------------------------------------------------------------------------
# TF-04  Cayley-Hamilton reductions used above
# --------------------------------------------------------------------------
def tf04_cayley_hamilton_reduction(n_samples: int = 400, seed: int = DEFAULT_SEED) -> dict:
    """TF-04. For real trace-free symmetric 3x3 ``sigma``:
    ``sigma^3 = (tr sigma^2 / 2) sigma + (tr sigma^3 / 3) I``,
    hence ``v.sigma^3.v`` and ``v.sigma^4.v`` reduce to the registered even set.

    This is the reduction that bounds the catalogue degree: no invariant of the
    form ``v . sigma^k . v`` with ``k >= 3`` is a new generator.
    """
    rng = np.random.default_rng(seed + 1)
    max_matrix = 0.0
    max_m3 = 0.0
    max_m4 = 0.0
    for _ in range(int(n_samples)):
        sigma = stf5_to_matrix(rng.normal(size=5))
        v = rng.normal(size=3)
        s2 = sigma @ sigma
        s3 = s2 @ sigma
        i2 = float(np.trace(s2))
        i3 = float(np.trace(s3))
        residual = s3 - (0.5 * i2) * sigma - (i3 / 3.0) * np.eye(3)
        scale = max(1.0, float(np.abs(s3).max()))
        max_matrix = max(max_matrix, float(np.abs(residual).max()) / scale)
        m0 = float(v @ v)
        m1 = float(v @ sigma @ v)
        m2 = float(v @ s2 @ v)
        m3 = float(v @ s3 @ v)
        m4 = float(v @ (s3 @ sigma) @ v)
        max_m3 = max(max_m3, abs(m3 - (0.5 * i2 * m1 + i3 * m0 / 3.0)) / max(1.0, abs(m3)))
        max_m4 = max(max_m4, abs(m4 - (0.5 * i2 * m2 + i3 * m1 / 3.0)) / max(1.0, abs(m4)))
    tol = 1e-9
    return {
        "proposition": "TF-04-CAYLEY-HAMILTON-REDUCTION",
        "max_relative_error_matrix_identity": max_matrix,
        "max_relative_error_v_sigma3_v": max_m3,
        "max_relative_error_v_sigma4_v": max_m4,
        "tolerance": tol,
        "n_samples": int(n_samples),
        "ok": bool(max(max_matrix, max_m3, max_m4) <= tol),
    }


# --------------------------------------------------------------------------
# TF-05  shape coordinates and the discriminant identity
# --------------------------------------------------------------------------
def tf05_shape_discriminant_identity(n_samples: int = 200_000, seed: int = DEFAULT_SEED) -> dict:
    """TF-05. With ``I2 = tr sigma^2 > 0`` and ``J = sqrt(6) I3 / I2^{3/2}``:

    * ``Delta := I2^3/2 - 3 I3^2`` is exactly the discriminant of the
      characteristic polynomial of ``sigma``;
    * ``Delta = (I2^3 / 2) (1 - J^2)``, hence ``|J| <= 1`` always, with
      ``|J| = 1`` iff ``sigma`` has a repeated eigenvalue (axisymmetric shear)
      and ``J = 0`` iff the eigenvalues are ``(lambda, -lambda, 0)``;
    * ``J`` is scale-free: it is invariant under ``sigma -> c sigma`` for
      ``c > 0`` and odd under ``c < 0``.

    Consequence for the programme: ``tr sigma^3`` is NOT merely a higher-order
    amplitude statistic. Normalised as ``J`` it is an amplitude-free
    anisotropy-TYPE coordinate whose two endpoints and midpoint are exactly the
    degenerate strata. This is the coordinate on which a shear morphology class
    is defined without reference to any Bianchi family.
    """
    rng = np.random.default_rng(seed + 2)
    lam = rng.normal(size=(int(n_samples), 3))
    lam = lam - lam.mean(axis=1, keepdims=True)
    i2 = (lam**2).sum(axis=1)
    i3 = (lam**3).sum(axis=1)
    keep = i2 > 1e-12
    i2, i3 = i2[keep], i3[keep]
    j = np.sqrt(6.0) * i3 / i2**1.5
    delta = 0.5 * i2**3 - 3.0 * i3**2
    identity_err = float(np.max(np.abs(delta - 0.5 * i2**3 * (1.0 - j**2)) / np.maximum(1.0, np.abs(delta))))

    # exact symbolic corroboration of both identities (optional dependency)
    symbolic = {"available": False}
    try:  # pragma: no cover - exercised when sympy is installed
        import sympy as sp

        l1, l2 = sp.symbols("l1 l2", real=True)
        l3 = -l1 - l2
        lam_sym = sp.symbols("lam")
        i2s = sp.expand(l1**2 + l2**2 + l3**2)
        i3s = sp.expand(l1**3 + l2**3 + l3**3)
        delta_s = sp.expand(sp.Rational(1, 2) * i2s**3 - 3 * i3s**2)
        disc = sp.discriminant(sp.expand((lam_sym - l1) * (lam_sym - l2) * (lam_sym - l3)), lam_sym)
        r1 = sp.simplify(sp.expand(disc - delta_s))
        r2 = sp.simplify(
            sp.expand(delta_s - sp.Rational(1, 2) * i2s**3 * (1 - sp.simplify(6 * i3s**2 / i2s**3)))
        )
        symbolic = {
            "available": True,
            "discriminant_residual": str(r1),
            "gauge_identity_residual": str(r2),
            "ok": bool(r1 == 0 and r2 == 0),
        }
    except Exception as exc:  # pragma: no cover
        symbolic = {"available": False, "reason": repr(exc)}

    # exact endpoints
    endpoints = {
        "axisymmetric_prolate_J": float(shape_coordinates(np.diag([2.0, -1.0, -1.0]))["J"]),
        "axisymmetric_oblate_J": float(shape_coordinates(np.diag([-2.0, 1.0, 1.0]))["J"]),
        "biaxial_J": float(shape_coordinates(np.diag([1.0, -1.0, 0.0]))["J"]),
    }
    scale_free = abs(
        shape_coordinates(np.diag([2.0, -1.0, -1.0]) * 7.3)["J"]
        - shape_coordinates(np.diag([2.0, -1.0, -1.0]))["J"]
    )
    return {
        "proposition": "TF-05-SHAPE-DISCRIMINANT",
        "identity": "Delta == (I2^3/2)(1 - J^2) == discriminant(charpoly)",
        "symbolic_check": symbolic,
        "degree_note": "J is scale-free (degree 0); Delta is degree-6 homogeneous",
        "max_relative_identity_error": identity_err,
        "empirical_J_min": float(j.min()),
        "empirical_J_max": float(j.max()),
        "endpoints": endpoints,
        "scale_invariance_error": float(scale_free),
        "n_samples": int(keep.sum()),
        "ok": bool(
            identity_err <= 1e-9
            and j.min() >= -1.0 - 1e-9
            and j.max() <= 1.0 + 1e-9
            and abs(endpoints["axisymmetric_prolate_J"] - 1.0) <= 1e-12
            and abs(endpoints["axisymmetric_oblate_J"] + 1.0) <= 1e-12
            and abs(endpoints["biaxial_J"]) <= 1e-12
            and scale_free <= 1e-12
        ),
    }


# --------------------------------------------------------------------------
# TF-06  how many invariant directions the state actually has
# --------------------------------------------------------------------------
def _invariants_sigma_omega_beta_k(state: np.ndarray) -> np.ndarray:
    sigma = stf5_to_matrix(state[:5])
    omega = state[5:8]
    beta = state[8:11]
    k = state[11]
    s2 = sigma @ sigma
    return np.array(
        [
            np.trace(s2),
            np.trace(s2 @ sigma),
            beta @ beta,
            omega @ omega,
            beta @ omega,
            beta @ sigma @ beta,
            omega @ sigma @ omega,
            beta @ sigma @ omega,
            beta @ s2 @ beta,
            omega @ s2 @ omega,
            beta @ s2 @ omega,
            krylov_determinant(sigma, beta),
            krylov_determinant(sigma, omega),
            np.linalg.det(np.column_stack([beta, omega, sigma @ beta])),
            np.linalg.det(np.column_stack([beta, omega, sigma @ omega])),
            k,
        ],
        dtype=float,
    )


def _invariants_with_acceleration(state: np.ndarray) -> np.ndarray:
    sigma = stf5_to_matrix(state[:5])
    vecs = {"omega": state[5:8], "beta": state[8:11], "accel": state[11:14]}
    k = state[14]
    s2 = sigma @ sigma
    out = [np.trace(s2), np.trace(s2 @ sigma), k]
    names = ("omega", "beta", "accel")
    for i, n1 in enumerate(names):
        for n2 in names[i:]:
            u, v = vecs[n1], vecs[n2]
            out += [u @ v, u @ sigma @ v, u @ s2 @ v]
    for n1 in names:
        out.append(krylov_determinant(sigma, vecs[n1]))
    for i, n1 in enumerate(names):
        for n2 in names[i + 1 :]:
            u, v = vecs[n1], vecs[n2]
            out += [
                np.linalg.det(np.column_stack([u, v, sigma @ u])),
                np.linalg.det(np.column_stack([u, v, sigma @ v])),
            ]
    out.append(np.linalg.det(np.column_stack([vecs["omega"], vecs["beta"], vecs["accel"]])))
    return np.array(out, dtype=float)


def _jacobian_rank(func, point: np.ndarray, step: float = 1e-6) -> int:
    n = point.size
    columns = []
    for i in range(n):
        e = np.zeros(n)
        e[i] = step
        columns.append((func(point + e) - func(point - e)) / (2.0 * step))
    jac = np.column_stack(columns)
    scale = max(1.0, float(np.abs(jac).max()))
    return int(np.linalg.matrix_rank(jac, tol=1e-6 * scale))


def _invariants_velocity_split(state: np.ndarray) -> np.ndarray:
    """18-dim state: sigma(5) + omega(3) + beta_RM(3) + beta_MO(3) + A(3) + k(1)."""
    sigma = stf5_to_matrix(state[:5])
    vecs = {
        "omega": state[5:8],
        "beta_RM": state[8:11],
        "beta_MO": state[11:14],
        "accel": state[14:17],
    }
    k = state[17]
    s2 = sigma @ sigma
    out = [np.trace(s2), np.trace(s2 @ sigma), k]
    names = tuple(vecs)
    for i, n1 in enumerate(names):
        for n2 in names[i:]:
            u, v = vecs[n1], vecs[n2]
            out += [u @ v, u @ sigma @ v, u @ s2 @ v]
    for n1 in names:
        out.append(krylov_determinant(sigma, vecs[n1]))
    for i, n1 in enumerate(names):
        for n2 in names[i + 1 :]:
            u, v = vecs[n1], vecs[n2]
            out += [
                np.linalg.det(np.column_stack([u, v, sigma @ u])),
                np.linalg.det(np.column_stack([u, v, sigma @ v])),
            ]
    return np.array(out, dtype=float)


def tf06_invariant_dimension(n_points: int = 5, seed: int = DEFAULT_SEED) -> dict:
    """TF-06. **On the principal stratum, where the generic isotropy is finite**,
    the kinematic state has exactly ``dim(state) - 3`` functionally independent
    SO(3) invariants, and the registered catalogues attain it.

    * ``(sigma, omega, beta, DeltaOmega_k)``: 12 - 3 = **9**;
    * with four-acceleration adjoined: 15 - 3 = **12**;
    * with the velocity-frame split ``beta -> (beta_RM, beta_MO)`` as well:
      18 - 3 = **15**.

    The stratum qualifier is not decorative: ``dim - 3`` is the count only where
    the generic orbit is three-dimensional. A single axial vector alone (dim 3)
    has isotropy ``U(1)``, a two-dimensional orbit, and therefore ONE invariant
    rather than zero; the counterexample is reported below so that the rule is
    never applied off-stratum.

    The signed budget projection ``x_C`` is ONE function on this space. The
    quantitative content of the tensor upgrade is therefore exact: the scalar
    resolves one of nine (respectively twelve, fifteen) invariant directions.
    Resolving a direction in the INVARIANT space is not the same as identifying
    it from data -- that is the separate question governed by the response rank
    (TF-10) and by partial identification.
    """
    rng = np.random.default_rng(seed + 3)
    ranks_12, ranks_15, ranks_18 = [], [], []
    for _ in range(int(n_points)):
        ranks_12.append(_jacobian_rank(_invariants_sigma_omega_beta_k, rng.normal(size=12)))
        ranks_15.append(_jacobian_rank(_invariants_with_acceleration, rng.normal(size=15)))
        ranks_18.append(_jacobian_rank(_invariants_velocity_split, rng.normal(size=18)))

    # off-stratum counterexample: one axial vector alone has isotropy U(1)
    single_vector_rank = _jacobian_rank(
        lambda v: np.array([float(v @ v)]), rng.normal(size=3)
    )

    ok = (
        all(r == 9 for r in ranks_12)
        and all(r == 12 for r in ranks_15)
        and all(r == 15 for r in ranks_18)
        and single_vector_rank == 1
    )
    return {
        "proposition": "TF-06-INVARIANT-DIMENSION",
        "scope": "principal stratum only (finite generic isotropy)",
        "state_dim_without_acceleration": 12,
        "expected_invariant_dim_without_acceleration": 9,
        "measured_ranks_without_acceleration": ranks_12,
        "state_dim_with_acceleration": 15,
        "expected_invariant_dim_with_acceleration": 12,
        "measured_ranks_with_acceleration": ranks_15,
        "state_dim_with_velocity_split": 18,
        "expected_invariant_dim_with_velocity_split": 15,
        "measured_ranks_with_velocity_split": ranks_18,
        "off_stratum_counterexample": {
            "state": "single vector, dim 3, isotropy U(1)",
            "naive_dim_minus_3": 0,
            "actual_invariant_dim": single_vector_rank,
        },
        "x_C_resolves": 1,
        "generic_orbit_dimension_on_principal_stratum": 3,
        "not_an_identifiability_claim": True,
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# TF-07  the budget sees only part of the quadratic sector
# --------------------------------------------------------------------------
def tf07_budget_morphology_splitting(
    seed: int = DEFAULT_SEED, w_eos: float = 0.0, omega_m: float = 0.3153
) -> dict:
    """TF-07. The Gauss-Friedmann budget functional **factors through** the four
    invariants ``{tr sigma^2, omega.omega, beta.beta, DeltaOmega_k}``. It
    therefore has ZERO derivative along the remaining quadratic invariant -- the
    tilt-vorticity helicity ``beta.omega`` -- and along every direction
    transverse to their common level set.

    Stated this way rather than by polynomial grading, because the repository's
    tilt term is ``Omega_tilt = (1 + w) Omega_m sinh^2(beta)``, an even function
    of ``beta.beta`` and NOT the monomial ``beta^2``: the budget does depend on
    higher even powers of ``beta.beta``, so a naive "supported on degree two,
    vanishes on degree three and above" claim would be false. What survives --
    and is what the programme actually needs -- is the factorisation.

    Two consequences, both positive:

    1. The blindness of ``x_C`` is structural and quantified, not a defect of an
       estimator: the constraint itself cannot see morphology, and the invisible
       directions begin already at quadratic order with the helicity.
    2. Because the budget factors through a four-dimensional subalgebra, the
       morphology programme is not competing with it for the same information;
       the two can be reported side by side without double counting.

    Verification is by two independent routes: an explicit witness that moves
    the helicity while holding all four budget invariants (hence ``x_C``)
    exactly fixed, and a COMPUTED gradient test showing the budget gradient
    lies in the span of the four invariant gradients while the helicity gradient
    does not.
    """
    rng = np.random.default_rng(seed + 8)

    def budget_from_state(state: np.ndarray) -> float:
        """Repo-faithful x_C: sigma2 - w2 + omega_tilt + delta_omega_k."""
        sigma = stf5_to_matrix(state[:5])
        omega = state[5:8]
        beta = state[8:11]
        k = state[11]
        sigma2 = float(np.trace(sigma @ sigma)) / 6.0
        w2 = float(omega @ omega) / 6.0
        omega_tilt = (1.0 + w_eos) * omega_m * float(np.sinh(np.linalg.norm(beta)) ** 2)
        return sigma2 - w2 + omega_tilt + float(k)

    def four_invariants(state: np.ndarray) -> np.ndarray:
        sigma = stf5_to_matrix(state[:5])
        return np.array(
            [
                float(np.trace(sigma @ sigma)),
                float(state[5:8] @ state[5:8]),
                float(state[8:11] @ state[8:11]),
                float(state[11]),
            ]
        )

    def helicity(state: np.ndarray) -> float:
        return float(state[5:8] @ state[8:11])

    def grad(fn, point, step=1e-6):
        g = np.zeros(point.size)
        for i in range(point.size):
            e = np.zeros(point.size)
            e[i] = step
            g[i] = (fn(point + e) - fn(point - e)) / (2.0 * step)
        return g

    residuals, helicity_residuals = [], []
    for _ in range(20):
        point = rng.normal(size=12) * 0.3
        span = np.column_stack(
            [grad(lambda s, i=i: four_invariants(s)[i], point) for i in range(4)]
        )
        proj = span @ np.linalg.pinv(span)
        gb = grad(budget_from_state, point)
        gh = grad(helicity, point)
        residuals.append(
            float(np.linalg.norm(gb - proj @ gb) / max(1e-12, np.linalg.norm(gb)))
        )
        helicity_residuals.append(
            float(np.linalg.norm(gh - proj @ gh) / max(1e-12, np.linalg.norm(gh)))
        )
    budget_factors = bool(max(residuals) < 1e-5)
    helicity_transverse = bool(min(helicity_residuals) > 0.1)

    # explicit witness
    sigma5 = np.array([1.0, 0.3, 0.2, -0.1, 0.4])
    omega = np.array([0.5, 0.1, -0.2])
    beta_a = np.array([0.4, 0.0, 0.0])
    angle = 1.1
    rot_z = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle), np.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    beta_b = rot_z @ beta_a
    k = 0.01
    state_a = np.concatenate([sigma5, omega, beta_a, [k]])
    state_b = np.concatenate([sigma5, omega, beta_b, [k]])
    entries_equal = bool(
        np.allclose(four_invariants(state_a), four_invariants(state_b), rtol=0.0, atol=1e-12)
    )
    xc_equal = bool(abs(budget_from_state(state_a) - budget_from_state(state_b)) <= 1e-12)
    helicity_moves = bool(abs(helicity(state_a) - helicity(state_b)) > 1e-6)

    return {
        "proposition": "TF-07-BUDGET-MORPHOLOGY-SPLIT",
        "statement": "the budget factors through {tr_sigma2, omega2, beta2, delta_omega_k}",
        "tilt_term_form": "Omega_tilt = (1+w) Omega_m sinh^2(|beta|), an even function of beta.beta",
        "quadratic_invariants": ["tr_sigma2", "omega2", "beta2", "beta_dot_omega"],
        "budget_gradient_max_relative_residual": max(residuals),
        "budget_factors_through_four": budget_factors,
        "helicity_gradient_min_transverse_fraction": min(helicity_residuals),
        "helicity_is_transverse": helicity_transverse,
        "witness_budget_invariants_equal": entries_equal,
        "witness_x_C_equal": xc_equal,
        "witness_helicity_moves": helicity_moves,
        "invisible_invariant_directions": 8,
        "ok": bool(
            budget_factors and helicity_transverse and entries_equal and xc_equal and helicity_moves
        ),
    }


# --------------------------------------------------------------------------
# TF-08  the canonical scalar summary of a vector saturation
# --------------------------------------------------------------------------
def tf08_product_gauge_is_max(n_samples: int = 2000, seed: int = DEFAULT_SEED) -> dict:
    """TF-08. For a product of per-sector balls the Minkowski gauge equals the
    MAXIMUM of the per-sector saturations.

    This is the constructive answer to "how does a vector saturation collapse to
    one comparable number without reintroducing an arbitrary convention": it
    does not collapse by a signed sum (the legacy ``x_C`` pathology) but by an
    L-infinity combination, and that combination is forced -- it IS the gauge of
    the registered admissible body. The exceedance functional inherits the same
    form, ``E = max(rho - 1, 0)``, so a multi-sector exceedance is refuted by
    its worst sector and by nothing else.

    Verified against a bisection evaluation of the gauge definition
    ``rho_A(u) = inf{lambda > 0 : u in lambda A}``, i.e. the gauge is never
    assumed to be the max -- it is measured and then compared.
    """
    rng = np.random.default_rng(seed + 4)
    max_err = 0.0
    for _ in range(int(n_samples)):
        n_sectors = int(rng.integers(2, 5))
        radii = np.exp(rng.normal(size=n_sectors))
        vectors = [rng.normal(size=3) * np.exp(rng.normal()) for _ in range(n_sectors)]
        saturations = [float(np.linalg.norm(v) / r) for v, r in zip(vectors, radii)]

        def inside(scale: float) -> bool:
            return all(
                np.linalg.norm(v) <= scale * r + 1e-15 for v, r in zip(vectors, radii)
            )

        lo, hi = 0.0, max(1.0, 2.0 * max(saturations))
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if inside(mid):
                hi = mid
            else:
                lo = mid
        max_err = max(max_err, abs(hi - max(saturations)) / max(1.0, max(saturations)))
    return {
        "proposition": "TF-08-PRODUCT-GAUGE-MAX",
        "identity": "rho_{prod A_j}(u) == max_j ||u_j|| / B_j",
        "exceedance_form": "E = max(rho - 1, 0)",
        "max_relative_error": max_err,
        "n_samples": int(n_samples),
        "ok": bool(max_err <= 1e-9),
    }


# --------------------------------------------------------------------------
# TF-09  the exact, model-free parity test
# --------------------------------------------------------------------------
def tf09_parity_sign_exactness(n_samples: int = 200_000, seed: int = DEFAULT_SEED) -> dict:
    """TF-09. Let ``psi`` be a reflection-odd invariant. Suppose

      (H1) the null law of the data is invariant under a reflection ``P`` that
           also fixes the analysis geometry (mask, weighting, pixelisation);
      (H2) the ESTIMATOR is exactly ``P``-equivariant, ``psi_hat . P = -psi_hat``,
           including mask deconvolution, regularisation and weighting;
      (H3) ``P(psi_hat = 0) = 0`` under the null.

    Then the law of ``psi_hat`` is symmetric about zero, so its SIGN is exactly
    Bernoulli(1/2) and is independent of its magnitude -- with no covariance
    model, no mock ensemble and no asymptotics.

    (H3) is not cosmetic and it FAILS on named strata: on the axisymmetric locus
    ``Delta_sigma = 0`` the Krylov chain of any vector is rank-deficient and
    ``K_beta`` vanishes identically, and any sector carrying MISSING_COMPONENT
    gives ``psi_hat = 0`` for every listed pseudoscalar. The test is undefined
    there and must abstain rather than report a sign.

    Why the proposition matters. Reflection through the Galactic plane fixes any
    latitude-symmetric mask ``|b| > b_cut`` and any parity-symmetric noise or
    foreground-variance model, so under (H1)-(H3) the exactness survives the
    modelling failures -- mask coupling, anisotropic noise, misspecified
    covariance scale -- that make every EVEN statistic conditional on a null
    ensemble. (H2) is the binding practical hypothesis: real selection functions
    and point-source holes are not ``b -> -b`` symmetric, and any such asymmetry
    must be carried as a declared violation rather than assumed away.

    COMBINATION WARNING. Independence of sign from magnitude is a statement
    about ONE statistic. Signs across depth windows or nested mask rungs are NOT
    independent -- TF-11 shows nested rungs generate a filtration, hence maximal
    dependence -- so a binomial pooling of rung signs is invalid. Combination
    must go through a dependence-agnostic combiner (the registered
    arithmetic-mean e-value merge, valid under arbitrary dependence).

    The demonstration contrasts three reflection-symmetric nulls of increasing
    anisotropy. The sign statistic holds its exact calibration in all three,
    while the even statistic's SCALE moves by more than an order of magnitude --
    which is what breaks a null-ensemble calibration. (Its mean stays zero by
    symmetry of the construction; the calibration failure is in the tails, not
    the centre.)
    """
    rng = np.random.default_rng(seed + 5)
    results = []
    for label, scales in (
        ("isotropic", (1.0, 1.0, 1.0)),
        ("anisotropic_parity_symmetric", (1.0, 0.4, 2.5)),
        ("extreme_anisotropy_parity_symmetric", (0.2, 3.0, 1.0)),
    ):
        d = np.diag(np.array(scales, dtype=float))
        m = rng.normal(size=(int(n_samples), 3, 3))
        m = 0.5 * (m + np.transpose(m, (0, 2, 1)))
        m = m - np.eye(3)[None, :, :] * np.trace(m, axis1=1, axis2=2)[:, None, None] / 3.0
        m = np.einsum("ij,njk,kl->nil", d, m, d)
        beta = rng.normal(size=(int(n_samples), 3)) @ d
        pseudo = np.array(
            [krylov_determinant(m[i], beta[i]) for i in range(int(n_samples))]
        )
        even = np.array([beta[i] @ m[i] @ beta[i] for i in range(int(n_samples))])
        frac = float(np.mean(pseudo > 0.0))
        se = float(np.sqrt(0.25 / n_samples))
        results.append(
            {
                "null": label,
                "P_positive": frac,
                "three_sigma_halfwidth": 3.0 * se,
                "within_three_sigma": bool(abs(frac - 0.5) <= 3.0 * se),
                "even_statistic_sd": float(even.std()),
                "even_statistic_mean": float(even.mean()),
                "pseudoscalar_exact_zero_fraction": float(np.mean(pseudo == 0.0)),
            }
        )

    # (H3) failure demonstration on the axisymmetric stratum
    axi = np.diag([2.0, -1.0, -1.0])
    rot = _random_rotation(rng)
    axi = rot @ axi @ rot.T
    degenerate = np.array(
        [abs(krylov_determinant(axi, rng.normal(size=3))) for _ in range(2000)]
    )
    scale_ratio = results[2]["even_statistic_sd"] / results[0]["even_statistic_sd"]
    return {
        "proposition": "TF-09-PARITY-SIGN-EXACTNESS",
        "statement": "under (H1) reflection-symmetric null, (H2) P-equivariant estimator, (H3) no atom at zero: sign ~ Bernoulli(1/2) exactly, independent of magnitude",
        "hypotheses": ("reflection_symmetric_null", "P_equivariant_estimator", "no_atom_at_zero"),
        "requires_covariance_model": False,
        "requires_mock_ensemble": False,
        "combination_rule": "arbitrary-dependence e-value merge; binomial pooling across nested rungs is INVALID",
        "cells": results,
        "even_statistic_scale_ratio_extreme_over_isotropic": scale_ratio,
        "even_statistic_scale_moves": bool(scale_ratio > 10.0),
        "h3_failure_stratum": {
            "stratum": "Delta_sigma = 0 (axisymmetric shear)",
            "max_abs_pseudoscalar": float(degenerate.max()),
            "identically_zero": bool(degenerate.max() < 1e-10),
        },
        "ok": bool(
            all(cell["within_three_sigma"] for cell in results)
            and scale_ratio > 10.0
            and degenerate.max() < 1e-10
        ),
    }


# --------------------------------------------------------------------------
# TF-10  local/global separation and the missing status
# --------------------------------------------------------------------------
def tf10_local_global_separation() -> dict:
    """TF-10. The dipole alone cannot separate a global tilt from a local boost
    (rank 3 of 6 parameters), but any channel that responds to the observer
    boost ALONE -- the aberration ``l <-> l+1`` coupling, or the locked-coefficient
    kinematic quadrupole -- restores full rank.

    This is the positive identification statement for research axis (a): the
    local boost sector is over-determined once a boost-only channel is
    registered, so the global tilt is identified as the residual rather than
    assumed away by a subtraction convention.

    The second half of the proposition is the status refinement the review note
    requires. As the boost-only channel weakens, the joint response stays FULL
    RANK while the minimum principal angle between the local and global tangent
    spaces goes to zero. Full rank with a vanishing angle is a distinct state
    from rank deficiency and must not be reported as ``SUM_ONLY``: the correct
    status is ``WEAKLY_IDENTIFIED``, gated on the pair (minimum principal angle,
    minimum singular value) rather than on the angle alone.
    """
    t_rm = 0.6 * np.eye(3)
    t_mo = 1.0 * np.eye(3)
    r_dipole = np.hstack([t_rm, t_mo])

    def principal_angles(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        ql, _ = np.linalg.qr(left)
        qr_, _ = np.linalg.qr(right)
        s = np.clip(np.linalg.svd(ql.T @ qr_, compute_uv=False), -1.0, 1.0)
        return np.arccos(s)

    ladder = []
    for amplitude in (0.85, 0.10, 0.01, 0.001):
        r_full = np.vstack(
            [r_dipole, np.hstack([np.zeros((3, 3)), amplitude * np.eye(3)])]
        )
        rank = int(np.linalg.matrix_rank(r_full))
        angle = float(principal_angles(r_full[:, :3], r_full[:, 3:]).min())
        sv = np.linalg.svd(r_full, compute_uv=False)
        if rank < 6:
            status = "SUM_ONLY"
        elif angle <= 0.1:
            status = "WEAKLY_IDENTIFIED"
        else:
            status = "SEPARABLE_CANDIDATE"
        ladder.append(
            {
                "boost_only_channel_amplitude": amplitude,
                "rank": rank,
                "min_principal_angle_rad": angle,
                "condition_number": float(sv[0] / sv[-1]),
                "status": status,
            }
        )
    dipole_rank = int(np.linalg.matrix_rank(r_dipole))
    weak_cells = [c for c in ladder if c["status"] == "WEAKLY_IDENTIFIED"]
    return {
        "proposition": "TF-10-LOCAL-GLOBAL-SEPARATION",
        "parameter_dimension": 6,
        "dipole_only_rank": dipole_rank,
        "dipole_only_status": "NON_IDENTIFIED",
        "ladder": ladder,
        "weakly_identified_is_full_rank": bool(all(c["rank"] == 6 for c in weak_cells)),
        "gate": "(min_principal_angle, min_singular_value) jointly, not angle alone",
        "ok": bool(dipole_rank == 3 and ladder[0]["status"] == "SEPARABLE_CANDIDATE" and weak_cells),
    }


# --------------------------------------------------------------------------
# TF-11  the nested-mask path is a reverse martingale
# --------------------------------------------------------------------------
def tf11_mask_path_reverse_martingale(
    n_samples: int = 200_000, seed: int = DEFAULT_SEED
) -> dict:
    """TF-11. A nested mask ladder generates a DECREASING filtration. If -- and
    only if -- every rung reports the conditional expectation of the SAME
    full-sky target given the data it retains, the ladder is a reverse
    martingale, the reversed finite sequence is an ordinary martingale, and
    Doob's inequality calibrates the whole path with no new mocks:

        P( max_j |M_j| >= lambda * sd(M_full) ) <= 1 / lambda^2 .

    The design trap this closes is concrete and is the current practice the
    review note flags: if each rung is instead renormalised to its own
    rung-specific target -- the natural thing to do when fitting each cut
    independently -- the martingale property is destroyed and the observed
    path excursions violate the bound by a wide margin. A ZoA morphology path
    is therefore not merely a plot of independently fitted cuts; it is a
    sequential object whose calibration is free if it is built correctly and
    absent if it is not.
    """
    rng = np.random.default_rng(seed + 6)
    n_modes = 64
    x = rng.normal(size=(int(n_samples), n_modes))
    retained = (64, 48, 32, 24, 16, 12, 8, 4)
    correct = np.column_stack([x[:, :k].sum(axis=1) / n_modes for k in retained])
    naive = np.column_stack([x[:, :k].mean(axis=1) for k in retained])
    shrunk = correct * np.array([0.9**j for j in range(len(retained))])[None, :]

    def martingale_defect(path: np.ndarray) -> float:
        """max over rungs and deciles of |E[M_j - M_{j+1} | F_{j+1}]|, scaled."""
        worst = 0.0
        scale = float(path[:, 0].std())
        for j in range(path.shape[1] - 1):
            cond = path[:, j + 1]
            edges = np.quantile(cond, np.linspace(0.0, 1.0, 11))
            idx = np.clip(np.searchsorted(edges, cond, side="right") - 1, 0, 9)
            for b in range(10):
                sel = idx == b
                if sel.sum() < 50:
                    continue
                diff = float((path[sel, j] - path[sel, j + 1]).mean())
                worst = max(worst, abs(diff) / scale)
        return worst

    defect_correct = martingale_defect(correct)
    defect_shrunk = martingale_defect(shrunk)

    mean_full = float(correct[:, 0].mean())
    sd_full = float(correct[:, 0].std())
    sup_correct = np.abs(correct).max(axis=1) / sd_full
    sup_naive = np.abs(naive).max(axis=1) / float(naive[:, 0].std())

    cells = []
    holds = True
    for lam in (1.5, 2.0, 2.5, 3.0, 4.0):
        empirical = float(np.mean(sup_correct >= lam))
        bound = 1.0 / lam**2
        holds = holds and empirical <= bound
        cells.append(
            {
                "lambda": lam,
                "empirical_correct": empirical,
                "doob_bound": bound,
                "holds": bool(empirical <= bound),
                "empirical_naive_renormalisation": float(np.mean(sup_naive >= lam)),
            }
        )
    naive_violates = any(c["empirical_naive_renormalisation"] > c["doob_bound"] for c in cells)
    return {
        "proposition": "TF-11-MASK-PATH-MARTINGALE",
        "requirement": "every rung reports E[full-sky target | retained data]",
        "bound_requires_centred_target": True,
        "measured_mean_of_full_sky_target": mean_full,
        "centred_within_mc_error": bool(abs(mean_full) <= 4.0 * sd_full / np.sqrt(n_samples)),
        "martingale_defect_correct_path": defect_correct,
        "martingale_defect_shrunk_control_path": defect_shrunk,
        "direct_martingale_test_separates_control": bool(defect_shrunk > 10.0 * max(defect_correct, 1e-6)),
        "cells": cells,
        "naive_renormalisation_violates_bound": bool(naive_violates),
        "n_samples": int(n_samples),
        "ok": bool(
            holds
            and naive_violates
            and defect_correct < 0.02
            and defect_shrunk > 10.0 * max(defect_correct, 1e-6)
        ),
    }


# --------------------------------------------------------------------------
# TF-12  the acceleration sector is slaved, not free
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class EulerSlavingPremises:
    """Premises TF-12 is conditional on. All must be declared with the result."""

    perfect_fluid: bool = True
    vanishing_frame_heat_flux: bool = True
    vanishing_anisotropic_stress: bool = True
    barotropic_or_constant_w: bool = True
    gradient_regularity_registered: bool = False  # no eps_g exists in-repo

    def as_tuple(self) -> tuple:
        return (
            "perfect_fluid",
            "vanishing_frame_heat_flux",
            "vanishing_anisotropic_stress",
            "barotropic_or_constant_w",
            "gradient_regularity_registered",
        )


def tf12_acceleration_euler_slaving(
    assumed_gradient_bound: float = 3.559629e-06,
    premises: EulerSlavingPremises | None = None,
) -> dict:
    """TF-12 (CONDITIONAL). The four-acceleration is not an independent kinematic
    degree of freedom for a perfect fluid: the 1+3 momentum equation

        (mu + p) A_a = - D_a p          (D_a the projected spatial gradient)

    slaves it to the pressure gradient. Writing ``p = w mu`` and
    ``c_s^2 = dp/dmu``,

        A_a / Theta = - [ c_s^2 / (1 + w) ] * ( D_a ln mu ) / Theta ,

    so with an ASSUMED dimensionless gradient bound
    ``|D_a ln mu| / Theta <= eps_g`` and the standard normalisation
    ``A2_std = A_a A^a / (6 H^2) = (3/2) |A/Theta|^2``:

        A2_max^Euler(w) = (3/2) [ c_s^2 / (1 + w) ]^2 eps_g^2 .

    PROVENANCE WARNING, load-bearing. **No ``eps_g`` is registered anywhere in
    the repository.** The default value here is a PLACEHOLDER numerically equal
    to ``C.eps2`` (the Commann/PR3 temperature quadrupole amplitude, a
    dimensionless ``Delta T / T``), which is NOT a bound on
    ``|D_a ln mu| / Theta`` and carries no MES or other authority. It is
    supplied only so that the closed form can be exercised; the epoch table
    below is a planning object, not a result, and its absolute scale is
    meaningless until a gradient bound is derived and registered with its own
    premises. The SHAPE of the result -- the ``[c_s^2/(1+w)]^2`` factor and its
    zero at ``c_s^2 = 0`` -- is what this proposition establishes.

    Three positive consequences, none of which is a MES-branch claim:

    1. **The geodesic premise becomes a derived late-time limit rather than an
       assumption.** For pressureless matter ``c_s^2 -> 0`` gives
       ``A2_max -> 0``: the ``u_dot = 0`` premise under which the registered MES
       shear and vorticity anchors are verified is recovered, with an explicit
       remainder rather than by fiat.
    2. **The sector that currently carries ``NO_MES_ANCHOR`` acquires a typed,
       epoch-conditional ceiling from a different authority** (the momentum
       constraint, not MES). It must be registered as a distinct authority kind
       with its own premises -- it is emphatically NOT a rehabilitation of the
       refuted non-geodesic MES triple.
    3. **The acceleration sector is congruence-typed by construction.** The same
       spacetime has ``A = 0`` for the matter congruence and ``A != 0`` for the
       photon-baryon congruence before decoupling; the ceiling is a statement
       about a declared ``congruence``, which is why the state must carry that
       field.

    Returned ceilings are conditional planning numbers, not results.
    """
    prem = premises or EulerSlavingPremises()
    eps = float(assumed_gradient_bound)

    def ceiling(cs2: float, w: float) -> float:
        return 1.5 * (cs2 / (1.0 + w)) ** 2 * eps**2

    epochs = {
        "pressureless_matter": {"c_s2": 0.0, "w": 0.0},
        "radiation": {"c_s2": 1.0 / 3.0, "w": 1.0 / 3.0},
        "photon_baryon_tight_coupling_R1": {"c_s2": 1.0 / 6.0, "w": 1.0 / 6.0},
    }
    table = {}
    for name, params in epochs.items():
        table[name] = {
            **params,
            "slaving_factor": params["c_s2"] / (1.0 + params["w"]),
            "A2_max_euler": ceiling(params["c_s2"], params["w"]),
        }

    # algebraic self-checks of the closed form
    radiation_factor = table["radiation"]["slaving_factor"]
    factor_ok = abs(radiation_factor - 0.25) <= 1e-15
    geodesic_ok = table["pressureless_matter"]["A2_max_euler"] == 0.0
    monotone_ok = (
        table["pressureless_matter"]["A2_max_euler"]
        < table["photon_baryon_tight_coupling_R1"]["A2_max_euler"]
        < table["radiation"]["A2_max_euler"]
    )
    scaling_ok = abs(ceiling(1.0 / 3.0, 1.0 / 3.0) / eps**2 - 1.5 * 0.0625) <= 1e-15

    return {
        "proposition": "TF-12-ACCELERATION-EULER-SLAVING",
        "status": "ACTIVE_CONDITIONAL",
        "authority_kind": "MOMENTUM_CONSTRAINT_NOT_MES",
        "premises": prem.as_tuple(),
        "closed_form": "A2_max_euler = (3/2) [c_s^2/(1+w)]^2 eps_g^2",
        "assumed_gradient_bound_used": eps,
        "gradient_bound_provenance": (
            "PLACEHOLDER numerically equal to C.eps2 (a Delta T / T quadrupole "
            "amplitude); no eps_g is registered in-repo; carries no MES authority"
        ),
        "gradient_regularity_registered": prem.gradient_regularity_registered,
        "absolute_scale_meaningful": False,
        "epochs": table,
        "geodesic_limit_recovered": bool(geodesic_ok),
        "radiation_slaving_factor_is_one_quarter": bool(factor_ok),
        "monotone_in_sound_speed": bool(monotone_ok),
        "forbidden_use": (
            "rehabilitating the refuted non-geodesic MES acceleration triple",
            "an acceleration saturation reported without its congruence and epoch",
        ),
        "ok": bool(factor_ok and geodesic_ok and monotone_ok and scaling_ok),
    }


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------
def run_all(seed: int = DEFAULT_SEED, fast: bool = False) -> dict:
    """Execute every proposition and return one receipt.

    ``fast=True`` reduces Monte Carlo sizes for CI smoke runs; the exact and
    symbolic propositions are unaffected.
    """
    scale = 0.05 if fast else 1.0
    results = [
        tf01_parity_typing(n_samples=max(20, int(300 * scale)), seed=seed),
        tf02_catalogue_completion(seed=seed),
        tf03_krylov_syzygy(n_samples=max(20, int(400 * scale)), seed=seed),
        tf04_cayley_hamilton_reduction(n_samples=max(20, int(400 * scale)), seed=seed),
        tf05_shape_discriminant_identity(n_samples=max(2000, int(200_000 * scale)), seed=seed),
        tf06_invariant_dimension(n_points=3 if fast else 5, seed=seed),
        tf07_budget_morphology_splitting(seed=seed),
        tf08_product_gauge_is_max(n_samples=max(50, int(2000 * scale)), seed=seed),
        tf09_parity_sign_exactness(n_samples=max(20_000, int(200_000 * scale)), seed=seed),
        tf10_local_global_separation(),
        tf11_mask_path_reverse_martingale(n_samples=max(20_000, int(200_000 * scale)), seed=seed),
        tf12_acceleration_euler_slaving(),
    ]
    by_id = {r["proposition"]: r for r in results}
    failed = tuple(pid for pid, r in by_id.items() if not r["ok"])
    return {
        "oracle_id": ORACLE_ID,
        "seed": int(seed),
        "fast": bool(fast),
        "propositions": by_id,
        "n_propositions": len(results),
        "failed": failed,
        "ok": not failed,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    report = run_all()
    for pid, res in report["propositions"].items():
        print(f"{'PASS' if res['ok'] else 'FAIL'}  {pid}")
    print()
    print(json.dumps({k: v for k, v in report.items() if k != "propositions"}, indent=2))
