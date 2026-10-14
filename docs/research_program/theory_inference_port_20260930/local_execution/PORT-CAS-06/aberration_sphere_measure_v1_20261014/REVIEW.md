# P06-A — independent review (verbatim final report of a fresh read-only reviewer)

## P06-A additive closeout review: aberration on the S² surface measure (`aberration_sphere_measure_v1_20261014`)

**Verdict: PASS_WITH_NOTES.** There are no blocking findings. Together with the prior reviewed unit (`endpoint_optical_invariants_v1_20261014`, PASS_WITH_NOTES), card lean_steps 1-4 and both acceptance items are now met at proof level. lean_step 2 is now proved on Mathlib's actual sphere measure, not in a chart. Scientific admission stays **HOLD**.

- **Reviewer:** Claude Opus 5.5 (model id `claude-opus-5-5`). I am a fresh, read-only reviewer and did not author this unit. I did not edit any repository file, ran no state-changing git command and spawned no subagents.
- **Scratch location:** everything I wrote is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p06-a_rerun/sphere/`. I used this new subfolder so nothing mixes with the earlier review's files.
- **T** = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-06/aberration_sphere_measure_v1_20261014`

### Per-check table

| # | Check | Status | Evidence |
|---|---|---|---|
| 0 | Card identity | PASS | The card member hashes to `debd1cd7…0b15` and the zip to `2d0b6da9…af6f`. Both match SOURCE_RECOVERY. Card: lean_step 2 = "aberration의 sphere Jacobian과 source area/observer solid-angle 정의를 연결한다"; tool_tasks.lean = "실제 측도·미분 연결까지". |
| 1a | SOURCE_RECOVERY citations | PASS | Prior REVIEW.md is `7b22b410…5ca31` and ADDENDUM is `89b6942b…047ad`; ADDENDUM lines 3-6 say what is claimed. G15BSphere.lean is `d08907e9…6c8b6`, with line 40 `σS := (volume).toSphere` and line 289 `σS_rotInv`. All Mathlib file:line references at fabf563a resolve to the named declarations: HaarToSphere 52/76/107/117/143, Jacobian 1187, Lebesgue 590, Calculus 197, RadialEquiv 67. All 17 cited P06AOptics line numbers point to the named definitions or theorems. EndpointScalarInvariant lines 5-9 are `zNew`, `dANew`, `endpoint_product_invariant`. |
| 1b | Frozen targets written before the first compile | PASS (mtime only) | FROZEN_TARGETS.md has mtime 02:54:23Z and sha `fb45b2b3…` (unchanged). The first receipt (`compile_01`) started at 02:54:40Z and the first main compile (`compile_07`) at 03:04:04Z. The "02:55Z" stamp inside the document is later than the first receipt; the amendment says so and calls it a rounding slip. The directory is untracked in git, so the order rests on mtimes alone, with no cryptographic anchor. |
| 1c | Final statements vs frozen statements | PASS | My own exact parser compares each declaration up to `:=`, whitespace-normalised and as full equality, not as a substring. 23 of 25 frozen declarations are EXACT. The other two (F8, F9) are EXACT after the A1 substitution and differ in nothing else. |
| 1d | Amendment A1 changes elaboration only | PASS | I compiled the frozen F8 text verbatim (`src/FrozenF8Probe.lean`). It fails with exit 1 and the same errors as the author's receipt: `n : E3` is passed where `↑S2` is expected, and the `FunLike (Measure ↑S2) (Set E3)` instance cannot be synthesised. So the frozen text is ill-typed. `∀ᵐ (n : S2) ∂σS` is its only well-typed reading. Hypotheses, quantifiers, measure and conclusions are unchanged. |
| 1e | σS is Mathlib's sphere measure | PASS | `example : σS = (volume : Measure (EuclideanSpace ℝ (Fin 3))).toSphere := rfl` compiles. I also proved `σS univ = ofReal (4π)` from `toSphere_apply_univ` and `volume_ball_fin_three`. So σS is the true surface measure, not a normalised probability. |
| 1f | `aberrS` has exactly `P06AOptics.aberr`'s components | PASS | `(aberrS hb n : E3) i = aberr b1 b2 b3 (n 0) (n 1) (n 2) i` holds by `fin_cases i <;> rfl`, and `dopS = doppler` holds by `rfl`. F1 (`aberrS_same_ray`) proves that `aberrS n` is the new-tetrad direction `dirOf (newComp …)` of the same null `k = E(1,−n)`. That fixes the same-ray reading. |
| 1g | The pushforward identity F4 is genuinely proved | PASS | `key_identity` runs exactly the stated route with no shortcut. (i) `coneDeriv` is proved to be the Fréchet derivative of `coneMap` on `{0}ᶜ`; it is not postulated. (ii) `det = D(x̂)` is computed with `Matrix.det_fin_three`. (iii) Mathlib's change of variables `lintegral_image_eq_lintegral_abs_det_fderiv_mul` is applied, with `InjOn` and image `{0}ᶜ` proved from the explicit inverse `coneMap(−β)`. (iv) The polar decomposition `measurePreserving_homeomorphUnitSphereProd` is used. (v) The radial measure `volumeIoiPow_apply_Iio` gives `D⁻³/3`. (vi) `lintegral_prod` splits the integral and the common factor 1/3 cancels. F4 then follows from `map_apply` and `withDensity_apply`. Nothing is circular: F4 depends only on `key_identity`. |
| 1h | det and radial integral checked by hand and with sympy | PASS | `sympy_check.out`: the symbolic Jacobian of `coneMap` equals `coneDeriv`, and `det J − D(x̂)` simplifies to 0. Over 200 random numeric points, max \|det J − D(x̂)\| = 3.6e-15. `∫₀^{1/D} r² dr = 1/(3D³)`, which times D gives `1/(3D²)`. `coneMap(r n) − r D(n) aberr(n) = 0`, `h·s = γ−1`, and \|aberr\|² = 1. By hand: `det(I + b ℓᵀ) = 1 + ℓ·b = 1 + γ β·x̂ + h s = γ(1+β·x̂)`. |
| 1i | F6: new solid angle for every measurable set | PASS | `solidAngleNew := comap aberrS σS`, which `rfl` confirms. The theorem gives `solidAngleNew = σS.withDensity D⁻²` and, for every measurable A, `σS(aberrS '' A) = ∫_A D⁻² dσS`. I instantiated it at A = univ: with surjectivity this gives `∫ D⁻² dσS = σS univ` (= 4π). The physics is correct: forward directions (D>1) are compressed, matching T5 `dΩ̃ = D⁻² dΩ`. |
| 1j | F7: area distance with the same source area | PASS | The statement is `∀ᵐ n ∂σS, areaDist dS (rnDeriv(solidAngleNew, σS)(n)·dΩ) = D·areaDist dS dΩ`. It uses the same `dS` on both sides, and the Radon–Nikodym density comes from the actual measures through `rnDeriv_withDensity`. It holds for all real dS and dΩ (sqrt of a negative argument is 0 on both sides). It is an a.e. statement, which is the right form because Mathlib's `rnDeriv` is defined only a.e. It is not vacuous, since `σS ≠ 0` (F10). |
| 1k | F8: composite without β ≠ 0; F9: β = 0 corollary | PASS | F8 has only the hypotheses `hb : s<1` and `0<E`; the prior unit's `0 < s` is gone. F9 states that `aberrS` is the identity, that `solidAngleNew = σS`, and that the composite holds at β=0. This closes the prior unit's addendum item on the β = 0 corollary. The z=0 boundary follows because Es is free; the prior unit also has `boundary_z_zero`. |
| 1l | Negative control is genuine | PASS | `pushforward_without_density_ne`: at β=(0,0,3/5), the pushforward of σS without the density is not σS. The proof is not trivial. It shows equality would force `withDensity D⁻² = σS`. On the open set U = {D > 3/2}, which contains the pole and so has positive measure, the density is below 4/9, a contradiction. Monte Carlo agrees: the density-free pullback measure differs from σS(A) by up to a factor of 30 (table below). |
| 1m | Card lean_step 4 on the sphere measure | PASS (note) | This unit adds no dL statement. In `src/SphereComposeCheck.lean` I proved `lum_sphere`: with explicit reciprocity hypotheses in each frame, `∀ᵐ n ∂σS, dL' n = dL n / D(n)`, with no β ≠ 0 hypothesis. It uses only F8 and the prior unit's `luminosity_from_reciprocity`. Exit 0; axioms {propext, Classical.choice, Quot.sound}. So lean_step 4 composes with the new measure. |
| 2 | No hypothesis assumes its conclusion; no vacuity | PASS | The only hypotheses are `s<1`, `0<E`, continuity of g in F5, and measurability of A in F6. I instantiated F4 at β = 0, (0,0,3/5) (author), (1/5,−3/10,1/2) and (−9/10,0,0), and F8 at a non-axial β. `σS ≠ 0` rules out vacuous a.e. statements. |
| 3a | Hash integrity and exit codes | PASS | For all 10 receipts, the recomputed hashes of source, stdout and stderr match. Each source path still has its recorded hash, except `compile_07` and `compile_08`, whose path was overwritten by later attempts; their `.source.lean` copies are kept and match. Exit codes: 01-04 = 0; 05 = 1 (failed API probe, kept); 06 = 0; 07 = 1 (failed main compile, kept); 08-10 = 0. `lean/P06ASphere.lean` is `0f32e6b0…` and equals the `compile_09` source. The olean is `69429409…`. The import oleans are byte-identical to the prior unit's `raw/imports`. P06AOptics source is `732fbbfd…`, unchanged and equal to the prior RETURN.json. |
| 3b | Forbidden constructs | PASS | `grep -nE 'sorry\|admit\|native_decide\|axiom\|set_option\|sorryAx\|maxHeartbeats\|unsafe\|implemented_by\|extern\|opaque\|macro\|elab\|run_cmd\|#eval' T/lean/P06ASphere.lean` returns rc=1 (no match). |
| 3c | Axioms | PASS | The author's `compile_10` lists 66 declarations, all within {propext, Classical.choice, Quot.sound}. My own audit does not use a hand-written list. A meta command enumerates every non-internal constant in namespace `P06ASphere` and calls `collectAxioms` on each, so it also covers the `eq_1` and `congr_simp` auxiliaries and the `E3`/`S2` abbrevs. Result: `AUDIT_TOTAL 77 BAD 0`. |
| 4 | Independent recompile | PASS | I copied the 5 sources (hashes equal the receipts) to `sphere/src`. From `/home/cosmosapjw/lean_oracles/viii_oracle` (`lean-toolchain` v4.31.0, manifest mathlib `fabf563a…`) I ran `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/<M>.olean $S/src/<M>.lean"` for PortCas01, PassiveTensorBridge, EndpointScalarInvariant, P06AOptics and P06ASphere. All exit 0. The only output is one deprecation warning (`ContinuousLinearMap.smul_apply`, line 245). My P06ASphere, PortCas01 and PassiveTensorBridge oleans are byte-identical to the author's. EndpointScalarInvariant and P06AOptics differ only by the embedded path, as the prior review explained. The audit file `src/SphereReviewAudit.lean` exits 0. |
| 5 | Monte Carlo of the pushforward identity | PASS | `python3 -I mc_sphere.py` (seed 20261014, N = 4e6 uniform directions) checks 5 β values × 5 caps; details below. |

