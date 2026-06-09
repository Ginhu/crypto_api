from app.strategies.ma_crossover import ma_crossover_20_50
from app.strategies.rsi import rsi_oversold

REGISTRY: dict[str, callable] = {
    "rsi_oversold": rsi_oversold,
    "ma_crossover_20_50": ma_crossover_20_50,
}
