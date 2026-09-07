---
title: 'From a CMB Sky Map to Physical Constraints'
subtitle: 'An introductory account of tensor morphology, kinematical bounds and response-limited inference'
author: Jiwon Park
date: 7 September 2026
lang: en-GB
---

## Abstract

A map of the cosmic microwave background describes a temperature in each direction. A cosmological model describes matter, radiation and geometry throughout spacetime. How can the first constrain the second? We develop this question from elementary tensor algebra. We construct the temperature quadrupole and octupole, prove their harmonic normalisations, and explain how a proper-rotation invariant description can retain information lost by scalar powers. We then introduce the kinematics of a family of observers and distinguish physical shear and vorticity from temperature tensors. Conditional isotropy bounds constrain the sizes of physical sectors, but do not reconstruct their directions. A response map and a feasible set are needed for that further step.

The account includes proofs of the finite-dimensional reconstruction and inference statements, exact finite-sample rank arguments, the local-observer temperature response, the quotient by an unrestricted nuisance image, and a matrix-valued numerical-error criterion. Worked counterexamples identify the assumptions that cannot be removed. A continuum masked-sky calculation is explained by an explicit algebraic certificate; finite-resolution conclusions and numerical observations are kept separate. No new observational estimate is made. The purpose is to make the relation between an observable pattern, a physical model and an identifiable conclusion understandable without access to the research project's internal records.

## How to read this report

We assume basic differentiation and integration, elementary matrix multiplication, and the usual rules for probabilities of events. No prior knowledge of symmetric trace-free tensors, rotation orbits, partial identification or CMB aberration is required. Section 2 supplies the finite-dimensional linear algebra used later. Section 3 introduces the angular description of a sky. Readers already familiar with these topics may begin with Section 4, returning to the definitions when needed.

The exposition follows one question throughout: which information is retained at each step from a temperature map to a physical conclusion? A definition tells us what object we use. A proposition or theorem states a mathematical consequence of specified hypotheses; its proof is supplied in the text or in the explicitly indicated appendix. A physical-input box states a modelling or literature premise rather than pretending that it has been proved from a sky map. A computational-result box reports a calculation, not a universal theorem. References provide attribution and further context. They are not substitutes for the proofs of the finite-dimensional propositions below.

One boundary needs stating at the outset. The general Einstein–Liouville almost-isotropy programme is a physical input to the MES application in Section 6. This report states the retained bounds and the derivative premises explicitly and derives their use in the present inference problem; it does not claim to reproduce the complete spacetime almost-EGS theorem. Likewise, historical numerical rank observations are not converted into symbolic proofs. This distinction is necessary for an honest account of what is self-contained: the mathematical deductions are internal, while the physical premises and the status of numerical evidence remain visible.

# Part I. Why a tensor description is needed

## 1. From a temperature pattern to a physical question

### 1.1 What the sky tells us directly

The cosmic microwave background, abbreviated CMB, is observed as radiation arriving from different directions. At a fixed observation event, let \(T(n)\) denote its thermodynamic temperature in the outward unit direction \(n\). The direction lies on the unit sphere, \(n\cdot n=1\). We split the field into its angular average and anisotropy,

\[
T(n)=T_0+\Delta T(n),\qquad
T_0=\frac1{4\pi}\int_{S^2}T(n)\,d\Omega.
\tag{1.1}
\]

The solid-angle element is \(d\Omega=\sin\theta\,d\theta\,d\varphi\), and the area of the unit sphere is \(4\pi\). Temperature has not been made dimensionless. The fractional anisotropy is \(\Delta T/T_0\), which is meaningful when \(T_0>0\).

A low angular multipole describes a pattern varying slowly across the sky. The dipole has one positive and one negative lobe. The quadrupole and octupole describe the next angular sectors. Their powers measure sizes, but not the complete arrangement of the pattern. Two maps can have the same quadrupole and octupole powers and different relative orientations. Later we will construct an even stronger example: a pattern and its mirror can agree in several scalar summaries while differing in an orientation-sensitive invariant.

This is the first reason to retain tensors. A scalar summary can be useful, but it is a many-to-one map. We should know what it removes before trying to invert it.

### 1.2 What the sky does not tell us by representation alone

Now consider the motion of matter in spacetime. A family of observers may expand, distort a small material ball into an ellipsoid, rotate, or accelerate. These effects are described by expansion, shear, vorticity and acceleration. They are not temperature multipoles. A temperature quadrupole and a shear tensor both have five independent components, but this does not make them the same physical object.

