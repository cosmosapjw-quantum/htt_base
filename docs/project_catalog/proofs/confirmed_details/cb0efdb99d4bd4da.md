# 기존 증명 근거의 버전별 상세

[확인 목록으로 돌아가기](../confirmed.md)

고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.

<a id="a93924ca54d7e428b22d71beab12ab3b"></a>
### Pr171TiltRelaxation.counterexampleEnergyConditions — a93924ca54d7e428b22d71beab12ab3b

```lean
theorem counterexampleEnergyConditions :
    (-1 : ℚ) ≤ 1/4 ∧ (1/4 : ℚ) ≤ 1 ∧ (0 : ℚ) ≤ 1/4
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 45-48; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="b028edffcf16d5b53a8c6cc291fa6c9b"></a>
### Pr171TiltRelaxation.counterexampleMap — b028edffcf16d5b53a8c6cc291fa6c9b

```lean
theorem counterexampleMap :
    (5/4 : ℚ) = 1 + 1/4 ∧ (1/4 : ℚ) < 1/3 ∧ (0 : ℚ) ≥ 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 41-44; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="a2b970904d15b1fc0750ba440a4ca863"></a>
### Pr171TiltRelaxation.dragCharacteristicIdentity — a2b970904d15b1fc0750ba440a4ca863

```lean
theorem dragCharacteristicIdentity (a x y r : ℚ) :
    dragChar a x y r = r^2 + (a+x+y+1)*r + a*(1+y)+x
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 20-24; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="353b6e18494af801a88fe229f5a2786c"></a>
### Pr171TiltRelaxation.dragHurwitz — 353b6e18494af801a88fe229f5a2786c

```lean
theorem dragHurwitz (a x y : ℚ) (ha : 0 < a) (hx : 0 ≤ x) (hy : 0 ≤ y) :
    0 < a+x+y+1 ∧ 0 < dragDet a x y
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 25-31; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="9060f9e61d072058cf37528eac759883"></a>
### Pr171TiltRelaxation.persistentFixture — 9060f9e61d072058cf37528eac759883

```lean
theorem persistentFixture :
    ((-1 : ℚ) * 1 + 1 * 1 = 0) ∧ (1 * 1 + (-1) * 1 = 0)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 37-40; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="b3a1619d6c78189cc8dd385be7fd3c7f"></a>
### Pr171TiltRelaxation.radiationBoundary — b3a1619d6c78189cc8dd385be7fd3c7f

```lean
theorem radiationBoundary (v : ℚ) :
    (1-v^2) * (3*(1/3 : ℚ)-1) * v = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 17-19; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="aaad94c8a0cbebbc8bb8e24f9608fa97"></a>
### Pr171TiltRelaxation.rwInvariantCleared — aaad94c8a0cbebbc8bb8e24f9608fa97

```lean
theorem rwInvariantCleared (v w : ℚ) :
    (3*w-1) * ((1-v^2) + (1-w)*v^2) = (3*w-1)*(1-w*v^2)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 11-14; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="3146a900c22fe4f74584bbff64c447c1"></a>
### Pr171TiltRelaxation.rwLinearization — 3146a900c22fe4f74584bbff64c447c1

```lean
theorem rwLinearization (w : ℚ) : (1 : ℚ) * (3*w-1) = 3*w-1
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 15-16; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

<a id="558137ac617f63042b82c3ac8a83a27a"></a>
### Pr171TiltRelaxation.stableFixture — 558137ac617f63042b82c3ac8a83a27a

```lean
theorem stableFixture :
    dragTrace (1/4) (1/2) (1/3) = (-25/12 : ℚ) ∧
    dragDet (1/4) (1/2) (1/3) = (5/6 : ℚ)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr171TiltRelaxation'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` — lines 32-36; 파일 ID `fca4799d957c0caac5f76498bd217820`; 소스 SHA-256 `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.
- `docs/generated/pr171_cas/generation_3/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `d75afc4bcdb7c61f0aad6778d21587d1`; 소스 SHA-256 `c3ca6ef9bb5ca832344d48a976dedf8f4bcb74e903e15e18d70c4550d7ec9da8`; 관찰 커밋 `b8a857742bd6c2d727ea2009f6e8a341a031b120`.

