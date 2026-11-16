# R54 보고서 — 심사, 이론 루프, 실행 결과 (2026-11-16)

브랜치 `research/r54-tensor-frame-tomography-20261116` (base `research/r50-observed-convergence-20261115`). 주장 상한 C0. 이 문서의 모든 수치는 `RESULTS/*.json`에서 생성된다.

## 1. 심사 결과 (출판가능성)

**권고: Major revision. 현재 상태로는 R53의 "bounded note"가 맞고, 방법론+발견 논문은 성립하지 않는다.**
R54에서 방어 가능한 내용은 세 가지다: (i) 모델 라벨이 붙은 CMB 범함수 한계와 그 모델 의존성, (ii) CF4 추정량 편향과 카탈로그 수준 LCDM body, (iii) zero-point 모형 의존성을 그대로 보고하는 진단표.
로컬 보정(R54-L01, R54-L04)을 통과하면 bounded note를 확장한 JCAP/PRD급 관측-방법 논문 한 편은 방어 가능하다. 새 물리 검출 주장은 없다.

강점
- 프레임·epoch 타입을 강제하는 선형-가우스 carrier 계층. R49의 Sigma 대 sigma/H0 혼동 같은 오류를 타입 오류로 만든다.
- 유한 MC 공분산 법칙의 held-out 보정(R51-R53)과 음성 결과의 보존.
- 식별 불가능 방향(omega, A)을 prior로 덮지 않고 보고한다.

치명적 약점
1. R52 관측 결합에서 5변수 중 Q, F, Pi가 UNAVAILABLE이었다. R54에서 CMB lane은 다섯 뷰가 모두 채워졌다. 저적색편이 lane은 x, Q, Pi, G_F만 채워지고 F는 UNAVAILABLE로 남는다(축 스캔은 support 범함수가 아니다).
2. 5변수 뷰는 정보를 더하지 않는다(R53 정리: exact likelihood와 tie). 보고 규약이지 새 통계량이 아니다. 기여는 타입화된 보고, 식별성, transport 검정에 한정된다.
3. R51의 조건부 (sigma/H)_0 한계는 perfect-fluid 가정에 묶여 있었다. 복사 비등방 stress, 중성미자 질량, 초기 상태에 따라 부호와 크기가 바뀐다(2.1).
4. PR3 저-ell 편광은 B-모드 null을 통과하지 못한다. E lane은 진단용이다.
5. CF4 lane의 추정량(거리에 선형)이 편향돼 있었고 공분산에 우주 속도장 항이 없었다. 둘을 고친 뒤의 결론은 zero-point nuisance 모형에 따라 달라진다(2.3). 선택 함수와 보정 공분산은 모형에 없다.
6. Type I 밖의 Bianchi family는 source-bound transfer가 없어 평가 불가다.
7. 선행연구와 겹친다: kernel 계(E46), CF4 zero-point dipole(E09, E33), 카탈로그별 log-distance dipole(E43), CF4 팽창률 다중극(E16), dipole anomaly 종설(E19).
8. 분석 선택 일부가 사후적이다(반구 분할 축, 공통 적색편이 구간, 판정 규칙). `THEORY_LOOPS.md`의 forking-path 목록에 기록했고 스캔 보정 꼬리를 함께 보고한다.

수정 우선순위
1. R54-L01: T+E 추정량 LOO 보정과 masked E 응답.
2. R54-L04: CF4 survey별 zero-point 분리와 nuisance 변형(반경 기울기, 은하 위도, 거리 오차항). 분류가 모형에 무관해지는지 판정한다.
3. R54-L02: PR4 없이 편광 공분산 삼각검증.
4. R54-L03: count dipole clustering body와 동일 추정량 null.
5. R54-L06/L07: 결합 프레임 단층과 적대적 벤치마크, 그 뒤 R54-L08 결정.

## 2. 여기서 실행한 결과

### 2.1 CMB: type-I shear history의 두 범함수 (R54-L1)

