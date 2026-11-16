> 준비 시점: R58 계산 전의 문헌·설계 부록. 현재 수치 결과와 출판 판정은 PUBLICATION_REVIEW_KO.md 및 BENCHMARK_CONTRACT.json을 우선한다.

# 출판성·선행연구 비교와 적대적 benchmark 계약

기준일: 2026-11-17 (KST). 이 파일은 외부 원전에 대한 독립 검토다. 저장소 R54의 5개 view 정의와 R7–R9의 robust union/max-p/Bonferroni 선행 구현은 저장소 census 담당자가 전달한 상태 요약으로 받아 아래 비교에 반영했다. 원본 전체에 대한 독립 재감사로 표시하지 않는다. 이 검토자는 수치 성과나 데이터 분석을 실행했다고 주장하지 않는다. 출처별 원문 확인 수준·버전·남은 연결은 LITERATURE_SOURCES.json에 기록했다.

## 핵심 판정

벡터·텐서 표현, low-\(\ell\) 형태 통계, 방향별 Hubble의 운동학적 분해, boost와 intrinsic dipole 분리, Bianchi template fitting은 이미 각각 상당한 선행연구가 있다. 저장소 R54도 5개 view 자체를 reporting convention으로 판정했고, 현재 benchmark는 WIN 0 / TIE 2 / NOT_COMPARABLE 7이라고 전달되었다. 수렴 목표는 **기존 5변수 구조를 정확히 보존한 tensor-valued carrier가 실제 보유 데이터에서 어느 물리 조합을 식별하며, 과거 압축에서 버린 상관이 결론을 얼마나 바꾸는지 입증하는 것**이다.

논문 가치가 생길 수 있는 기여는 (a) 기존 스칼라 압축에서 사라진 방향·cross-channel 정보를 보존하는 명시적 정리와 검산, (b) 같은 하늘·mask·noise·MC를 쓴 공정 비교에서 보정된 검정력/coverage 개선, (c) local boost와 물리적 anisotropy의 구별 가능한 조합 및 식별 불능 방향을 함께 산출하는 likelihood, (d) 파라미터별 기여와 nuisance 민감도를 해석 가능하게 분해하는 통계적 결과다. 이는 아직 프로젝트에서 검증해야 할 연구 목표이며 달성 사실이 아니다.

## R54에서 R58로의 수렴 설계: CF4 polar+STF joint carrier

Census가 전달한 현재 5개 view는 (1) precision \((F,t)\) carrier, (2) 선언된 body \(K_0\)의 gauge \(Q\), (3) named-law tail \(\Pi\), (4) 방향별 occupancy의 조건부 bound, (5) depth 간 transport \(G_F\)다. “5변수”를 임의의 다섯 요약통계나 다섯 물리성분으로 재정의하지 않는다. precision \(F\)와 occupancy view의 명칭이 겹치므로 구현에서는 서로 다른 field를 쓰고 기존 API와 대응표를 둔다.

현재 가장 가까운 과제는 이미 보유한 CF4의 32-row 관측 요약을 polar 12-row와 STF 20-row로 나눠 처리한 R54 결과에서 **두 block 사이 covariance와 공통 zero-point nuisance를 보존한 하나의 carrier**로 재계산하는 것이다. 데이터 row identity, depth ordering, component basis, covariance source와 zero-point prescription은 원본 계약에서 읽어야 한다.

\[
y=X\vartheta+B\eta+\epsilon,\quad \epsilon\sim N(0,C),\qquad
F=X^TC^{-1}X,\quad t=X^TC^{-1}y .
\]

이 식의 \(\vartheta\) 차원은 실제 design matrix로 정한다. 32개 row를 32개 독립 물리 파라미터로 가정하지 않는다. 공통 nuisance를 무제약 profile하는 경우

\[
P=C^{-1}-C^{-1}B(B^TC^{-1}B)^{+}B^TC^{-1},\quad
F_{\rm prof}=X^TPX,\quad t_{\rm prof}=X^TPy
\]

를 사용하되 pseudoinverse 허용 조건, nuisance rank, projected residual normalization을 실제 계약으로 고정한다. Gaussian prior nuisance는 이 projection 대신 \(C_{\rm eff}=C+B\Lambda B^T\)와 해당 평균 이동·정규화를 사용한다. 두 방법은 서로 다른 통계모형이므로 결과를 섞지 않는다.

