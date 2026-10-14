# G12-E — independent review (verbatim final report of a fresh read-only reviewer)

## G12-E independent review (fresh, read-only): verdict PASS_WITH_NOTES

This review was run by Claude Opus 5.5 (`claude-opus-5-5`). I did not author the package. I modified no repository files and ran no state-changing git commands. All scratch output is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-e_rerun2/`. That is a new subdirectory; I did not reuse any partial scratch from the earlier reviewer.

- **Verdict:** PASS_WITH_NOTES. There are no blocking findings.
- **Scientific admission:** HOLD.

Package under review: `T=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/g12e_moment_null_counterexample_v1_20261014`

### Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | done | `unzip -p HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip .../tasks/G12-E.json`. Read the scope (TEFF-H1), 5 lean_steps, 4 acceptance items and 2 pitfalls. |
| 1a | Source citations in SOURCE_RECOVERY.md | PASS | Hashes recomputed: TEFF_POSITIVE_BRIDGE.md f04d96fe…, CAS-12.json 5a682716…, COMMON_SPEC 4714827e…, TEFF_CLAIMS 9654e73e…, all matching. Every line citation checked by hand and matches: bridge :39, :43-46, :96, :145-151; CAS-12.json :47, :109; TEFF_CLAIMS :133-138; G11AIntegralBregman :21-33, :222-256, :361-370; G11AGuarded :22-31; G12DInterface :11-12; G12DUV :236, :240; G12DCardClosure :357; OscillatoryDerivative :12-32. |
| 1b | Frozen targets predate the first proof compile | PASS (note N1) | FROZEN_TARGETS.md sha 66317e6b… matches `raw/FROZEN_TARGETS.sha256`. File mtimes: FROZEN 21:44 UTC, sha file 21:48 UTC. First target compile (compile_12) started at 21:50:27 UTC. compile_01–11 are rebuilds of the 8 imports plus 3 API-name probes. The probes contain only `#check` of Mathlib/import names, no target statements. |
| 1c | Faithfulness to source `:145-151` | PASS | Family: `f_n = g + a·sin(n x)·q(E)`. Envelope A5: `0 ≤ f ≤ F` through `cdom`/`Admissible`. Divergence `D_H(f‖g)` uses the reviewed `G11A.Dext`/`Dfin` with `hS`/`hS'` (Paper I (11)-(14)). Moments are the (A1) δ-form `∫φ(f−g)dν = 0`. Measure is `nu C = C E² dE ⊗ volume.toSphere` (total solid angle 4π). The Fisher weight `1/(f(1+ξf))` equals the source's `1/(f(1+f))` for BE. Quantifiers: `∃ q a B` comes before `∀ n x` (T4) and `∃ B` before `∀ M` (T9). So the amplitude and the divergence bound are uniform in n, as the source says ("small fixed a"). |
| 1d | Every frozen statement equals the compiled theorem | PASS | My file `audit/RevFrozen.lean` types T1–T11 verbatim from FROZEN_TARGETS (T4 with its two annotations) and closes each with `exact <compiled theorem>`. It also checks the frozen definitions with `rfl`: cellWidth, cellCenter, rIn = w/4 and rOut = w/2, family, Admissible, nu, occupation, `hess .BE`. Exit 0, no errors. |
| 1e | T4 deviation (`Admissible (Ω := Ω)`, `z : ℝ × Ω`) | PASS: changes only how Lean elaborates, not what is claimed | `audit/RevFrozenLiteralT4.lean` uses the frozen T4 text literally and exits 1 with 5 errors ("don't know how to synthesize implicit argument Ω", "Failed to infer type of binder z"). The frozen text has no elaborated meaning on its own. The theorem's own Ω, which is also the carrier of μ, is the only coherent reading. Nothing is weakened. A minor wording point: the `(Ω := Ω)` annotation was already in compile_12's source; only the binder fix was driven by the failure. |
| 1f | Pitfall: q′ term | PASS | q is a function of `z.1` only, so it is constant in x. The derivative uses `CAS12C04.hasDerivAt_constant_q` with constant `q z.1`, which gives `∂_x f_n(0,z) = a n q(z.1)` with no q′ term. |
| 1g | Pitfall: finite kernel does not give C_c^∞ | PASS | Smoothness and compact support come from `ContDiffBump.contDiff` / `hasCompactSupport`. T2 holds for every c. The kernel (`LinearMap.ker_ne_bot_of_finrank_lt` on the m×(m+1) `momentMatrix`) only selects c ≠ 0. Since bump i is 1 at its own centre and 0 at the others, `q(center_i) = c_i`, so q ≠ 0 at some point of `Ioo E1 E2`. |
| 1h | Amplitude a independent of n | PASS | `a = δ/(2Q)` with `δ = min_{[E1,E2]} min(g, F−g) > 0` (compact minimum) and `Q = Σ|c_i| + 1`, fixed before n and x. |
| 1i | Same family: bounded D and unbounded derivative | PASS | T4 gives `B = max(Mb,0)·ν(patch)`, where Mb bounds the Bregman density, which is continuous on the compact set `[E1,E2]×[−a,a]`; the bound holds for all n and x. T9 combines this with T7/T8 on the same `family g q a N`, choosing N for each M. |
| 1j | T9 uses the closed domain `cdom` | PASS (note N3) | This matches the source's "admissible occupations" (Paper I Def. 1 closure). A larger class makes the existential slightly weaker, but T4 proves the witnesses lie in the open `dom`, and `f 0 = g ∈ dom` makes the `hess` integrand non-junk. |
| 1k | T10 BE instance is non-vacuous | PASS | Every T9 hypothesis is discharged for `g = occupation(2b)`, `F = F_b` on [1,2]. The strict slack comes from `exp(bE) < exp(2bE)`. Margin is checked numerically below. |
| 1l | T11 control is genuine | PASS | It shows `∫ 1·ψ_i dν > 0` by radial positivity on a ball where ψ_i > 0, so no single bump is null for the number score. Numeric values for the three bumps: 4.2930, 7.0855, 10.5762 (C = 1). |
| 1m | The seven BLOCKER.json items | PASS | (1) Measure: reused `G11A.nu`; T5 adds no mass at E ≤ 0 and a finite patch. (2) Scores: an arbitrary finite φ, IntegrableOn the patch, Bochner moments, plus the concrete number+energy family. (3) Function space: q C^∞ with compact `tsupport ⊆ [E1,E2]`, E1 > 0; T3b lifts it to C^∞_c on ℝ³; g measurable and continuous on the patch. (4) Construction: T3. (5) Envelope: reused `occupation*` lemmas; the margin is an explicit hypothesis, discharged in T10; a is proved uniform. (6) Divergence: reused Dext/Dfin and the guarded `finite_budget_stat`; uniform bound proved in T4. (7) Derivative: pointwise `HasDerivAt` plus `Tendsto atTop` for the L², Fisher and pointwise norms. The release condition's "integral differentiation" is covered by T4c. Each item is concretely fixed or reused; none is hand-waved. |
| 2 | No hypothesis assumes a conclusion, and no vacuity | PASS | All hypotheses are about (g, F, φ, μ, patch); none mentions q, a, B or derivatives. T10 instantiates all of them. The `M < ∫ …` conclusions cannot be met by a junk Bochner 0 for M ≥ 0, and integrability is proved through `radial_integral_pos`. |
| 3a | Hashes | PASS | Recomputed and matching AUTHOR_RETURN: both new `.lean` files, AxiomAudit, run_compile.py, SOURCE_RECOVERY, and all 10 oleans in `raw/imports`. All 8 import sources match their reviewed RETURN.json records (G11A RETURN covers BregmanThreePoint, G11AIntegralBregman and G11AGuarded; G12D RETURN covers its 4 files; C04 RETURN covers OscillatoryDerivative). For all 17 receipts, the `source`/`stdout`/`stderr` sha256 values match the files on disk (0 mismatches). |
| 3b | Exit codes and failed attempts kept | PASS | Failures 09, 10 (probes), 12, 14 and 15 are kept with their source snapshots and outputs. Diffs from 12→13 and 14/15→16 change proofs only, apart from the T4 binder. 13, 16 and 17 exit 0. |
| 3c | Axioms and forbidden tokens | PASS | `grep sorry\|admit\|native_decide\|axiom\|set_option\|unsafe\|implemented_by\|extern\|opaque` over `T/lean` finds nothing. The author's compile_17 shows 48 theorems with `[propext, Classical.choice, Quot.sound]`. My `audit/RevAxioms.lean` covers all 48 theorems plus the instance `dOmega_isFiniteMeasure`: 49 results, all on those three axioms only. |
| 4 | Independent recompile | PASS | Ran from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (Lean 4.31.0; manifest mathlib fabf563a…). All 10 modules were rebuilt from source into scratch via `lake env bash -c "LEAN_PATH=$S/olean:$LEAN_PATH lean -R $S/src -o $S/olean/<M>.olean $S/src/<M>.lean"`, all exit 0, in dependency order. G12EMomentNull.olean (8a70ac81…) and G12ECounterexample.olean (2c465f77…) are byte-identical to the author's, and so are 7 of the 8 imports. G11AIntegralBregman differs (mine 04d61b3e…, theirs 432b626a…); see N7. |
| 5 | Numeric spot-check of T10 (mpmath, 30 digits; `numcheck.py` / `numcheck.out`) | PASS | Setup: b = C = 1, patch [1,2], scores {1, E}, Mathlib-style `smoothTransition` bumps. The moment matrix is 2×3. Kernel c = (0.82616, −1, 0.33460). Retained moments of q are 2e−30 and 1e−30. δ = 0.0186574, Q = 3.16076, a = 2.9514e−3. Admissibility (0 < f < F) holds on a 2001-point grid for every tested (n, x). Uniform bound: D ≤ 8.382e−4. For n ∈ {1, 2, 5, 10, 100, 1000, 10⁴}: D(x = π/2n) = 8.3177e−4 for every n; L² = 9.13939e−5·n² (ratio constant to 10 digits); Fisher = 1.648e−3·n²; finite-difference ∂_x f_n(0,E) equals a·n·q(E) to 15 digits. |

