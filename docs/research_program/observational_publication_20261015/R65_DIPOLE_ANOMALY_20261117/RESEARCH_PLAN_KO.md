# P4 보완 논문 계획 — NVSS 횡방향 쌍극자의 flux 선택 의존성

작성일: 2026-11-17. 기준 commit은 `d76ef3a4e9b33c4703a02647b3aa850004d04253`이며,
이 문서는 R65의 실제 결과를 반영한 유한 논문 계획이다. 현재 판정은
**P4 companion으로 통합, 단독 투고는 NOT_READY_TO_SUBMIT**이다. 새로운 적합,
검정, 문헌조사 또는 독립 심사를 이 작성 단계에서 수행하지 않았다.

판정의 수치 기준은 [INTERPRETATION_SUMMARY.json](RESULTS/INTERPRETATION_SUMMARY.json)이다.
실험의 사전 범위는 [DESIGN.md](DESIGN.md), 계산식은 [THEORY.md](THEORY.md),
구현은 repository root 기준 `htt/htt/htt/infer/r65_count_quotient.py`,
`htt/htt/htt/infer/r65_racs.py`, `htt/htt/htt/infer/r65_overlap.py`,
`scripts/r65/run_r65_counts.py`, `scripts/r65/run_r65_integrated_flux.py`,
`scripts/r65/summarize_r65.py`에 있다. 최근접 선행연구의 근거는
[문헌 검토](REVIEW/r65_literature.md), 추가 integrated-flux 입력의 의미는
[source 검토](REVIEW/r65_nvss_flux_source.md)에 둔다. R8 extension은
[완료 receipt](RESULTS/PROVIDER_NVSS_EXECUTION.json)와 위 갱신된 수치 기준에
따라 반영하며 사전에 등록한 raw-peak 결과와 구분한다.
원래 42개 연구 노드와 P4 acceptance는 그대로
유지한다. 아래 후속 작업은 R65가 제공할 수 있는 증거를 한정하는 실행계획이며,
그 acceptance를 대체하거나 자동 통과시키는 새 심사체계가 아니다.

## 1. 논문 이름과 한 개의 중심 주장

가제는 **「NVSS 횡방향 쌍극자의 flux 선택 의존성: 동일 source 공분산을 보존한
조건부 분석」**, 영문은 *Flux-selection dependence of the transverse NVSS dipole
with shared-source covariance*로
한다. RACS 결과는 공개 사후분포를 운반한 보조 비교로 넣는다. 현재 자료에서
“cosmic dipole anomaly의 해결”, “새 속도 측정”, “global tilt 검출”을 제목에
넣을 근거는 없다.

중심 주장은 다음으로 고정한다.

> 같은 공개 NVSS component catalogue, 같은 sky mask와 같은 적위 조건부
> likelihood에서도 provider peak intensity와 integrated-component flux로
> 표본을 선택하면 횡방향 count dipole이 달라진다. 두 표본은 241,892개
> component를 공유하므로 그 차이의 불확실성은 marginal errors보다 훨씬 작으며,
> source-overlap covariance를 유지해야 관측된 선택 차이를 올바르게 평가할 수
> 있다. 이 차이는 사용한 flux 정의와 source 선택에 대한 실제 관측 결과다.

이 문장은 count 관측량과 그 선택 차이에 관한 결과다. 선택을 바꾸면 포함되는
population과 component 구성이 함께 변하므로 instrumental bias와 물리적
population 차이의 원인을 분리한 결과는 아니다. 그 차이의 작은 조건부 tail을
cosmic anomaly의 sigma로 변환하지 않는다. 각 선택 안에서 구간별 차이가 약하다는
결과, angular morphology의 영향과 beta/residual의 약한 분리 정밀도를 함께
제시한다. 물리적 속도 초과 주장은 실제 source-response와 LSS 조건이 추가된
경우에만 확장한다.

## 2. 이미 확보한 관측 결과와 정확한 질문

기준 NVSS 파일은 NRAO `CATALOG.FIT`이며 SHA256은
`a357a688dc7e43ae81ecbe465fdce216dfed678aee977780a626841eceb5bde4`다.
`PEAK INT`의 단위는 Jy/beam이다. 기본 표본은 HEALPix NSIDE64 pixel centre에
`dec>-37°`, `|b_Gal|>10°`를 적용한 33,000개 pixel, 185개 ring으로 구성된다.
세 peak 구간 `[20,40)`, `[40,80)`, `[80,infinity)` mJy/beam의 count는 각각
115,906, 65,260, 55,581개이며 합계는 **236,747개**다. 좌표는 ICRS/J2000,
방향은 sourceward, 계수 u는 무차원이다.

주 결과는 각 구간에 독립적인 ring 진폭과 네 개의 비축대칭 STF 사중극자 성분을
허용한 `base64_dipole_stf`이다. 공통 횡방향 count 계수와 그 공분산은

