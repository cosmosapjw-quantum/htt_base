# Physical interpretation of the five adaptive pushes, R27–R31

This note executes bounded R2/R3/R8 evidence reuse, premise alignment and result judgment. Requested runtime was gpt-6.1-sol/high; observed runtime is UNKNOWN. The sources are actual generated arrays, mathematical reports and independent reviews published in the five commits after c9df63efa4728255a5b785ad7cb752ecb8d8f3ef. It performs only small extraction, tensor decoding and eigendecomposition of saved aggregate arrays. It does not rerun a catalogue fit, map analysis, native solver or ODE, and does not promote any campaign acceptance.

The new empirical content is a source-selected CF4 apparent quadrupole after calibration projection and a full signed eight-map low-multipole comparison. The new spectral result is an instrument-table calculation that explains when a foreground model permits such a tensor to be isolated. The moving-lens addition supplies a physical-response correction and a fitted-estimator differential, rather than another velocity measurement. Together these are materially more informative than a list of morphology indices: they specify which signed combinations survive declared nuisance families and which physical changes remain observationally interchangeable.

## Source extent and current candidates

Per-commit paginated APIs, rather than the capped cross-branch compare, returned 102, 235, 38, 35 and 76 files for R27–R31 respectively. These are changed-file counts, not scientific result counts. Only selected scientific source files and aggregate results were retained. The relevant source records are under `sources/latest`; `retrieved_sources.json` records Git blob identities for the selected files. R31's complete accepted numerical result required a separate bounded file fetch because its commit patch was absent. That file's Git blob identity matches the retrieved bytes.

| Push | Commit | What changed scientifically |
|---|---|---|
| R27 | 4af5a2ddd5f2564a9e90455bf9f98c96d64acbec | Seven-channel release-compatible CF4 calibration response, full tensor covariance cone, seven-frequency signed E/B products |
| R28 | 71b272db893a92ec336c28164bc7efccf7c340b2 | Actual covariance-image application; calibration quotient; exact factored functional; SMICA eight-map comparison |
| R29 | e60a303120c1e26a5224cc83cd97c53c1ce78f68 | Controller/state preservation and bounded repair continuation; no new measured physical observable established |
| R30 | 6a7b25e90ee3556f67989e344f361910dfd4cedd | Moving-lens response domains, counterexample to unrestricted local advection, complete amplitude differential |
| R31 | 0d5ab96bdb55398076629099664c77517ec33bb4 | Finite seven-channel bandpass first-/second-order spectral identifiability, preserving all 24 signed target coordinates |

Current R28 exact-factor result is the metadata-repaired product, not the first factor candidate. Current eight-map interpretation is the `receipt_tail_closeout` result, not the original metadata-deficient JSON. Producer labels saying pending review are historical states: their final independent reviews establish only the declared scoped completion. Original H02/H03/H04, L03 and physical admission remain held. This note reads the actual numerical products rather than treating a PASS word as scientific evidence.

## A source-bound unit and basis correction

The actual 35,970-group E1 implementation is `htt/obsstat/cf4_apparent_kinematic_distribution.py` at the latest commit. Its retrieved SHA-256 is **843b19e464817d14455df68e9043a93cc71cc7449ab339052c3ddfe1c7298c19**, exactly the model identity frozen in the R28 result's `source_inputs.e1_design`. The local copy is `sources/latest/cf4_apparent_kinematic_distribution.py`.

The source-to-result chain is concrete:

1. Model lines 37–44 set the Frobenius-orthonormal basis, with the second tensor `diag(1,1,-2)/sqrt(6)`.
2. Model lines 80–84 define the coefficient by `H(n)/H0 = 1 + sum_a a_a T_a:n n`, and its modulus response by `delta_mu ≈ -(5/ln10)sum_a a_a(T_a:n n)`. The physical identification is explicitly conditional on absence/control of velocity, curvature and selection mixing.
3. Model lines 121–127 construct the shear columns as `-KAPPA*response` and state `shear is dimensionless`.
4. R27 `r26_cf4_release_stage_seven_channel/consume.py`, lines 446–453, imports this model and uses `B=X[:,shear]`. Lines 457–477 whiten by the magnitude metric and construct the fixed Fisher; lines 489–491 compute `M=solve(saved, Bw.T@PA)`.
5. R28 `r27_cf4_uniform_calibration_quotient_numeric/consume.py`, lines 240–252, loads the sealed same model, uses its shear columns unchanged and forms `y=dmzp-reference_mu_mag`. Lines 267 and 320–321 obtain the coefficient and decode it using that model's same STF basis.
6. R28 repaired exact-factor RESULT retains the displayed five-vector and decoded matrix, with no additional magnitude-to-rate scaling.

