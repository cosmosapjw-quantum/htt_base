#!/usr/bin/env wolframscript
(* Exact symbolic regression oracles for the MES-methodology recovery plan. *)
Quiet[
 Module[
  {Jx,Jy,Jz,vx,vy,vz,v,T,a,b,c,d,e,f,vecSol,tenSol,th,ph,n,
   v1,v2,v3,T11,T22,T12,T13,T23,T33,f1,f2,Vrec,Trec,measure,
   l1,l2,l3,a12,a13,a23,S,A,C,off,transDet,
   k11,k12,k22,pp,qq,rr,K,Dir,Fisher,fisherDet,
   d1,d2,R,Cinv,F0,Fd,scaleResidual,alpha,rankFormula,tieCheck,
   lam1,lam2,lam3,ee1,ee2,ee3,mean2,moment2,checks,m,
   transCheck,fisherCheck,result},

  Jx={{0,0,0},{0,0,-1},{0,1,0}};
  Jy={{0,0,1},{0,0,0},{-1,0,0}};
  Jz={{0,-1,0},{1,0,0},{0,0,0}};
  v={vx,vy,vz};
  T={{a,d,e},{d,b,f},{e,f,c}};
  vecSol=Solve[Flatten[{Jx.v,Jy.v,Jz.v}]==ConstantArray[0,9],{vx,vy,vz},Reals];
  tenSol=Solve[
    Join[Flatten[{Jx.T-T.Jx,Jy.T-T.Jy,Jz.T-T.Jz}],{Tr[T]}]
      ==ConstantArray[0,28],{a,b,c,d,e,f},Reals];

  th=Unique["th"]; ph=Unique["ph"];
  n={Sin[th] Cos[ph],Sin[th] Sin[ph],Cos[th]};
  measure=Sin[th];
  f1={v1,v2,v3}.n;
  Vrec=FullSimplify[
    (3/(4 Pi)) Table[
      Integrate[Integrate[f1 n[[i]] measure,{ph,0,2 Pi}],{th,0,Pi}],{i,3}],
    Assumptions->Element[{v1,v2,v3},Reals]];

  T33=-T11-T22;
  f2=Expand[n.{{T11,T12,T13},{T12,T22,T23},{T13,T23,T33}}.n];
  Trec=FullSimplify[
    (15/(8 Pi)) Table[
      Integrate[Integrate[f2 (n[[i]] n[[j]]-KroneckerDelta[i,j]/3) measure,
                          {ph,0,2 Pi}],{th,0,Pi}],{i,3},{j,3}],
    Assumptions->Element[{T11,T22,T12,T13,T23},Reals]];

  S=DiagonalMatrix[{l1,l2,l3}];
  A={{0,a12,a13},{-a12,0,a23},{-a13,-a23,0}};
  C=A.S-S.A;
  off={C[[1,2]],C[[1,3]],C[[2,3]]};
  transDet=Factor[Det[D[off,{{a12,a13,a23}}]]];
  transCheck=TrueQ[FullSimplify[transDet+(l1-l2)(l1-l3)(l2-l3)==0]];

  K={{k11,k12},{k12,k22}};
  Dir=DiagonalMatrix[{pp,qq,rr}];
  Fisher=KroneckerProduct[K,Dir];
  fisherDet=Factor[Det[Fisher]];
  fisherCheck=TrueQ[
    FullSimplify[fisherDet-(k11 k22-k12^2)^3 pp^2 qq^2 rr^2==0]];

  R={{r11,r12},{r21,r22}};
  Cinv={{c11,c12},{c12,c22}};
  F0=Transpose[R].Cinv.R;
  Fd=Transpose[R.DiagonalMatrix[{d1,d2}]].Cinv.(R.DiagonalMatrix[{d1,d2}]);
  scaleResidual=FullSimplify[
    Fd-DiagonalMatrix[{d1,d2}].F0.DiagonalMatrix[{d1,d2}]];

  alpha=1/20;
  rankFormula=And@@Table[
    Count[Range[0,m],pos_/;(1+pos)/(m+1)<=alpha]/(m+1)
      ==Floor[alpha(m+1)]/(m+1),{m,1,100}];
  tieCheck=And@@Flatten@Table[
    Count[Range[0,m],pos_/;(1+pos+t)/(m+1)<=alpha]
      <=Count[Range[0,m],pos_/;(1+pos)/(m+1)<=alpha],
    {m,1,100},{t,0,m}];

  ee1={1,0,0}; ee2={0,1,0}; ee3={0,0,1};
  mean2=Simplify[
    (lam1 ee1+lam1(-ee1)+lam2 ee2+lam2(-ee2)+lam3 ee3+lam3(-ee3))/2];
  moment2=Simplify[
    (lam1(Outer[Times,ee1,ee1]+Outer[Times,-ee1,-ee1])+
     lam2(Outer[Times,ee2,ee2]+Outer[Times,-ee2,-ee2])+
     lam3(Outer[Times,ee3,ee3]+Outer[Times,-ee3,-ee3]))/2];

  checks=<|
    "scalar_to_vector_no_go"->(vecSol=={{vx->0,vy->0,vz->0}}),
    "scalar_to_stf2_no_go"->(tenSol=={{a->0,b->0,c->0,d->0,e->0,f->0}}),
    "directional_dipole_recovery"->(Vrec=={v1,v2,v3}),
    "directional_stf2_recovery"->
      (Trec=={{T11,T12,T13},{T12,T22,T23},{T13,T23,-T11-T22}}),
    "eigenframe_slice_transverse_simple_spectrum"->transCheck,
    "local_global_fisher_factorization"->fisherCheck,
    "invertible_anchor_fisher_congruence"->
      (scaleResidual==ConstantArray[0,{2,2}]),
    "finite_rank_formula_n1_100"->rankFormula,
    "finite_rank_ties_conservative_n1_100"->tieCheck,
    "zero_mean_antipodal_construction"->(mean2=={0,0,0}),
    "second_moment_antipodal_construction"->
      (moment2==DiagonalMatrix[{lam1,lam2,lam3}])
  |>;

  result=<|
    "schema"->"htt.mes_methodology_recovery.wolfram.v1",
    "wolfram_version"->$Version,
    "all_pass"->TrueQ[And@@Values[checks]],
    "checks"->checks,
    "transversality_determinant"->ToString[InputForm[transDet]],
    "local_global_fisher_determinant"->ToString[InputForm[fisherDet]],
    "first_nonzero_rank_rejection_alpha_0p05"->
      SelectFirst[Table[{m,Floor[alpha(m+1)]/(m+1)},{m,1,100}],Last[#]>0&]
  |>;
  Print[ExportString[result,"RawJSON","Compact"->True]];
  If[TrueQ[result["all_pass"]],Exit[0],Exit[1]]
 ]
]
