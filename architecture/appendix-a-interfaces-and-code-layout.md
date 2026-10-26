[SpinTune v5 design](README.md) › Appendix A. Interfaces and code layout

# Appendix A. Interfaces and code layout

Plain numpy and json, so the two of you can work on separate pieces.

```text
Cell            dict: hidden params (evaluator only), wafer_id, chip_id, cell_index, die_xy, seed
fleet file      fleets/<name>.npz + fleets/<name>.json   (generator params, seeds, split, matched-OOD map)
Session         s = harness.open(cell, scenario)         # persistent noise/latching state + ledger
s.window(center: float[2], pitch, size) -> float32[size, size]        # billed
s.ray(start: float[2], direction: float[2], pitch, n) -> float32[n]   # billed; 8 <= n <= 64
s.declare(v_star: float[2], evidence) | s.abstain(reason)             # ends the run
evaluator.judge(cell, trace) -> {outcome: success|wrong_count|inadequate_margin|abstain|over_budget,
                                 hold_success, wrong_anchor, margin, occupancy}   # after the run only
tuner.run(s, metadata, history) -> trace
trace           runs/<tuner>/<fleet>/<seed>/<cell>.json:
                queries [{type, args, px, t_query, t_cum}], certificate, declaration,
                totals {px, rf_s, elapsed_s, dc_s, n_queries, slew_mV, compute_s}
history         this tuner's own earlier traces on this chip and wafer (declarations, measured lines, P, abstentions)
log file        logs/<train_fleet>/<tuner>.jsonl   (training-fleet tuning logs + verification flag)
prior file      priors/<name>.json: {fleet_mean[2], cov_wafer, cov_chip, cov_cell, radial_coeff, P_model}
```

Axes are [QT1, QA1] for the primary template and [P1, P2] for the generic one. QT2, BG and QT0 (sensor compensation) are fixed per scenario.

```text
spintune/
  fleet.py       hierarchical sampling, splits, matched OOD variants        (A1)
  device.py      QArray wrapper, QDarts worker, persistent noise/latching    (A2, A4)
  interface.py   Session: window/ray, ledger, cost model, caps, tile cache   (A2)
  evaluator.py   judge(), margins, masks: the only code that reads params    (A3)
  anchor.py      certificate, count, confirmation, declaration (shared)      (B1)
  tuners/        oracle_start.py, random_start.py, scan_fit.py (T2, T2-N), raynav.py (T3, T3-M, T3-H, T3-L), spintune.py (T5, T6)
  reader.py      v1 signal processing; optional U-Net-lite + ray head      (R1, R2)
  prior.py       fit hierarchical prior from verified tuning logs            (D2)
  harness.py     tuners × fleets × seeds, wafer bootstrap, gates, plots      (E1)
  qiskit_cz/     hamiltonian.py (2x2 block), budget_map.py, rb_aer.py, ibm_run.py   (F1–F4)
  drift.py       cross-correlation monitor (stretch)
checks/          evidence scripts (§1.2)
fleets/ runs/ logs/ priors/ figs/     generated output, git-ignored
```

---

← [18. Scaling](18-scaling.md) · [Index](README.md)
