---
name: htt-transfer-provenance
description: Use when wrapping current AniCLASS/external transfer functions, defining future native solver adapter stubs, AtlasEntryLite, budget ceilings, or transfer sensitivity reports.
---

# htt-transfer-provenance


Every transfer-dependent number must carry TransferFunctionSpec. External and native transfers must coexist side-by-side. Do not create fake native outputs. Adapter stubs may validate schema and raise NotImplementedError; they must not return synthetic science values unless explicitly labeled empirical_proxy.


## Required output when invoked

Return:

- evidence read,
- proposed changes,
- tests to run,
- risks and kill-switches,
- artifacts/status updates needed.
