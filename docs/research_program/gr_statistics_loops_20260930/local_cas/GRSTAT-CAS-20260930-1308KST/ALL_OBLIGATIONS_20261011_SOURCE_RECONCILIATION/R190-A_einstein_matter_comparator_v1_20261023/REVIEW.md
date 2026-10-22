# R190-A — independent review (verbatim final report of a fresh read-only reviewer)

# R190-A independent review: Einstein–matter comparator, PR-190

Reviewer model: Claude Opus 5.5 (`claude-opus-5-5`), running as a fresh in-session subagent. I did not author this package. The review was read-only: no repository file was edited and no state-changing git command was run. Scratch files are under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/`.

## Verdict: PASS_WITH_NOTES (no blocking findings)

- The Lean refutation is mathematically correct. It compiles independently, uses only the standard axioms, and its frozen targets are faithful to the sources.
- The refutation uses the definition the source actually registers, not a swapped one:
  - `CLAIM_LEDGER.yaml:280` puts the comparator W² on the slice normal n.
  - `t3_king_ellis.yaml:82-91,151-165` says the same.
  - The unmerged `bae6ac2df` spec gives `congruence_class: HYPERSURFACE_NORMAL` for all three targets.
- The withdrawn-W² / shear-swap pitfall is respected. The result agrees with the unmerged `bae6ac2df` verdict (`COMPLETED_FAILED_WITH_RECEIPT`, refuted at constraint level). R190-A strengthens it by deriving Frobenius from a general first jet, where `bae6ac2df` set the derivative to 0 by definition.
- Scientific admission: **HOLD**.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card and sources | PASS | Card read from the zip; card sha `4cb8e2bc…` matches `raw/card_R190-A.json`; zip sha `2d0b6da9…` matches. Snapshot `a30d84c7` is an ancestor of HEAD `9f0beb69`. All 14 cited source files are unchanged between recovery HEAD `d256ed4` and the current HEAD (`git diff --quiet`). |
| 1b | Comparator, box, corners | PASS | `egs3_graded_comparator.py:48-50`: SECTORS and c = (+1,−1,+1,+1). `egs3_linearized_realization.py:97-110`: lower corner (12,4,3,0)/100 → 11/100, upper corner (12,0,3,2)/100 → 17/100. Lean `regBox`/`cornerPoint` match exactly. Recomputed: algebraic interval [11/100, 17/100]. |
| 1c | Declared class, verbatim | PASS | `egs3_nonlinear_realization.py:22-43,102-140` (with the 198-209 caveats): Bianchi I for Ω_k = 0, Bianchi V with a_i = (a,0,0) and ³R = −6a², diagonal trace-free shear, antipodal pair, momentum `3 a_bσ^{ab} + κq^a = 0` (coefficient convention-dependent, so Lean quantifies over all k), and Gauss `Ω_m + Ω_Λ + Ω_k + Ω_tilt + Σ² − W² = 1`. `HomData.Domain/Gauss/Momentum/Jacobi` encode this. |
| 1d | Is "W² on n" the source definition? | PASS (with a citation note) | Explicit in `CLAIM_LEDGER:280` ("comparator W^2 stays defined on the slice normal, re-attribution to the matter congruence is a registered interpretive question NOT a claim"), in `t3_king_ellis.yaml:82-91,160-165`, and in `bae6ac2df pr190_spec.yaml:58-61,63-92`. Contrary readings exist: steelman H03 and the `frame_typed_algebra.py:5-6` docstring describe the v10 comparator as mixing "u-frame tilt/vorticity". `revival_frame_functor.py:34-35,77` registers both `W2_n` and `W2_u` and rejects n-shear + `W2_u` without a bridge. The u-reading therefore needs an owner re-definition (X1). It would also hit the roadmap's frame-mismatch kill (the only registered u→n bridge is order-β², not exact). KE-DYN further shows W²[u] is dynamically obstructed at Ω_k = 0 in the group-invariant perfect-fluid class; this is in-repo evidence and is not proved in Lean. Conclusion: this is not a definition mismatch. SOURCE_RECOVERY does not cite H03, `frame_typed_algebra.py:6` or `revival_frame_functor.py`. |
| 1e | Shear-swap pitfall | PASS | The registered lower endpoint stays 11/100 with W² = 4/100 (A5, A10). A7 and A11 show that the shear-only corner gives 15/100 ≠ 11/100. D14 and E2 declare the statement refuted rather than moving the endpoint to 15/100. |
| 1f | Frobenius (C11), by hand | PASS | Hand derivation: ∂_[c n_d] = (∂_c N n_d − ∂_d N n_c)/N, using the symmetric Hessian and torsion-free Γ. The projector then gives h_b^d n_d = n_b(1 + n·n) = 0, so ω_ab = 0 for any lapse and any symmetric Γ. |
| 1f | Frobenius (C11), SymPy | PASS | Fully symbolic generic jet: arbitrary N, dN, symmetric Hessian, symmetric Γ, and generic n^a rescaled so n^a n_a = −1. Every `vort` component simplifies to 0. |
| 1g | Upper witness, numerical | PASS | Exact recomputation with H = 1, w = 0, Ω_m = 3/10, κ = 1: Σ² = 3/25, Ω_k = a²/H² = 1/50, Ω_tilt from n-frame T₀₀ = 3/100, net flux = 0. Momentum k·a·s1 + κq = 0 for k ∈ {3, −3, 1, 7/2}. Ω_Λ = 53/100, Gauss = 1, x_C = 17/100. |
| 1h | Pair-density finding (C9/C10) | PASS (genuine source defect) | PR-187 `omega_tilt_antipodal_pair(fixed_total_density=True)` gives the single-stream value; per-stream doubles it. The egs3 modules invert with sinh²β = Ω_tilt / (2(1+w)Ω_m) = 1/20, using Ω_m = 0.3 per stream (`MU_REF = 1`). Gauss counts rest mass 0.3, but the pair's rest mass is 0.6. Under the fixed-total reading the same β yields excess 3/200 ≠ 3/100. The egs3 witnesses are therefore internally off by a factor of 2 (either in Ω_tilt or in the Gauss rest-mass term). Comparator target values are unaffected. Lean's `tiltPair` matches PR-187. This is a code defect in the egs3 modules, separate from any method limitation. |
| 1i | Frozen-target fidelity | PASS | All 49 ids (A1–A11, C1–C14, D1–D21, E1–E3) match the Lean signatures. Compile_01 → 02 changed proof scripts only (diff checked: projection depth, simp args, `h1w`); no signature changed. Refutations are quantified over every k, every `EvolSys` and every T, which is a strengthening. |
| 1j | Negative controls | PASS | C13 `badJet` gives vort₁₂ = −1/2. A11 is the shear swap. C10 is the mixed label. My own control `noNormJet` (n·n = −1 dropped, spatial dN ≠ 0) gives vort₁₀ ≠ 0, so the normalisation clause is load-bearing. |
| 2 | No assumed conclusion, no vacuity | PASS (with a note) | Attainability predicates appear only as conclusions, as premises of the ladder implications, or inside negations. Non-vacuity is shown by C14, D20 and D12. My `eleven_attained_wide` (Σ² ∈ [8,12]/100) shows the refutation depends on the registered box plus W²[n] = 0, which is faithful to roadmap line 244 ("sign-corner must equal the optimiser's"). Note: my `fullDynSharp_nonvacuous` proves `FullDynSharp` for a W-null box using a trivial 0-dimensional `EvolSys`. The predicate is not structurally false, but the generic Local/Global predicates carry no physics until O1 pins S_reg. |
| 3 | Integrity | PASS | Recomputed sha256 of SOURCE_RECOVERY `0e5b539c…`, lean `5456b6ce…`, AxiomAudit `de1ef9a7…`, olean `ce3b9de7…`, harness `c0d26ab3…`, and all compile_0{1,2,3} json/source/stdout/stderr: all match AUTHOR_RETURN. Exit codes 1/0/0; the failed attempt is kept. `raw/FROZEN_TARGETS.presha256` (18:22:57Z, hash `1042db17…`) equals the current file and predates compile_01 (18:25:32Z); this is self-attested and not git-committed. Forbidden-token grep (`sorry|admit|native_decide|axiom|set_option|maxHeartbeats|unsafe|implemented_by|extern|opaque`) on `T/lean` and the audit file: empty. |
| 4 | Independent recompile | PASS | `cd /home/cosmosapjw/lean_oracles/viii_oracle && lake env bash -c "LEAN_PATH=<rerun>:$LEAN_PATH lean -R <rerun>/src -o <rerun>/R190AComparator.olean <rerun>/src/R190AComparator.lean"`: exit 0, 26 s, one unused-variable warning (`hlo`, line 805). Toolchain v4.31.0, mathlib rev `fabf563a…` (from the manifest). My olean sha is `a0b336b4…`, which is not byte-identical to the author's `ce3b9de7…`; that is non-gating. |
| 4 | My audit file | PASS | `audit/ReviewAudit.lean`: `#print axioms` for all 62 public theorems plus 4 reviewer theorems. Exit 0; 66/66 print `[propext, Classical.choice, Quot.sound]`; no other axiom set. |
| — | Acceptance: signatures do not assume attainability | PASS | See check 2. |
| — | Acceptance: PR-186/187 convention cross-check | PASS | C1–C6 prove the W²/Σ² identities universally. Frame is typed (`FrameG .n`). The pair label is checked against `frame_typed_algebra.py:216-231`. |
| — | Separate sharpness predicates | PASS | Algebraic, Constraint, Local and Global are distinct, and E1 proves the ladder between them. |
| — | Pitfall: thin docs or missing lemma not used as permanent blocker | PASS | O1/O2 (transcribe the KE-DYN / Bianchi-V system, constraint propagation, Picard–Lindelöf, ≥ 5 e-folds) are kept as open proof obligations. X1 is a genuine owner definition choice. |
| — | Comparison with `bae6ac2df` | CONSISTENT | It is not an ancestor of HEAD (`merge-base` exit 1). Same verdict; its Lean axis is definitional (`spatialDerivative := 0`). R190-A adds the derived Frobenius lemma, the exact constraint image, typed corner/value maps and the convention audit. |

