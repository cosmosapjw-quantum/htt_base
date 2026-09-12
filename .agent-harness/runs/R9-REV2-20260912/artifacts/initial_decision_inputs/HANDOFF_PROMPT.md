# R9 revision 2 handoff — 기존 프로그램을 이어서 구현

```text
저장소 cosmosapjw-quantum/htt_base의
implementation/project-catalog-20260912 브랜치를 이어서 작업하라.
이 파일이 포함된 전달 커밋을 immutable starting point로 고정하라.
시드 보고서는 d514eabdbd6a464a92ff6e51e1aba91399a054db,
R9 원본은 5e4e899c0dfa2028d81a82ca68ccd11203947470이다.
현재 프로그램은 docs/research_program/tensor_joint_r9/의 revision 2다.
R10 별도 계획으로 초기화하거나 기존 증거를 최신 실행으로 덮어쓰지 마라.

사용자가 선택한 하네스는 GPT-6 Astra v4.0.0이다.
physmath-research-loop 스킬의 registry를 읽어 다음 원본 ZIP을 확보·확인하라.
research: physmath-research-harness-gpt6-astra-v4.0.0-20260908.zip
  libfile_07a54bff29548191bb87edd4bbe9cc73
  sha256 dae76c90f2e5d691bcdd595dadbe470bacacba3bb2a036ff9788ffe7d3bfabb7
coding: physmath-coding-harness-gpt6-astra-v4.0.0-20260908.zip
  libfile_b1f31b28c0688191a06a4ae8f943d862
  sha256 dc99e7ab2f9629dcce3ec0758d97e19acc5b645f86e208d1b338bb6430ff8d7a
START_HERE, core instructions, 현재 상태와 이번 phase를 읽고 적용하라.
이번 전달 세션은 Library retrieval 기능과 원본 ZIP이 없어 package activation이
BLOCKED_PACKAGE_UNAVAILABLE였다. 저장소 프로토콜로 연구/설계를 수행했지만
GPT-6 원본 패키지를 로드했다는 완료 기록은 없다. 재확인 없이 이를 PASS로 바꾸지 마라.

먼저 AGENTS.md와 관련 .agents/skills, canonical pr_backlog/pr_status를 읽어라.
그다음 tensor_joint_r9의 RESEARCH_STATE.json, REVISION_SPEC.md,
revision2/MODEL_TO_DATA.md, revision2/THEORY_EXTENSION.md,
campaign_dag.json, revision2/REVIEW.md와 evidence/execution_receipt.json을 읽어라.
원본 R9 THEORY/CMB_RESEARCH와 d514eabd compendium은 지정된 범위만 대조하라.
거대 카탈로그를 복구하거나 전체 검색을 처음부터 반복할 필요는 없다.

다음 작업은 R9-03/05의 공통 상태·작은 제품 intake와 R9-24/25의
전체 깊이 covariance adapter다. 기존 common/depth_path.py와 HTT infer adapter가
어느 커밋에서 실제로 사용되는지 확인하고 기존 API를 확장하라.
donor 6bafca66285ef071081453313bb7d2d6b261599c를 현재 branch와 동일시하지 마라.

핵심 구현:
1. 같은 추출·선택·group·calibration·mask·frame의 전체 Cjk와 mean/response를 유지한다.
2. r=HY, V=H C H^T의 교차 단계 항까지 계산한다. covariance가 없으면 unavailable.
3. HTT는 원 Y 또는 (Y0,HY)의 전체 법칙을 소비한다. 차분만으로 공통 신호를 지우지 마라.
4. 고정 feature transport와 full-past Gaussian innovation을 구분한다.
   fitted K/covariance/선택 단계는 joint law 또는 동일한 전체 mocks로 검증한다.
5. singular support를 먼저 검사하고 rank에 맞는 law를 적용한다. jitter로 제약을 지우지 마라.
6. 한 공통 state-anchor confidence set의 outer image를 tensor 함수들에 전달한다.
   point coverage와 full identified-set coverage를 구분한다.
   q가 불확실하면 고정-q fibre 공식을 plug-in confidence로 사용하지 마라.

먼저 재현할 명령:
python3 docs/research_program/tensor_joint_r9/revision2/run_checks.py
원시 stdout/stderr와 exit code를 기록하라. 참조 실험은 관측 적격성 증거가 아니다.
다음 production 변경은 실제 함수에 연결된 covariance 누락·지지집합·공통모드·
random-anchor·경계 fibre 반례를 통과해야 한다. 필요한 명제의 네 축 CAS는
기존 contract 아래 별도로 실행하라. Wolfram 작은 행렬 확인을 xAct/4축 PASS로 부르지 마라.

관측 실행은 한 제품의 selected law와 covariance가 실제로 준비된 경로부터 끝내라.
CF4 quarantine 수치 재사용 금지; JWST 위치 match는 물리 identity가 아니다.
DESI는 같은 release의 조건부 law; Union3는 근사 scenario; PR4는 기존대로 skip.
관측 morphology와 beta_RO, global matter tilt, physical sigma/omega를 구분하라.
physical provider/jet가 없으면 해당 함수만 unavailable로 남기고 독립 제품은 계속하라.
native Boltzmann solver를 구현/시뮬레이션하거나 Bianchi family를 주장하지 마라.

MIO는 diagnostic, HTT는 inference다. x/Q/F/Pi/G_F는 현재 tensorized 객체로 유지한다.
같은 하늘의 좌표변환·component·depth score를 독립 likelihood로 중복 계산하지 마라.
기존 family alpha .05, 제품별 1/80, CMB 내부 각 1/160을 보존하라.
새 depth 검정은 기본 진단이다. co-primary로 바꾸려면 결과 전에 제품 예산 내 분할과
전체 scan calibration을 등록하라. 빠진 제품의 alpha를 사후 재분배하지 마라.

Subagent를 쓰기 전에 context pack을 재생성하고 new_assignment.py로 등록하라.
blind-results와 sole-writer 경계를 지키고 실제 hook/profile evidence만 보고하라.
구현→최소 관련 검증→독립 검수→canonical 상태/미러/PR_DELTA 갱신→커밋/push→
원격 커밋/파일 readback을 수행하라. 과학적 부족 입력과 환경 실패를 구분하여
기록하고 assurance 문서만 반복하는 대신 제품 하나의 실행 가능한 경로를 끝내라.
```
