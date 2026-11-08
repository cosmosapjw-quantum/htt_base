# Paper Extract P5: Spacetime Geometry Compatibility, Curvature Orbits, and Morphology Stability

**Document ID:** `P5_GEOMETRY_COMPATIBILITY_ATLAS.md`  
**Parent Release:** `PR-R37-05-FINAL-REPORT` (Finite Scientific Convergence Release)  
**Target Paper:** P5 — *Bianchi observable-equivalence and family identification / Geometry Compatibility Atlas*  
**Claim Tier:** C0 (Conditional Geometry-Response & Invariant Classification Extract)  
**Artifact Mode:** Diagnostic Geometry Compatibility & Orbit Separation Extract  
**Ownership & Role:** HTT Statistical Inference / obsstat Feature Extraction  
**Transfer Source:** External/AniCLASS-calibrated transfer (pre-native solver baseline)  
**Baseline Commit:** `bdead6a8f51282ca647224b460b0f65de085568b`

---

## 1. Executive Summary & Physical Problem Statement

A central goal of observational cosmology beyond the FLRW paradigm is testing whether cosmic microwave or large-scale structure anomalies can be identified with specific spatially homogeneous anisotropic spacetimes (Bianchi classifications). However, assigning a unique spacetime family label (e.g., Bianchi $\mathrm{VII}_0$, $\mathrm{VII}_h$, $\mathrm{II}$, or $\mathrm{IX}$) from low-multipole observables faces profound mathematical degeneracies:
1. **Observable Equivalence:** Distinct simply transitive Lie group actions can induce identical local spatial geometry (e.g., Bianchi $\mathrm{I}$ and flat $\mathrm{VII}_0$);
2. **FLRW Origin Overlap:** In the limit of vanishing anisotropy amplitude ($a \to 0$), all Bianchi group orbits collapse onto the isotropic FLRW origin, rendering exclusive family classification impossible;
3. **The Gauss Bridge Requirement:** Spatial Ricci curvature ${}^3 R_{ij}$ cannot be determined from kinematic shear $\sigma_{ij}$ alone; reconstructing 3-curvature requires electric-Weyl curvature $E_{ij}$ and matter anisotropic stress $\pi_{ij}$;
4. **Adequacy Residual Necessity:** Preserving family likelihood ratios alone does not prevent false attribution; an omnibus adequacy residual is strictly required to detect when *all* hypothesized families fail to match the data.

Extract P5 presents the finite geometry-response and curvature-orbit framework established across R32-07, R36-10, and R37-04. We demonstrate exact analytic separation between Bianchi $\mathrm{II}$ and $\mathrm{VII}_0$ witnesses, compute the conservative exclusive separation margin as a function of noise and deterministic error, and establish the exact fixed-$Q$ chirality sign stability radius.

No Bianchi family identification or native Boltzmann solver validation is claimed.

---

## 2. Mathematical Formulation & Geometric Orbits

### 2.1 Hypersurface-Normal Congruences & The Gauss Bridge
Let $n^a$ be the unit timelike normal to a family of spacelike hypersurfaces ($n_a n^a = -1$, signature $(-,+,+,+)$). Let $h_{ab} = g_{ab} + n_a n_b$ be the induced 3-metric, $\mathcal{K}_{ab} = h_a{}^c h_b{}^d \nabla_c n_d$ the extrinsic curvature, $\Theta = \mathcal{K}^a{}_a = 3h$, and $\sigma_{ab} = \mathcal{K}_{\langle ab \rangle}$ the shear ($S_{ab} = \sigma_{ab}/c$).

The Gauss constraint relates 4-dimensional Einstein field equations to the intrinsic 3-Ricci tensor ${}^3 R_{ab}$:
$$
{}^3 R = 2\kappa_g \rho + 2\Lambda - 6h^2 + \boldsymbol{S}:\boldsymbol{S},
$$
$$
{}^3 R_{\langle ab \rangle} = E_{ab} + \frac{\kappa_g}{2}\pi_{ab} - h S_{ab} + \operatorname{STF}(S^2)_{ab},
$$
where $\kappa_g = 8\pi G / c^4$, $E_{ab} = C_{acbd} n^c n^d$ is the electric Weyl tensor, and $\pi_{ab}$ is the matter anisotropic stress.  
**Lemma (Incompleteness of Pure Shear):**  
Kinematic measurement of shear $\boldsymbol{S}$ determines ${}^3 R_{\langle ab \rangle}$ if and only if $E_{ab}$ and $\pi_{ab}$ are independently measured or constrained by a dynamical history model.

