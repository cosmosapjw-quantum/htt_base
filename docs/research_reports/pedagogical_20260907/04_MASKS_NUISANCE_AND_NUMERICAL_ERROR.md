# Part VI. What changes after observing and processing the sky?

## 10. Masking, fitting and unobserved angular structure

### 10.1 The order of operations is part of the model

A physical sky is not usually analysed by taking exact integrals over the whole sphere. Some directions may be downweighted, a beam smooths the signal, a finite pixelisation samples it, and a fitting procedure returns a selected set of coefficients. These operations define a new observable. We should derive its response rather than insert the full-sky response after processing.

We use the following order: begin with a positive thermodynamic-temperature sky, change the observer, apply the source beam and pixel-window transfer, synthesise the sampled sky, perform a weighted simultaneous fit through multipole five, apply the declared post-fit commonisation, and retain multipoles two through five. A transfer factor is the coefficient multiplying a harmonic mode under a specified linear smoothing operation. Commonisation here means converting the fitted response to the chosen common source/target smoothing convention; it must not be mistaken for a different order of the physical boost and smoothing.

The order matters even for simple diagonal transfer. If a transfer multiplies multipole \(\ell\) by \(b_\ell\), while the boost takes part of that multipole to \(\ell+1\), transfer after boost multiplies that part by \(b_{\ell+1}\). Transfer before boost multiplies it by \(b_\ell\). They agree only under an additional condition on the factors or the signal. Mask-induced mode mixing and matrix-valued responses for general filtering provide the relevant observational background. [@MASTER_2002; @LEUNG_2022]

### 10.2 The weighted fit and its structural monopole null

Let \(Y_{p\alpha}\) evaluate the fitted real spherical harmonic \(\alpha\) at pixel \(p\), and let \(W\) be a diagonal matrix of nonnegative pixel weights. Assume the weighted columns are linearly independent. The fitted coefficient vector for sampled data \(t\) is

\[
\widehat a=(Y^TWY)^{-1}Y^TWt.
\tag{10.1}
\]

This follows by differentiating \((t-Ya)^TW(t-Ya)\); the positive normal matrix makes the minimiser unique. The positivity requirement is a property of the particular mask and fitting grid. A rank-deficient design is not repaired by calling its inverse an ordinary inverse.

**Proposition 10.1 — a fitted dipole does not become a retained quadrupole in the exact fit.** If the simultaneous model includes the monopole and all dipoles and the retained output begins at \(\ell=2\), the first-order response to a physical constant monopole is zero in the retained output.

**Proof.** Section 9 gives \(\delta_\beta T_0=T_0\beta\cdot n\), a dipole. Its sampled vector is exactly \(Yd\) for a coefficient vector \(d\) supported on the fitted dipole columns. Substituting into Eq. (10.1) gives \(\widehat a=d\), independent of nonuniform weights. The retention operator removes those columns. Diagonal source/target smoothing preserves the dipole sector and does not alter this conclusion. \(\square\)

A separately implemented transform or iterative solve can nevertheless produce a small numerical leakage. Such leakage is an implementation residual, not a new physical monopole response. The proposition refers to the exact declared linear fit with consistent samples.

### 10.3 Source and output dimensions

The low-source coordinate is

\[
s_{\rm low}=(T_0,r_1,\ldots,r_6)\in\mathbb R^{49},
\qquad a_{00}=\sqrt{4\pi}\,T_0.
\tag{10.2}
\]

There are \(\sum_{\ell=1}^{6}(2\ell+1)=48\) anisotropy coordinates and one physical monopole coordinate. Retaining \(\ell=2,3,4,5\) gives \(5+7+9+11=32\) outputs. The first-order response coefficient is

\[
J_{i\alpha A}
=\left.\frac{\partial^2y_\alpha}
{\partial\beta_i\partial s_A}\right|_{\beta=0},
\qquad J\in\mathbb R^{3\times32\times49}.
\tag{10.3}
\]

All entries are dimensionless when source and output use the same temperature unit. For one unit boost direction \(\widehat b\), contraction with \(\widehat b_i\) and removal of the structural monopole column give a matrix \(J_{\widehat b}\) of shape \(32\times48\).

The source and output metrics in raw real coordinates are

\[
G_S=\operatorname{diag}(4\pi,G_1,\ldots,G_6),\qquad
G_R=\operatorname{diag}(G_2,G_3,G_4,G_5).
\tag{10.4}
\]

