# Extended Coverage (FB-3 → FB-11) — document bundle index

**Status**: scope sealed 2026-04-20. Living document set updated at
every phase-boundary.
**Parent plan**: [FULL_BIANCHI_COVERAGE_PLAN.md](../FULL_BIANCHI_COVERAGE_PLAN.md) (FB-0 .. FB-7 SSOT; §11 sealed 2026-04-20).
**Scope**: This bundle extends the parent plan by (i) recording the
phase-by-phase development history from FB-3 onward, (ii) specifying
three in-scope extension phases at SDD / WBS / PR granularity — FB-8
(local-boost vs global-tilt discrimination), FB-9 (massive
neutrino), FB-11 (inference driver + multi-type Bayes factor),
(iii) pinning the per-step self-audit + docs-update automation
protocol, (iv) surfacing the project constraints that previously
lived only in the assistant's persistent memory, and (v) documenting
the 2026-04-20 disposal of FB-10 / FB-12 / FB-13.

## Why a bundle (not one document)

The single-document temptation collides with two constraints:

1. The phase-boundary audit rule (see [SELF_AUDIT_AUTOMATION.md](SELF_AUDIT_AUTOMATION.md))
   requires that every commit closing a sub-phase updates its own slice
   of the bundle without rewriting the others. Splitting by purpose
   keeps merge conflicts local.
2. The historical log (FB-3 … FB-7) grows monotonically, while the
   forward plan (FB-8 / FB-9 / FB-11) churns as decisions land.
   Keeping them in different files makes the churn visible at the
   directory level.

## Read order

1. **[PROJECT_MEMORY_EXPLICIT.md](PROJECT_MEMORY_EXPLICIT.md)** — user
   profile, architecture constraints, workflow rules, performance
   targets, and every other item that previously lived only in the
   assistant's persistent memory. Read this first. *Everything below
   assumes these constraints hold.*
2. **[DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)** —
   historical record of every FB sub-phase already shipped (FB-0 …
   FB-3.2 at time of writing) plus forward-looking anchors for FB-3.3
   … FB-7. Each entry carries the commit anchor, the test delta, the
   audit-document link, and any carry-forward that survived the phase
   boundary.
3. **[EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md)**
   — coordinator plan. High-level description of the three in-scope
   phases, dependency graph, bundle-wide invariants, and pointers to
   the per-phase SDDs. **No calendar timelines.**
4. **Per-phase SDDs** (detail delegated here from the coordinator):
   - [FB8_DISCRIMINATOR_SDD.md](FB8_DISCRIMINATOR_SDD.md) — local-
     boost vs global-tilt discrimination + aberration kernel +
     discriminator statistic.
   - [FB9_MASSIVE_NEUTRINO_SDD.md](FB9_MASSIVE_NEUTRINO_SDD.md) —
     `MassiveNeutrinoBackground`, phase-space grid, registry
     integration.
   - [FB11_INFERENCE_DRIVER_SDD.md](FB11_INFERENCE_DRIVER_SDD.md) —
     emcee driver, `bayes_factor`, convergence diagnostics,
     11-type summary run.
5. **[SCOPE_DECISIONS.md](SCOPE_DECISIONS.md)** — append-only log of
   what was discarded (FB-10 / FB-12 / FB-13) and the re-entry
   procedure.
6. **[SELF_AUDIT_AUTOMATION.md](SELF_AUDIT_AUTOMATION.md)** — the
   per-PR self-audit protocol, the docs-update checklist that rides
   alongside every PR, and the `.claude/hooks/check_phase_boundary_audit.py`
   trigger pattern that binds the two together.

## Cross-reference map

