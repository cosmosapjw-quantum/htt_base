# Round-15 P1 — External-LLM Hand-off: PSTF / 1+3 covariant tetrad formalization

_Prepared 2026-04-25, after Round-15 P0 (D-1 LoS grid decoupling, commit `cb82a2a`).
For paste into a separate research-focused LLM session._

---

## §0. How to use this document

The empirical evidence from Round-15 P0 (see §3) shows that the BASS LoS
projector and its PSTF-based source assembly are structurally correct in
the FLRW limit at sub-recombination scales (k ≤ 10⁻² Mpc⁻¹) — but the
project lacks a formal derivation that says **why** the existing
implementation is correct, **where** its conventions differ from CAMB /
MB-95, and **how** to extend it to anisotropic Bianchi backgrounds with
PSTF/tetrad as the primary framework (not Newtonian-gauge as a stepping
stone).

This document is the briefing for an external research-LLM session
that will produce that derivation. Below: (§1) goals, (§2) the existing
documentation map, (§3) what we tried, succeeded, and failed at, (§4)
the gaps that the LLM session must close, (§5) a prompt list to paste
in sequence, (§6) deliverable acceptance criteria, (§7) constraints.

The output of the LLM session is **documentation only** — no production
code changes. Code follow-up is a separate Round-15 sub-track that the
present author / coding agent will execute *after* the derivation has
been audited.

---

## §1. Mission

Formalize BASS's PSTF / 1+3 covariant / tetrad treatment of CMB
temperature and polarization transport, with three deliverables:

1. **D1 — FLRW-limit PSTF derivation.** Derive the line-of-sight
   temperature transfer in the FLRW limit from the 1+3 covariant
   formalism (Ellis–van Elst 1998, Challinor–Lasenby 2000 I+II, Maartens
   1998), keeping PSTF variables as primary throughout. Show that the
   BASS implementation
   ```
   S_T(η) = g(η) [Θ_0(η) + Ψ(η) + (1/4) Π(η)]
          + e^{-κ(η)} [Φ̇(η) + Ψ̇(η)]
          + d/dη [g(η) v_b(η)]
   ```
   in [htt/bass/los/flrw_bessel_projector.py](../htt/bass/los/flrw_bessel_projector.py),
   sourced by Newtonian-gauge potentials Φ, Ψ derived from constraint
   algebra in [htt/bass/spectrum/tier_b_source_extraction.py](../htt/bass/spectrum/tier_b_source_extraction.py),
   is the correct projection of the PSTF observable. Identify the exact
   gauge / frame each quantity lives in, and whether the assembly
   silently introduces a gauge-mixed term.

2. **D2 — ℓ = 0 monopole convention audit.** PSTF multipoles for ℓ ≥ 1
   are gauge-invariant around FRW (Ellis–van Elst 1998 standard
   result). The ℓ = 0 monopole Θ_0 in the BASS hierarchy is the
   energy-density contrast of the photon fluid in the comoving radiation
   rest frame; CAMB's `clxg = Δ_γ = 4 Θ_0` is in the CDM rest frame
   (synchronous gauge). Derive the exact transformation between these
   two ℓ = 0 conventions, write it in PSTF-native algebra (no Newtonian
   crutch), and identify whether the LoS source assembly in BASS needs
   any correction. The empirical low-k match at ratio ≈ 1.0 (§3.1)
   suggests the answer is *no extra correction* — but the derivation
   must demonstrate this rather than assume it.

3. **D3 — Bianchi tetrad-frame extension plan.** Starting from the
   established FLRW result, lay out the formalism for:
   (a) tetrad transport on an anisotropic Bianchi background with
   shear σ_{ab} ≠ 0 (T7/T8/T9 operators in
   [htt/bass/hierarchy/hierarchy_rhs.py](../htt/bass/hierarchy/hierarchy_rhs.py)),
   (b) m = ±2 channel coupling (currently identically zero for
   Bianchi-I / FLRW; required for Bianchi II–IX),
   (c) tilted observer frames (n^a vs u_e^a, per
   [docs/lowell_bianchi_solver_reference.md](lowell_bianchi_solver_reference.md) §1.2),
   (d) Maartens–Ellis–Stoeger kinematic-bound translation to the
   `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` master departure
   identity (cf.
   [project/03_physics_notes/tomographic_MES_framework.md](../project/03_physics_notes/tomographic_MES_framework.md)).

The output should be **audit-ready**: derivations are step-by-step,
cited to canonical references, and each claim that maps to a BASS code
construct is explicitly tagged with the file + line range.

The user's directive: **PSTF/tetrad is the primary framework — not a
stepping stone toward Newtonian gauge.** Bianchi II–IX cannot be
expressed cleanly in synchronous gauge; the formalism must remain
PSTF-native end-to-end.

---

## §2. Documentation that already exists in the repo

Read these in order — they form the input the LLM session needs to
ground in.

### §2.1 Tier 1 — Central PSTF design + reference docs

