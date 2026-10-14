# Delivered Reconstructed Kappa Feature Rank

Owner: OBSSTAT. Diagnostic-only; scientific admission not evaluated.

Numerical results and retained identities: `result.json`. Figure: `diagnostic.png` / `diagnostic.pdf`.

- q_raw: upper rank 51/201, rank fraction 0.253731.
- q_controlled: upper rank 52/201, rank fraction 0.258706.

- Fixed 200 training and 200 calibration units; no post-score split choice
- Raw and controlled ranks are dependent comparisons; no minimum-rank selection
- Rank interpretation is conditional on delivered-unit exchangeability
- Cache receipt reuse; raw map/QE processing was not rerun
