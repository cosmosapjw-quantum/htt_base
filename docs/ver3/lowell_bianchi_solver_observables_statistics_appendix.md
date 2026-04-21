
# Low-\ell Bianchi Solver — Observables and Statistics Appendix
## 관측가능량 / 출력 형식 / 데이터 비교 / 통계 파이프라인 분리 문서

---

## 0. 문서 역할

이 문서는 본체 수학/물리/알고리즘 SSOT와 분리된 **관측가능량 및 통계 문서**다.
즉 여기서는 다음만 다룬다.

1. solver가 최종적으로 어떤 관측량을 출력해야 하는가
2. global tilt와 local boost를 출력 단계에서 어떻게 구분하는가
3. map / harmonic / covariance / likelihood를 어떤 계층으로 구현할 것인가
4. 실제 데이터 비교 전 어떤 validation gate가 필요한가

---

## 1. 출력 계층

### 1.1 primary field output

최소 출력은

\[
T(\hat n),\qquad Q(\hat n),\qquad U(\hat n)
\]

또는 동등하게

\[
a_{\ell m}^{T},\qquad a_{\ell m}^{E},\qquad a_{\ell m}^{B}
\]

이다.

### 1.2 secondary summary output

통계적 등방성이 성립하는 경우에만 familiar summary는

\[
C_\ell^{TT},\ C_\ell^{TE},\ C_\ell^{EE},\ C_\ell^{BB}
\]

로 줄어든다.
그러나 일반 Bianchi에서는 원칙적으로

\[
\left\langle a_{\ell m}^{X} a_{\ell' m'}^{Y*}\right\rangle
\]

의 full covariance 또는 deterministic template + stochastic covariance 형태가 더 자연스럽다.

### 1.3 deterministic + stochastic split

실제 출력은 다음 구조가 가장 정직하다.

\[
a_{\ell m}^{X}
=
a_{\ell m}^{X,{\rm det}}(\text{Bianchi background})
+
a_{\ell m}^{X,{\rm stoch}}(\text{perturbations})
+
a_{\ell m}^{X,{\rm boost}}(\text{observer/peculiar boost})
\]

즉
- background anisotropy
- stochastic perturbation
- local kinematic artifact
를 분리해서 보관해야 한다.

---

## 2. 출력 단계에서의 global tilt vs local boost 분리

### 2.1 global tilt
background/global tilt는 이미 solver 내부 state에 들어가 있어야 한다.
따라서 이것은 **forward model의 일부** 다.

### 2.2 local observer boost
local boost는 후처리다.
즉

\[
(T,Q,U) \mapsto (T',Q',U')
\]

또는
\[
a_{\ell m}^{X} \mapsto a_{\ell m}^{X\,\prime}
\]
로만 들어가야 한다.

### 2.3 금지 규칙

- global tilt가 구현되지 않았는데 observer boost만으로 geometry signal을 대체하는 것 금지
- boost artifact를 제거하지 않은 map을 geometry evidence로 쓰는 것 금지

---

## 3. 데이터 비교 단계

### 3.1 단계적 비교

#### Stage 0
- background-only deterministic template sanity check

#### Stage 1
- harmonic coefficient level comparison
\[
a_{\ell m}^{X}
\]
직접 비교

#### Stage 2
- map-domain comparison
\[
T,Q,U
\]
비교 및 mask/beam/noise 반영

#### Stage 3
- covariance-aware likelihood
\[
\mathcal L(d\mid \theta)
\]
평가

### 3.2 low-\ell에서 필요한 최소 정직성

low-\(\ell\) 비교라 하더라도 단순 \(C_\ell\)만 제시하면 부족할 수 있다.
특히 deterministic Bianchi template가 존재하는 경우에는
\[
a_{\ell m}
\]
레벨 비교가 기본이어야 한다.

---

## 4. 통계 모델 계층

### 4.1 deterministic template fit
background anisotropy orientation/amplitude를 deterministic template로 맞추는 단계

### 4.2 stochastic covariance fit
anisotropic covariance 또는 anisotropic transfer matrix를 포함한 Gaussian likelihood

### 4.3 hybrid model
\[
d = s_{\rm det}(\theta_{\rm Bianchi}) + s_{\rm stoch} + n
\]
형태

---

## 5. validation gate before statistics

아래 중 하나라도 미통과면 통계 fitting 금지.

- exact electron-frame Thomson block 미구현
- local boost / global tilt 분리 미완료
- family-specific spatial backend 미완료
- background constraint residual 큼
- perturbation IC provenance 없음
- low-\ell hierarchy cutoff convergence 미측정

---

## 6. observables-side 산출물

필수 파일:

- `maps/T_QU.fits` 또는 동등한 internal format
- `harmonics/alm_TEB.npz`
- `diagnostics/deterministic_vs_stochastic_split.npz`
- `diagnostics/global_tilt_vs_local_boost.npz`
- `reports/OBSERVABLES_README.md`

---

## 7. 한 줄 결론

\[
\boxed{
\text{본체 solver 문서가 수학/물리/알고리즘의 SSOT라면,}
\text{이 문서는 출력/데이터 비교/통계 계층의 SSOT다.}
}
\]
