# SQ-CF4 fifth-cycle theory: finite-redshift source laws, inclusion and covariance

## Scope and inherited evidence

At input HEAD eee33d7ed33e1af10d7c6a3c453810ecb227e461, R98 produced 36 overlapping-window log-distance coefficients for 35,970 groups, using 39,282 EH98 low-k quadrature directions/frequencies. Its projected covariance is a first-order model. The following construction provides source-observable maps, a joint likelihood with its normalization, a selection sensitivity bound and a matrix-free route beyond first order. Examples using released moduli condition on this registered catalogue. R78's 42 publication gates and the 60-node dependency structure retain their existing interpretation. The fitted signed log-distance STF is an apparent observational carrier. A physical shear, a matched physical null and their transported occupancy have not been supplied.

Read and used the research-loop 1.3.0 SKILL.md and references/THEORY_LOOP.md (R2–R5), POLICY_INTEGRATION.md and SUBAGENT_MODE.md. Existing checkout only. No predecessor artifact is edited by this note.

|Input in the existing checkout or its bound source directory|SHA-256|
|---|---|
|R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_THEORY.md|87dd9a47ebbff7f5fbc63389249a54dc8599fabcbc86486344f5eb665a655e19|
|R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_RESULTS.json|436630f094950d1d21d82ab61a9b587df788cc4f28c3976f5ff2b677a5350591|
|scripts/r98/cf4_p1.py|a5a2385778ff789eaa87f83e39fc29e7e2aecc76629c18c45874dd204c420c82|
|R30 fast_window_fixture_repair/science.py, resolved via cf4_p1.R30_DIR|ed9918ef9f2f12c7e6b04d5140ea8e51acd86c5fb6a541d80a27e9f42e3ad982|
|CF4 table2.dat, 55,877 galaxy rows|8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f|
|CF4 table3.dat, 38,053 grouped rows|c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d|
|CF4 table4.dat, 38,053 grouped rows|b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94|

## R2–R5. Finite-redshift observable dictionary

Use signature $(-,+,+,+)$, outward radial peculiar velocity $u>0$ for recession, $c=299792.458$ km/s and a comoving CMB-frame observer. Assume radial motion, photon number conservation, flat FLRW with $H(z)>0$, and neglect lensing, gravitational potentials, transverse velocity and source evolution in this kinematic map. Define $\chi(z)=c\int_0^z dz'/H(z')$ in Mpc and $\bar D_L(z)=(1+z)\chi(z)$. Additive source rapidity is $r=\operatorname{atanh}(u/c)$. The exact Doppler composition within these hypotheses gives $1+z=(1+\bar z)e^r$ and $\bar z=\operatorname{expm1}[\log(1+z)-r]$. Work at $\bar z>0$, i.e. $r<\log(1+z)$. Frame correction of the measured redshift alone does not establish that the flux has also been transformed to this observer frame.

