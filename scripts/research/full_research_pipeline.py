#!/usr/bin/env python3
"""
full_research_pipeline.py — Complete Autonomous Research Pipeline

Orchestrates the full research cycle:
  1. Edge Discovery Engine — scans 20+ data sources for tradable edges
  2. Regime-Aware Strategy Selector — determines which strategies to run
  3. Strategy-Regime Heatmap — evaluates strategy performance by regime
  4. Existing research modules (factor screener, revival, decay, hypotheses)
  5. Stages candidates for autonomous pipeline

Designed to run as a cron job (weekly or 3x/week).
Output: JSON for downstream consumers + human-readable report.

Usage:
    python3 full_research_pipeline.py                    # full pipeline
    python3 full_research_pipeline.py --json              # JSON output
    python3 full_research_pipeline.py --stage              # stage candidates
    python3 full_research_pipeline.py --skip-existing      # skip existing modules
"""

import sys
import json
import time
import argparse
import pathlib
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "research"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))

OUTPUT_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "research"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"  Warning: {fn.__name__} failed: {e}", file=sys.stderr)
        return None


def run_full_pipeline(stage: bool = False, skip_existing: bool = False) -> dict:
    """Run the full research pipeline."""
    pipeline_start = time.time()
    today = datetime.now(timezone.utc)
    timestamp = today.isoformat()
    
    print("=" * 60, file=sys.stderr)
    print("HermesForge Full Research Pipeline", file=sys.stderr)
    print(f"Started: {today.strftime('%Y-%m-%d %H:%M UTC')}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    results = {
        "timestamp": timestamp,
        "modules": {},
    }
    
    # ─── Module 1: Edge Discovery Engine ──────────────────────────────────
    print("\n[1/5] Edge Discovery Engine — scanning 20+ data sources...", file=sys.stderr)
    t0 = time.time()
    from edge_discovery_engine import run_edge_discovery, stage_top_edges
    
    edge_results = _safe_call(run_edge_discovery)
    if edge_results:
        results["modules"]["edge_discovery"] = {
            "total_edges": edge_results.get("total_edges", 0),
            "by_source": edge_results.get("by_source", {}),
            "top_edge": edge_results.get("top_edge", {}),
            "edges": edge_results.get("edges", []),
        }
        
        if stage:
            staged = stage_top_edges(edge_results, max_stage=5)
            results["modules"]["edge_discovery"]["staged_candidates"] = staged
        
        print(f"  Found {edge_results.get('total_edges', 0)} edges in {time.time()-t0:.1f}s", file=sys.stderr)
    
    # ─── Module 2: Regime-Aware Strategy Selector ─────────────────────────
    print("\n[2/5] Regime-Aware Strategy Selector...", file=sys.stderr)
    t0 = time.time()
    from regime_strategy_selector import get_strategy_directives
    
    directives = _safe_call(get_strategy_directives)
    if directives:
        results["modules"]["strategy_selector"] = {
            "overall_posture": directives.get("overall_posture", "unknown"),
            "posture_reasons": directives.get("posture_reasons", []),
            "regime": directives.get("regime", {}),
            "directives": directives.get("directives", {}),
            "summary": directives.get("summary", ""),
        }
        print(f"  Posture: {directives.get('overall_posture', '?')} in {time.time()-t0:.1f}s", file=sys.stderr)
    
    # ─── Module 3: Strategy-Regime Heatmap ────────────────────────────────
    print("\n[3/5] Strategy-Regime Performance Heatmap...", file=sys.stderr)
    t0 = time.time()
    from compute_strategy_regime import compute_strategy_regime_heatmap
    
    heatmap = _safe_call(compute_strategy_regime_heatmap)
    if heatmap and not heatmap.get("note"):
        results["modules"]["strategy_regime_heatmap"] = {
            "total_closed": heatmap.get("total_closed", 0),
            "regime_counts": heatmap.get("regime_counts", {}),
            "best_combos": heatmap.get("best_combos", []),
            "worst_combos": heatmap.get("worst_combos", []),
        }
        print(f"  {heatmap.get('total_closed', 0)} closed trades analyzed in {time.time()-t0:.1f}s", file=sys.stderr)
    else:
        print(f"  No data ({heatmap.get('note', '') if heatmap else 'failed'})", file=sys.stderr)
    
    # ─── Module 4: Existing Research Modules ──────────────────────────────
    if not skip_existing:
        print("\n[4/5] Existing Research Modules...", file=sys.stderr)
        t0 = time.time()
        
        try:
            from research_runner import run_full_pipeline as run_existing
            
            existing = _safe_call(run_existing, save=False)
            if existing:
                results["modules"]["existing_pipeline"] = {
                    "factor_screener": {
                        "stock_candidates": existing.get("factor_screener", {}).get("stock", {}).get("n_candidates", 0),
                        "crypto_candidates": existing.get("factor_screener", {}).get("crypto", {}).get("n_candidates", 0),
                    },
                    "revival_tester": {
                        "candidates": existing.get("revival_tester", {}).get("n_candidates", 0),
                    },
                    "decay_monitor": {
                        "decayed": existing.get("decay_monitor", {}).get("n_decayed", 0),
                    },
                    "hypothesis_generator": {
                        "stock_hypotheses": existing.get("hypothesis_generator", {}).get("stock", {}).get("n_candidates", 0),
                        "crypto_hypotheses": existing.get("hypothesis_generator", {}).get("crypto", {}).get("n_candidates", 0),
                    },
                }
                print(f"  Done in {time.time()-t0:.1f}s", file=sys.stderr)
        except Exception as e:
            print(f"  Existing pipeline failed: {e}", file=sys.stderr)
            results["modules"]["existing_pipeline"] = {"error": str(e)}
    else:
        print("\n[4/5] Skipping existing research modules", file=sys.stderr)
    
    # ─── Module 5: Generate Heatmap Visualizations ────────────────────────
    print("\n[5/5] Generating heatmap visualizations...", file=sys.stderr)
    t0 = time.time()
    try:
        from visualize_heatmaps import (
            generate_correlation_heatmap,
            generate_strategy_regime_heatmap,
            generate_crypto_performance_heatmap,
            generate_sector_rotation_heatmap,
        )
        
        viz_results = {}
        for name, fn in [
            ("correlation", generate_correlation_heatmap),
            ("strategy_regime", generate_strategy_regime_heatmap),
            ("crypto_performance", generate_crypto_performance_heatmap),
            ("sector_rotation", generate_sector_rotation_heatmap),
        ]:
            path = _safe_call(fn)
            if path:
                viz_results[name] = str(path)
        
        results["modules"]["visualizations"] = viz_results
        print(f"  Generated {len(viz_results)} heatmaps in {time.time()-t0:.1f}s", file=sys.stderr)
    except Exception as e:
        print(f"  Visualization failed: {e}", file=sys.stderr)
        results["modules"]["visualizations"] = {"error": str(e)}
    
    # ─── Summary ──────────────────────────────────────────────────────────
    runtime = time.time() - pipeline_start
    results["runtime_seconds"] = round(runtime, 1)
    
    # Build action items
    action_items = []
    
    # From edge discovery
    edge_mod = results["modules"].get("edge_discovery", {})
    for edge in edge_mod.get("edges", [])[:5]:
        score = edge.get("score", {}).get("composite", 0)
        if score > 60:
            action_items.append({
                "priority": "HIGH",
                "source": "edge_discovery",
                "action": f"Stage '{edge.get('edge_type', '')}' edge (score={score:.0f})",
                "description": edge.get("description", ""),
            })
        elif score > 40:
            action_items.append({
                "priority": "MEDIUM",
                "source": "edge_discovery",
                "action": f"Quick-test '{edge.get('edge_type', '')}' edge (score={score:.0f})",
                "description": edge.get("description", ""),
            })
    
    # From strategy selector
    sel_mod = results["modules"].get("strategy_selector", {})
    for strat_id, d in sel_mod.get("directives", {}).items():
        if d.get("action") == "boost":
            action_items.append({
                "priority": "INFO",
                "source": "strategy_selector",
                "action": f"Boost {strat_id} to {d.get('adjusted_risk', 0)}% risk",
                "description": d.get("reason", ""),
            })
        elif d.get("action") == "suppress":
            action_items.append({
                "priority": "HIGH",
                "source": "strategy_selector",
                "action": f"Suppress {strat_id} — regime mismatch",
                "description": d.get("reason", ""),
            })
    
    # From strategy-regime heatmap
    sr_mod = results["modules"].get("strategy_regime_heatmap", {})
    for combo in sr_mod.get("best_combos", [])[:2]:
        action_items.append({
            "priority": "INFO",
            "source": "strategy_regime",
            "action": f"{combo['strategy']} works well in {combo['regime']} (WR={combo['win_rate']}%)",
            "description": f"{combo['count']} trades, avg={combo['avg_r']:+.2f}R",
        })
    
    results["action_items"] = action_items
    results["total_action_items"] = len(action_items)
    
    # Save to file
    output_file = OUTPUT_DIR / f"research_{today.strftime('%Y%m%d')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Pipeline complete in {runtime:.1f}s", file=sys.stderr)
    print(f"   Output: {output_file}", file=sys.stderr)
    print(f"   {len(action_items)} action items", file=sys.stderr)
    
    return results


