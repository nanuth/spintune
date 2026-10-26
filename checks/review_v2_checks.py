import json
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize
from qiskit.quantum_info import Operator, average_gate_fidelity

X = np.array([[0, 1], [1, 0]])
Y = np.array([[0, -1j], [1j, 0]])
Z = np.diag([1, -1])
I = np.eye(2)
EX = (np.kron(X, X) + np.kron(Y, Y) + np.kron(Z, Z)) / 4
HZ = (np.kron(Z, I) - np.kron(I, Z)) / 2
CZ = Operator(np.diag([1, 1, 1, -1]))

def pulse(peak, zeeman, rel=0, n=2000):
    duration = 1 / peak
    dt = duration / n
    result = np.eye(4, dtype=complex)
    for time in (np.arange(n) + .5) * dt:
        exchange = peak * (1 + rel) * np.sin(np.pi * time / duration) ** 2
        result = expm(-2j * np.pi * (exchange * EX + zeeman * HZ) * dt) @ result
    return expm(2j * np.pi * zeeman * HZ * duration) @ result

def correction(phases):
    def rz(angle):
        return np.diag([np.exp(-1j * angle / 2), np.exp(1j * angle / 2)])
    return np.kron(rz(phases[0]), rz(phases[1]))

for peak, zeeman in [(5e6, 63e6), (20e6, 63e6), (100e6, 300e6)]:
    nominal = pulse(peak, zeeman)
    fit = min((minimize(lambda p: 1-average_gate_fidelity(Operator(correction(p) @ nominal), CZ), start,
                        method='Nelder-Mead', options={'xatol': 1e-11, 'fatol': 1e-14})
               for start in [[0, 0], [1, 1], [-1, 2], [2, -1], [3, 3]]), key=lambda r: r.fun)
    fixed = correction(fit.x)
    for rel in [0, .01, .05]:
        error = 1 - average_gate_fidelity(Operator(fixed @ pulse(peak, zeeman, rel)), CZ)
        zz = .8 * np.sin(np.pi * rel / 4) ** 2
        print(json.dumps({'J_MHz': peak / 1e6, 'dEz_MHz': zeeman / 1e6, 'fractional_J_error': rel,
                          'full_H_infidelity': error, 'pure_ZZ_infidelity': zz,
                          'relative_difference': None if zz == 0 else error / zz - 1}), flush=True)

# Toy model illustrating why a prior-spacing empty-anchor rule is insufficient.
# First/second loading transitions are at 0/40 mV, both in the allowed P range.
prior_period, true_period, start = 15, 40, 70
claimed_empty = start - 1.5 * prior_period
occupied = 0 if claimed_empty < 0 else 1 + int(claimed_empty // true_period)
print(json.dumps({'prior_period_mV': prior_period, 'actual_period_mV': true_period,
                  'start_mV': start, 'claimed_empty_mV': claimed_empty,
                  'true_electrons_at_claimed_empty': occupied}))

# Flat distributions spanning several charge periods cannot be represented by
# a locally identified absolute-cell Gaussian after an unreferenced line scan.
print('The Hamiltonian has odd-state Zeeman eigenvalues +/- dEz and a splitting of 2*dEz.')
