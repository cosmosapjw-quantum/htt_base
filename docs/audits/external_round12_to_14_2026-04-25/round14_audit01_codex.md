# V5-RUNTIME Round-14 External Audit Verdict

**Auditor**: Codex GPT-5  
**Date**: 2026-04-25  
**Bundle SHA**: 0536f0e

## Verdict (one-line)
**HYBRID-RECOMMENDED**

## Summary
F1/F2/F3는 모두 실질적으로 검증됩니다. 특히 CAMB `delta_p_l_k`를 `4π∫dlnk P_R Δ_l^2`로 재조립하면 CAMB raw `C_l`와 약 0.1% 이내로 일치하므로, direct CAMB 비교 자체가 잘못된 convention일 가능성은 낮습니다. 현재 BASS FLRW PSTF transfer는 per-`(k,l)` transfer로 수렴하거나 정규화될 수 있는 상태가 아니며, production FLRW limit은 CAMB transfer로 고정하고 Bianchi/PSTF perturbation만 BASS가 담당하는 hybrid가 가장 안전합니다.

## F1 / F2 / F3 검증
**F1: 4√2는 가짜 신호로 판단합니다.**  
진짜 global normalization이면 `BASS/CAMB` amplitude ratio가 모든 cell에서 거의 상수, 또는 부호 convention까지 포함해 일관된 상수여야 합니다. 관측값은 `l=2`에서 `+0.21 → +121`, `l=3`에서 `-0.92 → +1836`, `l=4`에서 `+130 → -164`로 cell별 부호와 크기가 무너집니다. D7의 `D_2 ratio=1.005`는 baseline sub-horizon `D_2 ratio=32.17`에 amplitude `1/(4√2)`를 곱해 power를 `1/32`로 낮춘 weighted RMS coincidence입니다. 같은 보정이 full grid에서는 여전히 `ratio=23.64`라서 global physics normalization이 아닙니다.

**F2: 현재 BASS transfer extraction은 n_output에 수렴하지 않습니다.**  
`n_output=64→256→1024`에서 sign flip과 `19×` magnitude swing은 정상적인 dense-output refinement가 아닙니다. 현재 구조는 solver output grid를 그대로 source/LoS quadrature grid로 쓰며, `1024`도 recombination visibility peak를 충분히 resolve하지 못합니다. PCHIP overflow는 위험 신호지만 1차 원인보다는 증상에 가깝습니다. 현재 LoS는 대부분 knot에서 값을 쓰므로 PCHIP off-grid pathology만으로 sign flip 전체를 설명하기 어렵습니다.

**F3: Doppler 가설은 반박되고, shared source pipeline 문제가 맞습니다.**  
component superposition 오차가 `~1e-17`인 것은 ablation이 선형적으로 잘 분리됐다는 뜻입니다. Doppler dominance가 `<0.5%`라서 Doppler undersampling은 주원인이 아닙니다. SW+polter와 ISW가 각각 CAMB 대비 부호와 크기에서 k-dependent하게 틀리므로, 공통 원인은 `Ψ/Φ`, `Θ0`, polarization quadrupole, visibility/opacity, 또는 source-grid projection 계약입니다.

## Q1 / Q2 / Q3 / Q4 답변
**Q1.1** 진짜 `4√2` normalization이 있다면 먼저 isolated primitive에서 보여야 합니다. 예측은 `Θ0+Ψ+Π/4`, `Ψdot+Φdot`, CAMB `T_source`, 또는 최종 `Δ_l(k)` 각각에서 `BASS/CAMB ≈ constant`입니다. 현재 per-cell ratio의 분산과 sign flip은 이 예측을 정면으로 실패시킵니다.

**Q1.2** `D_2=1.005`는 physics reason이 아니라 weighted integral cancellation입니다. `∫|α|²P_R`는 transfer shape 오류를 숨길 수 있고, 실제로 sub-horizon 일부 과소/과대 구간이 power integral에서 우연히 `1/32`에 맞았습니다.

