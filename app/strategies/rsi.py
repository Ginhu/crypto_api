from app.strategies.base import Trade


def rsi_oversold(candles: list[dict]) -> list[Trade]:
    period = 14
    closes = [float(c["close"]) for c in candles]

    if len(closes) <= period:
        return []

    gains = [max(closes[i] - closes[i - 1], 0.0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0.0) for i in range(1, len(closes))]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    trades: list[Trade] = []
    in_trade: Trade | None = None

    for i in range(period, len(closes)):
        rsi = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

        if in_trade is None and rsi < 30:
            in_trade = Trade(
                entry_time=candles[i]["open_time"],
                exit_time="",
                entry_price=float(candles[i]["close"]),
                exit_price=0.0,
            )
        elif in_trade is not None and rsi > 70:
            in_trade.exit_time = candles[i]["open_time"]
            in_trade.exit_price = float(candles[i]["close"])
            trades.append(in_trade)
            in_trade = None

        if i < len(closes) - 1:
            change = closes[i] - closes[i - 1]
            avg_gain = (avg_gain * (period - 1) + max(change, 0.0)) / period
            avg_loss = (avg_loss * (period - 1) + max(-change, 0.0)) / period

    return trades