The monopole factor follows from \(a_{00}=\sqrt{4\pi}T_0\). Replacing coordinates by \(G^{1/2}\) times those coordinates converts their norm to the Euclidean norm. Singular-value statements must use the resulting transformed response, or state the original metrics explicitly. Rank is invariant under these invertible coordinate changes, while singular values are metric dependent.

### 10.4 Nuisance directions and quotient information

Higher source multipoles can contribute to the same retained output after masking and fitting. For a cutoff \(L\ge7\), let

\[
K_{\widehat b}^{\rm hi}(L):
\bigoplus_{\ell=7}^{L}V_\ell\longrightarrow\mathbb R^{32},
\qquad
H_{\widehat b}(L)=\operatorname{Im}K_{\widehat b}^{\rm hi}(L),
\tag{10.5}
\]

where \(V_\ell\) is the \((2\ell+1)\)-dimensional real harmonic space. The number of high-source coordinates is

\[
d_H(L)=\sum_{\ell=7}^{L}(2\ell+1)
=(L+1)^2-49=(L-6)(L+8).
\tag{10.6}
\]

Here the high-source vector is an unrestricted deterministic nuisance. If two low-source responses differ by an element of \(H\), an appropriate nuisance change can make their total outputs coincide. Thus the retained information is an equivalence class modulo \(H\). The orthogonal representative of that class is

\[
J_{\rm surv}(L)=(I-P_H)J_{\widehat b}.
\tag{10.7}
\]

The subscript indicates the part surviving nuisance quotienting; it does not name a new observed tensor.

**Theorem 10.2 — quotient-rank identity.** For any compatible real matrices \(K,J\),

\[
\boxed{\operatorname{rank}[(I-P_{\operatorname{Im}K})J]
=\operatorname{rank}[K\ J]-\operatorname{rank}K.}
\tag{10.8}
\]

**Proof.** Let \(V=\operatorname{Im}K+\operatorname{Im}J\). Restrict the projection \(I-P_{\operatorname{Im}K}\) to \(V\). Its kernel is exactly \(\operatorname{Im}K\), since a vector is projected to zero precisely when it lies in that subspace. Its image is the image of the projected \(J\). Rank–nullity on \(V\) gives Eq. (10.8), since \(\dim V=\operatorname{rank}[K\ J]\). \(\square\)

**Corollary 10.3 — nesting cannot restore information already removed.** Appending higher-source columns enlarges \(H(L)\). Once \(\operatorname{Im}J\subseteq H(L)\), the projected response remains zero at every larger cutoff.

**Proof.** Each earlier column remains an available nuisance column. The inclusion therefore persists. Projection onto the orthogonal complement annihilates every vector in that inclusion. \(\square\)

This result concerns an unrestricted nuisance image. An amplitude bound, covariance model or prior can assign very different costs to different nuisance vectors; it defines a different inference problem. A vanishing deterministic quotient is not a statement that every statistical analysis has zero information.

## 11. A continuum example with an internal rank certificate

### 11.1 The model and why its normal matrix is invertible

We now use exact angular integrals, identity transfer, and the piecewise axisymmetric weight

\[
w(x)=
\begin{cases}
0,&-1\le x\le-3/4,\\
1/2+2x/3,&-3/4<x<3/4,\\
1,&3/4\le x\le1,
\end{cases}
\qquad x=\cos\theta.
\tag{11.1}
\]

Fit harmonics through \(\ell=5\), retain \(\ell=2\) through 5, and consider source multipoles 7 through \(L\). Let \(\alpha\) label the fitted harmonics and \(p\) the source harmonics. With the generator of Eq. (9.5), define

\[
N_{\alpha\beta}=\int_{S^2}wY_\alpha^*Y_\beta\,d\Omega,
\qquad
R_{\alpha p}^{(\widehat b)}=\int_{S^2}wY_\alpha^*\mathcal B_{\widehat b}Y_p\,d\Omega,
\tag{11.2}
\]

\[
K_{\widehat b}^{\rm cont}(L)=P_{2:5}N^{-1}R_{\widehat b}^{7:L}.
\tag{11.3}
\]

The symbol \(\mathcal B_{\widehat b}\) here acts on angular functions by Eq. (9.5); it is not the finite-dimensional tensor map \(B_Q\). The selection matrix \(P_{2:5}\) keeps the fitted rows in the stated range.