- 닫힌형 kernel: K_T = (6e^-tau + e^(-3tau/10))/7, K_E = (sqrt6/7)(e^(-3tau/10) - e^-tau). SymPy 봉인, ODE와 단위시험 허용오차 안에서 일치. E46(Basko & Polnarev 1980)이 푼 계의 재유도이며 새 결과로 주장하지 않는다.
- T와 E 사중극은 shear history의 서로 다른 선형 범함수 Sigma_T, Sigma_E를 잰다. kernel은 이온화 history만으로 정해지고 shear 동역학과 무관하다.
- Perfect fluid: Sigma_T/s0 = 35956 (R51 sharp 연산자 39267의 0.9157배), r_E = Sigma_E/Sigma_T = 0.0711. E의 18%가 재이온화 산란 몫이다.
- 복사 비등방 stress: 광자만 넣어도 부호가 뒤집힌다(s0/Sigma_T = -0.000244). 광자+중성미자 2-모드 족에서는 s0 = c_T Sigma_T + c_E Sigma_E이고, 무질량이면 (c_T, c_E) = (0.00166, -0.0254), 최소 정상 질량순서(0, 0.00868, 0.0503 eV; R54-EQ-06의 무충돌 stress 가중)이면 (0.000858, -0.0147)다.
- 초기 상태 sweep(중성미자 분리 시점 z_i = 1e+09~3e+10): 자유 흐름 시작을 z_i = 1.5e+10 (T_nu = 2.5 MeV)와 2e+10 (3.4 MeV) 사이에 두면 초기 shear 단위당 Sigma_T의 부호가 바뀐다. 이 구간은 뮤온·타우 중성미자의 분리 온도 추정 3.12 MeV(E49; 전자 중성미자 1.87 MeV)를 포함한다 (부호 변화 전 r_E = 0.050~0.109, 전체 8점에서 -1.057~0.109). 초기 상태에 따라 T 범함수 자체가 0을 지난다.
- 데이터(커밋된 PR3 carrier, FFP10 N=300, 주 carrier TE_l2): sd(Sigma_T) = 9.36e-06, sd(Sigma_E) = 6.1e-08; 전체 Wald 통계량 9.88, p = 0.48 (hotelling_T2(p=10,n=299)). 검출 없음.
- 95% 한계(Frobenius): |Sigma_T| <= 4.1e-05, |Sigma_E| <= 3.76e-07 (B-null floor 5.01e-07, Commander 3.41e-07).
- 방향별 동시 95%: |n.Sigma_T.n| <= 3.26e-05. 재결합 이후 방향별 누적 팽창 차이의 상한이다.
- 현재 shear |sigma/H|_0의 95% 예시값: perfect fluid T만 1.14e-09; perfect fluid T+E 1.42e-10; 무질량 2-모드 족 6.65e-08; 최소 정상 질량순서 3.43e-08. 한계가 아니라 모델 의존성의 예시이며 모델 라벨 없이 인용할 수 없다.
- 후기 shear: z < 0.2에 국한된 shear에 대해 T 범함수는 부호가 일정한 history는 제한하지만(한계 0.000225) 부호가 바뀌는 history에는 감도가 없다. 그 rms에 대한 E 범함수의 한계는 0.0729(B-null floor 0.0972)뿐이다(진단 lane). z < 0.5면 0.0112, z < 2면 0.000692. 후기 비등방 stress가 있으면 "CMB가 저적색편이 shear를 배제한다"는 문장은 성립하지 않는다(H-L3c 기각, 조건부 진술 H-L3d).
- B-null gate 실패: SMICA p = 9.54e-06, Commander p = 3.96e-07 (관측 rms 0.30 대 FFP10 0.11 uK). E ell=2는 통과(p = 0.25). E lane 수치는 진단용이다.
- R51 재현: T45 LOO tail 0.884; LOO sd/plug-in sd = 1.1546, 정확한 Wishart 식 1.1547. R53의 식은 이보다 약간 커서 보수적이었다. p = k인 주 carrier는 보정 계수가 1이고 꼬리는 Hotelling 법칙이다.

