# V5 Round-17 — External-Audit Verdict + Revised Closure Plan
_Authority: this doc + `docs/audits/external_round17_2026-04-27/{report1.md,report2.md}`. Created 2026-04-27 at the close of the external-audit cycle._

This document supersedes the sub-track ordering in `V5_ROUND17_PR_S13_REAL_SCOPE.md §4 revised` and `V5_ROUND17_NEXT_SESSION_OPENER.md §3 step 2`. Two external auditors (anonymous Korean-language Codex-class + Claude Opus 4.7) read the `external_round17_2026-04-27` bundle independently and converged on a substantially overlapping set of findings. The original `α → β → γ → δ` ordering is **refuted** by both; D-3 must precede δ.

---

## 1. Verdict synthesis

| Question | Report 1 (Codex-class) | Report 2 (Opus 4.7) | Combined |
|---|---|---|---|
| Q1 — D-2 diagnosis | PARTIALLY-CONFIRMED 4/5 | CONFIRMED 4.5/5 | **PARTIALLY/CONFIRMED — likely correct, needs the η_init sweep counter-test for 5/5** |
| Q2 — closure mechanism (η_init → z≈10⁹ + DAE) | PARTIALLY-CONFIRMED 3/5 | PARTIALLY 3.5/5 | **PARTIALLY-CONFIRMED — right direction, implementation risks unverified** |
| Q3 — ℓ=2 m=0 pin-only sufficient | PARTIALLY-CONFIRMED 3/5 | PARTIALLY 3.5/5 | **PARTIALLY — moment-ladder argument supports it; empirical trace required** |
| Q4 — other defects | PARTIALLY 3/5 | PARTIALLY 3/5 | **PARTIALLY — bias-floor revisit + polarization-basis injection test recommended** |
| Q5 — sub-track ordering α→β→γ→δ | "should be changed" 4/5 | **REFUTED** 4/5 | **REFUTED — D-3 must precede δ** |

The ordering refutation is decisive: Report 2 quotes our own brief
back at us — `02_AUDIT_FOCUSED_SUMMARY.md:159-162`: *"D-3 closure
could leak into δ's measurement budget if it's conflated with the
seed-validity residual"*. With D-3 sub-week and δ multi-month, parking
D-3 behind δ guarantees that any δ measurement will be contaminated by
unknown D-3 magnitude. The 4√2 fortuitous-averaging false-positive
(R13 Codex hypothesis, refuted in R14 finding F1) is the cautionary
prior: integrated metrics can hide per-(k, ℓ) defects that show up
later as residuals nobody can attribute.

---

## 2. New audit finding: production FLRW path uses LSODA, not IMEX ARK4

Both auditors flagged the bundle's `integrator.py` as routing the
DAE-relaxation through a `solve_ivp(method="LSODA")` call rather than
an IMEX implicit stage. Direct repo inspection (this session,
2026-04-27) confirms:

- `bass/runtime/ver2_execution.py:1802, 1816` — `execute_tier_b_solver` instantiates `LowellBianchiIntegrator`.
- `bass/hierarchy/integrator.py:5` (docstring) — explicitly says "into one `scipy.integrate.solve_ivp`".
- `bass/hierarchy/integrator.py:134` — `IntegratorConfig.solver_method: str = "LSODA"`.
- `bass/hierarchy/integrator.py:649` — `sol = solve_ivp(_rhs, (η_init, η_final), y0, t_eval=eta_out, method=self.config.solver_method, …)`.
- `bass/integration/imex_ark4.py` (Round-16 PR-S2 primitive) is imported **only by its own unit test** and the package `__init__.py`. It is **not wired into the production FLRW path**.

Implication. The `combined_rhs` callable assembled at `integrator.py:340`
(which contains the conditional inline DAE-relaxation block at lines
434–498) is dispatched as a single `_rhs(eta, y)` to LSODA. There is
**no explicit/implicit splitting** at all — the relax-rate term
`−a·Γ_T·(Π_2 − Π_2_alg)` enters the unified RHS and LSODA must build
its own (finite-difference) Jacobian or use BDF mode to handle the
stiffness.

This is consequential for δ. Report 2 §3.2 R-1 ("HIGH severity"):

> *"At z = 10⁹: a ~ 10⁻⁹, Γ_T (in η-prime units) is roughly n_e · σ_T · a evaluated in η-prime, which at full ionization in the radiation era gives Γ_T ~ 10¹² / Mpc order-of-magnitude. So `a · Γ_T ~ 10³ / Mpc`. Compared to the explicit dynamics (k_max ~ 0.03 / Mpc), the stiffness ratio is ~10⁵. This is well within the stability domain of any A-stable implicit method (ARK4(3)6L[2]SA is L-stable on the implicit stage), if the relaxation is in the implicit branch."*