\[
 \widehat{\boldsymbol u}_{\perp}
 =(-0.01141191696,\;0.00685401707),\qquad
 C_{u}=10^{-6}
 \begin{pmatrix}
 10.42613777&-0.73334027\\
 -0.73334027&13.29011953
 \end{pmatrix}.
\]

따라서 marginal SD는 `(0.00322895305, 0.00364556162)`이다. 횡방향 크기
0.0133120과 방위 RA=149.0109°는 같은 signed vector의 파생량이며, 별도
관측이나 3차원 dipole의 amplitude/direction으로 세지 않는다.

| 논문에서 묻는 질문 | 실제 결과 | 허용되는 해석 |
|---|---|---|
| 세 구간이 하나의 횡방향 count vector를 공유하는가? | 독립 구간 대비 공통 vector LR=1.87090883, 차원차 4; Wilks 근사 p=0.75948685 | 이 조건부 모형에서 구간별 vector 차이를 요구하는 증거가 없다. 공통 기원을 입증한 것은 아니다. |
| 위 구간 차이 검정의 조건부 bootstrap은 어떠한가? | 512회, 초과 375회; `(375+1)/(512+1)=0.73294347`; 초과확률의 binomial MC 95% 구간 [0.69182831, 0.77030789] | 적합된 공통 vector와 구간별 STF nuisance 아래의 parametric conditional bootstrap이다. 합성귀무가설의 정확한 유한표본 검정이나 물리적 LSS 보정은 아니다. |
| 고정 CMB template가 여섯 개 독립 count 성분 전체를 설명하는가? | α=.75인 고정 peak-proxy response에서 omnibus 6-df p=0.17734308 | 여섯 개 성분의 전체 잔차를 묻는 이차적 조건부 질문이다. |
| shared-beta 모형 안에서 CMB beta를 고정하면 얼마나 나빠지는가? | 같은 α=.75에서 LR=7.15386850, 차원차 2, p=0.02796129 | shared-beta 모형 안의 두 제약을 묻는 별도 nested contrast다. 위 6-df 검정과 같은 p-value가 아니며 물리적 속도 초과의 유의도가 아니다. |
| count의 각도 형태를 확장하면 계수가 얼마나 바뀌는가? | dipole-only 대비 공통 vector 변화 `(-0.00077470549, +0.00091167053)` | 확장 모형 marginal SD의 약 `(-0.240,+0.250)`배다. 이 비율은 척도 진단이며 paired-shift significance가 아니다. |
| 각도 형태와 dipole 추정은 얼마나 결합되는가? | 기본 구간별 최대 절대 polar–STF 상관 약 0.207–0.217; STF를 자유롭게 할 때 dipole SD 증가 약 1.3–2.5% | 실제 mask에서 형태 nuisance가 정보를 일부 소모함을 정량화한다. 추가 형태가 독립적인 새 dipole 정보를 만들었다고 해석하지 않는다. |

기본 구간의 Pearson dispersion 진단은 약 1.047–1.099이다. 이 값을 하나의
분산 배율로 쓰는 것만으로 공간 상관이나 source multiplicity를 모델링했다고
말할 수 없다. 주 bootstrap은 설정한 conditional multinomial law를 검증 대상으로
삼으며, 실제 우주의 모든 stochastic fluctuation을 포함한 모형 적합성 판정이 아니다.

NSIDE32, Galactic latitude 20° cut, bright-region excision은 사전에 정한
sensitivity다. 이들에는 같은 source가 중복 포함되므로 독립 재현으로 세거나
p-value를 합치지 않는다. `clean64`의 bright cut은 peak proxy로 정의된 것으로,
published total-flux mask를 정확히 재현했다고 쓰지 않는다. 선택한 네 geometry와
두 angular model의 모든 결과를 같은 표에 보존하고 가장 작은 p-value만을
제목·초록에 올리지 않는다.

### 별도 R8 extension: 실제 integrated-flux 입력

공개 `Full_NVSS_combined_named.dat`는 `integrated_flux`와 `peak_flux`를 따로
제공한다. 공급자 계산은 전자를 mJy, 후자를 mJy/beam의 peak 값으로 사용한다.
NRAO의 raw/fitted/deconvolved 구분과 raw FITS에 대한 열 개 source의 직접
좌표 대응으로 현재 `PEAK INT`가 통합 flux를 숨겨 저장한 열이 아님을 확인했다.
예를 들어 한 대응 source의 raw peak는 4.077 mJy/beam, provider peak는
4.3 mJy/beam, integrated flux는 7.6 mJy다. 여기서 provider peak는 공개 표의
`peak_flux`를 뜻한다. Raw 값과의 차이는 알려진 survey bias correction과
rounding에 부합하지만, 공급자의 정확한 extraction/correction 절차를
확인하거나 재현한 것은 아니다. 이 field label로 그 절차가 검증됐다는 뜻을
부여하지 않는다.