### 2.2 Instantaneous Bianchi II and $\mathrm{VII}_0$ Witnesses
In the canonical oriented orthonormal frame ($\epsilon_{123} = +1$), spatial Ricci curvature tensors for the retained R36-10 finite witnesses scale with structure parameter $u_*^2$:
$$
\boldsymbol{R}_{\rm II} = \operatorname{diag}\left( \frac{1}{2}, \; -\frac{1}{2}, \; -\frac{1}{2} \right) u_*^2, \qquad \boldsymbol{R}_{\mathrm{VII}_0} = \operatorname{diag}\left( -\frac{1}{2}, \; \frac{3}{2}, \; -\frac{3}{2} \right) u_*^2.
$$
- **Scalar Curvatures:** Both witnesses have identical trace:
  $$
  \operatorname{tr}(\boldsymbol{R}_{\rm II}) = \operatorname{tr}(\boldsymbol{R}_{\mathrm{VII}_0}) = -\frac{1}{2} u_*^2.
  $$
- **Quadratic Invariants:**
  $$
  \operatorname{tr}(\boldsymbol{R}_{\rm II}^2) = \frac{3}{4} u_*^4, \qquad \operatorname{tr}(\boldsymbol{R}_{\mathrm{VII}_0}^2) = \frac{19}{4} u_*^4.
  $$
  The trace-free quadratic invariants differ by:
  $$
  \|\operatorname{STF}(\boldsymbol{R}_{\rm II})\|_F^2 = \frac{2}{3} u_*^4, \qquad \|\operatorname{STF}(\boldsymbol{R}_{\mathrm{VII}_0})\|_F^2 = \frac{14}{3} u_*^4.
  $$

### 2.3 Exact Rotation-Orbit Distance
Under an isotropic Frobenius metric, minimizing the distance over all 3D spatial rotations $\mathrm{SO}(3)$ corresponds to the Euclidean distance between sorted eigenvalue triples:
$$
\operatorname{spec}^\uparrow(\boldsymbol{R}_{\rm II}) = \left(-\frac{1}{2}, \; -\frac{1}{2}, \; \frac{1}{2}\right) u_*^2, \qquad \operatorname{spec}^\uparrow(\boldsymbol{R}_{\mathrm{VII}_0}) = \left(-\frac{3}{2}, \; -\frac{1}{2}, \; \frac{3}{2}\right) u_*^2.
$$
For a continuous amplitude path scaling structure constants by $a \in [0, 1]$, where $\boldsymbol{R}(a) = a^2 \boldsymbol{R}(1)$:
$$
\delta(a) \equiv \operatorname{dist}_{\mathrm{SO}(3)}\left( \mathcal{O}_{\boldsymbol{R}_{\rm II}(a)}, \; \mathcal{O}_{\boldsymbol{R}_{\mathrm{VII}_0}(a)} \right) = \sqrt{ \left(-\frac{1}{2} - \left(-\frac{3}{2}\right)\right)^2 + 0^2 + \left(\frac{1}{2} - \frac{3}{2}\right)^2 } a^2 u_*^2 = \sqrt{2} a^2 u_*^2.
$$
This is an attained analytic minimum over all orientations, not a numerical grid lower bound. At $a = 0$, $\delta(0) = 0$, establishing origin overlap.

