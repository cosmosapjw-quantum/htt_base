I'll start by extracting and surveying the bundle, then read the key documents in the order the prompt specifies before forming a verdict.I've now read the audit-focused brief, the R12-14 investigation summary, the seed code, the integrator DAE block, the LoS grid builder, the closure-test config, the linear-probe script, the R15 P0 fix record, the Round-9 findings (where the bias-floor probe lives), the R17 PR-S13 scope, and the relevant sections of the detailed analysis. Producing the audit now.

---

# BASS Phase-1 Closure — External Audit, Round-17

**Auditor:** Claude Opus 4.7 (single instance). **Date:** 2026-04-27. **Bundle commit:** `02cb6c0`.
**Reading scope:** `02_AUDIT_FOCUSED_SUMMARY.md`, `03_AUDIT_PROMPT.md`, `01_DETAILED_ANALYSIS.md` §§5–18, §29, all 7 files in `code/`, all 8 files in `reference_docs/`. ~3,800 LoC in code/ + ~115 KB of reference docs read.

---

## 1. Verdicts (one line each)

| # | Question | Verdict | Confidence (1–5) |
|---|---|---|---|
| Q1 | D-2 (Lowell seed validity at sub-horizon `x = k·η_init`) is the diagnosis | **CONFIRMED** | **4.5 / 5** |
| Q2 | Proposed closure (η_init → z ≈ 10⁹ + DAE-relaxation) is the right mechanism | **PARTIALLY CONFIRMED** | **3.5 / 5** |
| Q3 | DAE-relaxation pinning ℓ = 2 m = 0 only is sufficient through deep TCA | **PARTIALLY CONFIRMED** | **3.5 / 5** |
| Q4 | No other architectural defects of comparable size are missed | **PARTIALLY CONFIRMED** | **3 / 5** |
| Q5 | Sub-track ordering α → β → γ → δ (with D-3 parked behind δ) | **REFUTED — D-3 should precede δ** | **4 / 5** |

---

## 2. Q1 — D-2 diagnosis: **CONFIRMED**

### 2.1 Reasoning

The diagnosis is two distinct claims, both load-bearing:

(i) *That the seed is the leading-order Taylor expansion in `x = k·η_init`*. This is mathematically inspectable from the code, not a hypothesis. At `code/regular_adiabatic_ic.py:142–186`, every entry of the returned dict is a finite polynomial of degree 2 or 3 in `x`, with one extra `ω·k²·η³` term that is also of bounded order. There is no resummation, no matching, no mode-by-mode adaptation. `delta_gamma = (amp/3)·x²` (line 165–168), `theta_gamma = (amp/27)·x³` (line 173), `pi_nu = -amp · (4/(3·denom)) · x²` (line 175) — these are the textbook Lewis–Challinor 2002 App. C / Lowell §13.2 leading-order forms, valid as a power series in `x`. They are wrong by the standard truncation-error argument once `x ≳ 1`. The code text settles this point.

(ii) *That this analytic shortcoming dominates the residual at η_init = 261 Mpc*. The strongest direct evidence in the bundle is `reference_docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md` Tables at lines 45–58, where the §10 decisive test (CAMB-perfect Newtonian-gauge sources fed through the BASS LoS projector) was re-run at η_init = 100 Mpc as a control. The per-cell ratios collapse precisely as the D-2 hypothesis predicts:

| Cell | LoS-fix only (η_init=261) | LoS-fix + η_init=100 | CAMB direct |
|---|---:|---:|---:|
| k=10⁻³, ℓ=2 | 1.28×10⁻³ (×0.03 vs CAMB) | 4.24×10⁻² (×0.93) | 4.54×10⁻² |
| k=10⁻², ℓ=2 | 6.36×10⁻³ (×0.83) | 7.99×10⁻³ (×1.04) | 7.65×10⁻³ |
| k=10⁻², ℓ=3 | 8.89×10⁻³ (×1.26) | 7.00×10⁻³ (×0.99) | 7.07×10⁻³ |

This is the right empirical fingerprint: pushing η_init back (without changing anything else) collapses the per-cell ratios toward CAMB. That is what the diagnosis predicts and is incompatible with most rivals (gauge mismatch would not depend on η_init this way; basis-convention errors would not depend on η_init at all).

