# HTT X01 tensorized 연구: Legacy × PR254–264 × 실제 Planck·CF4

2026-10-15 KST. 기준 commit 15096b9f37d9a678037b373e4bbbe1e5ea50fefe, 격리 브랜치 research/htt-tensor-source-bindings-20261015. 원본 owner checkout의 57개 미커밋 경로는 변경하지 않는다.

## 1. 원래 방법론 보존과 업그레이드

후속 PR254 typed convex MES anchor, PR255 matrix-valued covariance-whitened anchored response, PR256 local/global velocity frame separation, PR257/258 low-ell morphology and response-class quotient, PR262 original fixed-contraction tensor fibre-support contracts, PR264 tensor departure statistics, and the later TYPEFREE-INFERENCE-PORT (current FunctionalSpec/AnchorBodySpec/gauge/support/finite pushforward)를 실제 Git commit에서 재확인했다.

기본 물리학 상태는 \(\mathcal K=(\sigma_{\langle ab\rangle},\omega_a,A_a,\beta_a,\Delta\Omega_k)\), metric (-,+,+,+), epsilon123=+1. Legacy scalar x_C=Sigma²-W²+Omega_tilt+DeltaOmega_k와 Q=x_C/U_sigma는 역사적인 후속 projection에 한정한다. Principal statistical objects: functional-indexed x_phi, tensor-body gauge Q_A, directional support F_phi, conditional exceedance Pi_phi and joint mask/depth tensor path G_F. 관측된 Planck temperature STF tensors는 physical spacetime shear/omega/A/beta가 아니다.

## 2. STF2/3의 실제 source anchor 유도

원본 실제 Planck PR3 sky 9개 processed 결과는 ONE CMB SKY. FFP10 원본 K1 bank의 999개 고유 CMB signal simulation IDs에서 같은 실제 temperature mask의 real harmonic coefficients를 추출한다. \(\ell=2\) even rank2 STF는 5개 real modes, \(\ell=3\) odd rank3 STF는 7개 real modes. 각 block의 source mean \(\bar a_\ell\), positive definite empirical covariance \(C_\ell\)을 정의하고 unit-RMS ellipsoid를 typed body로 만든다.

\[
 \mathcal A_\ell^{\rm emp}=\{v:(v-\bar a_\ell)^T C_\ell^{-1}(v-\bar a_\ell)\le1\},\quad
 Q_{\mathcal A_\ell}=\sqrt{(a-\bar a_\ell)^TC_\ell^{-1}(a-\bar a_\ell)}.
\]
\[
 h_{\mathcal A_\ell}(\phi)=\sqrt{\phi^TC_\ell\phi},\quad
 F_\phi=\frac{\phi\cdot(a-\bar a_\ell)}{h_{\mathcal A_\ell}(\phi)}.
\]
Existing PR262 FunctionalSpec/FunctionalRecord, AnchorBodySpec, evaluate_paired_anchor, support_utilization, finite_joint_pushforward, strict_exceedance used DIRECTLY, not rewritten as legacy scalar. Pi_\ell(t) is empirical FFP10 proportion of Q_A>t; not cosmological posterior, not Planck null p. The same 999 source IDs under lmax=5 and12 form a paired mask/fit response path; this path is NOT actual redshift G_F. The physical kinematic tensor has no accepted observational transfer and receives typed missing mass=1 and outer exceedance [0,1].

Wolfram checked ellipsoid support/gauge algebra; Python checked typed gauge/direct quadratic identity, passive orthogonal coordinate changes, odd/even parity under n→−n and explicit real-harmonic-to-Cartesian STF reconstruction. Max STF2+STF3 vs six sky Ylm axes error **7.1054273576e−15 µK**.

## 3. 실제 source-conditioned 수치결과

| quantity | STF2 5 modes | STF3 7 modes |
|---|---:|---:|
| Actual one observed SMICA K1 source tensor covariance gauge | 1.090416242 | 1.962761249 |
| One sky lmax12−lmax5 paired tensor-gauge change | +0.419626148 | +0.241940064 |
| Same 999 simulation IDs path gauge change RMS | 0.514483266 | 0.696643659 |
| Empirical simulation fraction Q_A>2 | 555/999 | 767/999 |

