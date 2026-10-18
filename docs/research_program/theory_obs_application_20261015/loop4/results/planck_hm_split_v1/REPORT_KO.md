# Planck PR3 실제 SMICA HM1/HM2 half-mission 관측분할

공식 원본 및 HM missing-pixel mask 3종의 크기·SHA-256 확인. 공동 안전 mask의 NSIDE64 픽셀수 32864.

이는 단일 하늘의 두 관측 분할 결과이지 mock ensemble이 아니며, half-difference는 공통 systematic을 검출하지 못할 수 있다.

| ell | cross HM1xHM2 microK2 | halfdiff auto microK2 | halfsum auto microK2 | full source microK2 |
|---|---:|---:|---:|---:|
| 2 | 258.641 | 0.010029 | 258.651 | 258.689 |
| 3 | 409.263 | 0.00713934 | 409.27 | 409.07 |
| 4 | 265.528 | 0.00216549 | 265.53 | 265.433 |
| 5 | 295.603 | 0.00538274 | 295.609 | 295.418 |

Released split CMBs are not actual time-stream independent noise measurements; HM missing mask is combined with the source common mask, not silently set to zero.
No E2E native split covariance, no Planck scientific null or p-values. The full/half-average difference can include nontrivial compsep weights and transfer, not just random noise.
A physical CMB boost/Bianchi response must pass both split-specific transfer and correlate their latent common foreground/systematic terms.
