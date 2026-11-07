# Loop 6: Distinguishing Local Boost vs. Global Tilt
## Hostile Adversarial Audit, Systematics Interrogation, and Claim Firewall Verification

**Document ID**: `HTT-R40-LOOP06-ADVERSARIAL-AUDIT`  
**Research Loop**: Loop 6 (Theme 6: Distinguishing local boost vs. global tilt)  
**Date**: 2026-11-07  
**Auditor**: Independent Adversarial Mathematical & Statistical Auditor  
**Audit Protocol**: `$physmath-research-loop` v1.3.0 R1–R10 / C1–C10 Hostile Review Gate  
**Verdict**: **CONDITIONAL SCIENTIFIC PASS (STRICT CLAIM FIREWALL C0–C5 ENFORCED)**

---

### 1. Scope & Mandate of the Adversarial Audit

This hostile review interrogates the theoretical derivations, empirical calculations, and statistical claims presented in Loop 6:
- 4-Hypothesis competition: $H_0$ (Isotropic FLRW), $H_{\mathrm{loc}}$ (Pure Local Boost), $H_{\mathrm{tilt}}$ (Global Tilt Candidate), and $H_{\mathrm{mix/sys}}$ (Signal + Systematics Mixture).
- Bijective tensor depth path: $G_F = \mathbf{T} \boldsymbol{x} = (\bar{F}, \mathbf{H} \boldsymbol{x})$ evaluated across 9 tomographic shells spanning $z \in [0.005, 1089.0]$.
- Response overlap and principal angle audit: $\rho_{LB, GT}$, $\sigma_k$, and subspace angles $\theta_k$ against Galactic dust and survey selection templates.
- Volterra relaxation operator and Gronwall stability witness (PR-171 / egs3 / PR-223).
- Structured-null competition engine false-positive rates (FPR).

The auditor’s objective is to determine whether the apparent rejection of the pure local boost hypothesis $H_{\mathrm{loc}}$ ($\Delta\mathrm{BIC} = 25.67$, $\chi^2_{\mathrm{gap}}/\nu = 4.31$) is a true cosmological detection or an artifact of unmodeled selection functions, tracer incompatibilities, or correlated cosmic variance.

---

### 2. Hostile Interrogation of the Depth Gap $G_F \neq 0$

The central empirical result of Loop 6 is that the bijective depth path tensor $\mathbf{H} \boldsymbol{x}$ is non-zero at $> 4\sigma$ significance ($\chi^2_{\mathrm{gap}} = 103.49$ for 24 dof, $p = 1.8 \times 10^{-11}$). The auditor investigates three potential non-cosmological failure modes:

#### 2.1 Failure Mode A: Physical Tracer Incompatibility (Peculiar Velocities vs. Number Counts)
- **Hostile Indictment**: Low-z shells (CF4, SDSS PV, Pantheon+) measure direct metric distance-redshift departures, yielding physical peculiar velocities $v_{\mathrm{pec}} \approx 360 - 380\ \mathrm{km/s}$ consistent with the CMB dipole. Mid-to-high-z shells (Quaia low-z, Quaia high-z, CatWISE, NVSS), however, measure *angular number count dipoles* $D$. Converting $D$ to an effective velocity $\beta_{\mathrm{eff}} = D / K_{\mathrm{EB}}$ requires the Ellis-Baldwin kinematic factor:
  $$K_{\mathrm{EB}} = 2 + x(1 + \alpha),$$
  where $x = 2.5 \frac{d\log_{10} N}{dm}$ is the faint-end logarithmic count slope and $\alpha$ is the spectral index ($S_\nu \propto \nu^{-\alpha}$). If $K_{\mathrm{EB}}$ is underestimated due to redshift evolution in the luminosity function or incorrect spectral assumptions, the apparent velocity $\beta_{\mathrm{eff}}$ will be artificially inflated, creating an entirely spurious depth gap!
- **Audited Defense & Evidence**:
  1. In Loop 2, empirical magnitude slopes were measured directly from the Quaia catalogs near the completeness limits ($G = 20.0$ and $G = 20.5$), yielding $x \approx 1.392$ and $s \approx 0.557$. To reduce $\beta_{\mathrm{eff}} \approx 4.3 \times 10^{-3}$ down to the CMB kinematic value $\beta_{\mathrm{CMB}} \approx 1.23 \times 10^{-3}$ would require $K_{\mathrm{EB}} \approx 14.2$, corresponding to an impossible logarithmic count slope of $x \approx 8.1$ (or $s \approx 3.25$). No known quasar population exhibits such an extreme slope.
  2. The depth gap is corroborated by independent tracers: DESI directional BAO scale shifts at $z \sim 0.7$ also show an anisotropic scale modulation ($\Delta \alpha / \alpha \sim 0.8\%$) aligned within $20^\circ$ of the quasar count dipole, completely independent of the Ellis-Baldwin formula.
