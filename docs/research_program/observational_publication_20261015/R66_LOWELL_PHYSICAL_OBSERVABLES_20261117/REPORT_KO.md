# R66 — low-ell 형태론과 물리 관측량: 실제 계산 결과 및 출판 심사

## 결론

이번 단위는 **relating low-ell morphology to physical observables**만을 대상으로 한 독립적인10단계 이론/코딩 연구다. 기존R36의 정확한 복사 moment, R60의 실제 Commander STF carrier, R54/R58의 tensor·공분산 추론을 재사용해 실제 PR3/PR4 지도에서 **부호 있는 국소 광자 비등방 응력의 선형 proxy**와 선언한 Doppler quadrupole(DQ) 방향을 제거한4성분을 계산했다. 이 물리 사상 자체와 quotient/GLS를 새로운 일반이론으로 주장하지 않는다.

가장 중요한 관측 처리 결과는 두 가지다. PR3→PR4 차이의94.703%가 선언한 단일DQ 방향에 수직이며, PR4의 적합 대역을 ell<=6에서8로 바꾸면 retained tensor vector가66.596% 변한다. 이에 비해 retained-band 비선형 복사 보정은 약0.02283microK, 이상적 모형에서 paired GLS의 타원체 부피 감소는1.529%에 그친다. 논문화에서 우선 해결해야 할 문제는 finite-band reconstruction의 안정성과 source-qualified response다.

제출 판단은 **NOT_READY_TO_SUBMIT**이다. 실제 데이터 계산과 방법 비교는 완료했지만, 현재 결과만으로 새로운 우주론 anomaly, spacetime shear 측정, Bianchi 모형 귀속 또는 독립적인 새 통계이론을 지지하지 않는다. 가장 강한 출판 경로는 기존P2의 물리 관측량·방법·결과 절로 통합하고, 동일 estimand의 conventional reconstruction 한 가지와 유한한 bias/coverage 비교를 마치는 것이다.

## 실행 자료와 실패를 보존한 방식

[OBSERVED_EXTRACTION.json](RESULTS/OBSERVED_EXTRACTION.json)은 실제 지도, mask, 단위, hash와 연산자를 기록한다. PR3의 I_STOKES는 K_CMB, NESTED2048이며 PR4의 TEMPERATURE는 K_CMB, NESTED4096이다. common PR3 intensity mask를 native child pixel에 먼저 적용하고 parent coverage>=0.995를 요구했다. 주 추정기는 NSIDE64/ell<=6, controls는128/6과64/8이다. 상수·dipole·STF quadrupole은 native pixel 평균을 실제 설계행렬에 넣고, ell>=3은 parent-centre real harmonic을 썼다. native averaging된 DQ 주입 recovery 오차는최대4.0e-14microK, monopole/dipole 누출은5.93e-16 이하다.

128/6 control은 해상도와 retained mask support가 함께 변한다. 따라서 순수한 discretization-convergence 실험이라고 해석하지 않는다.64/6은33277pixel,128/6은145936pixel을 유지하며 설계행렬 condition은각각9.208,8.837이다.64/8은15.942다. 이들은 고정된 cut-sky finite estimator의 조건수이지 component-separation 역문제 전체의 조건수가 아니다.

최초에 선택한100개 공개005a Commander simulation 파일은 온도 reference로 부적격이었다. 전부 fresh SHA256가 원 acquisition receipt와 일치했지만 추출한 I carrier가0이었다.300,349,399 raw spot check도 I=0, Q/U!=0을 확인했다. 분석은0 covariance의 역산을 거부했고 regularization으로 통과시키지 않았다. 원래 배열과 extraction 결과는 `polarization_bank_temperature_diagnostic.npz`, `POLARIZATION_BANK_EXTRACTION.json`에 보존했다. **원 파일의 편광 활용이 무효라는 뜻은 아니다. 잘못된 온도 제품 선택을 교정한 것이다.**

별도의 공개 scalar T bank0200–0299를 실제 PLA catalogue와 header에서 찾았다. 이 제품은 RING4096이고 TUNIT1이 비어 있다.16개로 제한한 병렬 pilot은 HTTP response가 중도 종료되어 중단했고, 부분 파일은 realization으로 세지 않았다. 별도로 시작한0200은1,610,622,720byte 전체를 확보했으며 SHA256는 `62420c23f3dcd05a6d95a851808e21f3a041c8c3ba47f0545970e791180de2be`다. 이 한 파일은 내용·RING/NESTED 연산자 확인용이며, 단위 미확정 및 표본 부족 때문에 covariance/PTE에 사용하지 않는다. `SOURCE_FAILURE_AND_REPAIR.json`, `TEMPERATURE_PILOT.json`, `TEMPERATURE_CONTENT_PILOT.json`이 이 경계를 기록한다.

