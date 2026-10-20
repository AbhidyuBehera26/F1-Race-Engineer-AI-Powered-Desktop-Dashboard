"""
Belgian GP (Spa-Francorchamps 2024) Tyre Stint Analysis.
Parses official race stint data from OpenF1 / FastF1 timing feeds.
"""

import json
import statistics
import urllib.request
from pathlib import Path

SESSION_KEY = 9574  # 2024 Belgian GP Race
CACHE_FILE = Path(__file__).parent / "f1_cache" / "belgian_gp_2024_stints.json"


def load_stints() -> list:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    url = f"https://api.openf1.org/v1/stints?session_key={SESSION_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "F1-Data-Tool/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def main():
    raw_stints = load_stints()
    stints_by_compound = {}

    for s in raw_stints:
        comp = s.get("compound")
        start = s.get("lap_start")
        end = s.get("lap_end")
        if comp and start is not None and end is not None:
            comp = comp.upper()
            laps = (end - start) + 1
            stints_by_compound.setdefault(comp, []).append(laps)

    total_stints = sum(len(v) for v in stints_by_compound.values())
    print(f"\n2024 Belgian GP -- Stint Distribution ({total_stints} Total Stints)\n")
    print(f"{'Compound':<10} {'Stints':<8} {'Min':<6} {'Median':<8} {'Mean':<8} {'Max':<6}")
    print("-" * 48)

    for comp in ["HARD", "MEDIUM", "SOFT"]:
        laps = sorted(stints_by_compound.get(comp, []))
        if not laps:
            continue
        med = int(statistics.median(laps))
        mean = statistics.mean(laps)
        print(f"{comp:<10} {len(laps):<8} {min(laps):<6} {med:<8} {mean:<8.1f} {max(laps):<6}")

    print("\nLaps per stint (sorted):")
    for comp in ["HARD", "MEDIUM", "SOFT"]:
        print(f"  {comp:<7}: {sorted(stints_by_compound.get(comp, []))}")
    print()


if __name__ == "__main__":
    main()
