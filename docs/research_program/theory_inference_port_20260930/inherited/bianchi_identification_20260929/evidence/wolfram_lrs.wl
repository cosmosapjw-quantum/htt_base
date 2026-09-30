ClearAll["Global`*"];
xx={t,x,y,z}; metric=DiagonalMatrix[{-c^2,aa[t]^2,aa[t]^2,bb[t]^2}];
fields={{0,1,0,0},{0,0,1,0},{0,-q*y,q*x,1}};
lie[v_]:=Table[Sum[v[[k]] D[metric[[i,j]],xx[[k]]]+metric[[k,j]] D[v[[k]],xx[[i]]]+metric[[i,k]] D[v[[k]],xx[[j]]],{k,4}],{i,4},{j,4}];
br[v_,w_]:=Table[Sum[v[[k]] D[w[[i]],xx[[k]]]-w[[k]] D[v[[i]],xx[[k]]],{k,4}],{i,4}];
spatialDet=Det[Transpose[fields[[All,2;;4]]]];
coframe={{Cos[q*z],Sin[q*z],0},{-Sin[q*z],Cos[q*z],0},{0,0,1}};
coframeMetric=Simplify[Transpose[coframe].DiagonalMatrix[{aa[t]^2,aa[t]^2,bb[t]^2}].coframe];
h1=Derivative[1][aa][t]/aa[t];h3=Derivative[1][bb][t]/bb[t];theta=2h1+h3;
shearNorm=Factor[2(h1-theta/3)^2+(h3-theta/3)^2];
<|"LieDerivatives"->Simplify[lie/@fields],"Bracket31"->br[fields[[3]],fields[[1]]],"Bracket32"->br[fields[[3]],fields[[2]]],"TransitivityDeterminant"->spatialDet,"CoframeMetric"->coframeMetric,"ShearContraction"->shearNorm|>
