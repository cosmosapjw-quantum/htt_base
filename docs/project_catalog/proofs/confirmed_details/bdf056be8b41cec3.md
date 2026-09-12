# 기존 증명 근거의 버전별 상세

[확인 목록으로 돌아가기](../confirmed.md)

고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.

<a id="b16ab8ee5aaf02a0bba028e79f1fa516"></a>
### R7.L10_accepted_minors_and_minimal_cutoff — b16ab8ee5aaf02a0bba028e79f1fa516

```lean
theorem L10_accepted_minors_and_minimal_cutoff
    (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ)
    (haccepted : ∀ m, (Matrix.det ((B m).submatrix id (pivot m)))^2 = acceptedSquaredMinor m) :
    storedRank B = 32 ∧
    (∀ L : ℕ, L < 10 → ∀ B0 : Matrix (Fin 4) (Fin (L-6)) ℝ, B0.rank < 4) ∧
    (∀ m (j : Fin (rows m)), 7 + (pivot m j).val ≤ 10)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 162-169; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="7bbcfa4486778e33364c4f6cee841185"></a>
### R7.T1_no_proper_signed_stabilizer — 7bbcfa4486778e33364c4f6cee841185

```lean
theorem T1_no_proper_signed_stabilizer (s : Fin 3 → ℝ)
    (hs : ∀ i, s i ^ 2 = 1) (hproper : s 0 * s 1 * s 2 = 1)
    (hmap : ∀ i, s i ^ 3 * O i i i = -O i i i) : False
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 44-57; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="4ca597abba58a009d77bf6256cc6453e"></a>
### R7.T1_symmetry — 4ca597abba58a009d77bf6256cc6453e

```lean
theorem T1_symmetry : (∀ i j k, O i j k = O j i k) ∧
    (∀ i j k, O i j k = O i k j)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 21-24; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="b649b9c1a90cd7a5551d6933360bf00c"></a>
### R7.T1_trace_and_contraction — b649b9c1a90cd7a5551d6933360bf00c

```lean
theorem T1_trace_and_contraction :
    Matrix.trace Q = 0 ∧ (∀ i, ∑ j, O i j j = 0) ∧
    (∀ i, ∑ j, ∑ k, O i j k * Q j k = v i) ∧
    Matrix.det (![v, Q.mulVec v, Q.mulVec (Q.mulVec v)] : Matrix (Fin 3) (Fin 3) ℝ) = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 25-43; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="851e9befd0f4a8280345bc83c47027c8"></a>
### R7.T3_normalized_derivative — 851e9befd0f4a8280345bc83c47027c8

```lean
theorem T3_normalized_derivative (q temp : ℝ → ℝ) (qdot tempdot x : ℝ)
    (hq : HasDerivAt q qdot x) (ht : HasDerivAt temp tempdot x) (hp : 0 < temp x) :
    HasDerivAt (fun y => q y / temp y)
      ((qdot * temp x - q x * tempdot) / temp x ^ 2) x
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 58-63; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="08426858e49bde1c684d7760a1af754a"></a>
### R7.T3_normalized_derivative_and_odd_signs — 08426858e49bde1c684d7760a1af754a

```lean
theorem T3_normalized_derivative_and_odd_signs (Theta qdot Dd divo Cdot Cout E : ℝ)
    (hTheta : 0 < Theta) :
    -qdot - (-Dd) - (3/7 : ℝ) * (-divo) = -qdot + Dd + (3/7 : ℝ)*divo ∧
    -(3/Theta)*(-Cdot) - (-Cout) - (6/(5*Theta))*E =
      3*Cdot/Theta + Cout - 6*E/(5*Theta)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 64-73; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="27b010ebc0e7d77381e11b6fbd9fc699"></a>
### R7.T5_first_order_inverse_coefficient — 27b010ebc0e7d77381e11b6fbd9fc699

```lean
theorem T5_first_order_inverse_coefficient {n p q : Type*}
    [Fintype n] [DecidableEq n] (E : Matrix n n ℝ)
    (C : Matrix p n ℝ) (A : Matrix n q ℝ) :
    ((1 : Matrix n n ℝ) * E + (-E) * 1 = 0) ∧
    ((0 : Matrix p n ℝ) * E + (-C) * (1 : Matrix n n ℝ)) * A = -(C * A)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 83-90; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="5762bdace7fab790e6f0f5c878b236ed"></a>
### R7.T5_inverse_coefficients — 5762bdace7fab790e6f0f5c878b236ed

```lean
theorem T5_inverse_coefficients {n : Type*} [Fintype n] [DecidableEq n]
    (E B0 B1 : Matrix n n ℝ) (h0 : (1 : Matrix n n ℝ) * B0 = 1)
    (h1 : (1 : Matrix n n ℝ) * B1 + (-E) * B0 = 0) :
    B0 = 1 ∧ B1 = E
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 74-82; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="3df8e47a1bc62eedbe1681f006b0aacc"></a>
### R7.T5_scalar_cost_implication — 3df8e47a1bc62eedbe1681f006b0aacc

