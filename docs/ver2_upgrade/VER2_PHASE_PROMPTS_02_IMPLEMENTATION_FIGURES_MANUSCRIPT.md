# VER2 Prompt List 02

## Actual Implementation / Figures / Manuscript / Commit Automation

**Status**: execution packet list after skeleton pre-implantation  
**Authority**: `docs/ver2_upgrade/*`  
**Precondition**: `VER2-V0` barrier closed and prompt list 01 packets merged or at least locally integrated without schema conflict

## 0. Operating rule

This prompt list is for real code, validation campaigns, figures, and manuscript upgrades. Use it only after the relevant skeleton packet exists. Each packet remains bounded to one lane.

## 1. Common implementation contract

Every packet must follow this sequence:

1. Re-read the assigned ver2 authority docs twice.
2. Read the local skeletons and unresolved audit notes.
3. Run three separate validation lanes before editing:
   - internal docs + internal literature,
   - web CRAG using primary sources,
   - silent CoT + integrated phys-math-code audit.
4. Produce at least three candidate implementations.
5. Select one by divergence -> verification -> convergence.
6. Implement code and tests.
7. Run static audit and then targeted dynamic validation appropriate to the packet.
8. If failures remain, repair and re-audit up to five loops.
9. Update ledgers, audits, carry-forward, and next-session prompt.
10. Commit the packet if and only if its phase gate is green.

## 2. Global hard requirements

1. No packet may edit outside its write scope.
2. No packet may bypass the claim tier.
3. No packet may silently downgrade a physics requirement to a diagnostic surrogate.
4. No packet may ship a figure/table without a manifest-backed artifact.
5. If a conflict between docs is discovered, stop and reopen the supervisor barrier packet instead of improvising locally.

## 3. Standard packet footer

Every implementation prompt must end with:

- exact files changed,
- exact tests run,
- audit verdict,
- remaining caveats,
- commit subject,
- next blocked dependency, if any.

## 4. Packet table

| Packet | Phase | Parallel after | Lane | Commit prefix |
|---|---|---|---|---|
| `IM-00` | `VER2-V0` reopen only if needed | supervisor only | supervisor | `V2-C0:` |
| `IM-01S1` | `VER2-V1` | skeleton `SK-01S1` | `S1` | `V2-S1:` |
| `IM-02S2` | `VER2-V2` | `IM-01S1` | `S2` | `V2-S2:` |
| `IM-03S3A` | `VER2-V3` Tier B executable solver | `IM-02S2` | `S3` | `V2-S3:` |
| `IM-03S3B` | `VER2-V3` Tier A validation solver | `IM-03S3A` or parallel read-only prep | `S3` | `V2-S3:` |
| `IM-04O` | `VER2-V4` | `IM-03S3A` | `O` | `V2-O1:` |
| `IM-05T` | `VER2-V5` | `SK-05T`,`SK-01C` | `T` | `V2-T1:` |
| `IM-06H` | `VER2-V6` | `SK-06H`,`SK-01C` | `H` | `V2-H1:` |
| `IM-07M` | `VER2-V7` | `SK-07M`,`SK-01C` | `M` | `V2-M1:` |
| `IM-08V` | `VER2-V8` | `IM-03S3A`,`IM-04O`,`IM-05T`,`IM-06H`,`IM-07M` | `V` | `V2-V1:` |
| `IM-09D-FIG` | `VER2-V9` figure/export path | `IM-08V` | `D` | `V2-D1:` |
| `IM-10D-MAN` | `VER2-V9` manuscript path | `IM-09D-FIG` | `D` | `V2-D1:` |

## 5. Implementation prompts

### `IM-01S1` Solver Core Geometry / Background

**Write scope**

- `htt/bass/background/*`
- `htt/bass/species/*`
- `htt/bass/tilt/*`
- related tests

**Prompt**

