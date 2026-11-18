# R67 scientific and delivery verification

Date 2026-11-18, original checkout \`/home/cosmosapjw/Dropbox/bianchi/htt_base\`, branch \`research/r67-seven-axis-fusion-20261118\`, base commit \`1d833bbe0e6c70a42f2d0af002c2e6a7cfcd0593\`. Observations are read from \`/mnt/extdrive/workdir\`; no input mutations or data downloads were performed in R67. Original untracked material was preserved. Python scientific runs use \`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1\`.

## Real numerical execution

- \`.venv/bin/python -B -m scripts.r67.run_r67_fusion --bootstraps 32768 --seed 20261118\` → success; original CF4 group IDs 38053 exact matching table3 and table4; 998 multi-indicator groups; 92 triples; 1090 independent group-mean-free contrast rows; rank22; pair overlap 694/202/286. Conditional group-wild p-values FP–TF 0.1450761390, FP–SN 0.1760505356, TF–SN 0.8735390155, joint network 0.2448960908. Method-relative angular model full-sky RMS magnitudes 0.07781759, 0.10640970, 0.06342613 mag. Cross-catalog survey/selection and upstream shared calibration are **not** supplied.
- \`.venv/bin/python -B -m scripts.r67.sensitivity\` → success; radial order0–3 and posthoc large-residual controls explicitly exploratory.
- \`.venv/bin/python -B -m scripts.r67.gaia_frame\` → success; Gaia-CRF3 N1,614,173, quality1,580,645, rank6 E/B l1, E norm5.567204710 μas/year, B norm4.289544320 μas/year; formal and 192-spatial-patch sandwich errors differ, as do northern and southern subsets. **Not a cosmological vorticity detection**.
- \`.venv/bin/python -B -m scripts.r67.plot_r67\` → R67_FUSION_DIAGNOSTICS PNG and PDF, same actual JSON source.
- Additional CF4 bootstrap 2048, 8192, 32768 exploratory sensitivity results were preserved; no sample counts or p-values promoted to physical cosmological significance.

## Mathematical and code checks

- Exact Wolfram identity: marginalized group-mean precision equals covariance-aware pair-difference precision for arbitrary positive three-method variances. The three pair differences of a triple are not independent; correct rank2 contrast retained.
- First affected implementation suite: 15 tests passed. Independent Codex CLI *read-only* review found 2 HIGH code issues (rank-deficient QR; marginal/joint covariance inconsistency), 2 MEDIUM reporting/provenance (signed RMS; baseline protection), 1 LOW source hash transcription issue. Original reviewer verdict \`NEEDS_REPAIR\`.
- One finite coherent repair episode: fail-closed radial rank check; joint covariance must match marginals and require caller-provided source/independence provenance; nonnegative lnH RMS; baseline paper+42-node direct comparison against pinned \`git show\`; corrected CF4 table4 hash.
- New counterexample regressions and actual full CF4 32,768-draw rerun: **19 affected tests passed**, original scientific CF4 p-values/coefficients unchanged. Revision closed by targeted parent verification, not described as a second independent review PASS; see REVIEW/review_closure.json.

## DAG/preservation/delivery checks

- \`scripts/r67/build_r67_dag.py\` runs with baseline original 42 nodes and six papers exact comparison, outputs additive FUSION_DAG.json (7 research axes, 4 fused routes), seven conditional data triggers, and PROVENANCE.json with source/file hashes.
- \`scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml\` → 291 PRs, DAG valid.
- \`scripts/codex_harness/sync_pr_dag_mirrors.py --write\` → PR DAG/status mirrors synchronized; then \`--check\` to be executed as final gate.
- \`scripts/htt_publication_dag.py --validate\` → six papers, original42 nodes, no submission ready.
- \`git diff --check\` / selected files syntax / source identity / actual remote ref after push: see terminal result, do not infer success before execution.
- Canonical PR status completed count expected 226 after scoped R67, one more than 225 at baseline. 291 total cards. Percent PR completion is pure DAG bookkeeping, not physical research maturity.
- Host-native subagent creation: NOT_RUN (not exposed); independent review was a bounded separate Codex CLI read-only run, not a host-native subagent.
- The local working tree contained 1,084 preexisting unrelated untracked paths, neither staged nor modified by this assignment. R67-only staged paths are reviewed before committing.

## Scientific claim limit
\`EXPLORATORY_CONDITIONAL_NOT_COSMOLOGICAL_DETECTION\`. CF4 common group distance elimination is exact algebra in the declared source model. The working noise model and group wild-bootstrap do not supply the upstream method-by-method calibration posterior, sky selection covariance, LSS cross correlations or source-bound physical shear transfer. Gaia E/B proper motions are reference-frame fields, not measurements of present-matter shear/vorticity or global tilt. Other fused approaches are conditional proposals rather than executed joint physics likelihoods. Independent novel scientific significance remains under comparison with original CF4 and Gaia VSH/Bianchi literature. All P1–P6 paper submissions remain \`NOT_READY_TO_SUBMIT\`.