Therefore the actual coefficient is dimensionless; it already includes the conversion from optical magnitude residual to the declared apparent directional-rate coefficient. The correct units are

\[
 y\,[\mathrm{mag}],\quad B\,[\mathrm{mag}],\quad
 \widehat b=Ky\,[1],\quad K\,[\mathrm{mag}^{-1}],\quad
 M_7=KA_7\,[\mathrm{mag}^{-1}],\quad
 \Gamma_7\,[\mathrm{mag}^2].
\]

The working Fisher in this coefficient convention and its inverse are dimensionless (coefficient units suppressed), while the eigenvalues of `(R_F M)(R_F M)^T` retain `mag^-2`. The calibration budget `t` still has `mag^2`; its published numerical values do not need rescaling.

R28 `r27_m7_covariance_application_framing/DERIVATION.md`, lines 15–19, and the application RESULT's `units` object instead label `b` as mag, `M` as dimensionless, Fisher as mag^-2 and reference covariance as mag^2. That is a reproduced dimensional inconsistency with the sealed producer model, not a reinterpretation chosen to get a physical answer. The same framing text reverses the second basis tensor sign. Use the actual source and the decoded stored tensor. Do not apply `-ln(10)/5` to this stored coefficient a second time.

This correction is local. The restored 54-page article's 274-row B/C model and P1 `sections/03_selected_likelihood.tex` use raw STF design columns `n^T E_a n` against a magnitude response. Their coefficients are genuinely in magnitudes. P1 writes that retained coefficients are in the raw coordinates. Its 35,970-group four-window rate fit is another distinct model with dimensional rate coefficients. Sharing a catalogue name or STF representation does not make those parameterizations interchangeable.

## What the new CF4 statistic measures

Under the frozen flat reference `(H0,Omega_m)=(74.6,.3153)`, the source-selected modulus residual is projected against the inherited fourteen nuisance columns, seven singleton-channel calibration indicators and unrestricted coordinates on mixed-support rows. The target has five signed coordinates. The numerical nuisance rank is 19 and target rank five at relative thresholds 1e-12, 1e-10 and 1e-8. This means every quadrupole direction survives that particular quotient; it does not mean the sky supplies five independently calibrated physical shear measurements.

The model includes method intercepts, within-method log-redshift slopes, three bulk-velocity columns and three generic angular-dipole columns. Bulk and angular-dipole terms are nuisances here, not new physical velocity or acceleration measurements. The metric is

\[
 D_{ii}=e_{\mu,i}^2+(0.15\,\mathrm{mag})^2+
 [250\,\mathrm{km\,s^{-1}}\,j_{v,i}]^2.
\]

It is a chosen diagonal working metric. Actual inter-group, calibration, selection and peculiar-velocity covariance is not inferred from it.

The exact-factor displayed vector is

\[
 b=(-.01508104258001314,-.016431821419253857,
 .00907949492482731,.020566181835648047,.007976154841235332),
\]

and its dimensionless apparent-rate tensor is

\[
 S=\begin{pmatrix}
 -.01737217047930823&.006420172431094233&.01454248663910233\\
 .006420172431094233&.00395564447207248&.005639993176031414\\
 .01454248663910233&.005639993176031414&.01341652600723575
 \end{pmatrix}.
\]

The full matrix is necessary for model comparison and orientation. Its supplemental summaries, computed directly from this saved matrix, are

\[
 \lambda(S)=(-.023727165269042373,
 .001327948995864026,.022399216273178365),\qquad
 \|S\|_F=.03265680189321492.
\]

Within the declared apparent directional-rate parameterization, `q(n)=n^T S n` runs from **−2.3727% to +2.2399%**, a **4.61264 percentage-point** peak-to-peak quadrupolar variation. Its uniform-sphere RMS is `sqrt(2/15)||S||=.0119245780`, or **1.19246%**. These percentages are a readable description of the fitted coefficient's scale. They are not confidence bounds or measurements of physical expansion anisotropy. The equivalent *linear optical magnitude quadrupole* is `B_mu=-(5/ln10)S`, with eigenvalues approximately `(+.05152288,-.00288360,-.04863928)` mag. The sign reversal is physically sensible: at fixed redshift, greater apparent directional expansion corresponds to a smaller inferred distance and modulus in the stipulated model.

