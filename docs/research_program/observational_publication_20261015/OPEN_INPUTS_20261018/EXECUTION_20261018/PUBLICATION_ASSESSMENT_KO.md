# 실제 공개입력 연구 이후 여섯 논문 판정 — 2026-10-18

## Verdict

**REJECT / NOT READY** for journal submission. 원래42노드 중17개(40.48%)의
기존 scoped 완료를 재사용했고, 이번 자료 취득/진단을 추가 과학 노드 완료로
계산하지 않았다. 여섯 논문 모두 NOT_READY_TO_SUBMIT다. Main merge/투고는 없다.
이 문서는 새로운 영구 gate가 아니라 owner의 다음 실행/출판 판단을 위한 보고다.

## Minimal publishable claim

지금 게시할 수 있는 범위는 draft 연구 branch의 **실자료 처리·상대 보정·선택·
프레임 민감도 진단**이다. 저널의 신규성/실측 physical inference acceptance를
통과했다는 뜻이 아니다. 각 수치는 생성 코드/결과/그림/보고서/독립 검토에 연결된다.

|논문|이번 실제 증가분|허용되는 해석|아직 부족한 원래 acceptance|
|---|---|---|---|
|P1|[D07결과](D07_JOINT_CALIBRATION/D07_RESULT.json)의559pair/77calibrator inventory,75angular support와97LP; 공통 gauge witness|선언한 상대 calibration model의 조건부 feasible-set image|common-congruence optical→kinematic mapping와 정당한 finite-z/flow/selected-law bounds|
|P2|[D04결과](D04_SPLIT_NOISE/RESULT.json)의실제4splitnoise,원래T26846/P30021operator,고정L02family|같은nominalID의처리·형태 민감도|공동signal/noise/foreground/weight-selection law와통계량별coverage|
|P3|[D02](D02_HI_CF4/D02_RESULT.json)의628전체genealogy/조건부검출·품질fit,[D03](D03_PANTHEON_CF4/results/D03_RESULT.json)의1701행/fullcovariance/654hostassociation와[D06flow](D06_FLOW/D06_RESULT.json)|실제표적 내부 선택 진단과종속catalogue비교|전체parentselection,공동angularcalibration/velocity law; exactSNcontributors|
|P4|기존V02localboost결과 재사용; [D08](D08_EXTERNAL_PAYLOAD/RESULT.json)에서source-qualified legacyTfixture intake|기존 endpoint/local 실험 및 외부파일의유한처리|이미계산된global-history response와commonframe/IC/transport|
|P5|[D08결과](D08_EXTERNAL_PAYLOAD/RESULT.json)의두공식legacyT파일Gitblob/단위/169열fit검사|T-onlyexternal fixture,물리atlas적격성없음|검증된polarizedT/E/Ball-mphysicalatlas와equivalence/likelihood/null|
|P6|[D05결과](D05_GAIA_RADIO/RESULTS.json)의Gaia1614173행/16mode/13framequotient/12angularholdout/radio713|공개frame에서의관측VSH와선택·공간민감도|source-matchedsame-congruencenonradialresponse,NNR/frame/공동오차law|

공통 입력을 여섯 개 독립 검증으로 세지 않는다. P1/P3의559행과P3/P6의
calibration ancestry, Planck의공통하늘·중첩support, Gaia/radioframe중첩을 유지했다.

## Strengths

원자료는 Git 밖에 보존했다. 실제 overflow-free full Gaia, 실제 SH0ES C/L/y,
실제 HI 비검출을 포함한 분모, 실제 네 split FITS, 공식 script가 가리킨
수정 CF4++ 입력을 처리했다. 원래 CF4 대형 fit/Planck 관측5지도/8pair를
되풀이하지 않고 검토된 cache와 기존 연산자를 재사용했다.

추가 [SH0ES 전체 ladder 재현](SH0ES_LADDER_20261018/REPORT.md)은 실제3492행/
47변수의 Gaussian GLS와37host 공분산을 계산했다. QR/SVD 상대차1.98e-15,
host 공통모드 quotient rank36, 7tests와[별도 독립 검토](SH0ES_LADDER_20261018/INDEPENDENT_REVIEW.md)를
통과했다. H0=73.042819±1.007148은 공개모형의 formal 재현값이지 원논문의
더 넓은±1.04 또는 CF4 공동오차 추론이 아니다. 원래42노드/준비도는 불변이다.