| Path | Size | What it covers | Read priority |
|---|---:|---|---:|
| [docs/lowell_bianchi_solver_reference.md](lowell_bianchi_solver_reference.md) | 25 KB | THE central tetrad/PSTF design doc. 18 sections covering: 1+3 decomposition (§1); tetrad frames `n^a` for transport, `u_e^a` for collision (§1.2); state vector (§1.3); exact Bianchi background transport (§2); species perturbation equations (§3); exact Thomson collision tensor (§4); radiation Θ, E, B variables (§5); multipole hierarchy + low-ℓ cutoff (§6); Tier B state vector + LoS formalism (§7); SW/ISW + redshift source (§8); per-species perturbation eqs (§9); quadrupole-aware TCA (§10); recombination/reionization (§11). **This is the existing foundation; D1–D3 should extend / formalize what's here, not replace it.** | 🔴 highest |
| [project/04_implementation_specs/CAMB_Tight-Coupling_Approximation_Mapped_to_the_1_3_PSTF_Covariant_Hierarchy_…md](../project/04_implementation_specs/CAMB_Tight-Coupling_Approximation_Mapped_to_the_1_3_PSTF_Covariant_Hierarchy__Variable_Conventions__TCA_Equations__and_Implementation_Guide_for_bass_rs.md) | 26 KB | CAMB ↔ BASS PSTF variable identification: I_ℓ = F_{γ,ℓ}^{MB} = 4 Θ_ℓ; CAMB's `clxg, qg, pig, etak` mapping to BASS variables; CAMB's TCA equations (first-order + second-order Cyr-Racine corrections); polarization sign convention (CAMB E₂ has flipped sign vs theory literature); switchback protocol. **Notes that CAMB works in the CDM rest frame = synchronous gauge** — this is critical for understanding the ℓ = 0 D2 question. | 🔴 highest |
| [docs/PHYSICS_REFERENCES.md](PHYSICS_REFERENCES.md) | 9 KB | Canonical bibliography. PSTF references in §B: Challinor–Lasenby 2000 I+II, Maartens–Gebbie–Ellis 1999, Tsagas–Challinor–Maartens 2008, Maartens 1998, Lewis–Challinor 2006. MB-95 / CAMB / Hu-White listed in §B.5 as **verified oracle, not production target**. | 🟠 high |

### §2.2 Tier 2 — Bianchi/tilt/MES physics notes

| Path | Size | What it covers | Read priority |
|---|---:|---|---:|
| [project/03_physics_notes/tomographic_MES_framework.md](../project/03_physics_notes/tomographic_MES_framework.md) | — | Maartens–Ellis–Stoeger framework + Heinesen tomographic cosmography. Defines `H_o` generalised Hubble parameter, deceleration multipoles, dipole/quadrupole/vorticity sectors, departure proxy `x_C`. **The `x_C` master identity is the thesis target.** | 🟠 high |
| [project/03_physics_notes/Quadratic_Source_Coefficients_for_Second-Order_Bianchi_I_Boltzmann_Theory.md](../project/03_physics_notes/Quadratic_Source_Coefficients_for_Second-Order_Bianchi_I_Boltzmann_Theory.md) | 35 KB | Second-order quadratic source coefficients for Bianchi-I Boltzmann theory. Goes beyond linear theory; useful for understanding the m = ±2 channel at non-trivial Bianchi types. | 🟡 medium |
| [project/03_physics_notes/Second-Order_Neutrino_Quadratic_Sources_in_Two-Field_Fermi-Dirac_Theory_…md](../project/03_physics_notes/Second-Order_Neutrino_Quadratic_Sources_in_Two-Field_Fermi-Dirac_Theory__Hessian_Structure_and_Quadrupole_Coefficients.md) | 16 KB | Second-order neutrino quadratic sources, Hessian structure, quadrupole coefficients. | 🟡 medium |
| [project/03_physics_notes/bianchi_background_survey_v2.md](../project/03_physics_notes/bianchi_background_survey_v2.md) | — | Bianchi background classification survey. | 🟡 medium |
| [project/03_physics_notes/nonlinear_boltzmann_feasibility_v2.md](../project/03_physics_notes/nonlinear_boltzmann_feasibility_v2.md) | 38 KB | Nonlinear Boltzmann feasibility analysis. | 🟡 medium |
| [project/03_physics_notes/reionization_anisotropic_spacetimes.md](../project/03_physics_notes/reionization_anisotropic_spacetimes.md) | — | Reionization in anisotropic spacetimes. | ⚪ low (P1 scope) |
| [project/03_physics_notes/anisotropic_recombination.md](../project/03_physics_notes/anisotropic_recombination.md) | — | Recombination in anisotropic backgrounds. | ⚪ low (P1 scope) |
| [project/03_physics_notes/bmr_framework_v2.md](../project/03_physics_notes/bmr_framework_v2.md) | 45 KB | Buchert–Mourier–Roy backreaction framework. | ⚪ low (separate track) |

### §2.3 Tier 3 — Implementation files (PSTF formalism encoded in code)

These are the BASS source files where the formalism currently lives.
The LLM session should reference these for the "what BASS actually
computes" anchor in derivations.

