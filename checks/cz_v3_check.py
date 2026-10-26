# v3 CZ checks with the standard convention (FEASIBILITY_REVIEW_V2 R6):
#   H = (J/4)(XX+YY+ZZ) + (dEz/4)(ZI - IZ)     dEz = qubit-frequency difference (Hz)
#   odd-subspace splitting sqrt(J^2 + dEz^2)
# 1) nominal Hann-pulse error vs Jmax/dEz (local Z corrections fitted at nominal)
# 2) quasi-static dJ/J with corrections FIXED at nominal: full H vs pure-ZZ formula
# 3) speed: 4x4 expm per slice vs the exact 2x2 odd-block reduction, vectorised over draws
import time, numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit.quantum_info import Operator, average_gate_fidelity
X=np.array([[0,1],[1,0]]); Y=np.array([[0,-1j],[1j,0]]); Z=np.diag([1.,-1]); I=np.eye(2); k=np.kron
EX=(k(X,X)+k(Y,Y)+k(Z,Z))/4; HZ=(k(Z,I)-k(I,Z))/4; CZ=np.diag([1,1,1,-1]).astype(complex)
def U4(Jmax, dEz, rel=0.0, n=2000):
    T=1/Jmax; dt=T/n; U=np.eye(4, dtype=complex)
    for t in (np.arange(n)+.5)*dt:
        U = expm(-2j*np.pi*(Jmax*(1+rel)*np.sin(np.pi*t/T)**2*EX + dEz*HZ)*dt) @ U
    return expm(2j*np.pi*dEz*HZ*T) @ U          # rotating frame of dEz (virtual Z)
def rz(a): return np.diag([np.exp(-1j*a/2), np.exp(1j*a/2)])
def fit_corr(U):
    f=lambda p: 1-average_gate_fidelity(Operator(k(rz(p[0]),rz(p[1]))@U), Operator(CZ))
    r=min((minimize(f,x0,method='Nelder-Mead',options={'xatol':1e-12,'fatol':1e-15}) for x0 in ([0,0],[1,1],[-1,2],[2,-1],[3,3])), key=lambda r:r.fun)
    return k(rz(r.x[0]),rz(r.x[1])), r.fun
def favg(U, V):  # average gate fidelity, d=4
    return (abs(np.trace(V.conj().T@U))**2 + 4)/20
print("1) Nominal Hann-pulse infidelity (standard convention), corrections fitted at nominal")
print("   Jmax/dEz    Jmax  dEz   1-F")
for Jmax, dEz in [(5,63),(5,20),(10,63),(20,63),(20,40),(21,63),(31.5,63),(63,63),(10,20),(100,300)]:
    _, e = fit_corr(U4(Jmax*1e6, dEz*1e6)); print(f"   {Jmax/dEz:6.3f}  {Jmax:6.1f} {dEz:5.1f}   {e:.2e}")
print("2) Quasi-static dJ/J, corrections fixed at nominal: full H vs pure-ZZ 0.8 sin^2(pi*rel/4)")
print("   Jmax/dEz   Jmax  dEz   rel     full 1-F     pure-ZZ      (full-nominal)/ZZ - 1")
for Jmax, dEz in [(5,63),(10,63),(20,63),(20,300),(5,300),(21,63)]:
    C, e0 = fit_corr(U4(Jmax*1e6, dEz*1e6))
    for rel in (0.003, 0.01, 0.05):
        e = 1-favg(C@U4(Jmax*1e6, dEz*1e6, rel), CZ); zz = .8*np.sin(np.pi*rel/4)**2
        print(f"   {Jmax/dEz:6.3f}  {Jmax:6.1f} {dEz:5.1f}  {rel:5.3f}   {e:.4e}   {zz:.4e}   {(e-e0)/zz-1:+.3%}")
# 3) 2x2 odd-block reduction, vectorised over noise draws
def odd_block_prop(Jmax, dEz, rel, n=2000):
    """Exact propagator in the rotating frame, block form. rel: array of draws. Returns diag phases + 2x2 blocks."""
    T=1/Jmax; dt=T/n; m=len(rel)
    B=np.tile(np.eye(2, dtype=complex), (m,1,1)); ph=np.zeros(m)
    for t in (np.arange(n)+.5)*dt:
        J = Jmax*(1+rel)*np.sin(np.pi*t/T)**2                 # (m,)
        ph += -2*np.pi*(J/4)*dt                               # |00>,|11> energy J/4
        # odd block H = -J/4 I + [[dEz/2, J/2],[J/2, -dEz/2]]
        a, b = dEz/2, J/2; w = np.sqrt(a*a + b*b); th = 2*np.pi*w*dt
        c, s = np.cos(th), np.sin(th)/w
        g = np.exp(2j*np.pi*(J/4)*dt)
        S = np.empty((m,2,2), dtype=complex)
        S[:,0,0]=g*(c-1j*s*a); S[:,0,1]=g*(-1j*s*b); S[:,1,0]=g*(-1j*s*b); S[:,1,1]=g*(c+1j*s*a)
        B = S @ B
    # rotating frame: undo free Zeeman evolution on the odd block
    R = np.array([np.exp(2j*np.pi*(dEz/2)*T), np.exp(-2j*np.pi*(dEz/2)*T)])
    B = R[None,:,None]*B
    U = np.zeros((m,4,4), dtype=complex); U[:,0,0]=np.exp(1j*ph); U[:,3,3]=np.exp(1j*ph); U[:,1:3,1:3]=B
    return U
Jmax, dEz = 20e6, 63e6
Uref = U4(Jmax, dEz, 0.01); Ublk = odd_block_prop(Jmax, dEz, np.array([0.01]))[0]
print(f"3) Block reduction vs 4x4 expm, max |diff| = {np.abs(Uref-Ublk).max():.1e}")
t=time.perf_counter(); [U4(Jmax, dEz, 0.0) for _ in range(5)]; t4=(time.perf_counter()-t)/5
draws = np.random.default_rng(0).normal(0, 0.01, 1000)
t=time.perf_counter(); odd_block_prop(Jmax, dEz, draws); tb=time.perf_counter()-t
print(f"   4x4 expm, 2000 slices: {t4*1e3:.0f} ms per draw -> 1e7 draws = {t4*1e7/3600:.0f} core-h")
print(f"   2x2 block, 2000 slices, 1000 draws vectorised: {tb:.2f} s per map point -> 1e4 points = {tb*1e4/3600:.1f} core-h")
