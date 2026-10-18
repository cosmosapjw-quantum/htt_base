# L03 source-matched pilot execution

Existing checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
Branch at launch: `research/htt-sixpaper-goals-robustness-20261018`.
HEAD at launch: `5450b04442a400aa08e71f11565e774691590fa9`.
Origin: `https://github.com/cosmosapjw-quantum/htt_base.git`.
Historical continuation baseline: `1e095a2749cce9b28e45aac043a82218c21f84e5`.
Requested worker: `gpt-6.1-sol/high`; observed runtime model/effort `UNKNOWN`.
No child commit/push, nested agent, new checkout, solver, or ODE run.

Ownership is only this new directory plus the create-only external coarse cache.
Existing L01/L02 working changes are preserved. No canonical node completion is
asserted by this worker. L01 is awaiting its independent finite gate at intake.

Initial narrow tests:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L03_EXECUTION_20261018/test_source_matched_pilot.py
```

First run: `13 passed in 12.15s`.
After adding noise-amplitude limit tests: `16 passed in 2.54s`.
After adding the read-only L02 adapter and its tests: `21 passed in 4.67s`
(same command with the whole L03 directory as the test target).

Original eight-pair command (attempt 1, PID 44722 / terminal session 97221):

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L03_EXECUTION_20261018/source_matched_pilot.py --coarse-cache /mnt/extdrive/workdir/htt_open_data/provenance/L03_ORIGINAL_SELECTED_IQU_8PAIR_20261018.npz
```

Exactly IDs 00000 through 00007, one CMB and one noise-plus-systematics file each.
The script verifies actual bytes against the existing 1,299-entry raw SHA manifest,
then gathers RING native pixels by the exact NESTED child identity. Every selected
child index must pass `ring2nest(nest2ring(index)) == index`. Each component keeps
I/Q/U together. The final independent unit count remains eight rows.

The K1 cache is reused unchanged for the original temperature mask and source IDs.
Its existing map reduction and the six-processing T-only bank are not replaced or
rerun. Fresh T projection is necessary for the source-matched native-window
child-average operator, which is not the former map reduction.

Ancillary intake failures, not numerical failures:

- The historical `scripts/run_htt_planck_multisplit_spin_20261015.py` is absent in
  the current tree. Its original operator was read with `git show` at
  `c2889730d2b5e5b778951f15e8f09afd55bed4e3`; no file was restored or changed.
- The similarly named H02/L03 historical source archive does not include its
  `inputs/processing_coefficients.npz` in the current checkout. Its existing
  published JSON/code were inspected, and its completed 300-sky scan was not rerun.
- Direct browser open of the official A&A article returned `403 Forbidden`.
  Search-index primary-source text returned section 3.5 and sections 4.4.2–4.4.3.
  This is not represented as a successful direct article download.

The original L01 bridge and the three native P masks are read-only dependencies.
No observed native map is scanned; no SHT is run. A single low-band healpy synthesis
checks the finite Wigner-d chart against the original healpy spin convention.

Downstream sensitivity/plot command after the pilot:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L03_EXECUTION_20261018/diagnose_and_plot.py
```

The latter uses only the saved 8×2×96 coefficient bank. Noise amplitude ×0.95 and
×1.05 are deterministic nuisance perturbations of the same rows, not new skies.
The whole-repository test suite is not run for this bounded research increment.

Parent-authorized next finite calculation (no additional raw map scan):

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L03_EXECUTION_20261018/apply_l02_family.py
```

This imports the completed L02 kernel read-only, checks its original archive's
explicit spin-column metadata, then computes all T/E/B and TE/TB/EB descriptors
for five fixed component/amplitude variants of the same eight rows. No family
maximum, null rank, physical p-value, or L04/node completion is produced.

At elapsed approximately ten minutes, the first CMB file's full-byte hash had
finished and its FITS memmap was open in selected-child gathering. There were
no completed components or durable numerical results yet. `/proc/44722/io`
reported rchar 2,349,376,606, while read_bytes advanced slowly through approximately
108 MB; VmHWM was 761,384 KiB and VmSwap 304,656 KiB. Kernel wait was
`folio_wait_bit_common`. The session and parent user cgroups had no memory
high/max cap and no OOM events. Global IO pressure was high. These observations
classify slow local I/O/paging, not an external scientific missing-input result.
Parent stopped its own unrelated broad file search; no source process or input
was touched. A sequential RING streaming alternative was proposed to the parent.