To see that \(N\) is positive definite, take a finite harmonic combination \(f\). Its quadratic form is \(\int w|f|^2d\Omega\). If it vanishes, continuity implies that \(f\) vanishes on the open cap where \(w>0\). A finite harmonic combination is real analytic on the sphere: in local coordinates it is a finite combination of the polynomial restrictions introduced in Section 3. A real-analytic function zero on an open neighbourhood has all Taylor coefficients zero there; propagating overlapping Taylor neighbourhoods on the connected sphere makes it identically zero. Harmonic orthogonality then makes every coefficient zero. This proves positivity for a nonzero coefficient vector. It is a continuum argument, not an assumption about a finite pixel grid.

### 11.2 Reducing the axial calculation to polynomial integrals

For \(\widehat b=\widehat z\), Eq. (9.5) becomes

\[
\mathcal B_zf=xf-(1-x^2)\partial_xf.
\tag{11.4}
\]

Define
\(a_{\ell m}=\sqrt{(\ell^2-m^2)/[(2\ell-1)(2\ell+1)]}\).
The associated Legendre recurrences imply

\[
xY_{\ell m}=a_{\ell+1,m}Y_{\ell+1,m}+a_{\ell m}Y_{\ell-1,m},
\]

\[
(1-x^2)\partial_xY_{\ell m}
=-\ell a_{\ell+1,m}Y_{\ell+1,m}
+(\ell+1)a_{\ell m}Y_{\ell-1,m}.
\tag{11.5}
\]

A direct derivation of the needed polynomial identities is given in Appendix A. Subtracting Eq. (11.5) from its first line as in Eq. (11.4) gives

\[
\boxed{\mathcal B_zY_{\ell m}
=-\ell a_{\ell m}Y_{\ell-1,m}
+(\ell+1)a_{\ell+1,m}Y_{\ell+1,m}.}
\tag{11.6}
\]

The axial boost preserves \(m\). Since the mask is also independent of \(\varphi\), the Fourier integral makes the normal and response matrices block diagonal in \(m\).

For \(0\le m\le5\), define the normalised overlap

\[
I_m(\ell,k)=\frac12
\sqrt{\frac{(2\ell+1)(2k+1)(\ell-m)!(k-m)!}
{(\ell+m)!(k+m)!}}
\int_{-1}^1 w(x)(1-x^2)^mP_\ell^{(m)}(x)P_k^{(m)}(x)\,dx.
\tag{11.7}
\]

It is zero when either degree is smaller than \(m\). The two signs in associated Legendre functions cancel. The factor in front includes the azimuthal integral of the normalised harmonics.

The block equations are now fully specified:

\[
(N_m)_{\ell k}=I_m(\ell,k),\qquad \ell,k=m,\ldots,5,
\]

\[
(R_m)_{\ell p}
=-p a_{pm}I_m(\ell,p-1)+(p+1)a_{p+1,m}I_m(\ell,p+1),
\qquad p=7,\ldots,L,
\tag{11.8}
\]

and \(K_m\) consists of rows \(\ell\ge2\) of \(N_m^{-1}R_m\). Every integral is a polynomial integral with rational endpoints, followed by known harmonic normalisations. The complete finite recipe and exact minor values are printed in Appendix B; no external matrix file is needed to define the calculation.

### 11.3 Exact axial full row rank

**Theorem 11.1 — axial continuum rank at the stated cutoff.** The operator in Eq. (11.3), with Eqs. (11.1) and (11.4), has real row rank 32 at \(L=12\).

**Proof.** The retained row counts in the \(m=0,1,2,3,4,5\) blocks are \((4,4,4,3,2,1)\). The exact tabulation in Appendix B gives a nonzero determinant square for the square minor using the first corresponding number of source columns in every block. The tabulation is specified by Rodrigues' coefficients, elementary power integrals, the finite matrices in Eq. (11.8), and the determinant formula. All its numerators and denominators are strictly positive integers. Hence each block has at least its full row count as rank, and cannot have a larger rank because it has no further rows.

For a real field, the \(m=0\) block occurs once, while each positive \(m\) contributes two identical-rank real blocks from the real and imaginary coordinates. The total is
\(4+2(4+4+3+2+1)=32\). This is all retained dimensions. \(\square\)

The proof is an exact finite algebraic certificate, not a singular-value threshold argument. The integer fractions are reproduced from the retained exact calculation, with enough defining equations to check every entry. Their reproduction in this exposition is not a claim of a new independent numerical or computer-algebra run.

By Corollary 10.3, the axial continuum nuisance image is all of \(\mathbb R^{32}\) at this cutoff and every larger one. The unrestricted deterministic low-source quotient therefore vanishes for this operator. This conclusion neither bounds a physical high-source amplitude nor removes information under a separately specified stochastic model.

