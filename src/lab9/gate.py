"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    pair_sets = []
    tags = []
    graded = {m["id"] for m in spec["metrics"] if m["id"] in GRADERS}
    for entry in spec["metrics"] + spec.get("slices", []):
        th = entry.get("threshold", {}) if "id" in entry else entry
        for bound in ("min", "max", "max_increase"):
            if bound in th and (not isinstance(th[bound], (int, float)) or not math.isfinite(th[bound])):
                problems.append(f"invalid threshold {bound}")
    for name, report in (("PR", pr), ("baseline", base)):
        manifest = report.get("manifest", {})
        rows = report.get("rows", [])
        seeds = manifest.get("seeds", [])
        items = manifest.get("items", 0)
        if not seeds or len(seeds) != len(set(seeds)) or items < 1:
            problems.append(f"{name}: invalid item/seed manifest")
        if len(rows) != items * len(seeds):
            problems.append(f"{name}: row count differs from items x seeds")
        pairs = [(r.get("item_id"), r.get("seed")) for r in rows]
        unique = set(pairs)
        pair_sets.append(unique)
        if len(unique) != len(pairs):
            problems.append(f"{name}: duplicate item/seed rows")
        item_ids = {i for i, _ in pairs}
        if None in item_ids or len(item_ids) != items:
            problems.append(f"{name}: item count differs from manifest")
        if unique != {(i, s) for i in item_ids for s in seeds}:
            problems.append(f"{name}: incomplete item/seed grid")
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator_failures is not empty")
        for mid, value in report.get("metrics", {}).items():
            if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
                problems.append(f"{name}: invalid metric {mid}")
        for m in spec["metrics"]:
            if m["id"] not in report.get("metrics", {}):
                problems.append(f"{name}: missing metric {m['id']}")
        item_tags = {}
        for row in rows:
            row_tags = frozenset(row.get("slices") or [])
            item = row.get("item_id")
            if item in item_tags and item_tags[item] != row_tags:
                problems.append(f"{name}: inconsistent slice tags for {item}")
            item_tags[item] = row_tags
            for mid in graded:
                value = row.get(mid)
                if not isinstance(value, (bool, int, float)) or not math.isfinite(value):
                    problems.append(f"{name}: missing/nonfinite row metric {mid}")
        tags.append(item_tags)
        # Full harness reports carry costs, so their summaries can be checked
        # against their rows. Small unit-test fixtures need not carry costs.
        if rows and "cost_per_success" in {m["id"] for m in spec["metrics"]}:
            if any(not isinstance(r.get("cost"), (int, float)) or
                   not math.isfinite(r["cost"]) or r["cost"] < 0 for r in rows):
                problems.append(f"{name}: missing/invalid row costs")
            elif all(isinstance(r.get(mid), bool) for r in rows for mid in graded):
                recalculated = aggregate(rows, sorted(graded), k_values=spec.get("pass_k", []))
                for mid, value in recalculated.items():
                    stored = report.get("metrics", {}).get(mid)
                    if (value is not None and isinstance(stored, (int, float))
                            and abs(value - stored) > 1e-9):
                        problems.append(f"{name}: aggregate {mid} differs from rows")
    if pair_sets[0] != pair_sets[1]:
        problems.append("PR item/seed set differs from baseline")
    if tags[0] != tags[1]:
        problems.append("PR slice tags differ from baseline")

    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        def ratchet(old_entries, new_entries, key, nested):
            current = {key(m): m for m in new_entries}
            for old in old_entries:
                ident = key(old)
                new = current.get(ident)
                if new is None:
                    problems.append(f"ratchet: removed {ident}")
                    continue
                if old.get("blocking") and not new.get("blocking"):
                    problems.append(f"ratchet: disabled blocking for {ident}")
                before = old.get("threshold", {}) if nested else old
                after = new.get("threshold", {}) if nested else new
                for bound in ("min", "max", "max_increase"):
                    if bound in before and (bound not in after or
                            not isinstance(after[bound], (int, float)) or not math.isfinite(after[bound]) or
                            (after[bound] < before[bound] if bound == "min" else
                             after[bound] > before[bound])):
                        problems.append(f"ratchet: loosened {bound} for {ident}")
                if before.get("no_significant_drop") and not after.get("no_significant_drop"):
                    problems.append(f"ratchet: removed CI check for {ident}")
        ratchet(base_spec["metrics"], spec["metrics"], lambda m: m["id"], True)
        ratchet(base_spec.get("slices", []), spec.get("slices", []),
                lambda m: (m["name"], m["metric"]), False)
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        ident = f"slice:{name}/{metric}"
        a = per_item(pr, metric, slice_name=name)
        b = per_item(base, metric, slice_name=name)
        keys = sorted(a.keys() & b.keys())
        value = sum(a.values()) / len(a) if a else None
        failed = not keys or a.keys() != b.keys()
        note = ""
        if value is not None and "min" in rule and value < rule["min"]:
            failed = True
        if rule.get("no_significant_drop") and keys:
            d, lo, hi = stats.paired_bootstrap(
                [a[k] for k in keys], [b[k] for k in keys],
                n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            failed |= hi < 0
        if failed and rule.get("blocking"):
            blocked.append(ident)
        verdict = "BLOCK" if failed and rule.get("blocking") else "warn" if failed else "ok"
        lines.append(f"  {ident} {value} {note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
