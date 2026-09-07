# Report A — three-lane operation and existing R4A1E local execution

Date: 2026-09-05
Status: EXECUTION_HANDOFF_NOT_AN_EXECUTION_RECEIPT
Consuming decision: execute the existing R2 supporting-domain contract after K2FR publication, then assess its precise use in the current report.

## 1. Owner-directed division of work

The owner now uses three lanes. Necessary mathematics packages are installed on the local workstation; check the versions actually required by this contract rather than rediscovering or reinstalling every package.

| Lane | Responsibility | Write boundary |
|---|---|---|
| Discussion thread | Scientific scope, interpretation, DAG decisions, acceptance recommendations and owner decisions | Coordination documents and explicit status/comment updates; no claim of local execution |
| Work thread | Bounded source/evidence review, comparison with declared claims, independent response to actual failures, and evidence publication | New isolated evidence branch only when its assignment authorises publication; never edit another lane's running checkout |
| Local Codex | Actual tests, native mathematics/formal execution, logs, hashes and durable local artifacts | Fresh isolated worktree and run directory; preserve main checkout, venv, data and existing evidence |

A separate thread is not automatically a blind review. Record executor/reviewer overlap. Do not give multiple lanes ownership of the same mutable files. Existing completed work is reused, not repeated as a new task.

## 2. Fixed checkpoint and completed work

Repository: `cosmosapjw-quantum/htt_base`.

```yaml
report_pr: 449
report_head_at_intake: f0174dbae1f7ea33cf60541bf59f7553927059bb
report_base_at_intake: 687234128d7c12d04e68aad0f303c21d2d470393
published_repair_pr: 452
published_repair_branch: review/htt-k2fr-returned-repair-20260905-r1
execution_pin: 581d50cb8b8be61ca8ead538d0bf7d75420f9037
execution_tree: 435de757e124410c6f59bd56e709c4af18c8d3ad
repair_parent: f0174dbae1f7ea33cf60541bf59f7553927059bb
K2FR: K2FR_REVIEWED_REPAIR_PUBLISHED_NONCANONICAL
canonical_ledger: T9_V4
canonical_claims: 30
candidate_claims: 40
K5: REVIEW_PDF_DELIVERED_DO_NOT_REBUILD
```

PR #452 contains the four actual repaired files and the returned noncanonical evidence. The archived K2FER1 execution has 40+15=55 PASS, with the original 33 nodes retained and 19 negative fixtures included in that total. K2FR subsequently checked archive identities, the original execution records, four matching forty-ID surfaces, twenty bibliography entries, the five scope dispositions and publication readback. Neither the archived PASS nor K2FR readback is hosted-CI PASS for commit 581d50c.

Published evidence prefix:
`artifacts/research_reports/k2fr_20260905/`.

Important records at the execution pin:

- `K2FR_REVIEW_ANNEX.json`, Git blob `9c242d24e6702f8dbb155401e3d3387bdcc525b9`;
- `authority-bundle/K2F_COMPILATION_RECEIPT.json`, Git blob `87c26b121ff312c6758189f467dbaabe1d963153`;
- `old_to_new_identities.json`, Git blob `e163148f962c55f6b0dc97d23f0a812954a1dbe4`;
- `EVIDENCE_INDEX.json` for the published payload inventory.

Owner/executor-reported digests, not fresh measurements by the discussion thread:

```text
original K2FER1 archive:
8add038012321c7132203ce505c2eb8eec2f35b446ce047d4893fad246c1a70c
returned K2FR review ZIP:
7a9b0e2e99c0f08000f4efc1643993d00b09ebb8284c3389a11aeb3006d84fff
compilation receipt:
0510b3ea21bdca35113d88a9797fb37f86bf645556a84621ec3b50be5838c81e
review annex:
b8c743ca6996f9f027f7da53d02957e1569e486da7e22742c94051b40672213e
```

The review annex retains the five original compiler findings and its `all_conditional_claims_have_assumptions_or_boundary: false` value. Its five `SOURCE_SUPPORTED_SCOPE_BINDING` decisions are separately bound to the generated rows. The compiler did not consume the annex. Do not edit the successful bundle to clear those historical findings.

