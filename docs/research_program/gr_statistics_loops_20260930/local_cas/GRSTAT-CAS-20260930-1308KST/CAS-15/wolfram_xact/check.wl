(* CAS-15 photon jet, pointwise sphere kernel, commutator response. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b,d}];DefMetric[-1,eta[-a,-b],CD];
DefTensor[qq[-a,-b],GrstatM];DefTensor[ll[a],GrstatM];
xact=<|"photonContractionSymmetry"->TrueQ[ToCanonical[qq[-a,-b]ll[a]ll[b]-qq[-b,-a]ll[a]ll[b]]===0],
 "raisedLoweredPhoton"->TrueQ[ToCanonical[ContractMetric[eta[a,b]eta[-b,-d]ll[d]-ll[a]]]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[c,H,aa,sg,om,e,m,ww,la,mu,dd,rr,ey,em,ow,gap];
g=DiagonalMatrix[{-1,1,1,1}];
ea=Array[e,3];avec=Array[aa,3];ovec=Array[om,3];
sigma=Table[If[i<=j,sg[i,j],sg[j,i]],{i,1,3},{j,1,3}];
sigma[[3,3]]=-sigma[[1,1]]-sigma[[2,2]];
W={{0,ovec[[3]],-ovec[[2]]},{-ovec[[3]],0,ovec[[1]]},{ovec[[2]],-ovec[[1]],0}};
Q=Join[{Prepend[avec,0]},MapThread[Prepend,{H IdentityMatrix[3]+sigma+W,{0,0,0}}]];
L=c Prepend[ea,1];qL=L.Q;
projected=qL[[2;;4]]/c;
F=(IdentityMatrix[3]-Outer[Times,ea,ea]).(avec+sigma.ea);
(* e.e=1: spatial geodesic derivative is -F+W e, and photon energy
   derivative is -L Q L/c^2. *)
dirActual=-(IdentityMatrix[3]-Outer[Times,ea,ea]).projected;
dirTarget=-F+W.ea;
energyActual=-L.Q.L/c^2;
energyTarget=-(H+avec.ea+ea.sigma.ea);
normRule=e[3]^2->1-e[1]^2-e[2]^2;
c01=zero[FullSimplify[dirActual-dirTarget]/.normRule]&&
 zero[FullSimplify[energyActual-energyTarget]/.normRule]&&zero[Q.{1,0,0,0}];
(* Tangent divergence on S^2 is P_ij d_j F_i. The weak kernel below
   follows only after a separately justified no-boundary-flux IBP. *)
P=IdentityMatrix[3]-Outer[Times,ea,ea];
divF=Sum[P[[i,j]] D[F[[i]],ea[[j]]],{i,1,3},{j,1,3}];
kin=H+avec.ea+ea.sigma.ea;
weakLeft=Expand[(4kin+divF) Outer[Times,ea,ea]+Outer[Times,F,ea]+Outer[Times,ea,F]];
weakRight=Expand[(4H-ea.sigma.ea) Outer[Times,ea,ea]+Outer[Times,avec,ea]+
 Outer[Times,ea,avec]+Outer[Times,sigma.ea,ea]+Outer[Times,ea,sigma.ea]];
c02=zero[FullSimplify[divF-(-2avec.ea-3ea.sigma.ea)]/.normRule]&&
 zero[FullSimplify[weakLeft-weakRight]/.normRule];
M=DiagonalMatrix[Array[m,3]];
comm=M.W-W.M;
component=Table[If[i==j,0,(m[i]-m[j])W[[i,j]]],{i,3},{j,3}];
(* Frobenius gap bound and perturbation bound are scalar consequences of
   singular-value lower bound and ||[dM,W]||F<=2||dM||op||W||F. *)
bound1=FullSimplify[ForAll[{rr,ey,gap},rr>=0&&ey>=0&&gap>0&&gap rr<=ey,rr<=ey/gap]];
bound2=FullSimplify[ForAll[{rr,ey,em,ow,gap},rr>=0&&ey>=0&&em>=0&&ow>=0&&gap>0&&gap rr<=ey+2em ow,
 rr<=(ey+2em ow)/gap]];
c03=zero[comm-component]&&TrueQ[bound1]&&TrueQ[bound2]&&
 zero[Tr[Transpose[comm].comm]-2 Sum[(m[i]-m[j])^2 W[[i,j]]^2,{i,1,2},{j,i+1,3}]];
(* W basis and stacked response Gram, using independent upper entries
   weighted twice off diagonal to equal Frobenius norm. *)
wbasis=Table[W/.Thread[ovec->UnitVector[3,k]],{k,1,3}];
M1=DiagonalMatrix[{la,la,mu}];
axis={ss,0,cc};M2=la IdentityMatrix[3]+dd Outer[Times,axis,axis];
response[mm_,w_]:=mm.w-w.mm;
rg1=Table[Tr[response[M1,wbasis[[i]]].response[M1,wbasis[[j]]]],{i,3},{j,3}];
rg2=Table[Tr[response[M2,wbasis[[i]]].response[M2,wbasis[[j]]]],{i,3},{j,3}];
rg=rg1+rg2;
(* Unit axis ss^2+cc^2=1. The common commutant is zero when
   mu-la,dd,ss are nonzero; test rank by determinant factorization. *)
rgdet=Factor[Det[rg]/.cc^2->1-ss^2];
c04=zero[rg-Transpose[rg]]&&
 zero[rgdet-8 (mu-la)^2 dd^2 ss^2 ((mu-la)^2+dd^2)] ;
checks=<|"CAS-15-C01"->c01,"CAS-15-C02"->c02,"CAS-15-C03"->c03,"CAS-15-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"sphere_divergence_identity_residual"->ToString[InputForm[FullSimplify[divF+2avec.ea+3ea.sigma.ea]/.normRule]],
 "response_gram"->ToString[InputForm[rg]],"response_det"->ToString[InputForm[rgdet]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
