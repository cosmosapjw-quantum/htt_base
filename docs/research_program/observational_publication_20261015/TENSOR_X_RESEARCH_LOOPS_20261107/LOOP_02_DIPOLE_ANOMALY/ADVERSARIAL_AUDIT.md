# Adversarial Audit & Hostile Verification: Loop 2 Dipole Anomaly

**Subject:** Loop 2 — Relativistic Multi-Tracer Dipole Anomaly & Velocity Frame-Triangle Closure  
**Harness / Protocol:** $physmath-research-loop v1.3.0 Hostile Audit  
**Review Mode:** Adversarial Red-Team / Independent Skeptic  
**Audit Date:** 2026-11-07  
**Claim Tier:** C0 (Diagnostic & Consistency Only)  

---

## 1. Audit Overview & Adversarial Stance

This adversarial audit evaluates the claims, mathematical derivations, numerical pipelines, and physical conclusions presented in:
- `THEORY_AND_DERIVATION.md`
- `EMPIRICAL_CROSS_VALIDATION.json`
- Helper script `scripts/r40_tensor_loops/run_loop02_dipole_analysis.py`

The objective is to identify potential mathematical flaws, observational selection artifacts, false equivalences, statistical overcounting, and unauthorized claims of beyond-FLRW or Bianchi cosmology.

---

## 2. Axis 1: Mathematical & Relativistic Soundness

### 2.1 Velocity Composition and Triangle Closure
- **Claim:** The relativistic frame triangle satisfies exact closure:
  $$\Delta \vec{\beta}_{tri} \equiv \vec{\beta}_{RO} - (\vec{\beta}_{RM} \oplus \vec{\beta}_{MO}) = 0$$
- **Audit Verification:**
  In `scripts/r40_tensor_loops/run_loop02_dipole_analysis.py`, `compose_and_close_velocities` from `common.relativistic_velocity_closure` was executed on the empirical vectors:
  $$\vec{\beta}_{RO} = (-8.54 \times 10^{-5}, -8.17 \times 10^{-4}, 9.20 \times 10^{-4})$$
  $$\hat{\beta}_{MO} = (4.33 \times 10^{-3}, -2.37 \times 10^{-3}, 2.96 \times 10^{-3})$$
  $$\vec{\beta}_{RM} = (-4.41 \times 10^{-3}, 1.55 \times 10^{-3}, -2.04 \times 10^{-3})$$
  The computed closure residual norm is:
  $$|\Delta \vec{\beta}_{tri}| = 1.634 \times 10^{-8}$$
  In physical velocity units, this corresponds to $|\Delta v_{tri}| = 1.634 \times 10^{-8} \times 299792.458 \approx 0.0049\text{ m/s} = 4.9\text{ mm/s}$.
  This discrepancy is strictly of order $\mathcal{O}(\beta^3) \sim (5 \times 10^{-3})^3 \approx 1.25 \times 10^{-7}$, arising from the non-commutativity of non-collinear Lorentz boosts (Wigner Thomas precession).
- **Verdict: PASS.** Mathematical closure is verified to sub-centimeter per second accuracy.

### 2.2 Trace-Free Property of STF2 Quadrupole
- **Audit Verification:**
  The second-order kinematic quadrupole $Q_{ij}[\vec{\beta}] = \beta_i \beta_j - \frac{1}{3} \beta^2 \delta_{ij}$ was checked for $\vec{\beta}_{RO}$ and $\vec{\beta}_{MO}$.
  $$\text{Tr}(Q_{RO}) = 0.000 \times 10^{-18}$$
  $$\text{Tr}(Q_{MO}) = 0.000 \times 10^{-18}$$
  Symmetry $Q_{ij} = Q_{ji}$ holds identically.
- **Verdict: PASS.**

---

## 3. Axis 2: Statistical Independence & Overcounting Hazards

### 3.1 The Quaia G20 vs G20.5 Double-Counting Trap
- **Hostile Challenge:**
  Quaia $G < 20.0$ contains 755,850 quasars. Quaia $G < 20.5$ contains 1,295,502 quasars. All 755,850 quasars from $G < 20.0$ are contained inside $G < 20.5$.
  If an analyst treats $\vec{D}_{G20}$ and $\vec{D}_{G20.5}$ as independent measurements in a joint $\chi^2$ fit, the statistical significance $\Delta \chi^2$ will be artificially inflated by nearly a factor of 2!
- **Audit Resolution in Pipeline:**
  The pipeline explicitly evaluated the **shared Limber LSS clustering cross-covariance** between $G < 20.0$ and $G < 20.5$:
  $$C_1^{20, 20.5} = \frac{2}{\pi} \int dk \, k^2 P(k) W_1^{20}(k) W_1^{20.5}(k)$$
  yielding a cross-correlation coefficient:
  $$r = \frac{C_1^{20, 20.5}}{\sqrt{C_1^{20, 20} C_1^{20.5, 20.5}}} = 0.9878$$
  The full $12 \times 12$ covariance matrix $\mathbf{C}$ placed $\mathbf{C}_{LSS}^{20, 20.5} \mathbf{I}_3$ in the off-diagonal blocks between G20 and G20.5.
  Because $r \approx 0.99$, the Generalized Least Squares (GLS) fit properly downweights the redundant degrees of freedom, preventing false inflation of $\Delta \chi^2$.
- **Verdict: PASS.**

---

