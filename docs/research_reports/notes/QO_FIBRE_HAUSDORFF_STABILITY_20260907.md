# Fixed-quadrupole contraction fibres: exact Hausdorff distance and sharp boundary sensitivity

Date: 2026-09-07
Owner: MAIN conversation; observable Q/O theory
Evidence: DIRECT_DERIVATION; two scalar decimal checks only; NOT_NEW_CAS_OR_DECODER_VALIDATION
Status: supplementary research note, noncanonical; no production or acceptance-threshold change

## 1. Input and question

The preceding note is `docs/research_reports/notes/QO_CONTRACTION_FIBRE_GEOMETRY_20260907.md` at commit `d5a5444bab6be7dcc79e362a52811882dd0a66a3`, Git blob `0201ac7c08a33a2b041ccfedbb9dc582aa198abd`. Its sections 2–4 were freshly read for this continuation. It derives the contraction right inverse and unit-norm fibres from the retained T5 adjoint/projector identities. Those identities are the source input, not a new execution in this note.

The question is more specific than whether M_q is well conditioned: how does the entire unit-octupole feasible set change when the prescribed contraction changes, with the quadrupole held fixed?

Use real STF2 q and STF3 o in a fixed three-dimensional Euclidean spatial frame, full Frobenius products, q:q=1 and o:o=1. They are observable temperature shapes normalised by their nonzero Frobenius amplitudes. Their coordinates and v=o:q are dimensionless. v is not physical velocity, beta_RO or congruence kinematics. There is no natural-units convention and no new Lorentzian or transport assertion.

Set

\[
L_qo=o:q,\quad M_q=I+\frac65q^2,\quad
R_q=\mathcal B_q M_q^{-1},\quad
(\mathcal B_q w)_{abc}=3w_{\langle a}q_{bc\rangle}.
\]

Inherited identities give L_q R_q=I, R_q v perpendicular to N=ker L_q, dim N=4, and

\[
\|R_q v\|_F^2=\eta_v:=3v^TM_q^{-1}v.
\]

For eta_v<=1, write rho_v=sqrt(1-eta_v). The nonempty compact unit fibre is

\[
F_q(v)=R_qv+\rho_v S(N),\qquad
S(N)=\{z\in N:\|z\|_F=1\}.
\]

At rho_v=0 this notation denotes the singleton {R_qv}. For eta_v>1 the fibre is empty. All Hausdorff formulas below compare nonempty fibres at the SAME fixed q and the same metric. They do not apply without modification when q, the metric, amplitudes or a coordinate chart also change.

## 2. Exact Hausdorff distance

For nonempty compact sets A,B define

\[
d_H(A,B)=\max\{\sup_{a\in A}\inf_{b\in B}\|a-b\|_F,
\sup_{b\in B}\inf_{a\in A}\|a-b\|_F\}.
\]

For x=R_qv+rho_v z and y=R_qw+rho_w z', with z,z' in S(N), orthogonality gives

\[
\|x-y\|_F^2=\|R_q(v-w)\|_F^2+
\|\rho_vz-\rho_wz'\|_F^2.
\]

For fixed z the last term is minimised by z'=z when both radii are positive, and its minimum is (rho_v-rho_w)^2. The same expression holds if one or both radii vanish. It is independent of z, so the directed suprema are equal. Hence

\[
\boxed{d_H(F_q(v),F_q(w))^2
=3(v-w)^TM_q^{-1}(v-w)
+\left(\sqrt{1-\eta_v}-\sqrt{1-\eta_w}\right)^2.}
\]

This is a set distance, not a distance between arbitrarily selected representatives or a rotational-quotient distance. It concerns the reduced contraction/norm problem, not the full ten-trilinear packet image.

## 3. Interior Lipschitz and global relative-feasible Holder bounds

Introduce the fixed contraction metric

\[
\|a\|_q=\sqrt{3a^TM_q^{-1}a},\qquad s=\|v-w\|_q.
\]

