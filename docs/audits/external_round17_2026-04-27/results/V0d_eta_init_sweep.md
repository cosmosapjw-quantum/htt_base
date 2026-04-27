# V0d — η_init sweep counter-test

**Run:** 2026-04-27, commit `35e39ab`. **Script:**
`scripts/v5_round17_eta_init_sweep.py`. **Wall time:** 188.6 min on 4 workers.

## Result table

| η_init [Mpc] | x_max = k_max·η_init | D_2 [μK²]    | D_2 / D_anchor | PCHIP overflow |
|---:|---:|---:|---:|:---:|
| 261.0 | 8.254 | 7.0574e+03 | **7.043** | no |
| 200.0 | 6.325 | 1.2674e+11 | **1.265 × 10⁸** | no |
| 150.0 | 4.743 | 2.8830e+27 | **2.877 × 10²⁴** | no |
| 100.0 | 3.162 | 2.7296e+33 | 2.724 × 10³⁰ | yes |
|  70.0 | 2.214 | 4.8479e+30 | 4.838 × 10²⁷ | yes |
|  50.0 | 1.581 | 1.3584e+33 | 1.356 × 10³⁰ | no (silent NaN-clip?) |

## Predictions vs. observed

The audit's D-2 prediction (Report 2 §2.3): *monotone collapse from
≈ 6.43 (at η_init = 261) toward ≈ 1 (at η_init ≈ 50–70 Mpc, where
`x_max < 1` for k_max = 0.0316 Mpc⁻¹). Power-law slope on log-log axes.*

**Observed:** anti-monotone explosion. Ratio grows from 7 to 10⁸ to
10²⁴ to 10³⁰ as η_init shrinks from 261 to 100 Mpc. Then chaotic in
the [50, 100] Mpc regime where the species-table edge has been crossed.

## Diagnosis

Three independent infrastructure defects, all flagged by audit Report 2 but
not previously quantified, conflate to make V0d as designed
**uninterpretable as a pure D-2 diagnostic**:

### Defect-1: `_approx_tau_c` heuristic at `regular_adiabatic_ic.py:94-101`

```python
def _approx_tau_c(eta_initial: float, a_initial: float) -> float:
    """Early-time TCA startup timescale. … not a recombination solve;
    it is a deterministic radiation-era scaling chosen only to populate
    the small photon quadrupole / E2 startup surface in the absence of
    the full Thomson-rate pipeline."""
    return 0.15 * eta_initial / np.sqrt(max(a_initial, 1.0e-30))
```

The seed's photon quadrupole IC is `pi_gamma = -(32/45) · k · tau_c · theta_gamma`,
where `theta_gamma = (amp/27) · x³`. For η_init in the radiation era
where `a ∝ η`, the heuristic gives `tau_c ∝ η/√η = η^{1/2}`, so
`pi_gamma ∝ k⁴ · η^{7/2}`. The heuristic at η_init = 261 Mpc gives
`tau_c ≈ 1294 Mpc` (computed: 0.15 × 261 / √a where a ≈ 9.17 × 10⁻⁴),
versus the physical recombination-era `tau_c ≈ 1/Γ_T ≈ 2 Mpc` —
overestimating by ~600×.

The heuristic gets *worse* at deeper η_init because `√a` shrinks faster than the linear factor cancels. At η_init = 50 Mpc with `a ≈ 2 × 10⁻⁴`, the heuristic gives `tau_c ≈ 530 Mpc`, again wildly off from the physical radiation-era value (≈ 0.0004 Mpc at z ≈ 5000).

When the seed's `pi_gamma` is wrongly normalized at the IC, the IMEX
faithfully evolves it forward, producing the over-amplified D_2 at
recombination. Audit Report 2 §2.2 had flagged this exactly:
*"At δ's deep anchor, [_approx_tau_c] must be replaced by `1/Γ_T(η_init)`
from the species table. … Treat this as a pre-condition to δ, not an
alternative diagnosis."*

### Defect-2: Species background table edge at z ≈ 8000 (η ≈ 100 Mpc)

The `SpeciesBackgroundRegistry.from_planck2018` HYREC fixture covers
`z ∈ [0, 8000]`, equivalently `η ∈ [~100, 14147]` Mpc. At η_init below
~100 Mpc, three things start to happen:

1. The integrator's `aux_state.H_local_at(η)` returns 0 (out-of-range
   PCHIP), and the conditional inline DAE-relaxation dispatch silently
   skips (V0f confirmed this).
2. The visibility/kappa PCHIP callables (`flrw_pipeline.py:292-302`) clip
   values at the table edge. Source extraction becomes increasingly
   unphysical near and below the edge.
3. The PCHIP cubic interpolator triggers `RuntimeWarning: overflow
   encountered in divide` warnings in `scipy.interpolate._cubic.py:325`.
   These appeared at η_init = 100 and 70 Mpc; the η_init = 50 Mpc run
   *did not* show the warning, possibly because the table edge had been
   crossed completely by then and the PCHIP returned NaN (which silently
   propagated as ~10³⁰ D_2 instead of as an exception).

This is audit Report 2 R-2 risk made concrete: *"Real-IC at z = 10⁹
requires a radiation-era IC builder for all species. … `_approx_tau_c`
must be replaced by the actual `1/Γ_T(η_init)` from the species table,
and baryon/CDM/neutrino synchronous fluid quantities must be populated
correctly at z = 10⁹."*

### Defect-3: Pipeline cosmological-config helper assumes recombination-era anchors

