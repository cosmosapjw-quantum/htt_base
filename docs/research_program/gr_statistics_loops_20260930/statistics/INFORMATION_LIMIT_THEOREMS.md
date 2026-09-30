# Morphology retained and lost: exact information limits for local cosmography

Date: 2026-09-30. Proposer: `jcap_information_limits`. Status: **DERIVED CANDIDATE; independent decision pending**. Contract: `../RESEARCH_CONTRACT.json`; conventions and local optical image are those of `../gr/OPTICAL_THEOREMS.md`. This is an analytical statistical follow-up, with no catalogue fit, scientific numerical suite, or claim of established priority. The two results below concern different observation experiments and must not be conflated.

## 1. Optical data and the meaning of a powers-only summary

Use signature \((-+++)\), a fixed observer \(o=(1,0,0,0)\), past sourceward ray \(K=(-1,n)\), and \(U=cu\). Write the ideal local data as
\[
Z(n)=\gamma+v\cdot n,\qquad
H_{\rm sky}(n)=m+p\cdot n+T_{ij}n^in^j,
\quad T=T^\top,\quad \operatorname{tr}T=0.
\]
Here \(\gamma^2-|v|^2=1\), \(\gamma\ge1\), and \(H_{\rm sky}=c\,\partial z/\partial d_A|_0\). The local inverse is
\[
u=(\gamma,v),\quad
S=\begin{pmatrix}m&-p^\top/2\\-p/2&T\end{pmatrix},\quad
q=S(u,u),\quad B=S+qg,\quad A_a=2cB_{ab}u^b.
\tag{I1}
\]
Every such tuple is realizable as a smooth test-source first jet in a fixed smooth metric, including Minkowski. Pointwise zero acceleration is equivalent to \(Bu=0\). A zero-acceleration compatible jet can also be realized by a locally geodesic congruence, as proved in the optical note.

Define the separate-sector powers
\[
\mathcal P=(\gamma^2,|v|^2,m^2,|p|^2,\operatorname{tr}T^2).
\tag{I2}
\]
The standard full-sky harmonic powers differ only by known positive convention factors. With sphere-average normalization, sector contributions to the squared sky norms are \(\gamma^2, |v|^2/3\) and \(m^2,|p|^2/3,2\operatorname{tr}T^2/15\). A powers-only summary is any measurable function of these five separate quantities, with any fixed calibrations. It discards relative orientations between sectors. Its invariance group is larger than the physical common sky rotation group.

## 2. Exact geodesic/accelerated alias under separate-sector powers

