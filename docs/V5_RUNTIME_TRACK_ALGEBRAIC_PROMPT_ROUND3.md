# Algebraic Audit Prompt — Round 3

_Self-contained prompt for a fresh Claude session. No repo access; all code and structure-constant data inline._

This is the follow-up to `V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT.md` (Round 1) and
`V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND2.md` (Round 2). After Round-1 and
Round-2 patches, the residual-joint operator's largest real eigenvalue is at
machine precision for the **FLRW (Type I) anchor** (`λ_max ≈ 10⁻¹⁶` both at
`γ_T = 0` and `γ_T = 1`, across `L_max ∈ {4, 6, 8, 12, 16}`), the
`D_2 = 1002.086744 μK²` FLRW regression anchor is bit-identical through eight
consecutive physics patches, and the cosmological-range IMEX integration
completes `η = 261 → 14147 Mpc` in 130 s.

Round 2's Q-7.2 concluded that the per-family scalar `_family_conditioned_kernel_law`
(10 constants × 10 Bianchi families) is **not** a first-principles object: the
correct family dependence is matrix-valued and must be assembled from the
algebra data `(a, n, C, h)`. Round 2's Q-7.4 accordingly proposed neutralizing
the per-family scalars to identity values; as a practical matter the non-Type-I
code still holds hand-tuned 1.04–1.22 constants, and every non-Type-I run
therefore inherits (and silently contaminates) the Type-I operator with no
anisotropic structure entering the residual-joint hierarchy.

Round 3 fills in the matrix-valued replacement for five representative
non-Type-I families: **II, III, V, VII₀, VIII** (class-A nilpotent,
class-B hyperbolic open, class-B open anchor, class-A helical anchor, and
class-A noncompact `SL(2,ℝ)`-type, respectively). These five span the
intrinsic-anisotropic (II, III, VIII) and isotropic-anchor (V, VII₀)
branches; successful closure here sets the template for the remaining five
(IV, VI₀, VI_h, VII_h, IX).

Paste the block under **"PROMPT FOR CLAUDE"** into a fresh session and
forward the answer back for patching.

---

## Residual defect this round targets

After Round-1 and Round-2 patches the operator has:

- **Type I (FLRW)**: `λ_max = O(10⁻¹⁶)`, `D_2` bit-identical, Bianchi-I
  invariant manifold `r_h ≡ 0`, `b_hh ≡ 0` holds.
- **Types II–IX**: `_family_conditioned_kernel_law` dispatches to
  per-family branches with 10 × 10 hand-tuned scalar modifiers
  (`transport_scale`, `mix_scale`, `twist_mix_scale`, `polarization_scale`,
  `source_scale`, `mass_scale`, `local_drag_scale`, `cross_mode_scale`,
  `collision_scale`, `mode_plus_scale`, `mode_minus_scale`). Round-2 Q-7.2
  **explicitly rejected** these as first-principles objects. They remain in
  the code path because no replacement has been derived.
- **Consequence**: the residual-joint operator for Types II–IX inherits
  Type-I physics up to an overall 1–20% scalar modifier, with **no actual
  structure-constant-valued anisotropic transport or mode cross-coupling
  entering the operator**.

Round 3 asks for the matrix-valued replacement, per family.

---

## PROMPT FOR CLAUDE

