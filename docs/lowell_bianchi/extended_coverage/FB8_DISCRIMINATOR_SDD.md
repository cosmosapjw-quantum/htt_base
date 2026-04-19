# FB-8 SDD — Local-boost vs global-tilt discrimination

**Status**: draft, scope sealed 2026-04-20.
**Coordinator**: [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §5 FB-8](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).
**Prerequisite**: FB-3.5 β-gate reparametrisation (rapidity SSOT
per parent plan D4 = (a)).
**Audit contract**: [SELF_AUDIT_AUTOMATION.md](SELF_AUDIT_AUTOMATION.md).

This document specifies the FB-8 phase at SDD granularity: the new
public surfaces, their contracts, the unit-sized PR list, the
per-PR audit hooks, and the discriminator statistic that is the
**operational core** of the phase.

## 1. Purpose + scope

### 1.1 Problem statement

FB-7 delivers a direction-dependent likelihood whose pdf is
evaluated in the **Bianchi rest frame**. Real observations (Planck,
WMAP, LiteBIRD, future CMB-S4) live in the **Sun barycentric
frame**, whose peculiar-motion rapidity relative to the Bianchi
rest frame is neither known a priori nor identical to the
cosmology's global tilt. The FB-3 stack conflates the two into a
single `(β, v̂)` pair; as a consequence FB-7 cannot

1. independently report constraints on the cosmological tilt vs
   the observer's peculiar velocity, and
2. distinguish a Bianchi-IX-like anisotropy signal from a
   kinematic-dipole-like signal whose pattern happens to look
   similar at low ℓ.

FB-8 closes both gaps.

### 1.2 Shipping surfaces

- **`bass.observer.ObserverBoost(rapidity, v_hat)`** — type-distinct
  nuisance parameter; stores rapidity per D4 = (a); velocity is a
  derived property.
- **`bass.observer.aberration_kernel(L_max, boost) → K_{ℓℓ'}`** —
  the PSTF-basis ℓ-mode coupling matrix.
- **`bass.observer.apply_observer_boost(Cl_frame, boost, L_max)`** —
  observed-frame `C_ℓ` adapter.
- **`bass.observer.observed_alm_mixing(alm, boost, L_max)`** — map-
  space ℓm mixing.
- **`bass.observer.discriminator.likelihood_ratio(data, boost_model,
  tilt_model)`** — operational discriminator `Λ`.
- **`bass.observer.compose_tilts(global_tilt, observer_boost)`** —
  *diagnostic only*; non-commutation surface for the audit.
- **`bass.likelihood.observer_frame_adapter`** — ingests the FB-7.4
  cosmological-frame likelihood and exposes an observed-frame
  likelihood that exposes `ObserverBoost` as an independent axis.

### 1.3 Non-goals (pinned)

- Second-order boost corrections in `β²`: **out-of-scope**
  (discarded 2026-04-20 with FB-13; see
  [SCOPE_DECISIONS.md §4](SCOPE_DECISIONS.md)).
- Survey systematics (mask / beam / noise covariance): **out-of-
  scope** (discarded with FB-10; see [SCOPE_DECISIONS.md §2](SCOPE_DECISIONS.md)).
- Sampler prior over `(β_obs, v̂_obs)`: shipped in FB-11; FB-8
  delivers only the kernel + discriminator.
- Lensing aberration × CMB-lensing cross-terms: **out-of-scope**
  (discarded with FB-12).

### 1.4 Literature anchors

- **Challinor & van Leeuwen 2002**, *PRD* 65, 103001 — `K_{ℓℓ'}`
  derivation. Canonical equation set.
- **Planck 2013 XXVII** — operational aberration / Doppler
  pipeline; sanity numbers for `β_obs ≈ 1.23e-3`.
- **Kosowsky & Kahniashvili 2011**, *PRL* 106, 191301 — observer-
  boost reconstruction; consumed by the FB-8.5 likelihood-ratio
  statistic as the null hypothesis H_obs.
- **Ellis, Maartens & MacCallum 2012** §5.2–§5.3 — 1+3 covariant
  derivation that ties global tilt to observer boost.

---

## 2. FB-8.1 — `ObserverBoost` dataclass

### 2.1 Contract

```python
@dataclass(frozen=True)
class ObserverBoost:
    rapidity: float                # η_obs ∈ [0, ∞), SSOT per D4=(a)
    v_hat:    tuple[float, float, float]   # |v_hat|² = 1 ± 1e-10

    @property
    def velocity(self) -> float: ...    # derived: tanh(rapidity)
    @property
    def gamma(self) -> float: ...       # cosh(rapidity)
    @property
    def gamma_sq(self) -> float: ...    # cosh²(rapidity)
```

