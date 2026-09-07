# HTT 모의심사 후속 연구 — 확정 계획과 이론 우선 DAG

Date: 2026-09-07
Owner: MAIN conversation; downstream implementation/data executor: Local Codex
Status: PLANNING_COMPLETE / SCIENTIFIC_EXECUTION_RELEASE_PENDING

## 1. 이번 결정

55쪽 pedagogical report는 요청된 해설판으로 보존한다. 모의심사가 research article 기준으로 지적한 기여도·선행연구·관측 연결 문제는 새 연구논문과 후속 과학계산에서 해결한다. 기존 해설판을 실패작으로 소급 분류하거나, 학술지용 분량에 맞추기 위해 자기완결적 증명을 삭제하지 않는다.

후속 연구의 주 질문은 다음으로 고정한다.

> 저다중극 형태와 관측자·깊이 정보를 함께 다룰 때, 추가 관측과 부수변수 가정이 각각 어떤 식별가능성을 제공하는가?

첫 산출물은 CMB Q/O의 공동 불확실성과 고다중극 부수변수 처리의 비교다. 두 번째는 CF4·DESI 등으로 관측자 운동, 국소 구조, 깊이 일관성을 구별하는 분석이다. 조건부 운동학적 상한은 이 두 결과를 실제 전단·와도 측정으로 오인하지 않게 하는 별도의 물리적 해석 축이다. 새로운 Bianchi solver, 모든 family의 forward atlas, 모든 원격 관측 분석을 이번 논문의 선행조건으로 넣지 않는다.

계획은 완료했다. 그러나 이 문서의 존재를 이론 연구 전체나 구현의 완료로 세지 않는다. 아래 T1–T4의 과학적 명세와 검증 결과를 MAIN이 닫은 뒤, 하나의 실행 인계로 C0–C6 전체를 Codex에 위임한다. 지금은 그 실행을 시작하라는 인계가 아니다.

## 2. 읽은 자료와 증거의 구분

사용자 제공 자료는 두 모의심사, 두 업그레이드 제안, 2026-09-07 16:19 KST 자산 목록이다. 이들의 수치 재현 주장은 심사자 보고다. 이 대화에서 실제로 받은 것은 Markdown이며, 첫 심사의 별도 검산 ZIP 링크만으로 그 ZIP·전체 원 로그가 현재 환경에 있다고 간주하지 않는다. 새로 직접 유도한 식은 `01_DERIVATIONS_AND_REVIEW.md`, 실제 읽은 코드와 경로의 재사용 범위는 `02_REUSE_AND_EXECUTION_CONTRACT.md`에 구분했다.

원격 저장소는 다음 두 축으로 조사했다.

- 보고서·해설판 기준: `9c86759f4ac7054d01d88689290a658e8ffd5863`.
- 현재 default 코드 기준으로 관측한 `research/pr04-multicomponent`: `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`.

두 branch는 같은 과학적 구현 상태가 아니다. 추가로 exact-source Q/O decoder `9f7d06dec0fce1c3a8a53fa5372c84d9c679c037`의 실제 소스와 PR451 파일 목록을 읽었다. Root/기능 subtree, default code search, 관련 구현과 기존 depth 프로그램을 조사했지만, 큰 recursive JSON은 반환에서 잘렸고 모든 branch의 모든 source/log를 읽은 것은 아니다. 따라서 이번 결과는 **분기 간 기능 지도와 핵심 경로 source review**이지 저장소 전 파일의 실행 감사가 아니다. 다음 로컬 C0는 여기서 선택한 donor 경로와 import 경로만 확인하며 전역 재조사를 반복하지 않는다.

Native shell과 독립 Python 접근이 이번 MAIN에서 ClientError로 종료되어 새 code run, Monte Carlo, AST parsing 또는 파일 hash 계산은 수행하지 못했다. 웹 계산기로 일부 표시 상수만 산술 확인했다. SciSpace 검색 후 문헌 identity·주요 역할을 원 arXiv/저널 자료와 대조했다. 이 제한은 새 연구 식의 직접 유도와 구별한다.

## 3. 심사에서 채택할 내용과 수정할 내용

### 3.1 채택

