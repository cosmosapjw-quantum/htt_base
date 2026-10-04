(* Independent finite CAS-05-v3 Wolfram/xCoba calculation.  Only the neutral
   metric and cubic coefficients enter as definitions; targets are residuals. *)
$HistoryLength=0;
Needs["xAct`xCoba`"];
DefManifold[MCAS05,4,{a,b,c,d,e,f}];
DefChart[chart05,MCAS05,{0,1,2,3},{tt[],xx[],yy[],zz[]}];
coords={tt[],xx[],yy[],zz[]};
spatial=Rest[coords];
zero=Thread[coords->ConstantArray[0,4]];
eta=DiagonalMatrix[{-1,1,1,1}];
vanishes[expr_]:=TrueQ[FullSimplify[expr==0]];
allZero[expr_]:=And@@(vanishes/@Flatten[{expr}]);
at0[expr_]:=expr/.zero;
fmt[expr_]:=ToString[InputForm[Factor[expr]]];
fmat[mat_]:=Map[fmt,mat,{2}];

(* xCoba computes connection, Ricci and Einstein from this exact metric. *)
phi=-bb tt[]^2-bb Total[spatial^2]/2+ll tt[]^2 xx[]/2;
gconf=CTensor[Exp[2 phi] eta,{-chart05,-chart05}];
SetCMetric[gconf,chart05,SignatureOfMetric->{3,1,0}];
MetricCompute[gconf,chart05,"Christoffel"[1,-1,-1],CVSimplify->Simplify,Verbose->False];
MetricCompute[gconf,chart05,"Ricci"[-1,-1],CVSimplify->Simplify,Verbose->False];
MetricCompute[gconf,chart05,"Einstein"[-1,-1],CVSimplify->Simplify,Verbose->False];
cdconf=CovDOfMetric[gconf];
ein=ToValues[ComponentArray[Einstein[cdconf],{-chart05,-chart05}]];
ric=ToValues[ComponentArray[Ricci[cdconf],{-chart05,-chart05}]];
gamma=ToValues[ComponentArray[Christoffel[cdconf,PDchart05],{chart05,-chart05,-chart05}]];
ginv=Exp[-2 phi] eta;
rsc=Sum[ginv[[i,i]] ric[[i,i]],{i,1,4}];
einFromRic=ric-Exp[2 phi] eta rsc/2;
curvatureResidual=allZero[Map[Simplify,ein-einFromRic,{2}]];
connectionOrigin=allZero[at0[gamma]];

(* An independently displayed expression is a comparison target, not an
   input to MetricCompute.  xCoba has already produced ein above. *)
grad=Table[D[phi,coords[[i]]],{i,1,4}];
hess=Table[D[phi,coords[[i]],coords[[j]]],{i,1,4},{j,1,4}];
boxphi=Sum[eta[[i,i]] hess[[i,i]],{i,1,4}];
grad2=Sum[eta[[i,i]] grad[[i]]^2,{i,1,4}];
displayed=Table[-2 hess[[i,j]]+2 grad[[i]] grad[[j]]+
  eta[[i,j]] (2 boxphi+grad2),{i,1,4},{j,1,4}];
formulaResidual=allZero[Map[Simplify,ein-displayed,{2}]];

g0=at0[ein];
stress0=(g0+cosm eta)/kap;
epsilon=stress0[[1,1]];
pressures=Table[stress0[[i,i]],{i,2,4}];
gap=epsilon+pressures[[1]];
stressResidual=allZero[stress0-DiagonalMatrix[{(6 bb-cosm)/kap,cosm/kap,cosm/kap,cosm/kap}]];
gapResidual=vanishes[gap-6 bb/kap];
strictDEC=FullSimplify[epsilon>Abs[pressures[[1]]],
  Element[{bb,cosm,kap},Reals]&&bb>0&&cosm<3 bb&&kap>0];
dxEpsilon=at0[D[ein[[1,1]]-cosm Exp[2 phi],xx[]]]/kap;
dxP2=at0[D[ein[[3,3]]+cosm Exp[2 phi],xx[]]]/kap;
notEOSResidual=vanishes[dxEpsilon]&&vanishes[dxP2+2 ll/kap];