[Moving-lens 실자료 요약 실험](MOVING_LENS_20261018/REPORT.md)은 공개된 주파수별
진폭과 difference-map 진폭이 공통 scalar filter로 교환되지 않음을 실제수치로
보였다(잔차−.09,+.02,+.08; 반올림한계.015). 임의 의존성을 허용한 조건부
Gaussian contrast의 반올림/source-variant envelope는[.198267,1.931733]이다.
이는 서로 다른 projection의 차이일 뿐 physical moving-lens M의 유한구간이
아니다. Filter/SED/기타오차의 관측 bound가 없으므로 M은 UNBOUNDED다.
[독립 검토](MOVING_LENS_20261018/INDEPENDENT_REVIEW.md)의 실제 P2 HEAD-replay 결함을
한 번의 제한된 수리로 닫고11tests를 통과했다. 생성/그림은 재실행하지 않았다.

[Grouped64 source 비교](GROUPED_FLOW_SOURCE_20261018/REPORT.md)는 이미 수행한
유한 sphere probe를 재사용해 두 component 순서와8고정 시나리오를 원논문
6개 표 행에 대조했다. 모든 시나리오에서 완전한 행의 정수 반올림 parity는0/6이다.
명시한L1000/origin32에서 max잔차는 저자 reversal175.925932km/s, 대안순서
27.210855km/s지만 더 가까운 대안을 정답으로 채택하지 않았다. ±.5km/s는 표의
반올림 검사일 뿐 과학오차 허용치가 아니다. 원논문/저자 notebook의 물리결함을
입증한 것이 아니며 producer geometry/component/estimator는 SOURCE_CONFLICT/HOLD다.
11tests와[별도 독립 검토](GROUPED_FLOW_SOURCE_20261018/INDEPENDENT_REVIEW.md)를 통과했고
grid/host query/기존CF4 fit은 재실행하지 않았다.

[Pantheon+ source 응답](PANTHEON_SOURCE_RESPONSE_20261018/REPORT.md)은 실제 공개된
10FITRES/50HEAD/6로그(총15687158bytes)를 처리했다.32729행 중25843개 좌표를
16truth 대조와 원본float32→double 변환의 정확한 일치로 복구했다.6886개 방향은
불명,61개 공분산 quadratic은 평가불가로 보존했다. Color의 raw중앙값.0615218과
source-dust-predictor 차감후−.0115361은 selected-source 응답이며 순수측정오차가
아니다. SIM_c/mB는hostdust전 생성변수이므로 mB보정은HOLD다. 한 번의60.934s실행,
10controls 및[독립 검토](PANTHEON_SOURCE_RESPONSE_20261018/INDEPENDENT_REVIEW.md)를 통과했다.
미공개SDSS/SNLS HEAD나완전한angular selection법칙을 만들지 않았고42노드는불변이다.

[HFI 실제 beam 원본 자격 검사](D04_HFI_BEAM_SOURCE/SOURCE_ASSESSMENT.md)는
86556876byte 이중gzip을 받아451FITS/1319HDU의 메타데이터를 실제 확인했다.
단일gzip 첫실패를 보존하고 관찰된 형식만 수정했으며12tests/별도fresh리뷰를
통과했다. HM-labelled T/E/B진폭B(l)는 존재하지만 일반lm지도응답은 아니다.
이후 [고정100GHz 유한 계산](D04_HFI_BEAM_NUMERIC/REPORT.md)은 공개진폭과
고정가중치, 기존RING64 COARSE 캐시를 써서 normA=5.908757152759843e-9,
정확유리수Frobenius상계0.000000019597130453033084095083을 얻었다. 공개토큰에서는 Eℓ5만
비영이며 높은E→낮은B 블록은0이다. 이는 물리적 beam불확실성이나 절대µK오염량의
상계가 아니며 D04의 native-child연산자를 대체하지 않는다. 한 번의7.980s실행,
4tests/실제controls 및 [독립 검토](D04_HFI_BEAM_NUMERIC/INDEPENDENT_REVIEW.md)를
통과했다. 누락된 upstream주파수행 근거만 작은prefix발췌로 보완했으며 수치는
재실행/변경하지 않았다. 전체split/공통하늘/foreground/선택법칙과 L03은HOLD다.

