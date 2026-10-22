# R191-A frozen targets (written before any proof compile of this packet)

Module: `lean/RotatingRestBundleGauss.lean`, namespace `R191ARotatingRestGauss`.
Imports (unchanged, compiled into `raw/imports/`): P03-A `VelocityJetDecomposition`
(and its imports `VelocityJetRest`, `PortCas01`). P05-A `OrbitCurvatureEigenframe` is not
imported (see `SOURCE_RECOVERY.md` §5: orbit curvature is not rest-bundle curvature).

Scope statement (binding): pointwise / chart level at a single event. Frame data
(`γ`, `dγ`) and gauge 2-jets (`O`, `l`, `ν`) are independent real arrays; no frame field,
Lie derivative or smooth-manifold API is modelled. Nothing below is labelled a general
field-level or global theorem. Card mapping: lean_steps (1)-(4), acceptance (A1) "two
independent derivations agree in ω² sign/order", (A2) "ω = 0 hypersurface branch
reduction", pitfall (P) "for ω ≠ 0 never call it an orthogonal metric or slice curvature".

Abbreviations: `M3 := Matrix (Fin 3) (Fin 3) ℝ`; `Γ := Fin 4 → Fin 4 → Fin 4 → ℝ`;
`DΓ := Fin 4 → Fin 4 → Fin 4 → Fin 4 → ℝ`; `R4 := DΓ`; `η := PortCas01.eta`,
`e0 := PortCas01.e0`.

## Definitions (lean_step 1)

* `curvForm A dA c C D := dA C D - dA D C + (A C * A D - A D * A C) - ∑ E, c E C D • A E`
  (curvature 2-form of the rest-bundle connection with FULL bracket).
* `sliceForm` — same with the sum over `E : Fin 3` of `c E.succ C D • A E.succ` only
  (vertical component dropped; contrast object, never called slice curvature).
* `Compat γ := ∀ A B C, γ A B C = -γ C B A`; `bracket γ E C D := etaF E * (γ E C D - γ E D C)`;
  `riem γ dγ A B C D := dγ C A D B - dγ D A C B + ∑ E, etaF E * (γ A C E * γ E D B - γ A D E * γ E C B) - ∑ E, bracket γ E C D * γ A E B`;
  `jet γ B C := γ C B 0`; `restA γ C i j := γ i.succ C j.succ`; `restDA dγ C D i j := dγ C i.succ D j.succ`;
  `restCurv := curvForm (restA γ) (restDA dγ) (bracket γ)`; `sliceCurv := sliceForm (...)`;
  `restV γ k l := jet γ k.succ l.succ`; `restOmega γ k l := (restV γ k l - restV γ l k)/2`.
* Chart (P03-A objects): `projRiemTrace hU R := ∑ m n k l, hU m k * (hU n l * R m n k l)`;
  `gaussSame g ginv u D R := projRiemTrace (hUp ginv u) R + metricInner (hUp ginv u) V V - contract (hUp ginv u) V ^ 2`
  (verbatim source `_proj_riemann_trace`, same-order); `gaussTrans` — with `metricInner (hUp ginv u) V Vᵀ`;
  `V := spatialJet g u D`; `gaussTensor g u D R a b c d := (∑ p q r s, h_a^p h_b^q h_c^r h_d^s R p q r s) - V c a * V d b + V d a * V c b`.
* Gauge 2-jet: `gaugeA O l A C := Oᵀ * A C * O + Oᵀ * l C`;
  `gaugeDA O l ν A dA C D := (l C)ᵀ * A D * O + Oᵀ * dA C D * O + Oᵀ * A D * l C + (l C)ᵀ * l D + Oᵀ * ν C D`
  (Leibniz expansion, `O = g(p)`, `l C = e_C g`, `ν C D = e_C e_D g`).

## Theorems

