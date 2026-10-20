# 복사하여 사용할 Codex handoff

```text
repo cosmosapjw-quantum/htt_base의 기존 checkout에서 draft PR#561,
branch research/htt-open-input-theory-20261018의 최신 HEAD를 확인하고 이어서 작업하라.
이번 intake 기준은69870ee249cd98a869f35e442105d17c927d28fc이며 이후 게시된
FRONTIER_20261020 문서와 실제 remote HEAD가 재개 기준이다. 사용자 편집을 보존하라.

목표: 여섯 논문 DAG의 원래42개 acceptance를 유지하면서 모든 실행 가능한
solver-free 노드를 실제 유도·계산·관측 분석·plot·보고서·독립 검토까지 진행하라.
physmath-research-loop의 R1–R10/C1–C10을 적용하라. native solver 구축,
ODE 풀이, 새로운 Boltzmann/Einstein 진화 solver 실행은 하지 않는다.
문서나 입력 확보를 원래 과학 acceptance의 완료로 바꾸지 않는다.

먼저 AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md와 해당 repo skill,
docs/research_program/observational_publication_20261015/FRONTIER_20261020의
README_KO.md, HANDOFF_PROMPT_KO.md, RESEARCH_DAG_KO.md,
OBSERVATIONAL_DATA_KO.md, INDEPENDENT_REVIEW.md를 읽어라.
원래PUBLICATION_DAG.json과 OPEN_INPUTS_20261018/CONTINUATION_TASKS.json을
scripts/htt_open_input_packet.py로 대조하라. 현재17/42이며8직접외부입력과
17의존노드가 남아 있다. 과거 HOLD/UNKNOWN/R9 상태를 보존하라.

1. 새 이론의 A(z),h(z) 응답과 distance/CONDITIONAL_MODEL.md의
   redshift-only 응답을 구별하라. 실제 cached sky/depth 및 nuisance에 사영해
   local/global, calibration/flow의 rank·principal angle·조건수를 계산하라.
   완전한 선택법칙이 없어도 명시한 고정-covariance 조건부 결과는 만들 수 있다.
   공개Pantheon total covariance를 한 번만 사용하고 같은 stochastic PV 항을
   다시 더하지 마라. source-model K를 완전한 GR 광학 response로 부르지 마라.
2. 자료가 필요하면 추가 인증 없는 공식/저자/CDS/공개archive를 자율 취득하라.
   사용자 허가는 이미 있다. 기존 receipt/hash와 cached payload를 먼저 재사용하고
   FRONTIER_20261020/ACQUISITION_MANIFEST.json 및 기존 downloader를 사용하라.
   데이터는 Git 밖에 저장하고 length/hash/schema/release/단위/frame을 검증하라.
   대용량 NPIPE는 manifest의 semantic 조건을 스스로 해결한 뒤 필요한 제품만
   명시적으로 선택한다. NESTED CMB와 RING residual을 그대로 더하지 마라.
   PR4 관측·beam·mask·foreground·index·Q/U 규약을 묶은 별도 분석을 등록한다.
   원래 PR3 L03을 이름 변경만으로 완료시키지 마라. 인증 벽을 우회하지 않는다.
3. H02에는 전체parent selection과공동보정/속도법칙, B02에는 실제물리T/E/Ball-m,
   K03에는 proper-motion/NNR/clock의 물리응답과 공동오차가 필요하다.
   새 source payload나 새 해석적 증명 경로를 조사하고 가능한 제한 하위 결과를
   바로 실행하라. position covariance/그림/chain/온도-onlyfixture를 대체 입력으로
   승인하지 마라. 충분한 입력이 생기면 원래노드와 종속노드를 계속 실행하라.
4. 완료된 Gaia전체TAP·유일한1614173행stream,713radio envelope,
   네PR3split/8쌍cache,SDSS64fit,97LP 및 과거54history/432광학비교는 재실행하지
   말고 결과를 재사용하라. 기존 실패·사용량·one-use allocation은 보존한다.
5. parent 포함 최대4개, no nested, fresh bounded context, disjoint writes.
   parent Sol/high, theory/reviewer Astra/xhigh, bounded data Sol/high를 우선 사용한다.
   requested와observed runtime을 구분한다. parent만publish한다.
6. 한 작업이 끝나면 checkpoint 후 다음ready노드 또는 새 입력/이론 작업을 고르고
   계속하라. scientific-ready=0만을 이유로 멈추지 않는다. 단, 모든 경로가 실제
   미확보 입력을 기다리면 정확한 missing payload/formula, 확인한 경로, 재개 명령을
   남겨라. 같은 검색·진단을 반복하거나 미완료노드를 완료로 표시하지 않는다.
7. 실제 결과마다 의미 있는 narrow validation과 독립 검토를 한 번 수행한다.
   구체적 finding은 수정하고 해당 reviewer의 targeted closeout을 받는다.
   plot/report의 조건·실패·남은 불확실성을 명시하고 branch에push하라.
   main merge, journal submission은 하지 않는다.

첫 명령(기존 checkout·검증된 환경에서):
.venv/bin/python scripts/htt_open_input_packet.py
.venv/bin/python scripts/htt_open_input_packet.py --node V03

신규 공개자료의 local 취득(기존receipt재사용, 기본은계획):
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json --fetch
```

이 프롬프트는 실행할 목표·순서를 지정한다. Chat 세션이 종료된 뒤 작업이 자동으로 계속 실행 중이라는 뜻은 아니다. 현재의 제한 모형으로 원래의 미확보 physical sectors를 채우지 않는다.
