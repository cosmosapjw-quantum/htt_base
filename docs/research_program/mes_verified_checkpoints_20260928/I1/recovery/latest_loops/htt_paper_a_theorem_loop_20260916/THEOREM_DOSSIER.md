# HTT PAPER-A Novelty Theorem Dossier
Date: 2026-09-16
Scope: mathematical physics / statistical methodology; no new observational analysis
Metric signature: (-,+,+,+)

## 0. Research-loop disposition

This dossier applies the GPT-6 Astra-targeted `physmath-research-harness-gpt6-astra-v4.0.0-20260908.zip`
as a procedure, not as a claim about the currently executing model. The package was byte-verified
against SHA-256 `dae76c90f2e5d691bcdd595dadbe470bacacba3bb2a036ff9788ffe7d3bfabb7`
and its workspace validator and `SHA256SUMS` checks passed.

Final promotion is deliberately **not self-authorized**. Under the harness, a genuinely independent
decision reviewer is required for `PROMOTE`; no such independent reviewer is available in this
conversation. Therefore the terminal state is:

`HOLD / INDEPENDENT_REVIEW_UNAVAILABLE`

This does not block theorem derivation, CAS checks, literature comparison, or scoped adversarial review.

---

## 1. Evidence-state vocabulary

- **ESTABLISHED**: standard theorem or clearly established prior result.
- **LITERATURE-SUPPORTED**: supported by identified external literature, but not re-proved there here.
- **DERIVED**: proved directly in this dossier from stated premises.
- **CAS-CHECKED**: exact symbolic identities independently checked in Wolfram Language.
- **IMPLEMENTATION-VERIFIED**: supported by current repository source/tests previously executed or registered.
- **NOVELTY-CANDIDATE**: no direct prior counterpart found in the bounded literature audit; not a novelty certificate.
- **UNRESOLVED**: evidence insufficient for a stronger statement.
- **BLOCKED**: an explicit prerequisite is unavailable.

---

# Part I. Kinematical identifiability

## Theorem 1 — Local first-jet realization and pointwise nonidentifiability

### Statement

Let \((M,g)\) be a smooth Lorentzian spacetime, \(p\in M\), and let
\(u^a\in T_pM\) be a future-directed unit timelike vector,
\[
g_{ab}u^a u^b=-1.
\]
Let \(K_{ab}\) be any tensor at \(p\) satisfying the normalization-compatibility condition
\[
u^a K_{ab}=0.
\]
Then there exists a smooth unit timelike vector field \(U^a\), defined on a neighborhood of \(p\),
such that
\[
U^a(p)=u^a,
\qquad
\nabla_b U_a(p)=K_{ab}.
\]

Consequently, the pointwise value \(u^a(p)\) alone does not determine the expansion,
shear, vorticity, or acceleration of the congruence at \(p\).

### Proof

Choose Riemann normal coordinates \(x^\mu\) centered at \(p\), and choose the local Lorentz frame
so that \(u^\mu(p)=(1,0,0,0)\). At \(p\),
\[
\Gamma^\alpha_{\mu\nu}(p)=0,
\qquad
\partial_\lambda g_{\mu\nu}(p)=0.
\]

Raise the first index of \(K_{ab}\) with the metric at \(p\), and define a raw vector field
\[
W^a(x)=u^a+K^a{}_{b}x^b.
\]
Then \(W^a(p)=u^a\) and
\[
\nabla_bW_a(p)=K_{ab}.
\]

Now
\[
\partial_b[g(W,W)]_p
=
2u_aK^a{}_b
=
0
\]
by the compatibility condition. Hence in a sufficiently small neighborhood \(W\) is timelike.
Define
\[
U^a=\frac{W^a}{\sqrt{-g(W,W)}}.
\]
At \(p\), the derivative of the normalization factor vanishes, so
\[
U^a(p)=u^a,
\qquad
\nabla_bU_a(p)=K_{ab}.
\]
This proves the claim. \(\square\)

### Corollary 1.1 — Arbitrary local kinematical first jet under pointwise velocity matching