The missing ingredient is a response: a rule telling us how a change in a physical state changes the observation. The rule can depend on matter content, the observer, the epoch, the angular window and the data-processing procedure. Without such a rule, a similarity of tensor type is only a similarity of representation.

We therefore separate three questions. First, how completely have we represented the observable sky? Second, which physical states obey the maintained bounds and assumptions? Third, which of those states can produce the observation under a declared response? The distinction is the central organising principle of this report.

### 1.3 A small inverse problem before the cosmological one

Suppose a measurement gives

\[
y=x_1+x_2.
\tag{1.2}
\]

The value \(y\) certainly responds to either coordinate. It does not identify the two coordinates separately: \((x_1+t,x_2-t)\) gives the same observation for every real \(t\). This is a degeneracy, not a failure of measurement precision.

An independent bound, such as \(|x_1|\le1\) and \(|x_2|\le1\), can shorten the compatible line to a segment. It does not generally select a point. With the different maintained conditions \(x_1,x_2\ge0\) and the exact observation \(y=0\), however, the only compatible state is \((0,0)\). An inequality can remove a degeneracy, but only through its stated domain and the actual observation.

The CMB problem is more elaborate, but the logical structure is the same. A complete angular representation, a bound on physical magnitudes and a unique physical interpretation are three different achievements.

## 2. Mathematical tools used in the report

### 2.1 Components, contractions and norms

Spatial indices \(i,j,k\) run from 1 to 3. Repeated spatial indices are summed with the Euclidean metric \(\delta_{ij}\). Thus \(x_ix_i=x_1^2+x_2^2+x_3^2\). A rank-two tensor is represented by a matrix; a rank-three tensor is an array with three indices. Changing an orthonormal frame changes their components, but not their tensorial meaning.

The full Frobenius products are

\[
A:B=A_{ij}B_{ij},\qquad
U:V=U_{ijk}V_{ijk},\qquad
\|A\|_F=\sqrt{A:A}.
\tag{2.1}
\]

Every component is counted. For example, a symmetric matrix with \(A_{12}=A_{21}=a\) contributes \(2a^2\) to its squared norm. Storing only independent components does not remove their multiplicities from the metric.

Symmetrisation averages over the permutations of the indices. For two indices,

\[
A_{(ij)}=\tfrac12(A_{ij}+A_{ji}),\qquad
A_{[ij]}=\tfrac12(A_{ij}-A_{ji}).
\tag{2.2}
\]

Angle brackets denote a symmetric trace-free projection. For a symmetric rank-two tensor,

\[
A_{\langle ij\rangle}=A_{ij}-\tfrac13\delta_{ij}A_{kk}.
\tag{2.3}
\]

The notation STF means symmetric trace-free. For a fully symmetric rank-three tensor \(S\), put \(t_i=S_{ijj}\). Then

\[
S_{\langle ijk\rangle}
=S_{ijk}-\frac15(\delta_{ij}t_k+\delta_{ik}t_j+\delta_{jk}t_i).
\tag{2.4}
\]

To check the factor, contract \(j\) with \(k\). The three subtraction terms give \(t_i+t_i+3t_i=5t_i\), so the trace vanishes. The removed tensor is orthogonal to every STF3 tensor, because every contraction of a Kronecker delta with that tensor is a trace. Thus this is an orthogonal projection in the full Frobenius metric. The rank-two statement follows in the same way.

**Proposition 2.1 — component counts.** The real spaces of STF2 and STF3 tensors have dimensions five and seven.

**Proof.** A symmetric \(3\times3\) matrix has six entries, and its trace is one independent linear condition. A fully symmetric rank-three tensor has one entry for each unordered triple, hence \(\binom{5}{3}=10\) entries. Its trace is a vector, so there are three conditions. They are independent: the trace of \(\delta_{ij}w_k+\delta_{ik}w_j+\delta_{jk}w_i\) is \(5w_i\), and any trace vector can be obtained. The dimension is therefore \(10-3=7\). \(\square\)

### 2.2 Linear maps, kernels and images

For a linear map \(A:V\to W\), its kernel is \(\ker A=\{x:Ax=0\}\), and its image is \(\operatorname{Im}A=\{Ax:x\in V\}\). The rank is the dimension of the image. Two vectors have the same image precisely when their difference is in the kernel.

The rank–nullity identity is

\[
\dim V=\dim\ker A+\operatorname{rank}A.
\tag{2.5}
\]

To prove it, take a basis of the kernel and extend it to a basis of \(V\). The images of the added basis vectors span the image. They are independent, because any relation between them would put a combination of the added vectors in the original kernel basis. Counting the basis vectors gives Eq. (2.5).

