#!/usr/bin/env python3
"""MAE/MFE analysis on STR-Q deep backtest CSV."""
import csv
from collections import defaultdict, Counter

CSV_PATH = "/root/HermesForge/scripts/validation/results/STR-Q-stocks-deep-phase1a.csv"
OUT_PATH = "/root/HermesForge/06-Strategies/Backtests/STR-Q-mae-mfe-analysis.md"

rows = []
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for r in reader:
        r["r_multiple"] = float(r["r_multiple"])
        r["quality_score"] = float(r["quality_score"]) if r["quality_score"] else 0.0
        rows.append(r)

total = len(rows)
exit_counts = Counter(r["exit_type"] for r in rows)
stop_pct = exit_counts["stop"] / total * 100
target_pct = exit_counts["target"] / total * 100
time_pct = exit_counts["time"] / total * 100

# Average R per exit type
avg_r_by_exit = {}
for ex in ("stop", "target", "time"):
    rs = [r["r_multiple"] for r in rows if r["exit_type"] == ex]
    avg_r_by_exit[ex] = (sum(rs) / len(rs)) if rs else 0.0

# Overall avg R
overall_avg_r = sum(r["r_multiple"] for r in rows) / total
# Expectancy
expectancy = (stop_pct/100)*avg_r_by_exit["stop"] + (target_pct/100)*avg_r_by_exit["target"] + (time_pct/100)*avg_r_by_exit["time"]

# Win rate (R > 0)
wins = sum(1 for r in rows if r["r_multiple"] > 0)
win_rate = wins / total * 100

# Stop-hit rate by level_type
level_stats = defaultdict(lambda: {"total":0,"stop":0,"target":0,"time":0,"rs":[]})
for r in rows:
    lt = r["level_type"]
    level_stats[lt]["total"] += 1
    level_stats[lt][r["exit_type"]] += 1
    level_stats[lt]["rs"].append(r["r_multiple"])

# Stop-hit rate by direction
dir_stats = defaultdict(lambda: {"total":0,"stop":0,"target":0,"time":0})
for r in rows:
    d = r["direction"]
    dir_stats[d]["total"] += 1
    dir_stats[d][r["exit_type"]] += 1

# Stop-hit rate by quality_score quartile
qs_buckets = {"low (<=40)":0,"mid (41-60)":0,"high (>60)":0}
qs_total = {"low (<=40)":0,"mid (41-60)":0,"high (>60)":0}
for r in rows:
    q = r["quality_score"]
    b = "low (<=40)" if q<=40 else ("mid (41-60)" if q<=60 else "high (>60)")
    qs_total[b] += 1
    if r["exit_type"]=="stop":
        qs_buckets[b] += 1

# Build report
lines = []
lines.append("# STR-Q MAE/MFE Analysis (Deep Backtest, Phase 1A)")
lines.append("")
lines.append(f"**Source:** `scripts/validation/results/STR-Q-stocks-deep-phase1a.csv`  ")
lines.append(f"**Total trades:** {total}  ")
lines.append(f"**Generated:** 2026-08-15")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## Methodology Note")
lines.append("")
lines.append("This backtest CSV records the **final outcome** of each trade (stop / target / time exit) ")
lines.append("rather than bar-by-bar intraday MAE/MFE. Therefore this analysis is a **simplified excursion study**:")
lines.append("")
lines.append("- **MAE proxy:** `-1R` if `exit_type=stop` (price reached the stop), `0R` if `exit_type=time` (no stop touched), and a small positive value if `exit_type=target`.")
lines.append("- **MFE proxy:** `+3R` if `exit_type=target` (target reached). For `time` exits the trade closed at `exit_price` so only the final R is known, not the intraday peak favorable excursion.")
lines.append("")
lines.append("The key diagnostic this report targets is the **stop-hit rate** — the proportion of trades that ")
lines.append("reached their stop before their target or the time limit. This is the cleanest signal of whether ")
lines.append("STR-Q's sweep-entry timing is actually improving entry quality over the original daily-bar strategies.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 1. Exit Type Distribution")
lines.append("")
lines.append("| Exit Type | Count | % of Trades |")
lines.append("|-----------|-------|-------------|")
for ex in ("stop","target","time"):
    lines.append(f"| {ex} | {exit_counts[ex]} | {exit_counts[ex]/total*100:.1f}% |")
lines.append(f"| **Total** | **{total}** | **100.0%** |")
lines.append("")
lines.append(f"**Stop-hit rate: {stop_pct:.1f}%**  ")
lines.append(f"Target-hit rate: {target_pct:.1f}%  ")
lines.append(f"Time-exit rate: {time_pct:.1f}%")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 2. Comparison vs Original Daily-Bar Strategies (73.7% stop-hit)")
lines.append("")
lines.append(f"| Strategy | Stop-hit rate | Target-hit rate | Time-exit rate |")
lines.append(f"|----------|--------------|----------------|----------------|")
lines.append(f"| Original daily-bar (baseline) | 73.7% | ~? | ~? |")
lines.append(f"| **STR-Q (deep phase 1A)** | **{stop_pct:.1f}%** | **{target_pct:.1f}%** | **{time_pct:.1f}%** |")
lines.append("")
delta = stop_pct - 73.7
verb = "lower (better)" if delta < 0 else "higher (worse)"
lines.append(f"**Delta: {abs(delta):.1f} pts {verb} than the 73.7% original baseline.**")
lines.append("")
if delta < 0:
    lines.append(f"The sweep-entry timing in STR-Q reduces the stop-hit rate by **{abs(delta):.1f} percentage points**, ")
    lines.append("indicating the entry timing is filtering out a meaningful share of the trades that would have ")
    lines.append("stopped out under the original daily-bar strategy. The remainder that *do* stop out represent ")
    lines.append("genuine sweep failures rather than poor-timing noise.")