Thus eta_v=||v||_q^2. On the feasible ellipsoid, ||v||_q,||w||_q<=1, and

\[
|\eta_v-\eta_w|\le(\|v\|_q+\|w\|_q)s\le2s.
\]

Since |sqrt(a)-sqrt(b)|^2<=|a-b| for a,b>=0,

\[
\boxed{d_H(F_q(v),F_q(w))\le\sqrt{s^2+2s}.}
\]

This gives one-half Holder continuity for small s, relative to the feasible ellipsoid. It does not promise a nonempty fibre for outward perturbations through its boundary.

If both eta_v and eta_w are at most 1-delta for fixed 0<delta<=1, then

\[
|\rho_v-\rho_w|
=\frac{|\eta_v-\eta_w|}{\rho_v+\rho_w}
\le\sqrt{\frac{1-\delta}{\delta}}s.
\]

Substitution into the exact distance formula yields

\[
\boxed{d_H(F_q(v),F_q(w))\le\delta^{-1/2}\|v-w\|_q.}
\]

For unit q, M_q>=I, so also d_H<=sqrt(3/delta)||v-w||_2. Delta here is an analytical distance from saturation, not a new numerical acceptance threshold or calibration radius.

## 4. Sharp failure of a uniform Lipschitz bound

Choose any v_* with eta_*=1 and put v_t=(1-t)v_*, 0<t<1. Then

\[
\eta_t=(1-t)^2,\quad\rho_t=\sqrt{2t-t^2},\quad
\|v_t-v_*\|_q=t.
\]

The boundary fibre is {o_*}, where o_*=R_qv_*. Every element of F_q(v_t) has the form

\[
o_t=(1-t)o_*+\sqrt{2t-t^2}\,z,\quad z\in S(N).
\]

It obeys L_qo_t=v_t and ||o_t||_F=1, while

\[
\|o_t-o_*\|_F^2=t^2+(2t-t^2)=2t.
\]

Consequently

\[
\boxed{d_H(F_q(v_t),F_q(v_*))=\sqrt{2t}.}
\]

The ratio to ||v_t-v_*||_q is sqrt(2/t), which diverges. More generally, no bound C||v_t-v_*||_q^alpha with alpha>1/2 and fixed C can hold along this path. Together with section 3, this establishes the sharp local exponent one half. This is an elementary exact consequence of the sphere constraint; it is not a proof that the linear right inverse R_q is ill conditioned.

## 5. The phenomenon occurs on a cyclic Q/O chart

It is not restricted to the repeated-eigenvalue equality example used for the earlier universal 3/5 contraction bound. Take

\[
q=\frac1{\sqrt2}\operatorname{diag}(-1,0,1),\quad
M_q=\operatorname{diag}(8/5,1,8/5),
\]

\[
v_*=(\sqrt{8/45},\ 1/3,\ \sqrt{8/45})^T.
\]

The quadrupole is STF and unit norm, has three distinct eigenvalues, and all three components of v_* are nonzero. Direct substitution gives

\[
s_3=0,\quad\mu_0=7/15,\quad\mu_1=0,\quad\mu_2=8/45,
\]

\[
\eta_*=(120\mu_0-90\mu_2)/40=(56-16)/40=1.
\]

With ordered eigenvalues (-1/sqrt2,0,1/sqrt2),

\[
\det K_*=
\det[v_*,qv_*,q^2v_*]=\frac{4\sqrt2}{135}>0.
\]

Its Gram matrix is

\[
G_*=K_*^TK_*=\frac1{45}
\begin{pmatrix}21&0&8\\0&8&0\\8&0&4\end{pmatrix}.
\]

The eigenvalues are (25-sqrt545)/90, 8/45, (25+sqrt545)/90, so

\[
\kappa_2(K_*)=\sqrt{\frac{25+\sqrt{545}}{25-\sqrt{545}}}
\simeq5.405161599102375,\qquad\kappa_2(M_q)=8/5.
\]