## Blocking findings
None.

## Non-blocking notes (exact fixes)

1. **Citation completeness.** Add to SOURCE_RECOVERY §3/§4 the contrary-reading sources and why they do not govern: steelman H03 (`01_HOSTILE_REFEREE_STEELMAN.md`), `frame_typed_algebra.py:5-6` ("u-frame tilt/vorticity"), and `revival_frame_functor.py:34-35,77` (PR-212 `W2_n`/`W2_u`).
2. **Hash and line typos in SOURCE_RECOVERY.**
   - `egs3_graded_comparator.py` suffix `…b6c6` should be `…d6b7` (full `3332c3af…68c7d6b7`).
   - `t3_king_ellis.yaml` suffix `…1e0` should be `…e1b0`.
   - `egs3_king_ellis_frame.py` "20-21" should be 23, and "51-54" should be 60-61.
   - The prefixes are correct and the files are unchanged.
3. **Undisclosed tool tasks.** The card's `tool_tasks` (wolfram_xact, sympy, sage_singular) were not run, and AUTHOR_RETURN's `not_claimed` list does not say so. Add a disclosure line. My SymPy replay (Frobenius generic jet, upper witness, pair labels) can be cited as an independent non-author check.
4. **Generic predicates.** `LocalDev`/`GlobalDev` over a generic `EvolSys` are trivially satisfiable for degenerate S (shown in my audit). O1 must fix S_reg, its encoding, the constraint set, and the e-fold horizon, or no positive local/global claim is meaningful.
5. **Decoupled jet.** `HomData.jet` is not tied to the Bianchi data. This is harmless, because W²[n] = 0 for every valid jet, and it actually broadens the refutation to any foliation. Say this explicitly. Also add one sentence that, by C11, the refutation extends to every class whose comparator W² is a hypersurface-normal vorticity (Bianchi III/KS/non-LRS per the roadmap), while noting this is not stated as a Lean theorem.
6. **Downstream consistency.** `revival_sharpness_ladder.py:61-75` (`build_certified_ladder`) marks constraint as ATTAINED and local as ATTAINED_WITH_OBLIGATION without naming an endpoint. Given D10/E3, consumers must read that as upper-endpoint-only. Route this to the owner.
7. **egs3 pair-density defect (check 1h).** Route to the egs3 owner. The β values in `egs3_linearized_realization.py`/`egs3_nonlinear_realization.py` are off by a factor of 2 relative to PR-187's fixed-total default.