[SDSS source-only 실험](SDSS_SOURCE_NULL_20261018/SOURCE_ANALYSIS/REPORT.md)은
10,643,218,721byte 공개원본의 공식MD5와 전체2048파일 구조를 검증한 뒤,
결과를 보기 전에 고정한 box0–63/Y0의 64개 파일을 실제 분석했다. 실제 CSV의
36열/단위/mean-SD 정의는 별도 Astra가 확인했다. 두 중첩 창의16계수와
공동 working covariance를 보존했고 첫 mock의6controls를 통과했다.
한 번의38.420064820s 실행에서 고정threshold2.955166847497834 초과는4/64,
empirical/mean-working 분산비 범위는.966717–1.461197이었다. 같은 basis의
두 창 사이 empirical correlation은.720960–.859491로, 독립 창으로 곱하지 않는다.
3개PNG/PDF쌍과64개개별 결과/공분산을 보존했다. 이는 released SDSS source만의
진단이며 separate-box independence도 NOT_CERTIFIED다. H02의CF4+TF+6dF 공동법칙,
물리coverage 또는 원래노드완료의 대체물이 아니다.
[Fresh독립검토](SDSS_SOURCE_NULL_20261018/INDEPENDENT_REVIEW.md)는
PASS_SOURCE_ONLY_FINITE_DIAGNOSTIC이며 수리finding은 없었다. Reviewer가 설계한
저장결과 대조도 한 번 통과했고 source refit없이 누적41.027506327/600s다.

[Gaia working-covariance 상계 실험](GAIA_COVARIANCE_ENVELOPE_20261019/REPORT.md)은
기존16차원 normal/13차원 frame quotient를 재사용하고 원본1614173행을 한 번
streaming 처리했다. 새fit/RHS/holdout/TAP/radio계산은 없다. 알려진 source내부
2×2 working공분산을 고정하고 source간 임의PSD상관을 허용한 class에서
13좌표 각각의 최대분산을 계산했다. 예를 들어 E1_x의 sqrt분산은 block-diagonal
reference .318651809에서 relaxed maximum280.823190μas/yr다. 이는 실제Gaia오차
추정이나 confidence가 아니다. 최대값13개가 한 공분산에서 동시에 달성된다는
뜻도 아니며 실제frame 제약과의 양립성/누락systematics/bias는 UNKNOWN이다.
원본hash/XML/행수/0requiredrejection을 검증했고 reference상대차최대5.07e-15,
frame소거잔차6.17e-15였다. 두 초기실패(thread제한, fixture의NumPybyteorder)를
보존하고 각각의 명시적 제한수리 후12controls를 통과했다. 한 번의20.284s 실제
pass와PNG/PDF/report까지 누적31.560857996/120s다.
[Fresh독립검토](GAIA_COVARIANCE_ENVELOPE_20261019/INDEPENDENT_REVIEW.md)는
PASS_CONDITIONAL_WORKING_MARGINAL_ENVELOPE, blockingfinding/추가계산 없이
종료했다. 원래K03와17/42/여섯논문NOT_READY는 유지한다.

