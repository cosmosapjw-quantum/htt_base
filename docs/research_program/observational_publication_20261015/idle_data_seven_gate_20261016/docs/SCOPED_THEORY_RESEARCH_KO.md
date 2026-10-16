# HTT six-paper DAG: 다운로드 대기 중 수행한 7-gate 이론·경량 검증 루프

2026-10-16 KST. Authority `cosmosapjw-quantum/htt_base` Draft PR #547, head `b942c4dba6c8eab6d0f791c7532874d35664f2a7`, canonical 6 papers/42 nodes. The verified starting state is 14 `completed_scoped`, 28 `pending`, 7 physical-source blockers `S04,L03,H02,V03,B02,K03,K04`; READY `L01,S02`. Scope: independent mathematical/conditional precursor work *while user downloads original data externally*, not an inferred local download status. Neither canonical DAG nor 245 engineering backlog is modified in this branch. Physical metric signature (-,+,+,+); c is explicit in covariant formulas. Local numerical H_i units are 1/toy-time and never physical km/s/Mpc fits.

## A. H02: **selection and integration of one shared latent do not commute**

Under a **fixed preselected set of N labelled parent slots**, a proper common calibration latent \(\eta\) with prior \(\pi(\eta)\), and conditional independence of the pre-selection row observables \(Y_i\) given \(\eta\), the correct fixed-count joint law conditional on all slots entering the catalogue is

\[
 p(\boldsymbol y\mid S_1=\dots=S_N=1,\theta)
 = \frac{\int d\eta\,\pi(\eta\mid\theta)
          \prod_{i=1}^N s_i(y_i,\eta,\theta) p_i(y_i\mid\eta,\theta)}
        {\int d\eta\,\pi(\eta\mid\theta)
          \prod_{i=1}^N Z_i(\eta,\theta)},\quad
 Z_i(\eta,\theta)=\int dy_i\,s_i(y_i,\eta,\theta)p_i(y_i\mid\eta,\theta).
\]

Here inclusion selection \(s_i\) is an indicator or probability in [0,1]; an unknown **catalogue point process or count likelihood** requires a different likelihood and is not supplied by this formula. Conditional independence given \(\eta\) is a scientific modelling assumption, not a theorem about CF4 rows. Known overlap/grouping may violate it and requires an explicit joint conditional law. In the discrete case \(\eta=j\), the admitted latent weights satisfy

\[
 \pi_j^{\rm selected}\propto \pi_j\prod_i Z_{ij}.
\]

The tempting alternative \(\int \pi(\eta) \prod_i[p_i(y_i\mid\eta) s_i(y_i,\eta)/Z_i(\eta)]d\eta\) is itself normalized but **different**, because it conditions on the selection inside each fixed-\(\eta\) model and then restores the *unselected* parent prior. Mere density integration to one cannot catch the incorrect model. Which conditioning convention corresponds to the actual survey must be fixed before observation likelihood construction.

**Concrete manufactured witness.** Two latent types have parent probabilities (0.6,0.4), Gaussian means (-1,1.5), standard deviations (0.5,0.5), and selection \(Y>0\). After **both** independent conditional slots are admitted, type probabilities are (0.00077784748,0.9992221525), not (0.6,0.4). For \(y=(0.2,0.3)\), naive/original joint selected density ratio is **462.975789...**. Both densities integrate to one over the positive quadrant, proving normalization alone is insufficient. Source-code tests also verify extreme Gaussian tail stability and analytic selected-score \(y-\sqrt{2/\pi}\) for one-sided truncation at zero. These toy numbers are emphatically not CF4 bias estimates.

**Existing code to reuse:** HTT PR #518 `htt/htt/htt/infer/cf4_product_provider.py`, PR #520 `htt/htt/htt/infer/r7_joint_experiment.py`, PR #517 structured Gaussian `htt/src/common/structured_inference.py`, and PR #545 K02 group/method-overlap sensitivity. The new bounded program is an adversarial selected-shared-latent *regression oracle*, not a competing production Bayesian engine. Physical H02 admission requires full source group/individual genealogy, real parent sample completeness (W1 photometry/width/inclination/sky/redshift), selected-count scheme, calibrated \(C_\mathrm{grp}+Z\Lambda Z^T+C_\mathrm{vel}\), proper priors, independent selection-matched mock coverage, duplicate-group handling, and a reported sensitivity envelope for unknown selection.

