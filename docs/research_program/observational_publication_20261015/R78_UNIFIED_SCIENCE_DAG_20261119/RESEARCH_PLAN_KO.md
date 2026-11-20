# R78 통합 Master Research Plan v2.0 · P1–P6 × PHY-01–07

기준일 2026-11-19 KST. 단일 과학 DAG 정본은 INTEGRATED_DAG.json, 출처/브랜치 정본은 SOURCE_CENSUS.json, 과학 및 계획 심사 내역은 ADVERSARIAL_REVIEW.md, 실행 및 구조 검사는 validate_unified.py/VALIDATION.json이다. 이 문서는 단계 간 물리적 선행조건과 실제 다음 작업의 설명 정본이다. 이전 R60–R77 원전, 원래 PUBLICATION_DAG의 42-node payload, 별도 소프트웨어 PR 백로그, 역사적 GitHub PR들은 지우거나 덮어쓰지 않는다.

## 1. 하나의 프로그램 목표와 주장 상한

핵심 과학 질문: CF4의 방향별 거리·속도, Gaia position-drift E/B, radio selected-source dipole, CMB photon stress/multipoles와 일반 Bianchi Class A/B의 tilt를 **동일한 물리량이라고 가정하지 않고**, 실제 GR/Einstein–Boltzmann/Sachs/source-selection 전달과 source-matched covariance를 이용해 공통으로 식별할 수 있는 저차 비등방·비균질 물리량이 존재하는가? 없으면 어떤 유효범위, nullspace, nuisance/source 분리가 이를 차단하는지 실제 데이터로 한정할 수 있는가?

개별 논문 P1–P6의 acceptance는 그대로 유지한다. 원래 42개 과학 노드는 다음과 같다: common E0–E3,X01–X03 7개, P1 S01–S06 6개, P2 L01–L06 6개, P3 H01–H06 6개, P4 V01–V06 6개, P5 B01–B05 5개, P6 K01–K06 6개. 기록상 completed_scoped 18, pending 23, blocked_input 1. R60–R77의 범위 한정 계산과 이론 증명은 기존 미완료 노드를 출판 준비 완료로 올리지 않는다.

새로운 실무 노드는 **기존 42개 acceptance를 교체하지 않는** 11개 source/physics qualification work package, PHY-01..07의 7개 실제 cross-paper physical inference route다. 전체 60개 그래프 vertex/129개 directed dependency edge, 원래 42 payload SHA256 e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d 보존. 원래 42의 과학 의무와 달리 18개 overlay 노드는 source qualification 및 cross-study execution obligation이다. 새 PHY-01..07을 관측 독립성이 있는 7 likelihood나 새 원고 7편으로 세지 않는다.

프로그램 공통 컨벤션: metric (-,+,+,+); c,G,ħ,k_B 유지; x는 signed/typed physical or observed carrier, Q는 source/물리 허용체를 지정한 gauge, Pi는 matched null tail, F는 finite measure·event·denominator가 명시된 occupancy, GF는 같은 물리 referent의 genuine transport. Auxiliary chi, G_x, confidence volume, source posterior pushforward는 이름을 구분한다. 데이터 처리 obsstat/MIO/HTT 소유권, no-native-lowell-solver 구현 및 no-unqualified-family claim 규칙은 AGENTS와 canonical PR backlog를 그대로 따른다.

## 2. R60–R77 증거를 어디에 재사용하는가?