For a unit timelike congruence,
\[
\nabla_bu_a
=
-A_a u_b+\frac{\theta}{3}h_{ab}+\sigma_{ab}+\omega_{ab},
\]
where \(A_a u^a=0\), \(\sigma_{ab}\) is spatial symmetric trace-free, and
\(\omega_{ab}\) is spatial antisymmetric. Every such \(K_{ab}\) obeys
\(u^aK_{ab}=0\). Therefore two normalized congruences can agree at \(p\) while having arbitrary
different allowed values of \((A_a,\theta,\sigma_{ab},\omega_{ab})\) there.

### CAS check

For the explicit Minkowski field
\[
U^\mu=\gamma(1,\alpha x,0,0),
\qquad
\gamma=(1-\alpha^2x^2)^{-1/2},
\]
Wolfram Language returns
\[
U^\mu U_\mu=-1,\qquad
(\nabla_\mu U^\mu)_{x=0}=\alpha.
\]
The constant inertial field has the same value \(U^\mu=(1,0,0,0)\) at the origin but zero
first jet.

### Adversarial review

**Defended content:** pointwise frame velocity / rapidity cannot by itself identify the
congruence first jet.

**Rejected novelty shortcut:** this is not new differential geometry. It should not be sold as a
new general theorem. Its scientific role is a cosmological inference no-go: observer boost
information is not, by itself, shear/vorticity/expansion information.

**Scope limits:** field equations, geodesic constraints, rigidity conditions, or additional
neighborhood data can restrict the admissible first jet. The theorem says only that the
pointwise value of \(u^a\) alone is insufficient.

**Evidence status:** DERIVED; CAS-CHECKED; GENERAL-MATH-NOVELTY REJECTED; COSMOLOGICAL-FRAMING
LITERATURE-SUPPORTED.

---

## Theorem 2 — Radial-vorticity null for an affine velocity field

### Statement

Let a local spatial velocity field be affine,
\[
v_i(x)=b_i+A_{ij}x^j,
\qquad
A_{ij}=S_{ij}+\Omega_{ij},
\]
with \(S_{ij}=S_{ji}\) and \(\Omega_{ij}=-\Omega_{ji}\). For a source at
\(x^i=r\,n^i\), \(\|n\|=1\), the radial velocity is
\[
v_r(n,r)=n^iv_i(rn)
=n\!\cdot b+r\,n^iS_{ij}n^j.
\]
The antisymmetric part is identically absent:
\[
n^i\Omega_{ij}n^j=0.
\]

Hence the entire three-dimensional antisymmetric affine subspace lies in the kernel of any
purely radial response of this form, for arbitrary angular and radial sampling.

### Proof

Because \(n^in^j\) is symmetric and \(\Omega_{ij}\) is antisymmetric,
\[
n^i\Omega_{ij}n^j
=
\frac12n^in^j(\Omega_{ij}+\Omega_{ji})
=0.
\]
Substituting \(x^j=rn^j\) yields the displayed radial response. \(\square\)

### Covariant version

For any vector \(k^a\),
\[
k^ak^b\omega_{ab}=0
\]
because \(k^ak^b\) is symmetric. Thus any line-of-sight scalar built only from the symmetric
contraction of \(\nabla_bu_a\) cannot contain the vorticity tensor linearly.

### CAS check

Wolfram Language evaluated a fully symbolic antisymmetric \(3\times3\) matrix \(\Omega\) and returned
\[
n^T\Omega n=0
\]
identically.

### Adversarial review

**Major novelty downgrade:** this physical fact is already implicit, and in covariant cosmography
essentially explicit, in the decomposition of observed line-of-sight expansion into expansion
monopole, acceleration dipole, and shear quadrupole; vorticity is absent from the symmetric
line-of-sight contraction.

**Important correction:** increasing radial depth does **not** recover vorticity in this
radial-only response. Any wording that merges this theorem with the separate depth-separation
theorem below is false.

**Scientific role:** exact response-kernel statement and design constraint: a transverse or otherwise
vorticity-sensitive channel is needed.

**Evidence status:** DERIVED; CAS-CHECKED; PHYSICAL FACT ESTABLISHED/LITERATURE-SUPPORTED;
NOVELTY AS STANDALONE THEOREM REJECTED; INTEGRATION INTO IDENTIFIABILITY ARCHITECTURE DEFENDED.

