# S00/S01 source reconciliation — 2026-10-11

## Scope and claim boundary

This is a source and evidence reconciliation receipt for handoff tasks `S00` and
`S01`.  It is not a Lean build, a four-axis adjudication, an independent
mathematical review, or a scientific admission.  Existing theorem/review states
are preserved exactly as their source receipts state them.

## S00 — checkout state

Observed in the existing checkout, without clone, worktree, reset, clean, stash,
or source mutation:

- branch: `proof/cas15-ls-matrix-synthesis-20261008`
- HEAD: `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`
- tree: `106908e7513fbb139bcce538380abfc9e1a19819`
- `origin/proof/cas15-ls-matrix-synthesis-20261008`: the same HEAD
- local commit delta from that pin: empty
- dirty/untracked entries: 236, preserved; SHA-256 manifest:
  `b3ede41310c4f8f4c61013c197d0460b0f9b40c41ea30cfcb8ed5a7b4bc60314`

The manifest is an execution-local raw record at
`/tmp/htt_s00_dirty_manifest.json`; its digest is recorded rather than copying
user-owned dirty content into this receipt.

## S01 — sibling PR payload census

Method: for each PR, obtain the current GitHub head and full commit list using
`gh pr view <n> --repo cosmosapjw-quantum/htt_base`, enumerate the immediate
commit payload (not merely a head diff), then compare each non-deleted path's
working-tree Git blob identity against the payload commit's blob.  All 19 PRs
were OPEN when queried.  None of their heads is an ancestor of the current HEAD;
that ancestry result alone is therefore not used as a non-inclusion conclusion.

| PR | head | payload paths | exact | successor-different | deleted |
|---|---|---:|---:|---:|---:|
| #477 | `1a3755365bb72f4197292e4aa70fa71855744b8b` | 1241 | 1236 | 5 | 0 |
| #478 | `f7f6231cf8c2511ca9ff2b52f9e1d2fa8e05f11d` | 294 | 293 | 1 | 0 |
| #487 | `b3e99a1eb0d5be27c67315a848df7a487fc117d2` | 102 | 101 | 1 | 0 |
| #488 | `477f1154de5778bfed8451122d94e9d61733bb6a` | 64 | 63 | 1 | 0 |
| #489 | `063163156406eca58c7f16416fc8045c721ba444` | 85 | 84 | 1 | 0 |
| #490 | `2f4a84b7a993b3f967bfe41bc082b3517cddbf48` | 2 | 2 | 0 | 0 |
| #491 | `23194c91b8ab67dad0187765a70201a33b1c53c0` | 156 | 142 | 1 | 13 |
| #492 | `8e839be158dfa43fefaa39d6d0a2a12016f23618` | 97 | 96 | 1 | 0 |
| #493 | `d5bc8a7071a59226683d2f31848774d6fb2c9993` | 115 | 115 | 0 | 0 |
| #494 | `deffbcff612c886f1eaccf08586ce3163b99aedb` | 112 | 112 | 0 | 0 |
| #495 | `e372106da49f8604ce1e1da0facef8b2ef074bd4` | 60 | 60 | 0 | 0 |
| #496 | `329cd7021c199e2be96721de07cd465f450e165a` | 237 | 237 | 0 | 0 |
| #498 | `c0365da5789ee5de1cb11c47be827e577f86ca3d` | 83 | 83 | 0 | 0 |
| #499 | `339b0c6dce9702708d7ad825484bd4fff7e1651a` | 87 | 87 | 0 | 0 |
| #500 | `175c1323b384bebc25f1c8edeb1b22d625c0b6c0` | 108 | 108 | 0 | 0 |
| #501 | `00384ac123fb52e2093a4937235f63fd4f19fa99` | 67 | 67 | 0 | 0 |
| #502 | `42fc84b54b61dec71743029464d2cc9a44b21b19` | 66 | 66 | 0 | 0 |
| #504 | `3fd33b2e80d40a4e8856995e19e6d505ed73bacd` | 97 | 97 | 0 | 0 |
| #505 | `b3f1d2596d01a071155bfa093c9c8e73e66f6abd` | 169 | 169 | 0 | 0 |

The listed successor differences are only later `RETURN.json` records, plus the
current runtime/hook test files in #477; they are preserved as later evidence,
not overwritten.  The 13 #491 deleted paths are deletion entries in that PR, not
missing local inputs.  Thus each PR has disposition `REUSE_PAYLOAD_WITH_LATER_
SUCCESSOR_RECORDS`, except #490 which is `HISTORICAL_BLOCKER_REUSED`.

`#498` is bound to its actual C04 head above; no stale locator to CAS07 is used.
The local CAS02 C01–C03 candidate exists at
`CAS-02/c01_c03_input_aligned_v1_20261005/lean/Cas02.lean` and has the required
SHA-256 `283f64377e49585c697c3cb51f04cacece79015b36fa3c8d4a8e2d640678b520`.
This only restores source identity; it does not change its independent-review
status.

Additional identity controls:

- #503: `249fa16f5a83af80251e1e8350345c71b46ad546`, one commit; treated as the
  already-consumed CAS16 payload, not copied again.
- #507 and #508 both point at current head
  `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`; neither is a second payload.

Raw, local-only query summaries are retained by digest:

- PR metadata TSV: `66ca9d369727bcc0687222a0dca40b26a75891f671e6a5f9e4da6f57feb40de4`
- payload comparison JSON:
  `56c5b5a2fe0940d6f368eaecd2d7f148ab2fbd64cef124cf6cbe3994500a7713`

The local comparison JSON was normalized and checked with `jq empty`; this
changes only its final newline encoding, not its compared path records.

Independent review found that the aggregate comparison is not a durable
per-path/blob manifest.  A complete map was generated locally (3,242 entries;
uncompressed SHA-256 `22f630ae09a1ae87f7cc26cadfd7b26b976612cc180a271d3818f9c9d2b3d245`,
gzip SHA-256 `82e6fb27811d9782f3346d08d8de8625aa6d52eeb04fcac6b2a5a2a4426a1f3d`),
but has not been retained as a repository artifact.  Therefore `S01` is a
`PARTIAL_CENSUS`, not an accepted full path/hash reconciliation.  This does not
invalidate the census; it leaves the precise raw-manifest retention obligation
open.

## Tool disposition

Wolfram/xAct, SymPy, Sage/Singular: `NOT_NEEDED` (source reconciliation only).
Lean: `NOT_NEEDED` (no source changed and no theorem acceptance is claimed).

## Next executable node

`S02`: source-family discovery and original-plan coverage comparison.  It must
add any newly discovered obligations to the shared registry before scheduling a
mathematical proof task.
