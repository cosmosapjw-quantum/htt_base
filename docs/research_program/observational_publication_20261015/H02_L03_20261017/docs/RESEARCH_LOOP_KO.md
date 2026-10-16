# HTT 6-paper 다음 이론·코딩 루프: H02 calibration gauge + L03 paired null

2026-10-17 KST. Authority: Draft PR #550 head `d9089205c50dd698b0920770bb95e1885701320a`; immutable 42-node `PUBLICATION_DAG.json` (14 scoped completed, 28 pending). This is bounded independent theory/numerical research and NOT publication-level observational inference. No state upgrade.

## 1. Actual source identities, scientific input ceilings

* Cosmicflows-4 catalogue J/ApJ/944/94 source-locked subset: exactly 35,970 unique group IDs, `z_CMB∈(0.0100,0.1000)`, J2000 sourceward unit vector, `DMzp`, reported marginal `e_DMzp`, exactly one method-family label FP/TF/SN/OTHER. NPZ SHA-256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`, 1,235,181 bytes. Full source 38,053 groups/55,877 galaxies **not mounted in this sandbox**; it was independently hash-verified by the user locally. `e_DMzp` is not an independently calibrated diagonal noise law, and method family labels are not parent survey inclusion probabilities.
* Planck T/processing source: one physical sky, 6 alternative processing conditions, exactly 300 paired simulated sky rows with 32 real temperature coefficients each, observed shape 6×32 and paired shape 6×300×32. NPZ SHA-256 `0c104e41b2cbd979bbb92b61a43744fb0e17376d26dd8a534cc90ab79ca23b08` (462,850 bytes). Physical source-matched E2E/foreground/beam transfer and cross-product selection are not certified by this retained finite source. No Q/U polarization source is in this bank.

## 2. H02 exact gauge and a proper Gaussian calibration prior

Let `X_i∈R^8` comprise 3 dipoles and 5 STF2 functions of the **same** J2000 unit direction. Every selected group is assigned to exactly one of four method groups; let `D_m` be the corresponding 0/1 diagonal selector. Then **exactly, source by source**, `X=Σ_m D_mX`. An observation model with both a global common angular coefficient `β∈R^8` and arbitrary method angular calibration `γ_m∈R^8` reads

`y_i = Z0_i a + X_i β + Σ_m D_m(i)X_iγ_m + noise_i`.

For every δ, `(β, γ_m) -> (β+δ, γ_m−δ)` leaves the entire predicted catalogue invariant. Therefore, without an external angular-calibration anchor or proper prior, **global β is not identified**, even if the source geometry is full column rank after profiling only method intercepts. This is a finite linear model's algebraic gauge, not a universal physical spacetime no-go.

**Conditional Gaussian experiment only:** regard each published `e_DMzp` as an independent error σ_i and group method intercepts free. This is **not** physically justified for CF4's already aggregated shared-calibration data but defines a useful falsification oracle. The inverse-σ² centered Gram of method m is

`G_m=Σ_{i∈m}σ_i^{-2}(X_i−\bar X_m)(X_i−\bar X_m)^T`, with weighted method mean `\bar X_m`. If **independently** `γ_m~N(0, τ² I_8)`, properly integrating nuisance (Schur complement, source conditional) yields

`I_β(τ)=Σ_m G_m(I_8+τ² G_m)^{-1}`.

For each eigenvalue λ of G_m the information eigen-contribution is `λ/(1+τ² λ)`. Wolfram independently checked the rational identity `λ−λ²/(λ+τ⁻²)=λ/(1+λτ²)` and its τ→∞ zero limit. Our second independent verification compares the centered-Gram formula to the dense data-space covariance `D+τ²XX^T` **with the intercept reprofiled**; agreement <10⁻⁹ absolute for manufactured 35-row input.

The 35,970 actual source directions give `min eig Iβ(0)=23973.057776858226`, `max eig=142523.26146195657`, with units [mag⁻² times inverse raw angular-feature basis]. At assumed `τ=0.02 mag`, minimum/maximum are 6373.956/8808.065; at `τ=0.1 mag`, 389.936/397.696; at `τ=0.5 mag`, 15.983/15.996. For τ much larger than the source statistical scale and all four methods unanchored, `Iβ(τ)~(4/τ²)I8` and marginal standard errors approach `τ/2` per raw basis coefficient. Numerical fit to actual source at τ=.5 gives SE 0.25004–0.25010 mag. At τ→∞ all eight global angular modes vanish as identifiable directions. Fixing exactly **one method's angular calibration** can restore formal rank 8, but that is an **unprovided physical assumption**, not an instrument calibration we measured.

Uniform release zero-point shift δ (including the published −0.147 mag among the 37,825 released DMav-positive groups) leaves method-intercept-profiled data unchanged, with maximal numerical discrepancy <10⁻¹² mag. A **constant** zero point cannot alone mimic an angular mode; method-angle/sky-dependent calibration can. Do not treat DMzp, DMav and method-mean galaxy distances as independent data.

No posterior evidence ratio or physical Hubble/shear coefficient is computed. Parent survey completeness, actual W1 TF raw targeting, common calibration covariance and peculiar velocity field are still needed for H02's proper physical likelihood. Original Table2/3/4 exact 55,877/38,053/38,053-row auditor from PR #550 should be executed in `/mnt/extdrive/workdir/htt_open_data` and reconciled with this subset. Stiskalek et al. MNRAS 546(2) (2026), doi:10.1093/mnras/staf2048 shows observational dipole/template distinction versus local peculiar flows, so rank alone is not evidence of anisotropic spacetime.

## 3. L03 source-paired processing scan and crossed-noise reuse

The six `processing_coefficients.npz` treatments represent **six methods/conditions for each shared latent sky**, not 1,800 independent skies. For each of six conditions j define `E_j=Σ_{k=1}^{32}c_{jk}²`. Freeze an energy scale `s_j=median(E_{j,i},i=0..99)` from the **first 100 complete sky IDs**, and for each held-out sky i=100..299 define `T_i=max_j(E_{ji}/s_j)`. The observed source statistic is `Tobs=max_j(E_obs,j/s_j)`.

With 200 held-out sky rows we calculate `T_obs=0.9821895601885062`, 146 values `T_i>=Tobs`, conditional source-bank finite rank `(146+1)/(200+1)=0.7313432835820896`, heldout median 1.1366852058921277 and q95 1.8242019929940374. Correlation between method energy conditions ranges from 0.566919 to 0.999360. This is a **descriptive rank within the recorded source-processing simulator**, not an admitted p-value for a real Planck anomaly because actual E2E/null exchangeability is not established. Splitting calibration/evaluation reduces plug-in reuse, not systematic law mismatches; the 100+200 split is current diagnostic choice, not retrospective cosmic preregistration. DO NOT interpret 0.73134 as an independent discovery null test.

For cross-joined simulated CMB sky `U_i` and noise `V_j`, even if every Cartesian combination exists, an independent zero-mean additive model `T_ij=U_i+V_j` has

`Var(mean_{ij}T_ij)=σ_U²/N_CMB+σ_V²/N_noise`, NOT `(σ_U²+σ_V²)/(N_CMB N_noise)`.

At 999 skies/300 noise realizations and equal per-component variance, treating all 299700 combinations as independent would underestimate standard error by `sqrt((999+300)/2)=25.4852898747`. These counts are the official Planck 2018 release's CMB and noise banks, not assertions the currently loaded six×300 source bank is a full matched E2E cross-combination. Official Planck 2018 IV notes residual noise/systematic mismatch and fixed CMB extraction weights; validate mask/split/beam/foreground, independent ID and simulation compatibility before any physical p.

## 4. Remaining S02 and other physical gates

`S02` remains pending: a Gaussian conditional *working* `β` precision or T-process rank is not the physical posterior of signed `x_C,Q,F,G_F`. Undefined mass is not zero-filled, no construction of joint tilt/curvature/shear likelihood. `L01` likewise remains pending until true Q/U source Pol mask spin-2 high-ell injection, source beam/foreground and E2E law are confirmed. `S04,L03,H02,V03,B02,K03,K04` retain external-missing physical gates. All six papers NOT_READY_TO_SUBMIT, 14/42 complete.

## 5. Implementation, tests and reproducibility

Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests` in this archive's root. Tests include two real SHA locked source arrays, exact source gauge, true method-center offset invariance, method eigenvalue positivity, dense covariance Schur validation, conditional anchor and τ=∞, 200 held-out paired sky count, scan condition permutation, matched sky-row reordering, deliberate pair breaking, crossed noise variance and rejected source tampering. Numerical outputs `results/H02_ACTUAL_SELECTED_SOURCE_FISHER.json` and `results/L03_ACTUAL_SOURCE_PAIRED_SCAN.json` have deterministic content digests and are regenerated by `python src/run_studies.py`. Source inputs are unmodified copies from previous immutable checkpoints.

### Reference papers
- Tully et al. Cosmicflows-4 ApJ 944, 94 (2023), https://doi.org/10.3847/1538-4357/ac94d8 and https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html
- Stiskalek, Desmond, Lavaux, No evidence for local H0 anisotropy, MNRAS 546(2), 2026, https://doi.org/10.1093/mnras/staf2048
- Planck Collaboration, 2018 results IV: Diffuse component separation, A&A 641 A4 (2020), https://doi.org/10.1051/0004-6361/201833881
- Planck Legacy Archive product/simulation source: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Simulation_data
