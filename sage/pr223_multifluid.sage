v = var('v')
streams = [(1, vector([v,0,0])), (1, vector([-v,0,0]))]
F = sum(w*x for w,x in streams)
K = sum(w*x.outer_product(x) for w,x in streams)
tr = K.trace()
Pi = K - (tr/3)*identity_matrix(3)
Pi3 = (3*Pi).subs(v=1)
ok = (F == vector([0,0,0])) and (tr != 0) and (Pi != zero_matrix(3,3)) and Pi3.diagonal()==[4,-2,-2] and Pi3.trace()==0
print("first_moment=%s"%F); print("trace_K=%s"%tr); print("aniso_3Pi_diag=%s"%Pi3.diagonal())
print("PR223_SAGE_PASS" if ok else "PR223_SAGE_FAIL")
