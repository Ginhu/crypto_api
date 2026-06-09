from app.strategies.base import Trade


def ma_crossover_20_50(candles: list[dict]) -> list[Trade]:
    closes = [float(c["close"]) for c in candles]

    if len(closes) < 50:
        return []

    trades: list[Trade] = []
    in_trade: Trade | None = None
    prev_above: bool | None = None

    for i in range(49, len(closes)):
        ma20 = sum(closes[i - 19 : i + 1]) / 20
        ma50 = sum(closes[i - 49 : i + 1]) / 50
        above = ma20 > ma50

        if prev_above is not None:
            if not prev_above and above and in_trade is None:
                in_trade = Trade(
                    entry_time=candles[i]["open_time"],
                    exit_time="",
                    entry_price=closes[i],
                    exit_price=0.0,
                )
            elif prev_above and not above and in_trade is not None:
                in_trade.exit_time = candles[i]["open_time"]
                in_trade.exit_price = closes[i]
                trades.append(in_trade)
                in_trade = None

        prev_above = above

    return trades
