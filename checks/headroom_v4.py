# Exploratory cost estimate for the shared policy (design §6.1). Noiseless QArray cells, perfect line reader.
# These are estimates for one specified policy, not a cost floor: a different policy could gather the same
# evidence more cheaply.
#
# What is metered:
#  - every ray and window is a billed query at the policy's own pitch. Each ray is sized for the transition-free
#    length still missing plus one period, then rounded up to 16/32/64 samples (default, "batch") or used as is
#    within 8-64 samples (--need-sized). A ray that would cross the domain floor is shrunk to the largest allowed
#    size that fits. Windows are 16x16, or 32x32 at 4 mV when the period estimate exceeds 32 mV (§5.2). Pixel
#    counts are integers; decisions use only the samples acquired.
#  - a +-300 mV domain around the design-nominal target. A descent never goes below the point where the
#    certificate would leave the domain; if it would have to, the run abstains.
#  - query count and RF time with the §4.2 defaults: 10 us/px, 20 ms setup/query, 1 ms settle/line, 1 V/s slew.
#  - the confirmation window is retried (billed) when the period estimate is off by > 20% (§5.2).
# Policy: measure the period first if a known period would allow a coarser pitch; descend along the diagonal
# -(1,1)/sqrt2 until the stretch since the last transition is >= sqrt2*L + P_lo; put v0 sqrt2*L above the end of
# the descent (so the descent itself is the certificate's diagonal ray through v0); cast one ray per axis upward
# from v0 - L*e to the first line; relocate below v0 if an axis ray sees a transition below v0; confirm.
# --axis-descent uses the earlier rule instead: descend along -QT1, then -QA1, each until transition-free >= L,
# then certify with axis rays (reusing the last one if it crossed a line) plus a separate diagonal ray. That rule
# stalls when the other dot is still occupied and its lines cross the axis every P/x < L (cross-coupling x > ~0.3).
# Tuners: T* (oracle start), T3 (design spec), T3-M (fleet mean), H (chip history as a chip sequence: cell 1 has
# fleet knowledge only; cell k+1 gets a start point and period belief whose errors follow the §7.2 hierarchy
# given k earlier cells: start sd 22*sqrt(1+1/k) mV per axis, period log-sd 0.13*sqrt(1+1/k)). The history beliefs
# are drawn around the truth, not fitted from logs. Ablations: period knowledge only (k = 9 belief, cold start
# point) and start knowledge only (k = 9 start, design-spec period belief).
# Run: python headroom_v4.py anchor_check.py [--need-sized] [--axis-descent] [--stop-length MV]
#   --stop-length replaces the transition-free length L (49/65 mV) everywhere, e.g. 22.5 for the 1.5-period shortcut.
import sys, numpy as np
exec(open(sys.argv[1]).read().split('def descend')[0])     # device(), occ(), period_and_cell() from anchor_check.py

FIXED = '--need-sized' not in sys.argv; AXIS = '--axis-descent' in sys.argv
STOP = float(sys.argv[sys.argv.index('--stop-length') + 1]) if '--stop-length' in sys.argv else None
ALLOWED = (16, 32, 64) if FIXED else tuple(range(8, 65))
PITCHES = (0.5, 1, 2, 4)
T_INT, T_SETUP, T_SETTLE, SLEW = 10e-6, 20e-3, 1e-3, 1000.0      # s/px, s/query, s/line, mV/s   (§4.2 RF defaults)
E = np.eye(2)

class Refused(Exception): pass
class Relocate(Exception):
    def __init__(self, point): self.point = point

def pitch(P, per=3): return max([p for p in PITCHES if p <= P/per] or [PITCHES[0]])
def qsize(n): return next(s for s in (16, 32, 64, 64) if s >= min(n, 64)) if FIXED else int(min(max(n, 8), 64))

class Session:
    def __init__(s, m, mv, centre, half=300.0):
        s.m, s.mv = m, mv; s.lo, s.hi = centre - half/mv, centre + half/mv
        s.px = s.nq = 0; s.t = 0.0; s.pos = None
    def _bill(s, npx, nlines, first, last):
        jump = 0.0 if s.pos is None else np.abs(first - s.pos).max()*s.mv     # both gates slew together, mV
        s.px += npx; s.nq += 1; s.t += T_SETUP + npx*T_INT + nlines*T_SETTLE + jump/SLEW; s.pos = last
    def ray(s, start, d, p, n):
        pts = start + np.outer(np.arange(n), d)*(p/s.mv)
        if (pts < s.lo).any() or (pts > s.hi).any(): raise Refused
        s._bill(n, 1, pts[0], pts[-1]); return pts, occ(s.m, pts)
    def window(s, centre, p, size):
        g = (np.arange(size) - (size - 1)/2)*(p/s.mv)
        lo, hi = centre + g[0], centre + g[-1]
        if (lo < s.lo).any() or (hi > s.hi).any(): raise Refused
        s._bill(size*size, size, lo, hi)

