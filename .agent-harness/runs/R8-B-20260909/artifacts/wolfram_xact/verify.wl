(* Independent R8 O4 exact derivation. No numerical fixtures or sibling results. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
Print["ENGINE_VERSION: ", System`$Version];
Print["XTENSOR_VERSION: ", xAct`xTensor`$Version];
DefManifold[Euclid3, 3, {a,b,c,d,e,f,h}];
DefMetric[1, gg[-a,-b], CD, {";","D"}];
DefTensor[uv[a], Euclid3];
DefTensor[vv[a], Euclid3];
DefTensor[wv[a], Euclid3];
DefConstantSymbol[amp];
qabs[i_,j_] := amp ((uv[i] vv[j]+vv[i] uv[j])/2-gg[i,j] uv[d] vv[-d]/3);
babs[i_] := (uv[d] vv[-d] wv[i]+uv[d] wv[-d] vv[i]+vv[d] wv[-d] uv[i])/3;
sabs[i_,j_,k_] := (uv[i] vv[j] wv[k]+uv[i] wv[j] vv[k]+vv[i] uv[j] wv[k]+vv[i] wv[j] uv[k]+wv[i] uv[j] vv[k]+wv[i] vv[j] uv[k])/6;
oabs[i_,j_,k_] := amp (sabs[i,j,k]-(gg[i,j] babs[k]+gg[i,k] babs[j]+gg[j,k] babs[i])/5);
canon[expr_] := ToCanonical[ContractMetric[Expand[expr]]];
xactResiduals = <|
 "rank2_trace" -> canon[gg[a,b] qabs[-a,-b]],
 "rank2_symmetry" -> canon[qabs[-a,-b]-qabs[-b,-a]],
 "rank3_trace" -> canon[gg[a,b] oabs[-a,-b,-c]],
 "rank3_swap12" -> canon[oabs[-a,-b,-c]-oabs[-b,-a,-c]],
 "rank3_swap23" -> canon[oabs[-a,-b,-c]-oabs[-a,-c,-b]]|>;
Print["XACT_RESIDUALS: ", InputForm[xactResiduals]];

(* Components give exact universal polynomials, including all full multiplicities. *)
uvec={u1,u2,u3}; vvec={v1,v2,v3}; wvec={w1,w2,w3};
q2[aa_,u_List,v_List] := Table[aa ((u[[i]] v[[j]]+v[[i]] u[[j]])/2-KroneckerDelta[i,j] (u.v)/3), {i,3},{j,3}];
o3[aa_,u_List,v_List,w_List] := Module[{bv=( (u.v) w+(u.w) v+(v.w) u)/3},
 Table[aa ((u[[i]] v[[j]] w[[k]]+u[[i]] w[[j]] v[[k]]+v[[i]] u[[j]] w[[k]]+v[[i]] w[[j]] u[[k]]+w[[i]] u[[j]] v[[k]]+w[[i]] v[[j]] u[[k]])/6-(KroneckerDelta[i,j] bv[[k]]+KroneckerDelta[i,k] bv[[j]]+KroneckerDelta[j,k] bv[[i]])/5),{i,3},{j,3},{k,3}]];
qt=q2[amp,uvec,vvec]; ot=o3[amp,uvec,vvec,wvec];
allzero[expr_] := And@@(TrueQ[Expand[#] === 0]& /@ Flatten[{expr}]);
componentResiduals = <|
 "rank2_symmetric" -> Flatten[qt-Transpose[qt]],
 "rank2_trace" -> {Tr[qt]},
 "rank2_vector_swap" -> Flatten[qt-q2[amp,vvec,uvec]],
 "rank2_compensated_sign" -> Flatten[qt-q2[-amp,-uvec,vvec]],
 "rank2_zero_amplitude" -> Flatten[q2[0,uvec,vvec]],
 "rank3_index_permutations" -> Flatten[Table[ot-Transpose[ot,permutation],{permutation,Permutations[{1,2,3}]}]],
 "rank3_vector_permutations" -> Flatten[Table[ot-o3[amp,vecs[[1]],vecs[[2]],vecs[[3]]],{vecs,Permutations[{uvec,vvec,wvec}]}]],
 "rank3_traces" -> Table[Sum[ot[[i,i,k]],{i,3}],{k,3}],
 "rank3_compensated_sign" -> Flatten[ot-o3[-amp,-uvec,vvec,wvec]],
 "rank3_zero_amplitude" -> Flatten[o3[0,uvec,vvec,wvec]]|>;
nvec={1-z^2,I (1+z^2),2z};
nullResiduals=<|
 "null_bilinear_norm" -> {nvec.nvec},
 "quadrupole_trace_removal" -> {Sum[qt[[i,j]] nvec[[i]] nvec[[j]],{i,3},{j,3}]-amp (uvec.nvec) (vvec.nvec)},
 "octopole_trace_removal" -> {Sum[ot[[i,j,k]] nvec[[i]] nvec[[j]] nvec[[k]],{i,3},{j,3},{k,3}]-amp (uvec.nvec) (vvec.nvec) (wvec.nvec)}|>;
componentChecks=Map[allzero,componentResiduals];
nullChecks=Map[allzero,nullResiduals];
xactChecks=Map[allzero,xactResiduals];
Print["COMPONENT_RESIDUAL_COUNTS: ", InputForm[Map[Length,componentResiduals]]];
Print["COMPONENT_CHECKS: ", InputForm[componentChecks]];
Print["NULL_CONE_CHECKS: ", InputForm[nullChecks]];
Print["ALL_EXPANDED_RESIDUALS: ", InputForm[Map[Expand,Join[Values[xactResiduals],Flatten[Values[componentResiduals]],Flatten[Values[nullResiduals]]]]]];
versionOK=StringStartsQ[System`$Version,"15.0.0 "] && OrderedQ[{{1,2,0},ToExpression /@ StringSplit[xAct`xTensor`$Version[[1]],"."]}];
checks=<|
 "O4_STF2_trace_sign_permutation" -> TrueQ[versionOK && And@@Lookup[xactChecks,{"rank2_trace","rank2_symmetry"}] && And@@Lookup[componentChecks,{"rank2_symmetric","rank2_trace","rank2_vector_swap","rank2_compensated_sign","rank2_zero_amplitude"}]],
 "O4_STF3_trace_sign_permutation" -> TrueQ[versionOK && And@@Lookup[xactChecks,{"rank3_trace","rank3_swap12","rank3_swap23"}] && And@@Lookup[componentChecks,{"rank3_index_permutations","rank3_vector_permutations","rank3_traces","rank3_compensated_sign","rank3_zero_amplitude"}]],
 "O4_null_cone_and_trace_removal" -> TrueQ[versionOK && And@@Values[nullChecks]]|>;
payload=<|"checks"->checks,"domain_assumption_diff"->{},"counterexample"->Null,
 "tool_versions"-><|"wolfram"->System`$Version,"xact_xTensor"->xAct`xTensor`$Version[[1]]|>,
 "subchecks"->Join[xactChecks,componentChecks,nullChecks],
 "exact_residual_count"->Length[Values[xactResiduals]]+Length[Flatten[Values[componentResiduals]]]+Length[Flatten[Values[nullResiduals]]]|>;
payloadFile = Last[$CommandLine];
exported = Export[payloadFile,payload,"RawJSON","Compact"->True];
If[!StringQ[exported] || !FileExistsQ[payloadFile], Exit[2]];
Exit[If[TrueQ[And@@Values[checks]],0,1]];
