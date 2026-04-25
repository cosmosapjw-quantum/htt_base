# V5-RUNTIME Round-14 External Audit Verdict

| Field | Value |
|---|---|
| Auditor | Claude Opus 4.7 (independent external audit) |
| Date | 2026-04-25 |
| Bundle SHA | `0536f0e` |
| Audit cycle | 4 of 4 (Round-12 → Round-13 → Phase B-fix → **Round-14**) |
| Scope | Verdict on incremental-fix vs architectural-rework for BASS PSTF FLRW pipeline D_2 accuracy |

---

## Verdict (one-line)

**HYBRID-RECOMMENDED** — with a strong secondary verdict that an incremental fix is *available in principle* but blocked by **three** independent architectural defects, only one of which is cheap to repair.

---

## Executive summary

The per-(k, ℓ) discrepancy between BASS and CAMB is not a single bug. It is the composition of three independent defects:

- **(D-1) IMEX/LoS grid conflation** — the IMEX integrator's `n_output` η-grid is reused as the LoS quadrature grid. The two grids have unrelated sampling requirements (ODE accuracy near recombination vs Bessel-oscillation resolution at sub-horizon k); CAMB decouples them, BASS does not.
- **(D-2) Lowell seed validity range** — `_seed_formulae` in `regular_adiabatic_ic.py` is the leading-order Lowell §13.2 expansion in `x = k·η_init`, applied at `η_init ≈ 260 Mpc` to all k. For `k ≳ 4·10⁻³` Mpc⁻¹, `x > 1` and the seed is wrong by `O(x²)` to `O(x⁴)` magnitude.
- **(D-3) Synchronous/Newtonian gauge mismatch** — the SW source assembly takes `Θ_0` from the integrator's tower output (synchronous gauge) and combines it with `Ψ` reconstructed from Einstein constraints (Newtonian gauge). The Phase A diagnostic transcript already shows the unphysical signature (Ψ sign flip + Θ_0 linear-in-η ramp); the bundle did not flag it.

Each defect dominates in a different region of the (k, ℓ) plane, which is why no single calibration factor reconciles BASS with CAMB — and why the four prior audit rounds spent searching for one (4√2, 16/3, 2√6, etc.) all failed. Defect (D-1) is patchable in 1–2 weeks; (D-2) and (D-3) are multi-month architectural work.

The only path to production-grade FLRW D_2 in calendar months rather than calendar quarters is the hybrid: **CAMB transfer functions for the FLRW limit, BASS PSTF only for the genuinely-Bianchi correction layer**. The Route-B Rust anchor (`D_2 = 1002.087 μK²`) remains the FLRW reference, and BASS reports `D_2_total = D_2_FLRW_CAMB + ΔD_2_Bianchi_PSTF` — clean separation of concerns with no compromise to the original Bianchi-anisotropy science contribution.

A 1-hour test that disentangles (D-1), (D-2), (D-3) without modifying any BASS code is given in §10.

---

## 1. F1 — verified, with refined interpretation

The 4√2 ≈ 5.66 calibration is fortuitous. The integrated `D_2 = 4π ∫ |α|² P_R d ln k` averages over k, and the BASS-vs-CAMB discrepancy is a wildly k-dependent function that happens to integrate (with the standard `P_R(k)` weighting on the audit's k-range) to a number close to 32. There is no per-(k, ℓ) cell anywhere in the diagnostic data where the ratio is 4√2; the integrated match is a numerical coincidence of three unrelated bugs combining over the `P_R(k) k⁻¹` weighted measure.

The bundle is correct that the 4√2 hypothesis is refuted. I add: searching for *any* k-independent normalization factor at this point is misdirected work. The per-(k, ℓ) data falsify the existence of one. Round-9 §2 already showed the residual is N_k-dependent (doubling N_k from 4 → 12 shifts the ratio by 0.6×) and probe-amplitude-dependent (1.0 vs 0.01 shifts by 2×) — patterns incompatible with a single missing constant. F1 closes the door on the convention-factor search; further audit cycles spent on this question would not converge.

## 2. F2 — verified, but the diagnostic interpretation is partially wrong

The non-convergence in `n_output` is real, but the bundle's framing (BASS "should converge" with enough `n_output` and doesn't) conflates two independent effects.

