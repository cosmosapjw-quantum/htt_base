# Extended coverage plan — FB-8 / FB-9 / FB-11 (sealed scope)

**Status**: scope sealed 2026-04-20. Three in-scope phases only.
**Parent**: [INDEX.md](INDEX.md).
**Parent plan**: [FULL_BIANCHI_COVERAGE_PLAN.md](../FULL_BIANCHI_COVERAGE_PLAN.md) (FB-0 … FB-7 SSOT).
**Scope decisions**: [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md) — records the 2026-04-20 disposal of FB-10 / FB-12 / FB-13.

## 0. Scope statement (sealed)

Three phases extend the parent plan's FB-0 … FB-7 roadmap:

1. **FB-8 — Local-boost vs global-tilt discrimination** — introduces
   the observer-frame boost parameter `(β_obs, v̂_obs)` as a
   type-distinct nuisance alongside the cosmological global tilt
   `(β_cosmo, v̂_cosmo)` shipped by FB-3, and adds an active
   **discriminator** (likelihood-ratio statistic) that separates
   their signatures in observed data. Detailed SDD:
   [FB8_DISCRIMINATOR_SDD.md](FB8_DISCRIMINATOR_SDD.md).
2. **FB-9 — Massive neutrino species** — ships the `m_ν > 0`
   species required to reproduce Planck-2018 constraints on `Σm_ν`.
   Detailed SDD: [FB9_MASSIVE_NEUTRINO_SDD.md](FB9_MASSIVE_NEUTRINO_SDD.md).
3. **FB-11 — Inference driver + multi-type Bayes factor** — wraps
   the FB-7 + FB-8 + FB-9 likelihood stack in a sampler (choice
   pinned per parent plan D-answers) and produces
   `ln B_{Bianchi-k, FLRW}` for each of the 11 types. Detailed SDD:
   [FB11_INFERENCE_DRIVER_SDD.md](FB11_INFERENCE_DRIVER_SDD.md).

**Previously proposed, explicitly discarded on 2026-04-20**: FB-10
(survey integration), FB-12 (lensing / ISW), FB-13 (second-order
tilt). See [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md) for the
disposal rationale.

This plan document is a **coordinator**: it states the dependency
graph, the shared invariants, and the bundle-wide audit contract,
and defers per-phase design detail to the three SDD documents
above.

---

## 1. Load-bearing distinction (terminology pin)

Throughout FB-8, FB-9, and FB-11 the following names are strict
type-distinct surfaces. No single module carries both; no single
parameter name collapses them.

- **Global tilt** (shipped by FB-3): `(β_cosmo, v̂_cosmo)`.
  Parametrises the species rest frame relative to the Bianchi
  `n^a` field. Property of the cosmology. Sampled jointly with
  the Bianchi type and its structure constants. Internal SSOT
  storage: rapidity per parent plan D4 = (a); velocity exposed
  as a derived property for backward compatibility.
- **Local boost** (introduced by FB-8): `(β_obs, v̂_obs)`.
  Parametrises the measurement frame relative to the species
  rest frame (or the Bianchi rest frame at the observer's
  location). Nuisance parameter, marginalised at inference
  time. Internal SSOT storage: rapidity (parent plan D4 = (a)
  applied here too).
- **Aberration kernel** `K_{ℓℓ'}(β_obs)` (FB-8 artefact): the
  ℓ-mode coupling induced by the local boost when a
  cosmological-frame spectrum is observed in the measurement
  frame. PSTF-basis representation; `β_obs = 0` reduces to the
  identity. See [FB8_DISCRIMINATOR_SDD.md §3](FB8_DISCRIMINATOR_SDD.md).
- **Discriminator** `Λ(data)` (FB-8 artefact): the statistic that
  separates the two signatures. Operational core of FB-8 beyond
  the passive kernel.

---

## 2. Sealed answers to the open design decisions

The parent plan's D1–D10 open items are answered as recorded in
[FULL_BIANCHI_COVERAGE_PLAN.md §6 (sealed 2026-04-20)](../FULL_BIANCHI_COVERAGE_PLAN.md).
The following items in this plan are direct consequences of those
answers:

| Ref | Consequence |
|---|---|
| D1 = (b) + (a) conversion | FB-8 / FB-11 literature fixtures may be ingested in Ellis convention; conversion provided by `bass.background.bianchi_types.ellis_to_pc_rotation()` (to be added in the FB-BOOTSTRAP follow-up PR inside the FB-8 chain). |
| D4 = (a) rapidity SSOT | `GlobalTilt` and `ObserverBoost` dataclasses store rapidity internally; `.velocity` exposed as a derived property. FB-3.5 reparametrisation PR lands before FB-8 entry. |
| D7 = (a) massive ν included | FB-9 is in the extended scope (not post-FB). |
| D8 = (a) CAMB only | FB-9 and FB-11 fixtures use CAMB / CLASS output only as frozen NPZ files; no runtime import. |
| D9 = (a) HTT triad at FB-7.3 | FB-8 discriminator consumes the FB-7.3 HTT output; the discriminator does **not** duplicate or pre-empt the triad resolution. |