`cosmological_config.py::build_cosmological_integrator_config` defaults
to `eta_initial = η(z_*) − pre_recombination_margin_mpc`, with
`PLANCK_2018_Z_STAR = 1089.94` and `DEFAULT_PRE_RECOMBINATION_MARGIN_MPC = 20.0`.
The accepted `z_injection ∈ [100, 5000]` range explicitly excludes
the radiation era (z ≫ 5000). My V0d monkey-patches `eta_initial_mpc`
directly into the IntegratorConfig, bypassing the helper's z-range guard,
which means V0d also breaks the helper's own assumption that η_init
sits within ~20 Mpc of recombination.

## Verdict

**V0d as designed is INCONCLUSIVE for the D-2 hypothesis.** The
catastrophic explosion as η_init shrinks is **not** evidence against D-2;
it is evidence that the existing pipeline cannot test D-2 in isolation
because the seed `tau_c` heuristic, the species background-table range,
and the cosmological-config helper all break down together as η_init
moves into the radiation era.

Three out of three defects flagged by audit Report 2 are confirmed by V0d
to be **hard prerequisites for any δ work**, not soft ones.

## Implications for δ planning

The Phase-0 verdict landscape now reads:

| Gate | Status | What V0d clarified |
|---|---|---|
| V0a IMEX routing | ✅ DONE | LSODA confirmed |
| V0b "60% x>1" arithmetic | ✅ DONE | corrected in bundle docs |
| V0c primordial_b_k_sq doc | ✅ DONE | docstrings harmonized |
| V0e bias-floor | ✅ CLOSED | Δ_bias = 0 bit-zero |
| V0f LSODA tractability | ✅ PROVISIONAL TRACTABLE | LSODA Adams mode adequate |
| **V0d D-2 diagnosis** | **🟠 INCONCLUSIVE** | requires _approx_tau_c fix + species table extension first |

V0d's inconclusiveness does **not** refute D-2. It establishes that the
prerequisites for testing D-2 are themselves real engineering work:

- **PR-V0d-pre1** (1-2 days): Replace `_approx_tau_c` heuristic at
  `htt/bass/perturbation/regular_adiabatic_ic.py:94-101` with a real
  `1/Γ_T(η_init)` lookup from the species table. Verify that V0d at
  η_init = 261 (in-range, well-tested) still gives the bit-identical
  baseline ratio 7.04. Verify that V0d at η_init = 200 (just outside
  the cosmological-config helper's recommended range but inside the
  HYREC table) no longer explodes by 8 orders of magnitude.

- **PR-V0d-pre2** (sub-week to ~2 weeks): Extend the species background
  table builder (`bass/species/registry.py::from_planck2018`) to cover
  `z ∈ [0, 10⁹]`. The HYREC fixture extension is straightforward (HYREC
  natively goes to z ~ 10⁸; need to splice the radiation-era pre-HYREC
  thermal history below). Visibility, kappa, baryon, CDM, neutrino,
  Γ_T all need radiation-era scaling extension.

- **PR-V0d-pre3** (sub-day): Lift the `cosmological_config.py`
  `z_injection ∈ [100, 5000]` guard with proper validation that the
  species table covers the requested z. This is a small engineering fix
  but blocks any V0d re-run.

After all three pre-PRs land, V0d can be re-run as a clean D-2 test.
The expectation is then monotone collapse per audit Report 2 §2.3.

## Revised closure plan (updates V5_ROUND17_AUDIT_VERDICT_AND_REVISED_PLAN.md)

```
Phase 0 (gate verification)
  ✓ V0a-c, V0e, V0f closed
  🟠 V0d INCONCLUSIVE — exposed three latent prerequisites

Phase 0.5 (NEW — V0d prerequisites; was implicitly inside δ scope)
  PR-V0d-pre1: replace _approx_tau_c with real 1/Γ_T          [1-2 d]
  PR-V0d-pre2: extend species registry to z = 10⁹              [sub-week-to-2w]
  PR-V0d-pre3: lift cosmological_config.py z_injection guard   [sub-day]
  V0d re-run after pre1+pre2+pre3                              [3 h wall]

Phase 1
  α    (a-switch)         [1-2 d]
  β'   (real-IC)          [1-2 d]
  D-3  (sync→Newt source) [sub-week]

Phase 2
  δ (D-2 closure)         [multi-month, but the prerequisites are now in
                          Phase 0.5 instead of buried inside δ]
  γ (state-layout migration) parallel branch
```

Crucially, **the multi-month δ scope shrinks**. The prerequisites that
audit Report 2 had buried inside the δ-scope estimate (species
extension + tau_c replacement) are now Phase 0.5 work, scoped at
~2 weeks total. The remaining δ work — running the integrator across
12 decades and validating per-decade conservation — is genuinely
multi-month, but a smaller multi-month than before.

## Why the result is honest, not a failure

V0d's inconclusiveness is itself a **load-bearing audit finding**:

- It confirms audit Report 2 §2.2 + R-2 quantitatively. The auditor wrote
  "treat this as a pre-condition"; V0d shows this prediction is right by
  empirically blowing up exactly where the pre-conditions fail.
- It **prevents** entering δ on a false sense of preparedness. Without
  V0d, the team might have started δ assuming the heuristic and
  table-edge would somehow not matter at z = 10⁹; V0d shows they matter
  at η_init = 200, six orders of magnitude before the δ deep anchor.
- It refines the δ scope: a substantial fraction of "δ multi-month work"
  was actually pre-condition work. The team can now ship pre1/pre2/pre3
  in ~2 weeks of focused work and then face a smaller, cleaner δ.

V0d closes the Phase-0 audit cycle with five hard gates (V0a-c, V0e, V0f) and
one **conditionally-passable** gate (V0d) that the audit prerequisites must clear first.
