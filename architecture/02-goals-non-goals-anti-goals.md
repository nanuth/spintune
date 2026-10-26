[SpinTune v5 design](README.md) › 2. Goals, non-goals, anti-goals

# 2. Goals, non-goals, anti-goals

**Goals**
1. **C1, the research question:** *when does information from previously tuned cells reduce acquisition cost without increasing wrong charge declarations?*
   - **Test:** on unseen simulated cells, the shared policy with chip and wafer history (T6) against the same policy started cold (T3), and against a plain running mean of the same history (T3-H).
   - **Break-even map:** the gain or loss as a function of how much variation cells on a chip share and how predictable the charge period is ([§12](12-compute-plan.md)), including where history stops paying.
   - **Ablation:** knowledge of the start point vs knowledge of the period.
   - Whether C1 is the headline is set by G0 ([§11.4](11-success-measurement.md#114-gates-thresholds-frozen-at-the-tagged-commit)).
2. **C4, the benchmark (deliverable either way):**
   - the device generator and frozen fleets;
   - the metered interface with persistent device state;
   - a scoring contract that any tuner can use ([§2.2](#22-benchmark-scoring-contract-design-call));
   - the evidence rule and one success definition;
   - the baselines, including the oracle-start reference T★;
   - scripts that regenerate every figure from logs.
3. **Trust:** the wrong-declaration rate, with abstention and an upper bound, is a primary metric for every tuner.
4. **C2 (protected, because Qiskit is required):**
   - a model-based CZ error budget built from the device Hamiltonian, presented as a sensitivity study;
   - an Aer RB pipeline validated on known channels;
   - an IBM hardware run, as a scheduled demonstration with a fallback.
5. **C3 (stretch, first to cut):** drift detection and local re-tune.

**The protected outcome:** one correctly metered, sensor-only run that reaches and verifies (1,1), followed by an honest comparison against conventional history reuse. Everything else is built around it.

**Non-goals**
- Dot formation, barrier pinch-off, spin readout, and qubit-level calibration on spins.
- Estimating tunnel coupling, lever arms or spin parameters from charge data. This is infeasible in this regime ([§8.4](08-physics-layer-cz-error-budget.md#84-why-the-tuner-doesnt-estimate-these-parameters)).
- Joint tuning of a multi-cell chip or a 6-dot array ([§3.4](03-scope-and-device-template.md#34-deferred-and-stretch)).
- BO-based search (optional comparator only).
- Replacing or integrating with any commercial tuner.
- Real Equal1 hardware. We use it if offered; nothing depends on it.

**Anti-goals (a failure even if it technically works)**
- A headline that comes from an easy fleet, a weak baseline, a generous cold-start box, or a cost metric or budget picked after seeing results.
- A tuner that looks cheap because it stops early and wrongly. Wrong declarations are failures.
- Evaluator ground truth leaking into anything a tuner can see, including its history.
- Calling an idealized policy estimate a floor, or a pixel ratio a time saving.
- Claiming "≤ 1%" or "no silent failures" from an observed rate or from zero observed errors.
- Quantum for show ([§10.3](10-quantum-layer-qiskit.md#103-course-content-deliberately-not-used)), or calling a model-based Aer result "verification" of a physical qubit.
- Unsourced or outdated numbers on slides.

## 2.1 Related work, and what is new here

| Element | Existing evidence | What SpinTune adds |
|---|---|---|
| Ray measurements | Ray-based state identification and tuning, validated experimentally ([Zwolak et al., PRX Quantum 2, 020335 (2021)](https://doi.org/10.1103/PRXQuantum.2.020335)) | A specific evidence protocol, and a fair accounting of its cost |
| Uncertainty-aware charge tuning | Online single-dot tuning into the one-electron regime using neural-network uncertainty; 95% success over 20 runs ([Yon et al., Nano Lett. 25, 3717 (2025)](https://doi.org/10.1021/acs.nanolett.4c04889)) | Wrong-declaration risk, measured across explicit device shifts |
| FD-SOI line segmentation and target selection | CEA-Leti 300 mm FD-SOI: 1,015 experimental diagrams, nine geometries, seven wafers, 80.0% offline tuning success ([Samaha et al., arXiv 2604.13662 (2026)](https://arxiv.org/abs/2604.13662)) | Sequential acquisition, history reuse and a reproducible comparison. Their 80% is offline, on a different process, task and sensor, so it is not comparable with a synthetic target |
| Autonomous spin-qubit tuning | A full sequence from a grounded device to Rabi oscillations, Ge/Si nanowire ([Schuff et al., Nature Electronics (2026)](https://doi.org/10.1038/s41928-025-01562-4)) | A narrow, well-measured charge-tuning component that could fit into such a workflow |
| RF/FPGA acceleration | 9.8× faster measurement gave 2.2× faster total initialization, limited by Python execution ([Roux et al., IEEE TQE (2026)](https://doi.org/10.1109/TQE.2026.3670353)) | Time accounted per query, so pixel savings aren't mistaken for time savings |
| Hierarchical fleet prior | Empirical Bayes and shrinkage are standard methods | Evidence on when chip and wafer history helps, hurts, or adds nothing |
| Open benchmark | The community has asked for datasets, benchmarking and standardisation ([Zwolak et al., npj Quantum Inf. 10, 105 (2024)](https://doi.org/10.1038/s41534-024-00878-x)) | An executable protocol that scores independent tuners and reports their failures |

## 2.2 Benchmark scoring contract [design call]

- **Outcome scoring is separate from our policy.** A tuner is scored on what it declares and what it spent, not on whether it used our evidence rule:
  - the declared V\*, or an abstention with a reason;
  - the evaluator's verdict: count, margin, nominal success and hold success ([§11.2](11-success-measurement.md#112-success-for-one-cell));
  - cost: pixels, queries, RF time, compute;
  - risk: wrong declarations over all declarations, with bounds ([§11.5](11-success-measurement.md#115-statistics)).
- **Tuners that use our interface** run through the metered session directly.
- **External tuners** plug in through an adapter that maps each scan they request onto billed windows or rays at the nearest allowed pitch and size. Their own evidence, in whatever form, is logged but not required.
- **Constrained-protocol results**, meaning comparisons that require the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence, are labelled as such.
- **The value of the evidence rule is measured at comparable risk.** The benchmark includes credible heuristics with and without extra verification:
  - T2's scan-and-fit, with its native count (T2-N) and with the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence (T2);
  - the shared policy with its stopping length swept from a 1.5-period shortcut to the full L (T3-L).

  The rule's value is the cost difference at matched wrong-declaration rate ([§6.3](06-tuners-and-baselines.md#63-comparisons-each-one-answers-a-different-question) f), not its win over a known-broken shortcut.

---

← [1. Design decisions and evidence](01-design-decisions-and-evidence.md) · [Index](README.md) · [3. Scope and device template](03-scope-and-device-template.md) →