따라서 “쓸 수 있는 integrated-flux 자료가 없다”는 차단 사유는 닫혔다.
원 FITS의 열 정의는 그대로 두고, 공급자의 고정 release·SHA와 의미를 가진
**새 입력·새 estimand**로 추가한다. integrated flux는 catalogue Gaussian
component의 통합량이며 여러 component를 한 물리적 radio galaxy로 묶었다는
보장은 아니다. 원 detection의 peak limit, spectral response 및 component
grouping도 이 입력 확보만으로 해결되지 않는다.

root가 채택한 유한 R8 refinement는 baseline NSIDE64 mask와 동일한
`[20,40),[40,80),[80,infinity)` 경계에서 provider peak와 integrated flux를
각각 dipole 및 dipole+STF로 적합하는 네 모형이다. provider 내 동일 source의
overlap을 이용한 Poisson-source sandwich covariance로 paired common-u 변화도
계산한다. 이때 bin 이동과 sample 입출입을 보존하고, 두 선택의 marginal
covariance를 독립인 것처럼 더하지 않는다. 여전히 conditional Poisson-source
working law이며 LSS covariance는 아니다.

R8에서는 hash가 검증된 140,767,191-byte provider 파일을 실제로 사용했다.
SHA256은 `52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e`다.
1,773,488개 row가 모두 finite·positive 조건을 만족하고 source name은 중복이 없다.
provider-peak 표본은 241,892개, integrated-flux 표본은 263,158개이며
241,892개가 공유되고 21,266개가 integrated 선택에서 추가된다. integrated 구간별
count는 `(127130,72123,63905)`다. 이 row identity는 원 raw FITS 전체와 동일하다는
주장이 아니다. paired 비교는 **provider 내부의 동일 rows**로 구성했다.

| 동일 provider의 dipole+STF 결과 | provider peak 선택 | integrated-component flux 선택 |
|---|---:|---:|
| 선택 단위 | mJy/beam | mJy |
| 공통 `u_x` | −0.01238603526 | −0.01403005936 |
| 공통 `u_y` | +0.00649807469 | +0.01202274652 |
| marginal SD `(u_x,u_y)` | (0.00319332190, 0.00360615325) | (0.00306430766, 0.00345625817) |
| transverse amplitude | 0.0139871 | 0.0184767 |
| transverse RA | 152.317° | 139.406° |

integrated minus provider peak의 차이는

\[
 \Delta\boldsymbol u=(-0.001644024105,\;0.005524671827),\qquad
 \operatorname{SD}_{\rm paired}(\Delta\boldsymbol u)
 =(0.000898362927,\;0.001029922589).
\]

같은 축의 두 추정값 사이 overlap 상관은 약 `(0.95961,0.95835)`다.
전체 paired covariance는

\[
 C_\Delta=10^{-6}\begin{pmatrix}
 0.8070559481&-0.05946172890\\
 -0.05946172890&1.0607405393
 \end{pmatrix}
 =C_{\rm int}+C_{\rm peak}-C_{{\rm int},{\rm peak}}
                         -C_{{\rm peak},{\rm int}}.
\]

source-Poisson influence covariance에서 paired Wald quadratic은
**30.98946896**, 자유도 2의 working-Gaussian tail은 **1.86518673×10⁻⁷**이다.
공유 source를 무시해 두 source-influence marginal covariance를 독립으로 더하면 SD는
약 `(0.0044257,0.00499515)`, quadratic은 1.31544, tail은 약 0.518로 바뀐다.
후자는 독립성을 잘못 넣은 계산이며 또 하나의 동등한 sensitivity 모형이 아니다.

paired 결과는 independent-source Poisson influence/sandwich의 large-sample
결과다. LSS와 같은 galaxy의 여러 component에 의한 상관은 아직 포함하지 않았다.
따라서 “cosmic 5σ”, “속도 anomaly의 5σ 검출”, “기기 오류를 확인”으로 번역할
수 없다. 현재의 실증 주장은 **flux 선택 정의가 같은 자료의 apparent count
dipole을 바꾸며, 공유 source의 covariance가 그 차이를 평가하는 데 결정적**이라는
것이다. 공유 covariance 공식 자체는 표준 통계이며, novelty는 이 실제 선택
차이와 그 관측적 크기에 한정한다.

integrated-flux 표본에서도 세 구간의 common-vector contrast는 LR≈2.683,
차원차 4, p=0.612187로 구간 차이를 요구하지 않는다. 고정 α=.75의 response는
`(3.37055573,3.56879567,4.04082231)`이며, 같은 working law의 fixed-CMB omnibus는
6-df p=0.0013169968, shared-beta 안의 fixed-CMB contrast는 2-df
p=0.000065858748이다. 이는 원 raw-peak의 p=0.17734/0.02796과 별개의 선택 결과다.
통합 flux 확보로 입력의 물리적 적합성이 개선되었지만, boundary SED·원래 peak
detection·component selection 및 LSS를 모두 인증한 것은 아니므로 두 값도
물리적 anomaly 유의도로 채택하지 않는다. 원 raw-peak bootstrap을 이 새로운
표본의 유한표본 보정이라고 사용하지 않는다.

