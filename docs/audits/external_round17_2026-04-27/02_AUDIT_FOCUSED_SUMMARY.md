# BASS Phase-1 Closure — External Audit Brief
**Date:** 2026-04-27.   **Branch / commit:** `main` @ `02cb6c0`.   **Audit subject:** the 6.43× linear-probe D_2 residual.

This brief is **complementary** to `01_DETAILED_ANALYSIS.md`: it skips the codebase exposition and goes directly to (i) the focused problem statement, (ii) the development history compressed to facts, (iii) what was tried and verdict per attempt, (iv) the remaining plan, (v) blockers, and (vi) the questions we want the auditor to answer. The intent is for an auditor to be able to read this brief in 15 minutes and deliver a verdict in their preferred medium.

---

## 1. Problem statement

**Goal.** The Python "PSTF primary" CMB pipeline must reproduce the Rust MB-95 production anchor `D_2 = 1002.086744 μK²` for FLRW Planck-2018 to within 1 × 10⁻⁹ fractional tolerance. When that happens, the regression test `htt/bass/spectrum/test_d2_pstf_closure.py` (currently `xfail("PR-024c open")`) flips `xpass`, the xfail marker is removed, and PR-026 retires the Rust path.

**Current state (commit `02cb6c0`, measured 2026-04-27):**

| Path | D_2 (μK²) | Δ vs anchor | Ratio |
|---|---:|---:|---:|
| Rust MB-95 anchor (`bass_rs::dump_dl_spectrum_sparse`) | **1002.086744** | — | 1.00 |
| Python canonical (`compute_flrw_d_ell`) | **2.0451 × 10¹⁰** | +2.04 × 10¹⁰ | 2.04 × 10⁷ |
| Python linear-probe (`compute_flrw_d_ell_linear_probe`) | **6.4395 × 10³** | +5.44 × 10³ | 6.43 |

**The residual we're asking about: the 6.43× ratio between the linear-probe path and the anchor.** The 7-orders-of-magnitude canonical-vs-linear-probe gap is cleanly explained by the `max(|Σ_±|, 1e-6) = 1e-6` floor that `unit_amplitude_normalization=True` applies in the FLRW limit (boosts |α|² by ~10¹²). Mechanism is settled; closure is mechanical (1–2 days). The 6.43× is the open question.

**Internal triangulation:** The 6.43× has the *D-2* signature (Lowell §13.2 leading-order seed valid only for `x = k·η_init ≪ 1`; at η_init = 261 Mpc the validity boundary is k ≈ 3.83 × 10⁻³ Mpc⁻¹; the test k-grid `np.logspace(-4.0, -1.5, 65)` has **about 37% (24/65) of points in clear `x > 1` invalid territory and ~57% in marginal `x > 0.3` asymptotic-danger territory** — corrected from an earlier "~60%" claim by Round-17 audit Report 1). Prior 10-auditor / 4-cycle consensus (Round-12-14, 2026-04-25): per-(k, ℓ) std/|mean| 108–357% across all candidate single-multiplicative-factor explanations — refutes any "missing convention factor" story.

**Proposed closure (multi-month):** push the IMEX integrator's `η_init` from `261 Mpc (z ≈ 1100)` to `~10⁻³ Mpc (z ≈ 10⁹)`, where `x = k·η_init ≪ 1` for the entire Planck-relevant k-grid. The conditional inline DAE-relaxation already implemented at `htt/bass/hierarchy/integrator.py:434–498` is the load-bearing mechanism for handling the radiation-era TCA regime.

---

## 2. Development history (compressed to facts)

**Phase 1 anchor and dual-track architecture established 2026-04-19** (Round-1, before any of the convention-residual work). Production anchor `D_2 = 1002.086744 μK²` from Rust `bass_rs/src/sync_gauge_camb.rs::dump_dl_spectrum_sparse`. Bit-identical across 14+ subsequent commits.

**Round-8 (2026-04-23)** — Single-k linear probe (`compute_linear_probe_transfer_function`) introduced at `htt/bass/spectrum/flrw_pipeline.py`. Established that the IMEX response to seed amplitude is linear in `b_k_sq ∈ [10⁻³, 10]`.