반드시 비교할 세 모델은 full \(C\), cross-block 항을 0으로 둔 split \(C_{\rm split}\), 공통 zero-point nuisance를 포함한 full \(C\)다. split covariance가 실제 covariance와 다르면 split 추정량의 표본 covariance는 nominal \(F_{\rm split}^{-1}\)와 일반적으로 다르다. \(W=C_{\rm split}^{-1}\), \(A=(X^TWX)^{-1}X^TW\)일 때 실제 covariance는 \(ACA^T\)다. 이 sandwich covariance를 계산하면 보유 covariance 아래 split 방법의 coverage 손실을 직접 예측하고 작은 Gaussian 모의실험으로 검산할 수 있다. Gaussian 모의실험은 관측 데이터 결과와 별도 표기한다.

출판 대상으로 삼을 양은 새 이름의 통계량이 아니라 다음 실제 값이다.

- polar–STF cross-correlation의 singular spectrum과 어느 물리 조합이 영향을 받는지.
- full/split/nuisance 모델 사이 best fit 이동과 confidence ellipsoid의 고유축·부피 변화.
- \(K_0\), \(Q\), \(\Pi\), directional occupancy, \(G_F\)가 이 변화의 어느 부분을 분해하는지.
- 선택한 catalogue와 redshift/depth 범위에서 “anisotropy 유의성”이 zero-point 처방에 얼마나 의존하는지.
- R7–R9의 기존 robust union envelope로 모든 선언 모델 아래 유지되는 방향·상한과 그렇지 않은 방향.

**필수 대조군:** 동일 Gaussian \(X,C,B\)를 사용한 직접 GLS/likelihood. \((F,t)\) carrier에서 얻은 해·likelihood ratio가 이에 수치적으로 일치해야 한다. 이 TIE는 구현 검증이며 통계적 우월 성과가 아니다. 기존 split 방법과 차이가 관측되더라도 그것은 cross-covariance 보존의 정량적 응용 결과다. “full covariance 방법을 발명했다”는 문구는 쓰지 않는다.

**Robust-envelope 기여의 위치:** true model이 선언된 모델 집합 안에 있고 각 \(C_m\)가 올바르게 보정된 confidence set이면 \(\cup_m C_m\)은 적어도 그 coverage를 가진다. 각 모델 null이 union composite null을 이루는 경우 \(p_{\rm robust}=\max_m p_m\)의 보수성도 기존 성질이다. 이는 R7–R9를 재사용하는 근거이며 새 정리로 세지 않는다. model set 밖의 misspecification에 대한 robustness는 별도 스트레스 실험에서만 주장한다. 집합 크기가 클수록 trivial/unbounded envelope가 될 수 있으므로 그 경우를 명시적으로 결과로 보존한다.

**현재 평가:** R54의 WIN 0 / TIE 2 / NOT_COMPARABLE 7로는 타 방법보다 실질적으로 우수하다는 주장이 지지되지 않는다. 이번의 bounded application이 관측 카탈로그에서 결론을 바꾸는 구체적 보정 취약성, 보수적으로 유지되는 물리적 제약, 또는 사용 가능한 명확한 calibration 진단을 산출하면 응용·방법론 논문 경로가 생긴다. effect가 미미하면 그 결과를 정직하게 보고하고 기존 약한 novelty 판정을 유지한다.

## 관측량과 운동학 연결

시간 단위 운동학을 사용해 \(H,\Theta,\sigma_{ab}\)는 \({\rm s}^{-1}\), 물리적 가속도 \(A_a\)는 \({\rm m\,s}^{-2}\), \(\beta_a=v_a/c\)는 무차원으로 고정한다. 관측 방향 \(n^a\)는 관측자에서 광원으로 향한다. Heinesen의 \(c=1\), \(k^a=E(u^a-e^a)\) convention을 복원하면

\[
{\cal H}(\hat n)=\frac{\Theta}{3}+\sigma_{ab}n^an^b-\frac{A_an^a}{c},
\qquad
d_L(z,\hat n)=\frac{cz}{{\cal H}_o(\hat n)}+O(z^2).
\]