## 3. 분리 정밀도와 정보 보존이 주는 실제 결론

물리적 분리 정밀도의 중심 예는 이제 실제 integrated-component flux carrier로
한다. 고정 α=.75 및 고정 response 아래에서

\[
 \boldsymbol u_b=k_b\boldsymbol\beta_{\perp}
                  +\boldsymbol a_{\perp},\qquad
 (k_1,k_2,k_3)=(3.37055573,3.56879567,4.04082231)
\]

를 local Gaussian carrier에 적합하면 parameter rank는 4다. 따라서 “세 구간으로
kinematic와 공통 residual은 원리적으로 절대 분리할 수 없다”는 주장은 이
실험에서 성립하지 않는다. 반면 같은 축의 beta–residual 상관은
`(-0.99718475,-0.99718552)`이며, beta의 SD는
`(0.01135668207,0.01281238538)`이다. 이를 `369.82 km/s / c`로 나눈 값은
각각 **9.20623, 10.38629**다.
즉 현재 source·response·count 정밀도에서는 그 분리가 실용적으로 약하다.
rank와 정밀도를 같이 제시해야 이 결과의 물리적 의미가 드러난다.
원 raw-peak carrier의 rank 4, 상관 약 −0.99625, beta SD 8.404/9.497 CMB-speed
units는 원래 조건부 비교로 남기며 integrated 결과와 혼동하지 않는다. 두 carrier
모두 local Gaussian·고정 response의 정밀도 진단이며 실제 물리 beta의 측정 또는
보편적 분리 불가능 정리는 아니다.

원 raw-peak 여덟 모형에서 같은 exposure, ring nuisance와 angular feature를 사용한 표준 one-step Fisher
score와 exact conditional MLE 사이의 최대 information distance는 0.03470385다.
현재 계산으로는 exact-likelihood라는 이름이나 다섯 관점의 사용이 표준 matched
score보다 정보를 더 얻었다는 주장을 뒷받침할 수 없다. 직접 conditional fit의
장점은 정의된 확률모형, nuisance 제거 및 likelihood ratio를 일관되게 계산한다는
점이며, 자료가 주지 않는 정보를 추가했다는 점이 아니다.

원 raw-peak 주 결과의 signed bin carrier에서 Wald quadratic은 17.1273252169이고, 공통 level을
남긴 flux-path 변환 뒤에도 17.1273252169로 보존된다. 변환된 covariance의
off-diagonal 항을 인위적으로 버리면 7.7839349246이 된다. 이 차이는 제안한
방법의 성능 개선이 아니라 **공분산을 버린 계산이 다른 실험을 만든다**는
관측적 예다. 따라서 논문의 정보 관련 결론은 “유지된 정보와 제거된 정보의
추적”으로 정하고 “새 invariant가 정보를 회복한다”로 쓰지 않는다.

새 source-definition 비교에는
`X=(u_peak,x,u_peak,y,u_int,x,u_int,y)`와 실제 same-source 4×4 sandwich covariance를
보존했다. 그 path는 `(u_peak, u_int-u_peak)`이며 시간이나 redshift 축이 아니다.
두 marginal count likelihood를 독립으로 곱한 exact joint likelihood는 만들지 않았다.
이 4D Gaussian influence carrier와 그 confidence support를 다섯 관점으로 운반한
것으로만 표시한다. full-vector zero와 selection difference zero는 서로 다른
귀무가설이므로 4D omnibus tail을 paired-selection 유의도 대신 사용하지 않는다.

## 4. RACS를 포함하는 방식

공개 `inference_products.zip` v1.0.0의 SHA256은
`143cdcf32d85479ee171c8d5bc5da814178dd7123024ba12e5b5d9f9b9c94fc7`다.
six weighted models를 재사용했고 새 RACS training이나 fit은 **0회**다.
원 chain의 Galactic direction과 `observer_speed=v/(369.82 km/s)`를 ICRS vector로
변환하고 원래 nested weights를 보존했다.

횡방향 CMB-parallel 비율은

\[
 R_{\parallel}
 =\frac{\boldsymbol v_{\perp}\cdot\boldsymbol v_{\rm CMB,\perp}}
 {|\boldsymbol v_{\rm CMB,\perp}|^2}
\]

로 정의한다. 분모는 전체 CMB speed가 아닌 같은 평면의 transverse speed에
맞춘다. 이것은 source posterior의 기하학적 pushforward다. **RACS likelihood에
임의의 적위 선택함수를 넣고 제거한 재적합이 아니다.** NVSS의 conditional
selection quotient와 이 RACS 기하학적 projection은 같은 좌표 성분을 보지만
같은 nuisance 모형을 공유하지 않는다.