(iii) *Falsification of single-factor rivals*. R14 finding F1 (per-(k, ℓ) std/|mean| = 108–357 % across all candidate factors, `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:115–117`) eliminates any constant-multiplier hypothesis and is consistent with a per-k-functional error like D-2.

### 2.2 What I'd flag as a limitation, not a refutation

The empirical D-2 fingerprint comes from one control point (η_init = 100 Mpc). That is a 2.6× extension, not the 2.6×10⁵× extension δ proposes. The slope of (residual vs η_init) is established by a single non-anchor data point. The CONFIRMED verdict is on the *direction* and *mechanism*, not on the *quantitative claim* "all of the 6.43× lives in D-2".

There is also a small, separate, mathematically-distinct seed defect that travels under the D-2 banner but is not the Lowell expansion proper: the heuristic `_approx_tau_c(eta_initial, a_initial) = 0.15 · η_init / √a_init` at `code/regular_adiabatic_ic.py:94–101`, which is honestly labelled in its own docstring as "*not* a recombination solve … chosen only to populate the small photon quadrupole / E_2 startup surface". This poisons `pi_gamma` and `E_2` at η_init independently of the x-expansion. At η_init = 261 Mpc its contribution is small (because `theta_gamma ~ x³` is small at x ~ 1), but at the deep anchor (η_init = 10⁻³ Mpc, z ≈ 10⁹) the *actual* `Γ_T` from the species table must replace this heuristic, otherwise δ ships with a different (smaller, but real) seed defect than D-2. Treat this as a pre-condition to δ, not an alternative diagnosis.

### 2.3 Counter-test (the one I'd run before committing to multi-month δ work)

**η_init sweep on the existing pipeline, no integrator changes.** Shrink η_init through the largest range that *doesn't* require radiation-era TCA. The species PCHIP tables already extend to `η ≈ 100 Mpc` per the §10 fix's `k_adapted_η100` column, but the integrator config (`code/flrw_pipeline.py:406–419` calls `build_cosmological_integrator_config(...)`) anchors η_init at `η(z_*) − 20 Mpc ≈ 261 Mpc`. The species tables in `SpeciesBackgroundRegistry.from_planck2018` cover earlier η than the integrator currently requests; the integrator simply doesn't reach back into them.

Concrete script delta — *new file* `scripts/v5_round17_d2_eta_init_sweep.py` (~80 LoC):

```python
# Sweep η_init ∈ {261, 200, 150, 100, 70, 50} Mpc (no TCA changes; just lower the
# integrator's start). Use compute_flrw_d_ell_linear_probe at the same N_k=65
# k_grid as the closure test. Plot D_2/D_2_anchor vs η_init.
for eta_init in (261.0, 200.0, 150.0, 100.0, 70.0, 50.0):
    pipeline_cfg = FLRWPipelineConfig(L_max_tower=8, ell_max_transfer=8)
    # NEW knob: pipeline_cfg.eta_init_mpc_override that threads through to
    # build_cosmological_integrator_config (one new keyword in
    # cosmological_config.py, ~5 LoC). Below 50 Mpc the existing IC builders
    # may need radiation-era seed; that's δ's territory, hence the cap.
    bundle = compute_flrw_d_ell_linear_probe(
        species, k_grid_mpc=k_grid, pipeline_config=pipeline_cfg,
        # ... eta_init_override=eta_init ...
    )
    print(eta_init, bundle["d_tt"][2] / 1002.086744)
```

**Predictions**:
- D-2 confirmed: monotone collapse of `D_2/D_anchor` from ≈ 6.43 (at η_init=261) toward ≈ 1 (at η_init=50–70 Mpc, where `x = k·η_init < 0.5` for all k_max ≤ 0.0316 Mpc⁻¹). The shape should be a power law because the truncation error in `_seed_formulae` is itself a power of `x = k·η_init`.
- D-2 refuted: residual sticks near 6.43 across the range, or moves the wrong way. That outcome would force the residual onto a different defect (D-3 or something missed in Q4 below).

This sweep is **at most a few hours of wall time** (six runs × 31 min = 3.1 h on the 4-worker machine, fewer if you parallelize the sweep). Compared to multi-month δ work, this is the cheapest possible go/no-go gate. If I were planning δ I would not enter it without first running this sweep.

