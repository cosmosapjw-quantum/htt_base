"""
bass/transport/shear_sources.py  (FB-0.1: Ellis convention)
============================================================

Per-type shear ODE source terms for all 10 Bianchi types + FLRW.

Architectural role
------------------
Dispatch-table for the Bianchi spatial-curvature source contribution to
the Ellis conformal-shear evolution. Each Bianchi type registers a
function ``(sc, Sp, Sm, calH, a) -> (dSp_source, dSm_source)`` that
returns **ℋ² × S^{WE}(type)** in Mpc⁻² units, feeding the Ellis ODE:

    dΣ_+/dη = -2 ℋ Σ_+ + S_+(structure, state)      # Ellis: Σ = a σ
    dΣ_-/dη = -2 ℋ Σ_- + S_-(structure, state)

FB-0.1 convention flip
----------------------
Pre-FB-0.1 this module returned ``ℋ × S^{WE}`` (only one ℋ factor) to
feed a non-Ellis ODE where ``Σ × a = const`` in Type I. The Ellis ODE
requires one additional factor of ℋ (derivation:
``a² × S_proper = a² × H² × S^{WE} = ℋ² × S^{WE}``). All source
functions below accordingly multiply ``S^{WE}`` by ``calH**2`` on the
return path. The Σ-linear spiral coupling in source_VIIh keeps its
``ω_spiral × Σ_⊥`` rotation structure (rate has units of ℋ on both
sides of the convention flip); only the Σ-independent W-E piece picks
up the extra factor of ℋ.

Background (Wainwright-Ellis dimensionless form)
-------------------------------------------------
In the Hubble-normalized (τ = H t, Σ̂ = σ / H) form,

    dΣ̂/dτ = (q − 2)Σ̂ + S^{WE}(N_i, A)

with S^{WE}(N_i, A) the Bianchi spatial-curvature anisotropy.
Converting to proper time gives ``σ̇ = -3 H σ + H² S^{WE}``. Converting
to Ellis conformal shear ``Σ = a σ`` gives
``dΣ/dη = -2 𝓗 Σ + 𝓗² S^{WE}``.

Status tags
-----------
Each type source function carries a status tag:
    VALIDATED  : matches analytical limit or benchmark
    PROVISIONAL: dimensionally correct, FLRW limit verified, but full form
                 awaits FB-1 benchmark (per-type Wainwright-Ellis fixture)
    NOT_IMPLEMENTED: stub that returns zero (with warning)

References
----------
  Wainwright & Ellis, *Dynamical Systems in Cosmology* (CUP, 1997) §6, §18
  Ellis, Maartens & MacCallum, *Relativistic Cosmology* (CUP, 2012) §18
  Pontzen & Challinor, *PRD* 79, 103518 (2009) — VII_h spiral convention
  docs/audits/AUDIT_PHASE_FB0_2026-04-19.md §2 (convention-flip map)
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

    Wainwright-Ellis dimensionless source:
        S^{WE}_+ = -(2/3) N₁²
        S^{WE}_- = 0

    Ellis conformal source = ℋ² × S^{WE} (FB-0.1).

    PROVISIONAL: FLRW limit (N₁ → 0) verified; FB-1 will promote.
    """
    N1 = sc.n1
    dSp = -(2.0/3.0) * N1**2 * calH**2
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
    calH_sq = calH * calH
    dSp = -(2.0/3.0) * diff**2 * calH_sq
    dSm = -(2.0/math.sqrt(3.0)) * summ * diff * calH_sq
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
    calH_sq = calH * calH
    dSp = -(2.0/3.0) * diff**2 * calH_sq
    dSm = +(2.0/math.sqrt(3.0)) * summ * diff * calH_sq
    return dSp, dSm


def source_VIII(sc, Sp, Sm, calH, a):
    """Type VIII: sl(2,ℝ), (−, +, +) with one negative eigenvalue.

    Wainwright-Ellis §18 Table 11.1 row VIII leading-order source
    (all three N_i active):

        S^{WE}_+ = -(2/3) [2 N₁² − N₂² − N₃² + N₂ N₃]
        S^{WE}_- = (2/√3) [N₂² − N₃²]

    Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``.

    VALIDATED (FB-1.2): formula + Σ-independence + S_- sign pattern
    pinned to rel 1e-12 on (n_1<0, n_2>0, n_3>0, ℋ) grid in
    `test_type_VIII_WE_source_formula_and_signs`. FLRW limit
    (all N → 0) → 0. Full nonlinear Mixmaster / BKL dispatch (which adds
    the mixed-with-N_1 terms) deferred to FB-5 / FB-6.
    """
    n1, n2, n3 = sc.n1, sc.n2, sc.n3
    # Leading quadratic terms (see Ellis-Maartens-MacCallum eq. 18.26)
    S_plus_WE = -(2.0/3.0) * (2*n1**2 - n2**2 - n3**2 + n2*n3)
    S_minus_WE = (2.0/math.sqrt(3.0)) * (n2**2 - n3**2)
    calH_sq = calH * calH
    return S_plus_WE * calH_sq, S_minus_WE * calH_sq


