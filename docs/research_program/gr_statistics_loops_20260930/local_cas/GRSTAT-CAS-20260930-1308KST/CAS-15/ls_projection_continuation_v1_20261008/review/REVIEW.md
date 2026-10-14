# CAS15-C03 independent successor review

**Verdict: PASS_SCOPED_SUCCESSOR_REVIEW. Blocking findings: NONE.** The full stated mathematical perturbation bound and same-ordered-index eigenvalue/gap comparison are correctly DERIVED. The exact subset labeled FORMALLY_CHECKED is supported by inspected Lean proofs and a fresh successful build. This verdict is for the new strength-based successor; it does not adjudicate the historical four-axis contract, close the fully formal rotated-matrix theorem, or change scientific HOLD.

## Candidate and independence

Repository: `/home/cosmosapjw/Dropbox/bianchi/htt_base`; branch `proof/cas15-ls-matrix-synthesis-20261008`; base HEAD `6668510c16883e9036add8a8dde8c51fceba24e1`; base tree `c51db5cb7cf3915a2ec53fd67f60d5c62eea2227`. The reviewed new files were working-tree candidates on this base. Exact reviewed source/document hashes are in `REVIEW_IDENTITIES.json`; the source hashes below bind the proof verdict independently of later review-status/publication metadata edits.

Task directory C: `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/ls_projection_continuation_v1_20261008`.

I did not author the candidate, received no previous reviewer verdict, created no subagents, and kept the production repository read-only. All reviewer-generated evidence is under `/tmp/cas15-review-20261008`. First read operating instructions and only definitions/declarations/dependencies of the five modules. Before inspecting proof bodies, author assessments, notes or logs, recorded an independent derivation and failure probes in `INDEPENDENT_PRECHECK.md`. Then inspected all proof bodies and the analytical bridges. The author's two targeted documentation/evidence repairs were checked afterward; no mathematical source changed.

Requested reviewer settings: **gpt-6-astra / ultra**. Observed reviewer settings: **gpt-6-astra / ultra**, directly verified from matching session metadata and turn context, not inferred from the request. Session `01a11b85-2ced-7750-8f4d-87477adccac2`, turn `01a11b85-2d8e-7c21-865c-c1ab1ce19ceb`, agent path `/root/cas15_review`, correct repository cwd. Evidence: `/home/cosmosapjw/.codex/sessions/2026/10/08/rollout-2026-10-08T21-37-55-01a11b85-2ced-7750-8f4d-87477adccac2.jsonl`, metadata lines 1 and 8. Independently checked the three author session/turn IDs in RESULT.md: all observed gpt-6-sol/high with their stated cwd; that observation does not imply independent rediscovery or review.

## Mathematical audit

Assumptions: real symmetric 3x3 M and Mhat; W and What in the actual real skew subspace; R=[M,W]; arbitrary real Rhat; nonnegative epsR, epsM, Wstar with Frobenius data/noise and W bounds; induced Euclidean operator perturbation bound; positive minimum pairwise observed eigenvalue gap deltahat; global LS minimizer over all skew matrices. Norm and squared-norm minimizers agree by nonnegativity. This is finite Euclidean matrix algebra: no Lorentzian norm, physical reconstruction, transfer model, or observational inference is introduced. The units are homogeneous under [R]=[M][W]; both numerator terms have R units and division by a spectral gap has W units.

