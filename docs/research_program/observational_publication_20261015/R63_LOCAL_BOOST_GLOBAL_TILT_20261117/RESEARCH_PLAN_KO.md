# R63 P4 출판·후속 연구계획

작성일: 2026-11-17. 기준 commit: `f29bbab420a33aecb1c398ddd961fd45097f536b`.
범위: local boost와 global matter–radiation tilt를 구별하는 단일 10단계 연구의 후속 계획.
근거: [실자료 결과](RESULTS/OBSERVED/FRAME_HISTORY_RESULT.json),
[실제 catalogue chart 교정](RESULTS/CATALOGUE_CHART_TRANSPORT.json),
[최종 해석](RESULTS/INTERPRETATION_SUMMARY.json), [연구 보고서](REPORT_KO.md).
현재 판정은 **NOT_READY_TO_SUBMIT**다. 아래 미해결 단계는 자동 실행하는 새 연구 루프가 아니다.

## 1. 판정과 논문의 중심 주장

P4의 목표는 observer boost, 국소 source bulk flow, 물리적으로 지정한 global tilt/history를 공통 응답과 오차법칙으로 구별하는 것이다. R63는 이 질문에 대해 유효한 **조건부 방법·실자료 응답 결과**를 만들었지만, 독립적인 observer 측정이나 global spatial coherence를 입증하지 않았다. 따라서 P4는 NOT_READY_TO_SUBMIT를 유지한다. 원래 42개 gate의 상태를 이 계산만으로 변경하지 않는다.

현 결과의 핵심은 단순한 “rank가 있다/없다”가 아니다. 실제 CF4 footprint와 전체 공분산 아래 STF 정보를 보존하면 제한된 history coefficient의 rank3가 남지만, 그 분리 성분은 선택한 물리적 허용범위에서 사실상 검정력을 제공하지 않는다. 이 결과는 **algebraic identifiability와 물리적 크기에서의 실질적 구별을 분리한 것**이다. 일반적 우주론적 tilt의 불가능성 정리나 관측 상한으로 제시하면 안 된다.

현재 가장 정직한 출판 형태는 R58/R62의 공통 실험과 연결된 methods/application note다. 독립 논문으로 내세우려면 catalogue correction의 실제 source contract와 독립 채널의 모델별 응답을 닫아, “기존 CF4 자료에서 또 다른 선형 적합” 이상의 재사용 가능한 결과를 제시해야 한다. 그 닫힘이 없으면 R63를 P4의 근거 패키지·부록으로 보존하는 판단도 타당하다.

잠정 제목은 “Catalogue-frame corrections and the practical distinguishability of endpoint and compensated-history responses in Cosmicflows-4” 정도가 적절하다. ‘global tilt detection’, ‘model-independent no-go’, ‘first tensorized velocity method’는 현재 내용과 맞지 않는다.

## 2. 이미 얻은 결과와 허용되는 문장

실제 계산은 기존 35,970 group source, 원본 R58 전체 covariance 및 R62 source operator를 재사용해 약 2.283초에 끝났다. 영향받는 54개 과학 테스트가 native runtime에서 통과했다. 이어 같은 실험에서 42개 catalogue-chart affine transport와 직접 GLS의 일치를 확인했다. 실행 receipt는 REPORT의 검증 절과 RESULTS에 보존했다.

| 결과 | 현재 근거와 수치 | 논문에서 허용되는 해석 |
|---|---|---|
| endpoint fibre | source·observer·calibration을 함께 바꾸는 정확한1차 mean fibre, nullity3 | 지정한 constant-source mean과 자유 dipole calibration에서 source/observer 개별값은 식별되지 않음 |
| free-history 적합 | 7 calibration × J2/J3=14개; rank24 또는29; chart 교정 후 W=0 nominal p: J2 .182325–.713944, J3 .277414–.696765 | 고정 covariance·지정 mean family에서 추가 history coefficient가 요구되지 않음; 물리적 tilt 확률 아님 |
| history 정보 | dipole12만 남기고 같은 STF nuisance를 허용하면 nuisance rank12, target rank0; full32에서는 conditional target rank3 | 실제 angular leakage와 공동 nuisance 아래 STF를 버리면 이 history 방향 정보가 사라짐; STF가 독립 데이터라는 뜻 아님 |
| free W 불확실성 | 성분 sd 약0.54–1.01백만 km/s | 물리 영역을 벗어난 무제약 tangent의 낮은 감도를 나타냄; 속도 측정값·물리적 신뢰구간으로 제시하지 않음 |
| tied compensated vs bulk | beta*=.01, 필요한 matter/radiation outer body U<=2999.1923km/s에서 alpha=.1 oracle power 상한 최대 .100000418731 | 해당 선형·고정C·specified source family와 uniform-size 조건에서, 어떤 검정도 이 body에서 유용한 구별 능력을 갖기 어려움 |
| actual q source check | published V3k−Vh는 additive ICRS dipole에 rounding-scale로 맞음; fixed logarithmic-q는 depth dependence를 놓침 | 실제 catalogue chart를 읽고 전파해야 함; fitted correction vector는 독립 observer velocity 측정이 아님 |

