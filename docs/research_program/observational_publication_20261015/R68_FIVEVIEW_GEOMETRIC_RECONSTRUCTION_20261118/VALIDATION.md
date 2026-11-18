# R68 validation and honesty contract

Data and exact revision: parent 8089721e9ba74d79dadbb53d3158a5f76e9f96bf, original R66 source file OBSERVABLES.json SHA256 6d9c3f11a23995565dca25fe8ae02ef1ad79b3bc3f8ddf99f3c8c0a497b39d01, R66 embedded carrier 807b8eb391b6d150596ab431885f4b720bcafedd52fffdfe61c6db132661cc48. All original datasets and six-paper DAG acceptance remain unchanged.

Executed repository commands:
1. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.r68.fiveview_geometry
2. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_r68_fiveview_geometry.py

Most recent results: 14/14 focused tests PASS. Two actual R66 source-verified finite-band stress shape results: PR3 Q_rad=1.1637005109237419e-05, chi=-0.7074485821161334; PR4 Q_rad=1.2485285996402345e-05, chi=-0.6950341118626684. Neither is actual sky anisotropy significance or matter congruence shear. Separate mathematical toy: 85,000 isotropic white Gaussian STF5 nulls, unknown signed-amplitude axisymmetric mean; 95% max-axis statistic quantile 9.867821775865908; naive chi1 5% threshold would reject 49.65294117647059%. This is NOT a Planck/Commander end-to-end null or an empirically selected axis correction.

Independent verification: one read-only fresh Codex CLI reviewer examined theory, source and tests, returned NEEDS_REPAIR. Two high defects: nuisance-column scale dependent information; tiny nonzero target null reported as identified. Two lower issues: tiny STF trace threshold and tiny chi underflow; embedded R66 source hash insufficient. All four were repaired with one coherent bounded episode and added regressions, verified by 14 focused test PASS. Parent-managed targeted closure, NOT an additional independent reviewer PASS. See REVIEW.

Exact mathematical claims in THEORY_AND_PROOFS_KO.md are proved under their stated regularity/linear/physical constraints. Numerical checks are finite float64 and require explicit rank/precision confidence; identified=True never means a formal certificate of exact rank from floating input. Very small target null leakage is NUMERICALLY_AMBIGUOUS, not silently promoted to exact identification.

The methods paper itself, any original P1–P6 paper, physical global tilt, vorticity, shear, non-FLRW type identification and observational anomaly detection are NOT_READY_TO_SUBMIT or UNRESOLVED respectively. No automatic new data downloads and no forced publication/DAG closure.
