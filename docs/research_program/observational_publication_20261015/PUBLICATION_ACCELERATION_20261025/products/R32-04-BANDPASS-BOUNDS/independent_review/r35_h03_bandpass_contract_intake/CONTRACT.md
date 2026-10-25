# H03 structured discrepancy and seven-row bounded moments: implementation preparation

Prepared 2026-10-25 for the existing READY nodes R32-03-H03-STRUCTURED and R32-04-BANDPASS-BOUNDS. Requested framer: gpt-6-astra/xhigh; observed runtime: UNKNOWN. This is source/contract preparation, not a controller packet, execution, independent admission, publication, or original42 completion. The controller retains task/account identity, actual current source binding and all existing limits. This framer must not be the final independent reviewer. Repository, STATE, Git and products were read only. Only this external preparation directory was written.

The source inspection used htt-physics-math-audit, htt-observable-statistics and htt-xqpi-fg-formalism. No numerical SVD, response integration, raw sky/catalogue read, solver or ODE was performed. Simple norms of already accepted stored coefficient witnesses are explicitly distinguished from a new minimization. No new literature search was needed: the actual questions are finite linear algebra under the supplied retained definitions, and the relevant physical interpretation was already source-bound in R31.

## Source binding and directly consumable inputs

Let `P=/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025`.

Read `P/FRONTIER.json` task IDs above and `P/OUTPUT_DAG.json`; downstream R32-08 and R32-09 consume their qualified products only after actual execution and independent review. No state action follows from this note.

| Input relative to P | SHA256 | Consumed content |
|---|---|---|
| `evidence/sources/H03_SOURCE_TOMOGRAPHY.json` | `5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326` | four window means, complete joint36 covariance, saved bulk responses, centers/width and method fractions |
| `evidence/output/physical_results.json` | `25342649e30a8d631a5364002ae39ebffae0a5d92e1e4ad25c9e2f8dfe9362cc` | accepted extracted12D arrays and existing fits/thresholds; cross-check only |
| `evidence/research/physical_checks.py` | `cfe564b7980705a344f9b0f3941b91c744f4edc53096ae3e923ce716cfb7af2d` | existing extraction and GLS definition; do not execute its unrelated plots/checks |
| `evidence/R31/report/data/RESULT.json` | `b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f` | exact six stored7x9 matrices, scales, signed order and witnesses |
| `evidence/R31/scientific/framing/SPECTRAL_ONLY_CONTRACT.md` | `fb137b19b2ec901604691f5d4aa62f05a29e5cbe86404c3c748bf8c8c40386df` | full finite-model spectra, derivatives, row/unit conventions |
| `evidence/R31/report/evidence/INDEPENDENT_REVIEW_RESULT.json` | `ac948932ba9827ae9368ed05e8cbc1417d1fe8999cce10c0b51d9c4ec497537f` | accepted finite six-branch rank/complete24 result, not new admission |

All six hashes were checked against the existing EVIDENCE_MANIFEST in this intake. The old executable external R31 payload also exists at `/mnt/extdrive/workdir/htt_open_data/r30_cmb_spectral_response_numeric/attempt_38cdf6b948a41ee9/RESULT.json` with the same `b4c20f...291f` hash. Prefer the manifest-bound repo copy. Do not run the old producer, checker, integration or map pipeline.

The R33 extension's `/mnt/extdrive/workdir/htt_open_data/r35_wmap_planck_fresh_astra_review/RESULT.json` records SCOPED_FINITE_CONDITIONAL_PASS and `/mnt/extdrive/workdir/htt_open_data/r35_cmb_checker_api_fix/RESULT.json` records INDEPENDENT_NUMERIC_CHECK_PASS. These concern added WMAP rows. Their12/17-row matrices do not replace the seven rows required here; real-noise usefulness remains unqualified. Their checker elapsed17.4991413122043s is historical, not a new charge or allowance here.

## H03: sufficient statistics and frozen baseline

Use the window-major ICRS J2000 Cartesian order `(x,y,z)` for each of four windows. In zero-based indexing, `I=[9*w+j for w in range(4) for j in (1,2,3)]`. Set:

```python
j = json.loads((P/'evidence/sources/H03_SOURCE_TOMOGRAPHY.json').read_text())
wins = j['monopole_dipole_STF2_windows']
I = [9*w+k for w in range(4) for k in (1,2,3)]
y = np.concatenate([w['dipole_cartesian_km_s_Mpc'] for w in wins])
C = np.asarray(j['joint_covariance_36x36'])[np.ix_(I,I)]
R = np.vstack([np.asarray(w['bulk_velocity_design_response_9x3_per_Mpc'])[1:4,:]
               for w in wins])
G = np.tile(np.eye(3),(4,1))
X = np.column_stack((R,G))
```

