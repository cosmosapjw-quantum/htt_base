# Publishable Analysis Pack 2026-06-26

owner: COMMON
implementation_scope: research_program_handoff_pack
claim_tier: diagnostic_only
transfer_source: none_for_pack_code
sky_support_status: not_directional_for_pack_metadata
null_mock_status: synthetic_only
generating_command: manual package scaffold for future publishable novel data analysis
git_commit_or_worktree_state: created from repo state 8e104e573d78fd515044e6c268edb3d46e4c5d51 plus local audit docs
caveats:
- This pack is a research/development handoff and executable synthetic-mechanics harness.
- It does not close K1, K5, K6, PR08-006, or PR10.
- It does not create native solver output or native-atlas-dependent family/classification claims.

## Purpose

This pack turns the external-audit findings and current repo blockers into a concrete next research programme. It is designed to preserve novelty while keeping measurement claims tied to actual data provenance.

The target publishable direction is:

> A rank-aware, transfer-provenance-aware, local/global discrimination analysis of low-ell CMB and low-redshift velocity observables, proving which sectors are identifiable now, calibrating reachable sectors with public E2E and CF4 realization ensembles, and explicitly reporting blind sectors as a theorem-level no-go rather than as missing caveats.

That is stronger than a disclaimer-only programme. The novelty is the combination of:

- rank and blind-sector theorems;
- e-value and max-scan calibration under registered null ensembles;
- direct GR/Boltzmann visibility-kernel bounds for low-ell transfer response;
- CF4 realization-conditioned velocity-field diagnostics;
- a joint artifact that preserves missing sectors rather than silently setting them to zero.

## Contents

```text
README.md
RESEARCH_DIRECTION.md
THEOREM_CANDIDATES.md
BLOCKER_EXECUTION_GUIDE.md
AGENT_ORCHESTRATION.md
SUBAGENT_SYNTHESIS.md
WEB_CRAG_LEDGER.md
CLAIM_LEDGER.yaml
MANIFEST.json
examples/
  k1_e2e_manifest.example.json
  cf4_realization_manifest.example.json
  cf4_release_mock_manifest.example.json
scripts/
  candidate_experiments.py
  validate_blocker_manifest.py
tests/
  test_candidate_experiments.py
  test_blocker_manifest.py
```

## Quick Run

From repo root:

```bash
PACK=docs/research_program/publishable_analysis_pack_2026-06-26
venv/bin/python "$PACK/scripts/candidate_experiments.py" --out "$PACK/outputs/candidate_experiments.json"
venv/bin/python "$PACK/scripts/validate_blocker_manifest.py" "$PACK/examples/k1_e2e_manifest.example.json"
venv/bin/python "$PACK/scripts/validate_blocker_manifest.py" "$PACK/examples/cf4_realization_manifest.example.json"
venv/bin/python "$PACK/scripts/validate_blocker_manifest.py" "$PACK/examples/cf4_release_mock_manifest.example.json"
venv/bin/python -m pytest "$PACK/tests" -q
```

Expected synthetic harness result:

- rank/e-value invariants pass;
- GR/Boltzmann visibility bounds pass;
- local/global response-overlap classifier returns candidate or blocked status by rank, not rhetoric;
- blocker manifests validate required provenance fields.

## What This Pack Allows

Allowed strong statements after real inputs are bound and gates pass:

- the K1 low-ell statistic has a global E2E-calibrated rank p-value under the registered max-scan;
- the K5 bulk-flow coverage includes release-matched cosmic variance and method/depth/frame ablations;
- the K6 curl sector has either a realization-conditioned posterior or an explicit structural no-go;
- the joint PR08-006 artifact reports reachable rank-2 sectors and fail-closed blind sectors with provenance.

Blocked until PR10/native atlas:

- native low-ell solver outputs;
- native-atlas-dependent family/classification language;
- any collapse of scalar diagnostics into geometry claims.