The adjoint \(A^*\) is defined by \(\langle Ax,y\rangle_W=\langle x,A^*y\rangle_V\). With orthonormal real coordinates it is the transpose. With non-Euclidean coordinate metrics \(G_V,G_W\), it is instead \(G_V^{-1}A^TG_W\). This distinction will matter when real and imaginary harmonic coefficients are stored without their normalising factors.

A symmetric matrix \(H\) is positive semidefinite when \(x^THx\ge0\) for every \(x\); it is positive definite when the inequality is strict for nonzero \(x\). The notation \(H_1\preceq H_2\), called Loewner order, means that \(H_2-H_1\) is positive semidefinite. It compares quadratic forms, not individual matrix entries.

### 2.3 Spectral decomposition and singular values

**Lemma 2.2 — spectral decomposition.** A real symmetric matrix has an orthonormal basis of real eigenvectors.

**Proof.** The continuous function \(x^THx\) has a maximum on the unit sphere. At a maximiser \(u\), differentiation along every direction perpendicular to \(u\) gives \(z^THu=0\), so \(Hu\) is parallel to \(u\). Thus \(u\) is an eigenvector. Symmetry makes its orthogonal complement invariant: \(u^THz=(Hu)^Tz=0\). Repeat the argument on that lower-dimensional space. Induction completes the proof. \(\square\)

Apply the lemma to \(A^TA\). Its nonnegative eigenvalues are the squares of the singular values \(s_1(A)\ge s_2(A)\ge\cdots\ge0\). If \(v_i\) is an eigenvector with positive singular value, set \(u_i=Av_i/s_i\); these vectors are orthonormal. This gives

\[
A=U\Sigma V^T
\tag{2.6}
\]

after completing bases in the null spaces. This is the singular-value decomposition, or SVD. The operator norm is

\[
\|A\|_2=\sup_{\|x\|=1}\|Ax\|=s_1(A).
\tag{2.7}
\]

For an invertible square matrix, \(\kappa_2(A)=s_1(A)/s_n(A)\) is its relative condition number. A large value signals directions in which inversion can amplify relative errors. It is not itself an error estimate; the perturbation size and the quantities being compared still matter.

For later use, the singular values satisfy

\[
s_i(A)=\max_{\dim S=i}\ \min_{x\in S,\ \|x\|=1}\|Ax\|.
\tag{2.8}
\]

Indeed, the span of the first \(i\) right singular vectors achieves the value \(s_i\). Any \(i\)-dimensional subspace intersects the span of right singular vectors \(i,i+1,\ldots\) nontrivially, by the dimension count. A unit vector in that intersection has image norm at most \(s_i\). This proves the converse inequality.

**Proposition 2.3 — singular-value perturbation.** If \(A\) and \(E\) have the same shape, then

\[
|s_i(A+E)-s_i(A)|\le\|E\|_2.
\tag{2.9}
\]

**Proof.** For every unit vector, \(\|(A+E)x\|\le\|Ax\|+\|E\|_2\). Apply Eq. (2.8) to obtain the upper bound, and interchange \(A\) and \(A+E\) for the lower bound. \(\square\)

### 2.4 Projection, least squares and coordinates

Let the columns of \(U\) be an orthonormal basis of a subspace \(H\). Its orthogonal projector is \(P_H=UU^T\). We have \(P_H^2=P_H=P_H^T\), and every vector splits uniquely into

\[
x=P_Hx+(I-P_H)x,
\qquad P_Hx\perp(I-P_H)x.
\tag{2.10}
\]

The first term minimises \(\|x-h\|\) over \(h\in H\), because
\(\|x-h\|^2=\|(I-P_H)x\|^2+\|P_Hx-h\|^2\). This proof also explains why projections will appear in nuisance removal.

For a full-column-rank matrix \(A\), minimising \(\|Ax-y\|^2\) gives the normal equation \(A^TAx=A^Ty\). It has one solution since \(x^TA^TAx=\|Ax\|^2>0\) for nonzero \(x\). With positive weights \(W\), the same argument gives \(A^TWAx=A^TWy\). These equations define a least-squares fit; they do not say that the fitted model is physically correct.

A positive-definite matrix also has one upper-triangular positive-diagonal Cholesky factor \(B_+\) with \(B_+^TB_+=G\). Here is the construction rather than just its name. Split

\[
G=\begin{pmatrix}g_{11}&r^T\\r&G_2\end{pmatrix}.
\]

