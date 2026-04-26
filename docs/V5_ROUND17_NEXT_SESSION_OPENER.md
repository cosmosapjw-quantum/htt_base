# V5 Round-17 — Next-Session Opener (post-P2 measurement)
_Authority: this doc + `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md` (§4 revised + §7 R17 P2 measurement). Created 2026-04-27 at the close of the P2 measurement session._

A new session can drop in cold and continue Round-17 from this file
alone. **Read this top-to-bottom, then start at §3 (entry procedure).**

---

## 1. State of play (as of 2026-04-27)

**Latest commit on `main`** (will update after the closing commit
of the P2 measurement session — check `git log -1` at session start).

**287 Round-16 primitive tests pass in 15.80 s.** No production code
has been modified since the Round-16 P2 retraction commit
`224a177`. PR-S13 (G1) remains open.

**Round-17 P2 measurement landed (doc-only)**: `D_2 = 6.4395 × 10³
μK²` from `compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)` at
N_k=65, residual ratio **6.43** vs the Rust MB-95 anchor
`1002.086744 μK²`. This empirically confirms the V5_ROUND17 §3 (a)
"primordial-amplitude alignment" hypothesis as the dominant gap and
triangulates the residual to V5_ROUND12_TO_14 D-2 (Lowell §13.2 seed
validity range at sub-horizon k > 4e-3 Mpc⁻¹).

## 2. The one-screen recap

- **Canonical `compute_flrw_d_ell` produces D_2 ≈ 2.04 × 10¹⁰ μK²**
  — gap +2.04 × 10¹⁰ vs anchor (7 orders of magnitude over).
- **`compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)` produces
  D_2 ≈ 6.44 × 10³ μK²** — gap +5.44 × 10³ vs anchor (6.43× over).
- The 6.4-orders-of-magnitude jump between the two paths is
  attributable to disabling the spurious `max(|Σ_±|, 1e-6) = 1e-6`
  floor that `unit_amplitude_normalization=True` applies in FLRW
  (Σ_± = 0).
- The remaining 6.43× residual is **D-2** (Lowell §13.2 seed
  validity at sub-horizon k); 10-auditor 4-cycle R12-14 consensus
  forbids absorbing it into any single multiplicative calibration
  factor.

**Sub-track ordering (revised 2026-04-27)**: (a-switch) → (c) →
(b) → D-2.

| Sub-track | Closes 6.43× residual? | Effort | Closes `test_d2_pstf_closure.py` xpass? |
|---|:---:|:---:|:---:|
| (a-switch) — switch `compute_flrw_d_ell` default to linear-probe path | ❌ | 1-2d | ❌ |
| (c) — real-IC injection at η(z_*) | ❌ | 1-2d | ❌ |
| (b) — state-layout migration `m=0 → m∈{-2..+2}` | ❌ | 3-5d | ❌ |
| **D-2** — push integrator η_init to z ~ 10⁹ via TCA-enabled startup | ✅ | multi-month | ✅ |

## 3. Start here (entry procedure)

```bash
# 0. Verify clean baseline.
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
git log --oneline -1   # should show the Round-17 P2 doc commit (or later)
git status             # should be clean

cd htt
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -m pytest \
  bass/background/test_codazzi_tilt_rhs.py \
  bass/integration/test_imex_ark4.py \
  bass/hierarchy/test_mode_mixing_blocks.py \
  bass/hierarchy/test_seed_factory.py \
  bass/hierarchy/test_family_k_grid.py \
  bass/los/test_b_mode_projector.py \
  bass/los/family_propagators/ \
  bass/forward/test_map_producer.py \
  bass/inference/test_planck_likelihood.py \
  -q --tb=line
# Expected: 287 passed in ~16 s.

# 1. Read the corrected scope and prior measurement record.
#    docs/V5_ROUND17_PR_S13_REAL_SCOPE.md         ← real PR-S13 scope
#                                                   (§4 revised + §7 R17 P2)
#    docs/V5_ROUND17_NEXT_SESSION_OPENER.md       ← this doc
#    docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md
#                                                 ← D-2 background, 10-auditor
#                                                   consensus that no single
#                                                   factor closes the residual
#    docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md   ← R7-authoritative
#                                                   (do NOT apply Doppler /k)
#    docs/V5_ROUND9_FINDINGS.md                   ← linear-probe origins +
#                                                   bias-floor mechanism
#    CLAUDE.md §3 + §5                            ← phase status, anchors,
#                                                   approximation-free constraints

# 2. Decide next action (do not enter without explicit user confirmation):
#    α  (a-switch): switch compute_flrw_d_ell default to invoke the
#                   linear-probe path (or disable the 1e-6 floor in
#                   the canonical path directly). 1-2d. test_d2_pstf_closure
#                   xfail message updates but stays xfail.
#    β  (c): real-IC injection at η(z_*); BackgroundMonitor.from_recombination
#                   constructor. 1-2d. Closes monopole-frame contract.
#    γ  (b): state-layout migration m=0 → m∈{-2..+2}; wires Round-16
#                   primitives (mode_mixing_blocks, seed_factory,
#                   family_propagators) into hierarchy_rhs. 3-5d.
#                   Required for off-axis Bianchi families.
#    δ  D-2: push integrator η_init to z ~ 10⁹ via tight-coupling-enabled
#                   startup. Multi-month. Only path to xpass on
#                   test_d2_pstf_closure.py.

# 3. Forbidden moves (always — see §4 below).
```

