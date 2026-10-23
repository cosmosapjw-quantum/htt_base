# Complete HFI metadata intake: source-assessment candidate

Determination: `METADATA_SUPPORTS_NEXT_TARGETED_NUMERIC_READ`.

This determination is limited to the exact B(l) table targets below, whose
numeric validity is unchecked. It does not qualify the original selected-support
response G(R_a-R_b). Owner obsstat, C0/non-claim-bearing, transfer source none;
separate independent Astra source assessment remains required. D04, L03 and all
other scientific-node admission states are unchanged.

## Source and complete permitted scope

Official and final URL:
https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/HFI_RIMO_BEAMS_R3.01.tar.gz.
The parent-owned create-only fetch receipt records DOWNLOADED, 86,556,876 bytes,
local SHA-256
`187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994`,
Last-Modified `Mon, 19 Aug 2019 22:12:13 GMT`, ETag unavailable and upstream
checksum unavailable. Source and receipt remain outside Git at
`/mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz`
and its adjacent `.receipt.json`. The final continuation rehashed these bytes.
See preserved `ASSESSMENT.md` for acquisition evidence and limitations.

`SOURCE_INDEX_DOUBLE_GZIP.json` captures all 452 physical members in ordinal
order: one directory and 451 regular FITS files, containing 1,319 HDUs. All HDU
headers were reached and all array/table payload bytes skipped without numerical
interpretation. No regular non-FITS members, README or other documentation
members were present. Both gzip layers reached EOF with CRC validation; strict
GNU tar checksums were retained. No remaining archive contents are uninspected
within this metadata-only scope. Numeric values remain wholly uninspected.

The first one-layer parser failure and approved diagnostic remain frozen in
`SOURCE_INDEX.json`, `PREFIX_DIAGNOSTIC.json`, `ASSESSMENT.md`, and
`FORMAT_DIAGNOSIS.md`. The amendment is a separate explicit two-layer wrapper;
it does not replace the original parser or skip a prefix/checksum.

## Decisive metadata and exact next-read targets

Locations below use the source-index physical member ordinal, zero-based HDU
ordinal, and one-based retained card-list position. Literal filenames locate
objects; DET1/DET2 and COMMENT cards establish the limited semantics.
All files in this table are under the literal archive directory
`BeamWf_HFI_R3.01/`.

| Member ordinal | Literal basename | Header binding |
|---|---|---|
| 14 | `Bl_TEB_R3.01_fullsky_100hm1x100hm1.fits` | HDU0 cards8–9: DET1=DET2=`100hm1` |
| 22 | `Bl_TEB_R3.01_fullsky_100hm2x100hm2.fits` | HDU0 cards8–9: DET1=DET2=`100hm2` |
| 15 | `Bl_TEB_R3.01_fullsky_100hm1x100hm2.fits` | HDU0 cards8–9: DET1=`100hm1`, DET2=`100hm2` |
| 130 / 144 | `Bl_T_R3.01_fullsky_100hm1x100hm1.fits` / `Bl_T_R3.01_fullsky_100hm2x100hm2.fits` | HDU0 cards8–9 bind the corresponding literal labels |
| 185 / 195 | `Bl_T_R3.01_fullsky_143hm1x143hm1.fits` / `Bl_T_R3.01_fullsky_143hm2x143hm2.fits` | HDU0 DET1/DET2 bind these labels |
| 226 / 234 | `Bl_T_R3.01_fullsky_217hm1x217hm1.fits` / `Bl_T_R3.01_fullsky_217hm2x217hm2.fits` | HDU0 DET1/DET2 bind these labels |

The immediate metadata-supported targets are members 14 and 22, HDU1
`WINDOW FUNCTIONS`, columns `T`, `E`, `B`. Both HDU1s start at member byte offset
2,880. Their cards1–22 specify ASCII TABLE, BITPIX=8, NAXIS1=45, NAXIS2=4001,
PCOUNT=0, GCOUNT=1, TFIELDS=3; TTYPE1/2/3 are T/E/B, each TFORM=`E15.7`,
TBCOL=1/16/31; MAX-LPOL=4000, POLAR=T, BCROSS=F, ASYMCL=F. No TUNIT is present.

For each of these two files, HDU0 cards11–16 and repeated HDU1 cards24–29 state:

```text
Beam Window Functions B(l), for T, E and B
Compatible with Healpix (synfast, smoothing, ...) and PolSpice
To be squared before applying to power spectrum
C_TT_map(l) = C_TT_sky(l) * B_T(l)^2
C_EE_map(l) = C_EE_sky(l) * B_E(l)^2
C_BB_map(l) = C_BB_sky(l) * B_B(l)^2
```

Thus B(l) semantics come from the headers themselves. They were not manufactured
by square-rooting W(l). These comments and the explicit literal detector labels
support a next targeted numeric read of those exact table columns, retaining
all row ordinals. They do not yet establish a general harmonic map response,
the normalization, row origin, or the association to the exact processed maps.
Although 4,001 rows and MAX-LPOL=4000 are consistent with l=0…4000, no explicit
LMIN, ell column or row-origin convention appears. Do not silently identify a
row with a multipole or execute the selected-support calculation before that
mapping is qualified under a separate contract.

The T-only counterparts use HDU1 `WINDOW FUNCTION`, ASCII TABLE, NAXIS1=15,
NAXIS2=4001, column `TEMPERATURE`, TFORM=`E15.7`, TBCOL=1, MAX-LPOL=4000,
POLAR=F, BCROSS=F, ASYMCL=F. Member130 HDU0 cards11–14 and HDU1 cards18–21
explicitly call B(l) a beam window function to be squared for C_map=C_sky B(l)^2.

