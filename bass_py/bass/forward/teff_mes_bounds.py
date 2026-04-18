"""bass/forward/teff_mes_bounds.py — Two-layer T_eff-corrected MES bounds.

Migrated from legacy/bass/bass/forward/teff_mes_bounds.py (v8.3.0, C-12).

Two-layer decomposition of the nonlinear corrections to MES bounds:

    Layer 1 (dominant, O(β) ~ 10⁻³)
        Doppler boost modulation.  The observer peculiar velocity β
        generates ε₁ ≈ β and modulates higher multipoles via aberration
        + frequency shift.  Gives R_σ^{boost} = 1 + c₁·ε₁, c₁ ≈ 2.684.

    Layer 2 (subdominant, O(β²) ~ 10⁻⁶)
        Gaunt Θ⁴ nonlinearity.  The quartic T_eff composition generates
        nonlinear Legendre coefficients via C-14 Gaunt algebra.  The
        effective multipoles ε_ℓ^{Teff} = a_ℓ / 4 carry O(A², AQ, Q²)
        corrections, visible as a ε₁²-quadratic term in R_σ.

Combined correction: R_σ = R_σ^{boost} × R_σ^{Gaunt}.

C-09b (legacy derivation) finding: the empirical fit
R_σ = 1 + 2.684·ε₁ + 4.18·ε₁² is dominated by Layer 1 — the 2.684
coefficient encodes the aberration+modulation coupling, NOT the Gaunt
algebra.  The 4.18 quadratic coefficient in R_σ^{Gaunt} is the
next-to-leading ε₁² contribution from the a_2 = 4·A² term propagated
through the bound structure.

Cross-check scenarios ``VN04_SCENARIOS`` replicate the three legacy
reference points (S1/S2/S3) used to validate this closure to < 1%.
"""
from __future__ import annotations

from typing import Dict

from bass.forward.doppler_boost import DopplerBoostCorrection, analytical_c1
from bass.forward.teff_forward import theta4_coefficients  # noqa: F401

__all__ = [
    'TeffMESBounds',
    'VN04_SCENARIOS',
]


# ════════════════════════════════════════════════════════════════════
# VN-04 cross-check scenarios
# ════════════════════════════════════════════════════════════════════

VN04_SCENARIOS: Dict[str, Dict[str, float]] = {
    'S1': {
        'description': 'CF4 bulk flow (standard)',
        'eps1': 1.334e-3,
        'eps2': 1.233e-3,
        'eps3': 1.0e-4,
        'R_sigma_vn04': 1.0 + 2.684 * 1.334e-3,  # ≈ 1.00358
    },
    'S2': {
        'description': 'Strong tilt (hypothetical)',
        'eps1': 1.0e-2,
        'eps2': 1.0e-3,
        'eps3': 1.0e-4,
        'R_sigma_vn04': 1.0 + 2.684 * 1.0e-2,    # ≈ 1.02684
    },
    'S3': {
        'description': 'Weak tilt',
        'eps1': 1.0e-4,
        'eps2': 1.233e-3,
        'eps3': 1.0e-4,
        'R_sigma_vn04': 1.0 + 2.684 * 1.0e-4,    # ≈ 1.000268
    },
}


# ════════════════════════════════════════════════════════════════════
# Two-layer correction class
# ════════════════════════════════════════════════════════════════════

