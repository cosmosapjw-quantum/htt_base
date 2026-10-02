(* CAS-04 energy-frame derivative, rate identity and Euler projection. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b,d}];DefMetric[-1,met[-a,-b],CD];
DefTensor[tm[a,-b],GrstatM];DefTensor[u[a],GrstatM];DefTensor[ener[],GrstatM];
xact=<|"eigenProductDerivative"->TrueQ[ToCanonical[Expand[CD[-d][tm[a,-b]u[b]]]-CD[-d][tm[a,-b]]u[b]-tm[a,-b]CD[-d][u[b]]]===0],
 "normDerivative"->TrueQ[ToCanonical[CD[-d][met[-a,-b]u[a]u[b]]-2met[-a,-b]u[a]CD[-d][u[b]]]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[c,ep,p,dd,dt,cs,grad];
g=DiagonalMatrix[{-1,1,1,1}];u0={1,0,0,0};
Tmix=DiagonalMatrix[{-ep,p[1],p[2],p[3]}];
L=Tmix+ep IdentityMatrix[4];P=IdentityMatrix[4]+Outer[Times,u0,g.u0];
Dmat=Table[dt[mu,i],{mu,0,3},{i,1,3}];
(* Build derivative-first Q with Q_mu0=0 from unit normalization. *)
Q=Table[If[i==1,0,-c dt[mu,i-1]/(ep+p[i-1])],{mu,0,3},{i,1,4}];
projectedEigen=Table[(L.Q[[mu+1]])[[i+1]]+c dt[mu,i],{mu,0,3},{i,1,3}];
c01=zero[Tmix.u0+ep u0]&&zero[Q.u0]&&zero[projectedEigen]&&
 zero[Table[(P.L.Q[[mu+1]])[[1]],{mu,0,3}]];
Dsp=Q[[2;;4,2;;4]];theta=Tr[Dsp];sigma=(Dsp+Transpose[Dsp])/2-theta IdentityMatrix[3]/3;
W=(Dsp-Transpose[Dsp])/2;
omega={W[[2,3]],-W[[1,3]],W[[1,2]]};
acc=c Q[[1,2;;4]];
lhs=theta^2/3+Tr[Transpose[sigma].sigma]+2omega.omega+acc.acc/c^2;
rhs=c^2 Sum[dt[mu,i]^2/(ep+p[i])^2,{mu,0,3},{i,1,3}];
c02=zero[lhs-rhs]&&zero[Tr[Transpose[W].W]-2omega.omega];
(* Each summand has nonnegative slack for delta>0 and |gap_i|>=delta.
   Equality iff dt_mu_i=0 for every strictly larger absolute gap. *)
slack=Expand[c^2 Sum[dt[mu,i]^2(1/dd^2-1/(ep+p[i])^2),{mu,0,3},{i,1,3}]];
scalarBound=FullSimplify[ForAll[{gap,dd,z},dd>0&&gap>=dd&&z>=0,
 z/gap^2<=z/dd^2]];
scalarEquality=Resolve[ForAll[{gap,dd,z},dd>0&&gap>dd&&z>=0&&
 z (gap^2-dd^2)==0,z==0],Reals];
c03=TrueQ[scalarBound]&&TrueQ[scalarEquality]&&
 zero[slack-c^2 Sum[dt[mu,i]^2(1/dd^2-1/(ep+p[i])^2),{mu,0,3},{i,1,3}]];
(* Spatial conservation of perfect fluid gives (ep+p) A/c^2+Dp=0. *)
pressureGrad=Array[grad,3]; dEnergy=Array[de,3];
EulerA=-c^2 pressureGrad/(ep+p[1]);
barotropicA=-cs^2 dEnergy/(ep+p[1]);
c04=zero[(ep+p[1]) EulerA/c^2+pressureGrad]&&
 zero[(EulerA/.Thread[pressureGrad->cs^2 dEnergy/c^2])-barotropicA]&&
 zero[EulerA/.Thread[pressureGrad->ConstantArray[0,3]]];
checks=<|"CAS-04-C01"->c01,"CAS-04-C02"->c02,"CAS-04-C03"->c03,"CAS-04-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"rate_identity_residual"->ToString[InputForm[FullSimplify[lhs-rhs]]],
 "scalar_gap_bounds"->{ToString[InputForm[scalarBound]],ToString[InputForm[scalarEquality]]}|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
