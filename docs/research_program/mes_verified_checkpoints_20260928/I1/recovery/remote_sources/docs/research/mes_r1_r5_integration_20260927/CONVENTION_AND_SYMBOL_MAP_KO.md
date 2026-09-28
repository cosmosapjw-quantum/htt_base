# Convention 및 충돌 기호 대응

Owner: LOCAL_CODEX_THEORY_HANDOFF_INTEGRATOR. Scope: R1–R5 source-level adapter, C0 / transfer none. 적용 식의 근거·hash·판정 범위는 CLAIM_LEDGER의 동일 claim ID를 따른다. 원문 기호를 소급 수정하지 않는다.

| 계약 | 통합 표기/변환 | 주의 및 출처 |
|---|---|---|
| signature·velocity | (−,+,+,+), U·U=−c², u=U/c | R1 DERIVATIONS의 unit U와 R2 physical U 구별 |
| rates | Θ,H,σ,Ω,ω,a=A/c는 s⁻¹; A는 m s⁻² | R4/R5 E_A는 length derivative; b=cE0β, q=cK |
| constants | c,ℏ,k_B 명시; a_R=π²k_B⁴/(15ℏ³c³) | B=a_R T_temperature⁴/(4π)는 방향별 흑체에 한정 |
| derivative | dot=U·∇; Dbar=c h·∇ | R1 path-length optical equation에서 rates/c 복원 |
| vorticity | Ω_ab=D_[a U_b], ω^a=ε^abc Ω_bc/2; ε123=+1 | derivative-first; antisymmetrization includes 1/2 |
| R7/55p adapter | Ω_R1–R5=−ω_R7_tensor; 55p의 length tensor=−Ω/c | signed curl/morphology에 중요; norm만의 일치는 sign 확인 아님 |
| norm | ||Ω||_F=√2|ω| | tensor-vorticity bound를 axial vector에 옮길 때 /√2 |
| directions | n outward/sourceward, e=−n propagation | odd ℓ와 derivative의 부호도 일괄 변환; even 그대로 |
| integration | <f>=∫f dΩ/(4π) | R1/R2 physical density M=∫B…; R5 부록 M=<B…>이면 /4π |
| brightness/temperature | B의 multipoles와 T⁴의 multipoles; ϑ는 brightness-normalized일 수 있음 | 온도 carrier는 Planck perturbation/spectral-distortion contract 필요; C0=0으로 부족 |
| gradient | R2 weak form ∂e는 ambient homogeneous polynomial derivative | sphere gradient로 교체 시 (1−ℓ),(2−ℓ) 항 함께 변환 |
| geometry | normal homogeneous slice vs tilted rest projection | normal ω=A=0은 branch 전제; tilted D에 timejet가 들어감 |
| approximation | exact geometry/bolometric Liouville vs retained first-order radiation | R5 finite p exact와 R3 omitted products를 섞어 exact radiation으로 부르지 않음 |
| source | geodesic/nongeodesic, collisionless/generic/cold Thomson | polarized source와 spin-2 screen 미검증; finite-electron candidate HOLD |
| beta | β_o endpoint observer boost, β_U|n congruence tilt+jets, β_e|U electron-relative velocity | finite boost 합성은 단순 차 아님; R7 beta_flow=f/b_gal은 이들 beta와 다름 |
| reference | verified conditional upper bound / attainable maximum / declared scale | sharpness·remainder 없이 maximum 또는 universal ceiling으로 부르지 않음 |

## 기호 namespace

| 원 기호 | 통합의 구별된 명칭 | 의미/단위 |
|---|---|---|
| R1 K | K_opt | dimensionless endpoint log-strain; present shear 아님 |
| R4/R5 K | K_ext | <∇_Ei n,E_j>, length⁻¹; q=cK_ext rate |
| R2 Ktilde | K_def | projected congruence deformation; exact boost+∇β |
| R5 부록 K(e) | R_ray(e) | photon redshift rate s⁻¹; K_opt 아님 |
| R4 K_D(t) | K_Peano | shell remainder kernel; endpoint tensor 아님 |
| R1/R2 T | T_temperature | temperature K; normalized tensor와 구별 |
| R2–R5 T | T_norm | signed radial/reference-normalized bundle |
| R5 companion T | W_boost=S_boost⁻¹ | SPD inverse boost spatial matrix; 최종 보고서는 W로 이미 분리 |
| R5 S | S_boost | I+g²ppᵀ/(g+1); R1/R2 S_shear=σ와 구별 |
| R1 B / R2 script B | B_brightness | bolometric energy density per solid angle |
| R5 B | B_def | rest gradient derivative-first 3×3 rate matrix |
| Pi/πγ | π_rad / M2−ρI/3 | physical radiation STF quadrupole, energy density |
| Pi(q) | Pi_tail_tensor(q) | tensor exceedance; trace is tail under stated law |
| R1 A_sigma | T_sigma_norm | normalized shear amplitude; physical A_acc와 구별 |
| R2 A_B / R5 A(p) | A_response / A_jet | radiation response / 12×9 affine jet matrix |
| R3 Dconfidence / Ddistance / Dpercent | D_design / r_distance / D_margin | map / length / 100(1−γ); derivative Dbar 별도 |
| R5 disk x,z | x_disk,z_disk | latent disk coordinates; legacy signed x 아님; z_disk redshift 아님 |
| Q | Q_outer vs Q_gauge vs Q_temperature | outer product / premise gauge / harmonic STF carrier |
| F | F_amp vs F_support | squared reference fraction / directional support utilization; 동일 정의 아님 |
| G | G_tensor vs G_path vs G_connection | tensor two-state growth / registered coherence path / connection norm |

## normalization과 확률 계약

R1 shear pilot x_sigma=||σ/H||²/6, U_sigma=3 B_sigma²/2이면 A_sigma=σ/(3HB_sigma)이며 Q_sigma=x_sigma/U_sigma=||A_sigma||²다. R2 T_norm은 같은 shear sector에서 이와 일치한다. Full legacy signed x의 음의 와도·부호 있는 곡률·tilt 수축은 별도로 보존한다. Ω_tilt=|β|²라고 새로 정의하지 않는다.

Amplitude margin D=100(1−γ)=100(1−√F_amp), quadratic occupancy 100F_amp, norm fraction100√F_amp를 구별한다. 유효한 bound 내부에서만 F_amp∈[0,1]이며 noisy output을 clipping하지 않는다. denominator=0,unknown,infinite 또는 joint state가 0 denominator를 포함하면 undefined/unbounded branch를 남긴다.

Sector bounds의 product와 coupled ellipsoid는 다르다. 식별공간에서는 projection(P_I B)을 쓰고 intersection(B∩I)는 미관측 성분=0의 추가 전제다. Deterministic body는 confidence set이 아니며 posterior/sampling law 없이 Pi를 계산하지 않는다. G에는 사전 선언한 isometric frame/transport와 양의 분모가 필요하다. 두 depth label만으로 두 사건의 kinematics가 측정되지 않는다.

R5 equal-block disk의 radii와 1/√3는 선언 sensitivity convention이다. 각 sector의 fraction과 전체 radial gauge를 일반 상황에서 같은 값으로 취급하지 않는다. 원 full tensor·harmonic phase·cross block과 same-state denominator를 보존한다.
