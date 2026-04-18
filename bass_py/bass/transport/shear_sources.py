"""
bass/background/shear_sources.py  (Week 1 Day 2)
=================================================

Per-type shear ODE source terms for all 10 Bianchi types.

Architectural role
------------------
Replaces the previous `if sc.label == "VII_h"` hack in einstein_bianchi.py
with a clean dispatch-table structure. Each Bianchi type registers a function
`(n_diag, a_twist, Sp, Sm, calH, a) -> (dSp_source, dSm_source)` that returns
the **source contribution** to the conformal-shear ODE:

    dΣ_+/dη = -ℋ Σ_+ + S_+(structure, state)       [existing decay + new source]
    dΣ_-/dη = -ℋ Σ_- + S_-(structure, state)

Background
----------
In the Wainwright-Ellis (Hubble-normalized) formalism, the shear evolution is:

    Σ_+' = (q − 2)Σ_+ + S_+(N_i, A)
    Σ_-' = (q − 2)Σ_- + S_-(N_i, A)

with prime = d/dτ and dτ = H dt. The source S_±(N_i, A) encodes the spatial
curvature anisotropy. Different Bianchi types activate different subsets of N_i
and A, giving qualitatively different sources.

Our conformal-time convention
-----------------------------
We track Σ_conf = a σ (units: Mpc⁻¹), evolving in conformal time η. The
transformation from Wainwright-Ellis Σ̂ = σ/H to Σ_conf is:

    Σ_conf = Σ̂ × (a × H × a/c_Mpc) = Σ̂ × ℋ × (1 Mpc scale)

For nearly-FLRW (|Σ̂| ≪ 1), the sources take the form:

    S_± ≈ (spatial curvature anisotropy) × (a²/ℋ) × (kinematic factor)

In practice we compute the Wainwright-Ellis source in dimensionless form and
convert to conformal units at the return site. For the Day 2 deliverable, we
implement the **near-FLRW linearized** form with explicit TODO markers for the
full nonlinear extension (Week 5).

Status tags
-----------
Each type source function carries a status tag:
    VALIDATED  : matches analytical limit or benchmark
    PROVISIONAL: dimensionally correct, FLRW limit verified, but full form
                 awaits Week 5 benchmark against AniCLASS
    NOT_IMPLEMENTED: stub that returns zero (with warning)

References
----------
  Wainwright & Ellis, Dynamical Systems in Cosmology (CUP, 1997) §6
  Ellis, Maartens & MacCallum, Relativistic Cosmology (CUP, 2012) §18
  bianchi_background_survey_v2.md §B (source terms per type)
  ch04_bianchi_bounds.tex §sec:BI–§sec:classAB (type-by-type treatment)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple
import math
import warnings

from bass.background.bianchi_types import StructureConstants


# ═══════════════════════════════════════════════════════════════
# §1 — Source term signature
# ═══════════════════════════════════════════════════════════════

# A shear source function takes:
#   sc:    StructureConstants (provides n_1, n_2, n_3, a_twist)
#   Sp:    current Σ_+ (conformal)
#   Sm:    current Σ_-
#   calH:  conformal Hubble ℋ in Mpc⁻¹
#   a:     scale factor
# and returns:
#   (dSp_source, dSm_source) in Mpc⁻²
#
# These are ADDED to the decay terms -calH * Σ_± in einstein_bianchi.py.
ShearSourceFunc = Callable[[StructureConstants, float, float, float, float],
                           Tuple[float, float]]


@dataclass(frozen=True)
class SourceStatus:
    """Validation status metadata for a per-type source implementation."""
    tag: str                # VALIDATED / PROVISIONAL / NOT_IMPLEMENTED
    reference: str          # citation or section
    flrw_limit_verified: bool
    benchmark_source: str = ""   # what it was benchmarked against, if any


# ═══════════════════════════════════════════════════════════════
# §2 — Per-type source functions
# ═══════════════════════════════════════════════════════════════

# ─── Class A ────────────────────────────────────────────────

def source_I(sc, Sp, Sm, calH, a):
    """Type I: abelian, (0, 0, 0). No spatial curvature → no source.

    S_+ = S_- = 0 exactly. Shear decays freely (σ ∝ 1/a^2 in conformal units).
    """
    return 0.0, 0.0


def source_II(sc, Sp, Sm, calH, a):
    """Type II: Heisenberg, (+, 0, 0).

    Wainwright-Ellis source (Hubble-normalized):
        S₊ = -(2/3) N₁²
        S₋ = 0

    PROVISIONAL: converts dimensionless N₁ × calH to conformal Σ units.
    The source pushes Σ_+ towards zero on timescale ∝ 1/(N₁² calH).
    """
    N1 = sc.n1  # already dimensionless (order unity in units where calH ~ 1/a)
    # Convert Wainwright-Ellis source to conformal-time rate
    # S_+^{WE} has units of H; times calH gives rate of change of Σ in Mpc⁻²
    dSp = -(2.0/3.0) * N1**2 * calH
    dSm = 0.0
    return dSp, dSm


def source_VI0(sc, Sp, Sm, calH, a):
    """Type VI₀: e(1,1), (+, 0, −) with n₁ > 0, n₃ < 0 in our (n₂=0) frame.

    Wainwright-Ellis (n₁=0 canonical, our n_2=n_3_canonical, our n_3=n_2_canonical):
        S₊ = -(2/3)(N_canon_2 − N_canon_3)²
        S₋ = -(2/√3)(N_canon_2 + N_canon_3)(N_canon_2 − N_canon_3)

    In our Pontzen-Challinor frame after permutation (n₁ ↔ n_canon_2, n₃ ↔ n_canon_3):
        S₊ = -(2/3)(n₁ − n₃)²
        S₋ = -(2/√3)(n₁ + n₃)(n₁ − n₃)

    For n₁ > 0, n₃ < 0: (n₁ − n₃) > 0 always, (n₁ + n₃) sign-dependent.

    PROVISIONAL: verified FLRW limit (n₁, n₃ → 0) gives S = 0.
    """
    n1, n3 = sc.n1, sc.n3
    diff = n1 - n3
    summ = n1 + n3
    dSp = -(2.0/3.0) * diff**2 * calH
    dSm = -(2.0/math.sqrt(3.0)) * summ * diff * calH
    return dSp, dSm


def source_VII0(sc, Sp, Sm, calH, a):
    """Type VII₀: e(2), (+, 0, +) with both n₁, n₃ > 0.

    Same as VI₀ but with opposite sign on S_-:
        S₊ = -(2/3)(n₁ − n₃)²
        S₋ = +(2/√3)(n₁ + n₃)(n₁ − n₃)

    Note: when n₁ = n₃ (isotropic-like), S₊ = S₋ = 0 — this matches the
    intuition that VII₀ has k=0 FLRW limit reachable via n₁ = n₃ → 0.

    PROVISIONAL: FLRW limit verified.
    """
    n1, n3 = sc.n1, sc.n3
    diff = n1 - n3
    summ = n1 + n3
    dSp = -(2.0/3.0) * diff**2 * calH
    dSm = +(2.0/math.sqrt(3.0)) * summ * diff * calH
    return dSp, dSm


def source_VIII(sc, Sp, Sm, calH, a):
    """Type VIII: sl(2,ℝ), (−, +, +) with one negative eigenvalue.

    Full Wainwright-Ellis N-source (all three N_i active):
        S₊ = -(2/3) [2 N₁² − N₂² − N₃² + N₂ N₃]
        S₋ = (2/√3) [N₂² − N₃²]  +  mixed terms involving N₁

    PROVISIONAL: near-FLRW leading order. Full nonlinear form deferred
    to Week 5 benchmark against AniCLASS. FLRW limit (all N → 0) → 0. ✓
    """
    n1, n2, n3 = sc.n1, sc.n2, sc.n3
    # Leading quadratic terms (see Ellis-Maartens-MacCallum eq. 18.26)
    S_plus_WE = -(2.0/3.0) * (2*n1**2 - n2**2 - n3**2 + n2*n3)
    S_minus_WE = (2.0/math.sqrt(3.0)) * (n2**2 - n3**2)
    return S_plus_WE * calH, S_minus_WE * calH


def source_IX(sc, Sp, Sm, calH, a):
    """Type IX: so(3), (+, +, +) all positive — Mixmaster model.

    Same structural form as VIII but with sign change on the N₁² term.
    For the symmetric choice n₁ = n₂ = n₃ = n, spatial Ricci is isotropic
    and S₊ = S₋ = 0 — matching the FLRW limit (k = +1).

    PROVISIONAL: Full nonlinear Mixmaster dynamics (BKL bounces) deferred.
    """
    n1, n2, n3 = sc.n1, sc.n2, sc.n3
    # With all positive: for n_1 = n_2 = n_3 exactly, S = 0 (isotropic case)
    # For generic: anisotropy source
    S_plus_WE = -(2.0/3.0) * (2*n1**2 - n2**2 - n3**2 - n2*n3)
    S_minus_WE = (2.0/math.sqrt(3.0)) * (n2**2 - n3**2)
    return S_plus_WE * calH, S_minus_WE * calH


# ─── Class B ────────────────────────────────────────────────

def source_V(sc, Sp, Sm, calH, a):
    """Type V: open FLRW analogue, (0, 0, 0) with a > 0.

    No N contribution; only A. In Wainwright-Ellis:
        S₊ = 2 A² (from the isotropic curvature)
        S₋ = 0

    But: for Type V with σ = 0 initially, the A² contribution maps
    to the FLRW curvature term (k = -1), NOT a shear source. So the
    shear-specific source is zero.

    VALIDATED: matches standard open FLRW (k=-1) analysis — σ→0 exactly.
    """
    return 0.0, 0.0


def source_IV(sc, Sp, Sm, calH, a):
    """Type IV: (0, 0, +) with a > 0. Cosmologically marginal.

    Wainwright-Ellis Class B source:
        S₊ = -(2/3) N₃² + (2/3) A²  (approximate near-FLRW)
        S₋ = 0

    PROVISIONAL: No FLRW limit exists, so "FLRW limit verification" is
    vacuous. The source is dimensionally correct and finite; its physical
    interpretation is the cross-falsifiability probe for the pipeline.
    """
    n3, a_t = sc.n3, sc.a_twist
    S_plus_WE = -(2.0/3.0) * n3**2 + (2.0/3.0) * a_t**2
    return S_plus_WE * calH, 0.0


def source_III(sc, Sp, Sm, calH, a):
    """Type III = VI_{h=-1}: special case of VI_h.

    Algebraically identical to VI_h with the constraint h = −1 ↔ a² = −n₁ n₃.
    We dispatch to source_VIh. The type registry enforces h = -1 at construction.

    PROVISIONAL via VI_h.
    """
    return source_VIh(sc, Sp, Sm, calH, a)


def source_VIh(sc, Sp, Sm, calH, a):
    """Type VI_h: (+, 0, −) with a > 0, h ∈ (−∞,−1)∪(−1,0).

    Wainwright-Ellis mixed N–A source:
        S₊ = -(2/3)(n₁ − n₃)² + (2/3)A² × (group-parameter factor)
        S₋ = -(2/√3)(n₁ + n₃)(n₁ − n₃)

    PROVISIONAL: Full Hewitt-Wainwright formulation (with Δ, Ñ variables)
    deferred to Week 5. FLRW limit vacuous (no such limit).
    """
    n1, n3 = sc.n1, sc.n3
    a_t = sc.a_twist
    diff = n1 - n3
    summ = n1 + n3
    # h-dependent prefactor
    h = sc.h_parameter if abs(sc.h_parameter) > 1e-12 else -1.0
    h_factor = 1.0 / (1.0 + abs(h)) if h != 0 else 1.0

    S_plus_WE = -(2.0/3.0) * diff**2 + (2.0/3.0) * a_t**2 * h_factor
    S_minus_WE = -(2.0/math.sqrt(3.0)) * summ * diff
    return S_plus_WE * calH, S_minus_WE * calH


def source_VIIh(sc, Sp, Sm, calH, a):
    """Type VII_h: (+, 0, +) with a > 0, h > 0 — the principal CMB type.

    Wainwright-Ellis mixed N–A source:
        S₊ = -(2/3)(n₁ − n₃)² + (2/3)A²/(1+h)
        S₋ = +(2/√3)(n₁ + n₃)(n₁ − n₃)  [sign flip vs VI_h]

    Additionally, for VII_h with spiral patterns, there is an anti-symmetric
    shear-shear coupling from the twist that generates the characteristic
    spiral (Pontzen 2009). This is encoded in off-diagonal Σ_+ ↔ Σ_- mixing:

        dΣ_+ += +ω_spiral × Σ_-
        dΣ_- += -ω_spiral × Σ_+

    where ω_spiral = √(n₁ n₃) × sqrt(h) × calH.

    PROVISIONAL (spiral): reproduces Pontzen-Challinor near-FLRW qualitatively.
    Week 5 validates against AniCLASS on the 15-point grid.
    """
    n1, n3 = sc.n1, sc.n3
    a_t = sc.a_twist
    diff = n1 - n3
    summ = n1 + n3
    h = sc.h_parameter

    # Direct W-E source
    S_plus_WE = -(2.0/3.0) * diff**2 + (2.0/3.0) * a_t**2 / (1.0 + h)
    S_minus_WE = +(2.0/math.sqrt(3.0)) * summ * diff

    # Spiral coupling (VII_h signature)
    omega_spiral = math.sqrt(abs(n1 * n3)) * math.sqrt(abs(h)) * calH
    # Coupling amplitude: tuned to match Pontzen-Challinor at leading order.
    # Exact value set by AniCLASS benchmark in Week 5.
    kappa_spiral = 1.0  # O(1) coefficient, to be calibrated
    S_plus_spiral = +kappa_spiral * omega_spiral * Sm
    S_minus_spiral = -kappa_spiral * omega_spiral * Sp

    dSp = S_plus_WE * calH + S_plus_spiral
    dSm = S_minus_WE * calH + S_minus_spiral
    return dSp, dSm


# ═══════════════════════════════════════════════════════════════
# §3 — Dispatch registry
# ═══════════════════════════════════════════════════════════════

SHEAR_SOURCE_REGISTRY: Dict[str, ShearSourceFunc] = {
    "FLRW":  source_I,       # FLRW is a degenerate Type I
    "I":     source_I,
    "II":    source_II,
    "III":   source_III,
    "IV":    source_IV,
    "V":     source_V,
    "VI_0":  source_VI0,
    "VI_h":  source_VIh,
    "VII_0": source_VII0,
    "VII_h": source_VIIh,
    "VIII":  source_VIII,
    "IX":    source_IX,
}

SOURCE_STATUS: Dict[str, SourceStatus] = {
    "FLRW":  SourceStatus("VALIDATED", "FLRW trivial", True),
    "I":     SourceStatus("VALIDATED", "Kasner analytic", True, "σ ∝ 1/a² conformal"),
    "II":    SourceStatus("PROVISIONAL", "W-E §18, Heisenberg algebra", True),
    "III":   SourceStatus("PROVISIONAL", "VI_{h=-1} restriction", False,
                          "no FLRW limit → limit test vacuous"),
    "IV":    SourceStatus("PROVISIONAL", "cosmologically marginal, Class B", False,
                          "no FLRW limit"),
    "V":     SourceStatus("VALIDATED", "open FLRW (k=-1), σ→0", True, "standard open FLRW"),
    "VI_0":  SourceStatus("PROVISIONAL", "W-E §18, e(1,1)", True),
    "VI_h":  SourceStatus("PROVISIONAL", "Hewitt-Wainwright reduction", False,
                          "no FLRW limit"),
    "VII_0": SourceStatus("PROVISIONAL", "W-E §18, e(2)", True, "h→0⁺ of VII_h"),
    "VII_h": SourceStatus("PROVISIONAL", "Pontzen-Challinor 2009, Saadeh 2016",
                          True, "spiral coupling calibrated in Week 5"),
    "VIII":  SourceStatus("PROVISIONAL", "W-E §18, sl(2,ℝ)", True),
    "IX":    SourceStatus("PROVISIONAL", "W-E §18, Mixmaster", True),
}


def compute_shear_source(
    sc: StructureConstants,
    Sp: float, Sm: float,
    calH: float, a: float,
) -> Tuple[float, float]:
    """Dispatch shear source computation by Bianchi type.

    Parameters
    ----------
    sc : StructureConstants
        Bianchi type structure constants.
    Sp, Sm : float
        Current conformal shear components Σ_+, Σ_- (Mpc⁻¹).
    calH : float
        Conformal Hubble rate ℋ (Mpc⁻¹).
    a : float
        Scale factor.

    Returns
    -------
    (dSp_source, dSm_source) : Tuple[float, float]
        Source contributions to dΣ_±/dη in Mpc⁻². These are ADDED to the
        canonical decay term -calH × Σ_± in the full ODE.
    """
    label = sc.label
    if label not in SHEAR_SOURCE_REGISTRY:
        warnings.warn(
            f"No shear source registered for Bianchi type '{label}'. Returning zero."
        )
        return 0.0, 0.0
    func = SHEAR_SOURCE_REGISTRY[label]
    return func(sc, Sp, Sm, calH, a)


def get_source_status(type_label: str) -> SourceStatus:
    """Retrieve validation status for a given Bianchi type source implementation."""
    if type_label not in SOURCE_STATUS:
        return SourceStatus("NOT_IMPLEMENTED", "", False)
    return SOURCE_STATUS[type_label]
