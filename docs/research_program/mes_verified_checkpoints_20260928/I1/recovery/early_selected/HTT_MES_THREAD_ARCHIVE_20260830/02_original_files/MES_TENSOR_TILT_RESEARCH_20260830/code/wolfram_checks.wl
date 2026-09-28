(* The three blocks below were executed through WolframLanguageEvaluator.
   They are reproducible symbolic inputs, not an independent scientific review. *)
ClearAll[x,y,z,p,q,v1,v2,v3];
sm={{x,p,q},{p,y,z},{q,z,-x-y}}; v={v1,v2,v3};
s2=Tr[sm.sm]; s3=Tr[sm.sm.sm]; st2=sm.sm-s2 IdentityMatrix[3]/3;
raw=Table[(sm[[i,j]]v[[k]]+sm[[i,k]]v[[j]]+sm[[j,k]]v[[i]])/3,{i,3},{j,3},{k,3}];
trv=Table[Sum[raw[[i,i,k]],{i,3}],{k,3}];
st3=Table[raw[[i,j,k]]-(KroneckerDelta[i,j]trv[[k]]+KroneckerDelta[i,k]trv[[j]]+KroneckerDelta[j,k]trv[[i]])/5,{i,3},{j,3},{k,3}];
ld={x,y,-x-y}; sd=DiagonalMatrix[ld]; dis=Times@@((Subtract@@#)^2& /@ Subsets[ld,{2}]);
Print[<|"CH"->FullSimplify[sm.sm.sm-s2 sm/2-s3 IdentityMatrix[3]/3],
"quartic"->FullSimplify[Tr[sm.sm.sm.sm]-s2^2/2],
"STFSquare"->FullSimplify[Tr[st2.st2]-s2^2/6],
"STFShearVector"->FullSimplify[Total[Flatten[st3]^2]-s2(v.v)/3-2(v.sm.sm.v)/5],
"Discriminant"->FullSimplify[dis-Tr[sd.sd]^3/2+3Tr[sd.sd.sd]^2],
"Krylov"->Factor[Det[Transpose[{v,sd.v,sd.sd.v}]]]|>];

ClearAll[t,x,y,z]; eta=DiagonalMatrix[{-1,1,1,1}]; beta={1/3,2/3,0}; gam=3/2;
jj=IdentityMatrix[3]+gam^2/(gam+1) Outer[Times,beta,beta];
lm=ArrayFlatten[{{{{gam}},-gam {beta}},{-gam Transpose[{beta}],jj}}];
li=ArrayFlatten[{{{{gam}},gam {beta}},{gam Transpose[{beta}],jj}}];
mm={{2,1,0},{1,3,1},{0,1,4}};
aa=ArrayFlatten[{{{{0}},{{0,0,0}}},{{{0},{0},{0}},mm}}];
ap=Transpose[li].aa.li; sh=-Tr[ap[[2;;4,2;;4]]]/3; ar=ap+sh eta;
u=lm.{1,0,0,0}; nn={x,y,z}; k=Prepend[-nn,1]; f=(jj.nn-gam beta).mm.(jj.nn-gam beta);
Print[<|"Lorentz"->Simplify[Transpose[lm].eta.lm-eta],"Kernel"->Simplify[ap.u],
"TimelikeEigen"->Simplify[(eta.ar).u-sh u],"TimelikeNorm"->Simplify[u.eta.u],
"NullQuadratic"->Expand[k.ap.k-f],"Characteristic"->Factor[Det[t IdentityMatrix[4]-eta.ar]-(t-sh)Det[(t-sh)IdentityMatrix[3]-mm]],
"RecoveredBeta"->Simplify[-Rest[u]/First[u]],"GaugeDifference"->Factor[k.ar.k-f]|>];

ClearAll[x,y,z,a,b,c,d,e]; nn={x,y,z};
avg[poly_]:=Total[(If[AnyTrue[First[#],OddQ],0,(Times@@(Factorial2[#-1]& /@ First[#]))/Factorial2[Total[First[#]]+1]] Last[#])& /@ CoefficientRules[Expand[poly],nn]];
ss={{a,c,d},{c,b,e},{d,e,-a-b}}; f=nn.ss.nn; r2=Tr[ss.ss]; r3=Tr[ss.ss.ss]; f2=-(nn.ss.ss.nn)+3 f^2/2;
q2=Table[15/2 avg[f2(nn[[i]]nn[[j]]-KroneckerDelta[i,j]/3)],{i,3},{j,3}];
Print[<|"SecondMoment"->Simplify[avg[f^2]-2r2/15],"ThirdMoment"->Simplify[avg[f^3]-8r3/105],
"BianchiMean2"->Simplify[avg[f2]+2r2/15],"BianchiQuad2"->Simplify[q2+(ss.ss-r2 IdentityMatrix[3]/3)/7],
"SkewnessFactor"->FullSimplify[(8/105)/(2/15)^(3/2)/Sqrt[6]]|>];

(* Fourth external call: explicit Q -> O boost response contraction. *)
ClearAll[a,b,c,d,e,x,y,z]; q={{a,c,d},{c,b,e},{d,e,-a-b}};
v={x,y,z}; q2=Tr[q.q];
raw=Table[(q[[i,j]]v[[k]]+q[[i,k]]v[[j]]+q[[j,k]]v[[i]])/3,{i,3},{j,3},{k,3}];
trv=Table[Sum[raw[[i,i,k]],{i,3}],{k,3}];
o=3Table[raw[[i,j,k]]-(KroneckerDelta[i,j]trv[[k]]+KroneckerDelta[i,k]trv[[j]]+KroneckerDelta[j,k]trv[[i]])/5,{i,3},{j,3},{k,3}];
con=Table[Sum[o[[i,j,k]]q[[j,k]],{j,3},{k,3}],{i,3}];
<|"QOContractionResidual"->Simplify[con-(q2 IdentityMatrix[3]+6 q.q/5).v],
"ResponseNormResidual"->Simplify[Total[Flatten[o]^2]-v.(3q2 IdentityMatrix[3]+18q.q/5).v],
"ResponseTraceResidual"->Table[Simplify[Sum[o[[i,i,k]],{i,3}]],{k,3}]|>
