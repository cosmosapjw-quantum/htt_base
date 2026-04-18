# BASS Canonical Physics References

> Source: `BASS_Physics_Cosmological_Evolution_Compendium_v1_0.md` §16.

BASS 구현 SSOT 의 물리/수치 참조 기준. 각 PR 이 새 물리를 도입할 때 본 목록에 있는 reference 를 인용하거나, 새 reference 를 본 문서에 추가한 뒤 인용.

---

## §A. CMB baseline / gauge / LoS

> **Note (2026-04-17)**: MB-95 synchronous gauge, CAMB, CLASS, Hu-White references 는 §B.5 로 이동. MB-95 formalism 은 production 이 아닌 verified oracle 로 재분류.

(This section intentionally empty — see §B.5 for MB-95 oracle references, §B for PSTF primary references.)

---

## §B. 1+3 Covariant PSTF — Primary Formalism

> **Role (2026-04-17 update)**: PSTF (Projected Symmetric Trace-Free) 1+3 covariant formalism 은 BASS 의 **production target**. MB-95 synchronous gauge (`sync_gauge_camb.rs`) 는 verified FLRW oracle 로 격하. 자세한 formalism scope 는 `docs/SSOT_POLICY.md §17` 참조.

5. **Challinor, A. & Lasenby, A. (2000)**
   *1+3 Covariant Cosmic Microwave Background Anisotropies I*
   Ann. Phys. **282**, 285.  DOI: [10.1006/aphy.2000.6033](https://doi.org/10.1006/aphy.2000.6033)
   — Photon intensity PSTF hierarchy `I_{A_ℓ}` 의 기본 수식. PR-020 에서 `coupling::free_streaming_{down,up}` 과 `stf_normalization` 의 이론 출처.

6. **Challinor, A. & Lasenby, A. (2000)**
   *1+3 Covariant Cosmic Microwave Background Anisotropies II*
   Ann. Phys. **282**, 321.  DOI: [10.1006/aphy.2000.6034](https://doi.org/10.1006/aphy.2000.6034)
   — Polarization PSTF hierarchy (E, B mode) 와 Thomson collision 의 covariant form. PR-022 에서 electron-frame Thomson collision `ζ̃` 유도 기반.

7. **Maartens, R., Gebbie, T. & Ellis, G.F.R. (1999)**
   *Covariant CMB Anisotropies II: Nonlinear Dynamics*
   Phys. Rev. D **59**, 083506.  DOI: [10.1103/PhysRevD.59.083506](https://doi.org/10.1103/PhysRevD.59.083506)
   — Ellis-Maartens-Stoeger (MES) kinematic bounds. `x_C` departure parameter 의 theoretical ground. PR-080 에서 사용.

8. **Tsagas, C. G., Challinor, A. & Maartens, R. (2008)**
   *Relativistic Cosmology and Large-scale Structure*
   Phys. Rep. **465**, 61.  DOI: [10.1016/j.physrep.2008.03.003](https://doi.org/10.1016/j.physrep.2008.03.003)
   — 1+3 covariant formalism 의 comprehensive review. Z_{ab} (electric Weyl), σ_{ab} (geometric shear), tilt velocity 정의의 표준 reference. PR-020 `layout.rs`, PR-023 `metric.rs`, Phase 4 Bianchi extension 전체의 기반.

9. **Maartens, R. (1998)**
   *Covariant Velocity and Density Perturbations in Quasi-Newtonian Cosmologies*
   Phys. Rev. D **58**, 124006.  DOI: [10.1103/PhysRevD.58.124006](https://doi.org/10.1103/PhysRevD.58.124006)
   — Covariant velocity/density perturbation 의 FLRW 극한. PR-021 adiabatic IC 의 PSTF 유도 시 MB-95 Θ_0, v_b 와의 매핑 reference.

10. **Lewis, A. & Challinor, A. (2006)**
    *Weak Gravitational Lensing of the CMB*
    Phys. Rep. **429**, 1.  DOI: [10.1016/j.physrep.2006.03.002](https://doi.org/10.1016/j.physrep.2006.03.002)
    — CMB lensing covariant formulation. Phase 3 이후 lensing sub-track 기반.

---

## §B.5 MB-95 Synchronous Gauge — Verified Oracle

> **Role**: BASS production target 이 아니라 **verified FLRW oracle**. `sync_gauge_camb.rs` (4316 줄) 의 origin 이며, PSTF primary 의 FLRW 극한 검증 대상 (Phase 2 PR-025 의 equivalence test 참조 구현).

11. **Ma, C.-P. & Bertschinger, E. (1995)**
    *Cosmological Perturbation Theory in the Synchronous and Conformal Newtonian Gauges*
    ApJ **455**, 7.  DOI: [10.1086/176550](https://doi.org/10.1086/176550)
    — Synchronous/Newtonian gauge brightness multipole hierarchy 의 표준 reference. BASS 의 `sync_gauge_camb.rs` origin.

12. **Lewis, A., Challinor, A. & Lasenby, A. (2000)**
    *Efficient Computation of CMB Anisotropies in Closed FRW Models*
    ApJ **538**, 473.  DOI: [10.1086/309179](https://doi.org/10.1086/309179)
    — CAMB 원 논문. `sync_gauge_camb.rs::solve_production_spectrum` 의 알고리즘 구조와 D_ℓ 비교 기준.

13. **Hu, W. & White, M. (1997)**
    *CMB Anisotropies: Total Angular Momentum Method*
    Phys. Rev. D **56**, 596.  DOI: [10.1103/PhysRevD.56.596](https://doi.org/10.1103/PhysRevD.56.596)
    — `Π_BASS = Θ₂ + E₀ + E₂` (HW basis) 의 출처. PSTF 와 MB-95 polarization 매핑 bridge.

14. **Blas, D., Lesgourgues, J. & Tram, T. (2011)**
    *CLASS II: Approximation Schemes*
    JCAP **07** (2011) 034.  DOI: [10.1088/1475-7516/2011/07/034](https://doi.org/10.1088/1475-7516/2011/07/034)
    — TCA/UFA/RSA approximation schemes. PR-022 PSTF RHS 에서 TCA 구현 시 reference (`tca_lm.rs` 의 closure 기준).

---

## §C. Recombination / History

8. **Ali-Haïmoud, Y. & Hirata, C. M. (2010)**
   *Ultrafast Effective Multilevel Atom Method*
   arXiv:1006.1355
   — EMLA 기반. `hyrec_emla.rs` 의 알고리즘 origin.

9. **Ali-Haïmoud, Y. & Hirata, C. M. (2011)**
   *HyRec*
   Phys. Rev. D **83**, 043513.  DOI: [10.1103/PhysRevD.83.043513](https://doi.org/10.1103/PhysRevD.83.043513)
   — HyRec v1 논문.

10. **Lee, N. & Ali-Haïmoud, Y. (2020)**
    *hyrec-2*
    Phys. Rev. D **102**, 083517.  DOI: [10.1103/PhysRevD.102.083517](https://doi.org/10.1103/PhysRevD.102.083517)
    — HyRec-2 (현재 BASS 사용). `hyrec_emla_tables.rs` 의 rate table 출처.

---

## §D. Reionization / 21cm

11. **Furlanetto, S., Zaldarriaga, M. & Hernquist, L. (2004)**
    *The Growth of H II Regions During Reionization*
    ApJ **613**, 1.  DOI: [10.1086/423025](https://doi.org/10.1086/423025)
    — Excursion-set-based HII region growth. Track E (PR-040 reionization) reference.

12. **Mesinger, A., Furlanetto, S. & Cen, R. (2011)**
    *21cmFAST*
    MNRAS **411**, 955.  DOI: [10.1111/j.1365-2966.2010.17731.x](https://doi.org/10.1111/j.1365-2966.2010.17731.x)
    — Semi-numerical EoR simulator. PR-041 UV/X-ray/Lyα sweep 구현 reference.

13. **Murray, S. G., et al. (2020)**
    *21cmFAST v3*
    JOSS **5** (54), 2582.  DOI: [10.21105/joss.02582](https://doi.org/10.21105/joss.02582)
    — 21cmFAST v3 (현대적 포팅). Track E 알고리즘 템플릿.

14. **Molaro, M., et al. (2019)**
    *ARTIST*
    MNRAS **489**, 5594.  DOI: [10.1093/mnras/stz2171](https://doi.org/10.1093/mnras/stz2171)
    — Characteristics-based reionization. BASS 의 FullChar reionization branch (§2.3) reference.

---

## §E. EFT / Backreaction

15. **Buchert, T. (2000)**
    *On Average Properties of Inhomogeneous Fluids in GR*
    Gen. Rel. Grav. **32**, 105.  DOI: [10.1023/A:1001800617177](https://doi.org/10.1023/A:1001800617177)
    — Buchert averaging, `Q_D` kinematical backreaction. Track G (PR-060) Tier-2 reference.

16. **Buchert, T. & Räsänen, S. (2012)**
    *Backreaction in Late-Time Cosmology*
    Ann. Rev. Nucl. Part. Sci. **62**, 57.  DOI: [10.1146/annurev.nucl.012809.104435](https://doi.org/10.1146/annurev.nucl.012809.104435)
    — Late-time backreaction review.

17. **Carrasco, J.J.M., Hertzberg, M.P. & Senatore, L. (2012)**
    *The Effective Field Theory of Cosmological Large Scale Structures*
    JHEP **09** (2012) 082.  DOI: [10.1007/JHEP09(2012)082](https://doi.org/10.1007/JHEP09(2012)082)
    — EFTofLSS 원 논문. Track G (PR-061) counterterm reference.

18. **Carrasco, J.J.M., Foreman, S., Green, D. & Senatore, L. (2014)**
    *The Effective Field Theory of Large Scale Structures at Two Loops*
    JCAP **07** (2014) 057.  DOI: [10.1088/1475-7516/2014/07/057](https://doi.org/10.1088/1475-7516/2014/07/057)
    — 2-loop EFTofLSS.

---

## §F. Numerical methods

19. **Kennedy, C. A. & Carpenter, M. H. (2001)**
    *Additive Runge–Kutta Schemes for Convection–Diffusion–Reaction Equations*
    NASA/TM-2001-211038.
    — IMEX additive RK 원 논문. BASS Phase F (PR-050 hybrid solver) 의 ARK4(3)6L[2]SA 근간.

20. **Kennedy, C. A. & Carpenter, M. H. (2016)**
    *DIRK Methods for ODEs: A Review*
    NASA/TM-2016-219173.
    — Diagonally-implicit RK review.

---

## Cross-reference table: BASS code → paper

| BASS file / 모듈 | Primary reference |
|---|---|
| `sync_gauge_camb.rs` | Ma & Bertschinger 1995 (#1), Lewis-Challinor-Lasenby 2000 (#3) |
| `core::ssot::pi_bass` | Hu & White 1997 (#2) |
| `recombination::hyrec_emla` | Ali-Haïmoud & Hirata 2011 (#9), Lee & Ali-Haïmoud 2020 (#10) |
| `recombination::camb_xe_table` | Lewis-Challinor-Lasenby 2000 (#3) RECFAST 버전 |
| `core::ssot::TimeConvention` | — (BASS 자체 규약) |
| `bianchi::*` (future) | Challinor & Lasenby 2000 I+II (#5, #6) |
| `transport::characteristics` (future) | Challinor & Lasenby 2000 I+II (#5, #6) |
| `backreaction::*` (future) | Buchert 2000 (#15), Carrasco et al. 2012 (#17) |
| `reionization::*` (future) | Mesinger et al. 2011 (#12), Molaro et al. 2019 (#14) |
| IMEX solver (PR-050 future) | Kennedy & Carpenter 2001, 2016 (#19, #20) |

---

## 참조 추가 절차

새 reference 가 필요한 PR 은:

1. 본 문서의 적절한 §A-§F 섹션에 추가
2. Cross-reference table 에 BASS 파일 매핑 추가
3. DOI 명시 + 1-2 문장 사용 맥락 설명

**Rule**: 본 문서에 없는 paper 인용은 PR comment 로 추가 — merge 전에 본 문서에 승격 필수.

---

*Source: BASS Physics Compendium v1.0 §16. 마지막 갱신: 2026-04-17.*
