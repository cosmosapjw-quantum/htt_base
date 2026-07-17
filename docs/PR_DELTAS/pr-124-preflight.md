# PR-124 preflight — harness repair + repo pushability (2026-07-17)

Governing verdict: `docs/audits/shared_context_cas_harness_final_audit_20260717/`
(PRESERVE CORE / REPAIR ENFORCEMENT / REDUCE ORCHESTRATION / NEVER COLLAPSE
CAS-4). Owner `COMMON`, claim tier `diagnostic_only`, no scientific state
changed (102 OPEN / 0 RESCUED preserved; x_C / W2_max untouched).

## Harness repair (audit PDR Phases 0–3, all shipped)

- **Phase 0**: `build_context_pack.py` write-if-content-changed;
  `work_unit_id` cumulative spawn budgets; `run_summary.py` +
  `RUN_SUMMARY.json` for the 13 frozen historical runs; future runs
  untracked (`runs/RETENTION.md`, `RETENTION_LEDGER.jsonl`);
  `fork_turns=none` default; exactly-once context delivery.
- **Phase 1**: assignment schema v2 fail-closed (the audit's negative probe
  — unknown `agent_type` + empty lists — now returns 6 errors);
  `profile_registry.py` (duplicate names/sandbox conflicts raise; 3
  duplicate Jun-12 tomls deleted, 15 profiles / 15 unique names);
  `launch_receipt.py` (attestation or `generic_prompted` downgrade;
  `effective_context_sha256` blocks stale launches); stop hook hardened
  (final-line marker, pre-resolve symlink check, `launch_id` binding,
  sibling-read + duplicate-delivery gates); start hook delivery records.
- **Phase 2**: `CAS_CONTRACT.json` v2 + `CAS_AXIS_RESULT`/`CAS_ADJUDICATION`
  templates; `cas_gate.py` preflight/check-axis/adjudicate implementing the
  audit §5.5 state machine (4×PASS one contract hash → `CAS_4AXIS_PASS`;
  never 3-axis; no majority vote; preregistered non-self-approved
  exceptions only). All four axes preflight PASS on this host.
  `run_egs3_v9_seals.py` labeled legacy diagnostic runner (Makefile).
- **Phase 3**: normative dedup key `(claim_id, evidence_fingerprint,
  verdict)` + refs union + auto-conflict; cross-run `FINDING_LEDGER.jsonl`;
  content-addressed `evidence_store.py`; exact `test_receipt.py` reuse.
- **Acceptance**: `scripts/codex_harness/test_harness_enforcement.py` —
  audit §10 items 1–14, all pass.

## Roadmap amendment (ADJ-ROADMAP-001, targeted only)

`LONG_HORIZON_RESCUE_PR_ROADMAP_20260714_AMENDMENT_01_20260717.md` + four
line edits (§4.5 lifecycle checklist + risk-tier budgets; PR-124 →
"Four-axis CAS contract + derivation-lineage oracle"; §17.1 targeted tests
+ receipts; §20 historical-plan banner). `EXPECTED_ROADMAP_SHA256`
advanced; sanctioned intake `--write` + mirror sync + remediation `--write`;
DAG valid (113 PRs); claim-language lint clean.

## Repo hygiene + pushability

- Untracked ~300MB at HEAD (legacy/, package zips, raw jcap evidence,
  copyrighted PDFs, handoff archives); bytes stay on disk; byte authority =
  fixed-hash ledger + PR-120 quarantine inventory (binding code updated
  fail-closed).
- `.claude/settings.json` sanitized (machine-specific → settings.local.json);
  `AGENTS(9).md`/`agent.md` dedup; CLAUDE.md + per-package AGENTS.md now
  tracked; workflows dispatch-gated.
- **History rewrite** (git-filter-repo, in place): 839 commits 1:1, pack
  2.1GB → ~325MB, zero >50MB blobs. Commit map + strip list committed under
  `docs/git_history/`; bundle + full pre-rewrite `.git` on
  `/mnt/sn850x2t/htt_rewrite_20260717/` (sha256-pinned). Live-resolved pins
  rebound; string-only historical ids resolve via the map.

## Pre-existing rot repaired along the way

Baseline `tests/contracts` had 26 failures (the "1 pre-existing failure"
note was stale). Fixed: quarantine regex false-positive (4.44σ vs
4.44e-16), stale canonical inventory/block + ~26 block-record consumers,
PR-122 evidence graph/pin drift, stale v6/report-data/theorem/manuscript
figure packs, lean seal, backlog metadata drift, remediation-root refresh
(PR-122 precedent), pr123 oracle-lab pin + artifacts. Quarantine-by-design
reds (PR-120 deleted final report) and the sealed 2026-07-14 jcap
live-tree snapshot are documented `xfail(strict=False)`.

**Final suite: 863 passed / 1 failed (cf4pp network-only) / 15 xfailed.**