**Common-monopole gauge:** If a column \(q\) for apparent H0 lies in the span of unpenalized group/method zeropoints \(Z\), \(P_{Z}^{\perp}C^{-1/2}q=0\). A calibrated **proper prior** on zeropoints can give a positive conditional Fisher information in \(C_{\rm eff}=C+Z\Lambda Z^T\), but that additional information is prior-/calibration-dependent, not source-only identification. Sandboxed tests demonstrate both branches.

## B. L03 / L01: one latent Planck sky per independent null unit

Model released products by \(Y_{sp}=\mathcal P_p(S_s,N_{sp},B_p,M_p,F_p)\): \(s\) indexes independent CMB skies and \(p\) denotes release method/split. Each sky generates multiple products sharing the same latent CMB source. A proper predeclared scan over methods is reduced to **one score per sky** \(T_s=\max_p |\tau(Y_{sp})|\). For a genuinely exchangeable measured sky and \(N\) independent matched-null skies, the conservative rank PTE is
\[
 p=\frac{1+\#\{s:T_s\ge T_{\rm obs}\}}{N+1}.
\]
All masks/estimators/axes/spectral cuts chosen via scanning on observation must be equivalently repeated inside **each** simulated-sky score. Replacing N with N × number_of_products is invalid. A 101-sky 4-method mock recovers the exactly enumerated ranks (1,...,101)/101 with minimum 1/101 = 0.00990099. This is a rank-unit test, **not** a Planck anomaly p-value. It also recovers the expected positive cross-processing correlation due to a common latent sky.

**Still absent:** actual PR3 T/Q/U processing under the matched T and polarization masks, effective beam, high-\(\ell\) spin-2 leakage and E/B phases, independently indexed 999 CMB versus 300 noise/systematic realizations, and a fixed analysis-selection registry. Product/split number is not null unit count. Previous PR #536–#539 finite scalar-T masked-response work cannot automatically certify spin-2 E/B processing. The new mathematical test is a reusable acceptance unit for future simulations.

## C. V03: independent observer-frame information is necessary for a constant global tilt

For a toy time-history \(\beta_{RM}(t)=\beta_0+q(t)\beta_1\), normalized line-of-sight/visibility windows give
\[
 d_i=\beta_{RO}+\beta_0+\langle q\rangle_i\beta_1 + n_i.
\]
With two distinct windows, the 2×3 matrix has rank 2 and exact null vector (1,-1,0), irrespective of the gap between windows. A separately **calibrated** CMB aberration row measuring only \(\beta_{RO}\) has the toy response (1,0,0), giving rank 3 when the two visibility moments differ. This is an **identifiability criterion conditional on transfer functions and anchored source calibration**, not a Planck-only detection; the physical Planck aberration measurement and intrinsic dipole contamination must actually be accounted for. An alternative without such a local anchor is a third source with a linearly independent non-endpoint response and controlled astrophysical nuisances.

Practical physical next experiment: run fixed Bianchi/linear vector mode transfer with source history \(\beta_0\), slope \(\beta_1\), observer aberration, and astrophysical bulk-flow/mask columns; compute the nuisance-projected singular values. Require calibrated T/E/B and redshift-dependent response, not duplicate sky or intensity-only normalization.

## D. K03: proper-motion response and calibrated frame spin

In a flat rest-space local affine approximation \(v_i(\boldsymbol x)=G_{ij}x_j\), the ideal distance-normalized galaxy observables at direction \(n\) are
\[
 v_r/r=n_iG_{ij}n_j,\qquad
 \mu_\perp=(I-nn^T)G n +\Omega_{\rm frame}\times n+ (I-nn^T)g_{\rm glide}.
\]
Here \(G\) is the 3×3 *physical local* velocity-gradient proxy (not the GR congruence gradient or a global Bianchi identification). The radial response cannot see its 3 antisymmetric directions. Galaxy radial + tangent measurements at generic sky positions determine 12 independent combinations of the 15 columns \((G_9,\Omega_3,g_3)\): the physical antisymmetric gradient is exactly degenerate with frame spin. Adding independent **quasar** proper-motion rows \(\Omega\times n+P g\) in the same calibrated reference frame raises generic constructed rank to 15/15. The rank calculation is numerical and ideal/noiseless; a real survey must show a stable *smallest singular value after covariance and selection*, not merely exact rank in random simulated positions. Quasars calibrate observer frame spin/glide, not the cosmic matter vorticity. Galaxy proper motions need independent host distances, unit/frame conversion and realistic errors.

## E. K04 + B02: an **exact Bianchi-I collisionless frequency shift** bridges local to finite-redshift physics

Fix the kinematical metric \(ds^2=-c^2dt^2+\sum_{i=1}^3 a_i(t)^2(dx^i)^2\) on \(t\in[-\tau,0]\) with \(a_i(t)=e^{H_i t}\), constant rates \(H_i\) in inverse proper time, and observation-normalized \(a_i(0)=1\). This is a legitimate *kinematic spacetime metric*, not claimed to solve Einstein+matter for arbitrary \(H_i\). Spatial translation Killing symmetries conserve covariant photon momenta \(k_i\). With observed local unit direction \(n_i=k_i/E_{\rm obs}\) (suitable c-normalized units),
\[
 1+z(n,\tau)=\frac{E_{\rm em}}{E_{\rm obs}}
 =\Big(\sum_i n_i^2 e^{2H_i\tau}\Big)^{1/2},\qquad \sum_i n_i^2=1.
\]
Hence, writing \(\langle F(H)\rangle_n=\sum_i n_i^2 F(H_i)\),
\[
 \log(1+z)= \langle H\rangle_n\tau
      + \mathrm{Var}_n(H)\tau^2+O(\tau^3),\quad
 \langle H\rangle_n=\Theta/3+\sigma_{ij}n^in^j.
\]
By Jensen's inequality, for \(\tau>0\), \(\log(1+z)/\tau\ge\langle H\rangle_n\) with equality iff every rate with \(n_i^2>0\) is the same. Moreover \(d^2/d\tau^2[\frac12\log\sum w_i e^{2H_i\tau}]=2\mathrm{Var}_{w(\tau)}(H)\ge0\), so the secant rate \(\log(1+z)/\tau\) is nondecreasing as a function of lookback time. Independently confirmed with Wolfram (2-support case) and sandbox finite-difference/jensen tests. This establishes a **finite-time correction even for constant shear**. It does not identify the CF4 Hubble-window coefficient because CF4 has no direct observed \(\tau\), source/peculiar velocities and optical distances need their proper transfer.

If initially the emitter radiation is an unpolarized isotropic Planck distribution at the same emission proper time, collisionless Liouville transport gives \(T_{\rm obs}(n)=T_{\rm em}/(1+z(n))\). With \(H_i=H+\sigma_i\), \(\sum\sigma_i=0\), first-order \(\delta\ln T(n)=-\tau\sigma_{ij}n^in^j\), a pure traceless quadrupole. If the initial polarization density is proportional to the screen identity, free parallel transport alone keeps Q=U=V=0. **This is an exact collisionless Bianchi-I regression baseline; it does not create polarization and cannot qualify B02 full recombination/Thomson T/E/B solver.** Source code calculates the exact logsumexp redshift stably even when naive exponentials overflow. Literature basis: Pontzen & Challinor 2007 and Fleury/Pitrou/Uzan *Light propagation in a homogeneous and anisotropic universe*, arXiv:1410.8473. Full B02 needs actual collision, visibility, mode decomposition and source-validated NCP/AniCLASS transfer.

## F. S04: unknown-event mass under an **externally certified** selection-odds sensitivity \(\Gamma\)

Let a calibrated parent measure give \(P(A)\in[a,a+u]\), where \(a\) is known positive exceedance mass and \(u\) is original unknown-event mass. Suppose the *event versus complement* relative selection odds distortion is certified within \([1/\Gamma,\Gamma]\), \(\Gamma\ge1\). For a known event probability \(p\), sharp Bernoulli odds-reweighted bounds are
\[
 f_-(p)=\frac{p}{p+\Gamma(1-p)},\qquad
 f_+(p)=\frac{\Gamma p}{\Gamma p+1-p}.
\]
Monotonicity gives a conservative outer bound after selection
\([f_-(a),f_+(a+u)]\), sharp for unconstrained completion and reweighting within the stated \(\Gamma\) class. For manufactured \(a=0.3,u=0.5,\Gamma=2\), the interval is [0.176470588,0.888888889]. Without an independently bounded \(\Gamma\), this is just a sensitivity parameter, **not** a physical S04 posterior restriction. Full unknown mass u=1 remains [0,1] whatever finite Gamma is assumed. Physics coupling can reduce attainable completions, which requires separate proof.

## Claims, tests, and publication DAG policy

All examples use synthetic/deterministic inputs, not recent local CF4/Planck file downloads. Tests cover conditional mixture density (including 2D quadrature normalization), wrong-but-normalized counterexample, extreme Gaussian tails, selection score, calibration gauge, matched sky rank/enumeration, tilt anchored rank, quasar frame spin/glide, exact Bianchi-I photon momentum/redshift/blackbody/quadrupole, and Γ sensitivity. Each preexisting gate `S04,L03,H02,V03,B02,K03,K04` remains physically **UNRESOLVED** pending the documented source input. `L01,S02` still pending. This is novel *project-specific constructive linkage*, not novelty claim of selection-inference or Bianchi analytic geometry in the literature. Native subagent execution NOT_RUN (host exposes no native spawn/wait API); numerical lanes may be run as independent subprocesses with separate test files, but they are not agents.

**Next smallest physically executable tasks once local downloads finish:** (i) H02 selected W1-TF parent/child table and overlap graph, compare correct joint selection and source-anchored calibration; (ii) L03 method/mask/beam/split-injection end-to-end FFP10 null; (iii) B02 AniCLASS source-locked Bianchi-I benchmark including collisionless redshift and T/E/B after recombination; (iv) K03 galaxy+quasar crossmatch and actual weighted response singular values; (v) K04 finite-z Sachs transfer with velocity selection and bounded optical curvature; (vi) V03 remote/history source-mode transfer with local aberration anchor; (vii) S04 recompute signed sector pushforward from same valid joint source, never impute unavailable physical sectors.

### Primary literature pointers

- Tully et al., *Cosmicflows-4*, ApJ 944 94 (2023): https://doi.org/10.3847/1538-4357/ac94d8
- Boubel et al., *Testing anisotropic Hubble expansion* JCAP03(2025)066: https://doi.org/10.1088/1475-7516/2025/03/066
- Duangchan et al., *Prior-free cosmological parameter estimation of Cosmicflows-4*, A&A 708 A119 (2026): https://doi.org/10.1051/0004-6361/202556645
- Planck PR3 official simulations: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data
- Pontzen & Challinor, Bianchi CMB polarization, MNRAS 380 1387 (2007): https://doi.org/10.1111/j.1365-2966.2007.12221.x
- Fleury et al., *Light propagation in a homogeneous and anisotropic universe*: https://arxiv.org/abs/1410.8473
- Saadeh et al., *How Isotropic is the Universe?* PRL 117 131302 (2016): https://doi.org/10.1103/PhysRevLett.117.131302
- Heinesen, general optical Hubble multipoles JCAP05(2021)008: https://doi.org/10.1088/1475-7516/2021/05/008
- Manski, *Partial identification with missing data: concepts and findings*: https://doi.org/10.1016/j.ijar.2004.10.006
