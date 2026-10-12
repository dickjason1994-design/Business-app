"""Risk bot: position sizing, stops, and hard trading limits."""
from dataclasses import dataclass


@dataclass
class RiskConfig:
    risk_per_trade_pct: float = 1.0
    stop_loss_atr_mult: float = 2.0
    max_position_pct: float = 10.0
    max_daily_loss_pct: float = 3.0
    max_open_positions: int = 5


class RiskManager:
    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg

    def stop_price(self, entry: float, atr: float) -> float:
        return round(entry - atr * self.cfg.stop_loss_atr_mult, 2)

    def size(self, equity: float, entry: float, stop: float) -> int:
        per_share = entry - stop
        if per_share <= 0 or entry <= 0:
            return 0
        by_risk = equity * self.cfg.risk_per_trade_pct / 100 / per_share
        by_cap = equity * self.cfg.max_position_pct / 100 / entry
        return int(min(by_risk, by_cap))

    def check_buy(self, equity: float, start_equity: float, open_positions: int, cash: float, cost: float) -> str | None:
        """Return a reason string if the trade is blocked, else None."""
        if start_equity and (start_equity - equity) / start_equity * 100 >= self.cfg.max_daily_loss_pct:
            return "daily loss limit hit"
        if open_positions >= self.cfg.max_open_positions:
            return "max open positions"
        if cost > cash:
            return "insufficient cash"
        return None