Monte Carlo setup:
- β values: 0, 0.6ẑ, (0.2,−0.3,0.5), −0.9x̂, (0.5,0.5,0.5).
- Caps: ±ẑ with half-angle 0.5, an equatorial cap with half-angle 1.0, −x̂ with 0.3, and an oblique cap with 1.3.
- The closed-form aberration was cross-checked against an independently coded Lorentz boost of `k=(1,−n)`: directions and D agree to below 1e-12.

Monte Carlo results:

| Quantity | Result |
|---|---|
| `∫_{aberr⁻¹A} D⁻² dσ` vs exact `2π(1−cos α)` | max relative error 6.7e-3; max deviation 2.79 standard errors across 25 tests (consistent with noise) |
| Density-free control `σS(aberr⁻¹A)`, e.g. β=−0.9x̂, cap −x̂ | 3.805 vs 0.281 (clearly not σS) |
| F6 forward form `σS(aberr A)` vs `∫_A D⁻²` | 2.6537 vs 2.6569 (within noise) |
| Inverse map with −β | max error 1.3e-15 |
| `∫ D⁻² dσ / 4π` | 1.000 ± 9e-4 for all five β values |

### Card coverage, together with the prior unit

| Card item | Status | Where it is met |
|---|---|---|
| lean_step 1 (null tangent, measured energies, Doppler convention) | met | prior unit, PASS |
| lean_step 2 (sphere Jacobian connected to source area and observer solid angle on the actual measure) | now met | F3, F4, F5, F6, F7 against `Measure.toSphere`; F1 fixes the same ray. No chart, no rotation reduction, no `dΩ = dμ dφ` convention. |
| lean_step 3 (`(1+z′)dA′ = (1+z)dA`) | met | prior unit, plus F8 on the sphere measure for every β |
| lean_step 4 (explicit reciprocity, `dL′ = dL/D`, scalar inverse-T affine law) | met | prior unit, under hypotheses; composes with the sphere measure (my `lum_sphere`) |
| Acceptance 1 (same ray, remapped direction fixed by definition) | met | F1, plus the prior unit's `newDir_formula` and `same_ray_components` |
| Acceptance 2 (results hold at z=0 and β=0) | met | F9 states the β=0 composite; z=0 is covered because Es is free and by `boundary_z_zero` |
| Pitfall: distinct rays | respected | no distinct-ray comparison is made |
| Pitfall: polarization / spin-2 | respected | no spin-2 or polarization object exists |

