# PR-R9-MULTIDEPTH — real SDSS PV depth features and full mock covariance

Base: `c532862651235ed0586a0677b61a43b2e09b3c85` on
`implementation/project-catalog-20260912`. Owner: obsstat/root.

The previous executable product was one DESI scalar. This change connects the
official SDSS PV v1.1.0 catalogue and its complete released mock catalogues to
four cumulative depth windows. Each catalogue supplies one 36-component vector,
with its angular projection and shell response fitted again on that catalogue.
Training and evaluation are split by simulation box, retaining all eight
observers together. The common adapter preserves cross-depth Cjk, HCHᵀ, the
initial observation block and all corresponding mean/response transforms.

The result is a release-feature diagnostic with estimated moments. Public mocks
do not repeat the preferred group-richness correction, CF3 calibration, or the
survey-fitted upstream generator/selection/FP procedure. Those omissions prevent
a qualified selected observation law and common state–jet–anchor coverage.
The free eta zero point remains exactly degenerate with the shell monopoles.
No covariance jitter, dropped source rows, Gaussian likelihood, new probability,
or alpha allocation is used to bypass those limits.

## Evidence and validation

- `analysis.json` defines the exact consumed extraction. The published data and
  complete mock archive are checked against official MD5 values; fresh SHA256
  identities and numerical source hashes are recorded in final provenance.
- `validation_repair.json` and `tests_repair.stdout` record 25 passing tests,
  including the actual runner's 36-by-37 rank/null/sign regression requested by
  independent review. The original c532 55-test and DESI evidence is unchanged.
- `reader_initial_failure.json` preserves the real repeated-ID parsing failure.
  The repaired reader retains every row and both source ID and row-local identity.
  The partial-archive first-member smoke remains explicitly developmental.
- The initial independent review and its exact pre-repair source snapshots stay
  under `.agent-harness/runs/R9-MULTIDEPTH-20260913/`. The final source-bound full
  replay and same-reviewer closeout are separate from that first result.
- `harness_identity.json` records both registered original ZIP digests;
  `global_policy_refresh.json` records the user-requested global policy reapplication
  to `0b6022e1`. Actual hook dispatch/model identity is not verified.

## Preserved limits and next action

R8 STOP_INVALID, 25 unresolved pools, CF4 quarantine, PR4 skip, and
production/empirical/novelty/four-axis HOLD are unchanged. R9-24 FORMAL_DEPTH and
R9-25/26/27 scientific capabilities are not admitted. Family alpha remains 1/20,
each product 1/80, CMB internal allocations 1/160; this diagnostic consumes zero.

The next executable scientific step needs the upstream selected-law inputs named
in README.md. Fibre comparison remains a separate ambient-STF-direction task.
The original `revision2/run_checks.py` evidence is retained without another replay.
This PR is one coherent product execution, not a new release or scientific claim.


## Root adjudication and execution closeout

The full release-feature replay completed with exit 0 in 357.9186 seconds:
2,048 catalogues, 256 boxes, zero failures, and a 1,024/1,024 catalogue split
across disjoint 128/128 box sets. All source/config hashes in final provenance
match the code used here. The 36-by-36 C has numerical rank 36. Direct transformed
sample covariance agrees with TCTᵀ to 2.7755575615628914e-17 dex²; restoration
including Y0 agrees to 1.474514954580286e-17 dex. Cross-depth blocks are retained.

The independent initial review found one medium regression gap, not an erroneous
current zero-point response. The actual helper and rank/null/sign test close it.
The same reviewer independently recomputed the final saved-vector moments,
transforms, responses, split and identity bindings, and returned scoped PASS in
`.agent-harness/runs/R9-MULTIDEPTH-20260913/results/repair_closeout.json`.
Root accepts this bounded extraction/estimated-moment execution. The missing
upstream selected-law stages and physical common coverage remain unavailable.
No R9 scientific capability or admission follows from this result.

The current-run aggregate remains NOT_A_WHOLE_CURRENT_RUN_PASS: the initial
review's exact input seals bind the preserved pre-repair sources. Administrative
pointer closure preserves that result and its snapshots; it does not rewrite a
whole-run PASS. Default-cwd subagent hooks used a different checkout/run, so launch
and executing-model evidence remain unverified. Review timing is self-declared,
not a measured runtime receipt. Actual analysis timing is in final_execution.json.
The interrupted initial curl transport and later recoverable connection timeout
are retained in the external run and copied archive_download.log; official final
archive identity passes. No analysis failure is hidden by a retry.

Canonical PR-R9-MULTIDEPTH completion denotes this diagnostic capability only.
The canonical campaign records full estimated feature Cjk separately from the
unavailable selected observation law and physical coverage. The prior 55-test,
DESI interval/rejection and reference/Fibre records remain unchanged.
