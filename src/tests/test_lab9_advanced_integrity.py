"""Additional M7 traps that may otherwise turn a green report into false evidence."""
import copy

import pytest

from lab9 import gate

pytestmark = pytest.mark.student


@pytest.fixture
def evidence():
    rows = [{"item_id": item, "seed": seed, "pass_rate": True,
             "slices": ["money_movement"]} for item in ("A", "B") for seed in (1, 2)]
    report = {"manifest": {"items": 2, "seeds": [1, 2], "eval_set_sha": "x"},
              "rows": rows, "metrics": {"pass_rate": 1.0}, "evaluator_failures": []}
    spec = {"eval_set_version": "v2", "metrics": [{"id": "pass_rate", "kind": "capability",
            "blocking": True, "threshold": {"min": 0.85, "no_significant_drop": True}}],
            "slices": [{"name": "money_movement", "metric": "pass_rate", "min": 0.9,
                        "no_significant_drop": True, "blocking": True}]}
    return report, spec


@pytest.mark.parametrize("trap", ["duplicate", "green_crash", "missing", "inf", "tags", "grid"])
def test_advanced_integrity_rejects_hidden_evidence_changes(evidence, trap):
    base, spec = evidence
    pr = copy.deepcopy(base)
    if trap == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif trap == "green_crash":
        pr["evaluator_failures"] = ["grader crashed despite green aggregate"]
    elif trap == "missing":
        del pr["rows"][0]["pass_rate"]
    elif trap == "inf":
        pr["rows"][0]["pass_rate"] = float("inf")
    elif trap == "tags":
        for row in pr["rows"]:
            row["slices"] = []
    else:
        pr["manifest"]["seeds"] = [1, 3]
    assert gate.integrity_check(pr, base, spec)


@pytest.mark.parametrize("trap", ["metric", "slice", "ci", "blocking", "max"])
def test_advanced_ratchet_cannot_be_removed(evidence, trap):
    base, spec = evidence
    loose = copy.deepcopy(spec)
    if trap == "metric":
        loose["metrics"] = []
    elif trap == "slice":
        loose["slices"] = []
    elif trap == "ci":
        loose["slices"][0]["no_significant_drop"] = False
    elif trap == "blocking":
        loose["metrics"][0]["blocking"] = False
    else:
        spec["metrics"][0]["threshold"]["max_increase"] = 0.1
        loose["metrics"][0]["threshold"]["max_increase"] = 0.5
    assert gate.integrity_check(base, base, loose, spec)


def test_advanced_reordering_rows_preserves_evidence(evidence):
    base, spec = evidence
    pr = copy.deepcopy(base)
    pr["rows"].reverse()
    assert gate.integrity_check(pr, base, spec, spec) == []