### Blocking findings

None.

### Non-blocking notes

1. **Freeze evidence is mtime only.** The 17 s gap between freeze and the first receipt, and the unit's untracked status in git, mean there is no cryptographic anchor. The in-document "02:55Z" stamp is later than the first receipt; this is disclosed in the amendment. Committing the unit, or recording the hash in a tracked ledger, would anchor it.
2. **A1 is legitimate but must stay recorded.** F8 and F9 differ from the frozen text by the binder annotation only. I independently confirmed that the frozen text does not typecheck.
3. **F7 and F8 are σS-a.e. statements.** This is the correct form for a Radon–Nikodym density. F6 holds for every measurable set. A pointwise version through a continuous representative of the density is not stated.
4. **Optional corollary for lean_step 4.** Its sphere-measure form exists only as my scratch `lum_sphere`. If the controller wants lean_step 4 recorded at sphere-measure level as an owned theorem, the smallest fix is an additive corollary with that exact statement.
5. **Card tool_tasks have no author receipts.** wolfram_xact, sympy and sage_singular were not run by the author. My sympy check covers the Jacobian determinant, the cone lift and the radial integral as reviewer evidence only.
6. **Cosmetic.** There is one deprecation warning (line 245). Mathlib line references in SOURCE_RECOVERY are correct as of fabf563a.
7. **Runtime not attested.** The author's observed runtime and model are UNKNOWN. The interrupted-run claim ("no files reused") cannot be verified.

