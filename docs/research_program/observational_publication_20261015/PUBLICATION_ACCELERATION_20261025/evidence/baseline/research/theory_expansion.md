# Tensor images, local cosmography, and induced angular morphology

## Directional expansion and a nonlinear observable

The local expansion tensor supplies a direct physical interpretation of a directional Hubble law. We use signature $(-,+,+,+)$, proper length $s=c\tau$, a unit timelike congruence $u$, and a source direction $n$ in its instantaneous rest space. With physical expansion and shear rates measured in inverse time,
\[
\nabla_a u_b=-u_aA_b/c^2+(H/c)h_{ab}+\sigma_{ab}/c+\omega_{ab}/c.
\]
The past-directed null direction is $\ell^a=-u^a+n^a$, so that $u\cdot\ell=1$. Its contraction gives
\[
\mathcal H_u(n)=c\ell^a\ell^b\nabla_a u_b
=H-\frac{A\cdot n}{c}+\sigma:nn.
\tag{T1}
\]
The acceleration sign follows from this definition of the source direction. Antisymmetry removes the vorticity contraction. Under the regular local optical assumptions, with emitter and observer following this congruence, $d_L(z,n)=cz/\mathcal H_u(n)+O(z^2)$. This is the local covariant cosmography developed by Kristian and Sachs and by Heinesen; observer changes require the accompanying redshift, distance, and angular transformations [Heinesen 2021; Maartens et al. 2024].

Assume $H>0$ and introduce dimensionless quantities
\[
 d=-\frac{A}{cH},\qquad S=\frac{\sigma}{H},\qquad
 q(n)=d\cdot n+S:nn,\qquad
 \mathcal H_u(n)=H[1+q(n)].
\tag{T2}
\]
Here $S$ is a real symmetric trace-free rank-two tensor. We also assume $1+q(n)>0$ on the full sphere, so that the local positive-redshift distance law and its logarithm are defined in every direction. The directional rate contains only a monopole, dipole, and quadrupole at this event. The corresponding magnitude field need not have this angular truncation. Subtracting the isotropic magnitude at the same sufficiently small positive redshift and taking the local limit gives
\[
 f_\mu(n)=\lim_{z\downarrow0}5\log_{10}
 \frac{d_L(z,n)}{cz/H}
 =-\kappa\log[1+q(n)],\qquad \kappa=\frac5{\ln10}.
\tag{T3}
\]
The limit concerns the angular part of a local distance law; the individual magnitudes themselves diverge as $z\downarrow0$. The nonlinear map in (T3) generates higher angular multipoles even when (T1) has none. This distinction is useful whenever angular shape is used to interpret departures from an isotropic Hubble law.

There is an exact inverse statement for the complete ideal local field. Even if $f_\mu$ is known only up to a direction-independent intercept, define
\[
 r(n)=\frac{\exp[-f_\mu(n)/\kappa]}
 {\langle\exp[-f_\mu/\kappa]\rangle},\qquad
 \langle g\rangle=\frac1{4\pi}\int_{S^2}g\,d\Omega.
\]
Since $\langle q\rangle=0$, we obtain $r=1+q$ and
\[
 d_a=3\langle rn_a\rangle,\qquad
 S_{ab}=\frac{15}{2}\left\langle r
 \left(n_an_b-\frac{\delta_{ab}}3\right)\right\rangle.
\tag{T4}
\]
Thus the dimensionless local angular shape can be reconstructed without the absolute magnitude intercept under this observation law. The absolute quantities $H$, $A$, and $\sigma$ still require normalization. Selected angular support, finite-redshift fitting, and source-dependent magnitude calibration alter the observation map and must be retained in an application. In particular, exponentiating a truncated or noisy harmonic fit is not the same operation as applying (T4) to the complete field.

## Acceleration--shear coupling in the magnitude octupole

We now obtain the leading induced octupole and its error. Let $\mathsf P_3$ be the full-sphere orthogonal projector onto degree three. Define the rank-three STF tensor $O_\mu$ by
\[
 \mathsf P_3f_\mu(n)=O_{\mu,abc}n^an^bn^c,
 \qquad
 O_{\mu,abc}=\frac{35}{2}\langle f_\mu n_{\langle a}n_bn_{c\rangle}\rangle.
\tag{T5}
\]
This is an optical magnitude tensor, with magnitude units. We use a different symbol for a CMB temperature or polarization octupole: equal tensor rank does not imply equal physical response.

