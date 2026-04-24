# Algebraic Audit Prompt — Round 4

_Self-contained prompt for a fresh Claude session. No repo access; all code and physical data inline._

This is the follow-up to Rounds 1, 2, 3. Round 3 delivered the
matrix-valued kernel API (`FamilyKernelPack` +
`_family_conditioned_kernel_operator`) for Tier-A families (I, II, III,
V, VII₀, VIII), with μ-space signature matrices (Q-8.2) and transport-
matrix shapes (Q-8.3). **Six substantive items were left as "requires
v5 spec" or as unevaluated formulas**, and the kernel pack is not
wired into the residual-joint assembly because those items block a
physically complete assembly.

Round 4 closes those six items with concrete, evaluable forms. The
fresh auditor should not need any v5 §03A/§03B text beyond what is
inlined here; all physics context, all relevant literature pointers,
and all canonical/code data are provided in-line below. The goal is
turn-key numerical expressions (closed-form or small look-up tables)
that a patch can paste directly into the kernel pack.

Paste the block under **"PROMPT FOR CLAUDE"** into a fresh session and
forward the answer back for patching.

---

## Residual items this round targets

After Round 3 the kernel pack is structurally complete but has four
substantive placeholders and two unconfirmed conventions. In priority
order:

- **❿ `q_h` for Type VII₀ helical partners** — the helical-plane
  transport eigenvalue. Round-3 Q-8.3 returned `Q_{VII₀} = diag(q_0, q_h, q_h)`
  with `q_h` flagged as requiring the v5 §03A helical-basis card.
- **⓫ `ζ_R` for class-B `R_μ` correction** — O(|a|²) baryon-photon
  ratio anisotropy from tilt-coupling. Round-3 Q-8.5(a) flagged this
  as requiring the v5 background tilt closure.
- **⓬ `ζ_M` for class-B mass correction** — O(|a|²) anisotropic
  mass drag from Tr(σ·n) projection. Round-3 Q-8.5(b) flagged this
  as requiring the v5 shear closure.
- **⓭ Wigner-3j numerical evaluation of `twist_mix_kernel`** —
  Q-8.4(c) provided the closed form `|a| · Σ_q a_q · Wigner(ℓ,1,ℓ';m,q,m') · Wigner(ℓ,1,ℓ';-2,0,2)`
  but did not numerically evaluate the 3-j symbol table.
- **⓮ (confirmation) Sector similarity `S_{e,b,ν}`** — Round-3
  Q-8.6(b) asserted `μ_mode_coupling_e = μ_mode_coupling_t` (identity
  similarity in μ-space) if storage basis uses uniform normalization.
  Round 4 should confirm this from the ℓ-dependent PSTF row scaling
  conventions already frozen in the code.
- **⓯ (confirmation) Π_μ^α projector** — Round-3 Q-8.2 wrote
  `Π = I` for the canonical `(μ_0, μ_+, μ_-)` basis but noted that
  families with non-canonical axis ordering need an explicit Π. The
  code has `BianchiAlgebra.axis_permutation` already; Round 4 should
  either confirm this permutation is Π or derive the correct form.

Items ❿-⓭ are substantive and require first-principles derivation.
Items ⓮-⓯ are confirmations (auditor should state pass/fail on the
proposed forms and correct them if wrong).

---

## PROMPT FOR CLAUDE