| RACS source model | `R_parallel` median | weighted central 95% 구간 | thermal nuisance와의 상관 |
|---|---:|---:|---:|
| low3 fiducial | 3.73456188 | [2.26271431, 5.24633528] | −0.74123760 |
| mid1 fiducial | 3.98548128 | [1.97934245, 5.91900185] | −0.82222421 |

이 값은 원 source 모형·선택·prior 아래의 사후분포 결과다. 사후 tail probability를
frequentist p-value나 NVSS와 결합한 discovery significance로 변환하지 않는다.
parallel 비율만 비슷하다고 두 survey vector가 일치한다고 판단해서도 안 된다.
실제로 signed transverse perpendicular 성분의 median은 low3 약 −67.88 km/s,
mid1 약 −646.26 km/s이며, 각 95% 구간도 함께 보여 방향 차이를 보존한다.

no-clustering 및 no-temperature 결과는 source 모형이 어떤 요소에 민감한지 보여주는
ablation이다. 여섯 모형이 동등하게 적합성이 인증된 후보군인 것처럼 평균하거나,
그 min/max를 물리적 systematics confidence region으로 부르지 않는다. 원 논문이
보고한 thermal-model 필요성과 mid1 잔여 stripe 문제를 함께 적는다. 이 공개
posterior를 현재 조건에서 새 NVSS–RACS 공동 likelihood로 만들지 않는다.

## 5. 수학적 본문과 선행연구의 경계

본문의 수학은 새로운 일반 정리의 우선권 주장보다 이번 실험의 정의와 재현성을
담당한다. 필요한 내용은 네 묶음으로 충분하다.

1. `lambda_brp=A_br E_brp exp(u_b·n_perp,p + q_b·T_p)`에서 ring totals를
   조건화해 multinomial likelihood를 얻고, score와 PSD information, support에
   따른 rank를 제시한다. ring-constant z dipole과 축대칭 STF 성분이 제거됨을
   보인다. discrete pixel-centre 모형에서의 정확성과 finite-width/physical
   linear-density 모형에서의 근사 경계를 같이 적는다.
2. profile likelihood와 conditional likelihood의 동일성, nuisance-profile Fisher와
   ring-centred score의 동일성을 제시한다. physical density `1+d·n`은 원점에서는
   같은 tangent를 갖지만 비영 transverse dipole에서 `d_perp/(1+d_z z_r)`의
   second-order 의존성을 남긴다는 반례를 보존한다.
3. disjoint-bin signed carrier와 full covariance로 common vector, shared beta,
   beta+common residual을 구분한다. 첫 두 모형은 response가 변하면 비중첩이며,
   arbitrary likelihood 차이에 Wilks 자유도를 부여하지 않는다. finite-bin response의
   두 경계항과 peak/intensity qualification을 제시한다. provider의 중첩 선택에는
   실제 joint membership과 profiled influence를 사용해 full cross covariance와
   `C_delta=C_L+C_R-C_LR-C_RL`을 구성한다. 이는 새 정리가 아닌 실제 자료의 paired
   uncertainty 계산이며 independent-source Poisson 근사의 범위를 표시한다.
4. `(x,Q,Pi,F,G_F)`를 같은 관측 law의 pushforward로 연결한다. x는 signed
   vector/STF carrier, Q는 통계 reference body, Pi는 명명된 law의 tail, F는
   signed support, G_F는 공통 level과 full covariance를 유지한 flux-bin 또는
   source-definition path다. original bin 실험의 exact conditional likelihood와
   paired-selection의 approximate influence-Gaussian law를 구분한다.
   five views의 결합을 추가 likelihood로 곱하지 않는다.

Rubart & Schwarz (2013)는 이미 적위 sampling 문제에 강한 2D radio-dipole
추정과 flux-threshold 변화를 다뤘다. Siewert et al. (2021)은 mask와 direction
bias를 구체적으로 논의했다. Takeuchi (2026)의 일반 selection response와
Mittal & Lewis (2026)의 다중 flux 구간 공동 적합도 직접 선행연구다. 따라서
equatorial projection, declination resistance, finite-bin response, score/GLS,
Schur profiling 또는 five-view 명칭 자체를 novelty로 올리지 않는다.

현재의 새 실증 내용은 같은 provider에서 provider peak와 integrated flux를
선택했을 때의 **paired signed dipole 변화와 실제 overlap covariance**다.
각 선택 내부의 angular-morphology 변화, flux consistency와 beta/residual 분리 정밀도가
그 해석을 보조한다. 현대 RACS joint posterior의 방향·calibration 상관을 보존한
운반은 별도의 보조 비교로 둔다.
그 실증 차이가 독립 논문 분량과 의의를 갖는지는 source-qualified matched
comparison 뒤에 한 번 판단한다. 현시점의 판정은 기존 P4 프로그램 통합이다.

## 6. 원고 구성과 그림

