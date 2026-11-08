# PR4 Commander Low-Ell Polarization Morphology Report Delta

**Task**: `PR-R36-06-PR4-MORPHOLOGY`  
**Owner**: `obsstat`  
**Claim Tier**: `C0_DIAGNOSTIC_ONLY`  
**Status**: `COMPLETED_SUCCESS`  
**Transfer Source**: None (direct processed observational data and matched pipeline simulations; no Bianchi transfer or beam deconvolution)

---

## 1. Scope and Objective

This report delta establishes the statistical baseline for low-multipole ($\ell = 2, 3, 4$) polarization morphology extracted from the Planck PR4 (NPIPE) Commander full-mission observed polarization map against a qualified ensemble of 100 public end-to-end processed Commander Monte Carlo simulations (`mc_0300` through `mc_0399`).

The target features evaluate potential low-$\ell$ anomalies in cosmic polarization:
1. **$J_{234}$**: The normalized, rotationally invariant tripolar Wigner $3j$ contraction of E-mode multipoles ($\ell = 2, 3, 4$), sensitive to parity-odd/shape contractions.
2. **$|J_{234}|$**: The magnitude of the contraction, invariant under parity inversion $a_{\ell m} \to (-1)^\ell a_{\ell m}$.
3. **$\mathrm{alignment}_{23}^2$**: The squared cosine of the angle between the principal quadrupole ($\ell=2$) and octupole ($\ell=3$) polarization axes derived from the low-$\ell$ quadrupole/octupole power tensors.
4. **$C_\ell^{\mathrm{CMB}}$**: The unbinned E-mode pseudo-power spectrum at $\ell = 2, 3, 4$.

---

## 2. Methodology and Observational Operator

### Source Data
- **Observed Map**: Planck PR4 (NPIPE) Commander full-mission CMB map (`COM_CMB_IQU-commander_4096_R4.00_full.fits`), HDU 2 (Stokes $Q$ and $U$), Galactic coordinates, COSMO polarization angle convention, native resolution $N_{\mathrm{side}} = 2048$, units $\mathrm{K}_{\mathrm{CMB}}$.
- **Null Simulation Ensemble**: 100 fixed public end-to-end processed Commander FULL CMB simulation realizations (`npipe6v20_commander_cmb_2048_mc_0300_005a.fits` through `mc_0399`), HDU 1, scaled to $\mathrm{K}_{\mathrm{CMB}}$ from native $\mu\mathrm{K}_{\mathrm{CMB}}$.
- **Galactic Mask**: The Planck PR4 LoLLiPoP binary mask (`mask_PR4_Lollipop_ns16.fits`), containing 1273 retained pixels at $N_{\mathrm{side}} = 16$ ($f_{\mathrm{sky}} \approx 0.3108$). The mask is hierarchically upgraded by exact nested pixel repetition (repetition factor 16384 to $N_{\mathrm{side}} = 2048$, yielding 5,214,208 retained pixels) and applied identically to $Q$ and $U$ fields in RING pixel ordering.

### Harmonic Decomposition
- Harmonics are extracted via `healpy.map2alm_spin` with spin $s=2$, $\ell_{\max}=4$, $m_{\max}=4$, without beam inversion or artificial filtering.
- Retained $E$ and $B$ coefficients are verified to satisfy complex conjugate symmetry $a_{\ell,-m} = (-1)^m a_{\ell m}^*$, finite norm, and numerical stability against $\ell_{\max}=8$ truncation.
- Operator linearity and anisotropic mask response are confirmed via unit test mode injections.

---

## 3. Results: Observed vs. 100 MC Null Ensemble

### Observed Values
- $J_{234} = +0.023303$
- $|J_{234}| = 0.023303$
- $\mathrm{alignment}_{23}^2 = 0.458662$
- $C_2 = 1.1755 \times 10^{-14} \mathrm{ K}_{\mathrm{CMB}}^2$
- $C_3 = 1.1581 \times 10^{-15} \mathrm{ K}_{\mathrm{CMB}}^2$
- $C_4 = 3.4499 \times 10^{-15} \mathrm{ K}_{\mathrm{CMB}}^2$

