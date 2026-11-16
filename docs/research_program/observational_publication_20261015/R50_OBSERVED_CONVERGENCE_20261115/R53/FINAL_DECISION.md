# R53 final decision

**Decision: no methods-plus-discovery paper. Scope reduced to one bounded note: an observational result with negative and diagnostic findings.** Uncertainties are kept as computed.

## Basis

1. **Method advantage.** The signed tensor carrier ties the exact likelihood and the optimal score; it does not beat them (Table 3). It beats the scalar and power-only summaries only for signed or multi-direction targets, and those losses are standard. This is not a novelty claim.
2. **What actually changes the inference** is the covariance law and the epoch-correct response:
   - The plug-in Gaussian with a simulation covariance fails held-out calibration on PR3 low-ℓ data. The finite-MC law calibrates the data law, but parameter intervals still need the known covariance-noise inflation (coverage 0.929 → 0.954 at N=200; LOO factor 1.25 vs analytic 1.27; Hartlap et al. 2007, Dodelson & Schneider 2013, Percival et al. 2022).
   - The R49 joint posterior used σ/H₀ as line-of-sight integrated shear. With the correct history operator, CMB, Gaia and DESI constrain quantities from different epochs.
   - Both points are real corrections, but they apply known statistics (Sellentin & Heavens 2016) and known physics.
3. **Physical results survive only as bounds or inconsistencies:**
   - SMICA T shows no integrated shear. The bound is weaker than published Bianchi constraints that use polarization.
   - No homogeneous global tilt is supported once bulk-flow cosmic variance is included.
   - The count-dipole frame and the CMB+CF4 frame differ under the working law (p = 8×10⁻⁴), but not robustly: with bulk-flow cosmic variance and the CF4 misfit the tail rises to 0.06. It restates the known count-dipole anomaly in a frame-consistent decomposition and is not a finding.
   - The Gaia E2 residual is not cosmological shear.
   - A and ω are not identified.
4. **Family identification:** only FLRW/I are evaluable with source-bound transfer. No Bianchi family identification is possible (see AGENTS.md boundary 7).

## Publishable bounded content (manuscript-ready)

- Tables 1–4 in `MANUSCRIPT_CLAIM_TABLE.md`; Figures F1 (held-out PIT), F2 (integrated shear), F3 (frame offset by probe subset), F4 (CF4 window dipoles vs joint model), F5 (interval coverage by method).
- Proposed title: *A frame-consistent low-multipole test of Bianchi-I shear and observer/matter/radiation frames with finite-simulation covariance calibration*.
- The claims are limited to rows marked derived or checked. Every row marked unresolved stays out of the abstract.

## Conditions that would reopen a stronger paper

- Commander-matched FFP10 MC: a primary-pipeline result.
- A source-bound polarization and finite-curvature transfer: family comparison beyond type I.
- Count mocks with selection and clustering, giving a same-estimator null for β_MO: a calibrated Π for the dipole anomaly.
- An empirical CF4 covariance and a calibration model: identification of A.

No further audit-only node is opened. The R50–R53 DAG is complete.
