# R66 — low-ell 형태론에서 물리 관측량으로: P2 논문화 계획

## 선택한 논문과 심사 판단

이번 단위는 기존 P2의 독립 companion이다. 질문은 “실제 CMB 저차 다중극자의 어떤 부호 있는 조합이, 알려진 관측자 방향의 Doppler 사중극자 진폭을 모르는 상황에서도 국소 복사 비등방 응력으로 해석될 수 있는가?”로 고정한다. 여기에 실제 처리 연산자와 불확실성을 붙인다. 공간의 현재 shear 측정이나 Bianchi 분류를 이 논문의 결론으로 추가하지 않는다.

현 상태의 제출 판단은 **NOT_READY_TO_SUBMIT**이다. 이유는 연구가 실행되지 않았기 때문이 아니다. 실제 Commander PR3/PR4 관측, 명시적 물리 사상, 분석적으로 전파한 이상적 Gaussian 공분산 및4096개 합성 carrier 계산이 있다. 처음 선택한 공개005a100개의 I는 모두0이라 온도 reference에서 제외했고, 별도의 온도 제품은 단위와 확보 조건이 아직 완결되지 않았다. 다만 온도에서 복사 응력으로의 변환은 기존 이론이며 R36에 이미 구현되어 있고, DQ 보정과 저차 다중극자 tensor 통계 역시 선행연구가 있다. 이번 기여의 출판 가치는 실제 처리된 자료에서 보존되는 물리 정보, 같은 하늘의 처리 차이, 적합 대역 의존성과 그 제어를 얼마나 설득력 있게 정량화하는지에 달려 있다. 현재는 방법론·재현성 결과를 기존 P2에 통합하는 경로가 가장 강하다. 독립적인 새 우주론 발견 논문으로 포장하면 거절 가능성이 높다.

가제는 **Radiation-stress images of low-multipole CMB morphology with an unknown Doppler residual**로 둔다. 최종 제목에서는 정확한 자료·보정 범위에 따라 “conditional”을 포함할 수 있다.

## 이미 재사용하고 실행한 핵심

기존 573-PR metadata inventory를 재사용하고, 해당 가지의 결정적 내부 source 28개를 직접 다시 대조했다. R36의 정확한 T^4, rho/flux/pi/H4, Landau 및 radiation-response 연산자, R60의 실제 Commander STF 변환, R51/L01의 mask·단위·response 교훈, R54/R58의 전공분산 추론을 연결했다. 이 횟수는 573개 diff를 이번에 모두 다시 의미론적으로 심사했다는 뜻이 아니다. 정확한 파일·Git blob·SHA와 읽은 범위는 HISTORY와 SOURCES에 있다.

R66의 실제 관측 계산은 이미 로컬에 있는 공개 Commander 자료를 사용한다. 별도 온도 simulation 제품의 공개 접근도 직접 시도했지만 완료된 reference bank로 주장하지 않는다. PR3와 PR4 온도를 각각의 실제 native NESTED 해상도와 단위로 읽고, common intensity mask를 native pixel에 먼저 적용한 뒤 child average를 한다. parent coverage 0.995 이상을 남긴다. 주 실험은 NSIDE64, ell<=6이다. NSIDE128, ell<=6은 해상도와 보존 mask support가 함께 변하는 control이며 순수 discretization convergence라고 부르지 않는다. NSIDE64, ell<=8은 harmonic truncation control이다. 원래 42개 acceptance와 L03/L04/L06은 이 실행만으로 승격되지 않는다.

단일 DQ template는 실제 native pixel averaging과 추정기에 통과시켜 검산한다. 이는 알려진 downstream 반응이다. 공개 Commander component-separation 내부의 모든 잔여물 반응이 rank one이라는 관측적 확인은 아니다. 정확한 map product에 결부된 주파수·공간 의존 잔차가 주어지면 그 실제 span을 사용해야 한다.

0300–0399의 공개005a100개는 전부 fresh SHA256가 원 receipt와 일치했지만 I가0이었다. 분석은 singular covariance를 거부했고 원 데이터·실패 로그를 보존했다. 별도의 scalar T0200–0299 bank는 RING4096이지만 TUNIT1이 비어 있다.16개 pilot의 병렬 HTTP 응답이 중도 종료되어 부분 파일을 표본으로 세지 않았다. 단일0200 content 진단은 물리 reference 승인이 아니다.