| 계열 | 실제 보존한 성과 | 새 DAG의 물리적 활용 | 유지할 한계 |
|---|---|---|---|
| R60 | Covariance-amplitude likelihood·global optimizer·source/calibration test, C0 | SQ-CF4, P1/P3/source C | 관측자의 GR shear가 아님 |
| R61 | CF4 35,970 selected groups, signed V3/dH3/κ_STF5와 11D/16D working carrier | SQ-CF4, SQ-FRAME, P6 | H 절대값·omega·physical frame 미식별 |
| R62 | signed apparent STF shape/classification 및 source response | P5/PHY-05 morphological discriminant | Type family 검출 아님 |
| R63 | compensated local/global tilt 역사, low power | SQ-FRAME/P4 | global matter–radiation tilt 측정 아님 |
| R64 | finite-z directional H_D, nuisance profiling·calibration covariance | SQ-CF4/SQ-OPTICAL/P3, PHY-07 | H_D ≠ local Θ/3, same CF4 genealogy |
| R65 | NVSS conditional multinomial 3 flux bins 및 same-provider paired selection | SQ-RADIO/P4 | LSS/selection cosmic null 미확보 |
| R66 | PR3/PR4 finite-band actual photon STF/energy moment | SQ-CMB-NULL/SQ-PHOTON-FLUX/P2 | 실제 matched Commander T/E/B MC 및 photon flux 없음 |
| R67 | 원래 7 research axes, 6논문과 conditional registry/CF4 contrast | 11 SQ work packages의 프로그램 구조 | R67의 A1..A7 ≠ PHY-01..07 |
| R68–R69 | x→Q/Pi/F/GF의 물리적 typing, STF GR/kinetic/morphology bridges | 모든 SQ/PHY 수리물리 계약 | 미검증 전천/finite-z 물리모형 확대 금지 |
| R70–R73 | photon kinetic nonclosure; finite-z Jacobi H; radio boost curvature; 물리적 5뷰 결합 | PHY-02/03/06/07 | 서로 다른 실험 x는 같은 tensor가 아님 |
| R74 | 실제 R65 source-count ring profiling, F susceptibility와 axial null | SQ-RADIO/PHY-03/04/07 | score injection ≠ 실제 observer velocity |
| R75 | 모든 Bianchi Lie rank/Codazzi/tilt, Type V/exceptional VI_-1/9 morphology, R49 posterior geometry | SQ-LIE-FLUX/PHY-02/05/06 | R49 transfer-conditional, CMB/Gaia/CF4 PPC 부적합 |
| R76 | 실제 R61 공동 11D 전천 양성 하한, Gaia 16D masked E2/B2 covariance | SQ-GAIA/SQ-CF4/PHY-01/04/07 | CF4 apparent positivity ≠ 물리적 fullsky GR claim |
| R77 | PHY-01..07의 일곱 조건부 물리 정리, sharp CF4 mask leak·photon PSD–Codazzi·radio boost·Lie B2·rank·nonclosure·distance diversity | 7개 PHY 실행 노드의 이론 선행증거 | 실제 cross-probe joint likelihood는 아직 없음 |

R69 원번호 아래 서로 다른 세 연구 전달물(원래 물리 bridge, P1 GR, P1 second fiveview)을 정확한 별도 source path 및 해시로 보존한다. 서술상 완료/수치검증/조건부/차단을 서로 교환하지 않는다.

## 3. 기존 PR·브랜치와의 정합성 및 authority 분리

2026-11-19 현재 active checkout research/r69-observable-physics-bridges-20261118의 R77 기준 HEAD dd857ff8decbcfe90fd566a9dd87dcf5be60f609로 원 R60–R69 연구 브랜치 tip은 모두 **Git 조상**이다. R70–R77은 같은 active 연구 브랜치에서 scoped theory·source 결과를 게시했다. R49/R50/R54 이전 stacked PR #575/#576/#577은 GitHub에서 여전히 OPEN이며, 그 PR들이 default/main에 정식 merge되었다는 주장을 하지 않는다. 과거 열린 PR 내용은 비교·재사용 source로만 취급하고 이 과학 DAG 변경으로 auto merge하지 않는다.

PUBLICATION_DAG의 245 software PR baseline entry는 **2026-10-15의 과거 수**다. 실제 현재 docs/codex_handoff/pr_backlog.yaml에는 291 항목이 있으며 machine_readable/pr_backlog.yaml은 byte-identical mirror다. 291 software PR DAG는 구현·권한/테스트 SSOT로 유지, 42 science goals+18 overlay는 이번 통합 과학 DAG로 별도 정본이다. PR completion/blocked/pending/dormant counts are distinct from scientific claim admission and may be overlapping status sets. 원래 42 state와 PR status/미추적 다른 작업은 업데이트하지 않았다.

