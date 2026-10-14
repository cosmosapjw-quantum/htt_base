# G01-A — independent review (verbatim final report of a fresh read-only reviewer)

# G01-A independent review (`g01a_jacobi_vertex_taylor_v1_20261014`, partial unit)

**Verdict: PASS_WITH_NOTES.** This passes only as a frame-level partial unit. G01-A is not closed as a geometric theorem: R1, R2 and R3 stay NOT_PROVED, and scientific admission is HOLD.

**Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`). This was a fresh, read-only review; I did not author the unit. I edited no repository file and ran no state-changing git command. I wrote scratch files only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-a_rerun/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/g01a_jacobi_vertex_taylor_v1_20261014`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read | PASS | `unzip -p …/HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip …/tasks/G01-A.json`: scope, 4 lean_steps, 4 acceptance items, 2 pitfalls, tool_tasks. |
| 1a | Source hashes | PASS | Recomputed sha256 matches every citation in SOURCE_RECOVERY.md and AUTHOR_RETURN.json: OPTICAL `5ae2b6a6…8c21`, FINITE `d499eb7f…50ac`, CAS-01.json `9f1bbb01…9b57`, rerun RETURN.json `a2f7202d…a070`, synthesis RETURN.md `d28239f3…c674`, M05 Main.lean `0e10bfac…04af`, M04 Main.lean `39b7c460…76c9`, signature recovery `b97b94b1…94a7` and `c7757f0f…809b`. |
| 1b | Source line citations | PASS | Read each line. OPTICAL 9, 11–15, 17, 48 (`J''=ℛJ`, `J=ℓI+O(ℓ³)`, `d_A=√det J=ℓ+O(ℓ³)` on the positive branch, screen change by multiples of K). FINITE 7, 9 (`D''=-Ropt D`), 11 ("defines the sign", `‖Ropt‖≤Kc`, continuous Ropt), 15–18, 24–25, 47, 53. Also rerun RETURN.json:37, M05:12/33/48–60/78, M04:16–17/66–87 and M01:8–11 all match. |
| 1c | Agreement with the reviewed signature recovery | PASS | The sign is frozen to FINITE's `-Ropt` form. T0 is a definition `ℛ:=-Ropt` (a single `neg_comp` rewrite), not a symbol identification. Recovery items 1–3 map to R1–R3, still NOT_PROVED. Item 4 (populate every `JacobiPremises` field) is discharged at frame level by T2. |
| 1d | Frozen before first compile | PASS (evidence is mtime only) | `FROZEN_TARGETS.md` was last modified 2026-10-13T21:19:54.94Z. compile_01 started 21:20:14Z; the first proof compile, compile_02, started 21:26:31Z. Its sha `ad3eb13d…8688` matches AUTHOR_RETURN. The directory is untracked in git, so there is no commit anchor. |
| 1e | Final statements equal frozen statements | PASS | My audit file restates every frozen T0–T12, NV and NC signature verbatim as an `example` closed by the G01A declaration. All compile. The rescale and rotate field formulas match the frozen text by `rfl`. The only deviation is a naming one (note N2). |
| 1f | T2 / T12: every `JacobiPremises` field filled, no assumed conclusion | PASS | `exists_jacobi` builds D and D1 from a glued Picard–Lindelöf solution of the clamp-extended first-order system. D2 is defined as `-(F.R u)∘D u`, so `jacobi` holds by `rfl` (a definition, not an assumption). `deriv_D`, `deriv_D1`, `continuous_D2`, `D_zero`, `D1_zero` are each proved; `continuous_R` and `curvature_bound` come from F; `J.R = F.R`. T12 consumes exactly M05's separate hypotheses (`0≤K`, `0<L`, `0<s≤L`, `eta K L<1`) and does not assume its conclusion. |
| 1g | T4 vertex jet | PASS | `D2 0 = -R 0 ∘ D 0 = 0` is derived from `jacobi` and `D_zero`. D2 is the within-derivative of D1 on `[0,L]`, so this is the one-sided D''(0). |
| 1h | Taylor order (T5–T7) | PASS | The source requires `J=ℓI+O(ℓ³)`; T6 `cubic_bound` gives exactly this. T7 strengthens it: an exact integral remainder for `D - sI + (s³/6)R(0)` and an o(s³) bound. Hypotheses are weaker than the source's: continuous rather than smooth R, and no symmetry. The constant is existential (`K·B/6`, with B a compactness bound on ‖D'‖); this is disclosed. |
| 1i | T8: det>0 and dA = s+O(s³) | PASS | `det>0` is derived via the accepted C02 theorem with η=Cs², δ=1/(C+1). The positive root is justified by the derived sign, not assumed. |
| 1j | T9 screen transition | PASS (scoped) | `screen_transition` gets `D'=ODO⁻¹` from uniqueness (T3), and `det_conj` gives det/√det invariance for any `O ∈ O(2)`, reflections included. This matches the source's single parallel-transported frame. It does not cover "change by multiples of K" (R3), and it assumes rather than proves that parallel frames differ by a constant O. Both limits are honestly declared. |
| 1k | T10 affine rescaling | PASS (it is covariance, not invariance) | `rescale` checks out (D_c''=−c²R(cσ)D_c), with K→c²K and L→L/c. `rescale_area_distance` gives √det D_c = dA/c, so √det of the rescaled matrix equals the physical dA only when c=1. η is truly invariant. Only constant c>0 is treated; no arbitrary parameter is substituted, so the pitfall is respected. The link to T11 is not formalised (note N5). |
| 1l | T11 observer normalisation | PASS | Pure symmetric-bilinear algebra: `B(K,K)=0`, `B(o,K)=1`, and `B(o,cK)=1 ⇔ c=1`. Signs match OPTICAL eq. (1) with `o·o=-1`. My audit instantiates it non-vacuously on the 1+1 Minkowski form `-tt'+xx'` (`mink_symm` plus an example). |
| 1m | Negative controls | PASS (genuine) | My audit builds `constFrame 2 1` (R = 2·id, K=2) and `nonflat_jacobi_exists`. `nonflat_not_linear` then proves, via the author's `negative_control`, that the resulting D is not s·id. So the control discriminates and its hypothesis is not unsatisfiable. The flat witness covers K=0. |
| 1n | Pitfalls | PASS | (i) The matrix jet is not presented as ray existence: `exists_jacobi` is matrix-ODE existence from frame data, status is PARTIAL, and R2 is listed under not_claimed. (ii) The affine parameter is never silently replaced: only explicit constant `s=cσ`. |
| 2 | Hypotheses vs conclusions, vacuity | PASS | No hypothesis restates its conclusion. `ScreenFrameData` is instantiated with nonzero curvature in my audit. T12 is non-vacuous at least in the K=0 case (η=0<1; see the accepted `CAS07M05.zero_curvature_control`). |
| 3a | Integrity hashes and receipts | PASS | Every file hash in AUTHOR_RETURN reproduces: lean `6c1f7a66…de57`, AxiomAudit `57a7b842…bbd1`, run_compile `93fbfa74…60e3`, M05 olean `694b6683…fab0`, G01A olean `8539e328…e269`, all compile_* source/stdout/stderr hashes, and oracle M01 `83acab45…`, M04 `81e374aa…`, C02 `67344c6d…`. Exit codes: 01=0, 02–05=1 (failures kept; 03 is a disclosed identical rerun of 02), 06=0, 07=0, 08=0. The final compile_07 source equals the lean file. All stderr files are empty. |
| 3b | Forbidden constructs | PASS | grep finds no sorry, admit, native_decide, axiom, implemented_by, extern, unsafe, opaque, instance, macro or attribute; the only notation is the local `id₂`. The single `set_option synthInstance.maxHeartbeats 400000` matches the accepted M04 precedent (M04 Main.lean:4–5 sets both `maxHeartbeats` and `synthInstance.maxHeartbeats` to 400000). compile_02 stdout shows it was needed (`timeout at typeclass, maximum number of heartbeats (20000)`). It only raises a typeclass budget and cannot suppress an error. |
| 3c | Axioms | PASS | Author: 40/40 declarations use exactly `[propext, Classical.choice, Quot.sound]`. My audit covers 45 G01A declarations, including the 5 the author skipped (`jacobiField`, `clampR`, `conj`, `conjL`, `ScreenFrameData`), plus 3 of my own. All 48 use exactly those three axioms; no `sorryAx`. |
| 4 | Independent recompile | PASS | See the commands and results below. |
| N | Numerical check (mpmath, 40 digits, Taylor ODE) | PASS | See the numerical results below. |

