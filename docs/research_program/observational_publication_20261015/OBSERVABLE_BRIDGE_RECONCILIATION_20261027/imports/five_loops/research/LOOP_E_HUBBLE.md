# LOOP E — What a direction-dependent Hubble measurement measures

**Owner:** HTT internal theory loop E. **Date:** 2026-10-26. **Scope:** local covariant distance jets, a vacuum Bianchi I example, and statistical transport. Baseline commit: a55036ad09c53a9215dee3282e425d37cfb95443. No native evolution solver is used.

**국문 초록.** 방향별 Hubble 계수는 관측자 합동의 팽창·전단·가속도를 한 방향으로 투영한 국소 광학량이다. 유한 적색편이에서 \(cz/D_L\)로 정의한 값과 거리 미분으로 정의한 값은 서로 다른 물리량이다. 두 정의가 어느 차수에서 달라지는지 유도하고, 광학 거리의 세 번째 계수가 곡률과 합동의 변화율을 어떤 조합으로 측정하는지 계산한다. 진공 Kasner 시공간의 실제 Ricci 텐서를 직접 계산하여, 방향별 팽창과 겉보기 감속이 FLRW 물질 해석 없이도 변하는 명시적 예를 얻는다.

## R1 — Research question and useful output

The legacy programme asks for a redshift- and direction-dependent Hubble factor and its relation to the local geometric state. A map of fitted Hubble ratios answers this question after its distance definition, source congruence and redshift interval are fixed. This loop constructs the map from geometric derivatives to observable distance coefficients and identifies a curvature–history combination that an additional observable can resolve.

The output is a finite algebraic interface. The first distance coefficient measures directional expansion, the next its derivative along the ray, and the cubic term combines another derivative with Ricci focusing. Distance coefficients and their joint region enter a geometric image without constructing a new Einstein–Boltzmann history.

## R2 — Literature and source reuse

