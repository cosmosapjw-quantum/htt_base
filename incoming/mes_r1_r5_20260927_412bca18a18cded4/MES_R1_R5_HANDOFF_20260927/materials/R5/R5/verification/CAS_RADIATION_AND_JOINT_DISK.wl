ClearAll["Global`*"];
stf[m_] := (m + Transpose[m])/2 - Tr[m] IdentityMatrix[3]/3;
p = {p1, p2, p3}; v1 = {v11, v12, v13};
v2 = {{v21, v23, v24}, {v23, v22, v25}, {v24, v25, -v21-v22}};
vars = Join[v1, {v21, v22, v23, v24, v25}];
out1 = v1 + (2/5) v2.p;
out2 = v2 + stf[Outer[Times, p, v1]];
outs = Join[out1, {out2[[1,1]],out2[[2,2]],out2[[1,2]],out2[[1,3]],out2[[2,3]]}];
rad = Table[D[outs[[i]],vars[[j]]],{i,8},{j,8}];
psq = p.p;
schur = (1-psq/5) IdentityMatrix[3] - Outer[Times,p,p]/15;
checkSchur = Simplify[v1-(2/5) stf[Outer[Times,p,v1]].p-schur.v1];
checkDet = Factor[Det[rad]-(1-psq/5)^2 (1-4 psq/15)];
fixtureRad = rad /. {p1->0,p2->3/5,p3->0};
g = 5/4; p = {0,3/5,0};
sm = IdentityMatrix[3] + g^2 Outer[Times,p,p]/(g+1);
tm = Inverse[sm];
lm = {{0,0,0},{3 c alpha/5,0,0},{0,0,0}};
w0 = {0,0,-3 c alpha/10};
om = {{0,w0[[3]],-w0[[2]]},{-w0[[3]],0,w0[[1]]},{w0[[2]],-w0[[1]],0}};
b0 = hub IdentityMatrix[3]+om;
qm = Simplify[sm.b0.sm/g-lm];
acc = astar {x,0,z};
grad = b0+Outer[Times,p,acc];
bjet = Simplify[tm.(acc-Transpose[grad].p)];
gradDirect = Simplify[g sm.(qm+lm).tm + g^2 Outer[Times,p,sm.bjet]];
accDirect = Simplify[g^2 (sm.bjet+tm.Transpose[qm+lm].p)];
sig = stf[grad];
wv[m_] := {(m[[2,3]]-m[[3,2]])/2,(m[[3,1]]-m[[1,3]])/2,(m[[1,2]]-m[[2,1]])/2};
w = wv[grad];
rs = 3 astar/(5 Sqrt[2]); rw = 3 astar/10;
carrier = Simplify[Join[Flatten[sig/rs],(w-w0)/rw,acc/astar]/Sqrt[3]];
jmat = Transpose[{D[carrier,x],D[carrier,z]}];
proj = Simplify[jmat.Transpose[jmat]];
res = <|
 "SchurIdentityZero"->checkSchur,
 "RadiationDeterminantIdentityZero"->checkDet,
 "RadiationFixtureRank"->MatrixRank[fixtureRad],
 "RadiationFixtureDeterminant"->Det[fixtureRad],
 "SchurFixtureEigenvalues"->Eigenvalues[schur /. {p1->0,p2->3/5,p3->0}],
 "DiskSymmetricQ"->qm,
 "DiskQSymmetryResidual"->Simplify[qm-Transpose[qm]],
 "DiskBJet"->bjet,
 "Disk4DAdapterResidualB"->Simplify[gradDirect-grad],
 "Disk4DAdapterResidualA"->Simplify[accDirect-acc],
 "DiskExpansion"->Tr[grad],
 "DiskShear"->sig,
 "DiskVorticity"->w,
 "DiskVorticityConstraintResidual"->Simplify[w-Cross[p,acc]/2-sm.w0],
 "NormalizedCarrier"->carrier,
 "NormalizedCarrierSquaredNorm"->Simplify[carrier.carrier],
 "JointMapGram"->Simplify[Transpose[jmat].jmat],
 "JointMapRank"->MatrixRank[jmat],
 "ProjectorIdempotenceResidual"->Simplify[proj.proj-proj],
 "ProjectorTrace"->Tr[proj],
 "SectorSquaredNorms"->Simplify[{Flatten[sig].Flatten[sig]/rs^2,(w-w0).(w-w0)/rw^2,acc.acc/astar^2}],
 "UniformDiskTailScalar"->FullSimplify[Integrate[2 r,{r,Sqrt[qcut],1}],Assumptions->0<qcut<1],
 "UniformDiskTailOuterCoefficient"->FullSimplify[Integrate[r^3,{r,Sqrt[qcut],1}],Assumptions->0<qcut<1],
 "UniformDiskTailDirectionCoefficient"->FullSimplify[Integrate[r,{r,Sqrt[qcut],1}],Assumptions->0<qcut<1]
|>;
ToString[res,InputForm]
