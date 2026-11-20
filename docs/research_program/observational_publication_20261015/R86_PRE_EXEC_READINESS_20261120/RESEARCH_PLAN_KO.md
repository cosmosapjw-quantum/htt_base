# R86 | 최종 로컬 실행 전 60노드 코드 준비도 및 세부 연구계획 v1.0

**2026-11-20 KST | 판정: BLOCK_LOCAL_AGENT_START.**

과학 정본은 기존 R78 INTEGRATED_DAG.json revision 3이다. 원래 42개 science node SHA e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d, 전체 60개/129개 edge, NEXT_ID=SQ-CF4와 독립 291-entry software PR backlog를 그대로 둔다. R86 EXECUTION_READINESS_DAG.json은 동일한 60개 node/129 edge에 코드·source·실행 준비도를 추가한 파생 overlay이며 과학적 acceptance·state·authority를 대체하지 않는다.

## 1. 정확한 60노드 실행 준비 목록

R79–R85의 coding ordinal 1–60은 R78 원래 배열 순서나 위상 정렬이 아니다. 기계 검증에서 두 ID 집합이 동일한 60개로 확인됐다.

| coding ordinal | 노드 | 원래 구현 결과 | C10 evidence |
|---:|---|---|---|
| 1–10 | SQ-CF4, SQ-GAIA, SQ-RADIO, SQ-FRAME, SQ-P1-ANCHOR, SQ-CMB-NULL, SQ-PHOTON-FLUX, SQ-LIE-FLUX, SQ-OPTICAL, SQ-CROSS-COV | R79 source geometry/validated native kernels | 있음 |
| 11–20 | SQ-NATIVE, PHY-01–07, E0, E1 | R81 조건부 5-view/물리 source kernels | 있음 |
| 21–30 | E2,E3,X01–03,S01–05 | R82 original P1 source-conditional sample functional | 있음 |
| 31–40 | S06,L01–06,H01–03 | R83 Planck same-ID rank, H03 4×9/36×36 covariance | **C1–C8만 게시; C9/C10 누락** |
| 41–50 | H04–06,V01–06,B01 | R84 original NVSS ring score, Bianchi Lie and conditional rank | 있음 |
| 51–60 | B02–05,K01–06 | R85 Bianchi external input validator, K02 4×12/32×32 CF4 and K03 Gaia moment | 있음 |

정확히 5/6개의 coding preparation package에서 C10 증거가 존재한다. **이는 50개 과학 노드의 실행 완료를 의미하지 않는다.** R83의 열 노드는 수치 구현/테스트가 있으나 최종 C9 review, C10 matrix, provenance, report, handoff 5개 파일이 없다. 로컬에 미게시 R83 테스트 수정과 별도 runner가 남아 있으므로 사용자가 명시한 scope 밖에서 일괄 stage/reset/commit 하지 않는다.

R78 원래 과학 42개는 18 completed_scoped, 23 pending, 1 blocked_input이며, 11개 source qualification 중 4개 ready_scoped, PHY 7개는 모두 이론적 source-bounded 검증 후 관측자료 대기다. 42-node 전용 scripts/htt_publication_dag.py --validate 는 ready_now=0, R78 통합 DAG는 4개의 bounded source qualification ready_scoped를 기록한다. **두 CLI는 서로 다른 실행 계약이며 현재 검증된 60-node production task adapter는 없다.**

## 2. 물리학과 software의 구별된 실행 경계

