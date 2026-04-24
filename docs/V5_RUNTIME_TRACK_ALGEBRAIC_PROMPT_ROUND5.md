# Algebraic Audit Prompt — Round 5

_Self-contained prompt for a fresh Claude session. No repo access; all code and schemas inline._

This round closes the W10+ scalar-mode evolution gap — i.e. the **Tier-B
(1+3 covariant PSTF) output → FLRWSourceTerms** extraction that the
removed S8/S9 pipeline attempted with a toy Sachs-Wolfe MD
approximation `(Θ_0 + Ψ)_* = -R/5`. That approximation was reverted in
commit `85c2270` per the user's "no toy / no surrogate / no
pretend-perturbation-as-nonperturbative" directive (CLAUDE.md §6 bans
TCA pre-phase, FLRW UFA, and photon RSA constructs).

The end goal is end-to-end FLRW D_ℓ production at ℓ=2..30 by feeding
Tier-B-derived `FLRWSourceTerms` into the existing
`bass/los/flrw_bessel_projector.py` LoS integrator and
`bass/spectrum/cl_assembly.py::assemble_cl_TT_isotropic` k-sweep, with
D_2 cross-checked against the canonical `D_2 = 1002.086744 μK²` MM-curve
Route-B anchor.

This Round-5 prompt asks the auditor to derive, from first principles
in the 1+3 covariant (Ellis-van Elst) + PSTF (Maartens-Gebbie-Ellis)
formulation, the exact transformation from the VER2 solver's Tier-B
output fields to the five Newtonian-gauge callables
``FLRWSourceTerms(theta_0, psi, phi_dot_plus_psi_dot, v_b, pi)``.

---

## Residual items this round targets

1. **Q-16 VER2 gauge identification** — what gauge does the VER2 PSTF
   tower use, and how does it relate to Newtonian gauge in the FLRW
   limit?
2. **Q-17 Ψ(η, k) extraction** — closed-form from VER2 background +
   perturbation state, no toy MD formula.
3. **Q-18 `Φ̇ + Ψ̇` ISW driver** — expression in VER2 storage, no
   analytic approximation.
4. **Q-19 v_b(η, k) extraction** — from `baryon_local_history` + k
   normalization convention.
5. **Q-20 Π = Θ_2 − √6·E_2 PSTF normalization** — verify the prefactor
   and sign in VER2's spin-2 storage basis.
6. **Q-21 `extract_flrw_sources_from_tier_b(...)` signature** — the
   complete factory with explicit inputs, explicit outputs, explicit
   verification criterion against D_2 = 1002.086744 μK².

Items Q-16 through Q-20 are derivations; Q-21 is the concrete
signature + validation recipe that a patch can paste directly.

---

## PROMPT FOR CLAUDE