## 4. Forbidden moves (regression catalogue, post-R17 P2)

Carried from Round-16 P2 + new entries from R17 P2:

- **Doppler `/k`**: Do NOT add a Doppler `/k` factor anywhere in the
  source assembly (re-introduces the parallel-cycle false trail
  retracted in Round-16 P2; banned by the in-tree regression-armor
  test
  `htt/bass/los/test_flrw_bessel_projector.py::TestSharpVisibilityAnalyticOracles::test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`).
- **Premature xpass flip**: Do NOT mark `test_d2_pstf_closure.py`
  xpass without verifying the actual numerical value against the
  Rust anchor. (a-switch landing at 6.43× is **not** xpass-eligible;
  only D-2 closure to within 1e-9 fractional is.)
- **Sub-track entry without confirmation**: Do NOT enter
  (a-switch)/(b)/(c)/D-2 sub-tracks without explicit user
  confirmation. Each is a multi-day or multi-month commitment.
- **`calibration_factor` baking**: Do NOT absorb the 6.43× residual
  into a `calibration_factor` value baked into
  `compute_flrw_d_ell_linear_probe` defaults. The R12-14 4-cycle
  consensus explicitly forbids this — per-(k, ℓ) std/|mean| 108-357%
  across all candidate factors falsifies any single multiplicative
  constant.
- **(a) closure overclaim**: Do NOT declare PR-S13 (a) or G1 closed
  solely on the linear-probe path landing at 6.43× ratio.
  (a)-switch closes one piece; full G1 closure requires D-2.
- **`_seed_formulae` higher-x corrections**: Do NOT edit
  `_seed_formulae` to add higher-x correction terms.
  V5_ROUND12_TO_14 sub-option (D-2b) is non-viable: ~20 orders of
  expansion required to converge at x = 14.
- **TCA pre-phase**: Do NOT introduce a TCA *pre-phase* (i.e. an
  unconditional analytic solution replacing the photon hierarchy in
  an initial η-window). The conditional inline DAE-relaxation in
  `htt/bass/hierarchy/integrator.py:434-498` is the **permitted**
  mechanism for D-2 (CLAUDE.md §6 clarification 2026-04-26).

## 5. Critical context for D-2 (when ready)

CLAUDE.md §3 Round-15 P2 actionable: "push integrator η_init to z ~ 10⁹
via tight-coupling. §10 `k_adapted_η100` column already shows the
dominant low-k cells return to Case A once the truncation is lifted;
would also close the monopole-contract sub-percent question via
primordial-amplitude alignment."

The two pieces:

1. **Background extension to z = 10⁹**: requires the IMEX integrator
   to start at η_init corresponding to z ~ 10⁹ instead of the current
   z ≈ 1100 (η_init ≈ 261 Mpc). At z = 10⁹ the photon-baryon TCA
   regime is robust and the Lowell §13.2 leading-order expansion is
   valid for all Planck-relevant k (`x = k·η_init` ≪ 1). The full
   range η ∈ [η(z=10⁹), η_today] is ~5 orders of magnitude, so the
   IMEX integrator must remain stable across this range — Blocker 2
   (IMEX cosmological-range stability) is **CLOSED** per Round-15
   audit (`docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`). λ_max(A_right) ≈
   1e-16 at γ_T ∈ {0, 1}; cosmological η=261→14147 Mpc IMEX completes
   in 130 s.

2. **TCA-enabled startup**: in the radiation era the photon-baryon
   coupling is so tight that the photon quadrupole is algebraically
   slaved to the slip moments. The conditional inline DAE-relaxation
   dispatch in `htt/bass/hierarchy/integrator.py:434-498` already
   pins ℓ=2 m=0 to its algebraic limit when `Γ_T/H >
   closure.gamma_threshold_over_H` — the same mechanism would carry
   the seed forward through the radiation era. Switch-smoothness is
   audited by `htt/bass/hierarchy/test_tca_switch_smoothness.py`. The
   TCA *pre-phase* (unconditional analytic replacement of the
   hierarchy) remains banned per CLAUDE.md §6.

D-2 closure verification: re-run
`scripts/v5_round17_linear_probe_measurement.py` post-D-2; expected
result is D_2 → 1002.087 μK² to within numerical precision, at which
point `test_d2_pstf_closure.py` flips to `xpass` and the xfail marker
is removed.

