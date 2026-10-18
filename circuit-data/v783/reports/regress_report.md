# M2 Shiu regression check

## Verdict

**PASS**

## Checks

- monotonic: PASS (non-decreasing within 1 SD)
- ratio: PASS (R100/max = 0.712 (allowed [0.7, 0.9]))
- equivalence: PASS (all frequencies within tolerance)

## Simulation environment for M5/M6

- sim_env: py314

## Sweep tables

### 3.14 (current)

| frequency | mean Hz | SD | trials | wall s |
|---|---|---|---|---|
| 10 | 0.000 | 0.000 | 30 | 95.0 |
| 20 | 0.000 | 0.000 | 30 | 95.3 |
| 50 | 13.733 | 5.234 | 30 | 100.9 |
| 100 | 62.367 | 5.276 | 30 | 78.6 |
| 200 | 87.567 | 5.590 | 30 | 100.2 |

### golden

| frequency | mean Hz | SD | trials | wall s |
|---|---|---|---|---|
| 10 | 0.000 | 0.000 | 30 | 96.1 |
| 20 | 0.000 | 0.000 | 30 | 81.0 |
| 50 | 13.733 | 5.234 | 30 | 81.1 |
| 100 | 62.367 | 5.276 | 30 | 63.7 |
| 200 | 87.567 | 5.590 | 30 | 84.1 |

## Environments

- 3.14 (current): python 3.14.8, brian2 2.10.1, numpy 2.5.4, pandas 3.0.6, pyarrow 26.0.0, joblib 1.6.0
- golden: python 3.10.14, brian2 2.5.1, numpy 1.24.4, pandas 1.5.3, pyarrow 14.0.2, joblib 1.3.2

## Host

- 3.14 (current): cpu Apple M4 Pro, machine arm64, n_cpu 14, platform macOS-15.7.7-arm64-arm-64bit-Mach-O, ram_bytes 25769803776
- golden: cpu Apple M4 Pro, machine arm64, n_cpu 14, platform macOS-15.7.7-arm64-arm-64bit, ram_bytes 25769803776

## Timing

- 3.14 (current): total 469.9 s; per condition: 10 Hz 95.0 s, 20 Hz 95.3 s, 50 Hz 100.9 s, 100 Hz 78.6 s, 200 Hz 100.2 s; mean 94.0 s; conditions/hour 38.3
- golden: total 406.0 s; per condition: 10 Hz 96.1 s, 100 Hz 63.7 s, 20 Hz 81.0 s, 200 Hz 84.1 s, 50 Hz 81.1 s; mean 81.2 s; conditions/hour 44.3

## Peak memory

- 3.14 (current): parent 209 MiB, max worker 2572 MiB, n_workers 8, sum of worker peaks 18190 MiB
- golden: parent 179 MiB, max worker 2421 MiB, n_workers 8, sum of worker peaks 17235 MiB

## v630 availability

- available: Shiu repo philshiu/Drosophila_brain_model@91bdd1e (2023_03_23_completeness_630_final.csv, 2023_03_23_connectivity_630_final.parquet)

## Inputs

- completeness sha256: bbb847a4cc2caaa7a16349722d220c087317b946d148d4d592d94d250617a311
- connectivity sha256: 8a91a17f552f2c9b8cae9c45473fd2759b7b60134690def5a6d4114e29219a56
- vendored code hash: bf4b309f45e382f2c0e0be59911ba123cfb0090ce8858114eb9db953fae88004
- stim source: Shiu example.ipynb @91bdd1e: right sugar GRNs (v630 IDs; 20 of 21 present in v783, 720575940620900446 absent) and MN9