### 2.2 저적색편이 1차: 커밋된 R36 multipole + ideal-sky body (R54-L5) — CF4 부분은 2.3으로 대체됨

- Ideal-sky body null: dipole p = 5.71e-05, quadrupole p = 1.07e-05; 템플릿 최적 축이 적도 극에서 2.8도, 하늘 비율 0.0005.
- 이 1차 결과는 "적도 극 고정"으로 읽혔으나 추정량 편향과 과소한 body 위에 서 있었다. 2.3에서 다시 쟀다.
- Count dipole(커밋된 receipt): 운동학적 기대 대비 초과 tail p = 0.27 (Quaia), 0.46 (NVSS); 공통 초과 p = 0.12. 그러나 이 추정량이 운동학적 dipole의 2배인 dipole을 5% 수준에서 잡을 확률은 0.20이다. 판정 불가이며(H-L2a HOLD) 공개된 anomaly의 반증이 아니다.

### 2.3 저적색편이 2차: CF4 카탈로그 수준 분석 (R54-L05, 커밋된 35970 group으로 여기서 실행)

저장소에 CF4 source 행과 R36 연산자 백업이 커밋돼 있어(해시 일치) 로컬 드라이브 없이 실행했다. R36 연산자는 source에서 8.13e-20 오차로 재구성된다.

교정 1 — 추정량. R36/H03 추정량은 c z를 잡음 있는 거리 d에 선형 회귀한다. 같은 추정량 null(FLRW 거리 + 거리지수 오차 + 250 km/s)에서 이 추정량은 스스로 다중극을 만든다.
- 편향이 극 방향 dipole의 14-40%를 차지한다. 편향을 빼면 quadrupole null p와 극 하늘 비율이 바뀐다(p: 0.00343 → 0.129; 하늘 비율: 0 → 0.0755).
- 대체 추정량: eta = ln[H0 d_L(z)/d]를 [1, n, STF5]에 가중 회귀(R54-EQ-34). 거리지수에 선형이라 가우스 오차에서 불편이다(단위 시험으로 확인). 창별 H = 75.7-76.7 km/s/Mpc.

교정 2 — body. 35970^2 쌍 전체에 대한 선형 LCDM 속도 상관 pair-sum(R54-EQ-30/31/37; sigma_v = 309 km/s).
- Exact/ideal 표준편차 비: dipole 1.00-1.61, quadrupole 1.15-1.93. Ideal-sky body는 과소였다.

교정 후 결과 (log 추정량 + exact body). 조건: 선형 이론, 선택 함수 없음, 보정 공분산 없음.

Zero-point nuisance 모형별 요약. 세 모형 중 어느 것도 선험적으로 우선하지 않는다.

| nuisance 모형 | dipole null p | quadrupole null p | joint null p | 극 이득 | 극 고정 꼬리 | 규칙상 분류 |
|---|---|---|---|---|---|---|
| pooled (없음) | 0.001 | 0.017 | 0.000344 | 30.6 | 0.0242 | EXCESS_NOT_POLE_LOCKED |
| 방법별 monopole | 0.062 | 0.0029 | 0.00277 | 25.8 | 0.0085 | UNRESOLVED_POLE_LOCKED |
| 방법 x 반구 계단 | 0.598 | 0.0296 | 0.112 | 10.0 | 0.147 | LCDM_BODY_COMPATIBLE |

