# Source-qualified historical excerpts

The following excerpts retain their historical assertions. They do not certify truth, novelty, proof completion, or current applicability. Source identity remains as recorded by the catalog; missing original Git identity is not repaired by inference.

## role-61db4486cf9c9245 — NT2-A1

Source: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 9–22; content identity `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; excerpt SHA-256 `745ec2c80180d5b12cd793a16e540d1ad69fee0d3c2b667cd3802df0c7683288`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-61db4486cf9c9245

```text
### NT2-A1 — Genuine multi-multipole Fisher–Cramér–Rao floor on `F_shear`  [Provable; flagship]

**Statement.** Let `F_shear` depend on the low-ℓ CMB through the multipole powers `{C_ℓ}_{ℓ≥2}`, with response `r_ℓ = ∂ln C_ℓ/∂ln F_shear` (`r₂=1` by NT-A1; `r_{ℓ>2}>0` because the shear sources `ℓ>2` via the EGS gradient/octupole chain). For Gaussian multipoles on a fraction `f_sky` of sky, the Fisher information is `I = Σ_{ℓ≥2}(2ℓ+1)/2·f_sky·r_ℓ²`, and the Cramér–Rao bound on *any* unbiased estimator is
`σ(F_shear)/F_shear ≥ I^{−1/2} = [Σ_{ℓ≥2}(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`.
This is **strictly below** the single-ℓ value `√(2/(2·2+1))=√(2/5)≈0.632`, and decreases as more multipoles are included; sky cuts (`f_sky<1`) raise it.

**Why it matters (audit fix).** The report's NT-A3 labels the single-estimator sampling dispersion a "Cramér–Rao floor / irreducible / unmeasurable below 63%". That is not a floor over all estimators. NT2-A1 supplies the actual floor and shows it is lower — the report's "floor" language becomes correct only once stated as NT2-A1.

**Proof sketch.** For independent Gaussian `a_{ℓm}` with variance `C_ℓ`, `−∂²lnL/∂C_ℓ² ⇒ I(C_ℓ)=(2ℓ+1)f_sky/(2C_ℓ²)`; chain through `r_ℓ` to `F_shear` and sum the independent multipoles (Fisher additivity). The single-ℓ term recovers `√(2/5)`; any `r_{ℓ>2}>0` strictly increases `I`, lowering the floor. ∎ (MC-verified: a multipole-combining MLE achieves the floor, ratio→1.)

**Numerical support.** NT2-A1: floor 0.632→0.474→0.424 (`L=2,5,20`, `f_sky=1`); `f_sky=0.7` raises it; MC MLE ratio 0.99–1.00.

**To close.** Replace the toy response `r_ℓ` with the exact covariant ℓ=2/ℓ=3 coefficients and a real low-ℓ transfer; quote the floor with Planck `f_sky` and mask coupling.
```

## role-ac63913e9a4082d8 — NT2-A2

Source: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 23–30; content identity `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; excerpt SHA-256 `089f48a81d1c7003d1e7e5039332a13bb69658b905ba26599d79c7ee441f9842`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-ac63913e9a4082d8

```text
### NT2-A2 — Quadrupole+octupole sufficiency / EGS information saturation  [Conditional]

**Statement.** At leading EGS order the shear sources only `ℓ=2,3` appreciably (`r_ℓ` decays for `ℓ>3`); hence `(a₂,a₃)` is an approximately sufficient statistic for `F_shear`, and the marginal Fisher information from `ℓ>3` is bounded by `Σ_{ℓ>3}(2ℓ+1)/2·f_sky·r_ℓ²`, which converges. Measuring beyond the octupole yields diminishing returns for the shear-filling.

**Proof sketch.** Sufficiency from the factorisation of the Gaussian likelihood given `(C₂,C₃)` when `r_{ℓ>3}≈0`; the bound is the Fisher tail sum, convergent for any decaying `r_ℓ`. ∎

**To close.** A dedicated experiment computing the Fisher tail with the real `r_ℓ`; quantify the `(a₂,a₃)` sufficiency gap.
```

## role-93d992474af4a17c — NT2-A3

Source: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 31–40; content identity `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; excerpt SHA-256 `48d456ce7338d83f7e75e69f88a9a280a7999135bf6ddeef5d616b1ed0f4b44a`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-93d992474af4a17c

```text
### NT2-A3 — Registered global exceedance bound  [Conditional → Forecast]

**Statement.** For a frozen family of `m` low-ℓ statistics, convert each to a tail score, take the max, and form the rank Monte-Carlo p-value with the `+1` correction: `p_global=(#{sim max ≥ obs max}+1)/(N+1)`. Then `p_global ≥ max_i p_local,i` (no look-elsewhere undercount), and the registered exceedance `Π` over the family is calibrated. This makes the K1 "not globally significant" statement a *theorem* about the estimator, not a caveat.

**Proof sketch.** The max-scan rank statistic dominates each component rank; the `+1` correction bounds the estimator from below. ∎

**To close.** Run on the public Planck E2E ensemble (see `BLOCKER_SOLUTIONS.md`, K1).

---
```

## role-7656eee17e6a41ff — NT2-B1

Source: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 43–54; content identity `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; excerpt SHA-256 `0496ca713eb2000a7e9005ae46c4fc2127c8e35d92d7265061b5c72081de036d`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-7656eee17e6a41ff

