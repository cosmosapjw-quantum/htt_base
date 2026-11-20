# Local coding agent handoff | R89 eight analysis work packages

작업 위치: /home/cosmosapjw/Dropbox/bianchi/htt_base
기준 브랜치: research/r69-observable-physics-bridges-20261118
기준 Git 부모 커밋: 13820f70a0a5f4b1624faddd871a42805c4f46c8 (이 R89 패키지 게시 커밋은 후속 HEAD일 수 있다)
정본: docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json
작업 묶음: docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/MANIFEST.json

목표: 원래 60노드를 정확히 여덟 개의 source/분석군으로 분배하여, 기존 코드를 최대한 재사용하는 실질적인 한정 분석을 순차적으로 수행하라. 이 프롬프트는 60개 과학 노드의 무조건적 production START나 허위 완료를 승인하지 않는다.

실행 전:
1. AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md, R78 INTEGRATED_DAG, R86 EXECUTION_READINESS_DAG, R87 P0-B 과학 반환, R88 P0-C 보고 및 이 R89 MANIFEST를 읽어라. 현재 git HEAD, branch, 추적/미추적 dirty, 원본 source SHA를 확인하라.
2. PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/r89/prepare_eight_groups.py --check 와 R78 validate_unified.py --strict-authority 를 실행하라. 60 unique IDs/129 hard edges/8 그룹/원래 42 science hash/C10 6/6/원래 NEXT_ID SQ-CF4를 검증하고 기존 R78/R86의 scientific state를 절대로 변경하지 마라.
3. 작업 그룹 순서는 G01_COMMON → G02_CF4 → G03_GAIA → G04_RADIO_FRAME → G05_PLANCK → G06_P1 → G07_BIANCHI → G08_OPTICAL_PHY. 동일한 자료와 수치 계산은 이전 패키지의 정확한 결과를 재사용하라. 그룹 간 hard dependency는 R78/R86 그대로 적용하고, block된 노드는 수치 코드가 있어도 물리학적 성공으로 승격하지 마라.

각 그룹:
- 해당 PACKET_*.md 및 MANIFEST.json의 구체적 node, 입력, stop, 코드/테스트, write ownership만 수행하라. 한 분석군의 허용 결과 영역은 R89/runs/<group_id>/이며 서로 겹치지 않는다.
- 이미 completed_scoped인 노드는 증거만 확인하고 전체 재계산은 하지 않는다. ready_scoped 네 노드(SQ-CF4, SQ-GAIA, SQ-RADIO, SQ-FRAME)는 실제 source-dependent bounded 진단만 할 수 있다. 나머지는 원래 상태를 유지한 채 기존 커널 회귀·증거 확인·입력 blocker 분류까지만 수행한다.
- CF4 original group table은 이미 global MCMC intercalibration을 거쳤고 true S_PV, J_cal Sigma_cal J_cal^T, C_selection, independent upstream heldout는 결측이다. Planck 9 processes를 독립 sky로 세지 말고 8 pilot FFP를 full null이라 주장하지 않는다. 물리적 광자/Bianchi native solver나 공통 congruence transfer는 만들어내지 않는다.
- 기존 runner가 실제 실행 가능한 것으로 확인되면 source hash와 create-only output 경계에서만 계산하라. 미확보 외부 입력을 합성자료로 메우지 마라. 증거를 보존할 의미가 있을 때에만 코드/수치·출력 등을 새로 작성하고, 대형 구현 대신 기존 code paths를 우선하라.
- 로컬 자원은 매 패키지 시작 시 실제 측정하라. 기존 C8의 millisecond 숫자는 커널 전용이지 전체 pipeline 시간이 아니다. 35,970x35,970 dense float64 covariance는 행렬 한 장만 약 9.64 GiB이므로 불필요한 dense 복제·nested BLAS/OpenMP 과할당을 피하라. GPU 가용성은 검증 전 가정하지 마라.
- 그룹별 최소 검증(기존 테스트), 실제 artifact, 물리/수치/구현/환경 오류 구분, 한 번의 합당한 독립 검토 후 같은 active research branch에 그 그룹만 선택적으로 commit/push하라. 실질적 새 결과가 없는 봉쇄 사례는 빈 커밋을 만들지 말고 기존 근거와 정확한 BLOCKED 결과를 반환하라. 원격 identity를 확인하되 main merge, force push, unrelated dirty staging, 자동 PR/status 변경은 하지 마라. 검증이 실패하면 실제 blocker를 기록하고 거기서 더 이상 승격하지 마라.
- Return/report: 그룹ID, 원래 IDs, source/provenance, 실행한 실제 명령과 exit, 새 수치 결과 또는 정확한 재사용 근거, test outcome, 서브노드별 REUSED_SCOPED / DIAGNOSTIC_COMPLETED_SCOPED / BLOCKED_INPUT / BLOCKED_DEPENDENCY / NOT_ATTEMPTED / FAILED, 기존 논문 claim 판정 변경 없음, commit/remote result 또는 미게시 이유, 다음 실행 가능한 물리 작업. 끝에서 60개 원본 ID의 커버리지와 유일성을 합산하되 60/60 SCIENCE PASS로 표현하지 마라.

중단 조건: R78/R86/R87 authority mismatch, source hash drift, 현재 브랜치 충돌, 실제 미확보 physical covariance/null, 소유권 충돌, native solver 부재로 인한 수학적 결론 부족 등. 차단된 분석군은 BLOCKED_INPUT을 남기고 독립된 다른 그룹의 안전한 source 진단을 계속할 수 있으나, 전체 60노드 자동 연속 science execution이나 local-agent START 파일 발행은 금지다.

이번 위임은 8개 bounded analysis packages의 실행이다. 별도 요청이 없는 한 전체 논문 자동 제출·merge나 외부 raw 데이터 교체를 하지 마라.
