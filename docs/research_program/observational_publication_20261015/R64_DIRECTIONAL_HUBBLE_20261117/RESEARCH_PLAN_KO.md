# P3 논문 계획 — CF4 source-dependent radial 정보 회복과 거리 팽창률의 실제 분해능

기준일: 2026-11-17. 이 문서는 R64 관측 실행과 R8 augmentation을 반영한 논문 계획이다. 현재 투고 상태는 NOT_READY_TO_SUBMIT이다. 독립 최종심사와 scoped release의 실제 상태는 VALIDATION.md 및 REVIEW/final_review.json에 기록한다.

근거: DESIGN.md, THEORY.md, REVIEW/r64_history.md, REVIEW/r64_literature.md, scripts/r64의 실행 코드와 RESULTS/INTERPRETATION_SUMMARY.json이다. 아래 “42 fits, 62 tests”는 저장된 실제 실행 기록을 집계한 것이며 문서 작성 중 새 분석을 반복한 것이 아니다.

## 확정할 논문의 중심

이번에 실제로 풀린 문제는 **36개 압축 행에서 생긴 radial 미분의 구조적 null을, 이미 보유한 source-dependent correlated rows로 제거한 것**이다. L05의 method32 또는 sky36 요약행과 기존 full36을 joint covariance로 결합하면, 선정한 모든 68/72행 실험에서 J3의39열 finite mean family가 rank39로 회복된다. 이39열은 coherent V3와 네 Legendre 차수의 angular9개씩을 합친 파라미터다. 68행 실험에서는24개 method-angular nuisance를 profile한 뒤에도39열 rank가 유지된다.

이것은 추가 독립 은하를 얻은 결과가 아니라, 기존 catalogue에서 압축으로 버린 정보를 다시 사용한 결과다. 따라서 “CF4로는 미분을 원천적으로 식별할 수 없다” 또는 “추가 관측행 확보 전에는 rank 문제를 해결할 수 없다”는 서술은 철회한다. 앞선 초안의 최소 추가행 작업은 이번 R8에서 구체적으로 해결됐다.

동시에 rank 회복은 높은 미분 정밀도를 보장하지 않는다. J3의 H_D ratio 및 q_D confidence image는 이미 구현·저장됐지만, 선택한 grid의 상당 부분에서 D=1−B eta_z의 양성을95% joint region으로 인증하지 못한다. 더 중요한 관측 결과는 method rows를 복원하면 기존36행이 드러내지 못한 common-field 평균족의 부적합성이 나타나고, 그 정도와 method-angular nuisance의 효과가 operator에 따라 달라진다는 것이다.

**권장 중심 문장:** “보유한 source-dependent 요약량을 joint covariance와 함께 회복하면 거리장의 고차 radial mean을 식별할 수 있지만, 물리적으로 해석할 거리 미분의 정밀도와 common-field 적합성은 별개의 문제이며 관측 방법에 민감하다.”

잠정 제목:
“Source-dependent radial information and the resolution of directional distance expansion in Cosmicflows-4”

## 실제 실험과 수치 결과

35,970 selected groups, 관측 z_CMB 범위0.0100035872–0.0999991801, ICRS/J2000 sourceward 방향을 사용했다. full36은 네 창의 [monopole, polar3, STF5]다. initial7operators×J1/J2/J3=21 fits와 augmentation7families×J1/J2/J3=21 fits가 저장돼 총42 fits다. 실제 검증 기록은62 tests다. 새 independent source 수0, 새 PV pair sum0이다.

모든 수치는 white noise와 고정 Planck18 linear-PV body covariance를 채택한 working law 아래의 결과다. empirical shared-calibration covariance 및 실제 selection law를 새로 확보했다는 뜻은 아니다. J가 바뀌어도 eta는 실제 z_i에서 source-integrate한 뒤 O에 통과시키며, 창 중심에 다항식을 맞추지 않았다.

### 최초36행: 추가 radial angular mean의 근거가 없었다

아래 p_rad는 coherent V, 상수 angular field 및 자유 monopole history에 더해 higher-j dipole/STF가 필요한지 묻는 조건부 nested-null p다. 물리적 등방성 또는 static anisotropy 부재를 검정하는 값이 아니다.

