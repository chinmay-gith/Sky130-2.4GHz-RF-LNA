# SKY130 2.4 GHz RF Low-Noise Amplifier

A transistor-level RFIC design and simulation project implementing a 2.4 GHz CMOS Low-Noise Amplifier (LNA) in the open-source SkyWater SKY130 process — targeting the ISM band used by WiFi and Bluetooth Low Energy.

This project was built as a self-directed exploration of the RFIC design workflow: from schematic-level amplifier design through frequency-response simulation, impedance extraction, and iterative matching-network tuning, using fully open-source tools.

---

## Overview

The amplifier is a common-source CMOS RF LNA built around the SKY130 `sky130_fd_pr__nfet_01v8` device model, simulated in `ngspice`. The goal was to design and characterize a single-stage LNA at 2.4 GHz and understand, hands-on, the trade-offs between gain, input matching, and component selection in a real (if unoptimized) RF front end.

**Design workflow covered:**
- CMOS transistor-level RF amplifier design
- Input matching network design (Lg, Ls, C1)
- AC frequency-response analysis (100 MHz – 10 GHz sweep)
- Input impedance extraction
- S11 / input-return-loss evaluation
- Component parameter sweeps
- Simulation data extraction and result visualization

---

## LNA Architecture

Common-source CMOS RF amplifier topology with:
- NMOS gain transistor (`sky130_fd_pr__nfet_01v8`)
- Inductive source degeneration (Ls)
- Inductive gate matching network (Lg)
- Input coupling capacitor (C1)
- RF output load network
- Resistive gate bias
- 1.8 V supply

![SKY130 LNA Schematic](results/lna_schematic.png)

### Final Input Network

| Component                | Value  |
| ------------------------ | ------ |
| Gate inductance (Lg)     | 35 nH  |
| Source degeneration (Ls) | 0.5 nH |
| Input capacitor (C1)     | 1 pF   |
| Source resistance        | 50 Ω   |
| Supply voltage           | 1.8 V  |
| Gate bias                | 0.9 V  |

---

## Technology and Simulation

| Parameter        | Value                     |
| ----------------- | ------------------------- |
| Process           | SkyWater SKY130           |
| Transistor         | `sky130_fd_pr__nfet_01v8` |
| Supply             | 1.8 V                     |
| Target frequency   | 2.4 GHz                   |
| Simulator          | ngspice-42                |
| AC sweep           | 100 MHz – 10 GHz          |

---

## Simulation Results

| Metric                  | Result             |
| ------------------------ | ------------------- |
| Maximum voltage gain     | 26.90 dB            |
| Peak gain frequency      | 2.291 GHz           |
| Voltage gain @ 2.4 GHz   | 24.61 dB            |
| S11 @ 2.4 GHz            | -4.59 dB            |
| Zin @ ~2.4 GHz           | 197.24 − j5.05 Ω    |

The amplifier shows strong, frequency-selective gain centered close to the intended 2.4 GHz band, confirming the core amplifying stage is functioning as designed.

### Gain Response

![LNA Gain Response](results/lna_gain_response.png)

Peak voltage gain of ~26.9 dB occurs at 2.291 GHz, with ~24.6 dB retained at the 2.4 GHz target — a reasonably tight, well-behaved resonant response for a single-stage design.

### Input Return Loss

![LNA S11 Response](results/lna_s11_response.png)

Simulated S11 at 2.4 GHz is **-4.59 dB**.

### Input Impedance

At ~2.4 GHz, the simulated input impedance is:

```
Zin ≈ 197.24 - j5.05 Ω
```

---

## Known Limitations

This is an intentionally transparent section — these are the gaps that separate this from a production-ready design:

- **Input match is not production-quality.** S11 of -4.59 dB corresponds to a real, non-trivial mismatch (a well-matched 50 Ω RF front end typically targets S11 below -10 dB, ideally -15 dB or better). The real part of Zin (~197 Ω) is far from the 50 Ω target, indicating the input network needs further retuning of Lg/Ls/C1 — likely requiring a proper Smith-chart-based match rather than manual sweeps.
- **No noise figure (NF) analysis.** For an LNA, noise figure is arguably the headline spec — the "low noise" the design is named for — and it hasn't been characterized here yet. This is the single most important next step.
- **No output match (S22) or linearity characterization.** P1dB and IIP3 (compression and intermodulation behavior) haven't been evaluated, so the amplifier's real-world usable input power range is unknown.
- **Simulation-only, schematic-level.** No layout, parasitic extraction, or post-layout (PEX) simulation has been done — results reflect ideal component values without interconnect or substrate parasitics, which will shift performance at 2.4 GHz.
- **Single PVT corner.** Simulations were run at nominal process/voltage/temperature; no corner analysis (fast/slow, temperature extremes, supply variation) has been performed.

---

## Future Work

- [ ] Extract noise figure (NF) across the band using ngspice's `.noise` analysis
- [ ] Re-tune the input matching network for S11 < -10 dB using a systematic Smith-chart or optimizer-driven approach
- [ ] Characterize output match (S22) and add an output matching network
- [ ] Evaluate linearity: P1dB and IIP3
- [ ] Run PVT corner sweeps for robustness
- [ ] Move to physical layout (via OpenLane / Magic) and re-simulate post-layout with parasitics

---

## Repository Structure

```
.
├── experiments/     # Simulation netlists / sweep experiments
├── results/         # Extracted plots and schematic images
└── README.md
```

---

## About

A self-driven RFIC learning project exploring open-source analog/RF IC design with the SKY130 PDK — built to understand the full loop from transistor-level design through simulated characterization, including where the design currently falls short of a production-ready front end.