The inherited model is `y=R b+G d+D eta+e`, with b in km/s, d and y in km/s/Mpc, R in inverse Mpc, and `e~N(0,C)` only as the retained working law. C has units `(km/s/Mpc)^2`; preserve all cross-window and cross-axis entries. It is the12D marginal submatrix, not a Schur complement conditioning on observed monopole/STF coordinates. The original source has35970 groups, an assumed diagonal row-scatter law, shared groups across windows and unknown shared calibration/PV/selection contributions.

Frozen baseline: `rank(X)=6`, `T0=23.396720522667167`, `df=6`, `tau=chi2.ppf(.95,6)=12.591587243743977`, baseline working tail `.0006739334199762943`, unrestricted whitened mean budget `eta95=1.2885530036501112`. The covariance dipole-block minimum eigenvalue in retained checks is `.0038312674410547736`. Replacing C by window block diagonal gives `T=8.925712182985682`, illustrating a material forbidden substitution. `tau` remains fixed after optimizing sensitivity parameters; do not recompute a post-fit df or a new nominal p-value.

## H03: practical D fixed before new outcomes

No signed calibration Jacobian is supplied in this retained source. Family deletion entries contain dipole norms, not signed directional shifts, and cannot reconstruct such a Jacobian. Use the following **conditional finite-window response designs**, not an inferred physical error model.

Let `u0=1 km/s/Mpc`, `z=[.025,.04,.06,.08]`, and saved width `h=.012`. Define `t_w=(z_w-.04)/h`, giving `[-1.25,0,5/3,10/3]`. Let `p_w=wins[w]['source_method_distance_weight_fractions']['FP']`, exactly:

`[.30371471086623375, .53491723769988, .8024115244860296, .901889873332754]`.

Let `f_w=p_w-p_0`. For each Cartesian axis a, freeze:

* `D_z[(w,i),a]=u0*t_w*delta(i,a)`: an assumed linear change of angular rate across finite window centers, measured per one saved window width.
* `D_FP[(w,i),a]=u0*f_w*delta(i,a)`: an assumed dipolar offset modulated by the retained FP distance-weight fraction. This is a composition proxy, not the actual response to a distance-modulus zero point.
* `D_joint=[D_z,D_FP]`, depth columns first, then FP columns, each `(x,y,z)`.

Report all three designs; do not choose a preferred one from its residual reduction. The first two each have at most three projected directions, hence cannot span the six-dimensional fitted-signal residual space. D_joint has at most six; measure rather than assume its rank. The central subtraction in f is absorbed by the existing G signal and does not change its projected column space. Anisotropic/method-shared physical calibration assumptions are not added.

The primary coefficient metric is `M=I_p` for each p=3 or6 design: `eta^T M eta<=rho^2`, with eta dimensionless relative to u0. This makes rho a declared joint sensitivity budget, not an observed rate or uncertainty. Keep all coefficients jointly bounded, not separate unlimited axis budgets. Equations below also cover any explicitly supplied SPD M, but the worker must not select a different physical prior or metric after seeing outcomes.

## H03: projection, ellipsoid, trust region and exact attainment

Take `C=L L^T`, `W=L^{-1}`, `A=W X`, and a QR-based orthogonal projector `P=I-Q_A Q_A^T`. Define `r=P W y`, `B=P W D M^{-1/2}` and `xi=M^{1/2}eta`. Then

`T_min(rho)=min_{||xi||<=rho} ||r-B xi||^2`.

The discrepancy image is the possibly degenerate ellipsoid `E_rho={B xi:||xi||<=rho}`. Its support is `h_E(u)=rho*||B^T u||`; if `B^T u!=0`, it is attained at `xi=rho*B^T u/||B^T u||`. If `B^T u=0`, the support is zero and xi=0 is an attaining choice. A proposed projected correction q is attainable iff `q in col(B)` and `||B^+q||<=rho`. Thus a sphere bound alone is not sufficient for a non-spanning D.

For a thin resolved factorization `B=U diag(sigma) V^T`, let `alpha=U^T r` and `r_perp=r-U alpha`. Keep `T_perp=||r_perp||^2` explicitly, including its full signed12-coordinate vector. Let `rho_sat^2=sum(alpha_i^2/sigma_i^2)`. For `0<rho<rho_sat`, there is a positive multiplier lambda satisfying

