# R98 — SQ-CF4 재진입, 4차 이론·코딩 연구 결과

2026-11-23, Asia/Seoul. 작업 직전 commit은 52fee3f277d715cdb982dfbe751fefac10513060이며, 작업 branch는 research/r69-observable-physics-bridges-20261118이다.

## 1. 이번에 완료한 범위

선택한 4차 이론 R1–R10과 코딩 C1–C10에서 가능한 구성·계산·실행 준비를 완료했다. 전체 CF4 source, 기존 CMB·잡음 cache, 실제 CMB 지도 10개, Gaia·Quaia 전체 입력, 전파 카탈로그 5개를 분석했다. Bianchi 배경 5개와 그 위의 조건부 복사장을 계산했고, PHY01–07에도 실제 자료 또는 해당 배경을 입력했다. 단계별 작업과 증거는 THEORY_CODING_CYCLE_RECORD.json에 있다.

60개 노드는 원본 42개, source qualifier 11개, PHY 경로 7개로 보존했다. 원래 completed_scoped였던 18개의 상태를 유지했고 새 과학 acceptance 승격은 0개다. 이번 결과는 **60개 노드에 대한 실행 경로·상류 의존성·실제 준비 계산을 확보한 것**이다. 나머지 42개 노드의 과학적 수용 조건을 모두 만족했다는 뜻은 아니다. 공동 물리 Q, Pi, F, G_F는 미결이며, 이 미결을 불가능성 정리로 해석하지 않는다.

검증에서는 R98 신규 검사 55개와 R97 회귀검사 5개가 모두 통과했다. 실제 CMB cache 검사도 포함하며 총 실행 시간은 21.10초였다. R78의 strict graph/source/authority 검사 32개도 통과했다. 이는 선택한 변경 범위의 검증이며 저장소 전체의 모든 과거 검사를 통과했다는 주장은 아니다. 정확한 명령·exit code·범위는 VALIDATION.json에 있다.

## 2. 여섯 대주제와 일곱 교차 경로

| 연구축 | 실제 R98 작업 | 주요 남은 의무 |
|---|---|---|
| P1 통계 functional·부분 식별 | 같은 2,048개 joint draw에서 공통 nuisance의 유한 slice envelope와 정확한 접점 계산 | 물리 anchor/body, 보정된 joint law, 전체 nuisance 영역 |
| P2 CMB | 999 CMB·300 noise의 grouped cross-fit, 4,995개 투영 검산, 실제 지도 10개 대조 | matched noise/systematics/foreground law와 coverage |
| P3 CF4 | table2/3/4 전체 join, 35,970개 선택 그룹의 4창·36차원 log tomography | 상류 calibration posterior, selection, correlated PV |
| P4 국소·전역 상대운동 | 전파 5개 전체 catalog·19개 cut의 Poisson/NB1/STF 비교와 유한 boost 모멘트 | LSS/selection/SED, observer/global response의 식별 |
| P5 Bianchi·Einstein–Boltzmann | 실제 배경 5개, 시간 의존 기하, passive all-m T/E/B, 화학계의 작은 응답 | radiation feedback, primordial IC atlas, anisotropic recombination |
| P6 운동학·광학 연결 | CRF3/Quaia의 10개 VSH 적합, 공통 patch, redshift·weight 대조 | 공간계통오차·AGN·frame, finite-z optical transfer |
| PHY01–07 | 누락 STF, 양의 광자 모멘트, boost, E/B Gram, Codazzi 사전, 고유선 수송, radial rank | 각 경로에 상속되는 source/model/cross-covariance의 보정 |

R78의 node.depends_on에는 118개 연결이 있고 qualification overlay가 11개 더 있다. 새 manifest는 전체 129개 hard edge로 blocker를 전파한다. 원래 ID, objective, acceptance, dependencies와 현재 effective dependencies를 함께 보존했다. SQ-CF4의 --mode science는 미해결 source law를 명시하며 기대된 exit 3을 반환한다.