I verified by toy experiment — Gaussian source localized at recombination + extended ISW-like source, both projected against `j_ℓ(k(η₀-η))` via uniform-linear trapezoid:

- A **sharp** SW-like source converges from 9× over-prediction at N=64, to 2.4× at N=256, to 0.97–1.07 at N=1024, to ≤0.1 % error at N=8192. The dominant error at low N is recombination-width undersampling: at N=64, `Δη ≈ 220` Mpc puts only ~0.1 grid point inside the 19 Mpc visibility FWHM.
- An **extended** ISW-like source already converges to 1 % accuracy by N=256 across all k ∈ [10⁻³, 5·10⁻²].

So a *correctly-amplituded* smooth BASS source projected on uniform-linear trapezoid would converge by N ≈ 1024–4096 even at k = 5·10⁻² Mpc⁻¹. The actual BASS at N=1024 still gives ratios 6× to 100× CAMB. **This rules out "raise n_output further" as a fix** — even a converged trapezoid won't agree with CAMB because the input source is wrong, not just the quadrature.

The PCHIP `RuntimeWarning: overflow encountered in divide` at `_cubic.py:325` is a **symptom**, not a cause: it triggers when consecutive samples produce `mk = 0` (division by zero in the weighted-harmonic-mean of slopes). At N ≥ 256 the integrator's dense_output produces flat plateaus in Φ, Ψ, or Π — likely from rejected steps replayed at adjacent η values, or from regimes where the smooth potential simply doesn't change at machine precision over `Δη = 14` Mpc. Since the PCHIP wrapper is then never queried off-grid in the LoS path, the `inf` slopes never propagate to numerical output, but they do indicate the input data is not what `PchipInterpolator` was designed for.

## 3. F3 — verified, with sharpened root-cause attribution

The Doppler-negligible result is correct and rules out the GPT-5.5 / auditor #2 Doppler-undersampling hypothesis. The "SW + ISW both individually wrong" finding is correct, and the bundle's conclusion that the bug is in the *shared upstream pipeline* (Φ, Ψ, Π reconstruction or Θ_0 evolution) is correct.

I narrow this further: SW+polter at k = 5·10⁻², ℓ = 3 gives BASS = +0.467 vs CAMB(scalar full) = +2.5·10⁻⁴, i.e. 1869× over-prediction. The toy experiment in §2 shows that even maximally-bad uniform trapezoid undersampling cannot produce 1869× over-prediction from a smooth, correctly-amplituded source. **The SW+polter input itself (g · (Θ_0 + Ψ + Π/4)) must be over-amplified by a factor that scales steeply with k**, which is the (D-2) signature.

## 4. F4 — Phase A Ψ trajectory shows a third pathology not previously flagged

This finding was not in the bundle's enumeration. Re-reading `phase_a_D1234_full_diagnostic.txt` (which the team treated as a corroborator of "source extractor mostly fine"), the Ψ trajectory at k = 10⁻⁴ Mpc⁻¹, b_k_sq = 1.0 (deep super-horizon) is:

```
η =   260 Mpc:  Ψ = −0.336   Θ_0 = +3.5·10⁻⁵
η =  3787 Mpc:  Ψ = +0.393   Θ_0 = +0.759
η =  7314 Mpc:  Ψ = +0.069   Θ_0 = +1.504
η = 10841 Mpc:  Ψ = +0.022   Θ_0 = +2.242
η = 14147 Mpc:  Ψ = +0.0074  Θ_0 = +2.929
```

Two features are inconsistent with adiabatic ΛCDM Newtonian-gauge evolution:

