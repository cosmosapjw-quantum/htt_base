# GPT-5.6 → GPT-6 Astra: 설계 변경의 근거

작성·확인일: 2026-09-08 UTC. 출발점은 사용자가 첨부한 research/coding v3.1.0이다. 새 버전은 v4.0.0이며, 모델 이름을 바꾼 복사본이 아니라 Astra의 공식 행동 안내와 사용자의 연구 원칙에 맞춘 실행 계약 개정이다.

## 근거 상태

| 확인된 근거 | 이번 설계에 반영한 판단 | 한계 |
|---|---|---|
| [OpenAI Astra 이전 안내](https://developers.openai.com/api/docs/guides/latest-model), Prompting best practices | 조기 중단·추가질문·지침 충돌·위임 부족·과도한 테스트에 대응해 유효 승인, 선택적 phase, 독립 위임, 종료조건을 명료화 | 공식 보고에 근거한 설계다. 이 하네스의 성능 측정 결과가 아니다 |
| [Astra 모델 명세](https://developers.openai.com/api/docs/models/gpt-6-astra) | API ID는 `gpt-6-astra`; API reasoning effort와 호스트 설정을 구분 | 모델 가용성은 실행 환경에서 별도 확인 |
| [OpenAI 평가 지침](https://developers.openai.com/api/docs/guides/evaluation-best-practices) | 작업별 성공조건과 변경 전후 비교를 먼저 정하고, 구조 검사와 모델 행동 평가를 분리 | `docs/MODEL_REGRESSION.md`의 비교 실험은 아직 미실행 |
| [Huang 외, ICLR 2024, v2](https://arxiv.org/html/2310.01798v2) | 자체 확신 대신 외부 피드백·독립 계산을 교정 근거로 삼고, 비교 정보와 비용을 맞춤 | 당시 모델·과제의 결과이며 Astra의 자기교정 불가능성을 뜻하지 않음 |
| [PROVE, v2](https://arxiv.org/html/2410.12608v2) | 프로그램 실행을 검증 근거로 쓰되 해답을 코드로 번역하는 오류와 형식 증명을 구별 | 프로그램 기반 선별은 일반적인 물리적 타당성 증명이 아님 |

SciSpace에서 자기교정과 독립 검증에 관한 자연어 질문 1회로 문헌을 찾은 뒤 위 논문 원문을 확인했다. 검색 초록과 판본 내용이 다르면 확인한 원문 판본을 따른다. 원본의 다른 문헌 목록은 이번에 모두 검증한 목록이 아니며 `docs/RESEARCH_BASIS.md`에서 inherited 근거로 분리했다.

## 이 패키지가 선택한 정책

- 한 owner가 원래 연구 동기, 과학 계약, 상태와 결과 통합을 맡는다. 연구 후보의 최종 PROMOTE는 원본과 같이 독립 decision reviewer의 판정을 요구한다. 독립적인 원전 확인·대안 유도·diff 검토만 명시된 입력과 산출물로 위임한다. 동일 모델의 다수결은 과학적 증거가 아니다.
- 전체 phase 문서를 매번 주입하지 않는다. 핵심 instructions와 현재 상태를 읽고, 다음 판단에 필요한 phase만 추가한다. 실제로 필요한 유도·계산·구현을 산출한다.
- 탐색의 범위를 임의의 후보 개수로 제한하지 않는다. 수렴은 사용자 scope, 판별력, 실행 자원과 명시된 criterion으로 결정한다. novelty는 검증과 구별하되 연구 동기를 지운 채 통상적 문제로 대체하지 않는다.
- 이미 승인된 목표 안의 생산적인 수정은 acceptance 또는 구체적 blocker에 도달할 때까지 진행한다. 추가 검증은 남은 위험을 해소할 때 수행한다. 새로운 정보 없이 리뷰만 되풀이하지 않는다.
- checksum은 동일한 바이트를 확인한다. scientific authority, source authenticity, 실행 권한, 수학적 타당성까지 보장하지 않는다. 반대로 bytes가 달라도 허용된 의미 동일성이 증명되면 그 범위를 기록한다.

## API와 호스트 설정

공식 API effort는 `low / medium / high / xhigh / max`다. `none`은 미지원이다. 도구 호출은 Responses API를 사용하며 `temperature`, `top_p`, `top_logprobs`를 전송하지 않는다. 기존 effective effort를 관측한 뒤 명시적 필요 없이 올리지 않는다. Work/Codex가 별도로 제공하는 effort 이름을 API enum으로 복사하지 않는다. 이 ZIP은 API client를 실행하거나 설정 파일을 변경하지 않는다.

실행 중 도착하는 사용자 보완은 기존 목표에 통합하고 완료된 결과를 보존한다. 실제 호스트가 지원하는 병렬 도구 호출만 사용하며, 의존하는 호출과 외부 mutation은 순서대로 처리한다. 런타임 기능·단가·토큰량을 추정해 성능이나 비용 절감 수치를 만들지 않는다.

## 결론의 상한

`design_status = SOURCE_SUPPORTED_ADAPTATION`

구조 검사·라우팅 테스트·초기화 검증의 실제 결과는 `RELEASE_VALIDATION.json`을 따른다. 이것들은 연구 결과의 정확도나 GPT-5.6 대비 개선율을 입증하지 않는다. `cross_model_performance = NOT_EVALUATED`를 유지한다.