Only if a qualified observation map identifies this finite-window `S` with the same-congruence `sigma/H` could one form the physical point quantities `Sigma^2=||S||^2/6=.00017774445165` or `||sigma||/Theta=||S||/3=.01088560063`. The present results do not establish that map. These numbers are useful conditional translations, not reported physical observables.

The quotient keeps generalized information fractions

\[
 (.8358738825,.8621472192,.8749495121,.8943915217,.9168745814)
\]

relative to the saved E1 working geometry. Thus protecting against the declared calibration family costs about **8.31–16.41% of directional information**, with all five directions retained. If one additionally adopted the working metric as the true residual covariance, corresponding standard errors would inflate by about **4.4–9.4%** along these generalized directions. That last interpretation is a conditional working-law calculation; no empirical covariance or significance is supplied.

Of 35,970 rows, 944 have mixed channel support and are structurally saturated in the support-simplex quotient. The exact factored functional `K_fact=L D_diff` takes within-singleton-channel differences, so an arbitrary common additive calibration shift in each channel cancels identically. A channel with a single row has no within-channel contrast: the SBFm row 1484, group 11274, adds one more zero-leverage row, giving **945** exact zero-leverage rows after the factor correction. This is a substantive information-loss mechanism, not missing-data deletion hidden by a scalar summary.

The ideal `K_star` annihilates the support-simplex calibration family and inherited nuisance span symbolically. The earlier binary `K_hat` has only numerical calibration residuals, with raw Frobenius `||K_hat C||=1.579631719261872e-15`. Without a bound on `Gamma`, an arbitrarily small genuinely nonzero residual cannot prove finite uniform protection: `Gamma_t=t vv^T` makes `K_hat A Gamma_t A^T K_hat^T` grow without bound if `K_hat A v!=0`. The exact factor repairs calibration cancellation for its fixed family. It does not prove exact cancellation of all fourteen other nuisance columns or exact target identity: reported `||K_fact B-I||_F=2.9107538874e-15` and `||K_fact N||_F=3.0912688166e-15` remain numerical diagnostics. Nor does calibration cancellation remove residual peculiar velocities or source-selection bias outside that family.

For a physical model with parameters `p`, the actual useful comparison is to forward-process its predicted modulus field with this *same* fixed functional, `b_pred(p)=K_fact mu_pred(p)`, and compare the complete five-vector. A confidence statement additionally needs the joint residual law, including the uncertainty of any model calibration and selection. A measured nonzero vector without that law is not a sigma-level detection.

## What the covariance cone says about physical error budgets

The three retained 5×7 calibration response matrices have exact rank five when their serialized binary64 entries are interpreted as exact dyadic rationals. Consequently the image `{M Gamma M^T:Gamma>=0}` is the entire PSD cone on the five-dimensional target coefficient space. Every target covariance shape can be produced by *some* seven-channel calibration covariance. This is a precise conditional warning against declaring a tensor direction protected merely because one nominal zero-point scenario is small. It does not say that the real catalogue has that covariance or that arbitrarily large calibrations are physically plausible.

For the nominal map, working-normalized calibration eigenvalues are

\[
 (10.1025498478,.6981734341,.5055975434,.0932416551,.0428130176)
 \ \mathrm{mag}^{-2}.
\]

Under the explicit hypothetical cap `tr Gamma<=t`, the largest possible working-normalized variance is `t*lambda_max`. The first contrast can attain variance one at

\[
 t_{first}=.09898491124\,\mathrm{mag}^2,
 \quad \sqrt{t_{first}}=.31461867593\,\mathrm{mag}.
\]

The two feasible rounding representatives give `.09924026820` and `.09956796335` mag². These are comparative sensitivity scales, not measured calibration uncertainty, rejection thresholds or bounds on all physical errors. Matching the entire saved reference covariance requires `t_match=37.59135369` mag² for the nominal trace class; the minimum operator cap is `t_spec_match=23.35738185` mag². A budget sufficient to affect one fragile direction and a budget sufficient to recreate a full covariance matrix answer different questions.

