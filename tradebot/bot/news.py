"""News bot: scores recent headlines per ticker with a simple keyword model."""
import feedparser

POS = {"beat", "beats", "surge", "soar", "upgrade", "record", "raises", "strong", "buyback", "approval", "rally", "jumps"}
NEG = {"miss", "misses", "plunge", "downgrade", "lawsuit", "probe", "cuts", "weak", "recall", "falls", "slump", "fraud"}


def score_headline(text: str) -> int:
    words = {w.strip(".,:;!?'\"").lower() for w in text.split()}
    return len(words & POS) - len(words & NEG)


def scan(ticker: str, feeds: list[str], limit: int = 20) -> dict:
    heads = []
    for url in feeds:
        for e in feedparser.parse(url.format(ticker=ticker)).entries[:limit]:
            heads.append(e.get("title", ""))
    raw = sum(score_headline(h) for h in heads)
    score = max(-1.0, min(1.0, raw / 5))
    return {"score": score, "count": len(heads), "headlines": heads[:5]}