이 식은 문헌으로 뒷받침되는 국소 관계다 [L03]. 유한 redshift의 전역 \(H(z,\hat n)\)를 자동으로 제공하지 않는다. \(O(z^2)\) 이상에서는 운동학의 시간·공간 미분과 curvature가 추가되어 \((\sigma,\omega,A,\beta)\)의 순간값만으로 닫히지 않는다. 기존 데이터에서 사용 가능한 redshift 범위에 대해 truncation 또는 기존 forward model을 고정해야 한다.

대칭 수축 \(n^an^b\omega_{ab}=0\) 때문에 이 국소 1차 기울기에는 vorticity가 직접 나타나지 않는다. 이것은 해당 관측 연산자의 정확한 null direction이며, 모든 관측량에서 vorticity를 측정할 수 없다는 정리가 아니다. higher-order 거리 계수와 전파·편광·모형의 진화식에는 vorticity 관련 항이 들어갈 수 있다. local agent는 이 차이를 설계와 결과 서술에 유지해야 한다.

CMB quadrupole을 STF 행렬 \(Q_{ab}\)로 표현하는 것과 shear \(\sigma_{ab}\)를 같은 회전 representation으로 표현하는 것은 자연스럽다. 그러나 \(Q_{ab}=\sigma_{ab}\)로 놓을 수는 없다. 관측 \(a_{\ell m}\)에서 운동학을 추정하려면 모형·시간 이력·선택효과를 포함한 transfer map

\[
a_{\ell m}^{\rm det}
 = {\cal T}_{\ell m}[\sigma(t),\omega(t),A(t),\beta_{\rm global}(t);M]
\]

또는 근방 선형화 \(a_{\ell m}^{\rm det}=R_{\ell m,A}\theta_A\)가 필요하다. \({\cal T}\), \(R\)이 구현되지 않은 성분을 숫자 priors만 붙여 측정된 물리량으로 출력하면 안 된다.

## 여섯 주제의 독립적인 수렴 방향

| 주제 | 기존 기여와 겹침 | 기존 데이터에서 끝낼 관측 결과 | 다음 최소 연구 |
|---|---|---|---|
| low-\(\ell\) morphology→physical observable | multipole vectors [L01], BipoSH [L02]가 회전 공변 형태·공분산을 이미 제공 | 방향·진폭·교차-\(\ell\) 통계의 보정된 관측 값과 null p-value; 구현된 transfer의 identifiable 조합 | 동일 \(a_{\ell m}\)에서 스칼라 5변수·텐서 5변수·MV·BipoSH를 비교하고 lost-direction 반례를 구성 |
| dipole anomaly | dipole/aberration/Doppler 분리 [L05,L06] | 이미 보유한 dipole 및 coupling 자료가 지원하는 조건부 residual vector 또는 상한 | conversion artifact·mask/noise leakage·공유 covariance를 포함하고 dipolar-lensing 가정을 명시 |
| beyond-FLRW kinematics | 일반 cosmography [L03] | \(\Theta,\sigma,A\) 중 actual design matrix rank가 지지하는 조합 | STF 5성분+벡터 3성분의 단위·방향 contract, singular-value/identifiability 보고 |
| anisotropy/Bianchi 분류 | near-isotropic I/V/VII0/VIIh shear modes [L07] | local tensor shape와 지정된 Bianchi template family의 상대 likelihood | local eigenvalue taxonomy와 Bianchi Lie-algebra type을 구분; 구조상수·동역학 제약을 모형 label에 고정 |
| \(H(z,\hat n)\) | Hubble quadrupole와 deceleration dipole fits [L03,L10] | 기존 SNe/거리 catalog가 있으면 방향 및 redshift bin 계수·covariance; 없으면 CMB-only 결과로 종료 | catalog가 실제 존재하는지 먼저 확인; 각 frame와 correction convention을 고정하고 직접 STF regression과 비교 |
| local boost vs global tilt | 관측자 frame 변환 [L04], intrinsic dipole couplings [L05,L06] | 지정된 transfer model에서 분리 가능한 조합/상관·상한 | \(\beta_{\rm obs}\)와 \(\beta_{\rm global}\)를 별도 parameter block으로 두고 response column rank와 profile likelihood를 계산 |

“Bianchi class를 측정했다”는 주장은 spatial Lie algebra/curvature와 진화·광전파 template까지 사용한 모형 비교에 한한다. \(I_2={\rm tr}\sigma^2\), \(I_3={\rm tr}\sigma^3\)와 고유축은 local shear morphology를 분류한다. 같은 local STF tensor가 다른 전역 시공간에서 발생할 수 있다.