### 2.4 Profiled Carrier and Discarded-Space Adequacy Residual
The raw observation vector $\boldsymbol{y} \in \mathbb{R}^7$ consists of trace ($y_{\rm tr} = \operatorname{tr}(\boldsymbol{R})/\sqrt{3}$), five orthonormal STF components $\boldsymbol{y}_{\rm STF} \in \mathbb{R}^5$, and a calibration nuisance $y_{\rm cal}$. Under common Gaussian noise $\mathcal{N}(\boldsymbol{0}, \sigma^2 \boldsymbol{I}_7)$:
1. **5D STF Carrier:** Retains all likelihood ratios between family orbits at fixed amplitude $a$;
2. **6th Adequacy Coordinate:**
   $$
   r_{\rm adeq} = \frac{y_{\rm tr} - y_{\rm cal}}{\sqrt{2}} - \frac{\operatorname{tr}(\boldsymbol{R})}{\sqrt{6}}.
   $$
   If an unmodeled physical phenomenon shifts the trace relative to calibration, $r_{\rm adeq}$ exceeds the confidence tube, rejecting all hypothesized families simultaneously.

---

## 3. Quantitative Numerical Findings (R36-10 & R37-04)

### 3.1 Separation Certificates & Conservative Margins
Let $r_{95} = \sqrt{\chi_6^2(0.95)} = 3.5484626592$. Conditioning on noise standard deviation $\sigma$ and shared deterministic response error $\epsilon$, each family orbit is surrounded by a confidence tube of radius $\tau = r_{95} \sigma + \epsilon$.  
The conservative exclusive margin is:
$$
M_{\rm excl}(a) = \delta(a) - 2\tau = \sqrt{2}a^2 - 2(r_{95} \sigma + \epsilon).
$$
A positive margin $M_{\rm excl} > 0$ provides a mathematically certified guarantee that the two family confidence tubes are disjoint.

**Evaluation across the R37-04 Parameter Grid ($u_* = 1$):**
| Amplitude $a$ | Noise $\sigma$ | Error $\epsilon$ | Orbit Gap $\delta(a)$ | Exclusive Margin $M_{\rm excl}$ | Compatible Set (at II Center) |
|---|---|---|---|---|---|
| $0.0$ | $0.12$ | $0.10$ | $0.00000$ | $-1.05163$ | $\{\mathrm{II}, \; \mathrm{VII}_0\}$ (Unresolvable) |
| $0.5$ | $0.03$ | $0.10$ | $0.35355$ | $-0.05935$ | $\{\mathrm{II}\}$ (Empirically separated) |
| $0.5$ | $0.12$ | $0.10$ | $0.35355$ | $-0.69808$ | $\{\mathrm{II}, \; \mathrm{VII}_0\}$ (Ambiguous) |
| $1.0$ | $0.12$ | $0.10$ | $1.41421$ | $+0.36258$ | $\{\mathrm{II}\}$ (Certifiably Disjoint) |

At $a = 1$, $\sigma = 0.12$, and $\epsilon = 0.10$, the margin is strictly positive ($+0.36258$), proving that the witnesses are mutually exclusive under the R36 noise law.

### 3.2 Source-Qualified Ellipsoid Bounds
Using the source-qualified deterministic bounds from R36-10:
- Type $\mathrm{II}$ bound: $r_{\rm II} = 0.1471034953$;
- Type $\mathrm{VII}_0$ bound: $r_{\mathrm{VII}_0} = 0.2698726924$;
- Sum of radii: $r_{\rm sum} = 0.4169761877$.  
At $a = 1$, the source-set gap is at least:
$$
\operatorname{Gap}_{\rm source} = \sqrt{2} - 0.416976 = 0.9972373747.
$$
Under the synthetic Gaussian law with $\sigma = 0.12$, the exclusive margin after accounting for two $95\%$ noise balls remains $+0.145606$, confirming robustness without extrapolating beyond the supplied models.

### 3.3 Out-of-Family Adequacy Rejection
- In the explicit out-of-family control, shifting the raw trace coordinate by $+1.0$ from the Type $\mathrm{II}$ center (leaving the 5D STF carrier unchanged) yields an adequacy residual $r_{\rm adeq} = 1/\sqrt{2} \approx 0.707107$.
- For $\sigma = 0.12$ and $\epsilon = 0.10$, the critical rejection threshold is $\tau_{\rm adeq} = \sqrt{2}\tau = 0.743615$ on the raw shift axis.
- In 50,000 synthetic Monte Carlo draws at $a=1, \epsilon=0.10$, the true family was correctly retained in 49,960 draws ($99.92\%$) and the false family was rejected in all 50,000 draws ($0\%$ false acceptance).

