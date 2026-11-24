# R107-CLOUD 결과: solver 고차 ℓ 전송, 독립 비교기, 저적색편이 전자 이력, 데이터 확보 준비

출발 커밋 `bd0c6f492955b7311f369f93cf0c4ed547984f6e`(R106). 클라우드 작업 공간(Python 3.13.18, NumPy 2.5.3, SciPy 1.18.1, healpy 1.20.1, 2코어, 실제 관측 자료 없음)에서 수행했다. HYREC-2 표가 없어 결합 solver 자체는 여기서 실행하지 않았다. 물리적 귀속, 보정된 p, 계열 판정은 없다.

## 1. 결과 요약

| 항목 | 상태 | 근거 |
|---|---|---|
| 고차 ℓ 전송(B02·SQ-NATIVE) | 코드·검증 완료, 실제 계열 실행은 로컬 | `htt/bass/transport/hybrid_los_transfer.py`, 시험 10개 중 9개 통과(1개는 HYREC 필요로 건너뜀) |
| 결합 solver 이력 연결 | 16줄 추가(`record_history=True`일 때만) | `coupled_einstein_boltzmann.py` |
| BJS VII_h 독립 비교기 | 코드·시험 완료, 일치 실행은 로컬 | `bjs_bianchi_vii_h.py`, 시험 11개 |
| z<4 전자 이력 연장 | 코드·시험 완료 | `htt/bass/recombination/rei_lowz_continuation.py`, 시험 5개 |
| 데이터 확보 manifest | 12개 항목, 기본 dry-run | `scripts/r107_cloud/acquisition.py`, 시험 5개 |
| 60노드 공백 등록부 | 열린 42노드 전부 분류 | `GAP_REGISTER.json`, 시험 2개 |
| 이론 토대 | TF1–TF8 | `THEORY_FOUNDATIONS.md` |

## 2. 수치

- **정확한 특성선 검증.** Bianchi I 닫힌형 적색편이·방향 오차 < 1e-10. 정지 FLRW source T/Q/U/V 기계 정밀도. 움직이는 전자 뒤 두꺼운 껍질의 boosted blackbody 1e-12 재현.
- **native 계층과의 일치(VII_h형 class B, tanh 재결합).** ℓ≤4에서 T 2e-6, E/B 1e-4. node 간격을 절반으로 하면 약 4배 감소(2차)하므로 이산화 오차다.
- **native 절단 진단.** 집속형 기하(a/H 0.3, n/H 0.6)에서 native L=8의 ℓ≤4 오차는 1e-2–2e-1이다(T4 0.11, E4 0.19). L=12는 ≤4e-3, L=16은 ≤1.6e-4이다. 약한 기하에서는 L=8로 수렴한다. R105/R106 운용값 L=4–8에는 계열별로 이 진단을 붙여야 한다.
- **가시선 수렴.** Nside 32↔64 ≤5e-5(ℓ≤56), ray step 0.02↔0.01 ≤1e-6, node 2배 ≤5e-3(EE/BB)·7e-4(TT)이다. 49,152 ray·301 node가 1코어 31초다.
- **BJS 비교기.** 적분 수렴 5e-13. m=±1 외 power 1e-19 이하. 99% TT power가 ℓ 8–20(Ω₀ 0.3–0.7, x 0.62–3)에 있다. McEwen 2006과 Kogut 1997 표기는 서로 다른 지도를 준다. 어느 쪽이 정확한 측지선 수송과 맞는지는 로컬 일치 실행으로 정한다.
- **z<4 전자 이력.** R105 공통 전경 τ(0→4) 0.02112795923/0.02243045425를 2e-10 안에서 재현했다. donor 연속 연장의 τ(0→4)는 z_HeII 3.0/3.5/3.9에서 0.0221961/0.0224021/0.0225124이다(민감도).

## 3. 공백 등록부 요약

열린 42노드의 공백 유형은 DEPENDENCY 33, COMPUTE 22, DATA 7, DECISION 7, CODE 5, THEORY 3이다(중복 포함). 선행 노드 없이 바로 진행할 수 있는 노드는 9개다: SQ-CF4, SQ-CMB-NULL, SQ-FRAME, SQ-GAIA, SQ-LIE-FLUX, SQ-NATIVE, SQ-P1-ANCHOR, SQ-PHOTON-FLUX, SQ-RADIO. 나머지는 이 9개에서 시작하는 사슬에 묶여 있다.

## 4. 남은 입력

데이터(manifest D00–D11): HYREC-2 표, CF3 table3, 6dFGSv·6dFGS DR3 K등급, 2M++ C15 장, Manticore draw, Commander 7–299쌍과 HM/OE 분할, ICRF3, Gaia 스캔 법칙·AGN 교차표, RACS-low DR1. 이론: 독립 C1(TF7), 계열 귀속 전 BJS 표기 판정(TF4). 코드: 카탈로그 frame 등록부(SQ-FRAME), Rust REI 드라이버의 z<4 물리(퀘이사 HeII 방출률, UVB).
