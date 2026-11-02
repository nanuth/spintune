# PLAN 2.1/2.2 sensor spike: can ChargeSensedDotArray hold dot A : dot B step ratio at 2, 3, 4?
# Pass bar (fixed before the run): per-state ratio within +-20% of target over states (0..2, 0..2),
# no sign flip at nominal compensation (eps = 0).
import time
import numpy as np
from qarray import ChargeSensedDotArray
from qarray.python_implementations.helper_functions import free_energy

GATES = ['QT0', 'QT1', 'QT2', 'QA1']          # + a dummy 5th gate held at 0 V = the SEB's lead capacitance
EcA, EcB, Ecm, Ecs = 4.0, 4.4, 0.07 * 4.0, 2.0  # meV (Ecm from r_m = 0.07; Ecs [assumed])
ALPHA = np.array([                              # meV/mV, rows A, B, sensor; cols QT0 QT1 QT2 QA1  [assumed]
    [0.03, 0.27, 0.08, 0.25 * 0.27],
    [0.02, 0.25 * 0.25, 0.08, 0.25],
    [0.30, 0.15, 0.03, 0.01]])


def build(r, sA, gamma):
    E = np.array([[EcA, Ecm, sA], [Ecm, EcB, sA / r], [sA, sA / r, Ecs]])
    K = E / 2                                    # = cdd_full^-1 in QArray units
    cdd = np.linalg.inv(K)
    Cg = np.linalg.solve(K, ALPHA / 2)          # Maxwell-consistent gate capacitances, (3, 4)
    Cm, Cds = -cdd[0, 1], -cdd[2, :2]
    lead = np.diag(cdd)[:2] - Cm - Cds - Cg[:2].sum(1)
    dummy = cdd[2, 2] - Cds.sum() - Cg[2].sum()
    phys = (np.diag(cdd) - (np.abs(cdd).sum(1) - np.diag(cdd))) / 2 - Cg.sum(1)   # physical C_lead (factor-2 aware)
    assert Cm > 0 and (Cds > 0).all() and (lead >= 0).all() and dummy >= 0, (Cm, Cds, lead, dummy)
    m = ChargeSensedDotArray(
        Cdd=[[lead[0], Cm], [Cm, lead[1]]],
        Cgd=np.c_[Cg[:2], np.zeros(2)],
        Cds=[Cds], Cgs=[np.r_[Cg[2], dummy]],
        coulomb_peak_width=gamma, T=0, charge_carrier='e')
    assert np.allclose(2 * m.cdd_inv_full, E), 'forward energies mismatch'
    return m, phys


def detuning(m, V, n):
    """Sensor detuning (meV) of the nearest Coulomb peak, as QArray computes it."""
    Ns = np.round(np.einsum('ij,...j', m.cgd_full, V)[..., -1:])
    best = None
    for k in range(-3, 4):
        N0 = np.concatenate([n, Ns + k], -1); N1 = np.concatenate([n, Ns + k + 1], -1)
        d = free_energy(m.cdd_inv_full, m.cgd_full, V, N1) - free_energy(m.cdd_inv_full, m.cgd_full, V, N0)
        best = d if best is None else np.where(np.abs(d) < np.abs(best), d, best)
    return best


