# Finite optical inverses and the error radius required for a shear constraint

## Abstract

A local distance law encodes expansion, acceleration and shear, but a catalogue measures that law through selected directions and nuisance projections. We compose these operations and derive the exact identifiable sector of the resulting finite linear response. Its inverse is a set: measurement and response errors determine a residual-compatible image, while the response kernel remains free. We give its support function, a stable inverse bound, and an explicit tensor ellipsoid with an additional bounded response term. For the complete positive angular magnitude field, normalized exponentiation instead gives an exact intercept-independent inverse; a uniform field error yields a finite bound on the recovered dipole and shear. These two inverses have different domains. A retained CF4 calibration quotient illustrates the finite construction with five dimensionless tensor coordinates, norm 0.0326568018932, and principal values approximately −0.0237272, 0.00132795 and 0.0223992. Conditional shear bounds become positive only below the apparent tensor norm. We show their dependence on an assumed response-error radius and Hubble normalization, retaining the tensor region and the physical sectors absent from the local slope.

## 1. What the local distance slope contains

The first distance coefficient is a directional rate. Its physical content depends on the source congruence and observer, while its recovery depends on how the directions and distances were sampled. A finite tensor estimate therefore poses two questions: which combinations survive the observation operator, and which physical states remain compatible with its errors? We answer these questions with a composed response and a set-valued inverse.

General luminosity-distance cosmography expresses the local coefficients through finitely many kinematic multipoles [Heinesen2021]. Observer transformations must also be carried through the distance and redshift observables [Maartens2024]. We use the same-congruence local law and logarithmic remainder established in the companion optical construction [QOMethods]. Our finite result retains the sampling and nuisance operators before attempting an inverse. Its error regions are deterministic sets unless a joint sampling law is explicitly supplied.

Use signature \((-+++)\), proper length \(s=c\tau\), and a unit timelike congruence \(u^au_a=-1\). Let \(n\) point from observer to source, with past-directed null direction \(\ell=-u+n\). In the orthonormal rest space at the observation event,

\[
 \nabla_a u_b=-u_a A_b/c^2+(Hh_{ab}+\sigma_{ab}+\omega_{ab})/c,
 \qquad h_{ab}=g_{ab}+u_au_b .\tag{1}
\]

Here \(H,\sigma,\omega\) have units of inverse time and \(A\) of length per time squared. Since \(\ell^a\ell^b\omega_{ab}=0\),

\[
 \mathcal H_u(n)=c\ell^a\ell^b\nabla_a u_b
 =H-A\cdot n/c+\sigma:nn,\qquad
 d_L(z,n)=\frac{cz}{\mathcal H_u(n)}+O(z^2).\tag{2}
\]

Equation (2) assumes smooth emitters and an observer following this congruence, with a regular local geometric-optics distance expansion. The acceleration sign follows from our direction convention. Finite-distance peculiar motion, frame changes and calibration enter the application response separately.

For \(H>0\), define the dimensionless vector and STF tensor

\[
 d=-A/(cH),\quad S=\sigma/H,\quad
 q_\theta(n)=d\cdot n+S:nn,\quad \theta=(d,S),\quad
 \kappa=5/\ln10 .\tag{3}
\]

The local angular magnitude field is

\[
 f_\theta(n)=\lim_{z\downarrow0}5\log_{10}
 \frac{d_L(z,n)}{cz/H}=-\kappa\log[1+q_\theta(n)],
 \qquad \inf_n[1+q_\theta(n)]>0 .\tag{4}
\]

The ratio has a finite limit even though each magnitude diverges. The absolute scale \(H\) is absent from (4). Multiplying \((H,A,\sigma)\) by the same positive constant preserves \((d,S)\) and this angular field.

## 2. An inverse for the complete angular field

Let \(\langle\cdot\rangle\) denote normalized full-sphere integration. The following inverse requires the complete field and this measure.

**Proposition 1 (intercept-independent inverse and a finite field-error bound).** For any constant intercept \(b\), set

\[
 r_f(n)=\frac{e^{-(f_\theta(n)+b)/\kappa}}
                    {\langle e^{-(f_\theta+b)/\kappa}\rangle} .\tag{5}
\]

Then \(r_f=1+q_\theta\), and

\[
 d_i=3\langle r_fn_i\rangle,\qquad
 S_{ij}=\frac{15}{2}\langle r_f(n_in_j-\delta_{ij}/3)\rangle .\tag{6}
\]