LSODA's BDF mode is L-stable and *can* handle this stiffness, but at a
cost: step size will be controlled by accuracy, not stability, and the
step count over 12 decades of η is potentially much larger than what
IMEX ARK4 with proper splitting would need. This may or may not be
practical; **direct measurement is required** before committing to the
multi-month δ scope.

Two productive responses:
- **(short term)** Empirical step-count audit on the existing LSODA path with `gamma_T_override` synthetic deep-TCA values. If LSODA handles `Γ_T/H ~ 10⁹` with a tractable step count (say ≤ 10⁶ across the full η range), δ can proceed on the LSODA path.
- **(medium term)** Wire `imex_ark4.py` into the FLRW path with proper RHS splitting (`f^I` = relax-rate + Thomson; `f^E` = streaming + metric). This is **net-new wiring work** not previously scoped; ~1–2 weeks of integration if the Round-16 primitive's API is stable.

---

## 3. Documentation drift caught by the audit

### 3.1 The "60% of points in x>1" arithmetic error

`docs/audits/external_round17_2026-04-27/01_DETAILED_ANALYSIS.md §16` claimed:

> *"Counting points that land in `x > 1` (invalid Lowell expansion): the half above `k = 4 × 10⁻³` is `(log 4×10⁻³ - log 10⁻¹·⁵) / (log 10⁻¹·⁵ - log 10⁻⁴) × 65 ≈ 39 / 65 ≈ 60%`."*

Report 1 §1 corrected this:

> *"실제 수치는 `x>1: 37%`, `x>0.3: 57%`로 고쳐야 한다."*

The arithmetic re-derivation:
- k_grid = `np.logspace(-4.0, -1.5, 65)`, `η_init = 261 Mpc`
- `x = k · η_init`, validity boundary `k_crit = 1/η_init ≈ 3.83 × 10⁻³ Mpc⁻¹`
- log₁₀(k_crit) ≈ -2.418; log₁₀ k-grid spans [-4, -1.5]
- Fraction in `x > 1`: (-1.5 - (-2.418)) / (-1.5 - (-4)) = 0.918/2.5 ≈ **36.7% (24/65 points)**, not "60%"
- Fraction in `x > 0.3`: boundary at k = 0.3/261 ≈ 1.15 × 10⁻³, log₁₀ ≈ -2.94; fraction = 1.44/2.5 ≈ **57.6% (37/65 points)**

Corrected statement: *"about 37% of the test grid points are in clear `x > 1` invalid regime; about 57% are in marginal `x > 0.3` asymptotic-danger regime"*.

This is small in itself but genuine; Round-12-14 audit culture treats
arithmetic claims as load-bearing. Fix landed this session in both
`01_DETAILED_ANALYSIS.md §16` and `02_AUDIT_FOCUSED_SUMMARY.md §1`.

### 3.2 `primordial_b_k_sq` documentation drift in `integrator.py`

Report 1 §4 risk #6 caught a direct contradiction across three
files documenting the same parameter:

| File | Linear or squared? | Citation |
|---|---|---|
| `htt/bass/perturbation/regular_adiabatic_ic.py:111-135` | **Linear** ("Do NOT pass `A_s × (k/k_pivot)^(n_s-1)` here") | corrected post-R12 |
| `htt/bass/spectrum/flrw_pipeline.py:143-158` | **Linear** (matches regular_adiabatic_ic.py) | corrected post-R12 |
| `htt/bass/hierarchy/integrator.py:145-155` | **Squared** ("primordial amplitude squared `\|B_K\|²`"; "a physical ζ-normalized run sets `A_s × (k/k_pivot)^(n_s-1)`") | **stale, pre-R12** |

The R12 4-cycle convention audit established that `b_k_sq` enters every leading-order seed perturbation linearly (despite the historical `_sq` suffix dating to the CAMB Notes χ₀=−1 geometric β²=1 convention in flat FLRW). The integrator.py docstring carries the pre-R12 framing and is wrong. Fix landed this session.

---

## 4. Revised closure plan (this is now authoritative)

