# AUDIT_IM-09D-FIG_2026-04-21

## Target

- Packet: `IM-09D-FIG`
- Lane: `D`
- Authority: `docs/ver2_upgrade/*` only
- Goal: close the live figure/export path with manifest-backed result-pack exports, figure sidecars, gallery topic mapping, and figure-manifest auditing, without widening into manuscript-upgrade scope.

## RE2 Read Set

1. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_02_IMPLEMENTATION_FIGURES_MANUSCRIPT.md`
2. `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
3. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
4. `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
5. `docs/ver2_upgrade/audits/AUDIT_SK-09D_2026-04-21.md`
6. `docs/ver2_upgrade/audits/AUDIT_IM-08V_2026-04-21.md`
7. `docs/ver2_upgrade/generated/RESULT_PACK_INDEX.md`
8. `figures/paper/VER2_MANIFEST_INDEX.md`

## Divergence -> Verification -> Convergence

### Candidate A

- Land the local D-lane exporter as-is.
- Rejected:
  - it still synthesized a toy `SolverCoreOutput` / covariance bundle inside the script,
  - it built fake HTT forward bundles by scaling and offsetting observable spectra,
  - it still wrote `docs/manuscript/generated/*`, which exceeds the `IM-09D-FIG` write scope.

### Candidate B

- Replace the fake BASS/HTT inputs with live Tier-B and Tier-A runtime outputs, keep the current figure/result-pack architecture, and confine outputs to `scripts/*`, `figures/*`, and selected `docs/ver2_upgrade/*`.
- Selected:
  - closes the load-bearing mock issue,
  - keeps the packet inside scope,
  - preserves claim-tier and manifest gates.

### Candidate C

- Drop the current exporter and rebuild a smaller D-lane script from scratch.
- Rejected:
  - unnecessary rewrite,
  - higher regression risk,
  - does not improve the contract over Candidate B.

## Contract / Interface Audit

| Surface | Required contract | Pre-packet gap | Outcome |
|---|---|---|---|
| figure exporters | no figure from a non-manifest artifact | script built figures from internal toy solver/covariance state | fixed |
| result-pack exporters | JSON / Markdown / LaTeX packs must reflect live artifact manifests | pack A/C/D content depended on synthetic local bundles | fixed |
| gallery topic map | must resolve to live exported figure bases and source artifact ids | map existed only as dirty local output | fixed |
| caption gate | captions must not exceed claim tier | already implemented, kept and re-verified | pass |
| write-scope honesty | `IM-09D-FIG` must not mutate manuscript-upgrade outputs | script still regenerated `docs/manuscript/generated/*` | fixed |

## Three Verification Lanes

### 1. Internal docs + local code

- Re-read the `IM-09D-FIG` prompt and the existing local exporter/test state.
- Confirmed two adversarial failures:
  - the exporter claimed “live artifact-to-figure export” while sourcing some inputs from script-local toy builders,
  - the local implementation drifted into manuscript-generated outputs that belong to `IM-10D-MAN`.

### 2. Web CRAG

- Not needed for this packet.
- Reason:
  - no new figure-linked literature claim or caption citation was introduced,
  - the packet closes export plumbing and claim-tier enforcement only.

### 3. Integrated phys-math-code audit

- Physics: partial pass
  - the packet does not introduce new physics claims,
  - the exported BASS surfaces now consume the live Tier-B/Tier-A runtime bridge rather than toy arrays.
- Math: pass
  - claim-tier gating, manifest checks, and campaign/export cross-links remain explicit.
- Code: pass
  - live runtime-fed D-lane export path is now in scope,
  - manuscript-generated outputs are no longer touched by this packet.

## Patches

1. `scripts/ver2_artifact_export.py`
   - replaced script-local toy `SolverCoreOutput` / covariance / scaled-forward mocks with live `execute_tier_b_lowell_solver` and `execute_tier_a_validation_solver` inputs
   - derived HTT forward bundles from live `D_ell` / preferred-axis runtime outputs instead of scale/offset placeholders
   - removed `docs/manuscript/generated/*` emission from the D-lane exporter
2. `scripts/test_ver2_artifact_export.py`
   - added a scope-fence test to ensure `IM-09D-FIG` outputs stay outside `docs/manuscript/*`
   - added a regression check that the MIO export path consumes live Tier-A / Tier-B forward references
3. generated D-lane outputs
   - refreshed `docs/ver2_upgrade/generated/*`
   - refreshed `figures/paper/ver2_generated/*`
   - refreshed `figures/paper/VER2_MANIFEST_INDEX.md`

## Failure Modes Rechecked

1. `P0` figure/export surfaces are generated from script-local toy arrays instead of live VER2 artifacts
   - fixed by runtime-fed Tier-B/Tier-A export inputs
2. `P0` a D-lane packet silently mutates manuscript-upgrade outputs
   - fixed by confining exporter outputs to D-lane scope
3. `P1` captions overclaim beyond manifest claim tier
   - still blocked by explicit caption-gate checks
4. `P1` result-pack tables drift from artifact manifests
   - fixed by regenerating from manifest-backed records only
5. `P1` legacy paper figures get silently promoted without manifests
   - still blocked; `VER2_MANIFEST_INDEX.md` keeps 83 legacy figures quarantined

## Verification

- `venv/bin/python -m py_compile scripts/ver2_artifact_export.py scripts/test_ver2_artifact_export.py`
  - passed
- `venv/bin/python -m pytest scripts/test_ver2_artifact_export.py -q`
  - `6 passed`
- `venv/bin/python scripts/ver2_artifact_export.py`
  - passed
  - generated `32` D-lane surfaces and `5` manifest-ready `ver2_generated` figure bases
- `venv/bin/python scripts/ver2_artifact_export.py --check`
  - passed

## Remaining Carry-Forward

- `83` legacy paper figures remain `blocked_no_manifest`; only `figures/paper/ver2_generated/*` is promoted by this packet.
- Generated figure/export assets now exist, but chapter prose, citation closure, and manuscript claim-tier wording still belong to `IM-10D-MAN`.
- Exploratory/diagnostic claim ceilings remain unchanged; `IM-09D-FIG` does not promote them into publication claims.

## Final Judgment

- Verdict: partial pass, packet closed and ready to land in history.
- Implemented now:
  - live manifest-backed D-lane figure/result-pack exports sourced from current VER2 runtime artifacts.
- Do not touch now:
  - manuscript chapter text or `docs/manuscript/generated/*`; that belongs to `IM-10D-MAN`.
