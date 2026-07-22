"""EGS3 Axis E: identified-set reporting for the signed comparator x_C (P26/P31/P35, A8).

Operational resolution of the P1 x P18 tension: the comparator x_C = c^T g,
c = (+1, -1, +1, +1), needs all four components of g = (Sigma^2, W^2, Omega_tilt,
Omega_k_aniso), but the registered scalar/radial response reaches only a rank-2
subspace (W^2 and Omega_k are exact structural nulls of the channel design). The
reportable object is therefore NOT a point value but the identified set

    G(y) = { g : ||y - R g||^2 <= tau,  lower <= g <= upper }

and its image under c^T, the closed interval [x_C^-, x_C^+].

Two-stage tau semantics (P35). A single tau conflates two different degrees of
freedom. Stage 1 uses the m - r residual directions (orthogonal to col(R)) as a
SPECIFICATION TEST at level alpha1: if the residual statistic exceeds the stage-1
threshold the feasible set is EMPTY and the correct report is a misfit/refutation
status, not an interval. Stage 2 places a conditional ellipsoid on the r reachable
directions. The default threshold policy is the original known-covariance chi-square
branch; an explicit estimated-covariance Hotelling/F branch is available when the
covariance is simulation-estimated. alpha2 = 1.0 gives tau2 = 0, i.e. the POPULATION
identified set (no sampling inflation).

Status semantics (A8), in precedence order:
  ``empty``         -- stage-1 misfit, or the stage-2 ellipsoid misses the cone
                       (refutability: the model class is rejected, by design);
  ``unbounded``     -- a null direction with c_j != 0 carries no MES ceiling, so an
                       endpoint is infinite and the honest report is no-result;
  ``ceiling_unfit`` -- max(0, x_C^+)/U_C > 1: the certified-filling ceiling U_C is
                       inconsistent with the feasible set (F > 1 clip);
  ``feasible``      -- a finite sharp interval [x_lo, x_hi] is reported.

Endpoint uncertainty (P35 / Imbens-Manski). The interval endpoints are extrema of a
random set; a CI for the PARAMETER x_C needs the Imbens-Manski critical value C_N
solving Phi(C_N + Delta_hat / max(se)) - Phi(-C_N) = 1 - alpha (Imbens & Manski
2004; Stoye 2009 -- external-context citations). The naive per-endpoint one-sided
z_{1-alpha} construction UNDERCOVERS as the interval width Delta -> 0; the
set-coverage projection construction (z_{1-alpha/2}) is conservative for the
parameter. Both are implemented as explicit foils.

Domain restriction (honest): this module requires the null space of R to be spanned
by ZERO COLUMNS (axis-aligned nulls). The registered box-active problem has exactly
two reachable columns and is solved analytically. Higher-dimensional ellipsoids are
reported only when both objective support points are box-inactive; a box-active
higher-dimensional endpoint raises NotImplementedError rather than relying on an
uncertified generic optimiser. The registered channel design of
`egs3_graded_comparator.channel_response_design` has identically zero W^2 and
Omega_k columns and exactly two reachable columns.

Domain discipline. Component bounds are signed boxes. Nonnegativity is a branch
choice, not a global theorem: the registered open-curvature branch uses
Omega_k_aniso in [0, U_k], while the all-curvature branch uses [-U_k, U_k].

Claim discipline. Diagnostic-only, synthetic-witness statistics machinery. It is a
SEPARATE DIAGNOSTIC SURFACE: it never touches the bit-identical comparator x_C,
the response design, or the frozen registered low-ell statistic set, and it adds no
new registered statistic. No detection, family/geometry, native-solver, or posterior
claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy import optimize, stats

STATUS_FEASIBLE = "feasible"
STATUS_EMPTY = "empty"
STATUS_UNBOUNDED = "unbounded"
STATUS_CEILING_UNFIT = "ceiling_unfit"


class EndpointOptimizationError(RuntimeError):
    """Raised when a numerical endpoint candidate cannot be validated."""


__all__ = [
    "STATUS_FEASIBLE", "STATUS_EMPTY", "STATUS_UNBOUNDED", "STATUS_CEILING_UNFIT",
    "EndpointOptimizationError",
    "TwoStageTau", "two_stage_tau",
    "IdentifiedSetReport", "identified_set_report",
    "curvature_branch_bounds", "signed_curvature_branch_reports",
    "reachable_endpoints_closed_form",
    "im_critical_value", "im_interval", "projection_interval", "endpoint_interval",
    "ImCoverageResult", "im_coverage_experiment",
    "RefutabilityPower", "refutability_power_experiment",
    "toy_design",
]


@dataclass(frozen=True)
class TwoStageTau:
    """The two thresholds of the P35 construction.

    ``known_chi2`` preserves the original API and values. ``estimated_covariance_f``
    applies the finite-simulation Hotelling/F correction separately to each stage.
    """
    m: int
    r: int
    alpha1: float
    alpha2: float
    tau1: float
    tau2: float
    threshold_policy: str = "known_chi2"
    n_sim: int | None = None
    threshold_value: float = math.nan
    df_residual: int = 0
    df_reachable: int = 0


def two_stage_tau(m: int, r: int, *, alpha1: float = 0.05,
                  alpha2: float = 0.05,
                  threshold_policy: str = "known_chi2",
                  n_sim: int | None = None) -> TwoStageTau:
    """tau1 = chi^2_{m-r, 1-alpha1} (stage-1 specification test on the residual
    directions) and tau2 = chi^2_{r, 1-alpha2} (stage-2 conditional reachable
    ellipsoid). alpha2 = 1.0 -> tau2 = 0 -> population identified set.

    With ``threshold_policy="estimated_covariance_f"``, use
    df * (n_sim - 1) / (n_sim - df) * F_{df, n_sim-df, 1-alpha}, which is the
    fail-closed finite-simulation branch requested by the v7 audit.
    """
    m = int(m)
    r = int(r)
    if not (0 < r < m):
        raise ValueError("need 0 < r < m for the two-stage split")
    if not (0.0 < alpha1 < 1.0) or not (0.0 < alpha2 <= 1.0):
        raise ValueError("alpha1 in (0,1); alpha2 in (0,1]")
    policy = str(threshold_policy)
    df_residual = m - r
    df_reachable = r

    def _estimated_cov_threshold(df: int, alpha: float) -> float:
        if n_sim is None:
            raise ValueError("n_sim is required for estimated_covariance_f")
        n = int(n_sim)
        if n <= df + 1:
            raise ValueError("estimated_covariance_f requires n_sim > df + 1")
        return float(df * (n - 1) / (n - df) * stats.f.ppf(1.0 - alpha, df, n - df))

    if policy == "known_chi2":
        if n_sim is not None:
            raise ValueError("n_sim is only meaningful for estimated_covariance_f")
        tau1 = float(stats.chi2.ppf(1.0 - alpha1, df_residual))
        tau2 = 0.0 if alpha2 == 1.0 else float(stats.chi2.ppf(1.0 - alpha2, df_reachable))
    elif policy == "estimated_covariance_f":
        tau1 = _estimated_cov_threshold(df_residual, alpha1)
        tau2 = 0.0 if alpha2 == 1.0 else _estimated_cov_threshold(df_reachable, alpha2)
    else:
        raise ValueError("threshold_policy must be known_chi2 or estimated_covariance_f")
    return TwoStageTau(m=m, r=r, alpha1=float(alpha1), alpha2=float(alpha2),
                       tau1=tau1, tau2=tau2, threshold_policy=policy,
                       n_sim=None if n_sim is None else int(n_sim),
                       threshold_value=tau1, df_residual=df_residual,
                       df_reachable=df_reachable)


@dataclass(frozen=True)
class IdentifiedSetReport:
    """A8 report: status + interval + provenance of both stages."""
    status: str
    x_lo: float
    x_hi: float
    reachable_lo: float
    reachable_hi: float
    null_lo: float
    null_hi: float
    spec_stat: float
    spec_threshold: float
    spec_pass: bool
    rank: int
    m: int
    F_lo: float | None
    F_hi: float | None
    tau: TwoStageTau
    branch_id: str = "unspecified"
    component_bounds: tuple = ()
    input_modes: tuple = ()
    observational_claim_allowed: bool = False
    threshold_policy: str = "known_chi2"
    n_sim: int | None = None
    df_residual: int = 0
    df_reachable: int = 0


def _split_columns(R: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Active (nonzero) vs null (identically zero) column indices."""
    active_mask = np.any(R != 0.0, axis=0)
    active = np.flatnonzero(active_mask)
    null = np.flatnonzero(~active_mask)
    return active, null


