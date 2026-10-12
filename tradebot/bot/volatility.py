"""Volatility bot: ATR, realized vol, VIX regime, and trend."""
import numpy as np
import pandas as pd
from . import data


def atr(df: pd.DataFrame, n: int = 14) -> float:
    prev = df["Close"].shift()
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1])


def vix() -> float | None:
    try:
        return data.last_price("^VIX")
    except Exception:
        return None


def scan(ticker: str, vix_level: float | None = None) -> dict:
    df = data.history(ticker, "6mo")
    c = df["Close"]
    rv = float(np.log(c).diff().iloc[-20:].std() * np.sqrt(252))
    trend = 1 if c.iloc[-1] > c.rolling(50).mean().iloc[-1] else -1
    score = 0.5 * trend
    if vix_level is not None:
        score += 0.3 if vix_level < 18 else -0.5 if vix_level > 28 else 0
    if rv > 0.8:  # extremely choppy names get penalised
        score -= 0.3
    return {"score": max(-1.0, min(1.0, score)), "atr": atr(df), "realized_vol": round(rv, 3),
            "trend": trend, "price": float(c.iloc[-1])}