```text
Implement the actual VER2-V1 geometry/background packet using docs/ver2_upgrade as SSOT.

Scope:
- all-eleven-type Bianchi algebra and metadata,
- tetrad connection / curvature operators,
- constraints and IC builders,
- background RHS and diagnostics,
- tilted and orthogonal branches with explicit admissibility and metadata.

Verification lanes:
1. Internal docs + internal literature:
   - solver SDD/core docs
   - local reference note
2. Web CRAG:
   - Pontzen-Challinor 2007
   - Ma-Bertschinger 1995
   - Wainwright-Ellis background conventions as needed
3. Silent integrated phys-math-code audit.

Candidate generation:
- produce 3 implementation candidates,
- choose one with minimal semantic surface and maximal alignment with the SDD.

Validation requirements:
- Jacobi identity,
- class A / class B invariants,
- FLRW limit,
- orthogonal/tilted branch metadata,
- constraint residual plumbing.

If any placeholder or FLRW-only shortcut remains on the production path, repair it before committing.
Run up to 5 repair loops, update ledgers/audit docs, then commit `V2-S1:`.
```

### `IM-02S2` Radiation / Collision / History

**Write scope**

- `htt/bass/hierarchy/*`
- `htt/bass/transport/*`
- `htt/bass/collision/*`
- `htt/bass/recombination/*`
- `htt/bass/closure/*`
- related tests

**Prompt**

```text
Implement the actual VER2-V2 packet: photon geodesic transport, PSTF radiation multipoles, electron-frame Thomson tensor, visibility/reionization wiring, and IC compatibility.

Hard physics rules:
- transport in n^a frame,
- collision/source/visibility in electron frame,
- E/B remains explicit state information,
- low-ell truncation may be used but must be documented and convergence-tested,
- scalar recombination history is allowed only as an explicit first-pass approximation.

Verification lanes:
1. solver SDD/core docs + local reference note,
2. web CRAG on Pontzen-Challinor, HyRec/HyRec-2, and related transport/recombination references,
3. silent integrated phys-math-code audit.

Dynamic checks:
- FLRW low-ell recovery,
- frame-split metadata propagation,
- no FLRW-only collision shortcut,
- basic visibility/reionization event detection,
- cutoff sensitivity where applicable.

Repair up to 5 loops, then commit `V2-S2:`.
```

### `IM-03S3A` Tier B Executable Low-`ell` Solver

**Write scope**

- `htt/bass/los/*`
- `htt/bass/spectrum/*`
- `htt/bass/runtime/*`
- `htt/bass/integration/*`
- selected `htt/bass/forward/*`
- related tests

**Prompt**

```text
Implement the executable Tier B low-ell solver path first, exactly as a bounded research-grade path, not as a fake universal solver.

Scope:
- runtime orchestration,
- neutral `SolverCoreOutput`,
- anisotropic source-to-observer propagator,
- low-ell output assembly,
- cutoff/convergence campaign hooks,
- reproducibility metadata,
- Route-B-like sentinels only as validation tags, not as hidden physics owners.

Verification lanes:
1. solver SDD/core + observables contract,
2. web CRAG on solver suitability / known low-ell references / Planck low-ell context,
3. silent integrated phys-math-code audit.

Dynamic checks:
- executable example configs,
- metadata completeness,
- deterministic artifacts,
- no observational interpretation in BASS outputs,
- convergence and cutoff hooks actually invoked.

Choose among at least 3 implementation candidates and justify the selected one in the audit note. Commit `V2-S3:`.
```

### `IM-03S3B` Tier A Validation Solver

**Write scope**

- same as `IM-03S3A`, but no shared-schema edits

**Prompt**

```text
Implement Tier A as the validation-grade angular truth path that cross-checks Tier B. Treat this as a validation upgrade, not a requirement to replace Tier B as the first research executable.

Requirements:
- no overlap edits with unrelated lanes,
- explicit comparison hooks between Tier A and Tier B,
- no silent promotion of one tier over the other without validation evidence.

Verification lanes and 5-loop repair policy are mandatory. Commit `V2-S3:`.
```

### `IM-04O` Observable Atlas / Covariance / MES / xQPiFG

**Write scope**

- `htt/bass/observational/*`
- selected `htt/bass/spectrum/off_diagonal_covariance.py`
- selected `htt/workspace/contracts/*`
- related tests

**Prompt**

