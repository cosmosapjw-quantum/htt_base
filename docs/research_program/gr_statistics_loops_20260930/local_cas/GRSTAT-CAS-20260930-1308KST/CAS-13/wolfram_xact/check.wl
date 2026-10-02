(* CAS-13 TEFF finite polynomial, two-node moments, p=5/6 signs, minimax. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[MomentM,1,{i}];DefMetric[1,hm[-i,-i],DC];
xact=<|"oneDimMetricTrace"->TrueQ[ToCanonical[ContractMetric[hm[i,i1]hm[-i,-i1]]-1]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[a,b,u,d,y,m3,m4,c0,c3,c4,p,L,U,t];
psi1=ps0;psiPrime=ps1;psiSecond=ps2;
qlocal=c0+c3 y^3+c4 y^4;
localSol=Solve[{(qlocal/.y->1)==psi1,(D[qlocal,y]/.y->1)==psiPrime,
 (D[qlocal,{y,2}]/.y->1)==psiSecond},{c0,c3,c4}];
localCoeffs={c0->psi1-psiPrime/2+psiSecond/12,
 c3->psiPrime-psiSecond/3,c4->psiSecond/4-psiPrime/2};
third=psiThird[y]-(D[qlocal,{y,3}]/.localCoeffs);
c01=Length[localSol]==1&&zero[({c0,c3,c4}/.First[localSol])-({c0,c3,c4}/.localCoeffs)]&&
 zero[third-(psiThird[y]-6(c3/.localCoeffs)-24(c4/.localCoeffs)y)];
(* Ratios derive node equations; denominators positive for a<u,b>d>0. *)
ratioLower=(u^4-a^4)/(u^3-a^3);
ratioUpper=(b^4-d^4)/(b^3-d^3);
derivLower=FullSimplify[D[ratioLower,u]];
derivUpper=FullSimplify[D[ratioUpper,d]];
targetLower=u^2(3a^2+2a u+u^2)/(a^2+a u+u^2)^2;
targetUpper=d^2(3b^2+2b d+d^2)/(b^2+b d+d^2)^2;
wu=(m3-a^3)/(u^3-a^3);wb=(m3-d^3)/(b^3-d^3);
m4Lower=a^4+(m3-a^3)ratioLower;
m4Upper=b^4-(b^3-m3)ratioUpper;
nodeMoments=zero[(1-wu)a^3+wu u^3-m3]&&
 zero[(1-wu)a^4+wu u^4-m4Lower]&&
 zero[(1-wb)d^3+wb b^3-m3]&&
 zero[(1-wb)d^4+wb b^4-m4Upper];
endpointWeight=(m3-a^3)/(b^3-a^3);
endpointM4=(1-endpointWeight)a^4+endpointWeight b^4;
DiracNode=m3^(1/3);
Degenerate=zero[DiracNode^3-m3]&&zero[DiracNode^4-m3^(4/3)]&&
 zero[endpointM4-(a^4+(m3-a^3)(b^4-a^4)/(b^3-a^3))];
Lp=(1-wu)a^p+wu u^p;Up=(1-wb)d^p+wb b^p;
c02=zero[derivLower-targetLower]&&zero[derivUpper-targetUpper]&&
 nodeMoments&&Degenerate&&
 TrueQ[FullSimplify[targetLower>0,Assumptions->0<a<u]]&&
 TrueQ[FullSimplify[targetUpper>0,Assumptions->0<d<b]]&&
 zero[(Lp/.p->3)-m3]&&zero[(Up/.p->3)-m3];
(* Solve Hermite system afresh for each p. Compare the factorization and
   prove sign from positive polynomial coefficients on y>=0. *)
hermite[power_,edge_,node_]:=Module[{v0,v3,v4,poly,sol,q,res,delta,co},
 poly=v0+v3 y^3+v4 y^4;
 sol=Solve[{(poly/.y->edge)==edge^power,(poly/.y->node)==node^power,
 (D[poly,y]/.y->node)==power node^(power-1)},{v0,v3,v4}];
 q=poly/.First[sol];res=Factor[Together[y^power-q]];
 delta=3 edge^2+2 edge node+node^2;
 co=CoefficientList[Cancel[res delta/((y-edge)(y-node)^2)],y];
 {res,co,sol}];
h5=hermite[5,a,u];h6=hermite[6,a,u];
h5Upper=hermite[5,b,d];h6Upper=hermite[6,b,d];
posCoeffs[co_,edge_,node_]:=And@@(TrueQ[FullSimplify[#>0,
 Assumptions->edge>0&&node>0]]& /@ co);
signs=posCoeffs[h5[[2]],a,u]&&posCoeffs[h6[[2]],a,u]&&
 posCoeffs[h5Upper[[2]],b,d]&&posCoeffs[h6Upper[[2]],b,d];
(* Boundary branches are evaluated directly as Dirac/endpoint measures,
   never via u=a or d=b in a node ratio. *)
c03=signs&&zero[(h5[[1]]/.y->a)]&&zero[(h5[[1]]/.y->u)]&&
 zero[(h6[[1]]/.y->a)]&&zero[(h6[[1]]/.y->u)]&&
 zero[(h5Upper[[1]]/.y->b)]&&zero[(h6Upper[[1]]/.y->d)];
predict=2L U/(L+U);loss=(U-L)/(U+L);
equalEndpoints=zero[(predict-L)/L-loss]&&zero[(U-predict)/U-loss];
triangle=Resolve[ForAll[{t,L,U},0<L<=U,Abs[t-L]+Abs[t-U]>=U-L],Reals];
c04parts={equalEndpoints,TrueQ[triangle],
 TrueQ[FullSimplify[L<=predict<=U,Assumptions->0<L<=U]]};
c04=And@@c04parts;
checks=<|"CAS-13-C01"->c01,"CAS-13-C02"->c02,"CAS-13-C03"->c03,"CAS-13-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"analytic_obligations_not_checked"->{"general real p>4 principal representation theorem", "integrated bandpass Taylor remainder"},
 "intermediate"-><|"local_coefficients"->ToString[InputForm[localSol]],
 "lower_ratio_derivative"->ToString[InputForm[derivLower]],
 "upper_ratio_derivative"->ToString[InputForm[derivUpper]],
 "p5_residual"->ToString[InputForm[h5[[1]]]],"p6_residual"->ToString[InputForm[h6[[1]]]],
 "p5_coefficients"->ToString[InputForm[h5[[2]]]],"p6_coefficients"->ToString[InputForm[h6[[2]]]],
 "c04parts"->c04parts|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
