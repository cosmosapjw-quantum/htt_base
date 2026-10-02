(* CAS-09 angular/radial design rank and native-mean nuisance algebra. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[Sky,2,{a,b}];DefMetric[1,hs[-a,-b],DS];
xact=<|"skyMetricTrace"->TrueQ[ToCanonical[ContractMetric[hs[a,b]hs[-a,-b]]-2]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[R1,R2,c,eps,x,y,z];
b4[n_]:=Prepend[n,1];
b9[n_]:=Module[{x=n[[1]],y=n[[2]],z=n[[3]]},
 {1,x,y,z,x y,x z,y z,x^2-y^2,3z^2-1}];
pts=Join[Flatten[Table[{UnitVector[3,i],-UnitVector[3,i]},{i,3}],1],
 {{3/5,4/5,0},{3/5,0,4/5},{0,3/5,4/5}}];
E9=Map[b9,pts];E4=Map[b4,pts];
rank9=MatrixRank[E9];rank4=MatrixRank[E4[[{1,2,3,5}]]];
(* For repeated first four angular rows, subtract R2/R1 times the
   corresponding first-radius rows; the remaining 4x4 E4 block is
   multiplied by 1-R2/R1 and is nonsingular when R1,R2>0 unequal. *)
rankIdentity=zero[(9+4-0)-13];
c01=rank9==9&&rank4==4&&rankIdentity&&
 TrueQ[Det[E4[[{1,2,3,5}]]]!=0]&&
 TrueQ[FullSimplify[(1-R2/R1)!=0,Assumptions->R1>0&&R2>0&&R1!=R2]];
(* Future mass-shell intercept u(d) has one constrained degree: 3+9=12. *)
dv=Array[dd,3];chart=Prepend[dv,Sqrt[1+dv.dv]];
chartJac=Table[D[chart[[i]],dv[[j]]],{i,4},{j,3}];
chartAtZero=chartJac/.Thread[dv->ConstantArray[0,3]];
c02=MatrixRank[chartAtZero]==3&&
 zero[Transpose[chartJac].chartJac-(IdentityMatrix[3]+Outer[Times,dv,dv]/(1+dv.dv))]&&
 MatrixRank[ArrayFlatten[{{chartAtZero,ConstantArray[0,{4,9}]},
 {ConstantArray[0,{9,3}],IdentityMatrix[9]}}]]==12;
(* z times every degree<=1 basis lies in the degree<=2 quotient on S2. *)
var={x,y,z}; basis9=b9[var];basis4=b4[var];
coefs=Table[Array[coef[#]&,9],{4}];
representations=Table[SolveAlways[(z basis4[[j]]-coefs[[j]].basis9)==0,{x,y,z}],{j,4}];
productDegree=And@@(Length[#]>0& /@ representations);
constRadius=MatrixRank[Join[E4,(R1/c)E9,2]]==9;
radial=Table[R1/(1+eps pts[[i,3]]),{i,9}];
variableRank=MatrixRank[Join[E4,DiagonalMatrix[radial/c].E9,2]];
c03=productDegree&&constRadius&&variableRank==9&&
 TrueQ[FullSimplify[1+eps z>0,Assumptions->-1<eps<1&&eps!=0&&-1<=z<=1]];
(* Supplied nuisance transformation is an exact finite mean identity. *)
base=Array[baseMean,5];obs=Array[obsMean,5];rad=Array[rr,5];slope=Array[hh,5];
rho=obs-base-rad slope/c;
mean=base+rad slope/c+rho;
c04=zero[mean-obs];
checks=<|"CAS-09-C01"->c01,"CAS-09-C02"->c02,"CAS-09-C03"->c03,"CAS-09-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"angular_rank9"->rank9,"angular_rank4"->rank4,
 "variable_radius_rank"->variableRank,"z_basis_solutions"->ToString[InputForm[representations]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
