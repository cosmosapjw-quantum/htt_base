# CAS05 v3 중립 입력 정합 PASS

Host는 현재 소유자 요청에 따라 원문 정의를 별도 v3 후속 계약에 승인·결속하고,
**입력 정합 HOLD → PASS**로 판정했다. 기존 v2와 그 HOLD 기록은 수정하지 않았다.
CAS05 독립 4축은 아직 실행하지 않았으며 CAS_4AXIS_PASS는 아니다. CAS04는
CAS_BLOCKED, CAS06 입력과 해석적/과학적 admission은 HOLD를 유지한다.

원문 `gr/ENERGYFRAME_THEOREMS.md` EF3에는 H00=0, H0i=Hi0, 공간 r²,
모든 cubic H 성분과 배경 metric이 실제로 있었다. 이를 source-only 중립 입력에
명시했다. 원래 metric은 `exp(2phi0) eta + H`이고, polynomial은 정확한 metric
3-jet 대표 `eta + 2phi0 eta + H`다. 이 구분, index 전치, 차원, coefficient W와
kinematic W의 구분, 12개 k basis와 Bianchi 미분 차수를 계약에 결속했다.
미래 blind author는 원문 증명이나 이번 진단 코드를 받지 않는다.

실제 Python 3.12.3 / SymPy 1.14.0에서 로컬 모델 payload를 읽어 **477개 검사,
12개 basis image, 전체 40개 Einstein 1차 미분 계수**를 검증했다. 이는 입력
진단이며 독립 SymPy campaign 축 PASS가 아니다. 원래 validator의
`wrong_right_inverse` 음성 대조 이름은 과도했다: t*x² 변경은 입력 결속만
깨뜨린다. 동결 코드를 보존하고 t*y² 변경을 별도 검사해 mixed residual −t와
12개 basis 실패를 확인했다. 자세한 범위는 `GEOMETRIC_NEGATIVE_CONTROL.json`에 있다.

Managed Devstral CPU를 실제 2회 사용했다. 첫 응답은 미정의 이름과 잘못된
성분 전개로 거부됐다. 실패·raw·786 tokens를 보존하고, sym/skew 행과 quadratic
scalar를 명시하는 Host 지침으로 prompt를 수리했다. 두 번째 응답 839 tokens는
수학적 내용을 고치지 않고 단일 외곽 JSON fence만 제거한 뒤 통과했다.
합계 **1,625 new tokens**, 알려진 이전 local 6,038을 포함한 누계는 **7,663**이다.
이는 Host-guided 기계적 전개/직렬화 helper의 유한 적합성이다. 일반 CAS 유도
능력이나 general/prover 모델의 새 검증으로 확대하지 않는다. 두 lease는 종료됐다.

독립 reviewer는 실제 **gpt-6-astra/ultra**로 관측됐다. 입력 범위 내 미해결
중대 finding이 없다는 보고를 받고 Host가 최종 판정했다. reviewer는 별도
Ricci contraction, 실제 payload의 477개 검사와 음성 대조를 직접 확인했다.
reviewer 사용량은 **2,743,351 total tokens**, 그 중 cached input **2,625,536**이다.
cached input은 total에서 빼지 않으며 reasoning은 output에 이미 포함된다.
이번 Host 관측 창은 durable `HOST_USAGE_WINDOW_FINAL.json`에 별도로 기록한다.
전체 역사·통화 비용·인과적인 절약량은 NOT_MEASURED다. 목표 초과는 계속/재계획
대상이며 과학적 STOP_BUDGET나 local attempt cap으로 처리하지 않았다.

원래 과학 파일 **1,713개**와 사용자 tracked 변경 **4개**의 해시를 보존했다.
이전 Codex JSONL와 `/mnt` 반환·review·publication 자료를 함께 조사했으며,
원문/계약/실행/raw/lease/비용 결속은 다음 durable 디렉터리에 있다:
`/mnt/sn850x2t/local_ai_foundry/70_experiments/cuhg_cas05_neutral_admission_20261003/`.
첫 telemetry wrapper 옵션 오류는 엔진 시작 전 실패로 남겼고, 수정 호출은
실제 exit 0이다. 기존 완료 campaign 축은 재실행하지 않았다.

관련 전역 하네스 소스 변경은 없어 설치 authority
`d32480138583652abc40efc61cbdcbcfb8a647b8`을 유지한다. 이번 게시 commit/원격
ref와 R1 확인은 durable `RETURN.json`, `VERIFICATION.json`을 참조한다.

다음 단일 작업은 **v3 중립 입력을 사용하는 CAS05 C01–C03 독립 4축 유한 실행**이다.
`HANDOFF_PROMPT_KO.md`에 입력 해시 확인 명령, blind 입력 경계, local prompt 수리,
누적 비용 보존, runtime 및 판정 조건을 적었다.
