# R5 문헌·근사영역 점검: exact low-moment transport와 finite tilt

작성일: 2026-09-27 KST. 역할: 독립 문헌·물리 범위 검토. 이 파일은 최종 승격 판정이 아니다.

**R5 통합 범위 고정:** 본문에 채택할 내용은 문헌 authority, exact geometry와 R3 retained radiation의 근사영역 구분, frame/jet 요구조건, 원문 Eq.(71)의 내부 부호 불일치 기록이다. 아래 §§3,5,6의 추가 유도는 **미검증 탐색 후보 부록**으로만 보존한다. 특히 exact quadrupole coercivity와 finite-electron-velocity Thomson kernel을 이번 R5의 CAS-checked/독립승격된 결과로 제시하지 않는다. R3의 rank 판정은 R3 retained linear radiation model에 한정하며 arbitrary finite-tilt radiation law의 식별성으로 확장하지 않는다. 취득 PDF/전체 파생텍스트/렌더는 로컬 검토용이고 최종 배포 ZIP에는 포함하지 않는다.

입력으로 `R4/MES_R4_REPORT_KO.md`, `R4/closure_derivation.md`(특히 §7), `R4/inputs/R3_REPORT_KO.md`(특히 §§1,4,6 및 보충 검토)를 직접 읽었다. 탐색은 SciSpace 질의 1회와 해당 원논문의 직접 취득·본문/화면 대조 1단계로 종료했다. 이 담당자는 과학 수치진화나 CAS를 실행하지 않았다. 아래 `derived` 식은 수작업 유도이며 최종 패킷의 CAS/독립 검토와 구별한다.

## 1. 문헌 권위와 확인 범위

원논문: R. Maartens, T. Gebbie, G. F. R. Ellis, *Cosmic microwave background anisotropies: Nonlinear dynamics*, Phys. Rev. D **59**, 083506 (1999), DOI https://doi.org/10.1103/PhysRevD.59.083506 ; arXiv v2 (1999-02-18): https://arxiv.org/pdf/astro-ph/9808163v2 .

| 위치 | 직접 확인된 내용 | R5 허용 사용 |
|---|---|---|
| Eqs. (53)–(56), PDF p.11 | 비편광 cold Thomson 원래 적분 kernel와 정확한 에너지/방향 frame 변환 | finite 상대속도는 원래 kernel에서 시작 |
| Eqs. (64)–(68), p.13 | 상대 baryon 속도 전개와 명시적 `O[3]` remainder | arbitrary finite electron velocity의 정확식으로 사용 금지 |
| Eqs. (69)–(71), pp.13–14 | 정확한 null 에너지 변화 및 distribution/brightness multipole 수송 | 운동학량의 크기를 선형화하지 않는 출발점; 아래 부호 불일치 주의 |
| Eq. (89), p.15 | quadrupole의 nonlinear Liouville 항; collision은 속도 전개 | source를 generic/exact kernel로 분리하면 수송항 대조 가능 |
| Eqs. (91)–(94), p.16 | FLRW 선형화 후의 식 | R3 전제를 유지한 비교용, finite-tilt exact adapter와 무조건 결합 금지 |

SciSpace는 저널 1999 레코드와 저장소 항목의 2022 metadata를 함께 반환했다. 연도·version은 arXiv/저널 원문으로 고정했다. SciSpace 검색 자체는 식 검증 증거가 아니다.

원본 PDF를 `MGE_1999_astro-ph_9808163v2.pdf`로 취득했으며 pp.13–15를 직접 렌더링했다. `MGE_1999_fulltext.txt`는 탐색용 파생 텍스트다. 웹 참조 ID(루트가 최종 인용하려면 재open 필요): `turn30view0`, `turn30view2`, `turn30view4`, `turn33view0`; 제목 메타데이터 `turn28view1`.

## 2. R3–R4를 잇는 정확한 regime 판정

**조건부로 가능:** 한 사건의 target congruence에서 brightness moments ℓ=0,…,4와 필요한 1-jet가 주어지면 정확한 quadrupole 관계를 평가할 수 있다. 특정 Bianchi 분류나 시간 진화 solver는 필요하지 않다.

**별개이며 성립하지 않는 주장:** ℓ≤4 evolution hierarchy가 일반적으로 자체 폐쇄된다는 주장. 상위 moment의 evolution에는 추가 상위 moment가 나타난다. 여기서 얻는 것은 한 사건의 constraint/inversion relation이지 닫힌 시간발전 계가 아니다.

R3 §4에서는 `A,σ,ω,vartheta_l` 및 perturbative jets를 1차로 놓고 곱을 버렸다. finite β의 기하학적 adapter를 쓰는 것만으로 이 버린 항들이 다시 포함되지는 않는다. `small radiation anisotropy in the chosen frame`과 `small kinematics/relative velocity`는 별도 가정이다. 전자를 유지하되 후자를 풀려면 exact Liouville weak identity와 source law로 되돌아가야 한다.

`beta`를 항상 두 종류로 구분한다: 선택한 정상 congruence에 대한 분석 congruence의 `β_u`, 그리고 그 분석 congruence에 대한 electron congruence의 `β_e|u`. 두 벡터를 단순 차로 대체하는 것은 일반 finite-boost 합성법이 아니다.

