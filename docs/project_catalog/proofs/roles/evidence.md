# 역할 분류의 원문 근거

제안 당시의 의도와 내부 사용 역할을 읽은 기록이다. 학술적 신규성이나 증명 완료를 새로 판정하지 않는다.

<a id="role-4805cfd8132b7b9a"></a>
## role-4805cfd8132b7b9a — R8.scaling_norm_fixtures

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-AC-20260909/artifacts/lean/R8.lean` 26–31행
- 내용 버전: `a1cb21e68444295606be3fe8bccd2a678de813c52b1b7236600c77dcb38420b4:ad208a43`; 관찰 커밋: `9ed6ab5cd8cbb237b9fdd84e41f906ac39896970`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `db09386f3482e483e9b749d9aaaa13ff`

~~~~text
theorem scaling_norm_fixtures :
    ((-1 : ℝ)^2 + 0^2 + 1^2 = 2) ∧
    ((2 : ℝ)^2 + 3*(-1)^2 + 3*(-1)^2 = 10) ∧
    ((2 : ℝ)^2+(-1)^2+(-1)^2 = 6) ∧
    ((-1 : ℝ)^2+(-1)^2 = 2) := by norm_num

~~~~

<a id="role-380a476d9d4ba73a"></a>
## role-380a476d9d4ba73a — R8.tie_fixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-AC-20260909/artifacts/lean/R8.lean` 127–129행
- 내용 버전: `a1cb21e68444295606be3fe8bccd2a678de813c52b1b7236600c77dcb38420b4:ad208a43`; 관찰 커밋: `9ed6ab5cd8cbb237b9fdd84e41f906ac39896970`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `d4dbcc4d21b54b66d5089437ce778931`

~~~~text
theorem tie_fixture (n : ℕ) : countGE (fun _ : Fin n => (0:ℝ)) 0 = n := by
  simp [countGE]

~~~~

<a id="role-142eff15490fc09a"></a>
## role-142eff15490fc09a — R8O4.perm_cases

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` 78–91행
- 내용 버전: `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770:ad208a43`; 관찰 커밋: `ea0305fa9e5f23e4d22a40ab826155202e76b574`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `88b23d3a661895d21a27ca1d89574a44`

~~~~text
 theorem perm_cases (p : Equiv.Perm (Fin 3)) :
     (p 0 = 0 ∧ p 1 = 1 ∧ p 2 = 2) ∨
     (p 0 = 0 ∧ p 1 = 2 ∧ p 2 = 1) ∨
     (p 0 = 1 ∧ p 1 = 0 ∧ p 2 = 2) ∨
     (p 0 = 1 ∧ p 1 = 2 ∧ p 2 = 0) ∨
     (p 0 = 2 ∧ p 1 = 0 ∧ p 2 = 1) ∨
     (p 0 = 2 ∧ p 1 = 1 ∧ p 2 = 0) := by
  have h01 : p 0 ≠ p 1 := p.injective.ne (by decide)
  have h02 : p 0 ≠ p 2 := p.injective.ne (by decide)
  have h12 : p 1 ≠ p 2 := p.injective.ne (by decide)
  generalize h0 : p 0 = x
  generalize h1 : p 1 = y
  generalize h2 : p 2 = z
  fin_cases x <;> fin_cases y <;> fin_cases z <;> simp_all
~~~~

같은 소스의 사용 문맥 (93–95행):

~~~~text
     O A (v (p 0)) (v (p 1)) (v (p 2)) = O A (v 0) (v 1) (v 2) := by
  rcases perm_cases p with h|h|h|h|h|h <;> rcases h with ⟨h0,h1,h2⟩ <;> rw [h0,h1,h2]
  all_goals funext i j k
~~~~

<a id="role-6d906962acee7dfe"></a>
## role-6d906962acee7dfe — R8O4.q_cast

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` 132–135행
- 내용 버전: `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770:ad208a43`; 관찰 커밋: `ea0305fa9e5f23e4d22a40ab826155202e76b574`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `4c7d6898fa7e7fe7f7335123fc127947`

~~~~text
 theorem q_cast (A : ℝ) (u v : V ℝ) (i j : Fin 3) :
     ((Q A u v i j : ℝ) : ℂ) = Q (A : ℂ) (complexify u) (complexify v) i j := by
  simp only [Q, S2, delta, dot, complexify, Fin.sum_univ_succ]
  split_ifs <;> push_cast <;> ring
~~~~

같은 소스의 사용 문맥 (142–144행):

~~~~text
     (A : ℂ)*dot (complexify u) (nullVector z)*dot (complexify v) (nullVector z) := by
  simp_rw [q_cast]
  exact q_null _ _ _ _
~~~~

<a id="role-e98795336971b348"></a>
## role-e98795336971b348 — R8O4.o_cast

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-B-20260909/artifacts/direct_execution/O4.lean` 136–139행
- 내용 버전: `f46f52f91ff0dffcc27ae59fd1d03391bebde8a8663ba52b1ea70d2ae54d1770:ad208a43`; 관찰 커밋: `ea0305fa9e5f23e4d22a40ab826155202e76b574`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `5a7c8d3cc151ccd4c16dd40b2e7a4b10`

~~~~text
 theorem o_cast (A : ℝ) (u v w : V ℝ) (i j k : Fin 3) :
     ((O A u v w i j k : ℝ) : ℂ) = O (A : ℂ) (complexify u) (complexify v) (complexify w) i j k := by
  simp only [O, S3, b, delta, dot, complexify, Fin.sum_univ_succ]
  split_ifs <;> push_cast <;> ring
~~~~

같은 소스의 사용 문맥 (148–150행):

~~~~text
     dot (complexify w) (nullVector z) := by
  simp_rw [o_cast]
  exact o_null _ _ _ _ _
~~~~

<a id="role-b5a19545fc943675"></a>
## role-b5a19545fc943675 — R8D.fixture_norms

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-D-20260910/artifacts/direct_execution/Support.lean` 12–12행
- 내용 버전: `749977f58d7746684890e4e5d5da02575f123e620c5949f1ac5c5266ad4863b4:ad208a43`; 관찰 커밋: `7b571adb2e39d233a10c6633d51da74d9d50a0ca`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `480e1cc8f9f9d008cb901d669104e3f7`

~~~~text
theorem fixture_norms : (1:ℚ)^2+2^2+1^2+2^2+1^2+2^2+1^2+2^2=20 := by norm_num
~~~~

같은 소스의 사용 문맥 (25–27행):

~~~~text
#print axioms p1_w
#print axioms fixture_norms
#print axioms allocation
~~~~

<a id="role-7d1f7e9a85869887"></a>
## role-7d1f7e9a85869887 — R8D.ray_fixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/R8-D-20260910/artifacts/direct_execution/Support.lean` 16–16행
- 내용 버전: `749977f58d7746684890e4e5d5da02575f123e620c5949f1ac5c5266ad4863b4:ad208a43`; 관찰 커밋: `7b571adb2e39d233a10c6633d51da74d9d50a0ca`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `0d6796dfcf51dc77d1a57b86d9b4e17e`

~~~~text
theorem ray_fixture : v 0=0 ∧ v 1=0 ∧ v 2=0 ∧ v 3=0 ∧ v 7=1 := by decide
~~~~

같은 소스의 사용 문맥 (28–30행):

~~~~text
#print axioms sets
#print axioms ray_fixture
#print axioms ray_preserves
~~~~

<a id="role-3676466847525676"></a>
## role-3676466847525676 — PR254R3LeanAxis.finiteMax_le_iff

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 34–37행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `fca70042f9085a484f255f2b1c394052`

~~~~text
theorem finiteMax_le_iff (f : ι → ℝ) (c : ℝ) :
    finiteMax f ≤ c ↔ ∀ i, f i ≤ c := by
  simp [finiteMax, Finset.sup'_le_iff]

~~~~

같은 소스의 사용 문맥 (69–71행):

~~~~text
      ∀ j, blockEuclideanNorm A u j ≤ A.radii j := by
  rw [productGauge, finiteMax_le_iff]
  constructor
~~~~

<a id="role-64b98c41530d171f"></a>
## role-64b98c41530d171f — PR254R3LeanAxis.le_finiteMax

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 38–46행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `e3b91799f428c6a1450668f153b8ab09`

~~~~text
theorem le_finiteMax (f : ι → ℝ) (i : ι) :
    f i ≤ finiteMax f := by
  unfold finiteMax
  exact Finset.le_sup' (f := f) (Finset.mem_univ i)

end FiniteMaximum

/-! ## Product of typed Euclidean block balls -/

~~~~

같은 소스의 사용 문맥 (262–264행):

~~~~text
              polytopeFixture.bound i) :=
      le_finiteMax
        (fun i =>
~~~~

<a id="role-58b453b9e445b0a0"></a>
## role-58b453b9e445b0a0 — ellipsoid_fixture_form

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 112–117행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `bce6e597f8a24c68bd5ef5532a34d0de`

~~~~text
theorem ellipsoid_fixture_form (u : Fin 2 → ℝ) :
    quadraticForm ellipsoidFixtureQ u =
      (u 0) ^ 2 / 4 + (u 1) ^ 2 / 9 := by
  simp [quadraticForm, ellipsoidFixtureQ, Fin.sum_univ_two]
  ring

~~~~

같은 소스의 사용 문맥 (130–132행):

~~~~text
    · exact Or.inl h0
  rw [ellipsoid_fixture_form]
  rcases hcomponent with h0 | h1
~~~~

<a id="role-4c7226f3f01c247d"></a>
## role-4c7226f3f01c247d — ellipsoid_fixture_positive_definite

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 118–139행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `c0d7e07abb5be1917cd1a3a391ae71bb`

~~~~text
theorem ellipsoid_fixture_positive_definite :
    ∀ u : Fin 2 → ℝ, u ≠ 0 → 0 < quadraticForm ellipsoidFixtureQ u := by
  intro u hu
  have hcomponent : u 0 ≠ 0 ∨ u 1 ≠ 0 := by
    by_cases h0 : u 0 = 0
    · right
      intro h1
      apply hu
      funext i
      fin_cases i
      · exact h0
      · exact h1
    · exact Or.inl h0
  rw [ellipsoid_fixture_form]
  rcases hcomponent with h0 | h1
  · have hs0 : 0 < (u 0) ^ 2 := sq_pos_of_ne_zero h0
    have hs1 : 0 ≤ (u 1) ^ 2 := sq_nonneg (u 1)
    nlinarith
  · have hs0 : 0 ≤ (u 0) ^ 2 := sq_nonneg (u 0)
    have hs1 : 0 < (u 1) ^ 2 := sq_pos_of_ne_zero h1
    nlinarith

~~~~

같은 소스의 사용 문맥 (145–147행):

~~~~text
      norm_num [ellipsoidFixtureQ, Matrix.transpose_apply]
  positive_definite := ellipsoid_fixture_positive_definite

~~~~

<a id="role-a9638c6ddcc52bf9"></a>
## role-a9638c6ddcc52bf9 — polytope_fixture_normals_span

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 205–215행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `05db3a53e9f6efd545160101585f6688`

~~~~text
theorem polytope_fixture_normals_span :
    normalsSpan polytopeFixtureNormals := by
  unfold normalsSpan
  intro u h
  funext j
  fin_cases j
  · have h0 := h 0
    simpa [polytopeFixtureNormals, dotProduct, Fin.sum_univ_two] using h0
  · have h2 := h 2
    simpa [polytopeFixtureNormals, dotProduct, Fin.sum_univ_two] using h2

~~~~

같은 소스의 사용 문맥 (221–223행):

~~~~text
    fin_cases i <;> norm_num [polytopeFixtureBounds]
  normals_span := polytope_fixture_normals_span
  antipodal := by
~~~~

<a id="role-f449e4a70e270e00"></a>
## role-f449e4a70e270e00 — rank_fixture_S_isUnit_matrix

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 356–358행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `f590ab222207bae4af6dbc2a56fdc292`

~~~~text
theorem rank_fixture_S_isUnit_matrix : IsUnit rankFixtureS :=
  rankFixtureS.isUnit_iff_isUnit_det.mpr rank_fixture_S_isUnit

~~~~

같은 소스의 사용 문맥 (359–361행):

~~~~text
theorem rank_fixture_S_exact : rankFixtureS.rank = 2 := by
  simpa using Matrix.rank_of_isUnit rankFixtureS rank_fixture_S_isUnit_matrix

~~~~

<a id="role-fefb55232afa9f8e"></a>
## role-fefb55232afa9f8e — rank_fixture_S_exact

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 359–361행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `2e98e9d3272df1da862f09ffe5de7b5f`

~~~~text
theorem rank_fixture_S_exact : rankFixtureS.rank = 2 := by
  simpa using Matrix.rank_of_isUnit rankFixtureS rank_fixture_S_isUnit_matrix

~~~~

같은 소스의 사용 문맥 (364–366행):

~~~~text
    have hsub := Matrix.rank_submatrix_le rankFixtureR firstTwoRows id
    rw [rank_fixture_submatrix, rank_fixture_S_exact] at hsub
    exact hsub
~~~~

<a id="role-bffaae6be0749899"></a>
## role-bffaae6be0749899 — rank_fixture_R_exact

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 362–370행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `6dfd27b1d5457437bc941c62fe937ce1`

~~~~text
theorem rank_fixture_R_exact : rankFixtureR.rank = 2 := by
  have hlower : 2 ≤ rankFixtureR.rank := by
    have hsub := Matrix.rank_submatrix_le rankFixtureR firstTwoRows id
    rw [rank_fixture_submatrix, rank_fixture_S_exact] at hsub
    exact hsub
  have hupper : rankFixtureR.rank ≤ 2 := by
    simpa using Matrix.rank_le_card_width rankFixtureR
  exact le_antisymm hupper hlower

~~~~

같은 소스의 사용 문맥 (381–383행):

~~~~text
      rank_fixture_D_isUnit,
    rank_fixture_R_exact]

~~~~

<a id="role-22a9197b4b291804"></a>
## role-22a9197b4b291804 — rank_fixture_D_det

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 371–373행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `2bf93b5f89a5ce1712fdb5dff0c16955`

~~~~text
theorem rank_fixture_D_det : rankFixtureD.det = 1 := by
  norm_num [rankFixtureD, Matrix.det_fin_two]

~~~~

같은 소스의 사용 문맥 (374–376행):

~~~~text
theorem rank_fixture_D_isUnit : IsUnit rankFixtureD.det := by
  rw [rank_fixture_D_det]
  exact isUnit_one
~~~~

<a id="role-61325e7f80e21bb2"></a>
## role-61325e7f80e21bb2 — rank_fixture_D_isUnit

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 374–377행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `e23cd9b287412491da53f9e0c622b881`

~~~~text
theorem rank_fixture_D_isUnit : IsUnit rankFixtureD.det := by
  rw [rank_fixture_D_det]
  exact isUnit_one

~~~~

같은 소스의 사용 문맥 (380–382행):

~~~~text
  rw [invertible_scaling_rank rankFixtureR rankFixtureD
      rank_fixture_D_isUnit,
    rank_fixture_R_exact]
~~~~

<a id="role-44cc46218bc28220"></a>
## role-44cc46218bc28220 — rank_fixture_RD_exact

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr254-cas-r3-20260728/artifacts/A-PR254-R3-CAS-LEAN/PR254R3LeanAxis.lean` 378–385행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `4f3201a88b39a0d33cc21f3776313947`

~~~~text
theorem rank_fixture_RD_exact :
    (rankFixtureR * rankFixtureD).rank = 2 := by
  rw [invertible_scaling_rank rankFixtureR rankFixtureD
      rank_fixture_D_isUnit,
    rank_fixture_R_exact]

/-! ## J1 exact outer-envelope counterexample -/

~~~~

<a id="role-c855c444d3b56d21"></a>
## role-c855c444d3b56d21 — PR257Orbit.Vec3.extensionality

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 44–49행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `06550bbb4668ef1397238e93a65357d3`

~~~~text
theorem Vec3.extensionality {u v : Vec3}
    (hx : u.x = v.x) (hy : u.y = v.y) (hz : u.z = v.z) : u = v := by
  cases u
  cases v
  grind

~~~~

같은 소스의 사용 문맥 (49–51행):

~~~~text

theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
~~~~

<a id="role-2a8e7a7a58e974ba"></a>
## role-2a8e7a7a58e974ba — PR257Orbit.Mat3.extensionality

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 50–59행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `fadd119972d03372754d70036c1a4101`

~~~~text
theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
    (h02 : A.m02 = B.m02) (h10 : A.m10 = B.m10)
    (h11 : A.m11 = B.m11) (h12 : A.m12 = B.m12)
    (h20 : A.m20 = B.m20) (h21 : A.m21 = B.m21)
    (h22 : A.m22 = B.m22) : A = B := by
  cases A
  cases B
  grind

~~~~

같은 소스의 사용 문맥 (130–132행):

~~~~text
theorem mm_assoc (A B C : Mat3) : mm (mm A B) C = mm A (mm B C) := by
  apply Mat3.extensionality <;> grind [mm]

~~~~

<a id="role-faf362cac87c3297"></a>
## role-faf362cac87c3297 — PR257Orbit.mm_assoc

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 130–132행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `f3d387a84a1183b26b8eccf3f64e74ed`

~~~~text
theorem mm_assoc (A B C : Mat3) : mm (mm A B) C = mm A (mm B C) := by
  apply Mat3.extensionality <;> grind [mm]

~~~~

같은 소스의 사용 문맥 (179–181행):

~~~~text
        = mm (mm R sigma) (mm (transpose R) R) := by
            simp only [sigmaAction, mm_assoc]
    _ = mm (mm R sigma) ident := by rw [hR.rt_mul_r]
~~~~

<a id="role-b5426617bdaae211"></a>
## role-b5426617bdaae211 — PR257Orbit.mm_ident_left

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 133–135행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `774c45ad11a0488bb5527f1606a295d0`

~~~~text
theorem mm_ident_left (A : Mat3) : mm ident A = A := by
  apply Mat3.extensionality <;> grind [mm, ident]

~~~~

같은 소스의 사용 문맥 (209–211행):

~~~~text
    _ = trace (mm ident A) := by rw [hR.rt_mul_r]
    _ = trace A := by rw [mm_ident_left]

~~~~

<a id="role-3c358c965bc96a70"></a>
## role-3c358c965bc96a70 — PR257Orbit.fromCols_mv

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 154–157행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `8bd0ca2b1ce53f9851ef2a6abab9ddc1`

~~~~text
theorem fromCols_mv (R : Mat3) (u v w : Vec3) :
    fromCols (mv R u) (mv R v) (mv R w) = mm R (fromCols u v w) := by
  apply Mat3.extensionality <;> grind [fromCols, mv, mm]

~~~~

같은 소스의 사용 문맥 (267–269행):

~~~~text
  rw [sigmaAction_mv hR, sigmaAction_mv hR]
  rw [fromCols_mv, det_mul]

~~~~

<a id="role-73c53125cdaf77eb"></a>
## role-73c53125cdaf77eb — PR257Orbit.det_sq_one

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 158–160행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `782511d2a93a698cdff1fdf905d75018`

~~~~text
theorem det_sq_one {R : Mat3} (hR : O3 R) : det R * det R = 1 := by
  rcases hR.det_sign with h | h <;> grind

~~~~

같은 소스의 사용 문맥 (297–299행):

~~~~text
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
  have hd := det_sq_one hR
  grind
~~~~

<a id="role-9212618928aa87e8"></a>
## role-9212618928aa87e8 — PR257Orbit.dot_mv_adjoint

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 161–164행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `f3578bce6754bf1f2fbc5f1a20f1934d`

~~~~text
theorem dot_mv_adjoint (R : Mat3) (u v : Vec3) :
    dot (mv R u) v = dot u (mv (transpose R) v) := by
  grind [dot, mv, transpose]

~~~~

같은 소스의 사용 문맥 (168–170행):

~~~~text
    dot (mv R u) (mv R v)
        = dot u (mv (transpose R) (mv R v)) := dot_mv_adjoint _ _ _
    _ = dot u (mv (mm (transpose R) R) v) := by
~~~~

<a id="role-1d415c875b9e22f7"></a>
## role-1d415c875b9e22f7 — PR257Orbit.dot_mv

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 165–174행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `d91fd6284e1e2dd923454bb009b01aae`

~~~~text
theorem dot_mv {R : Mat3} (hR : O3 R) (u v : Vec3) :
    dot (mv R u) (mv R v) = dot u v := by
  calc
    dot (mv R u) (mv R v)
        = dot u (mv (transpose R) (mv R v)) := dot_mv_adjoint _ _ _
    _ = dot u (mv (mm (transpose R) R) v) := by
          rw [mv_assoc]
    _ = dot u (mv ident v) := by rw [hR.rt_mul_r]
    _ = dot u v := by rw [mv_ident]

~~~~

같은 소스의 사용 문맥 (245–247행):

~~~~text
    beta2 (mv R beta) = beta2 beta := by
  exact dot_mv hR beta beta

~~~~

<a id="role-40e323c0b09300a4"></a>
## role-40e323c0b09300a4 — PR257Orbit.trace_sigmaAction

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 203–211행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `e28ccac02a3b30d8414fd561cfcd0f94`

~~~~text
theorem trace_sigmaAction {R : Mat3} (hR : O3 R) (A : Mat3) :
    trace (sigmaAction R A) = trace A := by
  calc
    trace (sigmaAction R A)
        = trace (mm (transpose R) (mm R A)) := trace_cyclic _ _
    _ = trace (mm (mm (transpose R) R) A) := by rw [mm_assoc]
    _ = trace (mm ident A) := by rw [hR.rt_mul_r]
    _ = trace A := by rw [mm_ident_left]

~~~~

같은 소스의 사용 문맥 (214–216행):

~~~~text
  unfold tr2
  rw [sigmaAction_mul hR A A, trace_sigmaAction hR]

~~~~

<a id="role-2d502b0eb33b166f"></a>
## role-2d502b0eb33b166f — PR257Orbit.dot_vscale_right

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 274–277행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `ec6e7b5b79ff45aa55d58d6092a4db2c`

~~~~text
theorem dot_vscale_right (a : Rat) (u v : Vec3) :
    dot u (vscale a v) = a * dot u v := by
  grind [dot, vscale]

~~~~

같은 소스의 사용 문맥 (296–298행):

~~~~text
  unfold omega2
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
  have hd := det_sq_one hR
~~~~

<a id="role-538ba5c8f32f203b"></a>
## role-538ba5c8f32f203b — PR257Orbit.mv_madd

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 282–285행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `56a858d37bd9aaa57d87ed1c4a87d5e4`

~~~~text
theorem mv_madd (A B : Mat3) (u : Vec3) :
    mv (madd A B) u = vadd (mv A u) (mv B u) := by
  apply Vec3.extensionality <;> grind [mv, madd, vadd]

~~~~

같은 소스의 사용 문맥 (397–399행):

~~~~text
  rw [cayleyHamiltonSTF]
  rw [mv_madd, mv_mscale, mv_mscale, dot_vadd_right,
    dot_vscale_right, dot_vscale_right, mv_ident]
~~~~

<a id="role-3ad05304ff0e2e18"></a>
## role-3ad05304ff0e2e18 — PR257Orbit.mv_mscale

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 286–289행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `623ffa8aedbf93b7ca57245322a805f5`

~~~~text
theorem mv_mscale (a : Rat) (A : Mat3) (u : Vec3) :
    mv (mscale a A) u = vscale a (mv A u) := by
  apply Vec3.extensionality <;> grind [mv, mscale, vscale]

~~~~

같은 소스의 사용 문맥 (397–399행):

~~~~text
  rw [cayleyHamiltonSTF]
  rw [mv_madd, mv_mscale, mv_mscale, dot_vadd_right,
    dot_vscale_right, dot_vscale_right, mv_ident]
~~~~

<a id="role-a342638d2b0c619a"></a>
## role-a342638d2b0c619a — PR257Orbit.dot_vadd_right

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 290–293행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `d77f030196588776a45796d4f06f4826`

~~~~text
theorem dot_vadd_right (u v w : Vec3) :
    dot u (vadd v w) = dot u v + dot u w := by
  grind [dot, vadd]

~~~~

같은 소스의 사용 문맥 (397–399행):

~~~~text
  rw [cayleyHamiltonSTF]
  rw [mv_madd, mv_mscale, mv_mscale, dot_vadd_right,
    dot_vscale_right, dot_vscale_right, mv_ident]
~~~~

<a id="role-5d8fc2aced75db73"></a>
## role-5d8fc2aced75db73 — PR257Orbit.fixed_tr_sigma2

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 446–446행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `1896e57cd27670e20f966b5791766b4f`

~~~~text
theorem fixed_tr_sigma2 : tr2 fixedSigma = 14 := by native_decide
~~~~

<a id="role-d39b8ed959795a84"></a>
## role-d39b8ed959795a84 — PR257Orbit.fixed_tr_sigma3

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 447–447행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `9d2b7d772213fe34361f6d9c0f92aac4`

~~~~text
theorem fixed_tr_sigma3 : tr3 fixedSigma = -18 := by native_decide
~~~~

<a id="role-0b189742bcc53704"></a>
## role-0b189742bcc53704 — PR257Orbit.fixed_beta2

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 448–448행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `7a9591e2986900fbd53bde4a6513e884`

~~~~text
theorem fixed_beta2 : beta2 fixedBeta = 3 := by native_decide
~~~~

<a id="role-aa5dda2f9face489"></a>
## role-aa5dda2f9face489 — PR257Orbit.fixed_beta_sigma2_beta

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 451–452행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `863db3f06d3662fd3f04611024a6ec21`

~~~~text
theorem fixed_beta_sigma2_beta :
    betaSigma2Beta fixedSigma fixedBeta = 14 := by native_decide
~~~~

<a id="role-0f9650ae9cb785a1"></a>
## role-0f9650ae9cb785a1 — PR257Orbit.fixed_beta_krylov_det

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 453–454행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `ce328fcb86aa69bf62ab9de535d7c276`

~~~~text
theorem fixed_beta_krylov_det :
    betaKrylovDet fixedSigma fixedBeta = 20 := by native_decide
~~~~

<a id="role-9ec3f80db20ed5f4"></a>
## role-9ec3f80db20ed5f4 — PR257Orbit.fixed_beta_sigma2_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 464–466행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `1cdc27b9e2a49dfded8330ca39ee4c8a`

~~~~text
theorem fixed_beta_sigma2_omega :
    betaSigma2Omega fixedSigma fixedBeta fixedOmega = 36 := by native_decide

~~~~

<a id="role-3745322819312c03"></a>
## role-3745322819312c03 — PR257Orbit.fixed_beta_sigma3_beta

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 474–475행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `4e2c66e4632553a88f09971301c2319b`

~~~~text
theorem fixed_beta_sigma3_beta :
    betaSigma3Beta fixedSigma fixedBeta = -18 := by native_decide
~~~~

<a id="role-12105fde8fb2de59"></a>
## role-12105fde8fb2de59 — PR257Orbit.fixed_beta_sigma3_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 478–479행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `80be90e285330c61658fba7e1466fae4`

~~~~text
theorem fixed_beta_sigma3_omega :
    betaSigma3Omega fixedSigma fixedBeta fixedOmega = -64 := by native_decide
~~~~

<a id="role-9ee2ef099e5df542"></a>
## role-9ee2ef099e5df542 — PR257Orbit.completeness_not_promoted

- 역할: 내부 보조명제·검증 보조정리
- 출처: `.agent-harness/runs/premise-anchor-pr257-cas-r2-20260729/artifacts/A-PR257-CAS-LEAN-R2/PR257OrbitAxis.lean` 527–534행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `e610bb1a772df8aaace2cbaf46b0eafd`

~~~~text
theorem completeness_not_promoted :
    invariantRingCompletenessStatus = .UNPROVEN := rfl

/-!
  The eight contract-level checks are represented as propositions that are
  inhabited only because the load-bearing theorems above compiled.
-/

~~~~

<a id="role-61db4486cf9c9245"></a>
## role-61db4486cf9c9245 — NT2-A1 — Genuine multi-multipole Fisher–Cramér–Rao floor on `F_shear`  [Provable; flagship]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 9–22행
- 내용 버전: `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT2-A1 — Genuine multi-multipole Fisher–Cramér–Rao floor on `F_shear`  [Provable; flagship]

**Statement.** Let `F_shear` depend on the low-ℓ CMB through the multipole powers `{C_ℓ}_{ℓ≥2}`, with response `r_ℓ = ∂ln C_ℓ/∂ln F_shear` (`r₂=1` by NT-A1; `r_{ℓ>2}>0` because the shear sources `ℓ>2` via the EGS gradient/octupole chain). For Gaussian multipoles on a fraction `f_sky` of sky, the Fisher information is `I = Σ_{ℓ≥2}(2ℓ+1)/2·f_sky·r_ℓ²`, and the Cramér–Rao bound on *any* unbiased estimator is
`σ(F_shear)/F_shear ≥ I^{−1/2} = [Σ_{ℓ≥2}(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`.
This is **strictly below** the single-ℓ value `√(2/(2·2+1))=√(2/5)≈0.632`, and decreases as more multipoles are included; sky cuts (`f_sky<1`) raise it.

**Why it matters (audit fix).** The report's NT-A3 labels the single-estimator sampling dispersion a "Cramér–Rao floor / irreducible / unmeasurable below 63%". That is not a floor over all estimators. NT2-A1 supplies the actual floor and shows it is lower — the report's "floor" language becomes correct only once stated as NT2-A1.

**Proof sketch.** For independent Gaussian `a_{ℓm}` with variance `C_ℓ`, `−∂²lnL/∂C_ℓ² ⇒ I(C_ℓ)=(2ℓ+1)f_sky/(2C_ℓ²)`; chain through `r_ℓ` to `F_shear` and sum the independent multipoles (Fisher additivity). The single-ℓ term recovers `√(2/5)`; any `r_{ℓ>2}>0` strictly increases `I`, lowering the floor. ∎ (MC-verified: a multipole-combining MLE achieves the floor, ratio→1.)

**Numerical support.** NT2-A1: floor 0.632→0.474→0.424 (`L=2,5,20`, `f_sky=1`); `f_sky=0.7` raises it; MC MLE ratio 0.99–1.00.

**To close.** Replace the toy response `r_ℓ` with the exact covariant ℓ=2/ℓ=3 coefficients and a real low-ℓ transfer; quote the floor with Planck `f_sky` and mask coupling.

~~~~

