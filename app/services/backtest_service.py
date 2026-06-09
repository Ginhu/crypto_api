import statistics

from app.strategies.base import Trade


def _compute_metrics(trades: list[Trade]) -> dict:
    if not trades:
        return {
            "total_return_pct": 0.0,
            "win_rate_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sharpe_ratio": 0.0,
            "num_trades": 0,
        }

    returns = [(t.exit_price - t.entry_price) / t.entry_price for t in trades]
    total_return_pct = round(sum(returns) * 100, 2)
    win_rate_pct = round(sum(1 for r in returns if r > 0) / len(trades) * 100, 2)

    equity, peak, max_dd = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        dd = (equity - peak) / peak
        max_dd = min(max_dd, dd)
    max_drawdown_pct = round(max_dd * 100, 2)

    if len(returns) < 2:
        sharpe = 0.0
    else:
        mean_r = statistics.mean(returns)
        std_r = statistics.stdev(returns)
        sharpe = round((mean_r / std_r * 252 ** 0.5) if std_r > 0 else 0.0, 4)

    return {
        "total_return_pct": total_return_pct,
        "win_rate_pct": win_rate_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "sharpe_ratio": sharpe,
        "num_trades": len(trades),
    }
