#!/usr/bin/env python3
"""
regime_transition_detector.py — Regime Transition Detection

Detects when the market regime is CHANGING (not just what it currently is).
Transitions are the highest-risk, highest-opportunity moments for trading.

Stores daily regime snapshots and compares current to prior to detect:
  1. VIX regime shifts (risk_on → risk_off, etc.)
  2. F&G regime shifts (fear → greed, etc.)
  3. Breadth shifts (>70% → <40%, etc.)
  4. Correlation regime changes
  5. Funding rate shifts (neutral → extreme)
  6. VRP crossings (positive → negative)

Alerts:
  - "VIX ALERT: risk_on → risk_off" — reduce longs
  - "BREADTH ALERT: 75% → 35%" — deterioration
  - "F&G SHIFT: Fear → Greed" — sentiment reversal
  - "CORRELATION: unified → diversified" — stock-picking window opening

Usage:
    python3 regime_transition_detector.py               # detect + store snapshot
    python3 regime_transition_detector.py --json         # JSON output
    python3 regime_transition_detector.py --history       # show transition history
"""

import sys
import json
import argparse
import pathlib
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "research"))

HISTORY_FILE = pathlib.Path.home() / ".hermes" / "market_data" / "regime_history.json"


def _safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return None


def _load_history() -> list:
    """Load regime history."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            return []
    return []


def _save_history(history: list):
    """Save regime history (keep last 90 days)."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Keep last 90 entries
    history = history[-90:]
    HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str))


def _take_snapshot() -> dict:
    """Take a snapshot of current regime state."""
    from regime_filter import get_regime
    
    regime = _safe_call(get_regime) or {}
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "overall": regime.get("overall", "unknown"),
        "stock_regime": regime.get("stock_regime", "unknown"),
        "crypto_regime": regime.get("crypto_regime", "unknown"),
        "vix": regime.get("vix", {}).get("current", 0),
        "vix_regime": regime.get("vix", {}).get("regime", "unknown"),
        "fear_greed": regime.get("fear_greed", {}).get("value", 50),
        "breadth_pct_50ma": regime.get("breadth", {}).get("pct_above_50ma", 50),
        "breadth_divergence": regime.get("breadth", {}).get("divergence", "none"),
        "correlation_regime": regime.get("correlation", {}).get("correlation_regime", "normal"),
        "vol_risk_premium": regime.get("vol_risk_premium", {}).get("vol_risk_premium", 0),
        "put_call": regime.get("put_call", {}).get("total_ratio", 1.0),
        "funding_extremes": len([k for k, v in regime.get("funding", {}).items()
                                  if v.get("extreme", "neutral") != "neutral"]),
        "tvl_trend": regime.get("tvl", {}).get("trend", ""),
        "stablecoin_trend": regime.get("stablecoin", {}).get("trend", ""),
    }