## 6. Open questions for the human

These must be raised explicitly before progress on the hard parts:

- **Q1 (immediate)**: Pick α / β / γ / δ from §3 step 2. Recommended
  starting move is α (a-switch, 1-2d) — it's the smallest unit of
  visible PSTF-side progress and updates `test_d2_pstf_closure.py`'s
  xfail message to point at D-2 (better signal in CI than the
  current "PR-024c open" placeholder). β (c) and γ (b) are larger
  independent improvements; δ (D-2) is the path to bit-identity but
  multi-month.
- **Q2 (medium term)**: Once α lands, decide whether to keep
  `unit_amplitude_normalization=True` as the legacy code path
  (gated on a runtime flag with deprecation warning) or remove
  it entirely. Affects ~7 callsites.
- **Q3 (long term)**: D-2 closure may shift the Rust MB-95 anchor's
  bit-identity claim if the Rust path also has the Lowell-validity
  issue at sub-horizon k. Need to coordinate via SSOT drift audit
  (similar to `SSOT_TCMB_DRIFT_2026-04-19`) when D-2 lands.

## 7. References

| Topic | Doc |
|---|---|
| Real PR-S13 scope (this round) | `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md` |
| R7-authoritative PSTF derivation | `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` |
| D-2 / D-1 / D-3 background | `docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` |
| Linear-probe origins + bias-floor mechanism | `docs/V5_ROUND9_FINDINGS.md` |
| Round-15 P0 D-1 fix summary | `docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md` |
| Runtime-track diagnosis (Blockers 1-3) | `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md` |
| State-layout migration spec | `docs/V5_ROUND16_02_SOLVER_LAYER.md §1` |
| Round-16 master plan | `docs/V5_ROUND16_00_MASTER_PLAN.md` |
| Approximation-free constraints | `docs/ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md`, CLAUDE.md §6 |
| Reproduction script | `scripts/v5_round17_linear_probe_measurement.py` |

## 8. Suggested fresh-session opening prompt

Paste the following into a new session as the opening user prompt.
It is self-contained (does not depend on memory or prior session
state); the new agent will read the referenced docs, verify the
baseline, and stop at the user-decision gate.

---

```text
docs/V5_ROUND17_NEXT_SESSION_OPENER.md를 처음부터 끝까지 정독하고
거기 §1-§7의 상태와 forbidden-moves catalogue를 모두 확인해줘.
docs/V5_ROUND17_PR_S13_REAL_SCOPE.md §4 revised + §7 R17 P2 measurement
section 그리고 docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md
"Three independent defects" + "What was tried + why it failed" 도
함께 읽어 D-2 triangulation 근거를 확인해줘.

배경 (지난 세션 2026-04-27 마무리):
- compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0) at N_k=65 produced
  D_2 = 6.4395e+03 μK² (residual ratio 6.43 vs anchor 1002.087 μK²),
  6.4 orders of magnitude closer than canonical compute_flrw_d_ell
  (2.04e+10 μK², Round-16 P2 baseline).
- 잔차 6.43× 는 V5_ROUND12_TO_14 D-2 (Lowell §13.2 seed validity
  range at sub-horizon k) 로 triangulated. 10-auditor 4-cycle 합의:
  단일 multiplicative factor 로는 닫히지 않음.
- Sub-track ordering revised: (a-switch) → (c) → (b) → D-2.
  D-2 만이 test_d2_pstf_closure.py xpass 와 PSTF bit-identity 를
  닫음.
- 287 Round-16 primitive tests + sharp-visibility regression armor +
  25 FLRW pipeline tests pass. Production code 변경 없음.

이번 세션 우선순위:
1. 먼저 docs/V5_ROUND17_NEXT_SESSION_OPENER.md §3 step 0 의 baseline
   verification (287 Round-16 tests pass) 을 실행해줘.
2. 그 다음 §3 step 2 의 α/β/γ/δ 옵션 중 어느 것으로 진입할지
   사용자 결정 받기 전 §6 Q1 권장 (α a-switch, 1-2d) 의 근거를
   요약해서 제시해줘.
3. 사용자 명시적 confirmation 없이 어느 sub-track 도 본 구현 진입 금지.

§4 forbidden-moves 를 항상 준수해줘:
- Doppler /k factor 추가 금지 (parallel-cycle false trail).
- test_d2_pstf_closure.py xpass 표시 시 Rust anchor 와 실측 대조
  필수 (xfail mask 로 숫자 검증 우회 금지).
- 6.43× 잔차를 calibration_factor 로 흡수 금지 (R12-14 합의).
- _seed_formulae 에 higher-x correction 추가 금지 (D-2b 비현실).
- TCA *pre-phase* 도입 금지 (조건부 inline DAE-relaxation 만 허용).

마지막 commit: <git log -1 first>. main branch.
```

---

**End of Round-17 next-session opener.** Begin at §3.
