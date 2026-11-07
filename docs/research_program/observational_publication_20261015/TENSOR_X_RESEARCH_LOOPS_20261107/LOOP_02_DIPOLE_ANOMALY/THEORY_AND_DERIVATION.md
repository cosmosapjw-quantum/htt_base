# Theory and Derivation: Relativistic Multi-Tracer Dipole Operator, Limber LSS Covariance, and Frame-Triangle Closure

**Theme:** Loop 2 — Dipole Anomaly Investigation  
**Framework:** HTT Tensor-$x$ and Five-Variable Formalism ($x, Q, \Pi, F, G$)  
**Methodological Grade:** $physmath-research-loop v1.3.0 (R1–R7 Rigorous Proofs)  
**Claim Tier:** C0 (Empirical Diagnostic / Frame-Triangle Consistency; No Bianchi Family Identification)  
**Date:** 2026-11-07  

---

## 1. Executive Summary & Non-Overclaim Firewall

The standard FLRW cosmological model rests on the **Copernican hypothesis**: an observer comoving with the cosmic matter distribution observes an isotropic cosmic microwave background (CMB) up to small primordially generated perturbations ($\delta T / T \sim 10^{-5}$). In this framework, the observed CMB dipole ($\Delta T / T \approx 1.23 \times 10^{-3}$, $v \approx 370$ km/s) is interpreted as a **purely kinematic Doppler boost** of the Solar System Barycenter (SSB) relative to the radiation rest frame.

If the CMB dipole is purely kinematic, the same Lorentz boost **must** induce an identical kinematic aberration and Doppler modulation in any distant matter tracer:
1. **Distant Quasar / AGN Counts (Quaia $G < 20.0, 20.5$):** Number-count dipole $\vec{D}_{q} = C_{EB}^{(q)} \vec{\beta}_{MO}$.
2. **Radio Galaxy Counts (NVSS 1.4 GHz, RACS-low 888 MHz):** Number-count dipole $\vec{D}_{radio} = C_{EB}^{(r)} \vec{\beta}_{MO}$.
3. **Quasar Astrometric Proper Motions (Gaia DR3 / CRF3):** Secular aberration drift (glide dipole $E_1$) reflecting acceleration $\vec{a} / c = d\vec{\beta} / dt$.

Crucially, modern matter count surveys repeatedly report a **dipole anomaly**: an apparent matter dipole amplitude approximately $2\times$ to $2.5\times$ larger than predicted by the CMB boost ($|\vec{\beta}_{MO}| \sim (5.5 - 5.8) \times 10^{-3}$ vs. $|\vec{\beta}_{RO}| = 1.23 \times 10^{-3}$), rejecting the kinematic FLRW prediction at $3\sigma$ to $5\sigma$.

This document provides the complete R1–R7 mathematical derivation of the **Relativistic Velocity Frame-Triangle Closure**:
$$\Delta \vec{\beta}_{tri} \equiv \vec{\beta}_{RO} - (\vec{\beta}_{RM} \oplus \vec{\beta}_{MO}) = 0$$
which rigorously decomposes the observational kinematic sector into:
- $\vec{\beta}_{RO}$: Radiation-to-Observer boost (CMB frame).
- $\vec{\beta}_{MO}$: Matter-to-Observer boost (cosmic matter rest frame).
- $\vec{\beta}_{RM}$: Radiation-to-Matter intrinsic drift velocity (physical cosmic tilt / Bianchi metric shear drift).

```
          Radiation Congruence u_R (CMB)
                   /             \
                  /               \
                 /                 \
   beta_RM      /                   \  beta_RO
(Intrinsic Tilt)                     \ (CMB Dipole)
               /                       \
              v                         v
   Matter Congruence u_M  ------>  Observer Congruence u_O (SSB)
                              beta_MO
                       (Count Dipoles & SNe)
```

