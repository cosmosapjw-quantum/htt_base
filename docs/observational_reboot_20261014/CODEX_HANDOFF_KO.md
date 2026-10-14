# Codex handoff — 관측 reboot 전체 캠페인

아래를 Codex에 그대로 전달한다. 실제 배포 commit은 이 파일을 포함한 Git ref와 전달 PR에서 확인한다.

```text
목표: 현재까지 축적된 이론·코드·자료로 실행 가능한 모든 관측 분석을 직접 찾고,
goal을 지정하여 구현·실행·검증·scientific result·plot·보고서까지 계속 완결하라.
특정 PR, 계획 문서, 한 번의 검정 또는 그림 하나로 끝내지 마라.

기존 checkout /home/cosmosapjw/Dropbox/bianchi/htt_base를 사용한다.
브랜치 obs/legacy-reboot-20261014의 실제 최신 HEAD/status를 먼저 확인한다.
이번 reboot의 기준 commit은 b2afb6e2e60695f75ed0dbae21e9fde691bf926c,
기준 tree는 da485ff072a67370ad7f0583e7a7719c1bc22fb9다.
이후의 사용자 변경을 보존한다. 새 clone/worktree/전체 사본은 만들지 않는다.

읽기 순서:
1 AGENTS.md와 docs/harness/CURRENT_CODEX_RUNTIME.md
2 docs/observational_reboot_20261014/NEXT_TASK.json, DELIVERY.json
3 같은 디렉터리 AUTONOMOUS_GOALS_KO.md, GOALS.json, REBOOT_PLAN.json
4 research/ANALYSIS_OPPORTUNITY_INVENTORY.json 및 현재 task가 참조하는 source/code/tests
5 legacy 검토와 THEORY_REBOOT.md의 해당 절; 관련 canonical PR card

먼저 python scripts/reboot_task_packet.py --ready 를 실행한다.
RB00의 결과·통계 utility·SMICA60/240 pilot·합성 calibration·response laboratory는
DELIVERY의 정확한 범위로 재사용한다. 원자료가 그대로면 반복 계산하지 마라.
준비된 RB01/RB02/RB05/RB07을 우선 분담하고, 확장 inventory에서 ACT/CLASS/SDSS/
Union3/DESI/기타 입력이 준비된 분석도 구체적인 goal과 PR에 편입해 병렬로 진행하라.
현재 reboot 카드가 전체 저장소 분석 가능성의 상한은 아니다.

핵심 과학 흐름:
Planck 처리/전경/systematics 반응과 공동 null을 맞추고, full tensor morphology와
선택한 통계량·마스크·multipole·축·depth scan을 함께 calibration하여 p를 다시 계산한다.
PPC p, 유한 Monte Carlo rank p, posterior exceedance Pi, legacy power-index p를 구별한다.
같은 하늘의 여러 component/split/map이나 재활용 noise를 독립 실험 수로 세지 않는다.
기존 p=.039와 새 pilot은 서로 다른 통계/처리/null이다. 작은 값만 골라 결론내리지 않는다.
학습/검정은 분리하고, 이미 본 Planck 하늘의 분석은 retrospective selection을 보존한다.

물리 dipole/T0·제거 이력·frame·공분산을 복원한 뒤 local observer boost와 global
matter tilt의 실제 반응을 만든다. nuisance 사영 후 rank·condition·오차와 실제 깊이
반응을 먼저 검사한다. CF4/SDSS selected law 및 관측 selection/그룹/속도 covariance/
calibration/scale/remainder를 구체화한다. DESI scalar likelihood, 거리자료, CMB를
공통 latent/cross-covariance가 있는 하나의 법칙으로 연결하고 posterior/PPC/민감도를
실제로 계산한다. 같은 posterior draw/weight에서 tensor/MES/legacy 함수상을 만든다.
빠진 물리 성분을0으로 채우거나 온도 quadrupole을 shear로, residual ell1을 physical
dipole로, isotropic DESI qiso를 angular response로 바꾸지 않는다.

Bianchi morphology는 적절히 표시한 외부 transfer 조건부 경로부터 진행할 수 있다.
native solver는 이 repo에서 새로 구현하지 않는다. 외부 native atlas가 오면 source,
frame, 정확도, mask/covariance, family equivalence와 false-assignment를 검증하여
family 경쟁을 실행한다. Native 입력 대기는 다른 분석과 RB15 보고서를 막지 않는다.

모델 추천과 배분:
MODEL_POLICY_KO.md와 MODEL_POLICY.json을 읽어 실제 지원 모델을 확인한다.
기본 부모는 GPT-6.1 Sol/high, 핵심 물리·통계와 독립 reviewer는 GPT-6 Astra/xhigh,
정해진 구현은 Sol/medium→high, 작은 source/manifest 작업은 GPT-6 Luna/medium이다.
여러 독립 경로의 병렬 분할에는 부모 Ultra를 선택할 수 있지만 최대4agent를 유지한다.
Max는 특정한 어려운 단일 유도에만 쓴다. 저비용 worker가 물리 법칙이나 claim을
단독 승인하지 않는다. 요청 설정과 실제 관찰된 model/effort를 구별해 기록한다.

실행 방식:
부모 포함 최대4개 native subagent, 부모1명만 production writer.
명확한 질문·출력·코드 경로·수용 기준을 가진 goal을 스스로 정한다.
저비용 worker에는 task packet과 직접 선행 근거만 준다. 모델 요청/관찰값을 구별한다.
worker가 완료하면 종료하고 별도 fresh-context reviewer가 과학/코드/그림을 한 번 검토한다.
구체적 오류를 고치고 대상 테스트를 통과하면 canonical DAG/status와 mirrors를 동기화한다.
검토된 coherent 변경을 commit/push하고 다음 ready goal로 즉시 진행한다.
일상적인 구현·검증·push에 반복 허가를 묻지 않는다. main merge나 유료 조달은 하지 않는다.

한 경로가 막히면 실제 부족한 파일/법칙/권한을 기록하고, 획득·유도·정당한 조건부
모형/부분 식별을 시도하며 독립적인 ready 작업을 계속한다. 오래된 HOLD를 blanket
중단 이유로 쓰지 않고, 과학적 수용 없이 실행 가능성과 탐색 결과를 유지한다.
성공한 과거 큰 계산이나 proof campaign은 입력/전제가 바뀌지 않았으면 재실행하지 마라.
무거운 계산은 소규모 profiling 후 checkpoint와 재개 가능한 batch로 수행한다.
한 goal/PR의 완료와 모든 준비된 분석의 완료를 구별한다.

세션/맥락 경계에서는 goal, source, 완료/실행중 상태, PID/seed/batch, 다음 한 명령을
기록하고 이어서 재개한다. host가 허용하는 동안 스스로 다음 작업을 계속한다.
실제로 제공되지 않는 자동재개/외부자원은 성공했다고 주장하지 않는다.

종료는 capability inventory를 갱신한 뒤 준비된 과학 작업이 모두 끝났거나,
남은 모든 goal이 구체적인 외부 입력/권한/실행 의존성으로 막혔을 때만 한다.
결과·그림·보고서·tests/review·push ref/commit/tree와 잔여 goal별 정확한 재개 행동을
반환하라. 계획만 반환하거나 '원하면 이어서'라고 묻는 것으로 멈추지 마라.
```

