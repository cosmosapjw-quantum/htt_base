(* CAS-02 exact frame stability identities and scalar inverse bound. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[GrstatM,4,{a,b}];DefMetric[-1,met[-a,-b],CD];
DefTensor[sym[-a,-b],GrstatM,Symmetric[{-a,-b}]];
xact=<|"symmetricForm"->TrueQ[ToCanonical[sym[-a,-b]-sym[-b,-a]]===0],
 "metricTrace"->TrueQ[ToCanonical[ContractMetric[met[a,b]met[-a,-b]]-4]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[h0,h1,h2,dd,R,EH,EZ,LL,MM];g=DiagonalMatrix[{-1,1,1,1}];
h1v=Array[h1,3];h2m=Table[If[i<=j,h2[i,j],h2[j,i]],{i,3},{j,3}];
S=Join[{Prepend[-h1v/2,h0]},MapThread[Prepend,{h2m,-h1v/2}]];
frobenius=Tr[Transpose[S].S];
c01=zero[frobenius-(h0^2+h1v.h1v/2+Tr[Transpose[h2m].h2m])]&&
 zero[Tr[Transpose[g].g]-4];
S1=Table[If[i<=j,s1[i,j],s1[j,i]],{i,4},{j,4}];
S2=Table[If[i<=j,s2[i,j],s2[j,i]],{i,4},{j,4}];
u1=Array[v1,4];u2=Array[v2,4];du=u2-u1;
dlambda=u2.S2.u2-u1.S1.u1;
anchor1=u2.(S2-S1).u2+du.S1.u2+u1.S1.du;
anchor2=u1.(S2-S1).u1+du.S2.u1+u2.S2.du;
c02=zero[dlambda-anchor1]&&zero[dlambda-anchor2];
dv=Array[dd,3];d2=dv.dv;
map=Prepend[dv,Sqrt[1+d2]];
Jac=Table[D[map[[i]],dv[[j]]],{i,4},{j,3}];
Gram=Transpose[Jac].Jac; expectedGram=IdentityMatrix[3]+Outer[Times,dv,dv]/(1+d2);
eigens=Factor[CharacteristicPolynomial[Gram,z]];
expectedPoly=-(z-1)^2(z-(1+2d2)/(1+d2));
rapidity=zero[Sinh[R]^2/(1+Sinh[R]^2)-Tanh[R]^2]&&
 TrueQ[FullSimplify[v/(1+v)<=w/(1+w),Assumptions->0<=v<=w]];
c03=zero[Gram-expectedGram]&&zero[eigens-expectedPoly]&&TrueQ[rapidity];
(* Finite Cauchy certificate for Euclidean components and algebraic bound.
   The op-norm inequalities and triangle inequality use the declared
   Euclidean operator/Frobenius norms. *)
x=Array[xx,4];y=Array[yy,4];
cauchyResidual=Expand[(x.x)(y.y)-(x.y)^2-
 Sum[(x[[i]]y[[j]]-x[[j]]y[[i]])^2,{i,1,3},{j,i+1,4}]];
lambdaBound=MM^2 EH+2MM LL EZ;
Bbound=EH+2lambdaBound;
c04=zero[cauchyResidual]&&zero[Bbound-((1+2MM^2)EH+4MM LL EZ)]&&
 TrueQ[FullSimplify[ForAll[{EH,EZ,MM,LL},EH>=0&&EZ>=0&&MM>=1&&LL>=0,
 EH+2(MM^2 EH+2MM LL EZ)<=(1+2MM^2)EH+4MM LL EZ]]];
checks=<|"CAS-02-C01"->c01,"CAS-02-C02"->c02,"CAS-02-C03"->c03,"CAS-02-C04"->c04|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"JacobianGram"->ToString[InputForm[Gram]],
 "JacobianCharacteristicPolynomial"->ToString[InputForm[eigens]],
 "rapidityBound"->ToString[InputForm[rapidity]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
