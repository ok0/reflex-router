# rr-discover

Offline FlyWire v783 discovery toolchain for reflex-router.

## Host prerequisites

- Python 3.14 via uv.
- A working C/C++ compiler for brian2's Cython target: macOS: Xcode Command Line Tools; Linux: gcc/g++.
- About 0.9 GB free disk for raw data.

## Usage

Run from the repo root:

```
uv run rr-discover fetch --config discovery/discovery.toml [--data-dir DIR] [--record-hashes]
uv run rr-discover inspect --config discovery/discovery.toml
```

## Data integrity

- sha256 pins live in `discovery/data_manifest.toml`, trust-on-first-use.
- Zenodo md5 cross-check is applied when the Zenodo API publishes checksums.
- A mismatch fails with exit 1.
- Raw data lives in `circuit-data/v783/raw/` (git-ignored).

## Annotation source

- Repo, pinned tag and path as in `discovery/discovery.toml`.
- Exact case-sensitive `cell_type` match.
- Any naming mapping is documented in `circuit-data/v783/reports/schema_report.md`.

## Toolchain findings (M1)

- brian2 2.10.1 Cython target on Python 3.14: PASS (host macOS Darwin 24.6.0, compiler /usr/bin/cc, 2026-10-15)
- Annotation tag / file name corrections: none. Tag `v3.2.0` and path `supplemental_files/Supplemental_file1_neuron_annotations.tsv` fetched OK. Annotation root-ID column is `root_id` (candidate list handles it). Counts at v783: LC4=104, LPLC2=210, DNp01=2, descending=1303.

## M2 host prerequisites

Measured on macOS 15.7.7 arm64 (Apple M4 Pro, 14 CPU cores, 24 GiB RAM) on 2026-10-15, with 255 GiB free disk before M2 started.

- Python 3.14.8 via uv (brian2 2.10.1) for the dev env and the smoke run. Python 3.10.14 (brian2 2.5.1) via conda for the fallback sim env (ADR-14).
- C/C++ compiler for brian2's Cython target, in both envs. macOS: Xcode Command Line Tools (`/usr/bin/cc`) for 3.14; the fallback env installs `clangxx_osx-arm64=14.0.6`. Linux: remove that line from `discovery/environment-fallback.yml` and use system `gcc`/`g++`.
- conda (25.3.1 used) and network access for `shiu-fetch`, for `conda env create`, and for the v783 data fetch.
- Disk (`du -sh`): `circuit-data/v783/raw` 844M; `circuit-data/shiu/raw` 200M; `circuit-data/v783/model_input` 111M; conda env `rr-shiu-fallback` 952M; `.venv` 551M. The brian2 Cython build cache was not found under `~/.cython`; its size is not measured.
- RAM: each worker holds one whole-brain model. Measured peak RSS per worker: 2.12 GiB on the cold smoke (includes the one-time Cython compile), 1.84 GiB warm. `regress.n_proc = 8` gives about 17 GiB peak at worst, about 71 % of 24 GiB. The 80 % rule allows 9 workers at the cold peak.
- Wall time: `model-input` 15.0 s (peak RSS 4.14 GiB); `conda env create` 44 s; `regress --smoke` 1 trial at 100 Hz: 20.8 s cold, 3.2 s warm.

## M2 commands

Run from the repo root, in this order:

1. `uv run rr-discover shiu-fetch`
2. `uv run rr-discover model-input`
3. `conda env create -f discovery/environment-fallback.yml`
4. `uv run rr-discover regress --smoke`
5. `uv run rr-discover regress --capture-golden --python "$(conda run -n rr-shiu-fallback python -c 'import sys;print(sys.executable)')"` (one-time; golden committed)
6. `uv run rr-discover regress`
7. `RR_FALLBACK_PYTHON=… uv run pytest -m fallback_env`

The fallback env's explicit lock is `discovery/environment-fallback.lock.txt` (`conda list --explicit`, platform osx-arm64). All 14 pins in `environment-fallback.yml` solved as written; no solver changes.

## Model input

- Build: `uv run rr-discover model-input` writes `completeness_v783.csv`, `connectivity_v783.parquet`, `input_totals_v783.parquet` and `model_input_v783.json` to `circuit-data/v783/model_input/`.
- Sign rule (`SIGN_RULE`): presynaptic neuron inhibitory iff sum(syn_count*(gaba_avg+glut_avg)) / sum(syn_count*sum(NT_COLS)) > 0.5 over its rows with no NaN NT value; neurons with no such rows are excitatory.
- Missing NT: 1,732 rows with all-NaN NT values are excluded from the sign computation. On v783 every presynaptic neuron keeps at least one valid row (`n_pre_missing_nt = 0`), so the excitatory default for missing NT is not exercised.
- Measured agreement with Shiu's v783 `Excitatory` (`test_sign_agreement_with_shiu`): 0.96867; 4,324 of 138,005 presynaptic neurons differ. Shiu's per-synapse NT calls are not in the Zenodo table, so this rule is an approximation of Shiu's signs.
- Completeness: `completeness_v783.csv` is byte-identical to Shiu's `Completeness_783.csv` (sha256 `bbb847a4…a311`).
- Pairs: the (pre, post, Connectivity) set equals Shiu's `Connectivity_783.parquet`.
- Stats: 16,847,997 input rows; 138,639 neurons; 15,091,983 pairs; 138,005 presynaptic neurons, 43,643 inhibitory; 137,090 input-total targets.

