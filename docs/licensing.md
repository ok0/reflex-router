# Licensing

This file lists the license that applies to each part of the repository. Each statement points to the license or notice file that states it. The license texts are not restated here.

## Code

- The source code is licensed under the MIT License. The license text is in the root `LICENSE` file ("Copyright (c) 2026 ok0").
- The root `LICENSE` states that it does not apply to the contents of `circuit-data/`.
- Package metadata: the root `pyproject.toml` and `discovery/pyproject.toml` both declare `license = "MIT"`.

## Circuit data

- `circuit-data/` is licensed under CC BY-NC 4.0 (Attribution-NonCommercial 4.0 International). The legal text is in `circuit-data/LICENSE`.
- Attribution and the list of changes made to the source data are in `circuit-data/NOTICE.md`.
- `circuit-data/` is excluded from the core wheel and from the sdist.

## Vendored Shiu code

- The files `discovery/src/rr_discovery/shiu/model.py` and `discovery/src/rr_discovery/shiu/utils.py` are vendored from upstream code and are licensed under the MIT License, "Copyright (c) 2023 Philip Shiu and Nico Spiller". The license file is `discovery/src/rr_discovery/shiu/LICENSE`.
- Upstream: `philshiu/Drosophila_brain_model`, commit `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960`. See `discovery/src/rr_discovery/shiu/VENDOR.toml` and `discovery/src/rr_discovery/shiu/PATCHES.md`.
- Credit: Shiu et al. 2024 (see `docs/references.md`).

## License conflict

- The Zenodo record for FlyWire v783 (doi 10.5281/zenodo.10676866) states CC BY 4.0.
- The FlyWire Terms of Service (which name only edits and annotations) and the FlyWire Principles state CC BY-NC 4.0.
- The conflict is unresolved. This repository treats the non-commercial terms (CC BY-NC 4.0) as binding for `circuit-data/`.
- This repository does not resolve the conflict legally and gives no legal advice.

## Raw data

- FlyWire raw data is not redistributed in this repository.
- Raw downloads are git-ignored (`circuit-data/*/raw/`). Only the derived circuit and the reports are included.

## See also

- `NOTICE.md` (repository root)
- `circuit-data/NOTICE.md`
- `docs/references.md`