The unprojected seven-channel total error model remains

\[
 \operatorname{Cov}(\widehat b)=
 [K,KA_7,KJ_v]\,
 \operatorname{Cov}(\epsilon,\eta,v)\,
 [K,KA_7,KJ_v]^T.
\]

Measurement–calibration, measurement–velocity, calibration–velocity and transpose blocks all matter; direct-anchor residual correlations also belong to the residual block. Setting these terms to zero would add an unverified physical independence assumption. The covariance cone therefore changes what must be measured or bounded before a confidence region can be physical. It is not a substitute for those measurements.

R27 additionally constructs release-stage offsets from singleton groups and then checks compatible mixed groups without retuning. The frozen relative offsets are `[0,.127,.172,.105,.095,-.084]` mag and the absolute shift is `.147` mag, with `.146–.148` or `.145–.149` quantization-feasibility ranges under the two stated conventions. Those are source-compatible reconstruction parameters and feasibility sets, not calibration posterior intervals or authoritative producer parameters. A previous `.137` model's incompatibility was a failure of that model-to-release assumption, not proof of catalogue corruption.

## What the actual eight-map CMB numbers imply

The actual data product retains **192 signed coordinates**: eight maps times `(E2[5],E3[7],B2[5],B3[7])`. Seven are Planck nominal 30–353 GHz products; SMICA is a component-separation benchmark. All use the same 30,021 of 49,152 NSIDE64 parent cells (**61.0779%**) and their native children. Galactic COSMO conventions are fixed, with no U flip; LFI native NSIDE is 1024, HFI and SMICA 2048. The sums are masked, native-pixel-center spin-2 quadratures, without beam/pixel-window correction, smoothing or common-response inference.

| Map | Full 24-coordinate Euclidean norm [microK] |
|---|---:|
| 30 | 18.71896 |
| 44 | 4.86247 |
| 70 | 1.74453 |
| 100 | 2.21568 |
| 143 | 3.88431 |
| 217 | 11.97105 |
| 353 | 95.12168 |
| SMICA | .540235 |

These norms summarize actual delivered coordinates and keep their temperature units; they are neither full-sky angular powers nor foreground amplitudes. The large frequency dependence is consistent with the need for a foreground/response model. It cannot by itself separate Galactic emission, beam effects, masked E/B mixing or noise. The full signed arrays are retained in `latest_results.json`; no row was normalized before comparison.

The E-only algorithm fits the complete 12-coordinate E contrast to 30/353 anchors relative to 143, then uses those same two coefficients to predict all twelve B contrast coordinates. The anchor singular values are `81.71285873` and `7.65971135` microK (ratio `.0937393633`). For SMICA the coefficients are `(-.01551688187,-.04277523435)`; the complete E residual norm is `.24344135` microK and the held-out B residual norm is **.37923421 microK**. Corresponding B residual norms for 44/70/100/217 are `.91350892/.92938155/.88679752/.57762734` microK.

One transparent signed example is SMICA's 143-relative `B2:-sqrt(2)Im2`: observed `-.02733660` microK, E-fit prediction `-.32893497` microK, target-minus-prediction `+.30159837` microK. This directly measures how much that fixed finite E-to-B mixing rule misses one retained coordinate. It does not reject a physical foreground law or primordial-B null without a joint distribution for all the data and responses. The two fitted coefficients are signed regression weights, not physical mixture fractions. SMICA is not an independent sky, true-CMB oracle or eighth frequency, so smaller SMICA amplitude or residual cannot be counted as independent confirmation.

The seven-frequency `Q` values divide each norm by the explicit **10 microK** reference. They provide a finite frequency image with mass `1/7` at each channel. This computational CDF is not a sky filling fraction, occurrence probability or depth relation. Frequency is not redshift, so `G_F` is inapplicable here. The outer products of retained coordinates are deterministic uncentered products, not estimated stochastic covariance.

## R31 explains a real limitation of that separation problem

R31 uses actual released LFI R3.31/HFI R3.00 tables to evaluate a declared spectral model, rather than fitting observed sky. The seven CMB responses are `a=(1,...,1)`. First order admits synchrotron amplitude and index plus dust amplitude, index and temperature moments: five nuisance columns. Second order adds four more moments. Dust temperature coordinate is `t=(T-T_d)/T_d`; `S_d,tt=T_d^2 partial_T^2 S_d`, not a repeated logarithmic derivative. Moment coefficients are freely signed and independent in every retained tensor coordinate. This is a linear relaxation of a physical spectral expansion, so not every admitted coefficient array must arise from a nonlinear physical foreground.

