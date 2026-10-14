**Independent review: conditional CAS07 analytic synthesis — SCOPED VALID; no blocking findings.**

Reviewed candidate: `conditional_synthesis_v1_20261008/lean/Synthesis.lean` at SHA-256 `39bf9debfd249e274a9c840f1c096a1bad692e605ff6c9286c284821e0d5f770`. Review was read-only in the existing checkout, branch `proof/cas07-conditional-synthesis-20261008`, initial HEAD `5adf5e75b975d9dd12c20cb7c928ed96a510dd0c`. All reviewer-created files are under `/tmp/cas07-review-20261008`. No historical campaign, four-axis adjudication, publication, or installation was rerun. `RETURN.md` and `RESULT.md` were not read. Existing dirty state was preserved.

The main theorem is mathematically valid under its exact supplied-function premises, and a fresh narrow Lean compile passed. This is independent review of a conditional analytic theorem. It does not establish C01, construct physical functions, prove a spacetime/optical realization, pass an old four-axis campaign, or change scientific admission from HOLD.

**Independence and order.** I first inspected the target declaration, `ScalarPremises`, `JacobiPremises`, and exact M01/M02/M03/M04/M05/C02/C03/M06 interfaces, without the synthesis proof body or author assessments. Independent derivation and attempted boundary counterexamples were recorded in `preproof_reasoning.md` before opening the proof and execution records. I subsequently audited the full new proof, full M02/M05/M06 proofs, the pertinent M04 majorants and C02 determinant/sign argument, the build script, original build logs, and preserved first failures. The older M01/M03/C03 proof bodies were not fully re-audited; their exact declarations, mathematical role, accepted binary identities, and actual imported types were checked. No subagents were used.

**Mathematical and formal checks.**

| Check | Result and exact scope |
|---|---|
| Target as assumption | PASS. `Synthesis.lean:18` constructs C03.Premises. The Taylor field is obtained from M02 at lines 30–32; positive distance and the two screen bounds come from M05 at lines 26–29; eta order comes from M01. Neither the Taylor error nor determinant/distance conclusion is a field of the input scalar/Jacobi structures. |
| Supplied Jacobi regularity | PASS. Euclidean R2 continuous linear operators; D and D1 have the specified within-interval derivatives throughout [0,L], D2 and R are continuous there, D(0)=0, D1(0)=Id, D2(t)=−R(t) composed with D(t), and the induced Euclidean operator norm of R is at most K. No symmetry, diagonalizability, constant R, or commutation is assumed. |
| Scalar regularity | PASS under the exact M02 contract. Z and Z1 have full `HasDerivAt` witnesses at every point of [0,L], including endpoints; Z2 is continuous on that interval and bounded in absolute value by M2 there. Full endpoint differentiability is stronger than one-sided differentiability and must remain explicit in downstream descriptions. |
| Norm/coordinate conversion | PASS. `M05.matrixOf` is the inverse Euclidean matrix-to-linear-map conversion. `M05.opnorm_error_eq` identifies C02.euclideanOpNorm with the M04 continuous-linear-map norm exactly. No Frobenius norm or default matrix norm is substituted, and no missing dimension factor occurs. This theorem is specifically two-dimensional. |
| Determinant and root sign | PASS. Norm closeness with eta<1 controls singular values and fixes positive determinant even for nonsymmetric matrices. C02's inspected 2x2 argument independently proves the sign; M05 transfers it. The synthesis squares nonnegative bounds only after obtaining positive distance and `Real.sq_sqrt`. |
| Scalar slope and intercept | PASS. Z0=Z(0), H0=c Z1(0), c>0. Every displayed residual retains Z0. Absolute H0 handles both slope signs. M02 supplies the integral Taylor bound for every subinterval [0,s]. |
| C03 FD1–FD3 | PASS. FD1 combines Taylor with |s−dA|≤s eta. FD2 uses the positive global denominator 1−eta(L). FD3 uses c>0, dA>0 and the local denominator. No new scalar or geometry target is assumed. |
| M06 refinement | PASS. For q=dA/(1−eta(L)), both s≤L and s≤q give s≤min(L,q)≤L. Both min projections are used to prove the refined RHS is bounded above by FD2; eta monotonicity is applied only at positive arguments. `min_branches` proves both branches, including equality. The refinement is no worse than FD2; strict improvement is not claimed. |
| K=0, H0=0, M2=0 | PASS. K=0 has f=s and eta=0 for positive s; the accepted exact zero-curvature controls give D=s Id and dA=t=s. Zero H0 or M2 removes the corresponding term without division by it. Both zero give zero scalar residual. The universal theorem includes these cases. |
| eta(L) approaching 1 | PASS. Every eta(L)<1 is covered; denominator growth is permitted. Equality 1 and values above it are excluded, and no uniform finite limiting bound is asserted. |
| s=0 separation | PASS. The main theorem requires s>0. `closed_interval_controls` covers [0,L] for norm/deviation and scalar Taylor bounds without eta or distance division. The current totalized definition has eta(K,0)=−1, not its analytic limiting value 0; an additional reviewer Lean example verified this. No candidate conclusion uses eta at zero. |
| Physical units/realization | NOT_APPLICABLE beyond algebraic consistency of the declared real scalars. The c factors match the stipulated H0=c Z1(0). No geometric/observational interpretation of the supplied functions is derived. |