| Item | Assessment | Reason |
|---|---|---|
| Genuine arbitrary-data LS | Correct | Projection.lean:11-40 derives the range projection from global minimality, then applies its contraction to Rhat-A(W). It does not assume A(What)=Rhat. |
| Frobenius/skew encoding | Correct | Frobenius.lean:14-37 uses EuclideanSpace on nine entries, proves the sum-of-squares norm, defines X_ij=-X_ji for every pair, and implements MX-XM. Both off-diagonal entries contribute; no missing sqrt(2) factor. |
| Residual identity and sign | Correct | Rhat-[Mhat,W]=(Rhat-R)-[Mhat-M,W]. The formally proved identity matches the intended commutator convention. |
| Mixed norm constant 2 | Correct | Mixed.lean:24,38-91 uses the continuous-linear-map Euclidean operator norm; column bounds and transpose invariance prove both products, then the triangle inequality bounds the commutator. No default matrix norm is substituted. |
| Encoding bridge | Correct | Synthesis.comm_bridge identifies the same coordinate expressions, not merely equal dimensions or similarly named types. |
| Rotated coercivity | Correct analytical proof | SPECTRAL_NOTES.md:11-24 preserves skewness and Frobenius norm under U^T X U. Squared coefficients are bounded by deltahat^2 on every off-diagonal entry. Zero diagonal follows from real skewness. Nonnegative square roots give the unsquared inequality. |
| All ordered eigenvalue matches | Correct analytical proof | SPECTRAL_NOTES.md:33-40 uses a k-dimensional top span and a (4-k)-dimensional bottom span, whose intersection is nonzero in dimension 3. The two Rayleigh inequalities have the right directions. Swapping matrices proves the other side for each same ordered index, including repeated eigenvalues. |
| Gap loss 2 epsM | Correct | Sorted adjacent differences each lose at most 2 epsM. The nonadjacent difference is their sum, so taking the minimum is valid. Negative lower bounds do not establish positivity. |

Combining the independently checked steps gives `deltahat * ||What-W||F <= ||A(What-W)||F <= epsR + 2 epsM Wstar`; division uses only deltahat>0. No target conclusion is used as a premise of the full analytical argument.

Adversarial boundary checks: (i) Mhat=diag(2,1,0), W=0, Rhat=I has a nonzero out-of-range residual and What=0 as LS solution, so exact fitting is not required; (ii) allowing general, non-skew X would admit nonzero diagonal commuting matrices, invalidating coercivity, but the candidate's domain excludes them; (iii) repeated observed eigenvalues admit commuting skew rotations, so the positive-gap inverse condition is necessary; (iv) arbitrary eigenvalue relabeling fails already at zero perturbation, and the proof correctly uses decreasing order; (v) epsR=epsM=0 forces What=W with positive observed gap, while Wstar=0 or zero perturbation budgets cause no illicit division. These were mathematical probes, not sampled numerical evidence.

## Exact formal boundary

The kernel-checked parts are generic range projection and contraction; concrete Frobenius/skew contraction from norm and squared loss; residual identity; left/right mixed norm and commutator bounds; encoding correspondence; the perturbation implication **given coercivity**; unit-vector Rayleigh error; and scalar gap subtraction **given pointwise eigenvalue matches**.

`Synthesis.lean:19-30` explicitly takes `hcoerc`. Its lack of symmetry hypotheses is legitimate because this conditional implication is stronger than the intended symmetric application; the analytical spectral step supplies hcoerc for that application. Bounds on epsR and Wstar imply their nonnegativity even though the conditional synthesis does not separately repeat those hypotheses. `Spectral.lean:43-46` explicitly takes `hmatch`; it does not formalize Weyl matching. The sorted-triple interpretation of `orderedGap` is analytical. RESULT.md, PLAN.md and SPECTRAL_NOTES.md accurately distinguish these facts.

Still not kernel closed here: arbitrary orthogonal conjugation/Frobenius coercivity from the actual eigenbasis and gap, the ordered-eigenspace intersection bridge, and one universal formal theorem that supplies those premises from arbitrary symmetric matrices. This is an acknowledged formal-coverage limit, not a defect in the stated DERIVED result.

## Execution and raw evidence

