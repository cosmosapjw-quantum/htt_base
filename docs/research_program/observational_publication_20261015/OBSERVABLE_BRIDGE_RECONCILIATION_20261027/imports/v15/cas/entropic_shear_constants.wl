ClearAll["Global`*"];
curvature = D[-cc ii^(3/4), {ii,2}];
delta4 = 4 Pi Factorial[4]/(3*5*7*9);
entropyBoundSquared = Simplify[delta4*32 mm^(5/4)/(3 cc)];
angularMean[p_] := Integrate[Integrate[p,{ph,0,2 Pi}]/(2 Pi),{mu,-1,1}]/2;
e = {Sqrt[1-mu^2] Cos[ph],Sqrt[1-mu^2] Sin[ph],mu};
s0 = DiagonalMatrix[{1,1,-2}]/Sqrt[6];
s2 = DiagonalMatrix[{1,-1,0}]/Sqrt[2];
s1 = {{0,0,1},{0,0,0},{1,0,0}}/Sqrt[2];
p4 = LegendreP[4,mu];
slopes = FullSimplify[-angularMean[p4 (e.#.e)^2]& /@{s0,s1,s2}];
<|"curvature"->curvature,"Delta4"->delta4,
  "physical_epsilon_squared_factor"->entropyBoundSquared,
  "P4_response_eigenvalue_slopes_m0_m1_m2"->slopes|>
