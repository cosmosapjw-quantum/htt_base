(* CAS-17 wedge normal, constant scale, conformal connection, passive map. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b,d,e}];DefMetric[-1,met[-a,-b],CD];
DefTensor[lev[-a,-b,-d,-e],GrstatM,Antisymmetric[{-a,-b,-d,-e}]];
xact=<|"wedgeAntisymmetry"->TrueQ[ToCanonical[lev[-a,-b,-d,-e]+lev[-b,-a,-d,-e]]===0],
 "metricContraction"->TrueQ[ToCanonical[ContractMetric[met[a,b]met[-b,-d]met[d,-a]]-4]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[ll,c,H,Kc,M2,L,Z,offset,phi,ph,xx];
g=DiagonalMatrix[{-1,1,1,1}];
X=Table[xv[i,j],{i,1,4},{j,1,3}];
Gram=Transpose[X].g.X;
V=Table[Sum[Signature[{i,j,k,l}](g.X)[[j,1]](g.X)[[k,2]](g.X)[[l,3]],
 {j,1,4},{k,1,4},{l,1,4}],{i,1,4}];
(* Chosen orientation fixes the future branch of V/sqrt(det Gram). *)
normal=V/Sqrt[Det[Gram]];
uv={Sqrt[1+dv[1]^2+dv[2]^2+dv[3]^2],dv[1],dv[2],dv[3]};
Nrest={1,0,0,0};gamma=-uv.g.Nrest;
beta2=1-1/gamma^2;
c01=zero[Transpose[X].g.V]&&zero[V.g.V+Det[Gram]]&&
 zero[normal.g.normal+1]&&zero[beta2-(dv[1]^2+dv[2]^2+dv[3]^2)/(1+dv[1]^2+dv[2]^2+dv[3]^2)];
(* Constant positive ll: g'=ll^2 g, u'=u/ll, Q'_cov=ll Q. *)
u={Sqrt[1+dz[1]^2+dz[2]^2+dz[3]^2],dz[1],dz[2],dz[3]};
qcov=Table[qv[i,j],{i,4},{j,4}];Bcov=(qcov+Transpose[qcov])/2;
Acon=c g.Transpose[qcov].u;
Ascaled=c (g/ll^2).Transpose[ll qcov].(u/ll);
K=Array[kv,4]; photon=Array[pv,4];
Hraw=K.Bcov.K; Hscaled=(K/ll).(ll Bcov).(K/ll);
mag2=Acon.g.Acon;magScaled2=Ascaled.(ll^2 g).Ascaled;
calibration=TrueQ[FullSimplify[5Log[10,ll H]-5Log[10,H]-5Log[10,ll]==0,
 Assumptions->ll>0&&H>0]];
c02parts={zero[(u/ll).(ll^2 g).(u/ll)-u.g.u],
 zero[Ascaled-Acon/ll^2],zero[Hscaled-Hraw/ll],
 zero[magScaled2-mag2/ll^2],calibration,
 zero[(Kc/ll^2)(ll L)^2-Kc L^2],
 zero[(M2/ll^2)(ll L)^2-M2 L^2],
 zero[(ll dA)^2-ll^2 dA^2],
 zero[(u/ll).(ll^2 g).(photon/ll^2)-u.g.photon/ll]};
c02=And@@c02parts;
(* Derive connection difference from g'=exp(2phi) eta in coordinates. *)
coords=Array[xx,4];f=ph@@coords;gp=Exp[2f]g;gpi=Exp[-2f]g;
conn=Table[Sum[gpi[[i,l]](D[gp[[l,j]],coords[[k]]]+D[gp[[l,k]],coords[[j]]]-D[gp[[j,k]],coords[[l]]])/2,{l,4}],{i,4},{j,4},{k,4}];
grad=Table[D[f,coords[[i]]],{i,4}];
connectionTarget=Table[KroneckerDelta[i,j]grad[[k]]+KroneckerDelta[i,k]grad[[j]]-
 g[[j,k]](g.grad)[[i]],{i,4},{j,4},{k,4}];
connectionIdentity=zero[conn-connectionTarget];
uformal=Array[uvv,4];acc=Array[accv,4];
contr=Table[Sum[connectionTarget[[i,j,k]]uformal[[j]]uformal[[k]],{j,4},{k,4}],{i,4}];
(* Differentiate u'=exp(-phi)u and impose u.g.u=-1. *)
conformalAcc=Exp[-2f](acc+c^2(contr-uformal (uformal.grad)));
projectedTarget=Exp[-2f](acc+c^2(g.grad+uformal (uformal.grad)));
accIdentity=zero[(conformalAcc-projectedTarget)+
 Exp[-2f] c^2 (uformal.g.uformal+1) g.grad];
redshift=zero[(Exp[-phe]Ee)/(Exp[-pho]Eo)-Exp[pho-phe] Ee/Eo];
c03=connectionIdentity&&accIdentity&&redshift;
(* Passive common coordinate change: tensor and vector transform together. *)
J={{a1,b1,0,0},{0,a2,b2,0},{0,0,a3,b3},{0,0,0,a4}};
Jinv=Inverse[J];v=Array[vv,4];w=Array[ww,4];
gnew=Transpose[Jinv].g.Jinv;
c04=zero[(J.v).gnew.(J.w)-v.g.w]&&
 zero[Det[J]-a1 a2 a3 a4];
checks=<|"CAS-17-C01"->c01,"CAS-17-C02"->c02,"CAS-17-C03"->c03,"CAS-17-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"wedge_norm_residual"->ToString[InputForm[FullSimplify[V.g.V+Det[Gram]]]],
 "connection_residual"->ToString[InputForm[FullSimplify[conn-connectionTarget]]],
 "c02parts"->c02parts|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