A second, smaller counter-test that distinguishes D-2 from "low-k bias-floor still leaking after R10/R11": run `compute_transfer_function_at_k(k=1e-5, b_k_sq=0.0)` directly — i.e., redo the Round-9 §5d bias-floor probe (`reference_docs/V5_ROUND9_FINDINGS.md:271–308`) on the post-R15-P0 codebase. R9-D found `|Δ_bias|/|Δ_target| = 3.08` at k=10⁻⁴ before the fix; it was supposed to drop to ~ 0 after the `pi_nu`, `G_3` linear-amplitude correction. **The bundle does not contain a post-R11 measurement of this ratio.** If it has crept back up because of some other amplitude-independent term in the seed or the IMEX startup, part of the 6.43× could be a stale-bias contribution that survives bias-subtraction, *not* D-2. ~1 hour wall time, a 30-LoC script.

---

## 3. Q2 — Closure mechanism (extend η_init + DAE-relaxation): **PARTIALLY CONFIRMED**

The mechanism is the right *kind* of mechanism: it is exactly what CAMB does (early radiation-era IC at deep TCA, evolve forward through TCA to recombination). But three concerns weighing the verdict down from CONFIRMED to PARTIALLY CONFIRMED, in increasing order of severity:

### 3.1 IMEX 12-decade extrapolation (mild concern)

Blocker 2 (`reference_docs/V5_RUNTIME_TRACK_DIAGNOSIS.md:1–219`) is a clean closure: `λ_max(A_right) = +0.175 / Mpc → 4×10⁻¹⁶ / Mpc` after the eight algebraic patches. The operator is now *physically correct* (skew-adjoint streaming + negative-semidefinite Thomson, with Wigner-Eckart-correct cross-couplings derived from MB95 / KKS97). I cannot identify a physical reason this would break across 12 decades. A skew-adjoint streaming block has its eigenvalues on the imaginary axis at *every* η, not just η ∈ [261, 14147].

What I would still ask for, before declaring this risk-free:

- **Per-decade `λ_max(A_right)` snapshot.** Run `scripts/v5_operator_fast_check.py` (referenced at `V5_RUNTIME_TRACK_DIAGNOSIS.md:205–207`) at η ∈ {10⁻³, 10⁻², 10⁻¹, 1, 10, 100, 1000, 14000} Mpc with the actual species background (in particular the actual `Γ_T(η)` at radiation-era values ~10¹² /Mpc-equivalent), not the "γ_T=1" sentinel. If `λ_max` stays ≤ 10⁻¹² across the sweep, this concern is gone. The audit result so far is at γ_T = 1, which is reasonable for the recombination regime but not for `Γ_T/H ~ 10⁹`.
- **Conservation-law audit per decade.** Codazzi tilt (the audit's constitutive constraint), photon-baryon momentum balance (MB95 eq. 65 in TCA), and energy conservation. Each per-decade audit costs hours, not days.

### 3.2 Stiffness of the implicit step at `relax_rate = a · Γ_T` (real concern)

This is the concern I want most to flag. The DAE is implemented at `code/integrator.py:496–498`:

```python
relax_rate = a_val * float(Gamma_T)
rhs_T[slot] = -relax_rate * (current_Pi2 - theta_2_alg)
rhs_E[slot] = -relax_rate * (current_E2  - E_2_alg)
```

The relaxation puts a Jacobian eigenvalue at `−a·Γ_T` into the linearization. At z = 10⁹: a ~ 10⁻⁹, Γ_T (in η-prime units, i.e., d/dη conformal-time rate) is roughly `n_e · σ_T · a` evaluated in η-prime, which at full ionization in the radiation era gives `Γ_T ~ 10¹² / Mpc` order-of-magnitude. So `a · Γ_T ~ 10³ / Mpc`. Compared to the explicit dynamics (k_max ~ 0.03 / Mpc), the stiffness ratio is ~10⁵. This is well within the stability domain of any A-stable implicit method (ARK4(3)6L[2]SA is L-stable on the implicit stage), *if the relaxation is in the implicit branch*.

**The bundle does not show me where this term lands in the IMEX split.** ARK4(3)6L[2]SA is an additive RK that requires the user to label which terms are stiff (implicit) vs non-stiff (explicit). The block at lines 434–498 is wired into `combined_rhs` (line ~340 onward) which assembles `out` for the *whole* RHS. Whether the IMEX driver (which I cannot see in the bundle — `LowellBianchiIntegrator.run` referenced at `code/integrator.py:556`) splits this term into the implicit stage is a critical question.

If the relaxation is in the **explicit** branch, step size is bounded by `dt < 2 / |a·Γ_T|`. At z=10⁹ that's `dt < 2·10⁻³ Mpc`, and integrating from 10⁻³ to 14147 Mpc requires ~10⁷ steps. Computationally infeasible.

If it's in the **implicit** branch, no problem.

**Counter-test:** read the IMEX driver to confirm. If the `slot` overwrite at lines 497–498 routes through `combined_rhs` and `combined_rhs` is dispatched as a single explicit-stage callable, this is the failure mode. The fix is to register the relaxation as a linear stiff term (its Jacobian at the slot is exactly `−a·Γ_T·I`), with the algebraic value as the "constant" term to be solved against. ~50 LoC of refactoring.

### 3.3 Switch-smoothness across 6 decades of `Γ_T/H` (moderate concern)

The current threshold `gamma_T_over_H_threshold = 100` (default, `code/integrator.py:594`) governs the on/off transition. `htt/bass/hierarchy/test_tca_switch_smoothness.py` is referenced at `reference_docs/CLAUDE_md_excerpt.md:48` as enforcing the smoothness audit, but the test target is the *recombination* transition where `Γ_T/H` falls from ~10² to 10⁻¹ — i.e., the threshold transition is actually crossed in the recombination test. At z = 10⁹ the system *starts* deep above the threshold (`Γ_T/H ~ 10⁹`) and stays there for many decades before approaching threshold near recombination. The smoothness audit at the recombination transition does *not* verify that integration *inside* deep TCA is well-behaved across many decades.

What's at issue specifically: as the integrator descends from z=10⁹ to z~10⁵, `Γ_T/H` falls from ~10⁹ to ~10⁵ — still deep TCA, no threshold crossing. But the relax_rate `a·Γ_T` evolves smoothly (a grows, Γ_T falls more slowly than H), and the algebraic value `theta_2_alg` from `solve_tca_closure` also evolves smoothly. Nothing in this is *physically* problematic. The risk is purely numerical: that the implicit-stage conditioning of (I − dt · J) deteriorates as `dt · a · Γ_T` becomes very large and the algebraic solution dominates the time step. This is well-understood in the DAE-of-index-1 literature (which is what this is) and the cure is to formulate the slot equation as a *constraint* solved at each step rather than as a stiff-relaxation ODE — but that's an implementation detail of how the IMEX is set up, not a physics question.

### 3.4 What the verdict means

CONFIRMED that pushing η_init back is the correct *direction*. PARTIALLY because (i) implicit-branch routing of the relaxation needs verification, (ii) the conservation-law per-decade audit is genuine multi-month work that the bundle correctly identifies, and (iii) the `tau_c` heuristic in `_seed_formulae` must be replaced before the deep anchor or the seed will carry a *different* error than the one D-2 names.

---

## 4. Q3 — DAE-relaxation pinning only ℓ = 2 m = 0: **PARTIALLY CONFIRMED**

### 4.1 Reasoning

This is the right question and CAMB practice is the right benchmark. CAMB's deep-TCA handling (`equations.f90`) actually does more than just "evolve everything except ℓ=2"; it explicitly truncates the photon multipole hierarchy at ℓ=2 during deep TCA, with ℓ ≥ 3 set by analytic TCA-2 expansion (Lewis 2008). What BASS does — pin ℓ=2 algebraically, free-stream ℓ ≥ 3 — is *not* canonical CAMB practice; it's a different choice.

**Whether it's a defensible different choice depends on whether ℓ ≥ 3 stay near zero by themselves in deep TCA.** In the moment hierarchy, the source of `Π_ℓ` is `k · Π_{ℓ−1}`. The damping is `−Γ_T · Π_ℓ` for ℓ ≥ 2. So in steady state:

```
Π_ℓ ~ (k / Γ_T) · Π_{ℓ−1}    (radiation-era TCA scaling)
```

With `Γ_T ~ 10¹² / Mpc` and `k ≤ 0.03 / Mpc`, the ladder factor is `k/Γ_T ~ 3·10⁻¹⁴`. Each higher ℓ is suppressed by 14 orders of magnitude relative to its neighbor. So in deep TCA, ℓ ≥ 3 *should* stay essentially at machine precision; pinning them is unnecessary.

The Lowell seed sets `Π_ℓ ≥ 3 = 0` at η_init (only `theta_gamma`, `pi_gamma` are non-zero in the photon T tower; see `code/regular_adiabatic_ic.py:243–246`). So the initial condition is right and the deep-TCA dynamics keep them small.

**However** — what about the E-mode hierarchy? `code/integrator.py:498` pins `E_2`, but in deep TCA `E_3, E_4, …` get sourced through Thomson coupling to `T_2` in a slightly different way (KKS97 polarization tower, source involves `(T_2 − √6 E_2)`). The KKS97 source structure would also drive `E_ℓ ≥ 3 ~ 0` in deep TCA, but I'd want this confirmed empirically rather than asserted.

### 4.2 Counter-test for Q3

**Run a single-k integration from z=10⁹ to recombination at fixed `k = 10⁻²` (or whatever k is feasible inside the validation budget) with the existing DAE-relaxation, and trace `||Π_ℓ|| / ||Π_2_alg||` for ℓ ∈ {3, 4, 5, 6, 7, 8} at η-snapshots through the trajectory.** If all ratios stay below ~10⁻⁶ (well below truncation tolerance), the ℓ-only-2 pinning is sufficient. If any rises above ~10⁻³, BASS's deviation from CAMB practice is observable and would need additional pinning logic.

Concrete script delta: extend `scripts/v5_round15_decisive_los_test.py` (referenced at `V5_RUNTIME_TRACK_DIAGNOSIS.md:230–232`, not in bundle) to also dump `state.photon_T.tensors[ℓ].components[ℓ]` and `state.photon_E.E.tensors[ℓ].components[ℓ]` at every η-snapshot for ℓ ∈ {3..L_max_tower}. This requires the integrator to be willing to start at η < 261 Mpc, which is δ work; so this counter-test is naturally part of the early validation milestone of δ, not a precondition.

### 4.3 The relax-rate stiffness is treated above (§3.2)

It is the same point as Q3's third bullet from the audit prompt and I won't repeat it. The verdict for that sub-question: **not yet verifiable from the bundle alone — depends on the IMEX driver's split classification, which is not in `code/`**. If the relaxation is implicit, fine. If explicit, you need a smoother dispatch (e.g., compute `Π_2 = Π_2_alg` algebraically + project the dynamic state onto the constraint manifold each step) — this is the "DAE-index-reduction" route. Verification step is reading `LowellBianchiIntegrator.run` (~`code/integrator.py:556`+), which is not in the bundle.

---

## 5. Q4 — Other architectural defects: **PARTIALLY CONFIRMED**

The bundle's three-defect framing (D-1 closed; D-2 open / multi-month; D-3 open / sub-week) is principled and the auditor cycles converged on it. But it's worth listing what I checked and what I'd want stress-tested before treating "no other architectural defects" as settled.

### 5.1 Source-extractor sign convention at `tier_b_source_extraction.py:225`

This file is **not in the bundle**. The relevant snippet quoted at `reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:201–203` is:

```python
theta0_g = t_tower[:, _slot(0, 0)]   # synchronous-gauge tower output
```

combined at `flrw_bessel_projector.py:448`:

```python
sw_polter = g_arr * (theta0_arr + psi_arr + 0.25 * pi_arr)
```

This is D-3 (sync/Newt mismatch on Θ_0) + the SW source assembly. The sign convention itself I cannot audit without the file, but I note that the assembly form `Θ_0 + Ψ + Π/4` matches MB95 eq. 89 and is internally consistent for a *single* gauge — D-3 is precisely the cross-gauge mismatch claim, not a sign-convention bug per se. **Not a missed defect**, just a re-statement of D-3.

### 5.2 PSTF normalization at the LoS projector (`flrw_bessel_projector.py`)

Also not in the bundle. The 4√2 = √32 PSTF normalization candidate was explicitly tested in Round 13–14 (Codex hypothesis, refuted by F1 — `V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:240–241`). If a separate normalization defect existed it would show up the same way (single-multiplier signature) and would have failed F1. **Refuted by prior art.**

### 5.3 Polarization quadrupole basis convention

The audit prompt frames this as `Π_BASS = Θ_2 + E_0 + E_2` vs `polter = 2Θ_2/5 + 3E_2/5`. Per `reference_docs/CLAUDE_md_excerpt.md:41`, those are different objects in BASS: `Π_BASS` is the *Thomson collision primitive* (used inside the collision operator), `polter` is the *LoS source contribution* (used at the projector). E₀ is **unused in the production polter** by explicit policy. So the convention is documented and not internally contradicted.

The claim "not yet directly stress-tested at low-k" in the audit prompt's Q4 is honest. A clean stress test would be to inject `(Θ_2, E_2) = (1, 0)` and `(0, 1)` separately into the LoS source and confirm that the resulting `α(k, ℓ)` matches `2/5` and `3/5` (resp.) of an analytic single-mode reference. **Recommend:** add this as a pair of unit tests in `htt/bass/los/test_flrw_bessel_projector.py` — < 1 day work, would close the open question regardless of whether it's the residual or not.

### 5.4 Background-table interpolation (HYREC visibility)

The Rust path uses the same `SpeciesBackgroundRegistry` background table (`01_DETAILED_ANALYSIS.md:55`); only the *interpolation strategy* differs. The Rust path has its own table interpolation (presumably the standard HYREC tabulation + Akima/cubic spline); the Python path uses PCHIP via `scipy.interpolate.PchipInterpolator` with `extrapolate=False`. R14 finding F2 noted PCHIP overflow warnings at `n_output ≥ 256`; R15 P0's per-k LoS grid bypasses that by re-evaluating PCHIP on a denser grid that respects the visibility FWHM. The post-R15 LoS evaluations should be interpolation-stable.

I would be more concerned if the Rust path used pre-tabulated `j_ℓ(x)` while the Python path uses `scipy.special.spherical_jn` per call (it does, per `01_DETAILED_ANALYSIS.md:56`). Two independent routines for the same Bessel function will not be bit-identical. For Phase-1 bit-identity that's a real concern, but it should produce errors of order machine epsilon × O(integration weight), not 6.43×. **Not a candidate for the residual.**

### 5.5 Candidate the bundle doesn't flag explicitly: residual bias-floor at very-low k after R10/R11

Round-9 §5d (`reference_docs/V5_ROUND9_FINDINGS.md:271–308`) found `|Δ_bias|/|Δ_target| = 3.08` at k = 10⁻⁴ pre-fix. The R10/R11 fix added `B_K_sq` linear factors to `pi_nu` and `G_3`. **The bundle does not contain a post-R11 measurement of this ratio.** It is plausible — but unproven from the materials I have — that some *other* amplitude-independent term (in the IMEX startup, in `eta_cov`, or in the IC consistency surface) still leaks a small bias floor that survives bias-subtraction at very-low k. The R17 P2 measurement was at probe_b_k_sq = 1.0; if the residual bias is k-dependent and contaminates only k ≤ 10⁻³, it would distort the integrated D_2.

This is a single-script counter-test: reproduce R9-D §5d's `compute_transfer_function_at_k(k, b_k_sq=0.0)` probe at k ∈ {10⁻⁵, 10⁻⁴, 10⁻³, 10⁻², 10⁻¹·⁵} on the post-R15-P0 commit and tabulate `|Δ_bias|/|Δ_target|` per (k, ℓ). **One hour of wall time.** If the ratio stays small (≪ 1) across the grid, this concern is closed and the 6.43× is genuinely a forward-modeling residual (i.e. D-2 is even more unambiguously the cause). If it stays elevated at very-low k, that's a parallel, smaller defect that should be closed before declaring "D-2 is everything that's left".

### 5.6 The `tau_c` heuristic in the seed (already noted in §2.2)

Re-flag: at `code/regular_adiabatic_ic.py:94–101`, `tau_c = 0.15·η_init/√a_init` is a placeholder. Its contribution to the residual at η_init = 261 Mpc is small but not zero. At δ's deep anchor, it must be replaced by `1/Γ_T(η_init)` from the species table. **Not a missed defect at the current anchor; but a precondition for δ.**

---

## 6. Q5 — Sub-track ordering: **REFUTED — D-3 should precede δ**

### 6.1 Reasoning

The bundle's stated ordering is:

```
α (a-switch, 1–2 d)  →  β (real-IC, 1–2 d)  →  γ (m∈{−2..+2}, 3–5 d)  →  δ (D-2, multi-month)
```

with **D-3 (sub-week, sync/Newt gauge mismatch) parked indefinitely behind δ**. The bundle itself acknowledges the risk — `02_AUDIT_FOCUSED_SUMMARY.md:159–162`:

> *"D-3 closure could leak into δ's measurement budget if it's conflated with the seed-validity residual."*

I think this concern is decisive and the bundle isn't taking it seriously enough.

D-3 is *sub-week*. δ is *multi-month* with iterative re-validation cycles (each per-decade conservation audit, each `Γ_T/H` smoothness re-audit, each real-IC adjustment). During δ work, the team will repeatedly want to ask: "*Did the residual just collapse from 6.43 to (some smaller number) because of the η_init push, or is some of that shift unrelated D-3 behaviour?*" Without D-3 closed, that question has no clean answer; it has a "we'll have to back out the D-3 magnitude post-hoc" answer, which is exactly the analysis pathology that produced the 4√2 fortuitous-averaging false positive in R13–R14.

The bundle's argument for the current ordering is implicit at `02_AUDIT_FOCUSED_SUMMARY.md:108–111` — α, β, γ each have unit-of-progress value independent of the residual. That's true and not a counter-argument; α/β/γ should still ship in sub-week order. The question is where D-3 lands.

### 6.2 Recommended ordering

```
α (a-switch, 1–2 d)
   → η_init sweep counter-test (Q1.3 above, ~few hours, GO/NO-GO on δ)
   → β (real-IC, 1–2 d)
   → D-3 (sync/Newt, sub-week)
   → γ (m∈{−2..+2}, 3–5 d)
   → δ (D-2, multi-month) on a clean residual baseline
```

This adds at most one calendar week (sub-week D-3) before δ entry, and buys clean δ measurement budgets. The cost-benefit is overwhelming: one week of certainty vs. multi-month δ with conflated residuals.

### 6.3 Also: γ and δ should not be sequential in the strong sense

γ (state-layout migration `m=0 → m∈{−2..+2}`) is **independent of the FLRW residual**. The bundle says so explicitly (`02_AUDIT_FOCUSED_SUMMARY.md:110`). γ is on the critical path for off-axis Bianchi, not for FLRW closure. There is no reason γ has to be done before δ; γ and δ can run concurrently in different branches. If the team is one-person, do δ first (the bigger Phase-1 lever); if it has bandwidth for a parallel branch, push γ in parallel since it doesn't touch any δ-relevant code.

### 6.4 What I'd update on

If D-3 magnitude turns out to be very small (say, a 10–20 % effect after a quick spot-test on a single (k, ℓ) cell), the conflation concern is cosmetic and the original ordering is fine. A 1-hour spot test at k = 10⁻³, ℓ = 2 (the cell where the §10 decisive test is most diagnostic) computing the source-extractor output before and after a hypothetical `Θ_0_S → Θ_0_N + h_S′/6` patch would resolve this. The bundle has this on the to-do list (`reference_docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md:218–229`) but no measured number. Get the number first.

---

## 7. Risks specific to δ that should be planned around

In rough order of severity:

**R-1 (high). Stiff implicit routing of the DAE relaxation is unverified.** §3.2. If the IMEX driver does not register `−a·Γ_T` as a stiff-eigenvalue contribution, step size will be capped at `~10⁻³ Mpc` at z=10⁹ and integration is computationally infeasible. This is a 1-day check (read `LowellBianchiIntegrator.run` and follow how `combined_rhs` is dispatched into the ARK4(3)6L[2]SA stages). Do this *before* committing to δ's full scope.

**R-2 (high). Real-IC at z = 10⁹ requires a radiation-era IC builder for all species.** Currently `cosmological_config.py::build_cosmological_integrator_config` defaults to `η_initial = η(z_*) − 20 Mpc`. The Lowell seed itself is fine at z=10⁹ (its leading-order x-expansion is *more* accurate, not less, at smaller η_init), but `_approx_tau_c` (`code/regular_adiabatic_ic.py:94–101`) must be replaced by the actual `1/Γ_T(η_init)` from the species table, and baryon/CDM/neutrino synchronous fluid quantities must be populated correctly at z=10⁹. Plan ~2 weeks of work for this alone.

**R-3 (moderate). Per-decade conservation-law re-audit.** Codazzi-tilt RHS and momentum-balance constraints (per `reference_docs/CLAUDE_md_excerpt.md:48` PSTF lineage) need re-validation across η ∈ {10⁻³, 10⁻², 10⁻¹, …, 10⁴} Mpc. Not hard physics; just calendar time.

**R-4 (moderate). Switch-smoothness across `Γ_T/H ~ 10⁹ → 10⁻¹`.** Existing test (`htt/bass/hierarchy/test_tca_switch_smoothness.py`) covers the recombination transition; the deep-TCA-only regime (no threshold crossing) is structurally different and needs its own audit. Plan ~1 week.

**R-5 (moderate). Numerical conditioning across 12 decades of η.** With `rtol = 1e-6, atol = 1e-9` (`code/flrw_pipeline.py:125–126`), accumulated roundoff over 12 decades may be measurable at the 10⁻⁹ closure tolerance. Consider stepping in `ln η` rather than `η` for the radiation-era portion; this is a standard technique in cosmological Boltzmann solvers (Zhang & Yu 2017 numerical-relativity context, but the principle is generic).

**R-6 (low–moderate). Residual bias-floor at very-low k after R10/R11.** Counter-test in §5.5. If it has crept back, δ's measurement budget will be contaminated by something δ doesn't address.

**R-7 (low). Bessel-function evaluation reproducibility between Rust and Python.** Will surface as a small (10⁻⁶ – 10⁻⁸) per-(k, ℓ) variance once everything else is at the bit-identity scale. Not a δ blocker; a Phase-1 final-mile concern.

---

## 8. Confidence summary and what would update each verdict

**Q1 (D-2 diagnosis): 4.5 / 5.** The mathematical structure of the seed code is unambiguous; the η_init=100 control point in the §10 test is a direct empirical signature. I'd move to 5/5 if the η_init sweep counter-test (§2.3) shows monotone collapse of the residual with η_init, which I'm confident it will. I'd move to 3/5 if the post-R11 bias-floor probe (§5.5) shows a substantial residual amplitude-independent floor, which would indicate that part of the 6.43× lives in a different defect than D-2.

**Q2 (closure mechanism): 3.5 / 5.** Right direction; right CAMB-precedent; load-bearing DAE-relaxation is a sensible mechanism. Held back by the unverified implicit-routing question (§3.2), the conservation-audit calendar cost (§3.1), and the `_approx_tau_c` precondition (§2.2). Moves to 4.5/5 once the implicit-routing question is settled and the per-decade `λ_max` snapshots are in. Drops to 2/5 if the relaxation turns out to be in the explicit branch and a deeper refactor is needed.

**Q3 (DAE-relaxation pinning ℓ=2 m=0 only): 3.5 / 5.** The moment-ladder argument (§4.1) makes ℓ ≥ 3 dynamically irrelevant in deep TCA, and the seed sets them to zero. But this is theoretical, not demonstrated; the counter-test in §4.2 would settle it. Moves to 4.5/5 if higher-ℓ ratios stay below 10⁻⁶ in the empirical trace; drops to 2/5 if any ℓ ≥ 3 mode shows non-trivial amplitude in the deep-TCA region.

**Q4 (other defects): 3 / 5.** The three-defect framing is principled and the auditor cycles converged on it, but the bundle has at least two specific stones unturned (§5.3 polarization-basis injection test; §5.5 post-R11 bias-floor probe). Each is sub-day work and would fully close those open questions. Moves to 4/5 with both done; drops to 2/5 if either reveals a non-trivial residual contribution.

**Q5 (sub-track ordering): 4 / 5.** The bundle's own concern ("D-3 closure could leak into δ's measurement budget") is decisive when D-3 is sub-week and δ is multi-month. The only thing holding this back from 5/5 is uncertainty about D-3's magnitude — if it turns out to be very small, the conflation concern is cosmetic. A 1-hour spot test (§6.4) resolves it.

---

## 9. One-line summary

The D-2 diagnosis is right; the proposed closure is the right *kind* of closure but has implementation risks the bundle does not yet quantify (chiefly the IMEX implicit-stage routing of the DAE-relaxation); and the most cost-effective change to the plan is to insert sub-week D-3 closure and a few hours of η_init-sweep counter-testing **before** committing to multi-month δ.

---

*End of audit. File-line references resolve against the bundle layout at `external_round17_2026-04-27/`. If any cited file is needed at the level of full code (in particular `LowellBianchiIntegrator.run` and `flrw_bessel_projector.py`), recommend including them in the next bundle revision — the §3.2 implicit-routing question cannot be answered from the materials provided.*