**(a) Ψ flips sign from −0.336 to +0.393** between η = 260 (just before recombination) and η = 3787 Mpc (z ≈ 13). Newtonian-gauge Ψ for the adiabatic mode is monotonically negative in the matter era and decays in magnitude (does not change sign) into Λ-domination. A sign flip in the matter era is not a Λ-suppression artifact — Λ takes over only around z ≈ 0.4 (η ≈ 11 000 Mpc), well after the η = 3787 Mpc sample. The observed +0.39 at z ≈ 13 has the wrong sign.

**(b) Θ_0 grows monotonically and linearly in η**: 3.5·10⁻⁵ → 0.759 → 1.504 → 2.242 → 2.929. Linear-fit slope ≈ 2.13·10⁻⁴ Mpc⁻¹, residuals < 1.5 % across all four post-recombination points. Newtonian-gauge δ_γ in matter era is bounded and oscillatory (no growing mode); a clean linear-in-η ramp is not Newtonian behavior.

A linear-in-η drift in Θ_0 simultaneous with a Ψ sign flip in the matter era is the canonical signature of **synchronous-gauge growing modes appearing in a quantity that downstream code is interpreting as Newtonian**. In synchronous gauge, `δ_γ_S = δ_γ_N + (h_S' / 6) + ⋯` (Ma & Bertschinger 1995, eq. 27a + the gauge transformations around eq. 19); `h_S'` retains a residual gauge mode that grows like η during matter era for matter-tracking time slicing. Applied to `_seed_formulae` (which uses matter-tracking via the `Z` slot, line 177–180, and the `eta_cov` field, line 162), δ_γ_S then carries the linear h-driven growth observed.

This is a third independent defect:

> **(D-3) Gauge mismatch in the SW source assembly.** `tier_b_source_extraction.py` line 225 takes `theta0_g = t_tower[:, _slot(0, 0)]` directly from the integrator's tower (synchronous gauge) and combines it with `psi_arr` reconstructed in Newtonian gauge via Einstein constraints (lines 275–302). The Round-5 Q-16 auditor instruction "Θ_ℓ^VER2 = Θ_ℓ^MB directly (no gauge-transformation coefficient)" is correct for ℓ ≥ 1 (the higher MB multipoles are gauge-invariant in the FRW limit), but **wrong for ℓ = 0**, where the synchronous-to-Newtonian conversion adds the h-driven gauge term that BASS is currently leaving in.

So the SW source is `g · (Θ_0_synchronous + Ψ_Newtonian + Π/4)` instead of `g · (Θ_0_Newtonian + Ψ_Newtonian + Π/4)`. The extra h-term is small at η = η_rec (where the integrator has just started — h has not yet drifted), but the *time derivative* `(Φ̇ + Ψ̇)` driving the ISW source is contaminated by the h-evolution because the Newtonian Ψ inferred from synchronous-tower Einstein constraints inherits the h-drift, hence the sign flip.

---

## 5. How D-1, D-2, D-3 compose to give the observed pattern

Each defect dominates in a different (k, ℓ) regime, which is why no single calibration factor works:

| Regime | Dominant defect | Why |
|---|---|---|
| Deep super-horizon (k ≪ 1/η_rec ≈ 4·10⁻³), low ℓ | **D-3 (gauge)** + LoS undersampling | Lowell seed valid here; LoS Bessel period long; the residual is the ISW spurious-Ψ̇ driver from synchronous-gauge contamination integrated over the whole post-recomb history. |
| Transition (k ≈ 10⁻³ to 10⁻²) | mix of D-1, D-2, D-3 | All three contribute comparably. |
| Sub-horizon (k ≳ 10⁻²), low ℓ | **D-2 (seed)** | Seed amplitude over-injected by `O(x²)` at η_init = 260 Mpc; integrator faithfully evolves the wrong initial condition forward. |
| Sub-horizon, high ℓ | **D-1 (LoS undersampling)** + D-2 | Bessel oscillations not resolved by 64-point uniform-linear trapezoid; sign flips in n_output sweep are the trapezoid noise signature. |