## 3. SQ-CF4와 P1: 전체 자료에서 실제로 계산한 것

### Source census와 log 응답

table2의 은하 55,877개와 실제 table4의 그룹 38,053개를 이용했다. 논문 abstract의 그룹 수 38,065와 현재 저장된 table4의 행 수를 동일하게 적지 않는다. 선택 영역 0.01≤V_CMB/c≤0.1에는 35,970개 그룹이 있다. 전체 그룹 중 log 응답에 필요한 양의 값은 38,004개이고, 49개는 nonpositive다. DirectCal-only 228개 중 선택 영역에는 2개, velocity method와 겹친 DirectCal 108개 중 선택 영역에는 9개가 있다.

기존 velocity 적합과 비교하기 위해

$$
d_i=10^{(\mu_i-25)/5}\ {\rm Mpc},\qquad
y_i=\ln\!\left[\frac{v_{f,i}}
{(74.6\ {\rm km\,s^{-1}\,Mpc^{-1}})\,d_i}\right]
$$

를 정의했다. 겹치는 네 창에서 monopole 1개, dipole 3개, STF 5개를 보존해 36차원 joint covariance를 구했다. 고정 z에서 사용하는 working noise에는 250 km s⁻¹의 독립 dispersion을 채택했다. 이 항은 전체 상관 PV 법칙을 대체하지 않는다.

공통 거리계수 offset Δμ는 y를 정확히 −(ln10/5)Δμ만큼 이동시킨다. 따라서 현재 고정 z·가중치 조건에서는 monopole만 이동하고 방향 성분과 covariance는 유지된다. 실제 0.087 mag 이동으로도 확인했다. 상대 velocity-method calibration의 식별가능 rank는 5이며, common zero point와 DirectCal 방향은 별도 nuisance로 남는다.

네 창의 log-STF norm은 0.026860, 0.039792, 0.045817, 0.024384다. 같은 octant 예측과 같은 modulus 평가함수에서 RMS는 다음과 같다.

| 모형 | 예측 RMS, mag |
|---|---:|
| H03 velocity-cz | 0.458295 |
| velocity-fV | 0.457806 |
| log-cz | 0.456969 |
| log-fV | 0.456858 |

이는 작은 조건부 예측 개선이다. 상류 보정·선택 문제를 해결했다는 증거는 아니다.

### 공개 peculiar-velocity 열의 convention

실제 Vpwf 열은

$$
V_{\rm pwf}\simeq
\frac{v}{1+v/c}\log_{10}\!\left(\frac{v}{75d}\right)
$$

와 positive 전체 그룹에서 RMS 0.31333 km s⁻¹, 최대차 0.95594 km s⁻¹로 일치했다. v는 km s⁻¹, d는 Mpc이며 H=75의 단위를 위와 같이 사용한다. 선택 그룹에서 ln(v/d)에 대해 회귀한 slope는 0.43429527≈1/ln10이고 implied H는 75.0000094다. natural log와 같은 식으로 처리하면 수천 km s⁻¹의 차이가 생긴다. 이는 프로젝트의 reader·모형 convention을 고정하는 결과이며 카탈로그 오류 주장이 아니다.

### P1의 공통 nuisance와 접점 교정

같은 2,048개 joint Sobol 좌표를 네 창에 공통으로 전달했다. DirectCal ±0.5 mag의 예시 한 축 slice에서 “어느 창이든 log-STF norm>0.05”인 sharp finite count는 634–649/2048이다. 상대 calibration의 첫 Cholesky 축에서는 605–912/2048이다. 이는 조건부 working law의 한 축 유한 최적화이며, 7차원 전체 posterior나 전체 nuisance 영역의 sharp bound가 아니다.

