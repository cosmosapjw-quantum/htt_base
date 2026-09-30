$HistoryLength=0; Clear[L,U,m,t,a,r]; a=2 L U/(L+U); r=(U-L)/(L+U);
base=0<L<=U;
upper=Resolve[ForAll[{L,U,m},Implies[base&&L<=m<=U,Abs[(a-m)/m]<=r]],Reals];
endpoints=Resolve[ForAll[{L,U},Implies[base,Abs[(a-L)/L]==r&&Abs[(a-U)/U]==r]],Reals];
competitor=Resolve[ForAll[{L,U,t},Implies[base,r<=Max[Abs[(t-L)/L],Abs[(t-U)/U]]]],Reals];
result=<|"upper"->TrueQ[upper],"endpoints"->TrueQ[endpoints],"competitor"->TrueQ[competitor],"full_scope"->TrueQ[upper]&&TrueQ[endpoints]&&TrueQ[competitor],"raw_forms"->{ToString[InputForm[upper]],ToString[InputForm[endpoints]],ToString[InputForm[competitor]]}|>;
Print["CAS_JSON_BEGIN"];Print[ExportString[result,"RawJSON"]];Print["CAS_JSON_END"];Exit[0];