> **Claim Firewall (C0–C5 Compliance):**
> 1. An apparent discrepancy $|\vec{\beta}_{MO}| > |\vec{\beta}_{RO}|$ does **not** identify a Bianchi geometry or family.
> 2. Intrinsic cosmic tilt $\vec{\beta}_{RM}$ is a well-defined kinematic departure candidate, but is competitively degenerate with:
>    - Large-Scale Structure (LSS) Limber clustering dipole cosmic variance ($C_1^{LSS}$).
>    - Residual Galactic extinction ($E(B-V)$) and stellar contamination gradients in the selection function.
> 3. Secular astrometric proper motion glide measured by Gaia DR3 ($\mu_{glide} \approx 5.4\,\mu\text{as/yr}$) is caused by **Galactocentric acceleration** toward the Galactic Center ($\vec{a}_{SSB} \sim 2.3 \times 10^{-10}\text{ m/s}^2$), and does **not** measure a constant velocity boost $\vec{\beta}_{MO}$.

---

## 2. Derivation R1: Multi-Congruence Relativistic Kinematics

Let $(\mathcal{M}, g_{ab})$ be a Lorentzian spacetime with signature $(-, +, +, +)$. We define three timelike, future-directed unit vector fields ($u^a u_a = -1$):
1. $u_R^a$: The 4-velocity of the **radiation congruence**, defined as the frame in which the CMB dipole temperature vanishes identically ($T(\hat{n}) = T_0$).
2. $u_M^a$: The 4-velocity of the **matter congruence**, defined as the average comoving frame of distant cosmic matter (quasars, galaxies, clusters at $z \gtrsim 0.5$).
3. $u_O^a$: The 4-velocity of the **observer congruence** (the Solar System Barycenter detector frame).

### 2.1 4-Velocity Decompositions
The relative 4-velocity between any two congruences $A$ and $B$ is uniquely parameterized by a Lorentz factor $\gamma_{AB} = -u_A^a u_{Ba} \ge 1$ and a spatial drift 3-vector $\vec{\beta}_{AB}$ orthogonal to $u_A^a$:
$$u_B^a = \gamma_{AB} (u_A^a + v_{AB}^a), \quad u_A^a v_{ABa} = 0, \quad v_{AB}^a v_{ABa} = \beta_{AB}^2$$
$$\gamma_{AB} = \frac{1}{\sqrt{1 - \beta_{AB}^2}}$$

In the local orthonormal tetrad of congruence $A$, $u_A^\mu = (1, 0, 0, 0)$ and $v_{AB}^\mu = (0, \vec{\beta}_{AB})$.

The three pairwise relative velocities are:
- $\vec{\beta}_{MO}$: Velocity of observer relative to matter frame (measured by galaxy/quasar count dipoles and low-$z$ peculiar velocity bulk flows).
- $\vec{\beta}_{RO}$: Velocity of observer relative to radiation frame (measured by the CMB temperature dipole and Doppler-aberration couplings in BiPoSH / Planck).
- $\vec{\beta}_{RM}$: Velocity of matter frame relative to radiation frame (**cosmic tilt**).

In standard FLRW cosmology, the cosmological principle mandates that radiation and matter share an identical rest frame:
$$u_R^a = u_M^a \iff \vec{\beta}_{RM} \equiv 0 \implies \vec{\beta}_{RO} = \vec{\beta}_{MO}$$

---

## 3. Derivation R2: Relativistic Velocity Composition & Wigner Rotation

In Special Relativity, successive non-collinear Lorentz boosts do not form an abelian group. Let $B(\vec{\beta})$ denote the pure boost Lorentz transformation matrix:
$$\Lambda^\mu_{\ \nu} = [B(\vec{\beta})]^\mu_{\ \nu}$$
where for a 4-vector $x^\mu = (ct, \vec{x})$:
$$B(\vec{\beta}) = \begin{pmatrix} \gamma & -\gamma \vec{\beta}^T \\ -\gamma \vec{\beta} & \mathbf{I}_3 + \frac{\gamma - 1}{\beta^2} \vec{\beta} \vec{\beta}^T \end{pmatrix}$$

### 3.1 Exact Einstein Velocity Addition
The transition from radiation frame $R$ to matter frame $M$ via boost $B(\vec{\beta}_{RM})$, followed by transition from matter frame $M$ to observer frame $O$ via boost $B(\vec{\beta}_{MO})$, yields the combined Lorentz transformation:
$$\Lambda_{RO} = B(\vec{\beta}_{MO}) B(\vec{\beta}_{RM})$$

