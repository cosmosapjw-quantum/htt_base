# Moving-lens amplitude compression and foreground sensitivity

Owner: `htt`. Claim tier: C0, source-conditioned, `DIAGNOSTIC_ONLY` / `CONDITIONAL`.
This internal research artifact is not acceptance evidence. Scientific admission
remains HOLD pending fresh independent review and the missing physical payload.
Original 42-item acceptance and K03/V03 states are unchanged.

## Result and interpretation

The independently fitted amplitudes in Tables 1–2 of
[Hotinli et al., arXiv:2605.18938v1](https://arxiv.org/html/2605.18938v1)
cannot be represented by one shared scalar linear filter, even allowing all
three participating centers to have been rounded to the nearest hundredth.
This falsifies that downstream scalar-compression shortcut, not the paper's
independent fits or its moving-lens interpretation.

The fixed ACT150 minus Planck545-to150 contrast has the conditional Gaussian
interval [0.240680990786, 1.899319009214]. Outward nearest-hundredth rounding
and the source's alternative 0.00-centered CIB summary enlarge the envelope to
[0.198266963510, 1.931733036490]. No ACT–CIB independence is assumed.
These are intervals for the source's difference of scalar fitted amplitudes.
They do not establish a calibrated common-filter physical signal.

Without an observed bound on the total filter/SED/other error, the physical
moving-lens amplitude M has identified set `UNBOUNDED`. The sensitivity plot
shows hypothetical calibration requirements; it does not measure a foreground
bound, supply a prior, or privilege Δ=0.

## Source intake and exact identity

The original HTML and PDF are stored outside Git under
`/mnt/extdrive/workdir/htt_open_data/moving_lens_20261018/`.
`ACQUISITION.json` records source URLs, UTC acquisition times, final URLs, byte
sizes, content types, and SHA-256 identities. The HTML has 683517 bytes, hash
`de9b8aabb3f7a4f8f57a37987710bb58712486c3ce23f4f5f498025855af0331`;
the PDF has 2535422 bytes, hash
`4e333fff8b7e2e25b0ebeb4aacf1dd5280026f774b2b2c61820da4cf4b4cf0da`.
No upstream code was executed. No map, bandpower vector, or covariance was
downloaded or reconstructed from a plot. PDF text extraction independently
confirmed the target amplitudes, differences, mask, and bin width; generation
uses the exact HTML table cells and MathML `alttext`.

Base checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`;
branch `research/htt-open-input-theory-20261018`;
HEAD `ad27f4cb5f84dfaccc322e53f2810ad29dc72276`;
origin `https://github.com/cosmosapjw-quantum/htt_base.git`.
An unrelated untracked SH0ES directory was present at intake and preserved.
Only this moving-lens directory and its external raw-source directory are owned
by this implementation. Requested executor: `gpt-6.1-sol/high`; observed model
and reasoning effort: UNKNOWN / `NOT_INDEPENDENTLY_OBSERVED`.

The nonradial observational input is ACT DR6 CMB temperature correlated with a
transverse velocity template derived from DESI Legacy Surveys DR9 LRG density.
The moving-lens mechanism couples transverse peculiar motion and gravitational
potential gradients. The source's b_ML is dimensionless relative to its fiducial
halo-model/template normalization. It is neither a speed in km/s nor β=v/c,
and it does not determine global matter tilt, vorticity ω, or an anisotropy A.
Local peculiar motion and Bianchi background geometry remain distinct.

## Exact extracted rows and compression falsifier

`SOURCE_EXTRACTION.json` retains source row IDs, column numbers, table headers,
and selected contextual paragraphs. Tables 1–2 use the extended NGC+SGC sample
and six logarithmic bins over 2500≤ell≤6000 with the main GAL070 analysis mask.
The individual-frequency rows use column 7; difference-map rows use column 8.
They must not be mixed with the VI.1 GAL060 foreground-analysis amplitudes.

| Channel | Table 1 individual amplitude | Row |
|---|---:|---|
| 90 GHz | 0.93 ± 0.36 | S5.T1.2.8 |
| 150 GHz | 1.14 ± 0.32 | S5.T1.2.12 |
| 220 GHz | 3.08 ± 1.29 | S5.T1.2.16 |

| Contrast | Individual scalar subtraction | Published difference-map fit | Residual | Table 2 row |
|---|---:|---:|---:|---|
| 150−90 | 0.21 | 0.12 ± 0.39 | −0.09 | S5.T2.2.22 |
| 220−90 | 2.15 | 2.17 ± 1.30 | +0.02 | S5.T2.2.26 |
| 220−150 | 1.94 | 2.02 ± 1.26 | +0.08 | S5.T2.2.30 |

For a fixed linear functional L with common template normalization,
L(d_high−d_low)=L(d_high)−L(d_low). Three independent nearest-.01 center
roundings can change this identity's residual by at most 3×.005=.015.
Every observed absolute residual exceeds .015. This is a deterministic
counterexample to the common scalar-filter representation, not a statistical
test using the quoted measurement errors.

Eqs.24–25 specify a Gaussian bandpower likelihood and its fitted amplitude
b_hat=tᵀC⁻¹d/(tᵀC⁻¹t), with variance 1/(tᵀC⁻¹t). The resulting linear weights
depend on C and t. Separately fitted maps need not use the same C or effective
weights; common mask and beam do not supply these missing numerical weights.
Nothing in the residual calculation identifies a defect in the source pipeline.

## Fixed 545-to-150 contrast and dependence

VI.1 uses the same GAL060 footprint and 2-degree apodization for the compared
spectra, and six bins of width Δell=500 over 2000≤ell≤5000. This is distinct
from the main logarithmic binning. The selected combined amplitudes are:

| Scalar fit | Center ± quoted uncertainty | Exact HTML source |
|---|---:|---|
| ACT 150 | 1.06 ± 0.27 | S6.SS1.p6.m1 |
| Planck353 CIB scaled to 150 | −0.07 ± 0.14 | S6.SS1.p6.m3 |
| Planck545 CIB scaled to 150 | −0.01 ± 0.10 | S6.SS1.p6.m5 |
| Alternative 545 summary | 0.00 ± 0.10 | S6.SS1.p7.m1 and S7.I1.i1.p1.m3 |

The source CIB scaling assumes high-frequency CIB dominance, a modified
blackbody SED with β_d=1.7 and T_d=10.7 K in thermodynamic CMB temperature
units, and beam transfer correction. Source SED ratios to 150 GHz are .054
(353) and .0037 (545). These are upstream modeling conditions, not independently
calibrated here. The comparison is conditional on this one study's data selection,
mask, reconstruction, surrogate normalization, template, and covariance procedure.
The 353 estimate is context only; it is not pooled as an independent observation.

Define d_hat=1.06−(−.01)=1.07. Under the declared Gaussian marginal working
model, each published center has a two-sided 97.5% interval using
q=Φ⁻¹(.9875)=2.241402727604947. Each marginal interval has failure probability
.025, so their simultaneous failure probability is at most .05 by the union
bound, regardless of their dependence. Subtracting the two intervals gives
I_d=[d_hat−q(.27+.10), d_hat+q(.27+.10)]. No square-root sum of variances,
independent product likelihood, Gaussian joint law, or estimated cross-correlation
is used. The ≥95% coverage statement is conditional on the two Gaussian marginal
calibrations. It is not new empirical coverage validation of the source estimates.

Allow nearest-.01 rounding of both centers (±.005 each) and SDs (up to +.005
each). An outward interval has radius .01+q(.27+.10+.01), giving
[0.208266963510, 1.931733036490]. Applying the same construction to the
0.00±.10 source summary gives [0.198266963510, 1.921733036490]. Their union
envelope is [0.198266963510, 1.931733036490]. The two source versions are
alternative printed representations, not independent data; no additional
probability or significance is obtained by retaining both.

## Physical sensitivity and next useful payload

The physical interpretation requires d=M+e_filter+e_SED+e_other. If future
external calibration justified |e_filter+e_SED+e_other|≤Δ, the conditional
physical envelope would be I_M=I_d+[-Δ,Δ]. No such Δ was measured here.

| Hypothetical Δ (not measured) | Conditional lower M | Conditional upper M |
|---:|---:|---:|
| 0.00 | 0.198267 | 1.931733 |
| 0.10 | 0.098267 | 2.031733 |
| 0.20 | −0.001733 | 2.131733 |
| 0.25 | −0.051733 | 2.181733 |
| 0.50 | −0.301733 | 2.431733 |
| 1.00 | −0.801733 | 2.931733 |

A strictly positive lower envelope would require a justified
Δ<0.198266963510 in these source amplitude units. This is a calibration
requirement, not an inferred bound. Unknown Δ leaves M unbounded; Δ=0 is
only a plotted mathematical scenario.

The minimal payload for an actual common-filter comparison is the six ACT150
and six CIB545-to150 bandpowers for this VI.1 footprint, bin windows, a common
numerical template, ACT weights (or its 6×6 covariance), and CIB covariance
evaluated under ACT weights. Cross-covariance would sharpen a joint analysis,
but this Bonferroni construction does not invent it. Converting a calibrated
moving-lens amplitude into a physical β additionally needs the surrogate
velocity/potential normalization and its uncertainty. No ω or A conversion is
licensed by these scalar summaries.

## Validation, plot provenance, and claim audit

The existing `.venv/bin/python` is required. No installation or environment
replacement occurred. `run_bounded.py` captures generation and nine targeted
tests in raw logs, enforcing a combined 120-second finite-compute limit and
two-thread BLAS/OpenMP caps; no ODE or MCMC is used. Tests check source row
extraction, mask/bin fidelity, Bonferroni α, rounding corners, variant union,
monotone Δ expansion, missing-Δ UNBOUNDED, rejection of independence, and all
three scalar-filter counterexamples. `FIRST_FAILURES.txt` preserves the missing
optional bs4 preflight and first extraction error; neither was hidden or turned
into scientific evidence. Scientific four-axis CAS eligibility is not claimed.

The PNG/PDF are generated from RESULT.json-equivalent in-memory data by
`moving_lens.py`; owner HTT, C0, diagnostic mode, empirical-proxy transfer source,
unknown cross-channel covariance, no new null/coverage calibration. Allowed use:
compression falsification and calibration sensitivity. Forbidden uses: native
solver or family admission, physical speed/global tilt/vorticity estimation,
K03/V03 acceptance, posterior/evidence or MIO truth certification. The right
panel is explicitly hypothetical, including its Δ=0 endpoint. Rendered PNG was
visually inspected for legibility. No manuscript buildability claim is made.

| Claim | Owner | Status | Evidence | Remaining boundary |
|---|---|---|---|---|
| Common scalar-filter shortcut fails | htt | CONDITIONAL | Extracted source rows and rounding falsifier | Fixed source and nearest-.01 rounding |
| Contrast interval uses no independence | htt | CONDITIONAL | Gaussian marginal/union-bound arithmetic and tests | Upstream marginal calibration and study selection |
| Physical M is unresolved | htt | DIAGNOSTIC_ONLY | Missing total error bound | Common-filter payload and calibration required |

Skills used: htt-physics-math-audit, htt-scientific-code-validation,
htt-claim-firewall, htt-claim-provenance-ledger, htt-plot-provenance.
They enforce units/frame separation, narrow falsifiers, explicit provenance and
claim ceilings. No forbidden claim promotion was found. There is no new DAG node,
gate, acceptance item, permanent claim registry entry, or scientific admission.
Fresh independent Astra review is a separate pending decision; implementation
and targeted test success are not self-admission.

Replay repair after independent review: unrelated publication advanced the live
checkout to `b4a93016afb57a5b115bff4dbfa65bc3d56d4b65`. The first observed
test failure is retained in `REPLAY_FIRST_FAILURE.log`; it was a provenance/replay
defect, not a numerical discrepancy. `CANDIDATE_INITIAL.json` and
`moving_lens_INITIAL.py.txt` preserve the initial seal and implementation.
The repaired result builder retains the historical campaign base identity and
does not reject unrelated later HEADs. Replay checks the reviewed code and
acquisition hashes in `CANDIDATE.json`; original HTML/PDF byte verification is
still enforced. The execution receipt records the current HEAD separately.
The repair ran only eleven targeted tests, including a mocked advanced-HEAD
regression and full dictionary equality with the unchanged original RESULT.json.
Source extraction, plots, acquisition receipts, generation and test logs, and
VALIDATION.json are retained byte-for-byte; no generation or scientific
calculation campaign was rerun for this repair. A requested-runtime metadata
erratum corrects RESULT.json `/runtime/requested_model` and the generator's
matching field from `gpt-6-sol` to the dispatched `gpt-6.1-sol`; requested effort
stays `high` and observed identity stays UNKNOWN. `RESULT_INITIAL.json` preserves
the initial exact bytes. Every other result field, including all numbers and
scientific claims, is unchanged; the initial logs remain historical records.

Run narrow tests from the repository root (safe after unrelated commits):

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/MOVING_LENS_20261018/test_moving_lens.py
```

For a future explicitly authorized regeneration from the repository root:

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/MOVING_LENS_20261018/run_bounded.py
```

This regeneration command overwrites current generated outputs and raw logs;
preserve the reviewed candidate before using it. It is not needed for the
narrow repair validation above. `CANDIDATE.json` freezes the review inputs and
raw logs by byte identity, excludes itself, and does not certify correctness.