실행한 통계 기준은 기존 R49가 사용한 Planck TT 스펙트럼을 고정한 이상적 Gaussian 픽셀 모형이다. 같은 실제 추정기 가중치, native quadrupole response, 세 추정기의 공동 공분산을 보존한다. ell>=3은 NSIDE128 pixel-centre/window,5arcmin beam, ell<=256으로 명시한다. 공분산은 분석적으로 알려져 있으므로 주 likelihood는 Gaussian이며4096개 합성 carrier는 검증과 GLS 훈련용이다. 이것을 Commander end-to-end MC나 실현된 하늘의 measurement-only error로 부르지 않는다. SEVEM의 제한된 접근을 새 gate로 만들지 않는다.

## 검증 가능한 주장 묶음

1. **이론의 재사용과 새 적용을 분리한다.** STF 온도 텐서에서 pi_lin/rho0=(8/15)Q/T0로 가는 관계, 정확한 T^4 적분, 고정 rank-one nuisance quotient 및 GLS는 established/derived 결과다. 새 데이터 결과는 실제 Commander에서의 부호 있는 물리 proxy, release contrast, 처리 연산자 민감도 및 비선형 교정값이다.
2. **식별 집합을 먼저 제시한다.** 5성분 중 알려진 template의 진폭 하나를 제거하면 4성분이 남는다. 없어진 성분을 0으로 측정했다고 쓰지 않고 affine line/cylinder로 기록한다. Euclidean quotient와 공분산 profile의 동등성은 전체 공동 공분산을 보존할 때 성립한다.
3. **octupole의 물리적 경로를 계산한다.** 온도 ell=3은 선형 복사 응력에 직접 들어가지 않지만, 복원된 dipole과의 이차 결합 24 d_k O_kij/35를 통해 들어간다. ell<=6 T^4 적분은 이 항을 포함한 모든 retained-band 결합을 보존한다. 실제 누락 고차 모드·foreground·spectral completion에 대한 근거 없는 수치 상한은 만들지 않는다.
4. **같은 하늘의 공분산을 보존한다.** ell<=6와 ell<=8 출력은 독립 하늘이 아니다. 처리 의존성을 발견한 뒤 추가한 8차원 paired estimator는 이상적 모형의2048개 training carrier에서만 가중치를 정하고, 별도2048개로4차원 공분산을 검증한다. 선택한 likelihood는 알려진 분석 공분산 W C8 W^T를 사용한다. WJ=I4를 만족해야 한다. 원래 관측 primary 추정기는 유지한다. 이 추가 분석은 관측된 민감도에서 출발했으므로 현재 하늘의 discovery PTE로 사용할 수 없다.
5. **5변수는 하나의 통계 실험의 다섯 영상이다.** x는 full signed carrier와 공동 법칙, Q는 선언한 anchor를 이용한 score, Pi는 특정 법칙 아래의 exceedance이다. F는 허용된 기준 body에서 명시적 측도를 가진 occupancy이다. support function을 F라고 바꾸지 않는다. pi/rho의 정확한 positivity body와 pi_lin/rho0 proxy의 차이를 유지한다. 하나의 마지막산란 하늘에는 depth series가 없으므로 G_F는 NOT_APPLICABLE이다.

이 묶음은 기존의 정확한 a_lm likelihood보다 더 많은 정보를 만드는 방법이라는 주장을 포함하지 않는다. scalar C2·축·quadratic power tensor가 버리는 부호/방향을 보존한다는 비교가 정당한 범위다.

## 가장 가까운 방법과의 직접 비교

