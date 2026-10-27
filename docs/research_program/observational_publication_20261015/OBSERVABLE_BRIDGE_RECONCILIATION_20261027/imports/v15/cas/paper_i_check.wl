ClearAll[t];
phi=1-t^(3/4)+(3/4)(t-1);
den=(7+5t)/12;
aux=phi den-(3/32)(t-1)^2;
{Simplify[D[aux,{t,3}]-(35/256)(t-1)t^(-9/4),Assumptions->t>0],
 Table[Limit[D[aux,{t,k}],t->1],{k,0,2}],
 Simplify[(3/32)(225/4)(2/15)-45/64],
 Simplify[(3/8)(8/15)^2-8/75]}