```
You are a physics auditor for a CMB Boltzmann solver (BASS)
implementing the 1+3 covariant PSTF hierarchy for all 10 Bianchi
families. You will not run any code; all input is algebraic or
symbolic and all output is algebraic or a small numerical table. The
FLRW D_2 = 1002.086744 μK² regression anchor is bit-identical through
8 prior physics patches; any formulas you produce must preserve
b_hh ≡ 0 in the Type-I limit (a = 0, n = 0).

Rounds 1-3 of this audit (prompts V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT.md,
..._ROUND2.md, ..._ROUND3.md; answers
v5_residual_harmonic_algebraic_audit[_round2/3].md) have:

  1. Fixed the free-streaming sign flip (Q1), the diag_base
     SO(3)-violating placeholder (Q3), and the local+harmonic
     Thomson-damping signs (Option-B harmonic/local).
  2. Fixed the T↔E quadrupole-only Thomson coupling (Q-5.1 + Q-6.4)
     and the local↔harmonic cross-coupling with the Ma-Bertschinger
     form ±3κ̇/R and +κ̇/3.
  3. Neutralized the hand-tuned scalar surrogates `mix_scale → 0`,
     `polarization_scale → 1`, `source_scale → 1`, and fixed the
     source-block diagonal sign.
  4. Derived the matrix-valued μ-mode coupling for five Tier-A
     families. The Round-3 API landed as a dormant FamilyKernelPack
     with canonical unit-normalized signatures:
         Type I:      mu_mode_coupling_t = 0                      (3×3)
         Type II:     diag(1, 0, 0)    rank-1 nilpotent
         Type III:    diag(1, 1, -1)   semisimple + twist
         Type V:      diag(1, 0, 0)    pure twist
         Type VII₀:   diag(0, 1, 1)    helical anchor
         Type VIII:   diag(-1, 1, 1)   semisimple full-rank
     The other fields (transport, twist_mix_kernel, local_drag_by_mu,
     mass_by_mu) are placeholder identity / zero / ones until Round 4
     closes the remaining formulas below.

Round 4 closes four substantive placeholders (q_h, ζ_R, ζ_M,
Wigner-3j numerical table) and confirms two conventions (channel
similarity S_{e,b,ν}, axis projector Π).

=================================================================
DATA AVAILABLE TO YOU
=================================================================

BIANCHI ALGEBRA (frozen VER2 convention; from code schema):

    @dataclass(frozen=True)
    class BianchiAlgebra:
        type_name: str
        a: np.ndarray               # shape (3,)
        n: np.ndarray               # shape (3,3), symmetric
        C: np.ndarray               # shape (3,3,3), C^γ_{αβ}
        h_parameter: float | None
        class_label: "A" | "B"
        axis_permutation: tuple     # (0,1,2) for class A; (1,0,2) for class B
                                    # = Pontzen-Challinor → VER2 class-B axis swap

    Canonical gauge values (from v5 §03B), with the overall numerical
    normalization scale 0.01 used in the code:

    | Type   | diag(n) in code       | a in code      | |a|    | h        |
    |--------|----------------------|----------------|--------|----------|
    | I      | (0, 0, 0)            | (0, 0, 0)      | 0      | —        |
    | II     | (0.01, 0, 0)         | (0, 0, 0)      | 0      | —        |
    | III    | (0, 0.01, -0.01)     | (0.01, 0, 0)   | 0.01   | -1       |
    | IV     | (0, 0, 0.01)         | (0.01, 0, 0)   | 0.01   | —        |
    | V      | (0, 0, 0)            | (0.01, 0, 0)   | 0.01   | —        |
    | VI_0   | (0, 0.01, -0.01)     | (0, 0, 0)      | 0      | —        |
    | VI_h   | (0, 0.01, -0.01)     | (√|h|·0.01, 0, 0) | |a|  | h<0      |
    | VII_0  | (0.01, 0, 0.01)      | (0, 0, 0)      | 0      | —        |
    | VII_h  | (0.01, 0, 0.01)      | (√h·0.01, 0, 0) | |a|   | h>0      |
    | VIII   | (-0.01, 0.01, 0.01)  | (0, 0, 0)      | 0      | —        |
    | IX     | (0.01, 0.01, 0.01)   | (0, 0, 0)      | 0      | —        |

    Note: the 0.01 magnitude is a backend normalization — all
    structural signatures (signs, ranks, degeneracy patterns) are
    preserved. In particular, Type VII₀ has TWO degenerate eigenvalues
    +0.01 on axes 1 and 3 and a zero on axis 2, which is a swap of
    the v5 §03B "canonical" ordering diag(0, 1, 1). This is exactly
    what axis_permutation is for.

FAMILY MODE LABELS (canonical ordering in code):

    Type I:       (m0, m+2, m-2)
    Type II:      (mu_nil, mu_nil+, mu_nil-)
    Type III:     (mu_hyp, mu_hyp+, mu_hyp-)
    Type V:       (mu_open, mu_open+, mu_open-)
    Type VI_0:    (mu_vi0, mu_vi0+, mu_vi0-)
    Type VII_0:   (mu_hel, mu_hel+, mu_hel-)
    Type VII_h:   (mu_hel_h, mu_hel_h+, mu_hel_h-)
    Type VIII:    (mu_sl2r, mu_sl2r+, mu_sl2r-)
    Type IX:      (mu_compact, mu_compact+, mu_compact-)

FAMILY KERNEL PACK (Round-3, current shape):

    @dataclass(frozen=True)
    class FamilyKernelPack:
        family: str
        mode_labels: tuple[str, ...]
        transport: np.ndarray                        # (mu_count, mu_count)
        mu_mode_coupling_{t,e,b,nu}: np.ndarray      # (mu_count, mu_count)
        twist_mix_kernel: np.ndarray                 # (ell_max+1, 2*ell_max+1, 2, 2)
        local_drag_by_mu: np.ndarray                 # (mu_count,)
        mass_by_mu: np.ndarray                       # (mu_count,)
        collision: float                             # scalar, = 1.0

PSTF ROW WEIGHT (already frozen in code):

    pstf_weight(ell) = sqrt((ell+2)·(ell-1)) / (2ell+1)    for ell ≥ 2
                     = 0                                    for ell ≤ 1

    d^(X)_ell conventions (from Ma-Bertschinger + KKS):
        T:   d^(T)_ell   = 2ell + 1                         (scalar)
        E,B: d^(E,B)_ell = (2ell+1) · pstf_weight(ell)      (spin-2)
        nu:  d^(nu)_ell  = 2ell + 1                         (scalar)

    Streaming row scaling: W^(X)_ell = (2ell+1) / d^(X)_ell
    (Round-1 weighted skew-adjointness invariant).

FLRW / TYPE I LIMIT CONSTRAINT:

    In Type I: a = 0, n = 0. Every μ-mode matrix in the kernel pack
    must collapse to the zero matrix, and every ℓ-dependent coupling
    (Wigner-3j table, R_μ correction, mass correction) must collapse
    to its isotropic FLRW value. The D_2 anchor is bit-identical
    through Rounds 1-3 and must remain so.

=================================================================
DEFECT ❿ — q_h for Type VII₀ helical partners
=================================================================

CURRENT STATE (Round-3 Q-8.3):

    Q_{VII₀} = diag(q_0, q_h, q_h)     (3×3 in μ-space)

    q_0 is the anchor eigenvalue; q_h is the shared helical-partner
    eigenvalue (equal by μ_+ ↔ μ_- parity on the cos/sin real basis).

PHYSICS CONTEXT:

Type VII₀ is a class-A Bianchi model with structure constants
    C^1_{23} = −C^1_{32} = 1,    C^3_{12} = −C^3_{21} = 1
(in canonical VER2 axes; modulo the (0.01) scale this matches n =
diag(1, 0, 1)). The third axis forms an Abelian R factor; the first
and third axes carry an SO(2) helical rotation with infinitesimal
generator mixing them. Wave modes on a Type VII₀ homogeneous slice
decompose as

    ψ(x) = e^{i(k₁x₁ + k₃x₃)} · f(x₂; k₁, k₃)

with a SPIRAL-TWISTED harmonic structure along x₂ coming from the
helical generator. The scalar Laplacian on the spacelike slice reads
(in the synchronous tetrad, canonical gauge)

    Δ ψ = (k₁² + k₃² + k²_{twist}) · ψ,

where k²_{twist} is a DISCRETE shift from the helical generator's
commutator and equals +1 in canonical units for the helical partner
modes (v5 §03B's ν̇_{VII_h}(k) = |k| reduces to the same form with
p = 0 as VII_h → VII₀).

Real-cos/sin basis decomposition: the complex eigenmode
    ψ_k = e^{iφ} · [rotated harmonic]
splits into real (cos) and imaginary (sin) parts; these are the
μ_+ / μ_- helical partners and are energy-degenerate.

REFERENCES:

  - Wainwright & Ellis (1997), "Dynamical Systems in Cosmology",
    Chapter 7 (Bianchi VII₀ helical mode structure).
  - Pontzen (2009) MNRAS 396, "Rogues' gallery: the full freedom of the
    Bianchi CMB anomalies" — explicit VII₀ mode labels.
  - Pereira, Pitrou, Uzan (2007) JCAP 2007:09 — helical vector-mode
    transport in anisotropic backgrounds.
  - Gumrukcuoglu, Contaldi, Peloso (2007) JCAP 2007:11 — Bianchi VII₀
    perturbation spectra.
  - v5 §03B table for Type VII_h: ν̇_{VII_h}(k) = |k|, ρ = e^{-2pr}|k|
    with p = √h, limiting to VII₀ at p = 0.

QUESTION Q-10:

Q-10.1  Derive q_0(k) and q_h(k) as explicit closed forms.

        Expected output:
            q_0(k) = f_0(k₁, k₃)
            q_h(k) = f_h(k₁, k₃, twist_eigenvalue)

        The twist_eigenvalue is the non-zero eigenvalue of the n
        matrix restricted to the helical plane (eigenvalue +1 in
        canonical units).

        Specifically, identify whether q_h takes the form:
            (a) q_h = sqrt(k₁² + k₃² + 1)    (helical supercurvature)
            (b) q_h = sqrt(k₁² + k₃²) + ε    (helicity phase shift)
            (c) q_h = k_⊥·exp(-pr) with p=0  (Pontzen-Challinor VII_h limit)
            (d) some other form

        Cite the derivation (which reference, which equation).

Q-10.2  Specialize to the dimensionless scalar case: what is q_h in
        units of |k|? For integration against the Plancherel
        measure, does q_h saturate to |k| at large k or approach
        some fixed non-zero asymptote?

Q-10.3  Real-basis explicit form: in the (μ_hel, μ_hel+, μ_hel-)
        storage basis the three eigenvalues are (q_0, q_h, q_h)
        (degenerate real pair). Confirm that:
            transport_VII₀(k) = diag(q_0(k), q_h(k), q_h(k))
        is a valid 3×3 real diagonal matrix for all k ≥ 0 (no
        complex eigenvalues, no degeneracies above k = 0).

Q-10.4  Give the FLRW (Type I) limit check: as n → 0 (helical
        eigenvalue → 0), q_h → q_0 → |k|, recovering the isotropic
        transport. Confirm this limit explicitly.

=================================================================
DEFECT ⓫ — ζ_R for class-B R_μ correction
=================================================================

CURRENT STATE (Round-3 Q-8.5(a)):

    local_drag_by_mu = R_μ^{-1} ≈ R^{-1} · [1 + ζ_R · |a|² · (ê_a · e_μ)²]

    ζ_R requires the v5 background tilt closure: how do ρ_{γ,μ} and
    ρ_{b,μ} project onto the μ-basis for a class-B family with tilt
    vector v^α coupled to a^α?

PHYSICS CONTEXT:

Ratio R = 4ρ_γ / (3ρ_b). In FLRW, isotropic and μ-independent. In
class-B Bianchi with tilt, the baryon and photon momenta pick up
anisotropic corrections from the tilt 3-velocity v^α satisfying

    D_α v^α = -a^α · v_α   (Codazzi constraint in class B)

The linearized tilt expansion gives

    ρ_{γ,μ}(η) = ρ_γ(η) · [1 + δ_γ,μ(η) · (ê_a · e_μ)],
    ρ_{b,μ}(η) = ρ_b(η) · [1 + δ_b,μ(η) · (ê_a · e_μ)],

where δ_γ,μ and δ_b,μ are species-specific tilt amplitudes. These
enter R_μ as

    R_μ^{-1} = (3ρ_b/4ρ_γ) · [1 + (δ_b,μ - δ_γ,μ) · (ê_a · e_μ)] + O((ê·e)²).

The LINEAR term vanishes in the real (cos, sin) partner basis by
parity (μ_+ and μ_- carry opposite signs), so only the QUADRATIC
term O(|a|²·(ê·e)²) survives in the μ-diagonal. The coefficient
ζ_R is the ratio of δ-coefficients.

REFERENCES:

  - Maartens, Triginer, Ellis (1999) PRD 60 023502 — covariant
    multicomponent fluid in nearly-FLRW (supplies the tilt projection
    formulas).
  - Lim, Coley, Wainwright, Maartens (2004) PRD 69 103507 — second-
    order anisotropy in Bianchi class B.
  - Ma & Bertschinger (1995) eq. 29 for R(η).
  - Pontzen & Challinor (2011) JCAP 2011:05 — explicit tilt-species
    coupling in Bianchi CMB.

QUESTION Q-11:

Q-11.1  Derive δ_γ,μ and δ_b,μ from the linearized tilt closure:
        for a class-B family with a^α aligned along axis 1, what
        are the species-density perturbations at O(|a|)?

        Expected output: closed-form expressions in terms of
        background (H, Ω_γ, Ω_b, a^α components) and the tilt
        vector v^α.

Q-11.2  Compute the RATIO (δ_b,μ - δ_γ,μ) / (some normalization)
        and express R_μ^{-1} as

            R_μ^{-1} = R^{-1} · [1 + ζ_R · |a|² · (ê_a · e_μ)² + O(|a|⁴)]

        where ê_a = a / |a| and e_μ is the μ-th canonical axis.
        Identify ζ_R as a NUMERICAL or CLOSED-FORM coefficient,
        possibly depending on Ω_γ/Ω_b.

Q-11.3  Specialize to Type III and Type V (both have |a| = 1 in
        canonical units, a aligned on axis 1):

            R_μ^{-1,(III)} = R^{-1} · (1 + ζ_R, 1, 1) + O(|a|⁴)
            R_μ^{-1,(V)}   = R^{-1} · (1 + ζ_R, 1, 1) + O(|a|⁴)

        Are ζ_R^{(III)} and ζ_R^{(V)} numerically the same or
        different? (They share the same |a| and axis alignment;
        the difference is n ≠ 0 for III vs n = 0 for V.)

Q-11.4  Confirm Type-I limit: for a = 0, ζ_R contribution vanishes
        and local_drag_by_mu = R^{-1}·(1, 1, 1), recovering the
        isotropic FLRW result.

=================================================================
DEFECT ⓬ — ζ_M for class-B mass correction
=================================================================

CURRENT STATE (Round-3 Q-8.5(b)):

    mass_by_mu = 3H·1_μ + δM_μ,
    δM_μ ∼ ζ_M · Tr(σ · n) in canonical gauge
    (for Type II with n = diag(1, 0, 0), this projects to σ_11)

    ζ_M requires the v5 shear closure: how does σ^αβ enter the
    anisotropic mass drag on the baryon/CDM local block?

PHYSICS CONTEXT:

The anisotropic Hubble law splits as

    ∇_α u_β = (Θ/3) h_{αβ} + σ_{αβ}   (shear-free + shear)

Baryon/CDM momentum evolution in tetrad form:

    v̇_α + (Θ/3) v_α + σ_α^β v_β = -(1/ρ) ∇_α p + Thomson drag.

The coefficient of v_α on the left side is the "mass drag":

    mass_α = (Θ/3) · δ_α^β + σ_α^β = H·δ_α^β + σ_α^β (first order).

Projecting onto μ-basis (diagonal):

    mass_μ = H + σ_{μμ} = H + σ_αα (if μ aligned with α)
           ≡ H + Tr(σ_μ · projector_μ)

For Bianchi families, σ_{αβ} is diagonal in canonical axes (α = 1,2,3),
so σ_μ_μ is just a specific eigenvalue. With n = diag(n₁, n₂, n₃)
in canonical axes, the Ricci tensor on the spacelike slice carries
the combination

    R^{(3)}_{αβ} = -(1/2)(n^α · n^β + ...) = anisotropic

which FEEDS BACK into σ via the shear propagation equation

    σ̇_{αβ} + Θ·σ_{αβ} + R_{<αβ>}^{(3)} = 0.

At late times (slow evolution) this gives σ_{αβ} ∝ n ·something,
i.e. σ_μμ ∝ n_μμ. The coefficient ζ_M is the proportionality
between Tr(σ·n) and the anisotropic mass drag.

REFERENCES:

  - Ellis & van Elst (1998) "Cosmological Models" Cargèse lectures
    Chapters 2, 3 (1+3 covariant Hubble split).
  - Maartens, Ellis, Stoeger (1995) PRD 51 5942 — anisotropic
    dissipation bounds.
  - Ma & Bertschinger (1995) eq. 29-42 for the mass-drag term
    in the isotropic limit.
  - Wainwright & Ellis (1997) Chapter 6 — class-A shear dynamics.

QUESTION Q-12:

Q-12.1  Derive the anisotropic mass-drag term σ_{αα} for a class-A
        Bianchi family from the tetrad-form shear propagation
        equation, in the limit of slow background evolution.

        Expected: σ_{αα} = ζ_M · n_{αα} · (1/H) at lowest order,
        OR a more specific combination. Derive the exact form and
        the coefficient ζ_M.

Q-12.2  Compute mass_by_mu for Tier-A families in canonical units:

            Type II   (n = diag(1, 0, 0)):  mass_by_mu = (H + ζ_M, H, H)
            Type III  (n = diag(0, 1, -1)): mass_by_mu = (H, H + ζ_M, H - ζ_M)
            Type V    (n = 0):              mass_by_mu = (H, H, H)
            Type VII₀ (n = diag(1, 0, 1)):  mass_by_mu = (H + ζ_M, H, H + ζ_M)
            Type VIII (n = diag(-1, 1, 1)): mass_by_mu = (H - ζ_M, H + ζ_M, H + ζ_M)

        Confirm these formulas (or correct them) and give ζ_M
        as a numerical constant or explicit function.

Q-12.3  Normalization check: in Type I (n = 0), mass_by_mu = H·(1,1,1)
        recovering isotropic FLRW. Is this consistent with the
        Round-3 choice of returning `mass_by_mu = np.ones(3)` as a
        Type-I placeholder? (Note: the H factor is already carried
        by the baryon momentum ODE; the kernel-pack entry should
        be the RELATIVE μ-dependence only, so for Type I it should
        be ones.)

        For non-Type-I families, what should the kernel pack return:
        (a) the absolute mass_α = H + ζ_M·n_αα, or
        (b) the relative correction 1 + (ζ_M/H)·n_αα?

        (b) keeps the kernel pack dimensionless; clarify which is
        expected.

Q-12.4  Confirm Type-I limit: for n = 0, δM_μ = 0 and mass_by_mu
        reduces to (1, 1, 1) in relative form (option b) or (H, H, H)
        in absolute form (option a). State which.

=================================================================
DEFECT ⓭ — Wigner-3j numerical table for twist_mix_kernel
=================================================================

CURRENT STATE (Round-3 Q-8.4(c) + Q-8.6(a)):

    twist_mix_kernel: shape (ell_max+1, 2*ell_max+1, 2, 2)

    Entry form (from Q-8.4(c)):
        T^{(2)}_{a}[ℓ,m,ℓ',m'] = |a| · Σ_q a_q · (-1)^m ·
                                  sqrt((2ℓ+1)(2ℓ'+1)) ·
                                  wigner_3j(ℓ, 1, ℓ'; -m, q, m') ·
                                  wigner_3j(ℓ, 1, ℓ'; -2, 0, 2)

    with ℓ' = ℓ ± 1, m' = m + q, q ∈ {-1, 0, +1}.

    In canonical axis (a^α = |a|·δ^α_1), only the q = ±1 components
    contribute (a_{+1} = -1/√2, a_{-1} = +1/√2, a_0 = 0 in spherical
    basis).

    Entries are currently zero (placeholder).

PHYSICS CONTEXT:

The Wigner-3j symbol evaluations are standard and can be computed
via `sympy.physics.wigner.wigner_3j(j1, j2, j3, m1, m2, m3)` or
via the Racah formula. For the specific ℓ → ℓ ± 1 spin-2 transition
the symbol

    wigner_3j(ℓ, 1, ℓ'; -2, 0, 2)

has the closed form (from Edmonds / Sakurai):

    ℓ' = ℓ + 1: wigner_3j(ℓ, 1, ℓ+1; -2, 0, 2)
             = (-1)^{ℓ-2} · sqrt((ℓ-1)(ℓ+3)) / sqrt((2ℓ+1)(2ℓ+2)(2ℓ+3))

    ℓ' = ℓ - 1: wigner_3j(ℓ, 1, ℓ-1; -2, 0, 2)
             = (-1)^{ℓ-1} · sqrt((ℓ-2)(ℓ+2)) / sqrt((2ℓ-1)(2ℓ)(2ℓ+1))

    (Vanishes for ℓ < 2 because of the spin-2 selection rule.)

The ℓ → ℓ ± 1, m → m ± 1 symbols

    wigner_3j(ℓ, 1, ℓ±1; -m, ±1, m∓1)

also have closed forms in m and ℓ. The auditor can either:

    (a) Give the closed-form Edmonds expressions for each of the 4
        possible (Δℓ, Δm) combinations, leading to a 2×2 block per
        (ℓ, m), or
    (b) Give a small Python function using sympy.physics.wigner
        that populates the (ell_max+1, 2*ell_max+1, 2, 2) array.

REFERENCES:

  - Edmonds (1957) "Angular Momentum in Quantum Mechanics",
    equations 3.7.1 - 3.7.18 (closed forms for ℓ → ℓ ± 1
    Wigner-3j symbols).
  - Sakurai & Napolitano, Chapter 3.
  - Varshalovich, Moskalev, Khersonskii (1988) Section 8.5.

QUESTION Q-13:

Q-13.1  Give either closed-form expressions or a Python function
        that populates the array

            twist_mix_kernel[ell, m_offset, delta_ell_index, delta_m_index]

        with the correct Wigner-3j values for all (ℓ, m) in the
        storage basis, normalized such that Type III/V (|a|=1 in
        canonical) produces the correct T^{(2)}_a matrix element.

Q-13.2  Specify which convention the auditor uses for the spherical
        tensor components a_q of the twist vector:
            a_0 = a_z      (Racah)
            a_{±1} = ∓(a_x ± i·a_y)/sqrt(2)    (Condon-Shortley)

        In the canonical real storage basis (μ_0, μ_+, μ_-) with
        a^α = |a|·δ^α_1, the real-basis components are
        (a_1, 0, 0) = |a|·e_x. Translated to spherical:
            a_0 = 0
            a_{+1} = -|a|/sqrt(2)
            a_{-1} = +|a|/sqrt(2)

        Confirm this convention and trace through to the real
        2×2 block structure used in the kernel pack's
        twist_mix_kernel[..., 2, 2] final axes.

Q-13.3  Numerical table for ℓ_max = 8: provide the 9 × 17 × 2 × 2
        numerical array (or the equivalent closed-form by ℓ block)
        that a patch can drop into the code. If providing via a
        closed form, verify numerically that the Condon-Shortley
        phase convention is consistent.

Q-13.4  Verify Type-I limit: for |a| = 0, twist_mix_kernel = 0
        identically. (This follows from the overall |a| factor;
        confirm the formula carries it.)

=================================================================
DEFECT ⓮ — Sector similarity S_{e,b,ν} (confirmation)
=================================================================

PROPOSED FORM (Round-3 Q-8.6(b)):

    mu_mode_coupling_e = mu_mode_coupling_b = mu_mode_coupling_nu
                       = mu_mode_coupling_t

    i.e. S_{e,b,ν} = I in μ-space.

RATIONALE:

The storage basis uses uniform real normalization across channels;
the ℓ-dependent PSTF row scaling

    pstf_weight(ell) = sqrt((ell+2)(ell-1)) / (2ell+1)     for ell ≥ 2

is carried at the (ℓ, m) slot level (not μ-level). Channel-specific
row scaling d^(X)_ℓ enters through the 1/(2ℓ+1) normalization of
each channel's free-streaming recursion, which is sector-specific
but not μ-specific. Therefore the μ-space matrix is channel-agnostic.

QUESTION Q-14:

Q-14.1  Confirm (or refute) that in the frozen BASS storage basis
        with uniform real normalization, the μ-space part of the
        family-conditioned kernel is channel-agnostic:

            mu_mode_coupling_{t,e,b,ν} = N_family + |a|·P_a.

        Specifically, is there any family in the 5-Tier-A set
        (II, III, V, VII₀, VIII) where the μ-space cross-coupling
        differs between channels (T/E/B/ν), and if so what is the
        similarity transform?

Q-14.2  If similarity is non-identity, express it as a 3×3 real
        matrix S_E (and S_B, S_ν) and derive its form from the
        channel-specific PSTF coefficient d^(X)_ℓ and spin weighting
        in the storage basis.

Q-14.3  If similarity IS identity (the Round-3 default), state so
        and cite which storage-basis convention supports this
        (real basis with uniform normalization, standard ΠZSS
        polarization basis with 1/sqrt(2) E/B split, etc.).

=================================================================
DEFECT ⓯ — Π_μ^α projector (confirmation)
=================================================================

PROPOSED FORM (Round-3 Q-8.2):

    Π_μ^α = axis_permutation(family)     # 3×3 permutation matrix

The BianchiAlgebra schema already carries a field

    axis_permutation: Tuple[int, int, int]

with values:
    _IDENTITY_AXIS_PERMUTATION = (0, 1, 2)         # class A
    _PC_TO_VER2_CLASS_B_AXIS_PERMUTATION = (1, 0, 2) # class B

RATIONALE:

The μ-basis (μ_0, μ_+, μ_-) is the code's canonical mode-label
ordering, not the algebra axis ordering. For class-A families
(axis_permutation = I), μ_0 ↔ axis 0, μ_+ ↔ axis 1, μ_- ↔ axis 2.
For class-B families, the Pontzen-Challinor class-B axis swap is
applied.

For Type VII₀ specifically, the code has n_diag = (0.01, 0, 0.01),
which is axes 1 and 3 nonzero + axis 2 zero. The μ-basis should
probably assign μ_0 to the anchor (axis 2, zero eigenvalue) and
μ_+/μ_- to the two degenerate eigenvalues on axes 1 and 3. But
the current axis_permutation = (0, 1, 2) (identity) maps
μ_0 ↔ axis 0, μ_+ ↔ axis 1, μ_- ↔ axis 2. That would give
mu_mode_coupling_{VII₀} = diag(n_11, n_22, n_33) = diag(1, 0, 1)
instead of the Round-3 canonical diag(0, 1, 1).

QUESTION Q-15:

Q-15.1  For each Tier-A family (II, III, V, VII₀, VIII), state
        the correct Π_μ^α permutation such that

            Π · diag(n) · Π^T = N_canonical

        where N_canonical is the Round-3 canonical signature:
            II:     diag(1, 0, 0)
            III:    diag(0, 1, -1)   (twist contribution separate)
            V:      0
            VII₀:   diag(0, 1, 1)
            VIII:   diag(-1, 1, 1)

        Confirm whether axis_permutation as currently stored is
        sufficient, or whether each family needs a dedicated
        mode-basis permutation.

Q-15.2  For Type VII₀ with code n_diag = (0.01, 0, 0.01), identify
        which permutation produces canonical diag(0, 1, 1) in μ-space.
        (Likely π = (1, 0, 2) or a similar cyclic shift.)

Q-15.3  For families where eigenvalues are degenerate (VII₀ has
        two +0.01 on axes 1, 3), the permutation is not unique.
        State the canonical convention for handling degenerate
        eigenvalues in the mu_+/mu_- assignment.

Q-15.4  Provide the final per-family Π_μ^α 3×3 permutation matrix
        table:

            Type II:    Π = [[1,0,0],[0,1,0],[0,0,1]]    (identity)
            Type III:   Π = ? (class B, possibly (1,0,2) from the existing constant)
            Type V:     Π = ? (class B; N=0 so Π is irrelevant but P_a needs correct axis)
            Type VII₀:  Π = ? (anchor on axis 2; needs non-trivial permutation)
            Type VIII:  Π = ? (eigenvalues are all nondegenerate but signs differ)

        Confirm (or correct) these permutations.

=================================================================
OUTPUT FORMAT
=================================================================

Return your answer as a single markdown document with sections:

    ## Q-10 — q_h for Type VII₀ helical partners
    ## Q-11 — ζ_R for class-B R_μ correction
    ## Q-12 — ζ_M for class-B mass correction
    ## Q-13 — Wigner-3j numerical table for twist_mix_kernel
    ## Q-14 — Sector similarity S_{e,b,ν} confirmation
    ## Q-15 — Π_μ^α projector confirmation

For items ❿-⓭ (substantive derivations), provide both:
   (a) the symbolic/algebraic derivation with literature citations,
       AND
   (b) a turn-key numerical expression or small Python snippet that
       drops into the FamilyKernelPack / _family_conditioned_kernel_operator
       code directly.

For items ⓮-⓯ (confirmations), either confirm the proposed form or
provide the correction.

FLRW / Type-I limit check: for every formula you produce, verify
that at a = 0, n = 0 the expression reduces to the isotropic FLRW
value (zero for μ-couplings, (1, 1, 1) for diagonal vectors,
isotropic transport for Q). This check is non-negotiable and takes
precedence over other physics considerations — without it, the D_2
regression anchor breaks.

CRITICAL CONSTRAINTS:

(C1) The FLRW D_2 = 1002.086744 μK² regression anchor is bit-identical
     through 8 prior physics patches. Any formula must preserve
     b_hh ≡ 0 on the Type-I invariant manifold. Concretely: for
     Type I (a = 0, n = 0) every proposed kernel-pack field (except
     collision = 1.0 universally) reduces to its Type-I placeholder
     value (zero for matrices, ones for vectors).

(C2) Formulas must be REAL-VALUED in the canonical storage basis
     (μ_0, μ_+, μ_-). Helical partner eigenvalues come in degenerate
     pairs. Spherical-tensor conventions must be translated to the
     Condon-Shortley real basis before returning numerical values.

(C3) Provide dimensional analysis for q_h, ζ_R, ζ_M. Dimensionless
     ζ's are preferred (absorb H, R factors into separate code paths);
     if dimensional, state units explicitly.

(C4) No guessing. If a derivation genuinely requires additional v5
     §03A card content not supplied here, state what minimum
     specification is needed and propose a provisional formula that
     trivially reduces to the Type-I limit. A stub with explicit
     limitations is preferable to a false closed form.
```

