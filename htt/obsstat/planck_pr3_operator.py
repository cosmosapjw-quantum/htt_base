"""Planck PR3 low-ell operator closure on synthetic or admitted inputs.

The numerical operator in this module is shared by observation and matched
FFP10 rows.  It contains no data locator and no authorization logic.  In
particular, a profiling subset can extract features but cannot construct a
p-value, and a missing global response is an explicit abstention.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import math
from typing import Mapping, Sequence

import numpy as np

from .lowell_poles import angular_momentum_power_tensor
from .planck_post275_lane import (
    ObservationInclusiveMaxScan,
    PlanckLaneContractError,
    observation_inclusive_max_scan,
    validate_full_joint_covariance,
)


SCHEMA_VERSION = "htt.obsstat.planck_pr3_lowell_operator.v1"
REQUIRED_COMPONENTS = ("SMICA", "Commander")
EXPECTED_FFP10_NULL_ROWS = 999
LMIN = 2
LMAX = 5
COMPONENT_FEATURE_IDS = (
    "cl_l2",
    "cl_l3",
    "cl_l4",
    "cl_l5",
    "parity_even_over_odd_l2_l5",
    "power_tensor_gap_l2",
    "power_tensor_gap_l3",
    "multipole_l2_absdot",
    "multipole_l3_absdot_0",
    "multipole_l3_absdot_1",
    "multipole_l3_absdot_2",
    "multipole_plane_alignment_max_l2_l3",
)
COMPONENT_FEATURE_UNITS = (
    "microK_CMB^2",
    "microK_CMB^2",
    "microK_CMB^2",
    "microK_CMB^2",
    "dimensionless",
    "dimensionless",
    "dimensionless",
    "dimensionless",
    "dimensionless",
    "dimensionless",
    "dimensionless",
    "dimensionless",
)
JOINT_FEATURE_IDS = tuple(
    f"{component}.{feature}"
    for component in REQUIRED_COMPONENTS
    for feature in COMPONENT_FEATURE_IDS
)
JOINT_FEATURE_UNITS = COMPONENT_FEATURE_UNITS + COMPONENT_FEATURE_UNITS
MULTIPOLE_VECTOR_CONVENTION = (
    "Majorana polynomial sum_m sqrt(C(2l,l+m)) a_lm z^(l+m); "
    "orthonormal Condon-Shortley harmonics; "
    "z=exp(i*phi) cot(theta/2); antipodal axes; "
    "largest-absolute Cartesian component positive"
)
GLOBAL_CLAIM_BOUNDARY = "ABSTAIN_GLOBAL_RESPONSE_UNAVAILABLE"
JOINT_CUTSKY_ESTIMATOR_ID = "joint_weighted_real_harmonic_l0_l5_retain_l2_l5:v1"
JOINT_CUTSKY_TOTAL_DIMENSION = 36
JOINT_CUTSKY_RETAINED_DIMENSION = 32


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - exercised without optional dep
        raise PlanckLaneContractError(
            "healpy is required by the Planck operator"
        ) from exc
    return hp


def _sha256_array(array: np.ndarray, *, role: str) -> str:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(value.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(value.shape).encode("ascii") + b"\0")
    digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _finite_vector(values: object, *, label: str) -> np.ndarray:
    try:
        vector = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlanckLaneContractError(f"{label} must be numeric") from exc
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise PlanckLaneContractError(f"{label} must be a finite non-empty vector")
    return vector


def _canonical_axis(vector: object) -> np.ndarray:
    axis = _finite_vector(vector, label="multipole axis")
    if axis.shape != (3,):
        raise PlanckLaneContractError("multipole axis must have three components")
    norm = float(np.linalg.norm(axis))
    if norm <= 0.0:
        raise PlanckLaneContractError("multipole axis has zero norm")
    axis = axis / norm
    pivot = int(np.argmax(np.abs(axis)))
    if axis[pivot] < 0.0:
        axis = -axis
    return axis


def _dense_real_alm(alm: object, *, ell: int, lmax: int) -> dict[int, complex]:
    hp = _healpy()
    values = np.asarray(alm, dtype=np.complex128)
    if values.ndim != 1 or values.size != hp.Alm.getsize(lmax):
        raise PlanckLaneContractError("packed alm shape does not match lmax")
    if not 1 <= ell <= lmax:
        raise PlanckLaneContractError("multipole ell is outside the packed alm")
    m0 = complex(values[hp.Alm.getidx(lmax, ell, 0)])
    scale = max(1.0, float(np.max(np.abs(values))))
    if abs(m0.imag) > 1e-12 * scale:
        raise PlanckLaneContractError("m=0 alm violates the real-map convention")
    dense: dict[int, complex] = {0: complex(m0.real, 0.0)}
    for m in range(1, ell + 1):
        positive = complex(values[hp.Alm.getidx(lmax, ell, m)])
        dense[m] = positive
        dense[-m] = ((-1) ** m) * positive.conjugate()
    return dense


def _root_vector(root: complex | None) -> np.ndarray:
    if root is None:
        return np.array([0.0, 0.0, 1.0])
    radius2 = float(root.real * root.real + root.imag * root.imag)
    denominator = 1.0 + radius2
    return np.array(
        [
            2.0 * root.real / denominator,
            2.0 * root.imag / denominator,
            (radius2 - 1.0) / denominator,
        ],
        dtype=float,
    )


def _minimum_antipodal_matching(
    vectors: Sequence[np.ndarray],
) -> tuple[tuple[int, int], ...]:
    if len(vectors) % 2:
        raise PlanckLaneContractError("Majorana roots must have even cardinality")

    def solve(indices: tuple[int, ...]) -> tuple[float, tuple[tuple[int, int], ...]]:
        if not indices:
            return 0.0, ()
        first = indices[0]
        best: tuple[float, tuple[tuple[int, int], ...]] | None = None
        for position in range(1, len(indices)):
            second = indices[position]
            remaining = indices[1:position] + indices[position + 1 :]
            rest_cost, rest_pairs = solve(remaining)
            cost = float(np.linalg.norm(vectors[first] + vectors[second])) + rest_cost
            candidate = (cost, ((first, second),) + rest_pairs)
            if (
                best is None
                or candidate[0] < best[0] - 1e-15
                or (abs(candidate[0] - best[0]) <= 1e-15 and candidate[1] < best[1])
            ):
                best = candidate
        assert best is not None
        return best

    return solve(tuple(range(len(vectors))))[1]


def extract_multipole_vectors(
    alm: object,
    *,
    ell: int,
    lmax: int,
    root_tolerance: float = 1e-7,
) -> np.ndarray:
    """Return the genuine unordered antipodal Maxwell axes for one multipole.

    Roots at projective infinity are retained.  A power-tensor principal axis
    is never substituted for a missing or ill-conditioned Majorana root.
    """

    if not math.isfinite(root_tolerance) or not 0.0 < root_tolerance < 1e-2:
        raise PlanckLaneContractError("root tolerance is outside the frozen range")
    dense = _dense_real_alm(alm, ell=ell, lmax=lmax)
    coefficients = np.array(
        [
            math.sqrt(math.comb(2 * ell, ell + m)) * dense[m]
            for m in range(-ell, ell + 1)
        ],
        dtype=np.complex128,
    )
    scale = float(np.max(np.abs(coefficients)))
    if not math.isfinite(scale) or scale <= 0.0:
        raise PlanckLaneContractError("selected multipole has zero power")
    threshold = root_tolerance * scale * 1e-3
    highest = 2 * ell
    while highest >= 0 and abs(coefficients[highest]) <= threshold:
        highest -= 1
    if highest < 0:
        raise PlanckLaneContractError("Majorana polynomial vanished")
    infinity_count = 2 * ell - highest
    descending = coefficients[: highest + 1][::-1]
    finite_roots = list(np.roots(descending)) if highest else []
    roots: list[complex | None] = [complex(value) for value in finite_roots]
    roots.extend([None] * infinity_count)
    if len(roots) != 2 * ell:
        raise PlanckLaneContractError("Majorana projective root count drifted")
    vectors = [_root_vector(root) for root in roots]
    pairs = _minimum_antipodal_matching(vectors)
    axes: list[np.ndarray] = []
    for first, second in pairs:
        residual = float(np.linalg.norm(vectors[first] + vectors[second]))
        if residual > root_tolerance:
            raise PlanckLaneContractError(
                f"Majorana roots fail antipodal reality pairing: {residual:.3e}"
            )
        difference = vectors[first] - vectors[second]
        axes.append(_canonical_axis(difference))
    if len(axes) != ell:
        raise PlanckLaneContractError("multipole-vector cardinality drifted")
    axes.sort(key=lambda row: tuple(float(value) for value in row))
    return np.asarray(axes, dtype=float)


def real_alm_layout(
    *, lmin: int = LMIN, lmax: int = LMAX
) -> tuple[tuple[int, int, str], ...]:
    if not 0 <= lmin <= lmax:
        raise PlanckLaneContractError("invalid real-alm band")
    rows: list[tuple[int, int, str]] = []
    for ell in range(lmin, lmax + 1):
        rows.append((ell, 0, "real"))
        for m in range(1, ell + 1):
            rows.extend(((ell, m, "real"), (ell, m, "imag")))
    return tuple(rows)


def alm_to_real_vector(
    alm: object, *, lmin: int = LMIN, lmax: int = LMAX
) -> np.ndarray:
    hp = _healpy()
    values = np.asarray(alm, dtype=np.complex128)
    if values.ndim != 1 or values.size != hp.Alm.getsize(lmax):
        raise PlanckLaneContractError(
            "packed alm shape does not match mask-inverse band"
        )
    out: list[float] = []
    for ell, m, kind in real_alm_layout(lmin=lmin, lmax=lmax):
        value = values[hp.Alm.getidx(lmax, ell, m)]
        if m == 0:
            if abs(value.imag) > 1e-12 * max(1.0, abs(value.real)):
                raise PlanckLaneContractError("m=0 alm is not real")
            out.append(float(value.real))
        elif kind == "real":
            out.append(math.sqrt(2.0) * float(value.real))
        else:
            out.append(-math.sqrt(2.0) * float(value.imag))
    return np.asarray(out, dtype=float)


def real_vector_to_alm(
    vector: object, *, lmin: int = LMIN, lmax: int = LMAX
) -> np.ndarray:
    hp = _healpy()
    values = _finite_vector(vector, label="real alm vector")
    layout = real_alm_layout(lmin=lmin, lmax=lmax)
    if values.size != len(layout):
        raise PlanckLaneContractError("real alm vector has the wrong dimension")
    alm = np.zeros(hp.Alm.getsize(lmax), dtype=np.complex128)
    cursor = 0
    for ell in range(lmin, lmax + 1):
        alm[hp.Alm.getidx(lmax, ell, 0)] = values[cursor]
        cursor += 1
        for m in range(1, ell + 1):
            real = values[cursor] / math.sqrt(2.0)
            imag = -values[cursor + 1] / math.sqrt(2.0)
            cursor += 2
            alm[hp.Alm.getidx(lmax, ell, m)] = complex(real, imag)
    return alm


@dataclass(frozen=True)
class MaskCouplingInverse:
    matrix: np.ndarray
    inverse: np.ndarray
    singular_values: tuple[float, ...]
    condition_number: float
    lmin: int
    lmax: int
    nside: int
    mask_sha256: str

    @property
    def dimension(self) -> int:
        return self.matrix.shape[0]


@dataclass(frozen=True)
class JointCutSkyOperator:
    """One fixed weighted real-harmonic design shared by every sky row."""

    normal_matrix: np.ndarray
    mask: np.ndarray
    singular_values: tuple[float, ...]
    condition_number: float
    relative_threshold: float
    condition_ceiling: float
    lmin: int
    lmax: int
    retained_lmin: int
    nside: int
    mask_sha256: str
    normal_matrix_sha256: str
    operator_sha256: str
    basis_order: tuple[tuple[int, int, str], ...]
    retained_indices: tuple[int, ...]

    @property
    def dimension(self) -> int:
        return self.normal_matrix.shape[0]

    @property
    def retained_dimension(self) -> int:
        return len(self.retained_indices)


@dataclass(frozen=True)
class JointCutSkyFit:
    """Retained low-ell coefficients and fit diagnostics for one sky row."""

    retained_alm: np.ndarray
    retained_coefficients: np.ndarray
    all_coefficients: np.ndarray
    weighted_residual_norm: float
    operator_sha256: str


def _real_harmonic_design_block(
    nside: int,
    pixels: np.ndarray,
    *,
    lmin: int,
    lmax: int,
) -> np.ndarray:
    """Evaluate a bounded pixel block of the frozen real-harmonic basis."""

    hp = _healpy()
    from scipy.special import sph_harm_y

    theta, phi = hp.pix2ang(nside, pixels)
    layout = real_alm_layout(lmin=lmin, lmax=lmax)
    design = np.empty((pixels.size, len(layout)), dtype=float)
    for column, (ell, m, kind) in enumerate(layout):
        harmonic = sph_harm_y(ell, m, theta, phi)
        if m == 0:
            design[:, column] = harmonic.real
        elif kind == "real":
            design[:, column] = math.sqrt(2.0) * harmonic.real
        else:
            design[:, column] = math.sqrt(2.0) * harmonic.imag
    return design


def _canonical_json_sha256(payload: Mapping[str, object], *, role: str) -> str:
    import json

    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    )
    return "sha256:" + digest.hexdigest()


def build_joint_cutsky_operator(
    mask: object,
    *,
    lmin: int = 0,
    lmax: int = LMAX,
    retained_lmin: int = LMIN,
    relative_threshold: float = 1e-10,
    condition_ceiling: float = 1e8,
) -> JointCutSkyOperator:
    """Build the chunked joint weighted fit for all real modes in one band.

    The PR-315 branch uses ``lmin=0``, ``lmax=5`` and retains ``ell=2..5``.
    Allowing narrower bands is useful only for negative controls; the observed
    worker rejects anything other than the frozen 36-to-32 configuration.
    """

    hp = _healpy()
    weights = _finite_vector(mask, label="analysis mask")
    try:
        nside = hp.npix2nside(weights.size)
    except ValueError as exc:
        raise PlanckLaneContractError("analysis mask is not HEALPix") from exc
    if (
        np.any(weights < 0.0)
        or np.any(weights > 1.0)
        or np.count_nonzero(weights) == 0
    ):
        raise PlanckLaneContractError(
            "analysis mask weights must lie in [0,1] with support"
        )
    if (
        not 0 <= lmin <= retained_lmin <= lmax
        or not 0.0 < relative_threshold < 1.0
        or condition_ceiling <= 1.0
    ):
        raise PlanckLaneContractError("joint cut-sky configuration is invalid")

    basis = real_alm_layout(lmin=lmin, lmax=lmax)
    retained = tuple(
        index for index, (ell, _, _) in enumerate(basis) if ell >= retained_lmin
    )
    normal = np.zeros((len(basis), len(basis)), dtype=float)
    chunk_size = min(weights.size, 65_536)
    for start in range(0, weights.size, chunk_size):
        stop = min(weights.size, start + chunk_size)
        local_weights = weights[start:stop]
        support = local_weights > 0.0
        if not np.any(support):
            continue
        pixels = np.arange(start, stop, dtype=np.int64)[support]
        design = _real_harmonic_design_block(
            nside,
            pixels,
            lmin=lmin,
            lmax=lmax,
        )
        weighted = design * np.sqrt(local_weights[support])[:, None]
        normal += weighted.T @ weighted
    pixel_area = 4.0 * math.pi / weights.size
    normal *= pixel_area
    singular_values = np.linalg.svd(normal, compute_uv=False)
    largest = float(singular_values[0])
    smallest = float(singular_values[-1])
    if smallest <= relative_threshold * largest:
        raise PlanckLaneContractError(
            "joint cut-sky normal matrix is rank deficient at the frozen threshold"
        )
    condition = largest / smallest
    if not math.isfinite(condition) or condition > condition_ceiling:
        raise PlanckLaneContractError(
            "joint cut-sky normal matrix exceeds the frozen condition ceiling"
        )

    mask_sha256 = _sha256_array(weights, role="common_analysis_mask")
    normal_sha256 = _sha256_array(normal, role="joint_cutsky_normal_matrix")
    identity = {
        "estimator_id": JOINT_CUTSKY_ESTIMATOR_ID,
        "lmin": lmin,
        "lmax": lmax,
        "retained_lmin": retained_lmin,
        "basis_order": [list(row) for row in basis],
        "mask_sha256": mask_sha256,
        "normal_matrix_sha256": normal_sha256,
        "relative_threshold": relative_threshold,
        "condition_ceiling": condition_ceiling,
    }
    return JointCutSkyOperator(
        normal_matrix=normal,
        mask=weights.copy(),
        singular_values=tuple(float(value) for value in singular_values),
        condition_number=condition,
        relative_threshold=relative_threshold,
        condition_ceiling=condition_ceiling,
        lmin=lmin,
        lmax=lmax,
        retained_lmin=retained_lmin,
        nside=nside,
        mask_sha256=mask_sha256,
        normal_matrix_sha256=normal_sha256,
        operator_sha256=_canonical_json_sha256(
            identity, role="joint_cutsky_operator_identity"
        ),
        basis_order=basis,
        retained_indices=retained,
    )


def fit_joint_cutsky_alm(
    pixel_map: object,
    *,
    mask: object,
    operator: JointCutSkyOperator,
    source_beam: object,
    source_pixel_window: object,
    target_beam: object,
    target_pixel_window: object,
) -> JointCutSkyFit:
    """Profile nuisance and retained harmonics in one weighted linear solve."""

    if not isinstance(operator, JointCutSkyOperator):
        raise PlanckLaneContractError("joint cut-sky operator type drifted")
    values = _finite_vector(pixel_map, label="temperature map")
    weights = _finite_vector(mask, label="analysis mask")
    if values.shape != weights.shape or values.shape != operator.mask.shape:
        raise PlanckLaneContractError("map and joint cut-sky mask pixelization differ")
    if (
        _sha256_array(weights, role="common_analysis_mask") != operator.mask_sha256
        or not np.array_equal(weights, operator.mask)
    ):
        raise PlanckLaneContractError("joint cut-sky mask differs from its operator")

    rhs = np.zeros(operator.dimension, dtype=float)
    weighted_square = 0.0
    chunk_size = min(values.size, 65_536)
    for start in range(0, values.size, chunk_size):
        stop = min(values.size, start + chunk_size)
        local_weights = weights[start:stop]
        support = local_weights > 0.0
        if not np.any(support):
            continue
        pixels = np.arange(start, stop, dtype=np.int64)[support]
        design = _real_harmonic_design_block(
            operator.nside,
            pixels,
            lmin=operator.lmin,
            lmax=operator.lmax,
        )
        selected_values = values[start:stop][support]
        selected_weights = local_weights[support]
        rhs += design.T @ (selected_weights * selected_values)
        weighted_square += float(
            np.dot(selected_weights, selected_values * selected_values)
        )
    pixel_area = 4.0 * math.pi / values.size
    rhs *= pixel_area
    weighted_square *= pixel_area
    try:
        coefficients = np.linalg.solve(operator.normal_matrix, rhs)
    except np.linalg.LinAlgError as exc:  # defensive: construction already gates rank
        raise PlanckLaneContractError("joint cut-sky solve became singular") from exc
    if not np.all(np.isfinite(coefficients)):
        raise PlanckLaneContractError("joint cut-sky coefficients became nonfinite")

    residual_square = float(
        weighted_square
        - 2.0 * coefficients @ rhs
        + coefficients @ operator.normal_matrix @ coefficients
    )
    roundoff_floor = 128.0 * np.finfo(float).eps * max(
        1.0, weighted_square, abs(float(coefficients @ rhs))
    )
    if residual_square < -roundoff_floor:
        raise PlanckLaneContractError("joint cut-sky residual norm became negative")
    weighted_residual_norm = math.sqrt(max(0.0, residual_square))

    full_alm = real_vector_to_alm(
        coefficients, lmin=operator.lmin, lmax=operator.lmax
    )
    commonized = commonize_beam_pixel_alm(
        full_alm,
        source_beam=source_beam,
        source_pixel_window=source_pixel_window,
        target_beam=target_beam,
        target_pixel_window=target_pixel_window,
        lmax=operator.lmax,
    )
    retained_coefficients = alm_to_real_vector(
        commonized,
        lmin=operator.retained_lmin,
        lmax=operator.lmax,
    )
    if retained_coefficients.size != operator.retained_dimension:
        raise PlanckLaneContractError("joint cut-sky retained dimension drifted")
    retained_alm = real_vector_to_alm(
        retained_coefficients,
        lmin=operator.retained_lmin,
        lmax=operator.lmax,
    )
    return JointCutSkyFit(
        retained_alm=retained_alm,
        retained_coefficients=retained_coefficients,
        all_coefficients=coefficients,
        weighted_residual_norm=weighted_residual_norm,
        operator_sha256=operator.operator_sha256,
    )


def build_mask_coupling_inverse(
    mask: object,
    *,
    lmin: int = LMIN,
    lmax: int = LMAX,
    relative_threshold: float = 1e-10,
    condition_ceiling: float = 1e8,
) -> MaskCouplingInverse:
    """Build and invert the exact discrete real-linear cut-sky operator."""

    hp = _healpy()
    weights = _finite_vector(mask, label="analysis mask")
    nside = hp.npix2nside(weights.size)
    if np.any(weights < 0.0) or np.any(weights > 1.0) or np.count_nonzero(weights) == 0:
        raise PlanckLaneContractError(
            "analysis mask weights must lie in [0,1] with support"
        )
    if not 0.0 < relative_threshold < 1.0 or condition_ceiling <= 1.0:
        raise PlanckLaneContractError("mask-inverse thresholds are invalid")
    dimension = len(real_alm_layout(lmin=lmin, lmax=lmax))
    coupling = np.zeros((dimension, dimension), dtype=float)
    chunk_size = min(weights.size, 65_536)
    for start in range(0, weights.size, chunk_size):
        stop = min(weights.size, start + chunk_size)
        pixels = np.arange(start, stop)
        weighted_design = _real_harmonic_design_block(
            nside,
            pixels,
            lmin=lmin,
            lmax=lmax,
        )
        weighted_design *= np.sqrt(weights[start:stop])[:, None]
        coupling += weighted_design.T @ weighted_design
    pixel_area = 4.0 * math.pi / weights.size
    coupling *= pixel_area
    singular_values = np.linalg.svd(coupling, compute_uv=False)
    largest = float(singular_values[0])
    smallest = float(singular_values[-1])
    if smallest <= relative_threshold * largest:
        raise PlanckLaneContractError(
            "mask coupling is rank deficient at the frozen threshold"
        )
    condition = largest / smallest
    if not math.isfinite(condition) or condition > condition_ceiling:
        raise PlanckLaneContractError(
            "mask coupling exceeds the frozen condition ceiling"
        )
    inverse = np.linalg.inv(coupling)
    return MaskCouplingInverse(
        matrix=coupling,
        inverse=inverse,
        singular_values=tuple(float(value) for value in singular_values),
        condition_number=condition,
        lmin=lmin,
        lmax=lmax,
        nside=nside,
        mask_sha256=_sha256_array(weights, role="common_analysis_mask"),
    )


def remove_weighted_monopole_dipole(pixel_map: object, mask: object) -> np.ndarray:
    hp = _healpy()
    values = _finite_vector(pixel_map, label="temperature map")
    weights = _finite_vector(mask, label="analysis mask")
    if values.shape != weights.shape:
        raise PlanckLaneContractError("map and mask pixelization differ")
    nside = hp.npix2nside(values.size)
    x, y, z = hp.pix2vec(nside, np.arange(values.size))
    design = np.column_stack((np.ones(values.size), x, y, z))
    support = weights > 0.0
    weighted_design = design[support] * np.sqrt(weights[support])[:, None]
    weighted_values = values[support] * np.sqrt(weights[support])
    coefficients, _, rank, _ = np.linalg.lstsq(
        weighted_design, weighted_values, rcond=None
    )
    if rank != 4:
        raise PlanckLaneContractError("mask cannot identify monopole and dipole")
    return values - design @ coefficients


def commonize_beam_pixel_alm(
    alm: object,
    *,
    source_beam: object,
    source_pixel_window: object,
    target_beam: object,
    target_pixel_window: object,
    lmax: int = LMAX,
    amplification_tolerance: float = 1e-10,
) -> np.ndarray:
    hp = _healpy()
    values = np.asarray(alm, dtype=np.complex128)
    if values.ndim != 1 or values.size != hp.Alm.getsize(lmax):
        raise PlanckLaneContractError("alm shape does not match commonization lmax")
    arrays = [
        _finite_vector(value, label=label)
        for value, label in (
            (source_beam, "source beam"),
            (source_pixel_window, "source pixel window"),
            (target_beam, "target beam"),
            (target_pixel_window, "target pixel window"),
        )
    ]
    if any(array.size < lmax + 1 for array in arrays):
        raise PlanckLaneContractError(
            "beam/pixel transfer does not cover the frozen band"
        )
    source = arrays[0][: lmax + 1] * arrays[1][: lmax + 1]
    target = arrays[2][: lmax + 1] * arrays[3][: lmax + 1]
    if np.any(source <= 0.0) or np.any(target <= 0.0):
        raise PlanckLaneContractError("beam/pixel transfers must be positive")
    ratio = target / source
    if np.any(ratio > 1.0 + amplification_tolerance):
        raise PlanckLaneContractError("common target would amplify a source transfer")
    return hp.almxfl(values, ratio, inplace=False)


def deconvolve_commonized_map(
    pixel_map: object,
    *,
    common_mask: object,
    source_beam: object,
    source_pixel_window: object,
    target_beam: object,
    target_pixel_window: object,
    mask_inverse: MaskCouplingInverse,
) -> np.ndarray:
    hp = _healpy()
    values = remove_weighted_monopole_dipole(pixel_map, common_mask)
    mask = _finite_vector(common_mask, label="analysis mask")
    if hp.npix2nside(values.size) != mask_inverse.nside:
        raise PlanckLaneContractError("map pixelization differs from the mask inverse")
    raw_alm = hp.map2alm(values, lmax=mask_inverse.lmax, iter=0, pol=False)
    common_alm = commonize_beam_pixel_alm(
        raw_alm,
        source_beam=source_beam,
        source_pixel_window=source_pixel_window,
        target_beam=target_beam,
        target_pixel_window=target_pixel_window,
        lmax=mask_inverse.lmax,
    )
    common_map = hp.alm2map(
        common_alm, nside=mask_inverse.nside, lmax=mask_inverse.lmax, pol=False
    )
    pseudo_alm = hp.map2alm(
        mask * common_map, lmax=mask_inverse.lmax, iter=0, pol=False
    )
    deconvolved = mask_inverse.inverse @ alm_to_real_vector(
        pseudo_alm, lmin=mask_inverse.lmin, lmax=mask_inverse.lmax
    )
    return real_vector_to_alm(
        deconvolved, lmin=mask_inverse.lmin, lmax=mask_inverse.lmax
    )


def _alm_by_lm(
    alm: np.ndarray, *, ell: int, lmax: int
) -> dict[tuple[int, int], complex]:
    dense = _dense_real_alm(alm, ell=ell, lmax=lmax)
    return {(ell, m): value for m, value in dense.items()}


def component_features_from_vectors(
    alm: object,
    *,
    vectors2: object,
    vectors3: object,
    lmax: int = LMAX,
) -> np.ndarray:
    """Extract frozen features using already-computed multipole vectors."""
    hp = _healpy()
    values = np.asarray(alm, dtype=np.complex128)
    if lmax < LMAX or values.ndim != 1 or values.size != hp.Alm.getsize(lmax):
        raise PlanckLaneContractError("feature alm does not cover ell=2..5")
    cl = hp.alm2cl(values, lmax=lmax)
    band = np.asarray(cl[LMIN : LMAX + 1], dtype=float)
    if not np.all(np.isfinite(band)) or np.any(band < 0.0):
        raise PlanckLaneContractError("low-ell power is not finite and nonnegative")
    odd = float(cl[3] + cl[5])
    even = float(cl[2] + cl[4])
    if odd <= 0.0:
        raise PlanckLaneContractError("odd-parity denominator is not positive")
    tensors = {
        ell: angular_momentum_power_tensor(
            alm_by_lm=_alm_by_lm(values, ell=ell, lmax=lmax), ell=ell
        )
        for ell in (2, 3)
    }
    gaps = []
    for ell in (2, 3):
        eigenvalues = np.linalg.eigvalsh(tensors[ell])
        gaps.append(float(eigenvalues[-1] - eigenvalues[-2]))
    vectors2 = np.asarray(vectors2, dtype=float)
    vectors3 = np.asarray(vectors3, dtype=float)
    if vectors2.shape != (2, 3) or vectors3.shape != (3, 3):
        raise PlanckLaneContractError("multipole-vector shapes drifted")
    dot2 = abs(float(vectors2[0] @ vectors2[1]))
    dots3 = sorted(
        abs(float(vectors3[first] @ vectors3[second]))
        for first, second in itertools.combinations(range(3), 2)
    )
    normal2 = np.cross(vectors2[0], vectors2[1])
    norm2 = float(np.linalg.norm(normal2))
    if norm2 <= 1e-12:
        raise PlanckLaneContractError(
            "ell=2 multipole plane is undefined for coincident axes"
        )
    normal2 /= norm2
    candidates: list[float] = []
    for first, second in itertools.combinations(range(3), 2):
        normal3 = np.cross(vectors3[first], vectors3[second])
        norm3 = float(np.linalg.norm(normal3))
        if norm3 > 1e-12:
            candidates.append(abs(float(normal2 @ (normal3 / norm3))))
    if not candidates:
        raise PlanckLaneContractError(
            "ell=3 multipole planes are undefined for coincident axes"
        )
    plane_alignment = max(candidates)
    output = np.array(
        [*band, even / odd, *gaps, dot2, *dots3, plane_alignment], dtype=float
    )
    if output.shape != (len(COMPONENT_FEATURE_IDS),) or not np.all(np.isfinite(output)):
        raise PlanckLaneContractError("component feature order or finiteness drifted")
    return output


def extract_component_features(alm: object, *, lmax: int = LMAX) -> np.ndarray:
    """Extract the frozen 12-element low-ell feature vector from one sky."""

    vectors2 = extract_multipole_vectors(alm, ell=2, lmax=lmax)
    vectors3 = extract_multipole_vectors(alm, ell=3, lmax=lmax)
    return component_features_from_vectors(
        alm, vectors2=vectors2, vectors3=vectors3, lmax=lmax
    )


def assemble_joint_feature_row(
    component_features: Mapping[str, object],
) -> np.ndarray:
    if (
        not isinstance(component_features, Mapping)
        or tuple(component_features) != REQUIRED_COMPONENTS
    ):
        raise PlanckLaneContractError(
            "joint row must be ordered exactly as SMICA then Commander"
        )
    rows = [
        _finite_vector(component_features[component], label=f"{component} features")
        for component in REQUIRED_COMPONENTS
    ]
    if any(row.size != len(COMPONENT_FEATURE_IDS) for row in rows):
        raise PlanckLaneContractError("component feature dimension drifted")
    return np.concatenate(rows)


def ordered_row_id_hash(row_ids: Sequence[str]) -> str:
    """Content-bind the exact ordered same-sky FFP10 realization IDs."""

    digest = hashlib.sha256()
    digest.update(b"htt.planck.ffp10.inventory.v1\0")
    for row_id in row_ids:
        if not isinstance(row_id, str) or not row_id.strip():
            raise PlanckLaneContractError(
                "FFP10 row IDs must be unique non-empty strings"
            )
        digest.update(row_id.encode("utf-8") + b"\0")
    return "sha256:" + digest.hexdigest()


@dataclass(frozen=True)
class FFP10Inventory:
    row_ids: tuple[str, ...]
    expected_identity: str
    expected_null_rows: int = EXPECTED_FFP10_NULL_ROWS

    def __post_init__(self) -> None:
        if type(self.expected_null_rows) is not int or self.expected_null_rows < 2:
            raise PlanckLaneContractError("expected FFP10 count is invalid")
        if (
            not self.row_ids
            or any(
                not isinstance(value, str) or not value.strip()
                for value in self.row_ids
            )
            or len(set(self.row_ids)) != len(self.row_ids)
        ):
            raise PlanckLaneContractError(
                "FFP10 row IDs must be unique non-empty strings"
            )
        if (
            not isinstance(self.expected_identity, str)
            or not self.expected_identity.startswith("sha256:")
            or len(self.expected_identity) != 71
        ):
            raise PlanckLaneContractError(
                "expected FFP10 ordered inventory identity is malformed"
            )
        try:
            int(self.expected_identity.removeprefix("sha256:"), 16)
        except ValueError as exc:
            raise PlanckLaneContractError(
                "expected FFP10 ordered inventory identity is malformed"
            ) from exc

    @property
    def complete(self) -> bool:
        return (
            len(self.row_ids) == self.expected_null_rows
            and self.identity == self.expected_identity
        )

    @property
    def identity(self) -> str:
        return ordered_row_id_hash(self.row_ids)

    def require_complete(self) -> None:
        if not self.complete:
            raise PlanckLaneContractError(
                "partial FFP10 or identity-mismatched inventory cannot calibrate a p-value"
            )


@dataclass(frozen=True)
class JointCovariance:
    matrix: np.ndarray
    row_ids: tuple[str, ...]
    feature_ids: tuple[str, ...]
    feature_units: tuple[str, ...]
    rank: int
    condition_number: float
    cross_block_norm: float


def estimate_matched_joint_covariance(
    *,
    smica_row_ids: Sequence[str],
    commander_row_ids: Sequence[str],
    smica_features: object,
    commander_features: object,
    condition_ceiling: float = 1e10,
) -> JointCovariance:
    identifiers = tuple(smica_row_ids)
    commander_identifiers = tuple(commander_row_ids)
    if (
        not identifiers
        or any(not isinstance(value, str) or not value.strip() for value in identifiers)
        or len(set(identifiers)) != len(identifiers)
    ):
        raise PlanckLaneContractError("paired FFP10 row IDs are invalid or duplicated")
    if commander_identifiers != identifiers:
        raise PlanckLaneContractError(
            "SMICA/Commander same-sky row IDs are not exactly paired"
        )
    smica = np.asarray(smica_features, dtype=float)
    commander = np.asarray(commander_features, dtype=float)
    expected_component_dimension = len(COMPONENT_FEATURE_IDS)
    if (
        smica.ndim != 2
        or commander.ndim != 2
        or smica.shape != commander.shape
        or smica.shape != (len(identifiers), expected_component_dimension)
        or not np.all(np.isfinite(smica))
        or not np.all(np.isfinite(commander))
    ):
        raise PlanckLaneContractError("matched same-sky feature rows are incomplete")
    joint = np.concatenate((smica, commander), axis=1)
    if joint.shape[0] <= joint.shape[1]:
        raise PlanckLaneContractError(
            "joint covariance requires more skies than features"
        )
    covariance = np.cov(joint, rowvar=False, ddof=1)
    validation = validate_full_joint_covariance(covariance, JOINT_FEATURE_IDS)
    cross = covariance[:expected_component_dimension, expected_component_dimension:]
    cross_norm = float(np.linalg.norm(cross, ord="fro"))
    if not math.isfinite(cross_norm) or cross_norm <= 1e-14 * float(
        np.linalg.norm(covariance, ord="fro")
    ):
        raise PlanckLaneContractError(
            "same-sky covariance lost the SMICA/Commander cross block"
        )
    condition = float(validation["condition_number"])
    if condition > condition_ceiling:
        raise PlanckLaneContractError("joint covariance exceeds the condition ceiling")
    return JointCovariance(
        matrix=covariance,
        row_ids=identifiers,
        feature_ids=JOINT_FEATURE_IDS,
        feature_units=JOINT_FEATURE_UNITS,
        rank=int(validation["rank"]),
        condition_number=condition,
        cross_block_norm=cross_norm,
    )


@dataclass(frozen=True)
class ResponseRank:
    rank: int
    dimension: int
    singular_values: tuple[float, ...]
    absolute_threshold: float
    relative_threshold: float
    status: str
    global_response_status: str = "MISSING"
    global_claim_boundary: str = GLOBAL_CLAIM_BOUNDARY


def covariance_whitened_response_rank(
    covariance: object,
    local_response: object,
    *,
    relative_threshold: float = 1e-8,
    absolute_threshold: float = 1e-10,
) -> ResponseRank:
    matrix = np.asarray(covariance, dtype=float)
    response = np.asarray(local_response, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise PlanckLaneContractError("response covariance must be square")
    if response.ndim == 1:
        response = response[:, None]
    if (
        response.ndim != 2
        or response.shape[0] != matrix.shape[0]
        or not np.all(np.isfinite(response))
    ):
        raise PlanckLaneContractError("local response shape does not match covariance")
    if not 0.0 < relative_threshold < 1.0 or absolute_threshold <= 0.0:
        raise PlanckLaneContractError("response-rank thresholds are invalid")
    try:
        cholesky = np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError as exc:
        raise PlanckLaneContractError(
            "response covariance is not positive definite"
        ) from exc
    whitened = np.linalg.solve(cholesky, response)
    singular_values = np.linalg.svd(whitened, compute_uv=False)
    largest = float(singular_values[0]) if singular_values.size else 0.0
    threshold = max(absolute_threshold, relative_threshold * largest)
    rank = int(np.count_nonzero(singular_values > threshold))
    return ResponseRank(
        rank=rank,
        dimension=response.shape[1],
        singular_values=tuple(float(value) for value in singular_values),
        absolute_threshold=absolute_threshold,
        relative_threshold=relative_threshold,
        status="LOCAL_RESPONSE_RANK_COMPUTED",
    )


def calibrate_complete_synthetic_pool(
    *,
    observation_features: object,
    null_features: object,
    inventory: FFP10Inventory,
) -> ObservationInclusiveMaxScan:
    """Calibrate only a fully enumerated synthetic observation/null pool."""

    inventory.require_complete()
    observation = _finite_vector(
        observation_features, label="synthetic observation features"
    )
    nulls = np.asarray(null_features, dtype=float)
    if (
        nulls.ndim != 2
        or nulls.shape != (len(inventory.row_ids), observation.size)
        or not np.all(np.isfinite(nulls))
    ):
        raise PlanckLaneContractError(
            "complete FFP10 feature matrix is missing or malformed"
        )
    pool = np.vstack((observation, nulls))
    return observation_inclusive_max_scan(
        pool, ("two-sided",) * observation.size, observation_index=0
    )


SOURCE_IDENTITY_FIELDS = frozenset(
    {
        "map_product_id",
        "source_beam_id",
        "source_pixel_window_id",
        "source_mask_id",
        "source_covariance_id",
    }
)
SHARED_OPERATOR_FIELDS = frozenset(
    {
        "pipeline_id",
        "target_beam_id",
        "target_pixel_window_id",
        "common_analysis_mask_id",
        "mask_coupling_inverse_id",
        "harmonic_convention_id",
        "feature_order_id",
        "null_ensemble_id",
        "local_response_id",
        "units_id",
    }
)


def validate_component_operator_identities(
    observation: Mapping[str, Mapping[str, object]],
    null: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    """Preserve component inputs while requiring one derived operator."""

    if tuple(observation) != REQUIRED_COMPONENTS or tuple(null) != REQUIRED_COMPONENTS:
        raise PlanckLaneContractError(
            "operator components must be ordered SMICA, Commander"
        )
    validated: dict[str, dict[str, object]] = {}
    required_fields = SOURCE_IDENTITY_FIELDS | SHARED_OPERATOR_FIELDS
    for component in REQUIRED_COMPONENTS:
        left = observation[component]
        right = null[component]
        if set(left) != required_fields or set(right) != required_fields:
            raise PlanckLaneContractError("component operator identity fields drifted")
        if any(
            not isinstance(left[field], str) or not str(left[field]).strip()
            for field in required_fields
        ):
            raise PlanckLaneContractError(
                "operator identity values must be non-empty strings"
            )
        if dict(left) != dict(right):
            raise PlanckLaneContractError(
                "observation/null component operator identity differs"
            )
        validated[component] = dict(left)
    for field in SHARED_OPERATOR_FIELDS:
        if validated["SMICA"][field] != validated["Commander"][field]:
            raise PlanckLaneContractError(
                "derived SMICA/Commander operator identity differs"
            )
    for field in SOURCE_IDENTITY_FIELDS:
        if validated["SMICA"][field] == validated["Commander"][field]:
            raise PlanckLaneContractError(
                "component-specific SMICA/Commander source identity was collapsed"
            )
    return validated


def capability_snapshot(*, response_rank: ResponseRank | None) -> dict[str, object]:
    return {
        "schema": SCHEMA_VERSION,
        "beam_pixel_normalization": "IMPLEMENTED_NONAMPLIFYING_COMMON_TARGET",
        "mask_deconvolution": "IMPLEMENTED_FULL_RANK_REAL_LINEAR_INVERSE",
        "multipole_vectors": "IMPLEMENTED_MAJORANA_PROJECTIVE_ROOTS",
        "feature_order": list(JOINT_FEATURE_IDS),
        "feature_units": list(JOINT_FEATURE_UNITS),
        "joint_covariance": "IMPLEMENTED_MATCHED_SAME_SKY_FULL_CROSS_BLOCK",
        "ffp10_inventory": "COMPLETE_INVENTORY_REQUIRED_FOR_CALIBRATION",
        "synthetic_local_response_rank": (
            "NOT_COMPUTED" if response_rank is None else response_rank.status
        ),
        "synthetic_local_response_rank_value": (
            None if response_rank is None else response_rank.rank
        ),
        "global_response_status": "MISSING",
        "local_global_discrimination": GLOBAL_CLAIM_BOUNDARY,
        "Q": "BLOCKED_NO_DEPARTURE_BUNDLE_BUDGET",
        "F": "BLOCKED_NO_SIGN_CLEAN_XC_AND_CEILING",
        "Pi": "BLOCKED_NO_Q_OR_F_MEASURE",
        "G_F": "NOT_APPLICABLE_NO_DEPTH_AXIS",
        "likelihood_prior_posterior_evidence": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
        "observed_data": "NOT_EXECUTED",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }


__all__ = [
    "COMPONENT_FEATURE_IDS",
    "COMPONENT_FEATURE_UNITS",
    "EXPECTED_FFP10_NULL_ROWS",
    "FFP10Inventory",
    "GLOBAL_CLAIM_BOUNDARY",
    "JOINT_FEATURE_IDS",
    "JOINT_FEATURE_UNITS",
    "JOINT_CUTSKY_ESTIMATOR_ID",
    "JOINT_CUTSKY_RETAINED_DIMENSION",
    "JOINT_CUTSKY_TOTAL_DIMENSION",
    "JointCutSkyFit",
    "JointCutSkyOperator",
    "JointCovariance",
    "LMAX",
    "LMIN",
    "MULTIPOLE_VECTOR_CONVENTION",
    "MaskCouplingInverse",
    "REQUIRED_COMPONENTS",
    "ResponseRank",
    "SCHEMA_VERSION",
    "alm_to_real_vector",
    "assemble_joint_feature_row",
    "build_joint_cutsky_operator",
    "build_mask_coupling_inverse",
    "calibrate_complete_synthetic_pool",
    "capability_snapshot",
    "commonize_beam_pixel_alm",
    "component_features_from_vectors",
    "covariance_whitened_response_rank",
    "deconvolve_commonized_map",
    "estimate_matched_joint_covariance",
    "extract_component_features",
    "extract_multipole_vectors",
    "fit_joint_cutsky_alm",
    "ordered_row_id_hash",
    "real_alm_layout",
    "real_vector_to_alm",
    "remove_weighted_monopole_dipole",
    "validate_component_operator_identities",
]