서론은 “같은 NVSS 원천에서도 어떤 flux로 component를 선택했는지가 dipole에
얼마나 영향을 주는가?”라는 관측 질문으로 시작한다.
방법은 source identity·selection·조건부 likelihood와 paired covariance를 함께 정의하고,
결과는 NVSS raw-peak primary, provider peak/integrated의 직접 비교,
morphology/mask sensitivity, beta/residual precision, RACS 공개
posterior 순으로 쓴다. 논의에서는 물리 response와 LSS가 무엇을 바꿀 수 있는지
각각 해당 결과에 연결한다. 일반적인 cosmic-dipole 문헌 전체를 다시 서술하지 않는다.

| 그림/표 | 기존 산출물 또는 정해진 내용 | 독자가 확인할 결론 |
|---|---|---|
| 그림 1 | provider peak/integrated의 signed common vector와 별도 paired-difference ellipse; 실제 membership 이동 count | 큰 marginal ellipse의 시각적 중첩과 정밀한 paired difference가 양립함; 독립 covariance 오용의 영향을 한 panel로 표시 |
| 그림 2 | raw-peak의 `NVSS_SIGNED_FLUX_PATH`와 provider 두 선택의 대응 flux path | 각 선택 안의 구간 일관성과 선택 간 차이는 서로 다른 질문임; 단위 mJy/beam 대 mJy를 분리 |
| 그림 3 | `NVSS_MASK_MORPHOLOGY` 및 beta–common residual의 ellipse/precision 방향 | mask sensitivity와 실용적으로 약한 parameter 분리를 구분; 여러 mask를 독립 검출로 세지 않음 |
| 그림 4 | `RACS_TRANSVERSE_POSTERIOR`의 weighted intervals 및 fiducial의 parallel–thermal correlation panel | source-conditional 방향/thermal 결합; ablation은 시각적으로 구분하고 model averaging하지 않음 |
| 표 1 | source unit, mask, ring 수, 구간 count, covariance law, source identity | 실제 관측 실험의 재현 가능한 정의 |
| 표 2 | raw peak/provider peak/integrated별 common-vector test, 6-df CMB omnibus, 2-df shared-beta contrast; 별도 paired-selection 행 | 통계 질문·source 선택·자유도가 서로 다름을 명시 |
| 부록 | exact likelihood carrier, quadrupole convention, score comparison, path covariance equality, 검증 기록 | 표준 baseline과 동등한 정보 및 구현 정확성의 근거 |

현재 `RESULTS/`에는 원래 세 그림 `NVSS_SIGNED_FLUX_PATH`,
`NVSS_MASK_MORPHOLOGY`, `RACS_TRANSVERSE_POSTERIOR`와 새 provider paired 그림
`NVSS_PEAK_VS_INTEGRATED`가 모두 PNG/PDF로 생성되어 있다. 추가 precision/thermal
panel과 그림 안의 membership annotation은 계획된 항목이며 아직 생성하지 않았다.
이들은 저장된 full covariance와 weighted source samples로 만들 수 있어 새 fit이
필요하지 않다. 초록에는 대표 주 검정과 조건부 범위만 적고,
서로 다른 p-value와 posterior probability를 나열해 신뢰도를 부풀리지 않는다.

## 7. 유한 후속 작업: 입력·산출물·종료 결정

기본 경로는 현재 count 실험을 P4 companion 원고로 통합하는 것이다. 직접적인
다음 작업은 **실제 확보한 peak/integrated 선택 차이의 forward-selection·component
null을 한정하고, 같은 source·mask·law에서 기존 추정법과 하나의 matched comparison을
끝내는 것**이다. 물리적 속도 해석,
RACS selection-robust 재분석, 독립 tracer 결합은 주장 확장에 필요한 경우에만
아래 분기를 연다. 모든 가능한 systematic을 먼저 해결해야 현재 실험을 보존할
수 있다는 식의 무한 조건을 두지 않는다.

