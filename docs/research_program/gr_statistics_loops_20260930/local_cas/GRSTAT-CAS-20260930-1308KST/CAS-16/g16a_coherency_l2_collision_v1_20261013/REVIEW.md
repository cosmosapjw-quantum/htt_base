# G16-A — independent review (verbatim final report of a fresh read-only reviewer)

## G16-A fresh independent review: full coherency matrix-field L² collision norm

**Verdict: PASS_WITH_NOTES.** There are no blocking findings. Proof state is independently recompiled. Scientific admission stays on HOLD.

Reviewer model: Claude Opus 5.5 (`claude-opus-5-5`, from my own system prompt; no external attestation). I did not write this task. Review was read-only: no repository file was edited and no git state was changed. I also re-ran the author's sympy script inside T/raw with `python3 -I`; it created no files (no `__pycache__`). All scratch files are under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g16-a_rerun/`.

T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/g16a_coherency_l2_collision_v1_20261013`

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card and package identity | PASS | Zip sha256 `2d0b6da9…af6f` and member `tasks/G16-A.json` sha256 `5a52b0e6…b685` match AUTHOR_RETURN. Card scope: `C J = Γ[−J + 3/(8π) P_e(∫J)P_e]`, gain ≤ 3/2, full ≤ 5Γ/2. Pitfall: no optimality or tilt claims. |
| 1a | Source recovery citations | PASS | Hashes recomputed and all match: DOSSIER_POSITIVE_BRIDGE `00c1fcb0…5ebd` (also equals the CAS-16 contract provenance hash), CAS-16.json `c8c5c20c…86cb`, COMMON_SPEC `4714827e…1897`, Dossier IV PDF `8ce75785…88ef`, C01 ProjectorBridge `e38b8f8a…8abc` (equals C01 RETURN `source_sha256`; C01 review PASS_SCOPED). Line checks: DOSSIER :78 `P_e=I-ee^T`, :195–198 (C1) with Γ=c n_e σ_T, :202 (C2) 5/2 Γ, :204 coherency-not-intensity and tilt excluded, :206 one source tetrad. CAS-16.json :43–44/58–59/79–80 assumptions, :67 exclusions, :72–73 THOM-POL/THOM-TILT. DOSSIER_CLAIMS DP06 confirmed. Dossier IV via `pdftotext -f 13 -l 15`: Eq (74)–(77) complex Hermitian coherency with an `i f_V` term, so a ℂ-valued field is right. Eq (85)–(86) dΩ normalization, Eq (89) `−κ_T F + (3κ_T/8π) S(∫F dΩ′)S` with "multiplication by c" giving Γ=cκ_T, Eq (96) moving electrons, correctly excluded. |
| 1b | Source operator and normalization, by hand | PASS | ∫P_e dΩ = 4π(I − I/3) = (8π/3)I. For an isotropic unpolarized field J=(f/2)P_e, gain = 3/(8π)·P_e·(f/2)(8π/3)I·P_e = J, so it is a fixed point. Trace (photon number) is conserved for every J: ∫tr G dΩ = 3/(8π)·tr(A·(8π/3)I) = tr A. This matches Dossier IV's "angular trace is conserved". Normalized form: (3/2)·∫J dΩ/(4π) = 3/(8π)∫J dΩ. Constants: 3/(8π)·√(4π)·√(4π) = 3/2, and 1 + 3/2 = 5/2. |
| 1c | Normalization, numerically | PASS | Script `num/check.py`, 20×41 Gauss–Legendre × uniform-φ product rule. Weight sum = 4π to 1e-15. sympy gives ∫P_e dΩ = diag(8π/3). Isotropic fixed-point residual 1.8e-15. Trace-conservation residual on a random complex J 7.7e-16. N2 witness residual 6.7e-16. Normalized-operator residual 1.4e-17. On 200 random complex fields: worst gain ratio 1.08 (bound 1.5), worst collision ratio 0.9998 (bound 2.5). Exact norms: ‖gain‖ = √(3/2) = 1.2247, reached at A ∝ I. ‖C‖ ≈ 1.2623 Γ by power iteration on C*C. Both bounds hold and neither is sharp, which is consistent with "no optimality". |
| 1d | T1 complex Frobenius contraction | PASS | Proof splits A = re + i·im. `frob_sq_split` gives ‖A‖² = ‖re‖² + ‖im‖². `sandwich_re` shows PAP commutes with the split because P is real. The C01 `sandwich_frobenius_le` is applied to each part. This covers the card's "real/imag decomposition" route. Statement: unit v, any complex A. |
| 1e | T2 sphere mass 4π | PASS | `dΩ = volume.toSphere`. Mass = 3·vol(B³) = 3·(4π/3) via `toSphere_apply_univ` and `EuclideanSpace.volume_ball_fin_three`; it is proved, not assumed. The bounds use only total mass, because the abstract layer works for any finite μ. |
| 1f | T3 averaged-term Cauchy–Schwarz | PASS | Chain ‖∫J‖ₑ ≤ ‖J‖_{L¹} ≤ μ(univ)^{1/2}‖J‖_{L²} (`eLpNorm_le_eLpNorm_mul_rpow_measure_univ`), then converted to `Real.sqrt (4π) * toReal`. Exactly the card's ‖∫J‖_F ≤ √(4π)‖J‖_{L²}. Assumes `MemLp J 2`, which is needed for `toReal` to mean anything. |
| 1g | T4 gain ≤ 3/2 | PASS | `gain_abstract` gives a pointwise bound \|c\|·‖∫J‖ and an L² bound ≤ μ^{1/2}·\|c\|·μ^{1/2}‖J‖ = \|c\|μ‖J‖. `gain_coeff` gives \|3/(8π)\|·4π = 3/2. Also proves `MemLp` of the gain. |
| 1h | T5 collision ≤ 5Γ/2 | PASS | Triangle inequality on −J + G, then `five_halves`. Uses Γ ≥ 0 as in the contract (Γ = 0 included). Γ < 0 is not covered, consistent with the contract. |
| 1i | T6 bounded operators on Lp 2 | PASS | `gainLin` is ℝ-linear (additivity and smul proved via `integral_add_Lp` and `integral_smul_Lp`). `gainCLM = mkContinuous (3/2)`. `collisionCLM Γ = Γ•(gainCLM − id)`. T6a/T6c tie them a.e. to `thomsonGain` / `thomsonCollision`, so these are the source operator and not stand-ins. Op norms are ≤ 3/2 and ≤ (3/2 + 1)Γ. Non-vacuity checked by me: `gainCLM` on the constant-identity field is a.e. (3/2)P_e, and P_e ≠ 0 (trace 2). |
| 1j | T7 normalized measure dΩ/(4π) | PASS | `dΩnorm = (ofReal 4π)⁻¹ • dΩ` with mass 1. T7b: the coefficient-3/2 operator under dΩnorm equals `thomsonCollision` exactly, for all J. T7c: same constants 3/2 and 5Γ/2 in the dΩnorm L² norm. T7d: the norm scales by (4π)^{-1/2}. |
| 1k | `frobTop` is Mathlib's topology | PASS | My own audit, before any Frobenius instance was enabled: `example : frobTop = (instTopologicalSpaceMatrix : TopologicalSpace CMat) := rfl` and `… = (inferInstance …) := rfl` both compile. I also re-elaborated T5 inline with `(volume).toSphere`, explicit `Pc (fun i => (e:E3) i)` and the explicit 3/(8π) formula, without `frobTop`, and checked it against `collision_L2_bound`: accepted. The author's audit (re-elaboration of T3–T7c without `frobTop`) also passes on my rebuilt oleans. Statements are not silently changed. |
| 1l | Recorded adjustments | PASS (notes 1 and 2) | No weakening relative to the card. Universal over all of L²(S², ℂ^{3×3}), which contains the physical Hermitian/PSD/transverse subset. Full complex coherency is kept; no reduction to intensity. The `frobTop` instance was added after the freeze and is not listed in FROZEN_TARGETS; it is proven harmless (rfl). |
| 1m | Negative controls and witnesses | PASS | N1: v=(2,0,0) gives P = diag(−3,1,1), so ‖P E₀₀ P‖ = 9 > 1; this genuinely shows the unit hypothesis in T1 cannot be dropped. N2: gain of the identity field = (3/2)P_e, matching numerics. Reviewer additions: eLpNorm of the constant 1 is ≠ 0, so T5 instantiates non-vacuously; `gainCLM` is nonzero. |
| 2 | No assumed conclusions, no vacuity | PASS | Hypotheses are only `MemLp J 2`, `0 ≤ Γ`, and unit v. The abstract-layer hypotheses `hP` and `hPm` are discharged by `thomsonP_contract` and `thomsonP_meas` (continuity). Instantiated with J ≡ 1 in my audit. |
| 3a | Hash integrity | PASS | Recomputed sha256 matches AUTHOR_RETURN for: module `da458234…1357`, AxiomAudit `5366720a…b72e`, SOURCE_RECOVERY `dc556a3b…6d25`, FROZEN_TARGETS `4999d3be…a9a0`, run_compile `0301f8ca…9869`, sympy script `c1088e67…92e5`, oleans `aa128464…` and `99e19c61…`, and all six `compile_0*.json` receipt hashes. Snapshot `compile_05_main.source.lean` is byte-identical to the module and `compile_06_audit.source.lean` to AxiomAudit. Every receipt's src/stdout/stderr hash prefix matches. Stderr is empty for all. |
| 3b | Exit codes and failed attempts kept | PASS | compile_01–06 all exit 0. The only stdout warning is the unused `hJ` at :326. Failed probes are kept: p01, p03, p05, p06, p07, p08, p10 (exit 1); p02, p04, p09, p11, p12 exit 0. |
| 3c | Axioms | PASS | My audit enumerates all 53 non-internal `G16ACoherency.*` constants with `Lean.collectAxioms`. Every one is exactly `[propext, Classical.choice, Quot.sound]`; this includes C01 transitively. The author's 39 `#print axioms` lines re-run on my oleans are identical to `compile_06_audit.stdout`. |
| 3d | Forbidden tokens | PASS | `grep -nE 'sorry\|admit\|native_decide\|^\s*axiom\|set_option\|sorryAx\|implemented_by\|extern\|unsafe\|csimp'` over the module, AxiomAudit and ProjectorBridge finds nothing. My audit file has no `sorry`. |
| 4 | Independent recompile | PASS | Toolchain: `lean-toolchain` v4.31.0, `lake env lean --version` 4.31.0 (commit 68218e87), manifest mathlib rev `fabf563a…911f`. From cwd `/home/cosmosapjw/lean_oracles/viii_oracle`: (1) bridge rebuilt from source copy, `lake env bash -c "lean -R $R/bridge_src -o $R/imports/ProjectorBridge.olean …"`, exit 0, olean `99e19c61…`, byte-identical to the author's. (2) Main: `lake env bash -c "LEAN_PATH=$R/imports:$LEAN_PATH lean -R $R/main_src -o $R/imports/G16ACoherency.olean $R/main_src/G16ACoherency.lean"`, exit 0, same single warning. (3) Author AxiomAudit on my oleans, exit 0. (4) My `audit/ReviewAudit.lean`, exit 0 (output `ReviewAudit.v4.out`; v1–v3 were my own failed audit drafts, kept). |
| 5 | Scope and pitfalls | PASS | No claims of optimality, tilted/moving electrons, physical Γ = c n_e σ_T, Hermitian/PSD preservation, or Boltzmann/LoS statements. Admission is recorded as `AUTHOR_COMPILED_UNREVIEWED` / `NOT_PUBLISHED` / `HOLD`. |