The discussion thread freshly read both PRs and the published receipt, identity map, relevant annex sections and formal sources. Its shell and independent Python probes both returned ClientError before execution, so it did not independently hash the attached review ZIP or repeat all 73 payload checks. Publication is now connector-readable; this removes the old missing-transport task. No third intake or copy of the four-file repair is requested.

## 3. Exact next task, not a new research programme

Local task ID: `R4A1E_LOCAL_EXISTING_R2`.

Execute the existing contract `CAS-R4A1NF-DOMAIN-R2`, version 2. Its required axes are **SymPy and Lean**, not all installed engines. The four obligations are:

```text
photon_null_decomposition
observer_measured_photon_energy
boosted_observer_unit_timelike
regularized_error_envelope_positive_definite
```

The first two Lean obligations are scalar contractions under the prescribed observer/photon identities, not a newly formalised differential-geometric model. The matrix obligation is the registered general positive-semidefinite-plus-positive-identity regularisation statement. Keep this actual proof scope.

Do not rerun K2FER1, rematerialise its bundle, regenerate K5, run observations, implement a missing physical CMB response, or replace the existing CAS runner. Do not add optional Wolfram/Sage/Singular/Octave axes merely because they are installed. They neither replace a required axis nor turn this R2 contract into an R3 certificate.

The contract binds the original R3 manuscript `HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md`, the convention registry/appendix and T8. It deliberately does **not** bind the whole new revision-2 forty-claim manuscript. Running it at the published child commit is valid only if every registered input still matches. Do not silently replace the original manuscript pin with revision 2. Transfer of the four supporting lemmas to revision 2 is a subsequent scope comparison, not all-forty-claims verification.

## 4. Local Codex execution instructions

### 4.1 Source and workspace

Read this complete handoff, AGENTS.md and the applicable repository-local validation/claim/CAS skills. Use the current native isolation mechanism. No extra subagents are needed for this one runner; if used, obey the existing registered-assignment policy.

Previously supplied local checkout location:
`$HOME/Dropbox/bianchi/htt_base`.
This is a locator to verify, not evidence that the path currently exists or is clean.

Preferred independent work area:
`/mnt/sn850x2t/htt_base_e2e/` on the user's external NVMe.
Choose a unique run/worktree path there, or another explicitly writable isolated local area if that mount is not present. Preserve the existing repository venv and data directories. Never run reset/clean/delete against the main checkout, download archives, historical evidence or another worktree.

Inspect the actual repository identity and worktree list before creating a fresh detached worktree at:

```text
581d50cb8b8be61ca8ead538d0bf7d75420f9037
```

A normal local fetch to obtain this commit is allowed. Do not merge, rebase, force-push or update a remote branch. If a newer PR head exists, compare its relevant source changes; do not quietly change the execution pin. A coordination-only move of PR #449 does not change the pinned PR #452 source tree.

Require actual `git rev-parse HEAD` and `git rev-parse HEAD^{tree}` to equal the pin and tree above. Record tracked-file cleanliness and the hash of the formal inputs before execution. No fake .git or hand-transcribed verifier code.

### 4.2 Read the existing execution contract and programs

All paths below are read at the execution pin. These Git blob values were read through the connector in the discussion thread; local execution must verify actual bytes.

| Path | Git blob |
|---|---|
| `docs/research_reports/verifiers/r4a1nf/CAS_CONTRACT_R4A1NF_DOMAIN.json` | `225f5ed3ebe161b16371513b35b47a8a52f92b80` |
| `docs/research_reports/verifiers/r4a1nf/CAS_RUN_SPEC_R4A1NF_DOMAIN.json` | `cbb341cd224be947b7951cd5446a7ba511df8255` |
| `docs/research_reports/verifiers/r4a1nf/verify_source_bindings.py` | `5b20612efd6d1a9b080b3386c224939aeb6f1ce4` |
| `.agent-harness/scripts/cas_gate.py` | `a0d5ed80f8714a061b464f0cd179b3dc12fb6942` |
| `.agent-harness/scripts/_harness.py` | `718f8fd9150092326755ae9e5db1793ff32c065f` |
| `docs/research_reports/verifiers/r4a1nf/cas/axes/sympy/axis_program.py` | `bfb92f12687b6447f0b8eca234601f9e5c0402a7` |
| `docs/research_reports/verifiers/r4a1nf/cas/axes/lean/axis_program` | `fe5e451e4cc5cc1f094b6f88194a473cb3ee5181` |
| `formal_mathlib/Egs3V8Mathlib/ReportAConvention.lean` | `da950d0b29f7ab242ff1322e6ae7c794785cc95b` |
| `.github/workflows/report-a-formal-verifiers.yml` | `065a4685559d3f624d65254f3f961e9174c2a095` |