### Blocking findings
None.

### Non-blocking notes
- **N1. Freeze timing.** The freeze evidence is file mtimes plus receipt UTC stamps. The task directory is untracked in git (`??`), so the freeze is not git-attested. FROZEN predates every target compile but not the import rebuilds or API-name probes 09–10, which contain no target text.
- **N2. AUTHOR_RETURN deviation wording.** It says both annotations were driven by compile_12. Only the `z : ℝ × Ω` binder was; `(Ω := Ω)` was in the first submitted source. This is harmless.
- **N3. Optional strengthening of T9.** T9 could add `∀ x z, 0 < z.1 → f x z ∈ dom s`, already proved in T4. That would make the `hess` integrand's non-junk status visible from T9 alone.
- **N4. T4c has no integrability hypothesis.** It is meaningful only when `K·q` is integrable; otherwise both sides are the Bochner junk value 0.
- **N5. What "derivative" means.** It is the pointwise-in-z `HasDerivAt` field, normed in L²(ν). An L²(ν)-valued Fréchet derivative is not stated, though it is trivial here because the x-dependence is the scalar sin(nx). Reading the source's D_X as ∂_x assumes a flat parallel tetrad with no connection terms; that is a modelling reading, not something proved.
- **N6. The ℝ³ lift is separate.** T3b is not bundled into T9. Composing them is immediate (`tsupport ⊆ [E1,E2]`, E1 > 0).
- **N7. G11AIntegralBregman olean hash.** `strings` diff of the two oleans shows the only difference is the embedded absolute source path. My rebuild is deterministic (same 04d61b3e… twice). The author's olean hash is still the one their own receipt reports for their path.
- **N8. Author audit coverage.** The author's axiom audit omitted the instance `dOmega_isFiniteMeasure`. My audit covers it, and it uses only the standard axioms.
- **N9. Card CAS axes not executed.** wolfram_xact, sympy and sage_singular were not run, and the author says so. My mpmath run is a numeric kernel and moment certificate for the T10 instance only, not an exact CAS certificate.
- **N10. Coverage limits, all declared by the author.** The base state and envelope depend on energy only (isotropic). There are no concrete FD or MB instances. Angular Fisher budgets are not treated. The identification of `nu C` with C·d³p is not proved. These are scope limits and do not weaken the refutation: any single admissible g already refutes a universal bound.
- **N11.** `push_neg` deprecation warnings only.

