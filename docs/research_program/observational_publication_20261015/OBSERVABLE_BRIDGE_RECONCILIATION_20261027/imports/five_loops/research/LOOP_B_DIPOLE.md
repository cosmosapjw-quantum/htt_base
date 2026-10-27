# Loop B — an intrinsic CMB dipole as a calibrated observer-response problem

Owner: `dipole_loop_20261026`. Date: 2026-10-26. Scope: internal, solver-free theoretical research; non-claim-bearing observational design. Repository reference: `a55036ad09c53a9215dee3282e425d37cfb95443`. No push, native solver, ODE, catalogue fit, or observed-sky likelihood was performed. Equations below distinguish exact local transformations, a controlled expansion, and conditional statistical inference. This is an actual R1–R10 unit under research-loop 1.0.0; a separate fresh review is assigned by the parent.

## R1. Question and completed research contract

The legacy dipole goal becomes the following concrete question: given a measured temperature dipole and additional spectral/angular channels, which registered observable can estimate or bound the intrinsic dipole relative to a specified reference frame? The target vector is a dimensionless temperature coefficient \(d\), not a global matter-tilt history. Its temperature amplitude is \(T_0|d|\), in kelvin. The observer velocity is \(v=c\beta\).

We construct the exact phase-space transformation, derive its second-order dipole–quadrupole relation, examine what spectral channels add, and give a nuisance-projected multichannel estimator with a finite bound. The needed extra input is identified explicitly: either a calibrated angular-coupling response to observer motion or a constrained intrinsic-multipole response. This advances the old local/global discussion to a usable observation contract without introducing a dynamical Bianchi transfer.

## R2. Sources and retained expressions

The source-matched starting point is *FROM A CMB SKY MAP TO PHYSICAL CONSTRAINTS*, PDF pp. 28–30, equations (9.1)–(9.10): incoming propagation direction is opposite outward sky direction, temperature has Doppler weight one, and the first-order generator includes both modulation and angular remapping. The same expressions appear in *20-report-1-*, PDF pp. 14–16, §12–13, together with processed-response quotient and depth-path qualifications. Exact repository packs `T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md`, §§1–3, and `T6_WU011_PROCESSED_RESPONSE_QUOTIENT_THEOREM_PACK.md`, §§1–3, were also read. These are retained, rather than re-labelled as new results.

Ellis, Maartens and MacCallum, *Relativistic Cosmology*, supplied PDF pp. 106–108 (printed pp. 90–92), equations (5.2), (5.7)–(5.9), define barycentric, particle and energy frames. PDF pp. 120–121 (printed pp. 104–105), equations (5.76)–(5.82), give momentum decomposition, scalar distribution and PSTF multipoles. Cercignani and Kremer, *The Relativistic Boltzmann Equation*, supplied PDF pp. 42–43 (printed pp. 31–32), §2.1 and equations (2.1)–(2.5), supply the scalar distribution and invariant phase-space construction. We use these local kinematic statements; their collision terms are not solved.

Primary literature located through Exa on 2026-10-26 is: Dai–Chluba [1403.6117v2](https://arxiv.org/abs/1403.6117v2), Planck [1303.5087v3](https://arxiv.org/abs/1303.5087v3), Yasini–Pierpaoli [1610.00015v4](https://arxiv.org/abs/1610.00015v4), and Roldan–Notari–Quartin [1603.02664v2](https://arxiv.org/abs/1603.02664v2). The first separates Doppler weights; the second constructs angular-coupling velocity estimators; the third models low-multipole spectral leakage, including nonlinear blackbody terms in Appendices B–C; the fourth exposes gravitational dipole contributions to Doppler/aberration estimators. Literature supports the observational strategy and its assumptions; it does not establish this project's calibration.

The latest retained `evidence/baseline/research/theory_expansion.md`, T1–T15, concerns a different optical observable: \(-5\log[1+d_{\rm opt}\cdot n+S:nn]/\ln10\), with \(d_{\rm opt}=-A/(cH)\). Its acceleration–shear octupole and finite logarithm remainder are already derived. Here \(d\) denotes a radiation temperature dipole. Equal vector dimension or STF tensor rank does not identify these physical quantities.

## R3. Conventions and approximation hierarchy

Use signature \((-+++ )\), unit timelike \(u\cdot u=-1\), and physical photon energy \(\epsilon=-c p\cdot u>0\). A photon arriving from sky direction \(n\) has
\[
 p^a={\epsilon\over c}(u^a-n^a),\qquad u\cdot n=0,\quad n\cdot n=1.
\]
Thus the propagation direction in Ellis's convention is \(e=-n\). The changed observer is \(u'=\gamma(u+\beta)\), \(\gamma=(1-\beta^2)^{-1/2}\). Here \(\beta\) is dimensionless and spatial; \(c\), \(k_B\) and \(h=2\pi\hbar\) remain explicit in physical formulas.

