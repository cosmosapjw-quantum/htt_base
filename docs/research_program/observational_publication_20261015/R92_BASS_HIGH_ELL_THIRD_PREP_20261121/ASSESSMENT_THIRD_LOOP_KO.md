# R92 | BASS, REC, REI, Mayukh, Legacy 심층 조사와 제3차 연구 준비

작성: 2026-11-21 KST. HTT R91 브랜치의 R78 과학 정본은 보존하고, 요청한 일곱 디렉터리와 관련 GitHub 저장소의 실재 코드·문서·압축파일을 읽기 전용으로 조사했다. 이 보고서는 3차 연구 루프의 준비이며, 원래 60 science nodes의 완료나 3차 R1–R10/C1–C10 실행 결과가 아니다.

## 조사 범위와 신뢰성

- 실물 파일 92,127개, 압축파일 754개, 유효하게 내부 항목을 인덱싱한 압축파일 753개. 첫 ZIP/TAR 순회 154,522개 내부 항목, 중첩 ZIP 8,955개, 대형 TAR 추가 534개, 총 164,011개 압축파일 내부 레코드를 포함해 256,138개 searchable entries의 private SQLite FTS5 인덱스를 만들었다.
- 위치: /home/cosmosapjw/Downloads/htt_r92_private_index/R92_SEARCH_INDEX.sqlite. 사적 파일명·전체 경로와 ZIP/TAR 내부 member 목록은 이 디렉터리에만 남겼고 Git에는 인벤토리 전체를 게시하지 않았다.
- ZIP 예외 1개: rec_bianchi/20261016/REC_REI_THERM01_STAGE_C_20261022.zip. 유효한 ZIP 헤더는 보이나 central directory 해석 실패. 새 데이터를 추측하거나 추출하지 않았다.
- BASS, REC, REI, HTT 네 실제 연구 저장소의 HEAD, dirty, remote identity를 대조했다. REC에 이미 존재한 dirty files는 건드리지 않았다.
- 공식 GitHub 관련 저장소 9개: htt_base, bass, rec_bianchi, rei_bianchi, BASS_HE, bass_cr, bianchi_phase_r, HEP-ASTRO-COSMO, cosmo_lab. 마지막 cosmo_lab은 private metadata-only. HTT active branch recursive GitHub tree API는 truncated였으므로 정확한 HEAD의 로컬 Git tree 34,068 files를 보조 검증했다.

## Dossier를 이용한 직접적인 과학적 연결

Dossier I Homogeneous Geometry: Bianchi의 일반 3D Lie 구조상수, Jacobi, Codazzi, 3-curvature, Class A/B, tilted 다성분 momentum source와 제약 전파. HTT R49 general tilted background에 대한 독립 oracle의 후보. 실제로 수식의 time variable, H normalization, frame rotation, 3D Ricci 부호와 source momentum normalization을 비교하기 전에는 라이브 forward 모델로 채택하지 않는다.

Dossier II Kinetic Transport: mass-shell, covariant polarized photon transport, finite matter boost, screen holonomy, Thomson collision. HTT의 R49 general background를 polarized photon source와 연결할 가장 직접적인 경로. 그러나 재결합·재이온화의 실제 전자 이력과 초기/관측 경계조건을 지정해야 한다.

Dossier III Atomic Processes와 Dossier IV Reionization: hydrogen/helium source, opacity, electron current, optical depth, finite redshift-bin response. REC Bianchi I characteristic와 REI electron/material source를 HTT P5 high-l hierarchy에 입력하기 위한 물리적 provenance가 될 수 있다. 미승인 REC/REI PR의 draft 결과를 full release-matched visibility로 간주하지 않는다.

Dossier V Conservative Approximation: source perturbation의 adjoint observational error, constraint residuals. \ell_max 계층 절단을 높일 때 필요한 observables-directed error control에 적합하다.