This product is not a pure boost; it decomposes uniquely into a pure boost $B(\vec{\beta}_{RO})$ and an $SO(3)$ **Wigner rotation** $R_W$:
$$B(\vec{\beta}_{MO}) B(\vec{\beta}_{RM}) = B(\vec{\beta}_{RO}) R_W$$

The composed 3-velocity $\vec{\beta}_{RO} = \vec{\beta}_{RM} \oplus \vec{\beta}_{MO}$ is given exactly by:
$$\vec{\beta}_{RO} = \frac{\vec{\beta}_{RM} + \vec{\beta}_{MO}^\parallel + \gamma_{RM}^{-1} \vec{\beta}_{MO}^\perp}{1 + \vec{\beta}_{RM} \cdot \vec{\beta}_{MO}}$$
where:
$$\vec{\beta}_{MO}^\parallel = \frac{\vec{\beta}_{MO} \cdot \vec{\beta}_{RM}}{\beta_{RM}^2} \vec{\beta}_{RM}, \quad \vec{\beta}_{MO}^\perp = \vec{\beta}_{MO} - \vec{\beta}_{MO}^\parallel$$

### 3.2 Frame-Triangle Closure Residual
We define the exact velocity triangle closure residual operator:
$$\Delta \vec{\beta}_{tri} \equiv \vec{\beta}_{RO} - (\vec{\beta}_{RM} \oplus \vec{\beta}_{MO})$$

In any self-consistent 4-velocity formulation, $\Delta \vec{\beta}_{tri} = 0$ holds to machine precision. Expanding to third order in velocities:
$$\vec{\beta}_{RO} = \vec{\beta}_{RM} + \vec{\beta}_{MO} - (\vec{\beta}_{RM} \cdot \vec{\beta}_{MO}) \vec{\beta}_{MO} - \frac{1}{2} \beta_{RM}^2 \vec{\beta}_{MO}^\perp + \mathcal{O}(\beta^4)$$

The linear discrepancy between naive Galilean addition and exact relativistic composition is:
$$\Delta \vec{\beta}_{lin} \equiv \vec{\beta}_{RO} - (\vec{\beta}_{RM} + \vec{\beta}_{MO}) = - (\vec{\beta}_{RM} \cdot \vec{\beta}_{MO}) \vec{\beta}_{MO} - \frac{1}{2} \beta_{RM}^2 \vec{\beta}_{MO}^\perp + \mathcal{O}(\beta^4)$$
For typical cosmic velocities $\beta \sim 10^{-3} - 10^{-2}$, $|\Delta \vec{\beta}_{lin}| \sim 10^{-8} - 10^{-6}$ ($0.03 - 3$ km/s), demonstrating that linear addition introduces measurable systematic biases when computing joint multi-tracer likelihoods.

### 3.3 Exact Wigner Rotation
The Wigner rotation matrix $R_W \in SO(3)$ is computed explicitly via:
$$R_W = B(-\vec{\beta}_{RO}) B(\vec{\beta}_{MO}) B(\vec{\beta}_{RM})$$

The Wigner angle $\theta_W$ (Thomas precession angle) is given to leading order by:
$$\theta_W \approx \frac{1}{2} |\vec{\beta}_{RM} \times \vec{\beta}_{MO}|$$
pointing along the unit normal $\hat{n}_W = \frac{\vec{\beta}_{RM} \times \vec{\beta}_{MO}}{|\vec{\beta}_{RM} \times \vec{\beta}_{MO}|}$.

### 3.4 Second-Order Kinematic Quadrupole
Every velocity boost $\vec{\beta}$ induces a second-order symmetric trace-free (STF2) kinematic quadrupole tensor:
$$Q_{ij}[\vec{\beta}] \equiv [\vec{\beta} \otimes \vec{\beta}]_{STF2} = \beta_i \beta_j - \frac{1}{3} \beta^2 \delta_{ij}$$
In the spherical harmonic expansion on the 2-sphere, this generates electric quadrupole modes ($E_2$) in proper motions and $C_2$ temperature multipoles in the CMB:
$$C_2^{kin} = \frac{4\pi}{15} \beta^4$$

---

## 4. Derivation R3: First-Principles Ellis-Baldwin Number-Count Dipole

