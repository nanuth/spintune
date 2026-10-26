# SpinTune cross-review: Bobi's plan vs our v2 design

**Compared, 25 Oct 2026:**
- **Bobi's documents:**
  - `bobi_resources/SPINTUNE-2.md`, a revision of `SPINTUNE.md`;
  - `bobi_resources/PLAN.md`, the implementation plan.
- **Our documents:**
  - `FEASIBILITY_REVIEW.md`, including its addendum;
  - `SpinTune_Design_v2.md`;
  - the simulation checks behind them.
- **New for this review:** two measurements (§5).

---

## 1. Bottom line

- **The two plans agree on the skeleton.** Both have:
  - a fleet prior and a cold-vs-warm comparison;
  - success judged by ground truth, never by the tuner's own classifier;
  - random and heuristic baselines;
  - a pixel counter;
  - a shifted test fleet;
  - fixed barriers, because QArray has no tunnel coupling;
  - a pre-committed fallback if the result is weak.

  `PLAN.md` is a better working checklist than anything in v2: clear interfaces, a code layout, a critical path. It should stay the task list.
- **The plans disagree on what gets measured, and two disagreements block the headline.**
  1. **Bobi's target, "reach the double-dot regime", is almost free in QArray.** Under `PLAN.md`'s own label rules, **73–91% of random 32×32 windows are already "double"** [measured, §5.1]. A random first guess usually succeeds, so there is no search for a prior to save, and the "≥ 2× fewer pixels" bar can't be shown meaningfully.
  2. **Bobi's fleet barely varies.** Capacitances vary by 10%, the only offset is a common back-gate shift, and its size is chosen "so CSDs look varied but tunable". We measured earlier that without per-dot offsets, starting at the fleet-mean voltage lands in (1,1) on **100%** of devices. With published 22FDX spreads it lands **1–6%** of the time. The headline would come from the fleet choice, not the method.
- **Two more conflicts change the plan:**
  - Qiskit is only a stretch goal in Bobi's plan, but the judges require it.
  - Bobi puts the 6-dot run on the MVP path, but the 6-dot linear layout is not a confirmed Equal1 layout.
- **Recommendation:** keep `PLAN.md`'s structure and Bobi's best ideas (§3), and swap in four things from v2 (§6):
  1. the (1,1) target, using the anchor-and-count protocol;
  2. the sourced hierarchical fleet;
  3. a week-1 headroom check;
  4. the protected Qiskit track.

---

## 2. Where the plans agree

