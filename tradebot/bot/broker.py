"""Buy/sell bot: paper brokers. Live trading is intentionally not implemented."""
import json
import os
from datetime import date

STATE = os.path.join(os.path.dirname(__file__), "..", "paper_state.json")


class SimBroker:
    """Fake-money broker that persists to paper_state.json."""

    def __init__(self, cash: float, path: str = STATE):
        self.path = path
        if os.path.exists(path):
            with open(path) as f:
                self.s = json.load(f)
        else:
            self.s = {"cash": cash, "positions": {}, "log": [], "day": None, "day_start_equity": cash}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.s, f, indent=2)

    @property
    def cash(self):
        return self.s["cash"]

    @property
    def positions(self):
        return self.s["positions"]

    def equity(self, prices: dict) -> float:
        return self.cash + sum(p["qty"] * prices.get(t, p["entry"]) for t, p in self.positions.items())

    def start_day(self, equity: float) -> float:
        today = date.today().isoformat()
        if self.s["day"] != today:
            self.s["day"], self.s["day_start_equity"] = today, equity
        return self.s["day_start_equity"]

    def buy(self, t, qty, price, stop):
        self.s["cash"] -= qty * price
        self.positions[t] = {"qty": qty, "entry": price, "stop": stop}
        self.s["log"].append({"date": date.today().isoformat(), "side": "BUY", "ticker": t, "qty": qty, "price": price})

    def sell(self, t, price, why=""):
        p = self.positions.pop(t)
        self.s["cash"] += p["qty"] * price
        self.s["log"].append({"date": date.today().isoformat(), "side": "SELL", "ticker": t, "qty": p["qty"],
                              "price": price, "pnl": round((price - p["entry"]) * p["qty"], 2), "why": why})


class IBKRPaperBroker(SimBroker):
    """Mirrors SimBroker bookkeeping and also sends market orders to an IBKR *paper* account.

    Requires TWS / IB Gateway logged into a paper account (default port 7497) and `pip install ib_async`.
    """

    def __init__(self, cash, host, port, client_id):
        if port not in (7497, 4002):
            raise ValueError("Refusing non-paper IBKR port; use 7497 (TWS) or 4002 (Gateway)")
        super().__init__(cash)
        from ib_async import IB
        self.ib = IB()
        self.ib.connect(host, port, clientId=client_id)

    def _order(self, t, side, qty):
        from ib_async import MarketOrder, Stock
        sym, exch, cur = (t[:-3], "TSE", "CAD") if t.endswith(".TO") else (t, "SMART", "USD")
        c = Stock(sym, "SMART" if exch == "SMART" else exch, cur)
        self.ib.qualifyContracts(c)
        self.ib.placeOrder(c, MarketOrder(side, qty))

    def buy(self, t, qty, price, stop):
        self._order(t, "BUY", qty)
        super().buy(t, qty, price, stop)

    def sell(self, t, price, why=""):
        self._order(t, "SELL", self.positions[t]["qty"])
        super().sell(t, price, why)
