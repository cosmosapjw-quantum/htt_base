# R98 이후 local coding agent handoff

아래 블록을 새 local coding agent에 그대로 전달할 수 있다. 실행 기록과 scientific acceptance는 서로 구분한다.

---

너는 HTT 프로젝트의 R98 4차 연구 결과를 이어받는 local coding agent다. 다음 순서로 실제 연구를 수행하라.

## 고정한 작업 위치·권한·목표

- 기존 checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base
- 연구 branch: research/r69-observable-physics-bridges-20261118
- R98 작업 직전 baseline: 52fee3f277d715cdb982dfbe751fefac10513060
- R98 산출물: docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123
- 원래 60-node SSOT: R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json
- R78 SHA-256: 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11
- 6개 대주제, 7개 PHY 교차 경로, 42 original+11 SQ+7 PHY=60개 노드, hard graph edge 129개다. node.depends_on의 118개만 읽으면 11개 qualification overlay edge를 누락한다.
- 기존 checkout에서 작업하고 현재 HEAD, branch, git status, 관련 AGENTS.md를 읽어라. dirty/untracked 사용자 자료와 기존 기록을 보존하라. 별도 clone/worktree, main 변경, merge/force push, 원본 raw/legacy 덮어쓰기를 하지 않는다.
- 원본 /mnt/extdrive/workdir는 입력으로 읽는다. 새 다운로드·대용량 cache는 /home/cosmosapjw/Downloads 아래 해당 R98 경로를 쓴다.
- 사용자는 내부 모형·solver의 구성과 legacy 수정·확장을 이미 요청했다. 과거 R86의 blanket worker/native-code STOP를 새로운 과학 작업 금지로 재적용하지 말라. 현재 과학 acceptance 및 호스트 권한은 보존한다.
- 다음 목표는 SQ-CF4부터 독립 상류 source law와 남은 물리 응답을 구성하여 해당 노드를 실제로 진전시키는 것이다. R98 working-law 결과를 물리적 완료로 승격하지 말라. 물리 Q, Pi, F, G_F는 아직 null/unresolved다.

## 먼저 읽을 파일

1. REPORT_KO.md와 THEORY_CODING_CYCLE_RECORD.json
2. NODE60_EXECUTION_PREPARATION.json 및 NODE60_BLOCKERS_AND_ACTIONS.md
3. LEGACY_REUSE_DECISIONS.md, SOURCE_AND_SOLVER_LOCKS.json
4. CF4_P1_THEORY.md, BIANCHI_THEORY_CODE_KO.md, CROSS_PHY_THEORY_KO.md
5. RADIO_GAIA_THEORY_KO.md, CMB_THEORY_AND_RESULTS.md
6. VALIDATION.json, review/CF4_TANGENCY_CORRECTION.json, review/CROSS_PHY_C9.json, CMB_C9_CROSS_REVIEW.md
7. ACQUISITION_PREFLIGHT.json, MISSING_INPUT_CONTRACTS.json, PLANCK_COMMANDER_ACQUISITION.md

R98 결과의 7개 계산 패키지는 60개 노드에 연결되는 준비·검증 계산이다. 60개의 과학 acceptance가 모두 끝났다는 뜻이 아니다. 원래 completed_scoped 18개를 보존했고 새 노드 승격은 0이다.

## 실행 환경과 복원 확인

cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export HTT_ANALYSIS_BACKEND=auto

.venv/bin/python -m scripts.r98.program_preparation --build
.venv/bin/python -m scripts.r98.program_preparation --node SQ-CF4 --mode preparation

--mode science는 미해결 source law가 있으면 exit 3을 반환한다. 이것은 기대된 scientific gate이며 실행환경 장애가 아니다. 개별 노드의 준비 패키지를 실제 재실행하려면:

.venv/bin/python -m scripts.r98.program_preparation --node SQ-CF4 --mode preparation --execute

