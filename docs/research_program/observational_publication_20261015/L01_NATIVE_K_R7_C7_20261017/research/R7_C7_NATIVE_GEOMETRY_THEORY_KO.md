# HTT P2/L01: 실제 PR3 POL 마스크의 유한 spin-2 누출 연산자, 복소구조 및 식별 집합

2026-10-17 KST. 범위: **R7 판별 경량 검산 + C7 기하학적 연산자 검증**. 상위 권위: HTT publication DAG 42노드, Git blob `ac4a94c3da13f142eaab3b06b5275b58096c95e1`; 선행 Draft PR #555 `d80309c542af3d0ce99aa402bb44571e63a74d92`. 본 증거는 L01 부분 진척이며 L01 완료, L03 물리적 null, P2 논문 검출/투고 승인과 구별한다.

## 1. 실제 사용자가 실행한 결과와 그 근거 수준

**User-reported native run / SOURCE-CONDITIONED:** 실측 PR3 POL PMASK (`common`, `HM`, `OE`), `NESTED2048 -> RING64` healpy 변환, 각 마스크를 downgrade한 뒤 strict `>0.5` threshold, 이후 3자 교집합. Spin2 `ell2..5`(실수 64계수) 대비 `ell6..8`(실수 90계수). 원본 PMASK native SHA-256: common `c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4`, HM `33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296`, OE `1b2b4138f791b739938485fa0ebcac5f462e04fbc55626e93d71abd04aac3900`. V2 source manifest SHA-256 `3818b3c399c7c12320bf861697576d289788fe6d74dde3d6d220e276e4fb897e`; reference authenticity is **user-reported**, not publisher-signed.

| Source geometry | pixels/49152 | op norm | low condition | reported low identity residual | NPZ SHA256 |
|---|---:|---:|---:|---:|---|
| common | 38329 | 1.2813681702334279 | 2.105004597333465 | 1.3322676295501878e-15 | a45acd13c079bd871b6704dc6d4952ee6294db0f3f50403978abbd7606f06969 |
| common∩HM∩OE | 37054 | 1.2993976990506202 | 2.1622123352500675 | 2.1062145984149835e-15 | 3df2b8f2624ea7c831f72979788f08c176e3eaff661865d7759a9434c5ae9a59 |

Native `healpy.alm2map_spin` independent `ell2/3 m=0` source convention check maximum |difference| = 3.0531133177191805e-16. Pixel-center `healpy.pix2ang` crosscheck 3.1086244689504383e-15. Both numbers are quoted from user local output, not repeated in this sandbox. The output NPZ matrices were not uploaded or mounted here. **All-m real injection** is prepared but NOT_RUN with healpy here.

## 2. R7 derived theorem: same-weight Q/U geometry has a complex-linear response

Let the selected HEALPix pixels carry the screen-frame Stokes vector \(p=(Q_1,\dots,Q_N,U_1,\dots,U_N)^T\), with the same pixel mask weights \(w_i\) in Q and U. Fix E/B spin-harmonic real basis per multipole as original project implementation: \(a_{+2}=-(a_E+i a_B)\), \(a_{-2}=-(a_E-i a_B)\). Write

\[
  \widehat a_L = (L^T W L)^{-1}L^T W p,\quad
  p = L a_L + H h,
  \quad K=(L^T W L)^{-1}L^T W H.
\]

Here \(L\) contains \(\ell=2,\ldots,5\) and \(H\) contains \(\ell=6,\ldots,8\). All harmonic coefficients are in one compatible real-valued basis (e.g. thermodynamic \(\mu\mathrm K_{\mathrm CMB}\)), W and K dimensionless, and \(L^TWL\) must be nonsingular. These fields are **manufactured harmonic basis functions on actual mask geometry**, not observed Q/U maps.

Define \(J_s(Q,U)=(U,-Q)\) and coefficient-space \(J_L(e,b)=(-b,e)\), \(J_H(e,b)=(-b,e)\), each E/B block arranged per \(\ell\). Then \(LJ_L=J_sL\), \(HJ_H=J_sH\), \(J_s^TWJ_s=W\), and the weighted least-squares minimizer is unique. Applying \(J_s\) to the target therefore maps the minimizer to \(J_L\) of the original minimizer, proving

\[
 \boxed{K J_H = J_L K}.
\]

Grouping all E coefficients and then all B coefficients by **known per-ell indices** makes K a realification of one complex matrix:

\[
 K = \begin{pmatrix} A & B\\-B&A\end{pmatrix},\qquad
 \mathcal K=A-iB\in\mathbb C^{32\times45}.
\]

Hence \(K_{EE}=K_{BB}=A\), \(K_{BE}=-K_{EB}=-B\) as coefficient arrays in the given basis; \(\|K_{BE}\|_2=\|K_{EB}\|_2\), \(\|K_{EE}\|_2=\|K_{BB}\|_2\). Nonzero singular values of K appear twice, with rank even. **This is a testable numerical oracle** for the native K. Mask anisotropy per se does not break it, but distinct Q/U weights, a different sky frame not transported consistently, instrument mixing, or an incorrect coefficient index order can. Wolfram evaluated an exact rational 4x4 instance and obtained `KJ==JK=True`, singular-value squares `{10,10,20,20}`. Tests of source-compatible manufactured cut-sky spin2 designs pass in Python; source-native K check awaits NPZ access.