제안 의도 문맥 (`audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# 04 — Theorem Candidates (NT2-\*)

New theorems from applying the covariant Einstein–Boltzmann system to the report's diagnostic variables, beyond `T-*`, `F-*`, `N-*`, the report's `NT-A1/A3/B3`, and PAPER-A/B. Notation as in the report: temperature multipoles `a_ℓ=|τ_ℓ|`; quadrupole power `D₂∝a₂²`, `C_ℓ` the angular power; shear scalar `Σ`; shear-filling `F_shear=Σ²/x_max`, `x_max=9.25×10⁻⁶`; tilt anisotropic stress `Π_ab`. Spine: ETM ℓ=2↔shear (`κ=4/21`), the almost-EGS hypotheses H1–H3, and the standard Gaussian low-ℓ power statistics. Status: **Provable / Conditional / Forecast**.

---
~~~~

<a id="role-ac63913e9a4082d8"></a>
## role-ac63913e9a4082d8 — NT2-A2 — Quadrupole+octupole sufficiency / EGS information saturation  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 23–30행
- 내용 버전: `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT2-A2 — Quadrupole+octupole sufficiency / EGS information saturation  [Conditional]

**Statement.** At leading EGS order the shear sources only `ℓ=2,3` appreciably (`r_ℓ` decays for `ℓ>3`); hence `(a₂,a₃)` is an approximately sufficient statistic for `F_shear`, and the marginal Fisher information from `ℓ>3` is bounded by `Σ_{ℓ>3}(2ℓ+1)/2·f_sky·r_ℓ²`, which converges. Measuring beyond the octupole yields diminishing returns for the shear-filling.

**Proof sketch.** Sufficiency from the factorisation of the Gaussian likelihood given `(C₂,C₃)` when `r_{ℓ>3}≈0`; the bound is the Fisher tail sum, convergent for any decaying `r_ℓ`. ∎

**To close.** A dedicated experiment computing the Fisher tail with the real `r_ℓ`; quantify the `(a₂,a₃)` sufficiency gap.

~~~~

제안 의도 문맥 (`audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# 04 — Theorem Candidates (NT2-\*)

New theorems from applying the covariant Einstein–Boltzmann system to the report's diagnostic variables, beyond `T-*`, `F-*`, `N-*`, the report's `NT-A1/A3/B3`, and PAPER-A/B. Notation as in the report: temperature multipoles `a_ℓ=|τ_ℓ|`; quadrupole power `D₂∝a₂²`, `C_ℓ` the angular power; shear scalar `Σ`; shear-filling `F_shear=Σ²/x_max`, `x_max=9.25×10⁻⁶`; tilt anisotropic stress `Π_ab`. Spine: ETM ℓ=2↔shear (`κ=4/21`), the almost-EGS hypotheses H1–H3, and the standard Gaussian low-ℓ power statistics. Status: **Provable / Conditional / Forecast**.

---
~~~~

<a id="role-93d992474af4a17c"></a>
## role-93d992474af4a17c — NT2-A3 — Registered global exceedance bound  [Conditional → Forecast]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 31–40행
- 내용 버전: `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT2-A3 — Registered global exceedance bound  [Conditional → Forecast]

**Statement.** For a frozen family of `m` low-ℓ statistics, convert each to a tail score, take the max, and form the rank Monte-Carlo p-value with the `+1` correction: `p_global=(#{sim max ≥ obs max}+1)/(N+1)`. Then `p_global ≥ max_i p_local,i` (no look-elsewhere undercount), and the registered exceedance `Π` over the family is calibrated. This makes the K1 "not globally significant" statement a *theorem* about the estimator, not a caveat.

**Proof sketch.** The max-scan rank statistic dominates each component rank; the `+1` correction bounds the estimator from below. ∎

**To close.** Run on the public Planck E2E ensemble (see `BLOCKER_SOLUTIONS.md`, K1).

---

~~~~

제안 의도 문맥 (`audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# 04 — Theorem Candidates (NT2-\*)

New theorems from applying the covariant Einstein–Boltzmann system to the report's diagnostic variables, beyond `T-*`, `F-*`, `N-*`, the report's `NT-A1/A3/B3`, and PAPER-A/B. Notation as in the report: temperature multipoles `a_ℓ=|τ_ℓ|`; quadrupole power `D₂∝a₂²`, `C_ℓ` the angular power; shear scalar `Σ`; shear-filling `F_shear=Σ²/x_max`, `x_max=9.25×10⁻⁶`; tilt anisotropic stress `Π_ab`. Spine: ETM ℓ=2↔shear (`κ=4/21`), the almost-EGS hypotheses H1–H3, and the standard Gaussian low-ℓ power statistics. Status: **Provable / Conditional / Forecast**.

---
~~~~

<a id="role-7656eee17e6a41ff"></a>
## role-7656eee17e6a41ff — NT2-B1 — Two-sided quadrupole+octupole shear/`F` bracket  [Conditional; flagship]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 43–54행
- 내용 버전: `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT2-B1 — Two-sided quadrupole+octupole shear/`F` bracket  [Conditional; flagship]

**Statement.** Under H3 (`R_EGS=a₃/a₂≤R*`), the shear is bracketed by the observed quadrupole+octupole:
`a₂·κ/(1+R_EGS) ≤ Σ ≤ C_up·a₂`,
so `F_shear ∈ [ (a₂κ/(1+R_EGS))²/x_max , (C_up a₂)²/x_max ]`. The **lower** bound is the new, strong content: a **nonzero** CMB quadrupole **forbids a vanishing shear-filling** — an exclusion of zero at fixed `a₂`, not merely an upper limit.

**Proof sketch.** Upper: MES. Lower: the ℓ=2 relation `a₂=κΣ + (derivative correction)`; H3 bounds the derivative correction by `R_EGS·a₂`, so `Σ ≥ a₂/(κ⁻¹(1+R_EGS))`. ∎ (verified: `F_lo>0` in all rows.)

**Numerical support.** NT2-B1: e.g. `a₂=3×10⁻⁵, a₃=6×10⁻⁶ (R_EGS=0.2)` → `F_shear∈[2.45×10⁻⁶, 7.88×10⁻³]`, bounded away from zero.

**To close.** Exact MES upper constant and the covariant derivative-correction coefficient; quote the bracket with Planck `a₂,a₃`.

~~~~

제안 의도 문맥 (`audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# 04 — Theorem Candidates (NT2-\*)

New theorems from applying the covariant Einstein–Boltzmann system to the report's diagnostic variables, beyond `T-*`, `F-*`, `N-*`, the report's `NT-A1/A3/B3`, and PAPER-A/B. Notation as in the report: temperature multipoles `a_ℓ=|τ_ℓ|`; quadrupole power `D₂∝a₂²`, `C_ℓ` the angular power; shear scalar `Σ`; shear-filling `F_shear=Σ²/x_max`, `x_max=9.25×10⁻⁶`; tilt anisotropic stress `Π_ab`. Spine: ETM ℓ=2↔shear (`κ=4/21`), the almost-EGS hypotheses H1–H3, and the standard Gaussian low-ℓ power statistics. Status: **Provable / Conditional / Forecast**.

---
~~~~

<a id="role-268fdb1bddd84233"></a>
## role-268fdb1bddd84233 — NT2-B2 — GR shear-memory-sourced depth transport of `G_F`  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 55–64행
- 내용 버전: `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT2-B2 — GR shear-memory-sourced depth transport of `G_F`  [Conditional]

**Statement.** Using PAPER-B's shear-memory law `σ̇=−3Hσ+3H²Π` (`Π` the tilt anisotropic stress), the depth gap obeys a transport equation whose source is `Π(z)`: a depth-evolving `Π(z)` produces a depth-evolving `G_F(z)`, while a steady `Π` relaxes `G_F` toward a constant (EGS-like). This upgrades NT-B3's "a `ΔF` trend is attributable to the tilt only with a response-rank gate" to "the tilt anisotropic stress is the **explicit GR source** of the depth gap."

**Proof sketch.** Integrate the shear-memory ODE with source `3H²Π(z)`; `F_shear(z)=σ(z)²/x_max`; differentiate along the line of sight. Steady `Π` → `σ→` const → flat `G_F`; growing `Π(z)` → growing `σ(z)` → depth-dependent `G_F`. ∎ (verified.)

**Numerical support.** NT2-B2: steady `Π` → `G_F` spread 0; growing `Π(z)~z` → spread 2.45.

**To close.** The real `H(z)` and a survey-matched depth binning; couple to the prior tomographic forecast.

~~~~

제안 의도 문맥 (`audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# 04 — Theorem Candidates (NT2-\*)

New theorems from applying the covariant Einstein–Boltzmann system to the report's diagnostic variables, beyond `T-*`, `F-*`, `N-*`, the report's `NT-A1/A3/B3`, and PAPER-A/B. Notation as in the report: temperature multipoles `a_ℓ=|τ_ℓ|`; quadrupole power `D₂∝a₂²`, `C_ℓ` the angular power; shear scalar `Σ`; shear-filling `F_shear=Σ²/x_max`, `x_max=9.25×10⁻⁶`; tilt anisotropic stress `Π_ab`. Spine: ETM ℓ=2↔shear (`κ=4/21`), the almost-EGS hypotheses H1–H3, and the standard Gaussian low-ℓ power statistics. Status: **Provable / Conditional / Forecast**.

---
~~~~

<a id="role-9526674fe35823d9"></a>
## role-9526674fe35823d9 — NT2-B3 — Vorticity joint blind-sector no-go  [Provable, grounded]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 65–74행
- 내용 버전: `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT2-B3 — Vorticity joint blind-sector no-go  [Provable, grounded]

**Statement.** The vorticity term `W²_std` in `x_C` is unconstrained by the two observational channels the program uses, *simultaneously*: (i) CMB temperature multipoles do not bound the curl/magnetic-Weyl sector at EGS order (H3/Weyl loophole), and (ii) radial peculiar-velocity data carry no vorticity, since `n^aΩ_ab n^b=0` exactly for any antisymmetric `Ω` (PAPER-A A-radial-novortex). Therefore no estimator built on CMB-temperature + radial velocities alone can constrain the comparator's vorticity term — a strong no-go on the diagnostic's reach.

**Proof sketch.** (ii) is an algebraic identity (`Ω` antisymmetric ⇒ `n·Ω·n=0`); (i) is the Weyl loophole (NUWL 1999). The union closes both channels. ∎ (verified: radial projection 3.3e-16; CMB-T sensitivity 0.)

**To close.** State which *additional* channel (tangential velocities, polarisation B-modes, or the native low-ℓ morphology) re-opens the vorticity sector.

---

~~~~

제안 의도 문맥 (`audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# 04 — Theorem Candidates (NT2-\*)

New theorems from applying the covariant Einstein–Boltzmann system to the report's diagnostic variables, beyond `T-*`, `F-*`, `N-*`, the report's `NT-A1/A3/B3`, and PAPER-A/B. Notation as in the report: temperature multipoles `a_ℓ=|τ_ℓ|`; quadrupole power `D₂∝a₂²`, `C_ℓ` the angular power; shear scalar `Σ`; shear-filling `F_shear=Σ²/x_max`, `x_max=9.25×10⁻⁶`; tilt anisotropic stress `Π_ab`. Spine: ETM ℓ=2↔shear (`κ=4/21`), the almost-EGS hypotheses H1–H3, and the standard Gaussian low-ℓ power statistics. Status: **Provable / Conditional / Forecast**.

---
~~~~

<a id="role-3fc75c9afe77083a"></a>
## role-3fc75c9afe77083a — A37 — Evidence anatomy consistency theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_v4_critical_upgraded.md` 2856–2856행
- 내용 버전: `da980db92be1208852e018841c1d6929e22e538691beb32b0151ca498dc3e264:c57f56a5`; 관찰 커밋: `96e69e648f1182f4ae4f977a854066e0dc6c154f`
- 이유: 구판 연구계획이 신규 appendix A37로 증명 목표와 근사 합산식을 명시한다. 가정·오차의 정식화 및 후속 구현은 이 역할 판정에서 확인하지 않았다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A37 | **Evidence anatomy consistency theorem** (Σ channels Δln B ≈ total ln B) | ~200 L |
~~~~

제안 의도 문맥 (`docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_v4_critical_upgraded.md` 2846–2846행):

~~~~text
### 11.14.6 기존 Appendix A14→A15 재명명 + MIO 신규 appendix
~~~~

<a id="role-c5a99d504477c00a"></a>
## role-c5a99d504477c00a — T1. Signed curvature-coordinate domain theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 5–14행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `7f92b14a20fa131efdc4443e389349a0`

~~~~text
## T1. Signed curvature-coordinate domain theorem

**Statement.** \(\Omega_{k,{\rm aniso}}\)를 signed coordinate로 둘 때와 nonnegative magnitude로 둘 때, comparator \(x_C\), physical cone \(C_{\rm phys}\), endpoint decomposition의 필요충분 조건을 분류한다.

**Assumptions.** Registered congruence, fixed FLRW reference branch, explicit residual \(R_{\rm undeclared}\), declared curvature convention.

**Proof path.** Affine coordinate transformation과 cone image를 비교한다. signed case는 interval arithmetic, magnitude case는 non-linear absolute-value map 또는 split variables \(g_k^+,g_k^-\)로 처리한다.

**Numerical witness.** Random reference curvature를 뽑아 \(\Omega_k-\Omega_{k,ref}\)가 음수가 되는 예를 생성하고, 기존 nonnegative cone endpoint가 틀어지는 사례를 보여준다.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-97ffbd65abc8a965"></a>
## role-97ffbd65abc8a965 — T2. Component-cone sharpness versus GR-realizability theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 15–24행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `e9adc031681cc6b701292c4fd4cd6bf4`

~~~~text
## T2. Component-cone sharpness versus GR-realizability theorem

**Statement.** P31의 sharpness는 registered convex component model에서는 성립하지만, full Einstein constraint/evolution admissible set에서는 일반적으로 더 좁아질 수 있다.

**Assumptions.** Abstract box/cone admissible set \(C_{\rm box}\), physical solution admissible set \(C_{\rm GR}\subseteq C_{\rm box}\).

**Proof path.** Linear functional image inclusion: \(c^TC_{\rm GR}\subseteq c^TC_{\rm box}\). Equality requires a realization theorem for every endpoint. 이 조건을 별도 lemma로 둔다.

**Numerical witness.** Toy coupled constraint \(g_W\le a g_\Sigma\)를 추가하면 기존 interval이 sharp하지 않음을 보인다.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-af7d61b9223e159d"></a>
## role-af7d61b9223e159d — T3. Endpoint inference under active-set changes

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 25–34행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T3. Endpoint inference under active-set changes

**Statement.** Box/cone-constrained reachable estimator의 endpoint maps가 active-set 변화 지점에서 nonsmooth일 때, Gaussian endpoint CI 대신 directional bootstrap 또는 simulation calibration이 필요하다.

**Assumptions.** Local asymptotic normality, convex compact feasible set, endpoint map Hadamard directionally differentiable.

**Proof path.** Shapiro-style directional delta method. Smooth region에서는 IM critical value, kink에서는 bootstrap consistency 조건을 제시한다.

**Numerical witness.** True endpoint가 nonnegative boundary \(g_j=0\)에 있을 때 naive Gaussian endpoint CI가 왜곡되는 MC.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-e72a06362c26102c"></a>
## role-e72a06362c26102c — T4. Joint feasible ratio interval compatibility theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 35–44행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `1110b39c4126927b2022de12097d7c48`, `ced485eab54119209d866368ea32bc19`, `d6ae7e89194b99b3cfcc59fa7f6deb39`

~~~~text
## T4. Joint feasible ratio interval compatibility theorem

**Statement.** Joint ratio interval \(\{N(s)/D(s):s\in S\}\)가 naive quotient interval과 같아지는 필요충분 조건은 numerator와 denominator의 extremizers가 common feasible point에서 호환되는 것이다. Strict inclusion은 generic하지만 unconditional은 아니다.

**Assumptions.** Compact convex \(S\), affine \(N,D\), \(D>0\) on \(S\).

**Proof path.** Naive interval은 \(S\times S\), joint interval은 diagonal \(\{(s,s)\}\). Equality iff product-space extrema intersect diagonal.

**Numerical witness.** `scripts/run_all_experiments.py`의 \(N=2+s,D=5-s\) 반례.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-7b08208fb33137fa"></a>
## role-7b08208fb33137fa — T5. Prior-mediated null-direction update theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 45–54행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `341a4384df47f9bcd9dccaba595c5c85`

~~~~text
## T5. Prior-mediated null-direction update theorem

**Statement.** Likelihood가 null coordinate에 직접 의존하지 않으면 independent prior에서는 posterior marginal이 prior와 같고 KL=0이다. Coupled prior에서는 posterior marginal이 움직일 수 있지만, 그 update는 reachable coordinate와의 prior coupling을 통한 prior-mediated update로 분해된다.

**Assumptions.** Dominated Bayesian model, likelihood \(L(y|Rg)\), null column \(R_j=0\), prior conditional \(\pi(g_j|g_R)\).

**Proof path.** Posterior marginal \(p(g_j|y)=\int \pi(g_j|g_R)p(g_R|y)dg_R\). Independent case는 \(\pi(g_j)\). Coupled case는 likelihood update가 \(p(g_R|y)\)에만 직접 작용함을 보인다.

**Numerical witness.** Gaussian coupled prior KL 계산. 포함 코드에서 independent KL=0, coupled KL>0.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-a7860f17a42d01c5"></a>
## role-a7860f17a42d01c5 — T6. Estimated-covariance e-value calibration theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 55–64행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `0ee3d1d4bbcfdfd582efc527e8468b6e`

~~~~text
## T6. Estimated-covariance e-value calibration theorem

**Statement.** Whitening covariance가 finite simulation ensemble에서 추정될 때, Hartlap-corrected Gaussian route 또는 Sellentin–Heavens t route를 쓰지 않으면 nominal e-value/null calibration이 보수성 또는 size를 잃을 수 있다.

**Assumptions.** Wishart sample covariance, independent simulations, dimension \(m\), simulation count \(N_{sim}>m+2\).

**Proof path.** \(E[S^{-1}]=(N_{sim}-1)/(N_{sim}-m-2)C^{-1}\)에서 precision inflation을 보이고, corrected statistic의 expectation을 재계산한다.

**Numerical witness.** 포함 코드의 Hartlap experiment: \(N_{sim}=300,m=20\)에서 raw precision trace inflation \(\simeq1.076\), correction 후 \(\simeq1.001\).

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-f1977e327e2d3377"></a>
## role-f1977e327e2d3377 — T7. Predeclared finite-cover scan validity theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 65–74행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `e0108cf4bd5d31d29a72ad93b993d082`

~~~~text
## T7. Predeclared finite-cover scan validity theorem

**Statement.** Threshold/cell/window weights가 data-independent로 predeclared된 finite cover에서는 convex e-value merge가 arbitrary dependence에서도 e-value를 유지한다. Data-adaptive cover/weights는 별도 correction 없이는 보장되지 않는다.

**Assumptions.** \(E_0[E_k]\le1\), deterministic or predictable weights, finite \(K\).

**Proof path.** Linearity of expectation. Adaptive nonpredictable weight에 대한 counterexample를 appendix에 둔다.

**Numerical witness.** Common-factor dependent e-values와 post-hoc max-selected e-values 비교.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-9924acbc3185d19c"></a>
## role-9924acbc3185d19c — T8. Response-class quotient theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 75–84행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `1358f4893db83dd584ca541653da34b4`

~~~~text
## T8. Response-class quotient theorem

**Statement.** Whitened response rows/columns의 equivalence relation으로 legacy family labels를 quotient하면 현재 관측 support에서 구별 가능한 response classes만 남는다.

**Assumptions.** Registered feature map, nuisance-projected whitened response matrix, tolerance policy.

**Proof path.** Identifiability equivalence \(\theta\sim\theta'\iff R\theta=R\theta'\). Quotient parameter space의 Fisher rank가 identifiable dimension.

**Numerical witness.** Column duplication/row duplication examples. 포함 코드에서 column duplication은 rank 증가 없음, row duplication은 noise correlation \(\rho\)에 따라 Fisher factor \(2/(1+\rho)\).

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-000c930234f68e78"></a>
## role-000c930234f68e78 — T9. Data-promotion gate theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 85–94행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `0c0b6ffe972580ee5f485725472d5a92`

~~~~text
## T9. Data-promotion gate theorem

**Statement.** A diagnostic figure can be promoted to calibrated inference iff it has a registered observable vector, selection/window model, covariance/null ensemble, transfer response, predeclared statistic, and reproducible generator manifest.

**Assumptions.** Gate schema with monotone promotion rule.

**Proof path.** 이건 수학 정리보다는 software-contract theorem에 가깝다. Promotion predicate를 Boolean lattice로 정의하고, missing gate가 있으면 posterior/evidence claim이 type error임을 보인다.

**Numerical witness.** 현재 package sidecar 24개 모두 failed gates 때문에 diagnostic_only로 머무는 감사 스크립트.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-c76ec0bf89c0db3d"></a>
## role-c76ec0bf89c0db3d — T10. Transverse/spin-2 vorticity reopening theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 95–103행
- 내용 버전: `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `782fbb8751f5ee9e5980e58a34793da7`

~~~~text
## T10. Transverse/spin-2 vorticity reopening theorem

**Statement.** radial dyad response는 antisymmetric vorticity를 annihilate하지만, transverse screen/tensor 또는 spin-2 response basis가 충분한 rank 조건을 만족하면 vorticity-related sector가 row-space로 들어올 수 있다.

**Assumptions.** Screen basis completeness, noise whitening, nuisance projection, nonzero curl-sensitive template columns.

**Proof path.** Representation decomposition: radial scalar channel은 antisymmetric sector에 zero projection, transverse/spin-2 basis는 nonzero projection 가능. Rank condition을 necessary/sufficient로 제시.

**Numerical witness.** Toy response matrix rank 2에서 transverse/spin-2 rows 추가 시 rank 4가 되는 실험.
~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/critical_review/theorem_candidates.md` 1–5행):

~~~~text
# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem
~~~~

<a id="role-865dd5e8e067db8e"></a>
## role-865dd5e8e067db8e — T1. 부호 있는 널-박스에 대한 식별구간 (P26의 양측 일반화)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 7–31행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T1. 부호 있는 널-박스에 대한 식별구간 (P26의 양측 일반화)

**진술.**
```latex
\begin{theorem}[Signed-box partial-identification interval]
Let ${\cal G}(y)$ be the feasible set of \S3.3 with null columns of $R$,
${\cal C}_{\rm phys}=\{\bm g:\ g_\Sigma,g_W,g_t\ge0\}\times\R_{(k)}$, and
signed ceiling boxes $g_j\in[L_j,U_j]$ ($L_j\le0\le U_j$ allowed) on the
null components.  If ${\cal G}(y)\ne\emptyset$, the image
$\{c^T\bm g\}$ is the closed interval with endpoints
\[
x_C^\pm=\Bigl(\hbox{extremes of }c_R^T\bm g_R\Bigr)
+\sum_{j\in{\rm null}}
{\textstyle\bigl[\min(c_jL_j,c_jU_j),\ \max(c_jL_j,c_jU_j)\bigr]}^{\mp},
\]
and the one-sided case $L_j=0$ recovers P26.  In particular a two-sided
curvature box $|\Omega_{k,\rm aniso}|\le U_k$ moves the LOWER endpoint by
$-U_k$ relative to the one-sided declaration.
\end{theorem}
```
**증명 스케치.** P26과 동일: 볼록성 + 선형 함수 상 구간; 널 방향 인수분해; 박스 끝점에서의 극값은 \(c_j\) 부호에 따라 \(c_jL_j\) 또는 \(c_jU_j\). 새 내용은 부호 있는 박스의 min/max 정리(one-liner)뿐이므로 완결 증명 난이도는 낮다.
**난이도**: 하. **역할**: F1(치명 결함)의 수리 그 자체. **검증 훅**: exp02 (하한 0.11→0.09, 끝점 attainment 확인 완료).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-ba74640447b01832"></a>
## role-ba74640447b01832 — T2. Joint-대-naive 구간의 엄격성 판별 정리 (P36 교정)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 32–51행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `9b8b1af9bb69e8169952709951fcf29a`

~~~~text
## T2. Joint-대-naive 구간의 엄격성 판별 정리 (P36 교정)

**진술.**
```latex
\begin{theorem}[Strictness criterion for the joint depth-gap interval]
In the setting of P36 with box ${\cal S}=\prod_j[s_j^-,s_j^+]$ and $D>0$
on the feasible set, the joint and naive upper endpoints coincide iff the
set $\arg\max_{s}\,c_N\!\cdot\!s\ \cap\ \arg\min_{s}\,c_D\!\cdot\!s$ is
nonempty, which for a box holds iff $c_{N,j}\,c_{D,j}\le0$ for every $j$
with a nondegenerate interval (aligned regime).  Hence the inclusion of
P36 is strict at the upper endpoint iff some shared component competes,
$c_{N,j}c_{D,j}>0$ with $s_j^-<s_j^+$; the lower endpoint is analogous
with $\arg\min c_N\cdot s\cap\arg\max c_D\cdot s$.
\end{theorem}
```
**증명 스케치.** (⇐ 일치) 정렬 레짐이면 성분별로 \(c_{N,j}>0 \Rightarrow c_{D,j}\le 0\)이므로 \(s_j=s_j^+\)가 분자 최대·분모 최소를 동시에 달성(반대 부호도 대칭). 공통 최적점 \(s^\*\)에서 naive 상한 = joint 상한. (⇒ 엄격) 경쟁 성분 \(j\)가 있으면 naive는 분자에 \(s_j^+\), 분모에 \(s_j^-\)를 따로 쓰지만 joint는 하나의 \(s_j\)만 허용; 분수의 단조성으로 상한이 진성으로 작아짐. 박스 구조 덕에 argmax/argmin이 성분별로 분리된다는 사실만 쓰면 된다.
**난이도**: 하. **역할**: M1 수리; DER 등급 항목의 신뢰 회복. **검증 훅**: exp04 (정렬 레짐 등식 재현, 교정 기준 예측 일치 93/94 — 나머지 1건은 수치 허용오차 경계 사례).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-4c327ea816d036a1"></a>
## role-4c327ea816d036a1 — T3. 박스 극점의 제약-적합성 (P31 승격용 보조정리)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 52–72행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `ba1c07e1a8611bf59b26c7cc5cacf907`

~~~~text
## T3. 박스 극점의 제약-적합성 (P31 승격용 보조정리)

**진술.**
```latex
\begin{lemma}[Constraint compatibility of ceiling-box extremes]
Fix reachable values $(\Sigma^2,\Omega_t)$ with $w>-1$ and any null-box
values $(W^2,\Omega_k)$ with $x_C\le x_{\max}<1$.  Then there exists a
1+3 initial-data set (an LRS tilted-fluid configuration plus, if needed,
an antipodal kinetic stream pair) satisfying BOTH the Gauss constraint
\eqref{eq:parent} and the momentum constraint, with $\mu\ge0$,
$\Omega_\Lambda$ free of sign, and the weak energy condition on the
matter sector, whose normalized invariants realize the four prescribed
values.  Consequently the interval of T1 is sharp as a statement about
physically admissible configurations, not merely about the convex program.
\end{lemma}
```
**증명 스케치.** (1) Gauss: \(\Omega_m+\Omega_\Lambda=1-x_C>0\)로 예산 마감 — \(\Omega_m\ge0\) 선택 후 \(\Omega_\Lambda\) 부호 자유. (2) 운동량: LRS Bianchi V형 구성에서 \(2A\Sigma_+=(1+w)\Omega_m\beta\) (P5의 제약)가 shear–tilt 균형을 명시적으로 제공 — 임의의 \((\Sigma^2,\Omega_t,\Omega_k>0)\) 조합은 \((A,\beta,\Omega_m)\) 조절로 도달, \(\Omega_k<0\)쪽은 Kantowski–Sachs/Bianchi IX형 LRS 구성으로 동일 절차. (3) vorticity: LRS 회전 계열(예: tilted LRS class III) 또는 국소 kinetic 구성으로 \(W^2\) 주입 후, 유도되는 \(q_a\), \(\Pi_{ab}\)를 P11 스트림으로 흡수. (4) 에너지 조건은 작은-예산 영역(\(x_{\max}\ll1\))에서 열린 조건으로 성립. 주의: (3)이 실제 부담이며, 회전+틸트 LRS 제약대수의 명시적 해(Hewitt–Wainwright 계열)에 기대는 것이 최단 경로다. 완전 일반 증명이 무거우면 "각 극점의 실현 가능 분기 목록"으로 약화해도 P31 승격에는 충분하다.
**난이도**: 중~상 (프로그램 내 최대 가치). **역할**: M2 해소 — sharpness를 물리 명제로 승격. **검증 훅**: 신규 sympy seal 1개(제약 양변 대입 검증) 권장; P5 seal(exp12)이 부분 원형.

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-a9299e33f4ebb50f"></a>
## role-a9299e33f4ebb50f — T4. 추정 공분산 하 두-단계 커버리지 (P35의 유한-\(N_{\rm sim}\) 판)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 73–97행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T4. 추정 공분산 하 두-단계 커버리지 (P35의 유한-\(N_{\rm sim}\) 판)

**진술.**
```latex
\begin{theorem}[Two-stage coverage with simulation-estimated covariance]
Let $\widehat C_y$ be a Wishart covariance estimate from $N_{\rm sim}$
independent Gaussian simulations, $N_{\rm sim}>m+3$.  Replace the stage-1
and stage-2 thresholds by the Hotelling-type quantiles
\[
\tau_1'=\frac{(m-r)\,(N_{\rm sim}-1)}{N_{\rm sim}-(m-r)}\,
F_{m-r,\ N_{\rm sim}-(m-r),\ 1-\alpha_1},\qquad
\tau_2'\ \hbox{analogously with }r .
\]
Then statement (i) of P35 holds exactly at finite $N_{\rm sim}$; the
$\chi^2$ thresholds are recovered as $N_{\rm sim}\to\infty$; and the
uncorrected procedure has stage-1 size
$\alpha_1'=1-F_{m-r,N_{\rm sim}-(m-r)}\!\bigl(\tfrac{N_{\rm sim}-(m-r)}{(m-r)(N_{\rm sim}-1)}\chi^2_{m-r,1-\alpha_1}\bigr)>\alpha_1$,
quantifying the refutation-inflation of an uncorrected EMPTY verdict.
\end{theorem}
```
**증명 스케치.** 잔차 부분공간으로의 직교 사영 후 표준 Hotelling \(T^2\) 분포론: \(x^T\widehat C^{-1}x\)의 사영 성분은 \(T^2_{k,N-1} = \frac{k(N-1)}{N-k}F_{k,N-k}\). 사영들의 독립성(가우스 직교 사영)은 known-covariance 경우와 동일하게 성립하되, \(\widehat C\) 공유로 stage 1/2의 임계값 결합이 필요하면 Bonferroni로 처리(그대로 P35의 (i) 구조). IM 끝점 부분은 \(\widehat\sigma^\pm\)의 일치성만 요구하므로 asymptotic 문장은 유지.
**난이도**: 중 (표준 다변량 분포론). **역할**: M3 해소; K1 lane의 등록요건을 §3.4 본문 정리로 승격. **검증 훅**: exp11 (미보정 크기 0.072 재현; F-임계값 MC는 동일 코드 1줄 교체).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-9ab025238e4af52e"></a>
## role-9ab025238e4af52e — T5. 결정론적 폭 레짐에서 IM 구간의 정확(비점근) 커버리지

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 98–117행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `1911738ef1f06aa31300d2a941bc54f5`

~~~~text
## T5. 결정론적 폭 레짐에서 IM 구간의 정확(비점근) 커버리지

**진술.**
```latex
\begin{proposition}[Exact finite-sample IM coverage under deterministic width]
In the registered regime where both endpoint estimators share one
Gaussian reachable noise, $\widehat x^\pm = x^\pm + \varepsilon$,
$\varepsilon\sim{\cal N}(0,\sigma^2)$ with $\sigma$ known and
$\Delta=x^+-x^-$ DETERMINISTIC, the Imbens--Manski interval
$[\widehat x^--C_N\sigma,\ \widehat x^++C_N\sigma]$ has EXACT coverage
$\ge1-\alpha$ for every $\theta\in[x^-,x^+]$, with equality at the
endpoints; no asymptotics and no Stoye-type uniformity condition are
needed.
\end{proposition}
```
**증명 스케치.** 끝점 \(\theta=x^-\)에서 커버리지 = \(\Prob(-C_N\sigma\le\varepsilon\le C_N\sigma+\Delta)=\Phi(C_N+\Delta/\sigma)-\Phi(-C_N)=1-\alpha\) (IM 방정식 그 자체). 내부점은 단조성으로 \(\ge\). \(\Delta\) 추정 불확실성이 0이므로 Stoye 조건은 공허하게 성립. 이 관찰은 보고서가 이미 산문으로 언급한 것("the exact regime")의 정식화이며, 비용 없이 P35를 강화한다.
**난이도**: 하. **역할**: P35(iii)의 점근 문구를 정확 문장으로 승격 — 심사자 관점에서 가장 값싼 강화. **검증 훅**: exp03 (커버리지 0.9465 ≈ 0.95, Δ→0에서 0.953).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-4c6fd5b5b84d7f36"></a>
## role-4c6fd5b5b84d7f36 — T6. 횡속도 채널의 vorticity Fisher 하한 (P22의 정량판)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 118–141행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `c49e416df1615b068d67b7daf0acbb6c`

~~~~text
## T6. 횡속도 채널의 vorticity Fisher 하한 (P22의 정량판)

**진술.**
```latex
\begin{proposition}[Quantitative reopening of the vorticity sector]
Let the observable set add a transverse-velocity template
$t_a = P_{ab}\,\omega^{bc} n_c$ (screen projector $P_{ab}$) with white
noise level $\sigma_t$ over $N_{\rm src}$ sources of mean depth $\chi$.
Then the Fisher information for $W^2$ satisfies
\[
{\cal I}(W^2)\ \ge\ \frac{N_{\rm src}}{4\,\sigma_t^2}\,
\frac{(3H^2)\,\overline{\chi^2}\,\xi_{\rm geom}}{W^2},
\qquad \xi_{\rm geom}=\E\bigl[\|P\,\hat\omega\times n\|^2\bigr]>0
\]
for isotropic source distributions, with $\xi_{\rm geom}=2/3$ in the
full-sky limit.  Hence the structural null of P9 is broken at a
computable rate, not merely qualitatively.
\end{proposition}
```
**증명 스케치.** 횡속도 응답 \(v_\perp = \omega\times r\)의 스크린 사영 놈 기대값 계산(구면 평균 → \(2/3\)); 가우스 잡음 하 진폭 파라미터의 Fisher는 응답 제곱합/σ²; \(W^2 = \omega^2/(3H^2)\)로 변수 변환 시 야코비안 \(1/(2\sqrt{W^2}\cdot)\)에서 \(1/W^2\) 인자. full-sky 극한 상수는 exp07류 MC로 검증 가능.
**난이도**: 하~중. **역할**: P22를 "재개방 가능"에서 "얼마나 빨리 재개방되는가"로 승격 — K6 lane의 요구 데이터 양 산정 근거. **검증 훅**: 소형 MC 추가 (스크립트 1개, exp07 확장).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-8306412c3749551b"></a>
## role-8306412c3749551b — T7. 임의 의존 하 e-값 병합의 본질적 유일성 (문헌 이식)

- 역할: 기존 결과를 재사용한 기초·보조명제
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 142–149행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: T7은 원문이 “문헌 이식”이라고 명시하므로 표준/기존 결과 보조정리로만 분류한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T7. 임의 의존 하 e-값 병합의 본질적 유일성 (문헌 이식)

**진술.** Vovk–Wang의 정리를 프로그램 어휘로 이식: "임의 의존 e-값들에 대해 admissible한 대칭 병합 함수는 convex 결합(과 그 지배 함수)뿐이다." 따라서 P29의 convex 병합 선택은 임의가 아니라 **본질적으로 유일**하다.
**증명 스케치.** 문헌 정리 인용 + 프로그램의 finite-cover 세팅으로의 사상(셀 e-값의 교환 가능성 확인)만 필요. 새 증명 부담 없음.
**난이도**: 하 (이식). **역할**: P29 선택의 최적성 주장 — "왜 곱이 아니라 합인가"라는 표준 심사 질문의 선제 차단(독립 시에는 곱이 우월하나 의존 미지 시 합이 유일 admissible). **검증 훅**: exp05 (ρ=0.9 최대 의존에서 합 병합 유효 확인).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-db9982d7d61a57c0"></a>
## role-db9982d7d61a57c0 — T8. 사양검정의 검정력 단조성과 일치성 (E3의 정리판)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 150–169행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `bac9939dbd03f68b01e78b8609ef6a60`

~~~~text
## T8. 사양검정의 검정력 단조성과 일치성 (E3의 정리판)

**진술.**
```latex
\begin{proposition}[Monotone power of the stage-1 refutation test]
Under Gaussian noise the stage-1 statistic is noncentral
$\chi^2_{m-r}(\lambda)$ with $\lambda=\|P_\perp\mu_{\rm mis}\|^2$.  Its
rejection probability at any fixed threshold is strictly increasing in
$\lambda$ (MLR property of the noncentral $\chi^2$ family), equals
$\alpha_1$ at $\lambda=0$, and tends to $1$ as $\lambda\to\infty$.
Hence EMPTY-as-refutability is a consistent test against any
misspecification with a residual-space component, and is BLIND to
misspecification inside the reachable column space.
\end{proposition}
```
**증명 스케치.** 비중심 χ² 족의 단조우도비 성질(표준); \(\lambda\)의 정의에서 도달-공간 성분은 사영으로 소거 — 마지막 문장이 과학적으로 중요한 부분(반증력의 사각지대 명시).
**난이도**: 하. **역할**: E3 곡선을 정리로 승격 + "reachable-space 오설정은 EMPTY로 잡히지 않는다"는 한계의 정직한 명문화. **검증 훅**: exp03 검정력 곡선 (0.0518 → 1.000).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-8ed3bd0914680891"></a>
## role-8ed3bd0914680891 — T9. 다성분 틸트 예산의 정확 분해 (m1의 정리판)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 170–191행
- 내용 버전: `70d95410bce7756cff0ae09ecb6c8b12122abf40b0ca2d2da0e3dd4dce23ac78:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `e64050de0e5aa951b0508544f36f126e`

~~~~text
## T9. 다성분 틸트 예산의 정확 분해 (m1의 정리판)

**진술.**
```latex
\begin{proposition}[Exact multi-component tilt budget]
For $K$ non-interacting perfect-fluid components with equations of state
$w_i$ and rapidities $\beta_i$ relative to the normal frame,
\[
1=\sum_i\Omega_i+\Omega_\Lambda+\Omega_k+\Omt^{\rm tot}+\Sig-\Wsq,
\qquad
\Omt^{\rm tot}=\sum_i(1+w_i)\,\Omega_i\sinh^2\beta_i ,
\]
EXACTLY in every $\beta_i$; the boost-induced energy fluxes and
anisotropic stresses enter only the momentum constraint and the
evolution equations, not the Gauss budget.
\end{proposition}
```
**증명 스케치.** 성분별 \(T^{(i)}_{ab}n^an^b=\mu_i+(\mu_i+p_i)\sinh^2\beta_i\)의 합산(정확식, exp01의 단일 성분 계산과 동일); Gauss 제약은 총 \(T_{ab}n^an^b\)만 본다는 사실로 마감. CMB-물질 상대 틸트가 있는 시대(예: 재결합 전후)로 comparator를 확장할 때 필요한 정확한 형태.
**난이도**: 하. **역할**: m1 수리 + \(\Omega_{\rm tilt}\) 정의의 다성분 일반화 — Paper A의 완결성 요건. **검증 훅**: exp01 확장 1줄 (성분 합 잔차 0).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/03_theorem_candidates_ko.md` 1–5행):

~~~~text
# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---
~~~~

<a id="role-3c4443150307ed93"></a>
## role-3c4443150307ed93 — §1. T1′ — 부호 있는 널-박스 식별구간 (P26의 일반화; F1의 반전)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 7–29행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## §1. T1′ — 부호 있는 널-박스 식별구간 (P26의 일반화; F1의 반전)

**정리 T1′.** \(\mathcal{G}(y)\)를 §3.3의 feasible set이라 하자. 단, (i) \(R\)의 널 성분은 0-컬럼, (ii) \(\mathcal{C}_{\rm phys} = \{g_\Sigma, g_W, g_t \ge 0\} \times \mathbb{R}_{(k)}\), (iii) 각 널 성분 \(j\)는 선언된 부호 박스 \(g_j \in [L_j, U_j]\), \(L_j \le U_j\) (단측 선언은 \(L_j = 0\))를 갖는다. \(\mathcal{G}(y) \neq \emptyset\)이면 상 \(\{c^T \bm g : \bm g \in \mathcal{G}(y)\}\)는 닫힌구간 \([x_C^-, x_C^+]\)이고,

\[
x_C^{\pm} = \Bigl(\text{도달 타원체} \cap \text{콘 위 } c_R^T \bm g_R \text{의 극값}\Bigr) + \sum_{j \in \rm null} \bigl[\min(c_j L_j,\, c_j U_j),\ \max(c_j L_j,\, c_j U_j)\bigr]^{\mp}
\]

(윗첨자 \(\mp\): 하한에는 min-합, 상한에는 max-합). \(L_j = 0\)이면 P26으로 환원된다.

**증명.** (a) *구간성·닫힘*: \(\mathcal{G}(y)\)는 타원체 원기둥 ∩ 콘 ∩ 박스의 교집합으로 볼록·닫힘이고, 도달 슬라이스는 유계(타원체가 도달 좌표에서 유계), 널 박스는 콤팩트이므로 \(\mathcal{G}(y)\)는 콤팩트 볼록. 선형 함수의 콤팩트 볼록집합 상은 닫힌구간이다. (b) *분해*: 널 컬럼이 0이므로 데이터 misfit은 널 좌표에 의존하지 않고, 콘·박스 제약은 좌표 분리형이다. 따라서 \(\mathcal{G}(y) = \mathcal{G}_R(y) \times \prod_j [L_j, U_j]\)로 인수분해되고, \(\sup(A+B) = \sup A + \sup B\), \(\inf(A+B) = \inf A + \inf B\) (독립 좌표의 선형 결합)에 의해 극값이 성분별 합으로 분해된다. (c) *널 성분 극값*: 구간 \([L_j, U_j]\) 위에서 \(c_j g_j\)의 최소·최대는 \(\min(c_j L_j, c_j U_j)\), \(\max(c_j L_j, c_j U_j)\) — 이는 \(c_j\)와 \(L_j\)의 부호에 관계없이 성립한다. ∎

**따름정리 DL1 (분기-단조성).** 선언 박스 \([L_j, U_j] \subseteq [L_j', U_j']\)이면 \([x_C^-, x_C^+] \subseteq [x_C^{-\prime}, x_C^{+\prime}]\). 특히 open-branch(\(L_k = 0\)) 구간은 all-branch(\(L_k = -U_k\)) 구간에 포함되고, 하한 차는 정확히 \(|c_k| U_k\)이다.

**증명.** 박스 확대는 feasible set의 확대이므로 상의 확대. 하한 차는 T1′ 공식에서 \(\min(c_k L_k, c_k U_k)\)의 차로 즉시 계산된다. ∎

**따름정리 DL2 (분기-민감도 카드의 정당성).** 선언 분기가 서로 다른 두 구간은 모두 각자의 선언 하에서 sharp하므로, 두 구간을 병기하는 것(카드)은 보수화가 아니라 **선언의 가격을 정확히 인쇄하는 것**이다.

**[반전]** F1("비음수 가정이 닫힌형 곡률을 무언 배제")은 이제 이렇게 읽힌다: v6의 \([0.11, 0.17]\)은 open-branch 선언(\(L_k=0\))의 sharp 구간으로 **참**이고, all-branch 선언의 sharp 구간 \([0.09, 0.17]\)이 **추가**되었으며, 두 값의 차이는 DL1이 예측하는 정확한 양(\(U_k = 0.02\))이다. 적용 범위는 늘었고 철회된 것은 없다.
**[검증]** FORT01 자가시험: open \([0.1100, 0.1700]\), all \([0.0900, 0.1700]\), DL1 단조성 True, 상태대수 4분기(FEASIBLE/EMPTY/UNBOUNDED/CEILING_UNFIT) 전부 실행.

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-1df684ccd0112e30"></a>
## role-1df684ccd0112e30 — §2. T2′ — joint-대-naive 구간의 엄격성 판별 (P36의 강화; M1의 반전)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 30–44행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## §2. T2′ — joint-대-naive 구간의 엄격성 판별 (P36의 강화; M1의 반전)

**정리 T2′.** P36의 세팅(공유 널 성분 \(s \in \mathcal{S} = \prod_j [s_j^-, s_j^+]\), \(N(s) = n + c_N \cdot s\), \(D(s) = d + c_D \cdot s > 0\), \(n \in [n^-, n^+]\), \(d \in [d^-, d^+]\))에서:

(i) **포함**: joint 구간 ⊆ naive 구간 (항상).
(ii) **상한 등식 판별**: joint 상한 = naive 상한 \(\iff \arg\max_{s \in \mathcal{S}} c_N \cdot s \,\cap\, \arg\min_{s \in \mathcal{S}} c_D \cdot s \neq \emptyset\). 박스에서 이는 \(\forall j\) (비퇴화 구간): \(c_{N,j} c_{D,j} \le 0\)과 동치다.
(iii) **엄격성**: 따라서 상한에서 포함이 엄격 \(\iff \exists j:\ c_{N,j} c_{D,j} > 0\)이고 \(s_j^- < s_j^+\). 하한은 \(\arg\min c_N \cdot s \cap \arg\max c_D \cdot s\)로 대칭.

**증명.** (i) naive는 \((s_N, s_D) \in \mathcal{S} \times \mathcal{S}\) 위의 최적화, joint는 대각 \(\{(s,s)\}\) 위의 최적화 — 부분집합 위의 sup는 크지 않다. (ii, ⇐) 교집합에 \(s^\* \)가 있으면 naive 상한 \(= \frac{n^+ + c_N \cdot s^\*}{d^- + c_D \cdot s^\*}\)이 대각 원소 \((s^\*, s^\*)\)에서 달성되므로 joint 상한과 일치. (ii, ⇒) 박스에서 \(\arg\max c_N \cdot s\)는 \(\{s_j = s_j^+ \text{ if } c_{N,j} > 0;\ s_j^- \text{ if } c_{N,j} < 0;\ \text{임의 if } c_{N,j} = 0\}\)의 곱집합이고 \(\arg\min c_D \cdot s\)도 마찬가지. 두 곱집합의 교집합이 공집합 \(\iff\) 어떤 \(j\)에서 요구 꼭짓점이 상반 \(\iff c_{N,j} c_{D,j} > 0\) (비퇴화 \(j\)). 교집합이 공집합인 경우, naive 상한을 주는 어떤 \((s_N, s_D)\)도 \(s_N \neq s_D\)이며, 고정 \(s\)에 대해 \(\frac{n^+ + c_N \cdot s}{d^- + c_D \cdot s}\)는 경쟁 성분 \(j\)에서 \(s_j\)를 어느 쪽으로 움직여도 분자·분모가 같은 방향으로 움직여 진성 손실이 생긴다: 구체적으로 \(f(s) = \frac{a + c_N \cdot s}{b + c_D \cdot s}\)의 \(s_j\)-도함수는 \(\frac{c_{N,j}(b + c_D \cdot s) - c_{D,j}(a + c_N \cdot s)}{(b + c_D \cdot s)^2}\)로, naive가 요구하는 두 극값을 동시에 만족하는 \(s_j\)가 없으므로 \(\max_s f < \) naive 상한 (엄격). (iii)은 (ii)의 대우. ∎

**[반전]** M1의 반례(정렬 레짐 등식)는 이제 정리의 한 분기다. v6의 충분조건적 진술("항상 엄격")은 필요충분 판별로 대체되어 **원문보다 강한** 정리가 되었고, "joint 구성은 결코 naive보다 나쁘지 않으며 언제 정확히 이기는지 안다"는 완결적 주장으로 승격되었다.
**[검증]** FORT02: 유리수 정확 산술(허용오차 0) 371/371 판별 일치; 엄격 260건, 등식 111건; v6 문구에 대한 명시 반례 1건 보존.

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-23bc0ad168e0e8f7"></a>
## role-23bc0ad168e0e8f7 — §3. T4′ — 시뮬레이션-추정 공분산 하 두-단계 절차의 정확 크기 (M3의 반전)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 45–61행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## §3. T4′ — 시뮬레이션-추정 공분산 하 두-단계 절차의 정확 크기 (M3의 반전)

**정리 T4′.** \(\widehat{C}_y\)가 \(N_{\rm sim} > m + 3\)개의 독립 Gaussian 시뮬레이션의 표본공분산이고 데이터와 독립이라 하자. 잔차 부분공간(차원 \(k = m - r\))의 정규직교 기저 \(B\)에 대해 \(q = x_r^T (B^T \widehat{C}_y B)^{-1} x_r\), \(x_r = B^T x\)로 두면, 귀무(올바른 사양) 하에서

\[
\frac{N_{\rm sim} - k}{k (N_{\rm sim} - 1)}\, q \sim F_{k,\, N_{\rm sim} - k},
\]

이므로 임계값 \(\tau_1' = \frac{k (N_{\rm sim} - 1)}{N_{\rm sim} - k} F_{k, N_{\rm sim} - k, 1 - \alpha_1}\)를 쓰는 사양검정은 **유한 \(N_{\rm sim}\)에서 크기가 정확히 \(\alpha_1\)**이다. stage-2도 \(k \to r\)로 동일하며, \(N_{\rm sim} \to \infty\)에서 \(\chi^2\) 임계값으로 수렴한다. 미보정 \(\chi^2\) 임계값의 실제 크기는 \(\alpha_1' = 1 - F_{k, N_{\rm sim}-k}\bigl(\tfrac{N_{\rm sim}-k}{k(N_{\rm sim}-1)} \chi^2_{k, 1-\alpha_1}\bigr) > \alpha_1\)로 닫힌형 계산된다.

**증명.** \(x_r \sim \mathcal{N}(0, \Sigma_r)\), \((N_{\rm sim}-1) B^T \widehat{C}_y B \sim \mathcal{W}_k(\Sigma_r, N_{\rm sim}-1)\)이고 서로 독립이므로 \(q\)는 자유도 \((k, N_{\rm sim}-1)\)의 Hotelling \(T^2\) — 그 분포는 정의에 의해 \(\frac{k(N_{\rm sim}-1)}{N_{\rm sim}-k} F_{k, N_{\rm sim}-k}\)이고 \(\Sigma_r\)에 무관(피벗). 잔차·도달 사영의 독립성은 Gaussian 직교 사영에서 그대로 성립한다. 수렴과 미보정 크기 식은 \(F\)-분포의 극한과 단조성에서 즉시. ∎

**[반전]** M3("χ² 임계값은 추정 공분산에서 부정확, EMPTY가 과대")는 "**F-임계값 두-단계는 유한 \(N_{\rm sim}\)에서 정확하며, 따라서 EMPTY(반증) 판정은 추정 공분산 하에서도 유효한 주장**"으로 대체된다. v6의 등록요건(M5′, percent-level 언급)보다 강한 결론이고, Hartlap은 평균 보정일 뿐 꼬리는 F가 정답이라는 위계도 확정된다.
**[검증]** FORT03 (\(m=10, k=8, N_{\rm sim}=300\), 6000 MC): 미보정 크기 0.0665, F-임계값 0.0555 ± 0.0028 (명목 0.05와 2σ 이내), 검정력 손실 ≤ 3%p.

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-57696bddacdd3dc1"></a>
## role-57696bddacdd3dc1 — §4. T5′ — 결정론적 폭 레짐에서 IM 구간의 정확 유한표본 커버리지 (P35 강화)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 62–72행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## §4. T5′ — 결정론적 폭 레짐에서 IM 구간의 정확 유한표본 커버리지 (P35 강화)

**정리 T5′.** 두 끝점 추정량이 하나의 Gaussian 도달 잡음을 공유하고(\(\widehat{x}^{\pm} = x^{\pm} + \varepsilon\), \(\varepsilon \sim \mathcal{N}(0, \sigma^2)\), \(\sigma\) 기지), 폭 \(\Delta = x^+ - x^-\)가 결정론적(널-박스 폭)이라 하자. IM 방정식 \(\Phi(C_N + \Delta/\sigma) - \Phi(-C_N) = 1 - \alpha\)의 해 \(C_N\)에 대해 구간 \([\widehat{x}^- - C_N \sigma,\ \widehat{x}^+ + C_N \sigma]\)는 **모든** \(\theta \in [x^-, x^+]\)에 대해 유한표본 커버리지 \(\ge 1 - \alpha\)를 가지며 끝점에서 등호가 성립한다. 점근 논법도 Stoye형 균일성 조건도 불필요하다.

**증명.** \(\theta = x^- + t\), \(t \in [0, \Delta]\)에 대해 커버리지 사건은 \(\{\widehat{x}^- - C\sigma \le \theta \le \widehat{x}^+ + C\sigma\} = \{-C\sigma - (\Delta - t) \le \varepsilon \le C\sigma + t\}\)... 정확히는 \(\theta \ge \widehat{x}^- - C\sigma \iff \varepsilon \le t + C\sigma\), \(\theta \le \widehat{x}^+ + C\sigma \iff \varepsilon \ge t - \Delta - C\sigma\). 확률 \(= \Phi(C + t/\sigma) - \Phi(-C - (\Delta - t)/\sigma)\). 이 함수는 \(t = 0\)과 \(t = \Delta\)에서 같은 값 \(\Phi(C + \Delta/\sigma) - \Phi(-C)\)을 갖고(대칭), 도함수 \(\frac{1}{\sigma}[\varphi(C + t/\sigma) - \varphi(C + (\Delta - t)/\sigma)]\)의 부호가 \(t < \Delta/2\)에서 양, \(t > \Delta/2\)에서 음이므로(\(\varphi\)는 \([0,\infty)\)에서 감소) 단봉이며 최솟값은 끝점에서 달성된다. 끝점 값은 IM 방정식에 의해 정확히 \(1 - \alpha\). ∎

**[반전]** P35(iii)의 "asymptotic" 문구가 "exact"로 승격된다 — 비용 0의 강화.
**[검증]** exp03: IM 커버리지 0.9465 (N=4000, 명목 0.95, SE 0.0034); \(\Delta \to 0\)에서 0.953.

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-77aea85b91faac39"></a>
## role-77aea85b91faac39 — §5. T8′ — 사양검정 검정력의 단조성·일치성과 사각지대 (E3의 정리화)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 73–83행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: `46b8ed7852051e06db417d53c8c0b175`

~~~~text
## §5. T8′ — 사양검정 검정력의 단조성·일치성과 사각지대 (E3의 정리화)

**정리 T8′.** Gaussian 잡음에서 stage-1 통계는 비중심 \(\chi^2_{m-r}(\lambda)\), \(\lambda = \|P_\perp \mu_{\rm mis}\|^2\)이다. 고정 임계값에 대한 기각확률은 \(\lambda\)에 강단조 증가(비중심 \(\chi^2\) 족의 MLR 성질), \(\lambda = 0\)에서 \(\alpha_1\), \(\lambda \to \infty\)에서 1이다. 즉 EMPTY-as-refutability는 잔차 성분을 갖는 **모든** 오설정에 대해 일치(consistent) 검정이며, 도달 열공간 내부의 오설정(\(P_\perp \mu_{\rm mis} = 0\))에는 원리적으로 무감하다.

**증명.** 비중심 \(\chi^2\)의 밀도비가 \(\lambda\)에 대해 단조우도비임은 표준 사실(베셀 급수 표현에서 즉시). 기각확률의 극한은 비중심 모수 발산에서 자명. 사각지대 문장은 \(\lambda\)의 정의 그 자체다. ∎

**[반전]** E3의 "rising to 1.00"이 정리가 되고, 동시에 반증력의 한계(도달-공간 오설정)가 정직하게 명문화되어 "우리는 무엇을 반증할 수 없는지도 증명했다"는 프로그램 어법이 완성된다.
**[검증]** exp03 검정력 곡선 (0.0518 → 1.000, 단조).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-ecea2c58cade1809"></a>
## role-ecea2c58cade1809 — §6. T9′ — 다성분 틸트 예산의 정확 분해 (m1의 정리화)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 84–102행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: `1a8383a15dfd45ce7da73833cf5435e7`

~~~~text
## §6. T9′ — 다성분 틸트 예산의 정확 분해 (m1의 정리화)

**정리 T9′.** 상호작용 없는 \(K\)개 완전유체(상태방정식 \(w_i\), 정규 프레임 대비 rapidity \(\beta_i\))에 대해

\[
1 = \sum_i \Omega_i + \Omega_\Lambda + \Omega_k + \Omega_{\rm tilt}^{\rm tot} + \Sigma^2 - W^2, \qquad \Omega_{\rm tilt}^{\rm tot} = \sum_i (1 + w_i)\, \Omega_i \sinh^2 \beta_i,
\]

이 항등식은 모든 \(\beta_i\)에서 **정확**하다. 부스트 유도 에너지플럭스 \(q_a^{(i)} = (\mu_i + p_i) \sinh\beta_i \cosh\beta_i\, e_a^{(i)}\)와 비등방응력은 Gauss 예산이 아니라 운동량 제약·진화 방정식에만 들어간다.

**증명.** 성분별로 \(T^{(i)}_{ab} n^a n^b = (\mu_i + p_i) \cosh^2\beta_i - p_i = \mu_i + (\mu_i + p_i) \sinh^2\beta_i\) (정확식; \(u^{(i)} \cdot n = -\cosh\beta_i\)). Gauss 제약은 총 \(T_{ab} n^a n^b = \sum_i T^{(i)}_{ab} n^a n^b\)만 포함하므로 합산 후 \(3H^2\)로 나누면 진술식. 플럭스·응력은 \(T_{ab} n^a h^b{}_c\), \(T_{\langle ab \rangle}\) 성분으로 Gauss(시간-시간 성분)에 나타나지 않는다. ∎

**따름정리.** 반대 방향 틸트 쌍(\(\beta, -\beta\), 동일 \(w, \Omega\))은 \(q\)를 상쇄하면서 \(\Omega_{\rm tilt}^{\rm tot}\)에는 가산 기여한다 — T3(실현 정리)의 핵심 구성 요소.

**[반전]** m1("O(sinh²β)는 과소 진술")이 다성분 정확 정리로 승격되어, 복사+물질 시대(재결합 전후)로 comparator를 확장하는 Paper A의 완결성 요건을 충족한다.
**[검증]** exp01 (단일 성분 정확성; 다성분은 합산의 선형성으로 자명).

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-d5077977ee82eac0"></a>
## role-d5077977ee82eac0 — §7. T3-lin — 선형화 실현 정리 (P31 승격의 중간 단계; M2 대응) — 증명 스케치 + 잔여 보조정리

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 103–112행
- 내용 버전: `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 강화안에서 기존 결과를 더 강한 진술로 대체할 구체적인 정리·잔여 증명 목표를 제시한다. 원문의 완전 증명 표기는 별도 대조 대상이다.
- 연결 항목: `bcfb6eecfb18be2a191ed524b1859af8`

~~~~text
## §7. T3-lin — 선형화 실현 정리 (P31 승격의 중간 단계; M2 대응) — 증명 스케치 + 잔여 보조정리

**명제 T3-lin (등록 목표).** \(x_{\max} \ll 1\)인 임의의 목표 \((\Sigma^2_\*, W^2_\*, \Omega_{t\*}, \Omega_{k\*})\) (부호 박스·콘 준수)에 대해, FLRW 배경 위 선형화 초기데이터와 물질 배치가 존재하여 (i) Gauss·운동량 제약을 선형 차수에서 만족하고, (ii) 정규화 불변량이 목표값을 재현하며, (iii) 물질 부문이 약에너지조건을 만족한다. 따라서 T1′ 구간의 sharpness는 선형화 레짐에서 물리 명제다.

**증명 스케치.** (1) \(\Sigma^2_\*\): Bianchi I형 균질 전단 모드 — 운동량 제약이 자동 충족(대각 전단, \(q = 0\)). (2) \(\Omega_{k\*}\): FLRW 곡률 분기 혼합(등방 성분)과 Bianchi V/IX형 균질 곡률 모드; open/closed 부호 모두. (3) \(\Omega_{t\*}\): T9′ 따름정리의 반대-틸트 쌍 — 순 플럭스 0으로 운동량 제약 무부담. (4) \(W^2_\*\): 선형 벡터(회전) 모드 — 운동량 제약이 \(\nabla^2\)-역으로 \(q_{\rm vec}\)를 결정하며, 이는 (3)의 쌍에 소량의 비대칭 틸트를 얹어 공급; 진폭 자유. (5) 에너지조건: 모든 모드 진폭이 \(O(\sqrt{x_{\max}})\)이므로 배경 \(\mu > 0\)에 대한 선형 교란으로 유지. **잔여 보조정리 (등록 필요):** (4)에서 벡터 모드의 \(\omega\)와 (1)의 \(\sigma\)가 2차 결합 없이 목표 4-튜플을 독립 조준할 수 있음 — 선형 차수에서는 모드 중첩의 선형성으로 성립하나, "congruence 선택(정규 vs 물질 프레임)의 규약 고정" 문장을 정확히 써야 한다. 완전판(비선형, King–Ellis 틸트 Bianchi V 불변량 사상)은 WBS-C1.

**[반전]** M2("sharpness는 물리 명제로 미증명")는 "선형화 레짐(comparator의 실사용 영역 전체)에서 증명, 비선형 완전판은 등록된 정리 후보"로 재배치된다 — 갭의 인정이 아니라 정리 사다리의 명시.

---

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md` 1–3행):

~~~~text
# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.
~~~~

<a id="role-ee7999df52c88418"></a>
## role-ee7999df52c88418 — T1. Constraint-derived uniqueness of the signed comparator

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 5–24행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T1. Constraint-derived uniqueness of the signed comparator

**Statement.** Fix signature (-,+,+,+), congruence n^a, H=Θ/3, and registered dimensionless components

\[
\Sigma^2=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},\quad
W^2=\frac{\omega_{ab}\omega^{ab}}{6H^2},\quad
\Omega_{\rm tilt}=(1+w)\Omega_m\sinh^2\beta,
\]

with curvature component \(\Omega_{k,\rm aniso}=\Omega_k-\Omega_{k,\rm ref}\). Among linear dimensionless comparators that read off the non-FLRW contribution to the Gauss constraint while assigning zero to the FLRW reference branch, the coefficient vector is uniquely

\[
c=(1,-1,1,1).
\]

**Proof route.** Divide the 1+3 Gauss constraint by \(3H^2\), match normalized shear/vorticity terms, introduce tilted-frame energy excess, and subtract the registered FLRW reference. Uniqueness follows because the four registered components form an independent coordinate basis in the comparator layer.

**Potential obstruction.** If \(\Omega_{k,\rm aniso}\) is allowed to be signed, the “component magnitude cone” must be replaced by a signed affine coordinate. The theorem must explicitly choose one convention.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-b9902c3443c8cbae"></a>
## role-b9902c3443c8cbae — T2. Local constrained-data sharpness theorem for P31

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 25–34행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `a15729374d15baecfaa2004ab5d2826a`

~~~~text
## T2. Local constrained-data sharpness theorem for P31

**Statement.** Let \(g\) be sufficiently small in the registered HTT component cone and let the branch specify an equation of state and energy-condition domain. Under nondegeneracy of the York/conformal constraint operator, each endpoint of the P26 identified interval is realized by a local CMC initial-data family whose first-jet invariants match the endpoint components up to controlled \(O(\|g\|^2)\) residual; after conformal correction the Hamiltonian and momentum residuals vanish to solver tolerance.

**Proof route.** Start with local nearly-FLRW initial data, add transverse-traceless shear, stream-realized tilt stress, and small anisotropic curvature perturbations. Check first-order constraints. Apply implicit-function/conformal method to correct residuals. Use continuous dependence to preserve the comparator endpoint value up to controlled error.

**Numerical witness.** Implement `constraint_realization_endpoint_solver.py`: sweep eps, solve correction, report residual norms and convergence slopes.

**Why this strengthens the paper.** It turns “sharp over an abstract cone” into “sharp over an explicit physically realizable local-data class.”

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-003903a09bc241a0"></a>
## role-003903a09bc241a0 — T3. Exact equality conditions for P36 joint depth-gap intervals

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 35–42행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T3. Exact equality conditions for P36 joint depth-gap intervals

**Statement.** Let \(S\) be a compact polytope and \(N(s)=n+c_N\cdot s\), \(D(s)=d+c_D\cdot s>0\). The joint feasible interval for \(G_F=N/D\) is the exact image of the diagonal feasible set and is always contained in the marginal quotient interval. Equality of the lower endpoint holds iff the numerator-minimizing feasible face and denominator-maximizing feasible face contain a common point satisfying the linear-fractional lower optimum. Equality of the upper endpoint holds iff the numerator-maximizing feasible face and denominator-minimizing feasible face contain a common point satisfying the upper optimum. Outside these compatibility conditions, inclusion is strict. For generic coefficient vectors, equality conditions define a lower-dimensional algebraic/face-incidence set.

**Proof route.** Use Charnes-Cooper transform or quasiconvex/quasiconcave linear-fractional optimization on polytopes. Marginal quotient optimizes over \(S\times S\), joint over diagonal \(\Delta(S)\). Strictness reduces to whether product-space extremizers intersect the diagonal.

**Numerical witness.** Included in `scripts/strengthening_core.py`; strictness is generic in random coefficient draws, while the critique equality case is reproduced exactly.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-f6399f090540f95a"></a>
## role-f6399f090540f95a — T4. Known-covariance two-stage identified-set coverage

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 43–50행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T4. Known-covariance two-stage identified-set coverage

**Statement.** Under Gaussian whitened noise with fixed response matrix R, the residual projection statistic is \(\chi^2_{m-r}\) and independent of the reachable projection. Stage-1 EMPTY controls specification-test false rejection at \(\alpha_1\). Conditional stage-2 ellipsoid covers the reachable projection at \(1-\alpha_2\). For scalar \(x_C\) inside an interval-identified set, Imbens-Manski critical values give pointwise parameter coverage; two-sided endpoint/projection intervals give simultaneous identified-set coverage.

**Proof route.** Orthogonal projection of Gaussian vector into column space and residual space; then standard partial-identification endpoint logic.

**Numerical witness.** Included: residual EMPTY rate at zero shift is 0.04868 for \(\alpha_1=0.05\); power rises with residual shifts.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-57a3c3d765388607"></a>
## role-57a3c3d765388607 — T5. Estimated-covariance robust endpoint coverage

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 51–58행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T5. Estimated-covariance robust endpoint coverage

**Statement.** If covariance is estimated from \(N_{\rm sim}\) Gaussian simulations, the inverse sample covariance is biased. Using uncorrected Gaussian plug-in precision inflates reachable-sector precision. Hartlap correction removes first-order precision bias; Sellentin-Heavens covariance marginalization replaces the Gaussian likelihood by a multivariate-t form and propagates covariance uncertainty. Endpoint intervals must condition on this policy.

**Proof route.** Wishart expectation of inverse covariance; compare plug-in, Hartlap-corrected, and covariance-marginalized likelihood.

**Numerical witness.** Included: for p=20, raw precision trace ratio is ~1.075 at Nsim=300 and ~1.036 at Nsim=600; Hartlap-corrected mean is ~1.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-8ec6cab279698714"></a>
## role-8ec6cab279698714 — T6. Prior-exposure decomposition theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 59–66행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `1823398a92948e658dccbdb1b3373540`

~~~~text
## T6. Prior-exposure decomposition theorem

**Statement.** If likelihood depends on g only through Rg and column j of R is zero, then an independent prior leaves the posterior marginal of \(g_j\) equal to the prior exactly. If prior couples \(g_j\) to reachable coordinates, posterior movement of \(g_j\) is mediated entirely by the prior coupling and must be labelled prior-exposed.

**Proof route.** Factorization of posterior density; KL divergence of identical prior/posterior marginal is zero.

**Numerical witness.** Included in response-rank/prior exposure script.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-3d8178be2fa52eb4"></a>
## role-3d8178be2fa52eb4 — T7. Finite-cover dependent e-value merger theorem for K1/K5 scans

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 67–74행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `87493ec4ed694f3365a1d57497ec2bc9`

~~~~text
## T7. Finite-cover dependent e-value merger theorem for K1/K5 scans

**Statement.** For e-values \(E_k\) satisfying \(E_0 E_k\le 1\) under a common null, any convex weighted average is an e-value under arbitrary dependence. If sequential e-values satisfy \(E_0[E_t\mid\mathcal F_{t-1}]\le 1\), the product process is a nonnegative supermartingale and Ville control is anytime-valid.

**Proof route.** Linearity of expectation for finite cover; supermartingale property and Ville inequality.

**Numerical witness.** Included: dependent average e-value mean is ~0.997 and 200-step Ville crossing is 0.0397 for β=0.05.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-a961420736a6ae59"></a>
## role-a961420736a6ae59 — T8. Scalar/BiPoSH non-equivalence theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 75–82행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `960450a8d9aad912f086076b940b859d`

~~~~text
## T8. Scalar/BiPoSH non-equivalence theorem

**Statement.** Diagonal \(C_\ell\)-style compression annihilates off-diagonal \(L>0\) covariance morphology. Therefore scalar low-ell statistics and BiPoSH covariance statistics are non-equivalent projections; agreement or disagreement between them is a diagnostic pattern, not a geometry label.

**Proof route.** Schur orthogonality and rotational decomposition of covariance into BiPoSH coefficients.

**Data witness.** K1 map-stability matrix must report scalar and BiPoSH channels side by side with separate nulls.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-629bfb4bf59ad05b"></a>
## role-629bfb4bf59ad05b — T9. Transverse/spin-2 reopening theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 83–90행
- 내용 버전: `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; 관찰 커밋: `373941f2768511cdb3612c1e5b450d4da22a486b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `4349b4614dbf4909034d07f4d7b93f8c`

~~~~text
## T9. Transverse/spin-2 reopening theorem

**Statement.** Radial contractions annihilate antisymmetric vorticity contributions, but transverse velocity and spin-2 response tensors need not. Adding such channels can increase response rank and reopen sectors that are structural nulls for scalar/radial channels.

**Proof route.** Tensor symmetry: \(n^a\Omega_{ab}n^b=0\), while screen-space and spin-2 tensors are not equivalent to the radial dyad.

**Numerical witness.** Toy rank certificates: scalar/radial rank 2, enlarged transverse/spin-2 rank 4.

~~~~

제안 의도 문맥 (`docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md` 1–3행):

~~~~text
# 추가로 증명 가능한 정리 후보들

아래 정리들은 “claim을 낮추는” 게 아니라, 심사위원이 공격한 지점을 더 강한 수학 명제로 바꾸는 후보들이다.
~~~~

<a id="role-e4b260081c8a7d5e"></a>
## role-e4b260081c8a7d5e — S0 — EGS fixed-point semantics

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 5–5행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
1. **S0 — EGS fixed-point semantics.** Matched FLRW fixed point에서 \(x=F=0\), \(\Pi(q>0)=0\), \(G\)는 \(0/0\)이므로 undefined다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-d9e55ff54126cec1"></a>
## role-d9e55ff54126cec1 — S1 — angular relative-entropy multipole theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 6–6행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
2. **S1 — angular relative-entropy multipole theorem.** \(\epsilon_\ell\le(2\ell+1)\sqrt{D_{\rm KL}/(2\pi)}\).
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-2704b6f24d18dbee"></a>
## role-2704b6f24d18dbee — S2 — information-to-MES transduction

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 7–7행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
3. **S2 — information-to-MES transduction.** explicit bridge \(M_\ell\)과 derivative budget 아래 KL cap이 shear/vorticity/acceleration ceiling을 준다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-ef736581dca76002"></a>
## role-ef736581dca76002 — S3 — dynamic budget barrier

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 8–8행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
4. **S3 — dynamic budget barrier.** 같은 comparison operator와 source envelope를 갖는 \(X,U\)에 대해 \(X_0\le U_0\Rightarrow0\le F=X/U\le1\); margin과 \(\dot F\)의 explicit bound가 있다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-8c1fbf170ae84f59"></a>
## role-8c1fbf170ae84f59 — S4 — certified \(\Pi\) domination

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 9–9행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
5. **S4 — certified \(\Pi\) domination.** \(X\le B\) a.s.이면 \(P(X>q)\le P(B>q)\) for all \(q\).
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-3b29fc2cffbb5812"></a>
## role-3b29fc2cffbb5812 — S5 — finite-cover Copernican extension

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 10–10행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
6. **S5 — finite-cover Copernican extension.** Lipschitz \(D\)와 \(r\)-net sample에 대해 \(\sup D\le\max_iD_i+Lr\).
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-dc83d80ad7ea5b68"></a>
## role-dc83d80ad7ea5b68 — G1 — local Liouville isotropy rigidity

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 14–14행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
7. **G1 — local Liouville isotropy rigidity.** isotropic thermal massless distribution이 collisionless Liouville equation을 만족하면 \(\dot{\ln T}+H=0\), \(A_a+D_a\ln T=0\), \(\sigma_{ab}=0\).
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-5832d294cc13bde3"></a>
## role-5832d294cc13bde3 — G2 — two-frame thermal rigidity

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 15–15행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
8. **G2 — two-frame thermal rigidity.** nonconstant thermal radiation은 서로 다른 두 timelike frame에서 exact isotropy일 수 없다. Boosted isotropic radiation moments는 exact one-dimensional stress orbit를 이룬다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-adc6a1bcf36de1d4"></a>
## role-adc6a1bcf36de1d4 — G3 — Raychaudhuri–Hamiltonian consistency

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 16–16행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
9. **G3 — Raychaudhuri–Hamiltonian consistency.** \(\Delta q=2x+\frac32(w-1)\Omega_{\rm tilt}-2\Omega_{k,\rm aniso}+\Delta q_A\); \(w\neq1\)에서 tilt inversion, \(w=1\)에서 exact degeneracy.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-0b9d662b37fd1d39"></a>
## role-0b9d662b37fd1d39 — G4 — Bianchi-I filling-odds flow

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 17–17행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
10. **G4 — Bianchi-I filling-odds flow.** \(\operatorname{logit}F_{\sigma|m}=\operatorname{logit}F_0+3(1-w)\ln(1+z)\).
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-f595d458c3acd6b9"></a>
## role-f595d458c3acd6b9 — G5 — depth-slope degeneracy

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 18–18행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
11. **G5 — depth-slope degeneracy.** local/global degeneracy at \(w=0\), local/shear at \(w=1/3\), global/shear at \(w=-1/3\).
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-611a9a7c03082522"></a>
## role-611a9a7c03082522 — G6 — Weyl-completeness obstruction

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 19–19행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
12. **G6 — Weyl-completeness obstruction.** amplitude-only near-isotropy does not universally imply small normalized Weyl curvature.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-11903f505fdd694d"></a>
## role-11903f505fdd694d — B1 — coercive Boltzmann memory

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 23–23행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
13. **B1 — coercive Boltzmann memory.** anisotropic state norm is an integrating-factor memory of geometric forcing plus nuisance.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-7cce0a1e86175dce"></a>
## role-7cce0a1e86175dce — B2 — source-rank inverse almost-EGS

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 24–24행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
14. **B2 — source-rank inverse almost-EGS.** positive source minimum singular value converts \((h,\dot h)\) and nuisance bounds into a kinematic bound; zero rank is no-claim.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-9896e3eec39de8c4"></a>
## role-9896e3eec39de8c4 — B3 — tight-coupling tracking

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 25–25행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
15. **B3 — tight-coupling tracking.** \(Q'+\kappa Q=c_\sigma\sigma\)에서 quasi-static error와 shear inversion error가 explicit memory envelope로 제어된다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-0d37836a94a9c45b"></a>
## role-0d37836a94a9c45b — B4 — visibility rigidity/no-go

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 26–26행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
16. **B4 — visibility rigidity/no-go.** positive kernel와 sign-coherent source이면 inverse LOS bound가 가능하고, sign-changing source이면 일반적으로 불가능하다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-5f1566de3063c8c0"></a>
## role-5f1566de3063c8c0 — E1 — remote-observer statistical almost-EGS

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/12_consolidated_theorem_statements.md` 30–30행
- 내용 버전: `fad00fd7e6f460755698883fa3479cd274bd0de9c26cd23a0b9b07e773f9e53e:d283db23`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: MES/EGS 확장 연구프로그램이 S/G/B/E 축의 정리 목표로 정리한 구체적 진술이다. 기존 문헌 명제와의 차이는 학술 신규성 미검증으로 남긴다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
17. **E1 — remote-observer statistical almost-EGS.** remote angular information/derivative/Weyl diagnostics의 physical finite cover와 calibrated MES/Boltzmann bridge가 있으면 regional kinematic fillings와 conservative \(\Pi\) certificate가 구성된다.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip!/htt_beyond_mes_egs_theorem_program_2026-06-19/docs/00_scope_and_nonduplication.md` 1–15행):

~~~~text
# 범위, 권위, 중복배제 ledger

## 1. 목적

이 문서는 기존 연구의 beyond-MES bound와 \((x,Q,\Pi,F,G)\) formalism을 1+3 GR 및 Boltzmann equation에 직접 적용해 얻는 **새 정리군**만을 정리한다. Teff/TSC는 legacy이므로 theorem source나 active architecture로 사용하지 않는다.

기본 convention은 다음과 같다.

- metric signature: \((- + + +)\);
- \(u^a u_a=-1\), \(h_{ab}=g_{ab}+u_a u_b\);
- \(H=\Theta/3\);
- 자연단위는 선언하지 않으며 \(c\)는 속도/boost 정의에서 유지한다;
- 모든 \(F\)는 numerator와 denominator가 같은 physical sector에 속하는 경우에만 filling fraction으로 부른다;
- \(G\)는 \(F\)의 depth/time evolution이며 exact isotropy에서 \(0/0\)이므로 `undefined_at_fixed_point` status를 갖는다.

~~~~

<a id="role-229717dd6ca7353f"></a>
## role-229717dd6ca7353f — T1. Nuisance-projected local identifiability theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 7–55행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `ece59d46aa73b2e37b2e5ca2e54616fd`

~~~~text
## T1. Nuisance-projected local identifiability theorem

### Statement

Let

\[
\mathbf y=R_t\theta+R_n\eta+\epsilon,
\qquad
\epsilon\sim\mathcal N(0,C),
\]

with positive-definite \(C\). Define whitened responses

\[
\widetilde R_t=C^{-1/2}R_t,
\qquad
\widetilde R_n=C^{-1/2}R_n,
\]

and let \(P_n^\perp\) be the orthogonal projector onto the complement of \(\operatorname{col}(\widetilde R_n)\). Then \(\theta\) is locally identifiable modulo \(\eta\) if and only if

\[
\operatorname{rank}(P_n^\perp\widetilde R_t)=\dim\theta.
\]

### Proof

Two target parameter perturbations \(\delta\theta_1,\delta\theta_2\) are observationally equivalent modulo nuisance changes if

\[
\widetilde R_t(\delta\theta_1-\delta\theta_2)
\in\operatorname{col}(\widetilde R_n).
\]

Projecting with \(P_n^\perp\) gives

\[
P_n^\perp\widetilde R_t(\delta\theta_1-\delta\theta_2)=0.
\]

Uniqueness of \(\theta\) modulo nuisance therefore holds exactly when the null space of \(P_n^\perp\widetilde R_t\) is trivial, equivalent to full column rank. ∎

### Consequence

If the smallest singular value vanishes, no prior or sampler can create data identifiability. Posterior concentration then comes from prior structure or nonlinear boundaries.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-a66c842a23c92854"></a>
## role-a66c842a23c92854 — T2. Single-response local/global no-go corollary

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 56–69행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `de4937e4f007ad69d03e35d38ca43542`

~~~~text
## T2. Single-response local/global no-go corollary

If local and global amplitudes enter a dataset through proportional response vectors,

\[
R_{\rm glob}=\lambda R_{\rm loc},
\]

then a single amplitude-only dataset cannot distinguish them. This follows immediately from T1 with \(R_{\rm loc}\) in the nuisance block.

This is the formal reason a single direction-marginalized dipole amplitude cannot select global tilt over local boost.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-0ffe4939863f555d"></a>
## role-0ffe4939863f555d — T3. Exact log-prior-cutoff sensitivity identity

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 70–109행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T3. Exact log-prior-cutoff sensitivity identity

### Statement

Let a positive amplitude have a normalized log-uniform prior on \([a_-,a_+]\):

\[
\pi(a)=\frac{1}{a\log(a_+/a_-)}.
\]

For likelihood \(L(a)\), define

\[
I=\int_{a_-}^{a_+}L(a)\,d\log a,
\qquad
Z=\frac{I}{\log(a_+/a_-)}.
\]

Then

\[
\frac{\partial\log Z}{\partial\log a_-}
=-\frac{L(a_-)}{I}+\frac{1}{\log(a_+/a_-)},
\]

\[
\frac{\partial\log Z}{\partial\log a_+}
=\frac{L(a_+)}{I}-\frac{1}{\log(a_+/a_-)}.
\]

### Proof

Apply Leibniz differentiation to \(I\) in logarithmic coordinates and differentiate the prior normalization. ∎

### Use

This identity identifies whether a reported evidence value is data-localized or boundary-dominated without relying only on a few ad hoc prior reruns.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-33388bdc10392e43"></a>
## role-33388bdc10392e43 — T4. Fisher-information monotonicity under linear compression

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 110–148행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `8ae9d8eb2b2c879ce3c49508266c7cc5`

~~~~text
## T4. Fisher-information monotonicity under linear compression

### Statement

Let \(x\sim\mathcal N(\mu(\theta),C)\), with parameter-independent positive-definite \(C\), and let \(y=Ax\). Then

\[
F_y\preceq F_x.
\]

### Proof sketch

The score of the compressed experiment is the conditional expectation of the full score given \(y\). By the law of total variance,

\[
\operatorname{Var}(\mathbb E[s_x\mid y])
\preceq\operatorname{Var}(s_x).
\]

These variances are the Fisher matrices. ∎

### Off-diagonal covariance corollary

At a zero-mean isotropic Gaussian reference \(C=I\), a covariance derivative \(D_i\) has

\[
F_{ij}^{\rm full}=\frac12\operatorname{Tr}(D_iD_j).
\]

If only diagonal covariance responses are kept,

\[
F_{ij}^{\rm diag}=\frac12\sum_a(D_i)_{aa}(D_j)_{aa}.
\]

A purely off-diagonal response has positive full information and zero diagonal information. This establishes a rigorous information basis for a full-covariance MES extension.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-b31166513c96fbc1"></a>
## role-b31166513c96fbc1 — T5. Exact finite-mock false-positive upper bound

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 149–164행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T5. Exact finite-mock false-positive upper bound

If \(N\) independent null mocks produce zero triggers, then the exact one-sided \((1-\alpha)\) upper confidence bound is

\[
p_{\rm FPR}\le1-\alpha^{1/N}.
\]

### Proof

Under true trigger probability \(p\), the probability of zero triggers is \((1-p)^N\). Set this equal to \(\alpha\) and solve for \(p\). ∎

For \(N=100\) and 95% confidence, the bound is about 3%, not zero.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-b2479680617d2d6a"></a>
## role-b2479680617d2d6a — T6. Channel-matched occupancy necessity theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 165–182행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `6919eae2f25db303dcd094dceb92d121`

~~~~text
## T6. Channel-matched occupancy necessity theorem

### Statement

Let \(X=(X_1,\ldots,X_k)\) lie in a product of physically distinct non-negative sectors with ceilings \(U_j>0\). A scalar ratio

\[
F=\frac{\sum_j w_jX_j}{U_m}
\]

cannot be interpreted as a fraction of an available physical budget unless the denominator \(U_m\) bounds the same weighted numerator over the stated admissible set.

### Proof

If any sector \(j\ne m\) is unbounded by \(U_m\), choose an admissible sequence with \(X_j\to\infty\) and all other components fixed. Then \(F\) is unbounded and cannot be a filling fraction. Even if all sectors are finite, different sector units or constraint sets make the ratio convention-dependent unless a joint ceiling is proved. Therefore the minimal generally valid occupancy object is the vector \((X_j/U_j)_j\), plus a separately defined signed projection if desired. ∎

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-38aed17ce6749550"></a>
## role-38aed17ce6749550 — T7. Observational equivalence implies family non-identifiability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 183–194행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T7. Observational equivalence implies family non-identifiability

If two model families induce the same probability distribution for every observable in the adopted experiment,

\[
p(D\mid\mathcal F_1,\theta_1)=p(D\mid\mathcal F_2,\theta_2)
\]

under a parameter mapping covering the relevant support, no statistical test based on those observables can identify the family. Bayes factors then depend on prior volume and parameterization rather than data separation. This is the formal justification for equivalence-class reporting before a native morphology atlas exists.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-b454d1f327ac4d51"></a>
## role-b454d1f327ac4d51 — T8. Evidence stability under bounded transfer perturbation

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 195–224행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T8. Evidence stability under bounded transfer perturbation

### Statement

Let two transfer prescriptions induce log likelihoods \(\ell_1(\theta)\) and \(\ell_2(\theta)\) with the same normalized prior. If

\[
|\ell_1(\theta)-\ell_2(\theta)|\le\varepsilon
\]

for all \(\theta\), then

\[
|\log Z_1-\log Z_2|\le\varepsilon.
\]

### Proof

The pointwise bound implies

\[
e^{-\varepsilon}e^{\ell_1}\le e^{\ell_2}\le e^{\varepsilon}e^{\ell_1}.
\]

Integrating against the same prior and taking logarithms yields the result. ∎

This theorem turns external-to-native transfer comparison into a quantitative claim-promotion gate.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-cb72abf2f332daad"></a>
## role-cb72abf2f332daad — C1. First-order frame-composition lemma

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 227–230행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `a7cd2b5f9d5a123cf3e860f1d74ad117`

~~~~text
## C1. First-order frame-composition lemma

For non-relativistic relative velocities, rapidities add and the effective dipole velocity is the signed sum of observer, matter-frame, and local-flow velocities up to \(O(\beta^2)\). Exact vector composition requires the full Lorentz transformation; the first-order approximation is justified at \(\beta\sim10^{-3}\) only after the desired tolerance is stated.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-3e3ffebb8f3be8f8"></a>
## role-3e3ffebb8f3be8f8 — C2. Tomographic separation proposition

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 231–234행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `53627e3c58bc1bb6450861628cf5f06b`

~~~~text
## C2. Tomographic separation proposition

Suppose the nuisance-projected local response \(L(z)\) and global response \(G(z)\) are linearly independent over the observed bins and the covariance is positive definite. Then local and global amplitudes are identifiable by T1. The physical content lies in validating the response functions, not in assuming an exponential local decay.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-2bda87b554a5defa"></a>
## role-2bda87b554a5defa — C3. CMB boost anchor proposition

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 235–238행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `eeca78494834bbf639c186b76c2fe989`

~~~~text
## C3. CMB boost anchor proposition

If aberration and Doppler modulation are independently estimated with calibrated mask/noise response, they constrain the observer--CMB boost separately from a matter-number-count dipole. A residual coherent matter dipole may then test a matter--radiation rest-frame mismatch.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-cc28a1c07b0a94c4"></a>
## role-cc28a1c07b0a94c4 — C4. Native morphology necessity for family identification

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 239–244행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## C4. Native morphology necessity for family identification

Bianchi family identification requires observables whose response differs across families after orientation, amplitude, transfer, and nuisance marginalization. Scalar departure variables and a direction-marginalized dipole amplitude do not satisfy this requirement. Native \(a_{\ell m}\), polarization, BiPoSH/covariance, or equivalent morphology is therefore necessary.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-6dbdf98fdf5a865f"></a>
## role-6dbdf98fdf5a865f — T9. Nuisance-projected detection-threshold theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 245–296행
- 내용 버전: `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `e52314501cac0ed0376aa334ceae07d9`

~~~~text
## T9. Nuisance-projected detection-threshold theorem

### Statement

For the scalar-amplitude Gaussian model

\[
\mathbf y=a\,r+N\eta+\epsilon,
\qquad \epsilon\sim\mathcal N(0,C),
\]

let \(W=C^{-1/2}\) and let \(P_N^\perp\) project orthogonally away from \(\operatorname{col}(WN)\). If

\[
\mathcal I_a=r^T W^T P_N^\perp W r>0,
\]

then the generalized least-squares estimator of \(a\) after nuisance projection has variance

\[
\operatorname{Var}(\widehat a)=\mathcal I_a^{-1}.
\]

Consequently the minimum amplitude giving an expected Wald signal-to-noise \(s\) is

\[
|a|_{\min}=\frac{s}{\sqrt{\mathcal I_a}}.
\]

If \(\mathcal I_a=0\), no finite amplitude threshold exists within the adopted experiment because the target response lies in the nuisance span.

### Proof

Whiten the model and project away the nuisance span:

\[
P_N^\perp W\mathbf y=a\,P_N^\perp Wr+P_N^\perp W\epsilon.
\]

On the projected subspace, the noise covariance is the projector itself. The one-parameter generalized least-squares estimator is

\[
\widehat a=
\frac{r^T W^T P_N^\perp W\mathbf y}
{r^T W^T P_N^\perp Wr}.
\]

Its numerator noise variance is \(\mathcal I_a\), so division by \(\mathcal I_a^2\) yields \(\operatorname{Var}(\widehat a)=\mathcal I_a^{-1}\). The Wald signal-to-noise is \(|a|\sqrt{\mathcal I_a}\), giving the stated threshold. If \(\mathcal I_a=0\), T1 implies non-identifiability. ∎

### Research use

T9 converts the abstract rank condition into a survey-design statement: additional depth bins help only insofar as they add covariance-weighted response directions outside the local/systematic nuisance span.
~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md` 1–5행):

~~~~text
# Theorem candidates and analytic proofs

This document separates proved mathematical statements from conditional cosmology propositions and future solver-dependent theorems.

---
~~~~

<a id="role-cec19bb33424924a"></a>
## role-cec19bb33424924a — T-A1 — Cancellation / non-identifiability of isotropy from `x_C`  [Provable]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 11–20행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-A1 — Cancellation / non-identifiability of isotropy from `x_C`  [Provable]

**Statement.** The signed map `x_C : ℝ⁴_{≥,≥,·,·} → ℝ` has a cancellation set `Z = {s : x_C(s)=0}` of codimension 1, and `sup_{s∈Z} ‖s‖ = ∞`. Consequently `x_C` is not a proper isotropy functional: for every `ε>0` there exist configurations with `|x_C|<ε` and total magnitude `M=‖s‖` arbitrarily large. Isotropy (`s=0`) is identifiable only from the sector vector, not from `x_C`.

**Proof sketch.** `Z` is the zero set of a nonzero linear functional on ℝ⁴, hence a hyperplane (codim 1). The ray `s(t)=t·(1,1,0,0)` lies in `Z` (since `Σ²−W²=0`) with `‖s(t)‖=t√2 → ∞`. For the `ε`-statement, perturb within `Z`. ∎

**Numerical support.** N1: explicit dim-3 null family; smallest-`|x_C|` decile spans `M` over ~10³×.

**To close.** State the dimension of `Z∩{physical cone}` and the precise sense in which the sector vector is the minimal sufficient statistic for sector identifiability.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-0b535971595827a0"></a>
## role-0b535971595827a0 — T-A2 — Comparator covariance and the invariant content  [Provable / Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 21–30행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `49fad93726b157d89f59065bff9250a8`

~~~~text
### T-A2 — Comparator covariance and the invariant content  [Provable / Conditional]

**Statement.** Under the comparator action `χ : s ↦ (λ_χ Σ², λ_χ W², λ_χ Ω_tilt, Ω_{k,aniso}+δ_χ)`, the coordinate `x_C` is **not** invariant: `x_C(χs) = λ_χ(Σ²−W²+Ω_tilt) + Ω_{k,aniso} + δ_χ`. The combination invariant under the multiplicative part is the (shear,vorticity,tilt) magnitude `‖(Σ²,W²,Ω_tilt)‖` up to `λ_χ`; the curvature-reference shift `δ_χ` is the sole source of `x_C` non-invariance. Hence any reported `x_C`/`Q` is meaningful only with its comparator label, and the comparator-stable content is the shear–vorticity–tilt magnitude.

**Proof sketch.** Direct substitution of the action; the multiplicative factor cancels in the normalized magnitude; `δ_χ` enters `x_C` additively and has no invariant completion within the scalar. ∎

**Numerical support.** N2: `x_C` relative spread 45%→>1500%; rescaled norm spread ≪ that.

**To close.** Fix the physical definition of `λ_χ, δ_χ` from the comparator construction (not the documented toy) and prove invariance exactly.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-7f7d9023cba5b5c4"></a>
## role-7f7d9023cba5b5c4 — T-A3 — Selection-marginalized boost–tilt separability  [Conditional → Forecast]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 31–40행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-A3 — Selection-marginalized boost–tilt separability  [Conditional → Forecast]

**Statement.** Let `b(z)` be the kinematic (boost) dipole profile including the redshift-selection correction of von Hausegger–Dalang (2025), and `τ(z)` a global-tilt profile with transition `z_T`. If `τ` is not in the span of `{b, ∂_β b}` over the observed `z`-range (a genericity condition satisfied when `z_T` lies inside the range), then the residual `r(z) = m(z) − \hat A\,b(z)` (with `\hat A` the LS boost amplitude) has zero expectation under the boost hypothesis and nonzero expectation under the tilt hypothesis, and the Fisher information for boost-vs-tilt separation is `F = Σ_z (Δr(z)/σ_z)² > 0`, growing with depth coverage `z_max` and source count `N` (`σ_z ∝ N^{-1/2}`).

**Proof sketch.** `r` is the projection of `m` onto the orthogonal complement of the boost template; under boost, `E[r]=0`; under tilt, `E[r]=` the component of `τ` orthogonal to `b`, nonzero by the genericity condition. `F` is the standard Gaussian two-hypothesis Fisher information. ∎

**Numerical support.** N3-A: residual AUC→1.0, Fisher sep→~8 with `z_max=3, N=10⁶`. N3-B: the naive flatness statistic is **not** a valid test (FPR→100% under selection stress) — only the residual statistic is calibrated.

**To close.** Replace the toy `b,τ` with the survey-specific selection function and a covariant tilt template (`06` T-B3); propagate the full covariance; report the forecast significance for DESI/Quaia/SKA.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-64118825a227dd25"></a>
## role-64118825a227dd25 — T-A4 — Tilt-channel projection (one-dimensionality)  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 41–52행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `ad8bac17116f324a0acde125c722acfd`

~~~~text
### T-A4 — Tilt-channel projection (one-dimensionality)  [Conditional]

**Statement.** Under the dipole premise and the legacy transfer, the FLRW-departure log-evidence decomposes additively as `ln B = ln B_tilt + ln B_shear + I` with `ln B_shear ≤ 0` (anisotropic shear geometry disfavoured) and `ln B_tilt / ln B ≈ 1`. The data project onto the one-dimensional tilt subspace; the geometric (shear/vorticity) directions carry no positive evidence.

**Proof sketch / status.** Empirical decomposition (manuscript ch07/ch08): `ln B_tilt=+26.40`, `ln B_shear=−0.87`, `I=−0.07`. `ln B_shear≤0` follows from the shear adding an Occam-penalized parameter that the data set to zero (the data prefer `Σ²=0`). One-dimensionality = the evidence is a monotone function of the single tilt rapidity `β`.

**Numerical support.** N5: tilt fraction ~104%; sign structure stable in 20k channel reweightings (0 violations).

**To close.** Establish the decomposition as an orthogonal evidence projection under a stated prior factorization; bound `I`; restate transfer-conditionally.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-c512d8fb1c4e1efb"></a>
## role-c512d8fb1c4e1efb — T-B1 — Almost-EGS tilt loophole (sharpened)  [Conditional, grounded]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 55–62행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-B1 — Almost-EGS tilt loophole (sharpened)  [Conditional, grounded]

**Statement.** An almost-isotropic CMB temperature field (to `O(ε)`) for all fundamental observers, together with the Copernican principle, bounds the shear scalar `Σ = O(ε)` (Stoeger–Maartens–Ellis 1995) **only under additional constraints on the multipole derivatives**, and does **not** bound the tilt rapidity `β` of the matter frame nor the curl degrees of freedom (`curl E_{ab}`, `curl σ_{ab}`, `H_{ab}`). Hence a tilt `β ~ O(\text{dipole})` is compatible with an almost-isotropic CMB, and the matter dipole is the unique low-order observational handle on it.

**Status.** Grounded: SME almost-EGS + the explicit counterexamples of Nilsson–Uggla–Wainwright–Lim (1999) and Lim–Nilsson–Wainwright (2001) ("an almost isotropic CMB temperature does not imply an almost isotropic universe"); the unconstrained curl d.o.f. are noted in the covariant-cosmology reviews. This is the GR justification for the tilt-sector focus.

**To close.** Write the explicit `1+3` multipole-constraint chain showing exactly which derivative conditions are needed and where `β` escapes; cite the loophole literature precisely.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-bb9096c34c348bc0"></a>
## role-bb9096c34c348bc0 — T-B2 — Tilt-sector confinement (exclusion)  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 63–72행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-B2 — Tilt-sector confinement (exclusion)  [Conditional]

**Statement.** Let the observed matter dipole correspond to a departure amplitude `A_obs`. Under the MES linear shear ceiling `Σ²_max` and the Saadeh vorticity bound `W² < W²_Saadeh`, any FLRW departure that reproduces `A_obs` through the geometric (shear/vorticity) sector is excluded: the Frobenius-coupled vorticity required by a dipole-scale shear exceeds `W²_Saadeh` by ~8 orders of magnitude, and the shear required for the observed CMB quadrupole saturates/exceeds the MES window. Therefore the departure is confined to the tilt (boost) sector.

**Proof sketch.** `W² = R_WS² Σ²` (Frobenius coupling); a shear in the CMB sensitivity window `σ/H ~ 10⁻⁶` gives `W² ~ 10⁻¹³ ≫ W²_Saadeh ~ 10⁻²¹`; the tilt defect `Ω_tilt ~ (1+w)Ω_m sinh²β ~ β²` reproduces `A_obs` at the observed `β` without geometric shear. ∎ (orders-of-magnitude)

**Numerical support.** N4: vorticity margin ~8 dex over the Saadeh bound; tilt occupies ~2.7× the linear shear ceiling.

**To close.** Use the physical `Σ²_max`, `W²_Saadeh`, and `R_WS` (not toy values); state the exclusion confidence as a function of the bound uncertainties.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-3e449104c2c16bb3"></a>
## role-3e449104c2c16bb3 — T-B3 — Depth signature of a global tilt  [Conditional, template]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 73–80행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-B3 — Depth signature of a global tilt  [Conditional, template]

**Statement.** A global tilt (Turner tilted universe; Tsagas tilted cosmology) produces a matter-dipole amplitude that is redshift-dependent, with a transition redshift `z_T` at which the tilt contribution to the deceleration/peculiar dipole changes sign or behaviour, distinct from the (selection-corrected) kinematic profile.

**Status.** Grounded in the tilted-cosmology literature (the q-dipole sign change at a transition redshift). Stated as a *template*, not a numerical prediction, because `z_T` and the amplitude depend on the tilt model.

**To close.** Derive `z_T(model)` from the covariant tilt evolution; supply the template `τ(z)` used in T-A3/N3 from this derivation rather than the toy `tanh`.

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-7f2b20fd335a5e71"></a>
## role-7f2b20fd335a5e71 — T-B4 (secondary) — Neutrino-quadrupole exact closure  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 81–86행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-B4 (secondary) — Neutrino-quadrupole exact closure  [Conditional]

**Statement.** For collisionless neutrinos after decoupling, the `T_eff` tangency diagnostic `D_{ν,≥2}=0` holds exactly, so the finite-dimensional `T_eff` manifold is an invariant submanifold of the Boltzmann hierarchy and the neutrino quadrupole closure is exact (not perturbative). (Transfer-conditional for the resulting `D₂` share.)

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-a974dcb75935f0d6"></a>
## role-a974dcb75935f0d6 — T-C1 — Falsifiable tomographic discriminant (forecast)  [Forecast]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 89–98행
- 내용 버전: `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; 관찰 커밋: `9271a43e083f5e86ab24744a6bfea09886cf3334`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T-C1 — Falsifiable tomographic discriminant (forecast)  [Forecast]

**Statement.** The selection-marginalized residual tomographic dipole profile `r(z)` is, under the tilt hypothesis, a specific function of `z` (the orthogonalized tilt template of T-B3). A measurement of `r(z)` over `z ∈ [0, z_max]` with `N` sources distinguishes boost from tilt at a significance set by the Fisher information of T-A3; with `z_max ≳ 3` and `N ≳ 10⁶` (DESI/Quaia/SKA-scale), the separation is decisive in the toy, and the naive flatness test is explicitly invalid.

**Status.** Forecast, demonstrated in N3. This is the central publishable data-analysis result: **a concrete, falsifiable test that future tomographic dipole data can run, with the correct (selection-marginalized) statistic and a covariant tilt template.**

**To close.** Apply to real DESI DR1 QSO / Quaia / radio with the survey selection function; report the measured `r(z)` and the boost-vs-tilt likelihood ratio with full systematics (mask, magnification bias, estimator) per `07`.

---

~~~~

제안 의도 문맥 (`docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — Theorem Candidates (Strong Statements)

Strong, falsifiable, honest statements — exclusion, structure, and forecast — that survive the verification of `02`. Each: a formal statement, a proof sketch / status, the numerical support, and what is needed to close it to a full theorem. Notation: signed coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`; sector vector `s = (Σ²_std, W²_std, Ω_tilt, Ω_{k,aniso})`; comparator `χ ∈ {flat, matched, closed}`.
~~~~

<a id="role-88c3f1e0e7cac0ca"></a>
## role-88c3f1e0e7cac0ca — Contract-enforced semantic firewall for diagnostic statistics  ★ flagship

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 9–16행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F1 — Contract-enforced semantic firewall for diagnostic statistics  ★ flagship

- **Tier:** Methodological / Exact (the refusals are deterministic and test-backed).
- **What it is:** each diagnostic (`x_C, Q, Π, F, G_F`) is a frozen typed object that *refuses construction* if (a) its metadata/labels/caveats use reserved overclaim language (occupancy, posterior, evidence, bayes factor, family-ID, geometry, "global tilt", native-validated), (b) its `owner`/`claim_tier` is not the pinned diagnostic-only value, or (c) its certification gates fail. Enforced by `_scan_reserved_language`, owner/tier checks, and `tests/mio/*`.
- **Novelty:** Blinding (DES) hides *results* to protect analysis *choices*; pre-registration commits to choices in advance; multiverse/specification-curve analysis enumerates *outcomes*. **None refuses to construct an over-claimed diagnostic object.** A machine-checkable, test-enforced *semantic* firewall on the statistics themselves is essentially unprecedented in cosmology.
- **Audit status:** Praised — "enforce nearly all rejection triggers at the code level." Untouched.
- **Defense:** *"This is just disclaimers."* — Disclaimers are prose a reader can ignore; this is a *constructor that throws* on overclaim, with adversarial tests proving it (see F9/E6). It is the mechanism that makes a non-detection result structurally honest.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-4166dee898ca5cce"></a>
## role-4166dee898ca5cce — Signed comparator-projection coordinate `x_C` with a cancellation diagnostic

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 17–24행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F2 — Signed comparator-projection coordinate `x_C` with a cancellation diagnostic

- **Tier:** Exact (it is the normalized constraint rearranged) + Methodological (the cancellation_index).
- **What it is:** `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`, a single *signed* scalar with explicit comparator/frame/units and a `cancellation_index = 1 − |x_C|/Σ|components|` that quantifies inter-sector cancellation.
- **Novelty:** Prior covariant work (MES; 1+3 covariant) bounds modes separately or uses unsigned magnitudes. The *signed, comparator-explicit packaging plus a cancellation diagnostic that exposes the `x_C≈0 ≠ isotropy` trap* is new. (Verified: `x_C=0` with `cancellation_index=1` while shear+vorticity are large.)
- **Audit status:** `x_C` correct; the cancellation caveat is a finding → promote `cancellation_index` to first-class (F7).
- **Defense:** *"Just the Friedmann constraint."* — Yes, exact by design; the contribution is the signed/sector packaging and the built-in cancellation guard, not a new equation.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-ebf95277fbdb591c"></a>
## role-ebf95277fbdb591c — Fail-closed certified filling fraction `F`

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 25–32행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F3 — Fail-closed certified filling fraction `F`

- **Tier:** Methodological / Supported.
- **What it is:** `F = x_C/U` computed sample-wise (mean of ratios, not ratio of means), constructible *only* when `x_C ≥ 0` (sign-clean), the budget is an admissible ceiling, and `0 ≤ F ≤ 1` **without clipping** (it raises otherwise); external/atlas/observational denominators are barred from certifying.
- **Novelty:** Ratios-to-bounds exist (e.g. `Ω_k/Ω_k,max`). A *fail-closed certification semantics* — the object exists iff the preconditions hold, no silent clipping, provenance-stamped — applied to an anisotropy occupancy is new.
- **Audit status:** Praised (no clipping, sign-clean enforced). Naming finding → add F8 magnitude companion.
- **Defense:** *"Why refuse to return a number?"* — Because a clipped or sign-dirty occupancy is a false certificate; refusing is the honest behavior.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-168da898257bb7fd"></a>
## role-168da898257bb7fd — Registered-threshold exceedance curve `Π`

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 33–40행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F4 — Registered-threshold exceedance curve `Π`

- **Tier:** Methodological.
- **What it is:** an empirical survival fraction of `Q`/`F` samples with a typed threshold policy: `CURVE_ONLY` (no selected threshold) or `PRE_REGISTERED` (requires a `registration_hash` + `selection_rule`, forbids post-hoc language), plus a `measure_kind` that forces covariance/null status for `bootstrap`/`null_ensemble`.
- **Novelty:** Pre-registration is a practice; here it is **baked into the type** of the statistic, with anti-post-hoc enforcement and anti-smuggling of selected thresholds. A typed micro-pre-registration for an exceedance curve is new.
- **Audit status:** Praised. Finding: state `measure_kind` in captions (exceedance ≠ p-value unless matched null).
- **Defense:** *"Just a survival function."* — With a constructor that refuses post-hoc threshold selection and truth-probability language; that is the contribution.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-e5cf182155e30a6d"></a>
## role-e5cf182155e30a6d — Denominator-evolution-split depth gap `G_F`

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 41–48행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F5 — Denominator-evolution-split depth gap `G_F`

- **Tier:** Methodological / Supported.
- **What it is:** `G_F = exp(log F_cmp − log F_ref)` over ordered non-overlapping depth bins, floor-stabilized, with a mandatory **denominator-evolution split** that separates "F changed because `x_C` changed" from "because the ceiling/denominator changed," and mandatory covariance/null/calibration metadata.
- **Novelty:** Tomographic ratios are standard; the *structural separation of the numerator-vs-denominator-evolution confound*, with matched-null metadata required and "global tilt" language barred, is new.
- **Audit status:** Praised (split exposed). Finding: matched-null required before any tilt meaning; FPRs currently exceed threshold → no discrimination (honest).
- **Defense:** *"A depth ratio."* — One that refuses to hide the denominator-evolution confound and refuses to call itself global-tilt evidence.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-b5d83fa11adcaeaa"></a>
## role-b5d83fa11adcaeaa — Typed diagnostic↔inference (MIO↔HTT) firewall

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 49–56행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F6 — Typed diagnostic↔inference (MIO↔HTT) firewall

- **Tier:** Methodological / Exact.
- **What it is:** diagnostics are owner-pinned MIO/diagnostic-only; the inference-side `posterior_pushforward` *rejects MIO inputs* (`reject_mio_likelihood_inputs`) and forbids `ln_b`/`evidence`/`posterior`/`score` tokens.
- **Novelty:** A *typed boundary* that prevents laundering diagnostics into evidence/posterior/ranking. Reproducibility frameworks track provenance; they do not enforce a diagnostic↔inference type boundary.
- **Audit status:** Praised. Untouched.
- **Defense:** *"Bookkeeping."* — Bookkeeping that makes "these are diagnostics, not evidence" a checkable invariant rather than a hope.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-1560e36e6e35f4a8"></a>
## role-1560e36e6e35f4a8 — Sector-resolved departure vector + first-class cancellation reporting  ★ new

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 57–63행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F7 — Sector-resolved departure vector + first-class cancellation reporting  ★ new

- **Tier:** New (from the audit's cancellation finding).
- **What it is:** report the four signed components `(Σ², −W², Ω_tilt, Ω_{k,aniso})` and `cancellation_index` as first-class outputs alongside `x_C`, so `x_C≈0` is never mistaken for isotropy.
- **Novelty:** turns a known semantic trap into a *new reported object* (a sector-resolved departure profile) that is strictly more informative than the scalar.
- **Defense:** *"You only added this because of the audit."* — Correct; the corrected object is strictly more informative.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-54a8ac1373d38a08"></a>
## role-54a8ac1373d38a08 — Total-anisotropy magnitude companion to `F`  ★ new

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 64–70행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F8 — Total-anisotropy magnitude companion to `F`  ★ new

- **Tier:** New (from the audit's naming finding).
- **What it is:** an unsigned magnitude (e.g. `absolute_component_total` or a sector-norm) reported beside `F`, so users get both the *signed ceiling-occupancy* (`F`) and a genuine *total-anisotropy magnitude* — curing the "filling fraction"→physical-occupancy misread.
- **Novelty:** a paired signed/unsigned reporting convention for departure that prevents the cancellation trap from propagating into `F`.
- **Defense:** *"Redundant."* — Not redundant: `F` and the magnitude diverge exactly under cancellation, which is the case that matters.

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-198a4ed765030629"></a>
## role-198a4ed765030629 — Semantic-firewall specification + adversarial fuzzer  ★ new

- 역할: 역할 판단 보류
- 출처: `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 71–79행
- 내용 버전: `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50:c57f56a5`; 관찰 커밋: `d20e9af45912a07dc63ea6433db738afa98c5f29`
- 이유: Novelty Ledger의 형식화 주장이다. 이 매핑은 학술 신규성이나 정리 역할을 판정하지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## F9 — Semantic-firewall specification + adversarial fuzzer  ★ new

- **Tier:** New / Methodological (from the audit's semantic-split finding).
- **What it is:** a portable specification of the firewall (reserved-language sets, owner/tier rules, fail-closed gates) plus a **property-based fuzzer** that attempts to smuggle forbidden language/values and confirms refusal — generalizing the semantic-split lesson into a reusable artifact.
- **Novelty:** packages the firewall as something *other projects can adopt and test*, not just an internal guard.
- **Defense:** *"Internal tooling."* — A spec + fuzzer for anti-overclaim contracts is itself a methodological deliverable (cf. linters/validators as contributions).

---

~~~~

제안 의도 문맥 (`docs/audits/formalism_audit_2026-06-19/formalism_originality_program/01_NOVELTY_LEDGER.md` 1–5행):

~~~~text
# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).
~~~~

<a id="role-94f40bef9b3df71a"></a>
## role-94f40bef9b3df71a — full_fixture_rank

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` 97–99행
- 내용 버전: `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60:ad208a43`; 관찰 커밋: `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `5e9cb89714562af70d56ff76eb7f3fa4`

~~~~text
theorem full_fixture_rank : fullFixture.rank = 2 := by
  simp [fullFixture]

~~~~

<a id="role-986d9a91c3f3be1b"></a>
## role-986d9a91c3f3be1b — partial_fixture_rank

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` 100–103행
- 내용 버전: `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60:ad208a43`; 관찰 커밋: `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `b788567133e62076655cda2d1e2723f0`

~~~~text
theorem partial_fixture_rank : partialFixture.rank = 1 := by
  rw [partialFixture, Matrix.rank_diagonal]
  native_decide

~~~~

<a id="role-0534600409804efd"></a>
## role-0534600409804efd — zero_fixture_rank

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/mes_local_global_response/cas/axes/lean/PR328LocalGlobal.lean` 104–117행
- 내용 버전: `4c1db75bab9aedee0a06b27c14799d303285dd7a6bffa23e33deb9cfe3cd0a60:ad208a43`; 관찰 커밋: `b5ebf80ded7b4d31e3c480d750ccbccaff60b961`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `c03b428acdb6a208d0d19ff4fa3f8221`

~~~~text
theorem zero_fixture_rank : zeroFixture.rank = 0 := by
  simp [zeroFixture]

/-! ## Conditional composition bound and strict nonidentification -/

universe u

section ConditionalRank

variable {K E F G : Type u} [DivisionRing K]
variable [AddCommGroup E] [Module K E]
variable [AddCommGroup F] [Module K F]
variable [AddCommGroup G] [Module K G]

~~~~

<a id="role-1f932b980438e165"></a>
## role-1f932b980438e165 — Pr171TiltRelaxation.stableFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr171_cas/generation_3/source_snapshot/formal_pr171/Pr171TiltRelaxation/Basic.lean` 32–36행
- 내용 버전: `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797:ad208a43`; 관찰 커밋: `b8a857742bd6c2d727ea2009f6e8a341a031b120`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `558137ac617f63042b82c3ac8a83a27a`

~~~~text
theorem stableFixture :
    dragTrace (1/4) (1/2) (1/3) = (-25/12 : ℚ) ∧
    dragDet (1/4) (1/2) (1/3) = (5/6 : ℚ) := by
  norm_num [dragTrace, dragDet]

~~~~

<a id="role-e4a0605202c791c4"></a>
## role-e4a0605202c791c4 — product_fixture_exact

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr254_anchor_geometry/axes/lean/PR254R3LeanAxis.lean` 82–88행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `8aa8d7357e9dce80e54b0b0197fe71365a771f02`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `39a937486b1d0b224d84676848f88b86`

~~~~text
theorem product_fixture_exact : productFixtureGauge = (5 : ℝ) / 2 := by
  have h25 : Real.sqrt (25 : ℝ) = 5 := by norm_num
  have h64 : Real.sqrt (64 : ℝ) = 8 := by norm_num
  norm_num [productFixtureGauge, h25, h64]

/-! ## Positive-definite ellipsoid -/

~~~~

<a id="role-684daed5b2747228"></a>
## role-684daed5b2747228 — ellipsoid_fixture_exact

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr254_anchor_geometry/axes/lean/PR254R3LeanAxis.lean` 148–154행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `8aa8d7357e9dce80e54b0b0197fe71365a771f02`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `2dcfd11fdda7506135ead3543b0f5eba`

~~~~text
theorem ellipsoid_fixture_exact :
    quadraticForm ellipsoidFixtureQ ellipsoidFixtureU = 1 := by
  rw [ellipsoid_fixture_form]
  norm_num [ellipsoidFixtureU]

/-! ## Certified centrally symmetric spanning H-polytope -/

~~~~

<a id="role-add01c3bb0772b63"></a>
## role-add01c3bb0772b63 — polytope_fixture_exact

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr254_anchor_geometry/axes/lean/PR254R3LeanAxis.lean` 243–275행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `8aa8d7357e9dce80e54b0b0197fe71365a771f02`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `ea657d518434294e1ee11f45b3a71ef1`

~~~~text
theorem polytope_fixture_exact :
    polytopeGauge polytopeFixture polytopeFixtureU = (1 : ℝ) / 2 := by
  apply le_antisymm
  · apply max_le
    · apply (finiteMax_le_iff
        (fun i =>
          dotProduct (polytopeFixture.normal i) polytopeFixtureU /
            polytopeFixture.bound i) ((1 : ℝ) / 2)).mpr
      intro i
      fin_cases i <;>
        norm_num [polytopeFixture, polytopeFixtureNormals,
          polytopeFixtureBounds, polytopeFixtureU, dotProduct,
          Fin.sum_univ_two]
    · norm_num
  · have hterm :
        dotProduct (polytopeFixture.normal 0) polytopeFixtureU /
            polytopeFixture.bound 0 ≤
          finiteMax (fun i =>
            dotProduct (polytopeFixture.normal i) polytopeFixtureU /
              polytopeFixture.bound i) :=
      le_finiteMax
        (fun i =>
          dotProduct (polytopeFixture.normal i) polytopeFixtureU /
            polytopeFixture.bound i) 0
    have hraw : (1 : ℝ) / 2 ≤ rawPolytopeGauge
        polytopeFixture polytopeFixtureU := by
      simpa [rawPolytopeGauge, polytopeFixture, polytopeFixtureNormals,
        polytopeFixtureBounds, polytopeFixtureU, dotProduct,
        Fin.sum_univ_two] using hterm
    exact hraw.trans (le_max_left _ _)

/-! ## One-way outer-envelope implication -/

~~~~

<a id="role-2b82dda709b5a5ac"></a>
## role-2b82dda709b5a5ac — rank_fixture_submatrix

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr254_anchor_geometry/axes/lean/PR254R3LeanAxis.lean` 343–348행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `8aa8d7357e9dce80e54b0b0197fe71365a771f02`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `c29d15e9d066e40d8d223ab74e72d1fd`

~~~~text
theorem rank_fixture_submatrix :
    rankFixtureR.submatrix firstTwoRows id = rankFixtureS := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [rankFixtureR, rankFixtureS, firstTwoRows]

~~~~

같은 소스의 사용 문맥 (364–366행):

~~~~text
    have hsub := Matrix.rank_submatrix_le rankFixtureR firstTwoRows id
    rw [rank_fixture_submatrix, rank_fixture_S_exact] at hsub
    exact hsub
~~~~

<a id="role-fc295cd90fda21cb"></a>
## role-fc295cd90fda21cb — rank_fixture_S_det

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr254_anchor_geometry/axes/lean/PR254R3LeanAxis.lean` 349–351행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `8aa8d7357e9dce80e54b0b0197fe71365a771f02`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `e98fb9eebd74faf0c5c03a5c0dd1d071`

~~~~text
theorem rank_fixture_S_det : rankFixtureS.det = 1 := by
  norm_num [rankFixtureS, Matrix.det_fin_two]

~~~~

같은 소스의 사용 문맥 (352–354행):

~~~~text
theorem rank_fixture_S_isUnit : IsUnit rankFixtureS.det := by
  rw [rank_fixture_S_det]
  exact isUnit_one
~~~~

<a id="role-7630fda51051ab4d"></a>
## role-7630fda51051ab4d — rank_fixture_S_isUnit

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr254_anchor_geometry/axes/lean/PR254R3LeanAxis.lean` 352–355행
- 내용 버전: `7ebc96847f3dbf291c3ddbca2945bbf1e0848401108ced298dfea6844ce67c25:ad208a43`; 관찰 커밋: `8aa8d7357e9dce80e54b0b0197fe71365a771f02`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `c437ea70c28a1299c62930e980278125`

~~~~text
theorem rank_fixture_S_isUnit : IsUnit rankFixtureS.det := by
  rw [rank_fixture_S_det]
  exact isUnit_one

~~~~

같은 소스의 사용 문맥 (356–358행):

~~~~text
theorem rank_fixture_S_isUnit_matrix : IsUnit rankFixtureS :=
  rankFixtureS.isUnit_iff_isUnit_det.mpr rank_fixture_S_isUnit

~~~~

<a id="role-44851e48052e6042"></a>
## role-44851e48052e6042 — PR257Orbit.mm_ident_right

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 136–138행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `7ac63a2f4b99d0890cbc744f663ffd16`

~~~~text
theorem mm_ident_right (A : Mat3) : mm A ident = A := by
  apply Mat3.extensionality <;> grind [mm, ident]

~~~~

같은 소스의 사용 문맥 (181–183행):

~~~~text
    _ = mm (mm R sigma) ident := by rw [hR.rt_mul_r]
    _ = mm R sigma := mm_ident_right _

~~~~

<a id="role-97aefe50e47b3241"></a>
## role-97aefe50e47b3241 — PR257Orbit.mv_assoc

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 139–142행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `129989e2c353543b081479fd9b03fc38`

~~~~text
theorem mv_assoc (A B : Mat3) (u : Vec3) :
    mv (mm A B) u = mv A (mv B u) := by
  apply Vec3.extensionality <;> grind [mv, mm]

~~~~

같은 소스의 사용 문맥 (170–172행):

~~~~text
    _ = dot u (mv (mm (transpose R) R) v) := by
          rw [mv_assoc]
    _ = dot u (mv ident v) := by rw [hR.rt_mul_r]
~~~~

<a id="role-e9cfd2b980b95555"></a>
## role-e9cfd2b980b95555 — PR257Orbit.mv_ident

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 143–145행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `a221ac75cb41bf19cad4e6f3336d5c3c`

~~~~text
theorem mv_ident (u : Vec3) : mv ident u = u := by
  apply Vec3.extensionality <;> grind [mv, ident]

~~~~

같은 소스의 사용 문맥 (172–174행):

~~~~text
    _ = dot u (mv ident v) := by rw [hR.rt_mul_r]
    _ = dot u v := by rw [mv_ident]

~~~~

<a id="role-ea87ca7d0eba3f97"></a>
## role-ea87ca7d0eba3f97 — PR257Orbit.trace_cyclic

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 146–149행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `de8903950da8e522e0d03654716082f4`

~~~~text
theorem trace_cyclic (A B : Mat3) :
    trace (mm A B) = trace (mm B A) := by
  grind [trace, mm]

~~~~

같은 소스의 사용 문맥 (206–208행):

~~~~text
    trace (sigmaAction R A)
        = trace (mm (transpose R) (mm R A)) := trace_cyclic _ _
    _ = trace (mm (mm (transpose R) R) A) := by rw [mm_assoc]
~~~~

<a id="role-2df1a4ea65bf8340"></a>
## role-2df1a4ea65bf8340 — PR257Orbit.det_mul

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 150–153행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `ca8430b9d84c8d40d2860bd14d56be7c`

~~~~text
theorem det_mul (A B : Mat3) :
    det (mm A B) = det A * det B := by
  grind [det, mm]

~~~~

같은 소스의 사용 문맥 (267–269행):

~~~~text
  rw [sigmaAction_mv hR, sigmaAction_mv hR]
  rw [fromCols_mv, det_mul]

~~~~

<a id="role-fa00af408959bc89"></a>
## role-fa00af408959bc89 — PR257Orbit.dot_vscale_left

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 270–273행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `159964a6de5b7e45c2317b11041a906e`

~~~~text
theorem dot_vscale_left (a : Rat) (u v : Vec3) :
    dot (vscale a u) v = a * dot u v := by
  grind [dot, vscale]

~~~~

같은 소스의 사용 문맥 (296–298행):

~~~~text
  unfold omega2
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
  have hd := det_sq_one hR
~~~~

<a id="role-d2fb4698a55ba94d"></a>
## role-d2fb4698a55ba94d — PR257Orbit.mv_vscale

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 278–281행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `ce10e280a681c61a7d5f7b5612ecca99`

~~~~text
theorem mv_vscale (A : Mat3) (a : Rat) (u : Vec3) :
    mv A (vscale a u) = vscale a (mv A u) := by
  apply Vec3.extensionality <;> grind [mv, vscale]

~~~~

같은 소스의 사용 문맥 (305–307행):

~~~~text
  unfold omegaSigmaOmega
  rw [mv_vscale, sigmaAction_mv hR]
  rw [dot_vscale_left, dot_vscale_right, dot_mv hR]
~~~~

<a id="role-195d6c9e3d713c70"></a>
## role-195d6c9e3d713c70 — PR257Orbit.fixed_beta_sigma_beta

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 449–450행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `6c6a81643863c3b7f1603d8fdf43c85f`

~~~~text
theorem fixed_beta_sigma_beta :
    betaSigmaBeta fixedSigma fixedBeta = 0 := by native_decide
~~~~

<a id="role-c3c55960e0efa2af"></a>
## role-c3c55960e0efa2af — PR257Orbit.fixed_omega2

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 455–455행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `ac02c8637cbeee423950fe5c79d3429f`

~~~~text
theorem fixed_omega2 : omega2 fixedOmega = 14 := by native_decide
~~~~

<a id="role-f8fb136394fe52df"></a>
## role-f8fb136394fe52df — PR257Orbit.fixed_omega_sigma_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 456–457행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `566c3245ed6b00899328066b276ba3e8`

~~~~text
theorem fixed_omega_sigma_omega :
    omegaSigmaOmega fixedSigma fixedOmega = -18 := by native_decide
~~~~

<a id="role-f6a8f02aa7bdeec3"></a>
## role-f6a8f02aa7bdeec3 — PR257Orbit.fixed_omega_sigma2_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 458–459행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `6c18e5e04a058e0a4bf0e0925052208a`

~~~~text
theorem fixed_omega_sigma2_omega :
    omegaSigma2Omega fixedSigma fixedOmega = 98 := by native_decide
~~~~

<a id="role-e689c5e2d31b8469"></a>
## role-e689c5e2d31b8469 — PR257Orbit.fixed_beta_dot_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 460–461행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `dfae3b9b7e377375423d38c556c7dac7`

~~~~text
theorem fixed_beta_dot_omega :
    betaDotOmega fixedBeta fixedOmega = 6 := by native_decide
~~~~

<a id="role-88ede3fc8a95d9cd"></a>
## role-88ede3fc8a95d9cd — PR257Orbit.fixed_beta_sigma_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 462–463행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `095100c2d3ff001bb135bd9ea28578dd`

~~~~text
theorem fixed_beta_sigma_omega :
    betaSigmaOmega fixedSigma fixedBeta fixedOmega = -4 := by native_decide
~~~~

<a id="role-69d16f81e46588fd"></a>
## role-69d16f81e46588fd — PR257Orbit.fixed_omega_sigma3_omega

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 476–477행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `1e92cc7499ef0415f6dd0ec027145372`

~~~~text
theorem fixed_omega_sigma3_omega :
    omegaSigma3Omega fixedSigma fixedOmega = -210 := by native_decide
~~~~

<a id="role-4f89926dafd5a4e5"></a>
## role-4f89926dafd5a4e5 — PR257Orbit.fixed_beta_krylov_gram

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 480–483행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `46356c54635a35fa034f6ffc99e9c023`

~~~~text
theorem fixed_beta_krylov_gram :
    det (gramMatrix fixedBeta (mv fixedSigma fixedBeta)
      (mv fixedSigma (mv fixedSigma fixedBeta))) = 400 := by native_decide

~~~~

<a id="role-d0bc832cd16439b6"></a>
## role-d0bc832cd16439b6 — PR257Orbit.generic_separation_not_promoted

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/generated/pr257_lowell_morphology/axes/lean/PR257OrbitAxis.lean` 524–526행
- 내용 버전: `89e6f7e4158548c8392826fec06b389223f0ccb71c061b2b14c7f18dfeccfcb2:ad208a43`; 관찰 커밋: `81ab84fc4286fca016243405563be30d3ce4b6c4`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `7c94965800f0797eafe0446452c477d5`

~~~~text
theorem generic_separation_not_promoted :
    genericOrbitSeparationStatus = .UNPROVEN := rfl

~~~~

<a id="role-6b1cc934d6442123"></a>
## role-6b1cc934d6442123 — genuine multi-ℓ Fisher–CR floor `σ(F)/F ≥ [Σ(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`, strictly below 0.632; MLE-achievable

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 11–11행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-A1 ★ | genuine multi-ℓ Fisher–CR floor `σ(F)/F ≥ [Σ(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`, strictly below 0.632; MLE-achievable | `obsstat/egs2_fisher.py` | `test_egs2_fisher_bracket::FisherFloorTests` | provable |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-8dfb98e500689127"></a>
## role-8dfb98e500689127 — genuine multi-ℓ Fisher–CR floor `σ(F)/F ≥ [Σ(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`, strictly below 0.632; MLE-achievable

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 11–11행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-A1 ★ | genuine multi-ℓ Fisher–CR floor `σ(F)/F ≥ [Σ(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`, strictly below 0.632; MLE-achievable | `obsstat/egs2_fisher.py` | `test_egs2_fisher_bracket::FisherFloorTests` | provable |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-10d285406308aea0"></a>
## role-10d285406308aea0 — Fisher information saturates beyond the octupole; `(a₂,a₃)` ≈ sufficient

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 12–12행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-A2 | Fisher information saturates beyond the octupole; `(a₂,a₃)` ≈ sufficient | `obsstat/egs2_fisher.py:octupole_sufficiency_tail` | `..::test_octupole_information_saturates` | conditional |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-6b1fad0c1d31eb87"></a>
## role-6b1fad0c1d31eb87 — Fisher tail beyond the octupole converges (strictly positive at every finite L); the former sufficiency reading is superseded by the PR-130 gate (`common/nt2_tail_convergence.py`)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 12–12행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-A2 | Fisher tail beyond the octupole converges (strictly positive at every finite L); the former sufficiency reading is superseded by the PR-130 gate (`common/nt2_tail_convergence.py`) | `obsstat/egs2_fisher.py:octupole_sufficiency_tail` | `..::test_octupole_information_saturates` | superseded_reading_pr130 |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-3536863e0c4ffe2d"></a>
## role-3536863e0c4ffe2d — two-sided bracket `a₂κ/(1+R_EGS) ≤ Σ ≤ C_up a₂` under H3; zero shear-filling excluded

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 13–13행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-B1 ★ | two-sided bracket `a₂κ/(1+R_EGS) ≤ Σ ≤ C_up a₂` under H3; zero shear-filling excluded | `obsstat/egs2_shear_bracket.py` | `..::TwoSidedBracketTests` | conditional |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-c95afc222e2c9f9a"></a>
## role-c95afc222e2c9f9a — two-sided bracket `a₂κ/(1+R_EGS) ≤ Σ ≤ C_up a₂` under H3; zero shear-filling excluded

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 13–13행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-B1 ★ | two-sided bracket `a₂κ/(1+R_EGS) ≤ Σ ≤ C_up a₂` under H3; zero shear-filling excluded | `obsstat/egs2_shear_bracket.py` | `..::TwoSidedBracketTests` | conditional |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-33345758e8f3d07c"></a>
## role-33345758e8f3d07c — `Π(z)` GR-sources `dG_F/dz` via `σ̇=−3Hσ+3H²Π`

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 14–14행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-B2 | `Π(z)` GR-sources `dG_F/dz` via `σ̇=−3Hσ+3H²Π` | `obsstat/egs2_transport.py:sourced_depth_transport` | `test_egs2_transport::SourcedTransportTests` | conditional |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-3f637b27f5339e43"></a>
## role-3f637b27f5339e43 — `Π(z)` GR-sources `dG_F/dz` via `σ̇=−3Hσ+3H²Π`

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 14–14행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-B2 | `Π(z)` GR-sources `dG_F/dz` via `σ̇=−3Hσ+3H²Π` | `obsstat/egs2_transport.py:sourced_depth_transport` | `test_egs2_transport::SourcedTransportTests` | conditional |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-f12d5a893f4aa25d"></a>
## role-f12d5a893f4aa25d — vorticity is a joint blind sector of CMB-T + radial velocity

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 15–15행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-B3 | vorticity is a joint blind sector of CMB-T + radial velocity | `obsstat/egs2_transport.py:vorticity_blind_sector` | `test_egs2_transport::BlindSectorTests` | provable |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-fc728f7c08d48203"></a>
## role-fc728f7c08d48203 — vorticity is a joint blind sector of CMB-T + radial velocity

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 15–15행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| NT2-B3 | vorticity is a joint blind sector of CMB-T + radial velocity | `obsstat/egs2_transport.py:vorticity_blind_sector` | `test_egs2_transport::BlindSectorTests` | provable |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-77672571814171b0"></a>
## role-77672571814171b0 — registered max-scan calibration (`p_global ≥ max p_local`, +1)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 24–24행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T1 | registered max-scan calibration (`p_global ≥ max p_local`, +1) | `obsstat/lowell_global_calibration.py` | next-runner `quadrupole_filling`/K1 max-scan |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-a17159f43c314b9b"></a>
## role-a17159f43c314b9b — registered max-scan calibration (`p_global ≥ max p_local`, +1)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 24–24행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T1 | registered max-scan calibration (`p_global ≥ max p_local`, +1) | `obsstat/lowell_global_calibration.py` | next-runner `quadrupole_filling`/K1 max-scan |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-5d02ec9580c69765"></a>
## role-5d02ec9580c69765 — rank-exact local/global identifiability

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 25–25행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T2 | rank-exact local/global identifiability | `htt/departure/paper_a_closure.py` | next-runner `response_rank` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-b0298b723669060a"></a>
## role-b0298b723669060a — rank-exact local/global identifiability

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 25–25행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T2 | rank-exact local/global identifiability | `htt/departure/paper_a_closure.py` | next-runner `response_rank` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-438b161913524945"></a>
## role-438b161913524945 — Boltzmann collision-gap memory bound (Grönwall; γ≤0 blocks "forgetting")

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 26–26행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T3 | Boltzmann collision-gap memory bound (Grönwall; γ≤0 blocks "forgetting") | `bass/kinetic/boltzmann_memory.py` | next-runner `kinetic_and_egs_gates` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-6a3f03553a20bee4"></a>
## role-6a3f03553a20bee4 — Boltzmann collision-gap memory bound (Grönwall; γ≤0 blocks "forgetting")

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 26–26행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T3 | Boltzmann collision-gap memory bound (Grönwall; γ≤0 blocks "forgetting") | `bass/kinetic/boltzmann_memory.py` | next-runner `kinetic_and_egs_gates` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-df57114df9892125"></a>
## role-df57114df9892125 — visibility-cancellation inverse-source no-go

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 27–27행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T4 | visibility-cancellation inverse-source no-go | `bass/kinetic/visibility_rigidity.py` | next-runner `kinetic_and_egs_gates` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-f5e716fd238f04c5"></a>
## role-f5e716fd238f04c5 — visibility-cancellation inverse-source no-go

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 27–27행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T4 | visibility-cancellation inverse-source no-go | `bass/kinetic/visibility_rigidity.py` | next-runner `kinetic_and_egs_gates` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-089336818369b1f6"></a>
## role-089336818369b1f6 — almost-EGS promotion gate (needs accel + ∇T + derivative + Weyl bounds)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 28–28행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T5 | almost-EGS promotion gate (needs accel + ∇T + derivative + Weyl bounds) | `bass/geometry/egs_rigidity.py` | next-runner `kinetic_and_egs_gates` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-1853f1e2a6406742"></a>
## role-1853f1e2a6406742 — almost-EGS promotion gate (needs accel + ∇T + derivative + Weyl bounds)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 28–28행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T5 | almost-EGS promotion gate (needs accel + ∇T + derivative + Weyl bounds) | `bass/geometry/egs_rigidity.py` | next-runner `kinetic_and_egs_gates` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-9fa88a8584960a22"></a>
## role-9fa88a8584960a22 — potential-flow curl non-identifiability

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 29–29행
- 내용 버전: `6a39ecaedd9f2c30c4cf9a096d7e542009045a50311cfb82e4b44785840584d2:d283db23`; 관찰 커밋: `373c4068049b6b2e05972af034457587530ee3f7`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T6 | potential-flow curl non-identifiability | `obsstat/affine_flow.py:curl_suppression_ensemble` | next-runner `synthetic_data_mechanics` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-eff6ad25f3eeb7bc"></a>
## role-eff6ad25f3eeb7bc — potential-flow curl non-identifiability

- 역할: 역할 판단 보류
- 출처: `docs/research_program/egs2/THEOREM_MAP.md` 29–29행
- 내용 버전: `346c1fb20b55c4dff8da78ad4e3a3569cd026306b5f70e8b4ed6107faefac07a:d283db23`; 관찰 커밋: `221b374bb912fdd8c7005ad857b5354d19a0ede4`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| T6 | potential-flow curl non-identifiability | `obsstat/affine_flow.py:curl_suppression_ensemble` | next-runner `synthetic_data_mechanics` |
~~~~

제안 의도 문맥 (`docs/research_program/egs2/THEOREM_MAP.md` 1–5행):

~~~~text
# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.
~~~~

<a id="role-b6cd7fef04e0bb47"></a>
## role-b6cd7fef04e0bb47 — identifiable subspace of `g=(Σ²,W²,Ω_tilt,Ω_k)` from {CMB-T, radial-v} is rank 2; `W²,Ω_k` in the joint null

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 11–11행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A1 ★ | identifiable subspace of `g=(Σ²,W²,Ω_tilt,Ω_k)` from {CMB-T, radial-v} is rank 2; `W²,Ω_k` in the joint null | `obsstat/egs3_graded_comparator.py` · `test_egs3_axis_a::A1*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-f7be82ba76146c63"></a>
## role-f7be82ba76146c63 — identifiable subspace of `g=(Σ²,W²,Ω_tilt,Ω_k)` from {CMB-T, radial-v} is rank 2; `W²,Ω_k` in the joint null

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 11–11행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A1 ★ | identifiable subspace of `g=(Σ²,W²,Ω_tilt,Ω_k)` from {CMB-T, radial-v} is rank 2; `W²,Ω_k` in the joint null | `obsstat/egs3_graded_comparator.py` · `test_egs3_axis_a::A1*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-5c74d4ea13cfeafd"></a>
## role-5c74d4ea13cfeafd — the NT2-A1 Fisher–CR floor is reparametrization-invariant → one floor bounds all five scalars

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 12–12행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A2 | the NT2-A1 Fisher–CR floor is reparametrization-invariant → one floor bounds all five scalars | `egs2_fisher` · `test_egs3_axis_a::A2*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-ecafb77c3220731c"></a>
## role-ecafb77c3220731c — the NT2-A1 Fisher–CR floor is reparametrization-invariant → one floor bounds all five scalars

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 12–12행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A2 | the NT2-A1 Fisher–CR floor is reparametrization-invariant → one floor bounds all five scalars | `egs2_fisher` · `test_egs3_axis_a::A2*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-7ba8532111bde00c"></a>
## role-7ba8532111bde00c — `Π` is a calibrated **e-value**: `E=1[x>t]/α`, null mean 1, Markov `P(E≥1/β)≤β`; S4 domination ⇒ conservative

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 13–13행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A3 | `Π` is a calibrated **e-value**: `E=1[x>t]/α`, null mean 1, Markov `P(E≥1/β)≤β`; S4 domination ⇒ conservative | `obsstat/egs3_calibration.py` · `A3*` | proved (MC) |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-efdc957e7f4d1194"></a>
## role-efdc957e7f4d1194 — `Π` is a calibrated **e-value**: `E=1[x>t]/α`, null mean 1, Markov `P(E≥1/β)≤β`; S4 domination ⇒ conservative

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 13–13행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A3 | `Π` is a calibrated **e-value**: `E=1[x>t]/α`, null mean 1, Markov `P(E≥1/β)≤β`; S4 domination ⇒ conservative | `obsstat/egs3_calibration.py` · `A3*` | proved (MC) |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-3ebfaddaa628b13f"></a>
## role-3ebfaddaa628b13f — `(a₂,a₃,dipole)` Rao-Blackwell-dominates any raw estimator (`Var_RB ≤ Var_raw`)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 14–14행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A4 | `(a₂,a₃,dipole)` Rao-Blackwell-dominates any raw estimator (`Var_RB ≤ Var_raw`) | `egs3_calibration.py` · `A4*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-4c8966cf7bd263e5"></a>
## role-4c8966cf7bd263e5 — `(a₂,a₃,dipole)` Rao-Blackwell-dominates any raw estimator (`Var_RB ≤ Var_raw`)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 14–14행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A4 | `(a₂,a₃,dipole)` Rao-Blackwell-dominates any raw estimator (`Var_RB ≤ Var_raw`) | `egs3_calibration.py` · `A4*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-4d0e8ab1bb16d455"></a>
## role-4d0e8ab1bb16d455 — semi-native shear→multipole transfer `r_ℓ`; the genuine floor is a **k-profile**, saturating at 0.632 for super-horizon shear and below at finite k

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 20–20행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B1 ★ | semi-native shear→multipole transfer `r_ℓ`; the genuine floor is a **k-profile**, saturating at 0.632 for super-horizon shear and below at finite k | `bass/transfer/shear_quadrupole_seminative.py` · `test_egs3_axis_b::B1*` | proved (sharpens NT2-A1) |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-8eef1c6e0a1b7e0c"></a>
## role-8eef1c6e0a1b7e0c — semi-native shear→multipole transfer `r_ℓ`; the genuine floor is a **k-profile**, saturating at 0.632 for super-horizon shear and below at finite k

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 20–20행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B1 ★ | semi-native shear→multipole transfer `r_ℓ`; the genuine floor is a **k-profile**, saturating at 0.632 for super-horizon shear and below at finite k | `bass/transfer/shear_quadrupole_seminative.py` · `test_egs3_axis_b::B1*` | proved (sharpens NT2-A1) |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-5387340246348d70"></a>
## role-5387340246348d70 — depth gap is a **Volterra functional** of `Π` with kernel `exp(−3∫H)`; verified == ODE + Grönwall

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 21–21행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B2 | depth gap is a **Volterra functional** of `Π` with kernel `exp(−3∫H)`; verified == ODE + Grönwall | `obsstat/egs3_volterra_memory.py` · `B2*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-91a5d12039be0c5e"></a>
## role-91a5d12039be0c5e — depth gap is a **Volterra functional** of `Π` with kernel `exp(−3∫H)`; verified == ODE + Grönwall

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 21–21행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B2 | depth gap is a **Volterra functional** of `Π` with kernel `exp(−3∫H)`; verified == ODE + Grönwall | `obsstat/egs3_volterra_memory.py` · `B2*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-7f49db886d105c84"></a>
## role-7f49db886d105c84 — vorticity re-opens in the **transverse** velocity channel (`n·Ω·m≠0`, rank 3); CMB B-modes named

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 22–22행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B3 | vorticity re-opens in the **transverse** velocity channel (`n·Ω·m≠0`, rank 3); CMB B-modes named | `obsstat/egs3_vorticity_channels.py` · `B3*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-f4af788f176b8ead"></a>
## role-f4af788f176b8ead — vorticity re-opens in the **transverse** velocity channel (`n·Ω·m≠0`, rank 3); CMB B-modes named

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 22–22행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B3 | vorticity re-opens in the **transverse** velocity channel (`n·Ω·m≠0`, rank 3); CMB B-modes named | `obsstat/egs3_vorticity_channels.py` · `B3*` | proved |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-5e8d89665f9ac8c1"></a>
## role-5e8d89665f9ac8c1 — covariant bracket constants: H3 coefficient `κ/(1+R)`, nondegeneracy `C_up κ(1+R)>1` (κ=4/21,C_up=9)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 23–23행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B4 | covariant bracket constants: H3 coefficient `κ/(1+R)`, nondegeneracy `C_up κ(1+R)>1` (κ=4/21,C_up=9) | `wolfram/egs3_bracket_constants.wls` · `make egs3-wolfram` | symbolic PASS |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-b78fce37349e2480"></a>
## role-b78fce37349e2480 — covariant bracket constants: H3 coefficient `κ/(1+R)`, nondegeneracy `C_up κ(1+R)>1` (κ=4/21,C_up=9)

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 23–23행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: 원문 후보 문서의 개별 표/행이다. 원문의 proved/conditional/forecast 표기는 전사한 맥락이며 본 작업의 검증 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B4 | covariant bracket constants: H3 coefficient `κ/(1+R)`, nondegeneracy `C_up κ(1+R)>1` (κ=4/21,C_up=9) | `wolfram/egs3_bracket_constants.wls` · `make egs3-wolfram` | symbolic PASS |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-2b1083e744bba08d"></a>
## role-2b1083e744bba08d — K1 **global** p on public Planck FFP10/NPIPE E2E (max-scan)

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 29–29행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C1 ★ | K1 **global** p on public Planck FFP10/NPIPE E2E (max-scan) | `lowell_global_calibration.e2e_maxscan_from_summaries` | ticket `tickets/k1_ffp10_npipe.yaml` |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-53250d9d814e8eb0"></a>
## role-53250d9d814e8eb0 — K1 **global** p on public Planck FFP10/NPIPE E2E (max-scan)

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 29–29행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C1 ★ | K1 **global** p on public Planck FFP10/NPIPE E2E (max-scan) | `lowell_global_calibration.e2e_maxscan_from_summaries` | ticket `tickets/k1_ffp10_npipe.yaml` |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-181be05a6b454b36"></a>
## role-181be05a6b454b36 — K6/K5 posteriors via Hoffman–Ribak CR + WF/CR forward mocks

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 30–30행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C2 | K6/K5 posteriors via Hoffman–Ribak CR + WF/CR forward mocks | `constrained_realizations.curl_posterior`, `bulkflow_mle.hierarchical_coverage_experiment` | ticket `tickets/cf4_wfcr.yaml` |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-5d75dea049160940"></a>
## role-5d75dea049160940 — K6/K5 reconstruction and mock mechanics

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 30–30행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C2 | K6/K5 reconstruction and mock mechanics | `constrained_realizations.curl_posterior`, `bulkflow_mle.hierarchical_coverage_experiment` | quarantined while CF4 P0 findings are OPEN; synthetic mechanics only |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-ca50903fafc3446c"></a>
## role-ca50903fafc3446c — graded-comparator joint pushforward: synthetic rank witness + proven 2-sector no-go

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 31–31행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C3 | graded-comparator joint pushforward: synthetic rank witness + proven 2-sector no-go | `egs3_graded_comparator` | observational promotion blocked by `N-DATA-CF4-DOWNSTREAM` |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-e1494114aa4df2f6"></a>
## role-e1494114aa4df2f6 — graded-comparator joint pushforward: measured rank-2 sectors + proven 2-sector no-go

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 31–31행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C3 | graded-comparator joint pushforward: measured rank-2 sectors + proven 2-sector no-go | `egs3_graded_comparator` on K1/K4/K5/K6 | runnable once C1/C2 land |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-245001b3eb2c6bc9"></a>
## role-245001b3eb2c6bc9 — independent 2MRS cross-reconstruction (no covariance merge)

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 32–32행
- 내용 버전: `5592027a896d761afade914f82b7879195a8aef2b5e04655ff1f10bdef81f6eb:dd0517db`; 관찰 커밋: `2fb6d89d202e14bce3c238e68a15d16c22d7eb8c`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C4 | independent 2MRS cross-reconstruction (no covariance merge) | `../pr07/PR08-005...` | contract |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-9a86fa3773ae081b"></a>
## role-9a86fa3773ae081b — independent 2MRS cross-reconstruction (no covariance merge)

- 역할: 독립 명제가 아닌 검색 조각
- 출처: `docs/research_program/egs3/THEOREM_CANDIDATES.md` 32–32행
- 내용 버전: `9bdab9a3b04f0332101f8eb11d9416dd7358a43b38d6e90729c148df10304da2:dd0517db`; 관찰 커밋: `1650fbcccab4fc7fcfb84abc89c85e5b0631d5ea`
- 이유: EGS3 Axis C의 데이터 실행·교차재구성 티켓이다. 구체적인 수학 정리의 진술로 세지 않는다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| C4 | independent 2MRS cross-reconstruction (no covariance merge) | `../pr07/PR08-005...` | contract |
~~~~

제안 의도 문맥 (`docs/research_program/egs3/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).
~~~~

<a id="role-5e0368b7bb950239"></a>
## role-5e0368b7bb950239 — whitened stacked response blocks have rank = identifiable dimension; a duplicate block adds zero rank, nullspace = (x,−x) line

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 17–17행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-rank (response identifiability) | whitened stacked response blocks have rank = identifiable dimension; a duplicate block adds zero rank, nullspace = (x,−x) line | `test_pr04_response::test_full_and_duplicate_rank` | `A-rank` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-65b225587cd9ff86"></a>
## role-65b225587cd9ff86 — whitened stacked response blocks have rank = identifiable dimension; a duplicate block adds zero rank, nullspace = (x,−x) line

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 17–17행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-rank (response identifiability) | whitened stacked response blocks have rank = identifiable dimension; a duplicate block adds zero rank, nullspace = (x,−x) line | `test_pr04_response::test_full_and_duplicate_rank` | `A-rank` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-6c7ae5cc00c4c60c"></a>
## role-6c7ae5cc00c4c60c — projecting out a nuisance equal to a response block removes exactly that block's rank

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 18–18행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-nuisance | projecting out a nuisance equal to a response block removes exactly that block's rank | `test_pr04_response::test_nuisance_removes_exact_block` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-9c5b0c34f10410d6"></a>
## role-9c5b0c34f10410d6 — projecting out a nuisance equal to a response block removes exactly that block's rank

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 18–18행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-nuisance | projecting out a nuisance equal to a response block removes exactly that block's rank | `test_pr04_response::test_nuisance_removes_exact_block` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-3e3ec1e7e9853c33"></a>
## role-3e3ec1e7e9853c33 — identical response subspaces have zero principal angles

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 19–19행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-angles | identical response subspaces have zero principal angles | `test_pr04_response::test_principal_angle_identical` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-c96ba4262e6fb8af"></a>
## role-c96ba4262e6fb8af — identical response subspaces have zero principal angles

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 19–19행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-angles | identical response subspaces have zero principal angles | `test_pr04_response::test_principal_angle_identical` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-2662d70806affc70"></a>
## role-2662d70806affc70 — adding complementary blocks gains rank monotonically until the design is identifiable

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 20–20행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-ladder (complementary-channel sufficiency) | adding complementary blocks gains rank monotonically until the design is identifiable | `test_pr04_response::test_rank_ladder` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-c07a70c12df0b0cd"></a>
## role-c07a70c12df0b0cd — adding complementary blocks gains rank monotonically until the design is identifiable

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 20–20행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-ladder (complementary-channel sufficiency) | adding complementary blocks gains rank monotonically until the design is identifiable | `test_pr04_response::test_rank_ladder` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-8095f9af3bc1456f"></a>
## role-8095f9af3bc1456f — flat-FLRW comoving congruence has θ = 3H and zero shear/acceleration

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 21–21행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-flrw (congruence limit) | flat-FLRW comoving congruence has θ = 3H and zero shear/acceleration | `test_pr04_congruence::test_flat_flrw_limit` | `A-flrw` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-83436942fa563cd6"></a>
## role-83436942fa563cd6 — flat-FLRW comoving congruence has θ = 3H and zero shear/acceleration

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 21–21행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-flrw (congruence limit) | flat-FLRW comoving congruence has θ = 3H and zero shear/acceleration | `test_pr04_congruence::test_flat_flrw_limit` | `A-flrw` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-2f2ef2cace5ec264"></a>
## role-2f2ef2cace5ec264 — inertial Minkowski congruence has θ = σ = ω = a = 0

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 22–22행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-minkowski | inertial Minkowski congruence has θ = σ = ω = a = 0 | `test_pr04_congruence::test_minkowski_inertial` | (limit of A-flrw) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-bdaab5b23d220ef0"></a>
## role-bdaab5b23d220ef0 — inertial Minkowski congruence has θ = σ = ω = a = 0

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 22–22행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-minkowski | inertial Minkowski congruence has θ = σ = ω = a = 0 | `test_pr04_congruence::test_minkowski_inertial` | (limit of A-flrw) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-45678a721d4676fb"></a>
## role-45678a721d4676fb — two non-collinear boosts compose to an exact Lorentz map whose velocity ≠ Euclidean sum

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 23–23행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-wigner (rapidity non-additivity) | two non-collinear boosts compose to an exact Lorentz map whose velocity ≠ Euclidean sum | `test_pr04_congruence::test_noncollinear_boost_is_lorentz` | `A-wigner` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-7ca1f067095b8db2"></a>
## role-7ca1f067095b8db2 — two non-collinear boosts compose to an exact Lorentz map whose velocity ≠ Euclidean sum (PR07-002: **not** a Wigner-angle claim)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 23–23행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-boost (composition) | two non-collinear boosts compose to an exact Lorentz map whose velocity ≠ Euclidean sum (PR07-002: **not** a Wigner-angle claim) | `test_pr07_paper_a::test_boost_and_first_jet_split` | `A_boost` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-193cf5aa11cf6582"></a>
## role-193cf5aa11cf6582 — equality of pointwise four-velocity does not determine its first derivative (split from A-boost, PR07-002)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 24–24행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-first-jet (no-go) | equality of pointwise four-velocity does not determine its first derivative (split from A-boost, PR07-002) | `test_pr07_paper_a::test_boost_and_first_jet_split` | `first_jet_*` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-a2387502183a3d86"></a>
## role-a2387502183a3d86 — a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 24–24행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-failclosed | a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed | `test_pr04_congruence::test_incomplete_normalization_fails` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-97a0b8cb16ac7911"></a>
## role-97a0b8cb16ac7911 — a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 25–25행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-failclosed | a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed | `test_pr04_congruence::test_incomplete_normalization_fails` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-b542c38804a94bb0"></a>
## role-b542c38804a94bb0 — a purely radial response design places vorticity in the data nullspace

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 25–25행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-radial-novortex (radial-vorticity no-go) | a purely radial response design places vorticity in the data nullspace | (rank machinery: `audit_response_blocks`) | — | corollary (proof review) |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-702c0ab7fa7f2065"></a>
## role-702c0ab7fa7f2065 — a purely radial response design places vorticity in the data nullspace, `nᵃΩ_ab nᵇ=0`

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 26–26행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-radial-novortex (radial-vorticity no-go) | a purely radial response design places vorticity in the data nullspace, `nᵃΩ_ab nᵇ=0` | `test_pr07_paper_a::test_radial_vorticity_no_go` | `radial_vorticity_zero` | **closed PR07-004** ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-a6bbc4c424000918"></a>
## role-a6bbc4c424000918 — a single-shell response is rank-deficient for the joint bulk/shear/curl design

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 26–26행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-single-shell-degeneracy | a single-shell response is rank-deficient for the joint bulk/shear/curl design | (rank machinery: `rank_gain_ladder`) | — | corollary (proof review) |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-337c3be914eea306"></a>
## role-337c3be914eea306 — the dynamic tensor design recovers rank only with independent temporal kernels

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 27–27행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-temporal-tensor-rank | the dynamic tensor design recovers rank only with independent temporal kernels | (rank machinery) | — | corollary (proof review; ties to LR-06G) |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-e891bbbd9558a518"></a>
## role-e891bbbd9558a518 — one shell → rank 3; broad depth support → rank 6

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 27–27행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-single-shell-degeneracy | one shell → rank 3; broad depth support → rank 6 | `test_pr07_paper_a::test_single_shell_degeneracy_and_broad_depth_recovery` | — | **closed PR07-004** ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-4397fa52828cb13b"></a>
## role-4397fa52828cb13b — `rank(T ⊗ I₅) = 5·rank(T)` (independent temporal kernels)

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 28–28행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-temporal-tensor-rank | `rank(T ⊗ I₅) = 5·rank(T)` (independent temporal kernels) | `test_pr07_paper_a::test_temporal_tensor_rank` | — | **closed PR07-004** ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-f7fd4ba93addd172"></a>
## role-f7fd4ba93addd172 — duplicate-block null-space equals the (x,−x) line **only** under full column rank

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 29–29행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-rank-equality-qualifier | duplicate-block null-space equals the (x,−x) line **only** under full column rank | `test_pr07_paper_a::test_duplicate_rank_not_full_column_rank` | — | **closed PR07-002/004** ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-eec1ee2728450f76"></a>
## role-eec1ee2728450f76 — an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 41–41행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-codazzi (flux balance) | an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0 | `test_pr04_bianchi::test_counterstream_codazzi` | (numeric; flux algebra) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-2a401b0884d24e39"></a>
## role-2a401b0884d24e39 — a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 42–42행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-nonsuff (scalar nonclosure) | a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π | `test_pr04_bianchi::test_scalar_non_sufficiency` | `B-nonsuff` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-b5b0ee1edd374e63"></a>
## role-b5b0ee1edd374e63 — every PSD second moment K realizes as a sum of antipodal eigen-pairs e eᵀ, each with zero first moment

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 43–43행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-psd (PSD moment cone) | every PSD second moment K realizes as a sum of antipodal eigen-pairs e eᵀ, each with zero first moment | `test_pr04_bianchi::test_psd_pair_decomposition` | `B-psd` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-90fde66702e29ad2"></a>
## role-90fde66702e29ad2 — a(t) = (1 + 3H₀t/2)^(2/3) gives H = H₀/(1+3H₀t/2), Ḣ = −(3/2)H² and an exactly preserved Gauss constraint; the RK4 integrator reproduces it to ~2e-9

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 44–44행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-dust (exact FLRW oracle + Gauss transport) | a(t) = (1 + 3H₀t/2)^(2/3) gives H = H₀/(1+3H₀t/2), Ḣ = −(3/2)H² and an exactly preserved Gauss constraint; the RK4 integrator reproduces it to ~2e-9 | `test_pr04_bianchi::test_dust_flrw_limit` | `B-dust` | symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-d4f0028131f33f66"></a>
## role-d4f0028131f33f66 — shear obeys σ̇ = STF(−3Hσ + κΠ); d(σ̇)/dΠ = κ ≠ 0, so ablating the anisotropic stress changes the shear history

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 45–45행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-shear (shear memory) | shear obeys σ̇ = STF(−3Hσ + κΠ); d(σ̇)/dΠ = κ ≠ 0, so ablating the anisotropic stress changes the shear history | `test_pr04_bianchi::test_pi_ablation_changes_shear` | `B-shear` | symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-4ec4d1d5c4dc1820"></a>
## role-4ec4d1d5c4dc1820 — each species obeys the tilted continuity + Euler RHS; total flux is the Codazzi source

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 46–46행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-conservation (species continuity/Euler) | each species obeys the tilted continuity + Euler RHS; total flux is the Codazzi source | (`dynamics.rhs`, `constraint_residuals`) | — | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-2dd1fbea072ed1ec"></a>
## role-2dd1fbea072ed1ec — the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 47–47행
- 내용 버전: `b9b25b01062a23fc3549769045f25adef43bfa85d581f6b537a0acfbda0682da:d283db23`; 관찰 커밋: `0139f9691a17098b22f185f276660ed552418c64`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-pushforward (fail-closed reporting) | the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator | `test_pr04_pushforward::*` | — | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-4cfb59395ee7dd41"></a>
## role-4cfb59395ee7dd41 — an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 47–47행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-codazzi (flux balance) | an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0 | `test_pr04_bianchi::test_counterstream_codazzi` | (numeric; flux algebra) | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-6b4d74bf6e5a2191"></a>
## role-6b4d74bf6e5a2191 — a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 48–48행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-nonsuff (scalar nonclosure) | a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π | `test_pr04_bianchi::test_scalar_non_sufficiency` | `B-nonsuff` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-a5811cfec9b46c32"></a>
## role-a5811cfec9b46c32 — every PSD second moment K realizes as a sum of antipodal eigen-pairs e eᵀ, each with zero first moment

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 49–49행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-psd (PSD moment cone) | every PSD second moment K realizes as a sum of antipodal eigen-pairs e eᵀ, each with zero first moment | `test_pr04_bianchi::test_psd_pair_decomposition` | `B-psd` | symbolic ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-8bdaa0df795b4bae"></a>
## role-8bdaa0df795b4bae — a(t) = (1 + 3H₀t/2)^(2/3) gives H = H₀/(1+3H₀t/2), Ḣ = −(3/2)H² and an exactly preserved Gauss constraint; the RK4 integrator reproduces it to ~2e-9

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 50–50행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-dust (exact FLRW oracle + Gauss transport) | a(t) = (1 + 3H₀t/2)^(2/3) gives H = H₀/(1+3H₀t/2), Ḣ = −(3/2)H² and an exactly preserved Gauss constraint; the RK4 integrator reproduces it to ~2e-9 | `test_pr04_bianchi::test_dust_flrw_limit` | `B-dust` | symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-c3bd3dbc5af79256"></a>
## role-c3bd3dbc5af79256 — shear obeys σ̇ = STF(−3Hσ + κΠ); d(σ̇)/dΠ = κ ≠ 0, so ablating the anisotropic stress changes the shear history

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 51–51행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-shear (shear memory) | shear obeys σ̇ = STF(−3Hσ + κΠ); d(σ̇)/dΠ = κ ≠ 0, so ablating the anisotropic stress changes the shear history | `test_pr04_bianchi::test_pi_ablation_changes_shear` | `B-shear` | symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-abfdefd29e2f6e1a"></a>
## role-abfdefd29e2f6e1a — each species obeys the tilted continuity + Euler RHS; total flux is the Codazzi source

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 52–52행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-conservation (species continuity/Euler) | each species obeys the tilted continuity + Euler RHS; total flux is the Codazzi source | (`dynamics.rhs`, `constraint_residuals`) | — | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-5a39d4fa821a507a"></a>
## role-5a39d4fa821a507a — the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator

- 역할: 역할 판단 보류
- 출처: `docs/research_program/pr04/PAPER_THEOREM_MAP.md` 53–53행
- 내용 버전: `2598cecf4ba98538b5b382424aacd85d0a03413b4aa4b8a2790e39346d5fa6ee:d283db23`; 관찰 커밋: `0b2f82834fdb484dd84a74107b827808a824f37d`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-pushforward (fail-closed reporting) | the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator | `test_pr04_pushforward::*` | — | numeric ✓ |
~~~~

제안 의도 문맥 (`docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-093c5a1eb17fd09f"></a>
## role-093c5a1eb17fd09f — T1. Rank-Aware Comparator Identifiability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 7–29행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T1. Rank-Aware Comparator Identifiability

Statement candidate:

Let `R: Theta -> X` be the registered linearized response map from physical sectors to observable features after masking, nuisance projection, and fixed preprocessing. Then only `im(R)` is identifiable from the feature vector without additional prior information. Components in `ker(R)` are blind sectors. Any scalar comparator `x_C = c^T theta` is data-identified only through its projection onto `row(R)`.

Strong consequence:

- A rank-2 reachable comparator plus named blind sectors is a positive result, not a failed detection.
- Missing sectors cannot be set to zero in PR08-006.

Numerical witness:

- simulate a response matrix with two reachable columns and two blind columns;
- verify rank, null columns, and row-space projection;
- verify local/global response-overlap after nuisance projection.

Executable hook:

```bash
venv/bin/python docs/research_program/publishable_analysis_pack_2026-06-26/scripts/candidate_experiments.py --experiment rank_evalue
```

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-f4622347eaae21e9"></a>
## role-f4622347eaae21e9 — T2. Mixture E-Value Calibration For Registered Look-Elsewhere Scans

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 30–46행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T2. Mixture E-Value Calibration For Registered Look-Elsewhere Scans

Statement candidate:

If `E_j >= 0` are registered null e-values with `E_0[E_j] <= 1`, then any convex mixture `E_mix = sum_j w_j E_j`, `w_j >= 0`, `sum_j w_j = 1`, is an e-value. Therefore `P_0(E_mix >= 1/alpha) <= alpha`. This supports a registered low-ell max/mixture scan without pretending the selected statistic was fixed after seeing data.

Strong consequence:

- K1 can make a global calibration claim after FFP10/NPIPE E2E summaries are bound.
- The result is not a family/classification claim.

Numerical witness:

- simulate null e-values with unit mean;
- verify empirical threshold exceedances stay near the Markov envelope;
- report finite-sample uncertainty separately.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-c4368b5dcc44c6f5"></a>
## role-c4368b5dcc44c6f5 — T3. Finite-Mock Coverage Decomposition

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 47–57행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### T3. Finite-Mock Coverage Decomposition

Statement candidate:

For release-matched mocks, bulk-flow uncertainty decomposes into measurement variance plus cosmic-variance coverage only if the mocks share the release selection, frame, distance-error model, and estimator. A self-injection or non-release mock cannot estimate the same coverage functional.

Strong consequence:

- K5 can publish a coverage result once mock ownership is present.
- Without release-matched mocks, only mechanics and diagnostics are claimable.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-dd7947c201aa2683"></a>
## role-dd7947c201aa2683 — G1. Visibility-Weighted Boltzmann Transfer Contraction

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 60–94행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### G1. Visibility-Weighted Boltzmann Transfer Contraction

Statement candidate:

For a single shear-sourced low-ell mode with source `S(eta)` and normalized visibility `g(eta)`, the line-of-sight response

```text
T_l(k) = integral g(eta) S(eta) j_l(k(eta0 - eta)) d eta
```

obeys

```text
|T_l(k)| <= integral g(eta) |S(eta)| d eta
```

because `|j_l(x)| <= 1`. For `l > 0`, the superhorizon response has the expected small-`k` scaling from the spherical-Bessel expansion. This is a direct Boltzmann-equation transfer statement for the single-mode bridge, not a native atlas.

Strong consequence:

- The semi-native single-mode transfer can support bounded low-ell response profiles.
- It cannot support native-atlas-dependent family/classification language.

Numerical witness:

- evaluate `T_2(k)` and `T_3(k)` over a registered `k` grid;
- verify the contraction bound;
- verify small-`k` scaling ratios.

Executable hook:

```bash
venv/bin/python docs/research_program/publishable_analysis_pack_2026-06-26/scripts/candidate_experiments.py --experiment boltzmann_visibility
```

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-5a0398b9267a2744"></a>
## role-5a0398b9267a2744 — G2. Volterra Depth-Memory Stability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 95–110행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### G2. Volterra Depth-Memory Stability

Statement candidate:

For a depth response `F(z)` obeying a first-order relaxation equation with source `Pi(z)`, the Volterra integral representation with positive damping kernel is equivalent to the ODE solution and has Gronwall-stable perturbation bounds. If the source is depth-steady, the normalized depth gap is unity; sign-definite depth growth creates a non-unit gap.

Strong consequence:

- `G_F` is a meaningful depth-memory diagnostic when depth bins, covariance, and null status are recorded.
- It is not by itself a global-tilt evidence term.

Numerical witness:

- solve ODE and Volterra forms on the same grid;
- check max discrepancy and gap monotonicity.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-a2bd0d37845fc770"></a>
## role-a2bd0d37845fc770 — G3. Radial Vorticity Blindness And Transverse Reopening

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 111–121행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### G3. Radial Vorticity Blindness And Transverse Reopening

Statement candidate:

For antisymmetric vorticity tensor `Omega_ij`, radial velocity projection satisfies `n_i Omega_ij n_j = 0` for every line of sight `n`. Therefore a radial-only field is structurally blind to that sector, while a transverse or affine realization channel can reopen rank.

Strong consequence:

- K6 must use realization-conditioned field information, not a curl-suppressed point field.
- A no-go result is publishable if the field owner only supplies curl-suppressed reconstructions.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-0fa11bca7b5265c1"></a>
## role-0fa11bca7b5265c1 — D1. K1 Public E2E Global Calibration

- 역할: 역할 판단 보류
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 124–133행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 제안서의 데이터 관측 결과 목표다. 정리·증명 목표와 구별하며 수학 명제로의 정식화는 미확인이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### D1. K1 Public E2E Global Calibration

Statement candidate after exit gate:

The registered K1 low-ell morphology statistic has global rank `p` under the matched public E2E simulation ensemble and frozen max-scan configuration.

Blocked until:

- FFP10/NPIPE input manifests and per-simulation summaries are bound.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-13993aa53b93521c"></a>
## role-13993aa53b93521c — D2. K5 Release-Matched Cosmic-Variance Coverage

- 역할: 역할 판단 보류
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 134–143행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 제안서의 데이터 관측 결과 목표다. 정리·증명 목표와 구별하며 수학 명제로의 정식화는 미확인이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### D2. K5 Release-Matched Cosmic-Variance Coverage

Statement candidate after exit gate:

The CF4 bulk-flow apex/depth estimator has component and amplitude coverage under release-matched forward mocks, with bias and frame/depth ablations reported.

Blocked until:

- release-matched mock ownership exists.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-c355b8946b1a459b"></a>
## role-c355b8946b1a459b — D3. K6 Realization-Conditioned Curl Posterior Or Structural No-Go

- 역할: 역할 판단 보류
- 출처: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 144–153행
- 내용 버전: `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; 관찰 커밋: `058a6f1c1d9f7e6ea2ec46adc68d6160a55084f4`
- 이유: 제안서의 데이터 관측 결과 목표다. 정리·증명 목표와 구별하며 수학 명제로의 정식화는 미확인이다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### D3. K6 Realization-Conditioned Curl Posterior Or Structural No-Go

Statement candidate after exit gate:

The CF4 field-realization ensemble gives a realization-conditioned posterior for the affine curl sector, or the provided reconstruction is structurally curl-suppressed and no physical curl statement is available.

Blocked until:

- constrained 3D field realizations are bound.

~~~~

제안 의도 문맥 (`docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md` 1–5행):

~~~~text
# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis
~~~~

<a id="role-1c4d97828f9f1f38"></a>
## role-1c4d97828f9f1f38 — PR190NormalVorticity.registeredLowerW2Positive

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` 41–43행
- 내용 버전: `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2:ad208a43`; 관찰 커밋: `bae6ac2df15c95ee1e71a3e49b859c0added192d`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `dafb7e1931399b7d4ec40da14a1d588f`

~~~~text
theorem registeredLowerW2Positive : 0 < registeredLowerW2 := by
  norm_num [registeredLowerW2]

~~~~

같은 소스의 사용 문맥 (77–79행):

~~~~text
  · exact normalW2Zero
  · exact registeredLowerW2Positive
  · exact lowerEndpointSameFrameContradiction
~~~~

<a id="role-e1cdb3f8668b7482"></a>
## role-e1cdb3f8668b7482 — PR190NormalVorticity.registeredInteriorW2Positive

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` 49–51행
- 내용 버전: `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2:ad208a43`; 관찰 커밋: `bae6ac2df15c95ee1e71a3e49b859c0added192d`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `cf5e0540e3ba68dd0bce6efeccbc0d0a`

~~~~text
theorem registeredInteriorW2Positive : 0 < registeredInteriorW2 := by
  norm_num [registeredInteriorW2]

~~~~

같은 소스의 사용 문맥 (79–81행):

~~~~text
  · exact lowerEndpointSameFrameContradiction
  · exact registeredInteriorW2Positive
  · exact interiorEndpointSameFrameContradiction
~~~~

<a id="role-6b95388466ded315"></a>
## role-6b95388466ded315 — PR190NormalVorticity.refutedConstraintCannotPromote

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` 57–63행
- 내용 버전: `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2:ad208a43`; 관찰 커밋: `bae6ac2df15c95ee1e71a3e49b859c0added192d`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `618039ba02758f75d5d8e1c14a67e232`

~~~~text
theorem refutedConstraintCannotPromote
    (constraint localClaim globalClaim : Prop)
    (hConstraint : ¬ constraint) :
    ¬ (constraint ∧ localClaim ∧ globalClaim) := by
  intro h
  exact hConstraint h.1

~~~~

같은 소스의 사용 문맥 (81–83행):

~~~~text
  · exact interiorEndpointSameFrameContradiction
  · exact refutedConstraintCannotPromote

~~~~

<a id="role-7f78de30ea2fd284"></a>
## role-7f78de30ea2fd284 — PR190NormalVorticity.axisProofBundle

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/strengthening/pr190_cas/axes/lean/PR190NormalVorticityAxis.lean` 74–83행
- 내용 버전: `e9aecffac4f2a8012e14f0aa7cdaf28816e2bbb3a79d40b46bd268a8603314d2:ad208a43`; 관찰 커밋: `bae6ac2df15c95ee1e71a3e49b859c0added192d`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `82f85631e217d5d189a4f16ac454330c`

~~~~text
theorem axisProofBundle : AxisProofBundle := by
  constructor
  · exact normalSpatialVorticityZero
  · exact normalW2Zero
  · exact registeredLowerW2Positive
  · exact lowerEndpointSameFrameContradiction
  · exact registeredInteriorW2Positive
  · exact interiorEndpointSameFrameContradiction
  · exact refutedConstraintCannotPromote

~~~~

같은 소스의 사용 문맥 (83–85행):

~~~~text

#check PR190NormalVorticity.axisProofBundle

~~~~

<a id="role-9122c8dc857ac1c9"></a>
## role-9122c8dc857ac1c9 — PR270PillarT.Vec3.extensionality

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 43–49행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `c13dfac898ca749fa37a2d2e4b131a93`

~~~~text
theorem Vec3.extensionality {u v : Vec3}
    (hx : u.x = v.x) (hy : u.y = v.y) (hz : u.z = v.z) : u = v := by
  cases u
  cases v
  simp_all

@[ext]
~~~~

같은 소스의 사용 문맥 (49–51행):

~~~~text
@[ext]
theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
~~~~

<a id="role-49cd275c7bebcb32"></a>
## role-49cd275c7bebcb32 — PR270PillarT.Vec3.extensionality

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 44–49행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `0a9e1210e511475656496e95b483b0e5`

~~~~text
theorem Vec3.extensionality {u v : Vec3}
    (hx : u.x = v.x) (hy : u.y = v.y) (hz : u.z = v.z) : u = v := by
  cases u
  cases v
  grind

~~~~

같은 소스의 사용 문맥 (49–51행):

~~~~text

theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
~~~~

<a id="role-19d44973006455ca"></a>
## role-19d44973006455ca — PR270PillarT.Mat3.extensionality

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 50–59행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `6bba02acf901de45f8b7880d578542de`

~~~~text
theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
    (h02 : A.m02 = B.m02) (h10 : A.m10 = B.m10)
    (h11 : A.m11 = B.m11) (h12 : A.m12 = B.m12)
    (h20 : A.m20 = B.m20) (h21 : A.m21 = B.m21)
    (h22 : A.m22 = B.m22) : A = B := by
  cases A
  cases B
  simp_all

~~~~

같은 소스의 사용 문맥 (137–139행):

~~~~text
  rw [stf_tr2_half, stf_tr3_third]
  apply Mat3.extensionality <;>
    simp [stf, mm, madd, mscale, stfQ2, stfQ3, ident] <;> ring
~~~~

<a id="role-d696e5d9eee8b5cc"></a>
## role-d696e5d9eee8b5cc — PR270PillarT.Mat3.extensionality

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 50–59행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `b8ed2570c8a81ba0eeb7afab2306ab01`

~~~~text
theorem Mat3.extensionality {A B : Mat3}
    (h00 : A.m00 = B.m00) (h01 : A.m01 = B.m01)
    (h02 : A.m02 = B.m02) (h10 : A.m10 = B.m10)
    (h11 : A.m11 = B.m11) (h12 : A.m12 = B.m12)
    (h20 : A.m20 = B.m20) (h21 : A.m21 = B.m21)
    (h22 : A.m22 = B.m22) : A = B := by
  cases A
  cases B
  grind

~~~~

같은 소스의 사용 문맥 (135–137행):

~~~~text
  rw [stf_tr2_half, stf_tr3_third]
  apply Mat3.extensionality <;>
    grind (ringSteps := 500000)
~~~~

<a id="role-4a1fc884e18cd9d2"></a>
## role-4a1fc884e18cd9d2 — PR270PillarT.mm_assoc

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 141–143행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `f0d64adf2896eaa3bf4bb6a192cc385f`

~~~~text
theorem mm_assoc (A B C : Mat3) : mm (mm A B) C = mm A (mm B C) := by
  apply Mat3.extensionality <;> simp [mm] <;> ring

~~~~

같은 소스의 사용 문맥 (164–166행):

~~~~text
  | succ n ih =>
      rw [Nat.add_succ, mpow, ih, mpow, mm_assoc]

~~~~

<a id="role-ca9f9390cfe0bcd3"></a>
## role-ca9f9390cfe0bcd3 — PR270PillarT.mm_ident_right

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 144–146행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `f2b72c4a0b85af2744bc9fc4d89447ff`

~~~~text
theorem mm_ident_right (A : Mat3) : mm A ident = A := by
  apply Mat3.extensionality <;> simp [mm, ident]

~~~~

같은 소스의 사용 문맥 (162–164행):

~~~~text
  | zero =>
      simp [mpow, mm_ident_right]
  | succ n ih =>
~~~~

<a id="role-5d649fc06b85ca5c"></a>
## role-5d649fc06b85ca5c — PR270PillarT.mm_add_right

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 147–150행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `87c44d8863450c637dd65ec481d1cde4`

~~~~text
theorem mm_add_right (A B C : Mat3) :
    mm A (madd B C) = madd (mm A B) (mm A C) := by
  apply Mat3.extensionality <;> simp [mm, madd] <;> ring

~~~~

같은 소스의 사용 문맥 (193–195행):

~~~~text
        (mscale (tr3 A / 3) (mpow A n)) := by
          rw [mm_add_right, mm_scale_right, mm_scale_right]
          simp only [mpow, mm_ident_right]
~~~~

<a id="role-0f50d87d035488fa"></a>
## role-0f50d87d035488fa — PR270PillarT.mm_scale_right

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 151–154행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `a5f10651c5fd9932ecd135a85442e077`

~~~~text
theorem mm_scale_right (A B : Mat3) (r : ℝ) :
    mm A (mscale r B) = mscale r (mm A B) := by
  apply Mat3.extensionality <;> simp [mm, mscale] <;> ring

~~~~

같은 소스의 사용 문맥 (193–195행):

~~~~text
        (mscale (tr3 A / 3) (mpow A n)) := by
          rw [mm_add_right, mm_scale_right, mm_scale_right]
          simp only [mpow, mm_ident_right]
~~~~

<a id="role-9cafecbfd2088d2d"></a>
## role-9cafecbfd2088d2d — PR270PillarT.mpow_add

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 159–166행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `506a305ba87cf2ffd49f6205f9cffd6d`

~~~~text
theorem mpow_add (A : Mat3) (m n : ℕ) :
    mpow A (m + n) = mm (mpow A m) (mpow A n) := by
  induction n with
  | zero =>
      simp [mpow, mm_ident_right]
  | succ n ih =>
      rw [Nat.add_succ, mpow, ih, mpow, mm_assoc]

~~~~

같은 소스의 사용 문맥 (185–187행):

~~~~text
    mpow A (n + 3) = mm (mpow A n) (mpow A 3) := by
      rw [mpow_add]
    _ = mm (mpow A n) (mm (mm A A) A) := by rw [mpow_three]
~~~~

<a id="role-41e43de30e93f1fc"></a>
## role-41e43de30e93f1fc — PR270PillarT.mpow_three

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 167–171행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 상위 증명에서 사용하는 행렬·벡터 대수, 유한 최댓값, 형 변환·순열의 기초 보조정리다. 선언과 같은 파일의 사용 문맥을 읽어 역할을 확인했다.
- 연결 항목: `72f87923c50f63361ba2f224776b98ac`

~~~~text
theorem mpow_three (A : Mat3) :
    mpow A 3 = mm (mm A A) A := by
  simp [mpow, mm, ident]

/-- VT-T6 contraction reduction for every power, not only one fixture. -/
~~~~

같은 소스의 사용 문맥 (186–188행):

~~~~text
      rw [mpow_add]
    _ = mm (mpow A n) (mm (mm A A) A) := by rw [mpow_three]
    _ = mm (mpow A n)
~~~~

<a id="role-0bbc1c32c57a71bb"></a>
## role-0bbc1c32c57a71bb — PR270PillarT.principalShapeFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 194–199행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `49ccdf7b2554c3106e4339442ff0e60f`

~~~~text
theorem principalShapeFixture :
    shearI2 (-2) 0 = 8 ∧
    shearI3 (-2) 0 = 0 ∧
    shearDelta (-2) 0 = 256 := by
  native_decide

~~~~

<a id="role-826ffd23784e383b"></a>
## role-826ffd23784e383b — PR270PillarT.principalKrylovFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 224–226행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `b35c16cdac698eda0ed672cd13613967`

~~~~text
theorem principalKrylovFixture :
    krylovDet (-2) 0 principalVector = 16 := by native_decide

~~~~

<a id="role-db12abf05c906134"></a>
## role-db12abf05c906134 — PR270PillarT.principalKrylovGramFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 227–232행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `aa98a5c33db50d14c6fde0d25cb40b65`

~~~~text
theorem principalKrylovGramFixture :
    det (gramMatrix principalVector
      (diagAction (-2) 0 principalVector)
      (diagAction (-2) 0 (diagAction (-2) 0 principalVector))) = 256 := by
  native_decide

~~~~

<a id="role-5e5523d32070e03c"></a>
## role-5e5523d32070e03c — PR270PillarT.principalShapeFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 251–256행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `0401389d847e7c872b1adb42730decc8`

~~~~text
theorem principalShapeFixture :
    shearI2 (-2) 0 = 8 ∧
    shearI3 (-2) 0 = 0 ∧
    shearDelta (-2) 0 = 256 := by
  norm_num [shearI2, shearI3, shearDelta, lambda3]

~~~~

<a id="role-8bbe946bd996637d"></a>
## role-8bbe946bd996637d — PR270PillarT.principalKrylovFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 304–307행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `1de18999a1708c50acde6a30433017be`

~~~~text
theorem principalKrylovFixture :
    krylovDet (-2) 0 principalVector = 16 := by
  norm_num [krylovDet, principalVector, diagAction, lambda3, det, fromCols]

~~~~

<a id="role-01f1dbdcf072d656"></a>
## role-01f1dbdcf072d656 — PR270PillarT.principalKrylovGramFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 308–313행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `383bd143543698b8af22f4a28a98fe95`

~~~~text
theorem principalKrylovGramFixture :
    det (gramMatrix principalVector
      (diagAction (-2) 0 principalVector)
      (diagAction (-2) 0 (diagAction (-2) 0 principalVector))) = 256 := by
  norm_num [principalVector, gramMatrix, diagAction, lambda3, dot, det]

~~~~

<a id="role-f28e24fa259ae425"></a>
## role-f28e24fa259ae425 — PR270PillarT.globalSeparationNotPromoted

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 330–332행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `5439c190fc25a7ab9b33ddf4d9e5d902`

~~~~text
theorem globalSeparationNotPromoted :
    globalOrbitStatus = .unproven := rfl

~~~~

<a id="role-69901122ab5f0dd5"></a>
## role-69901122ab5f0dd5 — PR270PillarT.sourceDecompositionNotPromoted

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 333–337행
- 내용 버전: `1060279ad973f754c85a9e5413d269b269facc6dea4b2f09cee8d0e3e73b872c:ad208a43`; 관찰 커밋: `f8370a440ba1aa395995d62153977b64eb589ee0`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `26a4e66f42ad973a5ef67d36583b8f4f`

~~~~text
theorem sourceDecompositionNotPromoted :
    sourceDecompositionStatus =
      .inconclusiveMissingTypedEvolutionLaw := rfl

end PR270PillarT
~~~~

<a id="role-c280a7b095310f58"></a>
## role-c280a7b095310f58 — PR270PillarT.globalSeparationNotPromoted

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 512–514행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `845317082e21bb3a5848e29dfa922963`

~~~~text
theorem globalSeparationNotPromoted :
    globalOrbitStatus = .unproven := rfl

~~~~

같은 소스의 사용 문맥 (584–586행):

~~~~text
  vtT8Principal := principalLocalChartJacobian
  vtT8NoGlobalPromotion := globalSeparationNotPromoted
  vtT13ChainRule := shapeChainRuleNumerator
~~~~

<a id="role-a13504c5b6f38efc"></a>
## role-a13504c5b6f38efc — PR270PillarT.sourceDecompositionNotPromoted

- 역할: 내부 보조명제·검증 보조정리
- 출처: `docs/research_program/vector_tensor/cas/axes/lean/PR270PillarTAxis.lean` 515–519행
- 내용 버전: `c38a5cfe77821baa037990b8459f90b0290cb3d0f504e9e1c794f9dc62829603:ad208a43`; 관찰 커밋: `f2e7059d96cf36d8e74be23adea757bac8ca62cd`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `368fef90304ffc344ed4b3927110849b`

~~~~text
theorem sourceDecompositionNotPromoted :
    sourceDecompositionStatus =
      .inconclusiveMissingTypedEvolutionLaw := rfl

/-- One typed object binds every emitted boolean to a compiled theorem. -/
~~~~

같은 소스의 사용 문맥 (586–588행):

~~~~text
  vtT13ChainRule := shapeChainRuleNumerator
  vtT13NoSourcePromotion := sourceDecompositionNotPromoted

~~~~

<a id="role-9fda28d73dd61c26"></a>
## role-9fda28d73dd61c26 — A37 — Evidence anatomy consistency theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `docs/ver2_upgrade/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_critical_upgraded.md` 2856–2856행
- 내용 버전: `a947d263a1aae41bc657365eda52c57ec0c1db433e9d6dc9382ec0a15f7b533b:c57f56a5`; 관찰 커밋: `da35c0f9f464df0adce8063f98de72cf967ba0f9`
- 이유: 구판 연구계획이 신규 appendix A37로 증명 목표와 근사 합산식을 명시한다. 가정·오차의 정식화 및 후속 구현은 이 역할 판정에서 확인하지 않았다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A37 | **Evidence anatomy consistency theorem** (Σ channels Δln B ≈ total ln B) | ~200 L |
~~~~

제안 의도 문맥 (`docs/ver2_upgrade/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN_critical_upgraded.md` 2846–2846행):

~~~~text
### 11.14.6 기존 Appendix A14→A15 재명명 + MIO 신규 appendix
~~~~

<a id="role-46cdb91b7ea8bd66"></a>
## role-46cdb91b7ea8bd66 — NT-A1 — Quadrupole–filling EGS identity  [Conditional; flagship]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 11–22행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-A1 — Quadrupole–filling EGS identity  [Conditional; flagship]

**Statement.** In the free-streaming era the temperature quadrupole is fixed by the shear, `a₂ = κ·Σ + O(a₃\text{-derivatives})` with `κ` an O(1) covariant coefficient (ETM ℓ=2). Hence the **shear part** of the filling fraction is an EGS-bounded functional of the observed CMB quadrupole,
`F_shear = Σ²/x_max = a₂²/(κ² x_max) ∝ D₂`,
so `F_shear → 0` as `D₂ → 0` (EGS limit: an isotropic CMB forces zero shear-filling). The **tilt part** of `F` is sourced by the dipole `a₁` (velocity/tilt), not the quadrupole, and is therefore *not* bounded by `D₂`.

**Proof sketch.** Integrate the ℓ=2 Liouville multipole over photon energy (ETM trick) to relate `τ_{ab}` to `σ_{ab}`; square and normalize to get `F_shear ∝ a₂² ∝ D₂`. The dipole equation carries the velocity/tilt source `v_a`, decoupled from `τ_{ab}` at this order; hence `Ω_tilt` enters `F` through `a₁`, not `a₂`. ∎ (toy-verified)

**Numerical support.** NT1: `D₂/Σ²` constant to factor 1.00 over three decades; raising `β` moves `τ₁`, leaves `τ₂` at 0.0%.

**To close.** Use the exact covariant ℓ=2 coefficient `κ` and a real low-ℓ transfer; state the EGS-limit bound `F_shear ≤ D₂/(κ² x_max)` with the measured Planck `D₂`.

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-565fa176ca7a3509"></a>
## role-565fa176ca7a3509 — NT-A2 — Registered Π test of the almost-EGS H3 assumption  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 23–32행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-A2 — Registered Π test of the almost-EGS H3 assumption  [Conditional]

**Statement.** The MES shear bound `Σ ≲ C·a₂` is licensed only under H3. Define the EGS-derivative ratio `R_EGS = a₃/a₂`. Then: if `Π(R_EGS > r*) ` is controlled at a pre-registered `r* = O(1)`, the bound holds; if `R_EGS` exceeds `r*`, the quadrupole no longer pins the shear/Weyl and the bound is void. The report's registered exceedance `Π` is therefore the correct instrument to *certify* the EGS derivative assumption.

**Proof sketch.** H3 is exactly the statement that multipole derivatives are bounded by the multipoles (C1′,C2′); the octupole controls the leading derivative correction to the ℓ=2 relation, so `a₃/a₂ = O(1)` is the operational form of H3. Registering `r*` before looking blocks post-hoc acceptance of the bound. ∎

**Numerical support.** NT3: injected octupole drives `R_EGS` to 5–9 and decouples the quadrupole from the shear (54–2160% shift); `Π(R_EGS>1)=0.80` over the stress series.

**To close.** Map `a₂,a₃` to the measured Planck quadrupole/octupole; report `Π(R_EGS>r*)` with the registered `r*`.

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-85ff10a5d9f8761b"></a>
## role-85ff10a5d9f8761b — NT-A3 — Information-gain (Fisher / Cramér–Rao) EGS floor on F  [Conditional → Forecast; analytic]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 33–42행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-A3 — Information-gain (Fisher / Cramér–Rao) EGS floor on F  [Conditional → Forecast; analytic]

**Statement.** The Boltzmann hierarchy fixes the quadrupole covariance (cosmic variance `Var(a₂) ≳ a₂²/(2·2+1)` plus instrument/foreground terms). Propagating through NT-A1 gives a Cramér–Rao floor on the measurability of the shear-filling: `Var(F_shear) ≥ (∂F_shear/∂a₂)² Var(a₂) = (2 a₂/(κ² x_max))² Var(a₂)`. Hence there is an irreducible EGS-information limit: `F_shear` below `~ (cosmic-variance quadrupole)²/(κ² x_max)` is unmeasurable in principle.

**Proof sketch.** Standard error propagation of NT-A1 with the multipole covariance; the `ℓ=2` cosmic-variance floor sets the minimum resolvable `a₂`, hence the minimum resolvable `F_shear`. ∎

**To close.** A dedicated experiment sampling the quadrupole covariance and reporting the `F`-floor; fold in foreground/mask covariance.

---

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-df53f7b2871550ba"></a>
## role-df53f7b2871550ba — NT-B1 — Beyond-MES octupole-sharpened bound on Σ²/Q  [Conditional; flagship]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 45–54행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-B1 — Beyond-MES octupole-sharpened bound on Σ²/Q  [Conditional; flagship]

**Statement.** The MES bound `Σ₀ < C·a₂` (with the calibration `a₂≈a₃≈10⁻⁵ ⇒ Σ₀<10⁻⁴`) is sharpened by the octupole: `Σ₀ < C·a₂·f(a₂,a₃)` with `f(a₂,a₃) = 1 − min(a₃/a₂, f_max) < 1` when `a₃ ≪ a₂`. This tightens the algebraic ceiling `x_max = (3/2)Σ_max²` and hence the admissible range of `Q = x_C/x_max` and `F`.

**Proof sketch.** The next term in the ℓ=2↔shear relation is set by the octupole (the leading derivative correction controlled by H3); when `a₃` is small the derivative correction is small and the inequality tightens by the stated factor. ∎ (toy-verified)

**Numerical support.** NT2: beyond-MES strictly tighter than MES in all rows; the integrated-hierarchy shear respects both.

**To close.** Replace `C` and `f` with the exact MES coefficients (Eqs. 31,35,36) and the measured `a₂,a₃`; quote the sharpened `Σ₀`, `W₀`, and the `Q/F` ceiling.

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-2a9e444fd4a3f8ab"></a>
## role-2a9e444fd4a3f8ab — NT-B2 — Vorticity-EGS + Frobenius joint (Σ²,W²) bound  [Conditional; analytic]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 55–62행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-B2 — Vorticity-EGS + Frobenius joint (Σ²,W²) bound  [Conditional; analytic]

**Statement.** The temperature dipole/curl bounds the vorticity (the MES `W₀<10⁻³` from `a₂,a₃`); combined with the Frobenius coupling `W² = R_WS² Σ²`, the `(Σ²,W²)` block of `x_C` obeys a joint EGS bound `Σ² + W² ≤ (1+R_WS²) Σ²_max(a₂,a₃)`. Because `x_C` carries `Σ²` with `+` and `W²` with `−`, this also bounds the *cancellation* available in `x_C` from the shear/vorticity sector.

**Proof sketch.** MES vorticity inequality in `W²_std`; substitute the Frobenius relation; combine with NT-B1's `Σ²_max`. ∎

**To close.** A dedicated experiment integrating a vortical mode; the exact MES vorticity coefficient.

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-ecd59621e1bd58ca"></a>
## role-ecd59621e1bd58ca — NT-B3 — Boltzmann line-of-sight transport of G_F  [Conditional]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 63–72행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-B3 — Boltzmann line-of-sight transport of G_F  [Conditional]

**Statement.** Since `F_shear ∝ a₂²` (NT-A1) and `a₂` accumulates along the line of sight via the covariant Boltzmann integral, the depth gap `G_F(z) = F(z)/F(z_ref)` obeys a transport relation sourced by the shear history. For a depth-steady shear and no tilt, `G_F(z) ≡ 1` (EGS limit: no depth gap); a depth-evolving tilt (dipole source) imprints a depth dependence on `G_F`.

**Proof sketch.** Differentiate `F(z)` along `u^a` using the LoS form of the ℓ=2 equation; a `z`-independent shear gives `dF/dz = 0`; the tilt enters through the dipole's own `z`-evolution. ∎ (toy-verified)

**Numerical support.** NT4: depth-steady shear → `G_F=1.0000` (spread 0); depth-growing tilt → `G_F` 0.25→1.56.

**To close.** The real LoS transfer and a survey-matched depth binning (links to the prior tomographic forecast `T-C1`, kept separate).

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-f03606e8657137a4"></a>
## role-f03606e8657137a4 — NT-B4 — Weyl/curl loophole made quantitative  [Conditional, grounded]

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 73–82행
- 내용 버전: `c3026228ae45ef85f5c20047e9fe500acf74340420e4fb94ce760f8880289beb:dd0517db`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
### NT-B4 — Weyl/curl loophole made quantitative  [Conditional, grounded]

**Statement.** When H3 fails (`R_EGS > r*`), an almost-isotropic CMB temperature bounds neither the shear nor the Weyl curvature: explicitly, the magnetic Weyl `H_{ab}` and `curl σ_{ab}` are unconstrained by `{a₁,a₂,a₃}` (Nilsson–Uggla–Wainwright–Lim 1999: shear→0 but Weyl↛0). In the diagnostic variables this is residual freedom in `Ω_{k,aniso}` and the curl sector that `x_C`/`F` cannot see from the temperature multipoles alone. (Distinct from the prior tilt-rapidity loophole `T-B1`: this is the *Weyl/derivative* sector.)

**Status.** Grounded in the loophole literature; quantified operationally through `R_EGS` and `Π` (NT-A2).

**To close.** Express the residual Weyl freedom as an explicit bound-gap in `Ω_{k,aniso}` as a function of `R_EGS`.

---

~~~~

제안 의도 문맥 (`egs_theorem_program.zip!/04_THEOREM_CANDIDATES.md` 1–3행):

~~~~text
# 04 — EGS-Type Theorem Candidates (NT-\*)

New theorems obtained by applying the covariant 1+3 Einstein–Boltzmann system to the report's diagnostic variables. Disjoint from the prior `T-*`, `F-*`, `N-*` sets (see `00`). Notation: temperature multipoles `τ_{a₁…a_L}` with magnitudes `a_L = |τ_L|` (MES convention, `|·|` = root-sum-square); quadrupole power `D₂ ~ a₂²`; shear scalar `Σ² = σ²/(6H²)`; filling `F = x_C/x_max`; occupancy score `Q`; registered exceedance `Π`; depth gap `G_F`. Status tags as before: **Provable / Conditional / Forecast**.
~~~~

<a id="role-14e0eaea8a4d4aa4"></a>
## role-14e0eaea8a4d4aa4 — T-P1 — Pole rotation covariance

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 3–8행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P1 — Pole rotation covariance

power-tensor pole가 SO(3) active rotation에 공변하고 p~-p axis quotient에서 well-defined임을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-3e5ea17c2b08403a"></a>
## role-3e5ea17c2b08403a — T-P2 — Pole degeneracy instability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 9–14행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P2 — Pole degeneracy instability

eigen-gap가 0으로 갈 때 Davis-Kahan-type axis error bound가 발산함을 보여 direction abstention threshold를 정당화한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-0f746ebecd4f8b37"></a>
## role-0f746ebecd4f8b37 — T-P3 — Shell-sum conservation

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 15–20행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P3 — Shell-sum conservation

registered line-of-sight source decomposition의 shell sum이 total transfer를 재현하는 조건과 discretization remainder를 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-8ac598c0250f194d"></a>
## role-8ac598c0250f194d — T-P4 — Observer endpoint separation

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 21–26행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P4 — Observer endpoint separation

local Lorentz boost term이 remote dipole/quadrupole field source와 다른 boundary object임을 typed map으로 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-fb115ecca130a85b"></a>
## role-fb115ecca130a85b — T-P5 — Cross-shell effective rank

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 27–32행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P5 — Cross-shell effective rank

correlated redshift bins의 information은 bin count가 아니라 covariance-whitened nonzero modes에 의해 결정됨을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-1bda2ebc3b4f17dc"></a>
## role-1bda2ebc3b4f17dc — T-P6 — Pole-definition stability set

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 33–38행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P6 — Pole-definition stability set

여러 registered pole definitions의 intersection/union을 set-valued axis region으로 구성하고 coverage 조건을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-313d321af1e56c2e"></a>
## role-313d321af1e56c2e — T-P7 — Source superposition non-identification

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 39–44행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P7 — Source superposition non-identification

collinear local/systematic/global responses가 mixture weights를 비식별하게 만드는 kernel을 구성한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-22f28daa348fd2d1"></a>
## role-22f28daa348fd2d1 — T-P8 — Remote dipole optical-depth factorization

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 45–50행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P8 — Remote dipole optical-depth factorization

amplitude nuisance와 pole direction response가 어떤 조건에서 분리되는지 정리한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-1ed42c4806560eb4"></a>
## role-1ed42c4806560eb4 — T-P9 — Remote quadrupole low-SNR set

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 51–56행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P9 — Remote quadrupole low-SNR set

noisy spin-2 remote field에서 point axis 대신 confidence region을 구성하는 theorem을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-bbfeb6470eb31a6b"></a>
## role-bbfeb6470eb31a6b — T-P10 — Coherent fraction identified set

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 57–62행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P10 — Coherent fraction identified set

r=g+(1-g)b+e moment model과 general convex extension의 sharp interval을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-30db9f52fdccd274"></a>
## role-30db9f52fdccd274 — T-P11 — Cluster/exchangeable remote rank

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 63–68행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P11 — Cluster/exchangeable remote rank

shared primordial modes와 reused reconstruction noise 하에서 valid cluster-level finite rank 조건을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-954d5028c58233c4"></a>
## role-954d5028c58233c4 — T-P12 — E-optimal rank reopening

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 69–74행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P12 — E-optimal rank reopening

candidate response vectors의 convex design에서 minimum singular value를 최대로 하는 SDP와 dual certificate를 제시한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-3573f515ceb956c0"></a>
## role-3573f515ceb956c0 — T-P13 — Finite-window coherent-mode bridge

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 75–80행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P13 — Finite-window coherent-mode bridge

multi-window velocity operator가 homogeneous mode를 식별하는 rank condition과 no-go region을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-6df86d0e32ae4ea4"></a>
## role-6df86d0e32ae4ea4 — T-P14 — Simulator-form envelope

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 81–86행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P14 — Simulator-form envelope

여러 forward simulators의 discrepancy를 nuisance feasible set으로 통합할 때 coverage 보존 조건을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-14df1424a3138148"></a>
## role-14df1424a3138148 — T-P15 — SBI contraction attribution

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 87–92행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P15 — SBI contraction attribution

weak identified set 대비 posterior contraction을 prior/model/data restrictions로 분해하는 information inequality를 제안한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-8145eafec793e5ce"></a>
## role-8145eafec793e5ce — T-P16 — Native shell-pole limit

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 93–98행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P16 — Native shell-pole limit

native Bianchi transfer의 FLRW limit가 CAMB/CLASS shell-pole process로 수렴하는 conformance theorem을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-6f02f4d5fe54ef82"></a>
## role-6f02f4d5fe54ef82 — T-P17 — Native local/global decomposition

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 99–104행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P17 — Native local/global decomposition

paired boosted/unboosted native runs의 component decomposition과 noncommuting transfer remainder를 bound한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.

~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-2547259daf5ad54c"></a>
## role-2547259daf5ad54c — T-P18 — Common latent joint region

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 105–109행
- 내용 버전: `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; 관찰 커밋: `6f6afef6564a7e9bf9446194ec6ff87e1abd607b`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-P18 — Common latent joint region

모든 probe가 동일 latent state를 공유할 때 marginal product envelope보다 sharp한 joint support image를 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
~~~~

제안 의도 문맥 (`external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md` 1–3행):

~~~~text
# External-Fusion Theorem and Proof Backlog

## T-P1 — Pole rotation covariance
~~~~

<a id="role-8ee85ff0ca9f2547"></a>
## role-8ee85ff0ca9f2547 — Pr169UnsignedLeakage.missingPhysicalReceiptBlocksPromotion

- 역할: 내부 보조명제·검증 보조정리
- 출처: `formal_pr169/Pr169UnsignedLeakage/Basic.lean` 84–91행
- 내용 버전: `78f51ccdc142c891ca4eb11709ae2a2a723ac76389b62832350c671ba34146a0:ad208a43`; 관찰 커밋: `43ea72444bf6c7eda2a931b784eb67fd336ab16d`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `8625a512c1cdb33d29de8c33167ec8f3`

~~~~text
theorem missingPhysicalReceiptBlocksPromotion :
    ¬ physicalPromotion missingBundle := by
  intro h
  have impossible := h 0
  simp [missingBundle] at impossible

end Pr169UnsignedLeakage

~~~~

<a id="role-be438d8ca950da0c"></a>
## role-be438d8ca950da0c — Pr170BuchertTwoPatch.registeredTypeCount

- 역할: 내부 보조명제·검증 보조정리
- 출처: `formal_pr170/Pr170BuchertTwoPatch/Basic.lean` 80–82행
- 내용 버전: `8b7c8dec8a5b7fe1549dda19a47210d8ae322b01ae8d70788a483d5ca8843d3d:ad208a43`; 관찰 커밋: `c936fabd1527bb8c38cb13b98fc1ee608d0c5738`
- 이유: 검증 상태·명제 묶음·유한 타입 개수를 표현하는 내부 논리 보조정리다. 선언 본문의 대상은 새로운 물리 정리의 전체 범위가 아니다.
- 연결 항목: `81f4d04dd32b7831272672a11c46136a`

~~~~text
theorem registeredTypeCount : Fintype.card BianchiType = 11 := by decide

end Pr170BuchertTwoPatch
~~~~

<a id="role-f609a78c9dbd1bb2"></a>
## role-f609a78c9dbd1bb2 — Pr171TiltRelaxation.persistentFixture

- 역할: 내부 보조명제·검증 보조정리
- 출처: `formal_pr171/Pr171TiltRelaxation/Basic.lean` 37–40행
- 내용 버전: `cb0efdb99d4bd4dafaf600c8ad819fffe08f2a57e34c49e2a3830525e8461797:ad208a43`; 관찰 커밋: `b8a857742bd6c2d727ea2009f6e8a341a031b120`
- 이유: 명시된 고정 벡터·행렬·숫자 예제의 값이나 랭크를 확인하는 검증 보조정리다. 해당 예제의 계산을 일반 정리 후보 전체와 구별한다.
- 연결 항목: `9060f9e61d072058cf37528eac759883`

~~~~text
theorem persistentFixture :
    ((-1 : ℚ) * 1 + 1 * 1 = 0) ∧ (1 * 1 + (-1) * 1 = 0) := by
  norm_num

~~~~

<a id="role-fbd64fdd2e0c0b19"></a>
## role-fbd64fdd2e0c0b19 — A37 — Evidence anatomy consistency theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt/docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` 2378–2378행
- 내용 버전: `d2354d3a139de91da972a72e75769884fdf9454aa31b442618f5f88586bbf58e:c57f56a5`; 관찰 커밋: `071444aedb5cbcc3d19cb0f71bd324d49cc343c6`
- 이유: 구판 연구계획이 신규 appendix A37로 증명 목표와 근사 합산식을 명시한다. 가정·오차의 정식화 및 후속 구현은 이 역할 판정에서 확인하지 않았다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A37 | **Evidence anatomy consistency theorem** (Σ channels Δln B ≈ total ln B) | ~200 L |
~~~~

제안 의도 문맥 (`htt/docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` 2368–2368행):

~~~~text
### 11.14.6 기존 Appendix A14→A15 재명명 + MIO 신규 appendix
~~~~

<a id="role-8fea3d018a8076c7"></a>
## role-8fea3d018a8076c7 — T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 3–8행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness

- **Track:** `I`
- **Proof route:** derive dual identity and every conversion; mutation factor-three must fail
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-74824318453d1667"></a>
## role-74824318453d1667 — T2-DEFECT-BUNDLE — Frame-indexed comparator functor

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 9–14행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `84af0ccc039e1a0c49f9db77e0c0795c`

~~~~text
## T2-DEFECT-BUNDLE — Frame-indexed comparator functor

- **Track:** `I`
- **Proof route:** prove same-frame linear projection and obstruction to unbridged frame mixing
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-a06edc93d767901e"></a>
## role-a06edc93d767901e — T2-CURVATURE-SPLIT — Scalar curvature departure versus PSTF curvature sector

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 15–20행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-CURVATURE-SPLIT — Scalar curvature departure versus PSTF curvature sector

- **Track:** `I`
- **Proof route:** derive independent tensor/scalar carriers and response maps
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-a55a32232be4b0d3"></a>
## role-a55a32232be4b0d3 — T2-EGS-LATTICE — Premise lattice for exact/almost EGS

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 21–26행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-EGS-LATTICE — Premise lattice for exact/almost EGS

- **Track:** `I`
- **Proof route:** classify acceleration and derivative-premise counterexamples
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-5829c7a188948867"></a>
## role-5829c7a188948867 — T2-JOINT-SUPPORT — Support image on common feasible set

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 27–32행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-JOINT-SUPPORT — Support image on common feasible set

- **Track:** `I`
- **Proof route:** general compact-set theorem; box is a corollary
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-115cfcf017fdd1a5"></a>
## role-115cfcf017fdd1a5 — T2-PHYSICAL-SHARPNESS — Constraint/local/global endpoint attainability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 33–38행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-PHYSICAL-SHARPNESS — Constraint/local/global endpoint attainability

- **Track:** `I→II`
- **Proof route:** construct initial data, local development and global branch certificates
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-3967c97bf66cb4b1"></a>
## role-3967c97bf66cb4b1 — T2-MES-BRANCH — Source-exact MES branch hierarchy

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 39–44행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-MES-BRANCH — Source-exact MES branch hierarchy

- **Track:** `I`
- **Proof route:** derive geodesic/non-geodesic/acceleration branches independently
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-eb8b38538cfaf312"></a>
## role-eb8b38538cfaf312 — T2-INACTIVE-EVIDENCE — Inactive normalized prior invariance

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 45–50행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-INACTIVE-EVIDENCE — Inactive normalized prior invariance

- **Track:** `I`
- **Proof route:** measure-theoretic and numerical proof
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-f8486acfcdb96895"></a>
## role-f8486acfcdb96895 — T2-RESPONSE-QUOTIENT — Observable response equivalence quotient

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 51–56행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `c655ba392f82ddd4b544ab514e77be3c`

~~~~text
## T2-RESPONSE-QUOTIENT — Observable response equivalence quotient

- **Track:** `I→II`
- **Proof route:** prove refinement under row augmentation and rank uncertainty
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-6354ad7146694a37"></a>
## role-6354ad7146694a37 — T2-BULK-BRIDGE — Finite-window bulk-to-homogeneous-mode identification

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 57–62행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-BULK-BRIDGE — Finite-window bulk-to-homogeneous-mode identification

- **Track:** `I`
- **Proof route:** operator rank and stochastic covariance theorem
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-437b535b47a6131f"></a>
## role-437b535b47a6131f — T2-MULTIFLUID — Multi-fluid first/second-moment non-equivalence

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 63–68행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-MULTIFLUID — Multi-fluid first/second-moment non-equivalence

- **Track:** `I`
- **Proof route:** zero flux does not imply zero tilt energy/stress
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-59b2eabef00ee0b3"></a>
## role-59b2eabef00ee0b3 — T2-CLUSTER-RANK — Cluster-exchangeable finite rank

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 69–74행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-CLUSTER-RANK — Cluster-exchangeable finite rank

- **Track:** `I`
- **Proof route:** derive valid randomized/cluster calibration
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-5c06085a18fc989e"></a>
## role-5c06085a18fc989e — T2-ESTCOV-PID — Estimated-covariance partial-ID confidence

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 75–80행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-ESTCOV-PID — Estimated-covariance partial-ID confidence

- **Track:** `I`
- **Proof route:** finite/asymptotic coverage with active boundaries
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-fe16144ce27f09b6"></a>
## role-fe16144ce27f09b6 — T2-EVALUE — Dependent finite-cover and sequential e-values

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 81–86행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-EVALUE — Dependent finite-cover and sequential e-values

- **Track:** `I`
- **Proof route:** predictable weighting and optional stopping
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-50c6801d1431a389"></a>
## role-50c6801d1431a389 — T2-SOLVER-NULL — Native FLRW null and analytic Bianchi-I transfer

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 87–92행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-SOLVER-NULL — Native FLRW null and analytic Bianchi-I transfer

- **Track:** `II`
- **Proof route:** temperature/polarization benchmarks
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-e77ece6af95fd16c"></a>
## role-e77ece6af95fd16c — T2-POLARIZATION — Bianchi E/B parity and handedness

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 93–98행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-POLARIZATION — Bianchi E/B parity and handedness

- **Track:** `II`
- **Proof route:** representation and solver equivalence
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-03f10e5117ade2f6"></a>
## role-03f10e5117ade2f6 — T2-NATIVE-RANK — Native transfer Jacobian identifiability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 99–104행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-NATIVE-RANK — Native transfer Jacobian identifiability

- **Track:** `II`
- **Proof route:** rank confidence and quotient refinement
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-575fcca2e3c5a68f"></a>
## role-575fcca2e3c5a68f — T2-SURROGATE — Certified Teff/native remainder

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 105–110행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-SURROGATE — Certified Teff/native remainder

- **Track:** `II`
- **Proof route:** held-out uniform error envelope
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.

~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-b939dc581755e9fc"></a>
## role-b939dc581755e9fc — T2-COMMON-MODEL — Common latent cosmology joint identified region

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 111–115행
- 내용 버전: `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; 관찰 커밋: `c2412051864af2c638203a385abe07e80754d22d`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T2-COMMON-MODEL — Common latent cosmology joint identified region

- **Track:** `II/Joint`
- **Proof route:** one state generates all probes and constraints
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.
~~~~

제안 의도 문맥 (`htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md` 1–3행):

~~~~text
# Round-2 Theorem and Proof Backlog

## T2-W2-SSOT — Constraint-normalized vorticity convention uniqueness
~~~~

<a id="role-d36d8d234b943326"></a>
## role-d36d8d234b943326 — T-W2-SSOT — W² convention uniqueness

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 5–14행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-W2-SSOT — W² convention uniqueness

**Candidate statement.** 1+3 Gauss constraint, H=Θ/3, duality ω_abω^ab=2ω_aω^a에서 normalization과 MES conversion이 유일함을 증명.

**Proof route.** Cartan/exterior derivation + component algebra + Lean scalar core.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-186.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-890ac19cd3723e0c"></a>
## role-890ac19cd3723e0c — T-SIGNED-CARRIER — Signed comparator carrier

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 15–24행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-SIGNED-CARRIER — Signed comparator carrier

**Candidate statement.** g∈S_+³×R, x_C=cᵀg; PSD embedding은 positive block에만 작용하고 signed curvature를 보존.

**Proof route.** convex analysis + semialgebraic physical subset.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-187.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-7855a6f0136c97a0"></a>
## role-7855a6f0136c97a0 — T-FRAME-PUSHFORWARD — Congruence-indexed comparator functor

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 25–34행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-FRAME-PUSHFORWARD — Congruence-indexed comparator functor

**Candidate statement.** registered Lorentz/frame map 아래 g[n],g[u],g[obs]의 변환과 remainder/order를 명시하고 composition law를 증명.

**Proof route.** tetrad algebra + exact Lorentz stress-energy.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-187,194.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-a2b4ff30d2573081"></a>
## role-a2b4ff30d2573081 — T-JOINT-SUPPORT — General comparator identified set

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 35–44행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-JOINT-SUPPORT — General comparator identified set

**Candidate statement.** compact F에서 cᵀF의 extrema/connectedness; convex F는 interval, nonconvex F는 finite union; box formula는 factorized corollary.

**Proof route.** support functions, Tarski-Seidenberg/real algebraic geometry, certified optimization.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-189.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-eb677b412977266d"></a>
## role-eb677b412977266d — T-PHYSICAL-SHARPNESS — Dynamical endpoint attainability

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 45–54행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-PHYSICAL-SHARPNESS — Dynamical endpoint attainability

**Candidate statement.** joint support endpoints와 interior가 common Einstein–matter solution class에서 실현됨.

**Proof route.** exact initial data + local existence + constraint propagation + continuation.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-190.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-0b34575bc1215781"></a>
## role-0b34575bc1215781 — T-GAUSS-RESTSPACE — Vortical rest-bundle Gauss theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 55–64행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `a63c8c4e8009f66bc22a3c1276597f45`

~~~~text
## T-GAUSS-RESTSPACE — Vortical rest-bundle Gauss theorem

**Candidate statement.** nonintegrable rest distribution의 두 contraction conventions 관계와 canonical scalar를 정의하고 ω=0 hypersurface limit을 증명.

**Proof route.** Cartan structure equations + xAct.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-191.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-27449d897a1600da"></a>
## role-27449d897a1600da — T-KE-MAXIMAL-CLASS — Flat obstruction / curved existence classification

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 65–74행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-KE-MAXIMAL-CLASS — Flat obstruction / curved existence classification

**Candidate statement.** general invariant homogeneous perfect-fluid class에서 type-I tilted rotation obstruction의 necessary/sufficient conditions와 curved open-set existence.

**Proof route.** momentum constraints + Euler/Killing transport + local ODE existence.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-191.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-764fabd16864a1f0"></a>
## role-764fabd16864a1f0 — T-OMK-ALL-ORDER — OMK homological recurrence and resonances

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 75–84행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-OMK-ALL-ORDER — OMK homological recurrence and resonances

**Candidate statement.** c_n(w)의 recurrence, resonance set의 completeness, finite-domain remainder와 non-LRS persistence.

**Proof route.** invariant-manifold equation + exact algebra + interval tubes.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-192.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-a729e95805590b41"></a>
## role-a729e95805590b41 — T-MES-INTRINSIC-DIPOLE — MES ceiling surface

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 85–94행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-MES-INTRINSIC-DIPOLE — MES ceiling surface

**Candidate statement.** ε1,intrinsic를 포함한 geodesic/non-geodesic shear/vorticity/acceleration ceiling surface와 attribution admissibility.

**Proof route.** covariant multipole hierarchy first-principles derivation.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-193.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-5c1e239533655199"></a>
## role-5c1e239533655199 — T-BOOST-TILT-BRIDGE — Boost/tilt/fingerprint normalization theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 95–104행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `853264cb126023223fe9d01d913fa2ce`

~~~~text
## T-BOOST-TILT-BRIDGE — Boost/tilt/fingerprint normalization theorem

**Candidate statement.** observer boost kernel, tilted matter stress tensor, antipodal moment fingerprints의 branch-specific exact maps.

**Proof route.** Lorentz group representation + moment algebra.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-194.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-9d563e012f83bca4"></a>
## role-9d563e012f83bca4 — T-BULK-TO-TILT — Finite-window bulk-flow bridge

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 105–114행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-BULK-TO-TILT — Finite-window bulk-flow bridge

**Candidate statement.** B_W=v0+δ_W에서 homogeneous mode identified set과 finite-window remainder bound.

**Proof route.** Gaussian random fields/window operators + hierarchical inference.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-195.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-f983ee106702fb4d"></a>
## role-f983ee106702fb4d — T-PHYSICAL-RANK — Native response identifiability theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 115–124행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `de0a79bb4cf047d5ee0c60c1f914c239`

~~~~text
## T-PHYSICAL-RANK — Native response identifiability theorem

**Candidate statement.** actual transfer Jacobian과 nuisance projection 아래 reachable/null sectors와 rank interval.

**Proof route.** Fréchet derivatives, singular-value perturbation, native solver.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-196.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-0e053e1565b16177"></a>
## role-0e053e1565b16177 — T-CLUSTER-RANK — Cluster-valid finite rank

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 125–134행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-CLUSTER-RANK — Cluster-valid finite rank

**Candidate statement.** fixed scorer와 independent clusters under null에서 observation-inclusive rank의 super-uniformity; valid randomized cluster extension.

**Proof route.** conditional exchangeability/conformal rank proof.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-197.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-10e9fe0630aec71f"></a>
## role-10e9fe0630aec71f — T-PAIRED-BOOST — Paired boost residual theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 135–144행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: `40c2878290b4f290ab17dabb7abaf84d`

~~~~text
## T-PAIRED-BOOST — Paired boost residual theorem

**Candidate statement.** paired boosted-unboosted difference에서 exact template residual의 distribution과 amplitude estimator validity.

**Proof route.** paired Monte Carlo test + GLS/invariance.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-199.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-706f50a1b6094875"></a>
## role-706f50a1b6094875 — T-PARTIAL-ID-ESTCOV — Partial-ID confidence with random covariance

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 145–154행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-PARTIAL-ID-ESTCOV — Partial-ID confidence with random covariance

**Candidate statement.** estimated covariance, nonlinear endpoint, active constraints에서 uniform/grid-certified set coverage.

**Proof route.** QLR/quasi-posterior MC, t likelihood, bootstrap, projection.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-200.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-a907fc87b0e2ef54"></a>
## role-a907fc87b0e2ef54 — T-STRUCTURAL-ROBUSTNESS — Structural set vs pipeline set calculus

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 155–164행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-STRUCTURAL-ROBUSTNESS — Structural set vs pipeline set calculus

**Candidate statement.** I(θ)와 R(pipeline)의 union/intersection 및 combined uncertainty semantics.

**Proof route.** set-valued statistics and decision theory.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-201.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-bf042c997947cdf4"></a>
## role-bf042c997947cdf4 — T-JOINT-COMPARATOR-ID — Full common-model comparator identification

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 165–174행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-JOINT-COMPARATOR-ID — Full common-model comparator identification

**Candidate statement.** multi-probe likelihood/moments + GR restrictions의 common F_joint에서 x_C identified region과 prior-exposed directions.

**Proof route.** joint support theorem + physical response + coverage.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-205.

~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-48bd5150f379db75"></a>
## role-48bd5150f379db75 — T-SOURCE-DISCRIMINATION — Abstention-gated source discrimination

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 175–183행
- 내용 버전: `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 연구제안서가 구체적인 명제와 증명 목표를 후보로 명시한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T-SOURCE-DISCRIMINATION — Abstention-gated source discrimination

**Candidate statement.** normalized systematic/local/global models에서 identification, PPC, holdout, prior sensitivity를 conjunctive하게 만족할 때만 source set을 출력.

**Proof route.** decision theory + finite-sample calibration.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-206.
~~~~

제안 의도 문맥 (`htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md` 1–3행):

~~~~text
# 추가 증명 가능한 정리 후보와 formalization backlog

> 각 정리는 약한 문구로 retreat하기 위한 것이 아니라 v10의 강한 programme를 실제 theorem으로 완성하기 위한 후보다. dense numerical scan은 proof가 아니며 interval/CAS/formal core가 따로 필요하다.
~~~~

<a id="role-ca2f8c0e26b96c29"></a>
## role-ca2f8c0e26b96c29 — T1. Registered Max-Scan Calibration Theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 7–23행
- 내용 버전: `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; 관찰 커밋: `50d0fd652805dfde9b285e3347811e1764ab6615`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `7107d073d13fc49a62bdcbf60899983b`

~~~~text
## T1. Registered Max-Scan Calibration Theorem

**Math/stat axis.** For a fixed registered feature family
`S_1,...,S_p`, with a tail orientation for each statistic and simulations
processed through the same pipeline, the statistic
`T=max_j -log(p_j)` has a rank-calibrated finite-mock p-value with the `+1`
correction. Dependence among statistics is preserved because the full scan is
repeated in each mock.

**GR/cosmology axis.** The theorem makes no geometry statement. It is the
calibration layer needed before low-ell CMB morphology can enter almost-EGS or
MES discussion as an observed residual.

**Data axis.** This upgrades K1 from local low-ell feature tails to a registered
global scan once PR4/NPIPE E2E summaries exist. Until then the synthetic runner
only verifies mechanics.

~~~~

제안 의도 문맥 (`legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 1–5행):

~~~~text
# Theorem candidates for the next paper

The candidates below are meant to preserve novelty while staying inside the
current evidence boundary. Each theorem has three axes: math/stat theory,
GR/cosmology theory, and data interpretation.
~~~~

<a id="role-aba6d0a88a843cba"></a>
## role-aba6d0a88a843cba — T2. Rank-Exact Local/Global Identifiability Theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 24–39행
- 내용 버전: `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; 관찰 커밋: `50d0fd652805dfde9b285e3347811e1764ab6615`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `9afd4a0d4ea4f98237fb80b5bcd30b8a`

~~~~text
## T2. Rank-Exact Local/Global Identifiability Theorem

**Math/stat axis.** In the whitened linear response model, the identifiable
subspace is exactly the column space of the response design after nuisance
projection. Duplicate blocks add no rank; single-shell radial velocity designs
cannot separate coherent bulk and acceleration; radial data alone have zero
antisymmetric response.

**GR/cosmology axis.** This separates local boost, global tilt candidate,
survey/systematic response, and noise blocks before any HTT posterior. It also
formalizes why pointwise four-velocity is not enough: first-jet kinematics
carry expansion, shear, and vorticity.

**Data axis.** Use it as the entry gate for CF4, DESI, and low-ell axis
comparisons. Rank loss is a no-claim state, not weak evidence.

~~~~

제안 의도 문맥 (`legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 1–5행):

~~~~text
# Theorem candidates for the next paper

The candidates below are meant to preserve novelty while staying inside the
current evidence boundary. Each theorem has three axes: math/stat theory,
GR/cosmology theory, and data interpretation.
~~~~

<a id="role-40d8f40d5fb9ae77"></a>
## role-40d8f40d5fb9ae77 — T3. Boltzmann Collision-Gap Memory Bound

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 40–55행
- 내용 버전: `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; 관찰 커밋: `50d0fd652805dfde9b285e3347811e1764ab6615`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T3. Boltzmann Collision-Gap Memory Bound

**Math/stat axis.** If a linearized non-hydrodynamic moment obeys
`dM/dt <= -gamma M + S(t)` with `gamma>0` and bounded source envelope, then
`||M(t)|| <= ||M(0)|| exp(-gamma t) + S_max/gamma (1-exp(-gamma t))`.
If `gamma<=0`, forgetting language is disallowed.

**GR/cosmology axis.** This is a direct Boltzmann-equation theorem candidate:
Thomson/collision damping supplies the gap, while metric/tilt sources supply
the source envelope. The current repo already tests the synthetic gate; future
work must bind the actual operator convention and collision gap.

**Data axis.** This theorem turns a future low-ell transfer computation into a
bounded-memory diagnostic instead of an uncalibrated template fit. It does not
need family classification to be useful.

~~~~

제안 의도 문맥 (`legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 1–5행):

~~~~text
# Theorem candidates for the next paper

The candidates below are meant to preserve novelty while staying inside the
current evidence boundary. Each theorem has three axes: math/stat theory,
GR/cosmology theory, and data interpretation.
~~~~

<a id="role-ccf20aa164c0504d"></a>
## role-ccf20aa164c0504d — T4. Visibility-Cancellation No-Go Theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 56–70행
- 내용 버전: `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; 관찰 커밋: `50d0fd652805dfde9b285e3347811e1764ab6615`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `ed53713a73d2c6b486aa592936fb6232`

~~~~text
## T4. Visibility-Cancellation No-Go Theorem

**Math/stat axis.** A LOS integral cannot be inverted into a source upper bound
unless source rank, sign/phase coherence, visibility-kernel floor, and mask
support are all bound. Missing any one condition blocks source upper-bound
language.

**GR/cosmology axis.** This is the Boltzmann/line-of-sight counterpart of EGS
rigidity: observed low multipoles can vanish through projection or cancellation,
so absence of a feature is not automatically absence of a source.

**Data axis.** Apply this to K1 and future native solver comparisons. It gives a
strong negative result: some tempting inverse-source claims are mathematically
unsupported.

~~~~

제안 의도 문맥 (`legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 1–5행):

~~~~text
# Theorem candidates for the next paper

The candidates below are meant to preserve novelty while staying inside the
current evidence boundary. Each theorem has three axes: math/stat theory,
GR/cosmology theory, and data interpretation.
~~~~

<a id="role-b6f765deb06070d1"></a>
## role-b6f765deb06070d1 — T5. Almost-EGS Promotion Gate

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 71–83행
- 내용 버전: `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; 관찰 커밋: `50d0fd652805dfde9b285e3347811e1764ab6615`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
## T5. Almost-EGS Promotion Gate

**Math/stat axis.** An almost-EGS residual bound can be promoted only if
acceleration, temperature-gradient, derivative, and Weyl diagnostic bounds are
all present with provenance.

**GR/cosmology axis.** This keeps EGS-type reasoning strong: exact isotropy
implies FLRW under the theorem assumptions, and almost-isotropy requires all
control terms, not only a quadrupole summary.

**Data axis.** K1 can be used as one observed input to this gate, but it cannot
alone produce an almost-EGS cosmological conclusion.

~~~~

제안 의도 문맥 (`legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 1–5행):

~~~~text
# Theorem candidates for the next paper

The candidates below are meant to preserve novelty while staying inside the
current evidence boundary. Each theorem has three axes: math/stat theory,
GR/cosmology theory, and data interpretation.
~~~~

<a id="role-a77711b282e399c7"></a>
## role-a77711b282e399c7 — T6. Potential-Flow Curl Non-Identifiability Theorem

- 역할: 과거 연구제안의 구체적 정리·증명 후보
- 출처: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 84–96행
- 내용 버전: `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; 관찰 커밋: `50d0fd652805dfde9b285e3347811e1764ab6615`
- 이유: 후보 문서가 제시한 구체 절/명제다. 조건부·forecast·proved 등의 표기는 원문 역할/가정을 보존할 뿐 이 매핑의 증명 판정이 아니다.
- 연결 항목: `0bc3faba0b88ccb5c96a40a67148e001`

~~~~text
## T6. Potential-Flow Curl Non-Identifiability Theorem

**Math/stat axis.** Projection onto the symmetric affine-gradient subspace
annihilates the antisymmetric component. Therefore the vorticity channel is
structurally absent under a potential-flow reconstruction.

**GR/cosmology axis.** Vorticity is a kinematic first-jet component, but a
curl-suppressing reconstruction can remove it before estimation. A small
estimated curl is then a reconstruction property, not a physical measurement.

**Data axis.** This converts the K6 blocker into a result: report bulk,
expansion, and shear under current CF4++ reconstruction, but keep vorticity
only as a structural no-go unless field realizations with curl support exist.
~~~~

제안 의도 문맥 (`legacy/cf4_p0/packages/publishable_next/theorem_candidates.md` 1–5행):

~~~~text
# Theorem candidates for the next paper

The candidates below are meant to preserve novelty while staying inside the
current evidence boundary. Each theorem has three axes: math/stat theory,
GR/cosmology theory, and data interpretation.
~~~~

<a id="role-e48d3beeeb5a6ef7"></a>
## role-e48d3beeeb5a6ef7 — under a fixed linear Gaussian model, invertible whitening and fixed nuisance projection, rank$(P_NC^{-1/2}R)$ is the locally identifiable dimension; a duplicate block adds zero rank, its nullspace contains $(x,-x)$ and equals it only if the original block has full column rank

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 17–17행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-rank (local response identifiability) | under a fixed linear Gaussian model, invertible whitening and fixed nuisance projection, rank$(P_NC^{-1/2}R)$ is the locally identifiable dimension; a duplicate block adds zero rank, its nullspace contains $(x,-x)$ and equals it only if the original block has full column rank | `test_pr04_response::test_full_and_duplicate_rank`; `test_pr07_paper_a::test_duplicate_rank_hypothesis` | `A-rank` | repaired symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-748e3162284160ba"></a>
## role-748e3162284160ba — projecting out a nuisance equal to a response block removes exactly that block's rank

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 18–18행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-nuisance | projecting out a nuisance equal to a response block removes exactly that block's rank | `test_pr04_response::test_nuisance_removes_exact_block` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-2fd602d0016ef21d"></a>
## role-2fd602d0016ef21d — identical response subspaces have zero principal angles

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 19–19행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-angles | identical response subspaces have zero principal angles | `test_pr04_response::test_principal_angle_identical` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-b66bcdd8bd48b2a8"></a>
## role-b66bcdd8bd48b2a8 — adding complementary blocks gains rank monotonically until the design is identifiable

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 20–20행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-ladder (complementary-channel sufficiency) | adding complementary blocks gains rank monotonically until the design is identifiable | `test_pr04_response::test_rank_ladder` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-87ffadc9ebc2f95a"></a>
## role-87ffadc9ebc2f95a — for proper-time flat FLRW and normalized comoving $u^a$, $\Theta=3H$ and $A_a=\sigma_{ab}=\omega_{ab}=0$

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 21–21행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-flrw (congruence limit) | for proper-time flat FLRW and normalized comoving $u^a$, $\Theta=3H$ and $A_a=\sigma_{ab}=\omega_{ab}=0$ | `test_pr04_congruence::test_flat_flrw_limit` | `A-flrw` | repaired symbolic ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-8748bcd7a90eb3a9"></a>
## role-8748bcd7a90eb3a9 — inertial Minkowski congruence has θ = σ = ω = a = 0

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 22–22행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-minkowski | inertial Minkowski congruence has θ = σ = ω = a = 0 | `test_pr04_congruence::test_minkowski_inertial` | (limit of A-flrw) | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-e1f452cabc5f97a1"></a>
## role-e1f452cabc5f97a1 — two non-collinear boosts compose to an exact Lorentz map whose velocity is not the Euclidean sum; no Wigner angle is claimed by this theorem

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 23–23행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-boost-composition | two non-collinear boosts compose to an exact Lorentz map whose velocity is not the Euclidean sum; no Wigner angle is claimed by this theorem | `test_pr04_congruence::test_noncollinear_boost_is_lorentz` | `A-boost-composition` | repaired symbolic ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-70c07e381af12208"></a>
## role-70c07e381af12208 — equal pointwise four-velocity does not determine congruence kinematics; a first jet is required

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 24–24행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-first-jet-no-go | equal pointwise four-velocity does not determine congruence kinematics; a first jet is required | `test_pr07_paper_a::test_boost_and_first_jet_split` | `A-first-jet-no-go` | symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-bf46543dfbee18df"></a>
## role-bf46543dfbee18df — a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 25–25행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-failclosed | a single rapidity/velocity does not determine θ/σ/ω; incomplete normalization fails closed | `test_pr04_congruence::test_incomplete_normalization_fails` | (numeric) | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-498945042c9783c0"></a>
## role-498945042c9783c0 — for $r=dn$ and antisymmetric $\Omega$, $n^a\Omega_{ab}r^b=0$ exactly

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 26–26행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-radial-novortex (radial-vorticity no-go) | for $r=dn$ and antisymmetric $\Omega$, $n^a\Omega_{ab}r^b=0$ exactly | `test_pr07_paper_a::test_radial_vorticity_no_go` | `A-radial-novortex` + xAct canonicalization | proof closed ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-26704b07fbd6c790"></a>
## role-26704b07fbd6c790 — at one exact depth, acceleration-like and coherent-bulk dipole blocks are proportional; broad depth support can restore rank

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 27–27행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-single-shell-degeneracy | at one exact depth, acceleration-like and coherent-bulk dipole blocks are proportional; broad depth support can restore rank | `test_pr07_paper_a::test_single_shell_degeneracy_and_broad_depth_recovery` | algebraic proportionality | proof closed ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-b4b46ca4043a4b4f"></a>
## role-b4b46ca4043a4b4f — for $R=T\otimes I_5$, $\mathrm{rank}(R)=5\,\mathrm{rank}(T)$

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 28–28행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| A-temporal-tensor-rank | for $R=T\otimes I_5$, $\mathrm{rank}(R)=5\,\mathrm{rank}(T)$ | `test_pr07_paper_a::test_temporal_tensor_rank` | Kronecker-rank identity | proof closed ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-aadcbdb2d061dd99"></a>
## role-aadcbdb2d061dd99 — an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 41–41행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-codazzi (flux balance) | an antipodal species pair has zero tilt flux J (Codazzi residual 0), Ω_tilt > 0, realizability margin ≥ 0 | `test_pr04_bianchi::test_counterstream_codazzi` | (numeric; flux algebra) | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-6b356159a89172ca"></a>
## role-6b356159a89172ca — a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 42–42행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-nonsuff (scalar nonclosure) | a colinear antipodal pair and an isotropic six-stream share Ω_tilt = Tr(K) but differ in the STF moment Π | `test_pr04_bianchi::test_scalar_non_sufficiency` | `B-nonsuff` | symbolic ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-efd907aa6caa243a"></a>
## role-efd907aa6caa243a — every abstract PSD second moment admits an antipodal eigen-pair moment representation; this is not an Einstein-fluid existence theorem

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 43–43행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-psd-abstract (PSD moment cone) | every abstract PSD second moment admits an antipodal eigen-pair moment representation; this is not an Einstein-fluid existence theorem | `test_pr04_bianchi::test_psd_pair_decomposition` | `B-psd-abstract` | repaired symbolic ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-e7fce17e821d36f4"></a>
## role-e7fce17e821d36f4 — on $\Lambda=0$, $H_0>0$, $1+3H_0t/2>0$, the dust oracle is exact; RK4, DOP853 and Radau are compared using one manifest metric

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 44–44행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-dust (exact FLRW oracle) | on $\Lambda=0$, $H_0>0$, $1+3H_0t/2>0$, the dust oracle is exact; RK4, DOP853 and Radau are compared using one manifest metric | `test_pr04_bianchi::test_dust_flrw_limit`; `test_pr07_integrators::*` | `B-dust` | repaired symbolic + cross-integrator numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-117f484468f66d2d"></a>
## role-117f484468f66d2d — physical $\pi_{ab}$ and normalized $\Pi_{ab}=\kappa\pi_{ab}/(3H^2)$ are distinct: $\dot\sigma=\mathrm{STF}(-3H\sigma+\kappa\pi)=\mathrm{STF}(-3H\sigma+3H^2\Pi)$

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 45–45행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-shear (unit-safe shear memory) | physical $\pi_{ab}$ and normalized $\Pi_{ab}=\kappa\pi_{ab}/(3H^2)$ are distinct: $\dot\sigma=\mathrm{STF}(-3H\sigma+\kappa\pi)=\mathrm{STF}(-3H\sigma+3H^2\Pi)$ | `test_pr04_bianchi::test_pi_ablation_changes_shear`; `test_pr07_units::*` | repaired `B-shear` | symbolic + numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-ffb06ea14d764827"></a>
## role-ffb06ea14d764827 — primitive RHS is independently checked against projected energy/momentum conservation and $\dot G=-2HG$, $\dot q=-(4HI+\sigma)q$ over randomized admissible states

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 46–46행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-conservation (species continuity/Euler and constraint transport) | primitive RHS is independently checked against projected energy/momentum conservation and $\dot G=-2HG$, $\dot q=-(4HI+\sigma)q$ over randomized admissible states | `test_pr07_conservation::*`; `test_pr07_integrators::*` | Wolfram/xAct branch checks + independent Python chain rule | review gate closes only when all local runs pass |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

<a id="role-e313b3cd625d8410"></a>
## role-e313b3cd625d8410 — the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator

- 역할: 역할 판단 보류
- 출처: `pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 47–47행
- 내용 버전: `578ffaa6693168052748052846c1478e5495e49ed537d1a3ad49a98c7bbc07fd:d283db23`; 관찰 커밋: `없음/로컬·아카이브`
- 이유: 정리-테스트 매핑은 후보/보조정리의 과학적 역할이나 완료를 독립적으로 판정하지 않는다. 행의 상태와 제한은 원문 그대로 보존한다.
- 연결 항목: 기존 두 목록에 직접 대응하는 검색 항목 없음

~~~~text
| B-pushforward (fail-closed reporting) | the legacy x_C/Q/Π/F/G_F pushforward blocks on missing components and on a zero denominator | `test_pr04_pushforward::*` | — | numeric ✓ |
~~~~

제안 의도 문맥 (`pr07_repair_execution_pack/overlay/docs/research_program/pr04/PAPER_THEOREM_MAP.md` 1–5행):

~~~~text
# PR04 Theorem-to-Test Map (PAPER-A / PAPER-B)

owner: BASS/HTT · claim_tier: program_theorem · status source: LR-06B / LR-06C

Each theorem is backed by (i) a numerical property gate in
~~~~

