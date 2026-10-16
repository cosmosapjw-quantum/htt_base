# One-prompt-free local replay contract for HTT P3/H01

This is a self-contained package of the original source NPZ, Python module, runner, tests, results, and checksums; no user manual download is necessary to use the source in existing connected Dropbox. The GitHub PR publishes code and exact provenance, while the user's local source remains under:

`/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz`

With owner permission already granted for this project, local Codex can use the existing checkout and may copy this **single immutable source NPZ** into the published scoped `source/` directory if it does not exist, only after exact SHA check `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`. Never overwrite the original, never run git clean/reset/checkout on the dirty worktree.

For an isolated sandbox archive, run `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_hubble_window.py` and `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python src/run_h01.py`. The runner writes create-or-replace `results/H01_SOURCE_WINDOW_RESULT.json` in its working package; compare content-digest/NUMERICAL_IDENTITY against the archived original. Source NPZ bytes remain read-only. Do not treat these `H_W` outputs as actual physical H(z,n), inference, uncertainty, or observed anisotropy significance.

Review six-paper `PUBLICATION_DAG.json` H01 at original branch `research/htt-observation-publication-dag-20261015`, preserve 42 nodes and order, mark H01 `completed_scoped` only with tests, SHA, and scoped artifact. H03 becomes READY; H02 remains source blocked and X02 comparator must incorporate Kalbouneh et al. 2026. Keep historical PR #539 separate and no main merge.