For a vector $d$ and an STF tensor $S$, set
\[
 \begin{split}
 [L_Sd]_{abc}
 &=d_{(a}S_{bc)}
 -\frac{2}{15}\left[
 \delta_{ab}(Sd)_c+\delta_{ac}(Sd)_b+\delta_{bc}(Sd)_a\right],\\
 (L_Sd):n^3
 &=(d\cdot n)(S:nn)-\frac25(Sd)\cdot n.
 \end{split}
\tag{T6}
\]
Parentheses denote the average over the three distinct terms in $d_{(a}S_{bc)}$. The subtracted term removes its trace. Expanding (T3) through second order gives
\[
 -\kappa\left(q-\frac{q^2}{2}\right).
\]
The linear term has degrees one and two. In $q^2$, $(d\cdot n)^2$ and $(S:nn)^2$ are antipodally even, while the cross term is $2(d\cdot n)(S:nn)$. Its degree-three part is (T6). Consequently
\[
 O_\mu=\kappa L_Sd+R_3.
\tag{T7}
\]
The vector and shear therefore generate a seven-component angular octupole at second order. This is a coupling of already specified kinematics; it is not an additional free rank-three kinematic field.

Suppose a known bound satisfies
\[
 \sup_n|q(n)|\leq\epsilon<1.
\]
A sufficient choice is $\epsilon\geq |d|+\|S\|_{\rm op}$. The absolutely convergent logarithm series gives
\[
 \left|\log(1+q)-q+\frac{q^2}{2}\right|
 \leq\frac{\epsilon^3}{3(1-\epsilon)}.
\]
For any STF rank-three tensor $T$, spherical sixth moments give
\[
 \langle(T:n^3)^2\rangle=\frac{2}{35}T:T.
\]
Since $\mathsf P_3$ is an $L^2$ contraction under the normalized full-sphere measure, (T7) obeys the finite bound
\[
 \boxed{\quad
 \|R_3\|_F\leq E_3(\epsilon)
 :=\sqrt{\frac{35}{2}}\,
 \frac{\kappa\epsilon^3}{3(1-\epsilon)}.
 \quad}
\tag{T8}
\]
This bound controls truncation in the finite angular variable of the local law. It does not bound the omitted finite-redshift terms in $d_L$, an observer-frame error, or catalogue selection.

When $S=0$, the quadratic coupling vanishes and the leading optical octupole is cubic:
\[
 O_\mu=-\frac{\kappa}{3}\operatorname{STF}(d^{\otimes3})+R_{3,d},
 \qquad
 \|R_{3,d}\|_F\leq
 \sqrt{\frac{35}{2}}\,
 \frac{\kappa|d|^5}{5(1-|d|^2)},\quad |d|<1.
\tag{T9}
\]
Only the odd powers of the logarithm contribute to degree three, which proves the fifth-order remainder bound. For $d=-a\hat d$, (T9) has the positive sign of $-\kappa\log(1-a\hat d\cdot n)$ used in the retained zero-shear finite-source calculation. The acceleration--shear term in (T7) can therefore dominate that pure-dipole octupole when both dimensionless fields are of the same small order.

## Constructive inversion and the residual morphology

For fixed $S\ne0$, the coupling map retains all three components of $d$. Its useful identities are
\[
 \begin{split}
 \|L_Sd\|_F^2
 &=\frac{S:S}{3}|d|^2+\frac25|Sd|^2,\\
 (L_Sd):S&=K_Sd,\qquad
 K_S=\frac{S:S}{3}I+\frac25S^2.
 \end{split}
\tag{T10}
\]
To prove the first equation, write $T_{abc}=d_{(a}S_{bc)}$. Then
\[
 T:T=\frac13|d|^2(S:S)+\frac23|Sd|^2,
 \qquad T_{aac}=\frac23(Sd)_c.
\]
For a symmetric rank-three tensor, removing its trace subtracts $3|T_{aa\cdot}|^2/5$ from its squared norm, which gives the first line of (T10). Contracting (T6) with $S_{bc}$ gives the second. In particular, $K_S\succeq(S:S)I/3>0$. If $\lambda_i$ are the eigenvalues of $S$, the singular values of $L_S$ are
\[
 s_i(L_S)=\sqrt{\frac{S:S}{3}+\frac25\lambda_i^2}.
\tag{T11}
\]
No choice of shear eigenaxes is needed to use $K_S$.