### Blocking findings
None.

### Non-blocking notes (with suggested fixes)
1. **`frobTop` was added after the freeze but is not disclosed in FROZEN_TARGETS.** It is absent from both the p02 signature probe and the "Fixed definitions (verbatim)" block. It is harmless (rfl to `instTopologicalSpaceMatrix`, reproduced by me). Fix: add a "post-freeze adjustment" line to FROZEN_TARGETS or AUTHOR_RETURN naming `frobTop`, its reason (instance synthesis), and the rfl audit.
2. **One freeze-ordering sentence is inaccurate.** FROZEN_TARGETS says "No proof was attempted before freezing". But p01 (mtime 11:42:52Z, before the FROZEN mtime 11:46:08Z) contains a partial tactic proof of the T2 statement (failed, `sorry`). Statement content is unaffected. Fix: reword to "only a Mathlib-name/tactic probe (p01) preceded freezing".
3. **Freeze precedence rests only on file mtimes.** T is untracked in git (`?? …/g16a_…/`). FROZEN (11:46:08Z) predates the first main compile (11:55:30Z). Only the unchanged C01 import compile (11:41:58Z) and probes p01/p02 come before it.
4. **T7b `normalized_operator_eq` has an unused hypothesis `hJ`.** The identity holds for every J. This is harmless and weaker than what is provable; it causes the only compiler warning.
5. **`gainCLM` and `collisionCLM` are ℝ-linear, not ℂ-linear.** The operator-norm bounds are the same either way. ℂ-linearity is not claimed.
6. **The `wolfram_xact` tool task (a CAS-16 required axis) was not executed.** The author's sympy script only does constant arithmetic; it does not check ∫P_e dΩ = (8π/3)I or the isotropic fixed point. My numeric check covers this, but it is not a Lean theorem. Optional strengthening: a Lean lemma `∫ thomsonP dΩ = (8π/3)•1`, which would give number conservation and the isotropic fixed point formally.
7. **Instance fragility for downstream users.** Without `frobTop`, `Integrable J dΩ` fails to elaborate (`ContinuousENorm CMat` synthesis failure, seen in my `ReviewAudit.v2.out`). `MemLp`-based statements do elaborate. Downstream consumers need the same local instance setup.
8. **Main olean bytes depend on the build path.** My rebuilds give `4b44e4b1…` and `c629a328…`, versus the author's `aa128464…`. The bridge olean is path-independent. The author's "byte-identical" claim holds only for same-path rebuilds; this is not an integrity defect.
9. **Bounds are valid but not sharp.** True ‖gain‖ = √(3/2) and ‖C‖ ≈ 1.262Γ, versus 3/2 and 5Γ/2. This is consistent with the card's no-optimality pitfall.
10. **The physical shape of `volume.toSphere` is not separately proven.** That it is the rotation-invariant area measure is standard Mathlib but not proven here. It affects only operator-identity semantics; the bounds use total mass only.