The contract itself enumerates the rest of its input and toolchain hashes. Check all of them, not just this table. Use the existing binding validator; no bypass, in-memory constant mutation or hash repinning.

### 4.3 Use existing native packages at the required versions

```yaml
python: CPython 3.12; record actual patch version
sympy: 1.14.0
mpmath: 1.3.0
lean: leanprover/lean4:v4.31.0
mathlib_commit: fabf563a7c95a166b8d7b6efca11c8b4dc9d911f
mathlib_package_root: formal_mathlib
```

Prefer an already installed matching interpreter/environment and exact Lean/mathlib cache. Do not modify the main `htt_base/venv`. If an isolated environment needs a small missing pinned dependency, resolve it once in the run environment; do not repeat a broad installation or package census. A package being installed is not evidence that its version satisfies this contract.

Set `PY` to the actual matching Python executable. The run spec invokes **python3** by name for the SymPy child. Ensure the selected environment's `python3` resolves to the same CPython 3.12 environment, not the system Python. Record executable paths and versions. The parent's SymPy probe prefers a worktree-local `venv/bin/python` if present; inspect that possibility so a successful probe cannot disguise a different child interpreter.

Set the Lean environment to the pinned toolchain and verify the actual native version. In `formal_mathlib`, inspect the actual `.lake/packages/mathlib` checkout and its commit as well as the top-level manifest. A correct manifest string with a different installed dependency does not prove a matching proof environment. Use matching existing compiled cache artifacts where available. A bounded cache/dependency preparation under the pinned package is allowed; record it separately. Do not run the target theorem independently before the parent-owned CAS run merely to manufacture a prior PASS.

Do not run the generic `cas_gate.py preflight --all`; it would probe axes this contract does not require. The existing parent runner already probes each required axis.

### 4.4 Run the registered source binding, then the parent-owned adjudicator

Let `WT` be the isolated full worktree, `RUN` the external run-artifact directory and `PY` the verified interpreter. Establish these actual values locally; the discussion thread has not executed the following commands.

Use the registered receipt locations in the fresh worktree. If either receipt already exists, preserve it and establish a clean isolated worktree rather than overwriting old evidence.

```bash
cd "$WT"
D=docs/research_reports/verifiers/r4a1nf

"$PY" "$D/verify_source_bindings.py" \
  --contract "$D/CAS_CONTRACT_R4A1NF_DOMAIN.json" \
  --run-spec "$D/CAS_RUN_SPEC_R4A1NF_DOMAIN.json" \
  --adjudicator .agent-harness/scripts/cas_gate.py \
  --out "$D/CAS_SOURCE_BINDINGS_R4A1NF_DOMAIN.json" \
  > "$RUN/source-binding.stdout" 2> "$RUN/source-binding.stderr"
BIND_EXIT=$?
printf '%s\n' "$BIND_EXIT" > "$RUN/source-binding.exit"
```

If that exit is not zero or the receipt has `ok != true`, do not start either axis. Preserve the mismatch path, expected/actual identity and raw receipt. No repair or old-contract substitution is authorised in this execution task.

Only after the source-binding receipt passes:

```bash
"$PY" .agent-harness/scripts/cas_gate.py run-adjudicate \
  --contract "$D/CAS_CONTRACT_R4A1NF_DOMAIN.json" \
  --run-spec "$D/CAS_RUN_SPEC_R4A1NF_DOMAIN.json" \
  --out "$D/CAS_ADJUDICATION_R4A1NF_DOMAIN.json" \
  > "$RUN/adjudication.stdout" 2> "$RUN/adjudication.stderr"
CAS_EXIT=$?
printf '%s\n' "$CAS_EXIT" > "$RUN/adjudication.exit"
```

