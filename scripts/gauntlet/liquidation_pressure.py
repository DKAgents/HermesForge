"""
Liquidation Pressure Module (PROP-001)
Identifies liquidation clusters, cascade states, and exhaustion signals.
"""

import math
import statistics


# ── Constants ──────────────────────────────────────────────────────────────
CLUSTER_BAND_PCT = 0.005          # 0.5% price band for grouping liquidations
TOP_N_CLUSTERS = 5                # keep top-5 clusters per side
CASCADE_WICK_ATR_MULT = 2.0       # outsized wick threshold in ATR units
CASCADE_OI_DROP_PCT = -0.03       # -3% OI change threshold
CASCADE_WINDOW = 12               # bars to check conditions
EXHAUSTION_DISTANCE_ATR = 1.5     # distance from cluster in ATR for exhaustion


# ── Liquidation Clusters ──────────────────────────────────────────────────

def estimate_liquidation_clusters(liquidations: list) -> dict:
    """
    Group liquidations within 0.5% price bands into clusters.

    Args:
        liquidations: list of dicts, each with {'price': float, 'size': float, 'side': str}
                      side is 'long' or 'short'.

    Returns:
        dict with:
            'long_clusters':  [(price_avg, total_size), ...] top-N by total_size
            'short_clusters': [(price_avg, total_size), ...] top-N by total_size
    """
    longs = [liq for liq in liquidations if liq.get('side') == 'long']
    shorts = [liq for liq in liquidations if liq.get('side') == 'short']

    long_clusters = _cluster_by_price_band(longs)
    short_clusters = _cluster_by_price_band(shorts)

    # Sort by total_size descending, keep top N
    long_clusters.sort(key=lambda x: x[1], reverse=True)
    short_clusters.sort(key=lambda x: x[1], reverse=True)

    return {
        'long_clusters': long_clusters[:TOP_N_CLUSTERS],
        'short_clusters': short_clusters[:TOP_N_CLUSTERS],
    }


def _cluster_by_price_band(items: list) -> list:
    """
    Group items with prices within CLUSTER_BAND_PCT into clusters.
    Returns list of (avg_price, total_size).
    """
    if not items:
        return []

    # Sort by price ascending
    sorted_items = sorted(items, key=lambda x: x['price'])

    clusters = []
    current_bucket = [sorted_items[0]]

    for item in sorted_items[1:]:
        # Compare to the lowest price in the current bucket
        ref_price = current_bucket[0]['price']
        if ref_price == 0:
            pct_diff = abs(item['price'])
        else:
            pct_diff = abs(item['price'] - ref_price) / abs(ref_price)

        if pct_diff <= CLUSTER_BAND_PCT:
            current_bucket.append(item)
        else:
            clusters.append(_summarize_bucket(current_bucket))
            current_bucket = [item]

    # Don't forget the last bucket
    if current_bucket:
        clusters.append(_summarize_bucket(current_bucket))

    return clusters


def _summarize_bucket(bucket: list) -> tuple:
    """Return (volume_weighted_avg_price, total_size) for a bucket."""
    total_size = sum(item['size'] for item in bucket)
    if total_size == 0:
        return (bucket[0]['price'], 0.0)
    vwap = sum(item['price'] * item['size'] for item in bucket) / total_size
    return (vwap, total_size)


# ── Distance to Cluster ───────────────────────────────────────────────────

def distance_to_cluster_atr(current_price: float, clusters: list, atr: float) -> float:
    """
    Distance from current_price to the nearest cluster, in ATR units.

    Args:
        current_price: current mark price
        clusters: list of (price, total_size) from estimate_liquidation_clusters
        atr: current ATR value

    Returns:
        float: distance in ATR units (0.0 if no clusters or atr ≤ 0)
    """
    if not clusters or atr <= 0:
        return 0.0

    min_abs_distance = min(abs(cluster[0] - current_price) for cluster in clusters)
    return min_abs_distance / atr


# ── Cascade Detection ─────────────────────────────────────────────────────