def build_discord_summary(results: dict) -> str:
    """Build a concise Discord-friendly summary."""
    lines = []
    
    lines.append("🔬 **Full Research Pipeline Complete**")
    lines.append(f"*Runtime: {results.get('runtime_seconds', 0):.0f}s | {results['timestamp'][:10]}*")
    lines.append("")
    
    # Edge discovery
    edge_mod = results["modules"].get("edge_discovery", {})
    if edge_mod:
        n_edges = edge_mod.get("total_edges", 0)
        top = edge_mod.get("top_edge", {})
        lines.append(f"**Edge Discovery:** {n_edges} edges found")
        if top:
            score = top.get("score", {}).get("composite", 0)
            lines.append(f"  🔝 [{score:.0f}] {top.get('source', '')}/{top.get('edge_type', '')}")
            lines.append(f"     {top.get('description', '')[:100]}")
        staged = edge_mod.get("staged_candidates", [])
        if staged:
            lines.append(f"  📝 Staged {len(staged)} candidate(s) for pipeline")
        lines.append("")
    
    # Strategy selector
    sel_mod = results["modules"].get("strategy_selector", {})
    if sel_mod:
        posture = sel_mod.get("overall_posture", "?")
        lines.append(f"**Strategy Posture:** {posture.upper()}")
        for reason in sel_mod.get("posture_reasons", [])[:3]:
            lines.append(f"  • {reason}")
        # Show boosted/suppressed
        directives = sel_mod.get("directives", {})
        boosted = [k for k, v in directives.items() if v.get("action") == "boost"]
        suppressed = [k for k, v in directives.items() if v.get("action") == "suppress"]
        if boosted:
            lines.append(f"  🚀 Boosted: {', '.join(boosted)}")
        if suppressed:
            lines.append(f"  🚫 Suppressed: {', '.join(suppressed)}")
        lines.append("")
    
    # Strategy-regime heatmap
    sr_mod = results["modules"].get("strategy_regime_heatmap", {})
    if sr_mod and sr_mod.get("total_closed"):
        lines.append(f"**Strategy-Regime Analysis:** {sr_mod['total_closed']} closed trades")
        for combo in sr_mod.get("best_combos", [])[:2]:
            lines.append(f"  ✅ {combo['strategy']} @ {combo['regime']}: WR={combo['win_rate']}%, avg={combo['avg_r']:+.2f}R")
        for combo in sr_mod.get("worst_combos", [])[:2]:
            lines.append(f"  ❌ {combo['strategy']} @ {combo['regime']}: WR={combo['win_rate']}%, avg={combo['avg_r']:+.2f}R")
        lines.append("")
    
    # Visualizations
    viz_mod = results["modules"].get("visualizations", {})
    if viz_mod and not viz_mod.get("error"):
        lines.append(f"**Heatmaps:** {', '.join(viz_mod.keys())}")
        lines.append("")
    
    # Action items
    items = results.get("action_items", [])
    if items:
        high = [i for i in items if i["priority"] == "HIGH"]
        medium = [i for i in items if i["priority"] == "MEDIUM"]
        lines.append(f"**Action Items:** {len(high)} high, {len(medium)} medium")
        for item in high[:3]:
            lines.append(f"  🔴 {item['action']}")
        for item in medium[:3]:
            lines.append(f"  🟡 {item['action']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Full Research Pipeline")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--stage", action="store_true", help="Stage top edges as candidates")
    ap.add_argument("--skip-existing", action="store_true", help="Skip existing research modules")
    args = ap.parse_args()
    
    results = run_full_pipeline(stage=args.stage, skip_existing=args.skip_existing)
    
    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("\n" + build_discord_summary(results))
