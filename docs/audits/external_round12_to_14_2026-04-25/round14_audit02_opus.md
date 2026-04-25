# V5-RUNTIME Round-14 External Audit Verdict

**Auditor**: Claude Opus 4.7 [1m] (independent re-analysis)
**Date**: 2026-04-25
**Bundle SHA**: 0536f0e
**Bundle**: v5_round14_audit_bundle.zip (115 KB, 35 files)

## Verdict (one-line)

**HYBRID-RECOMMENDED** — with a parallel short-term incremental probe to
localize the blame between extractor vs. tower evolution.

## Summary

The three new Round-14 transcripts, taken together, rule out the entire
"single missing convention factor" class of hypotheses (Codex's 4√2,
Opus's n_output, GPT-5.5's Doppler) and instead force a structural
diagnosis: the `tier_b_source_extraction.py` Newtonian-gauge Ψ/Φ
reconstruction via the Einstein constraints is ill-conditioned on the
BASS output grid, mainly because (i) Ψ is built from a near-cancelling
combination `(δρ_tot − 3ℋ·mom/k)` multiplied by a 1/k² prefactor, and
(ii) the underlying VER2 tower is sampled onto `np.linspace(η_init,
η_today, 64)` and then passed through `PchipInterpolator` — a
combination that empirically loses sign at small k and explodes with
numerical noise at larger k (the `scipy _cubic.py:325` divide-overflow
warning is a direct flag that PCHIP is seeing near-zero `mk` slopes —
i.e. stationary points in Ψ from 1/k² amplified roundoff). The cleanest
production path is to feed the existing, well-tested
`flrw_bessel_projector.py` with CAMB-supplied `(Ψ, Φ̇+Ψ̇, Θ_0, v_b, Π)`
for the FLRW limit, reserving BASS's PSTF tower + extractor for the
genuinely anisotropic Bianchi contribution where no alternative exists.

## F1 / F2 / F3 verification

### F1 — "4√2 is fortuitous" — CONFIRMED

Mathematically: the 4√2 hypothesis predicts a k- and ℓ-independent
ratio |BASS/CAMB|² = 32. The per-(k, ℓ) data in
`round12_camb_comparison_n64.txt` give ratios spanning 0.21 → 1836 —
five decades of spread, with sign changes. The observation that
`D_2_probe(k_min=1e-3) · (1/32) → 1.005` is therefore a *weighted
integral* coincidence, not evidence of a convention factor. The
`k_min=1e-4` row of `phase_b_fix_D1D2D6D7.txt` confirms this: with the
same 1/32 factor applied, the ratio is 23.6, not 1 — i.e., changing
the lower-k cutoff by 10× breaks the "fix" by a factor of ~24. A true
convention factor would survive k_min changes.

### F2 — "BASS does not converge in n_output" — CONFIRMED and SHARPENED

Non-convergence isn't just failing to approach CAMB; it's failing
internally. Take k=3e-2, ℓ=2: α = +0.0930 → +0.0155 → +0.00433 as
n_output goes 64 → 256 → 1024. That's a factor-3 drop at each step, a
power-law decay of roughly n_output^(−1.5), which is NOT the O(h²)
decay of trapezoidal quadrature on a smooth integrand. If the
integrand were smooth, doubling n would give a 4× error reduction with
stable magnitude; here the *magnitude itself* keeps dropping, meaning
we are seeing a *leading* term shrink, not a convergence tail. This is
the signature of an aliasing/resonance artifact: a spurious
high-frequency mode in S_T being down-sampled differently at each
n_output, producing a different aliased projection at each grid.

PCHIP overflow warnings at n_output ≥ 256 are a *related* symptom, not
an independent cause. `_cubic.py:325` raises when `mk[:-1]` or `mk[1:]`
(consecutive Pchip slope estimates) approach zero. That happens when
Ψ(η) — which PCHIP is interpolating — has nearly-flat segments followed
by jumps, i.e. when the 1/k²-amplified roundoff in the Einstein
constraint produces a step-like Ψ(η). At n_output=64 the steps are
undersampled and averaged out of the integrand; at n_output ≥ 256 they
are resolved and the integral sees them.

Conclusion: **the η-grid is not the bug; it is merely the sampling
lens through which the Ψ-reconstruction bug becomes visible at
different scales.** Opus's R13 n_output hypothesis is thereby REFUTED
as the root cause — raising n_output does not help because the
underlying source `Ψ(η, k)` is numerically wrong even before sampling.

