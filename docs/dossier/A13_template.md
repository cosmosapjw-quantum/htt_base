# Dossier template — `<Model name>`

**Appendix**: A13
**Version**: 2026-04-19 (DOS-A13 landing; posterior fields remain placeholder until Phase H)
**Upstream**: BASS_PY_HTT_TSC_RESEARCH_PLAN.md §11.10.1

> This template is the single standard format for every model dossier
> (15 total, ~130 L each, 2 pages). Every model-specific file under
> `docs/dossier/A13_<NN>_<modelname>.md` must keep this section order
> and field set so that cross-model tables can be generated mechanically.

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | `A13-<NN>` |
| Model name            | `<Model name>` |
| Structural class      | FLRW / Bianchi (I, II, V, VI_0, VI_h, VII_0, VII_h, VIII, IX) / tilted-FLRW |
| Dimensionality        | `<D_free>` free parameters |
| Reference DOIs / arXiv | `<arXiv:YYMM.NNNNN, ...>` |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Cosmological tilt amplitude | β        | half-Gaussian | σ = 0.002 |
| Shear amplitude             | Σ²       | U[0, 1e-6] |   |
| Vorticity amplitude         | W²       | U[0, 1e-8] |   |
| Four-acceleration           | A²       | U[0, 1e-6] |   |
| Preferred direction (l, b)  | (l, b)   | uniform-on-S² | — |
| ... | | | |

> **Matched-complexity discipline** (§11.10.1 / A15): every dossier must
> declare the same *number* of free parameters as its direct competitor
> in the 15-model ladder, filled with δ-priors where no physical free
> parameter exists. Appendix A15 gives the enforcement algorithm.

## 3. Kinematic signature

Predicted time trajectories of the Ellis-Bruni frame scalars:

- Σ²(η)  — `<analytic form or reference>`
- W²(η)  — `<analytic form>`
- β(η)   — `<analytic form>`
- Θ(η), H(η), w_eff(η) consistency — `<note>`

## 4. Distinguishing channels

Which of the BASS channels (b, c, d, e, f, g, h; see A28) contribute
evidence under this model? Expected `Δ ln B` (per channel, fiducial
Σ² = 10⁻⁸):

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | TT anomalies (D2, D3) | — |
| (c) | TE / low-ℓ cross | — |
| (d) | Bulk flow / velocity monopole | — |
| (e) | BAO / sound-horizon hooks | — |
| (f) | MES hard ceiling | — |
| (g) | MES soft sigmoid (inert by default) | — |
| (h) | Direct D_ℓ χ² | — |

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_model | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| β        | *pending* | — | — |
| Σ²       | *pending* | — | — |
| (l, b)   | *pending* | — | — |

> Posterior fields land in Phase H. DOS-A13 only fixes the format.

## 7. Pitfalls / identifiability notes

- `<degeneracy pair 1>`: e.g. β vs (l, b) along line of sight
- `<degeneracy pair 2>`: Σ² vs A² at fixed Θ
- `<prior-driven tail>`: posterior pushes up against prior edge in …

## 8. Reference figures

- `F<NN>` — posterior corner plot
- `F<NN>` — kinematic signature overlay
- `F<NN>` — channel-by-channel evidence stack

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `<run_NN>` |
| Dynesty config hash | `<sha>` |
| Data bundle hash | `<sha>` |
| Generated on | `<YYYY-MM-DD>` |