### 2.2 Invariants

- `rapidity == 0.0` path short-circuits in every consumer — byte-
  identical to the FB-7 cosmological-frame output.
- Guards eager in `__post_init__`: non-finite rapidity, negative
  rapidity, non-unit `v_hat`, wrong-length `v_hat` — all
  `ValueError`.
- The class **does not** subclass `TiltedSpeciesBackground`; the
  two live in separate modules precisely so a type checker refuses
  to accept an `ObserverBoost` anywhere a `GlobalTilt` is expected
  and vice-versa.

### 2.3 Delivery PR

- **PR title**: `FB-8.1: ObserverBoost dataclass (rapidity SSOT)`
- **Changes**: new `bass/observer/__init__.py` +
  `observer_boost.py`; ≥ 15 tests mirroring the FB-3.1 guard set.
- **Byte anchor**: FB-3.2 (`fdb1d86`) — no consumer wired yet, so
  anchor is preserved trivially.
- **Audit hook**: admissibility-guard closed-form (every
  `ValueError` branch pinned by a dedicated test).

---

## 3. FB-8.2 — Aberration kernel `K_{ℓℓ'}(β_obs)`

### 3.1 Contract

```python
def aberration_kernel(L_max: int, boost: ObserverBoost) -> np.ndarray:
    """Return (L_max+1, L_max+1) real matrix K_{ℓℓ'}.

    boost.rapidity == 0 → identity matrix, byte-identical.
    """
```

### 3.2 Reference equations

Challinor-van Leeuwen 2002 eq (26):

```text
    a'_{ℓm} = Σ_{ℓ'} K_{ℓℓ'}^m(β_obs) a_{ℓ'm}
```

The PSTF-basis representation collapses the m-index to a single
diagonal block structure, so the kernel can be stored as a
`(L+1, L+1)` real symmetric matrix per m up to numerical order
`O(β)`. FB-8 ships the linear kernel; quadratic corrections are
discarded with FB-13.

### 3.3 Invariants

- `β_obs = 0 → K = I` byte-identical (`np.array_equal`).
- Parity: `K_{ℓℓ'}(β_obs) = K_{ℓ'ℓ}(β_obs)` up to the
  Challinor-van Leeuwen sign convention pinned in the audit.
- Column-sum of `K^m` preserves total power to linear order (unit
  test at `β_obs = 1e-3`).

### 3.4 Delivery PR

- **PR title**: `FB-8.2: Aberration kernel K_ll'(beta_obs)`.
- **Changes**: `bass/observer/aberration.py`; closed-form
  regression against `K_{22}` and `K_{23}` at `β_obs = 1e-3` (the
  Planck-XXVII table 1 entries are the target).
- **Audit hook**: dimensional + symmetry audit; sign convention
  pinned.

---

## 4. FB-8.3 — Observer-frame adapters

### 4.1 Contract

```python
def apply_observer_boost(
    Cl_frame: dict[str, np.ndarray],
    boost: ObserverBoost,
    L_max: int,
) -> dict[str, np.ndarray]: ...

def observed_alm_mixing(
    alm: np.ndarray,
    boost: ObserverBoost,
    L_max: int,
) -> np.ndarray: ...
```

### 4.2 Invariants

- `boost.rapidity == 0` ⇒ input passes through byte-identical.
- At `β_obs = 1.23e-3` (Sun / CMB dipole amplitude), the `C_ℓ^{TT}`
  ratio matches Planck-2013-XXVII Table 1 within its quoted
  tolerance.
- The two adapters agree on `C_ℓ` when the `a_{ℓm}` adapter is
  composed with the standard `C_ℓ = Σ_m |a_{ℓm}|² / (2ℓ+1)` map.

### 4.3 Delivery PR

- **PR title**: `FB-8.3: apply_observer_boost + observed_alm_mixing`.
- **Audit hook**: known-limit recovery at `β_obs = 0` and the
  Sun-dipole value; cross-consistency test between the two
  adapters.

---

## 5. FB-8.4 — Non-commutation + SSOT composition order

### 5.1 Contract

