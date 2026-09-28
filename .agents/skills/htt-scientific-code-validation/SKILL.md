---
name: htt-scientific-code-validation
description: Use when htt_base edits can affect numerical output, scientific tests, artifacts, inference or claim-bearing reports.
---

# htt-scientific-code-validation

Classify the affected scientific owner and exact input/environment before running.
Read the governing contract and use the existing interpreter. Bind required package
versions and APIs with the global runtime receipt when applicable; do not rely on
ambient `python`. Capture command, cwd, exit status, source identity and output.
Use `cuhg-telemetry run` for metadata; exporter failure does not stop computation.

Run the narrowest falsifier, affected unit/contract tests and necessary invariants.
Frozen tests, tolerances, references, one-use allocations and missing-input states
remain unchanged. Do not run an expensive scientific experiment just to validate
runtime repair. Compare SHA differences by class and inspect differing fields;
numerical equivalence and byte replay are separate contracts.

Use actual tests under `tests/contracts`, `tests/common`, `tests/htt`, `tests/mio`
or the owning module. Do not blindly run every archived suite. Preserve raw errors;
report NOT_RUN and skipped dependencies honestly. Update only the evidence consumed
by this task, not unrelated ledgers. Independent review precedes claim admission;
no smoke output or external-transfer result becomes native scientific evidence.
