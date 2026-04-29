# V5-RUNTIME Round-12 → Round-14 Investigation Summary

**Period**: 2026-04-25 (single intensive session)
**HEAD at start**: `0536f0e` (R12 Phase C semantic cleanup)
**HEAD at end**: same — no production code changes; this commit is
investigation artefacts only.

## TL;DR

After Round-9's R9-D bug fix landed (Round-10/R11 ν seed-formula
amplitude factor + Phase C semantic cleanup), the residual
`D_2^probe / D_2^Route-B = 7.57e+02` factor remained unexplained. Three
audit cycles (Round-12 → 14, **10 external auditor verdicts total**)
plus three internal Phase A/B-fix diagnostic stages produced a
consistent finding chain that this residual is **not a single missing
convention factor**, but the composition of three independent
architectural defects in the BASS PSTF FLRW pipeline:

- **(D-1) IMEX/LoS grid conflation** — integrator output η-grid reused
  as LoS quadrature grid; not k-adapted to Bessel oscillation.
- **(D-2) Lowell seed validity range** — `_seed_formulae` is the
  leading-order `x = k·η_init ≪ 1` expansion applied at η_init ≈ 260
  Mpc; for `k > 4e-3` the seed is wrong by `O(x²)` to `O(x^N)`.
- **(D-3) Synchronous/Newtonian gauge mismatch** — Θ_0 read from the
  integrator tower (synchronous gauge) combined with Ψ from Einstein
  constraint reconstruction (Newtonian gauge); SW source assembly
  inherits the gauge inconsistency.

All four Round-14 auditors recommend **HYBRID** as the only realistic
near-term path (CAMB transfer for FLRW, BASS PSTF for Bianchi
correction).

**User decision (2026-04-25)**: Hybrid as architectural default is
**rejected** — production code must remain self-contained without
external CAMB runtime dependency. CAMB stays as audit/comparison
oracle only. BASS-native fix path will be pursued through D-1, D-2,
D-3 in subsequent rounds (timeline multi-month).

## Round-by-round investigation

### Round-12 (4 auditors, 2026-04-25)

Triggered by post-R11 question: "where does the 760× residual come
from?" BASS team's hypothesis catalog: C-a (B_K_sq=ζ² double-counting),
C-b (LoS Bessel), C-c (source extractor), C-d (polter), C-e (sparse
quadrature).

**Verdict**: 4/4 REFUTED claim C-a. The seed bugs (R10/R11) are
correctly fixed; bias floor empirically zero. C-c (source extractor
super-horizon Einstein-constraint cancellation) ruled in by majority.

(Audit reports for Round-12 were `report*.txt` in repo root; deleted
prior to this commit and not preserved here. Conclusions captured in
this summary doc.)

### Round-13 (3 auditors, 2026-04-25)

Triggered by user "이제는 zip 파일 필요없이 이 프로젝트에 직접적으로 접근할
수 있는 외부 코딩 에이전트를 위한 프롬프트를 영어로 작성해줘" — agents had
direct repo access plus the `v5_round12_audit_bundle.zip`.

**Verdict**: 3/3 REFUTED Option A (k_min clipping) as a numerical
patch. Two new hypotheses surfaced:

- **Codex**: `sqrt(32) = 4√2` PSTF normalization factor — exact
  algebraic match to the empirical residual's square root.
- **Opus**: η-output grid undersampling (visibility g(η) FWHM ≈ 19 Mpc
  sampled on Δη=220 Mpc grid → 19% retention).

Audit verdicts stored at:
- `docs/audits/external_round12_to_14_2026-04-25/round13_audit01_gpt55.md`
  (GPT-5.5 Thinking, PARTIALLY-CONFIRMED)
- `docs/audits/external_round12_to_14_2026-04-25/round13_audit02_codex.md`
  (Codex, PARTIALLY-CONFIRMED)
- `docs/audits/external_round12_to_14_2026-04-25/round13_audit03_opus.md`
  (Claude Opus, REFUTED — explicit on Option A masking)

### Phase A diagnostic (BASS team, post-R13)

5 diagnostics in `scripts/v5_round12_phase_a_diagnostics.py`:
- D5: seed amplitude trace at k ∈ {1e-4, 1e-3} → `projected_seed.amplitude
  ∝ k²` (1.39e+4 · k²); irrelevant under `unit_amp_norm=False`
- D1+D2: Φ/Ψ behavior at k ∈ {1e-4, 3e-4, 1e-3} — **had `idx_star = 0`
  bug** that sampled Ψ at η_init instead of η_*; later fixed