### Null Ensemble Statistics ($N = 100$)
| Feature | Observed | MC Mean | MC Std | MC Median | MC 16% | MC 84% |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$J_{234}$** | $+0.02330$ | $+0.00587$ | $0.05150$ | $+0.00278$ | $-0.05130$ | $+0.06057$ |
| **$\|J_{234}\|$** | $0.02330$ | $0.04439$ | $0.02640$ | $0.04269$ | $0.01651$ | $0.07309$ |
| **$\mathrm{alignment}_{23}^2$** | $0.45866$ | $0.24249$ | $0.24916$ | $0.12965$ | $0.01060$ | $0.55969$ |
| **$C_2$ ($\mathrm{K}_{\mathrm{CMB}}^2$)** | $1.175 \times 10^{-14}$ | $5.183 \times 10^{-15}$ | $3.722 \times 10^{-15}$ | $4.188 \times 10^{-15}$ | $1.875 \times 10^{-15}$ | $8.317 \times 10^{-15}$ |
| **$C_3$ ($\mathrm{K}_{\mathrm{CMB}}^2$)** | $1.158 \times 10^{-15}$ | $3.043 \times 10^{-15}$ | $1.777 \times 10^{-15}$ | $2.757 \times 10^{-15}$ | $1.257 \times 10^{-15}$ | $4.380 \times 10^{-15}$ |
| **$C_4$ ($\mathrm{K}_{\mathrm{CMB}}^2$)** | $3.450 \times 10^{-15}$ | $3.224 \times 10^{-15}$ | $1.739 \times 10^{-15}$ | $3.067 \times 10^{-15}$ | $1.662 \times 10^{-15}$ | $4.633 \times 10^{-15}$ |

### Empirical $p$-Values
Using the standard unbiased plus-one rule $p = \frac{k + 1}{N + 1}$ with $N = 100$:
- **Signed $J_{234}$**: $k = 43$ simulations have $J_{234}^{\mathrm{MC}} \ge J_{234}^{\mathrm{obs}}$, giving:
  $$p(J_{234} \ge \mathrm{obs}) = \frac{43 + 1}{100 + 1} = \frac{44}{101} \approx 0.4356 \quad (p \approx 0.44)$$
- **Magnitude $|J_{234}|$**: $k = 74$ simulations have $|J_{234}^{\mathrm{MC}}| \ge |J_{234}^{\mathrm{obs}}|$, giving:
  $$p(|J_{234}| \ge |\mathrm{obs}|) = \frac{74 + 1}{100 + 1} = \frac{75}{101} \approx 0.7426 \quad (p \approx 0.74)$$
- **Quadrupole-Octupole Alignment $\mathrm{alignment}_{23}^2$**: $k = 22$ simulations have $(\mathrm{alignment}_{23}^2)^{\mathrm{MC}} \ge (\mathrm{alignment}_{23}^2)^{\mathrm{obs}}$, giving:
  $$p(\mathrm{alignment}_{23}^2 \ge \mathrm{obs}) = \frac{22 + 1}{100 + 1} = \frac{23}{101} \approx 0.2277 \quad (p \approx 0.23)$$

---

## 4. Scientific Conclusion and Claim Boundaries

1. **Null Consistency**: The observed PR4 Commander polarization morphology statistics are entirely within normal statistical fluctuations of the isotropic $\Lambda\mathrm{CDM}$ + noise null model. With $p \approx 0.44$ for signed $J_{234}$, $p \approx 0.74$ for $|J_{234}|$, and $p \approx 0.23$ for quadrupole-octupole alignment, there is no evidence of anomalous low-$\ell$ polarization morphology or alignment in the Commander full-mission map.
2. **Claim Tier**: Classified strictly as `C0_DIAGNOSTIC_ONLY`.
3. **Forbidden Claims**: These results do not detect Bianchi geometry, do not identify any Bianchi model family, and do not constitute a model-independent truth certificate.
4. **Delivered Artifacts**:
   - Aggregate summary JSON: `COMMANDER_MC100_AGGREGATE.json`
   - Publication vector histograms: `null_distribution_histograms.pdf` and `null_distribution_histograms.png`
   - Automated aggregation script: `aggregate_mc_morphology.py`
