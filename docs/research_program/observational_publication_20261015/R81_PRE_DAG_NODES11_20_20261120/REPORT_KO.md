# R81 · R78 11–20번 노드 사전 코딩 C1–C10 결과

**2026-11-20 KST.** 시작 Git HEAD \`2c58772c3eb78801901ad24ff94be66a8f9ed67a\` on \`research/r69-observable-physics-bridges-20261118\`. R78 통합 science DAG revision3 60 nodes/129 edges, original 42-node payload SHA \`e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d\`. 원 자료와 원래 DAG 상태를 보존했고, 소스 레벨 실행 전에 **코드 준비**만 수행했어. 기존 R79 1–10번이 첫 10개 SQ 우선순위였으므로 R81의 11–20은 SQ-NATIVE(11), PHY-01–07(12–18), 역사적으로 완료된 원 과학 E0/E1(19–20)로 정의했다. 이 실행용 ordinal과 원 JSON 배열/위상정렬의 번호는 별개다.

## 열 개 코딩 준비 노드

| # | 노드 | 실제 산출물 및 source 검증 | 남은 물리적 제한 |
|---:|---|---|---|
| 11 | SQ-NATIVE | 입력 provenance, SHA256, 외부 T/E/B 인덱스·units·frame 및 압축 전 안전 budget 검증기 | 외부 native transfer 데이터 자체가 없고, 이 저장소에서 native Bianchi solver 구현 금지 |
| 12 | PHY-01 | **Fortran/OpenMP 다중 반구축 마스크**와 full/source selected CF4 35,970개 그룹의 first/second moment, Type V sharp bound | Source 선택·PV·calibration full likelihood, 실제 normal shear 미측정 |
| 13 | PHY-02 | R66 PR3/PR4 photon PSD와 정상계 조건부 Codazzi flux feasibility | 실제 photon flux와 total normal density fraction, 독립 joint null 부재 |
| 14 | PHY-03 | Exact same-beta Lorentz radiation flux/STF와 selected radio k,κ rank-one closure | radio와 photon의 동일 3D rest frame 미검증 |
| 15 | PHY-04 | 일반 Lie normal B2 vs affine shear E2 벡터장, 실제 Gaia 16D source Fisher E/B alias | Gaia 고적색편이 광학 전달·AGN/scan null 미완성 |
| 16 | PHY-05 | 독립 shear5+normal flux3의 rank-aware Codazzi residual covariance; 태생적 tautology 차단 | 물리적 독립 normal flux 자료 부재 |
| 17 | PHY-06 | signed STF shear \(\chi,\dot\chi,[\sigma,D]\), photon \(\ell=4\) higher-moment cap·stress nonclosure | Einstein–Boltzmann/Thomson source 시간 진화 미구현 |
| 18 | PHY-07 | 실제 CF4 선택 radius/n 12D radial design, source-diagonal weighted Gram, **정확도 확인된 선택적 C++** | complete correlated PV/zero-point/selection covariance 없음 |
| 19 | E0 | 기존 PR533 원 연구 증거 commit/hash/status 재검증 | 기존 \`completed_scoped\`을 출판 판정으로 승격하지 않음 |
| 20 | E1 | 기존 CF4 17-scenario Schur 진단 증거 commit/file/status 재검증 | 기존 \`completed_scoped\`이고 물리적 normal sigma 검출 아님 |

각 API와 과학적 의미론·source/null 제약은 CONTRACTS.json 및 C10_NODE_MATRIX.json에 있고, 원 자료에 대해 직접 계산한 source-conditional 결과는 C7_PHYSICAL_SOURCE_REPLAY.json에 있어.

## C1–C10 코딩 연구 루프

C1: 현재 branch/HEAD, R78 science 정본과 real selected CF4 35,970-group의 기존 NumPy 96-axis mask baseline 중앙값 0.267325s, 12D weighted radial Gram baseline 0.000621s 검산.

C2: 열 노드 source/normal frame/관측량 x 및 물리적 Q, source Pi, finite F와 genuine GF의 계산 가능 조건을 분리한 계약.

C3: float64와 source 좌표 보존, 2e−11 rel precision acceptance, mask boundary/orientation, covariance SPD/nullspace, 제한된 source/PV 유효범위 및 Bianchi solver 금지 조건 고정. 독립 Wolfram 구면 STF 및 photon boost 역산식 정확히 검산.

C4: C++/Fortran optional source compiled library는 /tmp의 버전·소스 SHA별로 캐시, no -ffast-math. Fortran OpenMP는 축 단위 독립 작업으로 분할하고 각 축의 원 source 순서는 유지, C++ Gram은 주어진 자료에서 속도비를 보고 정직하게 채택.

C5: htt/obsstat/phy_fast.py에 실제 수학 계산 APIs, htt/obsstat/native/multi_axis_mask.f90 및 weighted_gram.cpp, scripts/r81/build_native.py, tests/obsstat/test_r81_phy_fast.py 구현. 먼저 ImportError TDD RED 재현 후 native compile/15 synthetic 테스트 GREEN.

C6: g++13.3/gfortran13.3 native source manifest와 exact C API 확인, 기존 R49/R61/R64/R65/R66/R67/R69/R79/R80 관련 회귀까지 **192 PASS** 및 R78 32/32 PASS. 첫 광역 테스트에서 해당 도구호출이 오직 R79 native 경로를 디렉터리로 잘못 설정한 인프라/테스트 구성 오류를 발견, 정확한 인증 .so 경로로 원 테스트를 그대로 재실행해 통과. 수치식은 변경하지 않았다.

C7: 실제 R80 원래 선택 CF4 35,970 group과 source magnitude uncertainty로 96-axis mask 누출 범위 \([0.01046503,0.02002599]\) (조건부 Type V 합성 \(s=0.03\)) 계산, 기존 R80 동일 선택 40–400 Mpc와 CMB axis의 unweighted sharp bound **0.01005736760419072**를 원래 R80의 0.01005736760419077과 \(\approx5.03\times10^{-17}\) 내에 재현. 실제 R66 photon stress, R69/R76 quality/north/south Gaia 16D Fisher alias quality \(\approx0.08042406258\), 일반 Bianchi Lie B2 fullsky E2 orthogonality, synthetic normal flux/cross covariance and photon P4 nonclosure, selected CF4 radial design rank12/Gram condition62.63, 역사 E0/E1 source/commit parity 전부 finite 검산. 실제 physical joint null이나 발견은 수행하지 않았다.

C8: **원래 CF4 35,970 group의 메모리상 numerical kernels**, OpenBLAS=1·5-run 중앙값: 96 axes NumPy 0.264878s→Fortran 8-worker 0.005386s, **49.18배**. 256 axes 0.701226s→0.012974s, **54.05배**. 32 axes 40.68배. 전체 1·4·8 workers, source native/NumPy 상대 차이 ~1.2e−13, count 완전 동일. Source-qualified auto Fortran cache/manifest 검사 포함 96 axes actual auto median 0.004845s와 backend used=fortran_batch 확인. CF4 12D weighted Gram은 NumPy 0.000748s, C++ 8-worker 0.001616s로 오히려 느렸으므로 CPP **default 해제**, NumPy 유지. C++ numeric F/score/fitted beta/covariance/min eig 차이 <=1.2e−14로 확인. Benchmark는 전체 CMB/Gaia/CF4 자료 I/O나 물리적 source calibrated inference의 49배 개선을 의미하지 않는다.

C9: 적대 검증에서 **외부 solver NPZ 입력을 해시만 검사하고 압축 해제 크기를 확인하지 않는 resource-risk**를 발견. RED 테스트로 재현한 뒤 source 파일 형식·필드·압축 전 메모리 budget (기본 128MiB)을 검사하도록 수정, 원래 source identity/광학 provenance 요건을 느슨하게 하지 않았다. Native source mutation source SHA cache 경계도 테스트했으며, 처음 테스트는 지정된 auto threshold 이하의 크기로 작성한 test configuration 실수였고 이를 명확히 교정했다. 새 테스트 19 PASS, 전체 관련 광역 **196 PASS**, R78 strict source/claim 32 PASS. 성능 검토 결과 Fortran만 default로 채택하고 C++ Gram은 수치 정확하지만 성능 때문에 선택적 경로로 유지. AGENTS.md의 기본 lane 운영 규칙에도 추가.

C10: 열 준비노드 각각의 코드, source/physics validation, 미확보 입력과 다음 순서, source·Git SHA provenance, 노드별 handoff를 보존한다. R78 원래 과학 DAG와 software PR backlog는 수정하지 않는다.

## 검증 한계와 다음 과학 단계

C1–C10을 **PRE-DAG CODE IMPLEMENTATION_VERIFIED** 상태로 닫는다. 외부 SQ-NATIVE는 schema validation 이외에 실제 solver source가 없어 물리적 blocked_external 그대로다. PHY-01..07 정리들은 source-conditional이며 독립 물리 관측·공동 likelihood 완료가 아니다. E0/E1는 기존 scoped status를 그대로 유지한다. 누락된 photon flux, normal j/rho, Gaia 광학 transfer, PR4 Commander matched null, radio kappa/selection과 CF4 전체 correlated C를 합성으로 채우지 않는다.

**실제 R78 과학 실행 다음 ID는 여전히 SQ-CF4.** R80이 exact selected 35,970-group original identity를 검증했으므로 이후 source-method/zero-point/PV/selection covariance와 heldout 검정이 필요한 과학 단계다. 그 단계에서는 기본 가속 Fortran mask, 기존 Gaia C++ GLS, 광자/STF NumPy/검증 API를 사용하되 실제 signed x와 source-null/frame/measure/transport gate를 별도로 충족해야 한다.