```
Phase 0 — VERIFICATION (this session + immediate follow-on)
  ✓ V0a — IMEX routing reality check               (DONE — finding §2 above)
  ✓ V0b — "60% x>1" arithmetic correction          (DONE — §3.1 above)
  ✓ V0c — primordial_b_k_sq drift fix              (DONE — §3.2 above)
  ↓ V0d — η_init sweep counter-test                (script landed; ~3 h wall time to run)
  ↓ V0e — bias-floor probe re-run at b_k_sq=0      (script landed; ~1 h wall time to run)
  ↓ V0f — LSODA step-count audit at deep TCA       (script landed; ~1 h wall time to run)

Phase 1 — TIER-1 LANDABLE (1-2 weeks)
  α  — (a-switch) canonical default → linear-probe path        [1-2 d]
  β' — (real-IC) BackgroundMonitor.from_recombination(z_*)    [1-2 d]
  D-3 — sync→Newt source-extractor patch                       [sub-week]
        ★ INSERTED HERE per audit verdict, was parked behind δ

Phase 2 — TIER-2 STRUCTURAL (multi-month)
  δ  — (D-2 closure) η_init → z≈10⁹ via TCA-enabled startup    [multi-month]
        Pre-conditions:
          • V0d sweep shows monotone D_2 collapse vs η_init
          • V0e bias-floor stays small post-R10/R11 + post-R15-P0
          • V0f LSODA step-count tractable OR imex_ark4 wired
          • _approx_tau_c heuristic replaced (regular_adiabatic_ic.py:94)

  γ  — (state-layout m=0 → m∈{-2..+2})                        [3-5 d]
        ★ DEMOTED from in-line ordering to PARALLEL track
        Independent of FLRW closure; can ship anytime with γ-branch
```

Rationale (drawn from the two audit reports, condensed):

- **V0a–V0c are doc/discovery work that already landed**. The IMEX routing finding alone changes how we plan δ; it cannot be filed as "minor doc fix".
- **V0d–V0f are cheap (≤ 1 day total wall time) GO/NO-GO gates** that should run *before* committing to δ. Both auditors agree on this. The η_init sweep is the single highest-value test: monotone collapse predicts D-2 closure success; flat residual predicts D-2 is *not* the dominant defect and δ-as-planned is misallocated work.
- **D-3 is moved between Phase 1 and Phase 2**. Sub-week effort vs. multi-month δ; the conflation cost during δ measurement is high; the bundle's own brief flagged this concern. Both auditors REFUTED keeping D-3 behind δ.
- **γ is demoted from sequential to parallel**. γ enables off-axis Bianchi (a Phase 2/3 deliverable), not FLRW closure. Report 2 §6.3 explicit: "γ and δ should not be sequential in the strong sense". One-person bandwidth → δ first; >1 → γ in parallel branch.

---

## 5. Counter-test scripts landed this session

Three diagnostic scripts under `scripts/`. Each is self-contained,
runs against the production codebase, and emits a numerical verdict
that is interpretable without bundle context.

### 5.1 `scripts/v5_round17_eta_init_sweep.py` (Report 2 §2.3, Report 1 Test C)

Runs `compute_flrw_d_ell_linear_probe` at `η_init ∈ {261, 200, 150, 100, 70, 50}` Mpc on the same N_k=65 k-grid as `test_d2_pstf_closure.py`. Each η_init value requires injecting `eta_initial_mpc_override` through the integrator config; the wrapper threads this through `build_cosmological_integrator_config`. Plots `D_2 / 1002.087` vs `x_max = k_max · η_init`.

Predictions (D-2 hypothesis):
- D_2/D_anchor monotonically decreases as η_init shrinks
- Ratio approaches ~1 as `x_max ≲ 1` (around η_init ≈ 30 Mpc for k_max = 0.0316 Mpc⁻¹)
- Power-law slope of (residual vs η_init) on log-log axes

GO/NO-GO criterion: at η_init ≈ 50 Mpc, ratio ≤ 2 → D-2 confirmed; ratio still > 5 → D-2 not dominant, replan δ scope.

Wall time: ~3 h on 4 workers (6 sweeps × 31 min ≈ 186 min, sequential).

### 5.2 `scripts/v5_round17_bias_floor_reprobe.py` (Report 1 §3, Report 2 §5.5)

Runs `compute_transfer_function_at_k(k, b_k_sq=0.0)` directly at k ∈ {10⁻⁵, 10⁻⁴, 10⁻³, 10⁻², 10⁻¹·⁵} on the post-R15-P0 codebase. Tabulates `|Δ_bias|/|Δ_target|` per (k, ℓ). The R10/R11 fix added `B_K_sq` linear factors to `pi_nu` and `G_3`; the bundle has no post-R11 measurement of this ratio. If small → 6.43× is genuinely D-2; if elevated at very-low k → secondary defect lives there too.

