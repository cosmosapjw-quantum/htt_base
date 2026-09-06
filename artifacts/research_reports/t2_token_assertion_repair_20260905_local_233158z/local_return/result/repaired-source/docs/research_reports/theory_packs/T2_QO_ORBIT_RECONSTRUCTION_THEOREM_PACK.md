# T2 — Generic Q/O proper-rotation orbit reconstruction on the cyclic domain

Date: 2026-09-03  
Evidence grade: `DERIVED`, independently exact-Wolfram-checked  
Implementation status: PR #440 source present; exact-head runtime unobserved  
Observational data used: none  
Novelty status: unresolved

## 1. Scope and representation

Let

\[
Q\in\operatorname{STF}_2(\mathbb R^3),\qquad
O\in\operatorname{STF}_3(\mathbb R^3)
\]

be the temperature quadrupole and octupole tensors. The proper-rotation action
is

\[
Q\mapsto RQR^T,
\qquad
O_{abc}\mapsto R_a{}^dR_b{}^eR_c{}^fO_{def},
\qquad R\in SO(3).
\]

This theorem concerns only the nonzero cyclic domain defined below. It is not a
claim about:

- the joint vector/tensor `STF2 + four vectors` representation of VT-T8;
- all singular orbit strata;
- a polynomial integrity basis or the full invariant ring;
- a minimal algebraically independent coordinate set;
- observational or physical-source identification.

The ambient dimension is

\[
\dim\operatorname{STF}_2+
\dim\operatorname{STF}_3=5+7=12.
\]

On the cyclic domain the stabilizer is trivial, so the quotient dimension is

\[
\boxed{12-3=9}.
\]

Equivalently, two positive amplitudes plus a seven-dimensional normalized
shape quotient are required.

## 2. Normalized tensors and Krylov frame

For nonzero tensors define

\[
A_Q=\|Q\|_F,\qquad A_O=\|O\|_F,
\]

\[
\bar Q=Q/A_Q,\qquad \bar O=O/A_O.
\]

Thus

\[
\bar Q:\bar Q=1,\qquad \bar O:\bar O=1.
\]

Contract the octupole with the quadrupole:

\[
v_a=\bar O_{abc}\bar Q_{bc}.
\]

Define the ordered Krylov matrix

\[
\boxed{
\mathscr K_{QO}
 =\bigl[v,\bar Qv,\bar Q^2v\bigr].
}
\]

The algebraic cyclic domain is

\[
\mathcal D_{\rm cyc}
 =\{(Q,O): A_QA_O\det\mathscr K_{QO}\neq0\}.
\]

The production implementation further restricts to the numerical subdomain

\[
\kappa_2(\mathscr K_{QO})\le\kappa_{\max},
\]

with a frozen condition limit. Algebraic singularity and numerical refusal are
therefore distinct states.

## 3. Cyclicity criterion

Let the eigenvalues of \(\bar Q\) be \(\lambda_1,\lambda_2,\lambda_3\), and
let \(v_i\) be the components of \(v\) in the corresponding orthonormal
eigenframe. Then

\[
\mathscr K_{QO}
 =\operatorname{diag}(v_1,v_2,v_3)
 \begin{pmatrix}
 1&\lambda_1&\lambda_1^2\\
 1&\lambda_2&\lambda_2^2\\
 1&\lambda_3&\lambda_3^2
 \end{pmatrix}.
\]

Hence

\[
\boxed{
\det\mathscr K_{QO}
 =v_1v_2v_3
  \prod_{i<j}(\lambda_j-\lambda_i).
}
\]

Therefore

\[
\det\mathscr K_{QO}\neq0
\iff
\begin{cases}
\bar Q\text{ has simple spectrum},\\
v_i\neq0\text{ for all three eigen-directions}.
\end{cases}
\]

Repeated-spectrum and noncyclic contraction strata are not repaired by
inventing an axis.

A useful consequence is freeness of the proper-rotation action on
\(\mathcal D_{\rm cyc}\). If \(R\in SO(3)\) fixes \(Q\) and \(O\), it fixes
\(v\) and therefore every column of \(\mathscr K_{QO}\). Invertibility gives
\(R=I\).

## 4. The invariant packet

Write

\[
s_2=\operatorname{tr}(\bar Q^2)=1,
\qquad
s_3=\operatorname{tr}(\bar Q^3),
\]

and the Krylov moments

\[
\mu_r=v^T\bar Q^rv,\qquad r=0,1,2.
\]

Let

\[
\chi=\det\mathscr K_{QO}.
\]

For \(0\le i\le j\le k\le2\), define ten symmetric trilinear contractions

\[
\tau_{ijk}
 =\bar O\bigl(\bar Q^iv,\bar Q^jv,\bar Q^kv\bigr).
\]

The PR #440 packet consists of the two amplitudes and

\[
\boxed{
\mathcal I(Q,O)
 =\left(
 s_2,s_3,\mu_0,\mu_1,\mu_2,\chi,
 \{\tau_{ijk}\}_{0\le i\le j\le k\le2}
 \right).
}
\]