자유 W=c b는 matter–normal 속도 계수이고, tied 모델의 U=(1+R)W는 present matter–radiation relative velocity다. benchmark R=2364.75에서 둘을 혼동하면 약2366배의 잘못된 물리적 해석을 낳는다. 예컨대 U=300km/s는 W≈.127km/s다. free W가 수십만 km/s라는 적합값은 이 물리적 해석을 지지하지 않는다.

oracle power 상한은 대립가설에서 가장 가까운 simple null을 취한 Gaussian Neyman–Pearson bound다. composite test의 실제 attained power, 선택된 절차의 coverage, Bayes factor가 아니다. U body도 matter/radiation의 필요한 조건이 주는 superset이며 observer 속도·Doppler displacement·finite-distance 및 이차 stress remainder 조건을 모두 충족한다는 뜻이 아니다. 더 좁은 진짜 물리 body는 그 상한을 높이지 않는다.

현재 실험은 Ωm=.3153, Ωr=.0001의 정해진 benchmark와 inherited fixed covariance를 썼다. 두-fluid universe의 cosmic covariance를 새로 보정하지 않았다. 따라서 모든 probability·power 문장에는 이 working experiment를 붙인다.

## 3. 선행작업과 겹치는 부분, 남는 기여

다음 항목 자체는 새 결과로 주장하지 않는다.

- sourceward luminosity-distance의 source·observer 계수 차이, redshift뿐 아니라 distance/flux도 변환해야 한다는 사실: Hui–Greene, Bonvin–Durrer–Gasparini 및 Davis 등의 선행 결과.
- matter와 radiation의 서로 다른 rest frame, 선형 compensated momentum, dust velocity∝a^-1와 radiation velocity constant: 기존 원전과 저장된 FRONTIER20261020 구성.
- GLS, SVD, nuisance projection, Schur complement, likelihood-preserving path transform, Neyman–Pearson simple-pair bound: 표준 수학·통계.
- x/Q/Pi/F/G_F 다섯 출력, 전체 covariance 보존, noise-reference gauge와 support ratio: R39/T7와 R54/R58에서 이미 구현.
- CONST_V count–CF4 비교와 dipole·constant calibration law: R54에서 이미 실행.
- finite-z STF morphology/polynomial source representation: R61/R62에서 이미 실행.

R63의 구체적인 증분은 이 요소를 **실제 처리된 eta chart와 실제 CF4 source operator**에 맞춰 연결한 데 있다. 정해진 compensated source에서 eta=g n.Vp+z g n.W+n.d를 얻고, h=1−c z g의 상수 부분이 실제 calibration nuisance로 제거되는 메커니즘을 명시한다. 이를 실제 covariance의 quotient에 전파해 “full32에서 rank3지만 물리 tied amplitude에서는 거의 size 수준의 power”라는 수치를 얻었다. 같은 STF nuisance를 dipole-only에도 유지해 target rank0를 확인한 비교는 tensor 정보가 구체적으로 무엇을 보존하는지 보여 준다.

추가로 actual published Vh/V3k pairs가 additive correction에 맞고 fixed logarithmic correction에는 맞지 않는다는 유한 source check는, 차트 선택이 가짜 depth trend를 만들 수 있는 실제 사례다. 다만 원래 완전한 photometric reduction을 재현하거나 논문 전체에 대한 선행연구 대비를 끝낸 것은 아니다. Nusser–Tully2608.14265도 zHEL과 zCMB의 역할을 명시하므로, “이 구분을 최초로 발견했다”는 주장은 제외한다.

이 범위의 기술적 기여는 성립할 수 있지만 단독 출판의 신규성·영향력은 아직 중간 이하다. 가장 강한 반론은 “알려진 작은 radial-law 차이를 기존 자료로 수치화한 것”이다. 이를 해결할 핵심은 독립 채널이 어떤 물리적 fibre를 실제로 자르는지 보여 주는 것이며, CF4 내부 적합을 더 늘리는 것으로 해결되지는 않는다.

## 4. 완료한 chart 보완과 남은 source 보완