**Round-9 (2026-04-24)** — Multi-k linear-probe wrapper (`compute_flrw_d_ell_linear_probe`) introduced. R9-A discovered the `unit_amplitude_normalization=True` 1e-6 floor (boosts |α|² by ~10¹² in FLRW). Disabling it dropped D_2 from `~10⁶⁷ μK²` (pre-fix) to `~10⁷ μK²`. R9-D §5d located a real seed-formula bug: `pi_nu` and `G_3` in `_seed_formulae` were *missing the `B_K_sq` linear factor* present in every other moment, asserting "ν quadrupole/octupole exist at b_k_sq = 0" — unphysical for an adiabatic mode and the source of the visibility-source bias floor that `bias_subtraction=True` was originally invented to mask.

**Round-10/Round-11 (2026-04-24)** — R9-D bug fix landed. Convention-audit residual ratio: 1.36 × 10⁴ (R9 N_k=24) → 7.57 × 10² (post-R11 N_k=variable). 18× improvement from one bug fix.

**Round-12-14 (2026-04-25)** — Three audit cycles, **10 external auditor verdicts total** (4 in R12, 3 in R13, 4 in R14), plus 5 internal Phase A/B-fix diagnostic stages. Key Round-14 findings (`docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md`):

- **F1.** No single multiplicative factor closes the residual. Per-(k, ℓ) std/|mean| 108–357% across all candidates (4√2, n_output, k_min clipping, Doppler resampling).
- **F2.** BASS doesn't converge in `n_output`. Sign flips at `n_output ≥ 256`; PCHIP overflow warnings.
- **F3.** SW + polter and ISW are individually wrong; Doppler is < 0.5% of the residual.

Three-defect consensus (D-1 / D-2 / D-3) emerged. 4/4 R14 auditors recommended HYBRID (use CAMB transfer for FLRW limit). User (2026-04-25) **rejected HYBRID** — "BASS code itself must generate the correct data; CAMB is only a comparison target." Multi-month BASS-native fix path adopted.

**Round-15 P0 (2026-04-25)** — D-1 (IMEX/LoS grid conflation) **CLOSED**. New module `htt/bass/los/los_grid_builder.py::build_los_grid` decouples LoS quadrature grid from IMEX output grid. Per-k composite grid: recombination zone `Δη = 2.4 Mpc` + k-adapted oscillation zone `Δη = 2π/k/8`. §10 decisive test: median |ratio| 8.30 → 1.00, max 3687 → 266, resolution-independent. 30 unit tests, fast baseline 1753 passed. Also closed Round-14 Blocker 1 (multipole_cutoff ≤ 40 hardcoded) and Blocker 2 (IMEX cosmological-range stability — 8 algebraic patches in `htt/bass/hierarchy/ver3_layout_protocol.py` brought `λ_max(A_right)` from `+0.175 / Mpc` to `~ 4 × 10⁻¹⁶`).

**Round-15 P1 (2026-04-26)** — Originally framed as "D-3 sync→Newt h_S′/6 patch"; that framing **retired** during the session because BASS hierarchy is PSTF/tetrad-native (verified at `htt/bass/hierarchy/hierarchy_rhs.py:343` + `htt/bass/hierarchy/seed_compatibility.py:210`). Two external-LLM derivations landed (`docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` is R7-authoritative; `docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md` is parallel-cycle, retracted as Appendix X "false trail"). Doppler `/k` patch from the parallel-cycle derivation was retracted and verified-against by code evidence. Test/diagnostic outputs landed (4 sharp-visibility analytic oracles + monopole-frame diagnostic). **No production-code changes.**

**Round-16 (2026-04-26)** — 14 PRs (S1–S14) of Bianchi primitives: codazzi-tilt RHS, IMEX ARK4(3)6L[2]SA validation, mode-mixing blocks, seed factory, family k-grid, B-mode projector, LoS family propagators, forward map producer, Planck likelihood scaffold. 287 primitive baseline tests, 15.80 s. Production code unmodified at the FLRW pipeline level — these primitives are wired up but not yet dispatched into the FLRW path.

**Round-16 P2 (2026-04-26)** — Doppler `/k` mandate from the Round-16 handoff **retracted** based on empirical 2 × 28 min `compute_flrw_d_ell` measurement: the patch shifts D_2 by **−0.012%, not the spec-claimed 0.5%**. Mandate originated from the parallel-cycle derivation already retracted in R15 P1. PR-S13 re-scoped to three sub-tracks (a) primordial-amplitude alignment, (b) state-layout `m=0 → m∈{-2..+2}`, (c) real-IC at η(z_*).

