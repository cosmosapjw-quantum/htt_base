# R195-A — independent review (verbatim final report of a fresh read-only reviewer)

# R195-A independent review (windowed bulk flow v1, 20261014)

Reviewer model: Claude Opus 5.5 (`claude-opus-5-5`). I did not author this task. I edited no repository file and ran no state-changing git command. My scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/`.

## Verdict: PASS_WITH_NOTES

There are no blocking findings. T1–T7 are proved exactly as frozen. The two card acceptance criteria hold, and both pitfall controls are genuine within their stated scope. The independent recompile succeeded and the axiom audit is clean. Scientific admission stays **HOLD**.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read first | PASS | Read via `unzip -p …/tasks/R195-A.json`. Scope: B_W = v0 + finite-k residual, with window, spectrum, gauge/frame and remainder. Acceptance: residual included, cross terms kept. Pitfalls: no B/c→β, no "failure ⇒ Ω_tilt=0". |
| 1b | Source citations | PASS (one minor note, N4) | I re-read every cited range: pr_backlog.yaml 6298-6352 (PR-195 target, kill, forbidden) and 8209-8233 (PR-222); roadmap 392-419; steelman H07 51-55; THEOREM_PROOF_BACKLOG 105-113; revival_bulk_bridge.py 1-43 (rows = windows, `C = diag + off*ones`); frame_typed_algebra.py 28, 53-54, 142-143; bulkflow_estimator.py 6-21; velocity_power.py 9-13, 74-80; cf4_velocity_estimators.py 110-115; report v10 :1547; crosswalk :29; plan KO 137-141; `git show a40e5382a:scripts/cf4_bulkflow_lcdm_variance.py` 24-50 (commit a40e5382a is "REV-R195"). All content matches SOURCE_RECOVERY.md. |
| 1c | Source sha256 | PASS | All 16 recomputed hashes match SOURCE_RECOVERY.md exactly: package zip `2d0b6da9…`, pr_backlog `5cf688f2…`, CF4 blob `b4a2d2eb…`, and the rest. |
| 1d | FROZEN_TARGETS predates proofs | PASS | FROZEN_TARGETS.md is committed in 6365e36d (2026-10-14 13:24 +0900). The working copy equals that commit (`git diff --quiet`), sha `86f07f2c…`. The first compile receipt is 2026-10-22T17:42Z. The frozen file contains no A1/A2 text (grep count 0); amendments are recorded separately. |
| 1e | T1–T7 exactly as frozen | PASS | Line-by-line comparison of the Lean file against FROZEN_TARGETS. I also re-typed the frozen statements of T1, T1g, T2, T3, T3m and T5 `remainder_bound` verbatim as `example … := R195A.thm` in my audit file, and they elaborate (exit 0). Signatures of T4, T5 remainder/`ofBulk`/`ofBulk_obs`, T6 and the seven T7 witnesses match textually. The only differences are the instance omissions recorded as A0, which make the results more general. |
| 1f | Key identities by hand | PASS | T3 sign: K = ∫e^{ik(x−y)}p and Ŵ(k) = ∫e^{−ikx}W give Cov = ∫conj(Ŵ)Ŵ′p, which is correct. T7 field: cos(x + jπ/2) gives the stated four functions. Covariance = cos(x−y)/2 = ¼·2cos(x−y) on δ₁+δ₋₁. Nonidentification: 0 + cos0 = 1 + (−sin0) = 1. Cross window E[a(0)a(1)] = cos1/2 > 0. |
| 1g | A1: CF4 A⁻¹b decomposition | PASS | `num/a1_algebra.py`. On a random catalogue (N=500) the max\|LHS−RHS\| is 2.2e-15 and \|ΣA⁻¹G_i − I\| is 1.1e-15. Sympy, for generic symbolic N=3: adj(A)·b − [det·v0 + Σ adj·G_i·δ_i + adj·Σw_iε_i n_i] expands to 0. |
| 1h | A2: matrix cross-spectrum | PASS (scope note N8) | p_ij is not free. It is pinned to the true covariance by hypothesis hK, and nothing derives it from physics. The source kernel (H0f)²P k_ik_j/k⁴ is a valid instance: \|k_ik_j\|/k⁴ ≤ 1/k², so hp holds whenever ∫P dk < ∞ (finite σ_v). This matches the source ⟨v_m v_n⟩, including the e^{ik(x_m−x_n)} sign. |
| 1i | A3: T8 under stronger measurability | Acceptable scope note, not a residual | T8 was optional ("attempted"). T2, T3 and T4 keep `hjoint` explicit, and nothing consumes T8. Replacing a.e.-strong measurability with `Measurable` (including W, W′) strengthens the hypotheses, so the theorem is weaker; this is honestly recorded and listed as not proved. The added `Integrable (a(·,x)²)` is not a substantive strengthening: Lean's Bochner integral returns 0 for non-integrable functions, so the bound alone would be vacuous. |
| 1j | Negative controls genuine | PASS (nuance N5) | B/c: `witness_residual_variance` (E[(B−v0)²] = 1/2 > 0) and `witness_residual_nonzero` show a nonzero finite-k residual. Bridge failure: `witness_nonidentification` shows one observed bulk value arising from v0=0 and from v0=1. `witness_cross_window` shows that zeroing the cross term is false. |
| 2 | No assumed conclusions; no vacuity | PASS | No hypothesis restates its conclusion; hK, hjoint and hmean are standard inputs. The author left joint satisfiability of all T4 hypotheses unclaimed. **I proved it**: `t4_nonvacuous` instantiates `multiwindow_forward_law` with ι = Fin 2, ν m = δ_m, W = 1, L = id, the four-phase field, μ = δ₁+δ₋₁ and pc = 1/4. It closes every hypothesis (hnorm, hv, hu, hint1, hmean, hjoint, hpc, hK). Axioms: [propext, Classical.choice, Quot.sound]. |
| 3a | Receipt integrity | PASS | For all 8 receipts, the source/stdout/stderr sha256 match the JSON and AUTHOR_RETURN. Exit codes are 01=1, 02=0, 03=1, 04=0, 05=0, 06=1, 07=0, 08=0; the failed attempts 01, 03 and 06 are kept with their logs. compile_07 source is byte-identical to `lean/R195AWindowedBulk.lean` (`9b8b2743…`), and compile_08 source equals AxiomAudit.lean (`ee052479…`). The olean sha matches AUTHOR_RETURN (`4c197ceb…`). stderr is empty in all receipts. |
| 3b | Forbidden tokens | PASS | grep for sorry/admit/native_decide/axiom/set_option/sorryAx/implemented_by/extern/unsafe/opaque in T/lean finds only the header comment at line 5. AxiomAudit.lean is clean. |
| 3c | Axioms | PASS | All 31 public theorems print a subset of {propext, Classical.choice, Quot.sound}. `ObsModel.obs_sub_v0` uses only propext. |
| 4 | Independent recompile | PASS | Source copied to `r195-a_rerun/src`, same sha. Compiled from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` with `lake env bash -c "LEAN_PATH=$S:$LEAN_PATH lean -R $S/src -o $S/R195AWindowedBulk.olean $S/src/R195AWindowedBulk.lean"`: exit 0, 4 warnings (unused section variables, one deprecation), 0 errors. Toolchain is leanprover/lean4:v4.31.0; mathlib manifest and checkout are both `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. My audit file `r195-a_rerun/audit/ReviewAudit.lean` (frozen restatements, `t4_nonvacuous`, `spectral_excludes_k0_of_null`, and `#print axioms` for all 31 public theorems plus mine) compiled with exit 0; output is in `r195-a_rerun/review_audit.stdout`. |
| 5 | GRF simulation of T3/A2 | PASS | `num/grf_crosswindow.py`, seed 77 rerun, and `num/t3_highstat.py`. Setup: periodic 32³ box (L=200), toy P(k) with p(0)=0 (finite-k only), discrete spectral measure p = P/V, v0 added. Details below. |