실제 row별 logarithmic correction과 고정 additive dipole reference의 차이를
동일한 선택 자료, 관측 연산자, covariance와 design에서 전파했다. 알려진 offset
\(O_m[(A+1)(q_i-n_i\cdot a)/c]\)를 데이터 평균에서 빼고 다시 fit하는 방식이다.
42개 affine transport와 직접 GLS의 최대 scaled discrepancy는
\(4.66\times10^{-12}\), tied \(U\) 벡터 변화의 최대 norm은
**0.428161 km/s**였다. J2 history p 범위는 **.182325–.713944**, J3는
**.277414–.696765**로 교정됐다. 모형 차이에 공통인 offset이므로
separation geometry와 power 상계는 바뀌지 않았다. 데이터 의존 score와 p는 바뀐다.

정수 velocity를 ±0.5 km/s의 결정론적 구간으로 놓은 민감도도 실제 bias map에
전파했다. 이 결과는 임의의 확률분포나 동시에 달성되는 성분별 오차가 아니다.
이 한정된 chart 보완은 완료했다. 남은 입력은 per-method distance/flux response,
group mixing weights, selection·calibration covariance와 finite physical remainder다.
모르는 photometric response를 0으로 놓아 observer posterior를 만들지 않는다.

## 5. 다음 결정적 경로: source-matched remote dipole를 우선

선택한 compensated source가 실재한다면 먼 electron의 photon-rest-frame dipole은 관측자 endpoint boost와 다른 물리량이다. 기존 bounded derivation은 electrons가 dust를, photon bath가 compensating radiation을 따른다는 조건 아래

    w_eff(n,z)=[1+z/(1+R)] n.U,
    E[hat w(n)]=b_v K_R n.U,
    K_R=∫dχ W_v(χ)[1+z/(1+R)]

를 준다. 이 채널은 CF4의 아주 작은 g 대 g[1+z/(1+R)] 차이를 재는 방식에 의존하지 않는다. 따라서 P4 다음 작업은 더 많은 CF4 parameter loop보다 **이 source와 맞는 기존 remote-dipole inference의 입력 계약을 한 번 닫는 것**이 정보 가치가 높다.

그 bounded 목표는 “kSZ로 global tilt를 검출”이 아니라, 공개 inference가 이 particular U에 어떤 identified set 또는 posterior image를 주는지 확인하는 것이다. 현재 문헌 값26km/s를 곧바로 U의95% 상한으로 채택하지 않는다. v1에는 main-text Y10 coefficient와 SM의 power-root amplitude 정규화 차이가 있고, 관련 식의 cross-term 차원 문제도 남아 있다. 저장된 note의12.70/K_R 및22.00/K_Rkm/s는 두 가정의 산술적 변환일 뿐 채택된 물리적 상한이 아니다.

이 경로의 구체적인 수용 조건은 다음과 같다.

| 필요한 입력 | 이 입력을 얻었을 때 실제로 하는 결정 | 실패 시 종료 상태 |
|---|---|---|
| publication 또는 authors’ 공개 계산의 정확한 amplitude convention과 likelihood | D_h=√(4π/3)K_R|U|인지 D_C=√(4π)/3 K_R|U|인지 하나로 고정 | numerical U bound는 unresolved; 두 조건부 변환만 보존 |
| reconstruction window의 정규화/모멘트와 optical-depth bias contract | K_R와 b_v의 공동 불확실성을 inherited law에 맞게 전파 | window/bias와 U를 분리한 제한만 보고 |
| electron–dust와 photon–radiation source matching | 위 remote response가 같은 compensated model의 prediction임을 확인 | 다른 source model 또는 추가 nuisance로 분류 |
| endpoint-map modulation·aberration·mask·selection response | detector boost가 practical reconstruction에 만드는 nuisance를 실제로 profile | 독립 physical channel이라고 부르더라도 calibrated observer separation은 HOLD |
| 실제 posterior samples 또는 likelihood와 covariance | 기존 prior의 induced U measure를 보존한 image 또는 source-specific refit | scalar published bar를 임의3D Gaussian으로 만들지 않음 |

현재 공유 CMB/reference·LSS/PV correlations가 닫히지 않았으므로 CF4×kSZ 독립 곱 likelihood는 만들지 않는다. 먼저 독립 dataset별 조건부 test 또는 simultaneous coverage를 가진 shared-state intersection을 사용할 수 있는지 판정한다. 같은95% 사건이 없는 두 region을 단순 교집합해95%라고 쓰지 않는다.

발표본 full text에 접근 실패가 남으면 공개 accepted manuscript/code의 정확한 한 경로만 확인한다. 같은 차단 요청을 반복하거나 normalized amplitude를 추측하지 않는다. 필요한 입력이 없으면 그 source 경로를 종료하고 보존한다. author contact는 이 계획만으로 수행하지 않는다.

## 6. 대안 경로: qualified aberration/Doppler observer anchor

remote-dipole 정규화·source qualification이 닫히지 않으면 두 번째 유한 경로는 실제 공개 beta_A/beta_D likelihood 또는 공동 posterior를 확보해 observer anchor로 검토하는 것이다. Planck/Ferreira–Quartin의 ell↔ell±1 aberration response는 이미 알려진 방법이며, 새 novelty는 이 특정 source와 CF4 correction에 맞춘 joint identified set에만 있다.

