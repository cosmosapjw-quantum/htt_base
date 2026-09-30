# TEFF positive bridge: spectral data → certified observable and collision residuals

2026-09-30. Proposer supplement; independent review pending. No autonomous promotion. “Adopted” means a supplied identity is used on its stated domain, not that manuscript priority or journal acceptance has been established.

## 1. Sources and the constructive conclusion

The supplied papers by Jiwon Park, Myung-Ki Cheoun and Jubin Park are user manuscripts dated September 3, 2026:

* Paper I: Effective-Temperature Multipoles for Relativistic Kinetic States. I. Exact Information Budgets and Sharp Coarse-Graining Limits; 21 PDF pages; SHA-256 d014d58f5265a35c6cefa3a5a206fe1f04adfdae3269b225075c807c06ea4704.
* Paper II: Effective-Temperature Multipoles for Relativistic Kinetic States. II. Number–Energy Refinement and Velocity-Dressed Coarse-Graining Geometry; 23 PDF pages; SHA-256 299870d7174ed560393c87e8dd6193643a614e7a1185ab1be2c5c2dc73c9b5f9.

Identity is cross-referenced to ../ADDED_PDFS_MANIFEST.json. Extracted main text, appendices and references were inspected across I pp. 1–21 and II pp. 1–23. Equation-level attention concentrated on the table below. Massive chart/asymptotic material was read for scope and is not imported into a CMB assertion. Numerical archives were not executed, and manuscript numerical percentages are not independently validated here.

**Positive result:** additional spectral information can supply a finite explicit uncertainty set for selected radiation observables and specified collision moments without solving a Boltzmann hierarchy. Two routes are proved below:

1. A certified entropy budget plus an occupation envelope gives a joint moment-refined observable-error ellipsoid.
2. In a fixed common-shape thermal-mixture class, adding number to energy gives a computable cubic-width error bound for general smooth bandpass responses, extending II's power-moment estimator.

Both are type-free. They control radiation observables; a subsequent inverse must specify the geometric variables and the observation map.

| Inspected location | Formula used | Scope retained |
|---|---|---|
| I p. 2, (11)–(16) | Kinetic entropy and h''=1/[f(1+ξf)] | Convex divergence, not automatically probability KL |
| I pp. 4–5, (38)–(40), (52)–(59) | Radial lift and exact spectral/angular split | Stated finite-divergence domain, fixed observer |
| I pp. 9–10, (83)–(100), App. C pp. 18–19 | Common-shape probability mixtures and sharp support envelope | Fixed fugacity, normalization and support prior |
| I pp. 19–20, (D8)–(D18) | Observer-change bound | Requires positive patches and angular H¹ input |
| II pp. 2–5, (5)–(22), (24)–(38) | Number/energy inverse, nested budgets and BE boundary | BE regular range; Planck endpoint is one-sided |
| II p. 6, (53)–(57) | Moment-residual orthogonality and Fisher projection response | Infinitesimal formula extended conditionally below |
| II pp. 11–12, (107)–(118), App. D p. 20 | Angular cutoff entropy certificate | Printed theorem is MB/FD, not automatically BE |
| II pp. 13–14, (119)–(130), App. E pp. 20–21 | Sharp added-number intervals and cubic estimator | Same prior in both comparisons; MaxEnt can leave it |
| II p. 15 | Local momentum-space versus sky resolution | Propagation and instrument maps remain additional |

Paper II (25)–(26) distinguishes density units from Paper I's reference-cell normalization. Every term below uses one common measure and normalization.

## 2. Proposition A: finite-amplitude moment-refined error ellipsoid

At one event and one observer use the massless measure

$$d\nu=C E^2\,dE\,d\Omega.$$

Let f,g be admissible occupations and δ=f−g. Assume

$$D_H(f\Vert g)\le\varepsilon<\infty,\qquad
\int\phi_a\delta\,d\nu=0,\quad a=1,\ldots,m. \tag{A1}$$

