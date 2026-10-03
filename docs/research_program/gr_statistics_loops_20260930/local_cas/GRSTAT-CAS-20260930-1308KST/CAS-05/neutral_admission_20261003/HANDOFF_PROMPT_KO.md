# CAS05 중립 입력 후속 실행 prompt

작업 루트는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`다. 기존 checkout을 사용하고
사용자 변경을 보존한다. 먼저 이 디렉터리의 `RETURN.json`과 durable publication
receipt를 읽어 **실제로 검토·게시된 입력 판정**과 commit을 확인한다.

이번 다음 작업은 **GR-CAS-05 C01–C03의 v3 중립 입력에 따른 독립 4축 유한 검증**이다.
논리 task는 `GRSTAT-CAS-20260930-1308KST-CAS-05`, run은
`GRSTAT-CAS-20260930-1308KST`를 유지한다. 과거 v2의 입력 HOLD, CAS04의
CAS_BLOCKED, 실패·STOP_BUDGET·raw·usage·launch/lifecycle를 수정하지 않는다.
CAS06 입력 정합과 해석적 증명/과학적 admission은 별도 HOLD다.

## 먼저 할 한 가지

아래 명령으로 새 계약의 입력 byte identity를 확인한 뒤, 새 **blind axis author**에게
허용된 세 입력만 전달하여 CAS05를 시작한다. 기존 성공한 다른 CAS 단위는 재실행하지 않는다.
Host가 읽은 진단 코드·결과·원문 증명은 새 blind author에게 넘기지 않는다.

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
python3 - <<'PY'
import hashlib, json
from pathlib import Path
p = Path('docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/EXECUTION_CONTRACT_V3.json')
c = json.loads(p.read_text())
assert c['identity']['contract_version'] == 3
for ref in c['identity']['source_input_hashes']:
    assert hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest() == ref['sha256'], ref['path']
old = c['identity']['successor']
assert hashlib.sha256(Path(old['predecessor_path']).read_bytes()).hexdigest() == old['predecessor_sha256']
print('V3 INPUT BINDINGS PASS; proceed to fresh CAS05 author dispatch')
PY
```

Blind author가 읽을 입력은 정확히 다음 세 개다.

1. 이 디렉터리의 `EXECUTION_CONTRACT_V3.json`.
2. 이 디렉터리의 `NEUTRAL_INPUT.json`.
3. `docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md`.

`gr/ENERGYFRAME_THEOREMS.md`는 Host/source-admission reviewer가 실제 정의를
확인한 provenance다. 원문의 유도와 결과를 author 입력으로 사용하지 않는다.
원문에서 확인한 H00=0, r², 대칭 H, 배경 metric은 중립 입력에 명시적으로 승인됐다.
새 계약의 version 3은 기존 구조 schema 2를 유지하는 별도 후속 계약이다.
기존 C03 statement pointer는 `/semantics/exact_statement/2`이고,
`/semantics/exact_statement/3`은 존재하지 않는다.

## 유한 의무와 실행

- C01: conformal metric에서 Christoffel/Ricci/Einstein을 직접 유도하고 원점
  stress/gap와 미분된 유한 eigenvector 방정식, acceleration/rate를 검증한다.
- C02: 명시된 ray의 orthonormal-frame stress contraction을 계산한다. gap이
  사라지는 점에서 고유 eigenframe 존재를 가정하거나 λ=0으로 나누지 않는다.
- C03: cubic H의 모든 대칭 성분, j²H=0, 12개 k basis, Einstein의 전체 40개
  1차 미분 성분과 원점 Bianchi 4개를 검사한다. S/W는 coefficient sym/skew이며
  COMMON_SPEC의 kinematic tensor와 혼동하지 않는다. δG 식은 1차 jet 식이다.

Wolfram/xAct, SymPy, Sage/Singular, Lean의 required 범위를 유지한다. 각 author의
source/raw/argv/cwd/exit/version과 실제 모델/effort를 기록하고, 결과를 서로
읽기 전에 독립 제출한다. Wolfram은 on-demand kernel과 실제 존재하는 cwd,
Sage Python은 `sage -python`, Singular는 실제 interpreter로 실행한다.
Lean은 계약에 결속된 `formal_mathlib` toolchain을 사용한다. kernel 통과와
수학적 statement alignment를 둘 다 확인한다. `sorry`, target axiom, rank-only
증명, 출력 상수 true는 허용하지 않는다. Host 입력 diagnostic을 독립 축 PASS로
재사용하거나 completed CAS01/C02/C03/C04 campaign을 재실행하지 않는다.

## 로컬 helper와 자원 계획

현재 authority의 `docs/CAS_LOCAL_ASSISTANCE.md`와 managed fleet를 사용한다.
입력 locator 같은 정확한 성공 receipt는 재사용한다. 새 cubic-H 성분 전개는
이번 durable `LOCAL_HELPER_FREEZE.json`, raw request/response, managed lease,
external validation에 기록돼 있다. 이는 Devstral의 **좁은 transcription helper**
적합성이며 general/coder/prover 전체 또는 CAS05 과학 적합성 인증이 아니다.
동일 모델을 다른 좁은 역할로 쓸 수 있지만 각각 실제 payload를 CAS/Lean으로
검증한다. 새 capability를 기존 세 capability ID로 위장하지 않는다.

큰 증명을 통째로 위임하지 말고 정확한 정의·index·출력 schema와 고정 validator가
있는 coefficient 전개, CAS syntax, 작은 Lean lemma로 나눈다. 결과가 잘리면
더 작은 요청/continuation으로 이어가고, 실패 시 실제 validator 잔차를 넣어
prompt를 수리한다. 전용 Qwen/DeepSeek/Kimina의 과거 runtime 실패를 유능한
다른 좁은 helper까지 배제하는 근거로 사용하지 않는다. 모든 호출은 managed
lease와 CPU/GPU/RAM/no-swap 보호 아래 실행한다.

Native token/cost 목표는 advisory다. 초과하면 정확한 누적량과 identity를 보존해
다음 행동을 재계획하고 계속한다. Local task token/attempt ceiling은 없다.
기계적 context/output 및 process timeout은 별개다. 불명확한 in-flight work는
정확한 lease/process를 먼저 reconcile한다. unknown spend를 0으로 간주하거나
새 task ID로 비용을 초기화하지 않는다. 기존 알려진 local 6,038 tokens와 이번
실제 사용량, 과거 native 기록의 포함 관계는 `RETURN.json`을 따른다.

## 판정과 반환

입력 정합 PASS, 각 엔진 실행, 독립 axis PASS, CAS_4AXIS_PASS, 전체 해석적
정리와 scientific admission을 구분한다. smooth eigenfield/IFT, Lorentzian/DEC
neighborhood, CAS04의 Wolfram projection 연결, EF6/CAS06 의무를 유한 PASS로
해제하지 않는다. 필요한 실제 reviewer profile을 등록하고 최종 claim은 Host가
판정한다. raw와 실패를 보존하고 한국어 RETURN, 비용/lifecycle, 다음 한 작업을
반환한다. 게시 시 non-force push와 R1 ref verification을 수행한다.

근거 위치:
`/mnt/sn850x2t/local_ai_foundry/70_experiments/cuhg_cas05_neutral_admission_20261003/`.
그 안의 `PRIOR_EVIDENCE_AUDIT.json`은 직전 Codex JSONL와 별도 `/mnt` 자료를
함께 결속한다. `RETURN.json`/`VERIFICATION.json`이 이번 실제 결과의 기준이다.
