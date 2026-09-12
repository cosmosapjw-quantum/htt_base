$HistoryLength=0;
Needs["xAct`xTensor`"];
DefManifold[JetSpace,3,{a,b,c,d}];
DefMetric[1,gg[-a,-b],CD,{";","D"}];
DefTensor[sig[-a,-b],JetSpace,Symmetric[{-a,-b}]];
DefConstantSymbol[th];
xactCheck=ToCanonical[Expand[(sig[a,b]/th)(sig[-a,-b]/th)/2-sig[a,b]sig[-a,-b]/(2 th^2)]]===0;
p1=FullSimplify[{
 (-qd+g+3 dv/7)/theta-(-qd/theta+g/theta+3 dv/(7 theta)),
 (3 cd/theta+cc-6 ee/(5 theta))/theta-(3 cd/theta^2+cc/theta-6 ee/(5 theta^2))},theta>0];
v=IdentityMatrix[8][[8]];rr=IdentityMatrix[8][[1;;4]];
checks=<|"P1_normalized_coefficients"->TrueQ[p1=={0,0} && xactCheck],
 "P2_mock6_squared_norms"->TrueQ[{1,2,1,2,1,2,1,2}.{1,2,1,2,1,2,1,2}==20 && Sqrt[8]^2==8 && Sqrt[5]^2==5 && Sqrt[3]^2==3],
 "J1_set_logic_and_allocation"->TrueQ[1-4/80==19/20 && TautologyQ[Equivalent[aa&&(bb||cc),(aa&&bb)||(aa&&cc)]]],
 "V08_fixture_ray"->TrueQ[rr.v=={0,0,0,0} && IdentityMatrix[8].v==v && v.v==1]|>;
Export[Last[$CommandLine],<|"checks"->checks,"versions"-><|"wolfram"->System`$Version,"xact"->xAct`xTensor`$Version[[1]]|>|>,"RawJSON"];
Exit[If[And@@Values[checks],0,1]];