The k_min sweep result in `phase_a_D1234_full_diagnostic.txt` D3 (D_2/Route-B = 3956 at k_min = 10⁻⁵, dropping to 32 at k_min = 10⁻³) is consistent with D-3 dominating at low k: cutting off k < 10⁻³ removes the modes most contaminated by the spurious ISW driver, and D_2 drops by ~100×.

---

## 6. Q1 — Is 4√2 a real per-(k, ℓ) factor or fortuitous?

**Fortuitous.**

- *Q1.1*: There is no quantity which, when isolated, would show a uniform 4√2 ratio. The seed ratio `B_K_sq / ζ` at b_k_sq = 1 vs Planck-2018 ζ ≈ 4.6·10⁻⁵ is ~2.18·10⁴, not 5.66. The CAMB Notes χ₀ = −1 normalization (referenced in the seed code) does not produce a 4√2 either.
- *Q1.2*: The integrated D_2 = 1.005 match is a coincidence of integrating a wildly-k-dependent ratio over the smooth `P_R(k) k⁻¹` measure across the audit's k-range. Change the k-grid (Round-9 §2 point 2: doubling N_k 4 → 12 shifts the ratio by 0.6×) and the "calibration factor" shifts by ~2×. This is not what a real convention factor looks like.

## 7. Q2 — Does BASS converge in n_output?

**Not for the right reason.** The IMEX-output η-grid is being conflated with the LoS quadrature η-grid. They have different sampling requirements: IMEX needs density where the photon-baryon hierarchy is stiff (recombination, tight-coupling boundary); LoS needs density where the source × Bessel integrand is non-negligible (recombination peak + late-time ISW), with k-adapted fineness for the Bessel oscillation.

CAMB decouples these explicitly — `cmbmain.f90` builds a separate `IV_q` integration grid per-k for the LoS, and pre-tabulates `j_ℓ(x)` on a much finer x-grid (Lewis & Challinor 2002, *Efficient computation of CMB anisotropies in closed FRW models*, PRD 66 023531, §5; CAMB source `BesselJl_setup` in `bessels.f90`). BASS does neither.

- *Q2.1*: The PCHIP overflow is a symptom of duplicated-y consecutive samples in Φ, Ψ, or Π. Likely cause is the IMEX adaptive stepper's dense-output emitting near-identical Φ values on consecutive output points where Φ is in a slowly-varying regime. Not a cause of the per-(k, ℓ) error.
- *Q2.2*: The IMEX adaptive stepper is correctly handling its own internal ODE accuracy. The output η-grid is `np.linspace(η_init, η_today, n_output)` (verified in `flrw_pipeline.py` config), evaluated via the integrator's dense_output spline. This is fine for ODE state, but is the wrong grid for LoS integration — the n_output convergence test is testing the wrong thing.
- *Q2.3*: The right policy is the CAMB policy — k-adapted η-stepping for the LoS, with density set by `Δη ≤ π/(N_per_period · k)` for some `N_per_period ~ 8–16`, plus a recombination-zone refinement with `Δη ≤ recomb_FWHM/N_per_FWHM` for some `N_per_FWHM ~ 8`.

## 8. Q3 — Root cause of SW+polter and ISW both being individually wrong

The shared-pipeline component is the **seed itself** plus its propagation through 280 → 14000 Mpc of IMEX evolution, *plus* the gauge mismatch in the SW source assembly.

