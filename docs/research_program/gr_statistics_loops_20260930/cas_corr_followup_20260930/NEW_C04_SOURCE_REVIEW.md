# C04 prepared certificate sources: bounded source review

Review scope: the two new certificate source files, their scope documents, and their relationship to the already-read pinned C04 version-3 contract. No package installation, mathematical engine execution, additional reviewer dispatch, or source mutation was performed. This is not the registered local independent-review admission.

Contract SHA-256: `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`.

Final inspected source snapshot hashes (including the targeted exception-path repair):

| File | SHA-256 |
|---|---|
| c04_sympy_certificate.py | 603f71eadc7451685d4e3ef27a13d2842f689626582a1db39a846c072b7efa2f |
| c04_sage_certificate.py | 13794a11756a48e32d013233cfb41959ef5c3b0b14c132be52b9256e877002bf |
| SYMPY_CERTIFICATE_SCOPE.md | 0f3540b44ff8f3c3effb857c98174ee132bf3bece1ffdd443f5de73c274437ec |
| SAGE_CERTIFICATE_SCOPE.md | 015eb425d07e15059273599df2561a9884a0996f42aff10c539f8bd33df1ef48 |

## Targeted correction and final decision

The first read exposed the already-known SymPy CLI classification defect: a broad exception handler could emit `checks[CAS13-C04-RELATIVE-MINIMAX]=false` for an execution error. The integrating host repaired that path. A bounded read of the changed tail confirms that `CertificateError` now produces stderr diagnostics and exit 1, while an unexpected backend exception produces stderr diagnostics and exit 3. Neither emits a target-result payload. The scope document now matches this behavior and honestly identifies the integrating host's source exposure. The hash table records this final inspected source, not the earlier failure-path text.

No remaining concrete source-level blocker was found in the requested scope. This is source-review acceptance for preparation, not a backend execution PASS.

## Exact target and logical coverage

Both sources authenticate the exact contract bytes before importing their mathematical backend. The pinned hash binds the full original target even though the SymPy parser also rechecks only selected fields. Both retain the positive closed interval, permit L=U, and impose no sign restriction on the competing real predictor.

The uniform interval proof checks both signed inequalities with positive denominators and explicit nonnegative factor certificates. The endpoint proof checks the signed equalities and uses the nonnegative radius to obtain the absolute equalities. These are the three literal component targets; neither source claims other CAS13 components or interval coverage from data.

Both implementations use the same sound endpoint-maximum lower-bound strategy: define t=max(abs(a/L-1),abs(a/U-1)); infer Lt-a+L>=0 and Ut+a-U>=0; add to obtain (L+U)t-(U-L)>=0; divide by L+U>0. This entails the endpoint lower bound for every real a without a predictor case split. It includes negative and zero a. No step divides by U-L or a.

The elementary absolute-value, maximum and ordered-field implications are implemented as explicitly disclosed trusted rules. SymPy checks exact rational-polynomial identities; Sage uses QQ polynomials and a definitional ideal with requested libSingular reduction. These are reviewable certificate interpreters, not proof-assistant kernels or general real quantifier elimination. The scope documents state that distinction correctly.

## Sage interval-premise isolation

The Sage implementation holds interval and endpoint facts in one dictionary, but the inspected competitor derivation uses only these dependencies:

`L>0, U-L>=0 -> e>=0, U>0, d>0 -> endpoint_L_slack, endpoint_U_slack -> competitor_gap`.

The two endpoint slacks come from the defined maximum and positive L/U. Their sum is reduced only modulo the four definitional equalities; those equalities do not restrict x. Neither x-L nor U-x enters this dependency chain, and the resulting polynomial has no x. Endpoint equalities likewise use only L,U,d,e. There is therefore no actual leakage of an interior-point premise into the all-real-a endpoint lower bound in this fixed source. A proof-assistant-style dependency tracker is not needed to accept this particular inspected chain.

## Runtime and preparation status

The Sage CLI prepares its complete payload before writing stdout, and its outer exception handler emits only stderr with nonzero exit. Its mutation controls count only explicit `CertificateFailure` exceptions as expected rejections; backend exceptions escape to execution failure.

Both scope documents describe the mathematical checks as unexecuted and do not claim an observed backend PASS. This review did not execute either mathematical backend, so actual SymPy compatibility, Sage/libSingular API behavior, successful identities, mutation-control outcomes, and any runner aggregate remain local execution obligations.

The targeted SymPy exception/output repair is source-confirmed; preparation may proceed to one local component execution. This review neither changes the historical CAS_CONFLICT nor fills the missing registered reviewer admission.
