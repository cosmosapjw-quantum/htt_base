# Git history rewrite record — 2026-07-17 (PR-124 preflight)

The repository history was rewritten in place with `git-filter-repo` to make
it pushable to GitHub: ~1.7 GB of repeatedly re-committed audit/report
archives (zips, PDFs, the `legacy/` tree, raw multi-agent run evidence) were
stripped from all commits. No file at the post-rewrite HEAD was removed —
every stripped path had already been untracked by the
"untrack bulk artifact payloads" commit, and all bytes remain on disk and in
the off-repo backup.

| item | value |
|---|---|
| rewrite date | 2026-07-17 |
| tool | git-filter-repo (venv), `--invert-paths --paths-from-file strip_paths_20260717.txt --prune-empty never --prune-degenerate never` |
| commits | 839 before = 839 after (1:1 mapping; nothing pruned) |
| pack size | 2.1 GB → ~325 MB |
| largest blob after | < 50 MB (GitHub warn threshold clear) |
| pre-rewrite heads | `research/pr04-multicomponent` 5e87966359ef020b42e6c3e8a605cb70aaa45a11, `main` 348e8ac74e33e108545b6b3eb19d70708088500e |
| backup bundle | `/mnt/sn850x2t/htt_rewrite_20260717/htt_base_all_refs.bundle` |
| bundle sha256 | `c8290411796011f5c81dece7f396c617c579ba9ae985cea09f7288c55a7c449b` |
| full pre-rewrite `.git` copy | `/mnt/sn850x2t/htt_rewrite_20260717/git_dir_pre_rewrite/` |

## Resolving historical commit ids

Every document/manifest that pins a pre-rewrite commit id (e.g.
`MANIFEST.json` `base_commit` fields, `EXPECTED_BASELINE_COMMIT`,
`git-commit:` strings in ledgers) resolves through
[`commit_map_20260717.tsv`](commit_map_20260717.tsv) (`old → new`,
one line per commit):

```bash
grep '^<old-id>' docs/git_history/commit_map_20260717.tsv
```

Content stripped from history (the `legacy/` snapshots, raw jcap evidence,
package zips) is recoverable from the backup bundle:

```bash
git clone /mnt/sn850x2t/htt_rewrite_20260717/htt_base_all_refs.bundle restored
```

The fixed-hash ledger
`docs/research_program/long_horizon_rescue/cf4_p0_legacy_package_hashes.json`
plus the PR-120 quarantine inventory remain the byte authorities for the
on-disk `legacy/cf4_p0` tree.

## Files

- `commit_map_20260717.tsv` — old→new commit id map (840 lines incl. header)
- `ref_map_20260717.tsv` — old→new ref map
- `strip_paths_20260717.txt` — exact path list given to git-filter-repo
