# G17-A — independent review (verbatim final report of a fresh read-only reviewer)

# G17-A fresh independent review (scaling and conformal source definitions; CAS17-C02/C03 at chart level)

**Reviewer runtime:** claude-opus-5-5, running as a read-only subagent. I did not author this unit. I edited no repository files and ran no state-changing git commands. Scratch files are only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-a_rerun/`.

## Verdict: PASS_WITH_NOTES

- **Proof status:** every frozen target T1–T7 and every negative control is kernel-checked at the declared chart/frame level. My independent recompile succeeded, and every declaration depends only on `propext`, `Classical.choice` and `Quot.sound`.
- **Blocking findings:** none.
- **One provenance correction is required:** a wrong file:line citation (F1 below). It does not affect any proof.
- **Two typed bridges remain unchained:** `slope_scale` and `tidal_op_scale`. They are disclosed and are not circular (N1, N2).
- **Scientific admission:** HOLD.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read | PASS | `unzip -p …PACKAGE.zip …/tasks/G17-A.json`. I read the scope, the 4 lean_steps, the 4 acceptance items and the pitfall "no new arbitrary definitions". |
| 1a | Source hashes | PASS | Recomputed sha256 matches SOURCE_RECOVERY/AUTHOR_RETURN for all 7 sources: CAS-17.json `123c73d5…`, COMMON_SPEC `4714827e…`, DOSSIER `00c1fcb0…`, NATIVE `e2158368…`, ADDED_BOOK `977125a6…`, OPTICAL `5ae2b6a6…`, FINITE `d499eb7f…`. |
| 1b | Line citations | PASS with one error (F1) and one inaccuracy (N6) | I read every cited line. Correct: FINITE:7, 9–11, 15–18, 59–63; OPTICAL:9, 11–15, 17, 22–23, 31–35, 40, 44, 48; COMMON_SPEC:4–8, 14, 16, 18, 19, 23; NATIVE:9, 11, 17, 25, 31–35, 51, 53–54, 56–65; ADDED_BOOK:46–56, 58–77, 79, 83–88, 92–96; CAS-17.json:48–49, 56, 61–67, 78–88, 119–120, 269–271; DOSSIER:10; `relativistic_kinematics.py:216–231`. **Wrong:** NATIVE:114–119 and NATIVE:119 (calibration offset κ, rescaling of r, H, Kc, M2, L). Those lines are Theorem N2 and the A=0 rejection text. The cited content is actually at NATIVE:173–178 (eq. 15 and the joint Kc, M2, L rescaling). |
| 1c | Z fixed exactly | PASS | Z = 1+z, not z, everywhere: FINITE:7 (`Z(s,n)=1+z=u.K`), OPTICAL:22/44, COMMON_SPEC:16 (`Z0=lim(1+z)`), NATIVE:32 (`m_zi = Z_i - 1`). ADDED_BOOK:95 (`1+z'=e^{φo-φe}(1+z)`) and CAS-17.json:271 (`Zprime=e^(phi_o-phi_e)Z`) agree only if Z=1+z. In Lean, `onePlusZ = ν_e/ν_o` and `zOf Z = Z-1`. |
| 1d | Frozen before first proof compile | PASS (evidence is mtime only) | FROZEN_TARGETS.md mtime is 17:47:09Z. compile_05_core (first proof) started 17:51:30Z. compile_01–04 ran before the freeze, but they are import builds plus an API probe (`p01_api.lean` is `#check` only). The directory is untracked in git, so there is no commit anchor. Frozen sha `1a702ea4…` matches. |
| 1e | Final statements equal frozen statements | PASS | My `ReviewAudit.lean` restates the frozen T1–T7, NC and witness signatures as `example`s closed by the G17A declarations; all elaborate (exit 0). Theorem headers in compile_05/06 vs final are unchanged (only proofs differ). Disclosed deviations are acceptable: `remBound_scale` takes `0<lam` (the contract domain is λ>0), and `intercept_formula` takes `n.t=0`. |
| 1f | Faithfulness of C02 to card/CAS-17 | PASS | (i) Γ invariant. (ii) Bcov → λB; tetrad B → λ⁻¹ (`tet2` with λ⁻¹E). (iii) A^a → λ⁻²; A_b invariant; measured A and Euclidean measured norm → λ⁻¹. (iv) Riemann (1,3) invariant. (v) I = Z0 and β invariant (frame level via C01, `betaSqW lorentz = betaSq` by `rfl`). (vi) Observer normalization forces μ=λ⁻¹; `affine_reparam` gives r_λ = λr, tangent λ⁻¹K and the geodesic equation of λ²g. (vii) d_A → λ through `G01A.jacobi_unique`; Kc → λ⁻²Kc and L → λL carried by `G01A.rescale`'s `curvature_bound`. (viii) M2 → M2/λ² on [0,λL]. (ix) Dom5/Dom6 are iff-invariant under the joint rescaling. (x) Modulus offset κ' = κ − 5 log10 λ with positive log arguments and a declared ℓ = 10 pc. (xi) zMean invariant. All of this matches ADDED_BOOK:46–77, NATIVE:173–178 and CAS-17.json:269–270. By hand, the dimension exponents agree with measured units: H, B_tet, \|A\| ~ length⁻¹; Kc, M2 ~ length⁻²; L, d_A ~ length; Z, β dimensionless. |
| 1g | Faithfulness of C03 | PASS | `chris` is *defined* from `fderiv` of g (`pd g x b d c = ∂_b g_dc`). The conformal law Γ' = Γ + δ^a_c∂_bφ + δ^a_b∂_cφ − g_bc g^{ad}∂_dφ is *proved* from the product rule (`pd_expsmul`) and `ginv_conf`; nothing is assumed. A' = e^{-2φ}(A + c²h^{ab}∂_bφ) follows from the general weighted law (`conformal_selfCov`, m=−1) plus the pointwise normalization g(U,U) = −c². The redshift law is 1+z' = e^{φo−φe}(1+z) from U' = e^{−φ}U with the same eikonal covector (ADDED_BOOK:92). Hypotheses (differentiable at x, nondegenerate at x) are weaker than the source's smoothness, so this is a strengthening. |
| 1h | Independent symbolic/numeric check | PASS | `py/conf_check.py` and `conf_check2.py` (sympy, exact rationals) implement the same component definitions on a generic non-diagonal 4D metric with nonpolynomial φ. Conformal Christoffel max error `0.e-173`. Flipping the sign of the last term gives error 1.96, so the check discriminates. Weighted selfCov law for m ∈ {−1, −2, 1/3}: error `0.e-165`. A' formula with U normalized at the point: error `0.e-165`, and g(U,U)+c² = 0. Constant scale: Γ difference exactly 0; A^a ratio 0.18367… = λ⁻² for λ = 7/3 in all 4 components. |
| 1i | Negative controls genuine | PASS (SCALE-INF is weak, N4) | **CONF-GRAD:** flat η, U = c e0, φ = x¹. φ(0)=0 and A¹=0, but A'¹ = c². This instantiates `conformal_accel` with real hypotheses, and I checked it by hand: Γ'^1_00 = −g_00 ∇¹φ = 1. **SCALE-FIXEDBOUND:** Dom5 with fixed Kc=M2=0, L=1, H=0 holds at r=1 and fails at r=2. **SCALE-INF:** pure arithmetic; it carries meaning only together with `A_measNorm_scale`. |
| 2a | Hypotheses do not assume conclusions | PASS with bridges N1/N2 | No transformation law of Γ, A, B, ν, 1+z, d_A, Kc, M2, L or κ enters as a hypothesis. `dA_scale`'s `hR` (R scaling) is not one of the source's displayed laws, and `tidal_op_scale` derives it. `slope_scale`'s `hrel` and `tidal_op_scale`'s `hJl` are typed bridges; see N1 and N2. |
| 2b | Non-vacuity | PASS | Witnesses: `minkowski_witness`, CONF-GRAD (uses `conformal_accel`, hence `conformal_selfCov` and `conformal_christoffel`), `straight_line_geodesic` (`affine_reparam`), `dA_scale_witness` (`hR` met by `G01A.rescale`), `tidal_flat_witness`. I added three more: `slope_scale` with nonzero slope (zf = (H/c)D, zl = (λ⁻¹H/c)D); the chain `dA_scale ∘ dA_scale_witness` on `G01A.flatJacobi`; and `lower (conf φ g) (e^{-2φ}k) = lower g k`, which shows the "same eikonal covector" convention agrees with the null rescaling in `conformal_null_affine`. All compile. |
| 3a | Receipt integrity | PASS | For all 12 receipts, sha256 of `.source.lean`, `.stdout` and `.stderr` matches the JSON. Exit codes: 01–03 = 0; 04 = 1 (probe); 05, 06 = 1 (failed proofs, kept); 07–12 = 0. Final sources equal compile_07 (core) and compile_11 (optics) byte-for-byte. The `set_option` tried in compile_08 is absent from the final sources. Failed-attempt error lines match the AUTHOR_RETURN `first_failure` text. |
| 3b | Import identity | PASS | C01.lean `934e6a96…`, M05 Main.lean `0e10bfac…` and G01AJacobiVertex.lean `6c1f7a66…` are unchanged. G01A and C01 are git-clean. Oracle oleans M01 `83acab45…`, M04 `81e374aa…` and C02 `67344c6d…` match. Toolchain is `leanprover/lean4:v4.31.0`, mathlib rev `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. |
| 3c | Forbidden constructs | PASS | grep over `T/lean/*.lean` for `sorry`, `admit`, `native_decide`, `axiom`, `set_option`, `implemented_by`, `extern`, `unsafe`, `opaque`, `decide`: 0 hits. |
| 3d | Axioms | PASS | My audit printed 120 `#print axioms` lines, covering all 119 top-level declarations plus `orthonormal_scale.velocity_norm_scale_gen`. All are `[propext, Classical.choice, Quot.sound]`. The author's compile_12 printed 115 with the same set; it only `#check`s the 5 type declarations. |
| 4 | Independent recompile | PASS | From cwd `/home/cosmosapjw/lean_oracles/viii_oracle`, each module built with `lake env bash -c "LEAN_PATH=<rerun>/out:<oracle>:$LEAN_PATH lean -R <rerun>/src -o <rerun>/out/<M>.olean <rerun>/src/<M>.lean"`. Imports were rebuilt from source in order C01 → CAS07M05Accepted → G01AJacobiVertex → G17ACore → G17AOptics. All exit 0 with empty stderr. Resulting oleans match the author's bit-for-bit for C01 `e34f0779…`, M05 `694b6683…` and G17AOptics `babe4cae…`. G01A and G17ACore differ only because of the `-R` root path: recompiling G17ACore with `-R T/lean` reproduces the author's `dd3ba3b4…` exactly. `ReviewAudit.lean` exits 0. |
| 5 | Type separation (card lean_step 2) | CONCERN, non-blocking | `Contra`, `Cov` and `Measured` wrapper types exist and are used for the acceleration outputs and tetrad vectors. However, `Bcov`/`tet2` return bare ℝ, `lower` returns `Pt n` (the same type as contravariant), U and u share `Pt n → Pt n` (`physVel` is just a map), and "length-valued coordinates" is documentation only (`chartPoint` is used by no theorem). Separation is enforced by distinct definitions and theorem statements, and I found no mixing of coordinate and measured scalings. Lean ℝ carries no units. |

## Blocking findings

None.

## Required correction (provenance only, no proof impact)

- **F1:** In `T/SOURCE_RECOVERY.md`, the rows "calibration offset κ" (`NATIVE:114-119`) and "constant-scale laws" (`NATIVE:119`) cite the wrong lines. Change them to `statistics/NATIVE_INFERENCE_THEOREMS.md:173-178` (eq. (15) and the joint Kc/M2/L rescaling). Make the same fix in `T/AUTHOR_RETURN.json` → `source_recovery.citations` (`…:9-17,25,29-35,51-65,114-119` → `…,173-178`). The recovered content is correct; only the line pointer is wrong.

## Non-blocking notes

- **N1 – `slope_scale` bridge `hrel : ∀ D≥0, zl(λD) = zf(D)`.** This does not hide the conclusion: the factor λ⁻¹ comes from the chain rule. But `hrel` is the composite of two transformations the source displays (D_A → λD_A and endpoint ratio invariance). Both are proved separately (`dA_scale` at the G01A frame level; `redshift_const_scale` plus `affine_reparam` at the chart level) but never formally composed. So H → λ⁻¹H is formally conditional on that composition, as disclosed in `not_claimed`.
  - Optional strengthening that needs no inverse function: define H via the affine parameter, H = c·dZ/ds|₀ / (d d_A/ds|₀) with d d_A/ds(0)=1, then chain `M2_identity`-style reparametrization with `dA_scale`.
  - `M2_scale` has the same implicit identification: the scaled-ray Z is written into the statement as Z(λ⁻¹·).
- **N2 – `tidal_op_scale` bridge `hJl`.** It identifies the scaled spacetime's G01-A operator with `tidalMat` built from the same `Rm` array, the λ⁻¹ frame and the λ⁻¹ tangent at the reparametrized point. Not circular: λ⁻² comes from `tidal_scale`, and "same Rm" is what `riemann_scale` proves for Rm = `riemann g`. But the chain from `riemann_scale`, `orthonormal_scale` and `affine_reparam` into `hJl` is not formalized, and the λ⁻¹ screen frame is not proved to be parallel transported. This matches the author's modelling inputs 2–3.
- **N3 – `dA_scale` requires `Jl` to carry exactly the indices (λ⁻²Kc, λL)** because `jacobi_unique` needs equal indices. A version allowing any `Kc'` would be slightly stronger. Not required.
- **N4 – SCALE-INF (`scale_inf_no_floor`) is pure real arithmetic.** It represents the exclusion "no scale-independent positive A floor" only when read together with `A_measNorm_scale`. It would be cleaner stated directly on `measNorm(tetVec …)`.
- **N5 – Frozen-before-compile evidence is mtime only.** T is untracked in git, so there is no commit anchor.
- **N6 – SOURCE_RECOVERY says "the first five hashes equal the reviewed freeze",** but the freeze table lists four sources (CAS-17.json, DOSSIER, NATIVE, ADDED_BOOK). COMMON_SPEC is not in it, though its hash does match the current file.
- **N7 – `redshift_const_is_special_case` states the result with the cosmetic factor exp(log λ − log λ).** It is valid and derived from `conformal_redshift`. For C02, the scaled covector is k_λ = λk, not the same k; the ratio is invariant either way.
- **N8 – Code defect vs method limitation.** No code defects found. The limitations are methodological and disclosed: single-chart pointwise statements; no manifold or atlas; no existence of geodesics or Jacobi fields from the metric; unchained bridges N1/N2.

## Not proved (outside this unit)

- **Scientific admission: HOLD.**
- Manifold/atlas-level Lorentzian formalization; existence of null geodesics, Jacobi fields or caustic-free segments derived from g.
- Parallel transport of the λ⁻¹ screen frame as an ODE statement.
- Formal chaining of z(d_A) along an actual ray (N1), and of the G01-A operator to the manifold tidal operator (N2).
- D_L scaling and reciprocity/transparency; A_cov = 2c B u; ∇g = 0 as a separate lemma.
- Any general-conformal same-calibrated-data claim (excluded by CAS-17.json:80).
- Calibration availability and the absolute distance scale.
- Historical four-axis (Wolfram/xAct, SymPy, Sage) adjudication. My sympy check is a reviewer cross-check, not a CAS_4AXIS verdict.
- Real-data fitting and production enablement.

## Suggested VALIDATION_MATRIX scientific row (not written by me)

`G17-A | CAS17-C02/C03 chart-level | PASS_WITH_NOTES (fresh independent review, claude-opus-5-5) | Z=1+z fixed; Γ from fderiv; conformal Γ, A' and 1+z' derived and sympy-confirmed (err ≤1e-164); constant-scale B/A/Riemann/d_A/Kc/M2/L/κ/Dom5-6 proved; CONF-GRAD and SCALE-FIXEDBOUND genuine; SCALE-INF arithmetic only; bridges: slope_scale hrel, tidal_op_scale hJl (unchained, disclosed); provenance fix F1 (NATIVE:173-178); axioms {propext, Classical.choice, Quot.sound}; independent recompile exit 0, Optics olean bit-identical | scientific admission HOLD`

## Files

- Reviewed unit: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/g17a_scaling_conformal_formal_v1_20261014/` (SOURCE_RECOVERY.md, FROZEN_TARGETS.md, AUTHOR_RETURN.json, lean/G17ACore.lean, lean/G17AOptics.lean, raw/).
- Reviewer audit: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-a_rerun/src/ReviewAudit.lean`
- Recompile logs and exit codes: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-a_rerun/logs/` (exits.txt, audit.out)
- Rebuilt oleans: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-a_rerun/out/`
- Sympy checks: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-a_rerun/py/conf_check.py` and `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g17-a_rerun/py/conf_check2.py`