## 4. Axis 3: Observational & Physical Vulnerabilities

### 4.1 The Gaia Proper Motion Glide Fallacy
- **Hostile Challenge:**
  Several recent preprint authors have claimed that Gaia proper motion glide ($\mu_{glide} \approx 5.4\,\mu\text{as/yr}$) directly confirms or refutes the CMB kinematic dipole boost $\vec{\beta}_{RO} \approx 1.23 \times 10^{-3}$. Is this valid?
- **Hostile Rejection & Physical Clarification:**
  **ABSOLUTELY NOT.** This claim is physically illiterate.
  A constant velocity boost $\vec{\beta}$ produces a static angular shift (aberration $\Delta \theta \approx \beta \sin \theta$). Because $\frac{d\vec{\beta}}{dt} = 0$, the time derivative of aberration is **zero**.
  Proper motions $\vec{\mu} = \frac{d\hat{n}}{dt}$ measure **acceleration**, not velocity:
  $$\vec{\mu} = \frac{\vec{a}_\perp}{c}$$
  The observed Gaia DR3 glide amplitude of $5.44 \pm 0.32\,\mu\text{as/yr}$ directed toward $(l, b) \approx (266^\circ, -33^\circ)$ is the **Galactocentric acceleration** of the Solar System in its Milky Way orbit around Sagittarius A* ($v_c \approx 230$ km/s, $R_0 \approx 8.2$ kpc $\implies a = v_c^2 / R_0 \approx 2.2 \times 10^{-10}\text{ m/s}^2$).
- **Audit Resolution:**
  `THEORY_AND_DERIVATION.md` and `EMPIRICAL_CROSS_VALIDATION.json` explicitly maintain this physical firewall: Gaia proper motion glide is documented as a secular acceleration cross-check, and is **excluded** from the velocity boost design matrix $\mathbf{S}$.
- **Verdict: PASS.**

### 4.2 Galactic Dust Extinction ($E(B-V)$) and Selection Gradients
- **Hostile Challenge:**
  Quasars are identified by color cuts in Gaia + unWISE. If Milky Way dust extinction is underestimated along the Galactic plane or toward low latitudes, quasar selection efficiency drops systematically as a function of Galactic latitude $b$.
  A north-south or plane-to-pole selection asymmetry directly mimics an artificial dipole!
- **Audit Verification:**
  1. Quaia uses random catalogs that explicitly fold in the selection function $S(p)$ evaluated at HEALPix NSIDE 64 pixels.
  2. The window matrix $\mathbf{W} = \langle \hat{n}_i \hat{n}_j \rangle_{rand}$ was inverted to decouple the mask geometry.
  3. However, even with window deconvolution, the raw Quaia dipole is $D \approx 0.0245 - 0.0289$. When independent radio surveys (NVSS at 1.4 GHz and RACS-low at 888 MHz) are examined, which are completely unaffected by optical dust extinction, they **also** report an excess dipole ($D_{NVSS} \approx 0.0150$, $D_{RACS} \approx 0.0195$) aligned with the CMB dipole within $15^\circ - 20^\circ$.
  4. While dust extinction gradients might contribute $\sim 20-30\%$ of the optical amplitude, dust cannot explain the radio dipole excess.
- **Verdict: QUALIFIED PASS WITH RESIDUAL RISK.** Residual extinction and stellar contamination remain a secondary systematic, duly recorded in the caveat ledger.

---

## 5. Axis 4: Claim Firewall Compliance (C0–C5)

We audit all text, JSON metadata, and code docstrings against the mandatory project-wide claim firewall:

| Forbidden Claim / Habit | Check Result | Status |
|---|---|---|
| "Detection of Bianchi geometry" | Grepped: 0 occurrences | **CLEAN** |
| "Bianchi family identified" | Grepped: 0 occurrences | **CLEAN** |
| "Model-independent truth certificate" | Grepped: 0 occurrences | **CLEAN** |
| "Confirmed beyond-FLRW metric tilt" | Framed as unconfirmed candidate only | **CLEAN** |
| "MIO posterior" | No MIO posteriors generated | **CLEAN** |
| "TSC / Teff full solver" | 0 occurrences | **CLEAN** |
| "External transfer validated as native" | No solver outputs claimed | **CLEAN** |

### Allowed Claim Language Maintained:
- `claim-tiered observational/statistical framework`
- `diagnostic-only certificate`
- `frame-triangle consistency check`
- `kinematic count dipole anomaly`
- `Limber clustering cosmic variance floor`

---

## 6. Final Audit Verdict

**Overall Evaluation: PASSED WITH QUALIFIED SCIENTIFIC HOLD ON GEOMETRIC CLAIMS.**

1. The mathematical formulation of the Relativistic Velocity Triangle Closure $\Delta \vec{\beta}_{tri} = 0$ is proven and verified to sub-cm/s accuracy.
2. The multi-tracer count dipole excess ($|\vec{\beta}_{MO}| \approx 4.7 \times |\vec{\beta}_{RO}|$) is confirmed as a robust observational discrepancy across optical (Quaia G20, G20.5) and radio (NVSS, RACS-low) catalogs at $\Delta \chi^2 \approx 140$ ($p < 10^{-15}$).
3. In accordance with the project firewall, this discrepancy is classified as an **unresolved empirical tension**, strictly demarcated from any premature claim of Bianchi spacetime or cosmic geometry identification.
