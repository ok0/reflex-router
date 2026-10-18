[한국어](report.ko.md)

# S1 research report: circuit gate versus formula gate

This report publishes the S1 pre-registered comparison of a gate built from the Drosophila giant-fiber escape circuit with a formula gate. The frozen verdict is STOP. No benefit is established under these settings. This is a research study, not a cost-saving router. Raw artifacts: [reports/s1/](../reports/s1/).

## 1 Question

Does a gate that decides by simulating the giant-fiber escape circuit discovered in FlyWire v783 make better fast-versus-deliberate routing decisions than a plain formula gate (weighted score against a threshold) given the same input signals? Success was defined before the run as the S1 criteria: decision cost at the stated cost ratios P = 3, 10, 30, not raw speed.

## 2 Biological basis

### 2.1 Sourced and extrapolated

- Sourced: LC4 and LPLC2 synapse onto the giant fiber; the giant fiber has a higher threshold than parallel routes yet can preempt them (von Reyn et al. 2014; von Reyn et al. 2017; Ache et al. 2019).
- Extrapolated: the mapping from looming to routing, and driving the whole-brain model with a looming-type input. The published Shiu et al. 2024 experiments did not include looming.
- Analogy: Mapping the giant-fiber output to the reflex outcome and the parallel descending output to the deliberate outcome is an analogy by design, not claimed biology.
- Caveats: Evidence caveats: the Shiu et al. 2024 methods were read from the preprint; Ache et al. 2019, von Reyn et al. 2014 and von Reyn et al. 2017 were read from abstracts and secondary pages only (abstract-only reads); the Dorkenwald et al. 2024 LC4/LPLC2-to-giant-fiber analysis and the DNp02 identifiers are unverified.
- LOW: The parallel descending neurons (17 neurons of 10 DN types in the 1231-neuron circuit) carry the evidence label LOW: the literature link between LC4/LPLC2 and these descending neurons comes from search snippets only, and the set was selected from v783 data ([parallel_dn_candidates.md](../circuit-data/v783/reports/parallel_dn_candidates.md)).
- Constants: Biological numbers are not presented as transferable constants. No threshold, latency or firing rate from the fly literature is used as a gate constant; stimulus rates in Hz are model inputs, not claims about fly neurons.

### 2.2 Feature-to-circuit table

| design element | circuit property it maps to | source | evidence level |
|---|---|---|---|
| Two gate outcomes: reflex (accept the fast answer) and deliberate (escalate) | Two escape routes: a short takeoff driven by the giant fiber (GF, DNp01) and a longer takeoff driven by parallel descending neurons; GF spike timing relative to the parallel routes selects the route | von Reyn et al. 2014 | MEDIUM, abstract only; the mapping of routes to routing outcomes is extrapolated |
| Decision rule: reflex when the GF spikes first | The GF has a higher threshold than the parallel routes yet can preempt them | von Reyn et al. 2014 | MEDIUM, abstract only |
| Two input channels, LC4 and LPLC2 | LC4 and LPLC2 synapse onto the GF | von Reyn et al. 2017; Ache et al. 2019 | MEDIUM, abstracts and secondary pages only |
| Circuit membership from an offline whole-brain LIF simulation with LC4 and LPLC2 stimulated | Whole-brain leaky integrate-and-fire model of the fly connectome | Shiu et al. 2024, Nature 634:210-219, doi 10.1038/s41586-024-07763-9 | Method sourced (methods read from the preprint); the looming-type drive is extrapolated |
| Connectome data | FlyWire whole-brain connectome, version v783 | Dorkenwald et al. 2024, Nature 634:124-138 | Data sourced; the LC4/LPLC2-to-GF analysis in that paper is unverified |
| Connection filter: more than 10 synapses, or more than 1% of the target cell's input | Connection-strength filter | Schlegel et al., bioRxiv 2023 doi 10.1101/2023.06.27.546055; Nature 634:139-152, doi 10.1038/s41586-024-07686-5 | Preprint abstract wording only |
| Deliberate output: 17 parallel descending neurons of 10 DN types | Descending neurons downstream of LC4/LPLC2 other than the GF | Search snippets plus v783 data | LOW |
| Signals-to-stimulus mapping (gain and offset to r_lc4, r_lplc2) | None | the project's own design | n/a |
| No-fire outcome resolves to deliberate | None | the project's own design | n/a |
| Formula gate (baseline) | None (not a circuit element) | the project's own design | n/a |

