(* R7 independent Wolfram+xAct axis. Finite algebraic implications only. *)
ClearAll["Global`*"];
axisDir = DirectoryName[$InputFileName];
repoRoot = Nest[DirectoryName, axisDir, 5];
contract = Import[FileNameJoin[{repoRoot, ".agent-harness/runs/TENSOR-JOINT-R7-20260908/CAS_CONTRACT.json"}], "RawJSON"];
certificate = Import[FileNameJoin[{repoRoot, "docs/generated/tensor_joint_r7/axial_certificate_source.json"}], "RawJSON"];
Needs["xAct`xTensor`"];
checks = AssociationThread[contract["target"]["exact_test_obligations"], ConstantArray[False, 7]];
evidence = <||>;
record[key_, value_, detail_] := (AssociateTo[checks, key -> TrueQ[value]]; AssociateTo[evidence, key -> detail]; Print[key, " = ", TrueQ[value]]);

(* T1: exact independent component tensor and invariant checks. *)
qMat = DiagonalMatrix[{-1, 0, 1}];
triples = {{1,1,1},{1,1,2},{1,1,3},{1,2,2},{1,2,3},{1,3,3},{2,2,2},{2,2,3},{2,3,3},{3,3,3}};
entries = {1,0,0,-2,1,1,1,-1,-1,1};
oArray = ConstantArray[0,{3,3,3}];
Do[Do[oArray[[Sequence@@perm]] = entries[[ii]], {perm,Permutations[triples[[ii]]]}],{ii,10}];
traceO = Table[Sum[oArray[[ii,jj,jj]],{jj,3}],{ii,3}];
contraction = Table[Sum[oArray[[ii,jj,kk]] qMat[[jj,kk]],{jj,3},{kk,3}],{ii,3}];
chi = Det[Transpose[{contraction,qMat.contraction,qMat.qMat.contraction}]];
symmetricO = And@@Table[And@@(oArray[[Sequence@@#]] == oArray[[Sequence@@ijk]] & /@ Permutations[ijk]),{ijk,Tuples[Range[3],3]}];
record["T1_trace_and_contraction", Tr[qMat]==0 && traceO=={0,0,0} && contraction=={0,-1,1} && chi==0 && symmetricO,
 <|"Q_trace"->Tr[qMat],"O_trace"->traceO,"O_contract_Q"->contraction,"chi"->chi,"symmetric"->symmetricO|>];
properSigns = Select[Tuples[{-1,1},3], Times@@#==1&];
rotationResiduals = Table[Flatten[Table[ss[[ii]] ss[[jj]] ss[[kk]] oArray[[ii,jj,kk]] + oArray[[ii,jj,kk]],{ii,3},{jj,3},{kk,3}]],{ss,properSigns}];
(* Distinct eigenvalues: commutator forces every offdiagonal entry to vanish. *)
rMat = Array[rr,{3,3}];
commutator = qMat.rMat-rMat.qMat;
offdiagonal = Flatten[Table[If[ii==jj,Nothing,FullSimplify[commutator[[ii,jj]]/(qMat[[ii,ii]]-qMat[[jj,jj]])]==rMat[[ii,jj]]],{ii,3},{jj,3}]];
record["T1_no_proper_signed_stabilizer", Length[properSigns]==4 && And@@offdiagonal && And@@(AnyTrue[#, #!=0&]& /@ rotationResiduals),
 <|"proper_axis_signs"->properSigns,"squared_residual_norms"->(Total[#^2]& /@ rotationResiduals),"distinct_eigenvalue_commutator"->TrueQ[And@@offdiagonal],"argument"->"RQ=QR with distinct eigenvalues forces diagonal R; orthogonality yields signs; determinant +1 selects these four. Nonzero residuals rule out O -> -O."|>];

(* T3: tensor algebra only. Spatial positive metric, rate derivative tau; Tbar depends only on tau. *)
DefManifold[Space3,3,{aa,bb,cc,dd,ee,ff}];
DefMetric[1,hh[-aa,-bb],CD,{"|","D"}];
DefParameter[tau];
DefTensor[qTensor[-aa,-bb],{Space3,tau},Symmetric[{-aa,-bb}]];
DefTensor[oTensor[-aa,-bb,-cc],{Space3,tau},Symmetric[{-aa,-bb,-cc}]];
DefTensor[dTensor[-aa],{Space3,tau}];
DefTensor[tbar[],{tau}];
DefConstantSymbol[theta];
normalizedResidual = ToCanonical[ParamD[tau][qTensor[-aa,-bb]/tbar[]] - ParamD[tau][qTensor[-aa,-bb]]/tbar[] + qTensor[-aa,-bb] ParamD[tau][tbar[]]/tbar[]^2];
stfDip[v_] := (CD[-aa][v[-bb]]+CD[-bb][v[-aa]])/2-hh[-aa,-bb] CD[cc][v[-cc]]/3;
propDip[index_] := -dTensor[index]/tbar[];
skyDip[index_] := dTensor[index]/tbar[];
propQuad = qTensor[-aa,-bb]/tbar[];
propOct = -oTensor[-aa,-bb,-cc]/tbar[];
sigmaProp = -ParamD[tau][propQuad] - stfDip[propDip] - (3/7) CD[cc][propOct];
sigmaSky = -ParamD[tau][qTensor[-aa,-bb]/tbar[]] + stfDip[skyDip] + (3/7) CD[cc][oTensor[-aa,-bb,-cc]/tbar[]];
sigmaResidual = ToCanonical[Expand[sigmaProp-sigmaSky]];
cOut = (CD[-aa][dTensor[-bb]/tbar[]]-CD[-bb][dTensor[-aa]/tbar[]])/2;
cProp = (CD[-aa][propDip[-bb]]-CD[-bb][propDip[-aa]])/2;
eQuad = (CD[-aa][CD[cc][qTensor[-bb,-cc]/tbar[]]] - CD[-bb][CD[cc][qTensor[-aa,-cc]/tbar[]]])/2;
omegaProp = -(3/theta) ParamD[tau][cProp]-cProp-(6/(5 theta)) eQuad;
omegaSky = (3/theta) ParamD[tau][cOut]+cOut-(6/(5 theta)) eQuad;
omegaResidual = ToCanonical[Expand[omegaProp-omegaSky]];
oddCurlResidual = ToCanonical[Expand[cProp+cOut]];
(* Independent scalar component quotient-rule check, with explicit T>0. *)
scalarNormalizedResidual = FullSimplify[D[qq[s]/tt[s],s]-(qq'[s]/tt[s]-qq[s]tt'[s]/tt[s]^2), Assumptions -> tt[s]>0];
record["T3_normalized_derivative_and_odd_signs", normalizedResidual===0 && scalarNormalizedResidual===0 && sigmaResidual===0 && omegaResidual===0 && oddCurlResidual===0,
 <|"xact_normalized_derivative_residual"->ToString[normalizedResidual,InputForm],"scalar_normalized_derivative_residual"->ToString[scalarNormalizedResidual,InputForm],"sigma_parity_residual"->ToString[sigmaResidual,InputForm],"omega_parity_residual"->ToString[omegaResidual,InputForm],"odd_curl_residual"->ToString[oddCurlResidual,InputForm],"manifold"->"Space3 (dimension 3)","metric"->"hh positive definite spatial metric; spacetime signature remains (-,+,+,+)","rate_parameter"->"tau; dot=c u.nabla, CD represents c h.nabla algebraically", "assumptions"->"Tbar>0, Theta>0, first-order geodesic hierarchy accepted; no independent physical closure proof; antisymmetrization has 1/2"|>];

(* T5: universal noncommutative word polynomial certificate of first-order inverse.
   A word denotes an ordered product of compatible matrices; {} denotes identity.
   Truncation is applied only AFTER multiplying, preserving all ordered products. *)
Clear[pmul,pnorm,ptrunc];
pnorm[p_List] := ({Expand[Total[#[[All,1]]]],#[[1,2]]}& /@ GatherBy[p,Last]);
pmul[p_List,q_List] := pnorm[Flatten[Table[{x[[1]] y[[1]],Join[x[[2]],y[[2]]]},{x,p},{y,q}],1]];
ptrunc[p_List,n_] := Select[({Normal[Series[#[[1]],{t,0,n}]],#[[2]]}& /@ p),First[#]=!=0&];
left = {{1,{}},{-t,{"E"}}};
invFirst = {{1,{}},{t,{"E"}}};
leftResidual = ptrunc[pmul[left,invFirst],1];
rightResidual = ptrunc[pmul[invFirst,left],1];
kPoly = pmul[pmul[{{-t,{"C"}}},invFirst],{{1,{"A"}}}];
kFirst = ptrunc[kPoly,1];
record["T5_first_order_inverse_coefficient", leftResidual=={{1,{}}} && rightResidual=={{1,{}}} && kFirst=={{-t,{"C","A"}}},
 <|"left_product_mod_t2"->ToString[leftResidual,InputForm],"right_product_mod_t2"->ToString[rightResidual,InputForm],"K_first_order"->ToString[kFirst,InputForm],"derivative_at_zero"->"-C.A","proof_scope"->"Free associative algebra through first order; two-sided inverse coefficient unique when inverse exists at t=0. No entrywise commutativity assumption."|>];

(* T5 scalar cost follows from the norm implication on its stated real domain.
   hnorm and knorm are nonnegative because they are norms. No lower rank assumption. *)
scalarPremise = 0<f<1/36 && costC>0 && dnorm>0 && hnorm>=0 && knorm>=0 && knorm<=costC*f/(1-36 f) && dnorm<=knorm*hnorm;
scalarConclusion = hnorm^2>=dnorm^2*(1-36 f)^2/(costC^2*f^2);
scalarCounterexamples = Reduce[scalarPremise && Not[scalarConclusion],{f,costC,dnorm,hnorm,knorm},Reals];
record["T5_scalar_cost_implication", scalarCounterexamples===False,
 <|"counterexample_set"->ToString[scalarCounterexamples,InputForm],"denominator_conditions"->"0<f<1/36, c>0; d>0; h and k nonnegative norms","claim"->"Every cancellant obeys the lower bound, hence its minimum/infimum does; K=0 or f=0 with d!=0 is infeasible by the norm premise."|>];

(* T6 exact scalar vector supplied by the contract. *)
u0=1; v0=1; e0=1; g0=1/4;
oldInformation=u0-v0^2/e0;
newInformation=u0-v0^2/(e0+g0);
gain=Together[newInformation-oldInformation];
record["T6_scalar_information_one_fifth", oldInformation==0 && newInformation==1/5 && gain==1/5,
 <|"U"->1,"V"->1,"E"->1,"G"->"1/4","information_before"->ToString[oldInformation,InputForm],"information_after"->ToString[newInformation,InputForm],"gain"->ToString[gain,InputForm],"claim_scope"->"Fixed scalar Schur-complement example only"|>];

(* L10: accepted source-column identities and exact rational positivity.
   This does not reconstruct the historical operator or its integrals. *)
rat[s_String] := Module[{parts=StringSplit[s,"/"]}, If[Length[parts]!=2 || !And@@(StringMatchQ[#,DigitCharacter..]& /@ parts),Return[$Failed]]; FromDigits[parts[[1]]]/FromDigits[parts[[2]]]];
blocks=certificate["pivot_minors"];
mins=rat /@ Lookup[blocks,"determinant_squared"];
normalDets=rat /@ certificate["normal_block_determinants"];
rowDims={4,4,4,3,2,1};
sourceCols=Lookup[blocks,"source_ells"];
mIds=Lookup[blocks,"m"];
positivity=And@@(#>0& /@ Join[mins,normalDets]);
columnBindings=sourceCols=={{7,8,9,10},{7,8,9,10},{7,8,9,10},{7,8,9},{7,8},{7}};
rowBindings=certificate["complex_block_ranks"]==rowDims && mIds==Range[0,5] && Length /@ sourceCols==rowDims;
realRank=rowDims[[1]]+2 Total[Rest[rowDims]];
maxPivotEll=Max[Flatten[sourceCols]];
(* For integer L<10, m=0 block has at most max(0,L-6)<=3 columns, but 4 rows.
   At L=10, all six accepted full-row minors are present, so each attains its row bound. *)
belowTenCounterexample=Reduce[Element[ell,Integers] && 7<=ell<10 && ell-6>=4,ell,Reals];
record["L10_accepted_minors_and_minimal_cutoff", positivity && columnBindings && rowBindings && realRank==32 && certificate["real_stored_rank"]==32 && maxPivotEll==10 && belowTenCounterexample===False,
 <|"all_rational_minors_positive"->positivity,"all_normal_determinants_positive"->And@@(#>0& /@ normalDets),"source_ell_bindings_match"->columnBindings,"complex_row_ranks"->rowDims,"real_rank"->realRank,"minimal_source_cutoff"->maxPivotEll,"L7_to_L9_column_count_counterexamples"->ToString[belowTenCounterexample,InputForm],"L_below_7"->"Source band ell=7..L is empty and cannot have row rank 32", "ceiling"->"Implication from accepted rational minor values and accepted source-column identities. No reconstruction of the historical axial operator, numerical quadrature, or empirical result."|>];

allChecks = And@@Values[checks];
toolchainAligned = StringStartsQ[System`$Version,"15.0.0 "] && OrderedQ[{{1,2,0},ToExpression /@ StringSplit[xAct`xTensor`$Version[[1]],"."]}];
result = <|"checks"->checks,"domain_assumption_diff"->If[toolchainAligned,{}, {"Toolchain version is outside the contract pin"}],"counterexample"->If[allChecks,Null,<|"failed_obligations"->Keys[Select[checks,Not]]|>],"evidence"->evidence,"toolchain"-><|"wolfram"->System`$Version,"xTensor"->xAct`xTensor`$Version[[1]],"xPerm"->xAct`xPerm`$Version[[1]],"xTensor_file"->FindFile["xAct`xTensor`"]|>,"claim_ceiling"->contract["identity"]["claim_ceiling"],"exact_symbolic"->True,"high_precision_numeric_status"->"Not needed: all fixed values and witnesses evaluated exactly; no float acceptance.","rules"->"Exact rational arithmetic, FullSimplify with explicitly positive T, xAct ToCanonical and parameter derivative, real Reduce, finite enumeration, free noncommutative word algebra."|>;
Export[FileNameJoin[{axisDir,"engine_result.json"}],result,"RawJSON"];
Print["R7_RESULT_JSON=",ExportString[result,"RawJSON","Compact"->True]];
Exit[If[allChecks && toolchainAligned,0,1]];
