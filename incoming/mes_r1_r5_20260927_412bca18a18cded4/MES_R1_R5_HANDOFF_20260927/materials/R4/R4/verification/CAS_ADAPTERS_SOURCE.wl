ClearAll["Global`*"];
dd={d,2d,4d};
aa=Table[{1,1/x,x},{x,dd}]; ii=FullSimplify[Inverse[aa],Assumptions->d>0];
v={x,y,z}; pr=IdentityMatrix[3]-Outer[Times,v,v];
ss={{s1,s3,s4},{s3,s2,s5},{s4,s5,-s1-s2}}; av={a1,a2,a3}; om={o1,o2,o3};
mom[p_]:=Total[(#[[2]] If[AnyTrue[#[[1]],OddQ],0,Times@@(If[#==0,1,Factorial2[#-1]]& /@ #[[1]])/Factorial2[Total[#[[1]]]+1]])& /@ CoefficientRules[Expand[p],v]];
mu=pr.ss.v+Cross[om,v];
ph=hh-av.v+v.ss.v;
norms=FullSimplify[{mom[(v.ss.v)^2]-2Tr[ss.ss]/15,mom[(pr.ss.v).(pr.ss.v)]-Tr[ss.ss]/5,mom[(av.v)^2]-av.av/3,mom[Cross[om,v].Cross[om,v]]-2om.om/3}];
f=1+ee Sin[kk (xx-cc nz tt)];
stream=FullSimplify[D[f,tt]+cc nz D[f,xx]];
<|"TestID"->"R4_CAS_ADAPTERS_SOURCE","ShellInverse"->ii,"InverseResidual"->FullSimplify[ii.aa-IdentityMatrix[3]],"AngularGramResiduals"->norms,"ExactCollisionlessResidual"->stream,"AtOriginSky"->(f/.{xx->0,tt->0}),"OriginDensityGradient"->(D[f,xx]/.{xx->0,tt->0})|>