The complete model is

\[
 Y=a s^T+F U,\qquad Y\in\mathbb R^{7\times24},\qquad
 A=a\otimes I_{24},\quad B=F\otimes I_{24}.
\]

With `P_F=I-FF^+`,

\[
 \operatorname{rank}[(P_F\otimes I_{24})A]
 =\begin{cases}24,&P_Fa\ne0,\\0,&P_Fa=0.\end{cases}
\]

This exact conditional identity applies to the full signed tensor, not a scalar amplitude. The data-table calculation supports the following cases across all six fixed LFI-convention/HFI-threshold branches:

| Quantity | First-order five-column family | Second-order nine-column family |
|---|---:|---:|
| Numerically resolved foreground rank | 5 | 7 |
| Augmented CMB+foreground rank | 6 | 7 |
| Smallest unit-column singular value | .0687691–.0688226 | .00552640–.00554409 |
| Resolved condition number | 21.9414–21.9633 | 390.347–391.826 |
| CMB–foreground principal-angle sine | .0384452–.0385397 | about 1e-16 |
| Retained signed target coordinates | 24 | 0 |

At first order a CMB-preserving annihilator exists in the stipulated model:

\[
 w=P_Fa/(a^TP_Fa),\qquad H=w^T\otimes I_{24},\quad
 HA=I_{24},\ HB=0.
\]

For branch `A_BT_1e-07`, the seven signed weights are approximately `(.4183405,-3.2500028,6.5487953,1.8380208,-6.0620767,1.5577579,-.0508349)`. Their Euclidean norm is `9.80717` (all branches `9.80716–9.83124`), displaying strong cancellation. Under the *additional hypothetical law* of equal independent noise `sigma^2 I`, the combined standard deviation would be `||w|| sigma`, around 9.8 times one channel's noise. No actual noise covariance was used, so this is a conditioning illustration, not measured noise.

At second order the finite matrix has full row rank. The stored witness `F2 c≈a` has relative residual `1.67e-15–1.39e-14` across the full 24-coordinate controls. For branch A the nine coefficients are approximately `(.4572242,.9876686,.9397699,8.8379699,-14.1702350,1.4394318,38.3878967,-42.0274799,5.3135951)`. For *every* signed target shift `v`, the shifts

\[
 \delta s=v,\qquad \delta U=-c v^T
\]

leave the modelled seven-channel data unchanged. This is a physical identifiability issue for the *declared foreground family*: seven-channel data cannot distinguish a CMB tensor perturbation from those admitted spectral moments under the common spatial response. It demonstrates why a technically correct first-order cleaning operation can give an answer dependent on an insufficient foreground model.

The obstruction is not a universal CMB-separation no-go. Qualified moment/remainder bounds, nonlinear relations, priors or sign restrictions, additional frequencies and independent spatial information can reduce the nuisance family or add response directions. A blackbody-spectrum nuisance with the same spatial operator remains exactly confounded irrespective of the dust/synchrotron calculation. More precision in the same seven numbers cannot resolve identical responses.

Actual use on the observed eight-map carrier still needs component-dependent polarized spatial response, beam/scan/mapmaking effects, omitted angular and frequency-domain terms, and a joint residual law. Six finite reader/threshold branches are reproducibility and sensitivity models, not a calibrated response-uncertainty set. No observed quotient tensor, physical amplitude, null probability or confidence region was measured in R31.

## R30: which moving-lens physics survives a scalar amplitude

For a rigid potential translated with coherent bulk velocity, with weak scalar fields, Born paths and negligible intrinsic evolution,

\[
 \Theta_{ML}=-2\int d\chi\,\beta^a_{bulk,\perp}
 \partial_{\perp a}\phi=-\alpha_a\beta^a_{bulk}.
\]

Here `phi=Phi_W/c^2`, `beta=v/c` and the unreduced deflection `alpha` are dimensionless; `Theta=DeltaT/T0`. This is a clean physical meaning: the signal responds to transverse *coherent potential translation*. It does not identify a fitted template amplitude with a signed velocity or matter vorticity.

