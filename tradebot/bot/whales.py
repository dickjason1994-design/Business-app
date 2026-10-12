"""Whale bot: free proxies for big money (volume blocks + options skew).

Real unusual-options / dark-pool / 13F feeds need a paid provider (e.g. Unusual
Whales, Quiver). Plug one in by replacing `scan`.
"""
import yfinance as yf
from . import data


def scan(ticker: str) -> dict:
    df = data.history(ticker, "3mo")
    vol_ratio = float(df["Volume"].iloc[-1] / df["Volume"].iloc[-21:-1].mean())
    up_day = df["Close"].iloc[-1] > df["Close"].iloc[-2]
    score = 0.0
    if vol_ratio > 2:  # unusually heavy volume, direction from price
        score += 0.5 if up_day else -0.5
    pc = None
    try:
        t = yf.Ticker(ticker)
        if t.options:
            ch = t.option_chain(t.options[0])
            calls, puts = ch.calls["volume"].sum(), ch.puts["volume"].sum()
            if calls + puts > 0:
                pc = float(puts / max(calls, 1))
                score += 0.5 if pc < 0.5 else -0.5 if pc > 1.5 else 0
    except Exception:
        pass
    return {"score": max(-1.0, min(1.0, score)), "volume_ratio": round(vol_ratio, 2), "put_call": pc}
