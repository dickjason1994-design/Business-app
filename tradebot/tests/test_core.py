from bot.risk import RiskConfig, RiskManager
from bot.news import score_headline
from bot.broker import SimBroker
from bot.compiler import composite


def test_sizing_respects_risk_and_cap():
    rm = RiskManager(RiskConfig(risk_per_trade_pct=1, max_position_pct=10))
    # $1000 risk / $2 per share = 500, but cap = $10k / $100 = 100
    assert rm.size(100_000, 100, 98) == 100
    assert rm.size(100_000, 100, 90) == 100
    assert rm.size(100_000, 100, 50) == 20
    assert rm.size(100_000, 100, 101) == 0


def test_daily_loss_blocks():
    rm = RiskManager(RiskConfig(max_daily_loss_pct=3))
    assert rm.check_buy(96_000, 100_000, 0, 50_000, 1_000) == "daily loss limit hit"
    assert rm.check_buy(99_000, 100_000, 0, 50_000, 1_000) is None
    assert rm.check_buy(99_000, 100_000, 5, 50_000, 1_000) == "max open positions"


def test_headline_score():
    assert score_headline("Apple beats estimates, stock jumps") > 0
    assert score_headline("Regulator opens probe after recall") < 0


def test_sim_broker_roundtrip(tmp_path):
    b = SimBroker(10_000, path=str(tmp_path / "s.json"))
    b.buy("X", 10, 100, 95)
    assert b.cash == 9_000 and b.equity({"X": 110}) == 10_100
    b.sell("X", 110, "test")
    assert b.cash == 10_100 and b.s["log"][-1]["pnl"] == 100
    b.save()


def test_composite():
    sig = {"news": {"score": 1}, "whales": {"score": 0}, "volatility": {"score": -1}}
    assert composite(sig, {"news": 0.3, "whales": 0.3, "volatility": 0.4}) == -0.1
