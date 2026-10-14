# G11-C source recovery (GR-CAS-11, TEFF-A2)

Written 2026-10-14 before `FROZEN_TARGETS.md`. Paths are relative to the
repository root unless absolute. `S` = `docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_POSITIVE_BRIDGE.md`
(sha256 `f04d96fe4b7dbee5fc946e10863d602c46399ca15723226ce6b63d4ab53ff21b`, matches the
`research_provenance_hashes` entry of the CAS-11 contract). `C` =
`docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-11.json`
(sha256 `6588ac42ca6724e58b2f673b0ee2c3234b7a3a6ab1df35a6d1f942c03f860025`).
Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip:HTT_ALL_OBLIGATIONS_20261011/tasks/G11-C.json`
(source_snapshot `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`).

## 1. Recovered definitions and statements

| Item | Source (file:line, gist) | Lean (this unit) |
|---|---|---|
| measure dν = C E² dE dΩ at one event/observer | S:37-39 | `G11A.nu C` (reused, G11-A) and an arbitrary measure `μ` |
| δ = f − g, D_H(f‖g) ≤ ε < ∞ | S:41-44 (A1) | `Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε`, `0 ≤ ε` (same form as reviewed G11-B) |
| exact retained moments ∫ φ_a δ dν = 0, a = 1..m; V = span{φ_a} | S:44 (A1), S:45 | `hmatch : ∀ a, ∫ x, φ a x * (f x - g x) ∂μ = 0`, `φ : Fin m → X → ℝ` (m arbitrary, m = 0 allowed); `retainedSpan` = span of the L²(W) classes |
| positive measurable W, sup_{z between f,g} z(1+ξz) ≤ W a.e. | S:46-51 (A2) | `G11A.WEnvelope μ s W f g` (reused unchanged) |
| kernels K_j and retained scores in L²(W dν); observable integrals finite | S:53 | `hK : ∀ j, MemLp (K j) 2 (wmeas μ W)`, `hφ : ∀ a, MemLp (φ a) 2 (wmeas μ W)`, `wmeas μ W = μ.withDensity (ofReal ∘ W)`; finiteness of ∫ K_j δ dν is DERIVED (Hölder in L²(W)), not assumed |
| (A3) \|∫K(f−g)dν\| ≤ √(2ε) dist_{L²(Wdν)}(K,V) | S:55-58 | `single_kernel_dist_bound` with `Metric.infDist` in `Lp ℝ 2 (wmeas μ W)` |
| r_j = K_j − P_V K_j, R_ij = ∫ W r_i r_j dν, e_j = ∫ K_j (f−g) dν | S:61-66 | `residuals`, `gramR = Matrix.gram ℝ residuals`, `gramR_eq_integral`, `evec` |
| (A4) e ∈ range(R), eᵀR†e ≤ 2ε; R† Moore–Penrose; singular R allowed | S:68-74 | `weighted_residual_ellipsoid`; R† = accepted C02 `CAS11C02.spectralPinvMatrix`; supplementary Penrose identities |
| proof: ∫ δ²/W ≤ 2ε (G11-B); matching removes v ∈ V; weighted CS; all-a bound; null vectors annihilate e; a = R†e | S:76-87 | T1-T5 below; finite step delegated to the accepted C02 theorem |
| \|aᵀe\| ≤ √(2ε aᵀRa) for every a | S:85 | `cauchy_all_a` (both squared and square-root forms) |
| (A6) uncertain matching: \|ΔO_K\| ≤ √(2ε)‖K − a·φ‖_W + \|a·Δm\| | S:106-114 | `mismatch_bound` (ENT-MISMATCH) |
| singular loci ENT-R0 all-retained → e = 0; ENT-SINGULAR duplicate kernels impose range; ENT-MISMATCH; ENT-DOMAIN | C:73-77, C:92-96, C:108-112 | `all_retained`, `gramR_zero_imp_evec_zero`, `duplicated_kernels`, `negative_control_mismatch`; ENT-DOMAIN inherited from G11-B guards (`f ∈ cdom`, `g ∈ dom`, W > 0) |
| exclusion "Gram not noise covariance" | C:68-69; card pitfalls | R is only the Gram matrix of residuals in L²(W); no covariance reading anywhere |
| uncontracted research targets "rj=Kj-PV Kj; Rij=<ri,rj>W; all a ...", "e in range R ... even singular R" | C:250-255 | this unit |
| "Hilbert projection and weighted Cauchy" as an additional analytic obligation | C:245-248 | T2-T4 (genuine infinite-dimensional L²(W dν), not a finite surrogate) |

## 2. Reused accepted Lean sources (imported unchanged; recompiled from their original paths into `raw/imports`)

| Module | Path | sha256 | Status record |
|---|---|---|---|
| `BregmanThreePoint` | `.../CAS-11/c01_bregman_three_point_v2_20261008/lean/BregmanThreePoint.lean` | `12f3dd682db93f0966fd3547f10f25eb4fca9e8506ff58fc7c1ba6ac7cf9975c` | C01 v2 CAS_4AXIS_PASS (dependency of G11-A) |
| `G11AIntegralBregman` | `.../CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AIntegralBregman.lean` | `85993ce761d3d5546e362ec3debd765617da1cfb542675c6da2aea3e85b11e9a` | G11-A FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES |
| `G11AGuarded` | `.../g11a_integral_bregman_v1_20261013/lean/G11AGuarded.lean` | `92758d9a0be6ba596461eddb322dd49f397d067ca52b5fe8e656aded10752b77` | idem (domain-guarded `_stat` wrappers) |
| `G11BHessianEnvelope` | `.../CAS-11/g11b_hessian_envelope_energy_v1_20261013/lean/G11BHessianEnvelope.lean` | `ba1bc644a2b13ac82fff23b5c66645efa596ef72f6e132da2fd76a018be68f27` | G11-B FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES |
| `FiniteGram` (namespace `CAS11C02`) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C02-20260930T090559Z/lean/FiniteGram.lean` | `af91ec609dbd79746f148e67c40cbe39eb0405ea390432b44eb1102918468ffc` | CAS11-C02 CAS_4AXIS_PASS, Astra review PASS (`completion/RESULT.md`, `completion/REVIEW.md`) |
| `WeightedProjection` (namespace `CAS11C03`) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS11-C03-20261001T020800Z/lean/WeightedProjection.lean` | `94f8b2139782f21f0b1455079d018a831bb357055b0029c2164512eca7df29da` | CAS11-C03 CAS_4AXIS_PASS, Astra review PASS (`RETURN.json`) |

Location discrepancy (recorded, not a missing item): the dispatch prompt locates the accepted finite
C02/C03 theorems in `CAS-11/lean/Main.lean`. That file (sha256 `71d4dc6cc9df6193f02fc60d3049cdbb0ab5df3c47e93630de8cc38889ef5fbe`, 6 lines; see
`CAS-11/lean/result.json`) only contains `grstat_cas11_bregman`; its own result marks C02/C03 `false`. The
accepted finite theorems actually live in the separate local runs `GRSTAT-CAS11-C02-20260930T090559Z`
(lean/FiniteGram.lean, completion/RESULT.md "CAS_4AXIS_PASS") and `GRSTAT-CAS11-C03-20261001T020800Z`
(lean/WeightedProjection.lean, RETURN.json `aggregate_status: CAS_4AXIS_PASS`). Those are the sources reused.

Reuse scope:
* `CAS11C02.finiteGramForward` (0 < n, PSD R, all-a hypothesis ⇒ range + spectral-pinv bound) is used
  verbatim for the finite step; its universal all-a hypothesis is discharged by the real integral (T4).
* `CAS11C03.weighted_cauchy_schwarz` is stated for an arbitrary real inner-product space (the
  `FiniteDimensional` instance is omitted for it in the source) and is used in L²(W dν).
  The other C03 definitions (`residual`, `gram`) require `[FiniteDimensional ℝ E]` and therefore do NOT
  apply to L²(W dν); they are not used. Card pitfall "finite C03 PASS does not replace weighted Hilbert-space
  existence" is respected: the projection onto V in L²(W dν) is constructed from completeness of the finite
  dimensional V in the (infinite-dimensional) Hilbert space `Lp ℝ 2 (wmeas μ W)`.
* `G11B.B2_integral` (∫ (f−g)²/W dμ ≤ 2ε, integrability) supplies the L²(W) membership of z = (f−g)/W.
  G11-A `_stat` wrappers enter only through G11-B (`B2_integral` uses `finite_budget_stat`).

## 3. Items not recoverable / not in scope

* The physical certification of ε, of the envelope W and of the actual channel kernels (S:100) is
  data/physics input, not a mathematical definition; not supplied, not claimed.
* The collision-operator variant (A7) (S:118-128) is a different card-level statement (adjoint L*);
  not in the G11-C card scope; not claimed.
* No missing definition blocks a G11-C sub-target.