def detect_transitions() -> dict:
    """Detect regime transitions by comparing current to prior snapshot."""
    history = _load_history()
    current = _take_snapshot()
    
    # Save current snapshot
    history.append(current)
    _save_history(history)
    
    transitions = []
    
    if len(history) < 2:
        return {
            "timestamp": current["timestamp"],
            "current": current,
            "transitions": [],
            "note": "First snapshot — no prior data for comparison",
        }
    
    prior = history[-2]
    
    # 1. Overall regime shift
    if current["overall"] != prior["overall"]:
        transitions.append({
            "type": "overall_regime",
            "severity": "HIGH",
            "from": prior["overall"],
            "to": current["overall"],
            "description": f"Overall regime shifted: {prior['overall']} → {current['overall']}",
            "action": _regime_action(prior["overall"], current["overall"]),
        })
    
    # 2. Stock regime shift
    if current["stock_regime"] != prior["stock_regime"]:
        transitions.append({
            "type": "stock_regime",
            "severity": "HIGH",
            "from": prior["stock_regime"],
            "to": current["stock_regime"],
            "description": f"Stock regime shifted: {prior['stock_regime']} → {current['stock_regime']}",
            "action": _regime_action(prior["stock_regime"], current["stock_regime"]),
        })
    
    # 3. Crypto regime shift
    if current["crypto_regime"] != prior["crypto_regime"]:
        transitions.append({
            "type": "crypto_regime",
            "severity": "HIGH",
            "from": prior["crypto_regime"],
            "to": current["crypto_regime"],
            "description": f"Crypto regime shifted: {prior['crypto_regime']} → {current['crypto_regime']}",
            "action": _regime_action(prior["crypto_regime"], current["crypto_regime"]),
        })
    
    # 4. VIX regime shift
    if current["vix_regime"] != prior["vix_regime"]:
        transitions.append({
            "type": "vix_regime",
            "severity": "HIGH",
            "from": prior["vix_regime"],
            "to": current["vix_regime"],
            "description": f"VIX regime: {prior['vix_regime']} → {current['vix_regime']} "
                          f"(VIX {prior['vix']:.1f} → {current['vix']:.1f})",
            "action": _vix_action(prior["vix_regime"], current["vix_regime"]),
        })
    
    # 5. F&G significant shift (change > 15 points)
    fg_change = current["fear_greed"] - prior["fear_greed"]
    if abs(fg_change) > 15:
        transitions.append({
            "type": "fear_greed_shift",
            "severity": "MEDIUM",
            "from": prior["fear_greed"],
            "to": current["fear_greed"],
            "change": fg_change,
            "description": f"F&G shifted {fg_change:+.0f} points: {prior['fear_greed']} → {current['fear_greed']}",
            "action": "Sentiment shift — review open positions for regime compatibility",
        })
    
    # 6. Breadth shift (change > 15%)
    breadth_change = current["breadth_pct_50ma"] - prior["breadth_pct_50ma"]
    if abs(breadth_change) > 15:
        transitions.append({
            "type": "breadth_shift",
            "severity": "HIGH" if abs(breadth_change) > 25 else "MEDIUM",
            "from": prior["breadth_pct_50ma"],
            "to": current["breadth_pct_50ma"],
            "change": breadth_change,
            "description": f"Breadth shifted {breadth_change:+.0f}%: {prior['breadth_pct_50ma']:.0f}% → {current['breadth_pct_50ma']:.0f}%",
            "action": "Breadth deterioration" if breadth_change < 0 else "Breadth improvement — stock-picking improving" if breadth_change > 0 else "",
        })
    
    # 7. Correlation regime change
    if current["correlation_regime"] != prior["correlation_regime"]:
        transitions.append({
            "type": "correlation_regime",
            "severity": "MEDIUM",
            "from": prior["correlation_regime"],
            "to": current["correlation_regime"],
            "description": f"Correlation regime: {prior['correlation_regime']} → {current['correlation_regime']}",
            "action": _correlation_action(prior["correlation_regime"], current["correlation_regime"]),
        })
    
    # 8. VRP sign change
    prior_vrp = prior.get("vol_risk_premium", 0)
    current_vrp = current.get("vol_risk_premium", 0)
    if (prior_vrp > 0 and current_vrp < 0) or (prior_vrp < 0 and current_vrp > 0):
        transitions.append({
            "type": "vrp_sign_flip",
            "severity": "MEDIUM",
            "from": prior_vrp,
            "to": current_vrp,
            "description": f"VRP sign flip: {prior_vrp:+.1f}% → {current_vrp:+.1f}%",
            "action": "Volatility risk premium changed sign — review breakout strategies",
        })
    
    # 9. Funding extreme onset
    if current["funding_extremes"] > prior["funding_extremes"] + 1:
        transitions.append({
            "type": "funding_extreme_onset",
            "severity": "MEDIUM",
            "from": prior["funding_extremes"],
            "to": current["funding_extremes"],
            "description": f"Funding extremes increased: {prior['funding_extremes']} → {current['funding_extremes']}",
            "action": "New funding extremes — squeeze risk elevated for affected coins",
        })
    
    # 10. Divergence onset
    if current["breadth_divergence"] != "none" and prior["breadth_divergence"] == "none":
        transitions.append({
            "type": "breadth_divergence_onset",
            "severity": "MEDIUM",
            "from": "none",
            "to": current["breadth_divergence"],
            "description": f"New breadth divergence detected: {current['breadth_divergence']}",
            "action": f"{current['breadth_divergence']} divergence — often precedes reversal",
        })
    
    return {
        "timestamp": current["timestamp"],
        "current": current,
        "prior": prior,
        "transitions": transitions,
        "total_transitions": len(transitions),
        "high_severity": sum(1 for t in transitions if t["severity"] == "HIGH"),
        "history_length": len(history),
    }