Wall time: ~5–10 minutes (single-k probes are fast; 5 × bias-only runs).

### 5.3 `scripts/v5_round17_lsoda_step_audit.py` (audit follow-up, response to §2 of this doc)

Runs `LowellBianchiIntegrator.run` over a grid of `η_init ∈ {261, 100, 30, 10, 3, 1, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001}` Mpc with **deliberate `gamma_T_override`** that simulates the deep-TCA `Γ_T/H` ratio at each anchor. Records:
- `solver_info.nfev` (function evaluations)
- `solver_info.njev` (Jacobian evaluations)
- `solver_info.nlu` (LU decomposions, BDF-mode signal)
- wall time per run
- whether the run completed without `RuntimeError`

GO/NO-GO criterion: `nfev` scales sub-quadratically with `η_total / η_init` → LSODA path is tractable for δ. `nfev` blows up → wire `imex_ark4.py` first.

Wall time: ~1 h (most runs short; a few may stall and timeout at ~10 min each).

---

## 6. What this session did NOT do

- Did not run V0d, V0e, V0f. Scripts are landed but execution requires several hours of dedicated wall time. Recommend running `bias_floor_reprobe` first (10 min, lowest cost), then `lsoda_step_audit` (1 h), then `eta_init_sweep` (3 h) only if the first two pass.
- Did not enter α / β / γ / δ / D-3. All sub-tracks remain pending; user decision required per `V5_ROUND17_NEXT_SESSION_OPENER.md §3 step 2`.
- Did not wire `imex_ark4.py` into production. That is medium-term work to be scoped separately if V0f shows LSODA is impractical.
- Did not modify `_approx_tau_c`. That's a δ pre-condition, not a Phase-1 closure item.

---

## 7. Forbidden moves (carried + new)

Carried from `V5_ROUND17_PR_S13_REAL_SCOPE.md §2 + §7.5`:
- No Doppler `/k` factor (regression-armor test enforces).
- No `xpass` on `test_d2_pstf_closure.py` without numerical verify.
- No baked `calibration_factor` for the 6.43×.
- No higher-x corrections to `_seed_formulae`.
- No TCA pre-phase (conditional inline DAE-relaxation only).

New from this audit cycle:
- **No δ entry without V0d/V0e/V0f passing** — both auditors require these gates be run before multi-month commitment.
- **No claim of "IMEX implicit stage handles stiffness"** in production FLRW path documentation until `imex_ark4.py` is actually wired (current path is LSODA).

---

## 8. Audit-loop completion state

```
2026-04-25  Round-12-14 cycle    →  D-1/D-2/D-3 framework
2026-04-25  Round-15 P0          →  D-1 closed
2026-04-26  Round-16 (S1-S14)    →  Bianchi primitives landed
2026-04-26  Round-16 P2          →  Doppler /k retracted
2026-04-27  Round-17 P2          →  Linear-probe measurement; 6.43×
2026-04-27  Round-17 audit cycle →  THIS DOC; D-2 likely, ordering refuted
2026-04-27  V0a-c                →  Doc/discovery items landed
????        V0d-f                →  GO/NO-GO gates (run when wall time available)
????        Phase 1 (α,β',D-3)   →  ~2 weeks of focused work
????        Phase 2 (δ)          →  multi-month
```

---

## 9. Cross-references

- Audit reports: `docs/audits/external_round17_2026-04-27/{report1.md, report2.md}`
- Original PR-S13 scope: `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md` (§4 ordering now superseded by this doc §4)
- Next-session bootstrap: `docs/V5_ROUND17_NEXT_SESSION_OPENER.md` (§3 step 2 ordering also superseded)
- Three-defect framework: `docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md`
- Counter-test scripts: `scripts/v5_round17_{eta_init_sweep,bias_floor_reprobe,lsoda_step_audit}.py`
- Integrator routing finding: `htt/bass/hierarchy/integrator.py:5, 134, 649` (LSODA confirmed); `htt/bass/integration/imex_ark4.py` (Round-16 primitive, not wired)
- `primordial_b_k_sq` drift fix: `htt/bass/hierarchy/integrator.py:145-155` (this session)

---

**End of revised plan.** Subsequent sessions begin at §4 Phase 0
(V0d/V0e/V0f) before any Phase 1 sub-track entry.
