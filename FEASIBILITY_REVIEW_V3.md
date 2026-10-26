**SpinTune v3 feasibility review — 25 October 2026**

**Verdict: proceed with a smaller simulation prototype, but revise the evidence and product claims before pitching them as established.** The most promising contribution is a reproducible benchmark of charge-count errors, abstention, and acquisition cost across simulated device families, with a test of whether chip history helps. The document does not yet establish a certified hardware tuner, a universal measurement-cost floor, or useful savings on Equal1 devices.

I read the complete design, inspected the evidence scripts, reran `anchor_check.py`, `headroom_v3.py`, and `cz_v3_check.py`, and checked the relevant dataset descriptions and primary literature. The design is unchanged. Public-data access was checked through repository records and documentation; the large datasets were not downloaded or evaluated. No sensor-only tuner, trained reader, or end-to-end benchmark currently exists in this workspace.

| Dimension | Assessment | Main dependency |
|---|---|---|
| Synthetic data acquisition | High feasibility | Implement a physically consistent sensor and stateful acquisition wrapper |
| Public experimental data | Available for partial validation | Different devices, observables, labels, and acquisition protocols |
| Equal1-specific fleet validation | Unproven | Grouped tuning logs with chip/wafer identities, failures, and independently verified outcomes |
| Success metrics | Strong foundation; several corrections needed | Operational time, rare-error uncertainty, and correct interpretation of conditional costs |
| Laptop computation | Feasible for the reduced study | Measure the complete query path and preserve history dependencies |
| Full scope in 180 person-hours | High delivery risk | Reader, certificate, stateful simulator, statistics, external data, and Qiskit all require integration |
| Innovation | Moderate methodological novelty; good potential engineering contribution | Demonstrate benefit beyond a conventional history baseline and qualify certification |

The wafer splits, histories containing each tuner's own mistakes, conventional history baseline, pre-registration, second simulator, and explicit separation of charge tuning from gate fidelity are substantive improvements. Keep them. The following issues remain consequential.

**1. High — the certificate claim is stronger than both the implementation and the available evidence.**

