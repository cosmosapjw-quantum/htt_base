(* CAS-16 finite coherency projector and exact degree-eight sphere cubature. *)
$HistoryLength=0;Needs["xAct`xTensor`"];
DefManifold[RestM,3,{a,b}];DefMetric[1,hh[-a,-b],D3];
DefTensor[coh[-a,-b],RestM,Symmetric[{-a,-b}]];
xact=<|"coherencySymmetry"->TrueQ[ToCanonical[coh[-a,-b]-coh[-b,-a]]===0],
 "restMetricTrace"->TrueQ[ToCanonical[ContractMetric[hh[a,b]hh[-a,-b]]-3]===0]|>;
zero[v_]:=And@@(TrueQ[FullSimplify[#==0]]& /@ Flatten[{v}]);
Clear[mu,phi];
unit={1,0,0};Proj=IdentityMatrix[3]-Outer[Times,unit,unit];
J=Table[jv[i,k],{i,3},{k,3}];
Frob[m_]:=Tr[Transpose[m].m];
loss=Expand[Frob[J]-Frob[Proj.J.Proj]];
removed=Total[Flatten[Table[If[i>=2&&k>=2,0,J[[i,k]]^2],{i,3},{k,3}]]];
scalarGain=3/(8Pi) (4Pi);
c01=zero[Proj.Proj-Proj]&&zero[Transpose[Proj]-Proj]&&
 zero[loss-removed]&&zero[scalarGain-3/2]&&zero[1+scalarGain-5/2];
L=4;LC=6;LT=4;Dstar=Max[L+4,LC+2,LT+2];
Nmu=5;Nphi=9;
c02=Dstar==8&&Nphi>=Dstar+1&&2Nmu-1>=Dstar&&
 (4<Ceiling[(Dstar+1)/2])&&(8<Dstar+1);
(* Exact finite reduction: every Cartesian monomial x^a y^b z^c of
   total degree <=8 has azimuthal Fourier modes |m|<=a+b<=8. The 9th
   roots of unity annihilate every nonzero such mode, leaving the same
   azimuthal constant coefficient as the sphere integral. For even a,b,
   that coefficient multiplies (1-mu^2)^((a+b)/2) mu^c, a polynomial
   of degree a+b+c<=8. For odd a or b the constant coefficient is zero.
   Therefore nine root sums and nine GL5 moments verify all 165 monomials. *)
triples=Select[Tuples[Range[0,8],3],Total[#]<=8&];
muNodes=mu/.Solve[LegendreP[5,mu]==0,mu];
muWeights=FullSimplify[2/((1-#^2)(D[LegendreP[5,mu],mu]/.mu->#)^2)]& /@ muNodes;
muMoments=Table[FullSimplify[(If[k==0,Total[muWeights],Total[muWeights muNodes^k]])-
 If[EvenQ[k],2/(k+1),0]],{k,0,8}];
rootModes=Table[FullSimplify[Sum[Exp[2Pi I mode j/9],{j,0,8}]/9],{mode,-8,8}];
rootTarget=Table[If[mode==0,1,0],{mode,-8,8}];
muNodes4=mu/.Solve[LegendreP[4,mu]==0,mu];
muWeights4=FullSimplify[2/((1-#^2)(D[LegendreP[4,mu],mu]/.mu->#)^2)]& /@ muNodes4;
radial4=FullSimplify[Total[muWeights4 muNodes4^8]-2/9];
(* The Fourier coefficient of cos(phi)^8 at cos(8phi) is 1/128;
   eight azimuth nodes alias that nonzero mode to the constant mode. *)
underAzimuth=Coefficient[TrigReduce[Cos[phi]^8],Cos[8phi]];
c03=Length[triples]==165&&Max[Total /@ triples]==8&&
 zero[muMoments]&&zero[rootModes-rootTarget]&&
 TrueQ[FullSimplify[radial4!=0]]&&zero[underAzimuth-1/128];
checks=<|"CAS-16-C01"->c01,"CAS-16-C02"->c02,"CAS-16-C03"->c03|>;
result=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "xact_actions"->xact,"intermediate"-><|"monomial_count"->Length[triples],"GL5_moment_residuals"->muMoments,
 "azimuth_root_modes"->rootModes,
 "radial_4node_degree8_error"->ToString[InputForm[radial4]],
 "azimuth_8node_degree8_error"->ToString[InputForm[underAzimuth]]|>,
 "wolfram_version"->System`$Version,"xtensor_version"->ToString[InputForm[xAct`xTensor`$Version]]|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];
Exit[If[And@@Values[checks]&&And@@Values[xact],0,2]];