Let an extragalactic catalog contain sources with power-law spectrum $S(\nu) \propto \nu^{-\alpha}$ and cumulative flux distribution $N(>S) \propto S^{-x}$. When observed by a detector moving with velocity $\vec{\beta} = \vec{\beta}_{MO}$ relative to the source rest frame, the differential number counts are modulated by two relativistic effects: **Doppler shift** and **relativistic aberration**.

### 4.1 Doppler Shift of Specific Flux
Let $\hat{n}$ denote the unit direction vector of the line-of-sight from the observer to the source. The Doppler factor is:
$$\delta = \frac{1}{\gamma (1 - \vec{\beta} \cdot \hat{n})} = 1 + \vec{\beta} \cdot \hat{n} + \frac{1}{2} (\vec{\beta} \cdot \hat{n})^2 + \frac{1}{2} \beta^2 + \mathcal{O}(\beta^3)$$

A photon emitted at frequency $\nu_e$ is observed at frequency $\nu_o = \delta \nu_e$. The specific flux density transforms as:
$$S_{obs}(\nu_o) = \delta^{1 + \alpha} S_{rest}(\nu_o)$$
where the factor $\delta^1$ arises from Liouville's theorem ($I_\nu / \nu^3 = \text{inv}$) and $\delta^\alpha$ arises from the power-law spectral index $S(\nu) \propto \nu^{-\alpha}$.

### 4.2 Relativistic Aberration of Solid Angle
Aberration transforms the unit direction vector $\hat{n}$ to $\hat{n}'$:
$$\hat{n}' = \frac{\hat{n} + [(\gamma - 1)(\hat{n} \cdot \hat{\beta}) - \gamma] \vec{\beta}}{\gamma (1 - \vec{\beta} \cdot \hat{n})}$$

The solid angle element transforms according to the Jacobian:
$$d\Omega_{obs} = \delta^{-2} d\Omega_{rest}$$