- *Q3.1*: Two shared quantities upstream of both SW and ISW. **(i)** The photon hierarchy state at η = η_init ≈ 260 Mpc, governed by `_seed_formulae` (regular_adiabatic_ic.py:142–185). The leading-order Lowell expansion gives `δ_γ(η_init) = (b_k_sq/3) · x²`, valid only for `x = k·η_init ≪ 1`. At η_init = 260 Mpc the validity boundary is k ≈ 4·10⁻³ Mpc⁻¹. Beyond it the seed is wrong by `O(x²)` — at k = 5·10⁻², `x = 14`, giving `δ_γ_seed = 65` for b_k_sq = 1, while the true sub-horizon adiabatic δ_γ at η_init = 260 Mpc with ζ = 1 is O(1) modulated by acoustic phase. The integrator faithfully evolves the wrongly-seeded state forward, producing over-amplified Φ, Ψ, Θ_0 at recombination. **(ii)** The gauge identity used to build the SW source (cf. F4 / D-3): `Θ_0_synchronous` from the tower combined with `Ψ_Newtonian` from the constraint reconstruction.

  The (i) effect was observed indirectly by Round-9 §5 ("the probe injects perturbations that are ~2.18·10⁴ times larger than the physical seed"), but framed as an amplitude-convention question (b_k_sq vs ζ vs A_s) rather than an asymptotic-validity question. Linearizing the b_k_sq scaling (Round-10/11 fix) was correct but did not address the underlying Lowell-expansion truncation. Compare to CAMB: CAMB starts radiation-era integration at much earlier η (z ≈ 10⁹) where x ≪ 1 for all k of interest, and uses tight-coupling approximation to bound the cost.

- *Q3.2*: Yes, two clean diagnostics, both are described in §10 below.

  - (a) **Compare BASS Φ(η_rec, k) vs CAMB Φ(η_rec, k) directly**, k-by-k. CAMB exposes the metric perturbations via `get_redshift_evolution`. If BASS Φ at recombination is x²-scaling-too-large at sub-horizon, this confirms (D-2) without going near LoS.
  - (b) **Run BASS at a much earlier η_init** (e.g. 1 Mpc, with the Lowell formula now valid since x = k·1 < 0.05 for k ≤ 5·10⁻²) and re-do the per-(k, ℓ) comparison. Computationally expensive without a tight-coupling approximation, but a single k = 5·10⁻² run would settle the question.

- *Q3.3*: The Q-17.2 Einstein constraint bracket cancellation — `four_pi_g_a2_over_k2 = 1.5·h0_mpc²·a²/k²` and the (`δρ_tot − 3·calH·mom/k`) bracket — looks correct in `tier_b_source_extraction.py:275–302`. The Round-5 anisotropic-stress correction (intensity quadrupoles only, not Π) also looks right. The bug is upstream of this code: Φ, Ψ are reconstructed correctly *from the integrator output*, but the integrator output itself encodes the over-amplified seed (D-2) and is in the wrong gauge for the ℓ=0 monopole (D-3).

## 9. Q4 — Architectural decision

Three defects, each requiring a different fix:

- **(D-1) Decouple LoS grid**: incremental, ~1–2 weeks. Decouple `_los_and_wrap` from the integrator output grid: build a separate per-k LoS grid sized for `j_ℓ(k(η₀-η))` resolution, evaluate the existing PchipInterpolator-wrapped Φ, Ψ, Π on that grid, project. Pre-tabulate `j_ℓ(x)` once per ℓ on a fine x-grid for cost amortization. No changes to integrator or seed.

- **(D-2) Lowell-expansion seed validity**: not incremental. Three sub-options:
  - (D-2a) Push η_init back to z ~ 10⁸–10⁹ (η_init ~ 0.01 Mpc) so x ≪ 1 for all k ≤ 5·10⁻¹. Requires implementing tight-coupling approximation in the IMEX integrator to bound radiation-era cost. **Multi-month work.**
  - (D-2b) Extend `_seed_formulae` to higher orders in x. Lowell §13.2 only writes the leading terms; the next-to-leading is straightforward (Ma & Bertschinger 1995 §7 eq. 96–100 give the recursive structure), but converging at x = 14 would require summing ~20 orders, which defeats the purpose of an asymptotic expansion. **Not viable.**
  - (D-2c) Matching-asymptotic: hand off from analytic super-horizon seed at very early η to numerical sub-horizon evolution at horizon crossing. Essentially what CAMB does. **Multi-month work.**

- **(D-3) Gauge mismatch**: a single-line conversion `Θ_0_N = Θ_0_S + (h_S'/6 + ...)` *if* the integrator exposes `h_S'` or its equivalent; otherwise requires plumbing the gauge term through. **Sub-week if h is exposed, multi-week otherwise.**

