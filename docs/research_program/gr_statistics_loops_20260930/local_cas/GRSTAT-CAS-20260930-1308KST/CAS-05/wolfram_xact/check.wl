(* CAS-05: curvature computed from a conformal metric, then finite jets. *)
$HistoryLength=0; Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b,d,e}];DefMetric[-1,met[-a,-b],CD];
xact=<|"riemannAntisymmetry"->TrueQ[ToCanonical[RiemannCD[-a,-b,-d,-e]+RiemannCD[-a,-b,-e,-d]]===0],
 "metricCompatibility"->TrueQ[ToCanonical[CD[-a][met[-b,-d]]]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[bpar,lam,kap,xx,ph,qv,mm];
coords=Array[xx,4];eta4=DiagonalMatrix[{-1,1,1,1}];
f=ph@@coords; gcov=Exp[2f] eta4; ginv=Exp[-2f] eta4;
Gam=Table[Sum[ginv[[i,l]](D[gcov[[l,j]],coords[[k]]]+D[gcov[[l,k]],coords[[j]]]-D[gcov[[j,k]],coords[[l]]])/2,{l,1,4}],{i,1,4},{j,1,4},{k,1,4}];
Ric=Table[Sum[D[Gam[[i,j,k]],coords[[i]]]-D[Gam[[i,j,i]],coords[[k]]]+Sum[Gam[[i,i,l]]Gam[[l,j,k]]-Gam[[i,k,l]]Gam[[l,j,i]],{l,1,4}],{i,1,4}],{j,1,4},{k,1,4}];
Rsc=Sum[ginv[[j,k]]Ric[[j,k]],{j,1,4},{k,1,4}];
Ein=Map[FullSimplify,Ric-gcov Rsc/2,{2}];
boxf=Sum[eta4[[i,i]]D[f,{coords[[i]],2}],{i,1,4}];
gradf=Table[D[f,coords[[i]]],{i,1,4}];
expectedEin=Table[-2D[f,coords[[i]],coords[[j]]]+2gradf[[i]]gradf[[j]]+
 2eta4[[i,j]]boxf+eta4[[i,j]](gradf.eta4.gradf),{i,1,4},{j,1,4}];
curvatureIdentity=zero[Ein-expectedEin];
poly=-bpar coords[[1]]^2-bpar Sum[coords[[i]]^2,{i,2,4}]/2+lam coords[[1]]^2 coords[[2]]/2;
polyRules=Join[{f->poly},Table[Derivative[Sequence@@Table[If[j==i,1,0],{j,4}]][ph]@@coords->D[poly,coords[[i]]],{i,4}]];
(* Evaluate the generic formula at the polynomial jet after deriving curvature. *)
Gpoly=expectedEin/.f->poly;
Gpoly=Gpoly/.Derivative[inds___][ph][args___]:>D[poly,Sequence@@MapThread[List,{coords,{inds}}]];
Gpoly=Table[expectedEin[[i,j]]/.f->poly/.Derivative[inds___][ph][args___]:>
 D[poly,Sequence@@MapThread[List,{coords,{inds}}]],{i,4},{j,4}];
(* Direct polynomial derivatives avoid any substitution ambiguity. *)
Gpoly=Table[-2D[poly,coords[[i]],coords[[j]]]+2D[poly,coords[[i]]]D[poly,coords[[j]]]+
 2eta4[[i,j]]Sum[eta4[[k,k]]D[poly,{coords[[k]],2}],{k,4}]+
 eta4[[i,j]]Sum[eta4[[k,k]]D[poly,coords[[k]]]^2,{k,4}],{i,4},{j,4}];
origin=Thread[coords->ConstantArray[0,4]];
G0=Gpoly/.origin;
energy0=(G0[[1,1]]-lam)/kap; pressure0=(G0[[3,3]]+lam)/kap;
(* G_01=-2 lam x0+O(x^2); energy-frame tilt derivative is
   -d_0 G_01/(epsilon+p)=lam/(3b), so physical A1=c^2 times it. *)
tiltSlope=-((D[Gpoly[[1,2]],coords[[1]]]/.origin)/(6bpar));
c01=curvatureIdentity&&zero[G0-DiagonalMatrix[{6bpar,0,0,0}]]&&
 zero[energy0-(6bpar-lam)/kap]&&zero[pressure0-lam/kap]&&
 zero[tiltSlope-lam/(3bpar)];
rayRules={coords[[1]]->0,coords[[2]]->ss,coords[[3]]->0,coords[[4]]->0};
rayExpr=FullSimplify[Exp[-2poly](Gpoly[[1,1]]+Gpoly[[3,3]])/.rayRules];
c02=zero[rayExpr-Exp[bpar ss^2](6bpar-2lam ss)]&&
 zero[(rayExpr/.ss->3bpar/lam)];
(* Linearized Einstein tensor from cubic symmetric metric perturbation. *)
sp=coords[[2;;4]];r2=sp.sp;
M=Table[mm[i,j],{i,3},{j,3}];S=(M+Transpose[M])/2;W=(M-Transpose[M])/2;
q=Array[qv,3];
H=ConstantArray[0,{4,4}];
Do[H[[1,i+1]]=-(coords[[1]]r2 q[[i]])/2-r2 (W.sp)[[i]]/5;
 H[[i+1,1]]=H[[1,i+1]],{i,3}];
Do[H[[i+1,j+1]]=-KroneckerDelta[i,j]coords[[1]](sp.S.sp)/2,{i,3},{j,3}];
Hmix=eta4.H;Hup=eta4.H.eta4;Htrace=Tr[eta4.H];
boxH[v_]:=Sum[eta4[[i,i]]D[v,{coords[[i]],2}],{i,4}];
divdiv=Sum[D[Hup[[i,j]],coords[[i]],coords[[j]]],{i,4},{j,4}];
deltaG=Table[1/2(Sum[D[Hmix[[r,j]],coords[[r]],coords[[i]]]+D[Hmix[[r,i]],coords[[r]],coords[[j]]],{r,4}]-
 boxH[H[[i,j]]]-D[Htrace,coords[[i]],coords[[j]]]-eta4[[i,j]](divdiv-boxH[Htrace])),{i,4},{j,4}];
target=Table[q[[i]]coords[[1]]+Sum[M[[i,j]]sp[[j]],{j,3}],{i,3}];
basisVariables=Join[q,Flatten[M]];
basisChecks=Table[zero[(deltaG[[1,2;;4]]-target)/.Thread[basisVariables->UnitVector[12,k]]],{k,12}];
j2=And@@Flatten[Table[zero[(D[H[[i,j]],Sequence@@Table[{coords[[k]],orders[[k]]},{k,4}]]/.origin)],
 {i,4},{j,4},{orders,Join[{ConstantArray[0,4]},Table[UnitVector[4,k],{k,4}],Flatten[Table[UnitVector[4,k]+UnitVector[4,l],{k,4},{l,k,4}],1]]}]];
bianchi=Table[zero[Sum[eta4[[i,i]]D[deltaG[[i,j]],coords[[i]]],{i,4}]],{j,4}];
c03=zero[deltaG[[1,2;;4]]-target]&&And@@basisChecks&&j2&&And@@bianchi;
checks=<|"CAS-05-C01"->c01,"CAS-05-C02"->c02,"CAS-05-C03"->c03|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"G_origin"->ToString[InputForm[G0]],
 "ray_residual"->ToString[InputForm[FullSimplify[rayExpr-Exp[bpar ss^2](6bpar-2lam ss)]]],
 "basis_checks"->basisChecks,"bianchi_checks"->bianchi|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
