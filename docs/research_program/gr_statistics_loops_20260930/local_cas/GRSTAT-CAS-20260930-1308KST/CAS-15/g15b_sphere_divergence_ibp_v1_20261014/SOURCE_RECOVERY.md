# G15-B source recovery

Paths are relative to `docs/research_program/gr_statistics_loops_20260930/`
unless they start with `HTT_` or `docs/`. Hashes are sha256 values taken in
this session.

## Inputs read

| input | sha256 | used for |
|---|---|---|
| `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (repo root) | 2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f | package |
| zip member `HTT_ALL_OBLIGATIONS_20261011/tasks/G15-B.json` | 7d889a282e2e84d6aa2d4fe8c7a08ed6b023cd77f2cbf1ba7f8bba73ea34a12b | card: scope, lean_steps 1–5, acceptance, pitfall |
| `cas/contracts/CAS-15.json` | eccc10a3f5105970a46a73412d8c82a27a1e82a6116013bc0abc6656816f8eee | C02 statement, target, uncontracted targets |
| `supplements/DOSSIER_POSITIVE_BRIDGE.md` | 00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd | (B1)–(B5) formulas |
| `cas/COMMON_SPEC.md` | 4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897 | conventions |
| `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/g15a_photon_energy_direction_v1_20261013/lean/G15APhoton.lean` | fc4d060643fc84a83beb729926df21b70480328dbf2eaab73bd5e31d541a7e39 | imported unchanged (reviewed PASS_SCOPED; REVIEW.md 349d7e92…) |
| `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/lean/Main.lean` | 7bf190fbfd8cfd1e863e48f1cee60d0ca36cbbb27c6e42ef7adf2a0bc6d672ef | inspected only; see "Reuse" below |

## Definition and statement bindings

**Card (G15-B.json).**

* `scope_original`: CAS15-C02 pointwise polynomial/divergence content
  together with the actual sphere integration by parts.
* `lean_steps[0..4]`:
  1. define the tangent gradient, divergence, measure and F tangency;
  2. derive the pointwise weights for eeᵀ, F·grad and We·grad;
  3. prove the closed-sphere divergence theorem or bind it to Mathlib;
  4. apply IBP to the matrix-valued componentwise integral;
  5. show degree ≤ 4 for the actual weak quadrupole.
* `pitfalls[0]`: no whole-sphere coordinate integration that hides pole
  singularities.
* `requires`: G15-A.

**Contract `cas/contracts/CAS-15.json`.**

* l.39 / l.113: C02, "Verify the pointwise sphere polynomial/divergence
  weights that yield the displayed weak quadrupole residual after an
  independently justified integration-by-parts step."
* l.93: canonical form "Spheregradient Pe∇ and divF=-2a·e-3sigma:ee". This
  binds `dS`, `gradS` (P_e∇) and `divS_Ffield_tracefree`.
* l.205: lean obligation "separate sphereIBP/transport proof".
* l.256: additional analytic obligation "Sphereintegration byparts".
* l.263: uncontracted target
  "WeakR=C2-T2-∫I{[4H-sigma:ee]eeT+a eT+e aT+(sigma e)eT+e(sigma e)T};
  onlyrank<=4". This binds `wB5`, `weak_residual_B5` and the G block.

**Dossier `supplements/DOSSIER_POSITIVE_BRIDGE.md`.**

* l.74–79 (B1): `a=A/c`, `H_u=θ/3`, `R(e)=H_u+a·e+σ:ee`,
  `F(e)=P_e(a+σe)`, `P_e=I−eeᵀ`. These bind `Rrate3`, `Ffield` and `Pt`.
* l.94–97 (B2): `𝒟I + [−F+We]·∇_{S²}I + 4RI = 𝒞`. This is used only as the
  explicit hypothesis `hB2` of `weak_quadrupole_commutator`.
* l.105–110 (B3): `r = 𝒞 − 𝒟I + F·∇I − 4RI`, `M = ∫ I eeᵀ dΩ`,
  `R = ∫ r eeᵀ dΩ`. These bind `Mmom` and the integrands of
  `weak_residual_B5`.
* l.118–122 (B4 proof): "We has zero sphere divergence … R = −∫ I[(We)eᵀ +
  e(We)ᵀ] = MW − WM". This binds `divS_skew` and `commutator_moments`, with
  `Wm W i j = (W b_j)_i` and `(WM)_ij = Σ_k W_ik M_kj`.
* l.138–149 (B5): `C2 = ∫ 𝒞 eeᵀ`, `T2 = ∫ (𝒟I) eeᵀ`, the boxed (B5), the
  angular term `−∫ I[(div F)eeᵀ + F eᵀ + e Fᵀ]`, and "Only brightness
  moments through rank four … are needed". These bind `angular_B5`,
  `weak_residual_B5` and `B5_rank_le_four_moments`.

**COMMON_SPEC.**

* l.10–11: W_ij = ε_ijk ω_k, so W is skew. In 3D rest components
  `IsSkew W` is used for a general skew W.
* l.17: e·u = 0 and e·e = 1. Directions therefore lie on the unit sphere of
  the rest space, which is `S2`.
* l.28: I and its derivative and collision inputs are independent supplied
  quantities. Hence `Cc` and `DI` are arbitrary functions with only the
  integrability that the integrals need.

**G15-A (`G15APhoton.lean`).**

* l.18 `V`, l.21 `mink`, l.46 `accel`, l.49 `Rrate`, l.53 `Fcov`. These are
  bound to the 3D objects by `bridge_Fcov` and `bridge_Rrate`. The rest frame
  is U = (c,0,0,0) and the spatial embedding is `emb3`.

## Recovered conventions and notes

1. σ in the source is the shear, which is symmetric and trace-free.
   `divS_Ffield` shows that the general formula carries a `+tr σ` term. The
   dossier's l.139 formula (`div F = −2a·e − 3σ:ee`) therefore needs
   trace-freeness, and only that is assumed (`trL σ = 0`). Symmetry is never
   used.
2. Dossier l.149 says "Combining with −4𝓡M". R depends on e, so the
   correct term is `−4 ∫ R(e) I(e) eeᵀ dΩ`. That is what is formalized.
   Proving (B5) with it confirms the boxed result; "−4𝓡M" is shorthand.
3. dΩ is modelled by any finite μ invariant under linear isometries. The
   instance used is `σS = volume.toSphere`, with total mass 4π; that mass is
   not formalized. All identities are linear in μ.
4. The sign of W follows the source exactly: the angular derivative term in
   (B2) is `(We)·∇I`, and `Wm`/`[M,W]` are read with `(We)_i = Σ_k W_ik e_k`.

## Reuse

* G15-A is reused by importing `G15APhoton` unchanged. The source sha256
  fc4d0606… matches the RETURN.json of G15-A. It was recompiled into
  `raw/imports/G15APhoton.olean`, sha256
  0c15d3c24f761c3400d9cc1a392a7425c2bdea146a67863eadccc58d0233fa04. That is
  byte-identical to the reviewed G15-A olean, as stated in G15-A REVIEW.md
  row 4.
* `CAS-15/lean/Main.lean` (sha 7bf190fb…) contains only
  `grstat_cas15_commutator_entry` (`mi*wij − wij*mj = (mi−mj)*wij`). Its own
  `result.json` records `CAS-15-C02: false`. It has no C02 polynomial or
  divergence content to import, so nothing from it is imported. Its one
  identity is subsumed by the ring step inside `commutator_moments`.
* No other existing Lean source covers sphere IBP. The search covered
  CAS-15 subfolders `c03_*`, `c04_*`, `ls_projection_continuation_*`,
  `spectral_wrapper_*` and `g15a_*`, and `git log` for the CAS-15 path, whose
  latest relevant commit is f3493a65 (G15-A).

## Mathlib identities relied on (verified in the pinned Mathlib fabf563a…)

`MeasureTheory.Measure.toSphere`, `Measure.toSphere_apply'`,
`Measure.toSphere_ne_zero`, `LinearIsometryEquiv.measurePreserving`,
`MeasurePreserving.measure_preimage_emb`, `MeasurePreserving.integral_comp`,
`NormedSpace.exp_mem_unitary_of_mem_skewAdjoint`,
`Unitary.linearIsometryEquiv`, `hasDerivAt_exp_smul_const`,
`hasDerivAt_integral_of_dominated_loc_of_deriv_le`,
`IsCompact.exists_bound_of_continuousOn`, `ContDiff.continuous_fderiv`,
`ContinuousLinearMap.eq_adjoint_iff`, `ContinuousLinearMap.instCompleteSpace`,
`MvPolynomial.eval_eq'`, `MvPolynomial.le_totalDegree`,
`MvPolynomial.totalDegree_{add,sub,mul,C,X,finsetSum}`. The API probes are
in `raw/probes/probe0{1,2,3}_*.lean`.

## Missing items

None blocking. These are not formalized and are not claimed:

* the existence of a C¹ ambient extension of a C¹ function on S²;
* the identification of `toSphere` with the Hausdorff surface measure;
* (B2) itself.