- 종합 분류: DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL. 극 고정 꼬리는 exact body에서 뽑은 null 4000회로 보정한 하늘 비율 꼬리다.
- "방법 x 반구 계단" 모형은 반구 방향 자체를 nuisance로 빼므로 dipole 초과가 사라지는 것은 거의 자동이다. 증거로 쓰지 않는다.
- pooled null의 chi2: dipole 32.9/12, quadrupole 35.6/20, 합 66.3/32. Damped body p = 0.000155; body를 2배로 하면 p = 0.188.
- 창별 분해(pooled): 안쪽 두 창(z = 0.025, 0.04) joint p = 0.00558 (dipole 0.0375, quadrupole 0.0411); 바깥 두 창(z = 0.06, 0.08) joint p = 3.89e-06 (dipole 0.000123, quadrupole 0.00109). 방법별 monopole 모형에서는 0.00796와 6.64e-05. z >= 0.055 표본은 FP가 98%이고 그 FP의 95%가 북반구다. 바깥 창의 dipole은 사실상 북쪽 FP와 나머지의 비교다.
- 극 고정 판정의 검정력: 관측 크기(0.036 mag)의 반구 계단을 주입해도 pole_locked 판정이 켜지는 비율은 17%뿐이다(주입 없음 1%). 꼬리가 0.01보다 크다는 것이 "고정 아님"을 뜻하지 않는다. "고정"도 "고정 아님"도 주장하지 않는다(H-L5c HOLD).
- 축(pooled): 적도 극 이득 30.6, 은하 극 30.4, 최적 축 (l,b) = (252, 79)로 적도 극에서 70도.
- 깊이 법칙: pooled에서 상수 분율 dipole chi2 = 10.4/9, 속도 법칙 chi2 = 16.2/9. 방법별 monopole을 주변화하면 차이가 사라진다(6.7 대 7.3).
- 상수 dipole(pooled): H의 3.1% (0.065 mag), 극 축에서 25도; 극 평행 성분 -2.76 +- 0.73% (북쪽이 낮다), 수직 성분 p = 0.0461.
- 지표별 dipole (z = 0.01-0.055): white 오차로는 p가 8.04e-29(TF)까지 내려가지만 exact body를 넣으면 FP 0.806, TF 0.19, SN 0.0873, OTHER 0.1. 네 family는 하나의 공통 벡터와 양립하지만(일치 p = 0.198) 그 공통 dipole 자체는 유의하지 않다(Wald p = 0.43).
- 방법별 반구 계단 s (eta = z-bin monopole + s sign(dec)), exact body 오차: FP -1.66 +- 0.57%, TF -1.96 +- 1.05%, SN -1.65 +- 0.65%, OTHER -2.22 +- 0.91%. 공통 계단 -1.66 +- 0.53%, 일치 p = 0.867. 등가 거리지수 차 (북-남) 0.072 +- 0.023 mag.
- 반구 분할 축 스캔(exact body, z < 0.055의 18351개, 축 151개): sign(dec) 축은 1차 분석 뒤에 골랐으므로 단일 축 꼬리(0.0017)만 인용할 수 없다. 스캔 최대값의 꼬리 = 0.0339. 천구 극은 151개 축 중 |z| 순위 1위이고, null에서 최적 축이 극 10도 안에 올 확률 = 0.02. 네 family 추정은 body를 공유한다(최량 단일 family 분산 / 공통 계단 분산 = 1.15; 독립이면 4).
- 계단(z < 0.055)과 창 초과(바깥 창이 더 강함)는 서로 다른 측정이다. 하나가 다른 것을 설명한다고 쓰지 않는다.
- 선행연구 대조: E43(Nusser & Tully 2026)은 log-distance 추정량으로 구성 카탈로그별 dipole을 재서 TFR과 6dFGS가 SDSS와 SN보다 크다고 보고했다. Family 수준에서 계단 크기가 같은 것은 서로 다른 원인(FP 안의 6dFGS 대 SDSS zero-point, 얕은 TF/SN 표본의 국소 유동)의 일치일 수 있다. "공통모드" 해석은 보류(H-L5g HOLD)이고 수치만 보고한다.
- 상수 quadrupole: H의 2.5%, Wald p = 0.000146(방법 x 반구 계단 모형 0.000489). 사후 통계량이며 주축이 모형에 따라 바뀐다. 보류.
- Jackknife(적도대, 북극관, 남극관 제외): 극 dipole -3.6% ~ -3.1%.
- 주입 시험(실제 footprint, exact body 잡음; 상수 법칙 선호 비율, 계단 주입 / 유동 주입): 0.05 mag와 300 km/s에서 93% / 24%; 관측 크기(0.036 mag, 371 km/s)에서 82% / 20%; 방법 monopole 연산자는 관측 크기에서 83% / 22%. 관측 크기에서는 두 법칙이 결과를 보기 전에 정한 기준(90% / 10%)만큼 갈리지 않는다(H-C3 HOLD).
- Bulk-only 벤치마크: white 오차면 283 km/s, E10 방향에서 11도(재현). Exact body면 371 km/s, (l,b) = (310, -44).
- Global tilt 닫힘 시험(R54-EQ-38, 예비): V_CF4 + c beta_excess = 0의 p = 0.0895 (V만), 0.0123 (상수 dipole 주변화). Count 쪽 검정력이 낮아 예비 수치다(H-L6b HOLD).
- 판정 규칙의 지위: 규칙과 임계값은 exact-body 수치를 보기 전에 코드에 넣었으나 커밋하지 않았으므로 사전 등록이 아니다. 물리적 방향 의존 Hubble 인자나 A_a의 검출이 아니다. 상수 dipole은 거리 zero-point dipole과 분리되지 않는다(H-L3b). 남은 질문은 survey 수준 zero-point와 nuisance 변형에서 분류가 하나로 모이는가이고 R54-L04가 답한다.