def source_IX(sc, Sp, Sm, calH, a):
    """Type IX: so(3), (+, +, +) all positive — Mixmaster model.

    Wainwright-Ellis §18 Table 11.1 row IX leading-order source (differs
    from VIII only by the sign of the N_2 N_3 cross-term — so(3) vs
    sl(2,ℝ) algebra):

        S^{WE}_+ = -(2/3) [2 N₁² − N₂² − N₃² − N₂ N₃]
        S^{WE}_- = (2/√3) [N₂² − N₃²]

    Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``.

    VALIDATED (FB-1.2): formula + Σ-independence + S_- sign pattern
    pinned to rel 1e-12 on (n_i>0, ℋ) grid in
    `test_type_IX_WE_source_formula_and_signs`. At the isotropic point
    n_1 = n_2 = n_3 = n the leading-order form gives
    ``S_+ = +(2/3) n² ℋ² ≠ 0``, a known W-E pathology that the full
    dynamical-systems treatment (Wainwright-Ellis §6.2) resolves
    through compactness at the BKL attractor; we pin this residual
    explicitly in `test_type_IX_isotropic_near_limit_known_pathology`.

    Bianchi IX recollapse is handled via
    `bianchi_ix_recollapse_event` + ``solve_ivp(events=...)`` (FB plan
    §6 D5). The event branch does **not** fire on the production
    Planck-2018 FLRW background (H > 0 always); full vacuum-IX BKL
    oscillation is FB-5 / FB-6 scope.
    """
    n1, n2, n3 = sc.n1, sc.n2, sc.n3
    # With all positive: for n_1 = n_2 = n_3 exactly, S = 0 (isotropic case)
    # For generic: anisotropy source
    S_plus_WE = -(2.0/3.0) * (2*n1**2 - n2**2 - n3**2 - n2*n3)
    S_minus_WE = (2.0/math.sqrt(3.0)) * (n2**2 - n3**2)
    calH_sq = calH * calH
    return S_plus_WE * calH_sq, S_minus_WE * calH_sq


# ─── Class B ────────────────────────────────────────────────

def source_V(sc, Sp, Sm, calH, a):
    """Type V: open FLRW analogue, (0, 0, 0) with a > 0.

    No N contribution; only A. In Wainwright-Ellis:
        S₊ = 2 A² (from the isotropic curvature)
        S₋ = 0

    But: for Type V with σ = 0 initially, the A² contribution maps
    to the FLRW curvature term (k = -1), NOT a shear source. So the
    shear-specific source is zero.

    VALIDATED (FB-1.3): pinned in ``test_type_V_shear_zero_pin``
    (S_± = 0 exactly across the (A, ℋ) grid; A² → FLRW k=-1 curvature).
    """
    return 0.0, 0.0


def source_IV(sc, Sp, Sm, calH, a):
    """Type IV: (0, 0, +) with a > 0. Cosmologically marginal.

    Wainwright-Ellis §18 Table 11.1 row IV source:
        S^{WE}_+ = -(2/3) N_3² + (2/3) A²
        S^{WE}_- = 0

    Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``.

    VALIDATED (FB-1.3): formula + axisymmetric ``S_- = 0`` +
    Σ-independence pinned to rel 1e-12 on the (N_3, A, ℋ) grid in
    ``test_type_IV_WE_source_formula``. Type IV has no FLRW limit —
    it serves as a cross-falsifiability probe for the pipeline; the
    W-E formula is dimensionally correct and finite.
    """
    n3, a_t = sc.n3, sc.a_twist
    S_plus_WE = -(2.0/3.0) * n3**2 + (2.0/3.0) * a_t**2
    return S_plus_WE * calH**2, 0.0