### Recompile commands and results (check 4)

All commands were run from `/home/cosmosapjw/lean_oracles/viii_oracle` (toolchain `leanprover/lean4:v4.31.0`, mathlib rev `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`).

- **M05 rebuilt from source:** `lake env bash -c "LEAN_PATH=…/viii_oracle:$LEAN_PATH lean -R <S>/imp -o <S>/out/CAS07M05Accepted.olean <S>/imp/CAS07M05Accepted.lean"` gave exit 0, and the olean `694b6683…` is byte-identical to the author's.
- **Copied module:** `LEAN_PATH=<S>/out:<S>/oracle:$LEAN_PATH lean -R <S>/src -o <S>/out/G01AJacobiVertex.olean <S>/src/G01AJacobiVertex.lean` gave exit 0, no errors, and one unused-variable warning (line 304). The olean is `1b0ceae4…`, deterministic over two runs.
- **Why the copy's olean hash differs:** the olean embeds the source path. Compiling the author's in-place source with the author's LEAN_PATH, output to scratch, reproduces `8539e328…` byte-identically.
- **Audit file:** `ReviewAudit.lean` (sha `dccc94bd…54bf`) gave exit 0; its stdout sha is `2cd32c0b…27ea`.

### Numerical results (check N)

The sample uses a non-symmetric, s-dependent field `R(s)=[[0.7+1.3s, 0.4−0.9s²],[−0.25+0.5s, −1.1+2s]]`.

