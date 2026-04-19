# FB-11 SDD — Inference driver + multi-type Bayes factor

**Status**: draft, scope sealed 2026-04-20.
**Coordinator**: [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §5 FB-11](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).
**Prerequisites**: FB-7 (cosmological-frame likelihood), FB-8
(observer-frame adapter + discriminator), FB-9 (massive neutrino
registry extension).
**Audit contract**: [SELF_AUDIT_AUTOMATION.md](SELF_AUDIT_AUTOMATION.md).

## 1. Purpose + scope

### 1.1 Problem statement

After FB-7, FB-8, and FB-9 close, the stack exposes a joint
likelihood `L(data | cosmology, Σm_ν, (β_cosmo, v̂_cosmo),
(β_obs, v̂_obs))`. FB-11 wraps that likelihood in an inference
driver that

1. draws a reproducible posterior over the joint parameter
   vector,
2. produces convergence diagnostics that a collaborator can
   read without running the sampler herself,
3. returns `ln B_{Bianchi-k, FLRW}` for each of the 11 Bianchi
   types, so a single summary table answers the research
   question ("which Bianchi type, if any, is favoured by the
   data?"),
4. and all of the above is deterministic under a fixed `seed`.

### 1.2 Shipping surfaces

- **`bass.inference.priors`** — module with documented priors for
  every sampled axis: `GlobalTilt`, `ObserverBoost`, `Σm_ν`, per-
  type structure parameters.
- **`bass.inference.run_posterior(likelihood, priors, *, seed) →
  PosteriorSample`** — the driver.
- **`bass.inference.bayes_factor(posterior_A, posterior_B) →
  float`** — nested-sampling-style evidence comparison (or the
  thermodynamic-integration fallback documented in §4.3).
- **`bass.inference.diagnostics`** — `r_hat`, `ess`, `geweke`,
  `trace_plot_data`.
- **`bass.inference.__main__`** — CLI entry point that takes a
  YAML config + seed and writes the posterior samples + a
  diagnostics JSON.

### 1.3 Non-goals (pinned)

- **ML-based likelihood emulators**: out of scope (post-
  extended).
- **GPU sampling**: out of scope (post-extended).
- **Hierarchy-marginal likelihood** (multi-level Bayesian
  pooling across Bianchi types): out of scope; FB-11 treats each
  Bianchi type as a separate model and computes pairwise Bayes
  factors.
- **Alternative samplers beyond the one selected in FB-11.2**:
  out of scope; a single sampler is selected, the others are
  available as reference implementations that must not be
  imported by production code.

### 1.4 Sampler choice

Per parent plan D-answer D8 = (a) (CAMB only on the external
side), no new runtime external dependency is accepted lightly.
FB-11.2 selects **emcee** as the production sampler — pure
Python, MIT-licensed, ensemble MCMC, transitively depends only on
`numpy`. The nested-sampling alternative (`dynesty`) is
implemented as a reference driver under `bass/inference/drivers/
dynesty_driver.py` but is **not imported** by the CLI and is not
exercised in the CI default path; it exists only so that §4.3's
thermodynamic-integration `ln B` can be cross-checked against the
nested-sampling evidence on a reduced test problem.

### 1.5 Literature anchors

- **Goodman & Weare 2010** — affine-invariant ensemble sampler.
- **Foreman-Mackey, Hogg, Lang & Goodman 2013**, *PASP* 125, 306
  — emcee reference.
- **Skilling 2006** — nested sampling (reference for the
  `dynesty` cross-check).
- **Lartillot & Philippe 2006** — thermodynamic integration for
  Bayes factors.
- **Gelman-Rubin 1992** — `r_hat`.
- **Geweke 1992** — `geweke` diagnostic.

---

## 2. FB-11.1 — `bass.inference.priors`

### 2.1 Contract

```python
@dataclass(frozen=True)
class Prior:
    name:   str
    domain: tuple[float, float] | None
    log_pdf: Callable[[np.ndarray], np.ndarray]
    sample:  Callable[[np.random.Generator, int], np.ndarray]
```

Concrete priors:

- `prior_rapidity(label: str, *, sigma: float) → Prior` — half-
  Gaussian on `η` (rapidity), truncated at `η = 0`. Used for
  both `GlobalTilt.rapidity` and `ObserverBoost.rapidity`; the
  caller picks `sigma` from the literature target.
- `prior_direction() → Prior` — isotropic on `S²` (used for both
  `v̂_cosmo` and `v̂_obs`).
- `prior_Sigma_mnu() → Prior` — half-Gaussian truncated at zero
  with `σ = 0.15 eV` (Planck-2018 VI prior shape).
- `prior_observer_boost() → Prior` — Kosowsky-Kahniashvili 2011
  Gaussian, centred at the measured CMB dipole, `σ = 1.23e-3`.
- `prior_structure_constants(bianchi_type: str) → Prior` — per-
  type structure-constant prior; for types with a free scaling
  parameter (II, VI_0, VII_0, VIII, IX, VI_h, VII_h) the prior
  is log-flat on the scaling factor within the admissible range
  defined in `bass.background.bianchi_types`.

### 2.2 Invariants

- Every prior has a `log_pdf` that agrees with the CDF of
  `sample` to within a Kolmogorov-Smirnov budget at `N = 10 000`.
- `prior_observer_boost` at `β_obs = 1.23e-3` has its mode at
  the measured Sun-CMB direction.

### 2.3 Delivery PR

- **PR title**: `FB-11.1: bass.inference.priors`.
- **Audit hook**: KS consistency between `log_pdf` and `sample`.

---

## 3. FB-11.2 — Sampler driver + reproducibility contract

### 3.1 Contract

```python
@dataclass(frozen=True)
class PosteriorSample:
    samples:       np.ndarray          # (N_walkers, N_steps, N_dim)
    log_prob:      np.ndarray          # (N_walkers, N_steps)
    seed:          int
    sampler:       str                 # e.g. "emcee-0.3.0"
    config:        dict                # frozen sampler config
    diagnostics:   dict                # r_hat, ess, geweke

def run_posterior(
    likelihood: Callable[[np.ndarray], float],
    priors:     dict[str, Prior],
    *,
    seed:       int,
    n_walkers:  int = 64,
    n_steps:    int = 5000,
    burnin:     int = 1000,
) -> PosteriorSample: ...
```

### 3.2 Reproducibility invariants

- `run_posterior(..., seed=42)` called twice on the same machine
  with the same `likelihood` / `priors` / config returns a
  `PosteriorSample` with byte-identical `samples`, `log_prob`,
  and `diagnostics`. The implementation uses
  `numpy.random.default_rng(seed)` threaded explicitly through
  emcee's `moves` state; no reliance on the global RNG.
- `run_posterior` is single-threaded by default. A `parallel=True`
  mode is available but **not** the default because thread-pool
  nondeterminism is the documented P0 failure mode (see §3.5).
- The sampler name and version are recorded on every
  `PosteriorSample` so a future reader can reconstruct the
  environment.

### 3.3 Config surface

A YAML config file specifies every sampler parameter explicitly;
no hidden defaults. A CLI entry point reads the config, runs the
sampler, and writes `.npz` + `.json` outputs.

### 3.4 Delivery PR

- **PR title**: `FB-11.2: emcee driver + reproducibility contract`.
- **Changes**: `bass/inference/drivers/emcee_driver.py`,
  `bass/inference/run.py`, `bass/inference/__main__.py`.
- **Audit hook**: byte-identical round-trip at `seed=42` on a
  toy problem (2-D Gaussian); determinism check documented in
  `§<tag>.4 numerical`.

### 3.5 Ranked P0 failure mode (pinned)

> "Sampler drifts between runs because of thread-pool
> nondeterminism."

Cheap probe: the byte-identical seed round-trip at
`parallel=False`. A second probe asserts that `parallel=True`
runs produce `log_prob` arrays that differ byte-wise — which
confirms the nondeterminism is confined to the parallel path and
is not leaking into the single-threaded default.

---

## 4. FB-11.3 — `bayes_factor` + symmetry

### 4.1 Contract

```python
def bayes_factor(
    posterior_A: PosteriorSample,
    posterior_B: PosteriorSample,
) -> BayesFactorResult: ...


@dataclass(frozen=True)
class BayesFactorResult:
    ln_B:       float
    ln_B_err:   float
    method:     str    # "nested" | "thermodynamic"
    provenance: dict
```

### 4.2 Algorithm

FB-11.2 selects emcee as the production sampler — emcee does not
return the marginal evidence directly. FB-11.3 therefore
implements **thermodynamic integration** (Lartillot-Philippe
2006) as the default `method`, computing

```text
    ln Z = ∫₀¹ dt ⟨ln L⟩_t
```

across a sweep of inverse-temperature `t` values. The `dynesty`
reference driver is used as a cross-check on the 2-D toy problem
in §4.4.

### 4.3 Invariants

- `bayes_factor(A, A)` returns `ln_B ≈ 0` within `3 · ln_B_err`.
- `bayes_factor(A, B)` and `bayes_factor(B, A)` are opposite in
  sign to within `ln_B_err`.
- On the 2-D toy problem (§4.4), the thermodynamic-integration
  `ln_B` matches the analytic `ln_B` within `0.1 ln units` and
  matches the `dynesty` nested-sampling value within
  `2 · ln_B_err`.

### 4.4 Cross-check

A dedicated test `test_bayes_factor_toy_two_gaussians` fixes a
2-D Gaussian-vs-Gaussian comparison with an analytic
`ln_B = −ln(2π) − ...`. The test asserts agreement at all three
levels: analytic, emcee + thermodynamic integration, dynesty
nested sampling.

### 4.5 Delivery PR

- **PR title**: `FB-11.3: bayes_factor (thermodynamic integration)`.
- **Audit hook**: symmetry + self-consistency + toy analytic
  cross-check.

---

## 5. FB-11.4 — Convergence diagnostics

### 5.1 Contract

```python
def r_hat(samples: np.ndarray) -> np.ndarray: ...           # per dim
def ess(samples: np.ndarray) -> np.ndarray: ...             # per dim
def geweke(samples: np.ndarray, *, first=0.1, last=0.5): ...
```

### 5.2 Thresholds (pinned)

- `r_hat < 1.01` for every dimension — stricter than the
  common `1.1` threshold, consistent with the project's
  "no silent fallback" rule.
- `ess > 400` for every dimension — empirical rule of thumb
  from Foreman-Mackey 2013; codified here.
- Geweke `|z| < 2` on the first-10 % vs last-50 % split.

If any threshold fails, `PosteriorSample.diagnostics['converged']`
is `False` and the CLI exits with a non-zero status. No silent
acceptance.

### 5.3 Delivery PR

- **PR title**: `FB-11.4: convergence diagnostics + thresholds`.
- **Audit hook**: threshold regressions from known-good fixtures;
  `converged=False` path is exercised by a test that deliberately
  under-runs the sampler.

---

## 6. FB-11.5 — Synthetic-injection end-to-end + coverage

### 6.1 Test design

For each of the 11 Bianchi types + FLRW:

1. Draw a ground-truth `(type, structure, Σm_ν, (β_cosmo,
   v̂_cosmo), (β_obs, v̂_obs))`.
2. Evaluate the FB-7 + FB-8 composed likelihood's forward model
   to produce a synthetic dataset at the declared noise level.
3. Run `run_posterior` on the synthetic dataset.
4. Check that the posterior's 1σ credible interval contains the
   ground truth in ≥ 68 % of mock realisations (`N_mock = 100`).

### 6.2 Invariants

- Coverage within `±5 %` of the nominal 68 %.
- At `(β_cosmo, β_obs) = (0, 0)` the posterior concentrates at
  FLRW; Bayes factor `ln_B_{Bianchi-k, FLRW}` is consistent with
  zero within `2 · ln_B_err` for every `k`.

### 6.3 Delivery PR

- **PR title**: `FB-11.5: synthetic-injection end-to-end + coverage`.
- **Audit hook**: coverage report + reproducibility at `seed=42`.

---

## 7. FB-11.6 — 11-type `ln B_{Bianchi-k, FLRW}` summary run

### 7.1 Deliverable

A single CLI invocation — `bass.inference --config
configs/fb11_summary.yaml --seed 42` — produces a summary table

```text
    Bianchi type | ln B | ln B_err | converged | MLE(β_cosmo, β_obs, Σm_ν)
```

for each of the 11 types against the FLRW baseline, on a
synthetic Planck-2018-quality dataset. The summary table lands
in `figures/paper/fb11_summary_table.json` + a human-readable
`fb11_summary_table.md` render.

### 7.2 Invariants

- The summary run is **byte-reproducible** at `seed=42` — two
  runs produce identical `.json` outputs.
- Every row has `converged=True`; rows that fail convergence
  are flagged explicitly and re-run with a longer chain before
  the summary is finalised.

### 7.3 Delivery PR

- **PR title**: `FB-11.6: 11-type ln B summary run`.
- **Audit hook**: reproducibility + convergence per-row;
  cross-check against the Pontzen-Challinor 2009 expected sign
  of `ln B` for Bianchi-IX vs FLRW on a synthetic Bianchi-IX
  dataset.

---

## 8. FB-11.7 — Docs + gallery

- **Gallery topic**: `figures/physics_gallery/16_inference_corner/`
  with
  - `01_corner_FLRW_vs_Bianchi_I.png` — corner plot on a FLRW
    synthetic dataset with Bianchi-I as the model.
  - `02_corner_Bianchi_IX_truth.png` — corner plot on a
    Bianchi-IX synthetic dataset.
  - `03_lnB_summary_bar.png` — the 11-type `ln B` bar chart.
  - `04_convergence_diagnostics.png` — `r_hat`, `ess`, Geweke
    per dimension.
- **Docs updates**:
  [05_integrator_spec.md](../05_integrator_spec.md) gains a new
  §N "Inference driver contract" documenting the reproducibility
  + threshold decisions.
  [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)
  (or its successor) receives one row per FB-11.* PR.

- **PR title**: `FB-11.7: docs + physics-gallery topic 16`.

---

## 9. Exit criteria (FB-11 closing audit)

1. Every FB-11.1 … FB-11.7 delivery PR has shipped with its audit
   document; the audits are unanimously Pass.
2. `run_posterior(..., seed=42)` byte-reproducible on the toy
   problem.
3. `bayes_factor` analytic cross-check within `0.1 ln units` on
   the 2-D Gaussian comparison; symmetry within `ln_B_err`.
4. Convergence thresholds (`r_hat < 1.01`, `ess > 400`, `|z_geweke|
   < 2`) met on every posterior row of the summary run.
5. Synthetic-injection coverage at `68 % ± 5 %` for all 11
   types.
6. Summary run reproducible at `seed=42`; summary-table JSON
   byte-identical across two runs.
7. Gallery topic 16 rendered; `figures/physics_gallery/README.md`
   updated.
8. `NEXT_SESSION_PROMPT.md §2` rotated to the final closing
   audit (or to `post-extended` maintenance if the extended
   bundle is the last planned phase).

---

## 10. Audit-doc skeleton (FB-11 closing)

Use the template in [SELF_AUDIT_AUTOMATION.md §3](SELF_AUDIT_AUTOMATION.md).
Phase-specific additions:

- **§FB-11.A** — reproducibility round-trip evidence: byte-identical
  `.npz` output hash recorded for two independent runs at the same
  seed.
- **§FB-11.B** — sampler-choice audit: record why emcee was
  selected over `dynesty` and `zeus`; include the wall-time and
  convergence comparison table from FB-11.2 sanity runs.
- **§FB-11.C** — coverage histogram from FB-11.5 + the summary-
  run-reproducibility digest.
- **§FB-11.D** — thermodynamic-integration vs nested-sampling
  cross-check from the 2-D toy problem.
