# HTT 여섯 논문 출판 DAG, P2/L01: 1단계 관측-응답 이론

**정본:** `research/htt-sixpaper-p3-h03-tomography-20261016` PR #541 HEAD `2a5d47b2f6af69e049ce41c068b77d99a1592d7f`, `PUBLICATION_DAG.json`의 `P2/L01`. 6편·42노드 계획만 적용한다. 기존 245-card PR backlog 변경 금지.

## 소스에서 직접 확인된 자료

- 2026-10-15 Loop5: 동일 물리 Planck sky의 temperature 9종, polarization(Q/U) 8종. `SMICA_noSZ_FULL`은 polarized product가 **없음**, 0으로 채워서는 안 된다.
- 원래 NSIDE2048 NESTED Galactic PR3 `I/Q/U`와 공통 온도/편광 Int/Pol mask를 각각 결합하고 NSIDE64 RING으로 집계한 관측 저계수의 원본 파일 해시를 인증했다. 실제 mask 픽셀: 온도 26,846 / 편광 30,021 (총 49,152), **같은 픽셀 배열이 아님**.
- 온도 \(\ell=0\ldots5\) 36변수 동시 OLS, \(\ell=2\ldots5\) 32변수 유지. 실제 온도 \(K_{6:16}\in\mathbb R^{32\times253}\) 및 \(K_{17:32}\in\mathbb R^{32\times800}\) 소스 고정. 결합 연산자 노름 2.4328695605629207. **그 이상 \(\ell>32\)**, 실제 고차 진폭, 유효 beam/foreground/E2E 미확인.
- 편광 \(Q/U\)를 **joint spin-2** \(S_{2:5}\in\mathbb R^{2N_P\times64}\)에 투영한 \(\ell=2\ldots5\) 64개 E/B 유한 응답좌표가 소스에 있음. 원본 설계 조건수 3.130962277; identity residual \(2.44\times10^{-15}\). 편광 \(\ell>5\) 고차 \(K^P\) 매트릭스의 **실제 mask-row 및 높은 \(\ell\) 행렬은 소스에 없음**. 피팅 계수만으로 해당 누출이나 E/B 분리를 관측적으로 보정할 수 없다.

## 엄밀한 수학적 계약

복소 spin 신호 \(P_\pm=Q\pm iU\)에 \({}_{\pm2}Y_{\ell m}\)를 적용하고, E/B 실수 계수의 고정 m0, cos, sin 순서로 복원한다. 저차 스핀 기저 \(S_L\), 생략한 고차 기저 \(S_H\), 편광 선택 \(W_P\)가 **같은 프레임·같은 픽셀**일 때:

\[
A_P=(S_L^T W_P S_L)^{-1}S_L^T W_P,\quad A_PS_L=I_{64},\qquad K^P_{LH}=A_P S_H.
\]

원래 데이터에는 \(A_PS_L\approx I\) 및 선택 픽셀 수/조건수가 알려졌지만 \(K^P_{LH}\)의 모든 행렬을 재구성할 입력은 없다. 같은 mask *픽셀 수*가 같더라도 위치를 바꾸면 \(K^P_{LH}\)는 달라진다. 이는 잘못된 물리적 확신을 차단하는 구체적 구성 예제이지 전역 no-go 정리가 아니다.

패리티에서 \(E_{\ell m}\mapsto(-1)^\ell E_{\ell m}\), \(B_{\ell m}\mapsto(-1)^{\ell+1} B_{\ell m}\). 정확히 일치하는 full-sky parity transformation 아래 \(E B\mapsto -E B\). cut sky 및 누락된 고차 modes를 무시한 fitted \(\widehat E\widehat B\)는 곧바로 우주론적 패리티 위반을 뜻하지 않는다.

동일 sky의 \(n\)개 처리본에는 독립 물리 하늘이 하나뿐이다. 평균 제거한 8×64 EB 행렬의 rank는 최대 7이지만, 이것은 **processing contrast**의 차원이지 통계적 CMB sample covariance rank가 아니다. FFP10의 6조건 × 300 pairing에서 독립 잠재 하늘은 300개이지 1,800개가 아니다.

## 이전 코드·문헌에 대한 의미

고정 소스 작성 코드 `scripts/run_htt_planck_multisplit_spin_20261015.py`는 `spin2_design_real`을 `healpy.alm2map_spin`으로 구축했고 common polarization Int/Pol mask로 실제 8개 처리본을 적합했다. 이번 독립적인 SciPy-only Wigner-d 구현은 합성 Stokes Q/U 스핀 frame, parity, finite source-mask 누출을 **검산**하지만 `healpy.alm2map_spin` 원소별 부호·orientation parity가 일치하는지 **독립적으로 실제 해시 고정 Planck 마스크에서 검증한 것은 아니다**.

Planck 2018 IV (doi:10.1051/0004-6361/201833881)는 알고리즘별 component separation과 noise/E2E 불일치를 설명한다. Planck 2018 VII (doi:10.1051/0004-6361/201935201)는 대각 스칼라 Q/U 피팅으로 E/B를 추출하지 않고 purified inpainting 및 mask leakage를 다룬다. 이번 단계는 published Planck PTE likelihood나 새로운 anomaly 유의도를 다시 만들지 않는다.

**S1 수학·소스 계약은 샌드박스 11개 테스트를 통과**, 과학적 claim은 `SOURCE_CONDITIONAL_T_EB_FINITE_IMAGE_AND_MASK_GEOMETRY_ONLY`. `P2/L01` 제출/관측 response 완성 판정은 S2 및 잔여 실제 편광 mask/beam 계약을 본 뒤 결정한다. native subagent 및 독립 reviewer는 NOT_RUN.
