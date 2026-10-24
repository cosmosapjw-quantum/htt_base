# Independent actual SMICA result review

**HOLD_ACCOUNTING_COMPLETENESS.** One blocking accounting finding; the exact-product delivered-map numerical component is conditionally sound. This review does not admit the original full-eight task, L03/H02, calibrated Pi, physical F/MES, native solver results, or family identification.

## Blocking finding SMICA-ACTUAL-F1 (P1)

`run_smica.py:323-325` resets the common phase after `debit()` has persisted its receipt. That persistence interval is in neither phase. The same pattern occurs at 352-353. The pre-native marker write at 370 is dropped by the reset at 378; `bounded_child` stops its timer at 246 before its terminal persistence at 269, and settlement persistence is also excluded. Final receipt/ledger writes at 412-417 follow the last charged timestamp at 409.

The existing 123.69659962807782-second sum and eight-account arithmetic are internally correct for the intervals recorded, but do not cover all wrapper wall time. The actual missing duration is UNKNOWN. The deterministic counterexample executes only the exact AST-extracted `debit` function with a virtual five-second persistence delay: through the same 16-second timestamp, only 11 seconds are charged. No producer, native data read, test batch, or projection was launched.

Minimal closeout: retain every existing byte and the native 110.38916298095137-second charge. Recover an authentic outer command elapsed measurement or justified bound, subtract the already charged intervals, and append only previously omitted common overhead once across the same eight accounts. Label a bound as conservative, never as an observed duration. Bind and ingest that successor before another same-lineage dispatch. If a reliable bound is unavailable, keep accounting HOLD. This finding does not call for a projection rerun or a second format-control batch.

## Source and numerical checks

IRSA confirms the PR3 full-mission SMICA polarization product at NSIDE 2048. Healpy 1.19.0 documents and implements implicit indexing when the scheme cannot be determined and `partial=False`. The row-p interpretation is therefore a named, exact-product compatibility inference, conditional on the already qualified released body; it is not established by row count alone. See [IRSA release table](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html), [healpy documentation](https://healpy.readthedocs.io/en/1.19.0/generated/healpy.fitsfunc.read_map.html), and [tagged source](https://raw.githubusercontent.com/healpy/healpy/1.19.0/lib/healpy/fitsfunc.py).

I independently checked the four implementation seals, exact input/packet/ACK, frozen operator/math/decoder/support seals, source qualification and body receipt seals, and unchanged qualified file stat. An 8640-byte header-only read confirmed header `a25bdcde…`, all four absent indexing cards, and the exact scalar 1E profile. No second full-body hash was performed. The public entrypoint requires the exact production identity; test-only fixture injection cannot be selected through its CLI. The reader preserves big-endian float32 Q/U offsets 4/8, K_CMB, Galactic COSMO, and unchanged U sign, and rejects scaling, heap/compression, contradictory indexing/profile, wrong field selection, invalid samples, and short reads. The five-test raw batch passed once before native launch.

The unchanged sealed kernel performs exactly the two original complete partitions, at 131072 and 131071 rows. Both use the saved 30021-cell support, selecting 30741504 native pixels. The saved full 24-vector contains 13 positive and 11 negative coordinates. Independent inverse STF calculations restore its signed canonical coordinates to at most 5.294e-23; each tensor is symmetric and trace-free. The largest saved partition difference is 1.3235e-23, versus minimum prescribed tolerance 1.0000016e-12. The largest reduction-only allowance is 1.2780e-15, about 1.0224% of the allowed tolerance/8. This excludes harmonic/libm and measurement error and is not a total-error certificate. Figure inspection and source inspection agree that all signed coordinates are plotted with explicit labels, K_CMB units, unchanged support, and a descriptive-only compatibility caption.

## Process and accounting lineage

The one native child exited 0 and was reaped after 110.38916298095137 seconds, under its 300-second bound. Loaded BLAS/OpenMP pools and observed child threads are 1. Child wait4 high-water is 159834112 bytes; the conservative sum of observed parent lifetime and child high-waters is 806756352 bytes, below 6 GiB. Launch MemAvailable is 16050626560 bytes and minimum sampled runtime MemAvailable is 15851122688 bytes, above the 10 GiB launch and 4 GiB runtime thresholds. These statements concern the declared wrapper/child scope.

The original failed attempt `2efa6827041549caa787f6de92fe4133` and charge 2.4969793090131134 seconds remain in sealed ledger `182cfde0…`. Sealed successors `300a2971…` and `a1c26745…` retain the original eight accounts and yield the actual SMICA base 301.22157064567614 seconds. Proposed terminal ledger `816e09a2…` reaches 413.2741632075183 seconds for SMICA and adds 1.6634295808908064 seconds to each other account. It requires the F1 additive reconciliation before acceptance as complete.

## Exact candidate and scope

Contract: `38bcd5ec436826c85b9507cf30cd0ae51c2899bcee8644a6db383c7f7fe28ff0`.
Input: `f38fad65711947960265183d3bd61a062fc883356366d445ad75b3b62cb8800d`.
Carrier: `ddceb8014d46544bf1b029bf83abb03ae9e8b2b88a48bbfc516f98bdf981b2d8`.
Numerical controls: `319c0ed3443e31b471daafd61c041a05d61fd2417f94c1496d8b2a4582ccf7e8`.
Figure: `fe65cdf07af68bfa5a5b854c17e62738f4338ec019be9ccdb20a1a9237d9edaf`.
All remaining exact identities and checks are in `REVIEW.json` and `NUMERICAL_AND_LINEAGE_CHECKS.json`.

Requested reviewer runtime: gpt-6-astra/xhigh. Observed runtime: UNKNOWN. The reviewer did not implement this candidate, did not consult prior verdicts as authority, and changed only this designated review directory. The completed numerical candidate can be reused for F1 closeout and then as an optional finite delivered-map comparator. Broader scientific admission remains HOLD.
