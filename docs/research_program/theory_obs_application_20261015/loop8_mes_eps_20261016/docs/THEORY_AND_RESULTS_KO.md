# C8-OBS-MES-EPS: 실제 Planck/FPP10 처리 오차와 almost-EGS 입력의 분리

**연구 단위:** HTT / OBSSTAT, 2026-10-16 KST.  **증거 등급:** source-bound / numerical-checked / conditional diagnostic.

**반드시 유지할 판단:** 현재 산출물은 어떤 Bianchi 계열이나 shear, vorticity, global tilt, EGS coefficient의 물리적 관측 posterior도 아니다. 기존 PR124의 geodesic 등록 정리를 대체하지 않으며, 다른 congruence에 식을 수송하지 않는다. 이전의 `HOLD/UNKNOWN` 및 PR #534의 draft 상태를 유지한다.

## 1. 관측량과 EGS 사이의 정의상 차이

온도계수가 orthonormal real spherical harmonic 좌표로 저장됐을 때만

\[
\widehat C_\ell^{(s)}=\frac{1}{2\ell+1}\sum_{m=-\ell}^{\ell}|\widehat a^{(s)}_{\ell m}|^2,\qquad
\widehat\epsilon^{(s)}_\ell=\frac{\sqrt{\widehat C^{(s)}_\ell}}{T_0},\quad T_0=2.72548\,\mathrm K
\]

는 정의 가능한 단일 sky realization의 **처리조건부 power-amplitude proxy**다. 위 계수는 동일 시간/관측자의 **masked simultaneous OLS**에서 생성됐다. 거의-EGS/MES의 covariant radiation multipoles와 그 시·공간 미분에 대한 일양 bound를 이 숫자로 곧장 대체할 근거는 없다. 특히 observed solar dipole을 `eps1`에 그대로 대입할 수 없으며 C1/C2의 Copernican-derivative 축약도 별도 가정이다.

Mask, beam, omitted high multipoles와 계수오차가 섞이는 일반적 유한 선형화는

\[
\widehat{\boldsymbol a}_L=A_L\boldsymbol a_L+K_{LH}\boldsymbol a_H+\boldsymbol\eta.
\]

여기서 `A_L=I`와 고차항 제한을 동시에 입증하지 않고 \(\widehat{\boldsymbol a}_L\)를 물리적 저모드로 식별하면 안 된다. **동일한 유한 쉘에 한해** \(\|K_{LH}\|_2\)를 알고 \(\|a_H\|_2\le E_H\)인 경우, 직교 projection의 non-expansiveness와 Euclidean norm 역삼각부등식으로

\[
\left|\Delta\epsilon_\ell\right|\le
\frac{\|P_\ell(A_L-I)a_L\|_2+\|K_{LH}\|_2 E_H+\|P_\ell\eta\|_2}{\sqrt{2\ell+1}T_0}.
\]

이는 증명 가능한 *conditional finite-shell inequality*다. 원래 FITS 처리까지의 높은 모드·foreground·beam·시간·공간·derivative envelope \(E_H\) 등은 이번 자료에서 주어지지 않았으므로 오른쪽을 실물리 상한 숫자로 바꾸지 않는다. \(\boldsymbol a_H=0\), \(\boldsymbol\eta=0\)로 채우지 않는다.

## 2. 서로 합치면 안 되는 두 실제 처리 실험

**Loop5 제품 실험:** 실제 Planck 9개 SMICA/NILC/HM/OE/noSZ 처리 이미지는 \(N_{\rm pix,T}=26,846\) 공동 mask에서 \(\ell=0..5\) 동시 OLS, \(\ell=2..5\) 저장. 이는 9개의 **서로 다른 우주 표본이 아니라 동일 하늘**이다. 복원한 9개 \(C_2,C_3\)은 기존 Loop6 source 결과와 numerical identity로 일치한다.

| Quantity | Nine-processing minimum | Maximum | Same-sky spread |
|---|---:|---:|---:|
| \(\widehat\epsilon_2\) | 6.081084e-6 | 6.214624e-6 | 1.335399e-7 |
| \(\widehat\epsilon_3\) | 6.992423e-6 | 7.054805e-6 | 6.238134e-8 |

**FFP10/K1 처리 실험:** 별도 threshold(0.5/0.8)와 finite fitting upper order \(\ell_{\max}=5,8,12\) 여섯 경우. 이 계열은 Loop5보다 다른 마스크, processing operator와 source pipeline에 놓여 있으므로 **Loop5 수치와 차분해 하나의 noise sigma를 구성하는 것은 금지**한다. `ffp_response`의 6×300×32 표본은 각 simulation latent sky의 여섯 처리 결과로 *paired*돼 있다. 첫 번째 처리 행은 원본 FFP pilot의 observed·300 paired coefficient와 정확히 일치한다.

| Mask threshold | fit \(\ell_{\max}\) | \(\widehat\epsilon_2\) | \(\widehat\epsilon_3\) | \(\|K_{6:16}\|_2\) |
|---:|---:|---:|---:|---:|
| 0.5 | 5 | 5.521335e-6 | 7.358289e-6 | 1.754275 |
| 0.5 | 8 | 7.401067e-6 | 1.029049e-5 | 3.346862 |
| 0.5 | 12 | 8.376884e-6 | 8.895453e-6 | 7.629347 |
| 0.8 | 5 | 5.490219e-6 | 7.262342e-6 | 1.803284 |
| 0.8 | 8 | 7.425713e-6 | 1.034961e-5 | 3.502861 |
| 0.8 | 12 | 8.513276e-6 | 8.960819e-6 | 8.112107 |

