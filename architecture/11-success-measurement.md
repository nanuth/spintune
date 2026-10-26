[SpinTune v5 design](README.md) › 11. How success is measured

# 11. How success is measured (frozen before the test fleet runs)

## 11.1 Primary question

*When does information from previously tuned cells reduce acquisition cost without increasing wrong charge declarations?* On unseen simulated 22FDX-style cells, T6 is compared with:
- the same policy started cold (T3);
- conventional use of the same history (T3-H);
- the best classical tuner (the comparator, [§6.3](06-tuners-and-baselines.md#63-comparisons-each-one-answers-a-different-question) d).

## 11.2 Success for one cell

**Nominal success (primary; all must hold):**
1. The tuner declares V\*. Whether the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence and [§5.2](05-reading-the-device.md#52-confirmation-and-declaration) confirmation were present is recorded as a separate flag, so tuners that don't use them (T2-N, external tuners) are scored on the same terms. For the shared policy they are part of the policy.
2. **QArray fleets:** the noiseless (T = 0) equilibrium occupancy of the nominal device at V\* is (1,1).
   **QDarts fleet:** at V\*, the dominant charge configuration in the thermal state at the fleet temperature is (1,1), with probability ≥ 0.9.
3. **Margin:** ≥ 0.15·P along every bounding transition's normal (for QDarts, measured to the 0.5-probability contours), and ≥ 3σ of projected quasi-static gate noise.

"Nominal" means the device without telegraph shifts, drift or latched state: the operating point a tuner is meant to find.

**Hold success (reported beside it, not gated):** after the declaration, the simulator holds V\* for 10 s of instrument time with every noise process and the latched state running. 10 s, not 1 s: the slowest fluctuators switch at ~1 Hz, and over 1 s a 1 Hz fluctuator stays put 37% of the time, so the hold would miss its other state. Over 10 s that drops below 0.01%. 1/f drift is not the reason: over 60 s it moves the gates by ~30–50 µV, ≈ 2% of the 0.15·P margin [computed]. The cell holds if its actual occupancy is (1,1) for ≥ 99% of that time. Telegraph shifts of up to 0.2·P per fluctuator can exceed the 0.15·P margin, so hold success can be lower than nominal success. The gap is a finding.

**Outcomes:**
- **Success:** nominal success.
- **Wrong declaration:** a declared V\* that fails step 2 (**wrong count**) or only step 3 (**inadequate margin**). Where a wrong anchor (v0 not (0,0)) caused it, that is logged as the cause.
- **Abstention:** the tuner stops with a reason, including the domain limit.
- **Over budget:** no declaration within B or B_t.

Cells whose certificate can't fit in the domain are recorded. Results are shown for all attempted cells and for reachable cells.

## 11.3 Scorecard

| Question | Metric | How it's reported |
|---|---|---|
| Does the tuner work? | **Reliability:** successes / all attempted cells | All cells and reachable cells; 95% CI; failures by cause |
| Can its declarations be trusted? | **Wrong-declaration rate:** wrong declarations / all declarations | Counts by type (wrong count, inadequate margin); abstention rate; exact one-sided 95% upper bound; the chip-level rate ([§11.5](#115-statistics)) |
| Is ≤ 1% established? | The upper bound | "≤ 1%" only if the bound is ≤ 1%; otherwise "observed X%, upper bound Y%" |
| Does it save acquisition? | **Paired pixel ratio** R_X/Y = Σ px_X / Σ px_Y over cells where both succeed | Labelled as conditional on joint success, always with the 2×2 table of joint success/failure counts |
| Does it reduce operational cost? | **All-cell elapsed cost:** RF time plus compute for every attempted cell, plus the frozen fallback (B px, B_t/1.25 s) for each non-success ([§4.2](04-measurement-interface.md#42-cost-model-pixels-are-not-time)) | Also in pixels; the failure-penalised restricted mean; success-vs-budget curves in pixels and RF time |
| Is learning necessary? | T6 vs T3-H (equal information); T6 vs T5 (value of history) | Under the reliability and wrong-declaration constraints of G3 |
| Does it tolerate shift? | Non-inferiority on each tested OOD fleet | The margins and the scenario list. OOD-spec goes into the trust report |
| Does it scale? | Per chip: completion, number of wrong declarations, all-cell cost including cell 1 | Cost vs cell position k |
| Cost above the reference | Paired cost minus T★'s | Within this policy only |
| Runtime | Tuner compute per cell; simulator time | — |
| C2 | Error-budget map; O1 loss vs map optimum; Markovian RB recovery; quasi-static decay report; rejected parameter sets | — |
| C3 (stretch) | Detection recall, false alarms per hour, delay, recovery cost | — |

## 11.4 Gates (thresholds frozen at the tagged commit)

| Gate | Question | Pass criterion |
|---|---|---|
| **G0 Headroom** (end of week 2; sensor-only, on pilot + validation) | Is there avoidable cost to save, within this policy? | Computed from sensor-only query traces: integer queries, the [§5.2](05-reading-the-device.md#52-confirmation-and-declaration) confirmation rules, retries, domain checks and complete chip histories. h = 1 − R_T★/ref in pixels, and h_t the same in RF time. "ref" is whichever cold classical baseline, T2 or T3, has the lower paired pixel cost. **Practical targets, relative to the measured headroom:** history must capture at least a third of it, so R_T6/T3 ≤ 1 − h/3 in pixels and ≤ 1 − h_t/3 in RF time. Both are computed from G0 and frozen at the tag. <br>**Pre-registered branches, decided on the lower one-sided 95% wafer-bootstrap bound of min(h, h_t)** (pilot + validation), never on the point estimate. Using both units means the branch can't depend on whichever happens to be kinder, and the bound means a point estimate near a line can't decide it. In the wide-period estimate the units disagree (27% px, 40% time). <br>**bound ≥ 30%:** C1 is the headline. <br>**10% ≤ bound < 30%:** headline = the benchmark and the measured error/cost trade-off; C1 is a measured secondary result; T6-NN dropped. <br>**bound < 10%:** report the headroom; no practical target; build nothing learned beyond T5/T6 shrinkage; put the time into C2 and the external tests. <br>**"Faster" wording**, in any branch, also needs h_t ≥ 10% and G3(c′). <br>**Idealized pre-pilot estimate: h ≈ 32%, h_t ≈ 33%** (in-distribution, [§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)), so targets of ≈ 0.89 in both units. The idealized history ratios (0.86 px, 0.73 time) pass, the pixel one narrowly. A point estimate of 32% will most likely have a lower bound under 30%, so **the middle branch is the expected outcome**; C1 is still measured and reported in full there. Noise, reader v1 and simulated training-fleet logs decide. The fleet is never made harder or easier to change h |
| **G1 Generator and certificate** | Does the simulator do what we say, and does the evidence rule hold in the noiseless model? | Lattice matches `optimal_Vg` within 1 px. Noise PSD slope within the set value ± 0.1. Certificate tests [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) (a) and (c) pass through the metered session: 100% correct-or-abstain on noiseless cells over each scenario's P range up to P_max; the ambiguity test passes. The persistent-state and latching-partition tests pass ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)) |
| **G2 Reader** | Can we read scans, and does the evidence rule survive the frozen reader? | Transition-mask F1 ≥ 0.9 in-distribution. Wrong-anchor rate ≤ 0.5% on the nominal-noise certificate set ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b), with its upper bound reported. Reported at the final, never hidden: the stress scenarios, OOD results, QDSD single-dot counting, D-CSD line F1 on our hand-labelled scans |
| **G3 Warm start (C1)**, ID test | Does it save measurement without losing trust? | (a) T6 reliability ≥ 90%, **and** the lower 95% bound of (reliability T6 − T3) ≥ −2 points. <br>(b) Wrong declarations: the one-sided 95% upper bound over all T6 declarations ≤ 1%, which establishes "≤ 1%", provided the [§11.5](#115-statistics) cascade check passes; if it fails, (b) is "not established" and the chip-level bound is the one quoted. If only the observed rate is ≤ 1%, G3(b) is "not established" and the report says "observed X%, upper bound Y%". The chip-level rate is reported beside it. <br>(c) Wafer-bootstrap 95% CI of the paired pixel ratio R_T6/T3 entirely < 1, **and** the point estimate ≤ the G0 practical target (1 − h/3). (c′) For speed wording, the same test on the all-cell RF elapsed cost, against 1 − h_t/3. <br>(d) CI of R_T6/comparator entirely < 1, with reliability non-inferior as in (a). Otherwise it is reported as "no gain over conventional use of the same information". <br>(e) **Pre-specified non-inferiority on the tested shifts:** on each OOD fleet (hot, noisy, crosstalk, wafer, simulator), the upper CI bound of R_T6/T3 ≤ 1.05, the point estimate of (reliability T6 − T3) ≥ −2 points, and its lower 95% bound ≥ −5 points. A claim about all five fleets at once uses Bonferroni-adjusted (one-sided 99%) intervals. Missing a bound means "not shown", not "worse", unless the point estimate itself is beyond the margin. <br>(f) ≥ 75% reliability on each OOD fleet. <br>**C1 primary pass = (a) + (b) + (c), at the frozen default fleet.** (c′), (d), (e), (f) and G3h are reported alongside it and qualify the wording; none of them can rescue a failed primary. <br>**Reported, not gated:** T6 reliability − T2 reliability, with a wafer-bootstrap CI, so the gap to the expensive, reliable baseline is visible. <br>A G3 pass is a pass *at the assumed hierarchy*; any claim beyond it comes from the break-even map (E4), and the gate slide says so |
| **G3h Hierarchy** | Does chip history add value beyond the fleet? | CI of R_T6/T5 entirely < 1 for cells k ≥ 3 |
| **G4 Error budget (C2)** | Is the Qiskit model sound, and what does it say? | (a) Block propagator vs 4×4 exponential: difference ≤ 10⁻¹². <br>Pure-ZZ formula vs full H, for J_max/ΔE_z ≤ 0.08 and δJ/J ∈ {0.3%, 1%, 2%}: \|Δ − ZZ\| ≤ 0.01·ZZ + 10⁻⁷, where Δ = (1 − F_full(δJ)) − (1 − F_full(0)). Outside that range the full H is the only reference. <br>(b) Aer IRB recovers the injected Markovian errors within systematic bounds plus fit CI. <br>(c) Quasi-static and IBM results are reported descriptively, not as pass/fail. <br>Rejected parameter sets (negative residual, dephasing over budget) are counted and reported. <br>Result: the map and the O1 statement per scenario |
| **G5 Drift** (C3, stretch) | Cheap recovery? | Recall ≥ 90% at ≤ 1 false alarm per simulated hour; recovery ≤ 25% of restart cost at equal success |

## 11.5 Statistics

- **Paired design:** every tuner runs on the same cells with the same exogenous noise ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)).
- **The unit of inference is the wafer.** Cost ratios, reliability and their differences use a wafer-level cluster bootstrap: resample wafers with replacement, keeping their chips, cells, histories and tuner seeds intact. Repeated tuner seeds do not add independent devices.
- **Rare events need their own bound.** A bootstrap can't bound a rate with zero observed events, because every replicate is zero. So wrong-declaration rates use:
  - the exact (Clopper–Pearson) one-sided 95% upper bound over declarations, labelled "assumes independent declarations";
  - the same bound over chips for the fraction of chips with ≥ 1 wrong declaration, which doesn't assume independence within a chip.
  - With 900 declarations, 0 / 1 / 3 / 4 errors give bounds of 0.33% / 0.53% / 0.86% / 1.01%. With 100 chips and none affected, the chip-level bound is 3.0%, so "≤ 1% of chips" can't be shown (that needs ~300 chips).
  - **Cascade check (T6, T3-H):** these tuners feed their own declarations into later cells, so one wrong declaration can make the next more likely. Compare the wrong-declaration rate on cells that follow a wrong declaration on the same chip with the rate after correct ones (exact test). A difference means declarations aren't independent: the per-declaration bound is dropped from the claim and the chip-level bound is quoted. Strictly, wafer history also links chips; that is stated in a footnote (the wafer-level bound, 0/20 → 14%, is too wide to use).
- **OOD comparisons** are paired by underlying cell.
- **Paired cost ratios** use only cells where both tuners succeed; every report states the dropped cells and the 2×2 joint counts. Reliability differences use all cells.
- **Multiple scenarios:** per-scenario intervals are unadjusted 95%. Any "on all scenarios" claim uses Bonferroni across the scenarios it names.
- **Seeds:** 3 per stochastic tuner on the pilot; up to 5 at final if the pilot's interval widths justify it.
- **Comparator choice:** the primary classical comparator and every threshold are chosen on validation, never on test.
- **Sizing the test fleet:** the pilot sizes it for all three claims, not only the cost ratio. The targets are a CI half-width ≤ 0.05 on R_T6/T3, ≤ 2 points on the reliability difference, and ≥ 300 declarations (so that zero errors gives a bound ≤ 1%). 90% reliability on 1,000 cells gives a binomial half-width of ≈ 1.9 points before clustering; clustered widths come from the pilot. The cap is 40 test wafers.

## 11.6 Pre-registration

- **Freeze:** after validation and before the test fleets are generated, tag a commit containing:
  - this document's thresholds and the G0 branch taken;
  - fleet seeds and configuration;
  - all tuners' hyperparameters, query-sizing parameters and the chosen primary comparator;
  - the reader choice (v1 or CNN) and the certificate constants;
  - the timing and fallback constants;
  - the analysis script.
- **After the freeze:** results are reported against the tag. Any later change is reported as a deviation.

---

← [10. Quantum layer (Qiskit)](10-quantum-layer-qiskit.md) · [Index](README.md) · [12. Compute plan](12-compute-plan.md) →
