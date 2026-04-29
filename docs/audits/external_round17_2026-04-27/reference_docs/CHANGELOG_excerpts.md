# CHANGELOG excerpts — Round-16 P2 + Round-17 P2

The full `CHANGELOG.md` lives at the repository root. This file extracts the two
entries directly relevant to the audit — Round-16 P2 (Doppler `/k` retraction)
and Round-17 P2 (linear-probe measurement, residual triangulation).

---

## V5 Round-17 P2: PR-S13 (a) confirmed via linear-probe; residual 6.43× = D-2 (2026-04-27)

Doc + diagnostic-script-only PR (no production code change). Confirms
the `V5_ROUND17_PR_S13_REAL_SCOPE.md §3 (a)` "primordial-amplitude
alignment" hypothesis as the dominant gap and triangulates the
remaining 6.43× residual to the V5_ROUND12_TO_14 D-2 defect (Lowell
§13.2 leading-order seed validity range).

**Empirical measurement (this session, 1 × 31.4 min
`compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)` run at 65
k-points × 4 workers, run on commit `7722f95`):**

| Path | D_2 (μK²) | Δ vs Rust MB-95 anchor | Ratio |
|---|---:|---:|---:|
| Rust MB-95 anchor | 1002.087 | — | 1.00 |
| Canonical `compute_flrw_d_ell` (Round-16 P2 baseline) | 2.0451 × 10¹⁰ | +2.0451 × 10¹⁰ | 2.04 × 10⁷ |
| **R17 (C) `compute_flrw_d_ell_linear_probe`** | **6.4395 × 10³** | **+5.4374 × 10³** | **6.43** |

The linear-probe path closed **6.4 orders of magnitude** of the
canonical path's gap by disabling the spurious
`max(|Σ_±|, 1e-6) = 1e-6` floor (FLRW limit Σ_±=0) that
`unit_amplitude_normalization=True` applies, plus the bias-subtraction
pair (b_k_sq=0 + b_k_sq=probe; `Δ_pure = Δ_target − Δ_bias`). This
matches V5_ROUND17 §3 (a) ship gate (within ~25× of anchor →
"primordial normalization confirmed as dominant gap").

**Triangulation of the residual 6.43× to D-2.** The convention-audit
trajectory across the BASS-team investigation history:

| Round | N_k | D_2^probe / D_2^Route-B |
|---|---:|---:|
| R9 (`V5_ROUND9_FINDINGS.md` §2, post seed bug-fix start) | 4 | 2.93e+04 |
| R9 dense | 24 | 1.36e+04 |
| R12-14 (post-R11, `V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` TL;DR) | — | 7.57e+02 |
| **R17 P2 (this measurement)** | **65** | **6.43** |

The 117× improvement R12-14 → R17 came principally from Round-15 P0
(LoS grid decoupling). The remaining 6.43× has the V5_ROUND12_TO_14
D-2 signature: at η_init ≈ 261 Mpc, `_seed_formulae` is the leading-
order Lowell §13.2 expansion, valid only for `x = k·η_init ≪ 1` (i.e.
`k ≲ 4e-3 Mpc⁻¹`). The R17 k_grid `np.logspace(-4.0, -1.5, 65)` spans
`x ∈ [0.026, 8.25]`; over half the points sit in the `x > 1` invalid
region. Per the 10-auditor 4-cycle Round-12-14 consensus, the
residual is **not a single missing convention factor** — R14 finding
F1 measured per-(k, ℓ) std/|mean| at 108-357% across all candidate
factors (4√2, n_output, k_min clipping, Doppler resampling), all
REFUTED.

**Sub-track scope re-alignment** (recorded in
`V5_ROUND17_PR_S13_REAL_SCOPE.md §4` revised + new §7):

- (a) primordial-amplitude alignment is **empirically closed** at the
  linear-probe path. The (a) implementation work reduces to switching
  `compute_flrw_d_ell` default to invoke the linear-probe path (or
  equivalently, disabling the 1e-6 floor in the canonical path).
  1-2 days. Does **not** close the residual 6.43×.
- (c) real-IC injection at η(z_*) is **independent**; addresses the
  CLAUDE.md §3 Round-15 P2 monopole-frame contract. 1-2 days.
- (b) state-layout migration `m=0 → m∈{-2..+2}` enables off-axis
  Bianchi families. 3-5 days. Not the FLRW residual source.
- **D-2 (multi-month)** is the only sub-track that closes the 6.43×
  residual to bit-identity and flips `test_d2_pstf_closure.py` to
  `xpass`. CLAUDE.md §3 Round-15 P2 actionable: push integrator
  η_init to z ~ 10⁹ via tight-coupling-enabled startup. The
  conditional inline DAE-relaxation in
  `htt/bass/hierarchy/integrator.py:434-498` is the permitted
  mechanism (TCA *pre-phase* remains banned per CLAUDE.md §6).