선택된 FFP 관측 하늘의 전체 처리 spread는 \(3.023057\times10^{-6}\) (quadrupole), \(3.087263\times10^{-6}\) (octupole). 60개의 training pair는 새 비교에서 빼고 **240 held-out paired sky**만 사용한다. 이들 중 각각 72, 44개가 observed span 이상이며, rank diagnostic \(73/241=0.302905\), \(45/241=0.186722\)이다. 이 통계량은 사후에 선택했으며 실제 sky와 FFP simulated skies의 exchangeability가 물리적으로 검증되지 않았다. **새로 발견된 CMB 이상/배제 또는 confirmatory p-value가 아니다.**

원본 FFP finite-shell operator \(K_{6:16}\)의 spectral norm으로 구한 **1 μK의 *가정된* omitted-shell amplitude에 대한** quadrupole proxy 이동 upper coefficient는 조건별 \(2.879\times10^{-7}\)에서 \(1.331\times10^{-6}\)이다. 실제 omitted-shell amplitude나 upstream processing bias가 이 자료로 제한됐다는 뜻이 아니다. \(\ell_{\max}=12\)를 사용해도 13–16 및 그 이상의 모드 coupling 문제가 사라지지 않는다.

배포 SMICA full `INT_BEAM`의 \(b_2=1.000275612\), \(b_3=1.000295639\)는 raw full-sky table의 해당 column 값일 뿐이다. \(b_0=b_1=0\)이므로 여기서 cosmological residual dipole을 역복원할 수 없다. 해당 table을 복잡한 mask/foreground effective transfer의 역행렬로 사용하지 않는다.

## 3. PR124의 geodesic branch, 직접 유도 및 코딩 검산

**정확한 branch:** geodesic congruence, signature \((-,+,+,+)\), registered PR124 coefficients

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,\quad
B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2.
\]

MES one-way branch의 형식적 normalized-sector ceilings는 \(\frac32 B_\sigma^2\), \(\frac32 B_\omega^2\). `B_sigma>B_omega>0`의 필요·충분한 조건(\(\epsilon_2>0,\epsilon_3\ge0,\epsilon_1\ge0\))은

\[
\boxed{0\le\epsilon_1<\frac{43}{25}\epsilon_2+\frac9{35}\epsilon_3}.
\]

실제 Loop5의 *power proxies*를 적용한 임계 \(\epsilon_1\) 구간은 \(1.22656\times10^{-5}\) ~ \(1.24904\times10^{-5}\). 이는 **데이터에서 e1을 추정한 것이 아니라 등록 계수의 algebraic-domain result**다. 이전 Loop7에서 가정했던 \(\epsilon_1=0\) branch의 9개 formal \(\Sigma_2\) ceiling은 \(6.77564\times10^{-10}\)~\(7.02819\times10^{-10}\); 저장된 PR124 결과에 전부 일치한다.

지금 사용 가능한 자료에는 observer residual cosmological \(\epsilon_1\), C1/C2의 time/spatial covariant derivatives, native/source-frame 1+3 response와 full high-\(\ell\)/beam/foreground uncertainty envelope가 없다. 가속도와 anisotropic-curvature에 대한 geodesic MES anchor도 없다. CF4 apparent STF2를 geometry shear numerator로 사용할 수 없다는 typed mismatch는 변경하지 않는다.

## 4. 결론, 검증·유효범위

| 대상 | 이번 판정 |
|---|---|
| Source 9개 C2/C3 재현 | `NUMERICALLY_CHECKED` |
| Loop7 PR124 geodesic e1=0 anchor parity | `NUMERICALLY_CHECKED` |
| FFP lane0/pilot observed + 300 paired byte-level array parity | `NUMERICALLY_CHECKED` |
| Same-sky 240-pair processing spread | `NUMERICALLY_CHECKED_CONDITIONAL_POSTHOC` |
| Finite-shell response operator coefficient | `DERIVED_FROM_PRECOMPUTED_OPERATOR_NORM` |
| Source physical EGS epsilon & C1/C2 derivatives | `UNRESOLVED` |
| Cosmological shear/vorticity/tilt posterior, physical Pi, Bayes evidence | `HOLD_UNCHANGED` |
| Real local workstation replay | `NOT_RUN_REMOTE_QUOTA` |
| Native fresh independent reviewer | `NOT_RUN_NO_NATIVE_DELEGATION` |

테스트는 source SHA-256 오염 검사, per-ell harmonic normalization, 9× source cross-check, 6×300 matched pair parity, exact threshold algebra, malformed inputs, fail-closed domain 및 physical-scope 유지 등을 검사한다. 실제 실행 증거는 `logs/pytest.log` 및 `logs/run.log`, 출력 원본은 `results/C8_OBS_MES_EPS_RESULT.json`이다. 새로운 raw Planck FITS의 다운로드나 고비용 실행은 수행하지 않았다.

**원전:** Maartens, Ellis & Stoeger, *Limits on the anisotropy of the Universe from the cosmic microwave background* (https://arxiv.org/abs/astro-ph/9501016), Stoeger, Araujo & Gebbie (https://arxiv.org/abs/astro-ph/9904346), Planck Collaboration IV (https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html). PR124 authoritative source: `htt/src/common/mes_theorem_authority.py` under source commit `13d8d85fa470d645d008986e8f77d8d0f70fdf54`, Git blob `96f0f8aa8e81343855da1a7da749edef9a406a91`.
