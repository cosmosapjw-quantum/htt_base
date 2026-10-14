# P10-A source recovery (PORT-CAS-10)

Repo HEAD at recovery: `ac3c7d2c5ca93c82802e6e2b777f4fc35a9eec5b` (card snapshot
`a30d84c7918b54238a48fa62e2ef482f7e6d36fa`; the owning implementation was last
changed at `bc45fb9292a4cfb095d7b61d4e5c02a32fb39c5c`).
Card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip` member `tasks/P10-A.json`
(member sha256 `8a27f01c9b86d1e686adbeb8fb678ab42eaed9945eff19704d37afd982486ce5`).

## Contract and map

| What | Where | sha256 |
|---|---|---|
| CAS-10 identity `B*=c*d*/delta*; Q=diag(1/3,1x5,2x3,c^-2x3)/B*^2; K_w=I_ws+I_wprime_m-(wbmb-wama)`; assumptions "positive stress gap; supplied derivatives; finite remainder integral and k bound" | `theory_inference_port_20260930/CAS_CONTRACT.json:123-126` | 904d95fe…389fad |
| F7-P2 "Conditional stress-gap body" -> `stress_gap_budget`; limits: supplied same-state eigenbranch, gap, derivative norm bound; not a universal MES anchor; no stress/Einstein inverse provider | `theory_inference_port_20260930/PORT_MAP.json:78-89` | d0050aa3…e5f0 |
| F7-W1 "Weak optical response" -> `weak_response_budget`; supplied integrals/endpoints/error bounds; "Uncertain coefficient error needs finite kinematic bound" | `theory_inference_port_20260930/PORT_MAP.json:92-103` | (same) |
| SOURCE_TO_REPO.json | no entry for `stress_gap_budget` / `weak_response_budget` / F7 (grep empty); recorded, not a blocker because PORT_MAP names the owning API | ac5aa450…cbf0 |
| Port mapping of F7 (Q in order (theta,sigma5,omega3,A3), K_w formula, epsilon = L*variation_integral + M_k*coefficient integral + supplied numerical errors) | `theory_inference_port_20260930/implementation_review/formalism_mapping.md:127-148` | 2a25f2ce…6426 |

## Owning implementation `htt/src/common/typefree_physical_budgets.py` (sha256 5dc34f39…6fff)

- `:18-32` `StressBudgetContext`: stress component, congruence, frame, epoch,
  derivative-norm definition, provenance must all be supplied (typed premise).
- `:42` coordinate order `(theta, sigma1..5, omega1..3, A1..3)`.
- `:45` "STF coefficients use a Frobenius-orthonormal five-vector basis" -> Lean `stf`.
- `:49` gauge = `sqrt(x @ Q @ x)` -> Lean `channel ⬝ᵥ (Qmat *ᵥ channel)`; body = gauge ≤ 1.
- `:52-60` `stress_gap_budget` docstring: `B*=c d*/delta*`; d* bounds the positive
  observer norm of all 4x3 projected stress derivatives (not Lorentzian); same-state
  timelike eigenbranch and gap/derivative bounds are supplied premises. Units: theta,
  sigma, omega inverse time; A acceleration; c length/time. Separate from the geodesic MES anchor.
- `:66-67` positive gap and c required; `:68` `budget = c*d/gap`.
- `:71-72` d*=0 -> `ZERO_BODY` (no Q); Lean W1/W2 therefore require d*>0.
- `:73` `q = diag([1/3, 1×5, 2×3, 1/c²×3]) / budget²` -> Lean `baseWeight`, `qWeight`, `Qmat`.
- `:90-98` `weak_response_budget` docstring: `K = I_ws + I_w'm − (w_b m_b − w_a m_a)`;
  `variation_integral = ∫|w| ||A|| |t−t0|`; `coefficient_error_integral = ∫|w| ||δA||`,
  which "needs a finite bound on ||k||"; inputs are supplied integrals, no quadrature claim.
- `:112-113` uncertain coefficients without finite `kinematic_bound` -> ValueError
  (the Lean W6a negative control is the mathematical reason).
- `:115` `error = l*v + bound*perturbation + numerical` -> Lean W5b/W5c radius
  `L*V + Mk*P + εnum`.