```text
Implement VER2-V4 using the atlas, observables, and MES documents as authority.

Scope:
- ObservableVector extraction,
- AtlasEntryLite production,
- sparse BiPoSH/off-diagonal covariance builder,
- FullCovMESReport,
- xQPiFG reporting objects and gates.

Hard rules:
- diagonal C_ell is not sufficient compression,
- rank failure is no-claim,
- local/global degeneracy must be represented explicitly,
- all outputs carry manifest and sky-support metadata.

Verification lanes:
1. internal docs and local contracts,
2. web CRAG on BiPoSH/statistical-isotropy references and covariance handling,
3. silent integrated phys-math-code audit.

Dynamic checks:
- isotropic limit gives zero L>0 BiPoSH,
- PSD and symmetry checks,
- rotation-covariance or equivalent invariant checks,
- report cards do not overclaim.

Repair up to 5 loops and commit `V2-O1:`.
```

### `IM-05T` TSC Active Service

**Write scope**

- `htt/tsc/*`
- related tests

**Prompt**

```text
Implement VER2-V5 with TSC kept strictly inside its authority boundary.

Scope:
- chart domain and admissibility,
- residual/defect reports,
- trace-source bridge,
- source-to-channel adequacy budgets,
- upgrade advisor,
- no-overclaim lint,
- adequacy overlay exporter.

Forbidden outcomes:
- TSC final allow/block,
- TSC evidence correction,
- TSC full spin-2 or family-identification claim.

Verification lanes:
1. TSC docs + v4 ownership rules,
2. web CRAG where chart-domain or admissibility references are needed,
3. silent integrated phys-math-code audit.

Dynamic checks:
- invalid-domain blocking,
- label grammar,
- no-overclaim vocabulary lint,
- source/propagation split preserved in outputs.

If solver-coupled adapters are not yet available, implement and validate the solver-independent TSC core first and record the adapter binding as carry-forward rather than blocking the packet. Commit `V2-T1:` after up to 5 repair loops.
```

### `IM-06H` HTT Directional / Model-Dependent Production

**Write scope**

- `htt/htt/htt/infer/*`
- `htt/htt/htt/integration/*`
- selected `htt/htt/htt/bridge/*`
- related tests

**Prompt**

```text
Implement VER2-V6 as the HTT-owned model-dependent layer.

Scope:
- directional likelihood,
- local-boost/global-tilt/Bianchi discrimination,
- matched-complexity and null-competition gates,
- posterior/evidence with explicit manifest and caveat propagation,
- production axis gating.

Hard rules:
- HTT owns posterior/evidence,
- no MIO certificate merge,
- no TSC posterior correction,
- diagnostic axes cannot become production axes without sky-support and mock-coverage gates.

Verification lanes:
1. ver2 docs + local HTT code,
2. web CRAG on Planck low-ell likelihood context and SI/local-boost references,
3. silent integrated phys-math-code audit.

Dynamic checks:
- production axis blocks when prerequisites are absent,
- null competition and PPC/LOOCV hooks remain explicit,
- outputs remain model-dependent and distinct from MIO.

If live solver outputs are not ready, implement contract-complete shell logic, gating, and caveat propagation first; leave solver binding explicit in carry-forward. Commit `V2-H1:`.
```

### `IM-07M` MIO Observatory

**Write scope**

- `htt/mio/*`
- related tests

**Prompt**

```text
Implement VER2-V7 as the model-independent observatory lane.

Scope:
- directional coherence,
- non-parametric shear extraction,
- FLRW tension,
- evidence anatomy,
- predictive residual atlas,
- production-status aware MioCertificate outputs.

Hard rules:
- MIO is not posterior,
- MIO is not evidence owner,
- MIO is not truth certificate,
- covariance, atlas, and null-mock prerequisites must be enforced explicitly.

Verification lanes:
1. xQPiFG + v4 docs + local MIO code,
2. web CRAG on SI-violation / covariance / coherence references,
3. silent integrated phys-math-code audit.

Dynamic checks:
- diagnostic-only downgrade when prerequisites are missing,
- no schema path to merge with HTT evidence,
- certificate caveats are explicit.

If atlas/covariance/null-mock inputs are not ready, implement production-status logic and diagnostic-only infrastructure first; record blocked estimators explicitly in carry-forward. Commit `V2-M1:`.
```

### `IM-08V` Validation Campaigns / Hostile Audit

**Write scope**

- selected `htt/workspace/contracts/*`
- `htt/scripts/*`
- validation docs / manifests

**Prompt**

