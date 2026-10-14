# 복사해서 실행할 Codex handoff

```text
htt_base의 solver-free 연구를 중단 없이 이어라. 기존 checkout /home/cosmosapjw/Dropbox/bianchi/htt_base를 사용하고, branch obs/solver-free-dossier-20261014의 최신 published HEAD/PR을 먼저 확인하라. 새로운 clone/worktree/full repo copy를 만들지 말고 사용자 dirty files를 보존하라.

AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md, docs/solver_free_research_20261014/DELIVERY.json, PLAN.json, SCIENTIFIC_REPORT_KO.md를 읽어라. 다음 한 명령은 python scripts/solver_free_task_packet.py --ready 이다. 후보 task마다 실제 source/code/result를 선택적으로 읽고 스스로 다음 goal을 정해 실행하라. 현재 PR 하나 완료나 native atlas 부재를 전체 연구의 중단 이유로 삼지 마라.

이론은 physmath-research-loop R1–R10, 코드는 C1–C10의 실제 유도·계산·구현·검증 흐름을 사용하라. 같은 성공 계산/증명은 재사용하고 바뀐 입력과 영향을 받는 코드만 검사하라. 첨부 BASS dossier의 current-flux, finite-bin/selection, physical Gram/dual norm, finite-observation-error 정리는 활용하되 solver를 구축하거나 ODE를 적분하지 마라. 새로운 native Bianchi solver, background evolution replacement, native family identification은 금지한다.

먼저 ready인 SF07 Gaia PSD angular-correlation sensitivity, SF08 CF4 cross-law precision, SF09 방법론 원고 중 과학적 가치와 실제 입력이 준비된 것을 선택하라. 각각 result.json→source-linked plot→report까지 완성하고 독립review·commit/push 뒤 다음readygoal로 이동하라. source blocker는 공개문헌/제품자료/분석적유도로 해소를 시도하고, 해결 불가능한 입력을 정확히 기록한 뒤 다른readylane을 계속하라. SF10 Union3 exact prior binding과 SF11 Planck/CLASS joint law는 가정을 측정값으로 바꾸지 말고 실제 product-to-run 연결을 확보하라.

기존 방법론4개/실제결과11개/향후후보는 PUBLICATION_CANDIDATES와 FUTURE_ANALYSES를 따른다. 이번 새 Gaia/CLASS/Union3/selection/CF4 결과를 반영해 novelty comparison과 calibration을 보강하라. 기준미달을 test PASS로 덮지 말고 무엇을 더 계산해야 하는지 정하고 수행하라. null/negative 결과도 정확한 범위에서 보고하라. 기존 HOLD/UNKNOWN, active R9와 historical CAS 판정을 바꾸지 말고, source·selection·shared-sky/calibration dependency를 유지하라. 없는 physical tensor/MES denominator/remainder를0으로 채우지 마라.

부모 gpt-6.1-sol/high, 수치worker gpt-6.1-sol/high, 독립reviewer gpt-6-astra/xhigh를 권장한다. 단순 extraction만 gpt-6-luna/medium으로 낮추고 deterministic validator를 둬라. 부모 포함최대4agent, fresh bounded taskpacket, disjoint writer ownership, productionwriter1명, 독립검토1회와구체수선으로운영하라. requested/observed runtime을분리하고 관측불가면UNKNOWN을기록하라.

사용자는 연구·코드·그림·보고서·push를 이미 승인했다. 통상적인다음goal마다진행여부를묻지마라. main merge, 논문제출, 타인에게메시지전송은 별도승인없이하지마라. 컨텍스트경계에서goal/HEAD/inputhash/command/process PID/seed/batch/remaininginput을checkpoint하고 같은작업을이어라. 자동백그라운드서비스가설치됐다고주장하지마라. 실제외부입력/권한/런타임경계면그증거와정확한재개명령을남겨라. 최종에는현재결과·진행중작업·남은blocker·remotecommit/PR·복사가능한handoff를출력하라.
```
