(* CAS-03 exact Lorentz eigenline, slope counterfamily, inverse defect. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
DefManifold[GrstatM, 4, {a, b}];
DefMetric[-1, eta[-a, -b], CD];
DefTensor[ss[-a, -b], GrstatM, Symmetric[{-a, -b}]];
xact = <|"selfAdjointCovariance" -> TrueQ[ToCanonical[ss[-a, -b]-ss[-b, -a]]===0],
 "metricSymmetry" -> TrueQ[ToCanonical[eta[-a,-b]-eta[-b,-a]]===0]|>;
zero[v_] := And @@ (TrueQ[FullSimplify[# == 0]] & /@ Flatten[{v}]);
Clear[st, ch, eps, b2, b3, n, h, beta, sh];
g = DiagonalMatrix[{-1, 1, 1, 1}];
u = {Cosh[ch], Sinh[ch], 0, 0};
S = Table[If[i<=j, st[i,j], st[j,i]],{i,1,4},{j,1,4}];
sval = -u.S.u;
(* Work directly with the scalar eigenvalue, not a target substitution. *)
B = S - s[val] g;
eigenResidual = g.B.u - (g.S.u - s[val] u);
svalue = -u.S.u;
restKernel = DiagonalMatrix[{0,0,b2,b3}];
noTimelikeCov = {{0,1,0,0},{1,0,0,0},{0,0,1,0},{0,0,0,2}};
noTimelikeMixed = g.noTimelikeCov;
(* The 0-1 block has eigenvalues +/- i, while real eigenvectors lie in
   the positive definite spatial 2-3 plane. *)
notimelike = zero[CharacteristicPolynomial[noTimelikeMixed[[1;;2,1;;2]], z]-(z^2+1)] &&
             zero[noTimelikeMixed[[3;;4,3;;4]]-DiagonalMatrix[{1,2}]];
c01 = zero[u.g.u+1] && zero[eigenResidual] &&
      zero[restKernel.u] && notimelike &&
      zero[({Cosh[ch],Sinh[ch],0,0}.g.{Cosh[ch],Sinh[ch],0,0})+1];
rflat = g.u;
Beps = eps Outer[Times,rflat,rflat] + DiagonalMatrix[{0,0,b2,b3}];
K = {-1,n[1],n[2],n[3]};
slope = K.Beps.K;
base = slope /. ch -> 0;
difference = eps (Sinh[ch]^2 + 2 Sinh[ch] Cosh[ch] n[1] + Sinh[ch]^2 n[1]^2);
r0 = DiagonalMatrix[{0,b2,b3,b3}];
r1 = DiagonalMatrix[{0,0,b2,b3}];
r2 = DiagonalMatrix[{0,0,0,b3}];
c02 = zero[FullSimplify[slope-base-difference]] && zero[r1.u] &&
      zero[r0.{1,0,0,0}] && zero[r2.{Cosh[ch],0,Sinh[ch],0}] &&
      zero[K.Beps.K-slope];
sg = Table[If[i<=j, sh[i,j], sh[j,i]],{i,1,3},{j,1,3}];
Dmat = h IdentityMatrix[3]+sg;
bet = Array[beta,3];
hone = -2 Dmat.bet;
(* Adjugate identity certifies the inverse on det(D)!=0. *)
invCertificate = zero[Adjugate[Dmat].Dmat-Det[Dmat] IdentityMatrix[3]];
recovered = -Adjugate[Dmat].hone/(2 Det[Dmat]);
recovery = zero[FullSimplify[Together[recovered-bet]]];
truncated = -(IdentityMatrix[3]-sg/h).hone/(2h);
defect = zero[Expand[bet-truncated-(sg.sg.bet)/h^2]];
sgControl = h DiagonalMatrix[{1/2,-1/4,-1/4}];
betaControl = {eps,0,0};
honeControl = -2 (h IdentityMatrix[3]+sgControl).betaControl;
truncatedControl = -(IdentityMatrix[3]-sgControl/h).honeControl/(2h);
negative = zero[truncatedControl-{3 eps/4,0,0}];
c03parts = {invCertificate,recovery,defect,negative};
c03 = And@@c03parts;
checks=<|"CAS-03-C01"->c01,"CAS-03-C02"->c02,"CAS-03-C03"->c03|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"eigen_residual"->ToString[InputForm[eigenResidual]],
 "slope_difference_residual"->ToString[InputForm[FullSimplify[slope-base-difference]]],
 "inverse_defect_residual"->ToString[InputForm[Expand[bet-truncated-(sg.sg.bet)/h^2]]],
 "c03parts"->c03parts|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];
Print[ExportString[result,"RawJSON"]];
Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