**Theorem I — physically admissible equal-power pair.** Fix a rate \(H>0\) and
\[
u=(5/4,3/4,0,0),\qquad B=H(g+u_\flat\otimes u_\flat).
\]
The corresponding coefficients are
\[
Z=5/4+(3/4)n_x,\quad m=7H/4,\quad
p=(15H/8,0,0),\quad
T=\operatorname{diag}(3H/8,-3H/16,-3H/16).
\tag{I3}
\]
Replace only \(p\) by \(p'=(0,15H/8,0)\), leaving the intercept, monopole, and quadrupole fixed. Both tuples are admissible, have identical \(\mathcal P\), and are distinguishable by their full coefficients. The first has \(A=0\); the second has \(A\ne0\).

**Proof.** Direct contraction of
\[
B=H\begin{pmatrix}
9/16&-15/16&0&0\\
-15/16&25/16&0&0\\
0&0&1&0\\0&0&0&1
\end{pmatrix}
\]
with \(K=(-1,n)\), followed by removal of the spatial trace, gives (I3). Also \(Bu=0\). For the rotated tuple,
\[
q'=377H/128,\qquad
B'=\frac{H}{128}
\begin{pmatrix}
-153&0&-120&0\\
0&425&0&0\\
-120&0&353&0\\
0&0&0&353
\end{pmatrix},
\tag{I4}
\]
and hence
\[
b'=B'u=\frac H{512}(-765,1275,-600,0),\qquad
b'\cdot u=0,\qquad b'_ab'{}^a=\frac{87525}{16384}H^2>0.
\tag{I5}
\]
Its acceleration is \(2cb'\). The image theorem supplies its normalization-compatible derivative and a smooth local realization. The equal powers are exactly
\[
\mathcal P=\left(\frac{25}{16},\frac9{16},\frac{49H^2}{16},
\frac{225H^2}{64},\frac{27H^2}{128}\right).
\tag{I6}
\]
This proves all assertions. \(\square\)

This is more than a global coordinate rotation: the intercept dipole and quadrupole stay fixed while the slope dipole moves. For example the common-rotation invariant \(v\cdot p\) is \(45H/32\) in (I3), but zero in the primed tuple. Even the within-slope contraction \(p^\top Tp\) differs: \(675H^3/512\) versus \(-675H^3/1024\).

**Precise normalization consequence.** Every norm or percentage computed solely from the separate powers in (I2), with a normalizer also determined by those powers, agrees exactly between the two models. This includes a proposed MES percentage only if its numerator and denominator obey that separate-sector invariance. No claim is made for an unspecified MES definition or any of the user's existing named invariants. In particular, the norm of the *combined* radial field \(Z+rH_{\rm sky}/c\) generally differs: its dipole power contains \(2r\,v\cdot p/c\). Calling such a combined quantity a radial norm does not make it a function of (I2).

The constructions are local kinematic source fields in the same chosen metric. They are not established as two solutions of the same Einstein–matter closure. Conserved positive-density dust excludes the accelerated member. The theorem therefore cannot be applied inside a dust-only model class without changing its hypotheses.

## 3. A scalar repair: retain the contractions needed for geodesicity

The loss arises from the selected invariances of the summary, not from its being scalar. Set \(t_a=S_{ab}u^b\), \(q=S(u,u)\), and define a new diagnostic named \(J_{\rm geo}\), unrelated to any preexisting \(G\), \(G_F\), \(Q\), \(F\), or \(\Pi\):
\[
\boxed{J_{\rm geo}=g^{ab}t_at_b+q^2
=g^{ab}(Bu)_a(Bu)_b=\frac{A_aA^a}{4c^2}\ge0.}
\tag{I7}
\]
On the admissible image, \(J_{\rm geo}=0\) if and only if \(A=0\). Indeed \(b=t+qu_\flat\), \(t\cdot u=q\), \(u^2=-1\), so \(b^2=t^2+q^2\). Moreover \(b\cdot u=0\); the rest space of a timelike vector is positive definite. This excludes a nonzero null vector as a spurious zero of (I7).

An explicit sky-coordinate form is
\[
q=m\gamma^2-\gamma p\cdot v+v^\top Tv,\qquad
w=Tv+qv-\frac\gamma2p,
\]
\[
\boxed{J_{\rm geo}=|w|^2-\frac{(v\cdot w)^2}{\gamma^2}.}
\tag{I8}
\]
Since \(b_i=w_i\) and \(b_0=-v\cdot w/\gamma\), (I8) follows. Its quadratic form has eigenvalues \(1,1,1/\gamma^2\), so it is nonnegative without diagonalizing \(T\). Expanding (I8) uses \(p\cdot v\), \(v^\top Tv\), \(p^\top Tv\), and \(v^\top T^2v\), together with powers and the signed monopole. These contractions preserve exactly the relative-orientation information erased by (I2). They are sufficient to evaluate this one property, not asserted sufficient to reconstruct the whole field.

For the explicit pair, \(J_{\rm geo}=0\) and \(J'_{\rm geo}=87525H^2/16384\). The formula is exact for admissible coefficients. Noise-biased plug-in estimates and a calibrated test of the boundary \(J_{\rm geo}=0\) need their own inference theory; no chi-square calibration is asserted here.

The scalar is invariant under a common sky coordinate rotation; (I7) is also a tensor scalar once the metric and physical source field are specified. Neither statement removes the metric normalization, calibrated distance/rate scale, or the fixed observer from the information contract. No invariance under arbitrary causal-conformal changes of the metric and units is claimed.

## 4. Exact statistical experiment: power equals size after compression

Choose orthonormal real coordinates within each of the five sectors (using the Euclidean norm for vectors and the Frobenius norm on the five-dimensional trace-free tensors). Observe independent Gaussian blocks
\[
X_j\sim N(\mu_j,\sigma_j^2 I_{d_j}),\quad
d_j=(1,3,1,3,5),\quad \sigma_j>0.
\tag{I9}
\]
The two means are the coefficient tuples in Theorem I. Define the observed separate powers \(P_j=|X_j|^2\).

**Theorem II — equality of compressed laws and strict full-data separation.** The joint distribution of \((P_j)_j\) is exactly identical under the two means in Theorem I. Every powers-only randomized test has rejection probability under the accelerated alternative equal to its rejection probability under the geodesic member. In particular, any such test with size at most \(\alpha\) over a null class containing the latter has power at most \(\alpha\) against this alternative. Nevertheless the full Gaussian experiments have
\[
D_{\rm KL}(P_\mu\Vert P_{\mu'})
=\frac12\sum_j\frac{|\mu_j-\mu'_j|^2}{\sigma_j^2}
=\frac{225H^2}{64\sigma_p^2}>0.
\tag{I10}
\]

**Proof.** For each block there is an orthogonal \(R_j\) with \(R_j\mu_j=\mu'_j\); all but the slope-dipole block may be the identity. Isotropic Gaussian noise is invariant under \(R_j\), and \(|R_jX_j|^2=|X_j|^2\). Block independence gives equality of the joint laws. The rejection expectation of every measurable randomized function of these powers consequently agrees. The Gaussian equal-covariance divergence is the displayed quadratic expression; only the slope dipole changes and its squared difference is \(2(15H/8)^2\), giving (I10). \(\square\)

For a direct consistency check, let \(\Delta=\mu'_p-\mu_p\). Under the two models, \(\Delta\cdot[X_p-(\mu_p+\mu'_p)/2]\) has means \(\mp|\Delta|^2/2\) and common variance \(\sigma_p^2|\Delta|^2\). Thresholding at zero gives error \(\Phi(-|\Delta|/(2\sigma_p))\to0\) as \(\sigma_p\to0\). This is a consistent simple-versus-simple full-data test; uniform consistency over every geodesic/accelerated boundary alternative is not claimed.

The Gaussian radial-invariance fact is standard. Its application to the explicit GR-admissible zero/nonzero-acceleration pair is the physical contribution investigated here. Block independence and isotropic covariance are hypotheses of this exact benchmark, not properties established for real catalogue estimates. Masks, angular sampling, anisotropic covariance, cross-block errors, priors, and nonlinear fitting can invalidate the equal-law statement. Whitening does not automatically preserve the meaning of physical sector powers. Full orientation-aware scalar contractions, including (I7), are outside the powers-only sigma-algebra. This theorem neither says that all scalar statistics fail nor that every raw survey has zero distinguishing information.

## 5. A different limitation: an unobserved inner ball

Here the observation is the full exterior redshift–area-distance relation, not local coefficients or their powers. Fix Minkowski spacetime, the same observer \(o=(1,0,0,0)\) at \(p=(0,0,0,0)\), and a radial cutout \(a>0\). A past null ray is \(x(r)=(-r,rn)\), and \(d_A=r\) exactly. The receiver is held fixed independently of the emitter congruence at \(p\).

**Theorem III — smooth source-value ambiguity with a fixed remainder bound.** For every \(M>0\) and \(a>0\), there are two smooth future unit test-source fields such that:

1. their exact exterior data agree for every direction and every \(r\ge a\): \(1+z=1\), \(d_A=r\);
2. each obeys \(|\partial_r^2(1+z)|\le M\) along all these rays, including the unobserved segment \(0\le r<a\);
3. their source values at \(p\) differ by rapidity
   \[
   \delta=\frac1{25}\min\{1,Ma^2\}>0,
   \tag{I11}
   \]
   and their intercept dipoles differ by \(\sinh\delta\,e_x\).

**Construction and proof.** Let \(F(t)=1-10t^3+15t^4-6t^5\) on \([0,1]\). Use the \(C^2\) cutoff \(q_0(r)=1\) for \(r\le a/4\), \(q_0(r)=F(2r/a-1/2)\) on \([a/4,3a/4]\), and \(q_0=0\) afterwards. It is defined on the whole real line. Since
\[
\max_{[0,1]}|F'|=15/8,\qquad
\max_{[0,1]}|F''|=10/\sqrt3,
\]
we have \(\|q'_0\|_\infty\le15/(4a)\) and \(\|q''_0\|_\infty\le40/(\sqrt3a^2)\). Convolve with any nonnegative unit-integral \(C^\infty\) mollifier supported in \([-a/8,a/8]\). The resulting \(q\) is smooth, remains in \([0,1]\), is one on \(r\le a/8\), zero on \(r\ge7a/8\), and has the same derivative bounds. The function \(q(|\mathbf x|)\) is smooth even at \(\mathbf x=0\), because it is constant nearby.

Take \(u_0=o\), and take the stationary field
\[
u_1(t,\mathbf x)=\big(\cosh\chi,\sinh\chi,0,0\big),\qquad
\chi=\delta q(|\mathbf x|).
\tag{I12}
\]
It is future unit everywhere. Along a ray,
\[
Z_1(r,n)=\cosh\chi(r)+n_x\sinh\chi(r),\qquad
|Z_1''|\le e^\delta\big(|\chi''|+|\chi'|^2\big)
\le\frac{e^\delta}{a^2}
\left(\frac{40}{\sqrt3}\delta+\frac{225}{16}\delta^2\right).
\tag{I13}
\]
Write \(x=Ma^2\), \(s=\min(1,x)\). With \(\delta=s/25\), \(s^2\le s\le x\), the last bound divided by \(M\) is at most
\[
e^{1/25}\left(\frac8{5\sqrt3}+\frac9{400}\right)<1.
\tag{I14}
\]
One entirely rational certificate is \(e^{1/25}<25/24\) and \(\sqrt3>12/7\), which bound the expression by \((25/24)(14/15+9/400)=1147/1152<1\). Thus both fields meet the same prescribed \(M\). Outside the support they equal \(o\), giving identical endpoint redshifts. Flat optical propagation gives identical area distances. At the origin \(u_1=(\cosh\delta,\sinh\delta,0,0)\), which proves (I11). \(\square\)

Both fields are constant near \(p\), hence their local slopes vanish; this theorem proves source-value/intercept ambiguity, not a slope ambiguity. The second field is generally accelerated in its transition region. It is a test congruence, not an Einstein–dust solution. If the receiver were required to coincide with the varying source velocity at \(p\), the denominator of the exterior redshift would change and this construction would not establish equality. The fixed-observer condition is essential.

The construction shows a positive identification floor of order \(Ma^2\) for small \(Ma^2\), with a deliberately conservative constant. It is not an assertion of minimax sharpness, nor a universal conversion from a redshift cut to a radius cut. The metric is held fixed and all allowed exterior optical data already agree exactly, so collecting more such data cannot determine the interior continuation in this class. The bounded-curvature condition of the finite-distance note holds here with \(K_c=0\); its Taylor remainder upper bound alone does not remove this ambiguity.

## 6. Finite-sample consequence of identical exterior laws

Let \(\theta_0,\theta_1\) denote either the source values, or the intercept dipoles, of Theorem III, with distance \(d(\theta_0,\theta_1)=D>0\). Suppose the measured-data model, sampling, and noise depend only on their common exterior data, and any nuisance variables have the same distribution. Then the complete data laws are identical, for every sample size. This observation-kernel condition is necessary: the theorem does not include any auxiliary observable that independently probes the interior.

**Corollary — confidence-set floor.** If a random set \(C\) has coverage at least \(1-\alpha\) at each of these two parameter points, \(0\le\alpha<1/2\), then under their common data law
\[
\mathbb P\{\operatorname{diam}_d C\ge D\}\ge1-2\alpha,
\qquad
\mathbb E[\operatorname{diam}_d C]\ge(1-2\alpha)D.
\tag{I15}
\]
Indeed the union bound gives probability at least \(1-2\alpha\) that both points are in \(C\), where its diameter is at least \(D\). For intercept dipoles \(D=\sinh\delta\ge\delta\). For source rapidity distance \(D=\delta\). Likewise every point estimator satisfies \(\max_i\mathbb E_i d(\widehat\theta,\theta_i)\ge D/2\), by the triangle inequality under the common law. These elementary two-point bounds are standard identification/optimal-recovery logic, not a new statistical principle.

## 7. Literature bridge, scientific meaning, and remaining gate

The retrieved primary paper [Kalbouneh et al., arXiv:2510.02510v1](https://arxiv.org/html/2510.02510v1), §2.1 and §6.3, imposes a lower redshift cut at 0.01 and discusses the breakdown of the fluid approximation on smaller scales. Its §4 and §4.2 retain harmonic coefficient vectors and examine alignment. These are contextual motivations for separating endpoint identification, finite-distance extrapolation, and angular morphology. They are **not** evidence that its actual analysis discards all orientations; this note makes no such allegation. Its estimator, observable, and model class differ from the ideal experiment in Theorem II. The masked catalogue covariance is not assumed isotropic here. The paper was inspected on 2026-09-30; exact stable section locators are given above.

The supplied pointer [arXiv:2507.01095v1](https://arxiv.org/html/2507.01095v1) resolves to *A theoretical prediction for the dipole in nearby distances using cosmography*. It is not cited as a convergence theorem: only its identity was checked in this bounded follow-up. A claimed convergence prior needs a correct, separately audited source locator.

| Claim | Evidence state | Novelty and scope |
|---|---|---|
| Explicit equal-power geodesic/accelerated pair, (I3)–(I6) | Derived, exact arithmetic shown | Candidate physical counterexample; priority unestablished; local test sources |
| Exact scalar geodesicity certificate, (I7)–(I8) | Derived from the local optical inverse | Useful orientation-preserving repair; novelty unestablished |
| Identical Gaussian sector-power laws and positive full KL | Derived application of standard Gaussian rotational invariance | Benchmark, not real-survey calibration |
| Smooth inner-cutout construction with common fixed \(M\) | Derived; auxiliary independent arithmetic check requested during drafting | Kinematic interior-continuation obstruction, not matter closure |
| Confidence-set and estimator floors | Derived elementary two-point argument | Standard statistical principle applied to the physical pair |
| JCAP-level original contribution, real-catalogue validity, minimax optimality | Unresolved | Requires focused prior-art review and a specified observational model |

The completed proposer target is the explicit information-loss mechanism together with its scalar repair, and the separate operational limit from an inner cutout. Independent decision review remains required before promotion. No actual dataset, numerical suite, repository change, publication-ready statistical calibration, or universal impossibility claim has been produced.