For example, φ_a=E Y_lm are energy scores and φ_a=Y_lm are number scores. Write V=span{φ_a}. Suppose a known positive measurable weight W satisfies

$$
\sup_{z\ {\rm between}\ f(E,e),g(E,e)}z(1+\xi z)\le W(E,e)
\quad\hbox{a.e.} \tag{A2}
$$

Assume the target kernels K_j and retained scores lie in L²(W dν), and their observable integrals are finite. Then

$$
\left|\int K(f-g)d\nu\right|
\le\sqrt{2\varepsilon}\,
{\rm dist}_{L^2(Wd\nu)}(K,V). \tag{A3}
$$

For r_j=K_j−P_VK_j, set

$$
R_{ij}=\int W r_i r_j\,d\nu,\qquad
e_j=\int K_j(f-g)d\nu.
$$

The vector e satisfies the simultaneous deterministic certificate

$$
e\in{\rm range}(R),\qquad e^TR^\dagger e\le2\varepsilon. \tag{A4}
$$

Here R† is the Moore–Penrose inverse. Singular R is allowed: kernels in V have exactly zero residual.

**Proof.** The integral Taylor remainder and I (14) give

$$
d_h(f\Vert g)=\delta^2\int_0^1(1-t)h''(g+t\delta)\,dt
\ge{\delta^2\over2W}.
$$

At physical endpoints the same statement follows by a limit. Integrating gives ∫δ²/W≤2ε. Matching removes any v∈V from K, and weighted Cauchy–Schwarz proves (A3). Applying it to a linear combination of kernels gives

$$|a^Te|\le\sqrt{2\varepsilon\,a^TRa}\quad\hbox{for every }a.$$

Every null vector of R annihilates e; therefore e lies in range R. Substituting a=R†e proves (A4). This is a finite-amplitude result, not a Fisher linearization.

The underlying convexity/Cauchy–Schwarz and projection arguments are standard. The useful assembly is a common, moment-refined residual set compatible with TEFF's entropy budget and the photon endpoint. No priority claim is made.

### A photon-compatible envelope

A sufficient BE envelope is

$$
0\le f,g\le F_b(E)={1\over e^{bE}-1},\quad b>0,\qquad
W=F_b(1+F_b). \tag{A5}
$$

Near E=0, W=O(E⁻²), so W dν=O(dE dΩ). At high energy W decays exponentially. Bounded angular kernels times nonnegative powers of E consequently have finite weighted norms. A uniform bound on the occupation itself at the Planck endpoint is unnecessary.

A common-shape mixture with T≤T_max and nonpositive common log-fugacity satisfies (A5) with b=1/(k_B T_max). For a fitted thermochemical reference also verify β≥b and η≤0, or enlarge the envelope. T_max is additional prior information, not inferred from bolometric energy alone.

To apply the theorem, acquire: the retained moments and calibration; a valid occupation/tail envelope; an independently certified ε for the unknown shape or total divergence; and the actual channel kernels. Retained moments or the entropy of a fitted reference alone do not certify ε. Multi-frequency spectral constraints plus an explicit uncertainty class can supply it.

Number refinement decreases the true nested divergence by II (29)–(31), and enlarging V reduces the distance term. The two improvements may be combined only when one common envelope is valid and the divergence bounds are actually available.

For uncertain matching, every coefficient vector a gives instead

$$
|\Delta O_K|
\le\sqrt{2\varepsilon}\|K-a\cdot\phi\|_W
+|a\cdot\Delta m|. \tag{A6}
$$

A simultaneous confidence set for Δm supplies its support function in the final term. This separates deterministic kinetic error from measurement uncertainty.

### Collision moments and the subsequent kinematic inverse

Let L be a specified fixed linear collision operator with adjoint for dν. If L* K_j satisfies the weighted integrability assumptions, apply the same theorem with

$$
r_j=L^*K_j-P_V(L^*K_j),\qquad
e_j=\langle K_j,Lf-Lg\rangle.
\tag{A7}
$$