- P1 S01–S06: 원래 2048 coupled sample P1 함수/partial interval/anchor-floor 계산 가능. 274-row selected 진짜 GR referent와 source positive scale, 실제 calibrated Pi/동일 정상계 전달이 없는 한 물리적 posterior 불가.
- P2 L01–L06: Planck 25 T/E/B fields, eight FFP pilot paired IDs per processing variant 및 SO3/O3 morphology 코드는 준비. 진짜 release-matched Commander T/E/B MC와 exchangeability는 미검증이다. 아홉 same-sky processing과 8 pilot를 독립 스카이로 계산하지 않는다.
- P3 H01–H06: H03 35,970 CF4 selected original 4×9/C36 및 K02 4×8/C32/Fortran 빠른 경로가 있음. H02 실제 물리 correlated PV/zero-point/calibration/selection C와 heldout 없이는 H04 실제 H(z,n)을 받아들일 수 없다.
- P4 V01–V06: normal/observer matter boost frame, source-conditional NVSS 33,000 pixel/185 rings/3 flux bins F와 score가 빠르게 계산된다. 진짜 global tilt의 독립 radiation/matter source kernel/selection/LSS null 없음.
- P5 B01–B05: 11 canonical Bianchi Lie Jacobi·Codazzi 검사 및 B02 외부 payload hash/coverage validator만 있음. 진짜 all-m physical Bianchi T/E/B mode-history/IC·Planck response/Bayes family evidence 없음.
- P6 K01–K06: K01 single-congruence H_opt(n)=Theta/3-A.n/c+sigma_nn, radial omega blindness. 실제 K03 Gaia 755850 A6/K6x102/qH6 moment는 있으나 독립 normal-frame optical transfer/sky covariance, K04/K05 joint C/null 없음.
- 11 SQ / 7 PHY: source-conditioned linear algebra/physical bridge는 실제 관측 cross-likelihood, cosmological Pi, transported GF를 만들어내지 않는다. 외부 결측이 반드시 존재하면 해당 node를 미정으로 둔다.

## 3. 새로 판명된 code completeness blocker

**SW-P0-1: R83 C9/C10 미봉인.** 재검토해야 할 대상: S06,L01–L06,H01–H03, 원래 H03 C36/Planck signed B axial parity/8 pilot paired IDs. 기존 dirty tests/obsstat/test_r83_p2p3_fast.py 및 untracked scripts/r83/run_h03_fast.py 작성 주체·현재 diff를 확인하고, 실제 current clean/dirty 테스트 차이를 기록한 뒤 C9/C10과 인계를 완료한다. 소유권을 무시한 git restore 또는 blanket git add 금지.

**SW-P0-2: R78 60-node 전용 실행 adapter/패킷 부재.** R78 validate_unified.py는 DAG 구조·출처·authority만 검증하며 실행을 수행하지 않는다. 기존 42-node scripts/htt_publication_dag.py는 R78 SQ source qualification을 포함하지 않는다. 여기서 먼저 R78/R86 기반 read-only --dry-run --node SQ-CF4 한정 adapter를 구현하고 정확한 source SHA, dependency, source task/acceptance/STOP, task-owned output, blocked/unknown node rejection, no implicit launch를 검증한다. 이는 전체 60 science dispatch를 허용하지 않는다.

**SCI-P0-3: SQ-CF4 실제 방법별 보정/물리 공분산·heldout 미완료.** R80은 table3/4/selected 35,970 group/source operator identity를 확인했으나 원래 7 method presence와 source family label의 차이를 밝혀냈다. 185 OTHER groups have zero table3 method indicators, 926 groups show multiple methods. 원래 source method genealogy 및 zero-point nuisance, S_PV, J_cal Sigma_cal J_cal^T, C_selection을 source-supported covariance로 구분해야 한다. Registered sky/method/depth heldout, actual coverage/contrast and independent source null 조건이 있어야 source-qualified 모델 claim이 가능하다. R80 group-ID mod5 geometry partition은 진짜 heldout cosmological validation이 아니다.

**SW-P1-4: stale declared paths.** R78 original H01 proposed htt/obsstat/htt_hubble_depth_window.py 및 H03 proposed scripts/run_htt_hubble_depth_tomography.py는 실제 파일이 없다. 대체 source code H03_20261016/src/h03_tomography.py 및 htt/obsstat/p2p3_fast.py를 R86 실행 계약에 연결하되 원래 immutable 42-node payload는 수정하지 않는다.

