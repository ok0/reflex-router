# Shiu vendored code: patches and deviations

## No changes

`model.py`, `utils.py` and `LICENSE` are byte-identical to upstream
`philshiu/Drosophila_brain_model` @ 91bdd1e7dcf193f3e7ca5a8933497fcef63b7960.
Hashes are recorded in `VENDOR.toml`.

## Deviations in use (not patches)

- `runner.py` (ours, MIT) calls `model.run_trial` directly instead of `run_exp`.
  It seeds each trial with `brian2.seed(seed_base + 1000*k + t)` and returns only
  the MN9 spike count. `run_exp` sets no seed.
- `default_params` are used unchanged except `r_poi`, which is set per sweep
  frequency (as in Shiu's `example.ipynb`).
- `n_run` in `default_params` is unused; the trial count comes from our config.

## Compatibility

`runner.py` must stay Python 3.10-compatible, because it runs under the
py3.10 fallback environment as well as the py3.14 environment.