| id | name | exact statement (hypotheses → conclusion) | card item |
|---|---|---|---|
| T1 | `curvForm_eq_sliceForm_sub` | `∀ A dA c C D, curvForm A dA c C D = sliceForm A dA c C D - c 0 C D • A 0` | step 2 (exterior, ω term) |
| T2 | `bracket_vertical` | `Compat γ → ∀ k l : Fin 3, bracket γ 0 k.succ l.succ = 2 * restOmega γ k l` | step 1/2 (non-integrability = 2ω) |
| T3 | `restCurv_exterior` | `Compat γ → ∀ dγ k l, restCurv γ dγ k.succ l.succ = sliceCurv γ dγ k.succ l.succ - (2 * restOmega γ k l) • restA γ 0` | step 2 |
| T4 | `gauss_frame` | `Compat γ → ∀ dγ i j k l, restCurv γ dγ k.succ l.succ i j = riem γ dγ i.succ j.succ k.succ l.succ - restV γ k i * restV γ l j + restV γ l i * restV γ k j` | step 2/3 (exterior = tensor, 4-index) |
| T5 | `gaussTensor_frame` | `Compat γ → ∀ dγ i j k l, gaussTensor η e0 (jet γ) (riem γ dγ) i.succ j.succ k.succ l.succ = restCurv γ dγ k.succ l.succ i j` | canonical tensor theorem |
| T6 | `restScalar_gauss` | `Compat γ → restScalar γ dγ = projRiemFrame γ dγ - traceFrame (restV γ) ^ 2 + transFrame (restV γ)` | step 3 |
| T7 | `gaussSame_sub_gaussTrans` | `ginvᵀ = ginv → ∀ (g) u D R, gaussSame g ginv u D R - gaussTrans g ginv u D R = 2 * metricInner (hUp ginv u) (vorticity 1 g u D) (vorticity 1 g u D)` | step 3 (ordering = exactly 2 ω_ab ω^ab, any chart) |
| T8 | `exterior_eq_tensor` | `Compat γ → ∀ dγ, restScalar γ dγ = gaussTrans η η e0 (jet γ) (riem γ dγ)` | A1 |
| T9 | `exterior_eq_tensor_same` | `Compat γ → ∀ dγ, restScalar γ dγ = gaussSame η η e0 (jet γ) (riem γ dγ) - 2 * metricInner (hUp η e0) ω ω`, `ω := vorticity 1 η e0 (jet γ)` | A1 (ω² sign/order: coefficient −2 relative to same-order) |
| T10 | `curvForm_gauge` | `O * Oᵀ = 1 → (∀ C, (l C)ᵀ * O + Oᵀ * l C = 0) → (∀ C D, ν C D - ν D C = ∑ E, c E C D • l E) → ∀ C D, curvForm (gaugeA O l A) (gaugeDA O l ν A dA) c C D = Oᵀ * curvForm A dA c C D * O` | step 4 (invariant content) |
| T11 | `sliceForm_gauge` | same hypotheses → `sliceForm (gaugeA ..) (gaugeDA ..) c C D = Oᵀ * sliceForm A dA c C D * O + c 0 C D • (Oᵀ * l 0)` | step 4 (convention-dependent content), P |
| T12 | `gauss_scalars_transpose_jet` + `vorticity_transpose_jet` | `ginvᵀ = ginv → gaussSame g ginv u Dᵀ R = gaussSame g ginv u D R ∧ gaussTrans g ginv u Dᵀ R = gaussTrans g ginv u D R`; `vorticity c g u Dᵀ = -vorticity c g u D` | step 4 (index-order convention vs invariant) |
| T13 | `frobenius_pointwise` | `Compat γ → ((∀ k l : Fin 3, bracket γ 0 k.succ l.succ = 0) ↔ restOmega γ = 0)` | A2 |
| T14 | `omega_zero_rest_eq_slice` | `Compat γ → restOmega γ = 0 → ∀ dγ k l, restCurv γ dγ k.succ l.succ = sliceCurv γ dγ k.succ l.succ` | A2 |
| T15 | `omega_zero_scalar` | `Compat γ → restOmega γ = 0 → ∀ dγ, restScalar γ dγ = gaussSame η η e0 (jet γ) (riem γ dγ) ∧ restScalar γ dγ = gaussTrans η η e0 (jet γ) (riem γ dγ)` | A2 (standard `R_proj + K_abK^ab − K²`) |
| T16 | `gaussSame_eq_gaussTrans_of_vorticity_zero` | `ginvᵀ = ginv → vorticity 1 g u D = 0 → gaussSame g ginv u D R = gaussTrans g ginv u D R` | A2 (chart) |
| T17 | `sliceForm_gauge_of_vertical_zero` | T10 hypotheses → `c 0 C D = 0 → sliceForm (gauge..) c C D = Oᵀ * sliceForm A dA c C D * O` | A2 |
| N1 | `compat_γW`, `γW_nonintegrable` | `Compat γW`; `bracket γW 0 1 2 = 1 ∧ restOmega γW 0 1 = 1/2` | non-vacuity (ω ≠ 0 admissible) |
| N2 | `γW_rest_ne_slice` | `∀ dγ, (restCurv γW dγ (Fin.succ 0) (Fin.succ 1) - sliceCurv γW dγ (Fin.succ 0) (Fin.succ 1)) 0 1 = -1` | negative control, P |
| N3 | `γW_ordering_gap` | `∀ dγ, gaussSame η η e0 (jet γW) (riem γW dγ) - restScalar γW dγ = 1` | negative control (same-order ≠ canonical at ω ≠ 0) |
| N4 | `gauge_witness_hyps`, `slice_not_frame_invariant` | T10 hypotheses hold for `(1, lW, νW, cW)`; `sliceForm (gauge..) cW 1 2 ≠ 1ᵀ * sliceForm 0 0 cW 1 2 * 1 ∧ curvForm (gauge..) cW 1 2 = 1ᵀ * curvForm 0 0 cW 1 2 * 1` | non-vacuity of T10/T11 + negative control |

Helper lemmas (`ring_core`, `transpose_of_orth_jet`, `sum_gaugeA`, `hUp_symm`,
`metricInner_sym_add_skew`, `metricInner_same_sub_trans`, `Pi4` evaluation lemmas,
`vorticity_frame_apply`, `metricInner_omega_frame`, `same_sub_trans_frame`,
`spatialJet_transpose`, `metricInner_transpose_both`, `contract_transpose`,
`sameFrame_omega_γW`, `etaF_*`) are public and audited but are not card targets.

## Explicitly not targeted
* the identification `h^{mk}h^{nl}R_mnkl = 2 G_uu` (needs Riemann pair symmetries / field equations);
* existence of `u`-orthogonal hypersurfaces at `ω = 0` (real Frobenius theorem); only the pointwise
  algebraic condition (T13) is proved;
* tensoriality in the 2-form slots under a change of the direction frame (T10 is the fibre-gauge part);
* PR-191 maximal-class KE obstruction/existence classification (not part of R191-A);
* Wolfram/xAct, SymPy, Sage/Singular axes (card `tool_tasks`): not executed in this packet.