| 최초 operator | J1 rank /21 | J1 adequacy p | J1 p_rad | J2 rank /30 | J2 adequacy p | J2 p_rad |
|---|---:|---:|---:|---:|---:|---:|
| log |21|.6601|.9335|30|.8433|.8261|
| log_mono |21|.4264|.9272|30|.6302|.7043|
| log_split |21|.8119|.4899|30|.8809|.6851|
| log_survey |21|.3837|.9482|30|.6364|.7019|
| log_mono_radial |20|.5120|.9426|29|.7929|.6518|
| log_mono_galactic |21|.3456|.7875|30|.4732|.6005|
| log_mono_error |21|.3129|.8910|30|.4791|.5678|

J1의 p_rad 범위는.4899–.9482, J2는.5678–.8261이며, simultaneous signed angular depth intervals에서0을 배제한 좌표는 없었다. J1 leave-one-window conditional prediction의 p는 각 operator 안에서 대략.228–.819 범위에 있었으나, overlapping-source 내부 예측이라는 해석을 유지한다.

최초36행의 J3는 전 operator에서 rank36/39이고 residual df0이다. 따라서 residual adequacy를 판정할 수 없었고, 저장된 nonlinear ingredient 검사는 비기준 H_D ratio162개와 q_D216개를 모두 INGREDIENT_UNIDENTIFIED로 분류했다. 이는 실제 원 catalogue 전체의 정보 한계가 아니라 이 압축 실험의 한계였다. log_mono_radial에서 J1/J2의 scalar radial null도 별도로 보존한다.

### source-dependent 행 복원: 모든 경우 J3 rank39를 회복했다

augmentation의 세68행 실험은 각각 log, log_mono, log_split의36행에 동일한 method32를 붙였다. sky72행 실험은 log36과 jk_no_equator36을 결합했다. 각 경우 shared rows와 cosmic/PV cross blocks를 유지했다. “+24”는 FP/SN/TF의 독립 angular8개씩을 상수 method offset으로 profile한 조건부 평균족이다. stochastic calibration prior가 아니다.

표의 세 숫자는 J1/J2/J3 순서다. field rank는 각각21/30/39로 모두 회복됐다. +24의 전체 mean rank는45/54/63이며68행 기준 residual df는23/14/5다.

| joint experiment / 평균족 | 관측 행수 | field rank J1/J2/J3 | adequacy p J1/J2/J3 | p_rad J1/J2/J3 |
|---|---:|---|---|---|
| log_method / common |68|21/30/39|.01382 / .01960 / .003716|.9021 / .5915 / .7956|
| log_method / +24 |68|21/30/39|.09865 / .1988 / .01619|.9257 / .5472 / .7804|
| mono_method / common |68|21/30/39|.005851 / .007642 / .003507|.9371 / .5752 / .5524|
| mono_method / +24 |68|21/30/39|.4385 / .5848 / .4043|.7791 / .5519 / .5927|
| split_method / common |68|21/30/39|.1115 / .09684 / .1147|.6815 / .7024 / .4662|
| split_method / +24 |68|21/30/39|.6928 / .6279 / .6151|.5749 / .7329 / .6775|
| log_sky / common |72|21/30/39|.07569 / .06470 / .05311|.9707 / .8439 / .7771|

이 표 전체를 보존한다. mono_method에서만 고른 좋은 nuisance 결과를 전 실험의 결론으로 쓰지 않는다. log_method+24의 J3 adequacy는.01619로 여전히 낮고, split_method common은 처음부터 다른 양상을 보인다. 일곱 family는 동일 source의 상관된 표현이므로 독립적인 일곱 재현 또는 일곱 likelihood의 곱이 아니다.

특히 최초 log_mono36의 adequacy .4264/.6302와 mono_method68 common의 .005851/.007642를 함께 제시하면, source-dependent 정보가 common-field 평균족을 시험하는 데 왜 필요한지 드러난다. 더 flexible한 J3만 추가해도 이 부적합성은 사라지지 않는다. 반면 method-angular24 nuisance를 허용하면 mono_method의 adequacy는.4385/.5848/.4043으로 바뀐다. 이는 “calibration error가 원인이라고 확인”한 결과가 아니라, 해당 관측 law에서 **method-dependent mean freedom이 결과 해석에 실질적**이라는 관측이다.

같은68행 안에서 common vs +24의 nested mean 비교는 다음과 같다. 모든 p는 명시한 고정 covariance와 finite mean의 nominal 값이며, multiple-model 탐색을 보정한 물리적 discovery p가 아니다.

