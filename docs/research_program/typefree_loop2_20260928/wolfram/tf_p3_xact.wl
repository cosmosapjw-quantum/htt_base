(* One-shot Wolfram/xAct exact check. No persistent kernel. *)
Needs["xAct`xCoba`"];
DefManifold[TFM2, 4, {a, bidx, cidx, didx, eidx}];
DefChart[TFchart2, TFM2, {0, 1, 2, 3}, {x0[], x1[], x2[], x3[]}];
DefConstantSymbol[bb];
DefConstantSymbol[ll];
phi = -bb x0[]^2 - bb (x1[]^2 + x2[]^2 + x3[]^2)/2 +
  ll x0[]^2 x1[]/2;
metric = CTensor[Exp[2 phi] DiagonalMatrix[{-1, 1, 1, 1}],
  {-TFchart2, -TFchart2}];
SetCMetric[metric, TFchart2, SignatureOfMetric -> {3, 1, 0}];
cd = CovDOfMetric[metric];
zero = {x0[] -> 0, x1[] -> 0, x2[] -> 0, x3[] -> 0};
ein = Einstein[cd][[1]];
coords = {x0[], x1[], x2[], x3[]};
jet2 = Table[D[metric[[1,i,j]], coords[[k]], coords[[l]]],
  {i,4},{j,4},{k,4},{l,4}] /. zero;
dT = Table[Simplify[D[ein[[i+1,1]], coords[[mu]]] /. zero]/kap,
  {mu,4},{i,3}];
dU = Simplify[-cspeed dT/(6 bb/kap)];
kSpatial = dU[[2;;4]];
theta = Tr[kSpatial];
sigma = (kSpatial+Transpose[kSpatial])/2-theta IdentityMatrix[3]/3;
omega = (kSpatial-Transpose[kSpatial])/2;
acc = cspeed dU[[1]];
Print["VERSION=", System`$Version];
Print["XACT_RIEMANN_SIGN=", xAct`xTensor`$RiemannSign];
Print["CURVATURE_CONVENTION=[nabla_c,nabla_d]v^a=R^a_bcd v^b"];
Print["XACT_EINSTEIN_ORIGIN=", ToString[InputForm[Simplify[ein /. zero]]]];
Print["XACT_D0_G10=", ToString[InputForm[Simplify[D[ein[[2,1]], x0[]] /. zero]]]];
Print["XACT_EINSTEIN_HEAD=", Head[ein]];
Print["METRIC_2JET_LAMBDA_FREE=",FreeQ[jet2,ll]];
Print["D_T_SPATIAL_0=",ToString[InputForm[dT]]];
Print["SELECTED_ACCELERATION=",ToString[InputForm[acc]]];
Print["THETA_SIGMA_OMEGA_ZERO=", {theta===0, sigma===ConstantArray[0,{3,3}],omega===ConstantArray[0,{3,3}]}];
Print["POINT_STRESS_MIXED=",ToString[InputForm[DiagonalMatrix[{-6 bb/kap,0,0,0}]]]];
Print["POINT_GAP=",ToString[InputForm[6 bb/kap]]];