**QA-P1-5: inherited 8 legacy CI failures.** R78 REGRESSION_RECEIPT.json은 옛 evidence SHA, PR-122 전용 runtime/venv, V03 stale fixture 8건을 분리한다. 이번 259 related tests PASS는 원래 dirty R83 test가 포함된 로컬 검증이고 clean-checkout/전체 repository PASS가 아니다. 기존 PR backlog 291개도 60-node kernel preflight와 별개다.

## 4. 과제별 후속 구현의 acceptance와 STOP

| 우선순위 | 여기서 실행할 실제 작업 | 성공조건 | 중단조건 |
|---|---|---|---|
| P0-A | R83 C9/C10 closure + original source parity | 정확한 HEAD/입력 byte identity, H03 4×9/C36, L02 T/E/B parity, L03 eight paired ID, stage C9/C10와 SHA/검증 | dirty R83 충돌/미검증이면 원래 파일 보존, source 확인 요청 |
| P0-B | SQ-CF4 method/source covariance/heldout numerics | 35,970 exact ID and 7-method genealogy, legitimate C or explicit partially identified sharp bound, registered heldout actual coverage | 실제 PV/selection source C가 없다면 과학 BLOCKED로 보존, H04/K04 미승격 |
| P0-C | R78 60-node fail-closed execution adapter | SQ-CF4 bounded dry-run packet, exactly 129 dependencies, blocked B02/S02 fail-closed, no implicit worker/PR/main publication | 검증된 source/task-output/ownership 없으면 START 미발행 |
| Source-dependent | SQ-CMB-NULL/SQ-NATIVE/SQ-PHOTON-FLUX/SQ-LIE-FLUX/SQ-CROSS-COV | 실제 외부 release/mode/IC/frame/source null, qualified independent source matching | 합성 전달/없는 physical posterior를 만들어 데이터처럼 쓰지 않음 |

기존 60개 과학 DAG에 임시 review gate를 추가하는 작업이 아니다. 원래 acceptance를 충족시키기 위한 최소 구체 실행 조치이며, 여러 반복 검토로 과학을 지연시키지 말고 소스·수치 결과를 만든다. 필요한 실제 수치 결과 없이 "PASS"만 생성하지 않는다.

## 5. 로컬 실행 전 최종 stop decision

실제 과학 실행의 첫 단계는 여전히 SQ-CF4다. 하지만 현재 전체 60-node all-run 또는 local coding agent의 "작업 시작" 권한은 승인할 수 없다. 본 검토는 R86 readiness overlay와 BLOCKER_LEDGER/검증 근거만 게시하고 **START_LOCAL_AGENT 파일, agent payload, 실행 명령을 게시하지 않는다**. P0-A와 P0-C 및 적어도 진짜 bounded SQ-CF4 source slice를 검증한 뒤, 사용자가 명시적으로 한정한 로컬 agent 작업만 다시 판단한다. B02 등 외부 조건이 충족되기 전에는 전체 60노드 연속 실행은 계속 제한한다.

재현: PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/r86_audit_preexecution.py; R86 overlay를 업데이트할 때만 --write 사용. pytest -p no:cacheprovider -q tests/obsstat/test_r86_preexecution_readiness.py 및 R78 validate_unified.py --strict-authority. R79–R85 관련 259 scoped tests PASS (현재 dirty R83 local checkout), original R78 structural 32/32 PASS. 이 결과는 real data physical claim을 증명하지 않는다.

External literature caution: Duangchan et al. A&A 708 A119 (2026), DOI 10.1051/0004-6361/202556645 used selection-matched CF4 mock forward-modeling; Salzano et al., Physics of the Dark Universe 53 102382 (2026) show peculiar-velocity correction changes apparent CF4 dipole signal. These public papers inform the next benchmark but are not a matched raw 35,970-source PV covariance payload.
