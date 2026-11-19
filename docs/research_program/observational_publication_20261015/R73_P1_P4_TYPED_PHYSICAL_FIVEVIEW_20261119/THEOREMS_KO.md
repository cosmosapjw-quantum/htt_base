# R73 · P1–P4 물리적 5뷰 도구: x → Q, Π, F, G_F의 계산 가능한 정리

Date 2026-11-19 KST. Repo cosmosapjw-quantum/htt_base, branch research/r69-observable-physics-bridges-20261118; pinned input HEAD 06886d0d4038cabe75d2270c69c19b89722f698a.
Scope: a NEW bounded cross-paper **theory-and-validation research package**, not a new P5/R74 paper loop, and no unsolicited ten-stage gate ceremony. All original P1–P6 science/42 DAG nodes unchanged. Publish real bounded substantive checkpoints to existing research branch as owner requested, no other untracked/dirty files. Native subagent unavailable (NOT_RUN), independent source math + Wolfram/SymPy checks recorded separately.

## 0. Semantic contract and exact sources

Reuse R68 THEOREM/typed fiveview \`R68_FIVEVIEW_GEOMETRIC_RECONSTRUCTION_20261118/THEORY_AND_PROOFS_KO.md\` and R69 \`R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/X_TO_FIVEVIEW_PHYSICAL_RESPONSE_KO.md\`, their actual data atlas and source corrections. Reuse R69_P1_FIVEVIEW_PHYSICS_LOOP2 for signed STF sky shape; R70-P2 for collisionless moment nonclosure; R71-P3 for source-computed H_D and a 39/39 rank with weak nonlinear domain certification; R72-P4 for observer boost/selected finite-bin kappa and same-source NVSS covariance.
Here \(\mathcal E=(P(y\mid\theta,\psi),{\cal T}_{GR/kinetic/optical},{\cal O}_{source},C,{\cal K},\mu)\) is a *typed experiment*. \(x\) is a signed field or vector together with units/frame/source/covariance, **not necessarily a five-component vector**. Its four dependent views:
\(Q_{\mathcal K}(x)=\inf\{t>0:x\in t\mathcal K\}\) for a convex physical body (or \`Q_stat\` for a named noise reference),
\(\Pi_{\mathcal L}=\Pr_{\mathcal L}[T(Y)\ge T(y_{\mathrm{obs}})]\) for a named experiment-matched null,
\(F_{\mu,\mathcal K}(E_x)=\mu(E_x\cap\mathcal K)/\mu(\mathcal K)\) for a specified **finite measure**,
\(G_F=F_j-F_i\) only for comparable physically transported source measure/event and joint law.
A different, intentionally named \(F_{\mathcal E}(\mathcal K):=\mu(\mathcal E\cap\mathcal K)/\mu(\mathcal E)\) uses *confidence-region* volume normalization and is NOT the same F as \(F_{\mu,\mathcal K}(E)\). It is still a valid typed occupancy if explicitly registered as such, but no Bayesian posterior/physical truth probability follows. Full-sky signed quadrupole positive-lobe fraction \(F_{\Omega,2}\) and orbit shape \(\chi\) are auxiliary geometric diagnostics, not unregistered independent stochastic laws. Tensor path \(G_x\) is not \(G_F\).

P1 authoritative source: P1_SELECTED_TENSOR_LAW_20261024/SCIENTIFIC_SCOPE.md (actual selected 274 rows, 15D full signed carrier and four fixed covariance shapes). Physical \(\sigma/H\) is NOT selected-data apparent STF. R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION/log__J2_coefficients.json is a separate 15D CF4 apparent STF coefficient+covariance for **demonstration**, not the original P1 274-row fit.
P2 source: R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json, finite-band actual PR3/PR4 signed \(\pi_\gamma/\rho_\gamma\), no same-frame photon flux or Commander full T null.
P3 source: R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/AUGMENTED/{AUGMENTED_CARRIERS.npz,AUGMENTED_RESULT.json}; fixed \`mono_method+24\` same-source 68D working Gaussian (35,970 selected CF4 groups), 3 models J1/J2/J3, with Q=distance derivative D>0 and 54 ICRS evaluation directions; H_D is not \(\mathcal H\).
P4 source: R65_DIPOLE_ANOMALY_20261117/RESULTS/INTERPRETATION_SUMMARY.json and R72_P4_LORENTZ_COUNT_TILT_20261119/RESULTS.json, same-provider peak/integrated transverse signed count contrast with shared source covariance (241,892 common components); R63 compensated-history low power separate. Radio log-intensity \(\widehat d\) is NOT the full 3D physical \(\boldsymbol\beta\).
Most important primary prior art: Heinesen arXiv:2010.06534, Maartens et al. arXiv:2312.09875, Takeuchi arXiv:2602.07389v2. Existing R68 Gaussian nuisance profile, radiation moment PSD and STF orbit theorem are established math, NOT new probability/SR firsts.

## 1. Universal theorem: identifiable physical view and physical-score firewall

For a full source model \(y=J\theta+N\gamma+\epsilon\), \(\epsilon\sim N(0,C)\) with \(C\succ0\), nuisance-profile Fisher is
\[
\mathcal I_{\theta|\gamma}=J^\top[C^{-1}-C^{-1}N(N^\top C^{-1}N)^+N^\top C^{-1}]J.
\]
A linear target \(L\theta\) is identifiable on unrestricted parameter fibres iff \(\ker\mathcal I_{\theta|\gamma}\subseteq\ker L\). For a nonlinear target, vanishing derivative on the kernel only provides **local first-order** identifiability, not a global no-go. In particular a physical \(Q\) or \(F\) cannot be computed on an observed nuisance quotient if its value changes along the quotient fibre. \(\Pi\) cannot be invented from a manifold constraint without an actual null. The five dependent views are deterministic/posterior-law functions of the same source experiment; a full-sky shape \(\chi\) and \(F_{\Omega,2}(\chi)\) carry no new Fisher information.

**Q-Pi deterministic relation, exact under a fixed full-rank Gaussian null:** for \(r\) Gaussian signed coordinates with null \(x_0\), \(Q_{\rm stat}=\sqrt{(\hat x-x_0)^\top\Sigma^{-1}(\hat x-x_0)}\) and \(\Pi_{\chi^2_r}=\mathrm{SF}_{\chi^2_r}(Q_{\rm stat}^2)\). Neither is a physical feasibility gauge. For R65 same-provider selected 2D contrast \(r=2\), \(\Pi=\exp(-Q_{\rm stat}^2/2)\). Statistical Q and Pi are just two presentations of one working-law reference, not independent confirmations.

## 2. Theorem R73-T1: exact physical-feasibility confidence support

Take a regular Gaussian coefficient experiment \(\hat\theta,\Sigma\succ0\), one simultaneous ellipsoid
\[
{\cal E}_\alpha=\{\theta:(\theta-\hat\theta)^\top\Sigma^{-1}(\theta-\hat\theta)\le c_\alpha\}.
\]
A family of **affine physical restrictions** \(g_n(\theta)=b_n+a_n^\top\theta\ge0\), for \(n\in\Omega\) (sky directions, photon intensity moments etc.), is satisfied throughout \({\cal E}_\alpha\) iff
\[
\boxed{\inf_{n\in\Omega}\left[g_n(\hat\theta)-\sqrt{c_\alpha\,a_n^\top\Sigma a_n}\right]\ge0.}
\]
Proof: Cauchy–Schwarz after whitening gives exact ellipsoid support at each fixed n, and infima over product sets commute. If \(a_n^\top\Sigma a_n>0\), an explicit feasible ellipsoid **boundary counter-witness** is
\[
\theta_*(n)=\hat\theta-\sqrt{c_\alpha}\,\Sigma a_n/\sqrt{a_n^\top\Sigma a_n}.
\]
If its \(g_n<0\), robust feasible-domain inclusion fails. This tests confidence-region containment, NOT whether the true universe violates a physical condition. Strict \(g_n>0\) requires a strict positive infimum. If Fisher rank deficient and the physical restriction varies along its null, the entire confidence cylinder is unconstrained in that direction; do not replace it with the pseudoinverse ellipse unless target estimability is established.
Applications:
- P1 **only if physically qualified** \(\theta=(H,d_i,S_A)\), \(g_n=H+d\cdot n+\sum_A S_A nE_A n\). The observed P1/R62 apparent STF lacks the optical \(\sigma/H\) transfer required for direct GR admission.
- P2 (stress only) \(g_n=1/3+n S n\) for all n, iff \(I/3+S\succeq0\), and flux-inclusive moment constraint requires additional \(f\); use this theorem for a full signed STF5 confidence ellipse only if its actual source covariance and null are qualified.
- P3 \(\theta=(V_3,a_0,\ldots,a_J)\), \(g_n=1-B(z)\eta_z(\theta,z,n)\), and \(a_n=-B(z)\times\) \`r64_directional_hubble.field_rows(z,n,J)[1]\`.
- P4 a **physical** linear-count density \(1+d\cdot n\) has \(g_n=1+d\cdot n\), but R65 uses an **exponential log-link** that is automatically positive and must not be falsely assigned this physical count gauge. The causal domain \(|\beta|<1\) requires actual source-qualified 3D \(\beta\), not R65 2D projected count coefficients.

## 3. Theorem R73-T2: exact Gaussian-ellipsoid halfspace occupancy (physical F under a *declared* finite reference measure)

Let \(\theta\in\mathbb R^r\), \(\Sigma\succ0\) and \({\cal E}_\alpha\) as above, with the **uniform Lebesgue** probability measure \(\mu_{\cal E}\) on that bounded ellipsoid. For the *one physical affine event* \(g(\theta)=a^\top\theta+b\ge0\), define the **ellipsoid-normalized** \(F_{\cal E}(g\ge0)\), to distinguish it from the original body-normalized \(F_{\mu,\cal K}(E)\). Set \(t=g(\hat\theta)/[\sqrt{c_\alpha}\sqrt{a^\top\Sigma a}]\) when \(a^\top\Sigma a>0\). The exact volume fraction is
\[
\boxed{F_{\cal E}=
\begin{cases}
0,&t\le-1,\\
\tfrac12+\tfrac{\operatorname{sgn}t}{2}I_{t^2}(\tfrac12,\tfrac{r+1}{2}),&-1<t<1,\\
1,&t\ge1.
\end{cases}}
\]
The one-dimensional marginal of the uniform \(r\)-ball has density \(\Gamma(1+r/2)/[\sqrt\pi\,\Gamma((r+1)/2)](1-u^2)^{(r-1)/2}\). Integrating it from \(-1\) to \(t\) proves the formula. If a=0, the event holds either everywhere or nowhere as determined by b. The case \(\mu_{\cal E}\) cannot be presented as a Bayesian posterior, frequentist confidence *coverage* of this event, or intrinsic physical measure without independently justifying it. Different reference measure/body normalization yields a different F.

**Joint n-dependent positivity:** \(F_{\cal E}(\bigcap_n\{g_n\ge0\})\le\min_n F_{\cal E}(\{g_n\ge0\})\), because an intersection is a subset of every event. A 54-direction check is only a coarser event than all-sky positivity, hence \(F_{\rm allsky}\le F_{54}\). A Monte Carlo \(\widehat F_{54}\) with fixed seed estimates a **specified finite-direction parameter-volume ratio**, not the intrinsic \(F_\Omega\) of a sky or a cosmic p-value. Meanwhile the R73-T1 robust condition \(\inf_{\theta\in\cal E}g_n(\theta)\ge0\) is a worst-case guarantee and is logically distinct from F being close to one.

## 4. P1: signed selected tensor, physical GR Hubble cone and sky shape

**Observed x, never automatically physical shear:** the original P1 selected Gaussian source consists of 274 rows and a signed 15-coordinate coefficient \(\beta\), four covariance shapes and a common unknown scale. That source's inferential \(\Pi\), \(F\) and selected confidence region retain their actual F/F-type law; do NOT replace it with an invented 15D fixed-covariance \(\chi^2\). The R62 35,970-CF4 source \`log__J2_coefficients.json\` is a separate *apparent* STF example, not the selected 274-row P1 dataset. The desired physical target is the 9-vector \(\theta_H=(H,d_3,S_5)\) in a chosen source congruence, with \(d=-A/c\) (same signature/observer convention) and \(S_{ij}=\sigma_{ij}\).
GR at a regular local vertex gives \(\mathfrak H(n)=H+d\cdot n+nSn\). With \(H>0\), normalized physical convex body \(\cal K_H=\{(d/H,S/H):\mathfrak H(n)\ge0\ \forall n\}\) has exact gauge \(Q_H=-\min_n[d\cdot n+nSn]/H\). \(Q_H<1\) means *all local directions expand in the vertex redshift sense*. With a full 9D source-qualified Gaussian ellipsoid, R73-T1 gives **robust entire-sky local positivity** via \(\min_n(\hat H(n)-\sqrt{c_\alpha}\sigma_H(n))\ge0\), preserving the correlated H–d–S covariance. The R62 apparent tensor cannot be inserted without optical transfer/calibration.
For a pure normalized physical shear \(U=\sigma/H\) with d=0, \(Q_H=-\lambda_{\min}(U)\). Together \((Q_H,\chi(U))\), \(U\ne0\), determine its *unordered three eigenvalues*: \(\chi\) fixes eigenvalue ratios because \(\lambda^3-I_2\lambda/2-I_3/3=0\), and \(Q_H\) supplies their magnitude scale. They do **not** determine eigenframe/eigendirections. Intrinsic \(F_{\Omega,2}=\mathrm{area}\{n:nUn>0\}/4\pi\) is a function \(\mathcal F(\chi)\), so adding it does not make another independent observation. Orientation and cross-source alignment require retaining signed STF5, not just \((Q_H,\chi,F_\Omega)\). At U=0, \chi and its orientation are undefined.
The actual R62 apparent STF example has signed \(\chi\approx-0.122766\), intrinsic \(F_{\Omega,2}\approx0.523642\), while actual CF4 selected 40–400 Mpc direction occupancy of the SAME tensor was ~0.26301. Those reflect different sky **measures**, not shape evolution. Under an entirely hypothetical local normalization H=1,d=0,S=R62 K0, Q_H≈.0177026, but this is a **conditional formula demonstration**, not observed physical GR shear.
\(\Pi_{P1}\) must use the original selected Gaussian F/common-scale design or an explicitly source-qualified alternative, with nonregular unknown-axis tests calibrated under the correct law. \(F_{P1}\) needs physical K and a finite measure; the original selected 15D confidence region is not a shear posterior. \(G_F\) needs the same source/observer/time transport; a source/window apparent STF path is \(G_x\), not \(G_F\).

## 5. Theorem R73-T3: photon flux feasibility ellipsoid and angular cap nonclosure (P2)

For a nonnegative normalized photon angular distribution p(n), in one observer tetrad define
\(f_i=\langle n_i\rangle_p\), \(P_{ij}=\langle n_i n_j\rangle_p\), \(S=P-I/3=\pi_\gamma/\rho_\gamma\in STF(3)\).
Then
\[
\boxed{\begin{pmatrix}1&f^\top\\f&I/3+S\end{pmatrix}\succeq0
\quad\iff\quad P\succeq0,\ f\in\mathrm{ran}P,\ f^\top P^+f\le1.}
\]
Proof: the forward direction is the generalized PSD Schur complement; the reverse is the rank-one downdate criterion \(P-ff^\top\succeq0\). If P>0, this is the exact three-dimensional **physical flux ellipsoid** \(f^\top P^{-1}f\le1\), with principal semiaxes \(\sqrt{\lambda_i(P)}\) in P's eigenframe. This establishes all angular **first-two-moment** realizability, not a full Boltzmann/Planck/Thomson history or a unique physical flux measurement.
With only observed S and no f, the stress-only physical gauge is \(Q_{\rm stress}(S)=\max(0,-3\lambda_{\min}(S))\). Full mixed \(Q_\gamma(f,S)\) is unavailable until flux is measured in the *same frame*. The observed low-\ell T tensor does NOT determine the photon energy cap F. For \(A_t=\{|n\cdot p|>t\}\) and \(P_{pp}=1/3+pSp\), every physically nonnegative angular intensity obeys the simple **conservative moment bounds**
\[
\boxed{\max\{0,(P_{pp}-t^2)/(1-t^2)\}
\le F^\gamma_{A_t}\le\min\{1,P_{pp}/t^2\},\quad0<t<1.}
\]
Proof: \(t^2\mathbf1_A\le(n\cdot p)^2\le t^2+(1-t^2)\mathbf1_A\), integrate over p. Full (f,S) may produce stronger bounds via a moment SDP; the displayed bounds are NOT claimed sharp when those additional moments are fixed.
Actual R66 PR3/PR4 *finite-band* released-temperature stress has \(Q_{\rm stress}\simeq1.1637\,10^{-5},1.2485\,10^{-5}\), but no matching actual photon flux. For \(t=.9\), the PR4 STF gives only \(0\le F^\gamma_{A_{.9}}\le0.4115246\). A tiny physical moment positivity gauge does **not** imply a tightly determined photon cap occupancy. The signed STF positive-quadrupole fullsky geometry ~0.5658 is unrelated to the unknown energy cap F. Commander matched physical \(\Pi\) unavailable; one observed CMB sky has no physical epoch \(G_F\).

## 6. Theorem R73-T4: an *actual* kinetic law for the time derivative of F (the prospective P2 G_F)

For an arbitrary fixed smooth angular event A on the round Fermi-propagated normal sky, define \(F_A(t)=\int_A p(t,n)\,d\Omega\) with normalized collisionless photon brightness p, source normal Bianchi geodesic V(n) and optical kinematics. R70 established the exact moment identity
\[
\frac{d}{dt}\langle h\rangle
=\langle V\cdot\nabla_{S^2}h\rangle-\operatorname{Cov}_p(h,\sigma_{nn}-2c\,a\cdot n).
\]
For \(h=\mathbf1_A\), a regular boundary ∂A and outward tangent conormal \(\nu_A\), the weak/distributional coarea identity gives
\[
\boxed{\dot F_A=-\oint_{\partial A}p\,V\cdot\nu_A\,d\ell
-\operatorname{Cov}_p(\mathbf1_A,\sigma_{nn}-2c\,a\cdot n)}
\]
for a *fixed* event A; collision/Thomson source terms add separately. The first contribution is angular-geodesic transport across the event boundary, the second is relative redshift/brightness weighting. For an event boundary transported with velocity W_A on the sky, replace \(V\) in its boundary term by \(V-W_A\). Under a complete physically specified time history, \(G_F(t_1,t_2)=\int_{t_1}^{t_2}\dot F_A\,dt\) is legitimate. With one actual CMB released sky and no physical time transfer, it remains UNAVAILABLE.
As a bounded axial Bianchi-I toy, let \(\sigma=s\mathrm{diag}(-1/3,-1/3,2/3)\), \(s=.07\) in declared time units, \(p_\epsilon(\mu)=(1+\epsilon P_4(\mu))/(4\pi)\) for \(\epsilon=0,1\), cap \(A=\{|\mu|>.9\}\). Both initial first-two photon moments are IDENTICAL, but exact kinetic boundary+covariance gives \(\dot F_A=-0.0159600000\) at ε=0 and \(-0.0208138350\) at ε=1. This proves a *physical time occupancy derivative* depends on unretained ell4 even when instantaneous signed STF5 and Q_stress agree. The toy is not an observed CMB sky history; verification in \`verify_fiveview.py\`.

## 7. P3: signed distance/redshift jet, physical Q_D and actual ellipsoid F

P3's source-qualified **observed** x is eta_lm(z), eta_lm,z(z), eta_lm,zz(z) with original signed 9-component [monopole,dipole3,STF5] per redshift and same CF4 full covariance, plus independent nuisance V3. The **latent physical** local Hcal=Theta/3+sigma_nn-A.n/c is NOT the same as H_D=c/[d_z(D_L/(1+z))].
For the R64 smooth flat reference B=H_ref chi/c, D(z,n)=1-B eta_z and H_D/H_ref=e^eta/D. At fixed z with B>=0 the positive distance-derivative domain is a convex intersection of halfspaces in its *signed derivative coefficient chart*:
\[
{\cal K}_D(z)=\{\theta:1-B(z)\eta_z(\theta,z,n)>0\ \forall n\in S^2\}.
\]
Its one-sided gauge Q_D=max(0,sup_n B eta_z) obeys Q_D<1 iff D>0 all sky, but is NOT a GR energy condition or a measurement of local Theta/3. If eta_z=alpha+d.n+n S n, a global minimum requires a spherical quadratic program; 54 sampled directions alone cannot prove positivity over S². eta(z,n)->eta(z,n)+a(n) with a independent of z leaves Q_D unchanged in the function model, not necessarily a finite source estimator with omitted nuisance basis.
F_Omega,D(z) is a separately typed **sky-area** fraction of D>0 from a physically reconstructed full sky; it is NOT F_E(K_D), the state-confidence ellipsoid volume. Pi is R64's nested fixed Gaussian working tail conditional on source selection/PV covariance. GF is unavailable until actual source/celestial-frame/optical transport and cross-depth covariance make two F's comparable; eta(z2)-eta(z1) is tensor G_x instead. Under Einstein+NEC and known same-ray physical Hcal, the Sachs consistency condition [R'-R/(1+z)](Hcal²)'/2+R''Hcal²<=0 is a separate physical necessary test, not interchangeable with Q_D<1.

**Actual R64 95% ellipsoid at z=.08:** using the model keys mono_method__J{1,2,3}__method_angular_nuisance, parameter dimensions 21/30/39 and 54 fixed ICRS directions, each D point mean is positive. The minimum joint-ellipsoid support among those 54 is J1 +0.5779945, J2 +0.0310494, J3 -2.8342154; number of positive lower certificates: 54/54, 54/54, 0/54 respectively. The J3 parameter witness at one direction has D=-2.8342154 and lies on the original Gaussian 95% boundary with Mahalanobis distance squared exactly chi2_39(.95)=54.57222776. Thus the J3 confidence ellipsoid is NOT wholly contained in the positive D domain, without implying the observed universe has negative H_D.
With explicitly selected **uniform volume on the original joint Gaussian ellipsoid**, the exact one-halfspace minimum occupancy over 54 directions is about 0.99384654 for J3 despite this witness. A reproducible 16,384-draw common-ellipsoid Monte Carlo using the joint coefficient covariance gives F_54=0.98822021 for the event D>0 at **all 54 evaluation directions**. This is a *reference-volume fraction*, not a frequentist confidence probability, posterior, sky area or cosmological significance. The allsky event is a subset of these 54 restrictions, so the true global parameter-volume fraction F_E(K_D,sky)<=F_54; its numerical value is not computed. Exact source fits remain conditioned on R64 phenomenological velocity and calibration.

## 8. P4: actual radio selected count x, working Pi(Q), physically missing beta

Original source R65_DIPOLE_ANOMALY_20261117: selected log-count dipoles d_b^perp in R² for three peak flux bins (joint signed 6D), with declination-ring conditional multinomial profile and actual cross-bin covariance. Registered *same-provider peak–integrated* comparison retains the **4D** signed pair x=(d_peak,x,d_peak,y,d_int,x,d_int,y) plus a full 4x4 same-source covariance, not two independent surveys. A physical boost is an additional *latent* three-velocity beta_O|S, not already measured as the observed d_b.
Actual integrated-minus-peak transverse contrast Delta=(-0.0016440241,0.0055246718) has working 2D Gaussian
T=Delta^T C_Delta^-1 Delta=30.98946896, Q_stat=sqrt(T)=5.56681857 and
\[
\boxed{\Pi_\mathrm{working}=\Pr[\chi_2^2\ge Q_{\rm stat}^2]=\exp(-Q_{\rm stat}^2/2)=1.8651867\times10^{-7}.}
\]
This is a **deterministic relation** of Q_stat and Pi under the named source Gaussian approximation, not two independent rejections. It is NOT cosmological LSS+survey calibrated significance or an instrumental/kinematic causal diagnosis. Ignoring actual same-source cross covariance changes T to 1.31544, which is a different incorrect experiment.
A physically source-calibrated kinematic model is d_b=k_b beta_perp+a_b. A *common* residual a and unequal known k_b may identify transverse beta using the nuisance-profile Fisher of R72; arbitrary bin-specific residuals leave beta unidentified. The exact R65 declination ring log-link absorbs the longitudinal component into free ring amplitudes at first order. The causal physical gauge Q_beta=|beta|<1 requires actual same-source 3D beta, so is **UNAVAILABLE** from the observed R65 carrier. A linear-count positivity gauge is inapplicable to the automatically positive exponential log-link model. Matter–radiation Gamma_MR=-g(U_M,U_R)/c² is a different invariant and cannot be derived from the radio dipole alone.
For selected sources, raw hemisphere fraction F_selected=N(H+)/N_selected under named mask/source population is a **descriptive empirical occupancy** with empirical count measure: for three peak bins F_selected=0.51198385, 0.51279497, 0.51134380 versus equal-area retained-pixel reference F_mask=0.50906061. These are NOT corrected fullsky intrinsic source anisotropy, nor confidence-volume F_E. Peak-to-integrated selection changes the event/population, not cosmological time, so is not physical GF.
Hypothetical source-qualified Lorentz STF quadrupole for selected sharp flux bin satisfies Q_count=(k_b²+k_b+kappa_b)/2 STF(beta beta)+O(beta^4). For a positive coefficient it has chi=+1 and intrinsic positive-lobe sky fraction 1-1/sqrt3; R65 flux/beam/alpha/source definitions do not yet establish actual Q_count or kappa. A chi/F pair does not detect global tilt.

## 9. Theorem R73-T5: transported covariance and physical GF

If **the same physical referent** has signed carriers x_i,x_j, a source-qualified deterministic linear frame/transport T_j<-i, and joint covariance C_ii,C_jj,C_ij, for Delta x=x_j-Tx_i,
\[
\boxed{C_{\Delta x}=C_{jj}+TC_{ii}T^\top-TC_{ij}-C_{ji}T^\top.}
\]
Exact covariance identity yields statistically valid G_x even when physical GF is unavailable. For differentiable, source-matched occupancies F_i(x_i),F_j(x_j) under common physical time/depth transport, delta-method variance is
\[
\operatorname{Var}(G_F)\simeq
\nabla F_j^\top C_{jj}\nabla F_j+\nabla F_i^\top C_{ii}\nabla F_i
-2\nabla F_j^\top C_{ji}\nabla F_i.
\]
At STF zero-contour topology transitions (chi≈0), F may be nondifferentiable and this delta approximation fails; a source-matched bootstrap or direct confidence-set image is then needed. If source events differ by radio flux (P4) or CMB release (P2), their difference is not physical time GF without an explicit transfer. The covariance theorem is already standard/R68 and is now specialized to four actual source laws, not a new probabilistic first.

## 10. Statistical application protocol: the physically typed five-view workflow

For each paper, begin from the actual source data operator and complete signed x and covariance, rather than from a scalar test statistic. Choose only one *identified* physical target or source-conditioned descriptive proxy and record frame, units, parity, time/redshift and source genealogy. Define the physical feasible body K with an actual GR/kinetic/selection equation; do not use Q_stat as Q_phys or construct a Minkowski gauge for a nonconvex Einstein solution manifold. Perform nuisance profile using full C, then use R73-T1 and the source model's exact rank to check the robust physical inequality. Reconstruct a common confidence region, never multiply Q/Π/F as if independent source laws. Specify Π only with a named source-compatible null, including calibration and covariance; otherwise output UNCALIBRATED. Register every F with its numerator, denominator, source population and finite measure; distinguish (a) F_{mu,K}(E) body-normalized, (b) F_E(K) ellipsoid-normalized, (c) F_Omega intrinsic sky area, and (d) F_selected empirical survey counts. Only report physical G_F after source-matched evolution/transport with nonzero cross-time covariance, else preserve G_x separately.

**Immediate executable decisions from R73 (source-conditional, not astrophysical discoveries):**
| Paper | x currently available | physically computable | law-calibrated Π | physical F or bounds | physical G_F |
| P1 | original selected 274x15; R62 separate apparent STF5 | local GR Q_H only after optical transfer; hypothetical R62 Q_H=.0177026, χ=-.122766 | P1 selected Gaussian common-scale F law, conditional only; R62 separate 5D zero-STF tail .104696 | no actual physical confidence/body K; intrinsic signed STF positive-area .523642 vs CF4 footprint .263010 | unavailable; possible coarea/Einstein driver only with actual normal-frame/shear history |
| P2 | R66 T^4 restored PR3/PR4 S_gamma STF5 | Q_stress=1.1637e-5/1.2485e-5 and allowed photon flux ellipsoid, full Q_gamma requires f | actual Commander T/E/B matched physical null unavailable | physical cap energy fraction PR4 t=.9 restricted to [0,.411525] by retained S, no exact F | actual CMB history NA; analytic toy photon Boltzmann derivative -0.01596 vs -0.020813835 despite same initial STF |
| P3 | R64 68D 35,970 selected source, signed eta(z), derivative jet and C | conditional Q_D and explicit confidence-domain witness J3 D=-2.834215 at z=.08 | fixed-C R64 angular/radial null only, no cosmological NEC PTE | ellipsoid-normalized one-direction F min .9938465 J3; joint fixed 54-direction F_MC .9882202±.0008429; physical sky area distinct | unavailable, depth G_x with covariance only |
| P4 | R65 6D bin count or same-provider 4D signed peak/integrated x | Q_stat=5.56682 under working contrast, physical Q_beta unavailable | fixed Gaussian source-conditional paired chi²2 tail 1.8652e-7 =exp(-Q_stat²/2), not LSS | selected CMB-axis raw count fractions .511984/.512795/.511344 vs uniform-pixel mask .509061; intrinsic/source-transport F unavailable | flux cut/release ≠ physical time; unavailable |

**Direct differentiations when actual transport becomes available:** physical local Hubble sign \(u(t,n)=d(t)\cdot n+n S(t)n\) with a regular signed zero set has \(dF_{\Omega}(t)/dt=(4\pi)^{-1}\oint_{u=0}\dot u/|\nabla_{S²}u|d\ell\) under fixed observer celestial coordinates. If u=a(t)u0, a>0, F and G_F remain constant even when amplitude changes. The Einstein shear-shape evolution \(\dot\chi\) in R69 is driven by tracefree 3-curvature and anisotropic stress, not isotropic H dilution alone. The actual \(\Pi(t)\) of a changing Gaussian null requires re-calibration when covariance/rank/source selection evolves. Do not infer dynamical constancy from constant F nor infer physical \(G_F\) from an arbitrary flux/source or redshift mask change.

**Adversarial review and evidence hierarchy:** T1, T2 exact linear support and beta-ball cap formula are standard convex and Gaussian geometry derived here with defined types. T3 flux PSD, conservative cap bound and T4 kinetic F transport follow exact first-two-moment and collisionless R70 assumptions, numerically checked for a specific smooth toy but not a general closed photon hierarchy. Actual per-paper readouts are implementation-verified against pinned R62/R64/R65/R66 source files, NOT new raw observational fits. The corrected status of all four physical analyses is conditional; no full source-qualified observer/kinetic/optical transfer or physical all-sky/lensing/null PTE was newly computed. Nonregular nodes (S=0, repeated eigenvalues,  χ≈0, D=0, rank-deficient nuisance) require explicit set-image or bootstrap, not automatic Wilks/delta method.
