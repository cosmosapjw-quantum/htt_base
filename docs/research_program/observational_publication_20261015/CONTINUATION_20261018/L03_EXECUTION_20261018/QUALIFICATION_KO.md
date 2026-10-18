# L03: original-support FFP10 I/Q/U pilot and remaining input law

Owner `obsstat`; claim tier `C0`; scope `DIAGNOSTIC_ONLY`; transfer source `none`.
This is preparation for the original L03 goal, not canonical completion.
L03 remains `HOLD`, and the paper gate remains `NOT_READY_TO_SUBMIT`.
The repaired execution returned exit 0 after 205.8075 s. All 16 selected raw
source SHA checks and all eight paired projections completed. Independent review
is pending; numerical execution is not node admission.

## Research question and source experiment

The original acceptance requires simulation ID as the independent unit and actual
and null data processed with the same mask, beam and foreground law. This work
tests the first executable part: whether genuine existing SMICA FFP10 I/Q/U
realizations can traverse the original L01 native-window child-average estimator
with the original temperature and polarization supports, rather than a T-only
surrogate or a new synthetic sky.

Exactly eight CMB IDs and eight noise IDs, 00000–00007, are selected before the
new coefficients are examined. Each pair is one diagnostic simulation row.
The numeric pairing is deterministic one-to-one coupling, not evidence that CMB
and noise share an upstream random seed. Temperature, Q and U from each physical
component are kept together; E/B/T do not count as separate independent skies.
There is no crossed reuse of 999×300 combinations.

Primary-source qualification: [Planck 2018 IV, section 3.5 and section 4.4.3](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html),
DOI `10.1051/0004-6361/201833881`, describes 999 CMB simulations including scanning
and asymmetric beams, and 300 noise-plus-systematics simulations propagated with
the real-data component-separation weights. It recommends testing sensitivity to
noise amplitude changes of ±5% and documents scale-dependent simulation mismatch.
That supports a fixed-weight source-conditional experiment, but does not establish
exchangeability for this estimator. Search-index primary-source text was available;
direct article open returned HTTP 403. No additional input was downloaded.

## Exact operator and convention

The original observed estimator is recovered from Git object
`c2889730d2b5e5b778951f15e8f09afd55bed4e3:scripts/run_htt_planck_multisplit_spin_20261015.py`.
The current working tree need not contain that historical script.

Both lanes first AND native common/HM/OE masks at NSIDE2048. Native children must
have at least 0.995 coverage in a coarse parent. T additionally intersects the
unchanged K1 confidence mask. This gives exactly 26,846 selected T pixels and
30,021 selected polarization pixels in RING64. The P selected-mask and native
window SHA must match the read-only L01 `ORIGINAL_SELECTED_SUPPORT_RESPONSE.json`
bridge, whose own SHA is frozen in the new driver. Actual mask-file hashes are
checked against existing source identities.

Local FFP10 FITS contain `INTENSITY`, `Q-POLARISATION`, `U-POLARISATION`,
NSIDE2048, RING ordering and `K_CMB`. Unlike the observed source's NESTED layout,
these are vector-column RING tables. The driver reads sequential RING chunks,
maps every native pixel to its exact NESTED index and accumulates the fixed-mask
sum and count in its coarse NESTED parent. Every visited child passes an
inverse-index round-trip. It then applies the same within-parent valid-pixel mean
and RING64 OLS. It does not assume a RING vector was already NESTED.
COORDSYS is absent in these simulation headers; the Galactic frame is the release
convention, recorded as such, not a header observation.

T fits simultaneous real harmonics ell0–5 and retains ell2–5 (32 coefficients).
Polarization fits joint Q/U against the 64-column real E/B ell2–5 design in the
original Galactic local-polar chart, per ell E then B, with m0/cos/sin layout and
`a_lm=(c_cos-i*c_sin)/sqrt(2)`. A native healpy low-band synthesis checks the
independent finite Wigner-d design. There is no beam reapplied, deconvolution,
SHT, native observed-map reread or polarized parallel transport. Child averaging
of Q/U intentionally reproduces the original estimator; it is not asserted to be
a transported physical polarization field. Cut-sky finite regression coefficients
are not identified cosmic alms or power spectra.

The existing K1 cache and the completed six-processing T-only bank remain unchanged.
K1 supplies the original confidence mask and checked initial IDs. A fresh T lane is
needed here because native mask-before-child-averaging is a different operator from
the older reduced map. No completed 300-sky scan is repeated.

## Outputs and validation

`results/PILOT_COEFFICIENTS.npz` stores separate signal and noise-plus-systematics
coefficients `[8,2,96]` and their paired sums `[8,96]`, with both component ID
arrays. The first 32 entries are T; the next 64 follow the interleaved E/B order
above. `results/PILOT.json` records actual selected source hashes, support hashes,
operator controls, environment, memory and run time. The create-only external
coarse I/Q/U cache allows all later finite-statistic work without reading the large
FITS again. Maps are zero outside their stated selected support, which is recorded
in that cache; those zero values are not reconstructed sky measurements.

`results/NOISE_AMPLITUDE_SENSITIVITY.json` and the PNG/PDF plot compare the same eight
rows under noise amplitude 0.95, 1 and 1.05. They report coefficient-energy shifts,
not an ensemble distinguishability or coverage test. The empirical joint matrix
has 96 columns and only eight rows; its centred rank can be at most seven.
No covariance inverse, physical p-value, anomaly claim or independence inference
from a lag-one correlation is produced.

Actual coefficient-norm ranges over these eight rows, in microK_CMB:

| Field | CMB component | Delivered noise-plus-systematics component | Sum |
|---|---:|---:|---:|
| T | 97.4855–137.8567 | 0.8831–1.1033 | 97.7993–137.9985 |
| E | 0.6630–0.9832 | 0.4782–0.6838 | 0.6680–1.1174 |
| B | 0.0868–0.1721 | 0.3973–0.5494 | 0.4301–0.5592 |

In this particular delivered-field finite regression, the noise-plus-systematics
B coefficient norm exceeds the CMB component norm in every row. This is an
operator/source diagnostic, not an identified physical B signal or a cosmic
polarization fraction. The source CMB B lane includes the input model and the
original cut-sky/child-average response; it is not assumed pure primordial B.

Increasing the same-row noise amplitude by 5% gives the following maximum absolute
changes across the eight IDs:

| Field | Coefficient energy change | Joint squared-axis-overlap change |
|---|---:|---:|
| T | 0.03264% | 0.0004356 |
| E | 4.71445% | 0.0404253 |
| B | 10.21265% | 0.0205386 |

The first column is norm-squared of the finite coefficient vector, not a full-sky
power spectrum. The second uses L02's fixed ell2/3 principal headless axes.
These are maximum deterministic nuisance shifts within eight paired rows, not
sampling uncertainty or a robustness threshold test. Negative 5% changes and all
individual signed descriptor shifts are retained in the JSON outputs.

The T and P design conditions reproduce 3.6013785312 and 3.1309622771 respectively;
the native low-spin injection relative error is 3.57e-15. Map-level signal+noise
projection closure is at most 4.90e-15. The centred 8×96 matrix has rank seven,
as expected, and was never inverted. The external coarse cache is 9,852,906 bytes,
SHA `6cd72d8461f1dc61b430343a34fdb335921c47465f33140f78396b915274d5f0`;
the 28,901-byte coefficient bank has SHA
`75a9a46c3cb2f576c994fefec248805cc604532345f7843bcd487ca848953123`.
Peak RSS was 949,524 KiB. The eight actual baseline rows pass 432 field and 432
cross-field SO(3)/O(3) transformations, with maximum absolute error 8.28e-15
under the inherited 2e-11 tolerance. Both PNG plots were visually inspected.

The narrow test suite checks exact agreement with direct NESTED averaging for
scalar and vector-column RING inputs, detects the wrong-order reduction, rejects
invalid source values on fixed support, accepts irrelevant masked invalid values,
rejects reused/permuted noise IDs, checks actual source-byte changes, verifies
finite OLS heldout injections/linearity and singular-design rejection, and checks
the zero-noise/noise-only limits of the ±5% amplitude calculation. New versus
original gather is compared on nonconstant big-endian float32 I/Q/U with the
actual 1024-value vector-column layout and differing masks. See
`EXECUTION_LOG.md` for commands and raw outcomes. No whole-repository suite is run.

The first random-access implementation was stopped with explicit parent approval
after reproducing a local I/O/paging failure before any component completed.
Its exact source and observed process outcome are retained. The second attempt
uses the same eight IDs and task accounting; it changes traversal/summation order
only. No scientific convention, input identity or acceptance tolerance is relaxed.

`results/L02_ON_EIGHT_PAIR_PILOT.json` and its figure apply the completed read-only
L02 family to all three fields and TE/TB/EB cross-fields on these same rows. The
five variants are signal-only, noise-plus-systematics-only, and signal plus noise
at amplitudes 0.95, 1 and 1.05. Forty variant rows and 120 field descriptors still
contain only eight independent pair IDs. The adapter validates the original
archive's explicit spin-column chart, retains unknown/degenerate descriptors, and
tests physical SO(3)/O(3) covariance on the eight actual baseline rows. This is
an executable downstream source-conditional preparation, not L04 significance.

## Acceptance decision and exact missing input

| Original L03 requirement | Evidence from this increment | State |
|---|---|---|
| Genuine matched I/Q/U input through original selected support and regression | Eight actual source pairs, byte identities and deterministic reduction controls | Diagnostic component, subject to independent review |
| Independent simulation ID units; no noise recycling | Fixed eight distinct paired IDs, I/Q/U retained jointly, rejection tests | Finite bookkeeping checked |
| Same full observational beam/foreground/systematics/selection law | Fixed-weight full-mission inputs are informative; complete law is not delivered here | HOLD |
| Joint HM1/HM2/OE1/OE2 dependence | Current local pilot files supply no matching split members | HOLD |
| Exchangeability, stochastic heldout coverage and null autocorrelation qualification | Eight rows and algebraic injections cannot establish these | HOLD |

The missing payload is a source-identified same-realization tuple of SMICA
HM1/HM2/OE1/OE2 signal and noise-plus-systematics products, with their common
simulation/seed mapping, split-specific weights and effective response, plus a
justified residual-foreground/weight-estimation and selection treatment for the
actual statistic family. The primary release may provide additional split products;
this is a statement about the current delivered local inputs, not an assertion
that no such public products exist. Split differences are not replaced by
independent noise or treated as extra skies.

Even for a narrower full-mission claim, statistic-specific coverage and residual
foreground qualification remain required. A finite ell2–5 regression can respond
to higher input multipoles through masks and child averaging; the paper's generic
large-scale simulation discussion does not eliminate that sensitivity. L01's
unbounded-tail limitations and L04's complete-selection requirement persist.

The safe next transition is independent review of this finite processing component
and reuse of the eight-row coefficient bank for L02's fixed family. Expanding to
the available 300 pairs is a distinct later data-execution decision and does not,
by itself, fill the absent joint split/foreground law or qualify a physical PTE.
No new permanent claim registry row or canonical completion is added here.
