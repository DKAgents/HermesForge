#!/usr/bin/env python3
"""
visualize_heatmaps.py — Visual Heatmap Generator

Generates PNG heatmap images for:
1. Cross-asset correlation matrix (30-day rolling)
2. Strategy × regime performance heatmap
3. Crypto performance heatmap (1d/7d/30d/90d returns)
4. Sector rotation heatmap

Output: PNG files saved to ~/.hermes/market_data/heatmaps/

Usage:
    python3 visualize_heatmaps.py                    # generate all
    python3 visualize_heatmaps.py --correlation      # correlation matrix only
    python3 visualize_heatmaps.py --strategy-regime  # strategy × regime only
    python3 visualize_heatmaps.py --crypto           # crypto performance only
    python3 visualize_heatmaps.py --sector           # sector rotation only
"""

import sys
import pathlib
import argparse
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "paper_trading"))
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "validation"))

OUTPUT_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "heatmaps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Custom diverging colormap: red → white → green (for correlations: -1 → 0 → +1)
CORR_CMAP = LinearSegmentedColormap.from_list("corr", ["#e74c3c", "#ecf0f1", "#2ecc71"])

# Performance colormap: red → yellow → green (for R multiples: negative → 0 → positive)
PERF_CMAP = LinearSegmentedColormap.from_list("perf", ["#e74c3c", "#f1c40f", "#2ecc71"])

# Returns colormap: red → dark → green
RET_CMAP = LinearSegmentedColormap.from_list("ret", ["#c0392b", "#2c3e50", "#27ae60"])


def _annotate_cells(ax, data, fmt="{:.2f}", fontsize=9, threshold=None):
    """Add value annotations to heatmap cells."""
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            if threshold is not None and (val is None or (isinstance(val, float) and np.isnan(val))):
                continue
            if isinstance(val, float) and np.isnan(val):
                ax.text(j, i, "—", ha="center", va="center", fontsize=fontsize, color="#7f8c8d")
            else:
                color = "white" if abs(val) > 0.6 else "#2c3e50"
                ax.text(j, i, fmt.format(val), ha="center", va="center", fontsize=fontsize, color=color)