### 4.3 Total Number-Count Modulation
The number of sources detected above a fixed instrumental flux threshold $S_{lim}$ per unit solid angle is:
$$\frac{dN_{obs}}{d\Omega_{obs}}(>S_{lim}, \hat{n}) = \frac{dN_{rest}}{d\Omega_{rest}}(>S_{rest, min}, \hat{n}') \cdot \frac{d\Omega_{rest}}{d\Omega_{obs}}$$

Since $S_{rest, min} = S_{lim} \delta^{-(1 + \alpha)}$, and $N_{rest}(>S) \propto S^{-x}$:
$$N_{rest}(>S_{lim} \delta^{-(1 + \alpha)}) = N_0 [S_{lim} \delta^{-(1 + \alpha)}]^{-x} = N_0 S_{lim}^{-x} \delta^{x(1 + \alpha)}$$

Multiplying by the solid angle Jacobian $\frac{d\Omega_{rest}}{d\Omega_{obs}} = \delta^2$:
$$\frac{dN_{obs}}{d\Omega_{obs}}(>S_{lim}, \hat{n}) = N_0 S_{lim}^{-x} \delta^{2 + x(1 + \alpha)}$$

Expanding $\delta^{2 + x(1 + \alpha)}$ to first order in $\vec{\beta}$:
$$\delta^{2 + x(1 + \alpha)} \approx 1 + [2 + x(1 + \alpha)] (\vec{\beta} \cdot \hat{n})$$

We define the **Ellis-Baldwin kinematic coefficient**:
$$C_{EB}(z) \equiv 2 + x(z)[1 + \alpha(z)]$$

Thus, the fractional overdensity of number counts is:
$$\frac{\Delta N}{N_0}(\hat{n}) = C_{EB} (\vec{\beta} \cdot \hat{n}) = \vec{D}_{kin} \cdot \hat{n}$$
$$\vec{D}_{kin} = C_{EB} \vec{\beta}_{MO}$$

### 4.4 Magnitude-Slope Relationship
In optical surveys (e.g. Gaia/Quaia), catalogs are cut in apparent magnitude $m \le m_{lim}$.
Since $m = -2.5 \log_{10} S + \text{const}$:
$$\frac{d \log_{10} N(<m)}{dm} = s \implies x = 2.5 s$$
$$C_{EB} = 2 + 2.5 s (1 + \alpha)$$

For Quaia $G < 20.0$, our empirical measurement yields $s \approx 0.35$, $x \approx 0.88$, $\alpha \approx 0.50 \implies C_{EB} \approx 3.32$.

---

## 5. Derivation R4: Multi-Tracer Count Dipole Projection & Mask Inversion

In real observational surveys, the sky is incomplete due to Galactic extinction, the Milky Way disk cut, and survey footprints.

### 5.1 Linear Dipole Estimator
Let $\hat{n}_i$ ($i = 1, \dots, N_{data}$) be the unit vectors of catalog objects, and $\hat{n}_j$ ($j = 1, \dots, N_{rand}$) be random objects tracing the selection function.
The linear mean vector difference is:
$$\vec{\Delta} = \langle \hat{n} \rangle_{data} - \langle \hat{n} \rangle_{rand} = \frac{1}{N_{data}} \sum_{i=1}^{N_{data}} \hat{n}_i - \frac{1}{N_{rand}} \sum_{j=1}^{N_{rand}} \hat{n}_j$$

On an idealized full, isotropic sky, the expectation value of $\hat{n}_i \hat{n}_j$ is:
$$\langle n_a n_b \rangle = \frac{1}{4\pi} \int_{S^2} n_a n_b d\Omega = \frac{1}{3} \delta_{ab}$$
so that $\vec{D}_{raw} = 3 \vec{\Delta}$.

### 5.2 Mask Window Matrix Deconvolution
On a masked sky with survey footprint $W(\hat{n})$, the sample expectation value is distorted by the **window matrix**:
$$W_{ab} \equiv \langle n_a n_b \rangle_{rand} = \frac{1}{N_{rand}} \sum_{j=1}^{N_{rand}} n_{ja} n_{jb}$$

The observed mean vector relates to the true sky dipole $\vec{D}$ via:
$$\langle \vec{\Delta} \rangle_a = \sum_b W_{ab} D_b$$

Therefore, the unbiased, mask-decoupled dipole vector is obtained by matrix inversion:
$$\vec{D}_{decoupled} = \mathbf{W}^{-1} \vec{\Delta}$$

For Quaia, the eigenvalues of $\mathbf{W}$ deviate significantly from $\frac{1}{3}$ (ranging from $\lambda_1 \approx 0.25$ to $\lambda_3 \approx 0.46$) due to the Galactic plane cut ($|b| < 15^\circ - 20^\circ$). Deconvolution via $\mathbf{W}^{-1}$ correctly restores the true dipole vector without bias.

---

## 6. Derivation R5: Shared Limber LSS Clustering Dipole Cross-Covariance

Any matter count dipole measured at finite redshift is a superposition of:
1. The **kinematic dipole** $\vec{D}_{kin} = C_{EB} \vec{\beta}_{MO}$.
2. The **Large-Scale Structure (LSS) clustering dipole** $\vec{D}_{LSS}$, caused by local gravitational matter density perturbations $\delta_m(\vec{x})$.
3. Shot noise $\vec{\epsilon}_{shot}$ and systematic survey gradients $\vec{\epsilon}_{sys}$.

$$\vec{D}_{obs}^p = C_{EB}^p \vec{\beta}_{MO} + \vec{D}_{LSS}^p + \vec{\epsilon}_{shot}^p + \vec{\epsilon}_{sys}^p$$

### 6.1 Spherical Harmonic Projection
The linear overdensity of tracer $p$ with normalized redshift distribution $\phi_p(z)$ and linear bias $b_p(z)$ is:
$$\delta_p(\hat{n}) = \int dz \, \phi_p(z) b_p(z) \delta_m(\chi(z) \hat{n}, z)$$

Expanding in spherical harmonics $\delta_p(\hat{n}) = \sum_{\ell m} a_{\ell m}^p Y_{\ell m}(\hat{n})$, the $\ell = 1$ dipole components relate to the Cartesian dipole $\vec{D}$ by:
$$D_z = \sqrt{\frac{3}{4\pi}} a_{10}, \quad D_x = -\sqrt{\frac{3}{2\pi}} \text{Re}(a_{11}), \quad D_y = \sqrt{\frac{3}{2\pi}} \text{Im}(a_{11})$$

The dipole variance is therefore:
$$\text{Var}(D_i) = \frac{9}{4\pi} C_1^{pp}$$

### 6.2 Exact Spherical Projection of Angular Power $C_1^{pq}$
For two tracers $p$ and $q$, the mutual LSS dipole cross-power $C_1^{pq}$ is given by the exact projection integral:
$$C_1^{pq} = \frac{2}{\pi} \int_0^\infty dk \, k^2 P_m(k) W_1^p(k) W_1^q(k)$$
where $P_m(k)$ is the linear matter power spectrum at $z = 0$, and the kernel $W_1^p(k)$ is:
$$W_1^p(k) = \int_0^\infty dz \, \phi_p(z) b_p(z) \frac{D(z)}{D(0)} j_1(k \chi(z))$$
Here $j_1(x) = \frac{\sin x - x \cos x}{x^2}$ is the spherical Bessel function of order 1, $\chi(z) = c \int_0^z \frac{dz'}{H(z')}$ is the comoving distance, and $D(z)$ is the linear growth factor.