Doing only (D-1) lands the per-(k, ℓ) ratios in the 10–100 range instead of 1000+ — better, but nowhere near production. Doing (D-1) + (D-3) might land in the 2–10 range. Only all three together get to <1.05.

This is why **Option B (hybrid)** is the only path to production-grade FLRW D_2 in calendar months rather than calendar quarters:

> Use CAMB transfer functions Δ_ℓ^T(k), Δ_ℓ^E(k) directly for the FLRW limit. Use BASS PSTF only for the genuinely-Bianchi correction layer (m = ±2 channels, anisotropic-stress modifications, tilted-boost terms). The split is clean because the Bianchi correction is a *perturbation* on top of the FLRW base, and the FLRW base doesn't need PSTF to be computed correctly — CAMB has been validated on it for decades. Route-B Rust D_2 = 1002.087 μK² remains the FLRW anchor; BASS reports `D_2_total = D_2_FLRW_CAMB + ΔD_2_Bianchi_PSTF` where the second term is what the BASS pipeline contributes.

(D-1), (D-2), (D-3) can then be fixed on a longer-running architectural track without blocking the science output. Once all three are solved, a final BASS-only path can replace the hybrid and reproduce CAMB to ~1 % in the FLRW limit as a regression check.

---

## 10. Decisive 1-hour test that disentangles (D-1) / (D-2) / (D-3)

The team has CAMB 1.6.6 installed and has confirmed it produces the per-(k, ℓ) reference Δ_T values used in F1. Run the following test, which costs ~1 hour of wall time and isolates each defect cleanly without modifying any BASS code:

```
TEST: CAMB-source-on-BASS-grid LoS projection
=============================================

Step 1 — Extract CAMB Newtonian-gauge sources S_T_CAMB(η, k) at the
    same Planck-2018 cosmology used in the audit. CAMB exposes these
    via results.get_redshift_evolution(['Phi_N', 'Psi_N', 'delta_photon',
    'velocity_baryon', ...], k, redshifts) — convert z to η via the
    bg_table. Build S_T_CAMB on the BASS integrator η-grid (n_output=64,
    uniform-linear from η_init=260 to η_today=14147) using the same
    formula as build_temperature_source.

Step 2 — Project S_T_CAMB against j_ℓ(k(η₀-η)) using the SAME
    project_temperature_transfer routine (np.trapezoid on 64 points).
    Call this α_camb_source_bass_grid(k, ℓ).

Step 3 — Compare against (a) the CAMB direct Δ_T_CAMB(k, ℓ) and
    (b) the existing BASS α_BASS(k, ℓ) at the same k-grid {1e-3, 1e-2,
    3e-2, 5e-2}.

Interpretation:

  Case A: α_camb_source_bass_grid ≈ Δ_T_CAMB to within 5%
    → LoS quadrature is fine; defect is purely BASS source (D-2 + D-3).
    → Hybrid is the only path. Do not waste time on D-1.

  Case B: α_camb_source_bass_grid is 10-100× too large at sub-horizon k
    → D-1 (LoS undersampling) is the dominant defect.
    → Decouple the LoS grid and re-test.

  Case C: α_camb_source_bass_grid matches Δ_T_CAMB at low k but
          diverges at high k
    → D-1 is dominant at high k, source is fine.
    → Same fix as Case B.

  Case D: any sign-flip in α_camb_source_bass_grid relative to
          Δ_T_CAMB at low k
    → Means even a perfect source can't be projected correctly on the
       BASS grid (Δη=220 Mpc on 19 Mpc visibility FWHM). Confirms D-1
       severity.
```

I expect Case C: low-k matches CAMB to within ~30 %, high-k diverges to 10–50× over-prediction. This would confirm D-1 contributes ~10× at high k, leaving the residual ~10–100× at all k attributable to D-2 + D-3.

If the test result is Case A — that is, the BASS LoS routine projects CAMB sources correctly — then (D-1) is essentially benign for the Bianchi-correction-only role envisaged in the hybrid recommendation. In that case the architectural decision simplifies to: keep the BASS LoS routine, replace the BASS source extractor with a CAMB-driven equivalent for the FLRW limit, and the BASS PSTF source extractor only handles the Bianchi-correction layer where there's no CAMB equivalent.