```text
### NT2-B1 — Two-sided quadrupole+octupole shear/`F` bracket  [Conditional; flagship]

**Statement.** Under H3 (`R_EGS=a₃/a₂≤R*`), the shear is bracketed by the observed quadrupole+octupole:
`a₂·κ/(1+R_EGS) ≤ Σ ≤ C_up·a₂`,
so `F_shear ∈ [ (a₂κ/(1+R_EGS))²/x_max , (C_up a₂)²/x_max ]`. The **lower** bound is the new, strong content: a **nonzero** CMB quadrupole **forbids a vanishing shear-filling** — an exclusion of zero at fixed `a₂`, not merely an upper limit.

**Proof sketch.** Upper: MES. Lower: the ℓ=2 relation `a₂=κΣ + (derivative correction)`; H3 bounds the derivative correction by `R_EGS·a₂`, so `Σ ≥ a₂/(κ⁻¹(1+R_EGS))`. ∎ (verified: `F_lo>0` in all rows.)

**Numerical support.** NT2-B1: e.g. `a₂=3×10⁻⁵, a₃=6×10⁻⁶ (R_EGS=0.2)` → `F_shear∈[2.45×10⁻⁶, 7.88×10⁻³]`, bounded away from zero.

**To close.** Exact MES upper constant and the covariant derivative-correction coefficient; quote the bracket with Planck `a₂,a₃`.
```

## role-268fdb1bddd84233 — NT2-B2

Source: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 55–64; content identity `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; excerpt SHA-256 `3f35ab66077975ccc2a2ba9cdbf6cd89c66141b147ab40da9f0108b6ce2719c8`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-268fdb1bddd84233

```text
### NT2-B2 — GR shear-memory-sourced depth transport of `G_F`  [Conditional]

**Statement.** Using PAPER-B's shear-memory law `σ̇=−3Hσ+3H²Π` (`Π` the tilt anisotropic stress), the depth gap obeys a transport equation whose source is `Π(z)`: a depth-evolving `Π(z)` produces a depth-evolving `G_F(z)`, while a steady `Π` relaxes `G_F` toward a constant (EGS-like). This upgrades NT-B3's "a `ΔF` trend is attributable to the tilt only with a response-rank gate" to "the tilt anisotropic stress is the **explicit GR source** of the depth gap."

**Proof sketch.** Integrate the shear-memory ODE with source `3H²Π(z)`; `F_shear(z)=σ(z)²/x_max`; differentiate along the line of sight. Steady `Π` → `σ→` const → flat `G_F`; growing `Π(z)` → growing `σ(z)` → depth-dependent `G_F`. ∎ (verified.)

**Numerical support.** NT2-B2: steady `Π` → `G_F` spread 0; growing `Π(z)~z` → spread 2.45.

**To close.** The real `H(z)` and a survey-matched depth binning; couple to the prior tomographic forecast.
```

## role-9526674fe35823d9 — NT2-B3

Source: `audit_files.zip!/egs_extension_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 65–74; content identity `8111df9ea26f901196aa4fac7e29c4c5dc57fc05588004161615aca001e31d3a:dd0517db`; excerpt SHA-256 `440386daefb144846d41ce073779a5c7429064f3a0fd3d6219f79a012b96c9b2`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-9526674fe35823d9

```text
### NT2-B3 — Vorticity joint blind-sector no-go  [Provable, grounded]

**Statement.** The vorticity term `W²_std` in `x_C` is unconstrained by the two observational channels the program uses, *simultaneously*: (i) CMB temperature multipoles do not bound the curl/magnetic-Weyl sector at EGS order (H3/Weyl loophole), and (ii) radial peculiar-velocity data carry no vorticity, since `n^aΩ_ab n^b=0` exactly for any antisymmetric `Ω` (PAPER-A A-radial-novortex). Therefore no estimator built on CMB-temperature + radial velocities alone can constrain the comparator's vorticity term — a strong no-go on the diagnostic's reach.

**Proof sketch.** (ii) is an algebraic identity (`Ω` antisymmetric ⇒ `n·Ω·n=0`); (i) is the Weyl loophole (NUWL 1999). The union closes both channels. ∎ (verified: radial projection 3.3e-16; CMB-T sensitivity 0.)

**To close.** State which *additional* channel (tangential velocities, polarisation B-modes, or the native low-ℓ morphology) re-opens the vorticity sector.

---
```

## role-9924acbc3185d19c — T8

Source: `docs/audits/external_2026-07-09/critical_review/theorem_candidates.md`; original lines 75–84; content identity `ec2c68c146b714e64d967885c83bd08392d6a69f55a8cf541e3d6ef638b2f063:dd0517db`; excerpt SHA-256 `d5ef144048398d61a98ba5dc8f62fbdbe2ba60f89ddeab39e0e82cc59577f420`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-9924acbc3185d19c

