# R66 최종 독립 과학·코드 검토

**판정: PASS — 선언된 범위의 구현과 해석. 제출 상태: NOT_READY_TO_SUBMIT.**

이번 검토는 P2 companion의 **low-ell CMB 형태론을 물리 관측량과 연결하는 한 단위**에 한정한다. 실제 PR3/PR4의 signed radiation-stress proxy, 선언한 downstream Doppler quadrupole(DQ) quotient, 명시적 이상적 Gaussian reference, retained-band 비선형 물리량과 같은 하늘의 공분산을 함께 검토했다. 현재 범위의 결론을 무효화하는 중대한 열린 결함은 발견하지 못했다. 전체 하늘의 정확한 응력 측정, source-qualified physical PTE, 현재 spacetime shear, 독립적인 새 통계이론 또는 기존 논문 acceptance를 승인하는 판정은 아니다.

관측된 reviewer model identity는 **UNKNOWN**이다. 요청된·상속된 프로파일을 실행 backend의 증거로 취급하지 않았다.

## 검토 근거와 실행 경계

Native repository는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`, baseline은 `3dd1893a3f74af8e1387c844e07897efeabdd0bf`다. 이하 D66은 `docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117`을 뜻한다.

RDC `read_file`로 보고서·유도·결과·출처 기록과 아래 구현을 직접 읽었다.

- `htt/htt/htt/infer/r66_radiation_quotient.py`
- `scripts/r66/{extract_r66_commander,build_r66_ideal_reference,analyze_r66_observables,acquire_r66_temperature_pilot,finalize_r66_dag}.py`
- `tests/test_r66_radiation_quotient.py`

Native command, test, fit, raw FITS 재검사, download, 재해시, Git 작업 또는 native mutation은 수행하지 않았다. `RESULTS/TEST_RECEIPT.json`의 **24 passed, 2.02 s, process362547, exit0**를 기록된 실행 증거로 검토했다. 이를 독립 재실행으로 표현하지 않는다. `OBSERVABLES.json`은 주요 관측·공분산·비선형·GLS 필드를 중심으로 대조했고, 원 extraction snapshot은 관련 kernel 부분을 읽었다.

## 1. 물리 사상과 부호·단위

Frobenius-orthonormal STF 기저에 대해 `delta T2(n)=Q:nn`이면

    <(Q:nn)^2> = 2 ||Q||_F^2 / 15,
    C2 = 8 pi ||q||^2 / 75,
    pi_lin/rho0 = 8 Q/(15 T0).

마지막 식은 brightness의 선형항 4Theta와 사차 구면 moment의 contraction에서 나온다. 구현의 thermodynamic μK→dimensionless stress→Pa 변환은 이 정규화와 맞는다. metric(-,+,+,+), sky-look n과 광자 진행 방향 −n의 구별, flux의 부호도 보존한다.

Retained ell<=6 온도 가족에서 상수·dipole 적합값을 absolute radiation 값으로 오인하지 않고, 명시한 T0와 dipole을 복원한다. T^4 응력의 적분항은 최대 degree26이고 사용한32×64 quadrature는 충분하다. 이차 dipole–octupole 항의24/35 계수는 STF octupole의 trace를 제거한 여섯차 구면 moment와 맞는다. 현재 수치 결과는 정확히 **선언된 retained family 안에서의 값**이다. 누락된 true-sky 고차 모드·스펙트럼·foreground의 수치 상한으로 승격하지 않은 점이 적절하다.

U^T b=0의 quotient는 알려진 하나의 downstream nuisance 진폭만 제거한다. covariance profiling과 U(U^T C U)^−1 U^T의 동등성은 양의 정부호 C에서 옳다. 이를 full-frame boost invariant, Commander upstream 잔여물의 실제 rank1 증명, 또는 제거된 성분을0으로 측정한 결과로 취급하지 않는다. 국소 복사 response L도 derivative/transport 정보가 없는 상태에서 spacetime shear 역산으로 쓰지 않는다. 이 경계는 코드·THEORY·REPORT에서 일치한다.

## 2. 실제 자료·연산자와 관측 결론

Native mask를 먼저 적용한 child average와 native monopole/dipole/STF polynomial columns가 추출 코드에 포함된다. ell>=3 parent-centre basis는 별도로 명시되어 있다. 같은 유한 연산자의 DQ 주입 recovery와 낮은 차수 누출 검사가 어떤 대상을 검증하는지 분명하다. upstream component separation의 전체 response를 검증했다는 주장도 없다.

저장 결과에서 핵심 수치를 대조하면 다음과 같다.

| 값 | 기록된 결과 | 타당한 해석 |
|---|---:|---|
| PR4 primary full STF norm |26.69383797 μK|유한 released-map 추정치|
| PR4 primary quotient norm |26.67642118 μK|선언된 DQ 방향에 수직인 성분|
| quotient stress norm |5.220153745e−6|pi_lin/rho0의 선형 proxy|
| PR4−PR3 contrast의 DQ-수직 power 비율 |94.70315057%|같은 하늘의 두 출력에 대한 대수적 처리 차이|
| fit ell6→8 quotient vector 변화 |66.59578518%|실제 관측의 큰 대역 민감도|
| NSIDE64→128/support control 변화 |4.06739064%|해상도와 retained support가 함께 바뀐 결과|
| retained octupole 효과 |0.0228675746 μK equivalent|선언된 T^4 가족 내의 기여|
| retained exact−linear quotient 차이 |0.0228295343 μK equivalent|전체 하늘의 체계오차 상한은 아님|

따라서 단일 DQ amplitude 변화만으로 두 release 출력의 차이를 설명할 수 없다는 결론은 지지된다. 그 차이의 원인을 cosmology·foreground·beam 중 하나로 특정하지 않는 것도 맞다. 큰 band dependence를 ideal-reference cutoff 안정성이나 작은 T^4 correction으로 닫지 않은 것이 이번 분석의 중요한 정직한 결론이다.

## 3. 실제 온도 reference와 이상적 reference의 구분

005a100개 파일의 I=0 문제는 covariance를 정칙화해서 숨기지 않고 온도 reference의 제품 선택 실패로 보존했다. 원 편광 활용의 유효성을 부정하는 주장도 없다. 별도의 scalar0200은 완전한 파일 하나의 content/operator 진단이며, TUNIT1과 COORDSYS가 비어 있다는 사실을 유지한다. 완료된 파일1개와 qualified actual temperature MC0개를 분리한 현재 보고서는 정확하다.

선택된 reference는 고정 Planck TT spectrum,5arcmin Gaussian beam, ell>=3의 NSIDE128 centre/window 모형, Lref256 및 native-averaged quadrupole block으로 정의된다. 세 실제 추정기의15차원 공동 covariance를 만들고, ell2를 모든 operator가 공유하도록 구현했다. 실수 하늘의 m>0 factor2와 map2alm(weight/pixel_area,iter0)의 finite harmonic sum도 일관된다. 이것은 명시된 이상적 모형의 계산이며 Commander E2E라는 이름을 붙이지 않았다.

알려진 analytic covariance를 선택된 Gaussian likelihood에 사용하므로 primary lower-tail **0.0984010544**의 chi-square4 법칙이 맞다.4096 synthetic draws를 covariance의 유일한 지식으로 취급해 불필요한 Student 법칙을 선택하지 않았다. 별도로 구현한 finite-N Wishart/F와 predictive Student의 조건도 이 주 분석과 구분되어 있다. 실제 physical PTE는 여전히 unresolved다.

## 4. Paired GLS와 다섯 영상의 의미

Paired GLS는 shared sky를 보존한 C8을 사용하고 WJ=I4를 만족한다.2048 training rows로 정한 W와2048 heldout의 역할이 구분되며 선택된 covariance는 W C8 W^T다. 기록된 analytic ellipsoid volume ratio **0.9847118921**은 약1.53%의 감소다. 이를 큰 개선이나 관측 후 선택과 무관한 discovery PTE로 부르지 않은 판단을 지지한다.

F의 구현은 명시한 inscribed stress ball 안에 포함된 mean-proxy ellipsoid의 uniform Lebesgue volume 비율이다. pi/rho의 정확한 positivity body와 pi_lin/rho0의 proxy를 구별하고, exact realized-sky physical F를 unavailable로 남긴다. 작은 F를 cosmological improbability로 바꾸지 않는다. G_F는 한 하늘에 존재하지 않는 depth series를 만들지 않고 NOT_APPLICABLE로 둔다.

같은 q에서 계산한 conventional quadratic power tensor의 trace=C2와 q→−q 불변성 비교는 적절하다. full signed a_lm와 STF가 가역 좌표변환이라는 설명도 맞다. Unit-free ACG는 zero-mean/common-shape 조건과 covariance prior를 명시한 별도 유도이며, 단일 미확정 temperature file에 적용하지 않았다.

## 5. 구현 검증·출처·DAG 범위

Focused test source는 단순 구현 복제에 그치지 않는다. 구면 적분 정규화, exact boost/flux/Landau,24/35 coupling, 독립 Wishart/sky draw, same-sky GLS, adjoint/direct harmonic sum, 실제 작은 FITS에서의 빈 masked RING chunk를 각각 검사한다. 기록된24개 통과는 이 유한 범위의 구현 증거이며 전체 repository suite의 통과는 아니다.

`PROVENANCE/SOURCE_IDENTITY.json`은 extraction 당시 module0616…과 최종 module0b603…를 구별한다. 직접 읽은 extraction kernel들은 최종 코드와 맞고, receipt도 해당 AST identity를 기록한다. 최종 module hash는 OBSERVABLES와 TEST_RECEIPT에 일치한다. 이는 semantic reuse의 근거이며 전체 module의 byte identity 주장과 다르다.

아직 실행되지 않은 finalizer는 fresh PASS, NOT_READY_TO_SUBMIT과 첫9단계 완료를 요구한 뒤 카드 한 개를 추가하도록 작성됐다. 기존 카드의 semantic equality,42-node payload hash, 종전 paper contracts의 보존을 명시적으로 검사한다. P2에 additive pointer를 더하며 automatic successor와 local-agent prompt를 만들지 않는다. 이번 검토는 이 **draft 코드의 보존 논리**를 확인한 것이고, stage10 실제 DAG validation·commit·push가 완료됐다고 주장하지 않는다.

## 한 번의 유한 마감에서 정리할 비차단 문구 두 곳

1. REPORT의 L-response 변화1.21544e−5는 코드상 **||L/rho−(8/15)I5||_F/(8/15)**다. “relative Frobenius change”만 쓰면 기준행렬의 Frobenius norm으로 나눈 값과 혼동된다. 그 정의라면5.4356186057e−6이다. 구현값은 유지하고 분모를 식으로 명시하면 충분하다.
2. SOURCE_IDENTITY의 `current_module_sha256=ef12…`는 과거 중간 snapshot인데 최종 hash0b603…와 함께 남아 있다. 전자를 `intermediate_module_sha256`로 바꾸거나 historical이라고 명시하고 값은 보존하면 된다.

둘 다 결과나 실행 코드를 바꾸는 수정이 아니므로 재계산·새 테스트·새 연구 loop가 필요하지 않다. 중대한 과학·구현 finding은 모두 닫혀 있고, 이 두 메모는 제출 상태를 바꾸는 gate가 아니다.

## 제출 판단

**NOT_READY_TO_SUBMIT을 유지한다.** 실질적인 제한은 source-qualified upstream response/reference의 부재와66.6% band sensitivity이며, 기존 선행 물리 사상·통계기법을 재사용했다는 novelty 범위도 그대로다. 현재 성과는 실제 자료에서의 signed physical proxy, 처리 차이의 정량화, source failure를 교정하고 조건부 통계실험을 실행한 데 있다. 이미 제안된 한 가지 동일-estimand reconstruction 비교와 P2 methods/results 통합 여부 판단이 이 결과의 자연스러운 후속 범위다. 이번 검토는 새로운 gate나 자동 후속 loop를 추가하지 않는다.