Set the first diagonal entry to \(\sqrt{g_{11}}>0\) and the rest of the first row to \(r^T/\sqrt{g_{11}}\). The remaining block must factor the Schur complement \(G_2-rr^T/g_{11}\). It is positive definite: insert \((-r^Ty/g_{11},y)\) into the quadratic form of \(G\). Repeat in lower dimension. The positive square root and triangular structure force every step, proving existence and uniqueness. No eigenvector sign choice is needed.

## 3. Describing the sky by harmonics and STF tensors

### 3.1 Spherical harmonics from polynomials

A homogeneous polynomial of degree \(\ell\) scales as \(P(tx)=t^\ell P(x)\). If its Euclidean Laplacian vanishes, it is harmonic. Restricted to the unit sphere, such polynomials form the angular multipole space of order \(\ell\). This explains why a quadratic STF tensor gives a quadrupole: for \(P(x)=Q_{ij}x_ix_j\), \(\nabla^2P=2Q_{ii}\). A cubic tensor gives an octupole because \(\nabla^2(O_{ijk}x_ix_jx_k)=6O_{iik}x_k\).

For explicit angular integration, use \(x=\cos\theta\). Define the Legendre polynomial by Rodrigues' formula,

\[
P_\ell(x)=\frac1{2^\ell\ell!}\frac{d^\ell}{dx^\ell}(x^2-1)^\ell,
\qquad
P_\ell^m(x)=(-1)^m(1-x^2)^{m/2}\frac{d^mP_\ell}{dx^m}.
\tag{3.1}
\]

For \(0\le m\le\ell\), let

\[
Y_{\ell m}(\theta,\varphi)
=\sqrt{\frac{2\ell+1}{4\pi}\frac{(\ell-m)!}{(\ell+m)!}}
P_\ell^m(\cos\theta)e^{im\varphi},
\qquad
Y_{\ell,-m}=(-1)^mY_{\ell m}^*.
\tag{3.2}
\]

The star is complex conjugation. The Fourier integral in \(\varphi\) makes different \(m\)'s orthogonal. For fixed \(m\), integration by parts in Rodrigues' formula, or the corresponding self-adjoint Legendre equation, gives

\[
\int_{-1}^1P_\ell^mP_k^m\,dx
=\frac{2(\ell+m)!}{(2\ell+1)(\ell-m)!}\,\delta_{\ell k}.
\tag{3.3}
\]

For clarity, the norm in Eq. (3.3) follows by integrating the \(m\) derivatives off one factor. Repeated differentiation of the Legendre equation yields
\(d^m[(1-x^2)^mP_\ell^{(m)}]/dx^m=(-1)^m(\ell+m)!P_\ell/(\ell-m)!\). Boundary terms vanish because of the powers of \(1-x^2\). Rodrigues' formula similarly gives \(\int P_\ell^2dx=2/(2\ell+1)\). Combining these two identities proves the displayed norm. For \(\ell\ne k\), subtract the two self-adjoint equations; the boundary term vanishes and the distinct eigenvalues \(\ell(\ell+1)\) and \(k(k+1)\) force the cross integral to zero. Thus \(\int Y_{\ell m}^*Y_{kn}\,d\Omega=\delta_{\ell k}\delta_{mn}\).

We need only finite harmonic bands in the constructions below. No convergence theorem for an arbitrary infinite sky expansion is being used in a finite matrix proof.

### 3.2 Real temperature and stored coordinates

Write a finite multipole as \(T_\ell(n)=\sum_m a_{\ell m}Y_{\ell m}(n)\). Reality implies

\[
a_{\ell,-m}=(-1)^m a_{\ell m}^*.
\tag{3.4}
\]

This follows by conjugating the expansion, substituting Eq. (3.2), and equating coefficients in an orthonormal basis. For \(m>0\), introduce the real basis \(\sqrt2\Re Y_{\ell m}\), \(\sqrt2\Im Y_{\ell m}\). Its coefficients are

\[
c_{\ell0}=a_{\ell0},\qquad
c_{\ell m,c}=\sqrt2\Re a_{\ell m},\qquad
c_{\ell m,s}=-\sqrt2\Im a_{\ell m}.
\tag{3.5}
\]

The minus sign is not optional under this sine-basis convention: the pair of complex terms is \(2\Re(a_{\ell m}Y_{\ell m})\).

**Proposition 3.1 — real-carrier isometry.** If
\(C_\ell=(2\ell+1)^{-1}\sum_m|a_{\ell m}|^2\), then

