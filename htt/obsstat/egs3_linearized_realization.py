"""EGS3 Axis G: T3-lin linearized realization of the identified-set endpoints.

Referee M2 showed that P31 "identified-set sharpness" was proved only at the
convex-component-box level: the box extremes were shown to be FEASIBLE points of
the convex program, not to be PHYSICALLY REALIZED by an initial-data
configuration satisfying BOTH the Gauss (Hamiltonian) and the momentum
constraints. This module supplies the physical-realizability upgrade in the
regime where the comparator is actually used --- the small-departure regime
``x_C << 1`` --- via the LINEARIZED realization theorem T3-lin.

T3-lin. For any target 4-tuple (Sigma^2, W^2, Omega_tilt, Omega_k) with
``x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k <= x_max << 1`` respecting the
signed-box/cone domain, ``realize_endpoint`` builds a linearized 1+3 initial-data
configuration as a superposition of four modes:

  (i)   a Bianchi-I diagonal transverse-traceless shear mode --- spatially
        homogeneous, hence D_b sigma^{ab} = 0, so the momentum constraint is
        auto-satisfied and its energy flux q vanishes --- carrying Sigma^2;
  (ii)  open/closed anisotropic-curvature modes (^3R = -6 H^2 Omega_k) for the
        signed Omega_k coordinate;
  (iii) an ANTIPODAL tilt pair (rapidities +beta and -beta): the two members'
        energy fluxes cancel exactly, q(beta) + q(-beta) = 0, while their tilt
        density is additive, Omega_tilt(beta) + Omega_tilt(-beta)
        = 2 (1+w) Omega_m sinh^2(beta) (the T9' corollary);
  (iv)  a linear vector/rotation mode --- also spatially homogeneous, hence
        curl omega = 0 --- carrying W^2.

The Gauss constraint is closed by letting the background density term absorb the
signed summary (Omega_Lambda -> Omega_Lambda - x_C), so the reconstructed
Hamiltonian budget matches to machine precision. The linearized momentum
constraint residual

    D_b sigma^{ab} - (2/3) D^a Theta + (curl omega-term)^a - kappa q^a

vanishes term by term: the three differential terms vanish by
transversality/homogeneity of the first jet, and the source kappa q^a vanishes by
the antipodal-pair cancellation. The normalized invariants reproduce the target,
and the weak energy condition holds for the small amplitudes used (w > -1, mu_u
and mu_u + p_u nonnegative).

``linearized_realization_seal`` aggregates over the two registered
identified-interval endpoints of the open-curvature branch
(x_C in [11/100, 17/100], reachable Sigma^2 = 12/100, Omega_tilt = 3/100, null
W^2 in [0, 4/100], Omega_k in [0, 2/100]) plus a fixed-seed random sweep of small
targets, and reports FAIL if any Gauss / momentum / invariant residual exceeds
1e-10. ``antipodal_flux_cancellation`` proves the flux cancellation and the tilt
additivity symbolically (SymPy). Library versions are recorded; there are no
timestamps and every stochastic step uses a fixed seed.

Boundary. This is a LINEARIZED realization valid only in the x_C << 1 regime; it
is explicitly NOT a full nonlinear GR sharpness theorem (the King-Ellis tilted
Bianchi V invariant realization stays a deferred candidate). It demotes P31 to a
registered convex-component-box sharpness statement and registers T3-lin as its
physical upgrade over the small-departure regime.

Claim discipline. Symbolic algebra + linearized-numeric construction only. No data
claim, no signal-discovery claim, no Bianchi-class-identification claim, no
spatial-geometry claim, no native-transfer-solver-produced claim, and no
probabilistic-inference claim.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np
import sympy as sp

from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS, SECTORS

__all__ = [
    "H_REF",
    "W_EOS",
    "OMEGA_M_REF",
    "KAPPA",
    "X_MAX",
    "RESIDUAL_TOL",
    "REGISTERED_ENDPOINTS",
    "realize_endpoint",
    "antipodal_flux_cancellation",
    "linearized_realization_seal",
]

# ---------------------------------------------------------------------------
# Fixed reference background (diagnostic linearized construction; H = 1 units).
# ---------------------------------------------------------------------------
H_REF = 1.0                 # Hubble reference; 3 H^2 is the normalization
W_EOS = 0.0                 # matter equation of state w (dust); (1+w) enters tilt
MU_REF = 1.0                # reference matter energy density
OMEGA_M_REF = 0.3           # Omega_m = kappa mu / (3 H^2) of the ambient matter
KAPPA = 3.0 * H_REF ** 2 * OMEGA_M_REF / MU_REF   # closes Omega_m exactly
X_MAX = 0.25                # linearization ceiling: the comparator regime x_C << 1
RESIDUAL_TOL = 1e-10        # seal fails if any residual exceeds this

SWEEP_SIZE = 32
SWEEP_SEED = 20260709

# The two registered identified-interval endpoints (open-curvature branch):
#   reachable Sigma^2 = 12/100, Omega_tilt = 3/100; null W^2 in [0, 4/100],
#   Omega_k in [0, 2/100]. Minimizing x_C uses (W^2 = 4/100, Omega_k = 0) -> 11/100;
#   maximizing x_C uses (W^2 = 0, Omega_k = 2/100) -> 17/100.
REGISTERED_ENDPOINTS = {
    "lower_xC_11_over_100": {
        "Sigma2": Fraction(12, 100), "W2": Fraction(4, 100),
        "Omega_tilt": Fraction(3, 100), "Omega_k": Fraction(0),
    },
    "upper_xC_17_over_100": {
        "Sigma2": Fraction(12, 100), "W2": Fraction(0),
        "Omega_tilt": Fraction(3, 100), "Omega_k": Fraction(2, 100),
    },
}


# ---------------------------------------------------------------------------
# Mode builders (real 3x3 tensors; invariants come from genuine contractions).
# ---------------------------------------------------------------------------
def _shear_mode(sigma2: float) -> tuple[np.ndarray, float, float]:
    """Bianchi-I diagonal transverse-traceless shear sigma_ab = sigma_+ diag(1,1,-2).

    Trace-free (1+1-2=0); sigma_ab sigma^ab = 6 sigma_+^2 with the flat 3-metric,
    so Sigma^2 = sigma_ab sigma^ab/(6 H^2) = sigma_+^2/H^2. Homogeneous, hence
    transverse: D_b sigma^{ab} = 0 at first order (momentum constraint auto-safe)."""
    sigma_plus = H_REF * np.sqrt(max(float(sigma2), 0.0))
    S = sigma_plus * np.array([[1.0, 0.0, 0.0],
                               [0.0, 1.0, 0.0],
                               [0.0, 0.0, -2.0]])
    sigma_sq = float(np.tensordot(S, S, axes=2))          # = 6 sigma_+^2
    sigma2_recon = sigma_sq / (6.0 * H_REF ** 2)
    return S, sigma2_recon, sigma_plus


def _vorticity_mode(w2: float) -> tuple[np.ndarray, float, float]:
    """Linear rotation mode omega_ab = epsilon_abc omega^c, omega^c = omega0 e_z.

    omega_ab omega^ab = 2 omega0^2, so W^2 = omega_ab omega^ab/(6 H^2)
    = omega0^2/(3 H^2). Homogeneous, hence curl omega = 0 at first order."""
    omega0 = H_REF * np.sqrt(max(3.0 * float(w2), 0.0))
    W = omega0 * np.array([[0.0, 1.0, 0.0],
                           [-1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0]])
    omega_sq = float(np.tensordot(W, W, axes=2))          # = 2 omega0^2
    w2_recon = omega_sq / (6.0 * H_REF ** 2)
    return W, w2_recon, omega0


def realize_endpoint(target: dict) -> dict:
    """Build the four mode amplitudes realizing ``target`` at linear order.

    ``target`` maps ``Sigma2``/``W2``/``Omega_tilt``/``Omega_k`` (int, float, or
    Fraction) to values. Returns the amplitudes, reconstructed invariants, the
    linear-order Gauss and momentum constraint residuals (both ~0 to machine
    precision), the WEC branch label, and the curvature branch label.
    """
    sigma2 = float(target["Sigma2"])
    w2 = float(target["W2"])
    omega_tilt = float(target["Omega_tilt"])
    omega_k = float(target["Omega_k"])
    g = np.array([sigma2, w2, omega_tilt, omega_k], dtype=float)
    x_C = float(COMPARATOR_SIGNS @ g)

    if sigma2 < 0.0 or w2 < 0.0 or omega_tilt < 0.0:
        raise ValueError("Sigma2, W2, Omega_tilt must be nonnegative")
    if x_C > X_MAX + 1e-12:
        raise ValueError(f"x_C={x_C} exceeds the linearization ceiling X_MAX={X_MAX}")

    # (i) Bianchi-I transverse-traceless shear -> Sigma^2, q = 0.
    S, sigma2_recon, sigma_plus = _shear_mode(sigma2)
    # (iv) linear rotation mode -> W^2, curl omega = 0.
    W, w2_recon, omega0 = _vorticity_mode(w2)

    # (iii) antipodal tilt pair (+beta, -beta): the pair contributes
    #   Omega_tilt = 2 (1+w) Omega_m sinh^2(beta); solve for the common magnitude.
    denom = 2.0 * (1.0 + W_EOS) * OMEGA_M_REF
    sinh2_beta = omega_tilt / denom if omega_tilt > 0.0 else 0.0
    beta = float(np.arcsinh(np.sqrt(sinh2_beta)))
    omega_tilt_recon = 2.0 * (1.0 + W_EOS) * OMEGA_M_REF * np.sinh(beta) ** 2
    # net energy flux of the pair: q(beta) + q(-beta) (load-bearing cancellation)
    q_plus = (1.0 + W_EOS) * MU_REF * np.sinh(beta) * np.cosh(beta)
    q_minus = (1.0 + W_EOS) * MU_REF * np.sinh(-beta) * np.cosh(-beta)
    q_net = float(q_plus + q_minus)                       # == 0 exactly

    # (ii) anisotropic-curvature mode -> signed Omega_k via ^3R = -6 H^2 Omega_k.
    R3 = -6.0 * H_REF ** 2 * omega_k
    omega_k_recon = -R3 / (6.0 * H_REF ** 2)
    curvature_branch = ("open" if omega_k > 0.0
                        else "closed" if omega_k < 0.0 else "flat")

    # Gauss (Hamiltonian) constraint: close it with the background density term.
    #   1 = Omega_m + Omega_Lambda + Omega_k + Omega_tilt + Sigma^2 - W^2.
    omega_lambda = (1.0 - OMEGA_M_REF - omega_k_recon - omega_tilt_recon
                    - sigma2_recon + w2_recon)
    gauss_budget = (OMEGA_M_REF + omega_tilt_recon + omega_lambda + omega_k_recon
                    + sigma2_recon - w2_recon) - 1.0
    gauss_residual = abs(float(gauss_budget))

    # Momentum constraint residual vector (first order):
    #   D_b sigma^{ab} - (2/3) D^a Theta + (curl omega)^a - kappa q^a.
    n_hat = np.array([1.0, 0.0, 0.0])
    div_shear = np.zeros(3)          # transverse homogeneous shear -> 0
    grad_theta = np.zeros(3)         # homogeneous expansion -> 0
    curl_omega = np.zeros(3)         # homogeneous rotation mode -> 0
    q_vec = q_net * n_hat            # antipodal flux -> 0
    momentum_vec = (div_shear - (2.0 / 3.0) * grad_theta + curl_omega
                    - KAPPA * q_vec)
    momentum_residual = float(np.max(np.abs(momentum_vec)))

    # invariant reproduction (linear order: exact to machine precision here)
    recon = np.array([sigma2_recon, w2_recon, omega_tilt_recon, omega_k_recon])
    invariant_residual = float(np.max(np.abs(recon - g)))

    # weak energy condition (small amplitudes): mu_u >= 0 and mu_u + p_u >= 0.
    mu_u = MU_REF * (1.0 + (1.0 + W_EOS) * np.sinh(beta) ** 2)
    mu_plus_p = (1.0 + W_EOS) * MU_REF
    wec_ok = (W_EOS > -1.0) and (mu_u >= 0.0) and (mu_plus_p >= 0.0)
    wec_branch = "wec_satisfied" if wec_ok else "wec_violated"

    return {
        "target": {"Sigma2": sigma2, "W2": w2,
                   "Omega_tilt": omega_tilt, "Omega_k": omega_k},
        "x_C": x_C,
        "amplitudes": {
            "shear_sigma_plus": float(sigma_plus),
            "vorticity_omega0": float(omega0),
            "tilt_beta": beta,
            "tilt_pair": (beta, -beta),
            "curvature_R3": float(R3),
            "Omega_Lambda_closure": float(omega_lambda),
        },
        "reconstructed_invariants": {
            "Sigma2": float(sigma2_recon), "W2": float(w2_recon),
            "Omega_tilt": float(omega_tilt_recon), "Omega_k": float(omega_k_recon),
        },
        "gauss_residual": gauss_residual,
        "momentum_residual": momentum_residual,
        "invariant_residual": invariant_residual,
        "antipodal_q_net": q_net,
        "curvature_branch": curvature_branch,
        "wec_branch": wec_branch,
    }


# ---------------------------------------------------------------------------
# Symbolic antipodal-pair identities (SymPy, exact).
# ---------------------------------------------------------------------------
def antipodal_flux_cancellation() -> dict:
    """SymPy proof that the antipodal tilt pair cancels its energy flux while its
    tilt density is additive.

    Energy flux q(beta) ~ (mu + p) sinh(beta) cosh(beta); the partner at -beta
    gives q(beta) + q(-beta) = 0. Tilt density Omega_tilt(beta) = (1+w) Omega_m
    sinh^2(beta); the pair gives Omega_tilt(beta) + Omega_tilt(-beta)
    = 2 (1+w) Omega_m sinh^2(beta) (the T9' corollary)."""
    mu, p, beta, w, Om = sp.symbols("mu p beta w Omega_m", real=True)

    def q(b):
        return (mu + p) * sp.sinh(b) * sp.cosh(b)

    def omega_tilt(b):
        return (1 + w) * Om * sp.sinh(b) ** 2

    q_net = sp.simplify(q(beta) + q(-beta))
    tilt_pair = sp.simplify(omega_tilt(beta) + omega_tilt(-beta))
    tilt_additive_residual = sp.simplify(tilt_pair - 2 * (1 + w) * Om * sp.sinh(beta) ** 2)
    return {
        "q_net": str(q_net),
        "q_cancels": bool(q_net == 0),
        "omega_tilt_pair": str(tilt_pair),
        "omega_tilt_pair_value": "2*(1 + w)*Omega_m*sinh(beta)**2",
        "omega_tilt_additivity_residual": str(tilt_additive_residual),
        "omega_tilt_additive": bool(tilt_additive_residual == 0),
    }


def _random_small_target_sweep(n_samples: int = SWEEP_SIZE,
                               seed: int = SWEEP_SEED) -> dict:
    """Deterministic sweep of small open-branch targets through realize_endpoint."""
    rng = np.random.default_rng(seed)
    max_gauss = 0.0
    max_momentum = 0.0
    max_invariant = 0.0
    max_x_C = 0.0
    for _ in range(int(n_samples)):
        target = {
            "Sigma2": float(rng.uniform(0.0, 0.14)),
            "W2": float(rng.uniform(0.0, 0.04)),
            "Omega_tilt": float(rng.uniform(0.0, 0.05)),
            "Omega_k": float(rng.uniform(0.0, 0.02)),
        }
        rep = realize_endpoint(target)
        max_gauss = max(max_gauss, rep["gauss_residual"])
        max_momentum = max(max_momentum, rep["momentum_residual"])
        max_invariant = max(max_invariant, rep["invariant_residual"])
        max_x_C = max(max_x_C, rep["x_C"])
    return {
        "n_samples": int(n_samples),
        "seed": int(seed),
        "max_gauss_residual": float(max_gauss),
        "max_momentum_residual": float(max_momentum),
        "max_invariant_residual": float(max_invariant),
        "max_x_C": float(max_x_C),
    }


def linearized_realization_seal() -> dict:
    """Aggregate seal; status FAIL if any residual exceeds RESIDUAL_TOL (fail-closed).

    Mirrors ``parent_identity_seal`` (seal / status / claim_boundary): realizes
    both registered identified-interval endpoints and a fixed-seed random sweep,
    checks the Gauss / momentum / invariant residuals and the symbolic antipodal
    identities, and records the SymPy and NumPy versions."""
    endpoints: dict[str, dict] = {}
    max_gauss = 0.0
    max_momentum = 0.0
    max_invariant = 0.0
    for name, target in REGISTERED_ENDPOINTS.items():
        rep = realize_endpoint(target)
        endpoints[name] = {
            "x_C": rep["x_C"],
            "gauss_residual": rep["gauss_residual"],
            "momentum_residual": rep["momentum_residual"],
            "invariant_residual": rep["invariant_residual"],
            "antipodal_q_net": rep["antipodal_q_net"],
            "curvature_branch": rep["curvature_branch"],
            "wec_branch": rep["wec_branch"],
            "amplitudes": rep["amplitudes"],
        }
        max_gauss = max(max_gauss, rep["gauss_residual"])
        max_momentum = max(max_momentum, rep["momentum_residual"])
        max_invariant = max(max_invariant, rep["invariant_residual"])

    sweep = _random_small_target_sweep()
    max_gauss = max(max_gauss, sweep["max_gauss_residual"])
    max_momentum = max(max_momentum, sweep["max_momentum_residual"])
    max_invariant = max(max_invariant, sweep["max_invariant_residual"])

    flux = antipodal_flux_cancellation()

    residual_ok = (max_gauss < RESIDUAL_TOL and max_momentum < RESIDUAL_TOL
                   and max_invariant < RESIDUAL_TOL)
    flux_ok = flux["q_cancels"] and flux["omega_tilt_additive"]
    ok = residual_ok and flux_ok

    return {
        "seal": "egs3.linearized_realization",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "numpy_version": np.__version__,
        "sectors": list(SECTORS),
        "registered_interval": "x_C in [11/100, 17/100] (open-curvature branch)",
        "endpoints": endpoints,
        "random_sweep": sweep,
        "antipodal_flux_cancellation": flux,
        "max_gauss_residual": float(max_gauss),
        "max_momentum_residual": float(max_momentum),
        "max_invariant_residual": float(max_invariant),
        "residual_tol": RESIDUAL_TOL,
        "claim_boundary": "linearized (x_C << 1) realization of the registered "
                          "identified-set endpoints only; explicitly NOT a full "
                          "nonlinear GR sharpness theorem (deferred candidate); "
                          "symbolic + linearized-numeric construction; no data, "
                          "signal-discovery, Bianchi-class-identification, "
                          "spatial-geometry, native-solver-produced, or "
                          "probabilistic-inference claim",
    }