| experiment | Delta chi2 J1/J2/J3 | df | nominal p J1/J2/J3 |
|---|---|---:|---|
| log_method |38.7841 /39.8869 /39.5648|24|.02877 /.02199 /.02380|
| mono_method |51.5946 /50.0836 /48.5991|24|.0008834 /.001382 /.002126|
| split_method |39.9152 /37.9715 /34.7989|24|.02184 /.03491 /.07144|

### rank 회복과 nonlinear 정밀도는 별개다

지정한54방향과 z=.025,.04,.06,.08에서 평가했다. ratio는 pivot .04의 자명한 동일 적색편이 항을 제외해162개, q_D는216개다. 아래 숫자는 저장된95% common-region support-box에서 DOMAIN_NOT_CERTIFIED인 항목 수다. 이는 독립 sky cell 수, 검출 수 또는 하늘 면적 비율이 아니다.

| joint family | H_D ratio domain 미인증 J1/J2/J3 [총162] | q_D domain 미인증 J1/J2/J3 [총216] |
|---|---|---|
| log_method common |0 /0 /73|0 /0 /73|
| log_method +24 |0 /0 /76|0 /0 /76|
| mono_method common |0 /0 /93|0 /0 /93|
| mono_method +24 |0 /0 /109|0 /0 /109|
| split_method common |0 /16 /119|0 /16 /122|
| split_method +24 |0 /14 /131|0 /14 /139|
| log_sky common |0 /3 /162|0 /3 /162|

표의 나머지 항목은 저장된 certificate에서 OK다. “OK”는 해당 support enclosure가 유한하고 지정한 denominator 양성을 보인다는 뜻이지, 구간이 좁거나 물리적으로 유의한 진화가 검출됐다는 뜻이 아니다. 예를 들어 mono_method J3 common의 z=.08,+x에서는 D의95% support가[-.86394,3.87265], +24에서는[-.90895,3.94628]이라서 점값이 존재해도 ratio/q_D의 유한 enclosing interval을 인증하지 못했다.

이 support-box 구간은 같은 rank-r Gaussian confidence region의 보수적인 image다. sharp profile-likelihood bound가 아니다. DOMAIN_NOT_CERTIFIED만으로 정확한 nonlinear image가 반드시 unbounded라고 증명되지는 않는다. 더 sharp한 image 최적화는 실제 논문 target을 바꿀 때만 한 번의 유한 보강으로 검토한다. 지금은 실패 상태와 그 원인을 정확히 보고하면 현재 실험은 완결된다.

## 정의·보정·물리 해석의 경계

D_M=D_L/(1+z), H_D=c/D_M,z이며 fixed observed ray를 따른다. 거리와 속도의 수치 단위를 고정해 정의한 eta_repo를 사용할 때 eta_relative=eta_repo−ln[H_ref,0/(km/s/Mpc)]를 유지한다. flat reference에서
   H_D/H_ref=exp(eta_relative)/(1−B eta_z),
   B=H_ref chi/c
가 성립한다. 물리적 redshift propagation rate는 source congruence에 대해
   Hcal=Theta/3+sigma_nn−A·n/c
이다. finite H_W와 H_D, Hcal은 서로 다른 estimand다.

z에 무관한 source angular calibration은 uncompressed field에서 H_D를 방향별 상수로 배율 변환하므로 same-ray radial H_D ratio와 q_D에 소거된다. 실제 estimator는 nuisance span에 표현된 angular field만 소거한다. R64의 l<=2 represented shift와 l=3 leakage witness는 이 차이를 실제 source response에서 보여준다. radial calibration·opacity evolution·population selection은 상수 angular quotient로 없어지지 않는다.

보고한 optical/background H_D는 g(z)n·V의 declared coherent-velocity nuisance를 뺀 다항식 부분의 image다. coherent V를 포함한 전체 fitted distance field와 구분한다. R63 published-q correction은 같은 관측 실험의 결정론적 chart transport이며 새로운 observer velocity measurement가 아니다. 광학 focusing, endpoint frame와 거리 처리의 closure가 없는 상태에서는 H_D를 임의 시공간의 Hcal이나 물리적 가속도로 바꾸지 않는다.

g(z)n·V는 일차 속도 응답의 tangent template이며, 이번 자유계수 Gaussian fit에서는 |g_i n_i·V|≪1 또는 고차 응답 나머지의 작은 크기를 강제하거나 인증하지 않았다. 식별된 확장 fit의 최대 ||V||는5788.052km/s, ||V||/(c z_min)≈1.93이다. 이는 source별 실제 radial response의 측정값이 아니라 응답 유효범위를 따로 확인해야 함을 보여주는 척도다. 초기 singular J3의21168.238km/s 대표값에는 gauge 자유도도 있다. 현재 다항식 image를 물리적으로 검증된 PV deboost로 해석하지 않으며, physical-map package에서 실제 response-domain과 비선형 나머지를 함께 제한한다.

