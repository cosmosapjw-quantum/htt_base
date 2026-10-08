# CAS-10-C04 SymPy finite polynomial proof

For real \(t\in[0,1]\), the admitted polynomial is
\(F=1-10t^3+15t^4-6t^5\). Direct differentiation gives
\(F'=-30t^2(1-t)^2\) and \(F''=-60t(1-t)(1-2t)\).
Substitution at 0 and 1 gives \(F(0)=1,F(1)=0\) and vanishing first
and second derivative jets.

Since \(0\leq t(1-t)\) and
\(1/4-t(1-t)=(t-1/2)^2\), one has
\(|F'|=30[t(1-t)]^2\leq 15/8\). Equality holds exactly at \(t=1/2\).

\(F'''=-60(1-6t+6t^2)\), whose complete real root set is
\(r_\pm=(3\pm\sqrt3)/6\), both in \((0,1)\). The endpoint values of
\(F''\) are zero; the values at \(r_-\) and \(r_+\) are respectively
\(-10/\sqrt3\) and \(+10/\sqrt3\). A positive absolute maximum of
\(F''\) in the interior occurs where \(F''\neq0\), and Fermat's theorem
then gives \(F'''=0\). Compactness ensures a maximum exists, so the
complete candidate set proves the global maximum \(10/\sqrt3\), with
equality exactly at the two stated roots.

Exact rational arithmetic yields
\((25/24)(14/15+9/400)=1147/1152=1-5/1152<1\).
The auxiliary bounds \(e^{1/25}<25/24\) and \(\sqrt3>12/7\) remain
assumed inputs. This proof makes no mollifier, probability, or science claim.
