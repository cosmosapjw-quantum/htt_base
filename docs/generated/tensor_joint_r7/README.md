# Tensor Joint R7 workstation delivery

**26/26 campaign nodes reached terminal outcomes; the full implementation plan is incomplete.** The retained implementation adds source-bound tensor, likelihood, confidence, nuisance and adapter kernels, and an actual resumable scientific campaign. [Implementation status](IMPLEMENTATION_STATUS.md) lists the unimplemented features separately from missing data and unresolved numerical calculations. No remote publication or merge was performed.

The branch starts at exact design commit `89a9a901e950cb186dcfedb95a250493fe4fd6fa`, a direct child of H `5702024e06eff4979087f07f86ee7131d13961ac`. It lives at `/mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R7-20260908/worktree` on `implementation/tensor-joint-r7-20260908`. The original `codex_emergency` checkout and its untracked files remain preserved.

## Results to read

- [Methods manuscript PDF](delivery/nodes/R7-24/methods.pdf), [LaTeX source](delivery/nodes/R7-24/methods.tex), and [separate integrated-data report](delivery/nodes/R7-24/integrated_data_results.md).
- [All 12 generated figures and their source-node manifest](delivery/nodes/R7-22/figure_manifest.json). All PNGs and all six PDF pages were opened. The settled PDF renders identically to the opened build; [render comparison](delivery/pdf_visual_equivalence.json).
- [Final scope-aware conclusion](delivery/conclusion.json), [validation cells](VALIDATION_RESULTS.json), and [review adjudication](ADJUDICATION.md). The two original independent FAIL reviews are retained; corrections received host regression verification in one repair-closeout round, with no second independent review.
- [Product-keyed dispositions](delivery/nodes/R7-21/science.json) retain inventory-only controls and explicit missing laws. No donor/product failure removes another donor/product capability.

The one supported empirical inference is **conditional on the selected released DESI BGS compressed Gaussian qiso summary model**:

| Quantity | Value | Conditional 95% confidence interval |
|---|---:|---:|
| qiso | 0.9828804416839027 | [0.9462387032298103, 1.019522180137995] |
| DV/rd | 7.924712263167666 | [7.629279348078372, 8.22014517825696] |

The fixed fiducial qiso=1 is accepted (quadratic 0.838550365535873; rank-one threshold 3.841458820694124). The released fixed Gaussian sampling assumption is explicit. True raw-catalogue coverage has not been independently established. This is not a posterior, anisotropic response, native solver result or Bianchi identification. The stat-only alternative is not multiplied into this selected syst law. [Exact scope and source ID](delivery/nodes/R7-19/science.json).

PR3/FFP10 full Q/O carriers are recomputed from the retained orthonormal-real harmonic rows. Both actual pools retain every ID, including unavailable decoder charts. All 1000 and 301 rows have unresolved exact orbit ranks under the fixed symmetric resource policy; no p-value is reported. WMAP9 is a descriptive temperature control. Actual CF4 CDS rows are retained, but their full group covariance is absent. JWST source-host offsets are fits under assumed independent quoted errors, explicitly scenario-only. PR4/NPIPE stays excluded and invalidated DESI PR151 numerical values are not consumed.

## Validation actually executed

- R7 suite: **75 passed**, with `-o addopts=''`; [log](delivery/logs/r7_scope_join_validation.log).
- Ten independent donor validation routes: **135 test executions passed**. Counts overlap the R7 suite and are not a count of independent scientific claims. [Per-route commands/logs](delivery/nodes/R7-02/science.json).
- Full consumed donor test files: **110 passed, 10 failed** on the corrected target import path. The failures concern two old PR309 dispatcher/acceptance checks, seven missing PR254 specification/publication/frozen-result wrappers, and one old HTT/MIO public-export expectation. They remain failures and were not resolved by importing whole donor branches. [Full failure log](delivery/logs/donors_target_full.txt), [command/environment](delivery/logs/donors_target_full.json).
- Gaussian operational stress: **11 declared cells, 10000 independent trials each** through the public acceptance kernel. All 99% Clopper–Pearson coverage/FPR gates pass. These finite-cell tests do not calibrate a real product by transfer. Repeated attempts with the same registered seeds are preserved and never pooled as new independent trials. [Cell results](delivery/nodes/R7-18/science.json).
- Wolfram/xAct, SymPy, Sage/Singular and Lean actually executed the same seven-obligation contract: [CAS_4AXIS_PASS adjudication](cas/cas_adjudication.json). It verifies fixed algebra and implications of accepted L=10 rational minors, not a fresh four-axis continuum-operator computation, pixel-error enclosure or physical model admission.
- Actual unchanged `--resume` created **no new attempts** and retained all 111 history entries. [Receipt](delivery/resume_validation.json).
- Final source paths are checked through actual module `__file__` values. Scientific executors use the worktree Python import roots, not an old editable installation. MLflow is optional and disabled by default; no live tracing environment was configured.

## Reproduce or resume locally

Use the existing compatible environment; no package installation is required for the delivered tests. The HDF5 reader uses a separately identified existing environment with h5py. Actual input archives remain in their original workstation locations.

```bash
cd /mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R7-20260908/worktree
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B \
  -m pytest -o addopts='' tests/r7 -q
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python -B \
  scripts/observed_runs/run_r7_campaign.py \
  --dag docs/research_program/tensor_joint_r7/campaign_dag.json \
  --run-dir /mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R7-20260908/campaign --resume
```

[Source bindings](source_bindings.json) are the original intake records; their initial `PENDING` integration-test fields are superseded by the actual per-donor results above. They retain the selected source bytes and original pins. [Location map](delivery/location_map.json) resolves copied evidence whose original absolute paths remain in the receipts. The full original campaign, failed attempts, archive inputs, ignored CAS run and environment are preserved outside this delivery copy; this is a local reproducible handoff, not a bundled public data release.

The next smallest data discriminator is an authenticated full CF4 group covariance and sampling-law sidecar in the original group order. Separately, unfinished implementation includes full multipole-vector ablation, generic non-Gaussian simulator calibration, additional default-driver bound-law execution, R3 stress/Jacobi adaptation, and remaining inventory-only control processing. These are not reclassified as successful or as absent physical data.

## Local closeout

[Delivery receipt](LOCAL_DELIVERY.json) binds the implementation/results commit and the actual validation counts. The bounded work unit terminates as `STOP_INVALID` for full-plan acceptance because named implementation obligations remain incomplete after its single repair-closeout round. This process decision does not invalidate the scoped conditional qiso result or the passing kernel tests. The required bounded-contract check passed; the ephemeral work contract is removed after this ordinary task result is recorded. No further review/repair wave is implied.