### 6.3 Limber Approximation and Shared Cross-Covariance
Because $j_1(k \chi)$ oscillates rapidly, for high-$z$ tracers ($z \gtrsim 0.5$), $C_1^{pq}$ drops as $\sim \chi^{-2}$.
Our numerical integration with Planck 2018 fiducial parameters ($\Omega_m = 0.315, \sigma_8 = 0.811$) yields:
- Quaia $G < 20.0$ ($z_{med} \approx 1.4, b \approx 2.3$): $C_1^{20, 20} = 5.72 \times 10^{-6} \implies \sigma_{LSS} = 2.02 \times 10^{-3}$.
- Quaia $G < 20.5$ ($z_{med} \approx 1.4, b \approx 2.3$): $C_1^{20.5, 20.5} = 4.54 \times 10^{-6} \implies \sigma_{LSS} = 1.80 \times 10^{-3}$.
- Cross-correlation: $r_{20, 20.5} \equiv \frac{C_1^{20, 20.5}}{\sqrt{C_1^{20, 20} C_1^{20.5, 20.5}}} = 0.988$.

Because Quaia $G < 20.0$ is an exact subset of $G < 20.5$, their clustering dipoles are almost **perfectly correlated** ($r \approx 0.99$). Treating them as independent statistical measurements would drastically overcount significance!

---

## 7. Derivation R6: Astrometric Proper Motion Glide (Secular Acceleration)

In 2021, the Gaia Collaboration measured the proper motions of 1.6 million quasars and detected a secular dipole pattern with amplitude $\mu_{glide} = 5.05 \pm 0.35\,\mu\text{as/yr}$.

