# A14 · N4 — Selection-response null family (von Hausegger–Dalang)

**Appendix**: A14 (§11.10.2 of `BASS_PY_HTT_TSC_RESEARCH_PLAN.md`)
**Version**: 2026-04-19 (DOS-A14 landing).
**Code anchor**: `bass_py/htt/htt/nulls/clustering.py` (class
`SelectionResponseNull`; shares module with N3 for efficiency — the
importable class name is distinct).
**Primary reference**: von Hausegger & Dalang, *Selection-function
anisotropies in number-count cosmology*, PRD 2025.

---

## 1. Physical origin

A survey's selection function $S(\hat{\mathbf n}, z, L)$ controls the
fraction of sources at a given sky direction, redshift, and luminosity
that end up in the catalogue. If $S$ varies in a way that is
*correlated with a preferred axis* — typically ecliptic latitude for
scanning surveys, or declination for transit radio surveys — a
*selection-response* dipole is injected into the number counts. Unlike
N3 (genuine clustering over-density), N4 arises from a *measurement-
dependent* completeness profile: the sky is isotropic, but our window
onto it is not.

von Hausegger & Dalang (2025) quantified the effect for the CatWISE
kinematic-dipole analysis and found that a $\sim 10\%$ variation of
effective magnitude limits with ecliptic latitude produces a dipole
residual of order $2 \times 10^{-4}$ — a candidate resolution of part
of the tension.

## 2. Forward model

$$
\epsilon_1^{\text{N4}}_{\mathrm{CW}} \sim
   \mathcal N(A_{\rm sel},\, \sigma_{\mathrm{stat,CW}}),
\qquad
\epsilon_1^{\text{N4}}_{\mathrm{radio}} \sim
   \mathcal N(0.3\, A_{\rm sel},\, \sigma_{\mathrm{stat,rad}}),
\qquad
b^{\text{N4}}_{\mathrm{CF4}} \sim
   \mathcal N(0,\, \sigma_{\mathrm{CF4}}).
$$

All clipped to non-negative. The lower $(0.3)$ radio coupling reflects
the different selection function of the Secrest 2021 radio sample
(flux-limited at 1.4 GHz, no IR magnitude dependence). CF4 is
*unaffected* — the Cosmicflows selection is luminosity-driven, not
sky-position-driven.

The cross-survey correlation

$$
\rho^{\text{N4}}_{\mathrm{CW,radio}} = 0.1
$$

is at the statistical-only floor — N4 does *not* elevate the
shared-cause statistic. This separates N4 from N2 (which does) and
from N3 (intermediate).

## 3. Amplitude prior

Calibrated to the von Hausegger–Dalang 2025 posterior median:

$$
A_{\rm sel} \sim \mathcal N(\mu = 2 \times 10^{-4},\,
                            \sigma = 1 \times 10^{-4}),
\qquad A_{\rm sel} \ge 0.
$$

Implemented as `SelectionResponseNull(A_sel_mean=2e-4,
A_sel_std=1e-4)`. The amplitude is smaller than N3 because selection
effects are *bounded* by completeness variation (typically ≲ 15%),
while clustering is not bounded from above.

Scale check: $\langle A_{\rm sel}\rangle = 2 \times 10^{-4}$ is $\sim
1/7$ of the CMB kinematic dipole. Combined with N1 scanning
($3 \times 10^{-4}$) the two can jointly account for $\sim 5 \times
10^{-4}$, still well below the CatWISE observation — so N1+N4 are
*necessary but not sufficient* explanations for the tension.

## 4. Sky pattern

Ecliptic-axis aligned (same as N1), but with a *different amplitude
profile*: N1 peaks at the poles, while N4 is driven by the ecliptic
*gradient* of the selection function — so it projects onto the
ecliptic dipole with a $\cos(\text{ecliptic lat})$ response rather
than N1's $\cos^2$ scanning profile. The two are therefore only
partially degenerate; a per-survey fit that lets the ecliptic-pole
*radial* profile vary can in principle separate them.

## 5. Statistical signature and distinguishing channels

| Channel | N4 contribution | Why |
|---|---|---|
| (b) TT anomalies | — | Planck SMICA has its own selection |
| (c) TE / low-ℓ cross | — | ibid. |
| (d) Bulk flow / velocity monopole | Leading (CW + partial radio) | N4 lives here |
| (e) BAO | — | selection is not scale-coupled |
| (f) MES hard ceiling | — | no Σ² footprint |
| (g) MES soft sigmoid | — | ibid. |
| (h) Direct $D_\ell$ χ² | — | different statistic |

Unlike N3, N4 does not reach CF4 — so a tension claim that is *robust*
to CF4 but *vulnerable* to removing CatWISE is a classic N4 failure.

## 6. False-positive prediction

$$
\text{FPR}_{\text{N4}}(\text{FLRW\_tilt}) < 0.05.
$$

At the published amplitude this is the *safest* null — a consequence
of its bounded physical mechanism and zero CF4 contribution.

## 7. Pitfalls

- **Degeneracy with N1**: both project on the ecliptic axis. Use the
  radial profile of the reconstructed dipole to distinguish (N1: polar
  sharp; N4: broad gradient).
- **Ecliptic → Galactic rotation**: same caveat as N1; evaluate the
  ecliptic-pole direction at the survey's equinox.
- **Luminosity-dependence**: the $A_{\rm sel}$ prior assumes the
  flux-limit variation alone. An evolving point-source subtraction
  threshold can add a $\sim 1.5\times$ amplification; not in the
  fiducial N4.

## 8. Provenance

| Field | Value |
|---|---|
| Forward-model source | `bass_py/htt/htt/nulls/clustering.py::SelectionResponseNull` |
| Amplitude prior | $\mathcal N(2\times 10^{-4},\,10^{-4})$ (von Hausegger–Dalang 2025) |
| CF4 coupling | 0 (exactly zero — per-se) |
| FPR datum | *pending* — ch08 §8.5 / F49 |
| Generated on | 2026-04-19 |
