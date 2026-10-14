# P05-A — independent review (verbatim final report of a fresh read-only reviewer)

# P05-A independent review: orbit curvature and eigenframe connection

**Verdict: PASS_WITH_NOTES.** The pass covers only the finite Lie-algebra model with a constant orthonormal frame. Nothing blocks it.

Reviewer: Claude Opus 5.5 (`claude-opus-5-5`), the model named in my system prompt. The card's review policy asks for `gpt-6-astra/ultra`, so the requested reviewer identity was **not** matched. This is a fresh, read-only review, and I did not author P05-A. I edited no repository files and ran no state-changing git commands. I wrote only to `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p05-a_rerun/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-05/orbit_curvature_eigenframe_v1_20261014`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card identity | PASS | Card member sha256 is `0d31538c…0427` and zip sha256 is `2d0b6da9…af6f`. Both match SOURCE_RECOVERY and AUTHOR_RETURN. |
| 0b | SOURCE_RECOVERY citations | PASS | I recomputed every cited hash: CAS_CONTRACT `904d95fe…`, PORT_MAP `d0050aa3…`, CLAIMS `5d7280b7…`, wolfram_curvature.wl `60cd5e1d…`, wolfram_curvature.json `5b469e8b…`, relativistic_kinematics.py `9ae767f9…` (last commit `bc45fb92`). I checked each cited line: CAS_CONTRACT 4/63/65/66; PORT_MAP 253/261, 266/273, 278/285; CLAIMS 67, 89–93, 106–107, 126–130, 143–145; py 248/256/258, 262/268/276, 363/385/386/388. All are verbatim. |
| 1a | C^k_ij convention matches the sources | PASS | Lean `Cna k i j = Σ_l ε_ijl n_lk + a_i δ_kj − a_j δ_ki` is Wolfram line 3 after renaming i→k, j→i, k→j. This is the Ellis–MacCallum form, with `[e_i,e_j] = C^k_ij e_k` (Python `C[k,i,j]`). sympy gives `traceForm = 2a`, which matches the convention a_i = ½ C^k_ik. |
| 1b | Koszul index order | PASS | Lean `koszul k i j = (C_kij − C_ijk + C_jki)/2` is the same as Python line 276 and Wolfram line 4. It equals ⟨∇_{e_i}e_j, e_k⟩. sympy confirms it is metric-compatible (`Γ^k_ij = −Γ^j_ik`) and torsion-free (`Γ^k_ij − Γ^k_ji = C^k_ij`). T1c proves uniqueness, so this is derived rather than postulated. |
| 1c | Riemann and scalar contraction | PASS | `riem` follows from R(e_j,e_k)e_l = ∇_j∇_k e_l − ∇_k∇_j e_l − ∇_[e_j,e_k] e_l with constant coefficients, and matches Wolfram line 5. `scal` is the sum of sectional curvatures, positive on a sphere. |
| 1d | R3 = −tr(n²) + (tr n)²/2 − 6a·a | PASS | **By hand:** n=1 gives −3 + 9/2 = 3/2, the known value for SU(2) with unit structure constants. diag(1,1,5) gives −27 + 49/2 = −5/2. diag(1,1,6) gives −6. Type V with a=(1,0,0) gives −6, as for H³. **sympy, general symmetric n and arbitrary a:** `scal − closed = 0` identically. **Independent route (genuine left-invariant metrics in coordinates, Christoffel-based scalar curvature):** type IV −13/2, VII_h(1/3,2) −2/3, VI_h −13/2, V −6, VI0 (Sol) −2, Nil −1/2. In each case coordinate R equals the closed form equals the Koszul-algebraic value. |
| 1e | Where n a = 0 is used | PASS | sympy: Jacobi residual = −2 ε_jkl (n a)_i (T3a), and Ric_pq − Ric_qp = 2 ε_pqr (n a)_r (T4b). The scalar formula holds without n a = 0. This also follows from SO(3) invariance: no quadratic scalar can contain n·a. It is consistent with the Wolfram evidence, where ScalarCurvature has no a·n1 term while Jacobi123 = −2 a n1. A3 records this honestly. T4 keeps the card's hypothesis, and T4′ is a separately named lemma with weaker hypotheses and the same conclusion. |
| 1f | Γ^j_ki = D_kT_ij/(λ_i − λ_j) | PASS | sympy: DT_kij = (λ_i − λ_j) Γ^j_ki for diagonal T, using metric compatibility. Lean T7 matches the CAS-05 index order and Python line 385 (`g[j,k,i] = dt[k,i,j]/(lam[i]−lam[j])`). T9a's `reconC` matches Python line 386. T7 holds for any metric-compatible Γ and needs only the gap of the pair involved, which is a strengthening. |
| 1g | Collision branch | PASS (note N3) | T8: λ_i = λ_j forces DT_kij = 0 for every metric-compatible Γ, so the equation reads 0 = 0·Γ. T8w is a genuine non-uniqueness witness: types I and IX with T = δ have identical DT, but Γ²_01 is 0 versus 1/2. My instantiation `DT (koszul (Cna 1 0)) (diagonal ![1,1,2]) 2 0 1 = 0` compiles. |
| 1h | Bianchi-label controls | PASS (note N4) | T10a: abelian C=0 and VII0 diag(1,1,0) both have R3 = 0, and C^0_12 = 1 ≠ 0. T10b: IX diag(1,1,6) and V a=(1,0,0) both have R3 = −6, with trace form 0 versus 2 (unimodular versus class B). T10c: IX gives both +3/2 and −5/2. No R3 > 0 ⇒ IX claim is made. |
| 1i | Negative control T4n | PASS | n0 = E01 (not symmetric) gives scal = −2, while the formula evaluated with n0 gives 0, so the symmetry of n is load-bearing. Cross-check: the canonical decomposition of the same C is n_s = ½(E01+E10) with a = (0,0,−½). The closed form then gives −½ − 3/2 = −2, which agrees. The control therefore shows a convention constraint, not a defect. |
| 1j | Units | PASS | T5: R3(s n, s a) = s² R3, consistent with n, a ~ 1/L and R3 ~ 1/L². |
| 1k | Pitfalls | PASS | Nothing identifies this curvature with a rotating rest-bundle slice. The module docstring and FROZEN_TARGETS disclaim it. No Bianchi label is drawn from one R3 value. |
| 1l | Amendments A1–A4 | PASS (non-semantic) | A1 (`noncomputable section`) affects code generation only. A2 adds helper slices; I diffed attempts 02, 03 and 05, and the final T3a/T4b statements are unchanged. A3 and A4 keep the card's hypotheses, which are unused but present. Attempt 02 already contained all 26 targets plus `reconGamma_eq`, so no target was added after the fact. |
| 2 | No circularity or vacuity | PASS | No hypothesis restates its conclusion. My audit file instantiates the hypotheses. `scal_Cna` holds for n = diag(0,0,1), a = (1,0,0): n a = 0, n ≠ 0, a type-IV-like class B case. `n a = 0` fails for n = 1, a = e0, so the iff theorems are not trivial. `structure_from_DT` holds on IX with λ = (0,1,2) and injectivity proved. T7w is the non-vacuity witness for the gap formula. |
| 3a | Hashes | PASS | I recomputed every source, receipt source/stdout/stderr and olean listed in AUTHOR_RETURN, and all match. EigenframeGap.lean is `de20d2e4…6268`, unchanged. |
| 3b | Exit codes and failed attempts | PASS | Receipts 01 (import, 0), 02 (main, 1), 03 (main, 1), 04 (probe, 0), 05 (main, 0) and 06 (audit, 0) are all kept with source snapshots. The 02/03 stdout shows the noncomputable error and the 200000-heartbeat timeout. Interrupted-run artifacts are dated 06:56–07:04 KST and the resumed run 11:40–11:44 KST; numbering continues at 04. |
| 3c | Freeze timing | PASS (note N2) | FROZEN_TARGETS mtime is 21:59:57Z. The first proof compile (02) started at 22:02:28Z. Receipt 01 (21:56Z) only builds the prior import. |
| 3d | Forbidden constructs and axioms | PASS | In T/lean and the import source, grep finds no `sorry`, `admit`, `native_decide`, `axiom`, `set_option`, `maxHeartbeats`, `unsafe`, `implemented_by`, `extern`, `opaque` or attributes. The only hit is a docstring line in EigenframeGap. In my own audit, all 39 public theorems depend on exactly `[propext, Classical.choice, Quot.sound]`. |
| 4 | Independent recompile | PASS | Run from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` with toolchain `v4.31.0` and mathlib rev `fabf563a…` (from lake-manifest). EigenframeGap rebuilt from source exits 0, and its olean is byte-identical (`f0a0b7d5…`). The main module, rebuilt with `lake env bash -c "LEAN_PATH=<scratch>/imports:$LEAN_PATH lean -R <scratch>/src -o <scratch>/imports/OrbitCurvatureEigenframe.olean <scratch>/src/OrbitCurvatureEigenframe.lean"`, exits 0 with 5 warnings and 0 errors, the same as the author's run. My `audit/ReviewAudit.lean` (39 `#check` and `#print axioms` plus 4 instantiation examples) exits 0. The `#check` signatures match every FROZEN_TARGETS statement. |
| 4b | Author numeric cross-check | PASS (not a proof) | I copied the script to scratch and reran it. It exits 0 and its JSON is byte-identical (`d3ba8484…`). |

