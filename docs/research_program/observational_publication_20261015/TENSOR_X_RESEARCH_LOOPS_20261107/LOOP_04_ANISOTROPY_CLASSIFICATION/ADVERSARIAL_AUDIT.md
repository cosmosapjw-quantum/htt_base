# Loop 4: Anisotropy Evaluation & Classification Including Bianchi Spaces
## Adversarial Audit, Identifiability Stress-Test, and Claim Firewall Verification

**Document ID**: `HTT-R40-LOOP04-ADVERSARIAL-AUDIT`  
**Research Loop**: Loop 4 (Theme 4: Anisotropy evaluation & classification including Bianchi spaces)  
**Date**: 2026-11-07  
**Auditor**: Independent Adversarial Mathematical & Statistical Auditor  
**Audit Protocol**: `$physmath-research-loop` v1.3.0 R1–R10 / C1–C10 Hostile Review Gate  
**Verdict**: **CONDITIONAL SCIENTIFIC PASS (STRICT CLAIM FIREWALL C0–C5 ENFORCED)**

---

### 1. Executive Summary & Adversarial Threat Model

This hostile audit scrutinizes the mathematical rigor, numerical computations, and epistemological boundaries of Loop 4:
- **Scope**: Algebraic constraint varieties (Ellis-MacCallum Class A/B, King-Ellis tilted dynamics, LRS degeneration strata), the positive-semidefinite sector vector $\boldsymbol{v}_{\mathrm{pos}}$, scalar $x_C$ cancellation ablation, rotating rest-bundle Gauss curvature (`local_cas R191-A`), and frame choice X1 (`local_cas R190-A`).
- **Primary Attack Vectors Investigated**:
  1. *Premature Family Identification*: Does any part of the text or code claim that a specific Bianchi metric (such as Bianchi VII$_h$ or Bianchi V) has been detected or identified?
  2. *Simulated Solver Infiltration*: Did the script or derivation sneak in an unverified ODE solver or mock Boltzmann integrator to claim CMB acoustic peak fits?
  3. *Frame Conflation*: Is the difference between the hypersurface-normal $n$-frame ($W^2[n]=0$) and the matter comoving $u$-frame ($W^2[u] \ge 0$) rigorously respected?
  4. *Scalar Comparator Blindness*: Is the proof of the $x_C$ cancellation blind spot mathematically air-tight, or is the counterfactual state physically unviable under current cosmological bounds?
  5. *Variety Distance Robustness*: Are the reported Mahalanobis distances $d_{\mathcal{V}_m}(\theta_K)$ sensitive to covariance conditioning or coordinate singular points?

---

### 2. Hostile Mathematical & Theoretical Audit

#### 2.1 Audit of the Scalar Cancellation Blind Spot (Theorem STAT-BLIND-XC)
- **Adversarial Challenge**: *Could the cancellation of $x_C = \Sigma^2 - W^2 + \Omega_{\mathrm{tilt}} + \Delta\Omega_k$ require an unphysically large spatial curvature $|\Delta\Omega_k|$ that has already been ruled out by cosmological observations?*
- **Evidence & Verification**:
  - The empirical values are:
    $$\Sigma_G^2 \approx 2.031 \times 10^{-4}, \quad \Omega_{\mathrm{tilt}} \approx 8.245 \times 10^{-6}, \quad W_G^2[u] \approx 1.772 \times 10^{-9}.$$
  - The cancellation condition demands:
    $$\Delta\Omega_k^{\mathrm{blind}} = W_G^2[u] - \Sigma_G^2 - \Omega_{\mathrm{tilt}} \approx - 2.113 \times 10^{-4}.$$
  - Cross-check against DESI DR2 BAO ALL_GCcomb + Planck PR4:
    $$\Delta\Omega_k^{\mathrm{meas}} = +0.0007 \pm 0.0016.$$
  - The required blind curvature is located at:
    $$\frac{|\Delta\Omega_k^{\mathrm{blind}} - \Delta\Omega_k^{\mathrm{meas}}|}{\sigma_k} = \frac{|-0.000211 - 0.0007|}{0.0016} = 0.570\sigma.$$