The resulting R gives exactly (A4) for the collision residual vector. If L* K belongs to V, its collision moment is determined exactly by the retained data. No time evolution is solved.

For illustration, explicitly define an elastic scalar angular-scattering model

$$
(Lf)(E,e)=\tau(E)\left[\int P(e,e')f(E,e')d\Omega'-f(E,e)\right],
\quad P={3[1+(e\cdot e')^2]\over16\pi}.
$$

The kernel is symmetric and normalized. Since P=(4π)⁻¹[1+P_2(e·e')/2], its harmonic eigenvalues are p_0=1, p_2=1/10, and p_l=0 otherwise. Thus

$$L^*[B(E)Y_{lm}]=\tau(E)(p_l-1)B(E)Y_{lm}.$$

For constant τ, retaining that spectral/angular moment exactly determines its collision contribution. For energy-dependent τ, add its weighted moment or use (A7). This is the explicitly declared unpolarized, elastic, fixed-scatterer-rest-frame model. It is not a guarantee for polarized or frequency-redistributing CMB transfer. Nonlinear collisions and unknown electron distributions need their own kernels and bounds.

For a subsequent linearized kinematic inverse y=Aq+e+noise, (A4) is a physically conditional joint residual set. It can be combined with an independently justified kinematic design matrix and noise set by profiling/projecting over e. It supplies neither the design matrix nor its rank. Independent per-channel bias bars would discard its shared constraints.

### Spacetime derivatives require a distinct input

An entropy budget at one spatial slice does not bound spatial/time derivatives. For example f_n(x,p)=g(p)+a sin(nx)q(p), with small fixed a and compactly supported q, can obey one common occupation envelope and a uniform entropy bound while ∂_x f_n(0,p)=anq(p). Choose q orthogonal to the retained moments to keep them fixed.

A positive sufficient replacement is an explicit horizontal-transport Fisher budget

$$\int{|\mathcal D_Xf|^2\over f(1+f)}\,d\nu\le J_X.$$

In a parallel local tetrad at the event, after controlling kernel and measure differentiation, a fixed stress kernel K then satisfies

$$
\left|\mathcal D_X\int Kf\,d\nu\right|
\le\sqrt{J_X}\left[\int K^2f(1+f)d\nu\right]^{1/2}.
$$

These derivative inputs can feed the GR energy-frame gap bound. They are additional spacetime information; static TEFF entropy or angular Fisher information does not supply them.

## 3. Proposition B: a cubic certificate for general thermal bandpass responses

Adopt exactly II (119)–(120): fixed statistics, one common admissible log-fugacity, fixed normalization, and a probability measure π of temperature ratios y∈[1−s,1+s], 0<s≤s₀<1. Retain

$$m_3=\int y^3d\pi,\qquad m_4=\int y^4d\pi.$$

Let ψ(y) be a calibrated single-temperature band response. For BE photons, for example,

$$
\psi(y)=C\int_0^\infty
{E^2K(E)\,dE\over \exp[E/(k_BT_*y)-\eta_0]-1}.
\tag{B1}
$$

Require ψ∈C³([1−s₀,1+s₀]). A bounded bandpass supported on a compact positive-energy interval suffices; wider kernels require a separate endpoint/tail domination check. The mixture observable is O=∫ψ(y)dπ.

Set

$$
c_3=\psi'(1)-{\psi''(1)\over3},\qquad
c_4={\psi''(1)\over4}-{\psi'(1)\over2},\qquad
c_0=\psi(1)-{\psi'(1)\over2}+{\psi''(1)\over12},
$$

and q(y)=c₀+c₃y³+c₄y⁴. Then the data-based estimator

$$\widehat O=c_0+c_3m_3+c_4m_4 \tag{B2}$$

obeys

$$
|O-\widehat O|
\le {s^3\over6}\,
\sup_{y\in[1-s_0,1+s_0]}
|\psi'''(y)-6c_3-24c_4y|. \tag{B3}
$$

**Proof.** The coefficients solve q(1)=ψ(1), q'(1)=ψ'(1), q''(1)=ψ''(1). Taylor's remainder bounds |ψ−q| by the right side of (B3). Integrate against the probability measure and use the measured moments.

For ψ(y)=y^p this reduces exactly to II (127):

$$
q(y)={(p-3)(p-4)\over12}
+{p(4-p)\over3}y^3+{p(p-3)\over4}y^4.
$$

Thus this extends the manuscript's power-moment cubic estimator to genuine frequency-band kernels. The mechanism is standard Hermite interpolation; sharp minimax optimality for every band kernel is not claimed.

Energy alone gives q_E(y)=ψ(1)−ψ'(1)/4+[ψ'(1)/4]y⁴, matching only value and first derivative. Its computable bound is

$$
|O-\widehat O_E|\le {s^2\over2}
\sup_{y\in[1-s_0,1+s_0]}|\psi''(y)-3\psi'(1)y^2|.
\tag{B4}
$$

The generally quadratic-to-cubic gain compares the same prior and target. Special kernels in the retained span are exact; special data at a feasibility boundary may yield faster shrinkage.

For moment uncertainties |Δm₃|≤d₃, |Δm₄|≤d₄, add |c₃|d₃+|c₄|d₄ to (B3). If ψ_min>0 on the support, division by ψ_min gives a valid relative error. Signed angular multipoles require absolute or covariance-scaled errors.

For a sky observable, apply the estimator raywise and integrate its absolute error against the absolute beam/angular weight. Additional radial data do not identify an unmeasured angular mode. Spatial/line-of-sight mixing must be inside the declared mixture and observation model.

### Sharp methods already available in the manuscripts

II Proposition 14, (121)–(126), gives exact attainable [L_p,U_p] for p>4 under the fixed support and (m₃,m₄), with extremizers on {a,u} and {d,b}. App. E (E3)–(E5) gives elementary polynomial certificates for p=5,6. Its relative-minimax estimate is 2L_pU_p/(L_p+U_p), with error (U_p−L_p)/(U_p+L_p). These are constructive classical moment-space methods, acknowledged as such in the manuscript.

II (129)–(130) also shows why the number–energy MaxEnt reference is not automatically a fixed-prior rate estimate: its changed fugacity can move it outside the original mixture class and its sharp interval. Use the interval predictor or (B2) for the declared observable and loss; keep MaxEnt as the entropy-selected reference.

## 4. Disposition and positive acquisition protocol

| Item | Proposer disposition | Remaining input/check |
|---|---|---|
| Static entropy split and regular number–energy inversion | Adopted conditionally | Same measure, observer and admissible BE branch |
| Manuscript sharp p=5,6 added-number intervals | Adopted conditionally | Preserve common shape/fugacity/support; do not relabel kernels as CMB |
| Proposition A, including joint collision ellipsoid | Candidate, derived | Independent review; certified ε, W, kernels and medium |
| Proposition B bandpass cubic certificate | Candidate, derived | Independent review; calibrated ψ derivatives, moment uncertainties, support |
| Static entropy implies spacetime derivative bound | Hold / false without extra hypotheses | Explicit transport derivative information J_X |
| Full nonlinear CMB collision or parameter-identifiability claim | Hold | Separate physics, observation map and inverse-rank evidence |

The practical positive sequence is: declare target frequency/angular kernels; retain number plus energy at measured ranks; add calibrated bands aligned with K−P_VK or L* K−P_VL* K; certify support/envelope and, for route A, the entropy budget; propagate the joint residual set into the kinematic/statistical inverse. This targets the information actually needed by the observable without enlarging an irrelevant hierarchy.

No actual dataset, heavy runtime suite, external repository or autonomous promotion was used. Priority of the new assembly remains unresolved; the analytic candidates are ready for independent review.