## Likelihood와 tensorized five-variable의 역할

관측 데이터를 \(d=(a_{\ell m},z_i,\hat n_i,\mu_i,\ldots)\), 기존 방법의 벡터·텐서 출력 전체를 \(S_5(d)\)라고 하자. likelihood는 \(L(\theta;d)=p(d\mid\theta)\), posterior는 \(p(\theta\mid d)\propto L(\theta;d)\pi(\theta)\)로 구분한다. \(S_5\)가 파라미터를 포함해 계산된다면 trial-parameter 의존성과 정규화까지 likelihood에 넣어야 한다.

보정된 summary likelihood의 최소 contract는

\[
p(S_5^{\rm obs}\mid\theta,\eta,M),\qquad
L_5(\theta)=\int p(S_5^{\rm obs}\mid\theta,\eta,M)\,\pi(\eta\mid M)\,d\eta
\]

이다. nuisance \(\eta\)는 mask/noise/foreground/calibration/frame·선택 효과 등 사용 데이터가 필요로 하는 항으로 제한한다. 같은 \(d\)에서 만든 low-\(\ell\) 통계, BipoSH, dipole residual을 독립 확률처럼 곱하지 않는다. joint covariance 또는 하나의 일관된 generative model로 처리한다.

정확한 likelihood score는 [L09]의 의미에서 fiducial 근방의 Fisher 정보를 보존한다. 따라서 텐서 압축이 올바른 full likelihood보다 정보를 더 만든다고 주장하지 않는다. 다만 현재 스칼라 압축보다 더 많은 정보를 보존하거나, specified misspecification 아래 더 나은 coverage/robustness를 얻거나, 같은 정확도에서 계산비용을 줄일 수 있다.

Gaussian baseline \(d\sim N(\mu(\theta),C(\theta))\)의 score는
\[
t_A=\mu_{,A}^{T}C^{-1}(d-\mu)
+\frac12(d-\mu)^TC^{-1}C_{,A}C^{-1}(d-\mu)
-\frac12{\rm tr}(C^{-1}C_{,A}).
\]
마지막 trace는 data-independent이지만 parameter likelihood를 평가하거나 score 평균을 검사할 때 빼먹지 않는다. 이를 full-data 또는 retained-data score baseline으로 구현한다.

## 적대적 benchmark: local agent에 전달할 실행 규약

모든 비교는 **같은 retained data, 같은 simulations, 같은 train/calibration/evaluation split, 같은 nuisance 자유도, 같은 입력 수치정밀도**를 쓴다. 관측 값을 보고 축·basis·cut·band·가중치를 선택한 경우 동일 선택 절차를 각 null simulation에 반복해야 한다 [L08]. 새 관측 자료 다운로드는 이 계획의 prerequisite이 아니다.

1. **B0 full/score baseline:** 계산 가능한 작은 Gaussian 관측 모델에서 full likelihood 또는 exact score와 비교. Fisher generalized eigenvalues, posterior/interval coverage, bias, NLL, wall time를 기록. tensor method가 더 많은 Fisher 정보를 주면 covariance·finite-MC·잘못된 baseline을 먼저 조사.
2. **B1 scalar ablation:** legacy scalar \(x_c\)와 tensor/vector \(x\)를 동일 입력·규모에서 비교. 모든 방향·cross-block 정보 제거 ablation을 넣는다. 차이는 동일 null calibration 아래 검정력 또는 constrained-direction 수로 증명.
3. **B2 morphology baseline:** power \(C_\ell\), multipole-vector alignment/planarity, 필요한 BipoSH sector를 각각 비교. rotation은 data+mask+noise+templates를 함께 변환하는 좌표 공변성 검사와 고정 mask 아래 실제 신호방향 변화 실험을 구분.
4. **B3 direct kinematic regression:** 실제 existing distance catalog가 있으면 weighted GLS STF regression을 baseline으로 사용. selection·covariance·distance offset nuisance를 동일하게 둔다. tensor method의 posterior credible interval이 더 좁을 때 coverage 손상이 없는지 확인.
5. **B4 boost–tilt confusion:** boost-only, global-template-only, both, null 네 생성모형을 선언하고 confusion matrix/likelihood-ratio power를 기록. dipolar lensing나 foreground nuisance의 deliberate misspecification case 포함. 실제로 구현된 templates만 사용.
6. **B5 Bianchi model-family:** prior volume·orientation prior를 고정한 evidence/profile-likelihood 비교를 사용. near-isotropic template와 nonlinear model의 결과를 혼합하지 않는다. 구조상수가 없는 모형은 Bianchi type 추론으로 승격하지 않는다.
7. **B6 empirical calibration:** existing ensemble에서 independent holdout을 확보하거나 cross-fitting을 정확히 명시한다. Type-I binomial CI, 68/95% interval empirical coverage CI, global/conditional p-value를 별도 보고. \(N_{\rm MC}\)가 작으면 p-value resolution \(1/(N_{\rm MC}+1)\)을 출력한다.

