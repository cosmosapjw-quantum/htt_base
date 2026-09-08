# HTT R7: tensor morphology to joint physical inference

2026-09-08 · 연구·설계 인계판 · 기준: `5702024e06eff4979087f07f86ee7131d13961ac`.

**중심 질문:** 관측된 저다중극 형태와 깊이별 신호에서 어떤 물리적 조합이 자료로 식별되고, 어떤 결론이 복사장·전경·고다중극·보정 가정에 의존하는가?

이번 문서는 원심사 R1/R2, 확장안 A1, R2/R3 이론 및 R6 독립 감사를 이어받아 실행 가능한 연구 설계로 연결한다. 원심사 요구, 장기 확장 목표, 이번 새 유도를 구분한다. 실제 관측 결과는 Local Codex 실행 뒤 생성한다. 수학적 비식별성, 기각, 조건부 경계, 추가 자료의 필요성도 각각 유효한 종료 결과다.

## 먼저 읽을 순서

| 문서 | 결정하는 사항 |
|---|---|
| [SCIENTIFIC_CONTRACT.md](SCIENTIFIC_CONTRACT.md) | 실험·변수·모형·자료 사용 범위 |
| [THEORY.md](THEORY.md) | 수식, 가정, 새 연구 결과와 한계 |
| [R3_MODEL_REFERENCE.md](R3_MODEL_REFERENCE.md) | 기존 제한 모형의 구현에 필요한 보존·복사·광학 수식 |
| [DESIGN.md](DESIGN.md) | 모듈 소유권·입출력·결과 분기 |
| [campaign_dag.json](campaign_dag.json) | 기초 검증부터 자료 분석·최종 합성까지의 기계 판독 DAG |
| [LOCAL_CODEX_PLAN.md](LOCAL_CODEX_PLAN.md) | 수정할 파일, 실행 순서, 수용 기준 |
| [OWNED_ASSETS.md](OWNED_ASSETS.md) | 보유 관측자료·외부 코드/라이브러리별 관측량·우도·control·DAG 연결 |
| [REUSE_MAP.md](REUSE_MAP.md) | H와 병렬/legacy 구현의 재사용·수리 구분 |
| [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) | 정확 검산·수치·통계·실자료 검증 계약 |
| [REVIEW_RESPONSE.md](REVIEW_RESPONSE.md) | 원심사·확장안별 대응과 논문 구성 |
| [state/CLOSEOUT.md](state/CLOSEOUT.md) | 이번 실제 완료 범위와 다음 실행 지점 |

## 연구 구조

1. **형태와 관측 연산:** full Q/O와 절대 프레임을 보존한다. 완전 packet, multipole vectors, power/alignment, `f_B`의 성능을 같은 자료에서 비교한다. 차트 실패는 full tensor 경로로 흡수한다.
2. **물리 상태와 공동집합:** tensorized MES의 텐서 방정식을 먼저 유지하고, shear·vorticity·tilt 및 불변량은 동일한 허용 상태에서 함께 계산한다. 단일 하늘만으로 미분·모든 관측자 전제를 추론하지 않는다.
3. **local/global 판별:** 네 high-source nuisance 법칙을 동일 관측 모형에서 비교한다. CF4·DESI의 깊이 응답과 JWST 보정을 공유 nuisance와 연결한다. 응답 kernel과 약한 식별을 먼저 보고한다.
4. **동역학 비교:** 기존 BASS 및 첨부 kinetic/optics는 R3 보존법칙의 검증 도구로 사용한다. 지원 범위가 확인된 외부 Bianchi transfer는 별도의 조건부 물리모형 분기다.

최소 방법론 논문은 1–2의 관측 검증으로 닫을 수 있다. 3은 다중 자료 논문, 4는 모형별 물리 제약의 후속 논문으로 연결한다. 어느 한 모형의 기각이 다른 논문의 계산을 중지시키지 않는다.

## 선택한 설계와 버린 대안

| 대안 | 장점 | 판정 |
|---|---|---|
| `f_B` 단일 주검정 유지 | 가장 작은 수정 | full morphology와 MES 공동 추론을 충족하지 못하여 중심 설계로 채택하지 않음 |
| native solver 완성 뒤 모든 분석 시작 | 하나의 완결 모형에 집중 | 외부 의존성과 구조적 대칭 때문에 기존 관측·방법론 성과까지 지연하므로 채택하지 않음 |
| 기존 모듈 + full tensor carrier + 공동 실험 + 분기별 추론 | 기존 구현을 살리면서 실패도 해석 가능 | **채택**. 공유 데이터는 한 번 생성하고 여러 읽기 전용 분석기가 소비 |

## 실행과 이력의 관계

이 캠페인은 사용자가 요청한 **공식 재계획 설계**다. 기존 M1/M2/M3와 THEORY_FREEZE의 과학적 의무를 없애거나 완료로 바꾸지 않는다. 이전의 단일 전역 release 대신, 명세·입력·검증이 충족된 분기만 실행한다. 이전 PR의 상태와 관측값은 그대로 보존한다. 특히 무효화된 DESI PR-151 결과값은 재사용하지 않고 원시 자산과 처리 코드만 재검증 대상으로 사용한다. PR4/NPIPE 자료 획득·분석 제외 지시는 유지한다.

새 하네스 두 개는 모두 **3.1.0**이며 연구 phase와 coding design phase에 적용했다. 저장소의 기존 AGENTS·harness를 교체하지 않는다. GitHub 읽기·문헌 대조·해석적 연구·문서/DAG 검사와 실제 과학 실행은 구분하여 기록한다. Wolfram 연결은 MCP 서버 오류로 사용할 수 없었으며 CAS 검증은 실행 완료로 세지 않는다.