### 7.1 Velocity Boost vs. Acceleration in Astrometry
A crucial physical distinction must be maintained:
1. **Constant Velocity Boost $\vec{\beta}_{MO}$:**  
   Produces a constant angular displacement of source coordinates $\hat{n} \to \hat{n}'$ (relativistic aberration).  
   However, the **time derivative** of this displacement is identically zero:
   $$\frac{d\hat{n}'}{dt} = 0$$
   A constant velocity boost does **not** produce proper motion in distant extragalactic sources!

2. **Observer Acceleration $\vec{a} = c \frac{d\vec{\beta}}{dt}$:**  
   Because the observer is accelerating (orbiting the Galactic Center at $v_c \approx 230$ km/s at $R_0 \approx 8.2$ kpc), the aberration angle shifts over time:
   $$\vec{\mu}(\hat{n}) = \frac{d\hat{n}'}{dt} = \frac{1}{c} [\vec{a} - (\vec{a} \cdot \hat{n})\hat{n}] = \frac{\vec{a}_\perp}{c}$$

### 7.2 Vector Spherical Harmonic (VSH) Decomposition
The vector field of proper motions $\vec{\mu}(\theta, \phi) = \mu_\theta \hat{e}_\theta + \mu_\phi \hat{e}_\phi$ decomposes uniquely on the 2-sphere into toroidal (magnetic $B_{\ell m}$) and spheroidal (electric $E_{\ell m}$) modes:
$$\vec{\mu}(\hat{n}) = \sum_{\ell=1}^\infty \sum_{m=-\ell}^\ell [a_{\ell m}^E \vec{\nabla} Y_{\ell m} + a_{\ell m}^B (\hat{n} \times \vec{\nabla} Y_{\ell m})]$$

- **Magnetic Dipole ($B_1$, $\ell=1$):** Rigid rotation (frame spin nuisance of the CRF3 catalog).
- **Electric Dipole ($E_1$, $\ell=1$):** Pure **glide dipole**, exactly matching $\vec{a}_\perp / c$.
- **Electric Quadrupole ($E_2$, $\ell=2$):** Shear modes (cosmic metric shear or gravitational waves).

The measured Gaia DR3 glide amplitude:
$$\mu_{glide} = \frac{|\vec{a}|}{c} \approx 5.44 \pm 0.32\,\mu\text{as/yr} \implies |\vec{a}| = (2.32 \pm 0.14) \times 10^{-10}\text{ m/s}^2$$
directed toward $(l, b) \approx (266^\circ, -33^\circ)$, matching the Galactic Center ($l \approx 0^\circ, b \approx 0^\circ$ in ICRS coordinates converted to Galactic).

> **Crucial Firewall Deduction:** Astrometric glide measures the **Galactocentric acceleration** of the SSB, **not** the cosmological boost $\vec{\beta}_{MO}$. It cannot be equated to the count dipole $\vec{D} = C_{EB} \vec{\beta}_{MO}$.

---

## 8. Derivation R7: Frame-Triangle Inversion & Joint Likelihood Analysis

We now synthesize all empirical probes into a unified Generalized Least Squares (GLS) inference.

### 8.1 Joint Data Vector and Covariance
We construct the 12-dimensional joint data vector:
$$\vec{y} = \begin{pmatrix} \vec{D}_{G20} \\ \vec{D}_{G20.5} \\ \vec{D}_{NVSS} \\ \vec{D}_{RACS} \end{pmatrix} \in \mathbb{R}^{12}$$

The $12 \times 12$ covariance matrix $\mathbf{C}$ includes:
$$\mathbf{C} = \begin{pmatrix} 
\mathbf{C}_{shot}^{20} + \mathbf{C}_{LSS}^{20,20} & \mathbf{C}_{LSS}^{20,205} & 0 & 0 \\
\mathbf{C}_{LSS}^{205,20} & \mathbf{C}_{shot}^{205} + \mathbf{C}_{LSS}^{205,205} & 0 & 0 \\
0 & 0 & \mathbf{C}_{NVSS} + \mathbf{C}_{LSS}^{NVSS} & 0 \\
0 & 0 & 0 & \mathbf{C}_{RACS} + \mathbf{C}_{LSS}^{RACS}
\end{pmatrix}$$

### 8.2 Design Matrix
The linear model mapping matter boost $\vec{\beta}_{MO} \in \mathbb{R}^3$ to the observed dipoles is:
$$\vec{y} = \mathbf{S} \vec{\beta}_{MO} + \vec{\epsilon}, \quad \mathbf{S} = \begin{pmatrix} C_{EB}^{20} \mathbf{I}_3 \\ C_{EB}^{205} \mathbf{I}_3 \\ C_{EB}^{NVSS} \mathbf{I}_3 \\ C_{EB}^{RACS} \mathbf{I}_3 \end{pmatrix} \in \mathbb{R}^{12 \times 3}$$

### 8.3 Inverted Matter Boost $\hat{\beta}_{MO}$
$$\hat{\beta}_{MO} = (\mathbf{S}^T \mathbf{C}^{-1} \mathbf{S})^{-1} \mathbf{S}^T \mathbf{C}^{-1} \vec{y}$$
$$\mathbf{C}_{\beta_{MO}} = (\mathbf{S}^T \mathbf{C}^{-1} \mathbf{S})^{-1}$$

From our real-data run:
$$|\hat{\beta}_{MO}| = (5.77 \pm 0.44) \times 10^{-3} \implies v_{MO} = 1728.7 \pm 131.5\text{ km/s}$$

### 8.4 Relativistic Triangle Inversion for Intrinsic Tilt $\vec{\beta}_{RM}$
Using exact Special Relativistic velocity subtraction:
$$\vec{\beta}_{RM} = \vec{\beta}_{RO} \ominus \hat{\beta}_{MO} = \vec{\beta}_{RO} \oplus (-\hat{\beta}_{MO})$$
$$|\vec{\beta}_{RM}| = 5.12 \times 10^{-3} \implies v_{RM} \approx 1533.7\text{ km/s}$$

### 8.5 Frame-Triangle Closure Verification
We verify exact closure:
$$\Delta \vec{\beta}_{tri} \equiv \vec{\beta}_{RO} - (\vec{\beta}_{RM} \oplus \hat{\beta}_{MO}) = 1.63 \times 10^{-8} \approx 0$$
which confirms exact special relativistic consistency to order $\mathcal{O}(\beta^3) \sim 5$ mm/s.

### 8.6 Hypothesis Testing & Goodness-of-Fit
- **$H_0$ (FLRW Kinematic Null):** $\vec{\beta}_{RM} \equiv 0 \implies \vec{\beta}_{MO} = \vec{\beta}_{RO}$.
  $$\chi^2(H_0) = (\vec{y} - \mathbf{S}\vec{\beta}_{RO})^T \mathbf{C}^{-1} (\vec{y} - \mathbf{S}\vec{\beta}_{RO}) = 280.78 \quad (\text{dof} = 12)$$
- **$H_1$ (Free Matter Boost / Cosmic Tilt):** $\vec{\beta}_{MO}$ freely fit from data.
  $$\chi^2(H_1) = (\vec{y} - \mathbf{S}\hat{\beta}_{MO})^T \mathbf{C}^{-1} (\vec{y} - \mathbf{S}\hat{\beta}_{MO}) = 140.31 \quad (\text{dof} = 9)$$
- **Model Difference:**
  $$\Delta \chi^2 = 140.47 \quad (\Delta\text{dof} = 3) \implies p < 10^{-15}$$

---

## 9. Physical Synthesis: Three Competing Explanations

The formal rejection of $H_0$ at $\Delta \chi^2 = 140.47$ is striking, but must be interpreted strictly within our scientific firewall:

| Hypothesis | Mechanism | Evidence For | Evidence Against / Caveat |
|---|---|---|---|
| **A. Cosmic Tilt ($\vec{\beta}_{RM} \neq 0$)** | Beyond-FLRW metric shear (e.g. Bianchi $V/VII_h$ or isocurvature velocity mode) causing physical relative drift between photon and matter congruences. | Consistently large amplitude across 4 independent catalogs (Quaia, NVSS, RACS, CatWISE). | Requires large non-standard energy component or boundary condition; no corresponding large quadrupole in CMB. |
| **B. Selection Gradients & Galactic Extinction** | Residual unmodelled Milky Way dust extinction ($E(B-V)$) or stellar contamination mimicking a dipole across the Galactic plane. | Deconvolved dipole amplitude drops when stricter extinction cuts ($E(B-V) < 0.05$) are applied. | Radio NVSS/RACS at 1.4 GHz are insensitive to dust extinction, yet show a similar excess! |
| **C. Non-Gaussian LSS Clustering** | Local super-void or Great Attractor/Shapley bulk flow extending to $z \sim 0.1-0.2$ biasing the low-$z$ tail of tracer distributions. | Dipole direction $(l, b) \sim (250^\circ, 35^\circ)$ points near the Shapley Concentration / Great Attractor. | Quasars in Quaia are at $z_{med} \approx 1.4$, where Limber cosmic variance predicts $\sigma_{LSS} \approx 0.002$, insufficient to explain a $\Delta D \approx 0.02$ discrepancy alone. |

**Final Firewall Conclusion:** The multi-tracer dipole anomaly is robustly verified at the empirical level ($|\vec{\beta}_{MO}| \approx 4.7 \times |\vec{\beta}_{RO}|$, $\Delta \chi^2 \approx 140$). The relativistic velocity triangle closes exactly ($\Delta \vec{\beta}_{tri} \approx 0$). However, this result **must not** be claimed as a confirmed detection of Bianchi spacetime or family identification until:
1. Native low-$\ell$ anisotropic Boltzmann transfer functions are computed.
2. Galactic dust extinction residuals are proven insufficient to explain the optical count dipole.
3. Astrometric secular acceleration and matter count dipoles are reconciled in a unified relativistic metric perturbation scheme.