**Round-17 P2 (2026-04-27, this session)** — `compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)` measured at N_k=65 in 31.4 min: **D_2 = 6.4395 × 10³ μK², residual 6.43×**. PR-S13 sub-track (a) confirmed empirically closed by the existing linear-probe path. The 6.43× residual triangulated to D-2.

---

## 3. What was tried, and verdict

### Tried + succeeded

| Attempt | Round | Outcome | Quantitative effect |
|---|---|---|---|
| `unit_amplitude_normalization` 1e-6 floor disable | R9-A | landed via wrapper override | 10⁶⁰ ratio reduction (10⁶⁷ → 10⁷) |
| ν seed bug fix (`pi_nu`, `G_3` missing `B_K_sq`) | R10/R11 | seed-formula correction | 18× ratio reduction (1.36 × 10⁴ → 7.57 × 10²) |
| LoS grid decoupling (D-1) | R15 P0 | new module `los_grid_builder.py`; `_los_and_wrap` reroute | 117× ratio reduction (7.57 × 10² → 6.43); §10 test resolution-independent |
| IMEX residual-joint operator algebraic fixes | R14/R15 | 8 patches in `ver3_layout_protocol.py` (sign flips, Wigner-Eckart, Thomson sign, Π-source, …) | `λ_max(A_right)` `+0.175 → 4 × 10⁻¹⁶ / Mpc` (machine zero) |
| IMEX cosmological-range stability validation | R15 | `bce0eb9` integration test | η = 261 → 14147 Mpc completes in 130 s |
| Doppler `/k` regression armor | R16 P2 | new test `test_sharp_visibility_doppler_analytic_protects_no_over_k_patch` | prevents future re-litigation |
| `cosmological_config.py` build helper | R15 | `build_cosmological_integrator_config(species, …)` | replaces `eta_initial_mpc=0.5` toy sentinel |

### Tried + refuted (with prior-art evidence trail)

| Hypothesis | Round | Verdict | Why it failed |
|---|---|---|---|
| C-a: `B_K_sq = ζ²` double-counting | R12 | 4/4 REFUTED | seed bugs (R10/R11) already fixed; bias-floor empirically zero |
| Option A: `k_min` clipping | R12, R13 | 7/7 REFUTED | masks physical SW peak; doesn't fix per-(k, ℓ) variance |
| 4√2 = √(32) PSTF normalization | R13 (Codex) → R14 | fortuitous integrated averaging | per-(k, ℓ) std/|mean| 108–357% |
| `n_output` increase | R13 (Opus) → R14 | BASS doesn't converge | sign flips at n_output ≥ 256, PCHIP overflow warnings |
| Doppler `np.gradient` undersampling | R13 → R14 ablation | < 0.5% | F3: Doppler is not the residual |
| IMEX projection drift via every_n_steps | Phase A D4 | bit-identical | not the cause |
| Single missing convention factor (any) | R12, R13, R14 | falsified by F1 | per-(k, ℓ) variance pattern |
| Doppler `(g v_b)′ → (1/k) d/dη[g v_b]` | R16 (handoff spec) → R16 P2 | 0.012% effect, not 0.5% spec | inherited from retracted parallel-cycle audit; v_b already dimensionless θ_b/k |
| HYBRID architecture (CAMB transfer for FLRW) | R14 | 4/4 RECOMMENDED → user-rejected | external runtime dep forbidden by user policy |
| `_seed_formulae` higher-x corrections (D-2b) | R12-14 | non-viable | series asymptotic; ~20 orders required at x = 14, then divergent |

### Open / not yet tried

| Item | Sub-track | Status |
|---|---|---|
| Switch canonical default to linear-probe path / disable 1e-6 floor in canonical | α (a-switch) | actionable, 1-2 d, awaiting user decision |
| Real-IC injection at η(z_*); `BackgroundMonitor.from_recombination` | β (c) | actionable, 1-2 d, awaiting user decision |
| State-layout migration `m=0 → m∈{-2..+2}` (wires R16 primitives) | γ (b) | actionable, 3-5 d, awaiting user decision |
| Push η_init to z ≈ 10⁹ via TCA-enabled startup (D-2 closure) | δ | multi-month, awaiting user decision |
| Source extractor `Θ_0_S → Θ_0_N + h_S′/6` gauge conversion (D-3) | (D-3) | sub-week if integrator exposes h_S′; documented but not entered |