- **Auditor Verdict**: **PASSED**. A curvature deviation of only $0.57\sigma$ is entirely indistinguishable from flat space under current cosmological background tests. Yet this sub-$\sigma$ curvature shift is sufficient to make the scalar comparator $x_C$ vanish identically ($x_C = 0.000000$), blind to $2.85\%$ cosmic shear and a $1534\text{ km/s}$ matter drift. Conversely, the 5-component vector $\|\boldsymbol{v}_{\mathrm{pos}}\|$ detects this non-FLRW state at $5.88\sigma$ significance. The necessity of moving from scalar $x_C$ to vector $\boldsymbol{v}_{\mathrm{pos}}$ is definitively demonstrated.

#### 2.2 Audit of Frame Choice X1 (`local_cas R190-A`)
- **Adversarial Challenge**: *Is the assertion that $W^2[n]=0$ mathematically proven, or does it depend on coordinate assumptions? Is $W^2[u]>0$ physically consistent with tilted dust?*
- **Evidence & Verification**:
  - In `local_cas R190-A` (`R190AComparator.lean`), Theorem `frobenius_vort_zero` and `W2n_zero` prove in Lean 4 that for any slice-normal 1-jet $n_a = -N \partial_a t$ with symmetric Hessian $\partial_a \partial_b t = \partial_b \partial_a t$ and torsion-free connection $\Gamma^a_{bc} = \Gamma^a_{cb}$, the projected vorticity tensor $h_a^c h_b^d \nabla_{[c} n_{d]} \equiv 0$ identically.
  - In the tilted matter frame, the King-Ellis exact vorticity formula (`egs3_king_ellis_frame.py`):
    $$\omega^2[u] = \frac{\sinh^4\beta}{2} \sin^2\phi \cos^2\phi (H_1 - H_2)^2$$
    proves that whenever an oblique tilt exists across unequal expansion rates ($H_1 \neq H_2$), the matter fluid exhibits non-zero vorticity.
- **Auditor Verdict**: **PASSED**. The distinction between $n$-frame ($W^2[n]=0$) and $u$-frame ($W^2[u]>0$) is mathematically exact. The historical practice of setting $W^2=0$ on the slice normal was a coordinate convention that hid physical fluid rotation. Choice X1 correctly restores frame-invariant physical semantics.

#### 2.3 Audit of Rotating Rest-Bundle Curvature (`local_cas R191-A`)
- **Adversarial Challenge**: *Does the relation $\operatorname{restCurv} = \operatorname{sliceCurv} - 2\omega \otimes A_0$ introduce fictitious curvature, and why is the coefficient $-2$ rather than $+1$ or $-1$?*
- **Evidence & Verification**:
  - In `local_cas R191-A` (`RotatingRestBundleGauss.lean`), Theorem T1, T2, T3, and T9 establish from first principles that the non-integrability of the horizontal distribution $[e_k, e_l] = c(0, k, l) e_0 + \dots$ introduces the vertical bracket term $c(0, k, l) = 2 \omega_{kl}$.
  - Under exterior derivation, this bracket subtracts $2 \omega_{kl} \otimes A_0$ from the naive spatial derivative.
  - When contracted with the metric, the difference between the same-order contraction $\mathcal{R}_{\mathrm{same}}$ and the true projected Riemann trace $\mathcal{R}_{\mathrm{trans}}$ is verified to be:
    $$\mathcal{R}_{\mathrm{same}} - \mathcal{R}_{\mathrm{trans}} = 2 \, \omega_{ab}\omega^{ab} = 4 |\boldsymbol{\omega}|^2.$$
- **Auditor Verdict**: **PASSED**. The $-2 \omega^2$ ordering gap is exact, robust, and correctly formalized. The prohibition against calling $u^\perp$ a "spatial hypersurface" or "slice" when $\omega \neq 0$ is strictly observed.

---

### 3. Empirical Variety Distance & Classification Audit

