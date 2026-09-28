# Fresh optical endpoint candidate — independent derivation

Status: candidate generation, not decision review or PROMOTE. No sky data, production repository, or numerical differential-equation solver was used. The specified v4 harness core, its initial empty state, model-routing instructions, and optical-source files 01–04 were read. Old internal conclusions, audits, and decision files were not used. This worker inherited the parent configuration without requesting a model override; exact host model identity is not independently observable in the present tool context.

## 1. Scope and precise outcome

**Derived:** A general homogeneous Bianchi I metric, an isotropic spatially uniform Planck distribution on one fixed emission-time surface, comoving geodesic emitters/observer, and subsequent collisionless propagation imply

\[
Y(\mathbf n):=T_o(\mathbf n)^{-2}=n^aM_{ab}n^b,\qquad M=M^T>0.
\]

This is an exact finite-amplitude result. The six entries of the positive matrix are recovered by full-sky monopole/quadrupole moments of **inverse-square total temperature**. Removing the scalar scale leaves a five-dimensional endpoint strain tensor. It fixes the complete temperature morphology in this restricted sector, including a nonlinear hierarchy of even multipoles.

The inferred tensor is not the local timelike shear, the null optical shear, or the image shear. A dynamical bridge is required to turn it into the present shear and the original MES-normalized percentage variables.

The exact diagonal forward temperature relation is already published. The supplied source program also already contains an ideal positive quadratic inverse according to the parent’s fresh source reading. Accordingly this is a rederivation and selection of a tractable program, not a novelty claim.

## 2. Exact momentum and Planck derivation

Use signature \((-+++ )\), cosmic proper time \(t\), and

\[
ds^2=-c^2dt^2+h_{ij}(t)dx^idx^j,\qquad h(t)>0.
\]

The comoving congruence \(u=\partial_t\) obeys \(u^2=-c^2\), zero acceleration, and zero vorticity. Translation Killing vectors make the photon **covariant** spatial momenta \(p_i\) constants. The null condition gives the physical measured energy

\[
E(t)^2=c^2p_i h^{ij}(t)p_j.
\]

Choose an observer orthonormal coframe \(C_o\) satisfying \(C_o^TC_o=h_o\). For outward sky direction \(\mathbf n\), \(p=-(E_o/c)C_o^T\mathbf n\); the sign cancels in the quadratic form. Thus

\[
\left(\frac{E_*}{E_o}\right)^2
=\mathbf n^TC_oh_*^{-1}C_o^T\mathbf n.
\]

At the source surface assume the phase-space occupation number everywhere and in every local direction is

\[
f_*=[\exp(E_*/k_BT_*)-1]^{-1},
\]

with one common \(T_*>0\). Collisionless transport preserves \(f\), and the redshift is independent of photon energy. Every individual observed direction therefore remains Planckian:

\[
T_o(\mathbf n)=\frac{T_*}{1+z(\mathbf n)},\qquad
M=T_*^{-2}C_oh_*^{-1}C_o^T.
\]

With symmetric \(C_o=h_o^{1/2}\), this is

\[
\boxed{M=T_*^{-2}h_o^{1/2}h_*^{-1}h_o^{1/2}}.
\]

A different observer triad merely orthogonally conjugates \(M\). All dependence on intermediate metric history drops out of this homogeneous energy ratio. Geodesic positions and image/Jacobi maps can still depend on the history; they are unnecessary here only because the source radiation is spatially and angularly uniform. Focusing does not supply an additional inverse-square brightness multiplier for a resolved diffuse background.

**Necessary scope conditions:** fixed source cosmic time; uniform source temperature; homogeneous metric; comoving observer; collisionless photons; geometric-optics validity. Finite-width recombination, inhomogeneous source temperature, peculiar boosts, scattering, and polarization require additional terms. A sky-averaged mixture of different directional blackbodies is generally not a single blackbody, even though each ideal direction is.

## 3. Exact algebraic inverse, scale, and degrees of freedom

