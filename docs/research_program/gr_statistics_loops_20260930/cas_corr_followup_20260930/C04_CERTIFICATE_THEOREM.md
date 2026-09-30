# CAS-13-C04: universal algebraic certificates for positive-interval relative minimax

Status: **derived universal proof; proposed certificate design, not an executed CAS result**.

This note supplies a complete elementary proof for the atomic component
`CAS13-C04-RELATIVE-MINIMAX` reported in
`GRSTAT-CAS-CORR-20260930-1420KST`. It does not close the parent CAS-13 contract,
change the recorded four-axis conflict, prove observational interval coverage,
or establish novelty. The corrected return identifies the component contract by
SHA-256 `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`.
The derivation below is source-informed continuation, not blind independent
authorship of the existing Lean proof.

## 1. Statement and conventions

All variables are real. Assume

\[
 0<L\le U,\qquad x\in[L,U],\qquad a\in\mathbb R.
\]

Set

\[
 s=L+U>0,\quad d=U-L\ge0,\quad
 t_*={2LU\over s},\quad e_*={d\over s},\quad
 \rho_*(x)={t_*-x\over x}.
\]

The three required targets are:

1. For every admissible \(x\), \(|\rho_*(x)|\le e_*\).
2. \(\rho_*(L)=e_*\) and \(\rho_*(U)=-e_*\), hence both endpoint
   absolute errors are exactly \(e_*\).
3. For every real predictor \(a\),

   \[
   e_*\le \max\left(\left|{a-L\over L}\right|,
                         \left|{a-U\over U}\right|\right).
   \]

In particular, for the loss \(E(a)=\sup_{x\in[L,U]}|(a-x)/x|\), these
targets prove \(\min_{a\in\mathbb R}E(a)=e_*\), attained by \(a=t_*\).
No positivity assumption on the competing predictor is used.

If \(L,U,x,a\) carry a common physical unit, \(t_*\) carries that unit and
\(e_*\) and \(\rho_*\) are dimensionless. This theorem by itself does not
interpret that unit, frame, or interval as an observationally guaranteed one.

## 2. Full-interval upper bound by two certificates

Write \(n=2LU-sx\); then \(\rho_*(x)=n/(sx)\). The complete
inequality proof consists of the exact polynomial identities

\[
 \boxed{dx-n=2U(x-L)},\qquad
 \boxed{dx+n=2L(U-x)}.
\]

The left identities hold in the unrestricted polynomial ring
\(\mathbb Q[L,U,x]\). The right sides are nonnegative on the declared
domain, because \(L>0\), \(U\ge L>0\), \(x-L\ge0\), and \(U-x\ge0\).
Moreover \(sx>0\). Dividing both identities by this *proved-positive*
denominator gives

\[
 e_*-\rho_*(x)={2U(x-L)\over sx}\ge0,\qquad
 e_*+\rho_*(x)={2L(U-x)\over sx}\ge0.
\]

Thus \(-e_*\le\rho_*(x)\le e_*\), which is equivalent to the required
absolute-value bound. The argument quantifies over the entire interval; it is
not an endpoint sample or a monotonicity conjecture.

For a coefficient-only nonnegativity representation, introduce the interval
gaps \(p=x-L\ge0\), \(q=U-x\ge0\). Then

\[
 x=L+p,\quad U=L+p+q,\quad
 sx=(2L+p+q)(L+p)>0,
\]

and the two certificate numerators are
\(2(L+p+q)p\) and \(2Lq\). This parameterization is onto the entire
admissible \((L,U,x)\) domain. It may be used as a separate implementation,
but the direct polynomial identities are simpler.

## 3. Endpoint equality and the degenerate interval

Substitution in the same identities, with no limiting operation, gives

\[
 \rho_*(L)={2LU-sL\over sL}={d\over s}=e_*,\qquad
 \rho_*(U)={2LU-sU\over sU}=-{d\over s}=-e_*.
\]

Since \(e_*\ge0\), their absolute values equal \(e_*\). At \(U=L\),
\(s=2L>0\), \(t_*=L\), and \(e_*=0\); the only admissible point is
\(x=L\). All denominators remain nonzero. The proof never divides by
\(U-L\), so no separate exclusion of the equality case is allowed.

## 4. Every real competitor: a nonnegative linear combination

For an arbitrary \(a\in\mathbb R\), define

\[
 r=\max\left(\left|{a-L\over L}\right|,
                   \left|{a-U\over U}\right|\right)\ge0.
\]

The definition of the maximum and the elementary absolute-value inequalities
imply

\[
 r\ge{a-L\over L},\qquad r\ge-{a-U\over U}.
\]

Multiplying by the positive endpoints gives two nonnegative slacks

\[
 f_L=Lr-a+L\ge0,\qquad f_U=Ur+a-U\ge0.
\]

Their sum is the exact polynomial certificate

\[
 \boxed{sr-d=f_L+f_U\ge0}.
\]

Dividing by \(s>0\) proves \(r\ge e_*\). Equivalently, before clearing
the endpoint denominators the certificate uses the nonnegative multipliers
\(L,U\):

\[
 L\left(r-{a-L\over L}\right)
 +U\left(r+{a-U\over U}\right)=sr-d.
\]

The coefficient of \(a\) cancels identically. Consequently this proof
includes all negative competitors, arbitrarily large competitors, and the
case \(U=L\), with no case split or numerical sampling. It does not
assume the desired minimax lower bound as an input inequality.