## Stimulus set

- Source: Shiu `example.ipynb` at commit 91bdd1e. It lists 21 right-hemisphere sugar GRNs and MN9, all as v630 IDs.
- In v783, 20 of the 21 sugar GRN IDs exist. `720575940620900446` is absent and is dropped from the v783 set. Mapping it to its v783 successor is out of scope.
- The v783 annotations label some of these IDs LB3d/LB4b rather than "sugar". The list follows Shiu's example, not the annotation labels.
- Readout: MN9, `720575940660219265`, which exists in both v783 and v630.
- The IDs live in `discovery/discovery.toml` under `[regress]` (v783) and `[regress.v630]`.

## Credit (R42)

- Shiu PK, et al. "A Drosophila computational brain model reveals sensorimotor processing." Nature 634, 210–219 (2024).
- Upstream repo: `philshiu/Drosophila_brain_model` (https://github.com/philshiu/Drosophila_brain_model), pinned at commit `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` (2024-09-14), MIT License (Copyright (c) 2023 Philip Shiu and Nico Spiller).
- `discovery/src/rr_discovery/shiu/` holds the vendored `LICENSE`, `model.py` and `utils.py`, byte-identical to upstream. `VENDOR.toml` records the hashes. `PATCHES.md` lists the deviations in use: our `runner.py` calls `model.run_trial` directly with an explicit per-trial `brian2.seed`; `r_poi` is set per sweep frequency; `n_run` is unused.

## M2 results

Measured on the long runs (`regress --capture-golden`, then `regress`), both with `n_proc = 8`, `n_trials = 30` per frequency, 5 frequencies (10, 20, 50, 100, 200 Hz).

- Host: Apple M4 Pro, 14 CPU cores, 24 GiB RAM, macOS 15.7.7 arm64.
- Golden env (python 3.10.14, brian2 2.5.1): per-condition wall time 10 Hz 96.1 s, 20 Hz 81.0 s, 50 Hz 81.1 s, 100 Hz 63.7 s, 200 Hz 84.1 s; total 406.0 s (CLI wall 410.6 s); mean 81.2 s per condition; 44.3 conditions/h.
- Current env (python 3.14.8, brian2 2.10.1): per-condition wall time 10 Hz 95.0 s, 20 Hz 95.3 s, 50 Hz 100.9 s, 100 Hz 78.6 s, 200 Hz 100.2 s; total 469.9 s (CLI wall 475.9 s); mean 94.0 s per condition; 38.3 conditions/h.
- Peak RSS (per worker, 8 workers): golden max worker 2.54 GB, sum of worker peaks 18.07 GB, parent 187 MB; current max worker 2.70 GB, sum of worker peaks 19.07 GB, parent 219 MB. Max worker × 8 is about 84 % of 24 GiB; the sum of worker peaks is about 74 %.
- Disk used: `circuit-data/v783/raw` 844 MB; `circuit-data/shiu/raw` 200 MB; `circuit-data/v783/model_input` 111 MB; conda env `rr-shiu-fallback` 952 MB; `~/.cython` not present on this host.
- Verdict: PASS. monotonic PASS (non-decreasing within 1 SD); ratio PASS, R100/max = 0.712 (allowed 0.7 to 0.9); equivalence PASS, per-frequency mean and SD equal to the golden at all 5 frequencies (deviation 0.0), and the per-trial readout spikes are identical in all 150 trials.
- `sim_env` for M5/M6: `py314`. The fallback env is not needed for M5/M6. The v630 rerun was not needed because the ratio passed on v783.
- v630 availability: available, Shiu repo `philshiu/Drosophila_brain_model@91bdd1e` (`2023_03_23_completeness_630_final.csv`, `2023_03_23_connectivity_630_final.parquet`).
- M6 grid recommendation: `max conditions ≈ budget_hours × 38.3` on `py314` with `n_proc = 8` (for example, 1 h gives about 38 conditions, 10 h about 383). Each condition is 30 trials at one frequency.

## M5 discovery (LC4/LPLC2 → circuit)

Run from the repo root:

```
uv run rr-discover discover
uv run rr-discover discover --step run
uv run rr-discover discover --step post
```

- `--step all` (default) runs `run` then `post`. `--step run` simulates and writes the spike counts. `--step post` re-derives the circuit from the stored counts without resimulating.
- Add `--python <path>` only when the M2 `sim_env` in `circuit-data/v783/reports/regress_report.md` is not `py314`.
- `--n-proc` sets the worker count only. Results do not depend on it.

Outputs:

- `circuit-data/v783/circuit.json` and `circuit-data/v783/metadata.json`.
- `circuit-data/v783/reports/parallel_dn_candidates.md` and `circuit-data/v783/reports/responsive_v783.tsv`.
- Git-ignored: `circuit-data/v783/discover/` (job, spike counts `spikes_v783.tsv`, run result, `run_log.json`).

Stimulus: LC4 ∪ LPLC2 by exact annotation cell type (104 + 210 neurons, both sides), driven at 150 Hz with Shiu defaults (only `r_poi` is set), 30 trials per run, seed `785000 + t` for trial `t`.

Responsive rule: a non-stimulated neuron is responsive iff its mean rate over trials is >= 2.0 Hz and it fired in >= 50% of trials. The comparison is exact (fractions), and stimulated neurons are excluded. Responsive neurons are ranked by relative rate (rate divided by the maximum rate among non-stimulated neurons). Absolute rates are not claims.

Connection filter: keep an edge iff it has more than 10 synapses or more than 1% of the target's total input synapses. Attribution: Schlegel et al., bioRxiv 2023 abstract (doi 10.1101/2023.06.27.546055); Nature 634:139-152 (doi 10.1038/s41586-024-07686-5). This is not Dorkenwald 2024. Codex's default threshold is 5 synapses; this project uses the rule above. Deviations from the stated rule: none (pair counts are summed across neuropils before the rule).

Output identification (ADR-15): the prior set DNp02, DNp03, DNp04, DNp06 is LOW evidence; DNp11 is reported; other descending types are data-driven. A candidate must pass (i) responsive, (ii) filtered direct LC4/LPLC2 input > 0 and (iii) membership in the circuit. A no-parallel outcome is valid: the export records `parallel_output: none` and the candidates report carries the limitation line.

Reproducibility: the spike-count file holds integers only, and seeds do not depend on the worker count. Re-run with `--step post` to re-derive without resimulating.

Timings (filled after the M5 long run, AC10):

| step | observed wall time |
|------|--------------------|
| run | 101.1 s (warm, n_proc 8, from run_log.json after the long-run test); 1323.7 s (first cold run, n_proc 8) |
| post | 0.8 s (warm); 0.7 s (first run) |

Dependency: `discovery` imports `reflex_router.circuit` (the M4 writer) and declares a workspace dependency on `reflex-router`. Core never imports discovery; the artifact passes to core as files.

## M6 robustness suite

Run from the repo root. The full run is long (about 2 h planned, 3 h cap):

```
uv run rr-discover robustness
uv run rr-discover robustness --step prepare
uv run rr-discover robustness --step run
uv run rr-discover robustness --step extract
uv run rr-discover robustness --step report
```

- `--step all` (default) runs `prepare`, `run`, `extract` and `report` in that order. Each stage can be run on its own; `run` skips finished conditions and `report` needs no simulation.
- Add `--python <path>` only when the M2 `sim_env` in `circuit-data/v783/reports/regress_report.md` is not `py314`.
- `--n-proc` sets the worker count only. Results do not depend on it.
- `--time-cap-s` overrides the 3 h cap in `discovery/robustness.toml` for this invocation.

Grid: `discovery/robustness.toml` is committed and is the only source of the grid. Its sha256 is written to `frozen.json` in the work dir by the first `run` step. A later edit to the grid file fails the run unless the file adds a `[[robustness.deviations]]` entry whose `from_sha256` is the frozen hash and whose `reason` says why the grid changed. The deviation is copied into the report.

Families (30 non-control conditions and 10 controls, each at 30 trials unless reduced; the baseline is extra):

| family | conditions | content |
|---|---|---|
| rate | 3 | 50, 100, 200 Hz, bilateral |
| w_syn | 4 | Shiu `w_syn` x 0.5, 0.75, 1.5, 2.0 |
| f_poi | 4 | Shiu `f_poi` x 0.5, 0.75, 1.5, 2.0 |
| subset_side | 8 | {LC4, LPLC2, both} x {left, right, bilateral}, minus both x bilateral |
| seed | 5 | five other seed bases at baseline settings |
| interaction | 6 | LC4 only and LPLC2 only (bilateral) at 50, 100, 200 Hz |
| random_set | 5 | controls: random sets of proofread non-LC4/LPLC2/GF neurons, same size and side split |
| shuffle | 5 | controls: degree-preserving shuffled connectome, real LC4 + LPLC2 stimulated |

- The baseline is the M5 condition. It is reused from `circuit-data/v783/discover/` when the M5 spike sha256 matches `metadata.json`; otherwise it is re-simulated first. The baseline must reproduce the committed M5 circuit exactly, or the run aborts before any grid condition.
- Seeds: condition `k` (0-based, in grid order) uses seed base `786000 + 100·k`; trial `t` uses `seed_base + t`. Ranges are disjoint from each other and from the M5 range `785000`–`785029`.

Stages and outputs (work dir `circuit-data/v783/discover/robustness/`, git-ignored):

- `prepare`: `plan.json` (frozen condition list and resolved stimulated sets), `shuffles/shuffle-<k>/` (connectivity and input totals of each shuffle, plus `shuffle.json` with swap counts and checks).
- `run`: `frozen.json`, `reductions.json` (if the budget rule applies), `conditions/<cid>/` (`job.json`, `spikes.tsv`, `run.json`, or `failed.json` with the reason). A condition is skipped when its spike hash and job match.
- `extract`: `baseline.json`, `chance.json` and `conditions/<cid>/result.json`.
- `report`: `circuit-data/v783/reports/robustness.md` and `circuit-data/v783/reports/robustness_results.json`. Both are byte-deterministic from the stored results.
- `run_log.json` (in the work dir) holds the wall times, the host and the budget projection. Nothing else in the work dir or the reports carries times.

Reduction rule (R10). After the first 3 conditions are simulated in an invocation, the projected total is `elapsed + sum over pending conditions of sec_per_condition x trials / 30`. `sec_per_condition` is the median over those 3 conditions of `wall_s x 30 / n_trials`. The median is used so that one cold first start (about 22 min) does not trigger reductions by itself. If the projection exceeds the cap, the reductions are applied in this order and stop as soon as the projection fits:

1. drop the interaction family;
2. cut the random-set and shuffle controls to 3 draws each;
3. cut the trial count of pending non-baseline conditions, down to no fewer than 15.

Every applied step, dropped id and reduced condition is listed in the report. Completed conditions are never changed. The grid is never silently shrunk.

Scope: M6 publishes retention numbers only. It sets no retention threshold and gives no pass/fail verdict on the circuit. The PAC2 threshold is set by the Verifier and finalized at Gate 1 (M11).

Run-cost estimate (planning, from the M6 spec):

| Item | Count | Estimate |
|---|---|---|
| Simulated conditions in the full grid | 40 | 40 x 100 s = about 67 min warm; about 100 min if conditions average 150 s |
| Shuffled-connectome construction | 5 | unmeasured; planning allowance up to about 30 min total |
| Cold start / first-run overhead | 1 | up to about 25 min once |
| Retention analysis and report | - | seconds to minutes |
| Planning envelope for the full run | - | about 2 h; hard cap 3 h wall |

Observed (filled after the M6 long run):

| item | observed |
|---|---|
| per condition (median, range) | Measured from `run_log.json` (`run:*` keys, 30 conditions): median 58.7 s, range 35.9–1341.7 s. Rate 50/100/200 Hz: 1333.6 / 1300.7 / 1341.7 s. w_syn x0.50/0.75/1.50/2.00: 654.3 / 650.1 / 656.2 / 668.1 s. The other 23 conditions (f_poi, seed, random-set, shuffle, subset/side): 35.9–245.1 s. random-1..3 hold the second-invocation values (40.1 / 38.1 / 38.9 s), because the first-invocation values were overwritten. |
| shuffle construction (per draw) | Measured, `shuffle-1`..`shuffle-5` in `run_log.json`: 111.4–115.7 s per draw (median 112.3 s). |
| cold start | Not recorded in `run_log.json` (no prepare or cold-start timing key). |
| total wall | First invocation: not recorded as a total in `run_log.json`. The 30 `run:*` wall times sum to 8313.0 s, but that sum includes the second-invocation values for random-1..3. Second invocation (re-run of random-1..3 after the fix): `run_total` wall 118.5 s. Budget block: projected 21979.1 s against a 10800 s cap (`sec_per_condition` 1333.6 s). |
| reductions applied | Reduction rule R10 was applied: 10 conditions dropped (the 6 interaction conditions, random-4/5 and shuffle-4/5), and 27 conditions reduced from 30 to 15 trials. The projection exceeded the cap, so the reductions were applied; the measured simulation time was 8313.0 s (sum of the `run:*` wall times above). |

Long-run test (on demand; not in the default run):

```
RR_M6_LONGRUN=1 uv run pytest discovery/tests/test_v783_m6_longrun.py
```

The data-only checks (grid side split, random-set draw, shuffle, baseline sanity, chance reference) run with `uv run pytest -m flywire discovery/tests/test_v783_m6.py` after `robustness --step prepare`. They skip when their inputs are absent.