`sum[sigma_i^2 alpha_i^2/(sigma_i^2+lambda)^2]=rho^2`.

The unique minimum-norm optimizer is `xi_lambda=V diag(sigma_i/(sigma_i^2+lambda))alpha`, and

`T_min=T_perp+sum[(lambda/(sigma_i^2+lambda))^2 alpha_i^2]`.

For rho=0, T_min=T0. For rho>=rho_sat, use `xi=B^+r` and T_min=T_perp; no coefficient-space null direction is needed. If B=0, T_min=T0 for every rho. These formulas follow from the convex quadratic KKT equations; the ellipsoid support follows by Cauchy-Schwarz, with the displayed equality witness. This is a derivation/specification; the future run checks its implementation.

The **minimum allowed coefficient budget** for the unchanged tau is:

* zero if T0<=tau;
* infinity / `THRESHOLD_UNATTAINABLE_FOR_THIS_D` if T_perp>tau;
* rho_sat if T_perp=tau<T0 (equality is attainable at a finite budget);
* otherwise find the unique lambda>0 satisfying `T_perp+sum[(lambda/(sigma_i^2+lambda))^2 alpha_i^2]=tau`, and evaluate rho from the first equation.

Recover `eta=M^{-1/2}xi` and refit the original six signal coefficients to `y-D eta`; save that full witness and check its actual GLS residual. Never merely subtract D without profiling the signal, replace the six-df working threshold by12-rank([X,D]), or call the minimizing sensitivity budget a measured calibration amplitude.

For a directly comparable secondary **projected-whitened-effect budget** q=||B xi||, the exact restricted-subspace minimum needed to reach tau is `sqrt(T0-T_perp)-sqrt(tau-T_perp)` when `T_perp<=tau<T0`; zero if already adequate, infinity if the floor is above tau. This uses a different budget than rho. At a finite coefficient-budget witness also report `q95=||B xi95||`, which must be at least the unrestricted `1.2885530036501112` (up to tolerance). Report `rho95>=eta95/||B||_op` as a basic check; never compare dimensionless raw rho and eta95 as if their image metrics were identical. The unrestricted comparator curve remains `max(0,sqrt(T0)-q)^2`.

H03 implementation controls: retain exact source hashes; C symmetry at1e-12 relative scale and Cholesky positivity with no jitter; extracted arrays agree with retained physical_results; T0 within1e-9, tau within1e-12 and eta95 within1e-9. Projector idempotence/symmetry and `P A=0` within1e-10 relative Frobenius. Resolve B singular values relative to its largest: >=1e-10 nonzero, <=1e-12 zero, intermediate `NUMERIC_RANK_HOLD`; B=0 handled separately. Do not threshold away a nonzero irreducible residual. Trust-region norm/KKT and direct refitted T at reported crossings agree within1e-8 scaled; roots to1e-10 relative/absolute budget and T residual<=1e-8. Actual data within1e-9 of a feasibility boundary require a numerical-boundary qualifier, not an arbitrary side assignment.

Minimal falsifiers: (1) replace C by block diagonal and verify the known wrong baseline8.925712 differs; (2) D=X gives B=0 and no improvement; (3) a synthetic correction in col(B) cancels only that component, leaving r_perp; (4) a synthetic floor exactly tau attains equality at rho_sat, not infinity; (5) D=L with p=12 and M=I recovers the unrestricted radial formula after projection; (6) simultaneous fixed orthogonal Cartesian rotation of y,C,X,D preserves T and budgets; (7) primary non-spanning designs preserve their measured floor for arbitrarily large budget; (8) zero budget returns the baseline and T_min is monotone. These are targeted synthetic controls, not new survey evidence.

Deliver table/curve for the three fixed designs, full signed projected correction/residual witnesses, rho95/floor/status, the distinct q95 comparison and a compact equation section. No physical-response input is needed to finish this conditional design product.

Stronger physical branch requires a signed source-bound derivative of each retained window estimator with respect to named calibration/PV/selection parameters, in the same units/frame, plus an externally justified joint coefficient bound/law. For actual WLS `theta=N^{-1}b`, the derivative is `dtheta=N^{-1}(db-dN*theta)`; changing distances, design or weights cannot be replaced by row fractions alone. Require the real row-response/design/weight dependence or an already computed equivalent Jacobian and its source binding. Missing shared covariance, calibration magnitudes, observer/cosmographic transfer and physical remainder bounds stay branch-local UNKNOWN/HOLD.

## Bandpass: keep exact seven-row and nine-column definitions

