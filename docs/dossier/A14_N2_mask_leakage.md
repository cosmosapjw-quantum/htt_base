# A14 · N2 — Galactic mask-leakage null family

**Appendix**: A14 (§11.10.2 of `BASS_PY_HTT_TSC_RESEARCH_PLAN.md`)
**Version**: 2026-04-19 (DOS-A14 landing; FPR numbers *pending* until
ch08 §8.5).
**Code anchor**: `bass_py/htt/htt/nulls/mask_leakage.py` (class
`MaskLeakageNull`).
**Primary references**: Planck 2018 Mission Paper (A&A 641, A1 / 2020)
for the SMICA mask construction; von Hausegger+2022 on Galactic
foreground residuals in dipole estimates.

---

## 1. Physical origin

Every all-sky dipole analysis is performed on a *masked* sky: a
Zone-of-Avoidance (ZoA) cut around the Galactic plane is applied to
reject the strongest foregrounds (synchrotron, free-free, AME). Any
residual flux that leaks through an imperfect mask — whether from
edge-of-mask diffraction, unsubtracted point sources, or dust
temperature error — biases the reconstructed dipole. Unlike N1, the
leakage is *Galactic-frame* aligned and affects every survey that
shares the Galactic mask geometry.

## 2. Forward model

Let $f_{\mathrm{cont}}$ be the *contamination fraction* — the
effective dipole amplitude leaked through the mask divided by the
observed dipole. The fiducial forward model is

$$
\epsilon_1^{\text{N2}}_{\mathrm{CW}}
  = f_{\mathrm{cont}} \cdot \epsilon_1^{\text{obs}}_{\mathrm{CW}},
\qquad
\epsilon_1^{\text{N2}}_{\mathrm{radio}}
  = 0.5 \; f_{\mathrm{cont}} \cdot \epsilon_1^{\text{obs}}_{\mathrm{CW}},
$$

i.e. the radio surveys experience the Galactic leakage at *half* the
CatWISE rate (the factor 0.5 is the wavelength-averaged ratio of
Galactic dipole contrast, calibrated against the Planck 2018 residual
maps; see mask_leakage.py docstring). The CF4 bulk-flow amplitude is
not affected directly.

The shared Galactic origin inflates the $\mathrm{CW}$–$\mathrm{radio}$
correlation coefficient from its nominal $\rho_{\mathrm{CW,radio}}
\approx 0.1$ (statistical only) to

$$
\rho^{\text{N2}}_{\mathrm{CW,radio}} = 0.3.
$$

This is the N2-specific fingerprint: N2 pushes $\rho$ up; N1 and N4
keep $\rho$ near 0.1.

## 3. Amplitude prior

A single non-random hyperparameter fixes the prior:

$$
f_{\mathrm{cont}} = 0.15 \qquad
\text{(`contamination\_frac=0.15` in the code)}.
$$

The per-realisation amplitude is then

$$
\epsilon_1^{\text{N2}}_{\mathrm{CW}} \sim
   \mathcal N\!\big( f_{\mathrm{cont}}\, \epsilon_1^{\mathrm{obs}}_{\mathrm{CW}},
                     \sigma_{\mathrm{stat,CW}} \big),
$$

clipped to $\epsilon_1 \ge 0$. The fixed $f_{\mathrm{cont}}$ is our
*conservative* point prior — a Gaussian over $f_{\mathrm{cont}}$ could
be adopted in a follow-up sweep, but its posterior is too narrow in
the Planck residuals to be worth marginalising at the current FPR
precision.

## 4. Sky pattern

Aligned with the Galactic north–south asymmetry of residual
foregrounds; in galactic $(l,b)$ the expected contamination axis is
close to $(l,b) \approx (0°,90°) \oplus (0°,-90°)$ with slight
hemisphere imbalance from the Planck 2018 $\mathrm{Nside}=2048$
high-frequency mask. This leaves the leaked dipole *orthogonal* to
the observed CatWISE direction $(233.8°, 32.8°)$, so direction-aware
channels (d of A28) can separate N2 from a real signal once the
direction credible cone is ≲ 30°.

## 5. Statistical signature and distinguishing channels

| Channel | N2 contribution | Why |
|---|---|---|
| (b) TT anomalies | *weak* (inflated $\sigma$) | Foreground residual also biases low-ℓ TT |
| (c) TE / low-ℓ cross | *weak* | ibid. |
| (d) Bulk flow / velocity monopole | Leading | direction-misaligned excess |
| (e) BAO | — | mask leakage does not produce a BAO-scale feature |
| (f) MES hard ceiling | — | no Σ² footprint |
| (g) MES soft sigmoid | — | ibid. |
| (h) Direct $D_\ell$ χ² | *weak* | residual foreground contributes at low ℓ |

The N2 evidence signature is primarily $\uparrow \rho_{\mathrm{CW,rad}}$
and a mild $\sigma_{\mathrm{eff}}$ inflation in channel (b).

## 6. False-positive prediction

Using the BASS mock calibration (ch08 §8.10), the expected false
discovery rate for the tilted-FLRW model under pure N2 injection is

$$
\text{FPR}_{\text{N2}}(\text{FLRW\_tilt}) < 0.05,
$$

per the §2.3.28 gate. Unlike N1, the shared-cause diagnostic $\rho$
actively *exposes* N2 — we expect the FPR to stay well below the
0.05 ceiling once the correlation test is folded in.

## 7. Pitfalls

- **Point-source residuals vs diffuse leakage**: $f_{\mathrm{cont}} =
  0.15$ is calibrated to *diffuse* residuals. Point-source residuals
  (radio catalogue blending) are handled in a separate null and should
  not be double-counted.
- **Hemispherical imbalance**: a purely north-hemisphere Galactic leak
  is non-dipolar at the catalogue level; the fiducial N2 draws
  symmetric leakage and may under-estimate the effect at high ecliptic
  latitudes.

## 8. Provenance

| Field | Value |
|---|---|
| Forward-model source | `bass_py/htt/htt/nulls/mask_leakage.py` |
| Contamination fraction prior | $f_{\mathrm{cont}} = 0.15$ (point value) |
| FPR datum | *pending* — ch08 §8.5 / F49 |
| Generated on | 2026-04-19 |
