(* CAS-07 conditional Jacobi majorant and finite difference envelopes. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[Screen,2,{a,b}];DefMetric[1,hs[-a,-b],DS];
DefTensor[jac[-a,-b],Screen];DefTensor[ropt[-a,-b],Screen];
xact=<|"screenMetric"->TrueQ[ToCanonical[ContractMetric[hs[a,b]hs[-a,-b]]-2]===0],
 "screenSymTrace"->TrueQ[ToCanonical[(jac[-a,-b]+jac[-b,-a])hs[a,b]-2jac[-a,-b]hs[a,b]]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[kc,s,t,eta,sl,lo,hi,dA,H0,c,M2,Z,Z0,EL];
f=Sinh[Sqrt[kc] s]/Sqrt[kc];
integral=Integrate[(s-t) Sinh[Sqrt[kc] t]/Sqrt[kc],{t,0,s},
 Assumptions->kc>0&&s>=0];
c01=zero[Limit[f,s->0]]&&zero[Limit[D[f,s],s->0]-1]&&
 zero[D[f,{s,2}]-kc f]&&zero[kc integral-(f-s)]&&
 zero[Limit[f,kc->0]-s];
(* Supplied operator majorization yields singular values in [lo,hi].
   Its Volterra derivation is an analytic prerequisite, outside CAS. *)
lo=s(1-eta);hi=s(1+eta);
detConsequence=Resolve[ForAll[{s,eta,sv1,sv2},
 s>0&&0<=eta<1&&lo<=sv1<=hi&&lo<=sv2<=hi,
 lo^2<=sv1 sv2<=hi^2],Reals];
orientation=zero[Det[s IdentityMatrix[2]]-s^2]&&
 TrueQ[FullSimplify[lo>0,Assumptions->s>0&&0<=eta<1]];
c02=TrueQ[detConsequence]&&orientation;
(* Let e=Z-Z0-H0 s/c; |e|<=M2 s^2/2 is supplied. Since
   |s-dA|<=s eta, the triangle envelope follows exactly. *)
errorEnvelope=M2 s^2/2+Abs[H0]s eta/c;
fd2=M2 dA^2/(2(1-EL)^2)+Abs[H0]dA EL/(c(1-EL));
fd2Sub=FullSimplify[(errorEnvelope/.{s->dA/(1-EL),eta->EL})-fd2];
fd3=c M2 s/(2(1-eta))+Abs[H0]eta/(1-eta);
fd3Raw=c M2 s^2/(2dA)+Abs[H0]s eta/dA;
fd3Sub=FullSimplify[(fd3Raw/.dA->s(1-eta))-fd3];
intercept=zero[c(Z-1)/dA-(c(Z-Z0)/dA+c(Z0-1)/dA)];
c03=zero[fd2Sub]&&zero[fd3Sub]&&intercept&&
 TrueQ[FullSimplify[ForAll[{s,eta},s>0&&0<=eta<1,s eta/(s(1-eta))>=0]]];
checks=<|"CAS-07-C01"->c01,"CAS-07-C02"->c02,"CAS-07-C03"->c03|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"majorant_integral"->ToString[InputForm[integral]],
 "determinant_consequence"->ToString[InputForm[detConsequence]],
 "FD2_residual"->ToString[InputForm[fd2Sub]],"FD3_residual"->ToString[InputForm[fd3Sub]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