1. Multipole-vector·frame/invariant 계보 및 2026 boost operator를 비교한다. '파워보다 정보가 많다'는 일반론이나 '처음으로 결합 궤도를 완전히 표현한다'는 주장은 독창성의 충분한 근거가 아니다.
2. 인쇄된 axial minors는 이미 L=10을 사용한다. L<=9의 m=0 블록 열 부족과 결합하여 정확한 최소 cutoff를 10으로 강화한다. 비축방향 여섯 사례의 수치를 모든 방향 정리로 확장하지 않는다.
3. 결정론적 nuisance image와 진폭 제한·Gaussian prior·추가 data-conditioned nuisance를 같은 parameter/model 안에서 비교한다. 단순 trace ratio를 정보 손실률로 부르지 않는다.
4. 실제 forward에는 monopole의 beta^2 T0와 beta DeltaT를 함께 비교한다. J_b의 source derivative와 beta에 대한 Jacobian을 분리한다.
5. 반복된 부정형 운영 문구는 논문 본문에서 정리하고, 과학적 domain/assumptions는 해당 결과 옆에 유지한다. 미사용 DeltaOmega_k나 재현 설정이 없는 historical finite-pixel 숫자는 논문 핵심 결과에서 제외한다.
6. 전체 합성 관측 실험은 복원뿐 아니라 bias, coverage, null size, power, abstention을 평가한다. 새로운 발견이나 map 간 일치 자체가 통과 조건은 아니다.

### 3.2 채택하지 않거나 고칠 내용

- **delta 사전 고정:** 유효한 deterministic error enclosure에서 s_min>1을 본 뒤 양의 여유폭을 보고할 수 있다. 잘못 선택한 error family/radius 또는 확률적 coverage의 선택 편향이 문제이지, 관측한 결정론적 여유의 사후 표기는 문제가 아니다. 제안서 P5는 첫 심사의 올바른 지적과 모순된다.
- **보편적 low-ell boost no-go:** 지정된 Gaussian intrinsic-octupole 모형에서 Fisher는 양의 정부호다. 정밀도가 나쁜 것과 구조적 비식별성은 다르다. intrinsic tensor가 무제한 결정론적 미지수일 때의 정확한 비식별성과 분리한다. 제공된 입력/공식으로 conditional RMS는 약 0.88235–0.88785이고 0.8435가 아니다.
- **'완전한 이상성 통계':** lossless orbit representation은 모든 대립가설에 powerful한 하나의 검정이 아니다. Overcomplete packet을 독립 9차원 Gaussian 좌표처럼 다루지 않는다. 귀무 결과가 모든 기존 anomaly의 상한을 주지도 않는다.
- **parity:** chi의 부호는 handedness, |chi|는 parity-even magnitude다. |chi|의 유의성만으로 parity violation을 주장하지 않는다. 외부 축과의 정렬에는 실제 프레임도 남겨야 한다.
- **all-observer 사다리:** 단일 관측자와 amplitude만 있는 첫 단계에서는 MES 전단/와도 상한이 나오지 않는다. all-domain·미분·congruence premise를 추가하기 전에 10^-3 상한을 배정하지 않는다.
- **mask arithmetic:** Gaunt/Wigner 경로도 mask coefficients, mask/pixel model, truncation, transfer와 roundoff의 영향을 받는다. 두 numerical 경로가 가깝다는 사실이나 Nside 수렴만으로 exact error membership을 증명하지 않는다. toy L=30의 수렴을 실제 mask로 옮기지 않는다.
- **axisymmetry 일반화:** 특정 LRS/axisymmetric 모델이 cyclic chart 밖이라는 것은 맞지만 generic Bianchi I/V/VII0 shear까지 모두 축대칭이라고 할 수 없다. degeneracy strata와 full-tensor fallback을 별도로 다룬다.
- **심사 숫자 수용:** 2e5 chart-quantile 표와 0.99 leakage 표는 현재 심사자 계산 보고다. normalization, covariance, units, seed, algorithm을 닫고 재현하기 전 기존 테스트 oracle로 고정하지 않는다.
- **문헌 정정:** astro-ph/0502574는 Katz–Weeks가 아니라 Land–Magueijo다. Katz–Weeks의 관련 논문은 astro-ph/0405631이다. SciSpace의 ingestion date나 불완전 저자 목록도 그대로 bibliography에 복사하지 않는다.