```text
## T8. Response-class quotient theorem

**Statement.** Whitened response rows/columns의 equivalence relation으로 legacy family labels를 quotient하면 현재 관측 support에서 구별 가능한 response classes만 남는다.

**Assumptions.** Registered feature map, nuisance-projected whitened response matrix, tolerance policy.

**Proof path.** Identifiability equivalence \(\theta\sim\theta'\iff R\theta=R\theta'\). Quotient parameter space의 Fisher rank가 identifiable dimension.

**Numerical witness.** Column duplication/row duplication examples. 포함 코드에서 column duplication은 rank 증가 없음, row duplication은 noise correlation \(\rho\)에 따라 Fisher factor \(2/(1+\rho)\).
```

## role-1df684ccd0112e30 — T2′

Source: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md`; original lines 30–44; content identity `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; excerpt SHA-256 `f2083c022dcd262c72b633440e2f6b6666d7a76151fe5c13ff3aafe9b2a3b7e0`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-1df684ccd0112e30

```text
## §2. T2′ — joint-대-naive 구간의 엄격성 판별 (P36의 강화; M1의 반전)

**정리 T2′.** P36의 세팅(공유 널 성분 \(s \in \mathcal{S} = \prod_j [s_j^-, s_j^+]\), \(N(s) = n + c_N \cdot s\), \(D(s) = d + c_D \cdot s > 0\), \(n \in [n^-, n^+]\), \(d \in [d^-, d^+]\))에서:

(i) **포함**: joint 구간 ⊆ naive 구간 (항상).
(ii) **상한 등식 판별**: joint 상한 = naive 상한 \(\iff \arg\max_{s \in \mathcal{S}} c_N \cdot s \,\cap\, \arg\min_{s \in \mathcal{S}} c_D \cdot s \neq \emptyset\). 박스에서 이는 \(\forall j\) (비퇴화 구간): \(c_{N,j} c_{D,j} \le 0\)과 동치다.
(iii) **엄격성**: 따라서 상한에서 포함이 엄격 \(\iff \exists j:\ c_{N,j} c_{D,j} > 0\)이고 \(s_j^- < s_j^+\). 하한은 \(\arg\min c_N \cdot s \cap \arg\max c_D \cdot s\)로 대칭.

**증명.** (i) naive는 \((s_N, s_D) \in \mathcal{S} \times \mathcal{S}\) 위의 최적화, joint는 대각 \(\{(s,s)\}\) 위의 최적화 — 부분집합 위의 sup는 크지 않다. (ii, ⇐) 교집합에 \(s^\* \)가 있으면 naive 상한 \(= \frac{n^+ + c_N \cdot s^\*}{d^- + c_D \cdot s^\*}\)이 대각 원소 \((s^\*, s^\*)\)에서 달성되므로 joint 상한과 일치. (ii, ⇒) 박스에서 \(\arg\max c_N \cdot s\)는 \(\{s_j = s_j^+ \text{ if } c_{N,j} > 0;\ s_j^- \text{ if } c_{N,j} < 0;\ \text{임의 if } c_{N,j} = 0\}\)의 곱집합이고 \(\arg\min c_D \cdot s\)도 마찬가지. 두 곱집합의 교집합이 공집합 \(\iff\) 어떤 \(j\)에서 요구 꼭짓점이 상반 \(\iff c_{N,j} c_{D,j} > 0\) (비퇴화 \(j\)). 교집합이 공집합인 경우, naive 상한을 주는 어떤 \((s_N, s_D)\)도 \(s_N \neq s_D\)이며, 고정 \(s\)에 대해 \(\frac{n^+ + c_N \cdot s}{d^- + c_D \cdot s}\)는 경쟁 성분 \(j\)에서 \(s_j\)를 어느 쪽으로 움직여도 분자·분모가 같은 방향으로 움직여 진성 손실이 생긴다: 구체적으로 \(f(s) = \frac{a + c_N \cdot s}{b + c_D \cdot s}\)의 \(s_j\)-도함수는 \(\frac{c_{N,j}(b + c_D \cdot s) - c_{D,j}(a + c_N \cdot s)}{(b + c_D \cdot s)^2}\)로, naive가 요구하는 두 극값을 동시에 만족하는 \(s_j\)가 없으므로 \(\max_s f < \) naive 상한 (엄격). (iii)은 (ii)의 대우. ∎

**[반전]** M1의 반례(정렬 레짐 등식)는 이제 정리의 한 분기다. v6의 충분조건적 진술("항상 엄격")은 필요충분 판별로 대체되어 **원문보다 강한** 정리가 되었고, "joint 구성은 결코 naive보다 나쁘지 않으며 언제 정확히 이기는지 안다"는 완결적 주장으로 승격되었다.
**[검증]** FORT02: 유리수 정확 산술(허용오차 0) 371/371 판별 일치; 엄격 260건, 등식 111건; v6 문구에 대한 명시 반례 1건 보존.

---
```

## role-23bc0ad168e0e8f7 — T4′

Source: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md`; original lines 45–61; content identity `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; excerpt SHA-256 `5e8341a27a33071f9f1da51136f10f22e64209ef9b3063f5ce447682613b06df`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-23bc0ad168e0e8f7

```text
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
```

## role-d5077977ee82eac0 — T3-lin

Source: `docs/audits/external_2026-07-09/referee_fortification/06_strengthened_theorems_ko.md`; original lines 103–112; content identity `4bacfb0d7d0edf22e53526c3b31181a8de41e1cd97b2dc4ffd98e8f267b72571:d283db23`; excerpt SHA-256 `20880995ed2fdd2771f2725f282cdbdddf3dc499c27e956bf7a57101f5ad0231`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-d5077977ee82eac0