현재 재현 명령은 README에 있다. 모든 run output은 새 디렉터리를 사용한다. `GOALS.json`의 broad goals와 `REBOOT_PLAN.json`의 상세 task는 소비 목적이 다르며, 실제 구현된 code command와 아직 설계할 provider를 구별한다.

## 2026-10-14 실제 관측 분석 closeout 추가

현재 유한 available queue는 27개 중 18개 scoped 완료, 9개 physical/native 입력 차단이다. 최신 [RETURN](RETURN.md), [DELIVERY](DELIVERY.json), [BLOCKERS](BLOCKERS.json), [13쪽 과학 보고서](results/scientific_report/scientific_report.pdf)를 먼저 읽는다. 이전 RB00 문맥과 상위 증명을 다시 실행하지 않는다. 동일 결과·원본 실패·과거 HOLD/UNKNOWN을 보존한다. 마지막 RB26은 실제 Gaia operator의 rho/raw-box 민감도이며 CAS07 물리 bound 인증이 아니다. 다음 한 명령은 `python scripts/reboot_task_packet.py --task RB09`; 부족한 global response가 공급되기 전 full physical fit을 시작하지 않는다. 기존 체크아웃·부모 production writer 1명·최대 4개 native agent와 observed UNKNOWN 규칙을 유지한다.