- `:118` `response = s + wp − (b − a)` with `a = w_a m_a`, `b = w_b m_b`.
- Tests `htt/src/common/test_relativistic_kinematics.py:134-148` (sha256 919b99cb…ea27):
  `stress_gap_budget(d=2, gap=4, c=2)` gives B*=1 (Lean `W1_python_fixture`);
  weak budget response `[7,9]`, radius 8.1, missing k bound raises.

## Original mathematics (definitions of s, m, w, A, k, d*, δ*)

- TF-P2: `typefree_loop2_20260928/source/ADJUDICATED_AMENDMENTS_KO.md:21-29`
  (sha256 91c3cfc8…51cd). Smooth future timelike branch with `T^a_b U^b = −ε U^a`,
  `L = S + εI`, `δ = min_i |ε+λ_i| > 0`, `D_μ = h(∇_{E_μ}T)u`,
  `∇_{E_μ}U = −c L^{-1} D_μ`, and
  `θ²/3 + ||σ||_F² + 2|ω|² + |A|²/c² ≤ c² Σ_μ|D_μ|²/δ²`; with `δ ≥ δ* > 0`,
  `||D|| ≤ d*` at the same state, `B* = c d*/δ*` (line 23). Line 28: E0=u,
  orthonormal rest triad, ||D||² = Σ_{μ=0}^3 Σ_i (D_μ^i)² (observer-positive).
  Exact rest-frame algebra: `typefree_loop2_20260928/RESULTS_KO.md:18-48`
  (sha256 16324109…0417).
- TF-W1: `ADJUDICATED_AMENDMENTS_KO.md:198-213`. Line 200: fixed finite-dimensional
  transported spaces, `m ∈ AC([a,b])`, `s ∈ L1`, `A ∈ L1`, `w ∈ C1`,
  `m′ + A k = s` a.e.; `k0 = k(t0)`, finite `L ≥ 0`, `||k(t)−k0|| ≤ L|t−t0|` a.e.;
  `K_w = ∫ w A k = ∫(ws + w′m) − [wm]_a^b`, `||Abar_w k0 − K_w|| ≤ L∫|w| ||A|| |t−t0|`,
  `Abar_w = ∫ w A`. Line 211: integrability of A and finiteness of the weighted
  error integrals must be explicit (Lean: `hA_int`, `hV_int`, `hP_int`).
- `typefree_loop2_20260928/TF_W1_INPUT_KO.md:23,36-44` (sha256 26b36aee…92ce):
  instance `m = ρ`, `m' = s − A_0 k`; uncertain `A_0` needs `∫|w| ||δA_0|| ||k||`,
  and if `||k||` is free it cannot become a finite number (line 44). K_w unit:
  energy density / time. Errata `typefree_loop2_closeout_20260928/ERRATA_F1_W1_KO.md`
  (sha256 486395b1…78e2) only re-scopes the kernel criterion, not the identity or budget.

Sign check of the contract's K_w (W4): from `A k = s − m′`,
`∫ w A k = ∫ w s − ∫ w m′ = ∫ w s − (w_b m_b − w_a m_a − ∫ w′ m)
= I_ws + I_w′m − (w_b m_b − w_a m_a)`. Matches CAS_CONTRACT and `:118`.

Budget recovered (W5): with true coefficient `A = Â + δA`,
`||Â̄_w k0 − K_computed|| ≤ L ∫|w| ||Â|| |t−t0| + M_k ∫|w| ||δA|| + ε_num`,
where `M_k ≥ ||k||` a.e., and `ε_num` bounds the supplied-integral error against the
exact `I_ws + I_w′m − [wm]`. This is `:115` term by term.

## Reused GR-04 results (citation only)

`gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-04/completion_20261003/lean/Proof.lean`
(sha256 8a870e4e…8144, AXIS_RESULT PASS): `theta/sigma/skew/omega/accel` encodings
(`:387-404`), `rate_four_by_three` (`:406`), `projected_eigen_derivative` (`:113`),
`signed_gap_sum_bound` (`:491`). The encodings are re-declared verbatim in
`P10A`; `rate_four_by_three` and a component gap lemma are re-proved locally as
private lemmas (not re-claimed as new). The derivation of the diagonal eigen equation
`gap_i q_μi = −c D_μi` from an actual smooth stress (GR-04 `projected_eigen_derivative`)
and the general self-adjoint diagonalization bridge remain premises here.

Missing source definitions: none blocking. SOURCE_TO_REPO.json lacks an F7 row (recorded).
