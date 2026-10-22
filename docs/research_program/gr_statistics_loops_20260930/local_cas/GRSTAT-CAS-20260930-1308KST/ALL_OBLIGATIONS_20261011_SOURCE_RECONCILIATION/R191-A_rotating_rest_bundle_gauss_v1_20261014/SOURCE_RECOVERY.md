# R191-A source recovery (rotating rest-bundle canonical Gauss object)

Repository HEAD at recovery time: `7bc52116` (read-only; no state-changing git used).
Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` (sha256 `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`)
member `HTT_ALL_OBLIGATIONS_20261011/tasks/R191-A.json`, extracted to `raw/card_R191-A.json`
(sha256 `a5160d07ad7b9ccdf4dc87258b1b87837836bcf6e59731adf17607f251517a9b`).

## 1. Card text (verbatim, translated only for reading)

* `scope_original`: "ω≠0 nonintegrable rest bundle의 curvature object와 slice curvature를 구별하여 canonical tensor theorem을 만든다."
  (Distinguish the curvature object of the ω≠0 nonintegrable rest bundle from slice curvature and make a canonical tensor theorem.)
* `lean_steps`: (1) define the rotating-congruence projector, connection and Gauss object from the source roadmaps;
  (2) write the exterior derivation including the nonintegrability term and the projected tensor derivation separately;
  (3) prove the ω² sign/order of the two representations as an exact equality;
  (4) make a transformation theorem distinguishing frame-convention change from invariant content.
* `acceptance`: two independent derivations agree in sign/order; reduction consistent with the ω=0 hypersurface branch.
* `pitfalls`: do not call the ω≠0 object an orthogonal metric or slice curvature.
* `existing_reuse`: frame-indexed algebra; finite random-state residuals are validation fixtures only.
* `consumed_export_review.consumed_exports`: "PR187 accepted frame/type/convention definitions; if no ready formal
  definition, reconstruct the source definition in this packet". No PR-187 formal Lean definition exists in the
  repository (searched `docs/research_program/**/lean`, `local_cas/**`, `local_execution/**` for PR187/frame-type
  modules: none). The definitions are therefore reconstructed below from the cited sources.

## 2. Parent PR and roadmap

* `docs/codex_handoff/pr_backlog.yaml:5940-5997` (sha256 `b204c187…f3d7`), PR-191 targets: "vortical congruence의
  nonintegrable rest bundle에는 명시된 Gauss curvature object를 사용하며 slice curvature와 구분한다";
  dod (`:5971-5972`): fail if the two independent exterior/tensor derivations differ in ω² sign/order;
  kill (`:5976`): describing a convention-dependent quantity as invariant; forbidden (`:5989`): the phrase
  'orthogonal metric' at ω≠0.
* `htt_post_v10_strengthening_plan_20260721/03_POST_V10_STRENGTHENING_PR_ROADMAP_20260721.md:269-297`
  (sha256 `869e11f9…a306`): "same-order/transposed contractions의 정확한 관계를 theorem으로 정리한다";
  "n-frame hypersurface curvature와 u-rest curvature를 별도 API로 구현한다"; PASS gate items "ω=0 limit에서 standard
  3-curvature exact recovery" and "contraction ordering difference exactly 2ω_abω^ab 증명".
* `htt_post_v10_strengthening_plan_20260721/01_HOSTILE_REFEREE_STEELMAN.md:27-31` (H03: for ω[u]≠0 no
  u-orthogonal hypersurface exists, so 'orthogonal metric 3-curvature' is undefined) and `:111-115` (H17: the two
  Gauss contractions differ by 2ω²).
* `htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md:55-63` T-GAUSS-RESTSPACE:
  relation between the two contraction conventions, canonical scalar, ω=0 hypersurface limit; proof route Cartan
  structure equations.
* `docs/codex_handoff/remaining_pr_crosswalk.csv:25` (PARTIAL_REMAINDER, "frame-indexed algebra exists",
  "scope-qualified theorem only"); `docs/codex_handoff/REMAINING_PR_EXECUTION_PLAN_KO.md:138-142` (reuse finite
  witnesses; do not call finite examples general closure).

## 3. Recovered definitions (verbatim sources)

Primary implementation source: `htt/obsstat/egs3_king_ellis_frame.py` (sha256 `608b4cf9…b236`, REV-R181 `26d7db769`,
ordering disclosure added in REV-R183 `3e20dcd77`).

| object | verbatim source | Lean (this packet) |
|---|---|---|
| jet `D_mn = ∇_m u_n` (derivative index first) | `egs3_king_ellis_frame.py:195` `grad[m, n] = nabla_m u_n` | P03-A `D a b` (imported unchanged); frame `jet γ B C = γ C B 0` |
| projector `h^m_a = δ^m_a + u^m u_a`, `h_ab = g_ab + u_a u_b` | `:210`, `:211` | P03-A `projDown`, `hDown`, `hUp` |
| `V_ab = h^m_a h^n_b ∇_m u_n` | `:216` (comment `:215`) | P03-A `spatialJet` |
| `ω = (V − Vᵀ)/2`, `σ = (V+Vᵀ)/2 − θh/3` | `:220`, `:221` | P03-A `vorticity 1`, `shear 1` |
| Riemann `R^l_{mkn}` (l out, m in, k,n 2-form slots) | `:120-121` | `riem` (frame, lowered first slot) |
| projected connection (rest-bundle connection) | `docs/research_program/gr_statistics_loops_20260930/supplements/DOSSIER_POSITIVE_BRIDGE.md:86` (sha256 `00c1fcb0…5ebd`): "use the rest-bundle connection obtained by projecting the spacetime connection: … h∇_X e = 0" | frame coefficients `γ i.succ B j.succ` (spatial i,j; any direction B) |
| Gauss scalar, same-order product | `:371-412` `_proj_riemann_trace`: `R3 = h^{mk}h^{nl}R_mnkl + V_abV^ab − (h^{ab}V_ab)^2`; `trVV` at `:409` | `gaussProdSame` |
| ordering disclosure | `:378-386`: "the TRANSPOSED contraction tr(V.V) instead of V_ab V^{ab} differs by exactly 2 omega_ab omega^ab and yields the Ellis-convention identity with -omega^2" | `gaussProdTrans`, theorem `same_sub_trans` |
| non-integrability note | `:481-485`: "for omega != 0 no family of 3-surfaces is orthogonal to u (Frobenius), so R3 is the Gauss-equation curvature of the formal rest spaces" | `bracket_vertical`, `frobenius_iff` |
| derived KE identity | `docs/research_program/THEOREM_REGISTRY.yaml:731-752` KE-FRAME; `docs/research_program/egs3/tickets/t3_king_ellis.yaml:123-125`; Wolfram twin `wolfram/ke_rotating_congruence.wls:108-122` (same trVV contraction at `:115-116`) | consistency target only (see §5) |
| ω index-order convention | `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md:10-11`: "This derivative-first W equals minus c times the book's velocity-first vorticity." | `vorticity_transpose_jet` |

## 4. Reconstruction of the exterior (Cartan) derivation

The sources fix the projector, jet, projected connection and the two scalar contractions, but contain no written
exterior/Cartan derivation (the backlog names Cartan structure equations as the proof route only). It is
reconstructed here, in an adapted orthonormal frame `e_0 = u`, `e_i` spatial, `η = diag(−1,1,1,1)`:

* `γ A B C := ⟨e_A, ∇_{e_B} e_C⟩` (frame connection coefficients); metric compatibility `γ A B C = −γ C B A`.
* torsion-free bracket `[e_C,e_D] = Σ_E C^E_{CD} e_E`, `C^E_{CD} = η_EE (γ E C D − γ E D C)` (`bracket`).
* Cartan second structure equation (lowered): `R_ABCD = e_C(γ_ADB) − e_D(γ_ACB) + Σ_E η_EE(γ_ACE γ_EDB − γ_ADE γ_ECB)
  − Σ_E C^E_{CD} γ_AEB` with the derivative data `dγ C A D B = e_C(γ_ADB)` an independent array (`riem`).
* Rest-bundle connection `∇^H_X Z = h∇_X Z`; its coefficients are `γ i B j` (spatial `i, j`, every direction `B`).
  Its curvature 2-form (exterior covariant derivative of the connection form) evaluated on `(e_C, e_D)` with the
  FULL bracket — whose vertical component `C^0_{kl}` is the nonintegrability (ω) term — is `restCurv`.
* `horizCurv` drops the vertical bracket component (what one obtains by treating the rest spaces as if they were
  slices). It is used only as the contrast object required by the pitfall.
* Frame jet: `D_BC = ⟨e_C, ∇_B u⟩ = γ C B 0` (`jet`); derivative-first, matching P03-A and `:195`.

The chart-level tensor derivation uses P03-A objects unchanged and defines the 4-index projected Gauss object
`G_abcd = h_a^p h_b^q h_c^r h_d^s R_pqrs − V_ca V_db + V_da V_cb` (`gaussTensor`), the index pattern forced by the
frame identity (theorem `gaussTensor_frame`).

## 5. Reused reviewed Lean (imported unchanged)

* P03-A `VelocityJetDecomposition.lean` (sha256 `f67b882235288225d81813c9a0ec87d78e0846e23349f437eb1793b0c5ce243b`,
  `RETURN.json` FORMALLY_CHECKED_SCOPED, review PASS_WITH_NOTES) at
  `docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-03/velocity_jet_decomposition_v1_20261014/lean/`;
  its imports `VelocityJetRest.lean` (`0d696565…b684`) and `PortCas01.lean` (`e289039f…0c7b`). All three are
  compiled unchanged from their original paths into `raw/imports/`.
* P05-A `OrbitCurvatureEigenframe.lean` is NOT imported: it models spacelike orbit (Lie-algebra) curvature and its
  `RETURN.json:56` explicitly does not claim "identification of spacelike orbit curvature with a rotating
  rest-bundle slice curvature". That pitfall is respected here: no orbit-curvature object is used.

## 6. Missing / not recovered

* No PR-187 formal frame/type module exists; reconstructed per the card's `consumed_exports` fallback (§4).
* `2 G_uu` identification of the projected-Riemann double trace (KE identity first term) is a source claim
  (`THEOREM_REGISTRY.yaml:741-743`) that needs Riemann pair symmetries and Ricci/Einstein definitions; it is not a
  card target and is not claimed here. Unlock: a separate target with explicit Riemann-symmetry hypotheses.
* Field-level realization (actual frame fields, brackets as Lie derivatives, `dγ` as true derivatives) is not
  modelled: everything is pointwise in an adapted frame or a chart basis.

## 7. Resume addendum (2026-10-23, second author run)

The first author run was interrupted by a rate limit after writing this file and
`raw/card_R191-A.json`; no frozen targets, Lean source or compile receipts existed. On resume
the repository HEAD is `a8fd1763` (read-only). Re-verified citations at that HEAD:

* `docs/codex_handoff/pr_backlog.yaml` now has sha256 `5cf688f233967f762778fa9d6636850c212cee16fb848a17eb8006fb63f3b935`;
  the PR-191 entry moved to `:6004-6077` (targets `:6022-6024`, dod `:6035-6036`, kill `:6040`,
  forbidden `:6053`). Content of the quoted fields is unchanged from §2.
* `htt/obsstat/egs3_king_ellis_frame.py` (sha256 `608b4cf9…b236`, unchanged): `:195`, `:371-412`,
  `:482-485` as cited in §3.
* `htt_post_v10_strengthening_plan_20260721/03_POST_V10_STRENGTHENING_PR_ROADMAP_20260721.md`
  (repository-root directory, sha256 `869e11f9…a306`, unchanged) `:269-297`.
* `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md:10-11` (sha256 `4714827e…97ff`).
* `docs/research_program/gr_statistics_loops_20260930/supplements/DOSSIER_POSITIVE_BRIDGE.md:86` (sha256 `00c1fcb0…5ebd`).

Convention finding recorded for the return: with `R_ABCD = ⟨e_A, R(e_C,e_D)e_B⟩` and the scalar
`Σ_{kl} F_{kl,kl}`, the curvature of the projected rest-bundle connection reproduces the
TRANSPOSED Gauss product `V_ab V^ba` (Ellis convention, coefficient `−ω²` relative to the
same-order product), not the source module's stated same-order `V_ab V^ab`. The source discloses
this ordering (`:378-386`); the two differ by exactly `2 ω_ab ω^ab` (theorem T7/T9).