| Topic | Bobi (`SPINTUNE-2.md` / `PLAN.md`) | Ours (v2) | Verdict |
|---|---|---|---|
| Core idea | Fleet prior warm-starts each new chip | Same, plus same-chip history | Agree |
| Success judged by | Oracle (ground truth), never the CNN (PLAN decision 3) | Evaluator only (§4, §11.1) | Agree |
| Measurement axis | Pixels acquired, same for every tuner | Pixels plus time-cost model | Agree, ours adds overheads |
| Baselines | Random, line-scan + Hough heuristic, cold BO, fleet-mean init | Random, zero-search start, scan-and-fit, transition navigation, cold, oracle-start floor | Agree in spirit |
| Shifted test fleet | Offset back gate, wider spread, more telegraph noise | Five OOD fleets plus external real data | Agree, ours is broader |
| Oracle-label ablation | T11 | Oracle-assisted reader (§5.3) | Agree |
| Barriers | Fixed: "searching over barriers would be pretending" | Fixed in charge tuning (§3.1) | Agree |
| Exchange physics | J = 4Ut_c²/(U² − ε²); quasi-static **ZZ** error | Same; ZZ verified numerically (v1's CPhase model was 3× too pessimistic) | Agree |
| Drift | 2D cross-correlation, no ML | Same | Agree |
| Honest fallback | "Don't move the bar after seeing the result"; "safe warm start, modest gain" | Pre-registered gates; "report it straight" | Agree |
| Compute scale | Plan for 10³ devices on a laptop; cluster is an ask | Laptop default; HPC optional | Agree |
| Team | Duo, tracks run in parallel | Duo, 20+ h/week each, two tracks | Agree |

---

## 3. What Bobi's plan does better: adopt into v2

1. **Learn the prior from tuning logs**, i.e. cold runs on a training fleet. It's "the data Equal1 would already have from chips it has brought up". That's a more realistic data source than v2's "fitted on the train fleet", which leaves open whether the fit uses ground truth. It's also a better pitch line.
   - **Adopt:** v2's fleet prior and chip history must be fitted only from confirmed targets in tuning logs.
2. **Never worse on chips unlike the fleet.** This is an explicit robustness bar on the shifted fleet. v2 only says "negative transfer reported".
   - **Adopt:** add "median and restricted-mean cost on every OOD fleet no worse than the cold start" to G3.
3. **Fleet-mean init as a named curve.** "If the full prior ≈ fleet-mean init, the claim becomes 'fleet statistics give X× fewer pixels'." This matches v2's T1/T5 ablations but is stated more clearly.
4. **Interfaces and code layout.** Plain numpy/json, `measure()`, `oracle()`, trace files, prior files, and the `spintune/` module map. v2 has nothing this concrete. **Adopt as is**, with the changes in §6.
5. **The critical path is written down**, and off-path work is assigned to whoever is blocked.
6. **Tuesday is an idea-only pitch, with no plots or demo.** v2 §15.1 planned two evidence slides. Keep them as backup only.
7. **A 6-dot convergence test that reuses the drift check.** Because "double" windows contain transitions by definition, cross-correlation has features to lock onto. That avoids the featureless-patch problem the feasibility review raised for G5. It's a good design for whenever the multi-dot run happens.

---

## 4. Conflicts, most severe first

**1. The target has almost no headroom (blocking)**
- **Bobi:** the target is "double-dot regime with a clean transition in the window", with (1,1) as a stretch goal (`SPINTUNE-2.md` §2; PLAN decision 2).
- **Evidence:**
  - In QArray, both dots always exist, because it doesn't model dot formation. Any window beyond the first electron of each dot is "double".
  - 73–91% of random windows qualify (§5.1).
  - In QFlow, "double" is a small region set by barrier voltages, so the target meant something there. It doesn't carry over to QArray.
- **Consequence:**
  - Cold BO's first few Sobol points will usually succeed, so cold, fleet-mean and full-prior curves will all sit at about 1–2 windows.
  - The fitted prior mean (average converged gates) will be near the domain centre and uninformative.
- **Recommendation:** make **(1,1) the MVP target**, read through the anchor-and-count protocol (v2 §5).
  - Bobi's regime CNN stays as a reader component (it's still useful for "bad" and "no-dot").
  - The success definition becomes (1,1) by ground truth with a margin.
  - The review's builder flagged that a classical tuner may then sit near the cost floor. v2's week-1 G0 check measures that before any learning is built.

**2. The fleet spread is unsourced and too narrow (blocking)**
- **Bobi:**
  - each capacitance entry is nominal × lognormal(10%);
  - the only offset is a common back-gate shift N(0, σ_bg);
  - σ_bg is "picked so the in-distribution CSDs look varied but tunable" (PLAN decision 4).
