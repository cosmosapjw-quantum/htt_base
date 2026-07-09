# HTT v6 strengthened publication bundle

이 번들은 이전 비판을 “주장 축소”로 받지 않고, 반대로 비판 지점을 논문용 방어선과 증명/실험 게이트로 끌어올리기 위한 작업 묶음이다. 핵심 원칙은 단순하다.

1. 틀린 보편명제는 말만 바꾸지 않는다. 더 강한 정리, 즉 정확한 필요충분조건·generic strictness·fail-closed gate로 대체한다.
2. diagnostic_only 상태를 숨기지 않는다. 대신 diagnostic을 출판 가능한 estimand로 승격한다: signed comparator, sharp identified set, rank/null theorem, calibrated e-value/coverage object.
3. 관측 결과 주장은 하나의 closed lane을 끝까지 닫은 뒤 낸다. K1은 Planck PR4/NPIPE 또는 E2E/FFP null, K5는 CF4 hierarchical/selection/Malmquist/correlated-field mocks, DESI는 random/mask/window selection correction을 갖춰야 한다.

## 파일 구성

- `publication_strengthening_plan_ko.md` — 강화형 출판 전략과 우선순위.
- `claim_defense_matrix.csv` — 비판 항목별 강화 주장, 필요한 정리, 필요한 실험, acceptance gate.
- `theorem_upgrade_candidates.md` — 추가 증명 가능한 정리 후보와 proof route.
- `work_packages/work_packages.yaml` — 실행 작업 패키지, 입력, 산출물, 실패 기준.
- `templates/preregistered_analysis_protocol.md` — K1/K5/DESI lane 사전등록 템플릿.
- `templates/reviewer_response_skeleton.md` — “tone down”이 아니라 “stronger theorem/gate로 흡수”하는 심사 답변 뼈대.
- `templates/paper_outline.md` — 실제 논문 구조 초안.
- `web_bibliography.md` — 웹 검색으로 확인한 외부 문헌·데이터 맥락.
- `scripts/strengthening_core.py` — 독립 수치 실험 핵심 함수.
- `scripts/run_strengthening_experiments.py` — 전체 synthetic gate 실행.
- `scripts/claim_gate_tests.py` — 최소 smoke tests.
- `outputs/strengthening_experiments.json` — 실행 결과.

## 재실행

```bash
cd htt_v6_strengthened_publication_bundle
python scripts/claim_gate_tests.py
python scripts/run_strengthening_experiments.py --out outputs/strengthening_experiments.json
```

빠른 확인은 다음처럼 한다.

```bash
python scripts/run_strengthening_experiments.py --quick --out outputs/strengthening_experiments.quick.json
```

## 핵심 실행 결과

- P36: universal strictness는 반례가 있으므로 그대로 방어하면 안 된다. 대신 joint envelope의 sharpness와 generic strictness를 정리로 세우는 방향이 더 강하다. synthetic random phase diagram에서 strict narrowing은 5000회 중 87.7%에서 나타났고, equality counterexample은 joint = naive로 정확히 재현된다.
- Imbens-Manski: interval-identified scalar parameter에 대한 pointwise endpoint coverage는 IM critical value가 nominal을 복구한다. 전체 identified set을 동시에 덮는 더 강한 목표에는 two-sided endpoint/projection interval이 필요하다.
- finite covariance: p=20에서 raw inverse covariance trace bias는 Nsim=300일 때 약 7.5% 과대, Nsim=600일 때 약 3.6% 과대이며 Hartlap correction 후 평균은 1에 근접한다.
- e-values: dependent merge 평균은 0.9969±0.0024로 null expectation ≤1을 만족하고, 200-step Ville crossing rate는 0.0397로 β=0.05 이하를 만족한다.

