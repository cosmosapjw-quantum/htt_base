# HTT 후속 관측 코딩 연구 루프: C1–C10, Planck multi-split/SH0ES full-C

실행일 2026-10-15 KST. 활성 owner checkout:
  /home/cosmosapjw/Dropbox/bianchi/htt_base
  branch obs/solver-free-dossier-20261014
  HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54
기존 미커밋 연구 31개 항목과 원본 raw 자료는 보존.
새 파일만 추가하는 방식, commit/push 미실행.

## C1: 실제 물리 계약과 성공/실패 정의

핵심 목표는 실제 하나의 Planck 하늘을 여러
같은-sky processing에서 비교하고, exact Q/O
morphology 및 finite polarized E/B response와
기존 Boost 이론을 연결하는 것이다.
통계적 귀무분포/물리 likelihood가 없는 항목에
유의성을 부여하면 FAIL.
SH0ES 자료는 공식 단일 joint covariance의
3492x47 GLS가 실제로 실행되고 normal-equation
residual과 공개 reference 차이를 기록하면
범위 한정 성공이다.
SH0ES와 CF4의 원천/host mapping을 구성하지
않았는데 cross-survey independent prior를 넣으면 FAIL.

## C2: 데이터–코드–물리 단위 대응

Planck public 2018 PR3:
  SMICA_HM1/HM2, SMICA_OE1/OE2,
  NILC_HM1/HM2, SMICA_FULL,
  SMICA_noSZ_FULL (I-only), NILC_FULL.
파일들은 K_CMB, NSIDE2048, NESTED Galactic,
외장하드 원본 FITS와 공식 HM/OE/common
Int/Pol mask를 사용한다.
  common T selected nside64 pixels: 26846
  common polarization selected pixels: 30021.
Native K->microK explicit factor 1e6.
Temperatures apply single simultaneously fitted
real l0..5, retain l2..5 32 real modes.
QU use l2..5 joint spin2 E/B real image 64 modes,
not two unrelated scalar Q,U harmonic expansions.
Missing-pixel supports downweighted by positive
fine-pixel fraction and 0.995 coverage threshold.
Neither temperature mask nor polarization mask
is swapped silently.

SH0ES pinned official commit:
  /mnt/extdrive/workdir/raw/shoes2022_calibration_reference_20261015/
  C: (3492,3492), L: (47,3492), y: (3492).
Source README states slope baseline -3.285.
lstsq_results.txt is an external released parameter
center/width list (not guaranteed exactly same GLS
without verifying the original fitting contract).

## C3–C4: 구현과 이산오차 구조

Planck I/QU native HEALPix FITS files are memmapped
and visited in chunks. One common fine-mask
is applied to each component across all maps;
the downsampling mean ignores truly missing/sentinel
pixels. No floating-point smoothing or new beam
model is invented. Fixed common 32D temperature
fit operator has design condition=3.60138 and
identity residual 3.997e-15. Fixed physical
spin2 design 64D has condition=3.13096 and
identity residual 2.442e-15.
A missing high-l sky causes finite low-l alias;
it is not automatically regularized or called
exact E/B sky extraction.

SH0ES dense full C is symmetrically whitened by
lower-triangular Cholesky. A.T C^-1 A is solved by
a second Cholesky, no full C inverse formed.
This is exact GLS for declared C and L,
not a solver for Einstein/Bianchi source parameters.
Reference q and q-error differences are retained.

## C5: 실제 작성한 코드와 연구 산출물

New core modules:
  htt/obsstat/htt_multisplit_lowell.py
  htt/obsstat/htt_shoes_matrix_bridge.py

New executables:
  scripts/run_htt_planck_multisplit_spin_20261015.py
  scripts/run_htt_polarization_EB_diagnostics_20261015.py
  scripts/run_htt_multisplit_boost_morphology_20261015.py
  scripts/run_htt_shoes_exact_gls_20261015.py

New tests:
  tests/obsstat/test_htt_multisplit_lowell.py
  tests/obsstat/test_htt_shoes_matrix_bridge.py

Real execution outputs, all create-only:
  results/planck_multisplit_spin_v1/
  results/planck_spinEB_modes_v1/
  results/planck_morphology_boost_comparison_v1/
  results/shoes_full_covariance_gls_v1/

## C6: 단위·회귀 검증

Synthetic Planck four-split common-sky cancellation,
inverse transform and per-ell cross=mean²-difference²
identities. Masked finite-pixel spin2 injection
recovers arbitrary E/B l2..4 real coefficients
through a common Q/U masked joint operator.
A physically invalid scalar-Q/U/Ylm approximation
is not used.

SH0ES GLS matches independent dense Gaussian
injection on small synthetic covariance matrices,
is invariant under invertible changes of the
parameter basis, and the same-source column
has vanishing projected information.
The source-matched joint SH0ES/CF4 shared-anchor
covariance identity was tested including
non-independent shared systematic and separate
orthogonal anchor cases. Unknown source loading
is refused by code, not silently fabricated.

## C7: 과학 검증 및 data identity

