P = Polyhedron(ieqs=[[0,1,0],[1,-1,0],[0,0,1],[1,0,-1],[1,-1,-1]], base_ring=QQ)  # x>=0,x<=1,y>=0,y<=1,x+y<=1
c = vector(QQ,[1,1])
joint_sup = max(c*vector(v) for v in P.vertices())
Pf = Polyhedron(ieqs=[[0,1,0],[1,-1,0],[0,0,1],[1,0,-1]], base_ring=QQ)
fact_sup = max(c*vector(v) for v in Pf.vertices())
prod_sup = 2
print("joint_sup=%s"%joint_sup); print("product_sup=%s"%prod_sup); print("strict_1_lt_2=%s"%(joint_sup<prod_sup)); print("factorized_joint_sup=%s"%fact_sup)
print("PR189_SAGE_PASS" if (joint_sup==1 and prod_sup==2 and joint_sup<prod_sup and fact_sup==2) else "PR189_SAGE_FAIL")
