# L01: a finite bridge between the original L128 and matched raw estimators

Owner: `obsstat`. Date: 2026-10-18 UTC. Scope: non-claim-bearing, solver-free
postprocessing of committed real-data summary norms. Status: `DIAGNOSTIC_ONLY`,
claim tier `C0`, transfer source `none`. The raw maps and native report arrays were
not available here. No native Bianchi solver or ODE was run.

The new result is a conditional bound between two estimates that had not yet
been directly compared: the original native-grid L128 reconstruction contrast
and the source-window-matched raw-data contrast. Existing results supply each
estimate's distance to the same original direct native contrast. They do not
supply the missing dot product between these two estimates. We bound that dot
product by positive semidefiniteness rather than inventing it.

| Coefficient space | Matched vs original L128 angle | Distance [nK_CMB] | Best nonnegative scalar-fit residual / matched norm |
|---|---:|---:|---:|
| All, using E/B block constraints | 55.6426°–73.7213° | 67.6506–75.9718 | at least 82.5533% |
| E | 60.4936°–77.2188° | 46.8505–52.3876 | at least 87.0301% |
| B | 50.7229°–70.3524° | 48.8020–55.0205 | at least 77.4093% |

Thus even an optimally chosen single nonnegative amplitude applied to the
original native L128 estimate cannot closely reproduce the matched raw estimate
under these summary constraints. This is coefficient-space processing geometry,
not a sky rotation, noise fraction, cosmic B measurement, or significance.
The old native L128 residual cannot be relabelled as a matched-estimator error.
That does not establish whether the matched estimator itself is accurate.

## Reused evidence and exact source identities

