# R47 — Solver-free low-ell morphology likelihood and six-loop convergence plan

**Date:** 2026-11-09 (Asia/Seoul)  
**Repository:** `cosmosapjw-quantum/htt_base`  
**Branch:** `research/r47-solverfree-morphology-likelihood-20261109`  
**Parent:** R46 commit `66b4bce6151a5fc19f317b02221b724223354fd6`  
**Claim ceiling at creation:** C0 / methods-design / solver-free temperature-template candidate  
**Execution boundary:** GitHub source audit, prior-result review, literature review, solver-free model derivation/design, and local-agent handoff. No raw observational bytes were downloaded or locally executed in this R47 authoring turn. No Cobaya chain was run here.

## 1. Decision

The sentence “tensorized morphology alone cannot attribute a sky to Bianchi geometry” is **conditionally correct**, but it must not be read as a theorem that tensor morphology is useless for Bianchi inference.

The precise boundary is:

1. A complete (a_{ell m}leftrightarrowmathrm{STF}_ell) transform preserves the retained band-limited map. A complete separating invariant packet can preserve its (SO(3)) orbit on its declared regular domain.
2. A predeclared Bianchi forward map can map physical parameters or integrated geometric state to a predicted mean and/or covariance in this tensor carrier. The resulting likelihood can conditionally prefer, constrain or reject that Bianchi model against a declared competitor set.
3. A low-ell morphology match does not uniquely identify the generating geometry unless the candidate model-to-data maps are globally separating after rotations, masks, transfer functions, nuisance projection and stochastic sky covariance. A shear-compatible tensor is not a Bianchi-family label.
4. The target of a solver-free Bianchi-I temperature calculation proposed here is the **integrated emission-to-observer anisotropy tensor** (or its exact nonlinear positive-definite metric carrier), not automatically the present-day (sigma_{ab}/H).

The R47 execution route therefore adds a solver-free, geodesic temperature-template likelihood as a bounded physical model. It does not replace a self-consistent polarized Bianchi transfer model and does not authorize a Bianchi V/VIIh family claim.

## 2. Findings from the current and inherited project state

### 2.1 GitHub state

The live project branch used for continuation is the stacked R46 head, not `main`:

| Item | State on 2026-11-09 |
|---|---|
| Main snapshot inspected | `f1007dd3e41c07eccd64024dd6b44fb5a40a3612` |
| R42 PR #566 | OPEN / DRAFT; stacked on R41 |
| R43 PR #567 | OPEN / DRAFT; synthetic theory/mocks only |
| R44 PR #568 | OPEN / DRAFT; Gaussian sufficiency/design mocks only |
| R45 PR #569 | OPEN / DRAFT; finite-model posterior information-loss mocks |
| R46 PR #570 | OPEN / DRAFT; target-specific posterior compression mocks |
| R47 branch parent | `66b4bce6151a5fc19f317b02221b724223354fd6` |

These PRs are not evidence of changes merged into main. R42–R46 must be reviewed as stacked snapshots, preserving their individual parent/head identities.

### 2.2 Reconciliation findings

