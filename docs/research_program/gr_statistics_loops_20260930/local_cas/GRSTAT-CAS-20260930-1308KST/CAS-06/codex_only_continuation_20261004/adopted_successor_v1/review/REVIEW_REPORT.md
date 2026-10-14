# Independent review of the adopted CAS06 finite successor

**R1 — INFO, nonblocking — lean/C03Action.lean:638**

C03 formal derivative coverage has an explicit finite order. The matched derivative theorem proves pressure/energy values and first radial derivatives. The second-lapse theorem proves nu'' under its displayed local action-source TOV equation. The bundle does not assert all second derivatives of (m,nu,epsilon). SymPy and Sage additionally check algebraic second epsilon/m/nu jets; Wolfram checks the second epsilon jet after differentiated TOV substitutions.

**Consequence:** Do not describe this as an all-variable formal second-jet theorem, arbitrary-order jet theorem, or whole-interval action/TOV identification.

**Minimal action:** Retain the exact order and conditional hypotheses in the result description. No repair is required by the frozen contract, which does not demand an all-variable formal second-jet order.

**R2 — INFO, nonblocking — sage_singular/run.py:96**

Actual Singular coverage comprises two localized C01 ideal-membership certificates. C01_G00 and C01_G11 target numerators are multiplied by r; the ideals contain metric/ODE generators, not target residuals. Raw output records Singular 44100, both zero remainders, and a completion sentinel without errors. Independent Sage calculations cover C01-C04.

**Consequence:** This is a SageMath-plus-Singular axis, with two meaningful Singular certificates; it does not provide separate Singular proofs of every assertion.

**Minimal action:** Preserve the existing singular_coverage field and two-certificate scope. No repair is required.

**R3 — INFO, nonblocking — REVIEW_INPUT_MANIFEST.json**

The seal is not a standalone archive of every installed computation/proof dependency. All 1039 candidate/evidence files match. The Lean runner records the pinned toolchain and mathlib revision, rebuilds owned sources, and uses installed library paths. The complete external library source/binary distributions are outside this seal.

**Consequence:** Evidence supports source-bound execution in the recorded local environment, not byte-identical restoration on another machine.

**Minimal action:** Retain the reproducibility limit. No additional archive or gate is required for this review.

**Verdict: PASS_FINITE_COMPONENT_REVIEW. Scientific admission: HOLD.** No blocking finding or required candidate repair. This report is independent review, not new four-axis adjudication or parent admission.

**Identity and seal.** Existing checkout HEAD f1007dd3e41c07eccd64024dd6b44fb5a40a3612. All 1,039 files / 14,705,435 bytes matched before inspection and after the selected compile. Manifest SHA-256 a725c2edeb6c3c61a4f7ac7e503efac66c213bc87a453fa5112d9516045ace70; contract 9936c95ac128126d34688bbd8ece9fb90c92aa7dfeea8fa7b41716ab449e88f3; admitted inputs 711de321c374a85b4b0414d5df1f8a62b55368f73c2a3d31e502e209af8793eb. Owner adoption supplies the neutral definitions/frame, selected derivative and fixed acceleration family. The original bdec…562b0 contract remains CAS_CONFLICT (Wolfram PASS; other three MISALIGNED_ASSUMPTIONS).

**Component coverage.**

- **C01: COVERED_CONDITIONAL_FINITE_COMPONENT.** Metric, inverse, actual coordinate metric derivatives, Christoffel, Riemann, Ricci and Einstein constructions are present. Six independent diagonal curvature pairs, mixed components, and all off-diagonal Einstein components are covered. General-Lambda Einstein/source identities use the three admitted TOV equations and differentiated lapse equation. Lean assumes local differentiability/ODE conditions, not curvature or Einstein conclusions. No existence assertion.
- **C02: COVERED_CONDITIONAL_FINITE_COMPONENT.** General-Lambda matched frame curvature is separate from Lambda=0, mu=kappa*epsilon0/6 Weyl specialization. Actual static covariant derivatives yield radial proper acceleration and zero expansion/shear/vorticity. General-Lambda acceleration and rate lemmas remain present in CAS06Foundation. The selected Weyl derivative includes all four connection terms and five frame factors; differentiation precedes event matching. Lean establishes the unspecialized local Weyl identity before differentiating it. No derivative of an identically-zero specialized expression. The derivative normalizes across axes to -kappa^2*epsilon0^2*(1+alpha)*(1+3*alpha)*r0/(18*alpha*sqrt(F0)), F0=1-kappa*epsilon0*r0^2/3 at Weyl specialization; strictly negative on the admitted domain. Weyl derivative length^-3; acceleration length/time^2 with x0=ct.
- **C03: COVERED_WITH_EXPLICIT_FINITE_JET_ORDER.** Literal inverse-determinant volume and kinetic variations derive stress and scalar-gradient current coefficients; the resulting static chart current has computed zero divergence. Fixed Pstar,q, X>0, positive real power, matched normalization/stress, radial conservation, and finite jets are covered. The scalar source is byte-identical to the admitted dependency and rebuilt, not declared as an axiom. Its exact positive-denominator/ratio theorem is an allowed dependency, including where another axis repeats only its algebra. No target stress/current formula is a premise. Formal order: Matched pressure/energy/stress values; first radial pressure and energy derivatives; conditional second lapse derivative from differentiated local action-source TOV. No all-variable formal second-jet or arbitrary-order result. The second-lapse theorem retains its displayed local action-source equation. Whole-interval identification with a separately supplied epsilon solution, existence and uniqueness remain HOLD.
- **C04: COVERED_CONDITIONAL_ALGEBRA_AND_REAL_LIMIT.** Fixed constants include Pstar,q. Actual metric acceleration is connected to r0=y/sqrt(C) and (c^2*abs(B)/sqrt(C))*y/sqrt(1-y^2). Positive finite values and one-sided +infinity limit are proved on 0<y<1,C>0,B!=0,c>0. Lean quantifies conditionally over family data meeting event/ODE premises; it does not assert existence or distinctness. No F0=0,alpha=0,r0=0 family member.

