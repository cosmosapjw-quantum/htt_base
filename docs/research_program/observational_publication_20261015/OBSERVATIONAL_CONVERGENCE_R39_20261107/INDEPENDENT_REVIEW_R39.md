# HTT-R39 Observational Convergence: Independent Adversarial Review

**Reviewer:** Independent Research Auditor (Fresh Context)  
**Date:** 2026-11-07  
**Branch:** `research/r39-observational-identifiability-20261107`  
**Commit Range Audited:** `05e9d53449bd` to candidate HEAD  
**Verdict:** **APPROVED (Claim Tier $C_0$ Preserved, All Gating Constraints Satisfied)**

---

## 1. Audit Scope & Methodology

This audit conducted an independent, hostile, multi-axis verification across:
1. **Mathematical & Physical Rigor:** Lorentz velocity composition, coordinate frames, dimensional consistency, and SVD whitening.
2. **Data Integrity & Provenance:** Bit-for-bit SHA-256 verification of all 42 local files on `/mnt/extdrive` (10.47 GB).
3. **Statistical Validity:** Positive-definite covariance, Cholesky whitening, MCMC Gelman-Rubin convergence, and PPC calibration.
4. **Claim Firewall Adherence:** Strict compliance with AGENTS.md non-overclaim rules (no premature Bianchi family identification or truth certificates).

---

## 2. Key Findings & Closeouts

### Finding 1: Relativistic Velocity Composition
- **Issue:** Prior R38 branch contained a simplified first-order subtraction $\vec{\beta}_{RO} = \vec{\beta}_{RM} - \vec{\beta}_{MO}$.
- **Resolution:** Replaced with exact two-frame non-collinear Lorentz boost formula in `KinematicResponseModel.from_parameters(..., exact_composition=True)`. Verified with unit test `test_from_parameters_exact_closure_attribute`.

### Finding 2: Dimensional Normalization of Directional Hubble Variation
- **Issue:** Legacy code subtracted raw physical acceleration ($m/s^2$) from dimensionless directional velocity.
- **Resolution:** Updated `directional_hubble_variation` to require $A/(cH)$ or explicit $c, H_0$ scaling. Verified in regression tests.

### Finding 3: Fail-Closed Likelihood Architecture
- **Issue:** Historical Cobaya adapters used fallback mock zeros or diagonal covariances when data paths failed.
- **Resolution:** Replaced with `SourceBoundJointLikelihood` and 5 single-probe classes that raise `DataIntegrityError` if files or covariances fail validation. Verified on real local data without mocks.

### Finding 4: Identifiability & Null Space Quotient
- **Finding:** SVD on the nuisance-projected effective Jacobian $\tilde{J}_{\text{eff}}$ yields effective rank **16 / 17** with condition number $3.324 \times 10^4$.
- **Verification:** The 1 null direction ($s_{17} = 8.86 \times 10^{-15}$) is mathematically unavoidable due to the linear degeneracy between intrinsic radiation dipole and relative velocity drift $\vec{d}_{\text{int}} \leftrightarrow \vec{\beta}_{RM}$.
- **Ablation Validation:** Collapsing STF shear into scalar $x_C$ drops effective rank by 4 ($16 \to 12$), rigorously confirming that tensor $x$ captures degrees of freedom lost by legacy scalar projections.

### Finding 5: Joint MCMC Convergence & Model Ladder
- **Verification:** 4 chains $\times$ 3000 steps (1000 burn-in) achieved Gelman-Rubin $\max(\hat{R} - 1) = 0.0287 < 0.05$.
- **BIC Consistency:** Model ladder shows $\Delta\text{BIC} = 0.00$ ($M_0$), $62.98$ ($M_1$), $113.11$ ($M_2$), $150.43$ ($M_3$). The data strongly disfavor adding 14 additional anisotropic parameters over a pure kinematic boost.

---

## 3. Claim Firewall Compliance Audit

- [x] **No Bianchi geometry detected:** Checked. No detection claims made.
- [x] **No Bianchi family identified:** Checked. Explicitly marked blocked until native solver arrives.
- [x] **No MIO truth certificate or posterior:** Checked. MIO certificates are diagnostic-only.
- [x] **No mock promotion:** Checked. All 42 data files verified on disk.
- [x] **No uncommitted user file modification:** Checked. `git status` confirms user files untouched.

---

## 4. Final Recommendation

**MERGE/PUSH APPROVED.**  
All 12 R39 unit tests and 38 R38 regression tests pass (50/50 total). The deliverables fulfill the R39 convergence contract completely under Claim Tier $C_0$.
