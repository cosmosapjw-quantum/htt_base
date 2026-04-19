# AUDIT_PHASE_FB_META11_2026-04-20

**Banner**: META pre-flight — FB-11 inference driver / multi-type Bayes
factor / extended-bundle skeletons + 3-channel verification
**Determinism pin**: throughout FB-11,
`run_posterior(..., seed=42)` must be documented as a same-machine
byte-reproducibility contract for `samples`, `log_prob`, and
`diagnostics`, even while the planted bodies still raise
`NotImplementedError`.
**External-driver pin**: `emcee` stays confined to
`bass/inference/drivers/`; production modules do not import the third-
party sampler directly, and `dynesty` remains a reference-only
cross-check path outside the CI default route.

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md`,
  `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`,
  `docs/lowell_bianchi/extended_coverage/SCOPE_DECISIONS.md`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/bass/observer/`,
  `htt/bass/species/massive_neutrino/`,
  and `htt/bass/likelihood/`.
- Reading summaries:
  - `PROJECT_MEMORY_EXPLICIT.md`: additive commits only, no silent
    fallbacks, and every phase boundary needs an explicit audit trail.
  - `FB11_INFERENCE_DRIVER_SDD.md`: FB-11 ships only priors, sampler
    contract, Bayes-factor contract, convergence diagnostics, a
    skip-marked synthetic-injection harness, an 11-type summary seam,
    and docs/gallery placeholders; determinism at `seed=42` is
    load-bearing.
  - `EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`: FB-11 is downstream of
    FB-7 + FB-8 + FB-9, inherits the bundle-wide byte-anchor rule, and
    is the final in-scope extended-bundle phase.
  - `SCOPE_DECISIONS.md`: no survey / lensing / second-order-tilt scope
    is reopened here; FB-11 stays limited to inference scaffolding.
  - `SELF_AUDIT_AUTOMATION.md`: FB-11 writes to
    `DEVELOPMENT_LOG_FB8_ONWARD.md`, rotates
    `NEXT_SESSION_PROMPT.md`, and must mark no-op gallery outcomes
    explicitly.
  - `AUDIT_PROMPT.md`: restore contract first, keep the
    physics/code/numerics split visible, and record the smallest honest
    patch.
  - `htt/bass/likelihood/`: the FB-7 cosmological-frame likelihood
    skeletons exist on disk and remain the upstream inference seam.
  - `htt/bass/observer/`: the FB-8 observer-frame boost / kernel /
    discriminator / wrapper scaffolds exist on disk and keep
    cosmological tilt distinct from observer boost.
  - `htt/bass/species/massive_neutrino/`: the FB-9 massive-neutrino
    package exists on disk and preserves the `Sigma_mnu = 0` LB-1
    byte-identity anchor.
- Grep-check completed for prerequisite symbols:
  `CosmologicalFrameLikelihood`, `build_htt_decomposition`,
  `ObserverFrameLikelihood`, `validate_planck2018_flrw_limit_match`,
  `ObserverBoost`, `aberration_kernel`, `apply_observer_boost`,
  `observed_alm_mixing`, `compose_tilts`, `DiscriminatorResult`,
  `likelihood_ratio`, `phase_space_grid`, `MassiveNeutrinoBackground`,
  `rho_rest`, `p_rest`, `dot_rho`, and `temperature`.
- Regression gate executed on the exact FB-11 META anchor:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 66 skipped`.
- Source correction recorded up front for FB-11.6: prompt-supplied
  `arXiv:0706.2075` is the Pontzen-Challinor Bianchi `VII_h`
  polarization paper, not a Bianchi-IX evidence-sign result, so the
  audit must keep that locator mismatch explicit rather than inventing a
  Bianchi-IX claim.

## §FB-11.1

Pending pre-flight scaffold for `bass.inference.priors`.

## §FB-11.2

Pending pre-flight scaffold for the emcee driver and the determinism
contract.

## §FB-11.3

Pending pre-flight scaffold for `bayes_factor`.

## §FB-11.4

Pending pre-flight scaffold for convergence diagnostics.

## §FB-11.5

Pending pre-flight scaffold for the synthetic-injection coverage
harness.

## §FB-11.6

Pending pre-flight scaffold for the 11-type summary seam.

## §FB-11.7

Pending pre-flight scaffold for docs + gallery placeholders.
