"""
Open Interest Delta Module (PROP-001)
Classifies OI changes against price changes into quadrants.
"""

import math
import statistics


# ── Constants ──────────────────────────────────────────────────────────────
QUADRANT_NEW_LONGS       = 'NEW_LONGS'
QUADRANT_SHORT_COVERING   = 'SHORT_COVERING'
QUADRANT_NEW_SHORTS       = 'NEW_SHORTS'
QUADRANT_LONG_LIQUIDATION = 'LONG_LIQUIDATION'
QUADRANT_NEUTRAL          = 'neutral'
QUADRANT_UNKNOWN          = 'unknown'


# ── Classification ─────────────────────────────────────────────────────────

def classify_oi_delta(price_change_pct: float,
                      oi_change_pct: float,
                      threshold: float = 0.001) -> str:
    """
    Classify an OI + price move into one of four quadrants.

    Both inputs are expressed as decimals (0.01 = 1 %).

    Parameters
    ----------
    price_change_pct : float
        Percentage price change as a decimal (e.g. 0.02 for +2 %).
    oi_change_pct : float
        Percentage OI change as a decimal.
    threshold : float
        Minimum absolute value to treat as a real move (default 0.001 = 0.1 %).
        Values with absolute magnitude below this are treated as zero for
        quadrant logic.

    Returns
    -------
    str
        One of 'NEW_LONGS', 'SHORT_COVERING', 'NEW_SHORTS',
        'LONG_LIQUIDATION', 'neutral', or 'unknown'.
    """
    # ── Guard against NaN ──
    if math.isnan(price_change_pct) or math.isnan(oi_change_pct):
        return QUADRANT_UNKNOWN

    # ── Apply threshold ──
    p_up   = price_change_pct > threshold
    p_down = price_change_pct < -threshold
    o_up   = oi_change_pct > threshold
    o_down = oi_change_pct < -threshold

    if p_up and o_up:
        return QUADRANT_NEW_LONGS
    elif p_up and o_down:
        return QUADRANT_SHORT_COVERING
    elif p_down and o_up:
        return QUADRANT_NEW_SHORTS
    elif p_down and o_down:
        return QUADRANT_LONG_LIQUIDATION
    else:
        return QUADRANT_NEUTRAL


# ── OI Delta Z-Score ───────────────────────────────────────────────────────

def compute_oi_delta_z(oi_changes_history: list) -> float:
    """
    Z-score of the latest OI change against its historical distribution.

    The *last* element is treated as the latest observation.
    """
    if len(oi_changes_history) < 2:
        return 0.0
    latest = oi_changes_history[-1]
    rest = oi_changes_history[:-1]
    mean = statistics.mean(rest)
    stdev = statistics.stdev(rest) if len(rest) >= 2 else 0.0
    if stdev == 0.0:
        return 0.0 if latest == mean else (float('inf') if latest > mean else float('-inf'))
    return (latest - mean) / stdev


# ── Participation Score ────────────────────────────────────────────────────

def participation_score(oi_delta_z: float, volume_z: float) -> float:
    """
    How significant is this OI move relative to typical volume?

    Returns a score in [0, 1] combining both z-scores via a sigmoid-like
    function so the output saturates gracefully.

    Parameters
    ----------
    oi_delta_z : float
        Z-score of the OI change.
    volume_z : float
        Z-score of the corresponding volume.

    Returns
    -------
    float  ∈ [0, 1]
    """
    # Average absolute z-score, weighted slightly toward OI.
    combined = (abs(oi_delta_z) * 0.6 + abs(volume_z) * 0.4)
    # Logistic squash: ~0.5 at z=1, ~0.88 at z=2, ~0.99 at z=4
    return 1.0 / (1.0 + math.exp(-combined + 1.0))


# ── Interpretation ─────────────────────────────────────────────────────────

def interpret_quadrant(quadrant: str, oi_delta_z: float, part_score: float) -> dict:
    """
    Produce a human-readable interpretation of a quadrant classification.

    Returns a dict with keys:
      - directional_bias: +1 (bullish), -1 (bearish), 0 (neutral / unknown)
      - conviction: 'low', 'med', or 'high'
      - narrative: single-sentence string explanation
    """
    # ── Directional bias by quadrant ──
    bias_map = {
        QUADRANT_NEW_LONGS:        +1,
        QUADRANT_SHORT_COVERING:   +1,
        QUADRANT_NEW_SHORTS:       -1,
        QUADRANT_LONG_LIQUIDATION: -1,
        QUADRANT_NEUTRAL:           0,
        QUADRANT_UNKNOWN:           0,
    }
    directional_bias = bias_map.get(quadrant, 0)

    # ── Conviction ──
    z_abs = abs(oi_delta_z)
    if math.isnan(part_score) or math.isinf(part_score):
        part_score_clean = 0.5
    else:
        part_score_clean = part_score

    if z_abs < 1.0 and part_score_clean < 0.5:
        conviction = 'low'
    elif z_abs < 2.0 and part_score_clean < 0.7:
        conviction = 'med'
    else:
        conviction = 'high'

    # ── Narrative ──
    narratives = {
        QUADRANT_NEW_LONGS:        'New long positions entering — bullish flow.',
        QUADRANT_SHORT_COVERING:   'Shorts closing / covering — potentially bullish.',
        QUADRANT_NEW_SHORTS:       'New shorts entering — bearish accumulation.',
        QUADRANT_LONG_LIQUIDATION: 'Longs being liquidated — bearish / forced selling.',
        QUADRANT_NEUTRAL:          'No clear OI-price divergence — signal neutral.',
        QUADRANT_UNKNOWN:          'Cannot classify — invalid or missing input data.',
    }
    narrative = narratives.get(quadrant, 'Unrecognised quadrant.')

    return {
        'directional_bias': directional_bias,
        'conviction': conviction,
        'narrative': narrative,
    }