**Simulation detail (check 5):**

- **Scalar T3, two overlapping normalized Gaussian windows.**
  - Theory gives C11 = 0.041411, C22 = 0.022056, C12 = 0.020205, and Ŵ(0) = 1.000000. A real-space Σ_xy W W′ C(x−y) evaluation agrees to about 1e-9.
  - Three seeds of 30k realizations each give emp/th − 1 between −0.33% and +0.59%, against a relative SE of 0.82%.
  - Earlier runs (6k and 20k realizations) gave z between −0.5 and −2.3. The 90k high-statistics runs show these were Monte Carlo fluctuations.
  - mean(B) − v0 is consistent with 0.
  - Setting the cross term to zero would be wrong by 43–78σ.
- **A2/CF4 operator windows.**
  - Linear-theory field v = i k δ/k² (spectrum P k_ik_j/k⁴), two overlapping catalogues of 400 tracers each, estimator B = A⁻¹Σw u n.
  - For the full 3×3 cross-covariance (16k realizations), the elementwise z-scores lie in [−2.24, +1.94] and are correlated.
  - mean(B_A,B) − v0 is consistent with 0, within 1.7σ.
  - The residual rms is about 1.3 per component against \|v0\| = 1.68, so the finite-k residual is a material part of the model, not negligible.

