[SpinTune v5 design](README.md) › 15. Plan

# 15. Plan

## 15.1 Before the pitch (Tue 27 Oct, idea-only)

- [ ] **Repo:** `git init`; lockfiles for both environments; commit `checks/`.
- [ ] **Update `SPINTUNE-2.md` to match this document:**
  - the [§0](00-pitch.md) pitch: "SpinTune tests whether chip history can make charge tuning cheaper without increasing wrong charge declarations";
  - none of "proves its answer", "never lies", "holds across all devices", "floor" or "nothing can save more";
  - the (1,1) target, with the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence rule and its assumptions;
  - "fleet modelled on published 22FDX statistics; the within-chip structure is an assumption";
  - electrons and the SEB + double-dot layout;
  - the CZ numbers from arXiv 2412.01920v3 (200 ns; 99.30% / 98.41%), with the trade-press numbers labelled "vendor-reported";
  - the FD-SOI noise range;
  - "pre-registered target", not "≥ 2×";
  - "non-inferiority on the tested shifts", not "never worse";
  - "learned from bring-up logs";
  - Qiskit protected;
  - the 6-dot run as a question for Equal1;
  - the report-straight sentence;
  - drop "every tuner step is a fresh simulation" as the HPC argument.
- [ ] **Comparison slide:** the [§2.1](02-goals-non-goals-anti-goals.md#21-related-work-and-what-is-new-here) table, including the CEA-Leti 2026 FD-SOI paper.
- [ ] **Q&A additions:**
  - *"Isn't charge tuning cheap already?"* — "Yes, and we measured how cheap, for one policy on ideal cells: about half a second per cell at RF rates, and pixels are about 1% of that. Chip history cut pixels by about 14% and time by about 27%, mostly by needing fewer queries. The value is a measured wrong-declaration rate and a benchmark that reports it for every tuner."
  - *"Is the certificate a proof?"* — "Only under stated assumptions: a bounded charge period, equilibrium occupancy, and a sensor that shows every line. Real devices can break each one, so we measure its error rate under noise, latching and sensor artefacts, and report the upper bound."
  - *"How is this different from the CEA-Leti FD-SOI work?"* — "They segment single diagrams offline, with 80% success on their own process. We test sequential acquisition with metered cost and history reuse. The numbers aren't comparable."
  - *"Why not BO?"* — "A scalar score can't count electrons, and its per-step overhead is larger than the simulation."
- [ ] **Backup slides only:**
  1. the stopping-rule miscount (8–15% in a one-axis descent, vs 0/300 per start spread with the period-bounded length; 4/300 for the shortcut under the shared policy, wide fleet; all noiseless);
  2. the idealized cost table (pixels, queries and time; [§0](00-pitch.md));
  3. the CZ gate from the Hamiltonian.
- [ ] **Hand Equal1 the structured data request** ([§14](14-questions-for-equal1.md) Q3–Q5) at the pitch.
- [ ] **Rehearse** the [§14](14-questions-for-equal1.md) questions.

## 15.2 Tracks and hour caps [design call]

| Track | Content | Cap |
|---|---|---:|
| A | Simulation, interface, evaluator (A4, the QDarts worker, counts against Track R's external cap) | 30 h |
| B | Evidence rule and baselines (B1 ≈ 12 h, B2–B4 ≈ 13 h) | 25 h |
| R | Reader v1 (15 h); QDarts and external data, a small study (15 h) | 30 h |
| D | Fleet learning | 15 h |
| E | Scoring and statistics | 25 h |
| F | Qiskit (protected, off the critical path) | 20 h |
| — | Presentation and reproduction | 15 h |
| — | Contingency | 20 h |
| | **Total** | **180 h** |

These are planning caps, not measured estimates. If a track won't fit its cap, shrink what it promises before spending the contingency.

## 15.3 Tasks ("Needs" = hard dependencies; "Done" = the check that must pass)

**Track A: simulation, interface, evaluator**
- **A0. Setup.** `git init`, two environments with lockfiles, `checks/` committed, both laptops working.
  - **Done:** every `checks/` script reruns from the repo on both machines, with outputs saved.
- **A1. Fleet generator.** Hierarchical sampler ([§7](07-fleet.md)) for both templates; whole-wafer splits; matched OOD variants.
  - **Needs:** A0.
  - **Done:** the same seed gives the same fleet; a 16-cell scan grid per fleet looks visibly different; the lattice matches `optimal_Vg` within 1 px.
- **A2. Session interface.** Windows and rays, ledger, cost model, caps, domain refusal, tile cache, persistent state, latching as relaxation, common random numbers.
  - **Needs:** A1.
  - **Done:**
    - the ledger equals the sum of billed pixels, and the time model passes unit tests;
    - at a stress rate (Γ_B ≤ 10² s⁻¹) a latched state survives a query boundary, and the reset ablation differs; at the default rates it never does;
    - the latching partition test passes ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call));
    - only exogenous noise is shared between tuners.
- **A3. Evaluator.** `judge()`: nominal success, hold success, wrong count vs inadequate margin, wrong anchor; the (1,1) polygon, masks, the QDarts dominant-state rule.
  - **Needs:** A1.
  - **Done:** 5 hand-checked cells; masks agree with occupancy changes.
