(* xAct canonicalization gates for PR07. *)
Needs["xAct`xTensor`"];
DefManifold[M3, 3, {a,b,c,d,e,f}];
DefMetric[1, h[-a,-b], D3, PrintAs -> "h"];
DefTensor[n[a], M3, PrintAs -> "n"];
DefTensor[omega[-a,-b], M3, Antisymmetric[{-a,-b}], PrintAs -> "omega"];
DefTensor[S[-a,-b], M3, Symmetric[{-a,-b}], PrintAs -> "S"];

radial = ToCanonical[n[a] omega[-a,-b] n[b]];
symAnti = ToCanonical[S[-a,-b] omega[a,b]];

<|
  "schema" -> "htt.pr07.xact.abstract.v1",
  "xact_version" -> ToString[InputForm[$Version]],
  "radial_vorticity_expression" -> ToString[InputForm[radial]],
  "radial_vorticity_zero" -> TrueQ[radial === 0],
  "symmetric_antisymmetric_contraction_zero" -> TrueQ[symAnti === 0]
|>