## 3 Method as pre-registered

### 3.1 Pre-registration record

- The binding pre-registration is the committed frozen code `spikes/s1/s1_frozen.py` (parameters, seeds, grid, costs, thresholds) and `spikes/s1/s1_verdict.py` (decision rules) with sha256 `dfb343f672dca9c5623bb6e0a9b2c1df49ea22c83a6bddd1143e978e445db9c2` and `f1da24d117d0e74f91457373b518e924aed107a67445bbe0f5e124487d1a6f01` respectively. The human-readable statement is [reports/s1/preregistration.md](../reports/s1/preregistration.md).
- Deviations: none recorded. run_meta.json records "deviations": [] and a clean git status of spikes/s1 at run time; the S1 report states "no deviations"; the independent verification ([reports/s1/verification.md](../reports/s1/verification.md)) found no change under spikes/, src/ and circuit-data/ relative to their state at run time.

### 3.2 Frozen rules

- Part A: 64 x 64 grid of log-spaced rates from 1 Hz to 1000 Hz on both axes (r_lc4, r_lplc2), simulation step 0.1 ms, window 100.0 ms; outcome per point gf_first, parallel_first, tie or no_fire.
- Part A rule: A_PASS needs gf_first and parallel_first each to cover at least 5% of the grid, each with one connected region holding at least 80% of its points, and fewer than 20% of rows and columns with more than 2 outcome changes. A_PARTIAL and A_FAIL are defined in the pre-registration.
- Part B scenarios: N0 (null, p = 0.7), L1 (linear), L2 (monotone saturating), X1 (interaction), X2 (band), C1 (circuit-native positive control), each at base noise and at high noise (p pulled halfway to 0.5).
- Signals: cache similarity s, request length L, risk class k, latency budget b, synthetic and identical across scenarios.
- Cost model: accept and correct = 1; accept and wrong = 1 + P; escalate = 5; P = 3, 10, 30 with base P = 10.
- Data: train 2000, test 20000, 20 dataset seeds per scenario and noise level.
- Fit budget: formula gate (logistic regression plus a threshold) at most 2008 evaluations; circuit gate (only the signals-to-stimulus mapping is fitted; the circuit is fixed) 8 restarts x 500 evaluations = 4000 candidate mappings. References: MLP (16 tanh hidden units, 3000 steps), true-p oracle, best constant policy.
- Statistics: paired per-seed difference circuit minus formula, 95% bootstrap CI over seeds with 10,000 resamples. Circuit WIN if the mean relative difference is at most -2% and the CI upper bound is below 0; formula WIN if at least +2% and the CI lower bound is above 0; otherwise TIE. The verdict uses P = 10 base noise, with the sign retained at P = 3 and P = 30; only X1 and X2 with the nonlinearity flag set (MLP beats formula by at least 2% at P = 10 base noise) can count as a circuit win.
- Validity: V1 (N0: no gate beats the best constant by more than 1%), V2 (C1: circuit gate not a formula WIN), V3 (L1: formula within 2% of the oracle).
- Combined table: STOP = A_FAIL with B_TIE or B_LOSE; REFRAME includes B_TIE with A_PASS or A_PARTIAL; GO needs B_WIN with A_PASS or A_PARTIAL.

## 4 Results

### 4.1 Verdict

Combined cell: STOP (Part A A_FAIL, Part B B_TIE; V1, V2, V3 PASS; validity valid), reached by mechanical application of the frozen table. No benefit is established under these settings.

### 4.2 Part A: decision map

| outcome | count | fraction | regions | largest | largest share |
|---|---:|---:|---:|---:|---:|
| gf_first | 156 | 0.0381 | 1 | 156 | 1.0000 |
| parallel_first | 3827 | 0.9343 | 1 | 3827 | 1.0000 |
| tie | 0 | 0.0000 | 0 | 0 | 0.0000 |
| no_fire | 113 | 0.0276 | 1 | 113 | 1.0000 |

