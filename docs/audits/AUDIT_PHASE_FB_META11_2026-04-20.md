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

### §FB-11.3 — `bayes_factor` skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md §4`
names `bayes_factor` and `BayesFactorResult` as the canonical FB-11.3
surface; verified the new module lives at `bass.inference.bayes` as the
SDD promises; verified the package root now exports both names; verified
the result dataclass fields match the SDD contract exactly; verified the
docstring pins thermodynamic integration as the default and `dynesty` as
reference-only; verified the new skipped harness test checks the public
signature without executing any evidence code.
**Channel B**: 3 source checks / 3 verified / 0 broken. Evidence:
Lartillot & Philippe 2006 are verified on PubMed as the canonical
thermodynamic-integration Bayes-factor paper and describe the method as
an alternative to the unreliable harmonic-mean estimator. Skilling 2006
is verified through the open-access Bayesian Analysis metadata as the
canonical nested-sampling evidence paper, where evidence is the prime
computational target and posterior samples are an optional by-product.
Those sources line up with the local SDD decision: production sampling
is `emcee`, so the default evidence method must be thermodynamic
integration; nested sampling stays a cross-check path only.
**Channel C** (prose, 6-10 lines): The safest FB-11.3 plant is a tiny
module with one dataclass and one raising function. Evidence code is
exactly the kind of thing that becomes misleading if a skeleton tries to
look half-complete, so the public contract needs to be explicit about
what method is primary and what method is only a reference. Choosing
thermodynamic integration as the documented default follows from the
previous sampler decision, not from any claim that TI is universally
better than nested sampling. The audit says that directly. `dynesty` is
still important here because the SDD wants a toy cross-check, but that
does not require importing it into the production path during the
skeleton cycle. The result carrier plus docstring is enough to lock that
logic into the repo.
**Alternatives**:
| # | Evidence surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `bayes_factor` with thermodynamic-integration default and nested-sampling provenance hook | Matches the emcee production choice and keeps the reference cross-check explicit. | Actual TI implementation still has to arrive later. | ✅ |
| 2 | Make nested sampling the production path immediately | Direct evidence estimates. | Reopens the sealed FB-11.2 sampler choice and broadens the default dependency/runtime path. | — |
| 3 | Leave evidence as an unnamed helper inside the driver | Smaller public API today. | Erases the FB-11.3 audit seam and hides method provenance. | — |
**Core principles**: separate evidence from posterior sampling; make TI
the explicit production default; keep nested sampling reference-only;
raise rather than fake a log-evidence calculation.
**Skeleton path**:
`htt/bass/inference/bayes.py`,
`htt/bass/inference/__init__.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb113_bayes_factor_skeleton.py -q`
**Guard rails** (yes/no): TI default explicit? yes; `dynesty`
reference-only note explicit? yes; result dataclass matches SDD? yes;
placeholder still raises? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 68 skipped` → `3403 passed + 69 skipped` pending the
phase-close gate.

## §FB-11.4

### §FB-11.4 — convergence diagnostics skeleton
**Threshold pin**: the planted docstrings now record the FB-11 policy
`R-hat < 1.01`, `ESS > 400`, and Geweke `|z| < 2`, with the threshold
history made explicit rather than silently attributed to the 1992
papers.
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md §5`
names `r_hat`, `ess`, `geweke`, and `trace_plot_data`; verified the new
diagnostics module exports exactly those names; verified the package root
re-exports all four functions; verified the docstrings pin the local
thresholds without pretending the algorithms are implemented; verified
the skip-marked harness test checks the signature defaults; verified no
driver or CLI code tries to consume numeric diagnostics yet.
**Channel B**: 4 source checks / 4 verified / 0 broken. Evidence:
Gelman & Rubin 1992 are the primary source for the potential scale
reduction factor and frame it as a diagnostic that approaches 1 at
convergence; they do not themselves canonize the modern `1.01` cutoff.
Geweke's 1991/1992 convergence work is verified through the Federal
Reserve Bank of Minneapolis abstract, which states that spectral methods
are used to evaluate numerical accuracy and construct convergence
diagnostics. Vehtari et al. 2021 explicitly describe flaws in the
traditional Gelman-Rubin `R-hat` and provide the modern improved
context. Current Stan guidance then recommends `R-hat < 1.01` for
trusting final samples and notes that `1.1` can be acceptable only in
early workflow. That sequence is the threshold history the audit pins:
the original statistic is from 1992, the stricter operational cutoff is
later.
**Channel C** (prose, 6-10 lines): This sub-phase is mostly about
honesty. Convergence thresholds are the kind of thing teams casually
quote without distinguishing the original statistic from the modern
workflow policy built around it. The skeleton docstrings now separate
those layers on purpose. `R-hat` comes from Gelman-Rubin, the Geweke `z`
comes from Geweke's spectral-diagnostic work, and the bundle's strict
`1.01` threshold is a project choice informed by later practice rather
than a backdated claim about 1992. That distinction matters because the
future implementation should inherit a correct citation chain, not just
the right numbers. The code remains tiny because the threshold policy is
the load-bearing part of the skeleton.
**Alternatives**:
| # | Diagnostics surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Dedicated `diagnostics.py` with explicit threshold docstrings | Keeps convergence policy inspectable and independent of sampler internals. | Adds a separate module before any numeric implementation exists. | ✅ |
| 2 | Hide diagnostics inside `run_posterior` only | Smaller API surface. | Hides the threshold policy and makes audit/CLI reuse harder. | — |
| 3 | Defer all diagnostics until summary-run work | Less code today. | Loses the threshold contract that the SDD treats as part of the public surface. | — |
**Core principles**: distinguish original diagnostics from later
operational cutoffs; keep threshold policy public; expose trace payload
as a separate helper; raise rather than compute partial diagnostics.
**Skeleton path**:
`htt/bass/inference/diagnostics.py`,
`htt/bass/inference/__init__.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb114_diagnostics_skeleton.py -q`
**Guard rails** (yes/no): threshold history explicit? yes; modern `1.01`
not misattributed to 1992? yes; Geweke defaults pinned? yes; numeric
implementation still absent? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 69 skipped` → `3403 passed + 70 skipped` pending the
phase-close gate.

## §FB-11.5

### §FB-11.5 — synthetic-injection coverage harness skeleton
**Determinism contract**: the future synthetic-injection harness must
reuse the same `run_posterior(..., seed=42)` same-machine byte-
reproducibility promise as FB-11.2, so repeated mock injections at fixed
seed generate byte-identical posterior artifacts before any coverage
aggregation is computed.
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md §6`
specifies FB-11.5 as a skip-marked synthetic-injection end-to-end test;
verified the prompt explicitly asks for a `pytest.skip` harness with a
`68 %` coverage assertion; verified the new test file lives under the
inference package rather than creating a fake runtime module; verified
the harness references both `run_posterior` and `bayes_factor` as the
future integration seam; verified no production code changes were needed
for this sub-phase.
**Channel B**: 2 source checks / 2 verified / 0 broken. Evidence:
Cook, Gelman, and Rubin 2006 are verified from the Columbia-hosted PDF
as the canonical software-validation paper and explicitly state that if
parameters are drawn from the prior, data are drawn from the sampling
distribution, and Bayesian inference is performed correctly, then
posterior intervals have correct average coverage (for example, 50% and
95% intervals contain the truth with probabilities `0.5` and `0.95`).
That directly supports the local FB-11.5 design of a simulation-based
coverage harness rather than an ad hoc recovery test.
**Channel C** (prose, 6-10 lines): The right FB-11.5 skeleton is only a
test. There is no reason to invent a runtime API for synthetic
injections when the SDD already defines this work as validation around
the existing posterior and evidence surfaces. The Cook-Gelman-Rubin
paper is especially helpful here because it gives a principled reason
for the harness shape: posterior calibration is checked by simulating
from the model and then re-fitting the same model. That is exactly what
the future FB-11.5 actual-work phase will do. The skipped test pins the
nominal `68 % ± 5 %` target now so the contract is visible in CI without
pretending the expensive mock loop already exists.
**Alternatives**:
| # | Coverage skeleton shape | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Skip-marked pytest harness that references `run_posterior` and `bayes_factor` | Matches the prompt directly and keeps the future validation on an existing CI seam. | No reusable helper code yet. | ✅ |
| 2 | New runtime `synthetic.py` module | Could centralize mock-generation helpers later. | Unnecessary API surface during the skeleton cycle. | — |
| 3 | Audit-only prose with no test file | Lowest code churn. | Fails to pin the contract into CI and weakens the validation seam. | — |
**Core principles**: validation belongs in tests; coverage target is
explicit; determinism requirement is inherited from the driver; no fake
mock-generation runtime is added during the skeleton cycle.
**Skeleton path**:
`htt/bass/inference/test_fb115_synthetic_injection_skeleton.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb115_synthetic_injection_skeleton.py -q`
**Guard rails** (yes/no): skip-marked harness present? yes; `68 %`
target explicit? yes; seed-roundtrip expectation recorded? yes; no new
runtime surface invented? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 70 skipped` → `3403 passed + 71 skipped` pending the
phase-close gate.

## §FB-11.6

### §FB-11.6 — 11-type `ln B_{Bianchi-k, FLRW}` summary seam
**Determinism contract**: once implemented,
`python -m bass.inference --config configs/fb11_summary.yaml --seed 42`
must emit `figures/paper/fb11_summary_table.json` and
`figures/paper/fb11_summary_table.md` byte-identically across two runs
on the same machine.
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB11_INFERENCE_DRIVER_SDD.md §7`
defines FB-11.6 as a CLI/output seam rather than a new runtime module;
verified the new `configs/fb11_summary.yaml` placeholder reserves the
11-type order against the FLRW baseline; verified the CLI docstrings now
name the exact summary command and output paths; verified the new
skip-marked harness test locks the 11-type SSOT order via
`ALL_BIANCHI_TYPES`; verified no dummy `.json` or `.md` paper outputs
were created during the skeleton cycle.
**Channel B**: 3 source checks / 2 verified / 1 corrected. Evidence:
Planck 2018 V (`arXiv:1907.12875`) is verified as the Planck 2018 CMB
power-spectrum / likelihood paper and is therefore a defensible anchor
for the local phrase "synthetic Planck-2018-quality dataset." Oxford
metadata for the later Bayesian-analysis paper on anisotropic
cosmologies states that tight constraints had already been placed on
Bianchi IX models, which is directionally consistent with expecting a
non-positive `ln B_{IX, FLRW}` on a Planck-like synthetic FLRW dataset.
Corrected: the prompt-supplied `arXiv:0706.2075` is the 2007
Pontzen-Challinor Bianchi `VII_h` / polarization paper, not a direct
Bianchi-IX evidence-sign source, so the exact sign citation remains a
carry-forward item for actual work rather than a silently accepted
locator.
**Channel C** (prose, 6-10 lines): The safe FB-11.6 skeleton is the
summary seam itself: the config file, the CLI contract, and the reserved
output paths. That makes the future review surface concrete without
faking the paper artifacts. The summary run belongs at the command-line
layer because it is orchestration across all 11 types, not a new piece
of posterior math. Reserving the config now also pins the type order to
the existing SSOT instead of leaving it implicit in a future loop. The
source correction matters here because a wrong Bianchi-IX evidence
citation would be easy to cargo-cult once the summary table exists. The
audit therefore keeps the exact-sign claim at the level of an explicit
inference and leaves the direct source requirement visible for the
actual-work session.
**Alternatives**:
| # | FB-11.6 skeleton shape | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Placeholder config + CLI output-path contract + skipped harness test | Pins the exact command, output paths, and 11-type order without fabricating a paper artifact. | Adds a config file before any parser exists. | ✅ |
| 2 | Pre-create dummy `fb11_summary_table.json` / `.md` files | Makes the future output names concrete. | Misleading, because no summary run has happened yet. | — |
| 3 | New runtime `summary.py` module during the skeleton cycle | Could centralize orchestration later. | Invents an extra module the SDD does not require and broadens the public surface early. | — |
**Core principles**: summary orchestration belongs at the CLI seam; no
dummy paper outputs; 11-type order is pinned via the background SSOT;
the Bianchi-IX sign citation gap stays explicit.
**Skeleton path**:
`configs/fb11_summary.yaml`,
`htt/bass/inference/__main__.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb116_summary_run_skeleton.py -q`
**Guard rails** (yes/no): exact CLI command pinned? yes; output paths
named explicitly? yes; 11-type order fixed via SSOT? yes; no dummy
summary artifacts created? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 71 skipped` → `3403 passed + 72 skipped` pending the
phase-close gate.

## §FB-11.7

### §FB-11.7 — docs + gallery placeholders
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified the
integrator spec now includes an explicit FB-11 inference-driver
placeholder section; verified the root gallery README now reserves topic
`16_inference_corner`; verified the new topic README states the no-PNG
status explicitly; verified the new skip-marked harness test locks the
docs/gallery file presence; verified no fake paper tables or gallery
PNGs were added during this docs-only sub-phase.
**Channel B**: no external literature anchor required for FB-11.7; the
local FB-11 SDD explicitly names the docs update plus gallery topic 16,
and `SELF_AUDIT_AUTOMATION.md` requires gallery no-ops to be stated
explicitly rather than implied. This sub-phase matches both local
requirements.
**Channel C** (prose, 6-10 lines): Docs-only closeouts are where a
skeleton phase can quietly become misleading, so the wording matters.
The new integrator-spec note says plainly that FB-11 is an inference
layer layered on top of the forward-model runtime rather than part of
the LB-5 integrator itself. The gallery README says the same thing in a
different place: the topic exists, but no inference figures have been
rendered yet. Reserving the topic number now avoids future ad hoc
placement once corner plots and convergence bars are real. As in the
earlier META placeholder phases, the honest move is a README and a
skipped presence test, not fabricated outputs.
**Alternatives**:
| # | FB-11.7 docs strategy | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Explicit placeholder section + reserved gallery topic README | Honest about scope and keeps future doc/gallery paths stable. | Adds visible documentation for work that is not yet implemented. | ✅ |
| 2 | Wait until real figures exist | Less placeholder prose today. | Violates the explicit no-op gallery rule and leaves the future topic path unstated. | — |
| 3 | Generate fake placeholder PNGs or paper tables | Makes the tree look complete. | Misleading and directly against the no-fabricated-artifact rule. | — |
**Core principles**: placeholder docs must say "not implemented" out
loud; no dummy artifacts; future topic/path names pinned now; inference
scope stays separate from the forward integrator runtime.
**Skeleton path**:
`docs/lowell_bianchi/05_integrator_spec.md`,
`figures/physics_gallery/16_inference_corner/README.md`,
`figures/physics_gallery/README.md`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb117_docs_gallery_skeleton.py -q`
**Guard rails** (yes/no): docs placeholder explicit? yes; gallery topic
reserved? yes; no dummy PNGs created? yes; skip-marked presence test
added? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 72 skipped` → `3403 passed + 73 skipped` pending the
phase-close gate.

## Phase close note

- **Status**: Pass on the FB-11 touched surface; whole-suite close gate
  is currently blocked by an unrelated dirty-worktree deletion.
- **Targeted gates**:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb115_synthetic_injection_skeleton.py -q`
  → `1 skipped`;
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb116_summary_run_skeleton.py -q`
  → `1 skipped`;
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/inference/test_fb117_docs_gallery_skeleton.py -q`
  → `1 skipped`.
- **Whole-suite close gate**:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3400 passed, 73 skipped, 26 warnings, 3 errors`.
- **External blocker**: the failing rows are the three
  `TestLBCAMBMatch` cases in `bass/integration/test_lowell_bianchi.py`,
  and the traceback shows the root cause is a pre-existing missing
  fixture at `data/camb_ref_planck2018.npz`. `git status --short`
  already reports that path as deleted outside the FB-11 work.
- **Baseline movement**: last fully green pre-phase anchor remained
  `3403 passed + 66 skipped`; the FB-11 skeleton plants add seven
  skip-marked tests, so the expected green profile after restoring the
  unrelated CAMB fixture is `3403 passed + 73 skipped`.
- **Determinism verdict**: preserved at the contract layer. FB-11 ships
  only docstrings, placeholders, and skip-marked harnesses; no sampler
  runtime was introduced.
- **Gallery status**: no-op by design; topic
  `figures/physics_gallery/16_inference_corner/` is reserved with a
  README only.
- **Handoff**: `NEXT_SESSION_PROMPT.md §2` rotated to the FB-4.1
  actual-work bootstrap with the mandatory FB-META sweep banner and a
  pointer to `AUDIT_FB_META_SUMMARY_2026-04-20.md`.
