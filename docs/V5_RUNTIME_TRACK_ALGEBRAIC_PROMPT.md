# Algebraic Audit Prompt — V5 Residual-Harmonic Operator Sign/Formulation Derivation

_Self-contained prompt for a fresh Claude session (API or chat). No repo access needed; all relevant code is embedded inline._

Copy the section under **"PROMPT FOR CLAUDE"** verbatim into a fresh session. All context Claude needs to answer algebraically is inside that section.

---

## Why this prompt exists

A Python-side instrumented audit localized a cosmological-range ODE divergence in the BASS Tier-B integrator to a **symmetric harmonic-block operator with a `+0.175 / Mpc` real eigenvalue**, confirmed across L_max ∈ {4,6,8,12,16} and 5 η snapshots. The local compute environment cannot rerun the D_2 bit-identity regression in an acceptable wall-clock budget, so the remaining derivation has to be done analytically.

Two findings must now be decided by pen-and-paper / symbolic manipulation rather than numerical sweep:

1. **Sign structure of the `prev_ℓ ↔ next_ℓ` coupling.** The code emits both couplings with positive signs (symmetric matrix). A free-streaming Boltzmann hierarchy operator is antisymmetric. Is flipping the `next_coeff_by_slot` sign (so `A_hh` becomes skew-symmetric in its streaming block) the correct FLRW-limit shape, and does it preserve the FLRW `D_2 = 1002.086744 μK²` anchor?

2. **Physical interpretation of `diag_base_by_slot = 0.35·(ℓ+1) + 0.08·|m|`.** This is a hand-chosen constant with no derivation in tree. Is it meant to represent Maartens-Ellis 1+3 covariant damping, a `(ℓ+1)/(2ℓ+1)` streaming coefficient that was hand-merged into the diagonal, or pure numerical stiffening? Whichever it is, what is the **correct** form in the FLRW limit where the residual-harmonic block should reduce to a known free-streaming problem?

The prompt below gives Claude everything it needs to answer both without running code.

---

## PROMPT FOR CLAUDE