class TeffMESBounds:
    """Two-layer T_eff-corrected MES bound wrapper.

    Combines the O(β) Doppler boost (``DopplerBoostCorrection``) with
    the O(β²) Gaunt algebra from ``theta4_coefficients`` to give
    R_σ, R_ω, R_u̇ correction factors and the F-invariance breakdown
    ``filling_fraction_correction``.
    """

    #: Empirical ε₁² coefficient in R_σ^{Gaunt} from C-09b.
    C2_GAUNT: float = 4.18

    def __init__(self):
        self._boost = DopplerBoostCorrection()

    # ── Layer 1: Doppler boost ──────────────────────────────────────

    def R_sigma_boost(self, eps1: float) -> float:
        """Layer 1 Doppler correction: R_σ^{boost} = 1 + c₁·ε₁."""
        return self._boost.R_sigma_boost(eps1)

    # ── Layer 2: Gaunt algebra ──────────────────────────────────────

    def R_sigma_gaunt(
        self,
        eps1: float,
        eps2: float,
        eps3: float = 0.0,
    ) -> float:
        """Layer 2 Gaunt correction: R_σ^{Gaunt} = 1 + c₂·ε₁² with c₂ = 4.18.

        C-09b: encodes the a₂ = 4·A² dipole-squared → quadrupole leakage
        propagated through the MES bound. Three orders of magnitude below
        Layer 1 at CF4 parameters.
        """
        return 1.0 + self.C2_GAUNT * float(eps1) ** 2

    # ── Combined ────────────────────────────────────────────────────

    def R_sigma_combined(
        self,
        eps1: float,
        eps2: float,
        eps3: float = 0.0,
    ) -> float:
        """R_σ = R_σ^{boost} × R_σ^{Gaunt}."""
        return self.R_sigma_boost(eps1) * self.R_sigma_gaunt(eps1, eps2, eps3)

    def R_omega_combined(
        self,
        eps1: float,
        eps2: float,
        eps3: float = 0.0,
    ) -> float:
        """Vorticity correction. Exactly 1 by azimuthal orthogonality (C-09b)."""
        return 1.0

    def R_udot_combined(
        self,
        eps1: float,
        eps2: float,
        eps3: float = 0.0,
    ) -> float:
        """Acceleration correction.  Subdominant, ≈ 1 + 0.3·ε₁."""
        return self._boost.R_udot_boost(eps1)

    # ── Universal ratios (Gaunt structure) ──────────────────────────

    def universal_ratios_analytical(self) -> Dict[str, float]:
        """Δ_ω/Δ_σ and Δ_u̇/Δ_σ from the C-14 Gaunt structure.

        Values come from the legacy pipeline (C-09b + C-14):
            Δ_ω / Δ_σ   ≈ 1.478
            Δ_u̇ / Δ_σ  ≈ 3 × 10⁻⁴
        """
        return {
            'Delta_omega_over_Delta_sigma': 1.478,
            'Delta_udot_over_Delta_sigma': 0.003,
            'source': 'C-09b + C-14 Gaunt structure',
            'c1': analytical_c1(),
            'c2': self.C2_GAUNT,
        }

    # ── F invariance breakdown ──────────────────────────────────────

    def filling_fraction_correction(
        self,
        x: float,
        x_max: float,
        Omega_tilt: float,
        R_sigma: float,
    ) -> Dict[str, float]:
        """F-invariance breakdown when Ω_tilt is non-negligible.

            F^{Teff} = F^{lin} − (Ω_tilt / x_max) · (1 − 1/R_σ²)

        The shear bound B_σ scales with R_σ under the boost, changing
        x_max, but Ω_tilt does not (it is a frame-boost effect, not a
        multipole correction) — hence the invariance failure.

        Parameters
        ----------
        x : float
            Master defect scalar.
        x_max : float
            MES ceiling (linear, without boost correction).
        Omega_tilt : float
            Tilt contribution (1+w)²Ω²β²/4 (or the exact sinh²β form for
            non-perturbative tilt).
        R_sigma : float
            Combined correction factor from ``R_sigma_combined``.

        Returns
        -------
        dict
            {'F_lin', 'F_teff', 'Delta_F', 'Delta_F_over_F'}.
        """
        if x_max <= 0:
            return {
                'F_lin': 0.0,
                'F_teff': 0.0,
                'Delta_F': 0.0,
                'Delta_F_over_F': 0.0,
            }

        F_lin = x / x_max
        R2 = R_sigma ** 2 if R_sigma != 0.0 else 1.0
        correction = (Omega_tilt / x_max) * (1.0 - 1.0 / R2)
        F_teff = F_lin - correction
        Delta_F = F_teff - F_lin
        Delta_F_over_F = (
            Delta_F / F_lin if abs(F_lin) > 1e-30 else 0.0
        )
        return {
            'F_lin': F_lin,
            'F_teff': F_teff,
            'Delta_F': Delta_F,
            'Delta_F_over_F': Delta_F_over_F,
        }

    # ── VN-04 cross-check ───────────────────────────────────────────

    def cross_check_vn04(self) -> Dict[str, Dict[str, float]]:
        """Compare R_σ^{combined} against VN-04 reference at S1/S2/S3."""
        out: Dict[str, Dict[str, float]] = {}
        for name, sc in VN04_SCENARIOS.items():
            R_ours = self.R_sigma_combined(sc['eps1'], sc['eps2'], sc['eps3'])
            R_vn04 = sc['R_sigma_vn04']
            rel_err = abs(R_ours - R_vn04) / abs(R_vn04)
            out[name] = {
                'R_ours': R_ours,
                'R_vn04': R_vn04,
                'rel_error': rel_err,
                'within_1pct': rel_err < 0.01,
            }
        return out
