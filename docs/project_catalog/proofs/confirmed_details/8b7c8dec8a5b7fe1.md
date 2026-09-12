# 기존 증명 근거의 버전별 상세

[확인 목록으로 돌아가기](../confirmed.md)

고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.

<a id="d7ad19880098135f5b164157ec3b65f1"></a>
### Pr170BuchertTwoPatch.barrowBuchertSeparation — d7ad19880098135f5b164157ec3b65f1

```lean
theorem barrowBuchertSeparation (variance meanSq meanMagnitude : ℚ) :
    qBT variance meanSq meanMagnitude =
      ((2 / 3) * variance - 2 * meanSq) + 2 * meanMagnitude ^ 2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 70-75; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="cfaf066d0c39735c3e5a6fa5b9939267"></a>
### Pr170BuchertTwoPatch.cancellationCondition — cfaf066d0c39735c3e5a6fa5b9939267

```lean
theorem cancellationCondition (variance shear : ℚ) (h : variance = 3 * shear) :
    (2 / 3) * variance - 2 * shear = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 52-56; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="096a6dcef0eaeb95e7fe6dba691227e7"></a>
### Pr170BuchertTwoPatch.constantExpansionBridge — 096a6dcef0eaeb95e7fe6dba691227e7

```lean
theorem constantExpansionBridge (w h s1 s2 : ℚ) (h0 : h ≠ 0) :
    omegaQ w h h s1 s2 = sigma2Rms w h h s1 s2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 42-51; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="6f92f365ef1c7b9109ffd93e92212739"></a>
### Pr170BuchertTwoPatch.generalBridgeResidual — 6f92f365ef1c7b9109ffd93e92212739

```lean
theorem generalBridgeResidual (w h1 h2 s1 s2 : ℚ)
    (h : hD w h1 h2 ≠ 0) :
    omegaQ w h1 h2 s1 s2 - sigma2Rms w h1 h2 s1 s2 =
      -varTheta w h1 h2 / (9 * (hD w h1 h2) ^ 2)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 34-41; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="214ba9ef2f20d004ee5bd12f089bf03b"></a>
### Pr170BuchertTwoPatch.patchExchangeHD — 214ba9ef2f20d004ee5bd12f089bf03b

```lean
theorem patchExchangeHD (w h1 h2 : ℚ) :
    hD w h1 h2 = hD (1 - w) h2 h1
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 57-61; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="ed0c9edbaa8524d6262e8f43959fcd15"></a>
### Pr170BuchertTwoPatch.patchExchangeVariance — ed0c9edbaa8524d6262e8f43959fcd15

```lean
theorem patchExchangeVariance (w h1 h2 : ℚ) :
    varTheta w h1 h2 = varTheta (1 - w) h2 h1
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 62-66; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="8e4d8f2a2d7a49670fd78aba11122c9c"></a>
### Pr170BuchertTwoPatch.qBReduction — 8e4d8f2a2d7a49670fd78aba11122c9c

```lean
theorem qBReduction (w h1 h2 s1 s2 : ℚ) :
    qB w h1 h2 s1 s2 =
      6 * w * (1 - w) * (h1 - h2) ^ 2 - 2 * meanSigmaSq w s1 s2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 28-33; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

<a id="81f4d04dd32b7831272672a11c46136a"></a>
### Pr170BuchertTwoPatch.registeredTypeCount — 81f4d04dd32b7831272672a11c46136a

```lean
theorem registeredTypeCount : Fintype.card BianchiType = 11
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace Pr170BuchertTwoPatch'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` — lines 80-81; 파일 ID `98e3c69335e4e01e650144cfb94b5547`; 소스 SHA-256 `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.
- `docs/generated/pr170_cas/axis_result_lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `041388750ed47ef5214d6d2ab60bda21`; 소스 SHA-256 `24af33f6690ef36889f980d915990b536bc85f246f05eaa6cf7e265aefdcc496`; 관찰 커밋 `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`.

