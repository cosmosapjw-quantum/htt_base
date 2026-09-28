# Fresh addendum: exact positive shear block of bolometric transport

Status: **derived; synthetic arithmetic checked; independently algebra-checked**. This is a bounded mathematical extension of the original MES/kinematics program. It is not a final decision review, a novelty claim, a data analysis, or an inference of shear from a static CMB map. No additional literature search and no ODE/PDE/Boltzmann solver were used.

## 1. Definitions and units

At one spacetime event choose a timelike observer congruence and an orthonormal spatial frame. Let \(e\in S^2\), \(P(e)=I-ee^T\), and \(V_2=\{S=S^T:\operatorname{tr}S=0\}\), with Frobenius pairing \(S:T=\operatorname{tr}(ST)\).

Use angular **energy density** \(B(e)\), so \(\rho=\int_{S^2}B\,d\Omega\). If the measured quantity is bolometric specific intensity, \(B=I_{\mathrm{bol}}/c\). Assume \(B\ge0\), \(0<\rho<\infty\). Initially take \(B\) sufficiently differentiable for sphere integration by parts; the final formulas extend weakly to finite positive angular measures.

For a physical shear \(S\) in \(\mathrm{s}^{-1}\), set

\[
q_S=e^TSe,\quad v_S=-PSe,\quad
E_{ab}=e_ae_b-\delta_{ab}/3,
\]

\[
\mathcal A_S B=v_S\cdot\nabla_{S^2}B+4q_SB.
\]

Then \(\mathcal L_B(S)=\int E\,\mathcal A_SB\,d\Omega\) has units energy density/time. Solid angles are dimensionless.

## 2. Integration by parts: exact sign and boundary check

For STF \(S\), \(q_S\) is a pure \(\ell=2\) spherical harmonic:

\[
\nabla_{S^2}q_S=2PSe,\qquad
\Delta_{S^2}q_S=-6q_S,\qquad
\operatorname{div}_{S^2}v_S=3q_S.
\]

Since the complete sphere has no boundary,

\[
\int E\,v_S\cdot\nabla B\,d\Omega
=-\int B\,[v_S\cdot\nabla E+3q_SE]\,d\Omega.
\]

The derivative of \(e\) in a tangent direction is that tangent vector, so

\[
v_S\cdot\nabla E=-(Se)e^T-e(Se)^T+2q_See^T.
\]

Adding the \(+4q_SB\) term proves the proposed expression with the stated signs:

\[
\boxed{\mathcal L_B(S)=\int B\left[(Se)e^T+e(Se)^T
-q_See^T-\frac{q_S}{3}I\right]d\Omega.}
\]

Its integrand is symmetric and trace-free. Integrating only a masked sky introduces an actual boundary term unless its treatment is explicitly supplied; the complete-sphere identity must not be applied directly to an observed mask.

## 3. Self-adjointness, positivity, and invertibility

For any \(S,T\in V_2\), contraction gives

\[
\boxed{T:\mathcal L_B(S)=\int B\,[2(Te)\cdot(Se)-q_Tq_S]d\Omega.}
\]

Thus \(\mathcal L_B\) is self-adjoint. Moreover

\[
S:\mathcal L_B(S)
=\int B\,[2|Se|^2-q_S^2]d\Omega
=\int B\,[|Se|^2+|PSe|^2]d\Omega.
\]

With \(M_2=\int B\,ee^T\,d\Omega\),

\[
\boxed{S:\mathcal L_B(S)\ge\operatorname{tr}(S^2M_2)
\ge\lambda_{\min}(M_2)\|S\|_F^2.}
\]

Therefore \(M_2\succ0\) suffices for a positive definite invertible operator on all five STF components, without a weak-anisotropy assumption. Its inverse satisfies

\[
\|\mathcal L_B^{-1}\|_{2\to2}
=\lambda_{\min}(\mathcal L_B)^{-1}
\le\lambda_{\min}(M_2)^{-1}.
\]

