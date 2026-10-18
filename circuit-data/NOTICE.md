# NOTICE — circuit-data/

Status: final (M10). The data files in this directory were derived in M5 and are unchanged since; this notice was completed in M10.

## Scope

This notice and `LICENSE` (CC BY-NC 4.0) cover every file under `circuit-data/`: `LICENSE`, `NOTICE.md` and the derived data directory `circuit-data/v783/` (circuit.json, metadata.json, outputs_confirmed.toml, reports/).

## Sources

- FlyWire Consortium.
- Dorkenwald, S. et al. "Neuronal wiring diagram of an adult brain." Nature 634, 124–138 (2024), doi:10.1038/s41586-024-07558-y.
- FlyWire connectivity data v783, Zenodo, doi:10.5281/zenodo.10676866.
- Cell-type annotations from flyconnectome/flywire_annotations (tag as pinned in `discovery/discovery.toml`).
- Schlegel, P. et al. Nature 634, 139–152 (2024), doi:10.1038/s41586-024-07686-5; bioRxiv preprint 2023, doi:10.1101/2023.06.27.546055.
- Eckstein, N., Bates, A. S. et al. "Neurotransmitter classification from electron microscopy images at synaptic sites in Drosophila melanogaster." Cell 187(10), 2574–2594 (2024), doi:10.1016/j.cell.2024.03.016.
- Codex, doi:10.13140/RG.2.2.35928.67844.
- Shiu, P. K. et al. "A Drosophila computational brain model reveals sensorimotor processing." Nature 634, 210–219 (2024), doi:10.1038/s41586-024-07763-9; code `philshiu/Drosophila_brain_model` (MIT, commit pinned in `discovery/discovery.toml`).

Verification status for each entry above is recorded in `docs/references.md`.

## Vendored code

- Shiu simulation code at `discovery/src/rr_discovery/shiu/` (not in this directory), MIT, "Copyright (c) 2023 Philip Shiu and Nico Spiller", license file `discovery/src/rr_discovery/shiu/LICENSE`, upstream commit as pinned in `discovery/discovery.toml`.

## Derived data

Everything in this directory is derived data produced by the reflex-router discovery toolchain from the sources above. It is not the original FlyWire data. Changes made:

- whole-brain LIF simulation of LC4/LPLC2 stimulation;
- restriction to stimulated plus responsive neurons;
- the >10 / >1% edge filter;
- per-pair synapse counts summed across neuropils;
- sign by the Shiu NT rule;
- roles from annotations.

## License status

- The Zenodo v783 record states CC BY 4.0.
- The FlyWire Terms of Service (edits and annotations) and FlyWire Principles ("published versions of FlyWire's data") state CC BY-NC 4.0.
- The FlyWire Terms explicitly name only edits and annotations.
- The conflict is unresolved. This project treats the stricter terms (CC BY-NC 4.0, non-commercial) as binding and labels this directory CC BY-NC 4.0 (see LICENSE in this directory).
- FlyWire raw data is not redistributed in this repository.

## Gaps against metadata.json

`circuit-data/v783/metadata.json` is not edited (its bytes and the circuit hash are fixed). Differences between its `details.citations` and `docs/references.md`, with the M10 outcome:

- `eckstein_bates2024`: metadata has `doi: null` and `doi_status: "unverified"`. M10: the DOI 10.1016/j.cell.2024.03.016 was found on Crossref (Cell 187(10):2574–2594, 2024; title as in Sources above). Whether this is the work the citation means, and Bates's position in the author list, were not checked.
- `doi_status` strings cite internal project notes (for example "charter R3", "charter R40", "charter R42", "research flywire-data-access C7", "discovery.toml [zenodo]") rather than sources. The M10 sources are listed in `docs/references.md`.
- `schlegel2023_preprint`: metadata text "Schlegel et al. 2023, bioRxiv (preprint)" gives no title. The preprint title is "Whole-brain annotation and multi-connectome cell typing quantifies circuit stereotypy in Drosophila" (Europe PMC record). Its abstract contains the filter wording (10 unitary synapses; more than 1% of input); the Nature paper and the preprint full text were not read.
- `codex`: metadata text "Codex (FlyWire connectome browser)". The DOI resolves to a DataCite preprint titled "Codex: Connectome Data Explorer" (2023, publisher "Unpublished").
- `flywire_v783_zenodo`: metadata text "FlyWire v783 release (Zenodo record)". The record is titled "FlyWire Whole-brain Connectome Connectivity Data", version 783.0, published 2024-06-02, and states `cc-by-4.0` (see License status above).
- `flyconnectome/flywire_annotations` tag v3.2.0 and the Shiu code commit `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` were not fetched in M10 and remain unverified.
- `dorkenwald2024`, `schlegel2024` and `shiu2024`: DOI and page numbers agree with the Sources above; the author list was checked for Shiu (27 authors, Crossref), not for the other two.
