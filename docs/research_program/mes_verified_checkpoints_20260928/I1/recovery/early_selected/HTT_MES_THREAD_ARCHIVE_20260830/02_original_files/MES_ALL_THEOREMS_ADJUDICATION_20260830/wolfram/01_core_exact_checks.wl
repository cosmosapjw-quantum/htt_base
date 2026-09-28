(* Exact finite-dimensional checks supporting, but not replacing, analytic proofs. *)
ClearAll[a,b,c,d,e,u,v,w,x,y,z,s2,s3,S,vec,m0,m1,m2,m3,m4,gram,krylov,beta,q2,BQ,Mq,t,r,L,eta,J,A,mu,n,gs,X];
S={{a,c,d},{c,b,e},{d,e,-a-b}};
vec={u,v,w}; s2=Tr[S.S]; s3=Tr[S.S.S];
m0=vec.vec; m1=vec.S.vec; m2=vec.S.S.vec;
m3=s2 m1/2+s3 m0/3; m4=s2 m2/2+s3 m1/3;
gram={{m0,m1,m2},{m1,m2,m3},{m2,m3,m4}};
krylov=Transpose[{vec,S.vec,S.S.vec}];
beta={x,y,z}; q2=s2;
BQ=Table[
 beta[[i]] S[[j,k]]+beta[[j]] S[[i,k]]+beta[[k]] S[[i,j]]
 -(2/5)(KroneckerDelta[i,j](S.beta)[[k]]+KroneckerDelta[i,k](S.beta)[[j]]+KroneckerDelta[j,k](S.beta)[[i]]),
 {i,3},{j,3},{k,3}];
Mq=q2 IdentityMatrix[3]+(6/5)S.S;
rfun=(2(1-t+t^2)+6/5)/(2(1-t+t^2)+(6/5)t^2);
eta=DiagonalMatrix[{-1,1,1,1}];
L={{Cosh[r],0,0,Sinh[r]},{0,1,0,0},{0,0,1,0},{Sinh[r],0,0,Cosh[r]}};
J=DiagonalMatrix[{0,x,y,z}]; A=Transpose[L].J.L;
<|
 "CayleyHamiltonResidual" -> Simplify[MatrixPower[S,3]-s2 S/2-s3 IdentityMatrix[3]/3],
 "DiscriminantIdentityResidual" -> Factor[Discriminant[CharacteristicPolynomial[S,lam],lam]-(s2^3/2-3s3^2)],
 "TraceFourthResidual" -> Simplify[Tr[MatrixPower[S,4]]-s2^2/2],
 "GramKrylovResidual" -> Simplify[Det[gram]-Det[krylov]^2],
 "BQTraceResidual" -> Simplify[Table[Sum[BQ[[i,i,k]],{i,3}],{k,3}]],
 "BQContractionResidual" -> Simplify[Table[Sum[BQ[[i,j,k]]S[[j,k]],{j,3},{k,3}],{i,3}]-Mq.beta],
 "BQNormResidual" -> Simplify[Sum[BQ[[i,j,k]]^2,{i,3},{j,3},{k,3}]-3 beta.Mq.beta],
 "ConditionDerivative" -> Factor[D[rfun,t]],
 "ConditionAtOneFifth" -> Simplify[rfun/.t->1/5],
 "LorentzResidual" -> FullSimplify[Transpose[L].eta.L-eta],
 "TimelikeKernelResidual" -> FullSimplify[A.{Cosh[r],0,0,-Sinh[r]}]
|>
