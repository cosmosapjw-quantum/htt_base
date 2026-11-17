"""Source-integrated distance-Hubble images of a fixed Gaussian experiment.

The optical eta excludes the separately fitted coherent-velocity nuisance.
All confidence supports use one simultaneous rank-r confidence cylinder.
These are distance-defined quantities, not a general congruence expansion.
"""
from __future__ import annotations

import numpy as np
from numpy.polynomial import legendre
from htt.htt.infer import r54_distance_estimators as de
from htt.htt.infer import r58_mixed_tensor_likelihood as mt

C_KM_S = 299792.458
Z_PIVOT = 0.055
Z_SCALE = 0.045
_GL_X, _GL_W = legendre.leggauss(64)


def _degree(degree):
    if isinstance(degree, (bool, np.bool_)) or not isinstance(degree, (int, np.integer)) or not 0 <= degree <= 3:
        raise ValueError('degree must be an integer from 0 to 3')
    return int(degree)


def _finite(value, name):
    a = np.asarray(value, dtype=float)
    if a.size == 0 or not np.isfinite(a).all():
        raise ValueError(name + ' must be nonempty and finite')
    return a


def _scalar(value, name):
    a = _finite(value, name)
    if a.ndim != 0:
        raise ValueError(name + ' must be scalar')
    return float(a)


def _direction(n):
    n = _finite(n, 'direction')
    if n.shape != (3,) or abs(float(n @ n) - 1.) > 1e-10:
        raise ValueError('direction must be a unit vector of shape (3,)')
    return n


def _redshift(z, *, scalar=False, positive=False):
    a = _scalar(z, 'redshift') if scalar else _finite(z, 'redshift')
    if np.any(np.asarray(a) < 0.) or (positive and np.any(np.asarray(a) <= 0.)):
        raise ValueError('redshift must be positive' if positive else 'redshift must be nonnegative')
    return a


def radial_jet(z, degree):
    """Return P_j(t), dP_j/dz, d2P_j/dz2, shape z.shape+(degree+1,).

    t=(z-.055)/.045. Values outside the sampled interval are extrapolations;
    evaluating them does not certify a cosmographic remainder there.
    """
    degree = _degree(degree)
    z = np.asarray(_redshift(z))
    t = (z - Z_PIVOT) / Z_SCALE
    arrays = []
    for derivative in range(3):
        arrays.append(np.stack([
            legendre.legval(t, legendre.legder(np.eye(degree + 1)[j], m=derivative))
            / Z_SCALE**derivative for j in range(degree + 1)
        ], axis=-1))
    if not all(np.isfinite(a).all() for a in arrays):
        raise ValueError('polynomial jet overflowed')
    return tuple(arrays)


def field_rows(z, n, degree):
    """Optical eta/eta_z/eta_zz rows; parameter layout V3,a0_9,...,aJ_9.

    The first three entries are exactly zero: the estimand excludes the
    declared coherent velocity. Its uncertainty is still profiled in the fit.
    """
    degree = _degree(degree)
    z, n = _redshift(z, scalar=True), _direction(n)
    b = de.multipole_basis(n[None, :])[0]
    return tuple(np.r_[np.zeros(3), (p[:, None] * b).ravel()]
                 for p in radial_jet(z, degree))


def radial_difference_row(z, z_ref, n, degree):
    """Common angular calibration cancels exactly in this optical contrast."""
    return field_rows(z, n, degree)[0] - field_rows(z_ref, n, degree)[0]


def source_design(z, n, g, degree):
    """Uncompressed N by [3+9(J+1)] mean design for application of actual O."""
    degree = _degree(degree)
    z = np.asarray(_redshift(z, positive=True))
    n, g = _finite(n, 'directions'), _finite(g, 'velocity response')
    if z.ndim != 1 or n.shape != (z.size, 3) or g.shape != z.shape:
        raise ValueError('need z(N), directions(N,3), g(N)')
    if np.max(np.abs(np.einsum('ni,ni->n', n, n) - 1.)) > 1e-10:
        raise ValueError('source directions must be unit vectors')
    b = de.multipole_basis(n)
    p = radial_jet(z, degree)[0]
    result = np.column_stack((g[:, None] * n, (p[:, :, None] * b[:, None, :]).reshape(z.size, -1)))
    if not np.isfinite(result).all():
        raise ValueError('source design overflowed')
    return result


