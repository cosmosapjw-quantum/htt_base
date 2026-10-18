# PR3 실제 Q/U의 finite low-ell E/B 관측계수: 소스 보존 연구

같은 NSIDE64 편광 신뢰 mask와 동일한 64차원 spin-2 joint LS를 사용함.
발표한 full-mission CMB EE/BB likelihood나 parity-violation 결과가 아님.

| ell | SMICA_FULL E-auto | SMICA_FULL B-auto | SMICA_FULL EB-cross |
|---:|---:|---:|---:|
| 2 | 0.0881122 | 0.0956766 | -0.0441829 |
| 3 | 0.0268992 | 0.00828159 | -0.00115445 |
| 4 | 0.0160986 | 0.00168142 | -0.00255943 |
| 5 | 0.00935879 | 0.00931903 | -0.0033102 |

| split | E half-diff total power sum | B half-diff total power sum |
|---|---:|---:|
| SMICA_HM | 0.0187097 | 0.00716722 |
| SMICA_OE | 0.0080239 | 0.00796144 |
| NILC_HM | 0.0172549 | 0.0105464 |

EB is odd under parity only in a fully specified physical spin basis; a finite cut-sky and unmodeled high-ell leak destroys naive parity-null interpretation.
Foreground/component-separation differences must be carried as common-source responses rather than independent cosmic signals.
