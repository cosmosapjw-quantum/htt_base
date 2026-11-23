# R103 · 6개 연구 분야의 소스 검증과 결합 복사 solver

출발점은 연구 브랜치 `research/r69-observable-physics-bridges-20261118`의 R102 게시 커밋 `664845022a9600ad925d6c1332143395aac5ed90`이다. R102의 CF4 관측 holdout, Commander 00000, 움직이는 전자와 tilted HYREC, Lie–Stokes 계산을 재사용했다. R103에서 직접 계산한 관측량은 선택 표본의 예측 점수, 카탈로그 재적합 민감도와 제한된 모형의 복사 전달이다. 데이터에 의해 보정된 물리적 초과확률과 Bianchi 계열 귀속은 여전히 미정이다.

원래 60개 노드 모두에 의존성과 다음 행동을 기록했다. 이번 결과가 직접 연결된 노드는 새 결과 파일이 연결된 10개와 교차 유도를 수행한 7개를 합친 17개다. 기존 판정은 범위 한정 완료 18개이며, 새 과학 수용 판정은 0개다.

## 분야별 결과

| 분야 | 이번 계산과 해석 | 남은 입력 또는 계산 |
|---|---|---|
| P1 · 텐서와 다섯 관점 | CF4의 같은 2,048개 추출에서 4창의 결합 비트 패턴을 셌다. 겉보기 STF/H 문턱 0.05에서 2개 이상 동시 초과 137개, 3개 이상 0개다. 주변 빈도·합집합·교집합만 보존한 경우의 sharp 구간은 각각 [126,137], [0,11]이다. | 실제 광학적·물리적 매핑 및 공통 척도가 정의되어야 물리적 Π를 산출할 수 있다. |
| P2 · CMB 저다중극 | PR3 Commander signal+noise 00000의 T/E/B 조화계수를 각각 구해 합산했다. 서로 다른 I/P 마스크로 TT, EE, BB, TE, EB, TB를 모두 계산했다. 기존 직접 지도합과 겹치는 ℓ=2…8에서 최대 절대차 2.274×10⁻¹³ μK². | 300개 matched noise 실현, 관측·MC 유효 beam, foreground 및 통계량별 coverage. |
| P3 · 방향·적색편이에 따른 팽창 | 6dFGSv 8,885행·7,190개 고유 선택 매치. 5-fold에서 훈련·검증 군에 같은 잠재 속도장을 적용하면 PGC Δlog 예측점수는 30.7511→25.2437, PGC1은 26.7070→25.4893. PGC의 한 fold는 +0.4144→−5.0638. 2,666개 군 소속 행에 group cz를 적용하면 합은 24.8652, 24.9233이다. | 독립 영점, 원래 선정·탈락 확률, 동일한 35,970개 군과 창에 정합한 속도장 법칙. 선택 코호트 내 교차검증의 점수를 외부 검정의 Bayes factor로 해석할 수 없다. |
| P4 · 국소 부스트와 전역 tilt | 겹치는 NVSS 241,892개 성분에서 peak/integrated 분류 대비를 약화시키는 최소 PSD 공분산을 유도했다. 쌍극 단독 모형은 95% working contour까지 무차원 RMS 0.00214123, STF nuisance 포함 시 0.00211490. | LSS·완전성·소스 형태 공분산의 경험적 추정, 공동 observer frame. |
| P5 · Bianchi 계열 | 유한 ℓ 전체에서 움직이는 Thomson gain/loss를 각 암시적 단계에 적용했다. 독립 4차원 응력에서 확인한 전단 적색편이 항을 복원하고 collisionless 무질량 중성미자와 광자를 각각 진화시켰다. 둘의 초기 분포, 에너지, 운동량, 압력 피드백을 일치시키고 바리온 반동은 광자에만 연결했다. | 질량 있는 중성미자, 일반 초기 모드, 독립 Einstein/열이력과 열린 곡률 다중극 비교, 관측 likelihood. |
| P6 · 공통 congruence의 운동학 | Quaia 634,233개 천체에서 저장한 정상방정식을 네 적색편이 구간에서 재적합했다. 48개 개별 하늘 패치와 1,128개 패치 쌍을 제외했다. E2 곡률 norm은 낮은/높은 z 조합 23.44/12.11, 대응 delete-two RMS 27.58/20.50 μas yr⁻¹ per z². B2도 두 구간 모두 패치 변동보다 작았다. | 비선형 AGN·스캔·광학 오차와 측정 프레임의 독립 공분산. |

PHY-01…07의 개별 유도와 수치표는 `CROSS_ROUTE_BOUNDS_KO.md`에 있다. 예를 들어 PR3/PR4 유한 대역의 부호 있는 복사 STF를 양의 단축 대칭 템플릿에 최적 적합해도 Frobenius norm의 70.72%/70.31%가 남는다. 이는 지정한 프레임·대역·노름의 기하학적 잔차다. 데이터 검출 유의성을 얻으려면 같은 추정량의 null을 전파해야 한다.

