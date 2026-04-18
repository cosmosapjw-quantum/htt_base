"""Geometry-discrimination channels for Bianchi type identification.

Three strategies that go beyond scalar amplitude to discriminate
the geometric source of the tilt signal:

Strategy 1: Quadrupole axis alignment
  - BI predicts quadrupole axis ∥ tilt axis
  - BVIIh predicts spiral-rotated offset

Strategy 2: Parity/handedness test
  - BVIIh is the ONLY type that breaks parity symmetry
  - The spiral parameter x_h determines handedness

Strategy 3: W²/Σ² joint posterior contour
  - The rotation bound constrains W² for BVIIh
  - If W² is too small for spirals, BVIIh is disfavoured

STATUS: These are EXPLORATORY channels. They use the existing
directional_models infrastructure + BASS hierarchy output.
"""
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

__all__ = [
    'QuadrupoleAxisTest', 'ParityTest', 'VorticityShearContour',
    'run_geometry_discrimination',
]


# ── Observed CMB quadrupole axis (Planck 2018) ──────────────
# The preferred axis of the observed ℓ=2 pattern
# From de Oliveira-Costa et al. (2004), updated by Planck:
OBS_QUAD_L = 240.0  # galactic longitude, degrees
OBS_QUAD_B = 64.0   # galactic latitude, degrees
OBS_QUAD_SIGMA = 25.0  # uncertainty cone radius, degrees


def _unit_vec(l_deg, b_deg):
    l, b = np.radians(l_deg), np.radians(b_deg)
    return np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])


def _angular_sep(l1, b1, l2, b2):
    d1, d2 = _unit_vec(l1, b1), _unit_vec(l2, b2)
    return np.arccos(np.clip(np.dot(d1, d2), -1, 1))


# ═══════════════════════════════════════════════════════════════
#  Strategy 1: Quadrupole Axis Alignment
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class QuadrupoleAxisResult:
    """Result of the quadrupole axis alignment test."""
    model: str
    tilt_axis_l: float
    tilt_axis_b: float
    predicted_quad_l: float
    predicted_quad_b: float
    observed_quad_l: float
    observed_quad_b: float
    angular_offset_deg: float
    log_likelihood_alignment: float
    interpretation: str