자연스러운 success criterion은 특정 방법의 승리를 강제하는 것이 아니다. 보정·coverage가 유지된 상태에서 적어도 하나의 사전 지정 scientific target에 대해 tensor method가 scalar legacy보다 정보를 보존하고, 강한 외부 baseline 대비 추가적인 유효 이점 또는 정확한 동등성+해석·계산 이점을 보여야 한다. 개선이 없으면 equivalent/underperforming 결과와 원인을 논문 framing에 반영한다.

## 판정을 바꾸는 치명적 실패와 최소 교정

| 실패 | 분류 | 영향 | 최소 교정 |
|---|---|---|---|
| tensorization을 새 물리로 제시, transfer map 없음 | 이론/해석 | morphology를 kinematic measurement로 오인 | 실제 \(R_{\ell m,A}\) 또는 \({\cal T}\)를 구현한 범위만 물리 추정 |
| unknown \(\omega\) component에 first-order distance 데이터만 사용 | 식별성 | prior가 likelihood 제약처럼 출력 | design-matrix nullspace와 profile likelihood를 보고하고 unresolved block 보존 |
| global tilt와 observer boost를 같은 \(\beta\)로 fit | 이론/구현 | 물리 구분 소멸 | 두 frame 정의·성분·모형 response 분리 |
| 같은 맵의 여러 summary likelihood를 독립으로 곱함 | 통계/구현 | 정보 중복·과신 | joint covariance 또는 한 번만 사용한 generative likelihood |
| observer redshift만 보정하고 distance/direction 그대로 사용 | 구현/이론 | 가짜 dipole/octupole [L04] | complete frame transformation regression test |
| observed sky로 basis를 고르고 같은 MC로 calibration 평가 | 통계 | 선택 편향·낙관적 coverage | selection replay 또는 독립 holdout/cross-fitting |
| local STF eigenvalues를 Bianchi type로 출력 | 물리 해석 | 공간 구조·진화의 미식별성 누락 | local morphology와 model-family posterior 필드 분리 |

## 출처와 조사 범위

핵심 10개 source record를 `LITERATURE_SOURCES.json`에 넣었다. Exa 35개 요청 결과, SciSpace dipole-estimator 교차탐색, Parallel cosmography/Planck/boost 탐색 및 원문 추출을 사용했다. 원전에서 직접 확인한 식·가정과 그 프로젝트 적용에 남은 조건을 분리했다. English CMB/cosmography/Bianchi/information-compression 문헌의 bounded review이며 전체 문헌에 대한 신규성 증명은 아니다. 2025–2026에 나온 모든 신규 논문의 체계적 인용망 조사는 수행하지 않았다.

원전 링크: [L01](https://arxiv.org/abs/astro-ph/0310511v2), [L02](https://arxiv.org/abs/astro-ph/0501001v1), [L03](https://arxiv.org/abs/2010.06534v2), [L04](https://arxiv.org/abs/2312.09875v3), [L05](https://arxiv.org/abs/2011.08385v2), [L05 companion](https://arxiv.org/abs/2107.10846), [L06](https://arxiv.org/abs/1603.02664v2), [L07](https://arxiv.org/abs/1605.07178v2), [L08](https://www.aanda.org/articles/aa/full_html/2020/09/aa35201-19/aa35201-19.html), [L09](https://arxiv.org/abs/1712.00012v2), [L10](https://arxiv.org/abs/2212.13569v1).

