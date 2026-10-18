from pathlib import Path
from typing import Any

from rr_discovery.robust_report import FORBIDDEN, NO_ROLE, STATEMENT, render, write

SECTIONS = [
    "## Grid and configuration",
    "## Baseline sanity",
    "## Retention",
    "## Chance-level reference",
    "## Negative controls",
    "## GF identity",
    "## Parallel identity",
    "## Persistence",
    "## Failed, dropped or reduced conditions",
    "## Run cost",
]

SHA = "a" * 64


def _metrics(retained: int, ref: int, rel: float) -> dict[str, Any]:
    return {
        "n_stimulated": 4,
        "n_core_excluded": 1,
        "reference_size": ref,
        "retained": retained,
        "n_new": 2,
        "n_both": retained,
        "core_retention": rel,
        "jaccard": 0.5,
        "spearman": 0.5,
    }


def _results(tmp: Path) -> dict[str, Any]:
    grid_text = "[robustness]\nschema = 1\n"
    completed_grid = {
        "cid": "rate-50hz",
        "family": "rate",
        "control": False,
        "status": "completed",
        "reason": None,
        "reduced": False,
        "params": {
            "rate_hz": 50.0,
            "w_syn_mult": 1.0,
            "f_poi_mult": 1.0,
            "groups": ["lc4", "lplc2"],
            "side": "bilateral",
            "n_trials": 30,
            "seed_base": 786000,
            "connectivity": "real",
        },
        "n_stimulated": 4,
        "spikes_sha256": SHA,
        "core": _metrics(3, 4, 0.75),
        "circuit": {"n_members": 10, "n_edges": 20, "n_edges_shared": 15, "edge_jaccard": 0.6},
        "gf": {
            "ids": [301],
            "equals_baseline": False,
            "missing": [
                {
                    "root_id": 302,
                    "responsive": False,
                    "rate_hz": 0.5,
                    "rel_rate": 0.1,
                    "rank": None,
                    "trial_frac": 0.25,
                }
            ],
            "extra": [],
        },
        "parallel": {
            "baseline_has_parallel": True,
            "condition_ids": [401],
            "retained_ids": [401],
            "new_ids": [],
            "lost": [[402, "DNp03", False, False]],
            "new_cell_types": [],
            "equals_baseline": False,
            "per_type": [
                {"cell_type": "DNp02", "n_baseline": 1, "n_retained": 1, "n_condition": 1},
                {"cell_type": "DNp03", "n_baseline": 1, "n_retained": 0, "n_condition": 0},
            ],
        },
        "random_draw": None,
    }
    second_grid = {
        **completed_grid,
        "cid": "wsyn-x0.50",
        "family": "w_syn",
        "core": _metrics(4, 4, 1.0),
        "gf": {
            "ids": [301, 302],
            "equals_baseline": True,
            "missing": [],
            "extra": [],
        },
        "parallel": {
            **completed_grid["parallel"],
            "retained_ids": [401, 402],
            "lost": [],
            "equals_baseline": True,
            "per_type": [
                {"cell_type": "DNp02", "n_baseline": 1, "n_retained": 1, "n_condition": 1},
                {"cell_type": "DNp03", "n_baseline": 1, "n_retained": 1, "n_condition": 1},
            ],
        },
    }
    control = {
        "cid": "random-1",
        "family": "random_set",
        "control": True,
        "status": "completed",
        "reason": None,
        "reduced": False,
        "params": {
            "rate_hz": 50.0,
            "w_syn_mult": 1.0,
            "f_poi_mult": 1.0,
            "groups": ["random"],
            "side": "bilateral",
            "n_trials": 30,
            "seed_base": 791000,
            "connectivity": "real",
        },
        "n_stimulated": 6,
        "spikes_sha256": SHA,
        "core": _metrics(0, 4, 0.0),
        "circuit": {"n_members": 3, "n_edges": 2, "n_edges_shared": 0, "edge_jaccard": 0.0},
        "gf": {"ids": [], "equals_baseline": False, "missing": [], "extra": []},
        "parallel": None,
        "random_draw": {
            "draw": 1,
            "side_counts": {"left": 2, "right": 3, "unlabeled": 1},
            "ids": [501, 502, 503, 504, 505, 506],
        },
    }
    failed = {
        "cid": "stim-lc4-left",
        "family": "subset_side",
        "control": False,
        "status": "failed",
        "reason": "condition runner exited with status 1",
        "reduced": False,
        "params": {
            "rate_hz": 50.0,
            "w_syn_mult": 1.0,
            "f_poi_mult": 1.0,
            "groups": ["lc4"],
            "side": "left",
            "n_trials": 30,
            "seed_base": 787000,
            "connectivity": "real",
        },
        "n_stimulated": None,
        "spikes_sha256": None,
        "core": None,
        "circuit": None,
        "gf": None,
        "parallel": None,
        "random_draw": None,
    }
    dropped = {
        "cid": "inter-lc4-50hz",
        "family": "interaction",
        "control": False,
        "status": "dropped",
        "reason": None,
        "reduced": False,
        "params": {
            "rate_hz": 50.0,
            "w_syn_mult": 1.0,
            "f_poi_mult": 1.0,
            "groups": ["lc4", "lplc2"],
            "side": "bilateral",
            "n_trials": 30,
            "seed_base": 788000,
            "connectivity": "real",
        },
        "n_stimulated": None,
        "spikes_sha256": None,
        "core": None,
        "circuit": None,
        "gf": None,
        "parallel": None,
        "random_draw": None,
    }
    return {
        "schema": 1,
        "kind": "rr-robustness",
        "data_version": "v783",
        "statement": STATEMENT,
        "grid": {
            "file": "robustness.toml",
            "sha256": SHA,
            "text": grid_text,
            "deviations": [],
        },
        "baseline": {
            "source": "m5",
            "spikes_sha256": SHA,
            "seed_base": 786000,
            "n_trials": 30,
            "rate_hz": 50.0,
            "n_responsive": 9,
            "core_size": 4,
            "n_members": 10,
            "n_edges": 20,
            "gf_ids": [301, 302],
            "parallel_ids": [401, 402],
            "parallel_cell_types": ["DNp02", "DNp03"],
            "circuit_sha256": SHA,
            "matches_m5": True,
            "side_counts": {"lc4": {"left": 1, "right": 1, "unlabeled": 0}},
        },
        "check_ii": [
            {"root_id": 401, "cell_type": "DNp02", "check_ii": True},
            {"root_id": 402, "cell_type": "DNp03", "check_ii": True},
        ],
        "tracked_types": ["DNp02", "DNp03", "DNp04"],
        "conditions": [completed_grid, second_grid, control, failed, dropped],
        "reductions": {
            "steps": [{"code": "drop_interaction", "n": 0}],
            "dropped": ["inter-lc4-50hz"],
            "reduced": {},
            "within_cap": True,
        },
        "chance": {
            "n_draws": 10,
            "seed": 3,
            "set_size": 4,
            "population_size": 20,
            "retention_mean": 0.2,
            "retention_sd": 0.1,
            "retention_min": 0.0,
            "retention_max": 0.5,
            "jaccard_mean": 0.1,
            "jaccard_sd": 0.05,
            "jaccard_min": 0.0,
            "jaccard_max": 0.3,
        },
        "shuffles": [
            {
                "draw": 1,
                "seed": 5,
                "rounds": 2,
                "n_attempted": 10,
                "n_accepted": 6,
                "n_changed_edges": 12,
                "self_loops_before": 0,
                "self_loops_after": 0,
                "checks": {
                    "out_degree_equal": True,
                    "in_degree_equal": True,
                    "syn_multiset_equal": True,
                    "signs_follow_pre": True,
                    "no_duplicates": True,
                    "no_new_self_loops": True,
                    "self_loops_before": 0,
                    "self_loops_after": 0,
                },
                "connectivity_sha256": SHA,
                "input_totals_sha256": SHA,
            }
        ],
        "persistence": {
            "n_conditions": 3,
            "bins": [
                {"label": "100%", "count": 1},
                {"label": ">=90%", "count": 1},
                {"label": ">=75%", "count": 1},
                {"label": ">=50%", "count": 1},
            ],
            "by_role": {
                "GF": [1, 1, 1, 1],
                NO_ROLE: [0, 0, 0, 0],
            },
            "neurons": [
                {
                    "root_id": 301,
                    "role": "GF",
                    "n_responsive": 3,
                    "n_eligible": 3,
                    "per_family": {"rate": [2, 2]},
                },
                {
                    "root_id": 999,
                    "role": NO_ROLE,
                    "n_responsive": 1,
                    "n_eligible": 3,
                    "per_family": {"rate": [1, 2]},
                },
            ],
        },
    }


