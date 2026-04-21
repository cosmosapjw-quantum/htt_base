# VER2 Prompt List 04

## HTT Parallel Follow-up

**Status**: post-VER2 follow-up packet list  
**Authority**: `docs/ver2_upgrade/*`  
**Purpose**: let HTT continue in parallel with BASS carry-forward without reopening settled VER2 ownership boundaries

## 0. Why this list exists

Prompt lists 01 and 02 are closed, and prompt list 03 closes the BASS-first executable path. What remains for HTT is no longer basic shell installation. The remaining work is HTT-specific inference closure: a dedicated posterior/evidence artifact writer, calibrated local/global discrimination, and a narrower readiness promotion path that upgrades only the shipped Type-I native route when the required hooks exist.

This list does not reopen `IM-06H`. It defines bounded follow-up packets that keep HTT as the owner of posterior/evidence/discrimination while preserving the BASS observer-neutral boundary, the MIO truth-certificate boundary, and the TSC caveat-only boundary.

## 1. Global rules

1. `docs/ver2_upgrade/*` remains the only semantic SSOT.
2. Do not let HTT absorb BASS runtime ownership, MIO certificate ownership, or TSC posterior-correction semantics.
3. Do not treat local/global degeneracy metadata as a calibrated separation result until the corresponding HTT packet lands.
4. Do not promote `diagnostic_only` H-lane outputs to production-ready without live solver/null/PPC/LOOCV evidence.
5. Keep the default path honest: shipped Type-I native support may reach `production_candidate`; broader morphology or non-Type-I science promotion must remain explicit carry-forward unless separately validated.

## 2. Packet table

| Packet | Goal | Depends on | Lane | Commit prefix |
| --- | --- | --- | --- | --- |
| `HTT-A` | add a dedicated HTT-owned posterior/evidence artifact writer and remove legacy-only export dependence | `IM-06H`, `IM-09D-FIG`, `IM-10D-MAN` | `H` | `V2-H2A:` |
| `HTT-B` | calibrate local/global discrimination around response overlap, morphology, and conditional separation outputs | `HTT-A`, `IM-04O`, `IM-08V` | `H/V` | `V2-H2B:` |
| `HTT-C` | tighten readiness promotion so the shipped Type-I native route can emit bounded HTT production-candidate outputs | `HTT-B`, `BF-05B-VAL`, `BF-06B-LIKE` | `H` | `V2-H2C:` |

## 3. Packet intent

### `HTT-A`

**Write scope**

- `htt/htt/htt/integration/*`
- selected `htt/htt/htt/infer/*`
- `htt/htt/tests/*`
- `docs/ver2_upgrade/*` session/ledger updates only

**Intent**

Install an HTT-owned posterior/evidence summary writer so `build_posterior_bundle` no longer depends only on legacy `workspace/results/integrated_pipeline_results.json`. The dedicated artifact remains HTT-owned and may be consumed by MIO only through the cross-check-only bundle contract.

**Required closure**

- HTT can emit a dedicated posterior/evidence summary artifact with an HTT-owned manifest.
- `build_posterior_bundle` can ingest that artifact directly.
- Legacy `integrated_pipeline_results.json` may remain as a compatibility fallback, but it must no longer be the only export path.

### `HTT-B`

**Write scope**

- `htt/htt/htt/infer/*`
- selected `htt/workspace/contracts/*`
- selected validation docs / runbooks
- related tests

**Intent**

Turn the current local/global discrimination shell into a calibrated conditional surface. The target is not blanket family identification; it is a better-founded response-overlap and morphology-aware separation result with explicit no-claim boundaries where calibration remains absent.

**Required closure**

- response-library overlap is no longer a fixed stub,
- morphology-backed overlap metadata exists where the current O-lane artifacts permit it,
- Result Pack B can move from pure diagnostic summary toward bounded conditional discrimination.

### `HTT-C`

**Write scope**

- `htt/htt/htt/infer/*`
- selected `htt/htt/htt/integration/*`
- `htt/htt/tests/*`
- selected `docs/ver2_upgrade/*`

**Intent**

After `HTT-B`, tighten the readiness gate so HTT can issue a bounded `production_candidate` surface for the shipped Type-I native route when live solver/null/PPC/LOOCV hooks exist. This is not full science closure for every morphology family.

**Required closure**

- readiness promotion remains closed-fail,
- shipped Type-I native support can surface as HTT-owned `production_candidate`,
- broader morphology/non-Type-I claims remain explicitly blocked or exploratory.

## 4. Parallel policy

1. `HTT-A` can run immediately in parallel with BASS physics/statistics carry-forward.
2. `HTT-B` should start only after `HTT-A` lands because it depends on HTT-owned artifact surfaces and updated readiness/export semantics.
3. `HTT-C` is blocked on `HTT-B` and the current BASS validation/likelihood floor.
4. None of these packets may reopen MIO or TSC ownership boundaries.

## 5. Immediate next action

The next HTT follow-up packet is:

1. `HTT-A`

After `HTT-A`, the next executable HTT packet is:

1. `HTT-B`

If `HTT-A` is already present in the local workspace, start with `HTT-B`.

Concrete execution handoff for the current local state:

1. `docs/ver2_upgrade/HTT_B_EXECUTION_PROMPT.md`
