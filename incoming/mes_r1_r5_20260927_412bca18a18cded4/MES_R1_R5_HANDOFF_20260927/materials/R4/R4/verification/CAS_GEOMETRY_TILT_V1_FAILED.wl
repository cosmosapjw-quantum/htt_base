ClearAll["Global\`*"];
zeroQ[x_] := And @@ (TrueQ[FullSimplify[# == 0]] & /@ Flatten[{x}]);
makeConn[f_] := Table[(f[[aa,bb,cc]]-f[[bb,cc,aa]]+f[[cc,aa,bb]])/2,{aa,3},{bb,3},{cc,3}];
rhoMat[ga_,rank_,aa_] := Sum[KroneckerProduct @@ Table[If[slot==jj,ga[[aa]],IdentityMatrix[3]],{slot,rank}],{jj,rank}];
firstMat[ga_,rank_] := Join @@ Table[-rhoMat[ga,rank,aa],{aa,3}];
secondMat[ga_,rank_] := Join @@ Flatten[Table[{rhoMat[ga,rank,aa].rhoMat[ga,rank,bb]+Sum[ga[[aa,bb,dd]]rhoMat[ga,rank,dd],{dd,3}]},{aa,3},{bb,3}],1];
fa=Normal[LeviCivitaTensor[3]];
fb=ConstantArray[0,{3,3,3}];
fb[[1,2,2]]=1; fb[[2,1,2]]=-1; fb[[1,3,3]]=1; fb[[3,1,3]]=-1;
geomResults=Table[Module[{ff=fixture[[2]],gg,jac,metric,torsion,g2,rows},
 gg=makeConn[ff];
 jac=Table[Sum[ff[[aa,bb,mm]]ff[[mm,cc,dd]]+ff[[bb,cc,mm]]ff[[mm,aa,dd]]+ff[[cc,aa,mm]]ff[[mm,bb,dd]],{mm,3}],{aa,3},{bb,3},{cc,3},{dd,3}];
 metric=Table[gg[[aa,bb,cc]]+gg[[aa,cc,bb]],{aa,3},{bb,3},{cc,3}];
 torsion=Table[gg[[aa,bb,cc]]-gg[[bb,aa,cc]]-ff[[aa,bb,cc]],{aa,3},{bb,3},{cc,3}];
 g2=Total[Max[Eigenvalues[Transpose[#].#]]& /@ gg];
 rows=Table[Module[{m1,m2,recur,naive,ev1,ev2},
  m1=firstMat[gg,rank];m2=secondMat[gg,rank];recur=firstMat[gg,rank+1].m1;
  naive=Join@@Flatten[Table[{rhoMat[gg,rank,aa].rhoMat[gg,rank,bb]},{aa,3},{bb,3}],1];
  ev1=Eigenvalues[rank^2 g2 IdentityMatrix[3^rank]-Transpose[m1].m1];
  ev2=Eigenvalues[(rank(rank+1)g2)^2 IdentityMatrix[3^rank]-Transpose[m2].m2];
  <|"Rank"->rank,"FirstMatrixDimensions"->Dimensions[m1],"SecondMatrixDimensions"->Dimensions[m2],"SecondRecursiveResidualZero"->zeroQ[m2-recur],"DerivativeSlotIsNonzero"->(!zeroQ[m2-naive]),"FirstCoarseBoundPSD"->TrueQ[Min[ev1]>=0],"SecondCoarseBoundPSD"->TrueQ[Min[ev2]>=0],"FirstGramBoundMinimumEigenvalue"->Min[ev1],"SecondGramBoundMinimumEigenvalue"->Min[ev2]|>
 ],{rank,1,3}];
 <|"Fixture"->fixture[[1]],"JacobiZero"->zeroQ[jac],"MetricCompatibilityZero"->zeroQ[metric],"TorsionZero"->zeroQ[torsion],"G2"->g2,"RankChecks"->rows|>
],{fixture,{{"classA_su2_unit",fa},{"classB_solvable_unit",fb}}}];
metric4=DiagonalMatrix[{-1,1,1,1}];
tiltCheck[beta_,jet_,conn_] := Module[{gam,w,wl,u,ul,proj,hs,ff,th,ac,sp,ss,oo,dec},
 gam=1/Sqrt[1-beta.beta];w=Prepend[beta,1];wl=metric4.w;u=gam w;ul=metric4.u;
 proj=IdentityMatrix[4]+Outer[Times,ul,u];hs=metric4+Outer[Times,ul,ul];
 ff=Table[KroneckerDelta[aa,1](gam^3(beta.jet)wl[[bb]]+gam Prepend[jet,0][[bb]])-c gam Sum[conn[[aa,bb,dd]]wl[[dd]],{dd,4}],{aa,4},{bb,4}];
 th=Tr[metric4.ff];ac=u.ff;sp=proj.ff.Transpose[proj];
 ss=(sp+Transpose[sp])/2-th hs/3;oo=(sp-Transpose[sp])/2;
 dec=ff-ss-oo-th hs/3+Outer[Times,ul,ac];
 <|"FourVelocityNorm"->FullSimplify[u.metric4.u],"F_UZero"->zeroQ[ff.u],"A_UZero"->zeroQ[ac.u],"ShearTraceZero"->zeroQ[Tr[metric4.ss]],"ShearSpatialZero"->zeroQ[ss.u],"VorticitySpatialZero"->zeroQ[oo.u],"DecompositionZero"->zeroQ[dec],"Theta"->FullSimplify[th],"AccelerationCovariant"->FullSimplify[c ac],"ShearCovariant"->FullSimplify[ss],"VorticityCovariant"->FullSimplify[oo]|>
];
jet={b1,b2,b3};empty=ConstantArray[0,{4,4,4}];
mink=tiltCheck[{1/3,1/4,0},jet,empty];
zeroTilt=tiltCheck[{0,0,0},jet,empty];
kk={{2,1,0},{1,3,1},{0,1,4}};normalConn=empty;
Do[normalConn[[ii+1,1,jj+1]]=kk[[ii,jj]];normalConn[[ii+1,jj+1,1]]=kk[[ii,jj]],{ii,3},{jj,3}];
normal=tiltCheck[{0,0,0},{0,0,0},normalConn];
normalShear=ArrayPad[c(kk-Tr[kk]IdentityMatrix[3]/3),{{1,0},{1,0}}];
<|"TestID"->"CAS_GEOMETRY_TILT_V1","EvidenceScope"->"Exact finite fixtures, not general theorem proof; c retained in tilt outputs","Geometry"->geomResults,"MinkowskiTilt"->KeyDrop[mink,{"ShearCovariant","VorticityCovariant"}],"ZeroTiltNonzeroJetAccelerationCheck"->zeroQ[zeroTilt["AccelerationCovariant"]-c Prepend[jet,0]],"NormalLimit"-><|"ThetaCheck"->zeroQ[normal["Theta"]-c Tr[kk]],"AccelerationZero"->zeroQ[normal["AccelerationCovariant"]],"ShearCheck"->zeroQ[normal["ShearCovariant"]-normalShear],"VorticityZero"->zeroQ[normal["VorticityCovariant"]]|>|>

