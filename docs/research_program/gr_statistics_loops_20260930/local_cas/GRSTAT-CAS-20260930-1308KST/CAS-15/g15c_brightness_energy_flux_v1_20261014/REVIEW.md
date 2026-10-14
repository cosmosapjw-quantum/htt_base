# G15-C — independent review (verbatim final report of a fresh read-only reviewer)

# G15-C fresh independent review (read-only)

**Reviewer model:** claude-opus-5-5 (Opus 5.5). I did not author this package. I modified no repository file and ran no state-changing git command. Scratch files are only under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-c_rerun/`.

## Verdict: **PASS_WITH_NOTES**

There are no blocking findings. All 25 frozen targets compile under my independent rebuild of the whole import chain. Each one is restated verbatim from FROZEN_TARGETS.md (A1 applied) and closed against the compiled theorem. Every constant in the module depends only on `[propext, Classical.choice, Quot.sound]`. The physics signs and coefficients pass three numerical checks to near machine precision: energy IBP, band flux, and the M2 quadrupole identity. The band flux is genuinely required: dropping it gives O(1) errors.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read | PASS | `unzip -p … tasks/G15-C.json`: member sha256 `6e017428…88ed` and zip sha256 `2d0b6da9…af6f` match SOURCE_RECOVERY.md. |
| 1b | Source citations | PASS | All 5 sources recomputed: DOSSIER `00c1fcb0…`, CAS-15.json `eccc10a3…`, COMMON_SPEC `4714827e…`, TEFF `f04d96fe…`, DOSSIER_CLAIMS `a42a50fb…`. Each is byte-identical to `git show a30d84c7:<path>` (the card's source_snapshot). Every cited line was read and matches verbatim: DOSSIER:74-82, 86, 89-99, 105, 138-147, 179; CAS-15.json:47, 48, 57, 81, 103, 122, 257, 262; COMMON_SPEC:5, 17, 28; TEFF:176; CLAIMS:15, 125. |
| 1c | Brightness normalization and energy weight | PASS | `bolI = α∫_{Ioi 0} E³ f` is the same as DOSSIER:91, 𝓘=α∫₀^∞E³f dE. The band version has the same weight on [E1,E2]. `bolC` matches 𝓒=α∫E³C_t. |
| 1d | (B1) rates and Liouville signs | PASS | `liouville = ∂_s f − 𝓡E ∂_E f + ∇_x f·(Wx − F)` follows from ∇_L ln E = −𝓡 and h∇_L e = −F + We. `liouville_chain` proves it is d/ds f(s,Eγ,eγ). With L=U+ce and x0=ct we have dt/ds=1, so C_t per second is consistent. T3/T4 bridge to G15-A H2/H3: `w4 W Y e = Y·(We)` matches the G15-A H3 term `W Y e` (derivative-first W, COMMON_SPEC:13-14). |
| 1e | Flux sign and coefficient 4 (by hand) | PASS | Integrating αE³·(kinetic eq) gives D + ∇I·(W−F) − 𝓡α∫E⁴∂_E f = C. Band IBP gives ∫E⁴∂_E f = [E⁴f] − 4∫E³f, so D + ∇I·(W−F) + 4𝓡I − 𝓡·flux = C. This is exactly K1, and `bandResidual` (+𝓡·flux) gives K2. |
| 1f | Band IBP, numerical (Planck f=1/(e^E−1), flux ≠ 0) | PASS | [0.5,3]: lhs = −5.923671949367, flux − 4I₃ = −5.923671949367, flux = 4.1477. [1,2]: −1.883844057199 on both sides, flux = 1.9223. [2,8]: −21.382891054489 on both sides, flux = −1.1298. In each case the no-flux error equals the flux. Bolometric (mpmath, 30 digits): ∫E⁴f′ = −25.975757609067316596 = −4·π⁴/15. |
| 1g | Full K1/K2 numerical check | PASS | f=1/(exp(E/T(s,x))−1) with T = 1 + 0.1s + 0.2x₀ + 0.15x₁x₂ + 0.1x₂². Nonzero H, a, tracefree symmetric σ, skew W; Ct := Liouville(f); band [0.5,4]; 5 random sphere points. K1 and K2 errors are ≤ 5.6e−15. Dropping the flux gives errors of 0.63–2.9, equal to 𝓡·flux. This check is partly tautological because Ct is defined by Liouville(f); it does test the flux sign and the coefficient 4. |
| 1h | M2 (band B5 with flux moment) on uniform sphere | PASS | 48×96 product quadrature. C₂ − T₂ + Φ₂ − ∫I·wB5 equals MW − WM with max abs difference 8.3e−14. Without the flux moment the difference is 10.6. This end-to-end check also corroborates the imported G15-B `weak_quadrupole_commutator` and `commutator_moments`. |
| 1i | Frozen-vs-compiled statements | PASS | My own whitespace-normalized diff of all 39 frozen declarations found only (i) A1 and (ii) `w4`, whose frozen text is signature plus comment; the body matches the comment, and `w4_apply` is `rfl`. Lean restatement check: `ReviewAudit.lean` restates all 25 frozen theorem signatures (A1 applied) and closes each with `exact`/`apply G15C.X <;> assumption`. All 25 elaborate, exit 0. So the compiled hypotheses are no stronger than the frozen ones, and the conclusions unify. |
| 1j | Amendment A1 | PASS (elaboration-only) | Frozen `0 (bas 0)` cannot elaborate. `(0 : E3 →L[ℝ] E3) (bas 0)` is the same W = 0 that `liouville 1 0 0 0` already uses. Data and meaning are unchanged. |
| 1k | Negative controls genuine | PASS | E4: ∫E⁴·0 = 0 ≠ −4·15/4 = −15, and 0 = (16−1) − 15. K5: f≡1, Ct≡0, H=1, a=σ=W=0 satisfies the kinetic law. The flux term is 15 and 4𝓡·bandI = 15 ≠ 0 = C. Both are real admissible data, not degenerate. |
| 1l | Bolometric endpoint separated from band correction | PASS | E2 keeps general limits (LUV − LIR). E3 and K3 have no flux term. Band K1, K2 and M2 keep 𝓡·flux and its quadrupole moment. COMM-BAND acceptance is met. |
| 1m | Card step 4 (bolometric endpoint vanishing from actual IR/UV assumptions) | PASS_WITH_NOTE | The source's actual assumption (DOSSIER:93) is literally "vanishing endpoint E⁴f". `BolHyp.IR/UV` encode exactly that, so K3 is faithful. E5 also derives the vanishing from weaker envelope bounds (\|E³g\| bounded near 0⁺, \|E⁵g\| bounded at large E), and E6 shows the Planck shape meets them; I checked the constants 1 and 1440 by hand. Note N1 lists the remaining gaps. |
| 1n | Card step 2 (Leibniz domination/regularity) | PASS (band) / PASS_WITH_NOTE (bolometric) | Band: domination is built by compactness from C¹ (`param_band`), not assumed. Bolometric: `param_Ioi` proves the interchange, but from a domination bound that is assumed (`BolHyp.dom`, `domInt`). This is declared. |
| 1o | Step 5 (every term an actual moment) | PASS | C, D and I are the energy moments of the supplied Ct and f. ∇I is the true Fréchet derivative of the band moment (L4 `band_fderiv_x` interchange). Band smoothness is derived (L3), not assumed. M3 assumes C¹ of `bolI` and C/D moment integrability; these are explicit and match the contract "Smoothbrightness" (CAS-15.json:48). |
| 2a | No circular inverse / C2, T2 independence | PASS | T₂ is built from ∂_s of the supplied f, and C₂ from the supplied Ct. W enters only through the kinetic law `hkin` (the forward physics), and every theorem is a forward identity. No W is fitted, and no theorem uses (B2) to generate D from a trial W. This matches the card pitfall and COMMON_SPEC:28. |
| 2b | No hypothesis assumes its conclusion | PASS | K3 assumes the endpoint limits and the kinetic law, not the brightness equation. M2 derives the integrability of C, D and Φ. M3 assumes C/D integrability, which is a standard regularity side condition, not the conclusion. |
| 2c | Non-vacuity | PASS (with note) | E7/K4 use the witness f=e^{−E}. My own instance: `band_brightness_equation` applied to f = e^{−E}(1+s²+x₀) on [1,2] with Ct := Liouville(f) compiles (`fexp_c1` plus an `example` in ReviewAudit.lean). |
| 3a | Hashes | PASS | Recomputed for all 8 receipts: source snapshot, stdout and stderr sha256 all match. Exit codes are 0,0,1,0,1,0,0,0. `lean/G15CBand.lean` (f8d49b92…) equals the attempt-7 snapshot. AxiomAudit 6f5ee126…, run_compile.py 7c20605d…, SOURCE_RECOVERY f45482cf…, FROZEN f50e6a2a…, and oleans G15A 0c15d3c2…, G15B 52b4de2a…, G15C f3e48941… all match AUTHOR_RETURN. |
| 3b | Failed attempts kept | PASS | Attempt 3 (pre-interruption) and attempt 5 (post-resume) failures are kept with stdout. Numbering is monotone. |
| 3c | Resume integrity | PASS | `diff compile_04_main.source.lean lean/G15CBand.lean` shows additions after line 284 only. The E1–E7 and L1 text is unchanged. FROZEN mtime is 07:00:18 KST and SOURCE_RECOVERY 06:58:59. The first G15C compile started 07:02:25 KST (22:02:25Z), after only the two import compiles. Neither file was modified after the resume. |
| 3d | Forbidden tokens | PASS | grep for `sorry\|admit\|native_decide\|axiom\|set_option\|maxHeartbeats\|implemented_by\|extern\|unsafe` in `lean/G15CBand.lean` and `raw/AxiomAudit.lean` finds nothing. |
| 3e | Axioms | PASS | My enumeration of every constant in module G15CBand (96 in total, including the BolHyp structure and auto equation lemmas) printed axioms for each. All are exactly `[propext, Classical.choice, Quot.sound]`; 0 deviate. The author's audit covered all 48 non-auto theorems; the only ones missing are the 10 auto-generated `.eq_1` lemmas. |
| 4 | Independent recompile | PASS (with note) | cwd `/home/cosmosapjw/lean_oracles/viii_oracle`, toolchain `leanprover/lean4:v4.31.0`, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` (from lake-manifest). Sources copied to scratch with matching sha256 (fc4d0606…, d08907e9…, f8d49b92…). Each built with `lake env bash -c "LEAN_PATH=<scratch>/imports:$LEAN_PATH lean -R <copy dir> -o <scratch>/imports/<M>.olean <copy>"`. G15APhoton, G15BSphere and G15CBand all exit 0. The G15C diagnostics equal the author's attempt-7 output (one unused-simp-arg lint at 223:15). Own audit `ReviewAudit.lean` exits 0. |