def reachable_endpoints_closed_form(A: np.ndarray, y: np.ndarray, c_R: np.ndarray,
                                    tau2: float) -> tuple[float, float]:
    """Cone-free (box-ignored) endpoints of c_R^T g over the reachable ellipsoid
    {g : ||A g - y||^2 <= s1 + tau2}: c_R^T g_hat -/+ sqrt(tau2 c_R^T (A^T A)^{-1} c_R).

    Independent cross-check route for the constrained endpoint implementation;
    coincides with it whenever the box constraints are inactive."""
    A = np.asarray(A, dtype=float)
    y = np.asarray(y, dtype=float)
    c_R = np.asarray(c_R, dtype=float)
    gram_inv = np.linalg.inv(A.T @ A)
    g_hat = gram_inv @ (A.T @ y)
    centre = float(c_R @ g_hat)
    half = math.sqrt(max(float(tau2), 0.0) * float(c_R @ gram_inv @ c_R))
    return centre - half, centre + half


def _active_column_scales(A: np.ndarray) -> np.ndarray:
    """Finite, units-equivariant scales for structurally nonzero columns."""
    scale = np.max(np.abs(A), axis=0)
    if (not np.all(np.isfinite(scale)) or np.any(scale <= 0.0)):
        raise ValueError("active response columns must have finite positive scale")
    return scale


