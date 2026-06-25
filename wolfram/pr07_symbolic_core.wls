(* PR07 symbolic theorem repair. Returns a JSON-serializable Association. *)
ClearAll["Global`*"];
$Assumptions = H > 0 && kap > 0 && -1 < b1 < 1 && -1 < b2 < 1;
eta = DiagonalMatrix[{-1, 1, 1, 1}];
stf[m_] := Simplify[(m + Transpose[m])/2 - IdentityMatrix[3] Tr[(m + Transpose[m])/2]/3];

(* Physical vs normalized anisotropic stress. *)
pi = {{p11, p12, p13}, {p12, p22, p23}, {p13, p23, -p11-p22}};
PiN = Simplify[kap pi/(3 H^2)];
sigma = {{s11, s12, s13}, {s12, s22, s23}, {s13, s23, -s11-s22}};
rhsPhysical = stf[-3 H sigma + kap pi];
rhsNormalized = stf[-3 H sigma + 3 H^2 PiN];

(* Non-collinear boost composition: exact Lorentz, nonadditive velocity. *)
bx[b_] := {{1/Sqrt[1-b^2], b/Sqrt[1-b^2], 0, 0},
           {b/Sqrt[1-b^2], 1/Sqrt[1-b^2], 0, 0},
           {0,0,1,0},{0,0,0,1}};
by[b_] := {{1/Sqrt[1-b^2], 0, b/Sqrt[1-b^2], 0},
           {0,1,0,0},
           {b/Sqrt[1-b^2],0,1/Sqrt[1-b^2],0},
           {0,0,0,1}};
L = Simplify[bx[b1].by[b2]];
vel = Simplify[{L[[2,1]],L[[3,1]],L[[4,1]]}/L[[1,1]]];

(* First-jet counterexample in Minkowski at x=0. *)
(* u_const=(1,0,0,0); u_grad=gamma(x)(1,alpha x,0,0). *)
gam[x_] := 1/Sqrt[1-alpha^2 x^2];
uGrad[x_] := {gam[x], gam[x] alpha x, 0, 0};
thetaGradOrigin = Simplify[D[uGrad[x][[2]], x] /. x -> 0];

(* Radial-vorticity no-go. *)
Om = {{0,-w3,w2},{w3,0,-w1},{-w2,w1,0}};
n = {n1,n2,n3};
radialVorticity = Expand[n.Om.n];

(* Dust FLRW oracle. *)
d = 1 + 3 H0 t/2;
aD = d^(2/3);
HD = Simplify[D[aD,t]/aD];
HdotD = Simplify[D[HD,t]];

<|
  "schema" -> "htt.pr07.wolfram.symbolic_core.v1",
  "checks" -> <|
    "b_shear_physical_normalized_equivalence" -> TrueQ[Simplify[rhsPhysical-rhsNormalized] == ConstantArray[0,{3,3}]],
    "d_sigma_dot_d_pi12" -> ToString[InputForm[Simplify[D[rhsPhysical[[1,2]],p12]]]],
    "d_sigma_dot_d_Pi12" -> ToString[InputForm[Simplify[D[stf[-3 H sigma + 3 H^2 pi][[1,2]],p12]]]],
    "lorentz_error_zero" -> TrueQ[Simplify[Transpose[L].eta.L-eta] == ConstantArray[0,{4,4}]],
    "composed_velocity" -> ToString[InputForm[vel]],
    "velocity_nonadditive" -> Not[TrueQ[Simplify[vel-{b1,b2,0}] == {0,0,0}]],
    "first_jet_same_point_different_expansion" -> TrueQ[thetaGradOrigin == alpha],
    "radial_vorticity_zero" -> TrueQ[radialVorticity == 0],
    "dust_raychaudhuri" -> TrueQ[Simplify[HdotD + 3 HD^2/2] == 0],
    "dust_domain" -> "H0>0 and 1+3 H0 t/2>0"
  |>
|>
