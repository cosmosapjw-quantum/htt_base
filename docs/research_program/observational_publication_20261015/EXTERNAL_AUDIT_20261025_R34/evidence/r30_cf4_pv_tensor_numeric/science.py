"""R30 conditional band-PV calculation. Importing this module does no work."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad, lebedev_rule
from scipy.special import roots_legendre, spherical_jn
from scipy.spatial import cKDTree

H = .6736
H0 = 67.36
OM = .3153
OL = .6847
OBHH = .02237
NS = .9649
SIGMA8 = .8111
TCMB = 2.7255
C = 299792.458
KAPPA = 5 / math.log(10)
RADII = np.array([5., 10., 20.])
BANDS = ((.005 * H, .02 * H), (.02 * H, .05 * H))
BASIS_LABELS = ('xx-yy', 'xx+yy-2zz', 'xy', 'xz', 'yz')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def verify_bindings(bindings):
    review=bindings['read_only_evidence']['exact_factor_independent_review']
    for item in (bindings['contract'], *bindings['immutable_numeric_inputs'].values(), review):
        p = Path(item['path'])
        if p.stat().st_size != item['bytes'] or sha256(p) != item['sha256']:
            raise ValueError(f"immutable input identity mismatch: {p}")
    with open(review['path']) as f:
        closeout=json.load(f)
    if (closeout.get('status')!='SCOPED_PASS_EXACT_FACTOR_METADATA_AND_ACTUAL_RESULT_CLOSEOUT' or
        closeout.get('candidate_identity') != 'sha256:'+bindings['immutable_numeric_inputs']['corrected_result']['sha256']):
        raise ValueError('exact-factor independent closeout mismatch')


def e_z(z):
    return np.sqrt(OM * (1 + z)**3 + OL)


def e_a(a):
    return np.sqrt(OM / a**3 + OL)


def distance_integral(z, order):
    x, w = roots_legendre(order)
    t = z[:, None] * (x[None] + 1) / 2
    return z * np.sum(w[None] / e_z(t), axis=1) / 2


def growth_integral(a, order):
    # t=a*u^2 makes the integrand smooth at the zero endpoint.
    x, w = roots_legendre(order)
    u = (x + 1) / 2
    t = a[:, None] * u[None]**2
    val = 2 * a[:, None] * u[None] / (t**3 * e_a(t)**3)
    return np.sum(w[None] * val, axis=1) / 2


def background(z, order):
    a = 1 / (1 + z)
    iz = distance_integral(z, order)
    ia = growth_integral(a, order)
    i1 = growth_integral(np.array([1.]), order)[0]
    ea = e_a(a)
    d = ea * ia / i1
    oma = OM / (a**3 * ea**2)
    f = -1.5 * oma + 1 / (a**2 * ea**3 * ia)
    g = a * H0 * ea * f * d
    chi = C * iz / H0
    logder = 1 / (1 + z) + 1 / (iz * e_z(z))
    j = -KAPPA * (1 + z) * logder / C
    return chi, g, j, d, f


def transfer(k):
    k = np.asarray(k, dtype=float)
    omhh = OM * H**2
    fb = OBHH / omhh
    theta = TCMB / 2.7
    s = 44.5 * np.log(9.83 / omhh) / np.sqrt(1 + 10 * (omhh * fb)**.75)
    keq = .0746 * omhh / theta**2
    alpha = 1 - .328 * np.log(431 * omhh) * fb + .38 * np.log(22.3 * omhh) * fb**2
    gamma = omhh * (alpha + (1 - alpha) / (1 + (.43 * k * s)**4))
    q = k / (13.41 * keq) * omhh / gamma
    l0 = np.log(2 * 2.718282 + 1.8 * q)
    c0 = 14.2 + 731 / (1 + 62.5 * q)
    return l0 / (l0 + c0 * q*q)


def top_hat(x):
    x = np.asarray(x, float)
    out = np.empty_like(x)
    near = np.abs(x) < .05
    y = x[near]
    out[near] = 1 - y*y / 10 + y**4 / 280 - y**6 / 15120
    y = x[~near]
    out[~near] = 3 * (np.sin(y) - y * np.cos(y)) / y**3
    return out


def power_amplitude():
    def integrand(logk):
        k = math.exp(logk)
        return k**3 * (k / .05)**NS * float(transfer(k))**2 * float(top_hat(k * 8 / H))**2 / (2 * math.pi**2)
    estimates = []
    for lo, hi in ((1e-6, 1e2), (1e-7, 1e3)):
        val, err = quad(integrand, math.log(lo), math.log(hi), epsrel=2e-9, epsabs=1e-12, limit=600)
        estimates.append((val, err, err / abs(val)))
    if max(v[2] for v in estimates) > 1e-7 or abs(estimates[0][0] / estimates[1][0] - 1) > 1e-6:
        raise ValueError(f'sigma8 normalization convergence failed: {estimates}')
    amp = SIGMA8**2 / estimates[1][0]
    return amp, estimates


def power(k, amp):
    return amp * (np.asarray(k) / .05)**NS * transfer(k)**2


def cc_rule(n, lo, hi):
    if n not in (16, 32):
        raise ValueError('only frozen CC16/32 rules')
    j = np.arange(n + 1)
    theta = math.pi * j / n
    weights = np.empty(n + 1)
    weights[0] = weights[-1] = 1 / (n*n - 1)
    interior = np.arange(1, n)
    w = np.ones(n - 1)
    for m in range(1, n // 2):
        w -= 2 * np.cos(2*m*theta[interior]) / (4*m*m - 1)
    w -= np.cos(n*theta[interior]) / (n*n - 1)
    weights[interior] = 2 * w / n
    return (lo+hi)/2 + (hi-lo)/2 * np.cos(theta), weights * (hi-lo)/2


def angular_rule(order):
    pts, weights = lebedev_rule(order)
    pts = np.asarray(pts).T.copy()
    weights = np.asarray(weights)
    if pts.shape[0] not in {35: (434,), 53: (974,), 65: (1454,)}[order]:
        raise ValueError('Lebedev rule size')
    if (np.max(abs(np.linalg.norm(pts, axis=1)-1)) > 1e-13 or
        abs(np.sum(weights)-4*math.pi) > 1e-12 or np.any(weights < 0)):
        raise ValueError('Lebedev rule geometry/weights')
    tree = cKDTree(pts)
    dist, mates = tree.query(-pts)
    if np.max(dist) > 1e-12 or np.any(mates[mates] != np.arange(len(pts))) or np.max(abs(weights-weights[mates])) > 1e-13:
        raise ValueError('Lebedev antipodal pairing')
    chosen = np.where(np.arange(len(pts)) < mates)[0]
    if len(chosen)*2 != len(pts):
        raise ValueError('Lebedev pair count')
    return pts, weights, pts[chosen], 2*weights[chosen]


def gram(k, u, weights, positions, directions, jg, L, nonref, refs, block=128):
    if block > 128:
        raise ValueError('direction block exceeds 128')
    matrix = np.zeros((5, 5), dtype=float)
    for start in range(0, len(weights), block):
        ub = u[start:start+block].T
        phase = positions @ ub
        amplitude = jg[:, None] * (directions @ ub)
        signal = amplitude * np.exp(1j*k*phase)
        # Difference before contraction; never construct rounded reference columns.
        w = L @ (signal[nonref] - signal[refs])
        matrix += np.real((w * weights[start:start+block][None]) @ w.conj().T)
    return matrix / (4*math.pi)


def joint_from_spectral(matrices, k, radial_weights, amp):
    joint = np.zeros((15, 15))
    for a, kk, wk in zip(matrices, k, radial_weights):
        smooth = np.exp(-.5 * (kk * RADII/H)**2)
        joint += wk * power(kk, amp) / (2*math.pi**2) * np.kron(np.outer(smooth, smooth), a)
    return joint


def matrix_diagnostics(joint):
    trace = float(np.trace(joint))
    asym = float(np.max(abs(joint-joint.T)))
    sym = (joint+joint.T)/2
    eig = np.linalg.eigvalsh(sym)
    if trace <= 0 or asym > 1e-12*trace or eig[0] < -1e-12*trace:
        raise ValueError(f'covariance symmetry/PSD failure: trace={trace}, asym={asym}, min_eig={eig[0]}')
    return sym, {'trace': trace, 'pre_symmetry_max_abs': asym, 'minimum_eigenvalue': float(eig[0]),
                 'ranks': {str(t): int(np.sum(eig > t*eig[-1])) for t in (1e-12, 1e-10, 1e-8)}}


def convergence(earlier, later):
    findings = []
    passed = True
    for name, aa, bb in [('band1', earlier[0], later[0]), ('band2', earlier[1], later[1]),
                          ('sum', earlier[0]+earlier[1], later[0]+later[1])]:
        diff = bb-aa
        norms = np.sqrt(np.diag(bb))
        if np.any(norms <= 0):
            findings.append({'matrix': name, 'status': 'UNRESOLVED_ZERO_DIAGONAL'}); passed = False; continue
        normalized = abs(diff) / np.outer(norms, norms)
        for r in range(3):
            sl = slice(5*r, 5*r+5)
            old = aa[sl,sl]; new = bb[sl,sl]; delta = diff[sl,sl]
            eig, vec = np.linalg.eigh(new)
            old_eig = np.linalg.eigvalsh(old)
            support = eig > 1e-10 * eig[-1]
            ranks = {str(t): int(np.sum(eig > t*eig[-1])) for t in (1e-12, 1e-10, 1e-8)}
            old_ranks = {str(t): int(np.sum(old_eig > t*old_eig[-1])) for t in (1e-12, 1e-10, 1e-8)}
            if len(set(ranks.values())) != 1 or ranks != old_ranks or not np.any(support):
                passed = False
                findings.append({'matrix': name, 'radius': r, 'status':'NUMERICAL_SUPPORT_UNCERTAIN',
                                 'earlier_ranks': old_ranks, 'later_ranks': ranks})
                continue
            root = (vec[:,support] / np.sqrt(eig[support])) @ vec[:,support].T
            whitened = float(np.linalg.norm(root @ delta @ root, 2))
            fro = float(np.linalg.norm(delta) / np.linalg.norm(new))
            entry = float(np.max(normalized[sl,sl]))
            ok = entry <= .005 and fro <= .003 and whitened <= .02
            passed &= ok
            findings.append({'matrix':name, 'radius':r, 'max_normalized_entry':entry,
                             'relative_frobenius':fro, 'whitened_spectral':whitened, 'ranks':ranks, 'pass':bool(ok)})
        for r in range(3):
            for s in range(r+1,3):
                entry = float(np.max(normalized[5*r:5*r+5, 5*s:5*s+5]))
                ok = entry <= .005
                passed &= ok
                findings.append({'matrix':name, 'cross_radii':[r,s], 'max_normalized_entry':entry, 'pass':bool(ok)})
    return bool(passed), findings


def pair_kernel(k, x, n):
    # Independent O(N^2) formula; use only on the <=12-row fixture.
    sep = x[:,None,:]-x[None,:,:]
    radius = np.linalg.norm(sep, axis=2)
    mu = n @ n.T
    z = k*radius
    j2 = spherical_jn(2,z)
    shat = np.divide(sep, radius[:,:,None], out=np.zeros_like(sep), where=radius[:,:,None]>0)
    ni = np.einsum('ic,ijc->ij',n,shat)
    nj = np.einsum('jc,ijc->ij',n,shat)
    return (spherical_jn(0,z)+j2)*mu/3 - j2*ni*nj