## 물리와 수치 구현

정상 tetrad의 부호는 $(-+++)$, 외향 하늘 방향은 $\hat n$, 광자 진행방향은 그 반대다. $\beta=v/c$이며 $N=\ln a$이다. 광학깊이는 양의 산란량이다. 상세 유도는 `NATIVE_EQUATIONS.md`, `REC_REI_THEORY.md`에 있다.

1. **전단과 강직 충돌.** 등방 배경의 $a^{-4}$ 감쇠를 분리한 볼로미터 밝기 $J=1+4\Theta$에 대해 광선 위에서 $\mathrm dJ/\mathrm dN=-4(\sigma_{ij}n^in^j/H)J$이다. 상수항만 구현할 경우 유한 tilt에서 $\mathrm d(q/E)/\mathrm dN$의 부호까지 틀리는 반례를 얻었다. 전단이 재분포시키는 기존 밝기의 곱셈항을 복원했다. Thomson gain은 차수 9 이하의 각 모멘트로, loss는 방향에 의존하는 희소 연산자로 계산한다. 이전 셀 시작점의 보정값과 낮은 ℓ 절단을 대체했다.
2. **Class B 재결합.** $D=\Gamma n_{H,\mathrm{rest}}$에 대한 전류 보존으로 $\mathrm d\ln(Da^3)/\mathrm dN=2(a_i/H)\beta^i$를 얻는다. 여기서 $a_i$는 저장소 구조상수의 벡터 부분을 시간율로 환산한 값이다. 광선별 Sobolev 기울기에 정지계 전단과 가속도를 포함했다. 방향 기울기의 최소값이 0에 닿으면 단일 공명 모형의 적용이 끝난다. 양의 광학률 보간과 셀 적분으로 $\sum_j p_j+\exp(-\tau)=1$을 보존한다. 광학률에 임의의 양수 바닥을 넣지 않는다.
3. **REI 실자료 인계.** 별도 REI 저장소 `56dc609ea9b801c88d3364aed3eee140b3a20d46`의 5개 물질 이력·5,005개 표본을 바리온 정지계 $n_e=n_H x_{HII}+n_{He}(x_{HeII}+2x_{HeIII})$로 읽었다. 평균 적색편이 20→4에서 $\tau(q=0)=0.03196820305$, $\tau(q=+0.01)=0.03196794375$. $|q|=0.005,0.01$에서 짝수 변화가 −6.4825×10⁻⁸, −2.59295×10⁻⁷이다. 두 수치의 부호 대칭과 약 4배 변화는 이 다섯 모형의 유한차분이다. 관측자까지의 전체 광학깊이나 외부 관측에 맞춘 재이온화 이력으로 채택하는 데에는 추가 자료가 필요하다.
4. **독립 수송.** AniCLASS가 제공한 closed IX regular tensor의 초기 T/E/B, 계량 소스와 산란률로부터 BASS가 네 후속 시각을 예측했다. $z=1601.419$에서 오늘까지 515셀의 peak-normalized 오차 T/E/B는 $5.52\times10^{-6},4.63\times10^{-5},1.20\times10^{-5}$였다. 별도 독립 해의 원래 방정식과 코드, 상대부호, 등각 거리의 단위는 `SIGNED_REFERENCE.md`, `CLOSED_TENSOR_HISTORY.md`에서 추적할 수 있다. 시계열을 공급한 비교이므로 BASS 자체의 열·계량이 독립 cosmological solver에 일치하는지는 열린 문제다.

강한 기울기 $|\beta|=0.90554$의 고정 편광 분포에서는 Thomson 사힘의 상대오차가 GL 16링에서 $7.99\times10^{-4}$, 32링에서 $5.26\times10^{-10}$였다. 32링은 이 시험에서 $10^{-8}$을 만족한 최소 시험 격자다.

## R1–R10 · C1–C10 실행 근거

