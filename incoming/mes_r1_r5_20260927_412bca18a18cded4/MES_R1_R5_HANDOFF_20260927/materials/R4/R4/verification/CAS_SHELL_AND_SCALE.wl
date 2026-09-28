ClearAll["Global`*"];
dd={d,2d,4d}; ww={-2,5,-2};
constraints=FullSimplify[{Total[ww],ww.dd,ww.(1/dd)},Assumptions->d>0];
pieces={-t,2d-3t,-2(4d-t)};
areas=FullSimplify[{-Integrate[pieces[[1]],{t,0,d}],-Integrate[pieces[[2]],{t,d,2d}],-Integrate[pieces[[3]],{t,2d,4d}]},Assumptions->d>0];
poly=kk+uu/x+bb x+mm x^2/2;
witness=FullSimplify[ww.(poly/.x->#& /@ dd)-kk,Assumptions->d>0];
hRate=70/ (648000/Pi*149597870700/1000*10^6);
uasYear=Pi/(180*3600*10^6)/(36525/100*86400);
bf=(3+3/7)*10^-5;
sigRate=3hRate bf;
<|"TestID"->"R4_CAS_SHELL_AND_SCALE","Weights"->ww,"Constraints"->constraints,
"PeanoAbsAreas"->areas,"SharpRemainder"->Total[areas] mm,
"QuadraticSaturator"->witness,"NoiseVarianceFactor"->ww.ww,"DeterministicEqualErrorFactor"->Total[Abs[ww]],
"ConstantNuisanceRetained"->Total[ww],
"H70PerSecond"->N[hRate,14],"H70MicroarcsecondsPerYear"->N[hRate/uasYear,14],
"DeclaredBenchmarkBsig"->N[bf,14],"DeclaredBenchmarkSigmaMicroarcsecondsPerYear"->N[sigRate/uasYear,14],
"DeclaredBenchmarkDriftRMSMicroarcsecondsPerYear"->N[sigRate/(Sqrt[5]uasYear),14],
"PublishedCoefficientErrorsOverBenchmarkDriftScale"->N[{23/100,46/100}/(sigRate/(Sqrt[5]uasYear)),10]|>
