"""R3 N1--N29: restricted LRS Bianchi-I dust/photon/Lambda experiment.

Units c=H_i=1 and 8*pi*G/(3*c**2)=1. This is a restricted history,
not a native low-ell solver or a product observation law. Review87 moments
and four-vector/Jacobi mechanics are adapted to the coupled physical stress.
"""
from dataclasses import dataclass
from functools import lru_cache
import ast
import hashlib
import tarfile
import numpy as np
from scipy.integrate import solve_ivp
from .r7_benchmark_provider import REVIEW87_MEMBERS

ETA = np.diag([-1., 1., 1., 1.])


def read_donors(archive):
    """Read only the three pinned members; execute the isolated NumPy donor.

    No license file exists in the supplied archive: retain that limitation,
    and do not vendor or claim a third-party redistribution license.
    """
    records = {}; sources = {}
    with tarfile.open(archive) as t:
        for name, expected in REVIEW87_MEMBERS.items():
            member = next(m for m in t if m.name.removeprefix('./') == name)
            data = t.extractfile(member).read()
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected:
                raise ValueError(f'immutable donor mismatch: {name}')
            records[name] = actual; sources[name] = data.decode()
    fs = {}; exec(compile(sources['bianchi/matter/freestream.py'], str(archive)+':freestream', 'exec'), fs)
    tree = ast.parse(sources['bianchi/rays/optical.py'])
    screen = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'screen_basis'], type_ignores=[])
    optics = {'np': np}; exec(compile(screen, str(archive)+':screen_basis', 'exec'), optics)
    return {'members': records, 'license': 'NOT_DECLARED_IN_SUPPLIED_ARCHIVE',
            'moments': fs['moments'], 'bose': fs['f_bose_einstein'],
            'screen_basis': optics['screen_basis']}


@lru_cache(maxsize=8)
def angular_grid(order):
    if order not in (32, 64, 128):
        raise ValueError('registered angular orders: 32, 64, 128')
    u, w = np.polynomial.legendre.leggauss(order)
    return u, w/2


@dataclass(frozen=True)
class Initial:
    kappa: float = 0.
    zeta: float = 0.
    dust: float = .3
    photons: float = .1
    vacuum: float = .6

    def __post_init__(self):
        vals = [self.kappa, self.zeta, self.dust, self.photons, self.vacuum]
        if not np.isfinite(vals).all() or abs(self.zeta) >= 1 or min(vals[2:]) < 0 or not np.isclose(sum(vals[2:]), 1., rtol=0, atol=1e-14):
            raise ValueError('finite positive normalized densities and |zeta|<1 required')

    @property
    def energies(self):
        f = 1-self.zeta**2
        return self.dust*f, self.photons*f, self.vacuum*f


def stress(a, b, initial, order=64):
    if a <= 0 or not np.isfinite([a, b]).all():
        raise ValueError('positive finite scale factor required')
    ed_i, eg_i, vacuum = initial.energies
    scales = a*np.exp(np.array([-b, -b, 2*b]))
    gamma = np.sqrt(1+(initial.kappa/scales[2])**2)
    beta = initial.kappa/np.sqrt(scales[2]**2+initial.kappa**2)
    ed = ed_i*gamma/(np.sqrt(1+initial.kappa**2)*a**3)
    pdz = ed*beta**2
    u, w = angular_grid(order); ap, az = 1/scales[0], 1/scales[2]
    r = np.sqrt(ap**2*(1-u*u)+az**2*u*u)
    eg = eg_i/a**3*np.dot(w, r)
    pgz = eg_i/a**3*np.dot(w, az**2*u*u/r)
    pgp = eg_i/a**3*np.dot(w, ap**2*(1-u*u)/(2*r))
    return dict(scales=scales, gamma=gamma, beta=beta, dust=ed,
                photons=eg, energy=ed+eg, perpendicular=pgp,
                parallel=pdz+pgz, photon_parallel=pgz, photon_perpendicular=pgp,
                vacuum=vacuum)


def rhs(t, y, initial, order=64, pi_scale=1., rapidity_mutant=False):
    a, b, s, h, chi = y; m = stress(a, b, initial, order)
    pbar = (2*m['perpendicular']+m['parallel'])/3
    hd = -1.5*(m['energy']+pbar)-3*s*s
    sd = -3*h*s+pi_scale*(m['parallel']-m['perpendicular'])
    cd = -(h+2*s)*(np.sinh(chi)*np.cosh(chi) if rapidity_mutant else np.tanh(chi))
    return np.array([a*h, s, sd, hd, cd])


@dataclass
class History:
    initial: Initial
    order: int
    tolerance: float
    solution: object
    pi_scale: float = 1.

    @property
    def end(self):
        return float(self.solution.t[-1])

    def at(self, t):
        if t < -1e-8 or t > self.end+1e-8:
            raise ValueError('outside the integrated history')
        y = self.solution.sol(np.clip(t, 0., self.end))
        d = rhs(t, y, self.initial, self.order, self.pi_scale)
        m = stress(y[0], y[1], self.initial, self.order)
        hi = y[3]+np.array([-y[2], -y[2], 2*y[2]])
        hid = d[3]+np.array([-d[2], -d[2], 2*d[2]])
        return y, m, hi, hid


