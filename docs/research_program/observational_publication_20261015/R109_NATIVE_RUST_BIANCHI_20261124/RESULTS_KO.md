# R109 · 원본 Rust solver로부터 얻은 균질 CMB 하늘

## 출발점 및 물리량

htt_base의 원격과 로컬 기준은 R108 `6ca0a914d47d3c5eb4935926010970051f2008d3`이다. R104 이후의 R105–108이 추가한 SDIRK 광학 셀, LoS-계층 비교, BJS VIIh 온도 comparator, Commander 마스크 연산자와 REC/REI 데이터 이력을 계승했다. 원본 BASS 과학 브랜치의 기준은 `40ba14ce60aac47991c0af812c153ff2a358269b`이다. 이때 이미 Lie 곡률, QState의 비선형 복사 배경, Type II 편광 특성선, Rust 미시물리 adapter가 있었다. REC에는 원자 과정과 독립 HyRec 이력이, REI에는 H/He 재고와 다섯 z=4 말단 이력이 있었다. 각 원본에서 runtime 변경을 실시했다. 세 원본의 재현 기준은 [고정 버전](NATIVE_MATERIAL_PINS.json)에 있다. [BASS 3966f2a08](https://github.com/cosmosapjw-quantum/bass/commit/3966f2a0824a8b32309a8a99481dd6940b952a35) · [REC f3797f42c](https://github.com/cosmosapjw-quantum/rec_bianchi/commit/f3797f42c36632d80a67f23a4e587f0799d12cc5) · [REI 25fbae98b](https://github.com/cosmosapjw-quantum/rei_bianchi/commit/25fbae98b3d63a47dfe7200160c86a36c5f80d27).

이론 R1–R10의 [도출과 원문 위치](THEORY_KO.md)를 먼저 확정했다. 대상은 공간적으로 균질하고 현재 구현에서는 팽창하는 정상 tetrad에서의 유한 전단, 곡률, 광자, 두 cold-dust 흐름이다. 각 type은 구조상수의 초기값만 고른다. 임의 입력의 Lie 제약과 STF 조건이 성립하면 같은 진화방정식을 쓴다. 기하는 1+3 정규직교 tetrad와 대칭 무흔 텐서로 계산한다. 전송은 볼로메트릭 스크린 coherency를 광선에서 진화시키고 최종 관측자에서 스핀 조화변환한다. 각 PSTF 다중극의 유한 위계 절단을 시간진화기로 채택한 구현과 구분한다.

## 코딩 연구 C1–C10

| 루프 | 실행한 개발 | 수치 판별 또는 산출물 |
|---|---|---|
| C1 | 원본 QState와 공유 특성선을 class A/B의 임의 Σ, N, A에 노출. VIh/VIIh의 연속 h와 III/예외 VI까지 공통 경로. | 두 Lie class의 Koszul 수축, Na=0, Gauss/Codazzi 초기자료, 비대각 VIII 기저 회전. |
| C2 | 광자와 두 유한 tilt 먼지의 법선 에너지·운동량·PSTF 응력을 매 시각 Einstein 방정식에 환류. 필요한 총 q에 맞춘 동향 흐름과 순운동량 0의 반대 흐름을 지원. | 등방 먼지+복사의 닫힌 해와 Cauchy 초기조건. 계열별 아틀라스의 Gauss·Codazzi·Jacobi 기록. |
| C3 | 광자 에너지, 도래방향, 스크린 회전, 입체각 Jacobian 동시 수송. 관측자 β의 유한 Lorentz 변환 뒤에 정상화. | I형 비축 Killing 광선 2차 수렴, FLRW 관측자 도플러 쌍극자. |
| C4 | 유한 전자 속도의 편광 Thomson gain/loss를 암시적 6성분 원천으로 풀이. 전자 숙주가 잃고 얻는 4-운동량을 같은 각 격자에서 맞춤. | 유한 β 항력 계수, 두꺼운 정지 평형, 복사 에너지 98%의 숙주 검사. VIstar 48→96 스텝 B 변화 0.087% 수준. |
| C5 | 원본 REC의 cell별 proper-time 산란·가시도와 원본 REI의 유한 tilt 재고/광학 깊이를 개발. Cargo가 같은 이름의 과거 REC crate를 선택하던 문제를 정본 crate 버전과 Git rev로 수정. | 두 원본과 BASS를 같이 링크해 동일 slab의 τ를 비교. [여섯 물질 이력](MATERIAL_BRIDGE_KO.md)으로 BASS 수행. |
| C6 | 전 m의 복소 T/E/B, TT/TE/TB/EE/EB/BB, 임의 (ℓm,ℓ′m′)의 9개 directed product 구현. 명시적 유한 확률법칙 또는 SO(3) 평균에서 중심 공분산까지 출력. | HEALPix/libsharp signed-mode oracle. NumPy와 5,625개 공분산, 독립 405방향 Haar 적분 대조. |
| C7 | 12개 계열의 무산란 active, 유한 속도 tracer, 반동 active 및 같은 조건의 τ 대조. 임의 기저 VIII에서 기하·관측자를 함께 회전. | 69회 × 각 25개 signed mode. Wigner m 혼합과 6채널 Cℓ의 회전불변성. |
| C8 | REC q=0의 1,101개 x_e 절점을 BASS의 실제 고유밀도·Hubble·광학 시계에 결합. 장거리 Gauss drift에 대해 감속도에 적용하는 독립적인 Gauss-reduced 식 개발. | z=1100→0 40회. flat 및 비대각 VIII 두 방식 대조. VII0에서 시간·극각·방위각 수렴을 구분. |
| C9 | ±전단 중심미분으로 독립적인 선형 응답을 구성하고 유한 전단 하늘과 대조. 산란의 대칭 텐서 합동변환을 6×6 직접식으로 전개. | 39회, ℓ≤6. CPU 5쌍 비교에서 전체 프로그램 중앙시간 비 1.08, 모드 최대 절대변화 2.95×10⁻¹⁶ (개발 중 두 실행 파일). |
| C10 | 원본 Rust template들을 htt_base의 실제 R108 Commander 빔·픽셀·마스크 연산자 및 384자세에 통과시킴. Python 초기조건/제약과 Rust의 signed Codazzi 보고도 정상계 물리 q에 맞춤. | [12×384×15×2 투영](COMMANDER_NATIVE_PROJECTION.json), [부호 회귀 및 구 IC 영향](CODAZZI_FIX_KO.md), [60노드 대응](NODE_CROSSWALK.json). |

## 수치로 확인된 결과

- Codazzi는 정상계 물리 플럭스에 대해 Dⱼσʲᵢ+κqᵢ=0으로 통일했다. VIh의 투영 상대잔차는 2.0000000000001683에서 3.34×10⁻¹⁵로 감소했다. 비영 플럭스의 선택적 전단·곡률 재조정은 Codazzi가 고정한 전단 성분과 영공간 성분을 나누어 Gauss와 함께 풀었다. 재현한 V형에서 종전의 상대 Codazzi 오차 0.296 및 0.298이 각각 0 및 8.64×10⁻¹⁷으로 감소했다. [부호 수정](CODAZZI_FIX_KO.md) · [두 제약의 동시 해](CODAZZI_CLOSURES_KO.md). 별도 제조해 220건에서 최대 상대 Codazzi 잔차는 1.34e-15, 최대 절대 Gauss 잔차는 4.44e-16였다. [계열별 수치](CODAZZI_JOINT_FAMILIES.json).
- VIIh에서 η=0.5, bare τ=0.2, 초기 dust fraction 0.22, 정지 관측자·초기 정지 먼지를 사용했다. 초기 전단 매개변수 +0.24의 전천 ℓ=2…6 결과를 ±0.0025, ±0.005의 4차 중심미분 선형 예측과 비교했다. 모든 부호 m의 L² 오차를 유한 해의 노름으로 나눈 값은 T=0.05880, E=0.04066, B=0.13968이다. +0.03에서는 0.00733, 0.00506, 0.01756이다. 이 차이는 관측 제약이나 계열 사이의 물리적 우열을 뜻하지 않는다. BASS `research/r109_native_sky/SHEAR_RESPONSE.json`에 입력과 39회 결과를 남겼다.
- 비대각 VIII에서 두 기저로 같은 물리 초기자료를 표현했다. DOF와 관측자 부스트를 함께 회전한 결과를 독립 Wigner 변환과 비교한 정밀 격자의 상대오차는 T 1.07×10⁻¹⁴, E 7.27×10⁻¹⁴, B 3.11×10⁻¹³ 수준이다. 개별 m은 회전으로 혼합되고 m 평균은 보존된다.
- flat 광자+먼지 장거리 적분의 해밀토니안 잔차는 시간 384셀에서 6.00×10⁻³ → 2.59×10⁻⁶, 12,288셀에서 5.86×10⁻⁶ → 2.53×10⁻⁹이다. 새 식은 감속도 q_dec의 Ω를 Gauss가 주는 값으로 평가한다. 밀도·P/E·비등방응력·H의 종단값으로부터 잔차를 독립적으로 측정한다. x_e를 통한 광학깊이는 12,288셀에서 1.12442453, 독립 flat 구적은 1.12442424이다. 초기 재결합부터 오늘까지의 잔류 전자에 대한 수치 기준이다.
- 긴 VII0 계산에서 μ만 세분했을 때 남아 보인 B가 φ를 192까지 올리면 ℓ=2 BB≈1.2×10⁻³⁴로 내려갔다. 비대각 VIII 계산에서는 같은 효과가 남지 않고 BB≈1.47×10⁻¹²라는 유한 값이 확인됐다. 각도 격자가 다르고 방출·숙주 속도가 조건부이므로 계열 고유의 관측 진폭으로 사용할 수 없다.
- [Commander 계수 배열](COMMANDER_NATIVE_COEFFICIENTS.npz)의 마지막 두 축은 T/E/B와 실수 사중극 기저 5성분이다. R108의 2048 해상도 마스크·빔·픽셀 응답과 정확히 같은 kernel SHA를 사용했다. 원 천구 모드는 ℓ≤4이고 국소 관측자 boost는 이미 계산에 들어 있다. 이 배열에는 데이터 적합이나 look-elsewhere 보정 결과가 없다.

## 해석 및 재현

한 하늘에 대해 D_lm^XY=a_lm^X a_lm^{Y*}이다. 중심 공분산은 정한 확률법칙의 K이며, 균질한 하나의 배경으로부터 원시 섭동 공분산이나 계열의 관측 귀속을 정할 수 없다. T는 I^(1/4)/⟨I^(1/4)⟩−1, Q/U는 볼로메트릭 Stokes/(4⟨I⟩)다. 마스크 적용시에 붙인 등가 μK는 T_CMB=2.72548 K로 환산한 템플릿 단위다. 일반적인 분광 bandpass, Compton 열재분배, 임의 물질방정식, H=0을 통과하는 IX 재수축 및 z<4의 천체물리적 REI 이력은 별도 입력/개발이 필요하다.

아틀라스와 원본 함수/테스트는 BASS의 `research/r109_native_sky`, `_rustcore/src/homogeneous_sky`, `_rustcore/src/kinetic`에 있다. [로컬 실행 지시](LOCAL_AGENT_PROMPT_KO.md)와 [Manticore의 실제 수신 경로](MANTICORE_ROUTE_KO.md)도 함께 사용한다. 관측량의 원자료·영모형에 의존하는 R78 노드의 수용 상태는 원래 근거를 인용한다.

### 독립 수치 확인과 원 문헌

BASS 최종 Rust 소스에서 기본 테스트 181개와 확률법칙 예제 테스트 3개를 통과했다. 최종 바이너리 SHA-256은 `2f6876ecb8b03c96b2c3387d3975648983e18912c3833f20322acf6498fe22ec`이다. 69회 아틀라스와 39회 전단 대조는 이 바이너리를 사용했다. 재결합 40회 자료의 실행 버전과 최종판은 `hyrec_1100/diagnostic_sign.json`으로 연결된다. 대표 두 경우 770개 시각에서 부호를 바꾼 Codazzi 성분과 나머지 진단이 일치했고, 출력 하늘은 바이트 단위로 같았다. 원본 REC/REI CLI 6개 물질 구간 × 4개 시간분해능을 최종 Git SHA로 다시 실행한 결과는 [NATIVE_MATERIAL_SKY.json](NATIVE_MATERIAL_SKY.json)에 있다.

Challinor의 일반 시공간 1+3 PSTF 편광 전달과 Pontzen–Challinor의 near-FRW Bianchi hierarchy가 외부 비교의 기준이다. R109의 유한 배경 스크린 수송과 보존적 이산 전자 반동은 프로젝트에서 구현하고 수치 검산했다. HEALPix/COSMO와 dossier 편광 부호의 대응은 같은 도래방향과 oriented dyad에서 적용한다. [Challinor 2000](https://arxiv.org/abs/astro-ph/9911481) · [Pontzen & Challinor 2007](https://arxiv.org/abs/0706.2075) · [HEALPix conventions](https://healpix.sourceforge.io/html/intro_HEALPix_conventions.htm).
