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

### §FB-11.1 — `bass.inference.priors` skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md §2`
names `Prior`, `prior_rapidity`, `prior_direction`,
`prior_Sigma_mnu`, `prior_observer_boost`, and
`prior_structure_constants` as the canonical FB-11.1 surfaces; verified
`docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §5`
pins FB-11.1 as a standalone priors module rather than a driver-local
helper; verified `docs/lowell_bianchi/00_conventions.md §13` keeps
observer boost and cosmological tilt type-distinct, so the shared
direction prior must not collapse ownership; verified the new
`bass.inference` package exports only the priors surface at this stage;
verified the frozen `Prior` dataclass matches the SDD field contract;
verified the new skipped harness test locks the public signatures
without fabricating any numerical prior.
**Channel B**: 4 source checks / 3 verified / 1 corrected. Evidence:
Planck 2018 VI is verified on arXiv as the canonical cosmological-
parameter paper and its PDF exposes `Table 2` as the baseline sampled-
parameter table; the same paper's abstract confirms the Planck-era
`sum m_nu < 0.12 eV` scale for neutrino-mass reporting. Kosowsky &
Kahniashvili 2011 (`arXiv:1007.4539`) verify the observer-motion signal
as a part-in-a-thousand effect tied to the CMB dipole. Corrected: the
local SDD's `Sigma_mnu` half-Gaussian shape is not directly specified by
Planck `Table 2`, so the skeleton docstring records Planck as a
parameter-range anchor while leaving the exact prior shape as a future
implementation decision rather than falsely attributing it to the
paper.
**Channel C** (prose, 6-10 lines): The safest FB-11.1 plant is a
dedicated `bass.inference.priors` module plus a frozen carrier type. A
prior surface has to be inspectable on its own because it will feed both
the sampler and the later evidence calculation, and pushing it into the
driver would blur two audit seams that the SDD keeps separate. The
skeleton also needs to be honest about what the papers do and do not
say. Planck 2018 VI is a legitimate anchor for the parameter set and the
general neutrino-mass scale, but it is not enough evidence to pretend
that the local half-Gaussian `Sigma_mnu` contract is already a published
Planck prior. Recording that correction now is better than letting a
future implementation inherit a false citation chain. The package
boundary plus raising functions pin the API cleanly without inventing
probability mass.
**Alternatives**:
| # | Prior surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Dedicated `bass/inference/priors.py` module with a frozen `Prior` dataclass | Keeps priors inspectable and independent of the sampler; matches the SDD one-for-one. | Adds a new package boundary before any numerical prior exists. | ✅ |
| 2 | Hide prior builders inside the future emcee driver | Smaller public surface today. | Blurs FB-11.1 and FB-11.2, weakens auditability, and couples priors to one sampler choice. | — |
| 3 | Represent priors as raw mappings / lambdas only | Minimal code now. | Loses the typed contract, hides sampling/log-pdf symmetry, and makes the later CLI schema harder to pin. | — |
**Core principles**: separate priors from drivers; keep observer and
cosmological direction ownership distinct; record the Planck/Table-2
versus local-half-Gaussian distinction explicitly; deterministic failure
until actual prior math lands.
**Skeleton path**:
`htt/bass/inference/__init__.py`,
`htt/bass/inference/priors.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb111_priors_skeleton.py -q`
**Guard rails** (yes/no): `Prior` dataclass explicit? yes; SDD names
preserved exactly? yes; observer/cosmology split preserved in prose?
yes; Planck/Table-2 mismatch recorded honestly? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 66 skipped` → `3403 passed + 67 skipped` pending the
phase-close gate.

## §FB-11.2

### §FB-11.2 — emcee driver + reproducibility contract skeleton
**Determinism contract**: the planted docstrings now pin the future rule
that `run_posterior(..., seed=42, parallel=False)` must return a
`PosteriorSample` whose `samples`, `log_prob`, and `diagnostics` are
byte-identical across two runs on the same machine; the parallel path is
explicitly documented as non-default.
**Channel A**: 7 checked / 7 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md §3`
names `PosteriorSample`, `run_posterior`, and a CLI entry point as the
canonical FB-11.2 surfaces; verified the new driver lives under
`bass/inference/drivers/` so the external-driver boundary is explicit;
verified the new package `__init__` re-exports the driver contract
without importing any third-party sampler; verified the CLI parser now
pins `--config` and `--seed`; verified the docstrings record the
byte-reproducibility promise and the default single-threaded path;
verified the skip-marked contract test inspects the exact defaults; and
verified no production module outside `bass.inference.drivers/` now
mentions `emcee`.
**Channel B**: 5 source checks / 5 verified / 0 broken. Evidence:
Foreman-Mackey et al. 2013 (`arXiv:1202.3665`) describe `emcee` as a
stable, well-tested Python implementation of the affine-invariant
ensemble sampler and emphasize its low hyperparameter count. The same
paper's ar5iv-rendered §2 documents the stretch move and the split-
ensemble parallel update, while warning that a naive all-walkers-at-once
parallelization violates detailed balance. Goodman & Weare 2010 verify
the affine-invariant ensemble rationale in the primary algorithm paper.
Current package metadata further support the choice comparison used in
the alternatives table: `emcee` is MIT-licensed and production-stable on
PyPI; `dynesty`'s own docs position it as a dynamic nested-sampling
package for posteriors *and evidences* with heavier dependencies
(`numpy`, `scipy`, `matplotlib`); `zeus`'s PyPI page describes ensemble
slice sampling and is GPLv3-licensed rather than MIT. Together these
checks support the local SDD rationale for picking `emcee`.
**Channel C** (prose, 6-10 lines): The right FB-11.2 skeleton is a
driver contract, not a sampler import. The whole point of this phase is
to pin the reproducibility rule before real chains ever run, and the
cleanest way to do that is to define the container, the call signature,
and the CLI interface while still refusing to sample. Keeping the module
inside `bass.inference.drivers/` also enforces the external-driver
policy at the path level. The alternatives table matters here because
the choice is not arbitrary: `dynesty` is valuable for evidence work but
comes with a broader dependency and algorithm surface, while `zeus`
would import a GPL-licensed ensemble-slice implementation when the local
bundle already chose the Goodman-Weare / emcee lineage. The deterministic
default then follows directly from Foreman-Mackey's own parallel-update
discussion: a split-ensemble parallel path is possible, but it should
not become the invisible default for a contract that promises bytewise
repeatability.
**Alternatives**:
| # | Driver choice | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `emcee` ensemble MCMC under `bass/inference/drivers/emcee_driver.py` | Direct Goodman-Weare lineage; MIT license; light pure-Python surface; ensemble geometry matches the local parameter-space story. | Does not provide marginal evidence directly, so FB-11.3 still needs thermodynamic integration. | ✅ |
| 2 | `dynesty` production driver | Strong evidence story and built-in nested-sampling outputs. | Heavier dependency/runtime surface; docs explicitly frame it around posterior/evidence trade-offs; conflicts with the sealed SDD pick. | — |
| 3 | `zeus` production driver | Ensemble sampler with low-tuning claims and parallel support. | GPLv3 license and a different ensemble-slice formalism than the sealed emcee/Goodman-Weare choice. | — |
**Core principles**: keep third-party sampler ownership inside
`drivers/`; document the deterministic single-threaded default; expose
the CLI seed/config contract now; do not import `emcee` until actual
work begins.
**Skeleton path**:
`htt/bass/inference/drivers/emcee_driver.py`,
`htt/bass/inference/__main__.py`,
`htt/bass/inference/__init__.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb112_emcee_driver_skeleton.py -q`
**Guard rails** (yes/no): driver confined to `drivers/`? yes;
byte-identical contract pinned in docstrings? yes; non-default parallel
path explicit? yes; alternatives table includes emcee/dynesty/zeus? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 67 skipped` → `3403 passed + 68 skipped` pending the
phase-close gate.

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
