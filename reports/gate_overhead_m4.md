# M4 gate decision overhead on synthetic circuits (no FlyWire data); report only, PAC6 judged in M11

- python: 3.14.8 (main, Oct  9 2026, 15:11:09) [Clang 22.1.3 ]
- numpy: 2.5.4
- platform: macOS-15.7.7-arm64-arm-64bit-Mach-O
- machine: arm64
- processor: arm
- dt_ms: 0.1, window_ms: 100.0, memo_quantum_hz: 1.0
- samples: 40, seed: 0

| neurons | connections | cold p50 (us) | cold p95 (us) | warm p50 (us) | warm p95 (us) | outcomes |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1000 | 10000 | 9124.8 | 9438.4 | 0.7 | 2.0 | no_fire: 40 |
| 5000 | 50000 | 20199.2 | 20843.8 | 0.6 | 0.9 | no_fire: 40 |