## Card acceptance and pitfalls

- **Finite-k residual included in the model: PASS.** It appears as `resid := bulk ν W u ω` in `ObsModel.ofBulk`, as an explicit term in T1/T1n and T4(i), in the covariance law of T3/T4(iii), and as Σ A⁻¹G_iδ_i in A1. Nothing drops it.
- **Correlated-window cross terms preserved: PASS.** T4(iii) holds for every pair (m, n), including m ≠ n, with its own `pc m n`. A2 keeps the full Σ_iΣ_j double sum. Both the witness (cos1/2 > 0) and the simulation show the cross term is nonzero.
- **B/c pitfall: PASS.** No β = B/c definition exists anywhere in the module.
- **Bridge-failure pitfall: PASS within scope.** No result maps v0 to Ω_tilt, and the non-identification witness blocks reading a bridge failure as v0 = 0.

## Blocking findings

None.

## Non-blocking notes

- **N1 – T6 hypothesis is stronger than needed (proved as frozen).**
  - `spectral_excludes_k0` assumes `[NoAtoms μ]`, but the proof uses only μ{0} = 0. The T7 witness measure δ₁+δ₋₁ has atoms, so T6 cannot be applied to the package's own witness.
  - I compiled `spectral_excludes_k0_of_null (h0 : μ {0} = 0)` and confirmed μ{0} = 0 for the witness.
  - T4 places no condition on μ{0}. If μ has an atom at k = 0, the "residual" contains a random constant mode that is degenerate with v0, so "finite-k" is a label in T4, not a constraint.
  - Optional fix: add a μ{0} = 0 lemma, and optionally a T4 corollary that carries that hypothesis.
- **N2 – Joint satisfiability of T4.** The author left this unclaimed; my `t4_nonvacuous` now witnesses it (check 2). The author may adopt it.
- **N3 – A1 is not formally linked to `bulkOp`.**
  - The `cf4_estimator_decomposition` docstring says the estimator "is an operator-window bulk flow". No lemma proves `Ainv (Σ w_i u_i n_i) = bulkOp (Σ_i dirac x_i) …`; A1 is pure finite algebra.
  - Suggested fix: add that bridge lemma, or soften the docstring wording.
