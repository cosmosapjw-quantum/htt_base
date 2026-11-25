# R113-CLOUD 독립 diff 리뷰 (`F0`)

- **리뷰 대상**:
  - `BASS` `40626723bcee34b3c02d1827344b2ee5ac3b368d..db72d1bcf8341d1fdeed3f1f03b169f00594efb6`
  - `REC` `3752213099ccb35998c22f1aaf0d42fb674184e4..05db5451a97c66b9a87de98ae35b88ab820d368f`
  - `htt_base` `e810a4f705c3785e06f9f998f5c57e64c3baef22..5a9a4fc455ac800c3b8491efe2c94a4953991a0e`
- **독립 리뷰 서브에이전트**: `332962c3-66c8-4c98-b99d-628a1a5c811d` (읽기 전용)
- **요약**: CRITICAL `0`, HIGH `1`, MEDIUM `5`, LOW `4`. 핵심 수학(`geom::lie`, `wigner`, `spin_sht`, `lie_hierarchy`), 부호 규약(`HEALPix E = -E_Dossier`), R112 하위 20/20 TSV 비트 일치 및 `REC matched_history` 불변량 검증 통과. (`F0-10`은 C1 장기 실행 검증에서 발견되어 R114에 추가 해결)

## 주요 지적 및 R114 조치
1. **[HIGH `F0-1`]** `BASS solve.rs`: `--recombination-stop-eta`가 스텝 시작점 `node.eta < stop_eta`만 검사해 구간을 걸치는 스텝이나 ULP 반올림 시 REI 구간(`z < 20`) 내부로 TLA 응답을 1스텝 넘기는 문제 → 스텝 종점 `next.eta <= stop_eta + 32*EPSILON*(1+stop_eta)` 게이트로 수정 및 비격자 `stop_eta` 회귀 테스트 추가.
2. **[MEDIUM `F0-2`]** `BASS geom/lie.rs`: 회전/진화된 Type IV(`rank(N)=1`)의 `1e-17` 반올림 오차로 `h ~ -1.30e16` 산출 → `III`, `VI_h`, `VI*_-1/9`, `VII_h`에서만 `1/kappa` 역수를 취하도록 제한 및 테스트 추가.
3. **[MEDIUM `F0-3`]** `REC matched_history.rs` + `BASS solve.rs`: `isotropic_peebles_rate`의 불필요한 구적(`None -> Some(temperature_k)`), `x_ref_next >= X_MAX` 사전 단락화, 및 Illinois 루프 내 2048점 `compton_temperature_k(&rsky)` 중복 호출 제거(루프 밖 1회 사전 계산).
4. **[MEDIUM `F0-4`]** `BASS examples/homogeneous_sky.rs`: `--route harmonic` 시 `(n_theta, n_phi)`와 `--lmax` Nyquist 검증 누락 및 불사용 `(nmu, nphi)` 과잉 제약 보완.
5. **[MEDIUM `F0-5`]** `BASS solve.rs`: 개방형 기하에서 `omega_lambda >= 1.0`과 `--recombination matched` 결합 시 평탄 참조 밀도 음수화 방지 게이트 추가.
6. **[LOW `F0-6..9`]** `recoil.rs` 비양수 입력 조기 차단, `ionization.rs` `added.is_finite()` 및 0깊이 필터링, `frames.rs` `gf^2/(1+gf)` 무상쇄 식, `spin_sht.rs` 영벡터 가드, `AGENTS.md` 기존 체크아웃 우선 원칙 준수(새 worktree 미생성), 클라우드 문서 차이(`THEORY.md:211,239,357`, `README_KO.md:144,150-153`, `homogeneous_sky.rs:261`) 투명 기록.
7. **[MEDIUM `F0-10`]** `BASS spin_sht.rs`, `field.rs`, `solve.rs`: 광학적으로 얇은 조화 충돌 셀마다 $O(1)$ 단극 전체를 비중심화 GL/방위 SHT로 덮어쓰고(`sum w_k - 4pi ~ 8e-14`), 고정 격자 구적으로 초기 모멘트를 계산하여 장기 적분(`1+z=1601`) 시 `I/IX`에서 `frame_rad ~ 6e-14` 및 $l=4$ 왜곡 발생 → `HarmonicSky::absorb_delta`, `SpinSht::analyze` 링·구면 평균 중심화, `projector(&e)` 비편광 화면 및 해석적 `l <= 2` `HarmonicSky::moments` 도입(격자 양의 강도/고윳값 검증 유지). 최종 바이너리(`3b775cf3...`)로 Rust `221+3` 테스트 통과 및 `V1` 20/20 TSV 비트 일치 재확인.