def integrate(initial=Initial(), order=64, tolerance=1e-10, pi_scale=1., rapidity_mutant=False):
    if tolerance not in (1e-6, 1e-8, 1e-10):
        raise ValueError('registered integration tolerances only')
    def end(t, y): return y[0]-2
    end.terminal = True; end.direction = 1
    sol = solve_ivp(lambda t, y: rhs(t, y, initial, order, pi_scale, rapidity_mutant),
                    (0., 4.), [1., 0., initial.zeta, 1., np.arcsinh(initial.kappa)],
                    rtol=tolerance, atol=tolerance*.01, method='DOP853', dense_output=True, events=end)
    if not sol.success or not len(sol.t_events[0]):
        raise RuntimeError('history did not reach a=2: '+sol.message)
    return History(initial, order, tolerance, sol, pi_scale)


def residuals(history, samples=101):
    records = []
    for t in np.linspace(0, history.end, samples):
        y, m, hi, hid = history.at(t); a, b, s, h, chi = y
        # Independent metric Einstein tensor; not the Hamiltonian RHS itself.
        g00 = hi[0]*hi[1]+hi[0]*hi[2]+hi[1]*hi[2]
        gii = np.array([-(hid[j]+hid[k]+hi[j]**2+hi[k]**2+hi[j]*hi[k])
                       for j, k in ((1, 2), (0, 2), (0, 1))])
        target = 3*np.array([m['perpendicular'], m['perpendicular'], m['parallel']])-3*m['vacuum']
        einstein = np.max(np.abs(gii-target))
        eps = 1e-5
        mp = stress(a*np.exp(h*eps), b+s*eps, history.initial, history.order)
        mm = stress(a*np.exp(-h*eps), b-s*eps, history.initial, history.order)
        egdot = (mp['photons']-mm['photons'])/(2*eps)
        eddot = (mp['dust']-mm['dust'])/(2*eps)
        photon = egdot+3*h*m['photons']+2*hi[0]*m['photon_perpendicular']+hi[2]*m['photon_parallel']
        dust = eddot+3*h*m['dust']+hi[2]*(m['parallel']-m['photon_parallel'])
        records.append([abs(g00-3*(m['energy']+m['vacuum'])), einstein,
                        abs(m['scales'][2]*np.sinh(chi)-history.initial.kappa),
                        abs(2*m['photon_perpendicular']+m['photon_parallel']-m['photons']),
                        abs(photon), abs(dust)])
    return dict(zip(('hamiltonian', 'einstein_spatial', 'killing_rapidity',
                     'photon_trace', 'photon_conservation', 'dust_conservation'), np.max(records, axis=0)))


def temperature(directions, a, b, beta=(0., 0., 0.), ti=1.):
    n = np.asarray(directions, float); v = np.asarray(beta, float); v2 = v@v
    if n.shape[-1] != 3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n, axis=-1), 1., rtol=0, atol=1e-12) or not 0 <= v2 < 1:
        raise ValueError('unit directions and subluminal observer required')
    g = 1/np.sqrt(1-v2); bo = n@v; doppler = 1/(g*(1-bo))
    nn = n if v2 == 0 else (n+(((g-1)*bo/v2-g)[..., None])*v)/(g*(1-bo)[..., None])
    return ti/a*doppler/np.sqrt(np.exp(-2*b)*(1-nn[..., 2]**2)+np.exp(4*b)*nn[..., 2]**2)


def boost_matrix(beta):
    v = np.asarray(beta, float); v2 = v@v
    if v.shape != (3,) or not np.isfinite(v).all() or not v2 < 1:
        raise ValueError('subluminal finite boost required')
    g = 1/np.sqrt(1-v2); b = np.eye(4); b[0, 0] = g
    b[0, 1:] = b[1:, 0] = g*v
    if v2: b[1:, 1:] += (g-1)*np.outer(v, v)/v2
    return b


def screen_basis(n):
    n = np.asarray(n, float)
    if n.shape != (3,) or not np.isclose(n@n, 1., rtol=0, atol=1e-12):
        raise ValueError('unit ray direction required')
    tmp = np.eye(3)[int(abs(n[0]) > .9)]
    e = np.cross(n, tmp); e /= np.linalg.norm(e)
    return np.array([[0., *e], [0., *np.cross(n, e)]])