```text
Implement VER2-V8 as the cross-lane validation and hostile-audit phase.

Scope:
- theorem-to-test map,
- null ensembles,
- synthetic injections,
- campaign registry,
- hostile review runbooks,
- no-claim / downgrade / quarantine handling.

Every campaign must include:
- baseline reproduction test,
- edge/adversarial test,
- physics sanity test,
- numerical stability or sensitivity test,
- regression test.

Verification lanes:
1. internal docs and all phase audit notes,
2. web CRAG to verify cited theorems or methodological references when needed,
3. silent integrated phys-math-code audit.

Commit `V2-V1:` only after the registry and at least the minimal campaign set are real.
```

### `IM-09D-FIG` Figures / Exporters

**Write scope**

- selected `scripts/*`
- `figures/*`
- selected `docs/ver2_upgrade/*`

**Prompt**

```text
Implement the figure/export path only after manifest-backed artifacts exist.

Scope:
- artifact-to-figure exporters,
- figure manifest checks,
- gallery topic mapping,
- paper JSON/MD/LaTeX table exporters.

Hard rule:
- no figure from a non-manifest artifact,
- no caption stronger than the claim tier,
- no manual status numbers.

Verification lanes:
1. internal docs and artifact manifests,
2. web CRAG for any figure-linked literature claim,
3. silent integrated phys-math-code audit.

Commit `V2-D1:`.
```

### `IM-10D-MAN` Manuscript Upgrade

**Write scope**

- `docs/manuscript/*`
- selected `docs/ver2_upgrade/*`
- selected exporters only

**Prompt**

```text
Implement the manuscript-upgrade phase only after figures/exports are manifest-backed.

Scope:
- chapter insertions,
- result-pack to manuscript mapping,
- claim-tiered wording,
- citation queue closure,
- appendix / table / figure references.

Hard rules:
- no geometry claim from scalar-only summaries,
- no MIO-as-truth language,
- no TSC-as-solver language,
- all status values generated from the shared snapshot.

Verification lanes:
1. internal docs, manifests, and generated artifacts,
2. web CRAG to verify all external citations used in new text,
3. silent integrated phys-math-code audit.

Repair up to 5 loops, update all ledgers, and commit `V2-D1:`.
```

## 6. Recommended parallel batches

### Batch 1

- `IM-05T`
- `IM-06H`
- `IM-07M`

### Batch 2

- `IM-01S1`

### Batch 3

- `IM-02S2`

### Batch 4

- `IM-03S3A`

### Batch 5

- `IM-04O`

### Batch 6

- `IM-08V`

### Batch 7

- `IM-09D-FIG`
- `IM-10D-MAN`

## 7. Phase-specific promotion criteria

### Solver-side promotion

- `IM-01S1` green: all-11-type algebra and background contracts are real.
- `IM-02S2` green: frame split is real and tested.
- `IM-03S3A` green: neutral executable output exists.
- `IM-03S3B` green: Tier A cross-check is wired.

### Statistics / inference promotion

- `IM-04O` green: covariance-aware observable substrate exists.
- `IM-05T` green: overlay and no-overclaim logic exist.
- `IM-06H` green: HTT directional production gates exist.
- `IM-07M` green: diagnostic-only vs production-grade MIO split is real.

### Final promotion

- `IM-08V` green: theorem-to-test map and campaign registry are active.
- `IM-09D-FIG` green: figures are manifest-backed.
- `IM-10D-MAN` green: manuscript wording and citations match claim tiers.

## 8. Exit condition for prompt list 02

Prompt list 02 is complete only when:

1. every phase has a real implementation commit,
2. every phase has a dated audit note,
3. every figure/table is manifest-backed,
4. manuscript text matches the actual implemented claim tier,
5. no unresolved shared-schema conflict remains.

## 9. Post-Closure Handoff

Prompt list 02 is historically complete and should not be rewritten to
hide that closure.

If follow-up work must prioritize `htt/bass/*` completion instead of
legacy D/H/M/T cleanup, switch to:

- `docs/ver2_upgrade/VER2_PHASE_PROMPTS_03_BASS_COMPLETION.md`

That follow-up list deliberately reorders the remaining work so that the
BASS solver spine closes before legacy figures, top-level doc sync, or
optional serializer cleanup.