---

## 4. Forward plan & blockers

**Sub-track ordering recommended (current `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md §4 revised`):**

```
α (a-switch, 1-2d)  →  β (real-IC, 1-2d)  →  γ (m∈{-2..+2}, 3-5d)  →  δ (D-2, multi-month)
```

Rationale (compressed):
- α has the smallest unit of visible PSTF-side progress and updates `test_d2_pstf_closure.py` xfail message to point at D-2 (better CI signal than current "PR-024c open" placeholder). Doesn't close `xpass`.
- β closes the CLAUDE.md §3 Round-15 P2 monopole-frame caveat. Independent of the residual.
- γ enables off-axis Bianchi families. Not the source of the FLRW residual.
- δ is the only path to bit-identity and `xpass`.

**Hard blockers (none active right now):**

- IMEX cosmological-range stability — **CLOSED 2026-04-24** by 8 algebraic patches.
- LoS grid undersampling — **CLOSED 2026-04-25** by `los_grid_builder.py`.
- `multipole_cutoff ≤ 40` hardcoded — **CLOSED** by Blocker 1 fix.

**Soft blockers (work-stream-level):**

- δ requires re-validating the IMEX across 6 additional decades of η (z ≈ 1100 to z ≈ 10⁹). Each decade requires conservation-law audit (Codazzi, momentum, energy).
- δ requires re-validating switch-smoothness of the conditional inline DAE-relaxation across 6 decades of `Γ_T / H` (from ~10² at recombination to ~10⁹ at z = 10⁹). The transition through the threshold must remain smooth.
- δ requires real-IC populated at z = 10⁹ for all species (radiation-era IC for photon, baryon, CDM, neutrino synchronously). Existing `cosmological_config.py` defaults to η(z_*) − 20 Mpc; a z = 10⁹ variant must be added.

**Anchor invariants (preserved throughout — verifiable):**

- Rust `D_2 = 1002.086744 μK²` (independent code path) — bit-identical across 14+ commits.
- Route-B Python golden MM-curve `D_2(Σ² = 10⁻⁸) = 0.174112 μK²` (analytic, no PSTF) — unaffected.
- 287 Round-16 primitive baseline tests in 15.80 s — fast verification path.

---

## 5. Specific questions for the auditor

**Q1 (Diagnosis).** Is **D-2** (Lowell §13.2 leading-order seed validity range applied at η_init = 261 Mpc, where ~37% of the test k-grid sits in clear `x > 1` invalid territory and ~57% in marginal `x > 0.3` asymptotic-danger territory) the correct diagnosis for the 6.43× residual? Are there alternative explanations consistent with:
- Per-(k, ℓ) std/|mean| 108–357% (R14 finding F1) ruling out single multiplicative factors;
- N_k-dependent ratio trajectory `2.93 × 10⁴ → 1.36 × 10⁴ → 7.57 × 10² → 6.43` across improvements;
- ν seed bug fix already landed (R10/R11);
- D-1 (LoS grid) already closed (R15 P0);
- BASS not converging in `n_output` (R14 F2);
- The fact that `(D-2b)` higher-x corrections to `_seed_formulae` are non-viable (asymptotic series, ~20 orders needed at `x = 14`)?

**Q2 (Closure mechanism).** Is the proposed D-2 closure (push integrator `η_init` to `z ≈ 10⁹` via the conditional inline DAE-relaxation already implemented at `htt/bass/hierarchy/integrator.py:434–498`) the correct mechanism? Concerns to weigh:
- Cosmological-range IMEX is proven stable for 5 decades (η = 261 → 14147 Mpc); we'd need to extend to 12 decades (η = 10⁻³ → 14147 Mpc).
- The DAE-relaxation is currently audited at switch-smoothness across the recombination transition (`Γ_T / H ~ 10² → 10⁻¹`); we'd need the same to hold across the full TCA→post-TCA transition (`~ 10⁹ → 10⁻¹`).
- The IMEX integrator is currently restricted to ℓ ≤ 40 (post Blocker 1 fix); does deep TCA ever require higher ℓ before pinning?

