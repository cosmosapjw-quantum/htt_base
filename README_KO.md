# 비용 라우터 (cost_router) 사용 안내

API 크레딧(월 약 $100)을 "싼 모델로 먼저, 검증 실패한 것만 위로" 방식으로 쓰는 도구 모음이다.
네트워크 호출은 `cascade_runners.py`에만 있고, `cost_router.py`는 가격·정책·장부만 가진다.

| 파일 | 역할 |
|---|---|
| `cost_router.py` | 가격표, 비용 계산, 사다리(rung), 난이도 클래스, 비용 상한, 장부, 예산 가드 |
| `cascade_runners.py` | Batch 캐스케이드(기본), async 스트리밍 실행기, CLI(`plan`/`run`/`report`) |
| `test_cost_router.py` | 오프라인 테스트 15개 (`python3 test_cost_router.py`) |
| `tasks.example.jsonl` | 작업 파일 예시 |

## 1. 설정 전 확인

1. 크레딧이 들어 있는 Console 조직의 API 키를 쓴다. `ANTHROPIC_API_KEY` 환경변수로만 넘기고 저장소에 커밋하지 않는다.
2. 월 API 크레딧은 API·Agent SDK(API 키 인증)·Managed Agents·플레이그라운드에서만 차감된다. Claude Code 구독 사용량이나 앱 추가 사용량과는 별개다. 이월되지 않는다. 소진되면 요청이 멈춘다.
3. Console의 워크스페이스 지출 한도를 $100 근처로 걸어 둔다. 이 도구의 `Budget`은 소프트 가드이고, 지출 한도가 하드 백스톱이다. 한도에 걸리면 HTTP 400이 오며 재시도 대상이 아니다.
4. 가격과 모델 ID는 `cost_router.py` 상단 `PRICES`에 있다. 공식 가격표와 다르면 거기만 고친다.

## 2. 사다리와 난이도 클래스

사다리(싼 쪽에서 강한 쪽): `haiku_low`(thinking 끔) → `haiku_high` → `sonnet_medium` → `sonnet_high` → `opus_medium` → `opus_high` → `opus_xhigh` → `fable_high` → `fable_xhigh`.

| 클래스 | 바닥 | 최종(terminal) | 검증기 없을 때 1회 실행 |
|---|---|---|---|
| mechanical (형식 변환, 단순 반복) | haiku_low | sonnet_high | haiku_high |
| routine | haiku_high | opus_medium | sonnet_high |
| analysis | sonnet_medium | opus_xhigh | opus_high |
| hard (증명 검토, 어려운 유도) | sonnet_high | fable_xhigh | fable_high |

`effort`는 `output_config.effort`로 전달한다. 모델을 바꾸기 전에 effort부터 조정하라는 공식 지침을 따라, 같은 모델 안에서도 낮은 effort 칸을 먼저 둔다.

## 3. "싼 모델 연속 실패가 강한 모델 한 번보다 비싸지는 것"을 막는 규칙

1. **비용 상한(ALPHA).** 한 작업이 최종 rung 아래에서 쓸 수 있는 누적 비용은 최종 rung 1회 추정 비용의 `alpha`(기본 0.5)배까지다. 다음 칸의 추정 비용이 남은 상한을 넘으면 중간 칸을 건너뛰고 곧바로 최종 rung으로 간다. 최악의 경우 작업당 비용은 강한 시도 1회의 (1 + alpha)배다.
2. **같은 실패 서명이 반복되면 즉시 최종 rung.** 검증기가 같은 오류 서명을 두 번 내면 더 싼 칸을 올라가며 반복하지 않는다.
3. **최종 rung은 1회만.** 같은 능력으로 재시도해도 잘 안 풀린다는 공식 지침에 따라, 최종 rung 실패는 `FAILED`로 끝내고 사람에게 넘긴다.
4. **검증기 없는 작업은 한 번만.** 실패 신호가 없으면 캐스케이드가 성립하지 않으므로 고정 rung에서 1회 실행하고 `DONE_UNVERIFIED`로 표시한다.
5. **시작 rung은 기대 비용 최소화로 고른다.** 각 (클래스, rung)의 성공률 prior와 장부에 쌓인 실측으로 계산한다. 싼 칸의 성공률이 낮게 관측되면 시작점이 자동으로 올라간다.
6. 실제 청구액은 `usage`에서 계산해 장부에 기록한다(캐시 읽기/쓰기, Haiku 100k 초과 구간, 배치 50% 반영).

## 4. 병렬 실행