Suppose a complete perturbed field is \(f_\theta+b+u\), with \(\|u\|_\infty\le\delta\), and \(\|q_\theta\|_\infty\le\epsilon<1\). Apply (5)–(6) to that field to obtain \((\widetilde d,\widetilde S)\). Then

\[
 |\widetilde d-d|\le\sqrt3 B,\qquad
 \|\widetilde S-S\|_F\le\sqrt{15/2}B,\qquad
 B=(1+\epsilon)(e^{2\delta/\kappa}-1).\tag{7}
\]

*Proof.* Trace freedom and spherical symmetry give \(\langle q_\theta\rangle=0\), so the denominator in (5) is exactly \(e^{-b/\kappa}\). The identities \(\langle n_in_j\rangle=\delta_{ij}/3\) and \(\langle n_in_jn_kn_l\rangle=(\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk})/15\) prove (6). Write \(r=1+q_\theta\). For the perturbed field,

\[
 \frac{\widetilde r}{r}=
 \frac{e^{-u/\kappa}}{\langle r e^{-u/\kappa}\rangle}
 \in[e^{-2\delta/\kappa},e^{2\delta/\kappa}].\tag{8}
\]

The denominator is an average with positive normalized weight \(r\), which proves this interval. Hence \(\|\widetilde r-r\|_2\le B\) in normalized spherical \(L^2\). Orthogonal harmonic projection cannot increase that norm. A dipole has squared spherical norm \(|d|^2/3\), and an STF quadrupole has squared norm \(2\|S\|_F^2/15\). Applying these identities to the two projected differences proves (7). A constant \(u\) cancels exactly, although the uniform bound does not exploit that special case. \(\square\)

This is also an injectivity result: two complete fields differing only by an intercept have the same \(d,S\). Replacing the field by a truncated fit introduces the omitted field as an additional \(u\); replacing the sphere by selected directions changes the integration operator. Without a bound on those changes, exponentiating a noisy low-order map does not inherit Proposition 1.

## 3. Sampling, nuisance removal and the optical response

Let \(\mathcal S\) be a specified finite sampling operator from angular fields to \(m\) magnitude coordinates. Point evaluations and normalized, possibly signed, window averages are examples. We require each row to have finite total variation \(\ell_i\), so \(|(\mathcal S g)_i|\le\ell_i\|g\|_\infty\). Let \(N\beta\) be a finite linear nuisance family in those same coordinates and let \(W\) be a nonsingular working whitening matrix. Using \(W\) as a metric imposes no stochastic law. Define

\[
 U=WN,\qquad P_N=I-UU^+,\qquad
 z=P_NWy,\qquad
 \Phi(\theta)=P_NW\mathcal S f_\theta .\tag{9}
\]

The superscript \(+\) denotes the Moore–Penrose inverse. Since \(P_NWN=0\), the observation equation becomes

\[
 y=\mathcal S f_\theta+N\beta+e_0,
 \qquad z=\Phi(\theta)+P_NWe_0 .\tag{10}
\]

This is the composed nonlinear map. Its exact equivalence relation is \(\theta\sim\theta'\) when \(P_NW\mathcal S(f_\theta-f_{\theta'})=0\). Global injectivity of (5) does not establish injectivity of (9).

To expose a constructive finite inverse, choose Frobenius-orthonormal coordinates for \(S\), and write \(V\theta=q_\theta\). In the domain \(\|q_\theta\|_\infty\le\epsilon<1\),

\[
 f_\theta=-\kappa V\theta+R_1(\theta),\qquad
 \|R_1(\theta)\|_\infty\le
 b_1(\epsilon):=\frac{\kappa\epsilon^2}{2(1-\epsilon)} .\tag{11}
\]

Indeed, the tail of \(\log(1+q)\) after its linear term has absolute value at most \(\sum_{k\ge2}\epsilon^k/k\le\epsilon^2/[2(1-\epsilon)]\). Set

\[
 A=-\kappa P_NW\mathcal S V,\qquad
 z=A\theta+e,\quad
 e=P_NW[e_0+\mathcal S R_1(\theta)].\tag{12}
\]

If \(e_0\in\mathcal E_0\), a uniform finite outer error region is

\[
 \mathcal E=P_NW\mathcal E_0\;\oplus\;
 P_NW\prod_{i=1}^m[-\ell_i b_1,\ell_i b_1].\tag{13}
\]