- **N4 – Citation precision.** SOURCE_RECOVERY credits `b = Σ w_i u_i n_i` to CF4 script lines 24-27. Those lines give only B = A⁻¹b and A. The b formula is in `htt/src/common/bulkflow_estimator.py:6-21`, which is also cited. Cosmetic only.
- **N5 – What the B/c control actually refutes.** Under hmean, T4(ii) shows E[wobs] = L v0, so B is an unbiased estimator of v0. The control refutes point substitution, i.e. ignoring the residual variance and the realization dependence, not unbiasedness. The bridge-failure control is a single-realization non-identification proxy, not a model of a failed calibration or test. Both match the "not claimed" list; the wording should keep that distinction.
- **N6 – Frame is a phantom index.**
  - `Frame` appears only in `Rem`/`ObsModel`. T2–T4, A1 and A2 carry no frame, and nothing enforces the PR-187 bridges (obs→u→n).
  - Gauge invariance is honestly listed as unrecovered (roadmap :398 has no source definition). This is a methodological limit, not a code defect.
- **N7 – A3 is acceptable as a scope note** (check 1i). The a.e.-strongly-measurable version stays not proved.
- **N8 – A2 spectrum.** p_ij is a hypothesis constrained by hK, not "a free choice". The linear kernel is a valid, integrable instance and is not derived.
- **N9 – Olean size differs** between the author's build (1405720 B) and mine (1405624 B). Both builds came from the identical source; I attribute this to the different build/output paths, but I did not investigate it.
- **N10 – Lint.** There are unused `[MeasurableSpace Ω]` section variables and a deprecated `ContinuousLinearMap.sum_apply` at line 461. Cosmetic.

## Not proved / not claimed

- **Scientific admission: HOLD.**
- The v0 → Ω_tilt / β map (R194-A/B).
- Gauge-invariant velocity; the frame appears only as tags.
- Bochner's theorem, i.e. existence of a spectral density (hK is a hypothesis).
- Derivation of P(k) or of the (aHf)² P k_ik_j/k⁴ kernel.
- The isotropic radial reduction and the σ_v closed form.
- Magnitudes or models of the selection and calibration remainders (only their typed additive placement is proved).
- T8 under a.e.-strong measurability.
- The `cf4` ↔ `bulkOp` bridge lemma (N3).
- A T6 variant under μ{0} = 0 inside the package (exists only in my audit file).
- PR-222 GLS rank-3 numerics, real-data fitting, any CF4 number.
- The PR-195 PASS gates: coverage over 10k injections, bias, and injection recovery. My simulation is a reviewer diagnostic, not the registered gate.
- The Independence gate.
- Publication readiness.

## VALIDATION_MATRIX scientific row (proposed; I did not write it)

`R195-A | scientific | PASS_WITH_NOTES (independent, claude-opus-5-5) | T1–T7 as frozen (verbatim re-typecheck); recompile exit 0 at Lean 4.31.0 / mathlib fabf563a; axioms ⊆ {propext, Classical.choice, Quot.sound}; T4 jointly non-vacuous (reviewer t4_nonvacuous); A1 algebra numeric 2e-15 + sympy exact; GRF 32³ T3 within 0.6% (90k realizations), A2/CF4 3×3 cross-cov |z| ≤ 2.24; cross-term ≠ 0 at 43–78σ; notes N1 (T6 NoAtoms→μ{0}=0), N3 (cf4↔bulkOp link), N6 (frame phantom/no gauge) | admission HOLD`

## Relevant paths

- Lean module: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/ALL_OBLIGATIONS_20261011_SOURCE_RECONCILIATION/R195-A_windowed_bulk_flow_v1_20261014/lean/R195AWindowedBulk.lean`
- Reviewer audit file: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/audit/ReviewAudit.lean`
- Reviewer audit output: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/review_audit.stdout`
- A1 algebra check: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/num/a1_algebra.py`
- GRF simulation: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/num/grf_crosswindow.py`
- GRF outputs: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/num/grf_crosswindow.out` and `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/num/grf_crosswindow_seed2.out`
- High-statistics T3 check: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r195-a_rerun/num/t3_highstat.py`