```text
## §7. T3-lin — 선형화 실현 정리 (P31 승격의 중간 단계; M2 대응) — 증명 스케치 + 잔여 보조정리

**명제 T3-lin (등록 목표).** \(x_{\max} \ll 1\)인 임의의 목표 \((\Sigma^2_\*, W^2_\*, \Omega_{t\*}, \Omega_{k\*})\) (부호 박스·콘 준수)에 대해, FLRW 배경 위 선형화 초기데이터와 물질 배치가 존재하여 (i) Gauss·운동량 제약을 선형 차수에서 만족하고, (ii) 정규화 불변량이 목표값을 재현하며, (iii) 물질 부문이 약에너지조건을 만족한다. 따라서 T1′ 구간의 sharpness는 선형화 레짐에서 물리 명제다.

**증명 스케치.** (1) \(\Sigma^2_\*\): Bianchi I형 균질 전단 모드 — 운동량 제약이 자동 충족(대각 전단, \(q = 0\)). (2) \(\Omega_{k\*}\): FLRW 곡률 분기 혼합(등방 성분)과 Bianchi V/IX형 균질 곡률 모드; open/closed 부호 모두. (3) \(\Omega_{t\*}\): T9′ 따름정리의 반대-틸트 쌍 — 순 플럭스 0으로 운동량 제약 무부담. (4) \(W^2_\*\): 선형 벡터(회전) 모드 — 운동량 제약이 \(\nabla^2\)-역으로 \(q_{\rm vec}\)를 결정하며, 이는 (3)의 쌍에 소량의 비대칭 틸트를 얹어 공급; 진폭 자유. (5) 에너지조건: 모든 모드 진폭이 \(O(\sqrt{x_{\max}})\)이므로 배경 \(\mu > 0\)에 대한 선형 교란으로 유지. **잔여 보조정리 (등록 필요):** (4)에서 벡터 모드의 \(\omega\)와 (1)의 \(\sigma\)가 2차 결합 없이 목표 4-튜플을 독립 조준할 수 있음 — 선형 차수에서는 모드 중첩의 선형성으로 성립하나, "congruence 선택(정규 vs 물질 프레임)의 규약 고정" 문장을 정확히 써야 한다. 완전판(비선형, King–Ellis 틸트 Bianchi V 불변량 사상)은 WBS-C1.

**[반전]** M2("sharpness는 물리 명제로 미증명")는 "선형화 레짐(comparator의 실사용 영역 전체)에서 증명, 비선형 완전판은 등록된 정리 후보"로 재배치된다 — 갭의 인정이 아니라 정리 사다리의 명시.

---
```

## role-b9902c3443c8cbae — T2

Source: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md`; original lines 25–34; content identity `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; excerpt SHA-256 `eff6969a539e39ba8c211d30e6bb4401f958a9a44593ac886d5401a5cdb2faac`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-b9902c3443c8cbae

```text
## T2. Local constrained-data sharpness theorem for P31

**Statement.** Let \(g\) be sufficiently small in the registered HTT component cone and let the branch specify an equation of state and energy-condition domain. Under nondegeneracy of the York/conformal constraint operator, each endpoint of the P26 identified interval is realized by a local CMC initial-data family whose first-jet invariants match the endpoint components up to controlled \(O(\|g\|^2)\) residual; after conformal correction the Hamiltonian and momentum residuals vanish to solver tolerance.

**Proof route.** Start with local nearly-FLRW initial data, add transverse-traceless shear, stream-realized tilt stress, and small anisotropic curvature perturbations. Check first-order constraints. Apply implicit-function/conformal method to correct residuals. Use continuous dependence to preserve the comparator endpoint value up to controlled error.

**Numerical witness.** Implement `constraint_realization_endpoint_solver.py`: sweep eps, solve correction, report residual norms and convergence slopes.

**Why this strengthens the paper.** It turns “sharp over an abstract cone” into “sharp over an explicit physically realizable local-data class.”
```

## role-003903a09bc241a0 — T3

Source: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md`; original lines 35–42; content identity `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; excerpt SHA-256 `9e24713102953ccf779c4a6cb526753f632f9088d3e1f42f82efccc6e5d5fe2e`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-003903a09bc241a0

```text
## T3. Exact equality conditions for P36 joint depth-gap intervals

**Statement.** Let \(S\) be a compact polytope and \(N(s)=n+c_N\cdot s\), \(D(s)=d+c_D\cdot s>0\). The joint feasible interval for \(G_F=N/D\) is the exact image of the diagonal feasible set and is always contained in the marginal quotient interval. Equality of the lower endpoint holds iff the numerator-minimizing feasible face and denominator-maximizing feasible face contain a common point satisfying the linear-fractional lower optimum. Equality of the upper endpoint holds iff the numerator-maximizing feasible face and denominator-minimizing feasible face contain a common point satisfying the upper optimum. Outside these compatibility conditions, inclusion is strict. For generic coefficient vectors, equality conditions define a lower-dimensional algebraic/face-incidence set.

**Proof route.** Use Charnes-Cooper transform or quasiconvex/quasiconcave linear-fractional optimization on polytopes. Marginal quotient optimizes over \(S\times S\), joint over diagonal \(\Delta(S)\). Strictness reduces to whether product-space extremizers intersect the diagonal.

**Numerical witness.** Included in `scripts/strengthening_core.py`; strictness is generic in random coefficient draws, while the critique equality case is reproduced exactly.
```

