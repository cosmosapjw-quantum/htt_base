# HTT 이론·관측·통계 연구 루프 2: R1–R10

2026-10-15 KST, source HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54.
이전 완성 R/C 루프의 정확한 소스 및 부분입증 결과를 재사용했다.
실제 Planck FFP10 SMICA/Cosmicflows-4 자료를 샌드박스로 복사하지 않았다.

## R1–R3: 질문, 원전, 정의

A: 이전 loop에서 확인한 finite NSIDE64의 고차모드 완전 nuisance span을
실제 통계적 불확실성으로 처리할 방법이 있는가? 이미 보존한 300개
CMB+noise 쌍의 동일 하늘에서 source-fit L5/L12의 차이를
조건부 누출통계로 재사용한다. 실제 E2E 물리 null과 진짜 unboosted sky는
미인증이다.

B: 실제 CF4 방향 H/Q 분석의 기존 Q 차단이 어디서 발생하는가?
기존 PR179 q-cubic·method/selection/error/H nuisance와 독립성 의무를
유지하여 방향별 정보 결핍을 재매개화에 불변인 고유값으로 계량한다.
Q physical estimation 또는 등록 기준의 사후 변경은 하지 않는다.

원전: HTT Report A R3, 기존 GR optical image/first-jet inverse,
Planck 2018 results IV (2020, A&A 641 A4),
https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html;
Phipson & Smyth 2010 DOI 10.2202/1544-6115.1585;
Hemerik & Goeman 2018 DOI 10.1007/s11749-017-0571-1;
Heinesen JCAP 2021/05/008, Tully et al. ApJ 944,94 (2023),
Duangchan et al. A&A 2026 CF4 forward modeling.
문헌은 kernel/검정법의 배경이지 이 프로젝트의 E2E 물리 null 검증이 아니다.

## R4–R5: 구성적 이론

### A. 같은 하늘의 훈련-조건부 잔차 검정

동일 masking과 sky-ID를 가진 관측 32-vector를

  Y = Y_(fit L5), D = Y_(fit L12) - Y_(fit L5)

로 정의한다. D는 동일한 하늘을 다른 연산자로 분석한 값이므로
새로운 독립 하늘이나 독립 likelihood가 아니다.
분리된 training60 하늘에서 중심화 행렬 Yc,Dc에 대해

  B_lambda = (Dc.T Dc + lambda I)^(-1) Dc.T Yc,
  lambda = rho * tr(Dc.T Dc)/32, rho in {0.25,1,4}

를 적합한다. ridge 잔차의 covariance를
  C_R = 0.8 S_R + 0.2 tr(S_R) I/32
로 shrinkage하고
  R=(Y-mean_trainY) - (D-mean_trainD) B_lambda,
  T=R C_R^(-1) R.T
를 계산한다. baseline B=0도 하나의 고정 경쟁 변환이다.

같은 하늘의 두 mask x (baseline + 세 ridge) 총 8개 점수에 대해
training60에서 정한 중심/척도로 표준화한 뒤 하나의 max score를
구성한다. **정리:** 실제 하늘과 240개 full-joint mock 행이
training에 조건부 교환가능한 귀무법칙 아래에 있고 모두에
동일한 고정변환을 적용하면, ties를 포함하는

  p_rank = (1 + count_i[T_i >= T_obs]) / 241

는 superuniform하다. 이는 finite rank의 익숙한 정리이며
FFP10 모의 데이터가 실제 하늘의 물리적 교환가능 귀무법칙을
만족한다는 입증이 아니다. 예전 observed sky를 이미 사용해
방법을 선택한 history는 이 joint eight-choice maximum의 범위 밖이다.

모집단 joint Gaussian에서 진짜 조건부 covariance는
  C_(Y|D)=C_YY-C_YD C_DD^(-1) C_DY.
학습 표본이 적고 ridge/shrinkage를 사용하는 현재 모델의
잔차 covariance는 이 Schur complement와 같지 않다.
Wolfram 정확대수로 scalar ridge residual와 simple
regularized Schur의 비동치를 확인했다.

이전의 masked local boost 접선 J5,J12에 대하여 위의
학습 결과 B를 고정하면 새 score의 응답은

  J_R = J5 - B.T (J12 - J5),
  F_beta= J_R.T C_R^(-1) J_R

이다. 이는 이미 관측된 source surrogate를 가상적으로
추가 boost시켰을 때의 감도이며 실제 속도/전단/global tilt posterior는 아니다.

### B. CF4 Q 방향별 Fisher 정보 budget

기존 PR179 q 원시 가중 Gram을 Graw=Q.T W Q,
고정 nuisance (method, z, reported eDM, sky-density, H,
z^2 n)을 제거한 Gram을 Gret=Qperp.T W Qperp라 둔다.

  eig_rel = eig( Graw^(-1/2) Gret Graw^(-1/2) ).

