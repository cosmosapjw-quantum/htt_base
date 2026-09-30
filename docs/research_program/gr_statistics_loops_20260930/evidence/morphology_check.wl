ClearAll["Global\`*"];
g=DiagonalMatrix[{-1,1,1,1}]; u={5/4,3/4,0,0}; uc=g.u;
rate=1; bone=rate(g+Outer[Times,uc,uc]);
hzero=bone[[1,1]]+Tr[bone[[2;;4,2;;4]]]/3;
hone=-2bone[[1,2;;4]];
htwo=bone[[2;;4,2;;4]]-Tr[bone[[2;;4,2;;4]]]/3 IdentityMatrix[3];
drot={0,15/8,0};
srot=ArrayFlatten[{{{{hzero}},-{drot}/2},{-Transpose[{drot}]/2,htwo}}];
q=u.srot.u; btwo=srot+q g; bb=btwo.u;
<|"h0"->hzero,"h1"->hone,"h2"->htwo,"baselineBu"->bone.u,"rotatedSuu"->q,"rotatedB"->btwo,"rotatedBu"->bb,"rotatedNorm"->bb.g.bb,"powerDifference"->(hone.hone-drot.drot),"invariantResidual"->Simplify[bb.g.bb-((srot.u).g.(srot.u)+q^2)]|>
