# 원래 78개 후보와 판정

원문 의미를 보존한 축약 진술이다. 수정된 정의는 별도 qualification 열과 증명 장에 둔다.

|ID|원래 후보|판정|증명|조건/수정|
|---|---|---|---|---|
|A01|Stored-real harmonic carrier는 weighted complex a_lm norm과 isometric이다|PROVED|P01|실수 sky의 a_l,-m=(-1)^m conjugate(a_lm), c=(a_l0,sqrt(2)Re,-sqrt(2)Im).|
|A02|Correct harmonic–STF map은 SO(3) action을 intertwine한다|PROVED|P01|같은 sky function과 회전 convention을 사용한다.|
|A03|Pure STF3 tensor는 degree 2,4,6,10 네 invariant의 minimal integrity basis를 가진다|CORRECTED|P02|O(3)에 대해서는 성립. 이 목록의 SO(3) framing에서는 degree-15 parity-odd invariant가 빠졌다.|
|A04|Generic (Q,O)/SO(3) orbit space는 9차원이므로 8 smooth scalar는 separating family가 될 수 없다|PROVED|P03|Q in Sym_0(3), O in STF3, generic trivial stabilizer.|
|A05|Simple-spectrum S와 cyclic v의 orbit은 (s2,s3,m0,m1,m2,sgn kappa)로 generic하게 결정된다|PROVED|P04|ordered real eigenvalues; polar vector; nonzero three eigencomponents.|
|A06|Q-eigenframe의 det[v,Qv,Q^2v]는 Vandermonde discriminant와 v1 v2 v3의 곱이다|PROVED|P04|고유값 차이의 Vandermonde 곱 자체이며 squared discriminant의 제곱근에 해당한다.|
|A07|det K!=0에서 orientation-fixed SO(3)-QR canonical frame이 유일하다|PROVED|P05|첫 두 QR diagonal을 positive, E in SO(3)로 고정한다.|
|A08|Krylov canonical pair (Qc,Oc)는 generic Q/O proper-rotation orbit을 분리한다|PROVED|P05|det K!=0인 open stratum.|
|A09|Canonical 12 components와 upper-triangular gauge의 3 constraints는 generic 9D orbit chart를 준다|PROVED|P05|gauge transversality를 증명한다. 12개 독립좌표라는 주장이 아니다.|
|A10|여러 equivariant seed vector를 사용하면 degenerate strata까지 덮는 finite canonical atlas가 존재한다|REFUTED|P06|nontrivial stabilizer를 가진 stratum에는 유일한 equivariant full frame이 존재할 수 없다. free stratum의 finite cover로 수정 가능.|
|A11|Krylov canonical field와 degree-bounded bispectrum invariant field는 generic stratum에서 rationally equivalent하다|REFUTED|P07|ordinary quadratic power plus cubic bispectrum로 해석하면 실패. QR square roots도 rational field equality를 막는다. 다른 bispectrum 정의는 별도 필요.|
|A12|Injective canonical chart 위 Gaussian kernel은 quotient distribution에 characteristic하다|PROVED|P08|standard Borel quotient, measurable injective chart, positive Gaussian bandwidth.|
|A13|Haar-averaged kernel은 group-invariant positive-definite kernel이며 조건부로 quotient-characteristic하다|PROVED|P08|compact SO(3), normalized Haar, double averaging; Gaussian base를 사용한다. arbitrary base kernel은 부족하다.|
|A14|Fixed quotient-kernel conformity score의 observation-inclusive finite rank는 exchangeable pool에서 exact하다|PROVED|P19|exact은 finite-sample validity; ties일 때 uniform equality가 아니라 superuniform.|
|B01|Sky RMS와 MES PSTF multipole norm 사이의 exact conversion|PROVED|P01|temperature expansion과 Delta_l를 명시한다. measured norm이 domain-wide MES upper premise를 증명하지는 않는다.|
|B02|STF2 shear orbit body는 0<=s2<=U, 6s3^2<=s2^3인 semialgebraic cusp다|PROVED|P09|spectral orbit quotient에 대한 exact characterization.|
|B03|\|tr S^3\|<=(tr S^2)^(3/2)/sqrt(6), uniaxial에서 포화|PROVED|P09|real symmetric trace-free 3x3.|
|B04|모든 tr S^n은 s2,s3 recurrence로 환원된다|PROVED|P09|p0=3,p1=0,p2=s2; k>=3.|
|B05|operator norm<=sqrt(2/3) Frobenius norm와 directional expansion bound|PROVED|P09|same rest-space metric and H>0 for MES normalization.|
|B06|mixed moments와 Cayley–Hamilton closure가 shear–vector moment cone을 정의한다|PROVED|P10|PSD Gram plus real-root spectrum은 repeated spectra에서도 존재성에 충분함을 추가 증명.|
|B07|Simple spectrum의 Vandermonde inversion으로 v_i^2를 복원한다|PROVED|P10|p_prime(lambda_i)!=0.|
|B08|Gram PSD는 (S,v) mixed moments의 necessary feasibility condition이다|PROVED|P10|CH closure와 spectrum condition을 함께 쓰면 sufficient도 성립.|
|B09|kappa^2<=m0^3(s2^3/2-3s3^2)/27 sharp bound|PROVED|P10|equal vector spectral weights에서 saturation; repeated spectrum는 kappa=0.|
|B10|norm STF(S_(ab v_c))의 exact identity와 MES upper bound|PROVED|P11|symmetrization에는 1/3을 포함한다.|
|B11|Geodesic MES shear bound는 vorticity decay-rate envelope를 준다|PROVED|P12|같은 congruence; A=0; omega!=0; all-time premise. homogeneous normal은 별도로 irrotational.|
|B12|Tilt anisotropic stress는 dot(tr sigma^3)의 mixed-moment source가 된다|PROVED|P12|일반 1+3 방정식과 Bianchi-I reduced equation의 pi coefficient를 구분한다.|
|B13|MES product body의 linear support function은 exact closed form이다|PROVED|P13|U_sigma,U_omega>=0, STF projection of the linear functional.|
|B14|Linear response image는 ellipsoid Minkowski sum이며 membership은 SOCP로 표현 가능하다|PROVED|P13|ellipsoid는 lower-rank image도 허용; existential SOC representation.|
|B15|Polynomial nonlinear response의 MES-compatible extremum은 compact semialgebraic optimization으로 표현된다|PROVED|P13|bounded physical variables, closed polynomial constraints; unbounded nuisances/\|v\|<1 alone는 제외.|
|B16|Archimedean norm bounds 아래 SOS hierarchy가 polynomial extrema에 수렴한다|PROVED|P13|Putinar positivity theorem 사용; finite-order exactness는 주장하지 않는다.|
|B17|Commuting shear history는 B=int sigma dt와 sharper Frobenius/cubic bound를 준다|PROVED|P14|matrix integral identity는 commutation 필요; norm bound는 그 가정 없이도 성립.|
|B18|Noncommuting history도 logarithmic endpoint deformation의 operator bound를 만족한다|PROVED_STRENGTHENED|P14|Fdot=sigma F, F(0)=I, sigma real STF integrable; Frobenius bound도 commuting 상수로 강화.|
|B19|Endpoint cubic invariant에는 integrated MES ceiling의 sharp one-way bound가 존재한다|PROVED_STRENGTHENED|P14|이전 16/sqrt(3) 상수는 valid but not sharp. sharp constant는 6.|
|B20|MES endpoint bound 위반은 ideal Bianchi-I와 해당 history premise의 incompatibility를 증명한다|PROVED|P14|kinematic control ball과 Einstein–matter reachable subset을 구별한다.|
|B21|Linearized MES의 remainder가 작으면 feasible body가 Hausdorff-stable하다|CORRECTED|P15|uniform correspondence 또는 explicit outer parallel body일 때 증명. one-sided norm premise만으로 actual solution sets의 양방향 Hausdorff bound는 불가.|
|B22|Scalar MES ceilings만으로 nonzero direction 또는 STF shape를 equivariantly 생성할 수 없다|PROVED|P06|deterministic map from trivial representation to nontrivial irrep.|
|C01|Lorentz boost는 exact harmonic aberration kernel로 CMB multipoles를 혼합한다|PROVED|P16|thermodynamic blackbody temperature, outward sky direction, exact Lorentz pullback.|
|C02|Quadrupole infinitesimal boost는 3 STF(beta tensor Q) octupole response를 생성한다|PROVED|P16|first order in beta; no intrinsic other-multipole terms implicitly removed.|
|C03|O:Q=(q2 I+6 Q^2/5) beta response identity|PROVED|P11|O=B_Q beta라는 response model에서; arbitrary O에서는 projection normal equation.|
|C04|q2 I+6 Q^2/5는 Q!=0에서 positive definite이고 uniformly well-conditioned하다|PROVED_STRENGTHENED|P11|2-norm condition number sharp upper bound 5/3; 이전 9/5도 valid but loose.|
|C05|Closed projection beta_hat=M^-1(O:Q)는 response subspace의 least-squares inverse다|PROVED|P11|Frobenius metric; general noise metric이면 whitened LS로 바뀜.|
|C06|O_perp=O-B_Q beta_hat는 O_perp:Q=0인 orthogonal residual이다|PROVED|P11|rank(B_Q)=3; residual dimension 4.|
|C07|Arbitrary intrinsic O_perp를 허용하면 beta는 단일 Q/O pair에서 point identified되지 않는다|REFUTED|P17|O_perp가 C06의 orthogonal residual이면 오히려 beta는 identified. unrestricted intrinsic O를 허용할 때 nonidentification.|
|C08|Ideal Bianchi-I isotropic blackbody emission에서 T^-2는 정확히 quadratic sphere function이다|PROVED|P18|single uniform emission surface, collisionless, achromatic propagation, known temperature calibration.|
|C09|Quadratic form은 A~A+lambda eta Lorentz gauge equivalence를 가진다|PROVED|P18|real symmetric A, exact restriction to full null cone.|
|C10|eta A의 timelike eigenvector와 eigenvalue differences가 beta,B,Tiso를 복원한다|PROVED|P18|strictly positive quadratic F on full sphere; rest-frame rotation convention specified.|
|C11|Generic timelike branch의 existence/uniqueness와 degenerate strata 분류|PROVED_STRENGTHENED|P18|모든 strictly positive quadratic F에서 유일성; repeated spatial eigenvalues는 axes만 불정, beta와 tensor는 유일.|
|C12|ell>2 residual은 ideal inverse model의 exact adequacy witness다|PROVED|P18|full-sky noiseless F residual is one-way falsification, not mechanism detection; mask/noise need forward modeling.|
|C13|올바른 bandpass 처리 후 frequency별 reconstructed T^-2 quadratic form은 동일해야 한다|PROVED|P18|known nonnegative bandpass의 full nonlinear Planck inversion; 단순 K_CMB 선형화와 다름.|
|C14|Frequency incoherence는 metric anisotropy parameter shift가 아니라 spectral/systematic model failure를 뜻한다|CORRECTED|P18|common achromatic model conjunction을 반증할 뿐, 특정 spectral/systematic 원인을 유일 식별하지 못한다.|
|C15|Gaussian T noise 아래 direct-T LS는 MLE이고 unweighted T^-2 fit은 일반적으로 효율적이지 않다|PROVED|P20|independent known variances; full transformed likelihood would preserve information on invertible positive domain.|
|C16|Small unmodelled component의 first-order parameter bias는 tangent-projected normal equation으로 주어진다|PROVED|P20|full-column-rank Jacobian and differentiable regular local solution.|
|C17|Residual이 model tangent에 orthogonal하면 first-order parameter bias가 사라진다|PROVED|P20|weighted orthogonality and regularity; higher orders remain.|
|C18|T,Q,U 전체에 대한 finite-boost inverse-square/projective generalization|NOT_A_DEFINED_PROPOSITION|P21|구체 transform/domain/conclusion 없는 연구제목. arbitrary polarization의 universal finite-quadratic closure는 반증. unpolarized isotropic seed는 Q=U=0을 보존.|
|D01|Affine radial velocity data는 bulk3 expansion1 shear5를 full-rank coverage에서 식별한다|PROVED|P22|explicit design matrix rank9; fixed positive radius full sphere is sufficient.|
|D02|Radial velocities만으로 antisymmetric solid rotation을 식별할 수 없다|PROVED|P22|n^T W n=0 for W^T=-W.|
|D03|두 shell의 distinct radial response coefficient는 local/global vector를 분리한다|PROVED|P22|known g1!=g2; unconstrained six linear parameters.|
|D04|Stacked local/global identifiability는 nuisance-projected full column rank와 동치다|PROVED|P22|known linear response and unrestricted additive linear nuisance; not arbitrary nonlinear models.|
|D05|Free optical-depth amplitude가 response와 완전히 겹치면 remote-field amplitude는 식별되지 않는다|PROVED|P22|amplitude scaling degeneracy; direction may remain identifiable.|
|D06|Remote likelihood와 MES feasible body의 intersection은 physical identified set을 좁힌다|PROVED|P23|subset/non-expansion만 보장. strict shrink는 보장 안됨; likelihood support와 identified set를 구분.|
|D07|Fixed-theta finite-rank test inversion으로 remote+MES confidence region을 구성할 수 있다|PROVED|P23|each true model calibrated; nuisance sup/union; exact MES premise or joint error budget.|
|D08|동일 seed를 공유한 두 pipeline 차이는 paired contrast rank로 calibration해야 한다|REFUTED|P23|paired contrast는 충분한 좋은 방법이나 유일한 유효 방법은 아님; joint calibration/Bonferroni 반례.|
|E01|Row-equivariant observation-inclusive rank는 exchangeability 아래 exact/superuniform하다|PROVED|P19|all score generation including adaptive choices must be equivariant; ties conservative.|
|E02|Integer LOO-ECDF midrank는 strictly monotone coordinate transform에 invariant하다|CORRECTED|P19|strictly increasing이면 동일 tail에서 성립. decreasing이면 upper/lower 교환이 필요하며 two-sided만 그대로 불변.|
|E03|전체 feature/tail selection을 pseudo-observation마다 재실행하면 adaptive exact rank를 갖는다|PROVED|P19|symmetric training and permutation-covariant randomization, including all choices.|
|E04|Known weighted exchangeability에서는 weighted rank validity를 사용할 수 있다|PROVED|P19|weights must equal conditional probability that each row is the query; estimated/arbitrary weights insufficient.|
|E05|Null mismatch는 exact exchangeability/known covariate shift/concept shift의 세 class로 구분되어야 한다|NOT_A_DEFINED_PROPOSITION|P24|overlapping non-exhaustive taxonomy, not theorem. unknown covariate shift is omitted.|
|E06|General shift 아래 coverage gap을 TV/Wasserstein score-distance로 bound할 수 있다|CORRECTED|P24|TV bound holds for full law/event. W1 needs anti-concentration or a calibrated-p coupling; unrestricted continuity at thresholds is false.|
|E07|Nuisance-whitened physical response cone projection statistic은 Gaussian GLRT다|PROVED|P25|closed convex cone and Gaussian known covariance. bounded MES body는 cone이 아니므로 같은 squared-projection formula 불가.|
|E08|동일 cone score를 row-equivariantly 계산하면 finite pool에서 exact conditional calibration된다|PROVED|P19|Gaussian assumption unnecessary for rank validity, required only for GLRT interpretation.|
|E09|Equal-sign dense Gaussian shift에서 sum/Stouffer가 max/min-p보다 높은 power 영역을 갖는다|PROVED_STRENGTHENED|P25|known iid unit Gaussian, d>=2, common positive mean: NP uniqueness gives strict superiority for every delta>0 at same nontrivial size.|
|E10|p_theta test inversion은 {theta:p_theta>alpha} confidence set을 준다|PROVED|P23|true point coverage, not automatically simultaneous coverage of whole identified set.|
|E11|MES-compatible와 test-inverted set의 projection은 cubic/mixed quantities에 simultaneous bounds를 준다|PROVED|P23|truth in common parameter set implies simultaneous transformed coverage; uncertain MES needs alpha+beta accounting.|
|E12|Conditional e-values의 product는 optional continuation 아래 validity를 유지한다|PROVED|P26|nonnegative adapted increment with conditional expectation <=1. marginal e-values not sufficient.|
|E13|Lane 선택을 conditional e-value/error rule에 묶으면 claim envelope를 유연하게 확장할 수 있다|PROVED|P26|predictable lane selection; establishes statistical evidence control, not physical ontology.|
|E14|Shared rows의 p/e-values를 independence 가정으로 곱하면 validity가 보장되지 않는다|PROVED|P26|explicit perfect-dependence counterexample.|
|E15|Typed absence가 row-equivariant하고 selection-independent일 때만 exact rank를 보존한다|REFUTED|P27|selection-independence is not necessary. symmetric data-dependent selection or invariant abort preserves validity.|
|E16|한 observation kernel score는 conditional anomaly rank를 주지만 two-sample consistency를 증명하지 않는다|PROVED|P27|single-query alternative mixture bounds attainable power away from1 even with infinite reference.|