이는 양의 정부호 원시 Gram 하에서 가역 Q 좌표변환에
불변인 worst-direction retained information을 제공한다.
0 <= eig_rel <= 1 이며, 기존 PR179의
min(eig Gret)/min(eig Graw)라는 다른 metric을
소급 대체하지 않는다. 이상적인 독립 정보가 생긴다면
등록된 기존 Q-cubic floor 값 tau=0.05를 참고한
eigenvalue 바닥 맞춤 구성은

  Nideal = (tau I - diag(eig_rel))_+

이다. 이것은 예측된 실제 measurement/source가 아니며,
성분별 canonical eigen-lift의 비음수 정보 요건이다.
관측 채널이 실제로 이 Gram을 제공하려면 별도 physical
response와 joint selection/calibration law가 필요하다.

## R6–R8: 실제 계산 및 적대적 해석

Planck에서 같은 300 CMB+noise pair를 60/240로 분리,
두 mask와 네 모델 8-choice 공동 최대 순위는

  (1+138)/241 = 139/241 = 0.5767634855.

이는 새로운 physical Planck p가 아니다. IID 240 reference
exceedances의 95% marginal CP는 [0.50977,0.63835]이며
실현된 finite p-rank 자체의 interval이 아니다.

핵심적으로 조건부 32x32 선형 ridge 누출 회귀는
240개 독립 simulation-heldout sky의 저차 계수 MSE를
**개선하지 못했다**. rho=.25의 MSE 증가는
mask0.5 +12.20% (paired-bootstrap 95% +10.05~14.41%),
mask0.8 +12.77% (+10.52~15.07%).
rho=1은 +5.6~5.8%, rho=4는 +2.1%였다.
따라서 이 stage에서 회귀를 좋은 Planck decontamination
방법으로 추천하면 안 된다.
기존 simulated sky law와 실제 source mismatch 때문에
원인이 finite-sample overfitting 하나뿐이라고 증명된 것은 아니다.

동일 관측 source-surrogate의 reference-beta Fisher tangent
sqrt(beta.T F_beta beta)는 약 0.0215~0.0284이며
검출 SNR·source identity를 뜻하지 않는다.

CF4 원시 38,053개 그룹 가운데 기존 PR179 선택된
35,549개의 5-fold 결과에서 등록 H_ONLY 유지,
Q-cubic retained ratio 약 .00834~.00974.
새 generalized weakest relative information 약
.00230~.00288. 가상 tau=.05 지향 정보 trace
약 .1286~.1295. 즉 부족한 Q 방향을 정확히 가리켰으나
새 independent 데이터 제공자가 없어 Q gate는 여전히 HOLD이다.

## R9–R10: 정식화와 연구의 다음 물리 입력

코드/근거:
- htt/obsstat/paired_highmode_control.py
- htt/obsstat/cf4_q_information_budget.py
- scripts/run_htt_paired_highmode_stat_20261015.py
- scripts/run_htt_cf4_q_information_budget_20261015.py
- loop2/results/cmb_paired_highmode_v2
- loop2/results/cf4_q_budget_v1

실질적으로 해결한 것은 same-sky 누출의 train-only
조건부 통계 경로, 공동 8-choice 유효성의 조건부 정리,
실제 모의표본의 out-of-sample 예측 불이득 판정,
그리고 CF4 Q 식별성 부족을 반례와 정보 고유값으로
계량한 부분이다. native Bianchi transfer, 실제 Planck
source/simulation law와 CF4 selection/calibration·독립
q response가 없는 물리적 blocker는 유지한다.
새 no-go의 journal-level 선취권·범용성 판정은 하지 않는다.

### Wolfram 국소 정확 대수 재검증

하나의 Gaussian Y,H (분산 a,b, 공분산 c)에서
모집단 ridge coefficient B=c/(b+lambda)의 잔차분산은

  V_ridge=a-2c^2/(b+lambda)+b c^2/(b+lambda)^2
         =a-c^2*(b+2 lambda)/(b+lambda)^2.

이상적 Schur 잔차분산 V_opt=a-c^2/b와 차이는

  V_ridge - V_opt =
       c^2 lambda^2/[b (b+lambda)^2] >= 0

이고, lambda 미분은 2 c^2 lambda/(b+lambda)^3 >=0.
Wolfram Language의 가정 a>0,b>0,c^2<ab,lambda>=0에서
위 세 식을 정확 계산했다. 이것은 모집단의 최적 회귀 대비
ridge 손실의 한정 정리이다. 실제 heldout MSE가 baseline보다
커진 현상을 이 계산 하나로 일반화하거나 완전히 설명할 수는 없다.