---

# Part II. Depth-dependent identifiability

## Theorem 3 — Single-shell dipole degeneracy and two-depth recovery

### Registered model

For direction \(n_k\in S^2\) and positive depth \(z_k\), define the six-parameter response
\[
d_k
=
n_k\!\cdot a+\frac{1}{z_k}n_k\!\cdot b,
\qquad
(a,b)\in\mathbb R^3\oplus\mathbb R^3.
\]
In the repository implementation, the first block is labelled “acceleration-like” and the second
a coherent-bulk dipole in a low-redshift log-distance linearization.

### Theorem 3A — exact single shell

Suppose all observations lie at one depth \(z_0>0\), and let the direction matrix
\(N\) have rows \(n_k^T\). Then
\[
D=[\,N,\;z_0^{-1}N\,].
\]
If \(\operatorname{rank}N=3\), then
\[
\operatorname{rank}D=3,
\qquad
\ker D
=
\{(a,b): a=-b/z_0\}.
\]
Only the three-vector combination
\[
a+\frac{b}{z_0}
\]
is identifiable.

### Proof

Factor
\[
D=N[\,I_3,\;z_0^{-1}I_3\,].
\]
The right factor has rank 3 and, when \(N\) has rank 3, the product has rank 3.
The kernel equation is exactly
\[
a+b/z_0=0.
\]
\(\square\)

### Theorem 3B — two distinct depths suffice under angular spanning

Suppose there are two depths \(z_1\ne z_2\), and at each depth the sampled directions span
\(\mathbb R^3\). Then the six-parameter design is injective:
\[
\operatorname{rank}D=6.
\]

### Proof

If \(D(a,b)=0\), angular spanning at \(z_1\) gives
\[
a+\frac{b}{z_1}=0,
\]
and angular spanning at \(z_2\) gives
\[
a+\frac{b}{z_2}=0.
\]
Subtracting,
\[
\left(\frac1{z_1}-\frac1{z_2}\right)b=0.
\]
Since \(z_1\ne z_2\), \(b=0\), hence \(a=0\). The kernel is trivial. \(\square\)

### Exact determinant certificate

For the explicit six rows corresponding to \(e_1,e_2,e_3\) at \(z_1\) and the same three
directions at \(z_2\),
\[
D=
\begin{pmatrix}
I_3&I_3/z_1\\
I_3&I_3/z_2
\end{pmatrix},
\]
Wolfram Language gives
\[
\det D
=
\frac{(z_1-z_2)^3}{z_1^3z_2^3}.
\]
Hence the determinant is nonzero exactly when \(z_1,z_2\) are finite, nonzero, and distinct.

### Corollary 3.1 — generic full rank

The relevant \(6\times6\) minors are analytic functions of directions and inverse depths.
Because one admissible configuration has a nonzero minor, rank deficiency is not an identity.
For sampling laws absolutely continuous on the allowed design manifold, the rank-deficient set is
contained in a proper zero set and is therefore nongeneric.

### Adversarial review

**Scope correction:** this theorem separates two *dipolar mechanisms with distinct depth laws*.
It does not restore vorticity.

**Source gap:** the matrix theorem is fully proved. The physical label “acceleration-like” for the
first \(n_i\) block is not, in the currently consulted repository evidence, bound to a full
cosmographic derivation. The coherent-bulk \(n_i/z\) scaling is plausible and literature-supported
at low redshift, but publication should bind the exact observable, normalization, and approximation
order.

**Novelty assessment:** the matrix algebra is elementary. No direct prior paper stating this exact
rank-3-to-rank-6 identifiability theorem was found in the bounded search. Therefore the defensible
claim is “an explicit survey-design/identifiability theorem under the declared response model,” not
“a new law of cosmological dipoles.”

**Evidence status:** DERIVED; CAS-CHECKED; IMPLEMENTATION-REGISTERED;
PHYSICAL-ATTRIBUTION PARTIALLY-SUPPORTED; NOVELTY-CANDIDATE AS APPLICATION.

---

# Part III. Nuisance-quotient identifiability

## Theorem 4 — Deterministic nuisance quotient