## 3. 독립 weak quadrupole 유도 — derived

R3 convention: `g=(-,+,+,+)`, `U=c u`, propagation direction `e`(outward sky direction의 반대), `a=A/c`, `H=Θ/3`, derivative-first vorticity vector `ω`. 모든 `H,a,σ,ω`는 s⁻¹. `⟨·⟩=(4π)⁻¹∫dΩ`이고 bolometric brightness를 `B(e)≥0`로 둔다. 공변 수송에서 angular horizontal derivative를 사용하며 선택한 triad의 회전항을 임의로 생략하지 않는다.

Null redshift/direction의 공변 rest-space 식은

\[
K(e)=H+a\cdot e+\sigma_{ab}e^ae^b,\qquad
V(e)=-P_e(a+\sigma e)-\omega\times e,\qquad
P_e=I-ee^T.
\]

에너지 감소율은 `−K`. 따라서 brightness Liouville operator는 `D_h B+V·∇_S B+4K B=S`; `D_h`는 `U+c e` 방향의 공변 horizontal 수송이다. 이 식은 distribution Liouville를 에너지 적분한 것으로 endpoint term `E⁴f→0`과 적분가능성이 필요하다. Planck 스펙트럼은 필요하지 않다. 온도 multipole와 동일시하려면 별도 스펙트럼 조건이 필요하다.

`q_ab=e_<a e_b>`에 대해 sphere integration by parts로 shear 항은

\[
\boxed{(\mathcal L_B\sigma)_{ab}
=\left\langle B\left[2e_{\langle a}\sigma_{b\rangle c}e^c
-(\sigma_{cd}e^ce^d)e_{\langle a}e_{b\rangle}\right]\right\rangle.}
\]

유도에 쓰인 항등식은 `div_S(P_eσe)=−3σ:ee`, `∇_S q·(P_eσe)=2e_<a(σe)_b>−2(σ:ee)q_ab`다. 첫 angular-advection 항의 약형에 redshift 항 `4(σ:ee)q`를 더하면 위 식이 된다.

`M_ab=⟨B e_a e_b⟩`, `M_abcd=⟨B e_a e_b e_c e_d⟩`로 쓰면

\[
\mathcal L_B\sigma
=\operatorname{STF}\{2\sigma_{c(a}M_{b)c}-M_{abcd}\sigma^{cd}\}.
\]

즉 연산자는 정확히 ℓ=0,2,4만 사용한다. STF 내적에서 self-adjoint이며

\[
\sigma:\mathcal L_B\sigma
=\langle B[2|\sigma e|^2-(\sigma:ee)^2]\rangle.
\]

`B≥B_min>0`이면 구면 2·4차 적분으로

\[
\sigma:\mathcal L_B\sigma\ge\frac8{15}B_{\min}\|\sigma\|_F^2.
\]

이는 충분조건이다. 좀 더 약하게 `M=⟨B ee⟩`가 양의 정부호이면 `2|σe|²−(σ:ee)²≥|σe|²`로부터 `σ:L_Bσ≥λ_min(M)||σ||²`도 얻는다. 특정 방향만 지지하는 비음 brightness에서는 SPD를 자동으로 선언하지 않는다.

같은 weak calculation에서 acceleration 항은 `2a_<a⟨B e_b>⟩`, vorticity 항은 `2⟨B e_<a(ω×e)_b>⟩`, expansion 항은 `4H⟨B q_ab⟩`다. 공간 수송은 rank-3 raw moment의 공변 divergence로 처리한다. 따라서 quadrupole equation은 정확하지만 미지의 `H,a,ω`, source 및 jet가 자유로우면 5개 식이 모든 운동학을 단독 식별하지는 않는다.

## 4. 원논문 내부의 부호 불일치 — 보존할 발견

PDF p.14 Eq.(71)의 마지막 lower-multipole shear 항은 실제 화면에도 `−(ℓ+2)σ_<aℓ aℓ−1 Π_Aℓ−2>`로 인쇄되어 있다. 단순 text extraction artifact가 아니다. 이 부호는 ℓ=2에서 같은 논문의 Eq.(89)의 양의 `8ρσ/15` 항과 맞지 않는다.

Eq.(70)의 해당 항을 원문 지시대로 직접 적분하면

\[
\int_0^\infty E^3[-E^{\ell-1}(E^{2-\ell}F)' ]\,dE
=(\ell+2)\int_0^\infty E^3F\,dE
\]

가 되어 **양의 부호**다(경계항 소멸 전제). 위 독립 weak derivation도 양의 isotropic shear response를 준다. 따라서 R5는 Eq.(71)를 부호까지 그대로 옮기지 않고 Eq.(70), Eq.(89), 자체 weak calculation의 일치하는 결과를 사용해야 한다. 이것은 이 로컬 원문의 내부 불일치 진단이며, 공식 erratum의 존재/원인까지 확인한 주장은 아니다. 더 넓은 원논문 감사를 이번 범위에 추가하지 않았다.

## 5. finite Lorentz boost와 low-moment 변환의 비폐쇄 — derived

동일 사건에서 `D=E'/E=γ(1−β·e)>0`, `e'^i=N^i(e)/D`라 하자. 여기서 `N(e)`는 boost한 null 4-vector의 공간성분으로 e에 affine다. Scalar distribution, 에너지 변수변환 및 aberration measure로

\[
B'(e')=D^4B(e),\quad dΩ'=D^{-2}dΩ,
\quad M'_l=\langle B D^{2-l}N^{\otimes l}\rangle.
\]