**Q3 (DAE-relaxation sufficiency).** Is the conditional inline DAE-relaxation at `htt/bass/hierarchy/integrator.py:434–498` (which pins **ℓ = 2 m = 0** to its algebraic Thomson-coupled value when `Γ_T / H > closure.gamma_threshold_over_H`) sufficient to carry the seed through the radiation era? Specifically:
- Should higher-ℓ photon multipoles be similarly pinned in deep TCA (`Γ_T / H ≫ 1`)? Or do they free-stream stably?
- Is the `relax_rate = a · Γ_T` choice numerically appropriate for `Γ_T / H ~ 10⁹` at z = 10⁹? Or does it become so stiff that the implicit IMEX stage rejects the substep?
- Does the threshold `gamma_T_over_H_threshold = 100` need re-tuning at deeper anchors, or does smoothness audit guarantee the choice is anchor-independent?

**Q4 (Other defects we may have missed).** Three audit cycles converged on D-1 / D-2 / D-3 as the consensus. Are there *other* architectural defects we may not have identified that could contribute to the 6.43× residual? Examples we considered and tested:
- **Source extractor sign convention** in `tier_b_source_extraction.py` — partially audited as D-3.
- **PSTF normalization** at the LoS projector — investigated Round-13 (4√2 candidate), refuted.
- **Polarization quadrupole basis convention** — Π_BASS = Θ_2 + E_0 + E_2 vs polter = (2Θ_2/5 + 3E_2/5); cross-checked at `docs/SSOT_POLICY.md §2.3`. Not yet directly stress-tested at low-k.
- **Background table interpolation** — HYREC table is shared between Rust and Python paths; interpolation strategies differ. Not directly tested as a residual source.

**Q5 (Sub-track ordering).** D-3 (sync/Newt gauge mismatch in source extractor at `tier_b_source_extraction.py:225` combined with Newtonian-gauge Ψ at `flrw_bessel_projector.py:448`) is **sub-week** vs δ which is **multi-month**. Should D-3 be closed before δ? Considerations:
- D-3 is currently not blocking any user-facing functionality.
- D-3 magnitude is uncertain — Phase A FIXED transcript at `k = 10⁻⁴` showed Ψ sign flip in matter era and linear-in-η Θ_0 drift (canonical synchronous-gauge growing mode), suggesting non-trivial contribution. But the Round-15 P0 D-1 fix may have absorbed some of D-3's effect (the sub-track was originally P1 of Round-15, then re-scoped after evidence that BASS hierarchy is PSTF-native).
- D-3 closure could leak into δ's measurement budget if it's conflated with the seed-validity residual.

---

## 6. Materials provided in this audit bundle

| File | Purpose |
|---|---|
| `00_README.md` | Bundle map and usage notes |
| `01_DETAILED_ANALYSIS.md` | Self-contained ~25 KB technical analysis (physics + code-internal algorithms) |
| `02_AUDIT_FOCUSED_SUMMARY.md` (this file) | Compressed audit brief |
| `03_AUDIT_PROMPT.md` | The prompt to send to the auditor |
| `code/flrw_pipeline.py` | Canonical entry point + linear-probe wrapper |
| `code/cl_assembly.py` | C_ℓ assembly + Planck-2018 P_R(k) wiring |
| `code/regular_adiabatic_ic.py` | `_seed_formulae` (D-2 source code) |
| `code/los_grid_builder.py` | Round-15 P0 D-1 fix |
| `code/integrator.py` | IMEX + conditional inline DAE-relaxation (lines 434–498) |
| `code/test_d2_pstf_closure.py` | The closure regression test (xfail) |
| `code/v5_round17_linear_probe_measurement.py` | Reproduction script (31 min wall time on 4 workers) |
| `reference_docs/V5_ROUND17_PR_S13_REAL_SCOPE.md` | Current scope ticket (this round) |
| `reference_docs/V5_ROUND17_NEXT_SESSION_OPENER.md` | Bootstrap doc for fresh sessions |
| `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` | Three-defect 10-auditor consensus |
| `reference_docs/V5_ROUND9_FINDINGS.md` | Linear-probe origins + ν seed bug |
| `reference_docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md` | D-1 closure record |
| `reference_docs/V5_RUNTIME_TRACK_DIAGNOSIS.md` | Blockers 1 + 2 closure (8 algebraic patches) |
| `reference_docs/CHANGELOG_excerpts.md` | Round-16 P2 + Round-17 P2 entries |

---

**End of audit-focused summary.** The detailed reasoning behind every claim in this brief is in `01_DETAILED_ANALYSIS.md`.
