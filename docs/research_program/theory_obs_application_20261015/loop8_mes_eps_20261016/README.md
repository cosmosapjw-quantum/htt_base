# HTT C8-OBS-MES-EPS: portable source-locked research package

Date 2026-10-16 KST. Source root: authenticated Dropbox-synced primary owner checkout of `htt_base`, pinned Git commit `13d8d85fa470d645d008986e8f77d8d0f70fdf54`. This directory is **an isolated portable research stage**, not a second Git checkout and not an overwrite of the owner's dirty files.

This package contains all **finite-coefficient sources required to rerun this specific conditional analysis**: 9 Planck common-mask processed low-ell arrays; 6 FFP10 processing choices with 300 matched source/noise sky pairs; Loop6/7 source registries; PR124 source; Loop7 next DAG; standalone code, 14 tests, 3 plots, numerical JSON, theory report and Codex handoff. Full raw Planck FITS and empirical covariant EGS derivatives are not available here; this stage cannot validate physics absent those inputs.

From the unpacked `htt_mes_eps_20261016` directory:

```bash
bash LOCAL_RUN.sh
# Optional: regenerate plots in fresh directory
python3 src/plot_mes_eps.py --result results/C8_OBS_MES_EPS_RESULT.json --ffp-pairs inputs/ffp_response/processing_coefficients.npz --output /tmp/htt_mes_eps_plots
```

`LOCAL_RUN.sh` verifies immutable source hashes, executes pytest, recomputes results in a disposable output directory and asserts JSON numerical identity with the frozen result. It does not touch the owner Git tree. Python numpy + pytest required; matplotlib only for plots.

Start with `docs/THEORY_AND_RESULTS_KO.md`, then `docs/DAG_PROGRESS.json` and `docs/CODEX_HANDOFF_KO.md`. Input provenance is in `docs/SOURCE_MAP.json`.

**Scientific state:** mathematical diagnostic completed in ChatGPT isolated container, 14 PASS; local workstation and native independent review NOT_RUN. Observer-frame radiation epsilon, Copernican spatial/time derivatives, finite upstream transfer and cosmological x/Q/Pi physical posterior HOLD.
