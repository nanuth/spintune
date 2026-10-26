# SpinTune implementation plan

The working checklist for building what [SPINTUNE.md](SPINTUNE.md) describes, due **Fri 27 Nov**. Who does what is decided later, so tasks are grouped into tracks that can run in parallel.

Anything marked **PROPOSED** is a judgement call and needs both of you to confirm it before it's built on.

---

## Open decisions (confirm first)
1. **Window size per tuner step. PROPOSED: 32×32 (1,024 pixels).** A full 100×100 CSD per BO step costs 10⁴ pixels, so line-scan heuristics would win on pixels almost by default.
   - The CNN trains on 32×32 crops, and QFlow maps get cropped or downsampled to match.
   - This also matches the drift window.
   - The compute table in SPINTUNE.md assumes 100×100, so smaller windows only make it cheaper.
2. **Labels. PROPOSED:** the label comes from QArray's ground-truth occupation over the window.
   - **no-dot:** zero electrons everywhere.
   - **single:** only one dot's occupation changes.
   - **double:** both dots' occupations change, and an interdot transition is present.
   - **bad:** the sensor's signal-to-noise is below a threshold, or a latching artefact is present.
   - QFlow's left / centre / right single-dot classes all map to single.
3. **Success is judged by ground truth, not by the CNN.** A tuner that's scored by its own classifier can fool itself.
   - A run succeeds when the final window is double by oracle labels, within the pixel budget.
   - The CNN's P(double) is only the BO objective.
4. **Fleet distribution. PROPOSED, in QArray model units:**
   - **In-distribution:** each capacitance entry is the nominal value × lognormal(σ = 10%). The back-gate offset is N(0, σ_bg).
   - **Shifted fleet:** σ = 25%, the back-gate offset mean moves by +2σ_bg, and telegraph noise amplitude is ×3.
   - Nominal values start from `bench_qarray.py`, and σ_bg gets picked so the in-distribution CSDs look varied but tunable.
5. **Pixel budget per run. PROPOSED: 300 windows' worth** (300 × 1,024 pixels). A run that hits the cap counts as a failure.
6. **Bars for the intermediate tasks. PROPOSED:**
   - The CNN reaches ≥ 90% accuracy on held-out QArray windows. QFlow accuracy is reported separately, with no bar.
   - Cold BO succeeds on ≥ 70% of in-distribution devices.

---

## Interfaces
Use plain numpy and json, so the two of you can work on different pieces without stepping on each other.

```
Device            dict: Cdd, Cgd, Cds, Cgs, noise params, bg_offset, position ('edge'|'interior'|None), seed
fleet file        fleets/<name>.npz   — N devices, plus the generator params in the header
measure(dev, gates: float[3], span, res=32) -> float32[res,res]     # every call is counted by the harness
oracle(dev, gates, span, res) -> label int8                          # ground truth, for scoring and the ablation only
tuner.run(measure, budget_px) -> trace
trace             runs/<tuner>/<fleet>/<seed>/<device>.json:
                  steps: [{gates, px, p_double}], final_gates, px_total, success
prior file        priors/<name>.json: {position: {mean: float[3], lengthscale: float[3]}}
```

`gates` = [P1, P2, back gate]. Barriers are fixed (see SPINTUNE.md).

---

## Code layout
```
spintune/
  fleet.py      device sampling, measure(), oracle()        (T1, T2)
  data.py       window generation, labels, QFlow loading    (T3)
  cnn.py        model, training, inference                  (T4)
  tuners.py     random, heuristic, BO cold / mean / prior   (T5, T6, T9)
  prior.py      fit the prior from tuning logs              (T8)
  harness.py    run tuners × fleets × seeds, plot, win bar  (T10, T11)
  sixdot.py     6-dot sweeps, drift check                   (T12, T13)
fleets/ runs/ priors/ figs/        generated output, git-ignored
bench_qarray.py
```

---

## Tasks
"Needs" lists the hard dependencies. "Done" is the check that has to pass before the task counts as finished.

### Track A: simulation and data
- **T0. Setup.** Initialise git, write `requirements.txt` (qarray 1.6, torch, botorch, numpy, scipy, matplotlib), and get the env working on both laptops.
  - **Done:** `bench_qarray.py` runs on both machines, and the timings are written down.
- **T1. Fleet generator.** Sample the in-distribution, shifted and training fleets from the decision 4 parameters, keeping the training and test fleets **disjoint**.
  - **Needs:** T0.
  - **Done:** the same seed gives the same fleet, and a grid of 16 CSDs from each fleet looks visibly different.
- **T2. `measure()` + `oracle()` + pixel counter.**
  - **Needs:** T1.
  - **Done:** the counter equals the sum of `res²` over all calls, and `oracle()` agrees with the occupation map on 5 hand-checked windows.