- Boundary length 57; maximum outcome changes on any row or column 6; 1 of 128 lines with more than 2 changes.
- Edge saturation: capped (the low-r_lc4 edge shows gf_first, no_fire and parallel_first).
- Determinism spot-check 20 of 20; lookup agreement with direct simulation 200 of 200.
- The gf_first region is a single corner: r_lc4 below about 6 Hz and r_lplc2 about 2.4-13.9 Hz (reports/s1/verification.md); the 5% rule needed 205 cells.
- Full map: [reports/s1/report.md](../reports/s1/report.md) section 5 and `part_a_map.csv`.

### 4.3 Part B: gate comparison

Means over 20 seeds; free threshold variants; costs in abstract units. Source: reports/s1/report.md section 7 and part_b_summary.json; constant-policy rows are omitted (see the source). The effective label is defined only at P = 10, where the verdict is taken; other rows show n/a.

**Table B1: expected cost and paired difference**

| scenario | noise | P | circuit cost | formula cost | MLP cost | oracle cost | circuit minus formula | relative | 95% CI | raw label | effective label |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| N0 | base | 3 | 1.9005 | 1.9000 | 1.9000 | 1.9000 | 0.0005 | +0.03% | [0.0001, 0.0010] | tie | n/a |
| N0 | base | 10 | 4.0245 | 4.0139 | 4.0438 | 4.0000 | 0.0106 | +0.26% | [0.0046, 0.0162] | tie | tie |
| N0 | base | 30 | 5.0600 | 5.0258 | 5.0428 | 5.0000 | 0.0343 | +0.68% | [0.0187, 0.0485] | tie | n/a |
| N0 | high | 3 | 2.2003 | 2.2000 | 2.2000 | 2.2000 | 0.0003 | +0.01% | [0.0001, 0.0006] | tie | n/a |
| N0 | high | 10 | 5.0000 | 5.0000 | 5.0000 | 5.0000 | 0.0000 | +0.00% | [0.0000, 0.0000] | tie | tie |
| N0 | high | 30 | 5.0644 | 5.0072 | 5.0326 | 5.0000 | 0.0572 | +1.14% | [0.0483, 0.0665] | tie | n/a |
| L1 | base | 3 | 2.6811 | 2.6809 | 2.6809 | 2.6809 | 0.0002 | +0.01% | [0.0001, 0.0005] | tie | n/a |
| L1 | base | 10 | 4.6618 | 4.5809 | 4.5891 | 4.5660 | 0.0809 | +1.77% | [0.0518, 0.1169] | tie | tie |
| L1 | base | 30 | 5.0130 | 4.9847 | 4.9990 | 4.9684 | 0.0282 | +0.57% | [0.0136, 0.0405] | tie | n/a |
| L1 | high | 3 | 2.5905 | 2.5904 | 2.5904 | 2.5904 | 0.0001 | +0.00% | [0.0000, 0.0002] | tie | n/a |
| L1 | high | 10 | 4.9630 | 4.9220 | 4.9311 | 4.9045 | 0.0410 | +0.83% | [0.0287, 0.0531] | tie | tie |
| L1 | high | 30 | 5.0439 | 5.0183 | 5.0314 | 5.0000 | 0.0256 | +0.51% | [0.0080, 0.0403] | tie | n/a |
| L2 | base | 3 | 2.4373 | 2.4368 | 2.4368 | 2.4368 | 0.0006 | +0.02% | [0.0002, 0.0013] | tie | n/a |
| L2 | base | 10 | 3.7340 | 3.6644 | 3.6497 | 3.6343 | 0.0696 | +1.90% | [0.0176, 0.1327] | tie | tie |
| L2 | base | 30 | 4.8678 | 4.6348 | 4.6505 | 4.6015 | 0.2330 | +5.03% | [0.1890, 0.2729] | formula_win | n/a |
| L2 | high | 3 | 2.4686 | 2.4684 | 2.4684 | 2.4684 | 0.0002 | +0.01% | [0.0001, 0.0004] | tie | n/a |
| L2 | high | 10 | 4.7098 | 4.6017 | 4.5950 | 4.5563 | 0.1081 | +2.35% | [0.0716, 0.1430] | formula_win | formula_win |
| L2 | high | 30 | 5.0443 | 5.0095 | 5.0295 | 5.0000 | 0.0348 | +0.69% | [0.0244, 0.0461] | tie | n/a |
| X1 | base | 3 | 2.7504 | 2.7502 | 2.7502 | 2.7502 | 0.0003 | +0.01% | [0.0001, 0.0005] | tie | n/a |
| X1 | base | 10 | 4.5332 | 4.5871 | 4.3991 | 4.3058 | -0.0539 | -1.18% | [-0.0688, -0.0317] | tie | tie |
| X1 | base | 30 | 5.0351 | 5.0326 | 5.0552 | 5.0000 | 0.0025 | +0.05% | [-0.0135, 0.0168] | tie | n/a |
| X1 | high | 3 | 2.6254 | 2.6251 | 2.6251 | 2.6251 | 0.0004 | +0.01% | [0.0001, 0.0007] | tie | n/a |
| X1 | high | 10 | 4.9190 | 4.9311 | 4.8774 | 4.7917 | -0.0121 | -0.25% | [-0.0297, 0.0066] | tie | tie |
| X1 | high | 30 | 5.0527 | 5.0091 | 5.0387 | 5.0000 | 0.0437 | +0.87% | [0.0302, 0.0584] | tie | n/a |
| X2 | base | 3 | 2.6567 | 2.6561 | 2.6561 | 2.6561 | 0.0006 | +0.02% | [0.0002, 0.0011] | tie | n/a |
| X2 | base | 10 | 4.8267 | 5.0004 | 4.3269 | 4.1751 | -0.1737 | -3.47% | [-0.2064, -0.1423] | circuit_win | tie |
| X2 | base | 30 | 5.0275 | 5.0039 | 5.0570 | 5.0000 | 0.0236 | +0.47% | [0.0138, 0.0356] | tie | n/a |
| X2 | high | 3 | 2.5783 | 2.5780 | 2.5780 | 2.5780 | 0.0002 | +0.01% | [0.0001, 0.0004] | tie | n/a |
| X2 | high | 10 | 4.9929 | 5.0054 | 4.8902 | 4.7525 | -0.0124 | -0.25% | [-0.0210, -0.0039] | tie | tie |
| X2 | high | 30 | 5.0390 | 5.0124 | 5.0299 | 5.0000 | 0.0266 | +0.53% | [0.0191, 0.0335] | tie | n/a |
| C1 | base | 3 | 3.0834 | 3.0833 | 3.0833 | 3.0833 | 0.0001 | +0.00% | [0.0000, 0.0002] | tie | n/a |
| C1 | base | 10 | 4.8256 | 4.8479 | 4.8018 | 4.7684 | -0.0223 | -0.46% | [-0.0453, 0.0033] | tie | tie |
| C1 | base | 30 | 5.0227 | 5.0186 | 5.0155 | 5.0000 | 0.0041 | +0.08% | [-0.0129, 0.0210] | tie | n/a |
| C1 | high | 3 | 2.7919 | 2.7916 | 2.7916 | 2.7916 | 0.0003 | +0.01% | [0.0001, 0.0005] | tie | n/a |
| C1 | high | 10 | 4.9901 | 4.9831 | 4.9699 | 4.9305 | 0.0070 | +0.14% | [-0.0055, 0.0186] | tie | tie |
| C1 | high | 30 | 5.0383 | 5.0124 | 5.0234 | 5.0000 | 0.0259 | +0.52% | [0.0142, 0.0373] | tie | n/a |

