import sympy as s
W = s.Matrix([[10,1,0],[2,8,1],[0,2,7],[6,3,2]])
G = W.T*W
detG = G.det()
multi_rank = W.rank()
single_rank = W[:1,:].rank()
print("G=", G.tolist()); print("det_G=", detG); print("multi_rank=", multi_rank, "single_rank=", single_rank)
ok = (detG==394584 and multi_rank==3 and single_rank==1)
print("PR222_SYMPY_PASS" if ok else "PR222_SYMPY_FAIL")