| 작업과 경로 | 실제 필요한 입력과 행동 | 실행 가능한 산출물 | 종료와 주장 결정 |
|---|---|---|---|
| A. 실제 선택 차이의 source/forward-null 한정 — 입력·네 모형·paired 계산 완료 | 현재 peak/integrated component rows와 원 detection의 peak limit, flux uncertainty, 실제 확보 가능한 size/SED·component-association 정보를 사용한다. 문서화된 하나의 component convention을 고정하고, 관측된 flux 경계와 selection을 그대로 적용한 forward model에서 기대되는 paired 변화 및 covariance를 계산한다. 원래 component 단위와 검증된 galaxy grouping을 비교할 수 있을 때만 한 번의 grouping contrast를 추가한다. 없는 SED/association 정보를 상수나 임의 묶음으로 대체하지 않는다. | 완료된 source receipt·네 모형·membership/covariance를 보존하고, `SELECTION_NULL_QUALIFICATION.json`에 response와 paired-null의 조건·추정/미확보 성분을 기록한다. 입력이 있는 경우에만 선택/그룹핑에 의한 예상 변화와 관측 Δu의 비교표를 만든다. | integrated 자료 부재라는 차단 사유는 종료했다. 현재 실제 선택 차이는 확정된 working-law 결과로 보존한다. finite forward/grouping 비교가 원인을 구분하지 못하면 instrumental과 population 기원을 분리하지 않는 주장으로 닫는다. 물리 velocity로 확장할 때는 boundary population SED와 peak-detection response를 추가로 요구한다. |
| B. 같은 자료의 표준 추정법 비교 — companion의 우선 비교 | A에서 확정한 한 표본과 primary mask를 사용한다. Rubart–Schwarz 2DCG와 실제 mask response를 갖는 count/Poisson 비교를 재현 가능한 범위로 구현한다. 같은 nuisance·support의 one-step score 검사는 이미 완료했으므로 반복하지 않는다. 비교 대상 간 estimator, mask correction, link, nuisance 차이를 명시한다. 작은 dipole, angular quadrupole, 지정한 RA calibration template의 유한 signal set을 같은 source law에 통과시킨다. | signed estimate·paired covariance, 주입 target bias/coverage 및 nuisance 조건별 정보차이를 담은 `MATCHED_ESTIMATOR_COMPARISON.json`과 한 표. 원 논문 전체 재현이 아니면 matched-subset 비교라고 적는다. | 동등하면 정보 우월성 주장을 닫고 현재 source-specific 결과를 P4 본문/부록에 통합한다. 실제 bias·calibration 취약성 차이가 확인되면 그 차이만 별도 핵심 결과로 승격한다. 작은 차이를 찾기 위해 mask/신호를 계속 늘리지 않는다. |
| C. Bin별 n(z), bias 및 cross-LSS — 물리 excess 주장에 필요 | 같은 flux·morphology source 선택에 대응하는 redshift/crossmatch 표본과 그 선택함수·가중치, angular counts/randoms와 bias 근거를 확보한다. 각 bin의 n_b(z), b_b(z) 및 uncertainty를 만들고 cross spectra `C_ell,ab`를 계산한다. 정한 multipole 범위의 fields를 실제 mask/estimator에 통과시킨다. aggregate C1 또는 다른 survey의 n(z)를 NVSS bin 입력으로 대체하지 않는다. | per-bin/cross-bin kernel 자료, `C_counts+LSS`의 전체 block matrix, 같은 primary target의 confidence/support와 두 CMB 질문 재평가표 | 실제 source-matched 입력이 확보되면 물리 excess 해석을 한 번 재평가한다. 확보되지 않으면 conditional count 논문에서 멈추고 sigma_LSS 공통-field sensitivity만 그 가정으로 표시한다. 물리 유의도는 제출하지 않는다. |
| D. RACS calibration 재적합 — selection-robust 공동 해석을 원할 때만 | 실제 source forward model·likelihood 또는 재현 가능한 training pipeline, RMS/temperature/declination 자료와 원래 prior를 확보한다. NVSS와 같은 종류의 nuisance 허용을 RACS 생성모형에 구현하고 simulation coverage를 확인한다. | source-trained calibration-refit posterior, 같은 projection의 전후 변화, nuisance recovery/coverage 기록 | 현재 목적이 공개 source-posterior의 비교이면 이 재적합은 하지 않아도 된다. “임의 적위 nuisance에 robust한 RACS” 또는 공동 물리 적합을 주장하려면 수행한다. 공개 samples만 있으면 그 주장을 보류하고 현 projection 결과로 닫는다. |
| E. 독립 tracer와 cross covariance — P4 물리적 결합 단계 | 독립 tracer의 signed vector/likelihood, response·selection과 동일 source/sky의 overlap 정보를 확보한다. shared objects shot noise와 correlated LSS를 분리한 cross covariance 또는 공동 생성모형을 만든다. | 비교 가능한 physical target의 joint likelihood, source-overlap receipt, marginal과 joint 결과 비교 | independence가 검증되거나 cross law가 확보된 경우에만 공동 유의도를 보고한다. 확보되지 않으면 survey별 결과를 병렬로 제시한다. 독립 CMB aberration full-vector law가 없는 현 상태를 CMB dipole template로 대체하지 않는다. |
| F. 원고 통합과 최종 주장 고정 — 현재 기본 경로 | 현재 R65 결과·그림·선행연구와 A/B의 유한 결론을 P4 기존 claim/acceptance에 대응시킨다. 기존 R54/R60 evidence와 source identity·covariance law의 차이를 명시한다. | companion manuscript, claim–evidence table, release manifest와 재현 명령; 기존 P4 acceptance의 실제 미완료 항목 유지 | B가 새 측정 차이를 제공하지 않으면 standalone 방법 논문은 추진하지 않고 P4 통합으로 종료한다. source-specific 새 차이가 충분한 경우에만 별도 논문으로 분리한다. 현재 작업에서 후속 연구루프나 agent 재시작 prompt를 만들지 않는다. |