For a compact set \(E\), write \(h_E(a)=\sup_{e\in E}a^{\mathsf T}e\). Equation (13) has the computable support

\[
 h_{\mathcal E}(a)=h_{\mathcal E_0}(W^{\mathsf T}P_Na)
 +b_1\sum_i\ell_i|(W^{\mathsf T}P_Na)_i| .\tag{14}
\]

The optical tail is correlated across directions and depends on \(\theta\). The box in (13) deliberately enlarges its image; (14) is exact for that outer set. The exact nonlinear feasible set instead retains the dependence,

\[
 \Theta_{\rm nl}(z)=
 \{\theta:\inf_n(1+q_\theta)>0,\quad
 z-\Phi(\theta)\in P_NW\mathcal E_0\}.\tag{15}
\]

On the stated \(\epsilon\) domain, (12)–(13) contain (15). A fit of only five shear columns is obtained by placing the chosen dipole and intercept columns in \(N\). Their linear contribution is then removed, while their nonlinear coupling remains in \(R_1\). This separation prevents nuisance projection from being mistaken for removal of every physical effect of those fields.

## 4. The exact finite identifiable sector

We now analyze the declared linear error model \(z=A\theta+e\), \(e\in\mathcal E\), without imposing an additional physical restriction on \(\theta\). Let

\[
 A=U_r D_r V_r^{\mathsf T},\qquad
 P_A=AA^+,\qquad P_I=A^+A=V_rV_r^{\mathsf T},\qquad
 \mathcal E_z=\{e\in\mathcal E:(I-P_A)(z-e)=0\}.\tag{16}
\]

Only positive singular values occur in \(D_r\). A numerical rank policy is a separately recorded approximation to this exact algebraic definition.

**Theorem 2 (finite inverse and support).** The model is feasible exactly when \(\mathcal E_z\ne\varnothing\). Its full parameter set is

\[
 \Theta_{\rm lin}(z)=
 \{A^+(z-e)+k:e\in\mathcal E_z,\ k\in\ker A\}.\tag{17}
\]

A linear carrier \(J\theta\) is determined by the noiseless observation for all \(\theta\) precisely when \(\ker A\subseteq\ker J\). For such a carrier, its error image is compact when \(\mathcal E\) is compact, and

\[
 h_{J\Theta_{\rm lin}}(a)
 =a^{\mathsf T}JA^+z+
 h_{\mathcal E_z}(-A^{+\mathsf T}J^{\mathsf T}a).\tag{18}
\]

We use the extended-real convention \(h_{\varnothing}(a)=-\infty\); thus an empty feasible set has an empty carrier image with support \(-\infty\). If \(\mathcal E_z\ne\varnothing\) and \(J^{\mathsf T}a\) has a nonzero component in \(\ker A\), the support in that direction is \(+\infty\). For \(r>0\), if \(\|e\|_2\le r_e\), the identifiable coordinate obeys

\[
 \|P_I\theta-A^+z\|_2\le\frac{r_e}{s_{\min}(A)} .\tag{19}
\]

*Proof.* If \(z-e=A\theta\), multiplication by \(I-P_A\) gives the compatibility condition in (16), and multiplication by \(A^+\) gives \(P_I\theta=A^+(z-e)\). The remaining component is in \(\ker A\), proving necessity in (17). Conversely, every vector in (17) satisfies \(A\theta=P_A(z-e)=z-e\). In the noiseless model two parameters have the same image exactly when their difference is in \(\ker A\); applying \(J\) proves the stated criterion. Under that criterion, the kernel term vanishes and maximizing the affine functional of \(e\) gives (18). Compactness follows because \(\mathcal E_z\) is a closed subset of a compact set. When \(\mathcal E_z\ne\varnothing\), choose a feasible \(\theta_0\in\Theta_{\rm lin}(z)\). A nonzero kernel component provides \(k\in\ker A\) with \(a^{\mathsf T}Jk>0\); then \(\theta_0+tk\) remains feasible for every \(t\ge0\), and \(a^{\mathsf T}J(\theta_0+tk)\to+\infty\), proving the infinite-support statement. Finally \(P_I\theta-A^+z=-A^+e\), and \(\|A^+\|_2=1/s_{\min}(A)\), which proves (19). \(\square\)