(* Differentiate both g_ab u^a u^b=-1 and the full mixed eigen equation
   T^a_b u^b=-epsilon u^a at the origin.  The normalized coordinate E0
   contraction has the correct first energy derivative there: the off-diagonal
   stress and first metric derivatives vanish at the origin. *)
tcov=(ein+cosm Exp[2 phi] eta)/kap;
tmixed=ginv.tcov;
mixed0=at0[tmixed];
originEigenResidual=allZero[mixed0[[All,1]]+epsilon UnitVector[4,1]];
epsilonFrame=Exp[-2 phi] tcov[[1,1]];
dEpsilon=Table[at0[D[epsilonFrame,coords[[mu]]]],{mu,1,4}];
dg00=Table[at0[D[Exp[2 phi] eta[[1,1]],coords[[mu]]]],{mu,1,4}];
duTemporal=dg00/2;
normalizationDerivativeResidual=dg00-2 duTemporal;
normalizationChecked=allZero[normalizationDerivativeResidual]&&
  allZero[dg00]&&allZero[duTemporal];
dMixedColumn=Table[at0[D[tmixed[[a,1]],coords[[mu]]]],
  {mu,1,4},{a,1,4}];
dT0i=Table[at0[D[ein[[1,i+1]],coords[[mu]]]]/kap,
  {mu,1,4},{i,1,3}];