For an octupole $O$, define the least-squares coupling vector and residual by
\[
 \widehat d_S(O)=\frac1\kappa K_S^{-1}(O:S),\qquad
 O_\perp=O-\kappa L_S\widehat d_S(O).
\tag{T12}
\]
The contraction $O:S$ is the adjoint $L_S^*O$, so (T12) is the orthogonal projection onto the three-dimensional image of $L_S$. The residual lies in a four-dimensional complement and satisfies $O_\perp:S=0$. For the exact logarithmic local response,
\[
 \|O_{\mu,\perp}\|_F\leq E_3(\epsilon),\qquad
 |\widehat d_S(O_\mu)-d|
 \leq\frac{E_3(\epsilon)}{\kappa\min_i s_i(L_S)}.
\tag{T13}
\]
Projection cannot increase the remainder norm, and the second inequality follows from the pseudoinverse norm. As $S\to0$, the vector reconstruction becomes increasingly sensitive to fixed absolute octupole errors; the separate pure-dipole cubic law (T9) remains available. For nonzero $S$, the relative condition number of $L_S$ is bounded by $\sqrt{9/5}$: trace freedom gives $\lambda_i^2\leq2(S:S)/3$, while (T11) bounds its squared singular values between $(S:S)/3$ and $3(S:S)/5$. The divergence is in absolute inverse gain as the shear amplitude vanishes. Equations (T12)--(T13) describe a concrete morphology test: at quadratic order a general seven-component magnitude octupole must lie close to a specified three-dimensional coupling image, rather than merely share an axis or a scalar power with the quadrupole. The result also indicates which information an axis-only summary would discard.

## The contraction geometry gains a physical realization

The operator in (T10) is the same positive operator that appears in the exact contraction ellipsoid of the quadrupole--octupole theorem. To see the connection, let $C_S:\mathrm{STF}_3\to\mathbb R^3$ denote $C_SO=O:S$. Then $C_S^*=L_S$ and $C_SC_S^*=K_S$. The abstract decomposition
\[
 O=L_SK_S^{-1}(O:S)+O_\perp,\qquad O_\perp\in\ker C_S
\]
is therefore the optical decomposition (T12). The quadratic response selects the minimum-norm lift of its contracted vector. Its four contraction-fibre coordinates vanish at that order; the full logarithmic response fills them only through the remainder in (T7). This connects the sharp tensor theorem to an explicit local observable mechanism.

The same relation gives a parity-sensitive consequence. For any vector $b$ define $\chi(S,b)=\det[b,Sb,S^2b]$, and for an octupole use the contraction definition $\chi(S,O)=\chi(S,O:S)$. On the quadratic optical response $O^{(2)}_\mu=\kappa L_Sd$,
\[
 \chi(S,O^{(2)}_\mu)
 =\kappa^3\det K_S\,\det[d,Sd,S^2d].
\tag{T13a}
\]
Indeed, $O^{(2)}_\mu:S=\kappa K_Sd$, and $K_S$ commutes with $S$, so that the same matrix $\kappa K_S$ multiplies all three determinant columns. Since $\det K_S>0$, the coupling preserves the sign of this local vector--shear pseudoscalar. For simple-spectrum $S$, in a positively oriented eigenframe its sign is that of
\[
 d_1d_2d_3\prod_{i<j}(\lambda_j-\lambda_i).
\]
Thus a generic acceleration direction with components along all three shear eigendirections can induce a chiral quadrupole--octupole pair in the magnitude field. Repeated eigenvalues or a missing vector component make this particular pseudoscalar vanish. This is a local geometric handedness under proper rotations, not a statement about parity violation in a stochastic cosmological ensemble. For the full logarithm the perturbation is controlled by (T8), and chirality stability must include that perturbation.

## Embedding the bridge in the departure bundle

The physical state can now be propagated through an explicit tensor map. For a common state $Z$ containing $d$, $S$, angular response, calibration, and allowed errors, useful retained functionals are
\[
 x_\phi(Z)=\bigl(d,S,O_\mu,O_{\mu,\perp}\bigr),
 \qquad
 \Sigma_u^2=\frac{S:S}{6}.
\tag{T14}
\]
A joint region $C$ supplies the image $\phi(C)$; its support function describes the convex outer geometry while retaining the underlying tensor image for nonlinear morphology. Both $S$ and $d$ must be transformed with the same physical rotation. If a full-sphere octupole error radius $e_O$ and a bound $\epsilon$ are justified on the same event, then for fixed known $S\ne0$ a useful positive anchor radius is $E_3(\epsilon)+e_O$. The score
\[
 Q_{\rm coupling}
 =\frac{\|O_{\mu,\perp}\|_F}{E_3(\epsilon)+e_O}
\tag{T15}
\]
compares retained morphology with that specified response envelope. Uncertain $S$ requires the joint image over its admissible values, rather than insertion of a best-fit eigenframe into (T12). A zero anchor is handled by the corresponding exact set-membership question. The score is conditional on this optical model and on its supplied error bounds.