- **Cubic jet residual:** ‖D−sI+(s³/6)R(0)‖/s³ = 0.0344, 0.0173, 0.0087, 0.00436, 0.00218 for s = 0.2 → 0.0125. That is o(s³); the ratio divided by s tends to 0.1747 ≈ ‖R'(0)‖/12, consistent with the next term −s⁴R'(0)/12.
- **Without the cubic term:** ‖D−sI‖/s³ → 0.2127 ≈ ‖R(0)‖/6, which confirms the coefficient −R(0)/6.
- **Area distance:** (√detD − s)/s³ → −trR(0)/12 = 0.0333 (0.0316 at s=0.0125), and det>0 at every s tested.
- **Other checks:**
  - Volterra residual: 0 at 40 digits. With the wrong sign it is 1.0e−2.
  - D''(0) = 0.
  - T9: ‖D'−ODO⁻¹‖ ≤ 6e−42 for both a rotation and a reflection, with zero det difference.
  - T10: ‖D_c−D(cσ)/c‖ = 1.4e−42, and c·√detD_c/√detD(cσ) = 1.
  - η(c²K, L/c) − η(K, L) = 0.

## Blocking findings

None.

## Non-blocking notes and suggested fixes

- **N1. Undeclared transitive import.** `CAS07M04Accepted` imports `CAS07M03Accepted`. That olean was taken from the whole `viii_oracle` directory on LEAN_PATH; it was neither hash-asserted in `raw/run_compile.py` (`ORACLE_OLEANS`) nor listed in AUTHOR_RETURN `imports`. My clean-path compile failed until I supplied it. Its hash `2728fb43…ca9e` does match the accepted CAS-07 records (for example `conditional_synthesis_v1_20261008/RETURN.md`, `jacobi_matrix_majorant_v1_20261007/lean/result.json`). The same LEAN_PATH also exposes the oracle's own `CAS07M05Accepted.olean` (identical hash, shadowed by `raw/imports`).
  - **Fix:** add `CAS07M03Accepted.olean: 2728fb43…` to `ORACLE_OLEANS` and to AUTHOR_RETURN `imports`, or restrict LEAN_PATH to a directory containing only hash-checked oleans.
