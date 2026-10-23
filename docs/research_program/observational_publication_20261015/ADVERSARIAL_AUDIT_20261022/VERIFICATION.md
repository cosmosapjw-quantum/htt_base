# Verification scope

Date: 2026-10-22. Baseline: `76595070beb97e52dce9f2d7a0ff1dbf3c289e98`.
This is a selected-file patch/test fixture, not a full checkout or full-repository test.
No native solver, ODE evolution, new large catalogue fit, package installation, main merge or submission occurred.

## Executed evidence

- Finite two-redshift script: 12 finite boosts, wrong-pipeline counterexample, attained correction-box endpoints,
  bandpass counterexample, fixed-data derivative and domain rejection. Maximum invariance residual
  `3.552713678800501e-15` mag. Independent reviewer called `main()` read-only and reproduced RESULT exactly.
- Wolfram algebra comparison: recorded `{0,0,0}` residuals in theory/WOLFRAM_CHECK.json.
  This is not a four-axis CAS admission. No new strong no-go admission.
- Nine source-response K03 tests passed; final staged run 0.018 s, exit0.
  Tests include aberration finite difference, field/covariance rotation, E1 divergence/curl,
  cross-sky fitted-mean covariance, bias KKT condition, and cosmic/local degeneracy.
  The source's printed-frame covariance parity **fails under the stated rounding model**;
  the test passes by preserving that discovered discrepancy, not by declaring the source covariance reconciled.
- Independent reviewer also found the frame discrepancy via a six-variable outer-relaxation LP.
  This and the author's ordinary-floating-point interval calculation are numerical checks, not formal interval proofs.
- Legacy graph audit and rational six-direction response rank reproduced by the independent reviewer.
  Frozen baseline result remains17/42; revised V03 is recorded separately.
- Actual Quaia auxiliary files: 1,279,519 bytes, published MD5 and locally measured SHA256 match;
  ZIP CRC and seven NumPy arrays inspected without extraction; FITS NSIDE64/RING structure inspected.
  First inspection rejected the ZIP directory entry as an unexpected member; corrected to skip directory entries,
  retaining checks on every data member. This is source schema qualification only.
- Existing downloader initially rejected the real879199-byte Quaia ZIP as `Unrecognized format`.
  New streamed ZIP handling validates it and upstream MD5 successfully.
- Downloader focused regression suite: **12 tests PASS**, final staged run0.047s,exit0.
  Covers known/unknown length uncapped transfers, explicit cap, length identity, disk shortage, gzip,
  streamed ZIP/no extraction, aggregate expanded bound, CRC corruption, MD5 mismatch,
  receipt SHA256 retention and refusal of MD5-only unreceipted adoption.
- Packet validation: all42 objective/acceptance/dependency contracts unchanged; all42 node packets
  and every historical/new task packet resolve. Only V03 scientific state changes; K03 remainspending.
  Revised summary18/42, scientifically ready nodes0, four executable new frontier actions ready.
- Default downloader plan selects the three Quaia resources and reports `max_bytes:null`, `fetch:false`.
  The owner mount/data cache was not inspected or changed here.
- `make_figure.py` generated PNG/PDF from the declared analytic tube and chosen ICRS covariance.
  PNG visually inspected; labels explicitly distinguish manufactured/conditional quantities from observed inference.

## Replay commands from the existing repository

```bash
python -B -m unittest discover -s tests/htt -p test_fetch_open_inputs_uncapped.py -v
python -B -m unittest discover -s docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/k03 -p 'test_*.py' -v
python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/theory/verify_two_redshift_null.py
python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/make_figure.py
python scripts/htt_open_input_packet.py
python scripts/htt_open_input_packet.py --task A22-03
```

Theory and plot commands regenerate their own scoped artifacts. A real-cache schema check additionally needs
the files named in the acquisition manifest and `data/inspect_quaia_inputs.py --data-root ... --output ...`.
The legacy audit script accepts an explicit DAG path; use the pinned baseline DAG to reproduce its historical
17/42 artifact, or the live DAG for the revised state. Do not compare these two inputs as if identical.

Runtime: Python3.12.14, NumPy2.3.5, SciPy1.17.0, Matplotlib3.10.8.
Requested authors: Sol/high for legacy/K03, Astra/xhigh for theory and narrow fetcher repair;
requested independent reviewer: Astra/xhigh. Observed backend identities: UNKNOWN.
Final independent closeout and candidate identities are stored separately.
No full-repository CI success is inferred from these scoped checks or from old PR workflow runs.
