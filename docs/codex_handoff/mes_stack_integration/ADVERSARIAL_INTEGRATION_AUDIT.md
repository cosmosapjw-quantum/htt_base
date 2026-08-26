# MES methodology stack-integration adversarial audit

## Exact integration identity

```yaml
repository: cosmosapjw-quantum/htt_base
branch: analysis/mes-methodology-stack-integration-20260826
integration_merge_commit: 1ace5692bb6778ee8d5b99c112fc84dc2ec8cb72
first_parent_PR412: 4733a4c6dbc638372dee7f99ac38f39dba56d933
first_parent_tree: 33672a84a6f94983a32e575edfb9c8ecb3f70613
second_parent_PR411: 5a3825f903546891fd90e3d708481707d59babf4
second_parent_tree: f51852334634405830f9a9cfa399b334f1efcff2
PR404_plan_source: 14bbb5bb264caa62fd47eb7cd7863f0a3367b1ea
PR403_observed_evidence_source: 883a7cf41116e6740b1bac9b76a5e9c6b3fd188e
```

## Verdict

```yaml
repaired_data_stack: INTEGRATED_AS_FIRST_PARENT
MES_recovery_package: INTEGRATED_AS_SECOND_PARENT_EXACT_PACKAGE
PR314_observed_evidence: EXACT_SOURCE_IMPORT
PR315_plan: EXACT_SOURCE_IMPORT
canonical_DAG_changed: false
science_code_changed: false
observed_data_executed: false

implementation_ready: false
ready_after:
  - exact-head integration CI
  - fresh-context P0=0/P1=0
  - explicit human acceptance
```

The split ancestry between PR #411 and repaired PR #412 is closed by a real
two-parent merge lineage. The exact PR #411 package is imported unchanged.
The PR #403 executed result and PR #404 repair plan are imported as exact source
artifacts, not as stale code branches.

## Scientific spine

The controlling chain remains:

```text
verified MES anchors
→ direction-indexed scalar fields
→ O(3)-typed vector/STF moments
→ row-equivariant finite calibration
→ physical depth response
→ local-boost/global-tilt identification or typed abstention
```

PR-314's `133/301 = 19/43` result remains an executed generic low-ell benchmark
control. It is not relabelled as an MES result.

PR-321's HSC SACC remains a scalar tomographic control. It is excluded from the
directional low-z candidate set because `cl_ee` has no direction or m-phase.

## Why open PRs are not all merged

Git branch ancestry is not equivalent to scientific content authority. PR-385
and PR-386 are already ancestors. PR-387/388 and PR-403/404 diverge from later
repairs; merging them wholesale could overwrite current code and status. Their
useful content is assigned exact source dispositions. PR-405..408 remain a
separate theory-closeout track; PR-411 already carries the selected method
receipts needed here.

The machine ledger is controlling. Closing or merging source PRs remains a
human action after the final disposition receipt.