For \(A=0\), every parameter is unresolved whenever \(z\in\mathcal E\); (19) is undefined. If a physical domain \(\Theta_0\) is added, its feasible set is \(\Theta_{\rm lin}\cap\Theta_0\). Domain restrictions can bound kernel directions, but that information comes from the domain. The exact support is then that of the intersection, with (18) providing an outer bound. Likewise, the rank of the tangent \(A=D\Phi(0)\) does not assert global identifiability of (15).

Residual compatibility matters. Sending every \(e\in\mathcal E\) through \(A^+\) while ignoring \((I-P_A)(z-e)=0\) can report a nonempty inverse for an inconsistent observation. This is the finite counterpart of carrying the unobserved angular field in Proposition 1.

### An explicit tensor image

For a fully identified five-coordinate STF estimate, suppose a chosen coefficient-error model is

\[
 \widehat b=b+C^{1/2}u+Gv,\qquad
 \|u\|_2\le\rho,\quad \|v\|_2\le\eta,\qquad C\succeq0.\tag{20}
\]

Here \(C\) is an adopted dimensionless shape matrix, \(G\) maps the response-error coordinates to coefficient space, and both radii are specified externally. Under this independent product of error balls, the exact coefficient region and support are

\[
 \mathcal B=\widehat b+C^{1/2}B_\rho\oplus GB_\eta,
 \qquad h_{\mathcal B}(a)=a^{\mathsf T}\widehat b
 +\rho\sqrt{a^{\mathsf T}Ca}+\eta\|G^{\mathsf T}a\|_2 .\tag{21}
\]

The error sets are centrally symmetric, explaining the plus sign. The support follows by maximizing independently over \(u,v\); Cauchy–Schwarz attains each maximum, including the zero-response cases by continuity. An arbitrary joint error region need not have this product structure. With an orthonormal STF basis \(T_\alpha\), the tensor is \(S=\sum_\alpha b_\alpha T_\alpha\), and a tensor functional \(L:S\) uses \(a_\alpha=L:T_\alpha\) in (21). The full tensor region is preserved by this isometry.

A sufficient Frobenius radius containing (21) is

\[
 r_Q=\rho\sqrt{\lambda_{\max}(C)}+\eta\|G\|_2.\tag{22}
\]

It discards anisotropic shape and can be conservative. If a fixed Gaussian joint coefficient law is additionally justified, one may select a quantile for \(\rho\); the deterministic shape matrix alone supplies no coverage. Shared calibration and cross-window dependence belong in that joint law or joint error region.

## 5. The retained CF4 quotient and conditional shear bounds

The retained calibration quotient fits a five-coordinate apparent directional-rate tensor using magnitude residuals. Its design already contains the optical conversion,

\[
 y_i=\mathrm{DMzp}_i-\mu_{{\rm ref},i},\qquad
 B_{i\alpha}=-\kappa(n_i^{\mathsf T}T_\alpha n_i),\qquad
 \widehat b=Ky .\tag{23}
\]

The coefficient \(\widehat b\) is dimensionless, while \(y\) has magnitude units and \(K\) inverse magnitude units. The basis is

\[
 T_0=\frac{\operatorname{diag}(1,-1,0)}{\sqrt2},\quad
 T_1=\frac{\operatorname{diag}(1,1,-2)}{\sqrt6},\quad
 T_{xy},T_{xz},T_{yz}=\frac{e_ie_j^{\mathsf T}+e_je_i^{\mathsf T}}{\sqrt2} .\tag{24}
\]

Thus \(\|\widehat S_{\rm app}\|_F=|\widehat b|\). The source uses J2000 Cartesian directions and a fixed reference cosmology. Its 35,970 selected rows include 944 mixed-support rows saturated by the nuisance quotient; the corrected exact factor has 945 zero-leverage rows. The saved target numerical rank is five, with singular values between 186.248352167 and 279.226623496 in its working metric [CF4Retained]. This establishes survival of five apparent tensor directions in that finite design.

The retained matrix is

\[
 \widehat S_{\rm app}=\begin{pmatrix}
 -0.01737217048&0.00642017243&0.01454248664\\
 0.00642017243&0.00395564447&0.00563999318\\
 0.01454248664&0.00563999318&0.01341652601
 \end{pmatrix},\tag{25}
\]

with

\[
 t:=\|\widehat S_{\rm app}\|_F=0.03265680189321492,\qquad
 \lambda(\widehat S_{\rm app})=
 (-0.023727165269042373,\ 0.001327948995864026,\ 0.022399216273178365).\tag{26}
\]