Any extended-plan decision table previously carrying E-numbered
items is superseded by this section; items not listed above were
either absorbed into the three SDD documents or dropped with
FB-10 / FB-12 / FB-13.

---

## 3. Dependency graph

```text
        FB-BOOTSTRAP ─► FB-3.5 (β-gate) ─► FB-8 ─┐
                                                 │
                                FB-9 ────────────┤
                                                 ▼
                                               FB-11
```

- `FB-BOOTSTRAP` (already specified in [SELF_AUDIT_AUTOMATION.md §6](SELF_AUDIT_AUTOMATION.md))
  extends the phase-boundary hook to recognise `FB-\d+(\.\d+)?:`
  commit prefixes. Shipped alongside the bundle documents.
- `FB-3.5` β-gate reparametrisation (already planned in the parent
  plan, see [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md))
  migrates `TiltedSpeciesBackground.beta` from velocity-SSOT to
  rapidity-SSOT per D4 = (a). FB-8 depends on this: `ObserverBoost`
  must inherit the same rapidity convention as `GlobalTilt`.
- `FB-8` and `FB-9` are independent and may ship in either order;
  FB-11 consumes both.

No calendar timelines — ordering stated by dependency only.

---

## 4. Bundle-wide invariants (non-negotiable)

Every PR inside FB-8 / FB-9 / FB-11 must preserve these invariants
byte-for-byte against their named anchor commit:

| Invariant | Anchor commit | Test mechanism |
|---|---|---|
| FB-3.2 tilt-kinematic adapter anchor | `fdb1d86` | `np.array_equal` on β = 0 adapter outputs |
| FB-2.4 driver anchor | `d7d25da` | `np.array_equal` on 12-label no-kwargs RHS |
| LB-6 regression | (LB-6 closure commit) | full suite green |
| Default-kwargs backward-compat | every prior anchor | every new kwarg defaults to `None` / `0` / identity |

Any PR that cannot meet all four invariants must either (a) re-open
the anchor with a documented rationale in the audit document, or
(b) halt and escalate. Silent drift is a P0 audit finding per
[SELF_AUDIT_AUTOMATION.md §3](SELF_AUDIT_AUTOMATION.md).

---

## 5. Per-phase summary tables

Full SDDs live in the per-phase documents. The rows below are a
directory-level summary so the coordinator plan stays legible.

### FB-8 — Local-boost vs global-tilt discrimination

| Unit | Title | Delivery doc |
|---|---|---|
| FB-8.1 | `ObserverBoost` dataclass (rapidity SSOT) | [§2 of SDD](FB8_DISCRIMINATOR_SDD.md) |
| FB-8.2 | Aberration kernel `K_{ℓℓ'}(β_obs)` | [§3 of SDD](FB8_DISCRIMINATOR_SDD.md) |
| FB-8.3 | Observer-frame adapter on `C_ℓ` / `a_{ℓm}` | [§4 of SDD](FB8_DISCRIMINATOR_SDD.md) |
| FB-8.4 | Non-commutation + SSOT composition order pin | [§5 of SDD](FB8_DISCRIMINATOR_SDD.md) |
| FB-8.5 | **Discriminator** `Λ(data; H_obs, H_cosmo)` | [§6 of SDD](FB8_DISCRIMINATOR_SDD.md) |
| FB-8.6 | Likelihood-stack ingest (FB-7.4 → observer-frame) | [§7 of SDD](FB8_DISCRIMINATOR_SDD.md) |
| FB-8.7 | Docs + gallery topic `14_observer_frame/` | [§8 of SDD](FB8_DISCRIMINATOR_SDD.md) |

### FB-9 — Massive neutrino species