Parent explicitly authorized the bounded performance-only repair. Immediately
before termination, the result directory and external cache were absent and no
`PAIR_COMPONENT_DONE` line had occurred: zero completed components/IDs. The old
source is preserved byte-identically in `attempt1_random_gather.py.preserved`, SHA
`83d82f855e68fe2c6b719b45d72721fa138454e733eb46fd3e91c91372b1650c`.
`ATTEMPT1_PERFORMANCE_OUTCOME.json` records the raw I/O/performance observation.
SIGTERM was sent only to PID 44722; session 97221 returned exit 143 and empty
stdout. The process was verified absent. No completed unit was replayed.

The repair retains the original gather function for comparison and changes only
traversal to sequential RING chunks, exact `ring2nest`, native mask lookup and
parent `bincount` accumulation. Masks, selected support, source hashes, field
values, coverage normalization, harmonic fit and existing tolerances are unchanged.
New tests use nonconstant three-field big-endian float32 data in the actual
1024-pixel FITS-vector layout, distinct native/coarse masks, inverse-order and
masked-invalid counterexamples. Old and new reductions agree within 2e-20 K plus
2e-14 relative tolerance, and coverage agrees exactly. This compares summation
implementations; it does not loosen a scientific acceptance tolerance.

After the repair: `25 passed in 6.42s` for the complete L03 directory.
The actual-layout equivalence fixture was subsequently strengthened to use the
real FITS interleaved I/Q/U row stride (12,288 bytes with 1,024 big-endian float32
values per field), rather than three separately contiguous field arrays. The
two affected scalar/vector cases passed: `2 passed, 18 deselected in 2.13s`.
This changed tests only; the executed driver/results did not change or rerun.
The identical eight-ID command was launched as attempt 2, PID 97183 / terminal
session 26480. Same task, IDs and cumulative execution; no cost or identity reset.
The new driver prints support-verification, source-byte-verification and
component-completion progress separately. Final numerical receipts bind the
attempt-1 record and the repaired executing code.

Attempt 2 observed progress: support verified at 22.7634 s; actual CMB00000 hash
verified at 27.8943 s and component projection completed at 33.8506 s; noise00000
hash verified at 38.4830 s and projection completed at 44.3358 s. These are
completed component calculations, not a claim that the complete bank existed then.

Attempt 2 final raw outcome: session 26480 returned exit 0. All eight paired IDs
and 16 source-component hashes completed; last noise component completed at
203.6823 s and final create-only numerical outputs at 205.8075 s. Peak RSS was
949,524 KiB. No covariance inverse or null rank was computed. The first attempt's
observed twelve-minute local performance failure remains part of cumulative
execution; the 205.8075 s figure is attempt 2 only, not the total task duration.

`diagnose_and_plot.py` returned exit 0 and generated both PNG/PDF files plus the
noise-amplitude JSON. Maximum absolute fractional coefficient-energy shifts for
noise ×1.05 were T 0.00032641253907872425, E 0.0471444910122798 and
B 0.10212645065489379. These are fractional values; multiply by 100 for percent.

`apply_l02_family.py` returned exit 0: exactly eight independent pair IDs,
40 variant rows, 120 T/E/B field-descriptor rows and 120 same-row cross-field
descriptors. Its eight actual baseline rows passed 432 field transformations and
432 cross-field SO(3)/O(3) transformations. Maximum absolute error was
8.271161533457416e-15 under the unchanged inherited 2e-11 tolerance. Noise ×1.05
maximum absolute squared-axis-overlap shifts were T 0.00043560915484497365,
E 0.04042530428976798 and B 0.020538562038866948.

Both generated PNGs were opened and visually inspected: labels, limits, curves,
units and diagnostic/coverage caveats are readable. No artifact was regenerated
solely for readback. One NSIDE64/ell≤5 inverse spin synthesis is the injection
control; the source-processing operator's `SHT=false` means no source SHT, and
no native-resolution forward or inverse transform is performed.

Final numerical bank: 28,901 bytes,
SHA `75a9a46c3cb2f576c994fefec248805cc604532345f7843bcd487ca848953123`.
External coarse cache: 9,852,906 bytes,
SHA `6cd72d8461f1dc61b430343a34fdb335921c47465f33140f78396b915274d5f0`.
The original physical acceptance remains HOLD. Parent integration and fresh
independent scientific review are the next transitions; this worker publishes
no commit and marks no canonical node complete.
