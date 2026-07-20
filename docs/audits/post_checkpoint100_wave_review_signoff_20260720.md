# Post-checkpoint-100 wave review sign-off — 2026-07-20

Scope: strict correctness review of every commit in `2103a734..ff2b9c14` (18 commits,
15 PR ids): PR-150/152/153 amendments, PR-151 acquisition start, PR-154, PR-167,
PR-168, PR-169, PR-170, PR-171, PR-172, PR-173, PR-177, PR-179, PR-176.
Review executed by three independent read-only passes (DAG/backlog map, per-PR
delta/artifact audit, verification battery) plus a five-batch pytest run of the
wave-added test files. This document records process evidence only; it makes no
scientific claim and changes no scientific status.

## Verdict

The wave is substantively correct. No P0 or P1 defect in any PR's artifacts,
receipts, status bookkeeping, or claim surfaces. One P2 reproducibility defect
found (F1 below). Two bookkeeping-staleness items (F2) are remediated by the
companion DOCS commits of this session.

Verified good, with evidence:

- Every delta-declared test file, source module, and generated result card exists
  on disk for all 15 PR ids (only expected absences: PR-151 terminal card
  `desi_official_mock_card.json` — acquisition still in progress).
- Receipt hashes pinned in `docs/codex_handoff/pr_status.yaml` for PR-176
  (`pr176_reviews/manifest.json`, `pr176_reviews/final_adjudication.json`) and
  PR-179 (`final adjudication`) match the actual file bytes.
- Mirror parity: `docs/codex_handoff/{pr_backlog,pr_status}.yaml` byte-identical
  to `machine_readable/` counterparts; `sync_pr_dag_mirrors.py --check` OK;
  `validate_pr_dag.py --strict-rescue-slice` OK (130 cards).
- Remediation authority intact: `research_remediation_state.yaml` OPEN=102,
  rescued_count=0; both CF4 P0 findings remain `scientific_status: OPEN`.
  PR-179 denies CF4-P0 payloads at the value-access boundary; no wave PR
  adjudicates or closes a CF4 P0.
- Frozen carriers untouched: canonical `bounds.py` / `departure_posteriors.py`
  unchanged across the range. The single x_C-carrier edit
  (PR-169, `htt/src/common/egs_oneway.py`) preserves the exact comparator
  identity and only hardens the firewall (adds `predicate_scope`
  `comparator_flrw_limit_only`, expands `_FORBIDDEN_TEXT`).
- Surfaces each delta declares untouched (`b_mode_projector.py`,
  `cf4_velocity_estimators.py`, core bounds) verified byte-unchanged.
- `check_claim_language.py --dry-run` over the PR-176 delta and result cards:
  0 issues, 0 missing paths. No detection/anisotropy/family-identification
  language in any new module or ledger row.
- PR-172 failure semantics consistent: `COMPLETED_FAILED_WITH_RECEIPT`,
  `success_dependency_satisfied: false`, listed under `blocked`; the PR-180
  `requires_success` edge is correctly unsatisfied.
- PR-179 closing before PR-176 violates no dependency (both gate only on
  PR-173, which is COMPLETED_SUCCESS).

## Pytest receipts (wave-added tests, 2026-07-20)

Commands: `env PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
MKL_NUM_THREADS=1 PYTHONPATH=htt:htt/src timeout 900 venv/bin/python -B -m
pytest -p no:cacheprovider -q <batch>` from repo root.

| Batch | Files | Result |
|---|---|---|
| B1 | pr_cards 154, 167, 168, 169, 170 | 72 passed, **1 failed** (F1) |
| B2 | pr_cards 171, 172, 173 | 36 passed |
| B3 | pr_cards 176, 177, 179 | 37 passed (98.3 s) |
| B4 | contracts pr154 runner, pr167 intake, pr167 tx-safety | 37 passed |
| B5 | contracts pr151-phase/desi-acquisition/pr153, htt jwst-hierarchy, obsstat cf4-affine-divergence/cf4-raw | 95 passed |

Total: 277 passed, 1 failed.

## F1 (P2, reproducibility): PR-169 consumer-scan artifact is not byte-stable under repo growth

`tests/pr_cards/test_pr_169_...::test_write_check_and_cas_collection_check_are_byte_stable`
fails at HEAD `ff2b9c14` with
`ValueError: artifact differs under --check: docs/generated/pr169_all_consumer_scan.json`.

