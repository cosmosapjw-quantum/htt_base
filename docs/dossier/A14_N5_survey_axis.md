# A14 · N5 — Survey-axis null family

**Appendix**: A14 (§11.10.2 of `BASS_PY_HTT_TSC_RESEARCH_PLAN.md`)
**Version**: 2026-04-19 (DOS-A14 landing).
**Code anchor**: `bass_py/htt/htt/nulls/clustering.py` (class
`SurveyAxisNull`).
**Primary reference**: no single published source — this family
aggregates the residual CatWISE–Radio sky-geometry overlap identified
during the BASS pipeline's cross-survey audit (ch08 §8.8).

---

## 1. Physical origin

CatWISE and the Secrest-radio catalogue were both built on sky-tiles
that share (i) ecliptic-latitude dependence of integration time and
(ii) a declination footprint tracking ground-based follow-up for the
radio catalogue. A common observational axis — not a common physical
origin — therefore correlates their systematic residuals. Unlike N3
(clustering) and N4 (selection) which arise from distinct mechanisms,
N5 is *operationally defined* by the shared sky geometry: whatever
pattern is impressed by the joint $(\text{ecliptic lat}, \text{decl})$
overlap.

This is the null family that is most directly exposed by the
shared-cause diagnostic of ch08 §8.8; it is explicitly *not* Bashir-
or Hausegger-type.

## 2. Forward model

Let $A_{\rm common}$ be a shared amplitude. The per-survey systematic
is

$$
A_{\mathrm{CW}} = A_{\rm common} + \eta_{\rm CW}, \qquad
\eta_{\rm CW} \sim \mathcal N(0, 10^{-4}),
$$
$$
A_{\mathrm{rad}} = A_{\rm common} + \eta_{\rm rad}, \qquad
\eta_{\rm rad} \sim \mathcal N(0, 1.5 \times 10^{-4}).
$$

The observed dipoles are

$$
\epsilon_1^{\text{N5}}_{\mathrm{CW}}
 = |A_{\mathrm{CW}} + n_{\mathrm{CW}}|,
\quad
\epsilon_1^{\text{N5}}_{\mathrm{radio}}
 = |A_{\mathrm{rad}} + n_{\mathrm{rad}}|,
\quad
b^{\text{N5}}_{\mathrm{CF4}}
 \sim \mathcal N(0, \sigma_{\mathrm{CF4}}),
$$

with the usual per-survey noise $n_\cdot$. CF4 is not affected.

The resulting effective correlation

$$
\rho^{\text{N5}}_{\mathrm{CW,radio}} = \rho_{\rm shared} = 0.5
$$

is the **highest** of any null family — N5 injects shared-systematic
coherence explicitly. This is the identifying signature: N5 is where
the shared-cause diagnostic $\rho_{\mathrm{CW,rad}}$ runs to $\ge
0.3$ robustly across realisations.

## 3. Amplitude prior

No literature posterior — we pick a *conservative* one-parameter prior
matching typical BASS mission-level systematic residuals:

$$
A_{\rm common} \sim \mathcal N(\mu = 3 \times 10^{-4},\, \sigma = 10^{-4}),
\qquad \rho_{\rm shared} = 0.5.
$$

Encoded as `SurveyAxisNull(rho_shared=0.5, A_axis_mean=3e-4)`. No
non-negativity clip is applied to $A_{\rm common}$ before the
per-survey projection (a negative common amplitude is physically
possible under N5 — the shared geometric axis can *suppress* one
survey while boosting the other). The absolute value is taken after
per-survey noise is added.

## 4. Sky pattern

Along the intersection of ecliptic-pole and declination-footprint
axes — roughly $(l, b) \approx (60°, -15°)$ in the galactic frame, or
the negative-dec ecliptic pole. This direction is *close* to the
observed CatWISE $(233.8°, 32.8°)$ only when projected through the
joint geometry; on the unit sphere it is in fact offset by $\sim 140°$,
so direction-resolved analyses separate N5 from a real signal much
more easily than from N1.

## 5. Statistical signature and distinguishing channels

| Channel | N5 contribution | Why |
|---|---|---|
| (b) TT anomalies | — | CatWISE/Radio are not CMB surveys |
| (c) TE / low-ℓ cross | — | ibid. |
| (d) Bulk flow / velocity monopole | Leading (CW + Radio, shared) | N5 lives here |
| (e) BAO | — | — |
| (f) MES hard ceiling | — | no Σ² |
| (g) MES soft sigmoid | — | ibid. |
| (h) Direct $D_\ell$ χ² | — | — |

**Identifier**: $\rho_{\mathrm{CW,rad}} \ge 0.3$ across the posterior.
In the 15-model × 5-null heatmap (F49) N5 is the null family that
tests the shared-cause protection of the pipeline.

## 6. False-positive prediction

$$
\text{FPR}_{\text{N5}}(\text{FLRW\_tilt}) < 0.05.
$$

N5 is the null family most likely to *fail* the gate in a pipeline
that omits the shared-cause test. The BASS protection lives in
`htt.infer.shared_cause`; if the diagnostic is turned off, N5's FPR
can climb to the 0.10–0.15 range at the published amplitude.

## 7. Pitfalls

- **Non-negativity**: the N5 forward model *intentionally* allows
  negative common amplitudes at the latent level. Do not apply
  `max(A, 0)` to $A_{\rm common}$ in the generator — that masks the
  suppression mode.
- **Correlation inheritance**: $\rho_{\rm shared} = 0.5$ is the
  *latent* correlation. After per-survey noise is added, the observed
  $\rho_{\mathrm{CW,rad}}$ is typically $\sim 0.3$; don't confuse the
  two when comparing to F49 readouts.
- **CF4 double-check**: N5 should never inject into CF4. A non-zero
  CF4 residual in an N5 realisation is a generator bug, not a
  physical effect.

## 8. Provenance

| Field | Value |
|---|---|
| Forward-model source | `bass_py/htt/htt/nulls/clustering.py::SurveyAxisNull` |
| Amplitude prior | $\mathcal N(3\times 10^{-4},\,10^{-4})$ (BASS-operational) |
| Shared correlation | $\rho_{\rm shared} = 0.5$ |
| FPR datum | *pending* — ch08 §8.5 / F49 |
| Generated on | 2026-04-19 |