**Q2.1** PCHIP overflow는 원인 후보이지만 단독 root cause로 보기는 어렵습니다. 핵심 문제는 sparse output grid, source derivative, LoS quadrature가 결합된 구조입니다.

**Q2.2** adaptive IMEX/dense-output 관점에서 정상 동작이 아닙니다. `n_output`이 바뀌면 physical transfer가 아니라 sampling/quadrature artifact가 바뀌고 있습니다.

**Q2.3** 올바른 정책은 ODE integration grid와 LoS source grid를 분리하는 것입니다. source grid는 recombination/reionization visibility peak, late ISW region, 그리고 `j_l(k(η0-η))` oscillation scale을 기준으로 refined해야 합니다. 단순 uniform-linear `n_output` sweep은 production policy가 아닙니다.

**Q3.1** 가장 의심되는 shared quantity는 `Ψ/Φ` reconstruction과 gauge/sign convention입니다. 다음은 `Θ0`의 gauge mapping과 sparse-grid ISW derivative입니다.

**Q3.2** 추가 isolation은 BASS 내부 진단이 아니라 CAMB oracle 비교여야 합니다. CAMB `get_time_evolution`의 `Weyl`, photon monopole/dipole/quadrupole, `T_source`와 BASS `phi`, `psi`, `theta0_g`, `pi`, `source_T`를 같은 `(k,η)` grid에서 직접 비교하십시오.

**Q3.3** 1차 suspect는 [tier_b_source_extraction.py:291](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/spectrum/tier_b_source_extraction.py:291)와 [tier_b_source_extraction.py:299](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/spectrum/tier_b_source_extraction.py:299)입니다. MB95 Newtonian equations는 `δT^0_0=-δρ`와 `k²(φ−ψ)=12πGa²(ρ+P)σ` 구조를 쓰는데, 현재 doc/code의 `Φ/Ψ` sign, momentum bracket, anisotropic-stress addition은 repo의 [convention.rs](/home/cosmosapjw/Dropbox/bianchi/htt_base/src/core/convention.rs:201) 경고와도 충돌합니다. 단, 이 줄만 고치는 것은 위험합니다.

**Q4** incremental production fix는 보이지 않습니다. 가능한 incremental work는 root-cause localization과 oracle tests 추가까지입니다. architectural decision은 **Option B hybrid**가 맞습니다.

## 권장 fix path
1. Production FLRW scalar transfer는 CAMB `delta_p_l_k` 또는 CAMB source transfer를 import/cache해서 사용하십시오.
2. BASS PSTF는 Bianchi/aniso correction path로 제한하고, FLRW limit에서는 CAMB를 기준 anchor로 삼으십시오.
3. 별도 rework branch에서 `MB95/SZ96/CAMB` convention map을 재작성하십시오: `Φ/Ψ`, `Θ0` gauge transform, `σγ/F2/Π`, opacity sign, source term을 하나의 SSOT로 묶어야 합니다.
4. 이후에만 [flrw_pipeline.py:326](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/spectrum/flrw_pipeline.py:326)의 sparse output-grid LoS 구조와 [flrw_bessel_projector.py:416](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/los/flrw_bessel_projector.py:416)의 source construction을 재설계하십시오.

## Confidence and caveats
Confidence: high for “4√2 is not real” and “hybrid recommended”; medium for the exact first faulty line. CAMB convention risk was checked by reconstructing `C_l` from CAMB transfer data and matching CAMB raw scalar `C_l` at ~0.1%.

Primary references used: CAMB transfer docs, Ma & Bertschinger 1995 (`conformal Newtonian` Einstein constraints), Seljak & Zaldarriaga 1996 line-of-sight source formalism.  
Sources: https://camb.readthedocs.io/en/stable/results.html , https://arxiv.org/abs/astro-ph/9506072 , https://arxiv.org/abs/astro-ph/9603033
