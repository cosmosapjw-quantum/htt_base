# Dossier — FLRW + cosmological tilt (main candidate)

**Appendix**: A13-01
**Status**: example / template calibration; primary competitor to A13-00
FLRW. Posterior fields placeholder pending Phase H (W15-02 dynesty run).
**Upstream**: BASS_PY_HTT_TSC_RESEARCH_PLAN.md §11.10.1 / DOS-A13

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-01 |
| Model name            | FLRW + cosmological tilt (β, l, b) |
| Structural class      | tilted-FLRW (peculiar velocity field, not Bianchi) |
| Dimensionality        | 3 free anisotropy d.o.f. (β, l, b) |
| Reference DOIs / arXiv | Maartens-Ellis 1995 (PRD 51, 5942); Pastén 2026 (arXiv:2603.20963) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Tilt amplitude | β | half-Gaussian | σ = 2 × 10⁻³ (matches Commander D_2 allowance) |
| Tilt l_deg | ℓ | uniform | [0°, 360°) |
| Tilt b_deg | b | uniform-on-S² (∝ cos b) | [−90°, +90°] |
| Σ²         | — | δ-prior at 0 |   |
| W²         | — | δ-prior at 0 |   |
| A²         | — | δ-prior at 0 |   |

Matched-complexity note: the three anisotropy d.o.f. (β, l, b) place this
dossier at `D_anisotropy = 3`; FLRW (A13-00) carries three δ-priors to
match, enforced by A15.

## 3. Kinematic signature

- Σ²(η) ≡ 0 — no shear
- W²(η) ≡ 0 — no vorticity
- β(η) — treated as z-independent amplitude in S1 baseline; S3 adds
  `W_R` window dynamics (upstream W12-01).

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` (fiducial β = 10⁻³) |
|---|---|---|
| (b) | D_2 / D_3 residual alignment | *pending* |
| (c) | TE dipole response | *pending* |
| (d) | Bulk flow correlation | *pending* |
| (e) | — (no shear) | ~0 |
| (f) | MES hard ceiling | marginal (|u̇|/Θ ≤ 2 ε_2) |
| (g) | MES soft sigmoid (inert) | 0 |
| (h) | D_ℓ χ² direct | *pending* |

W14-01 (3-signature separator) expects tilt β to show in both TT and EE
(unlike local W_R v_loc, which is TT-only).

## 5. Scenario-dependent Bayes factors

| Scenario | Description | ln Z_tilt | ln B vs. FLRW |
|---|---|---|---|
| S1 | Planck 2018 Commander low-ℓ TT | *pending* | *pending* |
| S2 | Planck + bulk flow              | *pending* | *pending* |
| S3 | full stack (+ W_R window + BAO) | *pending* | *pending* |

Target: Phase H should report ln B_tilt-vs-FLRW with F_Bayes = 0.093 ± 0.025
injection. At ln B ~ +26.4 (Route B anchor) the posterior support for a
nonzero tilt is "decisive" under Jeffreys' scale.

## 6. Posterior summary

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| β         | *pending* | — | — |
| l         | *pending* | — | — |
| b         | *pending* | — | — |

## 7. Pitfalls / identifiability notes

- **β ↔ (l, b) confusion**: small-β tilts with poorly constrained direction
  can mimic a large-β tilt along a near-orthogonal line of sight. Requires
  the selection-aware directional likelihood (COMMON-D) to break this.
- **ZoA contamination**: a diagnostic axis (`production_allowed=False`)
  must *never* feed the tilt posterior (HTT-P0-AJ gate).
- **Prior-edge behaviour**: when posterior pushes β against the half-Gaussian
  0-boundary, the posterior predictive p-value (A18) is the safer
  diagnostic than the marginal credible interval.

## 8. Reference figures

- F03 — (β, l, b) corner
- F04 — direction posterior healpix map
- F05 — TT+EE template decomposition (W14-01 output)

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | *pending Phase H* |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
