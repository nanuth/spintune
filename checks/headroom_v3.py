# Pre-pilot headroom estimate for the v3 policy (perfect line reader, noiseless QArray cells).
# Policy (design v3 §6.1), two phases:
#  1. Locate: alternate rays along -QT1 / -QA1 from the start s until both axes end in a
#     transition-free stretch >= L (no crossing required in this phase).
#  2. Certify at the end point v0: each axis needs a ray through v0 that crosses a line above v0 and
#     is transition-free for >= L below the crossing. The last locate pass is reused if it crossed a
#     line; otherwise (and always for the other axis) one ray is cast from v0 - L*e upward to the first
#     crossing + 2 pitches. Plus the diagonal ray sqrt(2)*L and a 16x16 confirmation (256 px).
#  Period (as in design §6.1): a tuner whose P belief is wider than +-25% first casts one 64-px ray at
#  1 mV centred on s along +QT1 (span 64 mV >= 2 P_max). If it shows >= 2 dot-A crossings, P is known
#  (~5%) and every later ray uses pitch(0.9 P). Otherwise it locates at pitch(P_lo), takes P from >= 2
#  same-dot crossings seen while locating, or else casts one more 64-px ray above the first line.
#  Pitch: largest allowed <= P_lo/3 (P_lo = 5th percentile of the tuner's P belief).
# Fleets: ID (P = 15 mV x lognormal 17%, P_max 30 mV) and wide (P ~ U[5,40], P_max 40 mV).
import sys, numpy as np
exec(open(sys.argv[1]).read().split('def descend')[0])     # device, occ, period_and_cell
def pitch(P): return max([p for p in (0.5, 1, 2, 4) if p <= P/3] or [0.5])
def locate(m, v, L, step):
    scanned = 0.0; ok = [False, False]; ax = 0; seen = {0: [], 1: []}; last = (None, False)
    while not all(ok):
        e = np.zeros(2); e[ax] = -1; n0 = occ(m, v)[0]; free = 0.0; crossed = False
        while free < L:
            v2 = v + e*step; n1 = occ(m, v2)[0]; scanned += step
            if (n1 != n0).any():
                crossed = True; free = 0.0
                if n1[ax] != n0[ax]: seen[ax].append(v2[ax])
                n0 = n1
            else: free += step
            v = v2
        ok[ax] = True
        if crossed: ok[1-ax] = False
        last = (ax, crossed); ax = 1 - ax
    return v, scanned, seen, last
def up_to_line(m, v0, ax, step, cap=400.0):
    e = np.zeros(2); e[ax] = 1; n0 = occ(m, v0)[0]; d = 0.0; v = v0.copy()
    while d < cap:
        v = v + e*step; d += step
        if (occ(m, v)[0] != n0).any(): return d
    return d
def run(fleet, n=300, seed=5):
    rng = np.random.default_rng(seed); rows = []
    for i in range(n):
        m = device(rng); Pm, c11 = period_and_cell(m)
        if fleet == 'ID': P = 15*np.exp(rng.normal(0, 0.17)); Pmax = 30.0; spec_lo = 7.5; fleet_lo = 15*np.exp(-1.645*0.17)
        else:             P = rng.uniform(5, 40);           Pmax = 40.0; spec_lo = 5.0; fleet_lo = 5.0
        L = 1.25*1.3*Pmax; mv = P/Pm; r = {}
        for name, sig, P_lo, knowsP in (('T*', 0, P, True), ('hist', 26, 0.8*P, True),
                                        ('fleet', 77, fleet_lo, False), ('cold', 77, spec_lo, False)):
            v0 = c11 + (rng.normal(0, sig, 2)/mv if sig else 0)
            step = 1.0/mv; extra = 0.0; Pknown = knowsP
            if not knowsP:
                extra += 64; vv = v0 + np.array([-32, 0])/mv; nA = occ(m, np.c_[np.linspace(vv[0], vv[0]+64/mv, 65), np.full(65, vv[1])])[:, 0]
                if np.count_nonzero(np.diff(nA)) >= 2: Pknown = True
            p = pitch(0.9*P) if (Pknown and not knowsP) else pitch(P_lo)
            vend, scanned, seen, (lax, lcross) = locate(m, v0.copy(), L/mv, step)
            mV = scanned*mv
            for ax in (0, 1):
                if ax == lax and lcross: continue
                mV += L + up_to_line(m, vend, ax, step)*mv + 2*p
            px = mV/p + extra
            if Pknown: p_fin = p
            else:
                if not any(len(s) >= 2 for s in seen.values()): px += 64
                p_fin = pitch(0.9*P)
            px += np.sqrt(2)*L/p_fin + 256
            r[name] = px
        rows.append(r)
    return {k: np.array([r[k] for r in rows]) for k in rows[0]}
for fleet in ('ID', 'wide'):
    t = run(fleet)
    print(f"{fleet} fleet:" + "".join(f"  {k} mean {v.mean():4.0f} (med {np.median(v):4.0f}, p90 {np.percentile(v,90):4.0f})" for k, v in t.items()))
    print(f"   h = (C_cold - C_T*)/C_cold = {(t['cold'].mean()-t['T*'].mean())/t['cold'].mean():.0%};"
          f"  hist/cold = {t['hist'].mean()/t['cold'].mean():.2f};  fleet/cold = {t['fleet'].mean()/t['cold'].mean():.2f};  T*/hist = {t['T*'].mean()/t['hist'].mean():.2f}")