```
You are a physics auditor for a CMB Boltzmann solver (BASS) implementing the
PSTF (1+3 covariant Ellis–van Elst) hierarchy for all 10 Bianchi families.
You will not run any code. All input is algebraic; all output is algebraic
or symbolic. Rounds 1 and 2 of this audit fixed eight defects in
bass/hierarchy/ver3_layout_protocol.py and confirmed the Type-I (FLRW)
free-streaming block is weighted skew-adjoint to machine precision WITH
the FLRW D_2 regression anchor bit-identical. Round 2's Q-7.2 concluded
that the per-family kernel law is empirical and should be replaced by
matrix-valued couplings assembled from the algebra data. Round 3 asks
you to derive that replacement for five representative non-Type-I
families.

=================================================================
ROUND-1+2 RECAP (established, do not re-derive)
=================================================================

STATE SPACE (Type I, Bianchi I / FLRW):
  residual_local   (baryon + CDM local DOFs at fixed mu)
  residual_harmonic (T, E, B, nu towers indexed by (mu, ell, m))
  residual_source  (visibility / polarization / doppler / reion sources)

Advance:  dr/dη = A_right(η) · r + b(η).

Round-1+2 findings (assumed now true):

1.  For each channel X in {T, E, B, nu}, the free-streaming sub-block A_X
    satisfies W^(X) A_X + A_X^T W^(X) = 0 with weight
    W^(X)_ell = (2 ell + 1) / d^(X)_ell. This is exactly the Ma-Bertschinger
    streaming Liouville operator in row-scaled basis; Re(λ) = 0 to machine
    precision.

2.  Thomson damping sign is -kappadot·Θ_ell for diagonal and +3·kappadot/R
    for local ↔ harmonic off-diagonal (Dodelson 4.105; MB 1995 eq. 64-66).

3.  T↔E quadrupole-only Thomson mix: restricted to ell=2, proportional to
    kappadot·√6/10 (KKS 1997). E↔B = 0 in FLRW (parity).

4.  Source-block diagonal sign = -kappadot (Thomson damping pattern 3/4).

5.  FLRW invariant manifold r_h(η) ≡ 0, b_hh(η) ≡ 0 holds. D_2 =
    1002.086744 μK² is bit-identical through 8 operator patches.

6.  (Q-7.2 CONCLUSION) The 10 × 10 per-family scalar `_family_conditioned_kernel_law`
    values are hand-tuned placeholders with no first-principles derivation.
    A true family dependence is matrix-valued and must come from the
    algebra data (a^α, n^αβ, C^γ_{αβ}, h). Scalar compression to
    "transport_scale = 1.10" (Type II) etc. requires a choice of (backend
    basis, mode-label normalization, operator norm) that is arbitrary.

=================================================================
BACKGROUND YOU MAY ASSUME
=================================================================

CODE SCHEMA (relevant for the patch target):

@dataclass(frozen=True)
class BianchiAlgebra:
    type_name: str                         # "I".."IX" or "VI_h"/"VII_h"
    a: np.ndarray                          # shape (3,), twist vector a^α
    n: np.ndarray                          # shape (3,3), symmetric n^αβ tensor
    C: np.ndarray                          # shape (3,3,3), C^γ_{αβ} = ε_{αβδ}·n^δγ + a_α·δ^γ_β − a_β·δ^γ_α
    h_parameter: float | None              # h = a² / (n2 n3) for class B; None for class A
    class_label: Literal["A", "B"]
    h_convention: str                      # "h = a^2/(n2*n3) in canonical VER2 class-B axes"
    # Jacobi identity n·a = 0 is enforced in __post_init__.

@dataclass(frozen=True)
class FamilySpec:
    family: str                            # canonical label
    algebra: BianchiAlgebra
    class_label: Literal["A","B"]
    isotropic_anchor: bool                 # True for I, V, VII_0, VII_h, IX
    preferred_backend: str                 # v5 §03B backend descriptor

The backend exposes `backend.family_spec.algebra.{a, n, C, h_parameter}` and
the layout exposes `layout.mode_labels: tuple[str,...]` (default 3 modes per
family; see CANONICAL MODE LABELS below).

CANONICAL STRUCTURE CONSTANTS (v5 §03B frozen canonical class-A / B gauge):

    | Type   | diag(n)         | a^α                   | h = a²/(n₂ n₃) |
    |--------|-----------------|-----------------------|----------------|
    | I      | (0, 0, 0)       | (0, 0, 0)             | —              |
    | II     | (1, 0, 0)       | (0, 0, 0)             | —              |
    | III    | (0, 1, −1)      | (1, 0, 0)             | −1 (VI_{−1})   |
    | IV     | (0, 0, 1)       | (1, 0, 0)             | —              |
    | V      | (0, 0, 0)       | (1, 0, 0)             | —              |
    | VI₀    | (0, 1, −1)      | (0, 0, 0)             | —              |
    | VI_h   | (0, 1, −1)      | (√(−h), 0, 0), h < 0  | h ∈ (−1, 0)    |
    | VII₀   | (0, 1, 1)       | (0, 0, 0)             | —              |
    | VII_h  | (0, 1, 1)       | (√h, 0, 0), h > 0     | h > 0          |
    | VIII   | (−1, 1, 1)      | (0, 0, 0)             | —              |
    | IX     | (1, 1, 1)       | (0, 0, 0)             | —              |

CANONICAL MODE LABELS (defaults; backend may override):

    I      : ("m0", "m+2", "m-2")
    II     : ("mu_nil", "mu_nil+", "mu_nil-")
    III    : ("mu_hyp", "mu_hyp+", "mu_hyp-")
    V      : ("mu_open", "mu_open+", "mu_open-")
    VII_0  : ("mu_hel", "mu_hel+", "mu_hel-")
    VIII   : ("mu_sl2r", "mu_sl2r+", "mu_sl2r-")

The "+" / "-" suffix denotes helicity partners; the bare label is the anchor
scalar mode. For class-A helical / compact-group families (VII_0, VII_h,
VIII, IX) the residual hierarchy couples anchor ↔ "+" ↔ "-" in a helical
triangle; for other families (I, II, III, IV, V, VI_0, VI_h) the residual
only couples to the anchor.

V5 §03B FROZEN BACKEND DATA (from docs/bianchi_design_pack_v5/03B,
solvable families II–VII scalar spectral ODE):

    Type II:   k_C_check(k) = (0, k),          ρ_II(k,r)  = |k|,         ν̇_II(k)  = |k|
    Type III:  k_C_check(k) = (k_2, k_1),      ρ_III(k,r) = e^{-r},     ν̇_III(k) = 1
    Type IV:   k_C_check(k) = (k_2, k_2·k_1),  ρ_IV(k,r)  = e^{-2r}(1+k_1), ν̇_IV(k) = 1 + k_1
    Type V:    (class B, a·a = 1; open hyperbolic anchor modes)   [derive]
    Type VI_0: k_C_check(k) = R_{π/2}^{k_2}(1,k_1),                ν̇_{VI₀}(k) = 1
    Type VI_h  (q > 0):  K = R_0^+ × Z_4,  ν̇ = q^{k_2 mod 2}
    Type VI_h  (q < 0):  K = R/2πZ,        ν̇ = cos²k − q·sin²k
    Type VII_0:  (helical anchor, two helical partners)           [derive]
    Type VII_h:  K = (−e^{πp}, −1] ∪ [1, e^{πp}),  ν̇ = |k|,
                 ρ_{VII_h}(k,r) = e^{-2pr}·|k|,    p = √h

    Type VIII principal-series Plancherel density:
        ρ^cont_{VIII}(μ, s) = (1 / (2π)²)·s·sinh(2π s) / (cosh(2π s) + cos(2π μ)),
        for −1/2 ≤ μ < 1/2, s ≥ 0.
    Type VIII discrete-series Plancherel density:
        ρ^disc_{VIII}(λ) = (1 / (2π)²)·(λ − 1/2),  λ ≥ 1/2.
    Special reductions:
        ρ^cont(0, s)   = (1/(2π)²)·s·tanh(π s),
        ρ^cont(1/2, s) = (1/(2π)²)·s·coth(π s).

OPERATOR SCALES CURRENTLY PRODUCED (bass/hierarchy/ver3_layout_protocol.py:
_operator_scales, lines 136–187, post-Round-2 neutralization):

    geom_scale    = branch_scale · max(√(Σnᵢ² + twist² + 0.25·|R| + |R_PSTF|² + |σ|²), 1)
                    · family_law["transport_scale"]
    mix_scale     = 0 · family_law["mix_scale"]              # neutralized
    twist_scale   = branch_scale · (|a|/(1+|a|+|h|)) · family_law["twist_mix_scale"]
    polarization  = 1 · family_law["polarization_scale"]     # neutralized base
    source_scale  = 1 · family_law["source_scale"]           # neutralized base
    mass_scale    = family_law["mass_scale"]
    local_drag    = family_law["local_drag_scale"]
    cross_mode    = family_law["cross_mode_scale"]
    collision     = family_law["collision_scale"]
    mode_plus     = family_law["mode_plus_scale"]
    mode_minus    = family_law["mode_minus_scale"]

For Type I: family_law returns identity (all 1.0 or 0.0 as appropriate).
For Types II–IX: family_law returns 1.04–1.22 hand-tuned scalars.

WHERE THESE SCALES ENTER THE OPERATOR:

    assemble_mass_matrix           uses  mass_scale, mode_plus, mode_minus
    assemble_free_streaming_block  uses  geom_scale, polarization, cross_mode, mode_plus, mode_minus
    assemble_mixing_block          uses  mix_scale (T↔E), twist_scale (E↔B), cross_mode,
                                           mode_plus, mode_minus
    assemble_explicit_block        uses  local_drag (baryon Thomson), collision (higher-ell
                                           photon Thomson), twist, cross_mode, mode_plus, mode_minus
    build_reduced_harmonic_affine  uses  all of the above through inv_t/e/b/nu diagonals
                                           and per-(ell,m) coefficient arrays from
                                           _reduced_harmonic_structure(ell_max, mode_labels, family)

AVAILABLE HELPER STRUCTURE (Round-1 weighted-skew per-channel streaming,
relevant for mu-mode cross-coupling):

    _mode_label_weight(mu, mu_index, mu_count, branch_scale, plus_scale, minus_scale)
        returns a scalar in {1, (1 + 0.12·branch)·plus, (1 − 0.08·branch)·minus}
        (the 0.12 / 0.08 / 0.03 constants are hand-tuned placeholders).

    _harmonic_cross_mode_coeff(mu_weight, mix_scale, cross_mode_scale, twist_scale,
                               sector, ell, mu_count):
        sector ∈ {"ph_I", "ph_E", "ph_B", "nu_I"}
        base = mu_weight · mix_scale · cross_mode_scale / max((ell+1)·mu_count, 1)
        returns:
            ph_I  :  0.18 · base
            ph_E  :  0.16 · base
            ph_B  :  0.16 · (1 + 0.5·twist_scale) · base
            nu_I  :  0.12 · base
        (the 0.18 / 0.16 / 0.12 sector-specific constants are hand-tuned
         placeholders and should be derived in Q-8.6 below.)

=================================================================
DEFECT ❾ — family-conditioned kernel: scalar → matrix-valued
=================================================================

The Round-2 Q-7.2 conclusion you may take as theorem:

    THEOREM (Round 2). There is no physically unique scalar replacement
    for transport_scale, mix_scale, twist_mix_scale, polarization_scale,
    source_scale, mass_scale, local_drag_scale, cross_mode_scale,
    collision_scale, mode_plus_scale, mode_minus_scale per Bianchi
    family. The correct family dependence is matrix-valued in the
    (mu, mu') mode-label basis and scalar-valued in the (ell, m) spherical-
    harmonic basis only for class-A isotropic-anchor families. For the
    remaining seven families, the residual-harmonic operator picks up
    ANISOTROPIC couplings of the form
        a^α · P^α_{A_{ell}}    (twist-projected tower drop),
        n^αβ · Q^{αβ}_{A_{ell-2} A_{ell}}  (shear-algebraic tower raise/drop),
        σ^αβ · S^{αβ}_{A_{ell}}  (shear-geometric rescaling),
    each of which mixes mu with mu'' through explicit dependence on the
    structure constants.

Round 3's task is to derive these matrix-valued kernels concretely for
five representative families and provide a patch recipe.

=================================================================
QUESTIONS
=================================================================

Q-8.1  Taxonomy of the 10 scales — matrix vs scalar.
       For each of
         transport_scale, mix_scale, twist_mix_scale, polarization_scale,
         source_scale, mass_scale, local_drag_scale, cross_mode_scale,
         collision_scale, mode_plus_scale, mode_minus_scale
       state which object it should be after Q-7.2:
       (M_μμ') a matrix in the mode-label index,
       (M_{(μ,ell)(μ',ell')}) a matrix also in (ell, m) — i.e. an
         anisotropic tower coupling,
       (s_μ) a mu-dependent scalar (diagonal in both indices), or
       (s) a genuine family-independent scalar.
       Justify each from 1+3 covariant (Ellis-van Elst) PSTF kinematics.
       For (M_{(μ,ell)(μ',ell')}) entries, state the minimum tower
       connectivity (what (ell', m') the entry at (ell, m) couples to).

Q-8.2  mu-mode cross-coupling matrix C^(ph_I)_{μμ'}, C^(ph_E), C^(ph_B),
       C^(nu_I) in terms of (a, n, C, h).
       The current code uses
           base = mu_weight · mix_scale · cross_mode_scale / max((ell+1)·mu_count, 1)
           C_{μμ'}^{ph_I} = 0.18 · base · δ_{μ' ≠ μ}
       Derive the correct form from the PSTF hierarchy's shear / twist /
       structure-constant couplings. Specifically:

       (a) For class-A families with a = 0 (I, II, VI_0, VII_0, VIII, IX),
           show that the only mu-mode cross-coupling is the shear-induced
           σ^αβ · n^γδ matrix element, and derive its explicit form for
           Type II (n = diag(1,0,0)) and Type VIII (n = diag(-1,1,1)).
           For Type II show C^(ph_X)_{μμ'} is rank 1 (single commutator
           direction); for Type VIII show it is rank 3 (semisimple).

       (b) For class-B families with |a| > 0 (III, V), the twist vector
           a^α contributes an additional a^α · δ^γ_{ell} term
           (the "divergence-anchored" coupling of Maartens-Ellis 1995
           eq. 4.14). Derive C^(ph_X)_{μμ'} for Type V (pure twist,
           n = 0) and Type III (n = diag(0,1,-1) and a = (1,0,0)
           simultaneously).

       (c) Confirm the sector-dependent prefactors 0.18 / 0.16 / 0.16 / 0.12
           and identify what they should be derived from. Candidates:
           PSTF normalization factor (2ell+1)/d_ell^(X), Thomson collision
           weight kappadot · π_weight, polarization radial integral
           √6 / 10 (KKS 1997 quadrupole). State each sector's correct
           coefficient explicitly.

       (d) Show that in the Type-I (a = 0, n = 0) limit, each C^(ph_X)_{μμ'}
           collapses to zero, so that b_hh(η) ≡ 0 remains on the Type-I
           invariant manifold and the FLRW D_2 anchor is preserved.

Q-8.3  transport_scale as matrix element.
       Round-2 Q-7.3 gave the correct FLRW limit as geom_scale → q_μ
       (mode eigenvalue of the transport operator), not the placeholder
       max(·, 1) = 1. Derive the per-family q_μ(k) for the five
       families using the v5 §03B scalar spectral ODE:

           ĥ₃₃ · P'' + i · k̂_C^T · F(z) · [ĥ_{•3} + (ĥ_{3•})^T] · P'
             − (λ + k̂_C^T · F(z) · ĥ_{2×2} · F^T(z) · k̂_C
                    − i · ĥ_{3•} · F^T(z) · M^T · k̂_C) · P = 0

       with k̂_C given in the table above and eigenvalue λ. For each
       family:
           Type II:   derive λ_μ(k) from ρ_II(k, r) = |k|, ν̇_II(k) = |k|.
                      Compare to the current placeholder
                          transport_scale · geom_scale = 1.10 · √(1² + 0² + ...).
           Type III:  derive λ_μ(k) from ρ_III(k, r) = e^{-r}.
                      Note that ν̇_III is k-independent → the mode
                      eigenvalue has only exponential radial dependence,
                      not magnitude dependence. Compare to current 1.16.
           Type V:    derive from class-B open-hyperbolic spectrum.
                      Show that the isotropic-anchor limit recovers the
                      FLRW result (Q-8.2d implies the algebraic coupling
                      vanishes in this limit).
           Type VII₀: derive from the helical anchor (complex-mode basis).
                      Identify the helicity split into mu_hel+, mu_hel-
                      and how transport_scale^{±} differs from the
                      anchor transport_scale^{0}.
           Type VIII: derive from the Plancherel density using the
                      principal-series label (μ, s). Identify
                      transport_scale as a function of s for the Type-I
                      (μ = 0) parity-restricted branch:
                      ρ^cont(0, s) = (1/(2π)²) · s · tanh(π s).
                      Derive the O(1) limit as s → ∞.

Q-8.4  twist_mix_scale as rank-1 projector.
       twist_scale enters assemble_mixing_block (E ↔ B parity-breaking
       coupling at ell ≥ 2) and currently reads
           twist_scale = branch_scale · |a| / (1 + |a| + |h|)
       multiplied by family_law["twist_mix_scale"] (hand-tuned).

       Derive the correct form from the PSTF hierarchy's a^α · I_{A_{ell}}
       coupling (Maartens 1998 eq. A.11; Challinor 2000 eq. 3.12).

       (a) Show that the raw coefficient is |a| itself (not a saturated
           form), and the saturation 1 / (1 + |a| + |h|) is a pure
           numerical placeholder.

       (b) Show that for class A (a = 0) every E ↔ B entry vanishes
           identically, and for class B (|a| > 0) the coupling is
           sign-definite (parity-odd → positive in one helicity basis,
           negative in the other).

       (c) Derive the explicit Wigner 3-j dependence for a · I_{A_{ell}}
           acting on spin-2 tensors: for (ell, m) → (ell ± 1, m ± 0, ± 1)
           transitions, state the coupling matrix element in the canonical
           axis (a^α = |a| · δ^α_1).

       (d) Provide the family-specific twist_mix_scale as a matrix
           element for Types III (|a| = 1, h = −1) and V (|a| = 1,
           h = 0). Show it reduces to zero for the class-A families.

Q-8.5  local_drag_scale, mass_scale, collision_scale as
       diagonal-in-(ell,m) but mu-dependent scalars.
       These three currently return hand-tuned 1.04–1.22 values per
       family. Ma-Bertschinger kappadot · n_e depends only on background
       (common across Bianchi families once the electron density is
       computed from the background). The mu-label weighting, however,
       can differ because:

       (a) local_drag_scale = 1/R_{μ}(η), with R_μ = (4 ρ_γ_μ) / (3 ρ_b_μ).
           For class-A families the background is mu-independent → R_μ = R;
           for class-B families the tilt vector v^α couples to a^α and
           induces a mu-dependent R shift. Derive the O(|a|²) correction
           to R_μ for Type III and Type V.

       (b) mass_scale = μ-dependent effective mass in the baryon
           momentum ODE from the anisotropic expansion 3·H_i · δv_i
           (Maartens-Ellis). Derive the trace ⟨mass_scale⟩ = 3·H for
           Type I and the anisotropic correction Tr(σ · n) for Type II
           (nilpotent).

       (c) collision_scale: the ell ≥ 2 Thomson rate is kappadot
           universally. Confirm this is mu-independent for all five
           families, so the 1.03–1.05 family-dependent placeholder has
           no physical basis and collision_scale should simply be 1.

Q-8.6  Concrete Python patch recipe.
       After Q-8.1–Q-8.5, propose a replacement for _family_conditioned_kernel_law
       of the form:

           def _family_conditioned_kernel_operator(backend) -> FamilyKernelPack:
               algebra = backend.family_spec.algebra
               family  = backend.family_spec.family
               mode_labels = backend.mode_labels
               a, n = algebra.a, algebra.n
               return FamilyKernelPack(
                   transport      = ...,   # matrix C_{μμ'} from Q-8.3
                   mu_mode_coupling_t = ..., # matrix C^(ph_I) from Q-8.2
                   mu_mode_coupling_e = ..., # matrix C^(ph_E) from Q-8.2
                   mu_mode_coupling_b = ..., # matrix C^(ph_B) from Q-8.2
                   mu_mode_coupling_nu= ..., # matrix C^(nu_I) from Q-8.2
                   twist_mix_kernel = ..., # Wigner 3-j per-(ell,m) from Q-8.4
                   local_drag_by_mu = ..., # vector R_μ⁻¹ from Q-8.5(a)
                   mass_by_mu       = ..., # vector ⟨mass⟩_μ from Q-8.5(b)
                   collision        = 1.0, # universal (Q-8.5c)
                   ...
               )

       (a) Specify the exact NumPy / linear-algebra shape of each returned
           object:
               transport, mu_mode_coupling_* : shape (mu_count, mu_count)
               twist_mix_kernel              : shape (ell_max+1, 2, 2)  or (ell_max, 2ell_max+1, 4)  — state
               local_drag_by_mu, mass_by_mu  : shape (mu_count,)
               collision                     : scalar

       (b) For Type II, Type III, Type V, Type VII₀, Type VIII, provide
           the explicit 3 × 3 (mu_count = 3) matrix entries for
           mu_mode_coupling_t, parametrized by (a, n). Show that each
           reduces to the 3 × 3 zero matrix in the Type-I limit.

       (c) Provide the patch-diff against the current _operator_scales
           in bass/hierarchy/ver3_layout_protocol.py so that non-Type-I
           runs use matrix multiplication against mu_mode_coupling_*
           rather than a scalar. Keep the Type-I FLRW invariant manifold
           protected: the patch MUST NOT modify b_hh(η) in the FLRW
           limit.

       (d) Explicitly state the expected FLRW post-patch λ_max behavior:
              Re(λ_max) ≤ 0 at γ_T = 0 and at γ_T = 1 for ALL FIVE FAMILIES
              (II, III, V, VII₀, VIII), not just Type I.
           Confirm the Bianchi-specific growing modes (Hawking 1966,
           Doroshkevich-Zeldovich-Novikov 1967) cannot destabilize the
           residual-joint operator — they enter as transient power
           in the background, not as positive eigenvalues of A_right.

=================================================================
OUTPUT FORMAT
=================================================================

Return your answer as a single markdown document with these sections:

    ## Q-8.1 — Taxonomy of the 10 scales
    ## Q-8.2 — mu-mode cross-coupling matrices (5 families)
    ## Q-8.3 — transport_scale as mode-eigenvalue matrix
    ## Q-8.4 — twist_mix_scale as Wigner-3j projector
    ## Q-8.5 — local_drag, mass, collision mu-dependence
    ## Q-8.6 — minimal patch recipe and FLRW-limit verification

Each section must show the algebra explicitly. Cite primary literature
(Ellis-van Elst 1998, Maartens-Ellis 1995, Pontzen-Challinor 2007/2011,
Challinor 2000, Hawking 1966, Ma-Bertschinger 1995, KKS 1997, v5 §03B)
where relevant.

If a question cannot be answered without further v5 spec content
(e.g. the exact backend mode basis for Type VII₀ helical partners),
say so precisely; do not guess. A single "this requires v5 §03A Type
VII₀ helical-basis card" statement is an acceptable and useful answer
for a given coefficient, with a short description of what the missing
piece should look like.

CRITICAL CONSTRAINTS:

(C1) The FLRW D_2 = 1002.086744 μK² regression anchor is bit-identical
     through eight prior patches. This implies r_h(η_0) = 0 and
     b_hh(η) ≡ 0 hold algebraically on the FLRW (Type I) invariant
     manifold. Any patch you propose must NOT change b_hh(η) in the
     FLRW limit — matrix-structure changes to A are safe, bias changes
     are not. Concretely, for Type I (a = 0, n = 0) every proposed
     mu_mode_coupling_* matrix MUST reduce to the zero matrix.

(C2) The Type-I fast-check λ_max < 2e-15 at both γ_T = 0 and γ_T = 1
     across L_max ∈ {4, 6, 8, 12, 16} (scripts/v5_operator_fast_check.py)
     must remain true. For each non-Type-I family II / III / V / VII₀ /
     VIII, the same fast check with family-specific algebra should
     also produce Re(λ_max) ≤ 0 post-patch.

(C3) Proposed matrices must be real-valued in the chosen storage basis.
     Helical partners (μ_hel+, μ_hel−, μ_sl2r+, μ_sl2r−) live in the
     (cos, sin) or (real, imaginary) real-basis decomposition of the
     complex helicity modes, so the matrix-valued coupling must be
     a real 3 × 3 when mu_count = 3.

(C4) The patch target is strictly the residual-joint operator A_right
     in bass/hierarchy/ver3_layout_protocol.py. Do not modify
     background evolution, opacity computation, or source-function
     assembly. Those live in separate modules (bass/background/,
     bass/runtime/, bass/los/) and are out of scope.
```

