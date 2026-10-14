# G15-B — independent review (verbatim final report of a fresh read-only reviewer)

# G15-B fresh independent review: sphere divergence, IBP and rank ≤ 4 weights

**Verdict: PASS_WITH_NOTES** (no blocking mathematical findings; scientific admission HOLD)

Reviewer model: Claude Opus 5.5 (`claude-opus-5-5`). This is self-reported and not externally attested. The card asks for `gpt-6-astra/ultra`. Author and reviewer are the same model family, so independence is limited. The review was read-only: no repository file was edited, no state-changing git command was run, and no subagents were spawned. Scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-b_rerun/`.

Task directory: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/g15b_sphere_divergence_ibp_v1_20261014` (written as T below).

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card and source identity | PASS | The zip hashes to `2d0b6da9…`. The `tasks/G15-B.json` member hashes to `7d889a28…`. `CAS-15.json` hashes to `eccc10a3…`, `DOSSIER_POSITIVE_BRIDGE.md` to `00c1fcb0…`, `COMMON_SPEC.md` to `4714827e…`, `G15APhoton.lean` to `fc4d0606…` and `CAS-15/lean/Main.lean` to `7bf190fb…`. All match SOURCE_RECOVERY.md. Every cited line was checked: CAS-15.json l.39/93/113/205/256/263, dossier (B1) l.75–78, (B2) l.94–97, (B3) l.105–110, (B4) proof l.118–122, (B5) l.138–149, and COMMON_SPEC l.10–11/17/28. G15A l.18/21/46/49/53 are `V`, `mink`, `accel`, `Rrate` and `Fcov`. `Main.lean` contains only `grstat_cas15_commutator_entry`, and `lean/result.json:5` reads `"CAS-15-C02": false`. |
| 1b | Frozen targets written before the first compile | PASS | Using `stat` birth times: FROZEN_TARGETS.md 06:10:25, then `compile_01_g15a` 06:10:39 (G15-A import only), then dev copy `c1.lean` born 06:13:45, then `compile_02_main` 06:26:04. `probe01` (06:06) is only an API `#check` probe. FROZEN_TARGETS was never modified after it was created. |
| 1c | Frozen statements match the compiled ones | PASS | My `audit/ReviewAudit.lean` retypes all 32 frozen statements verbatim and closes each with the module theorem. It also adds `rfl` checks that the definitions of σS, Pt, dS, divS, Ffield, Rrate3, RotInv, wB5, Kz and Kuw match FROZEN_TARGETS. Exit 0. |
| 1d | Faithfulness to the card and sources | PASS with one concern (note N2) | **Measure.** The theorems hold for any finite μ that is invariant under all linear isometries. This is a strengthening, and σS = `volume.toSphere` is proved invariant (`σS_rotInv`). **Signs.** Lean `hB2` is `DI + DI(We − F) + 4RI = C`, which matches (B2). The residual r = C − DI + F·∇I − 4RI matches (B3). `commutator_moments` gives (MW − WM)ᵢⱼ with `Wm W i j = (W bⱼ)ᵢ`, which matches the dossier's "−WM − MWᵀ = MW − WM". `wB5` equals the boxed (B5) bracket and the CAS-15 l.263 target term for term. **Bridge.** `bridge_Fcov` and `bridge_Rrate` use A = (0, c a), so a = A/c, and e = (0, e), so e·u = 0. Both match G15-A. |
| 1e | (c) Pointwise div F, checked with sympy using Gröbner reduction modulo \|x\|² − 1 | PASS | For a random non-symmetric σ with tr σ = 3/2: div_S F = tr σ − 2a·e − 3σ:ee holds exactly. The contract form without tr σ is false in that case. With σ = I, F vanishes identically on S², which agrees with the tr σ term. **Author's "source finding".** It is correct, but it is not a defect in the source: COMMON_SPEC l.10 defines σ as the symmetric trace-free (STF) part, so the dossier's l.139 formula is right under its own conventions. Lean assumes exactly `trL σ = 0` and never uses symmetry. |
| 1f | (c) Whether "−4𝓡M" at l.149 is shorthand, and whether boxed (B5) holds | PASS | The sympy pointwise identity (D I(F) − 4RI)eᵢeⱼ = [D(I eᵢeⱼ)(F) + I eᵢeⱼ div F] − I·wB5 is TRUE for all i, j. The a·e coefficient on eeᵀ is −2 + 4 − 2 = 0, which is the cancellation the dossier describes. On quadrature, max over i, j of \|∫(DI(F) − 4RI)eᵢeⱼ + ∫I·wB5\| = 2.1e-13. The literal scalar reading (𝓡 replaced by H_u) leaves a residual of 21.2. With non-trace-free σ the residual is 5.03. So "−4𝓡M" means −4∫𝓡(e) I eeᵀ dΩ, and with that reading (B5) holds exactly. |
| 1g | (b) Divergence theorem: route, boundarylessness, C¹, no poles | PASS | **Flow and boundary.** `integral_fderiv_skew` builds `flowL = Unitary.linearIsometryEquiv (exp(tW))` from `exp_mem_unitary_of_mem_skewAdjoint`. `integral_rot` then gives t ↦ ∫f(exp(tW)e)dμ constant: the flow maps S² onto itself and preserves μ. This is the only place boundarylessness enters. **Differentiation under the integral.** `hasDerivAt_integral_of_dominated_loc_of_deriv_le` is used with the constant bound C‖W‖. C bounds ‖Df‖ on the compact sphere via `exists_bound_of_continuousOn` and C¹ continuity of fderiv; the flow stays on the sphere by `hnorm`. The constant bound is integrable because μ is finite. **Pointwise step.** `divS_decomp` is pure algebra under \|e\| = 1 and tangency; sympy confirms it is exact for a random tangent polynomial field and fails for the radial field. **No poles.** There are no coordinates. The Lean `divS` (tr(DY∘P_e)) agrees with the spherical-coordinate divergence at generic points to within 5.3e-15. |
| 1h | (d) Degree ≤ 4 is the actual weak-quadrupole weight | PASS | `wB5_degree_le_four` gives ∃p, uniform in e, with p equal to wB5 everywhere on ℝ³. Over ℝ a polynomial function determines its polynomial, so this is a real statement. Sympy shows the generic total degree is exactly 4, from the nonzero quartic term −σ:ee eᵢeⱼ. See N2 for the moments corollary. |
| 1i | (e) Radial negative control | PASS (genuine) | `divS_radial` gives div_S x = 2, which is the mean curvature of the unit sphere. `radial_negative_control` gives ∫ = 2σS(univ) > 0 using `toSphere_ne_zero`. Quadrature gives 25.1327 = 8π. The field is C¹ and violates only tangency, so the control isolates that hypothesis. |
| 1j | Numerical divergence theorem and IBP on S² | PASS | Product Gauss–Legendre(40) × trapezoid(80) quadrature, exact for these polynomials. Total mass 4π to 1e-15. ∫div_S Y for a random tangent field: −7.8e-13. ∫div_S F with tr σ ≠ 0: −4.3e-13; F is tangent, so zero is expected, since 4π trσ − 3(4π/3)trσ = 0. Commutator ∫DI(We)eeᵀ − (MW − WM): 1.4e-13, against ‖[M,W]‖ ≈ 8.9. The dossier example M = 4πI₀/3·I + 8πI₀ε/15·diag(1,0,−1) is reproduced to 3.6e-14. Script: `num/check2.py`. |
| 2 | No circular hypotheses, no vacuity | PASS | No hypothesis restates a conclusion. **RotInv:** satisfied by σS ≠ 0 (proved in ReviewAudit). **Tangency:** satisfied by the nontrivial Kz field; ReviewAudit instantiates `divergence_theorem_σS` with it. **Skew:** `skew_witness` gives Kz ≠ 0. **Trace-free:** satisfiable, e.g. by σ = diag(1,−1,0). **hB2:** for any I, a, σ, W and DI, defining Cc by (B2) satisfies it, and continuity gives integrability. A pointwise ∀e is stronger than a.e., which is acceptable. The `he` argument of `dS_eq_fderiv_of_tangent` is unused (linter warning): a superfluous hypothesis, not vacuity. |
| 3 | Integrity: hashes, exit codes, axioms, forbidden tokens | PASS | **Hashes.** Recomputed sha256 matches every value in AUTHOR_RETURN and the receipts: lean `d08907e9…`, `compile_02.source` identical to it, audit `43fa287c…`, stdout `91a2456c…` / `35958ae7…`, stderr all `e3b0c442…` (empty), `G15APhoton.olean` `0c15d3c2…`, `G15BSphere.olean` `52b4de2a…`, `run_compile.py` `05d193e0…`, FROZEN `58469ea3…`, SOURCE_RECOVERY `ca97e9d7…`. **Exit codes.** All 0. **Forbidden tokens.** A grep for sorry/admit/native_decide/axiom/set_option/implemented_by/extern/opaque/unsafe/macro/elab in `lean/G15BSphere.lean` finds nothing. **Axioms.** My meta-audit runs `collectAxioms` over all 163 constants of module `G15BSphere`, including defs, instances and auxiliary declarations. The union is {propext, Classical.choice, Quot.sound}, with 0 offenders. **Failure retention:** UNMET, see N1. |
| 4 | Independent recompile | PASS | From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (Lean v4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` per `lake-manifest.json`). **G15-A.** `lake env bash -c "lean -R $S/src -o $S/imports/G15APhoton.olean $S/src/G15APhoton.lean"` exits 0 with empty output. The olean is `0c15d3c2…`, byte-identical to the author's. **G15-B.** `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/G15BSphere.olean $S/src/G15BSphere.lean"` exits 0 with empty stderr. Its five warnings are identical to the author's once paths are normalised. The olean is `96afbbb3…` and deterministic across two builds; the byte difference from the author's olean is explained in N3. **Audits.** The author's `AxiomAudit.lean`, run against my olean and against the author's olean, produces stdout byte-identical to `compile_03_audit.stdout` both times. `ReviewAudit.lean` exits 0. |

## Blocking findings

None.

## Non-blocking notes

**N1. Failure retention is UNMET (process, not mathematics).** The author developed in `raw/probes/c1.lean` and compiled it directly with `lake env lean`, outside `run_compile.py`, whose own docstring says "keep every attempt".
- **What is missing:** the stdout/stderr and exit code of every failed attempt, the attempt count, and every intermediate source. Only the last dev snapshot survives, and it differs from the final file only by cosmetic lemma renames and simp-argument edits. The `first_failure` field in AUTHOR_RETURN is a narrative recollection, not evidence.
- **Why it matters:** the card's `required_evidence` asks for argv, stdout/stderr and exit code for executed programs. This is weaker retention than G12-D, which at least kept 9 source snapshots and an index, and weaker than G15-A, which kept its failed compiles 01 and 02 in the harness.
- **Why it is not blocking:** the claimed theorems rest on the final source. Its receipts are complete, and I reproduced them independently. I am following G12-D's precedent, where the mathematical review was PASS_SCOPED and `strict_failure_retention_requirement=UNMET` was recorded as an evidence limitation.
- **Required action:** RETURN.json should record `strict_failure_retention_requirement: UNMET`, `original_failure_streams: UNAVAILABLE`, `failed_attempt_count: UNKNOWN`.
- **If the parent applies the G12-D hold:** the only remedy is a complete-retention re-execution from the final source. That cannot recover the lost history, and it must not be presented as recovering it.

**N2. `B5_rank_le_four_moments` has weak quantifiers.** Its form ∀μ ∀I ∃p lets p depend on I. I compiled a demonstration (`audit/UniformFix.lean`, exit 0): a degree-0 p reproduces any value whenever ∫I ≠ 0. So the theorem does not express the dossier claim that "only brightness moments through rank four are needed", which is uniform in I. SOURCE_RECOVERY binds that claim to this theorem, and the binding overstates it.
- The uniform content does follow from the frozen and proved `wB5_degree_le_four` plus linearity.
- I compiled the additive uniform version, `B5_rank_le_four_moments_uniform`: ∃p, deg ≤ 4 ∧ ∀μ [finite] ∀I continuous, …, with axioms [propext, Classical.choice, Quot.sound].
- **Minimal fix (either one):**
  - rebind the dossier citation to `wB5_degree_le_four` and describe `B5_rank_le_four_moments` as I-wise; or
  - add the uniform theorem as an additive, recorded deviation.

**N3. The olean differs only through an embedded absolute path.** `strings` shows the source path stored in the olean at entry 10628. The paths differ by 59 characters and the files by 56 bytes. Identical audit output against both oleans confirms they have the same content.

**N4. Declared non-formalized items.** These are correctly excluded and not claimed:
- the existence of a C¹ ambient extension of a C¹ function on S²; extension-independence of the operators is proved (S block);
- `toSphere` = Hausdorff measure, with total mass 4π;
- (B2) itself, which appears only as a hypothesis.

**N5. SOURCE_RECOVERY.md was created after the compiles (06:28).** It is not a frozen artifact, but FROZEN_TARGETS refers to it for bindings.

**N6. `sig4 σ` has matrix σᵀ as a bilinear form.** This does not matter for symmetric shear. Deprecated-name linter warnings (lines 263, 368, 389) are cosmetic.

## Not proved

- **Scientific admission:** HOLD.
- **Physics and model gaps:**
  - (B2) Liouville/energy transport and the horizontal derivative 𝒟;
  - C¹ extension existence;
  - the toSphere/Hausdorff identification and the 4π mass;
  - sharpness of the degree-4 bound (generically attained per sympy, but not formalized).
- **Out of scope:**
  - distinct-eigenvalue inversion, the gap bounds (B6) and the stacked commutant (C03/C04);
  - quadrature (C3);
  - any CAS axis or CAS_4AXIS_PASS.
- **Process gaps:** full failure-retention compliance; publication.

## Suggested VALIDATION_MATRIX scientific row (not written)

`G15-B | sphere div theorem + IBP + (B4)/(B5) + deg≤4 | Lean final src d08907e9…, independent recompile exit0, 163 constants axioms ⊆ {propext,Classical.choice,Quot.sound}; sympy exact div F=trσ−2a·e−3σ:ee, divS_decomp, B5 integrand; S² quadrature residuals ≤2.2e-13 (div thm, IBP/B5, [M,W]); radial control 8π | PASS_WITH_NOTES | notes: failure-retention UNMET (dev compiles outside harness); B5_rank_le_four_moments I-wise only (uniform version available) | admission HOLD`

## Relevant paths

- `T/lean/G15BSphere.lean`
- `T/FROZEN_TARGETS.md`, `T/SOURCE_RECOVERY.md`, `T/AUTHOR_RETURN.json`
- `T/raw/compile_0{1,2,3}_*.{json,stdout,stderr,source.lean}`, `T/raw/AxiomAudit.lean`
- `T/raw/probes/c1.lean`
- Scratch evidence, all under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-b_rerun/`:
  - `audit/ReviewAudit.lean`
  - `audit/UniformFix.lean`
  - `num/check2.py`
  - `main.stdout`, `audit.stdout`
  - `authaudit/{mine,theirs}.stdout`