[Radio scalar-marginal 상계](RADIO_SCALAR_COVARIANCE_ENVELOPE_20261019/REPORT.md)는
기존713행/8개 RA해석·working-rho 추정기의 full16차원 cache를 재사용했다.
미지의 source내·source간 상관을 자유롭게 허용하되 발표된 scalar 주변분산을
고정한 PSD class에서104좌표별 최대분산을 실제 계산했다. sqrt최대분산 범위는
1.95361–8.95381μas/yr, 기존working sigma 대비 비는16.3578–62.6936이다.
두 RA해석과 네rho를 전부 유지했으며 작은 값을 선호해 convention을 선택하지
않았다. 이것은 Gaia의 고정2×2-block class와 다른 조건부 문제다. 14controls,
한 번의 실제713행/8map계산과PNG/PDF/report까지 누적13.487808667/60s다.
최대VN잔차6.28e-15, 전체map잔차4.83e-14, working분산 상대차2.11e-14다.
실제frame/NNR 제약과의 양립성·bias·coverage·물리curl은 UNKNOWN이며
104최대값의 공동달성이나 Loewner상계를 뜻하지 않는다.
[Fresh독립검토](RADIO_SCALAR_COVARIANCE_ENVELOPE_20261019/INDEPENDENT_REVIEW.md)는
PASS_CONDITIONAL_SCALAR_MARGINAL_ENVELOPE, blocking/수리finding 및 추가수치계산
없이 종료했다. Original17/42/K03HOLD/여섯논문NOT_READY는 변하지 않았다.

검토는 각 coherent increment의 separate read-only Astra task에서 수행했고,
구체 결함은 source-binding, grid boundary, intake/execution/language 구분이다.
수정 경위·첫 실패·과거 bytes는 각 REVIEW/RESULT_INITIAL/receipt에 남긴다.
요청 model/effort와 실제 관측은 구분하며, observed runtime은 UNKNOWN이다.

## Fatal blockers

원래의 직접 입력 장벽8개와 정확한 재개 payload는 다음과 같다.

|노드|필요한 실제 payload / 조건|이번에 대신 쓰지 않은 것|
|---|---|---|
|S02|같은observer/congruence에서선택된광학자료를운동학sector에연결하는response와오차/flowremainder|apparentfield를physicalx/Q/F/G로이름변경|
|S04|그공통상태에대해정당한selectedlikelihood또는coverage가정당화된outerinterval|D07reference-radius를confidencelevel로취급|
|L03|동일release/processing/selection을통과한jointsplit signal+noise+foreground law와statistic-specificcoverage|nominalID4개를독립하늘로계수,부재HMsignal을noise로대체|
|H02|fullparenttargeting/detection/qualitylaw및방향calibration/velocityjointlaw또는정당한bound|GBT628cohort조건부확률을전체CF4선택가중치로사용|
|V03|source/IC/units/frame가정해진기존global-historynumericresponse와normal↔mattertransport|같은localendpoint열을globaltilt열로복제|
|B02|기존계산된physicalT/E/Ball-matlas,IC/모드/단위/frame/equivalence검사입력|T-only지도,코드,영상,posteriorchain을편광atlas로간주|
|K03|동일잠재상태의nonradialoptical/frame/clockkernel와NNR공동오차/보정transfer또는정당한bound|관측VSH를물질vorticity/4accel로자동변환|
|K04|실제CF4apparentSTF의common-frame광학→운동학사상과선택/보정/finite-zbudget|apparentσ를geometryshear로승격|

추가 source 단위 재개 조건: EDD의 실제 공개 SN-ID/PGC/group contributor export
(현 경로는 human-verification challenge; 우회하지 않음), grouped64-grid의
원점/간격/성분방향 contract다. SH0ES47열은 이제 명시적 primary reanalysis와
공식행렬을 연결한 composite parameter/host순서 및 named support를 검증했다.
이를 공식 Riess dictionary나 CF4 공동 calibration law라고 부르지 않는다.
이는 이번에 확보한 전체Pantheon covariance나 수정CF4++128-grid를 부정하지 않는다.

10월19일 fresh read-only `/root/remaining_executable_frontier`(requested
Astra/xhigh, observed UNKNOWN)는 원래 acceptance와 D07/SDSS/Gaia/D04/D08의
실제 결과 범위를 다시 대조했다. 현재 진행 중인 radio 조건부 상계 이후에는
검사한 입력으로 새로 실행할 수 있는 원래노드 관련 과학작업을 확인하지 못했다.
이는 모든 공개자료의 부재 증명이 아니라, 완료된 취득·대체경로 조사와 현재
payload에 한정한 판단이다. 더 많은 nominal noise ID/beam채널/임의 covariance
민감도는 위의 미공급 관측법칙·물리응답을 결정하지 않는다. V03는 정당한
analytic physical response도 허용하고 B02는 검증된 physical subset도 허용하지만,
이번 입력에서 그 source-bound 후보를 확보하지 못했다. 위8개 payload 중 하나,
실제 EDD contributor export, 또는 grouped64 producer geometry/estimator가
도착하면 해당 lane을 즉시 재개한다. 자료 부재를 새로운 강한 no-go로 부르지 않는다.

