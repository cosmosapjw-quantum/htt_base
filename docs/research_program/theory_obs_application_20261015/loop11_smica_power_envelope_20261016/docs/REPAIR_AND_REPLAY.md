# S2 local staging integration correction (2026-10-16 KST)

**Observed material defect:** The initial sandbox runner expected `stage/source/baseline_response_matrices.npz`. The GitHub draft intentionally publishes code without this 156 KiB source NPZ, while the owner has the exact source already in Loop9. Consequently a GitHub-only continuation could not run tests despite the existing data being present.

**Smallest correction:** `locate_source(stage)` first checks the unmodified embedded archival `source/` input, else checks the existing checkout `docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz`. The source `source_operator` verifies the same SHA-256 `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007`; it will not silently accept another NPZ.

**Observed outcome:** Focused suite changed 11→12 passed. A synthetic local repo path without embedded NPZ was constructed as disposable test fixture, and the original source content resolved with no download, network, clone, or original file mutation. Output scientific source and numerical results unchanged. Original first-test results preserved in previous S2 intermediate archive, v2 is authoritative. Native fresh independent reviewer NOT_RUN. Physical EGS/Bianchi HOLD unchanged.