Dossier VII Observation: Kasner finite-aperture polarized detector and boost/beam response. HTT R89/R91 저다중극 morphology와 계기적 angular convolution의 대조 실험을 구축하는 출발점.

Dossier VI Nuclear Reactions는 초기 조성 모형의 source로는 중요하지만 곧바로 Bianchi family를 판별하는 likelihood가 아니다.

## 코드별 채택·제한

1. BASS bianchi/charts/class_a_tilted_multi.py, class_b_tilted.py : Class A/B constrained tilted background, source q and pi, exceptional strata. HTT R49와 공유하는 \sigma, N, a, omega, frame을 equation-level로 비교해야 한다.
2. BASS bianchi/physical/frame_transport.py: orthonormal triad transport dE/dtau=(I+Sigma+Omega)E. Rotation generator sign convention의 독립 검증 요구.
3. BASS bianchi/matter/hierarchy.py: PSTF moment hierarchy, L_MAX_SUPPORTED=6; 현재 BASS의 물리적 고-\ell 전체 역학 해석기라고 주장할 수 없음.
4. BASS bianchi/matter/grid_boltzmann.py: angular quadrature, massless Thomson kernel, positivity/invariants. Basis-free collision oracle.
5. BASS bianchi/q/polarization.py: basis-free Hermitian J_ab, screen transport, Thomson/geometry. Pure Python selected test 3/3 PASS.
6. BASS bianchi/q/transport.py: native Rust runtime 필요. Current BASS wheel에 RF00 요구 rayon_thread_pool_size 심볼이 없음. 별도 wheel 격리본은 심볼이 있지만 SBOM byte identity 검증에서 거부. 실제 l=4 high-l test 1 PASS / 1 FAIL이며 수학적 틀림으로 판정하지 않는다.
7. REC characteristic_angular.py 및 background/axisymmetric_bianchi_i.py: Bianchi I frequency/angle characteristic과 안정한 positive optical transfer. 임의 Class B의 physical polarization으로 곧바로 확장하지 않는다.
8. REI current_OPERATOR_SPEC.md, current_STATE_LEDGER.md: source-defined electron/opacity, current material clocks; 실제 coupled full Bianchi high-l visibility 품질과 별개.
9. Mayukh ver3 HTT.zip의 htt/catalog_likelihood.py: low-z tilted redshift/distance-modulus model과 null/robustness prototype. CF4 post-intercalibration covariance와 동일시하면 안 된다.
10. Legacy bianchi_departure_v091_github.zip의 biposh_masked.py: mask variance를 단순 1/fsky 보정하는 구형 prototype. 실제 mask-induced off-diagonal covariance 및 BipoSH coupling inversion은 미구현이므로 production high-l likelihood로 그대로 사용하면 안 된다.
11. Legacy bass_htt_mio_github_ready_current.zip의 PR13AG: L=4 -> 6 -> 8 projected multipole hierarchy skeleton. Full tilt-aware collision, full observer T/E/B, exact angular PDE는 원래 명시적으로 제외됨.
12. Legacy mz_cmb_truncation_artifacts.zip: tail/absorbing boundary, finite-pole frequency fit 오차 제어 관련 참고. 지금의 GR physical hierarchy에 무검증 이식 금지.

## 고다중극으로 저다중극 한계를 보완할 수 있는가?

한정적으로 그렇다. 정확한 physics transfer, beam/selection/foreground와 release-matched null이 있을 때 high-l은 Bianchi scalar/vector/tensor mode와 coherent alignment의 추가 제약을 제공한다. Saadeh et al. 2016은 Bianchi high-l power를 포함하는 분석을 출판했다. 그러나 해당 연구는 단순한 \(C_\ell\)-only high-l Gaussian fit이 아니라 physical Bianchi radiation forward model과 그 likelihood를 사용했다.

핵심 구별:

- Model-independent off-diagonal BipoSH: 데이터 기반 1차 진단 경로. Model-independent 검출 자체가 특정 Bianchi family attribution은 아니다. Full mask/beam/noise/foreground coupling과 MC가 필요.
- Deterministic coherent Bianchi high-l T/E/B: BASS/REC/REI source와 polarized hierarchy를 coupling할 수 있다면 강력한 family discriminator. L<=6 현재 구현, native ABI·recombination source·convergence blocker가 남는다.
- PlikLite high-l scalar reference: HTT R91에서 실제 613-bin 계산 완료. 이는 nuisance/reference spectrum baseline이며 morphology phase를 잃기 때문에 단독으로 family attribution 불가능.

### 독립 Wigner 3j 구성

가정된 quadrupolar modulation \(T'(\hat n)=[1+gY_{20}(\hat n)]s(\hat n)\)에서는

\[
\langle a_{\ell m}a^*_{\ell' m'}\rangle
=C_\ell\delta_{\ell\ell'}\delta_{mm'}
+g(C_\ell+C_{\ell'})G_{\ell m,\ell'm'}+O(g^2),
\]

\[
G=(-1)^m\sqrt{\frac{5(2\ell+1)(2\ell'+1)}{4\pi}}
\begin{pmatrix}\ell&2&\ell'\\0&0&0\end{pmatrix}
\begin{pmatrix}\ell&2&\ell'\\-m&0&m'\end{pmatrix}.
\]

\(L=2,M=0\)에서 \(\ell'=\ell,\ell\pm2\), \(m'=m\)이므로 \ell=40의 \ell'=38,40,42만 3j 계수가 0이 아니다. Wolfram와 SymPy로 확인했다. 이 구성은 대각 \(C_\ell\)만으로는 볼 수 없는 정보를 high-l off-diagonal correlation에 추가할 수 있다는 증명용 예제다. 하지만 toy response이며 Bianchi Einstein–Boltzmann hierarchy의 직접 결과는 아니다.

참고 원전: Pontzen & Challinor (2007) https://arxiv.org/abs/0706.2075 , Saadeh et al. (2016) https://arxiv.org/abs/1604.01024 , Saadeh et al. (2016) https://arxiv.org/abs/1605.07178 , Marcori & Pereira (2016) https://arxiv.org/abs/1612.01994 .

## 제3차 루프를 위한 정확히 3개 연구 경로

1. Geometry/optics lane: R49와 BASS Class A/B tilted initial-state/connection의 수학적 재현 및 finite-z Jacobi null geodesic. **성공:** 동일 물리 상태의 Hamiltonian/Codazzi/curvature/observer-frame residual, FLRW/Type I/VI_-1/9 퇴화 극한 일치. **중단:** frame clock 또는 source flux/tilt 단위 불일치가 있으면 semantic bridge HOLD.
2. High-l morphology lane: 기존 PR3 map과 source-qualified MC에서 \(\ell\ge4\) off-diagonal \(A_{\ell_1\ell_2}^{LM}\), beam, mask coupling과 source-specific null을 비교. **성공:** exact Wigner selection, proper coupling inversion 및 matched injection recovery. **중단:** 1/fsky-only prototype으로 publication p-value 계산 시.
3. Physical polarized transfer lane: BASS basis-free Thomson + REC characterized geodesic rays + REI electron/opacity + high-l \ell truncation. **성공:** valid immutable native provenance, \ell=4/6/8 convergence with units and positivity/constraint invariants, concrete matched T/E/B. **중단:** native wheel, recombination/owner source unavailable; no synthetic source promotion.

과학 상태: R78 60 nodes/129 edges/NEXT_ID SQ-CF4 unchanged, R90 solver-free 17 units and separate 5 native-transfer units preserved. R92 preparation does NOT execute the third 10 theory + 10 coding full campaign. R92 reviewed sources and formulated an explicit executable bridge agenda and high-l toy numerical oracle only.