## role-f6399f090540f95a — T4

Source: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md`; original lines 43–50; content identity `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; excerpt SHA-256 `18950477490e950b09bcfb2922c9251aa459d3393ea36cc54a215fcde419609c`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-f6399f090540f95a

```text
## T4. Known-covariance two-stage identified-set coverage

**Statement.** Under Gaussian whitened noise with fixed response matrix R, the residual projection statistic is \(\chi^2_{m-r}\) and independent of the reachable projection. Stage-1 EMPTY controls specification-test false rejection at \(\alpha_1\). Conditional stage-2 ellipsoid covers the reachable projection at \(1-\alpha_2\). For scalar \(x_C\) inside an interval-identified set, Imbens-Manski critical values give pointwise parameter coverage; two-sided endpoint/projection intervals give simultaneous identified-set coverage.

**Proof route.** Orthogonal projection of Gaussian vector into column space and residual space; then standard partial-identification endpoint logic.

**Numerical witness.** Included: residual EMPTY rate at zero shift is 0.04868 for \(\alpha_1=0.05\); power rises with residual shifts.
```

## role-57a3c3d765388607 — T5

Source: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md`; original lines 51–58; content identity `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; excerpt SHA-256 `2fa48c289ca503deac1ed7e2dbaac2f142509cce798963862e3ff135b34a5712`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-57a3c3d765388607

```text
## T5. Estimated-covariance robust endpoint coverage

**Statement.** If covariance is estimated from \(N_{\rm sim}\) Gaussian simulations, the inverse sample covariance is biased. Using uncorrected Gaussian plug-in precision inflates reachable-sector precision. Hartlap correction removes first-order precision bias; Sellentin-Heavens covariance marginalization replaces the Gaussian likelihood by a multivariate-t form and propagates covariance uncertainty. Endpoint intervals must condition on this policy.

**Proof route.** Wishart expectation of inverse covariance; compare plug-in, Hartlap-corrected, and covariance-marginalized likelihood.

**Numerical witness.** Included: for p=20, raw precision trace ratio is ~1.075 at Nsim=300 and ~1.036 at Nsim=600; Hartlap-corrected mean is ~1.
```

## role-a961420736a6ae59 — T8

Source: `docs/audits/external_2026-07-09/strengthened_publication/theorem_upgrade_candidates.md`; original lines 75–82; content identity `c8c248d188e8bcaae0ad38e5c29501c7efd93703b5d1a81efbcb43d0a4a40163:dd0517db`; excerpt SHA-256 `86f7ad6dbddcc42416f1326c3570e2dd1a4f16e2ca1db03781104b037a32d9c3`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-a961420736a6ae59

```text
## T8. Scalar/BiPoSH non-equivalence theorem

**Statement.** Diagonal \(C_\ell\)-style compression annihilates off-diagonal \(L>0\) covariance morphology. Therefore scalar low-ell statistics and BiPoSH covariance statistics are non-equivalent projections; agreement or disagreement between them is a diagnostic pattern, not a geometry label.

**Proof route.** Schur orthogonality and rotational decomposition of covariance into BiPoSH coefficients.

**Data witness.** K1 map-stability matrix must report scalar and BiPoSH channels side by side with separate nulls.
```

## role-229717dd6ca7353f — T1

Source: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md`; original lines 7–55; content identity `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; excerpt SHA-256 `b3e26d13c1a607d489c6b4f5f08997ec6c5bfa32298aa69848d07cec5e523a35`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-229717dd6ca7353f

```text
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
```

## role-33388bdc10392e43 — T4

Source: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md`; original lines 110–148; content identity `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; excerpt SHA-256 `5de7c54905a62010d94123ef6393c861cd3e19b50daab2aaa3a4deed601f3e7e`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-33388bdc10392e43

```text
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
```

## role-38aed17ce6749550 — T7

Source: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md`; original lines 183–194; content identity `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; excerpt SHA-256 `6120e6b1b2fbfcc83fa022ee5372ee64122e14510b0c1c84c36bb22d72a58c58`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-38aed17ce6749550

```text
## T7. Observational equivalence implies family non-identifiability

If two model families induce the same probability distribution for every observable in the adopted experiment,

\[
p(D\mid\mathcal F_1,\theta_1)=p(D\mid\mathcal F_2,\theta_2)
\]

under a parameter mapping covering the relevant support, no statistical test based on those observables can identify the family. Bayes factors then depend on prior volume and parameterization rather than data separation. This is the formal justification for equivalence-class reporting before a native morphology atlas exists.

---
```

## role-b454d1f327ac4d51 — T8

Source: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md`; original lines 195–224; content identity `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; excerpt SHA-256 `3eb161bf88c1245bfe6a07783f97f7d433b04c7ffe716be77d5baf9b24e67994`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-b454d1f327ac4d51

```text
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
```

## role-6dbdf98fdf5a865f — T9

