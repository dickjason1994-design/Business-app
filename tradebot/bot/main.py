"""Run one cycle: scan -> score -> risk-check -> paper trade -> report.

Schedule it (cron / Task Scheduler) e.g. every 30 min during market hours.
"""
import argparse
import os
import yaml

from . import news, whales, volatility, compiler
from .broker import SimBroker, IBKRPaperBroker
from .risk import RiskConfig, RiskManager

ROOT = os.path.join(os.path.dirname(__file__), "..")


def run(cfg_path: str, dry: bool = False):
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("mode") == "paper", "Only paper mode is supported"
    rm = RiskManager(RiskConfig(**cfg["risk"]))
    sc = cfg["signals"]
    broker = (IBKRPaperBroker(cfg["starting_cash"], **cfg["ibkr"]) if cfg["broker"] == "ibkr"
              else SimBroker(cfg["starting_cash"]))

    vix = volatility.vix()
    rows = []
    for t in sorted(set(cfg["watchlist"]) | set(broker.positions)):
        try:
            sig = {"news": news.scan(t, cfg["news_feeds"]), "whales": whales.scan(t),
                   "volatility": volatility.scan(t, vix)}
        except Exception as e:
            print(f"skip {t}: {e}")
            continue
        rows.append({"ticker": t, **sig, "score": compiler.composite(sig, sc["weights"])})

    prices = {r["ticker"]: r["volatility"]["price"] for r in rows}
    equity = broker.equity(prices)
    start_eq = broker.start_day(equity)
    actions = []

    # Exits first: stop-loss or score turned negative
    for r in rows:
        t, px = r["ticker"], r["volatility"]["price"]
        p = broker.positions.get(t)
        if p and (px <= p["stop"] or r["score"] <= sc["sell_score"]):
            why = "stop hit" if px <= p["stop"] else f"score {r['score']:+.2f}"
            actions.append(f"SELL {t} {p['qty']} @ {px:.2f} ({why})")
            if not dry:
                broker.sell(t, px, why)

    # Entries, best score first
    for r in sorted(rows, key=lambda r: r["score"], reverse=True):
        t, px = r["ticker"], r["volatility"]["price"]
        if r["score"] < sc["buy_score"] or t in broker.positions:
            continue
        stop = rm.stop_price(px, r["volatility"]["atr"])
        qty = rm.size(equity, px, stop)
        block = rm.check_buy(broker.equity(prices), start_eq, len(broker.positions), broker.cash, qty * px)
        if qty <= 0 or block:
            actions.append(f"BLOCKED {t}: {block or 'size 0'}")
            continue
        actions.append(f"BUY {t} {qty} @ {px:.2f}, stop {stop}")
        if not dry:
            broker.buy(t, qty, px, stop)

    if not dry:
        broker.save()
    md = compiler.report(rows, actions, broker.equity(prices), broker.cash, vix)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "reports", "latest.md"), "w") as f:
        f.write(md)
    print(md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "config.yaml"))
    ap.add_argument("--dry-run", action="store_true", help="report only, no paper orders")
    a = ap.parse_args()
    run(a.config, a.dry_run)