- D3: k_min sweep showed ratio drops 760 → 32 from k_min=1e-4 → 1e-3
- D4: every_n_steps toggle → bit-identical (IMEX projection drift NOT
  the cause)

Transcripts: `docs/audits/diagnostic_transcripts_round12_to_14_2026-04-25/phase_a_*.txt`

### Phase B-fix diagnostic (BASS team, post-Phase A)

3 diagnostics in `scripts/v5_round13_phase_b_diagnostics.py`:
- D1+D2 FIXED: Ψ via PCHIP callable at proper η_*; revealed Ψ trajectory
  k-dependent (e.g. k=1e-4 Ψ flips sign over evolution: -0.34 → +0.39 → +5.13)
- D6: n_output sweep {64, 256, 1024}
- D7: 4√2 calibration trial → **D_2 ratio = 1.005 at k_min=1e-3** (looked
  like CONFIRMED but later refuted as fortuitous integrated averaging)

Transcripts: `phase_b_fix_D1D2D6D7.txt`

### Round-14 (4 auditors, 2026-04-25)

Triggered by user "바로 번들 작성하고 프롬프트 출력해줘" after Phase B-fix
+ CAMB direct comparison + n_output sweep + component ablation found
no single root cause.

3 new internal diagnostics:
- `scripts/v5_round12_camb_comparison.py` — direct per-(k, ℓ) CAMB compare
- `scripts/v5_round12_camb_compare_n_output_sweep.py` — n_output ∈ {64,
  256, 1024} CAMB compare
- `scripts/v5_round12_component_ablation.py` — SW+polter / ISW / Doppler
  isolation

**Round-14 findings (sent to auditors as F1/F2/F3)**:
- F1: 4√2 hypothesis is fortuitous (per-(k, ℓ) std/|mean| 108-357%, no
  single multiplicative factor)
- F2: BASS doesn't converge in n_output (sign flips, factor-19 swings,
  scipy PCHIP overflow warnings)
- F3: SW+polter and ISW both individually wrong; Doppler negligible
  (< 0.5%)

**Verdict**: 4/4 HYBRID-RECOMMENDED. Auditor-level diagnoses converged
to D-1/D-2/D-3 (Claude Opus's verdict was the most precise single
analysis — see `round14_audit04_opus.md`).

Audit verdicts stored at:
- `round14_audit01_codex.md` (Codex GPT-5)
- `round14_audit02_opus.md` (Claude Opus 4.7 — single-instance)
- `round14_audit03_gpt55.md` (GPT-5.5 Thinking)
- `round14_audit04_opus.md` (Claude Opus 4.7 — most detailed; explicit
  D-1/D-2/D-3 enumeration + §10 decisive 1-hour test design)

## Three independent defects (consensus)

### D-1: IMEX / LoS grid conflation

`flrw_pipeline.py::_los_and_wrap` (line ~316) clips
`integration_result.eta` and passes it as the LoS quadrature grid:
```python
eta_for_los = np.clip(eta_grid, 0.0, eta_0_mpc)
```

This grid is `np.linspace(η_init=260, η_today=14147, n_output=64)` —
uniform-linear, Δη=220 Mpc.

**Problems**:
- Visibility g(η) FWHM ≈ 19 Mpc → only 1 grid point in recombination zone
- Bessel oscillation period at k = 5e-2: `2π / k = 126 Mpc` — only 0.6
  grid samples per oscillation
- CAMB decouples ODE-internal grid from LoS grid (`cmbmain.f90`
  `IV_q` per-k integration grid + pre-tabulated `j_ℓ(x)`)

**Empirical signature**: BASS doesn't converge in n_output (F2);
PCHIP overflow warnings at n_output ≥ 256 (Φ, Ψ near-flat plateaus
on dense grid).

**Fix scope**: 1-2 weeks. Decouple LoS η-grid from IMEX output;
build per-k LoS grid sized for `j_ℓ(k(η₀-η))` resolution. New module
`bass.los.los_grid_builder`. No changes to integrator or seed.

### D-2: Lowell seed validity range

`regular_adiabatic_ic.py::_seed_formulae` (line 142-185, post Phase
C) applies the leading-order Lowell §13.2 expansion:
```python
delta_gamma = (amplitude / 3.0) * x²       # x = k·η_init
theta_gamma = (amplitude / 27.0) * x³
pi_gamma    = -(32.0 / 45.0) * k * τ_c * theta_gamma
```

Valid for `x = k·η_init ≪ 1`. At η_init = 260 Mpc, the validity
boundary is **k ≈ 4e-3 Mpc⁻¹**. Beyond it the expansion is wrong by
`O(x²)`:

| k [Mpc⁻¹] | x = k·η_init | seed validity |
|---|---|---|
| 1e-4 | 0.026 | ✓ |
| 1e-3 | 0.26 | marginal |
| 4e-3 | 1.04 | boundary |
| 1e-2 | 2.6 | invalid |
| 5e-2 | 13 | catastrophically wrong (`O(x²) ≈ 170×`) |

The IMEX integrator faithfully evolves the wrongly-seeded state
forward, producing over-amplified Φ, Ψ, Θ_0 at recombination.
Round-9 §5 noted "perturbations are 2.18e+4× too large" but framed
as amplitude convention, not asymptotic-validity question.

**Empirical signature**: BASS over-amplifies at sub-horizon, cleanly
correlated with `x` exceeding 1.

**Fix scope**: multi-month. Three sub-options:
- (D-2a) Push η_init back to z ~ 10⁹ + tight-coupling approximation
- (D-2b) Extend `_seed_formulae` to higher x orders (not viable —
  would need ~20 orders to converge at x=14)
- (D-2c) Matching-asymptotic: analytic super-horizon → numerical
  sub-horizon at horizon crossing (CAMB strategy)

### D-3: Synchronous / Newtonian gauge mismatch

`tier_b_source_extraction.py:225`:
```python
theta0_g = t_tower[:, _slot(0, 0)]   # synchronous-gauge tower output
```

combined at line 448 of `flrw_bessel_projector.py::build_temperature_source`:
```python
sw_polter = g_arr * (theta0_arr + psi_arr + 0.25 * pi_arr)
```

where `psi_arr` is reconstructed via Einstein constraints (Newtonian
gauge). The Round-5 Q-16 audit comment "Θ_ℓ^VER2 = Θ_ℓ^MB directly
(no gauge-transformation coefficient)" is **correct for ℓ ≥ 1** (the
higher MB multipoles are gauge-invariant in the FRW limit) but
**wrong for ℓ = 0**, where the synchronous-to-Newtonian conversion
adds an `h_S'/6` term.

**Empirical signature** (Phase A FIXED transcript at k=1e-4):
```
η =   260 Mpc:  Ψ = -0.336   Θ_0 = +3.5e-5
η =  3787 Mpc:  Ψ = +0.393   Θ_0 = +0.759   ← Ψ sign flip in matter era
η =  7314 Mpc:  Ψ = +0.069   Θ_0 = +1.504
η = 10841 Mpc:  Ψ = +0.022   Θ_0 = +2.242   ← Θ_0 monotonic linear-in-η ramp
η = 14147 Mpc:  Ψ = +0.0074  Θ_0 = +2.929
```

Sign flip of Ψ in matter era is unphysical for adiabatic Newtonian
mode. Linear-in-η Θ_0 drift is canonical synchronous-gauge growing
mode (`δ_γ_S = δ_γ_N + h_S'/6`).

**Fix scope**: sub-week if integrator exposes `h_S'`; multi-week if
plumbing required. Single-line conversion `Θ_0_N = Θ_0_S + h_S'/6`
in source extractor.

## What was tried + why it failed

| Hypothesis | Tried in | Outcome |
|---|---|---|
| C-a: B_K_sq=ζ² double-counting | Round-12 audit + Phase A | REFUTED (4 auditors) |
| Option A: k_min clipping | Round-12 audit | REFUTED (3 auditors); removes physical SW peak |
| 4√2 PSTF normalization | Phase B-fix D7 + Round-13 audit | Fortuitous integrated averaging; per-(k, ℓ) std/|mean| 108-357% |
| n_output increase (Opus R-13) | Phase B-fix D6 + Round-14 D6 | BASS doesn't converge — sign flips at higher n_output |
| Doppler `np.gradient` undersampling | Round-13 audit + R14 ablation | Doppler < 0.5% across all (k, ℓ) — REFUTED |
| Single missing convention factor | All 4 cycles, multiple candidates | Per-(k, ℓ) data falsify any single multiplicative factor |
| IMEX projection drift | Phase A D4 | bit-identical with `every_n_steps=1` — REFUTED |

**Lesson**: Round-9 already showed the residual is N_k-dependent (5e+4
→ 1.5e+4 → 1.4e+4 across N_k 4 → 12 → 24) and probe-amplitude-
dependent (factor 2 across `b_k_sq` 1.0 vs 0.01) — patterns
incompatible with any single missing constant. Three further audit
rounds searching for one is enough; this avenue is exhausted.

## What this commit preserves

### Investigation scripts (5 files in `scripts/`)