```python
def compose_tilts(
    global_tilt: GlobalTilt,
    observer_boost: ObserverBoost,
) -> np.ndarray:
    """Diagnostic only — returns the naïve vector sum
    tanh(η_cosmo)·v_hat_cosmo + tanh(η_obs)·v_hat_obs.
    Exposed for the audit's non-commutation check; never consumed
    on the production path.
    """
```

### 5.2 Tests

- `test_K(β_obs) · B(β_cosmo) ≠ B(β_cosmo) · K(β_obs)` at
  representative parameter choices. Non-commutation is the
  physical reason the two parameters cannot be collapsed into one.
- SSOT composition order `(cosmo-tilt → observe-boost)` pinned per
  parent plan consequence table (D-answers section of the
  coordinator plan).

### 5.3 Delivery PR

- **PR title**: `FB-8.4: non-commutation + SSOT composition order pin`.
- **Audit hook**: the audit's §5 P0 failure mode — "two parameters
  silently collapsed" — is closed only when the non-commutation
  test passes.

---

## 6. FB-8.5 — Discriminator `Λ(data; H_obs, H_cosmo)`

**This is the operational core of the phase.** The kernel (§3) and
adapters (§4) are passive transforms; the discriminator is the
active statistic.

### 6.1 Scientific content

Two competing hypotheses on a given dataset `d` (observed
`C_ℓ^{obs}` + dipole alignment vector):

- **H_obs** — the apparent anisotropy is a kinematic artefact of
  observer peculiar motion; cosmology is FLRW.
  Free parameters: `(β_obs, v̂_obs)`.
- **H_cosmo** — the apparent anisotropy is cosmological (Bianchi
  type + global tilt `(β_cosmo, v̂_cosmo)`); observer peculiar
  motion is fixed at its external-data value.

The discriminator is the maximum-likelihood ratio

```text
    Λ(d) = 2 [ ln L_max(H_cosmo | d) − ln L_max(H_obs | d) ]
```

evaluated under the FB-7.4 cosmological-frame likelihood composed
with the FB-8.3 observer-frame adapter. At the H_obs null, `Λ`
follows an asymptotic χ² distribution with degrees-of-freedom
equal to the effective Bianchi-model dimension minus the
observer-boost dimension — exact dof pinned by the audit's §2.

### 6.2 Why a dedicated discriminator (not just the sampler)

Two reasons:

1. **Model evidence recovery rate depends on which statistic the
   sampler optimises.** The FB-11 sampler runs the full posterior;
   the discriminator is the focused test for the specific
   local-boost-vs-global-tilt comparison and gives a frequentist
   p-value that the downstream reporting pipeline
   (parent plan FB-7.5) can quote.
2. **Kinematic dipole signature is easy to mis-attribute at low
   ℓ.** A Bianchi-IX-like quadrupole can look like a boosted
   FLRW octupole at the precision of the Planck dipole residual.
   The discriminator pins the ℓ-dependence difference that
   separates them (see Challinor-van Leeuwen 2002 Fig. 2).

### 6.3 Contract

```python
def likelihood_ratio(
    data: ObservedDataset,
    boost_model: CosmologicalHypothesis,   # H_obs template
    tilt_model:  CosmologicalHypothesis,   # H_cosmo template
    *,
    seed: int,
) -> DiscriminatorResult: ...


@dataclass(frozen=True)
class DiscriminatorResult:
    Lambda:       float              # the statistic
    p_value:      float              # χ² tail, asymptotic dof fixed
    ln_ratio:     float              # raw ln L difference
    boost_MLE:    ObserverBoost
    tilt_MLE:     GlobalTilt
    dof:          int
    converged:    bool
```

### 6.4 Coverage test

The discriminator must pass a coverage test: for `N = 500`
synthetic realisations drawn from H_obs (FLRW + known
`(β_obs, v̂_obs)`), the discriminator's `p_value` histogram is
uniform on `[0, 1]` within the Kolmogorov-Smirnov tolerance at
the 99 % level. The same coverage test is applied with samples
drawn from H_cosmo to verify the alternate direction.

### 6.5 Invariants

- Deterministic under a fixed seed: running the same
  `likelihood_ratio(data, …, seed=42)` twice returns byte-
  identical `DiscriminatorResult`.
- `ObservedDataset` generated at `β_cosmo = β_obs = 0` yields
  `Lambda ≈ 0` (within MC error) and `p_value ≈ 0.5`.
- At `β_cosmo = 0`, `β_obs = 1.23e-3` (pure kinematic dipole), the
  discriminator prefers H_obs at significance > 95 % for Planck-
  2018 noise level.