### Coefficient-space sharp identified bounds

For any bound \(\|h\|_2\le R\), **assumed externally and never inferred here**,

\[
 \sup_{\|h\|\le R}\|Kh\|_2 = R\sigma_{\max}(K),\qquad
 \sup_{\|h_E\|\le R_E}\|K_{BE}h_E\|_2=R_E\sigma_{\max}(K_{BE}).
\]

Both are sharp: choose an appropriate right singular vector. For a given low B coefficient vector \(b\), the minimum high E-only source norm is

\[
 \min_{K_{BE}h_E=b}\|h_E\|_2=\|K_{BE}^+b\|_2
\]

if \(b\in\mathrm{im}(K_{BE})\), otherwise no solution exists. If the real native \(K_{BE}\in\mathbb R^{32\times45}\) has full row rank 32, **every** low-B vector admits a high-E-only finite source in \(\ell=6\ldots8\), with best/worst necessary source norms for unit \(b\) given by \(1/\sigma_{\max}(K_{BE})\), \(1/\sigma_{\min}(K_{BE})\). That is conditional finite-window identifiability, not a statement that the actual high-E sky contains that source or that cosmological B vanishes. The code reports actual rank and these sharp extrema after NPZ readback.

### Real geometry mask difference

Both reported real native norms imply, by the reverse triangle inequality,

\[
 \|K_{\rm 3way}-K_{\rm common}\|_2 \ge
 1.2993976990506202-1.2813681702334279
 =0.01802952881719233.
\]

This is **derived from user-reported scalar norms**; the actual left-hand spectral distance, \(\|\Delta K_{BE}\|_2\), rank and doublet residuals require both NPZ matrices. No comparison of physical B signals or calibrated significance follows without actual sky coefficients and a matched simulation law.

## 3. C7 scoped coding validation and next executable input

New `src/l01_k_spectral_certificate.py` does not regenerate observations or synthesize a pretend Planck sky. It first requires the exact v2/source/mask/output NPZ SHA-256 and checks each saved 64x90 array against its own logged byte digest. It then independently computes full real and reduced complex SVD, block identities, rank/nullity, sharp norm bounds and actual \(\Delta K\). The identity is a **numerical and geometry convention guard**, not a physical acceptance gate. Optional `--all-m-spin-check` compares independent healpy spin2 synthesis against the local Wigner basis for all m via random mixed E/B real coefficients, across \(\ell=2,\ldots,8\). Optional `--native-replay` rereads the original FITS (v2 source-qualified), compares effective-mask SHA and numeric K outputs without requiring compressed NPZ ZIP byte determinism. Both optional paths are not executed in this sandbox.

Native completion command from extracted package:

```bash
python src/l01_k_spectral_certificate.py \
  --receipt /mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json \
  --out /mnt/extdrive/workdir/htt_open_data/provenance/L01_NATIVE_SPECTRAL_CERT_20261017.json \
  --all-m-spin-check
```

For independent source replay, append `--native-replay --root /mnt/extdrive/workdir/htt_open_data --compare-root /mnt/extdrive/workdir/htt_planck_irsa_reference`. This costlier read is optional and may be run after first certificate. Tests use synthetic exact-complex matrices and source-compatible cut-sky spin2 designs; a passing synthetic suite is not a passing real Planck run.

## 4. Literature and scientific admission

Primary comparators:
- Planck Collaboration (2020), *Planck 2018 results. VII. Isotropy and statistics of the CMB*, A&A 641 A7, DOI 10.1051/0004-6361/201935201, https://arxiv.org/abs/1906.02552. Distinct target: empirical low-ell Q/U and E, selected anomalies, FFP10 / end-to-end null simulations.
- Smith & Zaldarriaga (2007), *A general solution to the E-B mixing problem*, https://arxiv.org/abs/astro-ph/0610059. Pure pseudo-Cl separation and optimized noise-sensitive B-mode estimators, **not** identical to our finite pixel-regression response K.
- Alonso et al. (2019), *A unified pseudo-Cl framework*, MNRAS 484, 4127, DOI 10.1093/mnras/stz093, https://arxiv.org/abs/1809.09603. NaMaster E/B purification requires appropriate mask derivatives/apodization; the present binary-mask QR projection does not implement purification or unbiased Cl estimation.

The exact finite E/B complex-linear equivalence is an algebraic diagnostic for the present prescribed projection, **not a novelty claim**; masked polarization leakage and mitigation have substantial prior literature. Physical L01 gate remains open pending \(\ell>8\) remainder control and sky Q/U + beam/foreground/FFP10 matched response/selection, including original null simulation IDs and true independence units. Existing retrospective anomalies cannot be relabeled pre-registered.

**6-paper DAG (unchanged):** P1 1/6; P2 0/6; P3 2/6; P4 1/6; P5 1/5; P6 2/6; COMMON 7/7, total **14/42 completed_scoped, 28 pending**. READY `L01,S02`, 7 external physical blockers as in authoritative DAG. All six `NOT_READY_TO_SUBMIT`. Source/implementation/physics/release states separately recorded; no main merge or unrelated backlog updates.
