# 기존 증명 근거의 버전별 상세

[확인 목록으로 돌아가기](../confirmed.md)

고정 입력 계산이나 조건부 보조정리를 더 넓은 연구 명제의 완료로 해석하지 않는다. 이번 작업에서 증명 도구를 재실행하지 않았다.

<a id="2bfd5029ce7f429e998a5e5f1d6a8c67"></a>
### PR328LocalGlobal.nuisanceProjector_annihilates — 2bfd5029ce7f429e998a5e5f1d6a8c67

```lean
theorem nuisanceProjector_annihilates
    (U : Matrix m q ℝ) (hU : U.transpose * U = 1) :
    nuisanceProjector U * U = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 50-56; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="4e9e9143588e87d1dd922628d90d1e79"></a>
### PR328LocalGlobal.nuisanceProjector_idempotent — 4e9e9143588e87d1dd922628d90d1e79

```lean
theorem nuisanceProjector_idempotent
    (U : Matrix m q ℝ) (hU : U.transpose * U = 1) :
    nuisanceProjector U * nuisanceProjector U = nuisanceProjector U
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 36-49; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="3043baaf962d85993fde3b9ca5f26bee"></a>
### PR328LocalGlobal.nuisanceProjector_symmetric — 3043baaf962d85993fde3b9ca5f26bee

```lean
theorem nuisanceProjector_symmetric (U : Matrix m q ℝ) :
    (nuisanceProjector U).transpose = nuisanceProjector U
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 32-35; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="b06c2430a11ecb762f1038042562d19b"></a>
### PR328LocalGlobal.nuisance_basis_invariance — b06c2430a11ecb762f1038042562d19b

```lean
theorem nuisance_basis_invariance
    (M : Matrix m q ℝ) (Q : Matrix q q ℝ)
    (hQ : Function.Surjective Q.mulVec) :
    LinearMap.range (M * Q).mulVecLin = LinearMap.range M.mulVecLin
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 57-64; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="9689485601320b90969ba82bd2932694"></a>
### PR328LocalGlobal.whitening_identity — 9689485601320b90969ba82bd2932694

```lean
theorem whitening_identity
    (W C : Matrix m m ℝ)
    (h : W * C * W.transpose = 1) :
    W * C * W.transpose = 1
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 27-31; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="dc42643d37127b9b35e65c7d082abb03"></a>
### conditional_factorization_rank_bound — dc42643d37127b9b35e65c7d082abb03

```lean
theorem conditional_factorization_rank_bound
    (B : E →ₗ[K] F) (S : F →ₗ[K] G) :
    (S.comp B).rank ≤ min S.rank B.rank
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 118-122; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="5e9cb89714562af70d56ff76eb7f3fa4"></a>
### full_fixture_rank — 5e9cb89714562af70d56ff76eb7f3fa4

```lean
theorem full_fixture_rank : fullFixture.rank = 2
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 97-99; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="f1e153a55fd0d53c0c06727532b527bf"></a>
### gram_kernel_equivalence — f1e153a55fd0d53c0c06727532b527bf

```lean
theorem gram_kernel_equivalence (D : E →ₗ[ℝ] F) :
    (D.adjoint ∘ₗ D).ker = D.ker
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 77-80; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="bd5e7bceb2c11d28fd8b3b27f45d97fa"></a>
### gram_rank_equivalence — bd5e7bceb2c11d28fd8b3b27f45d97fa

```lean
theorem gram_rank_equivalence (D : E →ₗ[ℝ] F) :
    Module.finrank ℝ (D.adjoint ∘ₗ D).range =
      Module.finrank ℝ D.range
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 81-85; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="9df439aaec88da4946816d37fe10ddc1"></a>
### independent_operator_nonimplication — 9df439aaec88da4946816d37fe10ddc1

```lean
theorem independent_operator_nonimplication :
    Function.Injective
      (LinearMap.id : (Fin 2 → ℝ) →ₗ[ℝ] (Fin 2 → ℝ))
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 136-142; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="459ed5b59a6123b68add418046c4661b"></a>
### no_physical_response_derivation_claim — 459ed5b59a6123b68add418046c4661b

