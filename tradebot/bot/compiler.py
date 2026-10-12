"""Compiler bot: combines signals into a ranked watchlist and markdown report."""
from datetime import datetime


def composite(sig: dict, weights: dict) -> float:
    return round(sum(sig[k]["score"] * w for k, w in weights.items()), 3)


def report(rows: list[dict], actions: list[str], equity: float, cash: float, vix) -> str:
    rows = sorted(rows, key=lambda r: r["score"], reverse=True)
    out = [f"# Daily report {datetime.now():%Y-%m-%d %H:%M}", "",
           f"Equity **${equity:,.2f}** · Cash ${cash:,.2f} · VIX {vix if vix is not None else 'n/a'}", "",
           "| Rank | Ticker | Score | News | Whales | Vol | Price | Top headline |",
           "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        h = (r["news"]["headlines"] or [""])[0][:60].replace("|", "/")
        out.append(f"| {i} | {r['ticker']} | {r['score']:+.2f} | {r['news']['score']:+.2f} | "
                   f"{r['whales']['score']:+.2f} | {r['volatility']['score']:+.2f} | {r['volatility']['price']:.2f} | {h} |")
    out += ["", "## Actions", *([f"- {a}" for a in actions] or ["- none"])]
    return "\n".join(out)
