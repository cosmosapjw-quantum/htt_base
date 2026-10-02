(* CAS-12 fixed linear collision moments, Thomson harmonics, Planck, derivative. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[PhaseM,3,{a,b}];DefMetric[1,wm[-a,-b],DC];
DefTensor[ell[a,-b],PhaseM];
xact=<|"metricTrace"->TrueQ[ToCanonical[ContractMetric[wm[a,b]wm[-a,-b]]-3]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[bpar,en,mu,aamp,nn,xx];
L=Table[lop[i,j],{i,3},{j,3}];
Mass=DiagonalMatrix[Array[mw,3]];MassInv=DiagonalMatrix[1/Array[mw,3]];
Ladj=MassInv.Transpose[L].Mass;
f=Array[ff,3];g=Array[gg,3];K=Array[kk,3];
adjointIdentity=zero[K.Mass.L.(f-g)-(Ladj.K).Mass.(f-g)];
(* A retained adjoint null mode has unchanged moment, irrespective of f-g. *)
Lnull=DiagonalMatrix[{0,-lop[2,2],-lop[3,3]}];
Knull={1,0,0};
nullMoment=zero[Knull.Mass.Lnull.(f-g)];
c01=adjointIdentity&&nullMoment;
Pmu=3(1+mu^2)/(16Pi);
pvals=Table[FullSimplify[2Pi Integrate[Pmu LegendreP[l,mu],{mu,-1,1}]],{l,0,8}];
legendreExpansion=zero[Pmu-(LegendreP[0,mu]/(4Pi)+LegendreP[2,mu]/(8Pi))];
c02=legendreExpansion&&zero[pvals-{1,0,1/10,0,0,0,0,0,0}];
Fb=1/(Exp[bpar en]-1);Wplanck=Fb(1+Fb);
small=Series[en^2 Wplanck,{en,0,2}];
coefficient=Normal[small]/.en->0;
formal=zero[coefficient-1/bpar^2]&&
 zero[Wplanck-Exp[bpar en]/(Exp[bpar en]-1)^2];
c03=formal;
(* q is a finite moment-orthogonal representative. Continuum compact q
   and differentiation through its integral remain analytical inputs. *)
kvec=Array[kv,3];qvec={kvec[[2]],-kvec[[1]],0};
base=Array[bv,3];fn=base+aamp Sin[nn xx]qvec;
dfn=D[fn,xx];
moment=zero[kvec.qvec]&&zero[kvec.(fn-base)]&&zero[kvec.dfn];
positive=Array[pos,3];dvec=Array[der,3];
AV=dvec/Sqrt[positive];BV=kvec Sqrt[positive];
lagrange=(AV.AV)(BV.BV)-(AV.BV)^2-
 Sum[(AV[[i]]BV[[j]]-AV[[j]]BV[[i]])^2,{i,1,2},{j,i+1,3}];
c04=moment&&zero[FullSimplify[lagrange,Assumptions->And@@Thread[positive>0]]]&&
 zero[dfn-aamp nn Cos[nn xx]qvec];
checks=<|"CAS-12-C01"->c01,"CAS-12-C02"->c02,"CAS-12-C03"->c03,"CAS-12-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"analytic_obligations_not_checked"->{"small-en analytic limit and ultraviolet integrability", "continuum q construction and differentiation under integral"},
 "intermediate"-><|"Thomson_moments_l0_to_l8"->pvals,"Planck_formal_series"->ToString[InputForm[small]],
 "weighted_Cauchy_residual"->ToString[InputForm[FullSimplify[lagrange]]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