For the second-order calculation introduce a bookkeeping parameter \(\lambda\): \(\beta,d=O(\lambda)\), \(Q=O(\lambda^2)\), and
\[
 T(n)=T_0[1+d\cdot n+Q:nn]+O(\lambda^3),\qquad Q=Q^{\mathsf T},\quad\operatorname{tr}Q=0.
\tag{B1}
\]
The displayed hierarchy is a mathematical expansion, not an empirical statement that the actual intrinsic quadrupole has this scaling. If an intrinsic quadrupole or higher mode is retained at first order, its boost leakage is included using the generator below and becomes part of the registered response/nuisance model. Positivity of the exact input temperature is assumed.

The reference frame in (B1) is specified by the adopted physical/statistical model; it is not automatically the radiation energy frame. For a blackbody sky with a small temperature dipole, bolometric intensity is proportional to \(T^4=T_0^4(1+4d\cdot n+\cdots)\). Since photon propagation is \(-n\), direct angular integration gives physical energy flux \(\mathcal F^i=-(4/3)cU_\gamma d^i+O(\lambda^2)\), where \(U_\gamma\) is radiation energy density. Thus its radiation energy frame removes this dipole to first order. A nonzero intrinsic dipole relative to a statistical reference frame and a zero-flux radiation frame can coexist as different frame definitions. A matter energy or particle frame introduces an independently specified current or stress tensor. This is the physical content of the frame distinction, not an arbitrary name change.

## R4. Candidate channels and exact observer change

Direct contraction, with the incoming-direction sign retained, gives
\[
 \epsilon'=\gamma\epsilon(1+\beta\cdot n),\qquad
 n'={n+[(\gamma-1)(\hat\beta\cdot n)+\gamma|\beta|]\hat\beta
       \over\gamma(1+\beta\cdot n)}.