| Unit | Title | Delivery doc | Status |
|---|---|---|---|
| FB-9.1 | `phase_space_grid` + determinism tests | [§2 of SDD](FB9_MASSIVE_NEUTRINO_SDD.md) | ✅ shipped locally (2026-04-20; pending user commit hash) |
| FB-9.2 | `MassiveNeutrinoBackground.rho_rest` / `.p_rest` | [§3 of SDD](FB9_MASSIVE_NEUTRINO_SDD.md) | ✅ shipped locally (2026-04-20; pending user commit hash) |
| FB-9.3 | Registry integration + `m=0` byte-identity | [§4 of SDD](FB9_MASSIVE_NEUTRINO_SDD.md) | ✅ shipped locally (2026-04-20; pending user commit hash) |
| FB-9.4 | Hierarchy wire-up + free-streaming regression | [§5 of SDD](FB9_MASSIVE_NEUTRINO_SDD.md) | ✅ shipped locally (2026-04-20; pending user commit hash) |
| FB-9.5 | FB-3 compatibility (`TiltedSpeciesBackground` on massive ν) | [§6 of SDD](FB9_MASSIVE_NEUTRINO_SDD.md) | ✅ shipped locally (2026-04-20; pending user commit hash) |
| FB-9.6 | Docs + gallery topic `15_massive_neutrino/` | [§7 of SDD](FB9_MASSIVE_NEUTRINO_SDD.md) | ✅ shipped locally (2026-04-20; pending user commit hash) |

### FB-11 — Inference driver + multi-type Bayes factor

| Unit | Title | Delivery doc |
|---|---|---|
| FB-11.1 | `bass.inference.priors` module | [§2 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |
| FB-11.2 | Sampler driver + reproducibility contract | [§3 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |
| FB-11.3 | `bayes_factor` + symmetry / self-consistency | [§4 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |
| FB-11.4 | Convergence diagnostics (`r_hat`, `ess`, `geweke`) | [§5 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |
| FB-11.5 | Synthetic-injection end-to-end + coverage test | [§6 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |
| FB-11.6 | 11-type `ln B_{Bianchi-k, FLRW}` summary run | [§7 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |
| FB-11.7 | Docs + gallery topic `16_inference_corner/` | [§8 of SDD](FB11_INFERENCE_DRIVER_SDD.md) |

---

## 6. Aggregate exit criteria

The extended bundle closes when **all** of the following hold:

1. Every anchor in §4 is byte-identical on the full `bass/ tsc/`
   suite.
2. [FB8_DISCRIMINATOR_SDD.md §9](FB8_DISCRIMINATOR_SDD.md) exit
   criteria all green.
3. [FB9_MASSIVE_NEUTRINO_SDD.md §8](FB9_MASSIVE_NEUTRINO_SDD.md)
   exit criteria all green.
4. [FB11_INFERENCE_DRIVER_SDD.md §9](FB11_INFERENCE_DRIVER_SDD.md)
   exit criteria all green.
5. Every carry-forward item raised across FB-8 / FB-9 / FB-11
   carries a reserved session tag in the closing audit document
   (see [SELF_AUDIT_AUTOMATION.md §8](SELF_AUDIT_AUTOMATION.md)).
6. Bundle index ([INDEX.md](INDEX.md)) lists the three SDDs as
   "shipped" with commit anchors.
7. [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)
   (or its successor `DEVELOPMENT_LOG_FB8_ONWARD.md` once FB-7
   closes) carries one row per shipped FB-8 / FB-9 / FB-11 PR.

---

## 7. Out-of-scope disposals (recorded here for traceability)

- **FB-10** (survey integration — mask / beam / noise): discarded
  2026-04-20 per [SCOPE_DECISIONS.md §2](SCOPE_DECISIONS.md).
  The `htt/` and `mio/` subsystems retain their existing
  observation-side code; no `bass/` survey surface is added in the
  extended bundle.
- **FB-12** (lensing / ISW non-linear): discarded 2026-04-20 per
  [SCOPE_DECISIONS.md §3](SCOPE_DECISIONS.md).
- **FB-13** (second-order tilt): discarded 2026-04-20 per
  [SCOPE_DECISIONS.md §4](SCOPE_DECISIONS.md).

If any of these three re-enters scope later, the re-entry must
amend [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md) with a new dated
section and a rationale; simply re-adding rows to this plan is not
sufficient.

---

## 8. Cross-references

- [INDEX.md](INDEX.md) — bundle entry point + read order.
- [PROJECT_MEMORY_EXPLICIT.md](PROJECT_MEMORY_EXPLICIT.md) —
  constraints, user profile, workflow rules.
- [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md) —
  append-only ledger.
- [SELF_AUDIT_AUTOMATION.md](SELF_AUDIT_AUTOMATION.md) — per-PR
  discipline.
- [FB8_DISCRIMINATOR_SDD.md](FB8_DISCRIMINATOR_SDD.md)
- [FB9_MASSIVE_NEUTRINO_SDD.md](FB9_MASSIVE_NEUTRINO_SDD.md)
- [FB11_INFERENCE_DRIVER_SDD.md](FB11_INFERENCE_DRIVER_SDD.md)
- [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md)