An upper bound useful for conditioning is \(S:\mathcal L_B(S)\le\rho\|S\|_F^2\). To see this, set \(e=(0,0,1)\) and write \(S=\begin{pmatrix}A&w\\w^T&s\end{pmatrix}\), \(\operatorname{tr}A=-s\). The integrand is \(2|w|^2+s^2\), while \(\|S\|_F^2\ge2|w|^2+3s^2/2\).

**Sufficiency is not necessity.** For a finite positive measure the exact kernel is

\[
\ker\mathcal L_B=\{S\in V_2:Se=0\ \ B\text{-almost everywhere}\}.
\]

Consequently

\[
\boxed{\mathcal L_B\succ0\text{ on }V_2\quad\Longleftrightarrow\quad
\operatorname{rank}M_2\ge2.}
\]

A symmetric matrix annihilating a two-dimensional support span has rank at most one, and trace-freeness forces it to vanish. Rank-one support leaves two transverse STF null directions. Equal mass on the two axis pairs \(\pm e_1,\pm e_2\) gives \(M_2=(\rho/2)\operatorname{diag}(1,1,0)\), but \(\mathcal L_B\) is strictly positive.

For an ordinary nonzero nonnegative \(L^1(d\Omega)\) density, \(M_2\succ0\) is automatic: no nonzero density of positive integral can be supported only on a great circle of zero area measure. Exact rank deficiency concerns singular angular measures; near-singularity can still cause conditioning problems.

## 4. Exact dependence on only brightness multipoles 0, 2, and 4

Define **raw STF angular moments**, without harmonic-normalization factors:

\[
\Pi_{ab}=\int B e_{\langle a}e_{b\rangle}d\Omega,
\qquad
J_{abcd}=\int B e_{\langle a}e_be_ce_{d\rangle}d\Omega.
\]

Then

\[
M_{2,ab}=\rho\delta_{ab}/3+\Pi_{ab},
\]

\[
M_{4,abcd}=J_{abcd}
+\frac17(\delta_{ab}\Pi_{cd}+\delta_{ac}\Pi_{bd}
+\delta_{ad}\Pi_{bc}+\delta_{bc}\Pi_{ad}
+\delta_{bd}\Pi_{ac}+\delta_{cd}\Pi_{ab})
+\frac{\rho}{15}(\delta_{ab}\delta_{cd}
+\delta_{ac}\delta_{bd}+\delta_{ad}\delta_{bc}).
\]

Substitution and contraction give the compact exact block

\[
\boxed{[\mathcal L_B(S)]_{ab}=
\frac{8\rho}{15}S_{ab}
+\frac{10}{7}S_{c\langle a}\Pi_{b\rangle}{}^c
-J_{abcd}S^{cd}.}
\]

Thus odd moments and all brightness moments above \(\ell=4\) drop out of this **shear block**. They need not drop out of the complete transport problem or of its residual. The expression is the ordinary quadrupole moment of the shear terms in the covariant radiation hierarchy, reorganized as a finite linear operator in the unknown shear.

For isotropic \(B=\rho/(4\pi)\), \(\Pi=J=0\), and

\[
\boxed{\mathcal L_B=(8\rho/15)I_{V_2}.}
\]

Brightness moments are not temperature moments: for directionwise Planckian radiation, \(B=(a_R/4\pi)T^4\), with \(a_R=\pi^2k_B^4/(15\hbar^3c^3)\). One must transform the positive total temperature before forming these moments. No Planck assumption is required if the bolometric energy density is measured directly.

## 5. Local covariant legitimacy and coefficient 4

The phase-space distribution is a scalar on the null momentum bundle. Decompose null momentum relative to the chosen congruence, and separate horizontal spacetime derivatives from vertical sphere/energy derivatives. Per unit observer proper-time normalization, the shear contribution to direction change is \(-P\sigma e\), and to photon energy change it is \(-E\sigma:ee\). These are the local congruence shear, not Sachs null shear or image shear.

For energy-integrated intensity, \(B\) is proportional to \(\int_0^\infty E^3f\,dE\). The energy part of the Liouville operator obeys

\[
\int_0^\infty E^3(-Eq\,\partial_Ef)dE
=4q\int_0^\infty E^3f\,dE,
\]