Use `branches` from the hash-bound old RESULT without changing any matrix entry. Branch order is `A_BT_1e-07`, `A_BT_1e-08`, `A_BT_1e-06`, `B_BT_1e-07`, `B_BT_1e-08`, `B_BT_1e-06`. For each, `F=branch['F2']['matrix_7xk']` is7x9 and `a=branch['cmb_unity_responses']` is seven ones. Frequency order is030,044,070,100,143,217,353PSB. No SMICA or added WMAP row.

Keep moment order: `(s, s_beta, d, d_beta, d_t, s_betabeta, d_betabeta, d_beta_t, d_tt)`. Here t=(T-20K)/20K; reference beta_s=-3 (RJ), beta_d=1.5, nu_s=30GHz, nu_d=353GHz, T_CMB=2.7255K. Factorials were absorbed in coefficients. Every coordinate remains signed/free; second-temperature differentiation is T_d^2*d_T^2, not (T*d_T)^2. Response conventions and finite retained-node trapezoid definitions are inherited; do not integrate again. All six stored F2 ranks are7, augmented rank7 and complete target quotient rank0 for the FREE9 linear class. This is finite numerical rank, not a theorem that every physical foreground realizes every moment array.

Full target coordinate order is E2(5), E3(7), B2(5), B3(7), each ordered m=0 then positive-m `(sqrt(2) Re,-sqrt(2) Im)` pairs. Y is7x24 (frequency-major flattened); U is9x24 (moment-major flattened). The model is `Y=a s^T+F U`, equivalently A=a tensor I24 and B=F tensor I24. The budget is joint across all9 moment maps and24 signed target coordinates; individual scalar or norm-only data cannot replace Y.

## Bandpass: declared metric, minimum coefficient budget and directions

Freeze **one common primary metric across all six branches** from the nominal branch's stored scales:

`d=(1.261652382369369, .1777139521270542, 1.1309894216176297, .09451923139372441, .04109240642871376, .1151042544103929, .07145402059880916, .022520789584731377, .09386151314750793)`;

`M=diag(d^2)`.

This measures the sum of squared reference-branch column-normalized moment amplitudes. It is a computational moment metric, not measured noise or a physical foreground prior. Do not recompute M separately for each branch and quietly compare different classes. Report the additional raw-coordinate M=I calculation explicitly as metric sensitivity. All9 coordinates participate together in both metrics.

For any SPD M and full-row-rank F define `K=F M^{-1}F^T`. Then

`c_M=M^{-1}F^T K^{-1}a`, `ell_M^2=a^T K^{-1}a`.

This is the unique minimum-M-norm solution of F c=a. Every other solution is c_M+n with F n=0 and squared norm `ell_M^2+n^T M n`; this orthogonality proves minimality. The previously stored nine-component c is the M=I minimum-norm witness, not automatically the minimum for the primary M.

For metric-defined directions use `F M^{-1/2}=U_f diag(sigma) V_f^T`: whitened coefficient directions are V_f, original-coordinate directions are M^{-1/2}V_f, and `ell_M^2=sum[(u_i^T a)^2/sigma_i^2]`. Save sigma, the CMB projections and their budget contributions; singular values alone do not determine the CMB budget. Complete coefficient nullspace dimension2 remains present. New small-matrix calculations belong to the lower-tier actual execution, not this intake.

Retained raw-M=I witness norms, calculated here solely by summing squares of accepted stored c, are respectively `59.59210452696802`, `59.59209151806858`, `59.592192355037646`, `59.57284170474581`, `59.57282871526661`, `59.57292946657371`. These are source-reuse reference values for the future minimizer check. Existing normalized smallest singular values span `.00552639855542408` to `.005544094237990982`; the old witness relative residuals span1.73e-15 to1.39e-14. No new primary-metric ell value is asserted in this preparation.

## Bandpass: full24 identified set and the factor of two

Define the free bounded class `||U||_M^2=tr(U^T M U)<=rho^2`; U and rho have the target amplitude unit, consistently K_CMB or microK_CMB throughout. For specified Y and any candidate s, the unique minimum-budget U is

`U_s=M^{-1}F^T K^{-1}(Y-a s^T)`.

Thus the exact conditional identified set is

`S_rho(Y)={s in R24: tr[(Y-a s^T)^T K^{-1}(Y-a s^T)]<=rho^2}`.