For each indicator define $f_T(z,r)=\ln[D_T(z,0)/D_T(z,r)]$. Multiplying a given distance by a function of observed $z$ cancels in this *relative* response. Davis & Scrimgeour (2014) Eqs. 8–9,15 give redshift composition and the two source Doppler factors for a bolometric luminosity distance at a comoving observer; equivalently use $D_A=\chi(\bar z)/(1+\bar z)$ and $D_L=(1+z)^2D_A$. Howlett et al. (2022) Eq. 6 and Appendix D describe a comoving log-distance observable for SDSS FP. Tully et al. (2023) Eq. 3 uses a catalogue luminosity distance, whereas §4.2 describes the upstream SDSS comoving-distance PDF, its object-dependent selection normalization and group-richness correction. [Davis & Scrimgeour](https://arxiv.org/pdf/1405.0105) · [Howlett et al.](https://doi.org/10.1093/mnras/stac1681) · [Tully et al.](https://arxiv.org/pdf/2209.11238)

Let $L=\ln[\chi(z)/\chi(\bar z)]$, $K=(1+z)/[H(z)\chi(z)]$, with $K$ in (km/s)$^{-1}$. Then $\partial_r L|_0=cK$, since $\partial_r\bar z|_0=-(1+z)$ and $\chi'=c/H$. The following finite maps and derivatives are derived directly.

|Observable $T$|Source distance $D_T$ at fixed observed $z$|$f_T$|$\partial_u f_T$ at $u=0$|
|---|---|---|---|
|Background luminosity proxy|$\bar D_L(\bar z)$|$L+r$|$K+1/c$|
|Native comoving log-distance ratio|$\chi(\bar z)$|$L$, with $\eta=L/\ln 10$|$K$|
|Bolometric flux in stated observer frame|$e^{2r}\bar D_L(\bar z)=(1+z)e^r\chi(\bar z)$|$L-r$|$K-1/c$|

In R30 science.py lines 83–86, $j=-(5/\ln10)(1+z)\partial_z\ln\bar D_L(z)/c$. Consequently R98's $q_{\rm cosmo}=-(\ln10/5)j$ equals $K+1/c$. R98's $q_{\rm WF}=(1+v_f/c)/v_f$ instead comes from its log-velocity working estimator, $v_f=f_{\rm cat}cz$. At low $z$, all three kinematic derivatives have leading term $1/(cz)$. Their finite-$z$ differences of $1/c$ or $2/c$ already matter at fixed, infinitesimal $u$. Recover the zero-velocity modulus via $25+5\log_{10}(D_T(z,0)/{\rm Mpc})$. A model stochastic displacement is $-(5/\ln10)f_T$ in mag. Use survey-specific K-corrections, estimator definitions and observed frame before interpreting released mixed moduli as one of the rows. A mixture of per-galaxy pipeline estimators can also change the aggregation and noise law.

## R4–R5. A selected-mark likelihood with a shared velocity field

Fix measured redshifts, directions, target labels and group membership as design $x$. Let $F$ be the common latent field with specified pre-selection conditional law $P(dF\mid x)$. Let $p_i(dt\mid F,x)$ be the normalized law for a single source's native marks $t$ before selection; it can already integrate an independent rapidity residual, unobserved intrinsic properties, method noise and method calibration conditional on their shared nuisance values. Let $\epsilon_i(t,x,F)\in[0,1]$ be the probability to pass the upstream selection, and $K_i(dy\mid t)$ the map to a reported mark. Define

$$
 B_i(dy,F)=\int K_i(dy\mid t)\epsilon_i(t,x,F)p_i(dt\mid F,x),\qquad
 \alpha_i(F)=\int B_i(dy,F).
$$

For conditional independence of source selections and marks given the shared variables and design, the *joint* density of observed marks given that all identified targets were included is
$$
 p(dy_{1:N}\mid x,S_{1:N}=1)=
 \frac{\int P(dF\mid x)\prod_i B_i(dy_i,F)}
 {\int P(dF\mid x)\prod_i\alpha_i(F)}.
$$

Proof: the numerator is the joint included mark law, and integrating over all reported marks yields the denominator by Tonelli. Equivalently integrate $\prod_i B_i/\alpha_i$ against $P(dF\mid x,S)\propto P(dF\mid x)\prod_i\alpha_i(F)$. Substituting the pre-selection field measure into this latter representation changes the field weights. Shared method zero points integrate as shared random variables only if a law is provided; fixed external nuisance scenarios instead define a family of such ratios. Group "one or more members passes" selection, linked follow-up rules and shared observing conditions can violate mark independence. Use a group-level joint $B_g,\alpha_g$, or the actual joint inclusion law. Masking on $z$ that is already conditioned upon leaves the mark likelihood unchanged by itself. Count or spatial inference requires a parent intensity and a point-process model. In an unconditioned model with latent $\bar z$ and exact observed $z$, integrating $\delta[1+z-(1+\bar z)e^r]$ over $\bar z$ gives the prior density in $\bar z$ evaluated at the solution times $e^{-r}$. A factor in a prior per Mpc or per physical volume must include its own change of measure.

Example, for a native magnitude $m\mid F,r\sim N(M,\sigma_m^2)$ and bright-side probit selection $\epsilon=\Phi((m_\star-m)/t_s)$ with $t_s>0$ mag, $\alpha=\Phi(a)$, $a=(m_\star-M)/\sqrt{t_s^2+\sigma_m^2}$. This follows by adding an independent normal threshold error of variance $t_s^2$ and integrating the resulting normal. Differentiating $\log\alpha$ in $M$ gives the selected mean $M-\sigma_m^2\phi(a)/[\sqrt{t_s^2+\sigma_m^2}\Phi(a)]$. The hard threshold is the $t_s\to0$ limit. If $M=M(z,r)$, average the unnormalized numerator and $\alpha$ over the same residual law before division. Actual TF selection is substantially based on H I flux and FP selection involves multiple native cuts. A magnitude threshold on a registered group modulus is only a demonstrator. A raw likelihood must not reapply bias or selection correction already embedded in a released posterior or compression.

## R5. Identified quantities and partial identification

With fixed dimensionless expansion $E(z)=H(z)/H_0$ and a free additive common zero point $\Delta$ in mag, $H_0\mapsto e^s H_0$, $\Delta\mapsto\Delta+5s/\ln10$ leaves all distance-modulus predictions invariant if the selection/calibrator model supplies no external scale. Post-registration contrasts identify residual inconsistency on overlaps conditional on the published scale. They cannot recover the discarded calibration posterior or its covariance with the galaxy sample and a putative holdout.

For an individual native-mark stratum with strictly positive inclusion, the selected density is $g=s f/\alpha$. Every bounded $1\le h(y)\le\Gamma$ defines an observationally equivalent parent density $f_h=hg/E_g h$ and selection $s_h=c_0/h$ with $0<c_0\le1$. Then $\alpha_h=c_0/E_g h$. More generally these exhaust the relative inverse-inclusion functions within the specified ratio limit after rescaling. If $B$ is a measurable native-mark event and $p=P_g(B)$, its parent probability satisfies the **sharp** bounds
$$
 \frac{p}{p+\Gamma(1-p)}\ \le P_{f_h}(B)\le\
 \frac{\Gamma p}{1-p+\Gamma p}.
$$
The ratio is $E_g[h1_B]/E_g[h]$, increasing in the weights on $B$ and decreasing on its complement. The endpoint choices $h=(1,\Gamma)$ and $(\Gamma,1)$ attain the bounds. Constant inclusion gives $p$. Known hidden mass $\delta$ adds $[0,\delta]$ to $(1-\delta)$ times this support-conditional interval; if hidden mass is unrestricted the population event can be essentially unconstrained when both outcomes are possible off support. No selected-only computation identifies a finite $\Gamma$, missing-stratum weights, or the fraction of objects never eligible. Apply this bound to a specified mark stratum. The 2,048 P1 draws on an observational covariance are a different measure. They cannot be substituted for these target-level data.

## R5–R7. Magnitude response: exact finite-source check

Use R98's fixed $A$ (36 by 35,970), $y_i=\ln(v_{f,i}/H_{\rm ref})-a(\mu_i-25)$, $a=\ln10/5$ per mag, and the released fractional weights $W_{im}$ for the seven method channels. With R98's reference inverse-variance weights, standardize each channel's observed depth once at nominal $\mu$, $G_{im}=W_{im}(\mu_i-\bar\mu_m)/s_m$, including its documented low-variance fallback. Holding $G$, $A$, support and measurement errors fixed, $\mu(d)=\mu+Gd$ with $d_m$ in mag per standardized depth gives exactly
$$
 b(d)-b(0)=-a\,A G d.
$$
Thus the seven magnitude columns are $J_\mu=-aAG$. The two finite support-change columns are already differences of fitted coefficient vectors. The previous $+AG$ columns have the units and sign of additive log-$y$ tilts. An independent variance of $(0.05\ {\rm mag})^2$ in each magnitude tilt scales the seven-column covariance by $a^2=0.212075924419136$ relative to the old numerical matrix (conversion using numerical magnitudes). The sign is also required for cross-covariances with any signed nuisance.

Read-only full-source recomputation with d in channel order SNIa, FP, TFR, SBFm, SBFir, SNII, DirectCal equal to $(.011,-.021,.031,-.041,.051,-.061,.071)$ mag gave the following. Both sides were computed from original table3/4 and H03 window QR through R98 tomography. The perturbed side reconstructed the log data from the shifted moduli and independently reran all four fits.

|Numerical evidence|Value|
|---|---:|
|Maximum absolute refit shift in $b$|0.006797014627734726|
|Maximum absolute difference from $J_\mu d$|4.939625097843958e-16|
|Maximum absolute difference from historical $+AGd$|0.021556544358938945|
|Magnitude-typed seven-column covariance trace|0.0013953216797781653|
|Historical numerical seven-column covariance trace|0.006579349747501386|

Measurement here is a finite-response verification. The chosen 0.05 mag and the covariance structure remain sensitivity assumptions; this does not estimate a selection function or a rejected parent count.

## R5–R9. Full-source nonlinear moments on a Gaussian velocity design

For finite nonlinear $f_{T,i}$ a Gaussian velocity field cannot be projected after multiplying by a single derivative without approximation. A tractable scenario starts with a joint unit-normal vector $Z$, $\mathop{\rm Cov}(Z_i,Z_j)=\rho_{ij}$ from the matched low-k source operator and any separately declared stochastic small-scale component. Source positions are fixed at their observed-redshift fiducial coordinates as in R98; moving positions with latent distance requires a separate field/position likelihood. A source-wise rapidity map must enforce positive background distance. One explicit fixed-design **assumption** is a Gaussian copula with truncated Gaussian rapidity marginals:
$$
  r_i(Z_i)=(\sigma_i/c)\Phi^{-1}\!\left[\Phi(Z_i)\Phi\!\left(\frac{c\ln(1+z_i)}{\sigma_i}\right)\right].
$$
Here $\sigma_i$ in km/s scales the underlying Gaussian $c r$, rather than the final $u_i=c\tanh r_i$. The upper cut changes the prior and retains the latent Gaussian copula by construction. It differs generally from truncating a multivariate Gaussian jointly and conditioning all sources on the cut. Use log-CDFs and representable positive $\bar z$ near the upper boundary, check discarded tail probabilities explicitly. The $r\to\ln(1+z)^-$ log-distance singularity is square integrable for a bounded endpoint density.

For $g_i(Z_i)=f_{T,i}(z_i,r_i(Z_i))$, compute $a_{ik}=E[g_i(Z)\mathrm{He}_k(Z)/\sqrt{k!}]$ using probabilists' Hermite polynomials and one-dimensional Gaussian quadrature. The normal generating function gives $E[\mathrm{He}_k(Z_i)\mathrm{He}_\ell(Z_j)]=\delta_{k\ell}k!\rho_{ij}^k$ (it follows by expanding $E[e^{sZ_i-s^2/2}e^{tZ_j-t^2/2}]=e^{st\rho_{ij}}$). Hence
$$
 E[Ag]=Aa_0,\qquad
 \mathop{\rm Cov}(g_i,g_j)=\sum_{k\ge1}a_{ik}a_{jk}\rho_{ij}^{\,k}.
$$
For $S_{ij}=\sigma_i\sigma_j\rho_{ij}$ of the underlying shared-plus-independent Gaussian variable, $Q=\operatorname{diag}(a_{i1}/\sigma_i)$, the exact first Hermite contribution is $C_1=AQSQA^\top$. The discrete spectral part of $S$ uses the existing NUFFT by passing growth times $a_{i1}/\sigma_i$; propagate an independent diagonal part separately with the same $Q$. Each omitted order is PSD by the Schur product theorem, so $C-C_1\succeq0$. If $e_i=\operatorname{Var}(g_i)-a_{i1}^2$, then for any coefficient contrast $h$,
$$
 0\le h^\top(C-C_1)h\le \left(\sum_i|(A^\top h)_i|\sqrt{e_i}\right)^2 .
$$
This follows by Cauchy–Schwarz on the covariance of the omitted residuals. The bound may be conservative for an angular contrast. Small source residual fractions alone give no corresponding fractional bound after cancellation in a particular contrast. Compute the actual absolute projected envelope. Chi-square fits or tail laws based on only two moments require a separate distributional assumption. Sources of equal zero variance contribute their deterministic limits. An independent small-scale velocity enters the nonlinear map once; a fixed working weight can still be used to define $A$ without adding that noise twice. For beta-independent measurement error in reported magnitude, add its covariance once in native units after deterministic conversion.

**Stage-local numerical check.** Used the R30 flat background $\Omega_m=.3153$, $H_0=67.36$ km/s/Mpc, Gauss–Legendre distance integration of order 24, Gaussian-Hermite orders 12/24/48 and the above prior. For six benchmark redshifts (.01,.025,.04,.06,.08,.10), the central derivative at $\pm1$ km/s of the bolometric log shift agreed with $K-1/c$ to at most $3.78\times10^{-8}$ relative. Quadrature orders agreed to the displayed precision.

|Underlying $\sigma$ (km/s)|$z$|$E[f_{\rm flux}]$|$a_1/(\sigma q_{\rm flux})$|$(\operatorname{Var}f-a_1^2)/\operatorname{Var}f$|
|---:|---:|---:|---:|---:|
|150|.01|.0012691332|1.00256683|.00129905|
|150|.10|.000013822|1.00002973|.00001614|
|300|.01|.0051366445|1.01051506|.00540275|
|300|.10|.0000552949|1.00011895|.00006458|

**Computational contract.** In selected-ID order, retain H03's design or clearly version any refit. Evaluate the three typed responses, check $f(0)=0$, the signed derivative and their exact finite differences $f_{\rm proxy}-f_{\rm flux}=2r$. Use $\chi$ in Mpc, R30 $k$ in inverse Mpc, and note that the project legacy pair-velocity entry point accepts positions in Mpc/$h$ and wavenumbers in $h$/Mpc. For an independent radial-correlation check match $P$, normalization, redshift-dependent growth, $R$ and both band endpoints explicitly, and use only a small, noncoincident, representative subset. The zero-separation angular limit is $\hat n_i\cdot\hat n_j$ times the radial variance; handle coincident distinct positions explicitly. Compute the one-dimensional moments in batches, aggregate the mean and estimate/check the first-chaos operator and residual bounds before choosing higher orders. Detailed likelihood evaluation at a *given* field requires only scalar quadrature per selected group for independent residuals. Validate the probit normalization by numerical integration and a two-source/double-field example against the joint inclusion ratio. A separately integrated field scenario requires convergence diagnostics on both numerator and denominator and an honest high-dimensional error assessment. Report conditional evaluations, first-chaos projections and an actual integrated marginal likelihood under their respective names.

## R8–R9. Sources required to qualify the remaining gates

- **D01, absolute and method-relative calibration.** CF4 §10 describes the TRGB −0.05 mag shift to NGC 4258, the 489 TRGB, 76 Cepheid and six maser galaxies, with 542 unique anchors; its Table 1 lists component surveys. SH0ES provides its own data vector, calibration design and covariance. Match host aliases, PGC IDs, source roles, observations, excluded calibrators, and shared physical anchors; obtain an actual pre-intercalibration fitting likelihood or covariance and the relevant held-out split. Reusing the CF4 or CF3-tied distance as independent would count shared information again. [CF4](https://arxiv.org/pdf/2209.11238) · [SH0ES release](https://github.com/PantheonPlusSH0ES/DataRelease/tree/main/SH0ES_Data) · [Pantheon+ release](https://github.com/PantheonPlusSH0ES/DataRelease)
- **D02, native selection.** SDSS DR14 photometric/spectroscopic parent, Portsmouth measurements and Howlett §2.1 selection can support an actual FP parent-subset reconstruction. The author release v1.1.0 lists SDSS_PV_public.dat (20.2 MB, author MD5 b5b6e31caf7ea469c2ac2cb775fa8d14), randoms and mocks. Use integer objid to spectroscopic bestobjid, retain ambiguous crossmatches, trace the CF3 zero point. CF4 Table 1 lists 34,045 SDSS distances while the native catalogue has 34,059. Cf. 6dFGS native 8,885 vs CF4 table 7,099. CF4 §4.1 used 128 mocks and revised its nominal $J<13.65$ selection to $J<13.38$ for its PDF normalization. Parent survey spectra and photometry, visual rejections and group rules are distinct evidence. Kourkchi et al. provide H I flux, photometry and a BTFR-selected upstream route, whose H I limit is not a threshold on group modulus. Randoms and simulations can test a stipulated selection model; they do not enumerate historical rejected targets. [SDSS v1.1.0](https://zenodo.org/records/6824749) · [6dFGS survey](https://www.mso.anu.edu.au/6dfgs/) · [6dFGSv native table](https://www.mso.anu.edu.au/6dfgs/vfield/3dvfield.html) · [BTFR](https://doi.org/10.1093/mnras/stac303) · [EDD catalogues](https://edd.ifa.hawaii.edu/catalogs/)
- **M01, field and native likelihood.** Kinematic nonlinearity and independent small-scale dispersion are distinct from dynamically generated nonlinear peculiar velocities. The first-chaos calculation can use the EH98 band $k\in[.005,.05]\,h/{\rm Mpc}$; a matched higher-$k$ model requires justified power, coherence, smoothing and nonlinear residual ownership. Appoint an external data split with its calibrator genealogy before calling a held-out quantity an independent source test. A finite-$z$ FLRW/Doppler model supplies neither Bianchi shear nor a calibrated physical null.

Stage evidence is source-linked theory and the two executed exploratory numerical experiments above. Source qualification of the joint physical law remains open. The existing R98 covariance and Schur scores keep their historical scenario definitions.
