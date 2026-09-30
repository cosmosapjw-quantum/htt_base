"""Conditional local geometry from supplied tensors, without evolution.

Tetrad signature is (-+++), c=1 for normalized four-velocities u=U/c.
Spatial vectors point toward sources. These routines evaluate declared inputs;
they do not reconstruct a spacetime, select a homogeneous action, or calibrate
observational uncertainty. Tolerances are numerical acceptance thresholds, not
measurement uncertainties or exact proof certificates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .r7_contracts import NumericalUnresolved, finite_array

METRIC = np.diag([-1., 1., 1., 1.])
METRIC.setflags(write=False)


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return value


def _representable(value, name):
    if not np.isfinite(value).all():
        raise NumericalUnresolved(f"{name} is not representable at supplied scale")
    return value


def _symmetric(value, name, size=3):
    result = finite_array(value, shape=(size, size), name=name)
    scale = max(float(np.linalg.norm(result)), np.finfo(float).tiny)
    if np.linalg.norm(result - result.T) > 64*np.finfo(float).eps*scale:
        raise ValueError(f"{name} must be symmetric")
    return (result + result.T)/2


def unit_timelike(u, *, tolerance=1e-10):
    """Validate a future directed normalized contravariant four-vector."""
    tolerance = _positive(tolerance, "tolerance")
    if tolerance > 1e-6:
        raise ValueError("normalization tolerance must not exceed 1e-6")
    u = finite_array(u, shape=(4,), name="u")
    norm = float(_representable(u @ METRIC @ u, "timelike norm"))
    if u[0] <= 0 or norm >= 0 or abs(norm + 1) > tolerance:
        raise ValueError("expected future unit timelike u in signature -+++")
    return u


def four_velocity(beta):
    beta = finite_array(beta, shape=(3,), name="beta")
    b2 = float(beta @ beta)
    if b2 >= 1:
        raise ValueError("beta must be subluminal")
    if 1-b2 < 128*np.finfo(float).eps:
        raise NumericalUnresolved("beta too close to the null boundary")
    return np.r_[1., beta] / math.sqrt(1-b2)


def lorentz_boost(beta):
    """Active boost sending e0 to gamma(1,beta); inverse is boost(-beta)."""
    u = four_velocity(beta)
    beta = np.asarray(beta, dtype=float)
    gamma = u[0]
    result = np.eye(4)
    result[0, 0] = gamma
    result[0, 1:] = result[1:, 0] = gamma*beta
    result[1:, 1:] += (gamma*gamma/(gamma+1))*np.outer(beta, beta)
    return result


@dataclass(frozen=True)
class RelativeMotion:
    first: str
    second: str
    gamma: float
    rapidity: float
    beta_magnitude: float


def relative_motion(u, v, *, first: str, second: str):
    """Frame names are mandatory: U/O and U/N are distinct estimands."""
    if not isinstance(first, str) or not first.strip() or not isinstance(second, str) or not second.strip():
        raise ValueError("explicit nonempty physical congruence names required")
    u, v = unit_timelike(u), unit_timelike(v)
    gamma = -float(u @ METRIC @ v)
    if gamma < 1-1e-10:
        raise NumericalUnresolved("relative Lorentz factor below unity")
    gamma = max(gamma, 1.)  # within the declared normalization roundoff only
    return RelativeMotion(first, second, gamma, math.acosh(gamma), math.sqrt((gamma-1)*(gamma+1))/gamma)


def intercept_velocity(zeta0, zeta, *, tolerance=1e-10):
    """Ideal zero-distance intercept -> U in the observer tetrad.

    Requires the absolute free-intercept law 1+z=gamma(1+beta.n).
    Finite-distance/noisy fits generally do not lie on this mass shell.
    """
    zeta = finite_array(zeta, shape=(3,), name="zeta")
    return unit_timelike(np.r_[float(zeta0), zeta], tolerance=tolerance)


@dataclass(frozen=True)
class HubbleLift:
    source_u: np.ndarray
    symmetric_gradient: np.ndarray
    representative: np.ndarray
    eigengap: float
    eigenvalue: float


def hubble_tensor_lift(h0, h1, q, *, geodesic: bool, relative_gap=1e-9):
    """Lift H(n)=h0+h1.n+q:nn modulo g using B_ab u^b=0.

    Geodesicity is a supplied premise. This does not recover vorticity or
    the homogeneous normal N. Repeated timelike eigenvalues are unresolved.
    """
    if geodesic is not True:
        raise ValueError("geodesic premise is required for the slope lift")
    relative_gap = _positive(relative_gap, "relative_gap")
    h0 = float(h0)
    if not math.isfinite(h0):
        raise ValueError("h0 must be finite")
    h1 = finite_array(h1, shape=(3,), name="h1")
    q = _symmetric(q, "q")
    scale = max(abs(h0), float(np.linalg.norm(h1)), float(np.linalg.norm(q)), np.finfo(float).tiny)
    if abs(np.trace(q)) > 64*np.finfo(float).eps*scale:
        raise ValueError("q must be trace free")
    s = np.zeros((4, 4)); s[0, 0] = h0
    s[0, 1:] = s[1:, 0] = -h1/2
    s[1:, 1:] = q
    values, vectors = np.linalg.eig(METRIC @ s)
    if np.max(np.abs(values.imag)) > relative_gap*scale:
        raise NumericalUnresolved("complex spectrum has no certified physical lift")
    candidates = []
    for i in range(4):
        if np.max(np.abs(vectors[:, i].imag)) > relative_gap:
            continue
        v = vectors[:, i].real
        norm = float(v @ METRIC @ v)
        if norm < -relative_gap:
            gap = float(np.min(np.abs(values[i] - np.delete(values, i))))
            if gap <= relative_gap*scale:
                raise NumericalUnresolved("timelike eigenvalue is repeated or numerically inseparable")
            v = v/math.sqrt(-norm)
            if v[0] < 0:
                v = -v
            candidates.append((v, float(values[i].real), gap))
    if len(candidates) != 1:
        raise NumericalUnresolved("no unique separated timelike eigenline")
    u, lam, gap = candidates[0]
    b = s-lam*METRIC
    if np.linalg.norm(b @ u) > 16*relative_gap*scale*max(1., np.linalg.norm(u)):
        raise NumericalUnresolved("lift annihilation residual too large")
    return HubbleLift(finite_array(u), finite_array(b), finite_array(s), gap, lam)


def clock_normal(gradient_covector):
    """Future unit normal selected by a supplied timelike scalar gradient.

    Homogeneity and invariant clock provenance must be established upstream.
    """
    d = finite_array(gradient_covector, shape=(4,), name="gradient_covector")
    norm = float(d @ METRIC @ d)
    if norm >= 0:
        raise ValueError("clock gradient must be timelike")
    if -norm <= 128*np.finfo(float).eps*float(d @ d):
        raise NumericalUnresolved("clock gradient nearly null")
    n = METRIC @ d/math.sqrt(-norm)
    return n if n[0] > 0 else -n


def perfect_fluid_normal_projection(epsilon, pressure, beta):
    """Return (E,J,S) in N frame; epsilon,p share energy-density units.

    A single perfect fluid is assumed. Summed J=0 for several fluids does
    not establish that any individual component is untilted.
    """
    epsilon, pressure = float(epsilon), float(pressure)
    if not np.isfinite([epsilon, pressure]).all():
        raise ValueError("finite epsilon and pressure required")
    u = four_velocity(beta); beta = np.asarray(beta, dtype=float)
    wgamma2 = (epsilon+pressure)*u[0]**2
    e, j, s = wgamma2-pressure, wgamma2*beta, pressure*np.eye(3)+wgamma2*np.outer(beta, beta)
    for value in (e, j, s):
        _representable(value, "perfect-fluid projection")
    return e, j, s


def flux_to_beta(flux_norm, enthalpy):
    """Invert |J|=w beta/(1-beta^2) on the w>0 single-fluid branch."""
    w = _positive(enthalpy, "enthalpy")
    j = float(flux_norm)
    if not math.isfinite(j) or j < 0:
        raise ValueError("flux_norm must be finite and nonnegative")
    # Rescale before division; remains stable for very large j/w.
    m = max(j, w)
    js, ws = j/m, w/m
    result = js/(ws/2+math.hypot(ws/2, js))
    if result == 1.:
        raise NumericalUnresolved("subluminal inverse indistinguishable from unity")
    return result


def tilt_interval(j_lower, j_upper, w_lower, w_upper):
    values = np.asarray([j_lower, j_upper, w_lower, w_upper], dtype=float)
    if not np.isfinite(values).all() or not 0 <= j_lower <= j_upper or not 0 < w_lower <= w_upper:
        raise ValueError("require finite 0<=j_lower<=j_upper and 0<w_lower<=w_upper")
    return flux_to_beta(j_lower, w_upper), flux_to_beta(j_upper, w_lower)


def endpoint_boost(redshift, angular_distance, luminosity_distance, direction, beta):
    """Same physical ray under observer boost: (z',dA',dL',D).

    Direction is the old-frame source direction; angular arguments of sky
    maps still require aberration. No polarization transformation is implied.
    """
    n = finite_array(direction, shape=(3,), name="direction")
    if abs(float(n@n)-1) > 1e-10:
        raise ValueError("direction must be unit length")
    z, da, dl = map(float, (redshift, angular_distance, luminosity_distance))
    if not np.isfinite([z, da, dl]).all() or z <= -1 or min(da, dl) < 0:
        raise ValueError("require z>-1 and nonnegative finite distances")
    u = four_velocity(beta)
    d = float(u[0]+u[1:]@n)
    result = ((1+z)/d-1, d*da, dl/d, d)
    _representable(result, "endpoint transform")
    return result


def inverse_temperature_boost(a, b):
    """Affine absolute inverse temperature a+b.n -> (rest T, beta).

    This is the scalar blackbody criterion only. It is not a test of a full
    polarized CMB law or an identification of observer motion with arbitrary
    intrinsic sky freedom.
    """
    a = _positive(a, "a")
    b = finite_array(b, shape=(3,), name="b")
    u = four_velocity(-b/a)
    return float(_representable(u[0]/a, "rest temperature")), -b/a


def homogeneous_scalar_curvature(n, a):
    """R3=-tr(n^2)+(tr n)^2/2-6a^2, C convention in BIC-02.

    Supplied orthonormal orbit frame, inverse-length n,a; n a=0 is Jacobi.
    Returning R3 does not identify a Bianchi action from observations.
    """
    n = _symmetric(n, "n"); a = finite_array(a, shape=(3,), name="a")
    scale = max(float(np.linalg.norm(n)*np.linalg.norm(a)), np.finfo(float).tiny)
    if np.linalg.norm(n@a) > 128*np.finfo(float).eps*scale:
        raise ValueError("n a=0 Jacobi constraint violated")
    result = -np.trace(n@n)+np.trace(n)**2/2-6*(a@a)
    return float(_representable(result, "spatial scalar curvature"))


def homogeneous_connection(structure):
    """C[k,i,j] for [e_i,e_j]=C[k,i,j] e_k -> Gamma[k,i,j]."""
    c = finite_array(structure, shape=(3, 3, 3), name="structure")
    scale = max(float(np.linalg.norm(c)), np.finfo(float).tiny)
    if np.linalg.norm(c+c.swapaxes(1, 2)) > 128*np.finfo(float).eps*scale:
        raise ValueError("structure coefficients must be antisymmetric")
    jac = np.einsum('mjk,lim->lijk', c, c)+np.einsum('mki,ljm->lijk', c, c)+np.einsum('mij,lkm->lijk', c, c)
    _representable(jac, "Jacobi residual")
    if np.linalg.norm(jac) > 512*np.finfo(float).eps*scale**2:
        raise ValueError("Jacobi constraint violated")
    g = np.empty_like(c)
    for k in range(3):
        for i in range(3):
            for j in range(3):
                g[k, i, j] = (c[k, i, j]-c[i, j, k]+c[j, k, i])/2
    return _representable(g, "homogeneous connection")


def homogeneous_codazzi_flux(structure, extrinsic_curvature, *, kappa):
    """J_a=(D_b K^b_a-D_a trK)/kappa for spatially constant K.

    K_ADM=-h h nabla n (inverse length); kappa=8 pi G/c^4 for energy
    density. Orbit frame homogeneity of both C and K is supplied.
    """
    kappa = _positive(kappa, "kappa")
    g = homogeneous_connection(structure)
    k = _symmetric(extrinsic_curvature, "extrinsic_curvature")
    return _representable((np.einsum('bbd,da->a', g, k)-np.einsum('dba,bd->a', g, k))/kappa, "Codazzi flux")


def hamiltonian_orbit_curvature(*, energy_density_normal, cosmological_constant,
                                theta_normal, shear_full_contraction, kappa, speed_of_light):
    """Einstein constraint on the specified spacelike homogeneous orbit.

    kappa=8 pi G/c^4, energy density includes normal-frame tilt energy;
    shear_full_contraction is sigma_ab sigma^ab, without the 1/2 convention.
    A catalogue distance-curvature estimator is not this supplied geometrical
    input. All arguments must refer to the same normal frame, epoch and state.
    """
    c = _positive(speed_of_light, "speed_of_light")
    kappa = _positive(kappa, "kappa")
    e, lam, theta, sigma2 = map(float, (energy_density_normal, cosmological_constant, theta_normal, shear_full_contraction))
    if not np.isfinite([e, lam, theta, sigma2]).all() or sigma2 < 0:
        raise ValueError("finite inputs and nonnegative full shear contraction required")
    return float(_representable(2*kappa*e+2*lam-(2/3)*(theta/c)**2+sigma2/c**2, "Hamiltonian curvature"))


def ideal_position_drift_moment(moment, *, ideal_full_sky_calibrated_geodesic: bool):
    """M=<kappa(n)n^T>=S/5+W/3 -> (S,W) in the ideal BIC-04 limit.

    Supplied full-sphere angular moment and calibrated nonrotating frame are
    prerequisites. Finite masked sky averages cannot be substituted. W is the
    antisymmetric matrix in kappa=P(S+W)n, not an unlabelled vorticity vector.
    """
    if ideal_full_sky_calibrated_geodesic is not True:
        raise ValueError("ideal drift moment premises required")
    m = finite_array(moment, shape=(3, 3), name="drift moment")
    scale = max(float(np.linalg.norm(m)), np.finfo(float).tiny)
    if abs(np.trace(m)) > 128*np.finfo(float).eps*scale:
        raise ValueError("tangential drift moment must be trace free")
    return (_representable(2.5*(m+m.T), "drift shear"),
            _representable(1.5*(m-m.T), "drift rotation"))


@dataclass(frozen=True)
class VelocityKinematics:
    expansion: float
    shear_covariant: np.ndarray
    vorticity_covariant: np.ndarray
    acceleration_covariant: np.ndarray
    congruence: str
    frame: str


def kinematics_from_velocity_jet(u, derivative_covariant, *, speed_of_light, congruence, frame):
    """Supplied D_ab=nabla_a u_b in inverse-length units, u=U/c.

    Returns physical theta,sigma,omega in inverse-time and A in acceleration
    units. omega_ab=c h_a^c h_b^d D_[cd] (this explicit index convention).
    A value of beta alone supplies none of the derivatives required here.
    """
    if any(not isinstance(s, str) or not s.strip() for s in (congruence, frame)):
        raise ValueError("named congruence and tetrad frame required")
    u = unit_timelike(u); c = _positive(speed_of_light, "speed_of_light")
    d = finite_array(derivative_covariant, shape=(4, 4), name="velocity derivative")
    scale = max(float(np.linalg.norm(d)*np.linalg.norm(u)), np.finfo(float).tiny)
    if np.linalg.norm(d@u) > 128*np.finfo(float).eps*scale:
        raise ValueError("jet violates derivative of velocity normalization")
    ucov = METRIC@u
    projector = np.eye(4)+np.outer(ucov, u)
    h = METRIC+np.outer(ucov, ucov)
    spatial = projector@d@projector.T
    theta = c*float(np.trace(METRIC@spatial))
    shear = c*(spatial+spatial.T)/2-theta*h/3
    omega = c*(spatial-spatial.T)/2
    acceleration = c*c*(u@d)
    for value in (theta, shear, omega, acceleration):
        _representable(value, "velocity kinematics")
    return VelocityKinematics(theta, finite_array(shear), finite_array(omega), finite_array(acceleration), congruence, frame)


def invariant_eigenframe_structure(eigenvalues, derivative, *, invariant_on_homogeneous_neighborhood: bool, relative_gap=1e-9):
    """Reconstruct C from a simple invariant T in its orthonormal eigenframe.

    derivative[k,i,j]=(D_k T)_ij. This neither establishes homogeneity from
    point data nor reconstructs T from a sky morphology statistic.
    """
    if invariant_on_homogeneous_neighborhood is not True:
        raise ValueError("neighborhood invariance premise required")
    relative_gap = _positive(relative_gap, "relative_gap")
    lam = finite_array(eigenvalues, shape=(3,), name="eigenvalues")
    dt = finite_array(derivative, shape=(3, 3, 3), name="derivative")
    scale = max(float(np.max(np.abs(lam))), np.finfo(float).tiny)
    if min(abs(lam[i]-lam[j]) for i in range(3) for j in range(i)) <= relative_gap*scale:
        raise NumericalUnresolved("invariant tensor spectrum is not separated")
    dscale = max(float(np.linalg.norm(dt)), np.finfo(float).tiny)
    if np.linalg.norm(dt-dt.swapaxes(1, 2)) > 128*np.finfo(float).eps*dscale or np.linalg.norm(np.diagonal(dt, axis1=1, axis2=2)) > 128*np.finfo(float).eps*dscale:
        raise ValueError("derivative incompatible with a spatially constant symmetric eigenspectrum")
    g = np.zeros((3, 3, 3))
    for k in range(3):
        for i in range(3):
            for j in range(3):
                if i != j:
                    g[j, k, i] = dt[k, i, j]/(lam[i]-lam[j])
    c = g-g.swapaxes(1, 2)
    homogeneous_connection(c)  # also enforce the necessary Jacobi identity
    return c