**Table B2: false-reflex rate, reflex share and decision accuracy**

| scenario | noise | P | circuit false-reflex | formula false-reflex | MLP false-reflex | circuit reflex share | formula reflex share | MLP reflex share | circuit decision acc | formula decision acc | MLP decision acc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| N0 | base | 3 | 0.3000 | 0.3000 | 0.3000 | 0.9998 | 1.0000 | 1.0000 | 0.9998 | 1.0000 | 1.0000 |
| N0 | base | 10 | 0.3000 | 0.3000 | 0.3000 | 0.9755 | 0.9861 | 0.9562 | 0.9755 | 0.9861 | 0.9562 |
| N0 | base | 30 | 0.3000 | 0.3000 | 0.3000 | 0.0120 | 0.0052 | 0.0086 | 0.9880 | 0.9948 | 0.9914 |
| N0 | high | 3 | 0.4000 | 0.4000 | 0.4000 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| N0 | high | 10 | 0.4000 | 0.4000 | 0.4000 | 0.2373 | 0.5605 | 0.5390 | 0.7627 | 0.4395 | 0.4610 |
| N0 | high | 30 | 0.4000 | 0.4000 | 0.4000 | 0.0081 | 0.0009 | 0.0041 | 0.9919 | 0.9991 | 0.9959 |
| L1 | base | 3 | 0.5603 | 0.5603 | 0.5603 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| L1 | base | 10 | 0.2384 | 0.2420 | 0.2539 | 0.2123 | 0.2715 | 0.2890 | 0.8892 | 0.9544 | 0.9425 |
| L1 | base | 30 | 0.1586 | 0.1090 | 0.1191 | 0.0269 | 0.0437 | 0.0498 | 0.9664 | 0.9791 | 0.9713 |
| L1 | high | 3 | 0.5301 | 0.5301 | 0.5301 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| L1 | high | 10 | 0.3591 | 0.3528 | 0.3557 | 0.0941 | 0.1960 | 0.1868 | 0.8654 | 0.9341 | 0.9157 |
| L1 | high | 30 | 0.3653 | 0.2809 | 0.3077 | 0.0071 | 0.0038 | 0.0059 | 0.9929 | 0.9962 | 0.9941 |
| L2 | base | 3 | 0.4789 | 0.4789 | 0.4789 | 0.9998 | 1.0000 | 1.0000 | 0.9998 | 1.0000 | 1.0000 |
| L2 | base | 10 | 0.1222 | 0.1250 | 0.1216 | 0.4554 | 0.4860 | 0.4854 | 0.9515 | 0.9763 | 0.9832 |
| L2 | base | 30 | 0.1072 | 0.1027 | 0.1021 | 0.1597 | 0.4005 | 0.3763 | 0.7261 | 0.9610 | 0.9405 |
| L2 | high | 3 | 0.4895 | 0.4895 | 0.4895 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| L2 | high | 10 | 0.3088 | 0.3096 | 0.3100 | 0.3196 | 0.4425 | 0.4516 | 0.8303 | 0.9430 | 0.9510 |
| L2 | high | 30 | 0.3409 | 0.3000 | 0.3002 | 0.0076 | 0.0019 | 0.0059 | 0.9924 | 0.9981 | 0.9941 |
| X1 | base | 3 | 0.5834 | 0.5834 | 0.5834 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| X1 | base | 10 | 0.1677 | 0.2406 | 0.1772 | 0.2009 | 0.2609 | 0.2700 | 0.9114 | 0.9034 | 0.9676 |
| X1 | base | 30 | 0.1698 | 0.1528 | 0.1505 | 0.0476 | 0.0449 | 0.1051 | 0.9524 | 0.9551 | 0.8949 |
| X1 | high | 3 | 0.5417 | 0.5417 | 0.5417 | 0.9998 | 1.0000 | 1.0000 | 0.9998 | 1.0000 | 1.0000 |
| X1 | high | 10 | 0.3513 | 0.3588 | 0.3440 | 0.1290 | 0.1959 | 0.2283 | 0.8408 | 0.8662 | 0.9182 |
| X1 | high | 30 | 0.3833 | 0.3250 | 0.3261 | 0.0075 | 0.0016 | 0.0067 | 0.9925 | 0.9984 | 0.9933 |
| X2 | base | 3 | 0.5520 | 0.5520 | 0.5520 | 0.9997 | 1.0000 | 1.0000 | 0.9997 | 1.0000 | 1.0000 |
| X2 | base | 10 | 0.2479 | 0.4172 | 0.1873 | 0.1204 | 0.0162 | 0.3177 | 0.7479 | 0.6726 | 0.9474 |
| X2 | base | 30 | 0.2009 | 0.3166 | 0.1506 | 0.0173 | 0.0010 | 0.1077 | 0.9827 | 0.9990 | 0.8923 |
| X2 | high | 3 | 0.5260 | 0.5260 | 0.5260 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| X2 | high | 10 | 0.3893 | 0.5360 | 0.3502 | 0.0593 | 0.0075 | 0.2316 | 0.7044 | 0.6702 | 0.8591 |
| X2 | high | 30 | 0.4028 | 0.5201 | 0.3250 | 0.0053 | 0.0013 | 0.0052 | 0.9947 | 0.9987 | 0.9948 |
| C1 | base | 3 | 0.6944 | 0.6944 | 0.6944 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| C1 | base | 10 | 0.1721 | 0.2173 | 0.1842 | 0.0755 | 0.0827 | 0.0921 | 0.9781 | 0.9718 | 0.9888 |
| C1 | base | 30 | 0.2095 | 0.2067 | 0.1693 | 0.0150 | 0.0153 | 0.0225 | 0.9850 | 0.9847 | 0.9775 |
| C1 | high | 3 | 0.5972 | 0.5972 | 0.5972 | 0.9999 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 |
| C1 | high | 10 | 0.3766 | 0.3782 | 0.3555 | 0.0379 | 0.0612 | 0.0728 | 0.9329 | 0.9493 | 0.9639 |
| C1 | high | 30 | 0.4934 | 0.4035 | 0.3635 | 0.0039 | 0.0018 | 0.0038 | 0.9961 | 0.9982 | 0.9962 |

