# Phys–Math Coding Harness for GPT-6 Astra · v4.0.0

물리·수학 연구 코드를 위한 저장소 하네스다. 기존 GPT-5.6 v3.1.0의 scientific contract, validation matrix, 상태·실패 보존 구조를 유지하면서 GPT-6 Astra에서 승인된 목표의 자율 완결, 필요한 context 선택, 생산적인 수정 지속, 검증 종료 조건을 명료하게 했다. 모델 성능·비용 개선은 미측정이다.

## 안전하게 적용하기

ZIP은 먼저 **기존 repo와 다른 새 staging 디렉터리**에 푼다. 기존 repo 루트에 archive 전체를 바로 덮어쓰지 않는다. 이 패키지의 `AGENTS.md`, contracts, prompts를 기존 프로젝트 값과 검토·병합한다. 기존 코드, 과학 기준, 로그와 `.agents/skills/`를 보존한다. 개인 스킬을 설치하는 패키지가 아니다.

staging package에서 먼저 구조를 점검한다:

```bash
python3 tools/validate_harness.py --json
```

상태 초기화는 없는 파일만 생성하고 빈 파일을 포함한 기존 파일을 바이트 그대로 유지한다. 검토·병합한 repo에서 `python3 tools/init_harness.py`를 실행하거나 staging에서 명시적으로 기존 repo 경로를 지정한다:

```bash
python3 tools/init_harness.py --root /absolute/path/to/existing/repo
```

`--force`는 v4에서 제거했다. 초기화는 설치·병합이나 기존 상태 리셋을 수행하지 않는다. repo 적용 후 project contract와 실제 실행 명령을 채운다.

## 시작

`START_HERE.md`와 `docs/MODEL_ROUTING.md`를 읽는다. 작은 작업은 `prompts/00_ultralight.md`, 복잡한 단일 목표는 `prompts/01_deep_once.md`를 사용한다. phase 파일은 필요한 단계만 읽는 reference다. 단계가 끝날 때마다 작업을 중단하거나 재승인을 요청하지 않는다.

단일 owner가 승인된 계약 안에서 재현·위치 특정·설계·수정·검증을 완료한다. 근거가 있는 repair는 acceptance까지 계속하며 blind retry와 review recursion만 제한한다. 보호된 물리 의미·approximation·closure·tolerance·SSOT를 새 승인 없이 바꾸지 않는다.

구조 validator의 PASS는 패키지 구조만 뜻한다. 프로젝트 과학적 acceptance와 GPT-5.6 대비 모델 성능은 별도 실제 평가가 필요하다. `.agents/skills/` 다섯 파일은 원본 v3.1.0의 bytes 그대로 보존했다.