provided \(E^4f\to0\) at zero and infinity. This proves the coefficient \(+4\), including its sign. The collision energy moment is assumed finite. Planck radiation satisfies the endpoint condition.

The derivation is local and works in a general smooth spacetime. Frame/spacetime connection terms must be kept in the covariant horizontal derivative, or retained explicitly in the remaining transport operator; replacing those derivatives by ordinary partial derivatives of a static sky map is not legitimate. At the event a rotated orthonormal triad merely conjugates the tensor operator, so the statement is spatially covariant. It remains congruence-relative; changing the observer by a boost changes both the brightness and the kinematic decomposition.

This is a rearrangement of a local moment equation. It neither closes the full Einstein–Boltzmann system nor supplies the derivatives entering that equation.

## 6. What can be inferred when the residual is explicit

Write the exact bolometric equation with a declared convention as

\[
\mathcal T_{\mathrm{rest}}B+\mathcal A_\sigma B=C_B,
\]

where \(\mathcal T_{\mathrm{rest}}\) includes all horizontal derivatives and all non-shear kinematic terms. Define

\[
r=\int E[C_B-\mathcal T_{\mathrm{rest}}B]d\Omega.
\]

Then the exact quadrupole equation is

\[
\boxed{\mathcal L_B(\sigma)=r.}
\]

If \(r\) is known and \(\mathcal L_B\succ0\), solving a five-dimensional linear system determines the local shear. If a physically justified residual set \(\mathcal R\subset V_2\) is supplied instead, the honest result is the set

\[
\boxed{\mathcal S(B,\mathcal R)=\mathcal L_B^{-1}\mathcal R.}
\]

For \(\mathcal R=\{r:\|r-r_0\|_F\le\delta\}\), this is an explicit ellipsoid centered at \(\mathcal L_B^{-1}r_0\), contained in the Frobenius ball of radius \(\delta/\lambda_{\min}(\mathcal L_B)\). A residual norm bound therefore gives a shear norm bound, while the full tensor set preserves signs and orientation.

A static CMB brightness sky fixes \(B\) at one event and hence fixes the operator, but it does **not** by itself determine the time derivative, spatial gradients, collisions, acceleration/rotation/expansion contributions, or their quadrupole combination \(r\). If those terms are unrestricted so that \(\mathcal R=V_2\), then \(\mathcal S=V_2\): invertibility alone supplies no shear constraint. Even a locally isotropic sky is compatible with nonzero instantaneous shear if the unmeasured residual balances it.

The original MES program can use its full source assumptions to define \(\mathcal R\) and intersect the resulting set with the stated MES norm ceiling. The signed normalized tensor \(A_\sigma\) and percentage \(F_\sigma\) can then be propagated over that set. No source-free percentage or point estimate follows merely from positivity of \(B\).

## 7. Actual finite checks

A deterministic 64-node Gauss–Legendre by 128-azimuth quadrature was executed for

\[
B(e)=[1+0.7e_z+0.4e_x^2]^2>0,
\quad
S=\begin{pmatrix}.2&.3&-.1\\.3&-.4&.2\\-.1&.2&.2\end{pmatrix}.
\]

The direct angular-derivative projection and the integrated formula agreed to maximum absolute error \(1.71\times10^{-14}\). The raw-moment formula agreed to \(1.04\times10^{-14}\), and the five-dimensional operator matrix was symmetric to \(1.03\times10^{-14}\). Here

\[
\rho=18.3720338382,\quad\lambda_{\min}(M_2)=5.3269443433,
\]

and the five eigenvalues of \(\mathcal L_B\) were approximately

\[
9.14664865,\ 9.24326372,\ 9.79299257,\ 10.37942320,\ 10.42976211.
\]

They satisfy the proved lower bound. For the normalized rank-two axis-pair measure, the eigenvalues were \((1/6,1/2,1/2,1/2,1)\), confirming the distinction between sufficiency and necessity of \(M_2\succ0\).

A separate child agent independently rederived the integration-by-parts signs, bilinear form, isotropic coefficient, and kernel/rank characterization. This bounded algebra check is not the program’s final independent decision review.