### Not proved / not claimed (carry forward)

- Scientific admission: **HOLD**.
- `dΩ = dμ dφ` (Archimedes) for `toSphere`. It is not needed by this route.
- Pointwise (every-direction) versions of F7 and F8.
- Derivation of reciprocity or transparency. They are hypotheses, and no dL theorem is owned by this unit.
- Derivation of Planck occupation invariance (hypothesis only).
- Polarization, spin-2, or frequency-dependent intensity transfer.
- Distinct-ray comparison (negative control only).
- Curved-spacetime propagation, source motion, real data.
- The card's wolfram, sympy and sage tool tasks, as author receipts.
- Publication state and full PORT-CAS-06 / four-axis acceptance.

### Proposed VALIDATION_MATRIX scientific row (I did not edit it)

`P06-A (closeout) | aberration on S² surface measure (Measure.toSphere), same ray | PASS_WITH_NOTES (independent review, claude-opus-5-5) | F1-F10 proved; 77/77 constants axioms ⊆ {propext, Classical.choice, Quot.sound}; independent recompile exit 0 (P06ASphere olean byte-identical); statements = frozen (23 exact, 2 exact after A1 binder fix, frozen text shown ill-typed); sympy det(coneDeriv)=D(x̂), radial D⁻³/3; MC 25 β×cap cases ≤2.8σ, density-free control fails as expected | lean_steps 1-4 + acceptance 1-2 met with prior unit; F7/F8 σS-a.e.; reciprocity/occupation hypotheses; scalar only; freeze evidence mtime-only | scientific_admission HOLD`

### Files

- **Card:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (member `HTT_ALL_OBLIGATIONS_20261011/tasks/P06-A.json`)
- **Reviewed:** `T/lean/P06ASphere.lean`, `T/FROZEN_TARGETS.md`, `T/FROZEN_TARGETS_AMENDMENT.md`, `T/SOURCE_RECOVERY.md`, `T/AUTHOR_RETURN.json`, `T/raw/compile_01..10_*`, `T/raw/AxiomAudit.lean`, `T/raw/probes/compare_*.py`
- **Prior unit:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_optical_invariants_v1_20261014/` (`REVIEW.md`, `ADDENDUM_20261014.md`, `lean/P06AOptics.lean`)
- **Reviewer scratch,** in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p06-a_rerun/sphere/`:
  - `src/SphereReviewAudit.lean`, with output in `review_audit.out`
  - `src/FrozenF8Probe.lean`, with output in `frozenF8_probe.out`
  - `src/SphereComposeCheck.lean`, with output in `compose_check.out`
  - `sympy_check.py` and `sympy_check.out`
  - `mc_sphere.py` and `mc_sphere.out`
  - `rerun_*.out` and `imports/*.olean`