- **A4. QDarts worker.**
  - **Needs:** A2.
  - **Done:** same interface; speed test on 20 cells; OOD-simulator fleet size fixed.

**Track B: evidence rule and baselines**
- **B1. The whole evidence rule through the metered session** ([§5.1–5.2](05-reading-the-device.md#51-the-anchor-certificate-design-call)): diagonal descent, axis rays, sign calibration, 2D visibility, domain refusal, count and declaration. First with the oracle reader, then with reader v1. Write up the noiseless argument as a one-page note with its assumptions.
  - **Needs:** A2, A3.
  - **Done:** G1 certificate tests (a) and (c). Until B1 is done, slides quote only the noiseless descent result.
- **B2. T★ and T3, then T3-M and T3-H, with reader v1.**
  - **Needs:** B1, R1.
  - **Done:** **the first sensor-only end-to-end comparison**: T★, T3 and T3-H on the pilot, reaching and verifying (1,1), with pixels, queries and RF time. This is the week-1 objective.
  - **Week-1 fallback, decided now:** if A2 or R1 slips, W1 ends with the same comparison using the oracle reader (B1's first stage), labelled oracle-assisted. The sensor-only version moves to the start of W2 and must land before G0.
- **B3. T0, T2 (simple mosaic fit), T2-N, and the T3-L(ℓ) sweep.**
  - **Needs:** B1.
  - **Done:** all run end to end on the pilot; a first cost–risk curve on validation (the curve that is quoted comes from the stress set, B4).
- **B4. Certificate stress set** ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b, [§7.4](07-fleet.md#74-fleets)) with reader v1: the nominal-noise set and the stress scenarios.
  - **Needs:** B1, R1, and A2 complete (persistent noise and latching).
  - **Done:** the wrong-anchor rate on the nominal-noise set with its upper bound (feeds G2 and the reader choice); the stress-scenario table in three error categories.
  - **Then, off the critical path (after the reader freeze, before E2):** T3-L(ℓ) and T2-N on the same stress set, with the same noise. This is where the cost–risk curve ([§6.3](06-tuners-and-baselines.md#63-comparisons-each-one-answers-a-different-question) f) can separate: on validation alone, 0 errors gives a bound of only ~0.7%, and the idealized shortcut already makes 0/300 in-distribution. If a cheaper ℓ still shows no extra errors under stress, that is reported as the result.

**Track R: reader and external data**
- **R1. Reader v1** (signal processing: ray step detector, window orientation + Hough, abstention; [§5.3](05-reading-the-device.md#53-reader-contract-design-call)).
  - **Needs:** A3.
  - **Done:** F1 on validation windows and rays; wrong-anchor rate with v1 on noisy validation cells.
- **R2. CNN reader (optional).** Training samples from the training fleet; U-Net-lite + ray head.
  - **Needs:** R1.
  - **Done:** kept only if it beats v1 by the [§5.3](05-reading-the-device.md#53-reader-contract-design-call) margin on validation; otherwise dropped, and the reason recorded.
- **R3. External data.** Open a few raw QDSD and D-CSD files and map their labels into the reader contract. Run the QDSD single-dot counting experiment. Time 5–10 D-CSD labels (with a second review on a subset), then decide whether to label 50.
  - **Needs:** R1.
  - **Done:** numbers in the results table, labelling rate recorded, within the 15 h cap (shared with A4).

**Track D: fleet learning**
- **D1. Training-fleet tuning logs.** T3 with the frozen reader over the training fleet.
  - **Needs:** B2, and the reader choice frozen at the end of week 2 (R1, or R2 if kept).
  - **Done:** one trace per cell; success and wrong-declaration rates reported.
- **D2. Fit the hierarchical prior from verified logs**, plus the unfiltered-log ablation.
  - **Needs:** D1.
  - **Done:** prior file written; 50% and 90% ellipse coverage on validation within ±5 points.
- **D3. T5 and T6**, plus the start-only and period-only ablations.
  - **Needs:** D2.
  - **Done:** both beat T3 on 50 validation cells, or the reason is understood.

**Track E: scoring and statistics**
- **E1. Harness:** tuners × fleets × seeds; wafer bootstrap; Clopper–Pearson bounds over declarations and over chips; joint 2×2 counts; all-cell cost with the fallback; success-vs-budget plots; automatic PASS/FAIL per gate.
  - **Needs:** B2.
  - **Done:** one command regenerates every figure and verdict from saved traces.
- **E2. Validation runs**, the certificate stress set, comparator selection, thresholds, **freeze tag**.
  - **Needs:** E1, D3, B3, B4.
  - **Done:** tag pushed with the [§11.6](11-success-measurement.md#116-pre-registration) contents.
- **E3. Test and OOD runs**: G3, G3h, external tests, oracle-assisted ablation.
  - **Needs:** E2, A4, R3.
  - **Done:** results table and the gate slide.
- **E4. Coarse spread map**, i.e. the break-even map (the full map only with cluster hours).
  - **Needs:** E2.

**Track F: Qiskit (protected, off the critical path)**
- **F1. CZ Hamiltonian module**: standard convention, Hann pulse, 2×2 block propagator, ZZ cross-check.
  - **Needs:** A0.
  - **Done:** G4(a).
- **F2. Error-budget map** with composed channels, rejection counts, O0 and O1.
  - **Needs:** F1.
  - **Done:** the map figure and the conditional O1 statement.
- **F3. Aer RB/IRB**: Markovian validation, then the quasi-static scenarios.
  - **Needs:** F1.
  - **Done:** G4(b) and the descriptive quasi-static report.
- **F4. IBM Open Plan run.**
  - **Needs:** F3 working on `FakeTorino`.
  - **Done:** job IDs, pair, timestamps, analysed data and the descriptive comparison, or the documented fallback.

**Stretch (only after E2):**
- drift (C3, G5);
- T6-NN and T-BO;
- the 6-dot / multi-cell run, if Equal1 confirms the layout;
- QFlow 2.0;
- Samplomatic twirling;
- a dashboard.

## 15.4 Schedule

| Week | Tasks | Gate at the end of the week |
|---|---|---|
| W1 (28 Oct – 3 Nov) | A0, A1, A2 core (ledger, cost model, domain, tile cache, white noise), A3, B1, R1 minimal (ray step detector, window line fit), B2 | G1 except the persistent-state tests; **the first sensor-only, metered end-to-end comparison (T★, T3, T3-H) with reader v1** |
| W2 (4 – 10 Nov) | A2 rest (telegraph, 1/f, latching, common random numbers, partition test), A4, B3, B4, R1 complete (abstention, "bad" class), R2 (optional), start R3, F1, F2 | Rest of G1; G2; **sensor-only G0: does history add value in pixels and in time, and are wrong declarations controlled?** The branch is chosen and **the reader is frozen** |
| W3 (11 – 17 Nov) | D1, D2, D3, E1, E2; F3; **submit F4 by 13 Nov** | **Freeze tag by 17 Nov** |
| W4 (18 – 24 Nov) | E3, E4, R3; presentation; stretch if time | G3, G3h, G4 |
| 25 – 26 Nov | Demo and dry run | — |
| 27 Nov | Final | — |

Planned load is about 40 h a week (two people × 20 h) in W1–W3, with W4 lighter to leave room for the presentation. The 20 h contingency covers overruns; if it runs out, cut in the [§15.6](#156-cut-order-and-what-is-never-cut) order.

## 15.5 Critical path

**A1 → A2 → B1 → B2 → B4 → reader freeze → D1 → D2 → D3 → E2 → E3.**
- Reader v1 (R1) joins the path at B2, because the week-1 comparison is sensor-only.
- The harness (E1) must be finished before E2: comparator selection and the frozen analysis script use it.
- The CNN (R2) is off the path. Track F, B3, A4 and R3 sit off the path too. Give them to whoever is blocked.

## 15.6 Cut order, and what is never cut

**Cut in this order:**
1. Drift (C3).
2. The full spread map (keep the coarse one).
3. T6-NN and T-BO.
4. The CNN reader (keep v1).
5. QFlow 2.0.
6. Samplomatic twirling.
7. The IBM hardware run (keep the Aer and `FakeTorino` pipeline).
8. D-CSD labels beyond the timed first batch.
9. The coarse map, down to one axis.
10. Reduce the OOD-simulator fleet (never remove it).

**Never cut:**
- the interface and evaluator;
- the evidence rule and reader v1;
- T★, T2 (simple fitter), T3, T3-H, T5, T6;
- G0–G3h, the wafer bootstrap, the rare-event bounds and the freeze;
- the C2 Hamiltonian map with Aer RB validation (the Qiskit requirement).

**Must not displace the protected outcome** ([§2](02-goals-non-goals-anti-goals.md)): the IBM hardware run, a dashboard, drift, the 6-dot run, a neural set encoder, the large map.

## 15.7 Demo (27 Nov)

1. A new virtual chip.
2. **The evidence rule in action:** rays light up. On a wide-period cell where it happens (4/300 for T3 in the idealized wide fleet), the 1.5-period shortcut miscounts while the full rule certifies or abstains.
3. Cells 1–10 tuned in sequence, with pixel and time counters against the T★ reference, showing whatever was measured.
4. The wrong-declaration counter for every tuner, with upper bounds.
5. The headroom result with its confidence interval, and the G0 branch taken.
6. The CZ error budget from the Hamiltonian in Qiskit, with Aer RB, plus the IBM run if it happened.
7. The gates slide: pass or fail, including any failures.

## 15.8 Left to the builder

These are free choices, within the rules above:
- query sizing and ordering within [§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call), and retry logic;
- reader v1's filter details, and the CNN's architecture;
- how the hierarchical model is parameterised;
- T2's line-fitting algorithm, kept simple;
- plotting;
- file formats beyond [Appendix A](appendix-a-interfaces-and-code-layout.md);
- details of mapping parameters into QDarts.

---

← [14. Questions for Equal1](14-questions-for-equal1.md) · [Index](README.md) · [16. Risks](16-risks.md) →