def background_factors(z, omega_m, H0=67.36):
    """Smooth flat matter+Lambda reference, with c and H units retained.

    A fixed 64-point Gauss-Legendre integral defines chi_hat on 0<=z<=1.
    The inherited R54 interpolation is a separate numerical chart. Transport
    the known source eta offset before using this smooth-reference image.
    No radiation or curvature is silently added to the owned working law.
    """
    z = np.asarray(_redshift(z))
    om, h0 = _scalar(omega_m, 'omega_m'), _scalar(H0, 'H0')
    if not 0. <= om <= 1. or h0 <= 0. or np.any(z > 1.):
        raise ValueError('need 0<=omega_m<=1, H0>0 and 0<=z<=1 for this reference')
    zz = z[..., None] * ((_GL_X + 1.) / 2.)
    chi = .5 * z * np.sum(_GL_W / np.sqrt(om * (1. + zz)**3 + 1. - om), axis=-1)
    e = np.sqrt(om * (1. + z)**3 + 1. - om)
    lne_prime = 1.5 * om * (1. + z)**2 / e**2
    b = e * chi
    return dict(chi_hat=chi, E=e, dlnE_dz=lne_prime, B=b,
                B_prime=1. + lne_prime*b, H_ref=h0*e,
                q_ref=-1. + (1. + z)*lne_prime)


def point_image(theta, z, n, degree, omega_m, H0=67.36):
    """Exact smooth-reference H_D/q_D at a supplied optical-eta parameter.

    A minimum-norm representative of a singular fit is only a representative.
    Its image is not an identified estimate; test relevant rows separately.
    """
    z = _redshift(z, scalar=True)
    rows = field_rows(z, n, degree)
    theta = _finite(theta, 'theta')
    if theta.ndim != 1 or theta.shape != rows[0].shape:
        raise ValueError('theta has the wrong shape')
    bg = background_factors(z, omega_m, H0)
    eta, first, second = [float(row @ theta) for row in rows]
    if not np.isfinite([eta, first, second]).all():
        raise ValueError('field evaluation overflowed')
    denominator = float(1. - bg['B'] * first)
    result = dict(status='OK', eta_repo=eta, eta_relative=eta-np.log(H0),
                  eta_z=first, eta_zz=second, denominator=denominator,
                  H_D=None, H_D_km_s_Mpc=None, H_D_over_H_ref=None, q_D=None,
                  estimand='optical eta excluding declared coherent velocity nuisance',
                  interpolation_scope='smooth reference; sampled domain .01<z<.10')
    if not np.isfinite(denominator):
        result['status'] = 'NUMERICAL_RANGE_ERROR'
        return result
    if denominator <= 0.:
        result['status'] = 'NONPOSITIVE_DERIVATIVE'
        return result
    logh = float(np.log(bg['E']) + eta - np.log(denominator))
    if logh > np.log(np.finfo(float).max) or logh < np.log(np.nextafter(0., 1.)):
        result['status'] = 'NUMERICAL_RANGE_ERROR'
        return result
    h = float(np.exp(logh))
    q = float(bg['q_ref'] + (1. + z) * (first + (bg['B_prime']*first + bg['B']*second)/denominator))
    ratio = float(h / bg['H_ref'])
    if not np.isfinite([h, q, ratio]).all() or h <= 0.:
        result['status'] = 'NUMERICAL_RANGE_ERROR'
        return result
    result.update(H_D=h, H_D_km_s_Mpc=h, H_D_over_H_ref=ratio, q_D=q)
    return result


def _support(fit, row, level):
    """Delegate estimability and the shared confidence cutoff to R58."""
    return mt.linear_interval(fit, row, level=level, simultaneous=True)


def _denominator_support(fit, derivative_row, b, level):
    support = _support(fit, -float(b)*derivative_row, level)
    if support['identified']:
        support = dict(support, lower=1.+support['lower'], upper=1.+support['upper'],
                       estimate=1.+support['estimate'])
    return support