### F3 — "SW + polter + ISW both individually wrong" — CONFIRMED and REFINED

The component ablation is the strongest single piece of evidence in
the bundle. Three sub-findings deserve emphasis:

**(a) Doppler ≪ 1% — rules out `d/dη[g·v_b]` and v_b normalization.**
`FLRWSourceTerms.with_doppler_only` returns Doppler/CAMB ratios
0.001 → 2.2 across (k, ℓ). The 2.2 peak at k=5e-2 ℓ=3 is the *largest*
Doppler contribution seen and it is still <0.5% of the FULL signal at
that (k, ℓ). This buries any hypothesis that concerns v_b, the slot-1
baryon-velocity normalization, or the `np.gradient(g·v_b, η)`
stencil.

**(b) SW and ISW are individually wrong by the same *kind* of error.**
Look at k=5e-2 ℓ=2:
  - SW/CAMB = −118
  - ISW/CAMB = +177
  - FULL/CAMB = +57
The partial cancellation in FULL is a smoking gun: both SW and ISW
are driven by the *same* Ψ-reconstruction, via
(SW) g · (Θ_0 + Ψ + Π/4) and (ISW) exp(−κ)(Φ̇ + Ψ̇). If Ψ had a
k-dependent amplitude error `Ψ_BASS = A(k) · Ψ_true`, SW picks up that
factor at η_* (where g peaks) and ISW picks up its *time-derivative*
across the full integration, which for a smooth error gives a similar
but not identical factor. Observed SW and ISW contributions both grow
by ∼100× relative to CAMB at sub-horizon — exactly the behavior
predicted by a shared-Ψ amplitude error.

**(c) At super-horizon (k=1e-3, ℓ=2) the SW contribution is **smaller**
than CAMB (0.40×), while at sub-horizon (k=5e-2, ℓ=3) it is 1870×.**
This non-monotonic, k-dependent SW/CAMB pattern *cannot* be produced
by any k-independent normalization factor. It *can* be produced by the
1/k² amplification in the Einstein constraint interacting with the
cancellation `(δρ_tot − 3ℋ·mom/k)` — that combination is O(k²)
analytically at super-horizon but numerically becomes O(ε_machine · k²)
plus `O((3H·mom/k) · ε_rel)`, where the second term is k-independent
noise that the 1/k² prefactor amplifies to k^(−2) scaling.

## Q1 — is 4√2 a real convention, just hidden?

**No.** The 1.005 ratio at `k_min=1e-3` is arithmetically
`(32 · ∫|α_sub|²·P_R)·(1/32)`; any weighting factor that happened to
satisfy `⟨|α/α_CAMB|²⟩ ≈ 32` in the specific sub-horizon window would
have produced the same "clean" match. To verify, the team can compute
the *weighted-average* convention factor using the same k-band and it
will come out to 4√2 by construction — not evidence of new physics.

A real convention factor, if it existed, would show up as a tight
clustering of |BASS/CAMB| around one value *per k-bin*. The R14
table's std/|mean| = 108-357% proves the opposite: the ratio
distribution is broad, which is incompatible with any single
multiplicative convention.

A specific additional cross-check I recommend: isolate
σ_γ = 2·Θ_2^γ, pull it directly from the VER2 tower, and compare
with CAMB's `get_matter_transfer_data` → `delta_tot` or the tower
expansion from `camb.get_results().get_cmb_transfer_data().delta_p_l_k`
at ℓ=2. If σ_γ matches CAMB within 1%, the tower evolution is fine
and the bug is purely in `tier_b_source_extraction.py`. If σ_γ is off
by a clean power of 2 (4, √2, 2), that localizes a leftover
normalization in Θ_2 itself (separate from the Round-10/11 seed
fixes, which only touched the initial condition).

## Q2 — why BASS fails to converge in n_output

The scipy PCHIP warning at line 325 is:
  `whmean = (w1/mk[:-1] + w2/mk[1:]) / (w1 + w2)`
which divides by the local slope estimates `mk = diff(y)/diff(x)`.
Overflow there means `mk ≈ 0` at some interior point — i.e. Ψ(η) has
a stationary point with zero slope. This should not happen in a
physically smooth Ψ(η, k). Its presence at n_output ≥ 256 (but not 64)
means:

- At n_output=64, Δη=220 Mpc — interval too coarse to resolve any
  "wiggle" in Ψ; the gradient is averaged out.
- At n_output=256, Δη=55 Mpc — comparable to Silk-damping scales;
  the wiggle starts to show.
