(* CAS11-C02 v3, independent Wolfram/xAct axis.
   Frozen contract SHA-256: c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a.
   Forward target: for every n>=1, real symmetric PSD R, e in R^n,
   eps>=0, and every a, (a.e)^2 <= 2 eps (a.R.a), conclude
   e in range(R) and e.Rdagger.e <= 2 eps, with spectral MP inverse.

   Analytic derivation valid for arbitrary finite n/rank:
   R=U diag(lambda_1,...,lambda_n) U^T by the real symmetric spectral
   theorem, with lambda_i>=0. Put x=U^T e. For each lambda_i=0,
   instantiate the premise at a=U_i. Then x_i^2<=0, hence x_i=0.
   Therefore e belongs to range(R), including R=0. Put b=Rdagger e
   and q=e.Rdagger.e=Sum_{lambda_i>0} x_i^2/lambda_i>=0.
   Positive-eigenvalue coordinate identities give b.e=q and b.R.b=q.
   Instantiating the premise at a=b gives q^2<=2 eps q. If q=0,
   q<=2 eps follows from eps>=0; if q>0, divide by q. This covers
   positive definite, singular nonzero and zero R, with eps=0 or >0.
   No zero eigenvalue or eps is divided by.

   Wolfram verifies the scalar reductions below, not the spectral theorem,
   arbitrary-finite-sum lift, or universal-premise instantiation. The
   machine result is therefore INCONCLUSIVE for full contract coverage. *)
$HistoryLength = 0;
Print["ENGINE_VERSION=", $Version];
Needs["xAct`xTensor`"];
Print["XACT_XTENSOR_CONTEXT=", Context[xAct`xTensor`DefManifold]];
Clear[lam, x, eps, q];
tests = <|
 "null_eigenvalue_forces_zero_coordinate" ->
  TrueQ[Resolve[ForAll[{lam,x,eps},
    Implies[lam==0 && eps>=0 && x^2<=2 eps lam, x==0]], Reals]],
 "positive_eigenmode_pseudoinverse_identities" ->
  TrueQ[Resolve[ForAll[{lam,x},
    Implies[lam>0, (x/lam) x==x^2/lam &&
      lam (x/lam)^2==x^2/lam && x^2/lam>=0]], Reals]],
 "nonnegative_q_cancellation_including_zero" ->
  TrueQ[Resolve[ForAll[{q,eps},
    Implies[q>=0 && eps>=0 && q^2<=2 eps q, q<=2 eps]], Reals]],
 "zero_q_zero_eps_intersection" ->
  TrueQ[Resolve[ForAll[q, Implies[q>=0 && q^2<=0, q==0]], Reals]]
|>;
Print["SCALAR_CHECKS=", ExportString[Normal[tests], "RawJSON", "Compact"->True]];
If[!And @@ Values[tests], Print["SCALAR_CHECK_FAILURE"]; Quit[1]];
Print["SCALAR_REDUCTIONS_VERIFIED; FULL_UNIVERSAL_PROOF_NOT_ENGINE_CERTIFIED"];