Ellis, Maartens and MacCallum, *Relativistic Cosmology*, supplied PDF pp179–184 (printed pp163–168), develops null congruences, focusing and reciprocity. PDF pp207–208 (printed pp191–192) relates the leading optical expansion to observer kinematics. Heinesen, “Multipole decomposition of the general luminosity distance ‘Hubble law’ — a new framework for observational cosmology,” JCAP 05 (2021) 008, [arXiv:2010.06534v2](https://arxiv.org/abs/2010.06534), supplies the general cosmographic setting; equations (11), (14), (16), (19), (28) and (29) were checked in the primary text. General anisotropic cosmography is established prior work. The construction here connects it to the HTT state and the retained residual-compatible image.

The legacy affine radial recipe and current R32 moment-image results are reused. Loop C supplies the same-congruence optical interpretation; Loop D supplies a geometric compatibility body. Loop C uses inverse-time rates, whereas this loop uses inverse-length rates until multiplication by \(c\).

## R3 — Geometric convention and observables

Use signature \((-+++)\), a unit timelike field \(u\), and outward sky direction \(n\), with \(u^2=-1\), \(n^2=1\), \(u\cdot n=0\). The past-directed null tangent and redshift are
\[
K=E(-u+n),\qquad E=u\cdot K,\qquad E_O=1,\qquad z=E-1.
\tag{E1}
\]
Affine parameter \(\lambda\), increasing into the past, has length units. Put \(A=u\cdot\nabla u\) and
\[
h(\lambda)=\frac{\Theta}{3}+\sigma_{ab}n^an^b-A_an^a.
\tag{E2}
\]
Contracting the velocity gradient with \(K^aK^b\) gives
\[
\frac{dE}{d\lambda}=E^2h.
\tag{E3}
\]
Antisymmetric vorticity drops out. This tensor contraction was evaluated with xAct/xTensor. It identifies \(H_{\rm dir}(0,n)=ch_0(n)\), where \(h_0=h(0)\).

Assume geometric optics, a regular observer vertex, no caustic in the expansion neighbourhood, and photon-conserving reciprocity. Then
\[
D_A''=-\left(\frac12R_{ab}K^aK^b+|\widehat\sigma|^2\right)D_A,
\quad D_A(0)=0,\quad D_A'(0)=1,\qquad D_L=(1+z)^2D_A.
\tag{E4}
\]
At a regular vertex the optical shear is \(O(\lambda)\), so its square enters beyond the cubic distance term. Matter-congruence shear \(\sigma\) and null optical shear \(\widehat\sigma\) are different tensors.

## R4 — Distance-jet calculation

Write \(h_1=h'(0)\), \(h_2=h''(0)\), and \(R_0=(R_{ab}K^aK^b)_O\). The derivatives include ray-direction and energy evolution. Differentiating (E3) gives
\[
E=1+h_0\lambda+\left(h_0^2+\frac{h_1}{2}\right)\lambda^2
+\left(h_0^3+h_0h_1+\frac{h_2}{6}\right)\lambda^3+O(\lambda^4).
\tag{E5}
\]
Focusing gives \(D_A=\lambda-R_0\lambda^3/12+O(\lambda^4)\). For \(h_0\ne0\), series inversion yields
\[
D_L=d_1z+d_2z^2+d_3z^3+O(z^4),
\tag{E6}
\]
\[
d_1=\frac1{h_0},\qquad d_2=\frac1{h_0}-\frac{h_1}{2h_0^3},\qquad
d_3=\frac{h_1^2}{2h_0^5}-\frac{h_2}{6h_0^4}-\frac{R_0}{12h_0^3}.
\tag{E7}
\]
Wolfram series inversion returns zero residual against (E7). In FLRW, \(h_1=(1+q)h_0^2\), \(h_2=(j+4q+3)h_0^3\), \(R_0=2h_0^2(1+q-\Omega_k)\). Therefore
\[
d_3=\frac{-1+q+3q^2-j+\Omega_k}{6h_0}.
\tag{E8}
\]
This limit was also checked symbolically.

## R5 — Two Hubble estimands and a curvature–history combination

Define
\[
H_{\rm ratio}=\frac{cz}{D_L},\qquad
H_{\rm diff}=\frac{c}{\partial_z[D_L/(1+z)]}.
\tag{E9}
\]
With \(q_{\rm eff}=h_1/h_0^2-1\),
\[
H_{\rm ratio}=ch_0\left[1-\frac{1-q_{\rm eff}}2z+O(z^2)\right],
\qquad H_{\rm diff}=ch_0[1+(1+q_{\rm eff})z+O(z^2)].
\tag{E10}
\]
These are different finite-redshift observables. Even in FLRW, the transverse comoving-distance definition of \(H_{\rm diff}\) equals \(H(z)\) only in the spatially flat case. A directional derivative fit measures a specified optical coefficient.

**Finite-jet equivalence lemma.** The three coefficients (E7), at \(h_0\ne0\), determine \(h_0,h_1\), and
\[
\mathcal J=h_2+\frac{h_0R_0}{2}
=\frac{3h_1^2}{h_0}-6h_0^4d_3.
\tag{E11}
\]
They are invariant under
\[
R_0\mapsto R_0+\delta,\qquad h_2\mapsto h_2-\frac{h_0\delta}{2}.
\tag{E12}
\]
**Proof.** Recover \(h_0,h_1\) from the first two coefficients. Multiply the third by \(6h_0^4\) to obtain (E11); substitution proves (E12). A curvature or derivative measurement thus adds precisely the missing direction in this local jet space. A fixed matter model can restrict the space further.

A physical example is a smooth FLRW family with fixed \(H_0,q_0,j-\Omega_k\), while \(j\) and \(\Omega_k\) vary together. Smooth scale-factor jets with these values can be chosen locally; Einstein's equations define the corresponding homogeneous density and pressure when no fixed equation of state is imposed. This gives local realizability under that freedom.

## R6 — A relativistic anisotropic example without an evolution solver

For diagonal Bianchi I,
\[
ds^2=-c^2dt^2+\sum_i a_i(t)^2(dx^i)^2,\qquad H_i=\dot a_i/a_i.
\tag{E13}
\]
In an orthonormal spatial frame let \(H_n=\sum_iH_in_i^2\). Conserved spatial photon momenta give
\[
\frac{dt}{d\lambda}=-\frac{E}{c},\qquad
\frac{dn_i}{d\lambda}=\frac{E}{c}n_i(H_i-H_n).
\tag{E14}
\]
Hence
\[
h_0=\frac{H_n}{c},\qquad
h_1=\frac1{c^2}\left[-\sum_i\dot H_i n_i^2
+2\left(\sum_iH_i^2n_i^2-H_n^2\right)\right]_O.
\tag{E15}
\]
Twice the directional variance of expansion eigenvalues enters because the photon direction drifts. Holding \(n\) fixed during differentiation would omit this contribution.

Choose the vacuum Kasner solution \(a_i=(t/t_*)^{p_i}\), \(p=(-1/3,2/3,2/3)\). Direct Christoffel-to-Ricci calculation gives, with \(t_*=1\),
\[
R_{tt}=\frac{\sum_i p_i-\sum_i p_i^2}{t^2},\qquad
R_{ii}=\frac{p_i(\sum_jp_j-1)t^{2p_i-2}}{c^2}.
\tag{E16}
\]
Both vanish for this triple. For \(x=n_1^2\),
\[
tH_{\rm dir}=\frac23-x,\qquad
q_{\rm eff}(x)=-1+\frac{2/3+x-2x^2}{(2/3-x)^2}
=\frac{2+3(7-9x)x}{(2-3x)^2}.
\tag{E17}
\]
At \(x=0\), \(q_{\rm eff}=1/2\); at \(x=1/2\), it is \(23\). Volume expansion is \(c\Theta=1/t\), while directional expansion can vanish or change sign. Large \(q_{\rm eff}\) near \(x=2/3\) comes from a small directional denominator; the spacetime remains Ricci-flat.

At \(h_0=0\), the affine expansion survives but redshift ceases to be a valid first-order local coordinate. The figure restricts the redshift-series example to \(x\le0.55\). A survey crossing the zero should fit the distance/affine response directly.

## R7 — Finite-redshift remainder and statistical application

Suppose a declared local domain supplies
\[
|D_L-d_1z-d_2z^2|\le Mz^3,\qquad z>0.
\tag{E18}
\]
If \(L=d_1+d_2z-Mz^2>0\), exact reciprocal monotonicity gives
\[
\frac{c}{d_1+d_2z+Mz^2}\le H_{\rm ratio}
\le\frac{c}{d_1+d_2z-Mz^2}.
\tag{E19}
\]
This is conditional on a justified \(M\). Window variation and an independently bounded derivative class can assess finite-distance sensitivity; a polynomial fit alone does not certify \(M\).

Fit distance coefficients with scalar/STF angular functions and redshift powers, then push their joint region through (E7) and (E11). Shared calibration, peculiar velocities, masks and repeated objects enter one covariance/nuisance model. Public total covariance is used once. For SN data, fit magnitude or flux through its distance response rather than assuming transformed distances have homoscedastic Gaussian errors.

For a declared linear response \(z_{\rm obs}=A\theta+e\), reuse the repaired repository image
\[
E_z=\{e\in E:(I-AA^+)(z_{\rm obs}-e)=0\},\qquad
\Theta_z=\{A^+(z_{\rm obs}-e)+k:e\in E_z,\ k\in\ker A\}.
\tag{E20}
\]
Nonlinear inversion requires its nonlinear image or a bounded linearization remainder. A linear target \(J\theta\) is point identified only if \(\ker A\subseteq\ker J\). Useful combinations can therefore proceed while others await additional input.

## R8 — Physical meaning of statistical robustness and information

The supplied Wager text, *Causal Inference: A Statistical Learning Approach*, Chapter 3, PDF pp30–35, explains augmented weighting and product-error control. The same mechanism applies to a missing-data estimating equation under explicit missing-at-random assumptions; no intervention is inferred from a sky direction.

Let \(S\) indicate selection, \(X\) parent covariates and \(g_\theta(X,Y)\) a population physical moment. Assume \(E[g_\theta\mid X,S=1]=E[g_\theta\mid X]\) and \(\pi(X)=P(S=1\mid X)>0\). For working functions \(\widetilde m,\widetilde\pi\), assume \(\widetilde\pi>0\) on the parent support and integrability of the terms below, and set
\[
\psi_\theta=\widetilde m_\theta(X)
+\frac{S}{\widetilde\pi(X)}[g_\theta-\widetilde m_\theta(X)].
\tag{E21}
\]
With \(m_\theta=E[g_\theta\mid X]\), conditional expectation gives
\[
E[\psi_\theta]-E[g_\theta]
=E\!\left[\left(1-\frac{\pi}{\widetilde\pi}\right)
(\widetilde m_\theta-m_\theta)\right].
\tag{E22}
\]
This proves the double-robust mean identity and exposes its product error. For Hubble measurements it couples a directional-residual regression to selection modelling. Use group/calibration-blocked cross-fitting for shared errors. Without parent support or a justified selection law, a population moment remains conditional; an explicitly selected-cohort estimand can still be studied under its own law.

Polyanskiy and Wu, *Information Theory*, §2.6 and §3.2, supplied PDF pp61–62 and pp78–79, supplies the sufficiency framework. For a regular dominated family with score \(s(Y)\), a parameter-independent compression \(T(Y)\) has score \(E[s(Y)\mid T]\). Thus
\[
I_Y-I_T=E[\operatorname{Cov}(s(Y)\mid T)]\succeq0.
\tag{E23}
\]
Differentiation under the marginal integral and total covariance prove the identity. Invertible tensor coordinates preserve information, while a scalar amplitude can discard orientation or signed combinations that separate shear, boost and calibration. The identity does not establish sufficiency for an arbitrary chosen summary.

## R9 — Tensorized carrier and flexible acceptance

The carrier \(x\) holds jointly framed geometric variables or identifiable combinations, with a shared epoch and explicit units. Push the joint confidence/feasibility region through the declared maps.

Keep three \(F\) namespaces distinct: current typefree directional support utilization \(F_{\rm sup}\); legacy certified diagnostic \(F_{\rm cert}=x_C/U\); measure-defined occupancy \(F_\nu\). The legacy code explicitly rejects a material-volume interpretation. \(Q\) is the gauge of a specified anchor body, \(\Pi\) an exceedance object after supplying a source law, and \(G_F\) a depth/transport/coherence construction with its actual joint couplings. A geometric image can be completed before a calibrated exceedance probability exists.

Attach acceptance to each delivered observable or theorem. Equations (E11), (E19) and (E20) have useful, distinct acceptance conditions. They do not overwrite the original external-history requirement. This makes theorem and optical-coefficient progress possible while preserving the external history task.

## R10 — Verification and next experiment

Stored Wolfram checks cover series inversion, the full Bianchi I Ricci tensor, vacuum Kasner specialization, cubic-jet invariance and the FLRW limit. All residuals vanish. An initial syntax failure is retained separately from the repaired successful receipt. The xAct check establishes the null-gradient contraction, not a full cosmographic likelihood.

Next fit the first two optical coefficients jointly in fixed redshift windows, using one common nuisance/covariance model and explicit remainder sensitivity. Report \(ch_0(n)\), \(h_1(n)\), and the positive-denominator domain of ratios. Extend the fit to a supported cubic coefficient \(d_3\) before reporting \(\mathcal J(n)\). Compare radial shear with Loop C's transverse E2 response. The Kasner example and Loop D bodies then supply concrete geometric interpretations.
