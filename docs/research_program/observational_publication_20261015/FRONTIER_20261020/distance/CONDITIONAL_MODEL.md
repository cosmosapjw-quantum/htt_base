# A source-bound joint calibration / flow contract

Owner `htt`; C0; `SPECIFIED`, non-claim-bearing. No transfer function or native solver. Requested worker gpt-6.1-sol/high; observed runtime UNKNOWN. This is a candidate for a conditional analysis of cached observations. It does not close H02, S02, S04 or K04.

## Primary source and factorization

Stiskalek, Desmond & Lavaux, [arXiv:2509.14997v2](https://arxiv.org/html/2509.14997v2), published [MNRAS 546, staf2048](https://doi.org/10.1093/mnras/staf2048), supplies a joint TFR calibration/flow model. Section 3.1 equations (6)–(8) and Appendix A equations (23)–(33) define this schematic per-source factorization:

\[
L_i(\theta)=\int dr_i\,d\eta_i\;
\pi(r_i\mid\theta)\pi(\eta_i\mid\theta)
\frac{N(cz_i;cz_{\rm pred},s_{zi})
N(m_i;\mu(r_i)+M(\eta_i)+\boldsymbol d\cdot\hat n_i,s_{mi})
N(\eta_i^{\rm obs};\eta_i,\sigma_{\eta i})}{A_{\eta i}(\theta)}.
\]

Here normals use standard deviation, \(s_{zi}^2=\sigma_v^2+\sigma_{cz,i}^2\), \(s_{mi}^2=\sigma_{\rm int}^2+\sigma_{m,i}^2\), \(A_\eta\) normalizes observed-linewidth truncation, and \(\pi(r)\propto n(r)r^p\exp[-(r/R)^q]\) has its parameter-dependent normalization. The radial prior is phenomenological; it is not the missing full HI parent selection. The source uses CMB redshift, flat FLRW comoving distance, and \(h^{-1}\,\mathrm{Mpc}\). The SN likelihood instead couples all magnitudes through a covariance matrix; distances cannot then be independently integrated source by source.

The [July 2026 follow-up](https://doi.org/10.1093/mnras/stag1266), sections 4 and 7, fixes the radial Jacobian to \(r^2\), samples radial incompleteness and density bias, and uses a diagonal residual-redshift covariance. It expressly leaves more complete selection and residual-velocity correlations unresolved. It is a useful conditional law, not a supplied full composite-CF4 angular calibration/selection law.

## Derived response within this source model

These equations are our differentiation of the source model, not a new upstream physical result. Define \(z=z_{\rm cosmo}\), positive receding radial velocity \(u\) in km/s, fixed observed CMB redshift and fixed sky direction. The source model sets

\[
1+z_{\rm obs}=(1+z)[1+u(z,\boldsymbol a)/c],\qquad
d_L=(1+z)r(z),\qquad \mu=5\log_{10}(d_L/\mathrm{Mpc})+25.
\]

For a nuisance coefficient \(a\), differentiate the first equation implicitly:

\[
D=c+u+(1+z)\partial_z u,\qquad
\partial_a z=-\frac{(1+z)\partial_a u}{D},
\]

\[
\boxed{\partial_a\mu=-\frac{5}{\ln10}
\frac{1+(1+z)r'(z)/r(z)}{D}\,\partial_a u.}
\]

The denominator includes the radial gradient of the existing flow field. Setting \(\partial_z u=0\) defines a separately declared frozen-flow response. For \(u=\hat n\cdot[\beta v(r\hat n)+\sum_k B_k(r)\boldsymbol a_k]\), the direct derivative is \(\partial_{a_{kj}}u=B_k(r)\hat n_j\); the radial derivative in \(D\) still includes the background field and basis gradients. A zero of \(D\), or multiple distance roots, invalidates deterministic inversion. The latent-distance likelihood remains the appropriate source model in that case.

Calibration columns are \(X_{ij}=\hat n_{ij}\). Flow columns are \(U_{i,kj}=K_i B_k(r_i)\hat n_{ij}\), where \(K\) is the boxed prefactor. Units are mag and mag/(km/s), respectively. In the frozen, low-redshift limit, \(K\simeq-5/(\ln10\,cz)\): positive unmodelled recession lowers inferred cosmological distance at fixed observed redshift. A distance-proportional velocity dipole can therefore mimic an angular calibration dipole in this model. This supplies a concrete nuisance-response rank question.

This is a redshift-distance forward-model response. It does not include the full source/observer luminosity-distance Doppler, beaming and aberration terms; it is not a source-matched GR optical-to-kinematic kernel, a same-congruence STF/shear mapping, or K04/S02 admission evidence.

## Two constructive covariance branches

**Branch A: fixed public total covariance, deterministic mean only.** Reuse the actual cached Pantheon rows and full public covariance once, with its established symmetric-part handling. Declare a working Gaussian law
\(m\sim N(m_0+X\boldsymbol d+U\boldsymbol a+Z\boldsymbol\gamma,C_{\rm public})\), conditional on observed directions/redshifts, chosen baseline and declared nuisance columns. Use the covariance as the total released residual covariance; add no second stochastic PV covariance and integrate no additional latent PV uncertainty over the same term. A deterministic mean extension is permitted. Its scientific calibration remains conditional on the working law and selected sample. A weighted quotient of \(X\) against \([U,Z]\) determines which angular combinations survive in this declared model. Reuse the cached D03 sufficient arrays; this note authorizes no catalogue rerun.

**Branch B: reproduce the paper's explicit latent velocity/distance model.** Section 3.2 states that its Pantheon magnitude covariance had PV contributions removed using a matrix supplied privately by Anthony Carr. That exact matrix was not acquired. One needs a source-qualified decomposition, or a justified new joint covariance, before adding stochastic PV uncertainty to the public total covariance. No ad hoc subtraction is licensed by the source. Missing this private component prevents this exact paper replay, not every conditional deterministic-mean analysis.

For either branch, CF4 and Pantheon share contributors and calibration ancestry. This contract supplies no cross-catalogue covariance. A joint catalogue likelihood, source independence, coverage, calibrated significance and physical-anisotropy inference remain unqualified. Keeping a fixed total covariance does not make a selected angular sample representative.

## Scope audit

Evidence read: original DAG/resume/assessment; D03 host comparison; grouped-flow conflict report; the two primary articles; author compilation notebook; six-row NumCosmo fixture; claim-firewall/provenance and physics-math skills. Proposed change: source-bound conditional model specification and acquisition guidance only. Validation: algebraic implicit differentiation, dimensions, sign and low-z limits inspected; safe fixture parse run separately. No science fit or posterior executed. Kill switches: missing covariance identity, invalid response units/frame, nonmonotone distance inversion, or attempts to infer parent selection/crosscovariance from the six-row excerpt. No original node or permanent claim ledger is promoted.