def radial_hubble_interval(fit, z, z_ref, n, degree, omega_m, H0=67.36, level=.95):
    """Conservative enclosing H_D(z,n)/H_D(z_ref,n) confidence interval.

    Separate scalar supports are all images of the same cylinder; their use
    as a box does not posit independent parameters. A nonpositive lower
    denominator bound fails certification, even if the plug-in point is valid.
    """
    z, zr = _redshift(z, scalar=True), _redshift(z_ref, scalar=True)
    rows, refrows = field_rows(z, n, degree), field_rows(zr, n, degree)
    bg, br = background_factors(z, omega_m, H0), background_factors(zr, omega_m, H0)
    delta = _support(fit, rows[0]-refrows[0], level)
    den = _denominator_support(fit, rows[1], bg['B'], level)
    denref = _denominator_support(fit, refrows[1], br['B'], level)
    result = dict(status='OK', lower=None, upper=None, estimate=None,
                  delta_eta=delta, denominator=den, denominator_ref=denref,
                  level=float(level), simultaneous=True, sharp=False,
                  method='support-box enclosure of one rank-r Gaussian confidence cylinder',
                  formal_equal_redshift_identity=bool(z == zr),
                  identity_on_positive_domain=1. if z == zr else None)
    if not all(a['identified'] for a in (delta, den, denref)):
        # Ingredient estimability is sufficient, not necessary for nonlinear
        # estimability. In particular the equal-redshift ratio cancels exactly.
        result['status'] = 'DOMAIN_NOT_CERTIFIED' if z == zr else 'INGREDIENT_UNIDENTIFIED'
        return result
    if min(den['lower'], denref['lower']) <= 0.:
        result['status'] = 'DOMAIN_NOT_CERTIFIED'
        return result
    if z == zr:
        result.update(lower=1., upper=1., estimate=1., sharp=True)
        return result
    ratio = float(bg['E']/br['E'])
    loglo = np.log(ratio) + delta['lower'] + np.log(denref['lower']) - np.log(den['upper'])
    loghi = np.log(ratio) + delta['upper'] + np.log(denref['upper']) - np.log(den['lower'])
    logpoint = np.log(ratio) + delta['estimate'] + np.log(denref['estimate']) - np.log(den['estimate'])
    if (loghi > np.log(np.finfo(float).max) or loglo < np.log(np.nextafter(0., 1.))
            or not np.isfinite([loglo, loghi, logpoint]).all()):
        result['status'] = 'NUMERICAL_RANGE_ERROR'
        return result
    result.update(lower=float(np.exp(loglo)), upper=float(np.exp(loghi)), estimate=float(np.exp(logpoint)))
    return result


def q_interval(fit, z, n, degree, omega_m, H0=67.36, level=.95):
    """Conservative q_D enclosure from supports of the same joint cylinder."""
    z = _redshift(z, scalar=True)
    rows, bg = field_rows(z, n, degree), background_factors(z, omega_m, H0)
    first = _support(fit, rows[1], level)
    numerator = _support(fit, float(bg['B_prime'])*rows[1]+float(bg['B'])*rows[2], level)
    den = _denominator_support(fit, rows[1], bg['B'], level)
    result = dict(status='OK', lower=None, upper=None, estimate=None,
                  eta_z=first, numerator=numerator, denominator=den,
                  level=float(level), simultaneous=True, sharp=False,
                  method='support-box enclosure of one rank-r Gaussian confidence cylinder')
    if not all(a['identified'] for a in (first, numerator, den)):
        result['status'] = 'INGREDIENT_UNIDENTIFIED'
        return result
    if den['lower'] <= 0.:
        result['status'] = 'DOMAIN_NOT_CERTIFIED'
        return result
    quotients = [a/b for a in (numerator['lower'], numerator['upper'])
                 for b in (den['lower'], den['upper'])]
    lo = float(bg['q_ref']+(1.+z)*(first['lower']+min(quotients)))
    hi = float(bg['q_ref']+(1.+z)*(first['upper']+max(quotients)))
    point = float(bg['q_ref']+(1.+z)*(first['estimate']+numerator['estimate']/den['estimate']))
    if not np.isfinite([lo, hi, point]).all():
        result['status'] = 'NUMERICAL_RANGE_ERROR'
        return result
    result.update(lower=lo, upper=hi, estimate=point)
    return result