CMB 관측 지도 결과는 기존 파일을 사용하며 producer SHA가 맞는지 확인한다. 명시적으로 --include-observed-splits를 붙일 때만 10개 full-resolution 지도를 다시 변환한다.

## 필요한 결과만 재실행하는 명령

.venv/bin/python -m scripts.r98.cf4_p1
.venv/bin/python -m scripts.r98.cmb_full cache
.venv/bin/python -m scripts.r98.cross_survey --task gaia
.venv/bin/python -m scripts.r98.cross_survey --task radio
.venv/bin/python -m scripts.r98.bianchi_history --output docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123/BIANCHI_HISTORY_RESULTS.json
.venv/bin/python -m scripts.r98.cross_phy --output docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123/CROSS_PHY_RESULTS.json

CROSS는 CF4/Gaia/radio/Bianchi의 산출물 identity를 입력으로 사용한다. 상류 결과를 바꾸면 마지막에 다시 계산하고 새 해시와 semantic 차이를 기록한다. 소스 자료나 모형이 바뀌지 않았다면 이미 있는 전체 관측 지도 변환을 반복하지 않는다.

원본 radio cache의 fresh-byte 감사를 의도할 때만 --audit-inputs를 쓴다. raw source가 달라졌으면 기존 map을 재승인하지 말고 원인을 확인한 뒤 명시적 --rebuild로 새 지도를 만든다. raw 감사 실패 또는 변조된 cache를 자동으로 승인하면 안 된다.

## SQ-CF4의 다음 과학 작업

- 전체 table2 55,877, table4 38,053 및 선택된 35,970 그룹의 정확한 ID를 유지한다. 실제 파일 row count를 논문 abstract의 그룹 수와 혼동하지 않는다.
- R98 log response y=ln[v_f/(74.6 d)] 및 공통 modulus offset의 정확한 monopole 이동을 기준으로 유지한다. Vpwf의 공개 열은 v/(1+v/c) log10[v/(75d)]와 맞는다. ln, log10 및 Href를 섞지 않는다.
- method 순서는 SNIa, FP, TFR, SBFm, SBFir, SNII, DirectCal이다. DirectCal은 하나의 묶인 anchor 열이며 독립적으로 관측된 세 가지 method posterior라는 뜻이 아니다.
- D01: pre-intercalibration zero-point joint law, anchor training membership, DirectCal 교차공분산을 구하라. 공개 최종 modulus의 overlap로 상류 공분산을 다시 추정하여 독립 prior처럼 쓰지 말라. 입수 불가능한 성분은 unknown mass/bounded nuisance로 보존하라.
- D02/M01: selection/rejected-source law와 cosmology-conditioned PV response를 구성하라. 기존 R36 low-k covariance와 R95/R97 source Jacobian을 우선 재사용하라. 35,970² dense covariance를 기본값으로 만들지 말고 diagonal+low-rank 또는 검증된 matrix-free 연산자를 사용하라.
- finite source covariance의 각 항 N, S_PV, J_cal Sigma_cal J_cal^T, C_sel의 출처·단위·frame·gauge를 독립적으로 기술하라. data deficit와 model approximation을 분리하라.
- 새 source law가 주어지면 4개 overlapping window의 전체 36차원 공분산, 공통 calibration nuisance, 모든 source의 held-out/coverage 비교를 다시 수행하라.
- P1 finite envelope는 하나의 nuisance 값을 모든 draw/window에 공통으로 사용한다. near-double-root 반례를 보존한다. R98의 한 축 slice 결과를 전체 7차원 sharp bound로 표현하지 말라.

## 다른 경로의 병렬 가능한 실제 작업