```
You are a physics auditor for a CMB Boltzmann solver. You will not run any
code. All input is algebraic and all output must be algebraic / symbolic
(with sign verification and eigenvalue reasoning). A previous audit already
established the numerical symptoms below; your job is to derive the
formulation-level fix.

=================================================================
CONTEXT
=================================================================

The codebase is BASS, a Bianchi-anisotropic CMB Boltzmann solver written
in Python. Its Tier-B "residual-joint" integrator decomposes the
photon/polarization/neutrino hierarchy into three blocks per residual
mode label μ:

    residual_local       (baryon + CDM local DOFs per μ)
    residual_harmonic    (T, E, B, ν harmonic slots indexed by (ℓ, m) per μ)
    residual_source      (source-propagator local DOFs per μ)

and advances them by solving

    d/dη [ r_local, r_harm, r_src ]^T = A_right · [ r_local, r_harm, r_src ]^T + b(η)

with A_right and b assembled from a frozen snapshot of primary radiation
state (photon_T, photon_E, photon_B, ν, baryon, source) at time η.

The design intent: "residual" captures the departure of each mode label μ
from the "covered" mode (which absorbs the dominant axis-aligned FLRW
content). In the FLRW limit (Bianchi I, β = 0, tilt off), the residual
blocks carry ZERO physical content — every residual state is identically
zero — and A_right · 0 + b(η) must deliver RHS ≡ 0 as well.

=================================================================
OBSERVED SYMPTOMS (from the Python-side audit)
=================================================================

At η ∈ [300, 500] Mpc (well after recombination, post-photon-decoupling),
scipy.sparse.linalg.eigs(A_right, k=6, which="LR") on the L_max=8 FLRW
run (Bianchi I, β=0) returns the following largest real-part eigenvalues:

    η (Mpc) | top-6 Re(λ)                                | λ_max_right_eigvec harmonic-block weight
    300.4   | 0.190, 0.190, 0.174, 0.174, 0.169, 0.169   | 1.000
    350.2   | 0.176, 0.176, 0.161, 0.161, 0.156, 0.156   | 1.000
    400.2   | 0.175, 0.175, 0.160, 0.160, 0.155, 0.155   | 1.000
    450.1   | 0.175, 0.175, 0.160, 0.160, 0.155, 0.155   | 1.000
    500.2   | 0.175, 0.175, 0.160, 0.160, 0.155, 0.155   | 1.000

The left eigenvector of λ_max is ALSO 1.000 concentrated on the harmonic
block. An FD Jacobian check established |A - J_fd|_F / |A|_F ≈ 1.6e-13,
so A_right is a true linear operator — no hidden nonlinearity.

L_max sweep at η ≈ 350 Mpc:

    L_max | λ_max
    4     | +0.17574
    6     | +0.17582
    8     | +0.17582
    12    | +0.17582
    16    | +0.17582

λ_max is invariant under L_max (rules out truncation/reflecting-boundary).

Symmetry decomposition of the harmonic block A_hh (rows/cols of A_right
that act on residual_harmonic):

    |sym(A_hh)|_F  / |A_hh|_F  = 0.999
    |skew(A_hh)|_F / |A_hh|_F  = 0.038
    eig(sym(A_hh)) ∈ [-2.93, +0.27]

A_hh is 99.9 % symmetric, and its symmetric part has a positive
eigenvalue. For any physical photon-transport operator this is
impossible (free-streaming is skew-symmetric / purely imaginary
spectrum; Thomson dissipation is symmetric negative-semidefinite).

=================================================================
THE SUSPECT CODE (verbatim excerpts from
bass/hierarchy/ver3_layout_protocol.py)
=================================================================

--- SLOT STRUCTURE (_reduced_harmonic_structure, lines 489-533) ---

For each slot (ell, m) with 0 ≤ ℓ ≤ L_max and -ℓ ≤ m ≤ +ℓ:

    diag_base_by_slot[slot]       = 0.35 * (ell + 1) + 0.08 * abs(m)
    collision_factor_by_slot[slot] = 1.0 if ell <= 1 else 1.0 / (ell + 0.5)

    if ell > 0:
        prev_coeff_by_slot[slot]
            = sqrt( max(ell**2 - m**2, 0.0) ) / max(2*ell + 1, 1)

    if ell < L_max:
        next_coeff_by_slot[slot]
            = sqrt( max((ell+1)**2 - m**2, 0.0) ) / max(2*ell + 1, 1)

--- OPERATOR ASSEMBLY (build_reduced_harmonic_affine_operator, lines
1605-1676) ---

    ell_weight = 1.0 + 0.04 * ell_by_slot + 0.015 * geom_scale
    inv_t  = 1.0 / max( branch_scale * ell_weight, 1e-30 )
    inv_e  = 1.0 / max( branch_scale * (1.08 * polarization_scale) * ell_weight, 1e-30 )
    inv_b  = 1.0 / max( branch_scale * (1.12 + 0.5*twist_scale) * polarization_scale * ell_weight, 1e-30 )
    inv_nu = 1.0 / max( (1.0 + 0.1 * branch_scale + 0.02 * geom_scale) * ell_weight, 1e-30 )

    stream_base = geom_scale * diag_base_by_slot
    photon_coll = branch_scale * collision_scale * gamma_t * collision_factor_by_slot

    diag_t  = inv_t  * ( -stream_base + photon_coll )
    diag_e  = inv_e  * ( -stream_base * polarization_scale + photon_coll )
    diag_b  = inv_b  * ( -stream_base * polarization_scale + photon_coll )
    diag_nu = inv_nu * ( -stream_base )

    prev_t      = inv_t  * geom_scale                                      * prev_coeff_by_slot
    next_t_same = inv_t  * geom_scale                                      * next_coeff_by_slot
    prev_e      = inv_e  * geom_scale * polarization_scale                 * prev_coeff_by_slot
    next_e_same = inv_e  * geom_scale * polarization_scale                 * next_coeff_by_slot
    prev_b      = inv_b  * geom_scale * polarization_scale                 * prev_coeff_by_slot
    next_b_same = inv_b  * geom_scale * polarization_scale                 * next_coeff_by_slot
    prev_nu     = inv_nu * geom_scale                                      * prev_coeff_by_slot
    next_nu_same= inv_nu * geom_scale                                      * next_coeff_by_slot

Then the self-block is populated (showing T-channel only; E, B, ν
identical structure):

    self_block[t_off + slots,                              t_off + slots                          ] += diag_t                       # diagonal
    self_block[t_off + slots[prev_valid], t_off + prev_slot_by_slot[prev_valid]] += prev_t[prev_valid]      # T_ell ← T_{ell-1}
    self_block[t_off + slots[next_valid], t_off + next_slot_by_slot[next_valid]] += next_t_same[next_valid] # T_ell ← T_{ell+1}

Both prev and next couplings enter with POSITIVE signs (+=). This makes
the streaming part of the matrix symmetric under (ℓ, ℓ') → (ℓ', ℓ)
because

    A[T_ℓ, T_{ℓ-1}]  =  inv_t_[ℓ]  · geom_scale · sqrt(ℓ²    - m²) / (2ℓ  + 1)
    A[T_{ℓ-1}, T_ℓ]  =  inv_t_[ℓ-1]· geom_scale · sqrt(ℓ²    - m²) / (2ℓ-1)

and these differ only by the (inv_t_ℓ / inv_t_{ℓ-1}) ratio, which is
close to 1 for all ℓ, so the skew part is tiny (matches the observed
3.8 %) and the sym part dominates (matches 99.9 %).

=================================================================
REFERENCE PHYSICS
=================================================================

Standard photon Boltzmann hierarchy in the FLRW k-mode basis (Ma and
Bertschinger 1995, eq. 63-64; Dodelson "Modern Cosmology" eq. 8.79;
CMBFAST source):

    Θ̇_ℓ = k · [ ℓ/(2ℓ+1) · Θ_{ℓ-1}  −  (ℓ+1)/(2ℓ+1) · Θ_{ℓ+1} ]  − τ̇ · Θ_ℓ + S_ℓ

    ℓ ≥ 1    (monopole ℓ=0 is coupled to metric via continuity)
    τ̇ = -a·n_e·σ_T   (Thomson opacity)
    S_ℓ = source terms (dipole: baryon velocity; quadrupole: polarization)

The PREV and NEXT streaming coefficients carry OPPOSITE SIGNS:
    +ℓ/(2ℓ+1) for T_{ℓ-1}
    -(ℓ+1)/(2ℓ+1) for T_{ℓ+1}

This is a consequence of integrating the Liouville operator k·μ over
the Legendre decomposition: k·μ P_ℓ = [ℓ/(2ℓ+1)] P_{ℓ-1} + [(ℓ+1)/(2ℓ+1)]
P_{ℓ+1}, and d/dη Θ_ℓ picks up the opposite sign on the P_{ℓ+1} term
because of the direction of free-streaming photon flow.

The resulting tridiagonal matrix (in the ℓ index, m=0) is
ANTISYMMETRIC up to the normalization factor (2ℓ+1)/(2ℓ-1), so its
eigenvalues are purely imaginary — the solution is oscillatory.

In the code above, the `sqrt(ℓ² - m²)/(2ℓ+1)` and
`sqrt((ℓ+1)² - m²)/(2ℓ+1)` forms are the m-generalizations of
ℓ/(2ℓ+1) and (ℓ+1)/(2ℓ+1) via Clebsch-Gordan reduction of k·Y_ℓ^m,
so the structural intent is clear: these ARE meant to be streaming
coefficients. What is missing is the sign flip on next_coeff.

=================================================================
QUESTIONS FOR YOU TO ANSWER ALGEBRAICALLY
=================================================================

Q1  Confirm or refute: in the FLRW (Bianchi I, β=0) limit, the correct
    streaming-block assembly is

        self_block[..., t_off + prev_slot[...]] +=  prev_t[...]      # unchanged
        self_block[..., t_off + next_slot[...]] -=  next_t_same[...] # SIGN FLIP

    and this makes the harmonic block skew-symmetric up to (inv_t_ℓ)
    per-row scaling. Show the algebra that connects this code change to
    the Ma-Bertschinger reference equation above. If the current
    inv_t_ℓ per-row scaling breaks strict skew-symmetry even after the
    sign flip, quantify the residual symmetric part and say whether it
    is damping (negative eigenvalue) or growth (positive eigenvalue).

Q2  Algebraically derive: after the sign flip on ALL four (T/E/B/ν)
    next couplings, and setting γ_T = 0 (post-recombination), what is
    the largest real part of the eigenspectrum of the harmonic block?
    You do not need to diagonalize; a Gershgorin / Bauer-Fike bound is
    sufficient. In particular, is Re(λ_max) ≤ 0 guaranteed?

Q3  Explain the physical content of diag_base_by_slot = 0.35·(ℓ+1) +
    0.08·|m|. Against the Ma-Bertschinger reference (which has no
    diagonal self-damping in free-streaming), either:
       (a) identify which physical effect this is meant to encode
           (e.g. an ad-hoc 1+3 covariant expansion-damping term, a
           mis-merged Liouville expansion, a PSTF projection
           correction), OR
       (b) conclude it is a non-physical regularization and should be
           set to zero in the FLRW limit.
    If (a), write the correct coefficient in terms of ℓ, m, and any
    required background quantities (H, ℋ = a·H, k). If (b), explain
    why the short-window tests do not see this as a bug.

Q4  Do the same for the ell_weight formula:
        ell_weight = 1.0 + 0.04 · ℓ + 0.015 · geom_scale
    The inv_t = 1/(branch_scale · ell_weight) scaling means each row of
    the streaming operator is weighted by a placeholder time-scale. In
    the FLRW limit geom_scale → geom_scale_FLRW (pure Hubble magnitude)
    and branch_scale → 1. Identify what physical time-scale (per ℓ) the
    code is trying to imitate, and whether the 0.04·ℓ rise and 0.015
    geom_scale offset are derivable or hand-tuned.

Q5  FLRW D_2 bit-identity preservation.
    The regression anchor is D_2 = 1002.086744 μK². This is the Tier-B
    LoS-integrated result at ℓ = 2, computed via the "covered-mode"
    channel (not the residual-harmonic channel). In the FLRW limit the
    residual_harmonic state is identically zero throughout the
    integration interval. Therefore:

        residual_harmonic_rhs(η) = A_right_hh(η) · 0 + b_hh(η)
                                 = b_hh(η)

    and the D_2 output is sensitive ONLY to b_hh(η), not to the matrix
    structure of A_right_hh(η). State (yes/no) whether this reasoning
    implies that ANY change to the A_right_hh matrix structure is
    guaranteed to preserve the FLRW D_2 anchor bit-identically, as long
    as b_hh(η) is unchanged. If yes, show the algebra. If no, identify
    the specific path through which an A_right_hh change could leak
    into the covered-mode D_2 computation.

Q6  Propose a concrete, minimal patch (in diff form) to
    build_reduced_harmonic_affine_operator that:
       - applies the Q1 sign flip
       - sets diag_base_by_slot → 0 if Q3 concludes (b)
       - leaves ell_weight alone if Q4 concludes hand-tuned
       - includes a one-line assertion that the resulting A_hh is
         skew-symmetric at γ_T = 0 to machine precision (or, if not
         exactly skew, that its symmetric part has eig_max ≤ 0)

    Confirm by Q5 that this patch is safe against the D_2 bit-identity.

=================================================================
OUTPUT FORMAT
=================================================================

Return your answer as a single markdown document with these sections:

    ## Q1 — prev/next sign flip
    ## Q2 — post-flip eigenvalue bound
    ## Q3 — diag_base_by_slot interpretation
    ## Q4 — ell_weight interpretation
    ## Q5 — FLRW D_2 bit-identity preservation
    ## Q6 — minimal patch

Each section must show the algebra explicitly. No code execution is
allowed; all claims must be defensible from the equations you write
down. If a question cannot be answered without further information,
state precisely what input you need (e.g. "the visibility_amplitude
time-dependence in FLRW limit") rather than guessing.
```

