# HTT v6: claim을 축소하지 않고 출판 가능성으로 끌어올리는 강화 전략

## 한 문장 전략

HTT v6의 주장을 “우주론적 검출”로 억지 승격하는 대신, 더 강하고 더 방어 가능한 논문 주제로 바꾼다. 즉, **FLRW departure에 대한 signed comparator + sharp partial identification + response-rank/null-space theorem + calibrated current-data diagnostic atlas**를 하나의 출판 가능한 방법론/데이터-진단 논문으로 만든다. 이건 tone down이 아니라, 불안정한 수사적 주장을 검증 가능한 수학적·통계적 주장으로 강화하는 방향이다.

## 강화된 중심 claim

현재 원고의 중심 claim은 다음처럼 세워야 한다.

> We introduce a constraint-derived signed FLRW-departure comparator whose data-facing semantics are necessarily set-valued under rank-deficient observable support. For current CMB/velocity/LSS diagnostic products, the framework returns sharp identified intervals, rank/null certificates, prior-exposure labels, and finite-sample calibrated exceedance/e-value summaries rather than geometry labels. This gives a publishable, falsifiable, and reproducible route for comparing FLRW-departure channels before native anisotropic transfer solvers are available.

이 문장은 “검출을 포기한다”가 아니다. 오히려 관측 채널이 실제로 식별하는 대상을 정확히 명명한다. 심사위원이 공격하기 어려운 이유는 명확하다. signed comparator는 constraint identity에서 오고, rank deficiency는 row-space theorem으로 오고, unobserved components는 partial identification으로 오고, coverage/e-value는 별도 calibration gate로 온다.

## 이전 비판을 강화 포인트로 바꾸는 법

### 1. `diagnostic_only`를 약점이 아니라 estimand로 바꿔라

현재 보고서는 posterior/evidence/family assignment/native solver output을 주장하지 않는다고 명시한다. 이걸 감추면 손해다. 대신 논문 초록에서 먼저 선언해라.

강화 문장:

> The paper is not a Bianchi-family detection paper. It is an identifiability-first measurement paper: the estimand is a signed comparator identified set, not a geometry label.

그러면 Planck/Bianchi 문헌과 정면 충돌하지 않고, 오히려 기존 Bianchi template tradition의 사전 geometry assignment와 차별화된다.

필요 산출물:

- `component_source_matrix_current.json`
- `rank_null_certificate_current.json`
- `identified_set_current.json`
- `prior_exposure_report_current.json`
- `diagnostic_only_to_estimand_table.tex`

Acceptance gate:

- 모든 figure가 `estimand`, `observable y`, `response R`, `null/covariance status`, `claim tier`를 sidecar로 갖는다.
- figure caption에 “posterior/evidence/family assignment”가 섞이면 CI fail.

### 2. P31 sharpness를 “추상 cone sharpness”에서 “realizability theorem”으로 올려라

기존 P31의 취약점은 full GR constraint가 admissible set을 더 줄일 수 있다는 점이다. 이걸 회피하지 말고 더 강하게 대응한다.

강화 정리 후보:

> Local constrained-data sharpness theorem. For sufficiently small component vector g in the registered HTT cone satisfying the Hamiltonian and momentum constraints to order k, there exists a local CMC initial-data family whose first-jet invariants realize g up to O(||g||²), with exact realization after conformal-method correction under nondegenerate York operator assumptions.

이 정리는 쉽지 않지만 publication-level로 갈 가치가 있다. 적어도 1차 local jet realization과 numerical conformal-constraint witness를 만들면 “P31 is merely abstract” 공격을 상당히 차단한다.

필요 작업:

- constant-mean-curvature initial data ansatz 작성.
- shear/vorticity/tilt/anisotropic-curvature 성분을 small parameter로 놓고 Hamiltonian/momentum residual을 계산.
- conformal correction 후 residual norm이 `O(eps^2)` 또는 solver tolerance 이하로 가는지 확인.
- endpoints `[x_C^-, x_C^+]` 각각에 대해 realization witness 저장.

Acceptance gate:

- symbolic first-order constraint residual = 0.
- numerical residual norm `< 1e-10` for toy families or convergence slope ≥ 1.8 in eps.
- energy condition branch labels attached.

### 3. P36은 “strict whenever”를 억지 방어하지 말고 더 센 정리로 바꿔라

이건 중요하다. “strict whenever cN,cD ≠ 0”는 반례가 있으니 그대로 defend하면 심사에서 바로 깨진다. 하지만 claim을 약화할 필요는 없다. 다음처럼 바꾸면 오히려 강해진다.

강화 정리 후보:

> Joint feasible-set depth-gap theorem. The joint interval is the exact sharp identified interval. It is always a subset of the marginal quotient interval. Strict inclusion holds except when the argmin/argmax compatibility conditions for numerator and denominator are simultaneously satisfiable on the diagonal feasible set. In generic coefficient directions, equality is a codimension condition.

이 정리는 기존보다 더 출판 가능하다. 왜냐하면 포함관계뿐 아니라 equality condition까지 준다. 동봉 코드의 P36 random phase diagram은 strict narrowing이 generic하게 발생하고, critique equality case도 정확히 재현한다.

필요 산출물:

- theorem statement with necessary/sufficient equality conditions.
- Charnes-Cooper LP 또는 corner enumeration proof for boxes.
- phase diagram: random coefficient strictness rate, equality examples, degenerate cases.
- replacement text for P36.

Acceptance gate:

- equality counterexample unit test included.
- strict example unit test included.
- proof no longer contains universal strictness sentence.

### 4. P35 coverage는 “known covariance theorem”과 “estimated covariance theorem”으로 분리해라

Gaussian known covariance에서는 two-stage residual/reachable construction이 정리로 깔끔하다. 하지만 실제 K1/K5는 simulation-estimated covariance가 들어간다. 그러므로 theorem을 둘로 나눠야 한다.

강화 정리 후보:

> P35a. Known-covariance two-stage partial-identification coverage.
>
> P35b. Estimated-covariance robust coverage under Wishart covariance, with either Hartlap-corrected precision or Sellentin-Heavens t-likelihood; endpoint calibration is performed conditionally on covariance uncertainty.

필요 작업:

- known covariance Monte Carlo를 유지.
- estimated covariance Monte Carlo를 추가.
- Hartlap-only, Sellentin-Heavens, Gaussian plug-in을 비교.
- dimension p와 Nsim sweep을 figure로 제시.

Acceptance gate:

- Gaussian plug-in undercoverage or precision inflation explicitly shown.
- corrected/t-likelihood lane reaches nominal coverage within MC SE.
- every K1/K5 statistic sidecar records `Nsim`, `p`, correction policy.

### 5. K1은 Planck low-ell “anomaly detection”이 아니라 calibrated scalar/BiPoSH comparator lane으로 닫아라

Planck 2018 isotropy/statistics 결과는 large-angle anomalies를 확인하면서도 unambiguous cosmological detection을 주장하지 않는다. 그러므로 HTT가 살아남는 길은 “우리가 Planck보다 센 검출을 했다”가 아니라, “우리는 diagonal scalar와 off-diagonal covariance/BiPoSH를 분리하고, rank-null semantics로 signed comparator identified set을 만든다”이다.

필요 작업:

- Planck PR4/NPIPE maps and available simulations 또는 PR3 FFP/E2E simulations로 null ensemble 구성.
- SMICA/Commander/SEVEM/NILC map stability table.
- low-ell mask sensitivity, Doppler/foreground/systematic cuts.
- scalar channel vs BiPoSH covariance channel의 joint but not conflated report.
- Hartlap/Sellentin-Heavens correction.

Acceptance gate:

- map-product leave-one-out stability.
- null p/e-value calibration reproducible.
- scalar-only conclusion과 BiPoSH conclusion이 같은 문장 안에서 섞이지 않음.

### 6. K5/CF4는 “bulk-flow evidence”가 아니라 hierarchical selection-corrected depth-flow interval로 닫아라

