# PR-OBS-REBOOT

Legacy SMICA p, 다중 채널 PPC, dipole/boost/global tilt와 Bianchi morphology 결과는 서로 다른 통계량과 입력 법칙을 사용했다. 기존 handoff는 최근 b2af의 observation-law/posterior adapter 추가를 완전히 반영하지 않았고, 전체 가능한 분석을 계속 실행하는 goal queue가 없었다.

이번 변경은 legacy 보고서 재독과 source 검토, 실제 조건부 SMICA pilot, 재사용 가능한 finite-rank utility와 합성 calibration, local/global response 계산, 결과 기반 report/plots를 추가한다. global rank 129/241은 exploratory delivered-simulation conditional 결과다. native family나 full physical joint posterior를 계산한 것으로 보고하지 않는다.

23개 canonical PR 카드와 상세 JSON, 9개 autonomous goal, 20개 추가 분석 기회, bounded task-packet CLI와 복사 가능한 Codex prompt를 연결한다. Codex는 한 PR을 마치면 다음 ready goal을 선택하며, 특정 입력의 부재는 그 경로만 막는다. 전체 inventory는 계속 확장한다.

검증은 24개 targeted test, 실제 gated-cache 실행, 합성 오류율 캠페인, 수치·Wolfram 대수 확인, DAG/mirror 검사, PDF와 그림 검사 및 한 번의 독립 검토다. gate identity 오류와 두 개의 reviewer 결함은 기록하고 수정했다. 기존 scientific HOLD/UNKNOWN, historical runs와 native solver 경계는 보존한다.

배포 범위: `obs/scientific-analysis-ready-20261014`의 b2af 위에 쌓인 `obs/legacy-reboot-20261014`. main merge는 수행하지 않는다. 자세한 수치·명령·리뷰·후속 작업은 `docs/observational_reboot_20261014/README.md`에서 시작한다.