### 11.4 The numerical rank ladder and its interpretation

**Computational results, not new analytic theorems.** The preceding research calculations reported the following ranks for the same continuum weight and identity transfer:

| Source cutoff | Axial direction \(\widehat z\) | Transverse directions \(\widehat x,\widehat y\) | Specified diagonal directions |
|---:|---:|---:|---:|
| 8 | 20 | 24 | 24 |
| 9 | 27 | 29 | 32 |
| 12 | 32 | 32 | 32 |

The diagonal directions are \((1,1,1)/\sqrt3\), \((1,-1,1)/\sqrt3\) and \((1,1,-1)/\sqrt3\). This defines the six directions used in the comparison. At \(L=12\), the reported smallest singular values in orthonormal source and retained coordinates are

\[
s_{32}^{Z}\simeq0.006905664979696537,
\quad s_{32}^{X/Y}\simeq0.010490334912761,
\quad s_{32}^{\rm diag}\simeq0.008510322776380.
\tag{11.9}
\]

The nonaxial entries are multi-algorithm numerical evidence, not interval enclosures or analytic proofs for arbitrary directions. To define an independent direct-quadrature route, evaluate the harmonics of Section 3 and their angular derivatives, apply Eq. (9.5) for each of the six vectors, integrate Eq. (11.2) piecewise across the mask breakpoints, and solve the normal equations. The recorded cross-check used 48 Gauss–Legendre nodes on each of \((-3/4,3/4)\) and \((3/4,1)\), and 64 equally spaced azimuths. These quadrature settings describe that calculation; they are not claimed to provide rigorous interval errors.

At \(L=8\) there are already 32 high-source columns, yet the reported ranks are below 32. Column count is not a rank calculation. At \(L=12\), numerical agreement across methods is useful evidence, but it does not replace a mathematical error bound. Only the axial full-rank statement in Theorem 11.1 is supplied here with its exact minor certificate.

### 11.5 Why finite pixelisation remains a different problem

A finite HEALPix calculation replaces the continuum integrals and synthesis with a particular equal-area pixel grid and finite transform/fit algorithms. HEALPix is the name of that spherical pixelisation, not another continuum measure. Its computed response can differ from Eq. (11.3) by quadrature, iteration, transfer and roundoff errors.

The earlier finite matched-control investigation reported seventeen ambiguous coordinates, one resolved survivor and no containment candidate among its eighteen registered cases. These are historical finite-computation outcomes under its selected settings, not eighteen theorems and not a statement about every mask. This exposition does not rerun those cases or infer their missing error bounds from the continuum result.

A positive continuum smallest singular value can be overwhelmed by a numerical perturbation of comparable size. We therefore retain the finite-operator conclusion as unresolved. The next section explains precisely what kind of bound would permit a rank statement; it does not assume that the bound has already been established for an actual pixel calculation.

# Part VII. Numerical uncertainty and the meaning of a conclusion

## 12. Matrix errors, rank and subspace orientation

### 12.1 A declared family of errors

Let the response error have the same matrix shape as the response itself. Suppose the allowed perturbations are represented by finite families

\[
\Delta_f=\sum_i b_{fi}E_{fi},\qquad
\|b_f\|_2\le r_f,\qquad
\Delta=\sum_{f=1}^{F}\Delta_f.
\tag{12.1}
\]

Here \(F\ge1\) is the number of families, \(r_f>0\) is a declared coefficient radius, and every \(E_{fi}\) is a known error-direction matrix. The families, basis, coordinate metrics and radii must be fixed independently of the later rank decision. A matrix measured on one calibration sample does not by itself prove that all actual errors lie in the class.

An error family is a set of possible perturbations, not necessarily a probability distribution. Independent family coefficients are not assumed. The following bound holds even when they are dependent, since it uses worst-case norm bounds.

**Theorem 12.1 — a matrix-valued error envelope.** Every perturbation in Eq. (12.1) satisfies

\[
\Delta\Delta^T\preceq F\sum_f r_f^2\sum_iE_{fi}E_{fi}^T.
\tag{12.2}
\]

**Proof.** For any output-space vector \(x\), Cauchy–Schwarz in the finite family sum gives
\(\|\sum_f\Delta_f^Tx\|^2\le F\sum_f\|\Delta_f^Tx\|^2\).
Within one family,
\(\|\sum_i b_{fi}E_{fi}^Tx\|\le\|b_f\|_2(\sum_i\|E_{fi}^Tx\|^2)^{1/2}\),
which follows by applying scalar Cauchy–Schwarz to each component and summing. Squaring, using the radius bounds and adding families yields Eq. (12.2) as an inequality for every quadratic form \(x\). That is exactly the definition of Loewner order. \(\square\)

