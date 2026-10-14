# 모델과 사고 모드 추천

이 프로젝트의 기본 실행은 **GPT-6.1 Sol + High**를 추천한다. 장시간 구현·수치 실행·문서 갱신을 맡기고, 관측 법칙 선택과 물리 식별성의 어려운 판단 및 독립 검토에는 **GPT-6 Astra + Extra High**를 쓴다. 이는 아래 공식 기능 설명과 이 프로젝트의 작업 특성을 바탕으로 한 추천이며, 모델 간 실제 프로젝트 성능을 벤치마크한 결과는 아니다.

| 역할 | 모델 | 사고 설정 | 맡길 일 |
|---|---|---|---|
| 부모, 장기 실행 책임자 | `gpt-6.1-sol` | `high` | goal 선택, DAG 운영, 코드 통합, 분석 실행, 보고서와 다음 작업 연결 |
| 핵심 물리·통계 판단 | `gpt-6-astra` | `xhigh` | null/selection/covariance 법칙, local/global 식별성, 물리 반응과 family 해석 |
| 독립 reviewer | `gpt-6-astra` | `xhigh` | 원본 근거·수식·테스트·실제 그림을 독립적으로 점검 |
| 범위가 분명한 구현 worker | `gpt-6.1-sol` | `medium`, 어려우면 `high` | adapter, 수치 함수, 오류 재현, 의미 있는 테스트 |
| 저비용 worker | `gpt-6-luna` | `medium` | 정확한 경로 탐색, 표·manifest·source 추출, 결정된 변환, 작은 수정 |

전체 DAG의 여러 독립 경로를 한 번에 분담할 때는 부모의 **Ultra**도 적합하다. Ultra는 하위 agent를 활용하는 실행 모드다. 어려운 단일 유도에 더 많은 추론을 주는 **Max**와 목적이 다르다. 이 repo의 부모 포함 최대 4개 agent·production writer 1명 규칙은 어느 모드에서도 유지한다. reviewer는 재귀 reviewer를 만들지 않는다. 모든 worker를 Ultra/Max로 고정하지 않는다.

Luna에게 null의 타당성, Bianchi 식별, likelihood factorization, 과학적 수용 판정을 단독 위임하지 않는다. 작은 작업에서도 단위·frame·selection·같은 하늘의 의존성 문제가 발견되면 Sol 또는 Astra로 올린다. 동일한 실패를 프롬프트만 바꿔 반복하지 말고, 구체적인 반례와 실패 입력을 전달한다. 모델 수준을 높이는 것으로 누락 자료나 틀린 물리 전제를 해결했다고 취급하지 않는다.

## 기존 checkout에서 시작

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
codex -m gpt-6.1-sol -c 'model_reasoning_effort="high"'
```

그 뒤 [handoff](CODEX_HANDOFF_KO.md)의 text block을 붙여 넣는다. `/model`에서 모델과 사고 수준을 바꿀 수도 있다. Work에서는 입력창 아래 모델 선택기를 사용한다. 원하는 옵션이 실제 client에 표시되지 않으면 사용 가능한 모델/effort를 확인해 기록한다. 이 문서는 전역 설정 파일을 바꾸지 않는다.

2026-10-14 원격 로컬 설정은 `gpt-6-sol` / `medium`이었고, 같은 날 갱신된 모델 목록은 `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna`와 위의 설정을 광고했다. 이는 **client의 광고된 지원**이지 각 향후 run이 해당 모델에서 실행됐다는 증명은 아니다. run별 requested/observed model과 effort를 분리하고 관찰할 수 없으면 UNKNOWN으로 남긴다.

## 근거와 적용 범위

공식 문서를 2026-10-14에 직접 열어 확인했다. 공식 권고는 복잡한 agentic coding에 Sol, 범위가 좁은 반복 작업에 Luna를 연결하며, 모델/effort의 가용성은 계정과 client에 따른다. 이 프로젝트의 역할별 배분과 High/Extra High 선택은 그 설명에 근거한 운영 판단이다.

- [OpenAI 모델과 Codex 모델 선택](https://learn.chatgpt.com/docs/models)
- [OpenAI reasoning effort](https://developers.openai.com/api/docs/guides/reasoning)
- [Codex model_reasoning_effort 설정](https://learn.chatgpt.com/docs/config-file/config-reference)

Codex의 Ultra를 API `reasoning.effort` 값으로 그대로 옮기지 않는다. API의 reasoning mode와 effort, Codex의 UI 실행 모드를 구별하고 실제 API의 지원값을 확인한다. 비교 가격이나 절감률은 측정하지 않았으므로 숫자로 약속하지 않는다. machine-readable 배분은 [MODEL_POLICY.json](MODEL_POLICY.json)에 있다.