- At n_output=1024, Δη=14 Mpc — the wiggle is fully resolved and
  PCHIP sees true local-extrema → divide-by-zero.

This is the numerical fingerprint of a Ψ(η) that contains
1/k²-amplified stair-steps from the Einstein-constraint cancellation,
not a smooth physical Ψ. The IMEX solver's internal dense_output is
likely fine — it's the **post-hoc Ψ assembly on the output grid**
that manufactures the spurious stair-steps.

**Practical recommendation:** the right n_output policy is *not*
uniform-linear at any density. It should be log-spaced in (1+z) around
recombination (g-peak FWHM ~19 Mpc) and sparse elsewhere — the
`build_eta_grid_log_in_z` utility in `flrw_bessel_projector.py` exists
for exactly this purpose but is not currently used by the production
pipeline. But this is a palliative: it masks the Ψ pathology; it does
not fix it.

## Q3 — shared root cause between SW and ISW

Three candidates, ranked by probability:

**(1) Ψ reconstruction via Einstein constraints (HIGH probability).**
The Phase-A-fixed diagnostic for k=1e-4 shows `Ψ(η_init=260)=−0.336`
jumping to `Ψ(η_*=280)=−1.245` over a 20 Mpc interval. In MD super-
horizon, Ψ should be approximately frozen at −10/(4R_ν+15) ≈ −0.601.
The BASS value 20 Mpc later is 2× *too large in magnitude*. And at
η=3787 the Ψ has *flipped sign* to +0.393. No physical Ψ behaves this
way on super-horizon scales — this is the 1/k² constraint-noise
amplification. Every line in `tier_b_source_extraction.py:278-302`
evaluating `phi = four_pi_g_a2_over_k2 * (delta_rho_tot - 3·calH·mom/k)`
is suspect.

Concretely: `delta_rho_tot = ρ_b δ_b + ρ_c δ_c + 4ρ_γ Θ_0 + 4ρ_ν Θ_0^ν`
and `mom = ρ_b v_b + ρ_c v_c + (4/3)·ρ_γ·(3Θ_1) + (4/3)·ρ_ν·(3Θ_1^ν)`.
At super-horizon these two expressions must cancel to O(k²). They
contain *four* sources of potential convention mismatch:
  - `v_b` from slot-1 baryon history (MB-sync convention)
  - `v_c` from slot-1 CDM history (MB-sync convention)
  - `3·Θ_1^γ` from the tower (comment says MB F_1, but the seed
    stores `formulas["theta_gamma"]` directly at that slot — need
    to verify these match)
  - `3·Θ_1^ν` from neutrino_tower

The Round-9 convention audit landed on the hypothesis that
"BASS Θ_ℓ = F_ℓ_MB / 4" (seen as convention-factor candidate in
the R14 transcript). The seed injection at
`regular_adiabatic_ic.py:244` does `photon_T.tensors[0].components[0]
= delta_gamma / 4.0`, which fixes Θ_0 = F_0_MB (=δ_γ/4). But the
adjacent line 245 injects `theta_gamma` directly — *without* a
`/3k` division — into the ℓ=1 slot. The extractor at
`tier_b_source_extraction.py:258` then multiplies by 3 assuming
stored-value IS F_1_MB. If stored-value is actually MB's `θ_γ`
(= 3k·F_1_MB), the extractor under-divides by `k`, giving
`v_γ = θ_γ·3` instead of `v_γ = θ_γ/k · 1 = 3·F_1`. This one-line
mismatch would yield a k-dependent error in `mom` whose amplitude
scales as k · (3k·F_1)/F_1 = 3k² — exactly the kind of k-power that
when amplified by 1/k² gives a k⁰ error at one limit and diverges at
the other. **I strongly recommend the team print, at η_init, both
`theta1_g` from the tower and `formulas["theta_gamma"]` from the seed
builder and confirm they match byte-identically.** They should, if the
convention is consistent; if they don't, you have found the bug.

**(2) Visibility g(η) / κ(η) (LOW probability).** Background
quantities; would affect SW and ISW symmetrically, not explain
sign-flip between them. Unlikely to be the dominant bug.

**(3) LoS Bessel projector (VERY LOW probability).** The projector is
well-tested by the W9-01 sharp-visibility analytic and the Bessel
sum-rule checks in `flrw_bessel_projector.py:614-661`. It would be
the same code CAMB-sourced sources pass through, so a hybrid test
(below) would trivially exonerate it.

