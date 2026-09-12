# 기존 증명 근거의 버전별 상세

[확인 목록으로 돌아가기](../confirmed.md)

고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.

<a id="1b3b301540b55bd660d70928f174c24d"></a>
### R8O4.null_cone — 1b3b301540b55bd660d70928f174c24d

```lean
theorem null_cone (z : ℂ) : dot (nullVector z) (nullVector z) = 0
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 119-120; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="5a7c8d3cc151ccd4c16dd40b2e7a4b10"></a>
### R8O4.o_cast — 5a7c8d3cc151ccd4c16dd40b2e7a4b10

```lean
theorem o_cast (A : ℝ) (u v w : V ℝ) (i j k : Fin 3) :
     ((O A u v w i j k : ℝ) : ℂ) = O (A : ℂ) (complexify u) (complexify v) (complexify w) i j k
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 136-139; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="fd37779f7c2090326b37a8f687e81efb"></a>
### R8O4.o_contraction — fd37779f7c2090326b37a8f687e81efb

```lean
theorem o_contraction (A : K) (u v w n : V K) :
     contract3 (O A u v w) n =
     A*(dot u n*dot v n*dot w n-3*dot (b u v w) n*dot n n/5)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 112-117; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="f9625d64230219087e3fabdc2356d94b"></a>
### R8O4.o_index_perm — f9625d64230219087e3fabdc2356d94b

```lean
theorem o_index_perm (A : K) (u v w : V K) (idx : Fin 3 → Fin 3)
     (p : Equiv.Perm (Fin 3)) :
     O A u v w (idx (p 0)) (idx (p 1)) (idx (p 2)) =
     O A u v w (idx 0) (idx 1) (idx 2)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 98-107; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="86ad74c00ecdd525705c9a9acf366889"></a>
### R8O4.o_null — 86ad74c00ecdd525705c9a9acf366889

```lean
theorem o_null (A : ℂ) (u v w : V ℂ) (z : ℂ) :
     contract3 (O A u v w) (nullVector z) =
     A*dot u (nullVector z)*dot v (nullVector z)*dot w (nullVector z)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 125-130; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="630f539bf7eda305c30ef055d4158541"></a>
### R8O4.o_real_null — 630f539bf7eda305c30ef055d4158541

```lean
theorem o_real_null (A : ℝ) (u v w : V ℝ) (z : ℂ) :
     contract3 (fun i j k => ((O A u v w i j k : ℝ) : ℂ)) (nullVector z) =
     (A : ℂ)*dot (complexify u) (nullVector z)*dot (complexify v) (nullVector z)*
     dot (complexify w) (nullVector z)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 145-151; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="761b900f72fe02ed1ab906476d8f217a"></a>
### R8O4.o_sign — 761b900f72fe02ed1ab906476d8f217a

```lean
theorem o_sign (A : K) (u v w : V K) : O (-A) (-u) v w = O A u v w
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 67-70; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="d5eab382fd32557f80676d42116dab55"></a>
### R8O4.o_swap12 — d5eab382fd32557f80676d42116dab55

```lean
theorem o_swap12 (A : K) (u v w : V K) : O A u v w = O A v u w
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 44-47; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="53ce5765cf13ca6f494e529820b1b552"></a>
### R8O4.o_swap23 — 53ce5765cf13ca6f494e529820b1b552

```lean
theorem o_swap23 (A : K) (u v w : V K) : O A u v w = O A u w v
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 48-51; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="9bb56360143c4fe8e9ff7a8855d140bd"></a>
### R8O4.o_sym12 — 9bb56360143c4fe8e9ff7a8855d140bd

```lean
theorem o_sym12 (A : K) (u v w : V K) (i j k : Fin 3) :
     O A u v w i j k = O A u v w j i k
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 52-57; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="034d2a29261d752fb30fa556e3906d26"></a>
### R8O4.o_sym23 — 034d2a29261d752fb30fa556e3906d26

```lean
theorem o_sym23 (A : K) (u v w : V K) (i j k : Fin 3) :
     O A u v w i j k = O A u v w i k j
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 58-63; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="e316a97b2c22ba8bb2003ea2d21cb8a0"></a>
### R8O4.o_trace — e316a97b2c22ba8bb2003ea2d21cb8a0

```lean
theorem o_trace (A : K) (u v w : V K) (k : Fin 3) :
     (∑ i, O A u v w i i k) = 0
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 64-66; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="1e115c440738081c628760c45d9256c5"></a>
### R8O4.o_vector_perm — 1e115c440738081c628760c45d9256c5

