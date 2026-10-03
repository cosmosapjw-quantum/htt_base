# GR-CAS-01 유한 성분 실행 후속 검증

owner: research_program; claim_tier: non_claim_bearing; transfer_source: none.
원 task `GRSTAT-CAS-20260930-1308KST-CAS-01`, 원 v2 계약 SHA-256 `edc2df3348528a699b987ae1893ab76630e96b9915d11117db7916d005c406f1`을 유지했다.

현재 HEAD `bfdb1ef6f9767c06e4fb610fd572a41990e2a26f`에서 실제 `run-adjudicate`가 Wolfram+xAct → SymPy → Sage+Singular → Lean 순서로 실행되어 `CAS_4AXIS_PASS`를 반환했다. 원 독립 작성 소스의 Host 재실행이다. 새로운 네 독립 작성자를 실행했다는 뜻이 아니다. Wolfram 출력 경로와 두 wrapper의 실행 HEAD, Lean 실행 출처만 새 경로에서 명시적으로 변경했다. 원 수식과 Lean theorem 소스, 기존 CAS_CONFLICT와 raw는 보존했다.

각 축의 `raw.stdout`, `raw.stderr`, `EXECUTION.json`은 전체 실행 출력과 argv/cwd/exit/hash를 보존한다. Wolfram 내부 엔진 로그와 xTensor 버전, Sage/Singular 인증서, Lean 전체 compile 및 `#print axioms`도 새 경로에 있다. `ADJUDICATION.json`과 `PRESERVATION.json`이 실제 결과와 원본 보존을 기록한다.

수용 가능한 범위는 CAS-01-C01–C04의 유한 행렬·null cone·가속도 convention·원점 1-jet 성분이다. Jacobi ODE의 vertex Taylor/screen 불변성, smooth timelike 근방·국소 flow·source extension은 이 계약의 전체 해석 증명으로 닫히지 않았다. 고정 Einstein-matter 실현, 물리·관측 적용과 과학적 admission은 HOLD다. 과거 Lean launch의 미종결 lifecycle도 새 compiler PASS로 대체하지 않는다.

C01 원 v3·task와 실패 raw, C02/C03의 기존 수용, C04 launch, R9 및 사용자 변경을 보존했다. 575개 baseline hash가 모두 일치했다. 독립 심사와 게시 상태는 RETURN.json 및 최종 전달문에서 분리한다.

독립 reviewer의 실제 관측 runtime은 gpt-6-astra/xhigh이며 유한 실행 후속 게시 범위 verdict는 PASS다. SymPy 실행 interpreter와 runner preflight가 달랐던 증거 공백은 exact `/usr/bin/python3` 별도 probe로 보완했다. 이 probe는 사후 별도 process 관측이라는 한계를 명시한다.