def detect_cascade(wicks: list, oi_changes: list, funding_changes: list,
                   window: int = CASCADE_WINDOW) -> tuple:
    """
    Detect if a liquidation cascade is active.

    A cascade requires ALL three conditions within `window` bars:
      1. Outsized wick: wick > 2x ATR (wick = abs(high - low) for that bar)
         Here we use ATR as the mean of wicks across the window.
      2. OI drop > 3% (cumulative across window)
      3. Funding snap toward zero (abs(funding_change) > mean_abs_change * 2
         and direction toward zero)

    Args:
        wicks: list of dicts with {'high': float, 'low': float, 'close': float}
        oi_changes: list of floats (OI % change per bar)
        funding_changes: list of floats (funding rate change per bar)
        window: number of bars to check (default 12)

    Returns:
        tuple: (cascade_active: bool, direction: str, severity: str)
               direction is 'long_squeeze' (price up, wicks up), 'short_squeeze' (price down),
               or 'none'. severity is 'mild', 'moderate', 'severe', or 'none'.
    """
    if len(wicks) < 2 or len(oi_changes) < window or len(funding_changes) < window:
        return (False, 'none', 'none')

    # Use latest `window` bars
    window_wicks = wicks[-window:]
    window_oi = oi_changes[-window:]
    window_funding = funding_changes[-window:]

    # Compute ATR as mean wick size over the window
    wick_sizes = [abs(b['high'] - b['low']) for b in window_wicks]
    atr = statistics.mean(wick_sizes) if wick_sizes else 0

    if atr == 0:
        return (False, 'none', 'none')

    # Condition 1: outsized wick in the most recent bar
    latest_wick = wick_sizes[-1]
    outsized_wick = latest_wick > CASCADE_WICK_ATR_MULT * atr

    # Condition 2: cumulative OI drop > 3%
    cumulative_oi = sum(window_oi)
    oi_dropped = cumulative_oi < CASCADE_OI_DROP_PCT

    # Condition 3: funding snap toward zero
    funding_snap = _funding_snap_toward_zero(window_funding)

    cascade_active = outsized_wick and oi_dropped and funding_snap

    if not cascade_active:
        return (False, 'none', 'none')

    # Determine direction: check if price is moving down (short squeeze / longs liquidated)
    # or up (long squeeze / shorts liquidated)
    first_close = window_wicks[0]['close']
    last_close = window_wicks[-1]['close']
    if first_close == 0:
        return (False, 'none', 'none')

    pct_change = (last_close - first_close) / abs(first_close)

    if pct_change > 0.02:
        direction = 'short_squeeze'   # price moving up → shorts being squeezed
    elif pct_change < -0.02:
        direction = 'long_squeeze'    # price moving down → longs being liquidated
    else:
        direction = 'short_squeeze'   # default: large wick suggests squeeze

    # Severity based on combined signals
    wick_ratio = latest_wick / atr
    oi_drop_magnitude = abs(cumulative_oi)

    if wick_ratio > 4.0 or oi_drop_magnitude > 0.10:
        severity = 'severe'
    elif wick_ratio > 3.0 or oi_drop_magnitude > 0.06:
        severity = 'moderate'
    else:
        severity = 'mild'

    return (cascade_active, direction, severity)


def _funding_snap_toward_zero(funding_changes: list) -> bool:
    """
    Check if funding rate changes show a snap toward zero.

    A funding snap occurs when the recent segment of changes opposes
    the earlier trend, indicating funding is re-pricing toward neutral.

    Criteria:
      - Early segment and recent segment have opposing net direction
      - The opposing move has sufficient magnitude (≥ 25% of the earlier
        accumulation in absolute terms)
    """
    if len(funding_changes) < 3:
        return False

    # Split into early half and recent half
    mid = len(funding_changes) // 2
    early = funding_changes[:mid]
    recent = funding_changes[-mid:]

    early_sum = sum(early)
    recent_sum = sum(recent)

    if early_sum == 0:
        return False

    # Must have opposing signs: recent moves against the early trend
    if (early_sum * recent_sum) >= 0:
        return False  # same direction or zero recent

    # Recent move must be meaningful relative to the earlier accumulation
    ratio = abs(recent_sum) / abs(early_sum)
    return ratio >= 0.25


# ── Exhaustion Flag ───────────────────────────────────────────────────────

def exhaustion_flag(cascade_history: list, distance_to_cluster: float,
                    atr: float) -> tuple:
    """
    After a cascade, flag when the first retrace is tradeable.

    Exhaustion is signaled when:
      - A cascade was recently active (last entry in cascade_history is True)
      - Distance to nearest liquidation cluster > EXHAUSTION_DISTANCE_ATR * ATR
        (meaning the cascade has cleared through meaningful clusters)

    Args:
        cascade_history: list of bools indicating cascade state at each step.
                         Most recent is last element.
        distance_to_cluster: float, distance to nearest cluster in ATR units
        atr: current ATR value

    Returns:
        tuple: (flag: bool, confidence: float)
               confidence is 0.0-1.0 based on signal strength
    """
    if not cascade_history:
        return (False, 0.0)

    # Cascade must have been recently active
    # If latest entry is True, cascade is active → no exhaustion yet
    if cascade_history[-1]:
        return (False, 0.0)

    # Check if any recent cascade (last few bars) was active
    recent_window = min(6, len(cascade_history))
    recent_cascade = any(cascade_history[-recent_window:])

    if not recent_cascade:
        return (False, 0.0)

    # Check distance condition
    if distance_to_cluster <= EXHAUSTION_DISTANCE_ATR:
        return (False, 0.0)

    # Confidence: higher when distance is larger relative to threshold
    confidence = min(1.0, (distance_to_cluster - EXHAUSTION_DISTANCE_ATR) / EXHAUSTION_DISTANCE_ATR)
    confidence = max(0.0, min(1.0, confidence))

    return (True, confidence)