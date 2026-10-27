(* Loop D: exact finite orthonormal-frame 3-Ricci calculation.
   Convention [e_i,e_j]=C^k_ij e_k; R(X,Y)Z= nabla_X nabla_Y Z - nabla_Y nabla_X Z - nabla_[X,Y] Z.
   Orthonormal e_i, lengths measured in physical units; n and a are inverse length. *)
ClearAll[n1,n2,n3,aa,n,strC,gam,curv,ric,eps];
n=DiagonalMatrix[{n1,n2,n3}]; av={aa,0,0};
eps[i_,j_,k_]:=Signature[{i,j,k}];
strC[i_,j_,k_]:=Sum[eps[i,j,l] n[[l,k]],{l,1,3}]+av[[i]] KroneckerDelta[j,k]-av[[j]] KroneckerDelta[i,k];
gam[i_,j_,k_]:=(strC[i,j,k]-strC[j,k,i]+strC[k,i,j])/2;
curv[l_,m_,i_,j_]:=Sum[gam[j,m,k] gam[i,k,l]-gam[i,m,k] gam[j,k,l]-strC[i,j,k] gam[k,m,l],{k,1,3}];
ric=FullSimplify[Table[Sum[curv[i,j,i,k],{i,1,3}],{j,1,3},{k,1,3}]];
Print["RIC_GENERAL=",InputForm[ric]];
Print["RIC_CLASS_B_n1_0=",InputForm[FullSimplify[ric/.n1->0]]];
cases=<|"I"->{0,0,0,0},"II"->{u,0,0,0},"IX"->{u,u,u,0},"V"->{0,0,0,v},"VII0_flat"->{0,u,u,0},"VII0_generic"->{0,u,v,0}|>;
Do[rr=FullSimplify[ric/.Thread[{n1,n2,n3,aa}->cases[key]]];Print[key," Ric=",InputForm[rr]," R=",InputForm[Tr[rr]]],{key,Keys[cases]}];
