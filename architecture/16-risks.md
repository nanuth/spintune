[SpinTune v5 design](README.md) › 16. Risks

# 16. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Headroom is marginal.** The idealized estimate (h ≈ 32% in pixels) sits near the 30% line, and the idealized history ratio (0.86) only narrowly meets its relative target (≈ 0.89); noise, reader v1 and simulated training-fleet logs may move both | **High: it decides the headline** | Pre-registered G0 branches on sensor-only traces. The benchmark and the error/cost trade-off carry the headline in the lower branches. Costlier tuning stages are listed for follow-up ([§3.4](03-scope-and-device-template.md#34-deferred-and-stretch)) |
| **Pixel savings don't become time savings.** Pixels are ~1% of RF time | **High for practical value** | Time metered per query; "faster" needs h_t and G3(c′); sensitivity to setup and slew; Equal1's own time breakdown ([§14](14-questions-for-equal1.md) Q5) |
| **The history advantage is an artefact of the assumed joint distributions** | **High** | The break-even map over shared variation and period predictability; T3-H as the no-learning baseline; the structured data request ([§14](14-questions-for-equal1.md) Q3) |
| **The evidence rule fails under real sensing** (SEB background transitions, detuning, latching) | **High** | The [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b stress tests; three error categories; the depletion-window contingency; abstention |
| The paired cost ratio hides tuners that fail on different cells | Medium | The 2×2 joint counts; all-cell cost with the fallback; reliability non-inferiority in every cost claim |
| Too few declarations to bound a rare error rate | Medium | Clopper–Pearson bounds; a certificate stress set of ≥ 3,000 cells; "observed X%, upper bound Y%" wording |
| The evidence rule abstains too often under noise, so reliability < 90% | Medium | Validation-tuned SNR threshold and pitch; the pre-registered depletion-window contingency ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call)); abstentions reported |
| Our device mapping (SEB + double dot, plane (QT1, QA1)) is wrong | Medium | "Modelled on" wording; question 1 for Equal1; the generic template as a fallback |
| The compensated-sensor assumption hides real costs | Medium | Uncompensated and SEB-background stress scenarios, reported |
| Persistent-state simulation is harder or slower than planned | Medium | Fall back to per-query reset, clearly labelled as simplified |
| Sim-to-real gap | High | QDarts fleet, external data, sourced spreads; the honesty slide |
| σ_die is low-confidence | Medium | Swept 0–150 mV |
| T2 wins on reliability | Low–Medium | Reported. It's expensive in pixels by construction |
| **Scope vs 180 h** | **High** | Hour caps ([§15.2](15-plan.md#152-tracks-and-hour-caps-design-call)); the protected outcome first; reader v1 before any CNN; cut order |
| QDarts install or speed problems | Low–Medium | Verified install; lineshape fallback |
| IBM queue or access problems | Low | Submit by 13 Nov; `FakeTorino` fallback |

---

← [15. Plan](15-plan.md) · [Index](README.md) · [17. References](17-references.md) →