**Updated recommended ordering**: (a-switch) → (c) → (b) → D-2.

**Verification:** 287 Round-16 primitive baseline tests pass in
15.80 s pre-measurement; no production code modified;
`test_d2_pstf_closure.py` xfail marker preserved (still flags
+5.4374e+03 μK² gap at the linear-probe-equivalent canonical-default
switch — actual flip to `xpass` is gated on D-2 closure).

**Forbidden-moves catalogue (carried forward + new entries):**
- Carried: do not add a Doppler `/k` factor; do not mark
  `test_d2_pstf_closure.py` xpass without verifying numerical value
  against the Rust anchor; do not enter (a)/(b)/(c) sub-tracks
  without explicit user confirmation.
- New: do not absorb the 6.43× into a `calibration_factor` value
  baked into `compute_flrw_d_ell_linear_probe` defaults
  (R12-14 4-cycle consensus: per-(k, ℓ) variance falsifies any
  single multiplicative factor).
- New: do not declare PR-S13 (a) or G1 closed solely on the
  linear-probe path landing at 6.43× ratio. (a)-switch closes one
  piece; full G1 closure requires D-2.
- New: do not edit `_seed_formulae` to add higher-x correction terms
  (V5_ROUND12_TO_14 sub-option (D-2b) non-viable: ~20 orders required
  to converge at x=14).

---

## V5 Round-16 P2: Doppler `/k` mandate retracted; PR-S13 re-scoped (2026-04-26)

Doc-only retraction PR (no production code change). Triggered by an
empirical resolution session: the `/k` Doppler patch prescribed as
PR-S13's load-bearing fix in `V5_ROUND16_03 §1` + `V5_ROUND16_05`
gate row + `V5_ROUND16_NEXT_SESSION_HANDOFF.md §4.1/§6/§7-Q1` (commit
`607e759`) was empirically falsified.

**Empirical measurement (this session, 2 × 28 min `compute_flrw_d_ell`
runs at 65 k-points × 4 workers):**

| Configuration | D_2 (μK²) | Δ vs Rust MB-95 anchor |
|---|---:|---:|
| Anchor (Rust `bass_rs dump_dl_spectrum_sparse`) | 1002.086744 | — |
| Python PSTF, current `main` (no /k) | 2.0451 × 10¹⁰ | +2.0451 × 10¹⁰ |
| Python PSTF + `/k` Doppler patch (applied + reverted) | 2.0448 × 10¹⁰ | +2.0448 × 10¹⁰ |
| Effect of `/k` on D_2 | — | **−0.012% (vs spec-claimed 0.5%)** |

The /k patch shifts D_2 by 0.012%, not the spec-claimed 0.5%. The
actual gap is **7 orders of magnitude** and dominated by primordial-
amplitude normalization, not Doppler convention.

**Source of the false /k mandate:**
`docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md:22` — part of the
parallel-cycle audit explicitly retracted as Appendix X "false trail"
in the R7-authoritative `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md:9,
17, 405-407, 2218`. The R7 derivation is unambiguous: BASS's `v_b` slot
is the dimensionless `θ_b/k` (verified at
`htt/bass/hierarchy/seed_compatibility.py:210` and the baryon EOM in
`htt/bass/integration/ver2_native_integrator.py`); therefore
`(g v_b)'` is the canonical collapsed `j_ℓ`-only source and any `/k`
rewrite would double-divide. The in-tree regression-armor test
`htt/bass/los/test_flrw_bessel_projector.py::TestSharpVisibilityAnalyticOracles::test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`
(commit `a92640e`) enforces this.

**New ticket:**
- `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md` documents the corrected
  PR-S13 closure scope: three independent sub-tracks
  (a) primordial-amplitude alignment [leading hypothesis, 1-2d],
  (b) state-layout migration `m=0 → m∈{-2..+2}` [3-5d], and
  (c) real-IC injection at η(z_*) [1-2d]. Recommended ordering
  (a) → (c) → (b). Each requires explicit user confirmation before
  entry.

**Test fix (latent bug exposed by the empirical resolution):**
`htt/bass/spectrum/test_d2_pstf_closure.py:75` was
`L_max_tower=4, ell_max_transfer=8`, which fails
`FLRWPipelineConfig.__post_init__` validation at construction time —
so the xfail test never actually exercised the pipeline. Fixed to
`L_max_tower=8, ell_max_transfer=8` and `k_grid` length 64 → 65 (odd,
Simpson-compatible). The xfail marker remains; the test now fails
honestly at the pipeline assertion (Δ = +2.04 × 10¹⁰ μK²) rather than
at config validation.

**Verification:** baseline 287 Round-16 primitive tests pass in 15.3 s
post-edits; sharp-visibility regression-armor test passes; FLRW
pipeline test suite (25 tests) passes. No production code modified.