**Table B3: matched reflex share (each gate refit with the share within 2 points of 50%)**

| scenario | noise | P | circuit false-reflex | circuit reflex share | circuit fit feasible (seeds) | formula false-reflex | formula reflex share | MLP false-reflex | MLP reflex share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| N0 | base | 3 | 0.3000 | 0.5157 | 20/20 | 0.3000 | 0.5028 | 0.3000 | 0.5004 |
| N0 | base | 10 | 0.3000 | 0.5123 | 20/20 | 0.3000 | 0.5028 | 0.3000 | 0.5004 |
| N0 | base | 30 | 0.3000 | 0.4884 | 20/20 | 0.3000 | 0.5028 | 0.3000 | 0.5004 |
| N0 | high | 3 | 0.4000 | 0.5195 | 20/20 | 0.4000 | 0.5008 | 0.4000 | 0.5015 |
| N0 | high | 10 | 0.4000 | 0.4959 | 20/20 | 0.4000 | 0.5008 | 0.4000 | 0.5015 |
| N0 | high | 30 | 0.4000 | 0.4849 | 20/20 | 0.4000 | 0.5008 | 0.4000 | 0.5015 |
| L1 | base | 3 | 0.4107 | 0.5170 | 20/20 | 0.3524 | 0.5028 | 0.3548 | 0.5032 |
| L1 | base | 10 | 0.3733 | 0.4876 | 20/20 | 0.3524 | 0.5028 | 0.3548 | 0.5032 |
| L1 | base | 30 | 0.3744 | 0.4861 | 20/20 | 0.3524 | 0.5028 | 0.3548 | 0.5032 |
| L1 | high | 3 | 0.4593 | 0.5175 | 20/20 | 0.4273 | 0.5018 | 0.4317 | 0.5032 |
| L1 | high | 10 | 0.4393 | 0.4833 | 20/20 | 0.4273 | 0.5018 | 0.4317 | 0.5032 |
| L1 | high | 30 | 0.4503 | 0.4836 | 20/20 | 0.4273 | 0.5018 | 0.4317 | 0.5032 |
| L2 | base | 3 | 0.1898 | 0.5158 | 20/20 | 0.1356 | 0.5019 | 0.1325 | 0.5021 |
| L2 | base | 10 | 0.1557 | 0.4965 | 20/20 | 0.1356 | 0.5019 | 0.1325 | 0.5021 |
| L2 | base | 30 | 0.1606 | 0.4862 | 20/20 | 0.1356 | 0.5019 | 0.1325 | 0.5021 |
| L2 | high | 3 | 0.3730 | 0.5140 | 20/20 | 0.3240 | 0.5032 | 0.3210 | 0.5021 |
| L2 | high | 10 | 0.3378 | 0.4887 | 20/20 | 0.3240 | 0.5032 | 0.3210 | 0.5021 |
| L2 | high | 30 | 0.3481 | 0.4854 | 20/20 | 0.3240 | 0.5032 | 0.3210 | 0.5021 |
| X1 | base | 3 | 0.4461 | 0.5170 | 20/20 | 0.4202 | 0.5024 | 0.4192 | 0.5040 |
| X1 | base | 10 | 0.4215 | 0.4838 | 20/20 | 0.4202 | 0.5024 | 0.4192 | 0.5040 |
| X1 | base | 30 | 0.4270 | 0.4869 | 20/20 | 0.4202 | 0.5024 | 0.4192 | 0.5040 |
| X1 | high | 3 | 0.4831 | 0.5186 | 20/20 | 0.4610 | 0.5021 | 0.4603 | 0.5025 |
| X1 | high | 10 | 0.4636 | 0.4854 | 20/20 | 0.4610 | 0.5021 | 0.4603 | 0.5025 |
| X1 | high | 30 | 0.4696 | 0.4830 | 20/20 | 0.4610 | 0.5021 | 0.4603 | 0.5025 |
| X2 | base | 3 | 0.4323 | 0.5201 | 20/20 | 0.4592 | 0.5013 | 0.3536 | 0.4985 |
| X2 | base | 10 | 0.4122 | 0.4901 | 20/20 | 0.4592 | 0.5013 | 0.3536 | 0.4985 |
| X2 | base | 30 | 0.4182 | 0.4838 | 20/20 | 0.4592 | 0.5013 | 0.3536 | 0.4985 |
| X2 | high | 3 | 0.4796 | 0.5182 | 20/20 | 0.4795 | 0.4995 | 0.4325 | 0.4975 |
| X2 | high | 10 | 0.4616 | 0.4833 | 20/20 | 0.4795 | 0.4995 | 0.4325 | 0.4975 |
| X2 | high | 30 | 0.4682 | 0.4808 | 20/20 | 0.4795 | 0.4995 | 0.4325 | 0.4975 |
| C1 | base | 3 | 0.6478 | 0.5191 | 20/20 | 0.6393 | 0.5022 | 0.6386 | 0.4991 |
| C1 | base | 10 | 0.6360 | 0.4773 | 20/20 | 0.6393 | 0.5022 | 0.6386 | 0.4991 |
| C1 | base | 30 | 0.6388 | 0.4798 | 20/20 | 0.6393 | 0.5022 | 0.6386 | 0.4991 |
| C1 | high | 3 | 0.5784 | 0.5145 | 20/20 | 0.5695 | 0.5005 | 0.5694 | 0.4992 |
| C1 | high | 10 | 0.5750 | 0.4831 | 20/20 | 0.5695 | 0.5005 | 0.5694 | 0.4992 |
| C1 | high | 30 | 0.5789 | 0.4784 | 20/20 | 0.5695 | 0.5005 | 0.5694 | 0.4992 |