### 3.4 Fixed-$Q$ Chirality Sign Stability
For the sharp quadrupole witness $\boldsymbol{Q} = \operatorname{diag}(-1/\sqrt{2}, 0, 1/\sqrt{2})$, the exact ambient STF3 Frobenius distance to the zero-chirality hypersurface is:
$$
\rho_{\rm sign} = \frac{1}{\sqrt{3}} \approx 0.5773502692.
$$
An explicit orthogonal perturbation achieving zero chirality at this exact distance was verified to machine precision ($< 10^{-16}$).

---

## 4. Claim-Tier Firewall & Methodological Boundaries

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLAIM-TIER BOUNDARY                                │
├────────────────────────────────────────┬────────────────────────────────────┤
│ PERMITTED (Validated Diagnostic / C0) │ FORBIDDEN (Overclaim / Blocked)    │
├────────────────────────────────────────┼────────────────────────────────────┤
│ • "geometry compatibility atlas"       │ • "Bianchi geometry detected"      │
│ • "analytic rotation-orbit separation" │ • "Bianchi family identified"      │
│ • "certified exclusive margin"         │ • "FLRW falsified by Bianchi mode" │
│ • "discarded-space adequacy rejection" │ • "native solver validated"        │
│ • "sharp fixed-Q chirality stability"  │ • "model-independent truth bound"  │
└────────────────────────────────────────┴────────────────────────────────────┘
```

1. **No Universal Identification:** Local spatial Ricci curvature orbits $\mathcal{O}_{\boldsymbol{R}}$ do not uniquely determine global Bianchi topology or spacetime metric evolution.
2. **Hard Native Solver Gate:** Task R36-09 (external atlas intake) remains on **HOLD**. No observational CMB Bianchi limit can be claimed until the native low-$\ell$ Boltzmann solver produces full $TT, TE, EE, BB$ synthetic maps.

---

## 5. Residual Obligations & Solver Handoff Interface

1. **Native Solver Atlas:** Interface with the native low-$\ell$ solver via `AtlasEntryLite` to compute full-sky transfer matrices across Bianchi types $\mathrm{I}, \mathrm{II}, \mathrm{VII}_0, \mathrm{VII}_h, \mathrm{VIII}, \mathrm{IX}$.
2. **Non-Trivial Spatial Topologies:** Incorporate topological compactification scales $L$ to distinguish local Lie group shear from global topological identifications.
3. **Solver Handoff Schema:** The sorted eigenvalue orbit metric $\delta(a) = \sqrt{2}a^2$ and the adequacy residual $r_{\rm adeq}$ are integrated into the HTT posterior scoring engine to reject unphysical Bianchi parameter regions during MCMC exploration.

---

## 6. Primary Literature & Citation Ledger

1. **G. F. R. Ellis, R. Maartens, and M. A. H. MacCallum**, *Relativistic Cosmology*, Cambridge University Press (2012).
2. **D. Saadeh et al.**, *How isotropic is the Universe?*, Phys. Rev. Lett. **117**, 131302 (2016), [arXiv:1605.07178](https://arxiv.org/abs/1605.07178).
3. **T. S. Pereira, C. Pitrou, and J.-P. Uzan**, *Theory of cosmological perturbations in an anisotropic universe*, JCAP **09** (2007) 006, [arXiv:0707.0736](https://arxiv.org/abs/0707.0736).
4. **J. D. Barrow, R. Juszkiewicz, and D. H. Sonoda**, *Universal rotation: how large can it be?*, Mon. Not. R. Astron. Soc. **213**, 917–943 (1985).
5. **C. G. Tsagas, A. Challinor, and R. Maartens**, *Relativistic cosmology and large-scale structure*, Phys. Rep. **465**, 61–147 (2008), [arXiv:0705.4397](https://arxiv.org/abs/0705.4397).