Let `s0=Y^T K^{-1}a/ell_M^2` and `J0=tr{Y^T[K^{-1}-K^{-1}a a^T K^{-1}/ell_M^2]Y}`. Completing the square gives `J0+ell_M^2||s-s0||^2<=rho^2`: empty if rho^2<J0, otherwise the full24 ball centered at s0 of radius `sqrt(rho^2-J0)/ell_M`. Compute J0 stably from the residual at s0, not by subtracting nearly equal large traces; never silently clamp a materially negative value. This is a deterministic compatible set under a declared response/budget, not a confidence region or posterior. No observed Y is newly consumed in this task; display the formula and labelled synthetic witnesses.

For one foreground compensating a target shift v from zero, `Delta U=-c_M v^T`, with minimum norm `ell_M||v||`: attainable iff `||v||<=rho/ell_M`. For **two** allowed foregrounds U1,U2 each satisfying the same radius rho, their difference may have norm2rho. A common-data target difference v is possible iff `||v||<=2rho/ell_M` for some data; explicit witnesses are `s1=v/2`, `s2=-v/2`, `U1=-c_M v^T/2`, `U2=c_M v^T/2`, both giving Y=0. For a fixed generic Y the diameter is the smaller `2sqrt(rho^2-J0)/ell_M`. Do not confuse the one-compensator radius with the pairwise diameter or label either an observed CMB amplitude.

The required budget-versus-amplitude figure should plot both `rho/ell_M` and `2rho/ell_M` for each retained convention (and separate metric panels if showing M=I). Equivalently plot required budget ell_M*A and ell_M*A/2 against target tensor norm A. Preserve the full tensor witnesses behind the radial summary. The fixed zero-data identified ball gives a complete synthetic attainment illustration; the zero-centered class, not a physical sky null, creates it.

Numerical controls: preserve all old input hashes/rank facts and six conventions; new Fc=a relative residual<=1e-10; KKT `M c=F^T lambda` relative<=1e-10; compare raw-I ell to stored-witness norms to1e-8 relative. Verify minimality by M-orthogonality to the2D nullspace and positive quadratic norm increments. Solve K with a stable factorization; do not claim stability from a small residual alone. Use an independent high-precision solve on the cached7x9 matrix if needed for an ambiguous output; no source reintegration or reset of old rank checks. The final exported binary64 coefficients themselves must satisfy the residual gate, not just an internal higher-precision precursor.

Check all24 basis degeneracy actions and a mixed signed vector, at1e-9 relative; moment arrays are216D. At A=rho/ell and A=2rho/ell verify the explicit one/pairwise witnesses and their individual norms. Test a deterministic1% larger amplitude against the proved minimum to reject it. Test a synthetic generic Y with J0>0 for empty, singleton and nonzero-radius identified sets; recompute U_s to verify feasibility. At rho=0 the class reduces to U=0. As rho tends to infinity the free-class rank-zero obstruction is recovered. Nonzero column rescaling F'=F S, U'=S^{-1}U must carry M'=S^T M S and leave K/ell/identified sets invariant; failing to transform M is a change of model, not a numerical discrepancy. Simultaneous orthogonal rotations of the24 carrier coordinates preserve the joint norm and set.

Minimal falsifiers are a missing factor2 for pairwise degeneracy, replacing9 jointly bounded moments by scalar bounds, substituting12/17 rows, branch-dependent unannounced metrics, altered signed harmonic order, untransformed column rescaling, positivity imposed without a physical realization, or a residual checked only on one target coordinate. Existing signed moment coefficients cannot be required to be nonnegative merely because some underlying intensity is positive; polarization/harmonic moments and derivative moments need their actual realizability constraints. Optional physical positivity/coupling is a separate supplied finite constrained class and cannot block this free bounded result.

Stronger physical branch requires independently justified moment magnitude/coupling/remainder constraints, actual component-specific spatial response, real joint noise/calibration and a physically justified radius/metric. A blackbody-spectrum nuisance remains confounded. The future conditional numerical product leaves x and observed quotient tensor NOT_MEASURED, Q NOT_EVALUATED, F_physical NOT_EVALUABLE, Pi NOT_CALIBRATED and G_F NOT_APPLICABLE (frequency is not depth). No original42, physical global-tilt, family-identification or native-solver claim is promoted.

## Handoff and stopping rule

The mathematical designs/metrics above are now explicit before any new result. The selected lower-tier worker implements only the currently dispatched node in its assigned product path under the controller's existing limits and source seals. Preserve first numerical failures and return substantive tolerance/model failures to the controller; do not redesign D, M or the class to obtain a preferred result. The final fresh independent reviewer must be a different agent from this framer and the implementer. No hard time bank, dispatch count, one-use allowance or prior account was created/reset by preparation. No missing input prevents the two conditional base products; missing stronger physical inputs remain separate branches.