## 5. From the three targets to the minimax statement

For every \(a\), the loss function is continuous on the nonempty compact
interval \([L,U]\), because \(L>0\). Therefore \(E(a)\) is a finite
maximum. In particular it is at least its two endpoint values, so section 4
implies \(E(a)\ge e_*\). Sections 2 and 3 imply \(E(t_*)=e_*\).
This proves the minimax statement. Computing the entire function \(E(a)\)
for every competitor is unnecessary.

If only the three algebraic targets, rather than a supremum operator, occur
in the sealed component contract, the compactness step is an explanatory
corollary and is not to be mislabeled as a CAS-computed analytic result.

## 6. Sound universal certificate checker design

The symbolic engines can verify a universal inequality theorem by checking
its certificates and their logical interpretation. They need not discover
the proof through a general-purpose inequality solver. The implementation
must make the proof interpretation explicit instead of checking only a few
identities and labeling the entire theorem as complete.

### Fixed input and target binding

- Bind to the sealed component ID and SHA-256 above; compare every target
  and assumption with the local contract before execution.
- Use algebraically independent real indeterminates \(L,U,x,a,r\),
  exact rational coefficients, and the named positivity constraints.
- Define \(s,d,n,t_*,e_*\) from the formulas in section 1. Do not accept
  alternate user-supplied formulas or extra assumptions silently.
- Quantification is universal. Symbols must not be replaced by a grid,
  one-dimensional special family, or positive-only competing \(a\).

### Exact identity verification

Verify that each of the following is the zero polynomial in the indicated
exact rational polynomial ring:

1. \(dx-n-2U(x-L)\).
2. \(dx+n-2L(U-x)\).
3. \(2LU-sL-dL\).
4. \(2LU-sU+dU\).
5. \(sr-d-(Lr-a+L)-(Ur+a-U)\).

Substitution \(U=L\) must additionally yield the exact formulas
\(t_*=L\) and \(e_*=0\), with the nonzero denominator \(2L\).
SymPy can check polynomial coefficients in `Poly(..., domain=QQ)`;
Sage can use its rational polynomial ring. Neither proof requires an
approximate root finder, floating-point cancellation, or solver timeout.

### Positivity and logical bridges

The checker must explicitly validate the following proof dependencies:

1. From \(0<L\le U\) and \(L\le x\le U\), infer
   \(U>0,x>0,s>0,sx>0,d\ge0\).
2. Each upper-bound numerator is a product of a nonnegative rational
   constant and already established nonnegative factors. No unsupported
   sign query may be treated as `True`.
3. Two signed inequalities with a nonnegative bound imply an
   absolute-value bound. A fixed, documented real-order inference rule is
   used here, not a new assumption about \(\rho_*\).
4. For fresh \(r\), prove the implication
   \(r\ge|(a-L)/L|\) and \(r\ge|(a-U)/U|\) implies \(sr\ge d\)
   by the slack certificate. Then instantiate
   \(r=\max(|(a-L)/L|,|(a-U)/U|)\). Those endpoint inequalities follow
   from the maximum definition; they are not assumptions added to the
   final theorem's \(L,U,a\) domain.
5. Endpoint absolute equality follows from the signed endpoint identities
   and \(d/s\ge0\).

A small typed certificate interpreter may use only these audited rules:
positive/nonnegative constants, explicitly declared premises, preservation
under addition and multiplication, division by a proved-positive quantity,
polynomial equality substitution, absolute-value sandwich, and maximum
introduction. Unsupported rule names, missing premises, circular proof
dependencies, or additional domains must reject the certificate.

### What would and would not count as full scope

**Sufficient mathematical coverage:** exact polynomial identity checking
plus the complete, explicitly checked sign and order derivation above,
bound to the sealed target. This proves the universal theorem over the
reals; it is not a numerical approximation. The checker must cover all
obligation keys in the actual component contract.

**Insufficient:** checking endpoint equality alone; declaring symbols
positive and hoping simplification establishes the quantifiers; using
`Abs` examples; assuming \(a\ge0\); excluding \(L=U\); or supplying the
minimax inequality itself as a premise. Those outputs remain partial or
misaligned.

**Trust boundary:** polynomial arithmetic establishes exact algebraic
identities. The order-certificate interpreter and its mapping from the
stated theorem to those identities are additional logical code. A CAS
booleans report is not an independent proof of that interpreter's
soundness. Keep its rule set small, inspect it directly, and retain the
existing Lean theorem as the formal proof of the same mathematical
statement. Do not claim that sharing this certificate plan across SymPy
and Sage creates independent proof discovery or authorship.

**Execution boundary:** this document alone supplies no observed engine
verdict. After implementing the two missing axes, run the existing
contract-bound local runner and preserve its actual aggregate. Old raw
`CAS_CONFLICT` remains historical evidence even if a new atomic execution
closes. Mathematical theorem acceptance, formal Lean verification,
four-engine execution agreement, and observational applicability are
different statements.

## 7. Minimal next local work

Implement only the two missing C04 axes using the certificate plan and the
exact existing component contract. Include diagnostic rejection controls
for a sign-flipped certificate, an omitted denominator-positivity premise,
an undeclared restriction \(a\ge0\), and any attempted division by
\(U-L\). The controls test the checker; they are not substitutes for the
universal proof. Reuse neither a hard-coded `PASS` nor old stdout as fresh
execution. No rerun of unrelated CAS-13 components is needed to test this
atomic repair.