독립 검토는 매우 가까운 두 접점에서 long-double coefficient cancellation을 재현했다. 정확한 반례 p_k(s)=(s+2⁻ᵏ)², k=40,41의 nominal/minimum/maximum mass는 각각 1, 1/2, 1이어야 한다. 선택적 exact binary-rational coefficient와 real algebraic root 처리로 교정했고, 반환된 witness를 유리수로 다시 대입해 확인했다. 실제 CF4 slice의 결론은 유지됐다.

## 4. P2: CMB cache 전체와 실제 분할 지도

999개의 component-separated CMB 실현과 300개의 noise 실현을 모두 사용했다. cmb_id%300으로 반복되는 noise genealogy를 보존하고, noise ID로 분리한 5개 fold에서 가중치와 모형을 training 자료만으로 결정했다. 각 실현은 자신의 noise 그룹이 학습에 포함되지 않은 fold에서 한 번 평가됐다.

사전에 정한 fold 0에서 noise 그룹당 하나씩 택한 60개와 관측값을 비교한 SMICA 조건부 순위는 12/61=0.196721이다. 999개 전체에서 raw score 초과는 146개이고, noise 그룹을 균등하게 가중한 초과율은 0.147222다. ridge 0.150000, diagonal 0.268611, max-TEB 0.381111로 점수 정의에 따라 달라진다. padding 경고가 있던 818번을 training과 evaluation 모두에서 빼고 다시 적합하면 raw 결과는 0.151389다. 이 값들을 동일한 p-value처럼 합치지 않는다. primary 순위도 현재 working null에 조건부이며 물리 Pi로 승격하지 않는다.

4,995개 투영을 독립 NumPy 구현으로 재계산해 C++와의 최대차 3.11×10⁻¹⁵를 얻었다. 같은 커널의 시간은 C++ 0.317초, NumPy 1.849초로 약 5.83배 차이다. 파일 I/O나 전체 pipeline의 가속률은 아니다.

실제 관측지도는 SMICA HM1/HM2/OE1/OE2, NILC HM1/HM2, SMICA/Commander/NILC/SEVEM 전임무의 10개다. NSIDE 2048 전체를 정확한 6개 mask identity의 공통 support로 변환했다. l=2…48의 반차/반합 pseudo power 비는 다음과 같다.

| Split | T | E | B |
|---|---:|---:|---:|
| SMICA HM | 0.00015546 | 0.41544 | 0.56788 |
| SMICA OE | 0.00014525 | 0.39384 | 0.56689 |
| NILC HM | 0.00025641 | 0.44535 | 0.61793 |

HM 반합과 OE 반합 사이의 T/E/B 상관은 0.999997/0.984751/0.977570이다. 편광 split 사이의 차이는 크지만 두 방식으로 합친 공통 하늘은 훨씬 가깝다. split power 항등식의 최대잔차는 5.68×10⁻¹⁴ μK²였고, 지도 10개의 계산은 638.42초에 끝났다.

로컬 Commander 신호와 관측 split은 이미 있다. 남은 것은 이에 대응하는 qualified noise/systematics/foreground 공동 법칙이다. 이번에는 Commander fullmission noise ID 00000의 실제 공식 FITS 헤더와 제한된 취득 명령까지 확보했다. 한 파일의 다운로드 준비는 전체 null calibration의 완료가 아니다.

## 5. 전파·Gaia: 여러 자료와 여러 모형의 전체 비교

### 전파

전파 카탈로그 5개의 총 21,756,972행을 방문하는 기존 reader를 재사용했다. 이 수는 서로 중복될 수 있는 카탈로그 행 수이며 독립 천체 수가 아니다. 선언된 마스크 안의 zero-count 셀도 포함하고 19개 flux cut을 모두 적합했다.

Poisson4, NB1_4, NB1_9의 spatial held-out score를 비교했다. NB1은 Var N=μ/(1−p), μ=exp(Xb)이며 training 셀의 mean/variance로 p를 정한다. Boehme 등의 compound Poisson 법칙을 사용하되 positive exp mean은 R98의 명시적 확장이다. thin QR 좌표변환으로 SUMSS의 공선성에 따른 최적화 실패를 고쳤으며 임의 ridge로 실패를 숨기지 않았다.

