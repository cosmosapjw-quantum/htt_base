# CLAUDE.md excerpts (project SSoT)

The full `CLAUDE.md` lives at the repository root. The relevant sections for this audit are §1 (project identity), §3 (current phase status), §5 (physics anchors), and §6 (forbidden constructs). Excerpted below at last commit `02cb6c0`, last updated 2026-04-27.

---

## 1. Project identity

- **Name**: BASS (Boltzmann And Spectrum Solver / Bianchi Anisotropy Solver)
- **Thesis context**: Jiwon (Soongsil OMEG Institute), PhD thesis _"Tetrad-Based Departure Decomposition for FLRW Departure in Bianchi Anisotropic Cosmologies"_
- **Goal**: Compute CMB T+E+B spectra for 9 Bianchi types via the master departure identity `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`, linked to the Maartens–Ellis–Stoeger kinematic bound hierarchy
- **Production anchors**: `ln B(FLRW_tilt) = +26.40`, `β = 1.360×10⁻³`, `F_Bayes = 0.093 ± 0.025`
- **Dual-track architecture**:
  - `sync_gauge_camb.rs` (7363 lines) — MB-95 production path (CAMB-convention sync gauge, Rodas5P ODE)
  - PSTF primary — 1+3 covariant `I_{A_ℓ}` hierarchy (Ellis-van Elst), target formulation for Bianchi+tilt
- **Phase 1 objective**: PSTF primary produces bit-identical `D_2 = 1002.086744 μK²` vs MB-95 production. On completion, PR-026 switches production path from MB-95 → PSTF primary.

## 3. Current phase status (excerpts)

- **Phase 1 progress at PR-024a**: 50.8% (53.3 / 105 weighted); D_2 = 1002.086744 μK² regression anchor holds bit-identical across 14+ consecutive commits + 8 residual-joint operator patches (2026-04-24 runtime-track).
- **PR-024 remaining**: PR-024b (time integration + source grid), PR-024c (LoS + spectrum assembly, **PSTF D_2 bit-identical target**).
- **V5 Round-17 P2 status (2026-04-27 post-linear-probe-measurement)**:
  - **(a) primordial-amplitude alignment empirically confirmed** as the dominant gap. `compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)` at N_k=65 yields **D_2 = 6.4395 × 10³ μK²**, residual ratio **6.43** vs the Rust MB-95 anchor 1002.086744 μK².
  - **Residual 6.43× triangulated to V5_ROUND12_TO_14 D-2.** The Lowell §13.2 leading-order seed `_seed_formulae` is valid only for `x = k·η_init ≪ 1`; at η_init ≈ 261 Mpc the boundary is `k ≈ 4e-3 Mpc⁻¹`, and the R17 k_grid `np.logspace(-4.0, -1.5, 65)` spans `x ∈ [0.026, 8.25]` (>50% in the invalid region). 10-auditor 4-cycle Round-12-14 consensus: residual is **not a single missing convention factor** (R14 finding F1: per-(k, ℓ) std/|mean| 108-357% across all candidate factors).
  - **Sub-track ordering revised** to (a-switch) → (c) → (b) → D-2. Only D-2 closure (multi-month, Round-15 P2 actionable) flips `test_d2_pstf_closure.py` to `xpass`.
- **V5 runtime-track status (2026-04-26 post-session)**:
  - Round-15 **P0 (D-1 LoS grid decoupling) CLOSED**.
  - Round-15 **P1 (PSTF formalization) CLOSED as documentation + regression armor track**.
  - Round-15 **P2 (D-2 integrator η_init extension, multi-month) actionable** — push integrator η_init to z ~ 10⁹ via tight-coupling.
  - Blocker 1 (`multipole_cutoff` ≤ 40) **CLOSED**.
  - Blocker 2 (IMEX cosmological-range stability) **CLOSED** via 8 patches in `bass/hierarchy/ver3_layout_protocol.py`. λ_max(A_right) ≈ 1e-16 (machine precision); cosmological η = 261→14147 Mpc IMEX completes in 130 s.
  - Blocker 3 (real IC injection at `η(z_*)`) **actionable** — operator is stable.

## 5. Physics parameters (SSoT values)

From `docs/SSOT_POLICY.md` and `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`:

- **T_CMB canonical value**: `2.72548 K` (Fixsen 2009, ApJ 707, 916 central value).
- **D_2 regression anchor (Phase 1, FLRW limit)**: `D_2 = 1002.086744 μK²`. **Provenance**: anchor is currently *enforced* by the Rust-side `bass_rs dump_dl_spectrum_sparse` (MB-95 production path); on the Python (PSTF primary) side the anchor is a *target* tracked by PR-024c (LoS + spectrum assembly) and is **not yet bit-identical**. The Python-side closure regression lives at `htt/bass/spectrum/test_d2_pstf_closure.py` and is currently `xfail("PR-024c open")`. Has held across 14 consecutive commits *on the Rust path*.
- **Σ² (shear-squared) anchor point for gallery**: `D_2(Σ²=1e-8) = 0.174112 μK²`.
- **Canonical Thomson primitive**: `Π_BASS ≡ Θ₂ + E₀ + E₂` (see `docs/SSOT_POLICY.md §2.3`). Polter convention used in production: `polter = 2Θ_2/5 + 3E_2/5` (E₀ unused).
- **SSoT authority order**: exact/full transport → basis-normalized hierarchy → canonical source primitives → LoS/observable assembly → export bridge. No direct raw-to-source paths.
- **Stack ownership boundary**: BASS owns physics; HTT owns observation bridge; MIO owns reporting semantics.

## 6. What NOT to do in new sessions (forbidden constructs)

- Do not introduce the approximation-free-banned constructs: **TCA pre-phase, FLRW UFA, photon RSA** (approximation-free truth engine is mandated — see `docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`).
- **Clarification (2026-04-26)**: the *banned* construct is the TCA *pre-phase* (i.e. an unconditional analytic solution replacing the photon hierarchy in an initial η-window). The conditional inline DAE-relaxation dispatch in `htt/bass/hierarchy/integrator.py:434-498` — which only pins `ℓ=2 m=0` to its algebraic limit when `Γ_T/H > closure.gamma_threshold_over_H` — is **permitted** because the ODE is integrated throughout, the hierarchy is never replaced, and the relaxation timescale `1/Γ_T` collapses smoothly onto the off-TCA branch as `Γ_T/H → threshold`. A switch-smoothness audit is enforced by `htt/bass/hierarchy/test_tca_switch_smoothness.py`.

---

**Note for the auditor:** the full `CLAUDE.md` carries additional sections on directory layout, manuscript anchors, and session hygiene. None of those bear on the open closure question. If something here references a missing context, the full file is recoverable from the repo root.