| 비교 대상 | 이미 알려진 부분 | 이번에 대조한 내용 | 남은 차별성 조건 |
|---|---|---|---|
| Maartens–Gebbie–Ellis 1999; Challinor 2000 | 밝기 multipole, stress tensor, frame 변환 | 정의 적분과 c·단위·부호; 기존 R36 재사용 | 관계 자체를 새 이론으로 주장하지 않음 |
| Notari–Quartin 2015 | 주파수 의존 DQ와 morphology 변화 | 미지의 잔차 진폭을 보존하는 downstream quotient | 실제 PR3/PR4 residual response를 bound해야 exact physical claim 가능 |
| Planck 2018 VII | 저차 이상 통계, mask/MC 및 polarization 검정 | 동일 처리·같은 하늘·사후 선택을 유지한 실제 reference | 광범위 anomaly significance를 재주장하지 않음 |
| Aluri–Patel 2506.22795v1 | PR4 Commander power tensor·정렬 분석 | 같은 R66 입력에서 Eq.2 power tensor를 직접 계산; Q와 -Q 구별 불가 확인 | 그 논문의 inpainted pipeline/MC를 재현했다는 주장과 분리 |
| Banday et al. 2508.16451v1 | T-conditioned E와 T2/T3/E2/E3 axis 비교 | 단순 교차 축 정렬의 novelty 부족 확인 | E 추가는 여기에서 자동으로 별도 가지로 확장하지 않음 |
| R36/R51/R54/R58/R60 | 실제 프로젝트의 physics/operator/GLS/형태론 자산 | 데이터에서의 복사 응력 영상과 DQ-orthogonal signed 비교 | 새로운 이름이 아니라 결과와 해석의 증가량을 제시 |

Aluri–Patel의 논문은 온도 MC를 native NSIDE4096으로 서술한다. 최초 후보인2048/005a는 실제 I=0이었고, 별도의 bare4096 scalar T 제품을 찾아야 했다. 단순한 파일 개수나 Commander라는 이름으로 ensemble identity·온도 유효성·단위를 대체할 수 없다. NPIPE 논문의 SEVEM 절에서 설명한 DQ subtraction 역시 Commander의 정확한 residual template로 전용하지 않는다.

## 수렴하는 다음 작업: 세 개의 유한 패키지

### A. 실제 map response의 출판 범위 고정

관측 입력·해시·native operator와 실행한 이상적 기준법칙은 고정되어 있다. 현 결과의 release contrast94.70%가 단일DQ 방향에 수직이고, band6→8의 quotient vector 변화는66.60%다. 이 두 값을 error budget의 우선순위로 둔다. 남은 일은 정확한 PR3/PR4 Commander 제품의 DQ·유효 beam·simulation 구성을 자료 설명 또는 공개 producer 설정과 결부하는 것이다. 실제 잔차 template가 확보되면 동일한 추정기에 통과시키고, nuisance span의 rank와 projected stress 변화만 계산한다. 단일 진폭이 충분하지 않으면 새로운 template의 검증된 span을 반영한다. 자료가 확보되지 않으면 논문 표적을 “released-map conditional stress image”로 고정한다. 이것을 끝없는 source 탐색이나 새로운 이론 가지의 명분으로 삼지 않는다.

완료 조건은 둘 중 하나다. 정확한 product response로 변경폭을 산출하거나, 현존 source가 지지하는 조건부 범위를 명확히 확정하고 해당 표와 원고에 반영한다. 물리적 PTE가 필요 없는 처리 비교 결과 자체는 보존한다.

### B. 고정된 한 가지 conventional reconstruction과 비교

현재 power tensor 비교는 같은 입력이 보존하는 정보의 비교다. 실제 전체 하늘의 stress reconstruction을 주장하려면, 같은 mask·band·DQ nuisance·공분산 아래의 기존 Gaussian conditional harmonic reconstruction 또는 QML 한 가지와 비교해야 한다. 새로운 하늘을 대량으로 생산하기 전에 이미 저장한 signed MC carrier와 paired response로 bias/variance·coverage target을 구체화한다. 추가 noise/input-sky pairing이 필요한 경우 그 실제 입력을 먼저 식별한다.

현재 paired GLS는 다음 연구를 위한 실행 가능한 예제이며 관측 의존 선택을 제거한 결과는 아니다. 후속 검증은 지금 고정한 W와 target을 유지한 독립 자료 또는 독립 simulation에서 수행한다. 재선택한 W를 같은 holdout에 다시 최적화하지 않는다. 필요한 실제 MC 수는 목표 bias/coverage 정밀도에서 결정한다. 합성4096개는 현재 이상적 모형의 수치 정밀도를 높일 뿐 source 불확실성을 줄이지 않는다. GLS의 현 부피 감소1.53%는 실질적 개선을 입증하는 크기가 아니다.

