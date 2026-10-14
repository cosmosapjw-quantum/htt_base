**R1 — P2, blocking this finite review closeout: Flat-branch checks omit the literal target or use unbound constant-zero checks.**

Locations: sympy/run.py:65,76; sage_singular/sage_component.py:37,40.

SymPy computes 0*integrate(s-t,(t,0,s)); it omits f0(t)=t and -(flat_f-s). Sage checks is_zero(SR(0)) for the flat initial value and is_zero(SR(0)-(s-s)) for the flat integral without constructing the target integral. These are emitted as flat-branch coverage despite the frozen no-constant-true-check rule.

The source-bound SymPy/Sage PASS fields do not establish the requested literal flat-branch checks. Multiplication by zero masks the wrong SymPy integrand. The target theorem is not refuted; the exactly aligned Lean theorem independently compiles.

Exact reproduction: review/flat_branch_coverage_probe.py, pinned SymPy 1.14.0: encoded unscaled integral=s**2/2, specified unscaled integral=s**3/6; at s=1 these are 1/2 and 1/6. Both zero-weighted residuals are zero. This falsifies coverage, not the C01 theorem.

Minimal repair: In both affected sources bind f0(s)=s, form the actual interval integral (s-t)*f0(t), compare 0*integral against f0(s)-s, and derive the initial value by substitution into f0. Preserve this evidence and replace only the affected checks. Parent runs unchanged frozen external validators and decides the source-bound repair closeout.

**Verdict: HOLD for the submitted four-axis finite component review. Scientific admission: HOLD.** No mathematical counterexample was found. The exact Lean theorem independently proves the specified scalar statement. This review does not erase the preserved runner-observed C01 adjudication or promote the historical full-CAS07 conflict. The parent owns the final decision and any one targeted repair closeout.

The review used the specified checkout at f1007dd3e41c07eccd64024dd6b44fb5a40a3612. All 201 sealed paths match before and after probes. Contract SHA256: e5342381440cb6456ad27add75a9d23faa52a01b1a0f5998599e3026452a9f1a. Admitted-input SHA256: 30bbb6fce513eedfd98a693c2acbf3308363a7098a7938f4b5abf7e9282b2e39. Manifest SHA256: e5a8dfa5ee47f12704a4d3ea22ef721d2370977c57af5c865775a01b384da63c.

The original C01 statement is byte-identical. Neutral input restoration defines f, the actual interval and the fixed-s positive-side limit without assuming the result. CAS01 supplies accepted finite conventions only. Units agree: Kc is inverse-length-squared; the kernel integral has length cubed; Kc times that integral has the same length units as f-s. Derivative units also agree.

| Axis | Target coverage and execution evidence |
| --- | --- |
| wolfram_xact | Wolfram 15.0.0; xTensor 1.3.0. Full positive-branch initial/ODE/actual interval integral, separate flat branch and fixed-s right limit. Nonzero gradient contraction transforms g[a,b] CD[-a]F CD[-b]F to CD[-a]F CD[a]F with exact zero contracted difference. It meets the ancillary scalar index-consistency obligation; it does not establish Jacobi comparison. Final exit 0, no Wolfram messages and empty stderr. Four earlier unsuccessful parser/xTensor attempts remain retained. |
| sympy | 1.14.0. Exact symbolic positive-branch initial/ODE/interval-integral/right-limit checks align. Flat derivatives are correctly calculated from flat_f=s; R1 affects the flat integral. No numerical samples substitute for exact universal identities. Author attempt exit 0 and empty stderr. Observed adjudication reruns the same source. |
| sage_singular | SageMath 10.9; Singular 4.4.1 / 44100. Sage derives the full symbolic positive-branch calculus, actual integral and limit. Strict s>0 backend assumption is combined with explicit s=0 initial/integral evaluations; the zero endpoint limit follows f(K,0)=0. R1 affects flat checks. Singular uses a universal indeterminate, not finitely sampled coefficients, to verify polynomial consequences of the declared recurrence. It does not independently prove the Taylor expansion or analytic function; Sage supplies full-function calculus. All six complete Singular stdout files identical: version 44100 and zero ODE/integral residuals, no diagnostics, stderr empty. Sage attempts 001/002 fail domain/backend sign decisions; 003 fails the unnormalized integral residual; 004-006 succeed. |
| lean | Lean 4.31.0; mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. Explicit hyper=sinh(sqrt(k)*s)/sqrt(k), hk>0 and hs>=0. Genuine HasDerivAt sublemmas establish derivatives. Actual intervalIntegral follows by FTC with continuous/integrable kernel. Separate flat initial/ODE/integral theorems have no positive-k premise. Right nhdsWithin zero limit splits s=0 and s>0. No target initial/ODE/integral/limit premise is assumed. Development 01-05 exit 1 with elaboration/tactic failures and compiler-generated sorryAx in failed declarations; 06 exit 0. Final source and fresh review compile exit 0 with linter warnings only, no sorryAx. |