References: [pitch](SpinTune_Design_v3.md#0-pitch), [certificate](SpinTune_Design_v3.md#51-the-anchor-certificate-design-call-review-r1), and [anchor evidence script](checks/anchor_check.py).

I reproduced 24/300 and 45/300 wrong empty declarations for the old rule, and 0/300 in each starting-spread condition for the revised descent rule. That supports replacing the old stopping distance. However, `anchor_check.py` tests noiseless occupancy-guided descent. It does not implement the complete proposed certificate: visible crossings, a diagonal ray, calibrated signs, per-dot visibility in a confirmation window, domain refusal, and a final declaration are absent. The two conditions also reuse the same 300 devices; these are 600 trials, not 600 independent devices.

The proposed rule is conditional on a correct maximum projected charge period, bounded coupling, equilibration, a visible sensor response, and reliable transition detection. Two rays can miss the same transition because of persistent latching, sensor detuning, or a systematic reader error. Their redundancy is not an independence guarantee. An SNR threshold controls neither every missed-line mechanism nor an absolute charge-count error probability by itself. The separately reported OOD-spec scenario explicitly allows the assumed period bound to fail.

The physical sensing assumption deserves an early check. Equal1's paper describes a double-dot response overlaid with additional SEB transitions, and notes that detailed interpretation requires further analysis. This is more complicated than a universally signed step with only a 3:1 amplitude ratio. Compensation may make the proposed abstraction useful, but its feasibility and cost have not been demonstrated. [Equal1 SEB results, Fig. 4](https://arxiv.org/html/2412.08422v2).

**Required change:** describe this as an evidence-based declaration rule, or a certificate conditional on an explicit model and sensing assumptions. Replace “proves its answer,” “never lies,” and “holds across the whole range of devices a fab produces.” Implement the entire certificate through the metered interface before claiming its error rate. Exercise correlated missed transitions, persistent latching, sensor background transitions, and out-of-spec periods. Separately report incorrect anchors, incorrect final counts, and correct counts with inadequate margins. A formal noiseless statement would need its assumptions and argument written down independently of the Monte Carlo test.

**2. High — the cost estimates reproduce, but they are not a demonstrated floor or an implemented fleet learner.**

References: §1.4, §6.1–6.2, G0, and [headroom script](checks/headroom_v3.py).

| Scenario | Oracle start | History proxy | Fleet mean | Cold | History/cold |
|---|---:|---:|---:|---:|---:|
| In distribution, reproduced | 380 px | 442 px | 573 px | 563 px | 0.79 |
| Wide period, reproduced | 445 px | 492 px | 794 px | 765 px | 0.64 |

There are several limits beyond sensor noise:

- The history case is generated by drawing a start 26 mV from the true target and granting knowledge tied to the true period. It does not estimate that knowledge from prior cells or tuning logs, and it does not include the cold first cell and subsequent learning curve.
- Descent detects occupancy changes at 1 mV resolution, then divides the traversed distance by the selected billing pitch. It does not demonstrate that queries actually acquired at that pitch would yield the same decisions.
- Distances are converted into potentially fractional pixel counts; rays are not emitted as the interface's permitted 16/32/64-sample queries. Domain refusals and the actual query schedule are absent.
- The diagonal and confirmation are added analytically. The script always adds 256 confirmation pixels, whereas §5.2 specifies 1,024 when the estimated period exceeds 32 mV. With exact periods in the uniform 5–40 mV scenario, this omitted cost alone averages about 176 pixels per cell. The exact correction depends on the measured period and actual policy.
- Starting the shared descent policy at the true target does not prove that its evidence-acquisition path is optimal. A different policy could collect the same evidence more cheaply or reuse measurements differently.

**Required change:** call T★ an oracle-start reference for the specified policy. Replace “nothing can save more than about a third” with a conditional estimate of headroom within that policy. Compute G0 from real query traces, including integer query sizes, confirmation rules, retries, domain checks, and complete chip histories. Keep the current numbers as exploratory estimates with these qualifications.

**3. High — real data can validate components, but the proposed acquisitions cannot validate the central fleet claim.**

Reference: §7.6 and §14.

| Source | Acquisition feasibility | What it can support | What it cannot establish by itself |
|---|---|---|---|
| QArray training fleet | High; generated locally | Search development, controlled failure injection, supervised labels | Hardware realism or actual within-chip correlation |
| QDarts | Installed and independently documented | Sensitivity to equilibrium tunnel coupling and non-constant charging energies | Independent validation of the shared sensor/noise/latching wrapper |
| QDSD | Direct download; interpolated CSV archive about 127 MB plus labels | Single-dot line/count checks with an adapted observation model | The two-dot SEB certificate or Equal1 fleet learning |
| Delft D-CSD | Direct download; CSD archive about 1.8 GB | Experimental line-detection transfer and ambiguity analysis | Absolute (1,1) ground truth, sequential intervention results, or a fab-level hierarchy without suitable metadata |
| Equal1 logs/scans | Access unconfirmed | Potentially the actual fleet hypothesis and sensing assumptions | Nothing until the contents, labels, grouping, and permission to use them are established |

QDSD explicitly says only single-dot diagrams are labelled. Its README describes current measurements, and warns that interpolation/rounding loses information. A current peak and a charge-sensor step are different observations; the proposed signed-step certificate cannot simply be evaluated unchanged on these scans. Use QDSD for a separately labelled single-dot counting experiment. [QDSD record](https://zenodo.org/records/11402792), [data-format README](https://zenodo.org/records/11402792/files/README.md?download=1).

D-CSD's current record lists 9,850 diagrams, compared with 9,849 in the design. More materially, the collection was selected using a clean/noisy classifier. Its raw HDF5 data contain voltages and measurement values; default image loading resizes scans. Use the raw data and record the selection process. It does not supply the required absolute charge-count truth merely by containing recognizable lines. Hand-labelled line F1 is a useful transfer check, but is not a real-device certification result. [D-CSD record](https://zenodo.org/records/16363472), [loader README](https://zenodo.org/records/16363472/files/README.md?download=1).

Static replay also cannot reproduce what a device would have done under a different scan order, dwell time, averaging request, or history-dependent latch state. Treat it as offline observation/replay evidence. Likewise, QDarts is explicitly an equilibrium simulator; it expands the physics tested without validating the custom dynamics wrapper. [QDarts paper](https://arxiv.org/abs/2404.02064).

The core statistical gap is **joint distributions**. A 22 mV spread measured on one group's transistor dots and room-temperature threshold distributions across another group's wafer do not identify Equal1's cryogenic covariance between cells, chips, wafers, periods, and target locations. Those papers support plausible scenario ranges; the hierarchy that creates the history advantage remains an assumption. [First-electron variability study](https://arxiv.org/html/2310.20434), [22FDX transport study](https://arxiv.org/pdf/2501.10146).

**Required change:** prioritize a structured request over “50 scans.” Ask for raw signal and voltage axes; gate identities and fixed biases; sensor compensation; acquisition order, integration time, and timestamps; cell/chip/wafer/cooldown IDs; measured periods; verified target locations; and unsuccessful attempts. An initial sample spread over at least five chips with repeated same-design cells is useful for exploratory within-chip predictability. It will still not establish a rare-error ceiling or generalization across manufacturing wafers. Ask which independent downstream measurement supplies the verification flag assumed by §6.4.

Start by opening a handful of public raw files and mapping their labels into the reader contract. Time annotation on 5–10 scans before committing to 50 in four hours; include ambiguous labels and a second review on a subset. Keep test scans frozen if any public data are used to adjust preprocessing or thresholds.

**4. High for practical value — pixels saved need not mean tuning time saved.**

References: §4.2, §11.3–11.4.

The reproduced history proxy saves 121 pixels per cell. At the assumed 10 µs/pixel RF integration time, that is **1.21 ms**. One additional 20 ms query setup costs roughly 16.5 times that saving. Conversely, eliminating a query or a large voltage jump could make the benefit much larger than the pixel ratio suggests. Reader inference and orchestration also consume actual elapsed time, but are currently reported separately rather than clearly included in the operational-time gate.

This is a practical concern supported by experimental work: the cited RF/FPGA study reports a 9.8× measurement speedup translating into a 2.2× total initialization speedup, with Python execution limiting the result. [Published RF autotuning study](https://tqe.ieee.org/2026/03/04/rapid-autotuning-of-a-sige-quantum-dot-into-the-single-electron-regime-with-machine-learning-and-rf-reflectometry-fpga-based-measurements/).

**Required change:** retain pixels as the reproducible acquisition metric, and add an explicit wall-time result including query setup, settling, slew, reader/policy computation, and fallback. Let measured RF time influence the speed headline, not just pixel-based G0. Freeze the default timing assumptions and show sensitivity to query setup and slew. Obtain an actual charge-tuning time breakdown from Equal1 before claiming operational savings. The proposed DC calculation should remain labelled a re-costing; it is not a prediction of DC tuning reliability.

**5. High — the success gates do not yet support the advertised reliability statements.**

References: §11.2–11.5 and the pitch's trust claims.

The paired cost ratio over cells where both tuners succeed is useful, but conditional. Two tuners can each succeed on 90% of cells while failing on different 10% subsets. Their cost ratio then describes only the shared 80%; equal aggregate reliability does not remove that selection. The design recognizes this risk, but headline interpretation still needs to reflect it.

G3 permits an observed false-success fraction ≤1% with an upper confidence bound ≤2%. That does **not** establish a ≤1% population ceiling. Define the denominator as all declarations; “declared successes” can be confused with evaluator-confirmed successes. Also distinguish a wrong electron count from a margin failure, while retaining both in the overall unacceptable-declaration metric.

At a true 1% false-declaration probability, 29 independent declarations have approximately a **25.3%** probability of at least one error. Across 1,000, the expected number is ten. These are illustrative independence calculations, not estimates for a correlated fab, but they show why “no silent failures” is much stronger than the proposed target.

Zero observed errors also needs careful interpretation. Under an independent-binomial model, zero errors in 600 trials yields a one-sided 95% upper bound of about 0.50%; zero in 50 gives about 5.82%. Actual wafer clustering reduces the strength of such evidence. An ordinary nonparametric bootstrap of an all-zero error indicator will return zero in every replicate, so it cannot by itself provide a valid reassuring rare-event upper bound.

The “never worse” OOD gate actually allows up to 5% extra conditional cost and some loss of reliability, and covers only the sampled OOD scenarios. It should be called a pre-specified non-inferiority test. A failure to pass a confidence-bound gate may mean insufficient precision rather than demonstrated harm.

**Required changes to the scorecard:**

| Question | Metric and decision |
|---|---|
| Does the tuner work? | Success over every attempted cell; report all cells and reachable cells, confidence intervals, and failure causes |
| Can its declarations be trusted? | Wrong declarations / all declarations; report counts, coverage/abstention, and a rare-event interval method that remains meaningful with zero events |
| Is ≤1% established? | Require the chosen upper confidence bound ≤1%; otherwise say “observed ≤1%, upper bound X%” |
| Does it save acquisition? | Keep the paired pixel ratio; explicitly call it conditional on joint success and report the four joint success/failure counts |
| Does it reduce operational cost? | All-cell elapsed cost including a frozen fallback policy; retain failure-penalized cost and success-versus-budget curves |
| Is learning necessary? | T6 versus T3-H, with reliability and risk constraints; T6 versus T5 for history value |
| Does it tolerate shift? | Report the tested scenario and non-inferiority margins; include OOD-spec in trust reporting even if it is excluded from the speed gate |
| Does it scale safely? | Chip-level completion, number of bad declarations per chip, and all-cell cost including the first cell |

Keep the wafer bootstrap for cost and reliability comparisons. Size independent wafers for the intended claims, not only for the cost-ratio interval. Repeated tuner seeds do not create independent manufactured devices. If simultaneous robustness across multiple scenarios is advertised, specify the joint inference procedure before the freeze.

**6. Medium–high — stateful simulation and scoring still need a consistent physical contract.**

References: §4.3, §7.2, §11.2, §12.

The reference simulation shifts transition positions with persistent noise and carries latched occupancies between queries, while the QArray success rule reads noiseless T=0 occupancy. Specify whether this is the nominal device, the instantaneous noise-shifted equilibrium device, or the actual latched state at declaration. These can disagree: the telegraph shift reaches 0.2 periods, while the geometric margin threshold is 0.15 periods. Report nominal and realized success separately if both are useful.

A constant latching probability per pixel also changes effective relaxation when the tuner changes pitch or inserts repeated queries. A more physical model uses a transition probability derived from the elapsed time and applicable tunnel rate, for example `1 - exp(-Gamma * dt)`, with state and voltage dependence. At minimum, label the per-pixel rule as phenomenological and test sensitivity to query partitioning. Specify evolution during setup, jumps, and computation as well as during sampled pixels.

The shared-noise coupling must distinguish exogenous time-indexed noise from history-dependent latching: different policies drive different states, so only the random innovations can be shared, not a precomputed occupancy trajectory. Finally, §12's instruction to parallelize across cells conflicts with §6.4's sequential chip and wafer histories. Parallelize independent wafer/tuner/seed sessions; process history-dependent chips and cells in order.

**7. Medium–high — 180 hours is plausible only with a tighter protected deliverable.**

The primary risk is engineering and validation, not raw simulator throughput. Package installation and fast windows do not measure the cost of building a reader, geometrically valid confirmation placement, persistent state, logs, metrics, and external-data adapters. Track F and the external tests may be off the tuning dependency chain, but they still consume the same two people's time. QDarts, comparator selection, and the scoring harness also join the dependencies of the final frozen evaluation.

My planning judgment is that a reduced demo is feasible; delivery of every non-cuttable item at the promised standard has high overrun risk. Protect one working sensor-only end-to-end comparison first. Use a simple signal-processing reader as an initial baseline, adding the CNN when it demonstrates a useful improvement. Preserve T3, T3-H, T5, and T6 as configurations of the shared policy; treat T★ as a reference. Keep T2 as a validation comparator without making a sophisticated fitter a separate research project.

A possible 180-hour allocation is 30 h for simulator/interface/evaluator, 30 h for reader and evidence rule, 25 h for baselines and prior, 25 h for evaluation/statistics, 15 h for a small QDarts and external-data study, 20 h for Qiskit, 15 h for presentation/reproduction, and 20 h contingency. These are proposed planning caps, not measured estimates. If they do not fit, reduce the promise before using the contingency.

Make the first acquisition-accurate sensor-only comparison a week-one objective. In week two, decide whether history adds measurable value in pixels **and** time and whether errors can be controlled. Then freeze, run the held-out study, and finish the external checks. IBM hardware, a dashboard, drift, six-dot tuning, a neural set encoder, and a large multidimensional map should not displace this work.

**8. Innovation — position the contribution against current work, not generic “AI for tuning.”**

| Proposed element | Existing evidence | SpinTune's defensible opportunity |
|---|---|---|
| Ray measurements | Experimental ray-based identification and tuning were published in 2021 | A particular evidence protocol and fair accounting of its cost |
| Uncertainty-aware charge tuning | Online single-dot tuning with neural-network uncertainty was demonstrated in 2025 | Calibrated declaration risk across explicit device shifts |
| FDSOI line segmentation and target selection | An April 2026 study uses 1,015 experimental diagrams spanning nine geometries and multiple wafers | Sequential acquisition, history reuse, and a reproducible comparison |
| Autonomous spin-qubit tuning | A 2026 study demonstrates a complete sequence from a grounded device to Rabi oscillations | A narrow, well-measured charge-tuning component that can fit into such a workflow |
| Hierarchical fleet prior | Empirical Bayes and shrinkage are established methods | Evidence about when chip/wafer history helps, hurts, or adds nothing |
| Open benchmark | The community has explicitly identified benchmarking and standardization needs | A useful executable protocol with independent tuners and realistic failure reporting |

Sources: [ray-based framework](https://arxiv.org/abs/2102.11784), [online uncertainty-aware tuning](https://pubs.acs.org/doi/10.1021/acs.nanolett.4c04889), [2026 FDSOI segmentation study](https://arxiv.org/abs/2604.13662), [fully autonomous tuning](https://www.nature.com/articles/s41928-025-01562-4), [community data and benchmarking report](https://arxiv.org/abs/2312.14322).

The 2026 FDSOI paper is already mentioned as a possible data contact in §13, but should be a central related-work comparison. Its reported 80% offline success is not directly comparable with a 90% synthetic target: device, task, sensing mode, and protocol differ.

The strongest research question is: **When does information from previously tuned cells reduce acquisition cost without increasing incorrect charge declarations?** A useful result could be a break-even map versus shared variation and period predictability, including a no-gain result against a running mean. Add an ablation separating knowledge of target voltage from knowledge of period; the current estimate suggests the latter drives much of the gain.

For the open-benchmark claim, separate outcome scoring from the shared-policy experiment. An external tuner may provide valid evidence in a different form. Define an adapter and score its declared state, margins, cost, and risk; label comparisons that require SpinTune's particular certificate as a constrained protocol. Include a credible existing heuristic with and without extra verification at comparable risk, so the certificate's value is measured beyond beating v2's known-broken shortcut.

**9. Qiskit is feasible and technically better grounded, but it is a separate modelling result.**

I reran `cz_v3_check.py`. The 2×2 reduction agreed with the 4×4 propagator to approximately 7.2×10^-15; the vectorized benchmark took about 0.13 s per 1,000-draw map point on this run, consistent with a manageable map. The fixed-correction calculations reproduce the stated limited validity of the pure-ZZ approximation. These are numerical checks, not full noise-model or RB validation.

The separation between Si/SiGe calibration and an explicitly labelled 22FDX projection is appropriate. Keep Markovian RB validation and descriptive treatment of quasi-static RB. To keep the study interpretable, compose physical channels rather than simply adding component infidelities; derive any residual depolarizing strength from the composed nominal channel and reject parameter sets that would require negative residual noise. Treat charge-induced dephasing and T2* calibration consistently to avoid counting the same mechanism twice.

Matching a residual floor to one reported fidelity does not independently identify its physical cause. An optimum at zero detuning and the imposed pulse limit may mostly express the model assumptions. Present it as a sensitivity study conditional on those assumptions. It does not validate the tuner's electron count or show improved physical gate fidelity. A compact map and verified Aer pipeline are sufficient to demonstrate relevant Qiskit use; the actual acceptance of that scope remains a judging matter.

**What I would change before the pitch:** replace proof and universal-floor language; identify the benchmark and measured error/cost trade-off as the protected outcome; show the reproduced numbers as idealized policy estimates; request grouped logs and an RF timing breakdown; and add the 2026 FDSOI paper to the comparison slide. A defensible pitch is:

> SpinTune tests whether chip history can make charge tuning cheaper without increasing wrong charge declarations. We are building a reproducible benchmark with explicit evidence, abstention, and measurement accounting on literature-informed simulated fleets, with separate tests on experimental scans. Hardware validation depends on access to suitable device data.

The project is worth pursuing on that basis. The first decisive result is a correctly metered sensor-only run that reaches and verifies (1,1), followed by an honest comparison against conventional history reuse.