Root cause: `scan_active_consumers` in
`scripts/codex_harness/run_pr169_unsigned_leakage.py` enumerates the live tree
(`htt/**/*.py`, `scripts/**/*.py`, manuscript tex, backlog, results table) and
embeds a per-file inventory with SHA-256 digests into the artifact. Any later
commit that adds or edits an in-scope file changes the artifact, so `--check`
byte-stability cannot hold at any HEAD after the artifact's last regeneration.
This is the same defect class as the historical v6 report builder
("builder re-enumerates live tree", rev-r179 audit).

History: the artifact was regenerated once post-PR-169, by PR-170 (`c936fabd`),
absorbing PR-170's new files — establishing the regenerate-on-in-scope-change
convention. PR-171, 172, 173, 176, 177, 179 added eight in-scope runners
(`run_pr170_axis.py` … `run_pr179_directional_cosmography.py` are absent from
the pinned 251-file inventory) without regenerating, so the gate has been red
at every HEAD since PR-171 landed. The scan's scientific content is unaffected:
the pinned scan still reports `pass: true` (0 unresolved active claims) for the
tree it saw.

Disposition:

- Interim (this session, precedented): regenerate the artifact as part of each
  PR close that adds in-scope files (as PR-170 did), re-verifying
  `pass: true` and the byte-stability test at the new HEAD.
- Structural (checkpoint-110 agenda): decouple the live-tree consumer scan from
  the byte-stability contract — either scope the byte-stable artifact to
  PR-169's own outputs and move the scan to an always-regenerated report, or
  add the regeneration step to the per-PR closing checklist enforced by a gate.
- No receipt or test was amended ad hoc in this review.

## Sign-offs

- (d) PR-176 dual-axis bookkeeping — SIGNED OFF. `resolution:
  COMPLETED_SUCCESS` (infrastructure/mechanics axis) coexisting with
  `validation_axis: FROZEN_COVARIANCE_SELF_CONSISTENCY_GATE_FAILED` and
  `scientific_status_after: NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE` is
  deliberate two-axis bookkeeping: the delta separates the axes explicitly and
  the failed coverage gate (0.9424 with a Wilson interval excluding 0.95) is
  reported, not hidden. The failed axis cannot substitute for the registered
  q-response terminal, and no q/significance result exists or is claimed.
- (e) PR-172 / PR-180 disposition — DEFERRED TO CHECKPOINT 110 (owner
  decision recorded 2026-07-20: decide at checkpoint with auditor input).
  The B-projector documentation/implementation disagreement
  (max abs Delta_B = 0.006921858… against a documented exact-zero invariant)
  is a genuine open item; PR-180 stays locked through the failed
  `requires_success` edge until then.

## Records (report-only; receipts stay immutable)

- (b) `docs/PR_DELTAS/pr-151.md` describes the synthetic preflight cards as
  "retained", but commit `21ceaee6` deleted the `pr151_*.json` synthetic cards
  (preflight evidence remains in the delta text and history). Wording fix is
  deferred to the PR-151 finalize-time delta update.
- (c) `docs/PR_DELTAS/pr-167.md` pins a backlog-YAML hash that no longer
  matches HEAD because PR-168/169 cosmetically rewrapped the PR-168 backlog
  entry. The JSON mirror hash pinned by the same receipt still matches, and
  both mirrors are parity-clean, so there is no verification gap. Report-only.

## Bookkeeping remediation (F2)

CHANGELOG.md lacked entries for PR-154, 167, 168, 169, 170, 171, 172, 173,
176, 177, 179, and CLAUDE.md §3 still described the PR-153 / checkpoint-100
state. Both are updated by this session's DOCS commits; numbers are copied from
`progress_report.py` output (109/130 completed, 83.85%, dependency-weighted
90.25%, critical-path 50/56).

## Session context recorded for continuity

PR-151 background acquisition healthy at review time (writer lock held,
PID 16695, phase acquire; probe deltas show active part-file and log growth;
free space ~815 GiB, above the 300 GiB threshold). No foreground-defensible
DAG card exists at 109 completions; the deps-satisfied set is exactly
{PR-151 (running), PR-174, PR-182}, the latter two hypothesis-only
(`REGISTERED_NOT_SCHEDULED`, `public_use: false`). The owner explicitly
scheduled PR-174 then PR-182 for this session (recorded in their specs);
all hypothesis-only gates remain enforced. PR-155–158 remain an atomic
post-PR-151-terminal chain; PR-178/180/181 blocked; PR-159–166/183
native-dormant; checkpoint 110 due at the 110th completion.
