# Current CAS15 continuation — formally checked spectral closure

Current branch `proof/cas15-ls-matrix-synthesis-20261008`; task baseline was
`a79366286bfb9d9e9446e5eac80d017e16a0ae73`, tree
`d6b94b27b93dff187d54017181c6f1e3ed9b5d68`. The new reviewed task files are
`CoercivityBridge.lean`, `OrderedMatchingBridge.lean`, `FullSynthesis.lean`,
their narrow logs, and `review/FORMAL_CLOSURE_REVIEW.md`; no CAS07 or older
#507 evidence was restarted or edited.

`CAS15Coercivity.rotated_coercivity` is **FORMALLY_CHECKED** for the actual
Frobenius/skew representation from an explicit real orthogonal diagonalization
and pairwise spectral-gap witness, with no supplied `hcoerc`. It remains valid
at zero gap. `CAS15OrderedMatching.matrix_ordered_matching` is
**FORMALLY_CHECKED** for all decreasing same-index eigenvalues, including
repeated eigenvalues, from the induced Euclidean operator norm. It has neither
a permutation nor an assumed matching premise. `CAS15FullSynthesis` composes
both bridges with the existing least-squares/mixed-norm proof: its error bound
divides only under an explicitly positive observed gap, and its ordered-gap
bound does not assert positivity when `delta - 2 epsM` is negative.

