"""Free price data via yfinance."""
import pandas as pd
import yfinance as yf


def history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
    return df.dropna()


def last_price(ticker: str) -> float:
    return float(history(ticker, "5d")["Close"].iloc[-1])