```
You are a physics auditor for a CMB Boltzmann solver (BASS)
implementing the 1+3 covariant PSTF hierarchy for the 11 Bianchi
families. You will not run any code; all input is algebraic and all
output is algebraic or small numerical expressions. The FLRW
D_2 = 1002.086744 μK² regression anchor is bit-identical through 12
prior physics patches; any extraction formulas you produce must
either preserve that anchor exactly via the Route-B MM-curve lookup,
OR match it to within the k-grid quadrature error (typically 0.1%)
when evaluated via the k-integration path being established.

Rounds 1–4 of this audit (prompts V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT{,_ROUND2,
_ROUND3,_ROUND4}.md; answers v5_residual_harmonic_algebraic_audit{
,_round2,_round3,_round4}.md) closed the residual-joint operator
(λ_max < 2e-15), built the Round-3/4 matrix-valued family kernel pack
for Tier-A families (I/II/III/V/VII₀/VIII), and delivered Blocker 3's
cosmological integrator config helper
(build_cosmological_integrator_config). An end-to-end cosmological
smoke (scripts/v5_tier_b_cosmological_smoke.py + the slow-marked
bass/runtime/test_cosmological_smoke.py) confirms IMEX runs over
η ∈ [260, 14147] Mpc in 45 s at L_max=4, reaching η_today with finite
tower state.

Round 5 closes the W10+ scalar-mode evolution gap: how the VER2
solver's tower output is translated into the 5-callable
FLRWSourceTerms(theta_0, psi, phi_dot_plus_psi_dot, v_b, pi) that the
Seljak-Zaldarriaga LoS projector consumes.

=================================================================
DATA AVAILABLE TO YOU (all inline; no external lookup required)
=================================================================

GAUGE CONVENTION (FLRW LoS source):

The FLRWSourceTerms dataclass expects Newtonian-gauge quantities in
the Seljak-Zaldarriaga 1996 form:

    S_T(k, η) = g(η) · [Θ_0(k, η) + Ψ(k, η) + (1/4)·Π(k, η)]   (SW + polter)
              + e^{-κ(η)} · [Ψ̇(k, η) + Φ̇(k, η)]                (ISW)
              + d/dη [g(η) · v_b(k, η)]                         (Doppler)

    S_E(k, η) = -(√6/4) · g(η) · Π(k, η)                        (polter E)

with Π = Θ_2 − √6·E_2 (per KKS 1997 / Zaldarriaga-Seljak 1997).

VER2 TIER-B OUTPUT SCHEMA (IntegrationResult, trimmed to the
relevant fields):

    @dataclass
    class IntegrationResult:
        eta: np.ndarray                  # (N_eta,) conformal time grid
        a: np.ndarray                    # (N_eta,) scale factor
        Sigma_plus: np.ndarray           # (N_eta,) Bianchi-I shear Σ_+
        Sigma_minus: np.ndarray          # (N_eta,) Bianchi-I shear Σ_-
        photon_T_tower: np.ndarray       # (N_eta, (L+1)^2) PSTF Θ_ℓm
        photon_E_tower: np.ndarray       # (N_eta, (L+1)^2) PSTF E_ℓm (ℓ≥2)
        photon_B_tower: np.ndarray       # (N_eta, (L+1)^2) PSTF B_ℓm (ℓ≥2)
        neutrino_tower: np.ndarray       # (N_eta, (L+1)^2) PSTF ν_ℓm
        baryon_local_history: np.ndarray # (N_eta, 4) slots: [δ, v, ?, ?]
        cdm_local_history: np.ndarray    # (N_eta, 2) slots: [δ, v]
        source_history: np.ndarray       # (N_eta, 3) slots: [reion,dop,pol]
        config: IntegratorConfig
        critical_events: dict
        # ...

    VER2 tower packing (real spherical harmonic convention):
        offset(ℓ) = sum(2ℓ' + 1 for ℓ' in range(ℓ))
        slot(ℓ, m) = offset(ℓ) + (ℓ + m)        # m ∈ [−ℓ, +ℓ]
    Access helpers:
        pi_ell_m(ell, m=0) → photon_T_tower[:, slot(ell, m)]
        e_ell_m(ell, m=0) → photon_E_tower[:, slot(ell, m)]
        nu_ell_m(ell, m=0) → neutrino_tower[:, slot(ell, m)]

VER2 BACKGROUND MONITOR SCHEMA (BackgroundEvolutionResult):

    @dataclass(frozen=True)
    class BackgroundEvolutionResult:
        eta: np.ndarray                  # (N_eta,) conformal time
        a: np.ndarray                    # (N_eta,) scale factor
        H: np.ndarray                    # (N_eta,) conformal Hubble ℋ
        sigma_tensor: np.ndarray         # (N_eta, 3, 3) covariant shear σ_ab
        rho: np.ndarray                  # (N_eta,) total energy density
        p: np.ndarray                    # (N_eta,) total pressure
        q: np.ndarray                    # (N_eta, 3) energy-flux 4-vector
        pi: np.ndarray                   # (N_eta, 3, 3) covariant anisotropic pressure
        electric_weyl: np.ndarray        # (N_eta, 3, 3) E_ab
        magnetic_weyl: np.ndarray        # (N_eta, 3, 3) H_ab
        tilt_rapidity: np.ndarray        # (N_eta,) β(η)
        tilt_velocity: np.ndarray        # (N_eta, 3) v̂(η)

    For FLRW / Bianchi I orthogonal:
        sigma_tensor[k,:,:] = diag(Σ_+ + Σ_−, Σ_+ − Σ_−, −2·Σ_+)·a(η)
        tilt_rapidity ≡ 0, tilt_velocity ≡ 0
        q ≡ 0, pi[k,:,:] is traceless-symmetric (radiation quadrupole)

FLRW / TYPE-I LIMIT (a=0, n=0, σ=0):

    The Bianchi-specific shear vanishes (background becomes FLRW). All
    "Bianchi corrections" to the covariant radiation source reduce to
    zero. The covariant Θ_ℓ tower should then be identifiable with the
    Newtonian-gauge Θ_ℓ modulo a gauge transformation that is explicit
    in Ma-Bertschinger 1995 §5 (synchronous ↔ Newtonian).

VER2 SEED (current toy placeholder, Round-5 target for replacement):

    The current _build_seed_projection assembles a symbolic
    "adiabatic" seed with common amplitude = max(|Σ_±|, 1e-6) and
    common θ_common = amplitude/3. All 5 species (γ, b, c, ν) share
    this amplitude. This IS adiabatic but the normalization is
    decoupled from the primordial P(k). A follow-up
    (Blocker-3 item (i)) wires P(k)-derived amplitude; for Round 5
    we treat it as unit amplitude (Δζ_R = 1) without loss of
    generality (C_ℓ assembly then multiplies by P(k) via
    primordial_power_spectrum in cl_assembly.py).

D_2 REGRESSION ANCHOR:

    D_2 = 1002.086744 μK² (Route-B MM-curve Python mirror of the
    Rust bass_rs MB-95 oracle). Bit-identical through 12 prior
    physics patches. Any new extraction path that produces a full-k
    spectrum must match D_2 at ℓ=2 to within 0.1% (the typical
    k-grid trapezoid-quadrature error); any larger deviation is a
    bug in the extractor, not the k-grid.

1+3 COVARIANT / PSTF REFERENCES you may assume:

    - Ellis & van Elst (1998) "Cosmological models", Cargèse lectures,
      especially §2-3 (1+3 tetrad formalism) and §5 (linearization on
      FRW background).
    - Maartens, Gebbie, Ellis (1999) PRD 59 083506 — covariant
      CMB anisotropy, explicit S_T formula for the 1+3 covariant
      PSTF temperature hierarchy.
    - Challinor & Lasenby (1999) ApJ 513 1 — "Cosmic Microwave
      Background Anisotropies in the Cold Dark Matter Dominated Flat
      Universe" — covariant-gauge CMB formalism.
    - Challinor (2000) PRD 62 043004 — covariant polarization
      hierarchy, Π normalization.
    - Ma & Bertschinger (1995) ApJ 455 7 — synchronous ↔ Newtonian
      gauge dictionary (§5); Θ_ℓ/E_ℓ evolution equations; Π source
      factor √6/10.
    - Seljak & Zaldarriaga (1996) ApJ 469 437 — LoS integrator.
    - Kamionkowski, Kosowsky, Stebbins (1997) PRD 55 7368 — Π =
      Θ_2 − √6·E_2 decomposition and polarization assembly.
    - Zaldarriaga & Seljak (1997) PRD 55 1830 — all-sky polarization
      C_ℓ assembly.

=================================================================
DEFECT ⓰ / Q-16 — VER2 gauge identification
=================================================================

VER2 is the 1+3 covariant PSTF formulation. The Θ_ℓ(η) tower is the
set of PSTF projections of the photon distribution function moments,
projected orthogonal to the preferred 4-velocity u^a. In the
FLRW / Bianchi-I orthogonal case (u^a = normal to the spatial slice),
u^a is the same as in the Newtonian-gauge standard derivation.

QUESTIONS:

Q-16.1  For FLRW / Bianchi-I orthogonal (Σ_+ = Σ_− = 0), is the VER2
        Θ_ℓ = photon_T_tower[η, slot(ℓ, 0)] DIRECTLY equal to the
        Newtonian-gauge Θ_ℓ (Ma-Bertschinger convention), or is there
        a gauge-transformation coefficient between them?

        Expected output: either
            Θ_ℓ^VER2 = Θ_ℓ^MB       (direct identity)
        or
            Θ_ℓ^VER2 = α(ℓ) · Θ_ℓ^MB + β(ℓ) · (metric correction)

Q-16.2  Cite the specific Ellis-van Elst / Maartens-Gebbie-Ellis
        equation(s) that establish the identity (or the gauge-
        transformation coefficients). For FLRW, the expected answer
        is a direct identity because u^a coincides with the
        synchronous-gauge threading for a comoving observer on the
        Bianchi-I-orthogonal slice.

Q-16.3  Does the same identity hold for ALL ℓ, or only for specific
        ℓ (e.g., ℓ ≥ 2 might differ due to PSTF normalization)?
        Confirm explicitly whether `photon_T_tower[:, slot(0, 0)]`
        equals `Θ_0(η)` in the Newtonian-gauge sense for FLRW.

=================================================================
DEFECT ⓱ / Q-17 — Ψ(η, k) extraction (Newtonian-gauge potential)
=================================================================

In Newtonian gauge on an FRW background, Ψ is determined by the
Poisson equation:

    −k² Ψ = 4π G a² δρ_total + ℋ·θ_total-terms-from-Einstein-constraints

For a multi-species radiation-matter universe:

    Ψ(k, η) = − (3·ℋ²(η) / (2·k²)) · δ_total(k, η) + O(anisotropic stress)

with δ_total = Σ_i Ω_i(η) · δ_i(k, η) and anisotropic-stress
corrections from Π and the neutrino quadrupole.

VER2 does NOT store δ_γ, δ_b, δ_c, δ_ν separately in the form
Ma-Bertschinger expects. Instead:

    δ_b(k, η) = baryon_local_history[η, 0]   ← if slot 0 is density
    δ_c(k, η) = cdm_local_history[η, 0]      ← if slot 0 is density
    δ_γ(k, η) = 4 · Θ_0(k, η) = 4 · photon_T_tower[η, slot(0, 0)]
    δ_ν(k, η) = 4 · photon_T_tower for neutrinos at ℓ=0 channel?

(where "4·Θ_0" comes from δ_γ = 4·Θ_0 for radiation with δ = 3·(1+w)·Θ_0
with w=1/3 → δ = 4·Θ_0.)

QUESTIONS:

Q-17.1  Confirm or correct the δ extraction formulas above. Specifically:

        (a) Is baryon_local_history[η, 0] the baryon density
            perturbation δ_b in Newtonian gauge, OR in the 1+3
            covariant / synchronous-equivalent frame? If the latter,
            supply the gauge-transformation formula
            (Ma-Bertschinger §5 eqs. 27-30).
        (b) Is cdm_local_history[η, 0] similarly δ_c?
        (c) For photons: δ_γ = 4·Θ_0 — is this correct with VER2's
            PSTF normalization, or is there a PSTF prefactor (e.g.,
            (2ℓ+1)·something)?
        (d) For neutrinos: same question, noting the storage may
            differ from photons.

Q-17.2  Derive Ψ(k, η) in closed form for FLRW using the VER2 field
        accessors. Expected shape:

            Ψ(k, η) = f(H(η), δ_total(η), Π(η), k)

        where the inputs are all extractable from
        (background_monitor, integration_result). Explicitly state
        any anisotropic-stress contribution from Π and the neutrino
        quadrupole in the form
            Ψ − Φ = (12π G a²) · σ_stress(η) / k²
        (Ma-Bertschinger §5 "anisotropic stress" formula).

Q-17.3  Closed-form verification: in the MD limit (Ω_m → 1, Ω_γ → 0,
        Π → 0), does your formula reduce to the canonical Ψ = const
        (growing-mode MD potential)? Confirm or correct.

Q-17.4  Numerical stability: for k → 0 the Poisson formula has a
        1/k² factor. Document the small-k limit — at what k does
        the "Ψ extraction via Poisson" break down and where should
        the large-scale regularization (if any) begin?

=================================================================
DEFECT ⓲ / Q-18 — Φ̇ + Ψ̇ ISW driver
=================================================================

The ISW driver is the time derivative of Φ + Ψ. In Newtonian gauge:

    Φ + Ψ = 2·Φ − (anisotropic-stress correction) ≈ 2·Φ = −2·Ψ
                                                   (no aniso-stress limit)

So Φ̇ + Ψ̇ ≈ 2·Ψ̇ = 2·(dΨ/dη) in the no-anisotropic-stress limit.

With anisotropic stress:

    Ψ − Φ = (12π G a²) · σ_stress / k²
          ⇒ Φ̇ + Ψ̇ = Ψ̇ + Φ̇
                    = 2·Ψ̇ − (d/dη)[Ψ − Φ]
                    = 2·Ψ̇ − (12π G) · d/dη [a² · σ_stress / k²]

QUESTIONS:

Q-18.1  Confirm or correct the (Φ̇ + Ψ̇) decomposition above. Express
        it entirely in terms of VER2 fields (background_monitor.H,
        Π(η) = photon_T_tower quadrupole − √6 · E_tower quadrupole,
        etc.).

Q-18.2  Numerical differentiation: since Ψ̇ is a derivative of an
        extracted field, numerical noise is a concern. Recommend:
        (a) store Ψ(η) on the full η grid and differentiate via
            centered 4th-order finite differences (bulk) + 2nd-order
            one-sided (boundary), OR
        (b) derive Ψ̇ directly from Ma-Bertschinger's evolution
            equation (more robust; use the 1+3 covariant Ψ̇ formula).

        State the recommended path and justify.

Q-18.3  MD limit check: in matter domination, (Φ̇ + Ψ̇) = 0 exactly
        (Φ, Ψ are both constant). Does your formula reduce to zero?
        ISW contribution should only become non-zero during
        radiation- or Λ-domination.

=================================================================
DEFECT ⓳ / Q-19 — v_b(η, k) extraction and k normalization
=================================================================

Baryon velocity v_b is stored in baryon_local_history but the exact
slot and normalization convention need confirmation.

QUESTIONS:

Q-19.1  Slot identification: what does baryon_local_history[η, i]
        represent for each i ∈ {0, 1, 2, 3}? A plausible convention
        is:
            i=0: δ_b (density)
            i=1: v_b (velocity divergence / dipole amplitude)
            i=2: shear or higher moment?
            i=3: placeholder or geometric correction?

        Provide the exact slot dictionary. This is determined by
        build_reduced_local_affine_operator in
        bass/hierarchy/ver3_layout_protocol.py.

Q-19.2  k-normalization: is the stored v_b at the solver's single k
        (from `k_grid_mpc` parameter in execute_tier_b_solver), or is
        it a transfer function normalized to k=1? The LoS projector
        expects v_b(η, k) with explicit k-dependence inside the
        d/dη[g(η)·v_b] Doppler term.

Q-19.3  Sign convention: is v_b the peculiar velocity (∇_i δu^i / k
        in Fourier space) or the dipole amplitude (times −i·k)?
        Confirm the Ma-Bertschinger eq. 29 convention.

Q-19.4  Verification: at matter-radiation equality (η ~ η_eq), v_b
        should track v_γ through tight coupling. Numerically verify
        that `v_b(k, η_eq) ≈ v_γ(k, η_eq)` for the solver's output,
        where v_γ is extracted from photon_T_tower at ℓ=1.

=================================================================
DEFECT ⓴ / Q-20 — Π = Θ_2 − √6·E_2 PSTF normalization
=================================================================

The polarization source Π = Θ_2 − √6·E_2 is defined in Zaldarriaga-
Seljak 1997 / KKS 1997 with a specific ℓ-normalization convention
that depends on the spherical-harmonic vs spin-weighted-Ylm basis.

VER2 stores:
    photon_T_tower[:, slot(2, 0)]  — Θ_2 in PSTF normalization
    photon_E_tower[:, slot(2, 0)]  — E_2 in PSTF normalization

The PSTF weight factor is pstf_weight(ℓ) = √((ℓ+2)(ℓ−1)) / (2ℓ+1).
For ℓ=2: pstf_weight(2) = √(4·1) / 5 = 2/5.

QUESTIONS:

Q-20.1  Given the VER2 PSTF storage convention, is the formula
            Π(η) = photon_T_tower[:, slot(2, 0)]
                  − √6 · photon_E_tower[:, slot(2, 0)]
        correct AS IS, or does the PSTF row scaling d_ℓ^(X) / (2ℓ+1)
        introduce a prefactor?

Q-20.2  If a prefactor is needed, provide the exact formula:
            Π(η) = α_T · photon_T_tower[:, slot(2, 0)]
                  + α_E · photon_E_tower[:, slot(2, 0)]
        with α_T, α_E derived from the PSTF-to-Newtonian
        normalization conversion.

Q-20.3  Sign convention verification: Π appears in BOTH S_T (as
        +Π/4) and S_E (as −(√6/4)·Π). Confirm the sign on E_2 in Π
        is correct for the VER2 polarization convention.

Q-20.4  MD / pre-recombination limit: for η ≪ η_*, photons are
        tightly coupled, polarization is strongly damped, and
        Π → 0. Confirm the limit holds numerically (Round-1
        already made the residual-joint operator collisionless-
        stable; this is a post-coupling diagnostic).

=================================================================
DEFECT ⓵ / Q-21 — extract_flrw_sources_from_tier_b signature
=================================================================

With Q-16..Q-20 resolved, the concrete factory is:

    def extract_flrw_sources_from_tier_b(
        integration_result: "IntegrationResult",
        background_monitor: "BackgroundEvolutionResult",
        k: float,
        *,
        anisotropic_stress: bool = True,
    ) -> FLRWSourceTerms:
        ...

which builds the 5 callables `theta_0`, `psi`, `phi_dot_plus_psi_dot`,
`v_b`, `pi` — each an interpolator over the stored η grid — from the
Tier-B output and the background monitor.

QUESTIONS:

Q-21.1  Provide the exact Python pseudocode (sufficient for a patch
        to compile as-is) for
            extract_flrw_sources_from_tier_b(integration_result,
                                             background_monitor, k)

        The pseudocode should:
        (a) Extract eta, a, H grids from background_monitor.
        (b) Extract Θ_0, Θ_2, E_2 grids from integration_result via
            pi_ell_m(0), pi_ell_m(2), e_ell_m(2).
        (c) Compute Π(η) via Q-20 formula.
        (d) Extract δ_b(η), v_b(η) from baryon_local_history slot
            dictionary (Q-19).
        (e) Compute Ψ(η, k) via Q-17 Poisson formula.
        (f) Compute Φ̇(η, k) + Ψ̇(η, k) via Q-18 formula.
        (g) Return FLRWSourceTerms with 5 interpolator callables
            (linear or cubic in η; state which).

Q-21.2  Verification test: using the extracted FLRWSourceTerms, run
        the existing LoS projector (project_m0_temperature_transfer,
        project_m0_emode_transfer) at k = k_pivot = 0.05 Mpc⁻¹ and
        assemble C_ℓ^TT via assemble_cl_TT_isotropic. Compute D_2
        via compute_dl.

        Expected: D_2 from this path matches 1002.086744 μK² to within
        the k-grid quadrature error (0.1% at typical
        log-spaced k-grid with ~50 points).

        A larger deviation than 0.1% indicates a Q-16/Q-17/Q-20 bug.

Q-21.3  Anisotropic-stress off/on toggle: with anisotropic_stress=False
        (MD no-Π limit), the extractor should produce the SW-plateau
        plus ISW-only source. This recovers the reverted S8/S9 form
        EXCEPT that Ψ now comes from the full Poisson equation, not
        from the toy MD `(Θ_0+Ψ)_* = −R/5` formula. Confirm the
        FLRWSourceTerms matches the physical sharp-visibility
        analytic limit to 1% at ℓ=2.

Q-21.4  Computational cost: the extractor is called once per k (in
        the k-scan). For N_k = 50 and L_max = 4 in the existing smoke
        (45 s per Tier-B run), the full k-sweep costs N_k · 45 s ≈
        38 minutes. State whether any of the 5 callables have
        weak k-dependence that permits k-interpolation (e.g., Ψ(k, η)
        ∝ 1/k² for small k — can large-scale Ψ be precomputed at one
        k and scaled?).

=================================================================
CRITICAL CONSTRAINTS
=================================================================

(C1) FLRW D_2 = 1002.086744 μK² bit-identity through the Route-B
     MM-curve path is preserved. The Round-5 extractor path is a
     DIFFERENT code route (direct k-integration), and its D_2 must
     match to 0.1% (k-grid quadrature error), not bit-exactly.

(C2) NO toy Sachs-Wolfe approximation: Ψ must come from the Poisson
     equation using VER2's extracted δ_total, not from the MD
     `Ψ_* = -(3/5) · ζ_primordial` formula.

(C3) NO TCA pre-phase, NO FLRW UFA, NO photon RSA (per CLAUDE.md §6
     approximation-free mandate). If a numerical stability concern
     forces an approximation, explicitly state so and tag it for
     audit removal.

(C4) The VER2 gauge must be identified unambiguously. If the
     photon_T_tower is NOT directly the Newtonian-gauge Θ_ℓ in the
     FLRW limit, provide the gauge-transformation coefficients and
     state their derivation reference.

(C5) The five callables (`theta_0`, `psi`, `phi_dot_plus_psi_dot`,
     `v_b`, `pi`) returned by `extract_flrw_sources_from_tier_b`
     must be η → float interpolators with the η domain set to
     [background_monitor.eta[0], background_monitor.eta[-1]].
     Extrapolation outside this range is not permitted.

=================================================================
OUTPUT FORMAT
=================================================================

Return your answer as a single markdown document with sections:

    ## Q-16 — VER2 gauge identification
    ## Q-17 — Ψ(η, k) extraction from VER2 state
    ## Q-18 — Φ̇ + Ψ̇ ISW driver
    ## Q-19 — v_b(η, k) slot + k normalization
    ## Q-20 — Π = Θ_2 − √6·E_2 PSTF prefactor check
    ## Q-21 — extract_flrw_sources_from_tier_b signature + verification

Each section must cite the specific literature equation(s) used.
Turn-key Python pseudocode is preferred over prose for Q-21.
```