Full current sources/runners, actual argv/exits, raw outputs and before/after source-input bindings were inspected. All latest axis source/input/log bindings match (evidence_binding_audit.json). The actual bundled Singular executable is /home/cosmosapjw/opt/sage/local/bin/Singular with SHA256 9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c; its complete outputs were checked, not merely exit code or PASS markers.

Lean source SHA256: 282d48caf23e01b2cdc81efa81d5bf9818df82b29a107962548660500c82dedd. The immutable review_candidate/lean-result-observed.json binds the latest actual compile snapshot with those exact bytes and matching raw log hashes. complete_target lines 157-167 and its derivative/integral/right-limit/flat sublemmas cover the exact target. The fresh copy in review/ compiles under Lean 4.31.0 and mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. All 14 printed axiom lists contain only propext, Classical.choice and Quot.sound. No stale olean or status string is used as proof. Lean totalizes hyper at k=0, but that expression is not the flat branch: separate flat(s)=s is used.

Retained raw failures are not current proof evidence. Lean 01-05 contain genuine compiler errors and generated sorryAx, while 06 and final compile do not. Wolfram first used a commutator that evaluated to literal zero; the next three attempts fail index checks. The final nonzero gradient contraction resolves that earlier problem. Sage 001 rejects a nonnegative variable-domain string; 002 records Maxima requesting a strict sign; 003 leaves a nonzero-looking exponential-versus-sinh residual. Later exact exponential normalization resolves that residual.

C02/C03, Jacobi existence/majorization, Volterra comparison, determinant continuation and distance/redshift inference remain unproved by this component. Historical full CAS07 remains CAS_CONFLICT. Review, four-axis adjudication, publication, lifecycle acceptance, installation and scientific admission are distinct.

Author receipt observations show all four authors as gpt-6-sol/high. Host setup gpt-6.1-sol/high is parent-reported. Reviewer request is gpt-6-astra/xhigh; actual reviewer model/effort remain UNKNOWN because no observer receipt was supplied at report time. The structured report preserves each author receipt identity and cumulative usage instead of resetting accounting.

Known limits:

- Earlier Lean attempts 01-06 retain exact sources/logs/argv but per-attempt versions and pre/post pin measurements were not independently captured; those remain NOT_MEASURED.
- The author final Lean directory has no final envelope snapshot. The sealed review_candidate copy binds the latest observed compile and exact final source. This establishes current source-bound evidence, not historical packaging completeness.
- Some early Sage source revisions and Wolfram runner revisions have hashes/logs rather than full source snapshots in this seal; latest accepted sources and bindings are present.
- No forensic audit of author-session transcripts; observed author runtimes are inspected frozen receipts. Four engine ecosystems do not remove shared gpt-6-sol/high author-family correlation.
- Direct execution here is the byte-identical Lean compile and the SymPy coverage probe. Other engine runs are inspected frozen receipts, not reviewer reruns.
- Native currency cost and Host unit allocation remain NOT_MEASURED; prior campaign accounting remains UNKNOWN_NOT_ZERO.

Direct-review execution receipts are lean_direct_compile_receipt.json and flat_branch_coverage_probe.receipt.json, with full stdout/stderr and exact argv/exits. The before/after manifest reports show all 201 entries unchanged. All writes are within P/review/**. Author sources/results/pins and unrelated dirty files were preserved; no subagents, local models, memory retrieval or other-campaign executions were used.
