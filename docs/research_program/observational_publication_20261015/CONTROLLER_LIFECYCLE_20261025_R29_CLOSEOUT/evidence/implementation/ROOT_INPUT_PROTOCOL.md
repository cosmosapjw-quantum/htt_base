# Explicit execution baseline, v2

This is the single non-scientific R29-PROTOCOL-BASELINE repair. No commit or push was executed during implementation. Original scripts, packet, manifests, prior snapshots, scientific inputs and acceptance remain unchanged. New scripts are dormant until independently reviewed and explicitly bound by root. Use ordinary Python (not `python -O`, since existing fail-closed assertions are retained).

## Root input schema

Root alone supplies `APPROVED_COMMIT_INPUT_V2.json` or `APPROVED_PUSH_INPUT_V2.json` in the existing publication directory. Both require:

- `protocol`: exactly `R29_EXPLICIT_EXECUTION_BASELINE_V2`.
- `action`: exactly `commit` or `push`, matching the executable.
- `status`: commit `ROOT_GO_REVIEWED_EXACT_TREE_COMMIT`; push `ROOT_GO_EXACT_REVIEWED_COMMIT_PUSH`.
- `tree`: exactly `1e484cab48211ae5a433f3ae20192dddb3bbfdf1`.
- Commit: `parent` exactly `71b272db893a92ec336c28164bc7efccf7c340b2`, and `manifest_sha256` exactly the unchanged FILE_MANIFEST seal.
- Push: `sole_parent` exactly the same parent; `commit` exactly the successful candidate commit; `candidate_packet_sha256` seals its exact CANDIDATE_COMMIT_REVIEW_PACKET.json.
- `prior_anchor`, `execution_baseline`, `reconciliation`: exact descriptors `{ "path": "/absolute/path", "sha256": "64-character-lowercase-SHA256" }`. The SHA256 covers the complete file bytes, including formatting. No optional omission/ignore list exists.
- `review_seals`: nonempty list of distinct path/hash descriptors. All must still match their file bytes; no duplicate paths. Additional independent approval receipts may be included, but mandatory seals cannot be omitted or replaced.

Commit prior is the original CANONICAL_METADATA_AFTER_TREE.json, seal `5285641ed220230e7cc63125fb6d52436da3686c37d705a051302a2c518864f6`. Push prior is the exact successful CANONICAL_METADATA_AFTER_COMMIT.json; its seal is recorded in the successful v2 candidate packet's `canonical_after_commit_sha256`. Both anchors remain immutable. No root-selected substitute prior is accepted.

The fresh baseline is a complete JSON snapshot using the unchanged prepare_publication.snapshot() shape: top-level `non_object_metadata` and `canonical_object_stat_inventory`, each a map keyed by relative Git path. Every entry and field participates in equality, including HEAD, index, config, branch refs, object stat inventory, size, mode, mtime and applicable sha256/symlink values. Root must capture/review/seal this baseline for the exact next action. The worker scripts never capture a replacement baseline or excuse a difference.

Mandatory review seals: contract; original exact-tree packet; every frozen input in the contract; all packet `seals` resolved within publication directory; all packet `final_input_seals`; both actual live repository source files at packet `source_seals`; live durable STATE and active pointer at the frozen hashes; unchanged publication guard; both final v2 scripts and their shared helper. Push additionally requires the exact candidate packet seal. The example files enumerate these explicitly at current implementation hashes.

## Reconciliation schema

The root-sealed reconciliation JSON requires:

- `status`: exactly `ROOT_RECONCILED_EXACT_TRANSITION`.
- `action`: same exact action as approval.
- `prior_anchor`, `execution_baseline`, `review_seals`: exactly equal to approval's values.
- `context`: exactly the fixed context below (including added push keys).
- `independent_evidence`: ordered exact list consisting of contract descriptor then the contract's five classified_current_delta.evidence descriptors. Every evidence file is rechecked.
- `metadata_changes`: complete ordered list of changes from immutable prior to fresh baseline, sorted by group then path. Each row has exactly `group`, `path`, `before`, `after`, `classification`. Before/after contain complete entry values, or null for absence. `classification` must be a nonempty root-reviewed explanation. The script computes the complete delta and demands exact matching rows. Empty is valid only for an actually identical prior and baseline. New later drift needs new fieldwise root reconciliation; the old five evidence artifacts alone do not classify new changes.

Context keys: `tree`, `sole_parent`, `local_HEAD`, `remote_url`, `remote_ref`, `exact_tree_packet` (path/hash descriptor), `guard_sha256`. Push additionally includes `commit` and `candidate_packet` (path/hash descriptor). Values are fixed by the existing frozen protocol and exact candidate. Examples contain all fixed commit context values. Push placeholders must be replaced by the generated exact commit/packet/after-commit seals only after the separate root decision.

## Examples and next transition

`COMMIT_INPUT_V2.example.json`, `COMMIT_RECONCILIATION.example.json`, `PUSH_INPUT_V2.example.json`, and `PUSH_RECONCILIATION.example.json` are non-executable templates. Their baseline/reconciliation hashes are zero placeholders, and their status is TEMPLATE_NOT_AUTHORIZATION. They cannot pass either production script. They are never written to the live approval filenames by this worker. Root supplies the complete metadata_changes from its exact prior-to-baseline comparison, classifies every change, checks all source/state/pointer bindings, then seals the finalized reconciliation and input. Root must review fresh v2 script seals independently before changing either template status to GO.

Once root has supplied exact reviewed inputs, run at most once from existing publication directory: `PYTHONDONTWRITEBYTECODE=1 python create_reviewed_commit_v2.py`. Root must separately review/bind its successful candidate and a fresh push baseline/reconciliation before `PYTHONDONTWRITEBYTECODE=1 python push_approved_commit_v2.py`. These are documentation of the next authorized checkpoint, not worker execution or approval.

Both scripts retain shared original attempt/failure filenames; switching version cannot reset an exhausted attempt. The complete live snapshot is compared to root's baseline before read-only checks and immediately before the effectful operation. Complete before/after equality, status, exact HEAD, parent/tree/ref/URL, private objects without writer alternates, guard and existing hook chaining, and non-force single-ref push remain. No blanket ignore, auto-refresh, scientific rerun, checkout/ref/index write, acceptance reset or installation is introduced.