- **N2. Unrecorded naming deviation.** The frozen text names `JacobiPremises.rotate` and `JacobiPremises.rescale` (dot notation, `(J.rescale c hc)`). The final code has `G01A.rotate` and `G01A.rescale` (`rescale c hc J`). The content is identical (checked by `rfl` and verbatim examples). Record it as a naming-only adjustment.
- **N3. Probes not receipted or mentioned.** `raw/probes/p1.lean` (`#check` lookups, written before the freeze) and `raw/probes/p_kernel.lean` (a kernel-derivative probe) have no receipts and are not mentioned in AUTHOR_RETURN. They are exploratory only; list them.
- **N4. Incomplete author axiom audit.** The author's audit omits 5 declarations: `jacobiField`, `clampR`, `conj`, `conjL`, `ScreenFrameData`. I covered them and all use the standard three axioms; add them to `raw/AxiomAudit.lean`.
- **N5. T10 and T11 are not formally linked.** They are separate theorems, as acceptance item 2 requires, but nothing proves "o·K_σ = c and physical d_A = (o·K_σ)·√det D_c". Only √det of the c=1 normalised matrix is the physical d_A. The prose is not wrong; a formal link would be a strengthening.
- **N6. Inherited η boundary convention.** In Lean, M01 `eta K 0` evaluates to −1 (division by zero), while the source sets η(0)=0 by continuity. This is harmless here: T12 needs L>0, and T10b holds identically at L=0.
- **N7. Tool axes not executed (honestly reported).** wolfram_xact, sympy and sage were not run. The card's sympy "vertex jet exact certificate" is absent; my mpmath check is numerical evidence, not that certificate. Sage's NOT_APPLICABLE status is unadjudicated.
- **N8. Reflection orientation.** T9 uses one O at both screen ends, which matches the source's single transported frame. Independent frames at the two ends (O₁DO₂⁻¹ with det O₁·det O₂ = −1) would flip det's sign; that case is outside scope and should not be claimed.

## Not proved (always)

- **R1:** Lorentzian manifold, Levi-Civita connection, Riemann sign, and `Ropt_ab = R_{aKKb}`.
- **R2:** existence of the affine null geodesic (γ'(0)=−o+n), the screen bundle, parallel transport of an orthonormal frame, and equivalence between the geometric Jacobi field and the matrix solution. Constancy of O between parallel frames is assumed, not proved.
- **R3:** screen-representative change by multiples of K (quotient screen).
- Also not proved: an O(s⁴) remainder, a closed-form cubic constant, FD1–FD3, and the wolfram/sympy/sage axes.
- G01-A as a whole remains PARTIAL. There is no four-axis status change.
- **Scientific admission: HOLD.**

## Suggested VALIDATION_MATRIX scientific-row update (not applied)

`G01-A | g01a_jacobi_vertex_taylor_v1_20261014 | frame-level PARTIAL | independent review PASS_WITH_NOTES (Claude Opus 5.5, 2026-10-14) | recompile exit 0 (Lean 4.31.0, mathlib fabf563a); axioms {propext, Classical.choice, Quot.sound} on 45 decls; frozen==final verified; numerical cubic-jet/dA/T9/T10 check PASS | invariants: sign (T0 definitional) PASS, initial conditions PASS, Taylor order O(s³)+o(s³) jet PASS, det>0 positive branch PASS, O(2) frame covariance PASS, affine rescaling covariance PASS, observer normalization PASS | R1/R2/R3 NOT_PROVED; tool axes NOT_TESTED | notes N1 (M03 olean hash), N2 (naming) | scientific admission HOLD`

## Files

- Reviewed unit: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-01/g01a_jacobi_vertex_taylor_v1_20261014/` (`lean/G01AJacobiVertex.lean`, `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/`)
- My scratch: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g01-a_rerun/`
  - `audit/ReviewAudit.lean`
  - `audit.stdout`
  - `module.stdout`
  - `numcheck.py`
  - `numcheck.out`
  - `out/*.olean`