def _regime_action(from_regime: str, to_regime: str) -> str:
    if to_regime == "risk_off":
        return "🔴 Reduce long exposure, add hedges"
    elif to_regime == "risk_on" and from_regime in ("risk_off", "caution"):
        return "🟢 Risk-on returning — increase long exposure"
    elif to_regime == "complacent":
        return "⚠️ Complacency — prepare for correction"
    elif to_regime == "caution":
        return "🟡 Caution regime — reduce new entries"
    return f"Regime change: {from_regime} → {to_regime}"


def _vix_action(from_regime: str, to_regime: str) -> str:
    if to_regime == "risk_off":
        return "VIX spiking — reduce longs, tighten stops"
    elif to_regime == "risk_on" and from_regime in ("elevated", "risk_off"):
        return "VIX normalizing — breakout/breakout strategies can resume"
    elif to_regime == "complacent":
        return "VIX very low — prepare for vol expansion"
    return f"VIX regime: {from_regime} → {to_regime}"


def _correlation_action(from_regime: str, to_regime: str) -> str:
    if to_regime == "diversified" and from_regime == "unified":
        return "Stock-picking window opening — boost individual stock strategies"
    elif to_regime == "unified":
        return "Correlation rising — switch to index ETFs, reduce stock-picking"
    return f"Correlation: {from_regime} → {to_regime}"


def get_transition_summary() -> dict:
    """Get concise summary for regime filter / daily briefing."""
    result = detect_transitions()
    transitions = result.get("transitions", [])
    
    return {
        "available": True,
        "total_transitions": len(transitions),
        "high_severity": result.get("high_severity", 0),
        "top_transition": transitions[0] if transitions else None,
        "current_regime": result.get("current", {}).get("overall", "unknown"),
    }


def print_report(result: dict):
    print(f"\n🔄 **Regime Transition Detector**")
    print(f"   {result['timestamp'][:19]}")
    print(f"   History: {result.get('history_length', 0)} snapshots\n")
    
    current = result.get("current", {})
    print(f"**Current Regime:**")
    print(f"  Overall: {current.get('overall', '?')}")
    print(f"  VIX: {current.get('vix', 0):.1f} ({current.get('vix_regime', '?')})")
    print(f"  F&G: {current.get('fear_greed', 50)}")
    print(f"  Breadth: {current.get('breadth_pct_50ma', 50):.0f}% > 50MA")
    print(f"  Correlation: {current.get('correlation_regime', '?')}")
    print()
    
    transitions = result.get("transitions", [])
    if not transitions:
        print(f"**No regime transitions detected** — conditions stable since last check")
    else:
        print(f"**{len(transitions)} Transition(s) Detected:**\n")
        for t in transitions:
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            print(f"  {severity_emoji.get(t['severity'], '⚪')} [{t['severity']}] {t['type']}")
            print(f"     {t['description']}")
            if t.get("action"):
                print(f"     → {t['action']}")
            print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Regime Transition Detector")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--history", action="store_true", help="Show transition history")
    args = ap.parse_args()
    
    if args.history:
        history = _load_history()
        print(f"\n📜 Regime History ({len(history)} snapshots):\n")
        for snap in history[-10:]:  # last 10
            print(f"  {snap.get('date', '?')}: overall={snap.get('overall', '?')}, "
                  f"VIX={snap.get('vix', 0):.1f}, F&G={snap.get('fear_greed', 50)}, "
                  f"breadth={snap.get('breadth_pct_50ma', 50):.0f}%")
    else:
        result = detect_transitions()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print_report(result)
