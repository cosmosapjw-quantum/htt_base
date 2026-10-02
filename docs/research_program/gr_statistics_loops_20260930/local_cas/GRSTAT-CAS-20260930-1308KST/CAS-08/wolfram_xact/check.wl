(* CAS-08 exact projector and GLS algebra. The four named decision states
   are not specified in the permitted contract/common source. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[DataM,3,{a,b}];DefMetric[1,cm[-a,-b],DC];
DefTensor[pp[-a,-b],DataM,Symmetric[{-a,-b}]];
xact=<|"projectorSymmetryType"->TrueQ[ToCanonical[pp[-a,-b]-pp[-b,-a]]===0],
 "metricTrace"->TrueQ[ToCanonical[ContractMetric[cm[a,b]cm[-a,-b]]-3]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[c1,c2,c3,f1,f2,y1,y2,y3,b1,b2];
Cov=DiagonalMatrix[{c1,c2,c3}];
Wh=DiagonalMatrix[{1/Sqrt[c1],1/Sqrt[c2],1/Sqrt[c3]}];
Fmat={{f1,0},{0,f2},{0,0}};
(* Full-rank and rank-deficient cases explicitly; all claims are the
   Moore-Penrose projector identities on the indicated rank strata. *)
A=Wh.Fmat;
Pfull=DiagonalMatrix[{0,0,1}];
Prank1=DiagonalMatrix[{0,1,1}];
Pzero=IdentityMatrix[3];
pseudofull={{Sqrt[c1]/f1,0,0},{0,Sqrt[c2]/f2,0}};
pseudorank1={{Sqrt[c1]/f1,0,0},{0,0,0}};
projectionCheck[mat_,pinv_,proj_]:=zero[IdentityMatrix[3]-mat.pinv-proj]&&
 zero[Transpose[proj]-proj]&&zero[proj.proj-proj]&&zero[proj.mat]&&
 zero[proj.Wh.Cov.Transpose[Wh].proj-proj];
c01=zero[Wh.Cov.Transpose[Wh]-IdentityMatrix[3]]&&
 projectionCheck[A,pseudofull,Pfull]&&
 projectionCheck[A/.f2->0,pseudorank1,Prank1]&&
 projectionCheck[ConstantArray[0,{3,2}],ConstantArray[0,{2,3}],Pzero]&&
 zero[Tr[Pfull]-(3-2)]&&zero[Tr[Prank1]-(3-1)]&&zero[Tr[Pzero]-3];
r=Array[res,3];bet={b1,b2};
(* Orthogonal decomposition, with beta*=A+ r available in range(A). *)
glsResidual=Expand[(r-A.bet).(r-A.bet)-(Pfull.r).(Pfull.r)-
 (A.(bet-pseudofull.r)).(A.(bet-pseudofull.r))];
rank1A=A/.f2->0;
rank1Residual=Expand[(r-rank1A.bet).(r-rank1A.bet)-(Prank1.r).(Prank1.r)-
 (rank1A.(bet-pseudorank1.r)).(rank1A.(bet-pseudorank1.r))];
c02=zero[glsResidual]&&zero[rank1Residual]&&
 zero[Pfull.Wh.Cov.Transpose[Wh].Pfull-Pfull]&&
 zero[Prank1.Wh.Cov.Transpose[Wh].Prank1-Prank1]&&
 zero[Eigenvalues[Pfull]-{1,0,0}]&&zero[Sort[Eigenvalues[Prank1]]-{0,1,1}];
(* Set containment N subset F establishes N nonempty => F nonempty,
   and F empty => N empty. Four labeled states are not defined. *)
setLogic=Resolve[ForAll[{n,f},(n==0||f==1)&&n>=0&&n<=1&&f>=0&&f<=1,
 (n==1\[Implies]f==1)&&(f==0\[Implies]n==0)],Integers];
c03=False;
checks=<|"CAS-08-C01"->c01,"CAS-08-C02"->c02,"CAS-08-C03"->c03|>;
result=<|"checks"->checks,
 "domain_assumption_diff"->{"CAS-08-C03: the permitted contract names a four-way geodesicity decision but does not define its four outcomes or the finite sets and thresholds needed to check all four implications."},
 "counterexample"->Null,"xact_actions"->xact,
 "intermediate"-><|"set_containment_implication"->ToString[InputForm[setLogic]],
 "rank_values"->{Tr[Pfull],Tr[Prank1],Tr[Pzero]}|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