---

## After Claude answers

The Round-5 answer lands in `v5_residual_harmonic_algebraic_audit_round5.md`. Patches apply in order:

1. **Q-19** (v_b slot dictionary) → module-level constants in `bass/spectrum/tier_b_source_extraction.py`.
2. **Q-20** (Π prefactor) → single-line `pi(η)` function.
3. **Q-17** (Ψ extraction) → `psi(k, η)` closure factory with Poisson formula.
4. **Q-18** (Φ̇ + Ψ̇) → `phi_dot_plus_psi_dot(k, η)` closure factory (prefer Ma-Bertschinger's direct evolution form over numerical differentiation).
5. **Q-16** (gauge coefficients, if non-trivial) → row-scaling or direct identity applied at extractor entry.
6. **Q-21** (full factory) → `extract_flrw_sources_from_tier_b(integration_result, background_monitor, k)`.

After each patch:

```bash
venv/bin/python -m pytest htt/bass/spectrum/test_tier_b_source_extraction.py -q  # new
venv/bin/python -m pytest htt/bass/validation/test_d2_regression_anchor.py -q    # unchanged
venv/bin/python scripts/v5_operator_fast_check.py                                # unchanged
```

Success criterion:

- Round-5 extraction tests pass: 5 new unit tests per Q-21.1 pseudocode.
- D_2 via the new k-integration path matches `1002.086744 μK²` to 0.1%.
- Existing 1378/1378 fast baseline unchanged; slow cosmological smoke still passes.

Once Round-5 lands, the critical path reaches step 4d from V5 handoff Option D — E2E FLRW D_ℓ production at ℓ=2..30. Step 5 (CAMB cross-check) then becomes a straightforward compare.
