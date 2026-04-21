# VER2 Prompt List 03

## BASS-First Completion Follow-up

**Status**: post-VER2 follow-up packet list  
**Authority**: `docs/ver2_upgrade/*`  
**Purpose**: prioritize `htt/bass/*` completion before legacy figure/doc cleanup or optional H/M/T serializer work

## 0. Why this list exists

Prompt lists 01 and 02 are closed. `BF-01B-HCORE` has removed the bounded Lowell bridge from the production Tier-B route, and `BF-02B-SEED` has closed the native startup/seed-injection gap. The largest remaining implementation debt is now concentrated inside `htt/bass/*` around unresolved angular reconstruction plus O-lane covariance/morphology outputs that remain explicit proxy/no-claim surfaces.

This list does not reopen settled VER2 ownership rules. It only reorders the remaining follow-up work so that `htt/bass/*` reaches the highest feasible completion level first.

## 1. Global rules

1. `docs/ver2_upgrade/*` remains the only semantic SSOT.
2. Do not silently route new work back onto `einstein_bianchi.py` or other reduced compatibility owners.
3. Do not let BASS absorb HTT posterior ownership, MIO truth-certificate ownership, or TSC runtime allow/block ownership.
4. Do not promote proxy morphology, diagonal covariance, or warn-only validation to science-grade claims.
5. Preserve observer-neutral BASS outputs until a downstream packet explicitly owns the interpretation layer.

## 2. Reordered packet table

| Packet | Goal | Depends on | Lane | Commit prefix |
|---|---|---|---|---|
| `BF-01B-HCORE` | replace the bounded Lowell Tier-B core with an S1/S2-native executable hierarchy/RHS path | closed VER2 packets only | `B` | `V2-B1:` |
| `BF-02B-SEED` | make startup manifold, perturbative seed projection, and runtime IC injection live | `BF-01B-HCORE` | `B` | `V2-B2:` |
| `BF-03B-ANG` | close `project_from_angular_samples` / `reconstruct_on_sphere` and the observer-neutral angular bridge | `BF-02B-SEED` | `B` | `V2-B3:` |
| `BF-04B-COV` | replace `sparse_mode_block_proxy` / first-pass covariance logic with a validated low-`ell` morphology-covariance path | `BF-03B-ANG` | `B` | `V2-B4:` |
| `BF-05B-VAL` | promote BASS-focused null/injection/cutoff validation from warn-only to executable evidence where justified | `BF-04B-COV` | `B/V` | `V2-B5:` |
| `BF-06B-LIKE` | retarget `bass/observer`, `bass/likelihood`, and `bass/inference` onto the completed BASS physics path and fence residual surrogates | `BF-05B-VAL` | `B` | `V2-B6:` |
| `BF-07X-CLEANUP` | only after BASS-first closure: legacy figures, top-level docs sync, optional H/M/T serializer cleanup | `BF-06B-LIKE` | `X` | `V2-X1:` |

## 3. Packet intent

### `BF-01B-HCORE`

**Write scope**

- `htt/bass/hierarchy/*`
- `htt/bass/runtime/*`
- `htt/bass/background/*`
- `htt/bass/transport/*`
- `htt/bass/closure/*`
- selected `htt/bass/forward/*`
- related tests

**Intent**

Make the Tier-B executable path physically owned by the VER2 S1/S2 stack instead of the shipped Lowell bridge. This is the highest-priority BASS debt because it is the main reason `htt/bass/*` is still only conditionally complete.

**Required closure**

- S1 background evolution is the runtime owner.
- S2 frame split / transport / collision / visibility surfaces are the hierarchy owner.
- Tier-B runtime no longer uses the Lowell hierarchy/integrator as the hidden physics core.
- compatibility paths may remain, but must not be on the production route.

### `BF-02B-SEED`

**Write scope**

- `htt/bass/hierarchy/*`
- `htt/bass/closure/*`
- `htt/bass/runtime/*`
- selected `htt/bass/background/*`
- related tests

**Intent**

Close the seed/startup gap that VER2 left explicit: quadrupole startup manifold, perturbative seed solver, and runtime IC injection must become live rather than logged metadata.

### `BF-03B-ANG`

**Write scope**

- `htt/bass/los/*`
- `htt/bass/runtime/*`
- `htt/bass/observational/*`
- selected `htt/bass/forward/*`
- related tests

**Intent**

Replace the remaining angular bridge stubs with executable, observer-neutral angular reconstruction so that O-lane products are built from real angular content rather than final-slice proxies alone.

### `BF-04B-COV`

**Write scope**

- `htt/bass/observational/*`
- `htt/bass/spectrum/off_diagonal_covariance.py`
- selected `htt/workspace/contracts/*`
- related tests

**Intent**

Replace explicit proxy morphology/covariance status where possible with a validated low-`ell` basis reduction and better-founded covariance/nuisance handling. If full promotion is still unjustified, narrow the proxy region instead of silently overclaiming.

### `BF-05B-VAL`

**Write scope**

- selected `htt/bass/*`
- `htt/workspace/contracts/*`
- `htt/scripts/*`
- validation docs / manifests
- related tests

**Intent**

Close the BASS-centered validation gap: nulls, injections, cutoff campaigns, Tier A↔Tier B evidence, and observer-neutral recovery checks should move from registry-only or warn-only status toward executable evidence.

### `BF-06B-LIKE`

**Write scope**

- `htt/bass/observer/*`
- `htt/bass/likelihood/*`
- `htt/bass/inference/*`
- related tests

**Intent**

Only after the BASS physics path is completed, retarget observer/likelihood/inference onto it. This packet must fence or retire residual surrogate/mock routes instead of letting them coexist ambiguously with the completed physics path.

## 4. Parallel policy

1. `BF-01B-HCORE`, `BF-02B-SEED`, and `BF-03B-ANG` are serial. They all touch the same solver spine.
2. `BF-04B-COV` may start only after `BF-03B-ANG` lands.
3. `BF-05B-VAL` may run read-only prep during `BF-03B-ANG` and `BF-04B-COV`, but write work starts only after `BF-04B-COV`.
4. `BF-06B-LIKE` is blocked on `BF-05B-VAL`.
5. Legacy figure/doc cleanup is explicitly deprioritized until `BF-06B-LIKE` closes.

## 5. Immediate next action

`BF-01B-HCORE` and `BF-02B-SEED` are now closed in the execution ledger. If the goal is to
maximize `htt/bass/*` completion, the next packet is:

1. `BF-03B-ANG`

Only after `BF-03B-ANG` and the remaining serial solver-spine packets land should any
new non-BASS follow-up packet be considered.
