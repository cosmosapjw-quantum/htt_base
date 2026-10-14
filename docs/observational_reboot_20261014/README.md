# 관측 연구 reboot와 전체 분석 연속 실행

이 패키지는 legacy 연구를 다시 읽고 실제 SMICA 조건부 pilot, 합성 통계 보정 실험, local/global 식별성 계산을 실행한 결과다. **현재 완료 단위는 RB00이다.** 이후 Codex가 축적된 이론·코드·자료로 가능한 분석을 스스로 찾고, goal을 지정하여 scientific result·plot·보고서까지 계속하도록 23개 개발 카드, 9개 상위 goal과 20개 추가 분석 기회를 연결했다.

기준은 `b2afb6e2e60695f75ed0dbae21e9fde691bf926c`, 브랜치는 `obs/legacy-reboot-20261014`다. 감사 PR #530은 로컬 잔여물 snapshot이며 다른 99개 PR을 합친 결과가 아니다. 이 reboot도 기존 HOLD/UNKNOWN을 자동 변경하지 않는다.

## 먼저 읽기

| 목적 | 문서 |
|---|---|
| 실행 모델과 사고 수준 | [MODEL_POLICY_KO.md](MODEL_POLICY_KO.md), [MODEL_POLICY.json](MODEL_POLICY.json) |
| 다음 Codex에 전달 | [복사 가능한 handoff](CODEX_HANDOFF_KO.md) |
| 스스로 goal을 정하고 계속 실행 | [지속 작업 지시](AUTONOMOUS_GOALS_KO.md), [GOALS.json](GOALS.json) |
| 현재 상태와 다음 행동 | [DELIVERY.json](DELIVERY.json), [NEXT_TASK.json](NEXT_TASK.json) |
| subagent 개발 DAG와 상세 PR 카드 | [DEVELOPMENT_DAG_KO.md](DEVELOPMENT_DAG_KO.md), [REBOOT_PLAN.json](REBOOT_PLAN.json) |
| 새 결과와 그림 | [한국어 보고서](results/report/report.md), [PDF](results/report/reboot_report.pdf), [수치와 source hash](results/report/report.json) |
| 현재 repo 판단 | [REPO_REVIEW_KO.md](REPO_REVIEW_KO.md) |
| legacy 재독과 실제 이론 유도 | [LEGACY_REBOOT_REVIEW.md](research/LEGACY_REBOOT_REVIEW.md), [THEORY_REBOOT.md](research/THEORY_REBOOT.md) |
| 이론·코딩 각 10단계 실행 | [RESEARCH_LOOP_KO.md](RESEARCH_LOOP_KO.md) |
| 자료와 추가 분석 가능성 | [SMICA source audit](research/SMICA_SOURCE_AUDIT.md), [20개 기회](research/ANALYSIS_OPPORTUNITY_INVENTORY.md) |
| 통계 방법과 문헌 | [STATISTICAL_METHODS.md](research/STATISTICAL_METHODS.md), [PRIMARY_SOURCES.json](research/PRIMARY_SOURCES.json) |
| 독립 검토 | [INDEPENDENT_REVIEW.md](review/INDEPENDENT_REVIEW.md) |

## 실행한 결과

- 실제 K1 SMICA cache에 같은 mask와 ell0–5 OLS를 적용했다. 독립 전달 noise 300개를 각 1회 사용하며 training 60 / calibration 240으로 분리했다. ell2–5 전력 요약의 global rank는 **129/241 = 0.535270**이다. 관측–시뮬레이션 교환가능성을 가정한 retrospective 조건부 결과이며 confirmatory physical Planck p나 Bianchi 검출이 아니다.
- 고정 B=999, 1,000회 합성 실험의 global rejection frequency는 0.060, 비보정 minimum marginal 선택은 0.145였다. 95% binomial 구간 [0.04610, 0.07656]은 이 합성 절차의 오류율에 관한 것으로 Planck 모형의 수용 근거가 아니다.
- 알려진 공분산의 합성 반응 실험에서 nuisance 사영 후 rank는 constant/depth/free-shell 순으로 0/3/0이다. full rank여도 반응이 작으면 정보가 약하다. 실제 global tilt 값은 추정하지 않았다.
- 24개 targeted test와 실행 receipt를 남겼다. 최초 gate 문서/캐시 hash 혼동은 실행 전에 실패했고, 정확한 cache field로 수정 후 회귀 테스트와 실제 pilot을 통과했다. 그림 제목과 nuisance 단위 문제도 독립 검토에서 수정했다.