`l≤2`는 e의 최대 2차 polynomial이므로 stress-energy tensor의 유한 boost로 닫힌다. 반면 `l=3,4`에는 각각 `D⁻¹,D⁻²`가 남는다. 일반 angular sky에서는 이를 원 frame의 임의의 유한 low-l 목록만으로 정확히 구할 수 없다. finite boost가 bandlimit를 보존한다는 가정은 금지한다.

허용되는 세 계약은 (i) target-frame B3/B4를 직접 joint input으로 제공, (ii) 원 frame의 full angular B 및 jet에 정확 boost 적용, (iii) 명시한 angular family/tail norm과 remainder bound를 함께 사용한다. 이 외의 암묵적 고차 절단은 exact finite-jet 주장과 호환되지 않는다. 작은 β 전개는 별도 approximation lane이다.

## 6. exact cold-Thomson local source와 βdot의 역할 — derived from kernel

편광·electron thermal motion·recoil을 제외한 cold elastic Thomson kernel을 쓴다. 여기서 제외는 일반 polarized CMB에 exact라는 뜻이 아니다. `β_e|u`가 finite여도 전자 rest-frame photon energy가 Thomson 범위를 만족해야 한다.

전자 frame의 평균 `m_e=⟨B_e⟩`, STF quadrupole `Q_e=⟨B_e e_e<e_e>⟩`를 정의하면 kernel의 scatter-in brightness는 직접 적분으로

\[
\bar B_e(e_e)=m_e+\frac34Q_e:e_e e_e.
\]

분석 frame u에서 `D_e=γ_e(1−β_e·e)`, `Γ_e=c n_e σ_T`(`n_e`: electron rest number density)라 두면 exact **u-rate bolometric source**는

\[
\boxed{S_u(e)=\Gamma_e\left[D_e^{-3}\left(m_e+\frac34Q_e:e_e e_e\right)-D_e B_u(e)\right].}
\]

이는 `C[f]=n_eσ_T E_e(fbar−f)`를 u-frame energy로 적분한 결과다. `β_e=0`이면 `S=Γ(m+3Q:ee/4−B)`이고 quadrupole source는 `−9ΓQ/10`, monopole source는 0이다. 산란률 Γ=0이면 source가 velocity 정보를 제공하지 않는다.

이 source 계산에는 **βdot가 없다**. local source는 velocity value와 radiation stress/moments, local density에 의존한다. βdot는 boosted radiation tensor의 derivative 및 congruence acceleration/connection에서 나타난다. Source로 βdot를 제한하려면 matter inertia·압력/힘·Euler equation을 포함하는 별도 모델 계약이 필요하다. triad coefficient derivative `b=cE0β`와 covariant/gauge-corrected derivative를 혼동하지 않는다.

흥미로운 유한성: `m_e,Q_e`는 stress-energy boost로 u-frame moments l≤2에서 얻는다. `⟨q S_u⟩`의 loss는 affine D 때문에 u-frame l≤3만 사용하고, gain은 β 및 `m_e,Q_e`가 정하는 알려진 angular integrals다. 따라서 **generic B3/B4의 finite-boost 변환 비폐쇄**와 **특정 Thomson source moment의 finite local evaluation**은 서로 다른 명제다. 후자는 위 적분식으로 solver 없이 정의 가능하지만 실제 coefficient evaluation/CAS는 이 담당자 범위에서 미실행이다. β가 1에 접근하면 uniform conditioning/bounds를 별도 확인해야 한다.

## 7. R5 최소 admission 조건

1. `β_u`와 `β_e|u`의 carrier 및 frame을 별도로 고정한다.
2. finite tilt에 R3의 일차 식을 사용한다면 discarded products의 명시적 remainder를 넣거나 exact brightness weak law로 대체한다.
3. target-frame l3/l4와 그 jet가 어떤 정보로 제공되는지 위 세 계약 중 하나로 고정한다.
4. covariant derivative와 시간 회전 gauge의 변환을 전체 tensor slot에 적용한다.
5. Compact joint body에는 metric/connection, time jet, source rate, 밝기 coercivity, `|β|≤β_*<1`, norm/기준분모의 하한을 필요한 branch별로 포함한다.
6. 이는 조건부 물리 집합의 연속 image다. 정적인 CMB로 그 모든 입력을 식별했다거나 observed MES percentage를 계산했다는 주장은 별도 근거가 없다.

이번 bounded 문헌 단계는 종료한다. 독립 검토가 닫혀도 새로운 보편적 MES 계수, arbitrary-source 식별성 또는 데이터 기반 upper bound를 자동 승격하지 않는다.