- **Auditor Verdict**: Tracer incompatibility alone cannot explain the factor of $\sim 3.5$ amplitude discrepancy. However, second-order magnification bias and redshift-dependent spectral index gradients must be explicitly marginalized before elevated claim tiers can be admitted.

#### 2.2 Failure Mode B: Solar System Acceleration vs. Cosmic Drift in Astrometry
- **Hostile Indictment**: Gaia DR3 CRF3 astrometry exhibits a proper motion glide of $\mu = 5.44 \pm 0.16\ \mu\mathrm{as/yr}$. A careless analysis might treat this as high-redshift matter drift.
- **Audited Defense**: The analysis in `run_loop06_local_vs_global_analysis.py` explicitly isolates the Gaia astrometric vector as a local observer acceleration $A/c = (2.51 \pm 0.15) \times 10^{-10}\ \mathrm{m/s^2}$ pointing toward the Galactic Center ($l \approx 268^\circ, b \approx -19^\circ$). It assigns Gaia an independent physical response weight ($\mathcal{R}_{\mathrm{tilt}} = 0.20$), preventing it from corrupting cosmological tilt inference.
- **Auditor Verdict**: Astrometric glide is properly localized; no observer-drift conflation detected.

---

### 3. Response Overlap & Nuisance Orthogonality Stress-Test

The response overlap audit (`htt/departure/response_overlap.py`) evaluates the principal angles between the 2D Signal Subspace $\mathcal{S} = \operatorname{span}(\boldsymbol{r}_{\mathrm{loc}}, \boldsymbol{r}_{\mathrm{tilt}})$ and the 2D Nuisance Subspace $\mathcal{N} = \operatorname{span}(\boldsymbol{t}_{\mathrm{dust}}, \boldsymbol{t}_{\mathrm{sel}})$.

#### 3.1 Subspace Geometry Audit
- **Measured Principal Angles**:
  $$\theta_1 = 16.02^\circ \quad (\cos \theta_1 = 0.9612),$$
  $$\theta_2 = 45.80^\circ \quad (\cos \theta_2 = 0.6972).$$
- **Audited Finding**: While the subspace intersection is strictly trivial ($\mathcal{S} \cap \mathcal{N} = \{ \mathbf{0} \}$), the first principal angle $\theta_1 = 16.02^\circ$ is relatively small. This indicates that a linear combination of Galactic dust extinction and survey footprint selection functions possesses a non-negligible projection onto the depth-varying tilt response.
- **Residual Projection Check**: After orthogonal projection $\mathbf{P}_{\mathcal{N}}^\perp$, the projected singular values of the signal matrix are $\sigma_1 = 11.043$ and $\sigma_2 = 4.009$. Both remain well above the zero-threshold ($\tau = 10^{-12}$).
- **Adversarial Caveat**: Because $\theta_1 = 16.02^\circ$, any unaccounted non-linear coupling between dust and stellar contamination (e.g., in low-latitude $|b| < 20^\circ$ quasar selection) could leak into the tilt amplitude. Complete sky-mask marginalization must be retained as an open condition.

---

### 4. Fatal Structured-Null Finding: Correlated LSS Bulk Flows

The most critical hostile result emerges from the **Structured Null Competition Engine** (`evaluate_structured_null_competition`).

#### 4.1 False-Positive Rate Breakdown
When 1,000 synthetic Monte Carlo null realizations are injected with zero intrinsic tilt ($\boldsymbol{\beta}_{\mathrm{tilt}} = \mathbf{0}$) but subject to realistic survey noise and cosmic variance, the false-positive rates (where $H_{\mathrm{tilt}}$ is falsely preferred over $H_{\mathrm{loc}}$ by $\Delta\mathrm{BIC} > 6.0$) are:
- `null_shot_noise`: $\mathrm{FPR} = 0.001$ ($0.1\%$) $\rightarrow$ **ROBUST**
- `null_dust_gradient`: $\mathrm{FPR} = 0.012$ ($1.2\%$) $\rightarrow$ **ROBUST**
- `null_survey_footprint`: $\mathrm{FPR} = 0.232$ ($23.2\%$) $\rightarrow$ **VULNERABLE**
- `null_lss_bulk_flows`: $\mathrm{FPR} = 0.548$ ($54.8\%$) $\rightarrow$ **CRITICAL FAILURE**

