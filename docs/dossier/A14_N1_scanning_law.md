# A14 · N1 — WISE scanning-law null family

**Appendix**: A14 (§11.10.2 of `BASS_PY_HTT_TSC_RESEARCH_PLAN.md`)
**Version**: 2026-04-19 (DOS-A14 landing; FPR numbers remain *pending* until
the htt null competition run lands in ch08 §8.5).
**Code anchor**: `bass_py/htt/htt/nulls/scanning_law.py` (class
`ScanningLawNull`).
**Primary reference**: Bashir et al., *A posteriori SBI for the WISE
CatWISE dipole*, arXiv:2507.NNNNN (2025).

---

## 1. Physical origin

The WISE telescope executes a Sun-synchronous scanning pattern that
yields longer effective integration at the ecliptic poles than at the
ecliptic equator. In number-count projections this inhomogeneity
imprints a spurious dipole-like excess in completeness along the
ecliptic-pole axis — structurally indistinguishable from a low-amplitude
kinematic dipole to any single-survey pipeline that treats completeness
as isotropic. This is the mechanism identified by Bashir+2025 (SBI
reanalysis of the CatWISE2020 dipole); it is the target of null family
**N1**.

## 2. Forward model

Let the catalogue's observed number-count field be
$N(\hat{\mathbf n}) = \bar N \big[1 + \mathcal D(\hat{\mathbf n})\big]$
with total dipole component $\mathcal D = \boldsymbol{\epsilon}_1 \cdot
\hat{\mathbf n}$. Under N1 we replace the kinematic $\boldsymbol
\epsilon_1$ with a scanning-law contribution

$$
\boldsymbol\epsilon_1^{\text{N1}}
 = A_{\mathrm{scan}} \; \hat{\mathbf n}_{\mathrm{ecl-pole}},
$$

where $\hat{\mathbf n}_{\mathrm{ecl-pole}}$ is the unit vector toward the
north ecliptic pole ($(l,b) \approx (96.4°,\,29.8°)$ in galactic
coordinates) and the amplitude $A_{\mathrm{scan}}$ is the random
variable of interest.

Radio (Secrest+2021) and CF4 (Watkins+2023) counts are *not* produced
by WISE scanning and are modelled as unaffected ($\boldsymbol
\epsilon_1^{\text{N1}}_{\text{radio}} = 0$, $b^{\text{N1}}_{\text{CF4}}
= 0$); the family therefore predicts a *shared-cause failure*: CatWISE
shows an excess but the radio amplitude remains statistics-consistent
with zero. That cross-survey pattern is the N1-specific fingerprint
used downstream by `htt.infer.shared_cause`.

## 3. Amplitude prior

From the Bashir+2025 SBI posterior (their Fig. 4, top panel, marginal
over $A_{\mathrm{scan}}$) we adopt

$$
A_{\mathrm{scan}} \sim \mathcal N(\mu = 3 \times 10^{-4},\,
                                  \sigma = 1 \times 10^{-4}),
\qquad A_{\mathrm{scan}} \ge 0.
$$

This is the prior encoded in `ScanningLawNull(A_scan_mean=3e-4,
A_scan_std=1e-4)`. The non-negativity clip reflects the fact that
scanning-law completeness fluctuations can *add* to the observed
dipole but not cancel a true one — drawing $A<0$ would be
unphysical (the scanning excess is a positive bias on the
ecliptic-pole direction).

Conservative scaling: the published CatWISE $\epsilon_1^{\text{obs}}
\approx 1.55 \times 10^{-2}$ is ≈ 50× this scanning amplitude, so N1
alone cannot account for the observation. It is, however, of the same
order as the statistical uncertainty of the CatWISE dipole (their
$\sigma_{\mathrm{stat}} \sim 3 \times 10^{-4}$) and so contributes
non-negligibly when the signal shrinks under other systematics.

## 4. Sky pattern

Along the ecliptic-pole axis, localised; azimuthally symmetric around
it. In galactic $(l,b)$ the expected dipole direction is $(96.4°,
29.8°)$ — offset by $\approx 59°$ from the observed CatWISE direction
$(233.8°, 32.8°)$. That angular offset is the most direct way to
separate N1 from a true kinematic dipole when a direction posterior is
available: the N1 null injects to the *wrong* pole.

## 5. Statistical signature and distinguishing channels

N1 lives almost entirely in the BASS *direction* channel (channel **d**
of A28) and in the shared-cause diagnostic (ch08 §8.8). It does *not*
enter:

| Channel | N1 contribution | Why |
|---|---|---|
| (b) TT anomalies | — | Planck SMICA is not WISE-selected |
| (c) TE / low-ℓ cross | — | ibid. |
| (d) Bulk flow / velocity monopole | Leading (CatWISE-only) | N1 exists here by construction |
| (e) BAO / sound horizon | — | scanning law is number-count only |
| (f) MES hard ceiling | — | no Σ² footprint |
| (g) MES soft sigmoid | — | ibid. |
| (h) Direct $D_\ell$ χ² | — | anisotropy encoded in different statistic |

For 15-model evidence, N1 injection should therefore *inflate* the
ln B of FLRW relative to FLRW_tilt at fixed CatWISE $\epsilon_1$, since
it absorbs the excess without requiring a kinematic component.

## 6. False-positive prediction

Under the BASS pipeline at $N_{\rm mocks}=10^3$ realisations, the
expected false-positive rate for rejecting the FLRW null *while the
true underlying cosmology is FLRW + N1* is

$$
\text{FPR}_{\text{N1}}(\text{FLRW}) \;\; < 0.05,
$$

per §2.3.28 of the parent plan. Higher FPR indicates the pipeline is
mis-attributing the scanning-law bias as a kinematic signal. The
value is populated from the ch08 §8.5 null-competition heatmap (F49);
DOS-A14 fixes only the *derivation*.

## 7. Pitfalls

- **Ecliptic → Galactic rotation convention**: the ecliptic pole must
  be taken at the *equinox of observation* (J2000 for CatWISE). Using
  a drifted epoch leaks the scanning axis by $\sim 10^{-3}$ rad —
  small, but non-negligible next to the direction-posterior radius.
- **Combined N1 + kinematic injection**: when both a real $\beta$ and
  a scanning-law bias are present, their *vector* sum enters the
  observation; the pipeline's FPR is defined only in the *pure*-null
  limit (the mocked truth carries no kinematic component).
- **Degeneracy with N5 (survey axis)**: both produce CatWISE-aligned
  residuals. Distinguishing them requires the radio correlation
  coefficient $\rho_{\mathrm{CW,radio}}$ (see N5).

## 8. Provenance

| Field | Value |
|---|---|
| Forward-model source | `bass_py/htt/htt/nulls/scanning_law.py` |
| Prior adopted | $\mathcal N(3\times 10^{-4},\, 10^{-4})$ (Bashir+2025) |
| FPR datum | *pending* — ch08 §8.5 / F49 |
| Generated on | 2026-04-19 |