Nonlinearity flag: set for X1 and X2 (the MLP reference beats the formula gate by 4.1% and 13.5% at P = 10, base noise, as recomputed in reports/s1/verification.md).

### 4.4 Items (a) to (e)

**(a)** The verdict was STOP by mechanical rule: A_FAIL with B_TIE is the STOP cell of the frozen table.

**(b)** Part A failed only on the 5% coverage rule: gf_first covered 156/4096 = 3.81% of the grid. The region sits at an edge of the frozen 1-1000 Hz grid and is not saturated there, so the grid may cut off part of it. The other Part A conditions held (one region per outcome, 1 of 128 lines over 2 changes). Under the frozen rule (`part_a_verdict` in `spikes/s1/s1_verdict.py`), 5% coverage would give A_PASS, because the other Part A conditions already hold; `reports/s1/verification.md` states A_PARTIAL instead, which differs from the frozen code. Either label combined with B_TIE maps to REFRAME, so the STOP verdict (A_FAIL, B_TIE) is unchanged.

**(c)** Part B was a tie. On X2 the circuit had a raw win at P = 10 (-3.47%, 95% CI [-0.2064, -0.1423]), but the sign flips at P = 30 (+0.47%), so the pre-registered sign rule demoted it to tie. The circuit lost to the MLP reference by a wide margin: on X2 at P = 10 the expected cost was 4.8267 for the circuit, 4.3269 for the MLP and 4.1751 for the oracle. X1 was a tie (-1.18%, CI [-0.0688, -0.0317]).