Record the real exit even under a shell error policy; do not use an unchecked pipe to tee, `|| true`, or a wrapper that converts failures to success. The existing time limits are 600 seconds for the SymPy axis and 3600 seconds for Lean; do not alter them after a timeout.

Do not invoke the stored-result-only `adjudicate` command as a substitute for `run-adjudicate`. The latter actually owns both child processes. Do not run Lean's target outside the parent gate and then report its stored JSON as parent-observed evidence.

The existing parent runner stores child stdout/stderr tails in its JSON, not necessarily complete child transcripts. Preserve exactly what it emits and declare this log-coverage boundary. Do not claim missing full logs were captured, rewrite the frozen runner for prettier logs, or rerun a successful axis merely to duplicate its evidence.

### 4.5 Validate the actual output without expanding its claims

Read both original receipts. Require their contract SHA-256 values to match the actual same contract bytes. Verify all registered source rows, actual child executions, exit/timeout fields, the four exact obligation names, `domain_assumption_diff`, counterexample fields and each axis status.

For an accepted R2 execution component, both required axes must actually run and PASS, with the existing aggregate pass label, no applied exception and no missing axis. An absent child, wrong toolchain, inconclusive payload, timeout or proof error is not a PASS even if another tool is installed. Do not alter the parent result to improve its classification.

Keep the distinction between the runner's `claim_promotion_cas_eligible` field and any overall claim/publication decision. The runner can satisfy one CAS evidence component; it cannot grant scientific validity, novelty, empirical admission or canonical promotion. A failed Lean elaboration can be a formal-source or environment problem, not automatically a physical counterexample. Preserve the exact error and a minimal proposed next action; do not start a new unapproved repair loop.

Recheck actual source bytes and tracked-file status after the run. Untracked receipts/cache artifacts in this isolated worktree are execution products, not scientific-source edits. Do not commit a generated cache or modify tracked source to hide a dirty status.

### 4.6 Local return package

Return the actual original source-binding and CAS receipts, parent command stdout/stderr/exit files, exact interpreter/Lean/mathlib identity, a concise execution receipt and file checksum list. Include changed/missing-source checks. Copy or package them in the durable external run area before ending the session. Do not upload secrets, credentials, complete environment dumps, private unrelated data, or installed package/font binaries.

A matching tool/source dependency checkout is necessary for the run; copying all installed mathematics packages into the result is not. For the source closure, a manifest of the pinned Git files and their hashes is sufficient because the exact commit is already in GitHub.

Use this summary, filled with observed values rather than expectations:

```yaml
r4a1e_local_result:
  assignment: R4A1E_LOCAL_EXISTING_R2
  source_commit: 581d50cb8b8be61ca8ead538d0bf7d75420f9037
  source_tree: 435de757e124410c6f59bd56e709c4af18c8d3ad
  contract_id: CAS-R4A1NF-DOMAIN-R2
  contract_git_blob: 225f5ed3ebe161b16371513b35b47a8a52f92b80
  contract_sha256: null
  actual_python_executable: null
  python_version: null
  sympy_version: null
  mpmath_version: null
  actual_lean_version: null
  actual_mathlib_commit: null
  source_binding_exit: null
  source_binding_ok: null
  parent_adjudicator_exit: null
  sympy_solver_executed: null
  sympy_status: null
  lean_solver_executed: null
  lean_status: null
  aggregate_status_raw: null
  exceptions_applied: null
  input_bytes_unchanged: null
  source_binding_receipt_sha256: null
  adjudication_receipt_sha256: null
  artifact_package_path: null
  artifact_package_sha256: null
  child_log_coverage: PARENT_EMITTED_PAYLOAD_AND_TAILS_UNLESS_MORE_ACTUALLY_CAPTURED
  git_source_modified: false
  remote_mutated: false
  K2FER1_repeated: false
  K5_rebuilt: false
  all_40_claims_verified: false
  canonical_claims: 30
  candidate_claims: 40
  observational_data_used: false
  canonical_or_publication_promoted: false
  overall: null
```