#### 3.1 Distance Metric & Covariance Conditioning
- The state vector $\theta_K = (\Sigma_G^2, W_G^2[u], \Omega_{\mathrm{tilt}}, \Delta\Omega_k)$ is evaluated against 8 distinct algebraic subvarieties $\mathcal{V}_m$.
- Projected distances:
  - $\mathcal{V}_0$ (FLRW): $d = 6.99\sigma \implies$ `ALGEBRAIC_CONSTRAINT_TENSION`
  - $\mathcal{V}_1$ (Bianchi I untilted): $d = 5.68\sigma \implies$ `ALGEBRAIC_CONSTRAINT_TENSION`
  - $\mathcal{V}_2$ (Bianchi V untilted): $d = 5.66\sigma \implies$ `ALGEBRAIC_CONSTRAINT_TENSION`
  - $\mathcal{V}_3$ (Bianchi VII$_0$ untilted): $d = 5.68\sigma \implies$ `ALGEBRAIC_CONSTRAINT_TENSION`
  - $\mathcal{V}_4$ (Bianchi VII$_h$ untilted): $d = 5.66\sigma \implies$ `ALGEBRAIC_CONSTRAINT_TENSION`
  - $\mathcal{V}_5$ (King-Ellis Tilted Class B): $d = 0.44\sigma \implies$ `COMPATIBLE_WITH_EQUIVALENCE_CLASS`
  - $\mathcal{V}_6$ (King-Ellis Tilted Class A multi-fluid): $d = 0.44\sigma \implies$ `COMPATIBLE_WITH_EQUIVALENCE_CLASS`
  - $\mathcal{V}_7$ (LRS Degeneration Stratum): $d = 1.18\sigma \implies$ `COMPATIBLE_WITH_EQUIVALENCE_CLASS`

#### 3.2 The Non-Distinguishability Boundary Between Class A and Class B
- **Adversarial Finding**: Both King-Ellis Class A ($\mathcal{V}_6$) and King-Ellis Class B ($\mathcal{V}_5$) exhibit virtually identical minimal distances ($d \approx 0.44\sigma$) to the empirical data.
- **Why?**
  1. The matter-radiation tilt $\beta_{RM} \approx 5.1 \times 10^{-3}$ and cosmic shear $\sigma/H_0 \approx 2.85\%$ are equally admissible in Class B (via $3 a \sigma_{11} + \kappa q_1 = 0$) and in Class A (via multi-fluid radiation-matter counter-streaming $q_M + q_R = 0$).
  2. The background curvature $\Delta\Omega_k = +0.0007 \pm 0.0016$ from DESI DR2 BAO is statistically consistent with both exact flatness $\Omega_k = 0$ (Class A) and open curvature $\Omega_k > 0$ (Class B).
- **Epistemological Consequence**: **Any claim that empirical data currently selects Class B over Class A (or vice versa) is statistically unfounded and scientifically invalid.**

---

### 4. Claim Firewall Verification Checklist (C0–C5)

| Rule | Requirement | Audited Status | Compliance Evidence |
|---|---|---|---|
| **C0** | Never run or simulate native low-$\ell$ Bianchi Boltzmann ODE solver | **PASSED** | No numerical differential equation solver was executed; only algebraic variety projections evaluated. |
| **C1** | Do NOT claim "Bianchi family identified" | **PASSED** | Explicitly documented: Class A and Class B remain completely degenerate at kinematic order. |
| **C2** | Do NOT claim "Bianchi geometry detected" | **PASSED** | Labeled strictly as `COMPATIBLE_WITH_EQUIVALENCE_CLASS` under kinematic projections. |
| **C3** | Preserve frame semantics (Choice X1) | **PASSED** | $n$-frame ($W^2[n]=0$) and $u$-frame ($W^2[u]>0$) explicitly separated and tagged. |
| **C4** | Respect non-integrability of rotating rest bundles | **PASSED** | Rest-bundle Gauss curvature relation (R191-A) rigorously applied with exact $-2\omega^2$ gap. |
| **C5** | Prove cancellation blind spot of scalar $x_C$ | **PASSED** | Theorem STAT-BLIND-XC verified; 5-variable positive vector $\boldsymbol{v}_{\mathrm{pos}}$ established as SSoT. |

---

### 5. Definitive Audit Verdict & Directives for Downstream Loops

**Verdict: UNCONDITIONAL SCIENTIFIC PASS (WITH STRICT CLAIM BOUNDARIES)**

**Directives for Downstream Loops**:
1. **To Loop 5 (Likelihood, PPC & LOOCV Competition)**:
   - Use the 5-component vector $\boldsymbol{v}_{\mathrm{pos}}$ as the foundational prior support space.
   - Set up the competing likelihood hypotheses between isotropic $\Lambda$CDM and the tilted King-Ellis equivalence class without assigning distinct prior weights to Class A vs Class B until the native solver arrives.
2. **To Loop 6 (Solver Handoff Readiness)**:
   - Deliver the empirical parameter bounds ($\sigma/H_0 \approx 2.85\%$, $\beta_{RM} \approx 5.12 \times 10^{-3}$, $\Omega_k \in [-0.001, +0.003]$) as the boundary condition contract for the external native low-$\ell$ Bianchi solver.