Let \(X,E,Y\) be finite-dimensional vector spaces and consider
\[
y=Rx+N\eta,
\]
where \(x\in X\) is the physical parameter/state and \(\eta\in E\) is an unrestricted deterministic
nuisance. Let
\[
q:Y\to Y/\operatorname{Im}N
\]
be the quotient map.

Then:

1. \(x\) is fully identifiable modulo nuisance iff
   \[
   \ker(qR)=\{0\}.
   \]

2. A linear functional \(L:X\to Z\) is identifiable modulo nuisance iff
   \[
   \ker(qR)\subseteq\ker L.
   \]

3. The identifiable dimension is
   \[
   \operatorname{rank}(qR)
   =
   \dim(\operatorname{Im}R+\operatorname{Im}N)-\dim\operatorname{Im}N
   =
   \operatorname{rank}[R\;N]-\operatorname{rank}N.
   \]

### Proof

Two states \(x,x'\) are observationally equivalent after nuisance adjustment iff there exist
\(\eta,\eta'\) such that
\[
Rx+N\eta=Rx'+N\eta'.
\]
Equivalently,
\[
R(x-x')\in\operatorname{Im}N,
\]
which is precisely
\[
qR(x-x')=0.
\]
This proves the first statement.

A linear functional \(Lx\) is constant on every observational equivalence class iff
\(Lh=0\) for every \(h\in\ker(qR)\), which is the second statement.

For the third,
\[
\operatorname{Im}(qR)
\simeq
(\operatorname{Im}R+\operatorname{Im}N)/\operatorname{Im}N,
\]
and the quotient-dimension formula gives the result. \(\square\)

### Whitening invariance

For any invertible \(W:Y\to Y\), replacing \((R,N)\) by \((WR,WN)\) changes neither the
observational equivalence relation nor the quotient identifiable dimension.

### Orthogonal computational form

After choosing an inner product and whitening, let \(P_{(WN)^\perp}\) be orthogonal projection onto
the complement of the nuisance image. Then
\[
\ker(qR)
=
\ker\!\left(P_{(WN)^\perp}WR\right).
\]

### Adversarial review

This is **standard linear algebra / linear inverse-problem mathematics**. It is not a new theorem
of mathematics and must not be advertised as one.

Its role is architectural: it gives a precise type-safe bridge between observable data space,
physical parameter space, and nuisance directions. The novelty, if any, is in the cosmological
application and in the exact physical response/null theorems plugged into this structure.

If nuisance is stochastic with a nontrivial probability law rather than an unrestricted
deterministic direction, quotienting can discard information and is not automatically the correct
likelihood operation.

**Evidence status:** ESTABLISHED mathematics; DERIVED specialization; NOVELTY AS GENERAL THEOREM
REJECTED; METHODOLOGICAL INTEGRATION DEFENDED.

---

# Part IV. Robust numerical identifiability

## Theorem 5 — Exact robustness radius of full-column-rank identification

Let \(A:\mathbb R^p\to\mathbb R^m\), \(m\ge p\), have full column rank and singular values
\[
\sigma_1\ge\cdots\ge\sigma_p>0.
\]
Then the spectral-norm distance to the set of rank-deficient matrices is exactly
\[
\operatorname{dist}_2(A,\{\operatorname{rank}<p\})
=
\sigma_p(A).
\]

Hence every perturbation satisfying
\[
\|\Delta A\|_2<\sigma_p(A)
\]
preserves full column rank, while a perturbation of norm \(\sigma_p(A)\) can destroy it.

### Proof

Weyl's singular-value perturbation inequality gives
\[
\sigma_p(A+\Delta A)
\ge
\sigma_p(A)-\|\Delta A\|_2.
\]
Thus perturbations of norm strictly below \(\sigma_p(A)\) cannot make the smallest singular value
zero.

Let \(u_p,v_p\) be a singular-vector pair for \(\sigma_p\). Then
\[
\Delta A=-\sigma_p u_pv_p^T
\]
has norm \(\sigma_p\) and makes
\[
(A+\Delta A)v_p=0.
\]
So the bound is sharp. \(\square\)

### Methodological corollary

\[
\text{exact algebraic rank}
\;\ne\;
\text{robust numerical identifiability}
\;\ne\;
\text{statistical significance}.
\]

For subspace-orientation claims, a nonzero rank margin alone is insufficient; one additionally needs
a perturbation-to-spectral-gap bound (e.g. Davis–Kahan/Wedin-type control).

### Adversarial review

This is standard numerical linear algebra, not novelty. It should be used as a claim firewall:
a numerically nonzero singular value without an error budget does not certify a physically stable
identified direction.

**Evidence status:** ESTABLISHED; NOVELTY REJECTED; METHODOLOGICAL APPLICATION DEFENDED.

---

# Part V. STF quadrupole-to-octupole boost geometry

## Theorem 6 — Exact inverse geometry of the restricted STF boost response

Let \(Q_{ab}\) be a nonzero real symmetric trace-free rank-2 tensor in Euclidean 3-space and let
\[
q_2=Q_{ab}Q^{ab}.
\]
For \(\beta_a\in\mathbb R^3\), define
\[
(B_Q\beta)_{abc}
=
\beta_aQ_{bc}+\beta_bQ_{ca}+\beta_cQ_{ab}
-\frac25\left[
\delta_{ab}(Q\beta)_c+
\delta_{ac}(Q\beta)_b+
\delta_{bc}(Q\beta)_a
\right].
\]

Then:

### (i) STF property

\(B_Q\beta\) is totally symmetric and trace-free.

### (ii) contraction identity

\[
(B_Q\beta)_{abc}Q^{bc}
=
M_{Q\,a}{}^d\beta_d,
\]
where
\[
M_Q=q_2 I+\frac65Q^2.
\]

### (iii) Gram identity

With the Frobenius inner products on vectors and STF3 tensors,
\[
B_Q^\ast B_Q=3M_Q.
\]

### (iv) injectivity

For \(Q\ne0\), \(M_Q\) is positive definite and \(B_Q\) has rank 3.

### (v) least-squares inverse

For arbitrary \(O\in\mathrm{STF}_3\), the least-squares projection onto
\(\operatorname{Im}B_Q\) is obtained with
\[
\widehat\beta
=
M_Q^{-1}(O:Q),
\qquad
(O:Q)_a=O_{abc}Q^{bc},
\]
and
\[
P_{\operatorname{Im}B_Q}O
=
B_QM_Q^{-1}(O:Q).
\]

### Proof

Symmetry is manifest. Contracting any two indices gives
\[
\delta^{ab}(B_Q\beta)_{abc}
=
2(Q\beta)_c+(Q\beta)_c
-\frac25\left[3(Q\beta)_c+(Q\beta)_c+(Q\beta)_c\right]
=0.
\]

For the contraction with \(Q^{bc}\), using \(Q^b{}_b=0\),
\[
(B_Q\beta)_{abc}Q^{bc}
=
q_2\beta_a
+2(Q^2\beta)_a
-\frac25\left[
0+(Q^2\beta)_a+(Q^2\beta)_a
\right],
\]
hence
\[
(B_Q\beta):Q
=
\left(q_2I+\frac65Q^2\right)\beta.
\]

For any vector \(\gamma\), STF symmetry and tracelessness yield
\[
\langle B_Q\gamma,O\rangle
=
3\,\gamma\cdot(O:Q).
\]
Setting \(O=B_Q\beta\) gives
\[
\langle B_Q\gamma,B_Q\beta\rangle
=
3\gamma\cdot M_Q\beta,
\]
so \(B_Q^\ast B_Q=3M_Q\).

For \(Q\ne0\),
\[
\beta^TM_Q\beta
=
q_2\|\beta\|^2+\frac65\|Q\beta\|^2>0
\]
for every nonzero \(\beta\), proving positive definiteness and injectivity.

The normal equations for least squares are
\[
B_Q^\ast B_Q\,\widehat\beta
=
B_Q^\ast O.
\]
Using the two adjoint identities above,
\[
3M_Q\widehat\beta=3(O:Q),
\]
giving the result. \(\square\)

### CAS verification

Wolfram Language evaluated a generic symbolic trace-free symmetric \(Q\) and generic
\(\beta\). It returned exactly:

- all three pair traces of \(B_Q\beta\): zero;
- contraction residual against \(M_Q\beta\): \((0,0,0)\);
- Gram residual \(B_Q^\ast B_Q-3M_Q\): the zero \(3\times3\) matrix.

---

## Theorem 7 — Sharp condition-number bound

Under the hypotheses of Theorem 6,
\[
\boxed{\kappa_2(M_Q)\le\frac53}.
\]
The bound is sharp. Equality occurs precisely when the eigenvalue magnitudes of \(Q\) are in the
ratio
\[
5:4:1,
\]
equivalently when its signed spectrum is proportional to
\[
(-5,4,1)
\]
up to permutation and overall sign.

Consequently,
\[
\kappa_2(B_Q)
\le
\sqrt{\frac53}.
\]

### Proof

Let the real eigenvalues of \(Q\) be trace-free and nonzero. Order their magnitudes as
\[
A\ge B\ge C\ge0.
\]
Because three real numbers sum to zero, the largest magnitude belongs to the eigenvalue whose sign is
opposite the other two, hence
\[
A=B+C.
\]

The eigenvalues of \(M_Q\) are
\[
\mu_i=q_2+\frac65\lambda_i^2,
\qquad
q_2=A^2+B^2+C^2.
\]
Thus
\[
\kappa_2(M_Q)
=
\frac{q_2+\frac65A^2}{q_2+\frac65C^2}.
\]
The desired inequality is equivalent to
\[
4A^2\le5B^2+20C^2.
\]
Substitute \(A=B+C\):
\[
5B^2+20C^2-4(B+C)^2
=
(B-4C)^2
\ge0.
\]
Hence \(\kappa_2(M_Q)\le5/3\). Equality holds iff \(B=4C\), hence \(A=5C\).

Finally, \(B_Q^\ast B_Q=3M_Q\), so
\[
\kappa_2(B_Q)^2=\kappa_2(M_Q).
\]
\(\square\)

### CAS verification

Wolfram Language reduced the sharp inequality residual to
\[
(B-4C)^2
\]
and returned the equality condition \(B=4C\).

### Adversarial review

**Rejected shortcut:** Lorentz boosting of the CMB, aberration kernels, and adjacent-\(\ell\) mixing
are well-established and must not be claimed as new.

**Surviving novelty candidate:** the specific restricted STF2→STF3 inverse geometry,
the closed-form \(M_Q\), projector, and sharp \(5/3\) conditioning bound were not matched to a direct
prior result in the bounded literature search. This is the strongest theorem-level novelty survivor
in the current loop.

**Remaining blocker:** absence of a matched paper in a bounded search is not a novelty certificate.
A focused invariant-theory / CMB-boost literature search, preferably with primary-source inspection,
is still required before a “first” claim.

**Evidence status:** DERIVED; CAS-CHECKED; REPOSITORY-IMPLEMENTED/VERIFIED in scoped WU-010;
GENERAL BOOST PHYSICS ESTABLISHED; RESTRICTED INVERSE GEOMETRY NOVELTY-CANDIDATE.

---

# Part VI. Finite-sample validity of data-adaptive pipelines

## Theorem 8 — Recompute the adaptive pipeline under the randomization group

Let a finite group \(G\) act on a sample space \(\mathcal X\), and suppose the null law of
\(X\) is \(G\)-invariant. Let \(S:\mathcal X\to\mathbb R\) be any fixed measurable statistic,
where “fixed” means that all data-adaptive operations are part of the function \(S\).

Then the full-group randomization p-value
\[
p(X)
=
\frac1{|G|}
\sum_{g\in G}
\mathbf1\!\{S(gX)\ge S(X)\}
\]
is super-uniform under the null (with the usual tie convention).

If instead one derives an auxiliary object \(A(X)\) from the observed data and then freezes it while
transforming the data,
\[
S_{\rm frozen}(gX;X)=t(gX,A(X)),
\]
there is no general exactness guarantee.

### Proof sketch of the valid case

Condition on the orbit \(\{gX:g\in G\}\). Under group invariance, the observed orbit element is
uniform over the orbit (modulo stabilizers), and its rank among the values \(\{S(gX)\}\) is therefore
uniform/super-uniform under the standard tie rule. All adaptive steps are legitimate if they are
recomputed inside \(S(gX)\).

### Exact counterexample to frozen adaptivity

Let
\[
\mathcal X=\{0,1\},
\]
with the null uniform on the two points and \(G=\{e,s\}\), where \(s(x)=1-x\). Let
\[
A(x)=x,
\qquad
t(y,a)=\mathbf1\{y=a\}.
\]

For the observed data,
\[
t(x,A(x))=1.
\]
If \(A(x)\) is frozen while the transformed sample is evaluated,
\[
t(sx,A(x))=0,
\]
so the full-group p-value is
\[
p_{\rm frozen}(x)=\frac12
\]
for both \(x=0,1\). Therefore
\[
\Pr(p_{\rm frozen}\le1/2)=1>1/2,
\]
which is anti-conservative.

If the adaptive anchor is recomputed,
\[
S(x)=t(x,A(x))=1
\]
for both points, so every randomization p-value is \(1\).

### CAS check

Wolfram Language returned exactly:

- frozen p-values: \(\{1/2,1/2\}\);
- recomputed p-values: \(\{1,1\}\);
- \(\Pr(p_{\rm frozen}\le1/2)=1\).

### Cosmological implication

If a CMB morphology analysis derives from the observed map an axis, anchor, mask choice, response
direction, nuisance subspace, rank threshold, or scan family that affects the statistic, then an exact
randomization/null experiment must reproduce the corresponding adaptive operation on each null draw
unless a separate conditional-inference proof justifies freezing it.

### Adversarial review

The randomization principle is established statistics, not a new statistical theorem. The exact
two-point counterexample is pedagogically useful but elementary. The scientific contribution is the
claim discipline it imposes on data-dependent CMB pipelines.

**Evidence status:** ESTABLISHED statistical principle; DERIVED counterexample; CAS-CHECKED;
NOVELTY AS GENERAL STATISTICS REJECTED; COSMOLOGICAL-PIPELINE APPLICATION DEFENDED.

---

# Part VII. Auxiliary lemma

## Lemma 9 — Temporal STF tensor rank

For any matrix \(T\),
\[
\operatorname{rank}(T\otimes I_5)
=
5\,\operatorname{rank}T.
\]

This follows from the standard Kronecker-product rank identity
\[
\operatorname{rank}(A\otimes B)=\operatorname{rank}A\,\operatorname{rank}B.
\]

**Adversarial disposition:** useful computational lemma, no novelty claim.

---

# Part VIII. Adversarial decision ledger

| Candidate | Mathematical validity | Novelty after hostile review | Scientific role | Current disposition |
|---|---|---|---|---|
| First-jet nonidentifiability | DEFENDED | General theorem not novel | category-error firewall | keep as foundational proposition |
| Radial-vorticity null | DEFENDED | established/implicit prior art | exact kernel + survey-channel requirement | keep, do not headline as discovery |
| Single-shell → two-depth rank | DEFENDED | application-level novelty plausible | depth-driven identifiability | **survivor**, source binding needed |
| Nuisance quotient | DEFENDED | standard math | central architecture | keep as framework theorem, no novelty claim |
| Robust-rank radius | DEFENDED | standard numerical LA | numerical claim firewall | keep |
| STF boost inverse \(M_Q\) | DEFENDED + CAS | direct prior match not found | exact solved response example | **strong novelty survivor** |
| Sharp \(\kappa(M_Q)\le5/3\) | DEFENDED + CAS | direct prior match not found | stable inverse guarantee | **strong novelty survivor** |
| Adaptive-null recomputation | DEFENDED + exact counterexample | established stats | finite-sample validity | keep as methods theorem/application |
| Temporal STF rank | DEFENDED | standard | supporting lemma | appendix/lemma |

---

# Part IX. Negative results and corrections generated by this loop

1. **Rejected:** “broad depth support recovers radial vorticity.”
   - False. The radial antisymmetric kernel persists for every radius.
   - The depth theorem concerns two different dipolar response blocks, not vorticity.

2. **Rejected:** “radial-vorticity null is a new mathematical discovery.”
   - The antisymmetry argument and covariant line-of-sight decomposition are established.

3. **Rejected:** “pointwise boost/velocity no-go is new differential geometry.”
   - The local first-jet freedom is standard. Its value is inference discipline.

4. **Rejected:** “nuisance quotient is new inverse-problem mathematics.”
   - Standard linear algebra.

5. **Rejected:** “finite-null closure is a new permutation theorem.”
   - Standard invariance/randomization theory. The application to adaptive cosmological pipelines is the relevant contribution.

6. **Held:** physical interpretation of the single-shell first block as “acceleration-like.”
   - The current repository code labels it so, but the exact cosmographic source equation was not bound in the consulted evidence.
   - The algebraic theorem is valid independently.

7. **Held:** priority claim for the restricted STF boost inverse / \(5/3\) bound.
   - Exact derivation passed; no direct prior match found in bounded search.
   - Requires targeted primary-literature novelty audit.

8. **Repository inconsistency:** `PAPER_THEOREM_MAP.md` marks radial/single-shell/temporal rows “closed PR07-004” in the table, but its bottom exit-criteria summary still calls them `BLOCKED_PROOF_REVIEW`.
   - Publication SSOT must be repaired before freeze.

---

# Part X. Recommended paper-level theorem spine

For a mathematical-physics/statistical-methods PAPER-A, the strongest defensible spine is:

1. **Definition:** observable state, physical state, response, nuisance equivalence.
2. **Theorem 4:** nuisance-quotient identifiability (explicitly standard mathematics, used as architecture).
3. **Theorem 1:** pointwise velocity does not determine congruence first jet (foundational no-go, not sold as new math).
4. **Theorem 2:** radial vorticity lies in the response kernel (known physical fact, made explicit).
5. **Theorem 3:** single-shell dipole degeneracy and depth-driven rank recovery (application novelty survivor).
6. **Theorems 6–7:** exact STF boost inverse geometry and sharp conditioning (strongest theorem-level novelty survivor).
7. **Theorem 5:** robust numerical rank radius (standard numerical LA firewall).
8. **Theorem 8:** adaptive null must be rerun as a full pipeline for exact randomization validity (standard stats, cosmological application).

The paper's novelty should be framed as a **typed cosmological identifiability architecture plus specific exact response theorems**, not as the invention of quotient spaces, SVD, permutation tests, or Lorentz boosts.

---

# Part XI. Literature boundary used in this loop

Primary/peer-reviewed comparison targets include:

- Maartens, Ellis & Stoeger, almost-isotropy / CMB bounds on kinematical and curvature quantities.
- Räsänen, *Relation between the isotropy of the CMB and the geometry of the universe*, PRD 79, 123522 (2009).
- Clarkson et al., covariant cosmography / line-of-sight expansion decomposition.
- Copi, Huterer, Starkman et al., multipole-vector descriptions of low-\(\ell\) CMB morphology.
- Dai & Chluba, exact CMB aberration/boost kernels, PRD 89, 123504 (2014).
- Chluba & Ravenni, general boost-operator treatment (2026).
- Peculiar-velocity / luminosity-distance literature establishing radial-only observables and depth-dependent bulk-flow response.
- Standard permutation/randomization-test literature on group invariance and nuisance/adaptive procedures.

This search was bounded and is not an exhaustive novelty certificate.

---

# Part XII. Terminal state

## Local scientific state

- analytic theorem derivations: COMPLETE for the scope above;
- exact Wolfram cross-checks: PASS for registered algebraic identities checked above;
- adversarial self-review: COMPLETE, with multiple novelty downgrades and one substantive scope correction;
- literature contrast: COMPLETE at bounded-search level;
- independent promotion review: UNAVAILABLE.

## Decision

`HOLD / INDEPENDENT_REVIEW_UNAVAILABLE`

## Survivors recommended for the next freeze cycle

1. **STF boost inverse geometry and sharp conditioning theorem** — highest-priority novelty audit.
2. **Single-shell / multi-depth dipole identifiability theorem** — bind its physical source law and approximation regime.
3. **Unified response-quotient architecture** — retain as the paper's organizing theorem, explicitly crediting standard inverse-problem mathematics.
4. **Adaptive finite-null closure** — retain as statistical-methods firewall, explicitly crediting standard randomization theory.