## H02 실제 joins·holdout을 연결하는 위치

H02의 raw table2/3/4 join과 whole-group hash split을 source genealogy의 출발점으로 쓴다. 같은 group의 raw method presence/count, galaxy PGC, upstream shared calibration을 유지한다. pooled FP/TF/SN/OTHER labels는 순수하고 독립적인 tracer 측정의 목록이 아니다.

이미 있는 내부 heldout 결과는 아래처럼 그대로 보존한다.

| released-method contrast | train/test groups | constant/angular test WRMS [mag] |
|---|---:|---:|
| SNIA–FP |149/33|.303796/.306344|
| SNIA–TF |162/47|.324443/.357259|
| FP–TF |529/109|.475214/.471794|

앞의 두 조합은 angular 복잡성의 예측 개선을 보여주지 않고, 마지막 조합에는 작은 개선이 있다. 모두 이미 upstream 공동 calibration을 거친 released distances의 downstream overfit 진단이다. 이번 augmented method rows 역시 독립 tracer holdout이 아니다. H02 결과와 R64 leave-one-window를 새로운 외부 확인으로 다시 세지 않는다.

현재 augmentation이 실제 관측 작업을 전혀 하지 않은 단계로 되돌아가서도 안 된다. source-matched response, full shared covariance, 기존 method/sky rows를 통한 rank 회복과 common-field adequacy의 변화는 **이번에 완료한 실제 결과**다. 남은 작업은 그 결과를 만든 method dependence의 관측적 성격과 물리적 의미를 구분하는 다음 네 package다.

## 다음 관측 package 1 — 실제 공유 calibration covariance와 selection response

**입력.** H02 method-resolved joins, group·object 중복, 공유 HI/photometry/band 자료, anchor와 survey zero-point posterior/오차, 실제 magnitude·linewidth·quality cut·mask·completeness. 이미 계산한 within-release inclusion fraction은 최초 detection/targeting 확률로 부르지 않는다.

**실행 산출물.** source별 measurement genealogy 표, 실제 제공된 calibration Jacobian J_gamma와 Sigma_gamma에 따른 C_cal=J_gamma Sigma_gamma J_gamma^T, 선택·보정·grouping을 통과한 mean response 및 covariance. 이를 기존68/72행 operator에 통과시켜 지금의 fixed-C 결과와 target shift·uncertainty를 비교한다. 현재 +24는 자유 deterministic nuisance이며 이 stochastic calibration covariance를 측정한 것이 아님을 유지한다.

**종료 기준.** primary target과 선택한 method decomposition에 대해 실제 확보한 covariance 성분·selection law의 영향을 계산하고, 미확보 입력은 정확히 한정한다. 현재 common-field vs method-dependent 결과를 그 입력이 설명하는지, 남는 차이가 있는지 결정한다. 모든 가능한 catalogue systematic 해결을 요구하지 않는다. 설명되면 관측모형을 고정하고 다음 package로 이동하며, 남으면 그 residual target을 distinct tracer 검증 대상으로 삼는다.

## 다음 관측 package 2 — 이미 회복한 rank에서 실제 미분 정밀도로

**이미 완료.** 기존 L05 correlated rows로 J3 rank39를 전 case에서 회복했고, q_D confidence image도 저장했다. 최소 추가행을 찾아야 rank를 풀 수 있다는 과제는 종료한다.

**남은 질문.** J3 도함수의 약한 방향과 denominator uncertainty를 줄이려면 어떤 실제 정밀도·redshift 지원·velocity 정보가 필요한가? G theta를 선택한 eta_z, eta_zz 및 denominator target으로 고정하고, 이미 full-rank인 설계의 작은 singular directions와 target variance를 사용한다. 이제 목표는 nullity0을 다시 확인하는 것이 아니라 named target의 정밀도다.

**입력.** 기존 source별 적색편이·method uncertainty·source response 및 실제 확보 가능한 보강 후보 하나를 쓴다. 후보는 같은 raw source의 새 radial weighting으로 손실 정보를 더 회수하거나, 부족한 적색편이·각도·tracer 영역의 더 정밀한 거리 자료를 얻거나, 같은 congruence와 frame에서 coherent velocity/history를 측정하는 독립 anchor다. 기존 CMB redshift correction은 독립 velocity anchor가 아니다.

