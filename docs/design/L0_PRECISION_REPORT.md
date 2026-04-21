# L0 Precision Dashboard — ✅ PASS

- **Spec version**: `v1.0-w3d5a`
- **Generated**: 2026-04-17T14:38:13.394208+00:00
- **Checks**: 21 / 21 passed (7 with warnings)

## Check table

| check_id | category | stat | oracle | observed | tol | verdict | notes |
|----------|----------|------|--------|----------|-----|---------|-------|
| `I_3[BE, eta=0]` | moment | BE | 6.49394 | 6.49394 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_4[BE, eta=0]` | moment | BE | 24.8863 | 24.8863 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_3[MB, eta=0]` | moment | MB | 6 | 6 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_4[MB, eta=0]` | moment | MB | 24 | 24 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_3[FD, eta=0]` | moment | FD | 5.6822 | 5.6822 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_4[FD, eta=0]` | moment | FD | 23.3309 | 23.3309 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_4/I_3[BE]` | ratio | BE | 3.83223 | 3.83223 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_4/I_3[MB]` | ratio | MB | 4 | 4 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `I_4/I_3[FD]` | ratio | FD | 4.10596 | 4.10596 | 1.0e-10 | PASS | rel_err=0.00e+00 |
| `Sigma_2[BE]` | ch05_cross_ref | BE | 2.04386 | 2.04386 | 1.0e-10 | PASS | ch05 Eq.; rel_err=0.00e+00 |
| `Sigma_2[MB]` | ch05_cross_ref | MB | 2.13333 | 2.13333 | 1.0e-10 | PASS | ch05 Eq.; rel_err=0.00e+00 |
| `Sigma_2[FD]` | ch05_cross_ref | FD | 2.18985 | 2.18985 | 1.0e-10 | PASS | ch05 Eq.; rel_err=0.00e+00 |
| `MB_gram_diag[n=5, alpha=2]` | gram | MB | 2 | 2 | 1.0e-13 | PASS | diag_rel_err_max=3.00e-14 |
| `MB_gram_offdiag[n=5, alpha=2]` | gram | MB | 0 | 2.71041e-15 | 1.0e-13 | PASS | off_diag_max=2.71e-15 |
| `MB_twofield_Gram_kappa` | reproducibility | MB | 54.3 | 54.3149 | 5.0e-02 | PASS | W2D5 reference 54.3; rel_err=0.000 |
| `roundtrip_p95[amp=0.05]` | roundtrip | — | 0 | 2.20646e-10 | 1.0e-08 | PASS | worst p95 across 9 (xi, n) cells |
| `roundtrip_worst[amp=0.05]` | roundtrip | — | 0 | 1.50856e-09 | 1.0e-07 | PASS | worst max across 9 cells; single-trial outliers documented |
| `roundtrip_p95[amp=0.1]` | roundtrip | — | 0 | 1.62861e-11 | 1.0e-08 | PASS | worst p95 across 9 (xi, n) cells |
| `roundtrip_worst[amp=0.1]` | roundtrip | — | 0 | 1.00799e-09 | 1.0e-07 | PASS | worst max across 9 cells; single-trial outliers documented |
| `roundtrip_p95[amp=0.2]` | roundtrip | — | 0 | 7.5893e-11 | 1.0e-08 | PASS | worst p95 across 9 (xi, n) cells |
| `roundtrip_worst[amp=0.2]` | roundtrip | — | 0 | 4.189e-08 | 1.0e-07 | PASS | worst max across 9 cells; single-trial outliers documented |
