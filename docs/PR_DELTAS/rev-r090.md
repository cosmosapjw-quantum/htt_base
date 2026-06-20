# REV-R090 - Generate Manuscript Status Counts

owner: COMMON
implementation_scope: manuscript_status_provenance
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R090 generate manuscript status counts and provenance-gated figure audit`
git_commit_or_worktree_state: pending_rev_r090_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 3)
- `docs/generated/audit_ver2_response_matrix.md`
- `scripts/audit_manuscript_figures.py`
- `scripts/ver2_artifact_export.py`
- `docs/manuscript/generated/ver2_*.tex`
- `docs/manuscript/ch07_results.tex`
- `docs/ver2_upgrade/generated/status_snapshot.json`
- `figures/paper/VER2_MANIFEST_INDEX.md`
- `tests/contracts/test_manuscript_figure_audit.py`

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 3 from the strict research-hardening plan: replace
hand-typed manuscript count prose with generated, provenance-tagged source so
the near-pass "manual status counts" finding cannot regress.

## Role Split

- Code cartographer steelman: reuse the existing VER2 export renderers rather
  than re-deriving counts; the four count snippets already render from
  `status_rows`/figure-manifest data. Attack: the snippets carried no source
  hash, so the auditor could not distinguish a generated count from prose.
- Harness engineer steelman: gate the manual-status-number scan on a provenance
  marker (`generated from <source> (sha256:...)`) that hand-written prose cannot
  fake, and add a contract test that fails on any remaining manual count.
  Attack: a directory-based allowlist would silence honest hand-typed counts in
  generated files too.
- Physics/statistics auditor steelman: the counts are bookkeeping, not science;
  recording the exact source file and its content hash keeps them auditable.
  Attack: a snippet that claims a source it was not derived from is worse than a
  manual count.
- Claim-gate reviewer steelman: keep the change diagnostic-only; no claim tier,
  figure lane, or science gate moves. Attack: count provenance must not be read
  as result provenance.
- Regression tester steelman: pin the audit to zero manual status numbers and
  keep the existing figure-audit fixture (no provenance) still flagging its
  manual counts. Attack: the exemption must be content-keyed, not path-keyed.

## Changes

- Added `scripts/generate_manuscript_status_snippets.py`, the single focused
  entry point that re-renders the four count snippets
  (`ver2_titlepage_status`, `ver2_status_snapshot`, `ver2_artifact_export_policy`,
  `ver2_figure_manifest_status`) from the cached export bundle plus
  `figures/paper/VER2_MANIFEST_INDEX.md`, with a `--check` idempotency mode.
- Extended `scripts/ver2_artifact_export.py`:
  - added `_provenance_comment` (hashes the normalized on-disk source bytes) and
    `_insert_provenance` helpers;
  - threaded a `provenance` argument through the four count renderers and wired
    the source content + provenance strings in `_render_outputs`, so a full
    export run and the focused generator emit byte-identical snippets.
- The four generated count snippets now carry a
  `% generated from <source> (sha256:...)` line whose digest matches the actual
  on-disk source (`status_snapshot.json` and `VER2_MANIFEST_INDEX.md` verified).
- Hardened `scripts/audit_manuscript_figures.py`: `_manual_status_issues` now
  skips files carrying generated-source provenance
  (`GENERATED_SOURCE_PROVENANCE_RE`), so generated counts are no longer flagged
  as manual while hand-typed prose (no provenance) still is.
- Downcounted `docs/manuscript/ch07_results.tex`: the FB-6 verification anchor
  no longer pins `48 passed` / `72 passed, 1 skipped` literals; it now defers
  live pass/skip tallies to the generated status snapshot.
- Regenerated `docs/generated/manuscript_figure_inventory.md` and
  `docs/generated/missing_figure_references.md`; manual/status-number findings
  drop from 9 to 0 (remaining 5 text findings are pre-existing claim-risk rows
  outside this task's scope).

## Artifact Metadata

- owner: COMMON
- implementation_scope: manuscript_status_provenance
- claim_tier: diagnostic_only
- transfer_source: none
- config_hash:
  - `scripts/generate_manuscript_status_snippets.py:sha256:a399290d792138c0c41a8cbc22ceb2d2d5038547bcc2fd14f852cba706b68faf`
  - `scripts/audit_manuscript_figures.py:sha256:6f1282a4aba669d145750064a8d333f8e808807e228340903b9e085bfcb2b2d2`
- input_hashes:
  - `scripts/ver2_artifact_export.py:sha256:acc3a02c4509c06374b0d3b62741b8ca34d12ca0e81c3c1af94308df79fb7969`
  - `tests/contracts/test_generated_status_counts.py:sha256:2613670bd1e4e9a55f4528226114f5b97999b171888a030e95c5826b03637da9`
  - `docs/manuscript/generated/ver2_titlepage_status.tex:sha256:82126fe119132e1872b029dc2e45e9c641948ed5d2029d5f117910f320a8060d`
  - `docs/manuscript/generated/ver2_status_snapshot.tex:sha256:bd01b55d8c447860f8cc442f00440386959271110cbbc148c1351f2dbf3d859c`
  - `docs/manuscript/generated/ver2_figure_manifest_status.tex:sha256:42f40fa642b9b032ee4e90d3c82df8a81dfaf9804ae66f6bff1d64bb235d4bb9`
  - `docs/manuscript/generated/ver2_artifact_export_policy.tex:sha256:a5a3363b0720ee95f42f7ef4419a9ef8329cf5600fb09c7aaf9e737f1ac78ca3`
  - `docs/manuscript/ch07_results.tex:sha256:b377baf2aebd55f17731a49ce615fe43d92ae8f4eb485557b40726ee9b3e230d`
  - `docs/generated/manuscript_figure_inventory.md:sha256:3c037759b0edd11e51594d19c1d2a17d69eca83f1e4d7be4bfe49837b0247f46`
- caveats:
  - no native low-ell solver result is introduced;
  - count provenance is bookkeeping provenance, not result/science provenance;
  - the provenance exemption is content-keyed and only suppresses the
    manual-status-number scan, never the claim-risk or forbidden-claim scans.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_generated_status_counts.py -q` initially failed: 9 manual status numbers remained and the snippets carried no `generated from`/`sha256:` provenance.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_manuscript_status_snippets.py` | PASS | Wrote the four provenance-tagged count snippets. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_manuscript_status_snippets.py --check` | PASS | `Manuscript count snippets are up to date.` |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/audit_manuscript_figures.py --dry-run` | PASS | `Manual/status-number findings: 0`; `text_findings=5` (pre-existing claim-risk rows). |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_generated_status_counts.py tests/contracts/test_manuscript_figure_audit.py` | PASS | `6 passed`. |
