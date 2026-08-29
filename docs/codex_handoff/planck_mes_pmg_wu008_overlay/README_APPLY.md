# PMG-WU-008 foundation overlay

This branch is an execution-binding delivery on top of accepted PMG-WU-007 commit
`ccba350d7b725b227c64436e32af96abfe786449`.

The content-bound archive contains the complete WU-008 source, tests, validator,
machine-readable contract, registry, implementation plan and Codex prompt. It does
not contain a scientific power result.

Use a separate clean worktree, then run:

```bash
bash docs/codex_handoff/planck_mes_pmg_wu008_overlay/apply_overlay.sh
```

The script:

1. requires the accepted WU-007 commit to be an ancestor;
2. refuses a dirty worktree;
3. reconstructs the ZIP from exactly three tracked base64 parts;
4. verifies ZIP SHA-256 `e5cddee566a5ee30bcc2c3b0a98167c289878622586ec0e55ef1426fe035a4a2`;
5. verifies all 19 payload files against the internal manifest;
6. refuses any non-identical target collision;
7. copies only the bounded WU-008 payload.

No raw maps, private data, generated power result, or GitHub Actions state is included.
After application, follow `CODEX_HANDOFF_PROMPT.md`, commit the applied foundation to
the same branch, execute locally, review once, and push reviewed evidence.