과거 p=.039, .078/.079, lnB, MES 숫자는 각기 다른 처리·통계량·관측 법칙에 속한다. 새 p와 대소 비교만으로 과학적 진전을 판정하지 않는다. legacy 문서에 그 차이를 원본 경로와 함께 기록했다.

## 저비용 Codex의 진입 명령

기존 checkout에서 아래 명령은 작업 선택용 JSON만 출력한다. 분석 자체를 자동으로 실행하는 scheduler는 아니다. 반환된 packet을 읽은 agent가 구현·실행·검토·push 후 다음 goal로 이동한다.

```bash
python scripts/reboot_task_packet.py --validate
python scripts/reboot_task_packet.py --ready
python scripts/reboot_task_packet.py --task RB01
```

의존성이 준비된 첫 작업은 RB01/02/05/07/17/18/20/21/22다. 이는 입력 법칙까지 과학적으로 수용되었다는 뜻은 아니다. 각 packet의 input obligations를 해결하면서 진행한다. 부모 포함 최대 4개 agent, production writer 1명, 한 PR당 독립 검토 1회와 구체적 결함 수정으로 운영한다.

RB17–22는 ACT/Planck lensing, CMB spectra, CLASS·Planck·BeyondPlanck polarization, JWST·Union3 거리, SDSS depth, Gaia·COSMOS-Web와 미조사 자료를 포함한다. 이 목록은 확장 가능한 census다. Native atlas를 기다리는 경로가 다른 준비된 분석이나 보고서를 막아서는 안 된다.

## 필요한 경우의 재현

입력과 질문이 그대로면 저장 결과를 재사용한다. 아래 명령은 새 출력 디렉터리만 사용하며 historical 결과를 덮어쓰지 않는다. 기본 remote 환경은 Python/numpy/scipy/matplotlib, pilot에는 healpy가 필요하다. 실행 당시 실제 환경은 evidence와 각 execution_receipt에 있다.

```bash
export PYTHONPATH=htt:htt/htt:htt/src:scripts
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
/usr/bin/python3 -m pytest -q tests/test_reboot_statistics.py tests/test_smica_reboot_pilot.py tests/test_reboot_identifiability.py tests/test_reboot_task_packet.py

# 필요할 때만 새 경로로 재현
/home/cosmosapjw/venv/bin/python scripts/calibrate_reboot_statistics.py --demo --B 999 --replicates 1000 --seed 20261014 --output-dir /tmp/reboot_demo_fresh
/usr/bin/python3 scripts/run_smica_reboot_pilot.py --cache workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz --gate docs/generated/k1_e2e_cache_gate_ffp10_smica.json --output-dir /tmp/reboot_smica_fresh
/home/cosmosapjw/venv/bin/python scripts/analyze_reboot_identifiability.py --output-dir /tmp/reboot_response_fresh
/usr/bin/python3 scripts/build_reboot_report.py --output-dir /tmp/reboot_report_fresh
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/reboot_report_fresh /tmp/reboot_report_fresh/reboot_report.tex
```

결과의 한계는 [보고서](results/report/report.md)와 [DELIVERY](DELIVERY.json)에 명시했다. 다음 단계는 metadata를 늘리는 일이 아니라 실제 처리 반응, selected observation law, 물리 provider와 공분산을 연결하고 새로운 결과를 계산하는 일이다.