```lean
theorem o_vector_perm (A : K) (v : Fin 3 → V K) (p : Equiv.Perm (Fin 3)) :
     O A (v (p 0)) (v (p 1)) (v (p 2)) = O A (v 0) (v 1) (v 2)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 92-97; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="83ffb622a95bd634e7a0a38118fbcce2"></a>
### R8O4.o_zero — 83ffb622a95bd634e7a0a38118fbcce2

```lean
theorem o_zero (u v w : V K) : O 0 u v w = 0
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 71-77; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="88b23d3a661895d21a27ca1d89574a44"></a>
### R8O4.perm_cases — 88b23d3a661895d21a27ca1d89574a44

```lean
theorem perm_cases (p : Equiv.Perm (Fin 3)) :
     (p 0 = 0 ∧ p 1 = 1 ∧ p 2 = 2) ∨
     (p 0 = 0 ∧ p 1 = 2 ∧ p 2 = 1) ∨
     (p 0 = 1 ∧ p 1 = 0 ∧ p 2 = 2) ∨
     (p 0 = 1 ∧ p 1 = 2 ∧ p 2 = 0) ∨
     (p 0 = 2 ∧ p 1 = 0 ∧ p 2 = 1) ∨
     (p 0 = 2 ∧ p 1 = 1 ∧ p 2 = 0)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 78-91; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="4c7d6898fa7e7fe7f7335123fc127947"></a>
### R8O4.q_cast — 4c7d6898fa7e7fe7f7335123fc127947

```lean
theorem q_cast (A : ℝ) (u v : V ℝ) (i j : Fin 3) :
     ((Q A u v i j : ℝ) : ℂ) = Q (A : ℂ) (complexify u) (complexify v) i j
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 132-135; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="748d31f7222d005dab1625d3251c93ca"></a>
### R8O4.q_contraction — 748d31f7222d005dab1625d3251c93ca

```lean
theorem q_contraction (A : K) (u v n : V K) :
     contract2 (Q A u v) n = A*(dot u n*dot v n-dot u v*dot n n/3)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 108-111; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="d3531b8efed0feeabb889cd93db48a6c"></a>
### R8O4.q_null — d3531b8efed0feeabb889cd93db48a6c

```lean
theorem q_null (A : ℂ) (u v : V ℂ) (z : ℂ) :
     contract2 (Q A u v) (nullVector z) = A*dot u (nullVector z)*dot v (nullVector z)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 121-124; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="f3691f3bb0a22b27e46810a03a5432d5"></a>
### R8O4.q_real_null — f3691f3bb0a22b27e46810a03a5432d5

```lean
theorem q_real_null (A : ℝ) (u v : V ℝ) (z : ℂ) :
     contract2 (fun i j => ((Q A u v i j : ℝ) : ℂ)) (nullVector z) =
     (A : ℂ)*dot (complexify u) (nullVector z)*dot (complexify v) (nullVector z)
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 140-144; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="53fbc3f28e5fa8caef45ca82c1d7c274"></a>
### R8O4.q_sign — 53fbc3f28e5fa8caef45ca82c1d7c274

```lean
theorem q_sign (A : K) (u v : V K) : Q (-A) (-u) v = Q A u v
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 37-40; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="79fedf594c95af82cbe3ca315dfa3a56"></a>
### R8O4.q_swap — 79fedf594c95af82cbe3ca315dfa3a56

```lean
theorem q_swap (A : K) (u v : V K) : Q A u v = Q A v u
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 33-36; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="62cc992aa76e4b599092a993480ec1eb"></a>
### R8O4.q_sym — 62cc992aa76e4b599092a993480ec1eb

```lean
theorem q_sym (A : K) (u v : V K) (i j : Fin 3) : Q A u v i j = Q A u v j i
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 27-29; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="95e74e942de049939a40eee648556037"></a>
### R8O4.q_trace — 95e74e942de049939a40eee648556037

```lean
theorem q_trace (A : K) (u v : V K) : (∑ i, Q A u v i i) = 0
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 30-32; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

<a id="e083b595a5af3aa82d65c3963cc51d76"></a>
### R8O4.q_zero — e083b595a5af3aa82d65c3963cc51d76

```lean
theorem q_zero (u v : V K) : Q 0 u v = 0
```

- 소속: common; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nnamespace R8O4\nnoncomputable section\nvariable {K : Type*} \[Field K\] \[CharZero K\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', 'O4 STF2/STF3 trace/sign/permutation과 복소 bilinear null cone 항등식만 해당한다. transfer·관측·family 식별의 증명이 아니다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` — lines 41-43; 파일 ID `a4ce0e38bc2df93c010f7dd93e63f060`; 소스 SHA-256 `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.
- `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/lean_direct_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `7bfc82711437444d92c96100538eb2ac`; 소스 SHA-256 `a0017acbd90e98fbecac1983af6aef417d5f3f132ddc35a9a85fde40fedec1aa`; 관찰 커밋 `ea0305fa9e5f23e4d22a40ab826155202e76b574`.

