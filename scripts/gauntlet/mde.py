"""mde.py — Minimum Detectable Effect (MDE) reporting for the Strategy Gauntlet.

US-06 M-5. Addresses the critical review's core critique: "statistical power was
never measured." A null result is only informative to the extent that the test
*could* have detected a real edge of a given size. These helpers compute the
smallest edge (per-trade Sharpe, or cross-sectional information coefficient IC)
a test CAN detect at a given sample length, turnover, and trial count, so future
nulls are reported as "not detected above MDE X" — never "no edge".

Two conventions are exposed:

  1. ``mde_sharpe(...)``      — plain two-sided t-test MDE (single hypothesis,
                                no multiple-testing deflation). This is the
                                *floor*: an edge smaller than this is
                                undetectable even with no search at all.

  2. ``mde_sharpe_dsr(...)``  — DSR-consistent MDE: the smallest per-trade
                                Sharpe that clears the gauntlet's G5 gate
                                (DSR > ``dsr_threshold``, default 0.95) with
                                power (1 - beta), AFTER deflating for
                                ``n_trials`` prior searches. It reuses the exact
                                E[max] / V[max] null that
                                ``cpcv_harness.compute_dsr`` applies, so it is
                                wired to the same selection-adjusted benchmark
                                the gauntlet already enforces. THIS is the MDE
                                that governs whether a null could have been a
                                real (but search-deflated) edge.

IC is the cross-sectional analogue (correlation between a signal and the forward
return). For a strategy that takes sign(signal) against Gaussian returns,
per-trade Sharpe ~= IC * sqrt(2/pi) ~= 0.798 * IC (single signal, breadth 1).
The Grinold fundamental law bounds strategy Sharpe by IC * sqrt(breadth), so an
IC-only MDE is only meaningful with a breadth assumption; ``mde_ic`` exposes
``breadth`` (default 1) and documents the 1/sqrt(breadth) scaling.

Unit contract for sample length / turnover: ``n_observations = sample_length *
turnover`` with BOTH in the same basis (years * trades/year, or bars *
trades/bar). The caller MUST supply non-overlapping (declustered) observations —
overlapping returns inflate the apparent n and under-state MDE (the exact error
the findings summary flags as "overlapping returns inflate significance ~5x").

Self-contained (no scipy / no cross-module import) so it can be imported by
cpcv_harness without a circular dependency; the quantile/CDF mirrors
cpcv_harness._norm_ppf / _norm_cdf exactly.
"""

from __future__ import annotations

import math


# ── Normal quantile / CDF (mirror cpcv_harness exactly) ──────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF using the error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Standard normal PPF (quantile) using rational approximation."""
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")
    a = 0.147
    y = 2.0 * p - 1.0
    part1 = math.log(1.0 - y * y)
    part2 = 2.0 / (math.pi * a) + part1 / 2.0
    sign = 1.0 if y >= 0 else -1.0
    result = sign * math.sqrt(math.sqrt(part2 * part2 - part1 / a) - part2)
    return result * math.sqrt(2.0)


# ── DSR null (E[max] / V[max]) — identical to cpcv_harness.compute_dsr ───────

def _dsr_null(n_trials: int) -> tuple[float, float]:
    """Return (E[max], V[max]) of the max-Sharpe null over n_trials trials.

    Mirrors cpcv_harness.compute_dsr's extreme-value approximation (Bailey &
    Lopez de Prado 2014): E[max] ~= (1-gamma)*Z + gamma*Z1, V[max] ~= 1/(N*phi(Z)^2).
    """
    n_trials = max(1, int(n_trials))
    gamma = 0.5772156649015329  # Euler-Mascheroni
    Z = _norm_ppf(1.0 - 1.0 / n_trials)
    Z1 = _norm_ppf(1.0 - 1.0 / (n_trials * math.e))
    e_max = (1.0 - gamma) * Z + gamma * Z1
    phi_z = math.exp(-0.5 * Z * Z) / math.sqrt(2.0 * math.pi)
    v_max = 1.0 / (n_trials * phi_z * phi_z) if abs(Z) > 1e-15 and phi_z > 1e-15 else 1e-15
    if v_max <= 0.0:
        v_max = 1e-15
    return e_max, v_max