def spacing(pts, N, ax, mv):
    idx = np.nonzero(np.diff(N[:, ax]) != 0)[0]
    return np.abs(np.diff(pts[idx, ax])).mean()*mv if len(idx) >= 2 else None

def descend(S, v, o, d, p, need, P_lo, floor):
    """Continue from v (occupancy o; None = not yet measured) along unit direction d until the stretch since the
    last occupancy change is >= need (mV). Queries are sized to the free length still missing plus one period,
    and never go below `floor` mV above the domain's lower edge on any axis."""
    free, cr, first = 0.0, [], True
    L = need
    while first or free < L - 1e-9:
        room = int(np.floor(min(((v - S.lo)*S.mv - floor)[d < 0] / -d[d < 0]) / p))
        n = qsize(int(np.ceil((L - free + P_lo)/p))); first = False
        if n > room: n = max([q for q in ALLOWED if q <= room] or [0])
        if n < 8: raise Refused
        pts, N = S.ray(v if o is None else v + d*(p/S.mv), d, p, n)
        for x, ox in zip(pts, N):                        # samples past the first point that completes the
            if o is not None:                            # free stretch are billed but not used
                if (ox != o).any(): cr.append((x.copy(), ox != o)); free = 0.0
                else: free += p
            o, v = ox, x
            if free >= L - 1e-9: break
    ax = int(np.argmax(np.abs(d)))
    pos = [x[ax] for x, ch in cr if ch[ax]] if np.count_nonzero(d) == 1 else []
    P_seen = np.abs(np.diff(pos)).mean()*S.mv if len(pos) >= 2 else None
    return v, o, bool(cr), free, P_seen

def certify(S, v0, o0, last_ax, last_crossed, last_free, p, L, P_hint, diag_done=False):
    """Axis rays through v0 (the last descent ray is reused if it crossed a line) and the diagonal. Returns the
    distance (mV) from v0 up to the first line on each axis; raises Relocate if a ray sees a line below v0."""
    up = [None, None]
    for ax in (0, 1):
        if ax == last_ax and last_crossed: up[ax] = last_free; continue
        start = v0 - E[ax]*(L/S.mv); v, o, above, after, first = start, None, None, 0, True
        while above is None or after < 2:
            n = qsize(int(np.ceil((L + P_hint if first else P_hint)/p))); first = False
            pts, N = S.ray(v if o is None else v + E[ax]*(p/S.mv), E[ax], p, n)
            for x, ox in zip(pts, N):
                t = (x - v0)[ax]*S.mv
                if o is not None and (ox != o).any():
                    if t <= 1e-9: raise Relocate(start)
                    if above is None: above = t
                elif above is not None: after += 1
                o, v = ox, x
        up[ax] = above
    d = -(E[0] + E[1])/np.sqrt(2); rem = 0 if diag_done else int(np.ceil(np.sqrt(2)*L/p)); v = v0
    while rem > 0:
        n = qsize(rem); pts, N = S.ray(v + d*(p/S.mv), d, p, n); rem -= n
        if (N != o0).any(): raise Relocate(pts[-1])
        v = pts[-1]
    return up

def tune(m, mv, P, Pmax, centre, s, belief):
    """belief: None = exact period (oracle); else (P_hat, P_lo, P_hat_usable)."""
    S = Session(m, mv, centre); L = STOP or 1.25*1.3*Pmax; p_m = 1.0 if Pmax <= 32 else 2.0
    try:
        if belief is None: P_est, P_lo = P, P
        else:
            P_hat, P_lo, usable = belief; P_est = P_hat if usable else None
            if pitch(P_lo) < pitch(0.9*P_hat):           # a known period would allow a coarser pitch: measure it first
                pts, N = S.ray(s - E[0]*(32*p_m/mv), E[0], p_m, 64)
                Pm_ = spacing(pts, N, 0, mv)
                if Pm_: P_est, P_lo = Pm_, 0.9*Pm_
        p = pitch(P_lo); v, o = s.copy(), None
        U = (E[0] + E[1])/np.sqrt(2)
        for _ in range(6):
            if AXIS:
                v, o, _, _, Ps = descend(S, v, o, -E[0], p, L, P_lo, L + 2*p)
                v0, o0, crossed, free, Ps2 = descend(S, v, o, -E[1], p, L, P_lo, L + 2*p)
                if P_est is None: P_est = Ps or Ps2
                try: up = certify(S, v0, o0, 1, crossed, free, p, L, P_est or P_lo); break
                except Relocate as r: v, o = r.point, None
            else:
                v, o, _, free, _ = descend(S, v, o, -U, p, np.sqrt(2)*L + P_lo, P_lo, 2*p)
                v0 = v + U*(np.sqrt(2)*L/S.mv); o0 = o          # inside the free stretch, sqrt2*L above its end
                try: up = certify(S, v0, o0, None, False, 0.0, p, L, P_est or P_lo, diag_done=True); break
                except Relocate as r: v, o = r.point, None
        else: raise Refused
        if P_est is None:                                 # one more ray above the first dot-A line
            pts, N = S.ray(v0 + E[0]*((up[0] + p)/mv), E[0], p_m, 64); P_est = spacing(pts, N, 0, mv) or Pmax
        for attempt in (0, 1):
            Pw = P_est if attempt == 0 else P               # a retry uses the period fitted in the first window
            size, pw = (16, pitch(Pw, 4)) if Pw <= 32 else (32, 4.0)
            S.window(v0 + (E[0]*(up[0] + Pw/2) + E[1]*(up[1] + Pw/2))/mv, pw, size)
            if abs(np.log(P_est/P)) <= np.log(1.2): break
        wrong = tuple(occ(m, v0)[0]) != (0, 0)
        return S.px, S.nq, S.t, False, wrong
    except Refused:
        return S.px, S.nq, S.t, True, False