- **T3. Training windows + labels.** Generate ~200k labelled 32×32 windows from the training fleet (decision 2), plus a loader that turns QFlow lite into the same format.
  - **Needs:** T2.
  - **Done:** class balance is reported, and 20 random windows per class have been eyeballed.

### Track B: sensing and baselines
- **T4. CNN.**
  - **Needs:** T3.
  - **Done:** it meets the decision 6 bar on held-out windows, with QFlow accuracy reported.
- **T5. Random + heuristic baselines.** The heuristic is line scans plus edge/Hough detection. Both are scored by the pixel counter.
  - **Needs:** T2.
  - **Done:** both run end to end and write traces.
- **T6. Cold BO.** BoTorch over the 3 gates, maximising the CNN's P(double).
  - **Needs:** T4, T2.
  - **Done:** it meets the decision 6 bar on 100 in-distribution devices.

### Track C: fleet prior (the novelty)
- **T7. Training-fleet tuning logs.** Run cold BO over the **training** fleet, starting at 10³ devices. This is a fleet-evaluation-sized job, ~1.4 h on 8 cores.
  - **Needs:** T6.
  - **Done:** there's one trace per device, and the success rate is reported.
- **T8. Fit the prior.**
  - **mean:** the average converged gates of the successful runs.
  - **lengthscale:** the median of the fitted GP lengthscales.
  - Fit it per position for the 6-dot run, and as a single prior for the single-pair experiments.
  - **Needs:** T7.
  - **Done:** the prior file is written, and the mean lands inside the double-dot region for most training devices.
- **T9. Warm BO variants.**
  - **fleet-mean init:** cold BO, started at the prior mean.
  - **full prior:** the prior mean function plus priors on the lengthscales.
  - **Needs:** T8.
  - **Done:** both beat cold BO on 50 in-distribution devices, or you know why they don't.

### Track D: scoring (the 27 Nov result)
- **T10. Harness.** Run tuners × {in-distribution, shifted} × 3 seeds over 10³ test devices. Draw the headline plot of pixels-to-tune with 3 curves plus the baselines, and print **PASS/FAIL against the win bar** automatically.
  - **Needs:** T5, T9.
  - **Done:** one command regenerates the plot and the verdict from the saved traces.
- **T11. Oracle-label ablation.** Rerun the BO variants using `oracle()` in place of the CNN.
  - **Needs:** T10.
  - **Done:** it's on the backup slide.

### Track E: the 6-dot run
- **T13. Drift and convergence check.** 2D cross-correlation of a 32×32 window against a reference gives the shift. A pair is stable when the shift is below one transition width **and** the CNN still says double.
  - **Needs:** T4.
  - **Done:** an injected shift of k pixels is recovered within ±1 pixel.
- **T12. 6-dot sweeps.** Use the full 6-dot model, tune pairs 1–2 through 5–6, then re-check all of them, and repeat until stable or the 5-pass cap is hit. Compare cold vs per-position prior on 20 chips.
  - **Needs:** T13, T9, and a 6-dot fleet from T1.
  - **Done:** a table and plot of total pixels and passes, cold vs warm.

### Stretch (only after T10 passes)
(1,1) occupancy target · virtual gates · level (b) RB · drift-injection demo · real Equal1 CSDs · dashboard.

---

## Schedule
| Week | Tasks | Gate at the end of the week |
|---|---|---|
| W1 (to 3 Nov) | T0, T1, T2, T3, T5 | Labelled windows exist, and the baselines run |
| W2 (to 10 Nov) | T4, T6, T13 | The CNN and cold BO both meet their bars |
| W3 (to 17 Nov) | T7, T8, T9, T10 | **Headline plot plus PASS/FAIL verdict (must be done)** |
| W4 (to 27 Nov) | T11, T12, then stretch | 6-dot cold vs warm, then demo prep |

**Critical path:** T1 → T2 → T3 → T4 → T6 → T7 → T8 → T9 → T10. Track B's baselines (T5) and Track E's drift check (T13) sit off that path, so give them to whoever is blocked waiting on it.

## Risks
- **Cold BO misses its bar (T6).** Then the prior has nothing good to learn from. Fallback: let the heuristic generate the training logs.
- **CNN trained on sim, tested on sim.** That gap is invisible here. The shifted fleet is the only proxy until real Equal1 CSDs arrive.
- **The full prior ≈ fleet-mean init (T9).** Then pivot the claim to "fleet statistics give X× fewer pixels", as already agreed.
- **The win bar fails (T10).** Then report it honestly: "safe warm start, modest gain". Don't move the bar after seeing the result.