def test_render_deterministic_and_clean(tmp_path: Path) -> None:
    results = _results(tmp_path)
    first = tmp_path / "a"
    second = tmp_path / "b"
    write(results, report=first / "robustness.md", results_path=first / "results.json")
    write(results, report=second / "robustness.md", results_path=second / "results.json")
    for name in ("robustness.md", "results.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    text = (first / "robustness.md").read_text(encoding="utf-8")
    assert STATEMENT in text
    assert FORBIDDEN.search(text.replace(STATEMENT, "")) is None
    for banned in (str(tmp_path), str(Path.home()), "wall_s", "host", "UTC"):
        assert banned not in text


def test_failed_condition_listed(tmp_path: Path) -> None:
    text = render(_results(tmp_path))
    assert "| stim-lc4-left | subset_side | failed |" in text
    assert "| rate-50hz | rate | completed |" in text
    reason = "condition runner exited with status 1"
    assert text.index(reason) > text.index("## Failed, dropped or reduced conditions")


def test_no_parallel_baseline_sentence(tmp_path: Path) -> None:
    results = _results(tmp_path)
    results["baseline"]["parallel_ids"] = []
    results["baseline"]["parallel_cell_types"] = []
    text = render(results)
    assert "The baseline has no parallel group; only candidate cell types are tracked." in text


def test_sections_present(tmp_path: Path) -> None:
    text = render(_results(tmp_path))
    positions = []
    for heading in ["# Robustness of the v783 LC4/LPLC2 escape circuit (M6)", *SECTIONS]:
        assert text.count(heading) == 1
        positions.append(text.index(heading))
    assert positions == sorted(positions)