Let \(\langle f\rangle=(4\pi)^{-1}\int f\,d\Omega\), and \(n_{\langle a}n_{b\rangle}=n_an_b-\delta_{ab}/3\). Isotropic angular identities give

\[
\langle n_an_b\rangle=\frac{\delta_{ab}}3,\quad
\langle n_an_bn_cn_d\rangle=
\frac{\delta_{ab}\delta_{cd}+\delta_{ac}\delta_{bd}+\delta_{ad}\delta_{bc}}{15}.
\]

It follows directly that

\[
\langle Y\rangle=\tfrac13\operatorname{tr}M,\quad
\langle Yn_{\langle a}n_{b\rangle}\rangle=\tfrac{2}{15}M_{\langle ab\rangle},
\]

and hence

\[
\boxed{M_{ab}=\langle Y\rangle\delta_{ab}
 +\frac{15}{2}\langle Yn_{\langle a}n_{b\rangle}\rangle}.
\]

This is unique within the model. Equivalently \(M=(15/2)\langle Y\mathbf n\mathbf n^T\rangle-(3/2)\langle Y\rangle I\). For an arbitrary measured sky, the same expression only extracts its \(\ell=0,2\) projection; it does not establish model adequacy, and the fitted matrix need not be SPD. Positivity and the higher-multipole residual must be checked separately.

Define

\[
\alpha=(\det M)^{1/3},\quad
T_g=\alpha^{-1/2},\quad
K=\tfrac12\log(M/\alpha),\quad\operatorname{tr}K=0.
\]

Then

\[
\boxed{T_o(\mathbf n)=T_g[\mathbf n^Te^{2K}\mathbf n]^{-1/2}}.
\]

The real symmetric matrix logarithm is unique because \(M\) is SPD. \(K\) has five real degrees of freedom. With \(a\propto(\det h)^{1/6}\), \(T_g=T_*a_*/a_o\); \(T_g\) is not generally the angular mean temperature. Unknown absolute temperature calibration changes \(\alpha\), but not \(K\).

This inversion requires the positive total temperature, not a signed anisotropy map by itself. A temperature monopole convention must be supplied before taking \(T^{-2}\). Sky masks destroy the simple orthogonality identities, and noise is transformed nonlinearly; neither is solved by writing the full-sky formula.

## 4. Strain, history, and nonidentifiability

For fixed principal axes, write

\[
h_{ij}=a^2e^{2\beta_i}\delta_{ij},\qquad\sum_i\beta_i=0.
\]

The proper-time shear in the common orthonormal principal frame is \(\sigma_i=\dot\beta_i\), and

\[
K_i=\beta_i(t_o)-\beta_i(t_*)=\int_{t_*}^{t_o}\sigma_i(t)dt.
\]

Thus positive integrated expansion along an axis produces a colder direction on that axis, with the stated emission/observation order.

For a general rotating/noncommuting strain history, the endpoint logarithm is not the ordinary componentwise time integral of shear. Comparing tensors at different times first requires a declared transport identification, and matrix evolution is generally ordered. **Coaxial/commuting expansion is a sufficient condition for the simple integral formula, not a proven logically necessary condition:** noncommuting histories may accidentally give the same endpoint as a commuting one.

Endpoints cannot reconstruct arbitrary histories. Smooth anisotropic metric excursions returning to \(h_o\propto h_*\) give \(K=0\) while the intermediate shear need not vanish. Conversely arbitrary endpoint-compatible histories can have different \(\sigma_o\). Physical realizability further depends on the Einstein equations and stress source, not on the redshift identity alone.

## 5. Temperature morphology and finite-amplitude multipole conditions

Let \(F_K(\mathbf n)=(\mathbf n^Te^{2K}\mathbf n)^{-1/2}\), and use

\[
\Theta=\frac{T}{\bar T}-1=\frac{F_K}{\langle F_K\rangle}-1,\qquad\bar T=\langle T\rangle.
\]