\tag{B2}
\]
Replace \(\beta\) by \(-\beta\) to invert the angular map. Define
\[
 D={\epsilon'\over\epsilon}
 ={1\over\gamma(1-\beta\cdot n')}.
\]
The scalar occupation number therefore obeys exactly
\[
 f'(\epsilon',n')=f(\epsilon'/D,n(n')),
\quad I'_{\nu'}(n')=D^3I_{\nu'/D}(n(n')) .
\tag{B3}
\]
For \(I_\nu=B_\nu(T)=(2h\nu^3/c^2)[e^{h\nu/(k_BT)}-1]^{-1}\), equation (B3) gives the exact directional temperature
\[
 T'(n')=D\,T(n(n')) .\tag{B4}
\]
This follows by preserving \(\epsilon/(k_BT)\) for the same ray. At \(\beta\cdot n'>0\), the moving observer measures a hotter monopole, which checks the sign. Frequency-dependent occupation or intensity, rather than a fitted temperature alone, is the general input. Candidate discriminators are spectral low-multipole leakage and small-scale angular couplings, both linked by (B3).

## R5. Constructive second-order dipole–quadrupole calculation

At fixed observed direction, write \(b=\beta\cdot n'\), \(s=d\cdot n'\). The inverse aberration is \(n=n'-\beta+b n'+O(\lambda^2)\). Hence
\[
 d\cdot n=s-\beta\cdot d+bs+O(\lambda^3),\qquad
 D=1+b+b^2-\beta^2/2+O(\lambda^3).
\]
Multiplying, rather than adding separate Doppler and intrinsic templates, yields
\[
 {T'\over T_0}=1+(\beta+d)\cdot n'
 +b^2-\beta^2/2-\beta\cdot d+2bs+Q:n'n'
 +O(\lambda^3).
\tag{B5}
\]
Spherical averaging uses \(\langle n_i n_j\rangle=\delta_{ij}/3\). The relative mean shift, dipole vector \(a\), and temperature quadrupole \(K\) are consequently
\[
 m=-\beta^2/6-(\beta\cdot d)/3,\qquad
 a=\beta+d+O(\lambda^3),
\]
\[
 K=Q+\beta_{\langle i}\beta_{j\rangle}
       +2\beta_{\langle i}d_{j\rangle}+O(\lambda^3).
\tag{B6}
\]
In particular,
\[
 K-a_{\langle i}a_{j\rangle}
 =Q-d_{\langle i}d_{j\rangle}+O(\lambda^3).
\tag{B7}
\]
This is an explicit closure test. A free intrinsic quadrupole enters precisely where one might otherwise assign a dipole anomaly. Under the restricted assumption \(Q=0\), the residual is \(-dd_{\rm STF}\): its eigenvalues are \((-2|d|^2/3,|d|^2/3,|d|^2/3)\). It determines an unoriented dipole axis and amplitude, not its sign. With a bounded \(Q\), it becomes a bounded-contamination constraint. With unconstrained \(Q\), its interpretation is the stated response equation.

More explicitly, let \(M=K-aa_{\rm STF}\), suppose \(\|Q\|_F\leq q_{\max}\), and suppose the combined measurement and expansion error in \(\hat M\) is at most \(\delta_M\). Because \(\|dd_{\rm STF}\|_F=\sqrt{2/3}|d|^2\), the triangle and reverse-triangle inequalities yield
\[
 \sqrt{3/2}\max(0,\|\hat M\|_F-q_{\max}-\delta_M)
 \leq |d|^2
 \leq\sqrt{3/2}(\|\hat M\|_F+q_{\max}+\delta_M).
\tag{B7a}
\]
The upper amplitude bound is the square root of the right side. This is a second route to a finite intrinsic-dipole bound, conditional on a quantitative intrinsic-quadrupole envelope instead of an independent velocity channel. A simultaneous coverage event for \(\delta_M\) propagates to the same coverage for this interval. Its square-root sensitivity and unresolved dipole sign are visible in the formula. Deboosting by the fitted total dipole \(a\) leaves quadrupole \(Q-dd_{\rm STF}\) at this order, which is another direct interpretation of the same residual.

For a known nonzero \(\beta\) and a constrained/subtracted intrinsic quadrupole, define
\[
 R=K-Q-\beta\beta_{\rm STF}=L_\beta d,
\quad L_\beta d=\beta d^{\mathsf T}+d\beta^{\mathsf T}
                 -{2\over3}(\beta\cdot d)I.
\]
Direct multiplication and contraction give
\[
 \|L_\beta d\|_F^2=2\beta^2|d|^2+{2\over3}(\beta\cdot d)^2,
\quad
 d={1\over\beta^2}\left(I-{\hat\beta\hat\beta^{\mathsf T}\over4}\right)R\beta.
\tag{B8}
\]
Thus all three components survive this ideal map. Its smallest singular value is \(\sqrt2|\beta|\), and tensor error \(\delta_R\) produces \(|\delta d|\leq\delta_R/(\sqrt2|\beta|)\). The conditioning is finite while the absolute inverse gain diverges as the known boost tends to zero. An arbitrary intrinsic quadrupole is a five-dimensional nuisance and must be calibrated or constrained before using this inverse.

## R6. Independent spectral derivation and closure

Set \(G_\nu=T_0\partial_TB_\nu\), \(H_\nu=T_0^2\partial_T^2B_\nu\), evaluated at \(T_0\). Expansion of the exact Planck function, independently of the boost derivation, gives
\[
 I'_\nu=B_\nu(T_0)+G_\nu\Theta'+\tfrac12H_\nu(\Theta')^2+O(\lambda^3).
\]
For \(x=h\nu/(k_BT_0)\), \(H_\nu/G_\nu=x\coth(x/2)-2\). Its intensity quadrupole is
\[
 I'_{\nu,2}=\left[G_\nu K_{ij}
       +\tfrac12H_\nu a_{\langle i}a_{j\rangle}\right]n'_in'_j
       +O(\lambda^3).
\tag{B9}
\]
The observed monopole similarly is
\[
 \bar I'_\nu=B_\nu(T_0)+G_\nu m+H_\nu|a|^2/6+O(\lambda^3).
\tag{B10}
\]
These equations retain the \(d^2\) term; dropping it requires a different, explicitly recorded small-intrinsic-dipole hierarchy. If the mean temperature itself is fitted, the \(G_\nu m\) term is absorbed into that parameter at this order. Directional blackbodies and spectrally distorted angular averages are consistent: averaging is nonlinear in temperature.

Differentiate (B3) directly to verify the intensity generator:
\[
 \delta_\beta I_\nu=(\beta\cdot n)(3-\nu\partial_\nu)I_\nu
 -[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}I_\nu.
\tag{B11}
\]
The identity \((3-\nu\partial_\nu)G_\nu=G_\nu+H_\nu\) then makes intrinsic-dipole leakage into the quadrupole proportional to \((2G_\nu+H_\nu)\beta_{\langle i}d_{j\rangle}\). Kinematic monopole leakage has the same spectral shape, with coefficient \(\beta_{\langle i}\beta_{j\rangle}/2\). The \(H_\nu\) contribution from intrinsic blackbody nonlinearity completes the total \(a a_{\rm STF}/2\) in (B9).

This calculation specifies what a spectral closure measurement tests and why a frequency count alone is insufficient for assigning an arbitrary blackbody sky to a frame. Yasini–Pierpaoli's proposed separation uses a rest-frame multipole model, small-anisotropy treatment, and control of neighbouring-mode leakage; Appendix A explicitly assumes Gaussian uncorrelated rest-frame multipoles. Their Appendix C retains intrinsic-dipole nonlinear corrections. Our contract keeps these assumptions visible instead of treating their forecast as a model-free measurement. This is a scope clarification and a reusable calculation, with no novelty or new no-go assertion.

## R7. Executed CAS and an independent angular channel

Connected Wolfram Language evaluation completed the lightweight algebra in `cas/loop_b.wl`. The clean output was
\[
 \{0,\operatorname{diag}(2\beta^2,2\beta^2,8\beta^2/3),\{0,0,0\},0,0\}.
\]
The entries check (B5), the Gram matrix of (B8), its inverse, the spectral Euler identity, and the Planck spectral ratio. The receipt is `cas/loop_b_receipt.json`. Rotating \(\beta\) to the positive \(z\)-axis is justified by spatial covariance; no pixel fit, xAct calculation, ODE, or native transfer is inferred from these checks.

For the angular channel, the retained weight-one temperature generator is \(\beta[\mu-(1-\mu^2)\partial_\mu]\). The normalized spherical-harmonic recurrences give
\[
 \delta_\beta Y_{\ell m}=\beta[(\ell+1)c_{\ell+1,m}Y_{\ell+1,m}
                       -\ell c_{\ell m}Y_{\ell-1,m}],
\quad c_{\ell m}=\sqrt{{\ell^2-m^2\over4\ell^2-1}}.
\]
For zero-mean statistically isotropic rest-frame fluctuation modes with power \(C_\ell\), taking \(\ell\geq2\), this implies
\[
 \mathbb E[a'_{\ell m}a'^*_{\ell+1,m}]
 =\beta(\ell+1)c_{\ell+1,m}(C_\ell-C_{\ell+1})+O(\beta^2).
\tag{B12}
\]
Products across many modes therefore supply a response to \(\beta\) beyond the measured low-order dipole. Intensity-derived temperature maps require their actual bandpass modulation coefficient, so (B12) is not transplanted unchanged. Mask, beam, lensing, foregrounds, intrinsic dipolar covariance and the fitted power spectrum enter calibration. Roldan–Notari–Quartin identify physical dipolar-potential contributions that can mimic parts of these couplings; those contributions must be included or bounded when assigning this response to observer velocity.

## R8. Nuisance-projected estimate and finite intrinsic-dipole bound

Stack a measured three-component dipole and calibrated angular-coupling features into one vector \(y\), with known joint covariance \(C\succ0\). Optional spectral features obeying (B9) may be appended after their registered linearization. A simple six-parameter design is
\[
 y=H\theta+N\eta+r+\epsilon,\quad
 \theta=(\beta,d),\qquad H=\begin{pmatrix}I&I\\R_{\rm ang}&0\end{pmatrix}.
\tag{B13}
\]
Nuisance columns include allowed calibration patterns and physical competing responses. Define \(\bar N=C^{-1/2}N\), \(P=I-\bar N\bar N^+\), \(A=PC^{-1/2}H\), \(z=PC^{-1/2}y\). If \(\operatorname{rank}A=6\), then
\[
 \hat\theta=A^+z,\quad F=A^{\mathsf T}A,\quad
 \hat d=S\hat\theta,\quad V_d=SF^{-1}S^{\mathsf T},\qquad S=(0,I).
\tag{B14}
\]
Projection removes \(N\eta\) exactly because \(P\bar N=0\); substitution proves unbiasedness for \(r=0\), and multiplication of the Gaussian noise covariance proves the stated \(V_d\). For a declared projected remainder bound \(\|PC^{-1/2}r\|\leq\rho\), Gaussian noise with the registered fixed covariance gives the conservative finite coverage bound
\[
 |d|\leq|\hat d|+
 \sqrt{\chi^2_{3,1-\alpha}\lambda_{\max}(V_d)}
 +\rho\|SA^+\|_2
 \quad\text{with probability at least }1-\alpha.
\tag{B15}
\]
The proof adds the Gaussian marginal ellipsoid radius and the operator-norm bias bound. Correlations between dipole, frequency maps and quadratic products remain in \(C\); their separate likelihoods are not multiplied. Products of Gaussian sky modes are not exactly Gaussian, so a Gaussian feature law is a stated approximation; finite calibration can instead supply a valid event \(\|PC^{-1/2}\epsilon\|\leq q_{1-\alpha}\), replacing the two radius terms by \((q_{1-\alpha}+\rho)\|SA^+\|\). No numerical value of this bound is claimed here.

If the quotient rank drops, compute the estimable target combinations through \(S\ker A\). A dipole component is identified only when its target row annihilates \(\ker A\). Before nuisance projection, block elimination in (B13) gives \(\operatorname{rank}H=3+\operatorname{rank}R_{\rm ang}\). Thus a velocity measurement along only one direction adds one scalar constraint: it bounds the parallel intrinsic dipole, while perpendicular components require additional response or compact external bounds. A three-component amplitude bound such as (B15) requires three surviving velocity directions. For the transparent special case \(R_{\rm ang}=I\), \(\hat d=\hat a-\hat\beta\) and \(V_d=C_a+C_\beta-C_{a\beta}-C_{\beta a}\). This also exposes the practical role of shared-sky covariance. Compact external parameter bounds can still give a finite identified-set envelope when rank is deficient. This is the existing nuisance-quotient logic applied to a named dipole observable.

## R9. Observable contract and truncation control

The deliverable inputs are absolute or jointly calibrated frequency maps, bandpasses, common direction conventions, beams/pixel windows, masks, the actual low-mode fit operator, coupling-mode range, full shared covariance or calibrated noise law, nuisance columns, and the rest-frame statistical/physical model used for \(R_{\rm ang}\). Output is \(\hat d,V_d\), the bound (B15), projected rank/singular values, and spectral closure residuals from (B9)–(B10). Units are dimensionless until multiplying by \(T_0\). Any local matter velocity comparison needs its own frame and selection definition.

Truncation is a measurable obligation. For an exact positive polynomial input sky, scale \((\beta,d,Q)\mapsto(t\beta,td,t^2Q)\) in (B4), obtaining the dimensionless \(F(t,n')=T'(t,n')/T_0\). On a compact domain \(|\beta|\leq b_{\max}<1\), its third derivative is bounded. Taylor's theorem gives \(|R_T|\leq M_3/6\), with \(M_3=\sup_{t\in[0,1],n'}|\partial_t^3F|\). A certified derivative bound or exact-map difference supplies this value for registered inputs; an additional intrinsic sky remainder is propagated separately. Full-sphere dipole and quadrupole errors then obey \(|R_a|\leq\sqrt3 M_3/6\) and \(\|R_K\|_F\leq\sqrt{15/2}M_3/6\); processed operators propagate these into \(\rho\). These bounds follow from projector contraction and normalized spherical moments. Foreground and calibration uncertainty are additional terms, not absorbed into a formal Taylor symbol.

## R10. Verdict and resume point

Established inputs are the scalar phase-space law and local Lorentz response. Derived results are (B5)–(B11), the calibrated inverse (B8), the angular response (B12), and the conditional finite bound (B15); selected algebra was executed and passed. The actual observing design's rank, covariance, calibration remainder and observed intrinsic-dipole constraint remain unresolved input-dependent quantities.

The next concrete action is to instantiate (B13) from a specified released dipole plus angular-coupling product, propagate bandpasses and sky support through the same estimator, and compute \(\sigma_{\min}(A)\), \(V_d\) and \(\rho\). A radiation dipole or a calibrated endpoint velocity constrains one event's radiation–observer relation. A global matter-tilt history additionally requires matter-frame observables, depth windows and dynamical response. This separate obligation follows the supplied reports' source distinction and is preserved in the resume contract.

### Physics/math and claim audit

The four project skills read were `htt-physics-math-audit`, `htt-local-global-discrimination`, `htt-claim-firewall` and `htt-claim-provenance-ledger`; their existing equation, frame, rank and claim controls are applied here. No project policy was changed.

| Item | Scoped verdict | Evidence or required application |
|---|---|---|
| Dimensions and signs | Checked | \(\epsilon\) is energy, \(d,\beta,Q\) dimensionless; forward hot-spot and zero-boost limits agree. |
| Exact transform and expansion | DERIVED | (B2)–(B6); second-order residual zero in CAS. |
| Spectral closure and inverse | DERIVED | (B8)–(B11); Gram, inverse and spectral identities checked. |
| Statistical bound | CONDITIONAL | Known joint law/design, registered nuisance image and remainder bound. |
| Observed intrinsic dipole | SPECIFIED | Requires actual calibrated input products and quotient-rank evaluation. |
| Global-tilt inference | Separate target | Requires matter/depth/dynamical response in addition to this local law. |

The proposed change is a research construction only. The tests performed are symbolic identities; the tests to run at application are injected-boost recovery, bandpass consistency, mask mean-field and nuisance-rank calibration under the same operator order. Rank loss, unbounded competing intrinsic covariance, or a missing calibration remainder suspends the associated physical assignment while retaining valid response diagnostics. Claims are owned by `common` for the transformations, `obsstat` for features, and `htt` for a future model-dependent interval. Transfer source is `none`, tier is exploratory `C0`, and no claim is promoted to observed or native-solver validation. No strong no-go or novelty result is proposed, so NG1–NG7 admission is not invoked. The only packaging artifacts are the requested research note, claim record and executed algebra receipt; no permanent project registry was edited.

짧은 요약: 입사광의 진행방향은 하늘방향의 반대이므로 \(\epsilon'=\gamma\epsilon(1+\beta\cdot n)\)이다. 실제로 전개하면 관측 dipole은 \(a=\beta+d\), quadrupole은 \(K=Q+\beta\beta_{\rm STF}+2\beta d_{\rm STF}\)를 만족한다. 주파수별 quadrupole의 비선형 성분은 전체 관측 dipole과 연결되므로, intrinsic dipole을 정량화하려면 보정된 aberration 반응이나 intrinsic multipole 모형이 필요하다. 공동 covariance와 nuisance 사영을 포함한 추정량 및 유한 상한을 구성했고, 핵심 대수는 Wolfram으로 확인했다. 이 결과의 대상은 국소 복사–관측자 관계이며 전역 물질 tilt의 관측은 별도 자료·전달모형 의무로 남는다.