**(d)** The C1 positive control was degenerate: the frozen offset rule gave o* = -1.9 with a gf_first share of 0.0935 instead of the 50% target, so V2 passing is weak evidence that the fit can recover a circuit-generated rule.

**(e)** The result holds only under these settings: the frozen grid, the 6 synthetic scenarios and their signals, the fit budget, the fixed-form mapping and the discovered circuit. No benefit is established under these settings. Nothing is concluded about other circuits, other mappings or real LLM traffic.

## 5 Limitations

- One discovered circuit and one fixed-form mapping (gain and offset); a different mapping form could change Part B.
- Synthetic signals and scenarios; labels are a proxy, not real requests.
- A fixed fit budget (circuit 4000, formula at most 2008 evaluations).
- The frozen grid edge cuts the gf_first region (Part A).
- The C1 control was degenerate, so circuit recovery is weakly tested.
- The robustness run was reduced by its pre-registered rule (section 6).
- The biology rests on MEDIUM and LOW evidence, partly abstract-only or unverified (section 2).
- Real LLM traffic was never tested.

## 6 Robustness disclosure

The M6 whole-brain robustness report is published unchanged: [circuit-data/v783/reports/robustness.md](../circuit-data/v783/reports/robustness.md), with machine-readable results in `robustness_results.json` next to it. It reruns the discovery under varied conditions (families rate, w_syn, f_poi, subset_side, seed) plus random-set and shuffled-connectome negative controls, and reports how many of the 917 responsive baseline neurons are retained. The report sets no retention threshold and gives no pass/fail verdict; this write-up gives none either.