CF4는 거대하고 유용하지만, distance-method mixture, grouping, Malmquist/selection, sky anisotropy, correlated velocity field가 핵심이다. 그러므로 단순 shell plot이나 bootstrap band만으로 물리 claim을 내면 약하다. 강화하려면 forward model을 닫아야 한다.

필요 작업:

- CF4 grouped catalog ingestion script와 exact data version hash.
- distance-method mixture model: TF/FP/SNe 등 method label nuisance.
- Malmquist and selection correction.
- correlated Gaussian velocity-field mocks under ΛCDM baseline.
- estimator suite comparison: MLE, MV/MVE, group-GLS, Wiener-filter/CR.
- depth-bin covariance matrix and reference-bin policy.

Acceptance gate:

- mock coverage 0.68 and 0.95 bands pass within MC SE across depth bins.
- GF is withheld unless shell covariance and null are bound.
- apex/phase portraits are labeled diagnostic until covariance is attached.

### 7. DESI는 cap/tracer/redshift asymmetry plot에서 selection-corrected response vector로 승격해라

DESI DR1/DR2는 BAO와 full-shape 분석에서 매우 강한 survey systematics discipline을 요구한다. HTT의 DESI lane은 data-random dipole, mask/window, tracer handoff, NGC/SGC cap difference를 모두 random/mocks로 보정해야 한다.

필요 작업:

- official random catalogs and completeness weights.
- tracer/cap/redshift response matrix.
- cap asymmetry null from random rotations and survey mocks.
- DESI-to-CF4 overlap policy.
- no DESI physical asymmetry claim without window-deconvolved statistic.

Acceptance gate:

- data-random and random-random estimator outputs both saved.
- NGC-SGC figure has window-null bands.
- tracer handoff continuity has occupancy and selection weights.

## 논문을 두 개로 나눠라

### Paper A: Method/theory/statistics paper

제목 후보:

> Signed FLRW-Departure Comparators and Sharp Partial Identification under Rank-Deficient Cosmological Observables

논문 claim:

- constraint-derived signed comparator uniqueness.
- response-rank and null-space semantics.
- sharp identified sets with status algebra.
- posterior prior-exposure theorem.
- finite-cover e-value and two-stage coverage.
- synthetic and repo-local validation gates.

이 논문은 지금 가장 출판 가능하다.

### Paper B: Closed-lane observational diagnostic paper

제목 후보:

> A Calibrated Low-ell and Peculiar-Velocity Diagnostic Atlas for Signed FLRW-Departure Components

논문 claim:

- K1/K5/DESI 중 최소 하나의 lane을 null/covariance/mock까지 닫는다.
- signed comparator point estimate가 아니라 identified interval/e-value/depth-gap status를 결과로 낸다.
- geometry family assignment는 native transfer solver 이후 paper C로 미룬다.

Paper B는 데이터 pipeline을 실제로 닫은 뒤 제출해야 한다.

## 30일 실행 순서

1. P36 replacement theorem 작성과 unit tests merge.
2. P35a/P35b coverage theorem 분리.
3. component-source matrix와 rank-null certificate를 JSON schema로 고정.
4. 모든 D01-D24 figure sidecar에 `estimand`, `R-rank`, `null_status`, `covariance_status`, `claim_tier` 추가.
5. K1 또는 K5 중 하나만 골라 null/covariance/mock lane을 완결.
6. reproducibility package를 다시 만든다: generator scripts, fixtures, environment lock, input recipes, `make reproduce-paper`.

## 논문 제출 전 red-team gate

- “family assignment”라는 단어가 본문 결과절에 나오면 fail.
- `x_C` point value가 null-sector ceiling 없이 나오면 fail.
- covariance estimated인데 Hartlap/Sellentin-Heavens/Student-t policy가 없으면 fail.
- P36 universal strictness 문장이 남아 있으면 fail.
- CF4 shell GF가 matched covariance/null 없이 나오면 fail.
- DESI cap asymmetry가 random/mask/window 없이 물리 해석되면 fail.
- K1 low-ell result가 map-product stability 없이 나오면 fail.