두 심사의 '관측 결과 없으므로 reject' 식 일반화도 그대로 받아들이지 않는다. 새 방법이나 정확한 이론 결과는 관측 검출 없이도 연구 성과다. 다만 이번 programme은 요청대로 관측 검증까지 연결한다. 게재 보장이나 9개월 일정은 산출물 검증과 처리량 실측 없이 채택하지 않는다.

## 4. 과학 범위와 논문 구성

### A. Tensor morphology and nuisance-conditioned inference — 주 실행 경로

대상은 Q/O 공동 형태와 불확실성, local-observer response, mask·high-source 선택에 따른 결과 차이다. 비교는 네 가지로 고정한다: unrestricted deterministic nuisance, weighted bounded nuisance, fixed Gaussian nuisance, same-map auxiliary modes로 jointly constrained nuisance. 비교의 관심 parameter·데이터 공간을 맞춘다.

주 데이터는 **기보유 PR3 SMICA + 실제로 대응되는 FFP10 signal/noise/product 처리**를 우선한다. matched noise/calibration이 확인되지 않으면 실제 p-value 분석을 실행하지 않고 synthetic/model-conditional 결과까지만 생성한다. Commander·PR3 다른 성분분리 지도는 같은 하늘의 systematics/control family다. PR4는 제품 9개와 빈 NPIPE 경로를 구별하여 독립 intake 결과가 충족될 때만 추가 control로 사용한다. ELC는 유용한 후속 작은-mask 비교지만 이번 필수 다운로드로 잡지 않는다.

출력의 중심은 '가정을 추가했는가, 데이터를 추가했는가'에 따른 compatible/inferred region의 변화다. 새 coordinate로 같은 데이터를 다시 적었다는 이유만으로 information gain을 주장하지 않는다. 55쪽 해설판을 인용 가능한 동반 설명으로 유지하고 research article은 이 비교와 결과에 집중한다.

### B. Depth-resolved motion and pole coherence — 장기 목표를 보존하는 두 번째 경로

다음 네 객체는 별도다: ShellSourcePole, CumulativeObserverPole, RemoteDipolePole, RemoteQuadrupolePole. 현재의 CMB map 하나에 redshift label을 붙여 네 객체가 관측됐다고 하지 않는다.

이번 선택 범위는 기보유 CF4 catalog/reconstruction, Carrick/CORAS/Lilow의 correlated field controls, DESI spectroscopic data/randoms/mocks를 이용한 window-matched bulk/affine/dipole-depth diagnostics다. source-shell transfer는 CAMB/CLASS의 FLRW model-conditional 예측으로 분리한다. 광학적/은하 lensing shear는 observer-congruence shear와 다르다.

H_LOCAL과 H_LSS에 더해 H_COHERENT_PHENO는 명시된 redshift basis 위의 phenomenological residual model로만 비교한다. H_GLOBAL_NATIVE는 native transfer와 atlas가 없으면 실행 대상이 아니다. 낮은 redshift에서 잔차 방향이 일관되더라도 global tilt 검출로 승격하지 않는다.

kSZ/pSZ는 별도 후속 경로다. ACT lensing kappa alm은 high-resolution temperature map이 아니다. 원격 quadrupole은 최근 실제 연구에서도 유의한 검출이 없다는 보고가 있으므로 점 pole이나 zero-field를 강제하지 않는다. 해당 데이터·tau response·mean-field·cross covariance가 준비되지 않으면 이번 실행 범위 밖에 남긴다.

### C. Conditional kinematical envelopes — 물리 해석 경로

새로 유도한 내부 1차 모형의 cancellation-sensitive bound와 기존 MES 계보의 conservative bound를 나란히 제시한다. 같은 모델이라고 합치지 않는다. derivative coefficients와 intrinsic-dipole attribution은 관측오차와 분리된 assumption coordinates다. 데이터가 직접 제한하는 functional과 nullspace 때문에 제한하지 못하는 functional을 구분한다.

선택된 이론 범위의 결과는 '이 조건 아래의 상한·민감도·비식별성'이다. native Bianchi evolution이나 finite-amplitude nonlinear remainder를 계산하지 않았는데 관측된 cosmic shear/vorticity라고 부르는 단계는 없다.

## 5. MAIN에서 끝낸 뒤 넘길 네 이론 묶음

