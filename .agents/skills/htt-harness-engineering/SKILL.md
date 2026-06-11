---
name: htt-harness-engineering
description: Use when adding or modifying test runners, optional dependency handling, PR delta scaffolds, status snapshots, artifact linters, or CI-like local commands for htt_base.
---

# htt-harness-engineering


Build harness first, but do not let harness work become endless. Every harness PR must unlock a named downstream PR or block a concrete failure mode. Prefer small scripts with deterministic CLI, JSON/Markdown output, and pytest coverage. Do not hide failures with broad skips.


## Required output when invoked

Return:

- evidence read,
- proposed changes,
- tests to run,
- risks and kill-switches,
- artifacts/status updates needed.
