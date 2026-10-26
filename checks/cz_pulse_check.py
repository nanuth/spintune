# Square vs Hann-shaped exchange pulse at non-synchronised dEz (builder's probe values).
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit.quantum_info import Operator, average_gate_fidelity
X=np.array([[0,1],[1,0]]); Y=np.array([[0,-1j],[1j,0]]); Z=np.diag([1,-1]); I=np.eye(2); k=np.kron
CZ=np.diag([1,1,1,-1]); HEX=(k(X,X)+k(Y,Y)+k(Z,Z))/4; HZ=(k(Z,I)-k(I,Z))/2
def U_pulse(Jmax, dEz, shape, n=2000):
    T = 1/(2*Jmax) if shape=="square" else 1/Jmax          # both give integral J dt = 1/2
    ts = (np.arange(n)+0.5)*T/n; dt = T/n; U = np.eye(4, dtype=complex)
    for t in ts:
        J = Jmax if shape=="square" else Jmax*np.sin(np.pi*t/T)**2
        U = expm(-2j*np.pi*(J*HEX + dEz*HZ)*dt) @ U
    # remove the free Zeeman evolution (rotating frame of dEz), as calibrated virtual-Z would
    return expm(2j*np.pi*dEz*HZ*T) @ U, T
def rz(a): return np.diag([np.exp(-1j*a/2), np.exp(1j*a/2)])
def best(U):
    f = lambda p: -average_gate_fidelity(Operator(k(rz(p[0]),rz(p[1])) @ U), Operator(CZ))
    return -min((minimize(f, x0, method="Nelder-Mead") for x0 in ([0,0],[1,1],[-1,2],[2,-1],[3,3])), key=lambda r: r.fun).fun
print(" J(MHz)  dEz(MHz) | square 1-F  (t)      | Hann 1-F  (t)")
for J, dEz in [(5,52.5),(5,63),(5,112.5),(10,63),(20,63),(2.5,63)]:
    Us, Ts = U_pulse(J*1e6, dEz*1e6, "square"); Uh, Th = U_pulse(J*1e6, dEz*1e6, "hann")
    print(f" {J:6.1f}  {dEz:7.1f}  | {1-best(Us):.1e} ({Ts*1e9:4.0f} ns) | {1-best(Uh):.1e} ({Th*1e9:4.0f} ns)")