- `v5_round12_phase_a_diagnostics.py` — Phase A 5-diagnostic (had
  `idx_star = 0` bug; documented in Round-13 audit)
- `v5_round13_phase_b_diagnostics.py` — Phase B-fix: D1+D2 fixed +
  4√2 trial + n_output sweep
- `v5_round12_camb_comparison.py` — Round-14 direct CAMB compare
- `v5_round12_camb_compare_n_output_sweep.py` — Round-14 n_output sweep
- `v5_round12_component_ablation.py` — Round-14 SW/ISW/Doppler isolation

CAMB used as audit/comparison oracle only; not introduced as
production runtime dependency.

### Diagnostic transcripts (9 files)

`docs/audits/diagnostic_transcripts_round12_to_14_2026-04-25/`:
- `post_R11_*.txt` (3 baseline transcripts: convention audit,
  bias floor probe, per-k SW diagnostic)
- `phase_a_D5_seed_amplitude_trace.txt`
- `phase_a_D1234_full_diagnostic.txt`
- `phase_b_fix_D1D2D6D7.txt`
- `round12_camb_comparison_n64.txt`
- `round12_camb_compare_n_output_sweep.txt`
- `round12_component_ablation.txt`

### External audit verdicts (7 files preserved)

`docs/audits/external_round12_to_14_2026-04-25/`:
- Round-13 (3): `round13_audit01_gpt55.md`, `round13_audit02_codex.md`,
  `round13_audit03_opus.md`
- Round-14 (4): `round14_audit01_codex.md`, `round14_audit02_opus.md`,
  `round14_audit03_gpt55.md`, `round14_audit04_opus.md`

Round-12 verdicts (`report*.txt`) were deleted prior to this commit
and are not preserved here. Their conclusions are summarized inline
above.

## Round-15 plan (BASS-native, no external runtime dep)

User constraint: production code self-contained, CAMB allowed as
audit oracle only. Recommended next steps:

### Step 1 — §10 decisive 1-hour test (per Claude Opus R14 audit)

Run `scripts/v5_round15_decisive_los_test.py` (TODO):

```
Step 1.1: Extract CAMB Newtonian-gauge sources S_T_CAMB(η, k) at
          Planck-2018 cosmology on the BASS integrator η-grid.
Step 1.2: Project S_T_CAMB against j_ℓ(k(η₀-η)) using BASS's
          existing project_temperature_transfer routine.
Step 1.3: Compare result against (a) CAMB direct Δ_T_CAMB and
          (b) existing BASS α_BASS at the same k-grid.

Cases:
  A: agreement ≤ 5%   → projector is fine; defect 100% in source extractor
  B: 10-100× larger    → D-1 (LoS undersampling) dominant
  C: low-k OK, high-k diverges → D-1 dominant at high k
  D: any sign flip    → D-1 severity confirmed
```

This test uses CAMB **only as an oracle** — no CAMB import in
production code. Expected outcome (per Opus R14): Case A or C, which
isolates the defect to `tier_b_source_extraction.py` (D-2 + D-3).

### Step 2 — fix priority based on Step 1 outcome

If Step 1 shows the LoS projector is healthy:
- **D-3 first** (sub-week): expose synchronous-gauge `h_S'` from
  integrator state; convert `Θ_0_S → Θ_0_N` in source extractor.
- **D-2 second** (multi-month): tight-coupling-enabled early η_init
  OR matching-asymptotic seed handoff at horizon crossing.

If Step 1 shows D-1 contributes:
- **D-1 first** (1-2 weeks): decouple LoS η-grid from IMEX output;
  per-k LoS grid sized for `j_ℓ(k(η₀-η))` resolution.
- Then D-3, then D-2.

### Anchor invariants (preserved)

- Route-B Rust `D_2 = 1002.086744 μK²` — independent code path
- Route-B Python golden MM-curve — analytic, no PSTF
- 43 CAMB cross-check tests at `b_k_sq=1.0` — seed values, unaffected
- Fast baseline: 1723 passed (R10 → R11 → Phase C unchanged)

### Hybrid path explicitly rejected

The 4/4 Round-14 audit recommendation of using CAMB transfer functions
in production for the FLRW limit is rejected per user direction
(2026-04-25): "외부 모듈 의존성은 없으면 좋겠어. camb를 비교대상으로
쓰는견 좋은데 나는 이 코드 자체에서 올바른 데이터를 생성하게 하고싶어."
(BASS code itself must generate the correct data; CAMB is only a
comparison target.)

This decision adds calendar-quarter-scale work (D-2 fix is multi-month)
but preserves architectural independence.