On the olean hashes: G15A reproduces the author's hash exactly (0c15d3c2…). G15B and G15C differ (a6732da2… and 141b9e9a…). I traced this to the absolute source path embedded in the olean: `strings` shows the scratch path inside my G15B olean. My G15B build is deterministic across two builds, and my G15C olean hash is the same whether built against my imports or the author's. This is not a content discrepancy.

## Blocking findings
None.

## Non-blocking notes
- **N1 (step 4 strength).** There is no single composed theorem from the envelope bounds to K3; the user has to combine E5 with BolHyp.IR/UV by hand. The only BolHyp witness is e^{−E}, constant in (s,x), with domination bound ≡ 0, so domination, measurability and C¹ are not exercised. Suggested additions, not required:
  - `bol_brightness_equation_of_envelopes`.
  - A BolHyp witness for BE with a (s,x)-dependent temperature, f = 1/(exp(E/T(s,x))−1). By hand this is dominated by ~E² near 0 and by exponential decay in the UV, so it should be provable.
- **N2 (band hypothesis scope).** The band theorems assume global `ContDiff ℝ 1 (F3 f)` on ℝ×ℝ×E3. A BE/Planck occupation has a pole at E=0, so it does not satisfy this literally. A cutoff extension equal to f on a neighbourhood of [E1,E2] with E1>0 (and near (t, S²)) changes no quantity in K1, K2 or M2, so this does not reduce scientific content. It is not stated in `not_claimed`, though. Either add that line or provide a localized-hypothesis variant.
- **N3.** BE with nonzero chemical potential (TEFF η₀) is not covered by E6, which uses μ=0 and dimensionless E/kT. The G12-D conditional dependency is correctly left unimported.
- **N4 (process).** The freeze-before-compile evidence is filesystem mtime plus self-reported hashes; the folder is untracked with no commit anchor. The mtimes are consistent with the claim.
- **N5.** The DOSSIER access label in CAS-15.json is "orchestrator_identity_only". SOURCE_RECOVERY says the orchestrator authorized reading it for definition recovery. I cannot verify that authorization.
- **N6.** The imported G15-B is PASS_WITH_NOTES with limited process evidence. My numerical M2 check independently corroborates the composed B5/commutator identity for the uniform measure only, not for the whole RotInv class.