---

## After Claude answers

The Round-4 answer will land in `v5_residual_harmonic_algebraic_audit_round4.md`. Apply patches in order:

1. **Q-15 (Π projector)** → update `_family_conditioned_kernel_operator` to use `algebra.axis_permutation` for the N projection.
2. **Q-10 (q_h)** → `_build_transport_matrix(backend)` returning the per-family diagonal transport matrix.
3. **Q-13 (Wigner-3j)** → `_build_twist_mix_kernel(algebra.a, ell_max)` populating the (ell_max+1, 2*ell_max+1, 2, 2) array.
4. **Q-11 (ζ_R)** → `_build_local_drag_by_mu(backend)` with the O(|a|²) class-B correction.
5. **Q-12 (ζ_M)** → `_build_mass_by_mu(backend)` with the Tr(σ·n) projection.
6. **Q-14 (sector similarity)** → either confirm identity or apply S_E, S_B, S_ν transforms.

After each patch:
```bash
venv/bin/python -m pytest htt/bass/hierarchy/test_ver3_layout_protocol.py -k "round3_family_kernel" -q
venv/bin/python scripts/v5_operator_fast_check.py
venv/bin/python -m pytest htt/bass/validation/test_d2_regression_anchor.py -q
```

Success criterion per step:
- All 11 Round-3 unit tests pass (possibly with updated expected values for Q-15).
- `λ_max < 2e-15` at both γ_T = 0 and γ_T = 1 across L_max ∈ {4, 6, 8, 12, 16}.
- `D_2 = 1002.086744 μK²` bit-identical.

Once all six items are resolved, proceed to assembly wiring: Tier-A order II → III → V → VII₀ → VIII (see Round-3 diagnosis doc, follow-up (g)).