- P2: 현재 999 CMB/300 noise, 10 observed maps가 있다. noise ID 그룹을 지킨 cross-fit을 유지한다. Commander 신호 파일 한 개가 검증됐고 아래 fullmission noise ID00000 취득 경로가 준비됐다. 한 파일 취득은 전체 ensemble/null qualification을 만족시키지 않는다.
- P4: 전파 5개 전체 카탈로그·19 cut의 NB1/Poisson/STF 비교를 기준으로, 공식 RMS/coverage, component association, spectral-index, LSS를 포함하는 source/selection law를 확장한다. density-derived footprint를 독립 survey coverage로 간주하지 않는다.
- P6: Gaia CRF3 전체와 Quaia 634,233 적격 표본의 열 가지 적합을 유지한다. 48 patch에서 얻은 160차원 covariance rank는47이므로 full inverse를 만들지 말라. 공통 patch의 cross block을 유지하고 AGN/spatial/frame 모형을 도입한다.
- P5: R49 Einstein–Euler, BASS Thomson rank9, R97 all-m projection, R98 actual history/clock를 우선 확장한다. 현재 radiative sky는 passive prescribed-xe, k=0 조건부 구성이다. radiation feedback, primordial initial-condition atlas, anisotropic recombination을 서로 구분해 구현한다.
- 외부 AniLoS/AniCLASS는 SOURCE_AND_SOLVER_LOCKS.json의 exact commit을 비교 기준으로 한다. near-isotropic I,V,VII0,VIIh,IX의 일치하는 한계에서 먼저 비교하고 exceptional VI(-1/9)나 완전 tilted I–IX 승인으로 확대하지 않는다.
- PHY05의 R90 Codazzi를 R49에 연결할 때 A를 유지하고 n→−n을 적용한다. rank 3→2→3은 보존되지만 signed flux는 그대로 옮길 수 없다.
- PHY06의 two-time 각도/commutator는 동일 normal을 따라 Fermi–Walker 수송한 triad에서 비교한다. 시간 의존 frame을 쓰면 two-time transporter를 넣는다. 161개 시점 최대값을 연속시간 최대각 또는 vorticity로 표현하지 않는다.

## 다운로드 준비

metadata/header 확인:
.venv/bin/python -m scripts.r98.acquisition_preflight

준비된 정확한 1개 Commander fullmission noise 파일 취득:
.venv/bin/python -m scripts.r98.acquisition_preflight --fetch dx12_v3_commander_noise_mc_00000_raw.fits --budget-bytes 603987840

이 명령은 R98에서는 실행하지 않았다. 새 science payload는 Downloads에 저장하며 완료 후 full FITS/finite/hash를 검사한다. 독립 publisher SHA가 없는 경우 transport-verified local artifact 상태를 명시한다. ESA는 probe의 Range를 무시했다. 불완전 .part 재개 시 실제206와 정확한 Content-Range를 확인하며 거부한 응답으로 기존 부분 파일을 덮어쓰지 않는다. catalog 일부 읽기를 전체 row 분석이나 payload identity로 표현하지 않는다.

공식 LoTSS v1.0 table header와 로컬 header는 NAXIS2=13,667,877로 일치한다. 웹페이지의13,664,379는 별도 prose 불일치다. 현재 13,667,877행 전체 카탈로그로 얻은 결과를 재현하라.

## Acceptance와 반환물

새 과학 변경에 관련된 기존 회귀검사와 독립 물리 한계만 실행한다. R98 baseline은 다음의55개 새 검사+5개 R97 검사=60개 PASS, R78 strict graph/authority32개 PASS다.

HTT_R98_CMB_CACHE_AUDIT=1 .venv/bin/python -m pytest -q tests/obsstat/test_r98_*.py tests/obsstat/test_r97_science_execution.py
.venv/bin/python docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority

반환물에는 exact baseline/commit, 입력/코드/output SHA, 실행명령과 exit code, source counts, 수식→구현, 물리·수치·구현·환경 실패의 구분, 전체 자료 및 여러 모형의 paired comparison, 각 node의 DATA/MODEL/ADDITIONAL_ANALYSIS 변화를 포함하라. 새 물리 acceptance는 증거가 충족된 해당 node에만 적용하고 원본42개 payload를 임의로 고치지 않는다. 완료한 지적을 반복 감사하거나 준비용 파일을 늘리는 대신 다음 하나의 source law, 유도 또는 solver extension을 완성하라.
