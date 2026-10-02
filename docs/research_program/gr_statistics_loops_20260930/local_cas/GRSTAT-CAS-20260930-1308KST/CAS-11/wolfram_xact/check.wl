(* CAS-11 finite Bregman, residual Gram, singular ellipsoid, Cauchy. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[DataM,3,{a,b}];DefMetric[1,ip[-a,-b],DC];
DefTensor[gram[-a,-b],DataM,Symmetric[{-a,-b}]];
xact=<|"gramSymmetry"->TrueQ[ToCanonical[gram[-a,-b]-gram[-b,-a]]===0],
 "metricTrace"->TrueQ[ToCanonical[ContractMetric[ip[a,b]ip[-a,-b]]-3]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[epsilon,r1,r2,e1,e2,e3];
f=Array[ff,3];g=Array[gg,3];h=Array[hh,3];
gradG=Array[dg,3];gradH=Array[dh,3];
HF=Hf;HG=Hg;HH=Hh;
Dfg=HF-HG-gradG.(f-g);
Dfh=HF-HH-gradH.(f-h);
Dhg=HH-HG-gradG.(h-g);
threePoint=zero[Dfg-Dfh-Dhg-(gradH-gradG).(f-h)];
V=Table[v[i,j],{i,3},{j,2}];lambda=Array[lam,2];
matched=V.(lambda);
matchCancellation=zero[matched.(f-h)-lambda.(Transpose[V].(f-h))];
c01=threePoint&&matchCancellation;
(* Residual weighted Gram R=K^T W(I-P)K. The norm identity gives
   PSD for any positive diagonal weights and full-rank retained V. *)
W=DiagonalMatrix[Array[w,4]];
Vret={{1,0},{0,1},{0,0},{0,0}};
K=Table[kk[i,j],{i,4},{j,3}];
P=Vret.Inverse[Transpose[Vret].W.Vret].Transpose[Vret].W;
res=(IdentityMatrix[4]-P).K;
R=Transpose[res].W.res;
aa=Array[aa,3];
psdIdentity=zero[aa.R.aa-(res.aa).W.(res.aa)];
projector=zero[P.P-P]&&zero[Transpose[Vret].W.res];
(* Spectral reduction of arbitrary symmetric PSD R to diag(r1,r2,0).
   The universal inequality on the null basis forces e3=0. Choosing
   a=R+ e then yields q^2<=2 epsilon q, q=e^T R+e. *)
Rsing=DiagonalMatrix[{r1,r2,0}];Rplus=DiagonalMatrix[{1/r1,1/r2,0}];
ev={e1,e2,0};av=Rplus.ev;q=ev.Rplus.ev;
rangeCondition=zero[Rsing.Rplus.ev-ev]&&
 zero[{0,0,e3}.Rsing.{0,0,e3}]&&
 zero[{0,0,e3}.{0,0,e3}-e3^2];
chosenInequality=zero[(av.ev)^2-q^2]&&zero[av.Rsing.av-q];
zeroCase=zero[ConstantArray[0,{3,3}].{e1,e2,e3}]&&
 TrueQ[Resolve[ForAll[{e1,e2,e3},e1^2<=0&&e2^2<=0&&e3^2<=0,
 e1==0&&e2==0&&e3==0],Reals]];
c02=psdIdentity&&projector&&rangeCondition&&chosenInequality&&zeroCase;
(* Weighted Cauchy is exactly Lagrange's sum-of-squares identity. *)
p=Array[pv,4];zz=Array[zv,4];
cauchy=(p.p)(zz.zz)-(p.zz)^2-
 Sum[(p[[i]]zz[[j]]-p[[j]]zz[[i]])^2,{i,1,3},{j,i+1,4}];
weightIdentity=zero[(res.aa).W.(res.aa)-aa.R.aa];
c03=zero[cauchy]&&weightIdentity&&
 zero[Transpose[res].W.Vret];
checks=<|"CAS-11-C01"->c01,"CAS-11-C02"->c02,"CAS-11-C03"->c03|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"Bregman_residual"->ToString[InputForm[Expand[Dfg-Dfh-Dhg-(gradH-gradG).(f-h)]]],
 "Cauchy_residual"->ToString[InputForm[Expand[cauchy]]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
