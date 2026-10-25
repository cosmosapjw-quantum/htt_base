# Frozen pre-ACK clarification: ideal annihilation and binary64 leakage

This additive clarification applies to NEXT_CONTRACT.md SHA25680611699ffb4226b295c5dcb3a0c8ba9e5526a3f807747a17f24ba53b06c2678 before the first acknowledged execution. It resolves the meaning of “exact”, K and covariance cancellation in lines7,31–39,62–66,70,81–84. The original contract bytes, source family, estimator algorithm, tolerances, numerical controls, cohort, acceptance scope and120s+30s/600s account are unchanged. It adds no execution, scientific admission, CAS promotion, new review tier or extra test campaign. Root explicitly requested this clarification while the prepared consumer remains unexecuted/unacknowledged.

## Exact model identities

The support model defines C, E_M, Z and every admitted A by the stated released row supports. Its identity A=C+E_M A[M,:] is exact in that mathematical model; verifying three floating representative maps is not its proof. The zero/one support structure may be represented exactly by integer/Boolean arrays. It remains a conditional source-supported model, not a complete producer calibration law.

To distinguish notation, let W=diag(d_i^(-1/2)) and U_J=Z W [N,C] be mathematical real matrices for the specified fixed inputs, with d_i>0. Let U_J^+ denote its exact Moore–Penrose inverse and define

  P_star = Z - U_J U_J^+,
  R_star = P_star W B,
  K_star = R_star^+ P_star W.

Since range(U_J) is contained in range(Z), P_star is the ideal orthogonal complementary projector. The support decomposition proves

  P_star W A=0, P_star W N=0,
  K_star A=0, K_star N=0

for every admitted A, independent of a tolerance-selected numerical rank. R_star^+ is a mathematical definition, not an assertion that its exact entries or exact rank have been evaluated. For the full-rank ideal branch it is the original inverse-based definition; for rank loss it supplies the ideal minimum-norm operator with its true mathematical range. A numerical SVD with fixed tolerances does not certify that range.

The covariance cancellation statement in the original contract applies to this K_star: K_star A Gamma A^T K_star^T and the corresponding residual–calibration cross terms vanish algebraically whenever the stated joint moments exist. The covariance of the remaining physical residual, selection effects, source model and all original physical gates stay unresolved.

An exact factored **definition** consisting of the support data, fixed matrix references and the equations above may be returned as the intended functional. It is not an evaluated exact matrix, a verified error bound for its numerical evaluation, a CAS certificate or physical calibration qualification. If arrays for B,N,d were computed in floating point, distinguish their fixed serialized-real interpretation from the ideal reference formulas and from physical source uncertainty.

## Computed matrix and observed numerical result

Use K_hat,Q_hat,R_hat for the stored/computed binary64 arrays. The inherited normalized checks such as ||K_hat A||<=1e-10 test numerical consistency only. They do not establish K_hat A=0 in exact arithmetic. Printing a rounded zero, a small norm, or even obtaining zero from a floating dot product is not an exact contraction certificate; cancellation and underflow remain possible. No numerical threshold converts a small nonzero leakage into an exact annihilator.

A floating point estimate b_hat=K_hat y, the working metric matrices, signed tensor components and rank decisions are numerical outputs. They may be useful and pass the unchanged numerical checks while lacking a rigorous forward-error bound to K_star y. Agreement across1e-12/1e-10/1e-8 thresholds remains a stable *numerical* rank observation, not a proof of exact dependence or exact rank. The frozen rank-loss, uncertainty and no-zero-fill branches remain intact. If truncation selects a different mathematical rank, closeness to the exact pseudoinverse is not supplied merely by a small projector residual.

Mixed-row columns explicitly written as binary zero can be reported as structurally bit-exact zero columns of the saved K_hat. This establishes absence of those row contributions for that serialized linear functional. It does not establish exact singleton/direct-channel annihilation. In the real interpretation of saved entries, structural mixed zeros imply

  K_hat A = K_hat C

for every A in the support-simplex model, but the remaining sums K_hat C may be nonzero. Thus exact support decomposition and bit-exact mixed zeros coexist with only numerical checks of whole calibration annihilation.

## Consequence for unbounded calibration covariance

For E=K_hat A, if E is nonzero, choose v with Ev nonzero and Gamma_t=t vv^T. Every Gamma_t is PSD and

  E Gamma_t E^T = t (Ev)(Ev)^T

is unbounded as t grows. Therefore even an arbitrarily small nonzero leakage admits unbounded calibration covariance under the admitted unrestricted PSD class. Without an exact contraction certificate, this unit must report exact protection of the binary matrix as NOT_ESTABLISHED; it must not report a finite uniform covariance bound, zero calibration covariance, empirical immunity or physical confidence from the1e-10 acceptance. The same distinction applies to claims that calibration cross terms vanish in the *computed* operator.

For a fixed, separately justified finite Gamma, ||E Gamma E^T||_2 <= ||E||_2^2 ||Gamma||_2 is an algebraic sensitivity relation. It is not a bound delivered here because no finite Gamma cap is supplied or inferred. Likewise ||E eta|| <= ||E|| ||eta|| gives no uniform mean-error bound with unrestricted eta. Do not invent such caps, infer them from printed residuals, or transfer the old illustrative trace profiles into this unit. Rigorous numerical protection would require an exact arithmetic contraction certificate or a justified finite error/parameter domain; neither is newly required or claimed by this clarification.

## Required interpretation in consumer outputs and review

Use the existing result/report claim fields to distinguish these facts; equivalent clear field names are acceptable, and no permanent schema/registry is requested:

- Source-family support decomposition: EXACT_MODEL_IDENTITY within the declared fixed support envelope.
- Ideal K_star calibration annihilation: SYMBOLIC_MODEL_IDENTITY; exact factored definition available, exact numerical evaluation/rank not established by SVD tests.
- Stored K_hat calibration response: NUMERICAL_RESIDUAL_CHECK_ONLY, retaining the actual raw/scaled residuals and the structural mixed-zero check.
- Uniform protection of the binary matrix against unrestricted Gamma: NOT_ESTABLISHED; no finite calibration covariance bound or immunity claim.
- Apparent coefficients/tensors and working metric: NUMERICAL_SELECTED_SOURCE_OUTPUTS; empirical total covariance and all physical gates remain HOLD/UNKNOWN.

The report may say: “The support model admits an ideal calibration-annihilating functional. This run evaluates a floating surrogate and reports its full signed output and residual checks. Exact annihilation of the stored binary matrix and finite uniform protection under unrestricted calibration covariance are not established.” Avoid saying that the *computed observation* has exact immunity merely because it passed tolerance checks.

Implementation need only make provenance/math notation and result/report labels consistent. No algorithm change, threshold change, calibration cap, source replay or additional scientific computation is authorized here. Root must bind this clarification hash beside the original contract/input when issuing the actual packet/ACK. The lower worker then performs the already authorized single bounded consumer; the one already reserved independent review assesses the same scientific result with this distinction. No additional review ladder is introduced.