def optical_rhs(history, affine, state):
    t = state[0]; k = state[4:8]; sc = state[8:16].reshape(2, 4)
    _, m, hi, hid = history.at(t); scales = m['scales']
    gamma = np.zeros((4, 4, 4))
    for i in range(3):
        gamma[0, i+1, i+1] = scales[i]**2*hi[i]
        gamma[i+1, 0, i+1] = gamma[i+1, i+1, 0] = hi[i]
    kd = -np.einsum('abc,b,c->a', gamma, k, k)
    scd = -np.einsum('abc,Bb,c->Ba', gamma, sc, k)
    tetrad = np.r_[1., scales]; kh = k*tetrad; sh = sc*tetrad
    tidal = np.zeros((2, 2))
    for a in range(4):
        for b in range(a+1, 4):
            curvature = -(hid[b-1]+hi[b-1]**2) if a == 0 else hi[a-1]*hi[b-1]
            wedge = sh[:, a]*kh[b]-sh[:, b]*kh[a]
            tidal -= curvature*np.outer(wedge, wedge)
    d = state[16:20].reshape(2, 2); p = state[20:24].reshape(2, 2)
    return np.r_[k, kd, scd.ravel(), p.ravel(), (tidal@d).ravel()]


def _trace(history, initial_state, target, tolerance):
    direction = np.sign(target-initial_state[0])
    def event(lam, y): return y[0]-target
    event.terminal = True; event.direction = direction
    # Time is an independent integration variable. Integrate the same affine
    # equations divided by k^0; this avoids dense-history extrapolation at events.
    def ft(t, y):
        full = np.r_[t, y]
        return optical_rhs(history, 0., full)[1:]/full[4]
    sol = solve_ivp(ft, (initial_state[0], target), initial_state[1:], method='DOP853',
                    rtol=tolerance, atol=tolerance*.01, dense_output=True)
    if not sol.success: raise RuntimeError(sol.message)
    ys = np.vstack([sol.t, sol.y]); last = ys[:, -1]
    checks = {'null': 0., 'screen_null': 0., 'screen_gram': 0., 'killing': 0., 'wronskian': 0.}
    _, m0, _, _ = history.at(initial_state[0]); momenta = initial_state[5:8]*m0['scales']**2
    for y in ys.T:
        _, m, _, _ = history.at(y[0]); tr = np.r_[1., m['scales']]
        k = y[4:8]*tr; sc = y[8:16].reshape(2, 4)*tr; en = abs(k[0])
        d = y[16:20].reshape(2, 2); p = y[20:24].reshape(2, 2)
        checks['null'] = max(checks['null'], abs(k@ETA@k)/en**2)
        checks['screen_null'] = max(checks['screen_null'], np.max(np.abs(sc@ETA@k))/en)
        checks['screen_gram'] = max(checks['screen_gram'], np.max(np.abs(sc@ETA@sc.T-np.eye(2))))
        checks['killing'] = max(checks['killing'], np.max(np.abs(y[5:8]*m['scales']**2-momenta)))
        checks['wronskian'] = max(checks['wronskian'], np.max(np.abs(p.T@d-d.T@p)))
    return last, checks, len(sol.t)


def trace_distance(history, direction=(0., 0., 1.), beta_observer=(0., 0., 0.), tolerance=1e-10, reverse=True):
    n = np.asarray(direction, float); sc0 = screen_basis(n); boost = boost_matrix(beta_observer)
    _, mo, _, _ = history.at(history.end); tr_o = np.r_[1., mo['scales']]
    uo = boost[:, 0]; ko = boost@np.r_[-1., n]
    state = np.r_[history.end, np.zeros(3), ko/tr_o,
                  ((boost@sc0.T).T/tr_o).ravel(), np.zeros(4), np.eye(2).ravel()]
    last, checks, steps = _trace(history, state, 0., tolerance)
    _, ms, _, _ = history.at(0.); tr_s = np.r_[1., ms['scales']]
    us = boost_matrix((0., 0., ms['beta']))[:, 0]
    ks = last[4:8]*tr_s; es = us@ETA@ks
    if es <= 0: raise ValueError('nonpositive source energy')
    det = np.linalg.det(last[16:20].reshape(2, 2))
    if det <= 0: raise ValueError('conjugate-point/degenerate endpoint is outside this channel')
    da = np.sqrt(det)
    out = dict(redshift=es-1, angular_distance=da, luminosity_distance=es**2*da,
               invariants=checks, forward_steps=steps, scope='RESTRICTED_R3_BENCHMARK',
               jet_status='INPUT_UNAVAILABLE')
    if reverse:
        scr = last[8:16].reshape(2, 4)*tr_s
        scr -= np.outer(scr@ETA@us/es, ks)
        reverse_state = np.r_[0., last[1:4], -last[4:8]/es,
                             (scr/tr_s).ravel(), np.zeros(4), np.eye(2).ravel()]
        back, backchecks, backsteps = _trace(history, reverse_state, history.end, tolerance)
        da_back = np.sqrt(abs(np.linalg.det(back[16:20].reshape(2, 2))))
        out.update(reverse_steps=backsteps, reverse_invariants=backchecks,
                   reverse_angular_distance=da_back,
                   reciprocity_residual=abs(da_back-es*da),
                   return_position_residual=float(np.max(np.abs(back[1:4]))),
                   return_energy_residual=abs(abs(uo@ETA@(back[4:8]*tr_o))-1/es))
    return out