## Counting recommendation
- **Count as:** one formally verified negative closure of PR-190 at constraint level. Under the source-registered slice-normal comparator, the registered full statement (lower, upper and every interior value) is refuted for all k, all `EvolSys` and all T. The lower endpoint 11/100 and every x < 15/100 (including the interior challenge 12/100) are not constraint-attainable. The upper endpoint 17/100 is constraint-attained only (Bianchi V witness, Ω_Λ = 53/100). Proof-level count: 49/49 frozen targets, 62 theorems.
- **Suggested PR-190 status:** `COMPLETED_FAILED_WITH_RECEIPT`, matching `bae6ac2df`, subject to owner adoption. `success_dependency_satisfied` stays false.
- **Do not count as:**
  - PR-190 success;
  - any local or global dynamical attainability (O1/O2 are open);
  - a new scientific discovery — the obstruction is the 2026-07-10 withdrawal re-derived, and only the formal Frobenius derivation and the exact constraint image are new;
  - a replacement identified interval. Citing [15/100, 17/100] as "the PR-190 interval" or its lower endpoint would be exactly the forbidden withdrawn-W² → shear-corner swap.
- AUTHOR_RETURN's `status: ALL` refers only to the frozen targets.

## Not proved (always)
- Scientific admission: **HOLD**.
- Local or global Einstein–matter development of any endpoint or interior point (O1/O2).
- The registered evolution system itself, and the ≥ 5 e-fold horizon.
- Any statement about W²[u] or its re-attribution (X1).
- Uniqueness of the declared class.
- A sign condition on Λ.
- The momentum coefficient 3, which is left open by quantifying over all k.
- Publication use, data inference, native-solver results, family identification.
- Wolfram, Sage or SymPy CAS axes by the author.

## Proposed VALIDATION_MATRIX scientific row (not written)
`R190-A | PR-190 comparator attainability | Frobenius ω[n]=0: PASS (Lean general + SymPy generic jet) | upper witness Gauss/momentum/Ω_Λ=53/100: PASS (exact) | lower 11/100 & interior 12/100 constraint-unattainable under n-definition: PASS (Lean) | pair-density label: CONCERN (egs3 factor-2 vs PR-187 fixed-total; code defect, owner-routed) | local/global dynamics: NOT_TESTED (O1/O2) | W²[u] reading: NOT_APPLICABLE (X1 owner choice) | verdict PASS_WITH_NOTES, admission HOLD`

## Files
- Reviewed package: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/ALL_OBLIGATIONS_20261011_SOURCE_RECONCILIATION/R190-A_einstein_matter_comparator_v1_20261023/`
- Recompile copy and olean: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/src/R190AComparator.lean`, `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/R190AComparator.olean`, `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/compile_main.out`
- Reviewer audit: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/audit/ReviewAudit.lean`, `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/audit.out`
- SymPy checks: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r190-a_rerun/checks.py`