There are sixteen stored shape entries, but \(s_2=1\) and additional algebraic
relations hold. This is an overcomplete separating packet on its image, not a
claim of sixteen independent coordinates.

All shape entries are dimensionless. \(A_Q\) and \(A_O\) carry the original
temperature unit.

## 5. Proper-rotation invariance and parity

For \(R\in SO(3)\),

\[
v\mapsto Rv,\qquad
\mathscr K_{QO}\mapsto R\mathscr K_{QO}.
\]

Consequently \(s_2,s_3,\mu_r,\chi\), and every \(\tau_{ijk}\) are invariant.

For a general orthogonal transformation,

\[
\chi\mapsto\det(R)\chi.
\]

Thus \(\chi\) is an \(SO(3)\) scalar and an \(O(3)\) pseudoscalar. The packet
retains proper-orientation information rather than collapsing mirror pairs.

Under the full inversion \(O\mapsto-O\), \(Q\mapsto Q\), one has

\[
v\mapsto-v,\qquad
\mathscr K_{QO}\mapsto-\mathscr K_{QO},
\qquad
\chi\mapsto-\chi.
\]

The moments and trilinear contractions remain unchanged because the four sign
changes in \(\bar O(\mathscr K_i,\mathscr K_j,\mathscr K_k)\) cancel.

## 6. Cayley--Hamilton closure and the Gram matrix

For every trace-free \(3\times3\) matrix,

\[
\boxed{
\bar Q^3
 =\frac{s_2}{2}\bar Q+\frac{s_3}{3}I.
}
\]

Therefore

\[
\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0,
\]

\[
\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1.
\]

The first five moments determine the Krylov Gram matrix

\[
\boxed{
G=\mathscr K_{QO}^T\mathscr K_{QO}
 =\begin{pmatrix}
 \mu_0&\mu_1&\mu_2\\
 \mu_1&\mu_2&\mu_3\\
 \mu_2&\mu_3&\mu_4
 \end{pmatrix}.
}
\]

On \(\mathcal D_{\rm cyc}\), \(G\) is positive definite and

\[
\boxed{\det G=\chi^2}.
\]

## 7. Canonical proper-oriented Krylov frame

Choose the unique upper Cholesky factor \(B_+\) with positive diagonal such
that

\[
B_+^TB_+=G.
\]

If \(\chi>0\), set \(B=B_+\). If \(\chi<0\), set

\[
B=SB_+,\qquad S=\operatorname{diag}(1,1,-1).
\]

Then

\[
\boxed{B^TB=G,\qquad\det B=\chi.}
\]

This is the deterministic proper-oriented representative used by the
implementation. The orientation convention is appropriate for an \(SO(3)\),
not an \(O(3)\), quotient.

## 8. Reconstruction of the quadrupole

In the Krylov basis, multiplication by \(\bar Q\) is represented by

\[
C=
\begin{pmatrix}
0&0&s_3/3\\
1&0&s_2/2\\
0&1&0
\end{pmatrix},
\]

because

\[
\bar Q\,[v,\bar Qv,\bar Q^2v]
 =[v,\bar Qv,\bar Q^2v]C.
\]

Define

\[
\boxed{\bar Q_{\rm can}=BCB^{-1}.}
\]

The moment recurrences imply

\[
C^TG=GC.
\]

Together with \(B^TB=G\), this proves that \(\bar Q_{\rm can}\) is symmetric.
Also

\[
\operatorname{tr}C=0,\qquad
\operatorname{tr}C^2=s_2,\qquad
\operatorname{tr}C^3=s_3,
\]

so the reconstructed quadrupole is trace-free and has the required unit norm.

## 9. Reconstruction of the octupole

Extend the ten values \(\tau_{ijk}\) to a fully symmetric coordinate tensor
\(T_{ijk}\). Define

\[
\boxed{
(\bar O_{\rm can})_{abc}
 =(B^{-1})_{ia}(B^{-1})_{jb}(B^{-1})_{kc}T_{ijk}.
}
\]

For a valid packet in the image of \(\mathcal I\), this reconstructs the
unique symmetric rank-three tensor whose components in the canonical Krylov
frame are \(T_{ijk}\). Trace-free and unit-norm closure are necessary image
conditions and are checked rather than silently projected by the implementation.

This theorem does not claim that the currently stored scalar consistency checks
provide a complete intrinsic algebraic characterization of every arbitrary
16-vector lying in the packet image.

## 10. Orbit reconstruction theorem

### Theorem T2.1

On \(\mathcal D_{\rm cyc}\), two pairs \((Q,O)\) and \((Q',O')\) have the
same amplitudes and invariant packet if and only if they lie in the same
\(SO(3)\) orbit.

### Proof

The forward direction is the invariance established in Section 5.

For the converse, let \(\mathscr K\) be the original Krylov matrix and \(B\)
the canonical frame reconstructed from its packet. They have the same Gram
matrix and signed determinant. Set

\[
R=B\mathscr K^{-1}.
\]

Then

\[
R^TR
 =\mathscr K^{-T}B^TB\mathscr K^{-1}
 =\mathscr K^{-T}\mathscr K^T\mathscr K\mathscr K^{-1}
 =I,
\]