The revised report supplies a constructive counterexample to replacing the coherent velocity by an arbitrary spatial matter velocity. On a fixed zero-mean periodic snapshot domain, Poisson and continuity give

\[
 \phi'_v=-\kappa\nabla^{-2}\nabla\cdot[(1+\delta)v].
\]

For `phi=epsilon cos(kx)` and `v=V sin(qy)e_x`, the actual velocity-induced derivative has amplitude `k^2/(k^2+q^2)` times the local-advection expression. At `q=k` it is **one half**. The bulk/short-potential limit `q/k->0` recovers the leading advection approximation. This is a direct mechanism and domain boundary, not an unsupported prohibition on moving-lens inference.

A separate spherical internal-rotation snapshot has `v=Omega cross r`, `curl(v)=2Omega`, but vanishing velocity-induced scalar potential evolution. Thus nonzero local vorticity need not appear in this scalar ISW channel at that order. This is not a full Euler/Einstein solution, an actual-survey null or a Bianchi no-go. Potential-only reconstruction is longitudinal in Fourier space, but projection/density weighting can create angular curl, `curl(rho vhat)=grad(rho) cross vhat`; an angular TC parity test therefore cannot be relabelled a general physical vorticity bound.

The fitted amplitude also has a response beyond fixed weights. For `A=C^-1`, `h=t^TAt`, `bhat=t^T A d/h`,

\[
 d\widehat b={t^TA\,dd+(dt)^TA(d-2\widehat b t)
 -t^TA(dC)A(d-\widehat b t)\over h}.
\]

Changing data can change the empirical covariance, template or selection; the last two terms cannot be discarded merely by fixing the observed projected template. A scalar amplitude can compress different underlying velocity/foreground changes into the same number. In the source parameterization, a velocity-template correlation times a galaxy-potential calibration is invariant under reciprocal rescaling of the factors. In a thin patch, `Theta=alpha dot(s-beta)` is invariant under `beta->beta+q, s->s+q` when the lensing-gradient nuisance is unconstrained. External calibration and a joint covariance can break those conditional ambiguities; another transformation of the same amplitude summary cannot.

The published R30 intake's bounded primary-link search did not obtain the measurement-specific numerical TG/TC bands, full covariance and realized physical calibration. This note does not independently assert current universal internet absence. ACT cosmology covariance is a different product, and raw ACT/DESI input availability alone does not supply the measurement's physical response. R30 accordingly supplies theory useful for a future response calculation and keeps K03's original physical `omega/A/beta` requirement unresolved. It adds no new observation or calibrated physical amplitude bound.

## Decision and constructive next use

The new CF4 statistic says that a five-coordinate apparent quadrupole remains after removal of a declared additive calibration family, at a measured finite coefficient scale and explicitly quantified working information cost. It does not calibrate its significance or identify geometric shear. The eight-map data say which complete signed coordinates and E-to-B regression residuals are present in delivered masked maps. They do not separate sky components without response and joint-noise assumptions. R31 shows that adding physically motivated foreground freedom can destroy the very spectral identifiability a first-order cancellation assumes. R30 identifies which moving-lens response and derivative are needed before interpreting a scalar amplitude as a physical velocity constraint.

The resulting constructive program is specific: correct the local units/basis labels while preserving numerical arrays; forward-process candidate physical models through the same source-bound CF4 functional; obtain or bound the residual and selection/PV law; qualify the component-dependent CMB response and foreground-remainder class; and obtain measurement-specific moving-lens bands, calibration and joint covariance. Those additions would turn existing measured combinations into model tests. Current exact algebra, finite-data statistics and unresolved physical transport are kept as distinct evidence levels.

`latest_extract.py` creates `latest_results.json` directly from the retained products and checks STF decode, trace and norm parity. Actual output: zero decode difference; trace `-1.734723475976807e-18`; zero coefficient/tensor norm difference. This is an aggregate arithmetic check, not an independent scientific rerun or additional review layer. No global cosmological no-go or new formal campaign admission is proposed.

Skill context used: physmath-research-loop 1.3.0 SKILL.md; THEORY_LOOP.md selected R2/R3/R8 definitions; POLICY_INTEGRATION.md; SUBAGENT_MODE.md; latest repository AGENTS supplied by parent. No recursive delegation or review was performed. Parent owns integration and durable delivery.