---

## Usage notes

- Send as-is to a fresh Claude session. Do not prepend repo-specific history; the prompt is self-contained.
- The answer Claude produces is a derivation, not executable code. Validate Q1 and Q6 by hand before accepting the diff, and separately validate Q5 by running the D_2 anchor tests locally (which take < 2 s in this repo; it is the *full* regression run that is slow).
- If Claude flags that Q3 or Q4 requires more context, paste the relevant section of `docs/bianchi_design_pack_v5/` into a follow-up turn. The spec §03A and §03B are the authoritative references for the residual decomposition.

## After Claude answers

Once Q1/Q5 are confirmed (sign flip safe for D_2), the patch in Q6 can be applied and validated locally in three short commands:

```bash
# 1. Apply the Q6 diff to bass/hierarchy/ver3_layout_protocol.py
# 2. Re-run operator forensics — should show skew-symmetric harmonic block
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/v5_runtime_operator_forensics.py
# 3. Re-run D_2 anchor — should stay bit-identical at 1002.086744 μK²
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -m pytest bass/validation/test_d2_regression_anchor.py -q
```

If (2) shows `|skew(A_hh)|/|A_hh| > 0.9` and `sym_eig_max(A_hh) < 0`, and (3) stays green, the operator fix is validated without needing the full Tier-B regression run. The full-suite run can then be queued as a background task or deferred to a session with more CPU budget.