Under a named joint measure $\mu$, the associated exceedance is $\Pi_\mu(t)=\mu\{Q_{\rm coupling}>t\}$. A working Gaussian law, a posterior, and a finite collection of response scenarios give different versions of this quantity. The directional or tensor support information belongs to $F$; it does not determine $\mu$. Applying the construction across physically registered redshift or distance windows supplies a path $G_F$, with shared calibration and cross-window covariance retained. Window-dependent departures can then distinguish a change in dimensionless local morphology from changes induced by optical depth or processing. Such a path becomes a statement about $H(z,n)$ only when its windows, source congruence, and finite-redshift response have been specified.

The same STF and proper-rotation machinery can organize low-multipole CMB morphology. The bridge is mathematical and observational: nonlinear response can create a higher angular multipole, and full tensors reveal whether it has the constrained shape of a specified coupling. A common cosmological explanation of optical and CMB tensors additionally needs a model's distinct radiation-transfer and observer responses. Spatial homogeneity and a Bianchi Lie-algebra type are further structures; neither follows from (T1), (T7), or an agreement of tensor axes.

## Synthetic verification and figure caption

We evaluated the logarithmic response on a Gauss--Legendre--azimuthal full-sphere grid. The illustrative family uses
\[
 d=t(1,2,3)/\sqrt{14},\qquad S=t\operatorname{diag}(0.6,-0.2,-0.4),
 \qquad 0.002\leq t\leq0.25.
\]
The sufficient uniform bound is $\epsilon=1.6t\leq0.4$. Seven exact-rational cases verify the STF trace, norm identity, and contraction identity in (T10). For 45 amplitudes, the quadrature reproduces the quadratic coefficient and the reconstruction in (T12), and every measured exact-logarithm remainder lies below (T8). Comparing $40\times80$ and $60\times120$ grids gives a maximum octupole tensor difference $1.21\times10^{-14}$ magnitude. This quadrature comparison checks the finite synthetic calculation; the analytic bound follows from the proof above.

**Figure T1.** Induced optical magnitude octupoles in a local angular response. Left: the exact logarithmic octupole (solid) and its leading acceleration--shear quadratic approximation (dashed), compared with the exact acceleration-only response and its cubic approximation (dotted). The coupled signal is quadratic at small common amplitude, while the pure-dipole signal is cubic. Right: the coupled approximation error and the analytic uniform envelope (T8). The parameters are dimensionless synthetic kinematics, not an observational fit. No finite-redshift propagation or CMB transfer is included. Figure source: `research/theory_bridge_check.py`; machine-readable values: `research/theory_bridge_result.json`; figure: `figures/theory_induced_octupole.pdf`.

## Primary literature and source pointers

- A. Heinesen, *Multipole decomposition of the general luminosity distance 'Hubble law' -- a new framework for observational cosmology*, JCAP 05 (2021) 008; https://arxiv.org/abs/2010.06534v2 ; https://doi.org/10.1088/1475-7516/2021/05/008 . Existing report key `Heinesen2021`.
- R. Maartens, J. Santiago, C. Clarkson, B. Kalbouneh, C. Marinoni, *Covariant cosmography: the observer-dependence of the Hubble parameter*, JCAP 09 (2024) 070; https://arxiv.org/html/2312.09875v3 ; https://doi.org/10.1088/1475-7516/2024/09/070 . Existing report key `Maartens2024`. In particular, the observer transformation is physical; this paper separately identifies a spurious octupole from applying an uncorrected boosted distance relation. The same-frame logarithmic coupling derived here is a different operation.
- J. Kristian and R. K. Sachs, *Observations in cosmology*, Astrophys. J. 143 (1966) 379, republished Gen. Relativ. Gravit. 43 (2011); https://doi.org/10.1007/s10714-010-1114-1 . Historical local optical expansion, not attribution of (T6)--(T13).
- Source report: `sources/report140/sections/01_framework.tex`, `05_optics.tex`, `07_mathematical_details.tex`, especially the full-sphere shear moment, zero-shear nonlinear response, positive stress constraint, tensor orbit and chirality arguments, shared-nuisance image geometry, and ratio inversion.