- The R42 Planck observed carrier in `SOURCE_LOCK_MANIFEST.json` is `observed_lowell_EB.npz`, declared as 743 bytes and limited to (E/B), (ell=2,3,4). This is not a raw-map or full-(a_{ell m}^{T,E,B}) likelihood input. Its hashes, source bytes, and covariance provenance must be rechecked locally.
- The R42 Cobaya receipt reports (R-1=0.02), (hat R=1.02), but ESS (=53) and `ess_passed=false). The configuration also records `verify_sha: false`. This is a non-converged/underpowered pilot, not a production posterior.
- R42 synthetic calibration records mark all listed SBC scenarios uncalibrated. R42 predictive/evidence numbers remain quarantined pending a full source-bound replay.
- The R42 `full_observable_x_bundle.py` still contains default count-response and Gaia scale constants (including 3.6625, 3.3200, 0.92 and 0.18) and a simplified CMB carrier construction. Their presence contradicts the claim that all hardcoded response coefficients have been eliminated. They must be replaced by source-integrated operators or explicitly marked unavailable/proxy.
- The R42 `BianchiTransferAdapter.evaluate_lowell_transfer` currently raises `NotImplementedError` for both native-atlas reading and external transfer execution. Its provenance firewall is useful; it is not a functioning transfer implementation.
- R42’s two-layer benchmark architecture is retained: compare physical **generative models** separately from **inference/readout methods**. The five outputs (T=(x,Q,Pi,F,G_F)) remain one posterior/compatibility push-forward, never five independent likelihood terms.
- R43–R46 provide useful conditional information-theory results and synthetic controls. They do not constitute observed-data or Bianchi-transfer evidence.

### 2.3 Prior internal theory retained

The 2026-10-26 `HTT_FIVE_THEORY_LOOPS.pdf` remains a key internal source:

- Loop A: an exact positive radiative-shear response operator and its conditional finite-error inversion; radiation stress moments must not be equated with a temperature (Q/O) truncation.
- Loop B: observer boost and intrinsic radiation dipole/quadruple closure; an observed dipole alone does not separate the two.
- Loop C: local optical and proper-motion response; E2/B1 sectors, source congruence, and reference-frame spin remain explicit.
- Loop D: Bianchi structure constants, Jacobi, spatial Ricci, and Hamiltonian/momentum constraints; an exact Bianchi II/VII(_0) matched example shows same scalar curvature and local kinematics can coexist with different STF spatial Ricci.
- Loop E: directional distance jets and a vacuum Kasner Bianchi-I example without an evolution solver. It explicitly derives how the photon direction drifts along the ray and how a finite-redshift directional Hubble coefficient differs from the vertex coefficient.

This report’s internal review was `PASS_SCOPED_AFTER_TARGETED_REPAIRS`, but it did not establish empirical likelihoods, native Bianchi transfer, or a family identification.

## 3. Solver-free candidate selected for construction

The first candidate is a **Bianchi-I homogeneous-geodesic temperature map**. Bianchi I has spatial translation Killing fields, so covariant spatial photon momenta are conserved. Given a positive-definite spatial metric at emission and at observation, the emission-to-observer frequency ratio can be calculated algebraically without integrating a photon Boltzmann hierarchy.

With (g_{ij}(t_0)=delta_{ij}), a metric representation
[
g_{ij}(t)=a^2(t)[e^{2B(t)}]_{ij},qquad
B(t_0)=0,quad operatorname{tr}B=0,
]
and observer-frame direction (hat n), an isotropic Planck last-scattering surface plus collisionless propagation gives
[
rac{T_0(hat n)}{ar T_0}
=
left[hat n^T e^{-2B_*}hat night]^{-1/2}.
]
For a fixed commuting principal-axis history with (dot B=sigma),
[
B_*=-int_{t_*}^{t_0}sigma(t),dt.
]
The exact map therefore constrains an integrated metric-anisotropy carrier. It does not identify the present shear without a dynamical history relation. See `METHODS_NO_BOLTZMANN.md` for assumptions, limitations, and the full likelihood contract.

## 4. Research product and novelty hypothesis

The potentially publishable contribution is **not** “tensorizing (a_{ell m})” or “using BipoSH” in isolation. Those have substantial prior art. The novelty hypothesis to test is:

> A source-bound, frame-typed tensor posterior-push-forward (T=(x,Q,Pi,F,G_F)), connected to an explicitly derived solver-free geometric temperature response and jointly benchmarked against full harmonic, BipoSH, multipole-vector/power-tensor, local-boost, phenomenological-anisotropy, and covariant-cosmography competitors, can preserve or improve calibrated inference on predeclared physical tensor targets while exposing observationally equivalent geometric states instead of assigning spurious family labels.

This is only a **candidate**. R44–R46 already teach that information preservation is target-specific. The project must demonstrate that the actual HTT readout preserves posterior information for the scientific estimands under the real likelihood, and improves calibration/predictive utility over established readouts. A new representation alone is not scientific significance.

## 5. Short-term DAG and turn boundary

The next work is intentionally split into distinct turns. Do not execute every future node during one turn.

1. **R47-T0 (this checkpoint):** source/status audit, literature synthesis, solver-free construction choice, branch and handoff docs. Complete when the branch and draft PR are readback-verified.
2. **R47-T1:** relevance-indexed PR/legacy audit. Reconcile #565–#570 and older low-ell, FFP10/NPIPE, Bianchi/MES, EGS3, optical and five-variable source records. Do not reread unrelated PR diffs.
3. **R47-T2:** derive and adversarially check the Bianchi-I geodesic temperature map, conventions, exact (a_{ell m}) projection and limiting cases. Produce a theory seal; no observed-data claim.
4. **R47-T3:** implement the map-level low-ell likelihood adapter and tests on synthetic/analytic fixtures. Keep deterministic mean, stochastic covariance, boost, mask/beam, foreground, and noise pieces separately typed.
5. **R47-T4:** local agent downloads and validates the required Planck PR4/NPIPE inputs plus a separately labelled matched FFP10 robustness ensemble. Raw data stay outside Git.
6. **R47-T5:** run the observed CMB likelihood and Cobaya posterior with reproducible chains, convergence and SBC/PPC. If adequate matched simulations or transfer calibration are missing, report the conditional likelihood and the blocked empirical calibration separately.
7. **R47-T6:** execute the six independent non-CMB and cross-probe loops: dipole anomaly; 17-component kinematics; Bianchi/anisotropy compatibility; directional (H(z,hat n)); local boost vs global tilt; source-conditioned tensor readout.
8. **R47-T7:** join only admitted products using their shared state and full covariance; run adversarial matched mocks and held-out predictive tests; decide paper track and claim tier.

The machine-readable dependency and acceptance contracts are in `SHORT_TERM_DAG.json`.

## 6. Data policy

Use the official Planck Legacy Archive and the NPIPE/PR4 data portal as the primary acquisition routes. Minimum P0 inputs are frequency maps, suitable splits, masks, effective beams/transfer functions, noise products, and matched end-to-end simulations or documented alternatives. Component-separated products are robustness views, not independent skies. Do not mix PR3/FFP10 simulations with PR4/NPIPE maps as if they were matched.

Other P0 products are the full Pantheon+ table/covariance, Quaia catalogues/randoms/selection, NVSS catalogue/coverage, Gaia source-level astrometry/covariance/CRF calibration, and (only after requalification) Cosmicflows-4 original distance data. All inputs require local byte hashes and row/mask/covariance identities before sampling. The exact sources and staged downloads are in `DATA_INTAKE_MANIFEST.json`.

## 7. Claim firewall

- Current status: empirical discovery paper **HOLD**.
- Methods paper: **conditional candidate**, pending replay of production implementation, real data, source-matched calibration and adversarial comparisons.
- Bianchi-I: at most **geodesic-template compatibility / transfer-conditional** until the full physical and statistical conditions are met.
- Bianchi V/VIIh and broader family classification: **unresolved** unless validated transfer or curvature/derivative observables distinguish them.
- Local boost vs global tilt: **not identified** by a single dipole; requires independent frame/observer response and depth-dependent products.
- Vorticity from Gaia (B_1): **unavailable** until the ICRF spin degeneracy is anchored externally.
- R42’s numerical shear limits, M1-vs-M9 predictive differences and other reported posterior numbers are **quarantined** until the source bytes, likelihood implementation, and chains are replayed.

## 8. Actual status of this R47 turn

- Repository source: inspected through GitHub only.
- R42–R46 PR metadata/bodies: inspected; full line-by-line audit of every historical PR has **not** been completed.
- External primary literature: surveyed and cited in the companion method note.
- Solver-free Bianchi-I temperature map: **derived at design level**, not yet independently verified by CAS/code.
- NPIPE data: source portals and dataset families identified; no raw bytes downloaded in this turn.
- Cobaya: no production chain executed in this turn.
- Native subagents: **NOT_RUN**; no native delegation tools were available in this host inventory. A local coding agent is given the actual handoff prompt instead.
- GitHub mutation: isolated R47 branch created from R46; docs and draft PR remain the only authorized mutations.

## References

- Saadeh et al. (2016), *How isotropic is the Universe?*, PRL 117, 131302, https://doi.org/10.1103/PhysRevLett.117.131302.
- Pontzen & Challinor (2007), *Bianchi model CMB polarization and its implications for CMB anomalies*, MNRAS 380, 1387–1398, https://doi.org/10.1111/j.1365-2966.2007.12221.x.
- Saadeh et al. (2016), *A framework for testing isotropy with the CMB*, MNRAS 462, 1802, https://academic.oup.com/mnras/article/462/2/1802/2589609.
- Vicente, Pereira & Pitrou (2025), *CMB line-of-sight integrators for nearly-isotropic cosmological models*, arXiv:2506.07786, https://arxiv.org/abs/2506.07786.
- Gerbino et al. (2020), *Likelihood methods for CMB experiments*, arXiv:1909.09375, https://arxiv.org/abs/1909.09375.
- Planck Collaboration (2016), *Isotropy and statistics of the CMB*, https://arxiv.org/abs/1506.07135.
- Nadolny et al. (2021), *A new way to test the Cosmological Principle: measuring our peculiar velocity and the large-scale anisotropy independently*, https://arxiv.org/abs/2106.05284.
- HTT internal theory synthesis, 2026-10-26, `HTT_FIVE_THEORY_LOOPS.pdf` in the project library.