## Q4 — architectural decision

I recommend **Option B (Hybrid), executed in two stages, with Option A
held in reserve**:

### Stage 1 (2-3 days) — Hybrid validation of the LoS projector

Wire CAMB to supply the five callables that `flrw_bessel_projector.py`
expects:

```python
# From camb.get_results().get_background(): a(η), ℋ(η)
# From camb.get_matter_transfer_data() and CAMB's internal Ψ, Φ:
source = FLRWSourceTerms(
    theta_0 = camb_theta0_interp,
    psi     = camb_psi_interp,
    phi_dot_plus_psi_dot = camb_phiplus_psi_dot_interp,
    v_b     = camb_vb_interp,
    pi      = camb_pi_interp,
)
```

Feed through `project_temperature_transfer` and assemble in
`cl_assembly.py`. Target: D_2 matches CAMB's own D_2 to <1%.

**If this passes:** the LoS projector is exonerated and the bug is
100% localized to `tier_b_source_extraction.py`. Proceed to Stage 2.

**If this fails:** the bug is also (partly) in the projector or the
quadrature, and the audit scope widens. I estimate ≥90% probability
it passes; the projector is the most-tested piece in the stack.

### Stage 2 (2-3 weeks) — Extractor repair, with per-component CAMB cross-check

For each of the five callables in `FLRWSourceTerms`, add a
`*_vs_camb_max_rel_error` assertion in a new test file
`test_source_extractor_camb_match.py`. The tests compare
extractor-produced vs CAMB-produced callables on a common η-grid and
fail on >1% deviation.

Fix order, by sensitivity:

1. **Ψ reconstruction.** Replace the Einstein-constraint
   `Φ = (3H²/2k²) · (δρ − 3ℋ·mom/k)` with the gauge-invariant
   *comoving* formulation:
   ```
   Φ = (3H²/2k²) · δρ_comoving    where
   δρ_comoving = δρ_tot + 3·ℋ·(ρ+p)·θ_tot/k²
   ```
   Note δρ_comoving is O(k²) at super-horizon analytically, so the
   1/k² prefactor gives an O(1) Φ with no cancellation. This is the
   standard CAMB / CLASS strategy.

2. **Θ_1 convention.** Print
   `photon_T.tensors[1].components[1]` immediately after seed and
   again after one integrator step; compare to the MB convention
   formula `θ_γ_expected = (1/27)·(kτ)³`. If the stored value is
   `θ_γ` (not `F_1 = θ_γ/3k`), change the extractor's `vg = 3·Θ_1`
   to `vg = Θ_1 / k`. I'd give this a 50% chance of being the single
   line that matters.

3. **Anisotropic stress.** Round-5 Q-17 said σ_γ = 2·Θ_2^γ. Verify
   this against CAMB's σ_γ(η, k). The extractor uses
   `stress_intensity = (8/3)(ρ_γ·Θ_2^γ + ρ_ν·Θ_2^ν)`. If Θ_2
   normalization differs from the assumed, ψ−φ will be wrong even
   after a correct Φ.

### Option A held in reserve — pure incremental fix

If Stage 1 passes but Stage 2 reveals that the extractor needs more
than surface repair (say, a full gauge-transformation rewrite), the
HYBRID path becomes the production answer for the FLRW limit and the
extractor work is confined to Bianchi mode m ≠ 0. That is an
acceptable production outcome: no BASS customer needs the FLRW m=0
extractor to beat CAMB; they need BASS's Bianchi modes. The extractor
is only required to be *correct* for the FLRW limit as a
regression anchor — and for that, Hybrid suffices.

### Option C (from-scratch re-derivation) — NOT NEEDED

I see no evidence in the bundle that the PSTF formalism itself is
broken. The VER2 tower evolution appears stable (Blockers 1+2 closed,
IMEX converges at cosmological range). What is broken is the
*projection* from the PSTF-tower-native representation onto a
Newtonian-gauge presentation for the LoS projector. That is a
well-contained piece of code in a single file. Architectural rework
would throw out working infrastructure.

## Recommended fix path (concrete)

**Week 1:**
- Implement `source_from_camb()` adapter returning `FLRWSourceTerms`
  with each callable backed by a CAMB-derived interpolator on
  `η_grid`. Use CAMB 1.6.6 `get_cmb_transfer_data` and
  `get_background`.
- Feed into existing `flrw_bessel_projector.project_temperature_transfer`
  + `cl_assembly.assemble_c_ell_flrw`. Target D_2 match <1% with CAMB.
