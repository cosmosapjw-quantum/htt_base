# CAS15-C03 arbitrary-data least-squares perturbation synthesis

Owner htt; transfer source none; scientific admission HOLD. New strength-based successor; historical #497 CAS_CONFLICT and its frozen validator are unchanged. Separate independent review: PASS_SCOPED_SUCCESSOR_REVIEW, no blocking findings; exact scope and identities in review/REVIEW.md.

Let M,Mhat be symmetric real 3×3 matrices, W and What skew, R=[M,W], and Rhat an arbitrary real 3×3 matrix. Suppose epsR,epsM,Wstar≥0, ‖Rhat−R‖F≤epsR, ‖Mhat−M‖op≤epsM, ‖W‖F≤Wstar, the minimum pairwise gap deltahat of Mhat is positive, and What is a global least-squares minimizer over the skew subspace. A norm minimizer and squared-norm minimizer are equivalent; no exact-fit premise is used. The following full mathematical conclusions are DERIVED from the explicit arguments and lemmas below:

1. ‖What−W‖F ≤ (epsR+2 epsM Wstar)/deltahat.
2. For decreasingly ordered eigenvalues at the same three indices, |hatlambda_i−lambda_i|≤epsM, and deltahat≥delta−2 epsM.

| Conclusion | Proof/source | Exact evidence |
|---|---|---|
| Frobenius norm and genuine skew domain | Frobenius.frobenius_norm_sq, skew | FORMALLY_CHECKED nine-coordinate Euclidean space; not default matrix norm |
| Arbitrary-data projection and contraction | unchanged Projection.least_squares_projection/error_contraction; concrete Frobenius.skew_least_squares_contraction and squared variant | FORMALLY_CHECKED, genuine minimizer definition, no exact fit |
| Residual identity | Frobenius.residual_identity | FORMALLY_CHECKED, Rhat−[Mhat,W]=(Rhat−R)−[Mhat−M,W] |
| Mixed norm estimate | Mixed.norm_flat_comm_le | FORMALLY_CHECKED, all real matrices, exact Euclidean induced operator norm |
| Interface correspondence and error bound from coercivity | Synthesis.comm_bridge, perturbation_given_coercivity | FORMALLY_CHECKED, coercivity supplied explicitly at this formal boundary |
| Arbitrary rotated skew coercivity from spectral gap | SPECTRAL_NOTES.md: orthogonal diagonalization, skew preservation, trace/Frobenius invariance, squared diagonal coefficients | DERIVED; full general bridge not yet a Lean theorem |
| Ordered eigenvalue matching | SPECTRAL_NOTES.md: top-k and bottom-(4−k) spans intersect; Rayleigh bound for k=1,2,3 in both directions | DERIVED; matching is not a formal premise proved by the gap helper |
| Rayleigh error / ordered-gap consequence | Spectral.rayleigh_error_le, ordered_gap_from_pointwise_matches | FORMALLY_CHECKED, latter explicitly conditional on pointwise matches |

For the first conclusion, write A(X)=[Mhat,X] from the skew Frobenius subspace to the full Frobenius space. Genuine least-squares minimality yields A(What)=P Rhat, P the orthogonal range projection. Since A(W) belongs to the range, A(What−W)=P(Rhat−A(W)). Projection contraction bounds its norm by the exact residual (Rhat−R)−[Mhat−M,W]. The mixed bound and triangle inequality bound this by epsR+2 epsM Wstar. Rotated coercivity (proved analytically in SPECTRAL_NOTES.md) gives deltahat‖What−W‖F≤‖A(What−W)‖F. Divide only by positive deltahat. This is a full analytical derivation under the adopted inputs; the Lean synthesis stops exactly at the explicit coercivity hypothesis. It is not a fully formal arbitrary-rotated-matrix theorem.

The second conclusion follows from the explicit eigenspace intersection argument, not an assumed Weyl bound or an arbitrary eigenvalue permutation. Repeated eigenvalues are allowed in the matching estimate; a zero deltahat prevents the inverse error bound. The lower bound delta−2epsM may be negative and does not by itself imply positivity. General Rhat may have diagonal/antisymmetric components outside the commutator range; these remain least-squares residuals, never silently fitted. Exact-data epsR=epsM=0 gives What=W when deltahat>0. Wstar=0 gives W=0; no division by any epsilon or Wstar occurs.

New actual integration execution: `python …/ls_projection_continuation_v1_20261008/build.py`, logs `build_logs/20261008T123443937379Z`. Version, unchanged Projection minimal dependency compilation, Frobenius, Mixed, Spectral, Synthesis each exit 0. Lean4.31.0/mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. Synthesis axioms only propext/Classical.choice/Quot.sound; no sorryAx. New author first failures retained in respective *_logs, original Projection failed attempt preserved. No full historical CAS engine campaigns rerun; new inequalities/interfaces kernel checked.

Authors shared named interfaces/results; this is collaboration, not independent rediscovery. Requested native settings all gpt-6-sol/high. Matching session_meta/turn_context confirms each author model/effort/cwd: Frobenius session 01a11b7a-3a29-7772-98b3-46087720fb0d turn 01a11b7a-3ae7-7ff1-bc6a-7c69ec77c53e; Mixed session 01a11b7a-6a47-7583-b74c-a182f9b9823a turn 01a11b7a-6af8-7aa0-84b1-a354f8f8f928; Spectral session 01a11b7c-672e-7d93-b10a-217b896246e5 turn 01a11b7c-695f-7f22-9596-453ac1eac82f. Root integration author observed gpt-6.1-sol/medium, requested UNKNOWN. These are model observations, not independent reviews.

UNRESOLVED formal scope: full orthogonal-conjugation/Frobenius coercivity and ordered-eigenvalue dimension-intersection bridges in Lean; one universal fully formal theorem over arbitrary symmetric matrices. No historical four-axis adjudication eligibility or scientific admission follows. Separate independent review judged the full mathematical derivation and exact conditional formal boundary valid. Two P3 documentation/evidence findings were closed without proof changes. Reviewer requested and observed gpt-6-astra/ultra; fresh reviewer build all six steps exit0, 16 standard-only axiom outputs.
