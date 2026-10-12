# Paper-trading bot (6 modules)

**Paper mode only. Not financial advice.** Run on fake money for weeks before considering anything else.

| Module | File | What it does |
|---|---|---|
| News | `bot/news.py` | Yahoo RSS headlines → keyword sentiment score |
| Whales | `bot/whales.py` | Volume spikes + options put/call ratio (free proxies; swap in a paid feed) |
| Volatility | `bot/volatility.py` | ATR, realized vol, VIX regime, 50-day trend |
| Risk | `bot/risk.py` | 1% risk/trade sizing, ATR stops, position cap, max daily loss, max positions |
| Buy/Sell | `bot/broker.py` | `sim` fake-money broker, or IBKR **paper** account (refuses live ports) |
| Compiler | `bot/compiler.py` | Weighted score → ranked watchlist → `reports/latest.md` |

## Run
```bash
cd tradebot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m bot.main --dry-run   # report only
python -m bot.main             # place paper trades (state in paper_state.json)
python -m pytest tests         # unit tests
```
Edit `config.yaml` for tickers, risk limits, and signal weights.

## Schedule (every 30 min, weekdays, market hours ET)
Linux/macOS cron: `*/30 9-16 * * 1-5 cd /path/to/tradebot && .venv/bin/python -m bot.main`
Windows: Task Scheduler running `python -m bot.main` in this folder.

## RBC Direct Investing
RBC has no public trading API, so the bot can't place orders there. Keep `broker: sim` and copy the
report's BUY/SELL lines into RBC by hand (limit order, then a stop-loss at the listed stop) once you trust it.

## IBKR paper account
Install `ib_async`, log TWS/IB Gateway into your **paper** account, enable API on port 7497, set `broker: ibkr`.
