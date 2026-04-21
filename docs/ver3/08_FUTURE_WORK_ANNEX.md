# 08. Future Work Annex
## what is intentionally beyond current design-completeness scope

---

## 0. purpose

이 annex는 current design completeness와 genuine future work를 분리한다.
목적은 scope를 축소하는 것이 아니라,
지금 꼭 닫혀야 하는 것과 나중 단계 항목을 혼동하지 않게 하는 것이다.

---

## 1. genuine future work

1. patchy reionization
2. anisotropic recombination microphysics beyond isotropic-history adapter
3. unavailable analytic family backends beyond generic fallback
4. full high-\(\ell\) hierarchy and production outputs beyond low-\(\ell\)
5. full covariance-aware likelihood implementation details
6. nonlinear Compton / spectral distortion physics
7. aggressive performance optimization and hardware-specific kernels

---

## 2. not future work — must already be present now

1. 1+3 PSTF + tetrad engine split
2. all 11 family design-contract coverage
3. orthogonal/global tilt/local boost separation
4. exact electron-frame Thomson contract
5. family-specific backend contract and IC provenance rule
6. tier-A vs tier-B role split
7. residual normalization and hard gate philosophy
8. observables/statistics appendix separation
9. WBS / deliverable map / anti-mock discipline

---

## 3. H1 interpretation boundary

If an item lives in this annex, its absence does not by itself lower the package below “strong design package”.
But if an item in section 2 is missing, H1-like handoff quality is not achieved.

---

## 4. one-line summary

future work는 설계 completeness의 적이 아니라,
**current-scope 필수항목과 genuinely later-stage 항목을 분리해 과장과 공백을 동시에 막는 장치** 다.