### Not proved / not claimed
- Scientific admission: **HOLD**.
- CAS axes for G12-E (wolfram_xact, sympy, sage_singular).
- Anisotropic base states or envelopes; FD and MB concrete instances.
- The angular Fisher half of the TEFF-H1 ledger sentence.
- The positive replacement bound (J_X weighted Cauchy–Schwarz).
- The pushforward identification of `nu C` with C·d³p.
- An L²-valued Fréchet x-derivative, and D_X versus ∂_x in a curved or connection setting.
- Any CMB or cosmological identification.
- The parent card closure decision, which belongs to the adjudicator lane.

### Suggested VALIDATION_MATRIX scientific row (for the caller to record; I did not edit it)
`G12-E | TEFF-H1 moment-null counterexample | PASS_WITH_NOTES (fresh independent review, claude-opus-5-5) | recompile exit0 from source, new oleans byte-identical (8a70ac81…, 2c465f77…); 49/49 axioms ⊆ {propext, Classical.choice, Quot.sound}; frozen T1–T11 verbatim-conformant (T4 deviation elaboration-only, literal fails to elaborate); mpmath T10: D≤8.38e-4 uniform, L²=9.139e-5·n², Fisher=1.648e-3·n², moments≈1e-30 | notes N1–N11 | CAS axes not run | scientific admission HOLD`

### Files
- Reviewed package: `T` above, specifically `FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `lean/G12EMomentNull.lean`, `lean/G12ECounterexample.lean`, `raw/compile_*.json`, `raw/AxiomAudit.lean`.
- In my scratch directory `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-e_rerun2/`:
  - `build.sh`, `build_summary.txt`, `log_*.out`, `olean/` (the recompile)
  - `audit/RevAxioms.lean` and `.out` (axiom audit)
  - `audit/RevFrozen.lean` and `.out` (verbatim conformance check)
  - `audit/RevFrozenLiteralT4.lean` and `.out` (literal T4 fails to elaborate)
  - `numcheck.py`, `numcheck.out` (T10 numeric check)
