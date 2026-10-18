# ADR-0001: Signals-to-stimulus mapping for the circuit gate

## Status

Accepted. Recorded after the fact in M10; the decision was fixed by the frozen code `spikes/s1/s1_frozen.py` and `spikes/s1/s1_verdict.py` (sha256 recorded in `reports/s1/preregistration.md`), and is stated in `reports/s1/preregistration.md`.

## Context

The circuit gate needs the two stimulus rates (r_lc4, r_lplc2) derived from the four signals s, L, k and b. Under charter P3/A3 and S1 R14 the circuit (`circuit-data/v783/circuit.json`) is fixed, and only the mapping is fitted. The mapping is the project's own design (`docs/report.md` section 2.2, row "Signals-to-stimulus mapping"), not biology. Under S1 A5 the form of the mapping is S1's own choice.

## Decision

Use a fixed-form gain and offset mapping on the feature vector `fc = [s, L, k/2, b]`:

- `x1 = clip(theta[4] + fc . theta[0:4], 0, 3)` is log10 r_lc4.
- `x2 = clip(theta[9] + fc . theta[5:9], 0, 3)` is log10 r_lplc2.
- Rates span 1 Hz to 1000 Hz.
- Gain bounds (-6.0, 6.0); offset bounds (-3.0, 6.0).
- Fixed start `THETA0 = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0)`.
- Accept (reflex) is `gf_first`; any other outcome is escalate.
- The outcome is read from the 64 x 64 Part A map. Lookup agreement is checked on at least 200 points, per S1 R14.

## Alternatives

- Fitting the circuit weights. Rejected: the circuit is fixed by P3/A3.
- A learned nonlinear encoder. Out of S1 scope ("Encoder design for production").

## Consequences

Part B results hold only for this mapping form. A different mapping form could change Part B (limitations section of `docs/report.md`). No benefit established under these settings.