- **Evidence:**
  - With no per-dot offsets, the (1,1) centre moves only ±0.1 cell widths across a fleet, and the fleet-mean start hits (1,1) on 100% of devices (`FEASIBILITY_REVIEW.md` addendum D).
  - With the sourced spreads, fleet-mean success drops to 1–6% (v2 §1.2). Those spreads are 22 mV per dot within a chip ([arXiv 2310.20434](https://arxiv.org/html/2310.20434)) and about 74 mV across a wafer ([arXiv 2501.10146](https://arxiv.org/abs/2501.10146)).
  - Picking σ_bg by eye is exactly the "headline from an easy fleet" anti-goal.
- **Recommendation:**
  - Adopt v2 §7: per-dot offsets, chip-level shared offsets and scales, wafer level, all in mV from sources.
  - Bobi's shifted fleet maps onto v2's OOD-wafer and OOD-noisy fleets.
  - Bobi's common back-gate offset becomes the chip-level common-mode term.

**3. The stopping rule is undefined, so ground truth can leak**
- **Bobi:** "A run succeeds when the final window is double by oracle labels". Pixels-to-tune is not defined beyond that, and the trace stores `success`.
- **Problem:** if the harness stops a run at the first oracle-double window, the oracle decides when the tuner stops. Pixels-to-tune is then optimistic, and false successes can't happen by construction.
- **Recommendation:**
  - The tuner must **declare** success on its own evidence (the CNN plus a confirmation window). The oracle then judges the declared point.
  - A wrong declaration is a **false success**, counted as a failure with the full budget charged.
  - v2 §6 and §11 have the wording, and set false successes at ≤ 1%.

**4. The headline statistic hides failures**
- **Bobi:** "median ≥ 2× fewer pixels than cold BO with no worse success rate".
- **Problem:** a median over successful runs hides a method that fails more often. "No worse success rate" helps, but isn't tied to a statistical test.
- **Recommendation:**
  - Primary statistic: the restricted mean cost, which charges the full budget for every failure, with a paired bootstrap CI over chips.
  - Report the median alongside it.
  - Keep 2× as the stretch bar, with v2's ≤ 0.8 as the practical bar.
  - Pitch it as a *pre-registered target*, not as the fact `SPINTUNE-2.md` line 6 currently states ("reaches a tuned double dot in at least 2× fewer measured pixels").

**5. Qiskit is a stretch goal, but the judges require it**
- **Bobi:** level (b) RB is in the stretch list, built only after T10 passes (PLAN, Stretch).
- **Problem:** you've confirmed Qiskit use is required, so it can't depend on the headline passing.
- **Recommendation:** add a parallel **Track F**, off the critical path. It holds v2 §8 and §10:
  - a CZ gate from the device Hamiltonian with a Hann-shaped pulse (verified);
  - InterleavedRB in Aer with noise fixed per sequence;
  - the IBM Open Plan pipeline check (10 free QPU minutes).
- **Fix Bobi's level-(b) text.** "A larger t_c gives a faster gate, but more barrier sensitivity" is not what the equations give.
  - With t_c = t₀·e^(κV_B), the relative error is σ_J/J = 2κσ_V, independent of the barrier setting (`FEASIBILITY_REVIEW.md` finding 3).
  - Our first estimate says the CZ error budget is dominated by dephasing and the residual floor, not by J noise (v2 §8.5).

**6. The 6-dot run is on the MVP path, but the topology is unconfirmed**
- **Bobi:** T12 runs the full 6-dot model with 5 pairs and iterative sweeps, in week 4. The demo "shows the 6-dot run".
- **Evidence:**
  - Equal1's 22FDX cells are linear arrays of **at most 3 dots** [sourced].
  - Its Si/SiGe paper describes "a **two-qubit** processor in a 6-quantum dot array" ([arXiv 2412.01920 v1](https://arxiv.org/abs/2412.01920v1)), not five tunable qubit pairs.
  - Neither source supports "5 pairs of a 6-dot chip".
- **Recommendation:**
  - Move T12 to stretch until Equal1 answers question 1 at the pitch.
  - If they confirm a 6-dot linear array, Bobi's design is good to build as is (iterative sweeps, 5-pass cap, convergence via cross-correlation).
  - Otherwise, the natural multi-device demo is v2's same-chip warm start across cells.

**7. Gate model vs Equal1's published layout**
- **Bobi:** 2 plungers + back gate searched, barriers fixed. Carrier, gate stack and sensing listed as unverified.
- **Now sourced** (v2 §3.1):
  - electrons;
  - 5 gates in series (QA0, QT0, QT1, QT2, QA1) with **no plunger gates**, where the barrier gates and back gate act as plungers;
  - a single-electron-box sensor read by rf reflectometry.
- **Recommendation:** relabel P1, P2 → QT0, QT2 and the barrier → QT1, and move the three items off the "unverified" list. Nothing else breaks.

**8. Some facts are out of date**
- **Bobi:** 99.4% 1Q (84 ns) and 98.4% 2Q (**72 ns**), from trade press (TQI).
- **Paper (v3):** CZ **200 ns**, F_CZ 99.30% at 350 mK and 98.41% at 750 mK; the Bell fidelities differ from v1 ([arXiv 2412.01920 v3](https://arxiv.org/html/2412.01920v3)).
- **Recommendation:**
  - Keep the TQI numbers labelled "vendor-reported".
  - Use the v3 paper for any physics.
  - Don't mix 72 ns and 200 ns on one slide.
  - Add the FD-SOI charge-noise range (1.7–6.5 µeV/√Hz), since Si/SiGe is 3–20× quieter.

**9. The compute table counts the wrong cost**
- **Bobi:**
  - the table charges 300 steps × 0.13 s (full 100×100 maps) per device, while `PLAN.md` uses 32×32 windows;
  - it justifies HPC with "every tuner step is a fresh simulation".
- **Evidence** [measured]:
  - a 32×32 QArray window costs ~10 ms;
  - **BoTorch's per-step overhead (GP refit plus acquisition, 3 gates) is 0.05–0.17 s** at 50–300 observations (§5.2).
- **Consequence:**
  - A 300-step BO run spends ~15–50 s fitting models and ~3 s simulating.
  - The totals land near Bobi's estimate (T7 ≈ 5–15 core-hours for 10³ devices), so the laptop plan is feasible, but the bottleneck is GP fitting, not simulation.
  - Caching scans, or a cluster, helps the simulation part only.
- **Recommendation:** fix the table's basis. Drop "fresh simulation per step" as the HPC argument; v2 §12 uses the spread sweep instead.

**10. The pixel budget and window span**
- **Budget:** 300 windows is 307,200 px per run. v2 uses 20,000 px.
  - Neither is wrong, but at 307k px almost every method succeeds, so reliability tells you nothing.
  - **Recommendation:** set the budget on the pilot so the cold baseline lands at 70–90% success. Bobi's own decision 6 bar for cold BO (≥ 70%) points the same way. Then report the full success-versus-budget curve.
- **Span:** `measure(dev, gates, span, res=32)` charges res² pixels whatever the span.
  - A tuner can take one window spanning the whole domain for 1,024 px.
  - **Recommendation:** fix the allowed spans or pitches (v2 §4.1: {0.5, 1, 2, 4} mV) and charge a per-query overhead.

**11. What the headline is**
- **Bobi:** "The tuner is the headline. The open benchmark harness is a supporting feature, not the product."
- **Ours:** C1 (the tuner) is primary. You chose that if classical search turns out to be near-optimal, we report it straight, with the benchmark plus measured headroom as the headline.
- **Recommendation:** these are compatible. The tuner is the headline if G0 and G3 pass, and the benchmark is the headline otherwise. Write the same sentence into both documents.

**12. Smaller inconsistencies inside Bobi's documents**
- **QFlow's role:**
  - `SPINTUNE-2.md` says "a CNN trained on QArray plus QFlow".
  - `PLAN.md` says "QFlow accuracy is reported separately, with no bar".
  - **Pick test-only**, as v2 and the feasibility review do.
  - QFlow's "no-dot" (no dot formed) also differs from QArray's "zero electrons".
- **Statistics:** 3 seeds and medians, with no confidence intervals or test-once rule. Add v2 §11.4–11.5: cluster bootstrap over chips, and a tagged freeze before the test fleet.
- **Missing pieces v2 already covers:**
  - real-device external tests (QDSD electron-count labels; D-CSD);
  - the QDarts OOD fleet;
  - a time-cost model;
  - the oracle-start cost floor and the week-1 headroom gate.

---

## 5. New measurements for this review

### 5.1 How common is "double" under PLAN decision 2? [measured]

**Set-up:**
- QArray double dot, noiseless, T = 0.
- 60 devices drawn per PLAN decision 4: lognormal(10%) capacitances, common back-gate offset σ = 0.5 V.
- Random 32×32 windows inside the plunger domain [−2, 8] V (model units). That's ~0–7 electrons per dot, the range of the 100×100 timing map.
- Labels follow PLAN decision 2 exactly.

| Window span | "double" | "single" | "no-dot" | other |
|---|---:|---:|---:|---:|
| 1.0 V (~1 charge period) | **73%** | 17% | 5% | 5% |
| 2.0 V (~2 periods) | **85%** | 11% | 3% | 2% |
| 3.3 V (~3 periods) | **91%** | 5% | 1% | 3% |

A domain concentrated on the empty corner would lower these numbers. But in any multi-electron region, the honeycomb fills the window.

Script: `regime_check.py`.

### 5.2 BoTorch per-step overhead [measured]

**Set-up:**
- `SingleTaskGP` refit plus `qLogExpectedImprovement` optimisation (10 restarts, 256 raw samples).
- 3D search space, single thread, M4 Pro, BoTorch latest on Python 3.12.

| Observations n | GP fit | Acquisition | Total per step |
|---:|---:|---:|---:|
| 50 | 0.03 s | 0.03 s | 0.05 s |
| 100 | 0.02 s | 0.04 s | 0.07 s |
| 200 | 0.04 s | 0.06 s | 0.10 s |
| 300 | 0.08 s | 0.09 s | 0.17 s |

The first call takes ~1.4 s (warm-up). Script: `bo_overhead.py`.

Both scripts are in the session's temporary scratch folder, with the earlier checks. Copy them into `checks/` along with the v2 scripts (v2 §13, row 3).

---

## 6. Proposed merge: `PLAN.md` stays the checklist, with these edits

| PLAN item | Change | Source |
|---|---|---|
| Decision 1 (32×32 windows) | Keep. Add fixed pitches {0.5, 1, 2, 4} mV and a per-query overhead in the cost | v2 §4 |
| Decision 2 (labels) | Keep the regime labels as a reader output. **Target becomes (1,1)** via anchor + count; add transition masks | v2 §5; §4 conflict 1 |
| Decision 3 (oracle judges) | Keep. Add: the tuner declares, the oracle judges, false successes count as failures (≤ 1%) | v2 §6, §11 |
| Decision 4 (fleet) | Replace with the sourced hierarchical fleet in mV. Bobi's shifted fleet → OOD-wafer / OOD-noisy | v2 §7 |
| Decision 5 (budget 300 windows) | Set from the pilot so the cold baseline lands at 70–90%. Primary statistic: restricted mean cost | §4 conflicts 4, 10 |
| Decision 6 (bars) | Keep CNN ≥ 90%. Add G0: headroom ≥ 30% between the best classical tuner and the oracle-start floor, in week 1 | v2 §11.3 |
| T5 (heuristics) | Add **T★ oracle-start** and scan-and-fit; run G0 at the end of week 1 | v2 §6 |
| T6–T9 (cold BO, logs, prior, warm BO) | Keep Bobi's "prior from logs". The objective must use counted occupancy; or use v2's lattice tracker with the same policy for cold and warm (decision 3 below) | §3 item 1; v2 §6 |
| — | **Add Track F (Qiskit, protected):** Hamiltonian CZ (Hann), Aer IRB, IBM Open Plan run | v2 §8, §10; §4 conflict 5 |
| — | **Add same-chip history** (v2 T6) as the second warm-start curve | v2 §6 |
| T12 (6-dot) | Move to stretch until Equal1 confirms the layout | §4 conflict 6 |
| T10 (harness) | Add paired bootstrap CIs, OOD "never worse", a tagged freeze before the test fleet | v2 §11 |
| Before Tuesday | Idea-only pitch (Bobi). Update `SPINTUNE-2.md` with the §4 conflict 7–8 facts and soften the 2× wording to "target" | §4 conflicts 4, 7, 8 |

---

## 7. Decisions for the two of you (each one changes what gets built)

1. **Target:** (1,1) via anchor and count as the MVP (recommended, because the double regime has almost no headroom in QArray), or keep the double regime and accept that the 2× result can't be informative.
2. **6-dot run:** stretch until Equal1 confirms the layout (recommended), or keep it on the MVP path.
3. **Search policy:** v2's Bayesian lattice tracker, or Bobi's BoTorch BO with an objective based on counted occupancy. Either works if cold and warm share it. BoTorch costs ~0.1 s per step (§5.2) and doesn't count electrons on its own.
4. **Which document is the source of truth:** we suggest v2 for *what and why*, `PLAN.md` for *who and when*, and `SPINTUNE-2.md` as the pitch notes, all updated to agree.