All source reads were pinned to repository `cosmosapjw-quantum/htt_base`, commit
`967ef7c8f0b132ecaaba343045d333d4ebf299c1` (PR #559 branch). Below, `P` is
`docs/research_program/observational_publication_20261015`.

| Source | Git blob | Use |
|---|---|---|
| `P/L01_SMICA_QU_BAND_ACCOUNTING_20261017/MATCHED_SPLIT_STREAM_PROGRESS_20261018.json` | `bca4231760c9b19faef9d0da9bb445288faea3ce` | Actual user-executed matched full fit norms and change norms |
| `P/L01_SMICA_QU_BAND_ACCOUNTING_20261017/NATIVE_RESIDUAL_VISIBILITY_PROGRESS.json` | `17d67c6466ab78df998a8eb9e37ae8c58c4726f4` | Actual user-executed native direct, L128 reconstruction, and residual norms |
| `P/L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_matched_window_refit.py` | `845c4034bd5dacd684a3d83de29bde5179514dc9` | Original/matched contrasts use inner minus common; original fits replay archived raw RHS column 0 |
| `P/L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_native_residual_projection.py` | `14621d017c2c221701699873cece8659cbdd5b21` | Raw/reconstructed/residual contrast uses the same inner-minus-common convention |
| `P/L01_SMICA_QU_BAND_ACCOUNTING_20261017/MATCHED_SPLIT_STREAM_KO.md` | `f010d44cf5eb1382ec6bdaa33004646cd365cc81` | Native input paths and next matched split run |
| `P/L01_R8_C8_TWO_MASK_STABILITY_20261017/src/l01_matched_split_stream.py` | `b15421111bcc9ded93cd7b8a4af225f1fd405ee0` | Existing five-product source/support/replay contracts |

The first two files are retained byte-exact under `inputs/`; their Git blobs are
checked on each run. Extra copied progress snapshots in `inputs/` are background
evidence and are not numerical inputs to this calculation. This analysis trusts
the recorded workflow identity linking the native report to the matched refit;
matching scalar norms alone would not prove common vector identity. The original
native report path is
`/mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json`.

The latest full matched output was
`/mnt/extdrive/workdir/htt_open_data/provenance/L01_MATCHED_RAW_WINDOW_FIT_20261017T220911Z.json`.
Its values were supplied by the user and committed, not independently recomputed
from Planck maps in this worker. The matched five-product scan remains unexecuted
in the supplied evidence. Earlier L32 pseudo-spectrum ratios are different
statistics and are not used as matched-fit noise ratios.

## Definition, derivation, and constructive witnesses

Let `a` be the original direct native contrast, `u` the matched raw contrast, and
`v` the original native L128 reconstruction contrast. All belong to the same
fixed real ell2..5 coefficient convention. There are 64 coefficients, with
orthogonal 32-dimensional E and B blocks. Write their lengths as `A,B,C` and the
known distances as `p=||a-u||`, `q=||a-v||`. Then

```
cu = (A²+B²-p²)/(2AB),  cv = (A²+C²-q²)/(2AC)
u/B = cu*a/A + sqrt(1-cu²)*eu
v/C = cv*a/A + sqrt(1-cv²)*ev
```

Here `eu,ev` are unit vectors orthogonal to `a`, so their dot product `t` lies
between -1 and 1. Hence

```
cos(u,v) = cu*cv + sqrt(1-cu²)*sqrt(1-cv²)*t.
```

Every `t` in that interval has an explicit realization in dimension at least 3.
The endpoints use parallel or antiparallel perpendicular components. This proves
sharpness conditional on the supplied lengths and vector convention, without
statistical assumptions. Endpoint distances are calculated as sums of squared
parallel and perpendicular differences to avoid cancellation in a difference of
large squared lengths.

For a fixed cosine `c`, minimizing over scalar amplitudes gives

```
min_{alpha>=0} ||u-alpha*v|| / ||u|| = sqrt(1-max(c,0)²).
```

Using the largest feasible cosine gives the lower residual in the table. E and B
endpoint orientations can be chosen independently in their orthogonal blocks,
so the total squared-distance endpoints add. This tightens the all-only interval
from 55.4927°–73.8627° to 55.6426°–73.7213°. Additivity of all five supplied lengths
was verified to relative squared-length discrepancy at most `4.45e-16`.

No upper bound on an infinite harmonic tail is inferred. The direct input to the
matched fit is not first truncated to ell<=5; ell2..5 labels the fitted basis.
This comparison also does not replace the original estimator or alter archived
results. The measured estimator-change / old L128-residual ratios are 5.62464
(all), 6.25373 (E), and 5.18378 (B); these are descriptive ratios across the stated
finite operations, not a causal allocation of error.

## Implementation and actual validation

The implementation uses only Python's standard library for analysis and tests.
Run from this directory:

```bash
python -m unittest discover -s tests -v
python analyze_planck_anchor.py
python plot_planck_anchor.py
```

Actual runtime: `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python`,
Python 3.12.14; optional plot dependency Matplotlib 3.10.8. Eight tests passed,
including 500 independently sampled direct-vector comparisons, rational endpoint
witnesses, orthogonal-block simultaneous endpoint witnesses, analytic optimal
scalar projection, uniform rescaling through 1e-200 and 1e200, collinear and
orthogonal limits, and malformed/PSD-inconsistent inputs. Test execution took
0.008 s. The generator executed on the byte-pinned real summaries and produced
`results/PLANCK_ANCHOR_GEOMETRY_20261018.json`. PNG/SVG were rendered and inspected.
No pytest installation was added; the first environment probe found it absent.

The kernel rejects nonfinite/negative lengths, zero vector norms, impossible
triangles, and unresolved normalized dynamic range. Small cosine endpoint
roundoff is clipped within a declared floating tolerance. These are not formal
outward-rounded intervals; printed digits describe numerical evaluations of the
exact conditional formulas. No whole-repository test or native FITS scan ran.

This was an actually dispatched native worker. Requested model/effort inherited
the parent invocation; observed model and effort are `UNKNOWN`. A separate review
is the parent's integration responsibility. Primary checkout state is `UNKNOWN`.
Desktop Commander was not retried; no clone, worktree, or full repository copy was
created. Writes are confined to this bounded worker package.

## Scientific validity, risks, and next experiment

Safe claim: the two named finite coefficient estimates cannot be related by a
small positive scalar recalibration under the pinned summaries. Its evidence is
a derivation, synthetic independent-vector tests, and arithmetic on committed
real-data summaries. This does not identify the physical source of either vector.
Invalidate the numerical conclusion if the shared anchor, coefficient ordering,
sign, support, or source report linkage changes. Do not use intervals as p-values.

The exact next native experiment is the existing matched full/HM/OE stream. The
run helper `run_native_matched_splits.sh` uses the primary checkout and creates
only a new native output JSON. It performs no Git switch/fetch, installation,
download, old-output overwrite, SHT, or Gram recomputation. The primary checkout
must first contain the already-tested #559 source and its predecessor modules.
The existing helper's archive/source version checks remain intact. This fresh
diagnostic does not require any new solver dependency.

The original checkout guard (blob `ed1c466522cac5537b958fa07137c2685b2407f5`)
hard-coded the #559 remote branch even when another `--expected-ref` was supplied.
The parent authorized a narrow correction, included separately under `patches/`:
an explicit authorized `origin/<branch>` is accepted while preserving exact HEAD,
clean-tree, top-level, required-file, import-smoke and Git trust checks. The old
default stays compatible. Historical fresh-worktree recovery advice is replaced
with preservation of the existing primary checkout. The shell helper requires
this correction to be integrated and takes the selected remote ref explicitly:

```bash
bash run_native_matched_splits.sh origin/research/OWNER_SELECTED_CONTINUATION_BRANCH
```

The primary branch/ref state is currently unknown, so this remains a runnable
handoff after that state is safely prepared, not a native execution receipt.
Preparing the existing primary branch safely is the parent's next environment
action when terminal access returns. No gate is bypassed by this package.

Required local inputs under `/mnt/extdrive/workdir/htt_open_data`:

- `provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json`
- `provenance/L01_LOW_SOURCE_WINDOW_RESPONSE_20261017T150345Z.json`
- `provenance/L01_NATIVE_PR3_POL_K64x90_v2.json`, plus the source manifest and NPZ
  objects referenced by that existing receipt (the receipt validator resolves and
  checks those links; none are fabricated here).
- `planck/PR3/cmb/COM_CMB_IQU-smica_2048_R3.00_{full,hm1,hm2,oe1,oe2}.fits`
- `planck/PR3/masks/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits`
- `planck/PR3/masks/COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits`
- `planck/PR3/masks/COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits`
- The same compatible Python, NumPy/SciPy/healpy runtime and versioned source
  dependencies pinned in the saved native checkpoint contract.

Additional receipt-internal paths cannot be enumerated here because those native
JSON files are external and unavailable; their resolving validators remain the
authority. This is not a claim that their bytes or availability were checked.

First inspect full-column replay and support counts: common 37,120,921, inner
36,951,769, removed shell 169,152. The full matched contrast must reproduce the
archived vector before any new split statistic is accepted. Then inspect HM/OE
half differences and full-minus-split means under the same estimator. For noise,
the half-difference covariance is `T(N11+N22-N12-N21)T^T/4`; neither `N12=0` nor
an independent-sky sample count follows from the five products.

Canonical recommendation: keep `L01` pending and all six papers
`NOT_READY_TO_SUBMIT`; 14/42 completed scoped nodes remains unchanged. This packet
adds a concrete estimator-comparison capability and numerical result, not a new
gate, registry, stage completion, or manuscript-readiness claim.