Inspected build.py in full. It checks the unchanged Projection hash, equal toolchain bytes and equal declared package revisions; creates fresh temporary module sources/objects; compiles dependencies before consumers; retains per-step stdout/stderr/exit/timing/source hashes; fails on the first nonzero compile. Its absolute oracle path makes it a local reproducibility entrypoint, consistent with the stated environment. The local mathlib checkout is clean at `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. Inspected the relevant mathlib projection and toEuclideanCLM/operator-norm definitions to confirm statement semantics.

Executed once:

```text
TMPDIR=/tmp/cas15-review-20261008 PYTHONDONTWRITEBYTECODE=1 python C/build.py --log-dir /tmp/cas15-review-20261008/build
```

Here C denotes the exact task directory above. Actual argv, cwd, times, toolchain, package revisions and hashes are retained in `build/execution.json`. Lean reports 4.31.0, commit `68218e876d2a38b1985b8590fff244a83c321783`. Version, Projection, Frobenius, Mixed, Spectral and Synthesis all exited **0**; all stderr files are empty. All **16** printed theorem dependency lists contain only `propext`, `Classical.choice`, `Quot.sound`; no sorryAx or custom target axiom. The fresh five-source hash map exactly equals the author's `build_logs/20261008T123443937379Z/execution.json`, and final source bytes were rechecked after the documentation repair. No historical engine campaign was rerun.

Inspected all stdout/stderr and available exit evidence in the historical continuation attempt1/attempt2 and new frobenius_logs, mixed_logs, spectral_logs, plus the complete author integration build. Original Projection attempt1 is an equality-orientation elaboration failure (exit 1, downstream sorryAx); attempt2 is exit 0 without sorryAx. Frobenius initial failures are simplification/algebra/elaboration failures; its individual files do not independently record exit codes, so the fresh/integrated exits supply final execution evidence. Mixed's successful intermediate attempts 3 and 7 were preliminary, not the final axiom receipt; final attempt8 is exit 0. Spectral attempts 1-3 fail on notation/application/type issues; attempt4 is exit 0. These are preserved failed proof attempts, not counterexamples, and none is admitted as a successful proof.

## Findings and targeted closeout

No open findings.

1. **P3, CLOSED — formal wording.** Original RETURN.md:5 called squared-loss equivalence FORMALLY_CHECKED, while the explicit concrete theorem supplies squared-loss-minimizer contraction. Parent changed the phrase to `squared-loss-minimizer contraction`; verified the final text. No theorem edit or extra compile was needed.
2. **P3, CLOSED — raw failure labeling.** Mixed attempt1.console_transcript.txt is a shortened console summary, so saying all first failures were raw within those log files was imprecise. Parent added `mixed_logs/attempt1.raw_tool_output.json` and `attempt1.raw_console.txt`, preserved the summary, and clarified RETURN.md:7. Independently compared the added JSON to the exact inner exec result at author transcript line 126, `custom_tool_call_output` call `call_26a09fd625e547d9bf38d361ba1c9e5b`; compared the console file to its exact output string. Both match, exit 1, original_token_count 1144; no omitted/truncated response marker. This is combined console output, not independently separated stdout/stderr. A reviewer readback initially raced the filename refinement and then incorrectly compared the outer text-content wrapper; correcting the local inspection to the actual inner exec object closed both checks. These were reviewer inspection failures, not candidate math/build failures.

## Final proof identities

| File within C | SHA-256 |
|---|---|
| `Projection.lean` | `e32abc568e0400d5e5a1a6ddaf0044abe897bd9c77ea2f9c50bf4fdb072c4904` |
| `Frobenius.lean` | `e7e9c3f4f8998d6c3e89bf016e69cf29bab4c352129599f949a9e2f6334525ae` |
| `Mixed.lean` | `5f637968997a48560a69358e0b7726b0a532f36337d8e12965ee5ebb5238be3a` |
| `Spectral.lean` | `166f85718c297f70094dd901b08d1d252a566bae0de0ea119a3576c6cfa2437a` |
| `Synthesis.lean` | `896a4289807a3a3c0306b118215841cfcc04ebf1cae12613f5070bcc01b220bb` |

The reviewed analytical notes SHA-256 is `f4c5f98c89c162a23907d98e776b3aa40b47f34a44e6e3e82c98566019a462ce`; build.py SHA-256 is `7b9499eb74b8739928e3174b325255ceae535de0d9e6e59f0520feacc74851b5`. Other final document and raw-evidence identities are in REVIEW_IDENTITIES.json.

## Claim-tier recommendation and limits

Safe to report: the stated full finite-matrix result is DERIVED, the enumerated lemmas/conditional synthesis are FORMALLY_CHECKED, and the new successor received this scoped independent review. Maintain the explicit distinction throughout publication. Historical CAS_CONFLICT/blocked adjudication and scientific HOLD remain unchanged. No four-axis eligibility, complete CAS15/C03 campaign acceptance, physical reconstruction, observational calibration, Bianchi identification, or scientific admission follows. The review checked local candidate mathematics and evidence; remote publication/merge identity and preservation of all unrelated dirty files are the parent's separate closeout responsibility.