### Not proved / not claimed
- **Scientific admission: HOLD.**
- Optimality of 3/2 or 5Γ/2.
- Tilted or moving-electron Thomson operator (Dossier IV Eq. 96, THOM-TILT).
- Physical identification Γ = c n_e,rest σ_T.
- Hermitian, PSD or transversality preservation.
- THOM-POL loci; spin-quadrature generalizations.
- Any Boltzmann, radiative-transfer or LoS statement.
- Number conservation and the isotropic fixed point as Lean theorems (numeric only, by me).
- The `wolfram_xact` axis.
- Publication readiness.

### Files
- Author artifacts under T: `lean/G16ACoherency.lean`, `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/AxiomAudit.lean`, `raw/compile_0[1-6]_*`, `raw/probes/`.
- Reviewer scratch (`$R` = `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g16-a_rerun`):
  - `$R/audit/ReviewAudit.lean` and `$R/audit/ReviewAudit.v4.out` (final audit and output)
  - `$R/author_audit/out.txt` (author audit re-run on my oleans)
  - `$R/num/check.py` (numeric check)
  - `$R/imports/` (rebuilt oleans)
  - `$R/r_main.out` (main compile output)
  - `$R/pdf/iv.txt` (Dossier IV pp. 13–15 text)

### Suggested VALIDATION_MATRIX scientific-row update (not applied)
`G16-A | scientific | PASS_WITH_NOTES (fresh independent review, claude-opus-5-5) | 15/15 frozen targets recompiled (Lean 4.31.0 / mathlib fabf563a), 53 decls axioms = {propext, Classical.choice, Quot.sound}, frobTop ≡ instTopologicalSpaceMatrix by rfl; 3/(8π)(dΩ) ≡ 3/2 (dΩ/4π) verified by hand + numerically (isotropic fixed point 1.8e-15, trace conservation 7.7e-16); true norms √(3/2), ≈1.262Γ ≤ bounds | notes: frobTop post-freeze undisclosed, wolfram_xact NOT_EXECUTED | scientific admission HOLD`