Because K_t=(1-t)K_*, the relative condition number remains exactly this value for 0<t<1. The determinant is (1-t)^3 det K_* and remains nonzero. Thus the square-root fibre sensitivity can occur as t tends to zero while both M_q and the Krylov chart remain well conditioned. The t=1 endpoint, where v=0 and the chart fails, is not needed for the conclusion.

A concrete unit residual is z_{012}=1/sqrt6 and its six permutations, with all other components zero (indices 0,1,2). It is fully symmetric, trace-free, unit norm and L_qz=0 because q is diagonal. Together with o_*=B_q M_q^{-1}v_* this supplies explicit exact tensor witnesses o_t, not just a dimension count.

No production decoder call for these new witnesses has been executed in this session. Algebraic cyclicity and these condition values are not a claim that every floating-point check of an unexecuted witness passed.

## 6. Why this does not contradict the accepted decoder evidence

The fibres deliberately discard trilinear information. Along the explicit path, let A_* map an STF3 tensor to the ten trilinears in K_*. Since K_t=(1-t)K_*, the full packet has

\[
\tau_t=(1-t)^3\left[(1-t)A_*o_*+\sqrt{2t-t^2}\,A_*z\right].
\]

The exact trilinear map is injective for invertible K_*, so A_*z!=0. Consequently the full trilinear variation already has a leading square-root term. It is incorrect to treat the change of the complete packet as O(t) merely because v and the first moments change by O(t).

This is a reduced-information feasible-set sensitivity result, not a counterexample to full-packet reconstruction or its fixed numerical tests. PR451's accepted 28-node native evidence at `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`, published in PR456 at `43b21fada60ddd610e65d58fb995661939bd4050`, is retained with its replay-or-typed-unavailable boundary. Neither that run nor the four-lemma R2 contract is retroactively claimed to verify this note.

The practical interpretation is narrower: a bounded matrix condition number does not by itself control the Hausdorff sensitivity of a norm-constrained reduced feasible set. Away from saturation the explicit delta bound quantifies stability. At saturation, uncertainty or abstention must be treated according to a separately specified inference problem; no empirical threshold, prior or error model is introduced here.

## 7. Validation, literature role and non-actions

Direct checks performed in the derivation: orthogonal-distance minimisation including zero radii; exact radial family norm/contraction; q trace/norm/spectrum; eta=1 from both matrix and moment forms; positive Krylov determinant and exact Gram eigenvalues; fixed condition number under common scaling; explicit nonzero kernel tensor; distinction from complete trilinear perturbations.

Tool execution in this main session: one shell-backed process and one independent Python attempt each returned ClientError before an observable result. Wolfram connection returned MCP/SSE HTTP 404; no kernel result followed. The web calculator evaluated only the scalar condition expression (5.405161599102375) and determinant expression (0.04190262407031393). It did not verify tensors, general identities or a decoder. No new native, SymPy/Lean, Monte Carlo, stress, observation or PDF execution is claimed.

SciSpace located contextual literature; official publisher pages were read for:

- A. van der Sluis, 'Stability of the solutions of linear least squares problems', Numerische Mathematik 23, 241–254 (1974), DOI 10.1007/BF01400307. The publisher summary addresses geometric explanations and perturbation-dependent least-squares conditioning. Its later electronic publication date is not the original research year.
- A. C. M. Ran and L. Rodman, 'Stability in Matrix Analysis Problems', pp. 349–376 (2015), DOI 10.1007/978-3-319-15260-8_13. The abstract distinguishes stability and fractional-power stability of associated matrix-solution sets.

Only abstracts/metadata were consulted, not the full paywalled proofs. These references motivate distinguishing stability notions; neither is credited with the project-specific STF Hausdorff formula or cyclic example. The proof is the explicit calculation above. Novelty is not established.

This is result-informed MAIN derivation/review, not an independent blind audit. No manuscript/PDF, production code, test, numerical tolerance, claim ledger, original receipt, gate or source branch owned by a local writer is changed. Canonical remains T9 v4/30 and candidate remains 40. This supplementary note does not delay or expand the already registered PR450 source-replay task.