### 2.4 데이터 없이 증명한 진술 (R54-THM, `THEOREMS.md`)

신규성 주장에 필요한 항목 가운데 통계학과 수리물리만으로 닫히는 것을 증명했다. 각 진술은 `tests/r54/test_r54_theorems.py`에 실행 가능한 검사를 가진다. 증명은 아직 독립 심사를 받지 않았다.

- T1 (검정력): 충분통계량 논리로, carrier의 어떤 함수·압축·재좌표화도 exact likelihood의 검정력 한계를 넘지 못한다. R53에서 잰 tie는 정리다.
- T2, T3, T4 (타당성): 특이 precision의 신뢰 원통은 rank(F) 자유도로 정확한 coverage를 가지며 거기서 읽는 모든 뷰가 동시에 유효하다. 비식별 방향에서는 유효한 신뢰집합이 비유계이고, 유계 구간의 균등 coverage는 0이며, posterior는 조건부 prior와 같다. 고전 결과이고(E53, E55, E64) 우주론은 같은 목적에 profile likelihood를 이미 쓴다(E57, E58).
- T5 (유한 시뮬레이션 공분산): GLS 추정의 정확한 2차 모멘트 계수.
- T6 (선택 규칙): O(3) 등변성 아래 1차 응답은 (다중극, parity) 블록으로 대각이고 식별성은 블록별 rank 진술이 된다. vorticity는 어떤 스칼라 관측량에도 열이 없고 toroidal 고유운동 dipole에만 나타난다. B_2는 null 채널이다. 유한 파장 모드와 parity를 깨는 측정 사슬에는 적용되지 않는다.
- T7 (gauge 궤도): 깊이와 무관한 Hubble 다중극은 거리 표본들의 zero-point 패턴 공통 부분과 분리되지 않고, vorticity는 기준 좌표계의 spin과 분리되지 않는다. "물리적 dipole 없음" 가설은 상대 거리만으로는 검정할 수 없다.
- T8 (shear history 모멘트 문제): T와 E의 kernel은 Chebyshev 계를 이룬다. T에 보이지 않는 history는 부호가 한 번 이상, T와 E 모두에 보이지 않는 history는 두 번 이상 바뀐다. 부호나 family 제한이 없으면 shear 진폭의 상한은 없다.
- T9 (프레임 대수): 같은 shell의 count 초과와 bulk flow의 합은 항등적으로 0이다. Global tilt는 shell 사이의 선형 가설이다.
- 신규성: 통계 부분은 주장하지 않는다. T6과 T8은 구성 요소가 모두 문헌에 있고(E18, E25, E46, E50, E51) 하나의 진술로 묶은 형태는 이번 검색에서 찾지 못했다. 검색에 걸리지 않았다는 뜻일 뿐이며 R54-L07이 확인한다.