This single test would have settled the question after Round 12 if it had been run. **Strongly recommend it as the first action after this audit, before any further code changes.**

---

## 11. Recommended fix path (concrete)

**Near-term (1–2 weeks)**:

1. Run the §10 decisive test. Use its outcome to scope (D-1)'s contribution before allocating engineering time to it.
2. Implement Option B hybrid: add `bass.spectrum.flrw_camb_bridge` that wraps CAMB's `get_cmb_transfer_data` and produces Δ_ℓ^T(k), Δ_ℓ^E(k) with the same `BianchiTransferFunctions` interface. Route the FLRW limit (`bianchi_type="I"`, β=0) through this bridge by default; preserve the BASS PSTF path as `flrw_pstf_legacy` for diagnostic comparison. This unblocks D_2 production.
3. Build the BASS Φ-vs-CAMB-Φ direct comparison at recombination (Q3.2-a) to confirm the (D-2) diagnosis empirically.

**Medium-term (1–3 months)**:

4. Fix (D-1): decouple LoS η-grid from IMEX output. New module `bass.los.los_grid_builder` produces per-k grids; `_los_and_wrap` queries the existing PchipInterpolator-wrapped sources on the new grid.
5. Pre-tabulate `j_ℓ(x)` once per ℓ on a fine x-grid (analogous to CAMB's `BesselJl_setup`) for performance.
6. Fix (D-3): expose the synchronous-gauge metric trace `h_S'` (or equivalent) from the integrator state, and convert `Θ_0_S → Θ_0_N` in the source extractor before assembling the SW source. Cross-check the F4 Ψ trajectory disappears in favor of monotonically-decaying Newtonian Ψ.

**Long-term (3–6 months)**:

7. Tackle (D-2) via tight-coupling-enabled early-η_init or matching-asymptotic. Once (D-1), (D-2), (D-3) are all fixed, validate the BASS-only path against the CAMB hybrid as a regression test; then deprecate the hybrid for the FLRW limit (keep it for cross-checks).

**What to NOT do**: keep searching for a k-independent or cleanly-(k, ℓ)-structured normalization factor. Round-9 already showed the residual is N_k-dependent and probe-amplitude-dependent — incompatible with a single missing constant. Three further audit rounds spent on this hypothesis is enough; F1 closes the door.

---

## 12. Confidence and caveats

**High confidence (≥ 0.85)**:

- The 4√2 fortuitous-coincidence interpretation (F1).
- The IMEX/LoS grid-conflation diagnosis (D-1), based on direct code inspection of `_los_and_wrap` and `project_temperature_transfer` plus the toy convergence experiment in §2.
- The Lowell-expansion-out-of-validity-range diagnosis (D-2), based on `regular_adiabatic_ic.py:142–185` showing the leading-order x² and x³ terms applied at x as large as 14.
- The synchronous/Newtonian gauge mismatch diagnosis (D-3), based on the Phase A Ψ sign flip + Θ_0 linear-in-η ramp signature, both of which are canonical synchronous-gauge artifacts.
- Recommendation of Option B as the only realistic near-term path.

**Medium confidence (0.5–0.7)**:

- That (D-1), (D-2), (D-3) are the *complete* set of root causes. There may be additional smaller defects (e.g. boundary-effect in `_fd4_derivative` for ISW, anisotropic-stress sign questions noted in Round-5 Q-17) that survive after these three are fixed and become visible at the few-percent level. The toy experiments in §2 don't fully model BASS's actual sources.
- That CAMB at τ = 10⁻⁵ in the diagnostic scripts is the right reference — the team should double-check that CAMB's τ → 0 limit doesn't itself introduce a small artifact at these very-low ℓ. CAMB is well-tested but the τ = 10⁻⁵ mode is unusual.

**Caveats**:

- I did not run the BASS pipeline directly (the bundle is code-only without a runtime environment). All quantitative claims are from reading source + transcripts + my own toy experiments. The (D-2) diagnosis predicts that BASS Φ(η_rec, k = 5·10⁻²) at b_k_sq = 1 is roughly two orders of magnitude larger than CAMB Φ(η_rec, k = 5·10⁻²) at ζ = 1; running this comparison (Q3.2-a) in ~1 hour would falsify or confirm definitively. The (D-3) diagnosis predicts that subtracting the synchronous-gauge `h_S'/6` term from BASS Θ_0 collapses the Ψ trajectory to a monotonically-decaying matter-era plateau without sign flip; this is also testable in <1 day.
- The bundle's component-ablation script (`v5_round12_component_ablation.py:127`) uses the IMEX η-grid for LoS just as the production pipeline does, so all ablation conclusions inherit (D-1). Re-running ablation with a refined LoS grid (after fix D-1) could reveal whether the SW vs ISW per-component picture survives or shifts.
- Confidence that Option B is the *right* hybrid split (CAMB for FLRW base, BASS for Bianchi correction) depends on the Bianchi physics actually being a perturbative correction on top of FLRW, which it is for `|β| ≪ 1` but not for highly anisotropic Bianchi types. For the BASS team's stated science goal (tilted FLRW + small Bianchi anisotropy), the split is clean. For more extreme anisotropic models the architecture would need re-evaluation.

**Primary references** for the LoS, seed-validity, and gauge claims:

- Lewis & Challinor 2002, *Efficient computation of CMB anisotropies in closed FRW models*, PRD 66, 023531, §5 (LoS sampling and grid decoupling).
- Ma & Bertschinger 1995, ApJ 455, 7, §7 eq. 96–100 (regular-adiabatic super-horizon expansion is leading-order in kτ); eq. 19 + 27a (synchronous → Newtonian gauge transformation for δ_γ).
- Seljak & Zaldarriaga 1996, ApJ 469, 437 (LoS formulation).
- Ellis & van Elst 1998, *Cosmological models* (Cargèse lectures), §2.4–§3.3 (1+3 covariant PSTF formalism, gauge-invariance of ℓ ≥ 1 multipoles around FRW).
- CAMB source `cmbmain.f90` `out_transfers` and `bessels.f90` `BesselJl_setup` (reference implementation of decoupled LoS sampling and Bessel pre-tabulation).

---

## 13. Closing note to the BASS team

The pipeline has the structure of a research prototype that's been pushed past its design point. The original `flrw_bessel_projector.py` docstring (lines 32–60) was clear about what the projector is and isn't responsible for: "PROJECTOR/INTEGRATOR only … source-term evolution NOT solved here". Source-term evolution was deferred to "W10+", and what we now see in `tier_b_source_extraction.py` is a hand-rolled bridge that reuses the IMEX integrator for source evolution — but with η_init = 260 Mpc that's too late for sub-horizon adiabatic seeds, takes synchronous-gauge tower outputs and feeds them into a Newtonian-gauge Einstein-constraint reconstruction, and then projects on the IMEX output grid. Each step is a pragmatic shortcut that's individually defensible; the composition is not.

The four prior audit rounds focused on amplitude and convention questions because the team naturally treated the pipeline as a working artifact with one missing factor. The diagnostic data — especially Round-9's "convention factor varies with N_k and probe amplitude" and Phase A's Ψ sign flip — was already telling them otherwise. F4 here adds the gauge dimension to that picture explicitly.

For the doctoral work specifically: the FLRW-limit baseline is what reviewers will compare to CAMB. A hybrid that uses CAMB for the FLRW limit and routes only the genuinely-Bianchi part through BASS is the defensible path; the Bianchi-correction layer (m = ±2 channels, anisotropic-stress modifications) is where the original scientific contribution lives anyway, and that part doesn't depend on getting the FLRW Δ_ℓ exactly right via the same code path. Spending another quarter on internal BASS-FLRW debugging vs spending it on the Bianchi-correction physics is, at this point, an opportunity-cost question rather than a technical one.