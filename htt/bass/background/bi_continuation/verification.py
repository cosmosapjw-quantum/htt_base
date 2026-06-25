"""Independent PR07-003 verification helpers for the restricted Bianchi-I branch.

These checks are deliberately *independent* of the production RHS path: each
conservation residual is formed by differentiating the projected normal-frame
quantities (mu, q) via the chain rule and comparing against the analytic
conservation laws, rather than calling ``rhs`` and comparing it with itself.
The integrator cross-check drives SciPy DOP853/Radau against the exact dust
oracle with subluminal / denominator / expanding event guards.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from .moments import SpeciesPrimitive, project_species, total_projection
from .dynamics import BIState, rhs, constraint_residuals, shear_rhs_from_physical


def _stf(t: np.ndarray) -> np.ndarray:
    x = np.asarray(t, dtype=float).reshape(3, 3)
    s = 0.5 * (x + x.T)
    return s - np.eye(3) * np.trace(s) / 3.0


def species_chain_rule_residual(H: float, sigma: np.ndarray, species: SpeciesPrimitive) -> dict[str, object]:
    """Check primitive RHS against projected energy/momentum conservation."""
    state = BIState(1.0, H, sigma, (species,))
    value = rhs(state)
    rho_dot = value.rho_dot[0]
    v_dot = value.velocity_dot[0]
    v = species.velocity
    v2 = float(v @ v)
    gamma2 = 1.0 / (1.0 - v2)
    A = (1.0 + species.w) * species.rho_hat * gamma2
    log_A_dot = rho_dot / species.rho_hat + 2.0 * gamma2 * float(v @ v_dot)
    mu_dot = A * log_A_dot - species.w * rho_dot
    q_dot = A * (log_A_dot * v + v_dot)
    p = project_species(species)
    expected_mu = -3.0 * H * (p.mu + p.pressure) - float(np.sum(_stf(sigma) * p.anisotropic_stress))
    expected_q = -4.0 * H * p.flux - _stf(sigma) @ p.flux
    return {
        'energy_residual': float(mu_dot - expected_mu),
        'momentum_residual': np.asarray(q_dot - expected_q, dtype=float),
    }


def random_species_audit(samples: int = 1000, seed: int = 20260625) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    max_energy = 0.0
    max_momentum = 0.0
    min_1_minus_wv2 = np.inf
    for i in range(samples):
        H = float(rng.uniform(0.25, 2.0))
        sigma = _stf(rng.normal(scale=0.08 * H, size=(3, 3)))
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        speed = float(rng.uniform(0.0, 0.92))
        w = float(rng.uniform(-0.2, 0.95))
        rho = float(np.exp(rng.uniform(-2.0, 1.0)))
        sp = SpeciesPrimitive(rho, w, speed * direction, f's{i}')
        min_1_minus_wv2 = min(min_1_minus_wv2, 1.0 - w * speed * speed)
        r = species_chain_rule_residual(H, sigma, sp)
        max_energy = max(max_energy, abs(r['energy_residual']))
        max_momentum = max(max_momentum, float(np.linalg.norm(r['momentum_residual'])))
    return {
        'samples': int(samples),
        'seed': int(seed),
        'max_energy_residual': float(max_energy),
        'max_momentum_residual': float(max_momentum),
        'minimum_1_minus_wv2': float(min_1_minus_wv2),
        'passed': bool(max_energy < 1e-10 and max_momentum < 1e-10),
    }


def constraint_transport_residual(state: BIState, kappa: float = 1.0, Lambda: float = 0.0) -> dict[str, object]:
    value = rhs(state, kappa=kappa, Lambda=Lambda)
    projection = total_projection(state.species)
    mu_dot = 0.0
    q_dot = np.zeros(3)
    for sp, rho_dot, v_dot in zip(state.species, value.rho_dot, value.velocity_dot):
        v = sp.velocity
        v2 = float(v @ v)
        gamma2 = 1.0 / (1.0 - v2)
        A = (1.0 + sp.w) * sp.rho_hat * gamma2
        log_A_dot = rho_dot / sp.rho_hat + 2.0 * gamma2 * float(v @ v_dot)
        mu_dot += A * log_A_dot - sp.w * rho_dot
        q_dot += A * (log_A_dot * v + v_dot)
    sigma = _stf(state.sigma)
    G = constraint_residuals(state, kappa=kappa, Lambda=Lambda)['gauss']
    Gdot = 6.0 * state.H * value.Hdot - float(np.sum(sigma * value.sigmadot)) - kappa * mu_dot
    codazzi_transport = q_dot + 4.0 * state.H * projection.flux + sigma @ projection.flux
    return {
        'gauss': float(G),
        'gauss_transport_residual': float(Gdot + 2.0 * state.H * G),
        'codazzi_transport_residual': np.asarray(codazzi_transport, dtype=float),
    }


def integrate_solve_ivp(
    state: BIState,
    times: np.ndarray,
    *,
    method: str = 'DOP853',
    kappa: float = 1.0,
    Lambda: float = 0.0,
    rtol: float = 1e-10,
    atol: float = 1e-12,
) -> list[BIState]:
    t = np.asarray(times, dtype=float)
    if state.H <= 0.0:
        raise ValueError('registered branch requires H>0')
    if np.any(np.diff(t) <= 0.0):
        raise ValueError('times must be strictly increasing')
    template = state

    def pack(s: BIState) -> np.ndarray:
        pieces = [np.array([s.a, s.H]), s.sigma.reshape(-1)]
        for sp in s.species:
            pieces += [np.array([sp.rho_hat]), sp.velocity]
        return np.concatenate(pieces)

    def unpack(y: np.ndarray) -> BIState:
        a, H = y[:2]
        sigma = y[2:11].reshape(3, 3)
        pos = 11
        species = []
        for old in template.species:
            rho = float(y[pos]); v = y[pos+1:pos+4]; pos += 4
            species.append(SpeciesPrimitive(rho, old.w, v, old.name))
        return BIState(float(a), float(H), sigma, tuple(species))

    def f(_time: float, y: np.ndarray) -> np.ndarray:
        v = rhs(unpack(y), kappa=kappa, Lambda=Lambda)
        pieces = [np.array([v.adot, v.Hdot]), v.sigmadot.reshape(-1)]
        for rd, vd in zip(v.rho_dot, v.velocity_dot):
            pieces += [np.array([rd]), vd]
        return np.concatenate(pieces)

    def subluminal(_time: float, y: np.ndarray) -> float:
        s = unpack(y)
        return min(1.0 - float(sp.velocity @ sp.velocity) for sp in s.species) - 1e-8
    subluminal.terminal = True
    subluminal.direction = -1.0

    def denominator(_time: float, y: np.ndarray) -> float:
        s = unpack(y)
        return min(1.0 - sp.w * float(sp.velocity @ sp.velocity) for sp in s.species) - 1e-8
    denominator.terminal = True
    denominator.direction = -1.0

    def expanding(_time: float, y: np.ndarray) -> float:
        return float(y[1]) - 1e-10
    expanding.terminal = True
    expanding.direction = -1.0

    sol = solve_ivp(f, (float(t[0]), float(t[-1])), pack(state), t_eval=t,
                    method=method, rtol=rtol, atol=atol,
                    events=[subluminal, denominator, expanding])
    if not sol.success or sol.y.shape[1] != t.size:
        raise RuntimeError(sol.message)
    return [unpack(sol.y[:, i]) for i in range(t.size)]