Source: `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip!/htt_publishable_novel_analysis_program_2026-06-19/docs/04_theorem_candidates_and_proofs.md`; original lines 245–296; content identity `8530848e41eda1063b98d4ccd3a7e7af5827dd453a7df30fc4cb8a8110143ce2:dd0517db`; excerpt SHA-256 `5dad188d3b9ec2d4e74dd8085caa646978d86acc81935d0840affbd0d7d8b45b`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-6dbdf98fdf5a865f

```text
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

T9 converts the abstract rank condition into a survey-design statement: additional depth bins help only insofar as they add covariance-weighted response directions outside the local/systematic nuisance span.```

## role-cec19bb33424924a — T-A1

Source: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 11–20; content identity `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; excerpt SHA-256 `0227a70b82259956f4f967a6f8c4646f300bb2e782e2788fca68b07d9f45e67b`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-cec19bb33424924a

```text
### T-A1 — Cancellation / non-identifiability of isotropy from `x_C`  [Provable]

**Statement.** The signed map `x_C : ℝ⁴_{≥,≥,·,·} → ℝ` has a cancellation set `Z = {s : x_C(s)=0}` of codimension 1, and `sup_{s∈Z} ‖s‖ = ∞`. Consequently `x_C` is not a proper isotropy functional: for every `ε>0` there exist configurations with `|x_C|<ε` and total magnitude `M=‖s‖` arbitrarily large. Isotropy (`s=0`) is identifiable only from the sector vector, not from `x_C`.

**Proof sketch.** `Z` is the zero set of a nonzero linear functional on ℝ⁴, hence a hyperplane (codim 1). The ray `s(t)=t·(1,1,0,0)` lies in `Z` (since `Σ²−W²=0`) with `‖s(t)‖=t√2 → ∞`. For the `ε`-statement, perturb within `Z`. ∎

**Numerical support.** N1: explicit dim-3 null family; smallest-`|x_C|` decile spans `M` over ~10³×.

**To close.** State the dimension of `Z∩{physical cone}` and the precise sense in which the sector vector is the minimal sufficient statistic for sector identifiability.
```

## role-7f7d9023cba5b5c4 — T-A3

Source: `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip!/04_THEOREM_CANDIDATES.md`; original lines 31–40; content identity `f05a6b5aff005cf873671648ae644843bb6604750e8e193ba561188e7bae7f61:dd0517db`; excerpt SHA-256 `32a66c2be71d8e43f971eb5c1c62cf1efd58e6eed87104ece16a3e9e175297ab`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-7f7d9023cba5b5c4

```text
### T-A3 — Selection-marginalized boost–tilt separability  [Conditional → Forecast]

**Statement.** Let `b(z)` be the kinematic (boost) dipole profile including the redshift-selection correction of von Hausegger–Dalang (2025), and `τ(z)` a global-tilt profile with transition `z_T`. If `τ` is not in the span of `{b, ∂_β b}` over the observed `z`-range (a genericity condition satisfied when `z_T` lies inside the range), then the residual `r(z) = m(z) − \hat A\,b(z)` (with `\hat A` the LS boost amplitude) has zero expectation under the boost hypothesis and nonzero expectation under the tilt hypothesis, and the Fisher information for boost-vs-tilt separation is `F = Σ_z (Δr(z)/σ_z)² > 0`, growing with depth coverage `z_max` and source count `N` (`σ_z ∝ N^{-1/2}`).

**Proof sketch.** `r` is the projection of `m` onto the orthogonal complement of the boost template; under boost, `E[r]=0`; under tilt, `E[r]=` the component of `τ` orthogonal to `b`, nonzero by the genericity condition. `F` is the standard Gaussian two-hypothesis Fisher information. ∎

**Numerical support.** N3-A: residual AUC→1.0, Fisher sep→~8 with `z_max=3, N=10⁶`. N3-B: the naive flatness statistic is **not** a valid test (FPR→100% under selection stress) — only the residual statistic is calibrated.

**To close.** Replace the toy `b,τ` with the survey-specific selection function and a covariant tilt template (`06` T-B3); propagate the full covariance; report the forecast significance for DESI/Quaia/SKA.
```

## role-093c5a1eb17fd09f — T1

Source: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md`; original lines 7–29; content identity `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; excerpt SHA-256 `00327b1ff84a625c197c7783ce3cf9ac22a0ff82c6d82bebf40cf8b8e727c240`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-093c5a1eb17fd09f

```text
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
```

## role-a2bd0d37845fc770 — G3

Source: `docs/research_program/publishable_analysis_pack_2026-06-26/THEOREM_CANDIDATES.md`; original lines 111–121; content identity `1ae2208a62879350ab764671e53fb6be6713c92e15ed917ca196abf9484d494e:dd0517db`; excerpt SHA-256 `47f5ca4e4c3e5e98d75a1ac7639682d921e822ac591695122531cf088679b146`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-a2bd0d37845fc770

```text
### G3. Radial Vorticity Blindness And Transverse Reopening

Statement candidate:

For antisymmetric vorticity tensor `Omega_ij`, radial velocity projection satisfies `n_i Omega_ij n_j = 0` for every line of sight `n`. Therefore a radial-only field is structurally blind to that sector, while a transverse or affine realization channel can reopen rank.

Strong consequence:

- K6 must use realization-conditioned field information, not a curl-suppressed point field.
- A no-go result is publishable if the field owner only supplies curl-suppressed reconstructions.
```

## role-14e0eaea8a4d4aa4 — T-P1

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 3–8; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `5c857b9114f01c8b7cc082c06a15af726cbbade74c61a5872ac844c9e2c659cc`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-14e0eaea8a4d4aa4

```text
## T-P1 — Pole rotation covariance

power-tensor pole가 SO(3) active rotation에 공변하고 p~-p axis quotient에서 well-defined임을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-3e5ea17c2b08403a — T-P2

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 9–14; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `677e58d03771b5cf628551b65aa8a65ac50fa90f7e3725c19ce67e8f903758f4`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-3e5ea17c2b08403a

```text
## T-P2 — Pole degeneracy instability

eigen-gap가 0으로 갈 때 Davis-Kahan-type axis error bound가 발산함을 보여 direction abstention threshold를 정당화한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-8ac598c0250f194d — T-P4

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 21–26; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `9eb3bb84bfa1e7f81dcbb98b16574af57e376277f0ff50530ce7d237d3b704ac`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-8ac598c0250f194d

```text
## T-P4 — Observer endpoint separation

local Lorentz boost term이 remote dipole/quadrupole field source와 다른 boundary object임을 typed map으로 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-fb115ecca130a85b — T-P5

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 27–32; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `8c663c787074c4f8996921e25616eca49f6706d0330dce6c0a29beff11d0a5d7`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-fb115ecca130a85b

```text
## T-P5 — Cross-shell effective rank

correlated redshift bins의 information은 bin count가 아니라 covariance-whitened nonzero modes에 의해 결정됨을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-1bda2ebc3b4f17dc — T-P6

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 33–38; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `2d0db51400c15db6e1578dc54fb34f251adcf8e078308e9fe3f84cabc6520bf5`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-1bda2ebc3b4f17dc

```text
## T-P6 — Pole-definition stability set

여러 registered pole definitions의 intersection/union을 set-valued axis region으로 구성하고 coverage 조건을 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-313d321af1e56c2e — T-P7

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 39–44; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `85c815fac70cbd3caa1c4beee4a2dcfdacadadd2cdde0e32db431a93449f3024`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-313d321af1e56c2e

```text
## T-P7 — Source superposition non-identification

collinear local/systematic/global responses가 mixture weights를 비식별하게 만드는 kernel을 구성한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-954d5028c58233c4 — T-P12

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 69–74; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `0d4f9017ec4b94fee8d4a966822da68a82774140ebfd407dd738fd504213c527`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-954d5028c58233c4

```text
## T-P12 — E-optimal rank reopening

candidate response vectors의 convex design에서 minimum singular value를 최대로 하는 SDP와 dual certificate를 제시한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.
```

## role-2547259daf5ad54c — T-P18

Source: `external_fusion_round3/docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`; original lines 105–109; content identity `0ddb6c86671cd0a6949167fd7a316df7b87929ef054258814bfb57f240d2f1e8:d283db23`; excerpt SHA-256 `e42f6d7c5dc447e811b628695c596571460d3b362c922b7bffd9af4f50ed211a`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-2547259daf5ad54c

```text
## T-P18 — Common latent joint region

모든 probe가 동일 latent state를 공유할 때 marginal product envelope보다 sharp한 joint support image를 증명한다.

**Required witnesses:** analytic derivation, independent symbolic/numeric implementation, mutation, declared domain and downstream consumer test.```

## role-5829c7a188948867 — T2-JOINT-SUPPORT

Source: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md`; original lines 27–32; content identity `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; excerpt SHA-256 `d17063b44845988dc2514f3d3ce47d1928e966ac5127f6635a5ac9f0ef1d55b7`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-5829c7a188948867

```text
## T2-JOINT-SUPPORT — Support image on common feasible set

- **Track:** `I`
- **Proof route:** general compact-set theorem; box is a corollary
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.
```

## role-115cfcf017fdd1a5 — T2-PHYSICAL-SHARPNESS

Source: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md`; original lines 33–38; content identity `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; excerpt SHA-256 `60a4ccfba34e3f9c9a3b273910f91f49f8ae95efd2ac99628aabeb322cd80b38`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-115cfcf017fdd1a5

```text
## T2-PHYSICAL-SHARPNESS — Constraint/local/global endpoint attainability

- **Track:** `I→II`
- **Proof route:** construct initial data, local development and global branch certificates
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.
```

## role-f8486acfcdb96895 — T2-RESPONSE-QUOTIENT

Source: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md`; original lines 51–56; content identity `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; excerpt SHA-256 `4f804e5446e6c5d11cb37981e8cb9663b1dd88c8c42450278b527a5285c8a927`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-f8486acfcdb96895

```text
## T2-RESPONSE-QUOTIENT — Observable response equivalence quotient

- **Track:** `I→II`
- **Proof route:** prove refinement under row augmentation and rank uncertainty
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.
```

## role-5c06085a18fc989e — T2-ESTCOV-PID

Source: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md`; original lines 75–80; content identity `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; excerpt SHA-256 `35835536796da79c0052a91a6f9543d6c435a5aec534fb966e97602598ab6f96`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-5c06085a18fc989e

```text
## T2-ESTCOV-PID — Estimated-covariance partial-ID confidence