```lean
theorem no_physical_response_derivation_claim : True
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 143-145; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="b788567133e62076655cda2d1e2723f0"></a>
### partial_fixture_rank — b788567133e62076655cda2d1e2723f0

```lean
theorem partial_fixture_rank : partialFixture.rank = 1
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 100-103; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="daae272a9a0a90e1843927c1a34f8b81"></a>
### strict_factorization_bound_precludes_full_rank — daae272a9a0a90e1843927c1a34f8b81

```lean
theorem strict_factorization_bound_precludes_full_rank
    (B : E →ₗ[K] F) (S : F →ₗ[K] G)
    (hB : B.rank < Module.rank K E) :
    (S.comp B).rank < Module.rank K E
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 123-128; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

<a id="c03b428acdb6a208d0d19ff4fa3f8221"></a>
### zero_fixture_rank — c03b428acdb6a208d0d19ff4fa3f8221

```lean
theorem zero_fixture_rank : zeroFixture.rank = 0
```

- 소속: docs; 원문 상태: (미기재).
- 근거 방식: native_evaluation_in_trusted_base.
- 적용 범위: 기존 Lean 소스의 개별 theorem/lemma 선언과 명시적 가설 아래의 증명 근거. 증명 소스 바이트 버전 4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60
- 가정: \['명제 선언의 모든 명시적 바인더·가설을 그대로 가정한다. 이 가설을 제거한 일반화는 포함하지 않는다.', '파일의 선언 환경:\nimport Mathlib\nset_option autoImplicit false\nopen Matrix\nnamespace PR328LocalGlobal\nvariable {m q : Type} \[Fintype m\] \[Fintype q\]\nvariable \[DecidableEq m\] \[DecidableEq q\]\nvariable {E F : Type*}\nvariable \[NormedAddCommGroup E\] \[InnerProductSpace ℝ E\]\nvariable \[FiniteDimensional ℝ E\]\nvariable \[NormedAddCommGroup F\] \[InnerProductSpace ℝ F\]\nvariable \[FiniteDimensional ℝ F\]\nvariable {K E F G : Type u} \[DivisionRing K\]\nvariable \[AddCommGroup E\] \[Module K E\]\nvariable \[AddCommGroup F\] \[Module K F\]\nvariable \[AddCommGroup G\] \[Module K G\]'\]
- 제한: \['이번 작업에서 Lean/CAS/연구 코드를 실행하지 않았다.', '관측 응답의 물리적 유도는 physical_response_derived=false로 남는다. 기존 선형대수·확률 상계 명제의 명시된 가정만 해당한다. 소스 단위에 native_decide가 포함된다. 고정 계산과 확장된 native 평가 신뢰 기반을 구분해야 하며 kernel-reduction-only 증명이라고 부르지 않는다.', '대응한 기존 의존성·컴파일 문맥의 결과이며 다른 버전·다른 가정으로 자동 전이하지 않는다.'\]
- 후속 확인: 상위 연구 명제에 사용할 때는 아래 기존 한계와 해당 버전·가정의 일치를 확인한다.

기존 증명 및 기록:

- `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` — lines 104-110; 파일 ID `539b86fe47ad70695b8938afaa110f2c`; 소스 SHA-256 `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60`; 관찰 커밋 `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`.
- `.agent-harness/runs/pr328-local-global-identifiability-20260831/results/pr328-cas-lean.json` — $: historical source digest, compile/run command and scope fields; 파일 ID `76cd0917b1e3b2b157f3dd3a7edf2b28`; 소스 SHA-256 `a2efd1f090fcc4495493a57d209cec23d8927f0a09441a4afa9de86a01ffc427`; 관찰 커밋 `해당 없음`.