19개 cut 모두에서 NB1_4의 예측 점수가 Poisson4보다 높았다. STF 다섯 성분의 추가는 survey와 cut에 따라 개선되기도, 악화되기도 했다. 과산포를 포함하는 조건부 셀 법칙의 유용성을 보여 주지만 쌍극자의 우주론적 원인을 판별하려면 LSS/selection/SED 모형이 필요하다.

### Gaia·Quaia

CRF3 총 1,614,173행과 Quaia join 692,154행을 모두 방문했다. CRF3 품질 표본 1,580,645개와 Quaia 적격 표본 634,233개를 구분하여 열 가지 VSH 적합을 했다. 네 가지 Quaia 가중치 대안과 네 개 redshift bin이 포함된다. 서로 다른 가중치의 자체 χ²를 직접 비교하지 않고, 같은 inverse-noise 평가함수로 out-of-patch score를 다시 계산했다.

같은 48개 patch를 모든 적합에서 제거해 cross-covariance를 보존했다. Δ=β_A−β_B의 공분산은 C_A+C_B−C_AB−C_BA다. CRF3 전체와 품질 표본 대조의 trace는 독립가정 대비 0.000798배, CRF3 품질과 Quaia 대조는 0.02455배였다. 최저·최고 redshift bin 사이 E2/B2 차이는 8.537/6.603 μas yr⁻¹이며 trace 비는 0.4862다. 이를 우주론적 신호로 해석하려면 AGN·각도 계통오차·frame 응답을 분리해야 한다.

10×16=160차원 joint covariance의 rank는 47이다. 160차원 inverse를 계산하지 않았다. 전파의 5×3 joint 행렬은 rank 15지만 survey별 nonempty patch 수가 42/40/44/18/26으로 다르므로 공간 진단으로 제한했다. 전파 pair의 trace 비는 0.4203–1.0789로, 독립가정이 항상 보수적인 것도 아니었다.

모든 cut과 적합의 수치표 및 정확한 식은 RADIO_GAIA_THEORY_KO.md와 두 결과 JSON에 있다.

## 6. Solver 의존성을 줄인 실제 Bianchi 계산

legacy projected multipole spine, BASS의 rank 9 Thomson operator, R49 Einstein–Euler, R97의 all-m angular projection·exponential action을 연결했다. 각 배경의 같은 H, N, a, shear와 SI clock을 사용해 source와 opacity를 적분했다. 초기 a=1/1601에서 현재까지 FLRW, I, V, VIIh(h=0.25), VIh(h=−1/9)의 다섯 IVP와 signed L12 T/E/B를 구했다.

현재 모형은 명시한 초기조건과 prescribed xe에서의 passive k=0 radiation이다. 비선형 Einstein–Euler 배경과 연결했지만 radiation multipole의 feedback, primordial regular/irregular mode, 전체 I–IX atlas를 완성한 것은 아니다. 외부 solver 없이는 해당 계산을 할 수 없었던 의존성을 이 선언된 범위에서 줄였다.

| 검산 | 결과 |
|---|---|
| FLRW H의 analytic limit | 최대 상대차 4.68×10⁻⁹, T/E/B는 정확히 0 |
| Hamiltonian/(3H²) | 최대 9.37×10⁻⁹ 이하 |
| Codazzi 잔차 | 최대 4.28×10⁻⁸ 이하 |
| VIIh timestep refinement 2→4 | T/E/B 상대차 6.04×10⁻⁵ / 1.00×10⁻⁴ / 1.10×10⁻⁵ |
| L12→16 공통 low mode | 이 초기조건에서 차이 5.50×10⁻¹⁵ 이하 |