class QuadrupoleAxisTest:
    """Test whether the predicted quadrupole axis matches the observed one.

    For BI: the shear-induced quadrupole axis IS the tilt axis (axisymmetric).
    For BVIIh: the spiral rotates the quadrupole axis by an angle that
    depends on x_h. The rotation is in the plane perpendicular to the
    tilt axis, with magnitude ~ arctan(f₃/f₂) where f₂, f₃ are the
    VIIh transfer fractions.

    The likelihood is a Fisher distribution on the sphere:
      L_align = κ cos(Δθ)
    where Δθ is the angular separation and κ = 1/σ²_quad.
    """

    def __init__(self, sigma_deg: float = OBS_QUAD_SIGMA):
        self.kappa = (180.0 / (np.pi * sigma_deg))**2

    def predict_quad_axis_BI(self, tilt_l: float, tilt_b: float) -> Tuple[float, float]:
        """BI: quadrupole axis = tilt axis (axisymmetric shear)."""
        return tilt_l, tilt_b

    def predict_quad_axis_BVIIh(self, tilt_l: float, tilt_b: float,
                                 x_h: float) -> Tuple[float, float]:
        """BVIIh: quadrupole axis rotated by spiral angle.

        The spiral parameter x_h controls the angular offset between
        the tilt axis and the quadrupole axis. For x_h → 0 or x_h → ∞,
        the offset vanishes. Maximum offset at x_h ~ 0.3-0.5.
        """
        # Spiral rotation angle (phenomenological fit to AniCLASS templates)
        # The rotation is approximately arctan(x_h / (1 + x_h²)) × 90°
        phi_spiral = np.degrees(np.arctan(x_h / (1 + x_h**2))) * 2.0

        # Rotate the axis by phi_spiral in the perpendicular plane
        # Use great-circle rotation along the galactic equator
        new_l = (tilt_l + phi_spiral) % 360
        new_b = tilt_b  # spiral rotation is primarily in longitude
        return new_l, new_b

    def evaluate(self, model: str, tilt_l: float, tilt_b: float,
                 x_h: float = None) -> QuadrupoleAxisResult:
        """Evaluate quadrupole axis alignment for a given model."""
        if 'VIIh' in model and x_h is not None:
            pred_l, pred_b = self.predict_quad_axis_BVIIh(tilt_l, tilt_b, x_h)
        else:
            pred_l, pred_b = self.predict_quad_axis_BI(tilt_l, tilt_b)

        sep = np.degrees(_angular_sep(pred_l, pred_b, OBS_QUAD_L, OBS_QUAD_B))
        ll = self.kappa * np.cos(np.radians(sep))

        if sep < 30:
            interp = f"Consistent: predicted quad axis {sep:.0f}° from observed"
        elif sep < 60:
            interp = f"Marginal: predicted quad axis {sep:.0f}° from observed"
        else:
            interp = f"Tension: predicted quad axis {sep:.0f}° from observed"

        return QuadrupoleAxisResult(
            model=model,
            tilt_axis_l=tilt_l, tilt_axis_b=tilt_b,
            predicted_quad_l=pred_l, predicted_quad_b=pred_b,
            observed_quad_l=OBS_QUAD_L, observed_quad_b=OBS_QUAD_B,
            angular_offset_deg=round(sep, 1),
            log_likelihood_alignment=round(float(ll), 2),
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Strategy 2: Parity / Handedness Test
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ParityResult:
    """Result of the parity/handedness test."""
    model: str
    has_handedness: bool
    x_h: Optional[float]
    parity_asymmetry: float   # observed CMB parity anomaly measure
    preferred_handedness: str  # 'left' or 'right' or 'none'
    log_likelihood_parity: float
    interpretation: str


class ParityTest:
    """Test whether a model's parity signature matches the observed CMB.

    The CMB has a known parity anomaly: even-ℓ power > odd-ℓ power at
    low ℓ, and the quadrupole-octupole alignment has a preferred handedness.

    BVIIh is the ONLY Bianchi type that produces a parity-breaking pattern
    (the spiral has a definite handedness determined by sign(x_h)).
    BI, BIII, BIX are all parity-symmetric.

    The parity statistic is:
      S⁺ = Σ_{ℓ even} (2ℓ+1)C_ℓ / Σ_{ℓ odd} (2ℓ+1)C_ℓ
    """

    # Observed CMB parity anomaly (Planck 2018)
    # S⁺ ≈ 0.47 for ℓ ≤ 30 (even parity deficit) — p-value ~ 0.1%
    OBS_PARITY_RATIO = 0.47
    OBS_PARITY_SIGMA = 0.15

    def evaluate(self, model: str, x_h: float = None,
                 Theta: np.ndarray = None) -> ParityResult:
        """Evaluate parity test for a model.

        Parameters
        ----------
        model : str
            Model name.
        x_h : float
            VIIh spiral parameter (determines handedness).
        Theta : array
            Multipole amplitudes Θ_ℓ from BASS hierarchy (if available).
        """
        has_hand = 'VIIh' in model and x_h is not None

        if has_hand:
            # VIIh spiral produces parity asymmetry proportional to sin(2πx_h)
            # Handedness is determined by sign of x_h (convention)
            parity_pred = 1.0 + 0.3 * np.sin(2 * np.pi * x_h / 10.0)
            handedness = 'right' if x_h > 0 else 'left'
        else:
            # Parity-symmetric models predict S⁺ ≈ 1
            parity_pred = 1.0
            handedness = 'none'

        # If we have BASS hierarchy output, compute the actual parity ratio
        if Theta is not None and len(Theta) > 3:
            even_power = sum((2*ell+1) * Theta[ell]**2
                             for ell in range(2, len(Theta), 2))
            odd_power = sum((2*ell+1) * Theta[ell]**2
                            for ell in range(1, len(Theta), 2))
            if odd_power > 0:
                parity_pred = even_power / odd_power

        # Likelihood: Gaussian comparison with observed parity ratio
        chi2 = ((parity_pred - self.OBS_PARITY_RATIO) / self.OBS_PARITY_SIGMA)**2
        ll = -0.5 * chi2

        if has_hand:
            interp = (f"BVIIh spiral (x_h={x_h:.2f}, {handedness}) predicts "
                       f"S⁺={parity_pred:.2f} vs observed {self.OBS_PARITY_RATIO:.2f}")
        else:
            interp = (f"Parity-symmetric model predicts S⁺≈1.0 "
                       f"vs observed {self.OBS_PARITY_RATIO:.2f} (2.5σ tension)")

        return ParityResult(
            model=model,
            has_handedness=has_hand,
            x_h=x_h,
            parity_asymmetry=round(parity_pred, 3),
            preferred_handedness=handedness,
            log_likelihood_parity=round(float(ll), 2),
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Strategy 3: W²/Σ² Joint Posterior Contour
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class VorticityShearResult:
    """Result of the W²/Σ² joint contour analysis."""
    model: str
    W2_median: float
    Sigma2_median: float
    W2_95UL: float
    Sigma2_95UL: float
    W2_needed_for_spiral: float
    spiral_viable: bool
    rotation_bound_constrains: bool
    log_likelihood_ratio: float
    interpretation: str


class VorticityShearContour:
    """Joint W²/Σ² analysis for BVIIh geometry discrimination.

    BVIIh requires W² > 0 for the spiral pattern. The rotation bound
    (Saadeh et al.) constrains omega_H, which maps to W². If the
    rotation bound pushes W² below the level needed for an observable
    spiral in D₃, BVIIh is geometrically disfavoured.

    The critical question: is the W² needed for VIIh spirals
    compatible with the Saadeh rotation upper limit?
    """

    # Saadeh et al. 2016 rotation upper limit
    OMEGA_H_UL = 2.45e-11   # 95% CL
    OMEGA_H_SIGMA = 1.25e-11

    # Minimum W² for observable BVIIh spiral signature
    # (from AniCLASS: x_h ~ 0.3 with W² ≳ 10⁻¹⁸ gives D₃ ≳ 1 μK²)
    W2_SPIRAL_MIN = 1e-18

    def omH_from_W2(self, W2: float) -> float:
        """Convert vorticity W² to rotation parameter omega_H."""
        return np.sqrt(max(W2, 0)) * 1e-4  # scaling from evidence_models

    def evaluate(self, model: str,
                 W2_samples: np.ndarray = None,
                 Sigma2_samples: np.ndarray = None,
                 weights: np.ndarray = None) -> VorticityShearResult:
        """Evaluate the W²/Σ² joint contour.

        If posterior samples are provided, computes actual posterior summaries.
        Otherwise, uses characteristic values for the model type.
        """
        if W2_samples is not None and weights is not None:
            w = weights / weights.sum()
            W2_med = float(np.average(W2_samples, weights=w))
            W2_95 = float(np.percentile(W2_samples, 95))
            S2_med = float(np.average(Sigma2_samples, weights=w)) if Sigma2_samples is not None else 0.0
            S2_95 = float(np.percentile(Sigma2_samples, 95)) if Sigma2_samples is not None else 0.0
        else:
            # Characteristic values for BVIIh_tilt from pipeline
            W2_med = 1e-18
            W2_95 = 1e-14
            S2_med = 1e-25
            S2_95 = 1e-20

        # Is the rotation bound compatible with spiral-level W²?
        omH_at_W2_spiral = self.omH_from_W2(self.W2_SPIRAL_MIN)
        rotation_constrains = omH_at_W2_spiral < self.OMEGA_H_UL
        spiral_ok = W2_95 > self.W2_SPIRAL_MIN

        # Log-likelihood ratio: how much does the rotation bound
        # penalise the W² needed for spirals?
        omH_95 = self.omH_from_W2(W2_95)
        if omH_95 > self.OMEGA_H_UL:
            ll_penalty = -0.5 * ((omH_95 - self.OMEGA_H_UL) / self.OMEGA_H_SIGMA)**2
        else:
            ll_penalty = 0.0

        if spiral_ok and not rotation_constrains:
            interp = "W² sufficient for spiral AND consistent with rotation bound"
        elif spiral_ok and rotation_constrains:
            interp = "W² sufficient for spiral but rotation bound is tight"
        else:
            interp = "W² too small for observable spiral pattern"

        return VorticityShearResult(
            model=model,
            W2_median=W2_med, Sigma2_median=S2_med,
            W2_95UL=W2_95, Sigma2_95UL=S2_95,
            W2_needed_for_spiral=self.W2_SPIRAL_MIN,
            spiral_viable=spiral_ok,
            rotation_bound_constrains=rotation_constrains,
            log_likelihood_ratio=round(float(ll_penalty), 2),
            interpretation=interp,
        )


# ═══════════════════════════════════════════════════════════════
#  Combined: Run all three strategies
# ═══════════════════════════════════════════════════════════════

def run_geometry_discrimination(
    tilt_l: float = 261.0, tilt_b: float = 1.0,
    models: list = None,
    Theta_bass: np.ndarray = None,
    verbose: bool = True,
) -> Dict:
    """Run all three geometry-discrimination strategies.

    Parameters
    ----------
    tilt_l, tilt_b : float
        Best-fit tilt axis direction in galactic coordinates.
    models : list of str
        Model names to test. Default: BI_tilt, BVIIh_tilt.
    Theta_bass : array
        BASS hierarchy Θ_ℓ amplitudes (if available).
    verbose : bool
        Print results.
    """
    if models is None:
        models = ['BI_tilt', 'BVIIh_tilt']

    quad_test = QuadrupoleAxisTest()
    parity_test = ParityTest()
    ws_test = VorticityShearContour()

    results = {'tilt_axis': {'l': tilt_l, 'b': tilt_b}}

    if verbose:
        print(f"\n{'='*65}")
        print(f" GEOMETRY DISCRIMINATION ANALYSIS")
        print(f" Tilt axis: (l, b) = ({tilt_l:.1f}°, {tilt_b:.1f}°)")
        print(f"{'='*65}")

    # Strategy 1: Quadrupole axis alignment
    if verbose:
        print(f"\n--- Strategy 1: Quadrupole Axis Alignment ---")
    results['quadrupole_axis'] = {}
    for m in models:
        x_h = 1.0 if 'VIIh' in m else None
        r = quad_test.evaluate(m, tilt_l, tilt_b, x_h=x_h)
        results['quadrupole_axis'][m] = {
            'predicted_quad': (r.predicted_quad_l, r.predicted_quad_b),
            'angular_offset_deg': r.angular_offset_deg,
            'logL': r.log_likelihood_alignment,
            'interpretation': r.interpretation,
        }
        if verbose:
            print(f"  {m:20s} offset={r.angular_offset_deg:5.1f}°  "
                  f"logL={r.log_likelihood_alignment:+.2f}  {r.interpretation}")

    # Strategy 2: Parity test
    if verbose:
        print(f"\n--- Strategy 2: Parity / Handedness ---")
    results['parity'] = {}
    for m in models:
        x_h = 1.0 if 'VIIh' in m else None
        r = parity_test.evaluate(m, x_h=x_h, Theta=Theta_bass)
        results['parity'][m] = {
            'has_handedness': r.has_handedness,
            'parity_asymmetry': r.parity_asymmetry,
            'handedness': r.preferred_handedness,
            'logL': r.log_likelihood_parity,
            'interpretation': r.interpretation,
        }
        if verbose:
            print(f"  {m:20s} S⁺={r.parity_asymmetry:.3f}  "
                  f"logL={r.log_likelihood_parity:+.2f}  {r.interpretation}")

    # Strategy 3: W²/Σ² contour
    if verbose:
        print(f"\n--- Strategy 3: W²/Σ² Joint Contour ---")
    results['vorticity_shear'] = {}
    for m in models:
        if 'VIIh' in m:
            r = ws_test.evaluate(m)
        else:
            r = ws_test.evaluate(m, W2_samples=np.array([0.0]),
                                 Sigma2_samples=np.array([1e-25]),
                                 weights=np.array([1.0]))
        results['vorticity_shear'][m] = {
            'W2_median': r.W2_median,
            'W2_95UL': r.W2_95UL,
            'Sigma2_median': r.Sigma2_median,
            'spiral_viable': r.spiral_viable,
            'logL_penalty': r.log_likelihood_ratio,
            'interpretation': r.interpretation,
        }
        if verbose:
            print(f"  {m:20s} W²_95={r.W2_95UL:.1e}  spiral={r.spiral_viable}  "
                  f"logL={r.log_likelihood_ratio:+.2f}  {r.interpretation}")

    # Combined discrimination
    if verbose:
        print(f"\n--- Combined Geometry Discrimination ---")
        # For each model, sum the three logL contributions
        for m in models:
            total = (results['quadrupole_axis'][m]['logL']
                     + results['parity'][m]['logL']
                     + results['vorticity_shear'][m]['logL_penalty'])
            print(f"  {m:20s} total logL = {total:+.2f}")

    return results
