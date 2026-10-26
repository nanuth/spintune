[SpinTune v5 design](README.md) › 14. Questions for Equal1

# 14. Questions for Equal1 (most important first)

1. **Layout and axes:**
   - Is our reading of the SEB + double-dot configuration right: SEB between QT0 and QT1, dots between QT1/QT2 and QT2/QA1, with QT2 as the inter-dot barrier?
   - Which gates do you sweep for charge tuning, and how do you compensate the SEB?
2. **Reservoir of the far dot:** does the QT2/QA1 dot load from the drain through QA1, or only via the near dot?
3. **Data, as a structured request.** For an initial sample spread over **at least 5 chips, with repeated same-design cells**, could you share:
   - the raw sensor signal with its voltage axes, gate identities and fixed biases;
   - sensor compensation settings;
   - acquisition order, integration time and timestamps;
   - cell, chip, wafer and cooldown IDs;
   - measured charge periods and verified target locations;
   - unsuccessful attempts, not only successes?

   That would allow an exploratory look at within-chip predictability. It would not establish a rare-error ceiling or generalisation across wafers.
4. **Verification:** which independent downstream measurement tells you that a charge-tuned cell was right? Our tuning logs assume such a flag ([§6.4](06-tuners-and-baselines.md#64-histories-and-tuning-logs)).
5. **Cost today, broken down:** per cell, how much time goes to setup, settling, slewing, integration and analysis? That decides whether fewer pixels or fewer queries matter.
6. **Distributions:**
   - What are the cryogenic distributions across cells, chips and wafers of first-electron voltage, lever arms, E_c and cross-capacitance?
   - How much of that is shared within a chip?
   - Is a chip 29 cells or 35?
7. **Platform:** do Bell-1 qubits run on the 22FDX cells or on the Si/SiGe devices? NMOS or PMOS?
8. **Spins:** how are spins driven in 22FDX, and what is ΔE_z?
9. **Noise:** what are measured √S_E and its exponent in 22FDX?
10. **Exchange:** the t_c(V) and J(V) slopes; residual J; the CZ pulse shape.
11. **Multi-dot:** is there a linear multi-dot array you'd want tuned pair by pair?
12. **Cooldowns:** how much do the electrostatics shift between cooldowns?

---

← [13. Prerequisites](13-prerequisites.md) · [Index](README.md) · [15. Plan](15-plan.md) →