| Path | What it implements | Read priority |
|---|---|---:|
| [htt/bass/los/flrw_bessel_projector.py](../htt/bass/los/flrw_bessel_projector.py) | LoS projector. `S_T = g·[Θ_0 + Ψ + Π/4] + e^{-κ}·[Φ̇+Ψ̇] + d/dη[g·v_b]`. Spherical-Bessel j_ℓ + E-mode projection factor. References Seljak–Zaldarriaga 1996, Kamionkowski–Kosowsky–Stebbins 1997. | 🔴 highest |
| [htt/bass/spectrum/tier_b_source_extraction.py](../htt/bass/spectrum/tier_b_source_extraction.py) | Builds Φ, Ψ from Einstein constraints; Θ_0, v_b, Π_2 = Θ_2 − √6·E_2 from PSTF tower. References Ma–Bertschinger 1995 (sync ↔ Newt dictionary), Ellis–van Elst 1998 (1+3 covariant PSTF), Round-5 audit Q-16 / Q-17 / Q-20. | 🔴 highest |
| [htt/bass/hierarchy/hierarchy_rhs.py:343](../htt/bass/hierarchy/hierarchy_rhs.py#L343) | PSTF photon RHS via T1 (expansion), T7 (shear up), T8 (shear same), T9 (shear down) operators. Pure 1+3 covariant — no `h'` coupling. References Kolb–Turner, Ellis covariant formalism. | 🔴 highest |
| [htt/bass/hierarchy/integrator.py](../htt/bass/hierarchy/integrator.py) | `IntegrationResult` schema (l. 224), exposes photon_T_tower, photon_E_tower, neutrino_tower, baryon_local_history (delta_b, vb), cdm_local_history. **Does NOT expose `h_S` or any synchronous-gauge metric** — confirming BASS is PSTF-native. | 🟠 high |
| [htt/bass/los/los_grid_builder.py](../htt/bass/los/los_grid_builder.py) | Round-15 P0 D-1 fix. Per-k composite LoS η-grid. | 🟡 medium (background) |

### §2.4 Tier 4 — Empirical evidence + recent work

| Path | What it documents | Read priority |
|---|---|---:|
| [docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md](V5_ROUND15_P0_D1_FIX_SUMMARY.md) | Round-15 P0 outcome. D-1 LoS grid was the dominant defect; fix lands; resolution-independence proves grid is now healthy. | 🔴 highest |
| [docs/audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt](audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt) | §10 decisive test: 3-column diagnostic (uniform64 / k_adapted / k_adapted_η100). Shows post-D-1 BASS matches CAMB at low k once integrator η_init truncation is lifted. | 🔴 highest |
| [docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md](V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md) | Pre-fix investigation chain (4 audit cycles, 10 verdicts) that diagnosed D-1, D-2, D-3 separately. | 🟠 high |
| [docs/V5_ROUND15_SESSION_OPENER.md](V5_ROUND15_SESSION_OPENER.md) | Original Round-15 P0/P1/P2 spec. **Note: P1's `theta0_g_newtonian = theta0_g_synchronous + h_S_dot/6` formula does not apply to BASS** — see §3.4 of this hand-off. | 🟠 high |
| [docs/SSOT_POLICY.md](SSOT_POLICY.md) | SSoT authority order, T_CMB convention, BASS unit convention. | 🟡 medium |
| [CHANGELOG.md](../CHANGELOG.md) | Project history. Round-15 P0 entry at the top of `[Unreleased]`. | 🟡 medium |

### §2.5 External canonical references (consult during derivation)

The LLM session should already know these — listed for completeness.

- **Ellis & van Elst 1998** — *Cargèse Lectures on Cosmological Models*, gr-qc/9812046. The standard 1+3 covariant formalism reference.
- **Challinor & Lasenby 2000 I** — Ann. Phys. 282, 285. Photon intensity PSTF hierarchy.
- **Challinor & Lasenby 2000 II** — Ann. Phys. 282, 321. Polarization PSTF hierarchy + Thomson collision in covariant form.
- **Maartens, Gebbie & Ellis 1999** — Phys. Rev. D 59, 083506. MES kinematic bounds.
- **Tsagas, Challinor & Maartens 2008** — Phys. Rep. 465, 61. Comprehensive 1+3 review.
- **Maartens 1998** — Phys. Rev. D 58, 124006. Covariant velocity/density perturbations, FLRW limit.
- **Ma & Bertschinger 1995** — ApJ 455, 7. Synchronous + Newtonian gauge brightness multipoles. (BASS oracle, not target.)
- **Lewis–Challinor–Lasenby 2000** — ApJ 538, 473. CAMB original paper.
- **Hu & White 1997** — Phys. Rev. D 56, 596. Total angular momentum method, `Π_BASS = Θ_2 + E_0 + E_2`.
- **Seljak & Zaldarriaga 1996** — ApJ 469, 437. Line-of-sight integration.
- **Kamionkowski, Kosowsky & Stebbins 1997** — Phys. Rev. D 55, 7368. E/B polarization.
- **Cyr-Racine & Sigurdson 2011** — arXiv:1012.0569, PRD 83, 103521. Second-order TCA corrections.

---

## §3. What we have tried — successes and failures

### §3.1 What worked (Round-15 P0)

**D-1 LoS grid decoupling fix** (commit `cb82a2a`):

- Replaced the integrator's 64-point uniform-linear η-grid (Δη ≈ 220 Mpc)
  in `_los_and_wrap` with a per-k composite grid: recombination-refined
  zone (Δη ≈ 2.4 Mpc, 8 samples per visibility FWHM) + k-adapted
  oscillation zone (Δη = 2π/(8k), Nyquist-resolves the Bessel kernel).
- Resolution-independence verified by sweep
  `n_per_oscillation ∈ {8, 16, 32, 64, 128}` — ratios constant to fourth
  decimal at every (k, ℓ) cell. **The new grid resolves the LoS
  quadrature; the projector is healthy.**
- Fast baseline 1753 passed (1723 pre-existing + 30 new module tests),
  no regressions to any anchor (Route-B Python golden, Route-B Rust,
  fb53 super-horizon ICs, R10/R11 seed checks, D_2 = 1002.086744 μK²).

**Empirical low-k match (post-D-1, with truncation lifted to η_init = 100 Mpc)**:

| (k, ℓ)   | k_adapted_η100 ratio vs CAMB direct |
|---|---:|
| 1e-3, 2  | 0.93 |
| 1e-3, 3  | 0.98 |
| 1e-2, 2  | 1.04 |
| 1e-2, 3  | 0.99 |

At every cell where the §10 oracle is itself valid (see §3.3), BASS's
PSTF assembly produces ratios within 5% of CAMB once the integrator's
η_init truncation is artificially lifted. **This empirically demonstrates
the BASS PSTF→observable LoS source assembly is structurally correct in
the FLRW limit.** The D1 derivation should give the algebra that
explains *why*.

### §3.2 What does not work (out of P0 scope, but constrains P1)

**D-2 — integrator η_init truncation**. BASS's IMEX integrator runs
from η_init ≈ 261 Mpc (z ≈ 1100) to η_today ≈ 14147 Mpc. CAMB
internally integrates from η ≈ 0.01 Mpc (z ≈ 10⁹). The pre-recombination
window [≈ 100, 261] Mpc carries non-trivial photon LoS contribution
(visibility g(η) extends ~ 1 FWHM below η_*). BASS's PCHIP source
extractor (extrapolate=False) cannot reach below η_init, so this fix
requires running the integrator further back in time (multi-month P2
track per session opener). **Not a P1 concern.**

### §3.3 Where the §10 oracle itself breaks (independent of BASS)

A diagnostic ([scripts/v5_round15_decisive_los_test.py](../scripts/v5_round15_decisive_los_test.py))
that originally compared BASS LoS to CAMB direct turns out to have a
limited validity scope. Even integrating CAMB's *own* `T_source`
(from `get_time_evolution(['T_source'])`) over CAMB's full η range
[0.1, 14153] with 30 000 trapezoidal samples gives:

| k (Mpc⁻¹) | LoS-of-CAMB-T_source / CAMB.delta_p_l_k (ℓ=2) |
|---:|---:|
| 1e-4 | 1.0000 ✓ |
| 1e-3 | 1.0000 ✓ |
| 5e-3 | 0.9998 ✓ |
| 1e-2 | 0.9999 ✓ |
| 3e-2 | 0.9685 ⚠ |
| 5e-2 | **−0.2213** ✗ |
| 8e-2 | **0.0001** ✗ |

So the identity `Δ_T = ∫ T_source · j_ℓ dη` only holds for k ≤ ~10⁻²
in CAMB. At higher k, CAMB's internal `delta_p_l_k` is computed using
additional source-term refinements (RSA, second-order TCA, possibly
Limber-like late-time projection) that are not in `get_time_evolution`'s
exposed `T_source`. **§10 is therefore not a valid validation target for
BASS at k > ~10⁻²** — what looks like "BASS error at high k" is largely
a CAMB-introspection artifact.

### §3.4 What the session opener got wrong about P1

The Round-15 session opener prescribed:
> P1 (D-3 gauge fix, sub-week):
>   `theta0_g_newtonian = theta0_g_synchronous + h_S_dot / 6`

But BASS does **not use the synchronous gauge** internally — its photon
RHS is purely PSTF / 1+3 covariant (T1 expansion + T7/T8/T9 shear +
Thomson, all gauge-invariant). There is no `h_S` to expose, and no
`h_S_dot` term in the BASS hierarchy. Verified by exhaustive grep for
`h_S | h_dot | h_prime | metric_trace | sync_h` across `htt/bass/`:
**no production-code matches**. The session-opener formula was inherited
from the MB-95 oracle path (`sync_gauge_camb.rs`); it does not transfer
to the PSTF target path.

The proper question for P1 is therefore **not** "convert sync to
Newtonian", but **"is the PSTF-native ℓ = 0 monopole convention the right
input for the BASS LoS source as written?"** The empirical answer at low k
is yes, but the formal derivation has not been written down.

### §3.5 What this hand-off changes about the Round-15 plan

The session opener's P1/P2/P3 was framed as a sequence of code patches.
The empirical evidence in §3.1–§3.4 reframes it:

- **P0 (D-1 LoS grid, code) — done, commit `cb82a2a`.**
- **P1 (PSTF formalization, docs only) — this hand-off. Audit-first.**
- **P2 (D-2 η_init extension, code, multi-month) — unchanged from the
  session opener.**
- **A potential P1.5 (high-k validation oracle, code, sub-week) — once
  the formalization gives an analytic limit, build a CAMB-independent
  test.** The session opener implicitly assumed CAMB direct could be
  used as a high-k oracle; §3.3 shows it cannot.

---

## §4. Gaps in the existing documentation

Even with [docs/lowell_bianchi_solver_reference.md](lowell_bianchi_solver_reference.md)
covering 18 sections of formalism, the empirical issues we hit indicate
the following gaps. The LLM session must close them.

### §4.1 Gap A — FLRW-limit LoS source derivation from PSTF first principles

The lowell-bianchi reference (§7, §8) describes the Tier-B state vector
and the SW/ISW/redshift source structurally, but does not give the
explicit step-by-step derivation that:

1. Starts from the PSTF radiation transport equation (Challinor–Lasenby
   2000 I eq. ~(40)–(45)) on a FLRW background.
2. Reduces to the `S_T = g·[Θ_0 + Ψ + Π/4] + e^{-κ}·[Φ̇+Ψ̇] + d/dη[g·v_b]`
   form in the BASS code.
3. Identifies the gauge / frame each Φ, Ψ, Θ_0, v_b, Π lives in, and
   shows the assembly is gauge-coherent (no silent gauge-mixing).
4. Cross-validates against the standard MB-95 / Lewis-Challinor LoS
   source as a limit.

This is needed because the Round-12→14 investigation (4 audit cycles)
and Round-15 §10 test surfaced doubt about whether BASS was assembling
the LoS source correctly. We now have empirical evidence that it is
correct at low k, but the derivation that explains *why* is missing.

### §4.2 Gap B — ℓ = 0 monopole convention

The Round-5 audit Q-16 stated "FLRW / Bianchi-I orthogonal → Θ_ℓ^VER2 =
Θ_ℓ^MB directly (no gauge-transformation coefficient)". This is correct
for ℓ ≥ 1 (gauge-invariant in PSTF around FRW per Ellis–van Elst). For
ℓ = 0 it is **not** a priori true — the energy-density contrast is
gauge / frame-dependent. The audit didn't separate the two cases.

What's needed:

1. The exact identification: is BASS's `t_tower[:, slot(0,0)]` the
   PSTF radiation-frame `Θ_0^PSTF`, or some gauge-projected variant?
   Trace it from the IC ([htt/bass/hierarchy/seed_compatibility.py](../htt/bass/hierarchy/seed_compatibility.py))
   through the RHS evolution to the source extractor.
2. The relationship to CAMB's `clxg = 4 Θ_0^MB` (CDM rest frame =
   synchronous gauge).