The principal directions of \(M\) and \(K\) coincide. Temperature is greatest along the smallest eigenvalue of \(M\), least along its largest, and antipodal directions have exactly equal temperatures. Distinct eigenvalues give three antipodal stationary axis pairs; degeneracies give the expected axisymmetric or isotropic limits. The eigenframe, eigenvalue ordering, and signs remain useful morphology data beyond a nonnegative scalar norm.

Two rotation-invariant summaries are \(I_2=\operatorname{tr}K^2\) and \(I_3=\operatorname{tr}K^3\), with

\[
|I_3|\le I_2^{3/2}/\sqrt6.
\]

For \(I_2>0\), \(\sqrt6I_3/I_2^{3/2}\in[-1,1]\) describes eigenvalue shape, but it still omits sky orientation. At \(K=0\), eigenframe and normalized shape are undefined.

Exact conditions:

1. \(T(-\mathbf n)=T(\mathbf n)\); every odd temperature multipole vanishes in this rest-frame sector.
2. \(Y=T^{-2}\) has only \(\ell=0,2\); all \(Y\) multipoles with \(\ell\ge3\) vanish exactly.
3. \(T\) usually has nonzero \(\ell=4,6,\ldots\); these have no independent shape parameters beyond \(K\).

Define STF coefficients by \(\Theta(\mathbf n)=\sum_\ell\Theta_{A_\ell}n^{A_\ell}\). Then

\[
Q_{ab}=\frac{15}{2}\langle\Theta n_{\langle ab\rangle}\rangle,\qquad
H_{abcd}=\frac{315}{8}\langle\Theta n_{\langle abcd\rangle}\rangle.
\]

The **finite-amplitude hexadecapole relation** is the exact nonlinear graph

\[
\boxed{H_{abcd}(K)=\frac{315}{8}
\frac{\langle F_Kn_{\langle abcd\rangle}\rangle}{\langle F_K\rangle}}.
\]

It is an ordinary angular integral, not a differential equation. Equivalently the exact algebraic consistency test is \([(1+\Theta)^{-2}]_{\ell=4}=0\), together with every other forbidden inverse-square multipole. This latter relation couples **all** temperature multipoles; truncating it to a polynomial in the temperature quadrupole is not exact at finite amplitude.

For \(\|K\|\ll1\), let \(q=K:nn\) and \(r=K^2:nn\). Expansion gives

\[
F_K=1-q-r+\tfrac32q^2+O(K^3),\quad
\langle F_K\rangle=1-\tfrac{2}{15}\operatorname{tr}K^2+O(K^3).
\]

Therefore

\[
\boxed{\Theta=-K:nn+O(K^2)},
\]

and more precisely

\[
Q_{ab}=-K_{ab}-\tfrac17(K^2)_{\langle ab\rangle}+O(K^3),\qquad
\boxed{H_{abcd}=\tfrac32K_{\langle ab}K_{cd\rangle}+O(K^3)}.
\]

Thus \(H_{abcd}=\tfrac32Q_{\langle ab}Q_{cd\rangle}+O(K^3)\) is only a weak-anisotropy relation. A finite-temperature-quadrupole-only inversion cannot silently replace the exact inverse-square map.

Odd-mode power in an actual CMB sky is not a small violation to discard. It means this homogeneous uniform-source sector cannot be the whole sky; one must model a restricted deterministic component plus independent source/perturbation contributions, or reject the sector as a full explanation. No CMB data were examined here.

## 6. Einstein dynamics and what a quadrature actually buys

Let \(L^i{}_j=\tfrac12h^{ik}\dot h_{kj}\), \(H=\operatorname{tr}L/3\), and \(\sigma=L-HI\). For Bianchi I, the tracefree mixed spatial Einstein equation yields

\[
\boxed{\dot\sigma^i{}_j+3H\sigma^i{}_j=P^i{}_j,
\qquad P^i{}_j=\frac{8\pi G}{c^2}\pi^i{}_j}.
\]

Here \(\pi\) is anisotropic stress in pressure/energy-density units, so both sides have units \(\mathrm{s}^{-2}\). Mixed-coordinate components, or the equivalent properly transported physical components, are essential: coordinate covariant components cannot be differentiated as if the metric were constant. A quick direct derivation is \((R^i{}_j)_{\rm TF}=c^{-2}(\dot\sigma+3H\sigma)^i{}_j\).