**유한 출력·종료 기준.** 한 개 target set과 요구 precision/domain margin을 데이터 수집 전에 수치로 고정한다. 후보가 그 요구를 만족시키는 데 필요한 측정 수·오차·지원 범위를 계산한 design table 한 개를 만든다. 실현 가능한 최솟값이 나오면 관측 제안으로 넘기고, 후보가 요구를 만족하지 못하면 필요한 오차/지원의 격차를 적어 닫는다. “추가행이면 해결”이라는 일반 약속을 하지 않는다. fixed low-J 가정으로 얻은 작은 오차와 high-J에서 실제로 확보한 C1/C2 정보를 구분한다.

## 다음 관측 package 3 — overlap-aware distinct-tracer 예측

**입력.** H02 source genealogy에 따라 primary 학습 tracer와 다른 평가 tracer 하나를 고정한다. 동일 object/group, upstream anchor, 원시 photometry와 common PV field의 공유를 표시한다. 현재 augmented method summaries가 이미 사용한 source를 독립 holdout으로 재사용하지 않도록 학습·평가 분할과 사용 이력을 묶는다.

**실행 산출물.** 실제 source-level X_T,X_H,C_TT,C_TH,C_HH와 shared-calibration nuisance, 그리고 사전 고정한 radial angular target의 conditional innovation. Gaussian linear law에서는 C_HT를 남긴
   y_H−C_HT C_TT^{-1}y_T
   −(X_H−C_HT C_TT^{-1}X_T) theta_hat_T
와 Schur noise 및 parameter-estimation variance를 사용한다. source overlap을 없애도 correlated PV와 upstream calibration까지 없어지는 것은 아니다.

**종료 기준.** 한 개 distinct-tracer prediction의 식별·잔차·joint uncertainty를 실제 계산한다. agreement면 외부 예측 근거로 보고하고, disagreement면 method/calibration/selection의 구체적인 차이를 package1의 residual과 대조한다. 이름이 다른 catalogue의 p-value를 곱하지 않는다. 기존 selected SN covariance는 후보지만 zHD integral/zHEL prefactor와 CF4 overlap을 실제로 확인한 뒤 쓴다.

## 다음 관측 package 4 — 물리적 optics closure 또는 독립 H observable

거리 정의 결과의 완결과 물리적 Hcal 해석을 분리한다. 두 경로 중 실제 입력이 있는 **하나**를 고른다.

- optical closure: 특정 smooth congruence·metric/optical family, endpoint velocity·redshift chart, Ricci focusing·optical shear를 고정하고 Hcal→D_L→동일 관측 operator의 response를 계산한다.
- independent observable: cosmic chronometer, redshift drift 또는 radial BAO 중 실제 sky/redshift overlap과 covariance가 적합한 하나를 선택하고, source clock/ruler·동기화·population 조건과 실제 측정 estimand를 확인한다.

**유한 출력·종료 기준.** 선택한 경로의 response equation, 실제 overlap, joint covariance와 한 개 distance–expansion consistency result를 산출한다. 그것이 없으면 P3는 distance-defined 결과로 닫고 Hcal 판정을 unresolved로 남긴다. Milne/curved-FLRW 및 opacity 예제는 H_D와 Hcal의 해석 경계이며 새로운 universal no-go가 아니다.

## 문헌과의 공정한 비교 package

이 비교는 네 관측 package와 별개로 원고에 필요한 제한된 재현·대조 작업이다. 신규성은 성분 방법의 최초성이 아니라 실제 source-dependent 정보 회복, compression이 가렸던 mean adequacy, calibration/PV 조건과 미분 분해능의 차이를 정량화한 **이번 데이터 결과**에 둔다.

| 선행 분석 | 공통으로 맞출 대상 | 반드시 보존할 차이 |
|---|---|---|
| Kalbouneh2510.02510v2 | 자연로그/상용로그 eta 변환, shell monopole, 공통 z/source와 angular response | 축대칭 CC coefficients와 일반 signed STF5, CF4 독립오차와 이번 body covariance |
| Vicente2607.07821 | full2l+1 DOF, STF convention, mask·pixel/radial response, signal/noise law | maxima 정렬과 complete-vector alignment, l=3 정보는 이번 full36에 없음 |
| Salzano2512.02526v2 | log-HL 통계, CMB/PV chart, 대안적인 mu 또는 z selection, intrinsic scatter | ratio-type apparent H와 derivative H_D, evidence와 Gaussian tail |
| GaPP/Seikel1204.2832v2 | 같은 거리 likelihood, 함수/도함수 공분산, reference·kernel·length scale | GP smoothness prior·posterior band와 fixed-C confidence image, rank 회복과 실질 precision |