## 3. 주제별 결정

| 주제 | 결정 | 근거 |
|---|---|---|
| 증명된 진술 | PROMOTE (H-T1, H-T2, H-T6, H-T7, H-T8, H-T9; 신규성은 주장 없음 또는 미검증) | 2.4, THEOREMS.md |
| 핵심 계층 | PROMOTE (H-C1 보고 규약), REJECT (H-C2 검정력 이득), HOLD (H-C3 깊이 법칙 분리) | 2.3, state/HYPOTHESIS_GRAPH.md |
| 저-ell 형태와 물리량 | PROMOTE (H-L1a 범함수 재유도, H-L1b 모델 의존성), REJECT (H-L1c 편광 액면 사용, H-L1d ell>=3의 type-I 해석) | 2.1 |
| Dipole anomaly | HOLD (H-L2a 검정력 부족, H-L2b clustering body), REOPEN (H-L2c counts 대 CF4 프레임) | 2.2, 2.3 |
| Beyond-FLRW 운동학 측정 | PROMOTE (H-L3a, H-L3b: R52에서 승계한 구조적 식별성 진술; H-L3d: 조건부), REJECT (H-L3c: 조건 없는 진술) | 2.1, state/HYPOTHESIS_GRAPH.md |
| 비등방성 분류 | HOLD (H-L4a: 불변량의 null 보정 없음; family 식별은 차단 유지) | state/HYPOTHESIS_GRAPH.md |
| 방향·적색편이 의존 Hubble | REJECT (H-L5e 물리적 검출), PROMOTE (H-L5f 추정량 편향), HOLD (H-L5a body 초과, H-L5c 극 고정, H-L5g 공통 계단, H-L5h 상수 quadrupole) | 2.3 |
| Local boost 대 global tilt | HOLD (H-L6a 깊이 법칙, H-L6b 단일 global tilt, H-L6c map 수준 aberration) | 2.3 |

## 4. 텐서화 5변수의 역할

x는 부호 있는 precision-form carrier (F, t), Q는 선언된 body의 gauge 범위, F는 방향별 support 비, Pi는 이름 붙은 법칙의 tail, G_F는 깊이 간 transport와 지표 간 transport(공통 벡터) 검정이다.
Q와 F는 극 쌍대(R54-EQ-21)로 연결된다. 어떤 뷰도 likelihood에 정보를 더하지 않는다. 기여는 (i) 프레임·epoch 타입 강제, (ii) 특이 Fisher의 비식별 방향 보고, (iii) transport 법칙 비교다.
F 뷰는 매개변수 공간에 선언된 볼록 body가 있어야 한다. CMB lane에서만 AVAILABLE이고, 저적색편이 lane의 축 스캔은 Pi 아래에 기록한다.

## 5. 한계

선형 이론 body(선택 함수와 지표 간 보정 공분산 없음), survey 라벨 대신 반구 proxy, zero-point nuisance 모형 의존, 사후 선택(forking-path 목록), 이상 E 응답, 현재 shear 사상의 모델 의존, type I 한정. 각 항목의 해소 노드는 `RESEARCH_DAG.json`에 있다.

## 6. 독립 심사

작성자와 분리된 심사 중 보고서를 받은 것 1건, 중단된 것 1건. 상세는 `INDEPENDENT_REVIEW.json`.

- adversarial reviewer (physmath-research-harness:adversarial-reviewer): 판정 ACCEPT_WITH_REQUIRED_CHANGES; critical 2, major 7, minor 7; 수정 14건, 로컬 노드로 이관 2건 (R54-L04).
- scientific diff reviewer (physmath-coding-harness:scientific-diff-reviewer): 중단. 보고서를 받지 못했다(심사 agent가 계정 사용 한도에서 멈춤). 발견 사항 0건이 아니라 심사 미완료다. 로컬 세션이 첫 편집 전에 수행한다(`LOCAL_AGENT_CONTRACT.json`의 pending_independent_review).
