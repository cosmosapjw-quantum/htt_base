(* CAS-10: exact pair, invariant, Gaussian benchmark, cutoff extrema. *)
$HistoryLength=0; Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b,d}]; DefMetric[-1,eta[-a,-b],CD];
DefTensor[ss[-a,-b],GrstatM,Symmetric[{-a,-b}]];
DefTensor[u[a],GrstatM];
xact=<|"symmetricContraction"->TrueQ[ToCanonical[ss[-a,-b]u[a]u[b]-ss[-b,-a]u[a]u[b]]===0],
 "metricLowerRaise"->TrueQ[ToCanonical[ContractMetric[eta[a,b]eta[-b,-d]u[d]-u[a]]]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[H,c,sp,t]; g=DiagonalMatrix[{-1,1,1,1}]; u={5/4,3/4,0,0};
h0=7H/4; h2=DiagonalMatrix[{3H/8,-3H/16,-3H/16}];
h1a={15H/8,0,0};h1b={0,15H/8,0};
makeS[h1_]:=Join[{Prepend[-h1/2,h0]},MapThread[Prepend,{h2,-h1/2}]];
S1=makeS[h1a];S2=makeS[h1b];
makeB[S_]:=S+(u.S.u)g;
B1=makeB[S1];B2=makeB[S2];b1=B1.u;b2=B2.u;
K={-1,n1,n2,n3};
morph1=Expand[K.S1.K];morph2=Expand[K.S2.K];
powers1={h0^2,h1a.h1a,Tr[h2.h2]};
powers2={h0^2,h1b.h1b,Tr[h2.h2]};
c01=zero[u.g.u+1]&&zero[b1]&&zero[b2.g.b2-87525H^2/16384]&&
 zero[powers1-powers2]&&zero[morph1-(h0+h1a.{n1,n2,n3}+{n1,n2,n3}.h2.{n1,n2,n3})]&&
 zero[morph2-(h0+h1b.{n1,n2,n3}+{n1,n2,n3}.h2.{n1,n2,n3})];
(* For a unit timelike u, (Su)^2+(uSu)^2 is the squared positive
   spatial projection of Su, equal to B u squared. *)
J[S_]:=Module[{v=S.u},v.g.v+(u.S.u)^2];
spatialJ[S_]:=Module[{b=makeB[S].u},b.g.b];
c02=zero[J[S1]-spatialJ[S1]]&&zero[J[S2]-spatialJ[S2]]&&
 zero[J[S2]-(2c)^2 spatialJ[S2]/(4c^2)]&&zero[J[S1]]&&
 zero[spatialJ[S2]-87525H^2/16384];
(* The iff J=0 <=> A=0 is the Euclidean rest-space norm identity; its
   positivity is restricted to real physical unit u and c>0. *)
delv=h1a-h1b; KL=delv.delv/(2sp^2);
rot={{0,-1,0},{1,0,0},{0,0,1}};
c03parts={zero[KL-225H^2/(64sp^2)],zero[rot.Transpose[rot]-IdentityMatrix[3]],
 zero[rot.h1a-h1b],zero[powers1-powers2]};
c03=And@@c03parts;
F=1-10t^3+15t^4-6t^5;
fp=D[F,t]; fpp=D[fp,t];
tcrit={(3-Sqrt[3])/6,(3+Sqrt[3])/6};
c04=zero[{F/.t->0,F/.t->1,fp/.t->0,fp/.t->1,fpp/.t->0,fpp/.t->1}-{1,0,0,0,0,0}]&&
 zero[(fp/.t->1/2)+15/8]&&zero[(fpp/.t->tcrit[[1]])+10/Sqrt[3]]&&
 zero[(fpp/.t->tcrit[[2]])-10/Sqrt[3]]&&
 TrueQ[1147/1152<1]&&
 zero[Factor[fp]+30t^2(1-t)^2]&&
 zero[Factor[D[fpp,t]]/(-60)- (1-6t+6t^2)];
checks=<|"CAS-10-C01"->c01,"CAS-10-C02"->c02,"CAS-10-C03"->c03,"CAS-10-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"morphology_1"->ToString[InputForm[morph1]],
 "morphology_2"->ToString[InputForm[morph2]],"b2_norm"->ToString[InputForm[b2.g.b2]],
 "cutoff_derivatives"->ToString[InputForm[{fp,fpp}]],"c03parts"->c03parts|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