Amplitude와 (l,b)의 주변 오차막대로 Cartesian covariance를 새로 만들지 않는다. temperature-dipole distortion removal, aberration–Doppler leakage, dipolar lensing, foreground·mask·noise, 같은 sky의 SMICA/NILC 의존성을 포함하는 자료여야 한다. beta_D=Delta1가 되는 허용 모델에서는 Doppler 통계를 추가해도 intrinsic/observer 분리가 자동으로 생기지 않는다.

수용 조건은 실제 nuisance-profiled observer/history response가 기존 endpoint fibre를 자르는지, 그리고 source-matched calibration/error를 허용한 뒤에도 그 절단이 물리적 target 크기에서 유의미한지다. covariance가 없는 scalar anchor는 문헌 비교 표로는 사용할 수 있지만 “새 독립 observer3D 측정”으로 P4 gate를 통과시키지 않는다.

## 7. 유의미한 감도와 후속 실행의 수렴 기준

다음 채널을 실행할지 결정하는 기준은 rank 증가만이 아니다. 고정된 비교 family와 covariance에서 projected mean distance δ가 있으면 alpha=.1에서80% power의 **필요조건**은

    δ >= Φ^-1(.8)−Φ^-1(.1) ≈2.12

이다. 이것은 oracle upper bound를 이용한 screening 기준이며, 충분한 조건이나 actual test의 검정력 보장은 아니다. nuisance·window·calibration·remainder 불확실성을 포함한 conservative projected distance가 이 기준에 한참 못 미치면 그 설계는 실행을 확대하지 않는다. 다른 alpha/power를 선택한다면 공개 target를 먼저 고정한다.

기존 CF4 bound의 δ는 허용 body에서 대략 수×10^-6 수준이다. 따라서 같은 source, O, C, nuisance family에서 반복 적합·새 기저·더 많은 posterior draws는2.12와의 격차를 해결하지 못한다. 이를 재검토할 실질적 trigger는 독립 calibration anchor, 새 물리 response, 실제로 개선된 observation/covariance 또는 틀렸음이 입증된 source law다. 파일 구조·five-view presentation·단순 수치 precision 변경은 trigger가 아니다.

강한 물리 모델 비교를 출판하려면 finite source interval, beta ceiling, observer Doppler displacement, O(beta²) stress/metric accumulation, photometric/selection response의 총 remainder가 **구별하려는 projected signal보다 작다**는 근거가 필요하다. 그 bound가 없으면 관측된이차 이하 차이를 근거로 강한 physical rejection을 만들지 않는다. 완벽한 전체 우주론 솔버를 요구하는 대신, 정해진 source와 실제 channel에 필요한 finite error만 좁게 구한다.

## 8. 원고 구성과 현 종료점

본문은 문제와 source contract → processed eta의 endpoint/history map → 실제 source correction의 chart effect → full covariance와 shared nuisance → rank와 physical-scale oracle power → 독립 remote/aberration channel이 자르는 fibre 순서로 구성한다. generic GLS·five-view 정의는 재사용 출처를 인용하고 필요한 식만 남긴다.

주요 그림은 기존 결과의 두세 개면 충분하다. 현재 생성한 두 그림은 tangent 감도·물리 body·oracle power의 비교와 actual-q chart 차이다. 원고의 추가 그림이 필요하면 저장된 singular spectrum으로 full32 대 dipole12의 같은-nuisance 차이를 보여 준다. 추가 데이터 적합 없이 기존 carrier에서 만들 수 있다. 엄청난 tangent W mean의 하늘지도를 물리적 속도 지도처럼 보여 주지 않는다. actual-q source chart residual과 변화한 p는 부록에 충분하다.

현 R63의 닫힘은 “conditional actual-data response experiment completed; P4 physical attribution and submission unresolved”다. 다음 유한 source action은 remote-dipole published amplitude normalization/window/bias의 정확한 입력을 확보하는 것이고, 그것이 불가능하면 qualified aberration likelihood의 가용성을 확인하는 것이다. 어느 입력도 없으면 P4를 HOLD로 보존하고 R63 결과를 companion/appendix로 유지한다. 자동 다음 루프, 새 로컬 에이전트 프롬프트, 추가 CF4 fitting campaign은 이 계획에 포함하지 않는다.

독립 최종심사와 최종 DAG 상태는 [VALIDATION.md](VALIDATION.md), [REVIEW/final_review.json](REVIEW/final_review.json), [RESEARCH_DAG.json](RESEARCH_DAG.json)에 연결한다. 과학 결과의 닫힘과 논문 투고 준비를 구분한다.