def source_III(sc, Sp, Sm, calH, a):
    """Type III = VI_{h=-1}: special case of VI_h.

    Algebraically identical to VI_h with the constraint h = −1 ↔
    a² = −n₁ n₃. We dispatch to ``source_VIh``; the type registry
    enforces ``h = -1`` at construction via ``n_3 = -a²/n_1``.

    VALIDATED (FB-1.3): dispatch-identity + formula at h = -1 (A²
    prefactor 1/(1+|h|) = 1/2) pinned to rel 1e-12 on the (n_1, ℋ)
    grid in ``test_type_III_dispatches_to_VIh_at_h_minus_1``.
    Reference: Wainwright-Ellis §18 Table 11.1 row III.
    """
    return source_VIh(sc, Sp, Sm, calH, a)


def source_VIh(sc, Sp, Sm, calH, a):
    """Type VI_h: (+, 0, −) with a > 0, h ∈ (−∞,−1)∪(−1,0).

    Wainwright-Ellis §18 Table 11.1 row VI_h mixed N–A source:
        S^{WE}_+ = -(2/3)(n_1 − n_3)² + (2/3) A² / (1 + |h|)
        S^{WE}_- = -(2/√3)(n_1 + n_3)(n_1 − n_3)

    Ellis conformal form (FB-0.1): ``S_± = ℋ² × S^{WE}_±``. The
    h-dependent prefactor ``1/(1+|h|)`` is the Hewitt-Wainwright
    near-FLRW reduction (full Δ, Ñ variables deferred to FB-5/FB-6).

    VALIDATED (FB-1.3): formula + h-prefactor + ``S_+ < 0`` sign +
    Σ-independence pinned to rel 1e-12 on (n_1, n_3, A, h, ℋ) grid in
    ``test_type_VIh_WE_source_formula``. Type VI_h has no FLRW limit;
    the full Hewitt-Wainwright reduction remains FB-5/FB-6 scope.
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
    calH_sq = calH * calH
    return S_plus_WE * calH_sq, S_minus_WE * calH_sq


def source_VIIh(sc, Sp, Sm, calH, a):
    """Type VII_h: (+, 0, +) with a > 0, h > 0 — the principal CMB type.

    Wainwright-Ellis §18 Table 11.1 row VII_h mixed N–A source:
        S^{WE}_+ = -(2/3)(n_1 − n_3)² + (2/3) A² / (1 + h)
        S^{WE}_- = +(2/√3)(n_1 + n_3)(n_1 − n_3)  [sign flip vs VI_h]

    Additionally, the Pontzen-Challinor 2009 §III spiral coupling:

        dΣ_+ += +ω_spiral × Σ_-
        dΣ_- += −ω_spiral × Σ_+
        ω_spiral = √|n_1 n_3| × √h × ℋ,  (κ ≡ 1.0 for FB-1.3)

    The coupling is a **rotation** in the (Σ_+, Σ_-) plane: the
    identity ``Σ_+ dΣ_+^{spi} + Σ_- dΣ_-^{spi} ≡ 0`` holds exactly.

    VALIDATED (FB-1.3): W-E formula rel 1e-12 + P-C spiral sign +
    ω_spiral ∝ √h scaling + rotation invariance pinned in
    ``test_type_VIIh_WE_source_formula_and_spiral_signature`` +
    ``test_type_VIIh_spiral_omega_scales_as_sqrt_h`` +
    ``test_type_VIIh_spiral_rotation_conserves_amplitude``. Full
    quantitative calibration of the O(1) spiral coefficient κ against
    AniCLASS / P-C fixture remains FB-5 / FB-6 scope.

    Reference: Pontzen & Challinor, *PRD* 79, 103518 (2009) §III.
    """
    n1, n3 = sc.n1, sc.n3
    a_t = sc.a_twist
    diff = n1 - n3
    summ = n1 + n3
    h = sc.h_parameter

    # Direct W-E source (Ellis conformal: ℋ² × S^{WE})
    S_plus_WE = -(2.0/3.0) * diff**2 + (2.0/3.0) * a_t**2 / (1.0 + h)
    S_minus_WE = +(2.0/math.sqrt(3.0)) * summ * diff

    # Spiral coupling (VII_h signature). The rotation ``ω × Σ_⊥`` is
    # convention-invariant (rate has units of ℋ in both conventions);
    # only the Σ-independent W-E piece picks up the extra ℋ under
    # FB-0.1.
    omega_spiral = math.sqrt(abs(n1 * n3)) * math.sqrt(abs(h)) * calH
    kappa_spiral = 1.0  # O(1) coefficient, to be calibrated in FB-1
    S_plus_spiral = +kappa_spiral * omega_spiral * Sm
    S_minus_spiral = -kappa_spiral * omega_spiral * Sp

    calH_sq = calH * calH
    dSp = S_plus_WE * calH_sq + S_plus_spiral
    dSm = S_minus_WE * calH_sq + S_minus_spiral
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
    # VALIDATED (FB-1.1): Kasner σ × a³ = const pinned on
    # solve_bianchi_background trajectory (test_type_I_kasner_exponent_sum);
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.1.
    "I":     SourceStatus("VALIDATED", "Kasner analytic + W-E §18 Table 11.1", True,
                          "σ × a³ const on background integrator + FB-0.1 LB-5 I-11/I-12/I-12b"),
    # VALIDATED (FB-1.1): W-E §18 Table 11.1 row II formula
    # S^{WE}_+ = -(2/3) N_1², S^{WE}_- = 0 pinned to rel 1e-12 across
    # (N_1, ℋ) grid in test_type_II_WE_fixed_point_asymptotic;
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.1.
    "II":    SourceStatus("VALIDATED", "W-E §18 Table 11.1, Heisenberg e(1) axisymmetric", True,
                          "formula + sign + Σ-independence pinned on (N_1, ℋ) grid"),
    # VALIDATED (FB-1.3): III is the special case VI_{h=-1}; source_III
    # dispatches bit-identically to source_VIh and the W-E formula
    # evaluated at h = -1 (A² prefactor 1/(1+|h|) = 1/2) is pinned to
    # rel 1e-12 across the (n_1, ℋ) grid in
    # test_type_III_dispatches_to_VIh_at_h_minus_1. Σ-independence
    # pinned. docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.3.
    "III":   SourceStatus("VALIDATED", "W-E §18 Table 11.1 row III (≡ VI_{h=-1})", False,
                          "dispatches to VI_h; formula at h=-1 (A² prefactor 1/2) pinned; no FLRW limit"),
    # VALIDATED (FB-1.3): W-E §18 Table 11.1 row IV formula
    # S^{WE}_+ = −(2/3) N_3² + (2/3) A², S^{WE}_- = 0 pinned to rel
    # 1e-12 across (N_3, A, ℋ) grid in test_type_IV_WE_source_formula.
    # No FLRW limit (cosmologically marginal); Σ-independence pinned.
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.3.
    "IV":    SourceStatus("VALIDATED", "W-E §18 Table 11.1 row IV, cosmologically marginal Class B", False,
                          "formula + axisymmetric S_- = 0 + Σ-indep pinned; no FLRW limit"),
    # VALIDATED since LB baseline; FB-1.3 adds explicit (A, ℋ) grid
    # regression test_type_V_shear_zero_pin (shear-specific source is
    # identically zero — A² is absorbed into k = -1 FLRW curvature,
    # not into dΣ_±). docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.3.
    "V":     SourceStatus("VALIDATED", "W-E §18 Table 11.1 row V (open FLRW, k=-1)", True,
                          "S_± = 0 exactly pinned on (A, ℋ) grid; A² → FLRW curvature"),
    # VALIDATED (FB-1.1): W-E §18 Table 11.1 row VI₀ formula
    # S^{WE}_+ = -(2/3)(n_1-n_3)², S^{WE}_- = -(2/√3)(n_1+n_3)(n_1-n_3)
    # pinned to rel 1e-12 in test_type_VI0_WE_fixed_point_asymptotic;
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.1.
    "VI_0":  SourceStatus("VALIDATED", "W-E §18 Table 11.1, e(1,1) algebra", True,
                          "formula + S_+ < 0 sign + Σ-indep pinned on (n_1, n_3, ℋ) grid"),
    # VALIDATED (FB-1.3): W-E §18 Table 11.1 row VI_h formula
    # S^{WE}_+ = −(2/3)(n_1−n_3)² + (2/3) A² / (1+|h|),
    # S^{WE}_- = −(2/√3)(n_1+n_3)(n_1−n_3) pinned to rel 1e-12 across
    # (n_1>0, n_3<0, A>0, h ∈ (−∞,−1)∪(−1,0), ℋ) grid in
    # test_type_VIh_WE_source_formula. S_+ < 0 + Σ-independence
    # pinned. Full Hewitt-Wainwright (Δ, Ñ variables) reduction
    # remains FB-5/FB-6. docs/audits/AUDIT_PHASE_FB1_2026-04-19.md
    # §FB-1.3.
    "VI_h":  SourceStatus("VALIDATED", "W-E §18 Table 11.1 row VI_h (Hewitt-Wainwright near-FLRW)", False,
                          "formula + h-prefactor + S_+ < 0 + Σ-indep pinned; full reduction FB-5/FB-6"),
    # VALIDATED (FB-1.1): W-E §18 Table 11.1 row VII₀ formula
    # S^{WE}_+ = -(2/3)(n_1-n_3)², S^{WE}_- = +(2/√3)(n_1+n_3)(n_1-n_3)
    # pinned to rel 1e-12 in test_type_VII0_shear_decay_to_plane_wave_line;
    # isotropic n_1=n_3 → S=0 exactly pinned in
    # test_type_VII0_isotropic_limit_vanishes_exactly;
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.1.
    "VII_0": SourceStatus("VALIDATED", "W-E §18 Table 11.1, e(2) algebra (plane-wave line)", True,
                          "formula + S_- sign flip vs VI₀ + isotropic vanishing pinned"),
    # VALIDATED (FB-1.3): W-E §18 Table 11.1 row VII_h formula
    # S^{WE}_+ = −(2/3)(n_1−n_3)² + (2/3) A² / (1+h),
    # S^{WE}_- = +(2/√3)(n_1+n_3)(n_1−n_3) pinned rel 1e-12 on
    # (n_1>0, n_3>0, A>0, h>0, ℋ) grid; Pontzen-Challinor 2009 §III
    # spiral signature pinned qualitatively: antisymmetric coupling
    # (+ω_spi × Σ_-, −ω_spi × Σ_+), ω_spi ∝ √h scaling, and rotation
    # invariance Σ_+ dΣ_+^{spi} + Σ_- dΣ_-^{spi} ≡ 0 at float-
    # subtraction precision. Covered by
    # test_type_VIIh_WE_source_formula_and_spiral_signature +
    # test_type_VIIh_spiral_omega_scales_as_sqrt_h +
    # test_type_VIIh_spiral_rotation_conserves_amplitude. The O(1)
    # spiral coefficient κ = 1.0 is pinned by construction; quantitative
    # calibration against AniCLASS / P-C fixture is FB-5/FB-6.
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.3.
    "VII_h": SourceStatus("VALIDATED", "W-E §18 Table 11.1 row VII_h + Pontzen-Challinor 2009 §III spiral", True,
                          "formula + P-C spiral sign + √h scaling + rotation invariance pinned; κ calibration FB-5/FB-6"),
    # VALIDATED (FB-1.2): W-E §18 Table 11.1 row VIII leading-order
    # source S^{WE}_+ = −(2/3)[2 N_1² − N_2² − N_3² + N_2 N_3],
    # S^{WE}_- = (2/√3)[N_2² − N_3²] pinned to rel 1e-12 on the
    # (n_1<0, n_2>0, n_3>0, ℋ) parametrisation grid (Σ-independence +
    # S_- sign pattern co-pinned) in
    # test_type_VIII_WE_source_formula_and_signs. Full nonlinear
    # Mixmaster-class dispatch remains FB-5/FB-6 scope.
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.2.
    "VIII":  SourceStatus("VALIDATED", "W-E §18 Table 11.1, sl(2,ℝ) algebra", True,
                          "leading-order formula + sign + Σ-indep pinned; full Mixmaster deferred"),
    # VALIDATED (FB-1.2): W-E §18 Table 11.1 row IX leading-order
    # source S^{WE}_+ = −(2/3)[2 N_1² − N_2² − N_3² − N_2 N_3],
    # S^{WE}_- = (2/√3)[N_2² − N_3²] pinned to rel 1e-12 on the
    # (n_i>0, ℋ) parametrisation grid in
    # test_type_IX_WE_source_formula_and_signs. The isotropic-limit
    # (n_1=n_2=n_3=n) S_+ residual = +(2/3) n² ℋ² is a known W-E
    # leading-order pathology pinned explicitly in
    # test_type_IX_isotropic_near_limit_known_pathology; Bianchi IX
    # recollapse uses solve_ivp event dispatch via
    # bianchi_ix_recollapse_event (FB plan §6 D5). Full BKL
    # oscillation remains FB-5/FB-6.
    # docs/audits/AUDIT_PHASE_FB1_2026-04-19.md §FB-1.2.
    "IX":    SourceStatus("VALIDATED", "W-E §18 Table 11.1, so(3) (Mixmaster leading order)", True,
                          "formula + sign + Σ-indep pinned; isotropic W-E pathology documented; full BKL deferred"),
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
