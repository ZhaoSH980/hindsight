"""Pooled statistics over a suite: per-config claim-level aggregation with CIs.

Usage: python pooled_stats.py <suite_json_path>
"""
import json
import math
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main(path: str) -> None:
    summary = json.load(open(path, encoding="utf-8"))
    configs = summary["configs"]
    pooled: dict[str, dict] = {c: {"hit": 0, "gradable": 0, "briers": [], "crashed": 0} for c in configs}
    per_case_delta = []  # (case, base_hit_rate, naive_hit_rate) for paired reading

    for case, per in summary["results"].items():
        for cfg in configs:
            s = per.get(cfg) or {}
            if s.get("status") == "crashed":
                pooled[cfg]["crashed"] += 1
                continue
            o = s.get("outcome") or {}
            pooled[cfg]["hit"] += o.get("n_hit") or 0
            pooled[cfg]["gradable"] += o.get("n_gradable") or 0
            if o.get("brier") is not None:
                pooled[cfg]["briers"].append(o["brier"])

    print(f"{'config':12} {'claims':>7} {'hits':>5} {'hit_rate':>9} {'95% CI':>16} "
          f"{'brier_mean':>11} {'±SE':>7} {'crashed':>8}")
    print("-" * 82)
    for cfg in configs:
        d = pooled[cfg]
        n, k = d["gradable"], d["hit"]
        lo, hi = wilson_ci(k, n)
        briers = d["briers"]
        bm = sum(briers) / len(briers) if briers else float("nan")
        bse = (math.sqrt(sum((b - bm) ** 2 for b in briers) / (len(briers) - 1)) /
               math.sqrt(len(briers))) if len(briers) > 1 else float("nan")
        print(f"{cfg:12} {n:>7} {k:>5} {k / n if n else 0:>9.3f} "
              f"[{lo:.3f}, {hi:.3f}] {bm:>11.4f} {bse:>7.4f} {d['crashed']:>8}")

    # paired per-case Brier deltas: base vs naive, memory vs base
    for a, b in (("base", "naive"), ("memory", "base")):
        if a not in configs or b not in configs:
            continue
        deltas = []
        for case, per in summary["results"].items():
            oa = (per.get(a) or {}).get("outcome") or {}
            ob = (per.get(b) or {}).get("outcome") or {}
            if oa.get("brier") is not None and ob.get("brier") is not None:
                deltas.append(oa["brier"] - ob["brier"])
        if deltas:
            neg = sum(1 for d in deltas if d < 0)
            mean = sum(deltas) / len(deltas)
            print(f"\npaired Brier delta {a} - {b}: mean {mean:+.4f} over {len(deltas)} cases; "
                  f"{a} better (lower) in {neg}/{len(deltas)}")


if __name__ == "__main__":
    main(sys.argv[1])
