# Changelog

[한국어](CHANGELOG.md) | English

## Public release

This repository was started on 2026-07-22.

However, it was created on 2026-10-18 as a clean-slate public release (code scrubbing and public transition) starting from a single initial commit. The development recorded below was done in a previous repository.

## Stage 8

- Finished repository cleanup: licensing and data attribution, bibliography and citation markers, ADRs for stimulus mapping, fit budget and S1 decision rules, S1 research report (with Korean translation), confirmed circuit output cell types, and repository hygiene tests.

## Stage 7

- Published S1 spike results, pre-registration and verification, with tests checking the published artifacts against their checksums.
- Reworded the README goal to describe the gate.

## Stage 6

- Removed the router, race mode, arcs and adapters from `core`, and removed the `bench` package from the workspace.

## Stage 5

- Added the whole-brain robustness analysis: negative controls, retention metrics, driver, CLI subcommand, and published report and results.
- Pre-registered the circuit-vs-formula gate spike.
- Added the project README.

## Stage 4

- Added the discovery pipeline: model input builder, responsive rule extraction, connection filter, run stage, output identification, circuit export, and the `discover` command.
- Added the v783 escape circuit artifact and discovery reports, with tests for the pipeline and long-run reproducibility.

## Stage 3

- Added the runtime LIF simulator, circuit format and circuit gate; circuits may omit a parallel output group.

## Stage 2

- Added the `core` skeleton with the formula gate, race mode and decision records.

## Stage 1

- Set up the workspace scaffold, toolchain and data spike.