### 6.6 Delivery PR

- **PR title**: `FB-8.5: local-boost-vs-global-tilt discriminator`.
- **Changes**: `bass/observer/discriminator.py` +
  `bass/observer/discriminator_coverage_test.py`.
- **Audit hook**: §5 "P0 — discriminator collapse to zero at
  non-trivial input" ruled out by the §6.4 coverage test.

---

## 7. FB-8.6 — Likelihood-stack ingest

### 7.1 Contract

```python
class ObserverFrameLikelihood:
    """Wraps a cosmological-frame likelihood so it exposes an
    observer-frame `log_prob(params)` where `params` includes a
    separate ObserverBoost axis.

    Construction:
        ObserverFrameLikelihood(
            cosmo_likelihood: CosmologicalFrameLikelihood,  # from FB-7.4
            boost_prior:      Prior[ObserverBoost],
        )
    """

    def log_prob(self, params: dict) -> float: ...
    def marginalise_boost(self, params: dict) -> float: ...
    def profile_boost(self, params: dict) -> tuple[float, ObserverBoost]: ...
```

### 7.2 Invariants

- With a delta-function prior at `β_obs = 0`, the marginalised
  likelihood equals the input cosmological-frame likelihood
  byte-identically.
- Default prior is the Kosowsky-Kahniashvili 2011 Gaussian with
  mean at the measured CMB dipole direction and amplitude
  `σ = 1.23e-3` (fully documented in the audit).

### 7.3 Delivery PR

- **PR title**: `FB-8.6: observer-frame likelihood adapter`.
- **Audit hook**: delta-prior byte-identity test.

---

## 8. FB-8.7 — Docs + gallery

- **Gallery topic**: `figures/physics_gallery/14_observer_frame/`
  with
  - `01_kernel_heatmap_1p23e-3.png` — `K_{ℓℓ'}` heatmap at the
    Sun-dipole value.
  - `02_Cl_ratio_before_after.png` — `C_ℓ^{obs} / C_ℓ^{frame}`.
  - `03_alm_mixing_demo.png` — a single `a_{ℓm}` map before /
    after the adapter.
  - `04_discriminator_coverage.png` — p-value histogram from the
    §6.4 coverage test.
- **Docs updates**:
  [00_conventions.md](../00_conventions.md) gains a new section
  pinning the SSOT composition order (cosmo-tilt → observe-boost)
  and the `ObserverBoost` rapidity convention.
  [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)
  (or its successor) receives one row per FB-8.* PR.

- **PR title**: `FB-8.7: docs + physics-gallery topic 14`.

---

## 9. Exit criteria (FB-8 closing audit)

1. Every FB-8.1 … FB-8.7 delivery PR has shipped with its audit
   document; the audits are unanimously Pass.
2. `ObserverBoost(rapidity=0)` is the byte-identical short-circuit
   in every consumer.
3. Coverage test (§6.4) is green for both `N=500` realisations
   drawn from H_obs and H_cosmo.
4. Sun-dipole aberration correction on `C_ℓ^{TT}` matches
   Planck-2013-XXVII to within the cited tolerances.
5. The audit's §5 ranked failure modes: zero P0, zero P1; any P2
   / P3 carries a reserved session tag in [SELF_AUDIT_AUTOMATION.md §8](SELF_AUDIT_AUTOMATION.md).
6. Gallery topic 14 rendered; `figures/physics_gallery/README.md`
   updated.
7. `NEXT_SESSION_PROMPT.md §2` rotated to whichever phase lands
   next (FB-9 or FB-11 per the dependency graph in
   [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §3](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md)).

---

## 10. Audit-doc skeleton (FB-8 closing)

Use the template in [SELF_AUDIT_AUTOMATION.md §3](SELF_AUDIT_AUTOMATION.md).
The FB-8 audit must also carry the following phase-specific
sections beyond the skeleton:

- **§FB-8.A** — frame-convention conversion evidence: a unit test
  that roundtrips an Ellis-convention fixture through
  `ellis_to_pc_rotation()` + `pc_to_ellis_rotation()` and asserts
  byte-identity against the raw fixture. Closes parent plan D1 =
  (b) + (a) conversion requirement.
- **§FB-8.B** — discriminator coverage report (§6.4 histogram +
  KS p-value). Required for the phase to close.
- **§FB-8.C** — cross-check against Kosowsky-Kahniashvili 2011
  worked example (their Table 1 recovery of a synthetic
  `β_obs = 1.23e-3` dipole).