완료 조건은 같은 물리 estimand에 대한 conventional 방법과의 결과·불확실성·실패 조건 한 표다. 차이가 단지 좌표 변경이면 그 사실을 결론으로 채택한다. 의미 있는 bias 제어 또는 물리 식별성의 이득이 없으면 독립 방법론 논문보다 P2의 methods/results 절에 통합한다.

### C. 원고 통합과 출판 결정

권장 구성은 6개 절이다: (1) 물리적 질문과 선행연구, (2) 온도·밝기·observer frame 및 STF 정의, (3) 실제 finite operator와 식별 집합, (4) Commander 자료·같은 하늘의 공분산·conditional likelihood, (5) release/band sensitivity·T^4 교정·conventional comparison, (6) 물리 해석과 한계. THEORY의 일반 증명과 세밀한 provenance는 부록으로 보낸다. 본문에는 독자가 observable과 statistical experiment를 재구성할 수 있는 식과 핵심 표를 남긴다.

Figure는 현재 생성한 signed stress/unknown-DQ/ideal-reference/processing-control 그림을 시작점으로 삼는다. 최종 원고에서는 population reference 범위를 measurement error bar로 보이게 그리지 않는다. 필요하면 L_I의 방향 의존성 및 octupole 교정값을 별도 표에 포함한다. 수학적 회전 공변성, 실제 unit/header/hash와 실패 분류, 알려진 covariance 및 finite-N 대안, 같은 하늘 covariance, source-qualified claim을 한 번의 재현 package로 제공한다.

제출 결정은 “새 일반이론”과 “새 우주론 anomaly”를 제거한 뒤에도 실제 데이터와 비교 결과가 기존 P2에 비해 독자가 배울 내용을 남기는가로 내린다. 그렇다면 P2의 methods/results companion으로 합친다. 그렇지 않으면 검증된 계산과 한계를 프로젝트에 보존하고 독립 논문화 주장을 종료한다. 이번 요청은 하나의 10단계 단위이며 다음 loop를 자동 실행하지 않는다.

## 원전

- [Maartens–Gebbie–Ellis, astro-ph/9808163v2](https://arxiv.org/abs/astro-ph/9808163v2)
- [Challinor, astro-ph/9911481v2](https://arxiv.org/abs/astro-ph/9911481v2)
- [Notari–Quartin, 1504.02076v2](https://arxiv.org/abs/1504.02076v2)
- [Planck 2018 VII, 1906.02552v2](https://arxiv.org/abs/1906.02552v2)
- [Planck NPIPE, A&A643 A42](https://www.aanda.org/articles/aa/full_html/2020/11/aa38073-20/aa38073-20.html), Sections7.1/7.2 and AppendixC
- [Aluri–Patel, 2506.22795v1](https://arxiv.org/html/2506.22795v1), Eqs2–3 and Section3
- [Banday et al., 2508.16451v1](https://arxiv.org/html/2508.16451v1), Eq3.1 and Section7


## 현재 데이터로 고정한 주요 수치와 stop condition

PR4 primary quotient norm26.676421microK, pi_lin/rho0 norm5.22015e-6, 이상적 Gaussian 아래 lower-tail0.098401이다. 이 값은 물리 anomaly 검정의 최종값이 아니다. NSIDE128/support control의 벡터 변화4.067%, lmax8 control의 변화66.596%다. 복원된 dipole과 octupole의 retained-band 비선형 응력 효과는약0.023microK 규모여서 현재의 추정기 대역 의존성보다 훨씬 작다.

다음 작업의 종료 기준을 다음처럼 고정한다. 같은 입력·target의 conventional conditional harmonic reconstruction 한 가지와 비교해 band-sensitivity 감소, injection bias와 coverage를 한 표로 낸다. 실제 source contract가 승인되면 physical-null 분석을 수행하고, 승인되지 않으면 achieved conditional scope에서 원고를 닫는다. 단순 좌표변환 이상으로 보이는 이득이 없으면 독립방법론 논문 주장은 종료하고 기존P2 methods/results에 통합한다. 새 연구 가지, 무한 validation gate, local agent 지시문은 만들지 않는다.