| Document | References out to | Referenced by |
|---|---|---|
| INDEX.md (this file) | all bundle docs + parent plan | — |
| PROJECT_MEMORY_EXPLICIT.md | parent plan §10, audit prompt template | every PR must honour it |
| DEVELOPMENT_LOG_FB3_TO_FB7.md | audit docs per phase, parent plan §4 | coordinator plan §0 |
| EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md | SELF_AUDIT_AUTOMATION, SCOPE_DECISIONS, three per-phase SDDs, parent plan §10 | NEXT_SESSION_PROMPT.md after FB-7 closes |
| FB8_DISCRIMINATOR_SDD.md | SELF_AUDIT_AUTOMATION, SCOPE_DECISIONS, parent plan D1 / D4 / D9 | coordinator plan §5 |
| FB9_MASSIVE_NEUTRINO_SDD.md | SELF_AUDIT_AUTOMATION, parent plan D7 / D8 | coordinator plan §5 |
| FB11_INFERENCE_DRIVER_SDD.md | SELF_AUDIT_AUTOMATION, parent plan D8 | coordinator plan §5 |
| SCOPE_DECISIONS.md | coordinator plan §7, INDEX | coordinator plan, every SDD |
| SELF_AUDIT_AUTOMATION.md | `.claude/hooks/check_phase_boundary_audit.py`, [AUDIT_PROMPT.md](../../audits/AUDIT_PROMPT.md) | every PR in the plan |

## Update protocol (bundle-wide)

Every PR that touches any document in this bundle **must** also:

1. Append to the affected slice of [DEVELOPMENT_LOG_FB3_TO_FB7.md](DEVELOPMENT_LOG_FB3_TO_FB7.md)
   (or, after FB-7, a successor `DEVELOPMENT_LOG_FB8_ONWARD.md`) a new
   row with its commit hash, test delta, and audit-document link.
2. Update the PR's phase row in the per-phase SDD with an
   actual-vs-planned annotation (`✅ shipped @ <hash>` or `⚠ descope —
   <reason>`).
3. Re-run the self-audit template in [SELF_AUDIT_AUTOMATION.md §3](SELF_AUDIT_AUTOMATION.md)
   and attach the result as a fenced block to the PR's audit document.

A PR that claims "FB-N.k complete" without performing all three
updates is rejected by the phase-boundary hook described in
[SELF_AUDIT_AUTOMATION.md §5](SELF_AUDIT_AUTOMATION.md).

## Terminology pin

Throughout this bundle:

- **Global tilt** = cosmological tilt between species rest frame and
  Bianchi ``n^a`` frame; parametrised by `(β_cosmo, v̂_cosmo)`. This
  is what FB-3 ships. Internal SSOT storage: rapidity (parent plan
  D4 = (a)); velocity exposed as derived property.
- **Local boost** = observer peculiar-motion Lorentz boost between
  the species rest frame (or the Bianchi rest frame at the observer's
  location) and the actual measurement frame (Sun / spacecraft
  barycentric); parametrised by `(β_obs, v̂_obs)`. This is what
  **FB-8** introduces — FB-3 through FB-7 conflate them into a single
  vector, and that conflation is the primary gap addressed by the
  extended plan.
- **Observer-sky ℓ-ℓ' mixing** = the ℓ-mode coupling matrix
  `K_{ℓℓ'}(β_obs)` induced by aberration + Doppler boosting when the
  Bianchi-rest-frame spectrum is observed in the local-boost frame
  (Challinor & van Leeuwen 2002; Planck XXVII 2013).
- **Discriminator** = the likelihood-ratio statistic `Λ(data; H_obs,
  H_cosmo)` that separates a kinematic-dipole-only signal from a
  Bianchi-anisotropy signal, shipped in [FB8_DISCRIMINATOR_SDD.md §6](FB8_DISCRIMINATOR_SDD.md).
- **Direction-dependent likelihood** = a likelihood whose pdf
  conditions on both the Bianchi axis orientation and the observer's
  peculiar-velocity axis (which are *a priori* different), such that
  marginalisation is carried out over each independently.

## Out-of-scope pointer

Three phases that appeared in earlier drafts of this bundle
(FB-10 survey integration, FB-12 lensing / ISW, FB-13 second-order
tilt) were discarded on 2026-04-20. Rationale and re-entry procedure
are in [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md); the coordinator
plan §7 cross-links each.
