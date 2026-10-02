(* CAS-06: static spherical curvature from metric and pointwise TOV jets. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b,d,e}];DefMetric[-1,met[-a,-b],CD];
xact=<|"riemannAntisymmetry"->TrueQ[ToCanonical[RiemannCD[-a,-b,-d,-e]+RiemannCD[-a,-b,-e,-d]]===0],
 "ricciSymmetry"->TrueQ[ToCanonical[RicciCD[-a,-b]-RicciCD[-b,-a]]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[rr,th,tt,az,kap,lam,al,eps0,r0,mu,q,pstar,cs,cc];
coords={tt,rr,th,az};F=1-2mf[rr]/rr-lam rr^2/3;
g=DiagonalMatrix[{-Exp[2nf[rr]],1/F,rr^2,rr^2 Sin[th]^2}];
gi=DiagonalMatrix[{-Exp[-2nf[rr]],F,1/rr^2,1/(rr^2 Sin[th]^2)}];
Gam=Table[Sum[gi[[i,l]](D[g[[l,j]],coords[[k]]]+D[g[[l,k]],coords[[j]]]-D[g[[j,k]],coords[[l]]])/2,{l,4}],{i,4},{j,4},{k,4}];
Riem=Table[D[Gam[[i,j,l]],coords[[k]]]-D[Gam[[i,j,k]],coords[[l]]]+
 Sum[Gam[[i,k,s]]Gam[[s,j,l]]-Gam[[i,l,s]]Gam[[s,j,k]],{s,4}],{i,4},{j,4},{k,4},{l,4}];
Ric=Table[Sum[Riem[[i,j,i,l]],{i,4}],{j,4},{l,4}];
Ein=Ric-g Sum[gi[[i,i]]Ric[[i,i]],{i,4}]/2;
tetrad={Exp[-nf[rr]],Sqrt[F],1/rr,1/(rr Sin[th])};
curv[i_,j_,k_,l_]:=g[[i,i]]Riem[[i,j,k,l]]tetrad[[i]]tetrad[[j]]tetrad[[k]]tetrad[[l]];
Ghat=Table[Ein[[i,i]]tetrad[[i]]^2,{i,4}];
Nfun=mf[rr]+kap al ef[rr] rr^3/2-lam rr^3/3;
mp=kap rr^2 ef[rr]/2;nup=Nfun/(rr^2 F);ep=-(1+al)ef[rr]nup/al;
sub1={Derivative[1][mf][rr]->mp,Derivative[1][nf][rr]->nup,Derivative[1][ef][rr]->ep};
mp2=FullSimplify[D[mp,rr]/.sub1];nup2=FullSimplify[D[nup,rr]/.sub1];
sub2={Derivative[2][mf][rr]->mp2,Derivative[2][nf][rr]->nup2};
reduce[v_]:=FullSimplify[v/.sub2/.sub1/.{mf[rr]->mu r0^3,ef[rr]->eps0,nf[rr]->0,rr->r0,th->Pi/2},
 Assumptions->r0>0&&al>0&&kap>0&&1-(2mu+lam/3)r0^2>0];
curvPairs={{1,2,1,2},{1,3,1,3},{1,4,1,4},{2,3,2,3},{2,4,2,4},{3,4,3,4}};
curvAt=Map[reduce[curv@@#]&,curvPairs];
Gat=Map[reduce,Ghat];
p0=al eps0;Cpar=2mu+lam/3;B=mu+kap p0/2-lam/3;
expectedCurv={kap(eps0+p0)/2-2mu-lam/3,B,B,kap eps0/2-mu+lam/3,
 kap eps0/2-mu+lam/3,Cpar};
expectedG={kap eps0+lam,kap p0-lam,kap p0-lam,kap p0-lam};
(* Also check every off-diagonal Einstein component and Riemann pair coupling. *)
allPairs={{1,2},{1,3},{1,4},{2,3},{2,4},{3,4}};
mixedR=Flatten[Table[If[i==j,{},reduce[curv[allPairs[[i,1]],allPairs[[i,2]],
 allPairs[[j,1]],allPairs[[j,2]]]]],{i,6},{j,i+1,6}]];
c01parts={zero[Gat-expectedG],zero[curvAt-expectedCurv],zero[mixedR],
 zero[Table[If[i==j,0,reduce[Ein[[i,j]]]],{i,4},{j,4}]]};
c01=And@@c01parts;
accmag=cs^2 Abs[B] r0/Sqrt[1-Cpar r0^2];
accComputed=cs^2 Abs[reduce[nup Sqrt[F]]];
weyl=mu-kap eps0/6;
weylDerivative=reduce[D[mf[rr]/rr^3-kap ef[rr]/6,rr]];
weylSpecial=FullSimplify[weylDerivative/.{lam->0,mu->kap eps0/6}];
c02parts={zero[curvAt-expectedCurv],TrueQ[FullSimplify[accComputed==accmag,
 Assumptions->r0>0&&Cpar>0&&1-Cpar r0^2>0]],
 zero[weyl/.mu->kap eps0/6],
 zero[weylSpecial +kap (-(1+al)eps0 B r0/(al (1-Cpar r0^2))/.{mu->kap eps0/6,lam->0})/6]};
c02=And@@c02parts;
(* Scalar action and current for one fixed pstar,q. *)
s=(1+al)/(2al);X=q^2 Exp[-2nf[rr]]/2;
P=pstar X^s;PX=pstar s X^(s-1);PXX=pstar s(s-1)X^(s-2);
energy=2X PX-P;csratio=PX/(PX+2X PXX);
Jt=-q Exp[-2nf[rr]] PX;
volume=Exp[nf[rr]]rr^2 Sin[th]/Sqrt[F];
currentDiv=D[volume Jt,tt]/volume;
c03=zero[energy-P/al]&&zero[csratio-al]&&zero[currentDiv]&&
 zero[(P/.nf[rr]->0/.pstar->p0/(q^2/2)^s)-p0];
y=Unique["y"];divergence=cs^2 Abs[B]/Sqrt[Cpar] y/Sqrt[1-y^2];
(* Limit is from inside 0<y<1; C>0 and B!=0 are declared. *)
c04=zero[(accmag/.r0->y/Sqrt[Cpar])-divergence]&&
 TrueQ[FullSimplify[Limit[y/Sqrt[1-y^2],y->1,Direction->"FromBelow"]==Infinity]];
checks=<|"CAS-06-C01"->c01,"CAS-06-C02"->c02,"CAS-06-C03"->c03,"CAS-06-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"curvature"->ToString[InputForm[curvAt]],
 "Einstein"->ToString[InputForm[Gat]],"Weyl_derivative_special"->ToString[InputForm[weylSpecial]],
 "c01parts"->c01parts,"c02parts"->c02parts,"mixedR"->ToString[InputForm[mixedR]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