else:
    lines.append(f"STR-Q's stop-hit rate is **{delta:.1f} pts higher** than the original baseline, suggesting the ")
    lines.append("sweep entry filter is not (yet) improving entry quality. This warrants investigation of the ")
    lines.append("sweep detection criteria or the level-selection logic.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 3. Average R by Exit Type")
lines.append("")
lines.append("| Exit Type | Avg R | Count |")
lines.append("|-----------|-------|-------|")
for ex in ("stop","target","time"):
    lines.append(f"| {ex} | {avg_r_by_exit[ex]:+.3f} | {exit_counts[ex]} |")
lines.append("")
lines.append(f"**Overall avg R per trade: {overall_avg_r:+.4f}**  ")
lines.append(f"**Expectancy (weighted): {expectancy:+.4f}R per trade**  ")
lines.append(f"**Win rate (R>0): {win_rate:.1f}%** ({wins}/{total})")
lines.append("")
lines.append("Observations:")
lines.append("")
if abs(avg_r_by_exit["stop"] - (-1.0)) < 0.05:
    lines.append("- Stop exits are realized at exactly -1R (full stop), as expected.")
if abs(avg_r_by_exit["target"] - 3.0) < 0.05:
    lines.append("- Target exits are realized at exactly +3R (full target), as expected.")
if abs(avg_r_by_exit["time"]) < 0.5:
    lines.append(f"- Time exits cluster near 0R (avg {avg_r_by_exit['time']:+.3f}R) — trades that neither ")
    lines.append("  hit stop nor target expired roughly flat, recovering most of the entry-time slippage.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 4. Stop-Hit Rate by Level Type")
lines.append("")
lines.append("| Level Type | Total | Stop | Target | Time | Stop % | Avg R |")
lines.append("|------------|-------|------|--------|------|--------|-------|")
level_rows = []
for lt, s in sorted(level_stats.items(), key=lambda kv: -kv[1]["stop"]/kv[1]["total"]):
    avg_r = sum(s["rs"])/len(s["rs"])
    sp = s["stop"]/s["total"]*100
    level_rows.append((lt, s["total"], s["stop"], s["target"], s["time"], sp, avg_r))
    lines.append(f"| {lt} | {s['total']} | {s['stop']} | {s['target']} | {s['time']} | {sp:.1f}% | {avg_r:+.3f} |")
lines.append("")
# Worst level types
worst = level_rows[:3]
lines.append("**Worst stop-hit rates:**")
for lt, tot, st, tg, tm, sp, ar in worst:
    lines.append(f"- `{lt}`: {sp:.1f}% stop-hit ({st}/{tot}), avg R {ar:+.3f}")
lines.append("")
best = sorted(level_rows, key=lambda x: x[5])[:3]
lines.append("**Best stop-hit rates:**")
for lt, tot, st, tg, tm, sp, ar in best:
    lines.append(f"- `{lt}`: {sp:.1f}% stop-hit ({st}/{tot}), avg R {ar:+.3f}")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 5. Stop-Hit Rate by Direction")
lines.append("")
lines.append("| Direction | Total | Stop | Target | Time | Stop % |")
lines.append("|-----------|-------|------|--------|------|--------|")
for d, s in sorted(dir_stats.items()):
    lines.append(f"| {d} | {s['total']} | {s['stop']} | {s['target']} | {s['time']} | {s['stop']/s['total']*100:.1f}% |")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 6. Stop-Hit Rate by Quality Score Bucket")
lines.append("")
lines.append("| Quality Bucket | Total | Stop-hit % |")
lines.append("|----------------|-------|------------|")
for b in ("low (<=40)","mid (41-60)","high (>60)"):
    t = qs_total[b]
    sh = qs_buckets[b]/t*100 if t else 0
    lines.append(f"| {b} | {t} | {sh:.1f}% |")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## Key Findings")
lines.append("")
lines.append(f"1. **Stop-hit rate is {stop_pct:.1f}%** across {total} STR-Q trades, vs 73.7% for the original daily-bar baseline — a {abs(delta):.1f}-pt {verb.split(' ')[0]} difference.")
lines.append(f"2. **Target-hit rate {target_pct:.1f}%**, **time-exit rate {time_pct:.1f}%**.")
lines.append(f"3. **Expectancy: {expectancy:+.4f}R/trade**, win rate {win_rate:.1f}%.")
if worst:
    lines.append(f"4. **Worst level type:** `{worst[0][0]}` at {worst[0][5]:.1f}% stop-hit — candidate for filtering or criteria tightening.")
lines.append("")
lines.append("---")
lines.append("*End of report.*")

with open(OUT_PATH, "w") as f:
    f.write("\n".join(lines) + "\n")

# Also print summary to stdout for the parent agent
print(f"Total trades: {total}")
print(f"Stop: {exit_counts['stop']} ({stop_pct:.1f}%)  Target: {exit_counts['target']} ({target_pct:.1f}%)  Time: {exit_counts['time']} ({time_pct:.1f}%)")
print(f"Avg R - stop:{avg_r_by_exit['stop']:+.3f}  target:{avg_r_by_exit['target']:+.3f}  time:{avg_r_by_exit['time']:+.3f}")
print(f"Overall avg R: {overall_avg_r:+.4f}  Expectancy: {expectancy:+.4f}  Win rate: {win_rate:.1f}%")
print(f"Delta vs 73.7% baseline: {delta:+.1f} pts ({verb})")
print("Worst level types:")
for lt, tot, st, tg, tm, sp, ar in worst:
    print(f"  {lt}: {sp:.1f}% stop ({st}/{tot}), avg R {ar:+.3f}")
print(f"Report written to {OUT_PATH}")
