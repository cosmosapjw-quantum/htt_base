# Algebraic Audit Prompt — Round 2

_Self-contained prompt for a fresh Claude session. No repo access; all code inline._

This is the follow-up to `V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT.md` (round 1). Round 1's Q1 (prev/next sign flip) and Q3 (`diag_base → 0`) were applied and verified: each channel's free-streaming block is now weighted-skew-adjoint to machine precision, and the D_2 = 1002.086744 μK² FLRW anchor is bit-identical. A numerical Thomson-sign fix (Option B) was also applied, reducing `λ_max(A_right)` at `γ_T = 1` from +0.926 to +0.321, but three defects remain.

Paste the block under **"PROMPT FOR CLAUDE"** into a fresh session and forward the answer back for patching.

---

## Residual defects this round targets

After round-1 patches the operator still has:

- **γ_T = 0 branch: `λ_max ≈ +0.029`** — spectrum not purely imaginary. This is a non-Thomson mode. Leading suspect: the `mix_t / mix_e` T↔E coupling at ℓ≥2, which has **no γ_T dependence** — i.e. T and E are coupled in the code even in the free-streaming limit, contradicting Ma-Bertschinger where T↔E is a strict Thomson phenomenon.
- **γ_T = 1 branch: `λ_max ≈ +0.321`** — residual Thomson-era growth. The two main diagonal Thomson sign errors have been fixed (harmonic-block `+photon_coll` and local-block `+γ_T/baryon_diag`); this +0.321 must live in the **local ↔ harmonic cross-coupling** between `baryon_dipole` and `T_dipole`.
- **`_operator_scales` hand-tuned constants** — `mix_scale = branch_scale · (0.08 + 0.04 · min(geom_scale, 3))`, `polarization_scale = 1 + 0.35 · twist_scale`, `source_scale = 1 + 0.25 · min(|ricci_pstf|+|σ|, 2)`, and a per-family kernel law with 8 tuning constants per Bianchi family. These have no cited derivation in tree.

The prompt tasks Claude to derive the correct forms for all three.

---

## PROMPT FOR CLAUDE

