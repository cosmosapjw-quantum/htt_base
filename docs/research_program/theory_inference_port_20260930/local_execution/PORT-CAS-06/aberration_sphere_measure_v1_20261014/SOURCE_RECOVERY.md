# P06-A additive closeout — source recovery (aberration on the S² surface measure)

All repository paths are relative to `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
Read-only; no source outside this unit was edited.  No state-changing git command
was run.

## Card and open item

| Item | Source | Evidence |
|---|---|---|
| Card | `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member `HTT_ALL_OBLIGATIONS_20261011/tasks/P06-A.json` | member sha256 `debd1cd7672d84df5b888cb9e0e86fddfb1f78bfe50059083af6435db25b0b15`; zip sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f` |
| lean_step 2 | card `lean_steps[1]`: "aberration의 sphere Jacobian과 source area/observer solid-angle 정의를 연결한다" | target of this unit |
| acceptance 2 | card `acceptance[1]`: "z=0·β=0 등 경계에서 결과 유지" | F9 (β = 0 composite stated as a corollary) |
| tool_tasks.lean | "energy/area/solid-angle 정의에서 실제 측도·미분 연결까지 formalize" | F3 (derivative), F4–F7 (actual measure) |
| Open item | `docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_optical_invariants_v1_20261014/REVIEW.md` (sha256 `7b22b410…5ca31`), "Card lean_step 2" section and non-blocking note 1 | "Unlock: a new frozen target that states the pushforward of the S² surface measure under `aberr` has density D⁻², via `Measure.toSphere`" |
| Open item (controller) | same dir, `ADDENDUM_20261014.md` (sha256 `89b6942b…047ad`), lines 3-6 | "Not counted toward package progress until an additive unit proves the pushforward of the sphere measure under the aberration map has density D^-2"; "The beta = 0 composite … not stated as a corollary" |
| Physics source of `dΩ'=D⁻²dΩ`, `d_A'=D d_A` | cited by the prior unit's `SOURCE_RECOVERY.md`: T5 pack `inherited/tilt_boost_loop_20260930/inherited/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md:63-67`; `observations_findings.md:27` | reused unchanged through the reviewed definitions below |

## Reused reviewed definitions (imported UNCHANGED from P06AOptics)

`lean/P06AOptics.lean` of the prior unit, sha256
`732fbbfddfae5347cd2cf94a5137c02b0baaf7c2594e19ee161be7cb8a4890ab` (equal to the
sha recorded in its `RETURN.json` and to `raw/compile_04_imp_optics.json` here).

| Object | P06AOptics line | Use here |
|---|---|---|
| `photon E n = E(1,-n)`, `n` sourceward | 47 | F1, F8 |
| `energy u k = -g(k,u)` | 50 | F8 |
| `doppler b n = γ(1+β·n)` | 53-54 | `dopS` (F3–F10) |
| `newComp`, `dirOf` (same fixed null `k`, new tetrad) | 65, 68 | F1 |
| `aberr b n i` (closed-form aberration) | 72-75 | `aberrV`, `aberrS` |
| `areaDist dS dΩ = √(dS/dΩ)` (same source area `dS`) | 84 | F7, F8 |
| `redshiftOf Es E = Es/E - 1` | 88 | F8, F9 |
| `core` (γ>0, γ²(1-s)=1, h s = γ-1) | 95 | algebra |
| `gamma_neg`, `h_neg`, `s_neg` | 113-120 | inverse boost |
| `doppler_pos` | 168 | D>0 |
| `energy_new`, `energy_old` | 159-166 | F8 |
| `newDir_formula` | 238 | F1 |
| `aberr_unit` | 263 | `aberrV_mem_sphere` |
| `redshift_endpoint` | 537 | F8 |
| `boundary_beta_zero` | 755 | F9 |
| `nonvacuity_witness` (`doppler 0 0 (3/5) 0 0 1 = 2`) | 790 | F10 |

Transitively imported unchanged (sources compiled from their original paths; the
resulting oleans are byte-identical to the prior unit's `raw/imports`):

| Module | Source sha256 | Olean sha256 (here = prior unit) |
|---|---|---|
| `PortCas01` (`PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean`; `s`, `gamma`, `h` at lines 10-12, `fourVelocity` 119) | `e289039f…a0c7b` | `a83adac8…0bc8` |
| `PassiveTensorBridge` (GR-17 CAS17C04) | `49f37140…a8fb` | `7bf257e3…77e0` |
| `EndpointScalarInvariant` (`zNew` 5, `dANew` 6, `endpoint_product_invariant` 9) | `6e2ba677…aed83` | `e25af015…6640` |
| `P06AOptics` | `732fbbfd…90ab` | `01b11d0d…690b` |

## Sphere measure and calculus (Mathlib fabf563a, Lean 4.31.0)

Toolchain from `/home/cosmosapjw/lean_oracles/viii_oracle/lean-toolchain`
(`leanprover/lean4:v4.31.0`) and `lake-manifest.json` (mathlib rev
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`).  Paths below are under
`.lake/packages/mathlib/`.

| Item | File:line |
|---|---|
| `Measure.toSphere` (σS) | `Mathlib/MeasureTheory/Constructions/HaarToSphere.lean:52` |
| `volumeIoiPow_apply_Iio` (radial `r² dr`) | same file `:117` |
| `measurePreserving_homeomorphUnitSphereProd` (polar decomposition) | same file `:143` |
| `toSphere.instIsOpenPosMeasure`, `IsFiniteMeasure` instance | same file `:76`, `:107` |
| `lintegral_image_eq_lintegral_abs_det_fderiv_mul` (change of variables) | `Mathlib/MeasureTheory/Function/Jacobian.lean:1187` |
| `Measure.rnDeriv_withDensity` | `Mathlib/MeasureTheory/Measure/Decomposition/Lebesgue.lean:590` |
| `hasStrictFDerivAt_norm_sq` | `Mathlib/Analysis/InnerProductSpace/Calculus.lean:197` |
| `homeomorphUnitSphereProd` (`x ↦ (x/‖x‖, ‖x‖)`) | `Mathlib/Analysis/Normed/Module/Ball/RadialEquiv.lean:67` |

`σS := (volume : Measure E3).toSphere` is the same expression as the reviewed G15-B
`σS` (`gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/g15b_sphere_divergence_ibp_v1_20261014/lean/G15BSphere.lean:40`,
sha256 `d08907e9…6c8b6`).  G15BSphere was read but NOT imported: its rotation
invariance (`σS_rotInv`, line 289) is not needed by the light-cone route, and that
unit is recorded as evidence-limited / not counted (its `ADDENDUM_20261014.md`).

## Items not recoverable / not used

* `dΩ = dμ dφ` (Archimedes) for `toSphere`: not needed by this route and not proved;
  the task allowed proving it "if needed".
* No source supplies a derivation of reciprocity/transparency or Planck occupation
  invariance; untouched here (prior unit hypotheses).
* The card's wolfram_xact / sympy / sage_singular tool tasks: no receipts produced
  in this unit.