T1–T4는 새로운 계획 회의가 아니라 각각 수식·선택·검증 oracle을 닫는 연구 단위다. 본 계획의 다음 실행은 T1이다. T1에는 이번에 이미 얻은 직접 유도들이 들어 있으며, 남은 작업은 source-to-contract 교차검증과 원고 수정안 정합화다.

| ID | MAIN 산출물 | 종료 조건 |
|---|---|---|
| T1 | Novelty/source comparison; L=10 정리; Beta law·conditional error bound; 강화된 내부 shear/vorticity bounds; deterministic margin 정정 | 모든 핵심 식의 가정·단위·counterexample 명시. 외부 문헌 최초성은 미확정이면 좁은 기여 주장으로 종료. 새 algebra를 코드 검증 완료로 표기하지 않음 |
| T2 | Exact/controlled observer forward, four nuisance models, positivity/cancellation cost, same-data Schur complement, finite-operator target/error bound | J_source와 G_beta 계약 분리; likelihood mean/covariance/derivative를 하나의 source-order convention에 고정; interval/empirical error 결과 언어 결정 |
| T3 | Q/O joint-uncertainty and calibration protocol; primary score; contrast/control family; matched null/product decision table | score, train/calibration/test split, ties, chart fallback, multiple comparisons, prior sensitivity, coverage/power tests가 실행자가 선택하지 않아도 되도록 고정 |
| T4 | CF4/DESI/FLRW-shell response와 depth windows; radial-vorticity null; local/LSS/coherent basis 및 identifiable targets | 창·frame·단위·correlated errors, nuisance profiling, pole gap/abstention, radial-only 불가 주장의 수식 및 tests 고정. remote/native blocks는 명시적 제외 |

최종 SCIENCE_RELEASE는 T1–T4의 통과 여부를 소비하는 단일 handoff snapshot이다. 계획 문서가 늘어나는 것을 진척도로 세지 않는다. 레지스트리·gate 수를 추가하지 않고 실제 immutable spec과 입력/출력 계약을 하나로 묶는다. Codex가 원격 저장소나 파일 header에서 확인할 수 있는 product identity는 C0의 기계적 확인으로 남겨도 된다. 하지만 score, prior, missing response, covariance independence 같은 과학 결정을 '코딩하면서 적당히 선택'하도록 남기지는 않는다.

## 6. 그 뒤 Codex가 끊김 없이 수행할 구현·분석 DAG

```text
T1 ──> T2 ──> T3 ──┐
 └──────────> T4 ───┤
                    v
            SCIENCE_RELEASE
                    |
                   C0  selected donor/import and data admission
                    |
                   C1  reuse + required numerical modules + focused tests
                    |
             +------+------+
             |             |
            C2             C3
       operator validation  exact/statistical/synthetic validation
             +------+------+
                    |
                   C4  joint end-to-end synthetic experiments
                    |
             +------+------+
             |             |
           C5A            C5B
       CMB data study   depth data study
             +------+------+
                    |
                   C6  sensitivity, figures, paper tables, Git return
```

C2와 C3는 C1 인터페이스가 고정된 뒤 독립 진행 가능하지만 서로의 결과를 독립 심사로 부르지 않는다. C5A/C5B는 데이터 입수조건에 따라 한쪽만 실행될 수 있다. 미입수 branch가 다른 branch의 과학 결과를 막지 않으며, 그 경우 전체 programme가 완료됐다고는 하지 않는다. 어떤 null/대립 결과든 계약을 만족하면 유효한 산출물이다.

코드 경로는 `02_REUSE_AND_EXECUTION_CONTRACT.md`에 분류했다. 기존 common/OBSSTAT/HTT/MIO 역할을 유지하고 별도 전 우주론 프레임워크를 만들지 않는다. 현재 source에 존재하는 helper를 먼저 쓰되, 이름이 같다는 이유로 physical state catalogue를 temperature Q/O packet으로 치환하지 않는다.

## 7. 테스트와 관측 결론을 혼동하지 않는 acceptance