## Code defect vs. method limitation
I found no code defects. The method limitations are:
- the horizontal chart, and 𝒟 identified with ∂_s at fixed (E,x), are not formalized;
- the ambient C¹ extension of f off the sphere;
- bolometric domination is assumed rather than derived;
- the moment-level bolometric smoothness and integrability of `bolI` are assumed.

All of these are declared in `not_claimed`.

## Not proved / not claimed
- Scientific admission: **HOLD**.
- Existence of the horizontal chart and the identification 𝒟 = ∂_s at fixed (E,x).
- Ambient C¹ extension in x off S².
- Bolometric domination, measurability and C¹ fields (assumed). The only witness is e^{−E}.
- C¹ of `bolI` and the C/D quadrupole integrability in M3 (assumed).
- Sphere measures outside the RotInv class.
- G12-D BE-specific IR/UV bounds and BE with chemical potential.
- Any inverse or W-identifiability statement (C03/C04 scope).
- Fitting, solvers, production use, publication readiness.

## Suggested VALIDATION_MATRIX scientific row (not written)
`G15-C | brightness energy integral + band flux | units/normalization PASS (α∫E³f, DOSSIER:91) | sign/coeff-4 PASS (hand + numerical 1e-12..1e-15) | COMM-BAND flux kept PASS (E4/K5 genuine; drop-flux error = 𝓡·flux) | bolometric endpoint PASS_WITH_NOTE (source assumption verbatim; envelope→vanishing proved; BE (s,x)-dependent BolHyp witness NOT_TESTED in Lean) | M2 moment identity PASS (uniform sphere, 8e-14) | C2/T2 independence PASS | axioms std-3 only | independent recompile PASS (Lean 4.31.0 / mathlib fabf563a) | scientific admission HOLD | reviewer claude-opus-5-5 2026-10-14`

## Files
- Task folder: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/g15c_brightness_energy_flux_v1_20261014/` (`lean/G15CBand.lean`, `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/compile_0[1-8]_*`, `raw/AxiomAudit.lean`).
- Reviewer scratch, all under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g15-c_rerun/`:
  - `imports/*.olean` and `G15*.stdout`/`.stderr` (rebuild)
  - `audit/ReviewAudit.lean` and `audit/ReviewAudit.out` (restatements and axioms)
  - `audit/Enum.lean` and `audit/enum.txt` (constant enumeration)
  - `stmtdiff.py` (statement diff)
  - `numcheck.py` (numerical checks)