The directional RMS is \(\sqrt{2/15}\,t=0.011924578035260817\). The full precision matrix and coordinates, rather than the rounded display (25), generate the numerical table and figures. The magnitude quadrupole \(Q_\mu\) is a different tensor: at leading order \(Q_\mu=-\kappa S\), with

\[
 \|Q_\mu+\kappa S\|_F\le\sqrt{15/2}\,
 \frac{\kappa\epsilon^2}{2(1-\epsilon)} .\tag{27}
\]

This follows by projecting (11) and using the quadrupole norm identity in Proposition 1. The conversion in (23) is already present in the CF4 producer. Dividing (26) by \(\kappa\) again would change its units convention and its physical scale.

**Proposition 3 (shear-radius frontier).** Suppose a response qualification on one common event, congruence and frame establishes

\[
 S=\sigma/H,\qquad
 \|S-\widehat S_{\rm app}\|_F\le r_Q,\qquad
 H\in[H_-,H_+],\quad 0<H_-\le H_+ .\tag{28}
\]

The radius must cover the applicable statistical, calibration, sampling, finite-redshift, peculiar-motion and frame-response errors. Then the dimensionless shear amplitude and dimensional shear rate satisfy

\[
 \frac{(t-r_Q)_+}{\sqrt6}\le
 \Sigma:=\frac{\|\sigma\|_F}{\sqrt6 H}
 \le\frac{t+r_Q}{\sqrt6},\tag{29}
\]

\[
 \frac{H_-(t-r_Q)_+}{\sqrt6}\le
 \frac{\|\sigma\|_F}{\sqrt6}
 \le\frac{H_+(t+r_Q)}{\sqrt6}.\tag{30}
\]

*Proof.* The triangle and reverse triangle inequalities give \((t-r_Q)_+\le\|S\|_F\le t+r_Q\). Divide by \(\sqrt6\) for (29) and multiply by a positive \(H\in[H_-,H_+]\) for (30). Over the unrestricted STF ball, the two norm endpoints are attained along \(\widehat S_{\rm app}\), or at zero if \(r_Q\ge t\). Independent endpoint choices for \(H\) attain the dimensional endpoints over the corresponding product set. Additional physical or correlated-error restrictions can narrow these intervals. \(\square\)

The lower endpoint is strictly positive exactly when \(r_Q<t\). The present retained products do not estimate this qualified radius. Figure 1 therefore shows a requirement on the error budget, with \(r_Q/t\) and \(r_H/H_*\) as assumed sensitivity coordinates. In (30), write \(H_\pm=H_*\pm r_H\), \(0\le r_H<H_*\), and divide the plotted dimensional shear rate by \(H_*\). No numerical Hubble rate is needed.

If the measured tensor were instead a dimensional rate \(\widehat Q_H\), with \(\|\sigma-\widehat Q_H\|_F\le r_{Q_H}\), the normalized bounds would be

\[
 \frac{(\|\widehat Q_H\|_F-r_{Q_H})_+}{\sqrt6 H_+}
 \le\Sigma\le
 \frac{\|\widehat Q_H\|_F+r_{Q_H}}{\sqrt6 H_-}.\tag{31}
\]

Equation (31) belongs to a different input convention. Applying its Hubble division to (26) would count the normalization twice. Ordered eigenvalues under (28) obey

\[
 |\lambda_i(S)-\lambda_i(\widehat S_{\rm app})|\le r_Q .\tag{32}
\]

This follows from the min–max characterization and \(\|S-\widehat S_{\rm app}\|_{\rm op}\le r_Q\). For example, the largest principal value is guaranteed positive by this bound only if \(r_Q<0.022399216273178365\). It refers to expansion relative to the local mean. Eigenvector directions require an additional gap-sensitive perturbation analysis.

Figure 2 retains more information than the ball in (29): it shows a two-coordinate projection of (21), using the saved working shape matrix with \(\rho=1\), \(G=I\), and selected assumed \(\eta\). The curves are deterministic images of those chosen sets. They have no assigned confidence level.

## 6. Tensor carriers and unresolved physical sectors

Let \(Z\) retain the tensor state, support and response parameters, rather than only its norm. A suitable optical carrier and its deterministic image are

\[
 x_\phi(Z)=(d,S,\omega/H,H,\text{other physical sectors}),\qquad
 x_\phi[\Theta]=\{x_\phi(Z):Z\in\Theta\}.\tag{33}
\]

