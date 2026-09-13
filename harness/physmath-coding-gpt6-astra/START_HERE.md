# Start Here — GPT-6 Astra v4.0.0

1. `docs/MODEL_ROUTING.md`로 실제 선택 모델에 맞는 하네스를 고른다. 패키지 이름만 보고 runtime 모델이 전환됐다고 주장하지 않는다.
2. 안전한 staging에서 `python3 tools/validate_harness.py --json`으로 **package structure만** 점검한다. 적용은 `README.md`의 병합 절차를 따른다.
3. `AGENTS.md`, 현재 task contract, 프로젝트 값을 채운 `SCIENTIFIC_CONTRACT.md`, 관련 `VALIDATION_MATRIX.md` 행을 읽는다. 복구라면 실제 파일·source·실행 상태를 확인하고 `RUN_STATE.md`와 필요한 증거만 더 읽는다.
4. 작은 목표는 `prompts/00_ultralight.md`, 복잡한 목표는 `prompts/01_deep_once.md`를 사용한다. phase 목록 전체를 매번 로드하지 않는다.
5. 이미 승인된 bounded objective는 owner가 acceptance까지 수행한다. 한 repair cycle 안에서 필요한 여러 edit/test/diagnose를 진행한다. phase 사이에 자동 승인 대기를 삽입하지 않는다.
6. 실제 구현·과학·수치 증거와 claim ceiling을 남긴다. 중요한 변경은 독립 review를 수행하고 관련 필수 gate가 충족되면 산출물을 완결한다.

API effort와 호스트 UI effort는 같은 enum이라고 가정하지 않는다. 실행 가능한 tool·effort·model을 확인하고 지원되지 않는 값이나 측정하지 않은 성능·가격을 만들지 않는다.