## Major concerns

Parent는 다음 **여섯 관점**으로 위 판단을 통합했다. 이는 여섯 agent를
새로 실행했다는 주장이 아니다. 각 수치의 별도 독립 검토는 각 하위 폴더에 있다.

|관점|구체 질문과 현재 판정|
|---|---|
|상대론/우주론|observer3-acceleration,4-acceleration,물질congruence,광학누적응답을구별했는가? 물리mapping미공급→HOLD|
|통계추론|공통하늘/중첩창/같은calibration과selection을독립으로곱했는가? 아니오; workingnorm/OOF/holdout는coverage가아님|
|수치해석|실제경계/단위/순서/잔차/조건수/LP정밀도가검사됐는가? 좁은검증PASS;9개tminendpointorder는미해결정밀도한계보존|
|소프트웨어/재현|기존venv/원본/실패/구체commands가있는가? 예;원래전체testcollection/LaTexbuild는이번NOT_RUN|
|주장편집|다운로드·test·review·push가과학노드완료로승격됐는가? 아니오;MIOposterior/native/family검출주장없음|
|family/equivalence|verifiedpolarizedatlas와null/family-equivalence가있는가? 아니오;legacyT를대체물로쓰지않음|

## Minor concerns

Python/수치패키지는 기존 `.venv`를 사용했다. 전체 repository test suite,
optional solver toolchains, 모든 원고의 LaTex/bibliography buildability는 이번
증거가 아니므로 주장하지 않는다. 기존 historical/frozen failures도 닫지 않았다.

## Novelty and scope

HI/TF/CF4/Pantheon/Gaia/Planck catalogues와 calibration은 원저자의 기여다.
유한 regression quotient/gauge/LP는 알려진 방법이며 새 GR/no-go theorem으로
포장하지 않는다. 이번 증분은 repo의 정확한 실제source/공통처리/연결·의존성에
대한 계산이다. 저널 기여로 삼으려면 기존논문 대비 유용성과 오차/선택법칙의
정당화를 보여야 한다. 같은 결과를 여섯 개 핵심논문으로 중복 출판하지 않는다.