**Execution and proof evidence.**

- **wolfram_xact:** Wolfram 15.0.0; xTensor 1.3.0; xCoba 0.8.6. CTensor metric, SetCMetric and MetricCompute All; extracted connection and Einstein tensor compared with coordinate derivation; xAct connection used for rates and current divergence. Meaningful computation exceeds load-only/ToCanonical[0]. Raw stdout/stderr and exit inspected.
- **sympy:** SymPy 1.14.0; /usr/bin/python3.12. Exact symbolic component identities, variational coefficients, branches/signs and one-sided limit. No numerical-only universal proof. Source snapshot equals current sealed source.
- **sage_singular:** SageMath 10.9; /home/cosmosapjw/opt/sage/local/bin/Singular 4.4.1 / 44100. Independent differential rational jets, full symmetric inverse-metric variation, positive-real branch and limit, plus two actual localized Singular reductions. Complete current raw versions, executable, script, errors and completion inspected.
- **lean:** Lean 4.31.0; mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. Both receipts have nine zero-exit commands, including rebuilding all four owned modules from frozen sources and compiling the named entrypoint. Source/input maps, output module hashes, theorem axioms and toolchain agree. Raw logs contain no compiler errors or sorryAx; dependencies of the nine required named theorems are only propext, Classical.choice, Quot.sound.

The actual ADJUDICATION_STDOUT_REPAIRED.json has structured CAS_4AXIS_PASS, RUNNER_OBSERVED_EXECUTION, four PASS payloads and no errors. That status was inspected alongside sources and raw logs. The immutable registered Lean receipt at lean/attempts/20261004T220445384881Z/result.json and aggregate receipt at lean/attempts/20261004T221116644409Z/result.json bind the same source/input maps and compiled module hashes. Neither receipt nor mutable author result was changed.

**Direct reviewer validation.** Recompiled exact lean/C03Action.lean with output redirected to review/C03Action.olean. Exit 0, empty stderr, no compiler errors or sorryAx. The compiled hash 5b456c16536529fec700fea96d8b2c656e2e5c01e618bea50e3f1c627db186f5 matches the frozen source-bound output. Exact argv/environment, timestamps and logs are in C03_SOURCE_COMPILE_COMMAND.json, C03_SOURCE_COMPILE_RESULT.json and adjacent logs. Other axes were inspected, not rerun. EVIDENCE_CHECKS.json records source bindings, final complete axiom lists and the post-probe seal. Production sources and binaries remain unchanged.

**Runtime and independence.** Observed reviewer runtime is gpt-6-astra/xhigh, session 01a10900-210a-7ac3-b55e-6ce5c24a81b0, from the explicitly supplied routing/review-observed-runtime.json (SHA-256 2e5af65df0662ccf7a290ae3a56ec9c39741a137f94246f04ea139e8aa406017). Authors are parent-observed gpt-6-sol/high and share model-family correlation. No sibling-source reads appear in the inspected executables. Full author access history, lifecycle and accounting remain parent-owned. Native currency cost and Host-unit allocation remain NOT_MEASURED; historical UNKNOWN spend is not zero. No subagents, local models, memory retrieval or broad historical transcripts were used.

**Claim and lifecycle separation.** This is a finite conditional metric/action calculation and one-sided real limit. Local smooth existence, DEC persistence, normal-coordinate 2-jet theorem, interval uniqueness/equality, and distinct-germ interpretation remain HOLD. No hyperbolicity, UV/global stability, observational validation, native solver readiness or scientific admission follows. Review, four-axis execution, parent final validation, lifecycle acceptance, publication and installation are distinct. The reviewer performed no publication or installation action.

The parent owns final external validation and acceptance. No candidate repair is requested.

