# NOTICE — reflex-router

## Copyright and code license

The source code in this repository is licensed under the MIT License (root `LICENSE`, "Copyright (c) 2026 ok0"). The root `LICENSE` states that it does not apply to `circuit-data/`.

## Circuit data

`circuit-data/` is licensed under CC BY-NC 4.0 (`circuit-data/LICENSE`). It is derived from the FlyWire v783 connectome (Zenodo, doi:10.5281/zenodo.10676866). Everything in `circuit-data/` is derived data produced by the reflex-router discovery toolchain. It is not the original FlyWire data. Changes made:

- whole-brain LIF simulation of LC4/LPLC2 stimulation;
- restriction to stimulated plus responsive neurons;
- the >10 / >1% edge filter;
- per-pair synapse counts summed across neuropils;
- sign by the Shiu NT rule;
- roles from annotations.

## Attribution

- FlyWire Consortium.
- Dorkenwald, S. et al. "Neuronal wiring diagram of an adult brain." Nature 634, 124–138 (2024), doi:10.1038/s41586-024-07558-y.
- FlyWire connectivity data v783, Zenodo, doi:10.5281/zenodo.10676866.
- Cell-type annotations from flyconnectome/flywire_annotations (tag as pinned in `discovery/discovery.toml`).
- Schlegel, P. et al. Nature 634, 139–152 (2024), doi:10.1038/s41586-024-07686-5; bioRxiv preprint 2023, doi:10.1101/2023.06.27.546055.
- Eckstein, N., Bates, A. S. et al. "Neurotransmitter classification from electron microscopy images at synaptic sites in Drosophila melanogaster." Cell 187(10), 2574–2594 (2024), doi:10.1016/j.cell.2024.03.016.
- Codex, doi:10.13140/RG.2.2.35928.67844.
- Shiu, P. K. et al. "A Drosophila computational brain model reveals sensorimotor processing." Nature 634, 210–219 (2024), doi:10.1038/s41586-024-07763-9; code `philshiu/Drosophila_brain_model` (MIT, commit pinned in `discovery/discovery.toml`).

Verification status for each entry above is recorded in `docs/references.md`.

## License conflict

- The Zenodo v783 record states CC BY 4.0.
- The FlyWire Terms of Service (edits and annotations) and FlyWire Principles ("published versions of FlyWire's data") state CC BY-NC 4.0.
- The FlyWire Terms explicitly name only edits and annotations.
- The conflict is unresolved. This project treats the stricter terms (CC BY-NC 4.0, non-commercial) as binding and labels `circuit-data/` CC BY-NC 4.0 (see `circuit-data/LICENSE`).
- FlyWire raw data is not redistributed in this repository.

## Vendored code

- Shiu simulation code at `discovery/src/rr_discovery/shiu/` (not in `circuit-data/`), MIT, "Copyright (c) 2023 Philip Shiu and Nico Spiller", license file `discovery/src/rr_discovery/shiu/LICENSE`, upstream commit as pinned in `discovery/discovery.toml`.

## See also

- `docs/licensing.md` — license split and the license conflict.
- `docs/references.md` — bibliography and verification status.
- `circuit-data/NOTICE.md` — notice for the circuit data directory.
