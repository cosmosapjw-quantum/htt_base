$HistoryLength=0;
Needs["xAct`xTensor`"];
DefManifold[M,4,{a,b}]; DefMetric[-1,g[-a,-b],CD];
DefTensor[S[-a,-b],M,Symmetric[{-a,-b}]]; DefTensor[u[a],M];
xactChecks=<|
 "symmetric"->TrueQ[ToCanonical[S[-a,-b]u[a]u[b]-S[-b,-a]u[a]u[b]]===0],
 "raiseLower"->TrueQ[ToCanonical[ContractMetric[g[a,b]g[-b,-c]u[c]-u[a]]]===0]|>;
Clear[u0,u1,u2,u3,c,x0,x1,x2,x3,gam];
eta=DiagonalMatrix[{-1,1,1,1}]; uu={u0,u1,u2,u3};
ss=Array[s,{4,4}]; ss=(ss+Transpose[ss])/2;
h=Expand[uu.ss.uu]; bb=Expand[(ss+h eta).uu]; aa=2 c bb;
j=Expand[(ss.uu).eta.(ss.uu)+h^2]; shell=-u0^2+u1^2+u2^2+u3^2+1;
red[p_]:=PolynomialReduce[Together[p],{shell},{u0,u1,u2,u3}][[2]];
algebraResiduals={red[uu.bb],red[j-bb.eta.bb],red[j-aa.eta.aa/(4c^2)]};
algebra=And@@(TrueQ[Expand[#]===0]&/@algebraResiduals);
v={u1,u2,u3}; x={x1,x2,x3}; vx=v.x;
crosssum=Sum[(v[[i]] x[[j]]-v[[j]] x[[i]])^2,{i,1,3},{j,i+1,3}];
restIdentity=FullSimplify[(x.x-vx^2/gam^2)-(x.x+crosssum)/(1+v.v),Assumptions->{gam^2==1+v.v,gam>0}];
restExact=TrueQ[restIdentity===0];
controls=And[TrueQ[FullSimplify[((x.x-vx^2/gam^2)/.{u1->0,u2->0,u3->0,gam->1})==x.x]],TrueQ[FullSimplify[Equivalent[2 c x=={0,0,0},x=={0,0,0}],Assumptions->{c>0,Element[{c,x1,x2,x3},Reals]}]]];
checks=<|"mass_shell_algebra"->algebra,"rest_space_positive_identity"->restExact,"xact_tensor_symmetry"->And@@Values[xactChecks],"branches_controls"->controls|>;
result=<|"checks"->checks,"wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]],"xact_checks"->xactChecks,"rest_identity_residual"->ToString[InputForm[restIdentity]],"algebra_residuals"->(ToString[InputForm[#]]&/@algebraResiduals)|>;
Export[Last[$ScriptCommandLine],result,"RawJSON"];
Exit[If[And@@Values[checks],0,2]];
