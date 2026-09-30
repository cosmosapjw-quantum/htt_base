# C04 SageMath/Singular certificate scope

This is an independent source implementation prepared from the task instructions and the single pinned C04 contract. No sibling source, derivation, result, or root theorem document was read. The model identity is unknown; no cross-model independence or formal blind authorship claim is made.

**Execution status: unexecuted.** No SageMath or Singular installation or execution was performed during preparation. This document describes the intended checker and its mathematical trust boundary, not an observed backend PASS. Ordinary Python syntax inspection, if reported separately, is not Sage execution.

## Exact input and run requirements

The mandatory `--contract` argument must identify bytes with SHA-256:

```
0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63
```

The checker also checks the contract identity, version, field, quantifiers, formulas, axis obligations, and exact statement. The required runtime is a SageMath installation with its Python interpreter and functioning exact libSingular polynomial/Groebner backend. No network access is required at execution. This preparation does not claim compatibility with an actually tested Sage version.

Example, from the directory containing these files:

```sh
sage -python c04_sage_certificate.py --contract intake/contracts/CAS13-C04-RELATIVE-MINIMAX.json --self-test
```

The executor should independently capture the actual launcher argv, exit code, raw stdout and raw stderr, and source hash. The program's `actual_argv` records the Python process argv, not any invisible outer shell/Sage launcher arguments. Success writes one JSON object containing the exact target boolean, domain-assumption difference, counterexample field, source and contract hashes, statement alignment, coverage, every checked polynomial identity, and logical bridge details. A runtime, contract, or certificate failure exits nonzero with diagnostics on stderr and no fabricated target-result payload. `counterexample: null` on success means the checked universal certificate leaves none in its domain; the checker is not a counterexample search tool.

## Statement covered

For all real \(L,U\) with \(0<L\le U\), let

\[
a_* = \frac{2LU}{L+U},\qquad r_* = \frac{U-L}{L+U}.
\]

The certificate covers all three obligations:

1. Every real \(x\in[L,U]\) satisfies \(|a_*/x-1|\le r_*\).
2. Both endpoint losses equal \(r_*\).
3. Every real predictor \(a\), with no sign restriction, satisfies \(\max(|a/L-1|,|a/U-1|)\ge r_*\).

The closed branch \(L=U>0\) is included. The strict interval branch and all predictor branches \(a<0\), \(a=0\), and \(a>0\) follow from the same identities. No uniqueness statement is asserted.

## Exact certificate chain

The checker uses `PolynomialRing(QQ, ...)` with the definitional ideal

\[
d=L+U,\quad k=2LU,\quad e=U-L,\quad n=k-xd.
\]

It explicitly asks for `groebner_basis(algorithm="libsingular:std")`. Nonzero identity residuals are reduced against this basis, and must have zero normal form. Identities already identical by exact coefficient arithmetic are separately labeled as such; they are not presented as nontrivial Singular work. There is no reduction of an artificially constructed `p-p` offered as the theorem certificate.

The only domain sign atoms are \(L>0\), \(U-L\ge0\), \(x-L\ge0\), and \(U-x\ge0\). A restricted interpreter validates positive-coefficient sums and products of established sign facts. This establishes \(U>0\), \(x>0\), \(d>0\), \(xd>0\), and \(e\ge0\), before any positive-division step. No conclusion is inserted into the domain assumptions.

For the entire interval, the two polynomial certificates are

\[
xe-n=2U(x-L)\ge0,\qquad xe+n=2L(U-x)\ge0.
\]

Since \(xd>0\), these give

\[
-e/d\le n/(xd)\le e/d.
\]

The checker connects \(n/(xd)=a_*/x-1\) and \(e/d=r_*\) to the literal contract formulas by separate polynomial identities. The absolute-value rule then yields the bound at every interval point. Endpoint substitution is used only for the separate endpoint equalities:

\[
k-Ld=Le,\qquad k-Ud=-Ue.
\]

For arbitrary real \(a\), define \(t=\max(|a/L-1|,|a/U-1|)\). The maximum and absolute-value rules, with already established positive denominators, give

\[
g_L=Lt-a+L\ge0,\qquad g_U=Ut+a-U\ge0.
\]

The universal semialgebraic certificate is

\[
dt-e=g_L+g_U\ge0.
\]

This is a positive sum of the two endpoint signed-loss slacks, and cancels \(a\) identically. Dividing by \(d>0\) proves \(t\ge r_*\). The auxiliary inequalities for \(g_L,g_U\) are derived from the declared maximum; they are not extra restrictions on \(a\). More abstractly, the same polynomial certificate holds for any real \(t\) satisfying those two epigraph inequalities, which the declared maximum necessarily satisfies.

For additional branch visibility, the program checks the specialization \(U-L=0\), obtaining \(e=0\), \(d=2L>0\), and \(k=Ld\). No step divides by \(U-L\), \(a\), or a quantity that could vanish on the included branches.

## Soundness boundary

This is an exact algebraic certificate plus a small, inspectable ordered-real rule interpreter. It trusts Sage's rational polynomial arithmetic and libSingular, the interpreter and Python runtime, and elementary ordered-field, absolute-value, maximum, substitution, and positive-division rules. Those real-order and absolute-value rules are explicit semantic bridges; they are not proved by Singular. This is neither a general real quantifier-elimination result nor a formally kernel-checked Lean proof.

The resulting check concerns only this finite mathematical component. It does not construct an interval from observations, prove statistical coverage, establish the other CAS-13 components, make a scientific admission, or close the parent CAS-13 theorem.

## Negative controls

With `--self-test`, the original complete certificate must pass and these mutations must each fail:

- Replace the first interval certificate's multiplier 2 by 1.
- Reverse the sign of the interval lower-bound numerator.
- Reverse the upper endpoint's signed residual.
- Replace the competitor target \(dt-e\) by \(dt-2e\).
- Add an uncancelled arbitrary predictor term to the competitor target.
- Weaken \(L>0\) to mere nonnegativity.
- Remove the interior premise \(x-L\ge0\).
- Change the contract bytes, even only by adding a newline.

Only explicit certificate rejections count as successful negative controls. A backend/runtime exception is a failed execution, not evidence that a mutation was correctly rejected. Self-tests check whether important mutations are detected; they do not independently formalize the trusted real-order rules.