3. Whether the BASS LoS source assembly's `Θ_0 + Ψ` combination is
   actually a gauge-invariant observable, equal across all conventions,
   such that the ℓ = 0 distinction does not matter for the temperature
   transfer. (This is the typical MB-95 result; the question is whether
   it survives in the PSTF formulation.)

### §4.3 Gap C — Bianchi-essential extension blueprint

The session opener and various round-N notes mention that "PSTF/tetrad
is essential for Bianchi" but the implementation has not been pushed to
Bianchi yet beyond Bianchi-I (where m = ±2 ≡ 0 by structure). What's
needed:

1. A blueprint that takes the verified FLRW-limit assembly (Gap A
   output) and shows the systematic extensions for:
   - **Shear coupling**: σ_{ab} ≠ 0 introduces the T7/T8/T9 operators
     in [htt/bass/hierarchy/hierarchy_rhs.py](../htt/bass/hierarchy/hierarchy_rhs.py).
     The LoS source must inherit additional terms `σ_{ab} · Θ_{ab}` etc.
     What are they explicitly?
   - **m = ±2 channels**: derived from σ_{ab} eigen-structure of the
     Bianchi type. How do they couple back into the m = 0 LoS source?
     ([htt/bass/los/families/](../htt/bass/los/families/) currently
     has stub family backends — they need the explicit formalism.)
   - **Tilted observer**: when the matter rest frame `u_e^a` differs
     from the geometric normal `n^a`, what is the LoS source *seen* by
     the CMB observer? (cf. lowell-bianchi reference §1.2.)
   - **MES translation**: how does the resulting tetrad-frame Δ_ℓ
     relate to the `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`
     departure parameter?

