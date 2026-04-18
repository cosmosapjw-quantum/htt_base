# A14 · N3 — Clustering-dipole (Bashir-type) null family

**Appendix**: A14 (§11.10.2 of `BASS_PY_HTT_TSC_RESEARCH_PLAN.md`)
**Version**: 2026-04-19 (DOS-A14 landing).
**Code anchor**: `bass_py/htt/htt/nulls/clustering.py` (class
`ClusteringDipoleNull`).
**Primary references**:
- Bashir et al., *SBI for the WISE CatWISE dipole*, 2025 (N3 amplitude
  posterior source);
- Dalang & Bonvin, *Anisotropies of the cosmic rest frame*, PRD 2021
  (theoretical clustering dipole framework).

---

## 1. Physical origin

Any finite cosmological survey samples local large-scale structure
(LSS). The matter *over-density* in nearby super-clusters (Shapley,
Great Attractor, Perseus-Pisces) produces a genuine *clustering
dipole* in number counts even absent any bulk flow: more sources fall
along over-dense lines of sight than along under-dense ones. This
effect scales with the survey's selection function multiplied by the
LSS $\delta(\hat{\mathbf n})$ field, and contributes *additively* to
whatever kinematic dipole is present.

For shallow surveys (CatWISE $z_{\rm med} \sim 1$, Secrest-Radio
$z_{\rm med} \sim 1$) the clustering dipole is non-negligible; it is
the mechanism isolated by Bashir+2025 as a candidate for the observed
CatWISE excess over the kinematic prediction.

## 2. Forward model

Let $A_{\rm clust}$ denote the amplitude of the clustering-induced
dipole. The per-survey contributions are

$$
\epsilon_1^{\text{N3}}_{\mathrm{CW}} \sim
    \mathcal N\!\big(A_{\rm clust},\, \sigma_{\mathrm{stat,CW}}\big),
\qquad
\epsilon_1^{\text{N3}}_{\mathrm{radio}} \sim
    \mathcal N\!\big(0.7\, A_{\rm clust},\, \sigma_{\mathrm{stat,rad}}\big),
\qquad
b^{\text{N3}}_{\mathrm{CF4}} \sim
    \mathcal N\!\big(0.3\, A_{\rm clust},\, \sigma_{\mathrm{CF4}}\big),
$$

all clipped to non-negative. The $(1, 0.7, 0.3)$ weights reflect the
selection-function-weighted overlap of CatWISE, Radio, and CF4 with
the local LSS shell (CF4 probes much nearer structure and is only
partially correlated). The cross-survey correlation is

$$
\rho^{\text{N3}}_{\mathrm{CW,radio}} = 0.2,
$$

moderately above the statistical-only nominal 0.1 — a shared-cause
intermediate fingerprint.

## 3. Amplitude prior

From Bashir+2025 §5.2 (their 68% credible region for the clustering
amplitude):

$$
A_{\rm clust} \sim \mathcal N(\mu = 4 \times 10^{-4},\,
                              \sigma = 1.5 \times 10^{-4}),
\qquad A_{\rm clust} \ge 0.
$$

This is encoded as `ClusteringDipoleNull(A_clust_mean=4e-4,
A_clust_std=1.5e-4)`. The width is larger than N1 because the
Bashir+ posterior for clustering is broader (shared with galaxy bias
nuisance parameters), and the tail allows for post-Shapley
over-clustering realisations.

Scale check: $A_{\rm clust} \sim 4 \times 10^{-4}$ sits between the
pure-kinematic CMB prediction ($1.23 \times 10^{-3}$) and the
scanning-law N1 ($3 \times 10^{-4}$). If both N1 and N3 were
simultaneously present and fully additive, their joint expected
contribution $\langle A_{\rm scan} + A_{\rm clust}\rangle \approx 7
\times 10^{-4}$ is of the same order as the kinematic prediction and
dilutes the $\Lambda$CDM tension.

## 4. Sky pattern

Aligned with the *local gravitational quadrupole* — in galactic
coordinates the clustering-dipole direction is close to Shapley
$(l,b) \approx (311°, 30°)$, offset $\approx 77°$ from the CatWISE
observation and $\approx 96°$ from the CMB dipole. This is far enough
from the observed CatWISE direction that a direction-resolved N3
injection will *pull* the reconstructed dipole direction; N3 is
therefore most clearly exposed by §7.7 (dipole direction medians +
credible cones).

## 5. Statistical signature and distinguishing channels

| Channel | N3 contribution | Why |
|---|---|---|
| (b) TT anomalies | *weak* | LSS clustering has no direct CMB imprint |
| (c) TE / low-ℓ cross | *weak* | ibid. |
| (d) Bulk flow / velocity monopole | Leading, multi-survey | Shared across CW/Radio/CF4 |
| (e) BAO | *weak* | selection-weighted LSS correlates only at 100–200 Mpc |
| (f) MES hard ceiling | — | no Σ² footprint |
| (g) MES soft sigmoid | — | ibid. |
| (h) Direct $D_\ell$ χ² | *weak* | LSS contaminates the low-ℓ power spectrum |

The diagnostic column (d) is where N3 lives; crucially N3 is the only
null family that imprints a *bulk-flow*-like signal in CF4 (the $0.3
A_{\rm clust}$ component). That makes it the prime failure mode for
the ch07 §7.17 CF4++ tension claim.

## 6. False-positive prediction

Expected at:

$$
\text{FPR}_{\text{N3}}(\text{FLRW\_tilt}) < 0.05 \qquad
\text{(BASS gate, §2.3.28).}
$$

N3 is the *highest-amplitude* null family and the one most at risk of
breaching the 0.05 ceiling — especially once the CF4 channel enters.
Mitigating this is the main scientific motivation for matching the
direction-posterior radius to the Shapley-direction offset (§7.7
credible cones).

## 7. Pitfalls

- **Galaxy bias degeneracy**: Bashir+2025's $A_{\rm clust}$ posterior
  marginalises over galaxy bias $b_g$. Re-deriving N3 with a narrower
  $b_g$ prior can shift $\mu$ by a factor of $\sim 2$; cite the Bashir
  prior *as-is* rather than rescaling.
- **CF4 double-counting**: if the CF4++ analysis already subtracts the
  local LSS model, N3 must *not* be re-injected into $b_{\rm CF4}$;
  track the CF4 subtraction state in the data-bundle hash.
- **Overlap with N5 (survey axis)**: both share CatWISE/Radio; the
  distinguisher is the CF4 footprint — N5 does not touch CF4.

## 8. Provenance

| Field | Value |
|---|---|
| Forward-model source | `bass_py/htt/htt/nulls/clustering.py::ClusteringDipoleNull` |
| Amplitude prior | $\mathcal N(4\times 10^{-4},\,1.5\times 10^{-4})$ (Bashir+2025) |
| CF4 coupling weight | 0.3 (fiducial; Shapley-distance weighted) |
| FPR datum | *pending* — ch08 §8.5 / F49 |
| Generated on | 2026-04-19 |