## Blocking findings
None.

## Non-blocking notes
- **N1. Overwritten numeric runs.** Three earlier runs of `raw/numeric_crosscheck.py` were overwritten: two shim import errors, and a transpose bug in the script's own koszul reimplementation. Severity is low. The script is ancillary and not proof evidence, the failures were disclosed, and the final run reproduces byte-identically. It still departs from the keep-every-attempt rule, and the Python run has no argv/cwd/exit JSON receipt (only `.exit` plus AUTHOR_RETURN). Fix for future runs: route Python ancillaries through a receipt harness like `run_compile.py`.
- **N2. Freeze and "unchanged" rest on filesystem mtimes.** T is entirely untracked in git, and no content hash of FROZEN_TARGETS was recorded before the interruption. The evidence is consistent: the mtime predates the first compile, and the attempt-02 source already holds the same statement set. Fix: commit T, or record a pre-compile freeze hash in future runs.
- **N3. Collision witness is the fully degenerate case only.** T8w uses T = δ. Partial-collision non-uniqueness, where only one pair is degenerate, is covered by T8 but has no explicit two-algebra witness. Optional strengthening.
- **N4. Class labels are not proved invariant.** The class witnesses (C = 0, trace form, sign pattern of n) are not proved to be Lie-isomorphism invariants, and "IX" for diag(1,1,6) is not formally established. This is disclosed. Mathematically standard (tr ad is an iso-invariant), but outside the formal scope.
- **N5. Main olean is not byte-reproducible.** Mine is `0745d86a…`; the author's is `c2d1dbca…`. The evidence is source plus exit 0 plus axioms, not the olean bytes.
- **N6. Python guard is stricter than the theorem.** `homogeneous_scalar_curvature` rejects n a ≠ 0 even though the formula does not need it. This is a validity guard (Jacobi is required for a Lie algebra), not a contradiction, and no code change is suggested.
- **N7. Card tool_tasks not run.** The `wolfram_xact` and `sage_singular` tasks were not executed. The supplied homogeneous-neighborhood instance is not formalised. Both are disclosed.