## Spectrum mixing, label scope, and unresolved response fields

The complete index comprises 116 three-column B_T/E/B products, 196 T-only
products and 139 W(l) products. These counts are index summaries supported by
their HDUs and header comments, rather than filename-only science conclusions.

For W(l), member314
`Wl_R3.01_fullsky_100evenx100even.fits` HDU0 cards14–17 says W(l)=B(l)^2,
applies directly to power spectrum, C_map(l)=C_sky(l) W(l), includes cross-talk.
HDU0 XTNAME1–4 identify `TT`, `EE`, `BB`, `TE` extensions. Each extension is a
BINTABLE with NAXIS1=144036, NAXIS2=1, nine fields of TFORM=`4001E`,
MAX-LPOL=4000, POLAR=T, BCROSS=T, ASYMCL=T. In the TT HDU, columns are
`TT_2_TT`, `TT_2_EE`, `TT_2_BB`, `TT_2_TE`, `TT_2_TB`, `TT_2_EB`,
`TT_2_ET`, `TT_2_BT`, `TT_2_BE`; EE/BB/TE HDUs use the analogous first token.
These names and the power-spectrum COMMENT convention identify spectrum
cross-talk metadata. They do not specify an lm-to-l'm' map-response matrix.
The direction/order of every cross-field mixing convention is not further
explained by documentation in this archive.

Same-label `100hm1` / `100hm2` W(l) products occur at members322/332
(`fullsky`) and411/417 (`plikmask`); the latter has the same explicit spectral
COMMENT convention and table schema. The words fullsky/plikmask locate distinct
products; no mask bytes, spatial dependence or pixel-window prescription is
supplied by these headers. They cannot substitute for the selected-support map
operator or its mask response.

Across all headers DET1/DET2 explicitly contain labels at 100,143,217,353,545,
857 and bare, hm1/hm2, even/odd forms, plus 353p/353phm variants. The headers
describe DET1/DET2 only as Detector(set). They do not explicitly define hm as
half mission, identify even/odd with the required oe1/oe2 maps, bind a literal
label to an exact map release/processing state, or define bare labels as the
full-mission response. The bare `100` products, e.g. members40/168, remain
separate from the split-labelled products. No full-mission-to-split replacement
has been made.

Complete header inspection found only the structural/table keywords plus DATE,
DET1/DET2, EXTNAME/XTNAME, MAX-LPOL, POLAR, BCROSS, ASYMCL and COMMENT. There
are no TUNIT cards and no metadata specifying uncertainty modes, uncertainty
normalization, eigenvalues, covariance, split-channel correlations, confidence
meaning, pixel-window inclusion, calibration/LFI renormalization, SMICA weights,
or spatial/scan dependence. The COMMENT text contains no such conventions.
No full lm-to-l'm' response, selected-support response, or uncertainty law has
been supplied by the completed metadata inspection. This is the exact remaining
source insufficiency for the original G(R_a-R_b), even though a narrower next
table read is now identifiable.

The source URL/directory/member labels say R3.01. The headers have no independent
release/version keyword; DATE values run from 2016-06-15 to 2017-04-27 and
COMMENT provenance points to RD12rc3 generating NPZ paths and qp2fits.py.
These are creation/generation provenance, not a new R3.01 release declaration.
No release conflict has been resolved by fiat; compatibility of those generating
inputs with the exact downstream map product is unqualified.

## Bounds, execution, and verification

The prior first run and diagnostic were carried into the same limits:

| Quantity | Observed |
|---|---:|
| Prior decoded bytes | 1,536 |
| Continuation outer-layer decoded bytes | 86,555,314 |
| Continuation inner tar decoded bytes, including skips/padding/trailers | 120,350,720 |
| Cumulative decoded bytes, both layers and replay | 206,907,570 / 1,073,741,824 |
| New retained decoded metadata | 5,448,488 bytes |
| Conservatively charged prior metadata envelopes | 20,951 bytes |
| Maximum individual FITS header | 5,760 bytes / 1,048,576 |
| Physical members | 452 / 4,096 |
| Prior conservative wall charge | 1.563056 s |
| Continuation internal elapsed | 2.3666555769741535 s |
| Cumulative recorded wall charge | 3.9297137910034508 s / 120 |
| Peak RSS high-water value | 419,600 KiB |
| Address-space cap | 536,870,912 bytes |
| Observed process threads | 2 |

Canonical interpreter `.venv/bin/python`, Astropy8.0.2, execution HEAD
`db8ce0b88af7c4e4cac35e87a4871694d9b7a9c0`, requested executor
gpt-6.1-sol/high, observed runtime UNKNOWN. No extraction, link following,
upstream execution, numerical column interpretation, map/SHT/beam/noise
calculation or extra acquisition occurred.

Synthetic controls command, exit0:

```text
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m pytest -q -o addopts= docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/test_inspect_source.py docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/test_double_gzip.py
............                                                             [100%]
12 passed in 2.34s
```

Controls include valid double gzip, corrupt inner and outer trailers, invalid
tar checksum, third-layer rejection, and cumulative both-layer cap including
prior charges, plus the six preserved parser/control fixtures. They are not
scientific campaign executions.

Single authorized source continuation, exit0:

```text
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/inspect_double_gzip.py
coverage: COMPLETE_PERMITTED_METADATA_INSPECTION
obstruction: null
members: 452
```

Full raw structured outcome and command/resources are preserved in
`SOURCE_INDEX_DOUBLE_GZIP.json`. Source-content and mechanical parser execution
are not scientific admission. The next decision is fresh independent Astra
review of this frozen candidate and a separately contracted next numeric read,
with the row/map/convention limitations preserved.
