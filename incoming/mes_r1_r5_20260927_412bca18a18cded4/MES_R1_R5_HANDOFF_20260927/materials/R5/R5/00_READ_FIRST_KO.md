# MES R5 재현 패킷

먼저 MES_R5_REPORT_KO.md를 읽고 INDEPENDENT_REVIEW.md의 claim ceiling을 확인한다.

이번 산출물은 exact homogeneous finite-tilt 기하 연산자와 R3 retained radiation time-jet 식별성이다. 실제 우주의 MES percentage나 관측 posterior는 계산하지 않았다.

## 핵심 파일

- MES_R5_REPORT_KO.md: 통합 최종 보고서.
- KINEMATIC_OPERATOR_DERIVATION.md: 12×9 affine map, 역산, 와도 관계, 자유 time jet 정리.
- verification/CAS_KINEMATIC_AFFINE.wl 및 RAW_V1.json: 실제 Wolfram 기하 검산.
- verification/CAS_RADIATION_AND_JOINT_DISK.wl 및 RAW.json: radiation Schur 및 correlated disk 검산.
- INDEPENDENT_REVIEW.md: 후보 생성과 분리된 판정.
- PREREGISTRATION.json와 REGISTRATION_CHRONOLOGY.json: 원 등록 및 선행 CAS 예외. 원 등록만 보고 전체 CAS가 사전등록됐다고 해석하지 않는다.
- REPORT_CANDIDATE_V1_FROZEN.md: 검토에 넘긴 원고.
- REVISION_LOG.md, state/: 수정·근거·재개 상태.
- inputs/: 실제 사용한 R3–R4 기준 자료.
- sources/LITERATURE_AND_REGIME_AUDIT.md: 원전 감사 및 미채택 탐색 부록.

## 재현 방법과 경계

두 .wl 파일의 전체 내용을 Wolfram Language evaluator에서 각각 실행한다. 이 패킷은 local Wolfram 실행 파일의 존재를 전제하거나 설치하지 않는다. 코드는 유한 기호식·행렬·적분 검산이며 ODE/PDE/Boltzmann solver가 아니다. General rank proof는 보고서의 inverse 및 Schur proof에 있고 finite fixtures는 이를 보조한다.

Wolfram의 Out 번호나 출력 문자열의 표시 형식은 세션마다 달라질 수 있다. 의미상 항등식, rank, 유리수, 0 residual을 비교한다. 실제 raw 결과는 도구가 반환한 JSON 그대로 보존했다. Radiation/disk는 동일 code를 raw 보존을 위해 한 번 재호출했으며 독립 replication으로 세지 않는다.

원문 PDF·전체 추출 텍스트·페이지 렌더는 검토용 scratch에만 남겼다. 이 배포 ZIP에는 원전 URL·version·hash와 감사노트만 포함한다. source note의 새 exact quadrupole/Thomson 유도는 R5 채택 결과가 아니다.

MANIFEST.sha256은 최종 패킷의 상대경로별 SHA-256이다. Manifest 자체는 자기 해시 목록에서 제외한다. 패킷 byte integrity와 과학적 타당성은 별개다.
