# Published-source integration

Remote main remains `f1007dd3e41c07eccd64024dd6b44fb5a40a3612`; GitHub API reports all 29 PRs #477–#505 OPEN, all pinned heads matched. Only #479–#486 integrated. Each complete original history is one commit. No assumption of cumulative #505.

| PR | Original head | Evidence |
|---|---|---|
| #479 | `d5d129e529be0f432b4b4b433927ffe6dc329fac` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #480 | `8b51db067a2eda3eba54a0e7635adc051f13e943` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #481 | `11a6204d2439289ac1ff99f7a3b6d61c9959505d` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #482 | `6833d2469636652e3edea8040ace03998b86b930` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #483 | `52ec1537394754d92025b0b7dd05fae9ea6bad0a` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #484 | `20fc02b187010e9fc5e9d6a3e6f98342a91c914a` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #485 | `45ec9b6e660f3c341538679e93a895c87f65c39f` | Complete single-commit delta integrated; non-RETURN contents byte equal |
| #486 | `23edaea4454c64d69b068b83cf2636b8f60dfe12` | Complete single-commit delta integrated; non-RETURN contents byte equal |

Local differing RETURN.json files were preserved and restored; they remain unstaged metadata differences. All other source and evidence files compared to their original PR blobs. Copies of all 736 pre-existing colliding files are retained at `/tmp/htt-cas07-synthesis-20261008-preserved` with START_STATUS.txt and paths.json. Unrelated tracked and untracked files untouched. No stash/reset/clean/worktree.

The cherry-pick post-checkout hook reported a missing `/mnt/sn850x2t/htt_base_e2e/lean-shared/htt-lean-shared.py`; each cherry-pick itself succeeded. Pinned existing oracle is used for the new build. File disjointness alone is not integration validation; the new theorem compile and independent review are separate.

## Current continuation check — 2026-10-08

Start/current integration branch `proof/cas07-conditional-synthesis-20261008`, HEAD `5adf5e75b975d9dd12c20cb7c928ed96a510dd0c`, tree `648e1de291f80372d00a94ba8ac01728d827c86c`. `git status --short` observed existing tracked modifications and untracked candidates; original NUL-delimited status captured in `/tmp/htt-continuation-start-20261008.status`. Remote main queried with `git ls-remote` remains `f1007dd3e41c07eccd64024dd6b44fb5a40a3612`. `gh pr list --state open --limit 100 --json number,headRefOid` returned all 29 #477–#505 OPEN with unchanged handoff pins.

`git fetch origin refs/heads/main refs/pull/479/head … refs/pull/486/head refs/pull/497/head` exited 0. FETCH_HEAD identities match the table above and #497 `f6dde6fcd870e2c4676dc08209b4a89fa1bc8737`. Complete per-head `git diff-tree --no-commit-id --name-only -r` deltas contain respectively 253/42/71/60/63/58/72/117 files; each non-RETURN blob compared equal both to working files and HEAD. Existing RETURN differences remain preserved and unstaged. No second integration/cherry-pick occurred. The synthesis source SHA remains `39bf9debfd249e274a9c840f1c096a1bad692e605ff6c9286c284821e0d5f770`. Compilation and separate semantic review provide the integration argument in addition to these content checks.