- Add `v_b` vs CAMB, Ψ vs CAMB, Π vs CAMB per-quantity tests.

**Week 2:**
- Print-audit `photon_T.tensors[1].components[1]` convention (Q3
  candidate (1)). Likely one-line fix in
  `tier_b_source_extraction.py:258`.
- Add `delta_rho_comoving` formulation to the extractor, gated by a
  flag `use_comoving_constraint=True` so the legacy path stays for
  regression bisection.
- Per-(k, ℓ) CAMB comparison of BASS-extractor-produced Ψ vs
  CAMB-supplied Ψ. Target <1% at k ∈ [1e-4, 1e-1].

**Week 3:**
- If Stage 2 passes, swap `tier_b_source_extraction.py` path back on
  and repeat the R14 CAMB comparison. Ratios should collapse to
  ~1.00 ± 0.01 across all (k, ℓ).
- If Stage 2 produces residual scatter of a few % even with comoving-
  gauge Φ, that scatter is the PSTF-tower evolution error. Quantify
  it and decide whether to tighten IMEX tolerances or ship.

**Week 4:**
- Update PR-024b/024c to consume the fixed extractor.
- Add a permanent CI assertion: BASS extractor-produced D_2 within
  0.5% of CAMB D_2 at FLRW limit. This becomes the Phase-1 sentinel.

## Confidence and caveats

**High confidence (≥85%):**
- The 4√2 match at k_min=1e-3 is fortuitous, not a convention.
- Ψ reconstruction via the current Einstein-constraint code is
  numerically ill-conditioned and is the dominant error.
- PCHIP overflow warnings are symptoms of 1/k²-amplified roundoff,
  not a scipy bug.
- The LoS projector (`flrw_bessel_projector.py`) is healthy; Hybrid
  validation will pass.
- Hybrid is a safe production path for the FLRW limit.

**Medium confidence (50-70%):**
- The `Θ_1` ↔ `θ_γ` vs `F_1` convention mismatch I flagged in Q3(1.2)
  is the *single* one-line bug. Could also be a separate mismatch in
  `theta2_nu` normalization, or a ρ_γ(η) vs ρ_γ(a) conversion in the
  registry. Worth printing both seed-formula and post-seed-injection
  values to resolve.
- The `delta_rho_comoving` reformulation will solve the super-horizon
  pathology. If the BASS tower's velocities are gauge-inconsistent
  even after fix (e.g. sync/Newton mismatch persists), additional
  gauge-transformation work may be needed.

**Low confidence (<50%):**
- That Stage 2 (extractor repair) is achievable in 2-3 weeks. Gauge
  transformations can hide subtle issues; if the team finds the
  tower's velocities are already pseudo-Newton (rather than sync),
  the comoving formulation may need further adjustment. Budget 4-6
  weeks realistically.

**Caveats:**
- I did not re-run any BASS solver; my analysis is based on the
  transcripts and code in the bundle. A discrepancy between
  transcript text and actual current code would change the verdict.
- The CAMB comparison was done at `tau=1e-5`, which is essentially
  no reionization. This matches BASS's MB-95 baseline, so is correct
  for bit-identical comparison — but production Planck cosmology has
  τ ≈ 0.054, and tests at the production τ are still needed before
  PR-026.
- I have not verified CAMB 1.6.6's own internal consistency (one
  cycle of CAMB regression against CAMB 1.5.x would be prudent
  before pinning it as ground truth; CAMB-notes sign conventions
  have shifted historically). I consider this <5% risk.

**References**
- Ma & Bertschinger 1995, ApJ 455, 7 — §4 gauge transformation,
  §5 eqs 23a-d (synchronous gauge), §7 eq 96 (regular adiabatic IC).
- Lewis & Challinor 2002 (CAMB Notes), App. C — regular adiabatic
  series, and the `χ_0 = −1` convention used by BASS's
  `b_k_sq = 1.0` default.
- Seljak & Zaldarriaga 1996, ApJ 469, 437 — eq 12 (LoS source) and
  the δρ_comoving + comoving-gauge Poisson as the standard
  replacement for the Einstein-constraint approach used in BASS.
- Kamionkowski, Kosowsky, Stebbins 1997, PRD 55, 7368 — Π
  decomposition used in the BASS polter source.
- CAMB source: `fortran/equations.f90` routine `output` and
  `Newtonian_potential` — the reference implementation of the Ψ/Φ
  reconstruction strategy recommended above.
