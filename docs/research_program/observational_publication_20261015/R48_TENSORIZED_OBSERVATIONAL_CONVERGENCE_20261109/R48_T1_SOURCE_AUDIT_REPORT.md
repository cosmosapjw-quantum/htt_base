# R48-T1 source audit and bounded numerical results

Date: 2026-11-09 (Asia/Seoul)  
Repository: cosmosapjw-quantum/htt_base  
Branch/head audited: research/r48-tensorized-observational-convergence-20261109 / afb3ab9406cf13874e2e49e40d09f3b639b01c20  
Stage decision: **PASS_SCOPED for remote static source reconciliation and analytic/toy oracles; local implementation/runtime verification NOT_RUN.**

## 1. Completed work

- Reconciled the R41–R48 research ancestry and reused the R48-T0 metadata inventory (568 PR metadata records, 307 branch metadata records).
- Read and identity-bound the source modules for R42 forward response, five-variable push-forward, Cobaya likelihood/runner, R42 two-layer optimizer, R46 compression and exact SR closure.
- Recovered the September tensorized MES synthesis, WU-009 theorem dossier, WU-011 independent audit/repair contract, R7 readiness/handoff and August harness retrotrace.
- Wrote the physical 17D frame/event/epoch contract and a replay matrix C01–C16.
- Reproduced R46 target compression numerically and independently checked the R47 Bianchi-I small-amplitude sky-monopole coefficient.

## 2. Main source-level result

The R42 source does not support the earlier unqualified "Stage B repaired" narrative.

1. full_observable_x_bundle.py still has fixed Ellis–Baldwin factors 3.6625/3.3200, Gaia response scales 0.92/0.18, and an unused source_operators argument.
2. The Cobaya runner skips sampling when a cached chain exists, assigns t_run=553.24 and sampler=None, falls back to R-1=0.02, and derives ESS as 20% of rows if the GetDist method errors. It also sets verify_sha=False. The stored receipt has no sampler-executed flag or input/config/source hashes and reports ESS=53 with ess_passed=false. It cannot establish a fresh production chain.
3. The R42 null fallback draws seeded Gaussian samples but keeps default name MATCHED_NULL_PLANCK_MC100. A test itself creates a Gaussian pseudo-null and labels it MC100.
4. G_F default PHYSICAL_EXPANSION_TRANSPORT selects factor 1.0. Optional 1/(1+z) is not tied to a derived field-equation/optical transport kernel.
5. Nominal 17D physical chart is not a 17D free posterior: omega_i, A_i and DeltaOmega_k are fixed to zero in the R42 runner.
6. The joint five-probe likelihood sums five log-likelihood values without evidence for joint cross-probe covariance or conditional independence.
7. Bianchi transfer evaluation is unavailable until a validated native atlas reader or external transfer wrapper is bound.

These are implementation/provenance/statistical blockers, not reasons to discard mathematical R43–R47 work wholesale. They mean the numerical receipt and empirical discovery claims stay quarantined.

## 3. Cobaya-independent analysis performed

### 3.1 R46 target posterior compression

Using the same R46 source algorithm, 17D latent Gaussian model and score-row construction, with 40,000 prior-predictive draws:

- rank-2 target-aligned summary: expected target KL \(1.11\times10^{-16}\) nat, direct MMSE risk gap \(8.49\times10^{-31}\);
- dropping one target score direction: expected target KL \(0.68059\pm0.00261\) nat and MMSE risk gap \(1.14656\pm0.00810\);
- exact target compression still loses 6.62040 nats about the full latent posterior.

Status: **numerically checked, synthetic, target-chart conditional**. This supports target-specific compression, not empirical sufficiency of a physical HTT target map.

### 3.2 Ordered SR closure scale check

For
\[
\beta_{RM}=(1.1,-0.4,0.2)\times10^{-3},\quad
\beta_{MO}=(0.8,0.3,-0.5)\times10^{-3},
\]
the exact source-formula composition differs from vector addition by
\[
\|\Delta\beta\|=1.6044\times10^{-9},\qquad
\frac{\|\Delta\beta\|}{\|\beta_{RO}\|}=8.33\times10^{-7}.
\]
The exact zero-\(\beta_{RM}\) and zero-\(\beta_{MO}\) limits return the other boost exactly in the independent numerical oracle. The small correction at cosmological dipole speeds does not license the code to change frame semantics or to use vector addition as an exact closure.

Status: **numerically checked from documented formula; current repository integration NOT_RUN**.

### 3.3 Bianchi-I small-amplitude monopole

For the solver-free R47 temperature map
\[
T(\mathbf n)=\bigl[\mathbf n^T e^{-2B}\mathbf n\bigr]^{-1/2},
\qquad
B=\epsilon\,\mathrm{diag}(0.7,-0.2,-0.5),
\]
a 500-point Gauss–Legendre polar grid times 1000 uniform azimuths gives
\[
\langle T\rangle=1-\frac{2}{15}\operatorname{tr}(B^2)+O(\epsilon^3).
\]
Here \(-2\operatorname{tr}(B^2)/(15\epsilon^2)=-0.104\). Numerically inferred coefficients were -0.10397237, -0.10398643 and -0.10399327 for \(\epsilon=0.01,0.005,0.0025\), converging to -0.104.

Status: **independent numerical quadrature check of small-B expansion**. It does not validate Bianchi evolution, visibility/recombination, polarization, masked Planck response or Bianchi-family inference.

## 4. Historical reuse and separation

- WU-009 P16/P18/P20: exact local boost pullback, ideal Bianchi-I positive-quadratic temperature inverse, direct-temperature likelihood. Reuse only under stated blackbody/transfer assumptions.
- WU-010/011: local-observer Lorentz response and processed cut-sky operator. The continuum wide-mask identity-transfer result that high-source ell=7…12 spans retained ell=2…5 is an operator-identifiability warning, not a finite-HEALPix or Planck empirical result.
- WU-011 Task 5A/5B: metric whitening, physical monopole vs a00, ell=6 block classification, complete finite differences and source-coordinate typing remain replay obligations.
- R7 source-image handoff: proxy/source-image geometry is not observational likelihood or posterior.
- R43–R46: identifiability, evidence sufficiency, finite-model information loss and target posterior compression remain reusable as methods, conditional on actual physical target maps and data-source identities.
- R47: Bianchi-I geodesic temperature map is a separate intrinsic-anisotropy operator. It must not be merged conceptually with WU-010/011 observer boost or called global matter-frame tilt.

## 5. Next decision and stop conditions

R48-T1 is complete at remote static-audit level. Before R48-T2, local Codex must verify exact branch head and run bounded tests listed in COBAYA_FREE_ANALYSIS_PATHS.md. Next scientific task is R48-T2 only: implement the Bianchi-I low-ell temperature-response oracle with exact map, parity/rotation/quadrature checks and explicit nuisance separation from local-observer boost. No Cobaya production, observed anomaly claim or Bianchi V/VII_h family claim is authorized.

## 6. Explicitly NOT_RUN

- Local checkout git status, import/compile/pytest on current head.
- Real R42 two-layer benchmark against admitted, hash-verified source data.
- Cobaya sampling, posterior chains, SBC/PPC, matched-null/FPR calibration.
- Native or external Bianchi transfer execution.
- Native subagents / independent human review.