Choose an honest overall class such as `R2_LOCAL_EXECUTED_PASS_PENDING_SCOPE_REVIEW`, `R2_LOCAL_EXECUTED_NONPASS`, `SOURCE_BINDING_FAILED`, `PINNED_TOOLCHAIN_UNAVAILABLE`, `SOURCE_ACQUISITION_BLOCKED` or `EXECUTION_ENVIRONMENT_BLOCKED`. Preserve the raw runner status rather than replacing it with this transport label.

This local assignment performs no remote commit/push/PR mutation/merge. Return the durable result for the work-thread review below.

## 5. Work-thread assignment after the local return

Task ID: `R4A1ER_LOCAL_RESULT_SCOPE_REVIEW`.

Input: the complete local result package, the fixed execution pin, the existing R2 contract/source and the already published K2FR evidence. Do not begin a new K2FER1 repair, whole-repository census or PDF build. The local code executor is separate from this source/evidence reviewer; call the review what it is, not blind if the reviewer has seen the result or prior derivation.

1. Verify the returned package manifest and exact original receipts, contract/source/toolchain identities and before/after source checks. Inspect all four obligation payloads and whether both axes really executed in the parent-owned run.
2. If execution failed, separate environment/package/binding/implementation/proof errors and mathematical counterexamples. Preserve the first actual error and scope a minimal follow-up. Do not edit the original result or enlarge a timeout retroactively.
3. If it passed, compare the bound convention inputs with revision-2 manuscript blob `99a3f75c67ece3cfb00179bfd61787f47cb7e7ac`, specifically observer/photon conventions in 2.1, local-observer normalisation in 8.1 and positive regularisation in 11.1. Record which supporting lemmas transfer unchanged and which claims are not addressed.
4. The contract excludes Q/O reconstruction, finite-null validity, full physical kinematics/response, finite-HEALPix containment and observations. Do not use a four-lemma PASS as a forty-claim theorem certificate or as validation of the STF response normal-matrix factor in 8.2; that factor is not one of these four obligations.
5. Keep the original K2FR bundle, its five findings and the separate scope annex immutable. For eventual final reconciliation, explicitly list any still-required original obligations, including unresolved implementation/replay items if still applicable. Do not inherit stale 'not yet built' PDF status or silently delete a still-applicable execution requirement.
6. Produce one bounded review result with the admissible use of the local receipt, concrete unresolved issues and a recommendation to the discussion thread. No new permanent checker, compiler, audit framework or canonical ledger is required for this review.

Publication responsibility: after this review, the work thread may publish the exact new local receipts and its review as noncanonical text evidence on one **new isolated child branch based on the fixed PR #452 commit**, and create a Draft PR targeting `review/htt-k2fr-returned-repair-20260905-r1`. This is evidence publication only, not a release. Do not update source on existing PR #449/#452, change their base/head, overwrite any prior artifact, merge or force-push. Read back every newly published text payload and record commit/tree/PR/file identities. For a failed run, failure evidence may be published only with its actual nonpass status.

Large local binaries can remain in the returned ZIP; publish readable receipts and checksums rather than inventing a portable sandbox URL. Keep names unique to this run. If publishing is unavailable, retain the completed review and return its actual local files; do not revoke the calculation or repeat it.

## 6. Discussion-thread decision after those returns

The discussion thread combines the existing K5 PDF, published K2FR evidence, the new limited R2 execution and work review. It decides whether further source work is genuinely required and presents the exact remaining acceptance questions to the owner. It does not infer automatic canonical or merge permission from any PASS.

Current downstream order:

```text
K2FER1 + K2FR publication + K5 review PDF  [completed evidence retained]
                    |
R4A1E existing R2 native execution        [local Codex]
                    |
R4A1ER receipt and limited scope review  [work thread]
                    |
remaining-authority reconciliation      [discussion thread]
                    |
explicit owner canonical/release decision
```

Work may inspect the declared transfer scope while local execution runs, but must wait for the actual receipts before execution adjudication. One writer owns each output namespace. Nothing here promises autonomous background interaction between ChatGPT threads.

This handoff advances one existing executable obligation. It does not reset report completion, turn K2FR findings into new theory, claim that every final acceptance condition is already known to be satisfied, or authorise observations/native-solver work.