#### 4.2 Physical Mechanism of the LSS Failure Mode
- **The Core Flaw**: Under standard $\Lambda\mathrm{CDM}$, the local universe within $z \lesssim 0.05$ (CF4, SDSS PV) is subject to coherent bulk flows sourced by nearby matter overdensities (the Great Attractor, the Perseus-Pisces supercluster, the Shapley Concentration) with root-mean-square amplitude $\sigma_v \sim 250 - 350\ \mathrm{km/s}$.
- Conversely, at high redshift ($z \ge 0.5$, Quaia, DESI), the volume-averaged LSS cosmic variance drops dramatically ($C_{1, \mathrm{LSS}} \propto \int P(k) W(k)^2 dk \sim 10^{-5}$).
- Consequently, if local bulk flows pull the low-z tracers away from the CMB dipole or alter their measured vector relative to the distant universe, **a naive depth-gap test that assumes uncorrelated diagonal errors across shells will falsely attribute this transition to an evolving cosmological tilt $\beta_{RM}(z)$ in $54.8\%$ of all realizations!**
- **Decisive Conclusion**: Without full cross-tracer Limber covariance $C_1^{pq}$ and explicit forward-modeled LSS bulk flow fields, the depth gap $G_F \neq 0$ **cannot** be declared an intrinsic global cosmological tilt. It is entirely consistent with a standard local LSS bulk flow perturbing the low-z shells against an unperturbed high-z background!

---

### 5. Model Overfitting & Complexity Penalization

- In the 4-hypothesis competition, $H_{\mathrm{tilt}}$ achieves $\Delta\mathrm{BIC} = 25.67$ relative to $H_{\mathrm{loc}}$ ($\Delta\chi^2 = 35.56$ for $\Delta k = 3$).
- Under AIC ($2k$ penalty), $\Delta\mathrm{AIC} = 29.83$.
- Under BIC ($k \ln N$ penalty), the penalty for 3 parameters is $3 \ln(27) = 9.89$.
- The $\chi^2$ improvement ($\Delta\chi^2 = 35.56$) comfortably exceeds both AIC and BIC thresholds.
- However, as proven in Section 4, BIC assumes independent identically distributed errors and fails to penalize model flexibility when the true null distribution has broad covariance tails. Therefore, the nominal BIC posterior weight ($P = 81.54\%$) is **uncalibrated** and must not be interpreted as a true Bayesian posterior probability.

---

### 6. Claim Firewall Verification (C0–C5 Compliance)

The dossier and associated script have been audited against the repository-wide Claim Firewall rules (AGENTS.md / PR-171 / PR-223):

1. **Rule 1 (No Premature Family Identification)**:
   - *Audit Check*: Does the text mention Bianchi Type I, Type $\mathrm{VII}_h$, or Type IX geometry identification?
   - *Result*: **PASS**. The dossier strictly describes the phenomenon as a *"local/global discrimination candidate"* and an *"anisotropic shear candidate"*. No family identification is claimed.
2. **Rule 2 (No Truth Certificates)**:
   - *Audit Check*: Are certificates or model weights labeled as "truth certificates" or "MIO posteriors"?
   - *Result*: **PASS**. All certificates are explicitly designated as *diagnostic-only rank audits* and *candidate model weights*.
3. **Rule 3 (Transfer Source Provenance)**:
   - *Audit Check*: Are external transfer models falsely attributed to native solvers?
   - *Result*: **PASS**. Volterra memory is verified as an exact class-conditional mathematical theorem, not an unvalidated Boltzmann solver output.
4. **Rule 4 (Quarantined Inputs)**:
   - *Audit Check*: Does the analysis read forbidden or quarantined CF4 raw payloads without authorization?
   - *Result*: **PASS**. CF4 group kinematic observables are accessed strictly through the frozen, verified pooled methods operator (`selected_source_observables.npz`), preserving all audit safeguards.

---

### 7. Final Hostile Verdict & Required Qualifications

**Final Verdict**: **CONDITIONAL SCIENTIFIC PASS (STRICT CLAIM FIREWALL C0–C5 ENFORCED)**

#### Mandatory Qualifications for Publication:
1. The rejection of the pure local boost $H_{\mathrm{loc}}$ ($\chi^2_{\mathrm{gap}}/\nu = 4.31$) must be explicitly reported as **"conditional on diagonal LSS cosmic variance"**.
2. The finding that structured LSS bulk flows produce a false-positive rate of $\mathrm{FPR} = 54.8\%$ must be featured prominently in the abstract and conclusion of any resulting paper or report.
3. The global tilt hypothesis $H_{\mathrm{tilt}}$ must remain classified under **Claim Tier C0 (Diagnostic Candidate Only)** until joint multi-tracer Limber cross-covariance matrices are fully implemented.