```
You are a physics auditor for a CMB Boltzmann solver (BASS). You will
not run any code. All input is algebraic; all output is algebraic or
symbolic. Round 1 of this audit already fixed two defects in
bass/hierarchy/ver3_layout_protocol.py (free-streaming sign flip +
diag_base zeroing) and confirmed each channel's harmonic block is now
weighted-skew-adjoint to machine precision, WITH the FLRW D_2
regression anchor bit-identical. Three defects remain.

=================================================================
ROUND-1 RECAP (established, do not re-derive)
=================================================================

State space: residual_local (baryon+CDM local DOFs) + residual_harmonic
(T, E, B, ν harmonic towers indexed by (ℓ, m)) + residual_source.
Advance:  dr/dη = A_right(η) · r + b(η).

Round-1 findings (assumed now true):

1.  For each channel X ∈ {T, E, B, ν}, the free-streaming sub-block
    A_X satisfies W^(X) A_X + A_X^T W^(X) = 0 with the weight
    W^(X)_ℓ = (2ℓ+1) / d^(X)_ℓ.  This is exactly the Ma-Bertschinger
    streaming Liouville operator in the code's row-scaled basis.  Re(λ)
    of each isolated A_X is zero to machine precision.

2.  The FLRW invariant manifold r_h(η) ≡ 0, b_hh(η) ≡ 0 holds — D_2 =
    1002.086744 μK² is bit-identical through 4 operator patches.
    Therefore any matrix-structure change that leaves b_hh invariant
    preserves the FLRW anchor algebraically.

3.  Option-B Thomson-damping sign was applied to both the harmonic-
    block diagonal and the local-block diagonal:

        diag_X = -inv_X · (stream_base + photon_coll)     # was: (-stream_base + photon_coll)
        local_diag = -local_drag · γ_T / |baryon_diag|    # was: +local_drag · γ_T / |baryon_diag|

    This reduced λ_max at γ_T = 1 from +0.926 to +0.321 on an L_max=8
    harmonic block.

Round-2 targets the three remaining defects below.

=================================================================
DEFECT ❺ — local ↔ harmonic cross-coupling (Thomson drag between
baryon dipole and T_1)
=================================================================

CODE (bass/hierarchy/ver3_layout_protocol.py, build_reduced_joint_affine_operator
lines 2050-2069, verbatim):

    # local <- harmonic(theta_1) coupling
    baryon_base_diag = 1.0 + 0.08 * geom_scale + 0.03 * np.arange(baryon_width, dtype=np.float64)
    if baryon_width > 1 and structure.dipole_slot is not None:
        local_theta_coeff = float(
            0.25 * local_drag_scale * gamma_t / max(abs(float(baryon_base_diag[1])), 1.0e-30)
        )
        for residual_index in range(len(residual_labels)):
            local_row = residual_index * local_block_size + 1
            harmonic_col = local_dof + residual_index * harmonic_block_size + int(structure.dipole_slot)
            joint[local_row, harmonic_col] = local_theta_coeff

    # harmonic <- local(baryon velocity) coupling
    if baryon_width > 1 and structure.dipole_slot is not None:
        ell_weight = 1.0 + 0.04 * 1.0 + 0.015 * geom_scale
        inv_t_dipole = 1.0 / max(branch_scale * ell_weight, 1.0e-30)
        harmonic_baryon_coeff = float(inv_t_dipole * (-0.25 * local_drag_scale * gamma_t))
        for residual_index in range(len(residual_labels)):
            harmonic_row = local_dof + residual_index * harmonic_block_size + int(structure.dipole_slot)
            local_col = residual_index * local_block_size + 1
            joint[harmonic_row, local_col] = harmonic_baryon_coeff

REFERENCE PHYSICS (Ma-Bertschinger 1995 eq. 64-66; Dodelson eq. 4.105):

    v̇_b = -ℋ·v_b + (κ̇ / R) · (3·Θ_1 − v_b) + ∂-metric-terms     (baryon)
    Θ̇_1 = k·[(1/3)·Θ_0 − (2/3)·Θ_2] − κ̇ · (Θ_1 − v_b/3) + ...   (photon dipole)

with R ≡ (4 ρ_γ) / (3 ρ_b) the baryon-photon ratio and κ̇ = a·n_e·σ_T > 0.

From these equations the coupling block between (v_b, Θ_1) at ℓ=1 has:

    A[v_b, Θ_1]  =  +3·κ̇/R        # Doppler drive from photon dipole into baryon velocity
    A[Θ_1, v_b]  =  +κ̇/3          # Drag from baryon velocity into photon dipole

Note: both OFF-diagonals carry the SAME SIGN (+), not opposite. The
corresponding diagonals (from round-1 fixes) are:

    A[v_b, v_b]  =  -κ̇/R          # Thomson drag damping (as baryon velocity relaxes to photon dipole)
    A[Θ_1, Θ_1]  =  -κ̇             # Thomson damping of photon dipole

So the 2×2 Thomson block reads, in the (v_b, Θ_1) basis:

    [ -κ̇/R    +3·κ̇/R ]
    [ +κ̇/3    -κ̇      ]

Determinant = κ̇²/R − κ̇² = κ̇²·(1/R − 1); trace = -κ̇·(1/R + 1).
Eigenvalues (tr ± √(tr² − 4·det))/2.  Because the matrix is
column-stochastic (modulo sign) and describes a relaxation toward the
attractor Θ_1 = v_b/3, BOTH eigenvalues are real and non-positive for
R > 0.

QUESTIONS:

Q-5.1  Compare the code's 2×2 Thomson cross-coupling block with the
       Ma-Bertschinger form.  Specifically:
       (a) The code has `joint[local_row, harmonic_col] = +0.25 · γ_T / baryon_base_diag[1]`
           (off-diagonal "local ← harmonic").  Match this to +3·κ̇/R.
           Is the 0.25 constant consistent with 3/R for realistic R ≈ 0.6
           (matter-radiation equality) to R ≈ 3 (today)? Derive the
           numerical range of 3/R in the regime η ∈ [260, 14000] Mpc
           and compare.
       (b) The code has `joint[harmonic_row, local_col] = inv_t_dipole · (-0.25 · γ_T)`
           (off-diagonal "harmonic ← local").  Match this to +κ̇/3.
           Identify:
              - The SIGN.  Code is NEGATIVE; Ma-Bertschinger is POSITIVE.
                Is this a sign error?
              - The magnitude prefactor 0.25 vs 1/3.  Negligible or
                material?
       (c) Assemble the corrected 2×2 block and compute its trace and
           determinant symbolically in terms of γ_T and R.  Confirm
           both eigenvalues have Re ≤ 0.
       (d) Propose a concrete patch (in code-diff form) that replaces
           the two lines above with the Ma-Bertschinger form.  Use the
           code's `local_drag_scale` variable to carry `1/R` (Rationale:
           in FLRW, local_drag_scale = 1 ∼ O(1/R) at recombination;
           confirm this identification or flag it as an ambiguity the
           v5 §03A spec should resolve).

Q-5.2  Once the 2×2 block is correctly assembled, does the ENLARGED
       block — including the surrounding ℓ=0 and ℓ=2 rows — still have
       a positive eigenvalue for γ_T > 0?  In particular, does the
       streaming coupling A[Θ_1, Θ_0] = +k·(1/3) and A[Θ_1, Θ_2] =
       -k·(2/3) (round-1 sign flip) combine with the Thomson cross-
       coupling to create any new positive mode?  A 3×3 or 4×4 symbolic
       diagonalization should suffice; give the trace sum and rule out
       growth.

=================================================================
DEFECT ❻ — mix_t/mix_e T↔E coupling without γ_T dependence
=================================================================

CODE (build_reduced_harmonic_affine_operator, lines 1635-1636):

    mix_t = inv_t * mix_scale * structure.pstf_weight_by_slot
    mix_e = inv_e * (0.5 * mix_scale * structure.pstf_weight_by_slot)

assembled into self_block (lines 1687-1691):

    ge2_slots = slots[structure.ge2_mask]
    self_block[t_off + ge2_slots, e_off + ge2_slots] += mix_t[ge2_mask]    # T ← E
    self_block[e_off + ge2_slots, t_off + ge2_slots] += mix_e[ge2_mask]    # E ← T
    self_block[e_off + ge2_slots, b_off + ge2_slots] += eb_e[ge2_mask]     # E ← B
    self_block[b_off + ge2_slots, e_off + ge2_slots] += eb_b[ge2_mask]     # B ← E
    self_block[b_off + ge2_slots, t_off + ge2_slots] += eb_bt[ge2_mask]    # B ← T

with

    mix_scale = branch_scale * (0.08 + 0.04 * min(geom_scale, 3.0))
    eb_base   = twist_scale * structure.eb_base_by_slot
    eb_e      = inv_e * 0.75 * eb_base
    eb_b      = inv_b * (-1.0) * eb_base
    eb_bt     = inv_b * 0.25 * eb_base

REFERENCE PHYSICS (Kamionkowski-Kosowsky-Stebbins 1997; Zaldarriaga-Seljak 1997):

The polarization tensor Boltzmann hierarchy in the standard (E,B) decomposition:

    Θ̇_ℓ = k·c^-_ℓ·Θ_{ℓ-1} − k·c^+_ℓ·Θ_{ℓ+1} − κ̇·Θ_ℓ + κ̇·Π·δ_{ℓ,2}
    Ė_ℓ = k·c^-_ℓ·E_{ℓ-1} − k·c^+_ℓ·E_{ℓ+1} − κ̇·E_ℓ − κ̇·Π·√6·δ_{ℓ,2}/10
    Ḃ_ℓ = k·c^-_ℓ·B_{ℓ-1} − k·c^+_ℓ·B_{ℓ+1} − κ̇·B_ℓ

where Π ≡ Θ_2 − √6·E_2 is the polarization source.  Substituting Π
into the ℓ=2 rows gives the T↔E coupling explicitly:

    Θ̇_2 = free-streaming − κ̇·Θ_2 + κ̇·(Θ_2 − √6·E_2)/10
         = free-streaming − (9κ̇/10)·Θ_2 + (√6·κ̇/10)·E_2 · (-1)·(1/1)    ← check sign
    Ė_2 = free-streaming − κ̇·E_2 − κ̇·√6·(Θ_2 − √6·E_2)/10

So at ℓ=2, the Thomson-induced T-E coupling block is:

    [Θ̇_2]     [-(9κ̇/10)     (√6·κ̇/10)·?] [Θ_2]
    [Ė_2 ]  =  [(√6·κ̇/10)·?  ...            ] [E_2]  + streaming + ...

(signs and 1/(2ℓ+1)·something need careful rederivation).  The structural
point is that the T↔E coupling is ENTIRELY a Thomson phenomenon, so in
the limit γ_T → 0 it MUST vanish.

The code's `mix_scale = branch_scale·(0.08 + 0.04·min(geom_scale, 3))`
has NO γ_T dependence.  Therefore the code couples T and E even in the
pure free-streaming regime, which is unphysical.

QUESTIONS:

Q-6.1  Derive the correct form of mix_t, mix_e in terms of κ̇ (=γ_T in
       the code's notation), Π's coefficient, and the (2ℓ+1)·weighting
       that comes from PSTF normalization.  Show that the correct form
       is proportional to γ_T at every ℓ, and therefore vanishes at
       γ_T = 0.

Q-6.2  In the Ma-Bertschinger-compatible form, what should the sign
       structure of the T↔E coupling block be?  Specifically, should
       A[T_2, E_2] and A[E_2, T_2] carry the SAME sign (making the
       block symmetric — possibly indefinite, violating Re(λ) ≤ 0) or
       OPPOSITE signs (skew-adjoint, Re(λ) = 0) or some intermediate
       scheme constrained by the Π source algebra?

Q-6.3  Similarly for eb_e, eb_b, eb_bt (the E↔B and T↔B couplings):
       derive whether these should vanish at γ_T = 0 (i.e. B has no
       primary source in FLRW), or whether they represent a different
       physical effect (e.g. a gauge-invariance check coupling B to
       E via parity).  Flag whether `twist_scale` correctly vanishes
       for Bianchi I / FLRW (expected: yes, since twist is carried by
       the structure-constant `a` vector, which is zero for type I).

Q-6.4  Propose a concrete patch (diff form) replacing `mix_scale`,
       `mix_t`, `mix_e`, `eb_base`, and the assembly lines 1687-1691
       with the γ_T-proportional Thomson-derived form.

=================================================================
DEFECT ❼ — hand-tuned coefficients in _operator_scales
=================================================================

CODE (_operator_scales, lines 136-179):

    n_diag        = np.diag(algebra.n)              # structure-constant eigenvalues
    twist         = abs(algebra.a[0])                # structure constant a vector magnitude
    h_abs         = abs(algebra.h_parameter or 0)
    ricci_scalar  = abs(geometry.ricci_scalar)
    ricci_pstf    = geometry.ricci_pstf              # 3x3 PSTF Ricci tensor
    shear         = bg.get("sigma_tensor", 0)        # shear tensor

    geom_scale = sqrt(Σ n² + twist² + 0.25·|R_scalar| + |R_pstf|² + |σ|²)
    geom_scale = max(geom_scale, 1)

    branch_scale         = _branch_scale(bg)          # a second function; see below
    mix_scale            = branch_scale · (0.08 + 0.04 · min(geom_scale, 3))
    twist_scale          = branch_scale · twist / (1 + twist + h_abs)
    polarization_scale   = 1 + 0.35 · twist_scale
    source_scale         = 1 + 0.25 · min(|R_pstf| + |σ|, 2)

    family_law = _family_conditioned_kernel_law(bg, backend)
    return dict(
        branch_scale = branch_scale,
        geom_scale   = branch_scale · geom_scale · family_law["transport_scale"],
        mix_scale    = mix_scale · family_law["mix_scale"],
        twist_scale  = twist_scale · family_law["twist_mix_scale"],
        polarization_scale = polarization_scale · family_law["polarization_scale"],
        source_scale = source_scale · family_law["source_scale"],
        mass_scale   = family_law["mass_scale"],
        local_drag_scale = family_law["local_drag_scale"],
        cross_mode_scale = family_law["cross_mode_scale"],
        collision_scale = family_law["collision_scale"],
        mode_plus_scale = family_law["mode_plus_scale"],
        mode_minus_scale = family_law["mode_minus_scale"],
    )

and _family_conditioned_kernel_law has per-Bianchi-family entries like

    Type II:   transport_scale=1.10, mix_scale=0.92, twist_mix=0.98, polarization=1.02,
               source=0.94, local_drag=0.96, cross_mode=0.90, collision=1.03,
               mode_plus=1.02, mode_minus=0.99
    Type III:  transport=1.16, mix=1.05, twist_mix=1.02, polarization=0.96, ...
    (similar for IV, V, VI_0, VI_h, VII_0, VII_h, VIII, IX)

REFERENCE PHYSICS:

In 1+3 covariant Maartens-Ellis / Ellis-van Elst framework, the
residual-harmonic Boltzmann hierarchy in the Bianchi limit picks up
geometric couplings from:

    Θ_{A_ℓ} terms coupled via     - 1+3 shear σ_{ab}
                                  - expansion Θ = 3ℋ
                                  - vorticity ω_a (zero in Bianchi class A)
                                  - structure constants n^a_b  (algebra.n)
                                  - twist vector a^a           (algebra.a)

The PSTF tower derivative picks up terms like σ^{bc}·I_{c A_{ℓ-1}}
(shear-coupled ℓ-1 drop), a·I_{A_ℓ} (twist diagonal), n·I_{A_ℓ} (algebraic
coupling).  These are linear in σ/a/n and FIRST-PRINCIPLES DERIVABLE.

The constants 0.08, 0.04, 0.25, 0.35, 0.96, 1.02, 0.90, etc. in the
code have no such derivation.  They are placeholders.

QUESTIONS:

Q-7.1  For each of the following expressions, state whether it is
       (a) derived from first-principles Maartens-Ellis kinetic
       theory, (b) derivable but currently using placeholder
       numerical constants, or (c) entirely ad-hoc:

           geom_scale  = sqrt(Σ n² + twist² + 0.25 · |R_scalar| + |R_pstf|² + |σ|²)
           mix_scale   = branch_scale · (0.08 + 0.04 · min(geom_scale, 3))
           twist_scale = branch_scale · twist / (1 + twist + h_abs)
           polarization_scale = 1 + 0.35 · twist_scale
           source_scale = 1 + 0.25 · min(|R_pstf| + |σ|, 2)

       For (a) items, confirm the coefficient is correct.  For (b),
       identify the correct symbolic form and flag the numerical
       constants that should be replaced with physical values.  For
       (c), state so explicitly and recommend removal or rederivation
       under v5 §03A.

Q-7.2  Review the 10-parameter _family_conditioned_kernel_law per
       Bianchi family (II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII,
       IX).  Each parameter differs by 1-16% from the Type-I reference.
       Are these (a) physical rescalings of Maartens-Ellis structure
       coupling constants for each algebra (in which case their values
       should be computable from the structure constants), or (b)
       numerical tuning to match observational anchors for each family
       (in which case they are empirical parameters, not derived)?
       If (a), derive the correct Type-II and Type-III values from
       structure constants and compare to the code's values.

Q-7.3  In the FLRW limit (Bianchi I, β=0, no shear, no twist), ALL of
       geom_scale, mix_scale, twist_scale, source_scale should reduce
       to specific limiting values.  What are they?  Does the code
       match?  For example, with |σ| = |n| = twist = ricci = 0,
       geom_scale = max(0, 1) = 1; then mix_scale = 0.08 + 0.04·1 =
       0.12 (NONZERO, but should be zero in free-streaming FLRW!).
       Derive the consistent FLRW reduction and identify each
       coefficient that reduces to zero vs. nonzero.

Q-7.4  Minimal patch (diff).  With ❺❻❼ simultaneously fixed, does the
       FLRW-limit A_right have λ_max = 0 (purely imaginary free-
       streaming spectrum)?  Predict the expected value and, if
       nonzero, identify the residual physics (is it polarization
       relaxation to quadrupole, CDM free-streaming, neutrino
       decoupling, ...)?

=================================================================
OUTPUT FORMAT
=================================================================

Return your answer as a single markdown document with these sections:

    ## Q-5.1 — local ↔ harmonic Thomson coupling coefficients and signs
    ## Q-5.2 — full 3×3 / 4×4 block stability with corrected coupling
    ## Q-6.1 — correct T↔E mix_t / mix_e form (γ_T-proportional)
    ## Q-6.2 — sign structure of T↔E coupling
    ## Q-6.3 — eb_*  (E↔B, T↔B) and twist_scale in FLRW limit
    ## Q-6.4 — minimal patch for ❻
    ## Q-7.1 — taxonomy of _operator_scales formulas
    ## Q-7.2 — family_conditioned_kernel_law per-family deviations
    ## Q-7.3 — FLRW reduction of _operator_scales
    ## Q-7.4 — minimal patch for ❼ and expected post-patch spectrum

Each section must show the algebra explicitly. If a question cannot be
answered without v5 §03A/§03B specification content, say so precisely;
do not guess.  A single "this is a placeholder, needs v5 spec derivation"
is an acceptable and useful answer for a given coefficient.

CRITICAL CONSTRAINT:  The FLRW D_2 = 1002.086744 μK² regression anchor
is bit-identical through four prior patches.  This implies r_h(η_0) = 0
and b_hh(η) ≡ 0 hold algebraically on the FLRW invariant manifold.
Any patch you propose must NOT change b_hh(η) in the FLRW limit —
matrix-structure changes to A are safe, bias changes are not.
```

---

## After Claude answers

The round-2 answer will likely give 4 patches (one per defect).  Apply them in order ❺ → ❻ → ❼ with the same two-step validation after each:

```bash
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/v5_operator_fast_check.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -m pytest htt/bass/validation/test_d2_regression_anchor.py -q
```

Success criterion per-step: `λ_max` monotonically decreases toward zero (both γ_T=0 and γ_T=1 branches), D_2 anchor stays bit-identical. If any step breaks bit-identity, that step's patch touched `b_hh` in the FLRW limit (not matrix-only) and must be revised.

Once all three defects are closed, re-run the long-form verification:

```bash
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/v5_runtime_spectral_audit.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/v5_runtime_operator_forensics.py
```

Success: `λ_max(η) < 1e-10` across all 5 η snapshots, `|W A + A^T W|/|W A| < 1e-10` per channel, L_max sweep stays within round-off.