If total \(\pi=0\), then \(a^3\sigma\) is constant. The shear axes are fixed, so the coaxial bridge follows. Setting \(a_o=1\),

\[
I=\int_{t_*}^{t_o}a(t)^{-3}dt
 =\int_{a_*}^{1}\frac{da}{a^4H(a)},\qquad
K=I\sigma_o,\qquad\boxed{\sigma_o=K/I}.
\]

This requires one scalar background quadrature **if the background \(a(t)\) or \(H(a)\) is supplied**. It does not derive the background, matter content, emission time, or stress assumptions from the temperature sky. The Friedmann constraint includes shear energy; a self-consistent large-shear background cannot be borrowed unchanged from isotropic FLRW. With standard \(\sigma^2=\tfrac12\sigma:\sigma\), the constraint is \(3H^2=8\pi G\rho/c^2+\Lambda c^2+\sigma^2\), for \(\rho\) in energy-density units.

For a sourced **coaxial** history, define \(P(t)=8\pi G\pi(t)/c^2\). Integration from the observation endpoint gives

\[
\sigma(t)=a(t)^{-3}\left[\sigma_o-\int_t^{t_o}a(s)^3P(s)ds\right],
\]

and switching the integration order gives

\[
\boxed{K=I\sigma_o-J},\qquad
J=\int_{t_*}^{t_o}a(s)^3P(s)
\left[\int_{t_*}^{s}a(t)^{-3}dt\right]ds.
\]

If \(\|P(s)\|_F\le p(s)\), define the positive kernel integral \(J_{\max}\) by replacing \(P\) with \(p\). Then

\[
\boxed{\|\sigma_o-K/I\|_F\le J_{\max}/I}.
\]

This is a constructive stress-budget uncertainty envelope, not a unique dynamical inversion. The tensor/source restrictions must be retained when using it; the same ordinary integral is not justified for arbitrary noncommuting history.

An exact algebraic toy check is \(t\in[1,2]\), \(a=(t/2)^{2/3}\), and constant \(P=C\): \(I=2\), \(J=5C/6\), hence \(K=2\sigma_o-5C/6\). Time units are inherited from the chosen toy time unit.

### CMB backreaction caveat

An initially isotropic **gravitating**, freely streaming photon gas generally develops anisotropic stress when the expansion is anisotropic. With radiation constant \(a_R=\pi^2k_B^4/(15\hbar^3c^3)\),

\[
\rho_\gamma=a_R\langle T^4\rangle,\qquad
\pi^\gamma_{ab}=a_R\langle T^4n_{\langle a}n_{b\rangle}\rangle.
\]

In the weak endpoint sector this gives

\[
\pi^\gamma_{ab}=-(8/15)\rho_\gamma K_{ab}+O(K^2).
\]

Thus \(\pi_{\rm total}=0\) is not generally exact for self-gravitating collisionless CMB plus otherwise isotropic matter. Consistent uses are test radiation on a prescribed background, a stated late-time negligible-radiation approximation, or an explicit total-stress budget/cancellation model. Homogeneity lets radiation stress be evaluated by angular integrals of the endpoint distribution, but a full Einstein–radiation evolution still requires additional dynamics unless an analytic family is selected.

## 7. Retaining the MES percentage motivation

Use the parent’s declared pure-shear pilot variables, without redefining the source’s MES statistics:

\[
\Sigma=\sigma_o/H_o,\qquad x_\sigma=\operatorname{tr}\Sigma^2/6.
\]

With the source-conditional norm bound

\[
\|\sigma\|_F/\theta\le B_\sigma,
\quad B_\sigma=\tfrac53\epsilon_1+3\epsilon_2+\tfrac37\epsilon_3,
\quad\theta=3H,
\]

one has \(U_\sigma=\tfrac32B_\sigma^2\). For \(U_\sigma>0\), retain the signed tensor as well as its scalar percentage:

\[
A_\sigma=\frac{\Sigma}{\sqrt{6U_\sigma}},\qquad
F_\sigma=\operatorname{tr}A_\sigma^2=x_\sigma/U_\sigma.
\]

Under the zero-stress/supplied-background bridge,

\[
A_\sigma=\frac{K}{H_oI\sqrt{6U_\sigma}},\qquad
F_\sigma=\frac{\operatorname{tr}K^2}{6H_o^2I^2U_\sigma}.
\]

The percentage is \(100F_\sigma\%\) only relative to the declared MES ceiling. It is not a measured matter fraction or cosmic energy composition. The bound gives \(F_\sigma\le1\) only when its complete source assumptions hold. Unknown \(\epsilon_i\), unknown background/stress history, and unknown primordial source statistics remain explicit unknowns. \(A_\sigma\) preserves signs and eigenframe; reporting only \(F_\sigma\) discards the very morphology sought in this program. For \(U_\sigma=0\), the normalized tensor/ratio are undefined and the bound must instead be interpreted directly.

## 8. Two constructive alternatives beyond the endpoint sector

### A. Weak inhomogeneous transport with finite source moments

Choose a stated near-FLRW, synchronous, geodesic-observer perturbative sector,

\[
h_{ij}(t,\mathbf x)=a^2(t)[\delta_{ij}+2b_{ij}(t,\mathbf x)],\qquad\|b\|\ll1.
\]

For a uniform background temperature and a specified thin source surface, evaluating the first-order redshift along the unperturbed straight conformal ray gives

\[
\Theta_o(\mathbf n)=\Theta_*(\mathbf x_*(\mathbf n),\mathbf n)
-\int_{t_*}^{t_o}\dot b_{ij}(t,\mathbf x_o-\mathbf n\chi(t))n^in^jdt
+\hbox{specified endpoint/observer terms},
\]

where \(\chi(t)=\int_t^{t_o}c\,ds/a(s)\) and the sign of \(\mathbf n\) is fixed consistently as a propagation direction. This follows from the exact redshift transport identity at first order; source and observer terms must be retained for a gauge-invariant observable. Lensing of a perfectly uniform zeroth-order sky first affects its anisotropy at higher order.

Expand \(b_{ij}=\sum_Ac_Af_A(t)S^A_{ij}(\mathbf x)\) in a **declared finite physical family**. Precompute the line integrals analytically or by ordinary quadrature, and obtain \(\Theta_{\ell m}=\sum_AR_{\ell m,A}c_A+s_{\ell m}\). Fourier spatial templates give familiar spherical-Bessel angular kernels; spatial variation permits odd modes and more general morphology. Rank/null-space analysis of \(R\), with source nuisance columns, directly tests which signed coefficients and MES-normalized fractions are identifiable.

This is broader than homogeneous Bianchi I and avoids ODE/PDE solvers **only because the time/spatial basis is supplied**. It is not a numerical-free solution for arbitrary perturbation dynamics or for the Boltzmann hierarchy. A valid application needs a bound on omitted \(O(b^2)\) terms, a declared source model, and analytic field-equation/constraint checks for any interpretation as a physical cosmology. Current status: constructive derived linear response; no finite basis selected or fitted.

### B. Local cosmography to measure present kinematics directly

For a general smooth observer congruence in an inhomogeneous spacetime, a local redshift–distance expansion supplies an independent current-kinematics channel. For an outward sightline \(\mathbf n\), physical acceleration \(\mathbf a\), and \(H=\theta/3\),

\[
\mathcal H_o(\mathbf n)=H_o-\mathbf a_o\!\cdot\!\mathbf n/c
+\sigma_{o,ab}n^an^b,\qquad
D_L(z,\mathbf n)=\frac{cz}{\mathcal H_o(\mathbf n)}+O(z^2).
\]

(The acceleration dipole reverses if directions are defined along photon propagation.) The STF inverse of the fitted local slope is

