# Jwst Same Host Covariance And Influence Sensitivity

Owner: HTT. Diagnostic-only; scientific admission not evaluated.

Numerical results and retained identities: `result.json`. Figure: `diagnostic.png` / `diagnostic.pdf`.

- cchp_trgb_jagb: 7 hosts; covariance-mode offsets 0.00168624 to 0.0872806 mag.
- shoes_jwst_hst: 13 hosts; covariance-mode offsets -0.0421764 to 0.0281975 mag.

- PSD covariance modes are declared sensitivity scenarios, not observed shared covariance
- Same-host shared geometry cancels exactly; no tilt or H0 measurement
- Source families remain separate; calibration/host overlap does not create independent anchors
- No calibrated p-value or total uncertainty from these modes