Actual Planck same common mask T and polarization
counts and OLS identities are numerically checked
before claiming any contrasts. The source product
manifest is
  /mnt/extdrive/workdir/raw/HTT_ADDITIONAL_DATA_INTAKE_20261015.json
with 17/17 verified new public products. Existing
SMICA HM products and old common mask are explicit
input dependencies. The nominal historical SMICA HM
baseline used different mask support; it must
not be subtracted from the new common-mask result
as if operator identities were equal.

HTT source q/o tensors are converted with the
unchanged STF projection registry, unit carrying
microK and the same Galactic spin frame.
Beta reference in the fixed physical_dipole_v2
source is dimensionless. The ideal Q->O comparison
is NOT Planck-native Bianchi transfer.

SH0ES official full-ladder source 47-coordinate
GLS result differs nontrivially from the
lstsq_results.txt reference by max 0.0496177
coordinate units, with reference χ² higher
by 6.819643. This discrepancy is preserved
as observable source-code-model correspondence
rather than forced by widening tolerances.

## C8: 성능·불확실성·재현성

The 9-temperature/8-polarization native FITS
source processing and fixed mask projection
took about 170.31 seconds locally.
Observed maximum process RSS about 3418 MiB.
The SH0ES 3492x3492 full GLS with two-thread
BLAS executed in about 4.74 seconds; full
joint covariance was not inverted explicitly.
Outputs have deterministic fixed-source
real-harmonic ordering and exact release
source hashes or stored source-id contracts.

**Important:** The stochastic uncertainty in
split source coefficients is not estimated from
a single sky by declaring three different
processing pipelines independent.
The split-source sensitivities are numeric
observables, not confidence intervals.

## C9: risk-focused independent scope audit

- Common T and QU native fine masks use separate
  TMASK/PMASK fields; noSZ release has two I
  channels but no polarized Q/U and was
  explicitly excluded from spin2 fitted inputs.
- Common-support finite image makes actual
  splitting/method comparisons algebraically
  meaningful. Different frequency/beam/compsep
  responses still can alter the same sky signal.
- Low-l B and EB are not guaranteed true
  physical primordial B or parity invariants
  under cut-sky high-l unmodeled leakage.
- The SH0ES high-level covariance covers a
  single distance-ladder experiment with shared
  source anchors; it is not a prior on CF4
  zero-points until the shared host catalogue
  loading is independently identified.
- No source cosmology or global tilt estimator
  was manufactured to make these diagnostics
  look like detections.
- There is no exposed native subagent dispatch
  in the current host; no fresh second-model
  adjudication receipt. Record native_subagent=NOT_RUN.

## C10: 실행·재개·배포 계약

Retained:
  THEORY_LOOP_KO.md
  CODING_LOOP_KO.md
  scientific JSON+PNG+NPZ source-bound products
  BLOCKER_DELTA.json
  MANIFEST.json, NEXT_RESEARCH_DAG.json,
  source-byte hashes, test evidence.

Next scientifically positive action:
  (a) cross-validated physical full-sky Planck
      source beam/compsep and split covariance,
      including high-l and spin2 transfer, then
      pass Bianchi/boost physical templates through
      that operator;
  (b) join SH0ES 47 parameters and Cepheid/SNIa
      public host identities to CF4 method/event
      source-ID and conditional selection law,
      with the actual cross-anchor covariance;
  (c) if the reference GLS mismatch is relevant,
      reconstruct official published least-squares
      weights/priors from the pinned author code.

All old physical blockers in the existing
observational campaign remain unchanged.
No PR/commit/push is asserted.

## New source ID lane after first theory/code output

- htt/obsstat/htt_shoes_cf4_astrometric_join.py:
  J2000 spherical host centroid and nearest CF4 Cepheid
  catalogue galaxy position; rejects ambiguous ties.
- scripts/run_htt_shoes_cf4_candidate_hosts_20261015.py:
  SH0ES table2.tex exact-byte identity (SH0ES pinned
  source manifest) and CF4 Table2 exact-byte identity,
  actual host/galaxy position candidates, 4 arcmin
  fixed spatial selection.
- tests/obsstat/test_htt_shoes_cf4_astrometric_join.py:
  four bounded synthetic source-coordinate tests, including
  RA wrapping, ambiguous pairs and fail-closed contracts.
- Executed actual source map:
  results/shoes_cf4_astrometry_candidates_v1/{result.json,REPORT_KO.md}.

Outcome: 41 SH0ES WFC3 Cepheid field names vs
69 CF4 Cepheid-distance galaxies, 37 positional
candidates, four unmatched anchors/hosts, zero close
competing candidates, and source grouping collision:
  N3972 / N3982 -> CF4 1PGC 37642.

DO NOT turn these positional candidates into
SH0ES/CF4 shared anchor covariance yet: official
host labels and calibration correlations have not
been matched end-to-end. Next actual source step:
retrieve/certify cross-ID host/event tables and
verify the corresponding 47-column SH0ES parameter
identities, then construct the correctly joined
sample space and covariance.