그 상태에서 실행할 수 있는 통계 계산을 실제로 수행하기 위해 기존R49의 Planck R3.01 TT spectrum을 고정한 **명시적 이상적 Gaussian reference**를 구성했다. 세 추정기의15차원 공동 공분산을 분석적으로 전파했으며4096개 합성 carrier를 생성했다. 실제 native quadrupole injection과 같은 하늘의 cross-covariance를 보존한다. ell>=3은 NSIDE128 pixel-centre/window,5arcmin Gaussian beam, ell<=256이라는 생성모형을 선언한다. 이는 Commander end-to-end bank가 아니다. 정확한 가정과 재현식은 [IDEAL_REFERENCE.md](IDEAL_REFERENCE.md), 숫자는 [IDEAL_REFERENCE.json](RESULTS/IDEAL_REFERENCE.json)에 있다.

## 정의에서 물리 영상까지

metric은(-,+,+,+), n은 관측자가 하늘을 보는 방향이다. 광자 진행 방향은-n이므로 odd moment인 flux의 부호를 따로 유지한다. 온도 사중극자를

    delta T2(n)=Q_ij n_i n_j,  tr Q=0

로 정의한다. Frobenius-orthonormal STF 기저의 순서는(xx-yy)/sqrt2, (xx+yy-2zz)/sqrt6, (xy+yx)/sqrt2, (xz+zx)/sqrt2, (yz+zy)/sqrt2다. 이5벡터는 signed real a_2m와 가역적으로 대응한다.

T0=2.72548K, rho0=pi² k_B^4 T0^4/(15 hbar³ c³)=4.1746783808e-14J/m³를 쓰면 blackbody brightness의 선형 사중극자 응력은

    pi_lin,ij/rho0 = (8/15) Q_ij/T0.