def run(r, sA_over_g, eps, sgn, gamma=0.2, pitch=0.25, span=50.0):
    sA = sA_over_g * gamma
    m, phys = build(r, sA, gamma)
    a_s = 2 * (m.cdd_inv_full @ m.cgd_full)[-1]          # sensor lever arms (signed, QArray convention)
    k1, k3 = -a_s[1] / a_s[0] * (1 - eps), -a_s[3] / a_s[0] * (1 - eps)
    u = np.arange(0, span + 1e-9, pitch)
    U, W = np.meshgrid(u, u, indexing='ij')             # U: QT1, W: QA1 (our electron-like axes)

    def volts(c0, U, W):
        return sgn * np.stack([c0 + k1 * U + k3 * W, U, 0 * U, W, 0 * U], -1)

    # place the operating point: detuning at (0,0) so the (0,0)->(2,2) span is centred on the max-slope flank
    x0 = gamma / np.sqrt(3) - (2 * sA + 2 * sA / r) / 2
    c0 = 0.0
    for _ in range(4):
        d = detuning(m, volts(c0, np.zeros(1), np.zeros(1)), np.zeros((1, 2)))[0]
        d2 = detuning(m, volts(c0 + 1e-3, np.zeros(1), np.zeros(1)), np.zeros((1, 2)))[0]
        c0 -= (d - x0) / ((d2 - d) / 1e-3)

    V = volts(c0, U, W)
    sig, n = m.charge_sensor_open(V.reshape(-1, 5))
    sig = sig[:, 0].reshape(U.shape); n = np.asarray(n).reshape(*U.shape, 2).round().astype(int)
    x = detuning(m, V.reshape(-1, 5), n.reshape(-1, 2)).reshape(U.shape)

    stepsA, stepsB = {}, {}
    for ax in (0, 1):
        ds = np.diff(sig, axis=ax); dn = np.diff(n, axis=ax)
        n0 = n[:-1, :] if ax == 0 else n[:, :-1]
        for cls, store in (((1, 0), stepsA), ((0, 1), stepsB)):
            mask = (dn[..., 0] == cls[0]) & (dn[..., 1] == cls[1])
            for (a, b), s in zip(n0[mask], ds[mask]):
                store.setdefault((a, b), []).append(s)
    ratios, signs = {}, []
    for a in range(3):
        for b in range(3):
            if (a, b) in stepsA and (a, b) in stepsB:
                ratios[(a, b)] = np.median(stepsA[(a, b)]) / np.median(stepsB[(a, b)])
            signs += [np.sign(np.median(v)) for key, v in {**stepsA, **stepsB}.items() if key == (a, b)]
    xs = x[(n[..., 0] <= 2) & (n[..., 1] <= 2)]
    return dict(ratios=ratios, sign_flip=len(set(signs)) > 1, x_range=(xs.min() / gamma, xs.max() / gamma),
                phys=phys, stepA00=np.median(stepsA.get((0, 0), [np.nan])), model=m, c0=c0, k=(k1, k3))


if __name__ == '__main__':
    # 0. which voltage sign loads electrons in ChargeSensedDotArray?
    m, _ = build(3, 0.05, 0.2)
    for sgn in (+1, -1):
        n = np.asarray(m.ground_state_open(np.array([[0, sgn * 40, 0, sgn * 40, 0]], float)))
        print(f'sign {sgn:+d}: occupancy at |V|=40 mV on QT1,QA1 -> {n[0]}')
    sgn = +1 if np.asarray(m.ground_state_open(np.array([[0, 40, 0, 40, 0.]]))).sum() > 0 else -1
    print('using sign', sgn)

    print('\n r  sA/g  eps | ratio per state (a,b) a,b in 0..2           | min/max vs target | flip | detuning span /g | phys C_lead A,B,s')
    for r in (2, 3, 4):
        for sAg in (0.25, 0.5):
            for eps in (0.0, 0.2):
                o = run(r, sAg, eps, sgn)
                rv = np.array(list(o['ratios'].values()))
                txt = ' '.join(f'{v:.2f}' for v in rv)
                ok = (np.abs(rv / r - 1) <= 0.2).all() and not o['sign_flip']
                print(f' {r}  {sAg:.2f}  {eps:.1f} | {txt:44s} | {rv.min()/r:.2f}/{rv.max()/r:.2f} | {str(o["sign_flip"]):5s}'
                      f'| {o["x_range"][0]:+.2f}..{o["x_range"][1]:+.2f} | {np.round(o["phys"], 3)} {"PASS" if ok else "fail"}')

    # timing: ray (65 px) and windows (32^2, 64^2), T = 0 and 300 mK
    print()
    for T in (0, 300):
        m, _ = build(3, 0.05, 0.2); m.T = float(T)
        for name, npx in (('ray 65', 65), ('window 32x32', 32 * 32), ('window 64x64', 64 * 64)):
            V = np.zeros((npx, 5)); V[:, 1] = sgn * np.linspace(0, 50, npx); V[:, 3] = sgn * np.linspace(0, 50, npx)[::-1]
            m.charge_sensor_open(V)
            t = []
            for _ in range(10):
                t0 = time.perf_counter(); m.charge_sensor_open(V); t.append(time.perf_counter() - t0)
            print(f'T={T:3d} mK  {name:13s}: {np.median(t)*1e3:7.2f} ms/call  ({np.median(t)/npx*1e6:.2f} us/px)')