실제 source와 opacity를 유지하고 angular geometry만 고정하면 VIIh의 T/E/B 상대차는 0.01516/0.01036/1.04956이다. B의 절대차는 5.10×10⁻⁹, 기준 norm은 4.86×10⁻⁹다. 큰 상대 비율은 작은 분모와 함께 보고해야 한다.

독립 collisionless ray, Type I 기본해, Thomson 고유 projector로도 검산했다. actual H를 넣은 Peebles hydrogen의 z=1200→1000 보조 계산에서는 Δx_H(end)=5.638×10⁻⁹, Δτ=−3.766×10⁻⁷를 얻었다. 같은 Peebles FLRW 모형과 HyRec 기준의 차이가 더 크므로 이 작은 효과를 정밀 재결합 예측으로 주장하지 않는다. 이 보조 chemistry를 main sky에 feedback하지 않았다.

AniLoS/AniCLASS 원전과 exact repository HEAD를 확보했다. near-isotropic I, V, VII0, VIIh, IX에서 근사·초기조건·시각 규약을 맞춘 비교를 준비하는 용도다. exceptional VI(−1/9)의 일반 모형이나 전체 atlas 검증으로 대체할 수 없다. 핀은 SOURCE_AND_SOLVER_LOCKS.json에 있다.

## 7. PHY01–07의 실제 결과와 해석

| 경로 | 입력·구성 | 결과 |
|---|---|---|
| PHY01 | CF4 35,970개에서 STF 5열 누락 | 네 창 dipole shift norm 0.00379/0.00350/0.01596/0.02035; 누락변수 항등식 잔차 <2.78×10⁻¹⁶ |
| PHY02 | 다섯 조건부 L12 하늘의 I∝(1+T)⁴ | S−mmᵀ의 최소 고유값 ≥0.333044 |
| PHY03 | 전파 5 survey·19 cut의 조건부 boost | bolometric 모멘트의 해석식과 구적 차이 ≤2.95×10⁻¹⁶ |
| PHY04 | Gaia 열 가지 적합의 E2/B2 Gram | 전천 I₁₀/5와의 차이 ≤3.34×10⁻¹⁶; 실제 weighted E/B 상관 0.0322–0.0567 |
| PHY05 | exceptional VI(−1/9)와 인접 h | Codazzi rank 3→2→3; n→−n, A 유지 후 R90/R49 차이 ≤5.43×10⁻²⁰ |
| PHY06 | 실제 배경의 전단, 161개 시점 | 같은 Fermi–Walker triad에서 VIIh/VIh 고유선 최대각 80.57°/89.79° |
| PHY07 | 실제 CF4 radial response | 네 창 모두 rank 12; 거리를 100 Mpc로 고정하면 rank 9 |

PHY05에서는 두 구현의 structure-constant 부호 사전 차이를 확인했다. rank 정보만 이전하는 것과 signed flux를 이전하는 것은 다르다.

PHY06의 각도는 시간 의존 회전틀의 성분을 그대로 비교하면 바뀐다. 같은 normal을 따른 두 시각 사이의 수송을 넣으면 원래 각도가 복원된다. 161개 시점의 최대값과 연속시간 최대값도 구분한다. 독립 641개 시점 계산에서 VIh의 최대각은 89.970396°였다. 이 결과로 물리적 vorticity 또는 G_F의 관측값을 결정하지 않는다.

## 8. legacy 딥스캔과 과거 PR의 계승

이번에는 source·문서 본문, Python AST, legacy ZIP 내부 text payload를 읽었다. legacy root에서 physical text 1,618개, archive text 1,924개, ZIP 24개와 그 안의 member 4,320개를 조사했다. 전체 선택 root에서 byte 중복 class 776개, AST 구조 중복 class 277개를 얻었다. AST 동일성이 물리적 의미의 동일성을 증명하지는 않는다.

