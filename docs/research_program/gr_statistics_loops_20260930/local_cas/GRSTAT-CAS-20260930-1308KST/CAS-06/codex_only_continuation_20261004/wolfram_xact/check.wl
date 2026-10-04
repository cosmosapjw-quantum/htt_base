(* Blind Wolfram/xAct check of CAS-06-C03-SCALAR only. *)
ClearAll[x, pstar, alpha, s, p, d1, d2, energy, denominator];

(* xAct is loaded for the required engine/toolchain identity; no tensor claim is made. *)
Block[{$Output = {}}, Needs["xAct`xTensor`"]];
xactLoaded = MemberQ[$Packages, "xAct`xTensor`"] &&
   ValueQ[xAct`xTensor`$Version];

s = (1 + alpha)/(2 alpha);
assumptions = Element[{x, pstar, alpha}, Reals] && x > 0 && pstar > 0 &&
   0 < alpha < 1;
p = pstar Exp[s Log[x]];
d1 = D[p, x];
d2 = D[p, {x, 2}];
energy = 2 x d1 - p;
denominator = d1 + 2 x d2;

derivative1Proof = TrueQ[FullSimplify[d1 == s p/x, assumptions]];
derivative2Proof = TrueQ[FullSimplify[d2 == s (s - 1) p/x^2, assumptions]];
energyProof = TrueQ[FullSimplify[energy == (2 s - 1) p, assumptions]];
denominatorFactorProof = TrueQ[
   FullSimplify[denominator == s (2 s - 1) p/x, assumptions]];
positiveFactorsProof = TrueQ[FullSimplify[
    s > 0 && 2 s - 1 > 0 && pstar > 0 &&
     Exp[s Log[x]] > 0 && x > 0, assumptions]];
positiveDenominatorProof = denominatorFactorProof && positiveFactorsProof &&
   TrueQ[FullSimplify[denominator > 0, assumptions]];
ratioProof = positiveDenominatorProof &&
   TrueQ[FullSimplify[d1/denominator == alpha, assumptions]];

componentProof = And[xactLoaded, derivative1Proof, derivative2Proof, energyProof,
   denominatorFactorProof, positiveDenominatorProof, ratioProof];
payload = <|
   "checks" -> <|"CAS-06-C03-SCALAR" -> componentProof|>,
   "domain_assumption_diff" -> {},
   "counterexample" -> Null,
   "wolfram_version" -> System`$Version,
   "xact_xtensor_version" -> ToString[InputForm[xAct`xTensor`$Version]],
   "xact_loaded" -> xactLoaded,
   "assumptions" -> ToString[InputForm[assumptions]],
   "positive_real_power" -> ToString[InputForm[p]],
   "derived_first_derivative" -> ToString[InputForm[d1]],
   "derived_second_derivative" -> ToString[InputForm[d2]],
   "derived_denominator" -> ToString[InputForm[denominator]],
   "proofs" -> <|
     "first_derivative" -> derivative1Proof,
     "second_derivative" -> derivative2Proof,
     "energy_identity" -> energyProof,
     "denominator_factorization" -> denominatorFactorProof,
     "positive_factors" -> positiveFactorsProof,
     "positive_denominator" -> positiveDenominatorProof,
     "ratio_identity" -> ratioProof|>
   |>;
WriteString[$Output, ExportString[payload, "RawJSON"] <> "\n"];
Exit[If[componentProof, 0, 1]];