- **Batch 모드(기본, `--mode batch`).** 라운드마다 모든 대기 작업을 한 배치로 제출한다. 한 배치 안에 모델이 섞여도 된다. 입력·출력 모두 50% 할인이고 프롬프트 캐싱과 합산된다. 실패한 작업만 다음 라운드에서 한 칸 위로 올라간다. 응답은 분~시간 단위로 늦을 수 있다.
- **async 모드(`--mode async`).** 스트리밍으로 즉시 실행한다(정가). 모델별 동시성 제한기가 작게 시작해 성공하면 올리고, 429가 오면 절반으로 줄이며 `retry-after`를 지킨다. Fable 버킷은 작아서 기본 동시성이 낮다. `enforced_spend_limit_reached`는 재시도하지 않고 중단한다.
- `errored`/`expired`/`canceled` 배치 항목은 과금되지 않는다. 같은 rung에서 최대 2회 재시도하고, `invalid_request_error`는 `ERROR`로 표시한다.
- 중단 후 `--resume`으로 이어 가면 장부를 재생해서 이미 낸 요청을 다시 결제하지 않는다.

## 5. 사용법

```bash
export ANTHROPIC_API_KEY=...          # 크레딧이 있는 조직의 키
python3 cascade_runners.py plan tasks.jsonl --budget 100      # 호출 없이 예상 비용·경로만 출력
python3 cascade_runners.py run  tasks.jsonl --budget 100 --out results.jsonl
python3 cascade_runners.py run  tasks.jsonl --budget 100 --resume   # 중단 후 재개
python3 cascade_runners.py report --ledger ledger.jsonl       # rung별/클래스별 지출, 풀린 작업당 비용
```

`tasks.jsonl` 한 줄 형식: `{"id","klass","system","prompt","verifier":{"cmd":[...],"timeout":600}}`.
검증기는 모델 출력을 stdin으로 받는 명령이다. 종료 코드 0이 통과이고, 실패 시 stdout 마지막 줄이 실패 서명이다. 출력 뒤쪽 2000자는 다음 rung의 재시도 프롬프트에 붙는다.

`results.jsonl`: `{"id","status","klass","rung","spent_usd","nonterminal_usd","text"}`. status는 `SOLVED`, `FAILED`, `DONE_UNVERIFIED`, `BUDGET_STOP`, `ERROR` 중 하나다.

## 6. 먼저 확인할 것

- **prior 성공률은 추정값이다.** 처음 20~30개 작업을 돌린 뒤 `report`로 rung별 통과율을 보고, 장부가 prior를 덮어쓰는지 확인한다. 공식 지침도 자기 워크로드로 평가를 만들고 "풀린 작업당 비용"으로 비교하라고 한다.
- **검증기 품질이 전부다.** 검증기가 느슨하면 싼 모델의 오답이 통과한다. 증명 쪽은 CAS 게이트나 Lean 컴파일 같은 실제 실행 결과만 검증기로 쓰고, 모델이 모델을 채점하는 방식은 피한다.
- **advisor/orchestrator 패턴은 기본으로 끄고 둔다.** 공식 자료에서도 싼 실행 모델이 조언 도구를 자발적으로 거의 부르지 않는다는 관찰이 있다.
- `thinking: disabled`가 거부되는 rung은 실행기가 400 응답 후 `thinking` 필드를 빼고 재시도한다(async 모드).
- 아직 실제 API로는 돌려 보지 않았다. 오프라인 fake 클라이언트 테스트만 통과한 상태다. 첫 실행은 `--budget 2` 정도의 소액으로 하고 `report`를 확인한 뒤 올린다.

## 7. 증명 DAG와 병렬 실행의 경계

`PROOF_DAG.json`의 `serial_policy`는 한 번에 증명 단위 하나, 네 축은 fresh context에서 순차 실행, 등록된 지원 경로만 사용, 중첩 subagent 금지를 요구한다. 그래서 **증명 검증 자체는 이 라우터로 병렬화하지 않는다.** 병렬로 돌려도 되는 것은 다음뿐이다.

- 사람 결정이나 후속 계약이 필요한 노드(GR-CAS-04, 11, 18, NEEDS_SUCCESSOR 13개)의 분석 메모와 요구사항 초안. 검증기가 없으므로 `DONE_UNVERIFIED`이고, 결과는 비권위(non-authoritative)로 표시해서 쓴다.
- 형식 변환, 경로 정리, IGT 포맷 점검 같은 단발 작업.

Claude Code를 축 작성자 경로로 등록할지는 저장소 소유자 결정이다(`~/.codex/runtime/global-execution-policy.json`). 이 도구는 그 정책을 우회하지 않는다.