# ── MDE (Sharpe) ─────────────────────────────────────────────────────────────

def mde_sharpe(n_observations: int, n_trials: int = 1,
               alpha: float = 0.05, beta: float = 0.20) -> float:
    """Minimum detectable per-trade Sharpe via a two-sided t-test (no deflation).

    MDE = (z_{1-alpha/2} + z_{1-beta}) / sqrt(n_observations).

    This is the *single-hypothesis* floor: an edge weaker than this cannot be
    distinguished from zero at the chosen significance/power, even if it is the
    only test ever run.
    """
    n = max(1, int(n_observations))
    z = _norm_ppf(1.0 - alpha / 2.0) + _norm_ppf(1.0 - beta)
    return z / math.sqrt(n)


def mde_sharpe_dsr(n_observations: int, n_trials: int = 1,
                   dsr_threshold: float = 0.95, beta: float = 0.20) -> float:
    """Minimum per-trade Sharpe that clears the G5 DSR gate with power (1-beta).

    Solves the gauntlet's DSR pass condition

        DSR = Phi( (sharpe*sqrt(n) - E[max]) / sqrt(V[max]) ) > dsr_threshold

    for the smallest sharpe whose sampling distribution clears the threshold
    with probability (1 - beta):

        MDE = (E[max] + z_dsr*sqrt(V[max]) + z_{1-beta}) / sqrt(n).

    E[max]/V[max] are the SAME selection-adjusted null cpcv_harness.compute_dsr
    uses, so this MDE is wired to the exact benchmark the gauntlet enforces.
    """
    n = max(1, int(n_observations))
    e_max, v_max = _dsr_null(n_trials)
    z_dsr = _norm_ppf(dsr_threshold)
    z_beta = _norm_ppf(1.0 - beta)
    return (e_max + z_dsr * math.sqrt(v_max) + z_beta) / math.sqrt(n)


# ── MDE (IC) ─────────────────────────────────────────────────────────────────

def mde_ic(n_observations: int, n_trials: int = 1,
           breadth: float = 1.0, alpha: float = 0.05, beta: float = 0.20) -> float:
    """Minimum detectable information coefficient (signal/return correlation).

    A correlation of n observations has standard error ~ 1/sqrt(n), so the
    single-signal MDE is (z_{1-alpha/2} + z_{1-beta}) / sqrt(n). With
    cross-sectional breadth B, the strategy-level Sharpe ~ IC*sqrt(B) (Grinold),
    so the detectable IC scales by 1/sqrt(B):

        MDE_ic = mde_sharpe(...) / sqrt(breadth).

    breadth = number of independent cross-sectional bets per rebalance (1 for a
    single-signal timing strategy).
    """
    if breadth <= 0:
        raise ValueError("breadth must be > 0")
    return mde_sharpe(n_observations, n_trials, alpha=alpha, beta=beta) / math.sqrt(breadth)


# ── IC <-> Sharpe conversions (sign-trade + Grinold) ─────────────────────────

def ic_to_sharpe(ic: float, breadth: float = 1.0) -> float:
    """Strategy-level per-trade Sharpe implied by an IC at the given breadth.

    Grinold: Sharpe ~= IC * sqrt(breadth). (Single-signal sign-trading sharpens
    this by sqrt(2/pi) ~= 0.798; the sqrt(breadth) form is the standard bound
    and is what mde_ic inverts.)
    """
    return ic * math.sqrt(max(breadth, 1e-9))


def sharpe_to_ic(sharpe: float, breadth: float = 1.0) -> float:
    """Inverse of ic_to_sharpe: the IC a given Sharpe implies at the breadth."""
    return sharpe / math.sqrt(max(breadth, 1e-9))


# ── Convenience (sample length * turnover) ───────────────────────────────────