For a finite linear model \(\Theta\) includes the kernel in (17); for the complete field, \(d,S\) are determined but \(H\) and vorticity remain unresolved. The local slope contains no antisymmetric velocity gradient, and the angular normalization removes the absolute expansion scale. Curvature, a matter-frame energy split and a temporal history are also absent. The signed comparator \(x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Omega_{k,\rm aniso}\) consequently remains incomplete when only the shear sector is bounded. Unmeasured terms are not assigned zero.

For a declared positive tolerance \(q_*\), one may form a policy score, for example

\[
 Q_\phi(Z)=\|S\|_F/q_*,\qquad q_*>0 .\tag{34}
\]

Its interval image follows from the tensor region. The denominator is a policy input, not a fitted significance. At zero tolerance, use an exact set constraint instead of defining a ratio. The remaining diagnostics require different inputs:

\[
 F_\nu(B)=\frac{\nu(B\cap D)}{\nu(D)},\quad 0<\nu(D)<\infty;
 \qquad \Pi_P(a)=P\{Q_\phi(Z)>a\};
 \qquad G_F=\mathcal G(F_1,\ldots,F_k).\tag{35}
\]

Occupancy \(F\) requires a support measure and a specified admissible set or sign-clean ceiling. Exceedance \(\Pi\) requires a named joint law. A depth functional \(G_F\) requires registered windows, their measures and shared dependence. Here \(x_\phi\) has an apparent measured tensor component and conditional physical image; \(Q\) is specified only after \(q_*\) is chosen; \(F,\Pi,G_F\) are undefined because the corresponding measure, law and depth functional have not been supplied. The saved working matrix does not supply these missing objects. A model-dependent probability pushforward belongs to HTT; the deterministic region can be reported as a MIO diagnostic.

## 7. Discussion

There are two useful inverses. A complete positive local magnitude field determines its dimensionless acceleration and shear after normalized exponentiation. A finite observation first passes through sampling and nuisance removal, leaving an identifiable subspace, a kernel and a residual-compatibility condition. Their error bounds answer different questions, so the full-field identity cannot be substituted into an incomplete map without controlling the missing field.

The retained CF4 quotient makes the error target concrete. Its apparent tensor norm is 0.0326568 in the producer's dimensionless convention. To obtain a positive lower shear bound through the stated response identity, a qualified common-event radius must lie below this scale. A supplied response region can be propagated with (18) or (21), retaining anisotropy and dependence before taking the simpler norm bounds. An absolute Hubble interval then converts a dimensionless shear range to a dimensional rate.

This construction isolates what an additional physical input must do: constrain the response error or a currently unresolved sector. It also permits a complete conditional inverse result while those stronger inputs remain unavailable. The attainable sets and their support functions are the methods result; the apparent tensor is its retained finite-data illustration.

## References for bibliography generation

- [Heinesen2021] A. Heinesen, “Multipole decomposition of the general luminosity distance ‘Hubble law’—a new framework for observational cosmology,” JCAP 05, 008 (2021), DOI 10.1088/1475-7516/2021/05/008, arXiv:2010.06534v2. https://arxiv.org/abs/2010.06534v2
- [Maartens2024] R. Maartens, J. Santiago, C. Clarkson, B. Kalbouneh and C. Marinoni, “Covariant cosmography: the observer-dependence of the Hubble parameter,” JCAP 09, 070 (2024), DOI 10.1088/1475-7516/2024/09/070, arXiv:2312.09875v3. https://arxiv.org/abs/2312.09875v3
- [QOMethods] “Sharp quadrupole–octupole chirality and the nonlinear local distance response,” retained companion methods manuscript, R32-01-QO-METHODS (2026), equations (20)–(24), (36), (38)–(39); repository source products/R32-01-QO-METHODS/science/MANUSCRIPT.md. This is a repository manuscript, not an asserted journal publication.
- [CF4Retained] Source-bound CF4 calibration-quotient sufficient statistics, EVIDENCE_MANIFEST.json and evidence/research/latest_results.json, retained release 25 October 2026, especially units_correction and cf4_calibration_quotient. Original numerical producer R28 at commit 71b272db893a92ec336c28164bc7efccf7c340b2; corrected interpretation bound to model SHA-256 843b19e464817d14455df68e9043a93cc71cc7449ab339052c3ddfe1c7298c19. These are retained numerical research products, not an independently calibrated physical error law.
