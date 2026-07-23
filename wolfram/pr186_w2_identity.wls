(* PR-186 W^2 convention identity, Wolfram + xAct-loaded kernel *)
Needs["xAct`xTensor`"];
Print["XACT_LOAD_OK"];
(* General spatial antisymmetric 3x3 vorticity tensor *)
a=.;b=.;c=.;H=.;B=.;
A = {{0, a, b}, {-a, 0, c}, {-b, -c, 0}};
tensorNorm = Simplify[Total[Flatten[A*A]]];       (* A_ij A_ij *)
eps = LeviCivitaTensor[3];
w = Table[(1/2) Sum[eps[[i,j,k]] A[[j,k]], {j,3},{k,3}], {i,3}];
vecNorm = Simplify[w.w];
idOK = Simplify[tensorNorm - 2 vecNorm] === 0;
W2reg = Simplify[tensorNorm/(6 H^2)];
W2vec = Simplify[vecNorm/(3 H^2)];
regEqVec = Simplify[W2reg - W2vec] === 0;
wrongRatio = Simplify[(vecNorm/H^2)/W2reg];
Theta = 3 H;
W2max = Simplify[(B Theta)^2/(6 H^2)];
ceilOK = Simplify[W2max - (3/2) B^2] === 0;
Print["tensorNorm=", tensorNorm];
Print["vecNorm=", vecNorm];
Print["identity_A_eq_2w=", idOK];
Print["W2reg=", W2reg];
Print["reg_eq_vecform=", regEqVec];
Print["wrong_over_right=", wrongRatio];
Print["ceiling_eq_three_halves=", ceilOK];
If[idOK && regEqVec && wrongRatio === 3 && ceilOK, Print["PR186_WOLFRAM_PASS"], Print["PR186_WOLFRAM_FAIL"]];
Exit[0];
