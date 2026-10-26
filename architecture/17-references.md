[SpinTune v5 design](README.md) › 17. References

# 17. References

**Equal1 and 22FDX**
- Equal1 Si/SiGe two-qubit processor: [arXiv 2412.01920v3](https://arxiv.org/html/2412.01920v3)
- Equal1 22FDX quantum-dot cells: Amitonov et al., [arXiv 2412.08422v2](https://arxiv.org/html/2412.08422v2) (Figs. 1, 2, 4); [arXiv 2412.08302v1](https://arxiv.org/html/2412.08302v1)
- 22FDX transistor dots, first-electron spread (different group): Thomas et al., Nature Electronics 8, 75 (2025), [doi:10.1038/s41928-024-01304-y](https://doi.org/10.1038/s41928-024-01304-y), [arXiv 2310.20434](https://arxiv.org/html/2310.20434)
- 22FDX multi-gate dots (Quobly / CEA-Leti): Elbaz et al., [arXiv 2501.10146](https://arxiv.org/abs/2501.10146)
- Equal1 technology page: [equal1.com/technology](https://www.equal1.com/technology)

**Noise, tunnel coupling, exchange**
- SOI charge noise: [arXiv 2209.01853](https://arxiv.org/abs/2209.01853)
- 22FDX p-type charge noise: [arXiv 2507.21306v1](https://arxiv.org/html/2507.21306v1)
- Si/SiGe charge noise: [arXiv 2209.07242](https://arxiv.org/abs/2209.07242)
- Correlated noise in a Si/SiGe array: [arXiv 2603.03051](https://arxiv.org/html/2603.03051)
- Intel first-electron variability: [arXiv 2307.04812v2](https://arxiv.org/html/2307.04812v2)
- MOS tunnel-coupling slope: [arXiv 2411.13882](https://arxiv.org/abs/2411.13882)
- Exchange slope and CZ: [arXiv 2410.15590v2](https://arxiv.org/html/2410.15590v2)
- Exchange theory: [QTCAD](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)
- Polarisation-line t_c: DiCarlo et al., [PRL 92, 226801](https://arxiv.org/abs/cond-mat/0311308)

**Autotuning and related work**
- Ray-based state identification: Zwolak et al., PRX Quantum 2, 020335 (2021), [doi:10.1103/PRXQuantum.2.020335](https://doi.org/10.1103/PRXQuantum.2.020335), [arXiv 2102.11784](https://arxiv.org/abs/2102.11784)
- Online neural-network charge autotuning: Yon et al., Nano Lett. 25, 3717 (2025), [doi:10.1021/acs.nanolett.4c04889](https://doi.org/10.1021/acs.nanolett.4c04889), [arXiv 2409.20320](https://arxiv.org/abs/2409.20320)
- CEA-Leti 300 mm FD-SOI charge-state tuning by segmentation: Samaha et al., [arXiv 2604.13662](https://arxiv.org/abs/2604.13662) (2026)
- Fully autonomous spin-qubit tuning: Schuff et al., Nature Electronics (2026), [doi:10.1038/s41928-025-01562-4](https://doi.org/10.1038/s41928-025-01562-4), [arXiv 2402.03931](https://arxiv.org/abs/2402.03931)
- RF/FPGA autotuning and its time breakdown: Roux et al., IEEE Trans. Quantum Eng. (2026), [doi:10.1109/TQE.2026.3670353](https://doi.org/10.1109/TQE.2026.3670353), [arXiv 2509.19537](https://arxiv.org/abs/2509.19537)
- BO tuning: Moon et al. 2020, [PMC7438325](https://pmc.ncbi.nlm.nih.gov/articles/PMC7438325/)
- Data needs and benchmarking: Zwolak et al., npj Quantum Inf. 10, 105 (2024), [doi:10.1038/s41534-024-00878-x](https://doi.org/10.1038/s41534-024-00878-x), [arXiv 2312.14322](https://arxiv.org/abs/2312.14322)

**Simulators and data**
- QArray: [arXiv 2404.04994](https://arxiv.org/abs/2404.04994)
- QDarts: Krzywda et al., SciPost Phys. Codebases 43 (2025), [doi:10.21468/SciPostPhysCodeb.43](https://doi.org/10.21468/SciPostPhysCodeb.43), [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), [repo](https://github.com/qplai/QDarts)
- QDSD: Yon et al., [Zenodo 11402792](https://doi.org/10.5281/zenodo.11402792); Delft D-CSD: de Snoo et al., [Zenodo 16363472](https://doi.org/10.5281/zenodo.16363472); [QFlow 2.0](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)

**Qiskit, RB, IBM**
- Aer depolarising channel: [docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)
- qiskit-experiments RB and IRB systematic bounds: [manual](https://qiskit-community.github.io/qiskit-experiments/manuals/verification/randomized_benchmarking.html)
- RB under correlated (non-Markovian) noise: [arXiv 1504.05307](https://arxiv.org/abs/1504.05307)
- IBM plans (Open Plan, 28-day window): [docs](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview); QPU metric definitions: [docs](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information)
- IBM R2P course, Units 0–4: the `Unit_*` folders at the repository root

**Project documents**
- `bobi_resources/SPINTUNE-2.md`, `bobi_resources/PLAN.md`, `checks/README.md`

---

← [16. Risks](16-risks.md) · [Index](README.md) · [18. Scaling](18-scaling.md) →