Add a positive regularisation scale,

\[
\Gamma_E=F\sum_f r_f^2\sum_iE_{fi}E_{fi}^T+\lambda^2I,
\qquad\lambda>0.
\tag{12.3}
\]

For nonzero \(x\),
\(x^T\Gamma_Ex=F\sum_fr_f^2\sum_i\|E_{fi}^Tx\|^2+\lambda^2\|x\|^2>0\).
Thus \(\Gamma_E\) is positive definite and has the inverse square root \(W=\Gamma_E^{-1/2}\), obtained from Lemma 2.2 by replacing each positive eigenvalue with its inverse square root. All terms in Eq. (12.3) have squared-response units; whitening by \(W\) removes those units in the chosen metric.

### 12.2 Which reparametrisations leave the bound unchanged?

Replacing all matrices of family \(f\) by \(c_fE_{fi}\), with \(c_f>0\), and its radius by \(r_f/c_f\) leaves both the represented perturbation set and the corresponding Gram sum in Eq. (12.3) unchanged. Replacing the family basis by an orthogonal mixing also preserves the sum: if \(E_i'=\sum_jO_{ij}E_j\) and \(O^TO=I\), then
\(\sum_iE_i'E_i'^T=\sum_{jk}(\sum_iO_{ij}O_{ik})E_jE_k^T=\sum_jE_jE_j^T\).
These are exact invariances within the fixed family partition.

An exactly zero family is different. It adds no possible perturbation but changes the conservative prefactor \(F\). Therefore it should be omitted or rejected when defining the representation. Splitting or merging families is not covered by the preceding invariance: the coefficient geometry and the bound can change. This is why the partition itself is part of the error model.

### 12.3 A conditional rank certificate

Write \(K_{\rm obs}=K_{\rm true}+\Delta\), where the first is a computed matrix and the second the ideal matrix in the same coordinates. The word observed here refers to the computed response, not a new sky observation. If the actual error belongs to Eq. (12.1), then

\[
W\Delta\Delta^TW\preceq I,
\qquad\|W\Delta\|_2\le1.
\tag{12.4}
\]

The first inequality follows by congruence transformation of Eq. (12.2) with \(W\), using \(\Delta\Delta^T\preceq\Gamma_E\). The second follows because the squared operator norm is the largest eigenvalue of the product with its transpose.

**Theorem 12.2 — rank under a contained numerical error.** Under these hypotheses,

\[
s_i(WK_{\rm true})\ge s_i(WK_{\rm obs})-1,
\]

\[
\operatorname{rank}K_{\rm true}
\ge\#\{i:s_i(WK_{\rm obs})>1\}.
\tag{12.5}
\]

**Proof.** Apply Proposition 2.3 to \(WK_{\rm obs}\) and perturbation \(-W\Delta\). Every strictly positive lower bound gives a nonzero singular value of \(WK_{\rm true}\). Invertible left multiplication by \(W\) preserves the rank. \(\square\)

For an \(m\times n\) response with \(m\le n\), a sufficient full-row-rank condition is

\[
s_m(WK_{\rm obs})\ge1+\delta,\qquad\delta>0.
\tag{12.6}
\]

The positive margin is above the unit perturbation floor. A threshold at or below one is not justified by Eq. (12.5), however early that threshold was chosen. The parameter \(\delta\) must not be tuned after inspecting the same singular values.

This theorem is conditional on actual error membership. It does not establish that the error registry is complete. That premise is precisely what prevents us from replacing the unresolved finite-pixel result by the continuum rank certificate.

### 12.4 Why rank does not fix a singular subspace

A matrix can retain the same rank while its singular vectors rotate. For example, the two rank-one projectors onto distinct lines in a plane both have rank one, regardless of their angle. To control a nuisance projector, we need a separation between the selected spectral cluster and its complement as well as a perturbation bound.

Here is an explicit finite-dimensional version of that requirement. It supplies the argument instead of only naming a perturbation theorem; sharper or differently normalised bounds are available in the cited subspace literature. [@CAI_ZHANG_2018; @LI_1999; @LYU_WANG_2020]

**Proposition 12.3 — a gap-dependent projector bound.** Let \(H\) and \(\widehat H=H+E\) be real symmetric matrices. Let \(U\) and \(\widehat U\) have orthonormal columns spanning specified eigenspaces of equal dimension \(r\), and let \(U_c\) span the orthogonal complement of \(U\). Assume every eigenvalue \(\lambda_i\) of \(H\) in \(U_c\) is separated from every selected eigenvalue \(\widehat\lambda_j\) of \(\widehat H\) by at least \(g>0\). Then

\[
\|UU^T-\widehat U\widehat U^T\|_F
\le\frac{\sqrt2\,\|E\|_F}{g}.
\tag{12.7}
\]

**Proof.** Choose the displayed bases to be eigenvector bases, allowed by Lemma 2.2. Put \(C=U_c^T\widehat U\). Multiplying \(\widehat H\widehat U=\widehat U\widehat\Lambda\) by \(U_c^T\) gives
\(\Lambda_cC-C\widehat\Lambda=-U_c^TE\widehat U\).
Entrywise,
\((\lambda_i-\widehat\lambda_j)C_{ij}=-(U_c^TE\widehat U)_{ij}\).
The gap assumption implies
\(\|C\|_F\le\|U_c^TE\widehat U\|_F/g\le\|E\|_F/g\),
because orthogonal projections cannot increase a Frobenius norm. Finally,
\(\|UU^T-\widehat U\widehat U^T\|_F^2=2r-2\|U^T\widehat U\|_F^2=2\|C\|_F^2\),
where the last equality uses the orthogonal decomposition into \(U\) and \(U_c\). This proves Eq. (12.7). \(\square\)

For a rectangular response, use \(H=AA^T\); its eigenvectors are the left singular vectors of \(A\). If \(\widehat A=A+D\), then

\[
\widehat H-H=AD^T+DA^T+DD^T,
\qquad
\|\widehat H-H\|_F
\le(2\|A\|_2+\|D\|_2)\|D\|_F.
\tag{12.8}
\]

The norm bound follows from the triangle inequality and \(\|AB\|_F\le\|A\|_2\|B\|_F\), proved by applying the operator-norm bound to every column. Combining Eqs. (12.7)–(12.8) gives a concrete, possibly conservative, sufficient projector control once the specified cross-gap is known. It does not assert that an arbitrary numerically selected cluster has that gap or that the finite CMB error is already bounded. These are additional hypotheses, not consequences of a rank count.

## 13. What we have learned and what remains physical input

We began with a temperature map, not a spacetime solution. Harmonic and STF representations retain the same angular information, while scalar powers generally do not. On a nonzero cyclic domain, the invariant packet separates proper-rotation orbits and yields an explicit representative. Its singular boundaries are part of the result, not defects to hide by an arbitrary axis choice.

We then introduced physical kinematics independently. A shear tensor belongs to an observer congruence; a temperature quadrupole belongs to an angular field. Their common STF2 type does not supply a response. Conditional MES inequalities bound physical-sector norms under radiation, derivative and observer premises. They cannot recover directions from invariant scalars alone. The product gauge, exact affine fibre and finite-null arguments show where additional inequalities, shared data and sampling symmetry enter an inference.

The local-observer response provides one concrete translation between a change of frame and an angular pattern. We derived its temperature pullback, quadrupole-to-octupole tensor map, normal matrix and residual. Its least-squares coordinate remains an algebraic response coordinate unless a model distinguishes intrinsic and observer-induced contributions. General shear, vorticity or global-matter-tilt inference still needs the corresponding physical response.

Processing adds another layer. Weighted fitting and mask coupling change which nuisance patterns can occupy the retained output space. The continuum axial example demonstrates exact full nuisance-image rank for one stated operator, using a certificate included in this report. Numerical nonaxial results and finite-pixel studies retain different evidential status. A matrix error bound can support a rank or subspace conclusion only when it actually contains the relevant perturbations and has the required margin or gap.

The general mathematical statements of this exposition have their hypotheses and proofs locally available. The physical derivative inequalities in input M are deliberately stated as imported model premises; the complete Einstein–Liouville almost-isotropy argument is not reproduced. Historical numerical results are labelled as calculations rather than promoted into universal theorems. These are limits on what the report establishes, not invitations to identify missing information with zero.

No current observational p-value, physical shear estimate, intrinsic-octupole fraction, global-tilt estimate or finite-HEALPix containment conclusion is claimed. The practical outcome is a chain of well-defined questions: represent the observable, specify the physical state, declare the response and constraints, identify the compatible set, then justify the statistical and numerical interpretation. A future analysis can refine one of these steps without confusing it with all the others.
