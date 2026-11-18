# R67 coding track C1–C10: executable evidence and limits

Owner: HTT. Base 1d833bbe0e6c70a42f2d0af002c2e6a7cfcd0593. Branch research/r67-seven-axis-fusion-20261118. Executed on the owner's original checkout; no extra worktree or restricted source access. Source data left unchanged. The software makes no inference of new Bianchi physics or spacetime shear without a matched transfer.

| Stage | Executed computation or deliverable | Admission |
|---|---|---|
| C1 | Contract: full CF4 group table3/4, source-consistent 3-method relative calibration, Gaia-CRF3 6-mode proper-motion frame, seven-axis typed fusion. Defined explicit non-claims. | completed |
| C2 | Read canonical 42-node six-paper DAG, R61–R66 source histories, 2026-11-18 read-only workdir scan; fixed exact CF4 original table3/4, Gaia FITS 1,614,173-source file. | completed |
| C3 | Derive weighted source-group mean quotient, signed dipole+STF basis, common-source pair covariance and rank; Gaia tangent E/B l=1 basis, per-source 2×2 covariance; physical referent/epoch/frame/cross-source gate. | derived and Wolfram checked |
| C4 | Bounded plan: no new data downloads; vectorized source group method network; fixed B=32,768 group-level bootstrap, explicit exploratory radial variations; Gaia 100k-row chunks, 192 spatial-patch sandwich. | completed |
| C5 | Implement scripts/r67/fusion.py, run_r67_fusion.py, sensitivity.py, gaia_frame.py, likelihood_contract.py, plot_r67.py and three focused test modules. Real JSON, PNG/PDF produced. | completed |
| C6 | 15 targeted pytest tests passed on actual checkout. Synthetic physical-common-mode injection and 22D method-gauge recovery, exact E/B synthetic recovery, source row count, same-sky refusal, nuisance Schur. | implementation checked |
| C7 | Original38,053 source IDs match; primary 998 three-method connected groups,1090 contrast rows and rank22; Gaia valid1,614,173, quality1,580,645 and rank6. Same-group cancellation and reference-frame semantics verified by direct construction. | finite numerically checked |
| C8 | 2,048/8,192/32,768 bootstrap repetitions, radial nuisance orders0–3, posthoc four-residual trim, 192-patch spatial covariance sensitivity, hemispheres. Analytical score/actual original geometry comparison. | finite numerical sensitivity |
| C9 | Independent symbolic Wolfram exact three-method difference/quotient precision identity; same-context adversarial physics/implementation checks and test suite. Native-host subagent: NOT_RUN (no delegation tool advertised). Separate external CLI code-review gate attempted only if actual run receipt present. | scoped verification, no automatic manuscript-level independent PASS |
| C10 | Durable reports, typed fusion DAG and conditional data triggers, canonical DAG link; scoped branch commit/push only with observed validation and explicit independent-review caveat; original 42/paper acceptance preserved. | check delivery receipt; final acceptance remains pending |

## Reproducible commands
Use the existing repo virtual environment with PYTHONDONTWRITEBYTECODE=1, OPENBLAS_NUM_THREADS=1:
- python -B -m scripts.r67.run_r67_fusion --bootstraps 32768 --seed 20261118
- python -B -m scripts.r67.sensitivity
- python -B -m scripts.r67.gaia_frame
- python -B -m scripts.r67.plot_r67
- python -B -m pytest -p no:cacheprovider -q tests/test_r67_fusion.py tests/test_r67_gaia_frame.py tests/test_r67_likelihood_contract.py

## Source identities and failure boundaries
CF4 table3 SHA256 c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d.
CF4 table4 SHA256 b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94.
The Gaia FITS path is /mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits; exact byte hash should be recorded in provenance, not inferred from file size.
The existing CF4 Table3 group method modulus values have already been cross-calibrated by upstream catalog construction; the current analysis is a conditional reanalysis of the final published numbers. Unknown cross-method and global calibration covariance prevents cosmological anomaly significance.
The Gaia formal precision assumes independent quasars and ignores correlated scan/systematic/AGN jet motion; 192-patch sandwich is not a Gaia official systematic covariance. E/B l=1 is observer-frame morphology, not matter vorticity.
The conditionally-allowed likelihood contract does not infer data exchangeability or frame identity on behalf of its caller. Physical calibration/transfer is a separate source obligation.
No PR3/PR4 matched Commander temperature null was generated; no Bianchi polarized atlas, joint kSZ remote-dipole likelihood, or new source-specific DESI DR1 PV catalog was fabricated.

## Evidence classes
- Established/reused: original group zero-point overlap, Gaia E/B frame components, standard GLS/WLS/Schur, external Bianchi transfer literature.
- Derived: group contrast quotient and multi-method gauge/rank; transfer-compatible likelihood conditions; local projected Fisher formula.
- Numerically checked: CF4 full group original row validation, 32,768 group-bootstrap conditional laws, Gaia all-source E/B, 15 tests.
- Unresolved: shared catalog calibration, source selection, observer-to-global tilt transfer, CMB Bianchi transfer and high-l polarization, joint-sky cross covariance, independent physical statistical null and separate fresh agent review when not executed.

No input file under /mnt/extdrive/workdir was overwritten or deleted.

## Independent review and bounded repair (2026-11-18)
One fresh read-only Codex CLI reviewer produced NEEDS_REPAIR with two HIGH numerical/contract findings, two MEDIUM interpretation/provenance findings, and one LOW hash transcription finding. All five were repaired in a **single bounded parent-owned episode**; see REVIEW/review_closure.json. Targeted 19 tests passed and original CF4 32768-replicate estimates were unchanged. This is not a second independent reviewer PASS; no host-native subagent spawn tool was exposed. The original scientific NOT_READY_TO_SUBMIT remains unchanged. Remote commit identity is verified only after actual push.