**Exact formal coverage.** `conditional_analytic_synthesis` quantifies over every real 0<s≤L. It returns both Jacobi norm majorants, the coordinate operator-norm error bound, strict determinant positivity and squared determinant bounds, positive dA=sqrt(det D) and its two bounds, positivity of both denominators, the derived scalar Taylor bound, FD1–FD3, s≤t≤L and t>0, eta(s)≤eta(t)≤eta(L) with eta(s)≥0, the refined FD1 residual bound, and the refined-RHS≤FD2 comparison. `closed_interval_controls` covers the three non-divided bounds on the entire closed interval, including zero, without requiring eta(L)<1. `min_branches` is a definitional theorem. No C01 symbol occurs in the scientific import chain.

The dependency chain is M04←M03; M05←M01+M04+C02; M06←M01+C03+M05; synthesis←M02+M06. Six unchanged accepted interfaces (M01, C02, C03, M03, M04, M05) were reused after verifying their exact recorded `.olean` digests. These digests also match preserved dependency execution metadata. M02 and M06 were rebuilt from their unchanged sources as the missing imports. Actual imported types were printed from Lean in `ReviewChecks.stdout`, confirming the premises used by the compiled theorem. Historical source-to-cache generation was not repeated, in accordance with the task's reuse boundary.

**Direct execution and evidence.** The reviewer ran:

```sh
python3 /tmp/cas07-review-20261008/compile_review.py
```

The script uses the exact binary `/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean` with explicit LEAN_PATH entries for the temporary build directory, accepted oracle, and existing package libraries. Each compile is `lean -R /tmp/cas07-review-20261008/lean -o <temporary module.olean> <temporary module.lean>`. Commands, cwd, LEAN_PATH, durations, hashes and exits are recorded in `execution.json`.

| Direct step | Exit |
|---|---:|
| Lean version | 0 |
| CAS07M02Accepted source compile | 0 |
| CAS07M06Accepted source compile | 0 |
| Synthesis source compile | 0 |
| ReviewChecks dependency signatures, axioms and eta-at-zero check | 0 |

Observed Lean is 4.31.0, commit `68218e876d2a38b1985b8590fff244a83c321783`. The repo and oracle toolchain files match exactly. Package revisions agree; the actual mathlib checkout HEAD is `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, matching both manifests. Manifest byte differences are packaging metadata, not a mathematical failure. All stderr logs are empty. M02 emits its existing unused-section-variable warnings; no new warning or failure was observed. The four synthesis declarations report exactly `[propext, Classical.choice, Quot.sound]`; no `sorryAx` or additional axiom is present.

Original `logs/20261008T104259728756Z` commands, raw stdout/stderr and zero exits were inspected and their three source hashes match the reviewed sources. The preserved prebuild failure record contains the initial byte-manifest assertion and incorrect-root FileNotFoundError, both before Lean. The current build.py root resolves correctly. Its fixed, machine-local oracle is an explicit replay dependency; this review does not claim a standalone clean-host rebuild. I did not execute build.py itself because it writes production logs; the narrow independent script performs the equivalent selected compilation with all writes redirected to the permitted temporary directory. No fresh reviewer failure was encountered.

**Source binding.** All eight scientific dependency sources were unchanged between initial and final hashes. Synthesis and build.py final identities are included below; `source_identity_final.json` contains their complete repository paths and the reused artifact hashes.

| Source/module | SHA-256 |
|---|---|
| CAS07M01Accepted | `42ebc3e44a3104a7c7f67b8f608b41de704cba0d379f6191138aea580503443d` |
| CAS07M02Accepted | `19cc4dc624b54a983719989ecab650c1663b3241b1c8185ed9f4ec9ded45a00e` |
| CAS07C02Accepted | `695076b63464f425d2af034d2edfd3fc8b2a7709311388407f78d2175c6e4c75` |
| CAS07C03Accepted | `382fb440cdd16664a5aee08db13501c5d1f8b4164e172f5ce9da876b7d32a976` |
| CAS07M03Accepted | `98497a877b4a8be30f7449c706229c9e64070d84968951cc729a1a2ff3a74102` |
| CAS07M04Accepted | `39b7c46060a144baa98dc512c4768a159ed4be13df779dbd3a3cd19bf80176c9` |
| CAS07M05Accepted | `0e10bfac397e7f5e5d67166425f0cda6273c2ecdafdb561396a9503a954704af` |
| CAS07M06Accepted | `03e85f5b7e26d9bfd64c83a732deff22f46a6a46029b38c6e9a0bd8db2c5bb03` |
| Synthesis | `39bf9debfd249e274a9c840f1c096a1bad692e605ff6c9286c284821e0d5f770` |
| build.py | `a1e38cdfe0cc07f028abdd2bd53111c7e7eafff1bdf5d5435c10fe09a1742915` |

**Runtime.** Requested reviewer: gpt-6-astra / ultra. Observed reviewer: gpt-6-astra / ultra, directly read from actual session metadata and turn_context in `/home/cosmosapjw/.codex/sessions/2026/10/08/rollout-2026-10-08T21-25-22-01a11b79-afc0-7282-932e-7fbb7c9777e6.jsonl`. Session `01a11b79-afc0-7282-932e-7fbb7c9777e6`; turn `01a11b79-b00b-73c1-a4f5-52e21579b870`; parent `01a11b77-7e3d-7cc2-a68c-e3dea0aefb40`; agent path `/root/cas07_review`; CLI `0.159.0-alpha.12.1`. The metadata-only extraction is in `runtime_observation.json`. I did not author this candidate.

No blocking findings or mandatory repairs remain within this review scope. Production scientific/report files were not modified. This report is bound to the hashes above; subsequent changes to proof, premises, build dependencies or claim scope require assessment of the changed portion.
