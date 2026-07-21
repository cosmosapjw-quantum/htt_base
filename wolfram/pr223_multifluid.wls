Needs["xAct`xTensor`"]; Print["XACT_LOAD_OK"];
streams = {{1, {v, 0, 0}}, {1, {-v, 0, 0}}};
F = Total[(#[[1]] #[[2]]) & /@ streams];
KK = Total[(#[[1]] Outer[Times, #[[2]], #[[2]]]) & /@ streams];
tr = Tr[KK];
PiT = KK - (tr/3) IdentityMatrix[3];
Pi3 = Simplify[3 PiT /. v -> 1];
Print["first_moment=", Simplify[F]];
Print["trace_K=", Simplify[tr]];
Print["aniso_3Pi_diag=", Diagonal[Pi3]];
If[Simplify[F] === {0, 0, 0} && Simplify[tr] =!= 0 && Diagonal[Pi3] === {4, -2, -2} && Tr[Pi3] === 0,
   Print["PR223_WOLFRAM_PASS"], Print["PR223_WOLFRAM_FAIL"]];
Exit[0];