- Exact arithmetic fixtures: Beta CDF와 sharp trace endpoints, zero/known boost, all-sky high-to-low zero, selected axial L=10 certificate, Schur-complement and bounded-cost identities, radial curl null.
- Numerical validation: stated reference와 error budget에 대한 오차. 같은 수치가 나온다는 사실과 rigorous enclosure를 구별한다. 양성·음성·경계·nonfinite·singular input을 포함한다.
- Statistical validation: held-out synthetic experiments에서 size/coverage/power/abstention을 uncertainty와 함께 보고한다. 하나의 KS p-value를 PASS gate로 삼지 않는다. 동일한 값/분포 가설이 성립해야 하는 이유를 먼저 명시한다.
- Real data: map 차이가 예상보다 크거나 anomaly가 유의하지 않다는 것은 코드 FAIL이 아니다. calibration model inadequacy 또는 과학 결과로 반환한다. 큰 p값을 모든 대립의 배제로 해석하지 않는다.
- 600개 null을 쓰면 최소 순위는 1/601이다. 1312개 파일이나 재사용 noise seed를 그만큼의 독립 관측으로 세지 않는다. posterior sample은 null sky가 아니다.
- 진짜 신규 이론 문제를 발견하면 science boundary로 반환한다. 같은 계약의 import, algebra implementation, numerical stability, batching, plotting, packaging 결함은 Codex가 수정·검증을 계속한다. '추가 사고가 필요 없다'는 뜻은 연구모형을 임의 선택하지 않는다는 뜻이지 오류 진단을 금지하는 뜻이 아니다.

## 8. 분할·비용·완성도

월 단위 ETA를 임의로 배정하지 않는다. T1–T4 네 개 이론 단위, C0–C6 일곱 구현·실행 단위(실자료 두 분기)를 작업 분할로 사용한다. 데이터는 기존 inventory를 재사용하고 1.5TB 전체를 복제·재해시하지 않는다. Local의 C0/C1에서 한 파일/한 mask/소수 seed 처리량과 memory를 측정해 production batch 크기를 계산한다. 초기 planning allowance는 실측 진전에 따라 조절하되 누적 비용과 변경 이유를 보존한다.

현재 완료: 자료 기반 심사 판별, 추가 직접 유도, 핵심 경로 source review, 선택 범위·자료 우선순위·DAG·execution release 조건을 갖춘 계획. 미완료: T1–T4 전체의 최종 scientific specification freeze, native 새 계산·테스트, 실제 데이터 분석. 기존 두 보고서 산출물의 완료는 유지된다. 새로운 programme 완료율을 기존 테스트 개수나 문서 수로 산정하지 않는다.

## 9. 좁혀진 문헌 지도

아래는 이번 계획에 실제로 소비된 원전 identity다. 발견용 검색 결과나 2022 ingestion metadata를 출판 연도로 쓰지 않는다.

- Copi, Huterer, Starkman: multipole-vector representation, arXiv:astro-ph/0310511, PRD70 043515 (2004).
- Katz, Weeks: Polynomial Interpretation of Multipole Vectors, arXiv:astro-ph/0405631, PRD70 063527 (2004).
- Land, Magueijo: frames/invariants, arXiv:astro-ph/0502574, MNRAS362 838 (2005).
- Dai, Chluba: harmonic aberration operator, arXiv:1403.6117, PRD89 123504.
- Chluba, Ravenni: The boost operator: properties, computation, and applications, arXiv:2505.02080; MNRAS548(3)stag698, 14 April 2026, DOI 10.1093/mnras/stag698.
- Saadeh et al.: How isotropic is the Universe?, arXiv:1605.07178, PRL117 131302. Mode/model-conditional shear bounds are not generic MES or local velocity-gradient bounds.
- Clarkson, Barrett: arXiv:gr-qc/9906097; acceleration and Copernican/isotropic-radiation assumptions must not be silently suppressed.
- Planck NPIPE: arXiv:2007.04997; product/simulation correspondence must be checked locally.
- Aluri, Patel: PR4 low-multipole isotropy, arXiv:2506.22795.
- Nofi et al.: nearly full-sky foreground cleaned low-multipole maps, arXiv:2509.03718; ApJ1005 144 (2026), DOI 10.3847/1538-4357/ae685f. Useful future small-mask control, not locally admitted by this plan.
- Cayuso, Johnson, Mertens: remote dipole reconstruction, arXiv:1806.01290.
- Krywonos et al.: remote quadrupole/pSZ constraints, arXiv:2607.16071, 17 July 2026. No significant detection reported; not an input map already owned here.

The two original referees and upgrade notes are treated as criticism/proposals, not paper publication authority or new observational receipts. The main research derives its results independently of their verdict labels.