bass, rec_bianchi, reiBianchi, 두 Mayukh root 및 dossier PDF 8개를 연결했다. 통합 dossier의 92페이지에서 339,481자를 추출했으며 atomic, kinetic, reionization, geometry, observational, nuclear, approximation 문서의 역할도 기록했다. 크기 제한, vendor/build cache, symlink 대상 등의 제외 범위는 LEGACY_CONTENT_AUDIT.json에 명시했다. 다른 root의 모든 archive 본문까지 새로 분석했다고 주장하지 않는다.

로컬 exact Git tree의 tracked file은 34,190개였다. 이전 remote API의 32,291개 truncated tree와 구분했다. 관련 PR 33개를 다시 조회한 상태는 OPEN 23개, CLOSED 6개, MERGED 4개다. 코드가 branch에 존재하는 것과 PR이 merge된 것을 동일시하지 않았다. PR #575(R49), #576(R50), #571(R47), #549(CF4 download), #426(paired 300) 등의 OPEN 상태와 실제 재사용 내용을 기록했다.

핵심 계승은 다음과 같다.

- PR13AG projected solver의 시간적분 골격을 actual history·all-m source로 확장했다.
- masked BiPoSH의 중앙 슬롯·fsky 근사 한계를 signed 5-component Gaunt와 전체 grouped cache로 보완했다.
- pixel Gaussian의 Cholesky 구조는 활용 가능하지만 백색잡음 가정을 별도 입력 조건으로 남겼다.
- BASS Thomson의 기저 불변 rank 9 구조와 frame-transport 규약을 재사용했다.
- CF4의 bulk/catalog likelihood에서 H, log base, finite-z 응답과 calibration genealogy를 구분했다.
- rec/rei의 chemistry·trajectory operator를 실제 H에 대한 반응계로 연결하고 완전한 anisotropic closure와 구분했다.

원래 목적 → 원본 코드 → 교정 → 실제 검산 → 남은 의무의 대응과 source SHA 20개는 LEGACY_REUSE_DECISIONS.md에 있다. 보존된 원본을 기준으로 R98 adapter와 실행 모듈을 만들어 변경 원인을 추적할 수 있게 했다.

## 9. Blocker별 준비와 다운로드

21개는 서로 다른 근본 의무의 수이며 blocked node의 수가 아니다. 한 노드는 여러 범주의 의무를 상속한다. 전체 60개별 연결은 NODE60_BLOCKERS_AND_ACTIONS.md에 있다.

| 분류 | 수 | 내용 | 준비한 조치 |
|---|---:|---|---|
| DATA | 6 | CF4 상류 calibration·selection, CMB matched simulation, Gaia angular/AGN covariance, radio footprint/SED, 독립 normal flux | 입력 계약, 공식 index/header 확인, 제한된 downloader, 입수하지 못한 항목 명시 |
| MODEL | 9 | correlated PV, finite-z optics, P1 anchor, CMB foreground null, Gaia source/frame, radio LSS, local/global transfer, EB feedback/IC, anisotropic chemistry | 실제 log/NB1/shared-patch/passive-history 모형 개발, 다음 확장과 기존 solver 경로 연결 |
| ADDITIONAL_ANALYSIS | 6 | source coverage, CMB calibration, atlas convergence, cross-probe covariance, selection injection, publication/novelty | 기존 전체 자료와 여러 모형·자료를 대조하고 새 법칙을 받았을 때의 실행 조건 고정 |

공식 인덱스 6개, Commander 제품 2개의 헤더, LoTSS v1.0 table header를 확인했다. 기존 Commander 신호 ID 00000은 603,987,840 bytes 전체를 검사했고 세 채널에서 각각 50,331,648개 값이 모두 유한했다. 빠진 잡음 ID 00000의 동일 크기 제한 취득 명령은 준비했지만 실행하지 않았다. 새 full science payload는 내려받지 않았다.