한 원전의 source 크기를 다른 원전의 통계로 재사용하지 않는다: CF4 전체 table4 38,053 groups vs R61 selected 35,970, Gaia formal star-noise vs 192-patch exploratory, PR3/PR4 release same physical sky, R65 NVSS peak/integrated 241,892 overlapping components, R49 original 24D 4,000 thinned model posterior vs 직접 측정된 normal flux를 구분한다.

추가 2026 문헌 비교: CF4 forward-modeling은 catalog selection에 따른 bulk-flow amplitude 증폭/보정 문제를 직접 다룬다 (A&A 2026 https://www.aanda.org/articles/aa/full_html/2026/04/aa56645-25/aa56645-25.html). Salzano et al. (2026)에서는 peculiar-velocity correction이 겉보기 CF4 anisotropy를 크게 줄인다고 보고했다 (https://doi.org/10.1016/j.dark.2026.102382). 따라서 SQ-CF4 priority는 새로운 anisotropy 검출 가정이 아니라 선행 분석과의 source-matched 실증적 판별을 위한 것이다. Gaia VSH의 redshift/AGN/astrometric source-systematics와 Bianchi I position-drift 선행연구 (https://doi.org/10.1088/1361-6382/ae76b3)도 SQ-GAIA의 최소 비교 기준에 넣는다.

## 4. 새 단일 실행 DAG의 11 source qualification 노드

| ID | 목표 · 실제 scientific output | 현재 실행 상태 |
|---|---|---|
| **SQ-CF4** | 동일 selected CF4 group/method covariance + PV/calibration selection + heldout bias/coverage; P3 H02의 선행조건 | **READY 1** |
| SQ-GAIA | Gaia redshift/AGN/scanning-law systematic/source VSH heldout null, B1 spin and E2/B2 alias | READY 2 |
| SQ-RADIO | NVSS matched source IDs, k/κ/SED/beam/migration, paired LSS selection covariance | READY 3 |
| SQ-FRAME | Observer/emitter/normal frame, sign, Lorentz/peculiar-vs-tilt transfer | READY 4 |
| SQ-P1-ANCHOR | P1 selected 274-row physical scale/positive source anchor or partial identified set | BLOCKED physical anchor, source law exists |
| SQ-CMB-NULL | Commander matched full T/E/B null and PR3/PR4 exchangeability | BLOCKED source |
| SQ-PHOTON-FLUX | Photon f and normal density ratio, other matter flux, high-L Thomson closure | BLOCKED source |
| SQ-LIE-FLUX | Independent normal-frame rho,j,π and covariance for arbitrary Bianchi a,N | BLOCKED source |
| SQ-OPTICAL | One exact source-qualified Sachs/Jacobi/Gaia-position drift transfer with IC/BC and finite z | CONDITIONAL after frame |
| SQ-CROSS-COV | Actually measured cross-probe C, nuisance-projected rank and heldout test | CONDITIONAL after source/optical |
| SQ-NATIVE | External actual native polarized all-m morphology atlas validation, **not implementation here** | EXTERNAL BLOCKED |

이 중 READY는 전체 논문 출판에 필요한 모든 자료가 있다는 뜻이 아니라 **앞선 실제 자료로 한정된 실행 가능한 slice가 있다**는 뜻이다. 모든 node는 success/stop condition을 가지며, 누락 외부 자료가 있으면 정확히 해당 PHY/source-dependent node만 차단한다. SQ-NATIVE를 해결하려고 fake native solver를 만드는 작업은 금지한다.

## 5. P1–P6 science DAG와 PHY-01–07의 역할

- **P1 S01–S06 (1 done, 1 blocked, 4 pending):** 274-row signed selected original law, physical x anchor and partial identified confidence; R73 type semantics. SQ-P1-ANCHOR before historical S02. Claim gate remains an actual identified physical source parameter, not shape score.
- **P2 L01–L06 (2 done, 4 pending):** actual Planck finite-band stress vs full matched Monte Carlo; L03 requires SQ-CMB-NULL. Native source conditional optical/Thomson work remains distinct from Commander release difference.
- **P3 H01–H06 (2 done, 4 pending):** SQ-CF4 qualification before H02, then H04 source-calibrated H_D alternatives, H05 prior-art matched and H06 manuscript decision. Do not identify finite-z H_D with local H.
- **P4 V01–V06 (3 done, 3 pending):** SQ-FRAME and SQ-RADIO before V04 local observer boost vs physical global tilt; source-normal/compensated history and selection physics must remain distinct.
- **P5 B01–B05 (1 done, 4 pending):** external SQ-NATIVE before original B02 physical polarized family atlas; B03 also requires real CMB/null and optical qualification. R75 Lie constraint and R49 conditional posterior do not complete B02.
- **P6 K01–K06 (2 done, 4 pending):** SQ-GAIA before K03, SQ-OPTICAL before K04 and SQ-CROSS-COV before K05; Gaia B2 does not immediately measure fluid vorticity.

R67 **research axes A1–A7**는 분석/방법론의 조직화이고, R77 **physical cross PHY-01–07**은 실제 서로 다른 물리량 사이의 전달과 공동 관측 가능성을 검정할 조건부 경로다. 새 PHY 노드들은 이론 수학적 정리까지는 source-bounded로 검산됐지만 각자의 source qualification 입력이 마련되기 전에는 **observational route pending**이다. 이론 완료를 일곱 신규 likelihood나 42-science-node 과학 gate 충족으로 계산하지 않는다.

## 6. 앞으로 순차적으로 진행할 실제 실행 순서와 중단조건

**NEXT_ID = SQ-CF4.** 후속 연구 스레드는 반드시 최신 Git HEAD 및 R78 INTEGRATED_DAG/SOURCE_CENSUS의 exact identity를 확인하고 한 node만 실행한다. 이후 노드 계획 상태는 실제 증거로만 변경하고 GitHub의 기존 active research branch에 scoped commit/push 한다. 계획은 업무를 자동 수행하지 않는다.

SQ-CF4에서 할 일:
1. 원 R58/R61의 실제 selected 35,970 group IDs, CF4 table3/table4 group-level indicator lineage, R64 method32/sky source response와 selection/mask를 **동일 row identity**로 결합한다. R77 full-table4 38,053 mask result를 source-matched data로 섞지 않는다.
2. \(C=N_{\rm stat}+S_{\rm PV}+J_{\rm cal}\Sigma_{\rm cal}J_{\rm cal}^\top+C_{\rm selection}\)로 정해진 실제 source-supported nuisance와 미확인 covariance 성분을 구분한다. Group-overlap differences는 원 source를 다른 기저로 변환한 것으로 취급하고 독립 sample likelihood를 곱하지 않는다.
3. 동일 source/cut/reference에서 monopole, bulk/PV dipole, angular STF response와 H_D derivative의 identifiable subspace를 비교하고 heldout coverage·effect shift·PV-correction 및 selection sensitivity를 실제로 계산한다. 2026 CF4 forward-modelling 및 angular correction 문헌의 정의/샘플과 맞춘 비교가 필요하다.

**PASS:** source ID/provenance가 보존되고 합당한 same-source C 아래 물리적 식별 조합 한 개가 확보되거나, 수치·rank·검산으로 제한된 nonidentifiability와 coverage 결과가 나온 경우. **STOP:** 보정 공분산/선택함수를 원 자료에서 확보하지 못했다면 그 특정 성분을 미해결로 기록하고 SQ-GAIA로 이동하며, H04/P3 물리적 H(z,n) claim을 통과시키지 않는다.

다른 독립적인 READY frontier: SQ-GAIA → SQ-RADIO → SQ-FRAME. SQ-FRAME이 source-conditional 자격을 갖춘 뒤 SQ-OPTICAL에 진입할 수 있다. SQ-CMB-NULL/SQ-PHOTON-FLUX/SQ-LIE-FLUX/SQ-NATIVE는 자료나 외부 output이 나타날 때만 활성화한다. SQ-CROSS-COV와 일곱 PHY는 독립 source 전달/측정이 적합해질 때 실증적 결합을 시작한다. 가장 강한 물리적 DAG 노드가 반드시 다음 당장 실행할 수 있는 노드는 아니다.

## 7. 적대적 계획 검증과 수정 이력

첫 candidate는 60-node DAG에 129 edge로 cycle-free였으나 A1–A6의 실제 authority/provenance 결함을 드러냈다. **Rev1**은 blocked source를 READY에서 제거했고, R69 세 전달물·immutable 42-node checksum·current 291 software backlog/older PR 상태·P1 physical anchor 명칭을 교정했다. 28개 구조·물리 typing 검증이 PASS했다. **Rev2**에서는 실제 source plans/문헌 비교, 이 문서, 전체·요약 DAG 도식화, root PUBLICATION_DAG 및 AGENTS의 active science authority pointer를 일치시키고 strict validation과 외부 Git push readback을 수행한다. **Rev3는 새로운 실질 blocker가 발견되었을 때만** 실행하며 과정상 세 회를 억지로 채우지 않는다. 오류와 검산 결과는 ADVERSARIAL_REVIEW.md 및 VALIDATION.json에 구분해 보존한다.

## 8. 독자·후속 에이전트용 파일 계약

- INTEGRATED_DAG.json: 단일 60-node/129-edge machine-readable science DAG, immutable 42 payload, 11 SQ qualification, 7 PHY route, original/overlay dependency types, topological order and NEXT_ID.
- SOURCE_CENSUS.json: R60–R77 원전/체크섬과 R69 세 산출물, R60–R69 Git branch heads, 291 software PR current vs 245 history, historic older open PR references.
- RESEARCH_PLAN_KO.md: 과학적 이유와 실행 순서, claim gate, source/stop policy.
- PLAN_OVERVIEW.mmd 및 PLAN_OVERVIEW.svg: 계층별 실행 시각화.
- PLAN_FULL.dot 및 PLAN_FULL.svg: 60개 실제 DAG node와 129 dependency edge의 전체 가시화; status/edge kind를 구별.
- ADVERSARIAL_REVIEW.md: 후보 결함과 최대 세 번의 실제 수정 이력.
- validate_unified.py, VALIDATION.json: graph acyclicity, all source pins, original science 42 SHA, PR mirror, ready frontier, authority 및 source physics gate 검산.
- AGENTS.md + root PUBLICATION_DAG.json: R78을 **active science DAG**로 안내하되, 기존 software PR SSOT와 역사적 source DAG/PR 상태를 바꾸지 않는 짧은 포인터.

**논문 출판 판정:** 현재 여섯 논문 모두 NOT_READY_TO_SUBMIT. Source-conditioned theoretical advances are durable; claim promotion requires independently qualified physical observation, null and heldout comparator, not an attractive all-sky map.

## 9. 세 번째·최종 수정: 기존 저장소 회귀 검사의 근거 경계 (2026-11-19)

새 활성 과학 DAG를 변경한 뒤 관련 기존 테스트 67개를 대상으로 검사를 실행한 결과 59 PASS, 8 FAIL이었다. 문제는 R78 물리 DAG 구조검사와 분리하여 REGRESSION_RECEIPT.json에 모두 기록했다. 7개 실패는 기존 release-evidence graph가 예전 MIO budget_spec.py SHA (49b0afc4...)를 요구하지만 **R78 이전 기준 commit에서도 파일 SHA는 현재와 같은 25213b00...**이었다는 점과, PR-122 전용 launcher가 요구하는 repository/venv/bin/python이 없는 현재 환경에서 발생한다. 나머지 1개는 V03이 차단 상태라고 가정하는 오래된 synthetic test fixture이지만 R78 이전 원래 42-node DAG에서도 이미 V03은 completed_scoped였던 불일치다. 해당 8건은 각각 source/evidence hash·runtime environment·stale test semantics로 분리한다.

R78과 직접 관련된 구조/권한/출처 검사 **32/32 PASS**, 위 상속 실패 파일·fixture를 포함하지 않는 기존 과학 DAG 관련 테스트 **42/42 PASS**다. 이 성적을 과장하여 저장소 전체 regression PASS라고 주장하지 않는다. 이전 PR-122 release-evidence hash와 canonical Python 환경을 강제로 수정하거나 scientific claim freeze 상태를 올리는 일도 이번 과학계획 통합 범위에서 수행하지 않았다. 해당 8건은 원인별 별도 환경/증거 정합성 PR을 요청할 때만 재검토한다.

이에 따라 수정 횟수는 Rev1 실제 source/ready 오류, Rev2 권한·도식화, Rev3 기존 회귀 실패의 정확한 provenance 및 검증 구분으로 **총 3회**다. 별도의 R4 검토 계층이나 새 과학 DAG gate를 더하지 않았으며, 60개 노드·129개 edge 및 원래 42 payload는 그대로다. R78 DAG revision 3은 이 상속 검증 제약을 기계 판독 정보로 보존하고, root PUBLICATION_DAG의 활성 science pointer SHA가 revision 3을 정확히 가리킨다. 향후 연구의 최우선 NEXT_ID는 여전히 SQ-CF4다.


## 10. 2026-11-20 R86 최종 local 실행 준비도 감사 및 조건부 STOP

**과학 DAG 정본 R78 revision3, 60 nodes / 129 edges / 원본 42 science payload와 SQ-CF4 NEXT_ID는 변경하지 않는다.** R79–R85 coding preparation 1–60 numbering은 이 DAG의 노드 배열/위상 정렬 순서가 아니라 독립 작업 목록이며, 각 node ID와 실제 source를 대조한 새 R86 execution-readiness overlay를 아래 경로에 게시한다.

- docs/research_program/observational_publication_20261015/R86_PRE_EXEC_READINESS_20261120/EXECUTION_READINESS_DAG.json: 원본 R78 60 IDs/129 edges와 과학 states 그대로, 각 coding-stage source/코드 증거, 현재 full production physics source 부족, NO_START 판정
- 같은 경로의 RESEARCH_PLAN_KO.md 및 BLOCKER_LEDGER.json: 최소 후속 코드 구현 P0-A=R83 C9/C10 봉인, P0-B=SQ-CF4 실제 method/PV/selection/heldout source, P0-C=60-node fail-closed dry-run adapter. 외부 B02 polarized all-m/T,E,B 및 Planck calibrated null은 가짜 data로 대체하지 않음.
- scripts/r86_audit_preexecution.py와 tests/obsstat/test_r86_preexecution_readiness.py: read-only 60-ID coverage, 129 dependency edges, original source SHA and qualified code/readiness gate; 실행용 task packet 생성 또는 agent dispatch 없음.

2026-11-20 감사에서 소스 관련 회귀 259/259 PASS, R78 strict 32/32 PASS가 확인되었지만 **전체 repository clean checkout PASS나 전체 science DAG executable은 아니다**. 기존 R83의 C1–C8 수치 구현만 Git에 게시되어 C9 review/C10 matrix·provenance·report/handoff가 5개 누락돼 있다. 현재 R83 test는 tracked dirty, R83 runner는 untracked이므로 자동 add/reset 금지. R78의 과거 8 inherited CI failures도 별도 유지한다.

따라서 **R86 verdict = BLOCK_LOCAL_AGENT_START**, local coding agent 시작용 handoff/worker dispatch는 만들지 않는다. R78의 SQ-CF4 ready_scoped는 35,970-group source-bounded diagnostic 진입 가능성이지 correlated PV/calibration/selection C와 heldout validation을 통과한 과학 실행 패킷이라는 뜻이 아니다. 위 P0-A/B/C의 실제 검산과 owner task scope 확인 뒤에만 다시 한정된 local dispatch 여부를 결정한다. R78 original 42 acceptance, 11 SQ source status, 7 PHY conditional theorem states 및 original software PR backlog authority를 승격하지 않는다.