최소 출판 경로는 **완료된 peak/integrated 비교 → A의 유한 selection-null 한정 →
B의 단일 matched comparison → F의 P4
통합**이다. 이 경로는 peak-selected conditional 결과라는 좁은 주장을 완성한다.
물리적 anomaly를 제목·초록에 쓰는 경로는 A의 response 인증과 C가 추가로
필요하다. RACS까지 동일한 nuisance-robust 실험으로 결합할 때 D/E가 필요하며,
그 작업을 현재 companion의 정의와 혼동하지 않는다. 원래 P4 acceptance가 요구하는
독립 증거가 이 좁은 companion에서 충족되었다고 처리하지 않는다.

## 8. 검증 상태와 R65 종료 판정

실행 결과는 raw-peak의 여덟 모형과 provider의 네 모형을 합한 **12개 관측 모형,
36개 독립 bin fits, 102개 관측 optimization**이다. 원 raw-peak 실험의 512개
conditional bootstrap catalogue와 2,048개 refit은 재실행하지 않았으며,
여섯 weighted RACS posterior를 재사용했다. root 실행 기록은 기존 24개와 R8의
13개 focused check를 합한 **37 tests, 11 SymPy checks와 Wolfram 검산 통과**를
보고한다. 이 작성 lane은
그 계산을 재실행하거나 새로운 독립 검증을 주장하지 않는다. 구현 검증은 실제
선택모형과 우주론적 covariance의 정확성을 자동 입증하지 않는다.

R65가 지금 닫을 수 있는 과학적 결론은 다음과 같다. 실제 peak-selected NVSS의
transverse count와 그 signed covariance를 적위 nuisance 조건부 모형에서
측정했고, 각 선택의 세 flux 구간 간 차이는 요구되지 않았다. 이어 공개 provider의
provider peak와 integrated 선택 사이에서 실제 signed vector 차이를 측정했으며,
공유 source를 보존한 paired covariance가 그 차이의 정밀도에 결정적임을 보였다.
이는 selection-dependent component-count 결과이고, 물리적 원인의 분리는 남아 있다.
비축대칭 각도 형태를 허용한 효과와 beta/residual 분리의 약한 정밀도도 수치로 제시했다.
같은 정보를 보존한 다섯 관점이나 exact conditional fit의 이름 자체에서 추가적인
정보 우월성은 관측되지 않았다. 공개 RACS posterior는 projected signal과 thermal
calibration의 강한 결합을 보여 주지만, 임의 적위 선택을 제거한 새 공동 관측은 아니다.

따라서 현재 **physical anomaly claim=false, global tilt claim=false,
Bianchi assignment=false, publication_status=NOT_READY_TO_SUBMIT**을 유지한다.
이 판정은 계산 실패나 무의미한 결과라는 뜻이 아니다. 수행한 finite experiment는
그 관측량과 검증 범위에서 완결되며, 단독 논문/물리 주장에 필요한 다음 최소 작업은
위 A/B로 특정되어 있다. integrated-flux source qualification과 채택된 네 모형
refinement는 완료되었다. 실제 자료 부재라는 잘못된 차단 사유를 되살리지 않으며,
이미 완료한 연구를 처음부터 다시 돌리지 않는다.

## 주요 원전 연결

- Ellis & Baldwin (1984), *On the expected anisotropy of radio source counts*:
  https://adsabs.harvard.edu/pdf/1984MNRAS.206..377E
- Rubart & Schwarz (2013), *Cosmic radio dipole from NVSS and WENSS*, 2D estimator와
  declination 문제: https://www.aanda.org/articles/aa/full_html/2013/07/aa21215-13/aa21215-13.html
- Siewert, Schmidt-Rubart & Schwarz (2021), estimator와 mask 방향 bias:
  https://www.aanda.org/articles/aa/full_html/2021/09/aa39840-20/aa39840-20.html
- Wagenveld et al. (2025), shared kinematic/residual response:
  https://www.aanda.org/articles/aa/full_html/2025/05/aa53397-24/aa53397-24.html
- Takeuchi (2026), selection-functional response, arXiv:2602.07389v2:
  https://arxiv.org/html/2602.07389v2
- Mittal & Lewis (2026), multiple flux-density cuts, arXiv:2605.27520:
  https://arxiv.org/html/2605.27520
- Oayda et al. (2026), *Cracking into RACS–I*, source-model/prior 및 공개 posterior:
  https://arxiv.org/html/2610.35207v1
  ; release: https://github.com/o-oayda/cracking-into-racs-i/releases/tag/v1.0.0

위 원전의 상세 독해 범위와 출처별 한계는 [문헌 검토](REVIEW/r65_literature.md)를 따른다. 이 계획문
작성 중 새 primary-source 검색을 수행한 것으로 기록하지 않는다.