\[
\int_{S^2}T_\ell^2\,d\Omega
=\|c_\ell\|_2^2
=\sum_m|a_{\ell m}|^2
=(2\ell+1)C_\ell.
\tag{3.6}
\]

**Proof.** Orthogonality eliminates all unequal harmonic pairs in the integral. For each positive \(m\), the two equal complex moduli contribute \(2[(\Re a)^2+(\Im a)^2]\), precisely the squared norm of the two real coordinates in Eq. (3.5). \(\square\)

Here \(C_\ell\) is a power computed from a specified sky, not automatically an ensemble expectation. It has temperature-squared units. A probabilistic model for sky realisations is a separate ingredient.

If we instead store \(r=(a_{\ell0},\Re a_{\ell1},\Im a_{\ell1},\ldots)\), its metric is

\[
G_\ell=\operatorname{diag}(1,2,2,\ldots),\qquad
c=D_\ell r,\qquad D_\ell^TD_\ell=G_\ell.
\tag{3.7}
\]

The entries of \(D_\ell\) are \(1\) and repeated pairs \((\sqrt2,-\sqrt2)\). A rank is unchanged by this invertible adapter; a Euclidean singular value need not be. Before comparing numerical sensitivities, we must therefore specify the metric as well as the coordinate list.

### 3.3 Angular moments and the normalisation of Q and O

The tensor representation is

\[
T_2(n)=Q_{ij}n_in_j,\qquad
T_3(n)=O_{ijk}n_in_jn_k,
\tag{3.8}
\]

with \(Q\) STF2 and \(O\) STF3. Their independent component counts agree with \(2\ell+1\) at \(\ell=2,3\). We now derive the conversion factors instead of relying on a table.

**Lemma 3.2 — isotropic angular moments.** Odd products of components of \(n\) integrate to zero. For an even product,

\[
\int_{S^2} n_{i_1}\cdots n_{i_{2r}}\,d\Omega
=\frac{4\pi}{(2r+1)!!}
\sum_{\text{pairings}}\delta_{i_{a_1}i_{b_1}}\cdots
\delta_{i_{a_r}i_{b_r}}.
\tag{3.9}
\]

The double factorial is \((2r+1)!!=(2r+1)(2r-1)\cdots3\cdot1\), and the sum contains each pairing of the \(2r\) index positions once.

**Proof.** Oddness under \(n\mapsto-n\) gives the first statement. Contract the even integral with \(x_{i_1}\cdots x_{i_{2r}}\). Rotate \(x\) to the polar axis; the integral becomes
\(2\pi\|x\|^{2r}\int_{-1}^1\mu^{2r}d\mu=4\pi\|x\|^{2r}/(2r+1)\).
There are \((2r-1)!!\) pairings, each giving \(\|x\|^{2r}\). The proposed coefficient is forced. Equality of the resulting polynomials for every \(x\) gives equality of their symmetric coefficient tensors. \(\square\)

**Proposition 3.3 — harmonic-to-STF norm conversion.** With Eq. (3.8),

\[
\boxed{Q:Q=\frac{15}{8\pi}\|c_2\|_2^2
=\frac{75}{8\pi}C_2},\qquad
\boxed{O:O=\frac{35}{8\pi}\|c_3\|_2^2
=\frac{245}{8\pi}C_3}.
\tag{3.10}
\]

**Proof.** In the fourth angular moment, contracting with \(Q_{ij}Q_{kl}\) kills the pairing that traces either tensor. The remaining two pairings each give \(Q:Q\). Thus \(\int T_2^2d\Omega=(8\pi/15)Q:Q\). In the sixth angular moment, any pairing internal to either STF3 tensor gives a trace and vanishes. The remaining \(3!=6\) pairings connect every index across the two tensors, giving \(\int T_3^2d\Omega=(8\pi/35)O:O\). Combine these expressions with Eq. (3.6). \(\square\)

The tensors themselves can be recovered directly from angular integrals,

\[
Q_{ij}=\frac{15}{8\pi}\int T_2(n)n_{\langle ij\rangle}\,d\Omega,
\qquad
O_{ijk}=\frac{35}{8\pi}\int T_3(n)n_{\langle ijk\rangle}\,d\Omega.
\tag{3.11}
\]

To verify either formula, substitute Eq. (3.8), use Eq. (3.9), and retain only cross-pairings. This proves uniqueness as well as the normalisation. Harmonic coefficients and STF tensors are two complete coordinate descriptions of the same angular sector.

Before moving on, note what has not appeared: no Hubble rate, matter velocity or spacetime shear entered this construction. We have translated the observable temperature field into tensor language. We have not yet translated it into cosmological kinematics.