유한 비교는 공통 표본/estimand가 가능한 subset 하나와 두 source signal family로 정한다: 매끄러운 저차 radial angular eta, 그리고 coherent velocity 또는 radial calibration이 비슷한 거리 신호를 만드는 family다. 실제 operator를 통과시킨 target bias·분산·derivative/domain resolution을 비교한다. 원 논문의 mask·selection·covariance를 확보하지 못한 경우 exact reproduction으로 부르지 않고 matched-estimand comparison 범위를 기록한다. published sigma의 순위표는 만들지 않는다.

## 본문·그림과 종료 판정

본문은 (1)Hcal/H_D/H_W 정의, (2)source identity와36→68/72 관측 연산자, (3)finite law·calibration quotient·confidence image, (4)최초21fits와augmentation21fits의 전체 결과, (5)문헌 대조와 method dependence, (6)남은 관측 입력과 물리 해석 순서로 쓴다.

메인 그림 두 개면 중심을 전달할 수 있다.
1. 같은 catalogue에서36행 J3 rank36/39가 기존 source-dependent rows를 쓰면39/39가 되는 정보 회복, 그리고 모든 joint family의 adequacy 변화.
2. signed depth path와 H_D/q_D의 domain 인증·구간 폭을 함께 보여주는 그림. 높은 rank를 정밀한 물리적 H 측정으로 혼동하지 않게 한다.

전 operator를 표/부록에 보존하며, 사후로 좋은 방법만 primary로 채택하지 않는다. 단일 비교 예시로 mono_method를 설명할 경우 log_method·split_method·log_sky의 다른 adequacy와 domain 결과도 바로 제시한다. +24 nuisance의 fit 개선을 causal calibration 발견이라고 부르지 않는다.

**현재 과학적 판정.** 최초36행의 저차 실험에서 추가 radial angular mean의 근거는 없었다. 그러나 source-dependent 행을 회복하면 고차 mean은 식별되고, 일부 common-field 모델의 adequacy가 낮아지며 method dependence가 드러난다. H_D/q_D의 nonlinear precision은 rank 회복과 달리 여전히 제한적이다. 이 세 사실을 함께 쓸 수 있는 finite observational result가 이번 R64의 산출물이다.

**투고 판정.** 물리적 Hubble anisotropy 또는 genuine acceleration evolution 검출로 투고할 근거는 아직 없다. 현재 원고를 완성할 수 있는 경로는 source-dependent radial 정보·mean adequacy·미분 분해능 결과를 중심으로 쓰고, 네 package의 실제 관측 입력 상태를 분명히 하는 것이다. P3의 원래 과학 gate를 새 이름으로 완료 처리하지 않으며, R64 selected loop의 종료는 P3 submission-ready와 구분한다.

## 근거 파일 identity와 재개점

native 기준 파일:
docs/research_program/observational_publication_20261015/R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/INTERPRETATION_SUMMARY.json

augmentation RESULT SHA256:
c9a68a7e79de910185757acd43ca0e5a91e8d36a1c2a818a184804962de5160b

augmentation CARRIERS SHA256:
c960201a48879d26e687393d11499474cba360394712e9cb72117a547b867836

재사용 L05 cache SHA256:
f0acb8e1be3f09d212303967ff7678178fd59364ec0131ab12ba3f5149879cae

initial36 y/cov parity는 augmented blocks에서 약3e-15 /2.2e-19 이하였고, 원래 method dipole mean/SD와의 기록된 최대오차는0이다. cache의 전체 operator byte fingerprint는 일치하지 않으며, 기록은 pinned input/code/cache와 선택한 log-eta rows의 numerical parity를 재사용 근거로 한다. 논문에서 cache byte identity와 operator semantic/numerical compatibility를 혼동하지 않는다.

가장 가까운 다음 실행은 package1의 실제 source-calibration genealogy/covariance를 확보하는 일이다. rank 회복을 다시 수행하거나 새 미분불가능 정리를 만드는 일로 돌아가지 않는다. 이번 루프에서 자동 후속 연구나 local coding-agent용 프롬프트를 생성하지 않는다.