---

## After Claude answers

The Round-3 answer will likely give 5–6 patches (one per family × structure-
aware scale, plus possibly a single taxonomy-level refactor). Apply them in
order Type II → Type III → Type V → Type VII₀ → Type VIII, with the same
two-step validation after each family:

```bash
venv/bin/python scripts/v5_operator_fast_check.py --family II   # per-family variant
venv/bin/python -m pytest htt/bass/validation/test_d2_regression_anchor.py -q
```

Success criterion per-family:

- Type-I fast check remains `λ_max < 2e-15` at both γ_T values (no regression
  from the current 1366/1366 handoff baseline).
- Non-Type-I fast check now produces `Re(λ_max) ≤ 0` (previously the operator
  was Type-I-equivalent, so it was stable only trivially).
- `D_2 = 1002.086744 μK²` bit-identical (FLRW invariant manifold preserved).

Once all five families are patched, re-run the long-form verification:

```bash
venv/bin/python scripts/v5_runtime_spectral_audit.py  --family II --family III --family V --family VII_0 --family VIII
venv/bin/python scripts/v5_runtime_operator_forensics.py --family II --family III --family V --family VII_0 --family VIII
```

Success: `λ_max(η) < 1e-10` across all 5 η snapshots for each family,
`|W A + A^T W| / |W A| < 1e-10` per channel per family, L_max sweep stays
within round-off for each family.

After closure of Round 3, the Blocker-3 `from_recombination(background_monitor, z_*)`
constructor can proceed on a family-by-family basis. The five families
above become the Tier-A family set for the MIO observatory pipeline; the
remaining five (IV, VI₀, VI_h, VII_h, IX) follow the same pattern.