Numbers quoted from the report:

- rate-100hz: 657 / 917 retained, core retention 0.7165, GF set equal to baseline: yes.
- Completed grid conditions: core retention from 0.2290 to 0.9967 (median 0.8435).
- Control conditions: core retention from 0.0338 to 0.2628 (median 0.1442); random-1: 0.2628, GF set equal: no; shuffle-1: 0.0360.
- Chance level (1000 random sets of 917 neurons): mean core retention 0.0066.
- The GF set equals the baseline in every completed grid condition and in no control condition.

Reduction: The run applied the pre-registered reduction rule: the interaction family was dropped, random-set and shuffle controls were cut to 3 draws, and remaining non-baseline conditions were cut to 15 trials. 10 conditions were dropped, 27 conditions were reduced from 30 to 15 trials, within_cap is false (`robustness_results.json`), the remaining 30 conditions completed, and 0 failed.

Post-hoc wording change: The wording of the M6 acceptance criterion for this run was relaxed post-hoc, after the run had been seen and the M6 verifier had failed it, by the user's decision, so that a run reduced by the pre-registered rule could be accepted. No results-dependent threshold was changed, and the reductions were set by the rule from timing measured before the 4th condition, not chosen after seeing retention results.

## 7 Gate overhead

Decision overhead of the circuit gate, measured in M4 on synthetic circuits (no FlyWire data), 40 samples, seed 0, dt 0.1 ms, window 100.0 ms. Every sample ended in no_fire, so this is a synthetic, no-fire worst case. There is no threshold and no pass/fail, and no saving of any kind is claimed. Source: [reports/gate_overhead_m4.md](../reports/gate_overhead_m4.md).

| neurons | connections | cold p50 (us) | cold p95 (us) | warm p50 (us) | warm p95 (us) | outcomes |
|---:|---:|---:|---:|---:|---:|---|
| 1000 | 10000 | 9124.8 | 9438.4 | 0.7 | 2.0 | no_fire: 40 |
| 5000 | 50000 | 20199.2 | 20843.8 | 0.6 | 0.9 | no_fire: 40 |

Cold is a first decision with no memo; warm is a repeated decision served from the rate-keyed memo.

## 8 Post-hoc analysis

None. No analysis beyond the pre-registered S1 analysis was made for this write-up, and no number here is derived beyond the published artifacts. The post-hoc wording change to the M6 acceptance criterion (section 6) changed no analysis and no threshold.
