# Throwaway check: CZ from the exchange Hamiltonian (frequency units, h = 1).
#   H = (J/4)(XX + YY + ZZ) + (dEz/2)(ZI - IZ)
# Square pulse of length t = 1/(2J) gives conditional phase pi when dEz >> J.
# Compare with ideal CZ after the best local Z corrections; then check the
# analytic quasi-static error formula F = 1 - 0.3(1 - cos(dphi)), dphi = pi*dJ/J.
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit.quantum_info import Operator, average_gate_fidelity
X=np.array([[0,1],[1,0]]); Y=np.array([[0,-1j],[1j,0]]); Z=np.diag([1,-1]); I=np.eye(2)
k=np.kron; CZ=np.diag([1,1,1,-1])
def U(J, dEz, t):
    H = (J/4)*(k(X,X)+k(Y,Y)+k(Z,Z)) + (dEz/2)*(k(Z,I)-k(I,Z))
    return expm(-2j*np.pi*H*t)
def rz(a): return np.diag([np.exp(-1j*a/2), np.exp(1j*a/2)])
def best_local_fid(Uop):
    f = lambda p: -average_gate_fidelity(Operator(k(rz(p[0]),rz(p[1])) @ Uop), Operator(CZ))
    r = min((minimize(f, x0, method="Nelder-Mead") for x0 in ([0,0],[1,1],[-1,2],[2,-1])), key=lambda r: r.fun)
    return -r.fun, r.x
J = 5e6
print("Square exchange pulse, J = 5 MHz, t = 1/(2J) = %.0f ns" % (1e9/(2*J)))
for dEz in (20e6, 50e6, 100e6, 300e6):
    F, _ = best_local_fid(U(J, dEz, 1/(2*J)))
    print(f"   dEz = {dEz/1e6:5.0f} MHz -> best-local-Z CZ fidelity {F:.5f}")
# Quasi-static exchange error, corrections calibrated at nominal J (not per shot)
dEz = 300e6
F0, p = best_local_fid(U(J, dEz, 1/(2*J)))
corr = k(rz(p[0]), rz(p[1]))
print("Quasi-static dJ/J with fixed corrections (dEz = 300 MHz):")
for rel in (0.005, 0.01, 0.02, 0.05):
    Fsim = average_gate_fidelity(Operator(corr @ U(J*(1+rel), dEz, 1/(2*J))), Operator(CZ))
    dphi = np.pi*rel
    print(f"   dJ/J = {rel:5.3f}: simulated F = {Fsim:.6f}, analytic F0*(1-0.3(1-cos dphi)) = {F0*(1-0.3*(1-np.cos(dphi))):.6f}")
print("Pure-ZZ error model F = 1 - 0.8 sin^2(dphi/4) vs CPhase model 1 - 0.3(1 - cos dphi):")
for rel in (0.005, 0.01, 0.02, 0.05):
    Fsim = average_gate_fidelity(Operator(corr @ U(J*(1+rel), dEz, 1/(2*J))), Operator(CZ))
    dphi = np.pi*rel
    print(f"   dJ/J = {rel:5.3f}: 1-F simulated {1-Fsim:.3e} | pure-ZZ {0.8*np.sin(dphi/4)**2:.3e} | CPhase {0.3*(1-np.cos(dphi)):.3e}")