```lean
theorem T5_scalar_cost_implication (f c d k h : ℝ)
    (hf : 0 < f) (hsmall : f < 1/36) (hc : 0 < c) (hd : 0 < d)
    (hk : 0 ≤ k) (hh : 0 ≤ h)
    (hbound : k ≤ c*f/(1-36*f)) (hcancel : d ≤ k*h) :
    d^2 * (1-36*f)^2 / (c^2*f^2) ≤ h^2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 91-107; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="8a5b2695b0c39cf5713e9cc871143343"></a>
### R7.T6_scalar_information_one_fifth — 8a5b2695b0c39cf5713e9cc871143343

```lean
theorem T6_scalar_information_one_fifth :
    (1 : ℝ) * (1/1 - 1/(1+(1/4))) * 1 = 1/5 ∧
    ((1 : ℝ) - 1/(1+1/4)) - (1 - 1/1) = 1/5
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 108-111; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="4194c419487498e2dbbe9ca9cbd4ea8f"></a>
### R7.accepted_block_full_row_rank — 4194c419487498e2dbbe9ca9cbd4ea8f

```lean
theorem accepted_block_full_row_rank (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ)
    (haccepted : ∀ m, (Matrix.det ((B m).submatrix id (pivot m)))^2 = acceptedSquaredMinor m) :
    ∀ m, (B m).rank = rows m
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 128-145; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="b7fdafa25e62b69e5c808c8007f8acfb"></a>
### R7.accepted_columns_within_ten — b7fdafa25e62b69e5c808c8007f8acfb

```lean
theorem accepted_columns_within_ten (m : Fin 6) (j : Fin (rows m)) :
    7 + (pivot m j).val ≤ 10
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 119-121; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="87a913cc562fbaf708cc5b1e97f3c18e"></a>
### R7.accepted_rational_positivity — 87a913cc562fbaf708cc5b1e97f3c18e

```lean
theorem accepted_rational_positivity :
    (∀ m, 0 < acceptedSquaredMinor m) ∧ (∀ m, 0 < acceptedNormalDet m)
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 122-127; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="77a0f6f8b6e76668ddec5a4a496c47d7"></a>
### R7.cutoff_below_ten_not_full — 77a0f6f8b6e76668ddec5a4a496c47d7

```lean
theorem cutoff_below_ten_not_full (L : ℕ) (hL : L < 10)
    (B0 : Matrix (Fin 4) (Fin (L-6)) ℝ) : B0.rank < 4
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 157-161; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="fb25c708db52a466471352c5c56f34b4"></a>
### R7.cutoff_ten_stored_rank — fb25c708db52a466471352c5c56f34b4

```lean
theorem cutoff_ten_stored_rank (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ)
    (haccepted : ∀ m, (Matrix.det ((B m).submatrix id (pivot m)))^2 = acceptedSquaredMinor m) :
    storedRank B = 32
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 149-156; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

<a id="dba2e32fd5543cd1698279ab8f2a9899"></a>
### R7.rows_le_four — dba2e32fd5543cd1698279ab8f2a9899

```lean
theorem rows_le_four (m : Fin 6) : rows m ≤ 4
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: recorded_Lean_compilation.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib.Analysis.Calculus.Deriv.Inv\nimport Mathlib.LinearAlgebra.Matrix.Rank\nimport Mathlib.LinearAlgebra.Matrix.Determinant.Basic\nimport Mathlib.Tactic\nset_option maxRecDepth 4096\nset_option maxHeartbeats 2000000\nopen scoped BigOperators Matrix\nnoncomputable section\nnamespace R7'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '파일에 정의된 타입·모형·fixture와 개별 선언 범위만 해당한다. 상위 물리·통계·CAS 계약 전체의 승인 상태를 바꾸지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `TENSOR-JOINT-R7-20260908/worktree/.agent-harness/runs/TENSOR-JOINT-R7-20260908/axes/lean/Proof.lean` — lines 116-116; 파일 ID `7472b7a8d20afade6df44a000bab530b`; 소스 SHA-256 `bdf056be8b41cec39401309ab1f2748efa709fd8deb9311301ce4874702aab3a`; 관찰 커밋 `해당 없음`.
- `docs/generated/tensor_joint_r7/cas/axes/lean/build_receipt.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `fe7eeb066e0716775319eae25f25158d`; 소스 SHA-256 `a62042033763884c46f367d3d5127fe8b7dd2afcb04afc3e244540e5dacf13d1`; 관찰 커밋 `017870ca9cc8694728de2fa6270c1da52c382ffd`.