def generate_correlation_heatmap() -> pathlib.Path | None:
    """Generate cross-asset correlation matrix as PNG."""
    from compute_correlation import compute_asset_correlations
    
    data = compute_asset_correlations(30)
    corrs = data.get("correlations", {})
    if not corrs:
        print("  No correlation data available")
        return None
    
    assets = list(corrs.keys())
    n = len(assets)
    matrix = np.full((n, n), np.nan)
    for i, a1 in enumerate(assets):
        for j, a2 in enumerate(assets):
            matrix[i, j] = corrs[a1].get(a2, 0)
    
    fig, ax = plt.subplots(figsize=(max(8, n * 0.9), max(6, n * 0.8)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    
    im = ax.imshow(matrix, cmap=CORR_CMAP, vmin=-1, vmax=1, aspect="auto")
    
    # Labels
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(assets, rotation=45, ha="right", color="#ecf0f1", fontsize=10)
    ax.set_yticklabels(assets, color="#ecf0f1", fontsize=10)
    
    # Title
    avg = data.get("avg_correlation", 0)
    regime = data.get("regime", "?")
    ax.set_title(f"Cross-Asset Correlation Matrix (30-day)\nAvg: {avg:.3f} → {regime.upper()}",
                 color="#ecf0f1", fontsize=14, fontweight="bold", pad=15)
    
    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#ecf0f1")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#ecf0f1")
    
    # Annotate
    _annotate_cells(ax, matrix, fmt="{:.2f}")
    
    # Grid
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#2c3e50", linewidth=0.5)
    ax.tick_params(which="minor", size=0)
    
    plt.tight_layout()
    out_path = OUTPUT_DIR / "correlation_heatmap.png"
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path


def generate_strategy_regime_heatmap() -> pathlib.Path | None:
    """Generate strategy × regime performance heatmap as PNG."""
    from compute_strategy_regime import compute_strategy_regime_heatmap
    
    data = compute_strategy_regime_heatmap()
    matrix = data.get("matrix", {})
    if not matrix:
        print(f"  {data.get('note', 'No data')}")
        return None
    
    regimes = ["risk_on", "neutral", "caution", "risk_off", "complacent"]
    strategies = sorted(matrix.keys())
    
    # Build avg_r matrix
    n_strat = len(strategies)
    n_regime = len(regimes)
    r_matrix = np.full((n_strat, n_regime), np.nan)
    count_matrix = np.full((n_strat, n_regime), 0)
    wr_matrix = np.full((n_strat, n_regime), np.nan)
    
    for i, strat in enumerate(strategies):
        for j, regime in enumerate(regimes):
            cell = matrix[strat].get(regime, {})
            if cell.get("count", 0) > 0:
                r_matrix[i, j] = cell.get("avg_r", 0)
                count_matrix[i, j] = cell.get("count", 0)
                wr_matrix[i, j] = cell.get("win_rate", 0)
    
    fig, axes = plt.subplots(1, 2, figsize=(16, max(5, n_strat * 0.8)))
    fig.patch.set_facecolor("#1a1a2e")
    
    # --- Panel 1: Avg R ---
    ax1 = axes[0]
    ax1.set_facecolor("#1a1a2e")
    
    # Mask NaN for display
    masked_r = np.ma.masked_invalid(r_matrix)
    im1 = ax1.imshow(masked_r, cmap=PERF_CMAP, vmin=-3, vmax=3, aspect="auto")
    
    ax1.set_xticks(range(n_regime))
    ax1.set_yticks(range(n_strat))
    ax1.set_xticklabels(regimes, rotation=30, ha="right", color="#ecf0f1", fontsize=9)
    ax1.set_yticklabels(strategies, color="#ecf0f1", fontsize=10)
    ax1.set_title("Avg R Multiple by Regime", color="#ecf0f1", fontsize=12, fontweight="bold")
    
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.ax.yaxis.set_tick_params(color="#ecf0f1")
    plt.setp(plt.getp(cbar1.ax.axes, "yticklabels"), color="#ecf0f1")
    
    # Annotate with avg_r and count
    for i in range(n_strat):
        for j in range(n_regime):
            if count_matrix[i, j] > 0:
                val = r_matrix[i, j]
                color = "white" if abs(val) > 1.5 else "#2c3e50"
                ax1.text(j, i, f"{val:+.2f}R\n({int(count_matrix[i,j])}tr)",
                        ha="center", va="center", fontsize=8, color=color)
            else:
                ax1.text(j, i, "—", ha="center", va="center", fontsize=9, color="#7f8c8d")
    
    ax1.set_xticks(np.arange(-0.5, n_regime, 1), minor=True)
    ax1.set_yticks(np.arange(-0.5, n_strat, 1), minor=True)
    ax1.grid(which="minor", color="#2c3e50", linewidth=0.5)
    ax1.tick_params(which="minor", size=0)
    
    # --- Panel 2: Win Rate ---
    ax2 = axes[1]
    ax2.set_facecolor("#1a1a2e")
    
    masked_wr = np.ma.masked_invalid(wr_matrix)
    im2 = ax2.imshow(masked_wr, cmap=PERF_CMAP, vmin=0, vmax=100, aspect="auto")
    
    ax2.set_xticks(range(n_regime))
    ax2.set_yticks(range(n_strat))
    ax2.set_xticklabels(regimes, rotation=30, ha="right", color="#ecf0f1", fontsize=9)
    ax2.set_yticklabels(strategies, color="#ecf0f1", fontsize=10)
    ax2.set_title("Win Rate % by Regime", color="#ecf0f1", fontsize=12, fontweight="bold")
    
    cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.ax.yaxis.set_tick_params(color="#ecf0f1")
    plt.setp(plt.getp(cbar2.ax.axes, "yticklabels"), color="#ecf0f1")
    
    for i in range(n_strat):
        for j in range(n_regime):
            if count_matrix[i, j] > 0:
                val = wr_matrix[i, j]
                color = "white" if val < 30 or val > 80 else "#2c3e50"
                ax2.text(j, i, f"{val:.0f}%\n({int(count_matrix[i,j])}tr)",
                        ha="center", va="center", fontsize=8, color=color)
            else:
                ax2.text(j, i, "—", ha="center", va="center", fontsize=9, color="#7f8c8d")
    
    ax2.set_xticks(np.arange(-0.5, n_regime, 1), minor=True)
    ax2.set_yticks(np.arange(-0.5, n_strat, 1), minor=True)
    ax2.grid(which="minor", color="#2c3e50", linewidth=0.5)
    ax2.tick_params(which="minor", size=0)
    
    fig.suptitle(f"Strategy × Regime Performance Heatmap ({data.get('total_closed', 0)} closed trades)",
                 color="#ecf0f1", fontsize=14, fontweight="bold", y=0.98)
    
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    out_path = OUTPUT_DIR / "strategy_regime_heatmap.png"
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path


def generate_crypto_performance_heatmap() -> pathlib.Path | None:
    """Generate crypto performance heatmap (1d/7d/30d/90d returns)."""
    from compute_rotation import compute_crypto_heatmap
    
    data = compute_crypto_heatmap()
    if not data:
        print("  No crypto performance data")
        return None
    
    # Sort by 7d return
    sorted_coins = sorted(data.items(), key=lambda x: x[1].get("7d", 0), reverse=True)
    symbols = [c[0] for c in sorted_coins]
    n = len(symbols)
    
    # Build return matrix
    periods = ["1d", "7d", "30d", "90d"]
    period_labels = ["1D", "7D", "30D", "90D"]
    ret_matrix = np.full((n, len(periods)), 0.0)
    
    for i, (sym, perfs) in enumerate(sorted_coins):
        for j, period in enumerate(periods):
            ret_matrix[i, j] = perfs.get(period, 0)
    
    fig, ax = plt.subplots(figsize=(8, max(6, n * 0.45)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    
    # Clip extremes for color mapping
    vmax = max(20, np.percentile(np.abs(ret_matrix), 90))
    im = ax.imshow(ret_matrix, cmap=RET_CMAP, vmin=-vmax, vmax=vmax, aspect="auto")
    
    ax.set_xticks(range(len(periods)))
    ax.set_yticks(range(n))
    ax.set_xticklabels(period_labels, color="#ecf0f1", fontsize=11)
    ax.set_yticklabels(symbols, color="#ecf0f1", fontsize=10)
    ax.set_title("Crypto Performance Heatmap (%)", color="#ecf0f1", fontsize=14, fontweight="bold", pad=15)
    
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#ecf0f1")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#ecf0f1")
    cbar.set_label("Return %", color="#ecf0f1")
    
    # Annotate
    for i in range(n):
        for j in range(len(periods)):
            val = ret_matrix[i, j]
            color = "white" if abs(val) > vmax * 0.6 else "#2c3e50"
            ax.text(j, i, f"{val:+.1f}%", ha="center", va="center", fontsize=8, color=color)
    
    ax.set_xticks(np.arange(-0.5, len(periods), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#2c3e50", linewidth=0.5)
    ax.tick_params(which="minor", size=0)
    
    plt.tight_layout()
    out_path = OUTPUT_DIR / "crypto_performance_heatmap.png"
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path


def generate_sector_rotation_heatmap() -> pathlib.Path | None:
    """Generate sector rotation heatmap (relative strength vs SPY)."""
    from compute_rotation import compute_sector_rotation
    
    data = compute_sector_rotation()
    sectors = data.get("sectors", {})
    if not sectors:
        print("  No sector rotation data")
        return None
    
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1].get("rs_vs_spy", {}).get("20d", 0), reverse=True)
    names = [f"{s[1].get('name', s[0])} ({s[0]})" for s in sorted_sectors]
    n = len(names)
    
    periods = ["1d", "5d", "20d", "60d"]
    period_labels = ["1D", "5D", "20D", "60D"]
    rs_matrix = np.full((n, len(periods)), 0.0)
    
    for i, (etf, info) in enumerate(sorted_sectors):
        rs = info.get("rs_vs_spy", {})
        for j, period in enumerate(periods):
            rs_matrix[i, j] = rs.get(period, 0)
    
    fig, ax = plt.subplots(figsize=(8, max(5, n * 0.6)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    
    vmax = max(5, np.percentile(np.abs(rs_matrix), 90))
    im = ax.imshow(rs_matrix, cmap=RET_CMAP, vmin=-vmax, vmax=vmax, aspect="auto")
    
    ax.set_xticks(range(len(periods)))
    ax.set_yticks(range(n))
    ax.set_xticklabels(period_labels, color="#ecf0f1", fontsize=11)
    ax.set_yticklabels(names, color="#ecf0f1", fontsize=10)
    ax.set_title("Sector Rotation — Relative Strength vs SPY (%)", color="#ecf0f1",
                 fontsize=14, fontweight="bold", pad=15)
    
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#ecf0f1")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#ecf0f1")
    cbar.set_label("RS %", color="#ecf0f1")
    
    for i in range(n):
        for j in range(len(periods)):
            val = rs_matrix[i, j]
            color = "white" if abs(val) > vmax * 0.6 else "#2c3e50"
            ax.text(j, i, f"{val:+.2f}%", ha="center", va="center", fontsize=9, color=color)
    
    ax.set_xticks(np.arange(-0.5, len(periods), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#2c3e50", linewidth=0.5)
    ax.tick_params(which="minor", size=0)
    
    plt.tight_layout()
    out_path = OUTPUT_DIR / "sector_rotation_heatmap.png"
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Visual Heatmap Generator")
    ap.add_argument("--correlation", action="store_true")
    ap.add_argument("--strategy-regime", action="store_true")
    ap.add_argument("--crypto", action="store_true")
    ap.add_argument("--sector", action="store_true")
    args = ap.parse_args()
    
    # If no specific flag, generate all
    generate_all = not any([args.correlation, args.strategy_regime, args.crypto, args.sector])
    
    results = {}
    
    if generate_all or args.correlation:
        print("Generating correlation heatmap...")
        results["correlation"] = str(generate_correlation_heatmap())
    
    if generate_all or args.strategy_regime:
        print("Generating strategy-regime heatmap...")
        results["strategy_regime"] = str(generate_strategy_regime_heatmap())
    
    if generate_all or args.crypto:
        print("Generating crypto performance heatmap...")
        results["crypto"] = str(generate_crypto_performance_heatmap())
    
    if generate_all or args.sector:
        print("Generating sector rotation heatmap...")
        results["sector"] = str(generate_sector_rotation_heatmap())
    
    print(f"\n✅ Done. Output: {OUTPUT_DIR}")
    for name, path in results.items():
        if path and path != "None":
            print(f"  {name}: {path}")