ESA가 Range를 무시하면 header 뒤 stream을 닫았다. 부분 파일 재개는 실제 206과 정확한 Content-Range가 있을 때만 허용한다. 완성된 .part는 통신 없이 full hash를 확인한다. LoTSS 공식 table header와 로컬 header는 13,667,877행으로 바이트 단위로 일치하지만 웹 소개 문구는 13,664,379개다. 3,498행 차이의 원인은 확인하지 못했으며, 공식·로컬 파일 헤더의 일치와 전체 payload의 동일성을 구분했다.

## 10. 최적화·독립 검토·인계

가속에는 기존의 검증된 C++ 커널과 수학적 구조를 우선 사용했다. Gaia는 60,000행 chunk와 patch 충분통계로 메모리를 제한했고 C++ 385회, NumPy 316회를 실제로 사용했다. 전파는 최초 전체 hash·stream 이후 map과 source receipt의 identity를 검증해 재파싱을 피한다. 마지막 warm replay는 Gaia 약 10.05초, 전파 약 1.79초였다. cold I/O 시간과 순수 커널 시간은 서로 다른 측정이다.

독립 검토에서 확인된 위험은 다음과 같이 처리했다.

| 객체 | 관찰된 문제 | 교정·판정 |
|---|---|---|
| 유한 P1 slice | 가까운 접점에서 작은 양의 항이 floating coefficient에서 소실 | selective exact coefficient/root, 독립 유리수 witness 검증 |
| radio raw 감사 | 실패 뒤 seal이 먼저 갱신되어 stale map을 재승인할 수 있음 | source/map/receipt 일치 뒤에만 seal 기록 |
| radio 명시적 재감사 | 바뀐 유효 NPZ를 raw 감사로 다시 봉인할 수 있음 | 감사 분기 전에 이전 map·receipt SHA 확인 |
| signed Codazzi | R90/R49의 n 부호 규약 차이 | A 유지·n 반전 사전 확정, rank·flux 독립 대조 |
| history 고유선 | 프레임 미지정 각도와 표본 극값의 과대해석 | 두 시각의 수송 규약·표본 수·641개 시점 비교 명시 |

새 manifest의 통합 과정에서는 qualification edge 11개와 CROSS 명령의 필수 --output 인자도 확인·수정했다. 실패 기록과 교정 receipt를 함께 보존했다. 마지막 CROSS 재실행은 상류 artifact identity만 갱신했으며 과학적 payload는 이전 독립 검토 입력과 정확히 같았다.

재개점은 SQ-CF4다. 다음 과학 작업은 상류 calibration, selection, source-PV 법칙을 구성하는 일이다. 일부 자료가 없더라도 finite-z 광학 응답이나 radiation feedback처럼 독립적으로 구성 가능한 모형은 해당 계약 안에서 진행할 수 있다.

복사 가능한 지시는 HANDOFF_PROMPT_KO.md에 있다. 결과 JSON 7개, 이론 문서, legacy 조사·재사용 결정, 60-node overlay, 취득 준비, 검산 receipt와 코드를 함께 보존한다. ARTIFACT_MANIFEST.json은 baseline과 새 산출물의 exact SHA를 기록하며 Git publication 결과는 PUBLICATION_RECEIPT.json에서 분리한다. 이번 4차 종료 뒤 자동으로 5차 루프를 시작하지 않는다.

## 원전

- Cosmicflows-4: https://arxiv.org/abs/2209.11238v2 ; DOI 10.3847/1538-4357/ac94d8.
- Boehme et al., PRL 135, 201001 (2025): https://doi.org/10.1103/6z32-3zf4 .
- Vicente, Pereira, Pitrou, PRD 113, 043517 (2026): https://arxiv.org/abs/2506.07786v2 .
- Gaia-CRF3: https://arxiv.org/abs/2204.12574 .
- Quaia: https://zenodo.org/records/10403370 .
- LoTSS DR3: https://lofar-surveys.org/dr3.html .
- Planck PR3: https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html .