and

\[
\det R=\frac{\det B}{\det\mathscr K}=1.
\]

Thus \(R\in SO(3)\) and \(B=R\mathscr K\). Since
\(\bar Q\mathscr K=\mathscr KC\),

\[
\bar Q_{\rm can}
 =BCB^{-1}
 =R\bar QR^T.
\]

The trilinear components satisfy

\[
T_{ijk}
 =\bar O(\mathscr K_i,\mathscr K_j,\mathscr K_k),
\]

so the inverse-basis formula gives

\[
\bar O_{\rm can}=R^{\otimes3}\bar O.
\]

Restoring the equal positive amplitudes proves orbit equivalence. If two pairs
have the same packet, both reconstruct the same canonical representative and
are therefore related by a proper rotation. ∎

The theorem gives a global separating reconstruction on the declared cyclic
domain. It does not extend across the singular strata or prove polynomial
invariant-ring completeness.

## 11. Mirror counterexample to the ordinary four-statistic compression

The repository's ordinary compression is

\[
\left(
 Q:Q,\ O:O,\ \operatorname{tr}Q^3,\
 Q_{ij}O_{ikl}O_{jkl}
\right).
\]

It is unchanged under \(O\mapsto-O\). For every cyclic pair with
\(\chi\neq0\), the two states \((Q,O)\) and \((Q,-O)\) have opposite
\(\chi\), so they are in distinct \(SO(3)\) orbits even though the four
ordinary statistics agree.

This proves non-separation of that named compression. It is not a claim about
every possible bispectrum or every higher-order invariant catalogue.

## 12. Typed strata and refusal policy

| Stratum | Mathematical state | Report/implementation action |
|---|---|---|
| `Q=0` | no quadrupole amplitude or normalized shape | retain tensors; chart unavailable |
| `O=0` | no octupole amplitude or normalized shape | retain tensors; chart unavailable |
| `O:Q=0` | contraction-null; Krylov matrix zero | retain tensors; chart unavailable |
| repeated spectrum of `Q` | Vandermonde factor vanishes | retain tensors; chart unavailable |
| simple spectrum but some `v_i=0` | noncyclic vector | retain tensors; chart unavailable |
| `det K != 0` but condition limit exceeded | algebraically cyclic, numerically weak chart | typed numerical refusal; do not fabricate axes |
| cyclic conditioned domain | reconstruction theorem applies | packet plus amplitudes may be used |

Chart failure is not missing physics, a zero observation, or permission to drop
only simulation rows. The finite-null analysis must preserve row symmetry by
falling back to a statistic defined on the full tensors or by issuing a
pool-level abstention.

## 13. Exact Wolfram validation

Fresh exact calculations returned:

```yaml
companion_G_self_adjoint_residual: ZERO_3_BY_3
companion_trace_checks:
  trace_C: 0
  trace_C2_minus_s2: 0
  trace_C3_minus_s3: 0
eigenframe_K_determinant:
  -v1*v2*v3*(lambda1-lambda2)*(lambda1-lambda3)*(lambda2-lambda3)
symmetric_triple_count: 10
exact_witness:
  Q: diag(1,2,-3)
  trace_O: [0,0,0]
  v: [24,38,47]
  det_K: 857280
  det_Gram_minus_det_K_squared: 0
  Q_reconstruction_residual: ZERO_3_BY_3
  O_reconstruction_residual_max: 0
ordinary_mirror_residual: [0,0,0,0]
mirror_kappa_sum: 0
proper_rotation_K_residual: ZERO_3_BY_3
proper_rotation_kappa_residual: 0
reflection_kappa_residual: 0
dimensions:
  ambient: 12
  normalized_shape_ambient: 10
  generic_quotient: 9
  normalized_shape_quotient_plus_amplitudes: 9
```

The machine-readable receipt is
`T2_WOLFRAM_EXACT_RECEIPT.json`.

## 14. Literature and novelty boundary

A fresh SciSpace search retrieved nearby invariant-theory results for:

- the orbit space of a pure octupole and a vector-plus-quadrupole preamble;
- invariants of several symmetric matrices;
- rational invariant fields for collections of second-order tensors;
- Molien series for other SO(3) representations.

No source in the retrieved set directly establishes the specific real
`STF2(Q)+STF3(O)` Krylov reconstruction proved here. This search result is not
a universal novelty theorem. The mathematical result may be used with
`novelty_status: UNRESOLVED` pending a dedicated literature review.

## 15. T2 terminal

```text
PASS_QO_SO3_ORBIT_RECONSTRUCTION_ON_NONZERO_CYCLIC_DOMAIN
/
TYPED_SINGULAR_STRATA_PRESERVED
/
GLOBAL_INVARIANT_RING_COMPLETENESS_NOT_CLAIMED
/
NOVELTY_UNRESOLVED
```

This closes the Report-A reconstruction theorem at its declared domain. It does
not certify PR #440 runtime, select an observational statistic, produce a
Planck rank, identify a physical source, or authorize publication/merge.