microK 단위의 Q를 쓸 때 계수는1.95684185293e-7/microK다. 유도는 <n_i n_j n_k n_l>=(delta_ij delta_kl+delta_ik delta_jl+delta_il delta_jk)/15와 tr Q=0에서 바로 얻는다. exact rho와 pi는 각각 rho0<(1+Theta)^4>, rho0<(1+Theta)^4 n_<i n_j>>다. 문헌의 brightness multipole 이론과 기존R36 구현을 재사용했다. [Maartens–Gebbie–Ellis](https://arxiv.org/abs/astro-ph/9808163v2), [Challinor](https://arxiv.org/abs/astro-ph/9911481v2) 및 [THEORY.md](THEORY.md)를 참조한다.

기준 dipole은3362.08microK, Galactic(l,b)=(264.021,48.253)deg다. beta=dipole/T0에 대해 b=T0 STF(beta beta)의5성분을 만든다. 실제 downstream 추정기에 통과시킨 b의 recovery를 직접 검증했다. U^T b=0인5x4 정규직교 U를 고정하면

    s=U^T q,  q_perp=U s,  q ~ q+alpha b

이며 s는 선언한1차원 nuisance의 영향을 받지 않는다. 이는 정확한 full-frame boost invariant가 아니고, Commander 내부 잔여 response가 실제로 rank1이라는 확인도 아니다. 미지 성분을0으로 측정한 것이 아니라 affine line을 남긴 것이다. 공분산 C가 양의 정부호이면

    P=C^-1-C^-1 b (b^T C^-1 b)^-1 b^T C^-1
     =U (U^T C U)^-1 U^T

로 covariance profiling과 동등하다. 이 동등성은 실제 구현에서 검산했다.

## 실제 관측 결과

모든 수치는 아래 finite estimator에서의 point estimate다. population scatter를 실현된 하늘의 measurement-error bar로 붙이지 않는다. 상세 재현 숫자는 [OBSERVABLES.json](RESULTS/OBSERVABLES.json)에 있다.

| 지도/추정기 | ||q||[microK] | ||q_perp||[microK] | 이 추정기의 C2[microK²] |
|---|---:|---:|---:|
| PR3,64/6 |24.940209|24.885045|208.438893|
| PR4,64/6 primary |26.693838|26.676421|238.781478|
| PR3,128/6 |25.072439|24.948270|210.654991|
| PR4,128/6 |26.995849|26.941732|244.215133|
| PR3,64/8 |35.625110|34.755013|425.295730|
| PR4,64/8 |36.174058|35.508853|438.503491|

여기의 C2=8pi||q||²/75는 동일한 추정기에서의 harmonic power 표현이다. 전체 하늘을 무편향 복원한 최종 cosmological C2 추정치라고 명명하지 않는다.

PR4 primary의 signed5벡터는(-7.698302,-8.236857,21.944866,4.071190,9.343425)microK다. 행렬은

    [[-8.806204, 15.517363, 2.878766],
     [15.517363,  2.080839, 6.606799],
     [ 2.878766,  6.606799, 6.725365]] microK.

고정한 U에서 retained4성분의 pi_lin/rho0는(-1.2909283,4.2180562,0.8825263,2.6481424)x10^-6이다. 노름은5.2201537454e-6, SI 응력 노름은2.1792462985e-19Pa다. 숫자는 실제 지도에 대한 선형 quadrupole-sector proxy의 물리 단위 변환이다. 무관측 고차 모드·스펙트럼·foreground completion까지 포함한 정확한 전천 총응력 측정을 주장하지 않는다.

### 같은 하늘의 release contrast

64/6에서 ||q_PR4-q_PR3||=3.014357microK다. 이 차이를 alpha b로 최적 적합하면 alpha=0.204868933, 남은 수직 성분의 노름은2.933438microK다. 차이의 제곱노름 중94.70315%가 b에 수직이다.

따라서 **이 두 released-map 추정치의 차이를 선언한 단일DQ amplitude 변화만으로 설명할 수 없다**. 이 결론은 관측한 유한5벡터에 대한 대수적 사실이다. 원인이 foreground, component-separation, beam, 다른 처리, cosmology 중 무엇인지는 이 contrast만으로 결정되지 않는다. PR3/PR4는 같은 하늘이므로 두 독립 우주를 관측한 것으로 계산하지 않았다.

### 대역과 해상도/support 민감도

PR4 primary를 기준으로128/6의 retained vector 차이는1.085034microK,4.06739%다.64/8은17.765372microK,66.59579%다. 후자의 노름 증가 자체는약33.11%이지만 벡터 변화는 방향과 성분을 포함하므로 더 크다. scalar norm만 비교하면 이 차이를 축소해서 보게 된다.

이 실제 데이터 민감도는 이상적 reference의 cutoff 안정성과 다른 문제다. reference L64→256의 quotient covariance trace 변화는0.04738%이지만 실제 fitted band6→8의 변화는66.60%다. 앞의 작은 수치로 뒤의 불안정성을 닫을 수 없다.

## 비선형 물리량과 octupole의 기여

지도에서 적합한 상수와 dipole은 absolute radiation monopole/dipole로 해석하지 않고, 선언한 T0와 기준 dipole을 한 번 복원했다. ell<=6 retained temperature family에서 exact T^4 moment를32Gauss–Legendre×64azimuth quadrature로 계산했다. 최대 polynomial degree26을 처리한다. alpha in{-2,-1,0,1,2}는 추가DQ의 sensitivity coordinate이며 inferred correction이나 prior가 아니다.

Theta=d_i n_i+Q_ij n_i n_j/T0+O_ijk n_i n_j n_k+...일 때 dipole×octupole은

    (pi_ij/rho0)_(dO)=24 d_k O_kij/35

로 응력에 들어온다. octupole은 선형 pi에 직접 들어가지 않지만 이차 결합으로 물리량에 연결된다. 이를 별도 수치 구면적분과 비교했다.

실제 PR4 retained family에서 octupole을 제거했을 때의 quotient 차이는0.0228676microK equivalent이고, alpha=0에서 exact retained moment와 선형 proxy의 전체 quotient 차이는0.0228295microK equivalent다. 이는 현재의17.765microK band sensitivity보다 훨씬 작다. 누락된 true-sky high-ell, foreground와 spectral completion의 상한은 주어지지 않았으므로 이 작은 retained correction을 총 체계오차 상한으로 쓰지 않는다.

R36의 static radiation response L_I[S]=8rho S/15+10 STF(S pi)/7-H4:S도 실제 retained family에서 평가했다. PR4 L_I/rho의 고유값은0.53332996…0.53333783이고 isotropic8/15에서의 변화량은 ||L_I/rho-(8/15)I5||_F/(8/15)=1.21544e-5다. 분모를 기준행렬의 Frobenius norm ||(8/15)I5||_F로 잡으면5.43562e-6이며, 두 정규화를 구분한다. moment식과 direct integration의 최대 차이는1.33e-15다. 이것은 국소 복사 분포의 선형 응답 영상이며, 시간·공간 미분과 transport/source 정보 없이 현재의 spacetime shear를 역추정하는 식으로 승격하지 않는다.

## tensorized5변수의 실질적 역할

| 변수 | 실행된 정의·상태 | 해석 범위 |
|---|---|---|
| x | full signed STF5, quotient4, 실제 operator·covariance | 방향·부호·공분산을 보존하는 기본 carrier |
| Q | ||pi_lin,perp/rho0||/sqrt(2/3); PR4=6.3933565e-6 | exact positivity outer radius로 정규화한 선형 proxy score |
| Pi | 명시한 Gaussian모형에서 q² 및 lower/upper tail | 실제 Commander physical-null 유의도와 구분 |
| F | 허용된4차원 inscribed ball, uniform Lebesgue측도에서95%mean-ellipsoid의 부피 점유율 | probability of cosmology가 아니며 spectral/missing-mode completion 없이는 정확한 물리F가 아님 |
| G_F | NOT_APPLICABLE | 하나의 마지막산란 하늘에 depth-series를 만들어 붙이지 않음 |

F의 denominator는 R_in=1/sqrt6인 retained STF ball의 부피다. 정확한 radiation body는 I/3+pi/rho가 positive semidefinite인 집합이며 이 ball은 그 안에 들어간다. contained ellipsoid에 한해 F=c95^4 sqrt(det Cx)/R_in^4다. primary의 조건부 F=2.1298526e-18은 선택한 넓은 admissible body와 단위·측도에 대한 부피율이다. 작은 수치를 cosmological improbability로 바꾸지 않는다. PR3/PR4의 동일 covariance ellipsoid가 둘 다 body 안에 있으므로 이 F는 같으며, 중심과 방향의 차이는 x와 공분산을 함께 유지해야 보존된다.

부호 없는 C2와 conventional quadratic power tensor는 q와-q에 같은 값을 준다. pi_lin은 부호가 바뀐다. 실제 같은 입력에서 [Aluri–Patel Eq.2](https://arxiv.org/html/2506.22795v1)의 power tensor를 구현하고 trace=C2, 회전 공변성, sign invariance를 검증했다. PR4 primary의 entropy는0.8563598이다. 이 비교는 그 논문의 inpainted map/100MC pipeline을 재현했다는 주장이 아니다.

5변수 방법의 정당한 기여는 물리 estimand·식별된 성분·기준법칙·점유측도·변화축을 한 실험 안에 명시하면서 signed tensor를 버리지 않는 데 있다. 완전한 signed a_lm likelihood와 STF likelihood는 가역 좌표변환이므로 정보량이 같고,5변수라는 이름만으로 정보가 증가하지 않는다. 새로운 독립 통계 이론의 우월성은 이번 계산에서 입증되지 않았다.

## 조건부 likelihood와 paired reconstruction

물리적 mean-stress parameter를 mu라 두면 s_pi=k U^T q, k=8/(15T0_microK), C_pi=k² U^T Cq U에 대해

    L(mu|s_pi) ∝ |C_pi|^-1/2 exp[-(s_pi-mu)^T C_pi^-1(s_pi-mu)/2]

를 구성한다. 현재 Cq는 명시한 이상적 Gaussian model에서 알려진 population covariance다. 이 식을 kinematical theta=(sigma,omega,A,beta)에 대한 likelihood로 바꾸려면 별도의 검증된 mean map mu(theta)와 source/transport law가 필요하다. 한 하늘의 quadrupole만으로 모든 theta component를 측정했다고 해석하지 않는다. 기존R51/R54의 integrated-redshift/shear 모형은 가능한 제한적 forward model이며 이번에 새로 증명하거나 재실행한 가지가 아니다.

PR4 primary에서 q²=1.05336538,4자유도 lower-tail=0.09840105다. control64/8은0.23333582다. 이 모형 내부에서조차 강한 이상도를 주는 결과가 아니며, 이상적 law라는 제한이 먼저 적용된다. 실제 source-qualified physical PTE는 unresolved다. PR3에 이 reference를 적용한 숫자는 cross-release sensitivity로만 보존했다.

두 fitted band의 quotient를8벡터로 묶고 J=[I4;I4]를 사용했다.2048 synthetic training rows로 구한 W=(J^T S8^-1 J)^-1 J^T S8^-1은 WJ=I를2.22e-15 수준에서 만족한다. likelihood에는 analytic W C8 W^T를 사용하고,2048 holdout은 이를 검증한다. 상대 covariance eigenvalues는(0.98207,0.99239,0.99481,1.00012), 부피비는0.9847119다. 이 작은 감소는 강한 개선이나 최적의 물리 복원을 입증하지 않는다. paired PR4 norm은28.861965microK다. 관측된 민감도에서 출발한 exploratory secondary이므로 새 discovery PTE로 사용하지 않았다.

## 기존 연구 재사용과 novelty 심사

기존573PR metadata inventory를 재사용했고, 이 가지의 결정적 내부 source28개를 직접 다시 대조했다. 이번에573개 전체diff를 새로 의미론적으로 심사했다고 표현하지 않는다. 구체적인 source identity와 재사용 범위는 [HISTORY.md](HISTORY.md), [HISTORY_SOURCES.json](HISTORY_SOURCES.json)에 있다. 외부1차문헌과 실제 제품 설명은 [LITERATURE.md](LITERATURE.md), [SOURCE_ADDENDUM.md](SOURCE_ADDENDUM.md), [PUBLIC_TEMPERATURE_SOURCES.md](PUBLIC_TEMPERATURE_SOURCES.md)에 연결했다.

| 비교 | 이미 존재한 것 | R66의 증가량과 판정 |
|---|---|---|
| MGE/Challinor 및 내부R36 | brightness→rho/flux/pi, exact T^4,frame,response | 실제 Commander family에 적용; 변환 자체 novelty없음 |
| Notari–Quartin2015 | frequency-dependent DQ가 morphology를 바꿈 | 실제 downstream injection, 미지 amplitude quotient,release difference의 수직성; 정확한 upstream span은미확정 |
| Aluri–Patel2025 | PR4 low-ell power tensor·entropy·정렬 | 같은 signed 입력에서 직접 비교; signed stress target은 다르지만 fullharmonic법보다 정보가 많지는 않음 |
| Banday etal.2026 | T-conditioned E 및 T2/T3/E2/E3axis비교 | 단순 axis연결만으로 novelty를 주장하지 않음; 이 가지를 새E분석으로 확장하지 않음 |
| 내부R51/R54/R58/R60 | actual tensor,integratedkinematics,fullcovarianceGLS | 데이터→물리proxy→nuisance→reference의 실행 가능한 단일 계약,sourcefailure교정,정량오차우선순위 |

**현재 강점**은 실제 자료를 읽어 signed observable을 SI 단위까지 계산했고, 부호·같은 하늘·단위·누락모드·population과measurement error의 차이를 보존했다는 점이다. **주요 거절 사유**는 알려진 좌표변환을 새 이론으로 제시하는 것, band sensitivity를 해결하지 않은 전체하늘 stress 측정 주장, 이상적 Gaussian reference를 actual Commander significance로 취급하는 것이다. 후속 목표는 아이디어 추가보다 동일 target의 재구성 비교 한 번과 명확한 원고 범위다.

## 완료·미해결 상태와 논문화 계획

- **established / literature-supported:** 복사moment와 Doppler 관련 이론, 기존project의R36/R54/R58/R60 자산.
- **derived:** declaredDQ quotient와 profile동등성, retained dipole–octupole항, 유한Gaussian likelihood·occupancy·angular단위소거의 명시적 조건.
- **numerically checked / implementation-verified:** actualPR3/PR4추출, native injection, knowncovariance/finiteN검산, retainedT^4와response,24개focusedtests, 실제그림확인.
- **unresolved:** 정확한CommanderDQ/beam/noise/foreground response, 실제TMC단위와충분한bank, true-skycompletion, instantaneouskinematicinversion.
- **blocked:** 원래16파일pilot의HTTP중도종료. 부분파일을보존하고qualifiedMC로세지않음.

[RESEARCH_PLAN_KO.md](RESEARCH_PLAN_KO.md)는 세 유한패키지로 수렴한다. 첫째 정확한productresponse를결부하거나현재의conditionalreleased-map범위로원고를닫는다. 둘째 동일mask/band/nuisance/physicaltarget에서 conventional conditional harmonic reconstruction또는QML한가지만고정해 bias·variance·coverage를비교한다. 셋째 결과가기존P2보다실제물리해석을증가시키는지판정해 methods/results에통합한다. 차이가좌표변경에그치면독립새방법론주장을종료한다.

이번10단계 단위는 관측 결과, 계산 가능한 reference, 실패의 보존과 교정, 출판 판정 및 additiveDAG까지 완결하는 범위다. 원래42개 과학 gate와 모든 논문 acceptance는 보존하고 제출상태를 승격하지 않는다. 다음 연구 loop와localcodingagent지시문은 만들지 않는다.