Five CMB-source masked STF2/STF3 cross covariance canonical correlations: **0.1242046873, 0.0929193511, 0.0783332713, 0.0719421966, 0.0354229777**. Finite empirical covariance body is NOT a physical MES/Copernican theorem, isotropy null or full Planck foreground/noise/source covariance. The F_phi values may be signed and exceed 1 for a unit empirical covariance body; unlike legacy nonnegative sector filling fraction F they are not bounded fractions.

## 4. 실제 CF4 catalogue angular tensor source coupling, no joint likelihood

Actual 35,970 grouped CF4 ICRS J2000 sightlines and z_CMB are SHA-verified; rotated to Galactic with Astropy to construct the fixed 12-column operator of Planck STF2+STF3 angular template sampled on four disjoint CF4 source-depth shells. The one SMICA K1 low-ell T source projected onto pooled real CF4 sky window has mean **+2.910818076 µK**; shell means (0.01–0.03,0.03–0.05,0.05–0.075,0.075–0.10) are [−0.5159421,+2.8005067,+4.3604807,+4.5392380] µK. This is deterministic temperature angular sampling by a selected galaxy catalogue, NOT an observed Planck/CF4 correlation or cosmological shear. CF4 apparent five-coordinate STF from K02 is not physical 1+3 shear without true optical transfer and method selection.

## 5. X01 source/overlap graph, six paper ownership and external parallel readiness

Canonical SOURCE_BINDINGS.json, source-run results/X01_tensorized_source_bindings_v3/:
- 11 source classes with SHA checked, including actual 489 MiB K1 FFP10 bank bytes; 9 overlap/dependence edges.
- all 6 paper estimands explicitly bind actual source and missing physical transfer; 9 original tracked/untracked design snapshot authorities rechecked.
- PR254/255/256/257/258/262/264 source Git commit IDs verified. Separate PR531/532 source 11 report records and parent-24 SNIa/CF4 35,970 uncertain overlap retained.
- actual Planck 9 methods = ONE cosmological CMB sky; FFP10 CMB999 and first300 noise same source IDs; CF4 groups and selected SN not assumed independent without matching source ID; Planck + CF4 common-congruence joint physical likelihood ABSENT.

The previous seven external-input blockers (S04, L03, H02, V03, B02, K03, K04) receive typed tensor requirement matrix in results/X01_tensorized_source_bindings_v3/EXTERNAL_TENSOR_INPUTS.json: physical joint sigma5/omega3/A3/beta3 and curvature law; full Planck T/E/B end-to-end instrument covariance; true CF4 35970x35970 correlated selection/velocity/method covariance; global beta_RM(z) history; 11 Bianchi families plus exceptional VI_-1/9 all-m T/E/B atlas; proper-motion spin1/curl; common source physical GR optical-luminosity distance operator. All seven scientific blockers remain externally blocked. Candidate code/file existence is not physical qualification.

## 6. DAG result and resume

X01 scoped six-paper source identity/overlap acceptance is satisfied. P1 S03 is now READY and specifically prioritizes tensorized F_phi, Q_A, Pi_phi and correlated mask/depth G_F sensitivity using real 999 same-ID STF2/STF3, not the obsolete single scalar statistics. This run does not mark S03 complete, does not establish physical sigma/omega/A/tilt or a calibrated Planck+CF4 selected posterior. New overall DAG expected 13/42 scoped (30.95%), ready4, external7, waiting18 and manuscripts 0/6.

Canonical files:
- htt/obsstat/tensorized_lowell_source.py
- scripts/run_htt_tensorized_source_x01.py
- scripts/run_htt_tensor_source_bindings_x01.py
- tests/obsstat/test_tensorized_lowell_source.py, tests/obsstat/test_htt_x01_tensorized_source_acceptance.py
- results/X01_tensorized_stf_planck_ffp999_v2/ (scientific JSON, 999 source arrays, empirical morphology PNG)
- results/X01_tensorized_source_bindings_v3/ and SOURCE_BINDINGS.json
- DAG_PROGRESS_20261015_tensor_X01.json

Novelty/standards: Pontzen & Challinor, MNRAS 380 (2007), doi:10.1111/j.1365-2966.2007.12221.x polarized Bianchi physical transfer; Saadeh et al., PRL117 131302 (2016), doi:10.1103/PhysRevLett.117.131302 actual Planck physical Bianchi mode constraints; Rubtsov, arXiv:1612.02347 tensor quadrupolar statistical anisotropy. No physically new beyond-FLRW detection has been claimed. Native subagent unavailable (NOT_RUN). Local Codex NOT_USED.
