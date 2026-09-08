(* Independent R8 CAS axis. Exact arithmetic only. Named external lemmas and
   generic versus fixture scope are documented in derivation.md. *)
Needs["xAct`xTensor`"];
base=DirectoryName[$InputFileName];
checks=<||>;
check[name_,expr_]:=(checks[name]=TrueQ[expr];Print[name," = ",checks[name]]);
zero[a_]:=And@@Thread[Flatten[{a}]==0];
DefManifold[Euclidean3,3,{aa,bb,cc,dd,ee,ff}];
DefMetric[1,gg[-aa,-bb],CD,{";","D"}];
DefTensor[oct[-aa,-bb,-cc],Euclidean3,Symmetric[{-aa,-bb,-cc}]];
check["xAct_rank3_symmetry",ToCanonical[oct[-aa,-bb,-cc]-oct[-cc,-aa,-bb]]===0];
(* O1: lower bounds hold for each SAME rotation by the named spectral lemmas. *)
check["O1_generic_weighted_combination",Resolve[ForAll[{rq,ro,bq,bo,qs,os},Implies[rq>=bq>=0&&ro>=bo>=0&&qs>0&&os>0,(rq^2-bq^2)/qs^2+(ro^2-bo^2)/os^2>=0]],Reals]];
q=DiagonalMatrix[{-1,0,1}];
o=Table[Which[{i,j,k}=={1,1,1},2,Sort[{i,j,k}]=={1,2,2}||Sort[{i,j,k}]=={1,3,3},-1,True,0],{i,3},{j,3},{k,3}];
a=ArrayReshape[o,{3,9}];
check["O1_oct_STF",zero[Table[Sum[o[[i,i,k]],{i,3}],{k,3}]]];
check["O1_oct_norm_and_Gram",Total[Flatten[o]^2]==10&&a.Transpose[a]==DiagonalMatrix[{6,2,2}]];
check["O1_Q_scaling_lower_equals_identity_upper",Total[(Sort[Eigenvalues[q]]-Sort[Eigenvalues[2q]])^2]==2&&Tr[Transpose[q-2q].(q-2q)]==2];
check["O1_O_scaling_lower_equals_identity_upper",Total[(Sqrt[Sort[Eigenvalues[a.Transpose[a]]]]-Sqrt[Sort[Eigenvalues[4a.Transpose[a]]]])^2]==10&&Total[Flatten[o-2o]^2]==10];
check["O1_zero_repeated_spectra",Sort[Eigenvalues[0q]]=={0,0,0}&&Sort[Eigenvalues[a.Transpose[a]]]=={2,2,6}];
(* O2: homogeneous quaternion numerator, valid even when some components vanish. *)
rnum={{w^2+x^2-y^2-z^2,2(x y-w z),2(x z+w y)},{2(x y+w z),w^2-x^2+y^2-z^2,2(y z-w x)},{2(x z-w y),2(y z+w x),w^2-x^2-y^2+z^2}};
norm2=w^2+x^2+y^2+z^2;
check["O2_homogeneous_orthogonality",zero[Expand[rnum.Transpose[rnum]-norm2^2 IdentityMatrix[3]]]];
check["O2_homogeneous_det",Expand[Det[rnum]-norm2^3]===0];
xx={x,y,z};vv={v1,v2,v3}; ss=1+xx.xx;
chart=Prepend[xx,1]/Sqrt[ss];jac=Table[D[chart[[i]],xx[[j]]],{i,4},{j,3}];
check["O2_chart_normalization",FullSimplify[chart.chart==1,Element[xx,Reals]]];
check["O2_chart_Gram",zero[FullSimplify[Transpose[jac].jac-(IdentityMatrix[3]/ss-Outer[Times,xx,xx]/ss^2),Element[xx,Reals]]]];
check["O2_derivative_bound_SOS",Together[vv.vv/ss-vv.(IdentityMatrix[3]/ss-Outer[Times,xx,xx]/ss^2).vv-(xx.vv)^2/ss^2]===0];
(* Cell component distance d=dist(0,[lo,hi]) supplies norm>=m. *)
check["O2_cell_component_lower_norm",Resolve[ForAll[{lo,hi,t},Implies[lo<=t<=hi,Piecewise[{{lo^2,lo>0},{hi^2,hi<0}},0]<=t^2]],Reals]];
check["O2_center_cell_radius",Resolve[ForAll[{dx,dy,dz,hx,hy,hz},Implies[hx>=0&&hy>=0&&hz>=0&&-hx<=dx<=hx&&-hy<=dy<=hy&&-hz<=dz<=hz,dx^2+dy^2+dz^2<=hx^2+hy^2+hz^2]],Reals]];
check["O2_grid_radius_and_rational_upper",FullSimplify[2Sqrt[3/(4m^2)]==Sqrt[3]/m&&Sqrt[3]/m<=7/(4m),m>0]];
check["O2_planar_rational_rotation",With[{r={{3/5,-4/5,0},{4/5,3/5,0},{0,0,1}}},r.Transpose[r]==IdentityMatrix[3]&&Det[r]==1]];
(* O3: generic component inequalities, summed then divided by positive M. *)
bounds=li<=si<=ui&&l0<=s0<=u0;
check["O3_certain_inclusive_implies_exact",Resolve[ForAll[{li,si,ui,l0,s0,u0},Implies[bounds&&li>=u0,si>=s0]],Reals]];
check["O3_exact_implies_possible_inclusive",Resolve[ForAll[{li,si,ui,l0,s0,u0},Implies[bounds&&si>=s0,ui>=l0]],Reals]];
check["O3_count_division",Resolve[ForAll[{cl,ce,cu,mm},Implies[mm>0&&cl<=ce<=cu,(1+cl)/mm<=(1+ce)/mm<=(1+cu)/mm]],Reals]];
pts={0,1,2,3,10};scores=Table[Sort[Delete[Abs[pts-pts[[i]]],i]][[2]],{i,5}];
check["O3_scalar_k2_scores",scores=={2,1,1,2,8}];
check["O3_wide_decision_fixture",(1+Count[Thread[{0,0,0,0}>=10],True])/5==1/5&&(1+Count[Thread[{3,3,3,3}>=7],True])/5==1/5];
check["O3_tie_fixture",(1+Count[Thread[{0,0,0,0}>=0],True])/5==1];
check["O3_M1000_thresholds",Floor[1000/20]-1==49&&Floor[1000/20]==50&&Ceiling[Sqrt[999]]==32&&50/1000<=1/20&&51/1000>1/20];
check["O3_M301_thresholds",Floor[301/20]-1==14&&Floor[301/20]==15&&Ceiling[Sqrt[300]]==18&&15/301<=1/20&&16/301>1/20];
(* J2: exact structural factor, no rounded-rank decisions. *)
b={3/5,4/5};normal={-4/5,3/5};cov=4Outer[Times,b,b];rr=2b;off=rr+normal;
check["J2_factor_rank_and_PSD",b.b==1&&Det[cov]==0&&Sort[Eigenvalues[cov]]=={0,4}&&MatrixRank[cov]==1];
check["J2_factor_support_and_quadratic",normal.rr==0&&b.rr==2&&(b.rr)^2/4==1&&rr.PseudoInverse[cov].rr==1];
check["J2_factor_off_support",normal.off==1&&off-b(b.off)==normal];
(* Independent Z~N(0,1), S uniform +/-1; (X,Y)=(Z,S Z). *)
phi[t_,u_]:=(Exp[-(t+u)^2/2]+Exp[-(t-u)^2/2])/2;
check["J2_gaussian_marginal_characteristic",FullSimplify[phi[t,0]==Exp[-t^2/2]&&phi[0,u]==Exp[-u^2/2]]];
check["J2_covariance_zero",FullSimplify[-D[phi[t,u],t,u]/.{t->0,u->0}]===0];
check["J2_unit_marginal_variances",(-D[phi[t,u],{t,2}]/.{t->0,u->0})==1&&(-D[phi[t,u],{u,2}]/.{t->0,u->0})==1];
check["J2_nongaussian_joint_mixed_moment",(D[phi[t,u],{t,2},{u,2}]/.{t->0,u->0})==3&&3!=1];
check["J2_nongaussian_joint_cf_witness",FullSimplify[phi[1,1]-Exp[-1]>0]];
obligations=<|
"O1_weighted_lower_and_scaling"->And@@Values[KeySelect[checks,StringStartsQ["O1_"]]],
"O2_quaternion_rotation_and_chart_derivative"->And@@Values[KeySelect[checks,StringStartsQ["O2_"]]],
"O3_interval_inclusive_counts"->And@@Values[KeySelect[checks,StringStartsQ["O3_"]]],
"J2_rational_factor_support"->And@@Values[KeySelect[checks,StringStartsQ["J2_factor_"]]],
"J2_gaussian_marginal_counterexample"->And@@Values[KeySelect[checks,Function[k,StringStartsQ[k,"J2_"]&&!StringStartsQ[k,"J2_factor_"]]]]|>;
out=<|"axis"->"wolfram_xact","contract_sha256"->"5ff7f84db01b6871f74f7c60b5c36430a4cae93735466e277bd9c4019ab22723","wolfram_version"->System`$Version,"xact_version"->ToString[xAct`xTensor`$Version,InputForm],"checks"->checks,"contract_checks"->obligations,"domain_assumption_diff"->{},"counterexample"->Null,"all_pass"->And@@Values[checks]|>;
Export[FileNameJoin[{base,"checks.json"}],out,"RawJSON"];
Print["AXIS_ALL_PASS = ",out["all_pass"]];
Exit[If[TrueQ[out["all_pass"]],0,1]];
