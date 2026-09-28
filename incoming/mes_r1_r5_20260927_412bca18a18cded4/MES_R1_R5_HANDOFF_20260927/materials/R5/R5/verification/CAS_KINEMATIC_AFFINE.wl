ClearAll["Global`*"];
zeroQ[x_] := And @@ (TrueQ[FullSimplify[# == 0]] & /@ Flatten[{x}]);
eta = DiagonalMatrix[{-1, 1, 1, 1}];
eps = Normal[LeviCivitaTensor[3]];
outer[x_, y_] := Outer[Times, x, y];
axial[m_] := Table[Sum[eps[[ii,jj,kk]] m[[jj,kk]]/2, {jj,3},{kk,3}],{ii,3}];
stf[m_] := (m+Transpose[m])/2-Tr[m] IdentityMatrix[3]/3;
q = {{q11,q12,q13},{q12,q22,q23},{q13,q23,q33}};
b = {b1,b2,b3};
vars = {q11,q22,q33,q12,q13,q23,b1,b2,b3};
f = ConstantArray[0,{3,3,3}];
f[[1,2,2]]=alpha; f[[2,1,2]]=-alpha;
f[[1,3,3]]=alpha; f[[3,1,3]]=-alpha;
ga = Table[(f[[ii,jj,kk]]-f[[jj,kk,ii]]+f[[kk,ii,jj]])/2,{ii,3},{jj,3},{kk,3}];
fixture[p_] := Module[{g,s,t,l,z,boost,u,conn,ul,ff,bb,aa,bform,aform,wc,out,am,amB,shift,ray,rayExpected},
 g=1/Sqrt[1-p.p]; s=IdentityMatrix[3]+g^2 outer[p,p]/(g+1); t=Inverse[s];
 l=Table[-c Sum[ga[[ii,jj,kk]]p[[kk]],{kk,3}],{ii,3},{jj,3}]; z=q+l;
 boost=Table[Prepend[s[[ii]],g p[[ii]]],{ii,3}]; u=g Prepend[p,1]; ul=eta.u;
 conn=ConstantArray[0,{4,4,4}];
 Do[conn[[ii+1,1,jj+1]]=q[[ii,jj]]/c;conn[[ii+1,jj+1,1]]=q[[ii,jj]]/c,{ii,3},{jj,3}];
 Do[conn[[ii+1,jj+1,kk+1]]=ga[[ii,jj,kk]],{ii,3},{jj,3},{kk,3}];
 ff=Table[KroneckerDelta[ia,1](g^3(p.b)Prepend[p,-1][[ib]]+g Prepend[b,0][[ib]])-c Sum[conn[[ia,ib,ic]]ul[[ic]],{ic,4}],{ia,4},{ib,4}];
 bb=FullSimplify[boost.ff.Transpose[boost]]; aa=FullSimplify[u.ff.Transpose[boost]];
 bform=g s.z.t+g^2 outer[p,s.b]; aform=g^2(s.b+t.Transpose[z].p);
 wc=Table[-c Sum[eps[[ii,jj,kk]] f[[jj,kk,ll]]p[[ll]],{jj,3},{kk,3},{ll,3}]/4,{ii,3}];
 out=Join[Flatten[bb],aa]; am=Table[Coefficient[out[[ii]],vars[[jj]]],{ii,12},{jj,9}]; amB=am[[All,7;;9]];
 shift={v1,v2,v3}; ray=FullSimplify[({bb,aa}/.Thread[b->(b+shift)])-{bb,aa}];
 rayExpected={g^2 outer[p,s.shift],g^2 s.shift};
 <|"Beta"->p,"Gamma"->g,
 "BoostOrthonormal"->zeroQ[boost.eta.Transpose[boost]-IdentityMatrix[3]],
 "BoostOrthogonalToU"->zeroQ[boost.eta.u],
 "FullGradientOrthogonalLastIndex"->zeroQ[ff.u],
 "RestGradientClosedForm"->zeroQ[bb-bform],"RestAccelerationClosedForm"->zeroQ[aa-aform],
 "SymmetricRelation"->zeroQ[bb-outer[p,aa]-g t.z.t],
 "OmegaCompatibility"->zeroQ[axial[(bb-Transpose[bb])/2]-Cross[p,aa]/2-s.wc],
 "OmegaOffset"->FullSimplify[s.wc],
 "RecoverQ"->zeroQ[s.(bb-outer[p,aa]).s/g-l-q],
 "RecoverBJet"->zeroQ[t.(aa-Transpose[bb].p)-b],
 "TraceFormula"->zeroQ[Tr[bb]-g Tr[z]-g^3 p.b],
 "AffineRank"->MatrixRank[am],"BJetImageRank"->MatrixRank[amB],
 "AffineLeftNullDimension"->Length[NullSpace[Transpose[am]]],
 "BJetRayFormula"->zeroQ[ray-rayExpected],
 "BJetInvariant"->zeroQ[ray[[1]]-outer[p,ray[[2]]]],
 "BJetOmegaRank"->MatrixRank[Table[Coefficient[axial[(bb-Transpose[bb])/2][[ii]],b[[jj]]],{ii,3},{jj,3}]],
 "NormalLimitB"->If[p=={0,0,0},zeroQ[bb-q],"not_applicable"],
 "NormalLimitA"->If[p=={0,0,0},zeroQ[aa-b],"not_applicable"]|>
];
<|"TestID"->"R5_KINEMATIC_AFFINE_EXACT_V1","EvidenceScope"->"Exact finite fixtures with all six symmetric q components and three b components symbolic; general rank theorem is proved by analytic inverse", "Fixtures"->{fixture[{0,3/5,0}],fixture[{1/5,2/5,2/5}],fixture[{0,0,0}]},"STFBJetNormIdentity"->zeroQ[Tr[Transpose[stf[outer[{p1,p2,p3},{z1,z2,z3}]]].stf[outer[{p1,p2,p3},{z1,z2,z3}]]]-(({p1,p2,p3}.{p1,p2,p3})({z1,z2,z3}.{z1,z2,z3})/2+({p1,p2,p3}.{z1,z2,z3})^2/6)]|>
