# 로컬 CAS 정정 인계 — GRSTAT-CAS-CORR-20260930-1420KST

원 run `GRSTAT-CAS-20260930-1308KST`의 manifest `cf902736a422ca81673f02be74f9d537d9ab5150f4f0ede3fb613741be73280b`와 466개 기록 파일, 검토 ZIP의 11개 멤버 해시를 확인했다. HEAD는 지정 출판 커밋과 같다. 원 version 1/2 계약, 원시 verdict·실패 로그는 변경하지 않았다.

새 version 3 성분 계약과 해시는 `RETURN.json`의 `new_contracts`에 있다. CAS-03에서는 `det(D)≠0`의 정확한 선형 solve에 `H_D=0`을 허용하고, 절단식만 `H_D≠0`로 제한했다. spacelike `r_chi`, `B u=0`, timelike-dyad 실패 control을 새로 검사했다. C01의 일반 6성분 범위와 물리적 잔여항은 아직 닫히지 않았다.

CAS-13-C04의 새 runner 관측 aggregate는 `CAS_CONFLICT`이다: Wolfram·Lean PASS, SymPy·Sage 부분 인증으로 misaligned. 이는 `0<L≤U`, 전 구간, 양 끝, 모든 실수 경쟁자와 `L=U`를 목표로 한 원자 성분에 한정된다. Lean 소스는 보존 증명을 새 경로에서 다시 실행했으며 새 독립 저자 증명으로 표기하지 않는다.

CAS-11 Wolfram의 `aa=Array[aa,3]` 재귀를 clean kernel에서 재현했다. 분리 symbol control은 정상이고, 새 wrapper는 marker 부재·engine 오류에 과학 check=false JSON을 만들지 않고 비영 종료한다. 수정된 옛 고정 차원 검사는 진단일 뿐 임의 차원 C01/C02/C03 증명이 아니다.

세 순수 수학 인터페이스는 `PURE_MATH_INTERFACES.json`에 명세만 작성했다. CAS-08/09/15/16/17의 실제 누락 정의와 미증명 출력을 `NEXT_INPUT_AUDIT.json`에 분리했다. 독립 reviewer 완료, 전체 4축 통과, 원 계약 closure, 관측 catalogue fit, novelty·Bianchi 분류 승격은 없다. 과학 상태는 기존 conditional/HOLD다.

독립 검토 등록은 `NO_SUPPORTED_WORKER_WITHIN_DECLARED_COST_SCOPE`로 거절되어 완료 상태가 아니다. 봉인 환경의 최초 비고정 Lean 버전 probe는 timeout이었고, 실제 runner는 저장소 고정 toolchain의 preflight와 새 정리 실행을 성공적으로 관측했다. 두 기록은 `OBSERVED_RUNTIME.json`에 분리했다.