공개 대체 경로도 확인했다: official BIANCHI v1.1의실제Ttestfiles를획득했고,
[BIANCHI2 pinned tree](https://github.com/astro-informatics/bianchi2/tree/1a53b167b0c5402abd15553c17522e0812ed54e8)는
cosmological-constant temperature package/test만 보여준다. 기존AniCLASS notebook/
Zenodochains/movies의불충분판정은재사용했다. [ABSolve원논문](https://doi.org/10.1093/mnras/stw1731)의
편광모형설명/그림이새로운직렬화all-mpayload는아니다. 확인한공개경로에서
필수payload를얻지못했다는판정이며, 어디에도없다는보편적no-go는아니다.

10월19일의 별도 read-only Astra 조사에서는 세 primary source bundle을 직접
열어 추가 공개 경로를 검사했다. [Saadeh1605.07178v2 source](https://arxiv.org/src/1605.07178v2)는
TeX/bbl/figure.pdf 세 파일, [Planck1502.01593v2 source](https://arxiv.org/src/1502.01593v2)는
편광 Epol/Bpol의 렌더링 PDF를 포함하지만 독립적인 수치 map/alm 파일은
확인되지 않았다. [Pontzen0706.2075v2 source](https://arxiv.org/src/0706.2075v2)의
13개 파일도 EPS 여섯 개와 원고/서지/스타일/로그이며 sampled complex coefficient나
history array는 없었다. Planck의 해당 수치 원본과 temperature-matching
scale factor는 여전히 필요하다. 초기편광0이라는 물리가정은 최종E/B=0을
뜻하지 않으며 PDF그림을 atlas로 대체하지 않는다. APS supplement는 접근이
제한되어 내용 미확인이다. 이는 검사한 세 bundle/release surface에 한정한
결과이지 모든공개자료의 부재 증명이 아니다. 새로운 solver/ODE/상류코드 실행은 없다.

## Required validation

코드·결과·그림·보고서의increment별독립검토와targeted수리closeout를유지한다.
통합 affected suite는 **72tests,5subtests PASS /17.66s**였다(새7lane+
기존 acquisition tests). 원래streamkernel의좁은4tests도별도PASS다.
D07의metadata/language최종수리후 unchanged11tests/metadataassertions와같은reviewer의
closeout도PASS다.97LP/원래generator/rawledger/NPZ를재실행하거나변경하지않았다.

후속물리payload가실제로오면위직접노드의원래acceptance만검증한다.
그때만frontier를갱신하고새runnable원래노드로이동한다. 파일획득/형식PASS는
그physicalgate의대체물이아니다.

## Downclaims required

모든신규계산은DIAGNOSTIC_ONLY/CONDITIONAL이다. D07absolutecalibrationη와
latentapparentθ의식별자유도는선언한모형안의결과이며,물리적shear/tilt/no-go의
관측인증이아니다. reference-radius,formalσ,pointwiseRMS를calibratedconfidence로
읽지않는다. 미측정편광·공분산·부정의sector는0으로채우지않는다.

## Stronger claims allowed

출처가있는행수/조인/처리계수/조건부유한대수결과와실제로닫힌코드결함은
그정확한범위에서보고할수있다. 과학주장등급이나저널readiness의승격은없다.

## Merge/release decision

공개 SDSS v1.1.0 FP mock의 paired truth 실험은 실제 실행과 독립검토를
마쳤다. 원본의 초기 분할 전송은 프로세스 소실을 확인해2952790016bytes를
보존한 채 복구했다.
Parent root의 첫 복구는 API버전 문자열1.1.0/v1.1.0 검사 결함으로 bulk0회에서
멈췄다. 실제원본size/MD5는변함없고, 기존marker/실패/cumulative예산을 유지하는
단일 continuation phase는 short-body에서 멈춰 보존했으며, 별도로 승인/검토한
16요청 suffix phase가 기존 prefix를 재사용해 전체원본검증을 마쳤다. 실패/배정/
누적예산은 리셋하지 않았다.2048개는256box×8observer다. 이를2048독립
우주로 세지 않는다. 전체size/MD5와 실제header/단위를 검증한 뒤64 distinct
box의Y0만 고정 선택해 angular error를 검사했다. 다운로드/준비를 H02 공동법칙
검증으로 세지 않으며 fullCF4/TF/6dF 결합 mock과 joint calibration law는 필요하다.

2025–2026새 primary 대안도 제한된 범위에서 확인했다.
[Nusser–Tully2608.14265v1](https://arxiv.org/html/2608.14265v1)의2%SDSS공통보정은
예시적 민감도이지 empirical joint covariance/bound가 아니며 새자료를 배포하지 않는다.
[Wang2604.08314v1](https://arxiv.org/html/2604.08314v1)은 mock자료를 요청 경로로,
[Duangchan2507.22236v3](https://arxiv.org/html/2507.22236v3)은 independent distance-modulus
오차와 향후 selection/intercalibration 개선을 기술한다. 이번 검색에서 source-qualified
공개jointCF4payload를 찾지 못했다는 한정판정이지 어디에도없다는 no-go가 아니다.

검토된code/tests/results/plots/report만현재draftPR#561에commit/push한다.
Mainmerge/journalsubmission은별도owner지시없이는하지않는다.

기존완료17: E0,E1,E2,E3,X01,X02,X03,S01,L01,L02,H01,H03,V01,V02,B01,K01,K02.
직접미완료8: S02,S04,L03,H02,V03,B02,K03,K04.
그의존성대기17: S03,S05,S06,L04,L05,L06,H04,H05,H06,V04,V05,V06,
B03,B04,B05,K05,K06. 총25미완료이며원래기준을낮추지않았다.

실제새payload/보정법칙이없을때무한히같은진단을반복하지않는다.
[RESUME.md](RESUME.md)의현재HEAD/실제결과/정확한재개명령을따른다.