def mde_from_sample_length_turnover(
    sample_length: float,
    turnover: float,
    n_trials: int = 1,
    *,
    metric: str = "sharpe_dsr",
    breadth: float = 1.0,
    alpha: float = 0.05,
    beta: float = 0.20,
    dsr_threshold: float = 0.95,
) -> float:
    """MDE from sample length and turnover (both in the same unit basis).

    n_observations = sample_length * turnover. ``metric`` selects the MDE:
      * "sharpe"        -> mde_sharpe (single-hypothesis floor)
      * "sharpe_dsr"    -> mde_sharpe_dsr (G5 DSR-consistent, DEFAULT)
      * "ic"            -> mde_ic (cross-sectional, breadth-scaled)

    Example: 1 year of swing trading at ~300 trades/year, deflated for 168
    prior ledger trials.
    """
    n_obs = sample_length * turnover
    if n_obs < 1:
        raise ValueError("sample_length * turnover must yield >= 1 observation")
    n_obs = int(round(n_obs))
    if metric == "sharpe":
        return mde_sharpe(n_obs, n_trials, alpha=alpha, beta=beta)
    if metric == "sharpe_dsr":
        return mde_sharpe_dsr(n_obs, n_trials, dsr_threshold=dsr_threshold, beta=beta)
    if metric == "ic":
        return mde_ic(n_obs, n_trials, breadth=breadth, alpha=alpha, beta=beta)
    raise ValueError(f"unknown metric={metric!r}")


# ── Report formatting ────────────────────────────────────────────────────────

def format_null_verdict(observed: float | None, mde: float, metric: str = "Sharpe") -> str:
    """The 'not detected above MDE X' phrasing for null reports.

    Replaces the unqualified 'no edge' with a power-qualified statement.
    ``observed`` is the point estimate actually measured (may be None if the
    test was data-gated); ``mde`` is the minimum detectable effect at this
    sample length / turnover / trial count.
    """
    obs = "unmeasured" if observed is None else f"{observed:+.4f}"
    return (f"not detected above MDE {metric} = {mde:.4f} "
            f"(observed {metric} = {obs})")


def mde_report(n_observations: int, n_trials: int = 1, *,
               breadth: float = 1.0,
               alpha: float = 0.05, beta: float = 0.20,
               dsr_threshold: float = 0.95) -> dict:
    """Full MDE breakdown for one (n_observations, n_trials) cell."""
    return {
        "n_observations": int(n_observations),
        "n_trials": int(n_trials),
        "mde_sharpe_single": round(mde_sharpe(n_observations, n_trials, alpha, beta), 6),
        "mde_sharpe_dsr": round(mde_sharpe_dsr(n_observations, n_trials, dsr_threshold, beta), 6),
        "mde_ic_breadth1": round(mde_ic(n_observations, n_trials, 1.0, alpha, beta), 6),
        "mde_ic_breadth": round(mde_ic(n_observations, n_trials, breadth, alpha, beta), 6),
        "breadth": breadth,
        "alpha": alpha,
        "beta": beta,
        "dsr_threshold": dsr_threshold,
    }


if __name__ == "__main__":
    import json

    # Worked example: $10K swing account, ~1y, ~300 non-overlapping trades,
    # deflated for the current trials-ledger N (168 as of US-06).
    n = 300
    n_trials = 168
    print("=== MDE worked example (n=300 non-overlapping trades, n_trials=168) ===")
    print(json.dumps(mde_report(n, n_trials, breadth=30), indent=2))
    print()
    print("single-hypothesis MDE Sharpe   :", round(mde_sharpe(n), 4))
    print("DSR-consistent MDE Sharpe      :", round(mde_sharpe_dsr(n, n_trials), 4))
    print("MDE IC (breadth=1)             :", round(mde_ic(n, n_trials, 1.0), 4))
    print("MDE IC (breadth=30, cross-sec) :", round(mde_ic(n, n_trials, 30.0), 4))
    print("format_null_verdict example    :",
          format_null_verdict(0.02, mde_sharpe_dsr(n, n_trials), "Sharpe"))