- **Track:** `I`
- **Proof route:** finite/asymptotic coverage with active boundaries
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.
```

## role-b939dc581755e9fc — T2-COMMON-MODEL

Source: `htt_external_fusion_round3_20260722.zip!/htt_external_fusion_round3_20260722/context/round2/docs/06_THEOREM_PROOF_BACKLOG_ROUND2.md`; original lines 111–115; content identity `d39fe1dc8876c1b7b6d6784deaae42b85be2a9d48cbf9686a43ba61cb65f9926:d283db23`; excerpt SHA-256 `6b2ae78f338a9dcbbfc696aba9afd6d52060b78205cdcf8ae6608ae6765ff869`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-b939dc581755e9fc

```text
## T2-COMMON-MODEL — Common latent cosmology joint identified region

- **Track:** `II/Joint`
- **Proof route:** one state generates all probes and constraints
- **Promotion:** statement, assumptions, counterexample registry, at least two independent lineages and downstream consumer tests are all required.```

## role-0b34575bc1215781 — T-GAUSS-RESTSPACE

Source: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md`; original lines 55–64; content identity `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; excerpt SHA-256 `548b1f5e389c8ee203be6055a71d2b60923c91f3629a367c6e8bbce88ab813cf`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-0b34575bc1215781

```text
## T-GAUSS-RESTSPACE — Vortical rest-bundle Gauss theorem

**Candidate statement.** nonintegrable rest distribution의 두 contraction conventions 관계와 canonical scalar를 정의하고 ω=0 hypersurface limit을 증명.

**Proof route.** Cartan structure equations + xAct.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-191.
```

## role-a729e95805590b41 — T-MES-INTRINSIC-DIPOLE

Source: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md`; original lines 85–94; content identity `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; excerpt SHA-256 `f1798c0e0715335f2126d10717619fbe8422ff4f52d6c4bd59e9728055ad9c66`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-a729e95805590b41

```text
## T-MES-INTRINSIC-DIPOLE — MES ceiling surface

**Candidate statement.** ε1,intrinsic를 포함한 geodesic/non-geodesic shear/vorticity/acceleration ceiling surface와 attribution admissibility.

**Proof route.** covariant multipole hierarchy first-principles derivation.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-193.
```

## role-a907fc87b0e2ef54 — T-STRUCTURAL-ROBUSTNESS

Source: `htt_legacy_revival_round2_20260721/prior_round1/htt_post_v10_strengthening_plan_20260721.zip!/htt_post_v10_strengthening_plan_20260721/proofs/THEOREM_PROOF_BACKLOG.md`; original lines 155–164; content identity `0a7f48ff68124e66bc18937e74c4e6c7ae686da075e9ba55de1cfe07a5a689c3:d283db23`; excerpt SHA-256 `16357da011cb1d3405b204f13213975b4324bf9f36a986e6dd8b9b095b104672`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-a907fc87b0e2ef54

```text
## T-STRUCTURAL-ROBUSTNESS — Structural set vs pipeline set calculus

**Candidate statement.** I(θ)와 R(pipeline)의 union/intersection 및 combined uncertainty semantics.

**Proof route.** set-valued statistics and decision theory.

**Decisive falsifier.** Assumption-complete counterexample, independent derivation mismatch, or certified numerical enclosure failure.

**Owning PR.** PR-201.
```

## role-ca2f8c0e26b96c29 — T1

Source: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md`; original lines 7–23; content identity `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; excerpt SHA-256 `a03e735b6c1bb9845ff866f67a7a71cd75b9ae8f859b70d1e6d1fafde045d932`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-ca2f8c0e26b96c29

```text
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
```

## role-ccf20aa164c0504d — T4

Source: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md`; original lines 56–70; content identity `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; excerpt SHA-256 `ad3ef42cf55dc223c52a7f3ce3dcec2e03641dcf7f65dd638b8159103dfb6908`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-ccf20aa164c0504d

```text
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
```

## role-b6f765deb06070d1 — T5

Source: `legacy/cf4_p0/packages/publishable_next/theorem_candidates.md`; original lines 71–83; content identity `60a8a8c93e05df897d78cf73d72902b80449b2bbe109e16aacf6c332d3d3c11f:dd0517db`; excerpt SHA-256 `971aecabf38d8b2a8891cf41a354d2dd90696b1019ff60e98403f3b2c3fb42bf`.

Catalog evidence: https://github.com/cosmosapjw-quantum/htt_base/blob/9b725899a25fa410e7c3686ce36afaa667d14646/docs/project_catalog/proofs/roles/evidence.md#role-b6f765deb06070d1

```text
## T5. Almost-EGS Promotion Gate

**Math/stat axis.** An almost-EGS residual bound can be promoted only if
acceleration, temperature-gradient, derivative, and Weyl diagnostic bounds are
all present with provenance.

**GR/cosmology axis.** This keeps EGS-type reasoning strong: exact isotropy
implies FLRW under the theorem assumptions, and almost-isotropy requires all
control terms, not only a quadrupole summary.

**Data axis.** K1 can be used as one observed input to this gate, but it cannot
alone produce an almost-EGS cosmological conclusion.
```