def _bound_status(candidate: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> str:
    """Classify canonical coordinates as inside, outside, or ambiguous.

    Callers must supply column-normalised coordinates ``z = scale * g`` or
    displacements between such coordinates.  The unit floor is therefore
    invariant under positive column reparameterisations; applying it directly
    to physical ``g`` coordinates would introduce a units-dependent acceptance
    band.  A representable value just beyond a bound is not silently admitted:
    machine-scale violations are numerical no-results, while larger violations
    are genuinely outside.
    """
    magnitude = np.maximum(1.0, np.abs(candidate))
    magnitude = np.maximum(
        magnitude, np.where(np.isfinite(lo), np.abs(lo), 0.0))
    magnitude = np.maximum(
        magnitude, np.where(np.isfinite(hi), np.abs(hi), 0.0))
    bound_tol = 64.0 * np.finfo(float).eps * magnitude
    lower_violation = np.isfinite(lo) & (candidate < lo)
    upper_violation = np.isfinite(hi) & (candidate > hi)
    if not (np.any(lower_violation) or np.any(upper_violation)):
        return "inside"
    if (np.any(lower_violation & (candidate < lo - bound_tol))
            or np.any(upper_violation & (candidate > hi + bound_tol))):
        return "outside"
    return "ambiguous"


def _within_bounds(candidate: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> bool:
    """Return whether a canonical candidate is certifiably inside its box."""
    return _bound_status(candidate, lo, hi) == "inside"


def _scaled_active_bounds(lo: np.ndarray, hi: np.ndarray,
                          scale: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return canonical active-coordinate bounds without hiding overflow."""
    with np.errstate(over="ignore", invalid="ignore"):
        lo_scaled = lo * scale
        hi_scaled = hi * scale
    if (np.any(np.isfinite(lo) & ~np.isfinite(lo_scaled))
            or np.any(np.isfinite(hi) & ~np.isfinite(hi_scaled))):
        raise EndpointOptimizationError(
            "active component bounds overflow after column normalisation")
    return lo_scaled, hi_scaled


def _least_squares_centre(
        A: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return an absolute anchor, local correction, and centred residual.

    The correction is retained separately instead of being added back to a
    large anchor.  This one-step iterative refinement preserves small endpoint
    geometry when the parameter origin is translated by many orders of
    magnitude.
    """
    try:
        anchor, *_ = np.linalg.lstsq(A, y, rcond=None)
        anchor_residual = A @ anchor - y
        correction, *_ = np.linalg.lstsq(A, -anchor_residual, rcond=None)
    except np.linalg.LinAlgError as exc:
        raise EndpointOptimizationError("least-squares centre solve failed") from exc
    centre_residual = anchor_residual + A @ correction
    if (anchor.shape != (A.shape[1],)
            or correction.shape != anchor.shape
            or not np.all(np.isfinite(anchor))
            or not np.all(np.isfinite(correction))
            or not np.all(np.isfinite(centre_residual))):
        raise EndpointOptimizationError("least-squares centre is non-finite")
    return anchor, correction, centre_residual


def _bounds_relative_to_centre(
        lo: np.ndarray, hi: np.ndarray, scale: np.ndarray,
        anchor: np.ndarray, correction: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Express physical bounds around a split canonical centre.

    Subtract in physical coordinates before scaling the small displacement.
    Forming ``lo * scale - anchor`` first would discard local box geometry when
    both the coordinate origin and a column reparameterisation are extreme.
    """
    with np.errstate(over="ignore", invalid="ignore"):
        physical_anchor = anchor / scale
        anchor_roundtrip = physical_anchor * scale
        anchor_gap = anchor - anchor_roundtrip
        lo_delta = (
            (lo - physical_anchor) * scale - anchor_gap - correction)
        hi_delta = (
            (hi - physical_anchor) * scale - anchor_gap - correction)
    if (np.any(np.isfinite(lo) & ~np.isfinite(lo_delta))
            or np.any(np.isfinite(hi) & ~np.isfinite(hi_delta))):
        raise EndpointOptimizationError(
            "active component bounds overflow relative to the fitted centre")
    return lo_delta, hi_delta


def _residual_roundoff_tolerance(A: np.ndarray, y: np.ndarray,
                                 g: np.ndarray, *squared_scales: float) -> float:
    """Roundoff allowance in squared-residual units.

    The allowance follows the arithmetic scale of ``A @ g - y`` and never uses
    the public rank tolerance as a dimensionally mismatched residual floor.
    """
    arithmetic_scale = float(np.linalg.norm(np.abs(A) @ np.abs(g) + np.abs(y)))
    if not math.isfinite(arithmetic_scale):
        raise EndpointOptimizationError("residual validation overflowed")
    squared_values = [abs(float(value)) for value in squared_scales]
    if not all(math.isfinite(value) for value in squared_values):
        raise EndpointOptimizationError("residual validation received non-finite input")
    squared_scale = max(squared_values, default=0.0)
    roundoff_norm = 64.0 * np.finfo(float).eps * arithmetic_scale
    return (
        2.0 * math.sqrt(squared_scale) * roundoff_norm
        + roundoff_norm ** 2
        + 64.0 * np.finfo(float).eps
        * max(squared_scale, np.finfo(float).tiny)
    )


def _scalar_comparison_tolerance(
        left: float, right: float, *arithmetic_scales: float) -> float:
    """Return a relative binary64 ambiguity band for a scalar threshold.

    Endpoint values are continuous-real targets rounded through several
    binary64 operations.  A discontinuous public status must not be selected
    when its threshold lies inside that admitted arithmetic band.  No unit
    floor is used: rescaling the comparator and ceiling together rescales the
    band with them.
    """
    scales = [abs(float(left)), abs(float(right)), np.finfo(float).tiny]
    scales.extend(abs(float(value)) for value in arithmetic_scales)
    if not all(math.isfinite(value) for value in scales):
        raise EndpointOptimizationError(
            "scalar comparison received a non-finite arithmetic scale")
    scale = max(scales)
    return 64.0 * np.finfo(float).eps * scale


def _rank2_box_least_squares(
        A: np.ndarray, centre_residual: np.ndarray, lo_delta: np.ndarray,
        hi_delta: np.ndarray) -> tuple[np.ndarray, float]:
    """Analytic candidate for a centred rank-two box least-squares problem.

    A convex quadratic over a box is minimised either at its unconstrained
    centre or on a box face.  Fixing either coordinate reduces each finite face
    to a scalar quadratic; clipping its stationary point also covers corners.
    This registered-domain feasibility certificate is independent of SciPy's
    bounded least-squares stopping rules.
    """
    if (A.ndim != 2 or A.shape[1] != 2
            or centre_residual.shape != (A.shape[0],)
            or lo_delta.shape != (2,) or hi_delta.shape != (2,)):
        raise EndpointOptimizationError(
            "rank-2 feasibility certificate received invalid shapes")

    candidates: list[np.ndarray] = []
    if not np.all(np.isfinite(centre_residual)):
        raise EndpointOptimizationError(
            "rank-2 feasibility centre residual is non-finite")
    zero = np.zeros(2, dtype=float)
    if _within_bounds(zero, lo_delta, hi_delta):
        candidates.append(zero)

    for fixed_index in (0, 1):
        free_index = 1 - fixed_index
        free_column = A[:, free_index]
        quadratic = float(free_column @ free_column)
        if not math.isfinite(quadratic) or quadratic <= 0.0:
            raise EndpointOptimizationError(
                "rank-2 feasibility certificate has a degenerate face")
        for fixed_delta in (
                lo_delta[fixed_index], hi_delta[fixed_index]):
            if not math.isfinite(float(fixed_delta)):
                continue
            offset = centre_residual + A[:, fixed_index] * fixed_delta
            free_delta = -float(free_column @ offset) / quadratic
            free_delta = float(np.clip(
                free_delta, lo_delta[free_index], hi_delta[free_index]))
            candidate_delta = np.empty(2, dtype=float)
            candidate_delta[fixed_index] = fixed_delta
            candidate_delta[free_index] = free_delta
            if np.all(np.isfinite(candidate_delta)) and _within_bounds(
                    candidate_delta, lo_delta, hi_delta):
                candidates.append(candidate_delta)

    if not candidates:
        raise EndpointOptimizationError(
            "rank-2 box feasibility certificate found no finite candidate")

    def residual_squared(candidate_delta: np.ndarray) -> float:
        residual = centre_residual + A @ candidate_delta
        value = float(residual @ residual)
        if not math.isfinite(value):
            raise EndpointOptimizationError(
                "rank-2 feasibility residual is non-finite")
        return value

    best_delta = min(candidates, key=residual_squared)
    return best_delta, residual_squared(best_delta)


def _constrained_extreme(A: np.ndarray, y: np.ndarray, c_R: np.ndarray,
                         level: float, lo: np.ndarray, hi: np.ndarray,
                         feasible_delta: np.ndarray,
                         sense: float) -> tuple[float, float]:
    """Validated min/max candidate over an ellipsoid-box intersection.

    The box-inactive support point is solved analytically in any dimension.  A
    box-active registered rank-2 endpoint is obtained by deterministic face
    enumeration.  Higher-dimensional box-active endpoints are deliberately
    unsupported until an independent sharpness certificate exists.

    ``feasible_delta`` is expressed in canonical coordinates relative to the
    split, locally refined least-squares centre.  Candidates remain in this
    frame for bound and residual certification; only the final continuous-real
    endpoint is rounded to a scalar float.  The second returned value is the
    sum of the absolute objective terms used for that rounding; downstream
    discontinuous threshold decisions use it as their arithmetic scale.
    """
    endpoint = "lower" if sense > 0.0 else "upper"
    scale = _active_column_scales(A)
    if scale.shape != c_R.shape:
        raise EndpointOptimizationError(
            f"{endpoint} endpoint has invalid active-column scaling")

    # z = scale * g makes every active response column unit norm.  Under a
    # physical reparameterisation A_j -> s A_j, g_j -> g_j/s, c_j -> s c_j,
    # this optimisation problem is invariant.
    A_scaled = A / scale
    c_scaled = c_R / scale
    feasible_delta = np.asarray(feasible_delta, dtype=float)
    _scaled_active_bounds(lo, hi, scale)
    z_anchor, centre_correction, centre_resid = _least_squares_centre(
        A_scaled, y)
    centre_resid_sq = float(centre_resid @ centre_resid)
    if not math.isfinite(centre_resid_sq):
        raise EndpointOptimizationError(
            f"{endpoint} endpoint centre is non-finite")
    lo_delta, hi_delta = _bounds_relative_to_centre(
        lo, hi, scale, z_anchor, centre_correction)
    centre_objective_terms = tuple(
        float(coefficient) * float(coordinate)
        for coefficient, coordinate in zip(c_scaled, z_anchor)
    ) + tuple(
        float(coefficient) * float(displacement)
        for coefficient, displacement in zip(c_scaled, centre_correction)
    )
    centre_value = float(math.fsum(centre_objective_terms))
    if not math.isfinite(centre_value):
        raise EndpointOptimizationError(
            f"{endpoint} endpoint centre objective is non-finite")

    def delta_value(delta: np.ndarray) -> float:
        return float(math.fsum(
            float(coefficient) * float(coordinate)
            for coefficient, coordinate in zip(c_scaled, delta)
        ))

    def endpoint_value(delta: np.ndarray) -> tuple[float, float]:
        delta_terms = tuple(
            float(coefficient) * float(coordinate)
            for coefficient, coordinate in zip(c_scaled, delta)
        )
        objective_terms = centre_objective_terms + delta_terms
        value = float(math.fsum(objective_terms))
        arithmetic_scale = float(math.fsum(
            abs(term) for term in objective_terms))
        return value, arithmetic_scale

    def objective(delta: np.ndarray) -> float:
        return sense * delta_value(delta)

    def centered_residual_certificate(
            delta: np.ndarray) -> tuple[float, float]:
        """Return squared residual and roundoff allowance about the centre."""
        delta = np.asarray(delta, dtype=float)
        residual = centre_resid + A_scaled @ delta
        residual_squared = float(residual @ residual)
        tolerance = _residual_roundoff_tolerance(
            A_scaled, centre_resid, delta, level, residual_squared)
        return residual_squared, tolerance

    def certify(delta: np.ndarray) -> tuple[float, float]:
        delta = np.asarray(delta, dtype=float)
        if delta.shape != c_R.shape or not np.all(np.isfinite(delta)):
            raise EndpointOptimizationError(
                f"{endpoint} endpoint computation returned a non-finite candidate")

        if not _within_bounds(delta, lo_delta, hi_delta):
            raise EndpointOptimizationError(
                f"{endpoint} endpoint candidate violates the parameter bounds")

        # Evaluate around the least-squares centre.  This is algebraically the
        # same residual, but it avoids subtracting two large absolute-coordinate
        # predictions after a harmless translation of the parameter origin.
        resid_sq, feasibility_tol = centered_residual_certificate(delta)
        if (not math.isfinite(resid_sq)
                or resid_sq > float(level) + feasibility_tol):
            raise EndpointOptimizationError(
                f"{endpoint} endpoint candidate violates the residual constraint: "
                f"residual_squared={resid_sq!r}, level={float(level)!r}, "
                f"tolerance={feasibility_tol!r}")

        value, arithmetic_scale = endpoint_value(delta)
        if not math.isfinite(value) or not math.isfinite(arithmetic_scale):
            raise EndpointOptimizationError(
                f"{endpoint} endpoint objective is non-finite")
        return value, arithmetic_scale

    if np.all(c_scaled == 0.0):
        if not _within_bounds(feasible_delta, lo_delta, hi_delta):
            if c_R.size != 2:
                raise NotImplementedError(
                    "box-active endpoint sharpness is implemented only for rank two")
            raise EndpointOptimizationError(
                f"{endpoint} endpoint received an infeasible rank-2 witness")
        return certify(feasible_delta)

    # When the unconstrained ellipsoid support point lies inside the box it is
    # already the sharp constrained endpoint.  This exact r-dimensional route
    # keeps the exact box-inactive result on a closed-form path.
    try:
        radius_sq = float(level) - centre_resid_sq
        _, centre_tol = centered_residual_certificate(
            np.zeros_like(z_anchor))
        _, singular_values, right_vectors = np.linalg.svd(
            A_scaled, full_matrices=False)
        if np.any(singular_values <= 0.0):
            raise np.linalg.LinAlgError("singular active response")
        direction = right_vectors.T @ (
            (right_vectors @ c_scaled) / singular_values ** 2)
        support_sq = float(c_scaled @ direction)
        if radius_sq >= -centre_tol and support_sq > 0.0:
            distance = math.sqrt(max(radius_sq, 0.0) / support_sq)
            analytic_delta = -sense * distance * direction
            if _within_bounds(analytic_delta, lo_delta, hi_delta):
                return certify(analytic_delta)
    except np.linalg.LinAlgError:
        # The public rank check already excludes singular active designs.  If a
        # borderline numerical solve still fails, the certified fallback below
        # either succeeds or surfaces an explicit numerical no-result.
        pass

    if c_R.size == 2:
        # The registered EGS3 reachable block has rank two.  If its unconstrained
        # support point is outside the box, a sharp linear endpoint must lie on
        # one of the four box faces.  On each face the residual constraint is a
        # scalar quadratic, so enumerate its clipped feasible interval exactly.
        candidates: list[np.ndarray] = []
        for fixed_index in (0, 1):
            free_index = 1 - fixed_index
            for fixed_delta in (
                    lo_delta[fixed_index], hi_delta[fixed_index]):
                if not math.isfinite(float(fixed_delta)):
                    continue
                offset = (
                    centre_resid
                    + A_scaled[:, fixed_index] * fixed_delta
                )
                free_column = A_scaled[:, free_index]
                quadratic = float(free_column @ free_column)
                linear = float(free_column @ offset)
                if not math.isfinite(quadratic) or quadratic <= 0.0:
                    raise EndpointOptimizationError(
                        f"{endpoint} rank-2 face is degenerate")

                # Complete the scalar square by evaluating the residual at
                # its face minimum.  Forming linear**2 - q*constant in
                # absolute coordinates loses the entire discriminant after a
                # large but scientifically irrelevant coordinate translation.
                free_delta_centre = -linear / quadratic
                face_min_resid = offset + free_column * free_delta_centre
                face_min_resid_sq = float(face_min_resid @ face_min_resid)
                face_margin = float(level) - face_min_resid_sq
                face_margin_tol = _residual_roundoff_tolerance(
                    A_scaled, face_min_resid, np.zeros(2, dtype=float),
                    level, face_min_resid_sq)
                if face_margin < -face_margin_tol:
                    continue
                if face_margin < 0.0:
                    raise EndpointOptimizationError(
                        f"{endpoint} rank-2 face feasibility is numerically "
                        "ambiguous")
                half_width = math.sqrt(
                    max(face_margin, 0.0) / quadratic)
                free_bound_lo_delta = float(lo_delta[free_index])
                free_bound_hi_delta = float(hi_delta[free_index])
                feasible_delta_lo = max(
                    free_bound_lo_delta,
                    free_delta_centre - half_width,
                )
                feasible_delta_hi = min(
                    free_bound_hi_delta,
                    free_delta_centre + half_width,
                )
                interval_scale = max(
                    1.0, abs(feasible_delta_lo), abs(feasible_delta_hi))
                interval_tol = (
                    64.0 * np.finfo(float).eps * interval_scale)
                if feasible_delta_lo > feasible_delta_hi + interval_tol:
                    continue
                if feasible_delta_lo > feasible_delta_hi:
                    raise EndpointOptimizationError(
                        f"{endpoint} rank-2 face interval is numerically ambiguous")
                for free_delta in (feasible_delta_lo, feasible_delta_hi):
                    candidate_delta = np.empty(2, dtype=float)
                    candidate_delta[fixed_index] = fixed_delta
                    candidate_delta[free_index] = free_delta
                    if not _within_bounds(
                            candidate_delta, lo_delta, hi_delta):
                        continue
                    candidate_resid_sq, candidate_tol = (
                        centered_residual_certificate(candidate_delta)
                    )
                    if candidate_resid_sq <= level + candidate_tol:
                        candidates.append(candidate_delta)
        if not candidates:
            raise EndpointOptimizationError(
                f"{endpoint} rank-2 face enumeration found no valid endpoint")
        best = min(candidates, key=objective)
        return certify(best)

    raise NotImplementedError(
        "box-active endpoint sharpness is implemented only for rank two")


def identified_set_report(y, R, c, lower, upper, *, alpha1: float = 0.05,
                          alpha2: float = 0.05, ceiling_U: float | None = None,
                          tol: float = 1e-10,
                          threshold_policy: str = "known_chi2",
                          n_sim: int | None = None,
                          branch_id: str = "unspecified",
                          input_modes: tuple | list | None = None,
                          observational_claim_allowed: bool = False
                          ) -> IdentifiedSetReport:
    """Compute the A8 identified-set report for whitened observations y = R g + eps.

    Parameters: y (m,) whitened data; R (m,p) response; c (p,) signed comparator
    coefficients; lower/upper (p,) signed component bounds (np.inf = no ceiling).
    """
    y = np.asarray(y, dtype=float).ravel()
    R = np.asarray(R, dtype=float)
    c = np.asarray(c, dtype=float).ravel()
    lower = np.asarray(lower, dtype=float).ravel()
    upper = np.asarray(upper, dtype=float).ravel()
    tol = float(tol)
    if not math.isfinite(tol) or tol <= 0.0:
        raise ValueError("tol must be finite and positive")
    if R.ndim != 2:
        raise ValueError("R must be a two-dimensional response matrix")
    m, p = R.shape
    if not (y.shape == (m,) and c.shape == (p,) and lower.shape == (p,)
            and upper.shape == (p,)):
        raise ValueError("shape mismatch between y, R, c, lower, upper")
    if (not np.all(np.isfinite(y)) or not np.all(np.isfinite(R))
            or not np.all(np.isfinite(c))):
        raise ValueError("y, R, and c must contain only finite values")
    if np.any(np.isnan(lower)) or np.any(np.isnan(upper)):
        raise ValueError("component bounds must not contain NaN")
    if np.any(np.isposinf(lower)) or np.any(np.isneginf(upper)):
        raise ValueError(
            "lower bounds may use only -inf and upper bounds only +inf")
    if np.any(lower > upper):
        raise ValueError("lower bounds must not exceed upper bounds")
    if ceiling_U is not None:
        ceiling_U = float(ceiling_U)
        if not math.isfinite(ceiling_U) or ceiling_U <= 0.0:
            raise ValueError("ceiling_U must be finite and positive")

    active, null = _split_columns(R)
    A = R[:, active]
    active_scale = _active_column_scales(A)
    A_scaled = A / active_scale
    scaled_lower, scaled_upper = _scaled_active_bounds(
        lower[active], upper[active], active_scale)
    rank_tol = tol * max(1.0, float(np.max(np.abs(A_scaled))))
    r = int(np.linalg.matrix_rank(A_scaled, tol=rank_tol))
    if r != active.size:
        raise NotImplementedError(
            "identified_set_report requires axis-aligned nulls: the null space of R "
            "must be spanned by zero columns (the registered rank-2 case)")

    tau = two_stage_tau(m, r, alpha1=alpha1, alpha2=alpha2,
                        threshold_policy=threshold_policy, n_sim=n_sim)

    # Stage 1: specification test on the m - r residual directions.
    z_anchor, centre_correction, centre_residual = _least_squares_centre(
        A_scaled, y)
    centre_lo_delta, centre_hi_delta = _bounds_relative_to_centre(
        lower[active], upper[active], active_scale,
        z_anchor, centre_correction)
    s1 = float(centre_residual @ centre_residual)
    if not math.isfinite(s1):
        raise EndpointOptimizationError("stage-1 least-squares residual is non-finite")
    spec_pass = s1 <= tau.tau1

    # Null-box contribution to x_C (exact: null columns never touch the data).
    null_lo = 0.0
    null_hi = 0.0
    null_hi_arithmetic_scale = 0.0
    unbounded = False
    for j in null:
        cj = c[j]
        if cj == 0.0:
            continue
        contrib = sorted((cj * lower[j], cj * upper[j]))
        if not np.isfinite(contrib[0]):
            unbounded = True
        if not np.isfinite(contrib[1]):
            unbounded = True
        null_lo += contrib[0]
        null_hi += contrib[1]
        if np.isfinite(contrib[1]):
            null_hi_arithmetic_scale += abs(float(contrib[1]))

    empty = not spec_pass
    reach_lo = math.nan
    reach_hi = math.nan
    reach_hi_arithmetic_scale = math.nan
    if spec_pass:
        # Stage 2: cone-constrained feasibility on the reachable directions.
        level = s1 + tau.tau2
        c_R = c[active]
        if tau.tau2 == 0.0:
            # Full column rank makes the population reachable set exactly the
            # unconstrained least-squares singleton.  Its exclusion by the box
            # is scientific emptiness; no bounded numerical solve is needed.
            population_bound_status = _bound_status(
                np.zeros(active.size, dtype=float),
                centre_lo_delta,
                centre_hi_delta,
            )
            if population_bound_status == "outside":
                empty = True
            elif population_bound_status == "ambiguous":
                # Resolve an exact canonical boundary that may differ by one
                # rounding step when the equivalent physical bound was divided
                # by an extreme column scale.  This route is consulted only
                # after the translation-stable local route is ambiguous.
                absolute_lo_delta = (
                    scaled_lower - z_anchor - centre_correction)
                absolute_hi_delta = (
                    scaled_upper - z_anchor - centre_correction)
                alternate_status = _bound_status(
                    np.zeros(active.size, dtype=float),
                    absolute_lo_delta,
                    absolute_hi_delta,
                )
                if alternate_status != "inside":
                    raise EndpointOptimizationError(
                        "population box membership is numerically ambiguous")
            if not empty:
                c_scaled = c_R / active_scale
                population_terms = tuple(
                    float(coefficient) * float(coordinate)
                    for coefficient, coordinate in zip(c_scaled, z_anchor)
                ) + tuple(
                    float(coefficient) * float(displacement)
                    for coefficient, displacement in zip(
                        c_scaled, centre_correction)
                )
                population_value = float(math.fsum(population_terms))
                population_arithmetic_scale = float(math.fsum(
                    abs(term) for term in population_terms))
                if (not math.isfinite(population_value)
                        or not math.isfinite(population_arithmetic_scale)):
                    raise EndpointOptimizationError(
                        "population endpoint is non-finite")
                reach_lo = reach_hi = population_value
                reach_hi_arithmetic_scale = population_arithmetic_scale
        else:
            if active.size == 2:
                feasible_delta, minimum_residual = _rank2_box_least_squares(
                    A_scaled, centre_residual,
                    centre_lo_delta, centre_hi_delta)
                feasibility_tol = _residual_roundoff_tolerance(
                    A_scaled, centre_residual, feasible_delta,
                    level, minimum_residual)
                if minimum_residual > level + feasibility_tol:
                    empty = True
                elif minimum_residual > level:
                    raise EndpointOptimizationError(
                        "stage-2 rank-2 feasibility is numerically ambiguous")
                else:
                    reach_lo, _ = _constrained_extreme(
                        A, y, c_R, level, lower[active], upper[active],
                        feasible_delta,
                        sense=+1.0)
                    reach_hi, reach_hi_arithmetic_scale = _constrained_extreme(
                        A, y, c_R, level, lower[active], upper[active],
                        feasible_delta,
                        sense=-1.0)
            else:
                # The unconstrained centre is a valid witness only when the
                # analytic objective supports are also box-inactive.  The
                # endpoint helper refuses every higher-dimensional box-active
                # case instead of converting a local optimiser result into a
                # purportedly sharp scientific interval.
                centre_delta = np.zeros(active.size, dtype=float)
                reach_lo, _ = _constrained_extreme(
                    A, y, c_R, level, lower[active], upper[active],
                    centre_delta,
                    sense=+1.0)
                reach_hi, reach_hi_arithmetic_scale = _constrained_extreme(
                    A, y, c_R, level, lower[active], upper[active],
                    centre_delta,
                    sense=-1.0)

    if empty:
        status = STATUS_EMPTY
        x_lo = math.nan
        x_hi = math.nan
        F_lo = F_hi = None
    else:
        x_lo = float(math.fsum((reach_lo, null_lo)))
        x_hi = float(math.fsum((reach_hi, null_hi)))
        x_hi_arithmetic_scale = (
            reach_hi_arithmetic_scale + null_hi_arithmetic_scale)
        if unbounded:
            status = STATUS_UNBOUNDED
            F_lo = F_hi = None
        else:
            F_lo = F_hi = None
            status = STATUS_FEASIBLE
            if ceiling_U is not None:
                F_lo = max(0.0, x_lo) / ceiling_U
                F_hi = max(0.0, x_hi) / ceiling_U
                ceiling_excess = x_hi - ceiling_U
                ceiling_tol = _scalar_comparison_tolerance(
                    x_hi, ceiling_U, x_hi_arithmetic_scale)
                if abs(ceiling_excess) <= ceiling_tol:
                    raise EndpointOptimizationError(
                        "ceiling classification is numerically ambiguous: "
                        f"x_hi={x_hi!r}, ceiling_U={ceiling_U!r}, "
                        f"tolerance={ceiling_tol!r}")
                if ceiling_excess > 0.0:
                    status = STATUS_CEILING_UNFIT

    return IdentifiedSetReport(
        status=status, x_lo=x_lo, x_hi=x_hi,
        reachable_lo=reach_lo, reachable_hi=reach_hi,
        null_lo=null_lo, null_hi=null_hi,
        spec_stat=s1, spec_threshold=tau.tau1, spec_pass=spec_pass,
        rank=r, m=m, F_lo=F_lo, F_hi=F_hi, tau=tau,
        branch_id=str(branch_id),
        component_bounds=tuple((float(lo), float(hi)) for lo, hi in zip(lower, upper)),
        input_modes=tuple(input_modes or ()),
        observational_claim_allowed=bool(observational_claim_allowed),
        threshold_policy=tau.threshold_policy,
        n_sim=tau.n_sim,
        df_residual=tau.df_residual,
        df_reachable=tau.df_reachable,
    )


def curvature_branch_bounds(lower, upper, *, curvature_index: int = 3,
                            branch: str = "open") -> tuple[np.ndarray, np.ndarray, str]:
    """Return signed curvature branch bounds without mutating the input arrays.

    ``open`` keeps Omega_k_aniso in [0, U_k]. ``all`` permits signed curvature
    [-U_k, U_k]. This is branch metadata for diagnostic identified sets, not a
    family-identification or geometry claim.
    """
    lo = np.asarray(lower, dtype=float).copy()
    hi = np.asarray(upper, dtype=float).copy()
    j = int(curvature_index)
    if not (0 <= j < lo.size):
        raise ValueError("curvature_index out of range")
    u = float(hi[j])
    if not np.isfinite(u) or u < 0.0:
        raise ValueError("curvature upper bound must be finite and nonnegative")
    if branch == "open":
        lo[j] = 0.0
        hi[j] = u
        branch_id = "open_branch[0,Uk]"
    elif branch == "all":
        lo[j] = -u
        hi[j] = u
        branch_id = "all_branch[-Uk,Uk]"
    else:
        raise ValueError("branch must be open or all")
    return lo, hi, branch_id


def signed_curvature_branch_reports(y, R, c, lower, upper, *, curvature_index: int = 3,
                                    branches=("open", "all"), **kwargs
                                    ) -> dict[str, IdentifiedSetReport]:
    """Compute identified-set reports for the requested signed curvature branches."""
    reports: dict[str, IdentifiedSetReport] = {}
    for branch in branches:
        lo, hi, branch_id = curvature_branch_bounds(
            lower, upper, curvature_index=curvature_index, branch=str(branch))
        reports[branch_id] = identified_set_report(
            y, R, c, lo, hi, branch_id=branch_id, **kwargs)
    return reports


# ---------------------------------------------------------------------------
# Imbens-Manski endpoint semantics (P35)
# ---------------------------------------------------------------------------

def im_critical_value(delta_hat: float, se_max: float, alpha: float = 0.05) -> float:
    """C_N solving Phi(C_N + delta_hat/se_max) - Phi(-C_N) = 1 - alpha.

    Interpolates between the one-sided z_{1-alpha} (wide interval, delta >> se) and
    the two-sided z_{1-alpha/2} (point-identified limit, delta = 0)."""
    delta_hat = max(float(delta_hat), 0.0)
    alpha = float(alpha)
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha in (0,1)")
    if se_max <= 0.0:
        return float(stats.norm.ppf(1.0 - alpha))
    ratio = delta_hat / float(se_max)

    def f(cn: float) -> float:
        return stats.norm.cdf(cn + ratio) - stats.norm.cdf(-cn) - (1.0 - alpha)

    return float(optimize.brentq(f, 0.0, 10.0, xtol=1e-12))


def im_interval(x_lo: float, x_hi: float, se_lo: float, se_hi: float,
                alpha: float = 0.05) -> tuple[float, float, float]:
    """Imbens-Manski CI for the PARAMETER: [x_lo - C_N se_lo, x_hi + C_N se_hi]."""
    cn = im_critical_value(x_hi - x_lo, max(float(se_lo), float(se_hi)), alpha)
    return float(x_lo) - cn * float(se_lo), float(x_hi) + cn * float(se_hi), cn


def projection_interval(x_lo: float, x_hi: float, se_lo: float, se_hi: float,
                        alpha: float = 0.05) -> tuple[float, float]:
    """Set-coverage projection CI (z_{1-alpha/2} per endpoint): covers the whole
    identified set, hence CONSERVATIVE for the scalar parameter."""
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    return float(x_lo) - z * float(se_lo), float(x_hi) + z * float(se_hi)


def endpoint_interval(x_lo: float, x_hi: float, se_lo: float, se_hi: float,
                      alpha: float = 0.05) -> tuple[float, float]:
    """Naive per-endpoint one-sided z_{1-alpha} CI: the UNDERCOVERING foil -- its
    coverage of a boundary point drops to 1 - 2 alpha as the width Delta -> 0."""
    z = float(stats.norm.ppf(1.0 - alpha))
    return float(x_lo) - z * float(se_lo), float(x_hi) + z * float(se_hi)


# ---------------------------------------------------------------------------
# Registered r = 2, m = 6 toy (reproduces the section-10 example [0.11, 0.17])
# ---------------------------------------------------------------------------

def toy_design(m: int = 6, *, curvature_branch: str = "open") -> dict:
    """The registered toy: g = (Sigma2, W2, Omega_tilt, Omega_k); W2 and Omega_k are
    zero columns (structural nulls); truth (0.12, 0, 0.03, 0); MES ceilings
    U_W = 0.04, U_k = 0.02. Population identified interval = [0.11, 0.17]."""
    if m < 4:
        raise ValueError("need m >= 4 for the two-stage toy")
    R = np.zeros((m, 4))
    # two orthogonal reachable channels spread over the m rows
    R[: m // 2, 0] = 1.0                     # Sigma2 rows
    R[m // 2:, 2] = 1.0                      # Omega_tilt rows
    c = np.array([1.0, -1.0, 1.0, 1.0])
    lower = np.zeros(4)
    upper = np.array([np.inf, 0.04, np.inf, 0.02])
    if curvature_branch == "all":
        lower[3] = -upper[3]
    elif curvature_branch != "open":
        raise ValueError("curvature_branch must be open or all")
    g_true = np.array([0.12, 0.0, 0.03, 0.0])
    return {"R": R, "c": c, "lower": lower, "upper": upper, "g_true": g_true}


@dataclass(frozen=True)
class ImCoverageResult:
    n_mc: int
    seed: int
    alpha: float
    delta_over_sigma: float
    coverage_projection: float
    coverage_im: float
    coverage_endpoint: float
    se_binomial: float
    cn_im: float


def im_coverage_experiment(*, n_mc: int = 2000, seed: int = 20260708,
                           alpha: float = 0.05,
                           delta_over_sigma: float = 0.5) -> ImCoverageResult:
    """MC coverage of the three endpoint constructions at a boundary point.

    The r = 2, m = 6 toy: both interval endpoints derive from the SAME reachable
    estimate c_R^T g_hat (perfectly correlated endpoint noise -- exactly the regime
    where the IM equation is tight). Truth = the UPPER population endpoint (worst
    case). delta_over_sigma sets the interval-width-to-endpoint-se ratio; small
    values expose the naive endpoint construction's undercoverage."""
    toy = toy_design()
    A = toy["R"][:, [0, 2]]
    c_R = np.array([1.0, 1.0])
    gram_inv = np.linalg.inv(A.T @ A)
    unit_se = math.sqrt(float(c_R @ gram_inv @ c_R))

    null_lo = -0.04     # c_W * U_W
    null_hi = +0.02     # c_k * U_k
    delta = null_hi - null_lo
    sigma_noise = delta / (float(delta_over_sigma) * unit_se)
    se = sigma_noise * unit_se

    x_pt_true = float(c_R @ toy["g_true"][[0, 2]])
    theta = x_pt_true + null_hi              # upper endpoint = worst case

    rng = np.random.default_rng(seed)
    hits_proj = hits_im = hits_end = 0
    cn = im_critical_value(delta, se, alpha)
    for _ in range(int(n_mc)):
        eps = rng.normal(size=A.shape[0]) * sigma_noise
        g_hat, *_ = np.linalg.lstsq(A, A @ toy["g_true"][[0, 2]] + eps, rcond=None)
        x_pt = float(c_R @ g_hat)
        x_lo = x_pt + null_lo
        x_hi = x_pt + null_hi
        lo, hi = projection_interval(x_lo, x_hi, se, se, alpha)
        hits_proj += int(lo <= theta <= hi)
        lo, hi, _ = im_interval(x_lo, x_hi, se, se, alpha)
        hits_im += int(lo <= theta <= hi)
        lo, hi = endpoint_interval(x_lo, x_hi, se, se, alpha)
        hits_end += int(lo <= theta <= hi)

    n = float(n_mc)
    cov_im = hits_im / n
    se_bin = math.sqrt(max(cov_im * (1.0 - cov_im), 1e-12) / n)
    return ImCoverageResult(
        n_mc=int(n_mc), seed=int(seed), alpha=float(alpha),
        delta_over_sigma=float(delta_over_sigma),
        coverage_projection=hits_proj / n, coverage_im=cov_im,
        coverage_endpoint=hits_end / n, se_binomial=se_bin, cn_im=cn,
    )


@dataclass(frozen=True)
class RefutabilityPower:
    amplitudes: tuple
    empty_rate: tuple
    se: tuple
    alpha1: float
    n_mc: int
    seed: int


def refutability_power_experiment(amplitudes=(0.0, 1.0, 2.0, 3.0, 4.0, 6.0), *,
                                  n_mc: int = 1000, seed: int = 20260708,
                                  alpha1: float = 0.05) -> RefutabilityPower:
    """Empty-set rate under injected misspecification = specification-test power.

    y = R g_true + eps + a u with u a unit vector orthogonal to col(R): the stage-1
    residual statistic is noncentral chi^2_{m-r}(a^2), so the empty rate at a = 0 is
    alpha1 by construction (size) and rises monotonically with a (power). This is
    the refutability FEATURE of the identified-set semantics, not a defect."""
    toy = toy_design()
    R = toy["R"]
    g_true = toy["g_true"]
    A = R[:, [0, 2]]
    m = R.shape[0]
    q, _ = np.linalg.qr(A, mode="complete")
    u = q[:, -1]                              # unit vector orthogonal to col(A)
    tau = two_stage_tau(m, 2, alpha1=alpha1, alpha2=0.05)
    proj = A @ np.linalg.inv(A.T @ A) @ A.T
    perp = np.eye(m) - proj

    rng = np.random.default_rng(seed)
    rates = []
    ses = []
    for a in amplitudes:
        n_empty = 0
        for _ in range(int(n_mc)):
            y = A @ g_true[[0, 2]] + rng.normal(size=m) + float(a) * u
            s1 = float(y @ perp @ y)
            n_empty += int(s1 > tau.tau1)
        rate = n_empty / float(n_mc)
        rates.append(rate)
        ses.append(math.sqrt(max(rate * (1.0 - rate), 1e-12) / float(n_mc)))
    return RefutabilityPower(
        amplitudes=tuple(float(a) for a in amplitudes),
        empty_rate=tuple(rates), se=tuple(ses),
        alpha1=float(alpha1), n_mc=int(n_mc), seed=int(seed),
    )