def run(fleet, n=300, seed=5):
    rng = np.random.default_rng(seed); out = {}
    def add(k, r): out.setdefault(k, []).append(r)
    for i in range(n):
        m = device(rng); Pm, c11 = period_and_cell(m); k = i % 10                 # chips of 10 cells, k earlier cells
        if fleet == 'ID': P = 15*np.exp(rng.normal(0, 0.17)); Pmax, spec, fleetP = 30.0, (15, 7.5), (15, 15*np.exp(-1.645*0.17))
        else:             P = rng.uniform(5, 40);           Pmax, spec, fleetP = 40.0, (22.5, 5.0), (22.5, 6.75)
        mv = P/Pm; off = rng.normal(0, 77, 2); centre = c11 - off/mv               # design nominal = domain centre
        def hist_belief(kk):
            sd = 0.13*np.sqrt(1 + 1/kk); Ph = P*np.exp(rng.normal(0, sd)); return (Ph, Ph*np.exp(-1.645*sd), True)
        def near(sd): return c11 + rng.normal(0, sd, 2)/mv
        add('T* oracle start', tune(m, mv, P, Pmax, centre, c11.copy(), None))
        add('T3 cold (spec)', tune(m, mv, P, Pmax, centre, centre.copy(), (*spec, False)))
        add('T3-M fleet mean', tune(m, mv, P, Pmax, centre, centre.copy(), (*fleetP, False)))
        r = tune(m, mv, P, Pmax, centre, centre.copy(), (*fleetP, False)) if k == 0 else \
            tune(m, mv, P, Pmax, centre, near(22*np.sqrt(1 + 1/k)), hist_belief(k))
        add('H chip history (cells 1-10)', r); add(f'H k={k}', r)
        add('H, period knowledge only', tune(m, mv, P, Pmax, centre, centre.copy(), hist_belief(9)))
        add('H, start knowledge only', tune(m, mv, P, Pmax, centre, near(22*np.sqrt(1 + 1/9)), (*spec, False)))
    return {k: np.array(v, dtype=float) for k, v in out.items()}

for fleet in ('ID', 'wide'):
    t = run(fleet); c = t['T3 cold (spec)']; done = lambda a: a[:, 3] == 0
    print(f"\n{fleet} fleet, 300 cells. Means over finished runs; ratios over cells where both finished.")
    print(f"  {'tuner':28s} {'px':>5s} {'queries':>7s} {'RF ms':>6s} {'abstain':>7s} {'wrong':>5s} {'px/cold':>7s} {'time/cold':>9s}")
    for name, a in t.items():
        if name.startswith('H k=') and name not in ('H k=0', 'H k=1', 'H k=9'): continue
        g = done(a); line = f"  {name:28s} {a[g,0].mean():5.0f} {a[g,1].mean():7.1f} {1e3*a[g,2].mean():6.0f} {int((~g).sum()):7d} {int(a[:,4].sum()):5d}"
        if len(a) == len(c):
            b = g & done(c); line += f" {a[b,0].sum()/c[b,0].sum():7.2f} {a[b,2].sum()/c[b,2].sum():9.2f}"
        print(line)
    s = t['T* oracle start']; b = done(s) & done(c)
    print(f"  oracle-start headroom vs T3: pixels {1 - s[b,0].sum()/c[b,0].sum():.0%}, RF time {1 - s[b,2].sum()/c[b,2].sum():.0%};"
          f"  pixel integration is {100*T_INT*c[done(c),0].mean()/c[done(c),2].mean():.1f}% of T3's RF time")