Fresh final execution is `build_logs/20261009T000200000000Z/execution.json`:
Lean 4.31.0 and pinned mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`;
version plus eight modules all exited 0 and the final axioms are only
`propext`, `Classical.choice`, `Quot.sound`. The preceding two integration
receipts are preserved failures, not success evidence. A fresh read-only
reviewer requested as `gpt-6-astra/ultra` returned **PASS_SCOPED** with no
blocking finding; observed runtime is `UNKNOWN`. See
`review/FORMAL_CLOSURE_REVIEW.md` for precise scope and residual limitations.

Formal coverage is limited to the theorem inputs: the final synthesis accepts
an explicit orthogonal diagonalization/pairwise-gap witness rather than
constructing it from symmetry. Historical four-axis status remains `NOT_RUN`;
scientific admission remains `HOLD`. Next mathematical task after publication:
CAS16-C03 Cartesian monomial connection.

---

# Previous CAS15 continuation — reviewed analytical result / partial formal coverage

Branch `proof/cas15-ls-matrix-synthesis-20261008`; pre-publication HEAD `6668510c16883e9036add8a8dde8c51fceba24e1`, tree `c51db5cb7cf3915a2ec53fd67f60d5c62eea2227`. Upstream reviewed CAS07 payload `07d7acfcbea65a16f0e601b527e536a42793688c`, publication metadata tip `490102784822758fb2b108718e804b4a587a585d`, tree `b7f5dddf673187c273f68f453e73b7828c93be36`; PR506 OPEN and R1 identity verified. Full #497 single-commit head `f6dde6fcd870e2c4676dc08209b4a89fa1bc8737` integrated once as `6668510c16883e9036add8a8dde8c51fceba24e1`; all 88 source/evidence blobs equal original. Sole extra local publication receipt preserved untracked; all original 89 files remain byte equal to backup `/tmp/htt-cas15-497-original-20261008`. Failed first integration preflight/untracked-overwrite and historical post-checkout hook error recorded in integration_failures.txt. No reset/clean/stash/new checkout. Original dirty tracked candidates remain untouched.

New obligations: genuine skew Frobenius matrix domain; arbitrary-data least-squares projection/contraction, squared-loss-minimizer contraction, residual identity; full mixed Euclidean-operator/Frobenius commutator bound; exact encoding bridge and perturbation synthesis given coercivity — FORMALLY_CHECKED. Arbitrary rotated coercivity and all-three-index Weyl matching — DERIVED in SPECTRAL_NOTES.md, not formally kernel closed. The full mathematical perturbation theorem and gap comparison are DERIVED with these explicitly proven analytical bridges. Formal coverage is stated exactly in RESULT.md; pointwise eigenvalue matching is not misreported from an assumed premise.

Actual new integration build: `python …/ls_projection_continuation_v1_20261008/build.py`; logs build_logs/20261008T123443937379Z. Version/Projection/Frobenius/Mixed/Spectral/Synthesis all exit0; pinned Lean4.31.0/mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. Synthesis standard axioms only; new author raw compile failures and original Projection attempt1 remain preserved; Mixed attempt1.console_transcript.txt is a labeled summary, supplemented by the exact original tool response and stdout in attempt1.raw_tool_output.json/attempt1.raw_console.txt. Historical #497 contracts/adjudication/failures unchanged. All three native authors requested and observed gpt-6-sol/high; shared helpers/results are collaborative evidence. Authors explicitly stopped after completion.

Separate fresh native reviewer requested gpt-6-astra/ultra, production read-only, first declarations and independent reasoning then proofs/logs. Review completed: PASS_SCOPED_SUCCESSOR_REVIEW, no blocking findings; full DERIVED theorem and precisely bounded FORMALLY_CHECKED subset accepted. Requested and observed reviewer gpt-6-astra/ultra, session 01a11b85-2ced-7750-8f4d-87477adccac2, turn 01a11b85-2d8e-7c21-865c-c1ab1ce19ceb. Fresh build all six steps exit0, 16 theorem axiom outputs standard-only. Two P3 documentation/raw-evidence findings closed with exact transcript comparison, no mathematical source changes. Report/identities/commands/logs in review/. Reviewed new task files are ready for explicit stage/commit/non-force push; publication receipt follows below. No four-axis validator was run or passed; scientific admission HOLD.

UNRESOLVED formal scope: general orthogonal conjugation/coercivity and ordered-eigenspace intersection in Lean, yielding a fully formal arbitrary-symmetric-matrix theorem. One next actual mathematical theorem: prove `∀ X ∈ skew, deltahat * ‖X‖F ≤ ‖[Mhat,X]‖F` from the orthogonal eigenbasis and gap, without an hcoerc input. Reuse Frobenius.lean/Mixed.lean/Spectral.lean/Projection.lean/Synthesis.lean. Next command: `python …/ls_projection_continuation_v1_20261008/build.py --log-dir /tmp/NEW_NONEXISTING_LOG_DIR`. No full historical component closure, catalog fit, observation analysis or scientific promotion.

Publication preparation checks: canonical `validate_pr_dag.py` returned 213 PRs/DAG valid; this successor has no changed canonical DAG node, so no status/mirror row was manufactured. `git diff --cached --check` reports only two trailing-whitespace lines (17/19) in the preserved raw Frobenius first-failure stdout. These raw bytes are intentionally retained; source/document whitespace checks are clean. Reviewer completed thread explicitly stopped. All 21 original tracked dirty file hashes remain unchanged. Reviewer build logs were explicitly staged despite the generic build-directory ignore rule.

## Publication continuation

Reviewed task payload commit `fd33494a26647ce55ede05975cbd0ffe701387f5`, tree `b011f925ed55e74ec87c9862f7e7bfa03340f0f3`. Explicit staging contained 100 files only inside this task directory. `git push -u origin proof/cas15-ls-matrix-synthesis-20261008` exited0; remote ref query returned the exact payload commit. `gh pr create` exited0 and created https://github.com/cosmosapjw-quantum/htt_base/pull/507, OPEN, base `proof/cas07-conditional-synthesis-20261008` (#506). No original PR or main was merged/closed/forced. Remote main remains f1007dd3e41c07eccd64024dd6b44fb5a40a3612. Routine R1 verification uses provider success and exact ref/commit, without content redownload. This receipt-only follow-up does not change reviewed proof/build/analytical sources. Current tip includes the follow-up and is resolvable with `git rev-parse HEAD HEAD^{tree}`.

CAS07 first requested unit is complete and published #506. CAS15 new analytical successor and enumerated formal bridges are reviewed and published #507; fully formal arbitrary-rotated spectral closure remains UNRESOLVED. Do not mark historical C03/FULL CAS15 accepted from this result. Continue with the precise coercivity kernel theorem above, then ordered matching; defer CAS16 Cartesian synthesis until the chosen CAS15 formal continuation boundary is resolved or explicitly selected otherwise. All native author/reviewer threads completed and explicitly stopped.

---
# Preserved prior-session partial handoff (superseded current scope above)

# CAS15-C03 least-squares continuation candidate

FORMALLY_CHECKED: `least_squares_projection` and `least_squares_error_contraction` for an arbitrary linear map into a finite-dimensional real inner-product space, arbitrary data r, and a genuine global least-squares minimizer. `perturbation_from_least_squares` is FORMALLY_CHECKED conditional on separately supplied coercivity and noise bounds; it does not derive those matrix estimates.

The minimizer premise is ∀x, ‖r−A(what)‖≤‖r−A(x)‖. It is a minimizer definition, not the requested perturbation conclusion. The range contains A(what); the premise establishes that its distance is the infimum over the range. Mathlib's norm-minimality/orthogonality equivalence identifies A(what) with the range projection. Since A(w) is fixed by that projection, A(what−w)=P(r−A(w)); projection contraction gives the error estimate. There is no exact-fit assumption A(what)=r and no restriction on arbitrary r.

DERIVED concrete interpretation: choose the skew-matrix domain and the full 3×3 matrix space with the Frobenius inner product. Squared-loss minimality and norm-loss minimality are equivalent because norms are nonnegative. Then the general lemma applies to A(X)=[Mhat,X]. This concrete interpretation has not yet been encoded with Lean's matrix/Frobenius types; do not silently use mathlib's default matrix norm as Frobenius norm.

Actual execution: pinned Lean 4.31.0/mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f, `lake env lean <absolute Projection.lean>` from `/home/cosmosapjw/lean_oracles/viii_oracle`. attempt1 exited 1: the library projection equality was oriented opposite to the target. Its downstream sorryAx reports belong only to that failed compile. The author added `.symm`; attempt2 exited 0 and all three theorem axiom reports are `[propext, Classical.choice, Quot.sound]`. Commands, raw stdout/stderr/exits and final source hash retained in attempt2; raw first failure retained in attempt1. No mathematical counterexample.

Source check: fetched #497 head `f6dde6fcd870e2c4676dc08209b4a89fa1bc8737`, matched local BLOCKER.json, EXECUTION_CONTRACT.json and lean/CAS15C03.lean byte-for-byte. Contract SHA256 `536b6e955deb1627fcad72a332fe63db2622792421202d5865c4650e6e7a46b9`. #497 was fetched/read, not cherry-picked into the CAS07 integration branch. Existing CAS_CONFLICT/BLOCKED records remain untouched; this is a new partial result, not their adjudication.

UNRESOLVED: formal Frobenius/skew matrix instantiation, mixed operator/Frobenius commutator bound, arbitrary rotated coercivity, Weyl ordered-eigenvalue perturbation; separate independent review. No full CAS15-C03 completion, publication or scientific admission. Owner htt; transfer source none; scientific HOLD.

Next actual mathematical action: instantiate `least_squares_error_contraction` on the skew subspace and Frobenius Euclidean matrix space, derive the residual identity `(Rhat−R)−[Mhat−M,W]`, and connect the mixed norm estimate. Do not assume exact fit.
