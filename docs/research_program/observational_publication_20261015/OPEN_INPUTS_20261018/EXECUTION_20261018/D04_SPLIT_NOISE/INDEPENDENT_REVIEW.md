# D04 independent decision — 2026-10-18

Fresh bounded read-only task `/root/open_d02_review`, requested Astra/xhigh,
observed UNKNOWN, reviewed at3677216f. Scoped PASS; no concrete repair needed.
Original L03 remains HOLD; no joint signal/foreground/selection coverage,
stochastic independence, physical covariance or calibrated null inferred.

Independently verified all input/mask/FULLcache/weights/operator/chart/kernel
hashes. Four actual603987840-byte FITS have RING/NSIDE2048, three1024E I/Q/U
columns and K_CMB. COORDSYS absence is correctly distinguished from adopted
release convention. CachedT26846/P30021 supports match reused FULL support.

Independent SVD fits rank36/64, coefficient max discrepancy4.45e-21K,
normal-equation residual2.39e-18. Four contrasts and T/E/B norms reproduce.
27field and27cross-field morphology records, harmonic/STF synthesis and
reflection parity checked; maximum descriptor/projector discrepancy2.35e-14.
Actual axes/chiralities are away from declared degeneracy thresholds.
Weights finite/shapes/hashes and documented beam/LFI conventions verified;
no extra beam or upstream execution. Figure/report inspected for scope.

Independent tests: new6PASS; reused streaming selection4PASS,16deselected.
No four native stream/eight-pair campaign rerun. A reviewer-only summary
serialization error with numpy.int64 was corrected, with compact reanalysis
successful. This is not a candidate defect.

Frozen final SHA256:

```
split_stream.py 4b4f1823e8dab6490715218c23faead82222869df13a5275794a833dce998c9f
RESULT.json 54f2df36c6e06efa35a4d164ae9cf6b0b46ae86e2389bf61f6b48a72639c1b27
COEFFICIENTS.npz 624536d49828da366217fa513fb0f511f4bf5ae4002a519df66ec358bea9816b
REPORT_KO.md 3166e69607886ddaf728f5476672f8557756e3e0d62cad02657b14ff692d921f
```

The missing2018 HM FFP10 CMB limitation is supported by
https://doi.org/10.1051/0004-6361/201833886 . Review did not include D07, whose
contract this reviewer framed; a different independent reviewer assesses D07.
