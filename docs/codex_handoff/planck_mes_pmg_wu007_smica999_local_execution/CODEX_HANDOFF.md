# PMG-WU-007 local execution handoff — SMICA CMB-only 999 robustness

## Status

```yaml
repository: cosmosapjw-quantum/htt_base
accepted_predecessor_branch: changeset/planck-mes-wu006-admission-staging-20260829
accepted_predecessor_sha: 242eb4b9904a0c5d8514f3b50c7341d4837d71f5
accepted_predecessor_tree: 86c580bbdd9d465992b2db6532d1086e1ec1ce9a
accepted_predecessor_pr: 434
package_branch: changeset/planck-mes-wu007-smica999-preflight-20260829
work_unit: PMG-WU-007
package_state: PREFLIGHT_AND_EXECUTION_CONTRACT_ONLY
science_execution_in_this_commit: false
remote_download_required: false
github_actions_required: false
```

This package binds the already accepted PMG-WU-006 observer-irrep result to one separate CMB-only 999-row robustness lane. It does not replace the paired-300 primary, does not start PMG-WU-008, and does not authorize physical-source claims.

## Read first

```text
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/AUTHORITY_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/DATA_AVAILABILITY_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/WU007_EXECUTION_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/EVIDENCE_ADAPTIVE_CLAIM_ENVELOPE.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/REFEREE_FINDINGS_ROUTE.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/INVARIANT_TEST_MATRIX.yaml
```

Then inspect only the directly affected carrier/operator/reducer surfaces and their focused tests. Do not sweep unrelated data programmes or old WU-007 preflight branches.

## User policy

Do not query, rerun, or inspect GitHub Actions. Use local tests, local replay, one independent fresh review, and exact remote content readback after push.

No additional network download is permitted. The real-host inventory reports all required Planck CMB rows present. The remaining twelve inventory destinations elsewhere in the project are local transform/placement gaps and are outside this work unit.

## First commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git fetch origin --prune
git switch changeset/planck-mes-wu007-smica999-preflight-20260829
git pull --ff-only

git cat-file -e 242eb4b9904a0c5d8514f3b50c7341d4837d71f5^{commit}
test "$(git rev-parse 242eb4b9904a0c5d8514f3b50c7341d4837d71f5^{tree})" = "86c580bbdd9d465992b2db6532d1086e1ec1ce9a"
git merge-base --is-ancestor 242eb4b9904a0c5d8514f3b50c7341d4837d71f5 HEAD

python scripts/validate_planck_mes_pmg_wu007_smica999.py --check-git
python -m pytest -q tests/contracts/test_planck_mes_pmg_wu007_smica999.py tests/integration/test_planck_mes_smica999_preflight.py

python - <<'PY'
import json
from pathlib import Path
terminal = json.loads(Path("docs/generated/planck_mes_irrep_analysis/terminal.json").read_text())
assert terminal["format"] == "PLANCK_MES_IRREP_ANALYSIS_TERMINAL_V2"
assert terminal["work_unit"] == "PMG-WU-006"
assert terminal["state"] == "SUCCEEDED"
assert terminal["replay_status"] == "MATCH"
assert terminal["raw_maps_reopened"] is False
assert terminal["raw_data_mutation"] is False
assert terminal["claim_promotion"] is False
assert terminal["unresolved_blockers"] == []
assert terminal["next_executable_action"] == "PMG-WU-007"
PY
```

If the exact predecessor is unavailable or differs, stop with `BLOCKED_BY_MOVED_AUTHORITY`. A later PR base tip is not by itself a blocker.

## Local runtime

```bash
export HTT_WORKDIR=/mnt/sn850x2t/htt_base_e2e/workdir
test -d "$HTT_WORKDIR/raw/planck_ffp10"
mkdir -p "$HTT_WORKDIR/analysis/planck_mes_irrep/smica999"
```

Never write beneath `$HTT_WORKDIR/raw`, `$HTT_WORKDIR/downloads`, or `$HTT_WORKDIR/cobaya_packages/data`.

## Step 1 — execute the committed read-only preflight

```bash
python scripts/observed_runs/preflight_planck_mes_smica999.py \
  --workdir "$HTT_WORKDIR" \
  --output-dir docs/generated/planck_mes_smica_cmbonly_999_irrep \
  --private-output "$HTT_WORKDIR/analysis/planck_mes_irrep/smica999/preflight_manifest.json" \
  --execute
```

Required inventory: SMICA CMB IDs 00000..00999 excluding only 00970; exactly 999; 00818 included and semantically admitted; no noise file in the CMB-only route; no partial file; all resolved paths under the raw root. The preflight hashes only row 00818 and does not perform a full raw-tree hash.

## Step 2 — create a fresh implementation branch

After preflight succeeds:

```bash
git switch -c changeset/planck-mes-smica-cmbonly-999-irrep-20260829
```

Write RED tests first for exact row order, zero noise reads, exact operator/layout/frame/units, accepted observation-carrier reuse, same-pass scalar/carrier projection, primary separation, fail-closed completion, and the claim envelope.

## Step 3 — implement the smallest real runner

Add:

```text
scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py
tests/integration/test_planck_mes_smica_cmbonly_999.py
docs/research_program/post_pr327/planck_mes_wu007_registry.yaml
```

The observation row must be copied from the accepted PMG-WU-005/WU-006 carrier package by exact identity. Do not reopen or re-estimate the observation map.

Each of the 999 CMB-only null maps is processed once by the accepted joint-cutsky operator. Capture scalar features and retained 32-component real-harmonic coefficients from that same fit. Do not read a paired noise map, reconstruct a carrier from scalar features, or run a second estimator.

Use checkpoints only with content-bound row/input/operator identities. Preserve incomplete work on failure; do not drop or replace rows.

## Step 4 — compute only the frozen robustness result

Reuse the exact accepted WU-006 coordinate families, tails, reducers and typed-absence policy. Do not alter the registry after seeing the observation.

Write beneath `docs/generated/planck_mes_smica_cmbonly_999_irrep/`. The result is a separate conditional null-ensemble sensitivity diagnostic, not a primary replacement, unconditional p-value, foreground validation, component-separation replication, power study, or physical inference. Rank similarity or extremeness cannot promote the claim envelope.

## Step 5 — local verification and review

Use the risk-scoped commands from the work-unit contract. Do not run the full repository suite unless a distinct uncovered failure is named first.

Generate figures only after numerical results are frozen. The generator emits `PENDING_EXTERNAL_DIRECT_INSPECTION`; an external reviewer must inspect exact figure blobs at single- and double-column widths before `plot_audit.json` can record PASS.

Run one fresh-context, read-only review. At most one targeted repair is allowed. No review-of-review.

A PASS terminal must include: one observation, 999 nulls, 1000 total rows, exact inventory excluding 00970 and including 00818, zero noise reads, primary replacement false, replay MATCH, no raw mutation, no claim promotion, P0=0, P1=0, no blockers, and next action PMG-WU-008.

A preflight, scaffold, partial row set, self-attested figure receipt, or tests-only patch is not PASS.

## Claim policy

Claim levels are evidence-adaptive, not rank-adaptive. WU-007 can advance only the null/systematics-fidelity axis from paired-FFP10 conditional to paired-versus-CMB-only null sensitivity executed. It cannot advance orbit completeness, power, cross-map robustness, or physical identifiability.

## PASS transition

After local replay, fresh review, exact remote readback and clean evidence:

```text
PMG-WU-007 → PMG-WU-008 injection/power study
```

Do not create another planning package.