2. The deliverable need not be a complete Bianchi II–IX implementation
   — it should be a derivation that's modular enough that the coding
   agent can pick it up one term at a time.

### §4.4 Gap D — High-k analytic validation oracle

§3.3 shows we cannot use CAMB direct for k > 10⁻². We need a closed-form
or high-precision analytic LoS source for which Δ_T is known
analytically — to verify BASS at high k without depending on CAMB
internals. Candidates:

- Sharp-visibility limit (g(η) → δ(η − η_*), Π = ISW = Doppler = 0):
  Δ_ℓ^T = (Θ_0 + Ψ)_* · j_ℓ(k(η_0 − η_*)). Already implemented in
  [htt/bass/los/flrw_bessel_projector.py::sachs_wolfe_analytic_transfer](../htt/bass/los/flrw_bessel_projector.py#L614).
  But this ignores the recombination width and Doppler at sub-horizon —
  needs extension.
- Gaussian visibility + analytic MD-limit Φ, Ψ, v_b: closed form via
  saddle-point evaluation of the Bessel integral.
- Toy oscillating source `Θ_0 = A cos(c_s k η)` + sharp visibility:
  acoustic peak structure at known kr_*.

The deliverable here is the *list of analytic limits with closed-form
Δ_ℓ^T expressions* that the coding agent can wrap into unit tests.

### §4.5 Gap E — Code mapping (audit-ready)

Each derivation result must be mapped explicitly to a BASS code line or
module, so an audit can verify the formalism is faithfully implemented.
None of the existing physics docs do this systematically — they point to
references but not to specific BASS source files / line numbers.

---

## §5. Prompt list for the external LLM session

Each prompt is self-contained — paste them sequentially. Each round
should produce a written deliverable that's appended to a single
working document, e.g. `docs/V5_ROUND15_P1_PSTF_DERIVATION.md`. After
each round, the user reviews and the next prompt fires.

The order is: **ground in repo → derive FLRW → audit ℓ=0 → Bianchi
extension → analytic oracles → code map → audit-ready deliverable.**

### Prompt R1 — Ground in repo state and prior work

```
You are a research-LLM tasked with formalizing the PSTF / 1+3 covariant /
tetrad treatment of CMB transport for the BASS Boltzmann solver. This
is a documentation-only deliverable; no code is to be written by you.

Read these documents in this order, in full:

  1. docs/V5_ROUND15_P1_EXTERNAL_LLM_BRIEFING.md       (this hand-off)
  2. docs/lowell_bianchi_solver_reference.md           (existing PSTF design, 18 sections)
  3. project/04_implementation_specs/CAMB_Tight-Coupling_Approximation_Mapped_to_the_1_3_PSTF_Covariant_Hierarchy_…md  (CAMB ↔ BASS mapping)
  4. docs/PHYSICS_REFERENCES.md                        (bibliography)
  5. htt/bass/los/flrw_bessel_projector.py             (LoS projector code)
  6. htt/bass/spectrum/tier_b_source_extraction.py     (Tier-B → Newtonian-gauge sources)
  7. htt/bass/hierarchy/hierarchy_rhs.py:343–540       (PSTF photon RHS: T1, T7, T8, T9 ops)
  8. htt/bass/hierarchy/integrator.py:223–260          (IntegrationResult schema)
  9. docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md              (P0 outcome)
 10. docs/audits/v5_round15_p0_d1_fix_transcript_2026-04-25.txt  (empirical numbers)
 11. docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md    (pre-fix investigation)

Then produce, as a numbered list, your understanding of:
 (a) What gauge / frame the BASS PSTF photon hierarchy lives in.
 (b) What the existing lowell_bianchi_solver_reference.md covers and
     what it leaves implicit.
 (c) The empirical state of the FLRW-limit BASS implementation
     post Round-15 P0 (cite specific (k, ℓ) numbers from the
     transcript).
 (d) The three open formalization gaps (FLRW derivation, ℓ=0
     convention, Bianchi extension) as listed in the hand-off §4.

Do NOT yet derive anything new. The purpose of this round is to
establish a shared understanding of the existing state. End with
2–3 questions you would want answered before deriving (Round R2).
```

### Prompt R2 — Derive the FLRW-limit PSTF LoS source from first principles

```
Now derive, step by step, the FLRW-limit line-of-sight source for the
CMB temperature transfer, starting from the 1+3 covariant photon
intensity transport equation (Challinor–Lasenby 2000 I, eq. ~(40)–(45)),
keeping PSTF variables I_{A_ℓ} as primary throughout.

Concretely:

 1. Write the PSTF radiation transport equation in the FLRW limit
    (σ_{ab} = 0, A_a = 0). Specialize to the m = 0 scalar mode.
 2. Apply the LoS integration prescription (Seljak–Zaldarriaga 1996).
    Show the integration by parts that produces the ISW driver.
 3. Identify the four physical contributions: SW, ISW, Doppler, polter
    (Π = Θ_2 − √6 E_2 in BASS convention — verify the sign and the
    √6 prefactor against Hu–White 1997 and KKS 1997).
 4. Express the assembled source S_T(η, k) in terms of:
       Θ_0(η, k)   = ?  ← state explicitly which gauge / frame
       Ψ(η, k)     = ?  ← Newtonian potential, derived from constraint
       Φ(η, k)     = ?
       v_b(η, k)   = ?
       Π(η, k)     = Θ_2 − √6 E_2 (BASS) vs other conventions
       g(η)        = visibility (Thomson)
       e^{−κ(η)}   = optical-depth weight
 5. Compare your result to the BASS implementation in
    htt/bass/los/flrw_bessel_projector.py::build_temperature_source.
    Identify any term-by-term differences. If there are no differences,
    state explicitly that the BASS form is the correct PSTF→observable
    LoS source in the FLRW limit, and explain why ℓ ≥ 1 PSTF
    multipoles are gauge-invariant on FRW (Ellis–van Elst 1998
    cite).
 6. Cross-validate by reducing your result to the MB-95 / Lewis-
    Challinor synchronous-gauge LoS source. Show that the LoS integral
    Δ_ℓ^T = ∫ S_T · j_ℓ(k(η_0 − η)) dη is gauge-invariant even though
    S_T(η, k) is not pointwise.

Deliverable: a self-contained derivation document (markdown, ~5–8 KB)
that any cosmologist can audit. Cite equation numbers from the
references at every step. End with a "consistency check" subsection
that lists the empirical evidence (BASS post-D-1 ratios from §3.1 of
the hand-off) and explains why this is now expected from the formalism.
```

### Prompt R3 — Audit the ℓ = 0 monopole convention

```
The Round-5 audit Q-16 stated "FLRW / Bianchi-I orthogonal →
Θ_ℓ^VER2 = Θ_ℓ^MB directly (no gauge-transformation coefficient)".
For ℓ ≥ 1 this is the standard Ellis–van Elst result. For ℓ = 0 it is
not, because the energy-density contrast is gauge / frame-dependent.
Audit this for the BASS case.

Specifically:

 1. Trace the BASS ℓ = 0 monopole through the code chain:
       seed_compatibility.py    →   IC at η_init
       hierarchy_rhs.py          →   evolution
       integrator.py             →   t_tower[:, slot(0,0)] storage
       tier_b_source_extraction.py:225  →   read out as `theta0_g`
    Identify which gauge / frame each step assumes.
 2. Derive the exact transformation between:
       Θ_0^PSTF      (BASS — radiation rest frame, comoving)
       Θ_0^MB^N      (Newtonian / longitudinal gauge, MB-95)
       Θ_0^MB^S      (CAMB — CDM rest frame = synchronous gauge)
    Use PSTF-native algebra. Do NOT introduce h_S, η_s, or other
    synchronous-gauge metric variables as primary — they are
    gauge-fixed quantities and should appear only as derived combinations.
 3. Show whether the BASS LoS source assembly
       S_T = g·[Θ_0 + Ψ + Π/4] + e^{−κ}·[Φ̇ + Ψ̇] + d/dη[g·v_b]
    requires any correction to its `Θ_0` term given that BASS uses
    PSTF Θ_0 while Ψ comes from a Newtonian-gauge constraint
    (i.e., is the assembly silently gauge-mixed?).
 4. Reconcile with the empirical observation (§3.1 of the hand-off)
    that the assembly produces ratios within 5% of CAMB at low k once
    the η_init truncation is lifted. Either:
      (a) the assembly is gauge-coherent by an algebraic identity that
          you must produce, OR
      (b) the residual is at the percent level due to a small gauge
          mismatch, which you must quantify (e.g., using the
          α = (h' + 6η')/(2k²) MB-95 transformation only as a
          pedagogical tool — the actual derivation should be PSTF-native).

Deliverable: a derivation appended to the R2 document, with explicit
formulas for the Θ_0 transformations and a verdict on whether BASS
needs any code-level correction.
```

### Prompt R4 — Bianchi tetrad-frame extension

```
With the FLRW-limit derivation (R2) and the ℓ = 0 audit (R3) in place,
extend the formalism to anisotropic Bianchi backgrounds. The user's
directive: PSTF / tetrad is the primary framework, not a stepping stone.

Bianchi II–IX cannot be expressed cleanly in synchronous gauge because
the spatial slices don't admit a global comoving CDM rest frame —
PSTF/tetrad is mandatory.

Cover:

 1. Tetrad transport on a Bianchi-I background (σ_{ab} ≠ 0, A_a = 0,
    flat 3-curvature). Reproduce the T7 (shear up: Π_{next-next}),
    T8 (shear same: Π_ℓ), T9 (shear down: Π_{prev-prev}) operators
    in htt/bass/hierarchy/hierarchy_rhs.py. Cite Challinor & Lasenby
    2000 I eqs.
 2. m = ±2 channel coupling. Currently zero in BASS for FLRW /
    Bianchi-I; how do they appear once the eigenstructure of σ_{ab}
    is non-trivial? Write the LoS source contributions
    Δ_ℓ^T,m=+2(k) etc. explicitly.
 3. Tilted observer: the lowell_bianchi_solver_reference.md §1.2
    fixes "transport in n^a frame, collision/source/visibility in u_e^a
    frame". Show how the LoS source from §2 above is written in the
    u_e^a frame, when n^a ≠ u_e^a (tilted Bianchi).
 4. Maartens–Ellis–Stoeger translation. Define
    x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso} from the kinematic
    bound hierarchy and show how x_C connects to the C_ℓ TT/TE
    spectra produced by the formalism above. Cite Maartens–Gebbie–
    Ellis 1999 and the tomographic_MES_framework.md note in the repo.
 5. For each item (1)–(4), give an explicit code-mapping table:

      | Formalism term | BASS file : line | Status (implemented / partial / TODO) |

    so the coding agent's follow-up has unambiguous targets.

Deliverable: extends the working document with the Bianchi blueprint.
Bianchi II–IX explicit derivation is out of scope; the deliverable is
the **structure** that allows later per-type expansion.
```

### Prompt R5 — High-k analytic validation oracle

```
Round-15 §10 tested BASS LoS by comparing to CAMB's `delta_p_l_k`.
Empirically (§3.3 of the hand-off), this comparison is only valid for
k ≤ 10⁻² Mpc⁻¹: at higher k, CAMB's exposed `T_source` (from
get_time_evolution) is not what CAMB integrates internally.

We need a CAMB-independent analytic oracle for high-k validation.
Produce a list of analytic limits with closed-form Δ_ℓ^T expressions
that the coding agent can wrap into unit tests in
htt/bass/los/test_flrw_bessel_projector.py.

Candidates to derive (closed form, no numerical integration):

 1. Sharp-visibility limit: g(η) → δ(η − η_*), Π = ISW = Doppler = 0.
    Δ_ℓ^T(k) = (Θ_0 + Ψ)_* · j_ℓ(k(η_0 − η_*)).  Already in BASS as
    `sachs_wolfe_analytic_transfer`; document the derivation cleanly
    and identify any extension needed.
 2. Gaussian visibility + matter-domination analytic Φ, Ψ:
    closed form via saddle-point evaluation of
    ∫ exp(−(η−η_*)²/2σ²) · j_ℓ(k(η_0−η)) dη at large k.
 3. Acoustic-peak toy: Θ_0 = A cos(c_s k η) + sharp visibility.
    Reproduces peak structure at kr_* = (n+1)π.
 4. Pure ISW (g → 0, Φ̇ + Ψ̇ ≠ 0 in DE-dominated era): closed form
    in the Limber limit at high ℓ.
 5. Pure Doppler limit (Θ_0 + Ψ = 0, only the d/dη[g v_b] term).

For each:
  - state assumptions explicitly,
  - derive Δ_ℓ^T(k) in closed form,
  - state the (k, ℓ) regime in which the limit is faithful,
  - propose tolerance for the unit test (e.g., 1% at k·η_0 ∈ [10, 100],
    ℓ = 2–10).

Deliverable: appended to the working document. The coding agent will
then add the corresponding tests.
```

### Prompt R6 — Code mapping table (audit-ready)

```
For every derivation result produced in R2–R5, produce a single
master code-mapping table with these columns:

  | § in derivation | Formula | BASS file : lines | Implementation status | Notes |

Cover at minimum:
  - LoS temperature source assembly (R2 §4 → flrw_bessel_projector.py)
  - LoS polarization source (R2 → flrw_bessel_projector.py
    build_polarization_source)
  - Φ, Ψ from Einstein constraints (R2 → tier_b_source_extraction.py
    lines 270–303)
  - Π = Θ_2 − √6 E_2 (R2 → tier_b_source_extraction.py:234)
  - PSTF photon RHS (T1, T7, T8, T9) (R4 → hierarchy_rhs.py:343–540)
  - ℓ = 0 monopole identification (R3 → seed_compatibility.py +
    integrator.py)
  - Bianchi shear coupling (R4 → hierarchy_rhs.py T7/T8/T9 already
    implemented; lowell_bianchi_solver_reference.md §6, §7 should
    be cross-referenced)
  - m = ±2 channels (R4 → htt/bass/los/families/* — currently stubs)

The table is the artifact a future audit agent will use to verify
"the formalism is faithfully implemented in code".

Deliverable: appended to the working document. Plus a 1-page
EXECUTIVE SUMMARY at the very top of the working document with:
  - the verdict (BASS PSTF assembly is correct / has these N specific
    issues),
  - the list of code changes (if any) the coding agent should make,
  - the analytic test oracles to add.
```

### Optional Prompt R7 — Audit prompt for review by a second LLM

```
You have produced a derivation document in R2–R6. Now write the audit
prompt for a separate reviewer (a second research-LLM session) to
verify your derivation independently.

The audit prompt should:
  - Provide the derivation document as input.
  - Ask the reviewer to flag any equation that is wrong, ambiguous,
    or under-cited.
  - Ask specifically for second opinions on:
      (a) the gauge / frame audit of Θ_0 (R3),
      (b) the BASS-form vs canonical-form comparison (R2 §5),
      (c) the m = ±2 coupling derivation (R4 §2),
      (d) the analytic oracle closed forms (R5).
  - Specify deliverable: a numbered list of (i) verified claims,
    (ii) requires-correction claims with proposed fix, (iii)
    requires-clarification claims with the question.

Deliverable: a paste-ready audit prompt (~1–2 KB).
```

---

## §6. Acceptance criteria for the LLM-session output

The hand-off succeeds when, at minimum, the output document contains:

1. **Executive summary** (≤ 1 page) with the verdict on BASS's current
   PSTF assembly correctness, and a list of any code-level changes
   needed (with file paths + line numbers).

2. **FLRW-limit derivation** of the LoS temperature source assembly
   from PSTF first principles, term-by-term reconciled with the BASS
   implementation in
   [htt/bass/los/flrw_bessel_projector.py](../htt/bass/los/flrw_bessel_projector.py)
   and [htt/bass/spectrum/tier_b_source_extraction.py](../htt/bass/spectrum/tier_b_source_extraction.py).

3. **ℓ = 0 monopole convention audit** with explicit transformations
   between PSTF, Newtonian, and synchronous conventions.

4. **Bianchi-extension blueprint** covering shear, m = ±2 channels,
   tilted observer, and MES translation, with code-mapping for each
   formalism term.

5. **Analytic oracle list** with closed-form Δ_ℓ^T expressions for at
   least 3 limits (sharp-visibility, Gaussian-visibility + MD, acoustic
   toy) and recommended unit-test tolerances.

6. **Master code-mapping table** linking every derivation result to a
   BASS file + line range.

7. (Optional) **Audit prompt** for a second LLM reviewer.

The user reviews and signs off before the coding agent picks up any
follow-up.

---

## §7. Constraints

1. **PSTF / tetrad is primary.** Newtonian gauge, synchronous gauge,
   CAMB, MB-95 are all *oracles* — they may be used to cross-validate
   in the FLRW limit, but the derivation must remain PSTF-native end
   to end. Bianchi II–IX cannot be expressed cleanly in synchronous
   gauge.

2. **No production-code changes from the LLM session.** The deliverable
   is documentation. Code follow-ups (analytic-oracle unit tests,
   any small assembly corrections) are the coding agent's task in a
   separate Round-15 sub-track that fires *after* the derivation has
   been audited.

3. **No CAMB import in BASS production trees.** This was a Round-15 P0
   constraint and remains in force. CAMB stays in
   `scripts/v5_round1*_*.py` audit/diagnostic scripts only.

4. **Anchor invariants must remain unaffected.** Any code change
   proposed in the executive summary (§6 item 1) must explain why
   it preserves: (a) Route-B Python golden D_2 = 1002.086744 μK²,
   (b) Route-B Rust D_2 = 1002.086744 μK², (c) 43 fb53 + 9 R10/R11
   super-horizon IC tests, (d) D-1 fix's resolution-independence at
   the LoS projector.

5. **Derivations must be cited.** Every equation cited from a paper
   should reference equation number. Every claim that maps to BASS
   code should reference file + line range.

6. **`project/` is gitignored** — local-only planning tree. The LLM
   session can read these docs (the user has them locally) but the
   final deliverable should live in `docs/` so it can be committed.

---

## §8. Recommended deliverable filename

`docs/V5_ROUND15_P1_PSTF_DERIVATION.md`

After the LLM session finishes and the user signs off, the coding
agent will commit this doc, append a CHANGELOG entry, and begin any
code follow-ups identified by the executive summary.