\[
H_o=\langle\mathcal H_o\rangle,\quad
\mathbf a_o/c=-3\langle\mathcal H_o\mathbf n\rangle,\quad
\sigma_{o,ab}=\frac{15}{2}\langle\mathcal H_on_{\langle a}n_{b\rangle}\rangle.
\]

This measures present shear without assuming a shear decay history; it can feed \(A_\sigma,F_\sigma\) directly, while CMB morphology independently constrains the long-baseline integrated response. It does not predict the CMB from local data. Vorticity does not enter the leading symmetric radial slope and needs additional observables. Required limitations are the local-series regime, redshift/distance precision, peculiar motions, observer-frame definition, and higher-order gradients/curvature.

This route is already supported by general cosmographic literature and is a program choice, not claimed new. It preserves the MES aim while making a more local inverse problem measurable without integrating a cosmological ODE.

## 9. Primary-source evidence and novelty ceiling

| Source read | Exact scope supporting this note | Relation |
|---|---|---|
| [Fleury, Pitrou & Uzan, *Light propagation in a homogeneous and anisotropic universe*, PRD 91, 043511 (2015), arXiv:1410.8473](https://arxiv.org/pdf/1410.8473), §II Eqs. (2.7)–(2.9), §IV.A Eqs. (4.1)–(4.5), pp. 2, 4 | Fixed-axis Bianchi I, conserved covariant spatial wave momenta, exact endpoint redshift, conformal-time shear equation; also distinguishes full optical/Jacobi propagation | supports; limits forward novelty |
| [Koivisto & Mota, *Anisotropic Dark Energy: Dynamics of Background and Perturbations*, JCAP 06 (2008) 018, arXiv:0801.3676](https://arxiv.org/pdf/0801.3676), §4.1 Eqs. (70), (72)–(74), pp. 21–23 | Exact diagonal redshift and \(T=T_*/(1+z)\) under uniform source temperature; accumulated-expansion degeneracy | supports; limits forward novelty |
| [Heinesen, *Multipole decomposition of the general luminosity distance “Hubble law”*, arXiv:2010.06534](https://arxiv.org/pdf/2010.06534), Eqs. (3.12), (4.1), §4–5 | General spacetime local directional Hubble parameter and finite multipole cosmographic expansion | supports alternative B; limits novelty |
| Supplied optical files 01–04, read in full | Separation of timelike shear, null optical shear, image shear, and CMB STF moments; exact energy/direction transport and uniform-source endpoint law | supports definitions and inverse-target separation |

The general matrix endpoint form and the explicit moment calculation were independently derived here. The inspected external passages do not establish priority of the moment-inversion display. Parent source reading indicates the internal ideal quadratic inverse is already present. No exhaustive novelty search, general-theory completeness, or observational success is claimed.

## 10. Executed checks and remaining scope

A deterministic Python angular quadrature was actually run using 90 Gauss–Legendre polar nodes and 180 uniform azimuths. No ODE/PDE/Boltzmann solver was called. For a rotated SPD matrix with eigenvalues \((0.55,1.15,1.9)\):

- maximum entrywise error in the exact inverse: \(4.82\times10^{-14}\);
- a test \(\ell=4\) projection of \(Y\): \(-2.96\times10^{-16}\);
- the corresponding normalized \(T\) projection: \(2.5204\times10^{-3}\), demonstrating that finite-temperature \(\ell=4\) is generally nonzero.

For \(K=\varepsilon R\,\mathrm{diag}(-0.7,-0.1,0.8)R^T\), \(\varepsilon=0.1,0.03,0.01\), the norms of the second-order quadrupole residual divided by \(\varepsilon^3\) were approximately \(0.12755,0.12757,0.12754\); a test rank-four contraction behaved as \(O(\varepsilon^3)\). These are synthetic arithmetic checks of the derived formulas, not data validation or evidence for a cosmological model.

Unresolved: source and nuisance statistics, physical stress history, background closure for a large-anisotropy solution, mask/noise inference, MES epsilon determination, and an independent final decision review. The present deliverable completes the assigned derivation and candidate comparison only.
