# R2-03 execution

Cwd `/home/cosmosapjw/Dropbox/bianchi/htt_base`, branch `r2/03-cmb-response-20261014`, frozen base `c5a683eba0ef1a7d10cc5a7bd6cb6b853bc69eb1`. Existing unrelated dirty/untracked files preserved. Requested executor gpt-6.1-sol/medium; observed runtime UNKNOWN. No branch, commit or push operations.

Prefix for all runs: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=htt:htt/htt:htt/src`.

1. `/home/cosmosapjw/venv/bin/python -m pytest tests/htt/test_r2_cmb_product_bridge.py -q`: exit 0, 10 passed; `raw/tests_first.log`.
2. `/home/cosmosapjw/venv/bin/python scripts/r2_cmb_product_diagnostic.py --output docs/observational_upgrade_r2/R2-03/raw/diagnostic.json`: exit 1, missing astropy; `raw/diagnostic_first.{stdout,stderr}`.
3. `/home/cosmosapjw/venv/bin/python -m pytest tests/htt/test_r2_cmb_product_bridge.py tests/r7/test_cmb_product_response.py htt/htt/tests/test_teff_extended.py -q`: 13 passed, 2 failed from missing healpy; `raw/tests_affected.log`. No package installation.
4. `/usr/bin/python -m pytest tests/htt/test_r2_cmb_product_bridge.py tests/r7/test_cmb_product_response.py htt/htt/tests/test_teff_extended.py -q`: exit 0, 15 passed, one existing matplotlib Axes3D warning; `raw/tests_affected_system.log`.
5. Initial `/usr/bin/python scripts/r2_cmb_product_diagnostic.py --output docs/observational_upgrade_r2/R2-03/raw/diagnostic.json`: interrupted exit 130 during original multi-GB hashing at controller direction; raw streams `raw/diagnostic_system.{stdout,stderr}`. Preserve the first interrupted attempt.
6. Final same command after default header-only original provenance: exit 0; `raw/diagnostic_bounded.{stdout,stderr}` and `raw/diagnostic.json`. Original full-byte hashing is now explicit optional `--hash-original-fits`; numerical R8 NPZ/JSON inputs remain hashed.
7. Additional NILC/SEVEM original FITS header inspection via `/usr/bin/python`/astropy: exit 0, `raw/released_additional_headers.json`; no full-byte reads.
8. `/usr/bin/python` package-version capture: exit 0, `raw/runtime_versions.json`.

No proof rerun. Unit references use full-sphere Gauss-Legendre/uniform-phi quadrature, independent harmonic evaluation, rotation, centered gradient differences, nonlinear omitted-mode envelope, and an actual callable beam/removal/mask injection. The existing R7 suite exercises NSIDE64 zero/nonzero boost in the interpreter with healpy installed.

Web intake 2026-10-14: [Planck 2018 IV arXiv v2](https://arxiv.org/abs/1807.06208) verified the four component methods and release limitations. The official [PR3 DOI](https://doi.org/10.5270/esa-zfx8b4s) tool open failed; retain the resolvable owner-supplied release identity. Monopole/dipole treatment follows each product's supplied removal convention. No independent physical dipole is estimated from residual ell1.

## Reviewer scope repair

Qualified the module docstring and matching report language to each product supplied removal convention. No numerical implementation changed. Focused bridge suite using the existing `/usr/bin/python`: exit 0, 10 passed; `raw/review_scope_repair_tests.log`. Original numerical diagnostic and its generating code hashes retained unchanged. Previous candidate return preserved in `PRE_SCOPE_REPAIR_RETURN.json`; current source hashes are in `RETURN.json`.