## Not proved (scientific admission: HOLD)
- Manifold Levi-Civita on a simply transitive spacelike G3 orbit (the bridge from left-invariant frames to constant-component Koszul, and e_k(T_ij) = 0).
- Homogeneity on an open neighborhood.
- Spacetime versus slice action.
- Any identification with rotating rest-bundle slice curvature.
- R3 > 0 ⇒ IX (BIC-02).
- Any Bianchi label from an R3 value.
- Lie-isomorphism invariance of the witnesses.
- Correspondence between sky morphology and the tensor.
- Numerical stability near eigenvalue collisions.
- Wolfram/xAct and Sage/Singular engine runs.
- Proof admission beyond FORMALLY_CHECKED_SCOPED.
- Publication admission: HOLD.
- **Scientific admission: HOLD.**

## Suggested VALIDATION_MATRIX scientific row (for the owner to apply; I did not edit it)
`P05-A | CAS-05 R3 trace form + eigenframe Γ formula | Lie-algebra/constant-orthonormal-frame model | units PASS (T5), sign/normalization PASS (SU(2) 3/2, H³ −6, Nil −1/2, Sol −2, IV/VI_h/VII_h coordinate-metric match), Jacobi⇔na=0 PASS, Ricci symmetry⇔na=0 PASS, scalar independent of na PASS, collision branch PASS, label controls PASS | manifold bridge NOT_TESTED | independent review: claude-opus-5-5 PASS_WITH_NOTES (requested gpt-6-astra not matched) | scientific admission HOLD`

## Files
- Reviewed: `T/FROZEN_TARGETS.md`, `T/SOURCE_RECOVERY.md`, `T/lean/OrbitCurvatureEigenframe.lean`, `T/AUTHOR_RETURN.json`, `T/raw/compile_0{1..6}_*`, `T/raw/AxiomAudit.lean`, `T/raw/numeric_crosscheck.py`
- My scratch evidence:
  - `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/p05-a_rerun/audit/ReviewAudit.lean` and `ReviewAudit.out`
  - `…/p05-a_rerun/rc_main.out` and `…/p05-a_rerun/rc_gap.out`
  - `…/p05-a_rerun/indep_check.py` (sympy symbolic and coordinate-metric checks)
  - `…/p05-a_rerun/numeric/numeric_crosscheck.json`

