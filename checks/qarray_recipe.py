# Inverse recipe: targets (E_cA, E_cB, E_cm, lever-arm matrix alpha) -> QArray Cdd/Cgd (non-Maxwell). Verify forward.
import numpy as np
from qarray import DotArray
EcA, EcB, Ecm = 4.0, 4.4, 0.8                       # meV
alpha = np.array([[0.27, 0.0675], [0.06, 0.25]])    # meV/mV, rows dots A,B; cols gates QT1,QA1
K = 0.5*np.array([[EcA, Ecm], [Ecm, EcB]])          # = cdd^-1 in QArray units
cdd = np.linalg.inv(K); Cgd = np.linalg.solve(K, alpha/2)
Cm = -cdd[0, 1]; Clead = np.diag(cdd) - Cm - Cgd.sum(1)
print('Cm', Cm, 'Clead', Clead, 'Cgd', Cgd.round(4))
assert Cm > 0 and (Clead >= 0).all()
m = DotArray(Cdd=[[Clead[0], Cm], [Cm, Clead[1]]], Cgd=Cgd, charge_carrier='e', T=0)
# forward checks
Kq = m.cdd_inv; print('E_c fwd', 2*np.diag(Kq), 'E_cm fwd', 2*Kq[0,1], 'alpha fwd', (2*Kq@m.cgd).round(4))
V = np.linspace(-5, 60, 6501)
nA = np.asarray(m.ground_state_open(np.c_[V, np.zeros_like(V)]))
t = V[1:][np.diff(nA[:, 0]) > 0.5]; print('dot-A line spacing along QT1 (VQA1=0):', np.diff(t)[:2], 'pred P_A', EcA/alpha[0,0])
