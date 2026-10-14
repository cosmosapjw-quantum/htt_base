# C04 로컬 재검증 인계

새 run `GRSTAT-C04-CERT-20260930-1530KST`는 원 version 3 계약 SHA-256 `0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63`를 그대로 사용했습니다. 게시 HEAD `08429842`와 tree `6b4d30e0`을 확인했고, 인계 manifest 65/65 및 기존 소스·raw 인덱스의 해시를 확인했습니다.

새 SymPy와 Sage/Singular 자체검사는 각각 종료 0, 변조 거절 PASS입니다. 네 축을 새로 실행한 runner의 원시 aggregate는 `CAS_4AXIS_PASS`입니다. 범위는 실수 `0<L<=U`, 모든 `x∈[L,U]`, 모든 실수 경쟁자, 양 끝점 및 `L=U`인 C04 원자 성분입니다. Lean은 `formal_mathlib`에서 저장소 고정 `leanprover/lean4:v4.31.0`을 사용했습니다.

독립 reviewer의 지원된 등록은 성공했으나 child dispatch가 PreToolUse `ROUTING_REGISTRATION_REQUIRED`로 거절됐습니다. 등록 launch는 미청구이며 검토 완료가 아닙니다. 원 run의 `CAS_CONFLICT`, 실패·timeout 로그는 보존했습니다. 상위 CAS-13의 C01-C03, 관측 구간 포함·단위/프레임·수치오차, 과학적 HOLD는 열려 있습니다. catalogue fit은 수행하지 않았습니다. 상세 argv·cwd·버전·해시·raw는 `RETURN.json`과 `RAW_EVIDENCE_MANIFEST.json`에 있습니다.