mixedSpatialDerivativeResidual=allZero[dMixedColumn[[All,2;;4]]-dT0i];
duSpatial=Map[-#/gap&,dMixedColumn[[All,2;;4]],{2}];
du=Table[Prepend[duSpatial[[mu]],duTemporal[[mu]]],{mu,1,4}];
fullEigenEquation=Table[dMixedColumn[[mu,a]]+
  Sum[(mixed0[[a,b]]+epsilon KroneckerDelta[a,b]) du[[mu,b]],
    {b,1,4}]+KroneckerDelta[a,1] dEpsilon[[mu]],
  {mu,1,4},{a,1,4}];
fullEigenResidual=allZero[fullEigenEquation];
energyDerivativeResidual=allZero[dEpsilon]&&
  allZero[dMixedColumn[[All,1]]+dEpsilon];
rateResidual=allZero[du-{{0,ll/(3 bb),0,0},
  {0,0,0,0},{0,0,0,0},{0,0,0,0}}];
acceleration=cc^2 First[du];
accelerationResidual=allZero[acceleration-{0,cc^2 ll/(3 bb),0,0}];

(* Orthonormal E_a=exp(-phi) partial_a on t=y=z=0, x=s. *)
raySub={tt[]->0,xx[]->ss,yy[]->0,zz[]->0};
ray=FullSimplify[(Exp[-2 phi] (ein[[1,1]]+ein[[3,3]]))/.raySub];
rayTarget=Exp[bb ss^2] (6 bb-2 ll ss);
rayResidual=vanishes[ray-rayTarget];
lambdaZeroResidual=vanishes[(ray/.ll->0)-6 bb Exp[bb ss^2]];
rayRootResidual=vanishes[FullSimplify[ray/.ss->3 bb/ll,
  Element[{bb,ll},Reals]&&bb>0&&ll!=0]];
rayNoCross=allZero[Flatten[Table[(ein[[i,j]]/.raySub),
  {i,1,4},{j,i+1,4}]]];
UnsetCMetric[gconf];

(* The cubic H is built from the arbitrary q and M coefficients. *)
qv=Table[Symbol["q"<>ToString[i]],{i,1,3}];
matM=Table[Symbol["m"<>ToString[i]<>ToString[j]],{i,1,3},{j,1,3}];
makeH[q_,m_]:=Module[{sym=(m+Transpose[m])/2,skew=(m-Transpose[m])/2,
  r2=Total[spatial^2],quad,hh=ConstantArray[0,{4,4}]},
  quad=spatial.sym.spatial;
  Do[hh[[i+1,i+1]]=-tt[] quad/2,{i,1,3}];
  Do[hh[[1,i+1]]=-tt[] r2 q[[i]]/2-r2 (skew.spatial)[[i]]/5;
    hh[[i+1,1]]=hh[[1,i+1]],{i,1,3}];
  hh
];
H=makeH[qv,matM];
j2H=And@@Flatten[Table[allZero[at0[D[H[[i,j]],
  Sequence@@(coords[[#]]&/@inds)]]],{i,1,4},{j,1,4},
  {order,0,2},{inds,Tuples[Range[4],order]}]];

(* Linearized Ricci follows by differentiating the metric connection.  Since
   H and its first two derivatives vanish at 0, background-curvature times H
   and background-connection times its derivatives vanish in dG(0). *)
linEin[h_]:=Module[{tr,box,lr,ls},
  tr=Sum[eta[[i,i]] h[[i,i]],{i,1,4}];
  box[expr_]:=Sum[eta[[i,i]] D[expr,coords[[i]],coords[[i]]],{i,1,4}];
  lr=Table[(Sum[eta[[c,c]] (
     D[h[[c,j]],coords[[c]],coords[[i]]]+
     D[h[[c,i]],coords[[c]],coords[[j]]]),{c,1,4}]
     -box[h[[i,j]]]-D[tr,coords[[i]],coords[[j]]])/2,
     {i,1,4},{j,1,4}];
  ls=Sum[eta[[i,i]] lr[[i,i]],{i,1,4}];
  Expand[lr-eta ls/2]
];
linG=linEin[H];
jet=Table[at0[D[linG[[i,j]],coords[[mu]]]],
  {mu,1,4},{i,1,4},{j,1,4}];
baselineFirst=Table[at0[D[ein[[i,j]]/.ll->0,coords[[mu]]]],
  {mu,1,4},{i,1,4},{j,1,4}];
baselineResidual=allZero[baselineFirst];
target0i=Table[If[mu==1,qv[[i]],matM[[i,mu-1]]],
  {mu,1,4},{i,1,3}];
rightInverseResidual=allZero[Table[jet[[mu,1,i+1]]-target0i[[mu,i]],
  {mu,1,4},{i,1,3}]];
bianchi=Table[Sum[eta[[a,a]] jet[[a,a,j]],{a,1,4}],{j,1,4}];
bianchiResidual=allZero[bianchi];

(* Every coefficient basis is also calculated by xCoba directly from the
   polynomial metric eta+H.  Truncation to total coordinate degree 3 is exact
   for dG(0): g has no lower H jet, g^-1 needs degree <=3, Gamma needs <=2,
   and R/G need <=1.  It avoids irrelevant nonlinear rational terms at
   coordinate degree >=4.  No target jet enters MetricCompute. *)
trunc3[expr_]:=Expand[Normal[Series[expr/.
  Thread[coords->tau coords],{tau,0,3}]]/.tau->1];
names=Join[Table["k0"<>ToString[i],{i,1,3}],
  Flatten[Table["k"<>ToString[j]<>ToString[i],{j,1,3},{i,1,3}]]];
basisImages={};
xActMatches={};
Do[
  kb=ConstantArray[0,{4,3}];
  If[n<=3,kb[[1,n]]=1,
    jj=Quotient[n-4,3]+1;ii=Mod[n-4,3]+1;kb[[jj+1,ii]]=1];
  qb=-6 bb kb[[1]];
  mb=Table[-6 bb kb[[j+1,i]],{i,1,3},{j,1,3}];
  hb=makeH[qb,mb];
  gb=CTensor[eta+hb,{-chart05,-chart05}];
  SetCMetric[gb,chart05,SignatureOfMetric->{3,1,0}];
  MetricCompute[gb,chart05,"Einstein"[-1,-1],CVSimplify->trunc3,Verbose->False];
  cdb=CovDOfMetric[gb];
  eb=ToValues[ComponentArray[Einstein[cdb],{-chart05,-chart05}]];
  xjet=Table[Factor[at0[D[eb[[i,j]],coords[[mu]]]]],
    {mu,1,4},{i,1,4},{j,1,4}];
  ljet=Table[Factor[at0[D[linEin[hb][[i,j]],coords[[mu]]]]],
    {mu,1,4},{i,1,4},{j,1,4}];
  AppendTo[xActMatches,allZero[xjet-ljet]];
  AppendTo[basisImages,<|"basis"->names[[n]],
    "xact_jet"->Map[fmt,xjet,{3}],
    "linear_jet"->Map[fmt,ljet,{3}],
    "residual_zero"->Last[xActMatches]|>];
  UnsetCMetric[gb];
  Print["AXIS_PROGRESS basis ",n,"/12 ",names[[n]]," residual_zero=",Last[xActMatches]];
,{n,1,12}];

(* Explicit universal right inverse: arbitrary real q,M and b>0. *)
rightInverseK=Join[{Map[-#/(6 bb)&,qv]},
  Table[-matM[[i,j]]/(6 bb),{j,1,3},{i,1,3}]];
rightInverseQ=-6 bb rightInverseK[[1]];
rightInverseM=Table[-6 bb rightInverseK[[j+1,i]],{i,1,3},{j,1,3}];
rightInverseCoefficients=allZero[rightInverseQ-qv]&&
  allZero[rightInverseM-matM];
inducedK=Table[-jet[[mu,1,i+1]]/(6 bb),{mu,1,4},{i,1,3}];
inducedKResidual=allZero[inducedK-rightInverseK];

c01=And[curvatureResidual,connectionOrigin,formulaResidual,stressResidual,
  gapResidual,TrueQ[strictDEC],originEigenResidual,
  normalizationChecked,mixedSpatialDerivativeResidual,
  fullEigenResidual,energyDerivativeResidual,rateResidual,
  accelerationResidual,notEOSResidual];
c02=And[rayResidual,lambdaZeroResidual,rayRootResidual,rayNoCross];
c03=And[j2H,baselineResidual,rightInverseResidual,bianchiResidual,
  rightInverseCoefficients,inducedKResidual,And@@xActMatches];
payload=<|
 "checks"-><|"CAS-05-C01"->TrueQ[c01],"CAS-05-C02"->TrueQ[c02],
   "CAS-05-C03"->TrueQ[c03]|>,
 "domain_assumption_diff"->{},"counterexample"->Null,
 "computed"-><|
   "engine"->ToString[System`$Version],"xTensorVersion"->ToString[xAct`xTensor`$Version],
   "xCobaVersion"->ToString[xAct`xCoba`$Version],
   "c01"-><|"xact_G_origin"->fmat[g0],"stress_origin"->fmat[stress0],
     "gap"->fmt[gap],"dT0i"->Map[fmt,dT0i,{2}],
     "mixed_stress_origin"->fmat[mixed0],
     "d_mixed_stress_column_0"->Map[fmt,dMixedColumn,{2}],
     "d_epsilon"->Map[fmt,dEpsilon],
     "d_metric_00"->Map[fmt,dg00],
     "d_u_temporal_from_normalization"->Map[fmt,duTemporal],
     "normalization_derivative_residuals"->Map[fmt,normalizationDerivativeResidual],
     "d_u_all_components"->Map[fmt,du,{2}],
     "full_16_eigen_equation_residuals"->Map[fmt,fullEigenEquation,{2}],
     "full_eigen_equation_residual_zero"->fullEigenResidual,
     "acceleration"->Map[fmt,acceleration],
     "dx_epsilon"->fmt[dxEpsilon],"dx_p2"->fmt[dxP2],
     "non_EOS_derivative_residual_zero"->notEOSResidual,
     "curvature_ricci_identity"->curvatureResidual,
     "conformal_formula_residual_zero"->formulaResidual,
     "strict_DEC_origin"->strictDEC|>,
   "c02"-><|"ray_kappa_epsilon_plus_p2"->fmt[ray],
     "lambda_zero_residual_zero"->lambdaZeroResidual,
     "gap_root_residual_zero"->rayRootResidual|>,
   "c03"-><|"j2H_zero"->j2H,
     "first_Einstein_jet"->Map[fmt,jet,{3}],
     "basis_images"->basisImages,"all_basis_xact_residuals_zero"->And@@xActMatches,
     "bianchi_contractions"->Map[fmt,bianchi],
     "right_inverse_k_rows_mu0_to3"->Map[fmt,rightInverseK,{2}],
     "induced_eigenframe_jet"->Map[fmt,inducedK,{2}],
     "induced_k_residual_zero"->inducedKResidual,
     "target_0i_residual_zero"->rightInverseResidual|>
 |>
|>;
Print["AXIS_JSON_START",ExportString[payload,"RawJSON"],"AXIS_JSON_END"];
Exit[If[And[c01,c02,c03],0,2]];
