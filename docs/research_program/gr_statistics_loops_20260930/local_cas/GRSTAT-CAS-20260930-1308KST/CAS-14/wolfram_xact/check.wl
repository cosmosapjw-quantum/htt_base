(* CAS-14 exact rest-space vorticity and Gram reconstruction. *)
$HistoryLength=0; Needs["xAct`xTensor`"];
DefManifold[RestM,3,{i,j,k}];DefMetric[1,hh[-i,-j],D3];
DefTensor[eps3[-i,-j,-k],RestM,Antisymmetric[{-i,-j,-k}]];
xact=<|"leviAntisymmetry"->TrueQ[ToCanonical[eps3[-i,-j,-k]+eps3[-j,-i,-k]]===0],
 "restMetricContraction"->TrueQ[ToCanonical[ContractMetric[hh[i,j]hh[-j,-k]hh[k,-i]]-3]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[om,x,z,w1,w2,rr,ey,ea,os,sl];
o=Array[om,3];v=Array[x,3];
W={{0,o[[3]],-o[[2]]},{-o[[3]],0,o[[1]]},{o[[2]],-o[[1]],0}};
y=-W.v;P=IdentityMatrix[3]-Outer[Times,v,v];
crossIdentity=zero[W.v+Cross[o,v]]&&
 zero[Cross[v,y]-P.o /. v[[3]]^2->1-v[[1]]^2-v[[2]]^2];
(* A two-direction Gram instance and the exact quadratic form. *)
x1={1,0,0};x2={0,1,0};
G=w1 (IdentityMatrix[3]-Outer[Times,x1,x1])+w2 (IdentityMatrix[3]-Outer[Times,x2,x2]);
b=w1 Cross[x1,Cross[o,x1]]+w2 Cross[x2,Cross[o,x2]];
c01=crossIdentity&&zero[b-G.o]&&zero[Tr[Transpose[W].W]-2o.o];
quad=Array[z,3].G.Array[z,3];
quadCross=w1 Cross[Array[z,3],x1].Cross[Array[z,3],x1]+w2 Cross[Array[z,3],x2].Cross[Array[z,3],x2];
Ginv=DiagonalMatrix[{1/w2,1/w1,1/(w1+w2)}];
qcos=Unique["qcos"]; qsin=Unique["qsin"];
x2general={qcos,qsin,0};
Ggeneral=w1 (IdentityMatrix[3]-Outer[Times,x1,x1])+
 w2 (IdentityMatrix[3]-Outer[Times,x2general,x2general]);
generalDet=Factor[Det[Ggeneral] /. qsin^2->1-qcos^2];
c02=zero[quad-quadCross]&&zero[G.Ginv-IdentityMatrix[3]]&&
 zero[Det[G]-w1 w2 (w1+w2)]&&
 zero[generalDet-w1 w2 (w1+w2) (1-qcos^2)]&&
 TrueQ[FullSimplify[ForAll[{w1,w2,qcos},w1>0&&w2>0&&-1<qcos<1,
 w1 w2 (w1+w2)(1-qcos^2)>0]]];
(* The norm bounds follow from ||Ahat dω|| <= ||dy||+||dA|| ||ω||
   and sigma_min(Ahat)||dω|| <= ||Ahat dω||. Here the exact scalar
   implication is checked on the declared nonnegative real domain. *)
firstBound=FullSimplify[ForAll[{rr,ey,sl},
 ey>=0&&sl>0&&rr>=0&&sl rr<=ey,rr<=ey/sl]];
secondBound=FullSimplify[ForAll[{rr,ey,ea,os,sl},
 ey>=0&&ea>=0&&os>=0&&sl>0&&rr>=0&&sl rr<=ey+ea os,
 rr<=(ey+ea os)/sl]];
dw=Table[If[a==b,0,If[a==1&&b==2,om[3],If[a==1&&b==3,-om[2],If[a==2&&b==1,-om[3],If[a==2&&b==3,om[1],If[a==3&&b==1,om[2],-om[1]]]]]]],{a,3},{b,3}];
c03=TrueQ[firstBound]&&TrueQ[secondBound]&&zero[Tr[Transpose[dw].dw]-2o.o];
checks=<|"CAS-14-C01"->c01,"CAS-14-C02"->c02,"CAS-14-C03"->c03|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"Gram"->ToString[InputForm[G]],
 "scalar_bounds"->{ToString[InputForm[firstBound]],ToString[InputForm[secondBound]]}|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
