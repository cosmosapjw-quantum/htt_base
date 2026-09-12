# 기존 증명 근거의 버전별 상세

[확인 목록으로 돌아가기](../confirmed.md)

고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.

<a id="82f85631e217d5d189a4f16ac454330c"></a>
### PR190NormalVorticity.axisProofBundle — 82f85631e217d5d189a4f16ac454330c

```lean
theorem axisProofBundle : AxisProofBundle
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 74-85; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="ed59b76b2ceaf640254bcf625ea5f220"></a>
### PR190NormalVorticity.interiorEndpointSameFrameContradiction — ed59b76b2ceaf640254bcf625ea5f220

```lean
theorem interiorEndpointSameFrameContradiction :
    normalW2 ≠ registeredInteriorW2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 52-56; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="41a52cde8e7744d49ce59bfcaead58f5"></a>
### PR190NormalVorticity.lowerEndpointSameFrameContradiction — 41a52cde8e7744d49ce59bfcaead58f5

```lean
theorem lowerEndpointSameFrameContradiction :
    normalW2 ≠ registeredLowerW2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 44-48; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="55707911513114067581c35ddfefc971"></a>
### PR190NormalVorticity.normalOmegaSquaredZero — 55707911513114067581c35ddfefc971

```lean
theorem normalOmegaSquaredZero : normalOmegaSquared = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 35-37; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="935f224700af549477058c5c7a7024cc"></a>
### PR190NormalVorticity.normalSpatialVorticityZero — 935f224700af549477058c5c7a7024cc

```lean
theorem normalSpatialVorticityZero (i j : Fin 3) :
    vorticityTwoForm i j = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 31-34; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="32c116158396a718721f78d510968654"></a>
### PR190NormalVorticity.normalW2Zero — 32c116158396a718721f78d510968654

```lean
theorem normalW2Zero : normalW2 = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 38-40; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="618039ba02758f75d5d8e1c14a67e232"></a>
### PR190NormalVorticity.refutedConstraintCannotPromote — 618039ba02758f75d5d8e1c14a67e232

```lean
theorem refutedConstraintCannotPromote
    (constraint localClaim globalClaim : Prop)
    (hConstraint : ¬ constraint) :
    ¬ (constraint ∧ localClaim ∧ globalClaim)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 57-63; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="cf5e0540e3ba68dd0bce6efeccbc0d0a"></a>
### PR190NormalVorticity.registeredInteriorW2Positive — cf5e0540e3ba68dd0bce6efeccbc0d0a

```lean
theorem registeredInteriorW2Positive : 0 < registeredInteriorW2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 49-51; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

<a id="dafb7e1931399b7d4ec40da14a1d588f"></a>
### PR190NormalVorticity.registeredLowerW2Positive — dafb7e1931399b7d4ec40da14a1d588f

```lean
theorem registeredLowerW2Positive : 0 < registeredLowerW2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace PR190NormalVorticity'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` — lines 41-43; 파일 ID `9daa9e445bda2d365acf19abf6c5a189`; 소스 SHA-256 `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2`; 관찰 커밋 `bae6ac2df15c95ee1e71a3e49b859c0added192d`.
- `.agent-harness/runs/pr190-typed-attainability-20260802/results/A-PR190-CAS-LEAN.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `0703f872d00ca2578d7a52da192b8b3f`; 소스 SHA-256 `53556a387e33254226ec9f3e0c01e14921447b3c11d8f35ef7d13ce3932ccc30`; 관찰 커밋 `해당 없음`.

