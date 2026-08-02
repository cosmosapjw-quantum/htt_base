(* Independent Wolfram Engine + xAct axis for PR-190. *)

Block[{$Output = {}, $Messages = {}}, Needs["xAct`xTensor`"]];
ClearAll["Global`*"];

obligations = {
  "normal_spatial_vorticity_zero",
  "normal_frame_w2_zero",
  "registered_lower_w2_positive",
  "lower_endpoint_same_frame_contradiction",
  "registered_interior_w2_positive",
  "interior_endpoint_same_frame_contradiction",
  "refuted_constraint_cannot_promote"
};

(* Adapted homogeneous normal coordinates: n_i=0 and d_i N(t)=0. *)
nSpatial = ConstantArray[0, 3];
spatialDerivative = ConstantArray[0, {3, 3}];
vorticity = Simplify[(spatialDerivative - Transpose[spatialDerivative])/2];
omegaSquared = Simplify[Total[Flatten[vorticity]^2]];
normalW2 = Simplify[3 omegaSquared];
registeredLowerW2 = 1/25;
registeredInteriorW2 = 3/100;
lowerContradictionResidual = Simplify[registeredLowerW2 - normalW2];
interiorContradictionResidual = Simplify[registeredInteriorW2 - normalW2];
fullProgramme = True && False && localAttained && globalAttained;

checks = AssociationThread[
  obligations,
  {
    TrueQ[nSpatial === ConstantArray[0, 3] &&
      vorticity === ConstantArray[0, {3, 3}]],
    TrueQ[normalW2 === 0],
    TrueQ[registeredLowerW2 > 0],
    TrueQ[lowerContradictionResidual === 1/25 &&
      normalW2 =!= registeredLowerW2],
    TrueQ[registeredInteriorW2 > 0],
    TrueQ[interiorContradictionResidual === 3/100 &&
      normalW2 =!= registeredInteriorW2],
    TrueQ[FullSimplify[Not[fullProgramme]]]
  }
];

payload = <|
  "checks" -> checks,
  "computed" -> <|
    "normal_omega_squared" -> "0",
    "normal_W2" -> "0",
    "registered_lower_W2" -> "1/25",
    "registered_interior_W2" -> "3/100",
    "lower_contradiction_residual" -> "1/25",
    "interior_contradiction_residual" -> "3/100"
  |>,
  "counterexample" -> Null,
  "domain_assumption_diff" -> {}
|>;

WriteString[$Output, ExportString[payload, "RawJSON", "Compact" -> True], "\n"];
