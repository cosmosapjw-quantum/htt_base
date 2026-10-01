# CAS11-C03 weighted projection: SageMath and Singular axis

## Statement and scope

Let \(H\) be **any** finite-dimensional real vector space, including dimension zero, with a positive-definite symmetric bilinear form \(\langle u,v\rangle_W\). Let \(V\subseteq H\) be any subspace and \(P\) its \(W\)-orthogonal projection. For any finite family \(K_1,\ldots,K_m\in H\), including \(m=0\), set \(r_i=(I-P)K_i\) and \(R_{ij}=\langle r_i,r_j\rangle_W\). We prove all three target statements for every such \(H,V,K_i\) and all real coefficient vectors \(a\). The component is deterministic finite-dimensional algebra; it does not construct a physical residual, a covariance model, or a measure-space null class.

## Arbitrary-dimensional proof of projection

Positive definiteness gives a \(W\)-orthonormal basis \(u_1,\ldots,u_k\) of \(V\) by finite Gram–Schmidt. If \(V=\{0\}\), take the empty basis and \(k=0\). Define

\[
P x=\sum_{j=1}^{k}u_j\langle u_j,x\rangle_W.
\]

For every basis vector \(u_h\), bilinearity and orthonormality give \(\langle u_h,Px\rangle_W=\langle u_h,x\rangle_W\). Linearity then gives \(\langle v,(I-P)x\rangle_W=0\) for every \(v\in V\). Also \(Px\in V\), so applying this identity with \(v=u_h\) to \(Px\) gives \(P(Px)=Px\). Thus \(P^2=P\) and the prescribed orthogonality holds for every \(x\). At \(V=H\), \(P=I\); at \(V=0\), \(P=0\); in dimension zero these agree. No inverse is needed in any branch.

In coordinates with an arbitrary basis \(B\) of \(V\), \(G=B^TWB\) is positive definite when \(k>0\): for nonzero \(c\), \(c^TGc=\|Bc\|_W^2>0\). Therefore \(P=B G^{-1}B^T W\). The algebraic identities \(G=B^TWB\), \(P^2=P\), and \(B^TW(I-P)=0\) are the SageMath projection kernel. Singular checks the denominator-cleared rank-one kernel \(N=b(b^TW),d=b^TWb,N^2=dN,b^TW(dI-N)=0\). For nonzero \(b\), \(d>0\) and \(P=N/d\). These kernels illustrate and test the algebra; the preceding basis argument supplies every dimension and subspace.

## Arbitrary-dimensional proof of residual Gram positivity

For every \(a\in\mathbb R^m\), finite bilinearity yields

\[
a^TRa=\sum_{i,j}a_i a_j\langle r_i,r_j\rangle_W
=\left\langle\sum_i a_i r_i,\sum_j a_j r_j\right\rangle_W
=\left\|\sum_i a_i r_i\right\|_W^2\geq0.
\]

This also proves symmetry of \(R\). For \(m=0\), all sums are zero and the unique \(0\times0\) Gram matrix is positive semidefinite by the universal quantifier over its sole coefficient vector. If the residuals vanish or are dependent, \(R\) can be singular; positivity never required residual independence or \(R^{-1}\). Equality occurs exactly when \(\sum_i a_i r_i=0\), by positive definiteness of \(W\). The same reasoning includes \(V=H\), where every \(r_i=0\).

## Arbitrary-dimensional Cauchy–Schwarz certificate

Write \(A=\langle x,x\rangle_W\), \(B=\langle x,y\rangle_W\), \(C=\langle y,y\rangle_W\). If \(y=0\), then \(B=C=0\) and the inequality is equality. Otherwise \(C>0\); choosing the scalar projection coefficient \(t=B/C\) gives the exact square certificate

\[
0\leq\|x-ty\|_W^2=A-2tB+t^2C=A-B^2/C,
\qquad AC-B^2=C\|x-(B/C)y\|_W^2\geq0.
\]

Thus \(|\langle x,y\rangle_W|^2\leq\langle x,x\rangle_W\langle y,y\rangle_W\). The branch \(x=0\) is included. When \(y\ne0\), equality holds exactly when \(x=(B/C)y\); when \(y=0\), it always holds. Dimension zero has only the zero-vector branch.

There is also an arbitrary-dimension coordinate sum-of-squares form. Because \(W\) is positive definite, choose a linear isometry to Euclidean coordinates (for example, a \(W\)-orthonormal basis, or \(W=L^TL\) with \(X=Lx,Y=Ly\)). For any finite dimension \(n\), direct expansion and pairing of the \((i,j)\) and \((j,i)\) terms gives

\[
\|X\|^2\|Y\|^2-(X\cdot Y)^2
=\sum_{1\leq i<j\leq n}(X_iY_j-X_jY_i)^2.
\]

For \(n=0,1\) the sum is empty and equals zero. The SageMath and Singular scripts verify this polynomial kernel for generic symbolic diagonal weights and three coordinates; they do not substitute a fixed-dimension computation for the universal expansion above.

## Engine coverage and claim boundary

The SageMath source uses exact rational-function algebra for a generic \(3\times2\) basis and symbolic diagonal weights; it checks idempotence, orthogonality, the residual Gram identity and Gram determinant SOS, and weighted Cauchy–Schwarz SOS. The Singular source independently checks the same Gram and SOS polynomial kernels and all entries of a denominator-cleared rank-one projection. Generic indeterminates make these exact polynomial identities in the displayed sizes, not numerical examples. The analytic arguments above cover arbitrary positive-definite \(W\), arbitrary finite dimension, empty family, zero/full \(V\), dependent residuals, zero norm and equality branches. The engine results cannot validate the separate measure-space null-class and integrability obligations of the parent CAS-11 theorem, or any scientific interpretation. No sibling-axis proof or result was used.