| 단계 | 이론에서 얻은 결과 | 계산·코딩에서 수행한 작업 |
|---|---|---|
| R1 / C1 | 6개 논문과 R78 60노드의 acceptance를 기존 R102 측정과 대조 | 로컬 HEAD·원격 ref·부모 tree를 대조하고 기존 연구 브랜치에서 진행 |
| R2 / C2 | Dropbox의 kinetic transport·recombination·reionization dossier와 근등방 수송 원전에서 부호·프레임·시계 규약 식별 | 6dF/CF4·Quaia·PR3·REI donor·AniLoS/AniCLASS의 실제 코드·원자료 경로와 해시를 수치 결과에 연결 |
| R3 / C3 | 외향 하늘과 광자 진행 방향, 조건부 관측 점수와 물리적 calibration의 범위 확정 | log-sum-exp holdout, 단계별 low-rank 충돌, 보존형 셀 적분 및 finite-source 보간 설계 |
| R4 / C4 | 공유/새 속도장, 단일/분리 복사종, source-only/완전한 볼로미터 항의 판별 가능한 예측 구성 | 군 단위 5-fold, 같은 하늘 패치 삭제, 열림/닫힘 IC·전송 검증을 독립 실행 |
| R5 / C5 | 수소수 연속식, 유한 셀 가시도, 부스트한 분포의 q/E·π/E, 템플릿 노름 및 공분산 한계 유도 | 기존 결합 solver·4채널 HYREC 진입점과 CF4·자료 취득/축약 코드 수정 |
| R6 / C6 | 직접 각적분·4차원 응력·Wolfram 대수식·독립 소스 기저와 부호 대조 | 정상 입력, 틀린 frame/support/identity, 희박한 종, 중단·동시 저장을 회귀 시험 |
| R7 / C7 | pure shear의 미분 반례 및 closed IX의 비가환 산란/회전으로 구현 간 차이를 판별 | 실자료 재적합, 7계열+VIIh 양방향, 독립 AniCLASS 다중극, 다섯 REI 시나리오 실행 |
| R8 / C8 | 단계적 수렴과 자료 의존성을 분리해 해석 | 시간·Picard 반복 세분화, 실자료 Commander 두 변환 비교, 같은 정확도에서 HYREC RHS 최적화 측정 |
| R9 / C9 | 채택한 식·IC·단위·유효영역을 재현 문서에 연결 | 독립 검토에서 class-B 밀도, Sobolev Jacobian, 광자/중성미자 분리, 높은 tilt 각격자와 flux 불일치를 확인·수정 |
| R10 / C10 | 전달 계산과 관측 귀속에 필요한 남은 가정을 고정 | 실제 측정·소스 해시·실행 명령·로컬 분석 인계와 결과를 같은 연구 브랜치에 보존 |

### 통합 회귀와 해상도

워크스테이션에서 충돌·재결합·수송 모듈과 CF4·Commander 등 관련 시험 1,143개와 하위 시험 5개가 통과했다. healpy의 기존 `verbose` 인자 사용에 대한 폐기예정 경고 1건이 있었다. 최종 코드로 R102의 4차원 null geodesic/Sachs 및 결합 수렴 검사를 재실행했다. 160셀·2 substep에서 320셀·4 substep으로 바꾼 최종 결합 상태의 상대차는 VIIh 0.0014893, VI₋₁/₉ 0.00002560, IX 0.00046841이었다. 이는 기본 단일 복사종·작은 비등방 초기조건에서 얻은 값이다. 같은 실행의 광선/각수송 비교는 5개 계열에서 분리된 짧은 무충돌 방향·편광 수송을 검사한다. 전 구간의 독립 우주론 검사는 별도다. 입력과 수치표는 `NATIVE_CONVERGENCE_REPLAY.json`에 있다.

### 출처와 다음 입력

- Dropbox `/dossier/Dossier_II_Kinetic_Transport.pdf` rev `65dd5afc2e7920af03d47`, `Dossier_IV_Reionization.pdf` rev `65dd5afd21dc50af03d47`, 통합본 `BASS_Integrated_Dossier.pdf` rev `65dd5afc2e7910af03d47`; 이전 recombination 검증본 `/bianchi/Mathematical_Verification_Dossier_III_Recombination.pdf` rev `65b3f27c2fcdb0af03d47`.
- Pereira & Pitrou의 FLRW 극한이 있는 계열에 대한 선형 대응과 Vicente·Pereira·Pitrou의 Boltzmann 계층·observable 변환. [Bianchi spacetimes as super-curvature modes](https://arxiv.org/abs/1909.13688) · [CMB line-of-sight integrators](https://arxiv.org/html/2506.07786v2)
- PR3 모의지도는 독립 signal/noise 성분과 실제 기기 효과를 포함한다. 데이터의 beam HDU 유무만으로 MC beam을 지정하지 않는다. [Planck 2018 I, Appendix B.3](https://doi.org/10.1051/0004-6361/201833880)
- CF4를 조건으로 얻은 추정 속도장과 외부 2M++ 복원은 서로 다른 조건부 모형이다. Valade 등의 HMC 필드는 저자 요청 방식이며, Manticore-Local은 총 80개의 z=0 밀도·운동량 실현을 공개한다. 이 회차에서 Manticore 미러 연결은 시간 초과였다. 워크스테이션 전용 다운로드 환경의 설치·패키지 로딩·의존성 검사를 마쳤다. 실제 field draw는 0개이며, 35,970개 군의 투영 준비를 완료했다. [CF4 HMC 데이터 이용 조건](https://www.nature.com/articles/s41550-024-02370-0) · [Manticore 공식 자료](https://digitaltwin.fysik.su.se/data-access.html)

원자료 분석은 `HANDOFF_LOCAL_KO.md`에서 시작한다. 각 지표의 물리적 의미, 확인된 commit 및 재현 명령은 동봉된 개별 결과와 `VALIDATION.json`에서 확인할 수 있다.
