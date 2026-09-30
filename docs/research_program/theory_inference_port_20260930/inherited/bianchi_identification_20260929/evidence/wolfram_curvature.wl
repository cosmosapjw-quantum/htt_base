ClearAll["Global`*"];
nn=DiagonalMatrix[{n1,n2,n3}]; av={a,0,0};eps=Normal[LeviCivitaTensor[3]];
cc=Table[Sum[eps[[j,k,l]] nn[[l,i]],{l,3}]+av[[j]] KroneckerDelta[i,k]-av[[k]] KroneckerDelta[i,j],{i,3},{j,3},{k,3}];
gg=Table[(cc[[i,j,k]]-cc[[j,k,i]]+cc[[k,i,j]])/2,{i,3},{j,3},{k,3}];
rr=Table[Sum[gg[[m,k,l]] gg[[i,j,m]]-gg[[m,j,l]] gg[[i,k,m]]-cc[[m,j,k]] gg[[i,m,l]],{m,3}],{i,3},{l,3},{j,3},{k,3}];
sc=Expand[Sum[rr[[i,j,i,j]],{i,3},{j,3}]];
jac=Table[Expand[Sum[cc[[m,2,3]] cc[[i,1,m]]+cc[[m,3,1]] cc[[i,2,m]]+cc[[m,1,2]] cc[[i,3,m]],{m,3}]],{i,3}];
classB=Factor[sc/.n1->0];classA=Expand[sc/.a->0];
viii=Factor[(classA/.n3->-p)-(- (n1-n2)^2/2-p^2/2-p(n1+n2))];
minus=Reduce[n1>=0 && n2>=0 && p>0 && (classA/.n3->-p)>=0,{n1,n2,p},Reals];
<|"ScalarCurvature"->sc,"Jacobi123"->jac,"ClassB"->classB,"TypeVIIIIdentityResidual"->viii,"TypeVIIIorVIZeroPositiveImpossible"->minus,"TypeIXPositiveExample"->(classA/.{n1->1,n2->1,n3->1}),"TypeIXNegativeExample"->(classA/.{n1->1,n2->1,n3->5})|>
